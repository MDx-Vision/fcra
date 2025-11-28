"""
Stripe Payment Plans Service
Manages billing plans, subscriptions, checkout sessions, and customer portal
"""
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from services.stripe_client import get_stripe_client, get_stripe_credentials, get_webhook_secret
from database import get_db, BillingPlan, ClientSubscription, Client, IntegrationEvent, IntegrationConnection


class StripePlansService:
    """Service for managing Stripe billing plans and subscriptions"""
    
    DEFAULT_PLANS = [
        {
            'name': 'basic',
            'display_name': 'Basic',
            'price_cents': 29900,
            'billing_interval': 'month',
            'features': [
                'Standard credit repair',
                'Round 1 dispute letters (3 bureaus)',
                'Basic FCRA analysis',
                'Email support',
                '30-day response tracking'
            ],
            'sort_order': 1
        },
        {
            'name': 'professional',
            'display_name': 'Professional',
            'price_cents': 59900,
            'billing_interval': 'month',
            'features': [
                'Credit repair + litigation prep',
                'Rounds 1-3 dispute letters',
                'Full FCRA violation analysis',
                'Willfulness assessment',
                'Damages calculation',
                'Priority support',
                'Method of verification requests'
            ],
            'sort_order': 2
        },
        {
            'name': 'premium',
            'display_name': 'Premium',
            'price_cents': 99900,
            'billing_interval': 'month',
            'features': [
                'Full litigation suite',
                'All 4 dispute rounds',
                'Complete forensic analysis',
                'Settlement demand letters',
                'CFPB complaint generation',
                'Attorney coordination',
                'Dedicated support',
                'Credit monitoring integration'
            ],
            'sort_order': 3
        }
    ]
    
    def __init__(self):
        """Initialize with existing Stripe configuration"""
        self._stripe = None
        self._integration_id = None
    
    @property
    def stripe(self):
        """Lazy load Stripe client"""
        if self._stripe is None:
            self._stripe = get_stripe_client()
        return self._stripe
    
    def _get_integration_id(self, db) -> Optional[int]:
        """Get or create Stripe integration connection ID"""
        if self._integration_id:
            return self._integration_id
        
        integration = db.query(IntegrationConnection).filter_by(
            service_name='stripe'
        ).first()
        
        if not integration:
            integration = IntegrationConnection(
                service_name='stripe',
                display_name='Stripe Payments',
                is_active=True,
                connection_status='connected'
            )
            db.add(integration)
            db.commit()
        
        self._integration_id = integration.id
        return self._integration_id
    
    def _log_event(self, db, event_type: str, event_data: dict, 
                   client_id: Optional[int] = None, 
                   response_status: int = 200,
                   error_message: Optional[str] = None):
        """Log integration event for audit trail"""
        try:
            integration_id = self._get_integration_id(db)
            event = IntegrationEvent(
                integration_id=integration_id,
                event_type=event_type,
                event_data=event_data,
                client_id=client_id,
                response_status=response_status,
                error_message=error_message,
                created_at=datetime.utcnow()
            )
            db.add(event)
            db.commit()
        except Exception as e:
            print(f"Failed to log integration event: {e}")
    
    def test_connection(self) -> bool:
        """Test Stripe connection is working"""
        try:
            self.stripe.Account.retrieve()
            return True
        except Exception as e:
            print(f"Stripe connection test failed: {e}")
            return False
    
    def create_plan(self, name: str, price_cents: int, 
                    interval: str = 'month', 
                    features: List[str] = None,
                    display_name: str = None) -> Dict[str, Any]:
        """
        Create a new billing plan in Stripe and database
        
        Args:
            name: Internal plan name (lowercase, no spaces)
            price_cents: Price in cents (e.g., 29900 = $299.00)
            interval: Billing interval ('month' or 'year')
            features: List of feature descriptions
            display_name: Customer-facing plan name
            
        Returns:
            Dict with stripe_product_id, stripe_price_id, plan_id
        """
        db = get_db()
        try:
            display_name = display_name or name.title()
            features = features or []
            
            product = self.stripe.Product.create(
                name=display_name,
                description=f"Brightpath Ascend - {display_name} Plan",
                metadata={'plan_name': name}
            )
            
            price = self.stripe.Price.create(
                product=product.id,
                unit_amount=price_cents,
                currency='usd',
                recurring={'interval': interval}
            )
            
            existing = db.query(BillingPlan).filter_by(name=name).first()
            if existing:
                existing.stripe_product_id = product.id
                existing.stripe_price_id = price.id
                existing.price_cents = price_cents
                existing.billing_interval = interval
                existing.features = features
                existing.display_name = display_name
                existing.updated_at = datetime.utcnow()
                plan_id = existing.id
            else:
                plan = BillingPlan(
                    name=name,
                    display_name=display_name,
                    stripe_product_id=product.id,
                    stripe_price_id=price.id,
                    price_cents=price_cents,
                    billing_interval=interval,
                    features=features,
                    is_active=True
                )
                db.add(plan)
                db.flush()
                plan_id = plan.id
            
            db.commit()
            
            self._log_event(db, 'plan_created', {
                'plan_id': plan_id,
                'name': name,
                'price_cents': price_cents,
                'stripe_product_id': product.id,
                'stripe_price_id': price.id
            })
            
            return {
                'success': True,
                'plan_id': plan_id,
                'stripe_product_id': product.id,
                'stripe_price_id': price.id,
                'name': name,
                'display_name': display_name,
                'price_cents': price_cents,
                'interval': interval
            }
            
        except Exception as e:
            db.rollback()
            self._log_event(db, 'plan_create_error', {
                'name': name,
                'error': str(e)
            }, response_status=500, error_message=str(e))
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            db.close()
    
    def list_plans(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List all billing plans
        
        Returns:
            List of plan dictionaries
        """
        db = get_db()
        try:
            query = db.query(BillingPlan)
            if active_only:
                query = query.filter_by(is_active=True)
            
            plans = query.order_by(BillingPlan.sort_order).all()
            
            return [{
                'id': plan.id,
                'name': plan.name,
                'display_name': plan.display_name,
                'price_cents': plan.price_cents,
                'price_display': f"${plan.price_cents / 100:.2f}",
                'billing_interval': plan.billing_interval,
                'features': plan.features or [],
                'stripe_product_id': plan.stripe_product_id,
                'stripe_price_id': plan.stripe_price_id,
                'is_active': plan.is_active,
                'sort_order': plan.sort_order
            } for plan in plans]
            
        except Exception as e:
            print(f"Error listing plans: {e}")
            return []
        finally:
            db.close()
    
    def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific plan by ID"""
        db = get_db()
        try:
            plan = db.query(BillingPlan).filter_by(id=plan_id).first()
            if not plan:
                return None
            
            return {
                'id': plan.id,
                'name': plan.name,
                'display_name': plan.display_name,
                'price_cents': plan.price_cents,
                'price_display': f"${plan.price_cents / 100:.2f}",
                'billing_interval': plan.billing_interval,
                'features': plan.features or [],
                'stripe_product_id': plan.stripe_product_id,
                'stripe_price_id': plan.stripe_price_id,
                'is_active': plan.is_active
            }
        finally:
            db.close()
    
    def _get_or_create_stripe_customer(self, db, client: Client) -> str:
        """Get or create Stripe customer for client"""
        if client.stripe_customer_id:
            return client.stripe_customer_id
        
        customer = self.stripe.Customer.create(
            email=client.email,
            name=client.name,
            metadata={'client_id': str(client.id)}
        )
        
        client.stripe_customer_id = customer.id
        db.commit()
        
        return customer.id
    
    def create_checkout_session(self, client_id: int, plan_id: int,
                                 success_url: str, cancel_url: str) -> Dict[str, Any]:
        """
        Create Stripe Checkout session for subscription
        
        Args:
            client_id: Database client ID
            plan_id: Database billing plan ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            
        Returns:
            Dict with session_id and checkout_url
        """
        db = get_db()
        try:
            client = db.query(Client).filter_by(id=client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            plan = db.query(BillingPlan).filter_by(id=plan_id).first()
            if not plan or not plan.stripe_price_id:
                return {'success': False, 'error': 'Plan not found or not configured'}
            
            customer_id = self._get_or_create_stripe_customer(db, client)
            
            session = self.stripe.checkout.Session.create(
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
                    'plan_id': str(plan_id),
                    'plan_name': plan.name
                }
            )
            
            self._log_event(db, 'checkout_session_created', {
                'session_id': session.id,
                'client_id': client_id,
                'plan_id': plan_id,
                'plan_name': plan.name
            }, client_id=client_id)
            
            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url
            }
            
        except Exception as e:
            self._log_event(db, 'checkout_session_error', {
                'client_id': client_id,
                'plan_id': plan_id,
                'error': str(e)
            }, client_id=client_id, response_status=500, error_message=str(e))
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def create_customer_portal_session(self, client_id: int, 
                                        return_url: str) -> Dict[str, Any]:
        """
        Create Stripe Customer Portal session for managing subscription
        
        Args:
            client_id: Database client ID
            return_url: URL to redirect after portal
            
        Returns:
            Dict with portal_url
        """
        db = get_db()
        try:
            client = db.query(Client).filter_by(id=client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            if not client.stripe_customer_id:
                return {'success': False, 'error': 'Client has no Stripe customer ID'}
            
            session = self.stripe.billing_portal.Session.create(
                customer=client.stripe_customer_id,
                return_url=return_url
            )
            
            self._log_event(db, 'portal_session_created', {
                'client_id': client_id,
                'portal_url': session.url
            }, client_id=client_id)
            
            return {
                'success': True,
                'portal_url': session.url
            }
            
        except Exception as e:
            self._log_event(db, 'portal_session_error', {
                'client_id': client_id,
                'error': str(e)
            }, client_id=client_id, response_status=500, error_message=str(e))
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events
        
        Args:
            payload: Raw request body
            signature: Stripe-Signature header value
            
        Returns:
            Dict with event_type and processing result
        """
        db = get_db()
        try:
            webhook_secret = get_webhook_secret()
            
            if webhook_secret:
                event = self.stripe.Webhook.construct_event(
                    payload, signature, webhook_secret
                )
            else:
                event_data = json.loads(payload)
                event = self.stripe.Event.construct_from(event_data, self.stripe.api_key)
            
            event_type = event.type
            data = event.data.object
            
            self._log_event(db, f'webhook_{event_type}', {
                'event_id': event.id,
                'event_type': event_type
            })
            
            if event_type == 'checkout.session.completed':
                return self._handle_checkout_completed(db, data)
            elif event_type == 'customer.subscription.created':
                return self._handle_subscription_created(db, data)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(db, data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(db, data)
            elif event_type == 'invoice.paid':
                return self._handle_invoice_paid(db, data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_invoice_failed(db, data)
            
            return {
                'success': True,
                'event_type': event_type,
                'data': {'handled': False, 'message': 'Event type not processed'}
            }
            
        except self.stripe.error.SignatureVerificationError as e:
            return {'success': False, 'error': 'Invalid signature', 'details': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def _handle_checkout_completed(self, db, session) -> Dict[str, Any]:
        """Handle checkout.session.completed webhook"""
        client_id = session.metadata.get('client_id')
        plan_id = session.metadata.get('plan_id')
        
        if not client_id:
            return {'success': True, 'event_type': 'checkout.session.completed', 
                    'data': {'handled': False, 'message': 'No client_id in metadata'}}
        
        subscription = db.query(ClientSubscription).filter_by(
            client_id=int(client_id)
        ).first()
        
        if not subscription:
            subscription = ClientSubscription(
                client_id=int(client_id),
                plan_id=int(plan_id) if plan_id else None,
                stripe_customer_id=session.customer,
                stripe_subscription_id=session.subscription,
                status='active'
            )
            db.add(subscription)
        else:
            subscription.plan_id = int(plan_id) if plan_id else subscription.plan_id
            subscription.stripe_subscription_id = session.subscription
            subscription.status = 'active'
            subscription.updated_at = datetime.utcnow()
        
        client = db.query(Client).filter_by(id=int(client_id)).first()
        if client:
            client.payment_status = 'paid'
            client.payment_received_at = datetime.utcnow()
            client.payment_method = 'stripe'
        
        db.commit()
        
        return {
            'success': True,
            'event_type': 'checkout.session.completed',
            'data': {
                'handled': True,
                'client_id': client_id,
                'plan_id': plan_id,
                'subscription_id': session.subscription
            }
        }
    
    def _handle_subscription_created(self, db, subscription) -> Dict[str, Any]:
        """Handle customer.subscription.created webhook"""
        customer_id = subscription.customer
        
        client = db.query(Client).filter_by(stripe_customer_id=customer_id).first()
        if not client:
            return {'success': True, 'event_type': 'customer.subscription.created',
                    'data': {'handled': False, 'message': 'Client not found'}}
        
        client_sub = db.query(ClientSubscription).filter_by(
            client_id=client.id
        ).first()
        
        if not client_sub:
            client_sub = ClientSubscription(client_id=client.id)
            db.add(client_sub)
        
        client_sub.stripe_subscription_id = subscription.id
        client_sub.stripe_customer_id = customer_id
        client_sub.status = subscription.status
        client_sub.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
        client_sub.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        client_sub.next_payment_date = datetime.fromtimestamp(subscription.current_period_end)
        client_sub.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            'success': True,
            'event_type': 'customer.subscription.created',
            'data': {'handled': True, 'client_id': client.id}
        }
    
    def _handle_subscription_updated(self, db, subscription) -> Dict[str, Any]:
        """Handle customer.subscription.updated webhook"""
        client_sub = db.query(ClientSubscription).filter_by(
            stripe_subscription_id=subscription.id
        ).first()
        
        if not client_sub:
            return {'success': True, 'event_type': 'customer.subscription.updated',
                    'data': {'handled': False, 'message': 'Subscription not found'}}
        
        client_sub.status = subscription.status
        client_sub.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
        client_sub.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        client_sub.cancel_at_period_end = subscription.cancel_at_period_end
        client_sub.next_payment_date = datetime.fromtimestamp(subscription.current_period_end)
        client_sub.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            'success': True,
            'event_type': 'customer.subscription.updated',
            'data': {'handled': True, 'subscription_id': subscription.id}
        }
    
    def _handle_subscription_deleted(self, db, subscription) -> Dict[str, Any]:
        """Handle customer.subscription.deleted webhook"""
        client_sub = db.query(ClientSubscription).filter_by(
            stripe_subscription_id=subscription.id
        ).first()
        
        if not client_sub:
            return {'success': True, 'event_type': 'customer.subscription.deleted',
                    'data': {'handled': False, 'message': 'Subscription not found'}}
        
        client_sub.status = 'canceled'
        client_sub.canceled_at = datetime.utcnow()
        client_sub.updated_at = datetime.utcnow()
        
        client = db.query(Client).filter_by(id=client_sub.client_id).first()
        if client:
            client.payment_status = 'canceled'
        
        db.commit()
        
        return {
            'success': True,
            'event_type': 'customer.subscription.deleted',
            'data': {'handled': True, 'subscription_id': subscription.id}
        }
    
    def _handle_invoice_paid(self, db, invoice) -> Dict[str, Any]:
        """Handle invoice.paid webhook"""
        client_sub = db.query(ClientSubscription).filter_by(
            stripe_subscription_id=invoice.subscription
        ).first()
        
        if client_sub:
            client_sub.amount_paid_cents = (client_sub.amount_paid_cents or 0) + invoice.amount_paid
            client_sub.updated_at = datetime.utcnow()
            db.commit()
        
        return {
            'success': True,
            'event_type': 'invoice.paid',
            'data': {'handled': True, 'amount': invoice.amount_paid}
        }
    
    def _handle_invoice_failed(self, db, invoice) -> Dict[str, Any]:
        """Handle invoice.payment_failed webhook"""
        client_sub = db.query(ClientSubscription).filter_by(
            stripe_subscription_id=invoice.subscription
        ).first()
        
        if client_sub:
            client_sub.status = 'past_due'
            client_sub.updated_at = datetime.utcnow()
            db.commit()
        
        return {
            'success': True,
            'event_type': 'invoice.payment_failed',
            'data': {'handled': True, 'subscription_id': invoice.subscription}
        }
    
    def get_subscription_status(self, client_id: int) -> Dict[str, Any]:
        """
        Get current subscription status for a client
        
        Args:
            client_id: Database client ID
            
        Returns:
            Dict with status, plan, next_payment info
        """
        db = get_db()
        try:
            subscription = db.query(ClientSubscription).filter_by(
                client_id=client_id
            ).first()
            
            if not subscription:
                return {
                    'success': True,
                    'has_subscription': False,
                    'status': 'none',
                    'plan': None,
                    'next_payment': None
                }
            
            plan = None
            if subscription.plan_id:
                plan_obj = db.query(BillingPlan).filter_by(id=subscription.plan_id).first()
                if plan_obj:
                    plan = {
                        'id': plan_obj.id,
                        'name': plan_obj.name,
                        'display_name': plan_obj.display_name,
                        'price_cents': plan_obj.price_cents,
                        'price_display': f"${plan_obj.price_cents / 100:.2f}"
                    }
            
            return {
                'success': True,
                'has_subscription': True,
                'status': subscription.status,
                'plan': plan,
                'stripe_subscription_id': subscription.stripe_subscription_id,
                'current_period_start': subscription.current_period_start.isoformat() if subscription.current_period_start else None,
                'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                'next_payment': subscription.next_payment_date.isoformat() if subscription.next_payment_date else None,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'amount_paid_cents': subscription.amount_paid_cents or 0
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def cancel_subscription(self, client_id: int, at_period_end: bool = True) -> bool:
        """
        Cancel a client's subscription
        
        Args:
            client_id: Database client ID
            at_period_end: If True, cancel at end of billing period; if False, cancel immediately
            
        Returns:
            True if successful, False otherwise
        """
        db = get_db()
        try:
            subscription = db.query(ClientSubscription).filter_by(
                client_id=client_id
            ).first()
            
            if not subscription or not subscription.stripe_subscription_id:
                return False
            
            if at_period_end:
                self.stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
            else:
                self.stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = 'canceled'
                subscription.canceled_at = datetime.utcnow()
            
            subscription.updated_at = datetime.utcnow()
            db.commit()
            
            self._log_event(db, 'subscription_canceled', {
                'client_id': client_id,
                'at_period_end': at_period_end,
                'subscription_id': subscription.stripe_subscription_id
            }, client_id=client_id)
            
            return True
            
        except Exception as e:
            self._log_event(db, 'subscription_cancel_error', {
                'client_id': client_id,
                'error': str(e)
            }, client_id=client_id, response_status=500, error_message=str(e))
            return False
        finally:
            db.close()
    
    def initialize_default_plans(self) -> Dict[str, Any]:
        """Initialize default pricing plans in database and Stripe"""
        results = []
        
        for plan_config in self.DEFAULT_PLANS:
            db = get_db()
            try:
                existing = db.query(BillingPlan).filter_by(name=plan_config['name']).first()
                if existing and existing.stripe_price_id:
                    results.append({
                        'name': plan_config['name'],
                        'status': 'exists',
                        'plan_id': existing.id
                    })
                    continue
            finally:
                db.close()
            
            result = self.create_plan(
                name=plan_config['name'],
                price_cents=plan_config['price_cents'],
                interval=plan_config['billing_interval'],
                features=plan_config['features'],
                display_name=plan_config['display_name']
            )
            
            if result.get('success'):
                db = get_db()
                try:
                    plan = db.query(BillingPlan).filter_by(name=plan_config['name']).first()
                    if plan:
                        plan.sort_order = plan_config['sort_order']
                        db.commit()
                finally:
                    db.close()
            
            results.append({
                'name': plan_config['name'],
                'status': 'created' if result.get('success') else 'error',
                'result': result
            })
        
        return {'success': True, 'plans': results}
    
    def update_plan(self, plan_id: int, **kwargs) -> Dict[str, Any]:
        """Update a billing plan"""
        db = get_db()
        try:
            plan = db.query(BillingPlan).filter_by(id=plan_id).first()
            if not plan:
                return {'success': False, 'error': 'Plan not found'}
            
            if 'display_name' in kwargs:
                plan.display_name = kwargs['display_name']
            if 'features' in kwargs:
                plan.features = kwargs['features']
            if 'is_active' in kwargs:
                plan.is_active = kwargs['is_active']
            if 'sort_order' in kwargs:
                plan.sort_order = kwargs['sort_order']
            
            plan.updated_at = datetime.utcnow()
            db.commit()
            
            return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            db.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics for admin dashboard"""
        db = get_db()
        try:
            total_subscriptions = db.query(ClientSubscription).count()
            active_subscriptions = db.query(ClientSubscription).filter_by(status='active').count()
            canceled_subscriptions = db.query(ClientSubscription).filter_by(status='canceled').count()
            past_due = db.query(ClientSubscription).filter_by(status='past_due').count()
            
            from sqlalchemy import func
            total_revenue = db.query(func.sum(ClientSubscription.amount_paid_cents)).scalar() or 0
            
            plan_stats = []
            plans = db.query(BillingPlan).filter_by(is_active=True).all()
            for plan in plans:
                count = db.query(ClientSubscription).filter_by(
                    plan_id=plan.id, 
                    status='active'
                ).count()
                plan_stats.append({
                    'plan_id': plan.id,
                    'name': plan.display_name,
                    'active_count': count,
                    'mrr': count * plan.price_cents
                })
            
            mrr = sum(p['mrr'] for p in plan_stats)
            
            return {
                'success': True,
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'canceled_subscriptions': canceled_subscriptions,
                'past_due_subscriptions': past_due,
                'total_revenue_cents': total_revenue,
                'total_revenue_display': f"${total_revenue / 100:,.2f}",
                'mrr_cents': mrr,
                'mrr_display': f"${mrr / 100:,.2f}",
                'plan_stats': plan_stats
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def get_active_subscriptions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of active subscriptions with client info"""
        db = get_db()
        try:
            subscriptions = db.query(ClientSubscription).filter(
                ClientSubscription.status.in_(['active', 'past_due'])
            ).order_by(ClientSubscription.created_at.desc()).limit(limit).all()
            
            result = []
            for sub in subscriptions:
                client = db.query(Client).filter_by(id=sub.client_id).first()
                plan = db.query(BillingPlan).filter_by(id=sub.plan_id).first() if sub.plan_id else None
                
                result.append({
                    'subscription_id': sub.id,
                    'client_id': sub.client_id,
                    'client_name': client.name if client else 'Unknown',
                    'client_email': client.email if client else None,
                    'plan_name': plan.display_name if plan else 'Unknown',
                    'plan_price': f"${plan.price_cents / 100:.2f}" if plan else None,
                    'status': sub.status,
                    'current_period_end': sub.current_period_end.strftime('%Y-%m-%d') if sub.current_period_end else None,
                    'cancel_at_period_end': sub.cancel_at_period_end,
                    'amount_paid': f"${(sub.amount_paid_cents or 0) / 100:.2f}",
                    'created_at': sub.created_at.strftime('%Y-%m-%d') if sub.created_at else None
                })
            
            return result
        except Exception as e:
            print(f"Error getting active subscriptions: {e}")
            return []
        finally:
            db.close()


stripe_plans_service = StripePlansService()
