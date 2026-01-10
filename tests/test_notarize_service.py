"""
Unit Tests for Notarize.com Integration Service.
Tests for transaction creation and management, signature requests, status checking,
webhook handling, document download, and connection testing.
Covers all main functions with mocked database interactions and external API calls.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os
import hashlib
import hmac
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.notarize_service import (
    NotarizeService,
    get_notarize_service,
    is_notarize_configured,
    test_notarize_connection as check_notarize_connection,  # Renamed to avoid pytest collection
    PRODUCTION_BASE_URL,
    SANDBOX_BASE_URL,
    SERVICE_NAME,
)


# =============================================================================
# Tests for Constants and Configuration
# =============================================================================

class TestConstants:
    """Test service constants and configuration."""

    def test_production_base_url(self):
        """Test that production base URL is correctly set."""
        assert PRODUCTION_BASE_URL == "https://api.notarize.com/v1"

    def test_sandbox_base_url(self):
        """Test that sandbox base URL is correctly set."""
        assert SANDBOX_BASE_URL == "https://api.sandbox.notarize.com/v1"

    def test_service_name(self):
        """Test that service name is correctly set."""
        assert SERVICE_NAME == "notarize"


# =============================================================================
# Tests for NotarizeService Initialization
# =============================================================================

class TestNotarizeServiceInit:
    """Test NotarizeService initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        service = NotarizeService(api_key="test_api_key_12345", sandbox=True)
        assert service.api_key == "test_api_key_12345"
        assert service.sandbox is True
        assert service.base_url == SANDBOX_BASE_URL

    def test_init_production_mode(self):
        """Test initialization in production mode."""
        service = NotarizeService(api_key="test_api_key_12345", sandbox=False)
        assert service.sandbox is False
        assert service.base_url == PRODUCTION_BASE_URL

    @patch.dict(os.environ, {"NOTARIZE_API_KEY": "env_api_key_12345"})
    def test_init_with_env_notarize_api_key(self):
        """Test initialization with NOTARIZE_API_KEY environment variable."""
        service = NotarizeService()
        assert service.api_key == "env_api_key_12345"

    @patch.dict(os.environ, {"PROOF_API_KEY": "proof_api_key_12345"}, clear=True)
    def test_init_with_env_proof_api_key(self):
        """Test initialization with PROOF_API_KEY environment variable as fallback."""
        service = NotarizeService()
        assert service.api_key == "proof_api_key_12345"

    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_api_key(self):
        """Test initialization without any API key."""
        service = NotarizeService()
        assert service.api_key is None

    def test_init_default_sandbox_mode(self):
        """Test that sandbox mode is enabled by default."""
        service = NotarizeService(api_key="test_api_key_12345")
        assert service.sandbox is True


# =============================================================================
# Tests for is_configured Property
# =============================================================================

class TestIsConfigured:
    """Test is_configured property."""

    def test_is_configured_with_valid_key(self):
        """Test is_configured returns True with valid API key."""
        service = NotarizeService(api_key="valid_api_key_12345")
        assert service.is_configured is True

    def test_is_configured_with_short_key(self):
        """Test is_configured returns False with short API key."""
        service = NotarizeService(api_key="short")
        assert service.is_configured is False

    def test_is_configured_with_no_key(self):
        """Test is_configured returns False without API key."""
        service = NotarizeService(api_key=None)
        assert service.is_configured is False

    def test_is_configured_with_empty_key(self):
        """Test is_configured returns False with empty API key."""
        service = NotarizeService(api_key="")
        assert service.is_configured is False


# =============================================================================
# Tests for _get_headers Method
# =============================================================================

class TestGetHeaders:
    """Test _get_headers method."""

    def test_get_headers_success(self):
        """Test headers are correctly formatted."""
        service = NotarizeService(api_key="test_api_key_12345")
        headers = service._get_headers()

        assert headers["ApiKey"] == "test_api_key_12345"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    def test_get_headers_raises_without_config(self):
        """Test _get_headers raises ValueError when not configured."""
        service = NotarizeService(api_key=None)

        with pytest.raises(ValueError, match="API key is not configured"):
            service._get_headers()


# =============================================================================
# Tests for test_connection Method
# =============================================================================

class TestTestConnection:
    """Test test_connection method."""

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_connection_success(self, mock_session_class, mock_get):
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.test_connection()

        assert result is True
        mock_get.assert_called_once()

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_connection_success_201(self, mock_session_class, mock_get):
        """Test successful connection test with 201 response."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.ok = True
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.test_connection()

        assert result is True

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_connection_auth_failure(self, mock_session_class, mock_get):
        """Test connection test with authentication failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.ok = False
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.test_connection()

        assert result is False

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_connection_server_error(self, mock_session_class, mock_get):
        """Test connection test with server error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.ok = False
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.test_connection()

        assert result is False

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_connection_network_error(self, mock_session_class, mock_get):
        """Test connection test with network error."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.test_connection()

        assert result is False

    def test_connection_not_configured(self):
        """Test connection test when not configured."""
        service = NotarizeService(api_key=None)
        result = service.test_connection()

        assert result is False


# =============================================================================
# Tests for create_transaction Method
# =============================================================================

class TestCreateTransaction:
    """Test create_transaction method."""

    @patch('services.notarize_service.requests.post')
    @patch('services.notarize_service.SessionLocal')
    def test_create_transaction_success(self, mock_session_class, mock_post):
        """Test successful transaction creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": "ext_txn_123",
            "access_link": "https://notarize.com/session/abc123"
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.create_transaction(
            signer_email="test@example.com",
            signer_first_name="John",
            signer_last_name="Doe",
            document_url="https://example.com/doc.pdf"
        )

        assert result["success"] is True
        assert result["transaction_id"] == "ext_txn_123"
        assert result["access_link"] == "https://notarize.com/session/abc123"
        assert result["internal_id"] is not None
        assert result["error"] is None

    @patch('services.notarize_service.requests.post')
    @patch('services.notarize_service.SessionLocal')
    def test_create_transaction_with_all_options(self, mock_session_class, mock_post):
        """Test transaction creation with all optional parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "transaction_id": "ext_txn_456",
            "session_link": "https://notarize.com/session/def456"
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 2))

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.create_transaction(
            signer_email="jane@example.com",
            signer_first_name="Jane",
            signer_last_name="Smith",
            document_url="https://example.com/contract.pdf",
            requirement="esignature",
            client_id=100,
            document_id=200,
            document_name="Service Contract"
        )

        assert result["success"] is True
        assert result["transaction_id"] == "ext_txn_456"
        assert result["access_link"] == "https://notarize.com/session/def456"

    def test_create_transaction_not_configured(self):
        """Test transaction creation when not configured."""
        service = NotarizeService(api_key=None)
        result = service.create_transaction(
            signer_email="test@example.com",
            signer_first_name="John",
            signer_last_name="Doe",
            document_url="https://example.com/doc.pdf"
        )

        assert result["success"] is False
        assert "not configured" in result["error"]

    @patch('services.notarize_service.requests.post')
    @patch('services.notarize_service.SessionLocal')
    def test_create_transaction_api_error(self, mock_session_class, mock_post):
        """Test transaction creation with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.ok = False
        mock_response.text = "Bad Request: Invalid document URL"
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.create_transaction(
            signer_email="test@example.com",
            signer_first_name="John",
            signer_last_name="Doe",
            document_url="invalid-url"
        )

        assert result["success"] is False
        assert "400" in result["error"]

    @patch('services.notarize_service.requests.post')
    @patch('services.notarize_service.SessionLocal')
    def test_create_transaction_network_error(self, mock_session_class, mock_post):
        """Test transaction creation with network error."""
        import requests
        mock_post.side_effect = requests.RequestException("Connection timeout")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.create_transaction(
            signer_email="test@example.com",
            signer_first_name="John",
            signer_last_name="Doe",
            document_url="https://example.com/doc.pdf"
        )

        assert result["success"] is False
        assert "Network error" in result["error"]

    @patch('services.notarize_service.requests.post')
    @patch('services.notarize_service.SessionLocal')
    def test_create_transaction_database_error(self, mock_session_class, mock_post):
        """Test transaction creation with database error."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.ok = True
        mock_response.json.return_value = {"id": "ext_123", "access_link": "http://link"}
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)
        mock_session.commit.side_effect = Exception("Database connection lost")

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.create_transaction(
            signer_email="test@example.com",
            signer_first_name="John",
            signer_last_name="Doe",
            document_url="https://example.com/doc.pdf"
        )

        assert result["success"] is False
        assert "Database connection lost" in result["error"]
        mock_session.rollback.assert_called()


# =============================================================================
# Tests for get_transaction_status Method
# =============================================================================

class TestGetTransactionStatus:
    """Test get_transaction_status method."""

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_get_status_by_internal_id(self, mock_session_class, mock_get):
        """Test getting status by internal database ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"status": "completed"}
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.external_transaction_id = "ext_123"
        mock_transaction.status = "pending"
        mock_transaction.client_id = 100
        mock_transaction.webhook_events = []
        mock_transaction.completed_at = None
        mock_session.query().filter_by().first.side_effect = [MagicMock(id=1), mock_transaction]

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.get_transaction_status(1)

        assert result["success"] is True
        assert result["status"] == "completed"

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_get_status_by_external_id(self, mock_session_class, mock_get):
        """Test getting status by external transaction ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"status": "in_progress"}
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.external_transaction_id = "ext_abc123"
        mock_transaction.status = "created"
        mock_transaction.client_id = None
        mock_transaction.webhook_events = []
        mock_transaction.completed_at = None
        mock_session.query().filter_by().first.side_effect = [MagicMock(id=1), mock_transaction]

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.get_transaction_status("ext_abc123")

        assert result["success"] is True
        assert result["status"] == "in_progress"

    @patch('services.notarize_service.SessionLocal')
    def test_get_status_transaction_not_found(self, mock_session_class):
        """Test getting status for non-existent transaction."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.get_transaction_status(999)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.notarize_service.SessionLocal')
    def test_get_status_no_external_id(self, mock_session_class):
        """Test getting status when transaction has no external ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.external_transaction_id = None
        mock_transaction.status = "created"
        mock_transaction.webhook_events = []
        mock_session.query().filter_by().first.return_value = mock_transaction

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.get_transaction_status(1)

        assert result["success"] is False
        assert "No external transaction ID" in result["error"]

    def test_get_status_not_configured(self):
        """Test getting status when not configured."""
        service = NotarizeService(api_key=None)
        result = service.get_transaction_status(1)

        assert result["success"] is False
        assert "not configured" in result["error"]

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_get_status_api_404(self, mock_session_class, mock_get):
        """Test getting status when API returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.external_transaction_id = "ext_deleted"
        mock_transaction.webhook_events = []
        mock_session.query().filter_by().first.side_effect = [MagicMock(id=1), mock_transaction]

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.get_transaction_status(1)

        assert result["success"] is False
        assert result["status"] == "not_found"

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_get_status_normalizes_status(self, mock_session_class, mock_get):
        """Test that status values are properly normalized."""
        test_cases = [
            ("complete", "completed"),
            ("canceled", "cancelled"),
            ("in progress", "in_progress"),
        ]

        for api_status, expected_status in test_cases:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {"status": api_status}
            mock_get.return_value = mock_response

            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_transaction = MagicMock()
            mock_transaction.id = 1
            mock_transaction.external_transaction_id = "ext_123"
            mock_transaction.status = "pending"
            mock_transaction.client_id = None
            mock_transaction.webhook_events = []
            mock_transaction.completed_at = None
            mock_session.query().filter_by().first.side_effect = [MagicMock(id=1), mock_transaction]

            service = NotarizeService(api_key="test_api_key_12345")
            result = service.get_transaction_status(1)

            assert result["status"] == expected_status, f"Failed for {api_status}"


# =============================================================================
# Tests for download_completed_document Method
# =============================================================================

class TestDownloadCompletedDocument:
    """Test download_completed_document method."""

    def test_download_not_configured(self):
        """Test download when not configured."""
        service = NotarizeService(api_key=None)
        result = service.download_completed_document(1)

        assert isinstance(result, dict)
        assert result["success"] is False
        assert "not configured" in result["error"]

    @patch('services.notarize_service.SessionLocal')
    def test_download_transaction_not_found(self, mock_session_class):
        """Test download for non-existent transaction."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.download_completed_document(999)

        assert isinstance(result, dict)
        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_download_not_completed(self, mock_session_class, mock_get):
        """Test download for transaction that is not completed."""
        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.ok = True
        mock_api_response.json.return_value = {"status": "pending"}
        mock_get.return_value = mock_api_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.external_transaction_id = "ext_123"
        mock_transaction.status = "pending"
        mock_transaction.client_id = None
        mock_transaction.webhook_events = []
        mock_transaction.completed_at = None
        mock_session.query().filter_by().first.side_effect = [mock_transaction, MagicMock(id=1), mock_transaction]

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.download_completed_document(1)

        assert isinstance(result, dict)
        assert result["success"] is False
        assert "not completed" in result["error"]

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_download_success_with_url(self, mock_session_class, mock_get):
        """Test successful document download via URL."""
        # First call for status check
        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.ok = True
        mock_status_response.json.return_value = {"status": "completed"}

        # Second call for documents list
        mock_docs_response = MagicMock()
        mock_docs_response.status_code = 200
        mock_docs_response.json.return_value = {
            "documents": [{"url": "https://cdn.notarize.com/doc.pdf"}]
        }

        # Third call for document download
        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"%PDF-1.4 document content"

        mock_get.side_effect = [mock_status_response, mock_docs_response, mock_download_response]

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.external_transaction_id = "ext_123"
        mock_transaction.status = "completed"
        mock_transaction.client_id = 100
        mock_transaction.webhook_events = []
        mock_transaction.completed_at = datetime.utcnow()
        mock_session.query().filter_by().first.side_effect = [mock_transaction, MagicMock(id=1), mock_transaction]

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.download_completed_document(1)

        assert isinstance(result, bytes)
        assert b"%PDF" in result


# =============================================================================
# Tests for verify_webhook_signature Method
# =============================================================================

class TestVerifyWebhookSignature:
    """Test verify_webhook_signature method."""

    def test_verify_without_secret(self):
        """Test verification returns True when no secret configured."""
        service = NotarizeService(api_key="test_api_key_12345")

        with patch.dict(os.environ, {}, clear=True):
            result = service.verify_webhook_signature(
                payload='{"test": "data"}',
                signature="any_signature"
            )

        assert result is True

    def test_verify_without_signature(self):
        """Test verification fails when no signature provided."""
        service = NotarizeService(api_key="test_api_key_12345")

        result = service.verify_webhook_signature(
            payload='{"test": "data"}',
            signature="",
            secret="webhook_secret_key"
        )

        assert result is False

    def test_verify_valid_signature(self):
        """Test verification with valid signature."""
        service = NotarizeService(api_key="test_api_key_12345")
        payload = '{"event": "transaction.completed"}'
        secret = "webhook_secret_key"

        # Generate correct signature
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        result = service.verify_webhook_signature(
            payload=payload,
            signature=expected_sig,
            secret=secret
        )

        assert result is True

    def test_verify_signature_with_prefix(self):
        """Test verification with sha256= prefix in signature."""
        service = NotarizeService(api_key="test_api_key_12345")
        payload = '{"event": "transaction.completed"}'
        secret = "webhook_secret_key"

        expected_sig = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        result = service.verify_webhook_signature(
            payload=payload,
            signature=f"sha256={expected_sig}",
            secret=secret
        )

        assert result is True

    def test_verify_invalid_signature(self):
        """Test verification fails with invalid signature."""
        service = NotarizeService(api_key="test_api_key_12345")

        result = service.verify_webhook_signature(
            payload='{"event": "transaction.completed"}',
            signature="invalid_signature",
            secret="webhook_secret_key"
        )

        assert result is False

    def test_verify_with_bytes_payload(self):
        """Test verification with bytes payload."""
        service = NotarizeService(api_key="test_api_key_12345")
        payload = b'{"event": "transaction.completed"}'
        secret = "webhook_secret_key"

        expected_sig = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = service.verify_webhook_signature(
            payload=payload,
            signature=expected_sig,
            secret=secret
        )

        assert result is True


# =============================================================================
# Tests for handle_webhook Method
# =============================================================================

class TestHandleWebhook:
    """Test handle_webhook method."""

    @patch('services.notarize_service.SessionLocal')
    def test_webhook_invalid_signature(self, mock_session_class):
        """Test webhook handling with invalid signature."""
        service = NotarizeService(api_key="test_api_key_12345")

        with patch.object(service, 'verify_webhook_signature', return_value=False):
            result = service.handle_webhook(
                webhook_data={"event": "transaction.completed"},
                raw_payload='{"event": "transaction.completed"}',
                signature="invalid"
            )

        assert result["success"] is False
        assert "Invalid webhook signature" in result["error"]

    @patch('services.notarize_service.SessionLocal')
    def test_webhook_no_transaction_id(self, mock_session_class):
        """Test webhook handling without transaction ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.handle_webhook(
            webhook_data={"event": "transaction.completed"}
        )

        assert result["success"] is False
        assert "No transaction_id" in result["error"]

    @patch('services.notarize_service.SessionLocal')
    def test_webhook_transaction_not_found(self, mock_session_class):
        """Test webhook handling when transaction not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.handle_webhook(
            webhook_data={"transaction_id": "ext_nonexistent", "event": "completed"}
        )

        assert result["success"] is False
        assert "No transaction found" in result["error"]

    @patch('services.notarize_service.SessionLocal')
    def test_webhook_completed_event(self, mock_session_class):
        """Test webhook handling for completed event."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.status = "in_progress"
        mock_transaction.webhook_events = []
        mock_transaction.client_id = 100
        mock_transaction.completed_at = None
        mock_session.query().filter_by().first.side_effect = [mock_transaction, MagicMock(id=1)]

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.handle_webhook(
            webhook_data={
                "transaction_id": "ext_123",
                "event": "transaction.completed"
            }
        )

        assert result["success"] is True
        assert result["internal_id"] == 1
        assert "completed" in result["action_taken"]

    @patch('services.notarize_service.SessionLocal')
    def test_webhook_various_events(self, mock_session_class):
        """Test webhook handling for various event types."""
        events_to_test = [
            ("transaction.created", "created"),
            ("transaction.started", "in_progress"),
            ("transaction.scheduled", "scheduled"),
            ("transaction.cancelled", "cancelled"),
            ("transaction.expired", "expired"),
            ("transaction.failed", "failed"),
        ]

        for event_type, expected_status in events_to_test:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_transaction = MagicMock()
            mock_transaction.id = 1
            mock_transaction.status = "pending"
            mock_transaction.webhook_events = []
            mock_transaction.client_id = None
            mock_transaction.completed_at = None
            mock_session.query().filter_by().first.side_effect = [mock_transaction, MagicMock(id=1)]

            service = NotarizeService(api_key="test_api_key_12345")
            result = service.handle_webhook(
                webhook_data={
                    "transaction_id": "ext_123",
                    "event": event_type
                }
            )

            assert result["success"] is True, f"Failed for event {event_type}"

    @patch('services.notarize_service.SessionLocal')
    def test_webhook_database_error(self, mock_session_class):
        """Test webhook handling with database error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.status = "pending"
        mock_transaction.webhook_events = []
        mock_transaction.client_id = None
        mock_session.query().filter_by().first.return_value = mock_transaction
        mock_session.commit.side_effect = Exception("Database error")

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.handle_webhook(
            webhook_data={
                "transaction_id": "ext_123",
                "event": "transaction.completed"
            }
        )

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_session.rollback.assert_called()


# =============================================================================
# Tests for Factory Functions
# =============================================================================

class TestFactoryFunctions:
    """Test factory functions."""

    @patch.dict(os.environ, {"NOTARIZE_SANDBOX": "true"})
    def test_get_notarize_service_sandbox_from_env(self):
        """Test get_notarize_service uses sandbox mode from environment."""
        service = get_notarize_service()
        assert service.sandbox is True

    @patch.dict(os.environ, {"NOTARIZE_SANDBOX": "false"})
    def test_get_notarize_service_production_from_env(self):
        """Test get_notarize_service uses production mode from environment."""
        service = get_notarize_service()
        assert service.sandbox is False

    def test_get_notarize_service_override_sandbox(self):
        """Test get_notarize_service with explicit sandbox override."""
        service = get_notarize_service(sandbox=False)
        assert service.sandbox is False

    @patch.dict(os.environ, {"NOTARIZE_API_KEY": "configured_key_12345"})
    def test_is_notarize_configured_true(self):
        """Test is_notarize_configured returns True when configured."""
        assert is_notarize_configured() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_is_notarize_configured_false(self):
        """Test is_notarize_configured returns False when not configured."""
        assert is_notarize_configured() is False

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    @patch.dict(os.environ, {"NOTARIZE_API_KEY": "test_key_12345"})
    def test_test_notarize_connection(self, mock_session_class, mock_get):
        """Test test_notarize_connection helper function."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        result = check_notarize_connection()
        assert result is True


# =============================================================================
# Tests for _get_integration_id Method
# =============================================================================

class TestGetIntegrationId:
    """Test _get_integration_id method."""

    @patch('services.notarize_service.SessionLocal')
    def test_get_integration_id_existing(self, mock_session_class):
        """Test getting existing integration ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_connection = MagicMock()
        mock_connection.id = 42
        mock_session.query().filter_by().first.return_value = mock_connection

        service = NotarizeService(api_key="test_api_key_12345")
        result = service._get_integration_id()

        assert result == 42

    @patch('services.notarize_service.SessionLocal')
    def test_get_integration_id_creates_new(self, mock_session_class):
        """Test creating new integration connection."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        # Mock the refresh to set the ID
        def refresh_side_effect(conn):
            conn.id = 99
        mock_session.refresh.side_effect = refresh_side_effect

        service = NotarizeService(api_key="test_api_key_12345")
        result = service._get_integration_id()

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('services.notarize_service.SessionLocal')
    def test_get_integration_id_cached(self, mock_session_class):
        """Test integration ID is cached."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = NotarizeService(api_key="test_api_key_12345")
        service._integration_id = 123

        result = service._get_integration_id()

        assert result == 123
        mock_session.query.assert_not_called()


# =============================================================================
# Tests for _log_event Method
# =============================================================================

class TestLogEvent:
    """Test _log_event method."""

    @patch('services.notarize_service.SessionLocal')
    def test_log_event_success(self, mock_session_class):
        """Test successful event logging."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        service = NotarizeService(api_key="test_api_key_12345")
        service._log_event(
            event_type="test_event",
            event_data={"key": "value"},
            client_id=100,
            response_status=200
        )

        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    @patch('services.notarize_service.SessionLocal')
    def test_log_event_without_integration_id(self, mock_session_class):
        """Test event logging fails gracefully without integration ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = NotarizeService(api_key="test_api_key_12345")
        service._integration_id = None

        # Mock _get_integration_id to return None
        with patch.object(service, '_get_integration_id', return_value=None):
            service._log_event(event_type="test_event")

        # Should not attempt to add event
        mock_session.add.assert_not_called()


# =============================================================================
# Tests for Session Cleanup
# =============================================================================

class TestSessionCleanup:
    """Test that database sessions are properly closed."""

    @patch('services.notarize_service.requests.post')
    @patch('services.notarize_service.SessionLocal')
    def test_create_transaction_closes_session(self, mock_session_class, mock_post):
        """Test session is closed after create_transaction."""
        mock_post.side_effect = Exception("Network error")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)

        service = NotarizeService(api_key="test_api_key_12345")
        service.create_transaction(
            signer_email="test@example.com",
            signer_first_name="John",
            signer_last_name="Doe",
            document_url="https://example.com/doc.pdf"
        )

        mock_session.close.assert_called()

    @patch('services.notarize_service.SessionLocal')
    def test_get_status_closes_session(self, mock_session_class):
        """Test session is closed after get_transaction_status."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = NotarizeService(api_key="test_api_key_12345")
        service.get_transaction_status(1)

        mock_session.close.assert_called()

    @patch('services.notarize_service.SessionLocal')
    def test_handle_webhook_closes_session(self, mock_session_class):
        """Test session is closed after handle_webhook."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None

        service = NotarizeService(api_key="test_api_key_12345")
        service.handle_webhook({"transaction_id": "ext_123"})

        mock_session.close.assert_called()


# =============================================================================
# Tests for Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @patch('services.notarize_service.requests.post')
    @patch('services.notarize_service.SessionLocal')
    def test_create_transaction_alternative_response_fields(self, mock_session_class, mock_post):
        """Test transaction creation handles alternative API response fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "transactionId": "alt_txn_id",
            "signerUrl": "https://notarize.com/alt_url"
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.create_transaction(
            signer_email="test@example.com",
            signer_first_name="John",
            signer_last_name="Doe",
            document_url="https://example.com/doc.pdf"
        )

        assert result["success"] is True
        assert result["transaction_id"] == "alt_txn_id"
        assert result["access_link"] == "https://notarize.com/alt_url"

    @patch('services.notarize_service.SessionLocal')
    def test_webhook_with_id_field(self, mock_session_class):
        """Test webhook handling with 'id' field instead of 'transaction_id'."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.status = "pending"
        mock_transaction.webhook_events = []
        mock_transaction.client_id = None
        mock_transaction.completed_at = None
        mock_session.query().filter_by().first.side_effect = [mock_transaction, MagicMock(id=1)]

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.handle_webhook(
            webhook_data={
                "id": "ext_123",
                "type": "completed"
            }
        )

        assert result["success"] is True

    @patch('services.notarize_service.SessionLocal')
    def test_webhook_with_status_field(self, mock_session_class):
        """Test webhook handling with 'status' field instead of 'event'."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.status = "pending"
        mock_transaction.webhook_events = []
        mock_transaction.client_id = None
        mock_transaction.completed_at = None
        mock_session.query().filter_by().first.side_effect = [mock_transaction, MagicMock(id=1)]

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.handle_webhook(
            webhook_data={
                "transactionId": "ext_123",
                "status": "completed"
            }
        )

        assert result["success"] is True

    @patch('services.notarize_service.requests.get')
    @patch('services.notarize_service.SessionLocal')
    def test_get_status_string_numeric_id(self, mock_session_class, mock_get):
        """Test get_transaction_status with string numeric ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"status": "completed"}
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_transaction = MagicMock()
        mock_transaction.id = 123
        mock_transaction.external_transaction_id = "ext_123"
        mock_transaction.status = "pending"
        mock_transaction.client_id = None
        mock_transaction.webhook_events = []
        mock_transaction.completed_at = None
        mock_session.query().filter_by().first.side_effect = [MagicMock(id=1), mock_transaction]

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.get_transaction_status("123")

        assert result["success"] is True

    @patch('services.notarize_service.requests.post')
    @patch('services.notarize_service.SessionLocal')
    def test_create_transaction_witness_requirement(self, mock_session_class, mock_post):
        """Test transaction creation with witness requirement."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.ok = True
        mock_response.json.return_value = {"id": "ext_witness", "access_link": "http://link"}
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter_by().first.return_value = MagicMock(id=1)
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        service = NotarizeService(api_key="test_api_key_12345")
        result = service.create_transaction(
            signer_email="test@example.com",
            signer_first_name="John",
            signer_last_name="Doe",
            document_url="https://example.com/doc.pdf",
            requirement="witness"
        )

        assert result["success"] is True
        # Verify the payload contained witness requirement
        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json') or call_args[1].get('json')
        assert payload["documents"][0]["requirement"] == "witness"

    @patch.dict(os.environ, {"NOTARIZE_WEBHOOK_SECRET": "env_secret_key"})
    def test_verify_signature_uses_env_secret(self):
        """Test webhook signature verification uses environment secret."""
        service = NotarizeService(api_key="test_api_key_12345")
        payload = '{"event": "test"}'

        # Generate signature with env secret
        expected_sig = hmac.new(
            "env_secret_key".encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        result = service.verify_webhook_signature(payload, expected_sig)
        assert result is True
