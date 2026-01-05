"""
Unit tests for FreeAnalysisService

Tests the free teaser analysis flow including:
- Lead creation from uploaded reports
- Teaser analysis generation
- Full analysis access (paid customers)
- Stage transitions
"""

import pytest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from services.free_analysis_service import (
    FreeAnalysisService,
    get_free_analysis_service,
    ANALYSIS_PRICE,
    ROUND_1_PRICE,
    ROUND_2_PLUS_PRICE,
    SETTLEMENT_FEE_PERCENT,
    VIOLATION_VALUES,
)


class TestConstants:
    """Tests for pricing constants."""

    def test_analysis_price(self):
        """Test analysis price is $199."""
        assert ANALYSIS_PRICE == 19900

    def test_round_1_price(self):
        """Test Round 1 price is $497."""
        assert ROUND_1_PRICE == 49700

    def test_round_2_plus_price(self):
        """Test Round 2+ price is $297."""
        assert ROUND_2_PLUS_PRICE == 29700

    def test_settlement_fee(self):
        """Test settlement fee is 30%."""
        assert SETTLEMENT_FEE_PERCENT == 30

    def test_violation_values_defined(self):
        """Test violation values are defined."""
        assert 'fcra_violation' in VIOLATION_VALUES
        assert 'fdcpa_violation' in VIOLATION_VALUES
        assert 'late_reporting' in VIOLATION_VALUES


class TestServiceInit:
    """Tests for FreeAnalysisService initialization."""

    def test_init_with_db(self):
        """Test initialization with database session."""
        mock_db = MagicMock(spec=Session)
        service = FreeAnalysisService(mock_db)
        assert service.db == mock_db

    def test_factory_function(self):
        """Test factory function creates service."""
        with patch('services.free_analysis_service.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            service = get_free_analysis_service()

            assert isinstance(service, FreeAnalysisService)


class TestCreateLeadFromUpload:
    """Tests for create_lead_from_upload method."""

    def test_new_lead_created(self):
        """Test creating a new lead."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.free_analysis_token = 'test_token'

        with patch('services.free_analysis_service.Client') as MockClient:
            MockClient.return_value = mock_client

            service = FreeAnalysisService(mock_db)
            result = service.create_lead_from_upload(
                name='John Doe',
                email='john@example.com',
                phone='555-1234'
            )

        assert result['success'] == True
        assert result['is_existing'] == False
        assert 'token' in result

    def test_existing_client_with_token(self):
        """Test existing client returns existing token."""
        mock_db = MagicMock(spec=Session)
        mock_existing = MagicMock()
        mock_existing.id = 1
        mock_existing.free_analysis_token = 'existing_token'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

        service = FreeAnalysisService(mock_db)
        result = service.create_lead_from_upload(
            name='John Doe',
            email='john@example.com',
            phone='555-1234'
        )

        assert result['success'] == True
        assert result['is_existing'] == True
        assert result['token'] == 'existing_token'

    def test_existing_client_without_token(self):
        """Test existing client gets new token if none exists."""
        mock_db = MagicMock(spec=Session)
        mock_existing = MagicMock()
        mock_existing.id = 1
        mock_existing.free_analysis_token = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

        service = FreeAnalysisService(mock_db)
        result = service.create_lead_from_upload(
            name='John Doe',
            email='john@example.com',
            phone='555-1234'
        )

        assert result['success'] == True
        assert result['is_existing'] == True

    def test_parses_name_correctly(self):
        """Test name is split into first/last correctly."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = MagicMock()
        mock_client.id = 1

        with patch('services.free_analysis_service.Client') as MockClient:
            MockClient.return_value = mock_client

            service = FreeAnalysisService(mock_db)
            result = service.create_lead_from_upload(
                name='John Robert Doe',
                email='john@example.com',
                phone='555-1234'
            )

            # Check that Client was called with parsed name
            call_kwargs = MockClient.call_args[1]
            assert call_kwargs['first_name'] == 'John'
            assert call_kwargs['last_name'] == 'Robert Doe'

    def test_handles_single_name(self):
        """Test handling single word name."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = MagicMock()
        mock_client.id = 1

        with patch('services.free_analysis_service.Client') as MockClient:
            MockClient.return_value = mock_client

            service = FreeAnalysisService(mock_db)
            result = service.create_lead_from_upload(
                name='Madonna',
                email='madonna@example.com',
                phone='555-1234'
            )

            call_kwargs = MockClient.call_args[1]
            assert call_kwargs['first_name'] == 'Madonna'
            assert call_kwargs['last_name'] == ''

    def test_database_error(self):
        """Test handling database errors."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.side_effect = Exception("Database error")

        service = FreeAnalysisService(mock_db)
        result = service.create_lead_from_upload(
            name='John Doe',
            email='john@example.com',
            phone='555-1234'
        )

        assert result['success'] == False
        assert 'error' in result


class TestGetTeaserAnalysis:
    """Tests for get_teaser_analysis method."""

    def test_token_not_found(self):
        """Test error when token not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = FreeAnalysisService(mock_db)
        result = service.get_teaser_analysis(token='invalid_token')

        assert result['success'] == False
        assert 'not found' in result['error']

    def test_returns_teaser_without_analysis(self):
        """Test returns placeholder when no analysis exists."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.first_name = 'John'
        mock_client.name = 'John Doe'
        mock_client.client_stage = 'lead'

        # First query returns client, second returns no analysis
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = FreeAnalysisService(mock_db)
        result = service.get_teaser_analysis(token='valid_token')

        assert result['success'] == True
        assert 'teaser' in result
        assert result['teaser']['has_real_data'] == False

    def test_returns_real_teaser_with_analysis(self):
        """Test returns real data when analysis exists."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.first_name = 'John'
        mock_client.name = 'John Doe'
        mock_client.client_stage = 'lead'

        mock_analysis = MagicMock()
        mock_analysis.result = {
            'accounts': [
                {'payment_status': 'Late'},
                {'payment_status': 'Collection'}
            ],
            'violations': [
                {'type': 'fcra_violation'}
            ]
        }

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_analysis

        service = FreeAnalysisService(mock_db)
        result = service.get_teaser_analysis(token='valid_token')

        assert result['success'] == True
        assert result['teaser']['has_real_data'] == True


class TestGeneratePlaceholderTeaser:
    """Tests for _generate_placeholder_teaser method."""

    def test_returns_reasonable_estimates(self):
        """Test placeholder returns reasonable values."""
        mock_db = MagicMock(spec=Session)
        service = FreeAnalysisService(mock_db)

        teaser = service._generate_placeholder_teaser()

        assert teaser['negative_items'] > 0
        assert teaser['potential_violations'] > 0
        assert len(teaser['violation_types']) > 0
        assert teaser['min_value'] > 0
        assert teaser['max_value'] > teaser['min_value']
        assert teaser['has_real_data'] == False


class TestCalculateValueRange:
    """Tests for _calculate_value_range method."""

    def test_basic_calculation(self):
        """Test basic value range calculation."""
        mock_db = MagicMock(spec=Session)
        service = FreeAnalysisService(mock_db)

        min_val, max_val = service._calculate_value_range(
            negative_items=10,
            violations=3,
            violation_types=['fcra_violation', 'inaccurate_info']
        )

        assert min_val >= 3000  # Minimum threshold
        assert max_val > min_val

    def test_more_items_higher_value(self):
        """Test more items results in higher value."""
        mock_db = MagicMock(spec=Session)
        service = FreeAnalysisService(mock_db)

        min_small, max_small = service._calculate_value_range(5, 1, [])
        min_large, max_large = service._calculate_value_range(20, 5, ['fcra_violation'])

        assert min_large > min_small
        assert max_large > max_small


class TestMarkAnalysisPaid:
    """Tests for mark_analysis_paid method."""

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = FreeAnalysisService(mock_db)
        result = service.mark_analysis_paid(
            client_id=999,
            payment_intent_id='pi_123'
        )

        assert result['success'] == False
        assert 'not found' in result['error']

    def test_updates_client_stage(self):
        """Test client stage is updated to analysis_paid."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = FreeAnalysisService(mock_db)
        result = service.mark_analysis_paid(
            client_id=1,
            payment_intent_id='pi_123'
        )

        assert result['success'] == True
        assert result['client_stage'] == 'analysis_paid'
        assert mock_client.client_stage == 'analysis_paid'
        assert mock_client.analysis_payment_id == 'pi_123'
        assert mock_client.total_paid == ANALYSIS_PRICE

    def test_calculates_round_1_due(self):
        """Test Round 1 amount due is calculated with credit."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = FreeAnalysisService(mock_db)
        result = service.mark_analysis_paid(
            client_id=1,
            payment_intent_id='pi_123'
        )

        # Round 1 due = $497 - $199 = $298 = 29800 cents
        expected_round_1_due = ROUND_1_PRICE - ANALYSIS_PRICE
        assert mock_client.round_1_amount_due == expected_round_1_due
        assert result['round_1_due'] == expected_round_1_due


class TestGetFullAnalysis:
    """Tests for get_full_analysis method."""

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = FreeAnalysisService(mock_db)
        result = service.get_full_analysis(client_id=999)

        assert result['success'] == False
        assert 'not found' in result['error']

    def test_requires_payment_if_lead(self):
        """Test error if client hasn't paid."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.client_stage = 'lead'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = FreeAnalysisService(mock_db)
        result = service.get_full_analysis(client_id=1)

        assert result['success'] == False
        assert result['requires_payment'] == True
        assert result['amount'] == ANALYSIS_PRICE

    def test_returns_analysis_if_paid(self):
        """Test returns analysis for paid clients."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.client_stage = 'analysis_paid'

        mock_analysis = MagicMock()
        mock_analysis.result = {'test': 'data'}
        mock_analysis.created_at = datetime.utcnow()

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_analysis

        service = FreeAnalysisService(mock_db)
        result = service.get_full_analysis(client_id=1)

        assert result['success'] == True
        assert result['analysis'] == {'test': 'data'}

    def test_no_analysis_yet(self):
        """Test message when analysis not yet processed."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.client_stage = 'analysis_paid'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = FreeAnalysisService(mock_db)
        result = service.get_full_analysis(client_id=1)

        assert result['success'] == True
        assert result['analysis'] is None
        assert 'being processed' in result['message']


class TestProceedToOnboarding:
    """Tests for proceed_to_onboarding method."""

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = FreeAnalysisService(mock_db)
        result = service.proceed_to_onboarding(client_id=999)

        assert result['success'] == False
        assert 'not found' in result['error']

    def test_invalid_stage_transition(self):
        """Test error for invalid stage transition."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.client_stage = 'lead'  # Should be analysis_paid
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = FreeAnalysisService(mock_db)
        result = service.proceed_to_onboarding(client_id=1)

        assert result['success'] == False
        assert 'Invalid stage transition' in result['error']

    def test_moves_to_onboarding(self):
        """Test successful transition to onboarding."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.client_stage = 'analysis_paid'
        mock_client.portal_token = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = FreeAnalysisService(mock_db)
        result = service.proceed_to_onboarding(client_id=1)

        assert result['success'] == True
        assert result['client_stage'] == 'onboarding'
        assert mock_client.client_stage == 'onboarding'
        assert mock_client.dispute_status == 'onboarding'

    def test_generates_portal_token(self):
        """Test portal token is generated if not exists."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.client_stage = 'analysis_paid'
        mock_client.portal_token = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = FreeAnalysisService(mock_db)
        result = service.proceed_to_onboarding(client_id=1)

        assert mock_client.portal_token is not None
        assert 'portal_token' in result
