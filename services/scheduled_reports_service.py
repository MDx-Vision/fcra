"""
Scheduled Reports Service

Provides functionality for scheduling and running automated reports:
- Create, update, delete scheduled reports
- Run reports on schedule (daily, weekly, monthly)
- Send reports via email with CSV/PDF attachments
- Track run history and status

Usage:
    from services.scheduled_reports_service import (
        ScheduledReportsService,
        get_scheduled_reports_service,
        REPORT_TYPES,
    )

    # Create a scheduled report
    service = get_scheduled_reports_service()
    report = service.create_report(
        name="Weekly Revenue Report",
        report_type="revenue",
        schedule_type="weekly",
        schedule_day=0,  # Monday
        recipients=["admin@example.com"],
    )

    # Run due reports (call from cron/scheduler)
    results = service.run_due_reports()
"""

import csv
import io
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytz

logger = logging.getLogger(__name__)


# =============================================================================
# Report Types Configuration
# =============================================================================

REPORT_TYPES = {
    "revenue": {
        "name": "Revenue Report",
        "description": "Daily/weekly/monthly revenue metrics and trends",
        "generator": "generate_revenue_report",
    },
    "clients": {
        "name": "Client Summary",
        "description": "Client statistics, new signups, status breakdown",
        "generator": "generate_clients_report",
    },
    "analytics": {
        "name": "Analytics Summary",
        "description": "Key performance metrics and analytics",
        "generator": "generate_analytics_report",
    },
    "ai_usage": {
        "name": "AI Usage Report",
        "description": "AI API usage, costs, and efficiency metrics",
        "generator": "generate_ai_usage_report",
    },
    "disputes": {
        "name": "Dispute Status Report",
        "description": "Active disputes, response rates, success metrics",
        "generator": "generate_disputes_report",
    },
    "settlements": {
        "name": "Settlements Report",
        "description": "Settlement statistics, amounts, and conversion rates",
        "generator": "generate_settlements_report",
    },
    "staff_performance": {
        "name": "Staff Performance Report",
        "description": "Staff activity, case loads, and productivity metrics",
        "generator": "generate_staff_performance_report",
    },
    "bureau_tracking": {
        "name": "Bureau Tracking Report",
        "description": "Bureau response times and dispute outcomes",
        "generator": "generate_bureau_tracking_report",
    },
}

SCHEDULE_TYPES = ["daily", "weekly", "monthly"]

DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

TIMEZONES = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Phoenix",
    "UTC",
]


# =============================================================================
# Scheduled Reports Service
# =============================================================================


class ScheduledReportsService:
    """
    Service for managing scheduled reports.

    Supports:
    - Creating and managing scheduled reports
    - Running reports on schedule
    - Generating report content (CSV/HTML)
    - Sending reports via email
    """

    def __init__(self, db_session=None):
        """
        Initialize the service.

        Args:
            db_session: SQLAlchemy session (optional)
        """
        self._db = db_session

    def _get_db(self):
        """Get database session."""
        if self._db:
            return self._db
        from database import SessionLocal

        return SessionLocal()

    def _should_close_db(self):
        """Check if we should close the database session."""
        return self._db is None

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    def create_report(
        self,
        name: str,
        report_type: str,
        schedule_type: str,
        recipients: List[str],
        description: Optional[str] = None,
        schedule_time: str = "08:00",
        schedule_day: Optional[int] = None,
        timezone: str = "America/New_York",
        report_params: Optional[Dict] = None,
        created_by_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new scheduled report.

        Args:
            name: Report name
            report_type: Type of report (see REPORT_TYPES)
            schedule_type: daily, weekly, or monthly
            recipients: List of email addresses
            description: Optional description
            schedule_time: Time to run (HH:MM format)
            schedule_day: Day of week (0-6) or month (1-31)
            timezone: Timezone for scheduling
            report_params: Optional parameters for report generation
            created_by_id: Staff ID of creator

        Returns:
            Created report dictionary
        """
        if report_type not in REPORT_TYPES:
            raise ValueError(f"Invalid report type: {report_type}")

        if schedule_type not in SCHEDULE_TYPES:
            raise ValueError(f"Invalid schedule type: {schedule_type}")

        if not recipients:
            raise ValueError("At least one recipient is required")

        db = self._get_db()
        try:
            from database import ScheduledReport

            report = ScheduledReport(
                name=name,
                report_type=report_type,
                description=description,
                schedule_type=schedule_type,
                schedule_time=schedule_time,
                schedule_day=schedule_day,
                timezone=timezone,
                recipients=recipients,
                report_params=report_params,
                is_active=True,
                created_by_id=created_by_id,
            )
            db.add(report)
            db.commit()
            db.refresh(report)

            logger.info(f"Created scheduled report: {name} ({report_type})")
            return report.to_dict()

        finally:
            if self._should_close_db():
                db.close()

    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Get a scheduled report by ID."""
        db = self._get_db()
        try:
            from database import ScheduledReport

            report = db.query(ScheduledReport).filter_by(id=report_id).first()
            return report.to_dict() if report else None
        finally:
            if self._should_close_db():
                db.close()

    def get_all_reports(
        self,
        is_active: Optional[bool] = None,
        report_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all scheduled reports with optional filters."""
        db = self._get_db()
        try:
            from database import ScheduledReport

            query = db.query(ScheduledReport)

            if is_active is not None:
                query = query.filter_by(is_active=is_active)

            if report_type:
                query = query.filter_by(report_type=report_type)

            reports = query.order_by(ScheduledReport.name).all()
            return [r.to_dict() for r in reports]

        finally:
            if self._should_close_db():
                db.close()

    def update_report(
        self,
        report_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schedule_type: Optional[str] = None,
        schedule_time: Optional[str] = None,
        schedule_day: Optional[int] = None,
        timezone: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        report_params: Optional[Dict] = None,
        is_active: Optional[bool] = None,
        updated_by_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a scheduled report."""
        db = self._get_db()
        try:
            from database import ScheduledReport

            report = db.query(ScheduledReport).filter_by(id=report_id).first()
            if not report:
                return None

            if name is not None:
                report.name = name
            if description is not None:
                report.description = description
            if schedule_type is not None:
                if schedule_type not in SCHEDULE_TYPES:
                    raise ValueError(f"Invalid schedule type: {schedule_type}")
                report.schedule_type = schedule_type
            if schedule_time is not None:
                report.schedule_time = schedule_time
            if schedule_day is not None:
                report.schedule_day = schedule_day
            if timezone is not None:
                report.timezone = timezone
            if recipients is not None:
                report.recipients = recipients
            if report_params is not None:
                report.report_params = report_params
            if is_active is not None:
                report.is_active = is_active
            if updated_by_id is not None:
                report.updated_by_id = updated_by_id

            report.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(report)

            logger.info(f"Updated scheduled report: {report.name}")
            return report.to_dict()

        finally:
            if self._should_close_db():
                db.close()

    def delete_report(self, report_id: int) -> bool:
        """Delete a scheduled report."""
        db = self._get_db()
        try:
            from database import ScheduledReport

            report = db.query(ScheduledReport).filter_by(id=report_id).first()
            if not report:
                return False

            db.delete(report)
            db.commit()

            logger.info(f"Deleted scheduled report: {report.name}")
            return True

        finally:
            if self._should_close_db():
                db.close()

    def toggle_report(self, report_id: int) -> Optional[bool]:
        """Toggle a report's active status."""
        db = self._get_db()
        try:
            from database import ScheduledReport

            report = db.query(ScheduledReport).filter_by(id=report_id).first()
            if not report:
                return None

            report.is_active = not report.is_active
            report.updated_at = datetime.utcnow()
            db.commit()

            logger.info(
                f"Toggled report {report.name} to {'active' if report.is_active else 'inactive'}"
            )
            return report.is_active

        finally:
            if self._should_close_db():
                db.close()

    # -------------------------------------------------------------------------
    # Report Scheduling
    # -------------------------------------------------------------------------

    def get_due_reports(self) -> List[Dict[str, Any]]:
        """Get all reports that are due to run."""
        db = self._get_db()
        try:
            from database import ScheduledReport

            reports = db.query(ScheduledReport).filter_by(is_active=True).all()
            due_reports = []

            for report in reports:
                if self._is_report_due(report):
                    due_reports.append(report.to_dict())

            return due_reports

        finally:
            if self._should_close_db():
                db.close()

    def _is_report_due(self, report) -> bool:
        """Check if a report is due to run."""
        try:
            tz = pytz.timezone(report.timezone or "America/New_York")
            now = datetime.now(tz)

            # Parse schedule time
            hour, minute = map(int, (report.schedule_time or "08:00").split(":"))

            # Check if it's time to run
            current_hour = now.hour
            current_minute = now.minute

            # Allow 5-minute window for scheduling
            time_match = current_hour == hour and abs(current_minute - minute) <= 5

            if not time_match:
                return False

            # Check day/date based on schedule type
            if report.schedule_type == "daily":
                # Daily: always due at the right time
                pass

            elif report.schedule_type == "weekly":
                # Weekly: check day of week
                if now.weekday() != (report.schedule_day or 0):
                    return False

            elif report.schedule_type == "monthly":
                # Monthly: check day of month
                if now.day != (report.schedule_day or 1):
                    return False

            # Check if already run today
            if report.last_run_at:
                last_run_tz = report.last_run_at.replace(tzinfo=pytz.UTC).astimezone(tz)
                if last_run_tz.date() == now.date():
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking if report is due: {e}")
            return False

    def run_due_reports(self) -> Dict[str, Any]:
        """Run all reports that are due."""
        due_reports = self.get_due_reports()
        results = {
            "ran": 0,
            "succeeded": 0,
            "failed": 0,
            "details": [],
        }

        for report_dict in due_reports:
            try:
                result = self.run_report(report_dict["id"])
                results["ran"] += 1
                if result.get("success"):
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1
                results["details"].append(
                    {
                        "report_id": report_dict["id"],
                        "name": report_dict["name"],
                        "success": result.get("success"),
                        "error": result.get("error"),
                    }
                )
            except Exception as e:
                results["ran"] += 1
                results["failed"] += 1
                results["details"].append(
                    {
                        "report_id": report_dict["id"],
                        "name": report_dict["name"],
                        "success": False,
                        "error": str(e),
                    }
                )

        logger.info(
            f"Ran {results['ran']} reports: {results['succeeded']} succeeded, {results['failed']} failed"
        )
        return results

    def run_report(self, report_id: int) -> Dict[str, Any]:
        """Run a specific report and send it via email."""
        db = self._get_db()
        try:
            from database import ScheduledReport

            report = db.query(ScheduledReport).filter_by(id=report_id).first()
            if not report:
                return {"success": False, "error": "Report not found"}

            logger.info(f"Running report: {report.name}")

            # Generate report content
            try:
                content = self._generate_report_content(report)
            except Exception as e:
                error_msg = f"Failed to generate report: {str(e)}"
                self._update_run_status(db, report, "failed", error_msg)
                return {"success": False, "error": error_msg}

            # Send email
            try:
                self._send_report_email(report, content)
            except Exception as e:
                error_msg = f"Failed to send report: {str(e)}"
                self._update_run_status(db, report, "failed", error_msg)
                return {"success": False, "error": error_msg}

            # Update status
            self._update_run_status(db, report, "success")

            return {
                "success": True,
                "report_id": report.id,
                "report_name": report.name,
                "recipients": report.recipients,
            }

        finally:
            if self._should_close_db():
                db.close()

    def _update_run_status(
        self,
        db,
        report,
        status: str,
        error: Optional[str] = None,
    ):
        """Update report run status."""
        report.last_run_at = datetime.utcnow()
        report.last_run_status = status
        report.last_run_error = error
        report.run_count = (report.run_count or 0) + 1
        db.commit()

    # -------------------------------------------------------------------------
    # Report Generation
    # -------------------------------------------------------------------------

    def _generate_report_content(self, report) -> Dict[str, Any]:
        """Generate report content based on type."""
        report_type = report.report_type
        params = report.report_params or {}

        generator_name = REPORT_TYPES.get(report_type, {}).get("generator")
        if not generator_name:
            raise ValueError(f"Unknown report type: {report_type}")

        generator = getattr(self, generator_name, None)
        if not generator:
            raise ValueError(f"Generator not implemented: {generator_name}")

        return generator(params)

    def generate_revenue_report(self, params: Dict) -> Dict[str, Any]:
        """Generate revenue report content."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import Client, PaymentPlanPayment

            # Get date range
            days = params.get("days", 30)
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get revenue stats
            total_revenue = (
                db.query(func.sum(PaymentPlanPayment.amount))
                .filter(
                    PaymentPlanPayment.payment_date >= start_date,
                    PaymentPlanPayment.status == "completed",
                )
                .scalar()
                or 0
            )

            payment_count = (
                db.query(func.count(PaymentPlanPayment.id))
                .filter(
                    PaymentPlanPayment.payment_date >= start_date,
                    PaymentPlanPayment.status == "completed",
                )
                .scalar()
                or 0
            )

            # Get top clients by revenue
            top_clients = (
                db.query(
                    Client.id,
                    Client.first_name,
                    Client.last_name,
                    func.sum(PaymentPlanPayment.amount).label("total"),
                )
                .join(PaymentPlanPayment, PaymentPlanPayment.client_id == Client.id)
                .filter(
                    PaymentPlanPayment.payment_date >= start_date,
                    PaymentPlanPayment.status == "completed",
                )
                .group_by(Client.id)
                .order_by(func.sum(PaymentPlanPayment.amount).desc())
                .limit(10)
                .all()
            )

            # Build CSV data
            csv_rows = [
                ["Revenue Report", f"Last {days} Days"],
                [],
                ["Metric", "Value"],
                ["Total Revenue", f"${total_revenue:,.2f}"],
                ["Payment Count", payment_count],
                [
                    "Average Payment",
                    f"${(total_revenue / payment_count if payment_count else 0):,.2f}",
                ],
                [],
                ["Top Clients by Revenue"],
                ["Name", "Revenue"],
            ]

            for client in top_clients:
                name = f"{client.first_name or ''} {client.last_name or ''}".strip()
                csv_rows.append([name, f"${client.total:,.2f}"])

            return {
                "subject": f"Revenue Report - Last {days} Days",
                "csv_data": csv_rows,
                "summary": {
                    "total_revenue": float(total_revenue),
                    "payment_count": payment_count,
                    "period_days": days,
                },
            }

        finally:
            if self._should_close_db():
                db.close()

    def generate_clients_report(self, params: Dict) -> Dict[str, Any]:
        """Generate client summary report."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import Client

            days = params.get("days", 30)
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get client stats
            total_clients = db.query(func.count(Client.id)).scalar() or 0
            new_clients = (
                db.query(func.count(Client.id))
                .filter(Client.created_at >= start_date)
                .scalar()
                or 0
            )

            # Status breakdown
            status_counts = (
                db.query(Client.dispute_status, func.count(Client.id))
                .group_by(Client.dispute_status)
                .all()
            )

            csv_rows = [
                ["Client Summary Report", f"Last {days} Days"],
                [],
                ["Metric", "Value"],
                ["Total Clients", total_clients],
                ["New Clients", new_clients],
                [],
                ["Status Breakdown"],
                ["Status", "Count"],
            ]

            for status, count in status_counts:
                csv_rows.append([status or "Unknown", count])

            return {
                "subject": f"Client Summary - Last {days} Days",
                "csv_data": csv_rows,
                "summary": {
                    "total_clients": total_clients,
                    "new_clients": new_clients,
                    "period_days": days,
                },
            }

        finally:
            if self._should_close_db():
                db.close()

    def generate_analytics_report(self, params: Dict) -> Dict[str, Any]:
        """Generate analytics summary report."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import Analysis, Client, PaymentPlanPayment

            days = params.get("days", 30)
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get key metrics
            total_analyses = (
                db.query(func.count(Analysis.id))
                .filter(Analysis.created_at >= start_date)
                .scalar()
                or 0
            )

            total_payments = (
                db.query(func.sum(PaymentPlanPayment.amount))
                .filter(
                    PaymentPlanPayment.payment_date >= start_date,
                    PaymentPlanPayment.status == "completed",
                )
                .scalar()
                or 0
            )

            active_clients = (
                db.query(func.count(Client.id))
                .filter(Client.dispute_status == "active")
                .scalar()
                or 0
            )

            csv_rows = [
                ["Analytics Summary", f"Last {days} Days"],
                [],
                ["Metric", "Value"],
                ["New Analyses", total_analyses],
                ["Total Revenue", f"${total_payments:,.2f}"],
                ["Active Clients", active_clients],
            ]

            return {
                "subject": f"Analytics Summary - Last {days} Days",
                "csv_data": csv_rows,
                "summary": {
                    "total_analyses": total_analyses,
                    "total_revenue": float(total_payments or 0),
                    "active_clients": active_clients,
                },
            }

        finally:
            if self._should_close_db():
                db.close()

    def generate_ai_usage_report(self, params: Dict) -> Dict[str, Any]:
        """Generate AI usage report."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import AIUsageLog

            days = params.get("days", 30)
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get AI usage stats
            total_requests = (
                db.query(func.count(AIUsageLog.id))
                .filter(AIUsageLog.created_at >= start_date)
                .scalar()
                or 0
            )

            total_tokens = (
                db.query(func.sum(AIUsageLog.total_tokens))
                .filter(AIUsageLog.created_at >= start_date)
                .scalar()
                or 0
            )

            # total_cost_cents is in cents, convert to dollars
            total_cost_cents = (
                db.query(func.sum(AIUsageLog.total_cost_cents))
                .filter(AIUsageLog.created_at >= start_date)
                .scalar()
                or 0
            )
            total_cost = total_cost_cents / 100.0

            # By operation type
            by_operation = (
                db.query(
                    AIUsageLog.operation,
                    func.count(AIUsageLog.id),
                    func.sum(AIUsageLog.total_cost_cents),
                )
                .filter(AIUsageLog.created_at >= start_date)
                .group_by(AIUsageLog.operation)
                .all()
            )

            csv_rows = [
                ["AI Usage Report", f"Last {days} Days"],
                [],
                ["Metric", "Value"],
                ["Total Requests", total_requests],
                ["Total Tokens", total_tokens or 0],
                ["Total Cost", f"${total_cost:,.2f}"],
                [],
                ["By Operation Type"],
                ["Operation", "Requests", "Cost"],
            ]

            for op, count, cost_cents in by_operation:
                cost = (cost_cents or 0) / 100.0
                csv_rows.append([op or "Unknown", count, f"${cost:,.2f}"])

            return {
                "subject": f"AI Usage Report - Last {days} Days",
                "csv_data": csv_rows,
                "summary": {
                    "total_requests": total_requests,
                    "total_tokens": total_tokens or 0,
                    "total_cost": float(total_cost),
                },
            }

        finally:
            if self._should_close_db():
                db.close()

    def generate_disputes_report(self, params: Dict) -> Dict[str, Any]:
        """Generate disputes status report."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import DisputeLetter

            days = params.get("days", 30)
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get dispute stats
            total_letters = (
                db.query(func.count(DisputeLetter.id))
                .filter(DisputeLetter.created_at >= start_date)
                .scalar()
                or 0
            )

            sent_letters = (
                db.query(func.count(DisputeLetter.id))
                .filter(
                    DisputeLetter.created_at >= start_date,
                    DisputeLetter.sent_at.isnot(None),
                )
                .scalar()
                or 0
            )

            csv_rows = [
                ["Disputes Report", f"Last {days} Days"],
                [],
                ["Metric", "Value"],
                ["Total Letters Generated", total_letters],
                ["Letters Sent", sent_letters],
            ]

            return {
                "subject": f"Disputes Report - Last {days} Days",
                "csv_data": csv_rows,
                "summary": {
                    "total_letters": total_letters,
                    "sent_letters": sent_letters,
                },
            }

        finally:
            if self._should_close_db():
                db.close()

    def generate_settlements_report(self, params: Dict) -> Dict[str, Any]:
        """Generate settlements report."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import Settlement

            days = params.get("days", 30)
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get settlement stats
            total_settlements = (
                db.query(func.count(Settlement.id))
                .filter(Settlement.created_at >= start_date)
                .scalar()
                or 0
            )

            total_amount = (
                db.query(func.sum(Settlement.final_amount))
                .filter(
                    Settlement.created_at >= start_date, Settlement.status == "accepted"
                )
                .scalar()
                or 0
            )

            csv_rows = [
                ["Settlements Report", f"Last {days} Days"],
                [],
                ["Metric", "Value"],
                ["Total Settlements", total_settlements],
                ["Total Amount", f"${total_amount or 0:,.2f}"],
            ]

            return {
                "subject": f"Settlements Report - Last {days} Days",
                "csv_data": csv_rows,
                "summary": {
                    "total_settlements": total_settlements,
                    "total_amount": float(total_amount or 0),
                },
            }

        finally:
            if self._should_close_db():
                db.close()

    def generate_staff_performance_report(self, params: Dict) -> Dict[str, Any]:
        """Generate staff performance report."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import Staff, StaffActivity

            days = params.get("days", 30)
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get staff activity counts
            staff_activities = (
                db.query(
                    Staff.id,
                    Staff.first_name,
                    Staff.last_name,
                    func.count(StaffActivity.id).label("activity_count"),
                )
                .outerjoin(
                    StaffActivity,
                    (StaffActivity.staff_id == Staff.id)
                    & (StaffActivity.created_at >= start_date),
                )
                .filter(Staff.is_active == True)
                .group_by(Staff.id)
                .all()
            )

            csv_rows = [
                ["Staff Performance Report", f"Last {days} Days"],
                [],
                ["Staff Member", "Activities"],
            ]

            for staff in staff_activities:
                name = f"{staff.first_name or ''} {staff.last_name or ''}".strip()
                csv_rows.append([name, staff.activity_count or 0])

            return {
                "subject": f"Staff Performance - Last {days} Days",
                "csv_data": csv_rows,
                "summary": {
                    "staff_count": len(staff_activities),
                },
            }

        finally:
            if self._should_close_db():
                db.close()

    def generate_bureau_tracking_report(self, params: Dict) -> Dict[str, Any]:
        """Generate bureau tracking report."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import BureauDispute

            days = params.get("days", 30)
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get bureau stats by bureau
            bureau_stats = (
                db.query(
                    BureauDispute.bureau,
                    func.count(BureauDispute.id).label("total"),
                    func.sum(
                        func.cast(BureauDispute.response_received == True, Integer)
                    ).label("responded"),
                )
                .filter(BureauDispute.created_at >= start_date)
                .group_by(BureauDispute.bureau)
                .all()
            )

            csv_rows = [
                ["Bureau Tracking Report", f"Last {days} Days"],
                [],
                ["Bureau", "Total Disputes", "Responses Received"],
            ]

            for stat in bureau_stats:
                csv_rows.append([stat.bureau, stat.total, stat.responded or 0])

            return {
                "subject": f"Bureau Tracking - Last {days} Days",
                "csv_data": csv_rows,
                "summary": {
                    "bureaus_tracked": len(bureau_stats),
                },
            }

        except Exception as e:
            # Table might not exist
            return {
                "subject": f"Bureau Tracking - Last {params.get('days', 30)} Days",
                "csv_data": [["Bureau Tracking Report"], ["No data available"]],
                "summary": {},
            }

        finally:
            if self._should_close_db():
                db.close()

    # -------------------------------------------------------------------------
    # Email Sending
    # -------------------------------------------------------------------------

    def _send_report_email(self, report, content: Dict[str, Any]):
        """Send report via email with CSV attachment."""
        from services.email_service import send_email

        # Build CSV content
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        for row in content.get("csv_data", []):
            writer.writerow(row)
        csv_content = csv_buffer.getvalue()

        # Build HTML email
        summary = content.get("summary", {})
        summary_html = "".join(
            f"<li><strong>{k.replace('_', ' ').title()}:</strong> {v}</li>"
            for k, v in summary.items()
        )

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #22c55e;">{content.get('subject', report.name)}</h2>
            <p>Your scheduled report is ready. Please find the details below and the full report attached as a CSV file.</p>

            <h3>Summary</h3>
            <ul>
                {summary_html}
            </ul>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated report from Brightpath Ascend FCRA Platform.
                <br>Report: {report.name} | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
            </p>
        </body>
        </html>
        """

        # Create attachment
        attachments = [
            {
                "filename": f"{report.report_type}_report_{datetime.utcnow().strftime('%Y%m%d')}.csv",
                "content": csv_content,
                "content_type": "text/csv",
            }
        ]

        # Send to each recipient
        for recipient in report.recipients:
            try:
                send_email(
                    to_email=recipient,
                    subject=content.get("subject", report.name),
                    html_content=html_content,
                    attachments=attachments,
                )
                logger.info(f"Sent report to {recipient}")
            except Exception as e:
                logger.error(f"Failed to send report to {recipient}: {e}")
                raise

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduled reports statistics."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import ScheduledReport

            total = db.query(func.count(ScheduledReport.id)).scalar() or 0
            active = (
                db.query(func.count(ScheduledReport.id))
                .filter(ScheduledReport.is_active == True)
                .scalar()
                or 0
            )

            by_type = (
                db.query(ScheduledReport.report_type, func.count(ScheduledReport.id))
                .group_by(ScheduledReport.report_type)
                .all()
            )

            by_schedule = (
                db.query(ScheduledReport.schedule_type, func.count(ScheduledReport.id))
                .group_by(ScheduledReport.schedule_type)
                .all()
            )

            # Recent runs
            recent_runs = (
                db.query(ScheduledReport)
                .filter(ScheduledReport.last_run_at.isnot(None))
                .order_by(ScheduledReport.last_run_at.desc())
                .limit(5)
                .all()
            )

            return {
                "total_reports": total,
                "active_reports": active,
                "inactive_reports": total - active,
                "by_type": {t: c for t, c in by_type},
                "by_schedule": {s: c for s, c in by_schedule},
                "recent_runs": [
                    {
                        "name": r.name,
                        "last_run_at": (
                            r.last_run_at.isoformat() if r.last_run_at else None
                        ),
                        "status": r.last_run_status,
                    }
                    for r in recent_runs
                ],
            }

        finally:
            if self._should_close_db():
                db.close()


# =============================================================================
# Module-Level Convenience Functions
# =============================================================================

_service: Optional[ScheduledReportsService] = None


def get_scheduled_reports_service() -> ScheduledReportsService:
    """Get or create the singleton service."""
    global _service
    if _service is None:
        _service = ScheduledReportsService()
    return _service


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "ScheduledReportsService",
    "get_scheduled_reports_service",
    "REPORT_TYPES",
    "SCHEDULE_TYPES",
    "DAYS_OF_WEEK",
    "TIMEZONES",
]
