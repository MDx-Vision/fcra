"""
Bureau Response Tracking Service

Tracks disputes sent to credit bureaus and monitors response status.
FCRA requires CRAs to respond within 30 days (45 for complex disputes).
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from database import (
    BureauDisputeTracking,
    Case,
    Client,
    CRAResponse,
    DisputeItem,
    get_db,
)

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


class BureauResponseService:
    """Service for tracking bureau dispute responses"""

    def __init__(self):
        self.db = None

    def _get_db(self):
        if not self.db:
            self.db = get_db()
        return self.db

    def _close_db(self):
        if self.db:
            self.db.close()
            self.db = None

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

        except:
            return {
                "deleted": 0,
                "updated": 0,
                "verified": 0,
                "mixed": 0,
                "frivolous": 0,
            }
