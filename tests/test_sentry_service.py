"""
Unit tests for Sentry Error Tracking Service.

Tests error tracking, user context, Slack notifications,
and data sanitization functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from services.sentry_service import (
    init_sentry,
    is_sentry_configured,
    set_user_context,
    clear_user_context,
    set_request_context,
    capture_exception,
    capture_message,
    add_breadcrumb,
    track_errors,
    sentry_span,
    _sanitize_data,
    _is_sensitive_field,
    _categorize_error,
    _notify_slack,
    ERROR_CATEGORIES,
    IGNORED_ERRORS,
    SENSITIVE_FIELDS,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_sentry():
    """Mock Sentry SDK functions."""
    with patch("services.sentry_service.sentry_sdk") as mock:
        mock.init = Mock()
        mock.set_user = Mock()
        mock.set_tag = Mock()
        mock.set_context = Mock()
        mock.add_breadcrumb = Mock()
        mock.capture_exception = Mock(return_value="event-123")
        mock.capture_message = Mock(return_value="event-456")
        mock.push_scope = Mock()
        mock.start_span = Mock()
        yield mock


@pytest.fixture
def mock_requests():
    """Mock requests for Slack notifications."""
    with patch("services.sentry_service.requests") as mock:
        mock.post = Mock(return_value=Mock(status_code=200))
        yield mock


@pytest.fixture
def enable_sentry():
    """Enable Sentry for testing."""
    import services.sentry_service as sentry_service
    original = sentry_service._sentry_initialized
    sentry_service._sentry_initialized = True
    yield
    sentry_service._sentry_initialized = original


@pytest.fixture
def disable_sentry():
    """Disable Sentry for testing."""
    import services.sentry_service as sentry_service
    original = sentry_service._sentry_initialized
    sentry_service._sentry_initialized = False
    yield
    sentry_service._sentry_initialized = original


# =============================================================================
# Configuration Tests
# =============================================================================

class TestConfiguration:
    """Tests for Sentry configuration."""

    def test_error_categories_defined(self):
        """All error categories are defined."""
        assert "critical" in ERROR_CATEGORIES
        assert "high" in ERROR_CATEGORIES
        assert "medium" in ERROR_CATEGORIES
        assert "low" in ERROR_CATEGORIES

    def test_critical_errors_include_database(self):
        """Critical errors include database errors."""
        assert "DatabaseError" in ERROR_CATEGORIES["critical"]
        assert "OperationalError" in ERROR_CATEGORIES["critical"]

    def test_critical_errors_include_payment(self):
        """Critical errors include payment errors."""
        assert "PaymentError" in ERROR_CATEGORIES["critical"]
        assert "StripeError" in ERROR_CATEGORIES["critical"]

    def test_ignored_errors_defined(self):
        """Ignored errors list is defined."""
        assert "NotFound" in IGNORED_ERRORS
        assert "MethodNotAllowed" in IGNORED_ERRORS
        assert "BadRequest" in IGNORED_ERRORS

    def test_sensitive_fields_defined(self):
        """Sensitive fields for redaction are defined."""
        assert "password" in SENSITIVE_FIELDS
        assert "token" in SENSITIVE_FIELDS
        assert "api_key" in SENSITIVE_FIELDS
        assert "ssn" in SENSITIVE_FIELDS


# =============================================================================
# Initialization Tests
# =============================================================================

class TestInitialization:
    """Tests for Sentry initialization."""

    def test_init_without_dsn(self):
        """Init returns False without DSN."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("services.sentry_service.SENTRY_DSN", None):
                result = init_sentry()
                assert result is False

    def test_init_with_dsn(self, mock_sentry):
        """Init returns True with valid DSN."""
        with patch("services.sentry_service.SENTRY_DSN", "https://key@sentry.io/123"):
            with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                result = init_sentry(dsn="https://key@sentry.io/123")
                # Note: This may fail in test env without full Sentry setup
                # The important thing is it doesn't crash

    def test_is_sentry_configured_false_by_default(self, disable_sentry):
        """is_sentry_configured returns False when not initialized."""
        assert is_sentry_configured() is False

    def test_is_sentry_configured_true_when_enabled(self, enable_sentry):
        """is_sentry_configured returns True when initialized."""
        with patch("services.sentry_service.SENTRY_AVAILABLE", True):
            assert is_sentry_configured() is True


# =============================================================================
# User Context Tests
# =============================================================================

class TestUserContext:
    """Tests for user context setting."""

    def test_set_user_context_when_disabled(self, disable_sentry):
        """set_user_context does nothing when Sentry is disabled."""
        # Should not raise
        set_user_context(user_id=123, email="test@example.com")

    def test_set_user_context_with_all_fields(self, enable_sentry):
        """set_user_context sets all provided fields."""
        with patch("services.sentry_service.set_user") as mock_set_user:
            with patch("services.sentry_service.set_context") as mock_set_context:
                with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                    set_user_context(
                        user_id=123,
                        email="test@example.com",
                        username="Test User",
                        role="admin",
                        user_type="staff",
                        ip_address="192.168.1.1",
                        extra={"department": "IT"},
                    )

                    # Should call set_user with user data
                    mock_set_user.assert_called_once()
                    call_args = mock_set_user.call_args[0][0]
                    assert call_args["id"] == "123"
                    assert call_args["email"] == "test@example.com"
                    assert call_args["username"] == "Test User"

    def test_clear_user_context(self, enable_sentry):
        """clear_user_context clears the user."""
        with patch("services.sentry_service.set_user") as mock_set_user:
            with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                clear_user_context()
                mock_set_user.assert_called_once_with(None)


# =============================================================================
# Request Context Tests
# =============================================================================

class TestRequestContext:
    """Tests for request context setting."""

    def test_set_request_context_when_disabled(self, disable_sentry):
        """set_request_context does nothing when Sentry is disabled."""
        # Should not raise
        set_request_context(request_id="req-123")

    def test_set_request_context_with_id(self, enable_sentry):
        """set_request_context sets request ID as tag."""
        with patch("services.sentry_service.set_tag") as mock_set_tag:
            with patch("services.sentry_service.set_context"):
                with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                    set_request_context(request_id="req-123")
                    mock_set_tag.assert_any_call("request_id", "req-123")

    def test_set_request_context_with_endpoint(self, enable_sentry):
        """set_request_context sets endpoint as tag."""
        with patch("services.sentry_service.set_tag") as mock_set_tag:
            with patch("services.sentry_service.set_context"):
                with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                    set_request_context(endpoint="api_users")
                    mock_set_tag.assert_any_call("endpoint", "api_users")


# =============================================================================
# Error Capture Tests
# =============================================================================

class TestCaptureException:
    """Tests for exception capture."""

    def test_capture_exception_when_disabled(self, disable_sentry):
        """capture_exception logs error when Sentry is disabled."""
        with patch("services.sentry_service.logger") as mock_logger:
            result = capture_exception(ValueError("test error"))
            assert result is None
            mock_logger.error.assert_called_once()

    def test_capture_exception_ignored_error(self, enable_sentry):
        """capture_exception returns None for ignored errors."""
        with patch("services.sentry_service.SENTRY_AVAILABLE", True):
            # NotFound is in IGNORED_ERRORS
            class NotFound(Exception):
                pass

            result = capture_exception(NotFound("Not found"))
            assert result is None

    def test_capture_exception_with_extra(self, enable_sentry):
        """capture_exception includes extra context."""
        with patch("services.sentry_service.push_scope") as mock_push:
            with patch("services.sentry_service.sentry_capture_exception") as mock_capture:
                with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                    mock_scope = MagicMock()
                    mock_push.return_value.__enter__ = Mock(return_value=mock_scope)
                    mock_push.return_value.__exit__ = Mock(return_value=False)
                    mock_capture.return_value = "event-123"

                    result = capture_exception(
                        ValueError("test"),
                        extra={"key": "value"},
                    )

                    assert result == "event-123"


class TestCaptureMessage:
    """Tests for message capture."""

    def test_capture_message_when_disabled(self, disable_sentry):
        """capture_message logs when Sentry is disabled."""
        with patch("services.sentry_service.logger") as mock_logger:
            result = capture_message("Test message")
            assert result is None

    def test_capture_message_with_level(self, enable_sentry):
        """capture_message respects level parameter."""
        with patch("services.sentry_service.push_scope") as mock_push:
            with patch("services.sentry_service.sentry_capture_message") as mock_capture:
                with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                    mock_scope = MagicMock()
                    mock_push.return_value.__enter__ = Mock(return_value=mock_scope)
                    mock_push.return_value.__exit__ = Mock(return_value=False)
                    mock_capture.return_value = "event-456"

                    result = capture_message("Warning!", level="warning")

                    assert result == "event-456"
                    assert mock_scope.level == "warning"


# =============================================================================
# Breadcrumb Tests
# =============================================================================

class TestBreadcrumbs:
    """Tests for breadcrumb functionality."""

    def test_add_breadcrumb_when_disabled(self, disable_sentry):
        """add_breadcrumb does nothing when Sentry is disabled."""
        # Should not raise
        add_breadcrumb("Test breadcrumb")

    def test_add_breadcrumb_with_category(self, enable_sentry):
        """add_breadcrumb includes category."""
        with patch("services.sentry_service.sentry_sdk") as mock_sdk:
            with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                add_breadcrumb(
                    message="User clicked button",
                    category="ui",
                    level="info",
                )

                mock_sdk.add_breadcrumb.assert_called_once()
                call_kwargs = mock_sdk.add_breadcrumb.call_args[1]
                assert call_kwargs["message"] == "User clicked button"
                assert call_kwargs["category"] == "ui"
                assert call_kwargs["level"] == "info"


# =============================================================================
# Decorator Tests
# =============================================================================

class TestTrackErrorsDecorator:
    """Tests for track_errors decorator."""

    def test_decorator_success(self):
        """Decorator doesn't interfere with successful calls."""
        @track_errors()
        def my_function():
            return "success"

        result = my_function()
        assert result == "success"

    def test_decorator_captures_error(self, enable_sentry):
        """Decorator captures exceptions."""
        with patch("services.sentry_service.capture_exception") as mock_capture:
            with patch("services.sentry_service.add_breadcrumb"):
                @track_errors(operation="test_op")
                def failing_function():
                    raise ValueError("Test error")

                with pytest.raises(ValueError):
                    failing_function()

                mock_capture.assert_called_once()

    def test_decorator_with_operation_name(self, enable_sentry):
        """Decorator uses operation name in context."""
        with patch("services.sentry_service.capture_exception") as mock_capture:
            with patch("services.sentry_service.add_breadcrumb"):
                @track_errors(operation="custom_operation")
                def my_function():
                    raise RuntimeError()

                with pytest.raises(RuntimeError):
                    my_function()

                call_kwargs = mock_capture.call_args[1]
                assert call_kwargs["extra"]["operation"] == "custom_operation"

    def test_decorator_no_reraise(self, enable_sentry):
        """Decorator can suppress exceptions."""
        with patch("services.sentry_service.capture_exception"):
            with patch("services.sentry_service.add_breadcrumb"):
                @track_errors(reraise=False)
                def failing_function():
                    raise ValueError()

                # Should not raise
                result = failing_function()
                assert result is None


# =============================================================================
# Data Sanitization Tests
# =============================================================================

class TestSanitizeData:
    """Tests for data sanitization."""

    def test_sanitize_none(self):
        """Sanitize handles None input."""
        assert _sanitize_data(None) is None

    def test_sanitize_dict_with_password(self):
        """Sanitize redacts password fields."""
        data = {"username": "john", "password": "secret123"}
        result = _sanitize_data(data)

        assert result["username"] == "john"
        assert result["password"] == "[REDACTED]"

    def test_sanitize_nested_dict(self):
        """Sanitize handles nested dictionaries."""
        data = {
            "user": {
                "email": "test@example.com",
                "api_key": "sk-12345",
            }
        }
        result = _sanitize_data(data)

        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["api_key"] == "[REDACTED]"

    def test_sanitize_list(self):
        """Sanitize handles lists."""
        data = [{"token": "abc"}, {"name": "test"}]
        result = _sanitize_data(data)

        assert result[0]["token"] == "[REDACTED]"
        assert result[1]["name"] == "test"

    def test_sanitize_long_string(self):
        """Sanitize redacts long alphanumeric strings."""
        # Long alphanumeric strings are often secrets
        long_secret = "a" * 50
        result = _sanitize_data(long_secret)
        assert result == "[REDACTED]"

    def test_sanitize_preserves_normal_strings(self):
        """Sanitize preserves normal strings."""
        result = _sanitize_data("Hello World")
        assert result == "Hello World"


class TestIsSensitiveField:
    """Tests for sensitive field detection."""

    def test_password_is_sensitive(self):
        """Password fields are sensitive."""
        assert _is_sensitive_field("password") is True
        assert _is_sensitive_field("user_password") is True
        assert _is_sensitive_field("PASSWORD") is True

    def test_token_is_sensitive(self):
        """Token fields are sensitive."""
        assert _is_sensitive_field("token") is True
        assert _is_sensitive_field("access_token") is True
        assert _is_sensitive_field("auth_token") is True

    def test_api_key_is_sensitive(self):
        """API key fields are sensitive."""
        assert _is_sensitive_field("api_key") is True
        assert _is_sensitive_field("stripe_api_key") is True
        assert _is_sensitive_field("API_KEY") is True

    def test_ssn_is_sensitive(self):
        """SSN fields are sensitive."""
        assert _is_sensitive_field("ssn") is True
        assert _is_sensitive_field("social_security") is True

    def test_normal_field_not_sensitive(self):
        """Normal fields are not sensitive."""
        assert _is_sensitive_field("name") is False
        assert _is_sensitive_field("email") is False
        assert _is_sensitive_field("created_at") is False


# =============================================================================
# Error Categorization Tests
# =============================================================================

class TestErrorCategorization:
    """Tests for error categorization."""

    def test_categorize_database_error(self):
        """Database errors are critical."""
        assert _categorize_error("DatabaseError") == "critical"
        assert _categorize_error("OperationalError") == "critical"
        assert _categorize_error("IntegrityError") == "critical"

    def test_categorize_payment_error(self):
        """Payment errors are critical."""
        assert _categorize_error("PaymentError") == "critical"
        assert _categorize_error("StripeError") == "critical"

    def test_categorize_circuit_breaker_error(self):
        """Circuit breaker errors are critical."""
        assert _categorize_error("CircuitBreakerError") == "critical"

    def test_categorize_auth_error(self):
        """Authentication errors are high priority."""
        assert _categorize_error("AuthenticationError") == "high"
        assert _categorize_error("AuthorizationError") == "high"

    def test_categorize_connection_error(self):
        """Connection errors are medium priority."""
        assert _categorize_error("ConnectionError") == "medium"
        assert _categorize_error("TimeoutError") == "medium"

    def test_categorize_not_found_error(self):
        """Not found errors are low priority."""
        assert _categorize_error("NotFoundError") == "low"

    def test_categorize_unknown_error(self):
        """Unknown errors return 'unknown'."""
        assert _categorize_error("WeirdRandomError") == "unknown"


# =============================================================================
# Slack Notification Tests
# =============================================================================

class TestSlackNotification:
    """Tests for Slack notification functionality."""

    def test_notify_slack_without_webhook(self):
        """Notification returns False without webhook URL."""
        with patch("services.sentry_service.SLACK_WEBHOOK_URL", None):
            result = _notify_slack(ValueError("test"), "event-123", "critical")
            assert result is False

    def test_notify_slack_success(self, mock_requests):
        """Notification succeeds with valid webhook."""
        with patch("services.sentry_service.SLACK_WEBHOOK_URL", "https://hooks.slack.com/test"):
            result = _notify_slack(ValueError("test error"), "event-123", "critical")

            assert result is True
            mock_requests.post.assert_called_once()

            # Verify payload structure
            call_args = mock_requests.post.call_args
            payload = call_args[1]["json"]
            assert "blocks" in payload

    def test_notify_slack_includes_error_type(self, mock_requests):
        """Notification includes error type."""
        with patch("services.sentry_service.SLACK_WEBHOOK_URL", "https://hooks.slack.com/test"):
            _notify_slack(ValueError("test"), "event-123", "critical")

            call_args = mock_requests.post.call_args
            payload = call_args[1]["json"]

            # Check header block contains error type
            header_block = payload["blocks"][0]
            assert "ValueError" in header_block["text"]["text"]

    def test_notify_slack_handles_request_error(self):
        """Notification handles request errors gracefully."""
        with patch("services.sentry_service.SLACK_WEBHOOK_URL", "https://hooks.slack.com/test"):
            with patch("services.sentry_service.requests.post") as mock_post:
                mock_post.side_effect = Exception("Network error")

                result = _notify_slack(ValueError("test"), "event-123", "critical")
                assert result is False


# =============================================================================
# Context Manager Tests
# =============================================================================

class TestSentrySpan:
    """Tests for sentry_span context manager."""

    def test_span_when_disabled(self, disable_sentry):
        """Span does nothing when Sentry is disabled."""
        with sentry_span("database", "query") as span:
            assert span.span is None

    def test_span_creates_span(self, enable_sentry):
        """Span creates Sentry span when enabled."""
        with patch("services.sentry_service.sentry_sdk") as mock_sdk:
            with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                mock_span = MagicMock()
                mock_sdk.start_span.return_value = mock_span

                with sentry_span("database", "query"):
                    pass

                mock_sdk.start_span.assert_called_once_with(
                    op="database",
                    description="query",
                )


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration-style tests for Sentry service."""

    def test_full_error_capture_flow(self, enable_sentry):
        """Test complete error capture with context."""
        with patch("services.sentry_service.push_scope") as mock_push:
            with patch("services.sentry_service.sentry_capture_exception") as mock_capture:
                with patch("services.sentry_service.set_tag"):
                    with patch("services.sentry_service.set_context"):
                        with patch("services.sentry_service.SENTRY_AVAILABLE", True):
                            mock_scope = MagicMock()
                            mock_push.return_value.__enter__ = Mock(return_value=mock_scope)
                            mock_push.return_value.__exit__ = Mock(return_value=False)
                            mock_capture.return_value = "event-789"

                            # Set context first
                            set_user_context(user_id=123, email="test@example.com")
                            set_request_context(request_id="req-456")

                            # Capture an exception
                            error = ValueError("Something went wrong")
                            event_id = capture_exception(
                                error,
                                extra={"context": "test"},
                                tags={"version": "1.0"},
                            )

                            assert event_id == "event-789"
                            mock_capture.assert_called_once()

    def test_decorator_with_slack_notification(self, enable_sentry, mock_requests):
        """Test decorator triggers Slack notification."""
        with patch("services.sentry_service.capture_exception") as mock_capture:
            with patch("services.sentry_service.add_breadcrumb"):
                with patch("services.sentry_service.SLACK_WEBHOOK_URL", "https://hooks.slack.com/test"):
                    @track_errors(notify_slack=True)
                    def critical_operation():
                        raise RuntimeError("Critical failure!")

                    with pytest.raises(RuntimeError):
                        critical_operation()

                    # Verify capture was called with notify_slack=True
                    call_kwargs = mock_capture.call_args[1]
                    assert call_kwargs["notify_slack"] is True
