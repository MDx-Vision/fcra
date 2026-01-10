"""
Unit Tests for Electronic Signature Service - Full ESIGN Act Compliance.
Tests for session management, consent flow, document signing, audit trail,
CROA compliance, and tamper-evidence verification.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os
import base64
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.esignature_service import (
    # Session Management
    initiate_signing_session,
    get_session_by_uuid,
    complete_signing_session,
    cancel_signing_session,
    regenerate_signing_link,
    # Consent
    submit_esign_consent,
    get_esign_consent_disclosure,
    # Document Review & Signing
    get_document_for_review,
    record_document_review_progress,
    sign_document,
    # Verification
    verify_document_integrity,
    get_session_audit_trail,
    # CROA Compliance
    get_croa_compliance_status,
    cancel_service_during_croa_period,
    waive_cancellation_period,
    # Client History
    get_client_signing_history,
    list_document_types,
    # Helpers
    _generate_uuid,
    _generate_certificate_number,
    _compute_document_hash,
    _add_business_days,
    # Constants
    DOCUMENT_TYPES,
    PROVIDER_NAME,
    SESSION_EXPIRY_DAYS,
    ESIGN_CONSENT_DISCLOSURE,
    INTENT_STATEMENT,
    CERT_PREFIX,
)


# =============================================================================
# Tests for Constants and Configuration
# =============================================================================

class TestConstants:
    """Test service constants and configuration."""

    def test_provider_name(self):
        """Test that provider name is set correctly."""
        assert PROVIDER_NAME == "brightpath_esign"

    def test_session_expiry_days(self):
        """Test session expiry is 7 days."""
        assert SESSION_EXPIRY_DAYS == 7

    def test_document_types_defined(self):
        """Test that document types are defined."""
        assert "client_agreement" in DOCUMENT_TYPES
        assert "limited_poa" in DOCUMENT_TYPES
        assert "rights_disclosure" in DOCUMENT_TYPES
        assert "cancellation_notice" in DOCUMENT_TYPES

    def test_esign_consent_disclosure_exists(self):
        """Test consent disclosure HTML is defined."""
        assert ESIGN_CONSENT_DISCLOSURE is not None
        assert "Hardware and Software" in ESIGN_CONSENT_DISCLOSURE
        assert "Paper Copies" in ESIGN_CONSENT_DISCLOSURE
        assert "Withdraw Consent" in ESIGN_CONSENT_DISCLOSURE

    def test_intent_statement(self):
        """Test intent statement is defined."""
        assert "legally binding" in INTENT_STATEMENT.lower()


# =============================================================================
# Tests for Helper Functions
# =============================================================================

class TestHelperFunctions:
    """Test internal helper functions."""

    def test_generate_uuid(self):
        """Test UUID generation."""
        uuid1 = _generate_uuid()
        uuid2 = _generate_uuid()
        assert uuid1 != uuid2
        assert len(uuid1) > 20  # URL-safe tokens are reasonably long

    def test_generate_certificate_number(self):
        """Test certificate number generation."""
        cert = _generate_certificate_number()
        assert cert.startswith(CERT_PREFIX)
        assert "-" in cert
        # Format: PREFIX-YYYYMMDD-RANDOM
        parts = cert.split("-")
        assert len(parts) == 3

    def test_compute_document_hash(self):
        """Test SHA-256 document hashing."""
        content = "<html><body>Test document</body></html>"
        hash1 = _compute_document_hash(content)
        hash2 = _compute_document_hash(content)

        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters

        # Different content should produce different hash
        hash3 = _compute_document_hash(content + " modified")
        assert hash1 != hash3

    def test_add_business_days_weekday(self):
        """Test adding business days starting on a weekday."""
        # Monday
        start = datetime(2024, 12, 16, 14, 0, 0)
        result = _add_business_days(start, 3)

        # 3 business days from Monday = Thursday
        assert result.weekday() == 3  # Thursday
        assert result.day == 19
        assert result.hour == 23
        assert result.minute == 59

    def test_add_business_days_weekend(self):
        """Test adding business days that span a weekend."""
        # Thursday
        start = datetime(2024, 12, 19, 10, 0, 0)
        result = _add_business_days(start, 3)

        # 3 business days from Thursday = Tuesday (skips Sat/Sun)
        assert result.weekday() == 1  # Tuesday
        assert result.day == 24


# =============================================================================
# Tests for Session Management
# =============================================================================

class TestSessionManagement:
    """Test signing session creation and management."""

    @patch('services.esignature_service.SessionLocal')
    def test_initiate_signing_session_success(self, mock_session_local):
        """Test successful session initiation."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Mock client exists
        mock_client = MagicMock()
        mock_client.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client

        documents = [
            {"document_name": "Agreement", "document_type": "client_agreement", "document_html": "<p>Test</p>"}
        ]

        result = initiate_signing_session(
            client_id=1,
            documents=documents,
            signer_email="test@example.com",
            signer_name="John Doe",
        )

        assert result["success"] is True
        assert "session_uuid" in result
        assert "signing_link" in result
        assert result["documents_count"] == 1

    @patch('services.esignature_service.SessionLocal')
    def test_initiate_signing_session_client_not_found(self, mock_session_local):
        """Test session initiation with non-existent client."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = initiate_signing_session(
            client_id=999,
            documents=[{"document_name": "Test"}],
            signer_email="test@example.com",
            signer_name="John Doe",
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.esignature_service.SessionLocal')
    def test_get_session_by_uuid_success(self, mock_session_local):
        """Test getting session by UUID."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.session_uuid = "test-uuid"
        mock_signing_session.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_signing_session.documents = []
        mock_signing_session.consent_disclosure_html = "<p>Consent</p>"
        mock_signing_session.to_dict.return_value = {"session_uuid": "test-uuid"}

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session

        result = get_session_by_uuid("test-uuid")

        assert result["success"] is True
        assert "session" in result

    @patch('services.esignature_service.SessionLocal')
    def test_get_session_expired(self, mock_session_local):
        """Test getting expired session."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.expires_at = datetime.utcnow() - timedelta(days=1)

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session

        result = get_session_by_uuid("test-uuid")

        assert result["success"] is False
        assert "expired" in result.get("error", "").lower() or result.get("expired") is True


# =============================================================================
# Tests for ESIGN Act Consent
# =============================================================================

class TestEsignConsent:
    """Test ESIGN Act consent flow with 3 acknowledgments."""

    @patch('services.esignature_service.SessionLocal')
    def test_submit_consent_success(self, mock_session_local):
        """Test successful consent submission with all acknowledgments."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_signing_session.client_id = 1

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session

        result = submit_esign_consent(
            session_uuid="test-uuid",
            hardware_software_acknowledged=True,
            paper_copy_right_acknowledged=True,
            consent_withdrawal_acknowledged=True,
            ip_address="127.0.0.1",
        )

        assert result["success"] is True
        assert "consent_timestamp" in result

    @patch('services.esignature_service.SessionLocal')
    def test_submit_consent_missing_acknowledgment(self, mock_session_local):
        """Test consent submission with missing acknowledgment."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.expires_at = datetime.utcnow() + timedelta(days=1)

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session

        # Missing one acknowledgment
        result = submit_esign_consent(
            session_uuid="test-uuid",
            hardware_software_acknowledged=True,
            paper_copy_right_acknowledged=False,  # Missing
            consent_withdrawal_acknowledged=True,
        )

        assert result["success"] is False
        assert "acknowledgments" in result["error"].lower()

    def test_get_esign_consent_disclosure(self):
        """Test getting consent disclosure HTML."""
        disclosure = get_esign_consent_disclosure()
        assert disclosure is not None
        assert "Hardware" in disclosure
        assert "ESIGN Act" in disclosure


# =============================================================================
# Tests for Document Review & Signing
# =============================================================================

class TestDocumentReviewAndSigning:
    """Test document review and signature capture."""

    @patch('services.esignature_service.SessionLocal')
    def test_get_document_for_review_success(self, mock_session_local):
        """Test getting document for review."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.esign_consent_given = True
        mock_signing_session.id = 1
        mock_signing_session.client_id = 1

        mock_document = MagicMock()
        mock_document.document_uuid = "doc-uuid"
        mock_document.document_name = "Agreement"
        mock_document.document_type = "client_agreement"
        mock_document.document_html = "<p>Content</p>"
        mock_document.is_croa_document = False
        mock_document.status = "pending"
        mock_document.document_presented_at = None

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_signing_session,
            mock_document,
        ]

        result = get_document_for_review("session-uuid", "doc-uuid")

        assert result["success"] is True
        assert "document" in result
        assert "intent_statement" in result

    @patch('services.esignature_service.SessionLocal')
    def test_get_document_without_consent(self, mock_session_local):
        """Test that document review requires consent first."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.esign_consent_given = False

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session

        result = get_document_for_review("session-uuid", "doc-uuid")

        assert result["success"] is False
        assert "consent" in result["error"].lower()

    @patch('services.esignature_service.SessionLocal')
    def test_record_review_progress(self, mock_session_local):
        """Test recording scroll and duration progress."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.id = 1
        mock_signing_session.client_id = 1

        mock_document = MagicMock()
        mock_document.scroll_percentage = 0
        mock_document.review_duration_seconds = 0
        mock_document.scrolled_to_bottom = False
        mock_document.review_started_at = None

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_signing_session,
            mock_document,
        ]

        result = record_document_review_progress(
            session_uuid="session-uuid",
            document_uuid="doc-uuid",
            scroll_percentage=100,
            review_duration_seconds=60,
        )

        assert result["success"] is True
        assert result["scrolled_to_bottom"] is True

    @patch('services.esignature_service.SessionLocal')
    @patch('services.esignature_service._ensure_folders')
    def test_sign_document_success(self, mock_folders, mock_session_local):
        """Test successful document signing."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.esign_consent_given = True
        mock_signing_session.id = 1
        mock_signing_session.client_id = 1
        mock_signing_session.signer_name = "John Doe"
        mock_signing_session.signer_email = "john@example.com"

        mock_document = MagicMock()
        mock_document.document_uuid = "doc-uuid"
        mock_document.document_html = "<p>Content</p>"
        mock_document.status = "pending"
        mock_document.is_croa_document = False
        mock_document.id = 1
        mock_document.client_id = 1

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_signing_session,
            mock_document,
        ]

        result = sign_document(
            session_uuid="session-uuid",
            document_uuid="doc-uuid",
            signature_type="typed",
            signature_value="John Doe",
            intent_confirmed=True,
            typed_name="John Doe",
            ip_address="127.0.0.1",
        )

        assert result["success"] is True
        assert "certificate_number" in result
        assert "document_hash" in result

    @patch('services.esignature_service.SessionLocal')
    def test_sign_document_without_intent(self, mock_session_local):
        """Test signing without intent confirmation fails."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.esign_consent_given = True

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session

        result = sign_document(
            session_uuid="session-uuid",
            document_uuid="doc-uuid",
            signature_type="typed",
            signature_value="John Doe",
            intent_confirmed=False,  # Not confirmed
            typed_name="John Doe",
        )

        assert result["success"] is False
        assert "intent" in result["error"].lower()

    @patch('services.esignature_service.SessionLocal')
    def test_sign_document_name_mismatch(self, mock_session_local):
        """Test signing with wrong typed name fails."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.esign_consent_given = True
        mock_signing_session.signer_name = "John Doe"
        mock_signing_session.id = 1

        mock_document = MagicMock()
        mock_document.status = "pending"
        mock_document.is_croa_document = False

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_signing_session,
            mock_document,
        ]

        result = sign_document(
            session_uuid="session-uuid",
            document_uuid="doc-uuid",
            signature_type="typed",
            signature_value="Jane Smith",  # Wrong name
            intent_confirmed=True,
            typed_name="Jane Smith",  # Doesn't match signer_name
        )

        assert result["success"] is False
        assert "match" in result["error"].lower()


# =============================================================================
# Tests for Document Integrity Verification
# =============================================================================

class TestDocumentVerification:
    """Test document integrity verification."""

    @patch('services.esignature_service.SessionLocal')
    def test_verify_document_integrity_valid(self, mock_session_local):
        """Test verifying document that hasn't been tampered with."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        content = "<p>Original content</p>"
        original_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        mock_document = MagicMock()
        mock_document.document_uuid = "doc-uuid"
        mock_document.status = "signed"
        mock_document.document_html = content
        mock_document.document_hash_sha256 = original_hash
        mock_document.certificate_number = "BAG-20241224-ABCD1234"
        mock_document.signature_timestamp = datetime.utcnow()
        mock_document.signer_name = "John Doe"
        mock_document.verify_integrity.return_value = True

        mock_session.query.return_value.filter.return_value.first.return_value = mock_document

        result = verify_document_integrity("doc-uuid")

        assert result["success"] is True
        assert result["integrity_valid"] is True

    @patch('services.esignature_service.SessionLocal')
    def test_verify_unsigned_document(self, mock_session_local):
        """Test verifying unsigned document fails."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_document = MagicMock()
        mock_document.status = "pending"  # Not signed

        mock_session.query.return_value.filter.return_value.first.return_value = mock_document

        result = verify_document_integrity("doc-uuid")

        assert result["success"] is False
        assert "not been signed" in result["error"]


# =============================================================================
# Tests for Audit Trail
# =============================================================================

class TestAuditTrail:
    """Test audit trail functionality."""

    @patch('services.esignature_service.SessionLocal')
    def test_get_session_audit_trail(self, mock_session_local):
        """Test getting complete audit trail for session."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.id = 1

        mock_log1 = MagicMock()
        mock_log1.to_dict.return_value = {"action": "session_initiated"}

        mock_log2 = MagicMock()
        mock_log2.to_dict.return_value = {"action": "esign_consent_given"}

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_log1, mock_log2
        ]

        result = get_session_audit_trail("session-uuid")

        assert result["success"] is True
        assert len(result["audit_trail"]) == 2


# =============================================================================
# Tests for CROA Compliance
# =============================================================================

class TestCROACompliance:
    """Test CROA compliance features."""

    @patch('services.esignature_service.SessionLocal')
    def test_get_croa_compliance_status_no_tracker(self, mock_session_local):
        """Test getting CROA status when no tracker exists."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = get_croa_compliance_status(client_id=1)

        assert result["success"] is True
        assert result["has_tracker"] is False
        assert result["work_can_begin"] is False

    @patch('services.esignature_service.SessionLocal')
    def test_get_croa_compliance_status_with_tracker(self, mock_session_local):
        """Test getting CROA status with existing tracker."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_tracker = MagicMock()
        mock_tracker.rights_disclosure_signed = True
        mock_tracker.rights_disclosure_signed_at = datetime.utcnow()
        mock_tracker.contract_package_signed = True
        mock_tracker.contract_package_signed_at = datetime.utcnow()
        mock_tracker.cancellation_period_start = datetime.utcnow()
        mock_tracker.cancellation_period_end = datetime.utcnow() + timedelta(days=3)
        mock_tracker.cancellation_period_complete = False
        mock_tracker.client_cancelled = False
        mock_tracker.cancellation_waived = False
        mock_tracker.work_can_begin = False

        mock_session.query.return_value.filter.return_value.first.return_value = mock_tracker

        result = get_croa_compliance_status(client_id=1)

        assert result["success"] is True
        assert result["has_tracker"] is True
        assert result["rights_disclosure_signed"] is True
        assert result["contract_signed"] is True

    @patch('services.esignature_service.SessionLocal')
    def test_cancel_service_during_croa_period(self, mock_session_local):
        """Test cancelling service during 3-day period."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_tracker = MagicMock()
        mock_tracker.cancellation_period_end = datetime.utcnow() + timedelta(days=2)
        mock_tracker.client_cancelled = False

        mock_session.query.return_value.filter.return_value.first.return_value = mock_tracker

        result = cancel_service_during_croa_period(
            client_id=1,
            reason="Changed my mind",
        )

        assert result["success"] is True
        assert "cancelled_at" in result

    @patch('services.esignature_service.SessionLocal')
    def test_cancel_after_period_ends(self, mock_session_local):
        """Test that cancellation fails after period ends."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_tracker = MagicMock()
        mock_tracker.cancellation_period_end = datetime.utcnow() - timedelta(days=1)  # Ended

        mock_session.query.return_value.filter.return_value.first.return_value = mock_tracker

        result = cancel_service_during_croa_period(client_id=1)

        assert result["success"] is False
        assert "ended" in result["error"].lower()

    @patch('services.esignature_service.SessionLocal')
    def test_waive_cancellation_period(self, mock_session_local):
        """Test waiving cancellation period."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_tracker = MagicMock()
        mock_tracker.client_cancelled = False

        mock_session.query.return_value.filter.return_value.first.return_value = mock_tracker

        result = waive_cancellation_period(
            client_id=1,
            waiver_signature="John Doe",
        )

        assert result["success"] is True
        assert result["work_can_begin"] is True


# =============================================================================
# Tests for Client History
# =============================================================================

class TestClientHistory:
    """Test client signing history."""

    @patch('services.esignature_service.SessionLocal')
    def test_get_client_signing_history(self, mock_session_local):
        """Test getting client's signing history."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_doc = MagicMock()
        mock_doc.document_uuid = "doc-uuid"
        mock_doc.document_name = "Agreement"
        mock_doc.status = "signed"
        mock_doc.certificate_number = "BAG-20241224-ABCD"
        mock_doc.signature_timestamp = datetime.utcnow()

        mock_signing_session = MagicMock()
        mock_signing_session.session_uuid = "session-uuid"
        mock_signing_session.status = "completed"
        mock_signing_session.initiated_at = datetime.utcnow()
        mock_signing_session.completed_at = datetime.utcnow()
        mock_signing_session.documents = [mock_doc]

        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_signing_session
        ]

        result = get_client_signing_history(client_id=1)

        assert result["success"] is True
        assert result["total_sessions"] == 1
        assert len(result["sessions"]) == 1

    def test_list_document_types(self):
        """Test listing supported document types."""
        types = list_document_types()

        assert isinstance(types, dict)
        assert "client_agreement" in types
        assert "rights_disclosure" in types


# =============================================================================
# Tests for Session Cancellation and Link Regeneration
# =============================================================================

class TestSessionManagementAdvanced:
    """Test advanced session management features."""

    @patch('services.esignature_service.SessionLocal')
    def test_cancel_signing_session(self, mock_session_local):
        """Test cancelling a pending session."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.status = "pending"
        mock_signing_session.client_id = 1
        mock_signing_session.id = 1

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session

        result = cancel_signing_session("session-uuid", reason="No longer needed")

        assert result["success"] is True

    @patch('services.esignature_service.SessionLocal')
    def test_cannot_cancel_completed_session(self, mock_session_local):
        """Test that completed sessions cannot be cancelled."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.status = "completed"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session

        result = cancel_signing_session("session-uuid")

        assert result["success"] is False
        assert "completed" in result["error"].lower()

    @patch('services.esignature_service.SessionLocal')
    def test_regenerate_signing_link(self, mock_session_local):
        """Test regenerating expired signing link."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.status = "pending"
        mock_signing_session.client_id = 1
        mock_signing_session.id = 1

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session

        result = regenerate_signing_link("old-session-uuid")

        assert result["success"] is True
        assert "session_uuid" in result
        assert "signing_link" in result
        assert "expires_at" in result


# =============================================================================
# Tests for Complete Session Flow
# =============================================================================

class TestCompleteSessionFlow:
    """Test completing a signing session."""

    @patch('services.esignature_service.SessionLocal')
    def test_complete_session_all_signed(self, mock_session_local):
        """Test completing session when all documents are signed."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.id = 1
        mock_signing_session.client_id = 1
        mock_signing_session.initiated_at = datetime.utcnow()
        mock_signing_session.documents = [MagicMock()]
        mock_signing_session.return_url = "/portal/dashboard"

        # No unsigned documents
        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = complete_signing_session("session-uuid")

        assert result["success"] is True
        assert "completed_at" in result
        assert result["return_url"] == "/portal/dashboard"

    @patch('services.esignature_service.SessionLocal')
    def test_complete_session_with_unsigned_docs(self, mock_session_local):
        """Test that session cannot complete with unsigned documents."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_signing_session = MagicMock()
        mock_signing_session.id = 1

        mock_unsigned_doc = MagicMock()
        mock_unsigned_doc.document_name = "Agreement"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_signing_session
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_unsigned_doc]

        result = complete_signing_session("session-uuid")

        assert result["success"] is False
        assert "unsigned_documents" in result
