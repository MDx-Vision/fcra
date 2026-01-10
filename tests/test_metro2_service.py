"""
Unit Tests for Metro2 Service.
Tests for Metro2 file format validation and FCRA violation detection.
Covers all violation types, edge cases, damage calculations, and account status codes.
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.metro2_service import (
    detect_metro2_violations,
    _check_invalid_status_code,
    _check_balance_exceeds_limit,
    _check_invalid_date_sequence,
    _check_missing_dofd,
    _check_future_dates,
    _check_stale_reporting,
    _check_reaging,
    _check_balance_on_closed,
    _check_invalid_payment_history,
    calculate_violation_damages,
    check_duplicate_reporting,
    analyze_collection_account,
    generate_metro2_dispute_points,
    get_payment_status_info,
    get_state_sol_period,
    _parse_date,
    _parse_amount,
    _is_derogatory_status,
    _get_status_description,
    PAYMENT_STATUS_CODES,
    REVOLVING_STATUS_CODES,
    PAYMENT_HISTORY_CODES,
    ACCOUNT_TYPES,
    VIOLATION_SEVERITY,
    FCRA_SECTIONS,
    STATE_SOL_PERIODS,
)


# =============================================================================
# Tests for _parse_date()
# =============================================================================

class TestParseDate:
    """Test date parsing function."""

    def test_parse_date_none(self):
        """Test parsing None returns None."""
        assert _parse_date(None) is None

    def test_parse_date_date_object(self):
        """Test parsing a date object returns itself."""
        d = date(2023, 6, 15)
        assert _parse_date(d) == d

    def test_parse_date_datetime_object(self):
        """Test parsing a datetime object.

        Note: In Python, datetime is a subclass of date, so isinstance(datetime_obj, date)
        returns True. The function returns the datetime object directly since it passes
        the date check first. This is acceptable as datetime objects work in date comparisons.
        """
        dt = datetime(2023, 6, 15, 10, 30, 0)
        result = _parse_date(dt)
        # datetime is returned as-is since it's a subclass of date
        assert result.year == 2023
        assert result.month == 6
        assert result.day == 15

    def test_parse_date_iso_format(self):
        """Test parsing ISO date format YYYY-MM-DD."""
        assert _parse_date("2023-06-15") == date(2023, 6, 15)

    def test_parse_date_us_format(self):
        """Test parsing US date format MM/DD/YYYY."""
        assert _parse_date("06/15/2023") == date(2023, 6, 15)

    def test_parse_date_us_hyphen_format(self):
        """Test parsing US date format MM-DD-YYYY."""
        assert _parse_date("06-15-2023") == date(2023, 6, 15)

    def test_parse_date_slash_iso_format(self):
        """Test parsing YYYY/MM/DD format."""
        assert _parse_date("2023/06/15") == date(2023, 6, 15)

    def test_parse_date_month_year_format(self):
        """Test parsing MM/YYYY format (day defaults to 1)."""
        assert _parse_date("06/2023") == date(2023, 6, 1)

    def test_parse_date_compact_format(self):
        """Test parsing YYYYMMDD compact format."""
        assert _parse_date("20230615") == date(2023, 6, 15)

    def test_parse_date_invalid_string(self):
        """Test parsing invalid string returns None."""
        assert _parse_date("not-a-date") is None
        assert _parse_date("") is None
        assert _parse_date("abc123") is None

    def test_parse_date_invalid_type(self):
        """Test parsing invalid types returns None."""
        assert _parse_date(12345) is None
        assert _parse_date([2023, 6, 15]) is None


# =============================================================================
# Tests for _parse_amount()
# =============================================================================

class TestParseAmount:
    """Test amount parsing function."""

    def test_parse_amount_none(self):
        """Test parsing None returns None."""
        assert _parse_amount(None) is None

    def test_parse_amount_integer(self):
        """Test parsing integer returns float."""
        assert _parse_amount(1000) == 1000.0

    def test_parse_amount_float(self):
        """Test parsing float returns float."""
        assert _parse_amount(1234.56) == 1234.56

    def test_parse_amount_string_plain(self):
        """Test parsing plain string number."""
        assert _parse_amount("1000") == 1000.0

    def test_parse_amount_string_with_dollar_sign(self):
        """Test parsing string with dollar sign."""
        assert _parse_amount("$1,234.56") == 1234.56

    def test_parse_amount_string_with_commas(self):
        """Test parsing string with commas."""
        assert _parse_amount("1,234,567.89") == 1234567.89

    def test_parse_amount_string_with_spaces(self):
        """Test parsing string with spaces."""
        assert _parse_amount("  1234.56  ") == 1234.56

    def test_parse_amount_invalid_string(self):
        """Test parsing invalid string returns None."""
        assert _parse_amount("not-a-number") is None
        assert _parse_amount("") is None


# =============================================================================
# Tests for _is_derogatory_status()
# =============================================================================

class TestIsDerogatoryStatus:
    """Test derogatory status detection."""

    def test_is_derogatory_status_0(self):
        """Test status 0 (current) is not derogatory."""
        assert _is_derogatory_status("0") is False

    def test_is_derogatory_status_1_through_9(self):
        """Test statuses 1-9 are derogatory."""
        for i in range(1, 10):
            assert _is_derogatory_status(str(i)) is True

    def test_is_derogatory_status_r0(self):
        """Test R0 (revolving current) is not derogatory."""
        assert _is_derogatory_status("R0") is False
        assert _is_derogatory_status("r0") is False

    def test_is_derogatory_status_r1_through_r9(self):
        """Test R1-R9 are derogatory."""
        for i in range(1, 10):
            assert _is_derogatory_status(f"R{i}") is True
            assert _is_derogatory_status(f"r{i}") is True

    def test_is_derogatory_status_codes_g_h_k_l(self):
        """Test special derogatory codes G, H, K, L."""
        assert _is_derogatory_status("G") is True  # Collection
        assert _is_derogatory_status("H") is True  # Foreclosure completed
        assert _is_derogatory_status("K") is True  # Repossession
        assert _is_derogatory_status("L") is True  # Charge-off


# =============================================================================
# Tests for _get_status_description()
# =============================================================================

class TestGetStatusDescription:
    """Test status description retrieval."""

    def test_get_status_description_payment_codes(self):
        """Test getting descriptions for payment status codes."""
        assert _get_status_description("0") == "Current"
        assert _get_status_description("1") == "30-59 days past due"
        assert _get_status_description("9") == "Collection/Charge-off"

    def test_get_status_description_revolving_codes(self):
        """Test getting descriptions for revolving status codes."""
        assert _get_status_description("R0") == "Current"
        assert _get_status_description("R1") == "30-59 days past due"

    def test_get_status_description_unknown(self):
        """Test getting description for unknown code."""
        result = _get_status_description("XYZ")
        assert "Unknown status code" in result


# =============================================================================
# Tests for _check_invalid_status_code()
# =============================================================================

class TestCheckInvalidStatusCode:
    """Test invalid status code detection."""

    def test_invalid_status_code_no_data(self):
        """Test no violation when missing data."""
        assert _check_invalid_status_code("", "", "Test Creditor", "1234") is None
        assert _check_invalid_status_code("1", "", "Test Creditor", "1234") is None
        assert _check_invalid_status_code("", "000000", "Test Creditor", "1234") is None

    def test_invalid_status_code_consistent(self):
        """Test no violation when status matches history."""
        # Status 0 with current payment history
        assert _check_invalid_status_code("0", "000000000000", "Test Creditor", "1234") is None
        # Status 1 with late payment history
        assert _check_invalid_status_code("1", "100000000000", "Test Creditor", "1234") is None

    def test_invalid_status_code_mismatch(self):
        """Test violation when status conflicts with history."""
        # Status shows delinquent but history shows current
        result = _check_invalid_status_code("1", "000000000000", "Test Creditor", "1234")
        assert result is not None
        assert result["violation_type"] == "INVALID_STATUS_CODE"
        assert result["severity"] == "high"
        assert "623(a)(1)(A)" in result["fcra_section"]
        assert result["evidence"]["payment_status"] == "1"
        assert result["evidence"]["most_recent_history"] == "0"

    def test_invalid_status_code_r_status(self):
        """Test revolving status code handling."""
        result = _check_invalid_status_code("R1", "000000000000", "Test Creditor", "1234")
        assert result is not None
        assert result["violation_type"] == "INVALID_STATUS_CODE"

    def test_invalid_status_code_short_history(self):
        """Test with payment history shorter than 12 months."""
        result = _check_invalid_status_code("2", "00000", "Test Creditor", "1234")
        assert result is not None
        assert result["violation_type"] == "INVALID_STATUS_CODE"


# =============================================================================
# Tests for _check_balance_exceeds_limit()
# =============================================================================

class TestCheckBalanceExceedsLimit:
    """Test balance exceeds limit detection."""

    def test_balance_exceeds_limit_non_revolving(self):
        """Test no violation for non-revolving account types."""
        result = _check_balance_exceeds_limit(
            5000, 3000, 3000, "installment", "Test Creditor", "1234"
        )
        assert result is None

    def test_balance_exceeds_limit_zero_balance(self):
        """Test no violation when balance is zero."""
        result = _check_balance_exceeds_limit(
            0, 5000, 5000, "revolving", "Test Creditor", "1234"
        )
        assert result is None

    def test_balance_exceeds_limit_negative_balance(self):
        """Test no violation when balance is negative."""
        result = _check_balance_exceeds_limit(
            -100, 5000, 5000, "revolving", "Test Creditor", "1234"
        )
        assert result is None

    def test_balance_exceeds_limit_no_limit(self):
        """Test no violation when no credit limit specified."""
        result = _check_balance_exceeds_limit(
            5000, None, None, "revolving", "Test Creditor", "1234"
        )
        assert result is None

    def test_balance_exceeds_limit_within_tolerance(self):
        """Test no violation when balance is within 5% tolerance."""
        # 5000 balance, 4900 limit = 2% over (within 5% tolerance)
        result = _check_balance_exceeds_limit(
            5000, 4900, None, "revolving", "Test Creditor", "1234"
        )
        assert result is None

    def test_balance_exceeds_limit_over_threshold(self):
        """Test violation when balance exceeds limit by more than 5%."""
        # 6000 balance, 5000 limit = 20% over
        result = _check_balance_exceeds_limit(
            6000, 5000, None, "revolving", "Test Creditor", "1234"
        )
        assert result is not None
        assert result["violation_type"] == "BALANCE_EXCEEDS_LIMIT"
        assert result["severity"] == "medium"
        assert result["evidence"]["current_balance"] == 6000
        assert result["evidence"]["credit_limit"] == 5000
        assert result["evidence"]["overage_percent"] == 20.0

    def test_balance_exceeds_limit_uses_high_credit_fallback(self):
        """Test uses high_credit when credit_limit is not available."""
        result = _check_balance_exceeds_limit(
            6000, None, 5000, "revolving", "Test Creditor", "1234"
        )
        assert result is not None
        assert result["evidence"]["credit_limit"] == 5000

    def test_balance_exceeds_limit_line_of_credit(self):
        """Test violation for line of credit account type."""
        result = _check_balance_exceeds_limit(
            11000, 10000, None, "line_of_credit", "Test Creditor", "1234"
        )
        assert result is not None
        assert result["evidence"]["account_type"] == "line_of_credit"

    def test_balance_exceeds_limit_open_account(self):
        """Test violation for open account type."""
        result = _check_balance_exceeds_limit(
            11000, 10000, None, "open", "Test Creditor", "1234"
        )
        assert result is not None


# =============================================================================
# Tests for _check_invalid_date_sequence()
# =============================================================================

class TestCheckInvalidDateSequence:
    """Test invalid date sequence detection."""

    def test_invalid_date_sequence_no_date_opened(self):
        """Test no violation when date_opened is missing."""
        result = _check_invalid_date_sequence(
            None, date(2023, 6, 1), date(2023, 7, 1), "Test Creditor", "1234"
        )
        assert result is None

    def test_invalid_date_sequence_valid_dates(self):
        """Test no violation with valid date sequence."""
        result = _check_invalid_date_sequence(
            date(2020, 1, 1),
            date(2023, 6, 1),
            date(2023, 7, 1),
            "Test Creditor",
            "1234"
        )
        assert result is None

    def test_invalid_date_sequence_same_dates(self):
        """Test no violation when dates are the same."""
        result = _check_invalid_date_sequence(
            date(2023, 1, 1),
            date(2023, 1, 1),
            date(2023, 7, 1),
            "Test Creditor",
            "1234"
        )
        assert result is None

    def test_invalid_date_sequence_activity_before_opened(self):
        """Test violation when last activity is before date opened."""
        result = _check_invalid_date_sequence(
            date(2023, 6, 1),
            date(2023, 1, 1),  # Before date opened
            date(2023, 7, 1),
            "Test Creditor",
            "1234"
        )
        assert result is not None
        assert result["violation_type"] == "INVALID_DATE_SEQUENCE"
        assert result["severity"] == "high"
        assert result["evidence"]["date_opened"] == "2023-06-01"
        assert result["evidence"]["date_of_last_activity"] == "2023-01-01"

    def test_invalid_date_sequence_no_last_activity(self):
        """Test no violation when last activity date is missing."""
        result = _check_invalid_date_sequence(
            date(2023, 1, 1),
            None,
            date(2023, 7, 1),
            "Test Creditor",
            "1234"
        )
        assert result is None


# =============================================================================
# Tests for _check_missing_dofd()
# =============================================================================

class TestCheckMissingDofd:
    """Test missing date of first delinquency detection."""

    def test_missing_dofd_current_status(self):
        """Test no violation for current account status."""
        result = _check_missing_dofd("0", None, "Test Creditor", "1234")
        assert result is None

    def test_missing_dofd_with_dofd(self):
        """Test no violation when DOFD is present for derogatory account."""
        result = _check_missing_dofd("9", date(2022, 1, 1), "Test Creditor", "1234")
        assert result is None

    def test_missing_dofd_derogatory_no_dofd(self):
        """Test violation when derogatory status has no DOFD."""
        for status in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            result = _check_missing_dofd(status, None, "Test Creditor", "1234")
            assert result is not None
            assert result["violation_type"] == "MISSING_DOFD"
            assert result["severity"] == "high"
            assert "623(a)(6)" in result["fcra_section"]

    def test_missing_dofd_revolving_derogatory(self):
        """Test violation for revolving derogatory status without DOFD."""
        result = _check_missing_dofd("R3", None, "Test Creditor", "1234")
        assert result is not None
        assert result["violation_type"] == "MISSING_DOFD"


# =============================================================================
# Tests for _check_future_dates()
# =============================================================================

class TestCheckFutureDates:
    """Test future date detection."""

    def test_future_dates_all_past(self):
        """Test no violations when all dates are in the past."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        result = _check_future_dates(
            yesterday, yesterday, yesterday, yesterday,
            today, "Test Creditor", "1234"
        )
        assert len(result) == 0

    def test_future_dates_none_values(self):
        """Test no violations when dates are None."""
        today = date.today()
        result = _check_future_dates(
            None, None, None, None,
            today, "Test Creditor", "1234"
        )
        assert len(result) == 0

    def test_future_dates_date_opened_future(self):
        """Test violation when date opened is in the future."""
        today = date.today()
        future = today + timedelta(days=30)
        result = _check_future_dates(
            future, None, None, None,
            today, "Test Creditor", "1234"
        )
        assert len(result) == 1
        assert result[0]["violation_type"] == "FUTURE_DATE"
        assert result[0]["evidence"]["field_name"] == "date_opened"
        assert result[0]["evidence"]["days_in_future"] == 30

    def test_future_dates_date_reported_future(self):
        """Test violation when date reported is in the future."""
        today = date.today()
        future = today + timedelta(days=7)
        result = _check_future_dates(
            None, future, None, None,
            today, "Test Creditor", "1234"
        )
        assert len(result) == 1
        assert result[0]["evidence"]["field_name"] == "date_reported"

    def test_future_dates_last_activity_future(self):
        """Test violation when last activity date is in the future."""
        today = date.today()
        future = today + timedelta(days=1)
        result = _check_future_dates(
            None, None, future, None,
            today, "Test Creditor", "1234"
        )
        assert len(result) == 1
        assert result[0]["evidence"]["field_name"] == "date_of_last_activity"

    def test_future_dates_dofd_future(self):
        """Test violation when DOFD is in the future."""
        today = date.today()
        future = today + timedelta(days=60)
        result = _check_future_dates(
            None, None, None, future,
            today, "Test Creditor", "1234"
        )
        assert len(result) == 1
        assert result[0]["evidence"]["field_name"] == "date_of_first_delinquency"

    def test_future_dates_multiple_future(self):
        """Test multiple violations when multiple dates are in the future."""
        today = date.today()
        future = today + timedelta(days=30)
        result = _check_future_dates(
            future, future, future, future,
            today, "Test Creditor", "1234"
        )
        assert len(result) == 4


# =============================================================================
# Tests for _check_stale_reporting()
# =============================================================================

class TestCheckStaleReporting:
    """Test stale reporting detection."""

    def test_stale_reporting_no_date(self):
        """Test no violation when date_reported is missing."""
        result = _check_stale_reporting(None, date.today(), "Test Creditor", "1234")
        assert result is None

    def test_stale_reporting_recent(self):
        """Test no violation when reporting is recent (< 90 days)."""
        today = date.today()
        recent = today - timedelta(days=30)
        result = _check_stale_reporting(recent, today, "Test Creditor", "1234")
        assert result is None

    def test_stale_reporting_at_boundary(self):
        """Test no violation at exactly 90 days."""
        today = date.today()
        boundary = today - timedelta(days=90)
        result = _check_stale_reporting(boundary, today, "Test Creditor", "1234")
        assert result is None

    def test_stale_reporting_over_90_days(self):
        """Test violation when reporting is over 90 days old."""
        today = date.today()
        stale = today - timedelta(days=91)
        result = _check_stale_reporting(stale, today, "Test Creditor", "1234")
        assert result is not None
        assert result["violation_type"] == "STALE_REPORTING"
        assert result["severity"] == "medium"
        assert result["evidence"]["days_since_report"] == 91

    def test_stale_reporting_very_old(self):
        """Test violation when reporting is very old (> 1 year)."""
        today = date.today()
        very_stale = today - timedelta(days=400)
        result = _check_stale_reporting(very_stale, today, "Test Creditor", "1234")
        assert result is not None
        assert result["evidence"]["days_since_report"] == 400


# =============================================================================
# Tests for _check_reaging()
# =============================================================================

class TestCheckReaging:
    """Test reaging violation detection."""

    def test_reaging_no_dofd(self):
        """Test no violation when DOFD is missing."""
        result = _check_reaging(None, date(2020, 1, 1), "Test Creditor", "1234")
        assert result is None

    def test_reaging_no_previous_dofd(self):
        """Test no violation when previous DOFD is missing."""
        result = _check_reaging(date(2020, 1, 1), None, "Test Creditor", "1234")
        assert result is None

    def test_reaging_both_missing(self):
        """Test no violation when both DOFDs are missing."""
        result = _check_reaging(None, None, "Test Creditor", "1234")
        assert result is None

    def test_reaging_no_change(self):
        """Test no violation when DOFD hasn't changed."""
        same_date = date(2020, 1, 1)
        result = _check_reaging(same_date, same_date, "Test Creditor", "1234")
        assert result is None

    def test_reaging_dofd_earlier(self):
        """Test no violation when current DOFD is earlier than previous."""
        result = _check_reaging(
            date(2019, 1, 1),
            date(2020, 1, 1),
            "Test Creditor",
            "1234"
        )
        assert result is None

    def test_reaging_dofd_reaged(self):
        """Test violation when DOFD has been moved to later date."""
        result = _check_reaging(
            date(2022, 1, 1),  # Current (newer)
            date(2020, 1, 1),  # Previous (older)
            "Test Creditor",
            "1234"
        )
        assert result is not None
        assert result["violation_type"] == "REAGING"
        assert result["severity"] == "high"
        assert result["evidence"]["previous_dofd"] == "2020-01-01"
        assert result["evidence"]["current_dofd"] == "2022-01-01"
        assert result["evidence"]["days_reaged"] == 731  # ~2 years


# =============================================================================
# Tests for _check_balance_on_closed()
# =============================================================================

class TestCheckBalanceOnClosed:
    """Test balance on closed account detection."""

    def test_balance_on_closed_open_account(self):
        """Test no violation for open account with balance."""
        result = _check_balance_on_closed("open", 5000, "Test Creditor", "1234")
        assert result is None

    def test_balance_on_closed_closed_zero_balance(self):
        """Test no violation for closed account with zero balance."""
        result = _check_balance_on_closed("closed", 0, "Test Creditor", "1234")
        assert result is None

    def test_balance_on_closed_closed_none_balance(self):
        """Test no violation for closed account with None balance."""
        result = _check_balance_on_closed("closed", None, "Test Creditor", "1234")
        assert result is None

    def test_balance_on_closed_closed_with_balance(self):
        """Test violation for closed account with positive balance."""
        result = _check_balance_on_closed("closed", 5000, "Test Creditor", "1234")
        assert result is not None
        assert result["violation_type"] == "BALANCE_ON_CLOSED"
        assert result["severity"] == "medium"
        assert result["evidence"]["current_balance"] == 5000

    def test_balance_on_closed_paid_with_balance(self):
        """Test violation for paid account with positive balance."""
        result = _check_balance_on_closed("paid", 1000, "Test Creditor", "1234")
        assert result is not None
        assert result["violation_type"] == "BALANCE_ON_CLOSED"

    def test_balance_on_closed_settled_with_balance(self):
        """Test violation for settled account with positive balance."""
        result = _check_balance_on_closed("settled", 500, "Test Creditor", "1234")
        assert result is not None

    def test_balance_on_closed_transferred_with_balance(self):
        """Test violation for transferred account with positive balance."""
        result = _check_balance_on_closed("transferred", 2000, "Test Creditor", "1234")
        assert result is not None

    def test_balance_on_closed_case_insensitive(self):
        """Test closed detection is case insensitive."""
        result = _check_balance_on_closed("CLOSED", 1000, "Test Creditor", "1234")
        assert result is not None
        result2 = _check_balance_on_closed("Closed", 1000, "Test Creditor", "1234")
        assert result2 is not None


# =============================================================================
# Tests for _check_invalid_payment_history()
# =============================================================================

class TestCheckInvalidPaymentHistory:
    """Test invalid payment history length detection."""

    def test_invalid_payment_history_no_history(self):
        """Test no violation when payment history is missing."""
        result = _check_invalid_payment_history(
            "", date(2020, 1, 1), date.today(), "Test Creditor", "1234"
        )
        assert result is None

    def test_invalid_payment_history_no_date_opened(self):
        """Test no violation when date opened is missing."""
        result = _check_invalid_payment_history(
            "000000000000", None, date.today(), "Test Creditor", "1234"
        )
        assert result is None

    def test_invalid_payment_history_valid_length(self):
        """Test no violation when history length matches account age."""
        today = date.today()
        # Account opened 12 months ago, 12 months of history
        date_opened = date(today.year - 1, today.month, 1)
        result = _check_invalid_payment_history(
            "000000000000", date_opened, today, "Test Creditor", "1234"
        )
        assert result is None

    def test_invalid_payment_history_too_long(self):
        """Test violation when history is much longer than account age."""
        today = date.today()
        # Account opened 6 months ago
        date_opened = date(today.year, today.month - 6 if today.month > 6 else today.month + 6, 1)
        if today.month <= 6:
            date_opened = date(today.year - 1, today.month + 6, 1)
        # 24 months of history (way more than 6 months + 6 tolerance)
        result = _check_invalid_payment_history(
            "000000000000000000000000", date_opened, today, "Test Creditor", "1234"
        )
        assert result is not None
        assert result["violation_type"] == "INVALID_PAYMENT_HISTORY"

    def test_invalid_payment_history_within_tolerance(self):
        """Test no violation when within 6 month tolerance."""
        today = date.today()
        # Account opened 12 months ago, 15 months history (within 6 month tolerance)
        date_opened = date(today.year - 1, today.month, 1)
        result = _check_invalid_payment_history(
            "000000000000000", date_opened, today, "Test Creditor", "1234"
        )
        assert result is None


# =============================================================================
# Tests for detect_metro2_violations() - Main Function
# =============================================================================

class TestDetectMetro2Violations:
    """Test the main violation detection function."""

    def test_detect_violations_empty_tradeline(self):
        """Test with empty tradeline data."""
        result = detect_metro2_violations({})
        assert isinstance(result, list)

    def test_detect_violations_current_account(self):
        """Test no violations for healthy current account."""
        tradeline = {
            "creditor_name": "Test Bank",
            "account_number": "1234567890",
            "date_opened": date(2020, 1, 1),
            "date_reported": date.today() - timedelta(days=30),
            "current_balance": 5000,
            "credit_limit": 10000,
            "payment_status": "0",
            "payment_history": "000000000000",
            "date_of_last_activity": date.today() - timedelta(days=15),
            "account_type": "revolving",
            "account_status": "open",
        }
        result = detect_metro2_violations(tradeline)
        assert len(result) == 0

    def test_detect_violations_multiple_issues(self):
        """Test detection of multiple violations."""
        today = date.today()
        tradeline = {
            "creditor_name": "Bad Creditor",
            "account_number": "9999",
            "date_opened": date(2023, 1, 1),
            "date_reported": today - timedelta(days=120),  # Stale
            "current_balance": 15000,
            "credit_limit": 10000,  # Balance exceeds
            "payment_status": "3",  # Derogatory
            "payment_history": "000000000000",  # Mismatch with status
            "date_of_last_activity": date(2022, 1, 1),  # Before opened
            "date_of_first_delinquency": None,  # Missing DOFD
            "account_type": "revolving",
            "account_status": "open",
        }
        result = detect_metro2_violations(tradeline)
        violation_types = [v["violation_type"] for v in result]

        assert "INVALID_STATUS_CODE" in violation_types
        assert "BALANCE_EXCEEDS_LIMIT" in violation_types
        assert "INVALID_DATE_SEQUENCE" in violation_types
        assert "MISSING_DOFD" in violation_types
        assert "STALE_REPORTING" in violation_types

    def test_detect_violations_reaging(self):
        """Test reaging violation detection in main function."""
        tradeline = {
            "creditor_name": "Collection Agency",
            "account_number": "5555",
            "date_opened": date(2019, 1, 1),
            "payment_status": "9",
            "date_of_first_delinquency": date(2022, 6, 1),
            "previous_dofd": date(2020, 1, 1),  # Earlier DOFD
            "account_type": "collection",
            "date_reported": date.today() - timedelta(days=30),
        }
        result = detect_metro2_violations(tradeline)
        violation_types = [v["violation_type"] for v in result]
        assert "REAGING" in violation_types

    def test_detect_violations_future_date(self):
        """Test future date detection in main function."""
        future = date.today() + timedelta(days=30)
        tradeline = {
            "creditor_name": "Future Bank",
            "account_number": "7777",
            "date_opened": future,
            "payment_status": "0",
            "account_type": "installment",
        }
        result = detect_metro2_violations(tradeline)
        violation_types = [v["violation_type"] for v in result]
        assert "FUTURE_DATE" in violation_types


# =============================================================================
# Tests for calculate_violation_damages()
# =============================================================================

class TestCalculateViolationDamages:
    """Test damage calculation for violations."""

    def test_calculate_damages_empty_list(self):
        """Test damage calculation with no violations."""
        result = calculate_violation_damages([])
        assert result["damage_range_low"] == 0
        assert result["damage_range_high"] == 0
        assert result["total_violations"] == 0
        assert result["willful_violations"] == 0
        assert result["negligent_violations"] == 0

    def test_calculate_damages_single_negligent(self):
        """Test damage calculation for single negligent violation."""
        violations = [{
            "violation_type": "BALANCE_EXCEEDS_LIMIT",
            "severity": "medium",
            "evidence": {"creditor_name": "Test"},
        }]
        result = calculate_violation_damages(violations)
        assert result["total_violations"] == 1
        assert result["negligent_violations"] == 1
        assert result["damage_range_low"] > 0
        assert result["damage_range_high"] > result["damage_range_low"]

    def test_calculate_damages_single_willful(self):
        """Test damage calculation for single willful violation."""
        violations = [{
            "violation_type": "REAGING",
            "severity": "high",
            "evidence": {"creditor_name": "Test"},
        }]
        result = calculate_violation_damages(violations)
        assert result["total_violations"] == 1
        assert result["willful_violations"] == 1
        # Willful gets 1.5x multiplier
        assert result["damage_range_low"] >= 750 * 1.5  # Base is 750 for REAGING

    def test_calculate_damages_mixed_violations(self):
        """Test damage calculation for mixed violation types."""
        violations = [
            {
                "violation_type": "REAGING",
                "severity": "high",
                "evidence": {"creditor_name": "Creditor A"},
            },
            {
                "violation_type": "STALE_REPORTING",
                "severity": "medium",
                "evidence": {"creditor_name": "Creditor B"},
            },
            {
                "violation_type": "MISSING_DOFD",
                "severity": "high",
                "evidence": {"creditor_name": "Creditor C"},
            },
        ]
        result = calculate_violation_damages(violations)
        assert result["total_violations"] == 3
        assert result["willful_violations"] >= 2  # REAGING and MISSING_DOFD are willful
        assert len(result["per_violation_breakdown"]) == 3

    def test_calculate_damages_formatted_output(self):
        """Test that formatted currency strings are included."""
        violations = [{
            "violation_type": "INVALID_STATUS_CODE",
            "severity": "high",
            "evidence": {"creditor_name": "Test"},
        }]
        result = calculate_violation_damages(violations)
        assert "$" in result["damage_range_low_formatted"]
        assert "$" in result["damage_range_high_formatted"]

    def test_calculate_damages_breakdown_structure(self):
        """Test breakdown structure for each violation."""
        violations = [{
            "violation_type": "DUPLICATE_REPORTING",
            "severity": "high",
            "fcra_section": "623(a)(1)(B)",
            "evidence": {"creditor_name": "Test Creditor"},
        }]
        result = calculate_violation_damages(violations)
        breakdown = result["per_violation_breakdown"][0]
        assert "violation_type" in breakdown
        assert "creditor_name" in breakdown
        assert "damage_low" in breakdown
        assert "damage_high" in breakdown
        assert "is_willful" in breakdown
        assert breakdown["is_willful"] is True

    def test_calculate_damages_notes_generation(self):
        """Test that damage notes are generated."""
        violations = [
            {"violation_type": "REAGING", "severity": "high", "evidence": {}},
            {"violation_type": "REAGING", "severity": "high", "evidence": {}},
            {"violation_type": "REAGING", "severity": "high", "evidence": {}},
        ]
        result = calculate_violation_damages(violations)
        assert "notes" in result
        assert len(result["notes"]) > 0

    def test_calculate_damages_average(self):
        """Test average per violation calculation."""
        violations = [
            {"violation_type": "STALE_REPORTING", "severity": "medium", "evidence": {}},
            {"violation_type": "STALE_REPORTING", "severity": "medium", "evidence": {}},
        ]
        result = calculate_violation_damages(violations)
        expected_avg = (result["damage_range_low"] + result["damage_range_high"]) / 2 / 2
        assert result["average_per_violation"] == round(expected_avg, 2)


# =============================================================================
# Tests for check_duplicate_reporting()
# =============================================================================

class TestCheckDuplicateReporting:
    """Test duplicate reporting detection."""

    def test_duplicate_reporting_empty_list(self):
        """Test no violations with empty tradeline list."""
        result = check_duplicate_reporting([])
        assert len(result) == 0

    def test_duplicate_reporting_single_tradeline(self):
        """Test no violations with single tradeline."""
        tradelines = [{
            "creditor_name": "Test Bank",
            "account_number": "1234567890",
            "original_creditor": "Original Bank",
            "high_credit": 5000,
        }]
        result = check_duplicate_reporting(tradelines)
        assert len(result) == 0

    def test_duplicate_reporting_different_accounts(self):
        """Test no violations for different accounts."""
        tradelines = [
            {
                "creditor_name": "Bank A",
                "account_number": "1234",
                "original_creditor": "Original A",
                "high_credit": 5000,
            },
            {
                "creditor_name": "Bank B",
                "account_number": "5678",
                "original_creditor": "Original B",
                "high_credit": 10000,
            },
        ]
        result = check_duplicate_reporting(tradelines)
        assert len(result) == 0

    def test_duplicate_reporting_same_creditor(self):
        """Test no violation when same creditor reports same account."""
        tradelines = [
            {
                "creditor_name": "Same Bank",
                "account_number": "1234",
                "original_creditor": "original",
                "high_credit": 5000,
            },
            {
                "creditor_name": "Same Bank",
                "account_number": "1234",
                "original_creditor": "original",
                "high_credit": 5000,
            },
        ]
        result = check_duplicate_reporting(tradelines)
        assert len(result) == 0

    def test_duplicate_reporting_detected(self):
        """Test duplicate detection when different creditors report same account."""
        tradelines = [
            {
                "creditor_name": "Original Bank",
                "account_number": "1234567890",
                "original_creditor": "original",
                "high_credit": 5000,
            },
            {
                "creditor_name": "Collection Agency",
                "account_number": "XXXX7890",  # Last 4 match
                "original_creditor": "original",
                "high_credit": 5000,
            },
        ]
        result = check_duplicate_reporting(tradelines)
        assert len(result) == 1
        assert result[0]["violation_type"] == "DUPLICATE_REPORTING"
        assert "Original Bank" in result[0]["evidence"]["first_reporter"]
        assert "Collection Agency" in result[0]["evidence"]["second_reporter"]

    def test_duplicate_reporting_short_account_number(self):
        """Test no violation when account number is too short."""
        tradelines = [
            {
                "creditor_name": "Bank A",
                "account_number": "123",  # Too short
                "original_creditor": "original",
                "high_credit": 5000,
            },
            {
                "creditor_name": "Bank B",
                "account_number": "123",
                "original_creditor": "original",
                "high_credit": 5000,
            },
        ]
        result = check_duplicate_reporting(tradelines)
        assert len(result) == 0

    def test_duplicate_reporting_masked_numbers(self):
        """Test handling of masked account numbers (with X or *)."""
        tradelines = [
            {
                "creditor_name": "Bank A",
                "account_number": "XXXX5678",
                "original_creditor": "same orig",
                "high_credit": 1000,
            },
            {
                "creditor_name": "Collection Agency B",
                "account_number": "****5678",
                "original_creditor": "same orig",
                "high_credit": 1000,
            },
        ]
        result = check_duplicate_reporting(tradelines)
        assert len(result) == 1


# =============================================================================
# Tests for analyze_collection_account()
# =============================================================================

class TestAnalyzeCollectionAccount:
    """Test collection account analysis."""

    def test_analyze_collection_missing_original_creditor(self):
        """Test violation when original creditor is missing."""
        collection_data = {
            "creditor_name": "ABC Collections",
            "account_number": "COL12345",
            "original_creditor": "",
            "payment_status": "9",
            "date_of_first_delinquency": date(2020, 1, 1),
            "date_reported": date.today() - timedelta(days=30),
        }
        result = analyze_collection_account(collection_data)
        violation_types = [v["violation_type"] for v in result]
        assert "MISSING_ORIGINAL_CREDITOR" in violation_types

    def test_analyze_collection_dofd_mismatch(self):
        """Test violation when collection DOFD differs from original."""
        collection_data = {
            "creditor_name": "XYZ Collections",
            "account_number": "COL99999",
            "original_creditor": "Original Bank",
            "original_dofd": date(2020, 1, 1),
            "collection_dofd": date(2021, 1, 1),  # 1 year different
            "payment_status": "9",
            "date_of_first_delinquency": date(2021, 1, 1),
            "date_reported": date.today() - timedelta(days=30),
        }
        result = analyze_collection_account(collection_data)
        violation_types = [v["violation_type"] for v in result]
        assert "DOFD_MISMATCH" in violation_types

    def test_analyze_collection_dofd_within_tolerance(self):
        """Test no DOFD mismatch violation within 30-day tolerance."""
        collection_data = {
            "creditor_name": "Collections Inc",
            "account_number": "COL11111",
            "original_creditor": "Original Bank",
            "original_dofd": date(2020, 1, 1),
            "collection_dofd": date(2020, 1, 15),  # 14 days different
            "payment_status": "9",
            "date_of_first_delinquency": date(2020, 1, 15),
            "date_reported": date.today() - timedelta(days=30),
        }
        result = analyze_collection_account(collection_data)
        violation_types = [v["violation_type"] for v in result]
        assert "DOFD_MISMATCH" not in violation_types

    def test_analyze_collection_sol_expired(self):
        """Test SOL expired detection."""
        collection_data = {
            "creditor_name": "Zombie Debt Collectors",
            "account_number": "ZOM12345",
            "original_creditor": "Original Bank",
            "original_dofd": date(2015, 1, 1),  # Old enough for SOL expiration
            "collection_dofd": date(2015, 1, 1),
            "last_payment_date": date(2015, 1, 1),
            "state": "CA",  # California has 4-year SOL
            "payment_status": "9",
            "date_of_first_delinquency": date(2015, 1, 1),
            "date_reported": date.today() - timedelta(days=30),
        }
        result = analyze_collection_account(collection_data)
        violation_types = [v["violation_type"] for v in result]
        assert "SOL_EXPIRED" in violation_types

    def test_analyze_collection_junk_debt_buyer(self):
        """Test junk debt buyer flag detection."""
        collection_data = {
            "creditor_name": "Debt Buyer LLC",
            "account_number": "JDB12345",
            "original_creditor": "Original Bank",
            "is_sold_debt": True,
            "payment_status": "9",
            "date_of_first_delinquency": date(2022, 1, 1),
            "date_reported": date.today() - timedelta(days=30),
        }
        result = analyze_collection_account(collection_data)
        violation_types = [v["violation_type"] for v in result]
        assert "JUNK_DEBT_BUYER" in violation_types

        # Check verification requirements are included
        junk_violation = next(v for v in result if v["violation_type"] == "JUNK_DEBT_BUYER")
        assert "verification_requirements" in junk_violation["evidence"]


# =============================================================================
# Tests for generate_metro2_dispute_points()
# =============================================================================

class TestGenerateMetro2DisputePoints:
    """Test dispute point generation."""

    def test_generate_dispute_points_empty(self):
        """Test generating dispute points with no violations."""
        result = generate_metro2_dispute_points([])
        assert len(result) == 0

    def test_generate_dispute_points_structure(self):
        """Test dispute point structure."""
        violations = [{
            "violation_type": "REAGING",
            "description": "DOFD was changed",
            "fcra_section": "623(a)(6)",
            "evidence": {
                "creditor_name": "Bad Collector",
                "account_number": "12345",
                "previous_dofd": "2020-01-01",
                "current_dofd": "2022-01-01",
            },
        }]
        result = generate_metro2_dispute_points(violations)
        assert len(result) == 1
        point = result[0]
        assert "dispute_header" in point
        assert "dispute_body" in point
        assert "fcra_citation" in point
        assert "metro2_reference" in point
        assert "requested_action" in point
        assert "evidence_points" in point

    def test_generate_dispute_points_all_types(self):
        """Test dispute point generation for all violation types."""
        violation_types = [
            "INVALID_STATUS_CODE",
            "BALANCE_EXCEEDS_LIMIT",
            "INVALID_DATE_SEQUENCE",
            "MISSING_DOFD",
            "FUTURE_DATE",
            "STALE_REPORTING",
            "REAGING",
            "BALANCE_ON_CLOSED",
            "DUPLICATE_REPORTING",
            "INVALID_PAYMENT_HISTORY",
            "MISSING_ORIGINAL_CREDITOR",
            "SOL_EXPIRED",
            "DOFD_MISMATCH",
            "JUNK_DEBT_BUYER",
        ]

        for v_type in violation_types:
            violations = [{
                "violation_type": v_type,
                "description": f"Test {v_type}",
                "fcra_section": "623(a)(1)(A)",
                "evidence": {
                    "creditor_name": "Test Creditor",
                    "account_number": "12345",
                },
            }]
            result = generate_metro2_dispute_points(violations)
            assert len(result) == 1
            assert result[0]["violation_type"] == v_type
            assert len(result[0]["dispute_header"]) > 0


# =============================================================================
# Tests for get_payment_status_info()
# =============================================================================

class TestGetPaymentStatusInfo:
    """Test payment status info retrieval."""

    def test_get_payment_status_info_standard_codes(self):
        """Test getting info for standard payment codes 0-9."""
        for code in "0123456789":
            info = get_payment_status_info(code)
            assert "description" in info
            assert "is_derogatory" in info
            if code == "0":
                assert info["is_derogatory"] is False
            else:
                assert info["is_derogatory"] is True

    def test_get_payment_status_info_revolving_codes(self):
        """Test getting info for revolving codes R0-R9."""
        for i in range(10):
            info = get_payment_status_info(f"R{i}")
            assert "description" in info
            if i == 0:
                assert info["is_derogatory"] is False
            else:
                assert info["is_derogatory"] is True

    def test_get_payment_status_info_lowercase_revolving(self):
        """Test revolving codes are case-insensitive."""
        info = get_payment_status_info("r3")
        assert "description" in info
        assert info["is_derogatory"] is True

    def test_get_payment_status_info_unknown(self):
        """Test unknown status code returns appropriate response."""
        info = get_payment_status_info("ZZZ")
        assert "Unknown" in info["description"]
        assert info["is_derogatory"] is False


# =============================================================================
# Tests for get_state_sol_period()
# =============================================================================

class TestGetStateSolPeriod:
    """Test state statute of limitations period retrieval."""

    def test_get_state_sol_period_ca(self):
        """Test California SOL period."""
        assert get_state_sol_period("CA") == 4

    def test_get_state_sol_period_ny(self):
        """Test New York SOL period."""
        assert get_state_sol_period("NY") == 6

    def test_get_state_sol_period_ri(self):
        """Test Rhode Island SOL period (longest at 10 years)."""
        assert get_state_sol_period("RI") == 10

    def test_get_state_sol_period_dc(self):
        """Test District of Columbia SOL period."""
        assert get_state_sol_period("DC") == 3

    def test_get_state_sol_period_lowercase(self):
        """Test lowercase state codes work."""
        assert get_state_sol_period("ca") == 4

    def test_get_state_sol_period_unknown(self):
        """Test unknown state returns None."""
        assert get_state_sol_period("XX") is None
        assert get_state_sol_period("") is None


# =============================================================================
# Tests for Constants and Data Structures
# =============================================================================

class TestConstants:
    """Test module constants and data structures."""

    def test_payment_status_codes_complete(self):
        """Test all payment status codes 0-9 are defined."""
        for i in range(10):
            assert str(i) in PAYMENT_STATUS_CODES

    def test_revolving_status_codes_complete(self):
        """Test all revolving status codes R0-R9 are defined."""
        for i in range(10):
            assert f"R{i}" in REVOLVING_STATUS_CODES

    def test_payment_history_codes_exist(self):
        """Test common payment history codes are defined."""
        common_codes = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "B", "C", "X", "-"]
        for code in common_codes:
            assert code in PAYMENT_HISTORY_CODES

    def test_account_types_structure(self):
        """Test account types have required properties."""
        for account_type, props in ACCOUNT_TYPES.items():
            assert "has_credit_limit" in props
            assert "uses_high_credit" in props

    def test_violation_severity_values(self):
        """Test violation severity has valid values."""
        valid_severities = ["low", "medium", "high"]
        for severity in VIOLATION_SEVERITY.values():
            assert severity in valid_severities

    def test_fcra_sections_defined(self):
        """Test FCRA sections are defined for all violation types."""
        for v_type in VIOLATION_SEVERITY.keys():
            assert v_type in FCRA_SECTIONS

    def test_state_sol_periods_complete(self):
        """Test all US states have SOL periods defined."""
        # All 50 states plus DC
        assert len(STATE_SOL_PERIODS) >= 51
        assert "CA" in STATE_SOL_PERIODS
        assert "NY" in STATE_SOL_PERIODS
        assert "TX" in STATE_SOL_PERIODS
        assert "FL" in STATE_SOL_PERIODS
        assert "DC" in STATE_SOL_PERIODS


# =============================================================================
# Integration and Edge Case Tests
# =============================================================================

class TestIntegrationAndEdgeCases:
    """Test integration scenarios and edge cases."""

    def test_full_workflow_with_violations(self):
        """Test complete workflow: detect violations -> calculate damages -> generate disputes."""
        tradeline = {
            "creditor_name": "Problem Creditor",
            "account_number": "BAD123456",
            "date_opened": date(2020, 1, 1),
            "date_reported": date.today() - timedelta(days=120),
            "current_balance": 0,
            "payment_status": "9",
            "date_of_first_delinquency": None,  # Missing DOFD
            "account_type": "collection",
            "account_status": "closed",
        }

        # Step 1: Detect violations
        violations = detect_metro2_violations(tradeline)
        assert len(violations) > 0

        # Step 2: Calculate damages
        damages = calculate_violation_damages(violations)
        assert damages["total_violations"] > 0
        assert damages["damage_range_high"] > 0

        # Step 3: Generate dispute points
        dispute_points = generate_metro2_dispute_points(violations)
        assert len(dispute_points) == len(violations)

    def test_string_dates_handled(self):
        """Test that string dates are properly parsed in main function."""
        tradeline = {
            "creditor_name": "String Date Creditor",
            "account_number": "STR123",
            "date_opened": "2020-01-01",
            "date_reported": "2024-06-01",
            "payment_status": "0",
            "account_type": "installment",
        }
        # Should not raise an error
        result = detect_metro2_violations(tradeline)
        assert isinstance(result, list)

    def test_string_amounts_handled(self):
        """Test that string amounts are properly parsed."""
        tradeline = {
            "creditor_name": "String Amount Creditor",
            "account_number": "AMT123",
            "date_opened": date(2020, 1, 1),
            "date_reported": date.today() - timedelta(days=30),
            "current_balance": "$12,345.67",
            "credit_limit": "$10,000.00",
            "payment_status": "0",
            "account_type": "revolving",
        }
        result = detect_metro2_violations(tradeline)
        # Should detect balance exceeds limit
        violation_types = [v["violation_type"] for v in result]
        assert "BALANCE_EXCEEDS_LIMIT" in violation_types

    def test_unicode_creditor_names(self):
        """Test handling of unicode characters in creditor names."""
        tradeline = {
            "creditor_name": "Test Bank & Trust Co.",
            "account_number": "UNI123",
            "payment_status": "1",
            "payment_history": "000000",
            "date_of_first_delinquency": None,
            "date_reported": date.today() - timedelta(days=30),
        }
        result = detect_metro2_violations(tradeline)
        # Should work without errors
        assert isinstance(result, list)

    def test_very_old_dates(self):
        """Test handling of very old dates."""
        tradeline = {
            "creditor_name": "Old Account Creditor",
            "account_number": "OLD123",
            "date_opened": date(1990, 1, 1),
            "date_reported": date.today() - timedelta(days=30),
            "payment_status": "0",
            "payment_history": "000000000000" * 10,  # 120 months of history
            "account_type": "mortgage",
        }
        result = detect_metro2_violations(tradeline)
        # Should not flag invalid payment history for old accounts
        violation_types = [v["violation_type"] for v in result]
        assert "INVALID_PAYMENT_HISTORY" not in violation_types

    def test_collection_with_all_issues(self):
        """Test collection account with multiple issues."""
        collection_data = {
            "creditor_name": "Nightmare Collectors",
            "account_number": "NMR999",
            "original_creditor": "",  # Missing
            "is_sold_debt": True,  # Junk debt
            "original_dofd": date(2015, 1, 1),
            "collection_dofd": date(2020, 1, 1),  # Mismatched
            "last_payment_date": date(2015, 1, 1),
            "state": "CA",  # SOL expired
            "payment_status": "9",
            "date_of_first_delinquency": date(2020, 1, 1),
            "previous_dofd": date(2015, 1, 1),  # Reaging
            "date_reported": date.today() - timedelta(days=30),
        }
        result = analyze_collection_account(collection_data)
        violation_types = [v["violation_type"] for v in result]

        assert "MISSING_ORIGINAL_CREDITOR" in violation_types
        assert "JUNK_DEBT_BUYER" in violation_types
        assert "DOFD_MISMATCH" in violation_types
        assert "SOL_EXPIRED" in violation_types
        assert "REAGING" in violation_types


# =============================================================================
# Tests for Severity Classification
# =============================================================================

class TestSeverityClassification:
    """Test violation severity classifications."""

    def test_high_severity_violations(self):
        """Test that high severity violations are properly classified."""
        high_severity_types = [
            "INVALID_STATUS_CODE",
            "INVALID_DATE_SEQUENCE",
            "MISSING_DOFD",
            "FUTURE_DATE",
            "REAGING",
            "DUPLICATE_REPORTING",
            "MISSING_ORIGINAL_CREDITOR",
            "SOL_EXPIRED",
            "DOFD_MISMATCH",
        ]
        for v_type in high_severity_types:
            assert VIOLATION_SEVERITY.get(v_type) == "high", f"{v_type} should be high severity"

    def test_medium_severity_violations(self):
        """Test that medium severity violations are properly classified."""
        medium_severity_types = [
            "BALANCE_EXCEEDS_LIMIT",
            "STALE_REPORTING",
            "BALANCE_ON_CLOSED",
            "INVALID_PAYMENT_HISTORY",
            "JUNK_DEBT_BUYER",
        ]
        for v_type in medium_severity_types:
            assert VIOLATION_SEVERITY.get(v_type) == "medium", f"{v_type} should be medium severity"


# =============================================================================
# Tests for FCRA Section References
# =============================================================================

class TestFcraSectionReferences:
    """Test FCRA section references in violations."""

    def test_fcra_623a1a_violations(self):
        """Test violations that cite FCRA 623(a)(1)(A)."""
        section_623a1a_types = [
            "INVALID_STATUS_CODE",
            "BALANCE_EXCEEDS_LIMIT",
            "INVALID_DATE_SEQUENCE",
            "FUTURE_DATE",
            "BALANCE_ON_CLOSED",
            "INVALID_PAYMENT_HISTORY",
            "MISSING_ORIGINAL_CREDITOR",
            "JUNK_DEBT_BUYER",
        ]
        for v_type in section_623a1a_types:
            assert "623(a)(1)(A)" in FCRA_SECTIONS[v_type]

    def test_fcra_623a6_violations(self):
        """Test violations that cite FCRA 623(a)(6) for DOFD issues."""
        section_623a6_types = ["MISSING_DOFD", "REAGING", "DOFD_MISMATCH"]
        for v_type in section_623a6_types:
            assert "623(a)(6)" in FCRA_SECTIONS[v_type]

    def test_fcra_605a_violations(self):
        """Test violations that cite FCRA 605(a) for SOL issues."""
        assert "605(a)" in FCRA_SECTIONS["SOL_EXPIRED"]
