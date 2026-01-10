"""
API Authentication and Authorization Service

Provides:
- @require_api_key decorator for API key authentication with scope checking
- @require_auth decorator for flexible auth (session OR API key)
- JWT token generation and validation with secure secret
- Rate limit headers on API responses
- Request logging for authenticated API calls

Usage:
    from services.api_auth import require_api_key, require_auth

    @app.route('/api/clients')
    @require_api_key(scopes=['read:clients'])
    def get_clients():
        # g.api_key contains the authenticated APIKey object
        return jsonify(clients)

    @app.route('/api/analyze')
    @require_auth(scopes=['analyze:reports'])  # Accepts session OR API key
    def analyze():
        # g.auth_type is 'session' or 'api_key'
        return jsonify(result)
"""

import hashlib
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import List, Optional

import jwt
from flask import g, jsonify, make_response, request, session

from database import API_SCOPES, APIKey, APIRequest, get_db
from services.api_access_service import APIAccessService, rate_limiter
from services.config import config

# Use config secret or fallback for JWT
JWT_SECRET = config.SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7


def create_jwt_token(
    user_id: Optional[int] = None,
    scopes: Optional[List[str]] = None,
    expires_in_days: int = JWT_EXPIRY_DAYS,
) -> str:
    """
    Generate a JWT token for API access.

    Args:
        user_id: Optional user/staff ID to embed in token
        scopes: List of permission scopes for this token
        expires_in_days: Token expiration in days (default 7)

    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    payload = {
        "iat": now,
        "exp": now + timedelta(days=expires_in_days),
        "type": "api_access",
    }
    if user_id:
        payload["sub"] = user_id
    if scopes:
        payload["scopes"] = scopes

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def validate_jwt_token(token: str) -> tuple:
    """
    Validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        (payload, error) - payload dict if valid, error string if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError as e:
        return None, f"Invalid token: {str(e)}"


def get_api_key_from_request() -> Optional[str]:
    """
    Extract API key from request headers.
    Supports:
    - X-API-Key header
    - Authorization: Bearer <key>
    - Authorization: ApiKey <key>
    """
    # Check X-API-Key header first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key.strip()

    # Check Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    if auth_header.lower().startswith("apikey "):
        return auth_header[7:].strip()

    return None


def add_rate_limit_headers(response, rate_info: dict):
    """Add rate limit headers to response."""
    if rate_info:
        response.headers["X-RateLimit-Limit-Minute"] = str(
            rate_info.get("minute_limit", 60)
        )
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            rate_info.get("minute_remaining", 0)
        )
        response.headers["X-RateLimit-Limit-Day"] = str(
            rate_info.get("day_limit", 10000)
        )
        response.headers["X-RateLimit-Remaining-Day"] = str(
            rate_info.get("day_remaining", 0)
        )
    return response


def log_api_request(
    api_key_id: int, response_status: int, start_time: float, error: Optional[str] = None
) -> None:
    """Log an API request for analytics."""
    try:
        duration_ms = int((time.time() - start_time) * 1000)
        db = get_db()
        try:
            api_request = APIRequest(
                api_key_id=api_key_id,
                endpoint=request.path,
                method=request.method,
                request_ip=request.headers.get("X-Forwarded-For", request.remote_addr),
                response_status=response_status,
                response_time_ms=duration_ms,
                error_message=error,
            )
            db.add(api_request)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        # Don't fail the request if logging fails
        print(f"API request logging failed: {e}")


def require_api_key(scopes: Optional[List[str]] = None):
    """
    Decorator to require API key authentication.

    Args:
        scopes: List of required scopes (e.g., ['read:clients', 'write:clients'])
                If None, any valid API key is accepted.

    Usage:
        @app.route('/api/clients')
        @require_api_key(scopes=['read:clients'])
        def get_clients():
            # Access authenticated key via g.api_key
            return jsonify(clients)
    """
    scopes = scopes or []

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            # Extract API key from request
            raw_key = get_api_key_from_request()
            if not raw_key:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "API key required",
                            "message": "Provide API key via X-API-Key header or Authorization: Bearer <key>",
                        }
                    ),
                    401,
                )

            # Validate API key
            db = get_db()
            try:
                key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
                key_prefix = raw_key[:8] if len(raw_key) >= 8 else ""

                api_key = (
                    db.query(APIKey)
                    .filter(
                        APIKey.key_hash == key_hash, APIKey.key_prefix == key_prefix
                    )
                    .first()
                )

                if not api_key:
                    log_api_request(0, 401, start_time, "Invalid API key")
                    return jsonify({"success": False, "error": "Invalid API key"}), 401

                if not api_key.is_active:
                    log_api_request(api_key.id, 401, start_time, "API key revoked")
                    return (
                        jsonify(
                            {"success": False, "error": "API key has been revoked"}
                        ),
                        401,
                    )

                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    log_api_request(api_key.id, 401, start_time, "API key expired")
                    return (
                        jsonify({"success": False, "error": "API key has expired"}),
                        401,
                    )

                # Check scopes
                key_scopes = api_key.scopes or []
                missing_scopes = [s for s in scopes if s not in key_scopes]
                if missing_scopes:
                    log_api_request(
                        api_key.id, 403, start_time, f"Missing scopes: {missing_scopes}"
                    )
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "Insufficient permissions",
                                "required_scopes": scopes,
                                "missing_scopes": missing_scopes,
                            }
                        ),
                        403,
                    )

                # Check rate limits
                allowed, rate_info = rate_limiter.check_and_increment(
                    api_key.id,
                    api_key.rate_limit_per_minute or 60,
                    api_key.rate_limit_per_day or 10000,
                )

                if not allowed:
                    log_api_request(api_key.id, 429, start_time, "Rate limit exceeded")
                    response = make_response(
                        jsonify(
                            {
                                "success": False,
                                "error": "Rate limit exceeded",
                                "rate_limits": rate_info,
                            }
                        ),
                        429,
                    )
                    return add_rate_limit_headers(response, rate_info)

                # Update last used
                api_key.last_used_at = datetime.utcnow()
                api_key.last_used_ip = request.headers.get(
                    "X-Forwarded-For", request.remote_addr
                )
                api_key.usage_count = (api_key.usage_count or 0) + 1
                db.commit()

                # Store API key in g for access in the route
                g.api_key = api_key
                g.auth_type = "api_key"
                g.rate_info = rate_info

                # Execute the route
                result = f(*args, **kwargs)

                # Add rate limit headers to response
                if isinstance(result, tuple):
                    response = make_response(
                        result[0], result[1] if len(result) > 1 else 200
                    )
                else:
                    response = make_response(result)

                response = add_rate_limit_headers(response, rate_info)

                # Log successful request
                log_api_request(api_key.id, response.status_code, start_time)

                return response

            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()

        return decorated_function

    return decorator


def require_auth(
    scopes: Optional[List[str]] = None, allow_session: bool = True, allow_api_key: bool = True
):
    """
    Flexible authentication decorator that accepts session auth OR API key.

    Args:
        scopes: Required scopes for API key auth (ignored for session auth)
        allow_session: Accept session-based authentication
        allow_api_key: Accept API key authentication

    Sets g.auth_type to 'session' or 'api_key'
    Sets g.api_key if API key auth is used
    """
    scopes = scopes or []

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            # Try session auth first
            if allow_session and "staff_id" in session:
                g.auth_type = "session"
                g.staff_id = session["staff_id"]
                return f(*args, **kwargs)

            # Try API key auth
            if allow_api_key:
                raw_key = get_api_key_from_request()
                if raw_key:
                    # Use the require_api_key logic
                    db = get_db()
                    try:
                        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
                        key_prefix = raw_key[:8] if len(raw_key) >= 8 else ""

                        api_key = (
                            db.query(APIKey)
                            .filter(
                                APIKey.key_hash == key_hash,
                                APIKey.key_prefix == key_prefix,
                            )
                            .first()
                        )

                        if api_key and api_key.is_active:
                            # Check expiration
                            if (
                                api_key.expires_at
                                and api_key.expires_at < datetime.utcnow()
                            ):
                                return (
                                    jsonify(
                                        {
                                            "success": False,
                                            "error": "API key has expired",
                                        }
                                    ),
                                    401,
                                )

                            # Check scopes
                            key_scopes = api_key.scopes or []
                            missing_scopes = [s for s in scopes if s not in key_scopes]
                            if missing_scopes:
                                return (
                                    jsonify(
                                        {
                                            "success": False,
                                            "error": "Insufficient permissions",
                                            "missing_scopes": missing_scopes,
                                        }
                                    ),
                                    403,
                                )

                            # Check rate limits
                            allowed, rate_info = rate_limiter.check_and_increment(
                                api_key.id,
                                api_key.rate_limit_per_minute or 60,
                                api_key.rate_limit_per_day or 10000,
                            )

                            if not allowed:
                                response = make_response(
                                    jsonify(
                                        {
                                            "success": False,
                                            "error": "Rate limit exceeded",
                                        }
                                    ),
                                    429,
                                )
                                return add_rate_limit_headers(response, rate_info)

                            # Update usage
                            api_key.last_used_at = datetime.utcnow()
                            api_key.usage_count = (api_key.usage_count or 0) + 1
                            db.commit()

                            g.api_key = api_key
                            g.auth_type = "api_key"
                            g.rate_info = rate_info

                            result = f(*args, **kwargs)

                            if isinstance(result, tuple):
                                response = make_response(
                                    result[0], result[1] if len(result) > 1 else 200
                                )
                            else:
                                response = make_response(result)

                            return add_rate_limit_headers(response, rate_info)

                    finally:
                        db.close()

            # No valid auth found
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Authentication required",
                        "message": "Provide session cookie or API key via X-API-Key header",
                    }
                ),
                401,
            )

        return decorated_function

    return decorator


def require_scope(scope: str):
    """
    Decorator to require a specific scope.
    Must be used after @require_api_key or @require_auth.

    Usage:
        @app.route('/api/clients')
        @require_api_key()
        @require_scope('read:clients')
        def get_clients():
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.auth_type == "api_key":
                key_scopes = g.api_key.scopes or []
                if scope not in key_scopes:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "Insufficient permissions",
                                "required_scope": scope,
                            }
                        ),
                        403,
                    )
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Available scopes for documentation
AVAILABLE_SCOPES = {
    "read:clients": "Read client information",
    "write:clients": "Create and update clients",
    "delete:clients": "Delete clients",
    "read:cases": "Read case information",
    "write:cases": "Create and update cases",
    "read:disputes": "Read dispute information",
    "write:disputes": "Create and manage disputes",
    "analyze:reports": "Submit credit reports for AI analysis",
    "read:letters": "Read and download dispute letters",
    "write:letters": "Generate dispute letters",
    "manage:webhooks": "Create and manage webhooks",
    "admin:keys": "Manage API keys (admin only)",
    "admin:users": "Manage staff users (admin only)",
}
