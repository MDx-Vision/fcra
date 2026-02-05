"""
Unit tests for SOL Calculator Service

Tests cover:
- SOL calculation (2 year discovery / 5 year occurrence)
- Warning levels
- Expiration checking
- Formatting for display
- Database queries for violations
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from dateutil.relativedelta import relativedelta


class TestConstants:
    """Tests for SOL constants"""

    def test_discovery_period(self):
        """Should have 2-year discovery period"""
        from services.sol_calculator import DISCOVERY_PERIOD_YEARS

        assert DISCOVERY_PERIOD_YEARS == 2

    def test_occurrence_period(self):
        """Should have 5-year occurrence period"""
        from services.sol_calculator import OCCURRENCE_PERIOD_YEARS

        assert OCCURRENCE_PERIOD_YEARS == 5

    def test_warning_levels(self):
        """Should have warning level thresholds"""
        from services.sol_calculator import WARNING_LEVELS

        assert WARNING_LEVELS["critical"] == 30
        assert WARNING_LEVELS["warning"] == 90
        assert WARNING_LEVELS["caution"] == 180


class TestCalculateSol:
    """Tests for calculate_sol function"""

    def test_calculates_with_violation_date_only(self):
        """Should calculate SOL with only violation date"""
        from services.sol_calculator import calculate_sol

        violation_date = date.today() - timedelta(days=365)  # 1 year ago
        result = calculate_sol(violation_date)

        assert "expiration_date" in result
        assert "remaining_days" in result
        assert "is_expired" in result
        assert "warning_level" in result

    def test_calculates_with_discovery_date(self):
        """Should use discovery date when provided"""
        from services.sol_calculator import calculate_sol

        violation_date = date.today() - timedelta(days=365 * 3)  # 3 years ago
        discovery_date = date.today() - timedelta(days=365)  # 1 year ago

        result = calculate_sol(violation_date, discovery_date)

        # Discovery should limit SOL (2 years from discovery = 1 year from now)
        assert result["limiting_factor"] == "discovery"

    def test_uses_occurrence_when_earlier(self):
        """Should use occurrence expiration when it's earlier"""
        from services.sol_calculator import calculate_sol

        violation_date = date.today() - timedelta(days=365 * 4)  # 4 years ago
        discovery_date = date.today()  # Just discovered

        result = calculate_sol(violation_date, discovery_date)

        # Occurrence is 5 years from 4 years ago = 1 year from now
        # Discovery is 2 years from today = 2 years from now
        # Occurrence should be limiting factor
        assert result["limiting_factor"] == "occurrence"

    def test_handles_datetime_objects(self):
        """Should handle datetime objects"""
        from services.sol_calculator import calculate_sol

        violation_datetime = datetime.now() - timedelta(days=365)
        result = calculate_sol(violation_datetime)

        assert result["expiration_date"] is not None

    def test_returns_error_for_none_violation_date(self):
        """Should return error for None violation date"""
        from services.sol_calculator import calculate_sol

        result = calculate_sol(None)

        assert "error" in result
        assert result["expiration_date"] is None

    def test_expired_claim(self):
        """Should detect expired claim"""
        from services.sol_calculator import calculate_sol

        violation_date = date.today() - timedelta(days=365 * 6)  # 6 years ago
        result = calculate_sol(violation_date)

        assert result["is_expired"] is True
        assert result["remaining_days"] < 0

    def test_includes_formatted_expiration(self):
        """Should include formatted expiration date"""
        from services.sol_calculator import calculate_sol

        violation_date = date.today()
        result = calculate_sol(violation_date)

        assert "expiration_date_formatted" in result
        # Should be in "Month Day, Year" format
        assert "," in result["expiration_date_formatted"]


class TestGetRemainingDays:
    """Tests for get_remaining_days function"""

    def test_returns_positive_for_active_claim(self):
        """Should return positive days for active claim"""
        from services.sol_calculator import get_remaining_days

        violation_date = date.today() - timedelta(days=365)  # 1 year ago
        days = get_remaining_days(violation_date)

        assert days > 0

    def test_returns_negative_for_expired_claim(self):
        """Should return negative days for expired claim"""
        from services.sol_calculator import get_remaining_days

        violation_date = date.today() - timedelta(days=365 * 6)  # 6 years ago
        days = get_remaining_days(violation_date)

        assert days < 0

    def test_accepts_discovery_date(self):
        """Should accept discovery date"""
        from services.sol_calculator import get_remaining_days

        violation_date = date.today() - timedelta(days=365 * 4)
        discovery_date = date.today()
        days = get_remaining_days(violation_date, discovery_date)

        assert isinstance(days, int)


class TestIsExpired:
    """Tests for is_expired function"""

    def test_returns_false_for_active_claim(self):
        """Should return False for active claim"""
        from services.sol_calculator import is_expired

        violation_date = date.today() - timedelta(days=365)  # 1 year ago
        result = is_expired(violation_date)

        assert result is False

    def test_returns_true_for_expired_claim(self):
        """Should return True for expired claim"""
        from services.sol_calculator import is_expired

        violation_date = date.today() - timedelta(days=365 * 6)  # 6 years ago
        result = is_expired(violation_date)

        assert result is True


class TestGetSolWarningLevel:
    """Tests for get_sol_warning_level function"""

    def test_returns_expired(self):
        """Should return 'expired' for negative days"""
        from services.sol_calculator import get_sol_warning_level

        result = get_sol_warning_level(-10)

        assert result == "expired"

    def test_returns_critical(self):
        """Should return 'critical' for < 30 days"""
        from services.sol_calculator import get_sol_warning_level

        result = get_sol_warning_level(15)

        assert result == "critical"

    def test_returns_warning(self):
        """Should return 'warning' for < 90 days"""
        from services.sol_calculator import get_sol_warning_level

        result = get_sol_warning_level(60)

        assert result == "warning"

    def test_returns_caution(self):
        """Should return 'caution' for < 180 days"""
        from services.sol_calculator import get_sol_warning_level

        result = get_sol_warning_level(120)

        assert result == "caution"

    def test_returns_ok(self):
        """Should return 'ok' for >= 180 days"""
        from services.sol_calculator import get_sol_warning_level

        result = get_sol_warning_level(365)

        assert result == "ok"

    def test_returns_unknown_for_none(self):
        """Should return 'unknown' for None"""
        from services.sol_calculator import get_sol_warning_level

        result = get_sol_warning_level(None)

        assert result == "unknown"


class TestFormatSolForDisplay:
    """Tests for format_sol_for_display function"""

    def test_adds_color(self):
        """Should add color based on warning level"""
        from services.sol_calculator import format_sol_for_display

        sol_data = {"remaining_days": 15, "warning_level": "critical"}
        result = format_sol_for_display(sol_data)

        assert "color" in result
        assert result["color"] == "#ef4444"  # Red for critical

    def test_adds_level_label(self):
        """Should add level label"""
        from services.sol_calculator import format_sol_for_display

        sol_data = {"remaining_days": 365, "warning_level": "ok"}
        result = format_sol_for_display(sol_data)

        assert "level_label" in result
        assert result["level_label"] == "OK"

    def test_formats_remaining_text_days(self):
        """Should format remaining days text"""
        from services.sol_calculator import format_sol_for_display

        sol_data = {"remaining_days": 100, "warning_level": "caution"}
        result = format_sol_for_display(sol_data)

        assert "remaining_text" in result
        assert "100 days remaining" in result["remaining_text"]

    def test_formats_today_expiration(self):
        """Should format 'Expires today' for 0 days"""
        from services.sol_calculator import format_sol_for_display

        sol_data = {"remaining_days": 0, "warning_level": "critical"}
        result = format_sol_for_display(sol_data)

        assert result["remaining_text"] == "Expires today"

    def test_formats_single_day(self):
        """Should format '1 day remaining' for 1 day"""
        from services.sol_calculator import format_sol_for_display

        sol_data = {"remaining_days": 1, "warning_level": "critical"}
        result = format_sol_for_display(sol_data)

        assert result["remaining_text"] == "1 day remaining"

    def test_formats_expired_text(self):
        """Should format expired text"""
        from services.sol_calculator import format_sol_for_display

        sol_data = {"remaining_days": -30, "warning_level": "expired"}
        result = format_sol_for_display(sol_data)

        assert "Expired 30 days ago" in result["remaining_text"]

    def test_formats_unknown(self):
        """Should handle unknown/None remaining days"""
        from services.sol_calculator import format_sol_for_display

        sol_data = {"remaining_days": None, "warning_level": "unknown"}
        result = format_sol_for_display(sol_data)

        assert result["remaining_text"] == "Unknown"

    def test_preserves_original_data(self):
        """Should preserve original SOL data"""
        from services.sol_calculator import format_sol_for_display

        sol_data = {
            "remaining_days": 100,
            "warning_level": "caution",
            "expiration_date": "2025-06-15",
            "custom_field": "test"
        }
        result = format_sol_for_display(sol_data)

        assert result["expiration_date"] == "2025-06-15"
        assert result["custom_field"] == "test"


class TestGetViolationsWithSolStatus:
    """Tests for get_violations_with_sol_status function"""

    def test_returns_list(self):
        """Should return list of violations with SOL status"""
        from services.sol_calculator import get_violations_with_sol_status

        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.join.return_value.all.return_value = []

        result = get_violations_with_sol_status(mock_db)

        assert isinstance(result, list)

    def test_filters_by_client_id(self):
        """Should filter by client_id when provided"""
        from services.sol_calculator import get_violations_with_sol_status

        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = []

        result = get_violations_with_sol_status(mock_db, client_id=1)

        mock_db.query.return_value.join.return_value.join.return_value.filter.assert_called()


class TestGetUpcomingExpirations:
    """Tests for get_upcoming_expirations function"""

    @patch('services.sol_calculator.get_violations_with_sol_status')
    def test_returns_upcoming_expirations(self, mock_get_violations):
        """Should return violations expiring soon"""
        from services.sol_calculator import get_upcoming_expirations

        mock_get_violations.return_value = [
            {"violation_id": 1, "remaining_days": 30},
            {"violation_id": 2, "remaining_days": 60},
            {"violation_id": 3, "remaining_days": 120},
        ]

        mock_db = MagicMock()
        result = get_upcoming_expirations(mock_db, days=90)

        # Should only include violations with remaining_days <= 90
        assert len(result) == 2
        assert all(v["remaining_days"] <= 90 for v in result)

    @patch('services.sol_calculator.get_violations_with_sol_status')
    def test_sorts_by_remaining_days(self, mock_get_violations):
        """Should sort by remaining days ascending"""
        from services.sol_calculator import get_upcoming_expirations

        mock_get_violations.return_value = [
            {"violation_id": 1, "remaining_days": 60},
            {"violation_id": 2, "remaining_days": 30},
            {"violation_id": 3, "remaining_days": 10},
        ]

        mock_db = MagicMock()
        result = get_upcoming_expirations(mock_db, days=90)

        # Should be sorted by remaining_days ascending
        assert result[0]["remaining_days"] == 10
        assert result[1]["remaining_days"] == 30


class TestGetExpiredClaims:
    """Tests for get_expired_claims function"""

    @patch('services.sol_calculator.get_violations_with_sol_status')
    def test_returns_expired_violations(self, mock_get_violations):
        """Should return only expired violations"""
        from services.sol_calculator import get_expired_claims

        mock_get_violations.return_value = [
            {"violation_id": 1, "is_expired": True},
            {"violation_id": 2, "is_expired": False},
            {"violation_id": 3, "is_expired": True},
        ]

        mock_db = MagicMock()
        result = get_expired_claims(mock_db)

        assert len(result) == 2
        assert all(v["is_expired"] for v in result)


class TestGetSolStatistics:
    """Tests for get_sol_statistics function"""

    @patch('services.sol_calculator.get_violations_with_sol_status')
    def test_returns_statistics(self, mock_get_violations):
        """Should return SOL statistics"""
        from services.sol_calculator import get_sol_statistics

        mock_get_violations.return_value = [
            {"warning_level": "ok", "remaining_days": 200},
            {"warning_level": "caution", "remaining_days": 100},
            {"warning_level": "warning", "remaining_days": 50},
            {"warning_level": "critical", "remaining_days": 20},
            {"warning_level": "expired", "remaining_days": -30},
        ]

        mock_db = MagicMock()
        result = get_sol_statistics(mock_db)

        assert result["total"] == 5
        assert result["ok"] == 1
        assert result["caution"] == 1
        assert result["warning"] == 1
        assert result["critical"] == 1
        assert result["expired"] == 1

    @patch('services.sol_calculator.get_violations_with_sol_status')
    def test_counts_expiring_periods(self, mock_get_violations):
        """Should count expiring in 30/60/90 days"""
        from services.sol_calculator import get_sol_statistics

        mock_get_violations.return_value = [
            {"warning_level": "critical", "remaining_days": 20},
            {"warning_level": "critical", "remaining_days": 25},
            {"warning_level": "warning", "remaining_days": 50},
            {"warning_level": "caution", "remaining_days": 100},
        ]

        mock_db = MagicMock()
        result = get_sol_statistics(mock_db)

        assert result["expiring_30_days"] == 2
        assert result["expiring_60_days"] == 3
        assert result["expiring_90_days"] == 3
