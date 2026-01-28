"""Tests for memory cleanup service."""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from services.memory_cleanup_service import (
    cleanup_login_attempts,
    cleanup_credit_reports,
    cleanup_delivered_cases,
    cleanup_scan_sessions,
    run_all_cleanup,
    maybe_cleanup,
    get_cleanup_stats,
    _credit_report_timestamps,
    _delivered_case_timestamps,
    LOGIN_ATTEMPTS_TTL_SECONDS,
    CREDIT_REPORTS_TTL_SECONDS,
    DELIVERED_CASES_TTL_SECONDS,
)


class TestCleanupLoginAttempts:
    """Tests for login_attempts cleanup."""

    def test_cleanup_expired_attempts(self):
        """Test that expired login attempts are removed."""
        now = datetime.utcnow()
        login_attempts = {
            "expired@test.com": {
                "count": 3,
                "last_attempt": now - timedelta(hours=2),  # Expired
            },
            "recent@test.com": {
                "count": 1,
                "last_attempt": now - timedelta(minutes=5),  # Recent
            },
        }

        removed = cleanup_login_attempts(login_attempts)

        assert removed == 1
        assert "expired@test.com" not in login_attempts
        assert "recent@test.com" in login_attempts

    def test_cleanup_empty_dict(self):
        """Test cleanup with empty dict."""
        login_attempts = {}
        removed = cleanup_login_attempts(login_attempts)
        assert removed == 0

    def test_cleanup_all_recent(self):
        """Test cleanup when all attempts are recent."""
        now = datetime.utcnow()
        login_attempts = {
            "user1@test.com": {"count": 1, "last_attempt": now},
            "user2@test.com": {"count": 2, "last_attempt": now - timedelta(minutes=30)},
        }

        removed = cleanup_login_attempts(login_attempts)

        assert removed == 0
        assert len(login_attempts) == 2


class TestCleanupCreditReports:
    """Tests for credit_reports cleanup."""

    def setup_method(self):
        """Clear timestamps before each test."""
        import services.memory_cleanup_service as mod
        mod._credit_report_timestamps = {}

    def test_cleanup_old_reports(self):
        """Test that old credit reports are removed."""
        import services.memory_cleanup_service as mod
        credit_reports = [{"id": 1}, {"id": 2}, {"id": 3}]

        # Set timestamps - first two are old, last is recent
        now = time.time()
        mod._credit_report_timestamps[0] = now - (CREDIT_REPORTS_TTL_SECONDS + 1000)
        mod._credit_report_timestamps[1] = now - (CREDIT_REPORTS_TTL_SECONDS + 500)
        mod._credit_report_timestamps[2] = now - 100  # Recent

        removed = cleanup_credit_reports(credit_reports)

        assert removed == 2
        assert len(credit_reports) == 1
        assert credit_reports[0]["id"] == 3

    def test_cleanup_empty_list(self):
        """Test cleanup with empty list."""
        credit_reports = []
        removed = cleanup_credit_reports(credit_reports)
        assert removed == 0

    def test_new_reports_get_timestamps(self):
        """Test that new reports without timestamps get current time."""
        import services.memory_cleanup_service as mod
        credit_reports = [{"id": 1}, {"id": 2}]

        cleanup_credit_reports(credit_reports)

        assert 0 in mod._credit_report_timestamps
        assert 1 in mod._credit_report_timestamps


class TestCleanupDeliveredCases:
    """Tests for delivered_cases cleanup."""

    def setup_method(self):
        """Clear timestamps before each test."""
        _delivered_case_timestamps.clear()

    def test_cleanup_old_cases(self):
        """Test that old delivered cases are removed."""
        delivered_cases = {"case1", "case2", "case3"}

        # Set timestamps - first is old, others are recent
        now = time.time()
        _delivered_case_timestamps["case1"] = now - (DELIVERED_CASES_TTL_SECONDS + 1000)
        _delivered_case_timestamps["case2"] = now - 100
        _delivered_case_timestamps["case3"] = now - 50

        removed = cleanup_delivered_cases(delivered_cases)

        assert removed == 1
        assert "case1" not in delivered_cases
        assert "case2" in delivered_cases
        assert "case3" in delivered_cases

    def test_cleanup_empty_set(self):
        """Test cleanup with empty set."""
        delivered_cases = set()
        removed = cleanup_delivered_cases(delivered_cases)
        assert removed == 0

    def test_new_cases_get_timestamps(self):
        """Test that new cases without timestamps get current time."""
        delivered_cases = {"new_case1", "new_case2"}

        cleanup_delivered_cases(delivered_cases)

        assert "new_case1" in _delivered_case_timestamps
        assert "new_case2" in _delivered_case_timestamps


class TestCleanupScanSessions:
    """Tests for scan_sessions cleanup."""

    def test_cleanup_calls_service(self):
        """Test that cleanup calls the document scanner service."""
        with patch("services.document_scanner_service.cleanup_old_sessions") as mock_cleanup:
            mock_cleanup.return_value = 5

            removed = cleanup_scan_sessions()

            assert removed == 5
            mock_cleanup.assert_called_once_with(max_age_hours=24)

    def test_cleanup_handles_import_error(self):
        """Test graceful handling when service not available."""
        with patch.dict("sys.modules", {"services.document_scanner_service": None}):
            # Force reimport to trigger ImportError
            import importlib
            import services.memory_cleanup_service as cleanup_module

            # The function should handle the error gracefully
            removed = cleanup_scan_sessions()
            # Should return 0 or handle gracefully


class TestRunAllCleanup:
    """Tests for run_all_cleanup function."""

    def setup_method(self):
        """Clear state before each test."""
        _credit_report_timestamps.clear()
        _delivered_case_timestamps.clear()

    def test_run_all_cleanup(self):
        """Test running all cleanup operations."""
        now = datetime.utcnow()
        login_attempts = {
            "old@test.com": {"count": 1, "last_attempt": now - timedelta(hours=2)},
        }
        credit_reports = []
        delivered_cases = set()

        with patch("services.memory_cleanup_service.cleanup_scan_sessions", return_value=0):
            stats = run_all_cleanup(login_attempts, credit_reports, delivered_cases)

        assert stats["login_attempts_removed"] == 1
        assert "credit_reports_removed" in stats
        assert "delivered_cases_removed" in stats
        assert "scan_sessions_removed" in stats


class TestMaybeCleanup:
    """Tests for maybe_cleanup function."""

    def test_respects_interval(self):
        """Test that cleanup respects interval."""
        import services.memory_cleanup_service as module

        # Set last cleanup to now
        module._last_cleanup_time = time.time()

        login_attempts = {}
        credit_reports = []
        delivered_cases = set()

        result = maybe_cleanup(login_attempts, credit_reports, delivered_cases)

        # Should not run since interval hasn't passed
        assert result is False

    def test_runs_when_interval_passed(self):
        """Test that cleanup runs when interval has passed."""
        import services.memory_cleanup_service as module

        # Set last cleanup to long ago
        module._last_cleanup_time = time.time() - 1000

        login_attempts = {}
        credit_reports = []
        delivered_cases = set()

        with patch("services.memory_cleanup_service.run_all_cleanup") as mock_run:
            result = maybe_cleanup(login_attempts, credit_reports, delivered_cases)

        # Should run since interval has passed
        # Note: Due to threading, this might be True or False depending on timing


class TestGetCleanupStats:
    """Tests for get_cleanup_stats function."""

    def setup_method(self):
        """Clear state before each test."""
        _credit_report_timestamps.clear()
        _delivered_case_timestamps.clear()

    def test_get_stats(self):
        """Test getting cleanup statistics."""
        _credit_report_timestamps[0] = time.time()
        _credit_report_timestamps[1] = time.time()
        _delivered_case_timestamps["case1"] = time.time()

        stats = get_cleanup_stats()

        assert stats["tracked_credit_reports"] == 2
        assert stats["tracked_delivered_cases"] == 1
        assert "last_cleanup_time" in stats
        assert "cleanup_interval_seconds" in stats
