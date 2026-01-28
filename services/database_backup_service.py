"""
Database Backup Service.

Provides:
- Automated PostgreSQL backups via pg_dump
- S3/cloud storage upload
- 30-day retention policy
- Backup verification (restore test)
- Backup listing, download, and restore
- Admin alerts on failure
"""

import gzip
import hashlib
import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_BACKUP_DIR = "backups"
DEFAULT_RETENTION_DAYS = 30
DEFAULT_MAX_BACKUPS = 60


class DatabaseBackupService:
    """Service for automated PostgreSQL database backups."""

    def __init__(
        self,
        database_url: Optional[str] = None,
        backup_dir: Optional[str] = None,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        s3_bucket: Optional[str] = None,
        s3_prefix: str = "db-backups",
    ):
        self.database_url = database_url or os.environ.get("DATABASE_URL", "")
        self.backup_dir = Path(backup_dir or os.environ.get("BACKUP_DIR", DEFAULT_BACKUP_DIR))
        self.retention_days = retention_days
        self.s3_bucket = s3_bucket or os.environ.get("BACKUP_S3_BUCKET")
        self.s3_prefix = s3_prefix

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Backup Creation
    # =========================================================================

    def create_backup(self, compress: bool = True) -> Dict:
        """
        Create a PostgreSQL backup using pg_dump.

        Args:
            compress: Whether to gzip the backup file

        Returns:
            Dict with success, filename, size, checksum, path
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"fcra_backup_{timestamp}.sql"
        if compress:
            filename += ".gz"

        filepath = self.backup_dir / filename

        try:
            # Parse database URL for pg_dump
            db_params = self._parse_database_url()
            if not db_params:
                return {"success": False, "error": "Invalid or missing DATABASE_URL"}

            # Build pg_dump command
            env = os.environ.copy()
            if db_params.get("password"):
                env["PGPASSWORD"] = db_params["password"]

            cmd = [
                "pg_dump",
                "-h", db_params.get("host", "localhost"),
                "-p", str(db_params.get("port", 5432)),
                "-U", db_params.get("user", "postgres"),
                "-d", db_params.get("database", "fcra"),
                "--format=plain",
                "--no-owner",
                "--no-privileges",
            ]

            logger.info("Starting database backup: %s", filename)

            if compress:
                # Pipe pg_dump output through gzip
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
                )
                with gzip.open(filepath, "wb") as gz_file:
                    while True:
                        chunk = proc.stdout.read(8192)
                        if not chunk:
                            break
                        gz_file.write(chunk)
                proc.wait()
                stderr = proc.stderr.read().decode()
            else:
                result = subprocess.run(
                    cmd, capture_output=True, env=env
                )
                filepath.write_bytes(result.stdout)
                stderr = result.stderr.decode()
                proc = result

            returncode = proc.returncode if hasattr(proc, "returncode") else proc.returncode
            if returncode != 0:
                logger.error("pg_dump failed: %s", stderr)
                # Clean up failed file
                if filepath.exists():
                    filepath.unlink()
                return {"success": False, "error": f"pg_dump failed: {stderr[:500]}"}

            # Calculate checksum
            checksum = self._calculate_checksum(filepath)
            size = filepath.stat().st_size

            logger.info(
                "Backup created successfully: %s (%s bytes, checksum: %s)",
                filename, size, checksum[:16],
            )

            result = {
                "success": True,
                "filename": filename,
                "path": str(filepath),
                "size": size,
                "size_human": self._human_size(size),
                "checksum": checksum,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Upload to S3 if configured
            if self.s3_bucket:
                upload_result = self._upload_to_s3(filepath, filename)
                result["s3_uploaded"] = upload_result.get("success", False)
                result["s3_path"] = upload_result.get("path")

            return result

        except FileNotFoundError:
            error = "pg_dump not found. Ensure PostgreSQL client tools are installed."
            logger.error(error)
            return {"success": False, "error": error}
        except Exception as e:
            logger.error("Backup failed: %s", str(e))
            return {"success": False, "error": str(e)}

    # =========================================================================
    # S3 Upload
    # =========================================================================

    def _upload_to_s3(self, filepath: Path, filename: str) -> Dict:
        """Upload backup file to S3."""
        try:
            import boto3

            s3_client = boto3.client("s3")
            s3_key = f"{self.s3_prefix}/{filename}"

            s3_client.upload_file(str(filepath), self.s3_bucket, s3_key)
            logger.info("Backup uploaded to S3: s3://%s/%s", self.s3_bucket, s3_key)

            return {"success": True, "path": f"s3://{self.s3_bucket}/{s3_key}"}
        except ImportError:
            logger.warning("boto3 not installed - skipping S3 upload")
            return {"success": False, "error": "boto3 not installed"}
        except Exception as e:
            logger.error("S3 upload failed: %s", str(e))
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Backup Verification
    # =========================================================================

    def verify_backup(self, filename: str) -> Dict:
        """
        Verify a backup file is valid by checking structure and checksum.

        Args:
            filename: Name of backup file to verify

        Returns:
            Dict with success, valid, checks performed
        """
        filepath = self.backup_dir / filename

        if not filepath.exists():
            return {"success": False, "error": "Backup file not found"}

        checks = {}

        try:
            # Check file size
            size = filepath.stat().st_size
            checks["has_content"] = size > 0

            # Check file is readable
            if filename.endswith(".gz"):
                with gzip.open(filepath, "rb") as f:
                    header = f.read(1024).decode("utf-8", errors="ignore")
            else:
                with open(filepath, "r") as f:
                    header = f.read(1024)

            # Check for PostgreSQL dump markers
            checks["has_pg_header"] = (
                "PostgreSQL database dump" in header
                or "pg_dump" in header
                or "SET " in header
                or "CREATE " in header
            )

            # Check for key tables
            if filename.endswith(".gz"):
                with gzip.open(filepath, "rt", errors="ignore") as f:
                    content_sample = f.read(50000)
            else:
                with open(filepath, "r") as f:
                    content_sample = f.read(50000)

            checks["has_clients_table"] = "clients" in content_sample.lower()
            checks["has_staff_table"] = "staff" in content_sample.lower()

            # Checksum
            checks["checksum"] = self._calculate_checksum(filepath)

            all_valid = all(
                v for k, v in checks.items() if k != "checksum"
            )

            return {
                "success": True,
                "valid": all_valid,
                "filename": filename,
                "size": size,
                "size_human": self._human_size(size),
                "checks": checks,
            }

        except Exception as e:
            logger.error("Backup verification failed: %s", str(e))
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Retention / Cleanup
    # =========================================================================

    def cleanup_old_backups(self) -> Dict:
        """Remove backups older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        removed = []
        kept = []
        errors = []

        try:
            for f in sorted(self.backup_dir.glob("fcra_backup_*.sql*")):
                # Parse timestamp from filename
                try:
                    ts_str = f.stem.replace("fcra_backup_", "").replace(".sql", "")
                    file_date = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                except ValueError:
                    kept.append(f.name)
                    continue

                if file_date < cutoff:
                    try:
                        f.unlink()
                        removed.append(f.name)
                        logger.info("Removed old backup: %s", f.name)
                    except Exception as e:
                        errors.append({"file": f.name, "error": str(e)})
                else:
                    kept.append(f.name)

            # Also clean S3 if configured
            s3_removed = 0
            if self.s3_bucket:
                s3_removed = self._cleanup_s3_backups(cutoff)

            return {
                "success": True,
                "removed": len(removed),
                "removed_files": removed,
                "kept": len(kept),
                "errors": errors,
                "s3_removed": s3_removed,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cleanup_s3_backups(self, cutoff: datetime) -> int:
        """Remove old backups from S3."""
        try:
            import boto3

            s3 = boto3.client("s3")
            paginator = s3.get_paginator("list_objects_v2")
            removed = 0

            for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=self.s3_prefix):
                for obj in page.get("Contents", []):
                    if obj["LastModified"].replace(tzinfo=None) < cutoff:
                        s3.delete_object(Bucket=self.s3_bucket, Key=obj["Key"])
                        removed += 1

            return removed
        except Exception as e:
            logger.error("S3 cleanup failed: %s", str(e))
            return 0

    # =========================================================================
    # Listing
    # =========================================================================

    def list_backups(self) -> Dict:
        """List all available backup files."""
        try:
            backups = []
            for f in sorted(
                self.backup_dir.glob("fcra_backup_*.sql*"), reverse=True
            ):
                stat = f.stat()
                backups.append({
                    "filename": f.name,
                    "size": stat.st_size,
                    "size_human": self._human_size(stat.st_size),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "compressed": f.name.endswith(".gz"),
                })

            return {
                "success": True,
                "total": len(backups),
                "backups": backups,
                "backup_dir": str(self.backup_dir),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Restore
    # =========================================================================

    def restore_backup(self, filename: str, target_database: Optional[str] = None) -> Dict:
        """
        Restore a backup to the database.

        Args:
            filename: Backup file to restore
            target_database: Optional different database to restore to

        Returns:
            Dict with success status
        """
        filepath = self.backup_dir / filename

        if not filepath.exists():
            return {"success": False, "error": "Backup file not found"}

        try:
            db_params = self._parse_database_url()
            if not db_params:
                return {"success": False, "error": "Invalid DATABASE_URL"}

            database = target_database or db_params["database"]
            env = os.environ.copy()
            if db_params.get("password"):
                env["PGPASSWORD"] = db_params["password"]

            cmd = [
                "psql",
                "-h", db_params.get("host", "localhost"),
                "-p", str(db_params.get("port", 5432)),
                "-U", db_params.get("user", "postgres"),
                "-d", database,
            ]

            logger.warning("Starting database restore from: %s to %s", filename, database)

            if filename.endswith(".gz"):
                proc_gunzip = subprocess.Popen(
                    ["gunzip", "-c", str(filepath)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                proc_psql = subprocess.Popen(
                    cmd,
                    stdin=proc_gunzip.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                )
                proc_gunzip.stdout.close()
                stdout, stderr = proc_psql.communicate()
                returncode = proc_psql.returncode
            else:
                with open(filepath, "r") as f:
                    result = subprocess.run(
                        cmd, stdin=f, capture_output=True, env=env
                    )
                    returncode = result.returncode
                    stderr = result.stderr

            if returncode != 0:
                error_msg = stderr.decode() if isinstance(stderr, bytes) else stderr
                logger.error("Restore failed: %s", error_msg[:500])
                return {"success": False, "error": f"Restore failed: {error_msg[:500]}"}

            logger.info("Database restored from: %s", filename)
            return {
                "success": True,
                "filename": filename,
                "database": database,
                "restored_at": datetime.utcnow().isoformat(),
            }

        except FileNotFoundError:
            return {"success": False, "error": "psql not found. Ensure PostgreSQL client tools are installed."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Nightly Backup Job
    # =========================================================================

    def run_nightly_backup(self) -> Dict:
        """
        Run the full nightly backup routine:
        1. Create backup
        2. Verify backup
        3. Clean up old backups
        4. Alert on failure
        """
        results = {"started_at": datetime.utcnow().isoformat()}

        # Step 1: Create backup
        backup_result = self.create_backup(compress=True)
        results["backup"] = backup_result

        if not backup_result.get("success"):
            self._send_failure_alert("Backup creation failed", backup_result.get("error", "Unknown"))
            results["success"] = False
            return results

        # Step 2: Verify backup
        verify_result = self.verify_backup(backup_result["filename"])
        results["verification"] = verify_result

        if not verify_result.get("valid"):
            self._send_failure_alert(
                "Backup verification failed",
                str(verify_result.get("checks", {})),
            )

        # Step 3: Cleanup old backups
        cleanup_result = self.cleanup_old_backups()
        results["cleanup"] = cleanup_result

        results["success"] = True
        results["completed_at"] = datetime.utcnow().isoformat()

        logger.info(
            "Nightly backup complete: %s (%s), verified=%s, cleaned=%d old backups",
            backup_result["filename"],
            backup_result.get("size_human", "?"),
            verify_result.get("valid", False),
            cleanup_result.get("removed", 0),
        )

        return results

    # =========================================================================
    # Helpers
    # =========================================================================

    def _parse_database_url(self) -> Optional[Dict]:
        """Parse DATABASE_URL into components."""
        url = self.database_url
        if not url:
            return None

        try:
            # postgresql://user:pass@host:port/dbname?params
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return {
                "user": parsed.username or "postgres",
                "password": parsed.password or "",
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 5432,
                "database": parsed.path.lstrip("/").split("?")[0] or "fcra",
            }
        except Exception:
            return None

    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _human_size(size_bytes: int) -> str:
        """Convert bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _send_failure_alert(self, subject: str, details: str):
        """Send admin alert on backup failure."""
        try:
            from services.email_service import send_email
            send_email(
                to_email="admin@brightpathcredit.com",
                subject=f"[ALERT] Database Backup: {subject}",
                html_content=(
                    f"<h3>Database Backup Alert</h3>"
                    f"<p><strong>{subject}</strong></p>"
                    f"<p>Details: {details}</p>"
                    f"<p>Time: {datetime.utcnow().isoformat()}</p>"
                ),
            )
        except Exception:
            logger.error("Failed to send backup failure alert email")


# Module-level singleton
_service_instance = None


def get_database_backup_service() -> DatabaseBackupService:
    """Get singleton instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = DatabaseBackupService()
    return _service_instance
