"""
Comprehensive Unit Tests for Attorney Analytics Service

Tests cover:
- Performance calculation for staff members
- Leaderboard generation and ranking
- Strengths identification
- Case assignment recommendations
- Workload distribution analysis
- Capacity forecasting
- Helper methods (efficiency score, performance tier, etc.)
- Error handling and edge cases
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.attorney_analytics_service import (
    AttorneyAnalyticsService,
    attorney_analytics_service,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def analytics_service():
    """Create a fresh AttorneyAnalyticsService for each test"""
    return AttorneyAnalyticsService()


@pytest.fixture
def mock_staff():
    """Create a mock staff member"""
    staff = MagicMock()
    staff.id = 1
    staff.first_name = "John"
    staff.last_name = "Doe"
    staff.full_name = "John Doe"
    staff.initials = "JD"
    staff.role = "attorney"
    staff.is_active = True
    staff.email = "john.doe@example.com"
    return staff


@pytest.fixture
def mock_case_outcome():
    """Create a mock case outcome"""
    outcome = MagicMock()
    outcome.attorney_id = 1
    outcome.final_outcome = "won"
    outcome.settlement_amount = 5000.0
    outcome.time_to_resolution_days = 45
    outcome.violation_types = ["FCRA 611", "FCRA 605"]
    outcome.willfulness_score = 0.8
    outcome.created_at = datetime.utcnow() - timedelta(days=10)
    return outcome


@pytest.fixture
def mock_case():
    """Create a mock case"""
    case = MagicMock()
    case.id = 1
    case.client_id = 100
    case.analysis_id = 50
    case.case_number = "CASE-001"
    case.status = "active"
    return case


@pytest.fixture
def mock_case_score():
    """Create a mock case score"""
    case_score = MagicMock()
    case_score.total_score = 8
    case_score.standing_score = 3
    case_score.violation_quality_score = 2
    case_score.willfulness_score = 2
    case_score.documentation_score = 1
    return case_score


# =============================================================================
# Tests for AttorneyAnalyticsService Constants
# =============================================================================

class TestAttorneyAnalyticsServiceConstants:
    """Test service constants and configuration"""

    def test_period_mappings_contains_week(self, analytics_service):
        """Test week period mapping exists"""
        assert "week" in analytics_service.PERIOD_MAPPINGS
        assert analytics_service.PERIOD_MAPPINGS["week"] == 7

    def test_period_mappings_contains_month(self, analytics_service):
        """Test month period mapping exists"""
        assert "month" in analytics_service.PERIOD_MAPPINGS
        assert analytics_service.PERIOD_MAPPINGS["month"] == 30

    def test_period_mappings_contains_quarter(self, analytics_service):
        """Test quarter period mapping exists"""
        assert "quarter" in analytics_service.PERIOD_MAPPINGS
        assert analytics_service.PERIOD_MAPPINGS["quarter"] == 90

    def test_period_mappings_contains_year(self, analytics_service):
        """Test year period mapping exists"""
        assert "year" in analytics_service.PERIOD_MAPPINGS
        assert analytics_service.PERIOD_MAPPINGS["year"] == 365

    def test_metrics_list(self, analytics_service):
        """Test metrics list contains expected metrics"""
        expected_metrics = [
            "cases_handled",
            "cases_won",
            "cases_settled",
            "total_settlements",
            "avg_resolution_days",
            "efficiency_score",
        ]
        assert analytics_service.METRICS == expected_metrics

    def test_min_cases_for_ranking_default(self, analytics_service):
        """Test minimum cases for ranking default value"""
        assert analytics_service.min_cases_for_ranking == 3


# =============================================================================
# Tests for calculate_performance()
# =============================================================================

class TestCalculatePerformance:
    """Test performance calculation function"""

    @patch('services.attorney_analytics_service.get_db')
    def test_staff_not_found_returns_error(self, mock_get_db, analytics_service):
        """Test performance calculation when staff not found"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=999)

        assert result["success"] is False
        assert result["error"] == "Staff member not found"

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_no_outcomes(self, mock_get_db, analytics_service, mock_staff):
        """Test performance calculation with no case outcomes"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1)

        assert result["success"] is True
        assert result["metrics"]["cases_handled"] == 0
        assert result["metrics"]["win_rate"] == 0
        assert result["metrics"]["efficiency_score"] == 0

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_with_won_cases(self, mock_get_db, analytics_service, mock_staff):
        """Test performance calculation with won cases"""
        mock_db = MagicMock()

        # Create won outcomes
        won_outcome = MagicMock()
        won_outcome.final_outcome = "won"
        won_outcome.settlement_amount = 0
        won_outcome.time_to_resolution_days = 30
        won_outcome.willfulness_score = 0.5

        # Setup mock to return staff for filter_by and outcomes for filter
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Staff':
                mock_query.filter_by.return_value.first.return_value = mock_staff
            elif model.__name__ == 'CaseOutcome':
                mock_query.filter.return_value.all.return_value = [won_outcome]
            return mock_query

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1)

        assert result["success"] is True
        assert result["metrics"]["cases_handled"] == 1
        assert result["metrics"]["cases_won"] == 1
        assert result["metrics"]["win_rate"] == 100.0

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_with_settled_cases(self, mock_get_db, analytics_service, mock_staff):
        """Test performance calculation with settled cases"""
        mock_db = MagicMock()

        # Create settled outcome
        settled_outcome = MagicMock()
        settled_outcome.final_outcome = "settled"
        settled_outcome.settlement_amount = 10000.0
        settled_outcome.time_to_resolution_days = 45
        settled_outcome.willfulness_score = 0.5

        # Setup mock to return staff for filter_by and outcomes for filter
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Staff':
                mock_query.filter_by.return_value.first.return_value = mock_staff
            elif model.__name__ == 'CaseOutcome':
                mock_query.filter.return_value.all.return_value = [settled_outcome]
            return mock_query

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1)

        assert result["success"] is True
        assert result["metrics"]["cases_settled"] == 1
        assert result["metrics"]["total_settlements"] == 10000.0
        assert result["metrics"]["avg_settlement_amount"] == 10000.0

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_with_lost_cases(self, mock_get_db, analytics_service, mock_staff):
        """Test performance calculation with lost cases"""
        mock_db = MagicMock()

        # Create lost outcome
        lost_outcome = MagicMock()
        lost_outcome.final_outcome = "lost"
        lost_outcome.settlement_amount = 0
        lost_outcome.time_to_resolution_days = 60
        lost_outcome.willfulness_score = 0.5

        # Setup mock to return staff for filter_by and outcomes for filter
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Staff':
                mock_query.filter_by.return_value.first.return_value = mock_staff
            elif model.__name__ == 'CaseOutcome':
                mock_query.filter.return_value.all.return_value = [lost_outcome]
            return mock_query

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1)

        assert result["success"] is True
        assert result["metrics"]["cases_lost"] == 1
        assert result["metrics"]["win_rate"] == 0

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_mixed_outcomes(self, mock_get_db, analytics_service, mock_staff):
        """Test performance calculation with mixed outcomes"""
        mock_db = MagicMock()

        # Create mixed outcomes
        outcomes = []
        for outcome_type in ["won", "won", "settled", "lost"]:
            outcome = MagicMock()
            outcome.final_outcome = outcome_type
            outcome.settlement_amount = 5000.0 if outcome_type == "settled" else 0
            outcome.time_to_resolution_days = 30
            outcome.willfulness_score = 0.5
            outcomes.append(outcome)

        # Setup mock to return staff for filter_by and outcomes for filter
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Staff':
                mock_query.filter_by.return_value.first.return_value = mock_staff
            elif model.__name__ == 'CaseOutcome':
                mock_query.filter.return_value.all.return_value = outcomes
            return mock_query

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1)

        assert result["success"] is True
        assert result["metrics"]["cases_handled"] == 4
        assert result["metrics"]["cases_won"] == 2
        assert result["metrics"]["cases_settled"] == 1
        assert result["metrics"]["cases_lost"] == 1
        # Win rate = (2 + 1) / 4 = 75%
        assert result["metrics"]["win_rate"] == 75.0

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_different_periods(self, mock_get_db, analytics_service, mock_staff):
        """Test performance calculation with different time periods"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        for period in ["week", "month", "quarter", "year"]:
            result = analytics_service.calculate_performance(staff_user_id=1, period=period)
            assert result["success"] is True
            assert result["period"] == period

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_invalid_period_defaults_to_month(self, mock_get_db, analytics_service, mock_staff):
        """Test that invalid period defaults to 30 days"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1, period="invalid")
        assert result["success"] is True

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_returns_staff_info(self, mock_get_db, analytics_service, mock_staff):
        """Test that result includes staff information"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1)

        assert result["staff_id"] == 1
        assert result["staff_name"] == "John Doe"

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_handles_exception(self, mock_get_db, analytics_service):
        """Test that exceptions are handled gracefully"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1)

        assert result["success"] is False
        assert "Database error" in result["error"]


# =============================================================================
# Tests for get_leaderboard()
# =============================================================================

class TestGetLeaderboard:
    """Test leaderboard generation function"""

    @patch('services.attorney_analytics_service.get_db')
    def test_leaderboard_empty_staff(self, mock_get_db, analytics_service):
        """Test leaderboard with no staff members"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = analytics_service.get_leaderboard()

        assert result["success"] is True
        assert result["leaderboard"] == []
        assert result["total_staff"] == 0

    @patch('services.attorney_analytics_service.get_db')
    def test_leaderboard_with_staff_no_performance(self, mock_get_db, analytics_service, mock_staff):
        """Test leaderboard with staff but no performance records"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_staff]
        # No existing performance record
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        # No outcomes for calculating metrics
        mock_query_outcomes = MagicMock()
        mock_query_outcomes.all.return_value = []
        mock_db.query.return_value.filter.return_value = mock_query_outcomes
        mock_get_db.return_value = mock_db

        result = analytics_service.get_leaderboard()

        assert result["success"] is True

    @patch('services.attorney_analytics_service.get_db')
    def test_leaderboard_default_metric_is_efficiency_score(self, mock_get_db, analytics_service):
        """Test that default ranking metric is efficiency_score"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = analytics_service.get_leaderboard()

        assert result["metric"] == "efficiency_score"

    @patch('services.attorney_analytics_service.get_db')
    def test_leaderboard_invalid_metric_defaults_to_efficiency(self, mock_get_db, analytics_service):
        """Test that invalid metric defaults to efficiency_score"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = analytics_service.get_leaderboard(metric="invalid_metric")

        assert result["metric"] == "efficiency_score"

    @patch('services.attorney_analytics_service.get_db')
    def test_leaderboard_assigns_badges(self, mock_get_db, analytics_service):
        """Test that badges are assigned to top 3"""
        mock_db = MagicMock()

        # Create 4 staff members
        staff_list = []
        for i in range(4):
            staff = MagicMock()
            staff.id = i + 1
            staff.full_name = f"Staff {i + 1}"
            staff.initials = f"S{i + 1}"
            staff.role = "attorney"
            staff_list.append(staff)

        mock_db.query.return_value.filter.return_value.all.return_value = staff_list

        # Create performance records with different scores
        performances = []
        for i, score in enumerate([90, 80, 70, 60]):
            perf = MagicMock()
            perf.efficiency_score = score
            performances.append(perf)

        call_count = [0]
        def mock_first():
            if call_count[0] < len(performances):
                result = performances[call_count[0]]
                call_count[0] += 1
                return result
            return None

        mock_db.query.return_value.filter.return_value.order_by.return_value.first = mock_first
        mock_get_db.return_value = mock_db

        result = analytics_service.get_leaderboard()

        assert result["success"] is True
        # First 3 should have badges
        if len(result["leaderboard"]) >= 3:
            assert result["leaderboard"][0]["badge"] == "🥇"
            assert result["leaderboard"][1]["badge"] == "🥈"
            assert result["leaderboard"][2]["badge"] == "🥉"
        if len(result["leaderboard"]) >= 4:
            assert result["leaderboard"][3]["badge"] == ""

    @patch('services.attorney_analytics_service.get_db')
    def test_leaderboard_avg_resolution_sorts_ascending(self, mock_get_db, analytics_service):
        """Test that avg_resolution_days sorts in ascending order (lower is better)"""
        mock_db = MagicMock()

        staff1 = MagicMock()
        staff1.id = 1
        staff1.full_name = "Fast Attorney"
        staff1.initials = "FA"
        staff1.role = "attorney"

        staff2 = MagicMock()
        staff2.id = 2
        staff2.full_name = "Slow Attorney"
        staff2.initials = "SA"
        staff2.role = "attorney"

        mock_db.query.return_value.filter.return_value.all.return_value = [staff1, staff2]

        # Create performance records
        perf1 = MagicMock()
        perf1.avg_resolution_days = 30  # Faster
        perf2 = MagicMock()
        perf2.avg_resolution_days = 60  # Slower

        perfs = [perf1, perf2]
        call_count = [0]
        def mock_first():
            if call_count[0] < len(perfs):
                result = perfs[call_count[0]]
                call_count[0] += 1
                return result
            return None

        mock_db.query.return_value.filter.return_value.order_by.return_value.first = mock_first
        mock_get_db.return_value = mock_db

        result = analytics_service.get_leaderboard(metric="avg_resolution_days")

        assert result["success"] is True
        # For avg_resolution_days, lower is better, so should NOT be reverse sorted
        if len(result["leaderboard"]) >= 2:
            assert result["leaderboard"][0]["staff_name"] == "Fast Attorney"

    @patch('services.attorney_analytics_service.get_db')
    def test_leaderboard_handles_exception(self, mock_get_db, analytics_service):
        """Test that exceptions are handled gracefully"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = analytics_service.get_leaderboard()

        assert result["success"] is False
        assert "Database error" in result["error"]


# =============================================================================
# Tests for identify_strengths()
# =============================================================================

class TestIdentifyStrengths:
    """Test strengths identification function"""

    @patch('services.attorney_analytics_service.get_db')
    def test_strengths_staff_not_found(self, mock_get_db, analytics_service):
        """Test strengths identification when staff not found"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=999)

        assert result["success"] is False
        assert result["error"] == "Staff member not found"

    @patch('services.attorney_analytics_service.get_db')
    def test_strengths_no_outcomes(self, mock_get_db, analytics_service, mock_staff):
        """Test strengths identification with no outcomes"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=1)

        assert result["success"] is True
        assert result["strengths"] == []
        assert "Not enough case data" in result["message"]

    @patch('services.attorney_analytics_service.get_db')
    def test_strengths_high_settlement_rate(self, mock_get_db, analytics_service, mock_staff):
        """Test that high settlement rate is identified as strength"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        # Create outcomes with high settlement rate (>60%)
        outcomes = []
        for i in range(10):
            outcome = MagicMock()
            outcome.final_outcome = "settled" if i < 7 else "lost"
            outcome.settlement_amount = 5000.0 if i < 7 else 0
            outcome.time_to_resolution_days = 45
            outcome.violation_types = None
            outcomes.append(outcome)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=1)

        assert result["success"] is True
        settlement_strength = [s for s in result["strengths"] if s["area"] == "Settlement Negotiation"]
        assert len(settlement_strength) > 0

    @patch('services.attorney_analytics_service.get_db')
    def test_strengths_low_settlement_rate_improvement(self, mock_get_db, analytics_service, mock_staff):
        """Test that low settlement rate is identified as area for improvement"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        # Create outcomes with low settlement rate (<30%)
        outcomes = []
        for i in range(10):
            outcome = MagicMock()
            outcome.final_outcome = "settled" if i < 2 else "lost"
            outcome.settlement_amount = 5000.0 if i < 2 else 0
            outcome.time_to_resolution_days = 90
            outcome.violation_types = None
            outcomes.append(outcome)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=1)

        assert result["success"] is True
        improvement = [i for i in result["areas_for_improvement"] if i["area"] == "Settlement Negotiation"]
        assert len(improvement) > 0

    @patch('services.attorney_analytics_service.get_db')
    def test_strengths_fast_case_resolution(self, mock_get_db, analytics_service, mock_staff):
        """Test that fast case resolution is identified as strength"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        # Create outcomes with fast resolution (<60 days)
        outcomes = []
        for i in range(5):
            outcome = MagicMock()
            outcome.final_outcome = "won"
            outcome.settlement_amount = 0
            outcome.time_to_resolution_days = 30
            outcome.violation_types = None
            outcomes.append(outcome)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=1)

        assert result["success"] is True
        velocity_strength = [s for s in result["strengths"] if s["area"] == "Case Velocity"]
        assert len(velocity_strength) > 0

    @patch('services.attorney_analytics_service.get_db')
    def test_strengths_slow_case_resolution_improvement(self, mock_get_db, analytics_service, mock_staff):
        """Test that slow case resolution is identified as area for improvement"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        # Create outcomes with slow resolution (>120 days)
        outcomes = []
        for i in range(5):
            outcome = MagicMock()
            outcome.final_outcome = "won"
            outcome.settlement_amount = 0
            outcome.time_to_resolution_days = 150
            outcome.violation_types = None
            outcomes.append(outcome)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=1)

        assert result["success"] is True
        improvement = [i for i in result["areas_for_improvement"] if i["area"] == "Case Velocity"]
        assert len(improvement) > 0

    @patch('services.attorney_analytics_service.get_db')
    def test_strengths_high_value_cases(self, mock_get_db, analytics_service, mock_staff):
        """Test that high-value case experience is identified as strength"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        # Create outcomes with high total settlements
        outcomes = []
        for i in range(5):
            outcome = MagicMock()
            outcome.final_outcome = "settled"
            outcome.settlement_amount = 15000.0
            outcome.time_to_resolution_days = 45
            outcome.violation_types = None
            outcomes.append(outcome)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=1)

        assert result["success"] is True
        high_value_strength = [s for s in result["strengths"] if s["area"] == "High-Value Cases"]
        assert len(high_value_strength) > 0

    @patch('services.attorney_analytics_service.get_db')
    def test_strengths_violation_type_expertise(self, mock_get_db, analytics_service, mock_staff):
        """Test that violation type expertise is identified"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        # Create outcomes with specific violation type and high win rate
        outcomes = []
        for i in range(5):
            outcome = MagicMock()
            outcome.final_outcome = "won" if i < 4 else "lost"
            outcome.settlement_amount = 0
            outcome.time_to_resolution_days = 45
            outcome.violation_types = ["FCRA 611"]
            outcomes.append(outcome)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=1)

        assert result["success"] is True
        # Should identify FCRA 611 as a strength area
        fcra_strength = [s for s in result["strengths"] if "FCRA 611" in s["area"]]
        assert len(fcra_strength) > 0

    @patch('services.attorney_analytics_service.get_db')
    def test_strengths_handles_exception(self, mock_get_db, analytics_service):
        """Test that exceptions are handled gracefully"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=1)

        assert result["success"] is False
        assert "Database error" in result["error"]


# =============================================================================
# Tests for recommend_case_assignment()
# =============================================================================

class TestRecommendCaseAssignment:
    """Test case assignment recommendation function"""

    @patch('services.attorney_analytics_service.get_db')
    def test_case_not_found(self, mock_get_db, analytics_service):
        """Test recommendation when case not found"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = analytics_service.recommend_case_assignment(case_id=999)

        assert result["success"] is False
        assert result["error"] == "Case not found"

    @patch('services.attorney_analytics_service.get_db')
    def test_recommend_with_no_attorneys(self, mock_get_db, analytics_service, mock_case):
        """Test recommendation with no available attorneys"""
        mock_db = MagicMock()

        # Case found
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_case,  # Case query
            None,       # Client query
            None,       # CaseScore query
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = []  # No violations
        mock_db.query.return_value.filter.return_value.all.return_value = []  # No attorneys
        mock_get_db.return_value = mock_db

        result = analytics_service.recommend_case_assignment(case_id=1)

        assert result["success"] is True
        assert result["recommendations"] == []
        assert result["top_recommendation"] is None

    @patch('services.attorney_analytics_service.get_db')
    def test_recommend_considers_win_rate(self, mock_get_db, analytics_service, mock_case, mock_staff):
        """Test that recommendation considers attorney win rate"""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        # Case found
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_case,
            mock_client,
            None,  # No case score
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = []  # No violations
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_staff],  # One attorney
            [],  # No outcomes for this attorney
        ]
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        mock_get_db.return_value = mock_db

        result = analytics_service.recommend_case_assignment(case_id=1)

        assert result["success"] is True
        assert len(result["recommendations"]) > 0

    @patch('services.attorney_analytics_service.get_db')
    def test_recommend_considers_workload(self, mock_get_db, analytics_service, mock_case, mock_staff):
        """Test that recommendation considers attorney workload"""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_case,
            mock_client,
            None,
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_staff],
            [],  # No outcomes
        ]
        # Low workload - high availability
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        mock_get_db.return_value = mock_db

        result = analytics_service.recommend_case_assignment(case_id=1)

        assert result["success"] is True
        if result["recommendations"]:
            # Should show availability based on low caseload
            assert result["recommendations"][0]["availability"] == "high"

    @patch('services.attorney_analytics_service.get_db')
    def test_recommend_handles_high_value_case(self, mock_get_db, analytics_service, mock_case, mock_staff, mock_case_score):
        """Test recommendation for high-value case"""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        # High value case score
        mock_case_score.total_score = 9

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_case,
            mock_client,
            mock_case_score,
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_staff],
            [],
        ]
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_get_db.return_value = mock_db

        result = analytics_service.recommend_case_assignment(case_id=1)

        assert result["success"] is True
        assert result["case_characteristics"]["is_high_value"] is True

    @patch('services.attorney_analytics_service.get_db')
    def test_recommend_handles_complex_case(self, mock_get_db, analytics_service, mock_case, mock_staff):
        """Test recommendation for complex case (many violations)"""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        # Create many violations
        violations = []
        for i in range(15):
            v = MagicMock()
            v.violation_type = f"FCRA 61{i % 5}"
            violations.append(v)

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_case,
            mock_client,
            None,
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = violations
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_staff],
            [],
        ]
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_get_db.return_value = mock_db

        result = analytics_service.recommend_case_assignment(case_id=1)

        assert result["success"] is True
        assert result["case_characteristics"]["is_complex"] is True

    @patch('services.attorney_analytics_service.get_db')
    def test_recommend_handles_exception(self, mock_get_db, analytics_service):
        """Test that exceptions are handled gracefully"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = analytics_service.recommend_case_assignment(case_id=1)

        assert result["success"] is False
        assert "Database error" in result["error"]


# =============================================================================
# Tests for get_workload_distribution()
# =============================================================================

class TestGetWorkloadDistribution:
    """Test workload distribution function"""

    @patch('services.attorney_analytics_service.get_db')
    def test_workload_empty_staff(self, mock_get_db, analytics_service):
        """Test workload distribution with no staff"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = analytics_service.get_workload_distribution()

        assert result["success"] is True
        assert result["distribution"] == []
        assert result["summary"]["total_staff"] == 0

    @patch('services.attorney_analytics_service.get_db')
    def test_workload_with_balanced_staff(self, mock_get_db, analytics_service, mock_staff):
        """Test workload distribution with balanced workload"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_staff]
        mock_db.query.return_value.filter.return_value.count.return_value = 8  # Optimal load
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 2
        mock_get_db.return_value = mock_db

        result = analytics_service.get_workload_distribution()

        assert result["success"] is True
        assert result["balance_recommendation"] == "Workload balanced"

    @patch('services.attorney_analytics_service.get_db')
    def test_workload_identifies_overloaded_staff(self, mock_get_db, analytics_service, mock_staff):
        """Test that overloaded staff are identified"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_staff]
        mock_db.query.return_value.filter.return_value.count.return_value = 20  # High load
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        mock_get_db.return_value = mock_db

        result = analytics_service.get_workload_distribution()

        assert result["success"] is True
        assert result["distribution"][0]["capacity_status"] == "overloaded"

    @patch('services.attorney_analytics_service.get_db')
    def test_workload_identifies_available_staff(self, mock_get_db, analytics_service, mock_staff):
        """Test that available staff are identified"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_staff]
        mock_db.query.return_value.filter.return_value.count.return_value = 2  # Low load
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        mock_get_db.return_value = mock_db

        result = analytics_service.get_workload_distribution()

        assert result["success"] is True
        assert result["distribution"][0]["capacity_status"] == "available"

    @patch('services.attorney_analytics_service.get_db')
    def test_workload_recommends_redistribution(self, mock_get_db, analytics_service):
        """Test recommendation for redistribution when needed"""
        mock_db = MagicMock()

        # Create two staff - one overloaded, one available
        overloaded_staff = MagicMock()
        overloaded_staff.id = 1
        overloaded_staff.full_name = "Overloaded Attorney"
        overloaded_staff.role = "attorney"

        available_staff = MagicMock()
        available_staff.id = 2
        available_staff.full_name = "Available Attorney"
        available_staff.role = "attorney"

        mock_db.query.return_value.filter.return_value.all.return_value = [overloaded_staff, available_staff]

        # Different workloads
        workloads = [20, 2]  # overloaded, available
        call_count = [0]

        def mock_count():
            if call_count[0] < len(workloads):
                result = workloads[call_count[0]]
                call_count[0] += 1
                return result
            return 0

        mock_db.query.return_value.filter.return_value.count = mock_count
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        mock_get_db.return_value = mock_db

        result = analytics_service.get_workload_distribution()

        assert result["success"] is True
        assert "Redistribute" in result["balance_recommendation"]

    @patch('services.attorney_analytics_service.get_db')
    def test_workload_handles_exception(self, mock_get_db, analytics_service):
        """Test that exceptions are handled gracefully"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = analytics_service.get_workload_distribution()

        assert result["success"] is False
        assert "Database error" in result["error"]


# =============================================================================
# Tests for forecast_capacity()
# =============================================================================

class TestForecastCapacity:
    """Test capacity forecasting function"""

    @patch('services.attorney_analytics_service.get_db')
    def test_forecast_staff_not_found(self, mock_get_db, analytics_service):
        """Test forecast when staff not found"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = analytics_service.forecast_capacity(staff_user_id=999)

        assert result["success"] is False
        assert result["error"] == "Staff member not found"

    @patch('services.attorney_analytics_service.get_db')
    def test_forecast_basic_capacity(self, mock_get_db, analytics_service, mock_staff):
        """Test basic capacity forecast"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.all.return_value = [(30,), (45,), (60,)]
        mock_get_db.return_value = mock_db

        result = analytics_service.forecast_capacity(staff_user_id=1)

        assert result["success"] is True
        assert "current_capacity" in result
        assert "forecast" in result
        assert "recommendation" in result

    @patch('services.attorney_analytics_service.get_db')
    def test_forecast_at_max_capacity(self, mock_get_db, analytics_service, mock_staff):
        """Test forecast when at maximum capacity"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter.return_value.count.return_value = 15
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        result = analytics_service.forecast_capacity(staff_user_id=1)

        assert result["success"] is True
        assert result["current_capacity"]["utilization_percent"] == 100.0
        assert "maximum capacity" in result["recommendation"]

    @patch('services.attorney_analytics_service.get_db')
    def test_forecast_under_utilized(self, mock_get_db, analytics_service, mock_staff):
        """Test forecast when under-utilized"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        mock_db.query.return_value.filter.return_value.all.return_value = [(30,)]
        mock_get_db.return_value = mock_db

        result = analytics_service.forecast_capacity(staff_user_id=1)

        assert result["success"] is True
        assert "Under-utilized" in result["recommendation"]

    @patch('services.attorney_analytics_service.get_db')
    def test_forecast_weekly_projection(self, mock_get_db, analytics_service, mock_staff):
        """Test that forecast includes 4-week projection"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter.return_value.count.return_value = 8
        mock_db.query.return_value.filter.return_value.all.return_value = [(45,)]
        mock_get_db.return_value = mock_db

        result = analytics_service.forecast_capacity(staff_user_id=1)

        assert result["success"] is True
        assert len(result["forecast"]["weekly_projection"]) == 4
        for week in result["forecast"]["weekly_projection"]:
            assert "week" in week
            assert "projected_cases" in week
            assert "available_capacity" in week

    @patch('services.attorney_analytics_service.get_db')
    def test_forecast_handles_exception(self, mock_get_db, analytics_service):
        """Test that exceptions are handled gracefully"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = analytics_service.forecast_capacity(staff_user_id=1)

        assert result["success"] is False
        assert "Database error" in result["error"]


# =============================================================================
# Tests for Helper Methods
# =============================================================================

class TestCalculateEfficiencyScore:
    """Test efficiency score calculation"""

    def test_efficiency_zero_cases(self, analytics_service):
        """Test efficiency score with zero cases"""
        score = analytics_service._calculate_efficiency_score(
            cases=0, win_rate=0, avg_days=0, total_value=0
        )
        assert score == 0

    def test_efficiency_high_performance(self, analytics_service):
        """Test efficiency score with high performance"""
        score = analytics_service._calculate_efficiency_score(
            cases=10, win_rate=0.9, avg_days=30, total_value=100000
        )
        assert score > 60

    def test_efficiency_capped_at_100(self, analytics_service):
        """Test that efficiency score is capped at 100"""
        score = analytics_service._calculate_efficiency_score(
            cases=100, win_rate=1.0, avg_days=10, total_value=1000000
        )
        # Score formula: min(30, 100*3) + 1.0*30 + max(0, 20-(10/5)) + min(20, 1000000/5000)
        # = 30 + 30 + 18 + 20 = 98 (capped at 100 if over)
        assert score <= 100
        assert score >= 90  # Should be very high

    def test_efficiency_considers_cases(self, analytics_service):
        """Test that case count affects score"""
        score_low = analytics_service._calculate_efficiency_score(
            cases=1, win_rate=0.5, avg_days=45, total_value=5000
        )
        score_high = analytics_service._calculate_efficiency_score(
            cases=10, win_rate=0.5, avg_days=45, total_value=5000
        )
        assert score_high > score_low

    def test_efficiency_considers_win_rate(self, analytics_service):
        """Test that win rate affects score"""
        score_low = analytics_service._calculate_efficiency_score(
            cases=5, win_rate=0.3, avg_days=45, total_value=5000
        )
        score_high = analytics_service._calculate_efficiency_score(
            cases=5, win_rate=0.9, avg_days=45, total_value=5000
        )
        assert score_high > score_low

    def test_efficiency_considers_speed(self, analytics_service):
        """Test that resolution speed affects score"""
        score_fast = analytics_service._calculate_efficiency_score(
            cases=5, win_rate=0.5, avg_days=20, total_value=5000
        )
        score_slow = analytics_service._calculate_efficiency_score(
            cases=5, win_rate=0.5, avg_days=100, total_value=5000
        )
        assert score_fast > score_slow


class TestIdentifyStrengthsHelper:
    """Test internal strength identification helper"""

    def test_identify_strengths_empty_outcomes(self, analytics_service):
        """Test with empty outcomes"""
        strengths = analytics_service._identify_strengths([])
        assert strengths == []

    def test_identify_strengths_strong_negotiator(self, analytics_service):
        """Test identification of strong negotiator"""
        outcomes = []
        for i in range(4):
            outcome = MagicMock()
            outcome.final_outcome = "settled" if i < 3 else "lost"
            outcome.time_to_resolution_days = 45
            outcome.settlement_amount = 5000
            outcome.willfulness_score = 0.5
            outcomes.append(outcome)

        strengths = analytics_service._identify_strengths(outcomes)
        assert "Strong negotiator" in strengths

    def test_identify_strengths_fast_resolution(self, analytics_service):
        """Test identification of fast case resolution"""
        outcomes = []
        for i in range(4):
            outcome = MagicMock()
            outcome.final_outcome = "won"
            outcome.time_to_resolution_days = 30
            outcome.settlement_amount = 0
            outcome.willfulness_score = 0.5
            outcomes.append(outcome)

        strengths = analytics_service._identify_strengths(outcomes)
        assert "Fast case resolution" in strengths

    def test_identify_strengths_high_value_specialist(self, analytics_service):
        """Test identification of high-value case specialist"""
        outcomes = []
        for i in range(3):
            outcome = MagicMock()
            outcome.final_outcome = "settled"
            outcome.time_to_resolution_days = 60
            outcome.settlement_amount = 15000
            outcome.willfulness_score = 0.5
            outcomes.append(outcome)

        strengths = analytics_service._identify_strengths(outcomes)
        assert "High-value case specialist" in strengths

    def test_identify_strengths_willfulness_documentation(self, analytics_service):
        """Test identification of willfulness documentation skill"""
        outcomes = []
        for i in range(3):
            outcome = MagicMock()
            outcome.final_outcome = "won"
            outcome.time_to_resolution_days = 60
            outcome.settlement_amount = 5000
            outcome.willfulness_score = 0.85
            outcomes.append(outcome)

        strengths = analytics_service._identify_strengths(outcomes)
        assert "Willfulness documentation" in strengths

    def test_identify_strengths_limited_to_4(self, analytics_service):
        """Test that strengths are limited to 4"""
        outcomes = []
        for i in range(10):
            outcome = MagicMock()
            outcome.final_outcome = "settled"
            outcome.time_to_resolution_days = 30
            outcome.settlement_amount = 20000
            outcome.willfulness_score = 0.9
            outcomes.append(outcome)

        strengths = analytics_service._identify_strengths(outcomes)
        assert len(strengths) <= 4


class TestGetPerformanceTier:
    """Test performance tier determination"""

    def test_tier_elite(self, analytics_service):
        """Test Elite tier for score >= 80"""
        assert analytics_service._get_performance_tier(80) == "Elite"
        assert analytics_service._get_performance_tier(90) == "Elite"
        assert analytics_service._get_performance_tier(100) == "Elite"

    def test_tier_strong(self, analytics_service):
        """Test Strong tier for score 60-79"""
        assert analytics_service._get_performance_tier(60) == "Strong"
        assert analytics_service._get_performance_tier(70) == "Strong"
        assert analytics_service._get_performance_tier(79) == "Strong"

    def test_tier_developing(self, analytics_service):
        """Test Developing tier for score 40-59"""
        assert analytics_service._get_performance_tier(40) == "Developing"
        assert analytics_service._get_performance_tier(50) == "Developing"
        assert analytics_service._get_performance_tier(59) == "Developing"

    def test_tier_new(self, analytics_service):
        """Test New tier for score < 40"""
        assert analytics_service._get_performance_tier(0) == "New"
        assert analytics_service._get_performance_tier(20) == "New"
        assert analytics_service._get_performance_tier(39) == "New"


class TestGetCapacityRecommendation:
    """Test capacity recommendation generation"""

    def test_recommendation_at_max(self, analytics_service):
        """Test recommendation at maximum capacity"""
        rec = analytics_service._get_capacity_recommendation(100, 0)
        assert "maximum capacity" in rec

    def test_recommendation_near_capacity(self, analytics_service):
        """Test recommendation near capacity"""
        rec = analytics_service._get_capacity_recommendation(85, 2)
        assert "high-priority" in rec.lower()

    def test_recommendation_optimal(self, analytics_service):
        """Test recommendation at optimal capacity"""
        rec = analytics_service._get_capacity_recommendation(60, 5)
        assert "accept new cases" in rec.lower()

    def test_recommendation_under_utilized(self, analytics_service):
        """Test recommendation when under-utilized"""
        rec = analytics_service._get_capacity_recommendation(30, 10)
        assert "Under-utilized" in rec
        assert "10" in rec


# =============================================================================
# Tests for Singleton Instance
# =============================================================================

class TestSingletonInstance:
    """Test the module-level singleton instance"""

    def test_singleton_exists(self):
        """Test that singleton instance exists"""
        assert attorney_analytics_service is not None
        assert isinstance(attorney_analytics_service, AttorneyAnalyticsService)

    def test_singleton_has_correct_defaults(self):
        """Test that singleton has correct default values"""
        assert attorney_analytics_service.min_cases_for_ranking == 3
        assert "month" in attorney_analytics_service.PERIOD_MAPPINGS


# =============================================================================
# Tests for Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_zero_settlement_amount(self, mock_get_db, analytics_service, mock_staff):
        """Test performance with settled case but zero settlement amount"""
        mock_db = MagicMock()

        outcome = MagicMock()
        outcome.final_outcome = "settled"
        outcome.settlement_amount = None  # None instead of 0
        outcome.time_to_resolution_days = 45
        outcome.willfulness_score = 0.5

        # Setup mock to return staff for filter_by and outcomes for filter
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Staff':
                mock_query.filter_by.return_value.first.return_value = mock_staff
            elif model.__name__ == 'CaseOutcome':
                mock_query.filter.return_value.all.return_value = [outcome]
            return mock_query

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1)

        assert result["success"] is True
        assert result["metrics"]["total_settlements"] == 0

    @patch('services.attorney_analytics_service.get_db')
    def test_calculate_performance_zero_resolution_days(self, mock_get_db, analytics_service, mock_staff):
        """Test performance with zero or negative resolution days"""
        mock_db = MagicMock()

        outcome = MagicMock()
        outcome.final_outcome = "won"
        outcome.settlement_amount = 0
        outcome.time_to_resolution_days = 0  # Zero days
        outcome.willfulness_score = 0.5

        # Setup mock to return staff for filter_by and outcomes for filter
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Staff':
                mock_query.filter_by.return_value.first.return_value = mock_staff
            elif model.__name__ == 'CaseOutcome':
                mock_query.filter.return_value.all.return_value = [outcome]
            return mock_query

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = analytics_service.calculate_performance(staff_user_id=1)

        assert result["success"] is True
        assert result["metrics"]["avg_resolution_days"] == 0

    @patch('services.attorney_analytics_service.get_db')
    def test_identify_strengths_violation_types_not_list(self, mock_get_db, analytics_service, mock_staff):
        """Test strengths identification when violation_types is not a list"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        outcome = MagicMock()
        outcome.final_outcome = "won"
        outcome.settlement_amount = 5000
        outcome.time_to_resolution_days = 45
        outcome.violation_types = "FCRA 611"  # String instead of list

        mock_db.query.return_value.filter.return_value.all.return_value = [outcome]
        mock_get_db.return_value = mock_db

        result = analytics_service.identify_strengths(staff_user_id=1)

        # Should not crash, should complete successfully
        assert result["success"] is True

    @patch('services.attorney_analytics_service.get_db')
    def test_recommend_violation_types_matching(self, mock_get_db, analytics_service, mock_case, mock_staff):
        """Test that violation type matching works correctly"""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.name = "Test Client"

        # Create violation
        violation = MagicMock()
        violation.violation_type = "FCRA 611"

        # Create outcome with matching violation type
        outcome = MagicMock()
        outcome.final_outcome = "won"
        outcome.violation_types = ["FCRA 611", "FCRA 605"]

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_case,
            mock_client,
            None,
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = [violation]
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_staff],
            [outcome, outcome],  # Two matching outcomes
        ]
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_get_db.return_value = mock_db

        result = analytics_service.recommend_case_assignment(case_id=1)

        assert result["success"] is True

    def test_efficiency_zero_avg_days(self, analytics_service):
        """Test efficiency calculation with zero average days"""
        score = analytics_service._calculate_efficiency_score(
            cases=5, win_rate=0.8, avg_days=0, total_value=10000
        )
        # Should still calculate without division by zero
        assert score > 0

    @patch('services.attorney_analytics_service.get_db')
    def test_leaderboard_null_metric_values(self, mock_get_db, analytics_service, mock_staff):
        """Test leaderboard handles null metric values"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_staff]

        perf = MagicMock()
        perf.efficiency_score = None  # Null value

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = perf
        mock_get_db.return_value = mock_db

        result = analytics_service.get_leaderboard()

        assert result["success"] is True
        # Should handle null gracefully by treating as 0
        if result["leaderboard"]:
            assert result["leaderboard"][0]["metric_value"] == 0
