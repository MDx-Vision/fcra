"""
SMS Message Templates for Brightpath Ascend FCRA Platform
All templates are designed to be under 160 characters for single SMS when possible
"""

COMPANY_NAME = "Brightpath Ascend Group"
REPLY_STOP = "Reply STOP to unsubscribe."


def welcome_sms(client_name):
    """
    Welcome message for new clients.
    Sent after successful signup.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return (
        f"Welcome to {COMPANY_NAME}, {first_name}! "
        f"Your credit restoration case is being processed. "
        f"We'll update you on progress. {REPLY_STOP}"
    )


def document_reminder_sms(client_name, doc_type):
    """
    Reminder for missing documents.
    Sent when required documents are still pending.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return (
        f"Hi {first_name}, we still need your {doc_type} "
        f"to proceed with your credit case. "
        f"Please upload it to your client portal. {REPLY_STOP}"
    )


def case_update_sms(client_name, status):
    """
    Case status update notification.
    Sent when case moves to a new stage.
    """
    first_name = client_name.split()[0] if client_name else "there"

    status_messages = {
        "active": "Your case is now active and under review.",
        "stage1_pending": "Stage 1 analysis is in progress.",
        "stage1_complete": "Stage 1 analysis is complete! Check your portal for details.",
        "stage2_pending": "We're generating your dispute letters.",
        "stage2_complete": "Your dispute letters are ready for review.",
        "delivered": "All documents have been delivered. Check your portal.",
        "waiting_response": "Disputes sent. Awaiting bureau responses.",
        "complete": "Your case has been completed. Thank you!",
        "paused": "Your case is paused. Contact us with questions.",
    }

    message = status_messages.get(status, f"Your case status is now: {status}")

    return f"Hi {first_name}, {COMPANY_NAME} update: {message} {REPLY_STOP}"


def dispute_sent_sms(client_name, bureau):
    """
    Notification when dispute letter is sent to a bureau.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return (
        f"Hi {first_name}, great news! Your dispute letter "
        f"was sent to {bureau}. "
        f"Response expected in 30-45 days. {REPLY_STOP}"
    )


def cra_response_sms(client_name, bureau):
    """
    Notification when CRA response is received.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return (
        f"Hi {first_name}, we received a response from {bureau} "
        f"regarding your dispute. "
        f"Log in to your portal to review the results. {REPLY_STOP}"
    )


def payment_reminder_sms(client_name, amount):
    """
    Payment reminder for pending balance.
    """
    first_name = client_name.split()[0] if client_name else "there"
    formatted_amount = (
        f"${amount:,.2f}" if isinstance(amount, (int, float)) else f"${amount}"
    )
    return (
        f"Hi {first_name}, reminder: your payment of {formatted_amount} "
        f"for {COMPANY_NAME} services is pending. "
        f"Please complete payment to continue. {REPLY_STOP}"
    )


def appointment_reminder_sms(client_name, date_time):
    """
    Appointment reminder.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return (
        f"Hi {first_name}, reminder: you have a {COMPANY_NAME} "
        f"appointment scheduled for {date_time}. "
        f"Please confirm or reschedule if needed. {REPLY_STOP}"
    )


def round_started_sms(client_name, round_number):
    """
    Notification when a new dispute round starts.
    """
    first_name = client_name.split()[0] if client_name else "there"
    round_desc = {
        1: "Initial Dispute",
        2: "Follow-up (MOV Request)",
        3: "Pre-Litigation Warning",
        4: "Final Demand",
    }.get(round_number, f"Round {round_number}")

    return (
        f"Hi {first_name}, {COMPANY_NAME} has started "
        f"{round_desc} for your credit case. "
        f"We'll keep you updated. {REPLY_STOP}"
    )


def document_uploaded_sms(client_name, doc_type):
    """
    Confirmation when client uploads a document.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return (
        f"Hi {first_name}, we received your {doc_type}. "
        f"Thank you! Our team will review it shortly. {REPLY_STOP}"
    )


def analysis_ready_sms(client_name):
    """
    Notification when credit analysis is ready for review.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return (
        f"Hi {first_name}, your credit analysis is ready! "
        f"Log in to your {COMPANY_NAME} portal to review "
        f"violations found and next steps. {REPLY_STOP}"
    )


def letters_ready_sms(client_name, count):
    """
    Notification when dispute letters are generated.
    """
    first_name = client_name.split()[0] if client_name else "there"
    letter_word = "letter is" if count == 1 else "letters are"
    return (
        f"Hi {first_name}, {count} dispute {letter_word} ready! "
        f"Review and download them from your portal. "
        f"Ready to mail to bureaus. {REPLY_STOP}"
    )


def custom_sms(client_name, message):
    """
    Custom message template.
    Adds company branding and unsubscribe notice.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return f"Hi {first_name}, {COMPANY_NAME}: {message} {REPLY_STOP}"


def dispute_mailed_sms(client_name, bureau, round_number, tracking_number):
    """
    Notification when dispute letter has been mailed via certified mail.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return (
        f"Hi {first_name}, your Round {round_number} dispute to {bureau} "
        f"was mailed via certified mail. Tracking: {tracking_number}. "
        f"Response expected in 30 days. {REPLY_STOP}"
    )


def cra_response_received_sms(client_name, bureau, items_deleted):
    """
    Short notification when CRA responds with results.
    """
    first_name = client_name.split()[0] if client_name else "there"
    item_word = "item" if items_deleted == 1 else "items"
    return (
        f"Hi {first_name}, {bureau} responded! "
        f"{items_deleted} {item_word} deleted from your credit report. "
        f"Check your portal for full details. {REPLY_STOP}"
    )


def reinsertion_alert_sms(client_name, bureau):
    """
    URGENT alert for reinsertion violation.
    """
    first_name = client_name.split()[0] if client_name else "there"
    return (
        f"URGENT: {first_name}, {bureau} illegally reinserted a deleted item - "
        f"this is an FCRA violation! Check your email immediately for details. {REPLY_STOP}"
    )


TEMPLATE_TYPES = {
    "welcome": welcome_sms,
    "document_reminder": document_reminder_sms,
    "case_update": case_update_sms,
    "dispute_sent": dispute_sent_sms,
    "cra_response": cra_response_sms,
    "payment_reminder": payment_reminder_sms,
    "appointment_reminder": appointment_reminder_sms,
    "round_started": round_started_sms,
    "document_uploaded": document_uploaded_sms,
    "analysis_ready": analysis_ready_sms,
    "letters_ready": letters_ready_sms,
    "custom": custom_sms,
    "dispute_mailed": dispute_mailed_sms,
    "cra_response_received": cra_response_received_sms,
    "reinsertion_alert": reinsertion_alert_sms,
}


def get_template(template_type):
    """Get a template function by type name."""
    return TEMPLATE_TYPES.get(template_type)


def list_templates():
    """List all available template types."""
    return list(TEMPLATE_TYPES.keys())
