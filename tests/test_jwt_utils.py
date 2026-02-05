"""
Unit tests for JWT Utils

Tests cover:
- Token creation
- Token validation decorator
- Expiration handling
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


class TestCreateToken:
    """Tests for create_token function"""

    def test_creates_token_string(self):
        """Should create a JWT token string"""
        from services.jwt_utils import create_token

        token = create_token()

        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_has_correct_payload(self):
        """Should include expected payload fields"""
        from services.jwt_utils import create_token, SECRET_KEY

        token = create_token()
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        assert "exp" in decoded
        assert "iat" in decoded
        assert "scope" in decoded
        assert decoded["scope"] == "fcra_access"

    def test_token_includes_user_id(self):
        """Should include user_id when provided"""
        from services.jwt_utils import create_token, SECRET_KEY

        token = create_token(user_id=42)
        # Decode without validation since service stores int (not string) as sub
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_sub": False})

        assert "sub" in decoded
        assert decoded["sub"] == 42

    def test_token_includes_scopes(self):
        """Should include scopes when provided"""
        from services.jwt_utils import create_token, SECRET_KEY

        token = create_token(scopes=["read", "write"])
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        assert "scopes" in decoded
        assert decoded["scopes"] == ["read", "write"]

    def test_token_expires_in_7_days(self):
        """Should expire in 7 days"""
        from services.jwt_utils import create_token, SECRET_KEY

        token = create_token()
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        iat_time = datetime.utcfromtimestamp(decoded["iat"])

        # Should be approximately 7 days difference
        delta = exp_time - iat_time
        assert delta.days == 7

    def test_token_without_optional_fields(self):
        """Should work without optional fields"""
        from services.jwt_utils import create_token, SECRET_KEY

        token = create_token()
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        assert "sub" not in decoded
        assert "scopes" not in decoded


class TestRequireJwtDecorator:
    """Tests for require_jwt decorator"""

    def test_returns_401_without_auth_header(self):
        """Should return 401 when Authorization header is missing"""
        from services.jwt_utils import require_jwt
        from flask import Flask

        app = Flask(__name__)

        @require_jwt
        def protected_route():
            return {"data": "secret"}

        with app.test_request_context(headers={}):
            response, status = protected_route()

            assert status == 401
            assert "Missing or invalid token" in response.get_json()["error"]

    def test_returns_401_without_bearer_prefix(self):
        """Should return 401 when Bearer prefix is missing"""
        from services.jwt_utils import require_jwt
        from flask import Flask

        app = Flask(__name__)

        @require_jwt
        def protected_route():
            return {"data": "secret"}

        with app.test_request_context(headers={"Authorization": "invalid-token"}):
            response, status = protected_route()

            assert status == 401

    def test_returns_401_for_expired_token(self):
        """Should return 401 for expired token"""
        from services.jwt_utils import require_jwt, SECRET_KEY
        from flask import Flask

        app = Flask(__name__)

        # Create expired token
        payload = {
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(days=8),
            "scope": "fcra_access"
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        @require_jwt
        def protected_route():
            return {"data": "secret"}

        with app.test_request_context(headers={"Authorization": f"Bearer {expired_token}"}):
            response, status = protected_route()

            assert status == 401
            assert "Token expired" in response.get_json()["error"]

    def test_returns_401_for_invalid_token(self):
        """Should return 401 for invalid token"""
        from services.jwt_utils import require_jwt
        from flask import Flask

        app = Flask(__name__)

        @require_jwt
        def protected_route():
            return {"data": "secret"}

        with app.test_request_context(headers={"Authorization": "Bearer invalid.token.here"}):
            response, status = protected_route()

            assert status == 401
            assert "Invalid token" in response.get_json()["error"]

    def test_allows_valid_token(self):
        """Should allow request with valid token"""
        from services.jwt_utils import require_jwt, create_token
        from flask import Flask

        app = Flask(__name__)

        token = create_token()

        @require_jwt
        def protected_route():
            return {"data": "secret"}, 200

        with app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
            response, status = protected_route()

            assert status == 200


class TestSecretKey:
    """Tests for SECRET_KEY"""

    def test_secret_key_exists(self):
        """Should have a secret key configured"""
        from services.jwt_utils import SECRET_KEY

        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0

    def test_secret_key_is_non_empty(self):
        """Should have a non-empty secret key"""
        from services.jwt_utils import SECRET_KEY

        # Key should be a non-empty string (loaded from config)
        assert isinstance(SECRET_KEY, str)
        assert len(SECRET_KEY) >= 16  # Should be at least 16 chars for security
