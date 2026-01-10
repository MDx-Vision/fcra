"""
Unit tests for SubscriptionService

Tests Stripe subscription billing including plan management,
customer creation, subscription lifecycle, and webhook handling.
"""

import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session

from services.subscription_service import (
    SubscriptionService,
    get_subscription_service,
    SUBSCRIPTION_PLANS
)


class TestSubscriptionServiceInit:
    """Tests for SubscriptionService initialization."""

    def test_init_with_db_session(self):
        """Test initialization with database session."""
        mock_db = MagicMock(spec=Session)
        with patch('services.subscription_service.stripe'):
            service = SubscriptionService(mock_db)
            assert service.db == mock_db

    def test_factory_function(self):
        """Test the factory function creates service instance."""
        mock_db = MagicMock(spec=Session)
        with patch('services.subscription_service.stripe'):
            service = get_subscription_service(mock_db)
            assert isinstance(service, SubscriptionService)


class TestSubscriptionPlansConfig:
    """Tests for subscription plans configuration."""

    def test_plans_defined(self):
        """Test all expected plans are defined."""
        assert 'basic' in SUBSCRIPTION_PLANS
        assert 'pro' in SUBSCRIPTION_PLANS
        assert 'enterprise' in SUBSCRIPTION_PLANS

    def test_plan_structure(self):
        """Test each plan has required fields."""
        for plan_key, plan in SUBSCRIPTION_PLANS.items():
            assert 'name' in plan
            assert 'display_name' in plan
            assert 'price_cents' in plan
            assert 'billing_interval' in plan
            assert 'features' in plan
            assert isinstance(plan['features'], list)
            assert plan['billing_interval'] == 'month'

    def test_plan_prices(self):
        """Test plan prices are set correctly."""
        assert SUBSCRIPTION_PLANS['basic']['price_cents'] == 4900
        assert SUBSCRIPTION_PLANS['pro']['price_cents'] == 9900
        assert SUBSCRIPTION_PLANS['enterprise']['price_cents'] == 19900


class TestGetPlans:
    """Tests for get_plans method."""

    def test_get_active_plans(self):
        """Test getting active plans from database."""
        mock_db = MagicMock(spec=Session)

        mock_plans = [
            SimpleNamespace(
                id=1, name='basic', display_name='Basic Plan',
                price_cents=4900, billing_interval='month',
                features=['Feature 1'], stripe_price_id='price_123',
                is_active=True, sort_order=1
            ),
            SimpleNamespace(
                id=2, name='pro', display_name='Pro Plan',
                price_cents=9900, billing_interval='month',
                features=['Feature 1', 'Feature 2'], stripe_price_id='price_456',
                is_active=True, sort_order=2
            ),
        ]

        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_plans
        mock_db.query.return_value = mock_query

        with patch('services.subscription_service.stripe'):
            service = SubscriptionService(mock_db)
            plans = service.get_plans(active_only=True)

        assert len(plans) == 2
        assert plans[0]['name'] == 'basic'
        assert plans[0]['price_dollars'] == 49.00
        assert plans[1]['name'] == 'pro'

    def test_get_plan_by_name(self):
        """Test getting a specific plan by name."""
        mock_db = MagicMock(spec=Session)

        mock_plan = SimpleNamespace(
            id=1, name='pro', stripe_price_id='price_123'
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        with patch('services.subscription_service.stripe'):
            service = SubscriptionService(mock_db)
            plan = service.get_plan_by_name('pro')

        assert plan.name == 'pro'


class TestCustomerManagement:
    """Tests for customer management methods."""

    @patch('services.subscription_service.stripe')
    def test_get_or_create_customer_existing(self, mock_stripe):
        """Test getting existing Stripe customer."""
        mock_db = MagicMock(spec=Session)

        # Client with existing subscription
        mock_subscription = SimpleNamespace(stripe_customer_id='cus_existing')
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        mock_client = SimpleNamespace(
            id=1, email='test@example.com', first_name='John', last_name='Doe'
        )

        service = SubscriptionService(mock_db)
        customer_id = service.get_or_create_stripe_customer(mock_client)

        assert customer_id == 'cus_existing'

    @patch('services.subscription_service.stripe')
    def test_get_or_create_customer_new(self, mock_stripe):
        """Test creating new Stripe customer."""
        mock_db = MagicMock(spec=Session)

        # No existing subscription
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # No existing Stripe customer
        mock_stripe.Customer.list.return_value = SimpleNamespace(data=[])
        mock_stripe.Customer.create.return_value = SimpleNamespace(id='cus_new')

        mock_client = SimpleNamespace(
            id=1, email='test@example.com', first_name='John', last_name='Doe'
        )

        service = SubscriptionService(mock_db)
        customer_id = service.get_or_create_stripe_customer(mock_client)

        assert customer_id == 'cus_new'
        mock_stripe.Customer.create.assert_called_once()


class TestSubscriptionLifecycle:
    """Tests for subscription lifecycle methods."""

    @patch('services.subscription_service.stripe')
    def test_create_checkout_session(self, mock_stripe):
        """Test creating a Stripe checkout session."""
        mock_db = MagicMock(spec=Session)

        # Mock client
        mock_client = SimpleNamespace(
            id=1, email='test@example.com', first_name='John', last_name='Doe'
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_client,  # get client
            None,  # no existing subscription for customer lookup
        ]

        # Mock plan
        mock_plan = SimpleNamespace(
            id=1, name='pro', stripe_price_id='price_pro'
        )

        # Mock Stripe
        mock_stripe.Customer.list.return_value = SimpleNamespace(data=[])
        mock_stripe.Customer.create.return_value = SimpleNamespace(id='cus_123')
        mock_stripe.checkout.Session.create.return_value = SimpleNamespace(
            id='sess_123', url='https://checkout.stripe.com/sess_123'
        )

        service = SubscriptionService(mock_db)
        with patch.object(service, 'get_plan_by_name', return_value=mock_plan):
            with patch.object(service, 'get_or_create_stripe_customer', return_value='cus_123'):
                result = service.create_checkout_session(
                    client_id=1,
                    plan_name='pro',
                    success_url='http://example.com/success',
                    cancel_url='http://example.com/cancel'
                )

        assert result['session_id'] == 'sess_123'
        assert 'url' in result

    @patch('services.subscription_service.stripe')
    def test_create_checkout_session_invalid_client(self, mock_stripe):
        """Test checkout session with invalid client."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = SubscriptionService(mock_db)

        with pytest.raises(ValueError, match="Client 999 not found"):
            service.create_checkout_session(
                client_id=999,
                plan_name='pro',
                success_url='http://example.com/success',
                cancel_url='http://example.com/cancel'
            )

    @patch('services.subscription_service.stripe')
    def test_cancel_subscription_at_period_end(self, mock_stripe):
        """Test cancelling subscription at period end."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = MagicMock()
        mock_subscription.stripe_subscription_id = 'sub_123'
        mock_subscription.cancel_at_period_end = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        mock_stripe.Subscription.modify.return_value = SimpleNamespace(
            id='sub_123',
            status='active',
            cancel_at_period_end=True,
            current_period_end=1735689600  # 2025-01-01
        )

        service = SubscriptionService(mock_db)
        result = service.cancel_subscription(client_id=1, at_period_end=True)

        assert result['subscription_id'] == 'sub_123'
        assert result['cancel_at_period_end'] == True
        assert mock_subscription.cancel_at_period_end == True

    @patch('services.subscription_service.stripe')
    def test_cancel_subscription_immediately(self, mock_stripe):
        """Test cancelling subscription immediately."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = MagicMock()
        mock_subscription.stripe_subscription_id = 'sub_123'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        mock_stripe.Subscription.delete.return_value = SimpleNamespace(
            id='sub_123',
            status='canceled',
            cancel_at_period_end=False,
            current_period_end=None
        )

        service = SubscriptionService(mock_db)
        result = service.cancel_subscription(client_id=1, at_period_end=False)

        assert result['status'] == 'canceled'
        assert mock_subscription.status == 'canceled'

    @patch('services.subscription_service.stripe')
    def test_reactivate_subscription(self, mock_stripe):
        """Test reactivating a subscription pending cancellation."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = MagicMock()
        mock_subscription.stripe_subscription_id = 'sub_123'
        mock_subscription.cancel_at_period_end = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        mock_stripe.Subscription.modify.return_value = SimpleNamespace(
            id='sub_123',
            status='active',
            cancel_at_period_end=False
        )

        service = SubscriptionService(mock_db)
        result = service.reactivate_subscription(client_id=1)

        assert result['cancel_at_period_end'] == False
        assert mock_subscription.cancel_at_period_end == False

    @patch('services.subscription_service.stripe')
    def test_change_plan(self, mock_stripe):
        """Test upgrading/downgrading plan."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = MagicMock()
        mock_subscription.stripe_subscription_id = 'sub_123'
        mock_subscription.status = 'active'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        mock_plan = SimpleNamespace(id=2, name='enterprise', stripe_price_id='price_ent')

        mock_stripe.Subscription.retrieve.return_value = {
            'items': {'data': [SimpleNamespace(id='si_123')]}
        }
        mock_stripe.Subscription.modify.return_value = SimpleNamespace(
            id='sub_123',
            status='active'
        )

        service = SubscriptionService(mock_db)
        with patch.object(service, 'get_plan_by_name', return_value=mock_plan):
            result = service.change_plan(client_id=1, new_plan_name='enterprise')

        assert result['new_plan'] == 'enterprise'
        assert mock_subscription.plan_id == 2


class TestGetSubscription:
    """Tests for get_subscription method."""

    @patch('services.subscription_service.stripe')
    def test_get_subscription_with_plan(self, mock_stripe):
        """Test getting subscription with plan details."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = SimpleNamespace(
            id=1,
            stripe_subscription_id='sub_123',
            stripe_customer_id='cus_123',
            status='active',
            plan_id=1,
            current_period_start=datetime(2025, 1, 1),
            current_period_end=datetime(2025, 2, 1),
            cancel_at_period_end=False,
            canceled_at=None,
            amount_paid_cents=9900,
            next_payment_date=datetime(2025, 2, 1)
        )

        mock_plan = SimpleNamespace(
            id=1, name='pro', display_name='Pro Plan',
            price_cents=9900, features=['Feature 1']
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_subscription,
            mock_plan
        ]

        service = SubscriptionService(mock_db)
        result = service.get_subscription(client_id=1)

        assert result['status'] == 'active'
        assert result['plan']['name'] == 'pro'
        assert result['plan']['price_dollars'] == 99.00

    @patch('services.subscription_service.stripe')
    def test_get_subscription_not_found(self, mock_stripe):
        """Test getting subscription when none exists."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = SubscriptionService(mock_db)
        result = service.get_subscription(client_id=1)

        assert result is None


class TestBillingPortal:
    """Tests for billing portal session creation."""

    @patch('services.subscription_service.stripe')
    def test_create_billing_portal_session(self, mock_stripe):
        """Test creating a Stripe billing portal session."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = SimpleNamespace(
            stripe_customer_id='cus_123'
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        mock_stripe.billing_portal.Session.create.return_value = SimpleNamespace(
            url='https://billing.stripe.com/session/123'
        )

        service = SubscriptionService(mock_db)
        result = service.create_billing_portal_session(
            client_id=1,
            return_url='http://example.com/return'
        )

        assert 'url' in result
        assert result['return_url'] == 'http://example.com/return'

    @patch('services.subscription_service.stripe')
    def test_create_billing_portal_no_customer(self, mock_stripe):
        """Test billing portal with no customer."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = SimpleNamespace(stripe_customer_id=None)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        service = SubscriptionService(mock_db)

        with pytest.raises(ValueError, match="No customer found"):
            service.create_billing_portal_session(
                client_id=1,
                return_url='http://example.com/return'
            )


class TestWebhookHandlers:
    """Tests for webhook event handlers."""

    @patch('services.subscription_service.stripe')
    def test_handle_checkout_completed(self, mock_stripe):
        """Test handling checkout.session.completed webhook."""
        mock_db = MagicMock(spec=Session)

        mock_plan = SimpleNamespace(id=1, name='pro')

        # Mock subscription retrieval
        mock_stripe.Subscription.retrieve.return_value = SimpleNamespace(
            id='sub_123',
            customer='cus_123',
            status='active',
            cancel_at_period_end=False,
            current_period_start=1704067200,
            current_period_end=1706745600,
            metadata={'plan_name': 'pro'}
        )

        # No existing subscription
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = SubscriptionService(mock_db)
        with patch.object(service, 'get_plan_by_name', return_value=mock_plan):
            event = SimpleNamespace(
                type='checkout.session.completed',
                data=SimpleNamespace(object={
                    'mode': 'subscription',
                    'metadata': {'client_id': '1'},
                    'subscription': 'sub_123',
                    'customer': 'cus_123'
                })
            )
            result = service.handle_webhook_event(event)

        assert result['handled'] == True
        assert result['client_id'] == '1'

    @patch('services.subscription_service.stripe')
    def test_handle_subscription_updated(self, mock_stripe):
        """Test handling customer.subscription.updated webhook."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = MagicMock()
        mock_subscription.stripe_subscription_id = 'sub_123'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        service = SubscriptionService(mock_db)
        event = SimpleNamespace(
            type='customer.subscription.updated',
            data=SimpleNamespace(object={
                'id': 'sub_123',
                'status': 'active',
                'cancel_at_period_end': False,
                'current_period_start': 1704067200,
                'current_period_end': 1706745600,
                'canceled_at': None
            })
        )
        result = service.handle_webhook_event(event)

        assert result['handled'] == True
        assert mock_subscription.status == 'active'

    @patch('services.subscription_service.stripe')
    def test_handle_subscription_deleted(self, mock_stripe):
        """Test handling customer.subscription.deleted webhook."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = MagicMock()
        mock_subscription.stripe_subscription_id = 'sub_123'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        service = SubscriptionService(mock_db)
        event = SimpleNamespace(
            type='customer.subscription.deleted',
            data=SimpleNamespace(object={
                'id': 'sub_123'
            })
        )
        result = service.handle_webhook_event(event)

        assert result['handled'] == True
        assert mock_subscription.status == 'canceled'

    @patch('services.subscription_service.stripe')
    def test_handle_invoice_paid(self, mock_stripe):
        """Test handling invoice.paid webhook."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = MagicMock()
        mock_subscription.stripe_subscription_id = 'sub_123'
        mock_subscription.amount_paid_cents = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        service = SubscriptionService(mock_db)
        event = SimpleNamespace(
            type='invoice.paid',
            data=SimpleNamespace(object={
                'subscription': 'sub_123',
                'amount_paid': 9900,
                'next_payment_attempt': 1706745600
            })
        )
        result = service.handle_webhook_event(event)

        assert result['handled'] == True
        assert result['amount_paid'] == 9900
        assert mock_subscription.amount_paid_cents == 9900
        assert mock_subscription.status == 'active'

    @patch('services.subscription_service.stripe')
    def test_handle_invoice_payment_failed(self, mock_stripe):
        """Test handling invoice.payment_failed webhook."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = MagicMock()
        mock_subscription.stripe_subscription_id = 'sub_123'
        mock_subscription.status = 'active'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        service = SubscriptionService(mock_db)
        event = SimpleNamespace(
            type='invoice.payment_failed',
            data=SimpleNamespace(object={
                'subscription': 'sub_123'
            })
        )
        result = service.handle_webhook_event(event)

        assert result['handled'] == True
        assert result['status'] == 'past_due'
        assert mock_subscription.status == 'past_due'

    @patch('services.subscription_service.stripe')
    def test_handle_unknown_event(self, mock_stripe):
        """Test handling unknown webhook event type."""
        mock_db = MagicMock(spec=Session)

        service = SubscriptionService(mock_db)
        event = SimpleNamespace(
            type='unknown.event.type',
            data=SimpleNamespace(object={})
        )
        result = service.handle_webhook_event(event)

        assert result['handled'] == False
        assert result['event_type'] == 'unknown.event.type'


class TestSyncPlansToStripe:
    """Tests for sync_plans_to_stripe method."""

    @patch('services.subscription_service.stripe')
    def test_sync_creates_new_products(self, mock_stripe):
        """Test syncing plans creates new Stripe products."""
        mock_db = MagicMock(spec=Session)

        # No existing plans in database
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock Stripe API
        mock_stripe.Product.create.return_value = SimpleNamespace(id='prod_123')
        mock_stripe.Price.create.return_value = SimpleNamespace(id='price_123')

        service = SubscriptionService(mock_db)
        results = service.sync_plans_to_stripe()

        # Should sync all 3 plans
        assert 'basic' in results
        assert 'pro' in results
        assert 'enterprise' in results
        assert results['basic']['product_id'] == 'prod_123'

    @patch('services.subscription_service.stripe')
    def test_sync_updates_existing_products(self, mock_stripe):
        """Test syncing plans updates existing Stripe products."""
        mock_db = MagicMock(spec=Session)

        # Existing plan in database
        existing_plan = MagicMock()
        existing_plan.stripe_product_id = 'prod_existing'
        existing_plan.stripe_price_id = 'price_existing'
        existing_plan.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = existing_plan

        # Mock Stripe API
        mock_stripe.Product.modify.return_value = SimpleNamespace(id='prod_existing')

        service = SubscriptionService(mock_db)
        results = service.sync_plans_to_stripe()

        # Should have called modify for existing products
        assert mock_stripe.Product.modify.called


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @patch('services.subscription_service.stripe')
    def test_cancel_no_subscription(self, mock_stripe):
        """Test cancelling when no subscription exists."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = SubscriptionService(mock_db)

        with pytest.raises(ValueError, match="No active subscription found"):
            service.cancel_subscription(client_id=1)

    @patch('services.subscription_service.stripe')
    def test_reactivate_not_pending_cancellation(self, mock_stripe):
        """Test reactivating subscription not pending cancellation."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = SubscriptionService(mock_db)

        with pytest.raises(ValueError, match="No subscription pending cancellation"):
            service.reactivate_subscription(client_id=1)

    @patch('services.subscription_service.stripe')
    def test_change_plan_no_subscription(self, mock_stripe):
        """Test changing plan when no subscription exists."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = SubscriptionService(mock_db)

        with pytest.raises(ValueError, match="No active subscription found"):
            service.change_plan(client_id=1, new_plan_name='enterprise')

    @patch('services.subscription_service.stripe')
    def test_change_plan_invalid_plan(self, mock_stripe):
        """Test changing to invalid plan."""
        mock_db = MagicMock(spec=Session)

        mock_subscription = MagicMock()
        mock_subscription.stripe_subscription_id = 'sub_123'
        mock_subscription.status = 'active'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        service = SubscriptionService(mock_db)
        with patch.object(service, 'get_plan_by_name', return_value=None):
            with pytest.raises(ValueError, match="Plan invalid_plan not found"):
                service.change_plan(client_id=1, new_plan_name='invalid_plan')
