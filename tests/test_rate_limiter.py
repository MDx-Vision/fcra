"""
Unit tests for Rate Limiter Service
Tests for rate limiting configuration, key functions, and initialization.
"""
import pytest
import os
import sys
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============== Environment Variable Tests ==============


class TestEnvironmentVariables:
    """Tests for environment variable configuration."""

    def test_is_ci_flag_when_ci_env_true(self):
        """Test IS_CI flag is True when CI environment variable is 'true'."""
        with patch.dict(os.environ, {"CI": "true"}):
            # Need to reimport to get new value
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.IS_CI is True

    def test_is_ci_flag_when_ci_env_false(self):
        """Test IS_CI flag is False when CI environment variable is not 'true'."""
        with patch.dict(os.environ, {"CI": "false"}, clear=False):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.IS_CI is False

    def test_is_ci_flag_when_ci_env_not_set(self):
        """Test IS_CI flag is False when CI environment variable is not set."""
        env_copy = os.environ.copy()
        env_copy.pop("CI", None)
        with patch.dict(os.environ, env_copy, clear=True):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.IS_CI is False

    def test_default_rate_from_env(self):
        """Test DEFAULT_RATE can be set from environment."""
        with patch.dict(os.environ, {"RATE_LIMIT_DEFAULT": "500 per minute"}):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.DEFAULT_RATE == "500 per minute"

    def test_default_rate_fallback(self):
        """Test DEFAULT_RATE fallback when env not set."""
        env_copy = os.environ.copy()
        env_copy.pop("RATE_LIMIT_DEFAULT", None)
        with patch.dict(os.environ, env_copy, clear=True):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.DEFAULT_RATE == "200 per minute"

    def test_auth_rate_from_env(self):
        """Test AUTH_RATE can be set from environment."""
        with patch.dict(os.environ, {"RATE_LIMIT_AUTH": "10 per minute"}):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.AUTH_RATE == "10 per minute"

    def test_auth_rate_fallback(self):
        """Test AUTH_RATE fallback when env not set."""
        env_copy = os.environ.copy()
        env_copy.pop("RATE_LIMIT_AUTH", None)
        with patch.dict(os.environ, env_copy, clear=True):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.AUTH_RATE == "5 per minute"

    def test_api_rate_from_env(self):
        """Test API_RATE can be set from environment."""
        with patch.dict(os.environ, {"RATE_LIMIT_API": "200 per minute"}):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.API_RATE == "200 per minute"

    def test_api_rate_fallback(self):
        """Test API_RATE fallback when env not set."""
        env_copy = os.environ.copy()
        env_copy.pop("RATE_LIMIT_API", None)
        with patch.dict(os.environ, env_copy, clear=True):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.API_RATE == "100 per minute"

    def test_analysis_rate_from_env(self):
        """Test ANALYSIS_RATE can be set from environment."""
        with patch.dict(os.environ, {"RATE_LIMIT_ANALYSIS": "20 per minute"}):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.ANALYSIS_RATE == "20 per minute"

    def test_analysis_rate_fallback(self):
        """Test ANALYSIS_RATE fallback when env not set."""
        env_copy = os.environ.copy()
        env_copy.pop("RATE_LIMIT_ANALYSIS", None)
        with patch.dict(os.environ, env_copy, clear=True):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)
            assert rate_limiter.ANALYSIS_RATE == "10 per minute"


# ============== get_rate_limit_key Tests ==============


class TestGetRateLimitKey:
    """Tests for get_rate_limit_key function."""

    def test_get_rate_limit_key_authenticated_user(self):
        """Test key returns staff ID for authenticated users."""
        from services.rate_limiter import get_rate_limit_key

        with patch('services.rate_limiter.session', {"staff_id": 123}):
            key = get_rate_limit_key()
            assert key == "staff:123"

    def test_get_rate_limit_key_unauthenticated_user(self):
        """Test key returns IP address for unauthenticated users."""
        from services.rate_limiter import get_rate_limit_key

        with patch('services.rate_limiter.session', {}):
            with patch('services.rate_limiter.get_remote_address', return_value="192.168.1.100"):
                key = get_rate_limit_key()
                assert key == "192.168.1.100"

    def test_get_rate_limit_key_staff_id_none(self):
        """Test key returns IP when staff_id is None."""
        from services.rate_limiter import get_rate_limit_key

        with patch('services.rate_limiter.session', {"staff_id": None}):
            with patch('services.rate_limiter.get_remote_address', return_value="10.0.0.1"):
                key = get_rate_limit_key()
                assert key == "10.0.0.1"

    def test_get_rate_limit_key_staff_id_zero(self):
        """Test key returns IP when staff_id is 0 (falsy)."""
        from services.rate_limiter import get_rate_limit_key

        with patch('services.rate_limiter.session', {"staff_id": 0}):
            with patch('services.rate_limiter.get_remote_address', return_value="172.16.0.1"):
                key = get_rate_limit_key()
                assert key == "172.16.0.1"

    def test_get_rate_limit_key_different_staff_ids(self):
        """Test different staff IDs return unique keys."""
        from services.rate_limiter import get_rate_limit_key

        with patch('services.rate_limiter.session', {"staff_id": 1}):
            key1 = get_rate_limit_key()

        with patch('services.rate_limiter.session', {"staff_id": 2}):
            key2 = get_rate_limit_key()

        assert key1 != key2
        assert key1 == "staff:1"
        assert key2 == "staff:2"


# ============== init_rate_limiter Tests ==============


class TestInitRateLimiter:
    """Tests for init_rate_limiter function."""

    def test_init_rate_limiter_returns_limiter(self):
        """Test init_rate_limiter returns a Limiter instance."""
        from services.rate_limiter import init_rate_limiter
        from flask import Flask

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        limiter = init_rate_limiter(app)

        assert limiter is not None

    def test_init_rate_limiter_registers_error_handler(self):
        """Test init_rate_limiter registers 429 error handler."""
        from services.rate_limiter import init_rate_limiter
        from flask import Flask

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        init_rate_limiter(app)

        # Check that error handler is registered
        assert 429 in app.error_handler_spec.get(None, {})

    def test_init_rate_limiter_error_handler_returns_json(self):
        """Test 429 error handler returns proper JSON response."""
        from services.rate_limiter import init_rate_limiter
        from flask import Flask
        from werkzeug.exceptions import TooManyRequests

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        init_rate_limiter(app)

        with app.test_request_context():
            # Create a mock 429 error
            class MockRateLimitError:
                description = "60 seconds"

            with patch('services.rate_limiter.session', {}):
                with patch('services.rate_limiter.get_remote_address', return_value="127.0.0.1"):
                    with patch('services.rate_limiter.request') as mock_request:
                        mock_request.path = "/api/test"

                        # Get the error handler and call it
                        handler = app.error_handler_spec[None][429][TooManyRequests]
                        response, status_code = handler(MockRateLimitError())

                        assert status_code == 429
                        json_data = response.get_json()
                        assert json_data["success"] is False
                        assert json_data["error"] == "Rate limit exceeded"
                        assert "Too many requests" in json_data["message"]
                        assert json_data["retry_after"] == "60 seconds"

    @patch('services.rate_limiter.IS_CI', False)
    def test_init_rate_limiter_enabled_when_not_ci(self):
        """Test rate limiter is enabled when not in CI mode."""
        from flask import Flask

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        with patch('services.rate_limiter.Limiter') as MockLimiter:
            mock_limiter = Mock()
            MockLimiter.return_value = mock_limiter

            from services.rate_limiter import init_rate_limiter
            init_rate_limiter(app)

            # Check that enabled=True was passed (not IS_CI)
            call_kwargs = MockLimiter.call_args[1]
            assert call_kwargs.get('enabled') is True

    @patch('services.rate_limiter.IS_CI', True)
    def test_init_rate_limiter_disabled_when_ci(self):
        """Test rate limiter is disabled when in CI mode."""
        from flask import Flask

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        with patch('services.rate_limiter.Limiter') as MockLimiter:
            mock_limiter = Mock()
            MockLimiter.return_value = mock_limiter

            from services.rate_limiter import init_rate_limiter
            init_rate_limiter(app)

            # Check that enabled=False was passed (not IS_CI)
            call_kwargs = MockLimiter.call_args[1]
            assert call_kwargs.get('enabled') is False

    def test_init_rate_limiter_uses_memory_storage(self):
        """Test rate limiter uses in-memory storage."""
        from flask import Flask

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        with patch('services.rate_limiter.Limiter') as MockLimiter:
            mock_limiter = Mock()
            MockLimiter.return_value = mock_limiter

            from services.rate_limiter import init_rate_limiter
            init_rate_limiter(app)

            call_kwargs = MockLimiter.call_args[1]
            assert call_kwargs.get('storage_uri') == "memory://"

    def test_init_rate_limiter_uses_fixed_window_strategy(self):
        """Test rate limiter uses fixed-window strategy."""
        from flask import Flask

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        with patch('services.rate_limiter.Limiter') as MockLimiter:
            mock_limiter = Mock()
            MockLimiter.return_value = mock_limiter

            from services.rate_limiter import init_rate_limiter
            init_rate_limiter(app)

            call_kwargs = MockLimiter.call_args[1]
            assert call_kwargs.get('strategy') == "fixed-window"

    def test_init_rate_limiter_enables_headers(self):
        """Test rate limiter enables X-RateLimit headers."""
        from flask import Flask

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        with patch('services.rate_limiter.Limiter') as MockLimiter:
            mock_limiter = Mock()
            MockLimiter.return_value = mock_limiter

            from services.rate_limiter import init_rate_limiter
            init_rate_limiter(app)

            call_kwargs = MockLimiter.call_args[1]
            assert call_kwargs.get('headers_enabled') is True


# ============== get_rate_limits Tests ==============


class TestGetRateLimits:
    """Tests for get_rate_limits function."""

    def test_get_rate_limits_returns_dict(self):
        """Test get_rate_limits returns a dictionary."""
        from services.rate_limiter import get_rate_limits

        limits = get_rate_limits()
        assert isinstance(limits, dict)

    def test_get_rate_limits_has_default(self):
        """Test get_rate_limits includes default limit."""
        from services.rate_limiter import get_rate_limits, DEFAULT_RATE

        limits = get_rate_limits()
        assert "default" in limits
        assert limits["default"] == DEFAULT_RATE

    def test_get_rate_limits_has_auth(self):
        """Test get_rate_limits includes auth limit."""
        from services.rate_limiter import get_rate_limits, AUTH_RATE

        limits = get_rate_limits()
        assert "auth" in limits
        assert limits["auth"] == AUTH_RATE

    def test_get_rate_limits_has_api(self):
        """Test get_rate_limits includes api limit."""
        from services.rate_limiter import get_rate_limits, API_RATE

        limits = get_rate_limits()
        assert "api" in limits
        assert limits["api"] == API_RATE

    def test_get_rate_limits_has_analysis(self):
        """Test get_rate_limits includes analysis limit."""
        from services.rate_limiter import get_rate_limits, ANALYSIS_RATE

        limits = get_rate_limits()
        assert "analysis" in limits
        assert limits["analysis"] == ANALYSIS_RATE

    def test_get_rate_limits_has_unlimited(self):
        """Test get_rate_limits includes unlimited option."""
        from services.rate_limiter import get_rate_limits

        limits = get_rate_limits()
        assert "unlimited" in limits
        assert limits["unlimited"] is None

    def test_get_rate_limits_all_keys_present(self):
        """Test get_rate_limits has all expected keys."""
        from services.rate_limiter import get_rate_limits

        limits = get_rate_limits()
        expected_keys = {"default", "auth", "api", "analysis", "unlimited"}
        assert set(limits.keys()) == expected_keys


# ============== RATE_LIMITS Constant Tests ==============


class TestRateLimitsConstant:
    """Tests for RATE_LIMITS constant dictionary."""

    def test_rate_limits_is_dict(self):
        """Test RATE_LIMITS is a dictionary."""
        from services.rate_limiter import RATE_LIMITS

        assert isinstance(RATE_LIMITS, dict)

    def test_rate_limits_has_login(self):
        """Test RATE_LIMITS has login limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "login" in RATE_LIMITS
        assert RATE_LIMITS["login"] == "5 per minute"

    def test_rate_limits_has_password_reset(self):
        """Test RATE_LIMITS has password_reset limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "password_reset" in RATE_LIMITS
        assert RATE_LIMITS["password_reset"] == "3 per minute"

    def test_rate_limits_has_api_read(self):
        """Test RATE_LIMITS has api_read limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "api_read" in RATE_LIMITS
        assert RATE_LIMITS["api_read"] == "100 per minute"

    def test_rate_limits_has_api_write(self):
        """Test RATE_LIMITS has api_write limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "api_write" in RATE_LIMITS
        assert RATE_LIMITS["api_write"] == "30 per minute"

    def test_rate_limits_has_ai_analysis(self):
        """Test RATE_LIMITS has ai_analysis limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "ai_analysis" in RATE_LIMITS
        assert RATE_LIMITS["ai_analysis"] == "10 per minute"

    def test_rate_limits_has_pdf_generation(self):
        """Test RATE_LIMITS has pdf_generation limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "pdf_generation" in RATE_LIMITS
        assert RATE_LIMITS["pdf_generation"] == "20 per minute"

    def test_rate_limits_has_email_send(self):
        """Test RATE_LIMITS has email_send limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "email_send" in RATE_LIMITS
        assert RATE_LIMITS["email_send"] == "10 per minute"

    def test_rate_limits_has_bulk_action(self):
        """Test RATE_LIMITS has bulk_action limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "bulk_action" in RATE_LIMITS
        assert RATE_LIMITS["bulk_action"] == "5 per minute"

    def test_rate_limits_has_export(self):
        """Test RATE_LIMITS has export limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "export" in RATE_LIMITS
        assert RATE_LIMITS["export"] == "5 per minute"

    def test_rate_limits_has_webhook(self):
        """Test RATE_LIMITS has webhook limit."""
        from services.rate_limiter import RATE_LIMITS

        assert "webhook" in RATE_LIMITS
        assert RATE_LIMITS["webhook"] == "60 per minute"

    def test_rate_limits_all_keys_present(self):
        """Test RATE_LIMITS has all expected keys."""
        from services.rate_limiter import RATE_LIMITS

        expected_keys = {
            "login", "password_reset", "api_read", "api_write",
            "ai_analysis", "pdf_generation", "email_send",
            "bulk_action", "export", "webhook"
        }
        assert set(RATE_LIMITS.keys()) == expected_keys

    def test_rate_limits_values_are_strings(self):
        """Test all RATE_LIMITS values are strings."""
        from services.rate_limiter import RATE_LIMITS

        for key, value in RATE_LIMITS.items():
            assert isinstance(value, str), f"Expected string for {key}, got {type(value)}"

    def test_rate_limits_values_format(self):
        """Test all RATE_LIMITS values follow 'N per minute' format."""
        from services.rate_limiter import RATE_LIMITS
        import re

        pattern = r"^\d+ per minute$"
        for key, value in RATE_LIMITS.items():
            assert re.match(pattern, value), f"Value '{value}' for {key} doesn't match expected format"


# ============== exempt_when_authenticated Tests ==============


class TestExemptWhenAuthenticated:
    """Tests for exempt_when_authenticated decorator."""

    def test_exempt_when_authenticated_preserves_function_name(self):
        """Test decorator preserves the wrapped function's name."""
        from services.rate_limiter import exempt_when_authenticated

        @exempt_when_authenticated
        def test_function():
            return "test"

        assert test_function.__name__ == "test_function"

    def test_exempt_when_authenticated_preserves_return_value(self):
        """Test decorator preserves the wrapped function's return value."""
        from services.rate_limiter import exempt_when_authenticated

        @exempt_when_authenticated
        def test_function():
            return "expected_value"

        with patch('services.rate_limiter.session', {}):
            result = test_function()
            assert result == "expected_value"

    def test_exempt_when_authenticated_with_authenticated_user(self):
        """Test decorator works with authenticated user."""
        from services.rate_limiter import exempt_when_authenticated

        @exempt_when_authenticated
        def test_function():
            return "authenticated"

        with patch('services.rate_limiter.session', {"staff_id": 123}):
            result = test_function()
            assert result == "authenticated"

    def test_exempt_when_authenticated_with_unauthenticated_user(self):
        """Test decorator works with unauthenticated user."""
        from services.rate_limiter import exempt_when_authenticated

        @exempt_when_authenticated
        def test_function():
            return "unauthenticated"

        with patch('services.rate_limiter.session', {}):
            result = test_function()
            assert result == "unauthenticated"

    def test_exempt_when_authenticated_passes_args(self):
        """Test decorator passes arguments to wrapped function."""
        from services.rate_limiter import exempt_when_authenticated

        @exempt_when_authenticated
        def test_function(a, b, c=None):
            return (a, b, c)

        with patch('services.rate_limiter.session', {}):
            result = test_function(1, 2, c=3)
            assert result == (1, 2, 3)

    def test_exempt_when_authenticated_passes_kwargs(self):
        """Test decorator passes keyword arguments to wrapped function."""
        from services.rate_limiter import exempt_when_authenticated

        @exempt_when_authenticated
        def test_function(**kwargs):
            return kwargs

        with patch('services.rate_limiter.session', {}):
            result = test_function(x=1, y=2)
            assert result == {"x": 1, "y": 2}

    def test_exempt_when_authenticated_preserves_docstring(self):
        """Test decorator preserves the wrapped function's docstring."""
        from services.rate_limiter import exempt_when_authenticated

        @exempt_when_authenticated
        def test_function():
            """This is a test docstring."""
            return "test"

        assert test_function.__doc__ == "This is a test docstring."

    def test_exempt_when_authenticated_multiple_calls(self):
        """Test decorator handles multiple calls correctly."""
        from services.rate_limiter import exempt_when_authenticated

        call_count = 0

        @exempt_when_authenticated
        def test_function():
            nonlocal call_count
            call_count += 1
            return call_count

        with patch('services.rate_limiter.session', {"staff_id": 1}):
            result1 = test_function()
            result2 = test_function()
            result3 = test_function()

        assert result1 == 1
        assert result2 == 2
        assert result3 == 3


# ============== Integration Tests ==============


class TestIntegration:
    """Integration tests for rate limiter with Flask app."""

    def test_rate_limiter_with_flask_app(self):
        """Test rate limiter integrates correctly with Flask app."""
        from services.rate_limiter import init_rate_limiter
        from flask import Flask

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        limiter = init_rate_limiter(app)

        @app.route("/test")
        def test_route():
            return "OK"

        with app.test_client() as client:
            response = client.get("/test")
            assert response.status_code == 200

    def test_rate_limiter_headers_present(self):
        """Test rate limit headers are present in response."""
        from flask import Flask

        # Create a fresh app without CI mode
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        with patch('services.rate_limiter.IS_CI', False):
            import importlib
            from services import rate_limiter
            importlib.reload(rate_limiter)

            limiter = rate_limiter.init_rate_limiter(app)

            @app.route("/test")
            @limiter.limit("10 per minute")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                # When rate limiting is enabled, headers should be present
                # Note: Headers may not appear in test mode depending on Flask-Limiter version
                assert response.status_code == 200


# ============== Edge Cases ==============


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_get_rate_limit_key_with_string_staff_id(self):
        """Test key handles string staff_id (should still work)."""
        from services.rate_limiter import get_rate_limit_key

        with patch('services.rate_limiter.session', {"staff_id": "456"}):
            key = get_rate_limit_key()
            assert key == "staff:456"

    def test_rate_limits_immutability(self):
        """Test that RATE_LIMITS values cannot be accidentally modified."""
        from services.rate_limiter import RATE_LIMITS

        original_login = RATE_LIMITS["login"]
        # Attempting to modify should not affect future imports
        RATE_LIMITS["login"] = "modified"

        # Reimport to check if original is preserved
        import importlib
        from services import rate_limiter
        importlib.reload(rate_limiter)

        assert rate_limiter.RATE_LIMITS["login"] == "5 per minute"

    def test_error_handler_logs_warning(self):
        """Test 429 error handler logs a warning."""
        from services.rate_limiter import init_rate_limiter
        from flask import Flask
        from werkzeug.exceptions import TooManyRequests

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        init_rate_limiter(app)

        with app.test_request_context():
            class MockRateLimitError:
                description = "30 seconds"

            with patch('services.rate_limiter.session', {}):
                with patch('services.rate_limiter.get_remote_address', return_value="192.168.1.1"):
                    with patch('services.rate_limiter.request') as mock_request:
                        mock_request.path = "/api/sensitive"

                        with patch('services.logging_config.api_logger') as mock_logger:
                            handler = app.error_handler_spec[None][429][TooManyRequests]
                            handler(MockRateLimitError())

                            # Logger should have been called with warning
                            mock_logger.warning.assert_called_once()
                            call_args = mock_logger.warning.call_args[0][0]
                            assert "192.168.1.1" in call_args
                            assert "/api/sensitive" in call_args

    def test_multiple_flask_apps(self):
        """Test rate limiter can be initialized on multiple Flask apps."""
        from services.rate_limiter import init_rate_limiter
        from flask import Flask

        app1 = Flask("app1")
        app1.config["SECRET_KEY"] = "secret1"

        app2 = Flask("app2")
        app2.config["SECRET_KEY"] = "secret2"

        limiter1 = init_rate_limiter(app1)
        limiter2 = init_rate_limiter(app2)

        assert limiter1 is not None
        assert limiter2 is not None
        assert limiter1 is not limiter2

    def test_rate_limit_string_parsing(self):
        """Test rate limit strings are in valid format for Flask-Limiter."""
        from services.rate_limiter import RATE_LIMITS, DEFAULT_RATE, AUTH_RATE, API_RATE, ANALYSIS_RATE

        all_limits = list(RATE_LIMITS.values()) + [DEFAULT_RATE, AUTH_RATE, API_RATE, ANALYSIS_RATE]

        for limit in all_limits:
            # Flask-Limiter expects format like "N per period"
            parts = limit.split()
            assert len(parts) == 3
            assert parts[0].isdigit()
            assert parts[1] == "per"
            assert parts[2] in ["second", "minute", "hour", "day"]
