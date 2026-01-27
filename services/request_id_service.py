"""
Request ID Tracking Service for FCRA Platform

Provides comprehensive request ID tracking across the application:
- Generates unique request IDs per HTTP request
- Automatically adds request ID to all log entries
- Provides helpers for passing request ID to external services
- Includes request ID in error responses

Usage:
    from services.request_id_service import get_request_id, with_request_id_headers

    # Get current request ID
    request_id = get_request_id()

    # Add request ID to external API call
    headers = with_request_id_headers({"Authorization": "Bearer token"})
    response = requests.get(url, headers=headers)
"""

import logging
import os
import threading
import uuid
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

# Context variable for request ID (thread-safe)
_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Header names for request ID propagation
REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"

# Configuration
REQUEST_ID_PREFIX = os.environ.get("REQUEST_ID_PREFIX", "")  # Optional prefix for multi-service environments

logger = logging.getLogger("request_id")


def generate_request_id() -> str:
    """
    Generate a new unique request ID.

    Format: [prefix-]timestamp-uuid
    Example: fcra-20260126T153045-a1b2c3d4
    """
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]

    if REQUEST_ID_PREFIX:
        return f"{REQUEST_ID_PREFIX}-{timestamp}-{short_uuid}"
    return f"{timestamp}-{short_uuid}"


def get_request_id() -> Optional[str]:
    """
    Get the current request ID.

    Returns:
        The current request ID, or None if not in a request context
    """
    # First try context var (works in async contexts)
    request_id = _request_id_var.get()
    if request_id:
        return request_id

    # Fall back to Flask's g object
    try:
        from flask import g
        return getattr(g, "correlation_id", None) or getattr(g, "request_id", None)
    except RuntimeError:
        return None


def set_request_id(request_id: str) -> None:
    """
    Set the current request ID.

    Args:
        request_id: The request ID to set
    """
    _request_id_var.set(request_id)

    # Also set in Flask's g if available
    try:
        from flask import g
        g.request_id = request_id
        g.correlation_id = request_id  # For backward compatibility
    except RuntimeError:
        pass


def clear_request_id() -> None:
    """Clear the current request ID."""
    _request_id_var.set(None)


def with_request_id_headers(headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Add request ID headers to an existing headers dictionary.

    Use this when making external API calls to propagate the request ID.

    Args:
        headers: Existing headers dictionary (or None to create new)

    Returns:
        Headers dictionary with request ID headers added

    Example:
        headers = with_request_id_headers({"Authorization": "Bearer token"})
        response = requests.get(url, headers=headers)
    """
    result = dict(headers) if headers else {}
    request_id = get_request_id()

    if request_id:
        result[REQUEST_ID_HEADER] = request_id
        result[CORRELATION_ID_HEADER] = request_id

    return result


def extract_request_id_from_headers(headers: Dict[str, str]) -> Optional[str]:
    """
    Extract request ID from incoming headers.

    Checks multiple header names for compatibility with different systems.

    Args:
        headers: Request headers dictionary

    Returns:
        Request ID if found, None otherwise
    """
    # Check common header names in order of preference
    header_names = [
        REQUEST_ID_HEADER,
        CORRELATION_ID_HEADER,
        "X-Trace-ID",
        "X-Amzn-Trace-Id",  # AWS
        "traceparent",  # W3C Trace Context
    ]

    for name in header_names:
        value = headers.get(name)
        if value:
            return value

    return None


class RequestIDLogFilter(logging.Filter):
    """
    Logging filter that adds request ID to all log records.

    This ensures every log entry includes the request ID without
    requiring explicit passing of the ID.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id attribute to log record."""
        record.request_id = get_request_id() or "-"
        return True


class RequestIDFormatter(logging.Formatter):
    """
    Log formatter that includes request ID in the message format.

    Format: timestamp | level | request_id | logger | message
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        include_request_id: bool = True
    ):
        if fmt is None:
            if include_request_id:
                fmt = "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)-20s | %(message)s"
            else:
                fmt = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"

        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with request ID."""
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id() or "-"
        return super().format(record)


def configure_logging_with_request_id() -> None:
    """
    Configure all loggers to include request ID in their output.

    This adds the RequestIDLogFilter to the root logger, ensuring
    all log entries include the request ID.
    """
    root_logger = logging.getLogger()

    # Add filter to root logger
    request_id_filter = RequestIDLogFilter()
    root_logger.addFilter(request_id_filter)

    # Update existing handlers to use RequestIDFormatter
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            # Only update if not already using JSON formatter
            if not handler.formatter or "json" not in type(handler.formatter).__name__.lower():
                handler.setFormatter(RequestIDFormatter())

    logger.info("Request ID logging configured")


def init_request_id_middleware(app) -> None:
    """
    Initialize Flask middleware for request ID tracking.

    This middleware:
    - Extracts or generates request ID for each request
    - Adds request ID to response headers
    - Cleans up after request completes

    Args:
        app: Flask application instance
    """

    @app.before_request
    def set_request_id_before():
        """Set request ID at the start of each request."""
        from flask import request, g

        # Try to extract from incoming headers, or generate new
        incoming_id = extract_request_id_from_headers(dict(request.headers))
        request_id = incoming_id or generate_request_id()

        # Set in both Flask g and context var
        g.request_id = request_id
        g.correlation_id = request_id  # Backward compatibility
        set_request_id(request_id)

        logger.debug(f"Request started: {request_id}")

    @app.after_request
    def add_request_id_header(response):
        """Add request ID to response headers."""
        request_id = get_request_id()
        if request_id:
            response.headers[REQUEST_ID_HEADER] = request_id
            response.headers[CORRELATION_ID_HEADER] = request_id
        return response

    @app.teardown_request
    def cleanup_request_id(exception=None):
        """Clean up request ID after request completes."""
        clear_request_id()

    logger.info("Request ID middleware initialized")


def add_request_id_to_error_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add request ID to an error response dictionary.

    Args:
        response_data: The error response dictionary

    Returns:
        Response dictionary with request_id added

    Example:
        error_response = add_request_id_to_error_response({
            "success": False,
            "error": "Something went wrong"
        })
        # Returns: {"success": False, "error": "...", "request_id": "20260126T153045-a1b2c3d4"}
    """
    result = dict(response_data)
    request_id = get_request_id()
    if request_id:
        result["request_id"] = request_id
    return result


def log_with_request_id(
    logger_instance: logging.Logger,
    level: int,
    message: str,
    **extra_fields
) -> None:
    """
    Log a message with request ID included in extra data.

    Args:
        logger_instance: Logger to use
        level: Log level (e.g., logging.INFO)
        message: Log message
        **extra_fields: Additional fields to include
    """
    request_id = get_request_id()
    extra_data = {
        "request_id": request_id,
        **extra_fields
    }

    logger_instance.log(
        level,
        message,
        extra={"extra_data": extra_data}
    )


def request_id_context(request_id: Optional[str] = None):
    """
    Context manager for setting request ID in non-Flask contexts.

    Useful for background tasks, CLI commands, or tests.

    Args:
        request_id: Request ID to use, or None to generate new

    Example:
        with request_id_context("test-request-123"):
            # All logs in this block will include the request ID
            do_something()
    """
    class RequestIDContext:
        def __init__(self, rid: Optional[str]):
            self.request_id = rid or generate_request_id()
            self.previous_id: Optional[str] = None

        def __enter__(self):
            self.previous_id = get_request_id()
            set_request_id(self.request_id)
            return self.request_id

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.previous_id:
                set_request_id(self.previous_id)
            else:
                clear_request_id()
            return False

    return RequestIDContext(request_id)


def with_request_id(func: Callable) -> Callable:
    """
    Decorator to ensure a function runs with a request ID.

    If no request ID is set, generates a new one for the duration
    of the function call.

    Example:
        @with_request_id
        def background_task():
            logger.info("Processing...")  # Will include request ID
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if get_request_id() is None:
            with request_id_context():
                return func(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper


# HTTP client helpers for common libraries

def requests_session_with_request_id():
    """
    Create a requests.Session that automatically includes request ID headers.

    Returns:
        requests.Session with request ID headers hook

    Example:
        session = requests_session_with_request_id()
        response = session.get("https://api.example.com/data")
    """
    try:
        import requests

        session = requests.Session()

        def add_request_id_hook(request, *args, **kwargs):
            request_id = get_request_id()
            if request_id:
                request.headers[REQUEST_ID_HEADER] = request_id
                request.headers[CORRELATION_ID_HEADER] = request_id
            return request

        session.hooks["prepare_request"] = add_request_id_hook
        return session
    except ImportError:
        logger.warning("requests library not available")
        return None


def httpx_client_with_request_id():
    """
    Create an httpx.Client that automatically includes request ID headers.

    Returns:
        httpx.Client with request ID event hook

    Example:
        client = httpx_client_with_request_id()
        response = client.get("https://api.example.com/data")
    """
    try:
        import httpx

        def add_request_id_event(request: httpx.Request):
            request_id = get_request_id()
            if request_id:
                request.headers[REQUEST_ID_HEADER] = request_id
                request.headers[CORRELATION_ID_HEADER] = request_id

        return httpx.Client(event_hooks={"request": [add_request_id_event]})
    except ImportError:
        logger.warning("httpx library not available")
        return None


# Convenience exports
__all__ = [
    # Core functions
    "generate_request_id",
    "get_request_id",
    "set_request_id",
    "clear_request_id",
    # Header helpers
    "with_request_id_headers",
    "extract_request_id_from_headers",
    "REQUEST_ID_HEADER",
    "CORRELATION_ID_HEADER",
    # Logging
    "RequestIDLogFilter",
    "RequestIDFormatter",
    "configure_logging_with_request_id",
    "log_with_request_id",
    # Flask integration
    "init_request_id_middleware",
    # Error responses
    "add_request_id_to_error_response",
    # Context managers and decorators
    "request_id_context",
    "with_request_id",
    # HTTP clients
    "requests_session_with_request_id",
    "httpx_client_with_request_id",
]
