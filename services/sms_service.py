"""
Twilio SMS Service for Replit Integration
Uses environment variables for Twilio credentials
"""

import os

from twilio.rest import Client as TwilioClient

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

        if messaging_service_sid:
            # Use Messaging Service (A2P 10DLC compliant)
            sms = client.messages.create(
                body=message,
                messaging_service_sid=messaging_service_sid,
                to=formatted_to
            )
            sender = f"MessagingService:{messaging_service_sid}"
        else:
            # Fall back to direct phone number
            if from_number is None:
                from_number = get_twilio_phone_number()

            if not from_number:
                return {
                    "success": False,
                    "message_sid": None,
                    "error": "No Twilio phone number or Messaging Service configured",
                }

            sms = client.messages.create(body=message, from_=from_number, to=formatted_to)
            sender = from_number

        return {
            "success": True,
            "message_sid": sms.sid,
            "error": None,
            "status": sms.status,
            "to": formatted_to,
            "from": sender,
        }

    except Exception as e:
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
