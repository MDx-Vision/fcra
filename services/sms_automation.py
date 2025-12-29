"""
SMS Automation Triggers for Brightpath Ascend FCRA Platform
These functions are called at key workflow points to send automated SMS notifications.
"""

from datetime import datetime, timedelta

from .sms_service import format_phone_number, is_twilio_configured, send_sms
from .sms_templates import (
    analysis_ready_sms,
    appointment_reminder_sms,
    case_update_sms,
    cra_response_sms,
    custom_sms,
    dispute_sent_sms,
    document_reminder_sms,
    document_uploaded_sms,
    letters_ready_sms,
    payment_reminder_sms,
    round_started_sms,
    welcome_sms,
)


def get_sms_settings(db):
    """
    Get SMS settings from database.
    Returns dict with all SMS setting values.
    """
    from database import SignupSettings

    defaults = {
        "sms_enabled": False,
        "welcome_sms_enabled": True,
        "document_reminder_enabled": True,
        "case_update_enabled": True,
        "dispute_sent_enabled": True,
        "cra_response_enabled": True,
        "payment_reminder_enabled": True,
        "reminder_delay_hours": 24,
    }

    settings = {}
    for key, default in defaults.items():
        try:
            setting = (
                db.query(SignupSettings).filter_by(setting_key=f"sms_{key}").first()
            )
            if setting:
                if isinstance(default, bool):
                    settings[key] = setting.setting_value.lower() == "true"
                elif isinstance(default, int):
                    settings[key] = int(setting.setting_value)
                else:
                    settings[key] = setting.setting_value
            else:
                settings[key] = default
        except Exception:
            settings[key] = default

    return settings


def log_sms(
    db,
    client_id,
    phone_number,
    message,
    template_type,
    success,
    message_sid=None,
    error=None,
):
    """
    Log an SMS send attempt to the database.
    """
    from database import SMSLog

    try:
        log = SMSLog(
            client_id=client_id,
            phone_number=phone_number,
            message=message[:1000] if message else "",
            template_type=template_type,
            status="sent" if success else "failed",
            twilio_sid=message_sid,
            sent_at=datetime.utcnow(),
            error_message=error,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to log SMS: {e}")


def get_client_phone(db, client_id):
    """
    Get a valid phone number for a client.
    Tries mobile first, then phone, then phone_2.
    """
    from database import Client

    client = db.query(Client).filter_by(id=client_id).first()
    if not client:
        return None, None

    phone = client.mobile or client.phone or client.phone_2
    formatted = format_phone_number(phone) if phone else None

    return formatted, client


def trigger_welcome_sms(db, client_id):
    """
    Send welcome SMS when new client signs up.
    Called after successful signup completion.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled") or not settings.get("welcome_sms_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    message = welcome_sms(client.name)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "welcome",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def trigger_document_reminder(db, client_id, doc_type="required documents"):
    """
    Send document reminder when documents are missing.
    Called for clients missing docs after reminder_delay_hours.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled") or not settings.get("document_reminder_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    message = document_reminder_sms(client.name, doc_type)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "document_reminder",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def trigger_case_update(db, client_id, new_status):
    """
    Send case status update notification.
    Called when case moves to a new stage.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled") or not settings.get("case_update_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    message = case_update_sms(client.name, new_status)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "case_update",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def trigger_dispute_sent(db, client_id, bureau):
    """
    Send notification when dispute letter is sent.
    Called when dispute letter is mailed or electronically sent.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled") or not settings.get("dispute_sent_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    message = dispute_sent_sms(client.name, bureau)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "dispute_sent",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def trigger_cra_response(db, client_id, bureau):
    """
    Send notification when CRA response is uploaded.
    Called when bureau response document is received.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled") or not settings.get("cra_response_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    message = cra_response_sms(client.name, bureau)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "cra_response",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def trigger_payment_reminder(db, client_id, amount=None):
    """
    Send payment reminder for pending balance.
    Called when payment is pending > 3 days.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled") or not settings.get("payment_reminder_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    if amount is None and client.signup_amount:
        amount = client.signup_amount / 100
    elif amount is None:
        amount = "pending"

    message = payment_reminder_sms(client.name, amount)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "payment_reminder",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def trigger_analysis_ready(db, client_id):
    """
    Send notification when credit analysis is ready.
    Called when Stage 1 analysis is complete.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled") or not settings.get("case_update_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    message = analysis_ready_sms(client.name)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "analysis_ready",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def trigger_letters_ready(db, client_id, letter_count):
    """
    Send notification when dispute letters are generated.
    Called when Stage 2 letters are ready.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled") or not settings.get("case_update_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    message = letters_ready_sms(client.name, letter_count)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "letters_ready",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def trigger_round_started(db, client_id, round_number):
    """
    Send notification when a new dispute round starts.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled") or not settings.get("case_update_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    message = round_started_sms(client.name, round_number)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "round_started",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def send_custom_sms(db, client_id, message_text):
    """
    Send a custom SMS to a client.
    For admin-initiated messages.
    """
    settings = get_sms_settings(db)

    if not settings.get("sms_enabled"):
        return {"sent": False, "reason": "SMS disabled"}

    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    phone, client = get_client_phone(db, client_id)
    if not phone:
        return {"sent": False, "reason": "No valid phone number"}

    message = custom_sms(client.name, message_text)
    result = send_sms(phone, message)

    log_sms(
        db,
        client_id,
        phone,
        message,
        "custom",
        result["success"],
        result.get("message_sid"),
        result.get("error"),
    )

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def send_test_sms(phone_number, test_message=None):
    """
    Send a test SMS to verify Twilio configuration.
    Does not require a client or logging.
    """
    if not is_twilio_configured():
        return {"sent": False, "reason": "Twilio not configured"}

    if test_message is None:
        test_message = (
            "This is a test message from Brightpath Ascend. "
            "SMS notifications are working correctly!"
        )

    result = send_sms(phone_number, test_message)

    return {
        "sent": result["success"],
        "message_sid": result.get("message_sid"),
        "error": result.get("error"),
    }


def get_clients_needing_document_reminder(db, hours=24):
    """
    Get list of clients who need document reminders.
    Returns clients signed up > hours ago with missing documents.
    """
    from database import Client, ClientDocument

    cutoff = datetime.utcnow() - timedelta(hours=hours)

    clients_with_missing_docs = (
        db.query(Client)
        .filter(
            Client.created_at < cutoff,
            Client.status.in_(["signup", "active"]),
            Client.phone.isnot(None),
        )
        .all()
    )

    clients_needing_reminder = []

    for client in clients_with_missing_docs:
        docs = db.query(ClientDocument).filter_by(client_id=client.id).all()
        missing_docs = [d for d in docs if not d.received]

        if missing_docs:
            doc_types = [d.document_type for d in missing_docs]
            clients_needing_reminder.append(
                {"client": client, "missing_docs": doc_types}
            )

    return clients_needing_reminder


def get_clients_needing_payment_reminder(db, days=3):
    """
    Get list of clients who need payment reminders.
    Returns clients with pending payment for > days.
    """
    from database import Client

    cutoff = datetime.utcnow() - timedelta(days=days)

    clients = (
        db.query(Client)
        .filter(
            Client.created_at < cutoff,
            Client.payment_status == "pending",
            Client.payment_pending == True,
            Client.phone.isnot(None),
        )
        .all()
    )

    return clients
