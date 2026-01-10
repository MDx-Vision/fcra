"""
Unit tests for PaymentPlanService

Tests installment payment plan management including:
- Plan creation with various frequencies
- Payment recording and application
- Plan lifecycle (pause, resume, cancel, default)
- Late fee handling
- Dashboard and reporting
"""

import pytest
from datetime import datetime, date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from services.payment_plan_service import (
    PaymentPlanService,
    FREQUENCY_DAYS,
)


class TestConstants:
    """Tests for payment plan constants."""

    def test_frequency_days_defined(self):
        """Test frequency days are defined."""
        assert 'weekly' in FREQUENCY_DAYS
        assert 'biweekly' in FREQUENCY_DAYS
        assert 'monthly' in FREQUENCY_DAYS

        assert FREQUENCY_DAYS['weekly'] == 7
        assert FREQUENCY_DAYS['biweekly'] == 14
        assert FREQUENCY_DAYS['monthly'] is None  # Uses relativedelta


class TestServiceInit:
    """Tests for PaymentPlanService initialization."""

    def test_init_with_db(self):
        """Test initialization with database session."""
        mock_db = MagicMock(spec=Session)
        service = PaymentPlanService(db=mock_db)
        assert service.db == mock_db
        assert service._owns_session == False

    def test_init_without_db(self):
        """Test initialization without database session."""
        with patch('services.payment_plan_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            service = PaymentPlanService()
            assert service._owns_session == True


class TestCreatePlan:
    """Tests for create_plan method."""

    def test_success(self):
        """Test successful plan creation."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.to_dict.return_value = {'id': 1}

        with patch('services.payment_plan_service.PaymentPlan') as MockPlan:
            MockPlan.return_value = mock_plan

            service = PaymentPlanService(db=mock_db)
            result = service.create_plan(
                client_id=1,
                total_amount=1000.00,
                num_installments=4,
                down_payment=200.00,
                frequency='monthly'
            )

        assert result['success'] == True
        assert 'plan' in result
        assert 'installments' in result

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = PaymentPlanService(db=mock_db)
        result = service.create_plan(
            client_id=999,
            total_amount=1000.00,
            num_installments=4
        )

        assert result['success'] == False
        assert 'Client not found' in result['error']

    def test_invalid_total_amount(self):
        """Test error for invalid total amount."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = PaymentPlanService(db=mock_db)
        result = service.create_plan(
            client_id=1,
            total_amount=-100,
            num_installments=4
        )

        assert result['success'] == False
        assert 'positive' in result['error']

    def test_invalid_num_installments(self):
        """Test error for invalid number of installments."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = PaymentPlanService(db=mock_db)
        result = service.create_plan(
            client_id=1,
            total_amount=1000,
            num_installments=0
        )

        assert result['success'] == False
        assert 'at least 1' in result['error']

    def test_down_payment_exceeds_total(self):
        """Test error when down payment exceeds total."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = PaymentPlanService(db=mock_db)
        result = service.create_plan(
            client_id=1,
            total_amount=1000,
            num_installments=4,
            down_payment=1500
        )

        assert result['success'] == False
        assert 'cannot exceed' in result['error']

    def test_invalid_frequency(self):
        """Test error for invalid frequency."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = PaymentPlanService(db=mock_db)
        result = service.create_plan(
            client_id=1,
            total_amount=1000,
            num_installments=4,
            frequency='invalid'
        )

        assert result['success'] == False
        assert 'Invalid frequency' in result['error']


class TestGetPlan:
    """Tests for get_plan method."""

    def test_found(self):
        """Test getting existing plan."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.to_dict.return_value = {'id': 1}
        mock_plan.client_id = 1

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test'
        mock_client.email = 'test@example.com'

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_plan, mock_client]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = PaymentPlanService(db=mock_db)
        result = service.get_plan(plan_id=1)

        assert result is not None
        assert 'plan' in result

    def test_not_found(self):
        """Test when plan not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = PaymentPlanService(db=mock_db)
        result = service.get_plan(plan_id=999)

        assert result is None


class TestRecordPayment:
    """Tests for record_payment method."""

    def test_success(self):
        """Test successful payment recording."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.status = 'active'
        mock_plan.total_amount = 1000
        mock_plan.amount_paid = 0
        mock_plan.down_payment = 0
        mock_plan.num_installments = 4
        mock_plan.to_dict.return_value = {'id': 1}

        mock_installment = MagicMock()
        mock_installment.amount_due = 250
        mock_installment.amount_paid = 0
        mock_installment.to_dict.return_value = {'id': 1}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_installment]
        mock_db.query.return_value.filter.return_value.scalar.return_value = 1

        mock_payment = MagicMock()
        mock_payment.id = 1
        mock_payment.to_dict.return_value = {'id': 1}

        with patch('services.payment_plan_service.PaymentPlanPayment') as MockPayment:
            MockPayment.return_value = mock_payment

            service = PaymentPlanService(db=mock_db)
            result = service.record_payment(
                plan_id=1,
                amount=250,
                payment_method='manual'
            )

        assert result['success'] == True
        assert 'payment' in result

    def test_plan_not_found(self):
        """Test error when plan not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = PaymentPlanService(db=mock_db)
        result = service.record_payment(plan_id=999, amount=100)

        assert result['success'] == False
        assert 'not found' in result['error']

    def test_plan_already_completed(self):
        """Test error when plan is completed."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'completed'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.record_payment(plan_id=1, amount=100)

        assert result['success'] == False
        assert 'completed' in result['error']

    def test_invalid_amount(self):
        """Test error for invalid payment amount."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'active'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.record_payment(plan_id=1, amount=-50)

        assert result['success'] == False
        assert 'positive' in result['error']


class TestPausePlan:
    """Tests for pause_plan method."""

    def test_success(self):
        """Test successful plan pause."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'active'
        mock_plan.to_dict.return_value = {'id': 1, 'status': 'paused'}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.pause_plan(plan_id=1, reason='Client request')

        assert result['success'] == True
        assert mock_plan.status == 'paused'

    def test_plan_not_found(self):
        """Test error when plan not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = PaymentPlanService(db=mock_db)
        result = service.pause_plan(plan_id=999)

        assert result['success'] == False

    def test_cannot_pause_completed(self):
        """Test cannot pause completed plan."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'completed'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.pause_plan(plan_id=1)

        assert result['success'] == False
        assert 'Cannot pause' in result['error']


class TestResumePlan:
    """Tests for resume_plan method."""

    def test_success(self):
        """Test successful plan resume."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'paused'
        mock_plan.to_dict.return_value = {'id': 1, 'status': 'active'}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.resume_plan(plan_id=1)

        assert result['success'] == True
        assert mock_plan.status == 'active'

    def test_not_paused(self):
        """Test error when plan not paused."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'active'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.resume_plan(plan_id=1)

        assert result['success'] == False
        assert 'not paused' in result['error']


class TestCancelPlan:
    """Tests for cancel_plan method."""

    def test_success(self):
        """Test successful plan cancellation."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'active'
        mock_plan.internal_notes = ''
        mock_plan.to_dict.return_value = {'id': 1, 'status': 'cancelled'}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.cancel_plan(plan_id=1, reason='Client cancelled')

        assert result['success'] == True
        assert mock_plan.status == 'cancelled'

    def test_cannot_cancel_completed(self):
        """Test cannot cancel completed plan."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'completed'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.cancel_plan(plan_id=1)

        assert result['success'] == False
        assert 'completed' in result['error']


class TestMarkDefaulted:
    """Tests for mark_defaulted method."""

    def test_success(self):
        """Test successful default marking."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'active'
        mock_plan.to_dict.return_value = {'id': 1, 'status': 'defaulted'}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.mark_defaulted(plan_id=1, reason='Non-payment')

        assert result['success'] == True
        assert mock_plan.status == 'defaulted'

    def test_cannot_default_completed(self):
        """Test cannot default completed plan."""
        mock_db = MagicMock(spec=Session)
        mock_plan = MagicMock()
        mock_plan.status = 'completed'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        service = PaymentPlanService(db=mock_db)
        result = service.mark_defaulted(plan_id=1)

        assert result['success'] == False


class TestCheckLatePayments:
    """Tests for check_late_payments method."""

    def test_no_late_payments(self):
        """Test when no payments are late."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = PaymentPlanService(db=mock_db)
        result = service.check_late_payments()

        assert result['success'] == True
        assert result['updated_count'] == 0


class TestGetDueSoon:
    """Tests for get_due_soon method."""

    def test_returns_due_installments(self):
        """Test returns installments due soon."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = PaymentPlanService(db=mock_db)
        result = service.get_due_soon(days=7)

        assert isinstance(result, list)


class TestGetOverdue:
    """Tests for get_overdue method."""

    def test_returns_overdue_installments(self):
        """Test returns overdue installments."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = PaymentPlanService(db=mock_db)
        result = service.get_overdue()

        assert isinstance(result, list)


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary method."""

    def test_returns_summary(self):
        """Test returns dashboard summary."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = (0, 0, 0)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = PaymentPlanService(db=mock_db)
        result = service.get_dashboard_summary()

        assert 'status_counts' in result
        assert 'totals' in result
        assert 'overdue_count' in result


class TestListPlans:
    """Tests for list_plans method."""

    def test_list_all(self):
        """Test listing all plans."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.count.return_value = 0

        service = PaymentPlanService(db=mock_db)
        result = service.list_plans()

        assert 'plans' in result
        assert 'total' in result

    def test_filter_by_status(self):
        """Test filtering by status."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        service = PaymentPlanService(db=mock_db)
        result = service.list_plans(status='active')

        # Filter should be called
        mock_db.query.return_value.filter.assert_called()


class TestWaiveInstallment:
    """Tests for waive_installment method."""

    def test_success(self):
        """Test successful installment waiver."""
        mock_db = MagicMock(spec=Session)

        mock_installment = MagicMock()
        mock_installment.plan_id = 1
        mock_installment.amount_due = 250
        mock_installment.to_dict.return_value = {'id': 1}

        mock_plan = MagicMock()
        mock_plan.amount_remaining = 1000
        mock_plan.installments_completed = 0
        mock_plan.installments_remaining = 4
        mock_plan.to_dict.return_value = {'id': 1}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_installment, mock_plan
        ]

        service = PaymentPlanService(db=mock_db)
        result = service.waive_installment(installment_id=1, reason='Goodwill')

        assert result['success'] == True
        assert mock_installment.status == 'waived'

    def test_not_found(self):
        """Test error when installment not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = PaymentPlanService(db=mock_db)
        result = service.waive_installment(installment_id=999)

        assert result['success'] == False


class TestExportPlans:
    """Tests for export_plans method."""

    def test_returns_export_data(self):
        """Test returns exportable data."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        service = PaymentPlanService(db=mock_db)
        result = service.export_plans()

        assert isinstance(result, list)
