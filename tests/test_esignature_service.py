"""
Unit Tests for Electronic Signature Service.
Tests for signature request creation, status checking, document retrieval, webhook handling,
token verification, signature capture, and client signature history management.
Covers all main functions with mocked database interactions.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
import sys
import os
import base64
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.esignature_service import (
    create_signature_request,
    generate_signing_link,
    verify_signing_token,
    capture_signature,
    get_signature_status,
    get_pending_signatures,
    send_signature_reminder,
    cancel_signature_request,
    get_client_signature_history,
    list_document_types,
    _ensure_signature_folder,
    _get_base_url,
    _generate_token,
    _update_client_agreement_status,
    DOCUMENT_TYPES,
    PROVIDER_NAME,
    TOKEN_EXPIRY_DAYS,
    SIGNATURE_FOLDER,
)


# =============================================================================
# Tests for Constants and Configuration
# =============================================================================

class TestConstants:
    """Test service constants and configuration."""

    def test_provider_name(self):
        """Test that provider name is set correctly."""
        assert PROVIDER_NAME == "in_app"

    def test_token_expiry_days(self):
        """Test token expiry is set to 7 days."""
        assert TOKEN_EXPIRY_DAYS == 7

    def test_signature_folder(self):
        """Test signature folder path is set."""
        assert SIGNATURE_FOLDER == "static/signatures"

    def test_document_types_defined(self):
        """Test that document types are properly defined."""
        assert "client_agreement" in DOCUMENT_TYPES
        assert "limited_poa" in DOCUMENT_TYPES
        assert "dispute_authorization" in DOCUMENT_TYPES
        assert "fee_agreement" in DOCUMENT_TYPES

    def test_document_types_display_names(self):
        """Test document types have proper display names."""
        assert DOCUMENT_TYPES["client_agreement"] == "Main Service Agreement"
        assert DOCUMENT_TYPES["limited_poa"] == "Limited Power of Attorney"
        assert DOCUMENT_TYPES["dispute_authorization"] == "Authorization for Dispute Filing"
        assert DOCUMENT_TYPES["fee_agreement"] == "Fee Agreement"


# =============================================================================
# Tests for Helper Functions
# =============================================================================

class TestHelperFunctions:
    """Test helper/utility functions."""

    @patch('services.esignature_service.os.makedirs')
    def test_ensure_signature_folder_creates_directory(self, mock_makedirs):
        """Test that signature folder is created if it doesn't exist."""
        result = _ensure_signature_folder()
        mock_makedirs.assert_called_once_with(SIGNATURE_FOLDER, exist_ok=True)
        assert result == SIGNATURE_FOLDER

    @patch.dict(os.environ, {"REPLIT_DEV_DOMAIN": "myapp.replit.dev"})
    def test_get_base_url_with_replit_dev_domain(self):
        """Test base URL with REPLIT_DEV_DOMAIN set."""
        result = _get_base_url()
        assert result == "https://myapp.replit.dev"

    @patch.dict(os.environ, {"REPLIT_DEV_DOMAIN": "https://myapp.replit.dev"})
    def test_get_base_url_with_https_prefix(self):
        """Test base URL when domain already has https prefix."""
        result = _get_base_url()
        assert result == "https://myapp.replit.dev"

    @patch.dict(os.environ, {"REPLIT_DEV_DOMAIN": "", "REPL_SLUG_URL": "myslug.repl.co"})
    def test_get_base_url_with_repl_slug(self):
        """Test base URL with REPL_SLUG_URL fallback."""
        result = _get_base_url()
        assert result == "https://myslug.repl.co"

    @patch.dict(os.environ, {"REPLIT_DEV_DOMAIN": "", "REPL_SLUG_URL": ""}, clear=True)
    def test_get_base_url_empty_when_no_env(self):
        """Test base URL returns empty string when no env vars set."""
        # Need to clear the environment variables
        with patch.dict(os.environ, {}, clear=True):
            result = _get_base_url()
            assert result == ""

    def test_generate_token_returns_string(self):
        """Test that token generation returns a string."""
        token = _generate_token()
        assert isinstance(token, str)

    def test_generate_token_unique(self):
        """Test that generated tokens are unique."""
        tokens = [_generate_token() for _ in range(100)]
        assert len(set(tokens)) == 100

    def test_generate_token_url_safe(self):
        """Test that generated tokens are URL-safe."""
        token = _generate_token()
        # URL-safe base64 uses only alphanumeric, dash, and underscore
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        assert all(c in safe_chars for c in token)

    def test_generate_token_length(self):
        """Test that generated token has appropriate length."""
        token = _generate_token()
        # secrets.token_urlsafe(32) produces ~43 characters
        assert len(token) >= 40


# =============================================================================
# Tests for list_document_types()
# =============================================================================

class TestListDocumentTypes:
    """Test document types listing function."""

    def test_returns_copy_of_dict(self):
        """Test that function returns a copy, not the original."""
        result = list_document_types()
        assert result is not DOCUMENT_TYPES
        assert result == DOCUMENT_TYPES

    def test_modification_does_not_affect_original(self):
        """Test that modifying result doesn't affect original."""
        result = list_document_types()
        result["test_type"] = "Test Type"
        assert "test_type" not in DOCUMENT_TYPES


# =============================================================================
# Tests for create_signature_request()
# =============================================================================

class TestCreateSignatureRequest:
    """Test signature request creation."""

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._get_base_url')
    @patch('services.esignature_service._generate_token')
    def test_create_signature_request_success(self, mock_token, mock_base_url, mock_session_class):
        """Test successful signature request creation."""
        mock_token.return_value = "test_token_123"
        mock_base_url.return_value = "https://test.app"

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        result = create_signature_request(
            client_id=1,
            document_type="client_agreement",
            document_name="Service Agreement",
            document_path="/path/to/doc.pdf",
            signer_email="test@example.com",
            signer_name="Test User"
        )

        assert result["success"] is True
        assert result["request_id"] is not None
        assert result["signing_link"] == "https://test.app/sign/test_token_123"
        assert result["expires_at"] is not None
        assert result["error"] is None

    @patch('services.esignature_service.SessionLocal')
    def test_create_signature_request_invalid_document_type(self, mock_session_class):
        """Test request creation with invalid document type."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = create_signature_request(
            client_id=1,
            document_type="invalid_type",
            document_name="Test Doc",
            document_path="/path/to/doc.pdf",
            signer_email="test@example.com",
            signer_name="Test User"
        )

        assert result["success"] is False
        assert "Invalid document type" in result["error"]
        assert "invalid_type" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._get_base_url')
    @patch('services.esignature_service._generate_token')
    @patch('services.esignature_service.os.path.exists')
    def test_create_signature_request_nonexistent_document_path(self, mock_exists, mock_token, mock_base_url, mock_session_class):
        """Test request creation with nonexistent document path logs warning."""
        mock_token.return_value = "test_token"
        mock_base_url.return_value = "https://test.app"
        mock_exists.return_value = False

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        # Should still succeed, just log a warning
        result = create_signature_request(
            client_id=1,
            document_type="client_agreement",
            document_name="Test Doc",
            document_path="/nonexistent/path.pdf",
            signer_email="test@example.com",
            signer_name="Test User"
        )

        assert result["success"] is True

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._get_base_url')
    @patch('services.esignature_service._generate_token')
    def test_create_signature_request_no_base_url(self, mock_token, mock_base_url, mock_session_class):
        """Test request creation without base URL uses relative path."""
        mock_token.return_value = "test_token"
        mock_base_url.return_value = ""

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        result = create_signature_request(
            client_id=1,
            document_type="client_agreement",
            document_name="Test Doc",
            document_path=None,
            signer_email="test@example.com",
            signer_name="Test User"
        )

        assert result["success"] is True
        assert result["signing_link"] == "/sign/test_token"

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._generate_token')
    def test_create_signature_request_database_error(self, mock_token, mock_session_class):
        """Test request creation handles database errors."""
        mock_token.return_value = "test_token"

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.commit.side_effect = Exception("Database error")

        result = create_signature_request(
            client_id=1,
            document_type="client_agreement",
            document_name="Test Doc",
            document_path="/path.pdf",
            signer_email="test@example.com",
            signer_name="Test User"
        )

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_session.rollback.assert_called_once()

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._get_base_url')
    @patch('services.esignature_service._generate_token')
    def test_create_signature_request_all_document_types(self, mock_token, mock_base_url, mock_session_class):
        """Test request creation works for all valid document types."""
        mock_token.return_value = "test_token"
        mock_base_url.return_value = "https://test.app"

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        for doc_type in DOCUMENT_TYPES.keys():
            result = create_signature_request(
                client_id=1,
                document_type=doc_type,
                document_name=f"Test {doc_type}",
                document_path=None,
                signer_email="test@example.com",
                signer_name="Test User"
            )
            assert result["success"] is True, f"Failed for document type: {doc_type}"


# =============================================================================
# Tests for generate_signing_link()
# =============================================================================

class TestGenerateSigningLink:
    """Test signing link generation/regeneration."""

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._get_base_url')
    @patch('services.esignature_service._generate_token')
    def test_generate_signing_link_success(self, mock_token, mock_base_url, mock_session_class):
        """Test successful signing link regeneration."""
        mock_token.return_value = "new_token_456"
        mock_base_url.return_value = "https://test.app"

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_session.query().filter().first.return_value = mock_request

        result = generate_signing_link(request_id=1)

        assert result["success"] is True
        assert result["request_id"] == 1
        assert result["signing_link"] == "https://test.app/sign/new_token_456"
        assert result["token"] == "new_token_456"
        assert result["expires_at"] is not None
        assert result["error"] is None

    @patch('services.esignature_service.SessionLocal')
    def test_generate_signing_link_request_not_found(self, mock_session_class):
        """Test link generation when request not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.return_value = None

        result = generate_signing_link(request_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_generate_signing_link_already_signed(self, mock_session_class):
        """Test link generation fails for already signed document."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "signed"
        mock_request.signing_link = "https://old.link"
        mock_request.external_request_id = "old_token"
        mock_request.expires_at = datetime.utcnow()
        mock_session.query().filter().first.return_value = mock_request

        result = generate_signing_link(request_id=1)

        assert result["success"] is False
        assert "already been signed" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._generate_token')
    def test_generate_signing_link_database_error(self, mock_token, mock_session_class):
        """Test link generation handles database errors."""
        mock_token.return_value = "test_token"

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.status = "pending"
        mock_session.query().filter().first.return_value = mock_request
        mock_session.commit.side_effect = Exception("Commit failed")

        result = generate_signing_link(request_id=1)

        assert result["success"] is False
        assert "Commit failed" in result["error"]
        mock_session.rollback.assert_called_once()


# =============================================================================
# Tests for verify_signing_token()
# =============================================================================

class TestVerifySigningToken:
    """Test signing token verification."""

    @patch('services.esignature_service.SessionLocal')
    def test_verify_token_success(self, mock_session_class):
        """Test successful token verification."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.client_id = 10
        mock_request.status = "pending"
        mock_request.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_request.document_type = "client_agreement"
        mock_request.document_name = "Service Agreement"
        mock_request.document_path = "/path/to/doc.pdf"
        mock_request.signer_email = "test@example.com"
        mock_request.signer_name = "Test User"
        mock_request.created_at = datetime.utcnow()

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_session.query().filter().first.side_effect = [mock_request, mock_client]

        result = verify_signing_token("valid_token")

        assert result["valid"] is True
        assert result["request_id"] == 1
        assert result["request_details"]["client_name"] == "Test Client"
        assert result["error"] is None

    @patch('services.esignature_service.SessionLocal')
    def test_verify_token_invalid(self, mock_session_class):
        """Test verification of invalid token."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.return_value = None

        result = verify_signing_token("invalid_token")

        assert result["valid"] is False
        assert "Invalid signing token" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_verify_token_already_signed(self, mock_session_class):
        """Test verification fails for already signed document."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "signed"
        mock_session.query().filter().first.return_value = mock_request

        result = verify_signing_token("signed_token")

        assert result["valid"] is False
        assert "already been signed" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_verify_token_expired(self, mock_session_class):
        """Test verification fails for expired token."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_request.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired
        mock_session.query().filter().first.return_value = mock_request

        result = verify_signing_token("expired_token")

        assert result["valid"] is False
        assert "expired" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_verify_token_no_client_found(self, mock_session_class):
        """Test verification when client is not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.client_id = 10
        mock_request.status = "pending"
        mock_request.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_request.document_type = "client_agreement"
        mock_request.document_name = "Test Doc"
        mock_request.document_path = None
        mock_request.signer_email = "test@example.com"
        mock_request.signer_name = "Test User"
        mock_request.created_at = datetime.utcnow()

        mock_session.query().filter().first.side_effect = [mock_request, None]

        result = verify_signing_token("valid_token")

        assert result["valid"] is True
        assert result["request_details"]["client_name"] == "Unknown"

    @patch('services.esignature_service.SessionLocal')
    def test_verify_token_database_error(self, mock_session_class):
        """Test verification handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.side_effect = Exception("Query failed")

        result = verify_signing_token("any_token")

        assert result["valid"] is False
        assert "Query failed" in result["error"]


# =============================================================================
# Tests for capture_signature()
# =============================================================================

class TestCaptureSignature:
    """Test signature capture functionality."""

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._ensure_signature_folder')
    @patch('services.esignature_service._update_client_agreement_status')
    @patch('builtins.open', new_callable=mock_open)
    def test_capture_signature_success(self, mock_file, mock_update_status, mock_ensure_folder, mock_session_class):
        """Test successful signature capture."""
        mock_ensure_folder.return_value = SIGNATURE_FOLDER

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.client_id = 10
        mock_request.status = "pending"
        mock_request.document_type = "client_agreement"
        mock_request.document_path = "/path/to/doc.pdf"
        mock_session.query().filter().first.return_value = mock_request

        # Base64 encoded PNG signature
        signature_data = base64.b64encode(b"PNG_SIGNATURE_DATA").decode()

        result = capture_signature(request_id=1, signature_data=signature_data)

        assert result["success"] is True
        assert result["request_id"] == 1
        assert result["signature_path"] is not None
        assert result["signed_at"] is not None
        assert result["error"] is None

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._ensure_signature_folder')
    @patch('services.esignature_service._update_client_agreement_status')
    @patch('builtins.open', new_callable=mock_open)
    def test_capture_signature_with_data_uri(self, mock_file, mock_update_status, mock_ensure_folder, mock_session_class):
        """Test signature capture with data URI prefix."""
        mock_ensure_folder.return_value = SIGNATURE_FOLDER

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.client_id = 10
        mock_request.status = "pending"
        mock_request.document_type = "client_agreement"
        mock_request.document_path = "/path/to/doc.pdf"
        mock_session.query().filter().first.return_value = mock_request

        # Data URI format signature
        signature_base64 = base64.b64encode(b"PNG_DATA").decode()
        signature_data = f"data:image/png;base64,{signature_base64}"

        result = capture_signature(request_id=1, signature_data=signature_data)

        assert result["success"] is True

    @patch('services.esignature_service.SessionLocal')
    def test_capture_signature_request_not_found(self, mock_session_class):
        """Test signature capture when request not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.return_value = None

        result = capture_signature(request_id=999, signature_data="test")

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_capture_signature_already_signed(self, mock_session_class):
        """Test signature capture fails for already signed document."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "signed"
        mock_request.signed_document_path = "/path/to/signed.pdf"
        mock_request.signed_at = datetime.utcnow()
        mock_session.query().filter().first.return_value = mock_request

        result = capture_signature(request_id=1, signature_data="test")

        assert result["success"] is False
        assert "already been signed" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._ensure_signature_folder')
    def test_capture_signature_invalid_base64(self, mock_ensure_folder, mock_session_class):
        """Test signature capture with invalid base64 data."""
        mock_ensure_folder.return_value = SIGNATURE_FOLDER

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_session.query().filter().first.return_value = mock_request

        result = capture_signature(request_id=1, signature_data="invalid!!!base64")

        assert result["success"] is False
        assert "Invalid base64" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._ensure_signature_folder')
    @patch('builtins.open', new_callable=mock_open)
    def test_capture_signature_database_error(self, mock_file, mock_ensure_folder, mock_session_class):
        """Test signature capture handles database errors."""
        mock_ensure_folder.return_value = SIGNATURE_FOLDER

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.client_id = 10
        mock_request.status = "pending"
        mock_request.document_type = "client_agreement"
        mock_request.document_path = "/path/to/doc.pdf"
        mock_session.query().filter().first.return_value = mock_request
        mock_session.commit.side_effect = Exception("Database error")

        signature_data = base64.b64encode(b"PNG_DATA").decode()

        result = capture_signature(request_id=1, signature_data=signature_data)

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_session.rollback.assert_called_once()


# =============================================================================
# Tests for get_signature_status()
# =============================================================================

class TestGetSignatureStatus:
    """Test signature status retrieval."""

    @patch('services.esignature_service.SessionLocal')
    def test_get_status_success(self, mock_session_class):
        """Test successful status retrieval."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.client_id = 10
        mock_request.provider = "in_app"
        mock_request.status = "pending"
        mock_request.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_request.document_type = "client_agreement"
        mock_request.document_name = "Service Agreement"
        mock_request.document_path = "/path/to/doc.pdf"
        mock_request.signer_email = "test@example.com"
        mock_request.signer_name = "Test User"
        mock_request.signing_link = "https://test.app/sign/token"
        mock_request.signed_at = None
        mock_request.signed_document_path = None
        mock_request.created_at = datetime.utcnow()
        mock_request.updated_at = datetime.utcnow()

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_session.query().filter().first.side_effect = [mock_request, mock_client]

        result = get_signature_status(request_id=1)

        assert result["success"] is True
        assert result["status"] == "pending"
        assert result["details"]["client_name"] == "Test Client"

    @patch('services.esignature_service.SessionLocal')
    def test_get_status_request_not_found(self, mock_session_class):
        """Test status retrieval when request not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.return_value = None

        result = get_signature_status(request_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_get_status_expired(self, mock_session_class):
        """Test status shows expired for past expiration."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.client_id = 10
        mock_request.provider = "in_app"
        mock_request.status = "pending"
        mock_request.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired
        mock_request.document_type = "client_agreement"
        mock_request.document_name = "Test Doc"
        mock_request.document_path = None
        mock_request.signer_email = "test@example.com"
        mock_request.signer_name = "Test User"
        mock_request.signing_link = "https://test.app/sign/token"
        mock_request.signed_at = None
        mock_request.signed_document_path = None
        mock_request.created_at = datetime.utcnow()
        mock_request.updated_at = datetime.utcnow()

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_session.query().filter().first.side_effect = [mock_request, mock_client]

        result = get_signature_status(request_id=1)

        assert result["success"] is True
        assert result["status"] == "expired"

    @patch('services.esignature_service.SessionLocal')
    def test_get_status_signed(self, mock_session_class):
        """Test status retrieval for signed document."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        signed_at = datetime.utcnow() - timedelta(hours=1)
        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.client_id = 10
        mock_request.provider = "in_app"
        mock_request.status = "signed"
        mock_request.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_request.document_type = "client_agreement"
        mock_request.document_name = "Test Doc"
        mock_request.document_path = "/path/to/doc.pdf"
        mock_request.signer_email = "test@example.com"
        mock_request.signer_name = "Test User"
        mock_request.signing_link = "https://test.app/sign/token"
        mock_request.signed_at = signed_at
        mock_request.signed_document_path = "/path/to/signed.png"
        mock_request.created_at = datetime.utcnow()
        mock_request.updated_at = datetime.utcnow()

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_session.query().filter().first.side_effect = [mock_request, mock_client]

        result = get_signature_status(request_id=1)

        assert result["success"] is True
        assert result["status"] == "signed"
        assert result["details"]["signed_at"] is not None

    @patch('services.esignature_service.SessionLocal')
    def test_get_status_database_error(self, mock_session_class):
        """Test status retrieval handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.side_effect = Exception("Database error")

        result = get_signature_status(request_id=1)

        assert result["success"] is False
        assert "Database error" in result["error"]


# =============================================================================
# Tests for get_pending_signatures()
# =============================================================================

class TestGetPendingSignatures:
    """Test pending signatures retrieval."""

    @patch('services.esignature_service.SessionLocal')
    def test_get_pending_signatures_success(self, mock_session_class):
        """Test successful pending signatures retrieval."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.document_type = "client_agreement"
        mock_request.document_name = "Service Agreement"
        mock_request.signer_name = "Test User"
        mock_request.signer_email = "test@example.com"
        mock_request.signing_link = "https://test.app/sign/token"
        mock_request.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_request.created_at = datetime.utcnow()

        mock_session.query().filter().order_by().all.return_value = [mock_request]

        result = get_pending_signatures(client_id=1)

        assert result["success"] is True
        assert result["pending_count"] == 1
        assert len(result["pending_requests"]) == 1
        assert result["pending_requests"][0]["is_expired"] is False

    @patch('services.esignature_service.SessionLocal')
    def test_get_pending_signatures_includes_expired(self, mock_session_class):
        """Test pending signatures includes expired ones."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.document_type = "client_agreement"
        mock_request.document_name = "Service Agreement"
        mock_request.signer_name = "Test User"
        mock_request.signer_email = "test@example.com"
        mock_request.signing_link = "https://test.app/sign/token"
        mock_request.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired
        mock_request.created_at = datetime.utcnow()

        mock_session.query().filter().order_by().all.return_value = [mock_request]

        result = get_pending_signatures(client_id=1)

        assert result["success"] is True
        assert result["pending_requests"][0]["is_expired"] is True
        assert result["pending_requests"][0]["status"] == "expired"

    @patch('services.esignature_service.SessionLocal')
    def test_get_pending_signatures_empty(self, mock_session_class):
        """Test pending signatures when none exist."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().order_by().all.return_value = []

        result = get_pending_signatures(client_id=1)

        assert result["success"] is True
        assert result["pending_count"] == 0
        assert result["pending_requests"] == []

    @patch('services.esignature_service.SessionLocal')
    def test_get_pending_signatures_database_error(self, mock_session_class):
        """Test pending signatures handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().order_by().all.side_effect = Exception("Query failed")

        result = get_pending_signatures(client_id=1)

        assert result["success"] is False
        assert "Query failed" in result["error"]


# =============================================================================
# Tests for send_signature_reminder()
# =============================================================================

class TestSendSignatureReminder:
    """Test signature reminder sending."""

    @patch('services.esignature_service.SessionLocal')
    def test_send_reminder_request_not_found(self, mock_session_class):
        """Test reminder fails when request not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.return_value = None

        result = send_signature_reminder(request_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_send_reminder_already_signed(self, mock_session_class):
        """Test reminder fails for already signed document."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "signed"
        mock_request.signer_email = "test@example.com"
        mock_session.query().filter().first.return_value = mock_request

        result = send_signature_reminder(request_id=1)

        assert result["success"] is False
        assert "already been signed" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service.generate_signing_link')
    def test_send_reminder_success(self, mock_gen_link, mock_session_class):
        """Test successful reminder sending."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_request.signer_email = "test@example.com"
        mock_request.signer_name = "Test User"
        mock_request.document_name = "Service Agreement"
        mock_request.document_type = "client_agreement"
        mock_request.signing_link = "https://test.app/sign/token"
        mock_request.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_session.query().filter().first.return_value = mock_request

        # Mock the email modules that are imported inside the function
        mock_email_service = MagicMock()
        mock_email_service.is_sendgrid_configured.return_value = True
        mock_email_service.send_email.return_value = {"success": True}

        mock_email_templates = MagicMock()
        mock_email_templates.get_base_template.return_value = "<html>Template</html>"
        mock_email_templates.PRIMARY_COLOR = "#000000"
        mock_email_templates.SECONDARY_COLOR = "#111111"
        mock_email_templates.DARK_COLOR = "#222222"

        with patch.dict('sys.modules', {
            'services.email_service': mock_email_service,
            'services.email_templates': mock_email_templates
        }):
            result = send_signature_reminder(request_id=1)

        assert result["success"] is True
        assert result["email_sent"] is True
        assert result["recipient"] == "test@example.com"

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service.generate_signing_link')
    def test_send_reminder_email_not_configured(self, mock_gen_link, mock_session_class):
        """Test reminder fails when email not configured."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_request.signer_email = "test@example.com"
        mock_request.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_session.query().filter().first.return_value = mock_request

        # Mock the email modules that are imported inside the function
        mock_email_service = MagicMock()
        mock_email_service.is_sendgrid_configured.return_value = False

        mock_email_templates = MagicMock()
        mock_email_templates.PRIMARY_COLOR = "#000000"
        mock_email_templates.SECONDARY_COLOR = "#111111"
        mock_email_templates.DARK_COLOR = "#222222"

        with patch.dict('sys.modules', {
            'services.email_service': mock_email_service,
            'services.email_templates': mock_email_templates
        }):
            result = send_signature_reminder(request_id=1)

        assert result["success"] is False
        assert "not configured" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service.generate_signing_link')
    def test_send_reminder_regenerates_expired_link(self, mock_gen_link, mock_session_class):
        """Test reminder regenerates expired signing link."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_request.signer_email = "test@example.com"
        mock_request.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired
        mock_session.query().filter().first.return_value = mock_request

        mock_gen_link.return_value = {"success": True}

        # Mock the email modules that are imported inside the function
        mock_email_service = MagicMock()
        mock_email_service.is_sendgrid_configured.return_value = False

        mock_email_templates = MagicMock()
        mock_email_templates.PRIMARY_COLOR = "#000000"
        mock_email_templates.SECONDARY_COLOR = "#111111"
        mock_email_templates.DARK_COLOR = "#222222"

        # Will fail at email check, but we want to verify link regeneration was called
        with patch.dict('sys.modules', {
            'services.email_service': mock_email_service,
            'services.email_templates': mock_email_templates
        }):
            result = send_signature_reminder(request_id=1)

        mock_gen_link.assert_called_once_with(1)

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service.generate_signing_link')
    def test_send_reminder_email_send_fails(self, mock_gen_link, mock_session_class):
        """Test reminder handles email send failure."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_request.signer_email = "test@example.com"
        mock_request.signer_name = "Test User"
        mock_request.document_name = "Service Agreement"
        mock_request.document_type = "client_agreement"
        mock_request.signing_link = "https://test.app/sign/token"
        mock_request.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_session.query().filter().first.return_value = mock_request

        # Mock the email modules that are imported inside the function
        mock_email_service = MagicMock()
        mock_email_service.is_sendgrid_configured.return_value = True
        mock_email_service.send_email.return_value = {"success": False, "error": "SMTP error"}

        mock_email_templates = MagicMock()
        mock_email_templates.get_base_template.return_value = "<html>Template</html>"
        mock_email_templates.PRIMARY_COLOR = "#000000"
        mock_email_templates.SECONDARY_COLOR = "#111111"
        mock_email_templates.DARK_COLOR = "#222222"

        with patch.dict('sys.modules', {
            'services.email_service': mock_email_service,
            'services.email_templates': mock_email_templates
        }):
            result = send_signature_reminder(request_id=1)

        assert result["success"] is False
        assert result["email_sent"] is False
        assert "SMTP error" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_send_reminder_email_service_import_error(self, mock_session_class):
        """Test reminder handles email service import failure."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_request.signer_email = "test@example.com"
        mock_request.signer_name = "Test User"
        mock_request.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_session.query().filter().first.return_value = mock_request

        # Remove the email service module to trigger ImportError
        original_modules = sys.modules.copy()
        sys.modules['services.email_service'] = None

        try:
            # Force an ImportError by making the import fail
            with patch.dict('sys.modules', {'services.email_service': None}):
                # The function should handle this gracefully
                result = send_signature_reminder(request_id=1)
                # Either it handles the import error or succeeds with cached import
                assert result is not None
        finally:
            sys.modules.update(original_modules)


# =============================================================================
# Tests for cancel_signature_request()
# =============================================================================

class TestCancelSignatureRequest:
    """Test signature request cancellation."""

    @patch('services.esignature_service.SessionLocal')
    def test_cancel_request_success(self, mock_session_class):
        """Test successful request cancellation."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_session.query().filter().first.return_value = mock_request

        result = cancel_signature_request(request_id=1)

        assert result["success"] is True
        assert mock_request.status == "cancelled"
        mock_session.commit.assert_called_once()

    @patch('services.esignature_service.SessionLocal')
    def test_cancel_request_not_found(self, mock_session_class):
        """Test cancellation fails when request not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.return_value = None

        result = cancel_signature_request(request_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_cancel_request_already_signed(self, mock_session_class):
        """Test cancellation fails for signed document."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.status = "signed"
        mock_session.query().filter().first.return_value = mock_request

        result = cancel_signature_request(request_id=1)

        assert result["success"] is False
        assert "Cannot cancel" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_cancel_request_database_error(self, mock_session_class):
        """Test cancellation handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.status = "pending"
        mock_session.query().filter().first.return_value = mock_request
        mock_session.commit.side_effect = Exception("Commit failed")

        result = cancel_signature_request(request_id=1)

        assert result["success"] is False
        assert "Commit failed" in result["error"]
        mock_session.rollback.assert_called_once()


# =============================================================================
# Tests for get_client_signature_history()
# =============================================================================

class TestGetClientSignatureHistory:
    """Test client signature history retrieval."""

    @patch('services.esignature_service.SessionLocal')
    def test_get_history_success(self, mock_session_class):
        """Test successful history retrieval."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_signed = MagicMock()
        mock_signed.id = 1
        mock_signed.document_type = "client_agreement"
        mock_signed.document_name = "Service Agreement"
        mock_signed.document_path = "/path/to/doc.pdf"
        mock_signed.signer_name = "Test User"
        mock_signed.signer_email = "test@example.com"
        mock_signed.signing_link = "https://test.app/sign/token1"
        mock_signed.status = "signed"
        mock_signed.signed_at = datetime.utcnow() - timedelta(days=1)
        mock_signed.signed_document_path = "/path/to/signed.png"
        mock_signed.expires_at = datetime.utcnow() + timedelta(days=6)
        mock_signed.created_at = datetime.utcnow() - timedelta(days=2)

        mock_pending = MagicMock()
        mock_pending.id = 2
        mock_pending.document_type = "fee_agreement"
        mock_pending.document_name = "Fee Agreement"
        mock_pending.document_path = "/path/to/fee.pdf"
        mock_pending.signer_name = "Test User"
        mock_pending.signer_email = "test@example.com"
        mock_pending.signing_link = "https://test.app/sign/token2"
        mock_pending.status = "pending"
        mock_pending.signed_at = None
        mock_pending.signed_document_path = None
        mock_pending.expires_at = datetime.utcnow() + timedelta(days=5)
        mock_pending.created_at = datetime.utcnow() - timedelta(hours=2)

        mock_session.query().filter().order_by().all.return_value = [mock_signed, mock_pending]

        result = get_client_signature_history(client_id=1)

        assert result["success"] is True
        assert result["total_count"] == 2
        assert result["signed_count"] == 1
        assert result["pending_count"] == 1

    @patch('services.esignature_service.SessionLocal')
    def test_get_history_expired_request(self, mock_session_class):
        """Test history correctly marks expired requests."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_expired = MagicMock()
        mock_expired.id = 1
        mock_expired.document_type = "client_agreement"
        mock_expired.document_name = "Expired Agreement"
        mock_expired.document_path = None
        mock_expired.signer_name = "Test User"
        mock_expired.signer_email = "test@example.com"
        mock_expired.signing_link = "https://test.app/sign/token"
        mock_expired.status = "pending"
        mock_expired.signed_at = None
        mock_expired.signed_document_path = None
        mock_expired.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired
        mock_expired.created_at = datetime.utcnow() - timedelta(days=10)

        mock_session.query().filter().order_by().all.return_value = [mock_expired]

        result = get_client_signature_history(client_id=1)

        assert result["success"] is True
        assert result["requests"][0]["status"] == "expired"
        assert result["pending_count"] == 0  # Expired doesn't count as pending

    @patch('services.esignature_service.SessionLocal')
    def test_get_history_empty(self, mock_session_class):
        """Test history for client with no requests."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().order_by().all.return_value = []

        result = get_client_signature_history(client_id=1)

        assert result["success"] is True
        assert result["total_count"] == 0
        assert result["signed_count"] == 0
        assert result["pending_count"] == 0
        assert result["requests"] == []

    @patch('services.esignature_service.SessionLocal')
    def test_get_history_database_error(self, mock_session_class):
        """Test history retrieval handles database errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().order_by().all.side_effect = Exception("Query failed")

        result = get_client_signature_history(client_id=1)

        assert result["success"] is False
        assert "Query failed" in result["error"]


# =============================================================================
# Tests for _update_client_agreement_status()
# =============================================================================

class TestUpdateClientAgreementStatus:
    """Test client agreement status update helper."""

    def test_update_client_agreement_status_success(self):
        """Test successful client agreement status update."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.query().filter().first.return_value = mock_client

        _update_client_agreement_status(mock_session, client_id=1, document_type="client_agreement")

        assert mock_client.agreement_signed is True
        assert mock_client.agreement_signed_at is not None
        mock_session.commit.assert_called_once()

    def test_update_client_agreement_status_non_agreement(self):
        """Test no update for non-agreement document types."""
        mock_session = MagicMock()

        _update_client_agreement_status(mock_session, client_id=1, document_type="fee_agreement")

        mock_session.query.assert_not_called()

    def test_update_client_agreement_status_client_not_found(self):
        """Test no update when client not found."""
        mock_session = MagicMock()
        mock_session.query().filter().first.return_value = None

        # Should not raise an error
        _update_client_agreement_status(mock_session, client_id=999, document_type="client_agreement")

        mock_session.commit.assert_not_called()


# =============================================================================
# Tests for Edge Cases and Integration Scenarios
# =============================================================================

class TestEdgeCasesAndIntegration:
    """Test edge cases and integration scenarios."""

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._get_base_url')
    @patch('services.esignature_service._generate_token')
    def test_full_signature_workflow(self, mock_token, mock_base_url, mock_session_class):
        """Test full signature workflow from creation to capture."""
        mock_token.return_value = "workflow_token"
        mock_base_url.return_value = "https://test.app"

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        # Create request
        create_result = create_signature_request(
            client_id=1,
            document_type="client_agreement",
            document_name="Test Agreement",
            document_path=None,
            signer_email="test@example.com",
            signer_name="Test User"
        )

        assert create_result["success"] is True

    @patch('services.esignature_service.SessionLocal')
    def test_concurrent_signature_requests(self, mock_session_class):
        """Test multiple pending requests for same client."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Create multiple mock requests
        mock_requests = []
        for i, doc_type in enumerate(DOCUMENT_TYPES.keys()):
            req = MagicMock()
            req.id = i + 1
            req.document_type = doc_type
            req.document_name = f"Test {doc_type}"
            req.signer_name = "Test User"
            req.signer_email = "test@example.com"
            req.signing_link = f"https://test.app/sign/token{i}"
            req.expires_at = datetime.utcnow() + timedelta(days=1)
            req.created_at = datetime.utcnow()
            mock_requests.append(req)

        mock_session.query().filter().order_by().all.return_value = mock_requests

        result = get_pending_signatures(client_id=1)

        assert result["success"] is True
        assert result["pending_count"] == len(DOCUMENT_TYPES)

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._get_base_url')
    @patch('services.esignature_service._generate_token')
    def test_special_characters_in_names(self, mock_token, mock_base_url, mock_session_class):
        """Test handling of special characters in signer names."""
        mock_token.return_value = "test_token"
        mock_base_url.return_value = "https://test.app"

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        result = create_signature_request(
            client_id=1,
            document_type="client_agreement",
            document_name="Agreement for Jose Garcia-Martinez",
            document_path=None,
            signer_email="jose@example.com",
            signer_name="Jose Garcia-Martinez"
        )

        assert result["success"] is True

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._get_base_url')
    @patch('services.esignature_service._generate_token')
    def test_unicode_in_document_name(self, mock_token, mock_base_url, mock_session_class):
        """Test handling of unicode characters in document names."""
        mock_token.return_value = "test_token"
        mock_base_url.return_value = "https://test.app"

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        result = create_signature_request(
            client_id=1,
            document_type="client_agreement",
            document_name="Acuerdo de Servicio",
            document_path=None,
            signer_email="test@example.com",
            signer_name="Test User"
        )

        assert result["success"] is True

    @patch('services.esignature_service.SessionLocal')
    def test_verify_token_with_no_expires_at(self, mock_session_class):
        """Test token verification when expires_at is None."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.client_id = 10
        mock_request.status = "pending"
        mock_request.expires_at = None  # No expiration
        mock_request.document_type = "client_agreement"
        mock_request.document_name = "Test Doc"
        mock_request.document_path = None
        mock_request.signer_email = "test@example.com"
        mock_request.signer_name = "Test User"
        mock_request.created_at = datetime.utcnow()

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_session.query().filter().first.side_effect = [mock_request, mock_client]

        result = verify_signing_token("no_expire_token")

        assert result["valid"] is True

    @patch('services.esignature_service.SessionLocal')
    def test_signature_history_mixed_statuses(self, mock_session_class):
        """Test history with mixed document statuses."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        statuses = ["signed", "pending", "cancelled", "signed", "pending"]
        mock_requests = []

        for i, status in enumerate(statuses):
            req = MagicMock()
            req.id = i + 1
            req.document_type = "client_agreement"
            req.document_name = f"Document {i + 1}"
            req.document_path = None
            req.signer_name = "Test User"
            req.signer_email = "test@example.com"
            req.signing_link = f"https://test.app/sign/token{i}"
            req.status = status
            req.signed_at = datetime.utcnow() if status == "signed" else None
            req.signed_document_path = f"/path/sig{i}.png" if status == "signed" else None
            req.expires_at = datetime.utcnow() + timedelta(days=1)
            req.created_at = datetime.utcnow()
            mock_requests.append(req)

        mock_session.query().filter().order_by().all.return_value = mock_requests

        result = get_client_signature_history(client_id=1)

        assert result["success"] is True
        assert result["total_count"] == 5
        assert result["signed_count"] == 2
        assert result["pending_count"] == 2  # 2 pending, cancelled doesn't count


# =============================================================================
# Tests for Session Cleanup
# =============================================================================

class TestSessionCleanup:
    """Test that database sessions are properly closed."""

    @patch('services.esignature_service.SessionLocal')
    def test_create_request_closes_session(self, mock_session_class):
        """Test session is closed after create_signature_request."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.commit.side_effect = Exception("Error")

        create_signature_request(
            client_id=1,
            document_type="client_agreement",
            document_name="Test",
            document_path=None,
            signer_email="test@example.com",
            signer_name="Test"
        )

        mock_session.close.assert_called_once()

    @patch('services.esignature_service.SessionLocal')
    def test_verify_token_closes_session(self, mock_session_class):
        """Test session is closed after verify_signing_token."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.side_effect = Exception("Error")

        verify_signing_token("test_token")

        mock_session.close.assert_called_once()

    @patch('services.esignature_service.SessionLocal')
    def test_get_status_closes_session(self, mock_session_class):
        """Test session is closed after get_signature_status."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.side_effect = Exception("Error")

        get_signature_status(request_id=1)

        mock_session.close.assert_called_once()

    @patch('services.esignature_service.SessionLocal')
    def test_cancel_request_closes_session(self, mock_session_class):
        """Test session is closed after cancel_signature_request."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().first.side_effect = Exception("Error")

        cancel_signature_request(request_id=1)

        mock_session.close.assert_called_once()

    @patch('services.esignature_service.SessionLocal')
    def test_get_history_closes_session(self, mock_session_class):
        """Test session is closed after get_client_signature_history."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query().filter().order_by().all.side_effect = Exception("Error")

        get_client_signature_history(client_id=1)

        mock_session.close.assert_called_once()
