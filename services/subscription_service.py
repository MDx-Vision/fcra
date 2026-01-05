"""
Subscription Service

Handles Stripe subscription billing including:
- Plan management (Basic, Pro, Enterprise)
- Customer creation and management
- Subscription lifecycle (create, cancel, upgrade/downgrade)
- Webhook event handling
- Billing portal access
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
import stripe

from database import Client, BillingPlan, ClientSubscription


# ============================================================================
# Subscription Plans Configuration
# ============================================================================

SUBSCRIPTION_PLANS = {
    'basic': {
        'name': 'Basic',
        'display_name': 'Basic Plan',
        'price_cents': 4900,  # $49/month
        'billing_interval': 'month',
        'features': [
            'Credit report analysis',
            'Basic dispute letters',
            'Email support',
            '1 round of disputes',
        ],
        'sort_order': 1,
    },
    'pro': {
        'name': 'Pro',
        'display_name': 'Pro Plan',
        'price_cents': 9900,  # $99/month
        'billing_interval': 'month',
        'features': [
            'Full FCRA analysis',
            'Unlimited dispute rounds',
            'Priority email support',
            'Secondary bureau freezes',
            'Credit monitoring integration',
        ],
        'sort_order': 2,
    },
    'enterprise': {
        'name': 'Enterprise',
        'display_name': 'Enterprise Plan',
        'price_cents': 19900,  # $199/month
        'billing_interval': 'month',
        'features': [
            'Everything in Pro',
            'Dedicated account manager',
            'Phone support',
            'Litigation preparation',
            'Settlement assistance',
            'VIP priority queue',
        ],
        'sort_order': 3,
    },
}


class SubscriptionService:
    """Service for managing Stripe subscriptions."""

    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
        self._init_stripe()

    def _init_stripe(self):
        """Initialize Stripe API with credentials."""
        try:
            from services.stripe_client import get_stripe_secret_key
            stripe.api_key = get_stripe_secret_key()
        except Exception:
            # Fallback to environment variable
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

    # =========================================================================
    # Plan Management
    # =========================================================================

    def sync_plans_to_stripe(self) -> Dict[str, Any]:
        """
        Create or update Stripe products and prices for all plans.

        Returns:
            Dict with created/updated product and price IDs
        """
        results = {}

        for plan_key, plan_config in SUBSCRIPTION_PLANS.items():
            # Check if plan exists in database
            db_plan = self.db.query(BillingPlan).filter(
                BillingPlan.name == plan_key
            ).first()

            # Create or update Stripe product
            if db_plan and db_plan.stripe_product_id:
                # Update existing product
                product = stripe.Product.modify(
                    db_plan.stripe_product_id,
                    name=plan_config['display_name'],
                    description=', '.join(plan_config['features'][:3]),
                    metadata={'plan_key': plan_key}
                )
            else:
                # Create new product
                product = stripe.Product.create(
                    name=plan_config['display_name'],
                    description=', '.join(plan_config['features'][:3]),
                    metadata={'plan_key': plan_key}
                )

            # Create or get price (prices are immutable in Stripe)
            if db_plan and db_plan.stripe_price_id:
                price_id = db_plan.stripe_price_id
            else:
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=plan_config['price_cents'],
                    currency='usd',
                    recurring={'interval': plan_config['billing_interval']},
                    metadata={'plan_key': plan_key}
                )
                price_id = price.id

            # Save to database
            if not db_plan:
                db_plan = BillingPlan(
                    name=plan_key,
                    display_name=plan_config['display_name'],
                    stripe_product_id=product.id,
                    stripe_price_id=price_id,
                    price_cents=plan_config['price_cents'],
                    billing_interval=plan_config['billing_interval'],
                    features=plan_config['features'],
                    is_active=True,
                    sort_order=plan_config['sort_order']
                )
                self.db.add(db_plan)
            else:
                db_plan.stripe_product_id = product.id
                db_plan.stripe_price_id = price_id
                db_plan.display_name = plan_config['display_name']
                db_plan.price_cents = plan_config['price_cents']
                db_plan.features = plan_config['features']

            self.db.commit()

            results[plan_key] = {
                'product_id': product.id,
                'price_id': price_id,
                'db_plan_id': db_plan.id
            }

        return results

    def get_plans(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all subscription plans."""
        query = self.db.query(BillingPlan).order_by(BillingPlan.sort_order)

        if active_only:
            query = query.filter(BillingPlan.is_active == True)

        plans = query.all()

        return [{
            'id': p.id,
            'name': p.name,
            'display_name': p.display_name,
            'price_cents': p.price_cents,
            'price_dollars': p.price_cents / 100,
            'billing_interval': p.billing_interval,
            'features': p.features or [],
            'stripe_price_id': p.stripe_price_id,
            'is_active': p.is_active,
        } for p in plans]

    def get_plan_by_name(self, name: str) -> Optional[BillingPlan]:
        """Get a plan by name."""
        return self.db.query(BillingPlan).filter(
            BillingPlan.name == name
        ).first()

    # =========================================================================
    # Customer Management
    # =========================================================================

    def get_or_create_stripe_customer(self, client: Client) -> str:
        """
        Get existing Stripe customer or create new one.

        Args:
            client: Client model instance

        Returns:
            Stripe customer ID
        """
        # Check if client already has a subscription with customer ID
        subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.client_id == client.id
        ).first()

        if subscription and subscription.stripe_customer_id:
            return subscription.stripe_customer_id

        # Search Stripe for existing customer by email
        customers = stripe.Customer.list(email=client.email, limit=1)
        if customers.data:
            customer_id = customers.data[0].id
        else:
            # Create new customer
            customer = stripe.Customer.create(
                email=client.email,
                name=f"{client.first_name or ''} {client.last_name or ''}".strip() or client.email,
                metadata={
                    'client_id': str(client.id),
                    'source': 'fcra_platform'
                }
            )
            customer_id = customer.id

        # Store customer ID if subscription record exists
        if subscription:
            subscription.stripe_customer_id = customer_id
            self.db.commit()

        return customer_id

    def update_customer_payment_method(self, client_id: int, payment_method_id: str) -> Dict[str, Any]:
        """
        Attach a payment method to customer and set as default.

        Args:
            client_id: Client ID
            payment_method_id: Stripe payment method ID

        Returns:
            Updated customer data
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError(f"Client {client_id} not found")

        customer_id = self.get_or_create_stripe_customer(client)

        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id
        )

        # Set as default payment method
        stripe.Customer.modify(
            customer_id,
            invoice_settings={'default_payment_method': payment_method_id}
        )

        return {'customer_id': customer_id, 'payment_method_id': payment_method_id}

    # =========================================================================
    # Subscription Lifecycle
    # =========================================================================

    def create_checkout_session(
        self,
        client_id: int,
        plan_name: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for subscription.

        Args:
            client_id: Client ID
            plan_name: Plan name (basic, pro, enterprise)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            Checkout session data with URL
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError(f"Client {client_id} not found")

        plan = self.get_plan_by_name(plan_name)
        if not plan or not plan.stripe_price_id:
            raise ValueError(f"Plan {plan_name} not found or not configured in Stripe")

        customer_id = self.get_or_create_stripe_customer(client)

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': plan.stripe_price_id,
                'quantity': 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'client_id': str(client_id),
                'plan_name': plan_name,
            },
            subscription_data={
                'metadata': {
                    'client_id': str(client_id),
                    'plan_name': plan_name,
                }
            }
        )

        return {
            'session_id': session.id,
            'url': session.url,
            'customer_id': customer_id,
            'plan_name': plan_name,
        }

    def create_subscription(
        self,
        client_id: int,
        plan_name: str,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription directly (for clients with saved payment method).

        Args:
            client_id: Client ID
            plan_name: Plan name
            payment_method_id: Optional payment method ID

        Returns:
            Subscription data
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError(f"Client {client_id} not found")

        plan = self.get_plan_by_name(plan_name)
        if not plan or not plan.stripe_price_id:
            raise ValueError(f"Plan {plan_name} not found")

        customer_id = self.get_or_create_stripe_customer(client)

        # Set payment method if provided
        if payment_method_id:
            self.update_customer_payment_method(client_id, payment_method_id)

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': plan.stripe_price_id}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
            metadata={
                'client_id': str(client_id),
                'plan_name': plan_name,
            }
        )

        # Save to database
        self._save_subscription(client_id, plan.id, subscription)

        result = {
            'subscription_id': subscription.id,
            'status': subscription.status,
            'client_secret': None,
        }

        # Include client secret for incomplete subscriptions
        if subscription.latest_invoice and subscription.latest_invoice.payment_intent:
            result['client_secret'] = subscription.latest_invoice.payment_intent.client_secret

        return result

    def cancel_subscription(
        self,
        client_id: int,
        at_period_end: bool = True,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            client_id: Client ID
            at_period_end: If True, cancel at end of billing period
            reason: Optional cancellation reason

        Returns:
            Updated subscription data
        """
        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.client_id == client_id,
            ClientSubscription.status.in_(['active', 'trialing', 'past_due'])
        ).first()

        if not db_subscription or not db_subscription.stripe_subscription_id:
            raise ValueError("No active subscription found")

        if at_period_end:
            subscription = stripe.Subscription.modify(
                db_subscription.stripe_subscription_id,
                cancel_at_period_end=True,
                metadata={'cancellation_reason': reason or 'user_requested'}
            )
            db_subscription.cancel_at_period_end = True
        else:
            subscription = stripe.Subscription.delete(
                db_subscription.stripe_subscription_id
            )
            db_subscription.status = 'canceled'
            db_subscription.canceled_at = datetime.utcnow()

        self.db.commit()

        return {
            'subscription_id': subscription.id,
            'status': subscription.status,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end).isoformat() if subscription.current_period_end else None,
        }

    def reactivate_subscription(self, client_id: int) -> Dict[str, Any]:
        """
        Reactivate a subscription scheduled for cancellation.

        Args:
            client_id: Client ID

        Returns:
            Updated subscription data
        """
        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.client_id == client_id,
            ClientSubscription.cancel_at_period_end == True
        ).first()

        if not db_subscription or not db_subscription.stripe_subscription_id:
            raise ValueError("No subscription pending cancellation found")

        subscription = stripe.Subscription.modify(
            db_subscription.stripe_subscription_id,
            cancel_at_period_end=False
        )

        db_subscription.cancel_at_period_end = False
        self.db.commit()

        return {
            'subscription_id': subscription.id,
            'status': subscription.status,
            'cancel_at_period_end': False,
        }

    def change_plan(self, client_id: int, new_plan_name: str) -> Dict[str, Any]:
        """
        Upgrade or downgrade subscription plan.

        Args:
            client_id: Client ID
            new_plan_name: New plan name

        Returns:
            Updated subscription data
        """
        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.client_id == client_id,
            ClientSubscription.status == 'active'
        ).first()

        if not db_subscription or not db_subscription.stripe_subscription_id:
            raise ValueError("No active subscription found")

        new_plan = self.get_plan_by_name(new_plan_name)
        if not new_plan or not new_plan.stripe_price_id:
            raise ValueError(f"Plan {new_plan_name} not found")

        # Get current subscription
        subscription = stripe.Subscription.retrieve(db_subscription.stripe_subscription_id)

        # Update subscription with new price
        updated_subscription = stripe.Subscription.modify(
            db_subscription.stripe_subscription_id,
            items=[{
                'id': subscription['items']['data'][0].id,
                'price': new_plan.stripe_price_id,
            }],
            proration_behavior='create_prorations',
            metadata={'plan_name': new_plan_name}
        )

        # Update database
        db_subscription.plan_id = new_plan.id
        self.db.commit()

        return {
            'subscription_id': updated_subscription.id,
            'status': updated_subscription.status,
            'new_plan': new_plan_name,
            'effective_date': datetime.utcnow().isoformat(),
        }

    def get_subscription(self, client_id: int) -> Optional[Dict[str, Any]]:
        """
        Get subscription details for a client.

        Args:
            client_id: Client ID

        Returns:
            Subscription data or None
        """
        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.client_id == client_id
        ).first()

        if not db_subscription:
            return None

        plan = None
        if db_subscription.plan_id:
            plan = self.db.query(BillingPlan).filter(
                BillingPlan.id == db_subscription.plan_id
            ).first()

        return {
            'id': db_subscription.id,
            'stripe_subscription_id': db_subscription.stripe_subscription_id,
            'stripe_customer_id': db_subscription.stripe_customer_id,
            'status': db_subscription.status,
            'plan': {
                'name': plan.name if plan else None,
                'display_name': plan.display_name if plan else None,
                'price_cents': plan.price_cents if plan else None,
                'price_dollars': plan.price_cents / 100 if plan else None,
                'features': plan.features if plan else [],
            } if plan else None,
            'current_period_start': db_subscription.current_period_start.isoformat() if db_subscription.current_period_start else None,
            'current_period_end': db_subscription.current_period_end.isoformat() if db_subscription.current_period_end else None,
            'cancel_at_period_end': db_subscription.cancel_at_period_end,
            'canceled_at': db_subscription.canceled_at.isoformat() if db_subscription.canceled_at else None,
            'amount_paid_cents': db_subscription.amount_paid_cents,
            'next_payment_date': db_subscription.next_payment_date.isoformat() if db_subscription.next_payment_date else None,
        }

    # =========================================================================
    # Billing Portal
    # =========================================================================

    def create_billing_portal_session(
        self,
        client_id: int,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe billing portal session for subscription management.

        Args:
            client_id: Client ID
            return_url: URL to return to after portal session

        Returns:
            Portal session data with URL
        """
        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.client_id == client_id
        ).first()

        if not db_subscription or not db_subscription.stripe_customer_id:
            raise ValueError("No customer found for this client")

        session = stripe.billing_portal.Session.create(
            customer=db_subscription.stripe_customer_id,
            return_url=return_url,
        )

        return {
            'url': session.url,
            'return_url': return_url,
        }

    # =========================================================================
    # Webhook Handlers
    # =========================================================================

    def handle_webhook_event(self, event: stripe.Event) -> Dict[str, Any]:
        """
        Handle incoming Stripe webhook events.

        Args:
            event: Stripe event object

        Returns:
            Processing result
        """
        event_type = event.type
        data = event.data.object

        handlers = {
            'checkout.session.completed': self._handle_checkout_completed,
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'invoice.paid': self._handle_invoice_paid,
            'invoice.payment_failed': self._handle_invoice_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(data)

        return {'handled': False, 'event_type': event_type}

    def _handle_checkout_completed(self, session: Dict) -> Dict[str, Any]:
        """Handle checkout.session.completed event."""
        if session.get('mode') != 'subscription':
            return {'handled': False, 'reason': 'Not a subscription checkout'}

        client_id = session.get('metadata', {}).get('client_id')
        subscription_id = session.get('subscription')
        customer_id = session.get('customer')

        if not client_id or not subscription_id:
            return {'handled': False, 'reason': 'Missing metadata'}

        # Fetch full subscription details
        subscription = stripe.Subscription.retrieve(subscription_id)
        plan_name = subscription.metadata.get('plan_name')

        plan = self.get_plan_by_name(plan_name) if plan_name else None

        self._save_subscription(int(client_id), plan.id if plan else None, subscription, customer_id)

        return {'handled': True, 'client_id': client_id, 'subscription_id': subscription_id}

    def _handle_subscription_created(self, subscription: Dict) -> Dict[str, Any]:
        """Handle customer.subscription.created event."""
        client_id = subscription.get('metadata', {}).get('client_id')
        if not client_id:
            return {'handled': False, 'reason': 'Missing client_id in metadata'}

        plan_name = subscription.get('metadata', {}).get('plan_name')
        plan = self.get_plan_by_name(plan_name) if plan_name else None

        self._save_subscription(int(client_id), plan.id if plan else None, subscription)

        return {'handled': True, 'client_id': client_id}

    def _handle_subscription_updated(self, subscription: Dict) -> Dict[str, Any]:
        """Handle customer.subscription.updated event."""
        subscription_id = subscription.get('id')

        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.stripe_subscription_id == subscription_id
        ).first()

        if not db_subscription:
            return {'handled': False, 'reason': 'Subscription not found'}

        # Update subscription details
        db_subscription.status = subscription.get('status')
        db_subscription.cancel_at_period_end = subscription.get('cancel_at_period_end', False)

        if subscription.get('current_period_start'):
            db_subscription.current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
        if subscription.get('current_period_end'):
            db_subscription.current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
        if subscription.get('canceled_at'):
            db_subscription.canceled_at = datetime.fromtimestamp(subscription['canceled_at'])

        self.db.commit()

        return {'handled': True, 'subscription_id': subscription_id}

    def _handle_subscription_deleted(self, subscription: Dict) -> Dict[str, Any]:
        """Handle customer.subscription.deleted event."""
        subscription_id = subscription.get('id')

        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.stripe_subscription_id == subscription_id
        ).first()

        if not db_subscription:
            return {'handled': False, 'reason': 'Subscription not found'}

        db_subscription.status = 'canceled'
        db_subscription.canceled_at = datetime.utcnow()
        self.db.commit()

        return {'handled': True, 'subscription_id': subscription_id}

    def _handle_invoice_paid(self, invoice: Dict) -> Dict[str, Any]:
        """Handle invoice.paid event."""
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return {'handled': False, 'reason': 'Not a subscription invoice'}

        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.stripe_subscription_id == subscription_id
        ).first()

        if not db_subscription:
            return {'handled': False, 'reason': 'Subscription not found'}

        # Update payment tracking
        amount_paid = invoice.get('amount_paid', 0)
        db_subscription.amount_paid_cents = (db_subscription.amount_paid_cents or 0) + amount_paid
        db_subscription.status = 'active'

        # Update next payment date
        if invoice.get('next_payment_attempt'):
            db_subscription.next_payment_date = datetime.fromtimestamp(invoice['next_payment_attempt'])

        self.db.commit()

        return {'handled': True, 'subscription_id': subscription_id, 'amount_paid': amount_paid}

    def _handle_invoice_payment_failed(self, invoice: Dict) -> Dict[str, Any]:
        """Handle invoice.payment_failed event."""
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return {'handled': False, 'reason': 'Not a subscription invoice'}

        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.stripe_subscription_id == subscription_id
        ).first()

        if not db_subscription:
            return {'handled': False, 'reason': 'Subscription not found'}

        db_subscription.status = 'past_due'
        self.db.commit()

        # Send dunning email
        client = self.db.query(Client).filter(Client.id == db_subscription.client_id).first()
        if client and client.email:
            from services.email_service import send_subscription_past_due_email
            send_subscription_past_due_email(
                client_email=client.email,
                client_name=client.name or "Client"
            )

        return {'handled': True, 'subscription_id': subscription_id, 'status': 'past_due'}

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _save_subscription(
        self,
        client_id: int,
        plan_id: Optional[int],
        subscription: Any,
        customer_id: Optional[str] = None
    ) -> ClientSubscription:
        """Save or update subscription in database."""
        db_subscription = self.db.query(ClientSubscription).filter(
            ClientSubscription.client_id == client_id
        ).first()

        if not db_subscription:
            db_subscription = ClientSubscription(client_id=client_id)
            self.db.add(db_subscription)

        db_subscription.stripe_subscription_id = subscription.id if hasattr(subscription, 'id') else subscription.get('id')
        db_subscription.stripe_customer_id = customer_id or (subscription.customer if hasattr(subscription, 'customer') else subscription.get('customer'))
        db_subscription.plan_id = plan_id
        db_subscription.status = subscription.status if hasattr(subscription, 'status') else subscription.get('status')
        db_subscription.cancel_at_period_end = subscription.cancel_at_period_end if hasattr(subscription, 'cancel_at_period_end') else subscription.get('cancel_at_period_end', False)

        # Handle period dates
        period_start = subscription.current_period_start if hasattr(subscription, 'current_period_start') else subscription.get('current_period_start')
        period_end = subscription.current_period_end if hasattr(subscription, 'current_period_end') else subscription.get('current_period_end')

        if period_start:
            db_subscription.current_period_start = datetime.fromtimestamp(period_start)
        if period_end:
            db_subscription.current_period_end = datetime.fromtimestamp(period_end)
            db_subscription.next_payment_date = datetime.fromtimestamp(period_end)

        self.db.commit()
        return db_subscription


# Factory function
def get_subscription_service(db_session: Session) -> SubscriptionService:
    """Create a SubscriptionService instance."""
    return SubscriptionService(db_session)
