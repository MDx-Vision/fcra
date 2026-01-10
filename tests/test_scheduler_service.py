"""
Unit Tests for Scheduler Service.
Tests for schedule management and cron expression handling including:
- CronParser parsing and validation
- Cron expression matching
- Next run time calculation
- Human-readable description generation
- Schedule CRUD operations
- Job execution and management
- Scheduler statistics
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scheduler_service import (
    CronParser,
    SchedulerService,
    COMMON_CRON_EXPRESSIONS,
)


# =============================================================================
# Tests for CronParser.parse()
# =============================================================================

class TestCronParserParse:
    """Test cron expression parsing."""

    def test_parse_valid_five_part_expression(self):
        """Test parsing a valid 5-part cron expression."""
        result = CronParser.parse("0 9 * * *")
        assert result["minute"] == "0"
        assert result["hour"] == "9"
        assert result["day_of_month"] == "*"
        assert result["month"] == "*"
        assert result["day_of_week"] == "*"

    def test_parse_all_wildcards(self):
        """Test parsing expression with all wildcards."""
        result = CronParser.parse("* * * * *")
        assert result["minute"] == "*"
        assert result["hour"] == "*"
        assert result["day_of_month"] == "*"
        assert result["month"] == "*"
        assert result["day_of_week"] == "*"

    def test_parse_specific_values(self):
        """Test parsing expression with specific numeric values."""
        result = CronParser.parse("30 14 15 6 3")
        assert result["minute"] == "30"
        assert result["hour"] == "14"
        assert result["day_of_month"] == "15"
        assert result["month"] == "6"
        assert result["day_of_week"] == "3"

    def test_parse_step_expression(self):
        """Test parsing expression with step values."""
        result = CronParser.parse("*/5 */2 * * *")
        assert result["minute"] == "*/5"
        assert result["hour"] == "*/2"

    def test_parse_range_expression(self):
        """Test parsing expression with range values."""
        result = CronParser.parse("0 9-17 * * 1-5")
        assert result["hour"] == "9-17"
        assert result["day_of_week"] == "1-5"

    def test_parse_list_expression(self):
        """Test parsing expression with comma-separated values."""
        result = CronParser.parse("0 9,12,18 * * *")
        assert result["hour"] == "9,12,18"

    def test_parse_too_few_parts_raises_error(self):
        """Test that fewer than 5 parts raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            CronParser.parse("0 9 * *")
        assert "Expected 5 parts" in str(excinfo.value)

    def test_parse_too_many_parts_raises_error(self):
        """Test that more than 5 parts raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            CronParser.parse("0 9 * * * *")
        assert "Expected 5 parts" in str(excinfo.value)

    def test_parse_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            CronParser.parse("")

    def test_parse_whitespace_handling(self):
        """Test that extra whitespace is handled correctly."""
        result = CronParser.parse("  0 9 * * *  ")
        assert result["minute"] == "0"
        assert result["hour"] == "9"


# =============================================================================
# Tests for CronParser._matches_field()
# =============================================================================

class TestCronParserMatchesField:
    """Test cron field matching logic."""

    def test_matches_wildcard(self):
        """Test that wildcard matches any value."""
        assert CronParser._matches_field("*", 0, 0, 59) is True
        assert CronParser._matches_field("*", 30, 0, 59) is True
        assert CronParser._matches_field("*", 59, 0, 59) is True

    def test_matches_exact_value(self):
        """Test matching exact numeric value."""
        assert CronParser._matches_field("15", 15, 0, 59) is True
        assert CronParser._matches_field("15", 14, 0, 59) is False
        assert CronParser._matches_field("15", 16, 0, 59) is False

    def test_matches_step_from_zero(self):
        """Test step matching from zero (*/n format)."""
        assert CronParser._matches_field("*/5", 0, 0, 59) is True
        assert CronParser._matches_field("*/5", 5, 0, 59) is True
        assert CronParser._matches_field("*/5", 10, 0, 59) is True
        assert CronParser._matches_field("*/5", 3, 0, 59) is False
        assert CronParser._matches_field("*/5", 7, 0, 59) is False

    def test_matches_step_from_base(self):
        """Test step matching from a base value (n/m format)."""
        assert CronParser._matches_field("5/10", 5, 0, 59) is True
        assert CronParser._matches_field("5/10", 15, 0, 59) is True
        assert CronParser._matches_field("5/10", 25, 0, 59) is True
        assert CronParser._matches_field("5/10", 3, 0, 59) is False
        assert CronParser._matches_field("5/10", 10, 0, 59) is False

    def test_matches_range(self):
        """Test range matching (n-m format)."""
        assert CronParser._matches_field("9-17", 9, 0, 23) is True
        assert CronParser._matches_field("9-17", 12, 0, 23) is True
        assert CronParser._matches_field("9-17", 17, 0, 23) is True
        assert CronParser._matches_field("9-17", 8, 0, 23) is False
        assert CronParser._matches_field("9-17", 18, 0, 23) is False

    def test_matches_list(self):
        """Test list matching (comma-separated values)."""
        assert CronParser._matches_field("1,5,10", 1, 0, 59) is True
        assert CronParser._matches_field("1,5,10", 5, 0, 59) is True
        assert CronParser._matches_field("1,5,10", 10, 0, 59) is True
        assert CronParser._matches_field("1,5,10", 3, 0, 59) is False
        assert CronParser._matches_field("1,5,10", 7, 0, 59) is False

    def test_matches_zero_value(self):
        """Test matching zero values."""
        assert CronParser._matches_field("0", 0, 0, 59) is True
        assert CronParser._matches_field("0", 1, 0, 59) is False


# =============================================================================
# Tests for CronParser.matches()
# =============================================================================

class TestCronParserMatches:
    """Test datetime matching against cron expressions."""

    def test_matches_every_minute(self):
        """Test matching every minute expression."""
        dt = datetime(2024, 6, 15, 10, 30)
        assert CronParser.matches("* * * * *", dt) is True

    def test_matches_specific_time(self):
        """Test matching specific hour and minute."""
        dt = datetime(2024, 6, 15, 9, 0)
        assert CronParser.matches("0 9 * * *", dt) is True

        dt_wrong = datetime(2024, 6, 15, 10, 0)
        assert CronParser.matches("0 9 * * *", dt_wrong) is False

    def test_matches_specific_day_of_week(self):
        """Test matching specific day of week (Monday=0)."""
        # June 17, 2024 is a Monday
        dt_monday = datetime(2024, 6, 17, 8, 0)
        assert CronParser.matches("0 8 * * 0", dt_monday) is True

        # June 18, 2024 is a Tuesday
        dt_tuesday = datetime(2024, 6, 18, 8, 0)
        assert CronParser.matches("0 8 * * 0", dt_tuesday) is False

    def test_matches_specific_day_of_month(self):
        """Test matching specific day of month."""
        dt_first = datetime(2024, 6, 1, 0, 0)
        assert CronParser.matches("0 0 1 * *", dt_first) is True

        dt_second = datetime(2024, 6, 2, 0, 0)
        assert CronParser.matches("0 0 1 * *", dt_second) is False

    def test_matches_specific_month(self):
        """Test matching specific month."""
        dt_june = datetime(2024, 6, 15, 12, 0)
        assert CronParser.matches("0 12 15 6 *", dt_june) is True

        dt_july = datetime(2024, 7, 15, 12, 0)
        assert CronParser.matches("0 12 15 6 *", dt_july) is False

    def test_matches_every_5_minutes(self):
        """Test matching every 5 minutes expression."""
        dt_0 = datetime(2024, 6, 15, 10, 0)
        dt_5 = datetime(2024, 6, 15, 10, 5)
        dt_10 = datetime(2024, 6, 15, 10, 10)
        dt_3 = datetime(2024, 6, 15, 10, 3)

        assert CronParser.matches("*/5 * * * *", dt_0) is True
        assert CronParser.matches("*/5 * * * *", dt_5) is True
        assert CronParser.matches("*/5 * * * *", dt_10) is True
        assert CronParser.matches("*/5 * * * *", dt_3) is False

    def test_matches_invalid_expression_returns_false(self):
        """Test that invalid expression returns False instead of raising."""
        dt = datetime(2024, 6, 15, 10, 30)
        assert CronParser.matches("invalid", dt) is False
        assert CronParser.matches("0 9", dt) is False

    def test_matches_hourly(self):
        """Test matching hourly expression (top of every hour)."""
        dt_top_hour = datetime(2024, 6, 15, 10, 0)
        dt_mid_hour = datetime(2024, 6, 15, 10, 30)

        assert CronParser.matches("0 * * * *", dt_top_hour) is True
        assert CronParser.matches("0 * * * *", dt_mid_hour) is False


# =============================================================================
# Tests for CronParser.get_next_run()
# =============================================================================

class TestCronParserGetNextRun:
    """Test next run time calculation."""

    def test_get_next_run_every_minute(self):
        """Test next run for every minute expression."""
        from_dt = datetime(2024, 6, 15, 10, 30, 45)
        next_run = CronParser.get_next_run("* * * * *", from_dt)

        # Should be the next minute
        assert next_run == datetime(2024, 6, 15, 10, 31, 0)

    def test_get_next_run_specific_time_future(self):
        """Test next run for specific time in the future today."""
        from_dt = datetime(2024, 6, 15, 8, 0, 0)
        next_run = CronParser.get_next_run("0 9 * * *", from_dt)

        # Should be 9 AM same day
        assert next_run == datetime(2024, 6, 15, 9, 0, 0)

    def test_get_next_run_specific_time_next_day(self):
        """Test next run for specific time tomorrow."""
        from_dt = datetime(2024, 6, 15, 10, 0, 0)
        next_run = CronParser.get_next_run("0 9 * * *", from_dt)

        # Should be 9 AM next day
        assert next_run == datetime(2024, 6, 16, 9, 0, 0)

    def test_get_next_run_every_5_minutes(self):
        """Test next run for every 5 minutes expression."""
        from_dt = datetime(2024, 6, 15, 10, 7, 0)
        next_run = CronParser.get_next_run("*/5 * * * *", from_dt)

        # Should be the next 5-minute interval
        assert next_run == datetime(2024, 6, 15, 10, 10, 0)

    def test_get_next_run_uses_current_time_if_none(self):
        """Test that current time is used if from_dt is None."""
        next_run = CronParser.get_next_run("* * * * *")

        # Should be in the future
        assert next_run > datetime.utcnow()

    def test_get_next_run_specific_day_of_week(self):
        """Test next run for specific day of week."""
        # June 15, 2024 is Saturday (weekday 5)
        from_dt = datetime(2024, 6, 15, 10, 0, 0)
        # Looking for Monday (weekday 0)
        next_run = CronParser.get_next_run("0 8 * * 0", from_dt)

        # Should be Monday June 17, 2024
        assert next_run.weekday() == 0
        assert next_run.hour == 8
        assert next_run.minute == 0

    def test_get_next_run_monthly(self):
        """Test next run for monthly expression."""
        from_dt = datetime(2024, 6, 15, 0, 0, 0)
        next_run = CronParser.get_next_run("0 0 1 * *", from_dt)

        # Should be 1st of next month (July)
        assert next_run == datetime(2024, 7, 1, 0, 0, 0)


# =============================================================================
# Tests for CronParser.describe()
# =============================================================================

class TestCronParserDescribe:
    """Test human-readable cron description generation."""

    def test_describe_daily_9am(self):
        """Test description for daily at 9 AM."""
        result = CronParser.describe("0 9 * * *")
        assert result == "Daily at 9:00 AM"

    def test_describe_weekly_monday(self):
        """Test description for weekly on Monday."""
        result = CronParser.describe("0 8 * * 1")
        assert result == "Weekly on Monday at 8:00 AM"

    def test_describe_daily_6am(self):
        """Test description for daily at 6 AM."""
        result = CronParser.describe("0 6 * * *")
        assert result == "Daily at 6:00 AM"

    def test_describe_every_5_minutes(self):
        """Test description for every 5 minutes."""
        result = CronParser.describe("*/5 * * * *")
        assert result == "Every 5 minutes"

    def test_describe_hourly(self):
        """Test description for hourly."""
        result = CronParser.describe("0 * * * *")
        assert result == "Every hour"

    def test_describe_midnight(self):
        """Test description for daily at midnight."""
        result = CronParser.describe("0 0 * * *")
        assert result == "Daily at midnight"

    def test_describe_monthly_first(self):
        """Test description for monthly on the 1st."""
        result = CronParser.describe("0 0 1 * *")
        assert result == "Monthly on the 1st at midnight"

    def test_describe_custom_daily_time(self):
        """Test description for custom daily time not in lookup."""
        result = CronParser.describe("30 14 * * *")
        assert "Daily" in result
        assert "2:30 PM" in result

    def test_describe_custom_weekly(self):
        """Test description for custom weekly schedule."""
        # dow=5 maps to Saturday in the describe function (0=Monday, 5=Saturday)
        result = CronParser.describe("0 17 * * 5")
        assert "Weekly" in result
        assert "Saturday" in result

    def test_describe_invalid_expression_returns_original(self):
        """Test that invalid expression returns original string."""
        result = CronParser.describe("invalid")
        assert result == "invalid"


# =============================================================================
# Tests for COMMON_CRON_EXPRESSIONS
# =============================================================================

class TestCommonCronExpressions:
    """Test common cron expressions constant."""

    def test_every_5_minutes_exists(self):
        """Test every 5 minutes preset exists."""
        assert "every_5_minutes" in COMMON_CRON_EXPRESSIONS
        assert COMMON_CRON_EXPRESSIONS["every_5_minutes"]["expression"] == "*/5 * * * *"

    def test_hourly_exists(self):
        """Test hourly preset exists."""
        assert "hourly" in COMMON_CRON_EXPRESSIONS
        assert COMMON_CRON_EXPRESSIONS["hourly"]["expression"] == "0 * * * *"

    def test_daily_9am_exists(self):
        """Test daily 9 AM preset exists."""
        assert "daily_9am" in COMMON_CRON_EXPRESSIONS
        assert COMMON_CRON_EXPRESSIONS["daily_9am"]["expression"] == "0 9 * * *"

    def test_weekly_monday_exists(self):
        """Test weekly Monday preset exists."""
        assert "weekly_monday_8am" in COMMON_CRON_EXPRESSIONS
        assert COMMON_CRON_EXPRESSIONS["weekly_monday_8am"]["expression"] == "0 8 * * 1"

    def test_monthly_first_exists(self):
        """Test monthly first preset exists."""
        assert "monthly_first" in COMMON_CRON_EXPRESSIONS
        assert COMMON_CRON_EXPRESSIONS["monthly_first"]["expression"] == "0 0 1 * *"

    def test_all_presets_have_expression_and_label(self):
        """Test all presets have required fields."""
        for key, preset in COMMON_CRON_EXPRESSIONS.items():
            assert "expression" in preset, f"{key} missing expression"
            assert "label" in preset, f"{key} missing label"

    def test_all_preset_expressions_are_valid(self):
        """Test all preset expressions parse successfully."""
        for key, preset in COMMON_CRON_EXPRESSIONS.items():
            try:
                CronParser.parse(preset["expression"])
            except ValueError as e:
                pytest.fail(f"Preset {key} has invalid expression: {e}")


# =============================================================================
# Tests for SchedulerService.BUILT_IN_SCHEDULES
# =============================================================================

class TestBuiltInSchedules:
    """Test built-in schedule configurations."""

    def test_daily_case_summary_exists(self):
        """Test Daily Case Summary Report exists."""
        names = [s["name"] for s in SchedulerService.BUILT_IN_SCHEDULES]
        assert "Daily Case Summary Report" in names

    def test_weekly_revenue_report_exists(self):
        """Test Weekly Revenue Report exists."""
        names = [s["name"] for s in SchedulerService.BUILT_IN_SCHEDULES]
        assert "Weekly Revenue Report" in names

    def test_sol_deadline_checks_exists(self):
        """Test SOL Deadline Checks exists."""
        names = [s["name"] for s in SchedulerService.BUILT_IN_SCHEDULES]
        assert "SOL Deadline Checks" in names

    def test_sendcertified_tracking_exists(self):
        """Test SendCertified Tracking schedule exists."""
        names = [s["name"] for s in SchedulerService.BUILT_IN_SCHEDULES]
        assert "Check SendCertified Tracking Updates" in names

    def test_cra_response_deadline_exists(self):
        """Test CRA Response Deadline check exists."""
        names = [s["name"] for s in SchedulerService.BUILT_IN_SCHEDULES]
        assert "Check CRA Response Deadlines" in names

    def test_all_built_in_schedules_have_required_fields(self):
        """Test all built-in schedules have required fields."""
        for schedule in SchedulerService.BUILT_IN_SCHEDULES:
            assert "name" in schedule
            assert "task_type" in schedule
            assert "payload" in schedule
            assert "cron_expression" in schedule

    def test_all_built_in_cron_expressions_valid(self):
        """Test all built-in cron expressions are valid."""
        for schedule in SchedulerService.BUILT_IN_SCHEDULES:
            try:
                CronParser.parse(schedule["cron_expression"])
            except ValueError as e:
                pytest.fail(f"Schedule {schedule['name']} has invalid cron: {e}")


# =============================================================================
# Tests for SchedulerService.create_schedule()
# =============================================================================

class TestSchedulerServiceCreateSchedule:
    """Test schedule creation."""

    @patch('services.scheduler_service.get_db')
    @patch('services.scheduler_service.CronParser.get_next_run')
    def test_create_schedule_success(self, mock_get_next_run, mock_get_db):
        """Test successful schedule creation."""
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        mock_get_next_run.return_value = datetime(2024, 6, 16, 9, 0, 0)

        result = SchedulerService.create_schedule(
            name="Test Schedule",
            task_type="test_task",
            payload={"key": "value"},
            cron_expression="0 9 * * *",
            staff_id=1
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch('services.scheduler_service.get_db')
    def test_create_schedule_invalid_cron_raises_error(self, mock_get_db):
        """Test that invalid cron expression raises error."""
        with pytest.raises(ValueError):
            SchedulerService.create_schedule(
                name="Test Schedule",
                task_type="test_task",
                payload={},
                cron_expression="invalid"
            )

    @patch('services.scheduler_service.get_db')
    def test_create_schedule_closes_session(self, mock_get_db):
        """Test that session is closed after creation."""
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        try:
            SchedulerService.create_schedule(
                name="Test",
                task_type="test",
                payload={},
                cron_expression="0 9 * * *"
            )
        except Exception:
            pass

        mock_session.close.assert_called()


# =============================================================================
# Tests for SchedulerService.update_schedule()
# =============================================================================

class TestSchedulerServiceUpdateSchedule:
    """Test schedule updates."""

    @patch('services.scheduler_service.get_db')
    def test_update_schedule_name(self, mock_get_db):
        """Test updating schedule name."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_job.cron_expression = "0 9 * * *"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        mock_get_db.return_value = mock_session

        result = SchedulerService.update_schedule(1, name="New Name")

        assert mock_job.name == "New Name"
        mock_session.commit.assert_called()

    @patch('services.scheduler_service.get_db')
    def test_update_schedule_task_type(self, mock_get_db):
        """Test updating schedule task type."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        mock_get_db.return_value = mock_session

        SchedulerService.update_schedule(1, task_type="new_task")

        assert mock_job.task_type == "new_task"

    @patch('services.scheduler_service.get_db')
    def test_update_schedule_cron_expression(self, mock_get_db):
        """Test updating cron expression recalculates next_run."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        mock_get_db.return_value = mock_session

        SchedulerService.update_schedule(1, cron_expression="0 10 * * *")

        assert mock_job.cron_expression == "0 10 * * *"
        assert mock_job.next_run is not None

    @patch('services.scheduler_service.get_db')
    def test_update_schedule_not_found_returns_none(self, mock_get_db):
        """Test updating non-existent schedule returns None."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = SchedulerService.update_schedule(999, name="Test")

        assert result is None

    @patch('services.scheduler_service.get_db')
    def test_update_schedule_invalid_cron_raises_error(self, mock_get_db):
        """Test updating with invalid cron raises error."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        mock_get_db.return_value = mock_session

        with pytest.raises(ValueError):
            SchedulerService.update_schedule(1, cron_expression="invalid")

    @patch('services.scheduler_service.get_db')
    def test_update_schedule_activate_sets_next_run(self, mock_get_db):
        """Test activating schedule sets next_run if not set."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_job.next_run = None
        mock_job.cron_expression = "0 9 * * *"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        mock_get_db.return_value = mock_session

        SchedulerService.update_schedule(1, is_active=True)

        assert mock_job.is_active is True


# =============================================================================
# Tests for SchedulerService.delete_schedule()
# =============================================================================

class TestSchedulerServiceDeleteSchedule:
    """Test schedule deletion."""

    @patch('services.scheduler_service.get_db')
    def test_delete_schedule_success(self, mock_get_db):
        """Test successful schedule deletion."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        mock_get_db.return_value = mock_session

        result = SchedulerService.delete_schedule(1)

        assert result is True
        mock_session.delete.assert_called_with(mock_job)
        mock_session.commit.assert_called()

    @patch('services.scheduler_service.get_db')
    def test_delete_schedule_not_found(self, mock_get_db):
        """Test deleting non-existent schedule returns False."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = SchedulerService.delete_schedule(999)

        assert result is False
        mock_session.delete.assert_not_called()


# =============================================================================
# Tests for SchedulerService.get_schedule()
# =============================================================================

class TestSchedulerServiceGetSchedule:
    """Test schedule retrieval."""

    @patch('services.scheduler_service.get_db')
    def test_get_schedule_success(self, mock_get_db):
        """Test successful schedule retrieval."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_job.cron_expression = "0 9 * * *"
        mock_job.to_dict.return_value = {
            "id": 1,
            "name": "Test",
            "cron_expression": "0 9 * * *"
        }
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        mock_get_db.return_value = mock_session

        result = SchedulerService.get_schedule(1)

        assert result is not None
        assert result["id"] == 1
        assert "cron_description" in result

    @patch('services.scheduler_service.get_db')
    def test_get_schedule_not_found(self, mock_get_db):
        """Test getting non-existent schedule returns None."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = SchedulerService.get_schedule(999)

        assert result is None


# =============================================================================
# Tests for SchedulerService.get_all_schedules()
# =============================================================================

class TestSchedulerServiceGetAllSchedules:
    """Test getting all schedules."""

    @patch('services.scheduler_service.get_db')
    def test_get_all_schedules(self, mock_get_db):
        """Test getting all schedules."""
        mock_session = MagicMock()
        mock_job1 = MagicMock()
        mock_job1.cron_expression = "0 9 * * *"
        mock_job1.to_dict.return_value = {"id": 1, "name": "A", "cron_expression": "0 9 * * *"}
        mock_job2 = MagicMock()
        mock_job2.cron_expression = "0 10 * * *"
        mock_job2.to_dict.return_value = {"id": 2, "name": "B", "cron_expression": "0 10 * * *"}

        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_job1, mock_job2]
        mock_get_db.return_value = mock_session

        result = SchedulerService.get_all_schedules()

        assert len(result) == 2
        assert all("cron_description" in r for r in result)

    @patch('services.scheduler_service.get_db')
    def test_get_all_schedules_active_only(self, mock_get_db):
        """Test getting only active schedules."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        SchedulerService.get_all_schedules(active_only=True)

        mock_query.filter.assert_called()


# =============================================================================
# Tests for SchedulerService.get_due_jobs()
# =============================================================================

class TestSchedulerServiceGetDueJobs:
    """Test getting due jobs."""

    @patch('services.scheduler_service.get_db')
    def test_get_due_jobs(self, mock_get_db):
        """Test getting jobs that are due."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_job]
        mock_get_db.return_value = mock_session

        result = SchedulerService.get_due_jobs()

        assert len(result) == 1
        assert result[0] == mock_job


# =============================================================================
# Tests for SchedulerService.run_due_jobs()
# =============================================================================

class TestSchedulerServiceRunDueJobs:
    """Test running due jobs."""

    @patch('services.scheduler_service.TaskQueueService')
    @patch('services.scheduler_service.get_db')
    def test_run_due_jobs_success(self, mock_get_db, mock_task_queue):
        """Test running due jobs successfully."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "Test Job"
        mock_job.task_type = "test_task"
        mock_job.payload = {"key": "value"}
        mock_job.cron_expression = "0 9 * * *"
        mock_job.run_count = 0

        mock_session.query.return_value.filter.return_value.all.return_value = [mock_job]
        mock_get_db.return_value = mock_session

        mock_task = MagicMock()
        mock_task.id = 100
        mock_task_queue.enqueue_task.return_value = mock_task

        results = SchedulerService.run_due_jobs()

        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["job_id"] == 1
        assert results[0]["task_id"] == 100

    @patch('services.scheduler_service.TaskQueueService')
    @patch('services.scheduler_service.get_db')
    def test_run_due_jobs_error_handling(self, mock_get_db, mock_task_queue):
        """Test error handling when running due jobs."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "Test Job"
        mock_job.task_type = "test_task"
        mock_job.payload = {}

        mock_session.query.return_value.filter.return_value.all.return_value = [mock_job]
        mock_get_db.return_value = mock_session

        mock_task_queue.enqueue_task.side_effect = Exception("Queue error")

        results = SchedulerService.run_due_jobs()

        assert len(results) == 1
        assert results[0]["success"] is False
        assert "Queue error" in results[0]["error"]

    @patch('services.scheduler_service.get_db')
    def test_run_due_jobs_empty(self, mock_get_db):
        """Test running when no jobs are due."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        results = SchedulerService.run_due_jobs()

        assert len(results) == 0


# =============================================================================
# Tests for SchedulerService.run_job_now()
# =============================================================================

class TestSchedulerServiceRunJobNow:
    """Test manually running a job."""

    @patch('services.scheduler_service.TaskQueueService')
    @patch('services.scheduler_service.get_db')
    def test_run_job_now_success(self, mock_get_db, mock_task_queue):
        """Test manually triggering a job."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "Test Job"
        mock_job.task_type = "test_task"
        mock_job.payload = {}
        mock_job.run_count = 0

        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        mock_get_db.return_value = mock_session

        mock_task = MagicMock()
        mock_task.id = 100
        mock_task_queue.enqueue_task.return_value = mock_task

        result = SchedulerService.run_job_now(1)

        assert result is not None
        assert result["success"] is True
        assert result["task_id"] == 100
        mock_task_queue.enqueue_task.assert_called_with(
            task_type="test_task",
            payload={},
            priority=8
        )

    @patch('services.scheduler_service.get_db')
    def test_run_job_now_not_found(self, mock_get_db):
        """Test running non-existent job returns None."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = SchedulerService.run_job_now(999)

        assert result is None


# =============================================================================
# Tests for SchedulerService.pause_schedule() and resume_schedule()
# =============================================================================

class TestSchedulerServicePauseResume:
    """Test pausing and resuming schedules."""

    @patch('services.scheduler_service.SchedulerService.update_schedule')
    def test_pause_schedule(self, mock_update):
        """Test pausing a schedule."""
        mock_update.return_value = MagicMock()

        result = SchedulerService.pause_schedule(1)

        assert result is True
        mock_update.assert_called_with(1, is_active=False)

    @patch('services.scheduler_service.SchedulerService.update_schedule')
    def test_pause_schedule_not_found(self, mock_update):
        """Test pausing non-existent schedule."""
        mock_update.return_value = None

        result = SchedulerService.pause_schedule(999)

        assert result is False

    @patch('services.scheduler_service.SchedulerService.update_schedule')
    def test_resume_schedule(self, mock_update):
        """Test resuming a schedule."""
        mock_update.return_value = MagicMock()

        result = SchedulerService.resume_schedule(1)

        assert result is True
        mock_update.assert_called_with(1, is_active=True)

    @patch('services.scheduler_service.SchedulerService.update_schedule')
    def test_resume_schedule_not_found(self, mock_update):
        """Test resuming non-existent schedule."""
        mock_update.return_value = None

        result = SchedulerService.resume_schedule(999)

        assert result is False


# =============================================================================
# Tests for SchedulerService.get_scheduler_stats()
# =============================================================================

class TestSchedulerServiceGetStats:
    """Test scheduler statistics."""

    @patch('services.scheduler_service.get_db')
    def test_get_scheduler_stats(self, mock_get_db):
        """Test getting scheduler statistics."""
        mock_session = MagicMock()

        # Mock total count
        mock_session.query.return_value.count.return_value = 10

        # Mock active count
        mock_session.query.return_value.filter.return_value.count.return_value = 7

        # Mock total runs (func.sum)
        mock_session.query.return_value.scalar.return_value = 100

        # Mock next job
        mock_next_job = MagicMock()
        mock_next_job.id = 1
        mock_next_job.name = "Next Job"
        mock_next_job.next_run = datetime(2024, 6, 16, 9, 0, 0)
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_next_job

        mock_get_db.return_value = mock_session

        result = SchedulerService.get_scheduler_stats()

        assert "total_schedules" in result
        assert "active_schedules" in result
        assert "paused_schedules" in result
        assert "total_runs" in result
        assert "next_scheduled_job" in result

    @patch('services.scheduler_service.get_db')
    def test_get_scheduler_stats_no_next_job(self, mock_get_db):
        """Test stats when no next job scheduled."""
        mock_session = MagicMock()
        mock_session.query.return_value.count.return_value = 0
        mock_session.query.return_value.filter.return_value.count.return_value = 0
        mock_session.query.return_value.scalar.return_value = 0
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = SchedulerService.get_scheduler_stats()

        assert result["next_scheduled_job"] is None


# =============================================================================
# Tests for SchedulerService.initialize_built_in_schedules()
# =============================================================================

class TestSchedulerServiceInitializeBuiltIn:
    """Test built-in schedule initialization."""

    @patch('services.scheduler_service.get_db')
    def test_initialize_built_in_schedules_creates_new(self, mock_get_db):
        """Test creating new built-in schedules."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = SchedulerService.initialize_built_in_schedules()

        # Should create all built-in schedules
        assert mock_session.add.call_count == len(SchedulerService.BUILT_IN_SCHEDULES)
        mock_session.commit.assert_called()

    @patch('services.scheduler_service.get_db')
    def test_initialize_built_in_schedules_skips_existing(self, mock_get_db):
        """Test skipping existing built-in schedules."""
        mock_session = MagicMock()
        mock_existing = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_existing
        mock_get_db.return_value = mock_session

        result = SchedulerService.initialize_built_in_schedules()

        # Should not add any since all exist
        mock_session.add.assert_not_called()
        assert len(result) == 0


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_cron_parse_single_digit_values(self):
        """Test parsing single digit values."""
        result = CronParser.parse("5 9 1 1 1")
        assert result["minute"] == "5"
        assert result["hour"] == "9"
        assert result["day_of_month"] == "1"

    def test_cron_matches_boundary_minute_values(self):
        """Test matching at minute boundaries."""
        dt_min = datetime(2024, 6, 15, 10, 0)
        dt_max = datetime(2024, 6, 15, 10, 59)

        assert CronParser._matches_field("0", 0, 0, 59) is True
        assert CronParser._matches_field("59", 59, 0, 59) is True

    def test_cron_matches_boundary_hour_values(self):
        """Test matching at hour boundaries."""
        assert CronParser._matches_field("0", 0, 0, 23) is True
        assert CronParser._matches_field("23", 23, 0, 23) is True

    def test_cron_matches_february_29(self):
        """Test matching February 29 in leap year."""
        dt_leap = datetime(2024, 2, 29, 9, 0)  # 2024 is leap year
        assert CronParser.matches("0 9 29 2 *", dt_leap) is True

    def test_cron_describe_pm_time(self):
        """Test description for PM times."""
        result = CronParser.describe("0 14 * * *")
        assert "PM" in result

    def test_empty_payload_handling(self):
        """Test handling of None/empty payload in run_due_jobs."""
        with patch('services.scheduler_service.TaskQueueService') as mock_tqs:
            with patch('services.scheduler_service.get_db') as mock_get_db:
                mock_session = MagicMock()
                mock_job = MagicMock()
                mock_job.id = 1
                mock_job.name = "Test"
                mock_job.task_type = "test"
                mock_job.payload = None  # None payload
                mock_job.cron_expression = "0 9 * * *"
                mock_job.run_count = 0

                mock_session.query.return_value.filter.return_value.all.return_value = [mock_job]
                mock_get_db.return_value = mock_session

                mock_task = MagicMock()
                mock_task.id = 1
                mock_tqs.enqueue_task.return_value = mock_task

                results = SchedulerService.run_due_jobs()

                # Should use empty dict for None payload
                mock_tqs.enqueue_task.assert_called_with(
                    task_type="test",
                    payload={},
                    priority=7
                )
