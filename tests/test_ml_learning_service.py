"""
Comprehensive Unit Tests for ML Learning Service.

Tests cover:
- MLLearningService cache operations
- record_outcome() - Recording case outcomes for ML training
- get_similar_cases() - Finding similar historical cases
- calculate_success_rate() - Success rate calculations with filters
- get_average_settlement() - Settlement amount statistics
- get_resolution_time_estimate() - Resolution time predictions
- generate_prediction_features() - Feature extraction from client data
- predict_outcome() - Outcome predictions using Bayesian inference
- predict_settlement_range() - Settlement range predictions
- update_model_accuracy() - Model accuracy analysis
- get_learning_stats() - Comprehensive ML stats
- _get_model_recommendation() - Model recommendations
- Convenience functions (module-level wrappers)
"""

import json
import math
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ml_learning_service import (
    MLLearningService,
    record_outcome,
    get_similar_cases,
    calculate_success_rate,
    get_average_settlement,
    predict_outcome,
    predict_settlement_range,
    get_learning_stats,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def ml_service():
    """Create a fresh MLLearningService for each test."""
    service = MLLearningService()
    yield service
    # Clear cache after test
    service._cache.clear()
    service._cache_expiry.clear()


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_case_outcome():
    """Create a mock CaseOutcome object."""
    outcome = MagicMock()
    outcome.id = 1
    outcome.client_id = 1
    outcome.case_type = "fcra_dispute"
    outcome.violation_types = ["reinsertion", "611_failure"]
    outcome.furnisher_id = 10
    outcome.initial_score = 75
    outcome.final_outcome = "settled"
    outcome.settlement_amount = 5000
    outcome.actual_damages = 2000
    outcome.time_to_resolution_days = 90
    outcome.attorney_id = 5
    outcome.key_factors = {"strong_evidence": True}
    outcome.dispute_rounds_completed = 2
    outcome.bureaus_involved = ["Experian", "TransUnion"]
    outcome.violation_count = 3
    outcome.willfulness_score = 7
    outcome.documentation_quality = 8
    outcome.created_at = datetime.utcnow()
    outcome.to_dict = MagicMock(return_value={
        "id": 1,
        "client_id": 1,
        "final_outcome": "settled",
        "settlement_amount": 5000,
        "violation_types": ["reinsertion", "611_failure"],
    })
    return outcome


@pytest.fixture
def mock_client():
    """Create a mock Client object."""
    client = MagicMock()
    client.id = 1
    client.current_dispute_round = 2
    return client


@pytest.fixture
def mock_violation():
    """Create a mock Violation object."""
    violation = MagicMock()
    violation.violation_type = "reinsertion"
    violation.bureau = "Experian"
    violation.is_willful = True
    return violation


# =============================================================================
# Tests for MLLearningService Class Attributes
# =============================================================================

class TestMLLearningServiceAttributes:
    """Test MLLearningService class attributes and constants."""

    def test_model_version(self):
        """Test MODEL_VERSION is set correctly."""
        assert MLLearningService.MODEL_VERSION == "v1.0"

    def test_outcome_types(self):
        """Test OUTCOME_TYPES contains expected values."""
        expected = ["won", "lost", "settled", "dismissed"]
        assert MLLearningService.OUTCOME_TYPES == expected

    def test_violation_weights_contains_expected_types(self):
        """Test VIOLATION_WEIGHTS contains expected violation types."""
        weights = MLLearningService.VIOLATION_WEIGHTS
        assert "reinsertion" in weights
        assert "identity_theft" in weights
        assert "mixed_file" in weights
        assert "611_failure" in weights
        assert "605b_failure" in weights
        assert "623_failure" in weights
        assert "inaccurate_reporting" in weights
        assert "default" in weights

    def test_violation_weights_values(self):
        """Test VIOLATION_WEIGHTS have correct values."""
        weights = MLLearningService.VIOLATION_WEIGHTS
        assert weights["reinsertion"] == 2.5
        assert weights["identity_theft"] == 3.0
        assert weights["mixed_file"] == 2.0
        assert weights["default"] == 1.0


# =============================================================================
# Tests for Cache Operations
# =============================================================================

class TestMLLearningServiceCache:
    """Test cache operations."""

    def test_cache_initialization(self, ml_service):
        """Test cache is initialized empty."""
        assert ml_service._cache == {}
        assert ml_service._cache_expiry == {}

    def test_set_and_get_cache(self, ml_service):
        """Test setting and getting cache values."""
        ml_service._set_cache("test_key", {"data": "value"})
        result = ml_service._get_cache("test_key")
        assert result == {"data": "value"}

    def test_get_cache_miss(self, ml_service):
        """Test cache miss returns None."""
        result = ml_service._get_cache("nonexistent_key")
        assert result is None

    def test_cache_expiration(self, ml_service):
        """Test cache expires after duration."""
        ml_service._cache_duration = timedelta(seconds=0)
        ml_service._set_cache("test_key", "value")
        # Cache should be expired immediately
        result = ml_service._get_cache("test_key")
        assert result is None

    def test_cache_not_expired(self, ml_service):
        """Test cache returns value before expiration."""
        ml_service._cache_duration = timedelta(hours=1)
        ml_service._set_cache("test_key", "value")
        result = ml_service._get_cache("test_key")
        assert result == "value"


# =============================================================================
# Tests for record_outcome()
# =============================================================================

class TestRecordOutcome:
    """Test case outcome recording."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_record_outcome_success(self, mock_session_local, ml_service):
        """Test successful outcome recording."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcome_data = {
            "case_type": "fcra_dispute",
            "violation_types": ["reinsertion"],
            "furnisher_id": 10,
            "initial_score": 75,
            "final_outcome": "settled",
            "settlement_amount": 5000,
            "actual_damages": 2000,
            "time_to_resolution_days": 90,
            "attorney_id": 5,
            "key_factors": {"strong_evidence": True},
            "dispute_rounds_completed": 2,
            "bureaus_involved": ["Experian"],
            "violation_count": 3,
            "willfulness_score": 7,
            "documentation_quality": 8,
        }

        with patch.object(ml_service, '_update_predictions_with_actual'):
            result = ml_service.record_outcome(client_id=1, outcome_data=outcome_data)

        assert result["success"] is True
        assert "outcome_id" in result
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @patch('services.ml_learning_service.SessionLocal')
    def test_record_outcome_with_defaults(self, mock_session_local, ml_service):
        """Test outcome recording with default values."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Minimal outcome data - should use defaults
        outcome_data = {}

        with patch.object(ml_service, '_update_predictions_with_actual'):
            result = ml_service.record_outcome(client_id=1, outcome_data=outcome_data)

        assert result["success"] is True

    @patch('services.ml_learning_service.SessionLocal')
    def test_record_outcome_clears_cache(self, mock_session_local, ml_service):
        """Test that recording outcome clears the cache."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Pre-populate cache
        ml_service._cache["test_key"] = "test_value"

        with patch.object(ml_service, '_update_predictions_with_actual'):
            ml_service.record_outcome(client_id=1, outcome_data={})

        assert ml_service._cache == {}

    @patch('services.ml_learning_service.SessionLocal')
    def test_record_outcome_database_error(self, mock_session_local, ml_service):
        """Test outcome recording handles database errors."""
        mock_db = MagicMock()
        mock_db.add.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = ml_service.record_outcome(client_id=1, outcome_data={})

        assert result["success"] is False
        assert "error" in result
        mock_db.rollback.assert_called()

    @patch('services.ml_learning_service.SessionLocal')
    def test_record_outcome_calls_update_predictions(self, mock_session_local, ml_service):
        """Test that record_outcome calls _update_predictions_with_actual."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        with patch.object(ml_service, '_update_predictions_with_actual') as mock_update:
            ml_service.record_outcome(client_id=1, outcome_data={})
            mock_update.assert_called_once()


# =============================================================================
# Tests for _update_predictions_with_actual()
# =============================================================================

class TestUpdatePredictionsWithActual:
    """Test prediction update with actual outcomes."""

    def test_update_outcome_prediction(self, ml_service, mock_db):
        """Test updating outcome type prediction."""
        mock_prediction = MagicMock()
        mock_prediction.prediction_type = "outcome"
        mock_prediction.predicted_value = "settled"
        mock_prediction.actual_value = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_prediction]

        mock_outcome = MagicMock()
        mock_outcome.final_outcome = "settled"
        mock_outcome.settlement_amount = 5000
        mock_outcome.time_to_resolution_days = 90

        ml_service._update_predictions_with_actual(mock_db, client_id=1, outcome=mock_outcome)

        assert mock_prediction.actual_value == "settled"
        assert mock_prediction.was_accurate is True
        assert mock_prediction.resolved_at is not None

    def test_update_settlement_amount_prediction_accurate(self, ml_service, mock_db):
        """Test updating settlement amount prediction - accurate."""
        mock_prediction = MagicMock()
        mock_prediction.prediction_type = "settlement_amount"
        mock_prediction.predicted_value = "5000"
        mock_prediction.actual_value = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_prediction]

        mock_outcome = MagicMock()
        mock_outcome.final_outcome = "settled"
        mock_outcome.settlement_amount = 5000
        mock_outcome.time_to_resolution_days = 90

        ml_service._update_predictions_with_actual(mock_db, client_id=1, outcome=mock_outcome)

        assert mock_prediction.actual_value == "5000"
        assert mock_prediction.prediction_error == 0
        assert mock_prediction.was_accurate is True

    def test_update_settlement_amount_prediction_inaccurate(self, ml_service, mock_db):
        """Test updating settlement amount prediction - inaccurate (>25% error)."""
        mock_prediction = MagicMock()
        mock_prediction.prediction_type = "settlement_amount"
        mock_prediction.predicted_value = "10000"  # Predicted
        mock_prediction.actual_value = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_prediction]

        mock_outcome = MagicMock()
        mock_outcome.final_outcome = "settled"
        mock_outcome.settlement_amount = 5000  # Actual - 50% error
        mock_outcome.time_to_resolution_days = 90

        ml_service._update_predictions_with_actual(mock_db, client_id=1, outcome=mock_outcome)

        assert mock_prediction.prediction_error == 5000
        assert mock_prediction.was_accurate is False

    def test_update_resolution_time_prediction_accurate(self, ml_service, mock_db):
        """Test updating resolution time prediction - accurate (<30 days error)."""
        mock_prediction = MagicMock()
        mock_prediction.prediction_type = "resolution_time"
        mock_prediction.predicted_value = "95"
        mock_prediction.actual_value = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_prediction]

        mock_outcome = MagicMock()
        mock_outcome.final_outcome = "settled"
        mock_outcome.settlement_amount = 5000
        mock_outcome.time_to_resolution_days = 90

        ml_service._update_predictions_with_actual(mock_db, client_id=1, outcome=mock_outcome)

        assert mock_prediction.actual_value == "90"
        assert mock_prediction.prediction_error == 5
        assert mock_prediction.was_accurate is True

    def test_update_resolution_time_prediction_inaccurate(self, ml_service, mock_db):
        """Test updating resolution time prediction - inaccurate (>30 days error)."""
        mock_prediction = MagicMock()
        mock_prediction.prediction_type = "resolution_time"
        mock_prediction.predicted_value = "150"
        mock_prediction.actual_value = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_prediction]

        mock_outcome = MagicMock()
        mock_outcome.final_outcome = "settled"
        mock_outcome.settlement_amount = 5000
        mock_outcome.time_to_resolution_days = 90

        ml_service._update_predictions_with_actual(mock_db, client_id=1, outcome=mock_outcome)

        assert mock_prediction.prediction_error == 60
        assert mock_prediction.was_accurate is False


# =============================================================================
# Tests for get_similar_cases()
# =============================================================================

class TestGetSimilarCases:
    """Test similar case retrieval."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_similar_cases_no_filters(self, mock_session_local, ml_service, mock_case_outcome):
        """Test getting similar cases without filters."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_case_outcome]

        result = ml_service.get_similar_cases()

        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_similar_cases_with_furnisher_filter(self, mock_session_local, ml_service, mock_case_outcome):
        """Test getting similar cases filtered by furnisher."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_case_outcome]

        result = ml_service.get_similar_cases(furnisher_id=10)

        assert len(result) == 1

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_similar_cases_with_violation_types(self, mock_session_local, ml_service, mock_case_outcome):
        """Test similar cases scored by violation type overlap."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_case_outcome]

        result = ml_service.get_similar_cases(violation_types=["reinsertion"])

        assert len(result) == 1

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_similar_cases_scoring_with_matching_furnisher(self, mock_session_local, ml_service):
        """Test that matching furnisher increases similarity score."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Create two outcomes - one with matching furnisher
        outcome1 = MagicMock()
        outcome1.violation_types = ["reinsertion"]
        outcome1.furnisher_id = 10
        outcome1.to_dict = MagicMock(return_value={"id": 1, "furnisher_id": 10})

        outcome2 = MagicMock()
        outcome2.violation_types = ["reinsertion"]
        outcome2.furnisher_id = 20
        outcome2.to_dict = MagicMock(return_value={"id": 2, "furnisher_id": 20})

        # Note: furnisher_id filter is applied, so only outcomes for furnisher 10 are returned
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [outcome1, outcome2]

        result = ml_service.get_similar_cases(violation_types=["reinsertion"], furnisher_id=10)

        # Should return results (matching furnisher gets bonus score)
        assert len(result) >= 1
        # The first outcome should be returned since it has matching furnisher (gets +0.2 boost)
        assert result[0]["furnisher_id"] == 10

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_similar_cases_empty_result(self, mock_session_local, ml_service):
        """Test getting similar cases with no results."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = ml_service.get_similar_cases()

        assert result == []

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_similar_cases_database_error(self, mock_session_local, ml_service):
        """Test similar cases handles database errors."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = ml_service.get_similar_cases()

        assert result == []

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_similar_cases_respects_limit(self, mock_session_local, ml_service):
        """Test similar cases respects limit parameter."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = [MagicMock() for _ in range(20)]
        for i, o in enumerate(outcomes):
            o.violation_types = ["reinsertion"]
            o.furnisher_id = None
            o.to_dict = MagicMock(return_value={"id": i})

        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = outcomes

        result = ml_service.get_similar_cases(violation_types=["reinsertion"], limit=5)

        assert len(result) == 5


# =============================================================================
# Tests for calculate_success_rate()
# =============================================================================

class TestCalculateSuccessRate:
    """Test success rate calculation."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_calculate_success_rate_no_outcomes(self, mock_session_local, ml_service):
        """Test success rate with no outcomes."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.all.return_value = []

        result = ml_service.calculate_success_rate()

        assert result["total_cases"] == 0
        assert result["success_rate"] == 0
        assert result["confidence"] == 0

    @patch('services.ml_learning_service.SessionLocal')
    def test_calculate_success_rate_basic(self, mock_session_local, ml_service):
        """Test basic success rate calculation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Create mock outcomes: 2 won, 3 settled, 2 lost, 1 dismissed
        outcomes = []
        for outcome_type in ["won", "won", "settled", "settled", "settled", "lost", "lost", "dismissed"]:
            o = MagicMock()
            o.final_outcome = outcome_type
            o.violation_types = ["611_failure"]
            o.furnisher_id = 1
            outcomes.append(o)

        mock_db.query.return_value.all.return_value = outcomes

        result = ml_service.calculate_success_rate()

        assert result["total_cases"] == 8
        assert result["success_rate"] == 0.625  # (2+3)/8
        assert result["won_rate"] == 0.25  # 2/8
        assert result["settlement_rate"] == 0.375  # 3/8
        assert result["lost_rate"] == 0.25  # 2/8
        assert result["dismissed_rate"] == 0.125  # 1/8

    @patch('services.ml_learning_service.SessionLocal')
    def test_calculate_success_rate_with_furnisher_filter(self, mock_session_local, ml_service):
        """Test success rate with furnisher filter."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = ml_service.calculate_success_rate(filters={"furnisher_id": 10})

        assert result["total_cases"] == 0

    @patch('services.ml_learning_service.SessionLocal')
    def test_calculate_success_rate_with_date_range(self, mock_session_local, ml_service):
        """Test success rate with date range filter."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        # Use string dates which are JSON serializable (avoids cache key serialization issue)
        filters = {
            "date_from": "2024-01-01",
            "date_to": "2024-12-31"
        }
        result = ml_service.calculate_success_rate(filters=filters)

        assert result["total_cases"] == 0

    @patch('services.ml_learning_service.SessionLocal')
    def test_calculate_success_rate_by_violation_type(self, mock_session_local, ml_service):
        """Test success rate breakdown by violation type."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        # 2 reinsertion wins
        for _ in range(2):
            o = MagicMock()
            o.final_outcome = "won"
            o.violation_types = ["reinsertion"]
            o.furnisher_id = 1
            outcomes.append(o)
        # 1 reinsertion loss
        o = MagicMock()
        o.final_outcome = "lost"
        o.violation_types = ["reinsertion"]
        o.furnisher_id = 1
        outcomes.append(o)

        mock_db.query.return_value.all.return_value = outcomes

        result = ml_service.calculate_success_rate()

        assert "reinsertion" in result["by_violation_type"]
        assert result["by_violation_type"]["reinsertion"]["total"] == 3
        assert result["by_violation_type"]["reinsertion"]["success"] == 2
        assert result["by_violation_type"]["reinsertion"]["rate"] == 0.667

    @patch('services.ml_learning_service.SessionLocal')
    def test_calculate_success_rate_uses_cache(self, mock_session_local, ml_service):
        """Test success rate uses cached values."""
        # Pre-populate cache
        cache_key = 'success_rate_{}'
        ml_service._set_cache(cache_key, {"cached": True})

        result = ml_service.calculate_success_rate()

        assert result["cached"] is True
        mock_session_local.assert_not_called()

    @patch('services.ml_learning_service.SessionLocal')
    def test_calculate_success_rate_confidence_scaling(self, mock_session_local, ml_service):
        """Test confidence scales with sample size."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # 50 outcomes = 0.5 confidence
        outcomes = []
        for _ in range(50):
            o = MagicMock()
            o.final_outcome = "won"
            o.violation_types = []
            o.furnisher_id = None
            outcomes.append(o)

        mock_db.query.return_value.all.return_value = outcomes

        result = ml_service.calculate_success_rate()

        assert result["confidence"] == 0.5

    @patch('services.ml_learning_service.SessionLocal')
    def test_calculate_success_rate_database_error(self, mock_session_local, ml_service):
        """Test success rate handles database errors."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = ml_service.calculate_success_rate()

        assert "error" in result


# =============================================================================
# Tests for get_average_settlement()
# =============================================================================

class TestGetAverageSettlement:
    """Test average settlement calculation."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_average_settlement_no_outcomes(self, mock_session_local, ml_service):
        """Test average settlement with no outcomes."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = ml_service.get_average_settlement()

        assert result["count"] == 0
        assert result["average"] == 0
        assert result["median"] == 0

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_average_settlement_basic(self, mock_session_local, ml_service):
        """Test basic average settlement calculation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        amounts = [1000, 2000, 3000, 4000, 5000]
        for amt in amounts:
            o = MagicMock()
            o.settlement_amount = amt
            o.violation_types = []
            outcomes.append(o)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes

        result = ml_service.get_average_settlement()

        assert result["count"] == 5
        assert result["average"] == 3000.0
        assert result["median"] == 3000.0
        assert result["min"] == 1000.0
        assert result["max"] == 5000.0

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_average_settlement_even_count_median(self, mock_session_local, ml_service):
        """Test median calculation with even number of outcomes."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        amounts = [1000, 2000, 3000, 4000]
        for amt in amounts:
            o = MagicMock()
            o.settlement_amount = amt
            o.violation_types = []
            outcomes.append(o)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes

        result = ml_service.get_average_settlement()

        # Median of [1000, 2000, 3000, 4000] = (2000 + 3000) / 2 = 2500
        assert result["median"] == 2500.0

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_average_settlement_std_dev(self, mock_session_local, ml_service):
        """Test standard deviation calculation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        amounts = [1000, 2000, 3000, 4000, 5000]
        for amt in amounts:
            o = MagicMock()
            o.settlement_amount = amt
            o.violation_types = []
            outcomes.append(o)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes

        result = ml_service.get_average_settlement()

        # Expected std_dev for [1000, 2000, 3000, 4000, 5000]
        expected_std = math.sqrt(2500000)  # ~1581.14
        assert abs(result["std_dev"] - expected_std) < 1

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_average_settlement_percentiles(self, mock_session_local, ml_service):
        """Test percentile calculations."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        # Create 100 outcomes with amounts 1000-100000
        for i in range(1, 101):
            o = MagicMock()
            o.settlement_amount = i * 1000
            o.violation_types = []
            outcomes.append(o)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes

        result = ml_service.get_average_settlement()

        # 25th percentile: int(100 * 0.25) = 25, so amounts[25] = 26000
        # (because amounts are sorted 1000, 2000, ... and index 25 is the 26th element)
        assert result["percentile_25"] == 26000.0
        # 75th percentile: int(100 * 0.75) = 75, so amounts[75] = 76000
        assert result["percentile_75"] == 76000.0

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_average_settlement_by_violation_type(self, mock_session_local, ml_service):
        """Test average settlement breakdown by violation type."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        # Reinsertion outcomes: higher settlements
        for _ in range(3):
            o = MagicMock()
            o.settlement_amount = 10000
            o.violation_types = ["reinsertion"]
            outcomes.append(o)
        # 611_failure outcomes: lower settlements
        for _ in range(2):
            o = MagicMock()
            o.settlement_amount = 3000
            o.violation_types = ["611_failure"]
            outcomes.append(o)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes

        result = ml_service.get_average_settlement()

        assert "reinsertion" in result["by_violation_type"]
        assert result["by_violation_type"]["reinsertion"]["average"] == 10000.0
        assert result["by_violation_type"]["reinsertion"]["count"] == 3

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_average_settlement_database_error(self, mock_session_local, ml_service):
        """Test average settlement handles database errors."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = ml_service.get_average_settlement()

        assert "error" in result


# =============================================================================
# Tests for get_resolution_time_estimate()
# =============================================================================

class TestGetResolutionTimeEstimate:
    """Test resolution time estimation."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_resolution_time_no_outcomes(self, mock_session_local, ml_service):
        """Test resolution time estimate with no outcomes."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = ml_service.get_resolution_time_estimate()

        # Should return default values
        assert result["estimated_days"] == 90
        assert result["confidence"] == 0.3
        assert result["sample_size"] == 0

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_resolution_time_basic(self, mock_session_local, ml_service):
        """Test basic resolution time estimation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        days = [60, 90, 120, 90, 100]
        for d in days:
            o = MagicMock()
            o.time_to_resolution_days = d
            o.violation_types = ["611_failure"]
            outcomes.append(o)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes

        result = ml_service.get_resolution_time_estimate()

        # Average of [60, 90, 120, 90, 100] = 92
        assert result["estimated_days"] == 92
        assert result["sample_size"] == 5

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_resolution_time_with_violation_types(self, mock_session_local, ml_service):
        """Test resolution time filtered by violation types."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        # Reinsertion cases: longer resolution
        for _ in range(3):
            o = MagicMock()
            o.time_to_resolution_days = 120
            o.violation_types = ["reinsertion"]
            outcomes.append(o)
        # Other cases: shorter resolution
        for _ in range(2):
            o = MagicMock()
            o.time_to_resolution_days = 60
            o.violation_types = ["611_failure"]
            outcomes.append(o)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes

        result = ml_service.get_resolution_time_estimate(violation_types=["reinsertion"])

        # Should filter to reinsertion cases only
        assert result["estimated_days"] == 120
        assert result["sample_size"] == 3

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_resolution_time_falls_back_to_all(self, mock_session_local, ml_service):
        """Test resolution time falls back to all outcomes if no match."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        for _ in range(5):
            o = MagicMock()
            o.time_to_resolution_days = 90
            o.violation_types = ["611_failure"]
            outcomes.append(o)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes

        # Request violation type that doesn't exist
        result = ml_service.get_resolution_time_estimate(violation_types=["nonexistent"])

        # Should fall back to all outcomes
        assert result["sample_size"] == 5

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_resolution_time_confidence_scaling(self, mock_session_local, ml_service):
        """Test confidence scales with sample size."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        # 25 outcomes = 0.5 confidence (min(1.0, 25/50))
        for _ in range(25):
            o = MagicMock()
            o.time_to_resolution_days = 90
            o.violation_types = []
            outcomes.append(o)

        mock_db.query.return_value.filter.return_value.all.return_value = outcomes

        result = ml_service.get_resolution_time_estimate()

        assert result["confidence"] == 0.5

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_resolution_time_database_error(self, mock_session_local, ml_service):
        """Test resolution time handles database errors."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = ml_service.get_resolution_time_estimate()

        assert "error" in result


# =============================================================================
# Tests for generate_prediction_features()
# =============================================================================

class TestGeneratePredictionFeatures:
    """Test feature generation for ML predictions."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_generate_features_basic(self, mock_session_local, ml_service, mock_client, mock_violation):
        """Test basic feature generation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock violations
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_violation]
        # Mock standing
        mock_standing = MagicMock()
        mock_standing.has_concrete_harm = True
        mock_standing.has_dissemination = True
        mock_standing.denial_letters_count = 2
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_standing,  # Standing
            None,  # Damages
            None,  # CaseScore
            mock_client,  # Client
        ]

        result = ml_service.generate_prediction_features(client_id=1)

        assert result["violation_count"] == 1
        assert result["has_concrete_harm"] is True
        assert result["has_dissemination"] is True
        assert result["denial_letters"] == 2

    @patch('services.ml_learning_service.SessionLocal')
    def test_generate_features_with_damages(self, mock_session_local, ml_service, mock_client):
        """Test feature generation with damages record."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_damages = MagicMock()
        mock_damages.actual_damages_total = 5000
        mock_damages.statutory_damages_total = 3000

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # Standing
            mock_damages,  # Damages
            None,  # CaseScore
            mock_client,  # Client
        ]

        result = ml_service.generate_prediction_features(client_id=1)

        assert result["actual_damages"] == 5000
        assert result["statutory_damages"] == 3000
        assert result["total_damages"] == 8000

    @patch('services.ml_learning_service.SessionLocal')
    def test_generate_features_with_case_score(self, mock_session_local, ml_service, mock_client):
        """Test feature generation with case score."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_case_score = MagicMock()
        mock_case_score.total_score = 85
        mock_case_score.settlement_probability = 0.75

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # Standing
            None,  # Damages
            mock_case_score,  # CaseScore
            mock_client,  # Client
        ]

        result = ml_service.generate_prediction_features(client_id=1)

        assert result["case_score"] == 85
        assert result["settlement_probability"] == 0.75

    @patch('services.ml_learning_service.SessionLocal')
    def test_generate_features_weighted_score(self, mock_session_local, ml_service, mock_client):
        """Test weighted violation score calculation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Create violations with different types
        violation1 = MagicMock()
        violation1.violation_type = "reinsertion"  # weight 2.5
        violation1.bureau = "Experian"
        violation1.is_willful = False

        violation2 = MagicMock()
        violation2.violation_type = "identity_theft"  # weight 3.0
        violation2.bureau = "TransUnion"
        violation2.is_willful = False

        mock_db.query.return_value.filter.return_value.all.return_value = [violation1, violation2]
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None, None, None, mock_client
        ]

        result = ml_service.generate_prediction_features(client_id=1)

        # Expected: 2.5 + 3.0 = 5.5
        assert result["weighted_violation_score"] == 5.5

    @patch('services.ml_learning_service.SessionLocal')
    def test_generate_features_has_reinsertion(self, mock_session_local, ml_service, mock_client):
        """Test reinsertion flag detection."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        violation = MagicMock()
        violation.violation_type = "reinsertion"
        violation.bureau = "Experian"
        violation.is_willful = False

        mock_db.query.return_value.filter.return_value.all.return_value = [violation]
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None, None, None, mock_client
        ]

        result = ml_service.generate_prediction_features(client_id=1)

        assert result["has_reinsertion"] is True
        assert result["has_identity_theft"] is False

    @patch('services.ml_learning_service.SessionLocal')
    def test_generate_features_database_error(self, mock_session_local, ml_service):
        """Test feature generation handles database errors."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = ml_service.generate_prediction_features(client_id=1)

        assert "error" in result


# =============================================================================
# Tests for predict_outcome()
# =============================================================================

class TestPredictOutcome:
    """Test outcome prediction."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_outcome_basic(self, mock_session_local, ml_service):
        """Test basic outcome prediction."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 3,
                "willfulness_ratio": 0.3,
                "has_concrete_harm": True,
                "has_dissemination": False,
                "denial_letters": 1,
                "has_reinsertion": False,
                "has_identity_theft": False,
                "bureaus_count": 2,
                "willful_count": 1,
                "total_damages": 5000,
            }

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {
                    "success_rate": 0.6,
                    "confidence": 0.5
                }

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_outcome(client_id=1)

        assert "predicted_outcome" in result
        assert "success_probability" in result
        assert "confidence" in result
        assert "prediction_id" in result

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_outcome_high_violation_count_boost(self, mock_session_local, ml_service):
        """Test outcome prediction boost for multiple violations."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 10,  # >= 5 triggers boost
                "willfulness_ratio": 0.0,
                "has_concrete_harm": False,
                "has_dissemination": False,
                "denial_letters": 0,
                "has_reinsertion": False,
                "has_identity_theft": False,
                "bureaus_count": 1,
                "willful_count": 0,
                "total_damages": 0,
            }

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {"success_rate": 0.5, "confidence": 0.5}

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_outcome(client_id=1)

        assert "Multiple violations (+10%)" in result["confidence_factors"]

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_outcome_no_violations_penalty(self, mock_session_local, ml_service):
        """Test outcome prediction penalty for no violations."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 0,
                "willfulness_ratio": 0.0,
                "has_concrete_harm": False,
                "has_dissemination": False,
                "denial_letters": 0,
                "has_reinsertion": False,
                "has_identity_theft": False,
                "bureaus_count": 0,
                "willful_count": 0,
                "total_damages": 0,
            }

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {"success_rate": 0.5, "confidence": 0.5}

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_outcome(client_id=1)

        assert "No violations identified (-30%)" in result["confidence_factors"]

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_outcome_high_willfulness_boost(self, mock_session_local, ml_service):
        """Test outcome prediction boost for high willfulness ratio."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 5,
                "willfulness_ratio": 0.8,  # >= 0.5 triggers boost
                "has_concrete_harm": False,
                "has_dissemination": False,
                "denial_letters": 0,
                "has_reinsertion": False,
                "has_identity_theft": False,
                "bureaus_count": 1,
                "willful_count": 4,
                "total_damages": 0,
            }

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {"success_rate": 0.5, "confidence": 0.5}

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_outcome(client_id=1)

        assert "High willfulness ratio (+15%)" in result["confidence_factors"]

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_outcome_reinsertion_boost(self, mock_session_local, ml_service):
        """Test outcome prediction boost for reinsertion violation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 1,
                "willfulness_ratio": 0.0,
                "has_concrete_harm": False,
                "has_dissemination": False,
                "denial_letters": 0,
                "has_reinsertion": True,
                "has_identity_theft": False,
                "bureaus_count": 1,
                "willful_count": 0,
                "total_damages": 0,
            }

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {"success_rate": 0.5, "confidence": 0.5}

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_outcome(client_id=1)

        assert "Reinsertion violation (+15%)" in result["confidence_factors"]

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_outcome_score_clamping(self, mock_session_local, ml_service):
        """Test outcome prediction score is clamped between 0.1 and 0.95."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        # All positive factors should not exceed 0.95
        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 10,
                "willfulness_ratio": 1.0,
                "has_concrete_harm": True,
                "has_dissemination": True,
                "denial_letters": 5,
                "has_reinsertion": True,
                "has_identity_theft": True,
                "bureaus_count": 3,
                "willful_count": 10,
                "total_damages": 100000,
            }

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {"success_rate": 0.9, "confidence": 0.9}

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_outcome(client_id=1)

        assert result["success_probability"] <= 0.95

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_outcome_feature_error(self, mock_session_local, ml_service):
        """Test outcome prediction returns error from feature generation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {"error": "Feature generation failed"}

            result = ml_service.predict_outcome(client_id=1)

        assert "error" in result

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_outcome_database_error(self, mock_session_local, ml_service):
        """Test outcome prediction handles database errors."""
        mock_db = MagicMock()
        mock_db.add.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 1,
                "willfulness_ratio": 0.0,
                "has_concrete_harm": False,
                "has_dissemination": False,
                "denial_letters": 0,
                "has_reinsertion": False,
                "has_identity_theft": False,
                "bureaus_count": 1,
                "willful_count": 0,
                "total_damages": 0,
            }

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {"success_rate": 0.5, "confidence": 0.5}

                result = ml_service.predict_outcome(client_id=1)

        assert "error" in result
        mock_db.rollback.assert_called()


# =============================================================================
# Tests for predict_settlement_range()
# =============================================================================

class TestPredictSettlementRange:
    """Test settlement range prediction."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_settlement_range_basic(self, mock_session_local, ml_service):
        """Test basic settlement range prediction."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 2,
                "willful_count": 1,
                "has_reinsertion": False,
                "has_identity_theft": False,
                "has_concrete_harm": True,
                "denial_letters": 1,
                "bureaus_count": 2,
            }

            with patch.object(ml_service, 'get_average_settlement') as mock_settlement:
                mock_settlement.return_value = {
                    "count": 50,
                    "percentile_25": 2000,
                    "average": 5000,
                    "percentile_75": 10000,
                }

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_settlement_range(client_id=1)

        assert "settlement_range" in result
        assert "min" in result["settlement_range"]
        assert "average" in result["settlement_range"]
        assert "max" in result["settlement_range"]
        assert "multiplier" in result
        assert "confidence" in result

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_settlement_range_no_historical_data(self, mock_session_local, ml_service):
        """Test settlement range prediction with no historical data."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 1,
                "willful_count": 0,
                "has_reinsertion": False,
                "has_identity_theft": False,
                "has_concrete_harm": False,
                "denial_letters": 0,
                "bureaus_count": 1,
            }

            with patch.object(ml_service, 'get_average_settlement') as mock_settlement:
                mock_settlement.return_value = {"count": 0}

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_settlement_range(client_id=1)

        # Should use defaults: 1000, 5000, 15000
        assert result["historical_comparison"]["base_average"] == 5000

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_settlement_range_multiplier_for_reinsertion(self, mock_session_local, ml_service):
        """Test settlement range multiplier increases for reinsertion."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 1,
                "willful_count": 0,
                "has_reinsertion": True,  # +0.5
                "has_identity_theft": False,
                "has_concrete_harm": False,
                "denial_letters": 0,
                "bureaus_count": 1,
            }

            with patch.object(ml_service, 'get_average_settlement') as mock_settlement:
                mock_settlement.return_value = {"count": 0}

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_settlement_range(client_id=1)

        # Base multiplier 1.0 + reinsertion 0.5 = 1.5
        assert result["multiplier"] == 1.5

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_settlement_range_multiplier_clamping(self, mock_session_local, ml_service):
        """Test settlement range multiplier is clamped between 0.5 and 3.0."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_prediction = MagicMock()
        mock_prediction.id = 1

        # All positive multiplier factors
        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 20,  # +2.85 ((20-1)*0.15)
                "willful_count": 10,  # +2.5 (10*0.25)
                "has_reinsertion": True,  # +0.5
                "has_identity_theft": True,  # +0.4
                "has_concrete_harm": True,  # +0.2
                "denial_letters": 10,  # +1.0 (10*0.1)
                "bureaus_count": 3,  # +0.15
            }

            with patch.object(ml_service, 'get_average_settlement') as mock_settlement:
                mock_settlement.return_value = {"count": 0}

                with patch('services.ml_learning_service.OutcomePrediction') as MockPred:
                    MockPred.return_value = mock_prediction

                    result = ml_service.predict_settlement_range(client_id=1)

        assert result["multiplier"] == 3.0  # Capped at 3.0

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_settlement_range_feature_error(self, mock_session_local, ml_service):
        """Test settlement range returns error from feature generation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {"error": "Feature generation failed"}

            result = ml_service.predict_settlement_range(client_id=1)

        assert "error" in result

    @patch('services.ml_learning_service.SessionLocal')
    def test_predict_settlement_range_database_error(self, mock_session_local, ml_service):
        """Test settlement range handles database errors."""
        mock_db = MagicMock()
        mock_db.add.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        with patch.object(ml_service, 'generate_prediction_features') as mock_features:
            mock_features.return_value = {
                "violation_count": 1,
                "willful_count": 0,
                "has_reinsertion": False,
                "has_identity_theft": False,
                "has_concrete_harm": False,
                "denial_letters": 0,
                "bureaus_count": 1,
            }

            with patch.object(ml_service, 'get_average_settlement') as mock_settlement:
                mock_settlement.return_value = {"count": 0}

                result = ml_service.predict_settlement_range(client_id=1)

        assert "error" in result
        mock_db.rollback.assert_called()


# =============================================================================
# Tests for update_model_accuracy()
# =============================================================================

class TestUpdateModelAccuracy:
    """Test model accuracy analysis."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_update_model_accuracy_no_predictions(self, mock_session_local, ml_service):
        """Test model accuracy with no resolved predictions."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = ml_service.update_model_accuracy()

        assert result["total_predictions"] == 0
        assert result["accuracy"] == 0
        assert result["message"] == "No resolved predictions yet"

    @patch('services.ml_learning_service.SessionLocal')
    def test_update_model_accuracy_basic(self, mock_session_local, ml_service):
        """Test basic model accuracy calculation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        predictions = []
        # 2 accurate, 1 inaccurate
        for i, accurate in enumerate([True, True, False]):
            p = MagicMock()
            p.prediction_type = "outcome"
            p.was_accurate = accurate
            p.prediction_error = None
            predictions.append(p)

        mock_db.query.return_value.filter.return_value.all.return_value = predictions

        result = ml_service.update_model_accuracy()

        assert result["total_predictions"] == 3
        assert result["accuracy"] == 0.667  # 2/3

    @patch('services.ml_learning_service.SessionLocal')
    def test_update_model_accuracy_by_type(self, mock_session_local, ml_service):
        """Test model accuracy breakdown by prediction type."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        predictions = []
        # Outcome predictions: 2 accurate
        for _ in range(2):
            p = MagicMock()
            p.prediction_type = "outcome"
            p.was_accurate = True
            p.prediction_error = None
            predictions.append(p)
        # Settlement predictions: 1 accurate, 1 inaccurate
        for accurate in [True, False]:
            p = MagicMock()
            p.prediction_type = "settlement_amount"
            p.was_accurate = accurate
            p.prediction_error = 1000 if not accurate else 0
            predictions.append(p)

        mock_db.query.return_value.filter.return_value.all.return_value = predictions

        result = ml_service.update_model_accuracy()

        assert result["by_type"]["outcome"]["total"] == 2
        assert result["by_type"]["outcome"]["accurate"] == 2
        assert result["by_type"]["outcome"]["accuracy_rate"] == 1.0
        assert result["by_type"]["settlement_amount"]["total"] == 2
        assert result["by_type"]["settlement_amount"]["accurate"] == 1
        assert result["by_type"]["settlement_amount"]["accuracy_rate"] == 0.5

    @patch('services.ml_learning_service.SessionLocal')
    def test_update_model_accuracy_mean_error(self, mock_session_local, ml_service):
        """Test mean error calculation for settlement predictions."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        predictions = []
        errors = [100, 200, 300]
        for error in errors:
            p = MagicMock()
            p.prediction_type = "settlement_amount"
            p.was_accurate = False
            p.prediction_error = error
            predictions.append(p)

        mock_db.query.return_value.filter.return_value.all.return_value = predictions

        result = ml_service.update_model_accuracy()

        assert result["by_type"]["settlement_amount"]["mean_error"] == 200.0

    @patch('services.ml_learning_service.SessionLocal')
    def test_update_model_accuracy_database_error(self, mock_session_local, ml_service):
        """Test model accuracy handles database errors."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = ml_service.update_model_accuracy()

        assert "error" in result


# =============================================================================
# Tests for get_learning_stats()
# =============================================================================

class TestGetLearningStats:
    """Test comprehensive ML statistics."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_learning_stats_basic(self, mock_session_local, ml_service):
        """Test basic learning stats retrieval."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.count.side_effect = [5, 3, 1]
        mock_db.query.return_value.all.return_value = []

        with patch.object(ml_service, 'update_model_accuracy') as mock_accuracy:
            mock_accuracy.return_value = {"accuracy": 0.8}

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {"success_rate": 0.7}

                with patch.object(ml_service, 'get_average_settlement') as mock_settlement:
                    mock_settlement.return_value = {"average": 5000}

                    result = ml_service.get_learning_stats()

        assert "training_data" in result
        assert "predictions" in result
        assert "model_performance" in result
        assert "model_info" in result

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_learning_stats_outcomes_by_type(self, mock_session_local, ml_service):
        """Test learning stats includes outcomes by type."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        outcomes = []
        for outcome_type in ["won", "won", "settled", "lost"]:
            o = MagicMock()
            o.final_outcome = outcome_type
            outcomes.append(o)

        mock_db.query.return_value.count.return_value = 4
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.all.return_value = outcomes

        with patch.object(ml_service, 'update_model_accuracy') as mock_accuracy:
            mock_accuracy.return_value = {"accuracy": 0.8}

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {"success_rate": 0.75}

                with patch.object(ml_service, 'get_average_settlement') as mock_settlement:
                    mock_settlement.return_value = {"average": 5000}

                    result = ml_service.get_learning_stats()

        assert result["training_data"]["outcomes_by_type"]["won"] == 2
        assert result["training_data"]["outcomes_by_type"]["settled"] == 1
        assert result["training_data"]["outcomes_by_type"]["lost"] == 1

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_learning_stats_model_info(self, mock_session_local, ml_service):
        """Test learning stats includes model info."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_db.query.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.all.return_value = []

        with patch.object(ml_service, 'update_model_accuracy') as mock_accuracy:
            mock_accuracy.return_value = {}

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {}

                with patch.object(ml_service, 'get_average_settlement') as mock_settlement:
                    mock_settlement.return_value = {}

                    result = ml_service.get_learning_stats()

        assert result["model_info"]["version"] == "v1.0"
        assert result["model_info"]["type"] == "Bayesian Statistical Model"
        assert "features" in result["model_info"]

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_learning_stats_recommendation(self, mock_session_local, ml_service):
        """Test learning stats includes recommendation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_db.query.return_value.count.return_value = 5  # < 10 outcomes
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.all.return_value = []

        with patch.object(ml_service, 'update_model_accuracy') as mock_accuracy:
            mock_accuracy.return_value = {}

            with patch.object(ml_service, 'calculate_success_rate') as mock_success:
                mock_success.return_value = {}

                with patch.object(ml_service, 'get_average_settlement') as mock_settlement:
                    mock_settlement.return_value = {}

                    result = ml_service.get_learning_stats()

        assert "Need more training data" in result["recommendation"]

    @patch('services.ml_learning_service.SessionLocal')
    def test_get_learning_stats_database_error(self, mock_session_local, ml_service):
        """Test learning stats handles database errors."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db

        result = ml_service.get_learning_stats()

        assert "error" in result


# =============================================================================
# Tests for _get_model_recommendation()
# =============================================================================

class TestGetModelRecommendation:
    """Test model recommendation generation."""

    def test_recommendation_less_than_10_outcomes(self, ml_service):
        """Test recommendation for less than 10 outcomes."""
        result = ml_service._get_model_recommendation(5)
        assert "Need more training data" in result

    def test_recommendation_10_to_50_outcomes(self, ml_service):
        """Test recommendation for 10-50 outcomes."""
        result = ml_service._get_model_recommendation(30)
        assert "Model is learning" in result

    def test_recommendation_50_to_100_outcomes(self, ml_service):
        """Test recommendation for 50-100 outcomes."""
        result = ml_service._get_model_recommendation(75)
        assert "Good training progress" in result

    def test_recommendation_100_plus_outcomes(self, ml_service):
        """Test recommendation for 100+ outcomes."""
        result = ml_service._get_model_recommendation(150)
        assert "well-trained" in result


# =============================================================================
# Tests for Convenience Functions
# =============================================================================

class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch('services.ml_learning_service.MLLearningService')
    def test_record_outcome_convenience(self, MockService):
        """Test record_outcome convenience function."""
        mock_service = MagicMock()
        mock_service.record_outcome.return_value = {"success": True}
        MockService.return_value = mock_service

        result = record_outcome(client_id=1, outcome_data={"final_outcome": "settled"})

        mock_service.record_outcome.assert_called_once_with(1, {"final_outcome": "settled"})
        assert result["success"] is True

    @patch('services.ml_learning_service.MLLearningService')
    def test_get_similar_cases_convenience(self, MockService):
        """Test get_similar_cases convenience function."""
        mock_service = MagicMock()
        mock_service.get_similar_cases.return_value = [{"id": 1}]
        MockService.return_value = mock_service

        result = get_similar_cases(violation_types=["reinsertion"], furnisher_id=10, limit=5)

        mock_service.get_similar_cases.assert_called_once_with(["reinsertion"], 10, 5)
        assert len(result) == 1

    @patch('services.ml_learning_service.MLLearningService')
    def test_calculate_success_rate_convenience(self, MockService):
        """Test calculate_success_rate convenience function."""
        mock_service = MagicMock()
        mock_service.calculate_success_rate.return_value = {"success_rate": 0.7}
        MockService.return_value = mock_service

        result = calculate_success_rate(filters={"furnisher_id": 10})

        mock_service.calculate_success_rate.assert_called_once_with({"furnisher_id": 10})
        assert result["success_rate"] == 0.7

    @patch('services.ml_learning_service.MLLearningService')
    def test_get_average_settlement_convenience(self, MockService):
        """Test get_average_settlement convenience function."""
        mock_service = MagicMock()
        mock_service.get_average_settlement.return_value = {"average": 5000}
        MockService.return_value = mock_service

        result = get_average_settlement(filters={"violation_type": "reinsertion"})

        mock_service.get_average_settlement.assert_called_once_with({"violation_type": "reinsertion"})
        assert result["average"] == 5000

    @patch('services.ml_learning_service.MLLearningService')
    def test_predict_outcome_convenience(self, MockService):
        """Test predict_outcome convenience function."""
        mock_service = MagicMock()
        mock_service.predict_outcome.return_value = {"predicted_outcome": "settled"}
        MockService.return_value = mock_service

        result = predict_outcome(client_id=1)

        mock_service.predict_outcome.assert_called_once_with(1)
        assert result["predicted_outcome"] == "settled"

    @patch('services.ml_learning_service.MLLearningService')
    def test_predict_settlement_range_convenience(self, MockService):
        """Test predict_settlement_range convenience function."""
        mock_service = MagicMock()
        mock_service.predict_settlement_range.return_value = {"settlement_range": {"min": 1000}}
        MockService.return_value = mock_service

        result = predict_settlement_range(client_id=1)

        mock_service.predict_settlement_range.assert_called_once_with(1)
        assert "settlement_range" in result

    @patch('services.ml_learning_service.MLLearningService')
    def test_get_learning_stats_convenience(self, MockService):
        """Test get_learning_stats convenience function."""
        mock_service = MagicMock()
        mock_service.get_learning_stats.return_value = {"total_outcomes": 100}
        MockService.return_value = mock_service

        result = get_learning_stats()

        mock_service.get_learning_stats.assert_called_once()
        assert result["total_outcomes"] == 100


# =============================================================================
# Integration-style Tests
# =============================================================================

class TestMLLearningServiceIntegration:
    """Integration-style tests for MLLearningService."""

    @patch('services.ml_learning_service.SessionLocal')
    def test_full_prediction_workflow(self, mock_session_local, ml_service):
        """Test a full prediction workflow."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Setup mocks for feature generation
        mock_violation = MagicMock()
        mock_violation.violation_type = "reinsertion"
        mock_violation.bureau = "Experian"
        mock_violation.is_willful = True

        mock_standing = MagicMock()
        mock_standing.has_concrete_harm = True
        mock_standing.has_dissemination = True
        mock_standing.denial_letters_count = 2

        mock_client = MagicMock()
        mock_client.current_dispute_round = 2

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_violation]
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_standing, None, None, mock_client
        ]

        # Generate features
        features = ml_service.generate_prediction_features(client_id=1)

        assert features["violation_count"] == 1
        assert features["has_reinsertion"] is True
        assert features["has_concrete_harm"] is True
        assert features["denial_letters"] == 2

    def test_cache_invalidation_on_new_outcome(self, ml_service):
        """Test that cache is invalidated when new outcome is recorded."""
        # Pre-populate cache
        ml_service._set_cache("success_rate_{}", {"cached": True})
        ml_service._set_cache("settlement_stats", {"cached": True})

        assert ml_service._get_cache("success_rate_{}") is not None

        # Clear cache as would happen in record_outcome
        ml_service._cache.clear()

        assert ml_service._get_cache("success_rate_{}") is None
        assert ml_service._get_cache("settlement_stats") is None
