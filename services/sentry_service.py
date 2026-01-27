"""
Sentry Error Tracking Service

Provides enhanced error tracking with:
- User context (staff/client info)
- Request ID correlation
- Custom tags and context
- Slack notifications for critical errors
- Error categorization and filtering

Usage:
    from services.sentry_service import (
        init_sentry,
        set_user_context,
        capture_exception,
        capture_message,
        add_breadcrumb,
    )

    # Initialize at app startup
    init_sentry(app)

    # Set user context in before_request
    set_user_context(staff_id=123, email="user@example.com")

    # Capture errors
    try:
        risky_operation()
    except Exception as e:
        capture_exception(e, extra={"operation": "risky"})
"""

import functools
import logging
import os
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Sentry SDK imports
try:
    import sentry_sdk
    from sentry_sdk import capture_exception as sentry_capture_exception
    from sentry_sdk import capture_message as sentry_capture_message
    from sentry_sdk import configure_scope, push_scope, set_context, set_tag, set_user
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("sentry-sdk not installed, error tracking disabled")


# =============================================================================
# Configuration
# =============================================================================

# Environment variables
SENTRY_DSN = os.environ.get("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
SENTRY_RELEASE = os.environ.get("APP_VERSION", "1.0.0")
SLACK_WEBHOOK_URL = os.environ.get("SENTRY_SLACK_WEBHOOK")

# Error categories for filtering and alerting
ERROR_CATEGORIES = {
    "critical": [
        "DatabaseError",
        "OperationalError",
        "IntegrityError",
        "CircuitBreakerError",
        "PaymentError",
        "StripeError",
    ],
    "high": [
        "AuthenticationError",
        "AuthorizationError",
        "ValidationError",
        "APIError",
    ],
    "medium": [
        "ConnectionError",
        "TimeoutError",
        "ServiceUnavailable",
    ],
    "low": [
        "NotFoundError",
        "BadRequest",
        "RateLimitExceeded",
    ],
}

# Errors to ignore (don't send to Sentry)
IGNORED_ERRORS = [
    "NotFound",  # 404 errors
    "MethodNotAllowed",  # 405 errors
    "BadRequest",  # 400 errors from user input
]

# Sensitive fields to redact
SENSITIVE_FIELDS = [
    "password",
    "token",
    "api_key",
    "secret",
    "credit_card",
    "ssn",
    "social_security",
    "auth_token",
    "access_token",
    "refresh_token",
]

_sentry_initialized = False


# =============================================================================
# Initialization
# =============================================================================


def init_sentry(app=None, dsn: str = None) -> bool:
    """
    Initialize Sentry error tracking.

    Args:
        app: Flask application instance (optional)
        dsn: Sentry DSN (optional, defaults to SENTRY_DSN env var)

    Returns:
        True if initialized successfully, False otherwise
    """
    global _sentry_initialized

    if not SENTRY_AVAILABLE:
        logger.warning("Sentry SDK not available")
        return False

    dsn = dsn or SENTRY_DSN
    if not dsn:
        logger.info("Sentry DSN not configured, error tracking disabled")
        return False

    try:
        # Configure logging integration
        logging_integration = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors and above as events
        )

        integrations = [
            FlaskIntegration(transaction_style="url"),
            SqlalchemyIntegration(),
            logging_integration,
        ]

        sentry_sdk.init(
            dsn=dsn,
            integrations=integrations,
            # Performance monitoring
            traces_sample_rate=0.1,  # 10% of requests
            profiles_sample_rate=0.1,  # 10% for profiling
            # Environment info
            environment=SENTRY_ENVIRONMENT,
            release=SENTRY_RELEASE,
            # Privacy
            send_default_pii=False,
            # Custom configuration
            before_send=_before_send,
            before_breadcrumb=_before_breadcrumb,
            # Attach stack traces to all messages
            attach_stacktrace=True,
            # Max breadcrumbs to keep
            max_breadcrumbs=50,
            # Debug mode (only in development)
            debug=SENTRY_ENVIRONMENT == "development",
        )

        _sentry_initialized = True
        logger.info(
            f"Sentry initialized: env={SENTRY_ENVIRONMENT}, release={SENTRY_RELEASE}"
        )

        # Register Flask error handlers if app provided
        if app:
            _register_error_handlers(app)
            _register_request_hooks(app)

        return True

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def is_sentry_configured() -> bool:
    """Check if Sentry is configured and initialized."""
    return _sentry_initialized and SENTRY_AVAILABLE


# =============================================================================
# User Context
# =============================================================================


def set_user_context(
    user_id: Optional[int] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    role: Optional[str] = None,
    user_type: str = "staff",
    ip_address: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Set the current user context for error tracking.

    Args:
        user_id: User's database ID
        email: User's email address
        username: User's display name
        role: User's role (admin, staff, client)
        user_type: Type of user (staff, client, affiliate, partner)
        ip_address: User's IP address
        extra: Additional user-related context
    """
    if not is_sentry_configured():
        return

    user_data = {}

    if user_id:
        user_data["id"] = str(user_id)
    if email:
        user_data["email"] = email
    if username:
        user_data["username"] = username
    if ip_address:
        user_data["ip_address"] = ip_address

    # Add custom fields
    if role:
        user_data["role"] = role
    if user_type:
        user_data["user_type"] = user_type

    if user_data:
        set_user(user_data)

    # Set additional context
    if extra:
        set_context("user_extra", extra)


def clear_user_context() -> None:
    """Clear the current user context."""
    if is_sentry_configured():
        set_user(None)


# =============================================================================
# Request Context
# =============================================================================


def set_request_context(
    request_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Set request context for error correlation.

    Args:
        request_id: Unique request identifier
        endpoint: Flask endpoint name
        method: HTTP method
        path: Request path
        extra: Additional request context
    """
    if not is_sentry_configured():
        return

    if request_id:
        set_tag("request_id", request_id)

    if endpoint:
        set_tag("endpoint", endpoint)

    if method:
        set_tag("http_method", method)

    request_context = {}
    if path:
        request_context["path"] = path
    if extra:
        request_context.update(extra)

    if request_context:
        set_context("request", request_context)


# =============================================================================
# Error Capture
# =============================================================================


def capture_exception(
    exception: Exception,
    level: str = "error",
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    fingerprint: Optional[List[str]] = None,
    notify_slack: bool = None,
) -> Optional[str]:
    """
    Capture an exception and send to Sentry.

    Args:
        exception: The exception to capture
        level: Error level (error, warning, info)
        extra: Additional context data
        tags: Custom tags for the error
        fingerprint: Custom fingerprint for grouping
        notify_slack: Override Slack notification (None = auto based on severity)

    Returns:
        Sentry event ID if captured, None otherwise
    """
    if not is_sentry_configured():
        logger.error(f"Exception (Sentry disabled): {exception}", exc_info=exception)
        return None

    # Check if error should be ignored
    error_name = type(exception).__name__
    if error_name in IGNORED_ERRORS:
        return None

    event_id = None

    with push_scope() as scope:
        # Set level
        scope.level = level

        # Add tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        # Categorize error
        category = _categorize_error(error_name)
        scope.set_tag("error_category", category)

        # Add extra context
        if extra:
            scope.set_context("extra", _sanitize_data(extra))

        # Custom fingerprint for grouping
        if fingerprint:
            scope.fingerprint = fingerprint

        # Capture the exception
        event_id = sentry_capture_exception(exception)

    # Send Slack notification for critical errors
    if notify_slack is True or (notify_slack is None and category == "critical"):
        _notify_slack(exception, event_id, category)

    return event_id


def capture_message(
    message: str,
    level: str = "info",
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Capture a message and send to Sentry.

    Args:
        message: The message to capture
        level: Message level (info, warning, error)
        extra: Additional context data
        tags: Custom tags

    Returns:
        Sentry event ID if captured, None otherwise
    """
    if not is_sentry_configured():
        logger.log(
            logging.INFO if level == "info" else logging.WARNING,
            f"Message (Sentry disabled): {message}",
        )
        return None

    with push_scope() as scope:
        scope.level = level

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        if extra:
            scope.set_context("extra", _sanitize_data(extra))

        return sentry_capture_message(message)


# =============================================================================
# Breadcrumbs
# =============================================================================


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Add a breadcrumb for error context.

    Args:
        message: Breadcrumb message
        category: Category (http, query, ui, auth, etc.)
        level: Level (debug, info, warning, error)
        data: Additional data
    """
    if not is_sentry_configured():
        return

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=_sanitize_data(data) if data else None,
    )


# =============================================================================
# Decorators
# =============================================================================


def track_errors(
    operation: str = None,
    notify_slack: bool = False,
    reraise: bool = True,
):
    """
    Decorator to track errors in a function.

    Args:
        operation: Name of the operation (defaults to function name)
        notify_slack: Send Slack notification on error
        reraise: Re-raise the exception after capturing

    Example:
        @track_errors(operation="payment_processing", notify_slack=True)
        def process_payment(amount):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__

            add_breadcrumb(
                message=f"Starting {op_name}",
                category="function",
                level="info",
            )

            try:
                result = func(*args, **kwargs)
                add_breadcrumb(
                    message=f"Completed {op_name}",
                    category="function",
                    level="info",
                )
                return result

            except Exception as e:
                capture_exception(
                    e,
                    extra={
                        "operation": op_name,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    },
                    tags={"operation": op_name},
                    notify_slack=notify_slack,
                )

                if reraise:
                    raise

        return wrapper

    return decorator


# =============================================================================
# Flask Integration
# =============================================================================


def _register_error_handlers(app) -> None:
    """Register Flask error handlers for Sentry."""

    @app.errorhandler(500)
    def handle_500(error):
        from flask import request

        # Get request ID if available
        request_id = getattr(request, "request_id", None)

        capture_exception(
            error,
            extra={
                "request_id": request_id,
                "path": request.path,
                "method": request.method,
            },
            notify_slack=True,
        )

        return {"error": "Internal server error", "request_id": request_id}, 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        from flask import request

        # Don't capture HTTP exceptions (they're expected)
        from werkzeug.exceptions import HTTPException

        if isinstance(error, HTTPException):
            return error

        request_id = getattr(request, "request_id", None)

        capture_exception(
            error,
            extra={
                "request_id": request_id,
                "path": request.path,
                "method": request.method,
            },
        )

        return {"error": "Internal server error", "request_id": request_id}, 500


def _register_request_hooks(app) -> None:
    """Register Flask request hooks for context."""

    @app.before_request
    def set_sentry_context():
        from flask import request, session

        # Set request context
        request_id = getattr(request, "request_id", None)
        if not request_id:
            from services.request_id_service import get_request_id

            request_id = get_request_id()

        set_request_context(
            request_id=request_id,
            endpoint=request.endpoint,
            method=request.method,
            path=request.path,
        )

        # Set user context from session
        staff_id = session.get("staff_id")
        if staff_id:
            set_user_context(
                user_id=staff_id,
                email=session.get("staff_email"),
                username=session.get("staff_name"),
                role=session.get("staff_role"),
                user_type="staff",
                ip_address=request.remote_addr,
            )
        else:
            client_id = session.get("client_id")
            if client_id:
                set_user_context(
                    user_id=client_id,
                    email=session.get("client_email"),
                    user_type="client",
                    ip_address=request.remote_addr,
                )

    @app.after_request
    def add_response_breadcrumb(response):
        add_breadcrumb(
            message=f"Response {response.status_code}",
            category="http",
            level="info" if response.status_code < 400 else "warning",
            data={"status_code": response.status_code},
        )
        return response


# =============================================================================
# Slack Notifications
# =============================================================================


def _notify_slack(
    exception: Exception,
    event_id: Optional[str],
    category: str,
) -> bool:
    """
    Send Slack notification for critical errors.

    Args:
        exception: The exception that occurred
        event_id: Sentry event ID
        category: Error category

    Returns:
        True if notification sent, False otherwise
    """
    if not SLACK_WEBHOOK_URL:
        return False

    try:
        error_type = type(exception).__name__
        error_message = str(exception)[:500]  # Truncate long messages

        # Build Sentry link if available
        sentry_link = ""
        if event_id and SENTRY_DSN:
            # Extract org and project from DSN
            # DSN format: https://key@org.ingest.sentry.io/project
            try:
                import re

                match = re.search(r"@(\w+)\.ingest\.sentry\.io/(\d+)", SENTRY_DSN)
                if match:
                    org, project = match.groups()
                    sentry_link = f"https://sentry.io/organizations/{org}/issues/?query={event_id}"
            except Exception:
                pass

        # Build Slack message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {category.upper()} Error: {error_type}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Environment:*\n{SENTRY_ENVIRONMENT}"},
                    {"type": "mrkdwn", "text": f"*Category:*\n{category}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{error_message}```",
                },
            },
        ]

        if sentry_link:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{sentry_link}|View in Sentry>",
                    },
                }
            )

        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Event ID: `{event_id or 'N/A'}` | {datetime.utcnow().isoformat()}Z",
                    }
                ],
            }
        )

        payload = {"blocks": blocks}

        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=5,
        )

        return response.status_code == 200

    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False


# =============================================================================
# Helper Functions
# =============================================================================


def _before_send(event: Dict, hint: Dict) -> Optional[Dict]:
    """
    Process event before sending to Sentry.
    Used for filtering and modification.
    """
    # Get exception info
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        error_name = exc_type.__name__

        # Filter out ignored errors
        if error_name in IGNORED_ERRORS:
            return None

    # Sanitize request data
    if "request" in event:
        event["request"] = _sanitize_data(event["request"])

    return event


def _before_breadcrumb(crumb: Dict, hint: Dict) -> Optional[Dict]:
    """
    Process breadcrumb before adding.
    Used for filtering sensitive data.
    """
    # Sanitize breadcrumb data
    if "data" in crumb and crumb["data"]:
        crumb["data"] = _sanitize_data(crumb["data"])

    return crumb


def _categorize_error(error_name: str) -> str:
    """Categorize an error by its name."""
    for category, errors in ERROR_CATEGORIES.items():
        if any(e.lower() in error_name.lower() for e in errors):
            return category
    return "unknown"


def _sanitize_data(data: Any) -> Any:
    """
    Recursively sanitize sensitive data.

    Args:
        data: Data to sanitize

    Returns:
        Sanitized data with sensitive fields redacted
    """
    if data is None:
        return None

    if isinstance(data, dict):
        return {
            k: "[REDACTED]" if _is_sensitive_field(k) else _sanitize_data(v)
            for k, v in data.items()
        }

    if isinstance(data, (list, tuple)):
        return [_sanitize_data(item) for item in data]

    if isinstance(data, str):
        # Check if it looks like a secret (long alphanumeric string)
        if len(data) > 20 and data.isalnum():
            return "[REDACTED]"

    return data


def _is_sensitive_field(field_name: str) -> bool:
    """Check if a field name is sensitive."""
    field_lower = field_name.lower()
    return any(sensitive in field_lower for sensitive in SENSITIVE_FIELDS)


# =============================================================================
# Context Managers
# =============================================================================


class sentry_span:
    """
    Context manager for Sentry performance spans.

    Example:
        with sentry_span("database", "query_users"):
            users = db.query(User).all()
    """

    def __init__(self, op: str, description: str):
        self.op = op
        self.description = description
        self.span = None

    def __enter__(self):
        if is_sentry_configured():
            self.span = sentry_sdk.start_span(op=self.op, description=self.description)
            self.span.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.__exit__(exc_type, exc_val, exc_tb)
        return False


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Initialization
    "init_sentry",
    "is_sentry_configured",
    # User context
    "set_user_context",
    "clear_user_context",
    # Request context
    "set_request_context",
    # Error capture
    "capture_exception",
    "capture_message",
    # Breadcrumbs
    "add_breadcrumb",
    # Decorators
    "track_errors",
    # Context managers
    "sentry_span",
    # Configuration
    "ERROR_CATEGORIES",
    "IGNORED_ERRORS",
]
