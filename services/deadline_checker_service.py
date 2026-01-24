"""
Deadline Checker Service

Runs as a scheduled job to check for approaching deadlines and fire workflow triggers.
This enables automated notifications for:
- Secondary bureau freeze responses (30 days expected)
- CRA dispute responses (30-35 days expected)
- SOL deadlines
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_

from database import (
    CaseDeadline,
    Client,
    SecondaryBureauFreeze,
    get_db,
)


class DeadlineCheckerService:
    """Service for checking approaching deadlines and triggering notifications"""

    # Configuration for deadline types
    DEADLINE_CONFIG = {
        "secondary_bureau": {
            "expected_days": 30,
            "warning_days": 25,  # Warn 5 days before expected
            "overdue_days": 31,  # Overdue after 30 days
        },
        "cra_response": {
            "expected_days": 30,
            "warning_days": 25,
            "overdue_days": 35,
        },
        "sol": {
            "warning_days": 30,  # Warn 30 days before SOL expires
        },
    }

    @staticmethod
    def check_all_deadlines() -> Dict[str, Any]:
        """
        Main entry point - checks all deadline types and fires appropriate triggers.
        Called by the scheduler daily.
        """
        results = {
            "checked_at": datetime.utcnow().isoformat(),
            "secondary_bureaus": DeadlineCheckerService.check_secondary_bureau_deadlines(),
            "cra_responses": DeadlineCheckerService.check_cra_response_deadlines(),
            "sol_deadlines": DeadlineCheckerService.check_sol_deadlines(),
        }

        # Calculate totals
        results["total_warnings"] = (
            results["secondary_bureaus"]["warnings_sent"]
            + results["cra_responses"]["warnings_sent"]
            + results["sol_deadlines"]["warnings_sent"]
        )
        results["total_overdue"] = (
            results["secondary_bureaus"]["overdue_alerts"]
            + results["cra_responses"]["overdue_alerts"]
        )

        return results

    @staticmethod
    def check_secondary_bureau_deadlines() -> Dict[str, Any]:
        """
        Check secondary bureau freeze requests for approaching/overdue responses.

        - Warning at 25 days (5 days before expected)
        - Overdue at 31+ days
        """
        session = get_db()
        config = DeadlineCheckerService.DEADLINE_CONFIG["secondary_bureau"]
        today = datetime.utcnow()

        warnings_sent = 0
        overdue_alerts = 0
        clients_notified = set()

        try:
            # Get all pending secondary bureau freezes with a request date
            pending_freezes = (
                session.query(SecondaryBureauFreeze)
                .filter(
                    and_(
                        SecondaryBureauFreeze.status == "PENDING",
                        SecondaryBureauFreeze.freeze_requested_at.isnot(None),
                    )
                )
                .all()
            )

            for freeze in pending_freezes:
                days_since_request = (today - freeze.freeze_requested_at).days
                client_id = freeze.client_id

                # Check if overdue (31+ days)
                if days_since_request >= config["overdue_days"]:
                    DeadlineCheckerService._fire_deadline_trigger(
                        session=session,
                        client_id=client_id,
                        deadline_type="secondary_bureau_overdue",
                        deadline_date=freeze.freeze_requested_at
                        + timedelta(days=config["expected_days"]),
                        days_remaining=config["expected_days"] - days_since_request,
                        extra_data={
                            "bureau_name": freeze.bureau_name,
                            "days_overdue": days_since_request
                            - config["expected_days"],
                        },
                    )
                    overdue_alerts += 1
                    clients_notified.add(client_id)

                # Check if warning zone (25-30 days)
                elif days_since_request >= config["warning_days"]:
                    DeadlineCheckerService._fire_deadline_trigger(
                        session=session,
                        client_id=client_id,
                        deadline_type="secondary_bureau_due_soon",
                        deadline_date=freeze.freeze_requested_at
                        + timedelta(days=config["expected_days"]),
                        days_remaining=config["expected_days"] - days_since_request,
                        extra_data={
                            "bureau_name": freeze.bureau_name,
                        },
                    )
                    warnings_sent += 1
                    clients_notified.add(client_id)

            return {
                "checked": len(pending_freezes),
                "warnings_sent": warnings_sent,
                "overdue_alerts": overdue_alerts,
                "clients_notified": len(clients_notified),
            }
        finally:
            session.close()

    @staticmethod
    def check_cra_response_deadlines() -> Dict[str, Any]:
        """
        Check CRA dispute response deadlines.
        Uses CaseDeadline records with deadline_type='cra_response'.
        """
        session = get_db()
        config = DeadlineCheckerService.DEADLINE_CONFIG["cra_response"]
        today = datetime.utcnow().date()

        warnings_sent = 0
        overdue_alerts = 0
        clients_notified = set()

        try:
            # Get pending CRA response deadlines
            deadlines = (
                session.query(CaseDeadline)
                .filter(
                    and_(
                        CaseDeadline.deadline_type.in_(
                            ["cra_response", "response_check"]
                        ),
                        CaseDeadline.status == "pending",
                    )
                )
                .all()
            )

            for deadline in deadlines:
                days_until = (deadline.deadline_date - today).days
                client_id = deadline.client_id

                # Check if overdue (past deadline + 5 days grace)
                if days_until <= -5:
                    DeadlineCheckerService._fire_deadline_trigger(
                        session=session,
                        client_id=client_id,
                        deadline_type="cra_response_overdue",
                        deadline_date=deadline.deadline_date,
                        days_remaining=days_until,
                        extra_data={
                            "description": deadline.description,
                            "days_overdue": abs(days_until),
                        },
                    )
                    overdue_alerts += 1
                    clients_notified.add(client_id)

                # Check if warning zone (5 days before deadline)
                elif 0 <= days_until <= 5:
                    DeadlineCheckerService._fire_deadline_trigger(
                        session=session,
                        client_id=client_id,
                        deadline_type="cra_response_due_soon",
                        deadline_date=deadline.deadline_date,
                        days_remaining=days_until,
                        extra_data={
                            "description": deadline.description,
                        },
                    )
                    warnings_sent += 1
                    clients_notified.add(client_id)

            return {
                "checked": len(deadlines),
                "warnings_sent": warnings_sent,
                "overdue_alerts": overdue_alerts,
                "clients_notified": len(clients_notified),
            }
        finally:
            session.close()

    @staticmethod
    def check_sol_deadlines() -> Dict[str, Any]:
        """
        Check Statute of Limitations deadlines.
        Uses CaseDeadline records with deadline_type='sol'.
        """
        session = get_db()
        config = DeadlineCheckerService.DEADLINE_CONFIG["sol"]
        today = datetime.utcnow().date()

        warnings_sent = 0
        clients_notified = set()

        try:
            # Get SOL deadlines approaching (within 30 days)
            warning_cutoff = today + timedelta(days=config["warning_days"])

            deadlines = (
                session.query(CaseDeadline)
                .filter(
                    and_(
                        CaseDeadline.deadline_type == "sol",
                        CaseDeadline.status == "pending",
                        CaseDeadline.deadline_date <= warning_cutoff,
                        CaseDeadline.deadline_date >= today,
                    )
                )
                .all()
            )

            for deadline in deadlines:
                days_until = (deadline.deadline_date - today).days
                client_id = deadline.client_id

                DeadlineCheckerService._fire_deadline_trigger(
                    session=session,
                    client_id=client_id,
                    deadline_type="sol",
                    deadline_date=deadline.deadline_date,
                    days_remaining=days_until,
                    extra_data={
                        "description": deadline.description,
                        "urgent": days_until <= 7,
                    },
                )
                warnings_sent += 1
                clients_notified.add(client_id)

            return {
                "checked": len(deadlines),
                "warnings_sent": warnings_sent,
                "clients_notified": len(clients_notified),
            }
        finally:
            session.close()

    @staticmethod
    def _fire_deadline_trigger(
        session,
        client_id: int,
        deadline_type: str,
        deadline_date,
        days_remaining: int,
        extra_data: Dict[str, Any] = None,
    ) -> bool:
        """
        Fire the deadline_approaching workflow trigger for a specific deadline.
        """
        try:
            # Get client info
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client:
                return False

            # Build event data
            event_data = {
                "client_id": client_id,
                "client_name": client.name,
                "client_email": client.email,
                "client_phone": client.phone,
                "deadline_type": deadline_type,
                "deadline_date": (
                    deadline_date.isoformat()
                    if hasattr(deadline_date, "isoformat")
                    else str(deadline_date)
                ),
                "days_remaining": days_remaining,
            }

            if extra_data:
                event_data.update(extra_data)

            # Fire the workflow trigger
            from services.workflow_triggers_service import WorkflowTriggersService

            results = WorkflowTriggersService.evaluate_triggers(
                "deadline_approaching", event_data
            )

            return len(results) > 0

        except Exception as e:
            print(f"Error firing deadline trigger for client {client_id}: {e}")
            return False

    @staticmethod
    def get_deadline_summary(client_id: int) -> Dict[str, Any]:
        """
        Get a summary of all deadlines for a specific client.
        Useful for the client portal or staff dashboard.
        """
        session = get_db()
        today = datetime.utcnow()

        try:
            # Get secondary bureau freezes
            freezes = (
                session.query(SecondaryBureauFreeze)
                .filter(SecondaryBureauFreeze.client_id == client_id)
                .all()
            )

            secondary_bureaus = []
            for freeze in freezes:
                if freeze.freeze_requested_at:
                    days_since = (today - freeze.freeze_requested_at).days
                    expected_date = freeze.freeze_requested_at + timedelta(days=30)
                    secondary_bureaus.append(
                        {
                            "bureau_name": freeze.bureau_name,
                            "status": freeze.status,
                            "requested_at": freeze.freeze_requested_at.isoformat(),
                            "expected_by": expected_date.isoformat(),
                            "days_remaining": 30 - days_since,
                            "is_overdue": days_since > 30,
                        }
                    )

            # Get case deadlines
            deadlines = (
                session.query(CaseDeadline)
                .filter(CaseDeadline.client_id == client_id)
                .all()
            )

            case_deadlines = []
            for deadline in deadlines:
                days_until = (deadline.deadline_date - today.date()).days
                case_deadlines.append(
                    {
                        "type": deadline.deadline_type,
                        "description": deadline.description,
                        "deadline_date": deadline.deadline_date.isoformat(),
                        "days_remaining": days_until,
                        "status": deadline.status,
                        "is_overdue": days_until < 0 and deadline.status == "pending",
                    }
                )

            return {
                "client_id": client_id,
                "secondary_bureaus": secondary_bureaus,
                "case_deadlines": case_deadlines,
                "total_pending": sum(
                    1 for d in case_deadlines if d["status"] == "pending"
                ),
                "total_overdue": sum(1 for d in case_deadlines if d["is_overdue"]),
            }
        finally:
            session.close()


# Register the task handler for the scheduler
from services.task_queue_service import register_task_handler


@register_task_handler("check_deadlines")
def handle_check_deadlines(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Task handler for checking all deadlines"""
    return DeadlineCheckerService.check_all_deadlines()


@register_task_handler("check_secondary_bureau_deadlines")
def handle_check_secondary_bureau_deadlines(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Task handler for checking secondary bureau deadlines only"""
    return DeadlineCheckerService.check_secondary_bureau_deadlines()


@register_task_handler("check_cra_response_deadlines")
def handle_check_cra_response_deadlines(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Task handler for checking CRA response deadlines only"""
    return DeadlineCheckerService.check_cra_response_deadlines()
