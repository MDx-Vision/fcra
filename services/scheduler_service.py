import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_

from database import ScheduledJob, get_db
from services.task_queue_service import TaskQueueService


class CronParser:
    """Simple cron expression parser for scheduling"""

    @staticmethod
    def parse(expression: str) -> Dict[str, Any]:
        """Parse a cron expression into components
        Format: minute hour day_of_month month day_of_week
        Supports: *, specific values, ranges (1-5), steps (*/5)
        """
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression: {expression}. Expected 5 parts."
            )

        return {
            "minute": parts[0],
            "hour": parts[1],
            "day_of_month": parts[2],
            "month": parts[3],
            "day_of_week": parts[4],
        }

    @staticmethod
    def matches(expression: str, dt: datetime) -> bool:
        """Check if a datetime matches a cron expression"""
        try:
            parsed = CronParser.parse(expression)

            if not CronParser._matches_field(parsed["minute"], dt.minute, 0, 59):
                return False
            if not CronParser._matches_field(parsed["hour"], dt.hour, 0, 23):
                return False
            if not CronParser._matches_field(parsed["day_of_month"], dt.day, 1, 31):
                return False
            if not CronParser._matches_field(parsed["month"], dt.month, 1, 12):
                return False
            if not CronParser._matches_field(parsed["day_of_week"], dt.weekday(), 0, 6):
                return False

            return True
        except Exception:
            return False

    @staticmethod
    def _matches_field(field: str, value: int, min_val: int, max_val: int) -> bool:
        """Check if a value matches a cron field"""
        if field == "*":
            return True

        if "/" in field:
            base, step = field.split("/")
            step = int(step)
            if base == "*":
                return value % step == 0
            else:
                start = int(base)
                return value >= start and (value - start) % step == 0

        if "-" in field:
            start, end = map(int, field.split("-"))
            return start <= value <= end

        if "," in field:
            values = [int(v) for v in field.split(",")]
            return value in values

        return value == int(field)

    @staticmethod
    def get_next_run(expression: str, from_dt: Optional[datetime] = None) -> datetime:
        """Calculate the next run time for a cron expression"""
        if from_dt is None:
            from_dt = datetime.utcnow()

        dt = from_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)

        for _ in range(525600):
            if CronParser.matches(expression, dt):
                return dt
            dt += timedelta(minutes=1)

        return from_dt + timedelta(days=1)

    @staticmethod
    def describe(expression: str) -> str:
        """Generate a human-readable description of a cron expression"""
        try:
            parsed = CronParser.parse(expression)

            descriptions = {
                "0 9 * * *": "Daily at 9:00 AM",
                "0 8 * * 1": "Weekly on Monday at 8:00 AM",
                "0 6 * * *": "Daily at 6:00 AM",
                "*/5 * * * *": "Every 5 minutes",
                "0 * * * *": "Every hour",
                "0 0 * * *": "Daily at midnight",
                "0 0 1 * *": "Monthly on the 1st at midnight",
            }

            if expression in descriptions:
                return descriptions[expression]

            hour = parsed["hour"]
            minute = parsed["minute"]
            dow = parsed["day_of_week"]

            time_str = ""
            if hour != "*" and minute != "*":
                h = int(hour) if hour.isdigit() else 0
                m = int(minute) if minute.isdigit() else 0
                am_pm = "AM" if h < 12 else "PM"
                h = h if h <= 12 else h - 12
                h = 12 if h == 0 else h
                time_str = f"at {h}:{m:02d} {am_pm}"

            if dow != "*":
                days = [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]
                day_idx = int(dow) if dow.isdigit() else 0
                return f"Weekly on {days[day_idx]} {time_str}"

            if parsed["day_of_month"] != "*":
                return f"Monthly on day {parsed['day_of_month']} {time_str}"

            if time_str:
                return f"Daily {time_str}"

            return expression
        except Exception:
            return expression


class SchedulerService:
    """Service for managing scheduled jobs"""

    BUILT_IN_SCHEDULES = [
        {
            "name": "Daily Case Summary Report",
            "task_type": "generate_report",
            "payload": {"report_type": "case_summary"},
            "cron_expression": "0 9 * * *",
        },
        {
            "name": "Weekly Revenue Report",
            "task_type": "generate_report",
            "payload": {"report_type": "revenue"},
            "cron_expression": "0 8 * * 1",
        },
        {
            "name": "SOL Deadline Checks",
            "task_type": "generate_report",
            "payload": {"report_type": "sol_deadlines"},
            "cron_expression": "0 6 * * *",
        },
        # VA Letter Automation - Downloads tracking info from SFTP, updates letter status and deadlines
        {
            "name": "Check SendCertified Tracking Updates",
            "task_type": "check_sendcertified_tracking",
            "payload": {"update_deadlines": True},
            "cron_expression": "0 6 * * *",
        },
        # VA Letter Automation - Finds overdue CRA responses (35+ days), sends alerts, creates escalation tasks
        {
            "name": "Check CRA Response Deadlines",
            "task_type": "check_cra_response_deadlines",
            "payload": {
                "days_overdue_threshold": 35,
                "send_notifications": True,
                "create_escalation_tasks": True,
            },
            "cron_expression": "0 9 * * *",
        },
    ]

    @staticmethod
    def initialize_built_in_schedules() -> List[ScheduledJob]:
        """Create built-in schedules if they don't exist"""
        session = get_db()
        created = []

        try:
            for schedule in SchedulerService.BUILT_IN_SCHEDULES:
                existing = (
                    session.query(ScheduledJob)
                    .filter(ScheduledJob.name == schedule["name"])
                    .first()
                )

                if not existing:
                    job = ScheduledJob(
                        name=schedule["name"],
                        task_type=schedule["task_type"],
                        payload=schedule["payload"],
                        cron_expression=schedule["cron_expression"],
                        is_active=True,
                        next_run=CronParser.get_next_run(schedule["cron_expression"]),
                    )
                    session.add(job)
                    created.append(job)

            session.commit()
            return created
        finally:
            session.close()

    @staticmethod
    def create_schedule(
        name: str,
        task_type: str,
        payload: Dict[str, Any],
        cron_expression: str,
        staff_id: Optional[int] = None,
    ) -> ScheduledJob:
        """Create a new scheduled job"""
        CronParser.parse(cron_expression)

        session = get_db()
        try:
            job = ScheduledJob(
                name=name,
                task_type=task_type,
                payload=payload,
                cron_expression=cron_expression,
                is_active=True,
                next_run=CronParser.get_next_run(cron_expression),
                created_by_staff_id=staff_id,
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job
        finally:
            session.close()

    @staticmethod
    def update_schedule(job_id: int, **kwargs) -> Optional[ScheduledJob]:
        """Update an existing scheduled job"""
        session = get_db()
        try:
            job = session.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()

            if not job:
                return None

            if "name" in kwargs:
                job.name = kwargs["name"]
            if "task_type" in kwargs:
                job.task_type = kwargs["task_type"]
            if "payload" in kwargs:
                job.payload = kwargs["payload"]
            if "cron_expression" in kwargs:
                CronParser.parse(kwargs["cron_expression"])
                job.cron_expression = kwargs["cron_expression"]
                job.next_run = CronParser.get_next_run(kwargs["cron_expression"])
            if "is_active" in kwargs:
                job.is_active = kwargs["is_active"]
                if kwargs["is_active"] and not job.next_run:
                    job.next_run = CronParser.get_next_run(job.cron_expression)

            job.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(job)
            return job
        finally:
            session.close()

    @staticmethod
    def delete_schedule(job_id: int) -> bool:
        """Delete a scheduled job"""
        session = get_db()
        try:
            job = session.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            if job:
                session.delete(job)
                session.commit()
                return True
            return False
        finally:
            session.close()

    @staticmethod
    def get_schedule(job_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific scheduled job"""
        session = get_db()
        try:
            job = session.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            if job:
                result = job.to_dict()
                result["cron_description"] = CronParser.describe(job.cron_expression)
                return result
            return None
        finally:
            session.close()

    @staticmethod
    def get_all_schedules(active_only: bool = False) -> List[Dict[str, Any]]:
        """Get all scheduled jobs"""
        session = get_db()
        try:
            query = session.query(ScheduledJob)
            if active_only:
                query = query.filter(ScheduledJob.is_active == True)

            jobs = query.order_by(ScheduledJob.name).all()
            result = []
            for job in jobs:
                job_dict = job.to_dict()
                job_dict["cron_description"] = CronParser.describe(job.cron_expression)
                result.append(job_dict)
            return result
        finally:
            session.close()

    @staticmethod
    def get_due_jobs() -> List[ScheduledJob]:
        """Get jobs that are due to run"""
        session = get_db()
        try:
            now = datetime.utcnow()

            jobs = (
                session.query(ScheduledJob)
                .filter(
                    and_(ScheduledJob.is_active == True, ScheduledJob.next_run <= now)
                )
                .all()
            )

            return jobs
        finally:
            session.close()

    @staticmethod
    def run_due_jobs() -> List[Dict[str, Any]]:
        """Enqueue tasks for all due scheduled jobs"""
        session = get_db()
        results = []

        try:
            now = datetime.utcnow()

            jobs = (
                session.query(ScheduledJob)
                .filter(
                    and_(ScheduledJob.is_active == True, ScheduledJob.next_run <= now)
                )
                .all()
            )

            for job in jobs:
                try:
                    task = TaskQueueService.enqueue_task(
                        task_type=job.task_type, payload=job.payload or {}, priority=7
                    )

                    job.last_run = now
                    job.run_count += 1
                    job.next_run = CronParser.get_next_run(job.cron_expression, now)
                    job.last_status = "enqueued"
                    job.last_error = None

                    results.append(
                        {
                            "job_id": job.id,
                            "job_name": job.name,
                            "task_id": task.id,
                            "success": True,
                        }
                    )
                except Exception as e:
                    job.last_status = "error"
                    job.last_error = str(e)

                    results.append(
                        {
                            "job_id": job.id,
                            "job_name": job.name,
                            "success": False,
                            "error": str(e),
                        }
                    )

            session.commit()
            return results
        finally:
            session.close()

    @staticmethod
    def run_job_now(job_id: int) -> Optional[Dict[str, Any]]:
        """Manually trigger a scheduled job to run immediately"""
        session = get_db()
        try:
            job = session.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()

            if not job:
                return None

            task = TaskQueueService.enqueue_task(
                task_type=job.task_type, payload=job.payload or {}, priority=8
            )

            job.last_run = datetime.utcnow()
            job.run_count += 1
            job.last_status = "manual_run"
            session.commit()

            return {
                "job_id": job.id,
                "job_name": job.name,
                "task_id": task.id,
                "success": True,
            }
        finally:
            session.close()

    @staticmethod
    def pause_schedule(job_id: int) -> bool:
        """Pause a scheduled job"""
        return SchedulerService.update_schedule(job_id, is_active=False) is not None

    @staticmethod
    def resume_schedule(job_id: int) -> bool:
        """Resume a paused scheduled job"""
        return SchedulerService.update_schedule(job_id, is_active=True) is not None

    @staticmethod
    def get_scheduler_stats() -> Dict[str, Any]:
        """Get scheduler statistics"""
        session = get_db()
        try:
            total = session.query(ScheduledJob).count()
            active = (
                session.query(ScheduledJob)
                .filter(ScheduledJob.is_active == True)
                .count()
            )
            paused = total - active

            from sqlalchemy import func

            total_runs = session.query(func.sum(ScheduledJob.run_count)).scalar() or 0

            next_job = (
                session.query(ScheduledJob)
                .filter(
                    and_(
                        ScheduledJob.is_active == True,
                        ScheduledJob.next_run.isnot(None),
                    )
                )
                .order_by(ScheduledJob.next_run.asc())
                .first()
            )

            return {
                "total_schedules": total,
                "active_schedules": active,
                "paused_schedules": paused,
                "total_runs": total_runs,
                "next_scheduled_job": (
                    {
                        "id": next_job.id,
                        "name": next_job.name,
                        "next_run": (
                            next_job.next_run.isoformat() if next_job.next_run else None
                        ),
                    }
                    if next_job
                    else None
                ),
            }
        finally:
            session.close()


COMMON_CRON_EXPRESSIONS = {
    "every_5_minutes": {"expression": "*/5 * * * *", "label": "Every 5 minutes"},
    "every_15_minutes": {"expression": "*/15 * * * *", "label": "Every 15 minutes"},
    "every_30_minutes": {"expression": "*/30 * * * *", "label": "Every 30 minutes"},
    "hourly": {"expression": "0 * * * *", "label": "Every hour"},
    "daily_midnight": {"expression": "0 0 * * *", "label": "Daily at midnight"},
    "daily_6am": {"expression": "0 6 * * *", "label": "Daily at 6:00 AM"},
    "daily_9am": {"expression": "0 9 * * *", "label": "Daily at 9:00 AM"},
    "daily_noon": {"expression": "0 12 * * *", "label": "Daily at noon"},
    "daily_6pm": {"expression": "0 18 * * *", "label": "Daily at 6:00 PM"},
    "weekly_monday_8am": {
        "expression": "0 8 * * 1",
        "label": "Weekly on Monday at 8:00 AM",
    },
    "weekly_friday_5pm": {
        "expression": "0 17 * * 5",
        "label": "Weekly on Friday at 5:00 PM",
    },
    "monthly_first": {
        "expression": "0 0 1 * *",
        "label": "Monthly on the 1st at midnight",
    },
}
