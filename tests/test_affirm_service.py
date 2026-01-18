"""
Unit tests for Affirm BNPL Service

Tests cover:
- Configuration validation
- Checkout creation
- Charge authorization
- Charge capture
- Charge void
- Refund processing
- Webhook handling
- Monthly payment calculations
"""

import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from services.affirm_service import (
    AFFIRM_PRODUCTION_URL,
    AFFIRM_SANDBOX_URL,
    AffirmError,
    AffirmService,
    get_affirm_service,
)


class TestAffirmServiceConfiguration:
    """Tests for service configuration and initialization."""

    def test_service_sandbox_url(self):
        """Test sandbox URL is used by default."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            assert service.base_url == AFFIRM_SANDBOX_URL

    def test_service_production_url(self):
        """Test production URL is used when configured."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "production"

            service = AffirmService()
            assert service.base_url == AFFIRM_PRODUCTION_URL

    def test_is_configured_returns_true(self):
        """Test is_configured returns True when keys are set."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            assert service.is_configured() is True

    def test_is_configured_returns_false_missing_public(self):
        """Test is_configured returns False when public key is missing."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = ""
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            assert service.is_configured() is False

    def test_is_configured_returns_false_missing_private(self):
        """Test is_configured returns False when private key is missing."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = ""
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            assert service.is_configured() is False


class TestAffirmServiceMakeRequest:
    """Tests for the internal _make_request method."""

    @patch("services.affirm_service.requests.request")
    def test_make_request_not_configured(self, mock_request):
        """Test _make_request raises error when not configured."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = ""
            mock_config.AFFIRM_PRIVATE_KEY = ""
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()

            with pytest.raises(AffirmError) as exc:
                service._make_request("GET", "/test")

            assert "not configured" in str(exc.value)

    @patch("services.affirm_service.requests.request")
    def test_make_request_success(self, mock_request):
        """Test _make_request handles successful response."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"success": True}
        mock_response.content = b'{"success": true}'
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service._make_request("GET", "/test")

            assert result == {"success": True}

    @patch("services.affirm_service.requests.request")
    def test_make_request_api_error(self, mock_request):
        """Test _make_request handles API error response."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.content = b'{"message": "Invalid request", "code": "invalid_request"}'
        mock_response.json.return_value = {"message": "Invalid request", "code": "invalid_request"}
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()

            with pytest.raises(AffirmError) as exc:
                service._make_request("GET", "/test")

            assert "Invalid request" in str(exc.value)
            assert exc.value.error_code == "invalid_request"


class TestCreateCheckout:
    """Tests for checkout creation."""

    @patch("services.affirm_service.requests.request")
    def test_create_checkout_success(self, mock_request):
        """Test successful checkout creation."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b'{}'
        mock_response.json.return_value = {
            "checkout_id": "checkout_123",
            "checkout_token": "token_abc",
            "redirect_url": "https://affirm.com/checkout/abc",
            "expires_at": "2026-01-19T00:00:00Z",
        }
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.create_checkout(
                client_id="123",
                amount_cents=49700,
                description="Credit Restoration - Round 1",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
                client_email="test@example.com",
                client_name="John Doe",
            )

            assert result["checkout_id"] == "checkout_123"
            assert result["checkout_token"] == "token_abc"
            assert "redirect_url" in result

    @patch("services.affirm_service.requests.request")
    def test_create_checkout_with_metadata(self, mock_request):
        """Test checkout creation with custom metadata."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b'{}'
        mock_response.json.return_value = {
            "checkout_id": "checkout_123",
            "checkout_token": "token_abc",
        }
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.create_checkout(
                client_id="456",
                amount_cents=29800,
                description="Round 2 Payment",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
                metadata={"round": 2, "custom_field": "value"},
            )

            # Verify request was made with metadata
            call_args = mock_request.call_args
            request_data = call_args[1]["json"]
            assert "456" in request_data["metadata"]["client_id"]


class TestAuthorizeCharge:
    """Tests for charge authorization."""

    @patch("services.affirm_service.requests.request")
    def test_authorize_charge_success(self, mock_request):
        """Test successful charge authorization."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b'{}'
        mock_response.json.return_value = {
            "id": "charge_abc123",
            "status": "authorized",
            "amount": 49700,
            "created": "2026-01-18T12:00:00Z",
            "order_id": "client_123",
        }
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.authorize_charge(
                checkout_token="token_abc",
                order_id="client_123"
            )

            assert result["charge_id"] == "charge_abc123"
            assert result["status"] == "authorized"
            assert result["amount"] == 49700


class TestCaptureCharge:
    """Tests for charge capture."""

    @patch("services.affirm_service.requests.request")
    def test_capture_charge_full(self, mock_request):
        """Test capturing full charge amount."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b'{}'
        mock_response.json.return_value = {
            "status": "captured",
            "amount": 49700,
        }
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.capture_charge("charge_abc123")

            assert result["status"] == "captured"
            assert result["charge_id"] == "charge_abc123"

    @patch("services.affirm_service.requests.request")
    def test_capture_charge_partial(self, mock_request):
        """Test capturing partial charge amount."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b'{}'
        mock_response.json.return_value = {
            "status": "captured",
            "amount": 25000,
        }
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.capture_charge("charge_abc123", amount_cents=25000)

            # Verify amount was passed in request
            call_args = mock_request.call_args
            assert call_args[1]["json"]["amount"] == 25000


class TestVoidCharge:
    """Tests for voiding charges."""

    @patch("services.affirm_service.requests.request")
    def test_void_charge_success(self, mock_request):
        """Test successful charge void."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b'{}'
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.void_charge("charge_abc123")

            assert result["status"] == "voided"
            assert result["charge_id"] == "charge_abc123"


class TestRefundCharge:
    """Tests for refunding charges."""

    @patch("services.affirm_service.requests.request")
    def test_refund_charge_full(self, mock_request):
        """Test full refund."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b'{}'
        mock_response.json.return_value = {
            "id": "refund_123",
            "amount": 49700,
        }
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.refund_charge("charge_abc123")

            assert result["status"] == "refunded"
            assert result["refund_id"] == "refund_123"

    @patch("services.affirm_service.requests.request")
    def test_refund_charge_partial(self, mock_request):
        """Test partial refund."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b'{}'
        mock_response.json.return_value = {
            "id": "refund_456",
            "amount": 10000,
        }
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.refund_charge("charge_abc123", amount_cents=10000)

            assert result["amount"] == 10000


class TestGetCharge:
    """Tests for getting charge details."""

    @patch("services.affirm_service.requests.request")
    def test_get_charge_success(self, mock_request):
        """Test getting charge details."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b'{}'
        mock_response.json.return_value = {
            "id": "charge_abc123",
            "status": "captured",
            "amount": 49700,
            "currency": "USD",
            "created": "2026-01-18T12:00:00Z",
            "order_id": "client_123",
            "events": [
                {"type": "authorized", "created": "2026-01-18T12:00:00Z"},
                {"type": "captured", "created": "2026-01-18T12:01:00Z"},
            ],
        }
        mock_request.return_value = mock_response

        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.get_charge("charge_abc123")

            assert result["charge_id"] == "charge_abc123"
            assert result["status"] == "captured"
            assert len(result["events"]) == 2


class TestWebhookSignatureVerification:
    """Tests for webhook signature verification."""

    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature verification."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_secret"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()

            payload = b'{"type": "charge.captured"}'
            expected_sig = hmac.new(
                b"test_secret",
                payload,
                hashlib.sha256
            ).hexdigest()

            assert service.verify_webhook_signature(payload, expected_sig) is True

    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature verification."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_secret"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()

            payload = b'{"type": "charge.captured"}'
            invalid_sig = "invalid_signature"

            assert service.verify_webhook_signature(payload, invalid_sig) is False

    def test_verify_webhook_signature_empty(self):
        """Test empty signature returns False."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_secret"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()

            payload = b'{"type": "charge.captured"}'
            assert service.verify_webhook_signature(payload, "") is False
            assert service.verify_webhook_signature(payload, None) is False


class TestWebhookHandling:
    """Tests for webhook event handling."""

    def test_handle_webhook_charge_created(self):
        """Test handling charge.created webhook."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.handle_webhook(
                "charge.created",
                {"id": "charge_123"}
            )

            assert result["status"] == "processed"
            assert result["event"] == "charge.created"
            assert result["action"] == "authorization_created"

    def test_handle_webhook_charge_captured(self):
        """Test handling charge.captured webhook."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.handle_webhook(
                "charge.captured",
                {"id": "charge_123"}
            )

            assert result["status"] == "processed"
            assert result["event"] == "charge.captured"
            assert result["action"] == "payment_confirmed"

    def test_handle_webhook_charge_voided(self):
        """Test handling charge.voided webhook."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.handle_webhook(
                "charge.voided",
                {"id": "charge_123"}
            )

            assert result["status"] == "processed"
            assert result["event"] == "charge.voided"
            assert result["action"] == "authorization_cancelled"

    def test_handle_webhook_charge_refunded(self):
        """Test handling charge.refunded webhook."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.handle_webhook(
                "charge.refunded",
                {"id": "charge_123"}
            )

            assert result["status"] == "processed"
            assert result["event"] == "charge.refunded"
            assert result["action"] == "refund_processed"

    def test_handle_webhook_charge_failed(self):
        """Test handling charge.failed webhook."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.handle_webhook(
                "charge.failed",
                {"id": "charge_123", "reason": "insufficient_funds"}
            )

            assert result["status"] == "processed"
            assert result["event"] == "charge.failed"
            assert result["action"] == "payment_failed"
            assert result["reason"] == "insufficient_funds"

    def test_handle_webhook_unknown_event(self):
        """Test handling unknown webhook event."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.handle_webhook(
                "unknown.event",
                {"id": "charge_123"}
            )

            assert result["status"] == "ignored"
            assert result["event_type"] == "unknown.event"


class TestMonthlyPaymentCalculation:
    """Tests for monthly payment estimation."""

    def test_get_monthly_payment_12_months(self):
        """Test 12-month payment calculation."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.get_monthly_payment(49700, 12)

            assert result["amount"] == 497.0
            assert result["months"] == 12
            assert result["promo_monthly"] == pytest.approx(41.42, rel=0.01)  # $497/12 = ~$41.42
            assert "estimated_monthly" in result
            assert "disclaimer" in result

    def test_get_monthly_payment_6_months(self):
        """Test 6-month payment calculation."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.get_monthly_payment(49700, 6)

            assert result["amount"] == 497.0
            assert result["months"] == 6
            assert result["promo_monthly"] == pytest.approx(82.83, rel=0.01)  # $497/6 = ~$82.83

    def test_get_monthly_payment_3_months(self):
        """Test 3-month payment calculation."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            service = AffirmService()
            result = service.get_monthly_payment(49700, 3)

            assert result["amount"] == 497.0
            assert result["months"] == 3
            assert result["promo_monthly"] == pytest.approx(165.67, rel=0.01)  # $497/3 = ~$165.67


class TestSingletonService:
    """Tests for singleton service access."""

    def test_get_affirm_service_returns_singleton(self):
        """Test that get_affirm_service returns the same instance."""
        with patch("services.affirm_service.config") as mock_config:
            mock_config.AFFIRM_PUBLIC_KEY = "test_public"
            mock_config.AFFIRM_PRIVATE_KEY = "test_private"
            mock_config.AFFIRM_ENVIRONMENT = "sandbox"

            # Reset singleton
            import services.affirm_service
            services.affirm_service._affirm_service = None

            service1 = get_affirm_service()
            service2 = get_affirm_service()

            assert service1 is service2


class TestAffirmError:
    """Tests for AffirmError exception."""

    def test_affirm_error_basic(self):
        """Test AffirmError with basic message."""
        error = AffirmError("Test error")
        assert str(error) == "Test error"
        assert error.error_code is None
        assert error.details == {}

    def test_affirm_error_with_code(self):
        """Test AffirmError with error code."""
        error = AffirmError("Invalid request", error_code="invalid_request")
        assert str(error) == "Invalid request"
        assert error.error_code == "invalid_request"

    def test_affirm_error_with_details(self):
        """Test AffirmError with details."""
        error = AffirmError(
            "Validation failed",
            error_code="validation_error",
            details={"field": "amount", "message": "Must be positive"}
        )
        assert error.details["field"] == "amount"
