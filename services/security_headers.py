"""
Security Headers and HTTPS Enforcement Middleware

Provides:
- HTTPS redirect for production environments
- Strict-Transport-Security (HSTS) header
- Content-Security-Policy header
- X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- Referrer-Policy and Permissions-Policy
- Secure cookie enforcement

Usage:
    from services.security_headers import init_security_headers

    app = Flask(__name__)
    init_security_headers(app)
"""

from functools import wraps

from flask import g, redirect, request

from services.config import config


def init_security_headers(app, force_https=None, hsts_max_age=31536000):
    """
    Initialize security headers middleware.

    Args:
        app: Flask application
        force_https: Force HTTPS redirects (default: True in production)
        hsts_max_age: HSTS max-age in seconds (default: 1 year)
    """
    # Determine if we should enforce HTTPS
    if force_https is None:
        force_https = config.IS_PRODUCTION and not config.IS_CI

    @app.before_request
    def enforce_https():
        """Redirect HTTP to HTTPS in production."""
        if not force_https:
            return None

        # Check if request is already HTTPS
        # Handle reverse proxy headers (X-Forwarded-Proto)
        is_https = (
            request.is_secure
            or request.headers.get("X-Forwarded-Proto", "http") == "https"
            or request.headers.get("X-Forwarded-Ssl", "") == "on"
        )

        if not is_https:
            # Skip for health checks and localhost
            if request.path == "/" or request.host.startswith("localhost"):
                return None

            # Redirect to HTTPS
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)

        return None

    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""

        # Only add HSTS in production over HTTPS
        if force_https or config.IS_PRODUCTION:
            # Strict-Transport-Security (HSTS)
            # Tells browsers to only use HTTPS for this domain
            response.headers["Strict-Transport-Security"] = (
                f"max-age={hsts_max_age}; includeSubDomains; preload"
            )

        # X-Frame-Options - Prevent clickjacking
        # SAMEORIGIN allows embedding in same-origin frames only
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # X-Content-Type-Options - Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection - Enable browser XSS filter (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy - Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy - Disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), " "microphone=(), " "camera=(), " "payment=(), " "usb=()"
        )

        # Content-Security-Policy - Prevent XSS and data injection
        # This is a relatively permissive policy - tighten for production
        if not request.path.startswith("/static/"):
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' https://api.anthropic.com",
                "frame-ancestors 'self'",
                "form-action 'self'",
                "base-uri 'self'",
                "object-src 'none'",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Cache-Control for sensitive pages
        if request.path.startswith("/api/") or request.path.startswith("/dashboard/"):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )
            response.headers["Pragma"] = "no-cache"

        return response

    # Configure secure session cookies
    app.config.update(
        SESSION_COOKIE_SECURE=force_https or config.IS_PRODUCTION,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )


def require_https(f):
    """
    Decorator to require HTTPS for specific endpoints.
    Use for extra-sensitive endpoints even in development.

    Usage:
        @app.route('/api/sensitive')
        @require_https
        def sensitive_endpoint():
            ...
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_https = (
            request.is_secure
            or request.headers.get("X-Forwarded-Proto", "http") == "https"
        )

        if not is_https and config.IS_PRODUCTION:
            return {"success": False, "error": "HTTPS required for this endpoint"}, 403

        return f(*args, **kwargs)

    return decorated_function


# Security header values for reference
SECURITY_HEADERS = {
    "Strict-Transport-Security": "Enforces HTTPS connections",
    "X-Frame-Options": "Prevents clickjacking attacks",
    "X-Content-Type-Options": "Prevents MIME type sniffing",
    "X-XSS-Protection": "Enables browser XSS filter",
    "Content-Security-Policy": "Prevents XSS and injection attacks",
    "Referrer-Policy": "Controls referrer information leakage",
    "Permissions-Policy": "Disables unnecessary browser features",
}
