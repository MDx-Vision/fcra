"""
Unit Tests for Deadline Service.
Tests for FCRA deadline tracking and management including:
- Deadline creation and tracking
- Due date calculations
- Reminder notifications
- Deadline status updates
- Client deadline retrieval
- Upcoming deadline queries
- Deadline extensions and cancellations
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, date, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.deadline_service import (
    DEADLINE_TYPES,
    get_deadline_type_info,
    create_deadline,
    get_client_deadlines,
    get_upcoming_deadlines,
    _get_urgency_level,
    complete_deadline,
    extend_deadline,
    check_and_send_reminders,
    _send_deadline_reminder,
    _build_deadline_email,
    cancel_deadline,
    get_deadline_summary,
    create_cra_response_deadline,
    create_reinvestigation_deadline,
)


# =============================================================================
# Tests for DEADLINE_TYPES Constants
# =============================================================================

class TestDeadlineTypesConfiguration:
    """Test deadline type constants are properly defined."""

    def test_cra_response_type_exists(self):
        """Test CRA response deadline type exists with correct defaults."""
        assert "cra_response" in DEADLINE_TYPES
        assert DEADLINE_TYPES["cra_response"]["default_days"] == 30
        assert DEADLINE_TYPES["cra_response"]["name"] == "CRA Response"

    def test_reinvestigation_type_exists(self):
        """Test reinvestigation deadline type exists with correct defaults."""
        assert "reinvestigation" in DEADLINE_TYPES
        assert DEADLINE_TYPES["reinvestigation"]["default_days"] == 45
        assert DEADLINE_TYPES["reinvestigation"]["name"] == "Reinvestigation"

    def test_data_furnisher_type_exists(self):
        """Test data furnisher deadline type exists with correct defaults."""
        assert "data_furnisher" in DEADLINE_TYPES
        assert DEADLINE_TYPES["data_furnisher"]["default_days"] == 30
        assert DEADLINE_TYPES["data_furnisher"]["name"] == "Data Furnisher Response"

    def test_client_action_type_exists(self):
        """Test client action deadline type exists with correct defaults."""
        assert "client_action" in DEADLINE_TYPES
        assert DEADLINE_TYPES["client_action"]["default_days"] == 14
        assert DEADLINE_TYPES["client_action"]["name"] == "Client Action Required"

    def test_legal_filing_type_exists(self):
        """Test legal filing deadline type exists with correct defaults."""
        assert "legal_filing" in DEADLINE_TYPES
        assert DEADLINE_TYPES["legal_filing"]["default_days"] == 365
        assert DEADLINE_TYPES["legal_filing"]["name"] == "Legal Filing Deadline"

    def test_all_deadline_types_have_required_fields(self):
        """Test all deadline types have name, default_days, and description."""
        for type_key, type_info in DEADLINE_TYPES.items():
            assert "name" in type_info, f"{type_key} missing name"
            assert "default_days" in type_info, f"{type_key} missing default_days"
            assert "description" in type_info, f"{type_key} missing description"


# =============================================================================
# Tests for get_deadline_type_info()
# =============================================================================

class TestGetDeadlineTypeInfo:
    """Test deadline type info retrieval function."""

    def test_get_known_deadline_type(self):
        """Test retrieving info for a known deadline type."""
        info = get_deadline_type_info("cra_response")
        assert info["name"] == "CRA Response"
        assert info["default_days"] == 30

    def test_get_reinvestigation_deadline_type(self):
        """Test retrieving reinvestigation deadline type info."""
        info = get_deadline_type_info("reinvestigation")
        assert info["name"] == "Reinvestigation"
        assert info["default_days"] == 45

    def test_get_unknown_deadline_type_returns_default(self):
        """Test unknown deadline type returns default values."""
        info = get_deadline_type_info("unknown_type")
        assert info["name"] == "Unknown Type"
        assert info["default_days"] == 30
        assert info["description"] == "Custom deadline"

    def test_get_custom_deadline_type_with_underscores(self):
        """Test custom deadline type formats name correctly."""
        info = get_deadline_type_info("my_custom_deadline")
        assert info["name"] == "My Custom Deadline"

    def test_get_client_action_deadline_type(self):
        """Test client action deadline type info."""
        info = get_deadline_type_info("client_action")
        assert info["name"] == "Client Action Required"
        assert info["default_days"] == 14


# =============================================================================
# Tests for create_deadline()
# =============================================================================

class TestCreateDeadline:
    """Test deadline creation function."""

    @patch('database.CaseDeadline')
    @patch('database.Client')
    def test_create_deadline_with_date_object(self, MockClient, MockCaseDeadline):
        """Test creating deadline with date object."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        MockCaseDeadline.return_value = mock_deadline
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        start_date = date(2024, 1, 15)
        result = create_deadline(
            db=mock_db,
            client_id=1,
            case_id=10,
            deadline_type="cra_response",
            bureau="Experian",
            dispute_round=1,
            start_date=start_date,
            days_allowed=30
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('database.CaseDeadline')
    @patch('database.Client')
    def test_create_deadline_with_string_date(self, MockClient, MockCaseDeadline):
        """Test creating deadline with string date."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 2
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        MockCaseDeadline.return_value = mock_deadline
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        result = create_deadline(
            db=mock_db,
            client_id=1,
            case_id=10,
            deadline_type="cra_response",
            bureau="TransUnion",
            dispute_round=1,
            start_date="2024-01-15",
            days_allowed=30
        )

        mock_db.add.assert_called_once()

    @patch('database.CaseDeadline')
    @patch('database.Client')
    def test_create_deadline_with_datetime_object(self, MockClient, MockCaseDeadline):
        """Test creating deadline with datetime object."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 3
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        MockCaseDeadline.return_value = mock_deadline
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        start_date = datetime(2024, 1, 15, 10, 30, 0)
        result = create_deadline(
            db=mock_db,
            client_id=1,
            case_id=10,
            deadline_type="cra_response",
            bureau="Equifax",
            dispute_round=1,
            start_date=start_date
        )

        mock_db.add.assert_called_once()

    @patch('database.CaseDeadline')
    @patch('database.Client')
    def test_create_deadline_uses_default_days_when_not_provided(self, MockClient, MockCaseDeadline):
        """Test deadline uses type-specific default days when not provided."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 4
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        MockCaseDeadline.return_value = mock_deadline
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        create_deadline(
            db=mock_db,
            client_id=1,
            case_id=10,
            deadline_type="reinvestigation",
            bureau="Experian",
            dispute_round=1,
            start_date=date(2024, 1, 15)
            # days_allowed not provided - should use 45 for reinvestigation
        )

        # Check that CaseDeadline was called with days_allowed=45
        call_args = MockCaseDeadline.call_args
        assert call_args.kwargs["days_allowed"] == 45

    @patch('database.CaseDeadline')
    @patch('database.Client')
    def test_create_deadline_calculates_deadline_date_correctly(self, MockClient, MockCaseDeadline):
        """Test deadline date is calculated correctly from start date and days."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 5
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        MockCaseDeadline.return_value = mock_deadline
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        start_date = date(2024, 1, 15)
        create_deadline(
            db=mock_db,
            client_id=1,
            case_id=10,
            deadline_type="cra_response",
            bureau="Experian",
            dispute_round=1,
            start_date=start_date,
            days_allowed=30
        )

        call_args = MockCaseDeadline.call_args
        expected_deadline_date = date(2024, 2, 14)  # 30 days from Jan 15
        assert call_args.kwargs["deadline_date"] == expected_deadline_date

    @patch('database.CaseDeadline')
    @patch('database.Client')
    def test_create_deadline_with_no_case_id(self, MockClient, MockCaseDeadline):
        """Test creating deadline without case_id."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 6
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        MockCaseDeadline.return_value = mock_deadline
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        create_deadline(
            db=mock_db,
            client_id=1,
            case_id=None,
            deadline_type="client_action",
            bureau=None,
            dispute_round=1,
            start_date=date(2024, 1, 15)
        )

        call_args = MockCaseDeadline.call_args
        assert call_args.kwargs["case_id"] is None

    @patch('database.CaseDeadline')
    @patch('database.Client')
    def test_create_deadline_handles_client_not_found(self, MockClient, MockCaseDeadline):
        """Test deadline creation when client not found."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 7
        mock_deadline.client_id = 999

        MockCaseDeadline.return_value = mock_deadline
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = create_deadline(
            db=mock_db,
            client_id=999,
            case_id=10,
            deadline_type="cra_response",
            bureau="Experian",
            dispute_round=1,
            start_date=date(2024, 1, 15)
        )

        # Should still create deadline, just with fallback name
        mock_db.add.assert_called_once()

    @patch('database.CaseDeadline')
    def test_create_deadline_rollback_on_error(self, MockCaseDeadline):
        """Test deadline creation rolls back on error."""
        mock_db = MagicMock()
        mock_db.commit.side_effect = Exception("Database error")
        MockCaseDeadline.return_value = MagicMock()

        with pytest.raises(Exception):
            create_deadline(
                db=mock_db,
                client_id=1,
                case_id=10,
                deadline_type="cra_response",
                bureau="Experian",
                dispute_round=1,
                start_date=date(2024, 1, 15)
            )

        mock_db.rollback.assert_called_once()


# =============================================================================
# Tests for get_client_deadlines()
# =============================================================================

class TestGetClientDeadlines:
    """Test client deadline retrieval function."""

    def test_get_client_deadlines_empty(self):
        """Test getting deadlines when none exist."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = get_client_deadlines(mock_db, client_id=1)

        assert result == []

    def test_get_client_deadlines_active_only(self):
        """Test getting only active deadlines."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.case_id = 10
        mock_deadline.deadline_type = "cra_response"
        mock_deadline.bureau = "Experian"
        mock_deadline.dispute_round = 1
        mock_deadline.start_date = date(2024, 1, 1)
        mock_deadline.deadline_date = date.today() + timedelta(days=5)
        mock_deadline.days_allowed = 30
        mock_deadline.status = "active"
        mock_deadline.completed_at = None
        mock_deadline.reminder_sent_7_days = False
        mock_deadline.reminder_sent_3_days = False
        mock_deadline.reminder_sent_1_day = False
        mock_deadline.overdue_notice_sent = False
        mock_deadline.notes = None
        mock_deadline.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_deadline]

        result = get_client_deadlines(mock_db, client_id=1, include_completed=False)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["days_remaining"] == 5
        assert result[0]["is_overdue"] is False

    def test_get_client_deadlines_includes_completed(self):
        """Test getting deadlines including completed ones."""
        mock_db = MagicMock()
        mock_active = MagicMock()
        mock_active.id = 1
        mock_active.client_id = 1
        mock_active.case_id = 10
        mock_active.deadline_type = "cra_response"
        mock_active.bureau = "Experian"
        mock_active.dispute_round = 1
        mock_active.start_date = date(2024, 1, 1)
        mock_active.deadline_date = date.today() + timedelta(days=5)
        mock_active.days_allowed = 30
        mock_active.status = "active"
        mock_active.completed_at = None
        mock_active.reminder_sent_7_days = False
        mock_active.reminder_sent_3_days = False
        mock_active.reminder_sent_1_day = False
        mock_active.overdue_notice_sent = False
        mock_active.notes = None
        mock_active.created_at = datetime.utcnow()

        mock_completed = MagicMock()
        mock_completed.id = 2
        mock_completed.client_id = 1
        mock_completed.case_id = 10
        mock_completed.deadline_type = "cra_response"
        mock_completed.bureau = "TransUnion"
        mock_completed.dispute_round = 1
        mock_completed.start_date = date(2024, 1, 1)
        mock_completed.deadline_date = date.today() - timedelta(days=5)
        mock_completed.days_allowed = 30
        mock_completed.status = "completed"
        mock_completed.completed_at = datetime.utcnow()
        mock_completed.reminder_sent_7_days = True
        mock_completed.reminder_sent_3_days = True
        mock_completed.reminder_sent_1_day = True
        mock_completed.overdue_notice_sent = False
        mock_completed.notes = "Completed on time"
        mock_completed.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_active, mock_completed]

        result = get_client_deadlines(mock_db, client_id=1, include_completed=True)

        assert len(result) == 2

    def test_get_client_deadlines_calculates_overdue_correctly(self):
        """Test overdue deadline detection."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.case_id = 10
        mock_deadline.deadline_type = "cra_response"
        mock_deadline.bureau = "Experian"
        mock_deadline.dispute_round = 1
        mock_deadline.start_date = date(2024, 1, 1)
        mock_deadline.deadline_date = date.today() - timedelta(days=3)  # 3 days overdue
        mock_deadline.days_allowed = 30
        mock_deadline.status = "active"
        mock_deadline.completed_at = None
        mock_deadline.reminder_sent_7_days = True
        mock_deadline.reminder_sent_3_days = True
        mock_deadline.reminder_sent_1_day = True
        mock_deadline.overdue_notice_sent = True
        mock_deadline.notes = None
        mock_deadline.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_deadline]

        result = get_client_deadlines(mock_db, client_id=1)

        assert len(result) == 1
        assert result[0]["is_overdue"] is True
        assert result[0]["days_remaining"] == -3


# =============================================================================
# Tests for get_upcoming_deadlines()
# =============================================================================

class TestGetUpcomingDeadlines:
    """Test upcoming deadlines retrieval function."""

    def test_get_upcoming_deadlines_empty(self):
        """Test getting upcoming deadlines when none exist."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = get_upcoming_deadlines(mock_db, days_ahead=7)

        assert result == []

    def test_get_upcoming_deadlines_with_results(self):
        """Test getting upcoming deadlines with results."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.case_id = 10
        mock_deadline.deadline_type = "cra_response"
        mock_deadline.bureau = "Experian"
        mock_deadline.dispute_round = 1
        mock_deadline.start_date = date(2024, 1, 1)
        mock_deadline.deadline_date = date.today() + timedelta(days=3)
        mock_deadline.status = "active"
        mock_deadline.notes = None

        mock_client = MagicMock()
        mock_client.name = "Test Client"
        mock_client.email = "test@example.com"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(mock_deadline, mock_client)]

        result = get_upcoming_deadlines(mock_db, days_ahead=7)

        assert len(result) == 1
        assert result[0]["client_name"] == "Test Client"
        assert result[0]["urgency"] == "high"  # 3 days remaining = high

    def test_get_upcoming_deadlines_includes_overdue(self):
        """Test upcoming deadlines includes overdue when flag is True."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.case_id = 10
        mock_deadline.deadline_type = "cra_response"
        mock_deadline.bureau = "Experian"
        mock_deadline.dispute_round = 1
        mock_deadline.start_date = date(2024, 1, 1)
        mock_deadline.deadline_date = date.today() - timedelta(days=2)  # Overdue
        mock_deadline.status = "active"
        mock_deadline.notes = None

        mock_client = MagicMock()
        mock_client.name = "Test Client"
        mock_client.email = "test@example.com"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(mock_deadline, mock_client)]

        result = get_upcoming_deadlines(mock_db, days_ahead=7, include_overdue=True)

        assert len(result) == 1
        assert result[0]["is_overdue"] is True
        assert result[0]["urgency"] == "overdue"


# =============================================================================
# Tests for _get_urgency_level()
# =============================================================================

class TestGetUrgencyLevel:
    """Test urgency level calculation."""

    def test_urgency_overdue(self):
        """Test overdue urgency level."""
        assert _get_urgency_level(-1) == "overdue"
        assert _get_urgency_level(-5) == "overdue"
        assert _get_urgency_level(-100) == "overdue"

    def test_urgency_critical(self):
        """Test critical urgency level (0-1 days)."""
        assert _get_urgency_level(0) == "critical"
        assert _get_urgency_level(1) == "critical"

    def test_urgency_high(self):
        """Test high urgency level (2-3 days)."""
        assert _get_urgency_level(2) == "high"
        assert _get_urgency_level(3) == "high"

    def test_urgency_medium(self):
        """Test medium urgency level (4-7 days)."""
        assert _get_urgency_level(4) == "medium"
        assert _get_urgency_level(7) == "medium"

    def test_urgency_low(self):
        """Test low urgency level (8+ days)."""
        assert _get_urgency_level(8) == "low"
        assert _get_urgency_level(30) == "low"
        assert _get_urgency_level(365) == "low"


# =============================================================================
# Tests for complete_deadline()
# =============================================================================

class TestCompleteDeadline:
    """Test deadline completion function."""

    def test_complete_deadline_not_found(self):
        """Test completing non-existent deadline."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = complete_deadline(mock_db, deadline_id=999)

        assert result is None

    def test_complete_deadline_success(self):
        """Test successfully completing a deadline."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.status = "active"
        mock_deadline.notes = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline

        result = complete_deadline(mock_db, deadline_id=1)

        assert mock_deadline.status == "completed"
        assert mock_deadline.completed_at is not None
        mock_db.commit.assert_called_once()

    def test_complete_deadline_with_notes(self):
        """Test completing deadline with notes."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.status = "active"
        mock_deadline.notes = "Existing notes"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline

        result = complete_deadline(mock_db, deadline_id=1, notes="CRA responded on time")

        assert "[Completed]" in mock_deadline.notes
        assert "CRA responded on time" in mock_deadline.notes

    def test_complete_deadline_with_empty_existing_notes(self):
        """Test completing deadline when notes field is empty."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.status = "active"
        mock_deadline.notes = ""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline

        result = complete_deadline(mock_db, deadline_id=1, notes="Completed early")

        assert "[Completed] Completed early" in mock_deadline.notes

    def test_complete_deadline_rollback_on_error(self):
        """Test completion rolls back on error."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            complete_deadline(mock_db, deadline_id=1)

        mock_db.rollback.assert_called_once()


# =============================================================================
# Tests for extend_deadline()
# =============================================================================

class TestExtendDeadline:
    """Test deadline extension function."""

    def test_extend_deadline_not_found(self):
        """Test extending non-existent deadline."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = extend_deadline(mock_db, deadline_id=999, new_days=45)

        assert result is None

    def test_extend_deadline_success(self):
        """Test successfully extending a deadline."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.start_date = date(2024, 1, 15)
        mock_deadline.deadline_date = date(2024, 2, 14)  # Original: 30 days
        mock_deadline.days_allowed = 30
        mock_deadline.status = "active"
        mock_deadline.reminder_sent_7_days = True
        mock_deadline.reminder_sent_3_days = True
        mock_deadline.reminder_sent_1_day = True
        mock_deadline.overdue_notice_sent = False
        mock_deadline.notes = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline

        result = extend_deadline(mock_db, deadline_id=1, new_days=45)

        # New deadline should be start_date + 45 days
        expected_new_deadline = date(2024, 2, 29)  # Jan 15 + 45 days
        assert mock_deadline.deadline_date == expected_new_deadline
        assert mock_deadline.days_allowed == 45
        # Reminder flags should be reset
        assert mock_deadline.reminder_sent_7_days is False
        assert mock_deadline.reminder_sent_3_days is False
        assert mock_deadline.reminder_sent_1_day is False
        mock_db.commit.assert_called_once()

    def test_extend_deadline_reactivates_completed(self):
        """Test extending a completed deadline reactivates it."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.start_date = date(2024, 1, 15)
        mock_deadline.deadline_date = date(2024, 2, 14)
        mock_deadline.days_allowed = 30
        mock_deadline.status = "completed"
        mock_deadline.completed_at = datetime.utcnow()
        mock_deadline.reminder_sent_7_days = True
        mock_deadline.reminder_sent_3_days = True
        mock_deadline.reminder_sent_1_day = True
        mock_deadline.overdue_notice_sent = True
        mock_deadline.notes = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline

        result = extend_deadline(mock_db, deadline_id=1, new_days=60)

        assert mock_deadline.status == "active"
        assert mock_deadline.completed_at is None

    def test_extend_deadline_with_notes(self):
        """Test extending deadline with notes."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.start_date = date(2024, 1, 15)
        mock_deadline.deadline_date = date(2024, 2, 14)
        mock_deadline.days_allowed = 30
        mock_deadline.status = "active"
        mock_deadline.reminder_sent_7_days = False
        mock_deadline.reminder_sent_3_days = False
        mock_deadline.reminder_sent_1_day = False
        mock_deadline.overdue_notice_sent = False
        mock_deadline.notes = "Original notes"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline

        result = extend_deadline(mock_db, deadline_id=1, new_days=45, notes="Extended due to reinvestigation")

        assert "[Extended]" in mock_deadline.notes
        assert "Extended due to reinvestigation" in mock_deadline.notes


# =============================================================================
# Tests for check_and_send_reminders()
# =============================================================================

class TestCheckAndSendReminders:
    """Test reminder checking and sending function."""

    @patch('services.deadline_service.is_sendgrid_configured')
    def test_check_reminders_sendgrid_not_configured(self, mock_sendgrid):
        """Test reminder check when SendGrid is not configured."""
        mock_sendgrid.return_value = False
        mock_db = MagicMock()

        result = check_and_send_reminders(mock_db)

        assert result["checked"] == 0
        assert result["errors"] == 0

    @patch('services.deadline_service._send_deadline_reminder')
    @patch('services.deadline_service.is_sendgrid_configured')
    def test_check_reminders_sends_7_day_reminder(self, mock_sendgrid, mock_send):
        """Test 7-day reminder is sent."""
        mock_sendgrid.return_value = True
        mock_send.return_value = True

        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.deadline_date = date.today() + timedelta(days=5)  # 5 days remaining
        mock_deadline.status = "active"
        mock_deadline.reminder_sent_7_days = False
        mock_deadline.reminder_sent_3_days = False
        mock_deadline.reminder_sent_1_day = False
        mock_deadline.overdue_notice_sent = False

        mock_client = MagicMock()
        mock_client.email = "test@example.com"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(mock_deadline, mock_client)]

        result = check_and_send_reminders(mock_db)

        assert result["reminders_7_days"] == 1
        assert mock_deadline.reminder_sent_7_days is True

    @patch('services.deadline_service._send_deadline_reminder')
    @patch('services.deadline_service.is_sendgrid_configured')
    def test_check_reminders_sends_3_day_reminder(self, mock_sendgrid, mock_send):
        """Test 3-day reminder is sent."""
        mock_sendgrid.return_value = True
        mock_send.return_value = True

        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.deadline_date = date.today() + timedelta(days=2)  # 2 days remaining
        mock_deadline.status = "active"
        mock_deadline.reminder_sent_7_days = True
        mock_deadline.reminder_sent_3_days = False
        mock_deadline.reminder_sent_1_day = False
        mock_deadline.overdue_notice_sent = False

        mock_client = MagicMock()
        mock_client.email = "test@example.com"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(mock_deadline, mock_client)]

        result = check_and_send_reminders(mock_db)

        assert result["reminders_3_days"] == 1
        assert mock_deadline.reminder_sent_3_days is True

    @patch('services.deadline_service._send_deadline_reminder')
    @patch('services.deadline_service.is_sendgrid_configured')
    def test_check_reminders_sends_1_day_reminder(self, mock_sendgrid, mock_send):
        """Test 1-day reminder is sent."""
        mock_sendgrid.return_value = True
        mock_send.return_value = True

        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.deadline_date = date.today() + timedelta(days=1)  # 1 day remaining
        mock_deadline.status = "active"
        mock_deadline.reminder_sent_7_days = True
        mock_deadline.reminder_sent_3_days = True
        mock_deadline.reminder_sent_1_day = False
        mock_deadline.overdue_notice_sent = False

        mock_client = MagicMock()
        mock_client.email = "test@example.com"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(mock_deadline, mock_client)]

        result = check_and_send_reminders(mock_db)

        assert result["reminders_1_day"] == 1
        assert mock_deadline.reminder_sent_1_day is True

    @patch('services.deadline_service._send_deadline_reminder')
    @patch('services.deadline_service.is_sendgrid_configured')
    def test_check_reminders_sends_overdue_notice(self, mock_sendgrid, mock_send):
        """Test overdue notice is sent."""
        mock_sendgrid.return_value = True
        mock_send.return_value = True

        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.deadline_date = date.today() - timedelta(days=2)  # 2 days overdue
        mock_deadline.status = "active"
        mock_deadline.reminder_sent_7_days = True
        mock_deadline.reminder_sent_3_days = True
        mock_deadline.reminder_sent_1_day = True
        mock_deadline.overdue_notice_sent = False

        mock_client = MagicMock()
        mock_client.email = "test@example.com"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(mock_deadline, mock_client)]

        result = check_and_send_reminders(mock_db)

        assert result["overdue_notices"] == 1
        assert mock_deadline.overdue_notice_sent is True


# =============================================================================
# Tests for _build_deadline_email()
# =============================================================================

class TestBuildDeadlineEmail:
    """Test deadline email building function."""

    @patch('services.deadline_service.email_templates.get_base_template')
    def test_build_overdue_email(self, mock_template):
        """Test building overdue email."""
        mock_template.return_value = "<html>Email content</html>"

        subject, content = _build_deadline_email(
            first_name="John",
            deadline_type_name="CRA Response",
            bureau="Experian",
            deadline_date=date(2024, 1, 15),
            days_remaining=-3,
            reminder_type="overdue",
            dispute_round=1
        )

        assert "OVERDUE" in subject
        assert "CRA Response" in subject

    @patch('services.deadline_service.email_templates.get_base_template')
    def test_build_1_day_email(self, mock_template):
        """Test building 1-day reminder email."""
        mock_template.return_value = "<html>Email content</html>"

        subject, content = _build_deadline_email(
            first_name="Jane",
            deadline_type_name="CRA Response",
            bureau="TransUnion",
            deadline_date=date.today() + timedelta(days=1),
            days_remaining=1,
            reminder_type="1_day",
            dispute_round=2
        )

        assert "URGENT" in subject
        assert "Tomorrow" in subject

    @patch('services.deadline_service.email_templates.get_base_template')
    def test_build_3_day_email(self, mock_template):
        """Test building 3-day reminder email."""
        mock_template.return_value = "<html>Email content</html>"

        subject, content = _build_deadline_email(
            first_name="Bob",
            deadline_type_name="Data Furnisher Response",
            bureau=None,
            deadline_date=date.today() + timedelta(days=3),
            days_remaining=3,
            reminder_type="3_days",
            dispute_round=1
        )

        assert "3 Days" in subject

    @patch('services.deadline_service.email_templates.get_base_template')
    def test_build_7_day_email(self, mock_template):
        """Test building 7-day reminder email."""
        mock_template.return_value = "<html>Email content</html>"

        subject, content = _build_deadline_email(
            first_name="Alice",
            deadline_type_name="Reinvestigation",
            bureau="Equifax",
            deadline_date=date.today() + timedelta(days=7),
            days_remaining=7,
            reminder_type="7_days",
            dispute_round=1
        )

        assert "Upcoming Deadline" in subject


# =============================================================================
# Tests for cancel_deadline()
# =============================================================================

class TestCancelDeadline:
    """Test deadline cancellation function."""

    def test_cancel_deadline_not_found(self):
        """Test cancelling non-existent deadline."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = cancel_deadline(mock_db, deadline_id=999)

        assert result is None

    def test_cancel_deadline_success(self):
        """Test successfully cancelling a deadline."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.status = "active"
        mock_deadline.notes = None
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline

        result = cancel_deadline(mock_db, deadline_id=1)

        assert mock_deadline.status == "cancelled"
        mock_db.commit.assert_called_once()

    def test_cancel_deadline_with_reason(self):
        """Test cancelling deadline with reason."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_deadline.client_id = 1
        mock_deadline.status = "active"
        mock_deadline.notes = "Original notes"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline

        result = cancel_deadline(mock_db, deadline_id=1, reason="Account deleted from report")

        assert "[Cancelled]" in mock_deadline.notes
        assert "Account deleted from report" in mock_deadline.notes

    def test_cancel_deadline_rollback_on_error(self):
        """Test cancellation rolls back on error."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.id = 1
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_deadline
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            cancel_deadline(mock_db, deadline_id=1)

        mock_db.rollback.assert_called_once()


# =============================================================================
# Tests for get_deadline_summary()
# =============================================================================

class TestGetDeadlineSummary:
    """Test deadline summary statistics function."""

    def test_get_summary_empty(self):
        """Test summary with no deadlines."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0

        result = get_deadline_summary(mock_db)

        assert result["total_active"] == 0
        assert result["overdue"] == 0
        assert result["due_today"] == 0
        assert result["due_this_week"] == 0

    def test_get_summary_with_active_deadlines(self):
        """Test summary with active deadlines."""
        mock_db = MagicMock()

        # Create mock deadlines
        mock_overdue = MagicMock()
        mock_overdue.deadline_date = date.today() - timedelta(days=2)
        mock_overdue.deadline_type = "cra_response"
        mock_overdue.bureau = "Experian"

        mock_due_today = MagicMock()
        mock_due_today.deadline_date = date.today()
        mock_due_today.deadline_type = "cra_response"
        mock_due_today.bureau = "TransUnion"

        mock_due_in_3_days = MagicMock()
        mock_due_in_3_days.deadline_date = date.today() + timedelta(days=3)
        mock_due_in_3_days.deadline_type = "reinvestigation"
        mock_due_in_3_days.bureau = "Equifax"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_overdue, mock_due_today, mock_due_in_3_days]
        mock_query.count.side_effect = [5, 2]  # completed, cancelled

        result = get_deadline_summary(mock_db)

        assert result["total_active"] == 3
        assert result["overdue"] == 1
        assert result["due_today"] == 1
        assert result["due_this_week"] == 2  # today + 3 days

    def test_get_summary_by_type(self):
        """Test summary groups by deadline type."""
        mock_db = MagicMock()

        mock_cra1 = MagicMock()
        mock_cra1.deadline_date = date.today() + timedelta(days=5)
        mock_cra1.deadline_type = "cra_response"
        mock_cra1.bureau = "Experian"

        mock_cra2 = MagicMock()
        mock_cra2.deadline_date = date.today() + timedelta(days=10)
        mock_cra2.deadline_type = "cra_response"
        mock_cra2.bureau = "TransUnion"

        mock_reinv = MagicMock()
        mock_reinv.deadline_date = date.today() + timedelta(days=15)
        mock_reinv.deadline_type = "reinvestigation"
        mock_reinv.bureau = "Equifax"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_cra1, mock_cra2, mock_reinv]
        mock_query.count.side_effect = [0, 0]

        result = get_deadline_summary(mock_db)

        assert result["by_type"]["cra_response"] == 2
        assert result["by_type"]["reinvestigation"] == 1

    def test_get_summary_by_bureau(self):
        """Test summary groups by bureau."""
        mock_db = MagicMock()

        mock_exp = MagicMock()
        mock_exp.deadline_date = date.today() + timedelta(days=5)
        mock_exp.deadline_type = "cra_response"
        mock_exp.bureau = "Experian"

        mock_tu = MagicMock()
        mock_tu.deadline_date = date.today() + timedelta(days=10)
        mock_tu.deadline_type = "cra_response"
        mock_tu.bureau = "TransUnion"

        mock_no_bureau = MagicMock()
        mock_no_bureau.deadline_date = date.today() + timedelta(days=15)
        mock_no_bureau.deadline_type = "client_action"
        mock_no_bureau.bureau = None

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_exp, mock_tu, mock_no_bureau]
        mock_query.count.side_effect = [0, 0]

        result = get_deadline_summary(mock_db)

        assert result["by_bureau"]["Experian"] == 1
        assert result["by_bureau"]["TransUnion"] == 1
        assert None not in result["by_bureau"]  # None bureau not included

    def test_get_summary_for_specific_client(self):
        """Test summary filtered by client ID."""
        mock_db = MagicMock()

        mock_deadline = MagicMock()
        mock_deadline.deadline_date = date.today() + timedelta(days=5)
        mock_deadline.deadline_type = "cra_response"
        mock_deadline.bureau = "Experian"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_deadline]
        mock_query.count.side_effect = [1, 0]

        result = get_deadline_summary(mock_db, client_id=123)

        # Verify filter_by was called with client_id
        mock_query.filter_by.assert_called()
        assert result["total_active"] == 1


# =============================================================================
# Tests for create_cra_response_deadline()
# =============================================================================

class TestCreateCraResponseDeadline:
    """Test CRA response deadline convenience function."""

    @patch('services.deadline_service.create_deadline')
    def test_create_cra_response_deadline(self, mock_create):
        """Test creating CRA response deadline."""
        mock_deadline = MagicMock()
        mock_create.return_value = mock_deadline

        mock_db = MagicMock()
        result = create_cra_response_deadline(
            db=mock_db,
            client_id=1,
            case_id=10,
            bureau="Experian",
            dispute_round=1,
            letter_sent_date=date(2024, 1, 15)
        )

        mock_create.assert_called_once_with(
            db=mock_db,
            client_id=1,
            case_id=10,
            deadline_type="cra_response",
            bureau="Experian",
            dispute_round=1,
            start_date=date(2024, 1, 15),
            days_allowed=30
        )

    @patch('services.deadline_service.create_deadline')
    def test_create_cra_response_deadline_all_bureaus(self, mock_create):
        """Test creating CRA response deadlines for all bureaus."""
        mock_deadline = MagicMock()
        mock_create.return_value = mock_deadline

        mock_db = MagicMock()

        for bureau in ["Experian", "TransUnion", "Equifax"]:
            create_cra_response_deadline(
                db=mock_db,
                client_id=1,
                case_id=10,
                bureau=bureau,
                dispute_round=1,
                letter_sent_date=date(2024, 1, 15)
            )

        assert mock_create.call_count == 3


# =============================================================================
# Tests for create_reinvestigation_deadline()
# =============================================================================

class TestCreateReinvestigationDeadline:
    """Test reinvestigation deadline convenience function."""

    @patch('services.deadline_service.create_deadline')
    def test_create_reinvestigation_deadline(self, mock_create):
        """Test creating reinvestigation deadline."""
        mock_deadline = MagicMock()
        mock_create.return_value = mock_deadline

        mock_db = MagicMock()
        result = create_reinvestigation_deadline(
            db=mock_db,
            client_id=1,
            case_id=10,
            bureau="TransUnion",
            dispute_round=2,
            start_date=date(2024, 2, 1)
        )

        mock_create.assert_called_once_with(
            db=mock_db,
            client_id=1,
            case_id=10,
            deadline_type="reinvestigation",
            bureau="TransUnion",
            dispute_round=2,
            start_date=date(2024, 2, 1),
            days_allowed=45
        )

    @patch('services.deadline_service.create_deadline')
    def test_create_reinvestigation_uses_45_days(self, mock_create):
        """Test reinvestigation deadline uses 45-day period."""
        mock_deadline = MagicMock()
        mock_create.return_value = mock_deadline

        mock_db = MagicMock()
        create_reinvestigation_deadline(
            db=mock_db,
            client_id=1,
            case_id=10,
            bureau="Equifax",
            dispute_round=3,
            start_date=date(2024, 3, 1)
        )

        call_args = mock_create.call_args
        assert call_args.kwargs["days_allowed"] == 45


# =============================================================================
# Tests for _send_deadline_reminder()
# =============================================================================

class TestSendDeadlineReminder:
    """Test deadline reminder sending function."""

    @patch('services.deadline_service.send_email')
    def test_send_reminder_no_client_email(self, mock_send):
        """Test reminder not sent when client has no email."""
        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.deadline_type = "cra_response"
        mock_deadline.bureau = "Experian"
        mock_deadline.deadline_date = date.today() + timedelta(days=3)
        mock_deadline.dispute_round = 1

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = None  # No email
        mock_client.name = "Test Client"

        result = _send_deadline_reminder(
            mock_db, mock_deadline, mock_client, "3_days", 3
        )

        assert result is False
        mock_send.assert_not_called()

    @patch('services.deadline_service.send_email')
    @patch('services.deadline_service.email_templates.get_base_template')
    def test_send_reminder_success(self, mock_template, mock_send):
        """Test successful reminder sending."""
        mock_template.return_value = "<html>Email</html>"
        mock_send.return_value = {"success": True, "message_id": "msg123"}

        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.deadline_type = "cra_response"
        mock_deadline.bureau = "Experian"
        mock_deadline.deadline_date = date.today() + timedelta(days=3)
        mock_deadline.dispute_round = 1
        mock_deadline.id = 1

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = "test@example.com"
        mock_client.name = "Test Client"

        result = _send_deadline_reminder(
            mock_db, mock_deadline, mock_client, "3_days", 3
        )

        assert result is True
        mock_send.assert_called_once()
        mock_db.add.assert_called_once()  # EmailLog added

    @patch('services.deadline_service.send_email')
    @patch('services.deadline_service.email_templates.get_base_template')
    def test_send_reminder_failure(self, mock_template, mock_send):
        """Test failed reminder sending."""
        mock_template.return_value = "<html>Email</html>"
        mock_send.return_value = {"success": False, "error": "SMTP error"}

        mock_db = MagicMock()
        mock_deadline = MagicMock()
        mock_deadline.deadline_type = "cra_response"
        mock_deadline.bureau = "Experian"
        mock_deadline.deadline_date = date.today() + timedelta(days=3)
        mock_deadline.dispute_round = 1
        mock_deadline.id = 1

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = "test@example.com"
        mock_client.name = "Test Client"

        result = _send_deadline_reminder(
            mock_db, mock_deadline, mock_client, "3_days", 3
        )

        assert result is False
        mock_db.add.assert_called_once()  # EmailLog still added with failed status
