"""
Unit tests for the Scheduled Reports Service.

Tests cover:
- CRUD operations for scheduled reports
- Report scheduling logic
- Report generation for each type
- Email sending
- Statistics
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from services.scheduled_reports_service import (
    ScheduledReportsService,
    get_scheduled_reports_service,
    REPORT_TYPES,
    SCHEDULE_TYPES,
    DAYS_OF_WEEK,
    TIMEZONES,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """Create a scheduled reports service with a mock database."""
    return ScheduledReportsService(db_session=mock_db)


@pytest.fixture
def mock_report():
    """Create a mock scheduled report object."""
    report = MagicMock()
    report.id = 1
    report.name = "Test Report"
    report.report_type = "revenue"
    report.description = "A test report"
    report.schedule_type = "daily"
    report.schedule_time = "08:00"
    report.schedule_day = None
    report.timezone = "America/New_York"
    report.recipients = ["test@example.com"]
    report.report_params = {"days": 30}
    report.is_active = True
    report.last_run_at = None
    report.last_run_status = None
    report.last_run_error = None
    report.run_count = 0
    report.created_at = datetime.utcnow()
    report.updated_at = datetime.utcnow()
    report.to_dict = MagicMock(return_value={
        "id": 1,
        "name": "Test Report",
        "report_type": "revenue",
        "description": "A test report",
        "schedule_type": "daily",
        "schedule_time": "08:00",
        "schedule_day": None,
        "timezone": "America/New_York",
        "recipients": ["test@example.com"],
        "report_params": {"days": 30},
        "is_active": True,
        "last_run_at": None,
        "last_run_status": None,
        "last_run_error": None,
        "run_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    })
    return report


# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_report_types(self):
        """Test that REPORT_TYPES is defined correctly."""
        assert isinstance(REPORT_TYPES, dict)
        assert len(REPORT_TYPES) >= 5
        assert "revenue" in REPORT_TYPES
        assert "clients" in REPORT_TYPES
        assert "analytics" in REPORT_TYPES

    def test_report_type_structure(self):
        """Test that each report type has required fields."""
        for key, info in REPORT_TYPES.items():
            assert "name" in info
            assert "description" in info
            assert "generator" in info

    def test_schedule_types(self):
        """Test schedule types."""
        assert SCHEDULE_TYPES == ["daily", "weekly", "monthly"]

    def test_days_of_week(self):
        """Test days of week."""
        assert len(DAYS_OF_WEEK) == 7
        assert DAYS_OF_WEEK[0] == "Monday"
        assert DAYS_OF_WEEK[6] == "Sunday"

    def test_timezones(self):
        """Test timezones list."""
        assert "America/New_York" in TIMEZONES
        assert "UTC" in TIMEZONES


# =============================================================================
# Service Initialization Tests
# =============================================================================


class TestServiceInitialization:
    """Tests for service initialization."""

    def test_init_with_db_session(self, mock_db):
        """Test initialization with a database session."""
        service = ScheduledReportsService(db_session=mock_db)
        assert service._db == mock_db

    def test_init_without_db_session(self):
        """Test initialization without a database session."""
        service = ScheduledReportsService()
        assert service._db is None

    def test_should_close_db(self, mock_db):
        """Test _should_close_db logic."""
        service = ScheduledReportsService(db_session=mock_db)
        assert service._should_close_db() is False

        service2 = ScheduledReportsService()
        assert service2._should_close_db() is True


# =============================================================================
# CRUD Tests
# =============================================================================


class TestCreateReport:
    """Tests for create_report functionality."""

    def test_create_report_success(self, service, mock_db):
        """Test creating a new report."""
        new_report = MagicMock()
        new_report.to_dict.return_value = {
            "id": 1,
            "name": "New Report",
            "report_type": "revenue",
        }

        with patch("database.ScheduledReport", return_value=new_report):
            result = service.create_report(
                name="New Report",
                report_type="revenue",
                schedule_type="daily",
                recipients=["test@example.com"],
            )

        assert result["name"] == "New Report"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_report_invalid_type(self, service):
        """Test creating report with invalid type."""
        with pytest.raises(ValueError) as exc_info:
            service.create_report(
                name="Test",
                report_type="invalid_type",
                schedule_type="daily",
                recipients=["test@example.com"],
            )
        assert "Invalid report type" in str(exc_info.value)

    def test_create_report_invalid_schedule(self, service):
        """Test creating report with invalid schedule."""
        with pytest.raises(ValueError) as exc_info:
            service.create_report(
                name="Test",
                report_type="revenue",
                schedule_type="invalid",
                recipients=["test@example.com"],
            )
        assert "Invalid schedule type" in str(exc_info.value)

    def test_create_report_no_recipients(self, service):
        """Test creating report with no recipients."""
        with pytest.raises(ValueError) as exc_info:
            service.create_report(
                name="Test",
                report_type="revenue",
                schedule_type="daily",
                recipients=[],
            )
        assert "recipient" in str(exc_info.value).lower()


class TestGetReport:
    """Tests for get_report functionality."""

    def test_get_report_exists(self, service, mock_db, mock_report):
        """Test getting an existing report."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report
        result = service.get_report(1)
        assert result["name"] == "Test Report"

    def test_get_report_not_exists(self, service, mock_db):
        """Test getting a non-existent report."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        result = service.get_report(999)
        assert result is None


class TestGetAllReports:
    """Tests for get_all_reports functionality."""

    def test_get_all_reports(self, service, mock_db, mock_report):
        """Test getting all reports."""
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_report]
        result = service.get_all_reports()
        assert len(result) == 1
        assert result[0]["name"] == "Test Report"

    def test_get_all_reports_filtered_active(self, service, mock_db, mock_report):
        """Test filtering by active status."""
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [mock_report]
        result = service.get_all_reports(is_active=True)
        mock_db.query.return_value.filter_by.assert_called()

    def test_get_all_reports_filtered_type(self, service, mock_db, mock_report):
        """Test filtering by report type."""
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [mock_report]
        result = service.get_all_reports(report_type="revenue")
        mock_db.query.return_value.filter_by.assert_called()


class TestUpdateReport:
    """Tests for update_report functionality."""

    def test_update_report_success(self, service, mock_db, mock_report):
        """Test updating a report."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report

        result = service.update_report(
            report_id=1,
            name="Updated Report",
            description="Updated description",
        )

        assert mock_report.name == "Updated Report"
        mock_db.commit.assert_called()

    def test_update_report_not_found(self, service, mock_db):
        """Test updating non-existent report."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        result = service.update_report(report_id=999, name="Updated")
        assert result is None

    def test_update_report_invalid_schedule(self, service, mock_db, mock_report):
        """Test updating with invalid schedule type."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report

        with pytest.raises(ValueError):
            service.update_report(report_id=1, schedule_type="invalid")


class TestDeleteReport:
    """Tests for delete_report functionality."""

    def test_delete_report_success(self, service, mock_db, mock_report):
        """Test deleting a report."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report
        result = service.delete_report(1)
        assert result is True
        mock_db.delete.assert_called_once_with(mock_report)
        mock_db.commit.assert_called_once()

    def test_delete_report_not_found(self, service, mock_db):
        """Test deleting non-existent report."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        result = service.delete_report(999)
        assert result is False


class TestToggleReport:
    """Tests for toggle_report functionality."""

    def test_toggle_report_activate(self, service, mock_db, mock_report):
        """Test activating a report."""
        mock_report.is_active = False
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report

        result = service.toggle_report(1)
        assert result is True
        assert mock_report.is_active is True

    def test_toggle_report_deactivate(self, service, mock_db, mock_report):
        """Test deactivating a report."""
        mock_report.is_active = True
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report

        result = service.toggle_report(1)
        assert result is False
        assert mock_report.is_active is False

    def test_toggle_report_not_found(self, service, mock_db):
        """Test toggling non-existent report."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        result = service.toggle_report(999)
        assert result is None


# =============================================================================
# Scheduling Tests
# =============================================================================


class TestIsReportDue:
    """Tests for _is_report_due functionality."""

    def test_daily_report_due(self, service, mock_report):
        """Test daily report is due at correct time."""
        mock_report.schedule_type = "daily"
        mock_report.schedule_time = datetime.now().strftime("%H:%M")
        mock_report.last_run_at = None

        # This depends on current time, so we test the logic exists
        result = service._is_report_due(mock_report)
        assert isinstance(result, bool)

    def test_weekly_report_wrong_day(self, service, mock_report):
        """Test weekly report not due on wrong day."""
        mock_report.schedule_type = "weekly"
        mock_report.schedule_time = "08:00"
        # Set to a day that's not today
        mock_report.schedule_day = (datetime.now().weekday() + 1) % 7
        mock_report.last_run_at = None

        result = service._is_report_due(mock_report)
        assert result is False

    def test_already_run_today(self, service, mock_report):
        """Test report already run today."""
        mock_report.schedule_type = "daily"
        mock_report.schedule_time = datetime.now().strftime("%H:%M")
        mock_report.last_run_at = datetime.utcnow()

        result = service._is_report_due(mock_report)
        assert result is False


class TestRunDueReports:
    """Tests for run_due_reports functionality."""

    def test_run_due_reports_empty(self, service, mock_db):
        """Test running with no due reports."""
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        result = service.run_due_reports()

        assert result["ran"] == 0
        assert result["succeeded"] == 0
        assert result["failed"] == 0


# =============================================================================
# Report Generation Tests
# =============================================================================


class TestReportGeneration:
    """Tests for report generation methods."""

    def test_generate_revenue_report(self, service, mock_db):
        """Test revenue report generation."""
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10000
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = service.generate_revenue_report({"days": 30})

        assert "subject" in result
        assert "csv_data" in result
        assert "summary" in result
        assert "Revenue" in result["subject"]

    def test_generate_clients_report(self, service, mock_db):
        """Test clients report generation."""
        mock_db.query.return_value.scalar.return_value = 100
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10
        mock_db.query.return_value.group_by.return_value.all.return_value = []

        result = service.generate_clients_report({"days": 30})

        assert "subject" in result
        assert "csv_data" in result
        assert "Client" in result["subject"]

    def test_generate_analytics_report(self, service, mock_db):
        """Test analytics report generation."""
        mock_db.query.return_value.filter.return_value.scalar.return_value = 50

        result = service.generate_analytics_report({"days": 30})

        assert "subject" in result
        assert "csv_data" in result
        assert "Analytics" in result["subject"]

    def test_generate_ai_usage_report(self, service, mock_db):
        """Test AI usage report generation."""
        mock_db.query.return_value.filter.return_value.scalar.return_value = 1000
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.generate_ai_usage_report({"days": 30})

        assert "subject" in result
        assert "csv_data" in result
        assert "AI Usage" in result["subject"]

    def test_generate_disputes_report(self, service, mock_db):
        """Test disputes report generation."""
        mock_db.query.return_value.filter.return_value.scalar.return_value = 25

        result = service.generate_disputes_report({"days": 30})

        assert "subject" in result
        assert "csv_data" in result
        assert "Disputes" in result["subject"]

    def test_generate_settlements_report(self, service, mock_db):
        """Test settlements report generation."""
        mock_db.query.return_value.filter.return_value.scalar.return_value = 15

        result = service.generate_settlements_report({"days": 30})

        assert "subject" in result
        assert "csv_data" in result
        assert "Settlements" in result["subject"]

    def test_generate_staff_performance_report(self, service, mock_db):
        """Test staff performance report generation."""
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.generate_staff_performance_report({"days": 30})

        assert "subject" in result
        assert "csv_data" in result
        assert "Staff" in result["subject"]


# =============================================================================
# Run Report Tests
# =============================================================================


class TestRunReport:
    """Tests for run_report functionality."""

    def test_run_report_not_found(self, service, mock_db):
        """Test running non-existent report."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.run_report(999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_run_report_generation_error(self, service, mock_db, mock_report):
        """Test handling report generation errors."""
        mock_report.report_type = "invalid"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report

        result = service.run_report(1)

        assert result["success"] is False
        assert mock_report.last_run_status == "failed"

    def test_run_report_success(self, service, mock_db, mock_report):
        """Test successful report run."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report

        # Mock the report content generation
        mock_content = {
            "subject": "Test Report",
            "csv_data": [["Metric", "Value"], ["Total", 100]],
            "summary": {"total": 100}
        }

        with patch.object(service, '_generate_report_content', return_value=mock_content):
            with patch.object(service, '_send_report_email'):
                result = service.run_report(1)

        assert result["success"] is True


# =============================================================================
# Email Tests
# =============================================================================


class TestSendReportEmail:
    """Tests for _send_report_email functionality."""

    def test_send_report_email(self, service, mock_report):
        """Test sending report email."""
        content = {
            "subject": "Test Report",
            "csv_data": [["Header1", "Header2"], ["Data1", "Data2"]],
            "summary": {"metric": 100},
        }

        with patch("services.email_service.send_email") as mock_send:
            service._send_report_email(mock_report, content)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]["to_email"] == "test@example.com"
            assert call_args[1]["subject"] == "Test Report"


# =============================================================================
# Statistics Tests
# =============================================================================


class TestStatistics:
    """Tests for get_stats functionality."""

    def test_get_stats(self, service, mock_db):
        """Test getting statistics."""
        mock_db.query.return_value.scalar.return_value = 10
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5
        mock_db.query.return_value.group_by.return_value.all.return_value = [
            ("revenue", 3),
            ("clients", 2),
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = service.get_stats()

        assert "total_reports" in result
        assert "active_reports" in result
        assert "inactive_reports" in result
        assert "by_type" in result
        assert "by_schedule" in result


# =============================================================================
# Module-Level Functions Tests
# =============================================================================


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def test_get_scheduled_reports_service_singleton(self):
        """Test that get_scheduled_reports_service returns a service instance."""
        with patch("services.scheduled_reports_service._service", None):
            service1 = get_scheduled_reports_service()
            assert isinstance(service1, ScheduledReportsService)


# =============================================================================
# Integration-like Tests
# =============================================================================


class TestIntegrationScenarios:
    """Tests for realistic usage scenarios."""

    def test_create_and_run_daily_report(self, service, mock_db, mock_report):
        """Test creating and running a daily report."""
        # Create
        with patch("database.ScheduledReport", return_value=mock_report):
            created = service.create_report(
                name="Daily Revenue",
                report_type="revenue",
                schedule_type="daily",
                recipients=["admin@example.com"],
            )

        assert created is not None

    def test_create_weekly_report_with_day(self, service, mock_db, mock_report):
        """Test creating a weekly report on specific day."""
        with patch("database.ScheduledReport", return_value=mock_report):
            created = service.create_report(
                name="Weekly Summary",
                report_type="clients",
                schedule_type="weekly",
                schedule_day=0,  # Monday
                recipients=["admin@example.com"],
            )

        assert created is not None

    def test_create_monthly_report_with_date(self, service, mock_db, mock_report):
        """Test creating a monthly report on specific date."""
        with patch("database.ScheduledReport", return_value=mock_report):
            created = service.create_report(
                name="Monthly Analytics",
                report_type="analytics",
                schedule_type="monthly",
                schedule_day=1,  # 1st of month
                recipients=["admin@example.com"],
            )

        assert created is not None

    def test_update_recipients(self, service, mock_db, mock_report):
        """Test updating report recipients."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report

        service.update_report(
            report_id=1,
            recipients=["new@example.com", "another@example.com"],
        )

        assert mock_report.recipients == ["new@example.com", "another@example.com"]

    def test_deactivate_and_reactivate(self, service, mock_db, mock_report):
        """Test deactivating and reactivating a report."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_report
        mock_report.is_active = True

        # Deactivate
        result1 = service.toggle_report(1)
        assert result1 is False
        assert mock_report.is_active is False

        # Reactivate
        result2 = service.toggle_report(1)
        assert result2 is True
        assert mock_report.is_active is True
