"""
Stripe Webhooks Service

Handles incoming Stripe webhook events:
- payment_intent.succeeded - Payment was successful
- payment_intent.payment_failed - Payment failed
- charge.refunded - Payment was refunded
- customer.subscription.* - Subscription events (for prepay plans)

Webhook URL: /api/webhooks/stripe
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from database import Client, SessionLocal

logger = logging.getLogger(__name__)

# Event types we handle
HANDLED_EVENTS = [
    "payment_intent.succeeded",
    "payment_intent.payment_failed",
    "charge.refunded",
    "checkout.session.completed",
]


def get_stripe_webhooks_service(db=None):
    """Factory function to get StripeWebhooksService instance."""
    if db is None:
        db = SessionLocal()
    return StripeWebhooksService(db)


class StripeWebhooksService:
    """Service for handling Stripe webhook events."""

    def __init__(self, db):
        self.db = db

    def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route webhook event to appropriate handler.

        Args:
            event: Stripe event object (dict)

        Returns:
            Dict with success status and any relevant data
        """
        event_type = event.get("type")
        event_id = event.get("id")

        logger.info(f"Processing Stripe webhook: {event_type} ({event_id})")

        # Route to handler
        handlers = {
            "payment_intent.succeeded": self._handle_payment_succeeded,
            "payment_intent.payment_failed": self._handle_payment_failed,
            "charge.refunded": self._handle_refund,
            "checkout.session.completed": self._handle_checkout_completed,
        }

        handler = handlers.get(event_type)

        if handler:
            try:
                result = handler(event)
                return {
                    "success": True,
                    "event_type": event_type,
                    "event_id": event_id,
                    "result": result,
                }
            except Exception as e:
                logger.error(f"Error handling {event_type}: {str(e)}")
                return {
                    "success": False,
                    "event_type": event_type,
                    "event_id": event_id,
                    "error": str(e),
                }
        else:
            # Unhandled event type - acknowledge but don't process
            logger.info(f"Unhandled event type: {event_type}")
            return {
                "success": True,
                "event_type": event_type,
                "event_id": event_id,
                "message": "Event type not handled",
            }

    def _handle_payment_succeeded(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful payment.

        Updates client stage based on payment type:
        - analysis: lead -> analysis_paid
        - round: pending_payment -> active (for round 1)
        """
        payment_intent = event.get("data", {}).get("object", {})
        metadata = payment_intent.get("metadata", {})

        client_id = metadata.get("client_id")
        payment_type = metadata.get("payment_type")
        payment_intent_id = payment_intent.get("id")
        amount = payment_intent.get("amount", 0)

        if not client_id:
            return {"message": "No client_id in metadata"}

        client = self.db.query(Client).filter(Client.id == int(client_id)).first()
        if not client:
            return {"error": f"Client {client_id} not found"}

        if payment_type == "analysis":
            # Analysis payment - move to analysis_paid
            client.client_stage = "analysis_paid"
            client.analysis_payment_id = payment_intent_id
            client.analysis_paid_at = datetime.utcnow()
            client.total_paid = (client.total_paid or 0) + amount

            # Calculate Round 1 amount due with credit
            client.round_1_amount_due = 29800  # $298 after $199 credit

            self.db.commit()

            # Log timeline event
            self._log_timeline(
                client.id,
                "payment_received",
                "Analysis Payment Received",
                f"Payment of ${amount/100:.2f} received for full analysis.",
            )

            return {
                "client_id": client_id,
                "payment_type": "analysis",
                "new_stage": "analysis_paid",
                "amount": amount,
            }

        elif payment_type == "round":
            # Round payment
            round_number = int(metadata.get("round_number", 1))

            client.current_round_payment_id = payment_intent_id
            client.last_round_paid_at = datetime.utcnow()
            client.total_paid = (client.total_paid or 0) + amount
            client.current_dispute_round = round_number

            # First round activates the client
            if round_number == 1 and client.client_stage in [
                "pending_payment",
                "onboarding",
            ]:
                client.client_stage = "active"
                client.dispute_status = "active"

            self.db.commit()

            # Log timeline event
            self._log_timeline(
                client.id,
                "payment_received",
                f"Round {round_number} Payment",
                f"Payment of ${amount/100:.2f} received for Round {round_number} dispute letters.",
            )

            return {
                "client_id": client_id,
                "payment_type": "round",
                "round_number": round_number,
                "new_stage": client.client_stage,
                "amount": amount,
            }

        elif payment_type == "prepay":
            # Prepay package
            package = metadata.get("package")

            from services.client_payment_service import PREPAY_PACKAGES

            pkg_info = PREPAY_PACKAGES.get(package, {})

            client.prepay_package = package
            client.prepay_rounds_remaining = pkg_info.get("rounds", 0)
            client.total_paid = (client.total_paid or 0) + amount
            client.client_stage = "onboarding"

            self.db.commit()

            self._log_timeline(
                client.id,
                "payment_received",
                "Prepay Package Purchased",
                f'{pkg_info.get("name", package)} package activated with {pkg_info.get("rounds", 0)} rounds.',
            )

            return {
                "client_id": client_id,
                "payment_type": "prepay",
                "package": package,
                "rounds": pkg_info.get("rounds", 0),
                "amount": amount,
            }

        return {"message": f"Unknown payment_type: {payment_type}"}

    def _handle_payment_failed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle failed payment.

        Updates client stage to payment_failed.
        """
        payment_intent = event.get("data", {}).get("object", {})
        metadata = payment_intent.get("metadata", {})

        client_id = metadata.get("client_id")
        payment_type = metadata.get("payment_type")
        error_message = payment_intent.get("last_payment_error", {}).get(
            "message", "Unknown error"
        )

        if not client_id:
            return {"message": "No client_id in metadata"}

        client = self.db.query(Client).filter(Client.id == int(client_id)).first()
        if not client:
            return {"error": f"Client {client_id} not found"}

        # Update client stage
        previous_stage = client.client_stage
        client.client_stage = "payment_failed"

        self.db.commit()

        # Log timeline event
        self._log_timeline(
            client.id,
            "payment_failed",
            "Payment Failed",
            f"Your payment could not be processed: {error_message}",
        )

        # Send email notification about failed payment
        from services.email_service import send_payment_failed_email

        if client.email:
            send_payment_failed_email(
                client_email=client.email,
                client_name=client.name or "Client",
                error_message=error_message,
            )

        return {
            "client_id": client_id,
            "payment_type": payment_type,
            "previous_stage": previous_stage,
            "new_stage": "payment_failed",
            "error": error_message,
        }

    def _handle_refund(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle refund event.

        Logs the refund but doesn't change client stage.
        """
        charge = event.get("data", {}).get("object", {})
        metadata = charge.get("metadata", {})

        client_id = metadata.get("client_id")
        amount_refunded = charge.get("amount_refunded", 0)

        if not client_id:
            return {"message": "No client_id in metadata"}

        client = self.db.query(Client).filter(Client.id == int(client_id)).first()
        if not client:
            return {"error": f"Client {client_id} not found"}

        # Adjust total paid
        client.total_paid = max(0, (client.total_paid or 0) - amount_refunded)
        self.db.commit()

        # Log timeline event
        self._log_timeline(
            client.id,
            "refund_processed",
            "Refund Processed",
            f"A refund of ${amount_refunded/100:.2f} has been processed.",
        )

        return {"client_id": client_id, "amount_refunded": amount_refunded}

    def _handle_checkout_completed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle checkout session completed (used for prepay packages).
        """
        session = event.get("data", {}).get("object", {})
        metadata = session.get("metadata", {})

        client_id = metadata.get("client_id")
        payment_type = metadata.get("payment_type")

        if payment_type == "prepay":
            package = metadata.get("package")

            if not client_id:
                return {"message": "No client_id in metadata"}

            client = self.db.query(Client).filter(Client.id == int(client_id)).first()
            if not client:
                return {"error": f"Client {client_id} not found"}

            from services.client_payment_service import PREPAY_PACKAGES

            pkg_info = PREPAY_PACKAGES.get(package, {})

            client.prepay_package = package
            client.prepay_rounds_remaining = pkg_info.get("rounds", 0)
            client.client_stage = "onboarding"

            self.db.commit()

            return {
                "client_id": client_id,
                "package": package,
                "rounds": pkg_info.get("rounds", 0),
            }

        return {"message": f"Checkout completed for type: {payment_type}"}

    def _log_timeline(
        self, client_id: int, event_type: str, title: str, description: str
    ):
        """Helper to log timeline events."""
        try:
            from services.timeline_service import get_timeline_service

            service = get_timeline_service(self.db)
            service.add_event(
                client_id=client_id,
                event_type=event_type,
                title=title,
                description=description,
                category="payment",
            )
        except Exception as e:
            logger.warning(f"Failed to log timeline event: {e}")
