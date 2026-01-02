"""
Unit tests for WhatsApp Automation Service
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Set test environment
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost/test')
os.environ.setdefault('TWILIO_ACCOUNT_SID', 'ACtest123')
os.environ.setdefault('TWILIO_AUTH_TOKEN', 'test_token')
os.environ.setdefault('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+15559876543')


class TestCheckWhatsAppOptIn:
    """Tests for check_whatsapp_opt_in function"""

    def test_opt_in_all_conditions_met(self):
        """Test returns True when all conditions met"""
        from services.whatsapp_automation import check_whatsapp_opt_in

        client = MagicMock()
        client.whatsapp_opt_in = True
        client.whatsapp_verified = True
        client.whatsapp_number = "+15551234567"

        assert check_whatsapp_opt_in(client) is True

    def test_opt_in_not_opted_in(self):
        """Test returns False when not opted in"""
        from services.whatsapp_automation import check_whatsapp_opt_in

        client = MagicMock()
        client.whatsapp_opt_in = False
        client.whatsapp_verified = True
        client.whatsapp_number = "+15551234567"

        assert check_whatsapp_opt_in(client) is False

    def test_opt_in_not_verified(self):
        """Test returns False when not verified"""
        from services.whatsapp_automation import check_whatsapp_opt_in

        client = MagicMock()
        client.whatsapp_opt_in = True
        client.whatsapp_verified = False
        client.whatsapp_number = "+15551234567"

        assert check_whatsapp_opt_in(client) is False

    def test_opt_in_no_number(self):
        """Test returns False when no WhatsApp number"""
        from services.whatsapp_automation import check_whatsapp_opt_in

        client = MagicMock()
        client.whatsapp_opt_in = True
        client.whatsapp_verified = True
        client.whatsapp_number = None

        assert check_whatsapp_opt_in(client) is False

    def test_opt_in_none_client(self):
        """Test returns False for None client"""
        from services.whatsapp_automation import check_whatsapp_opt_in

        assert check_whatsapp_opt_in(None) is False


class TestGetWhatsAppSettings:
    """Tests for get_whatsapp_settings function"""

    def test_returns_defaults_when_no_settings(self):
        """Test returns default values when no settings in DB"""
        from services.whatsapp_automation import get_whatsapp_settings

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        settings = get_whatsapp_settings(mock_db)

        assert settings['whatsapp_enabled'] is False
        assert settings['document_request_enabled'] is True
        assert settings['status_update_enabled'] is True
        assert settings['letters_ready_enabled'] is True

    def test_returns_db_values_when_present(self):
        """Test returns database values when present"""
        from services.whatsapp_automation import get_whatsapp_settings

        mock_db = MagicMock()
        mock_setting = MagicMock()
        mock_setting.setting_value = 'true'
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_setting

        settings = get_whatsapp_settings(mock_db)

        assert settings['whatsapp_enabled'] is True


class TestLogWhatsAppMessage:
    """Tests for log_whatsapp_message function"""

    def test_logs_message_successfully(self):
        """Test logging a WhatsApp message"""
        from services.whatsapp_automation import log_whatsapp_message

        mock_db = MagicMock()
        # Mock the message object that gets added
        mock_message = MagicMock()
        mock_message.id = 1

        def capture_add(obj):
            obj.id = 1  # Simulate ID assignment after add
        mock_db.add.side_effect = capture_add

        with patch('services.whatsapp_automation.get_whatsapp_number', return_value='whatsapp:+15559876543'):
            result = log_whatsapp_message(
                db=mock_db,
                client_id=1,
                direction='outbound',
                to_number='+15551234567',
                body='Test message',
                template_name='test',
                twilio_sid='SM123',
                status='sent'
            )

        # The function adds to DB and commits, result should be the message id
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        # Result is the ID of the created message
        assert result == 1

    def test_logs_message_handles_error(self):
        """Test logging handles database errors gracefully"""
        from services.whatsapp_automation import log_whatsapp_message

        mock_db = MagicMock()
        mock_db.add.side_effect = Exception("DB Error")

        with patch('services.whatsapp_automation.get_whatsapp_number', return_value='whatsapp:+15559876543'):
            result = log_whatsapp_message(
                db=mock_db,
                client_id=1,
                direction='outbound',
                to_number='+15551234567',
                body='Test message'
            )

        assert result is None
        mock_db.rollback.assert_called_once()


class TestTriggerWhatsAppDocumentRequest:
    """Tests for trigger_whatsapp_document_request function"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.id = 1
        client.name = "Test Client"
        client.first_name = "Test"
        client.whatsapp_opt_in = True
        client.whatsapp_verified = True
        client.whatsapp_number = "+15551234567"
        return client

    @patch('services.whatsapp_automation.is_whatsapp_configured')
    def test_returns_error_when_not_configured(self, mock_configured, mock_db):
        """Test returns error when WhatsApp not configured"""
        from services.whatsapp_automation import trigger_whatsapp_document_request

        mock_configured.return_value = False

        result = trigger_whatsapp_document_request(mock_db, 1, 'drivers_license')

        assert result['success'] is False
        assert 'not configured' in result['reason']

    @patch('services.whatsapp_automation.is_whatsapp_configured')
    @patch('services.whatsapp_automation.get_whatsapp_settings')
    def test_returns_error_when_disabled(self, mock_settings, mock_configured, mock_db):
        """Test returns error when WhatsApp automation disabled"""
        from services.whatsapp_automation import trigger_whatsapp_document_request

        mock_configured.return_value = True
        mock_settings.return_value = {'whatsapp_enabled': False}

        result = trigger_whatsapp_document_request(mock_db, 1, 'drivers_license')

        assert result['success'] is False
        assert 'disabled' in result['reason']

    @patch('services.whatsapp_automation.is_whatsapp_configured')
    @patch('services.whatsapp_automation.get_whatsapp_settings')
    def test_returns_error_when_client_not_found(self, mock_settings, mock_configured, mock_db):
        """Test returns error when client not found"""
        from services.whatsapp_automation import trigger_whatsapp_document_request

        mock_configured.return_value = True
        mock_settings.return_value = {
            'whatsapp_enabled': True,
            'document_request_enabled': True
        }
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = trigger_whatsapp_document_request(mock_db, 999, 'drivers_license')

        assert result['success'] is False
        assert 'not found' in result['reason']

    @patch('services.whatsapp_automation.is_whatsapp_configured')
    @patch('services.whatsapp_automation.get_whatsapp_settings')
    def test_returns_error_when_not_opted_in(self, mock_settings, mock_configured, mock_db, mock_client):
        """Test returns error when client not opted in"""
        from services.whatsapp_automation import trigger_whatsapp_document_request

        mock_configured.return_value = True
        mock_settings.return_value = {
            'whatsapp_enabled': True,
            'document_request_enabled': True
        }
        mock_client.whatsapp_opt_in = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        result = trigger_whatsapp_document_request(mock_db, 1, 'drivers_license')

        assert result['success'] is False
        assert 'not opted in' in result['reason']

    @patch('services.whatsapp_automation.is_whatsapp_configured')
    @patch('services.whatsapp_automation.get_whatsapp_settings')
    @patch('services.whatsapp_automation.send_whatsapp')
    @patch('services.whatsapp_automation.log_whatsapp_message')
    def test_sends_whatsapp_successfully(self, mock_log, mock_send, mock_settings, mock_configured, mock_db, mock_client):
        """Test sends WhatsApp message successfully"""
        from services.whatsapp_automation import trigger_whatsapp_document_request

        mock_configured.return_value = True
        mock_settings.return_value = {
            'whatsapp_enabled': True,
            'document_request_enabled': True
        }
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_send.return_value = {'success': True, 'message_sid': 'SM123'}
        mock_log.return_value = 1

        result = trigger_whatsapp_document_request(mock_db, 1, 'drivers_license')

        assert result['success'] is True
        assert result['sent'] is True
        assert result['message_sid'] == 'SM123'
        mock_send.assert_called_once()
        mock_log.assert_called_once()


class TestTriggerWhatsAppStatusUpdate:
    """Tests for trigger_whatsapp_status_update function"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.id = 1
        client.name = "Test Client"
        client.first_name = "Test"
        client.whatsapp_opt_in = True
        client.whatsapp_verified = True
        client.whatsapp_number = "+15551234567"
        return client

    @patch('services.whatsapp_automation.is_whatsapp_configured')
    @patch('services.whatsapp_automation.get_whatsapp_settings')
    @patch('services.whatsapp_automation.send_whatsapp')
    @patch('services.whatsapp_automation.log_whatsapp_message')
    def test_sends_status_update_successfully(self, mock_log, mock_send, mock_settings, mock_configured, mock_db, mock_client):
        """Test sends status update successfully"""
        from services.whatsapp_automation import trigger_whatsapp_status_update

        mock_configured.return_value = True
        mock_settings.return_value = {
            'whatsapp_enabled': True,
            'status_update_enabled': True
        }
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_send.return_value = {'success': True, 'message_sid': 'SM123'}
        mock_log.return_value = 1

        result = trigger_whatsapp_status_update(mock_db, 1, "Your dispute was sent!")

        assert result['success'] is True
        assert result['sent'] is True


class TestTriggerWhatsAppLettersReady:
    """Tests for trigger_whatsapp_letters_ready function"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.id = 1
        client.name = "Test Client"
        client.first_name = "Test"
        client.whatsapp_opt_in = True
        client.whatsapp_verified = True
        client.whatsapp_number = "+15551234567"
        return client

    @patch('services.whatsapp_automation.is_whatsapp_configured')
    @patch('services.whatsapp_automation.get_whatsapp_settings')
    @patch('services.whatsapp_automation.send_whatsapp')
    @patch('services.whatsapp_automation.log_whatsapp_message')
    def test_sends_letters_ready_successfully(self, mock_log, mock_send, mock_settings, mock_configured, mock_db, mock_client):
        """Test sends letters ready notification successfully"""
        from services.whatsapp_automation import trigger_whatsapp_letters_ready

        mock_configured.return_value = True
        mock_settings.return_value = {
            'whatsapp_enabled': True,
            'letters_ready_enabled': True
        }
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_send.return_value = {'success': True, 'message_sid': 'SM123'}
        mock_log.return_value = 1

        result = trigger_whatsapp_letters_ready(mock_db, 1, 3)

        assert result['success'] is True
        assert result['sent'] is True


class TestSendCustomWhatsApp:
    """Tests for send_custom_whatsapp function"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.id = 1
        client.name = "Test Client"
        client.first_name = "Test"
        client.whatsapp_opt_in = True
        client.whatsapp_verified = True
        client.whatsapp_number = "+15551234567"
        return client

    @patch('services.whatsapp_automation.is_whatsapp_configured')
    def test_returns_error_when_not_configured(self, mock_configured, mock_db):
        """Test returns error when WhatsApp not configured"""
        from services.whatsapp_automation import send_custom_whatsapp

        mock_configured.return_value = False

        result = send_custom_whatsapp(mock_db, 1, "Custom message")

        assert result['success'] is False
        assert 'not configured' in result['reason']

    @patch('services.whatsapp_automation.is_whatsapp_configured')
    @patch('services.whatsapp_automation.send_whatsapp')
    @patch('services.whatsapp_automation.log_whatsapp_message')
    def test_sends_custom_message_successfully(self, mock_log, mock_send, mock_configured, mock_db, mock_client):
        """Test sends custom message successfully"""
        from services.whatsapp_automation import send_custom_whatsapp

        mock_configured.return_value = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_send.return_value = {'success': True, 'message_sid': 'SM123'}
        mock_log.return_value = 1

        result = send_custom_whatsapp(mock_db, 1, "Custom message to client")

        assert result['success'] is True
        assert result['sent'] is True


class TestDocumentTypes:
    """Test document type constants"""

    def test_document_types_defined(self):
        """Test all expected document types are defined"""
        from services.whatsapp_automation import DOCUMENT_TYPES

        assert 'drivers_license' in DOCUMENT_TYPES
        assert 'ssn_card' in DOCUMENT_TYPES
        assert 'utility_bill' in DOCUMENT_TYPES
        assert 'credit_report' in DOCUMENT_TYPES
        assert 'cra_response' in DOCUMENT_TYPES
        assert 'id_document' in DOCUMENT_TYPES
        assert 'other' in DOCUMENT_TYPES

    def test_document_types_have_display_names(self):
        """Test document types have human-readable display names"""
        from services.whatsapp_automation import DOCUMENT_TYPES

        for key, value in DOCUMENT_TYPES.items():
            assert isinstance(value, str)
            assert len(value) > 0


class TestWhatsAppTemplates:
    """Test template constants"""

    def test_templates_defined(self):
        """Test all expected templates are defined"""
        from services.whatsapp_automation import WHATSAPP_TEMPLATES

        assert 'document_request' in WHATSAPP_TEMPLATES
        assert 'status_update' in WHATSAPP_TEMPLATES
        assert 'letters_ready' in WHATSAPP_TEMPLATES
        assert 'document_received' in WHATSAPP_TEMPLATES
        assert 'verification_code' in WHATSAPP_TEMPLATES
        assert 'welcome' in WHATSAPP_TEMPLATES
