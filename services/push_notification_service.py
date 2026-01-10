"""
Push Notification Service

Web Push notifications for real-time client and staff updates.
Uses VAPID (Voluntary Application Server Identification) for authentication.

Environment Variables:
- VAPID_PUBLIC_KEY: Base64-encoded public key for push subscriptions
- VAPID_PRIVATE_KEY: Base64-encoded private key for sending notifications
- VAPID_SUBJECT: mailto: or https: URL identifying the application server

To generate VAPID keys, run:
    python -c "from services.push_notification_service import generate_vapid_keys; print(generate_vapid_keys())"
"""

import os
import json
import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Try to import pywebpush - optional dependency
try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False

# Try to import cryptography for VAPID key generation
try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# Notification types
NOTIFICATION_TYPES = {
    'case_update': {
        'title': 'Case Update',
        'icon': '/static/images/icons/case-update.png',
        'tag': 'case-update',
        'preference': 'notify_case_updates',
    },
    'message': {
        'title': 'New Message',
        'icon': '/static/images/icons/message.png',
        'tag': 'message',
        'preference': 'notify_messages',
    },
    'document': {
        'title': 'Document Update',
        'icon': '/static/images/icons/document.png',
        'tag': 'document',
        'preference': 'notify_documents',
    },
    'deadline': {
        'title': 'Deadline Reminder',
        'icon': '/static/images/icons/deadline.png',
        'tag': 'deadline',
        'preference': 'notify_deadlines',
    },
    'payment': {
        'title': 'Payment Update',
        'icon': '/static/images/icons/payment.png',
        'tag': 'payment',
        'preference': 'notify_payments',
    },
}


def get_vapid_keys() -> Dict[str, str]:
    """Get VAPID keys from environment variables"""
    return {
        'public_key': os.environ.get('VAPID_PUBLIC_KEY', ''),
        'private_key': os.environ.get('VAPID_PRIVATE_KEY', ''),
        'subject': os.environ.get('VAPID_SUBJECT', 'mailto:admin@brightpathascend.com'),
    }


def is_push_configured() -> bool:
    """Check if push notifications are properly configured"""
    keys = get_vapid_keys()
    return bool(keys['public_key'] and keys['private_key'] and WEBPUSH_AVAILABLE)


def generate_vapid_keys() -> Dict[str, str]:
    """
    Generate new VAPID keys for push notifications.

    Returns:
        Dict with 'public_key' and 'private_key' in URL-safe base64 format.
    """
    if not CRYPTO_AVAILABLE:
        return {'error': 'cryptography package not installed'}

    # Generate EC key pair on P-256 curve
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    public_key = private_key.public_key()

    # Get raw key bytes
    private_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    # Encode to URL-safe base64
    private_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
    public_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')

    return {
        'public_key': public_b64,
        'private_key': private_b64,
    }


def subscribe(
    endpoint: str,
    p256dh_key: str,
    auth_key: str,
    client_id: Optional[int] = None,
    staff_id: Optional[int] = None,
    user_agent: Optional[str] = None,
    device_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Register a new push subscription.

    Args:
        endpoint: The push service URL from the browser
        p256dh_key: Public key for message encryption
        auth_key: Authentication secret
        client_id: Associated client (for portal users)
        staff_id: Associated staff (for dashboard users)
        user_agent: Browser user agent string
        device_name: Friendly device name

    Returns:
        Dict with success status and subscription info
    """
    from database import get_db, PushSubscription

    if not client_id and not staff_id:
        return {'success': False, 'error': 'Either client_id or staff_id is required'}

    db = get_db()
    try:
        # Check if subscription already exists
        existing = db.query(PushSubscription).filter_by(endpoint=endpoint).first()

        if existing:
            # Update existing subscription
            existing.p256dh_key = p256dh_key
            existing.auth_key = auth_key
            existing.client_id = client_id
            existing.staff_id = staff_id
            existing.user_agent = user_agent
            existing.device_name = device_name or _parse_device_name(user_agent)
            existing.is_active = True
            existing.failed_count = 0
            existing.updated_at = datetime.utcnow()
            db.commit()

            return {
                'success': True,
                'subscription_id': existing.id,
                'message': 'Subscription updated',
            }

        # Create new subscription
        subscription = PushSubscription(
            endpoint=endpoint,
            p256dh_key=p256dh_key,
            auth_key=auth_key,
            client_id=client_id,
            staff_id=staff_id,
            user_agent=user_agent,
            device_name=device_name or _parse_device_name(user_agent),
        )
        db.add(subscription)
        db.commit()

        return {
            'success': True,
            'subscription_id': subscription.id,
            'message': 'Subscription created',
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def unsubscribe(endpoint: str) -> Dict[str, Any]:
    """
    Remove a push subscription.

    Args:
        endpoint: The push service URL to unsubscribe

    Returns:
        Dict with success status
    """
    from database import get_db, PushSubscription

    db = get_db()
    try:
        subscription = db.query(PushSubscription).filter_by(endpoint=endpoint).first()

        if not subscription:
            return {'success': False, 'error': 'Subscription not found'}

        db.delete(subscription)
        db.commit()

        return {'success': True, 'message': 'Subscription removed'}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def update_preferences(
    subscription_id: int,
    preferences: Dict[str, bool],
) -> Dict[str, Any]:
    """
    Update notification preferences for a subscription.

    Args:
        subscription_id: The subscription ID
        preferences: Dict of preference name to boolean value

    Returns:
        Dict with success status
    """
    from database import get_db, PushSubscription

    valid_prefs = [
        'notify_case_updates',
        'notify_messages',
        'notify_documents',
        'notify_deadlines',
        'notify_payments',
    ]

    db = get_db()
    try:
        subscription = db.query(PushSubscription).get(subscription_id)

        if not subscription:
            return {'success': False, 'error': 'Subscription not found'}

        for pref, value in preferences.items():
            if pref in valid_prefs:
                setattr(subscription, pref, bool(value))

        subscription.updated_at = datetime.utcnow()
        db.commit()

        return {'success': True, 'message': 'Preferences updated'}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def get_subscriptions(
    client_id: Optional[int] = None,
    staff_id: Optional[int] = None,
    active_only: bool = True,
) -> List[Dict[str, Any]]:
    """
    Get push subscriptions for a user.

    Args:
        client_id: Filter by client
        staff_id: Filter by staff
        active_only: Only return active subscriptions

    Returns:
        List of subscription dictionaries
    """
    from database import get_db, PushSubscription

    db = get_db()
    try:
        query = db.query(PushSubscription)

        if client_id:
            query = query.filter_by(client_id=client_id)
        if staff_id:
            query = query.filter_by(staff_id=staff_id)
        if active_only:
            query = query.filter_by(is_active=True)

        subscriptions = query.all()
        return [s.to_dict() for s in subscriptions]
    finally:
        db.close()


def send_notification(
    subscription_id: int,
    title: str,
    body: str,
    url: Optional[str] = None,
    icon: Optional[str] = None,
    tag: Optional[str] = None,
    data: Optional[Dict] = None,
    trigger_type: Optional[str] = None,
    trigger_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Send a push notification to a specific subscription.

    Args:
        subscription_id: The subscription to send to
        title: Notification title
        body: Notification body text
        url: URL to open when clicked
        icon: Icon URL
        tag: Notification tag for grouping
        data: Additional data payload
        trigger_type: What triggered this notification
        trigger_id: ID of the triggering entity

    Returns:
        Dict with success status
    """
    from database import get_db, PushSubscription, PushNotificationLog

    if not WEBPUSH_AVAILABLE:
        return {'success': False, 'error': 'pywebpush not installed'}

    vapid_keys = get_vapid_keys()
    if not vapid_keys['public_key'] or not vapid_keys['private_key']:
        return {'success': False, 'error': 'VAPID keys not configured'}

    db = get_db()
    try:
        subscription = db.query(PushSubscription).get(subscription_id)

        if not subscription:
            return {'success': False, 'error': 'Subscription not found'}

        if not subscription.is_active:
            return {'success': False, 'error': 'Subscription is inactive'}

        # Create notification log entry
        log_entry = PushNotificationLog(
            subscription_id=subscription_id,
            title=title,
            body=body,
            icon=icon,
            url=url,
            tag=tag,
            data=data,
            trigger_type=trigger_type,
            trigger_id=trigger_id,
            status='pending',
        )
        db.add(log_entry)
        db.commit()

        # Build payload
        payload = {
            'title': title,
            'body': body,
            'icon': icon or '/static/images/icons/notification.png',
            'badge': '/static/images/icons/badge.png',
            'tag': tag,
            'data': {
                'url': url or '/',
                **(data or {}),
            },
        }

        # Build subscription info for webpush
        subscription_info = {
            'endpoint': subscription.endpoint,
            'keys': {
                'p256dh': subscription.p256dh_key,
                'auth': subscription.auth_key,
            },
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=vapid_keys['private_key'],
                vapid_claims={
                    'sub': vapid_keys['subject'],
                },
            )

            # Update log entry
            log_entry.status = 'sent'
            log_entry.sent_at = datetime.utcnow()

            # Update subscription last used
            subscription.last_used_at = datetime.utcnow()
            subscription.failed_count = 0

            db.commit()

            return {'success': True, 'log_id': log_entry.id}

        except WebPushException as e:
            log_entry.status = 'failed'
            log_entry.error_message = str(e)

            # Handle subscription expiry
            if e.response and e.response.status_code in [404, 410]:
                subscription.is_active = False
                log_entry.status = 'expired'
            else:
                subscription.failed_count += 1
                # Deactivate after 5 consecutive failures
                if subscription.failed_count >= 5:
                    subscription.is_active = False

            db.commit()

            return {'success': False, 'error': str(e), 'log_id': log_entry.id}

    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def send_to_client(
    client_id: int,
    notification_type: str,
    body: str,
    url: Optional[str] = None,
    trigger_id: Optional[int] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a push notification to all of a client's subscribed devices.

    Args:
        client_id: The client to notify
        notification_type: One of the NOTIFICATION_TYPES keys
        body: Notification body text
        url: URL to open when clicked
        trigger_id: ID of the triggering entity
        title: Custom title (uses default from type if not provided)

    Returns:
        Dict with success status and sent count
    """
    from database import get_db, PushSubscription

    type_config = NOTIFICATION_TYPES.get(notification_type, {})
    preference_field = type_config.get('preference')

    db = get_db()
    try:
        # Get active subscriptions for this client
        query = db.query(PushSubscription).filter_by(
            client_id=client_id,
            is_active=True,
        )

        # Filter by notification preference if applicable
        if preference_field:
            query = query.filter(getattr(PushSubscription, preference_field) == True)

        subscriptions = query.all()

        if not subscriptions:
            return {'success': True, 'sent_count': 0, 'message': 'No active subscriptions'}

        sent_count = 0
        failed_count = 0

        for sub in subscriptions:
            result = send_notification(
                subscription_id=sub.id,
                title=title or type_config.get('title', 'Notification'),
                body=body,
                url=url,
                icon=type_config.get('icon'),
                tag=type_config.get('tag'),
                trigger_type=notification_type,
                trigger_id=trigger_id,
            )
            if result.get('success'):
                sent_count += 1
            else:
                failed_count += 1

        return {
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count,
        }
    finally:
        db.close()


def send_to_staff(
    staff_id: int,
    notification_type: str,
    body: str,
    url: Optional[str] = None,
    trigger_id: Optional[int] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a push notification to all of a staff member's subscribed devices.

    Args:
        staff_id: The staff member to notify
        notification_type: One of the NOTIFICATION_TYPES keys
        body: Notification body text
        url: URL to open when clicked
        trigger_id: ID of the triggering entity
        title: Custom title (uses default from type if not provided)

    Returns:
        Dict with success status and sent count
    """
    from database import get_db, PushSubscription

    type_config = NOTIFICATION_TYPES.get(notification_type, {})
    preference_field = type_config.get('preference')

    db = get_db()
    try:
        # Get active subscriptions for this staff
        query = db.query(PushSubscription).filter_by(
            staff_id=staff_id,
            is_active=True,
        )

        # Filter by notification preference if applicable
        if preference_field:
            query = query.filter(getattr(PushSubscription, preference_field) == True)

        subscriptions = query.all()

        if not subscriptions:
            return {'success': True, 'sent_count': 0, 'message': 'No active subscriptions'}

        sent_count = 0
        failed_count = 0

        for sub in subscriptions:
            result = send_notification(
                subscription_id=sub.id,
                title=title or type_config.get('title', 'Notification'),
                body=body,
                url=url,
                icon=type_config.get('icon'),
                tag=type_config.get('tag'),
                trigger_type=notification_type,
                trigger_id=trigger_id,
            )
            if result.get('success'):
                sent_count += 1
            else:
                failed_count += 1

        return {
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count,
        }
    finally:
        db.close()


def send_to_all_staff(
    notification_type: str,
    body: str,
    url: Optional[str] = None,
    trigger_id: Optional[int] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a push notification to all staff members.

    Args:
        notification_type: One of the NOTIFICATION_TYPES keys
        body: Notification body text
        url: URL to open when clicked
        trigger_id: ID of the triggering entity
        title: Custom title (uses default from type if not provided)

    Returns:
        Dict with success status and sent count
    """
    from database import get_db, PushSubscription

    type_config = NOTIFICATION_TYPES.get(notification_type, {})
    preference_field = type_config.get('preference')

    db = get_db()
    try:
        # Get all active staff subscriptions
        query = db.query(PushSubscription).filter(
            PushSubscription.staff_id.isnot(None),
            PushSubscription.is_active == True,
        )

        # Filter by notification preference if applicable
        if preference_field:
            query = query.filter(getattr(PushSubscription, preference_field) == True)

        subscriptions = query.all()

        if not subscriptions:
            return {'success': True, 'sent_count': 0, 'message': 'No active subscriptions'}

        sent_count = 0
        failed_count = 0

        for sub in subscriptions:
            result = send_notification(
                subscription_id=sub.id,
                title=title or type_config.get('title', 'Notification'),
                body=body,
                url=url,
                icon=type_config.get('icon'),
                tag=type_config.get('tag'),
                trigger_type=notification_type,
                trigger_id=trigger_id,
            )
            if result.get('success'):
                sent_count += 1
            else:
                failed_count += 1

        return {
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count,
        }
    finally:
        db.close()


def get_notification_logs(
    subscription_id: Optional[int] = None,
    client_id: Optional[int] = None,
    staff_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get notification logs with optional filters.

    Args:
        subscription_id: Filter by subscription
        client_id: Filter by client
        staff_id: Filter by staff
        status: Filter by status
        limit: Maximum number of logs to return

    Returns:
        List of notification log dictionaries
    """
    from database import get_db, PushNotificationLog, PushSubscription

    db = get_db()
    try:
        query = db.query(PushNotificationLog)

        if subscription_id:
            query = query.filter_by(subscription_id=subscription_id)

        if client_id or staff_id:
            query = query.join(PushSubscription)
            if client_id:
                query = query.filter(PushSubscription.client_id == client_id)
            if staff_id:
                query = query.filter(PushSubscription.staff_id == staff_id)

        if status:
            query = query.filter_by(status=status)

        logs = query.order_by(PushNotificationLog.created_at.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]
    finally:
        db.close()


def cleanup_expired_subscriptions() -> Dict[str, Any]:
    """
    Remove subscriptions that have been inactive or failed too many times.

    Returns:
        Dict with cleanup statistics
    """
    from database import get_db, PushSubscription
    from datetime import timedelta

    db = get_db()
    try:
        # Delete subscriptions inactive for 90+ days
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        old_inactive = db.query(PushSubscription).filter(
            PushSubscription.is_active == False,
            PushSubscription.updated_at < cutoff_date,
        ).all()

        deleted_count = len(old_inactive)
        for sub in old_inactive:
            db.delete(sub)

        db.commit()

        return {
            'success': True,
            'deleted_count': deleted_count,
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def _parse_device_name(user_agent: Optional[str]) -> str:
    """Parse a friendly device name from user agent string"""
    if not user_agent:
        return 'Unknown Device'

    ua = user_agent.lower()

    # Detect browser
    browser = 'Browser'
    if 'firefox' in ua:
        browser = 'Firefox'
    elif 'edg' in ua:
        browser = 'Edge'
    elif 'chrome' in ua:
        browser = 'Chrome'
    elif 'safari' in ua:
        browser = 'Safari'

    # Detect OS
    os_name = ''
    if 'windows' in ua:
        os_name = 'Windows'
    elif 'mac' in ua:
        os_name = 'Mac'
    elif 'linux' in ua:
        os_name = 'Linux'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'

    if os_name:
        return f'{browser} on {os_name}'
    return browser


# Convenience functions for workflow trigger integration
def notify_case_update(client_id: int, message: str, case_id: Optional[int] = None) -> Dict[str, Any]:
    """Send a case update notification to a client"""
    return send_to_client(
        client_id=client_id,
        notification_type='case_update',
        body=message,
        url=f'/portal/dashboard' if not case_id else f'/portal/case/{case_id}',
        trigger_id=case_id,
    )


def notify_new_message(client_id: int, sender_name: str, message_preview: str) -> Dict[str, Any]:
    """Send a new message notification to a client"""
    return send_to_client(
        client_id=client_id,
        notification_type='message',
        body=f'{sender_name}: {message_preview[:100]}',
        url='/portal/messages',
    )


def notify_document_ready(client_id: int, document_name: str, doc_id: Optional[int] = None) -> Dict[str, Any]:
    """Send a document ready notification to a client"""
    return send_to_client(
        client_id=client_id,
        notification_type='document',
        body=f'New document available: {document_name}',
        url='/portal/documents',
        trigger_id=doc_id,
    )


def notify_deadline_approaching(client_id: int, deadline_name: str, days_remaining: int) -> Dict[str, Any]:
    """Send a deadline reminder notification to a client"""
    return send_to_client(
        client_id=client_id,
        notification_type='deadline',
        body=f'{deadline_name} is due in {days_remaining} day{"s" if days_remaining != 1 else ""}',
        url='/portal/dashboard',
    )


def notify_payment_reminder(client_id: int, amount: float, due_date: str) -> Dict[str, Any]:
    """Send a payment reminder notification to a client"""
    return send_to_client(
        client_id=client_id,
        notification_type='payment',
        body=f'Payment of ${amount:.2f} is due on {due_date}',
        url='/portal/subscription',
    )


def notify_staff_new_upload(client_name: str, document_type: str) -> Dict[str, Any]:
    """Notify all staff about a new client document upload"""
    return send_to_all_staff(
        notification_type='document',
        body=f'{client_name} uploaded a new {document_type}',
        url='/dashboard/documents',
        title='New Client Upload',
    )


def notify_staff_new_message(client_name: str, message_preview: str) -> Dict[str, Any]:
    """Notify all staff about a new client message"""
    return send_to_all_staff(
        notification_type='message',
        body=f'{client_name}: {message_preview[:100]}',
        url='/dashboard/messaging',
        title='New Client Message',
    )
