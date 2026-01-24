"""
Affirm BNPL (Buy Now Pay Later) Integration Service

Allows clients to pay for credit restoration services over 3-12 months.
Merchant receives payment immediately, Affirm handles the risk.

Affirm Fee: ~6% + $0.30 per transaction
Example: $497 payment → Merchant receives ~$466.88

Benefits:
- Higher conversion rates (20-30% typical increase)
- Clients can afford services they couldn't pay upfront
- Affirm reports to Experian (helps clients build credit!)
- Immediate payment to merchant
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import requests

from services.config import config

logger = logging.getLogger(__name__)


# Affirm API endpoints
AFFIRM_SANDBOX_URL = "https://sandbox.affirm.com/api/v1"
AFFIRM_PRODUCTION_URL = "https://api.affirm.com/api/v1"


class AffirmError(Exception):
    """Base exception for Affirm-related errors."""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class AffirmService:
    """
    Service for handling Affirm BNPL payments.

    Affirm allows clients to pay over time (3, 6, or 12 months) while
    the merchant receives payment immediately minus the Affirm fee.
    """

    def __init__(self):
        """Initialize the Affirm service with API credentials."""
        self.public_key = config.AFFIRM_PUBLIC_KEY
        self.private_key = config.AFFIRM_PRIVATE_KEY
        self.environment = config.AFFIRM_ENVIRONMENT

        # Select API base URL
        if self.environment == "production":
            self.base_url = AFFIRM_PRODUCTION_URL
        else:
            self.base_url = AFFIRM_SANDBOX_URL

    def is_configured(self) -> bool:
        """Check if Affirm credentials are configured."""
        return bool(self.public_key and self.private_key)

    def _get_auth(self) -> tuple:
        """Get HTTP Basic Auth tuple for Affirm API."""
        return (self.public_key, self.private_key)

    def _make_request(
        self, method: str, endpoint: str, data: dict = None, params: dict = None
    ) -> dict:
        """
        Make an authenticated request to Affirm API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON as dict

        Raises:
            AffirmError: If the request fails
        """
        if not self.is_configured():
            raise AffirmError(
                "Affirm is not configured. Set AFFIRM_PUBLIC_KEY and AFFIRM_PRIVATE_KEY."
            )

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self._get_auth(),
                headers=headers,
                json=data,
                params=params,
                timeout=30,
            )

            # Log the request for debugging
            logger.info(f"Affirm API {method} {endpoint}: {response.status_code}")

            # Handle error responses
            if not response.ok:
                error_data = response.json() if response.content else {}
                error_message = error_data.get(
                    "message", f"HTTP {response.status_code}"
                )
                error_code = error_data.get("code", str(response.status_code))

                logger.error(f"Affirm API error: {error_message} (code: {error_code})")
                raise AffirmError(
                    message=error_message, error_code=error_code, details=error_data
                )

            return response.json() if response.content else {}

        except requests.RequestException as e:
            logger.error(f"Affirm API request failed: {str(e)}")
            raise AffirmError(f"Failed to connect to Affirm: {str(e)}")

    def create_checkout(
        self,
        client_id: str,
        amount_cents: int,
        description: str,
        success_url: str,
        cancel_url: str,
        client_email: str = None,
        client_name: str = None,
        client_phone: str = None,
        metadata: dict = None,
    ) -> dict:
        """
        Create an Affirm checkout session.

        This creates a checkout that the client will complete in Affirm's UI.
        After approval, Affirm redirects to success_url with a checkout_token.

        Args:
            client_id: Internal client ID for reference
            amount_cents: Total amount in cents (e.g., 49700 for $497.00)
            description: Product/service description
            success_url: URL to redirect after successful Affirm approval
            cancel_url: URL to redirect if client cancels
            client_email: Client's email address
            client_name: Client's full name
            client_phone: Client's phone number
            metadata: Additional metadata to store with the checkout

        Returns:
            Dict with checkout details including redirect_url
        """
        # Build the checkout request
        checkout_data = {
            "merchant": {
                "user_confirmation_url": success_url,
                "user_cancel_url": cancel_url,
            },
            "order_id": f"client_{client_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "total": amount_cents,
            "currency": "USD",
            "items": [
                {
                    "display_name": description,
                    "sku": f"FCRA-{client_id}",
                    "unit_price": amount_cents,
                    "qty": 1,
                }
            ],
            "metadata": metadata or {},
        }

        # Add client info if provided
        if client_email or client_name or client_phone:
            checkout_data["billing"] = {}
            if client_email:
                checkout_data["billing"]["email"] = client_email
            if client_name:
                # Try to split into first/last name
                name_parts = client_name.split(" ", 1)
                checkout_data["billing"]["name"] = {
                    "first": name_parts[0],
                    "last": name_parts[1] if len(name_parts) > 1 else "",
                }
            if client_phone:
                checkout_data["billing"]["phone_number"] = client_phone

        # Store client_id in metadata
        checkout_data["metadata"]["client_id"] = str(client_id)

        result = self._make_request("POST", "/checkout", data=checkout_data)

        logger.info(
            f"Created Affirm checkout for client {client_id}: {result.get('checkout_id')}"
        )

        return {
            "checkout_id": result.get("checkout_id"),
            "checkout_token": result.get("checkout_token"),
            "redirect_url": result.get("redirect_url"),
            "expires_at": result.get("expires_at"),
        }

    def authorize_charge(self, checkout_token: str, order_id: str = None) -> dict:
        """
        Authorize a charge after the client completes Affirm checkout.

        This is called after the client is redirected back from Affirm.
        The checkout_token comes from the redirect URL parameters.

        Args:
            checkout_token: Token from Affirm redirect (query param: checkout_token)
            order_id: Optional order ID to associate with the charge

        Returns:
            Dict with charge details including charge_id
        """
        data = {"checkout_token": checkout_token}
        if order_id:
            data["order_id"] = order_id

        result = self._make_request("POST", "/charges", data=data)

        charge_id = result.get("id")
        logger.info(f"Authorized Affirm charge: {charge_id}")

        return {
            "charge_id": charge_id,
            "status": result.get("status"),  # authorized
            "amount": result.get("amount"),
            "created_at": result.get("created"),
            "order_id": result.get("order_id"),
            "details": result.get("details", {}),
        }

    def capture_charge(self, charge_id: str, amount_cents: int = None) -> dict:
        """
        Capture an authorized charge.

        This finalizes the charge and initiates fund transfer to merchant.
        Can optionally capture a partial amount.

        Args:
            charge_id: The charge ID from authorize_charge
            amount_cents: Optional amount to capture (for partial captures)

        Returns:
            Dict with capture details
        """
        endpoint = f"/charges/{charge_id}/capture"
        data = {}
        if amount_cents is not None:
            data["amount"] = amount_cents

        result = self._make_request("POST", endpoint, data=data if data else None)

        logger.info(
            f"Captured Affirm charge {charge_id}: status={result.get('status')}"
        )

        return {
            "charge_id": charge_id,
            "status": result.get("status"),  # captured
            "amount": result.get("amount"),
            "captured_at": datetime.utcnow().isoformat(),
        }

    def void_charge(self, charge_id: str) -> dict:
        """
        Void an authorized charge before capture.

        Can only void charges that haven't been captured yet.

        Args:
            charge_id: The charge ID to void

        Returns:
            Dict with void status
        """
        endpoint = f"/charges/{charge_id}/void"
        result = self._make_request("POST", endpoint)

        logger.info(f"Voided Affirm charge {charge_id}")

        return {
            "charge_id": charge_id,
            "status": "voided",
            "voided_at": datetime.utcnow().isoformat(),
        }

    def refund_charge(self, charge_id: str, amount_cents: int = None) -> dict:
        """
        Refund a captured charge.

        Can refund full amount or partial amount.

        Args:
            charge_id: The charge ID to refund
            amount_cents: Amount to refund in cents (None = full refund)

        Returns:
            Dict with refund details
        """
        endpoint = f"/charges/{charge_id}/refund"
        data = {}
        if amount_cents is not None:
            data["amount"] = amount_cents

        result = self._make_request("POST", endpoint, data=data if data else None)

        logger.info(
            f"Refunded Affirm charge {charge_id}: amount={amount_cents or 'full'}"
        )

        return {
            "charge_id": charge_id,
            "refund_id": result.get("id"),
            "status": "refunded",
            "amount": result.get("amount"),
            "refunded_at": datetime.utcnow().isoformat(),
        }

    def get_charge(self, charge_id: str) -> dict:
        """
        Get details of an existing charge.

        Args:
            charge_id: The charge ID to look up

        Returns:
            Dict with full charge details
        """
        endpoint = f"/charges/{charge_id}"
        result = self._make_request("GET", endpoint)

        return {
            "charge_id": result.get("id"),
            "status": result.get("status"),
            "amount": result.get("amount"),
            "currency": result.get("currency"),
            "created_at": result.get("created"),
            "order_id": result.get("order_id"),
            "events": result.get("events", []),
            "details": result.get("details", {}),
        }

    def verify_webhook_signature(
        self, payload: bytes, signature: str, webhook_secret: str = None
    ) -> bool:
        """
        Verify an Affirm webhook signature.

        Args:
            payload: Raw webhook body bytes
            signature: X-Affirm-Signature header value
            webhook_secret: Webhook secret (if different from default)

        Returns:
            True if signature is valid
        """
        if not signature:
            return False

        # Compute expected signature
        secret = webhook_secret or self.private_key
        expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        # Compare signatures
        return hmac.compare_digest(expected_sig, signature)

    def handle_webhook(self, event_type: str, event_data: dict) -> dict:
        """
        Process an Affirm webhook event.

        Args:
            event_type: The webhook event type (e.g., charge.created)
            event_data: The event data payload

        Returns:
            Dict with processing result
        """
        charge_id = event_data.get("id") or event_data.get("charge_id")

        logger.info(f"Processing Affirm webhook: {event_type} for charge {charge_id}")

        # Map event types to handlers
        handlers = {
            "charge.created": self._handle_charge_created,
            "charge.captured": self._handle_charge_captured,
            "charge.voided": self._handle_charge_voided,
            "charge.refunded": self._handle_charge_refunded,
            "charge.failed": self._handle_charge_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(event_data)
        else:
            logger.warning(f"Unhandled Affirm webhook event type: {event_type}")
            return {"status": "ignored", "event_type": event_type}

    def _handle_charge_created(self, data: dict) -> dict:
        """Handle charge.created webhook event."""
        return {
            "status": "processed",
            "event": "charge.created",
            "charge_id": data.get("id"),
            "action": "authorization_created",
        }

    def _handle_charge_captured(self, data: dict) -> dict:
        """Handle charge.captured webhook event."""
        return {
            "status": "processed",
            "event": "charge.captured",
            "charge_id": data.get("id"),
            "action": "payment_confirmed",
        }

    def _handle_charge_voided(self, data: dict) -> dict:
        """Handle charge.voided webhook event."""
        return {
            "status": "processed",
            "event": "charge.voided",
            "charge_id": data.get("id"),
            "action": "authorization_cancelled",
        }

    def _handle_charge_refunded(self, data: dict) -> dict:
        """Handle charge.refunded webhook event."""
        return {
            "status": "processed",
            "event": "charge.refunded",
            "charge_id": data.get("id"),
            "action": "refund_processed",
        }

    def _handle_charge_failed(self, data: dict) -> dict:
        """Handle charge.failed webhook event."""
        return {
            "status": "processed",
            "event": "charge.failed",
            "charge_id": data.get("id"),
            "action": "payment_failed",
            "reason": data.get("reason", "unknown"),
        }

    def get_monthly_payment(self, amount_cents: int, months: int = 12) -> dict:
        """
        Calculate estimated monthly payment for promotional messaging.

        Note: Actual APR and terms are determined by Affirm based on client credit.

        Args:
            amount_cents: Total amount in cents
            months: Financing term (3, 6, or 12 months)

        Returns:
            Dict with payment estimates
        """
        amount_dollars = amount_cents / 100

        # Affirm APR typically ranges 0-36% - use 15% as estimate
        estimated_apr = 0.15
        monthly_rate = estimated_apr / 12

        # Calculate monthly payment with interest
        if estimated_apr > 0:
            monthly_payment = (
                amount_dollars
                * (monthly_rate * (1 + monthly_rate) ** months)
                / ((1 + monthly_rate) ** months - 1)
            )
        else:
            monthly_payment = amount_dollars / months

        # 0% APR promo payment (for messaging)
        promo_payment = amount_dollars / months

        return {
            "amount": amount_dollars,
            "months": months,
            "estimated_monthly": round(monthly_payment, 2),
            "promo_monthly": round(promo_payment, 2),  # 0% APR payment
            "estimated_apr": estimated_apr,
            "disclaimer": "Rates from 0-36% APR. Payment options through Affirm are subject to eligibility check.",
        }


# Singleton instance
_affirm_service = None


def get_affirm_service() -> AffirmService:
    """Get the singleton AffirmService instance."""
    global _affirm_service
    if _affirm_service is None:
        _affirm_service = AffirmService()
    return _affirm_service
