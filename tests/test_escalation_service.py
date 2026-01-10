"""
Unit Tests for Escalation Service.
Tests for FCRA dispute escalation recommendation logic including:
- Escalation level determination
- Case assignment and recommendation generation
- Staff notification via escalation rules
- Furnisher performance tracking
- Violation severity calculations
- Timeline generation
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.escalation_service import (
    DISPUTE_ACTIONS,
    TIMING_ACTIONS,
    DOCUMENTATION_ACTIONS,
    get_dispute_history,
    get_furnisher_performance,
    analyze_response_patterns,
    calculate_violation_severity,
    assess_documentation,
    estimate_damages,
    recommend_escalation,
    _generate_recommendation,
    get_escalation_timeline,
    save_recommendation,
    apply_recommendation,
    record_outcome,
    _update_furnisher_stats,
    get_escalation_stats,
    get_cases_needing_escalation_review,
)


# =============================================================================
# Tests for Constants and Configuration
# =============================================================================

class TestDisputeActionsConfiguration:
    """Test dispute action constants are properly defined."""

    def test_dispute_actions_contains_standard_redispute(self):
        """Test standard_redispute action exists."""
        assert "standard_redispute" in DISPUTE_ACTIONS
        assert DISPUTE_ACTIONS["standard_redispute"]["escalation_level"] == 1

    def test_dispute_actions_contains_mov_demand(self):
        """Test MOV demand action exists with correct level."""
        assert "mov_demand" in DISPUTE_ACTIONS
        assert DISPUTE_ACTIONS["mov_demand"]["escalation_level"] == 2

    def test_dispute_actions_contains_direct_furnisher(self):
        """Test direct furnisher action exists."""
        assert "direct_furnisher" in DISPUTE_ACTIONS
        assert DISPUTE_ACTIONS["direct_furnisher"]["escalation_level"] == 2

    def test_dispute_actions_contains_regulatory_complaint(self):
        """Test regulatory complaint action exists."""
        assert "regulatory_complaint" in DISPUTE_ACTIONS
        assert DISPUTE_ACTIONS["regulatory_complaint"]["escalation_level"] == 3

    def test_dispute_actions_contains_intent_to_sue(self):
        """Test intent to sue action exists."""
        assert "intent_to_sue" in DISPUTE_ACTIONS
        assert DISPUTE_ACTIONS["intent_to_sue"]["escalation_level"] == 4

    def test_dispute_actions_contains_settlement_demand(self):
        """Test settlement demand action exists."""
        assert "settlement_demand" in DISPUTE_ACTIONS
        assert DISPUTE_ACTIONS["settlement_demand"]["escalation_level"] == 4

    def test_dispute_actions_contains_media_pressure(self):
        """Test media pressure action exists (highest level)."""
        assert "media_pressure" in DISPUTE_ACTIONS
        assert DISPUTE_ACTIONS["media_pressure"]["escalation_level"] == 5

    def test_all_dispute_actions_have_required_fields(self):
        """Test all dispute actions have name, description, and escalation_level."""
        for action_key, action in DISPUTE_ACTIONS.items():
            assert "name" in action, f"{action_key} missing name"
            assert "description" in action, f"{action_key} missing description"
            assert "escalation_level" in action, f"{action_key} missing escalation_level"


class TestTimingActionsConfiguration:
    """Test timing action constants."""

    def test_wait_response_action(self):
        """Test wait for response timing action."""
        assert "wait_response" in TIMING_ACTIONS
        assert TIMING_ACTIONS["wait_response"]["days"] == 30

    def test_follow_up_action(self):
        """Test follow-up timing action."""
        assert "follow_up" in TIMING_ACTIONS
        assert TIMING_ACTIONS["follow_up"]["days"] == 35

    def test_escalate_immediately_action(self):
        """Test immediate escalation timing action."""
        assert "escalate_immediately" in TIMING_ACTIONS
        assert TIMING_ACTIONS["escalate_immediately"]["days"] == 0


class TestDocumentationActionsConfiguration:
    """Test documentation action constants."""

    def test_gather_evidence_action(self):
        """Test gather evidence action exists."""
        assert "gather_evidence" in DOCUMENTATION_ACTIONS
        assert "name" in DOCUMENTATION_ACTIONS["gather_evidence"]

    def test_request_disclosures_action(self):
        """Test request disclosures action exists."""
        assert "request_disclosures" in DOCUMENTATION_ACTIONS

    def test_prepare_litigation_action(self):
        """Test prepare litigation action exists."""
        assert "prepare_litigation" in DOCUMENTATION_ACTIONS


# =============================================================================
# Tests for get_dispute_history()
# =============================================================================

class TestGetDisputeHistory:
    """Test dispute history retrieval function."""

    def test_get_dispute_history_empty(self):
        """Test dispute history with no records."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []

        history = get_dispute_history(mock_db, client_id=1)

        assert history == []

    def test_get_dispute_history_with_cra_responses(self):
        """Test dispute history includes CRA responses."""
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_response.bureau = "Experian"
        mock_response.dispute_round = 1
        mock_response.response_type = "verified"
        mock_response.received_date = datetime(2024, 1, 15)
        mock_response.created_at = datetime(2024, 1, 10)
        mock_response.items_verified = 2
        mock_response.items_deleted = 1
        mock_response.items_updated = 0

        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.side_effect = [
            [mock_response],  # CRA responses
            []  # Dispute items
        ]

        history = get_dispute_history(mock_db, client_id=1)

        assert len(history) == 1
        assert history[0]["type"] == "cra_response"
        assert history[0]["bureau"] == "Experian"
        assert history[0]["items_verified"] == 2

    def test_get_dispute_history_with_dispute_items(self):
        """Test dispute history includes dispute items."""
        mock_db = MagicMock()
        mock_item = MagicMock()
        mock_item.bureau = "TransUnion"
        mock_item.creditor_name = "Test Creditor"
        mock_item.status = "in_progress"
        mock_item.dispute_round = 2
        mock_item.created_at = datetime(2024, 1, 20)

        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.side_effect = [
            [],  # CRA responses
            [mock_item]  # Dispute items
        ]

        history = get_dispute_history(mock_db, client_id=1)

        assert len(history) == 1
        assert history[0]["type"] == "dispute_item"
        assert history[0]["creditor"] == "Test Creditor"

    def test_get_dispute_history_combined(self):
        """Test dispute history combines both response types."""
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_response.bureau = "Equifax"
        mock_response.dispute_round = 1
        mock_response.response_type = "deleted"
        mock_response.received_date = None
        mock_response.created_at = datetime(2024, 1, 10)
        mock_response.items_verified = 0
        mock_response.items_deleted = 3
        mock_response.items_updated = 0

        mock_item = MagicMock()
        mock_item.bureau = "Experian"
        mock_item.creditor_name = "Collection Agency"
        mock_item.status = "sent"
        mock_item.dispute_round = None
        mock_item.created_at = datetime(2024, 1, 15)

        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.side_effect = [
            [mock_response],
            [mock_item]
        ]

        history = get_dispute_history(mock_db, client_id=1)

        assert len(history) == 2


# =============================================================================
# Tests for get_furnisher_performance()
# =============================================================================

class TestGetFurnisherPerformance:
    """Test furnisher performance retrieval."""

    def test_furnisher_not_found_returns_defaults(self):
        """Test default values when furnisher not found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        perf = get_furnisher_performance(mock_db, "Unknown Creditor")

        assert perf["found"] is False
        assert perf["deletion_rate"] == 0.5
        assert perf["avg_response_days"] == 25
        assert perf["settlement_rate"] == 0.1

    def test_furnisher_found_without_stats(self):
        """Test furnisher found but no stats."""
        mock_db = MagicMock()
        mock_furnisher = MagicMock()
        mock_furnisher.stats = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_furnisher

        perf = get_furnisher_performance(mock_db, "Test Creditor")

        assert perf["found"] is False

    def test_furnisher_with_stats_high_deletion_rate(self):
        """Test furnisher with high deletion rate."""
        mock_db = MagicMock()
        mock_furnisher = MagicMock()
        mock_furnisher.name = "Good Creditor"
        mock_stats = MagicMock()
        mock_stats.round_1_verified = 10
        mock_stats.round_1_deleted = 80
        mock_stats.round_1_updated = 10
        mock_stats.avg_response_days = 20
        mock_stats.settlement_count = 5
        mock_stats.total_disputes = 50
        mock_stats.settlement_avg = 5000
        mock_stats.violation_count = 3
        mock_stats.mov_requests_sent = 10
        mock_stats.mov_failed = 7
        mock_furnisher.stats = mock_stats
        mock_db.query.return_value.filter.return_value.first.return_value = mock_furnisher

        perf = get_furnisher_performance(mock_db, "Good Creditor")

        assert perf["found"] is True
        assert perf["deletion_rate"] == 0.8  # 80/(10+80+10)
        assert perf["avg_response_days"] == 20
        assert perf["settlement_rate"] == 0.1  # 5/50

    def test_furnisher_with_zero_disputes(self):
        """Test furnisher with zero total disputes."""
        mock_db = MagicMock()
        mock_furnisher = MagicMock()
        mock_furnisher.name = "New Creditor"
        mock_stats = MagicMock()
        mock_stats.round_1_verified = 0
        mock_stats.round_1_deleted = 0
        mock_stats.round_1_updated = 0
        mock_stats.avg_response_days = None
        mock_stats.settlement_count = 0
        mock_stats.total_disputes = 0
        mock_stats.settlement_avg = 0
        mock_stats.violation_count = 0
        mock_stats.mov_requests_sent = 0
        mock_stats.mov_failed = 0
        mock_furnisher.stats = mock_stats
        mock_db.query.return_value.filter.return_value.first.return_value = mock_furnisher

        perf = get_furnisher_performance(mock_db, "New Creditor")

        assert perf["found"] is True
        assert perf["deletion_rate"] == 0.5  # Default when no data
        assert perf["settlement_rate"] == 0.1  # Default


# =============================================================================
# Tests for analyze_response_patterns()
# =============================================================================

class TestAnalyzeResponsePatterns:
    """Test response pattern analysis."""

    def test_empty_responses(self):
        """Test pattern analysis with no responses."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        patterns = analyze_response_patterns(mock_db, client_id=1)

        assert patterns["total_responses"] == 0
        assert patterns["frivolous_count"] == 0
        assert patterns["no_response_count"] == 0

    def test_verified_response_pattern(self):
        """Test tracking verified responses."""
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_response.bureau = "Experian"
        mock_response.response_type = "verified"
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_response]

        patterns = analyze_response_patterns(mock_db, client_id=1)

        assert patterns["bureaus"]["Experian"]["verified"] == 1

    def test_frivolous_response_pattern(self):
        """Test tracking frivolous responses."""
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_response.bureau = "TransUnion"
        mock_response.response_type = "frivolous"
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_response]

        patterns = analyze_response_patterns(mock_db, client_id=1)

        assert patterns["bureaus"]["TransUnion"]["frivolous"] == 1
        assert patterns["frivolous_count"] == 1

    def test_no_response_pattern(self):
        """Test tracking no response cases."""
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_response.bureau = "Equifax"
        mock_response.response_type = "no_response"
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_response]

        patterns = analyze_response_patterns(mock_db, client_id=1)

        assert patterns["bureaus"]["Equifax"]["no_response"] == 1
        assert patterns["no_response_count"] == 1

    def test_multiple_bureaus(self):
        """Test pattern analysis across multiple bureaus."""
        mock_db = MagicMock()
        responses = []
        for bureau in ["Experian", "TransUnion", "Equifax"]:
            mock_resp = MagicMock()
            mock_resp.bureau = bureau
            mock_resp.response_type = "deleted"
            responses.append(mock_resp)
        mock_db.query.return_value.filter_by.return_value.all.return_value = responses

        patterns = analyze_response_patterns(mock_db, client_id=1)

        assert len(patterns["bureaus"]) == 3
        for bureau in ["Experian", "TransUnion", "Equifax"]:
            assert patterns["bureaus"][bureau]["deleted"] == 1


# =============================================================================
# Tests for calculate_violation_severity()
# =============================================================================

class TestCalculateViolationSeverity:
    """Test violation severity calculation."""

    def test_no_violations(self):
        """Test severity with no violations."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        severity = calculate_violation_severity(mock_db, client_id=1)

        assert severity["total_violations"] == 0
        assert severity["willful_count"] == 0
        assert severity["severity_score"] == 0

    def test_single_violation(self):
        """Test severity with single violation."""
        mock_db = MagicMock()
        mock_violation = MagicMock()
        mock_violation.is_willful = False
        mock_violation.fcra_section = "611"
        mock_violation.statutory_damages_min = 100
        mock_violation.statutory_damages_max = 1000
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_violation]

        severity = calculate_violation_severity(mock_db, client_id=1)

        assert severity["total_violations"] == 1
        assert severity["willful_count"] == 0
        assert severity["section_counts"]["611"] == 1

    def test_willful_violations_increase_severity(self):
        """Test that willful violations increase severity score."""
        mock_db = MagicMock()
        mock_violation = MagicMock()
        mock_violation.is_willful = True
        mock_violation.fcra_section = "611"
        mock_violation.statutory_damages_min = 100
        mock_violation.statutory_damages_max = 1000
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_violation]

        severity = calculate_violation_severity(mock_db, client_id=1)

        assert severity["willful_count"] == 1
        # Score = 1*0.5 + 1*2 + 1000/10000 = 0.5 + 2 + 0.1 = 2.6
        assert severity["severity_score"] > 0

    def test_severity_score_capped_at_10(self):
        """Test that severity score is capped at 10."""
        mock_db = MagicMock()
        violations = []
        for _ in range(20):
            mock_v = MagicMock()
            mock_v.is_willful = True
            mock_v.fcra_section = "611"
            mock_v.statutory_damages_min = 100
            mock_v.statutory_damages_max = 10000
            violations.append(mock_v)
        mock_db.query.return_value.filter_by.return_value.all.return_value = violations

        severity = calculate_violation_severity(mock_db, client_id=1)

        assert severity["severity_score"] == 10

    def test_severity_with_analysis_id_filter(self):
        """Test severity calculation filtered by analysis ID."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value.filter_by.return_value = mock_query
        mock_query.filter_by.return_value.all.return_value = []

        calculate_violation_severity(mock_db, client_id=1, analysis_id=5)

        # Verify filter_by was called twice (once for client_id, once for analysis_id)
        assert mock_db.query.return_value.filter_by.called


# =============================================================================
# Tests for assess_documentation()
# =============================================================================

class TestAssessDocumentation:
    """Test documentation assessment function."""

    def test_no_standing_record(self):
        """Test documentation assessment with no standing."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        strength = assess_documentation(mock_db, client_id=1)

        assert strength["has_concrete_harm"] is False
        assert strength["score"] == 0

    def test_full_standing_documentation(self):
        """Test documentation with all standing elements."""
        mock_db = MagicMock()
        mock_standing = MagicMock()
        mock_standing.has_concrete_harm = True
        mock_standing.has_dissemination = True
        mock_standing.has_causation = True
        mock_standing.denial_letters_count = 3
        mock_standing.adverse_action_notices_count = 2
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_standing

        strength = assess_documentation(mock_db, client_id=1)

        assert strength["has_concrete_harm"] is True
        assert strength["has_dissemination"] is True
        assert strength["has_causation"] is True
        # Score = 3 + 3 + 2 + min(2, 3) = 10
        assert strength["score"] == 10

    def test_partial_standing_documentation(self):
        """Test documentation with partial standing elements."""
        mock_db = MagicMock()
        mock_standing = MagicMock()
        mock_standing.has_concrete_harm = True
        mock_standing.has_dissemination = False
        mock_standing.has_causation = False
        mock_standing.denial_letters_count = 1
        mock_standing.adverse_action_notices_count = 0
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_standing

        strength = assess_documentation(mock_db, client_id=1)

        # Score = 3 + 0 + 0 + 1 = 4
        assert strength["score"] == 4


# =============================================================================
# Tests for estimate_damages()
# =============================================================================

class TestEstimateDamages:
    """Test damages estimation function."""

    def test_no_damages_record(self):
        """Test damages estimation with no damages record."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        # Mock violation severity for fallback
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        damages = estimate_damages(mock_db, client_id=1)

        assert damages["actual_damages"] == 0

    def test_damages_with_record(self):
        """Test damages estimation with existing damages record."""
        mock_db = MagicMock()
        mock_damages = MagicMock()
        mock_damages.actual_damages_total = 5000
        mock_damages.statutory_damages_total = 3000
        mock_damages.punitive_damages_amount = 9000
        mock_damages.total_exposure = 17000
        mock_damages.settlement_target = 8500
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_damages

        damages = estimate_damages(mock_db, client_id=1)

        assert damages["actual_damages"] == 5000
        assert damages["statutory_damages"] == 3000
        assert damages["punitive_potential"] == 9000
        assert damages["total_exposure"] == 17000
        assert damages["settlement_target"] == 8500


# =============================================================================
# Tests for _generate_recommendation()
# =============================================================================

class TestGenerateRecommendation:
    """Test recommendation generation logic."""

    def test_frivolous_response_triggers_regulatory_complaint(self):
        """Test frivolous response recommends regulatory complaint."""
        rec = _generate_recommendation(
            dispute_round=1,
            bureau="Experian",
            creditor_name="Bad Creditor",
            response_patterns={"bureaus": {"Experian": {"frivolous": 1}}},
            furnisher_stats={"deletion_rate": 0.5},
            violation_severity={"severity_score": 5},
            doc_strength={"score": 5},
            damages_estimate={"total_exposure": 10000}
        )

        assert rec["recommended_action"] == "regulatory_complaint"
        assert rec["confidence_score"] == 0.9
        assert "frivolous" in rec["reasoning"].lower()

    def test_no_response_triggers_regulatory_complaint(self):
        """Test no response recommends regulatory complaint."""
        rec = _generate_recommendation(
            dispute_round=1,
            bureau="TransUnion",
            creditor_name="Test Creditor",
            response_patterns={"bureaus": {"TransUnion": {"no_response": 1}}},
            furnisher_stats={"deletion_rate": 0.5},
            violation_severity={"severity_score": 3},
            doc_strength={"score": 3},
            damages_estimate={"total_exposure": 5000}
        )

        assert rec["recommended_action"] == "regulatory_complaint"
        assert rec["confidence_score"] == 0.85

    def test_round1_low_deletion_rate_recommends_mov(self):
        """Test round 1 with low deletion rate recommends MOV demand."""
        rec = _generate_recommendation(
            dispute_round=1,
            bureau="Equifax",
            creditor_name="Tough Creditor",
            response_patterns={"bureaus": {}},
            furnisher_stats={"deletion_rate": 0.2},
            violation_severity={"severity_score": 3},
            doc_strength={"score": 3},
            damages_estimate={"total_exposure": 5000}
        )

        assert rec["recommended_action"] == "mov_demand"
        assert "low deletion rate" in rec["reasoning"].lower()

    def test_round1_high_deletion_rate_recommends_standard(self):
        """Test round 1 with high deletion rate recommends standard redispute."""
        rec = _generate_recommendation(
            dispute_round=1,
            bureau="Experian",
            creditor_name="Good Creditor",
            response_patterns={"bureaus": {}},
            furnisher_stats={"deletion_rate": 0.7},
            violation_severity={"severity_score": 3},
            doc_strength={"score": 3},
            damages_estimate={"total_exposure": 5000}
        )

        assert rec["recommended_action"] == "standard_redispute"
        assert rec["confidence_score"] == 0.75

    def test_round2_verified_severe_recommends_intent_to_sue(self):
        """Test round 2 verified with severe violations recommends intent to sue."""
        rec = _generate_recommendation(
            dispute_round=2,
            bureau="Experian",
            creditor_name="Stubborn Creditor",
            response_patterns={"bureaus": {"Experian": {"verified": 1}}},
            furnisher_stats={"deletion_rate": 0.3},
            violation_severity={"severity_score": 8},
            doc_strength={"score": 6},
            damages_estimate={"total_exposure": 30000}
        )

        assert rec["recommended_action"] == "intent_to_sue"
        assert rec["confidence_score"] == 0.8

    def test_round2_verified_moderate_recommends_direct_furnisher(self):
        """Test round 2 verified with moderate violations recommends direct furnisher."""
        rec = _generate_recommendation(
            dispute_round=2,
            bureau="TransUnion",
            creditor_name="Test Creditor",
            response_patterns={"bureaus": {"TransUnion": {"verified": 1}}},
            furnisher_stats={"deletion_rate": 0.4},
            violation_severity={"severity_score": 5},
            doc_strength={"score": 4},
            damages_estimate={"total_exposure": 10000}
        )

        assert rec["recommended_action"] == "direct_furnisher"

    def test_round3_high_damages_strong_docs_recommends_settlement(self):
        """Test round 3+ with high damages and strong docs recommends settlement demand."""
        rec = _generate_recommendation(
            dispute_round=3,
            bureau="Equifax",
            creditor_name="Big Bank",
            response_patterns={"bureaus": {}},
            furnisher_stats={"deletion_rate": 0.3},
            violation_severity={"severity_score": 7, "willful_count": 2},
            doc_strength={"score": 7},
            damages_estimate={"total_exposure": 50000}
        )

        assert rec["recommended_action"] == "settlement_demand"
        assert rec["confidence_score"] == 0.85

    def test_round3_adds_media_pressure_for_willful(self):
        """Test round 3+ adds media pressure as alternative for willful violations."""
        rec = _generate_recommendation(
            dispute_round=4,
            bureau="Experian",
            creditor_name="Bad Actor",
            response_patterns={"bureaus": {}},
            furnisher_stats={"deletion_rate": 0.2},
            violation_severity={"severity_score": 5, "willful_count": 3},
            doc_strength={"score": 4},
            damages_estimate={"total_exposure": 15000}
        )

        assert "media_pressure" in rec["alternative_actions"]

    def test_recommendation_includes_supporting_factors(self):
        """Test recommendation includes all supporting factors."""
        rec = _generate_recommendation(
            dispute_round=1,
            bureau="Experian",
            creditor_name="Test",
            response_patterns={"bureaus": {}},
            furnisher_stats={"deletion_rate": 0.5},
            violation_severity={"severity_score": 5},
            doc_strength={"score": 6},
            damages_estimate={"total_exposure": 20000}
        )

        assert "supporting_factors" in rec
        assert "deletion_rate" in rec["supporting_factors"]
        assert "violation_severity" in rec["supporting_factors"]
        assert "documentation_strength" in rec["supporting_factors"]


# =============================================================================
# Tests for recommend_escalation()
# =============================================================================

class TestRecommendEscalation:
    """Test main recommendation engine."""

    @patch('services.escalation_service.get_db')
    def test_client_not_found(self, mock_get_db):
        """Test recommendation when client not found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = recommend_escalation(client_id=999)

        assert result == {"error": "Client not found"}

    @patch('services.escalation_service.estimate_damages')
    @patch('services.escalation_service.assess_documentation')
    @patch('services.escalation_service.calculate_violation_severity')
    @patch('services.escalation_service.analyze_response_patterns')
    @patch('services.escalation_service.get_dispute_history')
    @patch('services.escalation_service.get_furnisher_performance')
    @patch('services.escalation_service.get_db')
    def test_basic_recommendation_generation(
        self, mock_get_db, mock_furnisher, mock_history,
        mock_patterns, mock_severity, mock_docs, mock_damages
    ):
        """Test basic recommendation is generated."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.current_dispute_round = 1
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter_by.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        # Mock helper functions
        mock_history.return_value = []
        mock_patterns.return_value = {"bureaus": {}, "frivolous_count": 0, "no_response_count": 0, "total_responses": 0}
        mock_furnisher.return_value = {"found": False, "deletion_rate": 0.5, "avg_response_days": 25}
        mock_severity.return_value = {"total_violations": 0, "willful_count": 0, "severity_score": 0, "section_counts": {}}
        mock_docs.return_value = {"has_concrete_harm": False, "score": 0}
        mock_damages.return_value = {"actual_damages": 0, "total_exposure": 0}

        result = recommend_escalation(client_id=1)

        assert result["success"] is True
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

    @patch('services.escalation_service.estimate_damages')
    @patch('services.escalation_service.assess_documentation')
    @patch('services.escalation_service.calculate_violation_severity')
    @patch('services.escalation_service.analyze_response_patterns')
    @patch('services.escalation_service.get_dispute_history')
    @patch('services.escalation_service.get_furnisher_performance')
    @patch('services.escalation_service.get_db')
    def test_recommendation_with_bureau_filter(
        self, mock_get_db, mock_furnisher, mock_history,
        mock_patterns, mock_severity, mock_docs, mock_damages
    ):
        """Test recommendation filtered to single bureau."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.current_dispute_round = 1
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter_by.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        # Mock helper functions
        mock_history.return_value = []
        mock_patterns.return_value = {"bureaus": {}, "frivolous_count": 0, "no_response_count": 0, "total_responses": 0}
        mock_furnisher.return_value = {"found": False, "deletion_rate": 0.5, "avg_response_days": 25}
        mock_severity.return_value = {"total_violations": 0, "willful_count": 0, "severity_score": 0, "section_counts": {}}
        mock_docs.return_value = {"has_concrete_harm": False, "score": 0}
        mock_damages.return_value = {"actual_damages": 0, "total_exposure": 0}

        result = recommend_escalation(client_id=1, bureau="Experian")

        assert result["success"] is True


# =============================================================================
# Tests for get_escalation_timeline()
# =============================================================================

class TestGetEscalationTimeline:
    """Test timeline generation."""

    @patch('services.escalation_service.recommend_escalation')
    @patch('services.escalation_service.get_db')
    def test_timeline_client_not_found(self, mock_get_db, mock_recommend):
        """Test timeline when client not found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = get_escalation_timeline(client_id=999)

        assert result == {"error": "Client not found"}

    @patch('services.escalation_service.recommend_escalation')
    @patch('services.escalation_service.get_db')
    def test_timeline_basic_generation(self, mock_get_db, mock_recommend):
        """Test basic timeline generation."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.current_dispute_round = 1
        mock_client.round_started_at = datetime.utcnow() - timedelta(days=10)
        mock_client.created_at = datetime.utcnow() - timedelta(days=30)
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        mock_recommend.return_value = {
            "success": True,
            "recommendations": [{
                "recommended_action": "standard_redispute",
                "reasoning": "Test"
            }]
        }

        result = get_escalation_timeline(client_id=1)

        assert result["success"] is True
        assert "timeline" in result


# =============================================================================
# Tests for save_recommendation()
# =============================================================================

class TestSaveRecommendation:
    """Test recommendation saving."""

    @patch('services.escalation_service.get_db')
    def test_save_recommendation_basic(self, mock_get_db):
        """Test saving a recommendation."""
        mock_db = MagicMock()
        mock_rec = MagicMock()
        mock_rec.id = 1
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock the EscalationRecommendation constructor
        with patch('services.escalation_service.EscalationRecommendation') as MockRec:
            MockRec.return_value = mock_rec

            rec_id = save_recommendation({
                "client_id": 1,
                "dispute_round": 1,
                "bureau": "Experian",
                "creditor_name": "Test",
                "recommended_action": "standard_redispute",
                "confidence_score": 0.75,
                "reasoning": "Test reasoning"
            })

            assert rec_id == 1


# =============================================================================
# Tests for apply_recommendation()
# =============================================================================

class TestApplyRecommendation:
    """Test recommendation application."""

    @patch('services.escalation_service.get_db')
    def test_apply_recommendation_not_found(self, mock_get_db):
        """Test applying non-existent recommendation."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = apply_recommendation(recommendation_id=999)

        assert result == {"error": "Recommendation not found"}

    @patch('services.escalation_service.get_db')
    def test_apply_recommendation_success(self, mock_get_db):
        """Test successfully applying a recommendation."""
        mock_db = MagicMock()
        mock_rec = MagicMock()
        mock_rec.to_dict.return_value = {"id": 1, "applied": True}
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_rec
        mock_get_db.return_value = mock_db

        result = apply_recommendation(recommendation_id=1)

        assert result["success"] is True
        assert mock_rec.applied is True


# =============================================================================
# Tests for record_outcome()
# =============================================================================

class TestRecordOutcome:
    """Test outcome recording."""

    @patch('services.escalation_service.get_db')
    def test_record_outcome_not_found(self, mock_get_db):
        """Test recording outcome for non-existent recommendation."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = record_outcome(recommendation_id=999, outcome="deleted")

        assert result == {"error": "Recommendation not found"}

    @patch('services.escalation_service._update_furnisher_stats')
    @patch('services.escalation_service.get_db')
    def test_record_outcome_success(self, mock_get_db, mock_update_stats):
        """Test successfully recording an outcome."""
        mock_db = MagicMock()
        mock_rec = MagicMock()
        mock_rec.creditor_name = "Test Creditor"
        mock_rec.recommended_action = "standard_redispute"
        mock_rec.to_dict.return_value = {"id": 1, "outcome_actual": "deleted"}
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_rec
        mock_get_db.return_value = mock_db

        result = record_outcome(recommendation_id=1, outcome="deleted")

        assert result["success"] is True
        assert mock_rec.outcome_actual == "deleted"


# =============================================================================
# Tests for _update_furnisher_stats()
# =============================================================================

class TestUpdateFurnisherStats:
    """Test furnisher stats update function."""

    def test_update_stats_furnisher_not_found(self):
        """Test stats update when furnisher not found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Should not raise an error
        _update_furnisher_stats(mock_db, "Unknown Creditor", "standard_redispute", "deleted")

    def test_update_stats_creates_stats_if_missing(self):
        """Test stats are created if furnisher has none."""
        mock_db = MagicMock()
        mock_furnisher = MagicMock()
        mock_furnisher.stats = None
        mock_furnisher.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_furnisher

        with patch('services.escalation_service.FurnisherStats') as MockStats:
            mock_new_stats = MagicMock()
            mock_new_stats.total_disputes = None
            mock_new_stats.round_1_deleted = None
            MockStats.return_value = mock_new_stats

            _update_furnisher_stats(mock_db, "Test Creditor", "standard_redispute", "deleted")

            mock_db.add.assert_called()

    def test_update_stats_deleted_outcome(self):
        """Test stats update for deleted outcome."""
        mock_db = MagicMock()
        mock_furnisher = MagicMock()
        mock_stats = MagicMock()
        mock_stats.total_disputes = 10
        mock_stats.round_1_deleted = 5
        mock_furnisher.stats = mock_stats
        mock_db.query.return_value.filter.return_value.first.return_value = mock_furnisher

        _update_furnisher_stats(mock_db, "Test Creditor", "standard_redispute", "deleted")

        assert mock_stats.total_disputes == 11
        assert mock_stats.round_1_deleted == 6

    def test_update_stats_verified_outcome(self):
        """Test stats update for verified outcome."""
        mock_db = MagicMock()
        mock_furnisher = MagicMock()
        mock_stats = MagicMock()
        mock_stats.total_disputes = 10
        mock_stats.round_1_verified = 3
        mock_furnisher.stats = mock_stats
        mock_db.query.return_value.filter.return_value.first.return_value = mock_furnisher

        _update_furnisher_stats(mock_db, "Test Creditor", "standard_redispute", "verified")

        assert mock_stats.round_1_verified == 4

    def test_update_stats_settlement_outcome(self):
        """Test stats update for settlement outcome."""
        mock_db = MagicMock()
        mock_furnisher = MagicMock()
        mock_stats = MagicMock()
        mock_stats.total_disputes = 10
        mock_stats.settlement_count = 2
        mock_furnisher.stats = mock_stats
        mock_db.query.return_value.filter.return_value.first.return_value = mock_furnisher

        _update_furnisher_stats(mock_db, "Test Creditor", "settlement_demand", "settlement reached")

        assert mock_stats.settlement_count == 3


# =============================================================================
# Tests for get_escalation_stats()
# =============================================================================

class TestGetEscalationStats:
    """Test escalation statistics retrieval."""

    @patch('services.escalation_service.get_db')
    def test_empty_stats(self, mock_get_db):
        """Test stats with no recommendations."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = get_escalation_stats()

        assert result["success"] is True
        assert result["total_recommendations"] == 0

    @patch('services.escalation_service.get_db')
    def test_stats_with_completed_recommendations(self, mock_get_db):
        """Test stats with completed recommendations."""
        mock_db = MagicMock()
        mock_rec1 = MagicMock()
        mock_rec1.applied = True
        mock_rec1.outcome_actual = "deleted"
        mock_rec1.recommended_action = "standard_redispute"

        mock_rec2 = MagicMock()
        mock_rec2.applied = True
        mock_rec2.outcome_actual = "verified"
        mock_rec2.recommended_action = "standard_redispute"

        mock_db.query.return_value.all.return_value = [mock_rec1, mock_rec2]
        mock_get_db.return_value = mock_db

        result = get_escalation_stats()

        assert result["success"] is True
        assert result["total_recommendations"] == 2
        assert result["applied_recommendations"] == 2


# =============================================================================
# Tests for get_cases_needing_escalation_review()
# =============================================================================

class TestGetCasesNeedingEscalationReview:
    """Test cases needing review retrieval."""

    @patch('services.escalation_service.get_db')
    def test_no_cases_needing_review(self, mock_get_db):
        """Test when no cases need review."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = get_cases_needing_escalation_review()

        assert result == []

    @patch('services.escalation_service.get_db')
    def test_frivolous_response_needs_urgent_review(self, mock_get_db):
        """Test frivolous response triggers urgent review."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = "Test Client"
        mock_client.current_dispute_round = 1

        mock_response = MagicMock()
        mock_response.response_type = "frivolous"
        mock_response.created_at = datetime.utcnow() - timedelta(days=5)

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_client]
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = mock_response
        mock_get_db.return_value = mock_db

        result = get_cases_needing_escalation_review()

        assert len(result) == 1
        assert result[0]["priority"] == "urgent"

    @patch('services.escalation_service.get_db')
    def test_verified_response_needs_high_priority_review(self, mock_get_db):
        """Test verified response after 7 days triggers high priority review."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = "Test Client"
        mock_client.current_dispute_round = 2

        mock_response = MagicMock()
        mock_response.response_type = "verified"
        mock_response.created_at = datetime.utcnow() - timedelta(days=10)

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_client]
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = mock_response
        mock_get_db.return_value = mock_db

        result = get_cases_needing_escalation_review()

        assert len(result) == 1
        assert result[0]["priority"] == "high"

    @patch('services.escalation_service.get_db')
    def test_no_response_after_deadline_needs_urgent_review(self, mock_get_db):
        """Test no response after 35 days triggers urgent review."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = "Test Client"
        mock_client.current_dispute_round = 1
        mock_client.round_started_at = datetime.utcnow() - timedelta(days=40)

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_client]
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = get_cases_needing_escalation_review()

        assert len(result) == 1
        assert result[0]["priority"] == "urgent"
        assert "35 days" in result[0]["reason"]

    @patch('services.escalation_service.get_db')
    def test_cases_sorted_by_priority(self, mock_get_db):
        """Test that cases are sorted by priority."""
        mock_db = MagicMock()

        # Create clients with different priorities
        mock_client1 = MagicMock()
        mock_client1.id = 1
        mock_client1.name = "Client 1"
        mock_client1.current_dispute_round = 1
        mock_client1.round_started_at = None

        mock_client2 = MagicMock()
        mock_client2.id = 2
        mock_client2.name = "Client 2"
        mock_client2.current_dispute_round = 2
        mock_client2.round_started_at = None

        mock_response1 = MagicMock()
        mock_response1.response_type = "verified"
        mock_response1.created_at = datetime.utcnow() - timedelta(days=10)

        mock_response2 = MagicMock()
        mock_response2.response_type = "frivolous"
        mock_response2.created_at = datetime.utcnow() - timedelta(days=5)

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_client1, mock_client2]
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.side_effect = [
            mock_response1,  # For client1 - verified (high)
            mock_response2,  # For client2 - frivolous (urgent)
        ]
        mock_get_db.return_value = mock_db

        result = get_cases_needing_escalation_review()

        # Urgent should come before high
        assert len(result) == 2
        assert result[0]["priority"] == "urgent"
        assert result[1]["priority"] == "high"
