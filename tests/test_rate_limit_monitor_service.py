"""
Tests for Rate Limit Monitoring Service

Tests cover:
- Violation recording
- IP blocking
- Alert triggering
- Statistics and metrics
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from services.rate_limit_monitor_service import (
    IPStats,
    RateLimitMonitor,
    ViolationRecord,
    get_rate_limit_monitor,
    init_rate_limit_monitoring,
    is_ip_blocked,
    record_violation,
)


# ============================================================================
# ViolationRecord Tests
# ============================================================================

class TestViolationRecord:
    """Tests for ViolationRecord dataclass."""

    def test_create_violation_record(self):
        """Test creating a violation record."""
        record = ViolationRecord(
            ip_address="192.168.1.1",
            endpoint="/api/login",
            timestamp=datetime.utcnow(),
            user_agent="Mozilla/5.0",
            key="192.168.1.1",
        )

        assert record.ip_address == "192.168.1.1"
        assert record.endpoint == "/api/login"
        assert record.user_agent == "Mozilla/5.0"


# ============================================================================
# IPStats Tests
# ============================================================================

class TestIPStats:
    """Tests for IPStats dataclass."""

    def test_create_ip_stats(self):
        """Test creating IP stats."""
        stats = IPStats(
            ip_address="10.0.0.1",
            total_violations=5,
            violations_in_window=3,
        )

        assert stats.ip_address == "10.0.0.1"
        assert stats.total_violations == 5
        assert stats.blocked is False

    def test_ip_stats_to_dict(self):
        """Test converting stats to dictionary."""
        now = datetime.utcnow()
        stats = IPStats(
            ip_address="10.0.0.1",
            total_violations=5,
            first_violation=now,
            last_violation=now,
        )
        stats.endpoints_hit.add("/api/login")

        result = stats.to_dict()

        assert result["ip_address"] == "10.0.0.1"
        assert result["total_violations"] == 5
        assert "/api/login" in result["endpoints_hit"]


# ============================================================================
# RateLimitMonitor Tests
# ============================================================================

class TestRateLimitMonitor:
    """Tests for RateLimitMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create a fresh monitor for each test."""
        return RateLimitMonitor(
            violation_threshold=5,
            block_duration_minutes=30,
            violation_window_minutes=5,
            alert_threshold=3,
        )

    def test_monitor_creation(self, monitor):
        """Test creating a monitor."""
        assert monitor._violation_threshold == 5
        assert monitor._alert_threshold == 3
        assert monitor._total_violations == 0

    def test_record_violation(self, monitor):
        """Test recording a violation."""
        blocked = monitor.record_violation("192.168.1.1", "/api/login")

        assert blocked is False
        assert monitor._total_violations == 1

        stats = monitor.get_ip_stats("192.168.1.1")
        assert stats is not None
        assert stats["total_violations"] == 1
        assert "/api/login" in stats["endpoints_hit"]

    def test_multiple_violations_same_ip(self, monitor):
        """Test multiple violations from same IP."""
        for _ in range(3):
            monitor.record_violation("192.168.1.1", "/api/login")

        stats = monitor.get_ip_stats("192.168.1.1")
        assert stats["total_violations"] == 3
        assert stats["violations_in_window"] == 3

    def test_violations_different_endpoints(self, monitor):
        """Test violations to different endpoints."""
        monitor.record_violation("192.168.1.1", "/api/login")
        monitor.record_violation("192.168.1.1", "/api/users")
        monitor.record_violation("192.168.1.1", "/api/data")

        stats = monitor.get_ip_stats("192.168.1.1")
        assert len(stats["endpoints_hit"]) == 3

    def test_is_blocked_initially_false(self, monitor):
        """Test that IPs are not blocked initially."""
        assert monitor.is_blocked("192.168.1.1") is False

    def test_auto_block_after_threshold(self, monitor):
        """Test that IP is blocked after exceeding threshold."""
        for i in range(5):
            blocked = monitor.record_violation("192.168.1.1", "/api/login")

        assert blocked is True
        assert monitor.is_blocked("192.168.1.1") is True

    def test_manual_unblock(self, monitor):
        """Test manually unblocking an IP."""
        # Block the IP
        for _ in range(5):
            monitor.record_violation("192.168.1.1", "/api/login")

        assert monitor.is_blocked("192.168.1.1") is True

        # Unblock
        result = monitor.unblock_ip("192.168.1.1")
        assert result is True
        assert monitor.is_blocked("192.168.1.1") is False

    def test_permanent_blocklist(self, monitor):
        """Test permanent blocklist."""
        monitor.add_to_blocklist("10.0.0.1")

        assert monitor.is_blocked("10.0.0.1") is True

        # Can be removed
        monitor.unblock_ip("10.0.0.1")
        assert monitor.is_blocked("10.0.0.1") is False

    def test_get_blocked_ips(self, monitor):
        """Test getting list of blocked IPs."""
        # Block an IP
        for _ in range(5):
            monitor.record_violation("192.168.1.1", "/api/login")

        blocked = monitor.get_blocked_ips()
        assert len(blocked) == 1
        assert blocked[0]["ip_address"] == "192.168.1.1"

    def test_get_top_offenders(self, monitor):
        """Test getting top offenders."""
        # Multiple IPs with different violation counts
        for _ in range(3):
            monitor.record_violation("192.168.1.1", "/api/login")
        for _ in range(5):
            monitor.record_violation("192.168.1.2", "/api/login")
        for _ in range(1):
            monitor.record_violation("192.168.1.3", "/api/login")

        top = monitor.get_top_offenders(limit=2)

        # Note: 192.168.1.2 got blocked (5 violations) so it should be first
        assert len(top) == 2
        assert top[0]["ip_address"] == "192.168.1.2"
        assert top[0]["total_violations"] == 5

    def test_get_recent_violations(self, monitor):
        """Test getting recent violations."""
        monitor.record_violation("192.168.1.1", "/api/login")
        monitor.record_violation("192.168.1.2", "/api/users")

        recent = monitor.get_recent_violations(limit=10)

        assert len(recent) == 2
        # Most recent first
        assert recent[0]["ip_address"] == "192.168.1.2"

    def test_get_stats(self, monitor):
        """Test getting overall stats."""
        monitor.record_violation("192.168.1.1", "/api/login")
        monitor.record_violation("192.168.1.2", "/api/login")

        stats = monitor.get_stats()

        assert stats["total_violations"] == 2
        assert stats["unique_ips"] == 2
        assert stats["violation_threshold"] == 5


# ============================================================================
# Alert Tests
# ============================================================================

class TestAlerts:
    """Tests for alert functionality."""

    @pytest.fixture
    def monitor(self):
        """Create a monitor with low thresholds for testing."""
        return RateLimitMonitor(
            violation_threshold=5,
            alert_threshold=3,
        )

    def test_alert_callback_triggered(self, monitor):
        """Test that alert callback is triggered."""
        callback = MagicMock()
        monitor.add_alert_callback(callback)

        # Record enough violations to trigger alert (3)
        for _ in range(3):
            monitor.record_violation("192.168.1.1", "/api/login")

        assert callback.called

    def test_block_triggers_alert(self, monitor):
        """Test that blocking triggers an alert."""
        callback = MagicMock()
        monitor.add_alert_callback(callback)

        # Record enough violations to trigger block (5)
        for _ in range(5):
            monitor.record_violation("192.168.1.1", "/api/login")

        # Should have been called for threshold_approaching and ip_blocked
        assert callback.call_count >= 2


# ============================================================================
# Prometheus Metrics Tests
# ============================================================================

class TestPrometheusMetrics:
    """Tests for Prometheus metrics export."""

    @pytest.fixture
    def monitor(self):
        """Create a monitor for testing."""
        return RateLimitMonitor()

    def test_prometheus_format(self, monitor):
        """Test Prometheus metrics format."""
        monitor.record_violation("192.168.1.1", "/api/login")

        metrics = monitor.get_prometheus_metrics()

        assert "rate_limit_violations_total" in metrics
        assert "rate_limit_blocked_ips" in metrics
        assert "# HELP" in metrics
        assert "# TYPE" in metrics

    def test_prometheus_metrics_values(self, monitor):
        """Test that metrics have correct values."""
        for _ in range(3):
            monitor.record_violation("192.168.1.1", "/api/login")

        metrics = monitor.get_prometheus_metrics()

        assert "rate_limit_violations_total 3" in metrics


# ============================================================================
# Global Functions Tests
# ============================================================================

class TestGlobalFunctions:
    """Tests for module-level convenience functions."""

    def test_init_rate_limit_monitoring(self):
        """Test initializing rate limit monitoring."""
        import services.rate_limit_monitor_service as svc
        original = svc._rate_limit_monitor
        svc._rate_limit_monitor = None

        try:
            monitor = init_rate_limit_monitoring()
            assert monitor is not None
            assert svc._rate_limit_monitor is monitor
        finally:
            if svc._rate_limit_monitor:
                svc._rate_limit_monitor.stop_cleanup_thread()
            svc._rate_limit_monitor = original

    def test_is_ip_blocked_no_monitor(self):
        """Test is_ip_blocked when monitor not initialized."""
        import services.rate_limit_monitor_service as svc
        original = svc._rate_limit_monitor
        svc._rate_limit_monitor = None

        result = is_ip_blocked("192.168.1.1")
        assert result is False

        svc._rate_limit_monitor = original

    def test_record_violation_no_monitor(self):
        """Test record_violation when monitor not initialized."""
        import services.rate_limit_monitor_service as svc
        original = svc._rate_limit_monitor
        svc._rate_limit_monitor = None

        result = record_violation("192.168.1.1", "/api/login")
        assert result is False

        svc._rate_limit_monitor = original


# ============================================================================
# Cleanup Tests
# ============================================================================

class TestCleanup:
    """Tests for data cleanup."""

    def test_cleanup_old_data(self):
        """Test cleaning up old violation records."""
        monitor = RateLimitMonitor()

        # Add a violation
        monitor.record_violation("192.168.1.1", "/api/login")

        # Manually age the violation
        if monitor._violations:
            monitor._violations[0].timestamp = datetime.utcnow() - timedelta(hours=25)

        # Cleanup
        removed = monitor.cleanup_old_data(max_age_hours=24)

        assert removed == 1
        assert len(monitor._violations) == 0
