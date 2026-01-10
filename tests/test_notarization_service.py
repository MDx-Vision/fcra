"""
Unit tests for Proof.com (Notarize) Remote Online Notarization Service.
Tests for notarization order creation, status checking, document download,
webhook handling, and configuration validation.
Covers all public functions with mocked database interactions and external API calls.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.notarization_service import (
    is_proof_configured,
    get_api_key,
    _get_headers,
    _get_client_upload_folder,
    create_notarization_order,
    get_notarization_status,
    download_notarized_document,
    handle_webhook,
    get_order_by_id,
    get_orders_by_client,
    API_BASE_URL,
    PROVIDER_NAME,
)


# =============================================================================
# Tests for Constants and Configuration
# =============================================================================

class TestConstants:
    """Test service constants and configuration."""

    def test_api_base_url(self):
        """Test that API base URL is correctly set."""
        assert API_BASE_URL == "https://api.notarize.com/v1"

    def test_provider_name(self):
        """Test that provider name is correctly set."""
        assert PROVIDER_NAME == "proof.com"


# =============================================================================
# Tests for is_proof_configured
# =============================================================================

class TestIsProofConfigured:
    """Test is_proof_configured function."""

    @patch.dict(os.environ, {"PROOF_API_KEY": "test_api_key_12345"})
    def test_configured_with_api_key(self):
        """Test returns True when API key is configured."""
        assert is_proof_configured() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_not_configured_without_api_key(self):
        """Test returns False when API key is not configured."""
        # Clear the specific key if it exists
        os.environ.pop("PROOF_API_KEY", None)
        assert is_proof_configured() is False

    @patch.dict(os.environ, {"PROOF_API_KEY": ""})
    def test_not_configured_with_empty_api_key(self):
        """Test returns False when API key is empty string."""
        assert is_proof_configured() is False


# =============================================================================
# Tests for get_api_key
# =============================================================================

class TestGetApiKey:
    """Test get_api_key function."""

    @patch.dict(os.environ, {"PROOF_API_KEY": "my_secret_api_key"})
    def test_get_api_key_success(self):
        """Test successfully retrieving API key."""
        result = get_api_key()
        assert result == "my_secret_api_key"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_raises_when_not_set(self):
        """Test raises ValueError when API key is not set."""
        os.environ.pop("PROOF_API_KEY", None)
        with pytest.raises(ValueError, match="PROOF_API_KEY environment variable is not set"):
            get_api_key()


# =============================================================================
# Tests for _get_headers
# =============================================================================

class TestGetHeaders:
    """Test _get_headers function."""

    @patch.dict(os.environ, {"PROOF_API_KEY": "header_test_key"})
    def test_get_headers_success(self):
        """Test headers are correctly formatted."""
        headers = _get_headers()

        assert headers["ApiKey"] == "header_test_key"
        assert headers["Content-Type"] == "application/json"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_headers_raises_without_api_key(self):
        """Test _get_headers raises ValueError when not configured."""
        os.environ.pop("PROOF_API_KEY", None)
        with pytest.raises(ValueError):
            _get_headers()


# =============================================================================
# Tests for _get_client_upload_folder
# =============================================================================

class TestGetClientUploadFolder:
    """Test _get_client_upload_folder function."""

    def test_get_client_upload_folder_creates_directory(self):
        """Test that upload folder is created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('services.notarization_service.os.makedirs') as mock_makedirs:
                result = _get_client_upload_folder(123)

                assert result == "static/client_uploads/123/notarized"
                mock_makedirs.assert_called_once_with(
                    "static/client_uploads/123/notarized",
                    exist_ok=True
                )

    def test_get_client_upload_folder_different_client_ids(self):
        """Test folder path varies by client ID."""
        with patch('services.notarization_service.os.makedirs'):
            result1 = _get_client_upload_folder(1)
            result2 = _get_client_upload_folder(999)

            assert result1 == "static/client_uploads/1/notarized"
            assert result2 == "static/client_uploads/999/notarized"


# =============================================================================
# Tests for create_notarization_order
# =============================================================================

class TestCreateNotarizationOrder:
    """Test create_notarization_order function."""

    @patch('services.notarization_service.requests.post')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service.os.path.exists')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_create_order_success(self, mock_exists, mock_session_class, mock_post):
        """Test successful order creation."""
        mock_exists.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "ext_txn_123",
            "session_link": "https://notarize.com/session/abc123"
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock the order object after refresh
        def refresh_side_effect(order):
            order.id = 42
        mock_session.refresh.side_effect = refresh_side_effect

        result = create_notarization_order(
            client_id=1,
            document_path="/path/to/document.pdf",
            document_name="Test Document",
            signer_email="signer@example.com",
            signer_name="John Doe"
        )

        assert result["success"] is True
        assert result["transaction_id"] == "ext_txn_123"
        assert result["session_link"] == "https://notarize.com/session/abc123"
        assert result["order_id"] == 42
        assert result["error"] is None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service.os.path.exists')
    def test_create_order_document_not_found(self, mock_exists, mock_session_class):
        """Test order creation fails when document not found."""
        mock_exists.return_value = False
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = create_notarization_order(
            client_id=1,
            document_path="/nonexistent/document.pdf",
            document_name="Missing Doc",
            signer_email="signer@example.com",
            signer_name="John Doe"
        )

        assert result["success"] is False
        assert "Document not found" in result["error"]
        assert result["order_id"] is None
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.requests.post')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service.os.path.exists')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_create_order_api_error(self, mock_exists, mock_session_class, mock_post):
        """Test order creation with API error."""
        mock_exists.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Invalid parameters"
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = create_notarization_order(
            client_id=1,
            document_path="/path/to/document.pdf",
            document_name="Test Doc",
            signer_email="invalid-email",
            signer_name="John Doe"
        )

        assert result["success"] is False
        assert "400" in result["error"]
        assert result["order_id"] is None
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.requests.post')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service.os.path.exists')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_create_order_network_error(self, mock_exists, mock_session_class, mock_post):
        """Test order creation with network error."""
        import requests
        mock_exists.return_value = True
        mock_post.side_effect = requests.RequestException("Connection timeout")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = create_notarization_order(
            client_id=1,
            document_path="/path/to/document.pdf",
            document_name="Test Doc",
            signer_email="signer@example.com",
            signer_name="John Doe"
        )

        assert result["success"] is False
        assert "Network error" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.requests.post')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service.os.path.exists')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_create_order_database_error(self, mock_exists, mock_session_class, mock_post):
        """Test order creation with database error."""
        mock_exists.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "ext_123", "session_link": "http://link"}
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.commit.side_effect = Exception("Database connection lost")

        result = create_notarization_order(
            client_id=1,
            document_path="/path/to/document.pdf",
            document_name="Test Doc",
            signer_email="signer@example.com",
            signer_name="John Doe"
        )

        assert result["success"] is False
        assert "Database connection lost" in result["error"]
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.requests.post')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service.os.path.exists')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key", "REPL_SLUG_URL": "myapp.repl.co"})
    def test_create_order_with_replit_domain(self, mock_exists, mock_session_class, mock_post):
        """Test order creation uses Replit domain for document URL."""
        mock_exists.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "ext_456", "session_link": "http://link"}
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.refresh.side_effect = lambda x: setattr(x, 'id', 1)

        create_notarization_order(
            client_id=1,
            document_path="uploads/doc.pdf",
            document_name="Test Doc",
            signer_email="signer@example.com",
            signer_name="John Doe"
        )

        # Verify the POST was called with correct URL in payload
        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json') or call_args[1].get('json')
        assert "https://myapp.repl.co/uploads/doc.pdf" in str(payload)

    @patch('services.notarization_service.requests.post')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service.os.path.exists')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_create_order_alternative_response_fields(self, mock_exists, mock_session_class, mock_post):
        """Test order creation handles alternative API response fields."""
        mock_exists.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transaction_id": "alt_txn_id",
            "signerUrl": "https://notarize.com/alt_url"
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.refresh.side_effect = lambda x: setattr(x, 'id', 1)

        result = create_notarization_order(
            client_id=1,
            document_path="/path/to/doc.pdf",
            document_name="Test Doc",
            signer_email="signer@example.com",
            signer_name="John Doe"
        )

        assert result["success"] is True
        assert result["transaction_id"] == "alt_txn_id"
        assert result["session_link"] == "https://notarize.com/alt_url"


# =============================================================================
# Tests for get_notarization_status
# =============================================================================

class TestGetNotarizationStatus:
    """Test get_notarization_status function."""

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.SessionLocal')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_get_status_success(self, mock_session_class, mock_get):
        """Test successfully getting order status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "completed"}
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.status = "pending"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = get_notarization_status(1)

        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["order_id"] == 1
        assert result["transaction_id"] == "ext_123"
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_get_status_order_not_found(self, mock_session_class):
        """Test getting status for non-existent order."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = get_notarization_status(999)

        assert result["success"] is False
        assert "not found" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_get_status_no_external_transaction_id(self, mock_session_class):
        """Test getting status when order has no external transaction ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = None
        mock_order.status = "pending"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = get_notarization_status(1)

        assert result["success"] is False
        assert "No external transaction ID" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.SessionLocal')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_get_status_api_404(self, mock_session_class, mock_get):
        """Test getting status when API returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_deleted"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = get_notarization_status(1)

        assert result["success"] is False
        assert result["status"] == "not_found"
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.SessionLocal')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_get_status_api_error(self, mock_session_class, mock_get):
        """Test getting status with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = get_notarization_status(1)

        assert result["success"] is False
        assert "500" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.SessionLocal')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_get_status_network_error(self, mock_session_class, mock_get):
        """Test getting status with network error."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection refused")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = get_notarization_status(1)

        assert result["success"] is False
        assert "Network error" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.SessionLocal')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_get_status_normalizes_status_values(self, mock_session_class, mock_get):
        """Test that status values are properly normalized."""
        test_cases = [
            ("created", "pending"),
            ("pending", "pending"),
            ("in_progress", "in_progress"),
            ("in progress", "in_progress"),
            ("scheduled", "scheduled"),
            ("completed", "completed"),
            ("complete", "completed"),
            ("cancelled", "cancelled"),
            ("canceled", "cancelled"),
            ("expired", "expired"),
            ("failed", "failed"),
        ]

        for api_status, expected_status in test_cases:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": api_status}
            mock_get.return_value = mock_response

            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_order = MagicMock()
            mock_order.id = 1
            mock_order.external_transaction_id = "ext_123"
            mock_order.status = "pending"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_order

            result = get_notarization_status(1)

            assert result["status"] == expected_status, f"Failed for API status: {api_status}"

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.SessionLocal')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_get_status_sets_notarized_at_when_completed(self, mock_session_class, mock_get):
        """Test that notarized_at is set when status is completed."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "completed"}
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.status = "in_progress"
        mock_order.notarized_at = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = get_notarization_status(1)

        assert result["success"] is True
        assert mock_order.notarized_at is not None


# =============================================================================
# Tests for download_notarized_document
# =============================================================================

class TestDownloadNotarizedDocument:
    """Test download_notarized_document function."""

    @patch('services.notarization_service.SessionLocal')
    def test_download_order_not_found(self, mock_session_class):
        """Test download fails when order not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = download_notarized_document(999)

        assert result["success"] is False
        assert "not found" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_download_no_external_transaction_id(self, mock_session_class):
        """Test download fails when no external transaction ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = download_notarized_document(1)

        assert result["success"] is False
        assert "No external transaction ID" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    def test_download_not_completed(self, mock_session_class, mock_get_status):
        """Test download fails when notarization not completed."""
        mock_get_status.return_value = {"status": "pending"}

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = download_notarized_document(1)

        assert result["success"] is False
        assert "not completed" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service._get_client_upload_folder')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_success(self, mock_get_folder, mock_session_class, mock_get_status, mock_get):
        """Test successful document download."""
        mock_get_status.return_value = {"status": "completed"}
        mock_get_folder.return_value = "/tmp/test_folder"

        # First GET for documents list, second for actual download
        mock_docs_response = MagicMock()
        mock_docs_response.status_code = 200
        mock_docs_response.json.return_value = {
            "documents": [{"url": "https://cdn.notarize.com/doc.pdf", "name": "contract"}]
        }

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"%PDF-1.4 document content"

        mock_get.side_effect = [mock_docs_response, mock_download_response]

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.client_id = 100
        mock_order.document_name = "Test Contract"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('builtins.open', MagicMock()):
            result = download_notarized_document(1)

        assert result["success"] is True
        assert result["order_id"] == 1
        assert result["file_path"] is not None

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_api_error_getting_documents(self, mock_session_class, mock_get_status, mock_get):
        """Test download fails when API error getting documents."""
        mock_get_status.return_value = {"status": "completed"}

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = download_notarized_document(1)

        assert result["success"] is False
        assert "500" in result["error"]

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service._get_client_upload_folder')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_with_audit_trail(self, mock_get_folder, mock_session_class, mock_get_status, mock_get):
        """Test downloading document with audit trail."""
        mock_get_status.return_value = {"status": "completed"}
        mock_get_folder.return_value = "/tmp/test_folder"

        mock_docs_response = MagicMock()
        mock_docs_response.status_code = 200
        mock_docs_response.json.return_value = {
            "documents": [
                {"url": "https://cdn.notarize.com/doc.pdf", "name": "contract", "type": "document"},
                {"url": "https://cdn.notarize.com/audit.pdf", "name": "audit_trail", "type": "audit"}
            ]
        }

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"%PDF-1.4 document content"

        mock_get.side_effect = [mock_docs_response, mock_download_response, mock_download_response]

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.client_id = 100
        mock_order.document_name = "Test Contract"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('builtins.open', MagicMock()):
            result = download_notarized_document(1)

        assert result["success"] is True
        assert result["audit_trail_path"] is not None

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_network_error(self, mock_session_class, mock_get_status, mock_get):
        """Test download fails with network error."""
        import requests
        mock_get_status.return_value = {"status": "completed"}
        mock_get.side_effect = requests.RequestException("Network error")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = download_notarized_document(1)

        assert result["success"] is False
        assert "Network error" in result["error"]


# =============================================================================
# Tests for handle_webhook
# =============================================================================

class TestHandleWebhook:
    """Test handle_webhook function."""

    @patch('services.notarization_service.SessionLocal')
    def test_webhook_no_transaction_id(self, mock_session_class):
        """Test webhook handling without transaction ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = handle_webhook({"event": "transaction.completed"})

        assert result["success"] is False
        assert "No transaction_id" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_webhook_order_not_found(self, mock_session_class):
        """Test webhook handling when order not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = handle_webhook({
            "transaction_id": "ext_nonexistent",
            "event": "transaction.completed"
        })

        assert result["success"] is False
        assert "No order found" in result["error"]
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.download_notarized_document')
    @patch('services.notarization_service.SessionLocal')
    def test_webhook_completed_event(self, mock_session_class, mock_download):
        """Test webhook handling for completed event."""
        mock_download.return_value = {"success": True}

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "in_progress"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = handle_webhook({
            "transaction_id": "ext_123",
            "event": "transaction.completed"
        })

        assert result["success"] is True
        assert result["order_id"] == 1
        assert "completed" in result["action_taken"]
        mock_download.assert_called_once_with(1)

    @patch('services.notarization_service.download_notarized_document')
    @patch('services.notarization_service.SessionLocal')
    def test_webhook_completed_download_failed(self, mock_session_class, mock_download):
        """Test webhook handling when download fails after completion."""
        mock_download.return_value = {"success": False, "error": "Download failed"}

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "in_progress"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = handle_webhook({
            "transaction_id": "ext_123",
            "event": "transaction.completed"
        })

        assert result["success"] is True
        assert "download failed" in result["action_taken"]

    @patch('services.notarization_service.SessionLocal')
    def test_webhook_various_events(self, mock_session_class):
        """Test webhook handling for various event types."""
        events_to_test = [
            ("transaction.created", "pending"),
            ("transaction.started", "in_progress"),
            ("transaction.scheduled", "scheduled"),
            ("transaction.cancelled", "cancelled"),
            ("transaction.expired", "expired"),
            ("transaction.failed", "failed"),
            ("created", "pending"),
            ("started", "in_progress"),
            ("in_progress", "in_progress"),
            ("scheduled", "scheduled"),
            ("cancelled", "cancelled"),
            ("canceled", "cancelled"),
            ("expired", "expired"),
            ("failed", "failed"),
        ]

        for event_type, expected_status in events_to_test:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_order = MagicMock()
            mock_order.id = 1
            mock_order.status = "pending"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_order

            result = handle_webhook({
                "transaction_id": "ext_123",
                "event": event_type
            })

            assert result["success"] is True, f"Failed for event: {event_type}"
            assert mock_order.status == expected_status, f"Wrong status for event: {event_type}"

    @patch('services.notarization_service.SessionLocal')
    def test_webhook_with_id_field(self, mock_session_class):
        """Test webhook handling with 'id' field instead of 'transaction_id'."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "pending"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = handle_webhook({
            "id": "ext_123",
            "type": "started"
        })

        assert result["success"] is True

    @patch('services.notarization_service.SessionLocal')
    def test_webhook_with_status_field(self, mock_session_class):
        """Test webhook handling with 'status' field instead of 'event'."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "pending"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = handle_webhook({
            "transaction_id": "ext_123",
            "status": "in_progress"
        })

        assert result["success"] is True

    @patch('services.notarization_service.SessionLocal')
    def test_webhook_database_error(self, mock_session_class):
        """Test webhook handling with database error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "pending"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order
        mock_session.commit.side_effect = Exception("Database error")

        result = handle_webhook({
            "transaction_id": "ext_123",
            "event": "transaction.started"
        })

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_webhook_unknown_event_preserves_status(self, mock_session_class):
        """Test webhook with unknown event preserves existing status."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "in_progress"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = handle_webhook({
            "transaction_id": "ext_123",
            "event": "unknown.event"
        })

        assert result["success"] is True
        # Status should remain as is for unknown events
        assert mock_order.status == "in_progress"


# =============================================================================
# Tests for get_order_by_id
# =============================================================================

class TestGetOrderById:
    """Test get_order_by_id function."""

    @patch('services.notarization_service.SessionLocal')
    def test_get_order_by_id_success(self, mock_session_class):
        """Test successfully getting order by ID."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.client_id = 100
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        result = get_order_by_id(1)

        assert result == mock_order
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_get_order_by_id_not_found(self, mock_session_class):
        """Test getting order by ID when not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = get_order_by_id(999)

        assert result is None
        mock_session.close.assert_called_once()


# =============================================================================
# Tests for get_orders_by_client
# =============================================================================

class TestGetOrdersByClient:
    """Test get_orders_by_client function."""

    @patch('services.notarization_service.SessionLocal')
    def test_get_orders_by_client_success(self, mock_session_class):
        """Test successfully getting orders by client."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order1 = MagicMock()
        mock_order1.id = 1
        mock_order2 = MagicMock()
        mock_order2.id = 2

        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_order1, mock_order2
        ]

        result = get_orders_by_client(100)

        assert len(result) == 2
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_get_orders_by_client_with_status_filter(self, mock_session_class):
        """Test getting orders by client with status filter."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "completed"

        mock_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_order]

        result = get_orders_by_client(100, status="completed")

        assert len(result) == 1
        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_get_orders_by_client_empty(self, mock_session_class):
        """Test getting orders when client has none."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_orders_by_client(100)

        assert result == []
        mock_session.close.assert_called_once()


# =============================================================================
# Tests for Session Cleanup
# =============================================================================

class TestSessionCleanup:
    """Test that database sessions are properly closed."""

    @patch('services.notarization_service.requests.post')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service.os.path.exists')
    def test_create_order_closes_session_on_exception(self, mock_exists, mock_session_class, mock_post):
        """Test session is closed after exception in create_notarization_order."""
        mock_exists.return_value = True
        mock_post.side_effect = Exception("Unexpected error")

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        with patch.dict(os.environ, {"PROOF_API_KEY": "test_key"}):
            create_notarization_order(
                client_id=1,
                document_path="/path/doc.pdf",
                document_name="Test",
                signer_email="test@example.com",
                signer_name="Test User"
            )

        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_get_status_closes_session_on_exception(self, mock_session_class):
        """Test session is closed after exception in get_notarization_status."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.side_effect = Exception("Database error")

        get_notarization_status(1)

        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_handle_webhook_closes_session_on_exception(self, mock_session_class):
        """Test session is closed after exception in handle_webhook."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.side_effect = Exception("Query error")

        handle_webhook({"transaction_id": "ext_123"})

        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_get_order_by_id_closes_session(self, mock_session_class):
        """Test session is closed in get_order_by_id."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        get_order_by_id(1)

        mock_session.close.assert_called_once()

    @patch('services.notarization_service.SessionLocal')
    def test_get_orders_by_client_closes_session(self, mock_session_class):
        """Test session is closed in get_orders_by_client."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        get_orders_by_client(1)

        mock_session.close.assert_called_once()


# =============================================================================
# Tests for Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @patch('services.notarization_service.requests.post')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service.os.path.exists')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_create_order_with_url_response_field(self, mock_exists, mock_session_class, mock_post):
        """Test order creation handles 'url' response field for session link."""
        mock_exists.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ext_123",
            "url": "https://notarize.com/session/via_url_field"
        }
        mock_post.return_value = mock_response

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.refresh.side_effect = lambda x: setattr(x, 'id', 1)

        result = create_notarization_order(
            client_id=1,
            document_path="/path/doc.pdf",
            document_name="Test",
            signer_email="test@example.com",
            signer_name="Test User"
        )

        assert result["session_link"] == "https://notarize.com/session/via_url_field"

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service._get_client_upload_folder')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_handles_documents_as_dict(self, mock_get_folder, mock_session_class, mock_get_status, mock_get):
        """Test download handles documents response as dict with 'documents' key."""
        mock_get_status.return_value = {"status": "completed"}
        mock_get_folder.return_value = "/tmp/test"

        mock_docs_response = MagicMock()
        mock_docs_response.status_code = 200
        mock_docs_response.json.return_value = {
            "documents": [{"url": "https://cdn/doc.pdf", "name": "doc"}]
        }

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"%PDF content"

        mock_get.side_effect = [mock_docs_response, mock_download_response]

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.client_id = 100
        mock_order.document_name = "Test"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('builtins.open', MagicMock()):
            result = download_notarized_document(1)

        assert result["success"] is True

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service._get_client_upload_folder')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_handles_download_url_field(self, mock_get_folder, mock_session_class, mock_get_status, mock_get):
        """Test download handles 'download_url' field in document response."""
        mock_get_status.return_value = {"status": "completed"}
        mock_get_folder.return_value = "/tmp/test"

        mock_docs_response = MagicMock()
        mock_docs_response.status_code = 200
        mock_docs_response.json.return_value = [
            {"download_url": "https://cdn/doc.pdf", "name": "doc"}
        ]

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"%PDF content"

        mock_get.side_effect = [mock_docs_response, mock_download_response]

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.client_id = 100
        mock_order.document_name = "Test"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('builtins.open', MagicMock()):
            result = download_notarized_document(1)

        assert result["success"] is True

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service._get_client_upload_folder')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_handles_resource_field(self, mock_get_folder, mock_session_class, mock_get_status, mock_get):
        """Test download handles 'resource' field in document response."""
        mock_get_status.return_value = {"status": "completed"}
        mock_get_folder.return_value = "/tmp/test"

        mock_docs_response = MagicMock()
        mock_docs_response.status_code = 200
        mock_docs_response.json.return_value = [
            {"resource": "https://cdn/doc.pdf", "name": "doc"}
        ]

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"%PDF content"

        mock_get.side_effect = [mock_docs_response, mock_download_response]

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.client_id = 100
        mock_order.document_name = "Test"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('builtins.open', MagicMock()):
            result = download_notarized_document(1)

        assert result["success"] is True

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service._get_client_upload_folder')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_skips_document_without_url(self, mock_get_folder, mock_session_class, mock_get_status, mock_get):
        """Test download skips documents without URL."""
        mock_get_status.return_value = {"status": "completed"}
        mock_get_folder.return_value = "/tmp/test"

        mock_docs_response = MagicMock()
        mock_docs_response.status_code = 200
        mock_docs_response.json.return_value = [
            {"name": "doc_without_url"},  # No URL field
            {"url": "https://cdn/doc.pdf", "name": "doc_with_url"}
        ]

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"%PDF content"

        mock_get.side_effect = [mock_docs_response, mock_download_response]

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.client_id = 100
        mock_order.document_name = "Test"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('builtins.open', MagicMock()):
            result = download_notarized_document(1)

        # Should still succeed with the document that has URL
        assert result["success"] is True

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service._get_client_upload_folder')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_no_notarized_document_only_audit(self, mock_get_folder, mock_session_class, mock_get_status, mock_get):
        """Test download fails when only audit trail available (no main doc)."""
        mock_get_status.return_value = {"status": "completed"}
        mock_get_folder.return_value = "/tmp/test"

        mock_docs_response = MagicMock()
        mock_docs_response.status_code = 200
        mock_docs_response.json.return_value = [
            {"url": "https://cdn/audit.pdf", "name": "audit_trail", "type": "audit"}
        ]

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"%PDF audit content"

        mock_get.side_effect = [mock_docs_response, mock_download_response]

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.client_id = 100
        mock_order.document_name = "Test"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('builtins.open', MagicMock()):
            result = download_notarized_document(1)

        assert result["success"] is False
        assert result["audit_trail_path"] is not None
        assert "Could not download notarized document" in result["error"]

    @patch('services.notarization_service.requests.get')
    @patch('services.notarization_service.get_notarization_status')
    @patch('services.notarization_service.SessionLocal')
    @patch('services.notarization_service._get_client_upload_folder')
    @patch.dict(os.environ, {"PROOF_API_KEY": "test_key"})
    def test_download_sanitizes_document_name(self, mock_get_folder, mock_session_class, mock_get_status, mock_get):
        """Test download sanitizes document name for filename."""
        mock_get_status.return_value = {"status": "completed"}
        mock_get_folder.return_value = "/tmp/test"

        mock_docs_response = MagicMock()
        mock_docs_response.status_code = 200
        mock_docs_response.json.return_value = [
            {"url": "https://cdn/doc.pdf", "name": "document"}
        ]

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"%PDF content"

        mock_get.side_effect = [mock_docs_response, mock_download_response]

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.external_transaction_id = "ext_123"
        mock_order.client_id = 100
        mock_order.document_name = "Test@Doc#With$Special%Chars!"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('builtins.open', MagicMock()):
            result = download_notarized_document(1)

        assert result["success"] is True
        # The file path should have sanitized name
        assert "@" not in result["file_path"]
        assert "#" not in result["file_path"]
        assert "$" not in result["file_path"]
        assert "%" not in result["file_path"]

    @patch('services.notarization_service.SessionLocal')
    def test_webhook_sets_updated_at(self, mock_session_class):
        """Test webhook sets updated_at timestamp."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "pending"
        mock_order.updated_at = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        handle_webhook({
            "transaction_id": "ext_123",
            "event": "transaction.started"
        })

        assert mock_order.updated_at is not None

    @patch('services.notarization_service.download_notarized_document')
    @patch('services.notarization_service.SessionLocal')
    def test_webhook_completed_sets_notarized_at(self, mock_session_class, mock_download):
        """Test webhook sets notarized_at when completed."""
        mock_download.return_value = {"success": True}

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "in_progress"
        mock_order.notarized_at = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_order

        handle_webhook({
            "transaction_id": "ext_123",
            "event": "transaction.completed"
        })

        assert mock_order.notarized_at is not None
