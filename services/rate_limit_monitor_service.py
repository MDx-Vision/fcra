"""
Rate Limit Monitoring Service for FCRA Platform

Provides monitoring, alerting, and blocking for rate limit violations:
- Track violations by IP address
- Detect repeat offenders and potential attacks
- Auto-block IPs that exceed violation thresholds
- Export metrics for monitoring dashboards
"""

import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

from flask import request

# Configuration from environment
VIOLATION_THRESHOLD = int(os.environ.get("RATE_LIMIT_VIOLATION_THRESHOLD", "10"))  # violations before block
BLOCK_DURATION_MINUTES = int(os.environ.get("RATE_LIMIT_BLOCK_DURATION", "60"))  # minutes
VIOLATION_WINDOW_MINUTES = int(os.environ.get("RATE_LIMIT_VIOLATION_WINDOW", "5"))  # window to count violations
ALERT_THRESHOLD = int(os.environ.get("RATE_LIMIT_ALERT_THRESHOLD", "5"))  # violations before alert

logger = logging.getLogger("rate_limit_monitor")


@dataclass
class ViolationRecord:
    """Record of a single rate limit violation."""
    ip_address: str
    endpoint: str
    timestamp: datetime
    user_agent: str = ""
    key: str = ""  # Rate limit key (staff:id or IP)


@dataclass
class IPStats:
    """Statistics for a single IP address."""
    ip_address: str
    total_violations: int = 0
    violations_in_window: int = 0
    first_violation: Optional[datetime] = None
    last_violation: Optional[datetime] = None
    blocked: bool = False
    blocked_at: Optional[datetime] = None
    blocked_until: Optional[datetime] = None
    endpoints_hit: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ip_address": self.ip_address,
            "total_violations": self.total_violations,
            "violations_in_window": self.violations_in_window,
            "first_violation": self.first_violation.isoformat() if self.first_violation else None,
            "last_violation": self.last_violation.isoformat() if self.last_violation else None,
            "blocked": self.blocked,
            "blocked_at": self.blocked_at.isoformat() if self.blocked_at else None,
            "blocked_until": self.blocked_until.isoformat() if self.blocked_until else None,
            "endpoints_hit": list(self.endpoints_hit),
        }


class RateLimitMonitor:
    """
    Monitors rate limit violations and manages IP blocking.

    Usage:
        monitor = RateLimitMonitor()

        # Record a violation
        monitor.record_violation("192.168.1.1", "/api/login")

        # Check if IP is blocked
        if monitor.is_blocked("192.168.1.1"):
            return "Blocked", 403

        # Get stats
        stats = monitor.get_stats()
    """

    def __init__(
        self,
        violation_threshold: int = VIOLATION_THRESHOLD,
        block_duration_minutes: int = BLOCK_DURATION_MINUTES,
        violation_window_minutes: int = VIOLATION_WINDOW_MINUTES,
        alert_threshold: int = ALERT_THRESHOLD,
    ):
        self._violation_threshold = violation_threshold
        self._block_duration = timedelta(minutes=block_duration_minutes)
        self._violation_window = timedelta(minutes=violation_window_minutes)
        self._alert_threshold = alert_threshold

        # Storage
        self._violations: List[ViolationRecord] = []
        self._ip_stats: Dict[str, IPStats] = defaultdict(lambda: IPStats(ip_address=""))
        self._blocked_ips: Dict[str, datetime] = {}  # IP -> blocked_until
        self._permanent_blocklist: Set[str] = set()

        # Counters
        self._total_violations = 0
        self._total_blocks = 0
        self._total_alerts = 0

        # Thread safety
        self._lock = threading.Lock()

        # Alert callbacks
        self._alert_callbacks: List[Callable[[str, IPStats, str], None]] = []

        # Cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = False

    def record_violation(
        self,
        ip_address: str,
        endpoint: str,
        user_agent: str = "",
        key: str = ""
    ) -> bool:
        """
        Record a rate limit violation.

        Args:
            ip_address: Client IP address
            endpoint: The endpoint that was rate limited
            user_agent: Client user agent
            key: Rate limit key used

        Returns:
            True if IP was blocked as a result
        """
        now = datetime.utcnow()

        with self._lock:
            self._total_violations += 1

            # Create violation record
            violation = ViolationRecord(
                ip_address=ip_address,
                endpoint=endpoint,
                timestamp=now,
                user_agent=user_agent[:200] if user_agent else "",
                key=key,
            )
            self._violations.append(violation)

            # Update IP stats
            stats = self._ip_stats[ip_address]
            if stats.ip_address == "":
                stats.ip_address = ip_address

            stats.total_violations += 1
            stats.last_violation = now
            stats.endpoints_hit.add(endpoint)

            if stats.first_violation is None:
                stats.first_violation = now

            # Count violations in window
            window_start = now - self._violation_window
            stats.violations_in_window = sum(
                1 for v in self._violations
                if v.ip_address == ip_address and v.timestamp >= window_start
            )

            # Log the violation
            logger.warning(
                f"Rate limit violation: IP={ip_address}, endpoint={endpoint}, "
                f"violations_in_window={stats.violations_in_window}, "
                f"total={stats.total_violations}"
            )

            # Check for alert threshold
            if stats.violations_in_window >= self._alert_threshold and not stats.blocked:
                self._trigger_alert(ip_address, stats, "threshold_approaching")

            # Check for block threshold
            if stats.violations_in_window >= self._violation_threshold and not stats.blocked:
                self._block_ip(ip_address, stats)
                return True

        return False

    def _trigger_alert(self, ip_address: str, stats: IPStats, alert_type: str) -> None:
        """Trigger an alert for potential attack."""
        self._total_alerts += 1

        alert_msg = (
            f"Rate limit alert ({alert_type}): IP={ip_address}, "
            f"violations={stats.violations_in_window}/{self._violation_threshold}, "
            f"endpoints={list(stats.endpoints_hit)}"
        )
        logger.warning(f"🚨 {alert_msg}")

        for callback in self._alert_callbacks:
            try:
                callback(ip_address, stats, alert_type)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def _block_ip(self, ip_address: str, stats: IPStats) -> None:
        """Block an IP address."""
        now = datetime.utcnow()
        blocked_until = now + self._block_duration

        stats.blocked = True
        stats.blocked_at = now
        stats.blocked_until = blocked_until
        self._blocked_ips[ip_address] = blocked_until
        self._total_blocks += 1

        logger.error(
            f"🚫 IP BLOCKED: {ip_address} blocked until {blocked_until.isoformat()} "
            f"(violations: {stats.total_violations})"
        )

        self._trigger_alert(ip_address, stats, "ip_blocked")

    def is_blocked(self, ip_address: str) -> bool:
        """Check if an IP is currently blocked."""
        # Check permanent blocklist
        if ip_address in self._permanent_blocklist:
            return True

        with self._lock:
            if ip_address not in self._blocked_ips:
                return False

            blocked_until = self._blocked_ips[ip_address]
            if datetime.utcnow() >= blocked_until:
                # Block expired
                del self._blocked_ips[ip_address]
                if ip_address in self._ip_stats:
                    self._ip_stats[ip_address].blocked = False
                return False

            return True

    def unblock_ip(self, ip_address: str) -> bool:
        """Manually unblock an IP address."""
        with self._lock:
            if ip_address in self._blocked_ips:
                del self._blocked_ips[ip_address]
                if ip_address in self._ip_stats:
                    self._ip_stats[ip_address].blocked = False
                logger.info(f"IP unblocked: {ip_address}")
                return True

            if ip_address in self._permanent_blocklist:
                self._permanent_blocklist.remove(ip_address)
                logger.info(f"IP removed from permanent blocklist: {ip_address}")
                return True

        return False

    def add_to_blocklist(self, ip_address: str) -> None:
        """Permanently block an IP address."""
        with self._lock:
            self._permanent_blocklist.add(ip_address)
            logger.warning(f"IP added to permanent blocklist: {ip_address}")

    def add_alert_callback(self, callback: Callable[[str, IPStats, str], None]) -> None:
        """Add a callback for rate limit alerts."""
        self._alert_callbacks.append(callback)

    def get_ip_stats(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific IP."""
        with self._lock:
            if ip_address in self._ip_stats:
                return self._ip_stats[ip_address].to_dict()
        return None

    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of currently blocked IPs."""
        now = datetime.utcnow()
        result = []

        with self._lock:
            for ip, blocked_until in list(self._blocked_ips.items()):
                if now < blocked_until:
                    stats = self._ip_stats.get(ip)
                    result.append({
                        "ip_address": ip,
                        "blocked_until": blocked_until.isoformat(),
                        "remaining_seconds": (blocked_until - now).total_seconds(),
                        "total_violations": stats.total_violations if stats else 0,
                    })

            for ip in self._permanent_blocklist:
                result.append({
                    "ip_address": ip,
                    "blocked_until": "permanent",
                    "remaining_seconds": -1,
                    "total_violations": self._ip_stats.get(ip, IPStats(ip)).total_violations,
                })

        return result

    def get_top_offenders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top violating IPs."""
        with self._lock:
            sorted_stats = sorted(
                self._ip_stats.values(),
                key=lambda s: s.total_violations,
                reverse=True
            )[:limit]
            return [s.to_dict() for s in sorted_stats]

    def get_recent_violations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent violations."""
        with self._lock:
            recent = self._violations[-limit:]
            return [
                {
                    "ip_address": v.ip_address,
                    "endpoint": v.endpoint,
                    "timestamp": v.timestamp.isoformat(),
                    "user_agent": v.user_agent,
                }
                for v in reversed(recent)
            ]

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics."""
        with self._lock:
            now = datetime.utcnow()
            window_start = now - self._violation_window

            violations_in_window = sum(
                1 for v in self._violations if v.timestamp >= window_start
            )

            active_blocks = sum(
                1 for blocked_until in self._blocked_ips.values()
                if now < blocked_until
            )

            return {
                "total_violations": self._total_violations,
                "violations_in_window": violations_in_window,
                "window_minutes": self._violation_window.total_seconds() / 60,
                "unique_ips": len(self._ip_stats),
                "active_blocks": active_blocks + len(self._permanent_blocklist),
                "permanent_blocks": len(self._permanent_blocklist),
                "total_blocks": self._total_blocks,
                "total_alerts": self._total_alerts,
                "violation_threshold": self._violation_threshold,
                "alert_threshold": self._alert_threshold,
                "block_duration_minutes": self._block_duration.total_seconds() / 60,
            }

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        stats = self.get_stats()
        lines = [
            "# HELP rate_limit_violations_total Total rate limit violations",
            "# TYPE rate_limit_violations_total counter",
            f"rate_limit_violations_total {stats['total_violations']}",
            "",
            "# HELP rate_limit_violations_window Violations in current window",
            "# TYPE rate_limit_violations_window gauge",
            f"rate_limit_violations_window {stats['violations_in_window']}",
            "",
            "# HELP rate_limit_blocked_ips Currently blocked IPs",
            "# TYPE rate_limit_blocked_ips gauge",
            f"rate_limit_blocked_ips {stats['active_blocks']}",
            "",
            "# HELP rate_limit_blocks_total Total IPs blocked",
            "# TYPE rate_limit_blocks_total counter",
            f"rate_limit_blocks_total {stats['total_blocks']}",
            "",
            "# HELP rate_limit_alerts_total Total alerts triggered",
            "# TYPE rate_limit_alerts_total counter",
            f"rate_limit_alerts_total {stats['total_alerts']}",
            "",
            "# HELP rate_limit_unique_ips Unique IPs with violations",
            "# TYPE rate_limit_unique_ips gauge",
            f"rate_limit_unique_ips {stats['unique_ips']}",
        ]
        return "\n".join(lines)

    def cleanup_old_data(self, max_age_hours: int = 24) -> int:
        """Remove old violation records."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed = 0

        with self._lock:
            original_count = len(self._violations)
            self._violations = [v for v in self._violations if v.timestamp >= cutoff]
            removed = original_count - len(self._violations)

            if removed > 0:
                logger.info(f"Cleaned up {removed} old violation records")

        return removed

    def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._stop_cleanup:
            try:
                self.cleanup_old_data(max_age_hours=24)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

            # Sleep for 1 hour
            for _ in range(3600):
                if self._stop_cleanup:
                    break
                time.sleep(1)

    def start_cleanup_thread(self) -> None:
        """Start background cleanup thread."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        self._stop_cleanup = False
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="rate-limit-cleanup"
        )
        self._cleanup_thread.start()

    def stop_cleanup_thread(self) -> None:
        """Stop background cleanup thread."""
        self._stop_cleanup = True
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2)


# Global monitor instance
_rate_limit_monitor: Optional[RateLimitMonitor] = None


def get_rate_limit_monitor() -> Optional[RateLimitMonitor]:
    """Get the global rate limit monitor instance."""
    return _rate_limit_monitor


def init_rate_limit_monitoring() -> RateLimitMonitor:
    """Initialize rate limit monitoring."""
    global _rate_limit_monitor

    if _rate_limit_monitor is not None:
        return _rate_limit_monitor

    _rate_limit_monitor = RateLimitMonitor()
    _rate_limit_monitor.start_cleanup_thread()

    logger.info("Rate limit monitoring initialized")
    return _rate_limit_monitor


def record_violation(ip_address: str, endpoint: str, **kwargs) -> bool:
    """Convenience function to record a violation."""
    if _rate_limit_monitor:
        return _rate_limit_monitor.record_violation(ip_address, endpoint, **kwargs)
    return False


def is_ip_blocked(ip_address: str) -> bool:
    """Convenience function to check if IP is blocked."""
    if _rate_limit_monitor:
        return _rate_limit_monitor.is_blocked(ip_address)
    return False
