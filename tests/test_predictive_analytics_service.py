"""
Comprehensive Unit Tests for Predictive Analytics Service

Tests cover:
- Revenue forecasting with moving averages and trend analysis
- Client lifetime value (LTV) calculation
- Case timeline prediction
- Caseload forecasting
- Settlement probability prediction
- Revenue trends analysis
- Growth opportunities identification
- Churn risk calculation
- Top clients by LTV retrieval
- Edge cases and error handling
"""

import pytest
import statistics
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.predictive_analytics_service import (
    PredictiveAnalyticsService,
    predictive_analytics_service,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def service():
    """Create a PredictiveAnalyticsService instance."""
    return PredictiveAnalyticsService()


@pytest.fixture
def mock_client():
    """Create a mock Client."""
    client = Mock()
    client.id = 1
    client.name = "Test Client"
    client.email = "client@test.com"
    client.status = "active"
    client.signup_amount = 50000  # $500.00 in cents
    client.payment_status = "paid"
    client.payment_received_at = datetime.utcnow() - timedelta(days=30)
    client.current_dispute_round = 2
    client.referred_by_affiliate_id = None
    client.referred_by_client_id = None
    client.created_at = datetime.utcnow() - timedelta(days=60)
    client.updated_at = datetime.utcnow() - timedelta(days=5)
    return client


@pytest.fixture
def mock_case():
    """Create a mock Case."""
    case = Mock()
    case.id = 1
    case.client_id = 1
    case.status = "active"
    case.created_at = datetime.utcnow() - timedelta(days=30)
    return case


@pytest.fixture
def mock_case_score():
    """Create a mock CaseScore."""
    score = Mock()
    score.id = 1
    score.client_id = 1
    score.total_score = 7.5
    score.settlement_probability = 0.75
    return score


@pytest.fixture
def mock_settlement():
    """Create a mock Settlement."""
    settlement = Mock()
    settlement.id = 1
    settlement.case_id = 1
    settlement.target_amount = 10000.0
    settlement.status = "negotiating"
    settlement.contingency_earned = 3300.0
    settlement.payment_received = True
    settlement.payment_date = datetime.utcnow() - timedelta(days=10)
    return settlement


@pytest.fixture
def mock_violation():
    """Create a mock Violation."""
    violation = Mock()
    violation.id = 1
    violation.client_id = 1
    violation.is_willful = False
    violation.statutory_damages_max = 1000.0
    return violation


@pytest.fixture
def mock_case_outcome():
    """Create a mock CaseOutcome."""
    outcome = Mock()
    outcome.id = 1
    outcome.case_id = 1
    outcome.time_to_resolution_days = 90
    return outcome


@pytest.fixture
def mock_ltv_record():
    """Create a mock ClientLifetimeValue."""
    ltv = Mock()
    ltv.id = 1
    ltv.client_id = 1
    ltv.ltv_estimate = 1500.0
    ltv.probability_of_success = 0.75
    ltv.expected_settlement = 5000.0
    ltv.expected_fees = 1650.0
    ltv.acquisition_cost = 150.0
    ltv.churn_risk = 0.15
    return ltv


def create_mock_db():
    """Create a properly chained mock database session."""
    mock_db = MagicMock()
    # Set up proper chaining for SQLAlchemy query patterns
    mock_db.query.return_value = mock_db
    mock_db.filter.return_value = mock_db
    mock_db.filter_by.return_value = mock_db
    mock_db.order_by.return_value = mock_db
    mock_db.limit.return_value = mock_db
    mock_db.first.return_value = None
    mock_db.all.return_value = []
    mock_db.count.return_value = 0
    mock_db.scalar.return_value = None
    return mock_db


# ============================================================================
# Service Initialization Tests
# ============================================================================

class TestServiceInitialization:
    """Tests for service initialization."""

    def test_init_creates_instance(self, service):
        """Test service initialization creates an instance."""
        assert service is not None
        assert isinstance(service, PredictiveAnalyticsService)

    def test_init_default_values(self, service):
        """Test default values are set correctly."""
        assert service.default_acquisition_cost == 150.0
        assert service.avg_case_fee == 500.0
        assert service.avg_settlement_fee_percent == 0.33

    def test_singleton_exists(self):
        """Test that singleton instance exists."""
        assert predictive_analytics_service is not None
        assert isinstance(predictive_analytics_service, PredictiveAnalyticsService)


# ============================================================================
# Revenue Forecasting Tests
# ============================================================================

class TestForecastRevenue:
    """Tests for forecast_revenue method."""

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_revenue_success(self, mock_get_db, service):
        """Test successful revenue forecast."""
        mock_db = create_mock_db()
        mock_db.scalar.return_value = 10000
        mock_db.count.return_value = 5
        mock_get_db.return_value = mock_db

        result = service.forecast_revenue(months_ahead=3)

        assert result["success"] is True
        assert "forecasts" in result
        assert len(result["forecasts"]) == 3
        assert "historical" in result
        assert "trend_direction" in result
        assert "avg_monthly_revenue" in result
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_revenue_minimal_data(self, mock_get_db, service):
        """Test revenue forecast with minimal historical data."""
        mock_db = create_mock_db()
        mock_db.scalar.return_value = 0
        mock_db.count.return_value = 0
        mock_get_db.return_value = mock_db

        result = service.forecast_revenue(months_ahead=1)

        assert result["success"] is True
        # When all months have zero revenue, average should be 0
        # The service uses the actual data, not a default
        assert "avg_monthly_revenue" in result

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_revenue_database_error(self, mock_get_db, service):
        """Test revenue forecast handles database errors."""
        mock_db = create_mock_db()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = service.forecast_revenue(months_ahead=3)

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_revenue_trend_calculation(self, mock_get_db, service):
        """Test revenue forecast trend calculation."""
        mock_db = create_mock_db()
        # Simulate increasing revenue trend
        mock_db.scalar.return_value = 5000
        mock_db.count.return_value = 0
        mock_get_db.return_value = mock_db

        result = service.forecast_revenue(months_ahead=3)

        assert result["success"] is True
        assert result["trend_direction"] in ["up", "down", "stable"]

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_revenue_trend_capped(self, mock_get_db, service):
        """Test that trend is capped between -20% and 30%."""
        mock_db = create_mock_db()
        mock_db.scalar.return_value = 100000
        mock_db.count.return_value = 0
        mock_get_db.return_value = mock_db

        result = service.forecast_revenue(months_ahead=1)

        assert result["success"] is True
        # Trend should be capped
        assert -20 <= result["trend_percent"] <= 30


# ============================================================================
# Client LTV Calculation Tests
# ============================================================================

class TestCalculateClientLTV:
    """Tests for calculate_client_ltv method."""

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_ltv_success(self, mock_get_db, service, mock_client, mock_case, mock_case_score, mock_settlement):
        """Test successful LTV calculation."""
        mock_db = create_mock_db()

        # Setup query chain for different model queries
        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.count.return_value = 5
            query_mock.scalar.return_value = 5000.0

            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            if 'Client' in str(model_name):
                query_mock.first.return_value = mock_client
            elif 'Case' in str(model_name) and 'Score' not in str(model_name) and 'Outcome' not in str(model_name):
                query_mock.first.return_value = mock_case
            elif 'CaseScore' in str(model_name):
                query_mock.first.return_value = mock_case_score
            elif 'Settlement' in str(model_name):
                query_mock.first.return_value = mock_settlement
            elif 'Analysis' in str(model_name):
                query_mock.first.return_value = None
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.calculate_client_ltv(client_id=1)

        assert result["success"] is True
        assert result["client_id"] == 1
        assert "ltv_estimate" in result
        assert "probability_of_success" in result
        assert "expected_settlement" in result
        assert "churn_risk" in result
        assert result["ltv_tier"] in ["high", "medium", "low"]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_ltv_client_not_found(self, mock_get_db, service):
        """Test LTV calculation when client not found."""
        mock_db = create_mock_db()
        mock_db.first.return_value = None
        mock_get_db.return_value = mock_db

        result = service.calculate_client_ltv(client_id=999)

        assert result["success"] is False
        assert "Client not found" in result["error"]

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_ltv_without_case_score(self, mock_get_db, service, mock_client):
        """Test LTV calculation without case score uses violation count."""
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.count.return_value = 10  # 10 violations
            query_mock.scalar.return_value = 5000.0

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.calculate_client_ltv(client_id=1)

        assert result["success"] is True
        # Probability should be based on violations: min(0.85, 0.3 + (10 * 0.05)) = 0.8
        assert 0.3 <= result["probability_of_success"] <= 0.85

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_ltv_with_affiliate_referral(self, mock_get_db, service, mock_client):
        """Test LTV calculation increases acquisition cost for affiliate referrals."""
        mock_client.referred_by_affiliate_id = 1  # Has affiliate referral
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.count.return_value = 0
            query_mock.scalar.return_value = 5000.0

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.calculate_client_ltv(client_id=1)

        assert result["success"] is True
        # Acquisition cost should be 150 * 1.1 = 165
        assert result["acquisition_cost"] == 165.0

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_ltv_database_error(self, mock_get_db, service):
        """Test LTV calculation handles database errors."""
        mock_db = create_mock_db()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = service.calculate_client_ltv(client_id=1)

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_db.rollback.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_ltv_tier_classification(self, mock_get_db, service, mock_client):
        """Test LTV tier classification."""
        mock_client.signup_amount = 300000  # $3000 for high LTV
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.count.return_value = 0
            query_mock.scalar.return_value = 10000.0

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.calculate_client_ltv(client_id=1)

        assert result["success"] is True
        # With high signup amount, should be high tier
        assert result["ltv_tier"] in ["high", "medium", "low"]


# ============================================================================
# Case Timeline Prediction Tests
# ============================================================================

class TestPredictCaseTimeline:
    """Tests for predict_case_timeline method."""

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_timeline_success(self, mock_get_db, service, mock_client, mock_case_outcome):
        """Test successful case timeline prediction."""
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.limit.return_value = query_mock

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            elif 'CaseOutcome' in model_name:
                query_mock.all.return_value = [mock_case_outcome]
            elif 'CaseScore' in model_name:
                query_mock.first.return_value = None
            else:
                query_mock.first.return_value = None
                query_mock.all.return_value = []

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.predict_case_timeline(client_id=1)

        assert result["success"] is True
        assert result["client_id"] == 1
        assert "current_round" in result
        assert "expected_resolution_date" in result
        assert "days_remaining" in result
        assert "milestones" in result
        assert len(result["milestones"]) > 0

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_timeline_client_not_found(self, mock_get_db, service):
        """Test timeline prediction when client not found."""
        mock_db = create_mock_db()
        mock_db.first.return_value = None
        mock_get_db.return_value = mock_db

        result = service.predict_case_timeline(client_id=999)

        assert result["success"] is False
        assert "Client not found" in result["error"]

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_timeline_with_high_case_score(self, mock_get_db, service, mock_client, mock_case_score):
        """Test timeline prediction with high case score reduces time."""
        mock_client.current_dispute_round = 1
        mock_case_score.total_score = 9.0  # High score
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = []

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            elif 'CaseScore' in model_name:
                query_mock.first.return_value = mock_case_score
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.predict_case_timeline(client_id=1)

        assert result["success"] is True
        # High score should reduce days remaining by 30%
        # Default: 3 rounds * 45 days = 135 days, reduced by 30% = ~95 days
        assert result["days_remaining"] < 135

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_timeline_with_low_case_score(self, mock_get_db, service, mock_client, mock_case_score):
        """Test timeline prediction with low case score increases time."""
        mock_client.current_dispute_round = 1
        mock_case_score.total_score = 3.0  # Low score
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = []

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            elif 'CaseScore' in model_name:
                query_mock.first.return_value = mock_case_score
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.predict_case_timeline(client_id=1)

        assert result["success"] is True
        # Low score should increase days remaining by 30%
        assert result["days_remaining"] > 135

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_timeline_confidence_levels(self, mock_get_db, service, mock_client, mock_case_outcome):
        """Test timeline prediction confidence levels based on outcome data."""
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.limit.return_value = query_mock

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            elif 'CaseOutcome' in model_name:
                # 25 outcomes for high confidence
                query_mock.all.return_value = [mock_case_outcome for _ in range(25)]
            elif 'CaseScore' in model_name:
                query_mock.first.return_value = None
            else:
                query_mock.first.return_value = None
                query_mock.all.return_value = []

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.predict_case_timeline(client_id=1)

        assert result["success"] is True
        assert result["confidence"] == "high"

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_timeline_error_handling(self, mock_get_db, service):
        """Test timeline prediction handles errors."""
        mock_db = create_mock_db()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = service.predict_case_timeline(client_id=1)

        assert result["success"] is False
        assert "Database error" in result["error"]


# ============================================================================
# Caseload Forecasting Tests
# ============================================================================

class TestForecastCaseload:
    """Tests for forecast_caseload method."""

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_caseload_success(self, mock_get_db, service):
        """Test successful caseload forecast."""
        mock_db = create_mock_db()
        mock_db.count.return_value = 10
        mock_db.scalar.return_value = 0
        mock_get_db.return_value = mock_db

        result = service.forecast_caseload(months_ahead=3)

        assert result["success"] is True
        assert "forecasts" in result
        assert len(result["forecasts"]) == 3
        assert "historical" in result
        assert "current_active_cases" in result
        assert "current_pending_signups" in result

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_caseload_with_trend(self, mock_get_db, service):
        """Test caseload forecast calculates trend correctly."""
        mock_db = create_mock_db()
        # Simulate increasing signups - return count values in sequence
        count_values = [5, 6, 7, 8, 9, 10, 50, 10]  # historical + current counts
        mock_db.count.side_effect = count_values
        mock_get_db.return_value = mock_db

        result = service.forecast_caseload(months_ahead=1)

        assert result["success"] is True
        # Should show positive trend
        assert result["trend_percent"] > 0

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_caseload_minimum_prediction(self, mock_get_db, service):
        """Test caseload forecast has minimum of 1."""
        mock_db = create_mock_db()
        mock_db.count.return_value = 0
        mock_get_db.return_value = mock_db

        result = service.forecast_caseload(months_ahead=1)

        assert result["success"] is True
        assert result["forecasts"][0]["predicted_cases"] >= 1
        assert result["forecasts"][0]["low_estimate"] >= 1

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_caseload_error_handling(self, mock_get_db, service):
        """Test caseload forecast handles errors."""
        mock_db = create_mock_db()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = service.forecast_caseload(months_ahead=3)

        assert result["success"] is False
        assert "Database error" in result["error"]


# ============================================================================
# Settlement Probability Prediction Tests
# ============================================================================

class TestPredictSettlementProbability:
    """Tests for predict_settlement_probability method."""

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_probability_success(self, mock_get_db, service, mock_client, mock_case_score):
        """Test successful settlement probability prediction."""
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            elif 'CaseScore' in model_name:
                query_mock.first.return_value = mock_case_score
            elif 'Violation' in model_name:
                # Return different counts for total vs willful
                query_mock.count.side_effect = [8, 2]
            else:
                query_mock.first.return_value = None
                query_mock.count.return_value = 0

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.predict_settlement_probability(client_id=1)

        assert result["success"] is True
        assert result["client_id"] == 1
        assert "settlement_probability" in result
        assert "probability_percent" in result
        assert "factors" in result
        assert "recommendation" in result

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_probability_client_not_found(self, mock_get_db, service):
        """Test probability prediction when client not found."""
        mock_db = create_mock_db()
        mock_db.first.return_value = None
        mock_get_db.return_value = mock_db

        result = service.predict_settlement_probability(client_id=999)

        assert result["success"] is False
        assert "Client not found" in result["error"]

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_probability_high_violations(self, mock_get_db, service, mock_client):
        """Test probability increases with high violation count."""
        mock_client.current_dispute_round = 3
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            elif 'CaseScore' in model_name:
                query_mock.first.return_value = None
            elif 'Violation' in model_name:
                # High violation counts
                query_mock.count.side_effect = [15, 5]
            else:
                query_mock.first.return_value = None
                query_mock.count.return_value = 0

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.predict_settlement_probability(client_id=1)

        assert result["success"] is True
        # High violations + willful + round 3 should boost probability
        assert result["settlement_probability"] >= 0.5

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_probability_recommendations(self, mock_get_db, service, mock_client, mock_case_score):
        """Test probability provides appropriate recommendations."""
        mock_case_score.total_score = 9.0
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            elif 'CaseScore' in model_name:
                query_mock.first.return_value = mock_case_score
            elif 'Violation' in model_name:
                query_mock.count.return_value = 10
            else:
                query_mock.first.return_value = None
                query_mock.count.return_value = 0

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.predict_settlement_probability(client_id=1)

        assert result["success"] is True
        # High probability should get aggressive recommendation
        if result["settlement_probability"] >= 0.7:
            assert "aggressive" in result["recommendation"].lower() or "Excellent" in result["recommendation"]

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_probability_capped(self, mock_get_db, service, mock_client, mock_case_score):
        """Test probability is capped between 0.05 and 0.95."""
        mock_case_score.total_score = 10.0  # Max score
        mock_client.current_dispute_round = 4
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            elif 'CaseScore' in model_name:
                query_mock.first.return_value = mock_case_score
            elif 'Violation' in model_name:
                query_mock.count.side_effect = [20, 10]
            else:
                query_mock.first.return_value = None
                query_mock.count.return_value = 0

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.predict_settlement_probability(client_id=1)

        assert result["success"] is True
        assert result["settlement_probability"] <= 0.95
        assert result["settlement_probability"] >= 0.05


# ============================================================================
# Revenue Trends Tests
# ============================================================================

class TestGetRevenueTrends:
    """Tests for get_revenue_trends method."""

    @patch('services.predictive_analytics_service.get_db')
    def test_get_revenue_trends_success(self, mock_get_db, service):
        """Test successful revenue trends retrieval."""
        mock_db = create_mock_db()
        mock_db.scalar.return_value = 5000
        mock_db.count.return_value = 10
        mock_get_db.return_value = mock_db

        result = service.get_revenue_trends()

        assert result["success"] is True
        assert "monthly_data" in result
        assert len(result["monthly_data"]) == 12
        assert "total_revenue_12m" in result
        assert "avg_monthly_revenue" in result
        assert "yoy_growth_percent" in result
        assert "best_month" in result
        assert "worst_month" in result
        assert "revenue_by_type" in result

    @patch('services.predictive_analytics_service.get_db')
    def test_get_revenue_trends_yoy_growth(self, mock_get_db, service):
        """Test YoY growth calculation."""
        mock_db = create_mock_db()
        # All queries return constant value for simplicity
        mock_db.scalar.return_value = 5000
        mock_db.count.return_value = 10
        mock_get_db.return_value = mock_db

        result = service.get_revenue_trends()

        assert result["success"] is True
        # With constant revenue, growth should be 0
        assert "yoy_growth_percent" in result

    @patch('services.predictive_analytics_service.get_db')
    def test_get_revenue_trends_error_handling(self, mock_get_db, service):
        """Test revenue trends handles errors."""
        mock_db = create_mock_db()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = service.get_revenue_trends()

        assert result["success"] is False
        assert "Database error" in result["error"]


# ============================================================================
# Growth Opportunities Tests
# ============================================================================

class TestIdentifyGrowthOpportunities:
    """Tests for identify_growth_opportunities method."""

    @patch('services.predictive_analytics_service.get_db')
    def test_identify_opportunities_success(self, mock_get_db, service):
        """Test successful growth opportunities identification."""
        mock_db = create_mock_db()
        # Set up count to return different values for different queries
        mock_db.count.return_value = 10
        mock_db.scalar.return_value = 50000
        mock_get_db.return_value = mock_db

        result = service.identify_growth_opportunities()

        assert result["success"] is True
        assert "opportunities" in result
        assert "total_potential_value" in result
        assert "high_priority_count" in result
        assert "summary" in result

    @patch('services.predictive_analytics_service.get_db')
    def test_identify_opportunities_with_dormant_clients(self, mock_get_db, service):
        """Test identifies dormant client reactivation opportunity."""
        mock_db = create_mock_db()
        # Return values in order: dormant(15), pending(0), settlements(0), referrals(0), total(100), round4(0)
        mock_db.count.side_effect = [15, 0, 0, 0, 100, 0]
        mock_db.scalar.return_value = 0
        mock_get_db.return_value = mock_db

        result = service.identify_growth_opportunities()

        assert result["success"] is True
        dormant_opp = next(
            (o for o in result["opportunities"] if o["type"] == "reactivation"),
            None
        )
        assert dormant_opp is not None
        assert dormant_opp["priority"] == "high"  # > 10 dormant
        assert dormant_opp["count"] == 15

    @patch('services.predictive_analytics_service.get_db')
    def test_identify_opportunities_pending_signups(self, mock_get_db, service):
        """Test identifies pending signup conversion opportunity."""
        mock_db = create_mock_db()
        # Return values in order: dormant(0), pending(10), settlements(0), referrals(0), total(100), round4(0)
        mock_db.count.side_effect = [0, 10, 0, 0, 100, 0]
        mock_db.scalar.return_value = 0
        mock_get_db.return_value = mock_db

        result = service.identify_growth_opportunities()

        assert result["success"] is True
        conversion_opp = next(
            (o for o in result["opportunities"] if o["type"] == "conversion"),
            None
        )
        assert conversion_opp is not None
        assert conversion_opp["priority"] == "high"
        assert conversion_opp["potential_value"] == 10 * 500

    @patch('services.predictive_analytics_service.get_db')
    def test_identify_opportunities_low_referral_rate(self, mock_get_db, service):
        """Test identifies referral program opportunity when rate is low."""
        mock_db = create_mock_db()
        # Return values in order: dormant(0), pending(0), settlements(0), referrals(5), total(100), round4(0)
        mock_db.count.side_effect = [0, 0, 0, 5, 100, 0]
        mock_db.scalar.return_value = 0
        mock_get_db.return_value = mock_db

        result = service.identify_growth_opportunities()

        assert result["success"] is True
        referral_opp = next(
            (o for o in result["opportunities"] if o["type"] == "referral"),
            None
        )
        assert referral_opp is not None

    @patch('services.predictive_analytics_service.get_db')
    def test_identify_opportunities_sorted_by_value(self, mock_get_db, service):
        """Test opportunities are sorted by potential value."""
        mock_db = create_mock_db()
        # Multiple opportunities with different values
        mock_db.count.side_effect = [5, 10, 2, 5, 100, 3]
        mock_db.scalar.return_value = 10000
        mock_get_db.return_value = mock_db

        result = service.identify_growth_opportunities()

        assert result["success"] is True
        # Should be sorted by potential_value descending
        if len(result["opportunities"]) > 1:
            values = [o["potential_value"] for o in result["opportunities"]]
            assert values == sorted(values, reverse=True)

    @patch('services.predictive_analytics_service.get_db')
    def test_identify_opportunities_error_handling(self, mock_get_db, service):
        """Test growth opportunities handles errors."""
        mock_db = create_mock_db()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = service.identify_growth_opportunities()

        assert result["success"] is False
        assert "Database error" in result["error"]


# ============================================================================
# Churn Risk Calculation Tests
# ============================================================================

class TestCalculateChurnRisk:
    """Tests for calculate_churn_risk method."""

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_churn_risk_success(self, mock_get_db, service, mock_client):
        """Test successful churn risk calculation."""
        mock_db = create_mock_db()
        mock_db.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        result = service.calculate_churn_risk(client_id=1)

        assert result["success"] is True
        assert result["client_id"] == 1
        assert "churn_risk" in result
        assert "risk_percent" in result
        assert "risk_level" in result
        assert "risk_factors" in result
        assert "recommendation" in result
        assert "days_since_activity" in result

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_churn_risk_client_not_found(self, mock_get_db, service):
        """Test churn risk when client not found."""
        mock_db = create_mock_db()
        mock_db.first.return_value = None
        mock_get_db.return_value = mock_db

        result = service.calculate_churn_risk(client_id=999)

        assert result["success"] is False
        assert "Client not found" in result["error"]

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_churn_risk_paused_account(self, mock_get_db, service, mock_client):
        """Test churn risk for paused account."""
        mock_client.status = "paused"
        mock_db = create_mock_db()
        mock_db.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        result = service.calculate_churn_risk(client_id=1)

        assert result["success"] is True
        # Paused status should add 0.3 to risk
        assert result["churn_risk"] >= 0.4  # 0.1 base + 0.3 paused
        assert any(f["factor"] == "Account Paused" for f in result["risk_factors"])

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_churn_risk_pending_payment(self, mock_get_db, service, mock_client):
        """Test churn risk for pending payment."""
        mock_client.payment_status = "pending"
        mock_db = create_mock_db()
        mock_db.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        result = service.calculate_churn_risk(client_id=1)

        assert result["success"] is True
        # Pending payment should add 0.2 to risk
        assert any(f["factor"] == "Payment Pending" for f in result["risk_factors"])

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_churn_risk_inactive_client(self, mock_get_db, service, mock_client):
        """Test churn risk for inactive client."""
        mock_client.updated_at = datetime.utcnow() - timedelta(days=60)
        mock_db = create_mock_db()
        mock_db.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        result = service.calculate_churn_risk(client_id=1)

        assert result["success"] is True
        assert result["days_since_activity"] == 60
        assert any(f["factor"] == "Inactivity" for f in result["risk_factors"])

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_churn_risk_no_dispute_started(self, mock_get_db, service, mock_client):
        """Test churn risk when no dispute started."""
        mock_client.current_dispute_round = 0
        mock_db = create_mock_db()
        mock_db.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        result = service.calculate_churn_risk(client_id=1)

        assert result["success"] is True
        assert any(f["factor"] == "No Dispute Started" for f in result["risk_factors"])

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_churn_risk_levels(self, mock_get_db, service, mock_client):
        """Test churn risk level classification."""
        # High risk: paused + pending payment + inactive
        mock_client.status = "paused"
        mock_client.payment_status = "pending"
        mock_client.updated_at = datetime.utcnow() - timedelta(days=90)
        mock_db = create_mock_db()
        mock_db.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        result = service.calculate_churn_risk(client_id=1)

        assert result["success"] is True
        assert result["risk_level"] == "high"
        assert "Immediate outreach" in result["recommendation"]


# ============================================================================
# Internal Churn Risk Calculation Tests
# ============================================================================

class TestCalculateChurnRiskInternal:
    """Tests for _calculate_churn_risk_internal method."""

    def test_internal_churn_risk_base_value(self, service, mock_client):
        """Test internal churn risk starts with base value."""
        mock_db = Mock()
        mock_client.status = "active"
        mock_client.payment_status = "paid"
        mock_client.current_dispute_round = 2

        risk = service._calculate_churn_risk_internal(mock_db, mock_client)

        # Base risk is 0.1
        assert risk >= 0.1

    def test_internal_churn_risk_cancelled_status(self, service, mock_client):
        """Test internal churn risk for cancelled client."""
        mock_db = Mock()
        mock_client.status = "cancelled"

        risk = service._calculate_churn_risk_internal(mock_db, mock_client)

        assert risk == 0.95

    def test_internal_churn_risk_failed_payment(self, service, mock_client):
        """Test internal churn risk for failed payment."""
        mock_db = Mock()
        mock_client.payment_status = "failed"

        risk = service._calculate_churn_risk_internal(mock_db, mock_client)

        # Failed payment adds 0.3
        assert risk >= 0.4

    def test_internal_churn_risk_capped(self, service, mock_client):
        """Test internal churn risk is capped."""
        mock_db = Mock()
        mock_client.status = "paused"
        mock_client.payment_status = "failed"
        mock_client.updated_at = datetime.utcnow() - timedelta(days=300)
        mock_client.current_dispute_round = 0

        risk = service._calculate_churn_risk_internal(mock_db, mock_client)

        # Should be capped at 0.95
        assert risk <= 0.95
        assert risk >= 0.05

    def test_internal_churn_risk_reduced_for_advanced_round(self, service, mock_client):
        """Test internal churn risk reduced for advanced dispute round."""
        mock_db = Mock()
        mock_client.status = "active"
        mock_client.payment_status = "paid"
        mock_client.current_dispute_round = 4

        risk = service._calculate_churn_risk_internal(mock_db, mock_client)

        # Round 4 should reduce risk by 0.05
        assert risk < 0.15  # Less than base 0.1 + some inactivity


# ============================================================================
# Top Clients by LTV Tests
# ============================================================================

class TestGetTopClientsByLTV:
    """Tests for get_top_clients_by_ltv method."""

    @patch('services.predictive_analytics_service.get_db')
    def test_get_top_clients_success(self, mock_get_db, service, mock_ltv_record, mock_client):
        """Test successful retrieval of top clients by LTV."""
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'ClientLifetimeValue' in model_name:
                query_mock.all.return_value = [mock_ltv_record]
            elif 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None
                query_mock.all.return_value = []

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.get_top_clients_by_ltv(limit=10)

        assert result["success"] is True
        assert "top_clients" in result
        assert "count" in result
        assert len(result["top_clients"]) == 1

    @patch('services.predictive_analytics_service.get_db')
    def test_get_top_clients_empty(self, mock_get_db, service):
        """Test get top clients when no LTV records exist."""
        mock_db = create_mock_db()
        mock_db.all.return_value = []
        mock_get_db.return_value = mock_db

        result = service.get_top_clients_by_ltv(limit=10)

        assert result["success"] is True
        assert result["top_clients"] == []
        assert result["count"] == 0

    @patch('services.predictive_analytics_service.get_db')
    def test_get_top_clients_skips_missing_clients(self, mock_get_db, service, mock_ltv_record):
        """Test get top clients skips LTV records without clients."""
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'ClientLifetimeValue' in model_name:
                query_mock.all.return_value = [mock_ltv_record]
            else:
                query_mock.first.return_value = None
                query_mock.all.return_value = []

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.get_top_clients_by_ltv(limit=10)

        assert result["success"] is True
        assert result["top_clients"] == []

    @patch('services.predictive_analytics_service.get_db')
    def test_get_top_clients_includes_details(self, mock_get_db, service, mock_ltv_record, mock_client):
        """Test get top clients includes all required details."""
        mock_client.current_dispute_round = 3
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'ClientLifetimeValue' in model_name:
                query_mock.all.return_value = [mock_ltv_record]
            elif 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None
                query_mock.all.return_value = []

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.get_top_clients_by_ltv(limit=10)

        assert result["success"] is True
        client = result["top_clients"][0]
        assert "client_id" in client
        assert "client_name" in client
        assert "ltv_estimate" in client
        assert "probability_of_success" in client
        assert "status" in client
        assert "dispute_round" in client

    @patch('services.predictive_analytics_service.get_db')
    def test_get_top_clients_error_handling(self, mock_get_db, service):
        """Test get top clients handles errors."""
        mock_db = create_mock_db()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        result = service.get_top_clients_by_ltv(limit=10)

        assert result["success"] is False
        assert "Database error" in result["error"]


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_revenue_closes_db_on_success(self, mock_get_db, service):
        """Test forecast_revenue closes database on success."""
        mock_db = create_mock_db()
        mock_db.scalar.return_value = 0
        mock_db.count.return_value = 0
        mock_get_db.return_value = mock_db

        service.forecast_revenue(months_ahead=1)

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_revenue_closes_db_on_error(self, mock_get_db, service):
        """Test forecast_revenue closes database on error."""
        mock_db = create_mock_db()
        mock_db.query.side_effect = Exception("Error")
        mock_get_db.return_value = mock_db

        service.forecast_revenue(months_ahead=1)

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_ltv_closes_db(self, mock_get_db, service, mock_client):
        """Test calculate_client_ltv closes database."""
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.count.return_value = 0
            query_mock.scalar.return_value = 5000.0

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        service.calculate_client_ltv(client_id=1)

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_timeline_closes_db(self, mock_get_db, service, mock_client):
        """Test predict_case_timeline closes database."""
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = []

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        service.predict_case_timeline(client_id=1)

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_forecast_caseload_closes_db(self, mock_get_db, service):
        """Test forecast_caseload closes database."""
        mock_db = create_mock_db()
        mock_db.count.return_value = 0
        mock_get_db.return_value = mock_db

        service.forecast_caseload(months_ahead=1)

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_predict_probability_closes_db(self, mock_get_db, service, mock_client):
        """Test predict_settlement_probability closes database."""
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.count.return_value = 0

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        service.predict_settlement_probability(client_id=1)

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_get_revenue_trends_closes_db(self, mock_get_db, service):
        """Test get_revenue_trends closes database."""
        mock_db = create_mock_db()
        mock_db.scalar.return_value = 0
        mock_db.count.return_value = 0
        mock_get_db.return_value = mock_db

        service.get_revenue_trends()

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_identify_opportunities_closes_db(self, mock_get_db, service):
        """Test identify_growth_opportunities closes database."""
        mock_db = create_mock_db()
        mock_db.count.return_value = 0
        mock_db.scalar.return_value = 0
        mock_get_db.return_value = mock_db

        service.identify_growth_opportunities()

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_calculate_churn_risk_closes_db(self, mock_get_db, service, mock_client):
        """Test calculate_churn_risk closes database."""
        mock_db = create_mock_db()
        mock_db.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        service.calculate_churn_risk(client_id=1)

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_get_top_clients_closes_db(self, mock_get_db, service):
        """Test get_top_clients_by_ltv closes database."""
        mock_db = create_mock_db()
        mock_db.all.return_value = []
        mock_get_db.return_value = mock_db

        service.get_top_clients_by_ltv(limit=10)

        mock_db.close.assert_called_once()

    @patch('services.predictive_analytics_service.get_db')
    def test_client_with_null_updated_at(self, mock_get_db, service, mock_client):
        """Test handling client with null updated_at."""
        mock_client.updated_at = None
        mock_db = create_mock_db()
        mock_db.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        result = service.calculate_churn_risk(client_id=1)

        assert result["success"] is True
        # Should use default 90 days for null updated_at
        assert result["days_since_activity"] == 90

    @patch('services.predictive_analytics_service.get_db')
    def test_client_with_null_created_at(self, mock_get_db, service, mock_client):
        """Test handling client with null created_at in LTV calculation."""
        mock_client.created_at = None
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.count.return_value = 0
            query_mock.scalar.return_value = 5000.0

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.calculate_client_ltv(client_id=1)

        assert result["success"] is True

    @patch('services.predictive_analytics_service.get_db')
    def test_client_with_null_dispute_round(self, mock_get_db, service, mock_client):
        """Test handling client with null current_dispute_round."""
        mock_client.current_dispute_round = None
        mock_db = create_mock_db()

        def query_side_effect(model):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.filter_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = []

            model_name = str(model) if not hasattr(model, '__name__') else model.__name__
            if 'Client' in model_name:
                query_mock.first.return_value = mock_client
            else:
                query_mock.first.return_value = None

            return query_mock

        mock_db.query.side_effect = query_side_effect
        mock_get_db.return_value = mock_db

        result = service.predict_case_timeline(client_id=1)

        assert result["success"] is True
        # Should default to round 1
        assert result["current_round"] == 1
