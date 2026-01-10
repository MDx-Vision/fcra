"""
Comprehensive unit tests for services/sms_automation.py
Tests SMS automation triggers, settings, logging, and client helpers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sms_automation import (
    get_sms_settings,
    log_sms,
    get_client_phone,
    trigger_welcome_sms,
    trigger_document_reminder,
    trigger_case_update,
    trigger_dispute_sent,
    trigger_cra_response,
    trigger_payment_reminder,
    trigger_analysis_ready,
    trigger_letters_ready,
    trigger_round_started,
    send_custom_sms,
    send_test_sms,
    get_clients_needing_document_reminder,
    get_clients_needing_payment_reminder,
)


# ============== Fixtures ==============


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def mock_client():
    """Create a mock client object."""
    client = Mock()
    client.id = 1
    client.name = "John Doe"
    client.mobile = "+15551234567"
    client.phone = "+15559876543"
    client.phone_2 = "+15555555555"
    client.email = "john@example.com"
    client.signup_amount = 9900  # $99.00 in cents
    return client


@pytest.fixture
def mock_client_no_phone():
    """Create a mock client with no phone numbers."""
    client = Mock()
    client.id = 2
    client.name = "Jane Doe"
    client.mobile = None
    client.phone = None
    client.phone_2 = None
    client.email = "jane@example.com"
    return client


@pytest.fixture
def sms_enabled_settings():
    """Return settings with SMS enabled."""
    return {
        "sms_enabled": True,
        "welcome_sms_enabled": True,
        "document_reminder_enabled": True,
        "case_update_enabled": True,
        "dispute_sent_enabled": True,
        "cra_response_enabled": True,
        "payment_reminder_enabled": True,
        "reminder_delay_hours": 24,
    }


@pytest.fixture
def sms_disabled_settings():
    """Return settings with SMS disabled."""
    return {
        "sms_enabled": False,
        "welcome_sms_enabled": True,
        "document_reminder_enabled": True,
        "case_update_enabled": True,
        "dispute_sent_enabled": True,
        "cra_response_enabled": True,
        "payment_reminder_enabled": True,
        "reminder_delay_hours": 24,
    }


# ============== get_sms_settings Tests ==============


class TestGetSmsSettings:
    """Tests for get_sms_settings function."""

    def test_get_sms_settings_defaults(self, mock_db):
        """Test default SMS settings are returned when no settings exist."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        settings = get_sms_settings(mock_db)

        assert settings["sms_enabled"] is False
        assert settings["welcome_sms_enabled"] is True
        assert settings["document_reminder_enabled"] is True
        assert settings["case_update_enabled"] is True
        assert settings["dispute_sent_enabled"] is True
        assert settings["cra_response_enabled"] is True
        assert settings["payment_reminder_enabled"] is True
        assert settings["reminder_delay_hours"] == 24

    def test_get_sms_settings_from_database_true(self, mock_db):
        """Test boolean true settings are read from database."""
        mock_setting = Mock()
        mock_setting.setting_value = "true"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_setting

        settings = get_sms_settings(mock_db)

        assert settings["sms_enabled"] is True

    def test_get_sms_settings_from_database_false(self, mock_db):
        """Test boolean false settings are read from database."""
        mock_setting = Mock()
        mock_setting.setting_value = "false"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_setting

        settings = get_sms_settings(mock_db)

        assert settings["sms_enabled"] is False

    def test_get_sms_settings_int_parsing(self, mock_db):
        """Test integer setting parsing."""

        def mock_query(*args):
            mock_result = Mock()

            def mock_filter_by(**kwargs):
                filter_result = Mock()
                if kwargs.get("setting_key") == "sms_reminder_delay_hours":
                    setting = Mock()
                    setting.setting_value = "48"
                    filter_result.first.return_value = setting
                else:
                    filter_result.first.return_value = None
                return filter_result

            mock_result.filter_by = mock_filter_by
            return mock_result

        mock_db.query = mock_query
        settings = get_sms_settings(mock_db)
        assert settings["reminder_delay_hours"] == 48

    def test_get_sms_settings_exception_returns_default(self, mock_db):
        """Test that exceptions return default values."""
        mock_db.query.side_effect = Exception("Database error")

        settings = get_sms_settings(mock_db)

        # Should return defaults on error
        assert settings["sms_enabled"] is False
        assert settings["reminder_delay_hours"] == 24


# ============== log_sms Tests ==============


class TestLogSms:
    """Tests for log_sms function."""

    def test_log_sms_success(self, mock_db):
        """Test successful SMS logging."""
        log_sms(
            mock_db,
            client_id=1,
            phone_number="+15551234567",
            message="Test message",
            template_type="welcome",
            success=True,
            message_sid="SM123456789",
            error=None,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_log_sms_failed(self, mock_db):
        """Test logging failed SMS."""
        log_sms(
            mock_db,
            client_id=1,
            phone_number="+15551234567",
            message="Test message",
            template_type="welcome",
            success=False,
            message_sid=None,
            error="Twilio error",
        )

        mock_db.add.assert_called_once()
        added_log = mock_db.add.call_args[0][0]
        assert added_log.status == "failed"
        assert added_log.error_message == "Twilio error"

    def test_log_sms_truncates_long_message(self, mock_db):
        """Test that long messages are truncated to 1000 characters."""
        long_message = "A" * 2000

        log_sms(
            mock_db,
            client_id=1,
            phone_number="+15551234567",
            message=long_message,
            template_type="custom",
            success=True,
        )

        added_log = mock_db.add.call_args[0][0]
        assert len(added_log.message) == 1000

    def test_log_sms_handles_none_message(self, mock_db):
        """Test that None message is handled."""
        log_sms(
            mock_db,
            client_id=1,
            phone_number="+15551234567",
            message=None,
            template_type="welcome",
            success=True,
        )

        added_log = mock_db.add.call_args[0][0]
        assert added_log.message == ""

    def test_log_sms_database_error_rollback(self, mock_db):
        """Test that database errors trigger rollback."""
        mock_db.add.side_effect = Exception("Database error")

        # Should not raise exception
        log_sms(
            mock_db,
            client_id=1,
            phone_number="+15551234567",
            message="Test",
            template_type="welcome",
            success=True,
        )

        mock_db.rollback.assert_called_once()


# ============== get_client_phone Tests ==============


class TestGetClientPhone:
    """Tests for get_client_phone function."""

    def test_get_client_phone_uses_mobile_first(self, mock_db, mock_client):
        """Test that mobile is used as primary phone."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        phone, client = get_client_phone(mock_db, 1)

        assert phone == "+15551234567"
        assert client == mock_client

    def test_get_client_phone_falls_back_to_phone(self, mock_db, mock_client):
        """Test fallback to phone when mobile is None."""
        mock_client.mobile = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        phone, client = get_client_phone(mock_db, 1)

        assert phone == "+15559876543"

    def test_get_client_phone_falls_back_to_phone_2(self, mock_db, mock_client):
        """Test fallback to phone_2 when mobile and phone are None."""
        mock_client.mobile = None
        mock_client.phone = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        phone, client = get_client_phone(mock_db, 1)

        assert phone == "+15555555555"

    def test_get_client_phone_no_phone_numbers(self, mock_db, mock_client_no_phone):
        """Test when client has no phone numbers."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client_no_phone

        phone, client = get_client_phone(mock_db, 2)

        assert phone is None
        assert client == mock_client_no_phone

    def test_get_client_phone_client_not_found(self, mock_db):
        """Test when client is not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        phone, client = get_client_phone(mock_db, 999)

        assert phone is None
        assert client is None

    @patch("services.sms_automation.format_phone_number")
    def test_get_client_phone_formats_number(self, mock_format, mock_db, mock_client):
        """Test that phone number is formatted."""
        mock_client.mobile = "5551234567"  # Unformatted
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client
        mock_format.return_value = "+15551234567"

        phone, client = get_client_phone(mock_db, 1)

        mock_format.assert_called_once_with("5551234567")
        assert phone == "+15551234567"


# ============== trigger_welcome_sms Tests ==============


class TestTriggerWelcomeSms:
    """Tests for trigger_welcome_sms function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_welcome_sms_success(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test successful welcome SMS trigger."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM123"}

        result = trigger_welcome_sms(mock_db, 1)

        assert result["sent"] is True
        assert result["message_sid"] == "SM123"
        mock_send.assert_called_once()

    @patch("services.sms_automation.get_sms_settings")
    def test_trigger_welcome_sms_disabled(self, mock_settings, mock_db):
        """Test welcome SMS when SMS is disabled."""
        mock_settings.return_value = {
            "sms_enabled": False,
            "welcome_sms_enabled": True,
        }

        result = trigger_welcome_sms(mock_db, 1)

        assert result["sent"] is False
        assert "disabled" in result["reason"]

    @patch("services.sms_automation.get_sms_settings")
    def test_trigger_welcome_sms_type_disabled(self, mock_settings, mock_db):
        """Test welcome SMS when welcome type is disabled."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": False,
        }

        result = trigger_welcome_sms(mock_db, 1)

        assert result["sent"] is False
        assert "disabled" in result["reason"]

    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    def test_trigger_welcome_sms_twilio_not_configured(
        self, mock_settings, mock_configured, mock_db
    ):
        """Test welcome SMS when Twilio is not configured."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": True,
        }
        mock_configured.return_value = False

        result = trigger_welcome_sms(mock_db, 1)

        assert result["sent"] is False
        assert "Twilio not configured" in result["reason"]

    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_welcome_sms_no_phone(
        self, mock_get_phone, mock_settings, mock_configured, mock_db
    ):
        """Test welcome SMS when client has no phone."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = (None, Mock())

        result = trigger_welcome_sms(mock_db, 1)

        assert result["sent"] is False
        assert "No valid phone" in result["reason"]

    @patch("services.sms_automation.log_sms")
    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_welcome_sms_logs_result(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_log, mock_db, mock_client
    ):
        """Test that welcome SMS result is logged."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM123"}

        trigger_welcome_sms(mock_db, 1)

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[0][0] == mock_db
        assert call_args[0][1] == 1
        assert call_args[0][4] == "welcome"


# ============== trigger_document_reminder Tests ==============


class TestTriggerDocumentReminder:
    """Tests for trigger_document_reminder function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_document_reminder_success(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test successful document reminder SMS."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "document_reminder_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM456"}

        result = trigger_document_reminder(mock_db, 1, "Driver's License")

        assert result["sent"] is True
        mock_send.assert_called_once()

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_document_reminder_default_doc_type(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test document reminder with default doc type."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "document_reminder_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM456"}

        result = trigger_document_reminder(mock_db, 1)

        assert result["sent"] is True
        # Verify default doc type was used
        call_args = mock_send.call_args
        assert "required documents" in call_args[0][1]

    @patch("services.sms_automation.get_sms_settings")
    def test_trigger_document_reminder_disabled(self, mock_settings, mock_db):
        """Test document reminder when disabled."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "document_reminder_enabled": False,
        }

        result = trigger_document_reminder(mock_db, 1)

        assert result["sent"] is False


# ============== trigger_case_update Tests ==============


class TestTriggerCaseUpdate:
    """Tests for trigger_case_update function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_case_update_success(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test successful case update SMS."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM789"}

        result = trigger_case_update(mock_db, 1, "stage1_complete")

        assert result["sent"] is True
        mock_send.assert_called_once()

    @patch("services.sms_automation.get_sms_settings")
    def test_trigger_case_update_disabled(self, mock_settings, mock_db):
        """Test case update when disabled."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "case_update_enabled": False,
        }

        result = trigger_case_update(mock_db, 1, "stage1_complete")

        assert result["sent"] is False


# ============== trigger_dispute_sent Tests ==============


class TestTriggerDisputeSent:
    """Tests for trigger_dispute_sent function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_dispute_sent_success(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test successful dispute sent SMS."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "dispute_sent_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM001"}

        result = trigger_dispute_sent(mock_db, 1, "Equifax")

        assert result["sent"] is True
        call_args = mock_send.call_args
        assert "Equifax" in call_args[0][1]

    @patch("services.sms_automation.get_sms_settings")
    def test_trigger_dispute_sent_disabled(self, mock_settings, mock_db):
        """Test dispute sent when disabled."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "dispute_sent_enabled": False,
        }

        result = trigger_dispute_sent(mock_db, 1, "Equifax")

        assert result["sent"] is False


# ============== trigger_cra_response Tests ==============


class TestTriggerCraResponse:
    """Tests for trigger_cra_response function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_cra_response_success(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test successful CRA response SMS."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "cra_response_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM002"}

        result = trigger_cra_response(mock_db, 1, "Experian")

        assert result["sent"] is True
        call_args = mock_send.call_args
        assert "Experian" in call_args[0][1]

    @patch("services.sms_automation.get_sms_settings")
    def test_trigger_cra_response_disabled(self, mock_settings, mock_db):
        """Test CRA response when disabled."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "cra_response_enabled": False,
        }

        result = trigger_cra_response(mock_db, 1, "Experian")

        assert result["sent"] is False


# ============== trigger_payment_reminder Tests ==============


class TestTriggerPaymentReminder:
    """Tests for trigger_payment_reminder function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_payment_reminder_with_amount(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test payment reminder with specified amount."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "payment_reminder_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM003"}

        result = trigger_payment_reminder(mock_db, 1, amount=99.00)

        assert result["sent"] is True
        call_args = mock_send.call_args
        assert "$99.00" in call_args[0][1]

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_payment_reminder_from_client_signup_amount(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test payment reminder using client's signup amount."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "payment_reminder_enabled": True,
        }
        mock_configured.return_value = True
        mock_client.signup_amount = 9900  # $99.00 in cents
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM003"}

        result = trigger_payment_reminder(mock_db, 1)  # No amount specified

        assert result["sent"] is True
        call_args = mock_send.call_args
        assert "$99.00" in call_args[0][1]

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_payment_reminder_pending_amount(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test payment reminder with 'pending' amount when no amount available."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "payment_reminder_enabled": True,
        }
        mock_configured.return_value = True
        mock_client.signup_amount = None  # No signup amount
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM003"}

        result = trigger_payment_reminder(mock_db, 1)

        assert result["sent"] is True
        call_args = mock_send.call_args
        assert "pending" in call_args[0][1]

    @patch("services.sms_automation.get_sms_settings")
    def test_trigger_payment_reminder_disabled(self, mock_settings, mock_db):
        """Test payment reminder when disabled."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "payment_reminder_enabled": False,
        }

        result = trigger_payment_reminder(mock_db, 1)

        assert result["sent"] is False


# ============== trigger_analysis_ready Tests ==============


class TestTriggerAnalysisReady:
    """Tests for trigger_analysis_ready function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_analysis_ready_success(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test successful analysis ready SMS."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM004"}

        result = trigger_analysis_ready(mock_db, 1)

        assert result["sent"] is True
        call_args = mock_send.call_args
        assert "analysis" in call_args[0][1].lower()

    @patch("services.sms_automation.get_sms_settings")
    def test_trigger_analysis_ready_disabled(self, mock_settings, mock_db):
        """Test analysis ready when case_update is disabled."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "case_update_enabled": False,
        }

        result = trigger_analysis_ready(mock_db, 1)

        assert result["sent"] is False


# ============== trigger_letters_ready Tests ==============


class TestTriggerLettersReady:
    """Tests for trigger_letters_ready function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_letters_ready_success(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test successful letters ready SMS."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM005"}

        result = trigger_letters_ready(mock_db, 1, 3)

        assert result["sent"] is True
        call_args = mock_send.call_args
        assert "3" in call_args[0][1]

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_letters_ready_single_letter(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test letters ready with single letter."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM005"}

        result = trigger_letters_ready(mock_db, 1, 1)

        assert result["sent"] is True
        call_args = mock_send.call_args
        # Should use singular "letter is" instead of "letters are"
        assert "letter is" in call_args[0][1]


# ============== trigger_round_started Tests ==============


class TestTriggerRoundStarted:
    """Tests for trigger_round_started function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_round_started_success(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test successful round started SMS."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM006"}

        result = trigger_round_started(mock_db, 1, 2)

        assert result["sent"] is True
        call_args = mock_send.call_args
        # Round 2 should show "Follow-up (MOV Request)"
        assert "Follow-up" in call_args[0][1] or "MOV" in call_args[0][1]

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_trigger_round_started_initial_dispute(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test round started for round 1 (Initial Dispute)."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM006"}

        result = trigger_round_started(mock_db, 1, 1)

        assert result["sent"] is True
        call_args = mock_send.call_args
        assert "Initial Dispute" in call_args[0][1]


# ============== send_custom_sms Tests ==============


class TestSendCustomSms:
    """Tests for send_custom_sms function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_send_custom_sms_success(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test successful custom SMS."""
        mock_settings.return_value = {"sms_enabled": True}
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM007"}

        result = send_custom_sms(mock_db, 1, "Your appointment is confirmed!")

        assert result["sent"] is True
        call_args = mock_send.call_args
        assert "appointment is confirmed" in call_args[0][1]

    @patch("services.sms_automation.get_sms_settings")
    def test_send_custom_sms_disabled(self, mock_settings, mock_db):
        """Test custom SMS when SMS is disabled."""
        mock_settings.return_value = {"sms_enabled": False}

        result = send_custom_sms(mock_db, 1, "Custom message")

        assert result["sent"] is False
        assert "disabled" in result["reason"]

    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    def test_send_custom_sms_twilio_not_configured(
        self, mock_settings, mock_configured, mock_db
    ):
        """Test custom SMS when Twilio is not configured."""
        mock_settings.return_value = {"sms_enabled": True}
        mock_configured.return_value = False

        result = send_custom_sms(mock_db, 1, "Custom message")

        assert result["sent"] is False
        assert "Twilio not configured" in result["reason"]


# ============== send_test_sms Tests ==============


class TestSendTestSms:
    """Tests for send_test_sms function."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    def test_send_test_sms_success(self, mock_configured, mock_send):
        """Test successful test SMS."""
        mock_configured.return_value = True
        mock_send.return_value = {"success": True, "message_sid": "SM_TEST"}

        result = send_test_sms("+15551234567")

        assert result["sent"] is True
        assert result["message_sid"] == "SM_TEST"
        mock_send.assert_called_once()

    @patch("services.sms_automation.is_twilio_configured")
    def test_send_test_sms_not_configured(self, mock_configured):
        """Test test SMS when Twilio is not configured."""
        mock_configured.return_value = False

        result = send_test_sms("+15551234567")

        assert result["sent"] is False
        assert "Twilio not configured" in result["reason"]

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    def test_send_test_sms_custom_message(self, mock_configured, mock_send):
        """Test test SMS with custom message."""
        mock_configured.return_value = True
        mock_send.return_value = {"success": True, "message_sid": "SM_TEST"}

        result = send_test_sms("+15551234567", "Custom test message")

        mock_send.assert_called_once_with("+15551234567", "Custom test message")

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    def test_send_test_sms_default_message(self, mock_configured, mock_send):
        """Test test SMS with default message."""
        mock_configured.return_value = True
        mock_send.return_value = {"success": True, "message_sid": "SM_TEST"}

        result = send_test_sms("+15551234567")

        call_args = mock_send.call_args
        assert "Brightpath Ascend" in call_args[0][1]
        assert "test message" in call_args[0][1].lower()


# ============== get_clients_needing_document_reminder Tests ==============


class TestGetClientsNeedingDocumentReminder:
    """Tests for get_clients_needing_document_reminder function."""

    def test_get_clients_needing_document_reminder_success(self, mock_db):
        """Test getting clients with missing documents."""
        # Create mock client with missing docs
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Test Client"

        # Create mock document
        mock_doc = Mock()
        mock_doc.received = False
        mock_doc.document_type = "Driver's License"

        # Create a separate mock for the document query
        mock_doc_query = Mock()
        mock_doc_query.filter_by.return_value.all.return_value = [mock_doc]

        # Set up query to return different results based on what's being queried
        def query_side_effect(model):
            if hasattr(model, '__name__') and model.__name__ == 'ClientDocument':
                return mock_doc_query
            # Return client query chain
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [mock_client]
            return mock_query

        mock_db.query.side_effect = query_side_effect

        result = get_clients_needing_document_reminder(mock_db, hours=24)

        assert len(result) == 1
        assert result[0]["client"] == mock_client
        assert "Driver's License" in result[0]["missing_docs"]

    def test_get_clients_needing_document_reminder_all_received(self, mock_db):
        """Test when all documents are received."""
        mock_client = Mock()
        mock_client.id = 1

        mock_doc = Mock()
        mock_doc.received = True
        mock_doc.document_type = "Driver's License"

        mock_doc_query = Mock()
        mock_doc_query.filter_by.return_value.all.return_value = [mock_doc]

        def query_side_effect(model):
            if hasattr(model, '__name__') and model.__name__ == 'ClientDocument':
                return mock_doc_query
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [mock_client]
            return mock_query

        mock_db.query.side_effect = query_side_effect

        result = get_clients_needing_document_reminder(mock_db, hours=24)

        assert len(result) == 0

    def test_get_clients_needing_document_reminder_no_clients(self, mock_db):
        """Test when no clients need reminders."""
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = []
            return mock_query

        mock_db.query.side_effect = query_side_effect

        result = get_clients_needing_document_reminder(mock_db)

        assert len(result) == 0

    def test_get_clients_needing_document_reminder_custom_hours(self, mock_db):
        """Test with custom hours parameter."""
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = []
            return mock_query

        mock_db.query.side_effect = query_side_effect

        result = get_clients_needing_document_reminder(mock_db, hours=48)

        # Function should work with different hour values
        assert isinstance(result, list)

    def test_get_clients_needing_document_reminder_multiple_missing_docs(self, mock_db):
        """Test client with multiple missing documents."""
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Test Client"

        mock_doc1 = Mock()
        mock_doc1.received = False
        mock_doc1.document_type = "Driver's License"

        mock_doc2 = Mock()
        mock_doc2.received = False
        mock_doc2.document_type = "SSN Card"

        mock_doc3 = Mock()
        mock_doc3.received = True
        mock_doc3.document_type = "Utility Bill"

        mock_doc_query = Mock()
        mock_doc_query.filter_by.return_value.all.return_value = [mock_doc1, mock_doc2, mock_doc3]

        def query_side_effect(model):
            if hasattr(model, '__name__') and model.__name__ == 'ClientDocument':
                return mock_doc_query
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [mock_client]
            return mock_query

        mock_db.query.side_effect = query_side_effect

        result = get_clients_needing_document_reminder(mock_db, hours=24)

        assert len(result) == 1
        assert "Driver's License" in result[0]["missing_docs"]
        assert "SSN Card" in result[0]["missing_docs"]
        assert "Utility Bill" not in result[0]["missing_docs"]


# ============== get_clients_needing_payment_reminder Tests ==============


class TestGetClientsNeedingPaymentReminder:
    """Tests for get_clients_needing_payment_reminder function."""

    def test_get_clients_needing_payment_reminder_success(self, mock_db):
        """Test getting clients with pending payments."""
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Test Client"
        mock_client.payment_status = "pending"
        mock_client.payment_pending = True

        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [mock_client]
            return mock_query

        mock_db.query.side_effect = query_side_effect

        result = get_clients_needing_payment_reminder(mock_db, days=3)

        assert len(result) == 1
        assert result[0] == mock_client

    def test_get_clients_needing_payment_reminder_no_pending(self, mock_db):
        """Test when no clients have pending payments."""
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = []
            return mock_query

        mock_db.query.side_effect = query_side_effect

        result = get_clients_needing_payment_reminder(mock_db)

        assert len(result) == 0

    def test_get_clients_needing_payment_reminder_custom_days(self, mock_db):
        """Test with custom days parameter."""
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = []
            return mock_query

        mock_db.query.side_effect = query_side_effect

        result = get_clients_needing_payment_reminder(mock_db, days=7)

        assert isinstance(result, list)

    def test_get_clients_needing_payment_reminder_multiple_clients(self, mock_db):
        """Test with multiple clients having pending payments."""
        mock_client1 = Mock()
        mock_client1.id = 1
        mock_client1.name = "Client 1"

        mock_client2 = Mock()
        mock_client2.id = 2
        mock_client2.name = "Client 2"

        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [mock_client1, mock_client2]
            return mock_query

        mock_db.query.side_effect = query_side_effect

        result = get_clients_needing_payment_reminder(mock_db, days=3)

        assert len(result) == 2
        assert mock_client1 in result
        assert mock_client2 in result


# ============== Edge Cases and Error Handling ==============


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_sms_send_failure(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test handling of SMS send failure."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {
            "success": False,
            "message_sid": None,
            "error": "Twilio API error",
        }

        result = trigger_welcome_sms(mock_db, 1)

        assert result["sent"] is False
        assert "Twilio API error" in result.get("error", "")

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_empty_client_name(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db
    ):
        """Test SMS with empty client name."""
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = ""
        mock_client.mobile = "+15551234567"

        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM123"}

        result = trigger_welcome_sms(mock_db, 1)

        # Should still succeed, template handles empty name
        assert result["sent"] is True

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_none_client_name(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db
    ):
        """Test SMS with None client name."""
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = None
        mock_client.mobile = "+15551234567"

        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM123"}

        result = trigger_welcome_sms(mock_db, 1)

        # Should still succeed, template handles None name
        assert result["sent"] is True

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_special_characters_in_message(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test custom SMS with special characters."""
        mock_settings.return_value = {"sms_enabled": True}
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM123"}

        result = send_custom_sms(
            mock_db, 1, "Test with special chars: @#$%^&*()!<>\"'"
        )

        assert result["sent"] is True

    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_unicode_in_message(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_db, mock_client
    ):
        """Test custom SMS with unicode characters."""
        mock_settings.return_value = {"sms_enabled": True}
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM123"}

        result = send_custom_sms(mock_db, 1, "Test with unicode: Jose Garcia")

        assert result["sent"] is True


# ============== Integration-like Tests ==============


class TestSmsAutomationIntegration:
    """Integration-like tests for SMS automation workflow."""

    @patch("services.sms_automation.log_sms")
    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_full_welcome_workflow(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_log, mock_db, mock_client
    ):
        """Test complete welcome SMS workflow."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM_WELCOME"}

        result = trigger_welcome_sms(mock_db, 1)

        # Verify all steps
        mock_settings.assert_called_once_with(mock_db)
        mock_configured.assert_called_once()
        mock_get_phone.assert_called_once_with(mock_db, 1)
        mock_send.assert_called_once()
        mock_log.assert_called_once()
        assert result["sent"] is True

    @patch("services.sms_automation.log_sms")
    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_multiple_sms_types(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_log, mock_db, mock_client
    ):
        """Test sending multiple SMS types in sequence."""
        mock_settings.return_value = {
            "sms_enabled": True,
            "welcome_sms_enabled": True,
            "document_reminder_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True, "message_sid": "SM123"}

        # Send multiple types
        result1 = trigger_welcome_sms(mock_db, 1)
        result2 = trigger_document_reminder(mock_db, 1, "SSN Card")
        result3 = trigger_case_update(mock_db, 1, "active")

        assert all([result1["sent"], result2["sent"], result3["sent"]])
        assert mock_send.call_count == 3
        assert mock_log.call_count == 3


# ============== Template Type Verification Tests ==============


class TestTemplateTypeVerification:
    """Tests to verify correct template types are logged."""

    @patch("services.sms_automation.log_sms")
    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_welcome_logs_correct_type(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_log, mock_db, mock_client
    ):
        """Test welcome SMS logs correct template type."""
        mock_settings.return_value = {"sms_enabled": True, "welcome_sms_enabled": True}
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True}

        trigger_welcome_sms(mock_db, 1)

        call_args = mock_log.call_args[0]
        assert call_args[4] == "welcome"

    @patch("services.sms_automation.log_sms")
    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_document_reminder_logs_correct_type(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_log, mock_db, mock_client
    ):
        """Test document reminder logs correct template type."""
        mock_settings.return_value = {"sms_enabled": True, "document_reminder_enabled": True}
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True}

        trigger_document_reminder(mock_db, 1)

        call_args = mock_log.call_args[0]
        assert call_args[4] == "document_reminder"

    @patch("services.sms_automation.log_sms")
    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_case_update_logs_correct_type(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_log, mock_db, mock_client
    ):
        """Test case update logs correct template type."""
        mock_settings.return_value = {"sms_enabled": True, "case_update_enabled": True}
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True}

        trigger_case_update(mock_db, 1, "active")

        call_args = mock_log.call_args[0]
        assert call_args[4] == "case_update"

    @patch("services.sms_automation.log_sms")
    @patch("services.sms_automation.send_sms")
    @patch("services.sms_automation.is_twilio_configured")
    @patch("services.sms_automation.get_sms_settings")
    @patch("services.sms_automation.get_client_phone")
    def test_custom_logs_correct_type(
        self, mock_get_phone, mock_settings, mock_configured, mock_send, mock_log, mock_db, mock_client
    ):
        """Test custom SMS logs correct template type."""
        mock_settings.return_value = {"sms_enabled": True}
        mock_configured.return_value = True
        mock_get_phone.return_value = ("+15551234567", mock_client)
        mock_send.return_value = {"success": True}

        send_custom_sms(mock_db, 1, "Custom message")

        call_args = mock_log.call_args[0]
        assert call_args[4] == "custom"
