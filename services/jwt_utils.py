import datetime
from functools import wraps
from typing import Optional

import jwt
from flask import jsonify, request

from services.config import config

# Use secure secret from config (not hardcoded)
SECRET_KEY = config.SECRET_KEY


def create_token(user_id: Optional[int] = None, scopes: Optional[list] = None):
    """
    Generate a JWT token for API access (7-day expiry).

    Args:
        user_id: Optional user/staff ID to embed in token
        scopes: Optional list of permission scopes

    Returns:
        JWT token string
    """
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "iat": datetime.datetime.utcnow(),
        "scope": "fcra_access",
    }
    if user_id:
        payload["sub"] = user_id
    if scopes:
        payload["scopes"] = scopes

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def require_jwt(f):
    """Decorator to protect Flask routes with JWT authentication"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401

        token = auth_header.split(" ")[1]

        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except Exception as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401

        return f(*args, **kwargs)

    return wrapper
