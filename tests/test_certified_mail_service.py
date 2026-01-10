"""
Comprehensive Unit Tests for Certified Mail Service

Tests cover:
- API configuration checks
- Mailing cost calculations
- Sending certified letters (mock mode and API mode)
- Delivery status checking
- Webhook handling
- Order retrieval functions
- Error handling and edge cases
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, mock_open
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.certified_mail_service import (
    is_certified_mail_configured,
    get_mailing_cost,
    send_certified_letter,
    check_delivery_status,
    handle_webhook,
    get_order_by_id,
    get_orders_by_client,
    get_pending_orders,
    _get_api_key,
    _get_headers,
    _get_multipart_headers,
    _get_client_delivery_folder,
    _generate_mock_tracking,
    _generate_mock_order_id,
    _download_delivery_proof,
    VALID_LETTER_TYPES,
    COST_BASE,
    COST_PER_PAGE,
    COST_RETURN_RECEIPT,
    API_BASE_URL,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def mock_order():
    """Create a mock CertifiedMailOrder object."""
    order = MagicMock()
    order.id = 1
    order.client_id = 100
    order.external_order_id = "ext_order_123"
    order.tracking_number = "9400111899223334445566"
    order.recipient_name = "Test Recipient"
    order.recipient_address = "123 Test St, Test City, TS 12345"
    order.recipient_type = "credit_bureau"
    order.document_type = "dispute_round_1"
    order.document_path = "/path/to/document.pdf"
    order.letter_type = "dispute_round_1"
    order.dispute_round = 1
    order.bureau = "Equifax"
    order.status = "submitted"
    order.cost = 12.50
    order.submitted_at = datetime.utcnow()
    order.mailed_at = None
    order.delivered_at = None
    order.delivery_proof_path = None
    order.webhook_data = {}
    order.created_at = datetime.utcnow()
    return order


@pytest.fixture
def sample_document_path(tmp_path):
    """Create a temporary PDF file for testing."""
    doc_path = tmp_path / "test_document.pdf"
    # Create a file with some content (~100KB to simulate 2 pages)
    doc_path.write_bytes(b"%PDF-1.4\n" + b"x" * 100000)
    return str(doc_path)


# =============================================================================
# Test Class: Configuration Functions
# =============================================================================

class TestConfiguration:
    """Tests for API configuration functions."""

    def test_is_certified_mail_configured_with_api_key(self):
        """Test configuration check with API key set."""
        with patch.dict(os.environ, {'SENDCERTIFIEDMAIL_API_KEY': 'test-api-key'}):
            assert is_certified_mail_configured() is True

    def test_is_certified_mail_configured_without_api_key(self):
        """Test configuration check without API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if it exists
            os.environ.pop('SENDCERTIFIEDMAIL_API_KEY', None)
            assert is_certified_mail_configured() is False

    def test_is_certified_mail_configured_empty_api_key(self):
        """Test configuration check with empty API key."""
        with patch.dict(os.environ, {'SENDCERTIFIEDMAIL_API_KEY': ''}):
            assert is_certified_mail_configured() is False

    def test_get_api_key_returns_key(self):
        """Test getting API key from environment."""
        with patch.dict(os.environ, {'SENDCERTIFIEDMAIL_API_KEY': 'my-secret-key'}):
            assert _get_api_key() == 'my-secret-key'

    def test_get_api_key_returns_none_when_not_set(self):
        """Test getting API key returns None when not set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('SENDCERTIFIEDMAIL_API_KEY', None)
            assert _get_api_key() is None

    def test_get_headers_includes_authorization(self):
        """Test headers include authorization bearer token."""
        with patch.dict(os.environ, {'SENDCERTIFIEDMAIL_API_KEY': 'test-key'}):
            headers = _get_headers()
            assert headers['Authorization'] == 'Bearer test-key'
            assert headers['Content-Type'] == 'application/json'

    def test_get_multipart_headers(self):
        """Test multipart headers for file uploads."""
        with patch.dict(os.environ, {'SENDCERTIFIEDMAIL_API_KEY': 'test-key'}):
            headers = _get_multipart_headers()
            assert headers['Authorization'] == 'Bearer test-key'
            assert 'Content-Type' not in headers


# =============================================================================
# Test Class: Helper Functions
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_client_delivery_folder_creates_folder(self):
        """Test delivery folder creation."""
        with patch('os.makedirs') as mock_makedirs:
            folder = _get_client_delivery_folder(123)
            assert folder == "static/client_uploads/123/certified_mail"
            mock_makedirs.assert_called_once_with(
                "static/client_uploads/123/certified_mail",
                exist_ok=True
            )

    def test_generate_mock_tracking_format(self):
        """Test mock tracking number format."""
        tracking = _generate_mock_tracking()
        assert tracking.startswith("MOCK")
        assert len(tracking) == 20  # MOCK + 16 hex chars

    def test_generate_mock_tracking_unique(self):
        """Test mock tracking numbers are unique."""
        tracking1 = _generate_mock_tracking()
        tracking2 = _generate_mock_tracking()
        assert tracking1 != tracking2

    def test_generate_mock_order_id_format(self):
        """Test mock order ID format."""
        order_id = _generate_mock_order_id()
        assert order_id.startswith("mock_")
        assert len(order_id) == 17  # mock_ + 12 hex chars

    def test_generate_mock_order_id_unique(self):
        """Test mock order IDs are unique."""
        id1 = _generate_mock_order_id()
        id2 = _generate_mock_order_id()
        assert id1 != id2


# =============================================================================
# Test Class: Mailing Cost Calculations
# =============================================================================

class TestMailingCost:
    """Tests for mailing cost calculations."""

    def test_get_mailing_cost_single_page(self):
        """Test cost for single page document."""
        cost = get_mailing_cost(1, "certified")

        assert cost['base_cost'] == COST_BASE
        assert cost['page_cost'] == 0
        assert cost['return_receipt_cost'] == 0
        assert cost['total_cost'] == COST_BASE
        assert cost['pages'] == 1
        assert cost['mail_class'] == "certified"

    def test_get_mailing_cost_multiple_pages(self):
        """Test cost for multi-page document."""
        cost = get_mailing_cost(5, "certified")

        expected_page_cost = 4 * COST_PER_PAGE  # 4 additional pages
        assert cost['base_cost'] == COST_BASE
        assert cost['page_cost'] == expected_page_cost
        assert cost['total_cost'] == COST_BASE + expected_page_cost

    def test_get_mailing_cost_with_return_receipt(self):
        """Test cost with return receipt."""
        cost = get_mailing_cost(1, "certified_return_receipt")

        assert cost['return_receipt_cost'] == COST_RETURN_RECEIPT
        assert cost['total_cost'] == COST_BASE + COST_RETURN_RECEIPT

    def test_get_mailing_cost_multiple_pages_with_return_receipt(self):
        """Test cost for multi-page with return receipt."""
        cost = get_mailing_cost(3, "certified_return_receipt")

        expected_page_cost = 2 * COST_PER_PAGE
        expected_total = COST_BASE + expected_page_cost + COST_RETURN_RECEIPT
        assert cost['total_cost'] == expected_total

    def test_get_mailing_cost_zero_pages_treated_as_one(self):
        """Test zero pages treated as one page."""
        cost = get_mailing_cost(0, "certified")
        assert cost['pages'] == 1
        assert cost['page_cost'] == 0

    def test_get_mailing_cost_negative_pages_treated_as_one(self):
        """Test negative pages treated as one page."""
        cost = get_mailing_cost(-5, "certified")
        assert cost['pages'] == 1
        assert cost['page_cost'] == 0

    def test_get_mailing_cost_return_keyword_case_insensitive(self):
        """Test return receipt detection is case insensitive."""
        cost = get_mailing_cost(1, "CERTIFIED_RETURN_RECEIPT")
        assert cost['return_receipt_cost'] == COST_RETURN_RECEIPT

    def test_get_mailing_cost_values_rounded(self):
        """Test that all costs are rounded to 2 decimal places."""
        cost = get_mailing_cost(10, "certified_return_receipt")

        assert cost['base_cost'] == round(cost['base_cost'], 2)
        assert cost['page_cost'] == round(cost['page_cost'], 2)
        assert cost['total_cost'] == round(cost['total_cost'], 2)


# =============================================================================
# Test Class: Send Certified Letter - Mock Mode
# =============================================================================

class TestSendCertifiedLetterMockMode:
    """Tests for sending certified letters in mock mode (no API key)."""

    def test_send_letter_mock_mode_success(self, mock_session, sample_document_path):
        """Test sending letter in mock mode creates order successfully."""
        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=False):
                with patch('services.certified_mail_service.CertifiedMailOrder') as MockOrder:
                    mock_order_instance = MagicMock()
                    mock_order_instance.id = 1
                    MockOrder.return_value = mock_order_instance

                    result = send_certified_letter(
                        client_id=100,
                        recipient_name="Test Recipient",
                        recipient_address="123 Test St",
                        document_path=sample_document_path,
                        letter_type="dispute_round_1",
                        bureau="Equifax",
                        dispute_round=1
                    )

                    assert result['success'] is True
                    assert result['mock_mode'] is True
                    assert result['order_id'] == 1
                    assert result['external_order_id'].startswith("mock_")
                    assert result['tracking_number'].startswith("MOCK")
                    assert result['error'] is None

    def test_send_letter_mock_mode_sets_correct_status(self, mock_session, sample_document_path):
        """Test mock mode sets status to mock_pending."""
        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=False):
                with patch('services.certified_mail_service.CertifiedMailOrder') as MockOrder:
                    mock_order_instance = MagicMock()
                    mock_order_instance.id = 1
                    MockOrder.return_value = mock_order_instance

                    send_certified_letter(
                        client_id=100,
                        recipient_name="Test",
                        recipient_address="123 Test St",
                        document_path=sample_document_path,
                        letter_type="dispute_round_1"
                    )

                    call_kwargs = MockOrder.call_args[1]
                    assert call_kwargs['status'] == 'mock_pending'
                    assert call_kwargs['webhook_data']['mock_mode'] is True


# =============================================================================
# Test Class: Send Certified Letter - Validation
# =============================================================================

class TestSendCertifiedLetterValidation:
    """Tests for input validation when sending certified letters."""

    def test_send_letter_invalid_letter_type(self, mock_session):
        """Test sending with invalid letter type returns error."""
        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = send_certified_letter(
                client_id=100,
                recipient_name="Test",
                recipient_address="123 Test St",
                document_path="/path/to/doc.pdf",
                letter_type="invalid_type"
            )

            assert result['success'] is False
            assert "Invalid letter_type" in result['error']
            assert all(lt in result['error'] for lt in VALID_LETTER_TYPES[:3])

    def test_send_letter_document_not_found(self, mock_session):
        """Test sending with non-existent document returns error."""
        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = send_certified_letter(
                client_id=100,
                recipient_name="Test",
                recipient_address="123 Test St",
                document_path="/nonexistent/document.pdf",
                letter_type="dispute_round_1"
            )

            assert result['success'] is False
            assert "Document not found" in result['error']

    def test_send_letter_all_valid_letter_types(self, mock_session, sample_document_path):
        """Test all valid letter types are accepted."""
        for letter_type in VALID_LETTER_TYPES:
            with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
                with patch('services.certified_mail_service.is_certified_mail_configured', return_value=False):
                    with patch('services.certified_mail_service.CertifiedMailOrder') as MockOrder:
                        mock_order_instance = MagicMock()
                        mock_order_instance.id = 1
                        MockOrder.return_value = mock_order_instance

                        result = send_certified_letter(
                            client_id=100,
                            recipient_name="Test",
                            recipient_address="123 Test St",
                            document_path=sample_document_path,
                            letter_type=letter_type
                        )

                        assert result['success'] is True, f"Failed for letter_type: {letter_type}"


# =============================================================================
# Test Class: Send Certified Letter - API Mode
# =============================================================================

class TestSendCertifiedLetterAPIMode:
    """Tests for sending certified letters with API integration."""

    def test_send_letter_api_mode_success(self, mock_session, sample_document_path):
        """Test sending letter via API successfully."""
        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 201
        mock_upload_response.json.return_value = {"document_id": "doc_123"}

        mock_order_response = MagicMock()
        mock_order_response.status_code = 201
        mock_order_response.json.return_value = {
            "order_id": "order_456",
            "tracking_number": "9400111899223334445566",
            "cost": 12.50
        }

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.post') as mock_post:
                    mock_post.side_effect = [mock_upload_response, mock_order_response]
                    with patch('services.certified_mail_service.CertifiedMailOrder') as MockOrder:
                        mock_order_instance = MagicMock()
                        mock_order_instance.id = 1
                        MockOrder.return_value = mock_order_instance

                        result = send_certified_letter(
                            client_id=100,
                            recipient_name="Test Recipient",
                            recipient_address="123 Test St",
                            document_path=sample_document_path,
                            letter_type="dispute_round_1",
                            bureau="Equifax"
                        )

                        assert result['success'] is True
                        assert result['mock_mode'] is False
                        assert result['external_order_id'] == "order_456"
                        assert result['tracking_number'] == "9400111899223334445566"
                        assert result['estimated_cost'] == 12.50

    def test_send_letter_api_upload_failure(self, mock_session, sample_document_path):
        """Test handling upload failure."""
        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 500
        mock_upload_response.text = "Internal Server Error"

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.post', return_value=mock_upload_response):
                    result = send_certified_letter(
                        client_id=100,
                        recipient_name="Test",
                        recipient_address="123 Test St",
                        document_path=sample_document_path,
                        letter_type="dispute_round_1"
                    )

                    assert result['success'] is False
                    assert "Document upload failed" in result['error']
                    assert "500" in result['error']

    def test_send_letter_api_order_creation_failure(self, mock_session, sample_document_path):
        """Test handling order creation failure."""
        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 200
        mock_upload_response.json.return_value = {"document_id": "doc_123"}

        mock_order_response = MagicMock()
        mock_order_response.status_code = 400
        mock_order_response.text = "Bad Request"

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.post') as mock_post:
                    mock_post.side_effect = [mock_upload_response, mock_order_response]

                    result = send_certified_letter(
                        client_id=100,
                        recipient_name="Test",
                        recipient_address="123 Test St",
                        document_path=sample_document_path,
                        letter_type="dispute_round_1"
                    )

                    assert result['success'] is False
                    assert "Order creation failed" in result['error']

    def test_send_letter_network_error(self, mock_session, sample_document_path):
        """Test handling network errors."""
        import requests

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.post') as mock_post:
                    mock_post.side_effect = requests.RequestException("Connection timeout")

                    result = send_certified_letter(
                        client_id=100,
                        recipient_name="Test",
                        recipient_address="123 Test St",
                        document_path=sample_document_path,
                        letter_type="dispute_round_1"
                    )

                    assert result['success'] is False
                    assert "Network error" in result['error']

    def test_send_letter_database_error(self, mock_session, sample_document_path):
        """Test handling database errors."""
        mock_session.add.side_effect = Exception("Database connection lost")

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=False):
                with patch('services.certified_mail_service.CertifiedMailOrder'):
                    result = send_certified_letter(
                        client_id=100,
                        recipient_name="Test",
                        recipient_address="123 Test St",
                        document_path=sample_document_path,
                        letter_type="dispute_round_1"
                    )

                    assert result['success'] is False
                    assert "Error creating certified mail order" in result['error']
                    mock_session.rollback.assert_called_once()


# =============================================================================
# Test Class: Check Delivery Status
# =============================================================================

class TestCheckDeliveryStatus:
    """Tests for checking delivery status."""

    def test_check_status_order_not_found(self, mock_session):
        """Test checking status for non-existent order."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = check_delivery_status(999)

            assert result['success'] is False
            assert "not found" in result['error']
            assert result['order_id'] == 999

    def test_check_status_mock_order(self, mock_session, mock_order):
        """Test checking status for mock order returns cached data."""
        mock_order.status = "mock_pending"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = check_delivery_status(1)

            assert result['success'] is True
            assert result['mock_mode'] is True
            assert result['status'] == "mock_pending"

    def test_check_status_api_not_configured(self, mock_session, mock_order):
        """Test checking status when API is not configured."""
        mock_order.status = "submitted"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=False):
                result = check_delivery_status(1)

                assert result['success'] is True
                assert result['mock_mode'] is True

    def test_check_status_no_external_order_id(self, mock_session, mock_order):
        """Test checking status when no external order ID."""
        mock_order.status = "submitted"
        mock_order.external_order_id = None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                result = check_delivery_status(1)

                assert result['success'] is False
                assert "No external order ID" in result['error']

    def test_check_status_api_success(self, mock_session, mock_order):
        """Test checking status via API successfully."""
        mock_order.status = "submitted"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "in_transit",
            "tracking_number": "9400111899223334445566"
        }

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.get', return_value=mock_response):
                    result = check_delivery_status(1)

                    assert result['success'] is True
                    assert result['status'] == "in_transit"
                    assert result['mock_mode'] is False

    def test_check_status_api_404(self, mock_session, mock_order):
        """Test checking status when API returns 404."""
        mock_order.status = "submitted"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.get', return_value=mock_response):
                    result = check_delivery_status(1)

                    assert result['success'] is False
                    assert result['status'] == "not_found"

    def test_check_status_updates_delivered_timestamp(self, mock_session, mock_order):
        """Test checking status updates delivered_at timestamp."""
        mock_order.status = "submitted"
        mock_order.delivered_at = None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "delivered",
            "delivered_at": "2025-01-15T10:30:00Z"
        }

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.get', return_value=mock_response):
                    result = check_delivery_status(1)

                    assert result['success'] is True
                    assert result['status'] == "delivered"
                    mock_session.commit.assert_called()

    def test_check_status_normalizes_status(self, mock_session, mock_order):
        """Test status normalization (e.g., 'canceled' -> 'cancelled')."""
        mock_order.status = "submitted"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "canceled"}

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.get', return_value=mock_response):
                    result = check_delivery_status(1)

                    assert result['status'] == "cancelled"

    def test_check_status_network_error(self, mock_session, mock_order):
        """Test checking status handles network errors."""
        import requests

        mock_order.status = "submitted"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.get') as mock_get:
                    mock_get.side_effect = requests.RequestException("Timeout")

                    result = check_delivery_status(1)

                    assert result['success'] is False
                    assert "Network error" in result['error']


# =============================================================================
# Test Class: Download Delivery Proof
# =============================================================================

class TestDownloadDeliveryProof:
    """Tests for downloading delivery proof documents."""

    def test_download_proof_success(self, mock_order):
        """Test downloading delivery proof successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4\nproof content"

        with patch('services.certified_mail_service.requests.get', return_value=mock_response):
            with patch('services.certified_mail_service._get_client_delivery_folder', return_value='/tmp/delivery'):
                with patch('builtins.open', mock_open()) as mock_file:
                    result = _download_delivery_proof(mock_order, "https://example.com/proof.pdf")

                    assert result is not None
                    assert "delivery_proof_" in result
                    assert result.endswith(".pdf")

    def test_download_proof_failure(self, mock_order):
        """Test handling download failure."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('services.certified_mail_service.requests.get', return_value=mock_response):
            result = _download_delivery_proof(mock_order, "https://example.com/proof.pdf")

            assert result is None

    def test_download_proof_exception(self, mock_order):
        """Test handling download exception."""
        with patch('services.certified_mail_service.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = _download_delivery_proof(mock_order, "https://example.com/proof.pdf")

            assert result is None


# =============================================================================
# Test Class: Handle Webhook
# =============================================================================

class TestHandleWebhook:
    """Tests for webhook handling."""

    def test_webhook_no_order_id(self, mock_session):
        """Test webhook without order ID returns error."""
        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = handle_webhook({"status": "delivered"})

            assert result['success'] is False
            assert "No order_id" in result['error']

    def test_webhook_order_not_found(self, mock_session):
        """Test webhook for non-existent order."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = handle_webhook({"order_id": "unknown_123"})

            assert result['success'] is False
            assert "No order found" in result['error']

    def test_webhook_updates_status(self, mock_session, mock_order):
        """Test webhook updates order status."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = handle_webhook({
                "order_id": "ext_order_123",
                "event": "order.mailed"
            })

            assert result['success'] is True
            assert result['order_id'] == mock_order.id
            assert "Updated status" in result['action_taken']
            mock_session.commit.assert_called()

    def test_webhook_event_type_variations(self, mock_session, mock_order):
        """Test webhook handles different event type field names."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        # Test with 'type' field
        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = handle_webhook({
                "id": "ext_order_123",
                "type": "in_transit"
            })
            assert result['success'] is True

    def test_webhook_delivered_downloads_proof(self, mock_session, mock_order):
        """Test webhook downloads proof on delivery."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service._download_delivery_proof', return_value='/path/proof.pdf'):
                result = handle_webhook({
                    "order_id": "ext_order_123",
                    "event": "order.delivered",
                    "delivery_proof_url": "https://example.com/proof.pdf"
                })

                assert result['success'] is True
                assert "downloaded delivery proof" in result['action_taken']

    def test_webhook_updates_tracking_number(self, mock_session, mock_order):
        """Test webhook updates tracking number if provided."""
        mock_order.tracking_number = None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = handle_webhook({
                "order_id": "ext_order_123",
                "event": "order.mailed",
                "tracking_number": "9400111899223334445566"
            })

            assert result['success'] is True
            assert "updated tracking number" in result['action_taken']

    def test_webhook_sets_mailed_at_timestamp(self, mock_session, mock_order):
        """Test webhook sets mailed_at timestamp."""
        mock_order.mailed_at = None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = handle_webhook({
                "order_id": "ext_order_123",
                "event": "order.mailed",
                "mailed_at": "2025-01-15T09:00:00Z"
            })

            assert result['success'] is True
            assert "set mailed_at timestamp" in result['action_taken']

    def test_webhook_database_error(self, mock_session, mock_order):
        """Test webhook handles database errors."""
        mock_session.commit.side_effect = Exception("Database error")
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = handle_webhook({
                "order_id": "ext_order_123",
                "event": "order.mailed"
            })

            assert result['success'] is False
            assert "Error processing webhook" in result['error']
            mock_session.rollback.assert_called()


# =============================================================================
# Test Class: Get Order By ID
# =============================================================================

class TestGetOrderById:
    """Tests for getting orders by ID."""

    def test_get_order_found(self, mock_session, mock_order):
        """Test getting existing order."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = get_order_by_id(1)

            assert result is not None
            assert result['id'] == mock_order.id
            assert result['client_id'] == mock_order.client_id
            assert result['tracking_number'] == mock_order.tracking_number
            assert result['status'] == mock_order.status

    def test_get_order_not_found(self, mock_session):
        """Test getting non-existent order."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = get_order_by_id(999)

            assert result is None

    def test_get_order_includes_all_fields(self, mock_session, mock_order):
        """Test get order returns all expected fields."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = get_order_by_id(1)

            expected_fields = [
                'id', 'client_id', 'external_order_id', 'tracking_number',
                'recipient_name', 'recipient_address', 'letter_type',
                'bureau', 'dispute_round', 'status', 'cost',
                'submitted_at', 'mailed_at', 'delivered_at',
                'delivery_proof_path', 'created_at'
            ]
            for field in expected_fields:
                assert field in result


# =============================================================================
# Test Class: Get Orders By Client
# =============================================================================

class TestGetOrdersByClient:
    """Tests for getting orders by client."""

    def test_get_orders_by_client_found(self, mock_session, mock_order):
        """Test getting orders for client with orders."""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_order]
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = get_orders_by_client(100)

            assert len(result) == 1
            assert result[0]['id'] == mock_order.id
            # Note: get_orders_by_client does not include client_id in response
            assert result[0]['external_order_id'] is not None

    def test_get_orders_by_client_empty(self, mock_session):
        """Test getting orders for client with no orders."""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = get_orders_by_client(100)

            assert result == []

    def test_get_orders_by_client_multiple(self, mock_session):
        """Test getting multiple orders for client."""
        orders = [MagicMock(id=i) for i in range(5)]
        for i, order in enumerate(orders):
            order.external_order_id = f"ext_{i}"
            order.tracking_number = f"track_{i}"
            order.recipient_name = "Test"
            order.letter_type = "dispute_round_1"
            order.bureau = "Equifax"
            order.dispute_round = 1
            order.status = "submitted"
            order.cost = 12.50
            order.submitted_at = datetime.utcnow()
            order.mailed_at = None
            order.delivered_at = None
            order.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = orders
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = get_orders_by_client(100)

            assert len(result) == 5


# =============================================================================
# Test Class: Get Pending Orders
# =============================================================================

class TestGetPendingOrders:
    """Tests for getting pending orders."""

    def test_get_pending_orders_found(self, mock_session, mock_order):
        """Test getting pending orders."""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_order]
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = get_pending_orders()

            assert len(result) == 1

    def test_get_pending_orders_empty(self, mock_session):
        """Test getting pending orders when none exist."""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = get_pending_orders()

            assert result == []

    def test_get_pending_orders_returns_expected_fields(self, mock_session):
        """Test pending orders return expected fields."""
        order = MagicMock()
        order.id = 1
        order.client_id = 100
        order.external_order_id = "ext_123"
        order.tracking_number = "track_123"
        order.recipient_name = "Test"
        order.letter_type = "dispute_round_1"
        order.status = "pending"
        order.submitted_at = datetime.utcnow()
        order.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [order]
        mock_session.query.return_value = mock_query

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            result = get_pending_orders()

            expected_fields = [
                'id', 'client_id', 'external_order_id', 'tracking_number',
                'recipient_name', 'letter_type', 'status', 'submitted_at', 'created_at'
            ]
            for field in expected_fields:
                assert field in result[0]


# =============================================================================
# Test Class: Constants and Configuration
# =============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_valid_letter_types_not_empty(self):
        """Test valid letter types list is not empty."""
        assert len(VALID_LETTER_TYPES) > 0

    def test_valid_letter_types_contains_expected(self):
        """Test valid letter types contains expected types."""
        assert "dispute_round_1" in VALID_LETTER_TYPES
        assert "dispute_round_2" in VALID_LETTER_TYPES
        assert "intent_to_sue" in VALID_LETTER_TYPES
        assert "validation_request" in VALID_LETTER_TYPES
        assert "freeze_request" in VALID_LETTER_TYPES

    def test_cost_constants_positive(self):
        """Test cost constants are positive values."""
        assert COST_BASE > 0
        assert COST_PER_PAGE > 0
        assert COST_RETURN_RECEIPT > 0

    def test_api_base_url_https(self):
        """Test API base URL uses HTTPS."""
        assert API_BASE_URL.startswith("https://")


# =============================================================================
# Test Class: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_send_letter_with_bureau_sets_recipient_type(self, mock_session, sample_document_path):
        """Test sending with bureau sets recipient_type to credit_bureau."""
        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=False):
                with patch('services.certified_mail_service.CertifiedMailOrder') as MockOrder:
                    mock_order_instance = MagicMock()
                    mock_order_instance.id = 1
                    MockOrder.return_value = mock_order_instance

                    send_certified_letter(
                        client_id=100,
                        recipient_name="Test",
                        recipient_address="123 Test St",
                        document_path=sample_document_path,
                        letter_type="dispute_round_1",
                        bureau="Equifax"
                    )

                    call_kwargs = MockOrder.call_args[1]
                    assert call_kwargs['recipient_type'] == "credit_bureau"

    def test_send_letter_without_bureau_sets_recipient_type_other(self, mock_session, sample_document_path):
        """Test sending without bureau sets recipient_type to other."""
        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=False):
                with patch('services.certified_mail_service.CertifiedMailOrder') as MockOrder:
                    mock_order_instance = MagicMock()
                    mock_order_instance.id = 1
                    MockOrder.return_value = mock_order_instance

                    send_certified_letter(
                        client_id=100,
                        recipient_name="Test",
                        recipient_address="123 Test St",
                        document_path=sample_document_path,
                        letter_type="intent_to_sue"
                    )

                    call_kwargs = MockOrder.call_args[1]
                    assert call_kwargs['recipient_type'] == "other"

    def test_check_status_handles_invalid_datetime_format(self, mock_session, mock_order):
        """Test status check handles invalid datetime gracefully."""
        mock_order.status = "submitted"
        mock_order.delivered_at = None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "delivered",
            "delivered_at": "invalid-date-format"
        }

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.get', return_value=mock_response):
                    result = check_delivery_status(1)

                    # Should still succeed, using fallback datetime
                    assert result['success'] is True

    def test_webhook_handles_proof_url_variations(self, mock_session, mock_order):
        """Test webhook handles different proof URL field names."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_order
        mock_session.query.return_value = mock_query

        # Test with return_receipt_url
        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service._download_delivery_proof', return_value='/path/proof.pdf'):
                result = handle_webhook({
                    "order_id": "ext_order_123",
                    "event": "order.delivered",
                    "return_receipt_url": "https://example.com/receipt.pdf"
                })
                assert result['success'] is True

    def test_session_always_closed(self, mock_session, sample_document_path):
        """Test database session is always closed even on error."""
        mock_session.add.side_effect = Exception("Error")

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=False):
                with patch('services.certified_mail_service.CertifiedMailOrder'):
                    send_certified_letter(
                        client_id=100,
                        recipient_name="Test",
                        recipient_address="123 Test St",
                        document_path=sample_document_path,
                        letter_type="dispute_round_1"
                    )

                    mock_session.close.assert_called()

    def test_api_response_uses_alternative_field_names(self, mock_session, sample_document_path):
        """Test API response handling with alternative field names."""
        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 200
        mock_upload_response.json.return_value = {"id": "doc_123"}  # 'id' instead of 'document_id'

        mock_order_response = MagicMock()
        mock_order_response.status_code = 200
        mock_order_response.json.return_value = {"id": "order_456"}  # 'id' instead of 'order_id'

        with patch('services.certified_mail_service.SessionLocal', return_value=mock_session):
            with patch('services.certified_mail_service.is_certified_mail_configured', return_value=True):
                with patch('services.certified_mail_service.requests.post') as mock_post:
                    mock_post.side_effect = [mock_upload_response, mock_order_response]
                    with patch('services.certified_mail_service.CertifiedMailOrder') as MockOrder:
                        mock_order_instance = MagicMock()
                        mock_order_instance.id = 1
                        MockOrder.return_value = mock_order_instance

                        result = send_certified_letter(
                            client_id=100,
                            recipient_name="Test",
                            recipient_address="123 Test St",
                            document_path=sample_document_path,
                            letter_type="dispute_round_1"
                        )

                        assert result['success'] is True
                        assert result['external_order_id'] == "order_456"
