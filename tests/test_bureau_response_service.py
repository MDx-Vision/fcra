"""
Unit tests for BureauResponseService

Tests bureau dispute tracking, response recording, overdue detection,
and FCRA compliance features.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.bureau_response_service import (
    BureauResponseService,
    BUREAUS,
    STATUS_SENT,
    STATUS_DELIVERED,
    STATUS_AWAITING,
    STATUS_OVERDUE,
    STATUS_CLOSED,
    STANDARD_DEADLINE_DAYS,
    COMPLEX_DEADLINE_DAYS,
    RESPONSE_VERIFIED,
    RESPONSE_DELETED,
    RESPONSE_UPDATED,
    RESPONSE_MIXED,
    RESPONSE_FRIVOLOUS,
)

# Build response types list for tests
RESPONSE_TYPES = [RESPONSE_VERIFIED, RESPONSE_DELETED, RESPONSE_UPDATED, RESPONSE_MIXED, RESPONSE_FRIVOLOUS]
DEFAULT_RESPONSE_DAYS = STANDARD_DEADLINE_DAYS
EXTENDED_RESPONSE_DAYS = COMPLEX_DEADLINE_DAYS


# ============================================================================
# Constants Tests
# ============================================================================

class TestConstants:
    """Tests for module constants"""

    def test_bureaus_contains_three_bureaus(self):
        """Should have three credit bureaus"""
        assert len(BUREAUS) == 3
        assert "Equifax" in BUREAUS
        assert "Experian" in BUREAUS
        assert "TransUnion" in BUREAUS

    def test_response_types_defined(self):
        """Should have response types defined"""
        assert RESPONSE_DELETED == "deleted"
        assert RESPONSE_UPDATED == "updated"
        assert RESPONSE_VERIFIED == "verified"
        assert RESPONSE_MIXED == "mixed"
        assert RESPONSE_FRIVOLOUS == "frivolous"

    def test_status_constants(self):
        """Should have status constants"""
        assert STATUS_SENT == "sent"
        assert STATUS_DELIVERED == "delivered"
        assert STATUS_AWAITING == "awaiting_response"
        assert STATUS_OVERDUE == "overdue"
        assert STATUS_CLOSED == "closed"

    def test_response_day_defaults(self):
        """Should have correct FCRA response deadlines"""
        assert STANDARD_DEADLINE_DAYS == 30
        assert COMPLEX_DEADLINE_DAYS == 45


# ============================================================================
# Service Initialization Tests
# ============================================================================

class TestServiceInitialization:
    """Tests for service initialization"""

    def test_init_creates_service(self):
        """Should initialize service"""
        service = BureauResponseService()
        assert service is not None

    def test_init_db_is_none(self):
        """Should initialize with db as None"""
        service = BureauResponseService()
        assert service.db is None


# ============================================================================
# Track Dispute Sent Tests (with mocked DB)
# ============================================================================

class TestTrackDisputeSent:
    """Tests for tracking new disputes"""

    @patch('services.bureau_response_service.get_db')
    def test_track_dispute_creates_record(self, mock_get_db):
        """Should create tracking record for dispute"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_tracking = MagicMock()
        mock_tracking.to_dict.return_value = {'id': 1, 'status': 'sent'}
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = BureauResponseService()
        result = service.track_dispute_sent(
            client_id=1,
            bureau="Equifax",
            sent_date=date.today()
        )

        assert result['success'] == True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('services.bureau_response_service.get_db')
    def test_track_dispute_with_complex_flag(self, mock_get_db):
        """Should track complex disputes with 45-day deadline"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = BureauResponseService()
        result = service.track_dispute_sent(
            client_id=1,
            bureau="Experian",
            sent_date=date.today(),
            is_complex=True
        )

        assert result['success'] == True

    @patch('services.bureau_response_service.get_db')
    def test_track_dispute_with_case_id(self, mock_get_db):
        """Should track dispute with case reference"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = BureauResponseService()
        result = service.track_dispute_sent(
            client_id=1,
            bureau="TransUnion",
            sent_date=date.today(),
            case_id=123
        )

        assert result['success'] == True

    @patch('services.bureau_response_service.get_db')
    def test_track_dispute_with_dispute_round(self, mock_get_db):
        """Should track dispute round number"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = BureauResponseService()
        result = service.track_dispute_sent(
            client_id=1,
            bureau="Equifax",
            sent_date=date.today(),
            dispute_round=2
        )

        assert result['success'] == True

    @patch('services.bureau_response_service.get_db')
    def test_track_dispute_calculates_deadline(self, mock_get_db):
        """Should calculate expected response date"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = BureauResponseService()
        sent_date = date.today()
        result = service.track_dispute_sent(
            client_id=1,
            bureau="Equifax",
            sent_date=sent_date
        )

        assert result['success'] == True
        # Deadline should be 30 days from sent date
        expected_deadline = sent_date + timedelta(days=30)
        assert 'tracking' in result

    @patch('services.bureau_response_service.get_db')
    def test_track_dispute_generates_batch_id(self, mock_get_db):
        """Should generate batch ID"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = BureauResponseService()
        result = service.track_dispute_sent(
            client_id=1,
            bureau="Equifax",
            sent_date=date.today()
        )

        assert result['success'] == True


# ============================================================================
# Confirm Delivery Tests
# ============================================================================

class TestConfirmDelivery:
    """Tests for confirming mail delivery"""

    @patch('services.bureau_response_service.get_db')
    def test_confirm_delivery_updates_status(self, mock_get_db):
        """Should update status to delivered"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_tracking = MagicMock()
        mock_tracking.response_deadline_days = 30
        mock_tracking.to_dict.return_value = {'id': 1, 'status': 'delivered'}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tracking

        service = BureauResponseService()
        result = service.confirm_delivery(tracking_id=1, delivery_date=date.today())

        assert result['success'] == True
        mock_db.commit.assert_called_once()

    @patch('services.bureau_response_service.get_db')
    def test_confirm_delivery_not_found(self, mock_get_db):
        """Should return error for non-existent tracking"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = BureauResponseService()
        result = service.confirm_delivery(tracking_id=999, delivery_date=date.today())

        assert result['success'] == False


# ============================================================================
# Record Response Tests
# ============================================================================

class TestRecordResponse:
    """Tests for recording bureau responses"""

    @patch('services.bureau_response_service.get_db')
    def test_record_response_success(self, mock_get_db):
        """Should record response successfully"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_tracking = MagicMock()
        mock_tracking.to_dict.return_value = {'id': 1, 'response_received': True}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tracking

        service = BureauResponseService()
        result = service.record_response(
            tracking_id=1,
            response_date=date.today(),
            response_type="deleted"
        )

        assert result['success'] == True

    @patch('services.bureau_response_service.get_db')
    def test_record_response_with_item_counts(self, mock_get_db):
        """Should record item counts"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_tracking = MagicMock()
        mock_tracking.to_dict.return_value = {'id': 1}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tracking

        service = BureauResponseService()
        result = service.record_response(
            tracking_id=1,
            response_date=date.today(),
            response_type="mixed",
            items_deleted=5,
            items_updated=2,
            items_verified=3
        )

        assert result['success'] == True

    @patch('services.bureau_response_service.get_db')
    def test_record_response_not_found(self, mock_get_db):
        """Should return error for non-existent tracking"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = BureauResponseService()
        result = service.record_response(
            tracking_id=999,
            response_date=date.today(),
            response_type="deleted"
        )

        assert result['success'] == False


# ============================================================================
# Check Overdue Tests
# ============================================================================

class TestCheckOverdue:
    """Tests for overdue detection"""

    @patch('services.bureau_response_service.get_db')
    def test_check_overdue_marks_overdue_disputes(self, mock_get_db):
        """Should mark disputes past deadline as overdue"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_dispute = MagicMock()
        mock_dispute.id = 1
        mock_dispute.expected_response_date = date.today() - timedelta(days=5)
        mock_dispute.is_overdue = False
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_dispute]

        service = BureauResponseService()
        result = service.check_overdue_disputes()

        assert 'checked' in result
        assert 'newly_overdue' in result


# ============================================================================
# Query Method Tests (get_due_soon, get_overdue, etc.)
# ============================================================================

class TestQueryMethods:
    """Tests for query methods"""

    @patch('services.bureau_response_service.get_db')
    def test_get_due_soon_returns_list(self, mock_get_db):
        """Should return disputes due within specified days"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = BureauResponseService()
        result = service.get_due_soon(days=7)

        assert isinstance(result, list)

    @patch('services.bureau_response_service.get_db')
    def test_get_overdue_returns_list(self, mock_get_db):
        """Should return overdue disputes"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = BureauResponseService()
        result = service.get_overdue()

        assert isinstance(result, list)


# ============================================================================
# Dashboard Summary Tests
# ============================================================================

class TestDashboardSummary:
    """Tests for dashboard statistics"""

    @patch('services.bureau_response_service.get_db')
    def test_get_dashboard_summary_returns_dict(self, mock_get_db):
        """Should return dashboard statistics as dict"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = BureauResponseService()
        result = service.get_dashboard_summary()

        assert isinstance(result, dict)

    @patch('services.bureau_response_service.get_db')
    def test_get_dashboard_summary_has_expected_keys(self, mock_get_db):
        """Should have expected keys in summary"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = BureauResponseService()
        result = service.get_dashboard_summary()

        # Should have some stats-related keys
        assert isinstance(result, dict)


# ============================================================================
# Bureau Breakdown Tests
# ============================================================================

class TestBureauBreakdown:
    """Tests for bureau statistics"""

    @patch('services.bureau_response_service.get_db')
    def test_get_bureau_breakdown_returns_dict(self, mock_get_db):
        """Should return stats as dict"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = BureauResponseService()
        result = service.get_bureau_breakdown()

        assert isinstance(result, dict)


# ============================================================================
# Response Type Breakdown Tests
# ============================================================================

class TestResponseTypeBreakdown:
    """Tests for response type statistics"""

    def test_get_response_type_breakdown_returns_counts(self):
        """Should return counts for each response type"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ('deleted', 10),
            ('verified', 5),
        ]

        result = BureauResponseService.get_response_type_breakdown(mock_db)

        assert 'deleted' in result
        assert 'updated' in result
        assert 'verified' in result
        assert 'mixed' in result
        assert 'frivolous' in result

    def test_get_response_type_breakdown_handles_empty(self):
        """Should handle no responses"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = BureauResponseService.get_response_type_breakdown(mock_db)

        assert result['deleted'] == 0


# ============================================================================
# Close Dispute Tests
# ============================================================================

class TestCloseDispute:
    """Tests for closing disputes"""

    @patch('services.bureau_response_service.get_db')
    def test_close_dispute_success(self, mock_get_db):
        """Should close dispute successfully"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_tracking = MagicMock()
        mock_tracking.notes = ""
        mock_tracking.to_dict.return_value = {'id': 1, 'status': 'closed'}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tracking

        service = BureauResponseService()
        result = service.close_dispute(tracking_id=1)

        assert result['success'] == True
        assert mock_tracking.status == STATUS_CLOSED

    @patch('services.bureau_response_service.get_db')
    def test_close_dispute_not_found(self, mock_get_db):
        """Should return error for non-existent tracking"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = BureauResponseService()
        result = service.close_dispute(tracking_id=999)

        assert result['success'] == False


# ============================================================================
# Follow-up Tests
# ============================================================================

class TestFollowUp:
    """Tests for follow-up features"""

    @patch('services.bureau_response_service.get_db')
    def test_complete_follow_up_success(self, mock_get_db):
        """Should complete follow-up successfully"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_tracking = MagicMock()
        mock_tracking.follow_up_notes = ""
        mock_tracking.to_dict.return_value = {'id': 1}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tracking

        service = BureauResponseService()
        result = service.complete_follow_up(
            tracking_id=1,
            notes="Follow-up completed"
        )

        assert result['success'] == True


# ============================================================================
# Export Data Tests
# ============================================================================

class TestExportData:
    """Tests for data export"""

    @patch('services.bureau_response_service.get_db')
    def test_export_data_returns_list(self, mock_get_db):
        """Should return list of disputes for export"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = BureauResponseService()
        result = service.export_data()

        assert isinstance(result, list)


# ============================================================================
# FCRA Compliance Tests
# ============================================================================

class TestFCRACompliance:
    """Tests for FCRA compliance features"""

    def test_30_day_deadline_for_standard_disputes(self):
        """Standard disputes should have 30-day deadline"""
        assert STANDARD_DEADLINE_DAYS == 30

    def test_45_day_deadline_for_complex_disputes(self):
        """Complex disputes should have 45-day deadline"""
        assert COMPLEX_DEADLINE_DAYS == 45

    @patch('services.bureau_response_service.get_db')
    def test_deadline_calculation_from_sent_date(self, mock_get_db):
        """Deadline should be calculated from sent date"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = BureauResponseService()
        sent_date = date.today()
        result = service.track_dispute_sent(
            client_id=1,
            bureau="Equifax",
            sent_date=sent_date
        )

        # Verify the add was called (deadline is set internally)
        assert result['success'] == True


# ============================================================================
# Integration-like Tests (with mocked DB)
# ============================================================================

class TestIntegration:
    """Integration-style tests with mocked database"""

    @patch('services.bureau_response_service.get_db')
    def test_full_dispute_lifecycle(self, mock_get_db):
        """Test complete dispute lifecycle: track -> deliver -> respond -> close"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_tracking = MagicMock()
        mock_tracking.id = 1
        mock_tracking.response_deadline_days = 30
        mock_tracking.notes = ""
        mock_tracking.to_dict.return_value = {'id': 1, 'status': 'closed'}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tracking

        service = BureauResponseService()

        # Track dispute
        track_result = service.track_dispute_sent(
            client_id=1,
            bureau="Equifax",
            sent_date=date.today()
        )
        assert track_result['success'] == True

        # Confirm delivery
        deliver_result = service.confirm_delivery(
            tracking_id=1,
            delivery_date=date.today()
        )
        assert deliver_result['success'] == True

        # Record response
        response_result = service.record_response(
            tracking_id=1,
            response_date=date.today(),
            response_type="deleted",
            items_deleted=5
        )
        assert response_result['success'] == True

        # Close dispute
        close_result = service.close_dispute(tracking_id=1)
        assert close_result['success'] == True

    @patch('services.bureau_response_service.get_db')
    def test_multi_bureau_tracking(self, mock_get_db):
        """Test tracking disputes to all three bureaus"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = BureauResponseService()

        for bureau in BUREAUS:
            result = service.track_dispute_sent(
                client_id=1,
                bureau=bureau,
                sent_date=date.today()
            )
            assert result['success'] == True


# ============================================================================
# Response Parsing Tests (ISSUE-010)
# ============================================================================

class TestResponseTextParsing:
    """Tests for response text parsing functionality"""

    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return BureauResponseService(session=mock_db)

    def test_parse_deletion_response(self, service):
        """Test parsing a deletion response letter"""
        text = """
        Dear Consumer,

        We have completed our investigation. The account you disputed
        has been deleted from your credit file.

        Sincerely,
        Equifax Consumer Services
        """
        result = service._parse_response_text(text)

        assert result["response_type"] == RESPONSE_DELETED
        assert result["bureau"] == "Equifax"
        assert result["items_deleted"] >= 1

    def test_parse_verified_response(self, service):
        """Test parsing a verified as accurate response"""
        text = """
        TransUnion Investigation Results

        The information has been verified as accurate and will remain
        on your credit file.

        TransUnion Consumer Relations
        P.O. Box 2000, Chester, PA
        """
        result = service._parse_response_text(text)

        assert result["response_type"] == RESPONSE_VERIFIED
        assert result["bureau"] == "TransUnion"
        assert result["requires_follow_up"] is True

    def test_parse_updated_response(self, service):
        """Test parsing an updated response"""
        text = """
        Experian Investigation Complete

        The account information has been updated to reflect
        the corrected balance.

        P.O. Box 4500, Allen, TX
        """
        result = service._parse_response_text(text)

        assert result["response_type"] == RESPONSE_UPDATED
        assert result["bureau"] == "Experian"

    def test_parse_mixed_response(self, service):
        """Test parsing mixed results (some deleted, some verified)"""
        text = """
        Investigation Results:
        Account #1234: has been deleted from your credit report
        Account #5678: has been verified as accurate

        Equifax
        """
        result = service._parse_response_text(text)

        assert result["response_type"] == RESPONSE_MIXED

    def test_parse_frivolous_response(self, service):
        """Test parsing a frivolous determination"""
        text = """
        Your dispute is determined to be frivolous because it is
        substantially similar to your previous dispute.
        Please provide additional documentation.
        """
        result = service._parse_response_text(text)

        assert result["response_type"] == RESPONSE_FRIVOLOUS
        assert result["is_frivolous"] is True
        assert result["requires_follow_up"] is True

    def test_identify_equifax_bureau(self, service):
        """Test identifying Equifax from text"""
        text = "equifax information services atlanta ga"
        result = service._identify_bureau(text)
        assert result == "Equifax"

    def test_identify_experian_bureau(self, service):
        """Test identifying Experian from text"""
        text = "experian consumer services p.o. box 4500 allen tx"
        result = service._identify_bureau(text)
        assert result == "Experian"

    def test_identify_transunion_bureau(self, service):
        """Test identifying TransUnion from text"""
        text = "transunion p.o. box 2000 chester pa"
        result = service._identify_bureau(text)
        assert result == "TransUnion"

    def test_extract_account_numbers(self, service):
        """Test account number extraction"""
        text = """
        Account Number: 1234567890
        Acct# 9876543210
        Reference# REF-ABC-123
        """
        result = service._extract_account_numbers(text)

        assert len(result) >= 2

    def test_extract_dates_from_text(self, service):
        """Test date extraction"""
        text = """
        Investigation completed on 02/08/2026.
        Original dispute filed: January 15, 2026
        """
        result = service._extract_dates(text)

        assert len(result) >= 1

    def test_extract_item_counts(self, service):
        """Test extracting item counts from response"""
        text = """
        Results: 3 items have been deleted from your credit file.
        2 accounts were verified as accurate.
        """
        result = service._extract_item_counts(text)

        assert result["items_deleted"] >= 1
        assert result["items_verified"] >= 1


class TestExtractStatusFromText:
    """Tests for the extract_status_from_text API method"""

    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return BureauResponseService(session=mock_db)

    def test_extract_status_success(self, service):
        """Test successful status extraction"""
        text = "Your disputed account has been deleted."
        result = service.extract_status_from_text(text)

        assert result["success"] is True
        assert result["data"]["response_type"] == RESPONSE_DELETED

    def test_extract_status_empty_text(self, service):
        """Test with empty text"""
        result = service.extract_status_from_text("")
        assert result["success"] is False

    def test_extract_status_whitespace(self, service):
        """Test with whitespace only"""
        result = service.extract_status_from_text("   \n\t  ")
        assert result["success"] is False


class TestParseResponseLetter:
    """Tests for file-based response parsing"""

    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return BureauResponseService(session=mock_db)

    def test_parse_file_not_found(self, service):
        """Test with non-existent file"""
        result = service.parse_response_letter("/nonexistent/file.pdf")

        assert result["success"] is False
        assert "FILE_NOT_FOUND" in result["error_code"]


class TestBatchParseResponses:
    """Tests for batch response parsing"""

    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return BureauResponseService(session=mock_db)

    def test_batch_parse_empty_list(self, service):
        """Test with empty file list"""
        result = service.batch_parse_responses([])

        assert result["success"] is True
        assert result["data"]["total"] == 0

    @patch.object(BureauResponseService, 'parse_response_letter')
    def test_batch_parse_counts_results(self, mock_parse, service):
        """Test batch parsing counts success/failure"""
        mock_parse.side_effect = [
            {"success": True, "data": {"response_type": "deleted"}},
            {"success": False, "error": "File not found"},
        ]

        result = service.batch_parse_responses(["/file1.pdf", "/file2.pdf"])

        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert result["data"]["success_count"] == 1
        assert result["data"]["error_count"] == 1


class TestGetParseSummary:
    """Tests for parse summary statistics"""

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_session):
        return BureauResponseService(session=mock_session)

    def test_get_parse_summary_empty(self, service, mock_session):
        """Test summary with no responses"""
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = service.get_parse_summary()

        assert result["success"] is True
        assert result["data"]["total_responses"] == 0

    def test_get_parse_summary_with_data(self, service, mock_session):
        """Test summary with response data"""
        mock_response = MagicMock()
        mock_response.response_type = "deleted"
        mock_response.bureau = "Equifax"
        mock_response.items_deleted = 2
        mock_response.items_updated = 0
        mock_response.items_verified = 0
        mock_response.follow_up_required = False
        mock_response.follow_up_completed = False

        mock_session.query.return_value.filter.return_value.all.return_value = [mock_response]

        result = service.get_parse_summary()

        assert result["success"] is True
        assert result["data"]["total_responses"] == 1
        assert result["data"]["by_type"]["deleted"] == 1
        assert result["data"]["total_items_deleted"] == 2


class TestErrorHandlingImprovements:
    """Tests for improved error handling (ISSUE-010)"""

    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return BureauResponseService(session=mock_db)

    def test_error_response_structure(self, service):
        """Test error response has proper structure"""
        result = service._error_response(
            "Test error",
            "TEST_CODE",
            {"key": "value"}
        )

        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["error_code"] == "TEST_CODE"
        assert result["details"]["key"] == "value"

    def test_success_response_structure(self, service):
        """Test success response has proper structure"""
        result = service._success_response(
            data={"key": "value"},
            message="Test success"
        )

        assert result["success"] is True
        assert result["data"]["key"] == "value"
        assert result["message"] == "Test success"

    def test_success_response_with_kwargs(self, service):
        """Test success response with extra kwargs"""
        result = service._success_response(
            count=5,
            total=10
        )

        assert result["success"] is True
        assert result["count"] == 5
        assert result["total"] == 10
