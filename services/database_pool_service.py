"""
Database Connection Pool Monitoring Service

Provides metrics, monitoring, and alerts for SQLAlchemy connection pool:
- Pool usage statistics (size, checked out, overflow)
- Connection checkout/checkin event logging
- Pool exhaustion detection and alerting
- Prometheus-compatible metrics export
"""

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import event
from sqlalchemy.pool import Pool

# Configuration from environment
POOL_ALERT_THRESHOLD = float(os.environ.get("POOL_ALERT_THRESHOLD", "0.8"))  # 80% usage
POOL_METRICS_INTERVAL = int(os.environ.get("POOL_METRICS_INTERVAL", "60"))  # seconds
POOL_LOG_CHECKOUTS = os.environ.get("POOL_LOG_CHECKOUTS", "false").lower() == "true"

logger = logging.getLogger("database_pool")


@dataclass
class PoolMetrics:
    """Snapshot of connection pool metrics."""
    timestamp: datetime
    pool_size: int
    checked_out: int
    overflow: int
    checked_in: int
    total_connections: int
    usage_percent: float

    # Cumulative stats
    total_checkouts: int = 0
    total_checkins: int = 0
    total_overflows: int = 0
    total_invalidations: int = 0
    total_timeouts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "pool_size": self.pool_size,
            "checked_out": self.checked_out,
            "overflow": self.overflow,
            "checked_in": self.checked_in,
            "total_connections": self.total_connections,
            "usage_percent": round(self.usage_percent, 2),
            "total_checkouts": self.total_checkouts,
            "total_checkins": self.total_checkins,
            "total_overflows": self.total_overflows,
            "total_invalidations": self.total_invalidations,
            "total_timeouts": self.total_timeouts,
        }

    def to_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = [
            "# HELP db_pool_size Number of connections in the pool",
            "# TYPE db_pool_size gauge",
            f"db_pool_size {self.pool_size}",
            "",
            "# HELP db_pool_checked_out Number of connections currently checked out",
            "# TYPE db_pool_checked_out gauge",
            f"db_pool_checked_out {self.checked_out}",
            "",
            "# HELP db_pool_overflow Number of overflow connections",
            "# TYPE db_pool_overflow gauge",
            f"db_pool_overflow {self.overflow}",
            "",
            "# HELP db_pool_checked_in Number of connections available in pool",
            "# TYPE db_pool_checked_in gauge",
            f"db_pool_checked_in {self.checked_in}",
            "",
            "# HELP db_pool_usage_percent Pool usage percentage",
            "# TYPE db_pool_usage_percent gauge",
            f"db_pool_usage_percent {self.usage_percent:.2f}",
            "",
            "# HELP db_pool_checkouts_total Total connection checkouts",
            "# TYPE db_pool_checkouts_total counter",
            f"db_pool_checkouts_total {self.total_checkouts}",
            "",
            "# HELP db_pool_checkins_total Total connection checkins",
            "# TYPE db_pool_checkins_total counter",
            f"db_pool_checkins_total {self.total_checkins}",
            "",
            "# HELP db_pool_overflows_total Total overflow connections created",
            "# TYPE db_pool_overflows_total counter",
            f"db_pool_overflows_total {self.total_overflows}",
            "",
            "# HELP db_pool_invalidations_total Total connection invalidations",
            "# TYPE db_pool_invalidations_total counter",
            f"db_pool_invalidations_total {self.total_invalidations}",
            "",
            "# HELP db_pool_timeouts_total Total pool timeout errors",
            "# TYPE db_pool_timeouts_total counter",
            f"db_pool_timeouts_total {self.total_timeouts}",
        ]
        return "\n".join(lines)


class DatabasePoolMonitor:
    """
    Monitors SQLAlchemy connection pool and provides metrics/alerts.

    Usage:
        from database import engine
        monitor = DatabasePoolMonitor(engine)
        monitor.start()

        # Get current metrics
        metrics = monitor.get_metrics()

        # Add alert callback
        monitor.add_alert_callback(my_alert_function)
    """

    def __init__(
        self,
        engine,
        alert_threshold: float = POOL_ALERT_THRESHOLD,
        metrics_interval: int = POOL_METRICS_INTERVAL,
        log_checkouts: bool = POOL_LOG_CHECKOUTS,
    ):
        self._engine = engine
        self._pool: Optional[Pool] = engine.pool if hasattr(engine, 'pool') else None
        self._alert_threshold = alert_threshold
        self._metrics_interval = metrics_interval
        self._log_checkouts = log_checkouts

        # Cumulative counters
        self._total_checkouts = 0
        self._total_checkins = 0
        self._total_overflows = 0
        self._total_invalidations = 0
        self._total_timeouts = 0

        # Thread safety
        self._lock = threading.Lock()

        # Alert callbacks
        self._alert_callbacks: List[Callable[[PoolMetrics, str], None]] = []

        # Background monitoring
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = False

        # Alert state (prevent spam)
        self._last_alert_time: Optional[datetime] = None
        self._alert_cooldown_seconds = 300  # 5 minutes between alerts

        # Metrics history
        self._metrics_history: List[PoolMetrics] = []
        self._max_history = 60  # Keep last 60 snapshots

        # Register event listeners
        self._register_events()

    def _register_events(self) -> None:
        """Register SQLAlchemy pool event listeners."""
        if self._pool is None:
            logger.warning("No connection pool available for monitoring")
            return

        # Skip event registration for mock engines (testing)
        try:
            from sqlalchemy.engine import Engine
            if not isinstance(self._engine, Engine):
                logger.debug("Skipping event registration for non-Engine object")
                return
        except Exception:
            pass

        @event.listens_for(self._engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            with self._lock:
                self._total_checkouts += 1
            if self._log_checkouts:
                logger.debug(f"Connection checked out (total: {self._total_checkouts})")

        @event.listens_for(self._engine, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            with self._lock:
                self._total_checkins += 1
            if self._log_checkouts:
                logger.debug(f"Connection checked in (total: {self._total_checkins})")

        @event.listens_for(self._engine, "invalidate")
        def on_invalidate(dbapi_conn, connection_record, exception):
            with self._lock:
                self._total_invalidations += 1
            logger.warning(f"Connection invalidated: {exception}")

        @event.listens_for(self._engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            logger.debug("New database connection created")

        logger.info("Database pool event listeners registered")

    def get_pool_status(self) -> Dict[str, int]:
        """Get current pool status."""
        if self._pool is None:
            return {
                "pool_size": 0,
                "checked_out": 0,
                "overflow": 0,
                "checked_in": 0,
            }

        return {
            "pool_size": self._pool.size(),
            "checked_out": self._pool.checkedout(),
            "overflow": self._pool.overflow(),
            "checked_in": self._pool.checkedin(),
        }

    def get_metrics(self) -> PoolMetrics:
        """Get current pool metrics snapshot."""
        status = self.get_pool_status()

        pool_size = status["pool_size"]
        checked_out = status["checked_out"]
        overflow = status["overflow"]
        checked_in = status["checked_in"]

        # Total connections = pool size + overflow
        # But we need max possible for usage calculation
        max_connections = pool_size + (self._engine.pool._max_overflow if self._pool else 0)
        total_connections = checked_out + checked_in

        # Usage percent: checked out / (pool_size + max_overflow)
        if max_connections > 0:
            usage_percent = (checked_out / max_connections) * 100
        else:
            usage_percent = 0.0

        with self._lock:
            metrics = PoolMetrics(
                timestamp=datetime.utcnow(),
                pool_size=pool_size,
                checked_out=checked_out,
                overflow=overflow,
                checked_in=checked_in,
                total_connections=total_connections,
                usage_percent=usage_percent,
                total_checkouts=self._total_checkouts,
                total_checkins=self._total_checkins,
                total_overflows=self._total_overflows,
                total_invalidations=self._total_invalidations,
                total_timeouts=self._total_timeouts,
            )

        return metrics

    def add_alert_callback(self, callback: Callable[[PoolMetrics, str], None]) -> None:
        """Add a callback for pool alerts."""
        self._alert_callbacks.append(callback)

    def _check_alerts(self, metrics: PoolMetrics) -> None:
        """Check if any alerts should be triggered."""
        # Check cooldown
        if self._last_alert_time:
            elapsed = (datetime.utcnow() - self._last_alert_time).total_seconds()
            if elapsed < self._alert_cooldown_seconds:
                return

        alerts = []

        # High usage alert
        if metrics.usage_percent >= self._alert_threshold * 100:
            alerts.append(
                f"Pool usage at {metrics.usage_percent:.1f}% "
                f"(threshold: {self._alert_threshold * 100:.0f}%)"
            )

        # Overflow alert
        if metrics.overflow > 0:
            alerts.append(f"Pool overflow active: {metrics.overflow} overflow connections")

        # Invalidation spike (more than 5 in recent history)
        if metrics.total_invalidations > 5:
            alerts.append(f"High connection invalidations: {metrics.total_invalidations}")

        # Trigger alerts
        for alert_msg in alerts:
            logger.warning(f"POOL ALERT: {alert_msg}")
            self._last_alert_time = datetime.utcnow()

            for callback in self._alert_callbacks:
                try:
                    callback(metrics, alert_msg)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")

    def record_timeout(self) -> None:
        """Record a pool timeout error."""
        with self._lock:
            self._total_timeouts += 1
        logger.error(f"Pool timeout recorded (total: {self._total_timeouts})")

    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        logger.info(f"Pool monitoring started (interval: {self._metrics_interval}s)")

        while not self._stop_monitoring:
            try:
                metrics = self.get_metrics()

                # Store in history
                with self._lock:
                    self._metrics_history.append(metrics)
                    if len(self._metrics_history) > self._max_history:
                        self._metrics_history = self._metrics_history[-self._max_history:]

                # Check for alerts
                self._check_alerts(metrics)

                # Log periodic status
                logger.debug(
                    f"Pool status: {metrics.checked_out}/{metrics.pool_size} "
                    f"(+{metrics.overflow} overflow), {metrics.usage_percent:.1f}% usage"
                )

            except Exception as e:
                logger.error(f"Pool monitoring error: {e}")

            # Sleep in small intervals to allow quick shutdown
            for _ in range(self._metrics_interval):
                if self._stop_monitoring:
                    break
                time.sleep(1)

        logger.info("Pool monitoring stopped")

    def start(self) -> None:
        """Start background monitoring."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Pool monitoring already running")
            return

        self._stop_monitoring = False
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="db-pool-monitor"
        )
        self._monitoring_thread.start()

    def stop(self) -> None:
        """Stop background monitoring."""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent metrics history."""
        with self._lock:
            history = self._metrics_history[-limit:]
        return [m.to_dict() for m in history]

    def get_prometheus_metrics(self) -> str:
        """Get current metrics in Prometheus format."""
        return self.get_metrics().to_prometheus()


# Global monitor instance
_pool_monitor: Optional[DatabasePoolMonitor] = None


def get_pool_monitor() -> Optional[DatabasePoolMonitor]:
    """Get the global pool monitor instance."""
    return _pool_monitor


def init_pool_monitoring(engine, start_background: bool = True) -> DatabasePoolMonitor:
    """
    Initialize database pool monitoring.

    Args:
        engine: SQLAlchemy engine
        start_background: Whether to start background monitoring

    Returns:
        The pool monitor instance
    """
    global _pool_monitor

    if _pool_monitor is not None:
        logger.warning("Pool monitor already initialized")
        return _pool_monitor

    _pool_monitor = DatabasePoolMonitor(engine)

    if start_background:
        _pool_monitor.start()

    logger.info("Database pool monitoring initialized")
    return _pool_monitor


def get_pool_metrics() -> Dict[str, Any]:
    """Convenience function to get current pool metrics."""
    if _pool_monitor is None:
        return {"error": "Pool monitoring not initialized"}
    return _pool_monitor.get_metrics().to_dict()


def get_pool_prometheus() -> str:
    """Convenience function to get Prometheus metrics."""
    if _pool_monitor is None:
        return "# Pool monitoring not initialized"
    return _pool_monitor.get_prometheus_metrics()
