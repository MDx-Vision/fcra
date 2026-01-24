"""
Activity Logger Service - Human-Readable Logs

Like Paul said: "You should be able to skim through yourself without any technical training"

This creates easy-to-read logs that show exactly what's happening:
- What action was taken
- Who did it
- What was the result
- Any errors that occurred

View logs at: /dashboard/logs
"""

import json
import os
import time
from datetime import datetime
from functools import wraps

# Store recent activities in memory for quick access
RECENT_ACTIVITIES = []
MAX_ACTIVITIES = 500

# Activity log file
ACTIVITY_LOG_FILE = "logs/activity.log"


def log_activity(action: str, details: str = None, user: str = None,
                 client_id: int = None, status: str = "success", error: str = None):
    """
    Log an activity in human-readable format.

    Examples:
        log_activity("Email Sent", "Portal invite to john@example.com", user="staff@example.com")
        log_activity("Payment Failed", "Stripe declined card", client_id=123, status="error")
        log_activity("Credit Report Imported", "MyFreeScoreNow - 3 scores extracted", client_id=456)
    """
    timestamp = datetime.now()

    activity = {
        "time": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details,
        "user": user,
        "client_id": client_id,
        "status": status,  # success, error, warning, info
        "error": error
    }

    # Add to in-memory list (most recent first)
    RECENT_ACTIVITIES.insert(0, activity)

    # Keep only last N activities
    if len(RECENT_ACTIVITIES) > MAX_ACTIVITIES:
        RECENT_ACTIVITIES.pop()

    # Write to file
    try:
        os.makedirs("logs", exist_ok=True)

        # Human-readable format for the log file
        status_icon = {"success": "✓", "error": "✗", "warning": "⚠", "info": "ℹ"}.get(status, "•")

        log_line = f"[{activity['time']}] {status_icon} {action}"
        if details:
            log_line += f" | {details}"
        if user:
            log_line += f" | user: {user}"
        if client_id:
            log_line += f" | client: {client_id}"
        if error:
            log_line += f" | ERROR: {error}"
        log_line += "\n"

        with open(ACTIVITY_LOG_FILE, "a") as f:
            f.write(log_line)

    except Exception as e:
        print(f"Could not write to activity log: {e}")

    return activity


def get_recent_activities(limit: int = 100, status_filter: str = None,
                          action_filter: str = None) -> list:
    """Get recent activities from memory."""
    activities = RECENT_ACTIVITIES[:limit]

    if status_filter:
        activities = [a for a in activities if a["status"] == status_filter]

    if action_filter:
        activities = [a for a in activities if action_filter.lower() in a["action"].lower()]

    return activities


def get_activities_from_file(limit: int = 200, search: str = None) -> list:
    """Read activities from log file (for when server restarts)."""
    activities = []

    try:
        if os.path.exists(ACTIVITY_LOG_FILE):
            with open(ACTIVITY_LOG_FILE, "r") as f:
                lines = f.readlines()

            # Get last N lines, reversed (most recent first)
            for line in reversed(lines[-limit:]):
                line = line.strip()
                if line and (not search or search.lower() in line.lower()):
                    activities.append({"raw": line})

    except Exception as e:
        activities.append({"raw": f"Error reading log: {e}"})

    return activities


def read_error_log(limit: int = 100) -> list:
    """Read recent errors from error.log."""
    errors = []

    try:
        if os.path.exists("logs/error.log"):
            with open("logs/error.log", "r") as f:
                lines = f.readlines()

            for line in reversed(lines[-limit:]):
                line = line.strip()
                if line:
                    errors.append(line)

    except Exception as e:
        errors.append(f"Error reading error log: {e}")

    return errors


def read_app_log(limit: int = 100) -> list:
    """Read recent entries from app.log."""
    entries = []

    try:
        if os.path.exists("logs/app.log"):
            with open("logs/app.log", "r") as f:
                lines = f.readlines()

            for line in reversed(lines[-limit:]):
                line = line.strip()
                if line:
                    entries.append(line)

    except Exception as e:
        entries.append(f"Error reading app log: {e}")

    return entries


# Decorator to automatically log function calls
def logged(action_name: str = None):
    """
    Decorator to automatically log when a function is called and its result.

    Example:
        @logged("Generate Dispute Letter")
        def generate_letter(client_id, round_num):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = action_name or func.__name__
            start = time.time()

            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000

                details = f"completed in {duration:.0f}ms"
                log_activity(name, details, status="success")

                return result

            except Exception as e:
                duration = (time.time() - start) * 1000
                log_activity(name, f"failed after {duration:.0f}ms",
                           status="error", error=str(e))
                raise

        return wrapper
    return decorator


# Pre-built logging functions for common actions
def log_email_sent(to: str, subject: str, user: str = None):
    """Log email sent."""
    log_activity("Email Sent", f"To: {to} | Subject: {subject}", user=user)


def log_email_failed(to: str, error: str, user: str = None):
    """Log email failure."""
    log_activity("Email Failed", f"To: {to}", user=user, status="error", error=error)


def log_sms_sent(to: str, user: str = None):
    """Log SMS sent."""
    log_activity("SMS Sent", f"To: {to}", user=user)


def log_sms_failed(to: str, error: str, user: str = None):
    """Log SMS failure."""
    log_activity("SMS Failed", f"To: {to}", user=user, status="error", error=error)


def log_payment_success(client_id: int, amount: float, method: str):
    """Log successful payment."""
    log_activity("Payment Received", f"${amount:.2f} via {method}", client_id=client_id)


def log_payment_failed(client_id: int, amount: float, error: str):
    """Log failed payment."""
    log_activity("Payment Failed", f"${amount:.2f}", client_id=client_id,
                status="error", error=error)


def log_login(user: str, portal: str = "staff"):
    """Log user login."""
    log_activity("User Login", f"{portal} portal", user=user)


def log_login_failed(user: str, reason: str):
    """Log failed login attempt."""
    log_activity("Login Failed", reason, user=user, status="warning")


def log_client_created(client_id: int, name: str, user: str = None):
    """Log new client created."""
    log_activity("Client Created", name, user=user, client_id=client_id)


def log_dispute_generated(client_id: int, round_num: int, letter_count: int, user: str = None):
    """Log dispute letters generated."""
    log_activity("Disputes Generated",
                f"Round {round_num} | {letter_count} letters",
                user=user, client_id=client_id)


def log_credit_import(client_id: int, service: str, scores: dict = None):
    """Log credit report import."""
    score_str = ""
    if scores:
        score_str = f" | TU:{scores.get('transunion', '?')} EX:{scores.get('experian', '?')} EQ:{scores.get('equifax', '?')}"
    log_activity("Credit Report Imported", f"{service}{score_str}", client_id=client_id)


def log_credit_import_failed(client_id: int, service: str, error: str):
    """Log credit import failure."""
    log_activity("Credit Import Failed", service, client_id=client_id,
                status="error", error=error)


def log_document_uploaded(client_id: int, doc_type: str, filename: str):
    """Log document upload."""
    log_activity("Document Uploaded", f"{doc_type}: {filename}", client_id=client_id)


def log_api_call(service: str, endpoint: str, status_code: int, duration_ms: float):
    """Log external API call."""
    status = "success" if status_code < 400 else "error"
    log_activity(f"API Call: {service}",
                f"{endpoint} | {status_code} | {duration_ms:.0f}ms",
                status=status)
