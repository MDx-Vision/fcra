"""
Unit Tests for CROA Signing Service.
Tests for CROA document signing workflow, progress tracking, cancellation period management,
and compliance with Credit Repair Organizations Act requirements.
Covers all main functions with mocked database interactions.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.croa_signing_service import (
    CROASigningService,
    get_croa_signing_service,
    CROA_DOCUMENTS,
    DOCUMENT_PROGRESS_FIELDS,
    SIGNATURE_FOLDER,
)


# =============================================================================
# Tests for Constants and Configuration
# =============================================================================

class TestConstants:
    """Test service constants and configuration."""

    def test_croa_documents_count(self):
        """Test that all 7 CROA documents are defined."""
        assert len(CROA_DOCUMENTS) == 7

    def test_croa_documents_order(self):
        """Test documents are in correct signing order."""
        for i, doc in enumerate(CROA_DOCUMENTS):
            assert doc['order'] == i + 1

    def test_rights_disclosure_first(self):
        """Test Rights Disclosure is first and must sign before contract."""
        first_doc = CROA_DOCUMENTS[0]
        assert first_doc['code'] == 'CROA_01_RIGHTS_DISCLOSURE'
        assert first_doc['must_sign_before_contract'] is True

    def test_only_one_must_sign_before_contract(self):
        """Test only Rights Disclosure requires signing before contract."""
        must_sign_before = [d for d in CROA_DOCUMENTS if d['must_sign_before_contract']]
        assert len(must_sign_before) == 1
        assert must_sign_before[0]['code'] == 'CROA_01_RIGHTS_DISCLOSURE'

    def test_hipaa_is_optional(self):
        """Test HIPAA is the only optional document."""
        optional_docs = [d for d in CROA_DOCUMENTS if not d['is_required']]
        assert len(optional_docs) == 1
        assert optional_docs[0]['code'] == 'CROA_06_HIPAA'

    def test_document_codes_unique(self):
        """Test all document codes are unique."""
        codes = [d['code'] for d in CROA_DOCUMENTS]
        assert len(codes) == len(set(codes))

    def test_progress_fields_match_documents(self):
        """Test all documents have corresponding progress fields."""
        for doc in CROA_DOCUMENTS:
            assert doc['code'] in DOCUMENT_PROGRESS_FIELDS

    def test_signature_folder_path(self):
        """Test signature folder path is set."""
        assert SIGNATURE_FOLDER == "static/signatures"


# =============================================================================
# Tests for get_or_create_progress()
# =============================================================================

class TestGetOrCreateProgress:
    """Test progress creation and retrieval."""

    def test_create_new_progress(self):
        """Test creating new progress for client."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_db.query().filter().first.side_effect = [mock_client, None]  # Client exists, no progress

        service = CROASigningService(mock_db)
        result = service.get_or_create_progress(client_id=1)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result is not None

    def test_get_existing_progress(self):
        """Test retrieving existing progress."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.get_or_create_progress(client_id=1)

        mock_db.add.assert_not_called()
        assert result == mock_progress

    def test_client_not_found(self):
        """Test returns None when client not found."""
        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None

        service = CROASigningService(mock_db)
        result = service.get_or_create_progress(client_id=999)

        assert result is None


# =============================================================================
# Tests for get_progress_summary()
# =============================================================================

class TestGetProgressSummary:
    """Test progress summary retrieval."""

    def test_summary_empty_progress(self):
        """Test summary for new client with no signatures."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.current_document = 'CROA_01_RIGHTS_DISCLOSURE'
        mock_progress.is_complete = False
        mock_progress.completed_at = None
        mock_progress.rights_disclosure_signed_at = None
        mock_progress.lpoa_signed_at = None
        mock_progress.service_agreement_signed_at = None
        mock_progress.cancellation_notice_signed_at = None
        mock_progress.service_completion_signed_at = None
        mock_progress.hipaa_signed_at = None
        mock_progress.welcome_packet_signed_at = None
        mock_progress.cancellation_period_starts_at = None
        mock_progress.cancellation_period_ends_at = None
        mock_progress.cancellation_waived = False
        mock_progress.cancelled_at = None

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress, None, None, None, None, None, None, None]

        service = CROASigningService(mock_db)
        result = service.get_progress_summary(client_id=1)

        assert result['success'] is True
        assert result['documents_completed'] == 0
        assert result['total_documents'] == 7
        assert result['is_complete'] is False
        assert result['percentage'] == 0

    def test_summary_partial_progress(self):
        """Test summary with some documents signed."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.current_document = 'CROA_03_SERVICE_AGREEMENT'
        mock_progress.is_complete = False
        mock_progress.completed_at = None
        mock_progress.rights_disclosure_signed_at = datetime.utcnow() - timedelta(hours=2)
        mock_progress.lpoa_signed_at = datetime.utcnow() - timedelta(hours=1)
        mock_progress.service_agreement_signed_at = None
        mock_progress.cancellation_notice_signed_at = None
        mock_progress.service_completion_signed_at = None
        mock_progress.hipaa_signed_at = None
        mock_progress.welcome_packet_signed_at = None
        mock_progress.cancellation_period_starts_at = None
        mock_progress.cancellation_period_ends_at = None
        mock_progress.cancellation_waived = False
        mock_progress.cancelled_at = None

        mock_template = MagicMock()
        mock_db.query().filter().first.side_effect = [
            mock_client, mock_progress,
            mock_template, mock_template, mock_template, mock_template,
            mock_template, mock_template, mock_template
        ]

        service = CROASigningService(mock_db)
        result = service.get_progress_summary(client_id=1)

        assert result['success'] is True
        assert result['documents_completed'] == 2
        assert result['percentage'] == 28  # 2/7 = ~28%

    def test_summary_client_not_found(self):
        """Test summary when client not found."""
        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None

        service = CROASigningService(mock_db)
        result = service.get_progress_summary(client_id=999)

        assert result.get('error') == 'Client not found'


# =============================================================================
# Tests for get_document()
# =============================================================================

class TestGetDocument:
    """Test document retrieval."""

    def test_get_document_success(self):
        """Test successful document retrieval."""
        mock_db = MagicMock()
        mock_template = MagicMock()
        mock_template.code = 'CROA_01_RIGHTS_DISCLOSURE'
        mock_template.name = 'Consumer Credit File Rights Disclosure'
        mock_template.description = 'Required disclosure'
        mock_template.content_html = '<p>Document content</p>'
        mock_template.version = '1.0'
        mock_template.must_sign_before_contract = True

        mock_db.query().filter().first.return_value = mock_template

        service = CROASigningService(mock_db)
        result = service.get_document('CROA_01_RIGHTS_DISCLOSURE')

        assert result['success'] is True
        assert result['document']['code'] == 'CROA_01_RIGHTS_DISCLOSURE'
        assert result['document']['order'] == 1
        assert result['document']['is_required'] is True

    def test_get_document_not_found(self):
        """Test document retrieval when not found."""
        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None

        service = CROASigningService(mock_db)
        result = service.get_document('INVALID_CODE')

        assert result['success'] is False
        assert 'not found' in result['error']

    def test_get_all_croa_documents(self):
        """Test retrieving all CROA document codes."""
        mock_db = MagicMock()
        mock_template = MagicMock()
        mock_template.code = 'test'
        mock_template.name = 'Test'
        mock_template.description = 'Test'
        mock_template.content_html = '<p>Test</p>'
        mock_template.version = '1.0'
        mock_template.must_sign_before_contract = False

        mock_db.query().filter().first.return_value = mock_template

        service = CROASigningService(mock_db)

        for doc in CROA_DOCUMENTS:
            result = service.get_document(doc['code'])
            assert result['success'] is True


# =============================================================================
# Tests for get_current_document()
# =============================================================================

class TestGetCurrentDocument:
    """Test current document retrieval."""

    def test_get_first_document_when_none_signed(self):
        """Test returns first document when none are signed."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.is_complete = False
        mock_progress.rights_disclosure_signed_at = None
        mock_progress.lpoa_signed_at = None
        mock_progress.service_agreement_signed_at = None
        mock_progress.cancellation_notice_signed_at = None
        mock_progress.service_completion_signed_at = None
        mock_progress.hipaa_signed_at = None
        mock_progress.welcome_packet_signed_at = None

        mock_template = MagicMock()
        mock_template.code = 'CROA_01_RIGHTS_DISCLOSURE'
        mock_template.name = 'Rights Disclosure'
        mock_template.description = 'Required disclosure'
        mock_template.content_html = '<p>Content</p>'
        mock_template.version = '1.0'
        mock_template.must_sign_before_contract = True

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress, mock_template]

        service = CROASigningService(mock_db)
        result = service.get_current_document(client_id=1)

        assert result['success'] is True
        assert result['document']['code'] == 'CROA_01_RIGHTS_DISCLOSURE'

    def test_returns_complete_when_all_signed(self):
        """Test returns complete status when all required documents signed."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.is_complete = True

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.get_current_document(client_id=1)

        assert result['success'] is True
        assert result['is_complete'] is True

    def test_client_not_found(self):
        """Test returns error when client not found."""
        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None

        service = CROASigningService(mock_db)
        result = service.get_current_document(client_id=999)

        assert result['success'] is False
        assert 'not found' in result['error']


# =============================================================================
# Tests for sign_document()
# =============================================================================

class TestSignDocument:
    """Test document signing functionality."""

    def test_sign_first_document_success(self):
        """Test signing Rights Disclosure first."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = None
        mock_progress.is_complete = False

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.code = 'CROA_01_RIGHTS_DISCLOSURE'
        mock_template.name = 'Rights Disclosure'

        mock_db.query().filter().first.side_effect = [
            mock_client, mock_progress, mock_template,
            mock_client, mock_progress  # For get_current_document
        ]

        service = CROASigningService(mock_db)

        with patch.object(service, 'get_current_document', return_value={'success': True, 'document': None}):
            result = service.sign_document(
                client_id=1,
                document_code='CROA_01_RIGHTS_DISCLOSURE',
                signature_data='typed_name',
                signature_type='typed',
                ip_address='127.0.0.1',
                user_agent='Test Browser'
            )

        assert result['success'] is True
        assert result['document_signed'] == 'CROA_01_RIGHTS_DISCLOSURE'
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_cannot_sign_without_rights_disclosure(self):
        """Test cannot sign other documents before Rights Disclosure."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = None  # Not signed yet

        mock_template = MagicMock()
        mock_template.id = 2

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress, mock_template]

        service = CROASigningService(mock_db)
        result = service.sign_document(
            client_id=1,
            document_code='CROA_02_LPOA',
            signature_data='typed_name',
            signature_type='typed'
        )

        assert result['success'] is False
        assert 'Rights Disclosure must be signed' in result['error']

    def test_cannot_sign_same_document_twice(self):
        """Test cannot sign the same document twice."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow()  # Already signed

        mock_template = MagicMock()
        mock_template.id = 1

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress, mock_template]

        service = CROASigningService(mock_db)
        result = service.sign_document(
            client_id=1,
            document_code='CROA_01_RIGHTS_DISCLOSURE',
            signature_data='typed_name',
            signature_type='typed'
        )

        assert result['success'] is False
        assert 'already been signed' in result['error']

    def test_sign_document_invalid_code(self):
        """Test signing with invalid document code."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow()

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress, None]

        service = CROASigningService(mock_db)
        result = service.sign_document(
            client_id=1,
            document_code='INVALID_CODE',
            signature_data='typed_name',
            signature_type='typed'
        )

        assert result['success'] is False
        assert 'not found' in result['error']

    def test_sign_service_agreement_starts_cancellation(self):
        """Test signing service agreement starts cancellation period."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow()
        mock_progress.lpoa_signed_at = datetime.utcnow()
        mock_progress.service_agreement_signed_at = None
        mock_progress.is_complete = False
        mock_progress.cancellation_period_starts_at = None

        mock_template = MagicMock()
        mock_template.id = 3
        mock_template.code = 'CROA_03_SERVICE_AGREEMENT'
        mock_template.name = 'Service Agreement'

        mock_db.query().filter().first.side_effect = [
            mock_client, mock_progress, mock_template,
            mock_client
        ]

        service = CROASigningService(mock_db)

        with patch.object(service, 'get_current_document', return_value={'success': True, 'document': None}):
            result = service.sign_document(
                client_id=1,
                document_code='CROA_03_SERVICE_AGREEMENT',
                signature_data='typed_name',
                signature_type='typed'
            )

        assert result['success'] is True
        assert mock_progress.cancellation_period_starts_at is not None
        assert result['cancellation_status'] is not None

    def test_sign_client_not_found(self):
        """Test signing when client not found."""
        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None

        service = CROASigningService(mock_db)
        result = service.sign_document(
            client_id=999,
            document_code='CROA_01_RIGHTS_DISCLOSURE',
            signature_data='typed_name',
            signature_type='typed'
        )

        assert result['success'] is False
        assert 'Client not found' in result['error']


# =============================================================================
# Tests for skip_optional_document()
# =============================================================================

class TestSkipOptionalDocument:
    """Test optional document skipping."""

    def test_skip_hipaa_success(self):
        """Test successfully skipping HIPAA document."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress, mock_client, mock_progress]

        service = CROASigningService(mock_db)

        with patch.object(service, 'get_current_document', return_value={'success': True, 'document': None}):
            result = service.skip_optional_document(
                client_id=1,
                document_code='CROA_06_HIPAA'
            )

        assert result['success'] is True
        assert result['skipped'] == 'CROA_06_HIPAA'

    def test_cannot_skip_required_document(self):
        """Test cannot skip required documents."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.skip_optional_document(
            client_id=1,
            document_code='CROA_01_RIGHTS_DISCLOSURE'
        )

        assert result['success'] is False
        assert 'Cannot skip required document' in result['error']

    def test_skip_invalid_document(self):
        """Test skipping invalid document code."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.skip_optional_document(
            client_id=1,
            document_code='INVALID_CODE'
        )

        assert result['success'] is False
        assert 'Invalid document code' in result['error']


# =============================================================================
# Tests for Cancellation Period
# =============================================================================

class TestCancellationPeriod:
    """Test cancellation period functionality."""

    def test_get_cancellation_status_not_started(self):
        """Test cancellation status before service agreement signed."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.cancellation_period_starts_at = None
        mock_progress.cancelled_at = None
        mock_progress.cancellation_waived = False

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.get_cancellation_status(client_id=1)

        assert result['success'] is True
        assert result['in_cancellation_period'] is False
        assert result['can_cancel'] is False

    def test_get_cancellation_status_active(self):
        """Test cancellation status during 3-day period."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.cancellation_period_starts_at = datetime.utcnow()
        mock_progress.cancellation_period_ends_at = datetime.utcnow() + timedelta(days=3)
        mock_progress.cancelled_at = None
        mock_progress.cancellation_waived = False

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.get_cancellation_status(client_id=1)

        assert result['success'] is True
        assert result['in_cancellation_period'] is True
        assert result['can_cancel'] is True
        assert result['days_remaining'] >= 1

    def test_get_cancellation_status_expired(self):
        """Test cancellation status after period expired."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.cancellation_period_starts_at = datetime.utcnow() - timedelta(days=5)
        mock_progress.cancellation_period_ends_at = datetime.utcnow() - timedelta(days=2)
        mock_progress.cancelled_at = None
        mock_progress.cancellation_waived = False

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.get_cancellation_status(client_id=1)

        assert result['success'] is True
        assert result['in_cancellation_period'] is False
        assert result['can_cancel'] is False
        assert result['cancellation_expired'] is True

    def test_cancel_service_success(self):
        """Test successful service cancellation."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.cancellation_period_starts_at = datetime.utcnow()
        mock_progress.cancellation_period_ends_at = datetime.utcnow() + timedelta(days=3)
        mock_progress.cancelled_at = None
        mock_progress.cancellation_waived = False

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress, mock_client]

        service = CROASigningService(mock_db)
        result = service.cancel_service(client_id=1, reason='Changed my mind')

        assert result['success'] is True
        assert 'cancelled_at' in result
        assert mock_client.dispute_status == 'cancelled'
        mock_db.commit.assert_called()

    def test_cancel_service_period_expired(self):
        """Test cannot cancel after period expired."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.cancellation_period_starts_at = datetime.utcnow() - timedelta(days=5)
        mock_progress.cancellation_period_ends_at = datetime.utcnow() - timedelta(days=2)
        mock_progress.cancelled_at = None
        mock_progress.cancellation_waived = False

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.cancel_service(client_id=1)

        assert result['success'] is False
        assert 'expired' in result['error'].lower() or 'cannot' in result['error'].lower()

    def test_waive_cancellation_period(self):
        """Test waiving cancellation period."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.cancellation_period_starts_at = datetime.utcnow()
        mock_progress.cancelled_at = None
        mock_progress.cancellation_waived = False

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.waive_cancellation_period(client_id=1)

        assert result['success'] is True
        assert mock_progress.cancellation_waived is True
        mock_db.commit.assert_called()

    def test_waive_cancellation_not_started(self):
        """Test cannot waive if service agreement not signed."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.cancellation_period_starts_at = None

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.waive_cancellation_period(client_id=1)

        assert result['success'] is False
        assert 'not yet signed' in result['error']


# =============================================================================
# Tests for can_begin_services()
# =============================================================================

class TestCanBeginServices:
    """Test service start eligibility."""

    def test_can_begin_all_requirements_met(self):
        """Test can begin when all requirements met."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow() - timedelta(days=5)
        mock_progress.lpoa_signed_at = datetime.utcnow() - timedelta(days=5)
        mock_progress.service_agreement_signed_at = datetime.utcnow() - timedelta(days=5)
        mock_progress.cancellation_notice_signed_at = datetime.utcnow() - timedelta(days=5)
        mock_progress.service_completion_signed_at = datetime.utcnow() - timedelta(days=5)
        mock_progress.hipaa_signed_at = None  # Optional
        mock_progress.welcome_packet_signed_at = datetime.utcnow() - timedelta(days=5)
        mock_progress.cancellation_period_starts_at = datetime.utcnow() - timedelta(days=5)
        mock_progress.cancellation_period_ends_at = datetime.utcnow() - timedelta(days=2)  # Expired
        mock_progress.cancellation_waived = False
        mock_progress.cancelled_at = None

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.can_begin_services(client_id=1)

        assert result['success'] is True
        assert result['can_begin'] is True
        assert result['reason'] == 'all_requirements_met'

    def test_cannot_begin_missing_documents(self):
        """Test cannot begin with missing required documents."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow()
        mock_progress.lpoa_signed_at = None  # Missing
        mock_progress.service_agreement_signed_at = None  # Missing
        mock_progress.cancellation_notice_signed_at = None
        mock_progress.service_completion_signed_at = None
        mock_progress.hipaa_signed_at = None
        mock_progress.welcome_packet_signed_at = None

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.can_begin_services(client_id=1)

        assert result['success'] is True
        assert result['can_begin'] is False
        assert result['reason'] == 'documents_incomplete'
        assert len(result['missing_documents']) > 0

    def test_cannot_begin_in_cancellation_period(self):
        """Test cannot begin during cancellation period."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow()
        mock_progress.lpoa_signed_at = datetime.utcnow()
        mock_progress.service_agreement_signed_at = datetime.utcnow()
        mock_progress.cancellation_notice_signed_at = datetime.utcnow()
        mock_progress.service_completion_signed_at = datetime.utcnow()
        mock_progress.hipaa_signed_at = None
        mock_progress.welcome_packet_signed_at = datetime.utcnow()
        mock_progress.cancellation_period_starts_at = datetime.utcnow()
        mock_progress.cancellation_period_ends_at = datetime.utcnow() + timedelta(days=3)
        mock_progress.cancellation_waived = False
        mock_progress.cancelled_at = None

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.can_begin_services(client_id=1)

        assert result['success'] is True
        assert result['can_begin'] is False
        assert result['reason'] == 'cancellation_period_active'

    def test_can_begin_cancellation_waived(self):
        """Test can begin if cancellation period waived."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow()
        mock_progress.lpoa_signed_at = datetime.utcnow()
        mock_progress.service_agreement_signed_at = datetime.utcnow()
        mock_progress.cancellation_notice_signed_at = datetime.utcnow()
        mock_progress.service_completion_signed_at = datetime.utcnow()
        mock_progress.hipaa_signed_at = None
        mock_progress.welcome_packet_signed_at = datetime.utcnow()
        mock_progress.cancellation_period_starts_at = datetime.utcnow()
        mock_progress.cancellation_period_ends_at = datetime.utcnow() + timedelta(days=3)
        mock_progress.cancellation_waived = True  # Waived
        mock_progress.cancelled_at = None

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.can_begin_services(client_id=1)

        assert result['success'] is True
        assert result['can_begin'] is True

    def test_cannot_begin_if_cancelled(self):
        """Test cannot begin if service was cancelled."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow()
        mock_progress.lpoa_signed_at = datetime.utcnow()
        mock_progress.service_agreement_signed_at = datetime.utcnow()
        mock_progress.cancellation_notice_signed_at = datetime.utcnow()
        mock_progress.service_completion_signed_at = datetime.utcnow()
        mock_progress.hipaa_signed_at = None
        mock_progress.welcome_packet_signed_at = datetime.utcnow()
        mock_progress.cancellation_period_starts_at = datetime.utcnow() - timedelta(days=2)
        mock_progress.cancellation_period_ends_at = datetime.utcnow() - timedelta(days=1)
        mock_progress.cancellation_waived = False
        mock_progress.cancelled_at = datetime.utcnow()  # Was cancelled

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress]

        service = CROASigningService(mock_db)
        result = service.can_begin_services(client_id=1)

        assert result['success'] is True
        assert result['can_begin'] is False
        assert result['reason'] == 'cancelled'


# =============================================================================
# Tests for Cancellation Period Calculation
# =============================================================================

class TestCancellationCalculation:
    """Test 3 business day calculation."""

    def test_calculate_cancellation_end_weekday_start(self):
        """Test cancellation period starting on a weekday (Monday)."""
        service = CROASigningService(MagicMock())

        # Monday start
        monday = datetime(2025, 1, 6, 10, 0, 0)  # A Monday
        end = service._calculate_cancellation_end(monday)

        # Should be Thursday at 5 PM
        assert end.weekday() == 3  # Thursday
        assert end.hour == 17
        assert end.minute == 0

    def test_calculate_cancellation_end_friday_start(self):
        """Test cancellation period starting on Friday skips weekend."""
        service = CROASigningService(MagicMock())

        # Friday start
        friday = datetime(2025, 1, 3, 10, 0, 0)  # A Friday
        end = service._calculate_cancellation_end(friday)

        # Should be Wednesday at 5 PM (skip Sat, Sun)
        assert end.weekday() == 2  # Wednesday
        assert end.hour == 17

    def test_calculate_cancellation_end_saturday_start(self):
        """Test cancellation period starting on Saturday."""
        service = CROASigningService(MagicMock())

        # Saturday start
        saturday = datetime(2025, 1, 4, 10, 0, 0)  # A Saturday
        end = service._calculate_cancellation_end(saturday)

        # Sun=skip, Mon=1, Tue=2, Wed=3 → Wednesday (weekday 2)
        assert end.weekday() == 2  # Wednesday


# =============================================================================
# Tests for Signature Saving
# =============================================================================

class TestSignatureSaving:
    """Test signature image saving."""

    @patch('services.croa_signing_service.os.makedirs')
    @patch('builtins.open', create=True)
    def test_save_signature_image_success(self, mock_open, mock_makedirs):
        """Test successful signature image saving."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        service = CROASigningService(MagicMock())

        # Base64 encoded test data
        import base64
        signature_data = f"data:image/png;base64,{base64.b64encode(b'test').decode()}"

        result = service._save_signature_image(
            client_id=1,
            document_code='CROA_01_RIGHTS_DISCLOSURE',
            signature_data=signature_data
        )

        assert result is not None
        assert 'croa_sig_1_CROA_01' in result
        mock_makedirs.assert_called()

    @patch('services.croa_signing_service.os.makedirs')
    def test_save_signature_image_error(self, mock_makedirs):
        """Test signature saving handles errors gracefully."""
        mock_makedirs.side_effect = Exception("Permission denied")

        service = CROASigningService(MagicMock())

        result = service._save_signature_image(
            client_id=1,
            document_code='CROA_01_RIGHTS_DISCLOSURE',
            signature_data='invalid_data'
        )

        assert result is None


# =============================================================================
# Tests for Factory Function
# =============================================================================

class TestFactoryFunction:
    """Test service factory function."""

    @patch('services.croa_signing_service.SessionLocal')
    def test_get_service_creates_session(self, mock_session_class):
        """Test factory function creates new session."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        service = get_croa_signing_service()

        assert service is not None
        assert service.db == mock_session

    def test_get_service_with_existing_session(self):
        """Test factory function uses provided session."""
        mock_db = MagicMock()

        service = get_croa_signing_service(db=mock_db)

        assert service.db == mock_db


# =============================================================================
# Tests for Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_sign_document_with_drawn_signature(self):
        """Test signing with drawn signature saves image."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = None
        mock_progress.is_complete = False

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.code = 'CROA_01_RIGHTS_DISCLOSURE'
        mock_template.name = 'Rights Disclosure'

        mock_db.query().filter().first.side_effect = [
            mock_client, mock_progress, mock_template,
            mock_client, mock_progress
        ]

        service = CROASigningService(mock_db)

        import base64
        signature_data = f"data:image/png;base64,{base64.b64encode(b'test_image').decode()}"

        with patch.object(service, '_save_signature_image', return_value='/path/to/sig.png'):
            with patch.object(service, 'get_current_document', return_value={'success': True, 'document': None}):
                result = service.sign_document(
                    client_id=1,
                    document_code='CROA_01_RIGHTS_DISCLOSURE',
                    signature_data=signature_data,
                    signature_type='drawn'
                )

        assert result['success'] is True

    def test_progress_counts_signed_documents_correctly(self):
        """Test document counting is accurate."""
        service = CROASigningService(MagicMock())

        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow()
        mock_progress.lpoa_signed_at = datetime.utcnow()
        mock_progress.service_agreement_signed_at = datetime.utcnow()
        mock_progress.cancellation_notice_signed_at = None
        mock_progress.service_completion_signed_at = None
        mock_progress.hipaa_signed_at = None
        mock_progress.welcome_packet_signed_at = None

        count = service._count_signed_documents(mock_progress)

        assert count == 3

    def test_update_current_document_marks_complete(self):
        """Test progress is marked complete when all required signed."""
        service = CROASigningService(MagicMock())

        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = datetime.utcnow()
        mock_progress.lpoa_signed_at = datetime.utcnow()
        mock_progress.service_agreement_signed_at = datetime.utcnow()
        mock_progress.cancellation_notice_signed_at = datetime.utcnow()
        mock_progress.service_completion_signed_at = datetime.utcnow()
        mock_progress.hipaa_signed_at = None  # Optional
        mock_progress.welcome_packet_signed_at = datetime.utcnow()
        mock_progress.is_complete = False
        mock_progress.completed_at = None

        service._update_current_document(mock_progress)

        assert mock_progress.is_complete is True
        assert mock_progress.completed_at is not None
        assert mock_progress.current_document == 'complete'


# =============================================================================
# Tests for CROA Compliance
# =============================================================================

class TestCROACompliance:
    """Test CROA compliance requirements."""

    def test_rights_disclosure_must_be_first(self):
        """Verify Rights Disclosure must be signed first (CROA requirement)."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_progress = MagicMock()
        mock_progress.rights_disclosure_signed_at = None

        mock_template = MagicMock()
        mock_template.id = 2

        mock_db.query().filter().first.side_effect = [mock_client, mock_progress, mock_template]

        service = CROASigningService(mock_db)

        # Try to sign any document other than Rights Disclosure
        for doc in CROA_DOCUMENTS[1:]:  # Skip first (Rights Disclosure)
            mock_db.query().filter().first.side_effect = [mock_client, mock_progress, mock_template]
            result = service.sign_document(
                client_id=1,
                document_code=doc['code'],
                signature_data='test',
                signature_type='typed'
            )
            assert result['success'] is False
            assert 'Rights Disclosure' in result['error']

    def test_three_business_day_cancellation_period(self):
        """Verify 3 business day cancellation period is enforced."""
        service = CROASigningService(MagicMock())

        # Start on a Monday at 10am
        start = datetime(2025, 1, 6, 10, 0, 0)  # Monday
        end = service._calculate_cancellation_end(start)

        # The algorithm adds 3 business days after start
        # Monday start → Tue(1), Wed(2), Thu(3) → Thursday 5PM
        assert end.weekday() == 3  # Thursday
        assert end.hour == 17  # 5 PM

        # Also verify end is after start by at least 3 days
        days_diff = (end - start).days
        assert days_diff >= 3

    def test_document_signing_order_enforced(self):
        """Verify documents must be signed in order."""
        # This is tested implicitly by requiring Rights Disclosure first
        # and by the service tracking current_document
        assert CROA_DOCUMENTS[0]['code'] == 'CROA_01_RIGHTS_DISCLOSURE'
        assert CROA_DOCUMENTS[0]['order'] == 1
        assert CROA_DOCUMENTS[0]['must_sign_before_contract'] is True

    def test_all_required_documents_identified(self):
        """Verify all required CROA documents are properly marked."""
        required_docs = [d for d in CROA_DOCUMENTS if d['is_required']]

        # Should have 6 required documents (HIPAA is optional)
        assert len(required_docs) == 6

        required_codes = [d['code'] for d in required_docs]
        assert 'CROA_01_RIGHTS_DISCLOSURE' in required_codes
        assert 'CROA_02_LPOA' in required_codes
        assert 'CROA_03_SERVICE_AGREEMENT' in required_codes
        assert 'CROA_04_CANCELLATION_NOTICE' in required_codes
        assert 'CROA_05_SERVICE_COMPLETION' in required_codes
        assert 'CROA_07_WELCOME_PACKET' in required_codes
        assert 'CROA_06_HIPAA' not in required_codes
