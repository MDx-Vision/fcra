"""
Tests for Request ID Tracking Service

Tests cover:
- Request ID generation
- Context variable storage
- Flask integration
- Header propagation
- Logging integration
- Error response handling
"""

import logging
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

from services.request_id_service import (
    generate_request_id,
    get_request_id,
    set_request_id,
    clear_request_id,
    with_request_id_headers,
    extract_request_id_from_headers,
    RequestIDLogFilter,
    RequestIDFormatter,
    add_request_id_to_error_response,
    request_id_context,
    with_request_id,
    REQUEST_ID_HEADER,
    CORRELATION_ID_HEADER,
)


# ============================================================================
# Request ID Generation Tests
# ============================================================================

class TestGenerateRequestId:
    """Tests for generate_request_id function."""

    def test_generate_request_id_returns_string(self):
        """Test that generate_request_id returns a string."""
        request_id = generate_request_id()
        assert isinstance(request_id, str)

    def test_generate_request_id_format(self):
        """Test request ID format: timestamp-uuid."""
        request_id = generate_request_id()
        # Should have format: YYYYMMDDTHHMMSS-xxxxxxxx
        parts = request_id.split("-")
        assert len(parts) >= 2
        # First part should be timestamp
        timestamp_part = parts[0]
        assert "T" in timestamp_part

    def test_generate_request_id_unique(self):
        """Test that generated IDs are unique."""
        ids = [generate_request_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_generate_request_id_contains_timestamp(self):
        """Test that request ID contains current timestamp."""
        before = datetime.utcnow().strftime("%Y%m%d")
        request_id = generate_request_id()
        after = datetime.utcnow().strftime("%Y%m%d")

        # The date part should match either before or after
        assert before in request_id or after in request_id

    def test_generate_request_id_with_prefix(self):
        """Test request ID generation with prefix."""
        with patch.dict("os.environ", {"REQUEST_ID_PREFIX": "test-svc"}):
            # Need to reimport to pick up the env var
            import importlib
            import services.request_id_service as svc
            importlib.reload(svc)

            request_id = svc.generate_request_id()
            # Reload again to restore
            importlib.reload(svc)


# ============================================================================
# Get/Set/Clear Request ID Tests
# ============================================================================

class TestRequestIdContextVar:
    """Tests for request ID context variable operations."""

    def test_set_and_get_request_id(self):
        """Test setting and getting request ID."""
        test_id = "test-request-123"
        set_request_id(test_id)

        result = get_request_id()
        assert result == test_id

        # Cleanup
        clear_request_id()

    def test_clear_request_id(self):
        """Test clearing request ID."""
        set_request_id("test-id")
        clear_request_id()

        result = get_request_id()
        # Should return None (no Flask context)
        assert result is None

    def test_get_request_id_without_setting(self):
        """Test getting request ID when not set."""
        clear_request_id()
        result = get_request_id()
        assert result is None

    def test_request_id_isolation_between_sets(self):
        """Test that setting new ID replaces old ID."""
        set_request_id("first-id")
        set_request_id("second-id")

        result = get_request_id()
        assert result == "second-id"

        clear_request_id()


# ============================================================================
# Header Helpers Tests
# ============================================================================

class TestWithRequestIdHeaders:
    """Tests for with_request_id_headers function."""

    def test_with_request_id_headers_adds_headers(self):
        """Test that request ID headers are added."""
        set_request_id("test-123")

        headers = with_request_id_headers({"Authorization": "Bearer token"})

        assert headers["Authorization"] == "Bearer token"
        assert headers[REQUEST_ID_HEADER] == "test-123"
        assert headers[CORRELATION_ID_HEADER] == "test-123"

        clear_request_id()

    def test_with_request_id_headers_empty_dict(self):
        """Test with no existing headers."""
        set_request_id("test-456")

        headers = with_request_id_headers()

        assert REQUEST_ID_HEADER in headers
        assert CORRELATION_ID_HEADER in headers

        clear_request_id()

    def test_with_request_id_headers_none_input(self):
        """Test with None input."""
        set_request_id("test-789")

        headers = with_request_id_headers(None)

        assert REQUEST_ID_HEADER in headers

        clear_request_id()

    def test_with_request_id_headers_no_request_id(self):
        """Test when no request ID is set."""
        clear_request_id()

        headers = with_request_id_headers({"Custom": "Header"})

        assert headers["Custom"] == "Header"
        # Should not add request ID headers when not set
        assert REQUEST_ID_HEADER not in headers or headers.get(REQUEST_ID_HEADER) is None

    def test_with_request_id_headers_preserves_existing(self):
        """Test that existing headers are preserved."""
        set_request_id("test-id")

        original = {"Content-Type": "application/json", "Accept": "text/html"}
        headers = with_request_id_headers(original)

        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "text/html"

        clear_request_id()


class TestExtractRequestIdFromHeaders:
    """Tests for extract_request_id_from_headers function."""

    def test_extract_x_request_id(self):
        """Test extracting X-Request-ID header."""
        headers = {"X-Request-ID": "req-123"}
        result = extract_request_id_from_headers(headers)
        assert result == "req-123"

    def test_extract_x_correlation_id(self):
        """Test extracting X-Correlation-ID header."""
        headers = {"X-Correlation-ID": "corr-456"}
        result = extract_request_id_from_headers(headers)
        assert result == "corr-456"

    def test_extract_x_trace_id(self):
        """Test extracting X-Trace-ID header."""
        headers = {"X-Trace-ID": "trace-789"}
        result = extract_request_id_from_headers(headers)
        assert result == "trace-789"

    def test_extract_aws_trace_id(self):
        """Test extracting AWS X-Amzn-Trace-Id header."""
        headers = {"X-Amzn-Trace-Id": "Root=1-123-abc"}
        result = extract_request_id_from_headers(headers)
        assert result == "Root=1-123-abc"

    def test_extract_w3c_traceparent(self):
        """Test extracting W3C traceparent header."""
        headers = {"traceparent": "00-abc123-def456-01"}
        result = extract_request_id_from_headers(headers)
        assert result == "00-abc123-def456-01"

    def test_extract_priority_order(self):
        """Test that X-Request-ID takes priority."""
        headers = {
            "X-Request-ID": "preferred",
            "X-Correlation-ID": "second",
            "X-Trace-ID": "third"
        }
        result = extract_request_id_from_headers(headers)
        assert result == "preferred"

    def test_extract_no_headers(self):
        """Test extraction with no matching headers."""
        headers = {"Content-Type": "application/json"}
        result = extract_request_id_from_headers(headers)
        assert result is None

    def test_extract_empty_headers(self):
        """Test extraction with empty headers dict."""
        result = extract_request_id_from_headers({})
        assert result is None


# ============================================================================
# Logging Integration Tests
# ============================================================================

class TestRequestIDLogFilter:
    """Tests for RequestIDLogFilter class."""

    def test_filter_adds_request_id_attribute(self):
        """Test that filter adds request_id to log record."""
        set_request_id("log-test-123")

        filter_instance = RequestIDLogFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        result = filter_instance.filter(record)

        assert result is True
        assert hasattr(record, "request_id")
        assert record.request_id == "log-test-123"

        clear_request_id()

    def test_filter_uses_dash_when_no_request_id(self):
        """Test that filter uses '-' when no request ID."""
        clear_request_id()

        filter_instance = RequestIDLogFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        filter_instance.filter(record)

        assert record.request_id == "-"

    def test_filter_always_returns_true(self):
        """Test that filter always allows log record through."""
        filter_instance = RequestIDLogFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=None
        )

        result = filter_instance.filter(record)
        assert result is True


class TestRequestIDFormatter:
    """Tests for RequestIDFormatter class."""

    def test_formatter_includes_request_id_in_message(self):
        """Test that formatter includes request_id in output."""
        set_request_id("fmt-test-123")

        formatter = RequestIDFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        output = formatter.format(record)

        assert "fmt-test-123" in output

        clear_request_id()

    def test_formatter_default_format(self):
        """Test formatter default format string."""
        formatter = RequestIDFormatter()
        # Check that format includes request_id placeholder
        assert "%(request_id)s" in formatter._fmt

    def test_formatter_custom_format(self):
        """Test formatter with custom format string."""
        formatter = RequestIDFormatter(
            fmt="%(levelname)s - %(request_id)s - %(message)s"
        )

        set_request_id("custom-123")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Custom message",
            args=(),
            exc_info=None
        )

        output = formatter.format(record)

        assert "INFO" in output
        assert "custom-123" in output
        assert "Custom message" in output

        clear_request_id()


# ============================================================================
# Error Response Tests
# ============================================================================

class TestAddRequestIdToErrorResponse:
    """Tests for add_request_id_to_error_response function."""

    def test_adds_request_id_to_response(self):
        """Test that request_id is added to error response."""
        set_request_id("error-123")

        response = add_request_id_to_error_response({
            "success": False,
            "error": "Something went wrong"
        })

        assert response["success"] is False
        assert response["error"] == "Something went wrong"
        assert response["request_id"] == "error-123"

        clear_request_id()

    def test_preserves_existing_fields(self):
        """Test that existing fields are preserved."""
        set_request_id("error-456")

        response = add_request_id_to_error_response({
            "success": False,
            "error": "Error message",
            "error_code": "ERR_001",
            "details": {"field": "value"}
        })

        assert response["error_code"] == "ERR_001"
        assert response["details"] == {"field": "value"}

        clear_request_id()

    def test_no_request_id_when_not_set(self):
        """Test response when no request ID is set."""
        clear_request_id()

        response = add_request_id_to_error_response({
            "success": False,
            "error": "Error"
        })

        # Should not have request_id key
        assert "request_id" not in response or response.get("request_id") is None

    def test_does_not_modify_original(self):
        """Test that original dict is not modified."""
        set_request_id("error-789")

        original = {"success": False, "error": "Error"}
        response = add_request_id_to_error_response(original)

        # Original should not have request_id
        assert "request_id" not in original
        # New response should have it
        assert "request_id" in response

        clear_request_id()


# ============================================================================
# Context Manager Tests
# ============================================================================

class TestRequestIdContext:
    """Tests for request_id_context context manager."""

    def test_context_manager_sets_request_id(self):
        """Test that context manager sets request ID."""
        clear_request_id()

        with request_id_context("ctx-123"):
            assert get_request_id() == "ctx-123"

    def test_context_manager_generates_id_if_none(self):
        """Test that context manager generates ID if none provided."""
        clear_request_id()

        with request_id_context() as rid:
            assert rid is not None
            assert get_request_id() == rid

    def test_context_manager_clears_after_exit(self):
        """Test that context manager clears ID after exit."""
        clear_request_id()

        with request_id_context("temp-id"):
            pass

        assert get_request_id() is None

    def test_context_manager_restores_previous_id(self):
        """Test that context manager restores previous ID."""
        set_request_id("original-id")

        with request_id_context("nested-id"):
            assert get_request_id() == "nested-id"

        assert get_request_id() == "original-id"

        clear_request_id()

    def test_context_manager_returns_request_id(self):
        """Test that context manager returns request ID."""
        with request_id_context("return-test") as rid:
            assert rid == "return-test"


# ============================================================================
# Decorator Tests
# ============================================================================

class TestWithRequestIdDecorator:
    """Tests for with_request_id decorator."""

    def test_decorator_generates_request_id(self):
        """Test that decorator generates request ID if not set."""
        clear_request_id()

        @with_request_id
        def my_function():
            return get_request_id()

        result = my_function()
        assert result is not None

    def test_decorator_uses_existing_request_id(self):
        """Test that decorator uses existing request ID."""
        set_request_id("existing-id")

        @with_request_id
        def my_function():
            return get_request_id()

        result = my_function()
        assert result == "existing-id"

        clear_request_id()

    def test_decorator_preserves_return_value(self):
        """Test that decorator preserves function return value."""
        @with_request_id
        def add_numbers(a, b):
            return a + b

        result = add_numbers(2, 3)
        assert result == 5

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @with_request_id
        def my_named_function():
            pass

        assert my_named_function.__name__ == "my_named_function"

    def test_decorator_handles_exceptions(self):
        """Test that decorator handles exceptions properly."""
        @with_request_id
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()


# ============================================================================
# Constants Tests
# ============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_request_id_header_value(self):
        """Test REQUEST_ID_HEADER constant."""
        assert REQUEST_ID_HEADER == "X-Request-ID"

    def test_correlation_id_header_value(self):
        """Test CORRELATION_ID_HEADER constant."""
        assert CORRELATION_ID_HEADER == "X-Correlation-ID"


# ============================================================================
# Integration Tests
# ============================================================================

class TestRequestIdIntegration:
    """Integration tests for request ID tracking."""

    def test_full_flow(self):
        """Test complete request ID flow."""
        # 1. Generate request ID
        request_id = generate_request_id()
        assert request_id is not None

        # 2. Set request ID
        set_request_id(request_id)
        assert get_request_id() == request_id

        # 3. Add to headers
        headers = with_request_id_headers({"Content-Type": "application/json"})
        assert headers[REQUEST_ID_HEADER] == request_id

        # 4. Add to error response
        error = add_request_id_to_error_response({"success": False})
        assert error["request_id"] == request_id

        # 5. Clear
        clear_request_id()
        assert get_request_id() is None

    def test_nested_contexts(self):
        """Test nested request ID contexts."""
        set_request_id("outer")

        with request_id_context("middle"):
            assert get_request_id() == "middle"

            with request_id_context("inner"):
                assert get_request_id() == "inner"

            assert get_request_id() == "middle"

        assert get_request_id() == "outer"

        clear_request_id()
