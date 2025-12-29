"""
Comprehensive unit tests for services/email_automation.py
Tests email sending, batch operations, and template processing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os


class TestApplyTemplateMergeTags:
    """Tests for apply_template_merge_tags function."""

    def test_apply_basic_merge_tags(self):
        """Test basic merge tag replacement."""
        from services.email_automation import apply_template_merge_tags

        html = "Hello {{client_name}}, your email is {{client_email}}"
        values = {"client_name": "John Doe", "client_email": "john@example.com"}
        result = apply_template_merge_tags(html, values)
        assert result == "Hello John Doe, your email is john@example.com"

    def test_apply_default_company_values(self):
        """Test that default company values are applied."""
        from services.email_automation import apply_template_merge_tags

        html = "Welcome to {{company_name}}! Contact {{support_email}}"
        result = apply_template_merge_tags(html, {})
        assert "Brightpath Ascend Group" in result
        assert "support@brightpathascend.com" in result

    def test_apply_cra_addresses(self):
        """Test CRA address merge tags."""
        from services.email_automation import apply_template_merge_tags

        html = "Equifax: {{equifax_name}} at {{equifax_address}}"
        result = apply_template_merge_tags(html, {})
        assert "Equifax Information Services LLC" in result
        assert "P.O. Box 740256" in result

    def test_apply_merge_tags_none_content(self):
        """Test that None content returns None."""
        from services.email_automation import apply_template_merge_tags

        result = apply_template_merge_tags(None, {"key": "value"})
        assert result is None

    def test_apply_merge_tags_empty_content(self):
        """Test that empty content returns empty string."""
        from services.email_automation import apply_template_merge_tags

        result = apply_template_merge_tags("", {"key": "value"})
        assert result == ""

    def test_apply_merge_tags_none_value(self):
        """Test that None values become empty strings."""
        from services.email_automation import apply_template_merge_tags

        html = "Value: {{test_value}}"
        result = apply_template_merge_tags(html, {"test_value": None})
        assert result == "Value: "

    def test_apply_merge_tags_override_defaults(self):
        """Test that custom values override default values."""
        from services.email_automation import apply_template_merge_tags

        html = "Company: {{company_name}}"
        result = apply_template_merge_tags(html, {"company_name": "Custom Company"})
        assert result == "Company: Custom Company"

    def test_apply_merge_tags_numeric_values(self):
        """Test numeric values are converted to strings."""
        from services.email_automation import apply_template_merge_tags

        html = "Amount: {{amount}}"
        result = apply_template_merge_tags(html, {"amount": 12345})
        assert result == "Amount: 12345"


class TestGetEmailSettings:
    """Tests for get_email_settings function."""

    def test_get_email_settings_defaults(self):
        """Test default email settings are returned."""
        from services.email_automation import get_email_settings

        mock_db = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        settings = get_email_settings(mock_db)

        assert settings["email_enabled"] is True
        assert settings["welcome_email_enabled"] is True
        assert settings["document_reminder_enabled"] is True
        assert settings["reminder_delay_hours"] == 48

    def test_get_email_settings_from_database(self):
        """Test settings are read from database."""
        from services.email_automation import get_email_settings

        mock_db = Mock()
        mock_setting = Mock()
        mock_setting.setting_value = "false"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_setting

        settings = get_email_settings(mock_db)

        assert settings["email_enabled"] is False

    def test_get_email_settings_int_parsing(self):
        """Test integer setting parsing."""
        from services.email_automation import get_email_settings

        mock_db = Mock()

        def mock_query(*args):
            mock_result = Mock()

            def mock_filter_by(**kwargs):
                filter_result = Mock()
                if kwargs.get("setting_key") == "email_reminder_delay_hours":
                    setting = Mock()
                    setting.setting_value = "72"
                    filter_result.first.return_value = setting
                else:
                    filter_result.first.return_value = None
                return filter_result

            mock_result.filter_by = mock_filter_by
            return mock_result

        mock_db.query = mock_query
        settings = get_email_settings(mock_db)
        assert settings["reminder_delay_hours"] == 72

    def test_get_email_settings_invalid_int(self):
        """Test that invalid int values use defaults."""
        from services.email_automation import get_email_settings

        mock_db = Mock()

        def mock_query(*args):
            mock_result = Mock()

            def mock_filter_by(**kwargs):
                filter_result = Mock()
                if kwargs.get("setting_key") == "email_reminder_delay_hours":
                    setting = Mock()
                    setting.setting_value = "not_a_number"
                    filter_result.first.return_value = setting
                else:
                    filter_result.first.return_value = None
                return filter_result

            mock_result.filter_by = mock_filter_by
            return mock_result

        mock_db.query = mock_query
        settings = get_email_settings(mock_db)
        assert settings["reminder_delay_hours"] == 48  # Default value


class TestGetCustomTemplate:
    """Tests for get_custom_template function."""

    def test_get_custom_template_exists(self):
        """Test retrieving existing custom template."""
        from services.email_automation import get_custom_template

        mock_db = Mock()
        mock_template = Mock()
        mock_template.is_custom = True
        mock_template.subject = "Custom Subject"
        mock_template.html_content = "<h1>Custom Content</h1>"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_template
        )

        subject, html = get_custom_template(mock_db, "welcome")

        assert subject == "Custom Subject"
        assert html == "<h1>Custom Content</h1>"

    def test_get_custom_template_not_exists(self):
        """Test when no custom template exists."""
        from services.email_automation import get_custom_template

        mock_db = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        subject, html = get_custom_template(mock_db, "welcome")

        assert subject is None
        assert html is None

    def test_get_custom_template_not_custom(self):
        """Test when template exists but is_custom is False."""
        from services.email_automation import get_custom_template

        mock_db = Mock()
        mock_template = Mock()
        mock_template.is_custom = False
        mock_template.html_content = "<h1>Content</h1>"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_template
        )

        subject, html = get_custom_template(mock_db, "welcome")

        assert subject is None
        assert html is None


class TestLogEmail:
    """Tests for log_email function."""

    def test_log_email_success(self):
        """Test successful email logging."""
        from services.email_automation import log_email

        mock_db = Mock()

        result = log_email(
            mock_db,
            client_id=1,
            email_address="test@example.com",
            template_type="welcome",
            subject="Test Subject",
            status="sent",
            message_id="msg123",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_log_email_with_error(self):
        """Test email logging with error message."""
        from services.email_automation import log_email

        mock_db = Mock()

        result = log_email(
            mock_db,
            client_id=1,
            email_address="test@example.com",
            template_type="welcome",
            subject="Test Subject",
            status="failed",
            error_message="SMTP error",
        )

        mock_db.add.assert_called_once()
        added_log = mock_db.add.call_args[0][0]
        assert added_log.error_message == "SMTP error"


class TestGetPortalUrl:
    """Tests for get_portal_url function."""

    def test_get_portal_url_with_token(self):
        """Test portal URL generation with token."""
        from services.email_automation import get_portal_url

        mock_client = Mock()
        mock_client.portal_token = "abc123"

        with patch.dict(os.environ, {"REPLIT_DEV_DOMAIN": "example.com"}):
            url = get_portal_url(mock_client)

        assert url == "https://example.com/portal/abc123"

    def test_get_portal_url_no_token(self):
        """Test portal URL when client has no token."""
        from services.email_automation import get_portal_url

        mock_client = Mock()
        mock_client.portal_token = None

        url = get_portal_url(mock_client)

        assert url is None

    def test_get_portal_url_with_https_domain(self):
        """Test portal URL when domain already has https."""
        from services.email_automation import get_portal_url

        mock_client = Mock()
        mock_client.portal_token = "token123"

        with patch.dict(os.environ, {"REPLIT_DEV_DOMAIN": "https://example.com"}):
            url = get_portal_url(mock_client)

        assert url == "https://example.com/portal/token123"


class TestTriggerWelcomeEmail:
    """Tests for trigger_welcome_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_welcome_email_success(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test successful welcome email trigger."""
        from services.email_automation import trigger_welcome_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "John Doe"
        mock_client.email = "john@example.com"
        mock_client.portal_token = "token123"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "welcome_email_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True, "message_id": "msg123"}

        result = trigger_welcome_email(mock_db, 1)

        assert result["sent"] is True
        mock_send.assert_called_once()

    @patch("services.email_automation.get_email_settings")
    def test_trigger_welcome_email_disabled(self, mock_settings):
        """Test welcome email when disabled."""
        from services.email_automation import trigger_welcome_email

        mock_db = Mock()
        mock_settings.return_value = {
            "email_enabled": False,
            "welcome_email_enabled": True,
        }

        result = trigger_welcome_email(mock_db, 1)

        assert result["sent"] is False
        assert "disabled" in result["reason"]

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_welcome_email_sendgrid_not_configured(
        self, mock_settings, mock_configured
    ):
        """Test welcome email when SendGrid not configured."""
        from services.email_automation import trigger_welcome_email

        mock_db = Mock()
        mock_settings.return_value = {
            "email_enabled": True,
            "welcome_email_enabled": True,
        }
        mock_configured.return_value = False

        result = trigger_welcome_email(mock_db, 1)

        assert result["sent"] is False
        assert "SendGrid" in result["reason"]

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_welcome_email_no_client(self, mock_settings, mock_configured):
        """Test welcome email when client not found."""
        from services.email_automation import trigger_welcome_email

        mock_db = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_settings.return_value = {
            "email_enabled": True,
            "welcome_email_enabled": True,
        }
        mock_configured.return_value = True

        result = trigger_welcome_email(mock_db, 999)

        assert result["sent"] is False
        assert "not found" in result["reason"]


class TestTriggerDocumentReminderEmail:
    """Tests for trigger_document_reminder_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_document_reminder_success(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test successful document reminder email."""
        from services.email_automation import trigger_document_reminder_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Jane Doe"
        mock_client.email = "jane@example.com"
        mock_client.portal_token = "token456"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "document_reminder_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True, "message_id": "msg456"}

        result = trigger_document_reminder_email(
            mock_db, 1, ["Driver's License", "SSN Card"]
        )

        assert result["sent"] is True

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_document_reminder_string_docs(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test document reminder with string instead of list."""
        from services.email_automation import trigger_document_reminder_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Jane Doe"
        mock_client.email = "jane@example.com"
        mock_client.portal_token = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "document_reminder_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = trigger_document_reminder_email(mock_db, 1, "Driver's License")

        assert result["sent"] is True


class TestTriggerCaseUpdateEmail:
    """Tests for trigger_case_update_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_case_update_success(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test successful case update email."""
        from services.email_automation import trigger_case_update_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Test User"
        mock_client.email = "test@example.com"
        mock_client.portal_token = "token789"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True, "message_id": "msg789"}

        result = trigger_case_update_email(
            mock_db, 1, "stage1_complete", "Analysis completed"
        )

        assert result["sent"] is True

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_case_update_status_formatting(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test status display formatting."""
        from services.email_automation import trigger_case_update_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Test User"
        mock_client.email = "test@example.com"
        mock_client.portal_token = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = trigger_case_update_email(mock_db, 1, "waiting_response")

        # Verify email was sent with formatted status
        assert result["sent"] is True


class TestTriggerDisputeSentEmail:
    """Tests for trigger_dispute_sent_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_dispute_sent_success(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test successful dispute sent email."""
        from services.email_automation import trigger_dispute_sent_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Client Name"
        mock_client.email = "client@example.com"
        mock_client.portal_token = "token"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "dispute_sent_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = trigger_dispute_sent_email(
            mock_db, 1, "Equifax", "TRACKING123"
        )

        assert result["sent"] is True


class TestTriggerCraResponseEmail:
    """Tests for trigger_cra_response_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_cra_response_success(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test successful CRA response email."""
        from services.email_automation import trigger_cra_response_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Client Name"
        mock_client.email = "client@example.com"
        mock_client.portal_token = "token"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "cra_response_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = trigger_cra_response_email(
            mock_db, 1, "Experian", "3 items deleted"
        )

        assert result["sent"] is True


class TestTriggerPaymentReminderEmail:
    """Tests for trigger_payment_reminder_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_payment_reminder_success(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test successful payment reminder email."""
        from services.email_automation import trigger_payment_reminder_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Client Name"
        mock_client.email = "client@example.com"
        mock_client.portal_token = "token"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "payment_reminder_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = trigger_payment_reminder_email(
            mock_db, 1, 199.99, "2025-02-01"
        )

        assert result["sent"] is True


class TestTriggerAnalysisReadyEmail:
    """Tests for trigger_analysis_ready_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_analysis_ready_success(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test successful analysis ready email."""
        from services.email_automation import trigger_analysis_ready_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Client Name"
        mock_client.email = "client@example.com"
        mock_client.portal_token = "token"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "analysis_ready_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = trigger_analysis_ready_email(
            mock_db, 1, violations_count=15, exposure=50000
        )

        assert result["sent"] is True


class TestTriggerLettersReadyEmail:
    """Tests for trigger_letters_ready_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_letters_ready_success(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test successful letters ready email."""
        from services.email_automation import trigger_letters_ready_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Client Name"
        mock_client.email = "client@example.com"
        mock_client.portal_token = "token"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "letters_ready_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = trigger_letters_ready_email(
            mock_db, 1, 3, ["Equifax", "Experian", "TransUnion"]
        )

        assert result["sent"] is True

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_trigger_letters_ready_string_bureaus(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test letters ready with string bureaus."""
        from services.email_automation import trigger_letters_ready_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Client Name"
        mock_client.email = "client@example.com"
        mock_client.portal_token = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "letters_ready_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = trigger_letters_ready_email(mock_db, 1, 1, "Equifax")

        assert result["sent"] is True


class TestSendTestEmail:
    """Tests for send_test_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    def test_send_test_email_not_configured(self, mock_configured):
        """Test test email when SendGrid not configured."""
        from services.email_automation import send_test_email

        mock_configured.return_value = False

        result = send_test_email("test@example.com")

        assert result["success"] is False
        assert "not configured" in result["error"]

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    def test_send_test_email_success(self, mock_send, mock_configured):
        """Test successful test email."""
        from services.email_automation import send_test_email

        mock_configured.return_value = True
        mock_send.return_value = {"success": True, "message_id": "test123"}

        result = send_test_email("test@example.com")

        assert result["success"] is True
        mock_send.assert_called_once()

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    def test_send_test_email_custom_message(self, mock_send, mock_configured):
        """Test test email with custom message."""
        from services.email_automation import send_test_email

        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = send_test_email("test@example.com", "Custom test message")

        assert result["success"] is True
        # Verify custom message was included in the call
        call_args = mock_send.call_args
        assert "Custom test message" in call_args[0][2]


class TestSendCustomEmail:
    """Tests for send_custom_email function."""

    @patch("services.email_automation.is_sendgrid_configured")
    def test_send_custom_email_not_configured(self, mock_configured):
        """Test custom email when SendGrid not configured."""
        from services.email_automation import send_custom_email

        mock_db = Mock()
        mock_configured.return_value = False

        result = send_custom_email(
            mock_db, 1, "Custom Subject", "Custom message"
        )

        assert result["success"] is False

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    def test_send_custom_email_success(self, mock_send, mock_configured):
        """Test successful custom email."""
        from services.email_automation import send_custom_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "John Smith"
        mock_client.email = "john@example.com"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_configured.return_value = True
        mock_send.return_value = {"success": True, "message_id": "custom123"}

        result = send_custom_email(
            mock_db, 1, "Custom Subject", "Hello, this is a custom message"
        )

        assert result["success"] is True
        # Verify the email was logged
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @patch("services.email_automation.is_sendgrid_configured")
    def test_send_custom_email_client_not_found(self, mock_configured):
        """Test custom email when client not found."""
        from services.email_automation import send_custom_email

        mock_db = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_configured.return_value = True

        result = send_custom_email(
            mock_db, 999, "Subject", "Message"
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    def test_send_custom_email_extracts_first_name(
        self, mock_send, mock_configured
    ):
        """Test that custom email extracts first name correctly."""
        from services.email_automation import send_custom_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Jane Marie Doe"
        mock_client.email = "jane@example.com"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        send_custom_email(mock_db, 1, "Hello", "Test message")

        # Check the HTML content includes "Hi Jane"
        call_args = mock_send.call_args
        assert "Hi Jane" in call_args[0][2]


class TestCRAAddresses:
    """Tests for CRA_ADDRESSES constant."""

    def test_cra_addresses_contains_main_bureaus(self):
        """Test CRA addresses include main bureaus."""
        from services.email_automation import CRA_ADDRESSES

        assert "equifax_name" in CRA_ADDRESSES
        assert "experian_name" in CRA_ADDRESSES
        assert "transunion_name" in CRA_ADDRESSES

    def test_cra_addresses_contains_freeze_addresses(self):
        """Test CRA addresses include freeze addresses."""
        from services.email_automation import CRA_ADDRESSES

        assert "equifax_freeze_address" in CRA_ADDRESSES
        assert "experian_freeze_address" in CRA_ADDRESSES
        assert "transunion_freeze_address" in CRA_ADDRESSES

    def test_cra_addresses_contains_secondary_bureaus(self):
        """Test CRA addresses include secondary bureaus."""
        from services.email_automation import CRA_ADDRESSES

        assert "innovis_name" in CRA_ADDRESSES
        assert "chexsystems_name" in CRA_ADDRESSES
        assert "clarity_name" in CRA_ADDRESSES
        assert "lexisnexis_name" in CRA_ADDRESSES


class TestEmailFailureHandling:
    """Tests for email failure scenarios."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_email_send_failure_logged(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test that failed emails are properly logged."""
        from services.email_automation import trigger_welcome_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Test User"
        mock_client.email = "test@example.com"
        mock_client.portal_token = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "welcome_email_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {
            "success": False,
            "error": "SMTP Connection Failed",
        }

        result = trigger_welcome_email(mock_db, 1)

        assert result["sent"] is False
        assert "SMTP Connection Failed" in result.get("error", "")
        # Verify the failure was logged
        mock_db.add.assert_called()

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.get_email_settings")
    def test_client_no_email(self, mock_settings, mock_configured):
        """Test handling client with no email address."""
        from services.email_automation import trigger_welcome_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Test User"
        mock_client.email = None  # No email
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "welcome_email_enabled": True,
        }
        mock_configured.return_value = True

        result = trigger_welcome_email(mock_db, 1)

        assert result["sent"] is False
        assert "no email" in result["reason"]


class TestCustomTemplateProcessing:
    """Tests for custom template processing."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    @patch("services.email_automation.get_custom_template")
    def test_custom_template_used_when_available(
        self, mock_custom_template, mock_settings, mock_send, mock_configured
    ):
        """Test that custom template is used when available."""
        from services.email_automation import trigger_welcome_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "John Doe"
        mock_client.email = "john@example.com"
        mock_client.portal_token = "token"
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "welcome_email_enabled": True,
        }
        mock_configured.return_value = True
        mock_custom_template.return_value = (
            "Custom Welcome {{client_name}}!",
            "<h1>Hello {{client_name}}</h1>",
        )
        mock_send.return_value = {"success": True}

        trigger_welcome_email(mock_db, 1)

        # Verify custom template was processed
        call_args = mock_send.call_args
        subject = call_args[0][1]
        html = call_args[0][2]
        assert "Custom Welcome John Doe!" in subject
        assert "<h1>Hello John Doe</h1>" in html


class TestBatchEmailOperations:
    """Tests for batch email operations (simulated via multiple calls)."""

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    @patch("services.email_automation.get_custom_template")
    def test_multiple_emails_sent(
        self, mock_custom_template, mock_settings, mock_send, mock_configured
    ):
        """Test sending multiple emails in sequence."""
        from services.email_automation import trigger_welcome_email

        mock_db = Mock()
        mock_settings.return_value = {
            "email_enabled": True,
            "welcome_email_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}
        mock_custom_template.return_value = (None, None)

        # Create multiple mock clients
        clients = []
        for i in range(3):
            client = Mock()
            client.id = i + 1
            client.name = f"Client {i + 1}"
            client.email = f"client{i + 1}@example.com"
            client.portal_token = f"token{i + 1}"
            clients.append(client)

        # Use side_effect to return different clients on consecutive calls
        mock_db.query.return_value.filter_by.return_value.first.side_effect = clients

        # Send emails to all clients
        results = []
        for i in range(3):
            result = trigger_welcome_email(mock_db, i + 1)
            results.append(result)

        # Verify all emails were attempted
        assert all(r["sent"] for r in results)
        assert mock_send.call_count == 3


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_client_name(self):
        """Test handling empty client name in template."""
        from services.email_automation import apply_template_merge_tags

        html = "Hello {{client_name}}"
        result = apply_template_merge_tags(html, {"client_name": ""})
        assert result == "Hello "

    def test_special_characters_in_template(self):
        """Test special characters in merge values."""
        from services.email_automation import apply_template_merge_tags

        html = "Name: {{client_name}}"
        result = apply_template_merge_tags(
            html, {"client_name": "O'Brien & Associates <LLC>"}
        )
        assert result == "Name: O'Brien & Associates <LLC>"

    def test_unicode_in_template(self):
        """Test unicode characters in merge values."""
        from services.email_automation import apply_template_merge_tags

        html = "Name: {{client_name}}"
        result = apply_template_merge_tags(html, {"client_name": "Jose Garcia"})
        assert result == "Name: Jose Garcia"

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_none_status_in_case_update(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test case update with None status."""
        from services.email_automation import trigger_case_update_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Test User"
        mock_client.email = "test@example.com"
        mock_client.portal_token = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "case_update_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        # Should not raise an error
        result = trigger_case_update_email(mock_db, 1, None)
        assert result["sent"] is True

    @patch("services.email_automation.is_sendgrid_configured")
    @patch("services.email_automation.send_email")
    @patch("services.email_automation.get_email_settings")
    def test_none_bureau_in_letters_ready(
        self, mock_settings, mock_send, mock_configured
    ):
        """Test letters ready with None bureaus."""
        from services.email_automation import trigger_letters_ready_email

        mock_db = Mock()
        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = "Test User"
        mock_client.email = "test@example.com"
        mock_client.portal_token = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_client
        )

        mock_settings.return_value = {
            "email_enabled": True,
            "letters_ready_enabled": True,
        }
        mock_configured.return_value = True
        mock_send.return_value = {"success": True}

        result = trigger_letters_ready_email(mock_db, 1, 1, None)
        assert result["sent"] is True
