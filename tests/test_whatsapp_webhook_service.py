"""
Unit tests for WhatsApp Webhook Service
"""

import os
import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

# Set test environment
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost/test')
os.environ.setdefault('TWILIO_ACCOUNT_SID', 'ACtest123')
os.environ.setdefault('TWILIO_AUTH_TOKEN', 'test_token')


class TestWhatsAppWebhookService:
    """Tests for WhatsAppWebhookService class"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked db"""
        from services.whatsapp_webhook_service import WhatsAppWebhookService
        return WhatsAppWebhookService(mock_db)

    @pytest.fixture
    def mock_client(self):
        """Create mock client"""
        client = MagicMock()
        client.id = 1
        client.name = "Test Client"
        client.first_name = "Test"
        client.whatsapp_opt_in = True
        client.whatsapp_verified = True
        client.whatsapp_number = "+15551234567"
        client.current_dispute_round = 1
        client.dispute_status = "active"
        return client

    # ==========================================================================
    # Test _normalize_phone
    # ==========================================================================

    def test_normalize_phone_with_whatsapp_prefix(self, service):
        """Test normalizing WhatsApp prefixed number"""
        result = service._normalize_phone("whatsapp:+15551234567")
        assert result == "+15551234567"

    def test_normalize_phone_without_prefix(self, service):
        """Test normalizing number without prefix"""
        result = service._normalize_phone("+15551234567")
        assert result == "+15551234567"

    def test_normalize_phone_with_formatting(self, service):
        """Test normalizing number with formatting characters"""
        result = service._normalize_phone("whatsapp:+1 (555) 123-4567")
        assert result == "+15551234567"

    def test_normalize_phone_empty(self, service):
        """Test normalizing empty string"""
        result = service._normalize_phone("")
        assert result == ""

    def test_normalize_phone_none(self, service):
        """Test normalizing None"""
        result = service._normalize_phone(None)
        assert result == ""

    # ==========================================================================
    # Test _get_phone_variants
    # ==========================================================================

    def test_get_phone_variants(self, service):
        """Test generating phone variants"""
        variants = service._get_phone_variants("+15551234567")
        assert "+15551234567" in variants
        assert "15551234567" in variants
        assert "5551234567" in variants

    def test_get_phone_variants_without_plus(self, service):
        """Test generating variants for number without plus"""
        variants = service._get_phone_variants("15551234567")
        assert "15551234567" in variants
        assert "+15551234567" in variants

    # ==========================================================================
    # Test _identify_client
    # ==========================================================================

    def test_identify_client_by_whatsapp_number(self, service, mock_db, mock_client):
        """Test identifying client by whatsapp_number field"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        result = service._identify_client("+15551234567")
        assert result == mock_client

    def test_identify_client_not_found(self, service, mock_db):
        """Test when client is not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service._identify_client("+15559999999")
        assert result is None

    def test_identify_client_empty_phone(self, service):
        """Test identifying with empty phone"""
        result = service._identify_client("")
        assert result is None

    # ==========================================================================
    # Test _infer_document_type
    # ==========================================================================

    def test_infer_document_type_license(self, service):
        """Test inferring driver's license from message"""
        result = service._infer_document_type("Here is my license")
        assert result == "drivers_license"

    def test_infer_document_type_ssn(self, service):
        """Test inferring SSN card from message"""
        result = service._infer_document_type("Sending my ssn card")
        assert result == "ssn_card"

    def test_infer_document_type_utility(self, service):
        """Test inferring utility bill from message"""
        result = service._infer_document_type("My utility bill attached")
        assert result == "utility_bill"

    def test_infer_document_type_credit_report(self, service):
        """Test inferring credit report from message"""
        result = service._infer_document_type("Here is my credit report")
        assert result == "credit_report"

    def test_infer_document_type_unknown(self, service):
        """Test when document type cannot be inferred"""
        result = service._infer_document_type("Random message")
        assert result == "pending_classification"

    def test_infer_document_type_empty(self, service):
        """Test with empty message"""
        result = service._infer_document_type("")
        assert result == "pending_classification"

    # ==========================================================================
    # Test _get_extension_from_content_type
    # ==========================================================================

    def test_get_extension_jpeg(self, service):
        """Test getting extension for JPEG"""
        assert service._get_extension_from_content_type("image/jpeg") == ".jpg"

    def test_get_extension_png(self, service):
        """Test getting extension for PNG"""
        assert service._get_extension_from_content_type("image/png") == ".png"

    def test_get_extension_pdf(self, service):
        """Test getting extension for PDF"""
        assert service._get_extension_from_content_type("application/pdf") == ".pdf"

    def test_get_extension_unknown(self, service):
        """Test getting extension for unknown type"""
        assert service._get_extension_from_content_type("application/unknown") == ".bin"

    # ==========================================================================
    # Test _build_twiml_response
    # ==========================================================================

    def test_build_twiml_response(self, service):
        """Test building TwiML response"""
        result = service._build_twiml_response("Hello, World!")
        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        assert "<Response>" in result
        assert "<Message>Hello, World!</Message>" in result
        assert "</Response>" in result

    def test_build_twiml_response_escapes_special_chars(self, service):
        """Test that special characters are escaped"""
        result = service._build_twiml_response("Test <script> & 'quote'")
        assert "&lt;script&gt;" in result
        assert "&amp;" in result
        assert "&apos;quote&apos;" in result

    # ==========================================================================
    # Test handle_status_callback
    # ==========================================================================

    def test_handle_status_callback_updates_message(self, service, mock_db):
        """Test status callback updates existing message"""
        mock_message = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_message

        result = service.handle_status_callback(
            message_sid="SM123",
            status="delivered"
        )

        assert result['success'] is True
        assert mock_message.status == "delivered"
        mock_db.commit.assert_called()

    def test_handle_status_callback_with_error(self, service, mock_db):
        """Test status callback with error info"""
        mock_message = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_message

        result = service.handle_status_callback(
            message_sid="SM123",
            status="failed",
            error_code="30001",
            error_message="Queue overflow"
        )

        assert result['success'] is True
        assert mock_message.status == "failed"
        assert mock_message.error_code == "30001"
        assert mock_message.error_message == "Queue overflow"

    def test_handle_status_callback_message_not_found(self, service, mock_db):
        """Test status callback when message doesn't exist"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.handle_status_callback(
            message_sid="SM_nonexistent",
            status="delivered"
        )

        assert result['success'] is True  # Still returns success

    # ==========================================================================
    # Test _handle_unidentified_sender
    # ==========================================================================

    def test_handle_unidentified_sender(self, service):
        """Test handling message from unknown sender"""
        mock_message = MagicMock()
        mock_message.id = 1

        result = service._handle_unidentified_sender(mock_message)

        assert result['success'] is True
        assert result['identified'] is False
        assert 'twiml' in result
        # Check for the message content (accounting for XML escaping)
        assert "find your account" in result['twiml'].lower()

    # ==========================================================================
    # Test _handle_text_message
    # ==========================================================================

    def test_handle_status_keyword(self, service, mock_client):
        """Test STATUS keyword response"""
        mock_message = MagicMock()
        mock_message.id = 1

        result = service._handle_text_message(mock_client, mock_message, "STATUS")

        assert result['success'] is True
        assert 'twiml' in result
        assert "Round 1" in result['twiml']

    def test_handle_help_keyword(self, service, mock_client):
        """Test HELP keyword response"""
        mock_message = MagicMock()
        mock_message.id = 1

        result = service._handle_text_message(mock_client, mock_message, "HELP")

        assert result['success'] is True
        assert 'twiml' in result
        assert "STATUS" in result['twiml']
        assert "STOP" in result['twiml']

    def test_handle_stop_keyword(self, service, mock_db, mock_client):
        """Test STOP keyword sets opt-out"""
        mock_message = MagicMock()
        mock_message.id = 1

        result = service._handle_text_message(mock_client, mock_message, "STOP")

        assert result['success'] is True
        assert mock_client.whatsapp_opt_in is False
        mock_db.commit.assert_called()

    def test_handle_regular_text(self, service, mock_client):
        """Test regular text message (no keyword)"""
        mock_message = MagicMock()
        mock_message.id = 1

        result = service._handle_text_message(mock_client, mock_message, "Hello there!")

        assert result['success'] is True
        assert 'twiml' not in result  # No auto-reply for regular text

    # ==========================================================================
    # Test process_incoming
    # ==========================================================================

    def test_process_incoming_creates_message_record(self, service, mock_db, mock_client):
        """Test that incoming message creates WhatsAppMessage record"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        result = service.process_incoming(
            from_number="whatsapp:+15551234567",
            to_number="whatsapp:+15559876543",
            body="Hello",
            message_sid="SM123",
            profile_name="Test User"
        )

        assert result['success'] is True
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_process_incoming_handles_unidentified(self, service, mock_db):
        """Test handling unidentified sender"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.process_incoming(
            from_number="whatsapp:+15559999999",
            to_number="whatsapp:+15559876543",
            body="Hello",
            message_sid="SM123"
        )

        assert result['success'] is True
        assert result['identified'] is False
        assert 'twiml' in result


class TestWhatsAppWebhookServiceMedia:
    """Tests for media handling"""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    @pytest.fixture
    def service(self, mock_db):
        from services.whatsapp_webhook_service import WhatsAppWebhookService
        return WhatsAppWebhookService(mock_db)

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.id = 1
        client.name = "Test Client"
        client.first_name = "Test"
        client.whatsapp_opt_in = True
        return client

    @patch('services.whatsapp_webhook_service.requests.get')
    def test_download_media_success(self, mock_get, service):
        """Test successful media download"""
        mock_response = MagicMock()
        mock_response.content = b'fake image data'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = service._download_media("https://api.twilio.com/media/123")

        assert result == b'fake image data'
        mock_get.assert_called_once()

    @patch('services.whatsapp_webhook_service.requests.get')
    def test_download_media_failure(self, mock_get, service):
        """Test media download failure"""
        mock_get.side_effect = Exception("Connection error")

        result = service._download_media("https://api.twilio.com/media/123")

        assert result is None

    def test_download_media_no_credentials(self, mock_db):
        """Test media download without credentials"""
        from services.whatsapp_webhook_service import WhatsAppWebhookService

        # Create service without credentials
        service = WhatsAppWebhookService(mock_db)
        service.twilio_account_sid = ''
        service.twilio_auth_token = ''

        result = service._download_media("https://api.twilio.com/media/123")

        assert result is None


class TestKeywordConstants:
    """Test keyword constants and document hints"""

    def test_keywords_defined(self):
        """Test that all expected keywords are defined"""
        from services.whatsapp_webhook_service import WhatsAppWebhookService

        assert 'STATUS' in WhatsAppWebhookService.KEYWORDS
        assert 'HELP' in WhatsAppWebhookService.KEYWORDS
        assert 'STOP' in WhatsAppWebhookService.KEYWORDS

    def test_document_hints_defined(self):
        """Test that document hints are defined"""
        from services.whatsapp_webhook_service import WhatsAppWebhookService

        assert 'license' in WhatsAppWebhookService.DOCUMENT_HINTS
        assert 'ssn' in WhatsAppWebhookService.DOCUMENT_HINTS
        assert 'utility' in WhatsAppWebhookService.DOCUMENT_HINTS
        assert 'report' in WhatsAppWebhookService.DOCUMENT_HINTS


class TestFactoryFunction:
    """Test the factory function"""

    def test_get_whatsapp_webhook_service(self):
        """Test factory function returns service instance"""
        from services.whatsapp_webhook_service import get_whatsapp_webhook_service, WhatsAppWebhookService

        mock_db = MagicMock()
        service = get_whatsapp_webhook_service(mock_db)

        assert isinstance(service, WhatsAppWebhookService)
        assert service.db == mock_db
