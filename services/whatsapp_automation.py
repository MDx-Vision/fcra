"""
WhatsApp Automation Service

Handles outbound WhatsApp notifications using Twilio Content Templates.
Mirrors the SMS automation pattern but for WhatsApp-specific use cases.

NOTE: All outbound messages (except replies within 24hr window) require
pre-approved Twilio Content Templates. Template SIDs must be configured
after Meta/WhatsApp approval.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from .sms_service import (
    format_whatsapp_number,
    get_twilio_client,
    get_whatsapp_number,
    is_whatsapp_configured,
    send_whatsapp,
    send_whatsapp_template,
)

# Template SIDs - Replace with your approved Twilio Content Template SIDs
# See: https://www.twilio.com/docs/content
WHATSAPP_TEMPLATES = {
    "document_request": "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # TODO: Replace after approval
    "status_update": "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "letters_ready": "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "document_received": "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "verification_code": "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "welcome": "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
}

# Document type display names
DOCUMENT_TYPES = {
    "drivers_license": "Driver's License",
    "ssn_card": "Social Security Card",
    "utility_bill": "Utility Bill",
    "credit_report": "Credit Report",
    "cra_response": "CRA Response Letter",
    "id_document": "Government ID",
    "other": "Document",
}


def check_whatsapp_opt_in(client) -> bool:
    """
    Check if client has opted in to WhatsApp notifications.

    Returns True only if:
    - whatsapp_opt_in is True
    - whatsapp_verified is True
    - whatsapp_number is set
    """
    if not client:
        return False
    return bool(
        getattr(client, "whatsapp_opt_in", False)
        and getattr(client, "whatsapp_verified", False)
        and getattr(client, "whatsapp_number", None)
    )


def get_whatsapp_settings(db) -> Dict[str, Any]:
    """
    Get WhatsApp automation settings from database.
    """
    from database import SignupSettings

    defaults = {
        "whatsapp_enabled": False,
        "document_request_enabled": True,
        "status_update_enabled": True,
        "letters_ready_enabled": True,
    }

    settings = {}
    for key, default in defaults.items():
        try:
            setting = (
                db.query(SignupSettings)
                .filter_by(setting_key=f"whatsapp_{key}")
                .first()
            )
            if setting:
                if isinstance(default, bool):
                    settings[key] = setting.setting_value.lower() == "true"
                else:
                    settings[key] = setting.setting_value
            else:
                settings[key] = default
        except Exception:
            settings[key] = default

    return settings


def log_whatsapp_message(
    db,
    client_id: int,
    direction: str,
    to_number: str,
    body: str,
    template_name: str = None,
    template_variables: dict = None,
    twilio_sid: str = None,
    status: str = "sent",
    error: str = None,
) -> Optional[int]:
    """
    Log a WhatsApp message to the database.

    Returns the message ID or None if logging failed.
    """
    from database import WhatsAppMessage

    try:
        from_number = get_whatsapp_number() if direction == "outbound" else to_number

        message = WhatsAppMessage(
            client_id=client_id,
            twilio_sid=twilio_sid,
            direction=direction,
            from_number=from_number if direction == "outbound" else to_number,
            to_number=to_number if direction == "outbound" else from_number,
            body=body[:2000] if body else "",
            template_name=template_name,
            template_variables=template_variables,
            status=status,
            error_message=error,
            created_at=datetime.utcnow(),
        )
        db.add(message)
        db.commit()
        return message.id
    except Exception as e:
        db.rollback()
        print(f"Failed to log WhatsApp message: {e}")
        return None


def get_client_whatsapp_number(db, client_id: int) -> Optional[str]:
    """
    Get a client's verified WhatsApp number.
    """
    from database import Client

    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if client and check_whatsapp_opt_in(client):
            return client.whatsapp_number
        return None
    except Exception:
        return None


def trigger_whatsapp_document_request(
    db, client_id: int, document_type: str, custom_message: str = ""
) -> Dict[str, Any]:
    """
    Send a document request via WhatsApp.

    Args:
        db: Database session
        client_id: Client ID
        document_type: Type of document to request (e.g., 'drivers_license')
        custom_message: Optional custom message to include

    Returns:
        dict with 'success', 'sent', 'reason', 'message_sid'
    """
    from database import Client

    # Check configuration
    if not is_whatsapp_configured():
        return {"success": False, "sent": False, "reason": "WhatsApp not configured"}

    # Get settings
    settings = get_whatsapp_settings(db)
    if not settings.get("whatsapp_enabled"):
        return {
            "success": False,
            "sent": False,
            "reason": "WhatsApp automation disabled",
        }

    if not settings.get("document_request_enabled"):
        return {
            "success": False,
            "sent": False,
            "reason": "Document request notifications disabled",
        }

    # Get client
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return {"success": False, "sent": False, "reason": "Client not found"}

    # Check opt-in
    if not check_whatsapp_opt_in(client):
        return {
            "success": False,
            "sent": False,
            "reason": "Client not opted in for WhatsApp",
        }

    # Get client name
    first_name = client.first_name or (
        client.name.split()[0] if client.name else "there"
    )

    # Get document type display name
    doc_display = DOCUMENT_TYPES.get(document_type, document_type)

    # Build message (using template or plain text for 24hr window)
    template_sid = WHATSAPP_TEMPLATES.get("document_request")
    template_vars = None

    if template_sid and not template_sid.startswith("HXx"):  # Template configured
        template_vars = {"1": first_name, "2": doc_display}
        result = send_whatsapp_template(
            to_number=client.whatsapp_number,
            template_sid=template_sid,
            template_variables=template_vars,
        )
    else:
        # Fall back to plain message (only works within 24hr reply window)
        message = f"Hi {first_name}, we need your {doc_display} to continue processing your case.\n\nPlease reply with a photo. Questions? Reply HELP."
        if custom_message:
            message += f"\n\n{custom_message}"
        result = send_whatsapp(to_number=client.whatsapp_number, message=message)

    # Log the message
    log_whatsapp_message(
        db=db,
        client_id=client_id,
        direction="outbound",
        to_number=client.whatsapp_number,
        body=f"Document request: {doc_display}",
        template_name="document_request",
        template_variables=template_vars,
        twilio_sid=result.get("message_sid"),
        status="sent" if result.get("success") else "failed",
        error=result.get("error"),
    )

    if result.get("success"):
        return {"success": True, "sent": True, "message_sid": result.get("message_sid")}
    else:
        return {
            "success": False,
            "sent": False,
            "reason": result.get("error", "Failed to send WhatsApp message"),
        }


def trigger_whatsapp_status_update(
    db, client_id: int, status_message: str
) -> Dict[str, Any]:
    """
    Send a status update via WhatsApp.

    Args:
        db: Database session
        client_id: Client ID
        status_message: Status update text

    Returns:
        dict with 'success', 'sent', 'reason', 'message_sid'
    """
    from database import Client

    if not is_whatsapp_configured():
        return {"success": False, "sent": False, "reason": "WhatsApp not configured"}

    settings = get_whatsapp_settings(db)
    if not settings.get("whatsapp_enabled"):
        return {
            "success": False,
            "sent": False,
            "reason": "WhatsApp automation disabled",
        }

    if not settings.get("status_update_enabled"):
        return {
            "success": False,
            "sent": False,
            "reason": "Status update notifications disabled",
        }

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return {"success": False, "sent": False, "reason": "Client not found"}

    if not check_whatsapp_opt_in(client):
        return {
            "success": False,
            "sent": False,
            "reason": "Client not opted in for WhatsApp",
        }

    first_name = client.first_name or (
        client.name.split()[0] if client.name else "there"
    )

    template_sid = WHATSAPP_TEMPLATES.get("status_update")
    template_vars = None

    if template_sid and not template_sid.startswith("HXx"):
        template_vars = {"1": first_name, "2": status_message}
        result = send_whatsapp_template(
            to_number=client.whatsapp_number,
            template_sid=template_sid,
            template_variables=template_vars,
        )
    else:
        message = f"Hi {first_name}, your credit repair case update: {status_message}\n\nLog in to your portal for details."
        result = send_whatsapp(to_number=client.whatsapp_number, message=message)

    log_whatsapp_message(
        db=db,
        client_id=client_id,
        direction="outbound",
        to_number=client.whatsapp_number,
        body=f"Status update: {status_message}",
        template_name="status_update",
        template_variables=template_vars,
        twilio_sid=result.get("message_sid"),
        status="sent" if result.get("success") else "failed",
        error=result.get("error"),
    )

    if result.get("success"):
        return {"success": True, "sent": True, "message_sid": result.get("message_sid")}
    else:
        return {"success": False, "sent": False, "reason": result.get("error")}


def trigger_whatsapp_letters_ready(
    db, client_id: int, letter_count: int
) -> Dict[str, Any]:
    """
    Notify client that dispute letters are ready.

    Args:
        db: Database session
        client_id: Client ID
        letter_count: Number of letters ready

    Returns:
        dict with 'success', 'sent', 'reason', 'message_sid'
    """
    from database import Client

    if not is_whatsapp_configured():
        return {"success": False, "sent": False, "reason": "WhatsApp not configured"}

    settings = get_whatsapp_settings(db)
    if not settings.get("whatsapp_enabled"):
        return {
            "success": False,
            "sent": False,
            "reason": "WhatsApp automation disabled",
        }

    if not settings.get("letters_ready_enabled"):
        return {
            "success": False,
            "sent": False,
            "reason": "Letters ready notifications disabled",
        }

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return {"success": False, "sent": False, "reason": "Client not found"}

    if not check_whatsapp_opt_in(client):
        return {
            "success": False,
            "sent": False,
            "reason": "Client not opted in for WhatsApp",
        }

    first_name = client.first_name or (
        client.name.split()[0] if client.name else "there"
    )
    count_str = str(letter_count)

    template_sid = WHATSAPP_TEMPLATES.get("letters_ready")
    template_vars = None

    if template_sid and not template_sid.startswith("HXx"):
        template_vars = {"1": first_name, "2": count_str}
        result = send_whatsapp_template(
            to_number=client.whatsapp_number,
            template_sid=template_sid,
            template_variables=template_vars,
        )
    else:
        message = f"Hi {first_name}, great news! {letter_count} dispute letters are ready.\n\nCheck your portal to review and approve."
        result = send_whatsapp(to_number=client.whatsapp_number, message=message)

    log_whatsapp_message(
        db=db,
        client_id=client_id,
        direction="outbound",
        to_number=client.whatsapp_number,
        body=f"Letters ready: {letter_count} dispute letters",
        template_name="letters_ready",
        template_variables=template_vars,
        twilio_sid=result.get("message_sid"),
        status="sent" if result.get("success") else "failed",
        error=result.get("error"),
    )

    if result.get("success"):
        return {"success": True, "sent": True, "message_sid": result.get("message_sid")}
    else:
        return {"success": False, "sent": False, "reason": result.get("error")}


def trigger_whatsapp_document_received(
    db, client_id: int, document_type: str = None
) -> Dict[str, Any]:
    """
    Confirm document receipt via WhatsApp.

    Args:
        db: Database session
        client_id: Client ID
        document_type: Optional document type for specific confirmation

    Returns:
        dict with 'success', 'sent', 'reason', 'message_sid'
    """
    from database import Client

    if not is_whatsapp_configured():
        return {"success": False, "sent": False, "reason": "WhatsApp not configured"}

    settings = get_whatsapp_settings(db)
    if not settings.get("whatsapp_enabled"):
        return {
            "success": False,
            "sent": False,
            "reason": "WhatsApp automation disabled",
        }

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return {"success": False, "sent": False, "reason": "Client not found"}

    if not check_whatsapp_opt_in(client):
        return {
            "success": False,
            "sent": False,
            "reason": "Client not opted in for WhatsApp",
        }

    first_name = client.first_name or (
        client.name.split()[0] if client.name else "there"
    )

    template_sid = WHATSAPP_TEMPLATES.get("document_received")
    template_vars = None

    if template_sid and not template_sid.startswith("HXx"):
        template_vars = {"1": first_name}
        result = send_whatsapp_template(
            to_number=client.whatsapp_number,
            template_sid=template_sid,
            template_variables=template_vars,
        )
    else:
        message = f"Hi {first_name}, we received your document.\n\nOur team will review it shortly."
        result = send_whatsapp(to_number=client.whatsapp_number, message=message)

    log_whatsapp_message(
        db=db,
        client_id=client_id,
        direction="outbound",
        to_number=client.whatsapp_number,
        body=f"Document received confirmation",
        template_name="document_received",
        template_variables=template_vars,
        twilio_sid=result.get("message_sid"),
        status="sent" if result.get("success") else "failed",
        error=result.get("error"),
    )

    if result.get("success"):
        return {"success": True, "sent": True, "message_sid": result.get("message_sid")}
    else:
        return {"success": False, "sent": False, "reason": result.get("error")}


def send_custom_whatsapp(db, client_id: int, message_text: str) -> Dict[str, Any]:
    """
    Send a custom WhatsApp message to a client.

    NOTE: Only works within 24hr reply window unless using approved template.

    Args:
        db: Database session
        client_id: Client ID
        message_text: Custom message text

    Returns:
        dict with 'success', 'sent', 'reason', 'message_sid'
    """
    from database import Client

    if not is_whatsapp_configured():
        return {"success": False, "sent": False, "reason": "WhatsApp not configured"}

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return {"success": False, "sent": False, "reason": "Client not found"}

    if not check_whatsapp_opt_in(client):
        return {
            "success": False,
            "sent": False,
            "reason": "Client not opted in for WhatsApp",
        }

    result = send_whatsapp(to_number=client.whatsapp_number, message=message_text)

    log_whatsapp_message(
        db=db,
        client_id=client_id,
        direction="outbound",
        to_number=client.whatsapp_number,
        body=message_text,
        template_name="custom",
        twilio_sid=result.get("message_sid"),
        status="sent" if result.get("success") else "failed",
        error=result.get("error"),
    )

    if result.get("success"):
        return {"success": True, "sent": True, "message_sid": result.get("message_sid")}
    else:
        return {"success": False, "sent": False, "reason": result.get("error")}
