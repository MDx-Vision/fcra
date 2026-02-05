"""
Deadline Service for Brightpath Ascend FCRA Platform
Tracks deadlines for CRA responses, reinvestigations, and required actions.
Sends automated reminder emails at key intervals.
"""

import logging
from datetime import date, datetime, timedelta

from services import email_templates
from services.email_service import is_sendgrid_configured, send_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEADLINE_TYPES = {
    "cra_response": {
        "name": "CRA Response",
        "default_days": 30,
        "description": "Credit Reporting Agency must respond to dispute",
    },
    "reinvestigation": {
        "name": "Reinvestigation",
        "default_days": 45,
        "description": "Extended reinvestigation period",
    },
    "data_furnisher": {
        "name": "Data Furnisher Response",
        "default_days": 30,
        "description": "Data furnisher must respond to dispute",
    },
    "client_action": {
        "name": "Client Action Required",
        "default_days": 14,
        "description": "Client must complete required action",
    },
    "legal_filing": {
        "name": "Legal Filing Deadline",
        "default_days": 365,
        "description": "Statute of limitations tracking",
    },
}


def get_deadline_type_info(deadline_type):
    """Get information about a deadline type."""
    return DEADLINE_TYPES.get(
        deadline_type,
        {
            "name": deadline_type.replace("_", " ").title(),
            "default_days": 30,
            "description": "Custom deadline",
        },
    )


def create_deadline(
    db,
    client_id,
    case_id,
    deadline_type,
    bureau,
    dispute_round,
    start_date,
    days_allowed=None,
):
    """
    Create a new deadline for tracking.

    Args:
        db: Database session
        client_id: Client ID
        case_id: Case ID (optional, can be None)
        deadline_type: Type of deadline (cra_response, reinvestigation, data_furnisher, client_action, legal_filing)
        bureau: Credit bureau name (Experian, TransUnion, Equifax, or None)
        dispute_round: Dispute round number
        start_date: Start date for the deadline (date object or string YYYY-MM-DD)
        days_allowed: Number of days until deadline (defaults to type-specific default)

    Returns:
        Created CaseDeadline record
    """
    from database import CaseDeadline, Client

    try:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

        if days_allowed is None:
            type_info = get_deadline_type_info(deadline_type)
            days_allowed = type_info["default_days"]

        deadline_date = start_date + timedelta(days=days_allowed)

        deadline = CaseDeadline(
            client_id=client_id,
            case_id=case_id,
            deadline_type=deadline_type,
            bureau=bureau,
            dispute_round=dispute_round,
            start_date=start_date,
            deadline_date=deadline_date,
            days_allowed=days_allowed,
            status="active",
        )

        db.add(deadline)
        db.commit()
        db.refresh(deadline)

        client = db.query(Client).filter_by(id=client_id).first()
        client_name = client.name if client else f"Client {client_id}"

        type_info = get_deadline_type_info(deadline_type)
        logger.info(
            f"Created deadline: {type_info['name']} for {client_name} "
            f"(ID: {deadline.id}), Bureau: {bureau or 'N/A'}, "
            f"Due: {deadline_date}, Days: {days_allowed}"
        )

        return deadline

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating deadline for client {client_id}: {str(e)}")
        raise


def get_client_deadlines(db, client_id, include_completed=False):
    """
    Get all deadlines for a specific client.

    Args:
        db: Database session
        client_id: Client ID
        include_completed: If True, include completed deadlines

    Returns:
        List of deadline dicts with days_remaining calculated
    """
    from database import CaseDeadline

    try:
        query = db.query(CaseDeadline).filter_by(client_id=client_id)

        if not include_completed:
            query = query.filter(CaseDeadline.status == "active")

        deadlines = query.order_by(CaseDeadline.deadline_date.asc()).all()

        today = date.today()
        result = []

        for deadline in deadlines:
            days_remaining = (deadline.deadline_date - today).days
            type_info = get_deadline_type_info(deadline.deadline_type)

            result.append(
                {
                    "id": deadline.id,
                    "client_id": deadline.client_id,
                    "case_id": deadline.case_id,
                    "deadline_type": deadline.deadline_type,
                    "deadline_type_name": type_info["name"],
                    "bureau": deadline.bureau,
                    "dispute_round": deadline.dispute_round,
                    "start_date": deadline.start_date,
                    "deadline_date": deadline.deadline_date,
                    "days_allowed": deadline.days_allowed,
                    "days_remaining": days_remaining,
                    "is_overdue": days_remaining < 0,
                    "status": deadline.status,
                    "completed_at": deadline.completed_at,
                    "reminder_sent_7_days": deadline.reminder_sent_7_days,
                    "reminder_sent_3_days": deadline.reminder_sent_3_days,
                    "reminder_sent_1_day": deadline.reminder_sent_1_day,
                    "overdue_notice_sent": deadline.overdue_notice_sent,
                    "notes": deadline.notes,
                    "created_at": deadline.created_at,
                }
            )

        logger.info(f"Retrieved {len(result)} deadlines for client {client_id}")
        return result

    except Exception as e:
        logger.error(f"Error getting deadlines for client {client_id}: {str(e)}")
        raise


def get_upcoming_deadlines(db, days_ahead=7, include_overdue=True):
    """
    Get all deadlines due within the specified number of days.
    For admin dashboard view.

    Args:
        db: Database session
        days_ahead: Number of days to look ahead
        include_overdue: If True, include overdue deadlines

    Returns:
        List of deadline dicts with client info
    """
    from database import CaseDeadline, Client

    try:
        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        query = (
            db.query(CaseDeadline, Client)
            .join(Client, CaseDeadline.client_id == Client.id)
            .filter(CaseDeadline.status == "active")
        )

        if include_overdue:
            query = query.filter(CaseDeadline.deadline_date <= future_date)
        else:
            query = query.filter(
                CaseDeadline.deadline_date >= today,
                CaseDeadline.deadline_date <= future_date,
            )

        results = query.order_by(CaseDeadline.deadline_date.asc()).all()

        deadlines = []
        for deadline, client in results:
            days_remaining = (deadline.deadline_date - today).days
            type_info = get_deadline_type_info(deadline.deadline_type)

            deadlines.append(
                {
                    "id": deadline.id,
                    "client_id": deadline.client_id,
                    "client_name": client.name,
                    "client_email": client.email,
                    "case_id": deadline.case_id,
                    "deadline_type": deadline.deadline_type,
                    "deadline_type_name": type_info["name"],
                    "bureau": deadline.bureau,
                    "dispute_round": deadline.dispute_round,
                    "start_date": deadline.start_date,
                    "deadline_date": deadline.deadline_date,
                    "days_remaining": days_remaining,
                    "is_overdue": days_remaining < 0,
                    "urgency": _get_urgency_level(days_remaining),
                    "status": deadline.status,
                    "notes": deadline.notes,
                }
            )

        logger.info(
            f"Retrieved {len(deadlines)} upcoming deadlines (next {days_ahead} days)"
        )
        return deadlines

    except Exception as e:
        logger.error(f"Error getting upcoming deadlines: {str(e)}")
        raise


def _get_urgency_level(days_remaining):
    """Determine urgency level based on days remaining."""
    if days_remaining < 0:
        return "overdue"
    elif days_remaining <= 1:
        return "critical"
    elif days_remaining <= 3:
        return "high"
    elif days_remaining <= 7:
        return "medium"
    else:
        return "low"


def complete_deadline(db, deadline_id, notes=None):
    """
    Mark a deadline as completed.

    Args:
        db: Database session
        deadline_id: Deadline ID
        notes: Optional completion notes

    Returns:
        Updated deadline record
    """
    from database import CaseDeadline

    try:
        deadline = db.query(CaseDeadline).filter_by(id=deadline_id).first()

        if not deadline:
            logger.warning(f"Deadline {deadline_id} not found")
            return None

        deadline.status = "completed"
        deadline.completed_at = datetime.utcnow()

        if notes:
            existing_notes = deadline.notes or ""
            deadline.notes = f"{existing_notes}\n[Completed] {notes}".strip()

        db.commit()
        db.refresh(deadline)

        logger.info(f"Completed deadline {deadline_id} for client {deadline.client_id}")
        return deadline

    except Exception as e:
        db.rollback()
        logger.error(f"Error completing deadline {deadline_id}: {str(e)}")
        raise


def extend_deadline(db, deadline_id, new_days, notes=None):
    """
    Extend a deadline by recalculating the deadline_date.

    Args:
        db: Database session
        deadline_id: Deadline ID
        new_days: New total days from original start_date
        notes: Optional extension notes

    Returns:
        Updated deadline record
    """
    from database import CaseDeadline

    try:
        deadline = db.query(CaseDeadline).filter_by(id=deadline_id).first()

        if not deadline:
            logger.warning(f"Deadline {deadline_id} not found")
            return None

        old_deadline_date = deadline.deadline_date
        new_deadline_date = deadline.start_date + timedelta(days=new_days)

        deadline.deadline_date = new_deadline_date
        deadline.days_allowed = new_days

        deadline.reminder_sent_7_days = False
        deadline.reminder_sent_3_days = False
        deadline.reminder_sent_1_day = False
        deadline.overdue_notice_sent = False

        if deadline.status == "completed":
            deadline.status = "active"
            deadline.completed_at = None

        if notes:
            existing_notes = deadline.notes or ""
            extension_note = (
                f"[Extended] {old_deadline_date} -> {new_deadline_date}: {notes}"
            )
            deadline.notes = f"{existing_notes}\n{extension_note}".strip()

        db.commit()
        db.refresh(deadline)

        logger.info(
            f"Extended deadline {deadline_id}: {old_deadline_date} -> {new_deadline_date} "
            f"(client {deadline.client_id})"
        )
        return deadline

    except Exception as e:
        db.rollback()
        logger.error(f"Error extending deadline {deadline_id}: {str(e)}")
        raise


def check_and_send_reminders(db):
    """
    Check all active deadlines and send reminder emails as needed.
    Sends reminders at 7 days, 3 days, 1 day before deadline, and overdue notice.

    Args:
        db: Database session

    Returns:
        Dict with counts of reminders sent
    """
    from database import CaseDeadline, Client

    results = {
        "checked": 0,
        "reminders_7_days": 0,
        "reminders_3_days": 0,
        "reminders_1_day": 0,
        "overdue_notices": 0,
        "errors": 0,
    }

    if not is_sendgrid_configured():
        logger.warning("SendGrid not configured - skipping deadline reminders")
        return results

    try:
        active_deadlines = (
            db.query(CaseDeadline, Client)
            .join(Client, CaseDeadline.client_id == Client.id)
            .filter(CaseDeadline.status == "active")
            .all()
        )

        today = date.today()

        for deadline, client in active_deadlines:
            results["checked"] += 1
            days_remaining = (deadline.deadline_date - today).days

            try:
                if days_remaining < 0 and not deadline.overdue_notice_sent:
                    if _send_deadline_reminder(
                        db, deadline, client, "overdue", days_remaining
                    ):
                        deadline.overdue_notice_sent = True
                        results["overdue_notices"] += 1
                        logger.info(f"Sent overdue notice for deadline {deadline.id}")

                elif days_remaining == 1 and not deadline.reminder_sent_1_day:
                    if _send_deadline_reminder(
                        db, deadline, client, "1_day", days_remaining
                    ):
                        deadline.reminder_sent_1_day = True
                        results["reminders_1_day"] += 1
                        logger.info(f"Sent 1-day reminder for deadline {deadline.id}")

                elif (
                    days_remaining <= 3
                    and days_remaining > 1
                    and not deadline.reminder_sent_3_days
                ):
                    if _send_deadline_reminder(
                        db, deadline, client, "3_days", days_remaining
                    ):
                        deadline.reminder_sent_3_days = True
                        results["reminders_3_days"] += 1
                        logger.info(f"Sent 3-day reminder for deadline {deadline.id}")

                elif (
                    days_remaining <= 7
                    and days_remaining > 3
                    and not deadline.reminder_sent_7_days
                ):
                    if _send_deadline_reminder(
                        db, deadline, client, "7_days", days_remaining
                    ):
                        deadline.reminder_sent_7_days = True
                        results["reminders_7_days"] += 1
                        logger.info(f"Sent 7-day reminder for deadline {deadline.id}")

            except Exception as e:
                results["errors"] += 1
                logger.error(f"Error processing deadline {deadline.id}: {str(e)}")
                continue

        db.commit()

        total_sent = (
            results["reminders_7_days"]
            + results["reminders_3_days"]
            + results["reminders_1_day"]
            + results["overdue_notices"]
        )
        logger.info(
            f"Deadline reminder check complete: {results['checked']} checked, "
            f"{total_sent} reminders sent, {results['errors']} errors"
        )

        return results

    except Exception as e:
        db.rollback()
        logger.error(f"Error in check_and_send_reminders: {str(e)}")
        raise


def _send_deadline_reminder(db, deadline, client, reminder_type, days_remaining):
    """
    Send a deadline reminder email.

    Args:
        db: Database session
        deadline: CaseDeadline record
        client: Client record
        reminder_type: Type of reminder (7_days, 3_days, 1_day, overdue)
        days_remaining: Days remaining until deadline

    Returns:
        True if sent successfully, False otherwise
    """
    from database import EmailLog

    if not client.email:
        logger.warning(f"No email for client {client.id} - skipping reminder")
        return False

    type_info = get_deadline_type_info(deadline.deadline_type)
    first_name = client.name.split()[0] if client.name else "there"

    subject, html_content = _build_deadline_email(
        first_name=first_name,
        deadline_type_name=type_info["name"],
        bureau=deadline.bureau,
        deadline_date=deadline.deadline_date,
        days_remaining=days_remaining,
        reminder_type=reminder_type,
        dispute_round=deadline.dispute_round,
    )

    result = send_email(client.email, subject, html_content)

    log_entry = EmailLog(
        client_id=client.id,
        email_address=client.email,
        subject=subject,
        template_type=f"deadline_{reminder_type}",
        status="sent" if result["success"] else "failed",
        message_id=result.get("message_id"),
        error_message=result.get("error"),
        sent_at=datetime.utcnow(),
    )
    db.add(log_entry)

    if result["success"]:
        logger.info(
            f"Sent {reminder_type} reminder to {client.email} for deadline {deadline.id}"
        )
    else:
        logger.error(
            f"Failed to send {reminder_type} reminder to {client.email}: {result.get('error')}"
        )

    return result["success"]


def _build_deadline_email(
    first_name,
    deadline_type_name,
    bureau,
    deadline_date,
    days_remaining,
    reminder_type,
    dispute_round,
):
    """Build deadline reminder email content."""

    bureau_text = f" with {bureau}" if bureau else ""
    round_text = f" (Round {dispute_round})" if dispute_round else ""

    if reminder_type == "overdue":
        subject = f"⚠️ OVERDUE: {deadline_type_name} Deadline Passed"
        urgency_color = "#ef4444"
        urgency_text = f"This deadline was due on {deadline_date.strftime('%B %d, %Y')} ({abs(days_remaining)} days ago)."
        action_text = "Immediate action is required. Please contact us right away."
    elif reminder_type == "1_day":
        subject = f"🔴 URGENT: {deadline_type_name} Deadline Tomorrow!"
        urgency_color = "#f97316"
        urgency_text = (
            f"This deadline is due TOMORROW ({deadline_date.strftime('%B %d, %Y')})."
        )
        action_text = "Please ensure all required actions are completed today."
    elif reminder_type == "3_days":
        subject = f"⏰ Deadline in 3 Days: {deadline_type_name}"
        urgency_color = "#eab308"
        urgency_text = f"This deadline is due in {days_remaining} days ({deadline_date.strftime('%B %d, %Y')})."
        action_text = "Please prepare any necessary documentation or responses."
    else:
        subject = f"📅 Upcoming Deadline: {deadline_type_name}"
        urgency_color = "#3b82f6"
        urgency_text = f"This deadline is due in {days_remaining} days ({deadline_date.strftime('%B %d, %Y')})."
        action_text = "This is an advance notice to help you plan accordingly."

    content = f"""
        <h2 style="color: #1a1a2e; margin: 0 0 20px 0; font-size: 24px;">Deadline Reminder</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <div style="background-color: #f8fafc; border-left: 4px solid {urgency_color}; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
            <p style="color: #334155; margin: 0; font-size: 16px; font-weight: 600;">
                {deadline_type_name}{bureau_text}{round_text}
            </p>
            <p style="color: {urgency_color}; margin: 10px 0 0 0; font-size: 14px; font-weight: 500;">
                {urgency_text}
            </p>
        </div>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            {action_text}
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            <strong>What this deadline means:</strong>
        </p>

        <ul style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li>Credit bureaus and furnishers must respond within the legally required timeframe</li>
            <li>If no response is received, this strengthens your dispute case</li>
            <li>We track all deadlines to ensure your rights are protected</li>
        </ul>

        <p style="color: #64748b; font-size: 14px; margin-top: 30px;">
            If you have any questions about this deadline, please reply to this email or contact our team.
        </p>
    """

    html_content = email_templates.get_base_template(content, subject)

    return subject, html_content


def cancel_deadline(db, deadline_id, reason=None):
    """
    Cancel a deadline (mark as cancelled).

    Args:
        db: Database session
        deadline_id: Deadline ID
        reason: Optional cancellation reason

    Returns:
        Updated deadline record
    """
    from database import CaseDeadline

    try:
        deadline = db.query(CaseDeadline).filter_by(id=deadline_id).first()

        if not deadline:
            logger.warning(f"Deadline {deadline_id} not found")
            return None

        deadline.status = "cancelled"

        if reason:
            existing_notes = deadline.notes or ""
            deadline.notes = f"{existing_notes}\n[Cancelled] {reason}".strip()

        db.commit()
        db.refresh(deadline)

        logger.info(f"Cancelled deadline {deadline_id} for client {deadline.client_id}")
        return deadline

    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling deadline {deadline_id}: {str(e)}")
        raise


def get_deadline_summary(db, client_id=None):
    """
    Get summary statistics for deadlines.

    Args:
        db: Database session
        client_id: Optional client ID to filter by

    Returns:
        Dict with deadline statistics
    """
    from sqlalchemy import func

    from database import CaseDeadline

    try:
        query = db.query(CaseDeadline)

        if client_id:
            query = query.filter_by(client_id=client_id)

        today = date.today()

        active = query.filter(CaseDeadline.status == "active").all()

        total_active = len(active)
        overdue = sum(1 for d in active if d.deadline_date < today)
        due_today = sum(1 for d in active if d.deadline_date == today)
        due_this_week = sum(
            1 for d in active if today <= d.deadline_date <= today + timedelta(days=7)
        )

        by_type = {}
        for d in active:
            by_type[d.deadline_type] = by_type.get(d.deadline_type, 0) + 1

        by_bureau = {}
        for d in active:
            if d.bureau:
                by_bureau[d.bureau] = by_bureau.get(d.bureau, 0) + 1

        total_completed = query.filter(CaseDeadline.status == "completed").count()
        total_cancelled = query.filter(CaseDeadline.status == "cancelled").count()

        return {
            "total_active": total_active,
            "overdue": overdue,
            "due_today": due_today,
            "due_this_week": due_this_week,
            "by_type": by_type,
            "by_bureau": by_bureau,
            "total_completed": total_completed,
            "total_cancelled": total_cancelled,
        }

    except Exception as e:
        logger.error(f"Error getting deadline summary: {str(e)}")
        raise


def create_cra_response_deadline(
    db, client_id, case_id, bureau, dispute_round, letter_sent_date
):
    """
    Convenience function to create a CRA response deadline when a dispute letter is sent.

    Args:
        db: Database session
        client_id: Client ID
        case_id: Case ID
        bureau: Credit bureau name
        dispute_round: Dispute round number
        letter_sent_date: Date the dispute letter was sent

    Returns:
        Created CaseDeadline record
    """
    return create_deadline(
        db=db,
        client_id=client_id,
        case_id=case_id,
        deadline_type="cra_response",
        bureau=bureau,
        dispute_round=dispute_round,
        start_date=letter_sent_date,
        days_allowed=30,
    )


def create_reinvestigation_deadline(
    db, client_id, case_id, bureau, dispute_round, start_date
):
    """
    Convenience function to create a reinvestigation deadline.

    Args:
        db: Database session
        client_id: Client ID
        case_id: Case ID
        bureau: Credit bureau name
        dispute_round: Dispute round number
        start_date: Start date for reinvestigation

    Returns:
        Created CaseDeadline record
    """
    return create_deadline(
        db=db,
        client_id=client_id,
        case_id=case_id,
        deadline_type="reinvestigation",
        bureau=bureau,
        dispute_round=dispute_round,
        start_date=start_date,
        days_allowed=45,
    )
