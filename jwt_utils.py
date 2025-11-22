import jwt
import datetime
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "fcra_automation_secret_key_change_in_production"

def create_token():
    """Generate a JWT token for API access (7-day expiry)"""
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "iat": datetime.datetime.utcnow(),
        "scope": "fcra_access"
    }
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
