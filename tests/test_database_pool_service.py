"""
Tests for Database Pool Monitoring Service

Tests cover:
- Pool metrics collection
- Event listener registration
- Alert threshold detection
- Prometheus metrics export
- Background monitoring
"""

import threading
import time
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from services.database_pool_service import (
    DatabasePoolMonitor,
    PoolMetrics,
    get_pool_metrics,
    get_pool_prometheus,
    init_pool_monitoring,
)


# ============================================================================
# PoolMetrics Tests
# ============================================================================

class TestPoolMetrics:
    """Tests for PoolMetrics dataclass."""

    def test_pool_metrics_creation(self):
        """Test creating a PoolMetrics instance."""
        metrics = PoolMetrics(
            timestamp=datetime.utcnow(),
            pool_size=10,
            checked_out=5,
            overflow=2,
            checked_in=5,
            total_connections=12,
            usage_percent=50.0,
        )

        assert metrics.pool_size == 10
        assert metrics.checked_out == 5
        assert metrics.overflow == 2
        assert metrics.usage_percent == 50.0

    def test_pool_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        now = datetime.utcnow()
        metrics = PoolMetrics(
            timestamp=now,
            pool_size=10,
            checked_out=3,
            overflow=0,
            checked_in=7,
            total_connections=10,
            usage_percent=30.0,
            total_checkouts=100,
            total_checkins=97,
        )

        result = metrics.to_dict()

        assert result["pool_size"] == 10
        assert result["checked_out"] == 3
        assert result["usage_percent"] == 30.0
        assert result["total_checkouts"] == 100
        assert result["timestamp"] == now.isoformat()

    def test_pool_metrics_to_prometheus(self):
        """Test exporting metrics in Prometheus format."""
        metrics = PoolMetrics(
            timestamp=datetime.utcnow(),
            pool_size=10,
            checked_out=5,
            overflow=2,
            checked_in=5,
            total_connections=12,
            usage_percent=50.0,
            total_checkouts=1000,
            total_checkins=995,
            total_overflows=10,
            total_invalidations=2,
            total_timeouts=1,
        )

        result = metrics.to_prometheus()

        assert "db_pool_size 10" in result
        assert "db_pool_checked_out 5" in result
        assert "db_pool_overflow 2" in result
        assert "db_pool_usage_percent 50.00" in result
        assert "db_pool_checkouts_total 1000" in result
        assert "db_pool_timeouts_total 1" in result
        assert "# HELP" in result
        assert "# TYPE" in result


# ============================================================================
# DatabasePoolMonitor Tests
# ============================================================================

class TestDatabasePoolMonitor:
    """Tests for DatabasePoolMonitor class."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock SQLAlchemy engine."""
        engine = MagicMock()
        pool = MagicMock()

        # Mock pool methods
        pool.size.return_value = 10
        pool.checkedout.return_value = 3
        pool.overflow.return_value = 0
        pool.checkedin.return_value = 7
        pool._max_overflow = 20

        engine.pool = pool

        return engine

    def test_monitor_creation(self, mock_engine):
        """Test creating a pool monitor."""
        monitor = DatabasePoolMonitor(mock_engine, log_checkouts=False)

        assert monitor._engine == mock_engine
        assert monitor._alert_threshold == 0.8
        assert monitor._total_checkouts == 0

    def test_get_pool_status(self, mock_engine):
        """Test getting pool status."""
        monitor = DatabasePoolMonitor(mock_engine, log_checkouts=False)

        status = monitor.get_pool_status()

        assert status["pool_size"] == 10
        assert status["checked_out"] == 3
        assert status["overflow"] == 0
        assert status["checked_in"] == 7

    def test_get_metrics(self, mock_engine):
        """Test getting pool metrics."""
        monitor = DatabasePoolMonitor(mock_engine, log_checkouts=False)

        metrics = monitor.get_metrics()

        assert isinstance(metrics, PoolMetrics)
        assert metrics.pool_size == 10
        assert metrics.checked_out == 3
        # Usage = 3 / (10 + 20) * 100 = 10%
        assert metrics.usage_percent == 10.0

    def test_get_metrics_no_pool(self):
        """Test getting metrics when no pool is available."""
        engine = MagicMock()
        engine.pool = None

        monitor = DatabasePoolMonitor(engine, log_checkouts=False)
        monitor._pool = None

        status = monitor.get_pool_status()
        assert status["pool_size"] == 0

    def test_add_alert_callback(self, mock_engine):
        """Test adding alert callbacks."""
        monitor = DatabasePoolMonitor(mock_engine, log_checkouts=False)
        callback = MagicMock()

        monitor.add_alert_callback(callback)

        assert callback in monitor._alert_callbacks

    def test_record_timeout(self, mock_engine):
        """Test recording timeout errors."""
        monitor = DatabasePoolMonitor(mock_engine, log_checkouts=False)

        assert monitor._total_timeouts == 0

        monitor.record_timeout()
        assert monitor._total_timeouts == 1

        monitor.record_timeout()
        assert monitor._total_timeouts == 2

    def test_get_prometheus_metrics(self, mock_engine):
        """Test getting Prometheus format metrics."""
        monitor = DatabasePoolMonitor(mock_engine, log_checkouts=False)

        result = monitor.get_prometheus_metrics()

        assert "db_pool_size" in result
        assert "db_pool_checked_out" in result
        assert "# HELP" in result

    def test_get_history(self, mock_engine):
        """Test getting metrics history."""
        monitor = DatabasePoolMonitor(mock_engine, log_checkouts=False)

        # Initially empty
        history = monitor.get_history()
        assert history == []

        # Add some metrics manually
        metrics = monitor.get_metrics()
        monitor._metrics_history.append(metrics)

        history = monitor.get_history()
        assert len(history) == 1
        assert history[0]["pool_size"] == 10


# ============================================================================
# Alert Tests
# ============================================================================

class TestAlerts:
    """Tests for alert functionality."""

    @pytest.fixture
    def high_usage_engine(self):
        """Create engine with high pool usage."""
        engine = MagicMock()
        pool = MagicMock()

        pool.size.return_value = 10
        pool.checkedout.return_value = 25  # High usage
        pool.overflow.return_value = 5
        pool.checkedin.return_value = 0
        pool._max_overflow = 20

        engine.pool = pool
        return engine

    def test_high_usage_alert(self, high_usage_engine):
        """Test that high usage triggers alert."""
        monitor = DatabasePoolMonitor(
            high_usage_engine,
            alert_threshold=0.8,
            log_checkouts=False
        )
        callback = MagicMock()
        monitor.add_alert_callback(callback)

        metrics = monitor.get_metrics()
        monitor._check_alerts(metrics)

        # Should have called the callback
        assert callback.called

    def test_overflow_alert(self, high_usage_engine):
        """Test that overflow triggers alert."""
        monitor = DatabasePoolMonitor(
            high_usage_engine,
            alert_threshold=0.99,  # High threshold to not trigger usage alert
            log_checkouts=False
        )
        callback = MagicMock()
        monitor.add_alert_callback(callback)

        metrics = monitor.get_metrics()
        monitor._check_alerts(metrics)

        # Should have called for overflow
        assert callback.called

    def test_alert_cooldown(self, high_usage_engine):
        """Test that alerts respect cooldown period."""
        monitor = DatabasePoolMonitor(
            high_usage_engine,
            alert_threshold=0.5,
            log_checkouts=False
        )
        monitor._alert_cooldown_seconds = 300
        callback = MagicMock()
        monitor.add_alert_callback(callback)

        metrics = monitor.get_metrics()

        # First alert should fire
        monitor._check_alerts(metrics)
        first_call_count = callback.call_count

        # Second alert should be blocked by cooldown
        monitor._check_alerts(metrics)

        assert callback.call_count == first_call_count


# ============================================================================
# Background Monitoring Tests
# ============================================================================

class TestBackgroundMonitoring:
    """Tests for background monitoring."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock engine."""
        engine = MagicMock()
        pool = MagicMock()
        pool.size.return_value = 10
        pool.checkedout.return_value = 2
        pool.overflow.return_value = 0
        pool.checkedin.return_value = 8
        pool._max_overflow = 20
        engine.pool = pool
        return engine

    def test_start_monitoring(self, mock_engine):
        """Test starting background monitoring."""
        monitor = DatabasePoolMonitor(
            mock_engine,
            metrics_interval=1,
            log_checkouts=False
        )

        monitor.start()

        assert monitor._monitoring_thread is not None
        assert monitor._monitoring_thread.is_alive()

        # Clean up
        monitor.stop()

    def test_stop_monitoring(self, mock_engine):
        """Test stopping background monitoring."""
        monitor = DatabasePoolMonitor(
            mock_engine,
            metrics_interval=1,
            log_checkouts=False
        )

        monitor.start()
        time.sleep(0.1)  # Let it start

        monitor.stop()
        time.sleep(0.1)  # Let it stop

        assert monitor._stop_monitoring is True

    def test_double_start(self, mock_engine):
        """Test that double start doesn't create multiple threads."""
        monitor = DatabasePoolMonitor(
            mock_engine,
            metrics_interval=1,
            log_checkouts=False
        )

        monitor.start()
        thread1 = monitor._monitoring_thread

        monitor.start()  # Second start
        thread2 = monitor._monitoring_thread

        assert thread1 is thread2

        monitor.stop()


# ============================================================================
# Global Functions Tests
# ============================================================================

class TestGlobalFunctions:
    """Tests for module-level convenience functions."""

    def test_get_pool_metrics_not_initialized(self):
        """Test get_pool_metrics when not initialized."""
        # Reset global
        import services.database_pool_service as svc
        original = svc._pool_monitor
        svc._pool_monitor = None

        result = get_pool_metrics()
        assert "error" in result

        svc._pool_monitor = original

    def test_get_pool_prometheus_not_initialized(self):
        """Test get_pool_prometheus when not initialized."""
        import services.database_pool_service as svc
        original = svc._pool_monitor
        svc._pool_monitor = None

        result = get_pool_prometheus()
        assert "not initialized" in result

        svc._pool_monitor = original

    def test_init_pool_monitoring(self):
        """Test initializing pool monitoring."""
        import services.database_pool_service as svc
        original = svc._pool_monitor
        svc._pool_monitor = None

        engine = MagicMock()
        pool = MagicMock()
        pool.size.return_value = 5
        pool.checkedout.return_value = 1
        pool.overflow.return_value = 0
        pool.checkedin.return_value = 4
        pool._max_overflow = 10
        engine.pool = pool

        try:
            monitor = init_pool_monitoring(engine, start_background=False)
            assert monitor is not None
            assert svc._pool_monitor is monitor
        finally:
            if svc._pool_monitor:
                svc._pool_monitor.stop()
            svc._pool_monitor = original
