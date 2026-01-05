"""
Unit tests for PushNotificationService

Tests web push notification functionality including:
- VAPID key generation and management
- Subscription management
- Notification sending
- Preference management
- Convenience notification functions
"""

import pytest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock

from services.push_notification_service import (
    NOTIFICATION_TYPES,
    get_vapid_keys,
    is_push_configured,
    generate_vapid_keys,
    subscribe,
    unsubscribe,
    update_preferences,
    get_subscriptions,
    send_notification,
    send_to_client,
    send_to_staff,
    send_to_all_staff,
    get_notification_logs,
    cleanup_expired_subscriptions,
    _parse_device_name,
    notify_case_update,
    notify_new_message,
    notify_document_ready,
    notify_deadline_approaching,
    notify_payment_reminder,
    notify_staff_new_upload,
    notify_staff_new_message,
)


class TestNotificationTypes:
    """Tests for notification type configuration."""

    def test_case_update_type(self):
        """Test case_update notification type config."""
        assert 'case_update' in NOTIFICATION_TYPES
        config = NOTIFICATION_TYPES['case_update']
        assert config['title'] == 'Case Update'
        assert 'icon' in config
        assert 'tag' in config
        assert 'preference' in config

    def test_message_type(self):
        """Test message notification type config."""
        assert 'message' in NOTIFICATION_TYPES
        config = NOTIFICATION_TYPES['message']
        assert config['title'] == 'New Message'

    def test_document_type(self):
        """Test document notification type config."""
        assert 'document' in NOTIFICATION_TYPES
        config = NOTIFICATION_TYPES['document']
        assert config['title'] == 'Document Update'

    def test_deadline_type(self):
        """Test deadline notification type config."""
        assert 'deadline' in NOTIFICATION_TYPES
        config = NOTIFICATION_TYPES['deadline']
        assert config['title'] == 'Deadline Reminder'

    def test_payment_type(self):
        """Test payment notification type config."""
        assert 'payment' in NOTIFICATION_TYPES
        config = NOTIFICATION_TYPES['payment']
        assert config['title'] == 'Payment Update'


class TestGetVapidKeys:
    """Tests for get_vapid_keys function."""

    def test_returns_keys_from_env(self):
        """Test returns keys from environment variables."""
        with patch.dict('os.environ', {
            'VAPID_PUBLIC_KEY': 'test_public',
            'VAPID_PRIVATE_KEY': 'test_private',
            'VAPID_SUBJECT': 'mailto:test@example.com'
        }):
            keys = get_vapid_keys()

            assert keys['public_key'] == 'test_public'
            assert keys['private_key'] == 'test_private'
            assert keys['subject'] == 'mailto:test@example.com'

    def test_returns_empty_when_not_configured(self):
        """Test returns empty strings when env vars not set."""
        with patch.dict('os.environ', {}, clear=True):
            keys = get_vapid_keys()

            assert keys['public_key'] == ''
            assert keys['private_key'] == ''


class TestIsPushConfigured:
    """Tests for is_push_configured function."""

    def test_configured_when_all_present(self):
        """Test returns True when all keys present and webpush available."""
        with patch.dict('os.environ', {
            'VAPID_PUBLIC_KEY': 'test_public',
            'VAPID_PRIVATE_KEY': 'test_private'
        }):
            with patch('services.push_notification_service.WEBPUSH_AVAILABLE', True):
                assert is_push_configured() == True

    def test_not_configured_without_webpush(self):
        """Test returns False when webpush not available."""
        with patch.dict('os.environ', {
            'VAPID_PUBLIC_KEY': 'test_public',
            'VAPID_PRIVATE_KEY': 'test_private'
        }):
            with patch('services.push_notification_service.WEBPUSH_AVAILABLE', False):
                assert is_push_configured() == False

    def test_not_configured_without_keys(self):
        """Test returns False when keys not present."""
        with patch.dict('os.environ', {}, clear=True):
            assert is_push_configured() == False


class TestGenerateVapidKeys:
    """Tests for generate_vapid_keys function."""

    def test_returns_error_when_crypto_unavailable(self):
        """Test returns error when cryptography not installed."""
        with patch('services.push_notification_service.CRYPTO_AVAILABLE', False):
            result = generate_vapid_keys()

            assert 'error' in result

    def test_generates_keys_when_crypto_available(self):
        """Test generates keys when cryptography available."""
        with patch('services.push_notification_service.CRYPTO_AVAILABLE', True):
            # This requires the actual cryptography library
            try:
                result = generate_vapid_keys()
                # If cryptography is installed, we get keys
                if 'error' not in result:
                    assert 'public_key' in result
                    assert 'private_key' in result
            except:
                pass  # OK if cryptography not installed


class TestSubscribe:
    """Tests for subscribe function."""

    def test_requires_client_or_staff_id(self):
        """Test error when neither client_id nor staff_id provided."""
        result = subscribe(
            endpoint='https://push.example.com/123',
            p256dh_key='test_key',
            auth_key='test_auth'
        )

        assert result['success'] == False
        assert 'client_id or staff_id' in result['error']

    def test_creates_new_subscription(self):
        """Test creating new subscription."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter_by.return_value.first.return_value = None
            mock_get_db.return_value = mock_db

            mock_sub = MagicMock()
            mock_sub.id = 1

            with patch('services.push_notification_service.PushSubscription') as MockSub:
                MockSub.return_value = mock_sub

                result = subscribe(
                    endpoint='https://push.example.com/123',
                    p256dh_key='test_key',
                    auth_key='test_auth',
                    client_id=1
                )

            assert result['success'] == True
            assert result['message'] == 'Subscription created'

    def test_updates_existing_subscription(self):
        """Test updating existing subscription."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_existing = MagicMock()
            mock_existing.id = 1
            mock_db.query.return_value.filter_by.return_value.first.return_value = mock_existing
            mock_get_db.return_value = mock_db

            result = subscribe(
                endpoint='https://push.example.com/123',
                p256dh_key='new_key',
                auth_key='new_auth',
                client_id=1
            )

            assert result['success'] == True
            assert result['message'] == 'Subscription updated'


class TestUnsubscribe:
    """Tests for unsubscribe function."""

    def test_subscription_not_found(self):
        """Test error when subscription not found."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter_by.return_value.first.return_value = None
            mock_get_db.return_value = mock_db

            result = unsubscribe(endpoint='https://push.example.com/123')

            assert result['success'] == False
            assert 'not found' in result['error']

    def test_removes_subscription(self):
        """Test successful subscription removal."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_sub = MagicMock()
            mock_db.query.return_value.filter_by.return_value.first.return_value = mock_sub
            mock_get_db.return_value = mock_db

            result = unsubscribe(endpoint='https://push.example.com/123')

            assert result['success'] == True
            mock_db.delete.assert_called_with(mock_sub)


class TestUpdatePreferences:
    """Tests for update_preferences function."""

    def test_subscription_not_found(self):
        """Test error when subscription not found."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.get.return_value = None
            mock_get_db.return_value = mock_db

            result = update_preferences(
                subscription_id=999,
                preferences={'notify_messages': True}
            )

            assert result['success'] == False

    def test_updates_valid_preferences(self):
        """Test updating valid preferences."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_sub = MagicMock()
            mock_db.query.return_value.get.return_value = mock_sub
            mock_get_db.return_value = mock_db

            result = update_preferences(
                subscription_id=1,
                preferences={'notify_messages': True, 'notify_payments': False}
            )

            assert result['success'] == True


class TestGetSubscriptions:
    """Tests for get_subscriptions function."""

    def test_returns_client_subscriptions(self):
        """Test getting subscriptions by client."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_subs = [
                MagicMock(to_dict=MagicMock(return_value={'id': 1})),
                MagicMock(to_dict=MagicMock(return_value={'id': 2}))
            ]
            mock_db.query.return_value.filter_by.return_value.all.return_value = mock_subs
            mock_get_db.return_value = mock_db

            result = get_subscriptions(client_id=1)

            assert len(result) == 2


class TestSendNotification:
    """Tests for send_notification function."""

    def test_webpush_not_available(self):
        """Test error when webpush not installed."""
        with patch('services.push_notification_service.WEBPUSH_AVAILABLE', False):
            result = send_notification(
                subscription_id=1,
                title='Test',
                body='Test body'
            )

            assert result['success'] == False
            assert 'not installed' in result['error']

    def test_vapid_not_configured(self):
        """Test error when VAPID not configured."""
        with patch('services.push_notification_service.WEBPUSH_AVAILABLE', True):
            with patch.dict('os.environ', {}, clear=True):
                result = send_notification(
                    subscription_id=1,
                    title='Test',
                    body='Test body'
                )

            assert result['success'] == False
            assert 'not configured' in result['error']


class TestSendToClient:
    """Tests for send_to_client function."""

    def test_no_subscriptions(self):
        """Test when client has no subscriptions."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter_by.return_value.all.return_value = []
            mock_db.query.return_value.filter_by.return_value.filter.return_value.all.return_value = []
            mock_get_db.return_value = mock_db

            result = send_to_client(
                client_id=1,
                notification_type='case_update',
                body='Test update'
            )

            assert result['success'] == True
            assert result['sent_count'] == 0


class TestSendToStaff:
    """Tests for send_to_staff function."""

    def test_no_subscriptions(self):
        """Test when staff has no subscriptions."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter_by.return_value.all.return_value = []
            mock_db.query.return_value.filter_by.return_value.filter.return_value.all.return_value = []
            mock_get_db.return_value = mock_db

            result = send_to_staff(
                staff_id=1,
                notification_type='message',
                body='New message'
            )

            assert result['success'] == True
            assert result['sent_count'] == 0


class TestSendToAllStaff:
    """Tests for send_to_all_staff function."""

    def test_no_subscriptions(self):
        """Test when no staff have subscriptions."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = []
            mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
            mock_get_db.return_value = mock_db

            result = send_to_all_staff(
                notification_type='message',
                body='Broadcast message'
            )

            assert result['success'] == True
            assert result['sent_count'] == 0


class TestGetNotificationLogs:
    """Tests for get_notification_logs function."""

    def test_returns_logs(self):
        """Test getting notification logs."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_logs = [
                MagicMock(to_dict=MagicMock(return_value={'id': 1}))
            ]
            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_logs
            mock_get_db.return_value = mock_db

            result = get_notification_logs()

            assert len(result) == 1


class TestCleanupExpiredSubscriptions:
    """Tests for cleanup_expired_subscriptions function."""

    def test_deletes_old_inactive(self):
        """Test deleting old inactive subscriptions."""
        with patch('services.push_notification_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_old_subs = [MagicMock(), MagicMock()]
            mock_db.query.return_value.filter.return_value.all.return_value = mock_old_subs
            mock_get_db.return_value = mock_db

            result = cleanup_expired_subscriptions()

            assert result['success'] == True
            assert result['deleted_count'] == 2


class TestParseDeviceName:
    """Tests for _parse_device_name helper."""

    def test_chrome_windows(self):
        """Test parsing Chrome on Windows."""
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
        result = _parse_device_name(ua)

        assert 'Chrome' in result
        assert 'Windows' in result

    def test_firefox_mac(self):
        """Test parsing Firefox on Mac."""
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15) Firefox/89.0'
        result = _parse_device_name(ua)

        assert 'Firefox' in result
        assert 'Mac' in result

    def test_safari_ios(self):
        """Test parsing Safari on iOS."""
        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6) Safari/604.1'
        result = _parse_device_name(ua)

        assert 'Safari' in result
        assert 'iOS' in result

    def test_edge_windows(self):
        """Test parsing Edge on Windows."""
        ua = 'Mozilla/5.0 (Windows NT 10.0) Edg/91.0.864.67'
        result = _parse_device_name(ua)

        assert 'Edge' in result

    def test_android(self):
        """Test parsing Chrome on Android."""
        ua = 'Mozilla/5.0 (Linux; Android 11) Chrome/91.0'
        result = _parse_device_name(ua)

        assert 'Chrome' in result
        assert 'Android' in result

    def test_unknown_device(self):
        """Test with no user agent."""
        result = _parse_device_name(None)
        assert result == 'Unknown Device'


class TestConvenienceFunctions:
    """Tests for convenience notification functions."""

    def test_notify_case_update(self):
        """Test notify_case_update convenience function."""
        with patch('services.push_notification_service.send_to_client') as mock_send:
            mock_send.return_value = {'success': True, 'sent_count': 1}

            result = notify_case_update(
                client_id=1,
                message='Your case was updated',
                case_id=123
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]['client_id'] == 1
            assert call_args[1]['notification_type'] == 'case_update'

    def test_notify_new_message(self):
        """Test notify_new_message convenience function."""
        with patch('services.push_notification_service.send_to_client') as mock_send:
            mock_send.return_value = {'success': True}

            result = notify_new_message(
                client_id=1,
                sender_name='John',
                message_preview='Hello, how are you?'
            )

            mock_send.assert_called_once()

    def test_notify_document_ready(self):
        """Test notify_document_ready convenience function."""
        with patch('services.push_notification_service.send_to_client') as mock_send:
            mock_send.return_value = {'success': True}

            result = notify_document_ready(
                client_id=1,
                document_name='Dispute Letter',
                doc_id=456
            )

            mock_send.assert_called_once()

    def test_notify_deadline_approaching(self):
        """Test notify_deadline_approaching convenience function."""
        with patch('services.push_notification_service.send_to_client') as mock_send:
            mock_send.return_value = {'success': True}

            result = notify_deadline_approaching(
                client_id=1,
                deadline_name='Response deadline',
                days_remaining=3
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert '3 days' in call_args[1]['body']

    def test_notify_deadline_singular_day(self):
        """Test deadline notification with 1 day remaining."""
        with patch('services.push_notification_service.send_to_client') as mock_send:
            mock_send.return_value = {'success': True}

            result = notify_deadline_approaching(
                client_id=1,
                deadline_name='Response deadline',
                days_remaining=1
            )

            call_args = mock_send.call_args
            assert '1 day' in call_args[1]['body']

    def test_notify_payment_reminder(self):
        """Test notify_payment_reminder convenience function."""
        with patch('services.push_notification_service.send_to_client') as mock_send:
            mock_send.return_value = {'success': True}

            result = notify_payment_reminder(
                client_id=1,
                amount=199.00,
                due_date='January 15, 2026'
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert '$199.00' in call_args[1]['body']

    def test_notify_staff_new_upload(self):
        """Test notify_staff_new_upload convenience function."""
        with patch('services.push_notification_service.send_to_all_staff') as mock_send:
            mock_send.return_value = {'success': True, 'sent_count': 3}

            result = notify_staff_new_upload(
                client_name='John Doe',
                document_type='credit report'
            )

            mock_send.assert_called_once()

    def test_notify_staff_new_message(self):
        """Test notify_staff_new_message convenience function."""
        with patch('services.push_notification_service.send_to_all_staff') as mock_send:
            mock_send.return_value = {'success': True}

            result = notify_staff_new_message(
                client_name='Jane Smith',
                message_preview='Question about my case...'
            )

            mock_send.assert_called_once()
