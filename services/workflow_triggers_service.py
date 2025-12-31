import json
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

from sqlalchemy import and_, desc, func, or_

from database import (
    CaseDeadline,
    Client,
    ClientNote,
    WorkflowExecution,
    WorkflowTrigger,
    get_db,
)

TRIGGER_TYPES = {
    "case_created": {
        "name": "Case Created",
        "description": "Fires when a new client signs up",
        "fields": ["client_id", "client_name", "email", "phone", "plan"],
    },
    "status_changed": {
        "name": "Status Changed",
        "description": "Fires when case status is updated",
        "fields": ["client_id", "old_status", "new_status"],
    },
    "deadline_approaching": {
        "name": "Deadline Approaching",
        "description": "Fires when SOL or response deadline is near",
        "fields": ["client_id", "deadline_type", "deadline_date", "days_remaining"],
    },
    "document_uploaded": {
        "name": "Document Uploaded",
        "description": "Fires when a new document is received",
        "fields": ["client_id", "document_type", "document_name", "uploaded_by"],
    },
    "payment_received": {
        "name": "Payment Received",
        "description": "Fires when payment is processed",
        "fields": ["client_id", "amount", "payment_method", "plan"],
    },
    "dispute_sent": {
        "name": "Dispute Sent",
        "description": "Fires when a dispute letter is mailed",
        "fields": ["client_id", "bureau", "round_number", "tracking_number"],
    },
    "response_received": {
        "name": "Response Received",
        "description": "Fires when CRA response is received",
        "fields": [
            "client_id",
            "bureau",
            "response_type",
            "items_verified",
            "items_deleted",
        ],
    },
}

ACTION_TYPES = {
    "send_email": {
        "name": "Send Email",
        "description": "Send an email notification",
        "params": ["template", "subject", "to_override"],
    },
    "send_sms": {
        "name": "Send SMS",
        "description": "Send an SMS notification",
        "params": ["template", "message"],
    },
    "create_task": {
        "name": "Create Task",
        "description": "Create a background task",
        "params": ["task_type", "payload", "priority"],
    },
    "update_status": {
        "name": "Update Status",
        "description": "Change case status",
        "params": ["new_status"],
    },
    "assign_attorney": {
        "name": "Assign Attorney",
        "description": "Assign to a staff member",
        "params": ["staff_id", "assignment_type"],
    },
    "add_note": {
        "name": "Add Note",
        "description": "Add a case note",
        "params": ["note_text", "note_type"],
    },
    "schedule_followup": {
        "name": "Schedule Followup",
        "description": "Create a calendar event/deadline",
        "params": ["days_from_now", "deadline_type", "description"],
    },
    "generate_document": {
        "name": "Generate Document",
        "description": "Create document from template",
        "params": ["template_name", "document_type"],
    },
}

DEFAULT_TRIGGERS = [
    {
        "name": "Welcome New Client",
        "description": "Sends welcome email and SMS when a new client signs up",
        "trigger_type": "case_created",
        "conditions": {},
        "actions": [
            {
                "type": "send_email",
                "params": {
                    "template": "welcome",
                    "subject": "Welcome to Brightpath Ascend - Your Credit Dispute Journey Begins!",
                },
            },
            {
                "type": "send_sms",
                "params": {
                    "template": "welcome",
                    "message": "Welcome to Brightpath Ascend! Your credit dispute journey has begun. Check your email for next steps.",
                },
            },
            {
                "type": "add_note",
                "params": {
                    "note_text": "Client onboarded - Welcome communications sent",
                    "note_type": "system",
                },
            },
        ],
        "priority": 10,
    },
    {
        "name": "SOL Warning",
        "description": "Sends alert email when SOL deadline is approaching (30 days)",
        "trigger_type": "deadline_approaching",
        "conditions": {"deadline_type": "sol", "days_remaining_max": 30},
        "actions": [
            {
                "type": "send_email",
                "params": {
                    "template": "sol_warning",
                    "subject": "URGENT: Statute of Limitations Deadline Approaching",
                },
            },
            {
                "type": "create_task",
                "params": {
                    "task_type": "sol_review",
                    "payload": {"urgent": True},
                    "priority": 1,
                },
            },
        ],
        "priority": 10,
    },
    {
        "name": "Document Review Needed",
        "description": "Notifies assigned attorney when new document is uploaded",
        "trigger_type": "document_uploaded",
        "conditions": {},
        "actions": [
            {
                "type": "send_email",
                "params": {
                    "template": "document_review",
                    "subject": "New Document Uploaded - Review Required",
                },
            },
            {
                "type": "add_note",
                "params": {
                    "note_text": "New document uploaded - pending review",
                    "note_type": "document",
                },
            },
        ],
        "priority": 5,
    },
    {
        "name": "Payment Confirmation",
        "description": "Sends confirmation and updates status when payment is received",
        "trigger_type": "payment_received",
        "conditions": {},
        "actions": [
            {
                "type": "send_email",
                "params": {
                    "template": "payment_confirmation",
                    "subject": "Payment Received - Thank You!",
                },
            },
            {
                "type": "send_sms",
                "params": {
                    "template": "payment_confirmation",
                    "message": "Thank you! Your payment has been received. We are processing your case.",
                },
            },
            {"type": "update_status", "params": {"new_status": "active"}},
        ],
        "priority": 8,
    },
    {
        "name": "Dispute Tracking",
        "description": "Schedules followup task when dispute letter is sent",
        "trigger_type": "dispute_sent",
        "conditions": {},
        "actions": [
            {
                "type": "schedule_followup",
                "params": {
                    "days_from_now": 35,
                    "deadline_type": "response_check",
                    "description": "Check for CRA response",
                },
            },
            {
                "type": "add_note",
                "params": {
                    "note_text": "Dispute letter mailed - Response deadline set for 35 days",
                    "note_type": "dispute",
                },
            },
        ],
        "priority": 7,
    },
    {
        "name": "Response Alert",
        "description": "Notifies client and triggers analysis when CRA response is received",
        "trigger_type": "response_received",
        "conditions": {},
        "actions": [
            {
                "type": "send_email",
                "params": {
                    "template": "response_received",
                    "subject": "Credit Bureau Response Received - Update on Your Case",
                },
            },
            {
                "type": "send_sms",
                "params": {
                    "template": "response_received",
                    "message": "Good news! We received a response from the credit bureau. Check your email for details.",
                },
            },
            {
                "type": "create_task",
                "params": {
                    "task_type": "analyze_response",
                    "payload": {},
                    "priority": 3,
                },
            },
        ],
        "priority": 9,
    },
    {
        "name": "Create Response Deadline on Dispute Sent",
        "description": "Schedules 30-day response deadline and sends tracking notification when dispute letter is mailed",
        "trigger_type": "dispute_sent",
        "conditions": {},
        "actions": [
            {
                "type": "schedule_followup",
                "params": {
                    "days_from_now": 30,
                    "deadline_type": "cra_response",
                    "description": "CRA Response Deadline",
                },
            },
            {
                "type": "send_sms",
                "params": {
                    "template": "dispute_sent",
                    "message": "Your dispute letter has been sent via certified mail! Tracking: {tracking_number}",
                },
            },
        ],
        "priority": 8,
    },
    {
        "name": "Analyze Response and Progress Round",
        "description": "Creates analysis task and logs deletion/verification counts when CRA response is received",
        "trigger_type": "response_received",
        "conditions": {},
        "actions": [
            {
                "type": "create_task",
                "params": {
                    "task_type": "analyze_cra_response",
                    "payload": {"client_id": "{client_id}", "bureau": "{bureau}"},
                    "priority": 2,
                },
            },
            {
                "type": "add_note",
                "params": {
                    "note_text": "{bureau} Response: {items_deleted} deleted, {items_verified} verified",
                    "note_type": "cra_response",
                },
            },
        ],
        "priority": 9,
    },
    {
        "name": "No Response After 35 Days",
        "description": "Escalates when CRA fails to respond within required timeframe",
        "trigger_type": "deadline_approaching",
        "conditions": {"days_remaining_max": -5},
        "actions": [
            {
                "type": "create_task",
                "params": {
                    "task_type": "escalate_no_response",
                    "payload": {
                        "client_id": "{client_id}",
                        "deadline_type": "{deadline_type}",
                    },
                    "priority": 1,
                },
            },
            {
                "type": "send_email",
                "params": {
                    "template": "cra_no_response",
                    "subject": "URGENT: Credit Bureau Failed to Respond - Potential FCRA Violation",
                },
            },
        ],
        "priority": 10,
    },
    {
        "name": "Reinsertion Detected",
        "description": "Alerts and escalates when previously deleted item reappears on credit report",
        "trigger_type": "response_received",
        "conditions": {"response_type": "reinsertion"},
        "actions": [
            {
                "type": "send_email",
                "params": {
                    "template": "reinsertion_alert",
                    "subject": "🚨 URGENT: Item Reinserted - FCRA Violation Detected",
                },
            },
            {
                "type": "create_task",
                "params": {
                    "task_type": "reinsertion_violation",
                    "payload": {"client_id": "{client_id}", "bureau": "{bureau}"},
                    "priority": 1,
                },
            },
            {
                "type": "add_note",
                "params": {
                    "note_text": "FCRA §1681i(a)(5)(B) VIOLATION: Previously deleted item reinserted without proper notice",
                    "note_type": "violation",
                },
            },
        ],
        "priority": 10,
    },
]


def install_automation_triggers(db):
    """Install automation triggers if they don't already exist"""
    automation_trigger_names = [
        "Create Response Deadline on Dispute Sent",
        "Analyze Response and Progress Round",
        "No Response After 35 Days",
        "Reinsertion Detected",
    ]

    created_count = 0

    for trigger_data in DEFAULT_TRIGGERS:
        if trigger_data["name"] in automation_trigger_names:
            existing = (
                db.query(WorkflowTrigger)
                .filter(WorkflowTrigger.name == trigger_data["name"])
                .first()
            )

            if not existing:
                trigger = WorkflowTrigger(
                    name=trigger_data["name"],
                    description=trigger_data["description"],
                    trigger_type=trigger_data["trigger_type"],
                    conditions=trigger_data.get("conditions", {}),
                    actions=trigger_data["actions"],
                    priority=trigger_data.get("priority", 5),
                    is_active=True,
                )
                db.add(trigger)
                created_count += 1

    db.commit()
    return created_count


class WorkflowTriggersService:
    """Service for managing automated workflow triggers"""

    @staticmethod
    def get_trigger_types() -> Dict[str, Any]:
        """Get available trigger types with metadata"""
        return TRIGGER_TYPES

    @staticmethod
    def get_action_types() -> Dict[str, Any]:
        """Get available action types with metadata"""
        return ACTION_TYPES

    @staticmethod
    def create_trigger(
        name: str,
        trigger_type: str,
        conditions: Dict[str, Any],
        actions: List[Dict[str, Any]],
        description: Optional[str] = None,
        priority: int = 5,
        staff_id: Optional[int] = None,
    ) -> WorkflowTrigger:
        """Create a new workflow trigger"""
        if trigger_type not in TRIGGER_TYPES:
            raise ValueError(f"Invalid trigger type: {trigger_type}")

        session = get_db()
        try:
            trigger = WorkflowTrigger(
                name=name,
                description=description,
                trigger_type=trigger_type,
                conditions=conditions or {},
                actions=actions,
                priority=min(max(priority, 1), 10),
                is_active=True,
                created_by_staff_id=staff_id,
            )
            session.add(trigger)
            session.commit()
            session.refresh(trigger)
            return trigger
        finally:
            session.close()

    @staticmethod
    def update_trigger(trigger_id: int, **kwargs) -> Optional[WorkflowTrigger]:
        """Update an existing workflow trigger"""
        session = get_db()
        try:
            trigger = (
                session.query(WorkflowTrigger)
                .filter(WorkflowTrigger.id == trigger_id)
                .first()
            )

            if not trigger:
                return None

            allowed_fields = [
                "name",
                "description",
                "trigger_type",
                "conditions",
                "actions",
                "is_active",
                "priority",
            ]

            for key, value in kwargs.items():
                if key in allowed_fields:
                    if key == "trigger_type" and value not in TRIGGER_TYPES:
                        raise ValueError(f"Invalid trigger type: {value}")
                    if key == "priority":
                        value = min(max(value, 1), 10)
                    setattr(trigger, key, value)

            trigger.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(trigger)
            return trigger
        finally:
            session.close()

    @staticmethod
    def delete_trigger(trigger_id: int) -> bool:
        """Delete a workflow trigger"""
        session = get_db()
        try:
            trigger = (
                session.query(WorkflowTrigger)
                .filter(WorkflowTrigger.id == trigger_id)
                .first()
            )

            if not trigger:
                return False

            session.delete(trigger)
            session.commit()
            return True
        finally:
            session.close()

    @staticmethod
    def get_trigger(trigger_id: int) -> Optional[WorkflowTrigger]:
        """Get a single trigger by ID"""
        session = get_db()
        try:
            trigger = (
                session.query(WorkflowTrigger)
                .filter(WorkflowTrigger.id == trigger_id)
                .first()
            )
            return trigger
        finally:
            session.close()

    @staticmethod
    def get_all_triggers(active_only: bool = False) -> List[WorkflowTrigger]:
        """Get all workflow triggers"""
        session = get_db()
        try:
            query = session.query(WorkflowTrigger)
            if active_only:
                query = query.filter(WorkflowTrigger.is_active == True)
            triggers = query.order_by(
                WorkflowTrigger.priority.desc(), WorkflowTrigger.created_at.desc()
            ).all()
            return triggers
        finally:
            session.close()

    @staticmethod
    def toggle_trigger(trigger_id: int) -> Optional[bool]:
        """Toggle a trigger's active state"""
        session = get_db()
        try:
            trigger = (
                session.query(WorkflowTrigger)
                .filter(WorkflowTrigger.id == trigger_id)
                .first()
            )

            if not trigger:
                return None

            trigger.is_active = not trigger.is_active
            trigger.updated_at = datetime.utcnow()
            session.commit()
            return trigger.is_active
        finally:
            session.close()

    @staticmethod
    def evaluate_triggers(
        event_type: str, event_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Evaluate all matching triggers for an event and execute actions"""
        if event_type not in TRIGGER_TYPES:
            return []

        session = get_db()
        results = []

        try:
            triggers = (
                session.query(WorkflowTrigger)
                .filter(
                    and_(
                        WorkflowTrigger.trigger_type == event_type,
                        WorkflowTrigger.is_active == True,
                    )
                )
                .order_by(WorkflowTrigger.priority.desc())
                .all()
            )

            for trigger in triggers:
                if WorkflowTriggersService._check_conditions(
                    trigger.conditions, event_data
                ):
                    from services.task_queue_service import TaskQueueService

                    task = TaskQueueService.enqueue_task(
                        task_type="execute_workflow",
                        payload={
                            "trigger_id": trigger.id,
                            "event_type": event_type,
                            "event_data": event_data,
                        },
                        priority=trigger.priority,
                        client_id=event_data.get("client_id"),
                    )

                    results.append(
                        {
                            "trigger_id": trigger.id,
                            "trigger_name": trigger.name,
                            "task_id": task.id,
                            "status": "queued",
                        }
                    )

            return results
        finally:
            session.close()

    @staticmethod
    def _check_conditions(
        conditions: Dict[str, Any], event_data: Dict[str, Any]
    ) -> bool:
        """Check if event data matches trigger conditions"""
        if not conditions:
            return True

        for key, expected_value in conditions.items():
            if key.endswith("_min"):
                field = key[:-4]
                if field in event_data:
                    if event_data[field] < expected_value:
                        return False
            elif key.endswith("_max"):
                field = key[:-4]
                if field in event_data:
                    if event_data[field] > expected_value:
                        return False
            elif key.endswith("_in"):
                field = key[:-3]
                if field in event_data:
                    if event_data[field] not in expected_value:
                        return False
            elif key.endswith("_not_in"):
                field = key[:-7]
                if field in event_data:
                    if event_data[field] in expected_value:
                        return False
            elif key in event_data:
                if event_data[key] != expected_value:
                    return False

        return True

    @staticmethod
    def execute_actions(
        trigger_id: int, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute all actions for a trigger"""
        session = get_db()
        start_time = time.time()

        try:
            trigger = (
                session.query(WorkflowTrigger)
                .filter(WorkflowTrigger.id == trigger_id)
                .first()
            )

            if not trigger:
                return {"success": False, "error": "Trigger not found"}

            client_id = event_data.get("client_id")
            actions_executed = []
            errors = []

            for action in trigger.actions:
                action_result = WorkflowTriggersService._execute_single_action(
                    session, action, cast(int, client_id) if client_id else 0, event_data
                )
                actions_executed.append(action_result)
                if not action_result.get("success"):
                    errors.append(action_result.get("error"))

            execution_time = int((time.time() - start_time) * 1000)

            if not errors:
                status = "success"
                error_message = None
            elif len(errors) == len(trigger.actions):
                status = "failed"
                error_message = "; ".join(str(e) for e in errors if e)
            else:
                status = "partial"
                error_message = "; ".join(str(e) for e in errors if e)

            execution = WorkflowExecution(
                trigger_id=trigger_id,
                client_id=client_id,
                trigger_event={"type": event_type, "data": event_data},
                actions_executed=actions_executed,
                status=status,
                error_message=error_message,
                execution_time_ms=execution_time,
            )
            session.add(execution)

            trigger.last_triggered = datetime.utcnow()
            trigger.trigger_count = (trigger.trigger_count or 0) + 1

            session.commit()

            return {
                "success": status != "failed",
                "execution_id": execution.id,
                "status": status,
                "actions_executed": len(actions_executed),
                "execution_time_ms": execution_time,
                "errors": errors if errors else None,
            }
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
        finally:
            session.close()

    @staticmethod
    def _execute_single_action(
        session, action: Dict[str, Any], client_id: int, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.get("type")
        params = action.get("params", {})

        try:
            if action_type == "send_email":
                result = WorkflowTriggersService._action_send_email(
                    session, client_id, params, event_data
                )
            elif action_type == "send_sms":
                result = WorkflowTriggersService._action_send_sms(
                    session, client_id, params, event_data
                )
            elif action_type == "create_task":
                result = WorkflowTriggersService._action_create_task(
                    client_id, params, event_data
                )
            elif action_type == "update_status":
                result = WorkflowTriggersService._action_update_status(
                    session, client_id, params
                )
            elif action_type == "assign_attorney":
                result = WorkflowTriggersService._action_assign_attorney(
                    session, client_id, params
                )
            elif action_type == "add_note":
                result = WorkflowTriggersService._action_add_note(
                    session, client_id, params, event_data
                )
            elif action_type == "schedule_followup":
                result = WorkflowTriggersService._action_schedule_followup(
                    session, client_id, params, event_data
                )
            elif action_type == "generate_document":
                result = WorkflowTriggersService._action_generate_document(
                    client_id, params, event_data
                )
            else:
                result = {
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                }

            return {
                "action_type": action_type,
                "success": result.get("success", False),
                "result": result.get("result"),
                "error": result.get("error"),
            }
        except Exception as e:
            return {"action_type": action_type, "success": False, "error": str(e)}

    @staticmethod
    def _action_send_email(
        session, client_id: int, params: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send email action"""
        try:
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client or not client.email:
                return {"success": False, "error": "Client email not found"}

            from services.task_queue_service import TaskQueueService

            task = TaskQueueService.enqueue_task(
                task_type="send_email",
                payload={
                    "to_email": params.get("to_override") or client.email,
                    "subject": params.get("subject", "Notification"),
                    "template": params.get("template"),
                    "template_data": {
                        "client_name": client.name,
                        "client_first_name": client.first_name
                        or client.name.split()[0],
                        **event_data,
                    },
                },
                client_id=client_id,
                priority=5,
            )

            return {"success": True, "result": {"task_id": task.id}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _action_send_sms(
        session, client_id: int, params: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send SMS action - only sends if client has opted in"""
        try:
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client or not client.phone:
                return {"success": False, "error": "Client phone not found"}

            # Check SMS opt-in before sending
            if not getattr(client, 'sms_opt_in', False):
                return {"success": False, "error": "Client has not opted in for SMS", "skipped": True}

            from services.task_queue_service import TaskQueueService

            task = TaskQueueService.enqueue_task(
                task_type="send_sms",
                payload={
                    "to_phone": client.phone,
                    "message": params.get(
                        "message", "You have a notification from Brightpath Ascend."
                    ),
                },
                client_id=client_id,
                priority=5,
            )

            return {"success": True, "result": {"task_id": task.id}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _action_create_task(
        client_id: int, params: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create background task action"""
        try:
            from services.task_queue_service import TaskQueueService

            payload = params.get("payload", {})
            payload["client_id"] = client_id
            payload["event_data"] = event_data

            task = TaskQueueService.enqueue_task(
                task_type=params.get("task_type", "custom"),
                payload=payload,
                client_id=client_id,
                priority=params.get("priority", 5),
            )

            return {"success": True, "result": {"task_id": task.id}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _action_update_status(
        session, client_id: int, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update case status action"""
        try:
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {"success": False, "error": "Client not found"}

            old_status = client.status
            client.status = params.get("new_status", client.status)
            client.updated_at = datetime.utcnow()

            return {
                "success": True,
                "result": {"old_status": old_status, "new_status": client.status},
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _action_assign_attorney(
        session, client_id: int, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assign attorney action"""
        try:
            return {
                "success": True,
                "result": {
                    "staff_id": params.get("staff_id"),
                    "assignment_type": params.get("assignment_type", "primary"),
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _action_add_note(
        session, client_id: int, params: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add case note action"""
        try:
            note = ClientNote(
                client_id=client_id,
                note=params.get("note_text", "Automated workflow note"),
                note_type=params.get("note_type", "system"),
                is_internal=True,
                created_at=datetime.utcnow(),
            )
            session.add(note)

            return {"success": True, "result": {"note_added": True}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _action_schedule_followup(
        session, client_id: int, params: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule followup action"""
        try:
            days_from_now = params.get("days_from_now", 7)
            deadline_date = datetime.utcnow() + timedelta(days=days_from_now)

            deadline = CaseDeadline(
                client_id=client_id,
                deadline_type=params.get("deadline_type", "followup"),
                deadline_date=deadline_date.date(),
                description=params.get("description", "Automated followup"),
                status="pending",
                is_automated=True,
                created_at=datetime.utcnow(),
            )
            session.add(deadline)

            return {
                "success": True,
                "result": {
                    "deadline_date": deadline_date.isoformat(),
                    "deadline_type": params.get("deadline_type", "followup"),
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _action_generate_document(
        client_id: int, params: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate document action"""
        try:
            from services.task_queue_service import TaskQueueService

            task = TaskQueueService.enqueue_task(
                task_type="generate_document",
                payload={
                    "client_id": client_id,
                    "template_name": params.get("template_name"),
                    "document_type": params.get("document_type"),
                    "event_data": event_data,
                },
                client_id=client_id,
                priority=5,
            )

            return {"success": True, "result": {"task_id": task.id}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_trigger_history(trigger_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history for a trigger"""
        session = get_db()
        try:
            executions = (
                session.query(WorkflowExecution)
                .filter(WorkflowExecution.trigger_id == trigger_id)
                .order_by(WorkflowExecution.created_at.desc())
                .limit(limit)
                .all()
            )

            return [e.to_dict() for e in executions]
        finally:
            session.close()

    @staticmethod
    def get_recent_executions(limit: int = 100) -> List[Dict[str, Any]]:
        """Get all recent executions across all triggers"""
        session = get_db()
        try:
            executions = (
                session.query(WorkflowExecution)
                .order_by(WorkflowExecution.created_at.desc())
                .limit(limit)
                .all()
            )

            result = []
            for e in executions:
                exec_dict = e.to_dict()
                trigger = (
                    session.query(WorkflowTrigger)
                    .filter(WorkflowTrigger.id == e.trigger_id)
                    .first()
                )
                if trigger:
                    exec_dict["trigger_name"] = trigger.name
                    exec_dict["trigger_type"] = trigger.trigger_type
                result.append(exec_dict)

            return result
        finally:
            session.close()

    @staticmethod
    def get_trigger_stats() -> Dict[str, Any]:
        """Get performance metrics for workflow triggers"""
        session = get_db()
        try:
            total_triggers = session.query(WorkflowTrigger).count()
            active_triggers = (
                session.query(WorkflowTrigger)
                .filter(WorkflowTrigger.is_active == True)
                .count()
            )

            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            executions_today = (
                session.query(WorkflowExecution)
                .filter(WorkflowExecution.created_at >= today)
                .count()
            )

            successful_today = (
                session.query(WorkflowExecution)
                .filter(
                    and_(
                        WorkflowExecution.created_at >= today,
                        WorkflowExecution.status == "success",
                    )
                )
                .count()
            )

            failed_today = (
                session.query(WorkflowExecution)
                .filter(
                    and_(
                        WorkflowExecution.created_at >= today,
                        WorkflowExecution.status == "failed",
                    )
                )
                .count()
            )

            avg_time = (
                session.query(func.avg(WorkflowExecution.execution_time_ms))
                .filter(
                    and_(
                        WorkflowExecution.created_at >= today,
                        WorkflowExecution.execution_time_ms.isnot(None),
                    )
                )
                .scalar()
                or 0
            )

            total_executions = session.query(WorkflowExecution).count()
            total_successful = (
                session.query(WorkflowExecution)
                .filter(WorkflowExecution.status == "success")
                .count()
            )

            by_type = (
                session.query(
                    WorkflowTrigger.trigger_type, func.count(WorkflowTrigger.id)
                )
                .group_by(WorkflowTrigger.trigger_type)
                .all()
            )

            return {
                "total_triggers": total_triggers,
                "active_triggers": active_triggers,
                "inactive_triggers": total_triggers - active_triggers,
                "executions_today": executions_today,
                "successful_today": successful_today,
                "failed_today": failed_today,
                "success_rate_today": round(
                    (
                        (successful_today / executions_today * 100)
                        if executions_today > 0
                        else 100
                    ),
                    1,
                ),
                "avg_execution_time_ms": round(avg_time, 2),
                "total_executions": total_executions,
                "overall_success_rate": round(
                    (
                        (total_successful / total_executions * 100)
                        if total_executions > 0
                        else 100
                    ),
                    1,
                ),
                "triggers_by_type": {t: c for t, c in by_type},
            }
        finally:
            session.close()

    @staticmethod
    def test_trigger(
        trigger_id: int, sample_event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test a trigger with sample data without recording execution"""
        session = get_db()
        try:
            trigger = (
                session.query(WorkflowTrigger)
                .filter(WorkflowTrigger.id == trigger_id)
                .first()
            )

            if not trigger:
                return {"success": False, "error": "Trigger not found"}

            conditions_match = WorkflowTriggersService._check_conditions(
                trigger.conditions, sample_event_data
            )

            actions_preview = []
            for action in trigger.actions:
                actions_preview.append(
                    {
                        "type": action.get("type"),
                        "params": action.get("params", {}),
                        "would_execute": conditions_match,
                    }
                )

            return {
                "success": True,
                "trigger_name": trigger.name,
                "trigger_type": trigger.trigger_type,
                "conditions_match": conditions_match,
                "conditions": trigger.conditions,
                "event_data_used": sample_event_data,
                "actions_preview": actions_preview,
            }
        finally:
            session.close()

    @staticmethod
    def initialize_default_triggers() -> List[WorkflowTrigger]:
        """Create default triggers if they don't exist"""
        session = get_db()
        created = []

        try:
            for trigger_data in DEFAULT_TRIGGERS:
                existing = (
                    session.query(WorkflowTrigger)
                    .filter(WorkflowTrigger.name == trigger_data["name"])
                    .first()
                )

                if not existing:
                    trigger = WorkflowTrigger(
                        name=trigger_data["name"],
                        description=trigger_data["description"],
                        trigger_type=trigger_data["trigger_type"],
                        conditions=trigger_data.get("conditions", {}),
                        actions=trigger_data["actions"],
                        priority=trigger_data.get("priority", 5),
                        is_active=True,
                    )
                    session.add(trigger)
                    created.append(trigger)

            session.commit()
            return created
        except Exception as e:
            session.rollback()
            print(f"Error initializing default triggers: {e}")
            return []
        finally:
            session.close()


from services.task_queue_service import register_task_handler


@register_task_handler("execute_workflow")
def handle_execute_workflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Task handler for executing workflow actions"""
    trigger_id = payload.get("trigger_id")
    event_type = payload.get("event_type")
    event_data = payload.get("event_data", {})

    return WorkflowTriggersService.execute_actions(
        cast(int, trigger_id) if trigger_id else 0,
        cast(str, event_type) if event_type else "",
        event_data
    )
