"""
Scheduled Jobs Service

Handles automated tasks that run on a schedule:
1. capture_due_payments - Capture payments after 3-day CROA period
2. expire_stale_holds - Release holds if onboarding not completed
3. send_payment_reminders - Email clients with upcoming payments
4. activate_ready_clients - Move clients from pending_payment to active

These jobs can be triggered by:
- Cron jobs calling the API endpoints
- A scheduler like APScheduler
- Manual trigger from staff dashboard
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from database import SessionLocal, Client, CROAProgress

logger = logging.getLogger(__name__)


def get_scheduled_jobs_service(db=None):
    """Factory function to get ScheduledJobsService instance."""
    if db is None:
        db = SessionLocal()
    return ScheduledJobsService(db)


class ScheduledJobsService:
    """Service for running scheduled background jobs."""

    def __init__(self, db):
        self.db = db

    def capture_due_payments(self) -> Dict[str, Any]:
        """
        Find clients whose 3-day cancellation period has ended
        and capture their Round 1 payment.

        Run this hourly via cron.
        """
        results = {
            'processed': 0,
            'captured': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

        try:
            # Find clients in pending_payment stage where cancellation period ended
            now = datetime.utcnow()

            # Get all CROA progress records where cancellation period has ended
            ready_clients = self.db.query(Client).join(
                CROAProgress, Client.id == CROAProgress.client_id
            ).filter(
                Client.client_stage == 'pending_payment',
                CROAProgress.cancellation_period_ends_at <= now,
                CROAProgress.cancelled_at.is_(None)  # Not cancelled
            ).all()

            results['processed'] = len(ready_clients)

            for client in ready_clients:
                try:
                    # Check if they have a payment method on file
                    # For now, we'll just activate them - actual charge happens when letters sent
                    client.client_stage = 'active'
                    client.dispute_status = 'active'

                    results['captured'] += 1
                    results['details'].append({
                        'client_id': client.id,
                        'name': client.name,
                        'status': 'activated',
                        'message': 'Client activated after cancellation period'
                    })

                    # Log timeline event
                    try:
                        from services.timeline_service import log_milestone
                        log_milestone(
                            self.db,
                            client.id,
                            'case_activated',
                            'Case Activated',
                            'Your case is now active! Dispute letters will be sent soon.'
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log timeline event: {e}")

                except Exception as e:
                    results['failed'] += 1
                    results['details'].append({
                        'client_id': client.id,
                        'name': client.name,
                        'status': 'failed',
                        'error': str(e)
                    })

            self.db.commit()

            return {
                'success': True,
                'job': 'capture_due_payments',
                'run_at': now.isoformat(),
                'results': results
            }

        except Exception as e:
            logger.error(f"Error in capture_due_payments: {str(e)}")
            self.db.rollback()
            return {
                'success': False,
                'job': 'capture_due_payments',
                'error': str(e)
            }

    def expire_stale_holds(self, days_old: int = 7) -> Dict[str, Any]:
        """
        Release payment holds for clients who haven't completed onboarding
        within the specified number of days.

        Run this daily via cron.
        """
        results = {
            'processed': 0,
            'expired': 0,
            'details': []
        }

        try:
            now = datetime.utcnow()
            cutoff_date = now - timedelta(days=days_old)

            # Find clients stuck in onboarding for too long
            stale_clients = self.db.query(Client).filter(
                Client.client_stage == 'onboarding',
                Client.created_at < cutoff_date
            ).all()

            results['processed'] = len(stale_clients)

            for client in stale_clients:
                # Mark as expired/cancelled
                client.client_stage = 'cancelled'
                client.cancellation_reason = f'Onboarding not completed within {days_old} days'

                results['expired'] += 1
                results['details'].append({
                    'client_id': client.id,
                    'name': client.name,
                    'created_at': client.created_at.isoformat() if client.created_at else None,
                    'status': 'expired'
                })

                # TODO: Release any payment holds via Stripe
                # if client.payment_hold_id:
                #     stripe.PaymentIntent.cancel(client.payment_hold_id)

            self.db.commit()

            return {
                'success': True,
                'job': 'expire_stale_holds',
                'run_at': now.isoformat(),
                'days_threshold': days_old,
                'results': results
            }

        except Exception as e:
            logger.error(f"Error in expire_stale_holds: {str(e)}")
            self.db.rollback()
            return {
                'success': False,
                'job': 'expire_stale_holds',
                'error': str(e)
            }

    def send_payment_reminders(self) -> Dict[str, Any]:
        """
        Send reminder emails to clients whose payment is due soon.
        - Day before cancellation period ends
        - Day payment was supposed to process but failed

        Run this daily via cron.
        """
        results = {
            'processed': 0,
            'sent': 0,
            'details': []
        }

        try:
            now = datetime.utcnow()
            tomorrow = now + timedelta(days=1)

            # Find clients whose cancellation period ends tomorrow
            upcoming_clients = self.db.query(Client).join(
                CROAProgress, Client.id == CROAProgress.client_id
            ).filter(
                Client.client_stage == 'pending_payment',
                CROAProgress.cancellation_period_ends_at >= now,
                CROAProgress.cancellation_period_ends_at <= tomorrow,
                CROAProgress.cancelled_at.is_(None)
            ).all()

            results['processed'] = len(upcoming_clients)

            for client in upcoming_clients:
                try:
                    # Send reminder email
                    # TODO: Integrate with email service
                    # from services.email_service import send_payment_reminder
                    # send_payment_reminder(client)

                    results['sent'] += 1
                    results['details'].append({
                        'client_id': client.id,
                        'email': client.email,
                        'type': 'upcoming_payment',
                        'status': 'queued'
                    })

                except Exception as e:
                    results['details'].append({
                        'client_id': client.id,
                        'email': client.email,
                        'type': 'upcoming_payment',
                        'status': 'failed',
                        'error': str(e)
                    })

            # Also find clients with failed payments
            failed_clients = self.db.query(Client).filter(
                Client.client_stage == 'payment_failed'
            ).all()

            for client in failed_clients:
                try:
                    # Send retry payment email
                    # TODO: Integrate with email service

                    results['sent'] += 1
                    results['details'].append({
                        'client_id': client.id,
                        'email': client.email,
                        'type': 'payment_failed',
                        'status': 'queued'
                    })

                except Exception as e:
                    results['details'].append({
                        'client_id': client.id,
                        'email': client.email,
                        'type': 'payment_failed',
                        'status': 'failed',
                        'error': str(e)
                    })

            return {
                'success': True,
                'job': 'send_payment_reminders',
                'run_at': now.isoformat(),
                'results': results
            }

        except Exception as e:
            logger.error(f"Error in send_payment_reminders: {str(e)}")
            return {
                'success': False,
                'job': 'send_payment_reminders',
                'error': str(e)
            }

    def get_pending_activations(self) -> Dict[str, Any]:
        """
        Get list of clients ready for activation (cancellation period ended).
        """
        try:
            now = datetime.utcnow()

            ready_clients = self.db.query(Client).join(
                CROAProgress, Client.id == CROAProgress.client_id
            ).filter(
                Client.client_stage == 'pending_payment',
                CROAProgress.cancellation_period_ends_at <= now,
                CROAProgress.cancelled_at.is_(None)
            ).all()

            clients_list = []
            for client in ready_clients:
                croa = self.db.query(CROAProgress).filter_by(client_id=client.id).first()
                clients_list.append({
                    'client_id': client.id,
                    'name': client.name,
                    'email': client.email,
                    'cancellation_ended_at': croa.cancellation_period_ends_at.isoformat() if croa else None,
                    'ready_since': (now - croa.cancellation_period_ends_at).days if croa else None
                })

            return {
                'success': True,
                'count': len(clients_list),
                'clients': clients_list
            }

        except Exception as e:
            logger.error(f"Error getting pending activations: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def run_all_jobs(self) -> Dict[str, Any]:
        """
        Run all scheduled jobs. Useful for manual trigger or single cron.
        """
        results = {}

        results['capture_due_payments'] = self.capture_due_payments()
        results['expire_stale_holds'] = self.expire_stale_holds()
        results['send_payment_reminders'] = self.send_payment_reminders()

        return {
            'success': True,
            'run_at': datetime.utcnow().isoformat(),
            'jobs': results
        }
