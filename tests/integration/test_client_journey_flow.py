"""
Integration tests for complete client journey workflow.

Tests the full flow from lead capture through active client status:
1. Lead capture and analysis
2. Analysis payment
3. CROA signing workflow
4. Round 1 payment and activation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestLeadToAnalysisPaidFlow:
    """Tests for lead capture to analysis payment flow."""

    def test_complete_lead_to_analysis_flow(self):
        """Test complete flow from lead to analysis_paid."""
        from services.free_analysis_service import FreeAnalysisService, ANALYSIS_PRICE

        mock_db = MagicMock(spec=Session)

        # Step 1: Create lead
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'lead'
        mock_client.total_paid = 0
        mock_client.free_analysis_token = 'test_token_123'

        with patch('services.free_analysis_service.Client') as MockClient:
            MockClient.return_value = mock_client

            service = FreeAnalysisService(mock_db)
            result = service.create_lead_from_upload(
                name='Test Client',
                email='test@example.com',
                phone='555-1234'
            )

        assert result['success'] == True
        assert result['is_existing'] == False

        # Step 2: Mark analysis paid
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        result = service.mark_analysis_paid(
            client_id=1,
            payment_intent_id='pi_test_123'
        )

        assert result['success'] == True
        assert mock_client.client_stage == 'analysis_paid'
        assert mock_client.analysis_payment_id == 'pi_test_123'
        assert mock_client.total_paid == ANALYSIS_PRICE


class TestAnalysisPaidToOnboardingFlow:
    """Tests for analysis_paid to onboarding flow."""

    def test_proceed_to_onboarding(self):
        """Test proceeding from analysis_paid to onboarding."""
        from services.free_analysis_service import FreeAnalysisService

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.client_stage = 'analysis_paid'
        mock_client.portal_token = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = FreeAnalysisService(mock_db)
        result = service.proceed_to_onboarding(client_id=1)

        assert result['success'] == True
        assert mock_client.client_stage == 'onboarding'
        assert mock_client.portal_token is not None


class TestPaymentToActiveFlow:
    """Tests for payment to active client flow."""

    def test_round_1_payment_activates_client(self):
        """Test Round 1 payment activates client."""
        from services.client_payment_service import (
            ClientPaymentService,
            ROUND_1_WITH_CREDIT
        )

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_client.total_paid = 19900  # Analysis already paid
        mock_client.current_dispute_round = 0
        mock_client.client_stage = 'pending_payment'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.retrieve.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.confirm_round_payment(
                client_id=1,
                payment_intent_id='pi_round1',
                round_number=1
            )

        assert result['success'] == True
        assert mock_client.client_stage == 'active'
        assert mock_client.dispute_status == 'active'
        assert mock_client.current_dispute_round == 1


class TestWebhookToClientStateFlow:
    """Tests for webhook events updating client state."""

    def test_payment_succeeded_updates_state(self):
        """Test payment success webhook updates client state."""
        from services.stripe_webhooks_service import StripeWebhooksService

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_client.client_stage = 'lead'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            event = {
                'type': 'payment_intent.succeeded',
                'id': 'evt_test',
                'data': {
                    'object': {
                        'id': 'pi_analysis',
                        'amount': 19900,
                        'metadata': {
                            'client_id': '1',
                            'payment_type': 'analysis'
                        }
                    }
                }
            }

            result = service.handle_event(event)

        assert result['success'] == True
        assert mock_client.client_stage == 'analysis_paid'
        assert mock_client.total_paid == 19900


class TestScheduledJobFlow:
    """Tests for scheduled job flows."""

    def test_capture_due_payments_activates_clients(self):
        """Test capture_due_payments job activates ready clients."""
        from services.scheduled_jobs_service import ScheduledJobsService

        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'pending_payment'

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_client]

        service = ScheduledJobsService(mock_db)

        with patch('services.timeline_service.log_milestone'):
            result = service.capture_due_payments()

        assert result['success'] == True
        assert result['results']['captured'] == 1
        assert mock_client.client_stage == 'active'


class TestBatchOperationFlow:
    """Tests for batch operation flows."""

    def test_batch_status_update_flow(self):
        """Test batch status update flow."""
        from services.batch_processing_service import BatchProcessingService

        mock_session = MagicMock(spec=Session)

        service = BatchProcessingService(session=mock_session)

        # Create job
        with patch('services.batch_processing_service.BatchJob') as MockJob:
            mock_job = MagicMock()
            mock_job.id = 1
            mock_job.job_uuid = 'test-uuid'
            mock_job.to_dict.return_value = {'id': 1}
            MockJob.return_value = mock_job

            success, message, job_dict = service.create_job(
                name='Test Batch',
                action_type='update_status',
                client_ids=[1, 2, 3],
                action_params={'new_status': 'active'},
                staff_id=1
            )

        assert success == True


class TestRoundProgressionFlow:
    """Tests for round progression flow."""

    def test_round_2_payment_after_round_1(self):
        """Test Round 2 payment after completing Round 1."""
        from services.client_payment_service import (
            ClientPaymentService,
            ROUND_2_PLUS_PRICE
        )

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_client.analysis_paid_at = datetime.utcnow() - timedelta(days=30)
        mock_client.total_paid = 49700  # Analysis + Round 1
        mock_client.current_dispute_round = 1
        mock_client.client_stage = 'active'
        mock_client.prepay_rounds_remaining = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)

        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_secret_r2'
        mock_intent.id = 'pi_r2'

        with patch.object(service, '_stripe') as mock_stripe:
            mock_stripe.PaymentIntent.create.return_value = mock_intent
            service._stripe = mock_stripe

            result = service.create_round_payment_intent(
                client_id=1,
                round_number=2
            )

        assert result['success'] == True
        assert result['amount'] == ROUND_2_PLUS_PRICE


class TestPrepayPackageFlow:
    """Tests for prepay package flow."""

    def test_prepay_uses_prepaid_rounds(self):
        """Test prepay package uses prepaid rounds."""
        from services.client_payment_service import ClientPaymentService

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.prepay_rounds_remaining = 4
        mock_client.analysis_paid_at = datetime.utcnow()
        mock_client.current_dispute_round = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = ClientPaymentService(mock_db)
        result = service.charge_for_round(client_id=1, round_number=2)

        assert result['success'] == True
        assert result['used_prepaid'] == True
        assert mock_client.prepay_rounds_remaining == 3


class TestMetricsCalculationFlow:
    """Tests for metrics calculation flows."""

    def test_roi_calculation_with_violations(self):
        """Test ROI calculation includes violations."""
        from services.roi_calculator_service import ROICalculatorService

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'

        mock_violation = MagicMock()
        mock_violation.violation_type = 'FCRA'
        mock_violation.fcra_section = '1681'
        mock_violation.is_willful = True
        mock_violation.statutory_damages_min = 500
        mock_violation.statutory_damages_max = 1000

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_violation]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = ROICalculatorService(db=mock_db)
        result = service.calculate_roi(client_id=1, save=False)

        assert result['success'] == True
        assert result['violations']['total'] >= 1
        assert result['statutory_damages']['max'] >= 1000
