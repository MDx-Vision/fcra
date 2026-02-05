"""
Unit tests for Litigation Tools

Tests cover:
- calculate_damages function
- calculate_case_score function
- assess_willfulness function
"""

import pytest
from unittest.mock import Mock, MagicMock


class TestCalculateDamagesBasic:
    """Tests for calculate_damages basic functionality"""

    def test_returns_dict(self):
        """Should return a dictionary"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {})

        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """Should have all required damage categories"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {})

        assert "actual" in result
        assert "statutory" in result
        assert "punitive" in result
        assert "attorney_fees" in result
        assert "settlement" in result

    def test_empty_violations(self):
        """Should handle empty violations list"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {})

        assert result["statutory"]["total"] == 0
        assert result["punitive"]["amount"] == 0


class TestCalculateDamagesActual:
    """Tests for actual damages calculation"""

    def test_calculates_credit_denials(self):
        """Should include credit denials in actual damages"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {"credit_denials": 5000})

        assert result["actual"]["credit_denials"] == 5000

    def test_calculates_higher_interest(self):
        """Should include higher interest in actual damages"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {"higher_interest": 2500})

        assert result["actual"]["higher_interest"] == 2500

    def test_calculates_credit_monitoring(self):
        """Should include credit monitoring in actual damages"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {"credit_monitoring": 300})

        assert result["actual"]["credit_monitoring"] == 300

    def test_calculates_time_stress(self):
        """Should include time/stress in actual damages"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {"time_stress": 1000})

        assert result["actual"]["time_stress"] == 1000

    def test_calculates_other(self):
        """Should include other damages"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {"other": 500})

        assert result["actual"]["other"] == 500

    def test_calculates_total(self):
        """Should calculate total actual damages"""
        from services.litigation_tools import calculate_damages

        damages = {
            "credit_denials": 5000,
            "higher_interest": 2500,
            "credit_monitoring": 300,
            "time_stress": 1000,
            "other": 500,
        }
        result = calculate_damages([], damages)

        assert result["actual"]["total"] == 9300

    def test_handles_missing_fields(self):
        """Should handle missing damage fields"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {"credit_denials": 1000})

        assert result["actual"]["credit_denials"] == 1000
        assert result["actual"]["higher_interest"] == 0
        assert result["actual"]["total"] == 1000


class TestCalculateDamagesStatutory:
    """Tests for statutory damages calculation"""

    def test_605b_violation(self):
        """Should calculate 605B statutory damages"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "605B", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["605b"]["count"] == 1
        assert result["statutory"]["605b"]["amount"] == 1000

    def test_605b_with_parentheses(self):
        """Should recognize 605(B) format"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "605(B)", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["605b"]["count"] == 1

    def test_1681c_violation(self):
        """Should recognize 1681c format"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "1681c", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["605b"]["count"] == 1

    def test_607_violation(self):
        """Should calculate 607 statutory damages"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "607", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["607b"]["count"] == 1
        assert result["statutory"]["607b"]["amount"] == 750

    def test_1681e_violation(self):
        """Should recognize 1681e format"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "1681e", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["607b"]["count"] == 1

    def test_611_violation(self):
        """Should calculate 611 statutory damages"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "611", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["611"]["count"] == 1
        assert result["statutory"]["611"]["amount"] == 750

    def test_1681i_violation(self):
        """Should recognize 1681i format"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "1681i", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["611"]["count"] == 1

    def test_623_violation(self):
        """Should calculate 623 statutory damages"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "623", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["623"]["count"] == 1
        assert result["statutory"]["623"]["amount"] == 750

    def test_1681s_violation(self):
        """Should recognize 1681s format"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "1681s", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["623"]["count"] == 1

    def test_multiple_violations(self):
        """Should count multiple violations"""
        from services.litigation_tools import calculate_damages

        violations = [
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "611", "is_willful": False},
        ]
        result = calculate_damages(violations, {})

        assert result["statutory"]["605b"]["count"] == 2
        assert result["statutory"]["605b"]["amount"] == 2000
        assert result["statutory"]["611"]["count"] == 1
        assert result["statutory"]["total"] == 2750

    def test_case_insensitive(self):
        """Should handle case insensitive section matching"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "605b", "is_willful": False}]
        result = calculate_damages(violations, {})

        assert result["statutory"]["605b"]["count"] == 1


class TestCalculateDamagesPunitive:
    """Tests for punitive damages calculation"""

    def test_no_willful_violations(self):
        """Should have zero punitive for no willful violations"""
        from services.litigation_tools import calculate_damages

        violations = [
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "605B", "is_willful": False},
        ]
        result = calculate_damages(violations, {})

        assert result["punitive"]["multiplier"] == 0
        assert result["punitive"]["amount"] == 0

    def test_low_willfulness_ratio(self):
        """Should apply multiplier 2 for 10-30% willfulness"""
        from services.litigation_tools import calculate_damages

        violations = [
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "605B", "is_willful": False},
        ]
        result = calculate_damages(violations, {})

        assert result["punitive"]["multiplier"] == 2

    def test_medium_willfulness_ratio(self):
        """Should apply multiplier 3 for 30-50% willfulness"""
        from services.litigation_tools import calculate_damages

        violations = [
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "605B", "is_willful": False},
        ]
        result = calculate_damages(violations, {})

        # 2/5 = 40% willful
        assert result["punitive"]["multiplier"] == 3

    def test_high_willfulness_ratio(self):
        """Should apply multiplier 4 for 50-70% willfulness"""
        from services.litigation_tools import calculate_damages

        violations = [
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "605B", "is_willful": False},
        ]
        result = calculate_damages(violations, {})

        # 3/5 = 60% willful
        assert result["punitive"]["multiplier"] == 4

    def test_very_high_willfulness_ratio(self):
        """Should apply multiplier 5 for 70%+ willfulness"""
        from services.litigation_tools import calculate_damages

        violations = [
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": True},
        ]
        result = calculate_damages(violations, {})

        # 4/4 = 100% willful
        assert result["punitive"]["multiplier"] == 5

    def test_punitive_amount_calculation(self):
        """Should calculate punitive amount correctly"""
        from services.litigation_tools import calculate_damages

        violations = [
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": True},
        ]
        result = calculate_damages(violations, {})

        # 2 violations = $2000 statutory, 100% willful = 5x multiplier
        assert result["punitive"]["amount"] == 2000 * 5


class TestCalculateDamagesAttorneyFees:
    """Tests for attorney fees calculation"""

    def test_small_case(self):
        """Should estimate 15 hours for < 5 violations"""
        from services.litigation_tools import calculate_damages

        violations = [
            {"fcra_section": "605B", "is_willful": False},
            {"fcra_section": "605B", "is_willful": False},
        ]
        result = calculate_damages(violations, {})

        assert result["attorney_fees"]["estimated_hours"] == 15
        assert result["attorney_fees"]["total"] == 15 * 250

    def test_medium_case(self):
        """Should estimate 25 hours for 5-9 violations"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "605B", "is_willful": False} for _ in range(7)]
        result = calculate_damages(violations, {})

        assert result["attorney_fees"]["estimated_hours"] == 25

    def test_large_case(self):
        """Should estimate 40 hours for 10-19 violations"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "605B", "is_willful": False} for _ in range(15)]
        result = calculate_damages(violations, {})

        assert result["attorney_fees"]["estimated_hours"] == 40

    def test_very_large_case(self):
        """Should estimate 60 hours for 20+ violations"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "605B", "is_willful": False} for _ in range(25)]
        result = calculate_damages(violations, {})

        assert result["attorney_fees"]["estimated_hours"] == 60

    def test_hourly_rate(self):
        """Should use $250 hourly rate"""
        from services.litigation_tools import calculate_damages

        result = calculate_damages([], {})

        assert result["attorney_fees"]["hourly_rate"] == 250


class TestCalculateDamagesSettlement:
    """Tests for settlement calculation"""

    def test_total_exposure(self):
        """Should calculate total exposure"""
        from services.litigation_tools import calculate_damages

        violations = [
            {"fcra_section": "605B", "is_willful": True},
            {"fcra_section": "605B", "is_willful": True},
        ]
        actual = {"credit_denials": 5000}
        result = calculate_damages(violations, actual)

        # actual + statutory + punitive + attorney
        expected_exposure = (
            5000  # actual
            + 2000  # statutory (2 x $1000)
            + 2000 * 5  # punitive (5x multiplier)
            + 15 * 250  # attorney fees
        )
        assert result["settlement"]["total_exposure"] == expected_exposure

    def test_target_settlement(self):
        """Should calculate target settlement at 65%"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "605B", "is_willful": False}]
        result = calculate_damages(violations, {})

        expected_target = result["settlement"]["total_exposure"] * 0.65
        assert result["settlement"]["target"] == expected_target

    def test_minimum_settlement(self):
        """Should calculate minimum settlement at 45%"""
        from services.litigation_tools import calculate_damages

        violations = [{"fcra_section": "605B", "is_willful": False}]
        result = calculate_damages(violations, {})

        expected_minimum = result["settlement"]["total_exposure"] * 0.45
        assert result["settlement"]["minimum"] == expected_minimum


class TestCalculateCaseScore:
    """Tests for calculate_case_score function"""

    def test_returns_dict(self):
        """Should return a dictionary"""
        from services.litigation_tools import calculate_case_score

        result = calculate_case_score({}, [], {}, False)

        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """Should have all required score categories"""
        from services.litigation_tools import calculate_case_score

        result = calculate_case_score({}, [], {}, False)

        assert "standing" in result
        assert "violation_quality" in result
        assert "willfulness" in result
        assert "documentation" in result
        assert "total" in result
        assert "settlement_probability" in result
        assert "case_strength" in result
        assert "recommendation" in result
        assert "notes" in result


class TestCaseScoreStanding:
    """Tests for standing score"""

    def test_concrete_harm(self):
        """Should score 3 for concrete harm"""
        from services.litigation_tools import calculate_case_score

        standing = {"has_concrete_harm": True}
        result = calculate_case_score(standing, [], {}, False)

        assert result["standing"] == 3

    def test_dissemination_only(self):
        """Should score 1 for dissemination without concrete harm"""
        from services.litigation_tools import calculate_case_score

        standing = {"has_dissemination": True, "has_concrete_harm": False}
        result = calculate_case_score(standing, [], {}, False)

        assert result["standing"] == 1

    def test_no_standing(self):
        """Should score 0 for no standing"""
        from services.litigation_tools import calculate_case_score

        standing = {}
        result = calculate_case_score(standing, [], {}, False)

        assert result["standing"] == 0


class TestCaseScoreViolationQuality:
    """Tests for violation quality score"""

    def test_impossible_contradiction(self):
        """Should score 4 for impossible contradictions"""
        from services.litigation_tools import calculate_case_score

        violations = [{"violation_type": "Impossible contradiction in dates"}]
        result = calculate_case_score({}, violations, {}, False)

        assert result["violation_quality"] == 4

    def test_reinsertion(self):
        """Should score 3 for reinsertion violations"""
        from services.litigation_tools import calculate_case_score

        violations = [{"violation_type": "Reinsertion after deletion"}]
        result = calculate_case_score({}, violations, {}, False)

        assert result["violation_quality"] == 3

    def test_identity_theft_block(self):
        """Should score 3 for identity theft block failures"""
        from services.litigation_tools import calculate_case_score

        violations = [{"violation_type": "Identity theft block failure"}]
        result = calculate_case_score({}, violations, {}, False)

        assert result["violation_quality"] == 3

    def test_generic_accuracy_multiple(self):
        """Should score 2 for multiple generic accuracy issues"""
        from services.litigation_tools import calculate_case_score

        violations = [
            {"violation_type": "Accuracy issue"},
            {"violation_type": "Incorrect balance"},
            {"violation_type": "Accuracy error"},
        ]
        result = calculate_case_score({}, violations, {}, False)

        assert result["violation_quality"] == 2

    def test_weak_violations(self):
        """Should score 1 for weak violations"""
        from services.litigation_tools import calculate_case_score

        violations = [{"violation_type": "Minor issue"}]
        result = calculate_case_score({}, violations, {}, False)

        assert result["violation_quality"] == 1

    def test_no_violations(self):
        """Should score 0 for no violations"""
        from services.litigation_tools import calculate_case_score

        result = calculate_case_score({}, [], {}, False)

        assert result["violation_quality"] == 0


class TestCaseScoreWillfulness:
    """Tests for willfulness score"""

    def test_high_willfulness(self):
        """Should score 2 for 50%+ willful violations"""
        from services.litigation_tools import calculate_case_score

        violations = [
            {"violation_type": "Test", "is_willful": True},
            {"violation_type": "Test", "is_willful": True},
            {"violation_type": "Test", "is_willful": False},
        ]
        result = calculate_case_score({}, violations, {}, False)

        assert result["willfulness"] == 2

    def test_medium_willfulness(self):
        """Should score 1 for 20-50% willful violations"""
        from services.litigation_tools import calculate_case_score

        violations = [
            {"violation_type": "Test", "is_willful": True},
            {"violation_type": "Test", "is_willful": False},
            {"violation_type": "Test", "is_willful": False},
            {"violation_type": "Test", "is_willful": False},
        ]
        result = calculate_case_score({}, violations, {}, False)

        assert result["willfulness"] == 1

    def test_low_willfulness(self):
        """Should score 0 for < 20% willful violations"""
        from services.litigation_tools import calculate_case_score

        violations = [
            {"violation_type": "Test", "is_willful": False},
            {"violation_type": "Test", "is_willful": False},
            {"violation_type": "Test", "is_willful": False},
            {"violation_type": "Test", "is_willful": False},
            {"violation_type": "Test", "is_willful": False},
        ]
        result = calculate_case_score({}, violations, {}, False)

        assert result["willfulness"] == 0


class TestCaseScoreDocumentation:
    """Tests for documentation score"""

    def test_complete_documentation(self):
        """Should score 1 for complete documentation"""
        from services.litigation_tools import calculate_case_score

        result = calculate_case_score({}, [], {}, documentation_complete=True)

        assert result["documentation"] == 1

    def test_incomplete_documentation(self):
        """Should score 0 for incomplete documentation"""
        from services.litigation_tools import calculate_case_score

        result = calculate_case_score({}, [], {}, documentation_complete=False)

        assert result["documentation"] == 0


class TestCaseScoreTotal:
    """Tests for total score and recommendations"""

    def test_excellent_case(self):
        """Should rate 8+ as excellent"""
        from services.litigation_tools import calculate_case_score

        standing = {"has_concrete_harm": True}
        violations = [
            {"violation_type": "Impossible contradiction", "is_willful": True},
            {"violation_type": "Test", "is_willful": True},
        ]
        result = calculate_case_score(standing, violations, {}, True)

        # 3 + 4 + 2 + 1 = 10
        assert result["total"] >= 8
        assert result["case_strength"] == "Excellent"
        assert result["settlement_probability"] == 0.85
        assert "ACCEPT" in result["recommendation"]

    def test_strong_case(self):
        """Should rate 6-7 as strong"""
        from services.litigation_tools import calculate_case_score

        standing = {"has_concrete_harm": True}
        violations = [
            {"violation_type": "Reinsertion", "is_willful": False},
            {"violation_type": "Test", "is_willful": False},
        ]
        result = calculate_case_score(standing, violations, {}, True)

        # 3 + 3 + 0 + 1 = 7
        assert 6 <= result["total"] <= 7
        assert result["case_strength"] == "Strong"
        assert result["settlement_probability"] == 0.75

    def test_decent_case(self):
        """Should rate 4-5 as decent"""
        from services.litigation_tools import calculate_case_score

        standing = {"has_concrete_harm": True}
        violations = [{"violation_type": "Test", "is_willful": False}]
        result = calculate_case_score(standing, violations, {}, False)

        # 3 + 1 + 0 + 0 = 4
        assert 4 <= result["total"] <= 5
        assert result["case_strength"] == "Decent"
        assert result["settlement_probability"] == 0.60

    def test_weak_case(self):
        """Should rate 2-3 as weak"""
        from services.litigation_tools import calculate_case_score

        standing = {"has_dissemination": True}
        violations = [{"violation_type": "Test", "is_willful": False}]
        result = calculate_case_score(standing, violations, {}, False)

        # 1 + 1 + 0 + 0 = 2
        assert 2 <= result["total"] <= 3
        assert result["case_strength"] == "Weak"
        assert result["settlement_probability"] == 0.40
        assert "REVIEW" in result["recommendation"]

    def test_very_weak_case(self):
        """Should rate < 2 as very weak"""
        from services.litigation_tools import calculate_case_score

        standing = {}
        violations = []
        result = calculate_case_score(standing, violations, {}, False)

        # 0 + 0 + 0 + 0 = 0
        assert result["total"] < 2
        assert result["case_strength"] == "Very Weak"
        assert result["settlement_probability"] == 0.20
        assert "REJECT" in result["recommendation"]


class TestAssessWillfulness:
    """Tests for assess_willfulness function"""

    def test_returns_dict(self):
        """Should return a dictionary"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness("Test", "Test")

        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """Should have required keys"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness("Test", "Test")

        assert "is_willful" in result
        assert "indicators" in result
        assert "level" in result

    def test_reinsertion_is_willful(self):
        """Should mark reinsertion as willful"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness("Item was reinserted", "Reinsertion violation")

        assert result["is_willful"] is True
        assert result["level"] == "Reckless Disregard"

    def test_metro2_contradiction_is_willful(self):
        """Should mark Metro 2 contradictions as willful"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness("Metro 2 data shows contradiction", "Accuracy")

        assert result["is_willful"] is True
        assert result["level"] == "Reckless Disregard"

    def test_ignored_disputes_is_willful(self):
        """Should mark ignored disputes as willful"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness("Bureau ignored multiple disputes", "Dispute failure")

        assert result["is_willful"] is True
        assert result["level"] == "Reckless Disregard"

    def test_failed_to_correct_is_willful(self):
        """Should mark failed corrections with proof as willful"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness(
            "Documented proof provided but failed to correct", "Accuracy"
        )

        assert result["is_willful"] is True
        assert result["level"] == "Reckless Disregard"

    def test_pattern_is_willful(self):
        """Should mark patterns as willful"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness("Pattern across multiple accounts", "Systemic failure")

        assert result["is_willful"] is True
        assert result["level"] == "Reckless Disregard"

    def test_default_is_negligence(self):
        """Should default to negligence"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness("Simple error", "Minor issue")

        assert result["is_willful"] is False
        assert result["level"] == "Negligence"

    def test_handles_none_description(self):
        """Should handle None description"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness(None, "Test")

        assert result["is_willful"] is False

    def test_handles_none_type(self):
        """Should handle None violation type"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness("Test", None)

        assert result["is_willful"] is False

    def test_case_insensitive(self):
        """Should match case insensitively"""
        from services.litigation_tools import assess_willfulness

        result = assess_willfulness("REINSERTION occurred", "test")

        assert result["is_willful"] is True
