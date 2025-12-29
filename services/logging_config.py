"""
Comprehensive Logging Configuration for FCRA Litigation Platform

Provides structured logging with:
- Request/response logging
- Error tracking with stack traces
- Performance monitoring
- Audit trail for user actions
- Database query logging
"""

import json
import logging
import logging.handlers
import os
import sys
import time
import traceback
from datetime import datetime
from functools import wraps

# Log levels
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# JSON format for structured logging (production)
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_logging(app=None):
    """Configure logging for the application."""

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))

    # Clear existing handlers
    root_logger.handlers = []

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Use JSON format in production, readable format in development
    if os.environ.get("FLASK_ENV") == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    root_logger.addHandler(console_handler)

    # File handler for errors (rotates at 10MB, keeps 5 backups)
    try:
        os.makedirs("logs", exist_ok=True)
        error_handler = logging.handlers.RotatingFileHandler(
            "logs/error.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(error_handler)

        # Audit log for important actions
        audit_handler = logging.handlers.RotatingFileHandler(
            "logs/audit.log", maxBytes=10 * 1024 * 1024, backupCount=10
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logging.getLogger("audit").addHandler(audit_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")

    # Reduce noise from third-party libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger


# Application loggers
def get_logger(name):
    """Get a logger for a specific module."""
    return logging.getLogger(name)


# Specialized loggers
app_logger = get_logger("app")
api_logger = get_logger("api")
db_logger = get_logger("database")
ai_logger = get_logger("ai")
audit_logger = get_logger("audit")
perf_logger = get_logger("performance")


def log_request(request):
    """Log incoming HTTP request."""
    api_logger.info(
        f"REQUEST {request.method} {request.path}",
        extra={
            "extra_data": {
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": str(request.user_agent),
                "content_length": request.content_length,
            }
        },
    )


def log_response(response, duration_ms):
    """Log HTTP response."""
    level = logging.INFO if response.status_code < 400 else logging.WARNING
    api_logger.log(
        level,
        f"RESPONSE {response.status_code} ({duration_ms:.0f}ms)",
        extra={
            "extra_data": {
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        },
    )


def log_error(error, context=None):
    """Log an error with full context."""
    app_logger.error(
        f"ERROR: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra={"extra_data": {"context": context or {}}},
    )


def log_audit(action, user_id=None, client_id=None, details=None):
    """Log an audit event for compliance tracking."""
    audit_logger.info(
        f"AUDIT: {action}",
        extra={
            "extra_data": {
                "action": action,
                "user_id": user_id,
                "client_id": client_id,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )


def log_ai_request(model, tokens_in, tokens_out, cost, duration_ms):
    """Log AI API request for cost tracking."""
    ai_logger.info(
        f"AI: {model} | tokens: {tokens_in}→{tokens_out} | ${cost:.4f} | {duration_ms:.0f}ms",
        extra={
            "extra_data": {
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost": cost,
                "duration_ms": duration_ms,
            }
        },
    )


def log_db_query(query, duration_ms):
    """Log slow database queries."""
    if duration_ms > 100:  # Log queries slower than 100ms
        db_logger.warning(f"SLOW QUERY ({duration_ms:.0f}ms): {query[:200]}")


def log_performance(operation, duration_ms, details=None):
    """Log performance metrics."""
    level = logging.WARNING if duration_ms > 1000 else logging.DEBUG
    perf_logger.log(
        level,
        f"PERF: {operation} took {duration_ms:.0f}ms",
        extra={
            "extra_data": {
                "operation": operation,
                "duration_ms": duration_ms,
                **(details or {}),
            }
        },
    )


# Decorator for timing functions
def timed(func):
    """Decorator to log function execution time."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            if duration_ms > 500:  # Log slow functions
                perf_logger.info(f"SLOW: {func.__name__} took {duration_ms:.0f}ms")
            return result
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            log_error(
                e, context={"function": func.__name__, "duration_ms": duration_ms}
            )
            raise

    return wrapper


# Flask middleware for request logging
def init_request_logging(app):
    """Initialize request/response logging middleware."""

    @app.before_request
    def before_request():
        from flask import g, request

        g.start_time = time.time()
        log_request(request)

    @app.after_request
    def after_request(response):
        from flask import g

        if hasattr(g, "start_time"):
            duration_ms = (time.time() - g.start_time) * 1000
            log_response(response, duration_ms)
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        from flask import request

        log_error(e, context={"path": request.path, "method": request.method})
        # Re-raise to let Flask handle it
        raise e

    app_logger.info("Request logging middleware initialized")
