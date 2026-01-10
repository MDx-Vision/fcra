"""
Unit Tests for Stripe Client Module.
Tests for credential fetching, Stripe client initialization, checkout session creation,
webhook verification, and pricing tier configurations.
Covers all public functions with mocked Stripe API calls and environment variables.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stripe_client import (
    get_stripe_credentials,
    get_stripe_client,
    get_stripe_publishable_key,
    get_stripe_secret_key,
    get_webhook_secret,
    create_checkout_session,
    verify_webhook_signature,
    retrieve_checkout_session,
    PRICING_TIERS,
)


# =============================================================================
# Tests for PRICING_TIERS Configuration
# =============================================================================

class TestPricingTiers:
    """Test pricing tier configurations."""

    def test_pricing_tiers_exist(self):
        """Test that all pricing tiers are defined."""
        expected_tiers = ["free", "tier1", "tier2", "tier3", "tier4", "tier5"]
        for tier in expected_tiers:
            assert tier in PRICING_TIERS, f"Missing tier: {tier}"

    def test_free_tier_config(self):
        """Test free tier configuration."""
        free = PRICING_TIERS["free"]
        assert free["name"] == "Basic Analysis"
        assert free["amount"] == 0
        assert free["display"] == "FREE"
        assert "description" in free
        assert len(free["features"]) > 0

    def test_tier1_config(self):
        """Test tier1 configuration."""
        tier1 = PRICING_TIERS["tier1"]
        assert tier1["name"] == "Starter"
        assert tier1["amount"] == 30000
        assert tier1["display"] == "$300"
        assert len(tier1["features"]) > 0

    def test_tier2_config(self):
        """Test tier2 configuration."""
        tier2 = PRICING_TIERS["tier2"]
        assert tier2["name"] == "Standard"
        assert tier2["amount"] == 60000
        assert tier2["display"] == "$600"
        assert len(tier2["features"]) > 0

    def test_tier3_config(self):
        """Test tier3 configuration."""
        tier3 = PRICING_TIERS["tier3"]
        assert tier3["name"] == "Premium"
        assert tier3["amount"] == 90000
        assert tier3["display"] == "$900"
        assert len(tier3["features"]) > 0

    def test_tier4_config(self):
        """Test tier4 configuration."""
        tier4 = PRICING_TIERS["tier4"]
        assert tier4["name"] == "Professional"
        assert tier4["amount"] == 120000
        assert tier4["display"] == "$1,200"
        assert len(tier4["features"]) > 0

    def test_tier5_config(self):
        """Test tier5 configuration."""
        tier5 = PRICING_TIERS["tier5"]
        assert tier5["name"] == "Elite"
        assert tier5["amount"] == 150000
        assert tier5["display"] == "$1,500"
        assert len(tier5["features"]) > 0

    def test_all_tiers_have_required_fields(self):
        """Test that all tiers have required fields."""
        required_fields = ["name", "amount", "display", "description", "features"]
        for tier_key, tier in PRICING_TIERS.items():
            for field in required_fields:
                assert field in tier, f"Missing field {field} in tier {tier_key}"

    def test_tier_amounts_are_ascending(self):
        """Test that tier amounts increase from tier1 to tier5."""
        amounts = [
            PRICING_TIERS["tier1"]["amount"],
            PRICING_TIERS["tier2"]["amount"],
            PRICING_TIERS["tier3"]["amount"],
            PRICING_TIERS["tier4"]["amount"],
            PRICING_TIERS["tier5"]["amount"],
        ]
        for i in range(len(amounts) - 1):
            assert amounts[i] < amounts[i + 1], "Tier amounts should be ascending"

    def test_tier_features_are_lists(self):
        """Test that features are lists."""
        for tier_key, tier in PRICING_TIERS.items():
            assert isinstance(tier["features"], list), f"Features in {tier_key} should be a list"


# =============================================================================
# Tests for get_stripe_credentials()
# =============================================================================

class TestGetStripeCredentials:
    """Test Stripe credential fetching."""

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_success_development(self, mock_requests_get):
        """Test successful credential fetching in development."""
        # Reset the global cache
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "publishable": "pk_test_123",
                    "secret": "sk_test_456"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        publishable_key, secret_key = get_stripe_credentials()

        assert publishable_key == "pk_test_123"
        assert secret_key == "sk_test_456"
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        assert "development" in call_args.kwargs.get("params", {}).get("environment", "")

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '1'
    })
    def test_get_credentials_success_production(self, mock_requests_get):
        """Test successful credential fetching in production."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "publishable": "pk_live_123",
                    "secret": "sk_live_456"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        publishable_key, secret_key = get_stripe_credentials()

        assert publishable_key == "pk_live_123"
        assert secret_key == "sk_live_456"
        call_args = mock_requests_get.call_args
        assert "production" in call_args.kwargs.get("params", {}).get("environment", "")

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'WEB_REPL_RENEWAL': 'test_web_repl_token',
        'REPLIT_DEPLOYMENT': '0'
    }, clear=True)
    def test_get_credentials_uses_web_repl_renewal(self, mock_requests_get):
        """Test credential fetching uses WEB_REPL_RENEWAL when REPL_IDENTITY is missing."""
        import services.stripe_client as sc
        sc._connection_settings = None

        # Remove REPL_IDENTITY from environ if it exists
        os.environ.pop('REPL_IDENTITY', None)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "publishable": "pk_test_123",
                    "secret": "sk_test_456"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        publishable_key, secret_key = get_stripe_credentials()

        assert publishable_key == "pk_test_123"
        assert secret_key == "sk_test_456"
        call_args = mock_requests_get.call_args
        headers = call_args.kwargs.get("headers", {})
        assert "depl" in headers.get("X_REPLIT_TOKEN", "")

    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
    }, clear=True)
    def test_get_credentials_no_token_raises_error(self):
        """Test credential fetching raises error when no token found."""
        import services.stripe_client as sc
        sc._connection_settings = None

        os.environ.pop('REPL_IDENTITY', None)
        os.environ.pop('WEB_REPL_RENEWAL', None)

        with pytest.raises(ValueError) as exc_info:
            get_stripe_credentials()
        assert "No REPL_IDENTITY or WEB_REPL_RENEWAL token found" in str(exc_info.value)

    @patch.dict(os.environ, {
        'REPL_IDENTITY': 'test_identity_token',
    }, clear=True)
    def test_get_credentials_no_hostname_raises_error(self):
        """Test credential fetching raises error when hostname not found."""
        import services.stripe_client as sc
        sc._connection_settings = None

        os.environ.pop('REPLIT_CONNECTORS_HOSTNAME', None)

        with pytest.raises(ValueError) as exc_info:
            get_stripe_credentials()
        assert "REPLIT_CONNECTORS_HOSTNAME not found" in str(exc_info.value)

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_empty_items_raises_error(self, mock_requests_get):
        """Test credential fetching raises error when items are empty."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_requests_get.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            get_stripe_credentials()
        assert "connection not found" in str(exc_info.value)

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_no_items_key_raises_error(self, mock_requests_get):
        """Test credential fetching raises error when items key is missing."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_requests_get.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            get_stripe_credentials()
        assert "connection not found" in str(exc_info.value)

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_missing_publishable_key_raises_error(self, mock_requests_get):
        """Test credential fetching raises error when publishable key is missing."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "secret": "sk_test_456"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            get_stripe_credentials()
        assert "credentials incomplete" in str(exc_info.value)

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_missing_secret_key_raises_error(self, mock_requests_get):
        """Test credential fetching raises error when secret key is missing."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "publishable": "pk_test_123"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            get_stripe_credentials()
        assert "credentials incomplete" in str(exc_info.value)

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_correct_url_formation(self, mock_requests_get):
        """Test credential fetching forms correct URL."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "publishable": "pk_test_123",
                    "secret": "sk_test_456"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        get_stripe_credentials()

        call_args = mock_requests_get.call_args
        url = call_args.args[0] if call_args.args else call_args.kwargs.get("url", "")
        assert "https://connectors.example.com/api/v2/connection" == url

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_correct_params(self, mock_requests_get):
        """Test credential fetching sends correct parameters."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "publishable": "pk_test_123",
                    "secret": "sk_test_456"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        get_stripe_credentials()

        call_args = mock_requests_get.call_args
        params = call_args.kwargs.get("params", {})
        assert params["include_secrets"] == "true"
        assert params["connector_names"] == "stripe"
        assert "environment" in params


# =============================================================================
# Tests for get_stripe_client()
# =============================================================================

class TestGetStripeClient:
    """Test Stripe client initialization."""

    @patch('services.stripe_client.get_stripe_credentials')
    @patch('services.stripe_client.stripe')
    def test_get_stripe_client_sets_api_key(self, mock_stripe, mock_credentials):
        """Test get_stripe_client sets the API key."""
        mock_credentials.return_value = ("pk_test_123", "sk_test_456")

        result = get_stripe_client()

        assert mock_stripe.api_key == "sk_test_456"
        assert result is mock_stripe

    @patch('services.stripe_client.get_stripe_credentials')
    @patch('services.stripe_client.stripe')
    def test_get_stripe_client_returns_stripe_module(self, mock_stripe, mock_credentials):
        """Test get_stripe_client returns the stripe module."""
        mock_credentials.return_value = ("pk_test_123", "sk_test_456")

        result = get_stripe_client()

        assert result is mock_stripe


# =============================================================================
# Tests for get_stripe_publishable_key()
# =============================================================================

class TestGetStripePublishableKey:
    """Test Stripe publishable key retrieval."""

    @patch('services.stripe_client.get_stripe_credentials')
    def test_get_publishable_key_success(self, mock_credentials):
        """Test successful publishable key retrieval."""
        mock_credentials.return_value = ("pk_test_123", "sk_test_456")

        result = get_stripe_publishable_key()

        assert result == "pk_test_123"

    @patch('services.stripe_client.get_stripe_credentials')
    def test_get_publishable_key_calls_credentials(self, mock_credentials):
        """Test publishable key retrieval calls get_stripe_credentials."""
        mock_credentials.return_value = ("pk_test_123", "sk_test_456")

        get_stripe_publishable_key()

        mock_credentials.assert_called_once()


# =============================================================================
# Tests for get_stripe_secret_key()
# =============================================================================

class TestGetStripeSecretKey:
    """Test Stripe secret key retrieval."""

    @patch('services.stripe_client.get_stripe_credentials')
    def test_get_secret_key_success(self, mock_credentials):
        """Test successful secret key retrieval."""
        mock_credentials.return_value = ("pk_test_123", "sk_test_456")

        result = get_stripe_secret_key()

        assert result == "sk_test_456"

    @patch('services.stripe_client.get_stripe_credentials')
    def test_get_secret_key_calls_credentials(self, mock_credentials):
        """Test secret key retrieval calls get_stripe_credentials."""
        mock_credentials.return_value = ("pk_test_123", "sk_test_456")

        get_stripe_secret_key()

        mock_credentials.assert_called_once()


# =============================================================================
# Tests for get_webhook_secret()
# =============================================================================

class TestGetWebhookSecret:
    """Test webhook secret retrieval."""

    @patch.dict(os.environ, {'STRIPE_WEBHOOK_SECRET': 'whsec_test123'})
    def test_get_webhook_secret_success(self):
        """Test successful webhook secret retrieval."""
        result = get_webhook_secret()
        assert result == "whsec_test123"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_webhook_secret_returns_none_when_not_set(self):
        """Test webhook secret returns None when not set."""
        os.environ.pop('STRIPE_WEBHOOK_SECRET', None)
        result = get_webhook_secret()
        assert result is None


# =============================================================================
# Tests for create_checkout_session()
# =============================================================================

class TestCreateCheckoutSession:
    """Test checkout session creation."""

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_success(self, mock_get_client):
        """Test successful checkout session creation."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        result = create_checkout_session(
            draft_id="draft_abc123",
            tier_key="tier1",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )

        assert result.id == "cs_test_123"
        mock_stripe.checkout.Session.create.assert_called_once()

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_with_email(self, mock_get_client):
        """Test checkout session creation with customer email."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        create_checkout_session(
            draft_id="draft_abc123",
            tier_key="tier1",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            customer_email="test@example.com"
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert call_kwargs["customer_email"] == "test@example.com"

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_without_email(self, mock_get_client):
        """Test checkout session creation without customer email."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        create_checkout_session(
            draft_id="draft_abc123",
            tier_key="tier1",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert "customer_email" not in call_kwargs

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_invalid_tier_raises_error(self, mock_get_client):
        """Test checkout session creation raises error for invalid tier."""
        mock_stripe = MagicMock()
        mock_get_client.return_value = mock_stripe

        with pytest.raises(ValueError) as exc_info:
            create_checkout_session(
                draft_id="draft_abc123",
                tier_key="invalid_tier",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel"
            )
        assert "Invalid pricing tier" in str(exc_info.value)

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_correct_metadata(self, mock_get_client):
        """Test checkout session includes correct metadata."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        create_checkout_session(
            draft_id="draft_abc123",
            tier_key="tier2",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert call_kwargs["metadata"]["draft_id"] == "draft_abc123"
        assert call_kwargs["metadata"]["tier"] == "tier2"

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_correct_urls(self, mock_get_client):
        """Test checkout session includes correct URLs."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        create_checkout_session(
            draft_id="draft_abc123",
            tier_key="tier1",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert call_kwargs["success_url"] == "https://example.com/success"
        assert call_kwargs["cancel_url"] == "https://example.com/cancel"

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_correct_line_items(self, mock_get_client):
        """Test checkout session includes correct line items."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        create_checkout_session(
            draft_id="draft_abc123",
            tier_key="tier3",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        line_items = call_kwargs["line_items"]
        assert len(line_items) == 1
        assert line_items[0]["quantity"] == 1
        assert line_items[0]["price_data"]["currency"] == "usd"
        assert line_items[0]["price_data"]["unit_amount"] == PRICING_TIERS["tier3"]["amount"]

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_payment_mode(self, mock_get_client):
        """Test checkout session uses payment mode."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        create_checkout_session(
            draft_id="draft_abc123",
            tier_key="tier1",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert call_kwargs["mode"] == "payment"
        assert call_kwargs["payment_method_types"] == ["card"]

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_all_tiers(self, mock_get_client):
        """Test checkout session creation for all valid tiers."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        for tier_key in ["tier1", "tier2", "tier3", "tier4", "tier5"]:
            result = create_checkout_session(
                draft_id=f"draft_{tier_key}",
                tier_key=tier_key,
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel"
            )
            assert result is not None

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_free_tier_raises_error(self, mock_get_client):
        """Test checkout session for free tier (amount=0) still works."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        # Free tier should work but Stripe might reject 0 amount
        result = create_checkout_session(
            draft_id="draft_free",
            tier_key="free",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        assert result is not None

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_product_name_format(self, mock_get_client):
        """Test checkout session product name includes tier name."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        create_checkout_session(
            draft_id="draft_abc123",
            tier_key="tier4",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        product_name = call_kwargs["line_items"][0]["price_data"]["product_data"]["name"]
        assert "Professional" in product_name
        assert "FCRA Credit Restoration" in product_name


# =============================================================================
# Tests for verify_webhook_signature()
# =============================================================================

class TestVerifyWebhookSignature:
    """Test webhook signature verification."""

    @patch('services.stripe_client.get_webhook_secret')
    @patch('services.stripe_client.get_stripe_client')
    def test_verify_webhook_with_secret(self, mock_get_client, mock_get_secret):
        """Test webhook verification with signing secret."""
        mock_stripe = MagicMock()
        mock_event = MagicMock()
        mock_event.type = "checkout.session.completed"
        mock_stripe.Webhook.construct_event.return_value = mock_event
        mock_get_client.return_value = mock_stripe
        mock_get_secret.return_value = "whsec_test123"

        result = verify_webhook_signature(
            payload=b'{"type": "checkout.session.completed"}',
            sig_header="t=123,v1=abc123"
        )

        assert result is mock_event
        mock_stripe.Webhook.construct_event.assert_called_once()

    @patch('services.stripe_client.get_webhook_secret')
    @patch('services.stripe_client.get_stripe_client')
    def test_verify_webhook_with_custom_secret(self, mock_get_client, mock_get_secret):
        """Test webhook verification with custom signing secret."""
        mock_stripe = MagicMock()
        mock_event = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = mock_event
        mock_get_client.return_value = mock_stripe

        result = verify_webhook_signature(
            payload=b'{"type": "checkout.session.completed"}',
            sig_header="t=123,v1=abc123",
            webhook_secret="custom_secret"
        )

        assert result is mock_event
        mock_stripe.Webhook.construct_event.assert_called_with(
            b'{"type": "checkout.session.completed"}',
            "t=123,v1=abc123",
            "custom_secret"
        )
        mock_get_secret.assert_not_called()

    @patch('services.stripe_client.stripe')
    @patch('services.stripe_client.get_webhook_secret')
    @patch('services.stripe_client.get_stripe_client')
    def test_verify_webhook_without_secret(self, mock_get_client, mock_get_secret, mock_stripe_module):
        """Test webhook verification without signing secret."""
        mock_stripe = MagicMock()
        mock_stripe.api_key = "sk_test_123"
        mock_get_client.return_value = mock_stripe
        mock_get_secret.return_value = None

        mock_event = MagicMock()
        mock_stripe_module.Event.construct_from.return_value = mock_event

        payload = json.dumps({"type": "checkout.session.completed"}).encode()
        result = verify_webhook_signature(
            payload=payload,
            sig_header="t=123,v1=abc123"
        )

        assert result is mock_event
        mock_stripe_module.Event.construct_from.assert_called_once()

    @patch('services.stripe_client.get_webhook_secret')
    @patch('services.stripe_client.get_stripe_client')
    def test_verify_webhook_invalid_signature_raises_error(self, mock_get_client, mock_get_secret):
        """Test webhook verification raises error for invalid signature."""
        mock_stripe = MagicMock()
        mock_stripe.error.SignatureVerificationError = Exception
        mock_stripe.Webhook.construct_event.side_effect = mock_stripe.error.SignatureVerificationError("Invalid signature")
        mock_get_client.return_value = mock_stripe
        mock_get_secret.return_value = "whsec_test123"

        with pytest.raises(Exception) as exc_info:
            verify_webhook_signature(
                payload=b'{"type": "checkout.session.completed"}',
                sig_header="invalid_signature"
            )
        assert "Invalid signature" in str(exc_info.value)


# =============================================================================
# Tests for retrieve_checkout_session()
# =============================================================================

class TestRetrieveCheckoutSession:
    """Test checkout session retrieval."""

    @patch('services.stripe_client.get_stripe_client')
    def test_retrieve_checkout_session_success(self, mock_get_client):
        """Test successful checkout session retrieval."""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.payment_status = "paid"
        mock_stripe.checkout.Session.retrieve.return_value = mock_session
        mock_get_client.return_value = mock_stripe

        result = retrieve_checkout_session("cs_test_123")

        assert result.id == "cs_test_123"
        assert result.payment_status == "paid"
        mock_stripe.checkout.Session.retrieve.assert_called_once_with("cs_test_123")

    @patch('services.stripe_client.get_stripe_client')
    def test_retrieve_checkout_session_not_found(self, mock_get_client):
        """Test checkout session retrieval for non-existent session."""
        mock_stripe = MagicMock()
        mock_stripe.checkout.Session.retrieve.side_effect = Exception("No such checkout session")
        mock_get_client.return_value = mock_stripe

        with pytest.raises(Exception) as exc_info:
            retrieve_checkout_session("cs_nonexistent")
        assert "No such checkout session" in str(exc_info.value)


# =============================================================================
# Tests for Global State
# =============================================================================

class TestGlobalState:
    """Test global state management."""

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_connection_settings_cached(self, mock_requests_get):
        """Test that connection settings are cached globally."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "publishable": "pk_test_123",
                    "secret": "sk_test_456"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        # First call
        get_stripe_credentials()

        # Verify cache was set
        assert sc._connection_settings is not None
        assert sc._connection_settings.get("settings", {}).get("publishable") == "pk_test_123"


# =============================================================================
# Tests for Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @patch('services.stripe_client.get_stripe_client')
    def test_create_checkout_session_stripe_api_error(self, mock_get_client):
        """Test checkout session creation handles Stripe API errors."""
        mock_stripe = MagicMock()
        mock_stripe.checkout.Session.create.side_effect = Exception("Stripe API error")
        mock_get_client.return_value = mock_stripe

        with pytest.raises(Exception) as exc_info:
            create_checkout_session(
                draft_id="draft_abc123",
                tier_key="tier1",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel"
            )
        assert "Stripe API error" in str(exc_info.value)

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_request_error(self, mock_requests_get):
        """Test credential fetching handles request errors."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_requests_get.side_effect = Exception("Connection timeout")

        with pytest.raises(Exception) as exc_info:
            get_stripe_credentials()
        assert "Connection timeout" in str(exc_info.value)

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_json_decode_error(self, mock_requests_get):
        """Test credential fetching handles JSON decode errors."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_requests_get.return_value = mock_response

        with pytest.raises(json.JSONDecodeError):
            get_stripe_credentials()

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'test_identity_token',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_empty_settings(self, mock_requests_get):
        """Test credential fetching handles empty settings."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {}
            }]
        }
        mock_requests_get.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            get_stripe_credentials()
        assert "credentials incomplete" in str(exc_info.value)

    def test_pricing_tier_amounts_are_integers(self):
        """Test that all pricing tier amounts are integers."""
        for tier_key, tier in PRICING_TIERS.items():
            assert isinstance(tier["amount"], int), f"Amount in {tier_key} should be an integer"

    def test_pricing_tier_amounts_in_cents(self):
        """Test that pricing tier amounts appear to be in cents (not dollars)."""
        for tier_key, tier in PRICING_TIERS.items():
            if tier["amount"] > 0:
                # If it's a paid tier, amount should be > 100 (more than $1)
                assert tier["amount"] >= 100, f"Amount in {tier_key} should be in cents"


# =============================================================================
# Tests for Request Headers and Parameters
# =============================================================================

class TestRequestHeadersAndParams:
    """Test request headers and parameters formation."""

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'REPL_IDENTITY': 'my_repl_identity',
        'REPLIT_DEPLOYMENT': '0'
    })
    def test_get_credentials_repl_identity_header(self, mock_requests_get):
        """Test credential fetching includes correct REPL identity header."""
        import services.stripe_client as sc
        sc._connection_settings = None

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "publishable": "pk_test_123",
                    "secret": "sk_test_456"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        get_stripe_credentials()

        call_args = mock_requests_get.call_args
        headers = call_args.kwargs.get("headers", {})
        assert headers.get("X_REPLIT_TOKEN") == "repl my_repl_identity"
        assert headers.get("Accept") == "application/json"

    @patch('services.stripe_client.requests.get')
    @patch.dict(os.environ, {
        'REPLIT_CONNECTORS_HOSTNAME': 'connectors.example.com',
        'WEB_REPL_RENEWAL': 'my_web_repl_token',
        'REPLIT_DEPLOYMENT': '0'
    }, clear=True)
    def test_get_credentials_web_repl_renewal_header(self, mock_requests_get):
        """Test credential fetching includes correct WEB_REPL_RENEWAL header."""
        import services.stripe_client as sc
        sc._connection_settings = None

        os.environ.pop('REPL_IDENTITY', None)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{
                "settings": {
                    "publishable": "pk_test_123",
                    "secret": "sk_test_456"
                }
            }]
        }
        mock_requests_get.return_value = mock_response

        get_stripe_credentials()

        call_args = mock_requests_get.call_args
        headers = call_args.kwargs.get("headers", {})
        assert headers.get("X_REPLIT_TOKEN") == "depl my_web_repl_token"
