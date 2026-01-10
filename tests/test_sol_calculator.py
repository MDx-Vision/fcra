"""
Unit Tests for Statute of Limitations (SOL) Calculator Service.

Tests for FCRA SOL calculation functions including:
- Main SOL expiration calculation
- Warning level determination
- Display formatting
- Remaining days calculation
- Expiration checking

FCRA SOL Rules (15 U.S.C. 1681p):
- 2 years from date of discovery, OR
- 5 years from date of occurrence
- Whichever is EARLIER applies
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sol_calculator import (
    calculate_sol,
    get_remaining_days,
    is_expired,
    get_sol_warning_level,
    format_sol_for_display,
    DISCOVERY_PERIOD_YEARS,
    OCCURRENCE_PERIOD_YEARS,
    WARNING_LEVELS,
)


# =============================================================================
# Tests for calculate_sol() - Main SOL Calculation
# =============================================================================

class TestCalculateSol:
    """Test the main SOL calculation function."""

    def test_calculate_sol_basic_violation_only(self):
        """Test SOL calculation with only violation date (discovery defaults to same)."""
        # Violation occurred 1 year ago
        violation_date = date.today() - relativedelta(years=1)
        result = calculate_sol(violation_date)

        assert result["violation_date"] == violation_date.isoformat()
        assert result["discovery_date"] == violation_date.isoformat()
        assert "error" not in result  # No error field when successful
        assert result["is_expired"] is False
        # With same dates, discovery (2yr) is earlier than occurrence (5yr)
        assert result["limiting_factor"] == "discovery"

    def test_calculate_sol_with_discovery_date(self):
        """Test SOL calculation with both violation and discovery dates."""
        # Violation 4 years ago, discovery 1 year ago
        violation_date = date.today() - relativedelta(years=4)
        discovery_date = date.today() - relativedelta(years=1)
        result = calculate_sol(violation_date, discovery_date)

        assert result["violation_date"] == violation_date.isoformat()
        assert result["discovery_date"] == discovery_date.isoformat()
        assert result["is_expired"] is False
        # Occurrence: 4yr ago + 5yr = 1yr from now
        # Discovery: 1yr ago + 2yr = 1yr from now
        # They are very close; occurrence is actually the limiting factor here
        assert result["limiting_factor"] == "occurrence"

    def test_calculate_sol_occurrence_is_limiting_factor(self):
        """Test when 5-year occurrence limit is the limiting factor."""
        # Violation 4 years ago, discovery just yesterday
        violation_date = date.today() - relativedelta(years=4)
        discovery_date = date.today() - timedelta(days=1)
        result = calculate_sol(violation_date, discovery_date)

        # Occurrence: 4yr ago + 5yr = 1yr from now
        # Discovery: yesterday + 2yr = ~2yr from now
        # Occurrence should be limiting
        assert result["limiting_factor"] == "occurrence"

    def test_calculate_sol_discovery_is_limiting_factor(self):
        """Test when 2-year discovery limit is the limiting factor."""
        # Violation 1 year ago, discovery 1 year ago
        violation_date = date.today() - relativedelta(years=1)
        discovery_date = date.today() - relativedelta(years=1)
        result = calculate_sol(violation_date, discovery_date)

        # Occurrence: 1yr ago + 5yr = 4yr from now
        # Discovery: 1yr ago + 2yr = 1yr from now
        # Discovery should be limiting
        assert result["limiting_factor"] == "discovery"

    def test_calculate_sol_expired_claim(self):
        """Test SOL calculation for an expired claim."""
        # Violation 6 years ago (past 5yr occurrence limit)
        violation_date = date.today() - relativedelta(years=6)
        result = calculate_sol(violation_date)

        assert result["is_expired"] is True
        assert result["remaining_days"] < 0
        assert result["warning_level"] == "expired"

    def test_calculate_sol_expiring_soon(self):
        """Test SOL calculation for claim expiring within 30 days."""
        # Discovery 23 months ago (will expire in ~1 month)
        violation_date = date.today() - relativedelta(years=3)
        discovery_date = date.today() - relativedelta(months=23)
        result = calculate_sol(violation_date, discovery_date)

        assert result["is_expired"] is False
        assert result["remaining_days"] <= 45  # approximately 1 month
        assert result["warning_level"] in ["critical", "warning"]

    def test_calculate_sol_none_violation_date(self):
        """Test SOL calculation with None violation date returns error."""
        result = calculate_sol(None)

        assert result["error"] == "Violation date is required"
        assert result["expiration_date"] is None
        assert result["remaining_days"] is None
        assert result["is_expired"] is None

    def test_calculate_sol_datetime_input(self):
        """Test SOL calculation accepts datetime objects and converts them."""
        violation_datetime = datetime.now() - relativedelta(years=1)
        discovery_datetime = datetime.now() - relativedelta(months=6)
        result = calculate_sol(violation_datetime, discovery_datetime)

        # Should work with datetime objects
        assert result["is_expired"] is False
        assert "error" not in result or result.get("error") is None

    def test_calculate_sol_future_violation_date(self):
        """Test SOL calculation with future violation date."""
        # Edge case: future date
        violation_date = date.today() + relativedelta(years=1)
        result = calculate_sol(violation_date)

        # Should not be expired, will expire far in future
        assert result["is_expired"] is False
        assert result["remaining_days"] > 365 * 2  # More than 2 years away

    def test_calculate_sol_same_day_violation_and_discovery(self):
        """Test SOL when violation and discovery are same day."""
        same_date = date.today() - relativedelta(months=6)
        result = calculate_sol(same_date, same_date)

        assert result["violation_date"] == same_date.isoformat()
        assert result["discovery_date"] == same_date.isoformat()
        # Discovery limit (2yr) should be earlier than occurrence (5yr)
        assert result["limiting_factor"] == "discovery"

    def test_calculate_sol_expiration_date_format(self):
        """Test that expiration dates are properly formatted."""
        violation_date = date.today() - relativedelta(months=6)
        result = calculate_sol(violation_date)

        # Check ISO format
        assert "expiration_date" in result
        # Verify it's a valid ISO date string
        parsed_date = date.fromisoformat(result["expiration_date"])
        assert isinstance(parsed_date, date)

        # Check formatted date
        assert "expiration_date_formatted" in result
        # Should be like "January 15, 2025"
        assert len(result["expiration_date_formatted"]) > 0

    def test_calculate_sol_remaining_days_accuracy(self):
        """Test remaining days calculation accuracy."""
        # Set specific dates for predictable results
        violation_date = date.today()
        result = calculate_sol(violation_date)

        # With today as violation date, discovery expiration is 2 years from now
        expected_expiration = date.today() + relativedelta(years=2)
        expected_remaining = (expected_expiration - date.today()).days

        assert result["remaining_days"] == expected_remaining

    def test_calculate_sol_includes_both_expiration_dates(self):
        """Test that result includes both occurrence and discovery expiration dates."""
        violation_date = date.today() - relativedelta(years=1)
        discovery_date = date.today() - relativedelta(months=6)
        result = calculate_sol(violation_date, discovery_date)

        assert "occurrence_expiration" in result
        assert "discovery_expiration" in result
        # Verify they are valid ISO dates
        date.fromisoformat(result["occurrence_expiration"])
        date.fromisoformat(result["discovery_expiration"])


# =============================================================================
# Tests for get_remaining_days()
# =============================================================================

class TestGetRemainingDays:
    """Test the remaining days calculation helper."""

    def test_get_remaining_days_positive(self):
        """Test remaining days for non-expired claim."""
        violation_date = date.today() - relativedelta(months=6)
        days = get_remaining_days(violation_date)

        assert days > 0

    def test_get_remaining_days_negative_expired(self):
        """Test remaining days for expired claim (negative)."""
        violation_date = date.today() - relativedelta(years=6)
        days = get_remaining_days(violation_date)

        assert days < 0

    def test_get_remaining_days_with_discovery(self):
        """Test remaining days with discovery date."""
        violation_date = date.today() - relativedelta(years=4)
        discovery_date = date.today() - relativedelta(years=1)
        days = get_remaining_days(violation_date, discovery_date)

        # Discovery is limiting (1yr ago + 2yr = 1yr remaining)
        assert 300 < days < 400  # Approximately 1 year

    def test_get_remaining_days_zero(self):
        """Test remaining days when expiring today."""
        # Violation exactly 5 years ago
        violation_date = date.today() - relativedelta(years=5)
        days = get_remaining_days(violation_date)

        # Should be 0 or negative (expired)
        assert days <= 0


# =============================================================================
# Tests for is_expired()
# =============================================================================

class TestIsExpired:
    """Test the expiration check function."""

    def test_is_expired_true(self):
        """Test that expired claims return True."""
        violation_date = date.today() - relativedelta(years=6)
        assert is_expired(violation_date) is True

    def test_is_expired_false(self):
        """Test that non-expired claims return False."""
        violation_date = date.today() - relativedelta(months=6)
        assert is_expired(violation_date) is False

    def test_is_expired_boundary_just_expired(self):
        """Test expiration at exact 5-year boundary."""
        # Exactly 5 years and 1 day ago
        violation_date = date.today() - relativedelta(years=5) - timedelta(days=1)
        assert is_expired(violation_date) is True

    def test_is_expired_boundary_not_expired(self):
        """Test clearly before expiration (1 year ago)."""
        # 1 year ago - discovery defaults to same date
        # Discovery expiration: 1yr + 2yr = 1yr from now (not expired)
        # Occurrence expiration: 1yr + 5yr = 4yr from now (not expired)
        violation_date = date.today() - relativedelta(years=1)
        assert is_expired(violation_date) is False

    def test_is_expired_with_discovery_extends_window(self):
        """Test that late discovery can affect expiration status."""
        # Violation 4.5 years ago - would expire in 6 months via occurrence
        violation_date = date.today() - relativedelta(years=4, months=6)
        # Discovery only 6 months ago - expires in 18 months via discovery
        discovery_date = date.today() - relativedelta(months=6)

        # But occurrence (4.5yr + 5yr = 0.5yr remaining) is still limiting
        # Actually occurrence: 4.5yr ago + 5yr = 6mo from now
        # Discovery: 6mo ago + 2yr = 18mo from now
        # Occurrence is earlier (6mo < 18mo), so occurrence is limiting
        assert is_expired(violation_date, discovery_date) is False


# =============================================================================
# Tests for get_sol_warning_level()
# =============================================================================

class TestGetSolWarningLevel:
    """Test warning level determination."""

    def test_warning_level_expired(self):
        """Test expired warning level (negative days)."""
        assert get_sol_warning_level(-1) == "expired"
        assert get_sol_warning_level(-100) == "expired"
        assert get_sol_warning_level(-365) == "expired"

    def test_warning_level_critical(self):
        """Test critical warning level (0-29 days)."""
        assert get_sol_warning_level(0) == "critical"
        assert get_sol_warning_level(1) == "critical"
        assert get_sol_warning_level(15) == "critical"
        assert get_sol_warning_level(29) == "critical"

    def test_warning_level_critical_boundary(self):
        """Test boundary between critical and warning (30 days)."""
        assert get_sol_warning_level(29) == "critical"
        assert get_sol_warning_level(30) == "warning"

    def test_warning_level_warning(self):
        """Test warning level (30-89 days)."""
        assert get_sol_warning_level(30) == "warning"
        assert get_sol_warning_level(45) == "warning"
        assert get_sol_warning_level(60) == "warning"
        assert get_sol_warning_level(89) == "warning"

    def test_warning_level_warning_boundary(self):
        """Test boundary between warning and caution (90 days)."""
        assert get_sol_warning_level(89) == "warning"
        assert get_sol_warning_level(90) == "caution"

    def test_warning_level_caution(self):
        """Test caution level (90-179 days)."""
        assert get_sol_warning_level(90) == "caution"
        assert get_sol_warning_level(120) == "caution"
        assert get_sol_warning_level(150) == "caution"
        assert get_sol_warning_level(179) == "caution"

    def test_warning_level_caution_boundary(self):
        """Test boundary between caution and ok (180 days)."""
        assert get_sol_warning_level(179) == "caution"
        assert get_sol_warning_level(180) == "ok"

    def test_warning_level_ok(self):
        """Test ok level (180+ days)."""
        assert get_sol_warning_level(180) == "ok"
        assert get_sol_warning_level(365) == "ok"
        assert get_sol_warning_level(1000) == "ok"

    def test_warning_level_none_input(self):
        """Test warning level with None input."""
        assert get_sol_warning_level(None) == "unknown"

    def test_warning_level_zero_days(self):
        """Test warning level at exactly 0 days (expiring today)."""
        assert get_sol_warning_level(0) == "critical"


# =============================================================================
# Tests for format_sol_for_display()
# =============================================================================

class TestFormatSolForDisplay:
    """Test display formatting function."""

    def test_format_expired_display(self):
        """Test formatting for expired claims."""
        sol_data = {
            "remaining_days": -30,
            "warning_level": "expired",
            "expiration_date": "2023-01-01",
        }
        result = format_sol_for_display(sol_data)

        assert result["color"] == "#ef4444"  # Red
        assert result["level_label"] == "EXPIRED"
        assert "Expired 30 days ago" in result["remaining_text"]

    def test_format_critical_display(self):
        """Test formatting for critical warning level."""
        sol_data = {
            "remaining_days": 15,
            "warning_level": "critical",
            "expiration_date": "2024-02-01",
        }
        result = format_sol_for_display(sol_data)

        assert result["color"] == "#ef4444"  # Red
        assert result["level_label"] == "CRITICAL"
        assert "15 days remaining" in result["remaining_text"]

    def test_format_warning_display(self):
        """Test formatting for warning level."""
        sol_data = {
            "remaining_days": 60,
            "warning_level": "warning",
            "expiration_date": "2024-03-01",
        }
        result = format_sol_for_display(sol_data)

        assert result["color"] == "#f97316"  # Orange
        assert result["level_label"] == "WARNING"
        assert "60 days remaining" in result["remaining_text"]

    def test_format_caution_display(self):
        """Test formatting for caution level."""
        sol_data = {
            "remaining_days": 120,
            "warning_level": "caution",
            "expiration_date": "2024-05-01",
        }
        result = format_sol_for_display(sol_data)

        assert result["color"] == "#eab308"  # Yellow
        assert result["level_label"] == "CAUTION"
        assert "120 days remaining" in result["remaining_text"]

    def test_format_ok_display(self):
        """Test formatting for ok level."""
        sol_data = {
            "remaining_days": 365,
            "warning_level": "ok",
            "expiration_date": "2025-01-01",
        }
        result = format_sol_for_display(sol_data)

        assert result["color"] == "#22c55e"  # Green
        assert result["level_label"] == "OK"
        assert "365 days remaining" in result["remaining_text"]

    def test_format_unknown_display(self):
        """Test formatting for unknown level."""
        sol_data = {
            "remaining_days": None,
            "warning_level": "unknown",
        }
        result = format_sol_for_display(sol_data)

        assert result["color"] == "#6b7280"  # Gray
        assert result["level_label"] == "UNKNOWN"
        assert result["remaining_text"] == "Unknown"

    def test_format_expires_today(self):
        """Test formatting when expiring today."""
        sol_data = {
            "remaining_days": 0,
            "warning_level": "critical",
            "expiration_date": date.today().isoformat(),
        }
        result = format_sol_for_display(sol_data)

        assert result["remaining_text"] == "Expires today"

    def test_format_one_day_remaining(self):
        """Test formatting for singular day."""
        sol_data = {
            "remaining_days": 1,
            "warning_level": "critical",
            "expiration_date": (date.today() + timedelta(days=1)).isoformat(),
        }
        result = format_sol_for_display(sol_data)

        assert result["remaining_text"] == "1 day remaining"

    def test_format_preserves_original_data(self):
        """Test that formatting preserves all original data."""
        sol_data = {
            "remaining_days": 100,
            "warning_level": "caution",
            "expiration_date": "2024-04-01",
            "violation_date": "2023-01-01",
            "discovery_date": "2023-06-01",
            "limiting_factor": "discovery",
        }
        result = format_sol_for_display(sol_data)

        # Original data should still be present
        assert result["violation_date"] == "2023-01-01"
        assert result["discovery_date"] == "2023-06-01"
        assert result["limiting_factor"] == "discovery"
        assert result["expiration_date"] == "2024-04-01"


# =============================================================================
# Tests for Edge Cases and Integration
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_leap_year_violation_date(self):
        """Test SOL calculation with leap year dates."""
        # Feb 29, 2024 is a leap year date
        violation_date = date(2024, 2, 29)
        result = calculate_sol(violation_date)

        # Should handle leap year correctly
        assert result["is_expired"] is False
        assert "error" not in result or result.get("error") is None

    def test_end_of_year_violation_date(self):
        """Test SOL calculation at year boundaries."""
        violation_date = date(2023, 12, 31)
        result = calculate_sol(violation_date)

        expected_discovery_exp = date(2025, 12, 31)
        expected_occurrence_exp = date(2028, 12, 31)

        assert result["discovery_expiration"] == expected_discovery_exp.isoformat()
        assert result["occurrence_expiration"] == expected_occurrence_exp.isoformat()

    def test_very_old_violation_deeply_expired(self):
        """Test SOL calculation for very old (deeply expired) violations."""
        # 10 years ago - deeply expired
        violation_date = date.today() - relativedelta(years=10)
        result = calculate_sol(violation_date)

        assert result["is_expired"] is True
        # Should be expired by about 5 years (10 - 5 = 5)
        assert result["remaining_days"] < -1500  # More than ~5 years negative

    def test_discovery_before_violation_illogical_but_handled(self):
        """Test handling of illogical dates (discovery before violation)."""
        # Illogical case: discovered before it happened
        violation_date = date.today() - relativedelta(years=1)
        discovery_date = date.today() - relativedelta(years=2)
        result = calculate_sol(violation_date, discovery_date)

        # Should still compute without error
        # Discovery was 2yr ago, so discovery_expiration is today
        # Violation was 1yr ago, so occurrence_expiration is in 4yr
        assert "error" not in result or result.get("error") is None

    def test_same_occurrence_and_discovery_expiration(self):
        """Test when both expirations fall on same date."""
        # This would happen when discovery is exactly 3 years after violation
        # violation_date + 5yr = discovery_date + 2yr
        # discovery_date = violation_date + 3yr
        violation_date = date.today() - relativedelta(years=4)
        discovery_date = violation_date + relativedelta(years=3)
        result = calculate_sol(violation_date, discovery_date)

        # Both should expire at the same time
        assert result["occurrence_expiration"] == result["discovery_expiration"]

    def test_warning_levels_match_constants(self):
        """Test that warning levels use the defined constants."""
        # Verify the constants are as expected
        assert WARNING_LEVELS["critical"] == 30
        assert WARNING_LEVELS["warning"] == 90
        assert WARNING_LEVELS["caution"] == 180

    def test_period_constants(self):
        """Test that SOL period constants are correct per FCRA."""
        assert DISCOVERY_PERIOD_YEARS == 2
        assert OCCURRENCE_PERIOD_YEARS == 5


# =============================================================================
# Tests for Various Date Scenarios
# =============================================================================

class TestDateScenarios:
    """Test various realistic date scenarios."""

    def test_recent_violation_recent_discovery(self):
        """Test recent violation with recent discovery."""
        violation_date = date.today() - timedelta(days=30)
        discovery_date = date.today() - timedelta(days=7)
        result = calculate_sol(violation_date, discovery_date)

        assert result["is_expired"] is False
        assert result["warning_level"] == "ok"
        # Discovery is limiting since both are recent
        assert result["limiting_factor"] == "discovery"

    def test_old_violation_recent_discovery(self):
        """Test old violation with very recent discovery."""
        violation_date = date.today() - relativedelta(years=4, months=6)
        discovery_date = date.today() - timedelta(days=30)
        result = calculate_sol(violation_date, discovery_date)

        # Occurrence: 4.5yr ago + 5yr = 0.5yr remaining (183 days)
        # Discovery: 30 days ago + 2yr = ~2yr remaining
        # Occurrence should be limiting
        assert result["limiting_factor"] == "occurrence"
        assert result["is_expired"] is False

    def test_exactly_two_years_discovery(self):
        """Test discovery exactly 2 years ago (at expiration boundary)."""
        violation_date = date.today() - relativedelta(years=3)
        discovery_date = date.today() - relativedelta(years=2)
        result = calculate_sol(violation_date, discovery_date)

        # Discovery expiration is exactly today
        assert result["remaining_days"] <= 0
        assert result["warning_level"] in ["expired", "critical"]

    def test_exactly_five_years_violation(self):
        """Test violation exactly 5 years ago (at expiration boundary)."""
        violation_date = date.today() - relativedelta(years=5)
        result = calculate_sol(violation_date)

        # Should be at or past expiration
        assert result["remaining_days"] <= 0

    def test_mixed_scenario_discovery_after_occurrence_would_expire(self):
        """Test discovery after occurrence expiration would already pass."""
        # Violation 4.5 years ago, discovered just now
        violation_date = date.today() - relativedelta(years=4, months=6)
        discovery_date = date.today()
        result = calculate_sol(violation_date, discovery_date)

        # Occurrence expires in 6 months, discovery expires in 2 years
        # Occurrence is limiting
        assert result["limiting_factor"] == "occurrence"
        # Not expired yet
        assert result["is_expired"] is False


# =============================================================================
# Tests for Output Format Validation
# =============================================================================

class TestOutputFormat:
    """Test output format and structure."""

    def test_calculate_sol_returns_all_required_fields(self):
        """Test that calculate_sol returns all required fields."""
        violation_date = date.today() - relativedelta(months=6)
        result = calculate_sol(violation_date)

        required_fields = [
            "violation_date",
            "discovery_date",
            "expiration_date",
            "expiration_date_formatted",
            "remaining_days",
            "is_expired",
            "warning_level",
            "limiting_factor",
            "occurrence_expiration",
            "discovery_expiration",
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_calculate_sol_error_response_format(self):
        """Test error response format when violation date is None."""
        result = calculate_sol(None)

        assert "error" in result
        assert result["error"] is not None
        assert result["expiration_date"] is None
        assert result["remaining_days"] is None
        assert result["is_expired"] is None
        assert result["warning_level"] is None

    def test_format_sol_for_display_adds_display_fields(self):
        """Test that format_sol_for_display adds all display fields."""
        sol_data = {
            "remaining_days": 100,
            "warning_level": "caution",
        }
        result = format_sol_for_display(sol_data)

        assert "color" in result
        assert "level_label" in result
        assert "remaining_text" in result

    def test_date_fields_are_iso_format(self):
        """Test that date fields are in ISO 8601 format."""
        violation_date = date.today() - relativedelta(months=6)
        discovery_date = date.today() - relativedelta(months=3)
        result = calculate_sol(violation_date, discovery_date)

        # All date fields should be parseable as ISO dates
        iso_date_fields = [
            "violation_date",
            "discovery_date",
            "expiration_date",
            "occurrence_expiration",
            "discovery_expiration",
        ]

        for field in iso_date_fields:
            assert field in result
            # Verify it parses without error
            parsed = date.fromisoformat(result[field])
            assert isinstance(parsed, date)


# =============================================================================
# Tests for Integration with Real World Scenarios
# =============================================================================

class TestRealWorldScenarios:
    """Test real-world FCRA violation scenarios."""

    def test_typical_credit_report_error_scenario(self):
        """Test typical credit report error discovered during mortgage application."""
        # Consumer finds error when applying for mortgage
        # Violation (incorrect reporting) started 18 months ago
        # Discovery (during mortgage app) was 2 weeks ago
        violation_date = date.today() - relativedelta(months=18)
        discovery_date = date.today() - timedelta(days=14)
        result = calculate_sol(violation_date, discovery_date)

        assert result["is_expired"] is False
        assert result["warning_level"] == "ok"
        # Plenty of time to pursue claim

    def test_old_error_recently_discovered(self):
        """Test old error that was just discovered."""
        # Error has been on report for 4 years, just discovered
        violation_date = date.today() - relativedelta(years=4)
        discovery_date = date.today()
        result = calculate_sol(violation_date, discovery_date)

        assert result["is_expired"] is False
        # Occurrence limit (1 year remaining) is tighter than discovery (2 years)
        assert result["limiting_factor"] == "occurrence"

    def test_near_miss_expired_claim(self):
        """Test claim that nearly expired before discovery."""
        # Violation 4 years 11 months ago
        # Discovery 6 months ago (caught just in time)
        violation_date = date.today() - relativedelta(years=4, months=11)
        discovery_date = date.today() - relativedelta(months=6)
        result = calculate_sol(violation_date, discovery_date)

        # Occurrence expires in about 1 month
        # Should be critical or warning
        assert result["warning_level"] in ["critical", "warning", "caution"]
        assert result["is_expired"] is False

    def test_already_too_late_scenario(self):
        """Test scenario where consumer waited too long after discovery."""
        # Violation 3 years ago
        # Discovery 2 years and 1 month ago (already expired via discovery)
        violation_date = date.today() - relativedelta(years=3)
        discovery_date = date.today() - relativedelta(years=2, months=1)
        result = calculate_sol(violation_date, discovery_date)

        assert result["is_expired"] is True
        assert result["warning_level"] == "expired"

    def test_multiple_violation_dates_use_earliest(self):
        """Test that for multiple violations, each should be calculated separately."""
        # This tests that the function works correctly when called multiple times
        dates = [
            date.today() - relativedelta(years=1),
            date.today() - relativedelta(years=2),
            date.today() - relativedelta(years=4),
        ]

        results = [calculate_sol(d) for d in dates]

        # All should have different expiration dates
        exp_dates = [r["expiration_date"] for r in results]
        assert len(set(exp_dates)) == len(exp_dates)  # All unique

        # Oldest should have shortest remaining time
        assert results[2]["remaining_days"] < results[1]["remaining_days"] < results[0]["remaining_days"]
