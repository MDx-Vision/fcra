"""
Twilio SMS & WhatsApp Service for Replit Integration
Uses environment variables for Twilio credentials

Supports:
- SMS via Twilio (A2P 10DLC compliant)
- WhatsApp via Twilio WhatsApp Business API

Includes retry logic for transient failures.
"""

import logging
import os

from twilio.rest import Client as TwilioClient

from services.activity_logger import log_sms_failed, log_sms_sent
from services.retry_service import retry_twilio
from services.circuit_breaker_service import circuit_protected, CircuitBreakerError

logger = logging.getLogger(__name__)

_twilio_client = None


def get_twilio_credentials():
    """
    Get Twilio credentials from environment variables.
    Returns dict with account_sid, auth_token, phone_number, messaging_service_sid.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
    messaging_service_sid = os.environ.get("TWILIO_MESSAGING_SERVICE_SID")

    if not account_sid or not auth_token:
        raise ValueError(
            "Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables."
        )

    return {
        "account_sid": account_sid,
        "auth_token": auth_token,
        "phone_number": phone_number,
        "messaging_service_sid": messaging_service_sid,
    }


def get_twilio_client():
    """
    Get a configured Twilio client.
    Returns a TwilioClient instance.
    """
    global _twilio_client

    if _twilio_client is None:
        creds = get_twilio_credentials()
        _twilio_client = TwilioClient(creds["account_sid"], creds["auth_token"])

    return _twilio_client


def get_twilio_phone_number():
    """Get the configured Twilio phone number for sending SMS."""
    return os.environ.get("TWILIO_PHONE_NUMBER")


def get_messaging_service_sid():
    """Get the configured Twilio Messaging Service SID for A2P 10DLC compliance."""
    return os.environ.get("TWILIO_MESSAGING_SERVICE_SID")


def format_phone_number(phone):
    """
    Format phone number to E.164 format for Twilio.
    Handles various input formats.
    """
    if not phone:
        return None

    digits = "".join(filter(str.isdigit, str(phone)))

    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    elif len(digits) > 10 and not digits.startswith("1"):
        return f"+{digits}"
    elif phone.startswith("+"):
        return phone

    return None


@circuit_protected("twilio")
@retry_twilio(max_attempts=3)
def _send_sms_with_retry(client, to_number, message, messaging_service_sid=None, from_number=None):
    """
    Internal function to send SMS with circuit breaker and retry logic.
    Separated to allow retry on transient Twilio failures.
    """
    if messaging_service_sid:
        sms = client.messages.create(
            body=message,
            messaging_service_sid=messaging_service_sid,
            to=to_number,
        )
        sender = f"MessagingService:{messaging_service_sid}"
    else:
        sms = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number,
        )
        sender = from_number

    return sms, sender


def send_sms(to_number, message, from_number=None):
    """
    Send a single SMS message.

    Args:
        to_number: Recipient phone number (any format, will be normalized)
        message: Message body (max 1600 characters for long SMS)
        from_number: Optional sender number (defaults to configured Twilio number)
                    Ignored if TWILIO_MESSAGING_SERVICE_SID is configured (uses A2P 10DLC)

    Returns:
        dict with 'success', 'message_sid', 'error' keys

    Note: Includes automatic retry for transient Twilio API failures.
    """
    try:
        formatted_to = format_phone_number(to_number)
        if not formatted_to:
            return {
                "success": False,
                "message_sid": None,
                "error": f"Invalid phone number format: {to_number}",
            }

        client = get_twilio_client()

        # Prefer Messaging Service for A2P 10DLC compliance
        messaging_service_sid = get_messaging_service_sid()

        if not messaging_service_sid:
            # Fall back to direct phone number
            if from_number is None:
                from_number = get_twilio_phone_number()

            if not from_number:
                return {
                    "success": False,
                    "message_sid": None,
                    "error": "No Twilio phone number or Messaging Service configured",
                }

        # Use retry-enabled helper for the actual API call
        logger.debug(f"Sending SMS to {formatted_to}")
        sms, sender = _send_sms_with_retry(
            client, formatted_to, message,
            messaging_service_sid=messaging_service_sid,
            from_number=from_number
        )

        log_sms_sent(formatted_to)
        logger.info(f"SMS sent successfully to {formatted_to}, SID: {sms.sid}")
        return {
            "success": True,
            "message_sid": sms.sid,
            "error": None,
            "status": sms.status,
            "to": formatted_to,
            "from": sender,
        }

    except Exception as e:
        log_sms_failed(to_number, str(e))
        return {"success": False, "message_sid": None, "error": str(e)}


def send_bulk_sms(recipients, message):
    """
    Send SMS to multiple recipients.

    Args:
        recipients: List of phone numbers
        message: Message body

    Returns:
        dict with 'total', 'sent', 'failed', 'results' keys
    """
    results = []
    sent_count = 0
    failed_count = 0

    for phone in recipients:
        result = send_sms(phone, message)
        results.append(
            {
                "phone": phone,
                "success": result["success"],
                "message_sid": result.get("message_sid"),
                "error": result.get("error"),
            }
        )

        if result["success"]:
            sent_count += 1
        else:
            failed_count += 1

    return {
        "total": len(recipients),
        "sent": sent_count,
        "failed": failed_count,
        "results": results,
    }


def get_sms_status(message_sid):
    """
    Get the delivery status of a sent SMS.

    Args:
        message_sid: Twilio message SID

    Returns:
        dict with status info
    """
    try:
        client = get_twilio_client()
        message = client.messages(message_sid).fetch()

        return {
            "success": True,
            "status": message.status,
            "error_code": message.error_code,
            "error_message": message.error_message,
            "date_sent": message.date_sent,
            "date_updated": message.date_updated,
        }
    except Exception as e:
        return {"success": False, "status": "unknown", "error": str(e)}


def is_twilio_configured():
    """
    Check if Twilio credentials are configured and valid.
    Returns True if configured, False otherwise.
    """
    try:
        creds = get_twilio_credentials()
        return bool(
            creds.get("account_sid")
            and creds.get("auth_token")
            and creds.get("phone_number")
        )
    except Exception:
        return False


# =============================================================================
# WhatsApp Functions (via Twilio WhatsApp Business API)
# =============================================================================


def get_whatsapp_number():
    """
    Get the configured Twilio WhatsApp number.
    Must be a WhatsApp-enabled Twilio number in format: whatsapp:+1234567890
    """
    number = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    if number and not number.startswith("whatsapp:"):
        number = f"whatsapp:{number}"
    return number


def format_whatsapp_number(phone):
    """
    Format phone number for WhatsApp (whatsapp:+E.164 format).
    """
    formatted = format_phone_number(phone)
    if formatted:
        return f"whatsapp:{formatted}"
    return None


@circuit_protected("twilio")
@retry_twilio(max_attempts=3)
def _send_whatsapp_with_retry(client, to_number, message, from_number):
    """
    Internal function to send WhatsApp with circuit breaker and retry logic.
    """
    return client.messages.create(body=message, from_=from_number, to=to_number)


def send_whatsapp(to_number, message, from_number=None):
    """
    Send a WhatsApp message via Twilio.

    Args:
        to_number: Recipient phone number (any format, will be normalized)
        message: Message body
        from_number: Optional WhatsApp sender number (defaults to configured number)

    Returns:
        dict with 'success', 'message_sid', 'error' keys

    Note: For template messages (required for business-initiated conversations),
    use send_whatsapp_template() instead.
    Includes automatic retry for transient Twilio API failures.
    """
    try:
        formatted_to = format_whatsapp_number(to_number)
        if not formatted_to:
            return {
                "success": False,
                "message_sid": None,
                "error": f"Invalid phone number format: {to_number}",
            }

        if from_number is None:
            from_number = get_whatsapp_number()

        if not from_number:
            return {
                "success": False,
                "message_sid": None,
                "error": "No WhatsApp number configured. Set TWILIO_WHATSAPP_NUMBER.",
            }

        # Ensure from_number has whatsapp: prefix
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"

        client = get_twilio_client()

        logger.debug(f"Sending WhatsApp message to {formatted_to}")
        msg = _send_whatsapp_with_retry(client, formatted_to, message, from_number)
        logger.info(f"WhatsApp sent successfully to {formatted_to}, SID: {msg.sid}")

        return {
            "success": True,
            "message_sid": msg.sid,
            "error": None,
            "status": msg.status,
            "to": formatted_to,
            "from": from_number,
            "channel": "whatsapp",
        }

    except Exception as e:
        return {"success": False, "message_sid": None, "error": str(e)}


def send_whatsapp_template(
    to_number, template_sid, template_variables=None, from_number=None
):
    """
    Send a WhatsApp template message (for business-initiated conversations).

    Args:
        to_number: Recipient phone number
        template_sid: Twilio Content Template SID (e.g., HXxxxxx)
        template_variables: Dict of variables to substitute in template
        from_number: Optional WhatsApp sender number

    Returns:
        dict with 'success', 'message_sid', 'error' keys

    Note: Templates must be pre-approved by WhatsApp/Meta.
    """
    try:
        formatted_to = format_whatsapp_number(to_number)
        if not formatted_to:
            return {
                "success": False,
                "message_sid": None,
                "error": f"Invalid phone number format: {to_number}",
            }

        if from_number is None:
            from_number = get_whatsapp_number()

        if not from_number:
            return {
                "success": False,
                "message_sid": None,
                "error": "No WhatsApp number configured.",
            }

        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"

        client = get_twilio_client()

        # Build content variables if provided
        content_variables = {}
        if template_variables:
            for i, (key, value) in enumerate(template_variables.items(), 1):
                content_variables[str(i)] = str(value)

        msg = client.messages.create(
            content_sid=template_sid,
            content_variables=content_variables if content_variables else None,
            from_=from_number,
            to=formatted_to,
        )

        return {
            "success": True,
            "message_sid": msg.sid,
            "error": None,
            "status": msg.status,
            "to": formatted_to,
            "from": from_number,
            "channel": "whatsapp",
            "template_sid": template_sid,
        }

    except Exception as e:
        return {"success": False, "message_sid": None, "error": str(e)}


def send_bulk_whatsapp(recipients, message):
    """
    Send WhatsApp message to multiple recipients.

    Args:
        recipients: List of phone numbers
        message: Message body

    Returns:
        dict with 'total', 'sent', 'failed', 'results' keys
    """
    results = []
    sent_count = 0
    failed_count = 0

    for phone in recipients:
        result = send_whatsapp(phone, message)
        results.append(
            {
                "phone": phone,
                "success": result["success"],
                "message_sid": result.get("message_sid"),
                "error": result.get("error"),
            }
        )

        if result["success"]:
            sent_count += 1
        else:
            failed_count += 1

    return {
        "total": len(recipients),
        "sent": sent_count,
        "failed": failed_count,
        "results": results,
        "channel": "whatsapp",
    }


def is_whatsapp_configured():
    """
    Check if WhatsApp is configured.
    Returns True if configured, False otherwise.
    """
    try:
        creds = get_twilio_credentials()
        whatsapp_number = get_whatsapp_number()
        return bool(
            creds.get("account_sid") and creds.get("auth_token") and whatsapp_number
        )
    except Exception:
        return False


def send_message(
    to_number, message, channel="sms", template_sid=None, template_variables=None
):
    """
    Universal message sender - routes to SMS or WhatsApp based on channel.

    Args:
        to_number: Recipient phone number
        message: Message body (ignored if template_sid provided for WhatsApp)
        channel: "sms" or "whatsapp"
        template_sid: For WhatsApp templates only
        template_variables: For WhatsApp templates only

    Returns:
        dict with 'success', 'message_sid', 'channel', 'error' keys
    """
    if channel == "whatsapp":
        if template_sid:
            return send_whatsapp_template(to_number, template_sid, template_variables)
        return send_whatsapp(to_number, message)
    else:
        return send_sms(to_number, message)
