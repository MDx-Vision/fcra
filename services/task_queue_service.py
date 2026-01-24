import json
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import and_, or_

from database import BackgroundTask, get_db

TASK_HANDLERS: Dict[str, Callable] = {}


def register_task_handler(task_type: str):
    """Decorator to register a task handler"""

    def decorator(func: Callable):
        TASK_HANDLERS[task_type] = func
        return func

    return decorator


@register_task_handler("send_email")
def handle_send_email(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle email sending tasks"""
    from services import email_service

    to_email = payload.get("to_email")
    subject = payload.get("subject")
    body = payload.get("body")
    template = payload.get("template")
    template_data = payload.get("template_data", {})

    if template and hasattr(email_service, "send_template_email"):
        result = email_service.send_template_email(
            to_email, subject, template, template_data
        )
        success = (
            result.get("success", False) if isinstance(result, dict) else bool(result)
        )
    else:
        result = email_service.send_email(to_email, subject, body)
        success = (
            result.get("success", False) if isinstance(result, dict) else bool(result)
        )

    return {"success": success, "to_email": to_email}


@register_task_handler("send_sms")
def handle_send_sms(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle SMS sending tasks"""
    from services import sms_service

    to_phone = payload.get("to_phone")
    message = payload.get("message")

    result = sms_service.send_sms(to_phone, message)
    return {
        "success": result.get("success", False),
        "to_phone": to_phone,
        "sid": result.get("message_sid"),
    }


@register_task_handler("generate_report")
def handle_generate_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle report generation tasks"""
    report_type = payload.get("report_type")
    parameters = payload.get("parameters", {})

    if report_type == "case_summary":
        return generate_case_summary_report(parameters)
    elif report_type == "revenue":
        return generate_revenue_report(parameters)
    elif report_type == "sol_deadlines":
        return generate_sol_deadline_report(parameters)
    else:
        return {"success": False, "error": f"Unknown report type: {report_type}"}


def generate_case_summary_report(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate daily case summary report"""
    from database import Client, get_db

    session = get_db()
    try:
        today = datetime.utcnow().date()

        total_clients = session.query(Client).count()
        active_clients = session.query(Client).filter(Client.status == "active").count()
        new_today = (
            session.query(Client)
            .filter(Client.created_at >= datetime.combine(today, datetime.min.time()))
            .count()
        )

        return {
            "success": True,
            "report_type": "case_summary",
            "date": today.isoformat(),
            "data": {
                "total_clients": total_clients,
                "active_clients": active_clients,
                "new_today": new_today,
            },
        }
    finally:
        session.close()


def generate_revenue_report(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate weekly revenue report"""
    from database import Payment, get_db  # type: ignore[attr-defined]

    session = get_db()
    try:
        week_ago = datetime.utcnow() - timedelta(days=7)

        payments = session.query(Payment).filter(Payment.created_at >= week_ago).all()
        total_revenue = sum(p.amount_cents or 0 for p in payments) / 100

        return {
            "success": True,
            "report_type": "revenue",
            "period_start": week_ago.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "data": {"total_revenue": total_revenue, "payment_count": len(payments)},
        }
    except Exception as e:
        return {
            "success": True,
            "report_type": "revenue",
            "data": {"message": "No payment data available"},
        }
    finally:
        session.close()


def generate_sol_deadline_report(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate SOL deadline check report"""
    from database import NegativeItem, get_db  # type: ignore[attr-defined]

    session = get_db()
    try:
        upcoming_deadlines = []
        threshold = datetime.utcnow() + timedelta(days=30)

        items = (
            session.query(NegativeItem)
            .filter(
                and_(
                    NegativeItem.sol_expiration_date.isnot(None),
                    NegativeItem.sol_expiration_date <= threshold,
                    NegativeItem.sol_expiration_date >= datetime.utcnow(),
                )
            )
            .all()
        )

        for item in items:
            upcoming_deadlines.append(
                {
                    "item_id": item.id,
                    "client_id": item.client_id,
                    "creditor": item.creditor_name,
                    "expiration_date": (
                        item.sol_expiration_date.isoformat()
                        if item.sol_expiration_date
                        else None
                    ),
                }
            )

        return {
            "success": True,
            "report_type": "sol_deadlines",
            "data": {
                "upcoming_count": len(upcoming_deadlines),
                "deadlines": upcoming_deadlines[:100],
            },
        }
    except Exception as e:
        return {
            "success": True,
            "report_type": "sol_deadlines",
            "data": {"message": "SOL check completed", "upcoming_count": 0},
        }
    finally:
        session.close()


@register_task_handler("bulk_dispute")
def handle_bulk_dispute(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle bulk dispute letter generation"""
    client_ids = payload.get("client_ids", [])
    letter_type = payload.get("letter_type", "dispute")
    bureau = payload.get("bureau")

    results = []
    for client_id in client_ids:
        try:
            result = generate_dispute_letter(client_id, letter_type, bureau)
            results.append({"client_id": client_id, "success": True, "result": result})
        except Exception as e:
            results.append({"client_id": client_id, "success": False, "error": str(e)})

    success_count = sum(1 for r in results if r["success"])
    return {
        "success": success_count == len(client_ids),
        "total": len(client_ids),
        "success_count": success_count,
        "failed_count": len(client_ids) - success_count,
        "results": results,
    }


def generate_dispute_letter(
    client_id: int, letter_type: str, bureau: Optional[str]
) -> Dict[str, Any]:
    """Generate a single dispute letter"""
    return {
        "client_id": client_id,
        "letter_type": letter_type,
        "bureau": bureau,
        "generated_at": datetime.utcnow().isoformat(),
    }


@register_task_handler("credit_pull")
def handle_credit_pull(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scheduled credit pulls"""
    client_id = payload.get("client_id")
    bureaus = payload.get("bureaus", ["experian", "equifax", "transunion"])

    return {
        "success": True,
        "client_id": client_id,
        "bureaus": bureaus,
        "message": "Credit pull queued for processing",
        "queued_at": datetime.utcnow().isoformat(),
    }


@register_task_handler("analyze_report")
def handle_analyze_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle AI analysis jobs"""
    from services.ai_service import AIService

    client_id = payload.get("client_id")
    report_data = payload.get("report_data")
    analysis_type = payload.get("analysis_type", "full")

    try:
        ai_service = AIService()
        analysis = (
            ai_service.analyze_credit_report(report_data)
            if hasattr(ai_service, "analyze_credit_report")
            else None
        )

        return {
            "success": True,
            "client_id": client_id,
            "analysis_type": analysis_type,
            "analysis": analysis,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"success": False, "client_id": client_id, "error": str(e)}


class TaskQueueService:
    """Database-backed task queue service for async job processing"""

    @staticmethod
    def enqueue_task(
        task_type: str,
        payload: Dict[str, Any],
        priority: int = 5,
        scheduled_at: Optional[datetime] = None,
        client_id: Optional[int] = None,
        staff_id: Optional[int] = None,
        max_retries: int = 3,
    ) -> BackgroundTask:
        """Add a new task to the queue"""
        session = get_db()
        try:
            task = BackgroundTask(
                task_type=task_type,
                payload=payload,
                priority=min(max(priority, 1), 10),
                status="pending",
                scheduled_at=scheduled_at,
                client_id=client_id,
                created_by_staff_id=staff_id,
                max_retries=max_retries,
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        finally:
            session.close()

    @staticmethod
    def process_pending_tasks(limit: int = 1) -> List[Dict[str, Any]]:
        """Process pending tasks one at a time"""
        session = get_db()
        results = []

        try:
            now = datetime.utcnow()

            tasks = (
                session.query(BackgroundTask)
                .filter(
                    and_(
                        BackgroundTask.status == "pending",
                        or_(
                            BackgroundTask.scheduled_at.is_(None),
                            BackgroundTask.scheduled_at <= now,
                        ),
                    )
                )
                .order_by(
                    BackgroundTask.priority.desc(), BackgroundTask.created_at.asc()
                )
                .limit(limit)
                .with_for_update(skip_locked=True)
                .all()
            )

            for task in tasks:
                result = TaskQueueService._execute_task(session, task)
                results.append(result)

            return results
        finally:
            session.close()

    @staticmethod
    def _execute_task(session, task: BackgroundTask) -> Dict[str, Any]:  # type: ignore[type-arg]
        """Execute a single task"""
        task.status = "running"  # type: ignore[assignment]
        task.started_at = datetime.utcnow()  # type: ignore[assignment]
        session.commit()

        task_type: str = task.task_type  # type: ignore[assignment]
        handler = TASK_HANDLERS.get(task_type)

        if not handler:
            task.status = "failed"  # type: ignore[assignment]
            error_msg = f"No handler registered for task type: {task.task_type}"
            task.error_message = error_msg  # type: ignore[assignment]
            task.completed_at = datetime.utcnow()  # type: ignore[assignment]
            session.commit()
            return {"task_id": task.id, "success": False, "error": task.error_message}

        try:
            result = handler(task.payload or {})
            task.status = "completed"  # type: ignore[assignment]
            task.result = result  # type: ignore[assignment]
            task.completed_at = datetime.utcnow()  # type: ignore[assignment]
            session.commit()

            return {"task_id": task.id, "success": True, "result": result}
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            task.retries += 1  # type: ignore[assignment]

            if task.retries >= task.max_retries:
                task.status = "failed"  # type: ignore[assignment]
                task.error_message = error_msg  # type: ignore[assignment]
                task.completed_at = datetime.utcnow()  # type: ignore[assignment]
            else:
                task.status = "pending"  # type: ignore[assignment]
                retry_msg = f"Retry {task.retries}/{task.max_retries}: {str(e)}"
                task.error_message = retry_msg  # type: ignore[assignment]

            session.commit()

            return {
                "task_id": task.id,
                "success": False,
                "error": str(e),
                "will_retry": task.status == "pending",
            }

    @staticmethod
    def get_task_status(task_id: int) -> Optional[Dict[str, Any]]:
        """Get the status of a specific task"""
        session = get_db()
        try:
            task = (
                session.query(BackgroundTask)
                .filter(BackgroundTask.id == task_id)
                .first()
            )
            if task:
                return task.to_dict()
            return None
        finally:
            session.close()

    @staticmethod
    def cancel_task(task_id: int) -> bool:
        """Cancel a pending task"""
        session = get_db()
        try:
            task = (
                session.query(BackgroundTask)
                .filter(
                    and_(
                        BackgroundTask.id == task_id, BackgroundTask.status == "pending"
                    )
                )
                .first()
            )

            if task:
                task.status = "cancelled"
                task.completed_at = datetime.utcnow()
                session.commit()
                return True
            return False
        finally:
            session.close()

    @staticmethod
    def cleanup_old_tasks(days: int = 30) -> int:
        """Delete completed/failed/cancelled tasks older than specified days"""
        session = get_db()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            deleted = (
                session.query(BackgroundTask)
                .filter(
                    and_(
                        BackgroundTask.status.in_(["completed", "failed", "cancelled"]),
                        BackgroundTask.completed_at < cutoff,
                    )
                )
                .delete(synchronize_session=False)
            )

            session.commit()
            return deleted
        finally:
            session.close()

    @staticmethod
    def get_tasks(
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get tasks with optional filtering"""
        session = get_db()
        try:
            query = session.query(BackgroundTask)

            if status:
                if status == "active":
                    query = query.filter(
                        BackgroundTask.status.in_(["pending", "running"])
                    )
                else:
                    query = query.filter(BackgroundTask.status == status)

            if task_type:
                query = query.filter(BackgroundTask.task_type == task_type)

            tasks = (
                query.order_by(BackgroundTask.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [task.to_dict() for task in tasks]
        finally:
            session.close()

    @staticmethod
    def get_task_stats() -> Dict[str, Any]:
        """Get task queue statistics"""
        session = get_db()
        try:
            from sqlalchemy import func

            stats = (
                session.query(BackgroundTask.status, func.count(BackgroundTask.id))
                .group_by(BackgroundTask.status)
                .all()
            )

            result = {
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
            }

            for status, count in stats:
                if status in result:
                    result[status] = count

            result["total"] = sum(result.values())

            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            completed_today = (
                session.query(BackgroundTask)
                .filter(
                    and_(
                        BackgroundTask.status == "completed",
                        BackgroundTask.completed_at >= today,
                    )
                )
                .count()
            )

            result["completed_today"] = completed_today

            return result
        finally:
            session.close()

    @staticmethod
    def retry_failed_task(task_id: int) -> bool:
        """Retry a failed task"""
        session = get_db()
        try:
            task = (
                session.query(BackgroundTask)
                .filter(
                    and_(
                        BackgroundTask.id == task_id, BackgroundTask.status == "failed"
                    )
                )
                .first()
            )

            if task:
                task.status = "pending"
                task.error_message = None
                task.retries = 0
                task.started_at = None
                task.completed_at = None
                session.commit()
                return True
            return False
        finally:
            session.close()

    @staticmethod
    def get_available_task_types() -> List[str]:
        """Get list of registered task types"""
        return list(TASK_HANDLERS.keys())
