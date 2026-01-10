"""
Integration tests for payment workflow.

Tests the complete payment flow including:
1. Analysis payment creation and confirmation
2. Round payments with credit application
3. Prepay package checkout
4. Payment failure recovery
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestAnalysisPaymentWorkflow:
    """Tests for analysis payment workflow."""

    def test_full_analysis_payment_flow(self):
        """Test complete analysis payment flow."""
        from services.client_payment_service import (
            ClientPaymentService,
            ANALYSIS_PRICE,
            ROUND_1_WITH_CREDIT
        )

        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'lead'
        mock_client.total_paid = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        # Step 1: Create payment intent
        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_secret_analysis'
        mock_intent.id = 'pi_analysis'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            create_result = service.create_analysis_payment_intent(client_id=1)

        assert create_result['success'] == True
        assert create_result['amount'] == ANALYSIS_PRICE

        # Step 2: Confirm payment
        mock_intent.status = 'succeeded'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.retrieve.return_value = mock_intent
            service._stripe = mock_stripe

            confirm_result = service.confirm_analysis_payment(
                client_id=1,
                payment_intent_id='pi_analysis'
            )

        assert confirm_result['success'] == True
        assert mock_client.client_stage == 'analysis_paid'
        assert mock_client.total_paid == ANALYSIS_PRICE
        assert confirm_result['round_1_due'] == ROUND_1_WITH_CREDIT


class TestRoundPaymentWithCreditWorkflow:
    """Tests for round payment with credit application."""

    def test_round_1_with_analysis_credit(self):
        """Test Round 1 payment applies analysis credit."""
        from services.client_payment_service import (
            ClientPaymentService,
            ANALYSIS_PRICE,
            ROUND_1_WITH_CREDIT
        )

        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'analysis_paid'
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_client.total_paid = ANALYSIS_PRICE
        mock_client.current_dispute_round = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_secret_r1'
        mock_intent.id = 'pi_r1'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.create_round_payment_intent(
                client_id=1,
                round_number=1
            )

        # Should charge reduced price due to analysis credit
        assert result['amount'] == ROUND_1_WITH_CREDIT


class TestPrepayCheckoutWorkflow:
    """Tests for prepay package checkout workflow."""

    def test_starter_package_checkout(self):
        """Test Starter package checkout creates session."""
        from services.client_payment_service import (
            ClientPaymentService,
            PREPAY_PACKAGES
        )

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

    def test_confirm_prepay_activates_rounds(self):
        """Test confirming prepay package activates rounds."""
        from services.client_payment_service import (
            ClientPaymentService,
            PREPAY_PACKAGES
        )

        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_client.prepay_package = None
        mock_client.prepay_rounds_remaining = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        result = service.confirm_prepay_package(
            client_id=1,
            session_id='sess_123',
            package_key='standard'
        )

        assert result['success'] == True
        assert mock_client.prepay_package == 'standard'
        assert mock_client.prepay_rounds_remaining == 4  # Standard = 4 rounds
        assert mock_client.client_stage == 'onboarding'


class TestPaymentFailureRecoveryWorkflow:
    """Tests for payment failure and recovery."""

    def test_payment_failure_updates_stage(self):
        """Test payment failure updates client stage."""
        from services.stripe_webhooks_service import StripeWebhooksService

        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.client_stage = 'pending_payment'
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            with patch('services.stripe_webhooks_service.send_payment_failed_email'):
                event = {
                    'type': 'payment_intent.payment_failed',
                    'id': 'evt_fail',
                    'data': {
                        'object': {
                            'id': 'pi_failed',
                            'metadata': {
                                'client_id': '1',
                                'payment_type': 'round'
                            },
                            'last_payment_error': {
                                'message': 'Card declined'
                            }
                        }
                    }
                }

                result = service.handle_event(event)

        assert result['success'] == True
        assert mock_client.client_stage == 'payment_failed'

    def test_retry_payment_after_failure(self):
        """Test retrying payment after failure."""
        from services.client_payment_service import ClientPaymentService

        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'payment_failed'
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_client.current_dispute_round = 0
        mock_client.prepay_rounds_remaining = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        # Retry creates new payment intent
        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_secret_retry'
        mock_intent.id = 'pi_retry'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.create_round_payment_intent(
                client_id=1,
                round_number=1
            )

        assert result['success'] == True


class TestSettlementFeeWorkflow:
    """Tests for settlement fee calculation workflow."""

    def test_settlement_fee_calculation(self):
        """Test settlement fee calculation."""
        from services.client_payment_service import (
            ClientPaymentService,
            SETTLEMENT_FEE_PERCENT
        )

        mock_db = MagicMock(spec=Session)
        service = ClientPaymentService(mock_db)

        # Calculate fee for $10,000 settlement
        result = service.calculate_settlement_fee(1000000)  # Cents

        assert result['settlement_amount'] == 1000000
        assert result['fee_percent'] == SETTLEMENT_FEE_PERCENT
        assert result['fee_amount'] == 300000  # 30% of $10,000
        assert result['client_receives'] == 700000

    def test_settlement_fee_formatting(self):
        """Test settlement fee display formatting."""
        from services.client_payment_service import ClientPaymentService

        mock_db = MagicMock(spec=Session)
        service = ClientPaymentService(mock_db)

        result = service.calculate_settlement_fee(500000)  # $5,000

        assert result['fee_display'] == '$1,500.00'
        assert result['client_receives_display'] == '$3,500.00'


class TestPaymentSummaryWorkflow:
    """Tests for payment summary workflow."""

    def test_payment_summary_with_prepaid(self):
        """Test payment summary shows prepaid correctly."""
        from services.client_payment_service import ClientPaymentService

        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 129500  # Standard package price
        mock_client.analysis_paid_at = None  # No separate analysis payment
        mock_client.current_dispute_round = 2
        mock_client.prepay_package = 'standard'
        mock_client.prepay_rounds_remaining = 2

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.get_payment_summary(client_id=1)

        assert result['success'] == True
        assert result['next_payment_amount'] == 0
        assert result['next_payment_display'] == 'Prepaid'
        assert result['prepay_rounds_remaining'] == 2
