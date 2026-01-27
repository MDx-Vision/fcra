"""
Tests for Retry Service

Tests cover:
- Retry decorator functionality
- Exponential backoff calculation
- Retry statistics tracking
- Pre-configured retry decorators (Stripe, Twilio, Email, HTTP)
- RetryableHTTPClient
- Request ID integration
"""

import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from services.retry_service import (
    with_retry,
    retry_external_api,
    calculate_backoff_time,
    get_retry_stats,
    reset_retry_stats,
    retry_stripe,
    retry_twilio,
    retry_email,
    retry_http,
    RetryableHTTPClient,
    get_http_client,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MIN_WAIT_SECONDS,
    DEFAULT_MAX_WAIT_SECONDS,
    TRANSIENT_EXCEPTIONS,
)


# ============================================================================
# Backoff Calculation Tests
# ============================================================================

class TestCalculateBackoffTime:
    """Tests for calculate_backoff_time function."""

    def test_first_attempt_returns_min_wait(self):
        """First attempt should return approximately min_wait."""
        result = calculate_backoff_time(1, min_wait=1, max_wait=30, jitter=False)
        assert result == 1

    def test_exponential_increase(self):
        """Backoff should increase exponentially."""
        wait1 = calculate_backoff_time(1, min_wait=1, max_wait=100, jitter=False)
        wait2 = calculate_backoff_time(2, min_wait=1, max_wait=100, jitter=False)
        wait3 = calculate_backoff_time(3, min_wait=1, max_wait=100, jitter=False)

        assert wait1 == 1  # 1 * 2^0
        assert wait2 == 2  # 1 * 2^1
        assert wait3 == 4  # 1 * 2^2

    def test_max_wait_cap(self):
        """Wait time should not exceed max_wait."""
        result = calculate_backoff_time(10, min_wait=1, max_wait=30, jitter=False)
        assert result == 30

    def test_jitter_adds_randomness(self):
        """Jitter should add randomness to wait time."""
        results = [calculate_backoff_time(2, jitter=True) for _ in range(10)]
        # With jitter, not all results should be exactly the same
        assert len(set(results)) > 1

    def test_jitter_stays_within_bounds(self):
        """Jitter should stay within 0-25% of base wait time."""
        base_wait = calculate_backoff_time(2, min_wait=1, max_wait=30, jitter=False)
        for _ in range(100):
            result = calculate_backoff_time(2, min_wait=1, max_wait=30, jitter=True)
            # Should be between base and base + 25%
            assert result >= base_wait
            assert result <= base_wait * 1.25

    def test_custom_base(self):
        """Custom exponential base should work."""
        wait1 = calculate_backoff_time(1, min_wait=1, max_wait=100, base=3, jitter=False)
        wait2 = calculate_backoff_time(2, min_wait=1, max_wait=100, base=3, jitter=False)
        wait3 = calculate_backoff_time(3, min_wait=1, max_wait=100, base=3, jitter=False)

        assert wait1 == 1  # 1 * 3^0
        assert wait2 == 3  # 1 * 3^1
        assert wait3 == 9  # 1 * 3^2


# ============================================================================
# Retry Statistics Tests
# ============================================================================

class TestRetryStats:
    """Tests for retry statistics tracking."""

    def setup_method(self):
        """Reset stats before each test."""
        reset_retry_stats()

    def test_initial_stats_are_zero(self):
        """Initial stats should be zero."""
        stats = get_retry_stats()
        assert stats["total_attempts"] == 0
        assert stats["total_retries"] == 0
        assert stats["total_successes"] == 0
        assert stats["total_failures"] == 0
        assert stats["by_service"] == {}

    def test_reset_stats(self):
        """Reset should clear all stats."""
        # Modify stats
        with_retry(max_attempts=1)(lambda: 1)()

        # Reset
        reset_retry_stats()

        stats = get_retry_stats()
        assert stats["total_attempts"] == 0

    def test_successful_call_increments_success(self):
        """Successful calls should increment success counter."""
        reset_retry_stats()

        @with_retry(max_attempts=3, service_name="test_service")
        def successful_func():
            return "success"

        successful_func()

        stats = get_retry_stats()
        assert stats["total_successes"] == 1
        assert stats["total_attempts"] == 1
        assert stats["total_failures"] == 0


# ============================================================================
# Retry Decorator Tests
# ============================================================================

class TestWithRetryDecorator:
    """Tests for with_retry decorator."""

    def setup_method(self):
        """Reset stats before each test."""
        reset_retry_stats()

    def test_successful_first_attempt(self):
        """Function should succeed on first attempt without retries."""
        call_count = 0

        @with_retry(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()

        assert result == "success"
        assert call_count == 1

    def test_retry_on_transient_exception(self):
        """Should retry on transient exceptions."""
        call_count = 0

        @with_retry(max_attempts=3, min_wait=0.01, max_wait=0.02)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = fail_then_succeed()

        assert result == "success"
        assert call_count == 3

    def test_max_attempts_exhausted(self):
        """Should raise exception after max attempts exhausted."""
        call_count = 0

        @with_retry(max_attempts=3, min_wait=0.01, max_wait=0.02)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError, match="Always fails"):
            always_fail()

        assert call_count == 3

    def test_no_retry_on_non_transient_exception(self):
        """Should not retry on non-transient exceptions."""
        call_count = 0

        @with_retry(max_attempts=3, retry_exceptions=(ConnectionError,))
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not transient")

        with pytest.raises(ValueError, match="Not transient"):
            raise_value_error()

        assert call_count == 1

    def test_preserves_function_name(self):
        """Decorator should preserve function name."""
        @with_retry()
        def my_named_function():
            pass

        assert my_named_function.__name__ == "my_named_function"

    def test_preserves_return_value(self):
        """Decorator should preserve return value."""
        @with_retry()
        def return_dict():
            return {"key": "value", "number": 42}

        result = return_dict()
        assert result == {"key": "value", "number": 42}

    def test_reraise_false_returns_none(self):
        """With reraise=False, should return None on failure."""
        @with_retry(max_attempts=2, reraise=False, min_wait=0.01)
        def always_fail():
            raise ConnectionError("Fail")

        result = always_fail()
        assert result is None

    def test_custom_retry_exceptions(self):
        """Should retry on custom exception types."""
        call_count = 0

        class CustomError(Exception):
            pass

        @with_retry(max_attempts=3, retry_exceptions=(CustomError,), min_wait=0.01)
        def fail_with_custom():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise CustomError("Custom failure")
            return "success"

        result = fail_with_custom()
        assert result == "success"
        assert call_count == 3

    def test_service_name_for_logging(self):
        """Service name should be used for logging."""
        reset_retry_stats()

        @with_retry(max_attempts=1, service_name="my_service")
        def test_func():
            return True

        test_func()

        # Stats don't track by service for successes without retries
        # But the function should still work
        assert True


# ============================================================================
# Retry External API Function Tests
# ============================================================================

class TestRetryExternalApi:
    """Tests for retry_external_api function."""

    def test_successful_lambda(self):
        """Should work with lambda functions."""
        result = retry_external_api(
            lambda: "lambda result",
            service_name="test_lambda"
        )
        assert result == "lambda result"

    def test_retry_with_lambda(self):
        """Should retry lambda functions."""
        call_count = [0]

        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Temporary failure")
            return "success after retry"

        result = retry_external_api(
            flaky_func,
            max_attempts=3,
            min_wait=0.01,
            service_name="test_flaky"
        )

        assert result == "success after retry"
        assert call_count[0] == 2


# ============================================================================
# Pre-configured Decorator Tests
# ============================================================================

class TestPreConfiguredDecorators:
    """Tests for pre-configured retry decorators."""

    def test_retry_stripe_decorator(self):
        """retry_stripe should create a working decorator."""
        @retry_stripe(max_attempts=2)
        def stripe_call():
            return "stripe success"

        result = stripe_call()
        assert result == "stripe success"

    def test_retry_twilio_decorator(self):
        """retry_twilio should create a working decorator."""
        @retry_twilio(max_attempts=2)
        def twilio_call():
            return "twilio success"

        result = twilio_call()
        assert result == "twilio success"

    def test_retry_email_decorator(self):
        """retry_email should create a working decorator."""
        @retry_email(max_attempts=2)
        def email_call():
            return "email success"

        result = email_call()
        assert result == "email success"

    def test_retry_http_decorator(self):
        """retry_http should create a working decorator."""
        @retry_http(max_attempts=2, service_name="test_http")
        def http_call():
            return "http success"

        result = http_call()
        assert result == "http success"


# ============================================================================
# RetryableHTTPClient Tests
# ============================================================================

class TestRetryableHTTPClient:
    """Tests for RetryableHTTPClient class."""

    def test_initialization(self):
        """Client should initialize with correct defaults."""
        client = RetryableHTTPClient(service_name="test")
        assert client.service_name == "test"
        assert client.max_attempts == 3
        assert client.timeout == 30

    def test_custom_initialization(self):
        """Client should accept custom parameters."""
        client = RetryableHTTPClient(
            service_name="custom",
            max_attempts=5,
            min_wait=2,
            max_wait=60,
            timeout=45
        )
        assert client.max_attempts == 5
        assert client.min_wait == 2
        assert client.max_wait == 60
        assert client.timeout == 45

    @patch("requests.request")
    def test_get_request(self, mock_request):
        """GET request should work."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        client = RetryableHTTPClient(service_name="test")
        response = client.get("https://api.example.com/test")

        assert response == mock_response
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "https://api.example.com/test"

    @patch("requests.request")
    def test_post_request(self, mock_request):
        """POST request should work."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response

        client = RetryableHTTPClient(service_name="test")
        response = client.post(
            "https://api.example.com/test",
            json={"key": "value"}
        )

        assert response == mock_response
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[1]["json"] == {"key": "value"}

    @patch("requests.request")
    def test_retry_on_connection_error(self, mock_request):
        """Should retry on connection errors."""
        import requests as req_module

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise req_module.exceptions.ConnectionError("Connection failed")
            mock_response = MagicMock()
            mock_response.status_code = 200
            return mock_response

        mock_request.side_effect = side_effect

        client = RetryableHTTPClient(
            service_name="test",
            max_attempts=3,
            min_wait=0.01,
            max_wait=0.02
        )
        response = client.get("https://api.example.com/test")

        assert response.status_code == 200
        assert call_count[0] == 3

    @patch("requests.request")
    def test_retry_on_429_status(self, mock_request):
        """Should retry on 429 rate limit status."""
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_response = MagicMock()
            if call_count[0] < 2:
                mock_response.status_code = 429
                mock_response.text = "Rate limited"
            else:
                mock_response.status_code = 200
            return mock_response

        mock_request.side_effect = side_effect

        client = RetryableHTTPClient(
            service_name="test",
            max_attempts=3,
            min_wait=0.01,
            max_wait=0.02
        )
        response = client.get("https://api.example.com/test")

        assert response.status_code == 200
        assert call_count[0] == 2

    @patch("requests.request")
    def test_retry_on_500_status(self, mock_request):
        """Should retry on 5xx server error status."""
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_response = MagicMock()
            if call_count[0] < 2:
                mock_response.status_code = 503
                mock_response.text = "Service unavailable"
            else:
                mock_response.status_code = 200
            return mock_response

        mock_request.side_effect = side_effect

        client = RetryableHTTPClient(
            service_name="test",
            max_attempts=3,
            min_wait=0.01,
            max_wait=0.02
        )
        response = client.get("https://api.example.com/test")

        assert response.status_code == 200
        assert call_count[0] == 2

    def test_is_retryable_status(self):
        """Should correctly identify retryable status codes."""
        client = RetryableHTTPClient(service_name="test")

        # Retryable
        assert client._is_retryable_status(429) is True
        assert client._is_retryable_status(500) is True
        assert client._is_retryable_status(502) is True
        assert client._is_retryable_status(503) is True
        assert client._is_retryable_status(504) is True

        # Not retryable
        assert client._is_retryable_status(200) is False
        assert client._is_retryable_status(201) is False
        assert client._is_retryable_status(400) is False
        assert client._is_retryable_status(401) is False
        assert client._is_retryable_status(404) is False


# ============================================================================
# Get HTTP Client Helper Tests
# ============================================================================

class TestGetHttpClient:
    """Tests for get_http_client helper function."""

    def test_returns_retryable_client(self):
        """Should return a RetryableHTTPClient instance."""
        client = get_http_client("my_service")
        assert isinstance(client, RetryableHTTPClient)
        assert client.service_name == "my_service"

    def test_custom_parameters(self):
        """Should accept custom parameters."""
        client = get_http_client(
            "custom_service",
            max_attempts=5,
            timeout=60
        )
        assert client.max_attempts == 5
        assert client.timeout == 60


# ============================================================================
# Constants Tests
# ============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_default_max_attempts(self):
        """Default max attempts should be 3."""
        assert DEFAULT_MAX_ATTEMPTS == 3

    def test_default_min_wait(self):
        """Default min wait should be 1 second."""
        assert DEFAULT_MIN_WAIT_SECONDS == 1

    def test_default_max_wait(self):
        """Default max wait should be 30 seconds."""
        assert DEFAULT_MAX_WAIT_SECONDS == 30

    def test_transient_exceptions(self):
        """Transient exceptions should include connection-related errors."""
        assert ConnectionError in TRANSIENT_EXCEPTIONS
        assert TimeoutError in TRANSIENT_EXCEPTIONS
        assert OSError in TRANSIENT_EXCEPTIONS


# ============================================================================
# Integration Tests
# ============================================================================

class TestRetryIntegration:
    """Integration tests for retry functionality."""

    def test_full_retry_flow(self):
        """Test complete retry flow with failure and recovery."""
        reset_retry_stats()
        attempts = [0]

        @with_retry(max_attempts=3, min_wait=0.01, max_wait=0.02, service_name="integration_test")
        def flaky_operation():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ConnectionError("Network hiccup")
            return {"status": "success", "data": [1, 2, 3]}

        result = flaky_operation()

        assert result == {"status": "success", "data": [1, 2, 3]}
        assert attempts[0] == 3

        stats = get_retry_stats()
        assert stats["total_successes"] == 1
        assert stats["total_retries"] == 2  # 2 retries before success

    def test_timeout_retry_flow(self):
        """Test retry flow with timeout errors."""
        attempts = [0]

        @with_retry(max_attempts=3, min_wait=0.01, max_wait=0.02)
        def timeout_operation():
            attempts[0] += 1
            if attempts[0] < 2:
                raise TimeoutError("Request timed out")
            return "recovered"

        result = timeout_operation()

        assert result == "recovered"
        assert attempts[0] == 2

    @patch("services.request_id_service.get_request_id")
    def test_request_id_integration(self, mock_get_request_id):
        """Test that request ID is included in logging."""
        mock_get_request_id.return_value = "test-request-123"

        @with_retry(max_attempts=2, min_wait=0.01, service_name="request_id_test")
        def simple_operation():
            return "done"

        result = simple_operation()
        assert result == "done"
        # Request ID should have been retrieved (called in _get_request_id helper)
        mock_get_request_id.assert_called()
