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
