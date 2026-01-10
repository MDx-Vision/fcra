"""
Unit Tests for Settlement Calculator Service.
Tests for FCRA settlement calculation functions including statutory damages,
actual damages, punitive damages, attorney fees, and settlement likelihood.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.settlement_calculator import (
    format_currency,
    calculate_settlement,
    _calculate_statutory_damages,
    _calculate_actual_damages,
    _calculate_punitive_damages,
    _calculate_attorney_fees,
    _determine_settlement_likelihood,
    _calculate_recommended_demand,
    _generate_calculation_notes,
)


# =============================================================================
# Tests for format_currency()
# =============================================================================

class TestFormatCurrency:
    """Test currency formatting function."""

    def test_format_currency_integer(self):
        """Test formatting whole dollar amounts."""
        assert format_currency(1000) == "$1,000.00"

    def test_format_currency_float(self):
        """Test formatting amounts with cents."""
        assert format_currency(1234.56) == "$1,234.56"

    def test_format_currency_zero(self):
        """Test formatting zero amount."""
        assert format_currency(0) == "$0.00"

    def test_format_currency_none(self):
        """Test formatting None returns zero."""
        assert format_currency(None) == "$0.00"

    def test_format_currency_large_amount(self):
        """Test formatting large amounts with proper comma separation."""
        assert format_currency(1000000) == "$1,000,000.00"
        assert format_currency(123456789.99) == "$123,456,789.99"

    def test_format_currency_small_amount(self):
        """Test formatting small amounts under a dollar."""
        assert format_currency(0.50) == "$0.50"
        assert format_currency(0.01) == "$0.01"

    def test_format_currency_negative_amount(self):
        """Test formatting negative amounts."""
        assert format_currency(-500) == "$-500.00"


# =============================================================================
# Tests for _calculate_statutory_damages()
# =============================================================================

class TestCalculateStatutoryDamages:
    """Test statutory damages calculation for willful violations."""

    def test_statutory_damages_single_violation(self):
        """Test statutory damages for one willful violation."""
        low, high = _calculate_statutory_damages(1)
        assert low == 100.0  # $100 minimum per FCRA
        assert high == 1000.0  # $1,000 maximum per FCRA

    def test_statutory_damages_multiple_violations(self):
        """Test statutory damages for multiple willful violations."""
        low, high = _calculate_statutory_damages(5)
        assert low == 500.0  # 5 * $100
        assert high == 5000.0  # 5 * $1,000

    def test_statutory_damages_zero_violations(self):
        """Test statutory damages with no willful violations."""
        low, high = _calculate_statutory_damages(0)
        assert low == 0.0
        assert high == 0.0

    def test_statutory_damages_negative_violations(self):
        """Test statutory damages with negative violations (edge case)."""
        low, high = _calculate_statutory_damages(-1)
        assert low == 0.0
        assert high == 0.0

    def test_statutory_damages_large_violations(self):
        """Test statutory damages for many violations."""
        low, high = _calculate_statutory_damages(100)
        assert low == 10000.0  # 100 * $100
        assert high == 100000.0  # 100 * $1,000


# =============================================================================
# Tests for _calculate_actual_damages()
# =============================================================================

class TestCalculateActualDamages:
    """Test actual damages aggregation from itemized breakdown."""

    def test_actual_damages_empty_list(self):
        """Test actual damages with no items."""
        total, breakdown = _calculate_actual_damages([])
        assert total == 0.0
        assert all(cat["amount"] == 0.0 for cat in breakdown.values())

    def test_actual_damages_single_item(self):
        """Test actual damages with one item."""
        items = [{"type": "credit_denial", "amount": 5000, "description": "Mortgage denial"}]
        total, breakdown = _calculate_actual_damages(items)
        assert total == 5000.0
        assert breakdown["credit_denial"]["amount"] == 5000.0

    def test_actual_damages_multiple_items_same_category(self):
        """Test actual damages with multiple items in same category."""
        items = [
            {"type": "credit_denial", "amount": 5000, "description": "Mortgage denial"},
            {"type": "credit_denial", "amount": 3000, "description": "Auto loan denial"},
        ]
        total, breakdown = _calculate_actual_damages(items)
        assert total == 8000.0
        assert breakdown["credit_denial"]["amount"] == 8000.0
        assert len(breakdown["credit_denial"]["items"]) == 2

    def test_actual_damages_multiple_categories(self):
        """Test actual damages across multiple categories."""
        items = [
            {"type": "credit_denial", "amount": 5000, "description": "Mortgage denial"},
            {"type": "higher_interest", "amount": 2000, "description": "Higher rate on auto"},
            {"type": "emotional_distress", "amount": 10000, "description": "Anxiety and stress"},
        ]
        total, breakdown = _calculate_actual_damages(items)
        assert total == 17000.0
        assert breakdown["credit_denial"]["amount"] == 5000.0
        assert breakdown["higher_interest"]["amount"] == 2000.0
        assert breakdown["emotional_distress"]["amount"] == 10000.0

    def test_actual_damages_all_valid_categories(self):
        """Test that all valid damage categories are handled."""
        items = [
            {"type": "credit_denial", "amount": 1000, "description": "Test"},
            {"type": "higher_interest", "amount": 1000, "description": "Test"},
            {"type": "emotional_distress", "amount": 1000, "description": "Test"},
            {"type": "lost_employment", "amount": 1000, "description": "Test"},
            {"type": "medical_costs", "amount": 1000, "description": "Test"},
            {"type": "time_spent", "amount": 1000, "description": "Test"},
        ]
        total, breakdown = _calculate_actual_damages(items)
        assert total == 6000.0
        for cat in ["credit_denial", "higher_interest", "emotional_distress",
                    "lost_employment", "medical_costs", "time_spent"]:
            assert breakdown[cat]["amount"] == 1000.0

    def test_actual_damages_invalid_category_goes_to_other(self):
        """Test that invalid categories are placed in 'other'."""
        items = [
            {"type": "invalid_category", "amount": 500, "description": "Unknown damage"},
        ]
        total, breakdown = _calculate_actual_damages(items)
        assert total == 500.0
        assert breakdown["other"]["amount"] == 500.0

    def test_actual_damages_missing_type_goes_to_other(self):
        """Test that items without type go to 'other'."""
        items = [
            {"amount": 300, "description": "No type specified"},
        ]
        total, breakdown = _calculate_actual_damages(items)
        assert total == 300.0
        assert breakdown["other"]["amount"] == 300.0

    def test_actual_damages_formatted_amounts(self):
        """Test that breakdown includes formatted amounts."""
        items = [{"type": "credit_denial", "amount": 1234.56, "description": "Test"}]
        total, breakdown = _calculate_actual_damages(items)
        assert breakdown["credit_denial"]["formatted"] == "$1,234.56"
        assert breakdown["credit_denial"]["items"][0]["formatted"] == "$1,234.56"


# =============================================================================
# Tests for _calculate_punitive_damages()
# =============================================================================

class TestCalculatePunitiveDamages:
    """Test punitive damages calculation."""

    def test_punitive_damages_basic(self):
        """Test punitive damages multipliers (1x-3x statutory)."""
        punitive_low, punitive_high = _calculate_punitive_damages(1000, 5000)
        assert punitive_low == 1000.0  # 1x of low statutory
        assert punitive_high == 15000.0  # 3x of high statutory

    def test_punitive_damages_zero_statutory(self):
        """Test punitive damages when statutory is zero."""
        punitive_low, punitive_high = _calculate_punitive_damages(0, 0)
        assert punitive_low == 0.0
        assert punitive_high == 0.0

    def test_punitive_damages_large_statutory(self):
        """Test punitive damages for large statutory amounts."""
        punitive_low, punitive_high = _calculate_punitive_damages(10000, 100000)
        assert punitive_low == 10000.0  # 1x of low
        assert punitive_high == 300000.0  # 3x of high


# =============================================================================
# Tests for _calculate_attorney_fees()
# =============================================================================

class TestCalculateAttorneyFees:
    """Test attorney fees estimation."""

    def test_attorney_fees_30_percent(self):
        """Test attorney fees at 30% rate."""
        fees = _calculate_attorney_fees(10000, 0.30)
        assert fees == 3000.0

    def test_attorney_fees_40_percent(self):
        """Test attorney fees at 40% rate."""
        fees = _calculate_attorney_fees(10000, 0.40)
        assert fees == 4000.0

    def test_attorney_fees_zero_recovery(self):
        """Test attorney fees with zero recovery."""
        fees = _calculate_attorney_fees(0, 0.35)
        assert fees == 0.0

    def test_attorney_fees_large_recovery(self):
        """Test attorney fees on large recovery amount."""
        fees = _calculate_attorney_fees(1000000, 0.35)
        assert fees == 350000.0


# =============================================================================
# Tests for _determine_settlement_likelihood()
# =============================================================================

class TestDetermineSettlementLikelihood:
    """Test settlement likelihood determination."""

    def test_settlement_likelihood_high(self):
        """Test high settlement likelihood (>3 willful AND >$10k)."""
        likelihood = _determine_settlement_likelihood(5, 15000)
        assert likelihood == "high"

    def test_settlement_likelihood_high_boundary(self):
        """Test high likelihood at exact boundary (>3 willful AND >$10k)."""
        # At boundary - should NOT be high (needs > not >=)
        likelihood = _determine_settlement_likelihood(3, 10000)
        assert likelihood == "medium"  # Doesn't meet > requirements

    def test_settlement_likelihood_high_just_above_boundary(self):
        """Test high likelihood just above boundary."""
        likelihood = _determine_settlement_likelihood(4, 10001)
        assert likelihood == "high"

    def test_settlement_likelihood_medium_high_damages(self):
        """Test medium likelihood with high damages but few violations."""
        likelihood = _determine_settlement_likelihood(2, 8000)
        assert likelihood == "medium"

    def test_settlement_likelihood_medium_boundary(self):
        """Test medium likelihood at exact boundary (>$5k)."""
        likelihood = _determine_settlement_likelihood(1, 5001)
        assert likelihood == "medium"

    def test_settlement_likelihood_low(self):
        """Test low settlement likelihood."""
        likelihood = _determine_settlement_likelihood(1, 3000)
        assert likelihood == "low"

    def test_settlement_likelihood_low_at_boundary(self):
        """Test low likelihood at exact $5k boundary."""
        likelihood = _determine_settlement_likelihood(1, 5000)
        assert likelihood == "low"  # Needs > 5000, not >=

    def test_settlement_likelihood_zero_violations(self):
        """Test settlement likelihood with no violations."""
        likelihood = _determine_settlement_likelihood(0, 2000)
        assert likelihood == "low"

    def test_settlement_likelihood_many_violations_low_damages(self):
        """Test many willful violations but low damages."""
        likelihood = _determine_settlement_likelihood(10, 3000)
        assert likelihood == "low"


# =============================================================================
# Tests for _calculate_recommended_demand()
# =============================================================================

class TestCalculateRecommendedDemand:
    """Test recommended settlement demand calculation."""

    def test_recommended_demand_basic(self):
        """Test recommended demand calculation (2.5x expected value)."""
        demand = _calculate_recommended_demand(10000, 20000)
        expected_value = (10000 + 20000) / 2  # 15000
        assert demand == expected_value * 2.5  # 37500

    def test_recommended_demand_equal_low_high(self):
        """Test demand when low and high are equal."""
        demand = _calculate_recommended_demand(5000, 5000)
        assert demand == 5000 * 2.5  # 12500

    def test_recommended_demand_zero(self):
        """Test demand when totals are zero."""
        demand = _calculate_recommended_demand(0, 0)
        assert demand == 0.0

    def test_recommended_demand_large_amounts(self):
        """Test demand calculation for large amounts."""
        demand = _calculate_recommended_demand(100000, 500000)
        expected_value = (100000 + 500000) / 2  # 300000
        assert demand == expected_value * 2.5  # 750000


# =============================================================================
# Tests for calculate_settlement() - Full Integration
# =============================================================================

class TestCalculateSettlement:
    """Test the main settlement calculation function."""

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_calculate_settlement_basic(self, mock_save):
        """Test basic settlement calculation with all components."""
        mock_save.return_value = 1  # Mock estimate ID

        violations_data = {
            "total_violations": 5,
            "willful_violations": 3,
            "negligent_violations": 2,
            "actual_damages_items": [
                {"type": "credit_denial", "amount": 5000, "description": "Mortgage denial"},
            ],
        }

        result = calculate_settlement(
            case_id=1,
            client_id=1,
            violations_data=violations_data
        )

        assert result["success"] is True
        assert result["estimate_id"] == 1
        # 3 willful @ $100-$1000 each
        assert result["statutory_damages_low"] == 300.0
        assert result["statutory_damages_high"] == 3000.0
        assert result["actual_damages"] == 5000.0
        # Punitive: 1x-3x statutory
        assert result["punitive_damages_low"] == 300.0
        assert result["punitive_damages_high"] == 9000.0

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_calculate_settlement_no_violations(self, mock_save):
        """Test settlement calculation with no violations."""
        mock_save.return_value = 2

        violations_data = {
            "total_violations": 0,
            "willful_violations": 0,
            "negligent_violations": 0,
            "actual_damages_items": [],
        }

        result = calculate_settlement(
            case_id=None,
            client_id=1,
            violations_data=violations_data
        )

        assert result["success"] is True
        assert result["statutory_damages_low"] == 0.0
        assert result["statutory_damages_high"] == 0.0
        assert result["actual_damages"] == 0.0
        assert result["punitive_damages_low"] == 0.0
        assert result["punitive_damages_high"] == 0.0
        assert result["total_low"] == 0.0
        assert result["total_high"] == 0.0
        assert result["settlement_likelihood"] == "low"

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_calculate_settlement_max_violations(self, mock_save):
        """Test settlement calculation with many violations."""
        mock_save.return_value = 3

        violations_data = {
            "total_violations": 50,
            "willful_violations": 50,
            "negligent_violations": 0,
            "actual_damages_items": [
                {"type": "emotional_distress", "amount": 25000, "description": "Severe anxiety"},
                {"type": "lost_employment", "amount": 50000, "description": "Job loss"},
            ],
        }

        result = calculate_settlement(
            case_id=1,
            client_id=1,
            violations_data=violations_data
        )

        assert result["success"] is True
        # 50 willful @ $100-$1000 each
        assert result["statutory_damages_low"] == 5000.0
        assert result["statutory_damages_high"] == 50000.0
        assert result["actual_damages"] == 75000.0
        assert result["settlement_likelihood"] == "high"

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_calculate_settlement_only_negligent_violations(self, mock_save):
        """Test settlement with only negligent violations (no statutory damages)."""
        mock_save.return_value = 4

        violations_data = {
            "total_violations": 5,
            "willful_violations": 0,
            "negligent_violations": 5,
            "actual_damages_items": [
                {"type": "higher_interest", "amount": 3000, "description": "Higher rate"},
            ],
        }

        result = calculate_settlement(
            case_id=1,
            client_id=1,
            violations_data=violations_data
        )

        assert result["success"] is True
        # No statutory damages for negligent violations
        assert result["statutory_damages_low"] == 0.0
        assert result["statutory_damages_high"] == 0.0
        # But actual damages still apply
        assert result["actual_damages"] == 3000.0
        # Punitive also zero since based on statutory
        assert result["punitive_damages_low"] == 0.0
        assert result["punitive_damages_high"] == 0.0

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_calculate_settlement_formatted_output(self, mock_save):
        """Test that formatted currency strings are included."""
        mock_save.return_value = 5

        violations_data = {
            "total_violations": 2,
            "willful_violations": 2,
            "negligent_violations": 0,
            "actual_damages_items": [],
        }

        result = calculate_settlement(
            case_id=1,
            client_id=1,
            violations_data=violations_data
        )

        assert "formatted" in result
        assert result["formatted"]["statutory_low"] == "$200.00"
        assert result["formatted"]["statutory_high"] == "$2,000.00"

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_calculate_settlement_totals_calculation(self, mock_save):
        """Test that totals are correctly summed."""
        mock_save.return_value = 6

        violations_data = {
            "total_violations": 2,
            "willful_violations": 2,
            "negligent_violations": 0,
            "actual_damages_items": [
                {"type": "credit_denial", "amount": 1000, "description": "Test"},
            ],
        }

        result = calculate_settlement(
            case_id=1,
            client_id=1,
            violations_data=violations_data
        )

        # Manual calculation:
        # Statutory: low=200, high=2000
        # Actual: 1000
        # Punitive: low=200 (1x stat_low), high=6000 (3x stat_high)
        # Total low = 200 + 1000 + 200 = 1400
        # Total high = 2000 + 1000 + 6000 = 9000
        assert result["total_low"] == 1400.0
        assert result["total_high"] == 9000.0

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_calculate_settlement_attorney_fees(self, mock_save):
        """Test attorney fees calculation in settlement."""
        mock_save.return_value = 7

        violations_data = {
            "total_violations": 1,
            "willful_violations": 1,
            "negligent_violations": 0,
            "actual_damages_items": [],
        }

        result = calculate_settlement(
            case_id=1,
            client_id=1,
            violations_data=violations_data
        )

        # Total low = 100 + 0 + 100 = 200
        # Total high = 1000 + 0 + 3000 = 4000
        # Attorney fees low = 200 * 0.30 = 60
        # Attorney fees high = 4000 * 0.40 = 1600
        # Estimate = (60 + 1600) / 2 = 830
        assert result["attorney_fees_estimate"] == 830.0

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_calculate_settlement_calculation_notes(self, mock_save):
        """Test that calculation notes are generated."""
        mock_save.return_value = 8

        violations_data = {
            "total_violations": 3,
            "willful_violations": 2,
            "negligent_violations": 1,
            "actual_damages_items": [],
        }

        result = calculate_settlement(
            case_id=1,
            client_id=1,
            violations_data=violations_data
        )

        notes = result["calculation_notes"]
        assert "FCRA Settlement Calculation Summary" in notes
        assert "Willful violations: 2" in notes
        assert "Negligent violations: 1" in notes

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_calculate_settlement_missing_data(self, mock_save):
        """Test settlement calculation with missing/empty violations data."""
        mock_save.return_value = 9

        violations_data = {}  # Empty dict

        result = calculate_settlement(
            case_id=None,
            client_id=1,
            violations_data=violations_data
        )

        assert result["success"] is True
        assert result["statutory_damages_low"] == 0.0
        assert result["statutory_damages_high"] == 0.0
        assert result["actual_damages"] == 0.0


# =============================================================================
# Tests for _generate_calculation_notes()
# =============================================================================

class TestGenerateCalculationNotes:
    """Test calculation notes generation."""

    def test_generate_notes_structure(self):
        """Test that notes contain all required sections."""
        notes = _generate_calculation_notes(
            willful_violations=3,
            negligent_violations=2,
            statutory_low=300.0,
            statutory_high=3000.0,
            actual_damages=5000.0,
            punitive_low=300.0,
            punitive_high=9000.0,
            total_low=5600.0,
            total_high=17000.0,
            settlement_likelihood="high",
            recommended_demand=28250.0,
        )

        assert "FCRA Settlement Calculation Summary" in notes
        assert "VIOLATIONS:" in notes
        assert "STATUTORY DAMAGES" in notes
        assert "ACTUAL DAMAGES:" in notes
        assert "PUNITIVE DAMAGES" in notes
        assert "TOTAL RECOVERY RANGE:" in notes
        assert "SETTLEMENT LIKELIHOOD: HIGH" in notes
        assert "RECOMMENDED INITIAL DEMAND:" in notes

    def test_generate_notes_values(self):
        """Test that notes contain correct values."""
        notes = _generate_calculation_notes(
            willful_violations=5,
            negligent_violations=0,
            statutory_low=500.0,
            statutory_high=5000.0,
            actual_damages=10000.0,
            punitive_low=500.0,
            punitive_high=15000.0,
            total_low=11000.0,
            total_high=30000.0,
            settlement_likelihood="medium",
            recommended_demand=51250.0,
        )

        assert "Willful violations: 5" in notes
        assert "Negligent violations: 0" in notes
        assert "$500.00" in notes
        assert "$5,000.00" in notes
        assert "SETTLEMENT LIKELIHOOD: MEDIUM" in notes


# =============================================================================
# Edge Case and Integration Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_actual_damages_string_amount_conversion(self):
        """Test that string amounts are converted to float."""
        items = [{"type": "credit_denial", "amount": "5000", "description": "Test"}]
        total, breakdown = _calculate_actual_damages(items)
        assert total == 5000.0

    def test_actual_damages_missing_amount(self):
        """Test handling of missing amount field."""
        items = [{"type": "credit_denial", "description": "No amount"}]
        total, breakdown = _calculate_actual_damages(items)
        assert total == 0.0

    def test_actual_damages_missing_description(self):
        """Test handling of missing description field."""
        items = [{"type": "credit_denial", "amount": 1000}]
        total, breakdown = _calculate_actual_damages(items)
        assert total == 1000.0
        assert breakdown["credit_denial"]["items"][0]["description"] == ""

    @patch('services.settlement_calculator._save_settlement_estimate')
    def test_settlement_with_case_id_none(self, mock_save):
        """Test settlement calculation without a case ID (estimate only)."""
        mock_save.return_value = 10

        violations_data = {
            "total_violations": 1,
            "willful_violations": 1,
            "negligent_violations": 0,
            "actual_damages_items": [],
        }

        result = calculate_settlement(
            case_id=None,
            client_id=1,
            violations_data=violations_data
        )

        assert result["success"] is True
        # Verify mock was called with case_id=None
        call_kwargs = mock_save.call_args[1]
        assert call_kwargs["case_id"] is None
