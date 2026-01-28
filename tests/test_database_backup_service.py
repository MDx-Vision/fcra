"""
Unit tests for the Database Backup Service.

Tests cover:
- Backup creation (pg_dump)
- Backup verification
- Retention cleanup
- Backup listing
- Restore functionality
- Nightly backup routine
- Helper methods
"""

import gzip
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from services.database_backup_service import (
    DatabaseBackupService,
    get_database_backup_service,
    DEFAULT_RETENTION_DAYS,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def backup_dir(tmp_path):
    """Create a temporary backup directory."""
    return tmp_path / "backups"


@pytest.fixture
def service(backup_dir):
    """Create a backup service with temp directory."""
    return DatabaseBackupService(
        database_url="postgresql://user:pass@localhost:5432/fcra",
        backup_dir=str(backup_dir),
    )


@pytest.fixture
def sample_backup(backup_dir):
    """Create a sample backup file."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    filepath = backup_dir / "fcra_backup_20260125_020000.sql.gz"
    content = b"-- PostgreSQL database dump\nCREATE TABLE clients (id SERIAL);\nCREATE TABLE staff (id SERIAL);\n"
    with gzip.open(filepath, "wb") as f:
        f.write(content)
    return filepath


# =============================================================================
# Initialization Tests
# =============================================================================


class TestInitialization:

    def test_init_with_params(self, backup_dir):
        service = DatabaseBackupService(
            database_url="postgresql://localhost/test",
            backup_dir=str(backup_dir),
            retention_days=7,
        )
        assert service.database_url == "postgresql://localhost/test"
        assert service.retention_days == 7

    def test_init_defaults(self):
        service = DatabaseBackupService()
        assert service.retention_days == DEFAULT_RETENTION_DAYS

    def test_backup_dir_created(self, backup_dir):
        DatabaseBackupService(backup_dir=str(backup_dir))
        assert backup_dir.exists()


# =============================================================================
# Parse Database URL Tests
# =============================================================================


class TestParseDatabaseUrl:

    def test_parse_full_url(self, service):
        result = service._parse_database_url()
        assert result["user"] == "user"
        assert result["password"] == "pass"
        assert result["host"] == "localhost"
        assert result["port"] == 5432
        assert result["database"] == "fcra"

    def test_parse_url_no_password(self, backup_dir):
        service = DatabaseBackupService(
            database_url="postgresql://user@localhost/fcra",
            backup_dir=str(backup_dir),
        )
        result = service._parse_database_url()
        assert result["user"] == "user"
        assert result["password"] == ""

    def test_parse_empty_url(self, backup_dir):
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            service = DatabaseBackupService(database_url="", backup_dir=str(backup_dir))
            service.database_url = ""
            assert service._parse_database_url() is None


# =============================================================================
# Backup Creation Tests
# =============================================================================


class TestCreateBackup:

    @patch("services.database_backup_service.subprocess")
    def test_create_backup_success(self, mock_subprocess, service):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.read = MagicMock(side_effect=[b"-- PostgreSQL dump\n", b""])
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read = MagicMock(return_value=b"")
        mock_subprocess.Popen.return_value = mock_proc

        result = service.create_backup(compress=True)

        assert result["success"] is True
        assert "filename" in result
        assert result["filename"].endswith(".sql.gz")
        assert "checksum" in result
        assert "size" in result

    @patch("services.database_backup_service.subprocess")
    def test_create_backup_pg_dump_fails(self, mock_subprocess, service):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.read = MagicMock(return_value=b"")
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read = MagicMock(return_value=b"connection refused")
        mock_subprocess.Popen.return_value = mock_proc

        result = service.create_backup()

        assert result["success"] is False
        assert "connection refused" in result["error"]

    def test_create_backup_no_database_url(self, backup_dir):
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            service = DatabaseBackupService(database_url="", backup_dir=str(backup_dir))
            service.database_url = ""
            result = service.create_backup()
            assert result["success"] is False
            assert "DATABASE_URL" in result["error"]

    @patch("services.database_backup_service.subprocess.Popen", side_effect=FileNotFoundError)
    def test_create_backup_pg_dump_not_found(self, mock_popen, service):
        result = service.create_backup()
        assert result["success"] is False
        assert "pg_dump not found" in result["error"]


# =============================================================================
# Verification Tests
# =============================================================================


class TestVerifyBackup:

    def test_verify_valid_backup(self, service, sample_backup):
        result = service.verify_backup(sample_backup.name)

        assert result["success"] is True
        assert result["valid"] is True
        assert result["checks"]["has_content"] is True
        assert result["checks"]["has_pg_header"] is True
        assert result["checks"]["has_clients_table"] is True
        assert result["checks"]["has_staff_table"] is True

    def test_verify_missing_file(self, service):
        result = service.verify_backup("nonexistent.sql.gz")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_verify_empty_backup(self, service, backup_dir):
        backup_dir.mkdir(parents=True, exist_ok=True)
        filepath = backup_dir / "fcra_backup_20260125_010000.sql"
        filepath.write_text("")
        result = service.verify_backup(filepath.name)
        assert result["success"] is True
        assert result["checks"]["has_content"] is False


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestCleanup:

    def test_cleanup_removes_old(self, service, backup_dir):
        backup_dir.mkdir(parents=True, exist_ok=True)
        # Create old backup (40 days ago)
        old_name = "fcra_backup_20251215_020000.sql.gz"
        old_file = backup_dir / old_name
        with gzip.open(old_file, "wb") as f:
            f.write(b"old data")

        # Create recent backup
        recent = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        recent_name = f"fcra_backup_{recent}.sql.gz"
        recent_file = backup_dir / recent_name
        with gzip.open(recent_file, "wb") as f:
            f.write(b"recent data")

        result = service.cleanup_old_backups()

        assert result["success"] is True
        assert result["removed"] >= 1
        assert old_name in result["removed_files"]
        assert not old_file.exists()
        assert recent_file.exists()

    def test_cleanup_keeps_recent(self, service, sample_backup):
        result = service.cleanup_old_backups()
        assert result["success"] is True
        assert sample_backup.exists()


# =============================================================================
# List Backups Tests
# =============================================================================


class TestListBackups:

    def test_list_backups(self, service, sample_backup):
        result = service.list_backups()

        assert result["success"] is True
        assert result["total"] >= 1
        assert any(b["filename"] == sample_backup.name for b in result["backups"])

    def test_list_empty(self, service):
        result = service.list_backups()
        assert result["success"] is True
        assert result["total"] == 0


# =============================================================================
# Restore Tests
# =============================================================================


class TestRestore:

    def test_restore_file_not_found(self, service):
        result = service.restore_backup("nonexistent.sql.gz")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @patch("services.database_backup_service.subprocess")
    def test_restore_success(self, mock_subprocess, service, sample_backup):
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        mock_subprocess.Popen.return_value = mock_proc
        mock_subprocess.run.return_value = MagicMock(returncode=0, stderr=b"")

        result = service.restore_backup(sample_backup.name)

        assert result["success"] is True
        assert result["database"] == "fcra"

    def test_restore_no_database_url(self, backup_dir, sample_backup):
        service = DatabaseBackupService(database_url="", backup_dir=str(backup_dir))
        result = service.restore_backup(sample_backup.name)
        assert result["success"] is False


# =============================================================================
# Nightly Backup Tests
# =============================================================================


class TestNightlyBackup:

    @patch.object(DatabaseBackupService, "cleanup_old_backups")
    @patch.object(DatabaseBackupService, "verify_backup")
    @patch.object(DatabaseBackupService, "create_backup")
    def test_nightly_success(self, mock_create, mock_verify, mock_cleanup, service):
        mock_create.return_value = {
            "success": True, "filename": "test.sql.gz", "size_human": "1.0 MB"
        }
        mock_verify.return_value = {"valid": True, "checks": {}}
        mock_cleanup.return_value = {"success": True, "removed": 2}

        result = service.run_nightly_backup()

        assert result["success"] is True
        mock_create.assert_called_once()
        mock_verify.assert_called_once()
        mock_cleanup.assert_called_once()

    @patch.object(DatabaseBackupService, "create_backup")
    def test_nightly_backup_fails(self, mock_create, service):
        mock_create.return_value = {"success": False, "error": "disk full"}

        with patch.object(service, "_send_failure_alert") as mock_alert:
            result = service.run_nightly_backup()

        assert result["success"] is False
        mock_alert.assert_called_once()


# =============================================================================
# Helper Tests
# =============================================================================


class TestHelpers:

    def test_human_size_bytes(self):
        assert DatabaseBackupService._human_size(500) == "500.0 B"

    def test_human_size_kb(self):
        assert DatabaseBackupService._human_size(2048) == "2.0 KB"

    def test_human_size_mb(self):
        assert DatabaseBackupService._human_size(5 * 1024 * 1024) == "5.0 MB"

    def test_human_size_gb(self):
        assert DatabaseBackupService._human_size(3 * 1024 ** 3) == "3.0 GB"

    def test_calculate_checksum(self, service, sample_backup):
        checksum = service._calculate_checksum(sample_backup)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingleton:

    def test_get_database_backup_service(self):
        s1 = get_database_backup_service()
        s2 = get_database_backup_service()
        assert s1 is s2
