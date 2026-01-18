"""
Unit Tests for Stripe Plans Service.
Tests for plan management, checkout sessions, webhooks, subscription management,
and related billing operations.
Covers all main functions with mocked Stripe API calls and database interactions.
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stripe_plans_service import StripePlansService


# =============================================================================
# Tests for Constants and Default Plans
# =============================================================================

class TestDefaultPlans:
    """Test default plan configurations."""

    def test_default_plans_exist(self):
        """Test that default plans are defined."""
        service = StripePlansService()
        assert len(service.DEFAULT_PLANS) == 3

    def test_basic_plan_config(self):
        """Test basic plan configuration."""
        service = StripePlansService()
        basic = next(p for p in service.DEFAULT_PLANS if p["name"] == "basic")
        assert basic["display_name"] == "Basic"
        assert basic["price_cents"] == 29900
        assert basic["billing_interval"] == "month"
        assert len(basic["features"]) > 0

    def test_professional_plan_config(self):
        """Test professional plan configuration."""
        service = StripePlansService()
        pro = next(p for p in service.DEFAULT_PLANS if p["name"] == "professional")
        assert pro["display_name"] == "Professional"
        assert pro["price_cents"] == 59900
        assert pro["billing_interval"] == "month"

    def test_premium_plan_config(self):
        """Test premium plan configuration."""
        service = StripePlansService()
        premium = next(p for p in service.DEFAULT_PLANS if p["name"] == "premium")
        assert premium["display_name"] == "Premium"
        assert premium["price_cents"] == 99900
        assert premium["billing_interval"] == "month"

    def test_plans_have_sort_order(self):
        """Test that all plans have sort order."""
        service = StripePlansService()
        for plan in service.DEFAULT_PLANS:
            assert "sort_order" in plan
            assert isinstance(plan["sort_order"], int)

    def test_plans_have_required_fields(self):
        """Test that all plans have required fields."""
        service = StripePlansService()
        required_fields = ["name", "display_name", "price_cents", "billing_interval", "features"]
        for plan in service.DEFAULT_PLANS:
            for field in required_fields:
                assert field in plan, f"Missing field {field} in plan {plan.get('name')}"


# =============================================================================
# Tests for Service Initialization
# =============================================================================

class TestServiceInitialization:
    """Test service initialization."""

    def test_init_creates_instance(self):
        """Test service initialization creates an instance."""
        service = StripePlansService()
        assert service is not None

    def test_init_stripe_is_none(self):
        """Test that stripe client is not initialized immediately."""
        service = StripePlansService()
        assert service._stripe is None

    def test_init_integration_id_is_none(self):
        """Test that integration ID is not set on init."""
        service = StripePlansService()
        assert service._integration_id is None


# =============================================================================
# Tests for test_connection()
# =============================================================================

class TestConnectionTest:
    """Test Stripe connection testing."""

    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    def test_connection_success(self, mock_stripe_prop):
        """Test successful connection test."""
        mock_stripe = MagicMock()
        mock_stripe.Account.retrieve.return_value = {"id": "acct_123"}
        mock_stripe_prop.return_value = mock_stripe

        service = StripePlansService()
        result = service.test_connection()

        assert result is True
        mock_stripe.Account.retrieve.assert_called_once()

    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    def test_connection_failure(self, mock_stripe_prop):
        """Test failed connection test."""
        mock_stripe = MagicMock()
        mock_stripe.Account.retrieve.side_effect = Exception("Connection failed")
        mock_stripe_prop.return_value = mock_stripe

        service = StripePlansService()
        result = service.test_connection()

        assert result is False


# =============================================================================
# Tests for create_plan()
# =============================================================================

class TestCreatePlan:
    """Test plan creation functionality."""

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_create_plan_success(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test successful plan creation."""
        mock_stripe = MagicMock()
        mock_product = MagicMock(id="prod_123")
        mock_price = MagicMock(id="price_456")
        mock_stripe.Product.create.return_value = mock_product
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_plan(
            name="test_plan",
            price_cents=4999,
            interval="month",
            features=["Feature 1", "Feature 2"],
            display_name="Test Plan"
        )

        assert result["success"] is True
        assert result["stripe_product_id"] == "prod_123"
        assert result["stripe_price_id"] == "price_456"
        assert result["name"] == "test_plan"
        assert result["price_cents"] == 4999

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_create_plan_updates_existing(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test plan creation updates existing plan."""
        mock_stripe = MagicMock()
        mock_product = MagicMock(id="prod_new")
        mock_price = MagicMock(id="price_new")
        mock_stripe.Product.create.return_value = mock_product
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe_prop.return_value = mock_stripe

        mock_existing = MagicMock()
        mock_existing.id = 1
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_existing
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_plan(
            name="existing_plan",
            price_cents=5999,
            interval="year"
        )

        assert result["success"] is True
        assert result["plan_id"] == 1
        assert mock_existing.stripe_product_id == "prod_new"

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_create_plan_uses_default_display_name(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test plan creation uses title case of name as default display name."""
        mock_stripe = MagicMock()
        mock_product = MagicMock(id="prod_123")
        mock_price = MagicMock(id="price_456")
        mock_stripe.Product.create.return_value = mock_product
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_plan(
            name="my_awesome_plan",
            price_cents=9999
        )

        assert result["success"] is True
        assert result["display_name"] == "My_Awesome_Plan"

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_create_plan_stripe_error(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test plan creation handles Stripe errors."""
        mock_stripe = MagicMock()
        mock_stripe.Product.create.side_effect = Exception("Stripe API error")
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_plan(name="test", price_cents=1000)

        assert result["success"] is False
        assert "Stripe API error" in result["error"]
        mock_db.rollback.assert_called()

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_create_plan_with_yearly_interval(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test plan creation with yearly interval."""
        mock_stripe = MagicMock()
        mock_product = MagicMock(id="prod_123")
        mock_price = MagicMock(id="price_456")
        mock_stripe.Product.create.return_value = mock_product
        mock_stripe.Price.create.return_value = mock_price
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_plan(
            name="annual_plan",
            price_cents=99900,
            interval="year"
        )

        assert result["success"] is True
        assert result["interval"] == "year"


# =============================================================================
# Tests for list_plans()
# =============================================================================

class TestListPlans:
    """Test plan listing functionality."""

    @patch('services.stripe_plans_service.get_db')
    def test_list_plans_active_only(self, mock_get_db):
        """Test listing active plans only."""
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.name = "test"
        mock_plan.display_name = "Test"
        mock_plan.price_cents = 2999
        mock_plan.billing_interval = "month"
        mock_plan.features = ["feature1"]
        mock_plan.stripe_product_id = "prod_1"
        mock_plan.stripe_price_id = "price_1"
        mock_plan.is_active = True
        mock_plan.sort_order = 1

        mock_db = MagicMock()
        mock_db.query().filter_by().order_by().all.return_value = [mock_plan]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.list_plans(active_only=True)

        assert len(result) == 1
        assert result[0]["name"] == "test"
        assert result[0]["price_display"] == "$29.99"

    @patch('services.stripe_plans_service.get_db')
    def test_list_plans_include_inactive(self, mock_get_db):
        """Test listing all plans including inactive."""
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.name = "inactive"
        mock_plan.display_name = "Inactive"
        mock_plan.price_cents = 1000
        mock_plan.billing_interval = "month"
        mock_plan.features = []
        mock_plan.stripe_product_id = "prod_1"
        mock_plan.stripe_price_id = "price_1"
        mock_plan.is_active = False
        mock_plan.sort_order = 1

        mock_db = MagicMock()
        mock_db.query().order_by().all.return_value = [mock_plan]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.list_plans(active_only=False)

        assert len(result) == 1
        assert result[0]["is_active"] is False

    @patch('services.stripe_plans_service.get_db')
    def test_list_plans_empty(self, mock_get_db):
        """Test listing when no plans exist."""
        mock_db = MagicMock()
        mock_db.query().filter_by().order_by().all.return_value = []
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.list_plans()

        assert result == []

    @patch('services.stripe_plans_service.get_db')
    def test_list_plans_handles_null_features(self, mock_get_db):
        """Test listing plans with null features."""
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.name = "test"
        mock_plan.display_name = "Test"
        mock_plan.price_cents = 1000
        mock_plan.billing_interval = "month"
        mock_plan.features = None  # NULL features
        mock_plan.stripe_product_id = "prod_1"
        mock_plan.stripe_price_id = "price_1"
        mock_plan.is_active = True
        mock_plan.sort_order = 1

        mock_db = MagicMock()
        mock_db.query().filter_by().order_by().all.return_value = [mock_plan]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.list_plans()

        assert result[0]["features"] == []

    @patch('services.stripe_plans_service.get_db')
    def test_list_plans_database_error(self, mock_get_db):
        """Test listing plans handles database errors."""
        mock_db = MagicMock()
        mock_db.query().filter_by().order_by().all.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.list_plans()

        assert result == []


# =============================================================================
# Tests for get_plan()
# =============================================================================

class TestGetPlan:
    """Test getting a single plan."""

    @patch('services.stripe_plans_service.get_db')
    def test_get_plan_success(self, mock_get_db):
        """Test getting a plan successfully."""
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.name = "test"
        mock_plan.display_name = "Test"
        mock_plan.price_cents = 5000
        mock_plan.billing_interval = "month"
        mock_plan.features = ["feature1", "feature2"]
        mock_plan.stripe_product_id = "prod_1"
        mock_plan.stripe_price_id = "price_1"
        mock_plan.is_active = True

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_plan
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_plan(1)

        assert result is not None
        assert result["id"] == 1
        assert result["price_display"] == "$50.00"

    @patch('services.stripe_plans_service.get_db')
    def test_get_plan_not_found(self, mock_get_db):
        """Test getting a non-existent plan."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_plan(999)

        assert result is None

    @patch('services.stripe_plans_service.get_db')
    def test_get_plan_handles_null_features(self, mock_get_db):
        """Test getting a plan with null features."""
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.name = "test"
        mock_plan.display_name = "Test"
        mock_plan.price_cents = 5000
        mock_plan.billing_interval = "month"
        mock_plan.features = None
        mock_plan.stripe_product_id = None
        mock_plan.stripe_price_id = None
        mock_plan.is_active = True

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_plan
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_plan(1)

        assert result["features"] == []


# =============================================================================
# Tests for create_checkout_session()
# =============================================================================

class TestCreateCheckoutSession:
    """Test checkout session creation."""

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    @patch.object(StripePlansService, '_get_or_create_stripe_customer')
    def test_create_checkout_session_success(self, mock_customer, mock_log, mock_stripe_prop, mock_get_db):
        """Test successful checkout session creation."""
        mock_customer.return_value = "cus_123"

        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"

        mock_stripe = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_stripe_prop.return_value = mock_stripe

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = "test@example.com"

        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.stripe_price_id = "price_123"
        mock_plan.name = "premium"

        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = [mock_client, mock_plan]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_checkout_session(
            client_id=1,
            plan_id=1,
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel"
        )

        assert result["success"] is True
        assert result["session_id"] == "cs_test_123"
        assert "checkout.stripe.com" in result["checkout_url"]

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, '_log_event')
    def test_create_checkout_session_client_not_found(self, mock_log, mock_get_db):
        """Test checkout session creation with missing client."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_checkout_session(1, 1, "url", "url")

        assert result["success"] is False
        assert "Client not found" in result["error"]

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, '_log_event')
    def test_create_checkout_session_plan_not_found(self, mock_log, mock_get_db):
        """Test checkout session creation with missing plan."""
        mock_client = MagicMock()
        mock_client.id = 1

        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = [mock_client, None]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_checkout_session(1, 999, "url", "url")

        assert result["success"] is False
        assert "Plan not found" in result["error"]

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, '_log_event')
    def test_create_checkout_session_plan_not_configured(self, mock_log, mock_get_db):
        """Test checkout session creation with unconfigured plan."""
        mock_client = MagicMock()
        mock_client.id = 1

        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.stripe_price_id = None  # Not configured

        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = [mock_client, mock_plan]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_checkout_session(1, 1, "url", "url")

        assert result["success"] is False
        assert "not configured" in result["error"]

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    @patch.object(StripePlansService, '_get_or_create_stripe_customer')
    def test_create_checkout_session_stripe_error(self, mock_customer, mock_log, mock_stripe_prop, mock_get_db):
        """Test checkout session creation handles Stripe errors."""
        mock_customer.return_value = "cus_123"

        mock_stripe = MagicMock()
        mock_stripe.checkout.Session.create.side_effect = Exception("Stripe error")
        mock_stripe_prop.return_value = mock_stripe

        mock_client = MagicMock()
        mock_client.id = 1

        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.stripe_price_id = "price_123"
        mock_plan.name = "test"

        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = [mock_client, mock_plan]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_checkout_session(1, 1, "url", "url")

        assert result["success"] is False
        assert "Stripe error" in result["error"]


# =============================================================================
# Tests for create_customer_portal_session()
# =============================================================================

class TestCreateCustomerPortalSession:
    """Test customer portal session creation."""

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_create_portal_session_success(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test successful portal session creation."""
        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/session/123"

        mock_stripe = MagicMock()
        mock_stripe.billing_portal.Session.create.return_value = mock_session
        mock_stripe_prop.return_value = mock_stripe

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.stripe_customer_id = "cus_123"

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_client
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_customer_portal_session(1, "https://app.com/return")

        assert result["success"] is True
        assert "billing.stripe.com" in result["portal_url"]

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, '_log_event')
    def test_create_portal_session_client_not_found(self, mock_log, mock_get_db):
        """Test portal session creation with missing client."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_customer_portal_session(999, "url")

        assert result["success"] is False
        assert "Client not found" in result["error"]

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, '_log_event')
    def test_create_portal_session_no_stripe_customer(self, mock_log, mock_get_db):
        """Test portal session creation with no Stripe customer ID."""
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.stripe_customer_id = None

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_client
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.create_customer_portal_session(1, "url")

        assert result["success"] is False
        assert "no Stripe customer ID" in result["error"]


# =============================================================================
# Tests for handle_webhook()
# =============================================================================

class TestHandleWebhook:
    """Test webhook handling."""

    @patch('services.stripe_plans_service.get_db')
    @patch('services.stripe_plans_service.get_webhook_secret')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    @patch.object(StripePlansService, '_handle_checkout_completed')
    def test_handle_webhook_checkout_completed(self, mock_handler, mock_log, mock_stripe_prop, mock_webhook_secret, mock_get_db):
        """Test handling checkout.session.completed webhook."""
        mock_webhook_secret.return_value = "whsec_test"
        mock_handler.return_value = {"success": True, "event_type": "checkout.session.completed"}

        mock_event = MagicMock()
        mock_event.type = "checkout.session.completed"
        mock_event.id = "evt_123"
        mock_event.data.object = MagicMock()

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = mock_event
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.handle_webhook(b'{}', 'sig_123')

        assert result["success"] is True
        mock_handler.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    @patch('services.stripe_plans_service.get_webhook_secret')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    @patch.object(StripePlansService, '_handle_subscription_created')
    def test_handle_webhook_subscription_created(self, mock_handler, mock_log, mock_stripe_prop, mock_webhook_secret, mock_get_db):
        """Test handling customer.subscription.created webhook."""
        mock_webhook_secret.return_value = "whsec_test"
        mock_handler.return_value = {"success": True, "event_type": "customer.subscription.created"}

        mock_event = MagicMock()
        mock_event.type = "customer.subscription.created"
        mock_event.id = "evt_123"
        mock_event.data.object = MagicMock()

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = mock_event
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.handle_webhook(b'{}', 'sig_123')

        assert result["success"] is True
        mock_handler.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    @patch('services.stripe_plans_service.get_webhook_secret')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    @patch.object(StripePlansService, '_handle_subscription_updated')
    def test_handle_webhook_subscription_updated(self, mock_handler, mock_log, mock_stripe_prop, mock_webhook_secret, mock_get_db):
        """Test handling customer.subscription.updated webhook."""
        mock_webhook_secret.return_value = "whsec_test"
        mock_handler.return_value = {"success": True}

        mock_event = MagicMock()
        mock_event.type = "customer.subscription.updated"
        mock_event.id = "evt_123"
        mock_event.data.object = MagicMock()

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = mock_event
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.handle_webhook(b'{}', 'sig_123')

        mock_handler.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    @patch('services.stripe_plans_service.get_webhook_secret')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    @patch.object(StripePlansService, '_handle_subscription_deleted')
    def test_handle_webhook_subscription_deleted(self, mock_handler, mock_log, mock_stripe_prop, mock_webhook_secret, mock_get_db):
        """Test handling customer.subscription.deleted webhook."""
        mock_webhook_secret.return_value = "whsec_test"
        mock_handler.return_value = {"success": True}

        mock_event = MagicMock()
        mock_event.type = "customer.subscription.deleted"
        mock_event.id = "evt_123"
        mock_event.data.object = MagicMock()

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = mock_event
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.handle_webhook(b'{}', 'sig_123')

        mock_handler.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    @patch('services.stripe_plans_service.get_webhook_secret')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    @patch.object(StripePlansService, '_handle_invoice_paid')
    def test_handle_webhook_invoice_paid(self, mock_handler, mock_log, mock_stripe_prop, mock_webhook_secret, mock_get_db):
        """Test handling invoice.paid webhook."""
        mock_webhook_secret.return_value = "whsec_test"
        mock_handler.return_value = {"success": True}

        mock_event = MagicMock()
        mock_event.type = "invoice.paid"
        mock_event.id = "evt_123"
        mock_event.data.object = MagicMock()

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = mock_event
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.handle_webhook(b'{}', 'sig_123')

        mock_handler.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    @patch('services.stripe_plans_service.get_webhook_secret')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    @patch.object(StripePlansService, '_handle_invoice_failed')
    def test_handle_webhook_invoice_failed(self, mock_handler, mock_log, mock_stripe_prop, mock_webhook_secret, mock_get_db):
        """Test handling invoice.payment_failed webhook."""
        mock_webhook_secret.return_value = "whsec_test"
        mock_handler.return_value = {"success": True}

        mock_event = MagicMock()
        mock_event.type = "invoice.payment_failed"
        mock_event.id = "evt_123"
        mock_event.data.object = MagicMock()

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = mock_event
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.handle_webhook(b'{}', 'sig_123')

        mock_handler.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    @patch('services.stripe_plans_service.get_webhook_secret')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_handle_webhook_unhandled_event(self, mock_log, mock_stripe_prop, mock_webhook_secret, mock_get_db):
        """Test handling unrecognized webhook event."""
        mock_webhook_secret.return_value = "whsec_test"

        mock_event = MagicMock()
        mock_event.type = "some.unknown.event"
        mock_event.id = "evt_123"
        mock_event.data.object = MagicMock()

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = mock_event
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.handle_webhook(b'{}', 'sig_123')

        assert result["success"] is True
        assert result["data"]["handled"] is False

    @patch('services.stripe_plans_service.get_db')
    @patch('services.stripe_plans_service.get_webhook_secret')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    def test_handle_webhook_invalid_signature(self, mock_stripe_prop, mock_webhook_secret, mock_get_db):
        """Test handling webhook with invalid signature."""
        mock_webhook_secret.return_value = "whsec_test"

        mock_stripe = MagicMock()
        mock_stripe.error.SignatureVerificationError = Exception
        mock_stripe.Webhook.construct_event.side_effect = mock_stripe.error.SignatureVerificationError("Bad sig")
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.handle_webhook(b'{}', 'bad_sig')

        assert result["success"] is False
        assert "Invalid signature" in result["error"]

    @patch('services.stripe_plans_service.get_db')
    @patch('services.stripe_plans_service.get_webhook_secret')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_handle_webhook_no_secret(self, mock_log, mock_stripe_prop, mock_webhook_secret, mock_get_db):
        """Test handling webhook without secret (uses Event.construct_from)."""
        mock_webhook_secret.return_value = None  # No secret

        mock_event = MagicMock()
        mock_event.type = "some.event"
        mock_event.id = "evt_123"
        mock_event.data.object = MagicMock()

        mock_stripe = MagicMock()
        mock_stripe.Event.construct_from.return_value = mock_event
        mock_stripe.api_key = "sk_test"
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        payload = json.dumps({"type": "some.event"}).encode()
        result = service.handle_webhook(payload, 'sig')

        assert result["success"] is True


# =============================================================================
# Tests for webhook handlers
# =============================================================================

class TestWebhookHandlers:
    """Test individual webhook handlers."""

    def test_handle_checkout_completed_success(self):
        """Test checkout completed handler creates subscription."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = [None, MagicMock()]  # No sub, client exists

        mock_session = MagicMock()
        mock_session.metadata = {"client_id": "1", "plan_id": "2"}
        mock_session.customer = "cus_123"
        mock_session.subscription = "sub_456"

        service = StripePlansService()
        result = service._handle_checkout_completed(mock_db, mock_session)

        assert result["success"] is True
        assert result["data"]["handled"] is True
        mock_db.add.assert_called_once()

    def test_handle_checkout_completed_updates_existing(self):
        """Test checkout completed handler updates existing subscription."""
        mock_sub = MagicMock()
        mock_client = MagicMock()

        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = [mock_sub, mock_client]

        mock_session = MagicMock()
        mock_session.metadata = {"client_id": "1", "plan_id": "2"}
        mock_session.customer = "cus_123"
        mock_session.subscription = "sub_456"

        service = StripePlansService()
        result = service._handle_checkout_completed(mock_db, mock_session)

        assert result["success"] is True
        assert mock_sub.status == "active"

    def test_handle_checkout_completed_no_client_id(self):
        """Test checkout completed handler with missing client_id."""
        mock_db = MagicMock()

        mock_session = MagicMock()
        mock_session.metadata = {}

        service = StripePlansService()
        result = service._handle_checkout_completed(mock_db, mock_session)

        assert result["success"] is True
        assert result["data"]["handled"] is False

    def test_handle_subscription_created_success(self):
        """Test subscription created handler."""
        mock_client = MagicMock()
        mock_client.id = 1

        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = [mock_client, None]

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.customer = "cus_123"
        mock_subscription.status = "active"
        mock_subscription.current_period_start = 1700000000
        mock_subscription.current_period_end = 1702592000

        service = StripePlansService()
        result = service._handle_subscription_created(mock_db, mock_subscription)

        assert result["success"] is True
        assert result["data"]["handled"] is True

    def test_handle_subscription_created_client_not_found(self):
        """Test subscription created handler with missing client."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None

        mock_subscription = MagicMock()
        mock_subscription.customer = "cus_unknown"

        service = StripePlansService()
        result = service._handle_subscription_created(mock_db, mock_subscription)

        assert result["data"]["handled"] is False

    def test_handle_subscription_updated_success(self):
        """Test subscription updated handler."""
        mock_sub = MagicMock()

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_sub

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"
        mock_subscription.status = "active"
        mock_subscription.current_period_start = 1700000000
        mock_subscription.current_period_end = 1702592000
        mock_subscription.cancel_at_period_end = False

        service = StripePlansService()
        result = service._handle_subscription_updated(mock_db, mock_subscription)

        assert result["success"] is True
        assert mock_sub.status == "active"

    def test_handle_subscription_updated_not_found(self):
        """Test subscription updated handler with missing subscription."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_unknown"

        service = StripePlansService()
        result = service._handle_subscription_updated(mock_db, mock_subscription)

        assert result["data"]["handled"] is False

    def test_handle_subscription_deleted_success(self):
        """Test subscription deleted handler."""
        mock_sub = MagicMock()
        mock_sub.client_id = 1
        mock_client = MagicMock()

        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = [mock_sub, mock_client]

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_123"

        service = StripePlansService()
        result = service._handle_subscription_deleted(mock_db, mock_subscription)

        assert result["success"] is True
        assert mock_sub.status == "canceled"
        assert mock_client.payment_status == "canceled"

    def test_handle_invoice_paid_success(self):
        """Test invoice paid handler."""
        mock_sub = MagicMock()
        mock_sub.amount_paid_cents = 5000

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_sub

        mock_invoice = MagicMock()
        mock_invoice.subscription = "sub_123"
        mock_invoice.amount_paid = 2999

        service = StripePlansService()
        result = service._handle_invoice_paid(mock_db, mock_invoice)

        assert result["success"] is True
        assert mock_sub.amount_paid_cents == 7999

    def test_handle_invoice_paid_no_subscription(self):
        """Test invoice paid handler with no subscription."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None

        mock_invoice = MagicMock()
        mock_invoice.subscription = "sub_unknown"
        mock_invoice.amount_paid = 2999

        service = StripePlansService()
        result = service._handle_invoice_paid(mock_db, mock_invoice)

        assert result["success"] is True

    def test_handle_invoice_failed_success(self):
        """Test invoice failed handler."""
        mock_sub = MagicMock()

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_sub

        mock_invoice = MagicMock()
        mock_invoice.subscription = "sub_123"

        service = StripePlansService()
        result = service._handle_invoice_failed(mock_db, mock_invoice)

        assert result["success"] is True
        assert mock_sub.status == "past_due"


# =============================================================================
# Tests for get_subscription_status()
# =============================================================================

class TestGetSubscriptionStatus:
    """Test subscription status retrieval."""

    @patch('services.stripe_plans_service.get_db')
    def test_get_subscription_status_success(self, mock_get_db):
        """Test getting subscription status successfully."""
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.name = "premium"
        mock_plan.display_name = "Premium"
        mock_plan.price_cents = 9900

        mock_sub = MagicMock()
        mock_sub.plan_id = 1
        mock_sub.status = "active"
        mock_sub.stripe_subscription_id = "sub_123"
        mock_sub.current_period_start = datetime(2024, 1, 1)
        mock_sub.current_period_end = datetime(2024, 2, 1)
        mock_sub.next_payment_date = datetime(2024, 2, 1)
        mock_sub.cancel_at_period_end = False
        mock_sub.amount_paid_cents = 9900

        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = [mock_sub, mock_plan]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_subscription_status(1)

        assert result["success"] is True
        assert result["has_subscription"] is True
        assert result["status"] == "active"
        assert result["plan"]["name"] == "premium"

    @patch('services.stripe_plans_service.get_db')
    def test_get_subscription_status_no_subscription(self, mock_get_db):
        """Test getting status when no subscription exists."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_subscription_status(1)

        assert result["success"] is True
        assert result["has_subscription"] is False
        assert result["status"] == "none"

    @patch('services.stripe_plans_service.get_db')
    def test_get_subscription_status_no_plan(self, mock_get_db):
        """Test getting status when plan is missing."""
        mock_sub = MagicMock()
        mock_sub.plan_id = None
        mock_sub.status = "active"
        mock_sub.stripe_subscription_id = "sub_123"
        mock_sub.current_period_start = None
        mock_sub.current_period_end = None
        mock_sub.next_payment_date = None
        mock_sub.cancel_at_period_end = False
        mock_sub.amount_paid_cents = 0

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_sub
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_subscription_status(1)

        assert result["success"] is True
        assert result["plan"] is None

    @patch('services.stripe_plans_service.get_db')
    def test_get_subscription_status_error(self, mock_get_db):
        """Test getting status handles errors."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_subscription_status(1)

        assert result["success"] is False
        assert "DB error" in result["error"]


# =============================================================================
# Tests for cancel_subscription()
# =============================================================================

class TestCancelSubscription:
    """Test subscription cancellation."""

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_cancel_subscription_at_period_end(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test canceling subscription at period end."""
        mock_stripe = MagicMock()
        mock_stripe_prop.return_value = mock_stripe

        mock_sub = MagicMock()
        mock_sub.stripe_subscription_id = "sub_123"

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_sub
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.cancel_subscription(1, at_period_end=True)

        assert result is True
        mock_stripe.Subscription.modify.assert_called_once_with("sub_123", cancel_at_period_end=True)
        assert mock_sub.cancel_at_period_end is True

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_cancel_subscription_immediately(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test canceling subscription immediately."""
        mock_stripe = MagicMock()
        mock_stripe_prop.return_value = mock_stripe

        mock_sub = MagicMock()
        mock_sub.stripe_subscription_id = "sub_123"

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_sub
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.cancel_subscription(1, at_period_end=False)

        assert result is True
        mock_stripe.Subscription.delete.assert_called_once_with("sub_123")
        assert mock_sub.status == "canceled"

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, '_log_event')
    def test_cancel_subscription_not_found(self, mock_log, mock_get_db):
        """Test canceling non-existent subscription."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.cancel_subscription(999)

        assert result is False

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, '_log_event')
    def test_cancel_subscription_no_stripe_id(self, mock_log, mock_get_db):
        """Test canceling subscription without Stripe ID."""
        mock_sub = MagicMock()
        mock_sub.stripe_subscription_id = None

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_sub
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.cancel_subscription(1)

        assert result is False

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_cancel_subscription_stripe_error(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test canceling subscription handles Stripe errors."""
        mock_stripe = MagicMock()
        mock_stripe.Subscription.modify.side_effect = Exception("Stripe error")
        mock_stripe_prop.return_value = mock_stripe

        mock_sub = MagicMock()
        mock_sub.stripe_subscription_id = "sub_123"

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_sub
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.cancel_subscription(1)

        assert result is False


# =============================================================================
# Tests for update_plan()
# =============================================================================

class TestUpdatePlan:
    """Test plan update functionality."""

    @patch('services.stripe_plans_service.get_db')
    def test_update_plan_display_name(self, mock_get_db):
        """Test updating plan display name."""
        mock_plan = MagicMock()
        mock_plan.id = 1

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_plan
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.update_plan(1, display_name="New Name")

        assert result["success"] is True
        assert mock_plan.display_name == "New Name"

    @patch('services.stripe_plans_service.get_db')
    def test_update_plan_features(self, mock_get_db):
        """Test updating plan features."""
        mock_plan = MagicMock()
        mock_plan.id = 1

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_plan
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.update_plan(1, features=["New Feature 1", "New Feature 2"])

        assert result["success"] is True
        assert mock_plan.features == ["New Feature 1", "New Feature 2"]

    @patch('services.stripe_plans_service.get_db')
    def test_update_plan_is_active(self, mock_get_db):
        """Test updating plan active status."""
        mock_plan = MagicMock()
        mock_plan.id = 1

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_plan
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.update_plan(1, is_active=False)

        assert result["success"] is True
        assert mock_plan.is_active is False

    @patch('services.stripe_plans_service.get_db')
    def test_update_plan_not_found(self, mock_get_db):
        """Test updating non-existent plan."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.update_plan(999, display_name="Test")

        assert result["success"] is False
        assert "Plan not found" in result["error"]

    @patch('services.stripe_plans_service.get_db')
    def test_update_plan_error(self, mock_get_db):
        """Test updating plan handles errors."""
        mock_plan = MagicMock()

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_plan
        mock_db.commit.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.update_plan(1, display_name="Test")

        assert result["success"] is False
        mock_db.rollback.assert_called()


# =============================================================================
# Tests for get_subscription_stats()
# =============================================================================

class TestGetSubscriptionStats:
    """Test subscription statistics retrieval."""

    @patch('services.stripe_plans_service.get_db')
    def test_get_subscription_stats_success(self, mock_get_db):
        """Test getting subscription statistics."""
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.display_name = "Premium"
        mock_plan.price_cents = 9900

        mock_db = MagicMock()
        mock_db.query().count.return_value = 10
        mock_db.query().filter_by().count.side_effect = [5, 3, 2, 5]
        mock_db.query().scalar.return_value = 49500
        mock_db.query().filter_by().all.return_value = [mock_plan]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_subscription_stats()

        assert result["success"] is True
        assert "total_subscriptions" in result
        assert "active_subscriptions" in result
        assert "mrr_cents" in result

    @patch('services.stripe_plans_service.get_db')
    def test_get_subscription_stats_error(self, mock_get_db):
        """Test getting statistics handles errors."""
        mock_db = MagicMock()
        mock_db.query().count.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_subscription_stats()

        assert result["success"] is False


# =============================================================================
# Tests for get_active_subscriptions()
# =============================================================================

class TestGetActiveSubscriptions:
    """Test active subscription listing."""

    @patch('services.stripe_plans_service.get_db')
    def test_get_active_subscriptions_success(self, mock_get_db):
        """Test getting active subscriptions."""
        mock_sub = MagicMock()
        mock_sub.id = 1
        mock_sub.client_id = 10
        mock_sub.plan_id = 1
        mock_sub.status = "active"
        mock_sub.current_period_end = datetime(2024, 2, 1)
        mock_sub.cancel_at_period_end = False
        mock_sub.amount_paid_cents = 9900
        mock_sub.created_at = datetime(2024, 1, 1)

        mock_client = MagicMock()
        mock_client.name = "Test Client"
        mock_client.email = "test@example.com"

        mock_plan = MagicMock()
        mock_plan.display_name = "Premium"
        mock_plan.price_cents = 9900

        mock_db = MagicMock()
        mock_db.query().filter().order_by().limit().all.return_value = [mock_sub]
        mock_db.query().filter_by().first.side_effect = [mock_client, mock_plan]
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_active_subscriptions(limit=10)

        assert len(result) == 1
        assert result[0]["client_name"] == "Test Client"
        assert result[0]["status"] == "active"

    @patch('services.stripe_plans_service.get_db')
    def test_get_active_subscriptions_empty(self, mock_get_db):
        """Test getting active subscriptions when none exist."""
        mock_db = MagicMock()
        mock_db.query().filter().order_by().limit().all.return_value = []
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_active_subscriptions()

        assert result == []

    @patch('services.stripe_plans_service.get_db')
    def test_get_active_subscriptions_error(self, mock_get_db):
        """Test getting active subscriptions handles errors."""
        mock_db = MagicMock()
        mock_db.query().filter().order_by().limit().all.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.get_active_subscriptions()

        assert result == []


# =============================================================================
# Tests for initialize_default_plans()
# =============================================================================

class TestInitializeDefaultPlans:
    """Test default plan initialization."""

    @patch.object(StripePlansService, 'create_plan')
    @patch('services.stripe_plans_service.get_db')
    def test_initialize_default_plans_creates_new(self, mock_get_db, mock_create):
        """Test initializing default plans creates new plans."""
        mock_create.return_value = {"success": True}

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.initialize_default_plans()

        assert result["success"] is True
        assert mock_create.call_count == 3

    @patch.object(StripePlansService, 'create_plan')
    @patch('services.stripe_plans_service.get_db')
    def test_initialize_default_plans_skips_existing(self, mock_get_db, mock_create):
        """Test initializing default plans skips existing configured plans."""
        mock_existing = MagicMock()
        mock_existing.id = 1
        mock_existing.stripe_price_id = "price_existing"

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_existing
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        result = service.initialize_default_plans()

        assert result["success"] is True
        assert all(p["status"] == "exists" for p in result["plans"])
        mock_create.assert_not_called()


# =============================================================================
# Tests for Helper Methods
# =============================================================================

class TestHelperMethods:
    """Test helper methods."""

    @patch('services.stripe_plans_service.get_db')
    def test_get_integration_id_creates_new(self, mock_get_db):
        """Test _get_integration_id creates new integration."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None

        service = StripePlansService()
        result = service._get_integration_id(mock_db)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    def test_get_integration_id_returns_existing(self, mock_get_db):
        """Test _get_integration_id returns existing integration."""
        mock_integration = MagicMock()
        mock_integration.id = 5

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_integration

        service = StripePlansService()
        result = service._get_integration_id(mock_db)

        assert result == 5
        mock_db.add.assert_not_called()

    @patch('services.stripe_plans_service.get_db')
    def test_get_integration_id_caches_result(self, mock_get_db):
        """Test _get_integration_id caches the result."""
        mock_integration = MagicMock()
        mock_integration.id = 5

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_integration

        service = StripePlansService()
        service._get_integration_id(mock_db)
        service._get_integration_id(mock_db)

        # Should only query once
        assert mock_db.query().filter_by().first.call_count == 1

    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    def test_get_or_create_stripe_customer_existing(self, mock_stripe_prop):
        """Test _get_or_create_stripe_customer returns existing customer."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.stripe_customer_id = "cus_existing"

        service = StripePlansService()
        result = service._get_or_create_stripe_customer(mock_db, mock_client)

        assert result == "cus_existing"

    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    def test_get_or_create_stripe_customer_creates_new(self, mock_stripe_prop):
        """Test _get_or_create_stripe_customer creates new customer."""
        mock_stripe = MagicMock()
        mock_customer = MagicMock()
        mock_customer.id = "cus_new"
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = "test@example.com"
        mock_client.name = "Test Client"
        mock_client.stripe_customer_id = None

        service = StripePlansService()
        result = service._get_or_create_stripe_customer(mock_db, mock_client)

        assert result == "cus_new"
        assert mock_client.stripe_customer_id == "cus_new"
        mock_db.commit.assert_called_once()


# =============================================================================
# Tests for Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, '_get_integration_id')
    def test_log_event_handles_error(self, mock_integration, mock_get_db):
        """Test _log_event handles errors gracefully."""
        mock_integration.side_effect = Exception("Integration error")

        mock_db = MagicMock()

        service = StripePlansService()
        # Should not raise
        service._log_event(mock_db, "test_event", {"data": "test"})

    @patch('services.stripe_plans_service.get_db')
    def test_get_plan_closes_session(self, mock_get_db):
        """Test get_plan closes database session."""
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.name = "test"
        mock_plan.display_name = "Test"
        mock_plan.price_cents = 1000
        mock_plan.billing_interval = "month"
        mock_plan.features = []
        mock_plan.stripe_product_id = None
        mock_plan.stripe_price_id = None
        mock_plan.is_active = True

        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_plan
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        service.get_plan(1)

        mock_db.close.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    def test_list_plans_closes_session(self, mock_get_db):
        """Test list_plans closes database session."""
        mock_db = MagicMock()
        mock_db.query().filter_by().order_by().all.return_value = []
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        service.list_plans()

        mock_db.close.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, 'stripe', new_callable=PropertyMock)
    @patch.object(StripePlansService, '_log_event')
    def test_create_plan_closes_session(self, mock_log, mock_stripe_prop, mock_get_db):
        """Test create_plan closes database session."""
        mock_stripe = MagicMock()
        mock_stripe.Product.create.side_effect = Exception("Error")
        mock_stripe_prop.return_value = mock_stripe

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        service.create_plan("test", 1000)

        mock_db.close.assert_called_once()

    @patch('services.stripe_plans_service.get_db')
    @patch.object(StripePlansService, '_log_event')
    def test_checkout_session_closes_session(self, mock_log, mock_get_db):
        """Test create_checkout_session closes database session."""
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_get_db.return_value = mock_db

        service = StripePlansService()
        service.create_checkout_session(1, 1, "url", "url")

        mock_db.close.assert_called_once()

    def test_stripe_property_lazy_loads(self):
        """Test stripe property is lazily loaded."""
        service = StripePlansService()
        assert service._stripe is None

        # Verify the stripe property exists on the class (without triggering the getter)
        assert isinstance(type(service).__dict__.get('stripe'), property)
