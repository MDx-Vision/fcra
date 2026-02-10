"""
Bureau Response Tracking Service

Tracks disputes sent to credit bureaus and monitors response status.
FCRA requires CRAs to respond within 30 days (45 for complex disputes).

ISSUE-010: Enhanced with proper error handling, OCR integration,
and automated response parsing.
"""

import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from database import (
    BureauDisputeTracking,
    Case,
    Client,
    ClientUpload,
    CRAResponse,
    CRAResponseOCR,
    DisputeItem,
    get_db,
)

logger = logging.getLogger(__name__)

# Bureau constants
BUREAUS = ["Equifax", "Experian", "TransUnion"]

# Response deadline days
STANDARD_DEADLINE_DAYS = 30
COMPLEX_DEADLINE_DAYS = 45

# Status values
STATUS_SENT = "sent"
STATUS_DELIVERED = "delivered"
STATUS_AWAITING = "awaiting_response"
STATUS_RECEIVED = "response_received"
STATUS_OVERDUE = "overdue"
STATUS_CLOSED = "closed"

# Response types
RESPONSE_VERIFIED = "verified"
RESPONSE_DELETED = "deleted"
RESPONSE_UPDATED = "updated"
RESPONSE_MIXED = "mixed"
RESPONSE_FRIVOLOUS = "frivolous"
RESPONSE_NO_RESPONSE = "no_response"
RESPONSE_INVESTIGATING = "investigating"

# Error codes for structured error responses
ERROR_TRACKING_NOT_FOUND = "TRACKING_NOT_FOUND"
ERROR_CRA_RESPONSE_NOT_FOUND = "CRA_RESPONSE_NOT_FOUND"
ERROR_CLIENT_NOT_FOUND = "CLIENT_NOT_FOUND"
ERROR_FILE_NOT_FOUND = "FILE_NOT_FOUND"
ERROR_OCR_FAILED = "OCR_FAILED"
ERROR_PARSE_FAILED = "PARSE_FAILED"
ERROR_DATABASE = "DATABASE_ERROR"
ERROR_INVALID_INPUT = "INVALID_INPUT"

# Response letter keywords for parsing
DELETION_KEYWORDS = [
    "has been deleted",
    "have been deleted",
    "removed from your credit file",
    "removed from your credit report",
    "information has been removed",
    "account deleted",
    "tradeline deleted",
    "inquiry removed",
    "successfully removed",
    "no longer appears",
    "been removed from your file",
]

VERIFIED_KEYWORDS = [
    "has been verified",
    "have been verified",
    "verified as accurate",
    "investigation complete",
    "information is accurate",
    "previously reported correctly",
    "remains unchanged",
    "verified and will remain",
    "verified as reported",
    "confirmed as accurate",
]

UPDATE_KEYWORDS = [
    "has been updated",
    "have been updated",
    "information has been modified",
    "corrected as follows",
    "updated to reflect",
    "has been corrected",
    "modified on your credit file",
    "changed to show",
    "account updated",
]

FRIVOLOUS_KEYWORDS = [
    "frivolous",
    "substantially similar",
    "previously investigated",
    "no new information",
    "lacking sufficient",
    "does not contain sufficient",
    "unable to process",
    "provide additional documentation",
]

INVESTIGATING_KEYWORDS = [
    "currently investigating",
    "investigation in progress",
    "additional time",
    "extended investigation",
    "complex investigation",
    "45-day",
    "require more time",
]

# Bureau-specific identifiers
BUREAU_IDENTIFIERS = {
    "Equifax": ["equifax", "efx", "p.o. box 740241", "atlanta, ga"],
    "Experian": ["experian", "p.o. box 4500", "allen, tx", "p.o. box 9554"],
    "TransUnion": ["transunion", "p.o. box 2000", "chester, pa", "p.o. box 1000"],
}


class BureauResponseServiceError(Exception):
    """Custom exception for bureau response service errors."""

    def __init__(self, message: str, error_code: str, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": False,
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class BureauResponseService:
    """Service for tracking bureau dispute responses"""

    def __init__(self, session=None):
        self.db = session
        self._owns_session = session is None

    def _get_db(self):
        if not self.db:
            self.db = get_db()
        return self.db

    def _close_db(self):
        if self.db and self._owns_session:
            self.db.close()
            self.db = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_db()

    def _error_response(
        self, message: str, error_code: str, details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a standardized error response."""
        logger.error(f"BureauResponseService: {error_code} - {message}")
        return {
            "success": False,
            "error": message,
            "error_code": error_code,
            "details": details or {},
        }

    def _success_response(
        self, data: Any = None, message: str = None, **kwargs
    ) -> Dict[str, Any]:
        """Create a standardized success response."""
        response = {"success": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        response.update(kwargs)
        return response

    # =========================================================================
    # CREATE / TRACK DISPUTES
    # =========================================================================

    def track_dispute_sent(
        self,
        client_id: int,
        bureau: str,
        sent_date: date,
        dispute_round: int = 1,
        item_ids: List[int] = None,
        sent_method: str = "certified_mail",
        tracking_number: str = None,
        letter_id: int = None,
        certified_mail_id: int = None,
        case_id: int = None,
        is_complex: bool = False,
        sent_by_staff_id: int = None,
        notes: str = None,
    ) -> Dict[str, Any]:
        """
        Track a dispute sent to a bureau.
        Creates a tracking record and calculates expected response date.
        """
        db = self._get_db()

        try:
            # Calculate expected response date
            deadline_days = (
                COMPLEX_DEADLINE_DAYS if is_complex else STANDARD_DEADLINE_DAYS
            )
            expected_date = sent_date + timedelta(days=deadline_days)

            # Generate batch ID
            batch_id = f"{client_id}-{bureau[:3].upper()}-R{dispute_round}-{sent_date.strftime('%Y%m%d')}"

            # Create tracking record
            tracking = BureauDisputeTracking(
                client_id=client_id,
                case_id=case_id,
                bureau=bureau,
                dispute_round=dispute_round,
                batch_id=batch_id,
                letter_id=letter_id,
                certified_mail_id=certified_mail_id,
                item_count=len(item_ids) if item_ids else 0,
                item_ids=item_ids,
                sent_method=sent_method,
                sent_date=sent_date,
                sent_by_staff_id=sent_by_staff_id,
                tracking_number=tracking_number,
                expected_response_date=expected_date,
                response_deadline_days=deadline_days,
                is_complex_dispute=is_complex,
                status=STATUS_SENT,
                notes=notes,
            )

            db.add(tracking)
            db.commit()
            db.refresh(tracking)

            return {
                "success": True,
                "tracking": tracking.to_dict(),
                "message": f"Dispute to {bureau} tracked. Response expected by {expected_date}",
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    def confirm_delivery(
        self,
        tracking_id: int,
        delivery_date: date = None,
        recalculate_deadline: bool = True,
    ) -> Dict[str, Any]:
        """
        Confirm delivery of dispute letter.
        Optionally recalculate response deadline from delivery date.
        """
        db = self._get_db()

        try:
            tracking = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.id == tracking_id)
                .first()
            )

            if not tracking:
                return {"success": False, "error": "Tracking record not found"}

            tracking.delivery_confirmed = True
            tracking.delivery_date = delivery_date or date.today()
            tracking.status = STATUS_AWAITING

            # Recalculate deadline from delivery date (FCRA counts from receipt)
            if recalculate_deadline:
                tracking.expected_response_date = tracking.delivery_date + timedelta(
                    days=tracking.response_deadline_days
                )

            db.commit()

            return {
                "success": True,
                "tracking": tracking.to_dict(),
                "message": f"Delivery confirmed. Response expected by {tracking.expected_response_date}",
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    # =========================================================================
    # RECORD RESPONSES
    # =========================================================================

    def record_response(
        self,
        tracking_id: int,
        response_date: date,
        response_type: str,
        items_deleted: int = 0,
        items_updated: int = 0,
        items_verified: int = 0,
        items_investigating: int = 0,
        response_document_id: int = None,
        follow_up_required: bool = False,
        follow_up_type: str = None,
        notes: str = None,
    ) -> Dict[str, Any]:
        """Record a response received from a bureau."""
        db = self._get_db()

        try:
            tracking = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.id == tracking_id)
                .first()
            )

            if not tracking:
                return {"success": False, "error": "Tracking record not found"}

            tracking.response_received = True
            tracking.response_date = response_date
            tracking.response_type = response_type
            tracking.response_document_id = response_document_id
            tracking.items_deleted = items_deleted
            tracking.items_updated = items_updated
            tracking.items_verified = items_verified
            tracking.items_investigating = items_investigating
            tracking.status = STATUS_RECEIVED
            tracking.is_overdue = False
            tracking.days_overdue = 0

            if follow_up_required:
                tracking.follow_up_required = True
                tracking.follow_up_type = follow_up_type
                tracking.follow_up_date = response_date + timedelta(days=30)

            if notes:
                tracking.notes = (tracking.notes or "") + f"\n{response_date}: {notes}"

            db.commit()

            return {
                "success": True,
                "tracking": tracking.to_dict(),
                "message": f"Response recorded: {response_type}",
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    def link_cra_response(
        self, tracking_id: int, cra_response_id: int
    ) -> Dict[str, Any]:
        """Link a CRA response document to a tracking record."""
        db = self._get_db()

        try:
            tracking = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.id == tracking_id)
                .first()
            )

            if not tracking:
                return {"success": False, "error": "Tracking record not found"}

            cra_response = (
                db.query(CRAResponse).filter(CRAResponse.id == cra_response_id).first()
            )

            if not cra_response:
                return {"success": False, "error": "CRA response not found"}

            tracking.response_document_id = cra_response_id
            tracking.response_received = True
            tracking.response_date = cra_response.received_date or date.today()
            tracking.response_type = cra_response.response_type
            tracking.items_deleted = cra_response.items_deleted or 0
            tracking.items_updated = cra_response.items_updated or 0
            tracking.items_verified = cra_response.items_verified or 0
            tracking.status = STATUS_RECEIVED

            db.commit()

            return {"success": True, "tracking": tracking.to_dict()}

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    # =========================================================================
    # CHECK OVERDUE / UPDATE STATUS
    # =========================================================================

    def check_overdue_disputes(self) -> Dict[str, Any]:
        """
        Check all pending disputes for overdue status.
        Updates is_overdue and days_overdue fields.
        Returns list of newly overdue disputes.
        """
        db = self._get_db()
        today = date.today()
        newly_overdue = []

        try:
            # Get all pending disputes
            pending = (
                db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.response_received == False,
                    BureauDisputeTracking.status.in_(
                        [STATUS_SENT, STATUS_DELIVERED, STATUS_AWAITING]
                    ),
                )
                .all()
            )

            for tracking in pending:
                if (
                    tracking.expected_response_date
                    and tracking.expected_response_date < today
                ):
                    days_over = (today - tracking.expected_response_date).days

                    if not tracking.is_overdue:
                        newly_overdue.append(tracking.to_dict())

                    tracking.is_overdue = True
                    tracking.days_overdue = days_over
                    tracking.status = STATUS_OVERDUE
                    tracking.follow_up_required = True
                    tracking.follow_up_type = tracking.follow_up_type or "escalate"

            db.commit()

            return {
                "success": True,
                "checked": len(pending),
                "newly_overdue": len(newly_overdue),
                "overdue_disputes": newly_overdue,
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    def get_due_soon(self, days: int = 7) -> List[Dict]:
        """Get disputes with responses due within N days."""
        db = self._get_db()
        today = date.today()
        cutoff = today + timedelta(days=days)

        try:
            disputes = (
                db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.response_received == False,
                    BureauDisputeTracking.expected_response_date >= today,
                    BureauDisputeTracking.expected_response_date <= cutoff,
                )
                .order_by(BureauDisputeTracking.expected_response_date)
                .all()
            )

            result = []
            for d in disputes:
                data = d.to_dict()
                # Add client name
                client = db.query(Client).filter(Client.id == d.client_id).first()
                if client:
                    data["client_name"] = f"{client.first_name} {client.last_name}"
                result.append(data)

            return result

        except Exception as e:
            return []

    def get_overdue(self) -> List[Dict]:
        """Get all overdue disputes."""
        db = self._get_db()

        try:
            disputes = (
                db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.is_overdue == True,
                    BureauDisputeTracking.response_received == False,
                )
                .order_by(BureauDisputeTracking.days_overdue.desc())
                .all()
            )

            result = []
            for d in disputes:
                data = d.to_dict()
                client = db.query(Client).filter(Client.id == d.client_id).first()
                if client:
                    data["client_name"] = f"{client.first_name} {client.last_name}"
                result.append(data)

            return result

        except Exception as e:
            return []

    # =========================================================================
    # QUERY / RETRIEVAL
    # =========================================================================

    def get_tracking(self, tracking_id: int) -> Optional[Dict]:
        """Get a single tracking record by ID."""
        db = self._get_db()

        try:
            tracking = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.id == tracking_id)
                .first()
            )

            if not tracking:
                return None

            data = tracking.to_dict()
            client = db.query(Client).filter(Client.id == tracking.client_id).first()
            if client:
                data["client_name"] = f"{client.first_name} {client.last_name}"

            return data

        except Exception as e:
            return None

    def get_client_disputes(
        self,
        client_id: int,
        bureau: str = None,
        dispute_round: int = None,
        status: str = None,
    ) -> List[Dict]:
        """Get all dispute tracking records for a client."""
        db = self._get_db()

        try:
            query = db.query(BureauDisputeTracking).filter(
                BureauDisputeTracking.client_id == client_id
            )

            if bureau:
                query = query.filter(BureauDisputeTracking.bureau == bureau)
            if dispute_round:
                query = query.filter(
                    BureauDisputeTracking.dispute_round == dispute_round
                )
            if status:
                query = query.filter(BureauDisputeTracking.status == status)

            disputes = query.order_by(
                BureauDisputeTracking.dispute_round.desc(),
                BureauDisputeTracking.sent_date.desc(),
            ).all()

            return [d.to_dict() for d in disputes]

        except Exception as e:
            return []

    def get_all_pending(
        self, bureau: str = None, days_until_due: int = None
    ) -> List[Dict]:
        """Get all pending disputes awaiting response."""
        db = self._get_db()
        today = date.today()

        try:
            query = db.query(BureauDisputeTracking).filter(
                BureauDisputeTracking.response_received == False
            )

            if bureau:
                query = query.filter(BureauDisputeTracking.bureau == bureau)

            if days_until_due is not None:
                cutoff = today + timedelta(days=days_until_due)
                query = query.filter(
                    BureauDisputeTracking.expected_response_date <= cutoff
                )

            disputes = query.order_by(
                BureauDisputeTracking.expected_response_date
            ).all()

            result = []
            for d in disputes:
                data = d.to_dict()
                client = db.query(Client).filter(Client.id == d.client_id).first()
                if client:
                    data["client_name"] = f"{client.first_name} {client.last_name}"
                result.append(data)

            return result

        except Exception as e:
            return []

    # =========================================================================
    # DASHBOARD / STATISTICS
    # =========================================================================

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        db = self._get_db()
        today = date.today()

        try:
            # Total counts by status
            total_pending = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.response_received == False)
                .count()
            )

            total_overdue = (
                db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.is_overdue == True,
                    BureauDisputeTracking.response_received == False,
                )
                .count()
            )

            # Due this week
            week_end = today + timedelta(days=7)
            due_this_week = (
                db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.response_received == False,
                    BureauDisputeTracking.expected_response_date >= today,
                    BureauDisputeTracking.expected_response_date <= week_end,
                )
                .count()
            )

            # Responses received this month
            month_start = today.replace(day=1)
            responses_this_month = (
                db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.response_received == True,
                    BureauDisputeTracking.response_date >= month_start,
                )
                .count()
            )

            # By bureau
            bureau_stats = {}
            for bureau in BUREAUS:
                pending = (
                    db.query(BureauDisputeTracking)
                    .filter(
                        BureauDisputeTracking.bureau == bureau,
                        BureauDisputeTracking.response_received == False,
                    )
                    .count()
                )
                overdue = (
                    db.query(BureauDisputeTracking)
                    .filter(
                        BureauDisputeTracking.bureau == bureau,
                        BureauDisputeTracking.is_overdue == True,
                        BureauDisputeTracking.response_received == False,
                    )
                    .count()
                )
                bureau_stats[bureau] = {"pending": pending, "overdue": overdue}

            # Response type breakdown (last 30 days)
            thirty_days_ago = today - timedelta(days=30)
            response_types = {}
            for rtype in [
                RESPONSE_DELETED,
                RESPONSE_UPDATED,
                RESPONSE_VERIFIED,
                RESPONSE_MIXED,
                RESPONSE_FRIVOLOUS,
            ]:
                count = (
                    db.query(BureauDisputeTracking)
                    .filter(
                        BureauDisputeTracking.response_type == rtype,
                        BureauDisputeTracking.response_date >= thirty_days_ago,
                    )
                    .count()
                )
                response_types[rtype] = count

            # Calculate success rate (deleted + updated / total responses)
            total_responses = sum(response_types.values())
            success_count = response_types.get(
                RESPONSE_DELETED, 0
            ) + response_types.get(RESPONSE_UPDATED, 0)
            success_rate = (
                (success_count / total_responses * 100) if total_responses > 0 else 0
            )

            # Average response time
            avg_response_time = self._calculate_avg_response_time(db)

            return {
                "total_pending": total_pending,
                "total_overdue": total_overdue,
                "due_this_week": due_this_week,
                "responses_this_month": responses_this_month,
                "bureau_stats": bureau_stats,
                "response_types": response_types,
                "success_rate": round(success_rate, 1),
                "avg_response_days": avg_response_time,
                "follow_up_required": db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.follow_up_required == True,
                    BureauDisputeTracking.follow_up_completed == False,
                )
                .count(),
            }

        except Exception as e:
            return {
                "total_pending": 0,
                "total_overdue": 0,
                "due_this_week": 0,
                "responses_this_month": 0,
                "bureau_stats": {},
                "response_types": {},
                "success_rate": 0,
                "avg_response_days": 0,
                "follow_up_required": 0,
                "error": str(e),
            }

    def _calculate_avg_response_time(self, db) -> float:
        """Calculate average days between sent and response."""
        try:
            disputes = (
                db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.response_received == True,
                    BureauDisputeTracking.sent_date.isnot(None),
                    BureauDisputeTracking.response_date.isnot(None),
                )
                .limit(100)
                .all()
            )

            if not disputes:
                return 0

            total_days = 0
            count = 0
            for d in disputes:
                if d.sent_date and d.response_date:
                    days = (d.response_date - d.sent_date).days
                    if days >= 0:
                        total_days += days
                        count += 1

            return round(total_days / count, 1) if count > 0 else 0

        except:
            return 0

    def get_bureau_breakdown(self) -> Dict[str, Any]:
        """Get detailed breakdown by bureau."""
        db = self._get_db()

        try:
            result = {}
            for bureau in BUREAUS:
                total = (
                    db.query(BureauDisputeTracking)
                    .filter(BureauDisputeTracking.bureau == bureau)
                    .count()
                )

                pending = (
                    db.query(BureauDisputeTracking)
                    .filter(
                        BureauDisputeTracking.bureau == bureau,
                        BureauDisputeTracking.response_received == False,
                    )
                    .count()
                )

                responded = (
                    db.query(BureauDisputeTracking)
                    .filter(
                        BureauDisputeTracking.bureau == bureau,
                        BureauDisputeTracking.response_received == True,
                    )
                    .count()
                )

                deleted = (
                    db.query(BureauDisputeTracking)
                    .filter(
                        BureauDisputeTracking.bureau == bureau,
                        BureauDisputeTracking.response_type == RESPONSE_DELETED,
                    )
                    .count()
                )

                overdue = (
                    db.query(BureauDisputeTracking)
                    .filter(
                        BureauDisputeTracking.bureau == bureau,
                        BureauDisputeTracking.is_overdue == True,
                        BureauDisputeTracking.response_received == False,
                    )
                    .count()
                )

                result[bureau] = {
                    "total": total,
                    "pending": pending,
                    "responded": responded,
                    "deleted": deleted,
                    "overdue": overdue,
                    "success_rate": (
                        round(deleted / responded * 100, 1) if responded > 0 else 0
                    ),
                }

            return result

        except Exception as e:
            return {}

    # =========================================================================
    # NOTIFICATIONS / REMINDERS
    # =========================================================================

    def mark_reminder_sent(self, tracking_id: int) -> bool:
        """Mark that a reminder was sent for this dispute."""
        db = self._get_db()

        try:
            tracking = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.id == tracking_id)
                .first()
            )

            if tracking:
                tracking.reminder_sent = True
                tracking.reminder_sent_at = datetime.utcnow()
                db.commit()
                return True

            return False

        except:
            db.rollback()
            return False

    def mark_overdue_alert_sent(self, tracking_id: int) -> bool:
        """Mark that an overdue alert was sent."""
        db = self._get_db()

        try:
            tracking = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.id == tracking_id)
                .first()
            )

            if tracking:
                tracking.overdue_alert_sent = True
                tracking.overdue_alert_sent_at = datetime.utcnow()
                db.commit()
                return True

            return False

        except:
            db.rollback()
            return False

    def get_pending_reminders(self, days_before: int = 5) -> List[Dict]:
        """Get disputes that need reminder (N days before deadline)."""
        db = self._get_db()
        today = date.today()
        reminder_date = today + timedelta(days=days_before)

        try:
            disputes = (
                db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.response_received == False,
                    BureauDisputeTracking.reminder_sent == False,
                    BureauDisputeTracking.expected_response_date <= reminder_date,
                    BureauDisputeTracking.expected_response_date >= today,
                )
                .all()
            )

            result = []
            for d in disputes:
                data = d.to_dict()
                client = db.query(Client).filter(Client.id == d.client_id).first()
                if client:
                    data["client_name"] = f"{client.first_name} {client.last_name}"
                    data["client_email"] = client.email
                result.append(data)

            return result

        except:
            return []

    def get_pending_overdue_alerts(self) -> List[Dict]:
        """Get overdue disputes that haven't had alert sent."""
        db = self._get_db()

        try:
            disputes = (
                db.query(BureauDisputeTracking)
                .filter(
                    BureauDisputeTracking.is_overdue == True,
                    BureauDisputeTracking.response_received == False,
                    BureauDisputeTracking.overdue_alert_sent == False,
                )
                .all()
            )

            result = []
            for d in disputes:
                data = d.to_dict()
                client = db.query(Client).filter(Client.id == d.client_id).first()
                if client:
                    data["client_name"] = f"{client.first_name} {client.last_name}"
                    data["client_email"] = client.email
                result.append(data)

            return result

        except:
            return []

    # =========================================================================
    # FOLLOW-UP MANAGEMENT
    # =========================================================================

    def complete_follow_up(self, tracking_id: int, notes: str = None) -> Dict[str, Any]:
        """Mark follow-up as completed."""
        db = self._get_db()

        try:
            tracking = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.id == tracking_id)
                .first()
            )

            if not tracking:
                return {"success": False, "error": "Tracking record not found"}

            tracking.follow_up_completed = True
            if notes:
                tracking.follow_up_notes = (
                    tracking.follow_up_notes or ""
                ) + f"\nCompleted: {notes}"

            db.commit()

            return {"success": True, "tracking": tracking.to_dict()}

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    def close_dispute(self, tracking_id: int, notes: str = None) -> Dict[str, Any]:
        """Close a dispute tracking record."""
        db = self._get_db()

        try:
            tracking = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.id == tracking_id)
                .first()
            )

            if not tracking:
                return {"success": False, "error": "Tracking record not found"}

            tracking.status = STATUS_CLOSED
            if notes:
                tracking.notes = (tracking.notes or "") + f"\nClosed: {notes}"

            db.commit()

            return {"success": True, "tracking": tracking.to_dict()}

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    # =========================================================================
    # EXPORT
    # =========================================================================

    def export_data(
        self,
        client_id: int = None,
        status: str = None,
        bureau: str = None,
        start_date: date = None,
        end_date: date = None,
    ) -> List[Dict]:
        """Export tracking data for CSV/reporting."""
        db = self._get_db()

        try:
            query = db.query(BureauDisputeTracking)

            if client_id:
                query = query.filter(BureauDisputeTracking.client_id == client_id)
            if status:
                query = query.filter(BureauDisputeTracking.status == status)
            if bureau:
                query = query.filter(BureauDisputeTracking.bureau == bureau)
            if start_date:
                query = query.filter(BureauDisputeTracking.sent_date >= start_date)
            if end_date:
                query = query.filter(BureauDisputeTracking.sent_date <= end_date)

            disputes = query.order_by(BureauDisputeTracking.sent_date.desc()).all()

            result = []
            for d in disputes:
                data = d.to_dict()
                client = db.query(Client).filter(Client.id == d.client_id).first()
                if client:
                    data["client_name"] = f"{client.first_name} {client.last_name}"
                    data["client_email"] = client.email
                result.append(data)

            return result

        except:
            return []

    # =========================================================================
    # RESPONSE TYPE BREAKDOWN
    # =========================================================================

    @staticmethod
    def get_response_type_breakdown(db) -> Dict[str, int]:
        """Get count of responses by type."""
        try:
            from sqlalchemy import func

            results = (
                db.query(
                    BureauDisputeTracking.response_type,
                    func.count(BureauDisputeTracking.id),
                )
                .filter(
                    BureauDisputeTracking.response_received == True,
                    BureauDisputeTracking.response_type.isnot(None),
                )
                .group_by(BureauDisputeTracking.response_type)
                .all()
            )

            breakdown = {
                "deleted": 0,
                "updated": 0,
                "verified": 0,
                "mixed": 0,
                "frivolous": 0,
            }

            for response_type, count in results:
                if response_type in breakdown:
                    breakdown[response_type] = count

            return breakdown

        except Exception as e:
            logger.error(f"get_response_type_breakdown error: {e}")
            return {
                "deleted": 0,
                "updated": 0,
                "verified": 0,
                "mixed": 0,
                "frivolous": 0,
            }

    # =========================================================================
    # OCR INTEGRATION & RESPONSE PARSING (ISSUE-010)
    # =========================================================================

    def parse_response_letter(
        self,
        file_path: str,
        tracking_id: int = None,
    ) -> Dict[str, Any]:
        """
        Parse a bureau response letter using OCR and extract key information.

        Args:
            file_path: Path to the response letter (PDF or image)
            tracking_id: Optional tracking ID to link the response

        Returns:
            Dict with parsed data: bureau, response_type, items, dates, raw_text
        """
        try:
            # Import OCR service
            from services.ocr_service import (
                _extract_text_from_pdf,
                extract_cra_response_data,
            )

            # Check file exists
            if not os.path.exists(file_path):
                return self._error_response(
                    f"File not found: {file_path}",
                    ERROR_FILE_NOT_FOUND,
                    {"file_path": file_path},
                )

            # Extract text based on file type
            file_ext = file_path.lower().split(".")[-1]
            raw_text = None

            if file_ext == "pdf":
                raw_text = _extract_text_from_pdf(file_path)
            elif file_ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                # Use Claude OCR for images
                result = extract_cra_response_data(file_path, file_ext)
                if result.get("raw_text"):
                    raw_text = result.get("raw_text")
                elif result.get("success"):
                    # Return the parsed result directly
                    return self._success_response(
                        data=result, message="Response letter parsed successfully"
                    )

            if not raw_text:
                # Try Claude OCR as fallback
                result = extract_cra_response_data(file_path, file_ext)
                if result.get("success"):
                    return self._success_response(
                        data=result, message="Response letter parsed with OCR"
                    )
                return self._error_response(
                    "Failed to extract text from document",
                    ERROR_OCR_FAILED,
                    {"file_path": file_path},
                )

            # Parse the extracted text
            parsed = self._parse_response_text(raw_text)
            parsed["raw_text"] = raw_text
            parsed["file_path"] = file_path

            # If tracking_id provided, link the response
            if tracking_id:
                self._link_parsed_response(tracking_id, parsed)

            return self._success_response(
                data=parsed, message="Response letter parsed successfully"
            )

        except Exception as e:
            logger.error(f"parse_response_letter error: {e}")
            return self._error_response(
                f"Failed to parse response letter: {str(e)}",
                ERROR_PARSE_FAILED,
                {"file_path": file_path, "exception": str(e)},
            )

    def _parse_response_text(self, text: str) -> Dict[str, Any]:
        """
        Parse raw text from a bureau response letter.

        Extracts:
        - Bureau name
        - Response type (deleted, verified, updated, etc.)
        - Account numbers mentioned
        - Dates
        - Item counts
        """
        text_lower = text.lower()
        result = {
            "bureau": None,
            "response_type": None,
            "items_deleted": 0,
            "items_updated": 0,
            "items_verified": 0,
            "items_investigating": 0,
            "account_numbers": [],
            "dates_found": [],
            "is_frivolous": False,
            "requires_follow_up": False,
            "confidence_score": 0.0,
        }

        # Identify bureau
        result["bureau"] = self._identify_bureau(text_lower)

        # Count keyword matches for each response type
        deleted_score = sum(1 for kw in DELETION_KEYWORDS if kw in text_lower)
        verified_score = sum(1 for kw in VERIFIED_KEYWORDS if kw in text_lower)
        updated_score = sum(1 for kw in UPDATE_KEYWORDS if kw in text_lower)
        frivolous_score = sum(1 for kw in FRIVOLOUS_KEYWORDS if kw in text_lower)
        investigating_score = sum(
            1 for kw in INVESTIGATING_KEYWORDS if kw in text_lower
        )

        # Determine primary response type
        scores = {
            RESPONSE_DELETED: deleted_score,
            RESPONSE_VERIFIED: verified_score,
            RESPONSE_UPDATED: updated_score,
            RESPONSE_FRIVOLOUS: frivolous_score,
            RESPONSE_INVESTIGATING: investigating_score,
        }

        max_score = max(scores.values())
        if max_score > 0:
            # Get the response type with highest score
            result["response_type"] = max(scores, key=scores.get)

            # Check for mixed responses
            significant_scores = [s for s in scores.values() if s > 0]
            if len(significant_scores) > 1:
                # Multiple response types found
                if deleted_score > 0 and verified_score > 0:
                    result["response_type"] = RESPONSE_MIXED

            # Calculate confidence
            total_keywords = sum(scores.values())
            if total_keywords > 0:
                result["confidence_score"] = round(
                    max_score / max(total_keywords, 1), 2
                )

        # Extract item counts from text
        result.update(self._extract_item_counts(text))

        # Check for frivolous flag
        result["is_frivolous"] = frivolous_score > 0

        # Check if follow-up required
        if frivolous_score > 0 or investigating_score > 0 or verified_score > 0:
            result["requires_follow_up"] = True

        # Extract account numbers
        result["account_numbers"] = self._extract_account_numbers(text)

        # Extract dates
        result["dates_found"] = self._extract_dates(text)

        return result

    def _identify_bureau(self, text_lower: str) -> Optional[str]:
        """Identify which bureau sent the response."""
        for bureau, identifiers in BUREAU_IDENTIFIERS.items():
            if any(identifier in text_lower for identifier in identifiers):
                return bureau
        return None

    def _extract_item_counts(self, text: str) -> Dict[str, int]:
        """Extract item counts from response text."""
        counts = {
            "items_deleted": 0,
            "items_updated": 0,
            "items_verified": 0,
            "items_investigating": 0,
        }

        # Common patterns for counts
        text_lower = text.lower()

        # Look for patterns like "3 items deleted" or "deleted 2 accounts"
        patterns = [
            (
                r"(\d+)\s*(?:items?|accounts?|tradelines?)\s*(?:have been|were|has been)?\s*deleted",
                "items_deleted",
            ),
            (r"deleted\s*(\d+)\s*(?:items?|accounts?|tradelines?)", "items_deleted"),
            (
                r"(\d+)\s*(?:items?|accounts?|tradelines?)\s*(?:have been|were|has been)?\s*(?:removed|erased)",
                "items_deleted",
            ),
            (
                r"(\d+)\s*(?:items?|accounts?|tradelines?)\s*(?:have been|were|has been)?\s*updated",
                "items_updated",
            ),
            (r"updated\s*(\d+)\s*(?:items?|accounts?|tradelines?)", "items_updated"),
            (
                r"(\d+)\s*(?:items?|accounts?|tradelines?)\s*(?:have been|were|has been)?\s*verified",
                "items_verified",
            ),
            (r"verified\s*(\d+)\s*(?:items?|accounts?|tradelines?)", "items_verified"),
            (
                r"(\d+)\s*(?:items?|accounts?|tradelines?)\s*(?:under|require|being)\s*investigation",
                "items_investigating",
            ),
        ]

        for pattern, field in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                counts[field] = max(counts[field], max(int(m) for m in matches))

        # If no explicit counts, estimate from keyword frequency
        if sum(counts.values()) == 0:
            if any(kw in text_lower for kw in DELETION_KEYWORDS):
                counts["items_deleted"] = 1
            if any(kw in text_lower for kw in VERIFIED_KEYWORDS):
                counts["items_verified"] = 1
            if any(kw in text_lower for kw in UPDATE_KEYWORDS):
                counts["items_updated"] = 1

        return counts

    def _extract_account_numbers(self, text: str) -> List[str]:
        """Extract account numbers from response text."""
        account_numbers = []

        # Common account number patterns
        patterns = [
            r"account\s*#?\s*:?\s*([A-Z0-9]{4,20})",
            r"account\s+number\s*:?\s*([A-Z0-9]{4,20})",
            r"acct\s*#?\s*:?\s*([A-Z0-9]{4,20})",
            r"reference\s*#?\s*:?\s*([A-Z0-9]{4,20})",
            r"\b([0-9]{4}[X*]{4,}[0-9]{4})\b",  # Masked numbers like 1234XXXX5678
            r"\b([X*]{4,}[0-9]{4})\b",  # Masked like XXXX1234
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            account_numbers.extend(matches)

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for acct in account_numbers:
            if acct.upper() not in seen:
                seen.add(acct.upper())
                unique.append(acct.upper())

        return unique[:20]  # Limit to 20 accounts

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from response text."""
        dates = []

        # Common date patterns
        patterns = [
            r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b",  # MM/DD/YYYY
            r"\b(\d{1,2}-\d{1,2}-\d{2,4})\b",  # MM-DD-YYYY
            r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",  # Month DD, YYYY
            r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",  # DD Month YYYY
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)

        # Remove duplicates
        return list(dict.fromkeys(dates))[:10]  # Limit to 10 dates

    def _link_parsed_response(
        self, tracking_id: int, parsed_data: Dict[str, Any]
    ) -> bool:
        """Link parsed response data to a tracking record."""
        try:
            db = self._get_db()
            tracking = (
                db.query(BureauDisputeTracking)
                .filter(BureauDisputeTracking.id == tracking_id)
                .first()
            )

            if not tracking:
                return False

            # Update tracking with parsed data
            if parsed_data.get("response_type"):
                tracking.response_type = parsed_data["response_type"]

            tracking.items_deleted = parsed_data.get("items_deleted", 0)
            tracking.items_updated = parsed_data.get("items_updated", 0)
            tracking.items_verified = parsed_data.get("items_verified", 0)
            tracking.items_investigating = parsed_data.get("items_investigating", 0)
            tracking.response_received = True
            tracking.response_date = date.today()
            tracking.status = STATUS_RECEIVED

            if parsed_data.get("requires_follow_up"):
                tracking.follow_up_required = True

            db.commit()
            return True

        except Exception as e:
            logger.error(f"_link_parsed_response error: {e}")
            if self.db:
                self.db.rollback()
            return False

    def auto_parse_upload(
        self,
        upload_id: int,
        tracking_id: int = None,
    ) -> Dict[str, Any]:
        """
        Automatically parse a client upload as a bureau response.

        Args:
            upload_id: ClientUpload ID
            tracking_id: Optional tracking ID to link

        Returns:
            Parsed response data or error
        """
        db = self._get_db()

        try:
            upload = db.query(ClientUpload).filter(ClientUpload.id == upload_id).first()

            if not upload:
                return self._error_response(
                    "Upload not found", ERROR_FILE_NOT_FOUND, {"upload_id": upload_id}
                )

            if not upload.file_path:
                return self._error_response(
                    "Upload has no file path",
                    ERROR_FILE_NOT_FOUND,
                    {"upload_id": upload_id},
                )

            # Parse the file
            result = self.parse_response_letter(upload.file_path, tracking_id)

            if result.get("success"):
                # Update upload with parsed info
                parsed = result.get("data", {})
                upload.ocr_processed = True
                upload.ocr_confidence = parsed.get("confidence_score", 0)
                if parsed.get("raw_text"):
                    upload.ocr_text = parsed["raw_text"][:5000]  # Limit text size

                db.commit()

            return result

        except Exception as e:
            logger.error(f"auto_parse_upload error: {e}")
            db.rollback()
            return self._error_response(
                f"Failed to parse upload: {str(e)}",
                ERROR_PARSE_FAILED,
                {"upload_id": upload_id, "exception": str(e)},
            )

    def extract_status_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract response status from plain text.
        Useful for manual entry or email parsing.

        Args:
            text: Plain text from bureau response

        Returns:
            Dict with response_type, items, and confidence
        """
        if not text or not text.strip():
            return self._error_response("Empty text provided", ERROR_INVALID_INPUT)

        try:
            parsed = self._parse_response_text(text)
            return self._success_response(
                data=parsed,
                message=f"Detected response type: {parsed.get('response_type', 'unknown')}",
            )

        except Exception as e:
            logger.error(f"extract_status_from_text error: {e}")
            return self._error_response(
                f"Failed to extract status: {str(e)}", ERROR_PARSE_FAILED
            )

    def batch_parse_responses(
        self,
        file_paths: List[str],
    ) -> Dict[str, Any]:
        """
        Parse multiple response letters in batch.

        Args:
            file_paths: List of file paths to parse

        Returns:
            Summary with results for each file
        """
        results = []
        success_count = 0
        error_count = 0

        for path in file_paths:
            result = self.parse_response_letter(path)
            results.append(
                {
                    "file_path": path,
                    "success": result.get("success", False),
                    "data": result.get("data") if result.get("success") else None,
                    "error": result.get("error") if not result.get("success") else None,
                }
            )

            if result.get("success"):
                success_count += 1
            else:
                error_count += 1

        return self._success_response(
            data={
                "results": results,
                "total": len(file_paths),
                "success_count": success_count,
                "error_count": error_count,
            },
            message=f"Parsed {success_count}/{len(file_paths)} files successfully",
        )

    def get_parse_summary(
        self,
        client_id: int = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get summary of parsed responses.

        Args:
            client_id: Optional client filter
            days: Number of days to look back

        Returns:
            Summary statistics
        """
        db = self._get_db()
        cutoff = date.today() - timedelta(days=days)

        try:
            query = db.query(BureauDisputeTracking).filter(
                BureauDisputeTracking.response_received == True,
                BureauDisputeTracking.response_date >= cutoff,
            )

            if client_id:
                query = query.filter(BureauDisputeTracking.client_id == client_id)

            responses = query.all()

            summary = {
                "total_responses": len(responses),
                "by_type": {},
                "by_bureau": {},
                "total_items_deleted": 0,
                "total_items_updated": 0,
                "total_items_verified": 0,
                "follow_up_needed": 0,
            }

            for r in responses:
                # Count by type
                rtype = r.response_type or "unknown"
                summary["by_type"][rtype] = summary["by_type"].get(rtype, 0) + 1

                # Count by bureau
                bureau = r.bureau or "unknown"
                summary["by_bureau"][bureau] = summary["by_bureau"].get(bureau, 0) + 1

                # Sum items
                summary["total_items_deleted"] += r.items_deleted or 0
                summary["total_items_updated"] += r.items_updated or 0
                summary["total_items_verified"] += r.items_verified or 0

                # Count follow-ups
                if r.follow_up_required and not r.follow_up_completed:
                    summary["follow_up_needed"] += 1

            return self._success_response(data=summary)

        except Exception as e:
            logger.error(f"get_parse_summary error: {e}")
            return self._error_response(
                f"Failed to get summary: {str(e)}", ERROR_DATABASE
            )
