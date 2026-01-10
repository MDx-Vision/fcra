"""
Comprehensive Unit Tests for SendCertified Integration Service.

Tests cover:
- Service initialization and configuration
- API credential loading from database
- Connection testing
- Certified mail creation
- Tracking status retrieval
- Return receipt download
- Account balance checking
- Configuration functions
- Status retrieval functions
- Mailing statistics
- Error handling and edge cases
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sendcertified_service import (
    SendCertifiedService,
    get_sendcertified_service,
    configure_sendcertified,
    get_sendcertified_status,
    get_mailing_statistics,
    SANDBOX_BASE_URL,
    PRODUCTION_BASE_URL,
    SERVICE_NAME,
    DISPLAY_NAME,
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
    order.recipient_address = "123 Test St\nTest City, TS, 12345"
    order.recipient_type = "credit_bureau"
    order.document_type = "dispute_round_1"
    order.letter_type = "dispute_round_1"
    order.dispute_round = 1
    order.bureau = "Equifax"
    order.status = "submitted"
    order.cost = 12.50
    order.submitted_at = datetime.utcnow()
    order.delivered_at = None
    order.webhook_data = {}
    order.created_at = datetime.utcnow()
    return order


@pytest.fixture
def mock_connection():
    """Create a mock IntegrationConnection object."""
    connection = MagicMock()
    connection.id = 1
    connection.service_name = SERVICE_NAME
    connection.display_name = DISPLAY_NAME
    connection.api_key_encrypted = "encrypted_key"
    connection.api_secret_encrypted = "encrypted_secret"
    connection.is_sandbox = True
    connection.base_url = SANDBOX_BASE_URL
    connection.is_active = True
    connection.connection_status = "connected"
    connection.last_connected_at = datetime.utcnow()
    connection.last_error = None
    connection.created_at = datetime.utcnow()
    connection.updated_at = datetime.utcnow()
    return connection


@pytest.fixture
def sample_address():
    """Create a sample address dictionary."""
    return {
        "street": "123 Main St",
        "address_line_2": "Suite 100",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
        "country": "US",
    }


@pytest.fixture
def sample_document():
    """Create sample PDF document bytes."""
    return b"%PDF-1.4\nTest document content for certified mail"


# =============================================================================
# Test Class: Constants
# =============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_sandbox_base_url(self):
        """Test sandbox base URL is correctly set."""
        assert SANDBOX_BASE_URL == "https://sandbox.sendcertified.com/api/v1"

    def test_production_base_url(self):
        """Test production base URL is correctly set."""
        assert PRODUCTION_BASE_URL == "https://api.sendcertified.com/api/v1"

    def test_service_name(self):
        """Test service name is correctly set."""
        assert SERVICE_NAME == "sendcertified"

    def test_display_name(self):
        """Test display name is correctly set."""
        assert DISPLAY_NAME == "SendCertified"


# =============================================================================
# Test Class: SendCertifiedService Initialization
# =============================================================================

class TestSendCertifiedServiceInit:
    """Tests for SendCertifiedService initialization."""

    def test_init_with_api_credentials(self):
        """Test initialization with explicit API credentials."""
        service = SendCertifiedService(
            api_key="test_api_key",
            api_secret="test_api_secret",
            sandbox=True
        )
        assert service.api_key == "test_api_key"
        assert service.api_secret == "test_api_secret"
        assert service.sandbox is True
        assert service.base_url == SANDBOX_BASE_URL

    def test_init_production_mode(self):
        """Test initialization in production mode."""
        service = SendCertifiedService(
            api_key="test_api_key",
            api_secret="test_api_secret",
            sandbox=False
        )
        assert service.sandbox is False
        assert service.base_url == PRODUCTION_BASE_URL

    def test_init_default_sandbox_mode(self):
        """Test sandbox mode is enabled by default."""
        service = SendCertifiedService(
            api_key="test_api_key",
            api_secret="test_api_secret"
        )
        assert service.sandbox is True

    @patch('services.encryption.decrypt_value')
    @patch('services.sendcertified_service.SessionLocal')
    def test_init_loads_credentials_from_db(self, mock_session_class, mock_decrypt):
        """Test initialization loads credentials from database when not provided."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_connection = MagicMock()
        mock_connection.id = 1
        mock_connection.api_key_encrypted = "encrypted_key"
        mock_connection.api_secret_encrypted = "encrypted_secret"
        mock_connection.is_sandbox = False
        mock_session.query().filter_by().first.return_value = mock_connection

        mock_decrypt.side_effect = ["decrypted_key", "decrypted_secret"]

        service = SendCertifiedService()

        assert service.api_key == "decrypted_key"
        assert service.api_secret == "decrypted_secret"
        assert service.sandbox is False
        assert service.base_url == PRODUCTION_BASE_URL
        assert service._integration_id == 1

    @patch('services.sendcertified_service.SessionLocal')
    def test_init_handles_no_db_connection(self, mock_session_class):
        """Test initialization handles missing database connection gracefully."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = SendCertifiedService()

        assert service.api_key is None
        assert service.api_secret is None

    @patch('services.sendcertified_service.SessionLocal')
    def test_init_handles_db_error(self, mock_session_class):
        """Test initialization handles database errors gracefully."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.side_effect = Exception("DB Error")

        service = SendCertifiedService()

        assert service.api_key is None
        mock_session.close.assert_called()


# =============================================================================
# Test Class: is_configured Method
# =============================================================================

class TestIsConfigured:
    """Tests for is_configured method."""

    def test_is_configured_with_both_credentials(self):
        """Test is_configured returns True with both credentials."""
        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        assert service.is_configured() is True

    def test_is_configured_missing_api_key(self):
        """Test is_configured returns False without API key."""
        service = SendCertifiedService(
            api_key=None,
            api_secret="test_secret"
        )
        assert service.is_configured() is False

    def test_is_configured_missing_api_secret(self):
        """Test is_configured returns False without API secret."""
        service = SendCertifiedService(
            api_key="test_key",
            api_secret=None
        )
        assert service.is_configured() is False

    def test_is_configured_both_missing(self):
        """Test is_configured returns False with both credentials missing."""
        service = SendCertifiedService(
            api_key=None,
            api_secret=None
        )
        assert service.is_configured() is False

    def test_is_configured_empty_credentials(self):
        """Test is_configured returns False with empty credentials."""
        service = SendCertifiedService(
            api_key="",
            api_secret=""
        )
        assert service.is_configured() is False


# =============================================================================
# Test Class: _get_headers Method
# =============================================================================

class TestGetHeaders:
    """Tests for _get_headers method."""

    def test_get_headers_success(self):
        """Test headers are correctly formatted."""
        service = SendCertifiedService(
            api_key="test_api_key",
            api_secret="test_api_secret"
        )
        headers = service._get_headers()

        assert headers["Authorization"] == "Bearer test_api_key"
        assert headers["X-API-Secret"] == "test_api_secret"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    def test_get_headers_empty_credentials(self):
        """Test headers with empty credentials."""
        service = SendCertifiedService(
            api_key=None,
            api_secret=None
        )
        headers = service._get_headers()

        assert headers["Authorization"] == "Bearer "
        assert headers["X-API-Secret"] == ""


# =============================================================================
# Test Class: test_connection Method
# =============================================================================

class TestTestConnection:
    """Tests for test_connection method."""

    def test_connection_not_configured(self):
        """Test connection test when not configured."""
        service = SendCertifiedService(api_key=None, api_secret=None)
        result = service.test_connection()

        assert result is False

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_connection_success(self, mock_session_class, mock_get):
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.test_connection()

        assert result is True
        mock_get.assert_called_once()
        assert "account/status" in mock_get.call_args[0][0]

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_connection_failure_401(self, mock_session_class, mock_get):
        """Test connection test with authentication failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.test_connection()

        assert result is False

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_connection_timeout(self, mock_session_class, mock_get):
        """Test connection test with timeout."""
        import requests
        mock_get.side_effect = requests.Timeout("Connection timeout")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.test_connection()

        assert result is False

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_connection_network_error(self, mock_session_class, mock_get):
        """Test connection test with network error."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.test_connection()

        assert result is False


# =============================================================================
# Test Class: _update_connection_status Method
# =============================================================================

class TestUpdateConnectionStatus:
    """Tests for _update_connection_status method."""

    @patch('services.sendcertified_service.SessionLocal')
    def test_update_connection_status_connected(self, mock_session_class):
        """Test updating connection status to connected."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_connection = MagicMock()
        mock_session.query().filter_by().first.return_value = mock_connection

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._update_connection_status("connected")

        assert mock_connection.connection_status == "connected"
        assert mock_connection.last_connected_at is not None
        assert mock_connection.last_error is None
        mock_session.commit.assert_called_once()

    @patch('services.sendcertified_service.SessionLocal')
    def test_update_connection_status_error(self, mock_session_class):
        """Test updating connection status to error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_connection = MagicMock()
        mock_session.query().filter_by().first.return_value = mock_connection

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._update_connection_status("error", "Connection failed")

        assert mock_connection.connection_status == "error"
        assert mock_connection.last_error == "Connection failed"
        mock_session.commit.assert_called_once()

    @patch('services.sendcertified_service.SessionLocal')
    def test_update_connection_status_no_connection(self, mock_session_class):
        """Test updating connection status when no connection record exists."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._update_connection_status("connected")

        mock_session.commit.assert_not_called()

    @patch('services.sendcertified_service.SessionLocal')
    def test_update_connection_status_db_error(self, mock_session_class):
        """Test updating connection status handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.side_effect = Exception("DB Error")

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        # Should not raise exception
        service._update_connection_status("connected")

        mock_session.close.assert_called()


# =============================================================================
# Test Class: create_mailing Method
# =============================================================================

class TestCreateMailing:
    """Tests for create_mailing method."""

    def test_create_mailing_not_configured(self, sample_address, sample_document):
        """Test create_mailing when not configured."""
        service = SendCertifiedService(api_key=None, api_secret=None)
        result = service.create_mailing(
            recipient="Test Recipient",
            address=sample_address,
            document_content=sample_document
        )

        assert result["success"] is False
        assert "not configured" in result["error"]
        assert result["label_id"] is None
        assert result["tracking_number"] is None

    @patch('services.sendcertified_service.requests.post')
    @patch('services.sendcertified_service.SessionLocal')
    def test_create_mailing_success(self, mock_session_class, mock_post, sample_address, sample_document):
        """Test successful mailing creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "label_id": "lbl_123",
            "tracking_number": "9400111899223334445566",
            "cost": 8.95,
            "estimated_delivery": "2025-01-05"
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_order = MagicMock()
        mock_order.id = 1

        def refresh_side_effect(obj):
            obj.id = 1
        mock_session.refresh.side_effect = refresh_side_effect

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1

        result = service.create_mailing(
            recipient="Test Recipient",
            address=sample_address,
            document_content=sample_document,
            mail_class="certified",
            client_id=100,
            dispute_id=200,
            letter_type="dispute_round_1",
            bureau="Equifax"
        )

        assert result["success"] is True
        assert result["label_id"] == "lbl_123"
        assert result["tracking_number"] == "9400111899223334445566"
        assert result["cost"] == 8.95
        assert result["error"] is None

    @patch('services.sendcertified_service.requests.post')
    @patch('services.sendcertified_service.SessionLocal')
    def test_create_mailing_with_return_receipt(self, mock_session_class, mock_post, sample_address, sample_document):
        """Test mailing creation with return receipt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "mail_456",
            "tracking_number": "9400111899223334445566",
            "cost": 12.50
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        def refresh_side_effect(obj):
            obj.id = 1
        mock_session.refresh.side_effect = refresh_side_effect

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1

        result = service.create_mailing(
            recipient="Test Recipient",
            address=sample_address,
            document_content=sample_document,
            mail_class="certified_return_receipt"
        )

        assert result["success"] is True
        # Verify return_receipt was set in payload
        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json') or call_args[1].get('json')
        assert payload["return_receipt"] is True

    @patch('services.sendcertified_service.requests.post')
    @patch('services.sendcertified_service.SessionLocal')
    def test_create_mailing_api_error(self, mock_session_class, mock_post, sample_address, sample_document):
        """Test mailing creation with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Invalid address"
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1

        result = service.create_mailing(
            recipient="Test Recipient",
            address=sample_address,
            document_content=sample_document
        )

        assert result["success"] is False
        assert "400" in result["error"]
        assert result["label_id"] is None

    @patch('services.sendcertified_service.requests.post')
    @patch('services.sendcertified_service.SessionLocal')
    def test_create_mailing_network_error(self, mock_session_class, mock_post, sample_address, sample_document):
        """Test mailing creation with network error."""
        import requests
        mock_post.side_effect = requests.RequestException("Connection timeout")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1

        result = service.create_mailing(
            recipient="Test Recipient",
            address=sample_address,
            document_content=sample_document
        )

        assert result["success"] is False
        assert "Network error" in result["error"]

    @patch('services.sendcertified_service.requests.post')
    @patch('services.sendcertified_service.SessionLocal')
    def test_create_mailing_database_error(self, mock_session_class, mock_post, sample_address, sample_document):
        """Test mailing creation with database error."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "label_id": "lbl_123",
            "tracking_number": "9400111899223334445566",
            "cost": 8.95
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.commit.side_effect = Exception("Database error")

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1

        result = service.create_mailing(
            recipient="Test Recipient",
            address=sample_address,
            document_content=sample_document
        )

        assert result["success"] is False
        assert "Error creating mailing" in result["error"]
        mock_session.rollback.assert_called()

    @patch('services.sendcertified_service.requests.post')
    @patch('services.sendcertified_service.SessionLocal')
    def test_create_mailing_alternative_response_fields(self, mock_session_class, mock_post, sample_address, sample_document):
        """Test mailing creation with alternative API response fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "mailing_id": "mail_789",  # Alternative field name
            "tracking_number": "9400111899223334445566",
            "cost": 9.95
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        def refresh_side_effect(obj):
            obj.id = 1
        mock_session.refresh.side_effect = refresh_side_effect

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1

        result = service.create_mailing(
            recipient="Test Recipient",
            address=sample_address,
            document_content=sample_document
        )

        assert result["success"] is True
        assert result["label_id"] == "mail_789"


# =============================================================================
# Test Class: _format_address Method
# =============================================================================

class TestFormatAddress:
    """Tests for _format_address method."""

    def test_format_address_full(self):
        """Test formatting full address."""
        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        address = {
            "street": "123 Main St",
            "address_line_2": "Suite 100",
            "city": "New York",
            "state": "NY",
            "zip": "10001"
        }
        result = service._format_address(address)

        assert "123 Main St" in result
        assert "Suite 100" in result
        assert "New York" in result
        assert "NY" in result
        assert "10001" in result

    def test_format_address_alternative_fields(self):
        """Test formatting address with alternative field names."""
        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        address = {
            "address_line_1": "456 Oak Ave",
            "city": "Los Angeles",
            "state": "CA",
            "zip_code": "90001"
        }
        result = service._format_address(address)

        assert "456 Oak Ave" in result
        assert "Los Angeles" in result
        assert "CA" in result
        assert "90001" in result

    def test_format_address_minimal(self):
        """Test formatting minimal address."""
        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        address = {
            "street": "789 Elm St"
        }
        result = service._format_address(address)

        assert "789 Elm St" in result

    def test_format_address_empty(self):
        """Test formatting empty address."""
        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        address = {}
        result = service._format_address(address)

        assert result == ""


# =============================================================================
# Test Class: get_tracking_status Method
# =============================================================================

class TestGetTrackingStatus:
    """Tests for get_tracking_status method."""

    def test_get_tracking_status_no_tracking_number(self, mock_session):
        """Test getting tracking status without tracking number."""
        with patch('services.sendcertified_service.SessionLocal', return_value=mock_session):
            service = SendCertifiedService(
                api_key="test_key",
                api_secret="test_secret"
            )
            result = service.get_tracking_status()

            assert result["success"] is False
            assert "No tracking number" in result["error"]

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_tracking_status_by_order_id(self, mock_session_class, mock_order):
        """Test getting tracking status by order ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = mock_order

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "in_transit",
            "events": [{"timestamp": "2025-01-01", "description": "In transit"}]
        }

        with patch('services.sendcertified_service.requests.get', return_value=mock_response):
            service = SendCertifiedService(
                api_key="test_key",
                api_secret="test_secret"
            )
            service._integration_id = 1
            result = service.get_tracking_status(order_id=1)

            assert result["success"] is True
            assert result["status"] == "in_transit"

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_get_tracking_status_success(self, mock_session_class, mock_get):
        """Test successful tracking status retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "delivered",
            "events": [
                {"timestamp": "2025-01-01", "description": "Delivered"}
            ],
            "delivered_at": "2025-01-01T14:30:00Z",
            "signed_by": "John Doe"
        }
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_order = MagicMock()
        mock_order.status = "in_transit"
        mock_session.query().filter_by().first.return_value = mock_order

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.get_tracking_status(tracking_number="9400111899223334445566")

        assert result["success"] is True
        assert result["status"] == "delivered"
        assert result["signed_by"] == "John Doe"
        assert len(result["events"]) == 1

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_tracking_status_not_configured_with_cached_data(self, mock_session_class, mock_order):
        """Test getting tracking status when not configured returns cached data."""
        mock_order.webhook_data = {"events": [{"description": "Cached event"}]}
        mock_order.delivered_at = datetime(2025, 1, 1, 14, 30)

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = mock_order

        # Create service with explicit empty credentials - not configured for API access
        # but can still return cached data from database
        service = SendCertifiedService.__new__(SendCertifiedService)
        service.api_key = ""
        service.api_secret = ""
        service.sandbox = True
        service.base_url = SANDBOX_BASE_URL
        service._integration_id = None

        result = service.get_tracking_status(tracking_number="9400111899223334445566")

        assert result["success"] is True
        assert result["cached"] is True
        assert result["status"] == mock_order.status

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_tracking_status_not_configured_no_order(self, mock_session_class):
        """Test getting tracking status when not configured and no order found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = SendCertifiedService(api_key=None, api_secret=None)
        result = service.get_tracking_status(tracking_number="9400111899223334445566")

        assert result["success"] is False
        assert "not configured" in result["error"]

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_get_tracking_status_api_error(self, mock_session_class, mock_get):
        """Test tracking status retrieval with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.get_tracking_status(tracking_number="invalid")

        assert result["success"] is False
        assert "404" in result["error"]

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_get_tracking_status_network_error(self, mock_session_class, mock_get):
        """Test tracking status retrieval with network error."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.get_tracking_status(tracking_number="9400111899223334445566")

        assert result["success"] is False
        assert "Network error" in result["error"]

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_get_tracking_status_updates_order(self, mock_session_class, mock_get):
        """Test tracking status updates order in database."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "delivered",
            "events": [],
            "delivered_at": "2025-01-01T14:30:00Z"
        }
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_order = MagicMock()
        mock_order.status = "in_transit"
        mock_order.delivered_at = None
        mock_session.query().filter_by().first.return_value = mock_order

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        service.get_tracking_status(tracking_number="9400111899223334445566")

        assert mock_order.status == "delivered"
        mock_session.commit.assert_called()

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_get_tracking_status_invalid_datetime(self, mock_session_class, mock_get):
        """Test tracking status handles invalid datetime gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "delivered",
            "events": [],
            "delivered_at": "invalid-date"
        }
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_order = MagicMock()
        mock_order.status = "in_transit"
        mock_order.delivered_at = None
        mock_session.query().filter_by().first.return_value = mock_order

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.get_tracking_status(tracking_number="9400111899223334445566")

        # Should still succeed with fallback datetime
        assert result["success"] is True
        assert mock_order.delivered_at is not None


# =============================================================================
# Test Class: download_return_receipt Method
# =============================================================================

class TestDownloadReturnReceipt:
    """Tests for download_return_receipt method."""

    @patch('services.sendcertified_service.SessionLocal')
    def test_download_receipt_no_tracking_number(self, mock_session_class):
        """Test downloading receipt without tracking number."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        result = service.download_return_receipt()

        assert result is None

    @patch('services.sendcertified_service.SessionLocal')
    def test_download_receipt_not_configured(self, mock_session_class):
        """Test downloading receipt when not configured."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(api_key=None, api_secret=None)
        result = service.download_return_receipt(tracking_number="9400111899223334445566")

        assert result is None

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_download_receipt_success_pdf(self, mock_session_class, mock_get):
        """Test successful receipt download as PDF."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_response.content = b"%PDF-1.4 receipt content"
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.download_return_receipt(tracking_number="9400111899223334445566")

        assert result is not None
        assert b"%PDF" in result

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_download_receipt_success_octet_stream(self, mock_session_class, mock_get):
        """Test successful receipt download as octet-stream."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/octet-stream"}
        mock_response.content = b"%PDF-1.4 receipt content"
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.download_return_receipt(tracking_number="9400111899223334445566")

        assert result is not None

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_download_receipt_unexpected_content_type(self, mock_session_class, mock_get):
        """Test receipt download with unexpected content type."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.content = b"<html>Error page</html>"
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.download_return_receipt(tracking_number="9400111899223334445566")

        assert result is None

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_download_receipt_404_not_available(self, mock_session_class, mock_get):
        """Test receipt download when not yet available."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.download_return_receipt(tracking_number="9400111899223334445566")

        assert result is None

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_download_receipt_network_error(self, mock_session_class, mock_get):
        """Test receipt download with network error."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.download_return_receipt(tracking_number="9400111899223334445566")

        assert result is None

    @patch('services.sendcertified_service.SessionLocal')
    def test_download_receipt_by_order_id(self, mock_session_class, mock_order):
        """Test downloading receipt by order ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = mock_order

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_response.content = b"%PDF-1.4 receipt"

        with patch('services.sendcertified_service.requests.get', return_value=mock_response):
            service = SendCertifiedService(
                api_key="test_key",
                api_secret="test_secret"
            )
            service._integration_id = 1
            result = service.download_return_receipt(order_id=1)

            assert result is not None


# =============================================================================
# Test Class: get_account_balance Method
# =============================================================================

class TestGetAccountBalance:
    """Tests for get_account_balance method."""

    def test_get_account_balance_not_configured(self):
        """Test getting account balance when not configured."""
        service = SendCertifiedService(api_key=None, api_secret=None)
        result = service.get_account_balance()

        assert result["success"] is False
        assert "not configured" in result["error"]
        assert result["balance"] == 0
        assert result["credits"] == 0

    @patch('services.sendcertified_service.requests.get')
    def test_get_account_balance_success(self, mock_get):
        """Test successful account balance retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "balance": 150.00,
            "credits": 25,
            "monthly_usage": 10
        }
        mock_get.return_value = mock_response

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        result = service.get_account_balance()

        assert result["success"] is True
        assert result["balance"] == 150.00
        assert result["credits"] == 25
        assert result["monthly_usage"] == 10

    @patch('services.sendcertified_service.requests.get')
    def test_get_account_balance_api_error(self, mock_get):
        """Test account balance retrieval with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        result = service.get_account_balance()

        assert result["success"] is False
        assert "500" in result["error"]

    @patch('services.sendcertified_service.requests.get')
    def test_get_account_balance_exception(self, mock_get):
        """Test account balance retrieval with exception."""
        mock_get.side_effect = Exception("Unexpected error")

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        result = service.get_account_balance()

        assert result["success"] is False
        assert "Unexpected error" in result["error"]


# =============================================================================
# Test Class: _log_event Method
# =============================================================================

class TestLogEvent:
    """Tests for _log_event method."""

    @patch('services.sendcertified_service.SessionLocal')
    def test_log_event_success(self, mock_session_class):
        """Test successful event logging."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        service._log_event(
            event_type="test_event",
            event_data={"key": "value"},
            client_id=100,
            response_status=200
        )

        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    @patch('services.sendcertified_service.SessionLocal')
    def test_log_event_without_integration_id(self, mock_session_class):
        """Test event logging without integration ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = None
        service._log_event(event_type="test_event")

        mock_session.add.assert_not_called()

    @patch('services.sendcertified_service.SessionLocal')
    def test_log_event_database_error(self, mock_session_class):
        """Test event logging handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.commit.side_effect = Exception("DB Error")

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        # Should not raise exception
        service._log_event(event_type="test_event")

        mock_session.rollback.assert_called()
        mock_session.close.assert_called()


# =============================================================================
# Test Class: Factory Functions
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory functions."""

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_sendcertified_service(self, mock_session_class):
        """Test get_sendcertified_service factory function."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = get_sendcertified_service()

        assert isinstance(service, SendCertifiedService)


# =============================================================================
# Test Class: configure_sendcertified Function
# =============================================================================

class TestConfigureSendcertified:
    """Tests for configure_sendcertified function."""

    @patch('services.encryption.encrypt_value')
    @patch('services.sendcertified_service.SessionLocal')
    def test_configure_sendcertified_new_connection(self, mock_session_class, mock_encrypt):
        """Test configuring new SendCertified connection."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        mock_encrypt.side_effect = ["encrypted_key", "encrypted_secret"]

        with patch('services.sendcertified_service.SendCertifiedService') as MockService:
            mock_service = MagicMock()
            mock_service.test_connection.return_value = True
            MockService.return_value = mock_service

            result = configure_sendcertified(
                api_key="test_key",
                api_secret="test_secret",
                sandbox=True
            )

            assert result["success"] is True
            assert result["configured"] is True
            assert result["connection_test"] is True
            assert result["sandbox"] is True
            mock_session.add.assert_called()
            mock_session.commit.assert_called()

    @patch('services.encryption.encrypt_value')
    @patch('services.sendcertified_service.SessionLocal')
    def test_configure_sendcertified_update_existing(self, mock_session_class, mock_encrypt):
        """Test updating existing SendCertified connection."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_connection = MagicMock()
        mock_session.query().filter_by().first.return_value = mock_connection

        mock_encrypt.side_effect = ["encrypted_key", "encrypted_secret"]

        with patch('services.sendcertified_service.SendCertifiedService') as MockService:
            mock_service = MagicMock()
            mock_service.test_connection.return_value = True
            MockService.return_value = mock_service

            result = configure_sendcertified(
                api_key="new_key",
                api_secret="new_secret",
                sandbox=False
            )

            assert result["success"] is True
            assert mock_connection.api_key_encrypted == "encrypted_key"
            assert mock_connection.api_secret_encrypted == "encrypted_secret"
            assert mock_connection.is_sandbox is False

    @patch('services.encryption.encrypt_value')
    @patch('services.sendcertified_service.SessionLocal')
    def test_configure_sendcertified_database_error(self, mock_session_class, mock_encrypt):
        """Test configure_sendcertified handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.commit.side_effect = Exception("Database error")

        result = configure_sendcertified(
            api_key="test_key",
            api_secret="test_secret"
        )

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_session.rollback.assert_called()


# =============================================================================
# Test Class: get_sendcertified_status Function
# =============================================================================

class TestGetSendcertifiedStatus:
    """Tests for get_sendcertified_status function."""

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_status_not_configured(self, mock_session_class):
        """Test getting status when not configured."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        result = get_sendcertified_status()

        assert result["configured"] is False
        assert result["connected"] is False
        assert result["status"] == "not_configured"

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_status_configured_connected(self, mock_session_class, mock_connection):
        """Test getting status when configured and connected."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = mock_connection

        result = get_sendcertified_status()

        assert result["configured"] is True
        assert result["connected"] is True
        assert result["status"] == "connected"
        assert result["sandbox"] is True

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_status_configured_not_connected(self, mock_session_class):
        """Test getting status when configured but not connected."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_connection = MagicMock()
        mock_connection.api_key_encrypted = "encrypted_key"
        mock_connection.connection_status = "error"
        mock_connection.is_sandbox = False
        mock_connection.last_connected_at = None
        mock_connection.last_error = "Connection timeout"
        mock_session.query().filter_by().first.return_value = mock_connection

        result = get_sendcertified_status()

        assert result["configured"] is True
        assert result["connected"] is False
        assert result["status"] == "error"
        assert result["last_error"] == "Connection timeout"

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_status_database_error(self, mock_session_class):
        """Test getting status handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.side_effect = Exception("DB Error")

        result = get_sendcertified_status()

        assert result["configured"] is False
        assert result["status"] == "error"
        assert "DB Error" in result["last_error"]


# =============================================================================
# Test Class: get_mailing_statistics Function
# =============================================================================

class TestGetMailingStatistics:
    """Tests for get_mailing_statistics function."""

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_mailing_statistics_success(self, mock_session_class):
        """Test successful statistics retrieval."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock scalar returns for counts
        mock_session.query().scalar.return_value = 100
        mock_session.query().filter().scalar.return_value = 25

        result = get_mailing_statistics()

        assert "total" in result
        assert "submitted" in result
        assert "in_transit" in result
        assert "delivered" in result
        assert "returned" in result
        assert "this_month" in result
        assert "total_cost" in result

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_mailing_statistics_empty(self, mock_session_class):
        """Test statistics retrieval with no data."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_session.query().scalar.return_value = None
        mock_session.query().filter().scalar.return_value = None

        result = get_mailing_statistics()

        assert result["total"] == 0
        assert result["submitted"] == 0
        assert result["total_cost"] == 0

    @patch('services.sendcertified_service.SessionLocal')
    def test_get_mailing_statistics_database_error(self, mock_session_class):
        """Test statistics retrieval handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.side_effect = Exception("DB Error")

        result = get_mailing_statistics()

        assert result["total"] == 0
        assert result["delivered"] == 0
        assert result["total_cost"] == 0


# =============================================================================
# Test Class: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @patch('services.sendcertified_service.CertifiedMailOrder')
    @patch('services.sendcertified_service.requests.post')
    @patch('services.sendcertified_service.SessionLocal')
    def test_create_mailing_sets_credit_bureau_recipient_type(self, mock_session_class, mock_post, MockCertifiedMailOrder, sample_address, sample_document):
        """Test mailing creation sets recipient_type to credit_bureau when bureau specified."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "label_id": "lbl_123",
            "tracking_number": "9400111899223334445566",
            "cost": 8.95
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order_instance = MagicMock()
        mock_order_instance.id = 1
        MockCertifiedMailOrder.return_value = mock_order_instance

        def refresh_side_effect(obj):
            obj.id = 1
        mock_session.refresh.side_effect = refresh_side_effect

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1

        service.create_mailing(
            recipient="Equifax",
            address=sample_address,
            document_content=sample_document,
            bureau="Equifax"
        )

        # Verify the CertifiedMailOrder was created with credit_bureau recipient_type
        call_kwargs = MockCertifiedMailOrder.call_args[1]
        assert call_kwargs["recipient_type"] == "credit_bureau"

    @patch('services.sendcertified_service.CertifiedMailOrder')
    @patch('services.sendcertified_service.requests.post')
    @patch('services.sendcertified_service.SessionLocal')
    def test_create_mailing_sets_other_recipient_type(self, mock_session_class, mock_post, MockCertifiedMailOrder, sample_address, sample_document):
        """Test mailing creation sets recipient_type to other when no bureau."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "label_id": "lbl_123",
            "tracking_number": "9400111899223334445566",
            "cost": 8.95
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order_instance = MagicMock()
        mock_order_instance.id = 1
        MockCertifiedMailOrder.return_value = mock_order_instance

        def refresh_side_effect(obj):
            obj.id = 1
        mock_session.refresh.side_effect = refresh_side_effect

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1

        service.create_mailing(
            recipient="Some Creditor",
            address=sample_address,
            document_content=sample_document
        )

        # Verify the CertifiedMailOrder was created with other recipient_type
        call_kwargs = MockCertifiedMailOrder.call_args[1]
        assert call_kwargs["recipient_type"] == "other"

    @patch('services.sendcertified_service.SessionLocal')
    def test_session_always_closed_on_error(self, mock_session_class):
        """Test database session is always closed even on error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.side_effect = Exception("Error")

        service = SendCertifiedService(api_key=None, api_secret=None)
        service.get_tracking_status(tracking_number="9400111899223334445566")

        mock_session.close.assert_called()

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_tracking_status_alternative_event_field(self, mock_session_class, mock_get):
        """Test tracking status handles alternative event field name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "delivered",
            "tracking_events": [  # Alternative field name
                {"timestamp": "2025-01-01", "description": "Delivered"}
            ],
            "signature_name": "John Doe"  # Alternative field name
        }
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        result = service.get_tracking_status(tracking_number="9400111899223334445566")

        assert result["success"] is True
        assert len(result["events"]) == 1
        assert result["signed_by"] == "John Doe"

    def test_format_address_prefers_street_over_address_line_1(self):
        """Test _format_address prefers 'street' over 'address_line_1'."""
        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        address = {
            "street": "123 Main St",
            "address_line_1": "456 Other St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345"
        }
        result = service._format_address(address)

        assert "123 Main St" in result
        assert "456 Other St" not in result

    @patch('services.sendcertified_service.requests.post')
    @patch('services.sendcertified_service.SessionLocal')
    def test_create_mailing_encodes_document_as_base64(self, mock_session_class, mock_post, sample_address, sample_document):
        """Test mailing creation encodes document as base64."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "label_id": "lbl_123",
            "tracking_number": "9400111899223334445566",
            "cost": 8.95
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        def refresh_side_effect(obj):
            obj.id = 1
        mock_session.refresh.side_effect = refresh_side_effect

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1

        service.create_mailing(
            recipient="Test Recipient",
            address=sample_address,
            document_content=sample_document
        )

        # Verify the request was made with base64 encoded document
        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json') or call_args[1].get('json')
        import base64
        expected_encoded = base64.b64encode(sample_document).decode("utf-8")
        assert payload["document"]["document"] == expected_encoded

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_connection_updates_status_on_success(self, mock_session_class, mock_get):
        """Test connection test updates status to connected on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_connection = MagicMock()
        mock_connection.connection_status = "not_tested"
        mock_session.query().filter_by().first.return_value = mock_connection

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        service.test_connection()

        assert mock_connection.connection_status == "connected"

    @patch('services.sendcertified_service.requests.get')
    @patch('services.sendcertified_service.SessionLocal')
    def test_connection_updates_status_on_failure(self, mock_session_class, mock_get):
        """Test connection test updates status to error on failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_connection = MagicMock()
        mock_connection.connection_status = "connected"
        mock_session.query().filter_by().first.return_value = mock_connection

        service = SendCertifiedService(
            api_key="test_key",
            api_secret="test_secret"
        )
        service._integration_id = 1
        service.test_connection()

        assert mock_connection.connection_status == "error"
        assert "401" in str(mock_connection.last_error)
