"""
Unit tests for Activity Logger Service

Tests cover:
- log_activity function
- get_recent_activities filtering
- get_activities_from_file disk reading
- read_error_log and read_app_log
- @logged decorator
- Pre-built logging helpers
"""

import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, mock_open


class TestConstants:
    """Tests for module constants"""

    def test_max_activities(self):
        """Should have MAX_ACTIVITIES constant"""
        from services.activity_logger import MAX_ACTIVITIES

        assert MAX_ACTIVITIES == 500

    def test_activity_log_file(self):
        """Should have ACTIVITY_LOG_FILE constant"""
        from services.activity_logger import ACTIVITY_LOG_FILE

        assert ACTIVITY_LOG_FILE == "logs/activity.log"

    def test_recent_activities_is_list(self):
        """Should have RECENT_ACTIVITIES as list"""
        from services.activity_logger import RECENT_ACTIVITIES

        assert isinstance(RECENT_ACTIVITIES, list)


class TestLogActivity:
    """Tests for log_activity function"""

    def test_returns_activity_dict(self):
        """Should return activity dictionary"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        # Clear existing activities
        RECENT_ACTIVITIES.clear()

        result = log_activity("Test Action")

        assert isinstance(result, dict)
        assert "time" in result
        assert "action" in result
        assert result["action"] == "Test Action"

    def test_adds_to_recent_activities(self):
        """Should add to RECENT_ACTIVITIES list"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_activity("Test Action 1")
        log_activity("Test Action 2")

        assert len(RECENT_ACTIVITIES) >= 2

    def test_adds_at_front(self):
        """Should add new activities at front (most recent first)"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_activity("First")
        log_activity("Second")

        assert RECENT_ACTIVITIES[0]["action"] == "Second"
        assert RECENT_ACTIVITIES[1]["action"] == "First"

    def test_respects_max_activities(self):
        """Should keep only MAX_ACTIVITIES entries"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES, MAX_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        # Add more than MAX_ACTIVITIES
        for i in range(MAX_ACTIVITIES + 10):
            log_activity(f"Action {i}")

        assert len(RECENT_ACTIVITIES) == MAX_ACTIVITIES

    def test_includes_details(self):
        """Should include details when provided"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        result = log_activity("Test Action", details="Some details")

        assert result["details"] == "Some details"

    def test_includes_user(self):
        """Should include user when provided"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        result = log_activity("Test Action", user="test@example.com")

        assert result["user"] == "test@example.com"

    def test_includes_client_id(self):
        """Should include client_id when provided"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        result = log_activity("Test Action", client_id=123)

        assert result["client_id"] == 123

    def test_includes_status(self):
        """Should include status with default 'success'"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        result = log_activity("Test Action")

        assert result["status"] == "success"

    def test_custom_status(self):
        """Should allow custom status"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        result = log_activity("Test Action", status="error")

        assert result["status"] == "error"

    def test_includes_error(self):
        """Should include error when provided"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        result = log_activity("Test Action", error="Something went wrong")

        assert result["error"] == "Something went wrong"

    def test_time_format(self):
        """Should format time as YYYY-MM-DD HH:MM:SS"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        result = log_activity("Test Action")

        # Check format matches expected pattern
        time_str = result["time"]
        assert len(time_str) == 19  # "2024-01-15 10:30:45"
        assert time_str[4] == "-"
        assert time_str[7] == "-"
        assert time_str[10] == " "
        assert time_str[13] == ":"
        assert time_str[16] == ":"

    @patch('os.makedirs')
    def test_writes_to_file(self, mock_makedirs):
        """Should write to log file"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES, ACTIVITY_LOG_FILE

        RECENT_ACTIVITIES.clear()

        m = mock_open()
        with patch('builtins.open', m):
            log_activity("Test Action", details="Details")

        # Verify open was called with the log file path
        m.assert_called_with(ACTIVITY_LOG_FILE, "a")

    @patch('os.makedirs')
    def test_creates_logs_directory(self, mock_makedirs):
        """Should create logs directory if needed"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        with patch('builtins.open', mock_open()):
            log_activity("Test Action")

            mock_makedirs.assert_called_with("logs", exist_ok=True)

    @patch('os.makedirs', side_effect=Exception("Permission denied"))
    def test_handles_write_error(self, mock_makedirs):
        """Should handle file write errors gracefully"""
        from services.activity_logger import log_activity, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        # Should not raise exception
        result = log_activity("Test Action")

        assert result is not None
        assert result["action"] == "Test Action"


class TestGetRecentActivities:
    """Tests for get_recent_activities function"""

    def test_returns_list(self):
        """Should return a list"""
        from services.activity_logger import get_recent_activities, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        result = get_recent_activities()

        assert isinstance(result, list)

    def test_respects_limit(self):
        """Should respect limit parameter"""
        from services.activity_logger import log_activity, get_recent_activities, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        for i in range(10):
            log_activity(f"Action {i}")

        result = get_recent_activities(limit=5)

        assert len(result) == 5

    def test_filters_by_status(self):
        """Should filter by status"""
        from services.activity_logger import log_activity, get_recent_activities, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_activity("Success Action", status="success")
        log_activity("Error Action", status="error")
        log_activity("Another Success", status="success")

        result = get_recent_activities(status_filter="error")

        assert len(result) == 1
        assert result[0]["action"] == "Error Action"

    def test_filters_by_action(self):
        """Should filter by action substring"""
        from services.activity_logger import log_activity, get_recent_activities, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_activity("Email Sent")
        log_activity("SMS Sent")
        log_activity("Email Failed")

        result = get_recent_activities(action_filter="email")

        assert len(result) == 2

    def test_action_filter_case_insensitive(self):
        """Should filter action case-insensitively"""
        from services.activity_logger import log_activity, get_recent_activities, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_activity("EMAIL Sent")
        log_activity("email sent")

        result = get_recent_activities(action_filter="EMAIL")

        assert len(result) == 2

    def test_combines_filters(self):
        """Should combine status and action filters"""
        from services.activity_logger import log_activity, get_recent_activities, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_activity("Email Sent", status="success")
        log_activity("Email Failed", status="error")
        log_activity("SMS Sent", status="success")

        result = get_recent_activities(status_filter="success", action_filter="email")

        assert len(result) == 1
        assert result[0]["action"] == "Email Sent"


class TestGetActivitiesFromFile:
    """Tests for get_activities_from_file function"""

    def test_returns_list(self):
        """Should return a list"""
        from services.activity_logger import get_activities_from_file

        with patch('os.path.exists', return_value=False):
            result = get_activities_from_file()

        assert isinstance(result, list)

    def test_returns_empty_for_nonexistent_file(self):
        """Should return empty list if file doesn't exist"""
        from services.activity_logger import get_activities_from_file

        with patch('os.path.exists', return_value=False):
            result = get_activities_from_file()

        assert result == []

    def test_reads_lines_from_file(self):
        """Should read lines from log file"""
        from services.activity_logger import get_activities_from_file

        log_content = "[2024-01-15 10:30:00] Test Action\n[2024-01-15 10:31:00] Another Action\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=log_content)):
                result = get_activities_from_file()

        assert len(result) == 2

    def test_respects_limit(self):
        """Should respect limit parameter"""
        from services.activity_logger import get_activities_from_file

        lines = "\n".join([f"[2024-01-15 10:30:{i:02d}] Action {i}" for i in range(20)])

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=lines)):
                result = get_activities_from_file(limit=5)

        assert len(result) == 5

    def test_returns_most_recent_first(self):
        """Should return activities in reverse order (most recent first)"""
        from services.activity_logger import get_activities_from_file

        log_content = "First\nSecond\nThird\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=log_content)):
                result = get_activities_from_file()

        assert "Third" in result[0]["raw"]

    def test_filters_by_search(self):
        """Should filter by search string"""
        from services.activity_logger import get_activities_from_file

        log_content = "Email Sent\nSMS Sent\nEmail Failed\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=log_content)):
                result = get_activities_from_file(search="email")

        assert len(result) == 2

    def test_search_case_insensitive(self):
        """Should search case-insensitively"""
        from services.activity_logger import get_activities_from_file

        log_content = "EMAIL Sent\nemail sent\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=log_content)):
                result = get_activities_from_file(search="EMAIL")

        assert len(result) == 2

    def test_handles_read_error(self):
        """Should handle read errors gracefully"""
        from services.activity_logger import get_activities_from_file

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=Exception("Read error")):
                result = get_activities_from_file()

        assert len(result) == 1
        assert "Error reading log" in result[0]["raw"]

    def test_skips_empty_lines(self):
        """Should skip empty lines"""
        from services.activity_logger import get_activities_from_file

        log_content = "Line 1\n\nLine 2\n\n\nLine 3\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=log_content)):
                result = get_activities_from_file()

        assert len(result) == 3


class TestReadErrorLog:
    """Tests for read_error_log function"""

    def test_returns_list(self):
        """Should return a list"""
        from services.activity_logger import read_error_log

        with patch('os.path.exists', return_value=False):
            result = read_error_log()

        assert isinstance(result, list)

    def test_returns_empty_for_nonexistent_file(self):
        """Should return empty list if file doesn't exist"""
        from services.activity_logger import read_error_log

        with patch('os.path.exists', return_value=False):
            result = read_error_log()

        assert result == []

    def test_reads_error_log(self):
        """Should read from logs/error.log"""
        from services.activity_logger import read_error_log

        log_content = "Error 1\nError 2\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=log_content)):
                result = read_error_log()

        assert len(result) == 2

    def test_respects_limit(self):
        """Should respect limit parameter"""
        from services.activity_logger import read_error_log

        lines = "\n".join([f"Error {i}" for i in range(20)])

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=lines)):
                result = read_error_log(limit=5)

        assert len(result) == 5

    def test_returns_most_recent_first(self):
        """Should return errors in reverse order"""
        from services.activity_logger import read_error_log

        log_content = "First error\nSecond error\nThird error\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=log_content)):
                result = read_error_log()

        assert result[0] == "Third error"

    def test_handles_read_error(self):
        """Should handle read errors gracefully"""
        from services.activity_logger import read_error_log

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=Exception("Read error")):
                result = read_error_log()

        assert len(result) == 1
        assert "Error reading error log" in result[0]


class TestReadAppLog:
    """Tests for read_app_log function"""

    def test_returns_list(self):
        """Should return a list"""
        from services.activity_logger import read_app_log

        with patch('os.path.exists', return_value=False):
            result = read_app_log()

        assert isinstance(result, list)

    def test_returns_empty_for_nonexistent_file(self):
        """Should return empty list if file doesn't exist"""
        from services.activity_logger import read_app_log

        with patch('os.path.exists', return_value=False):
            result = read_app_log()

        assert result == []

    def test_reads_app_log(self):
        """Should read from logs/app.log"""
        from services.activity_logger import read_app_log

        log_content = "Entry 1\nEntry 2\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=log_content)):
                result = read_app_log()

        assert len(result) == 2

    def test_respects_limit(self):
        """Should respect limit parameter"""
        from services.activity_logger import read_app_log

        lines = "\n".join([f"Entry {i}" for i in range(20)])

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=lines)):
                result = read_app_log(limit=5)

        assert len(result) == 5

    def test_handles_read_error(self):
        """Should handle read errors gracefully"""
        from services.activity_logger import read_app_log

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=Exception("Read error")):
                result = read_app_log()

        assert len(result) == 1
        assert "Error reading app log" in result[0]


class TestLoggedDecorator:
    """Tests for @logged decorator"""

    def test_logs_successful_call(self):
        """Should log successful function calls"""
        from services.activity_logger import logged, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        @logged("Test Function")
        def test_func():
            return "result"

        result = test_func()

        assert result == "result"
        assert len(RECENT_ACTIVITIES) >= 1
        assert RECENT_ACTIVITIES[0]["action"] == "Test Function"
        assert RECENT_ACTIVITIES[0]["status"] == "success"

    def test_logs_with_duration(self):
        """Should include duration in details"""
        from services.activity_logger import logged, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        @logged("Test Function")
        def test_func():
            return "result"

        test_func()

        assert "completed in" in RECENT_ACTIVITIES[0]["details"]
        assert "ms" in RECENT_ACTIVITIES[0]["details"]

    def test_logs_failed_call(self):
        """Should log failed function calls"""
        from services.activity_logger import logged, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        @logged("Failing Function")
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_func()

        assert len(RECENT_ACTIVITIES) >= 1
        assert RECENT_ACTIVITIES[0]["action"] == "Failing Function"
        assert RECENT_ACTIVITIES[0]["status"] == "error"
        assert "Test error" in RECENT_ACTIVITIES[0]["error"]

    def test_re_raises_exception(self):
        """Should re-raise exceptions after logging"""
        from services.activity_logger import logged

        @logged("Failing Function")
        def failing_func():
            raise RuntimeError("Original error")

        with pytest.raises(RuntimeError) as exc_info:
            failing_func()

        assert "Original error" in str(exc_info.value)

    def test_uses_function_name_as_default(self):
        """Should use function name if action_name not provided"""
        from services.activity_logger import logged, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        @logged()
        def my_function_name():
            return "result"

        my_function_name()

        assert RECENT_ACTIVITIES[0]["action"] == "my_function_name"

    def test_preserves_function_metadata(self):
        """Should preserve function name and docstring"""
        from services.activity_logger import logged

        @logged("Test")
        def documented_function():
            """This is the docstring."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is the docstring."

    def test_passes_args_and_kwargs(self):
        """Should pass arguments to wrapped function"""
        from services.activity_logger import logged

        @logged("Test")
        def func_with_args(a, b, c=None):
            return (a, b, c)

        result = func_with_args(1, 2, c=3)

        assert result == (1, 2, 3)


class TestLogEmailSent:
    """Tests for log_email_sent helper"""

    def test_logs_email_sent(self):
        """Should log email sent activity"""
        from services.activity_logger import log_email_sent, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_email_sent("test@example.com", "Test Subject")

        assert RECENT_ACTIVITIES[0]["action"] == "Email Sent"
        assert "test@example.com" in RECENT_ACTIVITIES[0]["details"]
        assert "Test Subject" in RECENT_ACTIVITIES[0]["details"]

    def test_includes_user(self):
        """Should include user when provided"""
        from services.activity_logger import log_email_sent, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_email_sent("to@example.com", "Subject", user="from@example.com")

        assert RECENT_ACTIVITIES[0]["user"] == "from@example.com"


class TestLogEmailFailed:
    """Tests for log_email_failed helper"""

    def test_logs_email_failed(self):
        """Should log email failure"""
        from services.activity_logger import log_email_failed, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_email_failed("test@example.com", "SMTP error")

        assert RECENT_ACTIVITIES[0]["action"] == "Email Failed"
        assert RECENT_ACTIVITIES[0]["status"] == "error"
        assert RECENT_ACTIVITIES[0]["error"] == "SMTP error"


class TestLogSmsSent:
    """Tests for log_sms_sent helper"""

    def test_logs_sms_sent(self):
        """Should log SMS sent activity"""
        from services.activity_logger import log_sms_sent, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_sms_sent("+1234567890")

        assert RECENT_ACTIVITIES[0]["action"] == "SMS Sent"
        assert "+1234567890" in RECENT_ACTIVITIES[0]["details"]


class TestLogSmsFailed:
    """Tests for log_sms_failed helper"""

    def test_logs_sms_failed(self):
        """Should log SMS failure"""
        from services.activity_logger import log_sms_failed, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_sms_failed("+1234567890", "Twilio error")

        assert RECENT_ACTIVITIES[0]["action"] == "SMS Failed"
        assert RECENT_ACTIVITIES[0]["status"] == "error"
        assert RECENT_ACTIVITIES[0]["error"] == "Twilio error"


class TestLogPaymentSuccess:
    """Tests for log_payment_success helper"""

    def test_logs_payment_success(self):
        """Should log successful payment"""
        from services.activity_logger import log_payment_success, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_payment_success(client_id=123, amount=199.99, method="stripe")

        assert RECENT_ACTIVITIES[0]["action"] == "Payment Received"
        assert "$199.99" in RECENT_ACTIVITIES[0]["details"]
        assert "stripe" in RECENT_ACTIVITIES[0]["details"]
        assert RECENT_ACTIVITIES[0]["client_id"] == 123


class TestLogPaymentFailed:
    """Tests for log_payment_failed helper"""

    def test_logs_payment_failed(self):
        """Should log failed payment"""
        from services.activity_logger import log_payment_failed, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_payment_failed(client_id=123, amount=199.99, error="Card declined")

        assert RECENT_ACTIVITIES[0]["action"] == "Payment Failed"
        assert RECENT_ACTIVITIES[0]["status"] == "error"
        assert RECENT_ACTIVITIES[0]["error"] == "Card declined"


class TestLogLogin:
    """Tests for log_login helper"""

    def test_logs_login(self):
        """Should log user login"""
        from services.activity_logger import log_login, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_login("test@example.com")

        assert RECENT_ACTIVITIES[0]["action"] == "User Login"
        assert "staff" in RECENT_ACTIVITIES[0]["details"]

    def test_logs_portal_login(self):
        """Should log portal-specific login"""
        from services.activity_logger import log_login, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_login("test@example.com", portal="client")

        assert "client" in RECENT_ACTIVITIES[0]["details"]


class TestLogLoginFailed:
    """Tests for log_login_failed helper"""

    def test_logs_failed_login(self):
        """Should log failed login attempt"""
        from services.activity_logger import log_login_failed, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_login_failed("test@example.com", "Invalid password")

        assert RECENT_ACTIVITIES[0]["action"] == "Login Failed"
        assert RECENT_ACTIVITIES[0]["status"] == "warning"
        assert RECENT_ACTIVITIES[0]["details"] == "Invalid password"


class TestLogClientCreated:
    """Tests for log_client_created helper"""

    def test_logs_client_created(self):
        """Should log new client creation"""
        from services.activity_logger import log_client_created, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_client_created(client_id=123, name="John Doe")

        assert RECENT_ACTIVITIES[0]["action"] == "Client Created"
        assert RECENT_ACTIVITIES[0]["details"] == "John Doe"
        assert RECENT_ACTIVITIES[0]["client_id"] == 123


class TestLogDisputeGenerated:
    """Tests for log_dispute_generated helper"""

    def test_logs_dispute_generated(self):
        """Should log dispute letter generation"""
        from services.activity_logger import log_dispute_generated, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_dispute_generated(client_id=123, round_num=2, letter_count=5)

        assert RECENT_ACTIVITIES[0]["action"] == "Disputes Generated"
        assert "Round 2" in RECENT_ACTIVITIES[0]["details"]
        assert "5 letters" in RECENT_ACTIVITIES[0]["details"]
        assert RECENT_ACTIVITIES[0]["client_id"] == 123


class TestLogCreditImport:
    """Tests for log_credit_import helper"""

    def test_logs_credit_import(self):
        """Should log credit report import"""
        from services.activity_logger import log_credit_import, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_credit_import(client_id=123, service="MyFreeScoreNow")

        assert RECENT_ACTIVITIES[0]["action"] == "Credit Report Imported"
        assert "MyFreeScoreNow" in RECENT_ACTIVITIES[0]["details"]

    def test_logs_with_scores(self):
        """Should include scores when provided"""
        from services.activity_logger import log_credit_import, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        scores = {"transunion": 650, "experian": 680, "equifax": 670}
        log_credit_import(client_id=123, service="MyFreeScoreNow", scores=scores)

        details = RECENT_ACTIVITIES[0]["details"]
        assert "TU:650" in details
        assert "EX:680" in details
        assert "EQ:670" in details

    def test_handles_partial_scores(self):
        """Should handle partial score data"""
        from services.activity_logger import log_credit_import, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        scores = {"transunion": 650}  # Only one score
        log_credit_import(client_id=123, service="Test", scores=scores)

        details = RECENT_ACTIVITIES[0]["details"]
        assert "TU:650" in details
        assert "EX:?" in details


class TestLogCreditImportFailed:
    """Tests for log_credit_import_failed helper"""

    def test_logs_credit_import_failed(self):
        """Should log failed credit import"""
        from services.activity_logger import log_credit_import_failed, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_credit_import_failed(client_id=123, service="MyFreeScoreNow", error="Login failed")

        assert RECENT_ACTIVITIES[0]["action"] == "Credit Import Failed"
        assert RECENT_ACTIVITIES[0]["status"] == "error"
        assert RECENT_ACTIVITIES[0]["error"] == "Login failed"


class TestLogDocumentUploaded:
    """Tests for log_document_uploaded helper"""

    def test_logs_document_uploaded(self):
        """Should log document upload"""
        from services.activity_logger import log_document_uploaded, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_document_uploaded(client_id=123, doc_type="ID", filename="license.jpg")

        assert RECENT_ACTIVITIES[0]["action"] == "Document Uploaded"
        assert "ID" in RECENT_ACTIVITIES[0]["details"]
        assert "license.jpg" in RECENT_ACTIVITIES[0]["details"]
        assert RECENT_ACTIVITIES[0]["client_id"] == 123


class TestLogApiCall:
    """Tests for log_api_call helper"""

    def test_logs_successful_api_call(self):
        """Should log successful API call"""
        from services.activity_logger import log_api_call, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_api_call(service="Stripe", endpoint="/charges", status_code=200, duration_ms=150.5)

        assert RECENT_ACTIVITIES[0]["action"] == "API Call: Stripe"
        assert "/charges" in RECENT_ACTIVITIES[0]["details"]
        assert "200" in RECENT_ACTIVITIES[0]["details"]
        assert "150ms" in RECENT_ACTIVITIES[0]["details"]
        assert RECENT_ACTIVITIES[0]["status"] == "success"

    def test_logs_failed_api_call(self):
        """Should log failed API call as error"""
        from services.activity_logger import log_api_call, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_api_call(service="Twilio", endpoint="/sms", status_code=500, duration_ms=250)

        assert RECENT_ACTIVITIES[0]["status"] == "error"

    def test_logs_4xx_as_error(self):
        """Should log 4xx status codes as error"""
        from services.activity_logger import log_api_call, RECENT_ACTIVITIES

        RECENT_ACTIVITIES.clear()

        log_api_call(service="API", endpoint="/test", status_code=400, duration_ms=100)

        assert RECENT_ACTIVITIES[0]["status"] == "error"
