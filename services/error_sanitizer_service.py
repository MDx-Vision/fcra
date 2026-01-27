"""
Error Sanitization Service for FCRA Platform

Prevents internal error details from leaking to clients:
- Database errors (table names, queries)
- File paths
- Stack traces
- Internal service names

Logs full errors server-side while returning generic messages to clients.
"""

import logging
import os
import re
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from flask import jsonify, request

# Environment check
IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production" or os.environ.get("PRODUCTION") == "true"
DEBUG_ERRORS = os.environ.get("DEBUG_ERRORS", "false").lower() == "true"

# Logger for server-side error logging
error_logger = logging.getLogger("error_sanitizer")


# Error code mapping for common error types
ERROR_CODES = {
    "database": "ERR_DB_001",
    "validation": "ERR_VAL_001",
    "authentication": "ERR_AUTH_001",
    "authorization": "ERR_AUTHZ_001",
    "not_found": "ERR_NF_001",
    "external_service": "ERR_EXT_001",
    "file_operation": "ERR_FILE_001",
    "rate_limit": "ERR_RATE_001",
    "payment": "ERR_PAY_001",
    "internal": "ERR_INT_001",
}

# Generic messages for each error type
GENERIC_MESSAGES = {
    "database": "A database error occurred. Please try again later.",
    "validation": "Invalid request data. Please check your input.",
    "authentication": "Authentication failed. Please log in again.",
    "authorization": "You don't have permission to perform this action.",
    "not_found": "The requested resource was not found.",
    "external_service": "An external service is temporarily unavailable.",
    "file_operation": "A file operation error occurred.",
    "rate_limit": "Too many requests. Please try again later.",
    "payment": "A payment processing error occurred.",
    "internal": "An unexpected error occurred. Please try again later.",
}

# Patterns that indicate sensitive information
SENSITIVE_PATTERNS = [
    r"/Users/[^/]+",  # macOS user paths
    r"/home/[^/]+",  # Linux user paths
    r"C:\\Users\\[^\\]+",  # Windows user paths
    r"password|secret|key|token|credential",  # Sensitive keywords
    r"postgresql://[^@]+@",  # Database connection strings
    r"mysql://[^@]+@",
    r"sqlite:///",
    r"SQLSTATE\[[^\]]+\]",  # SQL state codes
    r"at line \d+",  # Line numbers
    r"File \"[^\"]+\"",  # File paths in tracebacks
    r"Traceback \(most recent call last\)",  # Stack traces
]


def classify_error(error: Exception) -> str:
    """
    Classify an error into a category based on its type and message.

    Args:
        error: The exception to classify

    Returns:
        Error category string
    """
    error_type = type(error).__name__
    error_msg = str(error).lower()

    # File operation errors - check type first (before "not found" check)
    if error_type in ["FileNotFoundError", "IOError", "PermissionError", "IsADirectoryError", "NotADirectoryError"]:
        return "file_operation"
    if "file" in error_msg and ("read" in error_msg or "write" in error_msg or "open" in error_msg):
        return "file_operation"

    # Database errors
    if any(db_type in error_type for db_type in ["SQLAlchemy", "Database", "Postgres", "MySQL", "IntegrityError", "OperationalError"]):
        return "database"
    if "database" in error_msg or "sql" in error_msg or "query" in error_msg:
        return "database"

    # Validation errors
    if "ValidationError" in error_type or "ValueError" in error_type:
        return "validation"
    if "invalid" in error_msg or "required" in error_msg or "missing" in error_msg:
        return "validation"

    # Authentication errors
    if "auth" in error_type.lower() or "login" in error_msg or "password" in error_msg:
        return "authentication"

    # Authorization errors
    if "permission" in error_msg or "forbidden" in error_msg or "access denied" in error_msg:
        return "authorization"

    # Not found errors
    if "NotFound" in error_type or "not found" in error_msg or "does not exist" in error_msg:
        return "not_found"

    # External service errors
    if any(svc in error_msg for svc in ["stripe", "twilio", "sendgrid", "api", "timeout", "connection"]):
        return "external_service"

    # Rate limit errors
    if "rate" in error_msg and "limit" in error_msg:
        return "rate_limit"

    # Payment errors
    if "payment" in error_msg or "charge" in error_msg or "card" in error_msg:
        return "payment"

    return "internal"


def contains_sensitive_info(message: str) -> bool:
    """
    Check if a message contains sensitive information.

    Args:
        message: The message to check

    Returns:
        True if sensitive info is found
    """
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return True
    return False


def generate_error_id() -> str:
    """Generate a unique error ID for tracking."""
    return f"ERR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"


def log_error_server_side(
    error: Exception,
    error_id: str,
    category: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log full error details server-side only.

    Args:
        error: The exception
        error_id: Unique error ID
        category: Error category
        context: Additional context
    """
    # Get request ID for correlation
    request_id = None
    try:
        from services.request_id_service import get_request_id
        request_id = get_request_id()
    except ImportError:
        pass

    log_data = {
        "error_id": error_id,
        "request_id": request_id,
        "category": category,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Add request context if available
    try:
        log_data["path"] = request.path
        log_data["method"] = request.method
        log_data["remote_addr"] = request.remote_addr
        log_data["user_agent"] = request.headers.get("User-Agent", "")[:100]
    except RuntimeError:
        # Outside of request context
        pass

    # Add custom context
    if context:
        log_data["context"] = context

    # Log with full traceback
    error_logger.error(
        f"[{error_id}] {category.upper()}: {type(error).__name__}: {str(error)}",
        extra=log_data,
        exc_info=True
    )


def sanitize_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    include_error_id: bool = True
) -> Dict[str, Any]:
    """
    Sanitize an error for client response.

    Args:
        error: The exception to sanitize
        context: Additional context for logging
        include_error_id: Whether to include error ID in response

    Returns:
        Sanitized error dict safe for client response
    """
    error_id = generate_error_id()
    category = classify_error(error)

    # Always log full error server-side
    log_error_server_side(error, error_id, category, context)

    # In debug mode or non-production, return more details
    if DEBUG_ERRORS or not IS_PRODUCTION:
        error_msg = str(error)
        # Still sanitize sensitive patterns even in debug
        if contains_sensitive_info(error_msg):
            error_msg = GENERIC_MESSAGES.get(category, GENERIC_MESSAGES["internal"])
    else:
        # Production: always use generic message
        error_msg = GENERIC_MESSAGES.get(category, GENERIC_MESSAGES["internal"])

    result = {
        "success": False,
        "error": error_msg,
        "error_code": ERROR_CODES.get(category, ERROR_CODES["internal"]),
    }

    if include_error_id:
        result["error_id"] = error_id

    # Add request ID for correlation
    try:
        from services.request_id_service import get_request_id
        request_id = get_request_id()
        if request_id:
            result["request_id"] = request_id
    except ImportError:
        pass

    return result


def sanitize_error_response(
    error: Exception,
    status_code: int = 500,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[Any, int]:
    """
    Create a sanitized Flask JSON response for an error.

    Args:
        error: The exception
        status_code: HTTP status code
        context: Additional context for logging

    Returns:
        Tuple of (Flask response, status code)
    """
    sanitized = sanitize_error(error, context)
    return jsonify(sanitized), status_code


def safe_error_message(error: Exception, default: str = "An error occurred") -> str:
    """
    Get a safe error message for client display.

    This is a simple helper for cases where you just need a string,
    not a full JSON response.

    Args:
        error: The exception
        default: Default message if error can't be safely displayed

    Returns:
        Safe error message string
    """
    if DEBUG_ERRORS or not IS_PRODUCTION:
        error_msg = str(error)
        if not contains_sensitive_info(error_msg):
            return error_msg

    category = classify_error(error)
    return GENERIC_MESSAGES.get(category, default)


# Convenience function for quick sanitization
def handle_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> Tuple[Any, int]:
    """
    Handle an exception with full sanitization and logging.

    Usage in route handlers:
        try:
            # ... code ...
        except Exception as e:
            return handle_exception(e)

    Args:
        error: The exception
        context: Additional context
        status_code: HTTP status code

    Returns:
        Sanitized Flask JSON response tuple
    """
    return sanitize_error_response(error, status_code, context)
