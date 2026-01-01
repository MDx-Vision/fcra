"""
Tests for DeadlineCheckerService

Tests the deadline checking functionality that runs as a scheduled job
to notify clients about approaching and overdue deadlines.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from services.deadline_checker_service import DeadlineCheckerService


class TestDeadlineCheckerService:
    """Test the DeadlineCheckerService class"""

    def test_deadline_config_exists(self):
        """Test that deadline configuration is defined"""
        config = DeadlineCheckerService.DEADLINE_CONFIG
        assert "secondary_bureau" in config
        assert "cra_response" in config
        assert "sol" in config

    def test_secondary_bureau_config(self):
        """Test secondary bureau deadline configuration"""
        config = DeadlineCheckerService.DEADLINE_CONFIG["secondary_bureau"]
        assert config["expected_days"] == 30
        assert config["warning_days"] == 25
        assert config["overdue_days"] == 31

    def test_cra_response_config(self):
        """Test CRA response deadline configuration"""
        config = DeadlineCheckerService.DEADLINE_CONFIG["cra_response"]
        assert config["expected_days"] == 30
        assert config["warning_days"] == 25
        assert config["overdue_days"] == 35

    def test_sol_config(self):
        """Test SOL deadline configuration"""
        config = DeadlineCheckerService.DEADLINE_CONFIG["sol"]
        assert config["warning_days"] == 30


class TestCheckAllDeadlines:
    """Test the check_all_deadlines method"""

    @patch.object(DeadlineCheckerService, 'check_secondary_bureau_deadlines')
    @patch.object(DeadlineCheckerService, 'check_cra_response_deadlines')
    @patch.object(DeadlineCheckerService, 'check_sol_deadlines')
    def test_check_all_deadlines_calls_all_checkers(
        self, mock_sol, mock_cra, mock_bureau
    ):
        """Test that check_all_deadlines calls all deadline checkers"""
        mock_bureau.return_value = {"warnings_sent": 2, "overdue_alerts": 1}
        mock_cra.return_value = {"warnings_sent": 1, "overdue_alerts": 0}
        mock_sol.return_value = {"warnings_sent": 1}

        result = DeadlineCheckerService.check_all_deadlines()

        mock_bureau.assert_called_once()
        mock_cra.assert_called_once()
        mock_sol.assert_called_once()

    @patch.object(DeadlineCheckerService, 'check_secondary_bureau_deadlines')
    @patch.object(DeadlineCheckerService, 'check_cra_response_deadlines')
    @patch.object(DeadlineCheckerService, 'check_sol_deadlines')
    def test_check_all_deadlines_calculates_totals(
        self, mock_sol, mock_cra, mock_bureau
    ):
        """Test that check_all_deadlines calculates correct totals"""
        mock_bureau.return_value = {"warnings_sent": 2, "overdue_alerts": 1}
        mock_cra.return_value = {"warnings_sent": 1, "overdue_alerts": 2}
        mock_sol.return_value = {"warnings_sent": 3}

        result = DeadlineCheckerService.check_all_deadlines()

        assert result["total_warnings"] == 6  # 2 + 1 + 3
        assert result["total_overdue"] == 3  # 1 + 2

    @patch.object(DeadlineCheckerService, 'check_secondary_bureau_deadlines')
    @patch.object(DeadlineCheckerService, 'check_cra_response_deadlines')
    @patch.object(DeadlineCheckerService, 'check_sol_deadlines')
    def test_check_all_deadlines_includes_timestamp(
        self, mock_sol, mock_cra, mock_bureau
    ):
        """Test that check_all_deadlines includes a timestamp"""
        mock_bureau.return_value = {"warnings_sent": 0, "overdue_alerts": 0}
        mock_cra.return_value = {"warnings_sent": 0, "overdue_alerts": 0}
        mock_sol.return_value = {"warnings_sent": 0}

        result = DeadlineCheckerService.check_all_deadlines()

        assert "checked_at" in result
        # Should be valid ISO format
        datetime.fromisoformat(result["checked_at"])


class TestCheckSecondaryBureauDeadlines:
    """Test the check_secondary_bureau_deadlines method"""

    @patch('services.deadline_checker_service.get_db')
    def test_returns_expected_structure(self, mock_get_db):
        """Test that the method returns expected structure"""
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = DeadlineCheckerService.check_secondary_bureau_deadlines()

        assert "checked" in result
        assert "warnings_sent" in result
        assert "overdue_alerts" in result
        assert "clients_notified" in result

    @patch('services.deadline_checker_service.get_db')
    def test_no_pending_freezes_returns_zeros(self, mock_get_db):
        """Test that no pending freezes returns zero counts"""
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = DeadlineCheckerService.check_secondary_bureau_deadlines()

        assert result["checked"] == 0
        assert result["warnings_sent"] == 0
        assert result["overdue_alerts"] == 0


class TestCheckCRAResponseDeadlines:
    """Test the check_cra_response_deadlines method"""

    @patch('services.deadline_checker_service.get_db')
    def test_returns_expected_structure(self, mock_get_db):
        """Test that the method returns expected structure"""
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = DeadlineCheckerService.check_cra_response_deadlines()

        assert "checked" in result
        assert "warnings_sent" in result
        assert "overdue_alerts" in result
        assert "clients_notified" in result


class TestCheckSOLDeadlines:
    """Test the check_sol_deadlines method"""

    @patch('services.deadline_checker_service.get_db')
    def test_returns_expected_structure(self, mock_get_db):
        """Test that the method returns expected structure"""
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = DeadlineCheckerService.check_sol_deadlines()

        assert "checked" in result
        assert "warnings_sent" in result
        assert "clients_notified" in result


class TestFireDeadlineTrigger:
    """Test the _fire_deadline_trigger method"""

    @patch('services.workflow_triggers_service.WorkflowTriggersService.evaluate_triggers')
    def test_fire_trigger_with_valid_client(self, mock_evaluate_triggers):
        """Test firing trigger with valid client"""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = "Test Client"
        mock_client.email = "test@example.com"
        mock_client.phone = "5551234567"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client

        mock_evaluate_triggers.return_value = [{"trigger_id": 1}]

        result = DeadlineCheckerService._fire_deadline_trigger(
            session=mock_session,
            client_id=1,
            deadline_type="secondary_bureau_due_soon",
            deadline_date=datetime.utcnow(),
            days_remaining=5,
            extra_data={"bureau_name": "Innovis"}
        )

        assert result is True
        mock_evaluate_triggers.assert_called_once()

    def test_fire_trigger_with_invalid_client(self):
        """Test firing trigger with invalid client returns False"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = DeadlineCheckerService._fire_deadline_trigger(
            session=mock_session,
            client_id=999,
            deadline_type="secondary_bureau_due_soon",
            deadline_date=datetime.utcnow(),
            days_remaining=5
        )

        assert result is False


class TestGetDeadlineSummary:
    """Test the get_deadline_summary method"""

    @patch('services.deadline_checker_service.get_db')
    def test_returns_expected_structure(self, mock_get_db):
        """Test that the method returns expected structure"""
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = DeadlineCheckerService.get_deadline_summary(client_id=1)

        assert "client_id" in result
        assert "secondary_bureaus" in result
        assert "case_deadlines" in result
        assert "total_pending" in result
        assert "total_overdue" in result

    @patch('services.deadline_checker_service.get_db')
    def test_calculates_days_remaining(self, mock_get_db):
        """Test that days remaining is calculated correctly"""
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock a freeze with a specific date
        mock_freeze = MagicMock()
        mock_freeze.bureau_name = "Innovis"
        mock_freeze.status = "PENDING"
        mock_freeze.freeze_requested_at = datetime.utcnow() - timedelta(days=20)
        mock_freeze.client_id = 1

        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_freeze],  # First call for freezes
            [],  # Second call for case deadlines
        ]

        result = DeadlineCheckerService.get_deadline_summary(client_id=1)

        assert len(result["secondary_bureaus"]) == 1
        bureau = result["secondary_bureaus"][0]
        assert bureau["bureau_name"] == "Innovis"
        assert bureau["days_remaining"] == 10  # 30 - 20 = 10
        assert bureau["is_overdue"] is False


class TestTaskHandlers:
    """Test the registered task handlers"""

    @patch.object(DeadlineCheckerService, 'check_all_deadlines')
    def test_handle_check_deadlines(self, mock_check):
        """Test the check_deadlines task handler"""
        from services.deadline_checker_service import handle_check_deadlines

        mock_check.return_value = {"total_warnings": 5}

        result = handle_check_deadlines({})

        mock_check.assert_called_once()
        assert result["total_warnings"] == 5

    @patch.object(DeadlineCheckerService, 'check_secondary_bureau_deadlines')
    def test_handle_check_secondary_bureau_deadlines(self, mock_check):
        """Test the check_secondary_bureau_deadlines task handler"""
        from services.deadline_checker_service import handle_check_secondary_bureau_deadlines

        mock_check.return_value = {"warnings_sent": 3}

        result = handle_check_secondary_bureau_deadlines({})

        mock_check.assert_called_once()
        assert result["warnings_sent"] == 3

    @patch.object(DeadlineCheckerService, 'check_cra_response_deadlines')
    def test_handle_check_cra_response_deadlines(self, mock_check):
        """Test the check_cra_response_deadlines task handler"""
        from services.deadline_checker_service import handle_check_cra_response_deadlines

        mock_check.return_value = {"overdue_alerts": 2}

        result = handle_check_cra_response_deadlines({})

        mock_check.assert_called_once()
        assert result["overdue_alerts"] == 2


class TestDeadlineLogic:
    """Test the deadline calculation logic"""

    def test_warning_at_25_days(self):
        """Test that warning is triggered at 25 days"""
        config = DeadlineCheckerService.DEADLINE_CONFIG["secondary_bureau"]
        days_since = 25

        # At 25 days, should trigger warning (not overdue)
        is_warning = days_since >= config["warning_days"] and days_since < config["overdue_days"]
        is_overdue = days_since >= config["overdue_days"]

        assert is_warning is True
        assert is_overdue is False

    def test_overdue_at_31_days(self):
        """Test that overdue is triggered at 31 days"""
        config = DeadlineCheckerService.DEADLINE_CONFIG["secondary_bureau"]
        days_since = 31

        is_overdue = days_since >= config["overdue_days"]

        assert is_overdue is True

    def test_no_alert_before_25_days(self):
        """Test that no alert is triggered before 25 days"""
        config = DeadlineCheckerService.DEADLINE_CONFIG["secondary_bureau"]
        days_since = 20

        is_warning = days_since >= config["warning_days"]
        is_overdue = days_since >= config["overdue_days"]

        assert is_warning is False
        assert is_overdue is False

    def test_cra_overdue_at_35_days(self):
        """Test that CRA is overdue at 35 days"""
        config = DeadlineCheckerService.DEADLINE_CONFIG["cra_response"]
        days_since = 35

        is_overdue = days_since >= config["overdue_days"]

        assert is_overdue is True
