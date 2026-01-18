"""
Client Payment Service

Handles all payment operations for the client journey:
1. $199 Analysis Payment
2. Round 1 Payment ($497 - $199 credit = $298)
3. Round 2+ Payments ($297 each)
4. Prepay Package Purchases
5. Settlement Fee Processing

Payment flow:
- Analysis: One-time charge of $199
- Round 1: $298 after analysis credit applied
- Round 2+: $297 per round, charged when letters are sent
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from database import SessionLocal, Client

logger = logging.getLogger(__name__)

# Pricing constants (in cents)
ANALYSIS_PRICE = 19900  # $199
ROUND_1_PRICE = 49700   # $497
ROUND_1_WITH_CREDIT = 29800  # $298 (after $199 credit)
ROUND_2_PLUS_PRICE = 29700  # $297
SETTLEMENT_FEE_PERCENT = 30

# Prepay packages (in cents)
PREPAY_PACKAGES = {
    'starter': {
        'name': 'Starter Package',
        'rounds': 2,
        'normal_price': 79400,   # $794 (analysis + 2 rounds)
        'prepay_price': 74900,   # $749
        'savings': 4500,         # $45
    },
    'standard': {
        'name': 'Standard Package',
        'rounds': 4,
        'normal_price': 138800,  # $1,388 (analysis + 4 rounds)
        'prepay_price': 129500,  # $1,295
        'savings': 9300,         # $93
    },
    'complete': {
        'name': 'Complete Package',
        'rounds': 6,
        'normal_price': 198200,  # $1,982 (analysis + 6 rounds)
        'prepay_price': 179500,  # $1,795
        'savings': 18700,        # $187
    },
    'unlimited': {
        'name': 'Unlimited Package',
        'rounds': 99,  # Effectively unlimited
        'normal_price': None,
        'prepay_price': 200000,  # $2,000
        'savings': None,
    },
}

# Financing upcharge
FINANCING_UPCHARGE = 20000  # $200


def get_client_payment_service(db=None):
    """Factory function to get ClientPaymentService instance."""
    if db is None:
        db = SessionLocal()
    return ClientPaymentService(db)


class ClientPaymentService:
    """Service for handling client payments."""

    def __init__(self, db):
        self.db = db
        self._stripe = None

    @property
    def stripe(self):
        """Lazy-load Stripe client."""
        if self._stripe is None:
            try:
                from services.stripe_client import get_stripe_client
                self._stripe = get_stripe_client()
            except Exception as e:
                logger.warning(f"Could not initialize Stripe: {e}")
                self._stripe = None
        return self._stripe

    def create_analysis_payment_intent(
        self,
        client_id: int,
        return_url: str = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent for the $199 analysis fee.

        Returns client_secret for frontend Stripe Elements.
        """
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}

            if client.client_stage not in ['lead']:
                return {
                    'success': False,
                    'error': f'Invalid stage for analysis payment: {client.client_stage}'
                }

            if not self.stripe:
                return {'success': False, 'error': 'Payment system unavailable'}

            # Create payment intent
            intent = self.stripe.PaymentIntent.create(
                amount=ANALYSIS_PRICE,
                currency='usd',
                metadata={
                    'client_id': str(client_id),
                    'payment_type': 'analysis',
                    'client_email': client.email,
                },
                receipt_email=client.email,
                description=f'Credit Analysis - {client.name}',
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'
                },
            )

            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': ANALYSIS_PRICE,
                'amount_display': '$199.00'
            }

        except Exception as e:
            logger.error(f"Error creating analysis payment: {str(e)}")
            return {'success': False, 'error': str(e)}

    def confirm_analysis_payment(
        self,
        client_id: int,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Confirm the analysis payment was successful.
        Updates client stage and applies credit.
        """
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}

            if not self.stripe:
                # In test mode, just mark as paid
                client.client_stage = 'analysis_paid'
                client.analysis_payment_id = payment_intent_id or 'test_payment'
                client.analysis_paid_at = datetime.utcnow()
                client.total_paid = (client.total_paid or 0) + ANALYSIS_PRICE
                client.round_1_amount_due = ROUND_1_WITH_CREDIT
                self.db.commit()
                return {
                    'success': True,
                    'client_stage': 'analysis_paid',
                    'analysis_credit': ANALYSIS_PRICE,
                    'round_1_due': ROUND_1_WITH_CREDIT
                }

            # Verify payment with Stripe
            intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)

            if intent.status != 'succeeded':
                return {
                    'success': False,
                    'error': f'Payment not successful: {intent.status}'
                }

            # Update client
            client.client_stage = 'analysis_paid'
            client.analysis_payment_id = payment_intent_id
            client.analysis_paid_at = datetime.utcnow()
            client.total_paid = (client.total_paid or 0) + ANALYSIS_PRICE
            client.round_1_amount_due = ROUND_1_WITH_CREDIT  # $298

            self.db.commit()

            return {
                'success': True,
                'client_stage': 'analysis_paid',
                'analysis_credit': ANALYSIS_PRICE,
                'round_1_due': ROUND_1_WITH_CREDIT,
                'message': 'Analysis payment confirmed! $199 credit applied to Round 1.'
            }

        except Exception as e:
            logger.error(f"Error confirming analysis payment: {str(e)}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}

    def create_round_payment_intent(
        self,
        client_id: int,
        round_number: int = None
    ) -> Dict[str, Any]:
        """
        Create a PaymentIntent for a dispute round.

        Round 1: $298 (after $199 credit)
        Round 2+: $297
        """
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}

            # Determine round number
            if round_number is None:
                round_number = (client.current_dispute_round or 0) + 1

            # Calculate amount
            if round_number == 1:
                # Check if analysis was paid
                if client.analysis_paid_at:
                    amount = ROUND_1_WITH_CREDIT  # $298
                    description = f'Round 1 Dispute Letters (with $199 credit)'
                else:
                    amount = ROUND_1_PRICE  # $497
                    description = f'Round 1 Dispute Letters'
            else:
                amount = ROUND_2_PLUS_PRICE  # $297
                description = f'Round {round_number} Dispute Letters'

            if not self.stripe:
                return {
                    'success': True,
                    'amount': amount,
                    'amount_display': f'${amount/100:.2f}',
                    'round_number': round_number,
                    'test_mode': True
                }

            intent = self.stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                metadata={
                    'client_id': str(client_id),
                    'payment_type': 'round',
                    'round_number': str(round_number),
                    'client_email': client.email,
                },
                receipt_email=client.email,
                description=f'{description} - {client.name}',
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'
                },
            )

            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': amount,
                'amount_display': f'${amount/100:.2f}',
                'round_number': round_number
            }

        except Exception as e:
            logger.error(f"Error creating round payment: {str(e)}")
            return {'success': False, 'error': str(e)}

    def confirm_round_payment(
        self,
        client_id: int,
        payment_intent_id: str,
        round_number: int
    ) -> Dict[str, Any]:
        """
        Confirm a round payment was successful.
        Updates client and enables letter sending.
        """
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}

            # Determine amount paid
            if round_number == 1:
                amount = ROUND_1_WITH_CREDIT if client.analysis_paid_at else ROUND_1_PRICE
            else:
                amount = ROUND_2_PLUS_PRICE

            if self.stripe:
                # Verify payment with Stripe
                intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
                if intent.status != 'succeeded':
                    return {
                        'success': False,
                        'error': f'Payment not successful: {intent.status}'
                    }

            # Update client
            client.current_round_payment_id = payment_intent_id
            client.last_round_paid_at = datetime.utcnow()
            client.total_paid = (client.total_paid or 0) + amount

            # For round 1, ensure client is active
            if round_number == 1:
                client.client_stage = 'active'
                client.dispute_status = 'active'
                client.current_dispute_round = 1
            else:
                client.current_dispute_round = round_number

            self.db.commit()

            return {
                'success': True,
                'round_number': round_number,
                'amount_paid': amount,
                'client_stage': client.client_stage,
                'can_send_letters': True,
                'message': f'Round {round_number} payment confirmed! Letters can now be sent.'
            }

        except Exception as e:
            logger.error(f"Error confirming round payment: {str(e)}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}

    def charge_for_round(
        self,
        client_id: int,
        round_number: int,
        payment_method_id: str = None
    ) -> Dict[str, Any]:
        """
        Charge the client for a round using their saved payment method.
        Called by staff when ready to send letters.

        This is the "charge when letters sent" model.
        """
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}

            # Determine amount
            if round_number == 1:
                amount = ROUND_1_WITH_CREDIT if client.analysis_paid_at else ROUND_1_PRICE
            else:
                amount = ROUND_2_PLUS_PRICE

            # Check if client has prepaid rounds
            if client.prepay_rounds_remaining and client.prepay_rounds_remaining > 0:
                # Use prepaid round
                client.prepay_rounds_remaining -= 1
                client.current_dispute_round = round_number
                self.db.commit()

                return {
                    'success': True,
                    'round_number': round_number,
                    'used_prepaid': True,
                    'prepaid_rounds_remaining': client.prepay_rounds_remaining,
                    'can_send_letters': True,
                    'message': f'Prepaid round used. {client.prepay_rounds_remaining} rounds remaining.'
                }

            if not self.stripe:
                return {
                    'success': False,
                    'error': 'Payment system unavailable',
                    'requires_payment': True,
                    'amount': amount
                }

            # If no payment method provided, return that payment is needed
            if not payment_method_id:
                return {
                    'success': False,
                    'error': 'Payment method required',
                    'requires_payment': True,
                    'amount': amount,
                    'amount_display': f'${amount/100:.2f}'
                }

            # Charge using saved payment method
            intent = self.stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                payment_method=payment_method_id,
                confirm=True,
                off_session=True,
                metadata={
                    'client_id': str(client_id),
                    'payment_type': 'round',
                    'round_number': str(round_number),
                },
                receipt_email=client.email,
                description=f'Round {round_number} Dispute Letters - {client.name}',
            )

            if intent.status == 'succeeded':
                # Update client
                client.current_round_payment_id = intent.id
                client.last_round_paid_at = datetime.utcnow()
                client.total_paid = (client.total_paid or 0) + amount
                client.current_dispute_round = round_number
                self.db.commit()

                return {
                    'success': True,
                    'round_number': round_number,
                    'amount_paid': amount,
                    'payment_intent_id': intent.id,
                    'can_send_letters': True,
                    'message': f'Round {round_number} payment successful! Letters can be sent.'
                }
            else:
                return {
                    'success': False,
                    'error': f'Payment failed: {intent.status}',
                    'requires_action': intent.status == 'requires_action'
                }

        except Exception as e:
            logger.error(f"Error charging for round: {str(e)}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}

    def create_prepay_checkout(
        self,
        client_id: int,
        package_key: str,
        financed: bool = False,
        success_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for a prepay package.
        """
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}

            package = PREPAY_PACKAGES.get(package_key)
            if not package:
                return {'success': False, 'error': f'Invalid package: {package_key}'}

            amount = package['prepay_price']
            if financed:
                amount += FINANCING_UPCHARGE

            if not self.stripe:
                return {
                    'success': True,
                    'package': package_key,
                    'amount': amount,
                    'test_mode': True
                }

            session = self.stripe.checkout.Session.create(
                payment_method_types=['card', 'us_bank_account'],
                payment_method_options={
                    'us_bank_account': {
                        'financial_connections': {
                            'permissions': ['payment_method'],
                        },
                        'verification_method': 'instant',
                    },
                },
                mode='payment',
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': amount,
                        'product_data': {
                            'name': f'Credit Restoration - {package["name"]}',
                            'description': f'Includes {package["rounds"]} rounds of dispute letters',
                        },
                    },
                    'quantity': 1,
                }],
                metadata={
                    'client_id': str(client_id),
                    'payment_type': 'prepay',
                    'package': package_key,
                    'financed': str(financed),
                },
                customer_email=client.email,
                success_url=success_url or '/portal/onboarding?prepay=success',
                cancel_url=cancel_url or '/portal/onboarding?prepay=cancelled',
            )

            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id,
                'package': package_key,
                'amount': amount
            }

        except Exception as e:
            logger.error(f"Error creating prepay checkout: {str(e)}")
            return {'success': False, 'error': str(e)}

    def confirm_prepay_package(
        self,
        client_id: int,
        session_id: str,
        package_key: str
    ) -> Dict[str, Any]:
        """
        Confirm a prepay package purchase after Stripe checkout.
        """
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}

            package = PREPAY_PACKAGES.get(package_key)
            if not package:
                return {'success': False, 'error': f'Invalid package: {package_key}'}

            # Update client with prepaid rounds
            client.prepay_package = package_key
            client.prepay_rounds_remaining = package['rounds']
            client.total_paid = (client.total_paid or 0) + package['prepay_price']
            client.client_stage = 'onboarding'  # Move to onboarding

            self.db.commit()

            return {
                'success': True,
                'package': package_key,
                'rounds_available': package['rounds'],
                'client_stage': 'onboarding',
                'message': f'{package["name"]} activated! You have {package["rounds"]} rounds available.'
            }

        except Exception as e:
            logger.error(f"Error confirming prepay package: {str(e)}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}

    def calculate_settlement_fee(self, settlement_amount: int) -> Dict[str, Any]:
        """
        Calculate the settlement fee (30% of settlement).
        """
        fee = int(settlement_amount * (SETTLEMENT_FEE_PERCENT / 100))
        return {
            'settlement_amount': settlement_amount,
            'fee_percent': SETTLEMENT_FEE_PERCENT,
            'fee_amount': fee,
            'fee_display': f'${fee/100:,.2f}',
            'client_receives': settlement_amount - fee,
            'client_receives_display': f'${(settlement_amount - fee)/100:,.2f}'
        }

    def get_payment_summary(self, client_id: int) -> Dict[str, Any]:
        """
        Get a summary of all payments for a client.
        """
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}

            # Build payment history
            payments = []

            # Analysis payment
            if client.analysis_paid_at:
                payments.append({
                    'type': 'Analysis',
                    'amount': ANALYSIS_PRICE,
                    'date': client.analysis_paid_at.isoformat() if client.analysis_paid_at else None,
                    'status': 'paid'
                })

            # Calculate next payment
            current_round = client.current_dispute_round or 0
            next_round = current_round + 1

            if next_round == 1:
                next_amount = ROUND_1_WITH_CREDIT if client.analysis_paid_at else ROUND_1_PRICE
            else:
                next_amount = ROUND_2_PLUS_PRICE

            # Check prepaid
            has_prepaid_rounds = (client.prepay_rounds_remaining or 0) > 0

            return {
                'success': True,
                'client_id': client_id,
                'total_paid': client.total_paid or 0,
                'total_paid_display': f'${(client.total_paid or 0)/100:,.2f}',
                'payments': payments,
                'current_round': current_round,
                'next_round': next_round,
                'next_payment_amount': 0 if has_prepaid_rounds else next_amount,
                'next_payment_display': 'Prepaid' if has_prepaid_rounds else f'${next_amount/100:.2f}',
                'prepay_package': client.prepay_package,
                'prepay_rounds_remaining': client.prepay_rounds_remaining or 0,
                'analysis_credit_applied': bool(client.analysis_paid_at),
                'analysis_credit_amount': ANALYSIS_PRICE if client.analysis_paid_at else 0
            }

        except Exception as e:
            logger.error(f"Error getting payment summary: {str(e)}")
            return {'success': False, 'error': str(e)}

    def save_payment_method(
        self,
        client_id: int,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """
        Save a payment method to the client's Stripe customer record.
        Used for future charges (rounds, etc.)
        """
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}

            if not self.stripe:
                return {'success': False, 'error': 'Payment system unavailable'}

            # Get or create Stripe customer
            if not hasattr(client, 'stripe_customer_id') or not client.stripe_customer_id:
                customer = self.stripe.Customer.create(
                    email=client.email,
                    name=client.name,
                    metadata={'client_id': str(client_id)}
                )
                # Note: Would need to add stripe_customer_id column to Client model
                # For now, we'll just attach the payment method
            else:
                customer = self.stripe.Customer.retrieve(client.stripe_customer_id)

            # Attach payment method to customer
            self.stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer.id
            )

            # Set as default
            self.stripe.Customer.modify(
                customer.id,
                invoice_settings={'default_payment_method': payment_method_id}
            )

            return {
                'success': True,
                'message': 'Payment method saved successfully'
            }

        except Exception as e:
            logger.error(f"Error saving payment method: {str(e)}")
            return {'success': False, 'error': str(e)}
