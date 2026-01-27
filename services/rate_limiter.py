"""
Rate Limiting Configuration for FCRA Litigation Platform

Prevents abuse by limiting API requests per user/IP.
Uses Flask-Limiter with in-memory storage (can upgrade to Redis for production).
"""

import os

from flask import jsonify, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Check if running in CI/test mode - disable rate limiting for tests
def is_testing_mode():
    """Check if running in CI/test mode at runtime."""
    return (
        os.environ.get("CI", "").lower() == "true" or
        os.environ.get("CYPRESS_TEST", "").lower() == "true" or
        os.environ.get("TESTING", "").lower() == "true"
    )

IS_CI = is_testing_mode()

# Get rate limit settings from environment or use defaults
DEFAULT_RATE = os.environ.get("RATE_LIMIT_DEFAULT", "200 per minute")
AUTH_RATE = os.environ.get("RATE_LIMIT_AUTH", "5 per minute")  # Stricter for login
API_RATE = os.environ.get("RATE_LIMIT_API", "100 per minute")
ANALYSIS_RATE = os.environ.get(
    "RATE_LIMIT_ANALYSIS", "10 per minute"
)  # AI calls are expensive


def get_rate_limit_key():
    """
    Get the key for rate limiting.
    Uses staff_id if authenticated, otherwise IP address.
    """
    if session.get("staff_id"):
        return f"staff:{session['staff_id']}"
    return get_remote_address()


def init_rate_limiter(app):
    """Initialize rate limiter on Flask app."""

    limiter = Limiter(
        key_func=get_rate_limit_key,
        app=app,
        default_limits=[DEFAULT_RATE],
        storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
        strategy="fixed-window",
        headers_enabled=True,  # Adds X-RateLimit headers to responses
        enabled=not is_testing_mode(),  # Disable rate limiting in CI/test mode
    )

    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        from services.logging_config import api_logger
        from services.rate_limit_monitor_service import get_rate_limit_monitor, is_ip_blocked

        ip_address = get_remote_address()
        endpoint = request.path
        user_agent = request.headers.get("User-Agent", "")

        api_logger.warning(
            f"Rate limit exceeded: {get_rate_limit_key()} - {endpoint}"
        )

        # Record violation in monitor
        monitor = get_rate_limit_monitor()
        if monitor:
            was_blocked = monitor.record_violation(
                ip_address=ip_address,
                endpoint=endpoint,
                user_agent=user_agent,
                key=get_rate_limit_key(),
            )
            if was_blocked:
                api_logger.error(f"IP blocked due to repeated violations: {ip_address}")

        return (
            jsonify(
                {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please slow down.",
                    "retry_after": e.description,
                }
            ),
            429,
        )

    return limiter


# Rate limit decorators for different endpoint types
def get_rate_limits():
    """
    Returns rate limit decorators for different endpoint categories.
    Usage:
        limits = get_rate_limits()

        @app.route('/api/analyze')
        @limits['analysis']
        def analyze():
            ...
    """
    return {
        "default": DEFAULT_RATE,
        "auth": AUTH_RATE,  # Login/logout - prevent brute force
        "api": API_RATE,  # Standard API endpoints
        "analysis": ANALYSIS_RATE,  # AI analysis - expensive operations
        "unlimited": None,  # Health checks, static files
    }


# Pre-defined rate limit strings
RATE_LIMITS = {
    # Authentication - strict to prevent brute force
    "login": "5 per minute",
    "password_reset": "3 per minute",
    # API endpoints - moderate limits
    "api_read": "100 per minute",
    "api_write": "30 per minute",
    # Expensive operations - strict limits
    "ai_analysis": "10 per minute",
    "pdf_generation": "20 per minute",
    "email_send": "10 per minute",
    # Bulk operations - very strict
    "bulk_action": "5 per minute",
    "export": "5 per minute",
    # Webhooks - allow more for integrations
    "webhook": "60 per minute",
}


def exempt_when_authenticated(f):
    """
    Decorator to exempt authenticated staff from rate limits.
    Still applies limits to unauthenticated requests.
    """
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("staff_id"):
            # Staff members get higher limits
            return f(*args, **kwargs)
        return f(*args, **kwargs)

    return decorated_function
