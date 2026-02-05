"""
Memory Cleanup Service

Provides TTL-based cleanup for in-memory data structures to prevent memory leaks.
Handles cleanup of:
- login_attempts: Failed login tracking
- credit_reports: Received credit reports
- delivered_cases: Delivered analysis tracking
- scan_sessions: Document scanning sessions

Configuration via environment variables:
- LOGIN_ATTEMPTS_TTL_SECONDS: TTL for login attempts (default: 3600 = 1 hour)
- CREDIT_REPORTS_TTL_SECONDS: TTL for credit reports (default: 86400 = 24 hours)
- DELIVERED_CASES_TTL_SECONDS: TTL for delivered cases (default: 604800 = 7 days)
- CLEANUP_INTERVAL_SECONDS: How often to run cleanup (default: 300 = 5 minutes)
"""

import logging
import os
import time
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Configuration from environment
LOGIN_ATTEMPTS_TTL_SECONDS = int(
    os.environ.get("LOGIN_ATTEMPTS_TTL_SECONDS", 3600)
)  # 1 hour
CREDIT_REPORTS_TTL_SECONDS = int(
    os.environ.get("CREDIT_REPORTS_TTL_SECONDS", 86400)
)  # 24 hours
DELIVERED_CASES_TTL_SECONDS = int(
    os.environ.get("DELIVERED_CASES_TTL_SECONDS", 604800)
)  # 7 days
CLEANUP_INTERVAL_SECONDS = int(
    os.environ.get("CLEANUP_INTERVAL_SECONDS", 300)
)  # 5 minutes
SCAN_SESSION_MAX_AGE_HOURS = int(
    os.environ.get("SCAN_SESSION_MAX_AGE_HOURS", 24)
)  # 24 hours

# Track last cleanup time
_last_cleanup_time = 0.0
_cleanup_lock = Lock()

# Store timestamps for items that need TTL tracking
_credit_report_timestamps: dict[int, float] = {}  # index -> timestamp
_delivered_case_timestamps: dict[Any, float] = {}  # case_id -> timestamp


def cleanup_login_attempts(login_attempts: dict) -> int:
    """
    Remove login attempts older than TTL.

    Args:
        login_attempts: The login_attempts dict from app.py

    Returns:
        Number of entries removed
    """
    now = datetime.utcnow()
    ttl = timedelta(seconds=LOGIN_ATTEMPTS_TTL_SECONDS)
    expired = []

    for email, data in list(login_attempts.items()):
        last_attempt = data.get("last_attempt")
        if last_attempt and (now - last_attempt) > ttl:
            expired.append(email)

    for email in expired:
        del login_attempts[email]

    if expired:
        logger.info(f"Cleaned up {len(expired)} expired login attempts")

    return len(expired)


def cleanup_credit_reports(credit_reports: list) -> int:
    """
    Remove credit reports older than TTL.

    Args:
        credit_reports: The credit_reports list from app.py

    Returns:
        Number of reports removed
    """
    global _credit_report_timestamps

    now = time.time()
    ttl = CREDIT_REPORTS_TTL_SECONDS

    # Track new reports that don't have timestamps
    current_len = len(credit_reports)
    for i in range(current_len):
        if i not in _credit_report_timestamps:
            _credit_report_timestamps[i] = now

    # Find expired reports (from oldest to newest to maintain indices)
    expired_indices = []
    for idx, timestamp in list(_credit_report_timestamps.items()):
        if idx < current_len and (now - timestamp) > ttl:
            expired_indices.append(idx)

    # Remove from newest to oldest to preserve indices
    expired_indices.sort(reverse=True)
    for idx in expired_indices:
        if idx < len(credit_reports):
            credit_reports.pop(idx)
            del _credit_report_timestamps[idx]

    # Reindex remaining timestamps
    if expired_indices:
        new_timestamps = {}
        for old_idx, timestamp in sorted(_credit_report_timestamps.items()):
            # Count how many indices below this one were removed
            removed_below = sum(1 for exp_idx in expired_indices if exp_idx < old_idx)
            new_idx = old_idx - removed_below
            if new_idx >= 0:
                new_timestamps[new_idx] = timestamp
        _credit_report_timestamps = new_timestamps
        logger.info(f"Cleaned up {len(expired_indices)} expired credit reports")

    return len(expired_indices)


def cleanup_delivered_cases(delivered_cases: set) -> int:
    """
    Remove delivered case markers older than TTL.

    Args:
        delivered_cases: The delivered_cases set from app.py

    Returns:
        Number of cases removed
    """
    global _delivered_case_timestamps

    now = time.time()
    ttl = DELIVERED_CASES_TTL_SECONDS

    # Track new cases that don't have timestamps
    for case_id in delivered_cases:
        if case_id not in _delivered_case_timestamps:
            _delivered_case_timestamps[case_id] = now

    # Find expired cases
    expired = []
    for case_id, timestamp in list(_delivered_case_timestamps.items()):
        if (now - timestamp) > ttl:
            expired.append(case_id)

    # Remove expired cases
    for case_id in expired:
        delivered_cases.discard(case_id)
        del _delivered_case_timestamps[case_id]

    # Clean up timestamps for cases no longer in set
    orphaned = [cid for cid in _delivered_case_timestamps if cid not in delivered_cases]
    for case_id in orphaned:
        del _delivered_case_timestamps[case_id]

    if expired:
        logger.info(f"Cleaned up {len(expired)} expired delivered cases")

    return len(expired)


def cleanup_scan_sessions() -> int:
    """
    Clean up old document scanning sessions.

    Returns:
        Number of sessions removed
    """
    try:
        from services.document_scanner_service import cleanup_old_sessions

        removed = cleanup_old_sessions(max_age_hours=SCAN_SESSION_MAX_AGE_HOURS)
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired scan sessions")
        return removed
    except ImportError:
        logger.warning("document_scanner_service not available for cleanup")
        return 0
    except Exception as e:
        logger.error(f"Error cleaning up scan sessions: {e}")
        return 0


def run_all_cleanup(
    login_attempts: dict = None,
    credit_reports: list = None,
    delivered_cases: set = None,
) -> dict:
    """
    Run all cleanup operations.

    Args:
        login_attempts: Optional login_attempts dict
        credit_reports: Optional credit_reports list
        delivered_cases: Optional delivered_cases set

    Returns:
        Dict with cleanup statistics
    """
    stats = {
        "login_attempts_removed": 0,
        "credit_reports_removed": 0,
        "delivered_cases_removed": 0,
        "scan_sessions_removed": 0,
    }

    if login_attempts is not None:
        stats["login_attempts_removed"] = cleanup_login_attempts(login_attempts)

    if credit_reports is not None:
        stats["credit_reports_removed"] = cleanup_credit_reports(credit_reports)

    if delivered_cases is not None:
        stats["delivered_cases_removed"] = cleanup_delivered_cases(delivered_cases)

    stats["scan_sessions_removed"] = cleanup_scan_sessions()

    return stats


def maybe_cleanup(
    login_attempts: dict = None,
    credit_reports: list = None,
    delivered_cases: set = None,
) -> bool:
    """
    Run cleanup if enough time has passed since last cleanup.
    Thread-safe with double-check locking.

    Args:
        login_attempts: Optional login_attempts dict
        credit_reports: Optional credit_reports list
        delivered_cases: Optional delivered_cases set

    Returns:
        True if cleanup was run, False otherwise
    """
    global _last_cleanup_time

    now = time.time()

    # Quick check without lock
    if now - _last_cleanup_time < CLEANUP_INTERVAL_SECONDS:
        return False

    with _cleanup_lock:
        # Double-check after acquiring lock
        if now - _last_cleanup_time < CLEANUP_INTERVAL_SECONDS:
            return False

        _last_cleanup_time = now
        run_all_cleanup(login_attempts, credit_reports, delivered_cases)
        return True


def get_cleanup_stats() -> dict:
    """
    Get statistics about tracked items for monitoring.

    Returns:
        Dict with current counts
    """
    return {
        "tracked_credit_reports": len(_credit_report_timestamps),
        "tracked_delivered_cases": len(_delivered_case_timestamps),
        "last_cleanup_time": _last_cleanup_time,
        "cleanup_interval_seconds": CLEANUP_INTERVAL_SECONDS,
    }


def register_cleanup_hook(
    app, login_attempts: dict, credit_reports: list, delivered_cases: set
):
    """
    Register a Flask before_request hook to run cleanup automatically.

    Args:
        app: Flask application instance
        login_attempts: The login_attempts dict
        credit_reports: The credit_reports list
        delivered_cases: The delivered_cases set
    """

    @app.before_request
    def _cleanup_before_request():
        maybe_cleanup(login_attempts, credit_reports, delivered_cases)

    logger.info(
        "Memory cleanup hook registered",
        extra={
            "login_attempts_ttl": LOGIN_ATTEMPTS_TTL_SECONDS,
            "credit_reports_ttl": CREDIT_REPORTS_TTL_SECONDS,
            "delivered_cases_ttl": DELIVERED_CASES_TTL_SECONDS,
            "cleanup_interval": CLEANUP_INTERVAL_SECONDS,
        },
    )
