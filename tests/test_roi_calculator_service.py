"""
Unit tests for ROICalculatorService

Tests ROI and potential recovery value calculation including:
- Violation counting
- Statutory damages calculation
- Settlement estimates
- Litigation potential scoring
- Score improvement estimates
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from services.roi_calculator_service import (
    ROICalculatorService,
    FCRA_WILLFUL_MIN,
    FCRA_WILLFUL_MAX,
    HISTORICAL_DELETION_RATES,
    SCORE_IMPROVEMENT_PER_COLLECTION,
    CREDIT_VALUE_PER_SCORE_POINT,
)


class TestConstants:
    """Tests for ROI calculator constants."""

    def test_fcra_willful_min(self):
        """Test FCRA willful minimum is $100."""
        assert FCRA_WILLFUL_MIN == 100

    def test_fcra_willful_max(self):
        """Test FCRA willful maximum is $1,000."""
        assert FCRA_WILLFUL_MAX == 1000

    def test_deletion_rates_defined(self):
        """Test historical deletion rates are defined."""
        assert 'collection' in HISTORICAL_DELETION_RATES
        assert 'charge_off' in HISTORICAL_DELETION_RATES
        assert 'late_payment' in HISTORICAL_DELETION_RATES

    def test_score_improvement_values(self):
        """Test score improvement constants."""
        assert SCORE_IMPROVEMENT_PER_COLLECTION == 10
        assert CREDIT_VALUE_PER_SCORE_POINT == 250


class TestServiceInit:
    """Tests for ROICalculatorService initialization."""

    def test_init_with_db(self):
        """Test initialization with provided database."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)
        assert service.db == mock_db
        assert service._owns_session == False

    def test_init_without_db(self):
        """Test initialization without database."""
        with patch('services.roi_calculator_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            service = ROICalculatorService()
            assert service._owns_session == True


class TestCalculateROI:
    """Tests for calculate_roi method."""

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ROICalculatorService(db=mock_db)
        result = service.calculate_roi(client_id=999)

        assert result['success'] == False
        assert 'not found' in result['error']

    def test_success_returns_all_fields(self):
        """Test successful calculation returns all expected fields."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = ROICalculatorService(db=mock_db)
        result = service.calculate_roi(client_id=1, save=False)

        assert result['success'] == True
        assert 'violations' in result
        assert 'statutory_damages' in result
        assert 'actual_damages' in result
        assert 'estimates' in result
        assert 'litigation' in result
        assert 'score_improvement' in result


class TestCountViolationsByType:
    """Tests for _count_violations_by_type method."""

    def test_empty_violations(self):
        """Test counting with no violations."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        result = service._count_violations_by_type([])

        assert result['total'] == 0
        assert result['fcra'] == 0
        assert result['willful'] == 0

    def test_counts_fcra_violations(self):
        """Test counting FCRA violations."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        v1 = MagicMock()
        v1.violation_type = 'FCRA Violation'
        v1.fcra_section = '1681'
        v1.is_willful = True

        result = service._count_violations_by_type([v1])

        assert result['total'] == 1
        assert result['fcra'] == 1
        assert result['willful'] == 1

    def test_counts_multiple_types(self):
        """Test counting multiple violation types."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        v1 = MagicMock(violation_type='FCRA', fcra_section='1681a', is_willful=True)
        v2 = MagicMock(violation_type='FDCPA', fcra_section='', is_willful=False)
        v3 = MagicMock(violation_type='TCPA', fcra_section='', is_willful=False)

        result = service._count_violations_by_type([v1, v2, v3])

        assert result['total'] == 3
        assert result['fcra'] == 1
        assert result['fdcpa'] == 1
        assert result['tcpa'] == 1
        assert result['willful'] == 1
        assert result['negligent'] == 2


class TestCalculateStatutoryDamages:
    """Tests for _calculate_statutory_damages method."""

    def test_no_violations(self):
        """Test with no violations."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        result = service._calculate_statutory_damages([])

        assert result['min'] == 0
        assert result['max'] == 0
        assert result['punitive'] == 0

    def test_willful_violation_defaults(self):
        """Test willful violation uses default min/max."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        v = MagicMock()
        v.is_willful = True
        v.statutory_damages_min = None
        v.statutory_damages_max = None

        result = service._calculate_statutory_damages([v])

        assert result['min'] == FCRA_WILLFUL_MIN
        assert result['max'] == FCRA_WILLFUL_MAX

    def test_willful_violation_stored_values(self):
        """Test willful violation uses stored min/max."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        v = MagicMock()
        v.is_willful = True
        v.statutory_damages_min = 500
        v.statutory_damages_max = 2000

        result = service._calculate_statutory_damages([v])

        assert result['min'] == 500
        assert result['max'] == 2000

    def test_punitive_potential_calculated(self):
        """Test punitive damages potential is calculated."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        v = MagicMock()
        v.is_willful = True
        v.statutory_damages_min = None
        v.statutory_damages_max = None

        result = service._calculate_statutory_damages([v])

        assert result['punitive'] > 0


class TestCalculateActualDamages:
    """Tests for _calculate_actual_damages method."""

    def test_no_inputs(self):
        """Test with no inputs."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        result = service._calculate_actual_damages(None, {})

        assert result['total'] == 0
        assert result['credit_denial'] == 0

    def test_from_analysis_damages(self):
        """Test populates from analysis damages."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        mock_damages = MagicMock()
        mock_damages.credit_denials_amount = 1000
        mock_damages.higher_interest_amount = 500
        mock_damages.time_stress_amount = 200
        mock_damages.other_actual_amount = 100

        result = service._calculate_actual_damages(mock_damages, {})

        assert result['credit_denial'] == 1000
        assert result['higher_interest'] == 500
        assert result['total'] == 1800

    def test_user_inputs_override(self):
        """Test user inputs override analysis damages."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        mock_damages = MagicMock()
        mock_damages.credit_denials_amount = 1000
        mock_damages.higher_interest_amount = 500
        mock_damages.time_stress_amount = 200
        mock_damages.other_actual_amount = 100

        user_inputs = {'credit_denial': 5000}

        result = service._calculate_actual_damages(mock_damages, user_inputs)

        assert result['credit_denial'] == 5000


class TestEstimateAttorneyFees:
    """Tests for _estimate_attorney_fees method."""

    def test_basic_calculation(self):
        """Test basic attorney fee calculation."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        result = service._estimate_attorney_fees(
            violation_count=5,
            statutory_max=5000,
            actual_total=2000
        )

        assert result > 0

    def test_higher_violations_higher_fees(self):
        """Test more violations result in higher estimated fees."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        low = service._estimate_attorney_fees(1, 1000, 500)
        high = service._estimate_attorney_fees(10, 10000, 5000)

        assert high > low


class TestAnalyzeDisputeItems:
    """Tests for _analyze_dispute_items method."""

    def test_empty_items(self):
        """Test with no items."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        result = service._analyze_dispute_items([])

        assert result['total'] == 0
        assert result['disputable'] == 0
        assert result['deletion_rate'] == 0

    def test_counts_by_type(self):
        """Test counts items by type."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        items = [
            MagicMock(account_type='Collection', status='pending', balance=500),
            MagicMock(account_type='Charge-off', status='pending', balance=1000),
            MagicMock(account_type='Late Payment', status='disputed', balance=0),
        ]

        result = service._analyze_dispute_items(items)

        assert result['total'] == 3
        assert result['by_type']['collections'] == 1
        assert result['by_type']['charge_offs'] == 1
        assert result['by_type']['late_payments'] == 1

    def test_identifies_high_value(self):
        """Test identifies high-value items."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        items = [
            MagicMock(account_type='Collection', status='pending', balance=5000),
        ]

        result = service._analyze_dispute_items(items)

        assert result['high_value'] == 1


class TestCalculateSettlementEstimates:
    """Tests for _calculate_settlement_estimates method."""

    def test_basic_estimates(self):
        """Test basic settlement estimates."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        statutory = {'min': 500, 'max': 5000, 'punitive': 10000}
        actual = {'total': 2000}
        violations = {'total': 5, 'willful': 2}
        items = {'high_value': 3}

        result = service._calculate_settlement_estimates(
            statutory, actual, 3000, violations, items
        )

        assert 'conservative' in result
        assert 'moderate' in result
        assert 'aggressive' in result
        assert 'most_likely' in result
        assert result['conservative'] < result['moderate'] < result['aggressive']


class TestCalculateLitigationPotential:
    """Tests for _calculate_litigation_potential method."""

    def test_low_score(self):
        """Test low litigation potential."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        violations = []
        counts = {'total': 1, 'willful': 0}
        statutory = {'min': 0, 'max': 500}
        actual = {'total': 0}
        items = {'high_value': 0, 'deletion_rate': 0.7}

        result = service._calculate_litigation_potential(
            violations, counts, statutory, actual, items
        )

        assert result['score'] < 30
        assert result['recommended'] == False

    def test_high_score(self):
        """Test high litigation potential."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        violations = [MagicMock() for _ in range(10)]
        counts = {'total': 10, 'willful': 5}
        statutory = {'min': 5000, 'max': 15000}
        actual = {'total': 10000}
        items = {'high_value': 6, 'deletion_rate': 0.2}

        result = service._calculate_litigation_potential(
            violations, counts, statutory, actual, items
        )

        assert result['score'] >= 60
        assert result['recommended'] == True


class TestEstimateScoreImprovement:
    """Tests for _estimate_score_improvement method."""

    def test_no_items(self):
        """Test with no items."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        items = {
            'by_type': {
                'collections': 0,
                'charge_offs': 0,
                'late_payments': 0,
                'inquiries': 0,
                'public_records': 0,
            }
        }

        result = service._estimate_score_improvement(items)

        assert result == 0

    def test_with_items(self):
        """Test score improvement calculation with items."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        items = {
            'by_type': {
                'collections': 5,
                'charge_offs': 2,
                'late_payments': 3,
                'inquiries': 2,
                'public_records': 0,
            }
        }

        result = service._estimate_score_improvement(items)

        assert result > 0
        assert result <= 150  # Capped at 150


class TestQuickEstimate:
    """Tests for quick_estimate method."""

    def test_basic_estimate(self):
        """Test basic quick estimate."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        result = service.quick_estimate(
            violations_count=5,
            willful_count=2,
            collections_count=3,
            chargeoffs_count=1,
            actual_damages=1000
        )

        assert result['success'] == True
        assert result['quick_estimate'] == True
        assert 'estimates' in result
        assert 'score_improvement' in result

    def test_empty_estimate(self):
        """Test estimate with no inputs."""
        mock_db = MagicMock(spec=Session)
        service = ROICalculatorService(db=mock_db)

        result = service.quick_estimate()

        assert result['success'] == True
        assert result['violations_count'] == 0


class TestGetClientCalculations:
    """Tests for get_client_calculations method."""

    def test_returns_calculations(self):
        """Test returning calculation history."""
        mock_db = MagicMock(spec=Session)
        mock_calcs = [
            MagicMock(to_dict=MagicMock(return_value={'id': 1})),
            MagicMock(to_dict=MagicMock(return_value={'id': 2})),
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_calcs

        service = ROICalculatorService(db=mock_db)
        result = service.get_client_calculations(client_id=1)

        assert len(result) == 2


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary method."""

    def test_returns_summary(self):
        """Test dashboard summary structure."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.scalar.return_value = 0
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.query.return_value.first.return_value = (0, 0, 0, 0, 0, 0)
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = ROICalculatorService(db=mock_db)
        result = service.get_dashboard_summary()

        assert 'total_calculations' in result
        assert 'recent_calculations' in result
        assert 'averages' in result
        assert 'recent' in result


class TestGetAggregateStats:
    """Tests for get_aggregate_stats method."""

    def test_no_calculations(self):
        """Test with no calculations."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.all.return_value = []

        service = ROICalculatorService(db=mock_db)
        result = service.get_aggregate_stats()

        assert result['count'] == 0
        assert result['total_violations'] == 0

    def test_with_period_filter(self):
        """Test filtering by period."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ROICalculatorService(db=mock_db)

        for period in ['week', 'month', 'quarter', 'year']:
            result = service.get_aggregate_stats(period=period)
            assert 'count' in result


class TestExportCalculations:
    """Tests for export_calculations method."""

    def test_empty_export(self):
        """Test export with no calculations."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = ROICalculatorService(db=mock_db)
        result = service.export_calculations()

        assert result == []
