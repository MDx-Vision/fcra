"""
Tests for Error Sanitization Service

Tests cover:
- Error classification
- Sensitive info detection
- Error sanitization
- Error ID generation
- Production vs debug modes
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from services.error_sanitizer_service import (
    ERROR_CODES,
    GENERIC_MESSAGES,
    classify_error,
    contains_sensitive_info,
    generate_error_id,
    handle_exception,
    safe_error_message,
    sanitize_error,
)


# ============================================================================
# Error Classification Tests
# ============================================================================

class TestErrorClassification:
    """Tests for error classification."""

    def test_classify_database_error_by_type(self):
        """Test classifying database errors by exception type."""
        # Simulate SQLAlchemy error
        class SQLAlchemyError(Exception):
            pass

        error = SQLAlchemyError("connection failed")
        assert classify_error(error) == "database"

    def test_classify_database_error_by_message(self):
        """Test classifying database errors by message content."""
        error = Exception("Database connection timeout")
        assert classify_error(error) == "database"

        error = Exception("SQL query failed")
        assert classify_error(error) == "database"

    def test_classify_validation_error(self):
        """Test classifying validation errors."""
        error = ValueError("invalid input")
        assert classify_error(error) == "validation"

        error = Exception("Required field missing")
        assert classify_error(error) == "validation"

    def test_classify_authentication_error(self):
        """Test classifying authentication errors."""
        error = Exception("Login failed")
        assert classify_error(error) == "authentication"

        error = Exception("Wrong password provided")
        assert classify_error(error) == "authentication"

    def test_classify_authorization_error(self):
        """Test classifying authorization errors."""
        error = Exception("Permission denied")
        assert classify_error(error) == "authorization"

        error = Exception("Access denied to resource")
        assert classify_error(error) == "authorization"

    def test_classify_not_found_error(self):
        """Test classifying not found errors."""
        error = Exception("Resource not found")
        assert classify_error(error) == "not_found"

        error = Exception("User does not exist")
        assert classify_error(error) == "not_found"

    def test_classify_external_service_error(self):
        """Test classifying external service errors."""
        error = Exception("Stripe API error")
        assert classify_error(error) == "external_service"

        error = Exception("Connection timeout to API")
        assert classify_error(error) == "external_service"

    def test_classify_file_error(self):
        """Test classifying file operation errors."""
        error = FileNotFoundError("file.txt not found")
        assert classify_error(error) == "file_operation"

        error = PermissionError("Cannot write to file")
        assert classify_error(error) == "file_operation"

    def test_classify_rate_limit_error(self):
        """Test classifying rate limit errors."""
        error = Exception("Rate limit exceeded")
        assert classify_error(error) == "rate_limit"

    def test_classify_payment_error(self):
        """Test classifying payment errors."""
        error = Exception("Payment failed")
        assert classify_error(error) == "payment"

        error = Exception("Card declined")
        assert classify_error(error) == "payment"

    def test_classify_internal_error(self):
        """Test classifying unknown errors as internal."""
        error = Exception("Something went wrong")
        assert classify_error(error) == "internal"

        error = RuntimeError("Unexpected state")
        assert classify_error(error) == "internal"


# ============================================================================
# Sensitive Info Detection Tests
# ============================================================================

class TestSensitiveInfoDetection:
    """Tests for sensitive information detection."""

    def test_detect_macos_path(self):
        """Test detection of macOS user paths."""
        assert contains_sensitive_info("/Users/john/projects/app.py") is True
        assert contains_sensitive_info("Error in /Users/admin/secret") is True

    def test_detect_linux_path(self):
        """Test detection of Linux user paths."""
        assert contains_sensitive_info("/home/ubuntu/app/config.py") is True

    def test_detect_windows_path(self):
        """Test detection of Windows user paths."""
        assert contains_sensitive_info("C:\\Users\\admin\\Documents") is True

    def test_detect_database_connection_string(self):
        """Test detection of database connection strings."""
        assert contains_sensitive_info("postgresql://user:pass@localhost/db") is True
        assert contains_sensitive_info("mysql://root:secret@127.0.0.1/mydb") is True

    def test_detect_sensitive_keywords(self):
        """Test detection of sensitive keywords."""
        assert contains_sensitive_info("Invalid password provided") is True
        assert contains_sensitive_info("API key invalid") is True
        assert contains_sensitive_info("Token expired") is True

    def test_detect_sql_state(self):
        """Test detection of SQL state codes."""
        assert contains_sensitive_info("SQLSTATE[42000]: Syntax error") is True

    def test_detect_traceback(self):
        """Test detection of Python tracebacks."""
        assert contains_sensitive_info("Traceback (most recent call last):") is True
        assert contains_sensitive_info('File "/app/main.py", line 42') is True

    def test_safe_messages(self):
        """Test that safe messages are not flagged."""
        assert contains_sensitive_info("Invalid email format") is False
        assert contains_sensitive_info("User not found") is False
        assert contains_sensitive_info("Request timeout") is False


# ============================================================================
# Error ID Generation Tests
# ============================================================================

class TestErrorIdGeneration:
    """Tests for error ID generation."""

    def test_generate_error_id_format(self):
        """Test error ID format."""
        error_id = generate_error_id()
        assert error_id.startswith("ERR-")
        # Format: ERR-YYYYMMDDHHMMSS-XXXXXXXX (27 chars)
        assert len(error_id) == 27

    def test_generate_unique_ids(self):
        """Test that error IDs are unique."""
        ids = [generate_error_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique


# ============================================================================
# Error Sanitization Tests
# ============================================================================

class TestErrorSanitization:
    """Tests for error sanitization."""

    @patch("services.error_sanitizer_service.IS_PRODUCTION", True)
    @patch("services.error_sanitizer_service.DEBUG_ERRORS", False)
    def test_sanitize_error_production(self):
        """Test that errors are sanitized in production."""
        error = Exception("Database query failed on table users at /home/app/db.py")

        with patch("services.error_sanitizer_service.error_logger"):
            result = sanitize_error(error)

        assert result["success"] is False
        assert "users" not in result["error"]
        assert "/home/app" not in result["error"]
        assert "error_code" in result
        assert "error_id" in result

    @patch("services.error_sanitizer_service.IS_PRODUCTION", False)
    @patch("services.error_sanitizer_service.DEBUG_ERRORS", False)
    def test_sanitize_error_development(self):
        """Test that safe errors show details in development."""
        error = Exception("User email format invalid")

        with patch("services.error_sanitizer_service.error_logger"):
            result = sanitize_error(error)

        assert result["success"] is False
        # In development, safe messages can be shown
        assert "email" in result["error"].lower() or "invalid" in result["error"].lower()

    @patch("services.error_sanitizer_service.IS_PRODUCTION", False)
    @patch("services.error_sanitizer_service.DEBUG_ERRORS", False)
    def test_sanitize_sensitive_error_development(self):
        """Test that sensitive errors are sanitized even in development."""
        error = Exception("Failed at /Users/john/secret/app.py")

        with patch("services.error_sanitizer_service.error_logger"):
            result = sanitize_error(error)

        assert result["success"] is False
        assert "/Users/john" not in result["error"]

    def test_sanitize_error_includes_error_id(self):
        """Test that error ID is included by default."""
        error = Exception("test error")

        with patch("services.error_sanitizer_service.error_logger"):
            result = sanitize_error(error, include_error_id=True)

        assert "error_id" in result
        assert result["error_id"].startswith("ERR-")

    def test_sanitize_error_without_error_id(self):
        """Test that error ID can be excluded."""
        error = Exception("test error")

        with patch("services.error_sanitizer_service.error_logger"):
            result = sanitize_error(error, include_error_id=False)

        assert "error_id" not in result

    def test_sanitize_error_has_error_code(self):
        """Test that error code is included."""
        error = ValueError("invalid input")

        with patch("services.error_sanitizer_service.error_logger"):
            result = sanitize_error(error)

        assert result["error_code"] == ERROR_CODES["validation"]


# ============================================================================
# Safe Error Message Tests
# ============================================================================

class TestSafeErrorMessage:
    """Tests for safe error message helper."""

    @patch("services.error_sanitizer_service.IS_PRODUCTION", True)
    @patch("services.error_sanitizer_service.DEBUG_ERRORS", False)
    def test_safe_message_production(self):
        """Test safe message in production."""
        error = Exception("Database error on table users")

        message = safe_error_message(error)

        assert "users" not in message
        assert message == GENERIC_MESSAGES["database"]

    @patch("services.error_sanitizer_service.IS_PRODUCTION", False)
    @patch("services.error_sanitizer_service.DEBUG_ERRORS", False)
    def test_safe_message_development(self):
        """Test safe message in development with safe error."""
        error = Exception("Email format invalid")

        message = safe_error_message(error)

        assert "Email format invalid" == message

    def test_safe_message_default(self):
        """Test default message."""
        error = Exception("Unknown error")

        with patch("services.error_sanitizer_service.IS_PRODUCTION", True):
            with patch("services.error_sanitizer_service.DEBUG_ERRORS", False):
                message = safe_error_message(error, default="Custom default")

        # Should return generic message for internal errors
        assert message == GENERIC_MESSAGES["internal"]


# ============================================================================
# Handle Exception Tests
# ============================================================================

class TestHandleException:
    """Tests for handle_exception helper."""

    def test_handle_exception_returns_tuple(self):
        """Test that handle_exception returns response tuple."""
        error = Exception("test error")

        with patch("services.error_sanitizer_service.error_logger"):
            with patch("services.error_sanitizer_service.jsonify") as mock_jsonify:
                mock_jsonify.return_value = {"success": False}
                response, status_code = handle_exception(error)

        assert status_code == 500
        mock_jsonify.assert_called_once()

    def test_handle_exception_custom_status_code(self):
        """Test handle_exception with custom status code."""
        error = Exception("not found")

        with patch("services.error_sanitizer_service.error_logger"):
            with patch("services.error_sanitizer_service.jsonify") as mock_jsonify:
                mock_jsonify.return_value = {"success": False}
                response, status_code = handle_exception(error, status_code=404)

        assert status_code == 404

    def test_handle_exception_with_context(self):
        """Test handle_exception with additional context."""
        error = Exception("test error")
        context = {"user_id": 123, "action": "create"}

        with patch("services.error_sanitizer_service.error_logger") as mock_logger:
            with patch("services.error_sanitizer_service.jsonify") as mock_jsonify:
                mock_jsonify.return_value = {"success": False}
                handle_exception(error, context=context)

        # Verify logger was called
        assert mock_logger.error.called


# ============================================================================
# Error Code Mapping Tests
# ============================================================================

class TestErrorCodeMapping:
    """Tests for error code mapping."""

    def test_all_categories_have_codes(self):
        """Test that all categories have error codes."""
        categories = [
            "database", "validation", "authentication", "authorization",
            "not_found", "external_service", "file_operation", "rate_limit",
            "payment", "internal"
        ]

        for category in categories:
            assert category in ERROR_CODES
            assert category in GENERIC_MESSAGES

    def test_error_codes_format(self):
        """Test error code format."""
        for code in ERROR_CODES.values():
            assert code.startswith("ERR_")
            assert "_" in code

    def test_generic_messages_not_empty(self):
        """Test generic messages are not empty."""
        for message in GENERIC_MESSAGES.values():
            assert len(message) > 10
            assert message.endswith(".")
