"""
Comprehensive Unit Tests for Pattern Analyzer Service

Tests cover:
- PatternAnalyzerService initialization and caching
- Furnisher behavior analysis
- Seasonal trend detection
- Winning strategy identification
- Attorney strength analysis
- Pattern insights retrieval
- Pattern refresh functionality
- Convenience functions
- Edge cases and error handling
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pattern_analyzer_service import (
    PatternAnalyzerService,
    analyze_furnisher_behavior,
    detect_seasonal_trends,
    identify_winning_strategies,
    find_attorney_strengths,
    get_pattern_insights,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def service():
    """Create a fresh PatternAnalyzerService for each test"""
    return PatternAnalyzerService()


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def mock_outcome():
    """Create a mock CaseOutcome object"""
    outcome = Mock()
    outcome.furnisher_id = 1
    outcome.final_outcome = "settled"
    outcome.settlement_amount = 5000.0
    outcome.time_to_resolution_days = 60
    outcome.violation_types = ["FCRA_1681e", "FCRA_1681i"]
    outcome.attorney_id = 1
    outcome.created_at = datetime.utcnow() - timedelta(days=30)
    outcome.documentation_quality = 0.8
    outcome.dispute_rounds_completed = 2
    return outcome


@pytest.fixture
def mock_furnisher():
    """Create a mock Furnisher object"""
    furnisher = Mock()
    furnisher.id = 1
    furnisher.name = "Test Furnisher Inc"
    return furnisher


@pytest.fixture
def mock_staff():
    """Create a mock Staff object"""
    staff = Mock()
    staff.id = 1
    staff.full_name = "Test Attorney"
    return staff


@pytest.fixture
def mock_pattern():
    """Create a mock FurnisherPattern object"""
    pattern = Mock()
    pattern.id = 1
    pattern.furnisher_id = 1
    pattern.furnisher_name = "Test Furnisher"
    pattern.pattern_type = "response_behavior"
    pattern.pattern_data = {"settlement_rate": 0.75, "avg_settlement": 5000.0}
    pattern.sample_size = 20
    pattern.confidence = 0.85
    pattern.last_updated = datetime.utcnow()
    return pattern


# ============================================================================
# PatternAnalyzerService Initialization Tests
# ============================================================================


class TestPatternAnalyzerServiceInit:
    """Tests for PatternAnalyzerService initialization"""

    def test_init_creates_empty_cache(self, service):
        """Test initialization creates empty cache"""
        assert service._cache == {}
        assert service._cache_expiry == {}

    def test_init_sets_cache_duration(self, service):
        """Test initialization sets default cache duration"""
        assert service._cache_duration == timedelta(minutes=30)

    def test_pattern_types_constant(self, service):
        """Test PATTERN_TYPES constant is defined"""
        assert "response_behavior" in service.PATTERN_TYPES
        assert "settlement_tendency" in service.PATTERN_TYPES
        assert "seasonal_trend" in service.PATTERN_TYPES
        assert "violation_correlation" in service.PATTERN_TYPES
        assert "attorney_performance" in service.PATTERN_TYPES


# ============================================================================
# Cache Tests
# ============================================================================


class TestPatternAnalyzerServiceCache:
    """Tests for caching functionality"""

    def test_get_cache_miss(self, service):
        """Test cache miss returns None"""
        result = service._get_cache("nonexistent_key")
        assert result is None

    def test_set_and_get_cache(self, service):
        """Test setting and getting cache value"""
        service._set_cache("test_key", {"data": "test_value"})
        result = service._get_cache("test_key")
        assert result == {"data": "test_value"}

    def test_cache_expiration(self, service):
        """Test cache expires after duration"""
        service._cache_duration = timedelta(seconds=0)
        service._set_cache("test_key", {"data": "value"})

        # Cache should be expired
        result = service._get_cache("test_key")
        assert result is None

    def test_cache_not_expired(self, service):
        """Test cache is valid within duration"""
        service._set_cache("test_key", {"data": "value"})

        # Cache should still be valid
        result = service._get_cache("test_key")
        assert result == {"data": "value"}


# ============================================================================
# analyze_furnisher_behavior Tests
# ============================================================================


class TestAnalyzeFurnisherBehavior:
    """Tests for analyze_furnisher_behavior method"""

    def test_analyze_requires_furnisher_id_or_name(self, service):
        """Test that method requires furnisher_id or furnisher_name"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            result = service.analyze_furnisher_behavior()

            assert "error" in result
            assert "Must provide furnisher_id or furnisher_name" in result["error"]

    def test_analyze_by_furnisher_id(self, service, mock_furnisher, mock_outcome):
        """Test analysis by furnisher ID"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Setup query mocks
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = [mock_outcome]
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            assert result["furnisher_id"] == 1
            assert result["sample_size"] == 1
            assert "statistics" in result
            assert "patterns" in result
            assert "insights" in result

    def test_analyze_by_furnisher_name(self, service, mock_furnisher, mock_outcome):
        """Test analysis by furnisher name"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = [mock_outcome]
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_name="Test Furnisher")

            assert result["furnisher_name"] == "Test Furnisher Inc"
            assert result["sample_size"] == 1

    def test_analyze_furnisher_not_found_by_name(self, service):
        """Test analysis when furnisher not found by name"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None
            mock_query.all.return_value = []
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_name="Unknown")

            assert result["furnisher_name"] == "Unknown"
            assert result["sample_size"] == 0
            assert "No historical data" in result["insights"]

    def test_analyze_no_outcomes(self, service, mock_furnisher):
        """Test analysis with no case outcomes"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = []
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            assert result["sample_size"] == 0
            assert result["patterns"] == []
            assert "No historical data" in result["insights"]

    def test_analyze_high_settlement_rate(self, service, mock_furnisher):
        """Test analysis detects high settlement tendency"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Create 10 outcomes with 8 settled (80% rate)
            outcomes = []
            for i in range(10):
                outcome = Mock()
                outcome.furnisher_id = 1
                outcome.final_outcome = "settled" if i < 8 else "lost"
                outcome.settlement_amount = 5000.0 if i < 8 else 0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = ["FCRA_1681e"]
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            pattern_types = [p["type"] for p in result["patterns"]]
            assert "high_settlement_tendency" in pattern_types

    def test_analyze_low_settlement_rate(self, service, mock_furnisher):
        """Test analysis detects low settlement tendency"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Create 10 outcomes with 2 settled (20% rate)
            outcomes = []
            for i in range(10):
                outcome = Mock()
                outcome.furnisher_id = 1
                outcome.final_outcome = "settled" if i < 2 else "lost"
                outcome.settlement_amount = 5000.0 if i < 2 else 0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = ["FCRA_1681e"]
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            pattern_types = [p["type"] for p in result["patterns"]]
            assert "low_settlement_tendency" in pattern_types

    def test_analyze_fast_resolution(self, service, mock_furnisher):
        """Test analysis detects fast resolution pattern"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for i in range(5):
                outcome = Mock()
                outcome.furnisher_id = 1
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 5000.0
                outcome.time_to_resolution_days = 30  # Fast resolution
                outcome.violation_types = ["FCRA_1681e"]
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            pattern_types = [p["type"] for p in result["patterns"]]
            assert "fast_resolution" in pattern_types

    def test_analyze_slow_resolution(self, service, mock_furnisher):
        """Test analysis detects slow resolution pattern"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for i in range(5):
                outcome = Mock()
                outcome.furnisher_id = 1
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 5000.0
                outcome.time_to_resolution_days = 150  # Slow resolution
                outcome.violation_types = ["FCRA_1681e"]
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            pattern_types = [p["type"] for p in result["patterns"]]
            assert "slow_resolution" in pattern_types

    def test_analyze_most_effective_violation(self, service, mock_furnisher):
        """Test analysis identifies most effective violation type"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            # Add 5 successful FCRA_1681e violations
            for i in range(5):
                outcome = Mock()
                outcome.furnisher_id = 1
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 5000.0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = ["FCRA_1681e"]
                outcomes.append(outcome)

            # Add 5 unsuccessful FCRA_1681i violations
            for i in range(5):
                outcome = Mock()
                outcome.furnisher_id = 1
                outcome.final_outcome = "lost"
                outcome.settlement_amount = 0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = ["FCRA_1681i"]
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            pattern_types = [p["type"] for p in result["patterns"]]
            assert "most_effective_violation" in pattern_types

            effective_pattern = next(p for p in result["patterns"] if p["type"] == "most_effective_violation")
            assert effective_pattern["value"] == "FCRA_1681e"

    def test_analyze_db_exception_handling(self, service):
        """Test analysis handles database exceptions"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_db.query.side_effect = Exception("Database error")
            mock_db.close = Mock()
            mock_session.return_value = mock_db

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            assert "error" in result
            assert "Database error" in result["error"]

    def test_analyze_confidence_calculation(self, service, mock_furnisher):
        """Test confidence is calculated correctly based on sample size"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Create 20 outcomes (max confidence of 0.9)
            outcomes = []
            for i in range(20):
                outcome = Mock()
                outcome.furnisher_id = 1
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 5000.0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = []
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            assert result["confidence"] == 0.9


# ============================================================================
# detect_seasonal_trends Tests
# ============================================================================


class TestDetectSeasonalTrends:
    """Tests for detect_seasonal_trends method"""

    def test_seasonal_insufficient_data(self, service):
        """Test seasonal trends with insufficient data"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Only 5 outcomes (less than 12)
            outcomes = [Mock() for _ in range(5)]

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.detect_seasonal_trends()

            assert "Need at least 12 cases" in result["message"]
            assert result["sample_size"] == 5
            assert result["trends"] == []

    def test_seasonal_uses_cache(self, service):
        """Test seasonal trends uses cache on second call"""
        cached_data = {"cached": True, "trends": []}
        service._set_cache("seasonal_trends", cached_data)

        result = service.detect_seasonal_trends()

        assert result == cached_data

    def test_seasonal_calculates_monthly_stats(self, service):
        """Test seasonal trends calculates monthly statistics"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Create outcomes for different months
            outcomes = []
            for month in range(1, 13):
                for _ in range(2):
                    outcome = Mock()
                    outcome.created_at = datetime(2024, month, 15)
                    outcome.final_outcome = "settled" if month <= 6 else "lost"
                    outcome.settlement_amount = 5000.0 if month <= 6 else 0
                    outcome.time_to_resolution_days = 60
                    outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.detect_seasonal_trends()

            assert result["sample_size"] == 24
            assert "monthly_stats" in result
            assert "quarterly_summary" in result

    def test_seasonal_identifies_best_month(self, service):
        """Test seasonal trends identifies best month"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for month in range(1, 13):
                for _ in range(3):
                    outcome = Mock()
                    outcome.created_at = datetime(2024, month, 15)
                    # January has 100% success rate
                    outcome.final_outcome = "settled" if month == 1 else "lost"
                    outcome.settlement_amount = 5000.0 if month == 1 else 0
                    outcome.time_to_resolution_days = 60
                    outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.detect_seasonal_trends()

            trend_types = [t["type"] for t in result["trends"]]
            assert "best_month" in trend_types

    def test_seasonal_identifies_worst_month(self, service):
        """Test seasonal trends identifies worst month"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for month in range(1, 13):
                for _ in range(5):
                    outcome = Mock()
                    outcome.created_at = datetime(2024, month, 15)
                    # December has 0% success rate
                    outcome.final_outcome = "lost" if month == 12 else "settled"
                    outcome.settlement_amount = 0 if month == 12 else 5000.0
                    outcome.time_to_resolution_days = 60
                    outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.detect_seasonal_trends()

            trend_types = [t["type"] for t in result["trends"]]
            assert "worst_month" in trend_types

    def test_seasonal_calculates_quarterly_summary(self, service):
        """Test seasonal trends calculates quarterly summary"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for month in range(1, 13):
                for _ in range(2):
                    outcome = Mock()
                    outcome.created_at = datetime(2024, month, 15)
                    outcome.final_outcome = "settled"
                    outcome.settlement_amount = 5000.0
                    outcome.time_to_resolution_days = 60
                    outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.detect_seasonal_trends()

            assert "Q1" in result["quarterly_summary"]
            assert "Q2" in result["quarterly_summary"]
            assert "Q3" in result["quarterly_summary"]
            assert "Q4" in result["quarterly_summary"]

    def test_seasonal_exception_handling(self, service):
        """Test seasonal trends handles exceptions"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_db.query.side_effect = Exception("Database error")
            mock_db.close = Mock()
            mock_session.return_value = mock_db

            result = service.detect_seasonal_trends()

            assert "error" in result

    def test_seasonal_sets_cache(self, service):
        """Test seasonal trends sets cache after calculation"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for month in range(1, 13):
                for _ in range(2):
                    outcome = Mock()
                    outcome.created_at = datetime(2024, month, 15)
                    outcome.final_outcome = "settled"
                    outcome.settlement_amount = 5000.0
                    outcome.time_to_resolution_days = 60
                    outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            service.detect_seasonal_trends()

            # Check that cache was set
            assert "seasonal_trends" in service._cache


# ============================================================================
# identify_winning_strategies Tests
# ============================================================================


class TestIdentifyWinningStrategies:
    """Tests for identify_winning_strategies method"""

    def test_strategies_insufficient_data(self, service):
        """Test strategies with insufficient data"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Only 3 outcomes (less than 5)
            outcomes = [Mock() for _ in range(3)]

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.identify_winning_strategies()

            assert "Need more case data" in result["message"]
            assert result["sample_size"] == 3
            assert result["strategies"] == []

    def test_strategies_violation_effectiveness(self, service):
        """Test strategies identify violation type effectiveness"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            # Add 5 successful FCRA_1681e cases
            for i in range(5):
                outcome = Mock()
                outcome.final_outcome = "settled"
                outcome.violation_types = ["FCRA_1681e"]
                outcome.settlement_amount = 5000.0
                outcome.attorney_id = None
                outcome.documentation_quality = 0.8
                outcome.dispute_rounds_completed = 2
                outcomes.append(outcome)

            # Add 3 unsuccessful FCRA_1681i cases
            for i in range(3):
                outcome = Mock()
                outcome.final_outcome = "lost"
                outcome.violation_types = ["FCRA_1681i"]
                outcome.settlement_amount = 0
                outcome.attorney_id = None
                outcome.documentation_quality = 0.5
                outcome.dispute_rounds_completed = 1
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.identify_winning_strategies()

            assert result["sample_size"] == 8
            assert result["successful_cases"] == 5
            strategy_types = [s["type"] for s in result["strategies"]]
            assert "violation_effectiveness" in strategy_types

    def test_strategies_documentation_impact(self, service):
        """Test strategies identify documentation quality impact"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            # Add successful cases with high documentation quality
            for i in range(5):
                outcome = Mock()
                outcome.final_outcome = "settled"
                outcome.violation_types = []
                outcome.settlement_amount = 10000.0
                outcome.attorney_id = None
                outcome.documentation_quality = 0.9
                outcome.dispute_rounds_completed = 2
                outcomes.append(outcome)

            # Add unsuccessful cases with low documentation quality
            for i in range(5):
                outcome = Mock()
                outcome.final_outcome = "lost"
                outcome.violation_types = []
                outcome.settlement_amount = 0
                outcome.attorney_id = None
                outcome.documentation_quality = 0.3
                outcome.dispute_rounds_completed = 1
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.identify_winning_strategies()

            strategy_types = [s["type"] for s in result["strategies"]]
            assert "documentation_impact" in strategy_types

    def test_strategies_attorney_involvement(self, service):
        """Test strategies identify attorney involvement impact"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            # Cases with attorney - high success
            for i in range(5):
                outcome = Mock()
                outcome.final_outcome = "settled"
                outcome.violation_types = []
                outcome.settlement_amount = 5000.0
                outcome.attorney_id = 1
                outcome.documentation_quality = 0.8
                outcome.dispute_rounds_completed = 2
                outcomes.append(outcome)

            # Cases without attorney - lower success
            for i in range(5):
                outcome = Mock()
                outcome.final_outcome = "lost" if i < 4 else "settled"
                outcome.violation_types = []
                outcome.settlement_amount = 0 if i < 4 else 2000.0
                outcome.attorney_id = None
                outcome.documentation_quality = 0.8
                outcome.dispute_rounds_completed = 2
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.identify_winning_strategies()

            strategy_types = [s["type"] for s in result["strategies"]]
            assert "attorney_involvement" in strategy_types

    def test_strategies_optimal_rounds(self, service):
        """Test strategies identify optimal dispute rounds"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            # Round 2 has best settlements
            for i in range(5):
                outcome = Mock()
                outcome.final_outcome = "settled"
                outcome.violation_types = []
                outcome.settlement_amount = 10000.0
                outcome.attorney_id = None
                outcome.documentation_quality = 0.8
                outcome.dispute_rounds_completed = 2
                outcomes.append(outcome)

            # Round 1 has lower settlements
            for i in range(5):
                outcome = Mock()
                outcome.final_outcome = "settled"
                outcome.violation_types = []
                outcome.settlement_amount = 3000.0
                outcome.attorney_id = None
                outcome.documentation_quality = 0.8
                outcome.dispute_rounds_completed = 1
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.identify_winning_strategies()

            strategy_types = [s["type"] for s in result["strategies"]]
            assert "optimal_rounds" in strategy_types

    def test_strategies_top_violation_types(self, service):
        """Test strategies returns top violation types"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for i in range(10):
                outcome = Mock()
                outcome.final_outcome = "settled"
                outcome.violation_types = ["FCRA_1681e", "FCRA_1681i"]
                outcome.settlement_amount = 5000.0
                outcome.attorney_id = None
                outcome.documentation_quality = 0.8
                outcome.dispute_rounds_completed = 2
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.identify_winning_strategies()

            assert "top_violation_types" in result
            assert len(result["top_violation_types"]) <= 5

    def test_strategies_exception_handling(self, service):
        """Test strategies handle exceptions"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_db.query.side_effect = Exception("Database error")
            mock_db.close = Mock()
            mock_session.return_value = mock_db

            result = service.identify_winning_strategies()

            assert "error" in result


# ============================================================================
# find_attorney_strengths Tests
# ============================================================================


class TestFindAttorneyStrengths:
    """Tests for find_attorney_strengths method"""

    def test_attorney_insufficient_data(self, service):
        """Test attorney strengths with insufficient data"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Only 3 outcomes (less than 5)
            outcomes = [Mock() for _ in range(3)]

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.find_attorney_strengths()

            assert "Need more attorney-linked cases" in result["message"]
            assert result["sample_size"] == 3
            assert result["attorneys"] == []

    def test_attorney_strengths_calculation(self, service, mock_staff):
        """Test attorney strengths calculation"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for i in range(10):
                outcome = Mock()
                outcome.attorney_id = 1
                outcome.final_outcome = "settled" if i < 8 else "lost"
                outcome.settlement_amount = 12000.0 if i < 8 else 0
                outcome.time_to_resolution_days = 45
                outcome.violation_types = ["FCRA_1681e"]
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_staff
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.find_attorney_strengths()

            assert result["sample_size"] == 10
            assert len(result["attorneys"]) == 1
            assert result["attorneys"][0]["attorney_id"] == 1
            assert result["attorneys"][0]["success_rate"] == 0.8

    def test_attorney_top_performer(self, service, mock_staff):
        """Test attorney strengths identifies top performer"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for i in range(10):
                outcome = Mock()
                outcome.attorney_id = 1
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 5000.0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = []
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_staff
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.find_attorney_strengths()

            assert result["top_performer"] is not None
            assert result["top_performer"]["success_rate"] == 1.0

    def test_attorney_specialization(self, service, mock_staff):
        """Test attorney strengths identifies specialization"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            # 5 successful FCRA_1681e cases
            for i in range(5):
                outcome = Mock()
                outcome.attorney_id = 1
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 5000.0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = ["FCRA_1681e"]
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_staff
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.find_attorney_strengths()

            assert result["attorneys"][0]["specialization"] == "FCRA_1681e"

    def test_attorney_strengths_list(self, service, mock_staff):
        """Test attorney strengths identifies specific strengths"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            # High success rate with high settlements and fast resolution
            for i in range(10):
                outcome = Mock()
                outcome.attorney_id = 1
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 15000.0  # High settlement
                outcome.time_to_resolution_days = 40  # Fast resolution
                outcome.violation_types = ["FCRA_1681e"]
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_staff
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.find_attorney_strengths()

            strengths = result["attorneys"][0]["strengths"]
            assert "High overall success rate" in strengths
            assert "Strong settlement negotiator" in strengths
            assert "Fast case resolution" in strengths

    def test_attorney_insights_generation(self, service, mock_staff):
        """Test attorney insights generation"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for i in range(10):
                outcome = Mock()
                outcome.attorney_id = 1
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 8000.0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = ["FCRA_1681e"]
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_staff
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.find_attorney_strengths()

            assert "insights" in result
            assert len(result["insights"]) > 0

    def test_attorney_exception_handling(self, service):
        """Test attorney strengths handles exceptions"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_db.query.side_effect = Exception("Database error")
            mock_db.close = Mock()
            mock_session.return_value = mock_db

            result = service.find_attorney_strengths()

            assert "error" in result


# ============================================================================
# _identify_attorney_strengths Tests
# ============================================================================


class TestIdentifyAttorneyStrengthsHelper:
    """Tests for _identify_attorney_strengths helper method"""

    def test_high_success_rate_strength(self, service):
        """Test high success rate is identified as strength"""
        data = {
            "resolution_times": [60, 70, 80],
            "violation_types": {}
        }
        strengths = service._identify_attorney_strengths(data, 0.85, 5000.0)
        assert "High overall success rate" in strengths

    def test_good_success_rate_strength(self, service):
        """Test good success rate is identified as strength"""
        data = {
            "resolution_times": [60, 70, 80],
            "violation_types": {}
        }
        strengths = service._identify_attorney_strengths(data, 0.65, 5000.0)
        assert "Good success rate" in strengths

    def test_strong_negotiator_strength(self, service):
        """Test strong negotiator is identified as strength"""
        data = {
            "resolution_times": [60, 70, 80],
            "violation_types": {}
        }
        strengths = service._identify_attorney_strengths(data, 0.5, 15000.0)
        assert "Strong settlement negotiator" in strengths

    def test_fast_resolution_strength(self, service):
        """Test fast case resolution is identified as strength"""
        data = {
            "resolution_times": [30, 40, 50],
            "violation_types": {}
        }
        strengths = service._identify_attorney_strengths(data, 0.5, 5000.0)
        assert "Fast case resolution" in strengths

    def test_violation_expert_strength(self, service):
        """Test violation expert is identified as strength"""
        data = {
            "resolution_times": [60, 70, 80],
            "violation_types": {
                "FCRA_1681e": {"total": 5, "success": 5}  # 100% success
            }
        }
        strengths = service._identify_attorney_strengths(data, 0.5, 5000.0)
        assert "Expert in FCRA_1681e cases" in strengths

    def test_max_three_strengths(self, service):
        """Test that max 3 strengths are returned"""
        data = {
            "resolution_times": [30, 40, 50],
            "violation_types": {
                "FCRA_1681e": {"total": 5, "success": 5},
                "FCRA_1681i": {"total": 5, "success": 5}
            }
        }
        strengths = service._identify_attorney_strengths(data, 0.9, 15000.0)
        assert len(strengths) <= 3


# ============================================================================
# _generate_attorney_insights Tests
# ============================================================================


class TestGenerateAttorneyInsights:
    """Tests for _generate_attorney_insights helper method"""

    def test_empty_attorneys_list(self, service):
        """Test insights with empty attorneys list"""
        insights = service._generate_attorney_insights([])
        assert insights == []

    def test_top_performer_insight(self, service):
        """Test top performer insight is generated"""
        attorneys = [
            {"name": "Top Attorney", "success_rate": 0.9, "avg_settlement": 5000.0},
            {"name": "Other Attorney", "success_rate": 0.7, "avg_settlement": 3000.0}
        ]
        insights = service._generate_attorney_insights(attorneys)
        assert any("Top Attorney" in i and "highest success rate" in i for i in insights)

    def test_best_settler_insight(self, service):
        """Test best settler insight is generated"""
        attorneys = [
            {"name": "High Settler", "success_rate": 0.7, "avg_settlement": 10000.0},
            {"name": "Low Settler", "success_rate": 0.8, "avg_settlement": 2000.0}
        ]
        insights = service._generate_attorney_insights(attorneys)
        assert any("High Settler" in i and "highest average settlements" in i for i in insights)

    def test_specialist_insight(self, service):
        """Test specialist insight is generated"""
        attorneys = [
            {
                "name": "Specialist",
                "success_rate": 0.7,
                "avg_settlement": 5000.0,
                "specialization": "FCRA_1681e",
                "specialization_success_rate": 0.95
            }
        ]
        insights = service._generate_attorney_insights(attorneys)
        assert any("Specialist" in i and "specializes in FCRA_1681e" in i for i in insights)


# ============================================================================
# get_pattern_insights Tests
# ============================================================================


class TestGetPatternInsights:
    """Tests for get_pattern_insights method"""

    def test_pattern_insights_basic(self, service, mock_pattern):
        """Test basic pattern insights retrieval"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_query = Mock()
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = [mock_pattern]
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            # Mock the other methods called internally
            with patch.object(service, 'detect_seasonal_trends', return_value={"trends": [], "recommendations": []}):
                with patch.object(service, 'identify_winning_strategies', return_value={"strategies": []}):
                    result = service.get_pattern_insights()

            assert "insights" in result
            assert "furnisher_patterns" in result["insights"]
            assert "generated_at" in result

    def test_pattern_insights_with_filters(self, service, mock_pattern):
        """Test pattern insights with filters"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_query = Mock()
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = [mock_pattern]
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            with patch.object(service, 'detect_seasonal_trends', return_value={"trends": [], "recommendations": []}):
                with patch.object(service, 'identify_winning_strategies', return_value={"strategies": []}):
                    result = service.get_pattern_insights(filters={"furnisher_id": 1})

            assert result["filters_applied"] == {"furnisher_id": 1}

    def test_pattern_insights_high_confidence(self, service):
        """Test pattern insights identifies high confidence patterns"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            high_conf_pattern = Mock()
            high_conf_pattern.id = 1
            high_conf_pattern.furnisher_id = 1
            high_conf_pattern.furnisher_name = "Test"
            high_conf_pattern.pattern_type = "response_behavior"
            high_conf_pattern.pattern_data = {"settlement_rate": 0.8}
            high_conf_pattern.sample_size = 20
            high_conf_pattern.confidence = 0.85
            high_conf_pattern.last_updated = datetime.utcnow()

            mock_query = Mock()
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = [high_conf_pattern]
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            with patch.object(service, 'detect_seasonal_trends', return_value={"trends": [], "recommendations": []}):
                with patch.object(service, 'identify_winning_strategies', return_value={"strategies": []}):
                    result = service.get_pattern_insights()

            assert len(result["insights"]["high_confidence"]) == 1

    def test_pattern_insights_recommendations(self, service):
        """Test pattern insights generates recommendations"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            high_settlement_pattern = Mock()
            high_settlement_pattern.id = 1
            high_settlement_pattern.furnisher_id = 1
            high_settlement_pattern.furnisher_name = "High Settler"
            high_settlement_pattern.pattern_type = "response_behavior"
            high_settlement_pattern.pattern_data = {"settlement_rate": 0.8}
            high_settlement_pattern.sample_size = 20
            high_settlement_pattern.confidence = 0.7
            high_settlement_pattern.last_updated = datetime.utcnow()

            mock_query = Mock()
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = [high_settlement_pattern]
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            with patch.object(service, 'detect_seasonal_trends', return_value={"trends": [], "recommendations": []}):
                with patch.object(service, 'identify_winning_strategies', return_value={"strategies": []}):
                    result = service.get_pattern_insights()

            recs = result["insights"]["actionable_recommendations"]
            assert any("aggressive" in str(r).lower() for r in recs)

    def test_pattern_insights_exception_handling(self, service):
        """Test pattern insights handles exceptions"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_db.query.side_effect = Exception("Database error")
            mock_db.close = Mock()
            mock_session.return_value = mock_db

            result = service.get_pattern_insights()

            assert "error" in result


# ============================================================================
# refresh_all_patterns Tests
# ============================================================================


class TestRefreshAllPatterns:
    """Tests for refresh_all_patterns method"""

    def test_refresh_patterns_success(self, service, mock_furnisher):
        """Test successful pattern refresh"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_query = Mock()
            mock_query.all.return_value = [mock_furnisher]
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            with patch.object(service, 'analyze_furnisher_behavior', return_value={"sample_size": 10}):
                with patch.object(service, 'detect_seasonal_trends', return_value={}):
                    with patch.object(service, 'identify_winning_strategies', return_value={}):
                        result = service.refresh_all_patterns()

            assert result["success"] is True
            assert result["furnishers_updated"] == 1
            assert result["errors"] == []
            assert "timestamp" in result

    def test_refresh_patterns_with_errors(self, service, mock_furnisher):
        """Test pattern refresh with errors"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_query = Mock()
            mock_query.all.return_value = [mock_furnisher]
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            with patch.object(service, 'analyze_furnisher_behavior', side_effect=Exception("Analysis failed")):
                with patch.object(service, 'detect_seasonal_trends', return_value={}):
                    with patch.object(service, 'identify_winning_strategies', return_value={}):
                        result = service.refresh_all_patterns()

            assert result["success"] is True
            assert result["furnishers_updated"] == 0
            assert len(result["errors"]) == 1

    def test_refresh_patterns_exception_handling(self, service):
        """Test pattern refresh handles exceptions"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_db.query.side_effect = Exception("Database error")
            mock_db.close = Mock()
            mock_session.return_value = mock_db

            result = service.refresh_all_patterns()

            assert "error" in result


# ============================================================================
# _save_pattern Tests
# ============================================================================


class TestSavePattern:
    """Tests for _save_pattern method"""

    def test_save_pattern_create_new(self, service, mock_db):
        """Test creating a new pattern"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No existing pattern
        mock_db.query.return_value = mock_query
        mock_db.add = Mock()
        mock_db.commit = Mock()

        service._save_pattern(
            mock_db,
            furnisher_id=1,
            furnisher_name="Test Furnisher",
            pattern_type="response_behavior",
            pattern_data={"settlement_rate": 0.75},
            sample_size=20,
            confidence=0.85
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_save_pattern_update_existing(self, service, mock_db, mock_pattern):
        """Test updating an existing pattern"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_pattern
        mock_db.query.return_value = mock_query
        mock_db.commit = Mock()

        service._save_pattern(
            mock_db,
            furnisher_id=1,
            furnisher_name="Test Furnisher",
            pattern_type="response_behavior",
            pattern_data={"settlement_rate": 0.80},
            sample_size=25,
            confidence=0.90
        )

        assert mock_pattern.pattern_data == {"settlement_rate": 0.80}
        assert mock_pattern.sample_size == 25
        assert mock_pattern.confidence == 0.90
        mock_db.commit.assert_called_once()

    def test_save_pattern_exception_rollback(self, service, mock_db):
        """Test save pattern rolls back on exception"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = Exception("Query failed")
        mock_db.query.return_value = mock_query
        mock_db.rollback = Mock()

        service._save_pattern(
            mock_db,
            furnisher_id=1,
            furnisher_name="Test",
            pattern_type="test",
            pattern_data={},
            sample_size=1,
            confidence=0.5
        )

        mock_db.rollback.assert_called_once()


# ============================================================================
# Convenience Functions Tests
# ============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    def test_analyze_furnisher_behavior_function(self):
        """Test analyze_furnisher_behavior convenience function"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Mock furnisher query returning a furnisher
            mock_furnisher = Mock()
            mock_furnisher.id = 1
            mock_furnisher.name = "Test Furnisher"

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = []
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = analyze_furnisher_behavior(furnisher_name="Test")

            assert "furnisher_name" in result

    def test_detect_seasonal_trends_function(self):
        """Test detect_seasonal_trends convenience function"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_db.query.return_value.all.return_value = []
            mock_db.close = Mock()

            result = detect_seasonal_trends()

            assert "sample_size" in result or "message" in result

    def test_identify_winning_strategies_function(self):
        """Test identify_winning_strategies convenience function"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_db.query.return_value.all.return_value = []
            mock_db.close = Mock()

            result = identify_winning_strategies()

            assert "sample_size" in result or "message" in result

    def test_identify_winning_strategies_with_violation_type(self):
        """Test identify_winning_strategies with violation type filter"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_db.query.return_value.all.return_value = []
            mock_db.close = Mock()

            result = identify_winning_strategies(violation_type="FCRA_1681e")

            assert "sample_size" in result or "message" in result

    def test_find_attorney_strengths_function(self):
        """Test find_attorney_strengths convenience function"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_db.query.return_value.filter.return_value.all.return_value = []
            mock_db.close = Mock()

            result = find_attorney_strengths()

            assert "sample_size" in result or "message" in result

    def test_get_pattern_insights_function(self):
        """Test get_pattern_insights convenience function"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.close = Mock()

            with patch.object(PatternAnalyzerService, 'detect_seasonal_trends', return_value={"trends": [], "recommendations": []}):
                with patch.object(PatternAnalyzerService, 'identify_winning_strategies', return_value={"strategies": []}):
                    result = get_pattern_insights()

            assert "insights" in result or "error" in result

    def test_get_pattern_insights_with_filters(self):
        """Test get_pattern_insights with filters"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.close = Mock()

            with patch.object(PatternAnalyzerService, 'detect_seasonal_trends', return_value={"trends": [], "recommendations": []}):
                with patch.object(PatternAnalyzerService, 'identify_winning_strategies', return_value={"strategies": []}):
                    result = get_pattern_insights(filters={"furnisher_id": 1})

            assert "insights" in result or "error" in result


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_empty_violation_types_list(self, service, mock_furnisher):
        """Test handling of empty violation_types list"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcome = Mock()
            outcome.furnisher_id = 1
            outcome.final_outcome = "settled"
            outcome.settlement_amount = 5000.0
            outcome.time_to_resolution_days = 60
            outcome.violation_types = []  # Empty list

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = [outcome]
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            assert result["sample_size"] == 1
            # Should not have most_effective_violation pattern
            pattern_types = [p["type"] for p in result["patterns"]]
            assert "most_effective_violation" not in pattern_types

    def test_none_violation_types(self, service, mock_furnisher):
        """Test handling of None violation_types"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcome = Mock()
            outcome.furnisher_id = 1
            outcome.final_outcome = "settled"
            outcome.settlement_amount = 5000.0
            outcome.time_to_resolution_days = 60
            outcome.violation_types = None  # None value

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = [outcome]
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            assert result["sample_size"] == 1

    def test_zero_settlement_amount(self, service, mock_furnisher):
        """Test handling of zero settlement amounts"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for i in range(5):
                outcome = Mock()
                outcome.furnisher_id = 1
                outcome.final_outcome = "lost"
                outcome.settlement_amount = 0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = []
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            assert result["statistics"]["avg_settlement"] == 0

    def test_zero_resolution_time(self, service, mock_furnisher):
        """Test handling of zero resolution time"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcome = Mock()
            outcome.furnisher_id = 1
            outcome.final_outcome = "settled"
            outcome.settlement_amount = 5000.0
            outcome.time_to_resolution_days = 0
            outcome.violation_types = []

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_furnisher
            mock_query.all.return_value = [outcome]
            mock_db.query.return_value = mock_query
            mock_db.commit = Mock()
            mock_db.rollback = Mock()
            mock_db.close = Mock()

            result = service.analyze_furnisher_behavior(furnisher_id=1)

            assert result["statistics"]["avg_resolution_days"] == 0

    def test_null_created_at_in_seasonal(self, service):
        """Test seasonal trends handles null created_at"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for i in range(15):
                outcome = Mock()
                outcome.created_at = None  # Null created_at
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 5000.0
                outcome.time_to_resolution_days = 60
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.detect_seasonal_trends()

            # Should not crash, monthly_stats should be empty
            assert result["sample_size"] == 15

    def test_null_documentation_quality(self, service):
        """Test strategies handle null documentation_quality"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            outcomes = []
            for i in range(10):
                outcome = Mock()
                outcome.final_outcome = "settled" if i < 5 else "lost"
                outcome.violation_types = []
                outcome.settlement_amount = 5000.0 if i < 5 else 0
                outcome.attorney_id = None
                outcome.documentation_quality = None  # Null value
                outcome.dispute_rounds_completed = None
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.identify_winning_strategies()

            # Should not crash
            assert result["sample_size"] == 10

    def test_staff_not_found_for_attorney(self, service):
        """Test attorney strengths handles missing staff record"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Create 10 outcomes with attorney_id=999 (need >= 5 for analysis)
            outcomes = []
            for i in range(10):
                outcome = Mock()
                outcome.attorney_id = 999  # Non-existent attorney
                outcome.final_outcome = "settled"
                outcome.settlement_amount = 5000.0
                outcome.time_to_resolution_days = 60
                outcome.violation_types = []
                outcomes.append(outcome)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None  # Staff not found
            mock_query.all.return_value = outcomes
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            result = service.find_attorney_strengths()

            assert result["attorneys"][0]["name"] == "Attorney #999"

    def test_pattern_filter_by_pattern_type(self, service, mock_pattern):
        """Test pattern insights filter by pattern_type"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            mock_query = Mock()
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = [mock_pattern]
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            with patch.object(service, 'detect_seasonal_trends', return_value={"trends": [], "recommendations": []}):
                with patch.object(service, 'identify_winning_strategies', return_value={"strategies": []}):
                    result = service.get_pattern_insights(filters={"pattern_type": "response_behavior"})

            # Pattern should be included because it matches the filter
            assert len(result["insights"]["furnisher_patterns"]) == 1

    def test_low_settlement_recommendation(self, service):
        """Test low settlement generates litigation prep recommendation"""
        with patch('services.pattern_analyzer_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            low_settlement_pattern = Mock()
            low_settlement_pattern.id = 1
            low_settlement_pattern.furnisher_id = 1
            low_settlement_pattern.furnisher_name = "Difficult Furnisher"
            low_settlement_pattern.pattern_type = "response_behavior"
            low_settlement_pattern.pattern_data = {"settlement_rate": 0.2}  # Low rate
            low_settlement_pattern.sample_size = 20
            low_settlement_pattern.confidence = 0.7
            low_settlement_pattern.last_updated = datetime.utcnow()

            mock_query = Mock()
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = [low_settlement_pattern]
            mock_db.query.return_value = mock_query
            mock_db.close = Mock()

            with patch.object(service, 'detect_seasonal_trends', return_value={"trends": [], "recommendations": []}):
                with patch.object(service, 'identify_winning_strategies', return_value={"strategies": []}):
                    result = service.get_pattern_insights()

            recs = result["insights"]["actionable_recommendations"]
            assert any("litigation" in str(r).lower() for r in recs)
