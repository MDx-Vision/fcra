"""
Unit tests for ClientPaymentService

Tests all payment operations for the client journey including:
- $199 Analysis Payment
- Round 1-4 Payments (with credit application)
- Prepay Package Purchases
- Settlement Fee Processing
- Payment Summaries
"""

import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session

from services.client_payment_service import (
    ClientPaymentService,
    get_client_payment_service,
    ANALYSIS_PRICE,
    ROUND_1_PRICE,
    ROUND_1_WITH_CREDIT,
    ROUND_2_PLUS_PRICE,
    SETTLEMENT_FEE_PERCENT,
    PREPAY_PACKAGES,
    FINANCING_UPCHARGE,
)


class TestConstants:
    """Tests for pricing constants."""

    def test_analysis_price(self):
        """Test analysis price is $199."""
        assert ANALYSIS_PRICE == 19900

    def test_round_1_price(self):
        """Test Round 1 price is $497."""
        assert ROUND_1_PRICE == 49700

    def test_round_1_with_credit(self):
        """Test Round 1 with credit is $298."""
        assert ROUND_1_WITH_CREDIT == 29800

    def test_round_2_plus_price(self):
        """Test Round 2+ price is $297."""
        assert ROUND_2_PLUS_PRICE == 29700

    def test_settlement_fee_percent(self):
        """Test settlement fee is 30%."""
        assert SETTLEMENT_FEE_PERCENT == 30

    def test_financing_upcharge(self):
        """Test financing upcharge is $200."""
        assert FINANCING_UPCHARGE == 20000


class TestPrepayPackages:
    """Tests for prepay package configuration."""

    def test_starter_package(self):
        """Test Starter package configuration."""
        pkg = PREPAY_PACKAGES['starter']
        assert pkg['name'] == 'Starter Package'
        assert pkg['rounds'] == 2
        assert pkg['prepay_price'] == 74900  # $749

    def test_standard_package(self):
        """Test Standard package configuration."""
        pkg = PREPAY_PACKAGES['standard']
        assert pkg['name'] == 'Standard Package'
        assert pkg['rounds'] == 4
        assert pkg['prepay_price'] == 129500  # $1,295

    def test_complete_package(self):
        """Test Complete package configuration."""
        pkg = PREPAY_PACKAGES['complete']
        assert pkg['name'] == 'Complete Package'
        assert pkg['rounds'] == 6
        assert pkg['prepay_price'] == 179500  # $1,795

    def test_unlimited_package(self):
        """Test Unlimited package configuration."""
        pkg = PREPAY_PACKAGES['unlimited']
        assert pkg['name'] == 'Unlimited Package'
        assert pkg['rounds'] == 99
        assert pkg['prepay_price'] == 200000  # $2,000


class TestServiceInit:
    """Tests for ClientPaymentService initialization."""

    def test_init_with_db_session(self):
        """Test initialization with database session."""
        mock_db = MagicMock(spec=Session)
        service = ClientPaymentService(mock_db)
        assert service.db == mock_db
        assert service._stripe is None

    def test_factory_function(self):
        """Test the factory function creates service instance."""
        with patch('services.client_payment_service.SessionLocal') as mock_session:
            mock_db = MagicMock(spec=Session)
            mock_session.return_value = mock_db
            service = get_client_payment_service()
            assert isinstance(service, ClientPaymentService)

    def test_factory_function_with_db(self):
        """Test factory function with provided database."""
        mock_db = MagicMock(spec=Session)
        service = get_client_payment_service(mock_db)
        assert service.db == mock_db

    def test_stripe_lazy_loading(self):
        """Test Stripe client is lazy-loaded."""
        mock_db = MagicMock(spec=Session)
        service = ClientPaymentService(mock_db)

        with patch('services.stripe_client.get_stripe_client') as mock_get_stripe:
            mock_stripe = MagicMock()
            mock_get_stripe.return_value = mock_stripe

            # Access stripe property
            stripe = service.stripe

            assert mock_get_stripe.called
            assert stripe == mock_stripe

    def test_stripe_init_failure(self):
        """Test Stripe initialization failure is handled."""
        mock_db = MagicMock(spec=Session)
        service = ClientPaymentService(mock_db)

        with patch('services.stripe_client.get_stripe_client') as mock_get_stripe:
            mock_get_stripe.side_effect = Exception("Stripe not configured")

            stripe = service.stripe

            assert stripe is None


class TestCreateAnalysisPaymentIntent:
    """Tests for create_analysis_payment_intent method."""

    def test_success(self):
        """Test successful analysis payment intent creation."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'lead'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_secret_123'
        mock_intent.id = 'pi_123'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.create_analysis_payment_intent(client_id=1)

        assert result['success'] == True
        assert result['client_secret'] == 'pi_secret_123'
        assert result['payment_intent_id'] == 'pi_123'
        assert result['amount'] == ANALYSIS_PRICE
        assert result['amount_display'] == '$199.00'

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientPaymentService(mock_db)
        result = service.create_analysis_payment_intent(client_id=999)

        assert result['success'] == False
        assert 'not found' in result['error']

    def test_invalid_stage(self):
        """Test error when client not in lead stage."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.client_stage = 'active'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.create_analysis_payment_intent(client_id=1)

        assert result['success'] == False
        assert 'Invalid stage' in result['error']

    def test_stripe_unavailable(self):
        """Test error when Stripe is not available."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.client_stage = 'lead'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        service._stripe = None

        with patch.object(ClientPaymentService, 'stripe', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            result = service.create_analysis_payment_intent(client_id=1)

        assert result['success'] == False
        assert 'unavailable' in result['error']


class TestConfirmAnalysisPayment:
    """Tests for confirm_analysis_payment method."""

    def test_success_with_stripe(self):
        """Test successful analysis payment confirmation with Stripe."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.retrieve.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.confirm_analysis_payment(
                client_id=1,
                payment_intent_id='pi_123'
            )

        assert result['success'] == True
        assert result['client_stage'] == 'analysis_paid'
        assert result['analysis_credit'] == ANALYSIS_PRICE
        assert result['round_1_due'] == ROUND_1_WITH_CREDIT
        assert mock_client.client_stage == 'analysis_paid'
        assert mock_client.total_paid == ANALYSIS_PRICE

    def test_success_without_stripe(self):
        """Test analysis payment in test mode (no Stripe)."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        service._stripe = None

        with patch.object(ClientPaymentService, 'stripe', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            result = service.confirm_analysis_payment(
                client_id=1,
                payment_intent_id='test_pi_123'
            )

        assert result['success'] == True
        assert mock_client.client_stage == 'analysis_paid'

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientPaymentService(mock_db)
        result = service.confirm_analysis_payment(client_id=999, payment_intent_id='pi_123')

        assert result['success'] == False
        assert 'not found' in result['error']

    def test_payment_not_succeeded(self):
        """Test error when payment status is not succeeded."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.status = 'requires_payment_method'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.retrieve.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.confirm_analysis_payment(
                client_id=1,
                payment_intent_id='pi_123'
            )

        assert result['success'] == False
        assert 'not successful' in result['error']


class TestCreateRoundPaymentIntent:
    """Tests for create_round_payment_intent method."""

    def test_round_1_with_analysis_credit(self):
        """Test Round 1 payment with analysis credit applied."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.current_dispute_round = 0
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_secret_r1'
        mock_intent.id = 'pi_r1'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.create_round_payment_intent(client_id=1, round_number=1)

        assert result['success'] == True
        assert result['amount'] == ROUND_1_WITH_CREDIT  # $298

    def test_round_1_without_analysis_credit(self):
        """Test Round 1 payment without prior analysis payment."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.current_dispute_round = 0
        mock_client.analysis_paid_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_secret_r1'
        mock_intent.id = 'pi_r1'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.create_round_payment_intent(client_id=1, round_number=1)

        assert result['amount'] == ROUND_1_PRICE  # $497

    def test_round_2_plus_payment(self):
        """Test Round 2+ payment amount."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.current_dispute_round = 1
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_secret_r2'
        mock_intent.id = 'pi_r2'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.create_round_payment_intent(client_id=1, round_number=2)

        assert result['amount'] == ROUND_2_PLUS_PRICE  # $297

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientPaymentService(mock_db)
        result = service.create_round_payment_intent(client_id=999)

        assert result['success'] == False

    def test_test_mode_returns_amount(self):
        """Test mode returns amount without Stripe."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.current_dispute_round = 0
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        service._stripe = None

        with patch.object(ClientPaymentService, 'stripe', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            result = service.create_round_payment_intent(client_id=1, round_number=1)

        assert result['success'] == True
        assert result['test_mode'] == True
        assert result['amount'] == ROUND_1_WITH_CREDIT


class TestConfirmRoundPayment:
    """Tests for confirm_round_payment method."""

    def test_round_1_activates_client(self):
        """Test Round 1 payment activates client."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_client.total_paid = ANALYSIS_PRICE
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.retrieve.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.confirm_round_payment(
                client_id=1,
                payment_intent_id='pi_r1',
                round_number=1
            )

        assert result['success'] == True
        assert mock_client.client_stage == 'active'
        assert mock_client.dispute_status == 'active'
        assert mock_client.current_dispute_round == 1

    def test_round_2_updates_round(self):
        """Test Round 2 payment updates round number."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_client.total_paid = ANALYSIS_PRICE + ROUND_1_WITH_CREDIT
        mock_client.current_dispute_round = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.retrieve.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.confirm_round_payment(
                client_id=1,
                payment_intent_id='pi_r2',
                round_number=2
            )

        assert result['success'] == True
        assert mock_client.current_dispute_round == 2

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientPaymentService(mock_db)
        result = service.confirm_round_payment(
            client_id=999,
            payment_intent_id='pi_123',
            round_number=1
        )

        assert result['success'] == False


class TestChargeForRound:
    """Tests for charge_for_round method."""

    def test_uses_prepaid_round(self):
        """Test charging when client has prepaid rounds."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.prepay_rounds_remaining = 5
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.charge_for_round(client_id=1, round_number=2)

        assert result['success'] == True
        assert result['used_prepaid'] == True
        assert result['prepaid_rounds_remaining'] == 4
        assert mock_client.prepay_rounds_remaining == 4

    def test_no_payment_method_requires_payment(self):
        """Test error when no payment method and no prepaid rounds."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.prepay_rounds_remaining = 0
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_stripe = MagicMock()
        with patch.object(service, '_stripe', mock_stripe):
            result = service.charge_for_round(client_id=1, round_number=2)

        assert result['success'] == False
        assert result['requires_payment'] == True

    def test_stripe_payment_success(self):
        """Test successful Stripe payment for round."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.prepay_rounds_remaining = 0
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_client.total_paid = ANALYSIS_PRICE
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_intent.id = 'pi_charge'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.charge_for_round(
                client_id=1,
                round_number=2,
                payment_method_id='pm_123'
            )

        assert result['success'] == True
        assert result['can_send_letters'] == True

    def test_stripe_payment_failed(self):
        """Test Stripe payment failure for round."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.prepay_rounds_remaining = 0
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.status = 'requires_action'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.charge_for_round(
                client_id=1,
                round_number=2,
                payment_method_id='pm_123'
            )

        assert result['success'] == False
        assert result['requires_action'] == True

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientPaymentService(mock_db)
        result = service.charge_for_round(client_id=999, round_number=1)

        assert result['success'] == False


class TestCreatePrepayCheckout:
    """Tests for create_prepay_checkout method."""

    def test_starter_package_checkout(self):
        """Test creating checkout for Starter package."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_session = MagicMock()
        mock_session.url = 'https://checkout.stripe.com/sess_123'
        mock_session.id = 'sess_123'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.checkout.Session.create.return_value = mock_session
            service._stripe = mock_stripe

            result = service.create_prepay_checkout(
                client_id=1,
                package_key='starter'
            )

        assert result['success'] == True
        assert result['package'] == 'starter'
        assert result['amount'] == PREPAY_PACKAGES['starter']['prepay_price']

    def test_financed_package_adds_upcharge(self):
        """Test financed package adds $200 upcharge."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_session = MagicMock()
        mock_session.url = 'https://checkout.stripe.com/sess_123'
        mock_session.id = 'sess_123'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.checkout.Session.create.return_value = mock_session
            service._stripe = mock_stripe

            result = service.create_prepay_checkout(
                client_id=1,
                package_key='standard',
                financed=True
            )

        expected_amount = PREPAY_PACKAGES['standard']['prepay_price'] + FINANCING_UPCHARGE
        assert result['amount'] == expected_amount

    def test_invalid_package(self):
        """Test error for invalid package key."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.create_prepay_checkout(
            client_id=1,
            package_key='invalid_package'
        )

        assert result['success'] == False
        assert 'Invalid package' in result['error']

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientPaymentService(mock_db)
        result = service.create_prepay_checkout(
            client_id=999,
            package_key='starter'
        )

        assert result['success'] == False

    def test_test_mode_returns_success(self):
        """Test mode returns success without Stripe."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        service._stripe = None

        with patch.object(ClientPaymentService, 'stripe', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            result = service.create_prepay_checkout(
                client_id=1,
                package_key='complete'
            )

        assert result['success'] == True
        assert result['test_mode'] == True


class TestConfirmPrepayPackage:
    """Tests for confirm_prepay_package method."""

    def test_success(self):
        """Test successful prepay package confirmation."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.confirm_prepay_package(
            client_id=1,
            session_id='sess_123',
            package_key='standard'
        )

        assert result['success'] == True
        assert result['rounds_available'] == 4
        assert mock_client.prepay_package == 'standard'
        assert mock_client.prepay_rounds_remaining == 4
        assert mock_client.client_stage == 'onboarding'

    def test_unlimited_package(self):
        """Test confirmation of unlimited package."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.confirm_prepay_package(
            client_id=1,
            session_id='sess_123',
            package_key='unlimited'
        )

        assert result['success'] == True
        assert mock_client.prepay_rounds_remaining == 99

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientPaymentService(mock_db)
        result = service.confirm_prepay_package(
            client_id=999,
            session_id='sess_123',
            package_key='starter'
        )

        assert result['success'] == False

    def test_invalid_package(self):
        """Test error for invalid package key."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.confirm_prepay_package(
            client_id=1,
            session_id='sess_123',
            package_key='invalid'
        )

        assert result['success'] == False


class TestCalculateSettlementFee:
    """Tests for calculate_settlement_fee method."""

    def test_basic_calculation(self):
        """Test basic 30% settlement fee calculation."""
        mock_db = MagicMock(spec=Session)
        service = ClientPaymentService(mock_db)

        result = service.calculate_settlement_fee(1000000)  # $10,000

        assert result['settlement_amount'] == 1000000
        assert result['fee_percent'] == 30
        assert result['fee_amount'] == 300000  # $3,000
        assert result['client_receives'] == 700000  # $7,000

    def test_fee_display_formatting(self):
        """Test fee display formatting."""
        mock_db = MagicMock(spec=Session)
        service = ClientPaymentService(mock_db)

        result = service.calculate_settlement_fee(250000)  # $2,500

        assert result['fee_display'] == '$750.00'
        assert result['client_receives_display'] == '$1,750.00'

    def test_small_amount(self):
        """Test fee with small settlement amount."""
        mock_db = MagicMock(spec=Session)
        service = ClientPaymentService(mock_db)

        result = service.calculate_settlement_fee(10000)  # $100

        assert result['fee_amount'] == 3000  # $30


class TestGetPaymentSummary:
    """Tests for get_payment_summary method."""

    def test_success_with_payments(self):
        """Test payment summary with payments made."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = ANALYSIS_PRICE + ROUND_1_WITH_CREDIT
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_client.current_dispute_round = 1
        mock_client.prepay_package = None
        mock_client.prepay_rounds_remaining = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.get_payment_summary(client_id=1)

        assert result['success'] == True
        assert result['current_round'] == 1
        assert result['next_round'] == 2
        assert result['next_payment_amount'] == ROUND_2_PLUS_PRICE
        assert result['analysis_credit_applied'] == True

    def test_prepaid_shows_no_payment_due(self):
        """Test summary shows no payment when prepaid rounds available."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = PREPAY_PACKAGES['standard']['prepay_price']
        mock_client.analysis_paid_at = None
        mock_client.current_dispute_round = 1
        mock_client.prepay_package = 'standard'
        mock_client.prepay_rounds_remaining = 3
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.get_payment_summary(client_id=1)

        assert result['success'] == True
        assert result['next_payment_amount'] == 0
        assert result['next_payment_display'] == 'Prepaid'
        assert result['prepay_rounds_remaining'] == 3

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientPaymentService(mock_db)
        result = service.get_payment_summary(client_id=999)

        assert result['success'] == False


class TestSavePaymentMethod:
    """Tests for save_payment_method method."""

    def test_success_new_customer(self):
        """Test saving payment method for new customer."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.stripe_customer_id = None

        # Use spec=False to allow arbitrary attributes
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_customer = MagicMock()
        mock_customer.id = 'cus_new'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.Customer.create.return_value = mock_customer
            service._stripe = mock_stripe

            result = service.save_payment_method(
                client_id=1,
                payment_method_id='pm_123'
            )

        assert result['success'] == True

    def test_stripe_unavailable(self):
        """Test error when Stripe is unavailable."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        service._stripe = None

        with patch.object(ClientPaymentService, 'stripe', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            result = service.save_payment_method(
                client_id=1,
                payment_method_id='pm_123'
            )

        assert result['success'] == False
        assert 'unavailable' in result['error']

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientPaymentService(mock_db)
        result = service.save_payment_method(
            client_id=999,
            payment_method_id='pm_123'
        )

        assert result['success'] == False


class TestExceptionHandling:
    """Tests for exception handling in all methods."""

    def test_create_analysis_payment_exception(self):
        """Test exception handling in create_analysis_payment_intent."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.client_stage = 'lead'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.side_effect = Exception("Stripe error")
            service._stripe = mock_stripe

            result = service.create_analysis_payment_intent(client_id=1)

        assert result['success'] == False
        assert 'Stripe error' in result['error']

    def test_confirm_analysis_payment_exception(self):
        """Test exception handling in confirm_analysis_payment."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.retrieve.side_effect = Exception("Stripe error")
            service._stripe = mock_stripe

            result = service.confirm_analysis_payment(
                client_id=1,
                payment_intent_id='pi_123'
            )

        assert result['success'] == False
        mock_db.rollback.assert_called_once()

    def test_charge_for_round_exception(self):
        """Test exception handling in charge_for_round."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.prepay_rounds_remaining = 0
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.side_effect = Exception("Card declined")
            service._stripe = mock_stripe

            result = service.charge_for_round(
                client_id=1,
                round_number=2,
                payment_method_id='pm_123'
            )

        assert result['success'] == False
        mock_db.rollback.assert_called_once()


class TestIntegration:
    """Integration tests for complete payment flows."""

    def test_full_payment_flow(self):
        """Test complete payment flow from analysis to Round 2."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'lead'
        mock_client.total_paid = 0
        mock_client.analysis_paid_at = None
        mock_client.current_dispute_round = 0
        mock_client.prepay_rounds_remaining = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        # Step 1: Analysis payment
        service._stripe = None
        with patch.object(ClientPaymentService, 'stripe', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None

            result = service.confirm_analysis_payment(
                client_id=1,
                payment_intent_id='test_pi_analysis'
            )

        assert result['success'] == True
        assert mock_client.client_stage == 'analysis_paid'

        # Update mock for next step
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_client.total_paid = ANALYSIS_PRICE

        # Step 2: Round 1 payment
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'

        mock_stripe = MagicMock()
        mock_stripe.PaymentIntent.retrieve.return_value = mock_intent
        service._stripe = mock_stripe

        result = service.confirm_round_payment(
            client_id=1,
            payment_intent_id='pi_r1',
            round_number=1
        )

        assert result['success'] == True
        assert mock_client.client_stage == 'active'
        assert mock_client.current_dispute_round == 1
