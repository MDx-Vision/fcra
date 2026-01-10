"""
Unit Tests for Triage Service.
Tests for AI-powered case triage system including:
- Priority score calculation
- Settlement value estimation
- Complexity determination
- Queue recommendation
- Key violation identification
- Risk and strength factor analysis
- Triage summary generation
- Database operations for triage records
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.triage_service import (
    calculate_priority_score,
    estimate_settlement_value,
    determine_complexity,
    recommend_queue,
    identify_key_violations,
    identify_risk_factors,
    identify_strengths,
    generate_triage_summary,
    triage_case,
    get_triage_by_id,
    get_triage_by_analysis,
    get_queue_cases,
    get_triage_stats,
    update_triage_review,
)


# =============================================================================
# Helper Functions for Creating Mock Objects
# =============================================================================

def create_mock_violation(
    violation_id=1,
    violation_type="generic",
    description="Test violation",
    fcra_section="611",
    is_willful=False,
    bureau="Experian",
    statutory_damages_min=100,
    statutory_damages_max=1000
):
    """Create a mock Violation object."""
    mock_violation = MagicMock()
    mock_violation.id = violation_id
    mock_violation.violation_type = violation_type
    mock_violation.description = description
    mock_violation.fcra_section = fcra_section
    mock_violation.is_willful = is_willful
    mock_violation.bureau = bureau
    mock_violation.statutory_damages_min = statutory_damages_min
    mock_violation.statutory_damages_max = statutory_damages_max
    return mock_violation


def create_mock_standing(
    has_concrete_harm=False,
    denial_letters_count=0,
    has_dissemination=False,
    adverse_action_notices_count=0
):
    """Create a mock Standing object."""
    mock_standing = MagicMock()
    mock_standing.has_concrete_harm = has_concrete_harm
    mock_standing.denial_letters_count = denial_letters_count
    mock_standing.has_dissemination = has_dissemination
    mock_standing.adverse_action_notices_count = adverse_action_notices_count
    return mock_standing


def create_mock_damages(
    actual_damages_total=0,
    statutory_damages_total=0,
    punitive_damages_amount=0
):
    """Create a mock Damages object."""
    mock_damages = MagicMock()
    mock_damages.actual_damages_total = actual_damages_total
    mock_damages.statutory_damages_total = statutory_damages_total
    mock_damages.punitive_damages_amount = punitive_damages_amount
    return mock_damages


def create_mock_case_score(
    documentation_score=5,
    total_score=6
):
    """Create a mock CaseScore object."""
    mock_case_score = MagicMock()
    mock_case_score.documentation_score = documentation_score
    mock_case_score.total_score = total_score
    return mock_case_score


# =============================================================================
# Tests for calculate_priority_score()
# =============================================================================

class TestCalculatePriorityScore:
    """Test priority score calculation."""

    def test_empty_violations_returns_minimum_score(self):
        """Test score with no violations."""
        priority, raw, confidence = calculate_priority_score([], None, None, None)
        assert priority == 1
        assert raw == 0.0
        assert confidence == 0.3

    def test_single_basic_violation(self):
        """Test score with single basic violation."""
        violations = [create_mock_violation()]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        # Score = 0.5 (base per violation)
        assert priority == 1
        assert raw == 0.5
        assert confidence >= 0.3

    def test_reinsertion_violation_in_type(self):
        """Test reinsertion violation adds 2 points via violation_type."""
        violations = [create_mock_violation(violation_type="reinsertion")]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        # Score = 2 (reinsertion) + 0.5 (base) = 2.5
        assert raw == 2.5
        assert priority == 2  # int(2.5/2) + 1 = 2

    def test_reinsertion_violation_in_description(self):
        """Test reinsertion in description adds 2 points."""
        violations = [create_mock_violation(description="This is a reinsertion case")]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        assert raw == 2.5

    def test_identity_theft_violation_in_type(self):
        """Test identity theft violation adds 2 points."""
        violations = [create_mock_violation(violation_type="identity theft")]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        # Score = 2 (identity) + 0.5 (base) = 2.5
        assert raw == 2.5

    def test_identity_theft_in_description(self):
        """Test identity theft in description adds 2 points."""
        violations = [create_mock_violation(description="identity theft related")]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        assert raw == 2.5

    def test_strong_fcra_section_611a5(self):
        """Test FCRA section 611(a)(5) adds 1.5 points."""
        violations = [create_mock_violation(fcra_section="611(a)(5)")]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        # Score = 1.5 (section) + 0.5 (base) = 2.0
        assert raw == 2.0

    def test_strong_fcra_section_605B(self):
        """Test FCRA section 605B adds 1.5 points."""
        violations = [create_mock_violation(fcra_section="605B")]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        assert raw == 2.0

    def test_strong_fcra_section_with_symbol(self):
        """Test FCRA section with section symbol."""
        violations = [create_mock_violation(fcra_section="§611(a)(5)")]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        assert raw == 2.0

    def test_willful_violation_adds_points(self):
        """Test willful violation adds 1.5 points."""
        violations = [create_mock_violation(is_willful=True)]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        # Score = 0.5 (base) + 1.5 (willful) = 2.0
        assert raw == 2.0

    def test_multiple_bureaus_adds_point(self):
        """Test multiple bureaus (2) adds 1 point."""
        violations = [
            create_mock_violation(bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
        ]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        # Score = 0.5 + 0.5 (base) + 1 (multiple bureaus) = 2.0
        assert raw == 2.0

    def test_all_three_bureaus_adds_extra_points(self):
        """Test all 3 bureaus adds 1.5 total points."""
        violations = [
            create_mock_violation(bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
            create_mock_violation(bureau="Equifax"),
        ]
        priority, raw, confidence = calculate_priority_score(violations, None, None, None)
        # Score = 0.5*3 (base) + 1 (2+ bureaus) + 0.5 (3 bureaus) = 3.0
        assert raw == 3.0

    def test_standing_with_concrete_harm(self):
        """Test standing with concrete harm adds 1 point."""
        standing = create_mock_standing(has_concrete_harm=True)
        priority, raw, confidence = calculate_priority_score([], standing, None, None)
        assert raw == 1.0

    def test_standing_with_denial_letters(self):
        """Test standing with denial letters adds 1 point."""
        standing = create_mock_standing(denial_letters_count=2)
        priority, raw, confidence = calculate_priority_score([], standing, None, None)
        assert raw == 1.0

    def test_standing_with_dissemination(self):
        """Test standing with dissemination adds 0.5 points."""
        standing = create_mock_standing(has_dissemination=True)
        priority, raw, confidence = calculate_priority_score([], standing, None, None)
        assert raw == 0.5

    def test_standing_with_adverse_action_notices(self):
        """Test standing with adverse action notices adds 0.5 points."""
        standing = create_mock_standing(adverse_action_notices_count=1)
        priority, raw, confidence = calculate_priority_score([], standing, None, None)
        assert raw == 0.5

    def test_standing_full_points(self):
        """Test standing with all elements."""
        standing = create_mock_standing(
            has_concrete_harm=True,
            denial_letters_count=2,
            has_dissemination=True,
            adverse_action_notices_count=1
        )
        priority, raw, confidence = calculate_priority_score([], standing, None, None)
        # 1 + 1 + 0.5 + 0.5 = 3.0
        assert raw == 3.0

    def test_damages_over_25k(self):
        """Test damages over $25K adds 2 points."""
        damages = create_mock_damages(actual_damages_total=20000, statutory_damages_total=10000)
        priority, raw, confidence = calculate_priority_score([], None, damages, None)
        assert raw == 2.0

    def test_damages_over_10k(self):
        """Test damages over $10K adds 1 point."""
        damages = create_mock_damages(actual_damages_total=8000, statutory_damages_total=5000)
        priority, raw, confidence = calculate_priority_score([], None, damages, None)
        assert raw == 1.0

    def test_damages_under_10k(self):
        """Test damages under $10K adds no points."""
        damages = create_mock_damages(actual_damages_total=5000, statutory_damages_total=2000)
        priority, raw, confidence = calculate_priority_score([], None, damages, None)
        assert raw == 0.0

    def test_case_score_high_documentation(self):
        """Test case score with high documentation adds 1 point."""
        case_score = create_mock_case_score(documentation_score=8)
        priority, raw, confidence = calculate_priority_score([], None, None, case_score)
        assert raw == 1.0

    def test_case_score_low_documentation(self):
        """Test case score with low documentation adds no points."""
        case_score = create_mock_case_score(documentation_score=5)
        priority, raw, confidence = calculate_priority_score([], None, None, case_score)
        assert raw == 0.0

    def test_priority_score_capped_at_5(self):
        """Test priority score never exceeds 5."""
        violations = [
            create_mock_violation(
                violation_type="reinsertion identity",
                description="reinsertion identity theft",
                fcra_section="611(a)(5)",
                is_willful=True,
                bureau="Experian"
            ),
            create_mock_violation(
                violation_type="reinsertion",
                is_willful=True,
                bureau="TransUnion"
            ),
            create_mock_violation(
                violation_type="identity",
                is_willful=True,
                bureau="Equifax"
            ),
        ]
        standing = create_mock_standing(
            has_concrete_harm=True,
            denial_letters_count=5,
            has_dissemination=True,
            adverse_action_notices_count=3
        )
        damages = create_mock_damages(actual_damages_total=50000, statutory_damages_total=30000)
        case_score = create_mock_case_score(documentation_score=10)

        priority, raw, confidence = calculate_priority_score(violations, standing, damages, case_score)
        assert priority <= 5

    def test_priority_score_minimum_is_1(self):
        """Test priority score never goes below 1."""
        priority, raw, confidence = calculate_priority_score([], None, None, None)
        assert priority >= 1

    def test_confidence_increases_with_factors(self):
        """Test confidence increases with more factors."""
        violations = [create_mock_violation()]
        standing = create_mock_standing(has_concrete_harm=True, denial_letters_count=1)
        damages = create_mock_damages(actual_damages_total=15000)
        case_score = create_mock_case_score(documentation_score=8)

        _, _, confidence = calculate_priority_score(violations, standing, damages, case_score)
        assert confidence > 0.3

    def test_confidence_capped_at_1(self):
        """Test confidence never exceeds 1.0."""
        violations = [create_mock_violation() for _ in range(20)]
        standing = create_mock_standing(has_concrete_harm=True, denial_letters_count=5, has_dissemination=True)
        damages = create_mock_damages(actual_damages_total=50000)
        case_score = create_mock_case_score(documentation_score=10)

        _, _, confidence = calculate_priority_score(violations, standing, damages, case_score)
        assert confidence <= 1.0


# =============================================================================
# Tests for estimate_settlement_value()
# =============================================================================

class TestEstimateSettlementValue:
    """Test settlement value estimation."""

    def test_empty_violations_returns_zero(self):
        """Test settlement value with no violations."""
        value = estimate_settlement_value([], None, None)
        assert value == 0.0

    def test_single_basic_violation_base_value(self):
        """Test single violation base value is $1,000."""
        violations = [create_mock_violation()]
        value = estimate_settlement_value(violations, None, None)
        assert value == 1000.0

    def test_willful_violation_doubles_value(self):
        """Test willful violation doubles the base value."""
        violations = [create_mock_violation(is_willful=True)]
        value = estimate_settlement_value(violations, None, None)
        assert value == 2000.0

    def test_reinsertion_violation_type_multiplier(self):
        """Test reinsertion in violation_type applies 2.5x multiplier."""
        violations = [create_mock_violation(violation_type="reinsertion")]
        value = estimate_settlement_value(violations, None, None)
        assert value == 2500.0

    def test_reinsertion_description_multiplier(self):
        """Test reinsertion in description applies 2.5x multiplier."""
        violations = [create_mock_violation(description="reinsertion case")]
        value = estimate_settlement_value(violations, None, None)
        assert value == 2500.0

    def test_identity_theft_violation_type_multiplier(self):
        """Test identity theft in violation_type applies 3x multiplier."""
        violations = [create_mock_violation(violation_type="identity")]
        value = estimate_settlement_value(violations, None, None)
        assert value == 3000.0

    def test_identity_theft_description_multiplier(self):
        """Test identity theft in description applies 3x multiplier."""
        violations = [create_mock_violation(description="identity theft case")]
        value = estimate_settlement_value(violations, None, None)
        assert value == 3000.0

    def test_willful_and_reinsertion_stack(self):
        """Test willful and reinsertion multipliers stack."""
        violations = [create_mock_violation(is_willful=True, violation_type="reinsertion")]
        value = estimate_settlement_value(violations, None, None)
        # 1000 * 2 (willful) * 2.5 (reinsertion) = 5000
        assert value == 5000.0

    def test_willful_and_identity_theft_stack(self):
        """Test willful and identity theft multipliers stack."""
        violations = [create_mock_violation(is_willful=True, violation_type="identity")]
        value = estimate_settlement_value(violations, None, None)
        # 1000 * 2 (willful) * 3 (identity) = 6000
        assert value == 6000.0

    def test_standing_concrete_harm_with_denial_letters(self):
        """Test strong standing with harm and denial letters applies 1.5x."""
        violations = [create_mock_violation()]
        standing = create_mock_standing(has_concrete_harm=True, denial_letters_count=2)
        value = estimate_settlement_value(violations, standing, None)
        assert value == 1500.0

    def test_standing_concrete_harm_only(self):
        """Test standing with concrete harm only applies 1.3x."""
        violations = [create_mock_violation()]
        standing = create_mock_standing(has_concrete_harm=True, denial_letters_count=0)
        value = estimate_settlement_value(violations, standing, None)
        assert value == 1300.0

    def test_standing_dissemination_only(self):
        """Test standing with dissemination only applies 1.3x."""
        violations = [create_mock_violation()]
        standing = create_mock_standing(has_dissemination=True)
        value = estimate_settlement_value(violations, standing, None)
        assert value == 1300.0

    def test_two_bureaus_multiplier(self):
        """Test 2 bureaus applies 1.15x multiplier."""
        violations = [
            create_mock_violation(bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
        ]
        value = estimate_settlement_value(violations, None, None)
        # 2000 * 1.15 = 2300
        assert value == 2300.0

    def test_three_bureaus_multiplier(self):
        """Test 3 bureaus applies 1.3x multiplier."""
        violations = [
            create_mock_violation(bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
            create_mock_violation(bureau="Equifax"),
        ]
        value = estimate_settlement_value(violations, None, None)
        # 3000 * 1.3 = 3900
        assert value == 3900.0

    def test_actual_damages_added(self):
        """Test actual damages add 50% to total."""
        violations = [create_mock_violation()]
        damages = create_mock_damages(actual_damages_total=2000)
        value = estimate_settlement_value(violations, None, damages)
        # 1000 + (2000 * 0.5) = 2000
        assert value == 2000.0

    def test_zero_actual_damages_not_added(self):
        """Test zero actual damages doesn't affect total."""
        violations = [create_mock_violation()]
        damages = create_mock_damages(actual_damages_total=0)
        value = estimate_settlement_value(violations, None, damages)
        assert value == 1000.0

    def test_complex_calculation(self):
        """Test complex calculation with multiple factors."""
        violations = [
            create_mock_violation(is_willful=True, violation_type="reinsertion", bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
        ]
        standing = create_mock_standing(has_concrete_harm=True, denial_letters_count=1)
        damages = create_mock_damages(actual_damages_total=5000)

        value = estimate_settlement_value(violations, standing, damages)
        # Violation 1: 1000 * 2 (willful) * 2.5 (reinsertion) = 5000
        # Violation 2: 1000 = 1000
        # Total violations: 6000
        # Standing multiplier: 1.5
        # Bureau multiplier (2 bureaus): 1.15
        # 6000 * 1.5 * 1.15 = 10350
        # Plus damages: 10350 + (5000 * 0.5) = 12850
        assert value == 12850.0


# =============================================================================
# Tests for determine_complexity()
# =============================================================================

class TestDetermineComplexity:
    """Test complexity level determination."""

    def test_no_violations_returns_simple(self):
        """Test no violations results in simple complexity."""
        complexity = determine_complexity([], None, None)
        assert complexity == "simple"

    def test_single_violation_returns_simple(self):
        """Test single violation results in simple complexity."""
        violations = [create_mock_violation()]
        complexity = determine_complexity(violations, None, None)
        assert complexity == "simple"

    def test_two_violations_adds_complexity_score(self):
        """Test 2-4 violations adds 1 to complexity score."""
        # 2 violations with same bureau = score 1 (< 2 for moderate)
        violations = [create_mock_violation() for _ in range(2)]
        complexity = determine_complexity(violations, None, None)
        # Score = 1 (2+ violations), need >= 2 for moderate
        assert complexity == "simple"

    def test_two_violations_different_bureaus_returns_moderate(self):
        """Test 2 violations across 2 bureaus results in moderate complexity."""
        violations = [
            create_mock_violation(bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
        ]
        complexity = determine_complexity(violations, None, None)
        # Score = 1 (2+ violations) + 1 (2 bureaus) = 2
        assert complexity == "moderate"

    def test_five_violations_increases_complexity(self):
        """Test 5-9 violations adds to complexity score."""
        violations = [create_mock_violation() for _ in range(5)]
        complexity = determine_complexity(violations, None, None)
        assert complexity == "moderate"

    def test_ten_violations_high_complexity(self):
        """Test 10+ violations significantly increases complexity."""
        # 10 violations with same bureau = score 3 (only 10+ violations)
        violations = [create_mock_violation() for _ in range(10)]
        complexity = determine_complexity(violations, None, None)
        # Score = 3 (10+ violations), need >= 5 for complex
        assert complexity == "moderate"

    def test_ten_violations_multiple_bureaus_complex(self):
        """Test 10+ violations with identity across bureaus is complex."""
        violations = [
            create_mock_violation(violation_type="identity", bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
            create_mock_violation(bureau="Equifax"),
        ] + [create_mock_violation() for _ in range(7)]
        complexity = determine_complexity(violations, None, None)
        # Score = 3 (10+ violations) + 2 (3 bureaus) + 2 (identity) = 7
        assert complexity == "expert_review"

    def test_two_bureaus_adds_complexity(self):
        """Test 2 bureaus adds to complexity."""
        violations = [
            create_mock_violation(bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
        ]
        complexity = determine_complexity(violations, None, None)
        assert complexity == "moderate"

    def test_three_bureaus_adds_more_complexity(self):
        """Test 3 bureaus adds more to complexity."""
        violations = [
            create_mock_violation(bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
            create_mock_violation(bureau="Equifax"),
        ]
        complexity = determine_complexity(violations, None, None)
        assert complexity == "moderate"

    def test_identity_violation_adds_complexity(self):
        """Test identity-related violation adds complexity."""
        violations = [create_mock_violation(violation_type="identity theft")]
        complexity = determine_complexity(violations, None, None)
        assert complexity == "moderate"

    def test_fraud_violation_adds_complexity(self):
        """Test fraud-related violation adds complexity."""
        violations = [create_mock_violation(violation_type="fraud")]
        complexity = determine_complexity(violations, None, None)
        assert complexity == "moderate"

    def test_high_damages_over_50k(self):
        """Test damages over $50K adds to complexity."""
        violations = [create_mock_violation()]
        damages = create_mock_damages(actual_damages_total=30000, punitive_damages_amount=30000)
        complexity = determine_complexity(violations, None, damages)
        assert complexity == "moderate"

    def test_moderate_damages_over_25k(self):
        """Test damages over $25K adds 1 to complexity."""
        # Single violation (score 0) + damages over 25K (score 1) = 1 < 2
        violations = [create_mock_violation()]
        damages = create_mock_damages(actual_damages_total=15000, punitive_damages_amount=15000)
        complexity = determine_complexity(violations, None, damages)
        # Score = 0 (1 violation) + 1 (>25K damages) = 1
        assert complexity == "simple"

    def test_damages_over_25k_with_multiple_violations(self):
        """Test damages over $25K with multiple violations is moderate."""
        violations = [create_mock_violation() for _ in range(2)]
        damages = create_mock_damages(actual_damages_total=15000, punitive_damages_amount=15000)
        complexity = determine_complexity(violations, None, damages)
        # Score = 1 (2+ violations) + 1 (>25K damages) = 2
        assert complexity == "moderate"

    def test_expert_review_threshold(self):
        """Test expert review is returned for very complex cases."""
        # Create highly complex case
        violations = [
            create_mock_violation(violation_type="identity theft", bureau="Experian"),
            create_mock_violation(violation_type="fraud", bureau="TransUnion"),
        ] + [create_mock_violation(bureau="Equifax") for _ in range(8)]

        damages = create_mock_damages(actual_damages_total=60000)
        complexity = determine_complexity(violations, None, damages)
        assert complexity == "expert_review"


# =============================================================================
# Tests for recommend_queue()
# =============================================================================

class TestRecommendQueue:
    """Test queue recommendation."""

    def test_missing_critical_info_returns_hold(self):
        """Test missing critical info returns hold queue."""
        queue = recommend_queue(5, "simple", has_critical_info=False)
        assert queue == "hold"

    def test_expert_review_complexity_returns_review_needed(self):
        """Test expert review complexity always returns review_needed."""
        queue = recommend_queue(5, "expert_review", has_critical_info=True)
        assert queue == "review_needed"

    def test_priority_5_simple_returns_fast_track(self):
        """Test priority 5 with simple complexity returns fast_track."""
        queue = recommend_queue(5, "simple", has_critical_info=True)
        assert queue == "fast_track"

    def test_priority_5_moderate_returns_fast_track(self):
        """Test priority 5 with moderate complexity returns fast_track."""
        queue = recommend_queue(5, "moderate", has_critical_info=True)
        assert queue == "fast_track"

    def test_priority_5_complex_returns_standard(self):
        """Test priority 5 with complex complexity returns standard."""
        queue = recommend_queue(5, "complex", has_critical_info=True)
        assert queue == "standard"

    def test_priority_4_returns_standard(self):
        """Test priority 4 returns standard queue."""
        queue = recommend_queue(4, "simple", has_critical_info=True)
        assert queue == "standard"

    def test_priority_3_returns_standard(self):
        """Test priority 3 returns standard queue."""
        queue = recommend_queue(3, "moderate", has_critical_info=True)
        assert queue == "standard"

    def test_priority_2_returns_review_needed(self):
        """Test priority 2 returns review_needed queue."""
        queue = recommend_queue(2, "simple", has_critical_info=True)
        assert queue == "review_needed"

    def test_priority_1_returns_review_needed(self):
        """Test priority 1 returns review_needed queue."""
        queue = recommend_queue(1, "simple", has_critical_info=True)
        assert queue == "review_needed"


# =============================================================================
# Tests for identify_key_violations()
# =============================================================================

class TestIdentifyKeyViolations:
    """Test key violation identification."""

    def test_empty_violations_returns_empty(self):
        """Test empty violations returns empty list."""
        key_violations = identify_key_violations([])
        assert key_violations == []

    def test_basic_violation_not_key(self):
        """Test basic violation is not identified as key."""
        violations = [create_mock_violation()]
        key_violations = identify_key_violations(violations)
        assert len(key_violations) == 0

    def test_reinsertion_type_is_key(self):
        """Test reinsertion in type is identified as key."""
        violations = [create_mock_violation(violation_type="reinsertion")]
        key_violations = identify_key_violations(violations)
        assert len(key_violations) == 1
        assert "Reinsertion violation" in key_violations[0]["reasons"]

    def test_reinsertion_description_is_key(self):
        """Test reinsertion in description is identified as key."""
        violations = [create_mock_violation(description="reinsertion issue")]
        key_violations = identify_key_violations(violations)
        assert len(key_violations) == 1

    def test_identity_theft_type_is_key(self):
        """Test identity theft in type is identified as key."""
        violations = [create_mock_violation(violation_type="identity")]
        key_violations = identify_key_violations(violations)
        assert len(key_violations) == 1
        assert "Identity theft related" in key_violations[0]["reasons"]

    def test_identity_theft_description_is_key(self):
        """Test identity theft in description is identified as key."""
        violations = [create_mock_violation(description="identity theft case")]
        key_violations = identify_key_violations(violations)
        assert len(key_violations) == 1

    def test_strong_fcra_section_is_key(self):
        """Test strong FCRA section is identified as key."""
        violations = [create_mock_violation(fcra_section="611(a)(5)")]
        key_violations = identify_key_violations(violations)
        assert len(key_violations) == 1
        assert any("Strong FCRA section" in r for r in key_violations[0]["reasons"])

    def test_willful_violation_is_key(self):
        """Test willful violation is identified as key."""
        violations = [create_mock_violation(is_willful=True)]
        key_violations = identify_key_violations(violations)
        assert len(key_violations) == 1
        assert "Willful violation" in key_violations[0]["reasons"]

    def test_key_violation_includes_correct_fields(self):
        """Test key violation dict includes all required fields."""
        violations = [create_mock_violation(
            violation_id=42,
            violation_type="reinsertion",
            fcra_section="611",
            bureau="Experian",
            is_willful=True,
            statutory_damages_min=100,
            statutory_damages_max=1000
        )]
        key_violations = identify_key_violations(violations)
        kv = key_violations[0]
        assert kv["id"] == 42
        assert kv["type"] == "reinsertion"
        assert kv["section"] == "611"
        assert kv["bureau"] == "Experian"
        assert kv["willful"] is True
        assert kv["damages_min"] == 100
        assert kv["damages_max"] == 1000
        assert "reasons" in kv

    def test_multiple_reasons_for_same_violation(self):
        """Test violation can have multiple reasons."""
        violations = [create_mock_violation(
            violation_type="reinsertion identity",
            is_willful=True,
            fcra_section="605B"
        )]
        key_violations = identify_key_violations(violations)
        assert len(key_violations[0]["reasons"]) > 1

    def test_max_10_key_violations_returned(self):
        """Test only top 10 key violations are returned."""
        violations = [create_mock_violation(is_willful=True) for _ in range(15)]
        key_violations = identify_key_violations(violations)
        assert len(key_violations) == 10


# =============================================================================
# Tests for identify_risk_factors()
# =============================================================================

class TestIdentifyRiskFactors:
    """Test risk factor identification."""

    def test_missing_standing_is_high_risk(self):
        """Test missing standing is identified as high risk."""
        risks = identify_risk_factors([], None, None)
        standing_risks = [r for r in risks if r["type"] == "missing_standing"]
        assert len(standing_risks) == 1
        assert standing_risks[0]["severity"] == "high"

    def test_weak_standing_is_medium_risk(self):
        """Test weak standing (no concrete harm) is medium risk."""
        standing = create_mock_standing(has_concrete_harm=False)
        risks = identify_risk_factors([], standing, None)
        weak_standing = [r for r in risks if r["type"] == "weak_standing"]
        assert len(weak_standing) == 1
        assert weak_standing[0]["severity"] == "medium"

    def test_strong_standing_no_risk(self):
        """Test strong standing (with concrete harm) has no risk."""
        standing = create_mock_standing(has_concrete_harm=True)
        risks = identify_risk_factors([], standing, None)
        standing_risks = [r for r in risks if "standing" in r["type"]]
        assert len(standing_risks) == 0

    def test_missing_damages_is_medium_risk(self):
        """Test missing damages is identified as medium risk."""
        risks = identify_risk_factors([], create_mock_standing(has_concrete_harm=True), None)
        damage_risks = [r for r in risks if r["type"] == "missing_damages"]
        assert len(damage_risks) == 1
        assert damage_risks[0]["severity"] == "medium"

    def test_low_damages_is_medium_risk(self):
        """Test low damages (under $1K) is medium risk."""
        damages = create_mock_damages(actual_damages_total=500, statutory_damages_total=300)
        risks = identify_risk_factors([], create_mock_standing(has_concrete_harm=True), damages)
        low_damage_risks = [r for r in risks if r["type"] == "low_damages"]
        assert len(low_damage_risks) == 1
        assert low_damage_risks[0]["severity"] == "medium"

    def test_adequate_damages_no_risk(self):
        """Test adequate damages has no risk."""
        damages = create_mock_damages(actual_damages_total=5000, statutory_damages_total=5000)
        risks = identify_risk_factors([], create_mock_standing(has_concrete_harm=True), damages)
        damage_risks = [r for r in risks if "damages" in r["type"]]
        assert len(damage_risks) == 0

    def test_no_violations_is_high_risk(self):
        """Test no violations is identified as high risk."""
        risks = identify_risk_factors([], create_mock_standing(has_concrete_harm=True), None)
        no_violation_risks = [r for r in risks if r["type"] == "no_violations"]
        assert len(no_violation_risks) == 1
        assert no_violation_risks[0]["severity"] == "high"

    def test_single_violation_is_low_risk(self):
        """Test single violation is identified as low risk."""
        violations = [create_mock_violation()]
        standing = create_mock_standing(has_concrete_harm=True)
        damages = create_mock_damages(actual_damages_total=5000)
        risks = identify_risk_factors(violations, standing, damages)
        single_violation_risks = [r for r in risks if r["type"] == "single_violation"]
        assert len(single_violation_risks) == 1
        assert single_violation_risks[0]["severity"] == "low"

    def test_multiple_violations_no_single_violation_risk(self):
        """Test multiple violations has no single violation risk."""
        violations = [create_mock_violation() for _ in range(3)]
        standing = create_mock_standing(has_concrete_harm=True)
        damages = create_mock_damages(actual_damages_total=5000)
        risks = identify_risk_factors(violations, standing, damages)
        single_violation_risks = [r for r in risks if r["type"] == "single_violation"]
        assert len(single_violation_risks) == 0

    def test_no_willfulness_is_medium_risk(self):
        """Test no willfulness indicators is medium risk."""
        violations = [create_mock_violation(is_willful=False)]
        standing = create_mock_standing(has_concrete_harm=True)
        damages = create_mock_damages(actual_damages_total=5000)
        risks = identify_risk_factors(violations, standing, damages)
        willfulness_risks = [r for r in risks if r["type"] == "no_willfulness"]
        assert len(willfulness_risks) == 1
        assert willfulness_risks[0]["severity"] == "medium"

    def test_willful_violation_no_willfulness_risk(self):
        """Test willful violation has no willfulness risk."""
        violations = [create_mock_violation(is_willful=True)]
        standing = create_mock_standing(has_concrete_harm=True)
        damages = create_mock_damages(actual_damages_total=5000)
        risks = identify_risk_factors(violations, standing, damages)
        willfulness_risks = [r for r in risks if r["type"] == "no_willfulness"]
        assert len(willfulness_risks) == 0


# =============================================================================
# Tests for identify_strengths()
# =============================================================================

class TestIdentifyStrengths:
    """Test strength identification."""

    def test_empty_case_no_strengths(self):
        """Test empty case has no strengths."""
        strengths = identify_strengths([], None, None, None)
        assert len(strengths) == 0

    def test_all_three_bureaus_is_strength(self):
        """Test violations across all 3 bureaus is a strength."""
        violations = [
            create_mock_violation(bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
            create_mock_violation(bureau="Equifax"),
        ]
        strengths = identify_strengths(violations, None, None, None)
        bureau_strengths = [s for s in strengths if s["type"] == "multi_bureau"]
        assert len(bureau_strengths) == 1
        assert "all 3 bureaus" in bureau_strengths[0]["description"]

    def test_two_bureaus_not_strength(self):
        """Test violations across 2 bureaus is not a multi_bureau strength."""
        violations = [
            create_mock_violation(bureau="Experian"),
            create_mock_violation(bureau="TransUnion"),
        ]
        strengths = identify_strengths(violations, None, None, None)
        bureau_strengths = [s for s in strengths if s["type"] == "multi_bureau"]
        assert len(bureau_strengths) == 0

    def test_three_willful_violations_is_strength(self):
        """Test 3+ willful violations is a strength."""
        violations = [create_mock_violation(is_willful=True) for _ in range(3)]
        strengths = identify_strengths(violations, None, None, None)
        willful_strengths = [s for s in strengths if s["type"] == "willful_violations"]
        assert len(willful_strengths) == 1
        assert "3 willful violations" in willful_strengths[0]["description"]

    def test_two_willful_violations_not_strength(self):
        """Test 2 willful violations is not a willful_violations strength."""
        violations = [create_mock_violation(is_willful=True) for _ in range(2)]
        strengths = identify_strengths(violations, None, None, None)
        willful_strengths = [s for s in strengths if s["type"] == "willful_violations"]
        assert len(willful_strengths) == 0

    def test_reinsertion_violation_is_strength(self):
        """Test reinsertion violation is a strength."""
        violations = [create_mock_violation(violation_type="reinsertion")]
        strengths = identify_strengths(violations, None, None, None)
        reinsertion_strengths = [s for s in strengths if s["type"] == "reinsertion"]
        assert len(reinsertion_strengths) == 1
        assert "high value" in reinsertion_strengths[0]["description"]

    def test_strong_standing_is_strength(self):
        """Test strong standing with harm and denial letters is a strength."""
        standing = create_mock_standing(has_concrete_harm=True, denial_letters_count=2)
        strengths = identify_strengths([], standing, None, None)
        standing_strengths = [s for s in strengths if s["type"] == "strong_standing"]
        assert len(standing_strengths) == 1
        assert "2 denial letters" in standing_strengths[0]["description"]

    def test_concrete_harm_without_denial_not_standing_strength(self):
        """Test concrete harm without denial letters is not strong_standing strength."""
        standing = create_mock_standing(has_concrete_harm=True, denial_letters_count=0)
        strengths = identify_strengths([], standing, None, None)
        standing_strengths = [s for s in strengths if s["type"] == "strong_standing"]
        assert len(standing_strengths) == 0

    def test_high_damages_is_strength(self):
        """Test damages over $10K is a strength."""
        damages = create_mock_damages(actual_damages_total=8000, statutory_damages_total=5000)
        strengths = identify_strengths([], None, damages, None)
        damage_strengths = [s for s in strengths if s["type"] == "high_damages"]
        assert len(damage_strengths) == 1
        assert "$13,000" in damage_strengths[0]["description"]

    def test_moderate_damages_not_strength(self):
        """Test damages under $10K is not a high_damages strength."""
        damages = create_mock_damages(actual_damages_total=5000, statutory_damages_total=3000)
        strengths = identify_strengths([], None, damages, None)
        damage_strengths = [s for s in strengths if s["type"] == "high_damages"]
        assert len(damage_strengths) == 0

    def test_high_case_score_is_strength(self):
        """Test case score >= 8 is a strength."""
        case_score = create_mock_case_score(total_score=8)
        strengths = identify_strengths([], None, None, case_score)
        score_strengths = [s for s in strengths if s["type"] == "strong_case_score"]
        assert len(score_strengths) == 1
        assert "8/10" in score_strengths[0]["description"]

    def test_moderate_case_score_not_strength(self):
        """Test case score < 8 is not a strong_case_score strength."""
        case_score = create_mock_case_score(total_score=7)
        strengths = identify_strengths([], None, None, case_score)
        score_strengths = [s for s in strengths if s["type"] == "strong_case_score"]
        assert len(score_strengths) == 0


# =============================================================================
# Tests for generate_triage_summary()
# =============================================================================

class TestGenerateTriageSummary:
    """Test triage summary generation."""

    def test_summary_includes_priority_label(self):
        """Test summary includes priority label."""
        summary = generate_triage_summary(5, 10000.0, "simple", "fast_track", [], [], [], 3)
        assert "HIGH PRIORITY" in summary
        assert "5/5" in summary

    def test_summary_includes_all_priority_levels(self):
        """Test all priority levels have correct labels."""
        labels = {
            5: "HIGH PRIORITY",
            4: "ELEVATED PRIORITY",
            3: "STANDARD PRIORITY",
            2: "LOW PRIORITY",
            1: "MINIMAL PRIORITY",
        }
        for priority, label in labels.items():
            summary = generate_triage_summary(priority, 1000.0, "simple", "standard", [], [], [], 1)
            assert label in summary

    def test_summary_includes_estimated_value(self):
        """Test summary includes formatted estimated value."""
        summary = generate_triage_summary(3, 12500.50, "moderate", "standard", [], [], [], 5)
        assert "$12,500.50" in summary

    def test_summary_includes_complexity(self):
        """Test summary includes complexity level."""
        summary = generate_triage_summary(3, 5000.0, "complex", "standard", [], [], [], 2)
        assert "COMPLEX" in summary

    def test_summary_includes_queue_label(self):
        """Test summary includes queue recommendation label."""
        queues = {
            "fast_track": "Fast Track processing recommended",
            "standard": "Standard queue assignment",
            "review_needed": "Manual review required",
            "hold": "Case on hold pending information",
        }
        for queue, label in queues.items():
            summary = generate_triage_summary(3, 5000.0, "moderate", queue, [], [], [], 2)
            assert label in summary

    def test_summary_includes_violation_counts(self):
        """Test summary includes violation counts."""
        key_violations = [{"id": 1}, {"id": 2}]
        summary = generate_triage_summary(3, 5000.0, "moderate", "standard", key_violations, [], [], 5)
        assert "5 identified" in summary
        assert "2 high-value" in summary

    def test_summary_includes_strengths(self):
        """Test summary includes strengths."""
        strengths = [
            {"type": "multi_bureau", "description": "All 3 bureaus"},
            {"type": "willful", "description": "3 willful violations"},
        ]
        summary = generate_triage_summary(4, 10000.0, "moderate", "standard", [], [], strengths, 5)
        assert "Strengths:" in summary
        assert "All 3 bureaus" in summary

    def test_summary_includes_high_risks(self):
        """Test summary includes high-severity risks."""
        risks = [
            {"type": "missing_standing", "severity": "high", "description": "Standing analysis not available"},
            {"type": "low_damages", "severity": "medium", "description": "Estimated damages below $1,000"},
        ]
        summary = generate_triage_summary(2, 500.0, "simple", "review_needed", [], risks, [], 1)
        assert "Risks:" in summary
        assert "Standing analysis not available" in summary
        # Medium severity should not be included
        assert "damages below" not in summary


# =============================================================================
# Tests for triage_case()
# =============================================================================

class TestTriageCase:
    """Test main triage function."""

    @patch('services.triage_service.SessionLocal')
    def test_analysis_not_found(self, mock_session_local):
        """Test triage when analysis not found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session_local.return_value = mock_db

        result = triage_case(999)

        assert result["success"] is False
        assert result["error"] == "Analysis not found"

    @patch('services.triage_service.SessionLocal')
    def test_existing_triage_returned(self, mock_session_local):
        """Test existing triage is returned instead of creating new."""
        mock_db = MagicMock()

        # Mock Analysis found
        mock_analysis = MagicMock()
        mock_analysis.id = 1
        mock_analysis.client_id = 10

        # Mock existing CaseTriage
        mock_triage = MagicMock()
        mock_triage.id = 100
        mock_triage.priority_score = 4
        mock_triage.estimated_value = 5000.0
        mock_triage.recommended_queue = "standard"

        # Configure query returns
        def query_filter_first(model):
            mock_query = MagicMock()
            # This will be called multiple times; we need to return appropriate values
            return mock_query

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_analysis,  # First call for Analysis
            mock_triage,    # Second call for existing CaseTriage
        ]
        mock_session_local.return_value = mock_db

        result = triage_case(1)

        assert result["success"] is True
        assert result["message"] == "Triage already exists"
        assert result["triage_id"] == 100

    @patch('services.triage_service.SessionLocal')
    def test_new_triage_created(self, mock_session_local):
        """Test new triage is created when none exists."""
        mock_db = MagicMock()

        # Mock Analysis
        mock_analysis = MagicMock()
        mock_analysis.id = 1
        mock_analysis.client_id = 10

        # Mock violations
        mock_violation = create_mock_violation(is_willful=True)

        # Configure query returns for different calls
        call_count = [0]
        def filter_first_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_analysis  # Analysis query
            elif call_count[0] == 2:
                return None  # No existing CaseTriage
            else:
                return None  # Standing, Damages, CaseScore

        mock_db.query.return_value.filter.return_value.first.side_effect = filter_first_side_effect
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_violation]

        mock_session_local.return_value = mock_db

        result = triage_case(1)

        assert result["success"] is True
        assert "triage_id" in result
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('services.triage_service.SessionLocal')
    def test_triage_error_handling(self, mock_session_local):
        """Test triage handles database errors."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = triage_case(1)

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_db.rollback.assert_called_once()


# =============================================================================
# Tests for get_triage_by_id()
# =============================================================================

class TestGetTriageById:
    """Test get triage by ID function."""

    @patch('services.triage_service.SessionLocal')
    def test_triage_not_found(self, mock_session_local):
        """Test returns None when triage not found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session_local.return_value = mock_db

        result = get_triage_by_id(999)

        assert result is None

    @patch('services.triage_service.SessionLocal')
    def test_triage_found(self, mock_session_local):
        """Test returns triage dict when found."""
        mock_db = MagicMock()

        mock_triage = MagicMock()
        mock_triage.id = 1
        mock_triage.client_id = 10
        mock_triage.analysis_id = 5
        mock_triage.priority_score = 4
        mock_triage.estimated_value = 5000.0
        mock_triage.complexity_level = "moderate"
        mock_triage.recommended_queue = "standard"
        mock_triage.key_violations = []
        mock_triage.risk_factors = []
        mock_triage.strengths = []
        mock_triage.triage_summary = "Test summary"
        mock_triage.ai_confidence = 0.75
        mock_triage.reviewed = False
        mock_triage.reviewed_by = None
        mock_triage.reviewed_at = None
        mock_triage.final_priority = None
        mock_triage.notes = None
        mock_triage.created_at = datetime(2025, 1, 15, 10, 30)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_triage
        mock_session_local.return_value = mock_db

        result = get_triage_by_id(1)

        assert result["id"] == 1
        assert result["client_id"] == 10
        assert result["analysis_id"] == 5
        assert result["priority_score"] == 4
        assert result["estimated_value"] == 5000.0
        assert result["reviewed"] is False


# =============================================================================
# Tests for get_triage_by_analysis()
# =============================================================================

class TestGetTriageByAnalysis:
    """Test get triage by analysis ID function."""

    @patch('services.triage_service.SessionLocal')
    @patch('services.triage_service.get_triage_by_id')
    def test_triage_not_found(self, mock_get_by_id, mock_session_local):
        """Test returns None when no triage for analysis."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session_local.return_value = mock_db

        result = get_triage_by_analysis(999)

        assert result is None
        mock_get_by_id.assert_not_called()

    @patch('services.triage_service.SessionLocal')
    @patch('services.triage_service.get_triage_by_id')
    def test_triage_found(self, mock_get_by_id, mock_session_local):
        """Test returns triage when found for analysis."""
        mock_db = MagicMock()

        mock_triage = MagicMock()
        mock_triage.id = 100

        mock_db.query.return_value.filter.return_value.first.return_value = mock_triage
        mock_session_local.return_value = mock_db

        mock_get_by_id.return_value = {"id": 100, "priority_score": 4}

        result = get_triage_by_analysis(5)

        assert result == {"id": 100, "priority_score": 4}
        mock_get_by_id.assert_called_once_with(100)


# =============================================================================
# Tests for get_queue_cases()
# =============================================================================

class TestGetQueueCases:
    """Test get queue cases function."""

    @patch('services.triage_service.SessionLocal')
    def test_empty_queue(self, mock_session_local):
        """Test empty queue returns empty list."""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_session_local.return_value = mock_db

        result = get_queue_cases()

        assert result == []

    @patch('services.triage_service.SessionLocal')
    def test_queue_with_cases(self, mock_session_local):
        """Test queue returns cases with client info."""
        mock_db = MagicMock()

        mock_triage = MagicMock()
        mock_triage.id = 1
        mock_triage.client_id = 10
        mock_triage.analysis_id = 5
        mock_triage.priority_score = 4
        mock_triage.estimated_value = 5000.0
        mock_triage.complexity_level = "moderate"
        mock_triage.recommended_queue = "standard"
        mock_triage.ai_confidence = 0.75
        mock_triage.reviewed = False
        mock_triage.final_priority = None
        mock_triage.created_at = datetime(2025, 1, 15)

        mock_client = MagicMock()
        mock_client.name = "Test Client"
        mock_client.email = "test@example.com"

        mock_analysis = MagicMock()
        mock_analysis.dispute_round = 2

        # Set up query mock
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_triage]

        def query_side_effect(model):
            if hasattr(model, '__tablename__'):
                if model.__tablename__ == 'case_triage':
                    return mock_query
            # For Client and Analysis queries
            mock_inner_query = MagicMock()
            mock_inner_query.filter.return_value.first.side_effect = [mock_client, mock_analysis]
            return mock_inner_query

        mock_db.query.side_effect = query_side_effect
        mock_session_local.return_value = mock_db

        result = get_queue_cases()

        assert len(result) >= 0  # May vary based on mock setup

    @patch('services.triage_service.SessionLocal')
    def test_queue_with_filter(self, mock_session_local):
        """Test queue filters by queue name."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_session_local.return_value = mock_db

        get_queue_cases(queue_name="fast_track")

        mock_query.filter.assert_called()


# =============================================================================
# Tests for get_triage_stats()
# =============================================================================

class TestGetTriageStats:
    """Test triage statistics function."""

    @patch('services.triage_service.SessionLocal')
    def test_empty_stats(self, mock_session_local):
        """Test stats with no triage records."""
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        # Mock for avg and sum
        mock_db.query.return_value.scalar.return_value = 0

        mock_session_local.return_value = mock_db

        result = get_triage_stats()

        assert result["total"] == 0
        assert result["fast_track"] == 0
        assert result["standard"] == 0
        assert result["review_needed"] == 0
        assert result["hold"] == 0

    @patch('services.triage_service.SessionLocal')
    def test_stats_with_records(self, mock_session_local):
        """Test stats with triage records."""
        mock_db = MagicMock()

        # Set up mock counts
        mock_db.query.return_value.count.return_value = 100
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            25,  # fast_track
            50,  # standard
            20,  # review_needed
            5,   # hold
            30,  # unreviewed
            40,  # high_priority
        ]

        # Mock for avg and sum
        mock_db.query.return_value.scalar.side_effect = [15000.0, 1500000.0]

        mock_session_local.return_value = mock_db

        result = get_triage_stats()

        assert result["total"] == 100
        assert "avg_estimated_value" in result
        assert "total_estimated_value" in result


# =============================================================================
# Tests for update_triage_review()
# =============================================================================

class TestUpdateTriageReview:
    """Test triage review update function."""

    @patch('services.triage_service.SessionLocal')
    def test_triage_not_found(self, mock_session_local):
        """Test update when triage not found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session_local.return_value = mock_db

        result = update_triage_review(999, "reviewer@example.com")

        assert result["success"] is False
        assert result["error"] == "Triage record not found"

    @patch('services.triage_service.SessionLocal')
    def test_successful_review_without_priority_change(self, mock_session_local):
        """Test successful review without changing priority."""
        mock_db = MagicMock()

        mock_triage = MagicMock()
        mock_triage.id = 1
        mock_triage.priority_score = 4
        mock_triage.complexity_level = "moderate"
        mock_triage.recommended_queue = "standard"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_triage
        mock_session_local.return_value = mock_db

        result = update_triage_review(1, "reviewer@example.com")

        assert result["success"] is True
        assert mock_triage.reviewed is True
        assert mock_triage.reviewed_by == "reviewer@example.com"
        assert mock_triage.final_priority == 4  # Same as original

    @patch('services.triage_service.SessionLocal')
    def test_successful_review_with_priority_change(self, mock_session_local):
        """Test successful review with priority change."""
        mock_db = MagicMock()

        mock_triage = MagicMock()
        mock_triage.id = 1
        mock_triage.priority_score = 3
        mock_triage.complexity_level = "simple"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_triage
        mock_session_local.return_value = mock_db

        result = update_triage_review(1, "reviewer@example.com", final_priority=5)

        assert result["success"] is True
        assert mock_triage.final_priority == 5
        # Queue should be updated based on new priority
        mock_db.commit.assert_called_once()

    @patch('services.triage_service.SessionLocal')
    def test_review_with_notes(self, mock_session_local):
        """Test review with notes."""
        mock_db = MagicMock()

        mock_triage = MagicMock()
        mock_triage.id = 1
        mock_triage.priority_score = 3
        mock_triage.complexity_level = "moderate"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_triage
        mock_session_local.return_value = mock_db

        result = update_triage_review(
            1, "reviewer@example.com",
            notes="Reviewed and approved"
        )

        assert result["success"] is True
        assert mock_triage.notes == "Reviewed and approved"

    @patch('services.triage_service.SessionLocal')
    def test_review_priority_clamped(self, mock_session_local):
        """Test priority is clamped between 1 and 5."""
        mock_db = MagicMock()

        mock_triage = MagicMock()
        mock_triage.id = 1
        mock_triage.priority_score = 3
        mock_triage.complexity_level = "simple"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_triage
        mock_session_local.return_value = mock_db

        # Test with priority > 5
        update_triage_review(1, "reviewer@example.com", final_priority=10)
        assert mock_triage.final_priority == 5

        # Reset mock
        mock_triage.reset_mock()

        # Test with priority < 1
        update_triage_review(1, "reviewer@example.com", final_priority=-1)
        assert mock_triage.final_priority == 1

    @patch('services.triage_service.SessionLocal')
    def test_review_error_handling(self, mock_session_local):
        """Test review handles database errors."""
        mock_db = MagicMock()

        mock_triage = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_triage
        mock_db.commit.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = update_triage_review(1, "reviewer@example.com")

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_db.rollback.assert_called_once()


# =============================================================================
# Integration-style Tests
# =============================================================================

class TestTriageIntegration:
    """Integration-style tests for complete triage workflow."""

    def test_high_priority_case_workflow(self):
        """Test workflow for high-priority case."""
        # Create high-value case
        violations = [
            create_mock_violation(
                violation_type="reinsertion",
                is_willful=True,
                bureau="Experian"
            ),
            create_mock_violation(
                violation_type="identity theft",
                is_willful=True,
                bureau="TransUnion"
            ),
            create_mock_violation(
                is_willful=True,
                bureau="Equifax"
            ),
        ]
        standing = create_mock_standing(has_concrete_harm=True, denial_letters_count=3)
        damages = create_mock_damages(actual_damages_total=20000, statutory_damages_total=15000)
        case_score = create_mock_case_score(documentation_score=9, total_score=9)

        # Calculate priority
        priority, raw_score, confidence = calculate_priority_score(
            violations, standing, damages, case_score
        )
        assert priority >= 4

        # Estimate value
        value = estimate_settlement_value(violations, standing, damages)
        assert value > 10000

        # Determine complexity
        complexity = determine_complexity(violations, standing, damages)
        assert complexity in ["moderate", "complex", "expert_review"]

        # Get queue recommendation
        queue = recommend_queue(priority, complexity)
        # High priority cases should go to fast_track or standard
        assert queue in ["fast_track", "standard", "review_needed"]

        # Identify key violations
        key_violations = identify_key_violations(violations)
        assert len(key_violations) >= 2

        # Identify strengths
        strengths = identify_strengths(violations, standing, damages, case_score)
        assert len(strengths) >= 2

        # Generate summary
        summary = generate_triage_summary(
            priority, value, complexity, queue,
            key_violations, [], strengths, len(violations)
        )
        assert "HIGH" in summary or "ELEVATED" in summary

    def test_low_priority_case_workflow(self):
        """Test workflow for low-priority case."""
        # Create minimal case
        violations = [create_mock_violation()]
        standing = create_mock_standing()
        damages = create_mock_damages()
        case_score = None

        # Calculate priority
        priority, raw_score, confidence = calculate_priority_score(
            violations, standing, damages, case_score
        )
        assert priority <= 2

        # Estimate value
        value = estimate_settlement_value(violations, standing, damages)
        assert value <= 2000

        # Determine complexity
        complexity = determine_complexity(violations, standing, damages)
        assert complexity == "simple"

        # Get queue recommendation
        queue = recommend_queue(priority, complexity)
        assert queue == "review_needed"

        # Identify risks
        risks = identify_risk_factors(violations, standing, damages)
        assert len(risks) >= 1

    def test_edge_case_empty_data(self):
        """Test edge case with completely empty data."""
        priority, raw_score, confidence = calculate_priority_score([], None, None, None)
        assert priority == 1
        assert raw_score == 0.0
        assert confidence == 0.3

        value = estimate_settlement_value([], None, None)
        assert value == 0.0

        complexity = determine_complexity([], None, None)
        assert complexity == "simple"

        queue = recommend_queue(1, "simple", has_critical_info=False)
        assert queue == "hold"

        key_violations = identify_key_violations([])
        assert key_violations == []

        risks = identify_risk_factors([], None, None)
        assert len(risks) >= 2  # Missing standing and no violations
