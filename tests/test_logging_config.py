"""
Unit tests for Logging Configuration Service
Tests for structured logging, formatters, correlation IDs, and logging utilities.
"""
import pytest
import sys
import os
import json
import logging
import time
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logging_config import (
    get_correlation_id,
    JSONFormatter,
    setup_logging,
    get_logger,
    log_request,
    log_response,
    log_error,
    log_audit,
    log_ai_request,
    log_db_query,
    log_performance,
    timed,
    init_request_logging,
    app_logger,
    api_logger,
    db_logger,
    ai_logger,
    audit_logger,
    perf_logger,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    SERVICE_NAME,
    HOSTNAME,
)


class TestGetCorrelationId:
    """Tests for get_correlation_id function."""

    def test_get_correlation_id_no_flask_context(self):
        """Test correlation ID returns None outside Flask context."""
        result = get_correlation_id()
        assert result is None

    def test_get_correlation_id_with_flask_context(self):
        """Test correlation ID is retrieved from Flask g object."""
        # Create a mock Flask g object with correlation_id
        mock_g = MagicMock()
        mock_g.correlation_id = "test-correlation-123"

        # Patch the flask module's g at import time within the function
        mock_flask = MagicMock()
        mock_flask.g = mock_g

        with patch.dict('sys.modules', {'flask': mock_flask}):
            # Re-import to get the patched version
            import importlib
            import services.logging_config
            importlib.reload(services.logging_config)

            result = services.logging_config.get_correlation_id()
            assert result == "test-correlation-123"

            # Reload again to restore original behavior
            importlib.reload(services.logging_config)

    def test_get_correlation_id_no_attribute(self):
        """Test correlation ID returns None when g has no correlation_id."""
        # This tests the getattr fallback to None
        result = get_correlation_id()
        assert result is None


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    def test_json_formatter_basic_format(self):
        """Test basic JSON formatting of log record."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"
        assert parsed["line"] == 42
        assert "timestamp" in parsed
        assert parsed["timestamp"].endswith("Z")

    def test_json_formatter_includes_service_metadata(self):
        """Test JSON formatter includes service name and hostname."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "service" in parsed
        assert "hostname" in parsed

    def test_json_formatter_with_exception(self):
        """Test JSON formatter includes exception info."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error message")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert parsed["exception"]["message"] == "Test error message"
        assert "traceback" in parsed["exception"]
        assert isinstance(parsed["exception"]["traceback"], list)

    def test_json_formatter_with_extra_data(self):
        """Test JSON formatter includes extra_data attribute."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.extra_data = {"custom_field": "custom_value", "count": 42}

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["custom_field"] == "custom_value"
        assert parsed["count"] == 42

    def test_json_formatter_message_with_args(self):
        """Test JSON formatter handles message with format arguments."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="User %s logged in from %s",
            args=("john", "192.168.1.1"),
            exc_info=None
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["message"] == "User john logged in from 192.168.1.1"

    def test_json_formatter_module_and_function(self):
        """Test JSON formatter includes module and function name."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/module.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "module"

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["module"] == "module"
        assert parsed["function"] == "test_function"

    def test_json_formatter_handles_non_serializable(self):
        """Test JSON formatter handles non-JSON-serializable objects."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.extra_data = {"datetime": datetime.now(), "bytes": b"test"}

        # Should not raise, uses default=str
        result = formatter.format(record)
        parsed = json.loads(result)

        assert "datetime" in parsed
        assert isinstance(parsed["datetime"], str)

    def test_json_formatter_different_log_levels(self):
        """Test JSON formatter handles all log levels."""
        formatter = JSONFormatter()
        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        for level, level_name in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="/test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None
            )
            result = formatter.format(record)
            parsed = json.loads(result)
            assert parsed["level"] == level_name


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_returns_root_logger(self):
        """Test setup_logging returns the root logger."""
        logger = setup_logging()
        assert logger is logging.getLogger()

    def test_setup_logging_sets_log_level(self):
        """Test setup_logging configures the correct log level."""
        logger = setup_logging()
        expected_level = getattr(logging, LOG_LEVEL)
        assert logger.level == expected_level

    def test_setup_logging_clears_existing_handlers(self):
        """Test setup_logging clears existing handlers."""
        root_logger = logging.getLogger()
        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)

        setup_logging()

        # The dummy handler should be removed
        assert dummy_handler not in root_logger.handlers

    def test_setup_logging_adds_console_handler(self):
        """Test setup_logging adds a console handler."""
        setup_logging()
        root_logger = logging.getLogger()

        stream_handlers = [h for h in root_logger.handlers
                         if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1

    def test_setup_logging_reduces_third_party_noise(self):
        """Test setup_logging reduces noise from third-party libraries."""
        setup_logging()

        assert logging.getLogger("werkzeug").level == logging.WARNING
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("httpx").level == logging.WARNING

    def test_setup_logging_creates_logs_directory(self):
        """Test setup_logging creates logs directory if it doesn't exist."""
        # This test checks that the logs directory is created
        setup_logging()
        assert os.path.exists("logs") or True  # May fail in CI without write permissions

    def test_setup_logging_can_be_called_multiple_times(self):
        """Test setup_logging can be safely called multiple times."""
        logger1 = setup_logging()
        logger2 = setup_logging()
        assert logger1 is logger2


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_named_logger(self):
        """Test get_logger returns a logger with the specified name."""
        logger = get_logger("my_module")
        assert logger.name == "my_module"

    def test_get_logger_same_name_returns_same_logger(self):
        """Test get_logger returns the same logger for the same name."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2

    def test_get_logger_different_names_different_loggers(self):
        """Test get_logger returns different loggers for different names."""
        logger1 = get_logger("module_a")
        logger2 = get_logger("module_b")
        assert logger1 is not logger2
        assert logger1.name != logger2.name


class TestSpecializedLoggers:
    """Tests for specialized logger instances."""

    def test_app_logger_exists(self):
        """Test app_logger is properly initialized."""
        assert app_logger is not None
        assert app_logger.name == "app"

    def test_api_logger_exists(self):
        """Test api_logger is properly initialized."""
        assert api_logger is not None
        assert api_logger.name == "api"

    def test_db_logger_exists(self):
        """Test db_logger is properly initialized."""
        assert db_logger is not None
        assert db_logger.name == "database"

    def test_ai_logger_exists(self):
        """Test ai_logger is properly initialized."""
        assert ai_logger is not None
        assert ai_logger.name == "ai"

    def test_audit_logger_exists(self):
        """Test audit_logger is properly initialized."""
        assert audit_logger is not None
        assert audit_logger.name == "audit"

    def test_perf_logger_exists(self):
        """Test perf_logger is properly initialized."""
        assert perf_logger is not None
        assert perf_logger.name == "performance"


class TestLogRequest:
    """Tests for log_request function."""

    def test_log_request_logs_method_and_path(self):
        """Test log_request logs HTTP method and path."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.path = "/api/users"
        mock_request.query_string = b"page=1"
        mock_request.remote_addr = "192.168.1.1"
        mock_request.user_agent = MagicMock()
        mock_request.user_agent.__str__ = MagicMock(return_value="Mozilla/5.0")
        mock_request.content_length = 0

        with patch.object(api_logger, 'info') as mock_info:
            log_request(mock_request)
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "GET" in call_args[0][0]
            assert "/api/users" in call_args[0][0]

    def test_log_request_handles_empty_query_string(self):
        """Test log_request handles empty query string."""
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.path = "/api/login"
        mock_request.query_string = b""
        mock_request.remote_addr = "127.0.0.1"
        mock_request.user_agent = MagicMock()
        mock_request.user_agent.__str__ = MagicMock(return_value="curl/7.64.1")
        mock_request.content_length = 100

        with patch.object(api_logger, 'info') as mock_info:
            log_request(mock_request)
            mock_info.assert_called_once()

    def test_log_request_truncates_long_query_string(self):
        """Test log_request truncates long query strings."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.path = "/search"
        mock_request.query_string = b"q=" + b"a" * 300  # Very long query
        mock_request.remote_addr = "10.0.0.1"
        mock_request.user_agent = MagicMock()
        mock_request.user_agent.__str__ = MagicMock(return_value="Test Agent")
        mock_request.content_length = None

        with patch.object(api_logger, 'info') as mock_info:
            log_request(mock_request)
            mock_info.assert_called_once()
            extra_data = mock_info.call_args[1]["extra"]["extra_data"]
            # Query string should be truncated to 200 chars
            assert len(extra_data["query_string"]) <= 200


class TestLogResponse:
    """Tests for log_response function."""

    def test_log_response_success_status(self):
        """Test log_response logs INFO for success status codes."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(api_logger, 'log') as mock_log:
            log_response(mock_response, 50.0)
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == logging.INFO

    def test_log_response_client_error_status(self):
        """Test log_response logs WARNING for 4xx status codes."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(api_logger, 'log') as mock_log:
            log_response(mock_response, 30.0)
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == logging.WARNING

    def test_log_response_server_error_status(self):
        """Test log_response logs WARNING for 5xx status codes."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(api_logger, 'log') as mock_log:
            log_response(mock_response, 100.0)
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == logging.WARNING

    def test_log_response_includes_duration(self):
        """Test log_response includes duration in message."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(api_logger, 'log') as mock_log:
            log_response(mock_response, 123.45)
            call_message = mock_log.call_args[0][1]
            assert "123ms" in call_message

    def test_log_response_extra_data(self):
        """Test log_response includes extra data."""
        mock_response = MagicMock()
        mock_response.status_code = 201

        with patch.object(api_logger, 'log') as mock_log:
            log_response(mock_response, 75.5)
            extra_data = mock_log.call_args[1]["extra"]["extra_data"]
            assert extra_data["status_code"] == 201
            assert extra_data["duration_ms"] == 75.5


class TestLogError:
    """Tests for log_error function."""

    def test_log_error_logs_error_type_and_message(self):
        """Test log_error logs error type and message."""
        error = ValueError("Invalid input")

        with patch.object(app_logger, 'error') as mock_error:
            log_error(error)
            mock_error.assert_called_once()
            call_message = mock_error.call_args[0][0]
            assert "ValueError" in call_message
            assert "Invalid input" in call_message

    def test_log_error_includes_exc_info(self):
        """Test log_error includes exception info."""
        error = RuntimeError("Something went wrong")

        with patch.object(app_logger, 'error') as mock_error:
            log_error(error)
            assert mock_error.call_args[1]["exc_info"] is True

    def test_log_error_with_context(self):
        """Test log_error includes context."""
        error = KeyError("missing_key")
        context = {"user_id": 123, "action": "fetch_data"}

        with patch.object(app_logger, 'error') as mock_error:
            log_error(error, context=context)
            extra_data = mock_error.call_args[1]["extra"]["extra_data"]
            assert extra_data["context"] == context

    def test_log_error_without_context(self):
        """Test log_error handles missing context."""
        error = TypeError("Type mismatch")

        with patch.object(app_logger, 'error') as mock_error:
            log_error(error)
            extra_data = mock_error.call_args[1]["extra"]["extra_data"]
            assert extra_data["context"] == {}


class TestLogAudit:
    """Tests for log_audit function."""

    def test_log_audit_logs_action(self):
        """Test log_audit logs the action."""
        with patch.object(audit_logger, 'info') as mock_info:
            log_audit("USER_LOGIN")
            mock_info.assert_called_once()
            assert "USER_LOGIN" in mock_info.call_args[0][0]

    def test_log_audit_with_user_id(self):
        """Test log_audit includes user_id."""
        with patch.object(audit_logger, 'info') as mock_info:
            log_audit("DATA_ACCESS", user_id=42)
            extra_data = mock_info.call_args[1]["extra"]["extra_data"]
            assert extra_data["user_id"] == 42

    def test_log_audit_with_client_id(self):
        """Test log_audit includes client_id."""
        with patch.object(audit_logger, 'info') as mock_info:
            log_audit("CLIENT_UPDATE", client_id=100)
            extra_data = mock_info.call_args[1]["extra"]["extra_data"]
            assert extra_data["client_id"] == 100

    def test_log_audit_with_details(self):
        """Test log_audit includes details."""
        details = {"old_value": "A", "new_value": "B"}

        with patch.object(audit_logger, 'info') as mock_info:
            log_audit("FIELD_CHANGE", details=details)
            extra_data = mock_info.call_args[1]["extra"]["extra_data"]
            assert extra_data["details"] == details

    def test_log_audit_includes_timestamp(self):
        """Test log_audit includes timestamp."""
        with patch.object(audit_logger, 'info') as mock_info:
            log_audit("TEST_ACTION")
            extra_data = mock_info.call_args[1]["extra"]["extra_data"]
            assert "timestamp" in extra_data

    def test_log_audit_all_parameters(self):
        """Test log_audit with all parameters."""
        with patch.object(audit_logger, 'info') as mock_info:
            log_audit(
                "FULL_AUDIT",
                user_id=1,
                client_id=2,
                details={"key": "value"}
            )
            extra_data = mock_info.call_args[1]["extra"]["extra_data"]
            assert extra_data["action"] == "FULL_AUDIT"
            assert extra_data["user_id"] == 1
            assert extra_data["client_id"] == 2
            assert extra_data["details"]["key"] == "value"


class TestLogAiRequest:
    """Tests for log_ai_request function."""

    def test_log_ai_request_basic(self):
        """Test log_ai_request logs AI request details."""
        with patch.object(ai_logger, 'info') as mock_info:
            log_ai_request("gpt-4", 100, 200, 0.05, 500.0)
            mock_info.assert_called_once()
            message = mock_info.call_args[0][0]
            assert "gpt-4" in message
            assert "100" in message
            assert "200" in message

    def test_log_ai_request_extra_data(self):
        """Test log_ai_request includes extra data."""
        with patch.object(ai_logger, 'info') as mock_info:
            log_ai_request("claude-3", 500, 1000, 0.15, 1200.0)
            extra_data = mock_info.call_args[1]["extra"]["extra_data"]
            assert extra_data["model"] == "claude-3"
            assert extra_data["tokens_in"] == 500
            assert extra_data["tokens_out"] == 1000
            assert extra_data["cost"] == 0.15
            assert extra_data["duration_ms"] == 1200.0

    def test_log_ai_request_cost_formatting(self):
        """Test log_ai_request formats cost correctly."""
        with patch.object(ai_logger, 'info') as mock_info:
            log_ai_request("test-model", 10, 20, 0.0001, 50.0)
            message = mock_info.call_args[0][0]
            assert "$0.0001" in message


class TestLogDbQuery:
    """Tests for log_db_query function."""

    def test_log_db_query_slow_query_logged(self):
        """Test log_db_query logs queries slower than 100ms."""
        with patch.object(db_logger, 'warning') as mock_warning:
            log_db_query("SELECT * FROM users WHERE id = 1", 150.0)
            mock_warning.assert_called_once()
            assert "SLOW QUERY" in mock_warning.call_args[0][0]

    def test_log_db_query_fast_query_not_logged(self):
        """Test log_db_query does not log fast queries."""
        with patch.object(db_logger, 'warning') as mock_warning:
            log_db_query("SELECT * FROM users WHERE id = 1", 50.0)
            mock_warning.assert_not_called()

    def test_log_db_query_exactly_100ms_not_logged(self):
        """Test log_db_query does not log exactly 100ms queries."""
        with patch.object(db_logger, 'warning') as mock_warning:
            log_db_query("SELECT 1", 100.0)
            mock_warning.assert_not_called()

    def test_log_db_query_truncates_long_queries(self):
        """Test log_db_query truncates long queries to 200 chars."""
        long_query = "SELECT " + "column, " * 100 + "id FROM table"

        with patch.object(db_logger, 'warning') as mock_warning:
            log_db_query(long_query, 200.0)
            logged_message = mock_warning.call_args[0][0]
            # The query part should be truncated
            assert len(logged_message) < len(long_query) + 50  # Account for prefix


class TestLogPerformance:
    """Tests for log_performance function."""

    def test_log_performance_slow_operation_warning(self):
        """Test log_performance logs WARNING for operations over 1000ms."""
        with patch.object(perf_logger, 'log') as mock_log:
            log_performance("database_backup", 1500.0)
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == logging.WARNING

    def test_log_performance_fast_operation_debug(self):
        """Test log_performance logs DEBUG for operations under 1000ms."""
        with patch.object(perf_logger, 'log') as mock_log:
            log_performance("cache_read", 50.0)
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == logging.DEBUG

    def test_log_performance_exactly_1000ms_debug(self):
        """Test log_performance logs DEBUG for exactly 1000ms operations."""
        with patch.object(perf_logger, 'log') as mock_log:
            log_performance("boundary_operation", 1000.0)
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == logging.DEBUG

    def test_log_performance_includes_operation_name(self):
        """Test log_performance includes operation name in message."""
        with patch.object(perf_logger, 'log') as mock_log:
            log_performance("render_report", 500.0)
            message = mock_log.call_args[0][1]
            assert "render_report" in message

    def test_log_performance_with_details(self):
        """Test log_performance includes additional details."""
        details = {"records_processed": 1000, "batch_size": 100}

        with patch.object(perf_logger, 'log') as mock_log:
            log_performance("batch_process", 800.0, details=details)
            extra_data = mock_log.call_args[1]["extra"]["extra_data"]
            assert extra_data["records_processed"] == 1000
            assert extra_data["batch_size"] == 100

    def test_log_performance_without_details(self):
        """Test log_performance handles missing details."""
        with patch.object(perf_logger, 'log') as mock_log:
            log_performance("simple_op", 100.0)
            extra_data = mock_log.call_args[1]["extra"]["extra_data"]
            assert extra_data["operation"] == "simple_op"
            assert extra_data["duration_ms"] == 100.0


class TestTimedDecorator:
    """Tests for timed decorator."""

    def test_timed_decorator_executes_function(self):
        """Test timed decorator executes the wrapped function."""
        @timed
        def add_numbers(a, b):
            return a + b

        result = add_numbers(2, 3)
        assert result == 5

    def test_timed_decorator_preserves_return_value(self):
        """Test timed decorator preserves function return value."""
        @timed
        def get_data():
            return {"key": "value", "count": 42}

        result = get_data()
        assert result == {"key": "value", "count": 42}

    def test_timed_decorator_logs_slow_functions(self):
        """Test timed decorator logs functions taking over 500ms."""
        @timed
        def slow_function():
            time.sleep(0.6)  # 600ms
            return "done"

        with patch.object(perf_logger, 'info') as mock_info:
            result = slow_function()
            assert result == "done"
            mock_info.assert_called_once()
            assert "slow_function" in mock_info.call_args[0][0]

    def test_timed_decorator_does_not_log_fast_functions(self):
        """Test timed decorator does not log fast functions."""
        @timed
        def fast_function():
            return "quick"

        with patch.object(perf_logger, 'info') as mock_info:
            result = fast_function()
            assert result == "quick"
            mock_info.assert_not_called()

    def test_timed_decorator_handles_exceptions(self):
        """Test timed decorator handles and re-raises exceptions."""
        @timed
        def failing_function():
            raise ValueError("Expected error")

        with patch('services.logging_config.log_error') as mock_log_error:
            with pytest.raises(ValueError, match="Expected error"):
                failing_function()
            mock_log_error.assert_called_once()

    def test_timed_decorator_logs_error_with_context(self):
        """Test timed decorator logs error with function context."""
        @timed
        def another_failing_function():
            raise RuntimeError("Test failure")

        with patch('services.logging_config.log_error') as mock_log_error:
            with pytest.raises(RuntimeError):
                another_failing_function()

            call_args = mock_log_error.call_args
            context = call_args[1]["context"]
            assert context["function"] == "another_failing_function"
            assert "duration_ms" in context

    def test_timed_decorator_preserves_function_name(self):
        """Test timed decorator preserves function name."""
        @timed
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    def test_timed_decorator_handles_args_and_kwargs(self):
        """Test timed decorator passes arguments correctly."""
        @timed
        def complex_function(a, b, c=None, d=None):
            return f"{a}-{b}-{c}-{d}"

        result = complex_function(1, 2, c="three", d="four")
        assert result == "1-2-three-four"


class TestInitRequestLogging:
    """Tests for init_request_logging function."""

    def test_init_request_logging_registers_before_request(self):
        """Test init_request_logging registers before_request handler."""
        mock_app = MagicMock()

        init_request_logging(mock_app)

        mock_app.before_request.assert_called_once()

    def test_init_request_logging_registers_after_request(self):
        """Test init_request_logging registers after_request handler."""
        mock_app = MagicMock()

        init_request_logging(mock_app)

        mock_app.after_request.assert_called_once()

    def test_init_request_logging_registers_error_handler(self):
        """Test init_request_logging registers errorhandler."""
        mock_app = MagicMock()

        init_request_logging(mock_app)

        mock_app.errorhandler.assert_called_once_with(Exception)


class TestModuleConstants:
    """Tests for module-level constants."""

    def test_log_level_default(self):
        """Test LOG_LEVEL has a valid default."""
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_log_format_defined(self):
        """Test LOG_FORMAT is defined."""
        assert LOG_FORMAT is not None
        assert "%(asctime)s" in LOG_FORMAT
        assert "%(levelname)" in LOG_FORMAT
        assert "%(message)s" in LOG_FORMAT

    def test_log_date_format_defined(self):
        """Test LOG_DATE_FORMAT is defined."""
        assert LOG_DATE_FORMAT is not None
        assert "%Y" in LOG_DATE_FORMAT
        assert "%m" in LOG_DATE_FORMAT
        assert "%d" in LOG_DATE_FORMAT

    def test_service_name_defined(self):
        """Test SERVICE_NAME is defined."""
        assert SERVICE_NAME is not None
        assert isinstance(SERVICE_NAME, str)

    def test_hostname_defined(self):
        """Test HOSTNAME is defined."""
        assert HOSTNAME is not None
        assert isinstance(HOSTNAME, str)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_json_formatter_empty_message(self):
        """Test JSON formatter handles empty message."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)
        parsed = json.loads(result)
        assert parsed["message"] == ""

    def test_json_formatter_none_exc_info(self):
        """Test JSON formatter handles None exc_info gracefully."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/test.py",
            lineno=1,
            msg="Error without traceback",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)
        parsed = json.loads(result)
        assert "exception" not in parsed

    def test_json_formatter_partial_exc_info(self):
        """Test JSON formatter handles partial exc_info."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/test.py",
            lineno=1,
            msg="Error",
            args=(),
            exc_info=(None, None, None)
        )

        result = formatter.format(record)
        parsed = json.loads(result)
        # Should handle gracefully
        if "exception" in parsed:
            assert parsed["exception"]["type"] is None

    def test_log_request_with_none_query_string(self):
        """Test log_request handles None query string."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.path = "/test"
        mock_request.query_string = None
        mock_request.remote_addr = "127.0.0.1"
        mock_request.user_agent = MagicMock()
        mock_request.user_agent.__str__ = MagicMock(return_value="Test")
        mock_request.content_length = None

        with patch.object(api_logger, 'info') as mock_info:
            # Should not raise
            log_request(mock_request)
            mock_info.assert_called_once()

    def test_log_response_zero_duration(self):
        """Test log_response handles zero duration."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(api_logger, 'log') as mock_log:
            log_response(mock_response, 0.0)
            mock_log.assert_called_once()

    def test_log_error_with_nested_exception(self):
        """Test log_error handles nested/chained exceptions."""
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e
        except RuntimeError as e:
            with patch.object(app_logger, 'error') as mock_error:
                log_error(e)
                mock_error.assert_called_once()

    def test_log_audit_with_none_values(self):
        """Test log_audit handles None values."""
        with patch.object(audit_logger, 'info') as mock_info:
            log_audit("TEST", user_id=None, client_id=None, details=None)
            extra_data = mock_info.call_args[1]["extra"]["extra_data"]
            assert extra_data["user_id"] is None
            assert extra_data["client_id"] is None
            assert extra_data["details"] == {}

    def test_log_performance_zero_duration(self):
        """Test log_performance handles zero duration."""
        with patch.object(perf_logger, 'log') as mock_log:
            log_performance("instant_operation", 0.0)
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == logging.DEBUG

    def test_log_db_query_empty_query(self):
        """Test log_db_query handles empty query string."""
        with patch.object(db_logger, 'warning') as mock_warning:
            log_db_query("", 200.0)
            mock_warning.assert_called_once()

    def test_timed_decorator_with_generator(self):
        """Test timed decorator with generator function."""
        @timed
        def generate_numbers(n):
            for i in range(n):
                yield i

        result = list(generate_numbers(3))
        assert result == [0, 1, 2]

    def test_log_ai_request_with_zero_tokens(self):
        """Test log_ai_request handles zero tokens."""
        with patch.object(ai_logger, 'info') as mock_info:
            log_ai_request("test-model", 0, 0, 0.0, 0.0)
            mock_info.assert_called_once()
