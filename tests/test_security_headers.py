"""
Unit tests for Security Headers Service
Tests for HTTPS enforcement, security headers middleware, and require_https decorator.
"""
import pytest
import os
import sys
from unittest.mock import Mock, MagicMock, patch
from flask import Flask

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.security_headers import (
    init_security_headers,
    require_https,
    SECURITY_HEADERS,
)


# ============== Helper Functions ==============


def create_test_app():
    """Create a fresh Flask app for testing."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    return app


# ============== SECURITY_HEADERS Constant Tests ==============


class TestSecurityHeadersConstant:
    """Tests for SECURITY_HEADERS dictionary constant."""

    def test_security_headers_is_dict(self):
        """Test SECURITY_HEADERS is a dictionary."""
        assert isinstance(SECURITY_HEADERS, dict)

    def test_security_headers_has_hsts(self):
        """Test SECURITY_HEADERS contains Strict-Transport-Security."""
        assert "Strict-Transport-Security" in SECURITY_HEADERS

    def test_security_headers_has_x_frame_options(self):
        """Test SECURITY_HEADERS contains X-Frame-Options."""
        assert "X-Frame-Options" in SECURITY_HEADERS

    def test_security_headers_has_x_content_type_options(self):
        """Test SECURITY_HEADERS contains X-Content-Type-Options."""
        assert "X-Content-Type-Options" in SECURITY_HEADERS

    def test_security_headers_has_x_xss_protection(self):
        """Test SECURITY_HEADERS contains X-XSS-Protection."""
        assert "X-XSS-Protection" in SECURITY_HEADERS

    def test_security_headers_has_csp(self):
        """Test SECURITY_HEADERS contains Content-Security-Policy."""
        assert "Content-Security-Policy" in SECURITY_HEADERS

    def test_security_headers_has_referrer_policy(self):
        """Test SECURITY_HEADERS contains Referrer-Policy."""
        assert "Referrer-Policy" in SECURITY_HEADERS

    def test_security_headers_has_permissions_policy(self):
        """Test SECURITY_HEADERS contains Permissions-Policy."""
        assert "Permissions-Policy" in SECURITY_HEADERS

    def test_security_headers_all_values_are_strings(self):
        """Test all SECURITY_HEADERS values are strings (descriptions)."""
        for key, value in SECURITY_HEADERS.items():
            assert isinstance(value, str), f"Expected string description for {key}"

    def test_security_headers_count(self):
        """Test SECURITY_HEADERS has expected number of entries."""
        assert len(SECURITY_HEADERS) == 7


# ============== init_security_headers Tests ==============


class TestInitSecurityHeaders:
    """Tests for init_security_headers function."""

    def test_init_security_headers_configures_session_cookies(self):
        """Test init_security_headers configures secure session cookies."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            assert app.config["SESSION_COOKIE_HTTPONLY"] is True
            assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"

    def test_init_security_headers_secure_cookie_when_https(self):
        """Test SESSION_COOKIE_SECURE is True when force_https is True."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=True)

            assert app.config["SESSION_COOKIE_SECURE"] is True

    def test_init_security_headers_secure_cookie_in_production(self):
        """Test SESSION_COOKIE_SECURE is True in production."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app)

            assert app.config["SESSION_COOKIE_SECURE"] is True

    def test_init_security_headers_not_secure_in_development(self):
        """Test SESSION_COOKIE_SECURE is False in development without force_https."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            assert app.config["SESSION_COOKIE_SECURE"] is False

    def test_init_security_headers_default_hsts_max_age(self):
        """Test default HSTS max-age is one year (31536000 seconds)."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app)

            # Make a request and check the header
            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                hsts = response.headers.get("Strict-Transport-Security")
                assert hsts is not None
                assert "max-age=31536000" in hsts

    def test_init_security_headers_custom_hsts_max_age(self):
        """Test custom HSTS max-age can be set."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, hsts_max_age=86400)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                hsts = response.headers.get("Strict-Transport-Security")
                assert hsts is not None
                assert "max-age=86400" in hsts


# ============== HTTPS Enforcement Tests ==============


class TestHttpsEnforcement:
    """Tests for HTTPS redirect enforcement."""

    def test_no_redirect_when_force_https_false(self):
        """Test no redirect when force_https is False."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                assert response.status_code == 200

    def test_no_redirect_for_localhost(self):
        """Test no HTTPS redirect for localhost requests."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, force_https=True)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                # localhost should not be redirected
                response = client.get("/test", headers={"Host": "localhost:5000"})
                assert response.status_code == 200

    def test_no_redirect_for_root_path(self):
        """Test no HTTPS redirect for root path (health check)."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, force_https=True)

            @app.route("/")
            def root_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/")
                assert response.status_code == 200

    def test_no_redirect_when_already_https(self):
        """Test no redirect when request is already HTTPS (via X-Forwarded-Proto)."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, force_https=True)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get(
                    "/test",
                    headers={"X-Forwarded-Proto": "https", "Host": "example.com"},
                )
                assert response.status_code == 200

    def test_no_redirect_when_x_forwarded_ssl_on(self):
        """Test no redirect when X-Forwarded-Ssl is 'on'."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, force_https=True)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get(
                    "/test",
                    headers={"X-Forwarded-Ssl": "on", "Host": "example.com"},
                )
                assert response.status_code == 200

    def test_redirect_http_to_https(self):
        """Test HTTP requests are redirected to HTTPS."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, force_https=True)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test", headers={"Host": "example.com"})
                assert response.status_code == 301
                assert "https://" in response.location

    def test_force_https_none_uses_config(self):
        """Test force_https=None uses config values."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, force_https=None)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test", headers={"Host": "example.com"})
                # Should redirect since IS_PRODUCTION=True and IS_CI=False
                assert response.status_code == 301

    def test_force_https_disabled_in_ci(self):
        """Test force_https is disabled in CI environment."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = True

            init_security_headers(app, force_https=None)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test", headers={"Host": "example.com"})
                # Should not redirect since IS_CI=True
                assert response.status_code == 200


# ============== Security Headers in Response Tests ==============


class TestSecurityHeadersInResponse:
    """Tests for security headers added to responses."""

    def test_x_frame_options_header(self):
        """Test X-Frame-Options header is set to SAMEORIGIN."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"

    def test_x_content_type_options_header(self):
        """Test X-Content-Type-Options header is set to nosniff."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_xss_protection_header(self):
        """Test X-XSS-Protection header is set correctly."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy_header(self):
        """Test Referrer-Policy header is set correctly."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                assert (
                    response.headers.get("Referrer-Policy")
                    == "strict-origin-when-cross-origin"
                )

    def test_permissions_policy_header(self):
        """Test Permissions-Policy header is set correctly."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                permissions_policy = response.headers.get("Permissions-Policy")
                assert permissions_policy is not None
                assert "geolocation=()" in permissions_policy
                assert "microphone=()" in permissions_policy
                assert "camera=()" in permissions_policy
                assert "payment=()" in permissions_policy
                assert "usb=()" in permissions_policy

    def test_hsts_header_in_production(self):
        """Test HSTS header is added in production."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                hsts = response.headers.get("Strict-Transport-Security")
                assert hsts is not None
                assert "max-age=" in hsts
                assert "includeSubDomains" in hsts
                assert "preload" in hsts

    def test_hsts_header_when_force_https(self):
        """Test HSTS header is added when force_https is True."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=True)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                # Request with HTTPS headers to avoid redirect
                response = client.get(
                    "/test", headers={"X-Forwarded-Proto": "https"}
                )
                hsts = response.headers.get("Strict-Transport-Security")
                assert hsts is not None

    def test_no_hsts_header_in_development(self):
        """Test no HSTS header in development without force_https."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                hsts = response.headers.get("Strict-Transport-Security")
                assert hsts is None


# ============== Content-Security-Policy Tests ==============


class TestContentSecurityPolicy:
    """Tests for Content-Security-Policy header."""

    def test_csp_header_present(self):
        """Test CSP header is present on non-static routes."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert csp is not None

    def test_csp_default_src(self):
        """Test CSP has default-src 'self' directive."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "default-src 'self'" in csp

    def test_csp_script_src(self):
        """Test CSP has script-src directive with CDN allowlist."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "script-src" in csp
                assert "https://cdn.jsdelivr.net" in csp
                assert "https://cdnjs.cloudflare.com" in csp

    def test_csp_style_src(self):
        """Test CSP has style-src directive with CDN and fonts allowlist."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "style-src" in csp
                assert "https://fonts.googleapis.com" in csp

    def test_csp_font_src(self):
        """Test CSP has font-src directive with Google Fonts allowlist."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "font-src" in csp
                assert "https://fonts.gstatic.com" in csp

    def test_csp_img_src(self):
        """Test CSP has img-src directive allowing data URLs and https."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "img-src" in csp
                assert "data:" in csp
                assert "blob:" in csp

    def test_csp_connect_src(self):
        """Test CSP has connect-src directive with Anthropic API allowlist."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "connect-src" in csp
                assert "https://api.anthropic.com" in csp

    def test_csp_frame_ancestors(self):
        """Test CSP has frame-ancestors 'self' directive."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "frame-ancestors 'self'" in csp

    def test_csp_form_action(self):
        """Test CSP has form-action 'self' directive."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "form-action 'self'" in csp

    def test_csp_base_uri(self):
        """Test CSP has base-uri 'self' directive."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "base-uri 'self'" in csp

    def test_csp_object_src_none(self):
        """Test CSP has object-src 'none' directive."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                csp = response.headers.get("Content-Security-Policy")
                assert "object-src 'none'" in csp

    def test_no_csp_on_static_routes(self):
        """Test CSP header is not added on static routes."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/static/test.js")
            def static_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/static/test.js")
                csp = response.headers.get("Content-Security-Policy")
                assert csp is None


# ============== Cache-Control Tests ==============


class TestCacheControl:
    """Tests for Cache-Control headers on sensitive pages."""

    def test_cache_control_on_api_routes(self):
        """Test Cache-Control header is set on API routes."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/api/test")
            def api_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/api/test")
                cache_control = response.headers.get("Cache-Control")
                assert cache_control is not None
                assert "no-store" in cache_control
                assert "no-cache" in cache_control
                assert "must-revalidate" in cache_control
                assert "private" in cache_control

    def test_pragma_no_cache_on_api_routes(self):
        """Test Pragma header is set to no-cache on API routes."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/api/test")
            def api_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/api/test")
                pragma = response.headers.get("Pragma")
                assert pragma == "no-cache"

    def test_cache_control_on_dashboard_routes(self):
        """Test Cache-Control header is set on dashboard routes."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/dashboard/test")
            def dashboard_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/dashboard/test")
                cache_control = response.headers.get("Cache-Control")
                assert cache_control is not None
                assert "no-store" in cache_control

    def test_no_cache_control_on_regular_routes(self):
        """Test no special Cache-Control header on regular routes."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/public/test")
            def public_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/public/test")
                pragma = response.headers.get("Pragma")
                # Pragma should not be set on non-API/non-dashboard routes
                assert pragma is None


# ============== require_https Decorator Tests ==============


class TestRequireHttpsDecorator:
    """Tests for require_https decorator."""

    def test_require_https_preserves_function_name(self):
        """Test decorator preserves the wrapped function's name."""

        @require_https
        def test_function():
            return "test"

        assert test_function.__name__ == "test_function"

    def test_require_https_preserves_docstring(self):
        """Test decorator preserves the wrapped function's docstring."""

        @require_https
        def test_function():
            """This is a test docstring."""
            return "test"

        assert test_function.__doc__ == "This is a test docstring."

    def test_require_https_allows_https_in_production(self):
        """Test require_https allows HTTPS requests in production."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True

            @app.route("/secure")
            @require_https
            def secure_route():
                return {"success": True}

            with app.test_client() as client:
                response = client.get(
                    "/secure", headers={"X-Forwarded-Proto": "https"}
                )
                assert response.status_code == 200

    def test_require_https_blocks_http_in_production(self):
        """Test require_https blocks HTTP requests in production."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True

            @app.route("/secure")
            @require_https
            def secure_route():
                return {"success": True}

            with app.test_client() as client:
                response = client.get("/secure")
                assert response.status_code == 403
                data = response.get_json()
                assert data["success"] is False
                assert "HTTPS required" in data["error"]

    def test_require_https_allows_http_in_development(self):
        """Test require_https allows HTTP requests in development."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False

            @app.route("/secure")
            @require_https
            def secure_route():
                return {"success": True}

            with app.test_client() as client:
                response = client.get("/secure")
                assert response.status_code == 200

    def test_require_https_with_request_is_secure(self):
        """Test require_https recognizes secure requests via request.is_secure."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True

            @app.route("/secure")
            @require_https
            def secure_route():
                return {"success": True}

            # This is tricky to test since request.is_secure depends on WSGI env
            # We'll test via X-Forwarded-Proto instead
            with app.test_client() as client:
                response = client.get(
                    "/secure", headers={"X-Forwarded-Proto": "https"}
                )
                assert response.status_code == 200

    def test_require_https_passes_args(self):
        """Test decorator passes arguments to wrapped function."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False

            @app.route("/secure/<item_id>")
            @require_https
            def secure_route(item_id):
                return {"item_id": item_id}

            with app.test_client() as client:
                response = client.get("/secure/123")
                assert response.status_code == 200
                data = response.get_json()
                assert data["item_id"] == "123"

    def test_require_https_passes_kwargs(self):
        """Test decorator passes keyword arguments to wrapped function."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False

            @app.route("/secure")
            @require_https
            def secure_route():
                from flask import request

                param = request.args.get("param", "default")
                return {"param": param}

            with app.test_client() as client:
                response = client.get("/secure?param=custom")
                assert response.status_code == 200
                data = response.get_json()
                assert data["param"] == "custom"


# ============== Integration Tests ==============


class TestIntegration:
    """Integration tests for security headers middleware."""

    def test_all_security_headers_present(self):
        """Test all security headers are present in response."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")

                assert response.headers.get("X-Frame-Options") is not None
                assert response.headers.get("X-Content-Type-Options") is not None
                assert response.headers.get("X-XSS-Protection") is not None
                assert response.headers.get("Referrer-Policy") is not None
                assert response.headers.get("Permissions-Policy") is not None
                assert response.headers.get("Strict-Transport-Security") is not None
                assert response.headers.get("Content-Security-Policy") is not None

    def test_headers_on_error_responses(self):
        """Test security headers are added to error responses."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/error")
            def error_route():
                from flask import abort

                abort(404)

            with app.test_client() as client:
                response = client.get("/error")
                assert response.status_code == 404
                # Basic security headers should still be present
                assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
                assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_headers_on_json_responses(self):
        """Test security headers are added to JSON responses."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/json")
            def json_route():
                from flask import jsonify

                return jsonify({"data": "test"})

            with app.test_client() as client:
                response = client.get("/json")
                assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
                assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_headers_on_post_requests(self):
        """Test security headers are added to POST requests."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/post", methods=["POST"])
            def post_route():
                return "OK"

            with app.test_client() as client:
                response = client.post("/post")
                assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
                assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_multiple_apps(self):
        """Test security headers can be initialized on multiple apps."""
        app1 = create_test_app()
        app2 = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app1, force_https=False)
            init_security_headers(app2, force_https=False)

            @app1.route("/test")
            def test_route1():
                return "App1"

            @app2.route("/test")
            def test_route2():
                return "App2"

            with app1.test_client() as client1:
                response1 = client1.get("/test")
                assert response1.headers.get("X-Frame-Options") == "SAMEORIGIN"

            with app2.test_client() as client2:
                response2 = client2.get("/test")
                assert response2.headers.get("X-Frame-Options") == "SAMEORIGIN"


# ============== Edge Cases ==============


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_hsts_max_age_zero(self):
        """Test HSTS with max-age of zero."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, hsts_max_age=0)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                response = client.get("/test")
                hsts = response.headers.get("Strict-Transport-Security")
                assert hsts is not None
                assert "max-age=0" in hsts

    def test_empty_path(self):
        """Test handling of empty/root path."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/")
            def root():
                return "OK"

            with app.test_client() as client:
                response = client.get("/")
                assert response.status_code == 200
                assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"

    def test_deeply_nested_api_path(self):
        """Test Cache-Control on deeply nested API paths."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/api/v1/users/123/reports/456")
            def nested_api():
                return "OK"

            with app.test_client() as client:
                response = client.get("/api/v1/users/123/reports/456")
                cache_control = response.headers.get("Cache-Control")
                assert "no-store" in cache_control

    def test_path_case_sensitivity_for_static(self):
        """Test static path detection is case-sensitive."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/Static/test.js")
            def static_uppercase():
                return "OK"

            with app.test_client() as client:
                response = client.get("/Static/test.js")
                # /Static/ (uppercase) should have CSP since it doesn't match /static/
                csp = response.headers.get("Content-Security-Policy")
                assert csp is not None

    def test_api_vs_api_prefix(self):
        """Test /api/ path vs /api-docs/ path for Cache-Control."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/api-docs/")
            def api_docs():
                return "OK"

            with app.test_client() as client:
                response = client.get("/api-docs/")
                # /api-docs/ should NOT have no-cache since it doesn't start with /api/
                pragma = response.headers.get("Pragma")
                assert pragma is None

    def test_unicode_path(self):
        """Test handling of unicode characters in path."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = False
            mock_config.IS_CI = False

            init_security_headers(app, force_https=False)

            @app.route("/test/<name>")
            def unicode_route(name):
                return f"Hello {name}"

            with app.test_client() as client:
                response = client.get("/test/caf%C3%A9")  # /test/cafe with accent
                assert response.status_code == 200
                assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"

    def test_special_characters_in_host(self):
        """Test handling of special characters in host header."""
        app = create_test_app()

        with patch("services.security_headers.config") as mock_config:
            mock_config.IS_PRODUCTION = True
            mock_config.IS_CI = False

            init_security_headers(app, force_https=True)

            @app.route("/test")
            def test_route():
                return "OK"

            with app.test_client() as client:
                # Test with various host headers
                response = client.get(
                    "/test",
                    headers={"Host": "localhost.localdomain", "X-Forwarded-Proto": "https"},
                )
                # localhost.localdomain starts with localhost, so no redirect
                assert response.status_code == 200
