"""
Unit tests for StripeWebhooksService

Tests all Stripe webhook event handlers:
- payment_intent.succeeded
- payment_intent.payment_failed
- charge.refunded
- checkout.session.completed
"""

import pytest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from services.stripe_webhooks_service import (
    StripeWebhooksService,
    get_stripe_webhooks_service,
    HANDLED_EVENTS,
)


class TestConstants:
    """Tests for webhook constants."""

    def test_handled_events_defined(self):
        """Test all expected events are in handled events list."""
        assert 'payment_intent.succeeded' in HANDLED_EVENTS
        assert 'payment_intent.payment_failed' in HANDLED_EVENTS
        assert 'charge.refunded' in HANDLED_EVENTS
        assert 'checkout.session.completed' in HANDLED_EVENTS

    def test_handled_events_count(self):
        """Test the count of handled events."""
        assert len(HANDLED_EVENTS) == 4


class TestServiceInit:
    """Tests for StripeWebhooksService initialization."""

    def test_init_with_db_session(self):
        """Test initialization with database session."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)
        assert service.db == mock_db

    def test_factory_function(self):
        """Test the factory function creates service instance."""
        with patch('services.stripe_webhooks_service.SessionLocal') as mock_session:
            mock_db = MagicMock(spec=Session)
            mock_session.return_value = mock_db
            service = get_stripe_webhooks_service()
            assert isinstance(service, StripeWebhooksService)

    def test_factory_function_with_db(self):
        """Test factory function with provided database."""
        mock_db = MagicMock(spec=Session)
        service = get_stripe_webhooks_service(mock_db)
        assert service.db == mock_db


class TestHandleEvent:
    """Tests for the main handle_event routing method."""

    def test_routes_to_correct_handler(self):
        """Test events are routed to correct handlers."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_handle_payment_succeeded') as mock_handler:
            mock_handler.return_value = {'processed': True}

            event = {
                'type': 'payment_intent.succeeded',
                'id': 'evt_123',
                'data': {'object': {}}
            }

            result = service.handle_event(event)

            mock_handler.assert_called_once()
            assert result['success'] == True
            assert result['event_type'] == 'payment_intent.succeeded'

    def test_unhandled_event_acknowledged(self):
        """Test unhandled events are acknowledged but not processed."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'unknown.event.type',
            'id': 'evt_unknown',
            'data': {'object': {}}
        }

        result = service.handle_event(event)

        assert result['success'] == True
        assert result['message'] == 'Event type not handled'

    def test_handler_exception_returns_error(self):
        """Test handler exceptions are caught and returned."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_handle_payment_succeeded') as mock_handler:
            mock_handler.side_effect = Exception("Handler error")

            event = {
                'type': 'payment_intent.succeeded',
                'id': 'evt_123',
                'data': {'object': {}}
            }

            result = service.handle_event(event)

            assert result['success'] == False
            assert 'Handler error' in result['error']


class TestPaymentSucceeded:
    """Tests for _handle_payment_succeeded method."""

    def test_analysis_payment_updates_client(self):
        """Test analysis payment updates client stage."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            event = {
                'type': 'payment_intent.succeeded',
                'id': 'evt_123',
                'data': {
                    'object': {
                        'id': 'pi_analysis',
                        'amount': 19900,
                        'metadata': {
                            'client_id': '1',
                            'payment_type': 'analysis'
                        }
                    }
                }
            }

            result = service.handle_event(event)

        assert result['success'] == True
        assert mock_client.client_stage == 'analysis_paid'
        assert mock_client.analysis_payment_id == 'pi_analysis'
        assert mock_client.total_paid == 19900
        assert mock_client.round_1_amount_due == 29800

    def test_round_payment_updates_client(self):
        """Test round payment updates client."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 19900
        mock_client.client_stage = 'pending_payment'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            event = {
                'type': 'payment_intent.succeeded',
                'id': 'evt_123',
                'data': {
                    'object': {
                        'id': 'pi_r1',
                        'amount': 29800,
                        'metadata': {
                            'client_id': '1',
                            'payment_type': 'round',
                            'round_number': '1'
                        }
                    }
                }
            }

            result = service.handle_event(event)

        assert result['success'] == True
        assert mock_client.client_stage == 'active'
        assert mock_client.dispute_status == 'active'
        assert mock_client.current_dispute_round == 1

    def test_round_2_payment_updates_round(self):
        """Test Round 2 payment updates round number only."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 49700
        mock_client.client_stage = 'active'
        mock_client.current_dispute_round = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            event = {
                'type': 'payment_intent.succeeded',
                'id': 'evt_123',
                'data': {
                    'object': {
                        'id': 'pi_r2',
                        'amount': 29700,
                        'metadata': {
                            'client_id': '1',
                            'payment_type': 'round',
                            'round_number': '2'
                        }
                    }
                }
            }

            result = service.handle_event(event)

        assert mock_client.current_dispute_round == 2
        # Stage should remain 'active', not change
        assert mock_client.client_stage == 'active'

    def test_prepay_payment_activates_package(self):
        """Test prepay payment activates package."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            with patch('services.stripe_webhooks_service.PREPAY_PACKAGES', {
                'standard': {'name': 'Standard Package', 'rounds': 4}
            }):
                event = {
                    'type': 'payment_intent.succeeded',
                    'id': 'evt_123',
                    'data': {
                        'object': {
                            'id': 'pi_prepay',
                            'amount': 129500,
                            'metadata': {
                                'client_id': '1',
                                'payment_type': 'prepay',
                                'package': 'standard'
                            }
                        }
                    }
                }

                result = service.handle_event(event)

        assert result['success'] == True
        assert mock_client.prepay_package == 'standard'
        assert mock_client.prepay_rounds_remaining == 4
        assert mock_client.client_stage == 'onboarding'

    def test_no_client_id_in_metadata(self):
        """Test handling when no client_id in metadata."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'payment_intent.succeeded',
            'id': 'evt_123',
            'data': {
                'object': {
                    'id': 'pi_no_client',
                    'amount': 19900,
                    'metadata': {
                        'payment_type': 'analysis'
                    }
                }
            }
        }

        result = service.handle_event(event)

        assert result['success'] == True
        assert 'No client_id' in result['result']['message']

    def test_client_not_found(self):
        """Test handling when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'payment_intent.succeeded',
            'id': 'evt_123',
            'data': {
                'object': {
                    'id': 'pi_123',
                    'amount': 19900,
                    'metadata': {
                        'client_id': '999',
                        'payment_type': 'analysis'
                    }
                }
            }
        }

        result = service.handle_event(event)

        assert result['success'] == True
        assert 'not found' in result['result']['error']

    def test_unknown_payment_type(self):
        """Test handling unknown payment type."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'payment_intent.succeeded',
            'id': 'evt_123',
            'data': {
                'object': {
                    'id': 'pi_unknown',
                    'amount': 10000,
                    'metadata': {
                        'client_id': '1',
                        'payment_type': 'unknown_type'
                    }
                }
            }
        }

        result = service.handle_event(event)

        assert result['success'] == True
        assert 'Unknown payment_type' in result['result']['message']


class TestPaymentFailed:
    """Tests for _handle_payment_failed method."""

    def test_updates_client_stage_to_failed(self):
        """Test payment failure updates client stage."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.client_stage = 'pending_payment'
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            with patch('services.stripe_webhooks_service.send_payment_failed_email'):
                event = {
                    'type': 'payment_intent.payment_failed',
                    'id': 'evt_fail',
                    'data': {
                        'object': {
                            'id': 'pi_failed',
                            'metadata': {
                                'client_id': '1',
                                'payment_type': 'round'
                            },
                            'last_payment_error': {
                                'message': 'Card declined'
                            }
                        }
                    }
                }

                result = service.handle_event(event)

        assert result['success'] == True
        assert mock_client.client_stage == 'payment_failed'

    def test_sends_failure_email(self):
        """Test payment failure sends email notification."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.client_stage = 'pending_payment'
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test Client'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            with patch('services.stripe_webhooks_service.send_payment_failed_email') as mock_email:
                event = {
                    'type': 'payment_intent.payment_failed',
                    'id': 'evt_fail',
                    'data': {
                        'object': {
                            'id': 'pi_failed',
                            'metadata': {
                                'client_id': '1',
                                'payment_type': 'round'
                            },
                            'last_payment_error': {
                                'message': 'Insufficient funds'
                            }
                        }
                    }
                }

                result = service.handle_event(event)

                mock_email.assert_called_once_with(
                    client_email='test@example.com',
                    client_name='Test Client',
                    error_message='Insufficient funds'
                )

    def test_no_client_id_in_metadata(self):
        """Test handling when no client_id in metadata."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'payment_intent.payment_failed',
            'id': 'evt_fail',
            'data': {
                'object': {
                    'id': 'pi_no_client',
                    'metadata': {},
                    'last_payment_error': {}
                }
            }
        }

        result = service.handle_event(event)

        assert result['success'] == True
        assert 'No client_id' in result['result']['message']


class TestRefund:
    """Tests for _handle_refund method."""

    def test_adjusts_total_paid(self):
        """Test refund adjusts client's total paid."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 50000
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            event = {
                'type': 'charge.refunded',
                'id': 'evt_refund',
                'data': {
                    'object': {
                        'id': 'ch_123',
                        'amount_refunded': 19900,
                        'metadata': {
                            'client_id': '1'
                        }
                    }
                }
            }

            result = service.handle_event(event)

        assert result['success'] == True
        assert mock_client.total_paid == 30100  # 50000 - 19900

    def test_total_paid_not_negative(self):
        """Test refund doesn't make total_paid negative."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 10000
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch.object(service, '_log_timeline'):
            event = {
                'type': 'charge.refunded',
                'id': 'evt_refund',
                'data': {
                    'object': {
                        'id': 'ch_123',
                        'amount_refunded': 50000,  # More than total_paid
                        'metadata': {
                            'client_id': '1'
                        }
                    }
                }
            }

            result = service.handle_event(event)

        assert mock_client.total_paid == 0  # max(0, 10000-50000)

    def test_no_client_id_in_metadata(self):
        """Test handling when no client_id in metadata."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'charge.refunded',
            'id': 'evt_refund',
            'data': {
                'object': {
                    'id': 'ch_123',
                    'amount_refunded': 19900,
                    'metadata': {}
                }
            }
        }

        result = service.handle_event(event)

        assert result['success'] == True
        assert 'No client_id' in result['result']['message']


class TestCheckoutCompleted:
    """Tests for _handle_checkout_completed method."""

    def test_prepay_checkout_activates_package(self):
        """Test prepay checkout completion activates package."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        with patch('services.stripe_webhooks_service.PREPAY_PACKAGES', {
            'complete': {'name': 'Complete Package', 'rounds': 6}
        }):
            event = {
                'type': 'checkout.session.completed',
                'id': 'evt_checkout',
                'data': {
                    'object': {
                        'id': 'sess_123',
                        'metadata': {
                            'client_id': '1',
                            'payment_type': 'prepay',
                            'package': 'complete'
                        }
                    }
                }
            }

            result = service.handle_event(event)

        assert result['success'] == True
        assert mock_client.prepay_package == 'complete'
        assert mock_client.prepay_rounds_remaining == 6
        assert mock_client.client_stage == 'onboarding'

    def test_non_prepay_checkout(self):
        """Test non-prepay checkout is acknowledged."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'checkout.session.completed',
            'id': 'evt_checkout',
            'data': {
                'object': {
                    'id': 'sess_123',
                    'metadata': {
                        'payment_type': 'subscription'
                    }
                }
            }
        }

        result = service.handle_event(event)

        assert result['success'] == True
        assert 'Checkout completed' in result['result']['message']


class TestLogTimeline:
    """Tests for _log_timeline helper method."""

    def test_timeline_event_logged(self):
        """Test timeline events are logged correctly."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)

        with patch('services.stripe_webhooks_service.get_timeline_service') as mock_get_timeline:
            mock_timeline = MagicMock()
            mock_get_timeline.return_value = mock_timeline

            service._log_timeline(
                client_id=1,
                event_type='payment_received',
                title='Payment Received',
                description='$199 received'
            )

            mock_timeline.add_event.assert_called_once_with(
                client_id=1,
                event_type='payment_received',
                title='Payment Received',
                description='$199 received',
                category='payment'
            )

    def test_timeline_failure_does_not_raise(self):
        """Test timeline logging failure is caught."""
        mock_db = MagicMock(spec=Session)
        service = StripeWebhooksService(mock_db)

        with patch('services.stripe_webhooks_service.get_timeline_service') as mock_get_timeline:
            mock_get_timeline.side_effect = Exception("Timeline error")

            # Should not raise
            service._log_timeline(
                client_id=1,
                event_type='payment_received',
                title='Test',
                description='Test'
            )


class TestIdempotency:
    """Tests for webhook idempotency handling."""

    def test_same_event_processed_consistently(self):
        """Test processing same event twice produces consistent results."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'payment_intent.succeeded',
            'id': 'evt_123',
            'data': {
                'object': {
                    'id': 'pi_analysis',
                    'amount': 19900,
                    'metadata': {
                        'client_id': '1',
                        'payment_type': 'analysis'
                    }
                }
            }
        }

        with patch.object(service, '_log_timeline'):
            result1 = service.handle_event(event)

            # Reset for second call
            mock_client.total_paid = 19900
            result2 = service.handle_event(event)

        # Both should succeed (idempotent)
        assert result1['success'] == True
        assert result2['success'] == True


class TestEventDataExtraction:
    """Tests for correct event data extraction."""

    def test_extracts_payment_intent_data(self):
        """Test payment intent data is extracted correctly."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.total_paid = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'payment_intent.succeeded',
            'id': 'evt_123',
            'data': {
                'object': {
                    'id': 'pi_test',
                    'amount': 29800,
                    'metadata': {
                        'client_id': '1',
                        'payment_type': 'round',
                        'round_number': '1'
                    }
                }
            }
        }

        with patch.object(service, '_log_timeline'):
            result = service.handle_event(event)

        assert result['result']['amount'] == 29800
        assert result['result']['round_number'] == 1

    def test_handles_missing_error_message(self):
        """Test handles missing error message in payment failure."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.client_stage = 'pending_payment'
        mock_client.email = 'test@example.com'
        mock_client.name = 'Test'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = StripeWebhooksService(mock_db)

        event = {
            'type': 'payment_intent.payment_failed',
            'id': 'evt_fail',
            'data': {
                'object': {
                    'id': 'pi_failed',
                    'metadata': {
                        'client_id': '1',
                        'payment_type': 'round'
                    },
                    'last_payment_error': {}  # No message
                }
            }
        }

        with patch.object(service, '_log_timeline'):
            with patch('services.stripe_webhooks_service.send_payment_failed_email'):
                result = service.handle_event(event)

        assert result['success'] == True
        assert result['result']['error'] == 'Unknown error'
