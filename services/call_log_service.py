"""
Call Log Service

Manages phone call logging for client interactions.
Tracks inbound/outbound calls, notes, outcomes, and follow-ups.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session


class CallLogService:
    """Service for managing call logs"""

    # Valid call directions
    DIRECTIONS = ['inbound', 'outbound']

    # Valid call statuses
    STATUSES = [
        'completed',      # Call was completed successfully
        'missed',         # Inbound call that was missed
        'voicemail',      # Left voicemail or received voicemail
        'no_answer',      # Outbound call with no answer
        'busy',           # Line was busy
        'cancelled',      # Call was cancelled before connecting
    ]

    # Common call outcomes
    OUTCOMES = [
        'scheduled_appointment',   # Scheduled a follow-up appointment
        'left_message',            # Left a message
        'follow_up_needed',        # Requires follow-up
        'resolved',                # Issue was resolved
        'information_provided',    # Provided information to client
        'document_requested',      # Requested documents from client
        'payment_discussed',       # Discussed payment
        'case_update',             # Provided case update
        'complaint',               # Client complaint
        'other',                   # Other outcome
    ]

    def __init__(self, db: Session):
        self.db = db

    def create_call_log(
        self,
        staff_id: int,
        direction: str,
        call_started_at: datetime,
        client_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        call_ended_at: Optional[datetime] = None,
        duration_seconds: Optional[int] = None,
        status: str = 'completed',
        outcome: Optional[str] = None,
        subject: Optional[str] = None,
        notes: Optional[str] = None,
        follow_up_required: bool = False,
        follow_up_date: Optional[date] = None,
        follow_up_notes: Optional[str] = None,
        recording_url: Optional[str] = None,
        recording_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new call log entry.

        Args:
            staff_id: ID of the staff member who handled the call
            direction: 'inbound' or 'outbound'
            call_started_at: When the call started
            client_id: Optional client ID if linked to a client
            phone_number: External phone number
            call_ended_at: When the call ended
            duration_seconds: Call duration (calculated if not provided)
            status: Call status (completed, missed, voicemail, etc.)
            outcome: Call outcome
            subject: Brief subject/reason for call
            notes: Detailed call notes
            follow_up_required: Whether follow-up is needed
            follow_up_date: Date for follow-up
            follow_up_notes: Notes for follow-up
            recording_url: URL to call recording
            recording_duration: Duration of recording in seconds

        Returns:
            Dict with success status and call log data
        """
        from database import CallLog, Staff, Client

        # Validate direction
        if direction not in self.DIRECTIONS:
            return {"success": False, "error": f"Invalid direction. Must be one of: {self.DIRECTIONS}"}

        # Validate status
        if status not in self.STATUSES:
            return {"success": False, "error": f"Invalid status. Must be one of: {self.STATUSES}"}

        # Validate staff exists
        staff = self.db.query(Staff).filter_by(id=staff_id).first()
        if not staff:
            return {"success": False, "error": "Staff member not found"}

        # Validate client if provided
        if client_id:
            client = self.db.query(Client).filter_by(id=client_id).first()
            if not client:
                return {"success": False, "error": "Client not found"}

        # Calculate duration if not provided
        if duration_seconds is None and call_ended_at:
            duration_seconds = int((call_ended_at - call_started_at).total_seconds())

        try:
            call_log = CallLog(
                staff_id=staff_id,
                client_id=client_id,
                direction=direction,
                phone_number=phone_number,
                call_started_at=call_started_at,
                call_ended_at=call_ended_at,
                duration_seconds=duration_seconds or 0,
                status=status,
                outcome=outcome,
                subject=subject,
                notes=notes,
                follow_up_required=follow_up_required,
                follow_up_date=follow_up_date,
                follow_up_notes=follow_up_notes,
                recording_url=recording_url,
                recording_duration=recording_duration
            )

            self.db.add(call_log)
            self.db.commit()
            self.db.refresh(call_log)

            return {
                "success": True,
                "call_log_id": call_log.id,
                "call_log": self._serialize_call_log(call_log)
            }

        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def update_call_log(
        self,
        call_log_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update an existing call log.

        Args:
            call_log_id: ID of the call log to update
            **kwargs: Fields to update

        Returns:
            Dict with success status and updated call log data
        """
        from database import CallLog

        call_log = self.db.query(CallLog).filter_by(id=call_log_id).first()
        if not call_log:
            return {"success": False, "error": "Call log not found"}

        # Allowed fields to update
        allowed_fields = [
            'client_id', 'phone_number', 'call_ended_at', 'duration_seconds',
            'status', 'outcome', 'subject', 'notes', 'follow_up_required',
            'follow_up_date', 'follow_up_notes', 'recording_url', 'recording_duration'
        ]

        try:
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    setattr(call_log, field, value)

            # Recalculate duration if end time changed
            if 'call_ended_at' in kwargs and kwargs['call_ended_at']:
                call_log.duration_seconds = int(
                    (call_log.call_ended_at - call_log.call_started_at).total_seconds()
                )

            call_log.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(call_log)

            return {
                "success": True,
                "call_log": self._serialize_call_log(call_log)
            }

        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def delete_call_log(self, call_log_id: int) -> Dict[str, Any]:
        """Delete a call log entry."""
        from database import CallLog

        call_log = self.db.query(CallLog).filter_by(id=call_log_id).first()
        if not call_log:
            return {"success": False, "error": "Call log not found"}

        try:
            self.db.delete(call_log)
            self.db.commit()
            return {"success": True, "message": "Call log deleted"}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def get_call_log(self, call_log_id: int) -> Optional[Dict[str, Any]]:
        """Get a single call log by ID."""
        from database import CallLog

        call_log = self.db.query(CallLog).filter_by(id=call_log_id).first()
        if not call_log:
            return None
        return self._serialize_call_log(call_log)

    def get_call_logs(
        self,
        client_id: Optional[int] = None,
        staff_id: Optional[int] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        outcome: Optional[str] = None,
        follow_up_required: Optional[bool] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get call logs with filtering options.

        Args:
            client_id: Filter by client
            staff_id: Filter by staff member
            direction: Filter by direction (inbound/outbound)
            status: Filter by status
            outcome: Filter by outcome
            follow_up_required: Filter by follow-up status
            date_from: Filter by start date
            date_to: Filter by end date
            search: Search in subject and notes
            limit: Max results to return
            offset: Offset for pagination

        Returns:
            Dict with call logs and pagination info
        """
        from database import CallLog

        query = self.db.query(CallLog)

        # Apply filters
        if client_id:
            query = query.filter(CallLog.client_id == client_id)
        if staff_id:
            query = query.filter(CallLog.staff_id == staff_id)
        if direction:
            query = query.filter(CallLog.direction == direction)
        if status:
            query = query.filter(CallLog.status == status)
        if outcome:
            query = query.filter(CallLog.outcome == outcome)
        if follow_up_required is not None:
            query = query.filter(CallLog.follow_up_required == follow_up_required)
        if date_from:
            query = query.filter(func.date(CallLog.call_started_at) >= date_from)
        if date_to:
            query = query.filter(func.date(CallLog.call_started_at) <= date_to)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    CallLog.subject.ilike(search_term),
                    CallLog.notes.ilike(search_term),
                    CallLog.phone_number.ilike(search_term)
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        call_logs = query.order_by(desc(CallLog.call_started_at))\
            .offset(offset)\
            .limit(limit)\
            .all()

        return {
            "call_logs": [self._serialize_call_log(cl) for cl in call_logs],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": total > offset + limit
        }

    def get_client_call_history(self, client_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get call history for a specific client."""
        from database import CallLog

        call_logs = self.db.query(CallLog)\
            .filter(CallLog.client_id == client_id)\
            .order_by(desc(CallLog.call_started_at))\
            .limit(limit)\
            .all()

        return [self._serialize_call_log(cl) for cl in call_logs]

    def get_staff_call_activity(
        self,
        staff_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get call activity statistics for a staff member."""
        from database import CallLog

        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()

        query = self.db.query(CallLog).filter(
            CallLog.staff_id == staff_id,
            func.date(CallLog.call_started_at) >= date_from,
            func.date(CallLog.call_started_at) <= date_to
        )

        call_logs = query.all()

        # Calculate statistics
        total_calls = len(call_logs)
        inbound = sum(1 for cl in call_logs if cl.direction == 'inbound')
        outbound = sum(1 for cl in call_logs if cl.direction == 'outbound')
        completed = sum(1 for cl in call_logs if cl.status == 'completed')
        total_duration = sum(cl.duration_seconds or 0 for cl in call_logs)
        avg_duration = total_duration / total_calls if total_calls > 0 else 0

        # Calls by outcome
        outcome_counts = {}
        for cl in call_logs:
            if cl.outcome:
                outcome_counts[cl.outcome] = outcome_counts.get(cl.outcome, 0) + 1

        return {
            "staff_id": staff_id,
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "total_calls": total_calls,
            "inbound": inbound,
            "outbound": outbound,
            "completed": completed,
            "total_duration_seconds": total_duration,
            "total_duration_formatted": self._format_duration(total_duration),
            "avg_duration_seconds": round(avg_duration),
            "avg_duration_formatted": self._format_duration(int(avg_duration)),
            "outcomes": outcome_counts
        }

    def get_pending_follow_ups(
        self,
        staff_id: Optional[int] = None,
        include_overdue: bool = True
    ) -> List[Dict[str, Any]]:
        """Get call logs that require follow-up."""
        from database import CallLog

        query = self.db.query(CallLog).filter(
            CallLog.follow_up_required == True
        )

        if staff_id:
            query = query.filter(CallLog.staff_id == staff_id)

        if not include_overdue:
            query = query.filter(
                or_(
                    CallLog.follow_up_date.is_(None),
                    CallLog.follow_up_date >= date.today()
                )
            )

        call_logs = query.order_by(CallLog.follow_up_date.asc().nullsfirst()).all()

        result = []
        for cl in call_logs:
            data = self._serialize_call_log(cl)
            if cl.follow_up_date:
                data['is_overdue'] = cl.follow_up_date < date.today()
                data['days_until_due'] = (cl.follow_up_date - date.today()).days
            else:
                data['is_overdue'] = False
                data['days_until_due'] = None
            result.append(data)

        return result

    def mark_follow_up_complete(self, call_log_id: int) -> Dict[str, Any]:
        """Mark a follow-up as complete."""
        from database import CallLog

        call_log = self.db.query(CallLog).filter_by(id=call_log_id).first()
        if not call_log:
            return {"success": False, "error": "Call log not found"}

        call_log.follow_up_required = False
        call_log.updated_at = datetime.utcnow()
        self.db.commit()

        return {"success": True, "message": "Follow-up marked as complete"}

    def get_call_statistics(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get overall call statistics."""
        from database import CallLog

        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()

        query = self.db.query(CallLog).filter(
            func.date(CallLog.call_started_at) >= date_from,
            func.date(CallLog.call_started_at) <= date_to
        )

        call_logs = query.all()

        # Basic stats
        total_calls = len(call_logs)
        inbound = sum(1 for cl in call_logs if cl.direction == 'inbound')
        outbound = sum(1 for cl in call_logs if cl.direction == 'outbound')

        # Status breakdown
        status_counts = {}
        for status in self.STATUSES:
            status_counts[status] = sum(1 for cl in call_logs if cl.status == status)

        # Duration stats
        completed_calls = [cl for cl in call_logs if cl.status == 'completed' and cl.duration_seconds]
        total_duration = sum(cl.duration_seconds for cl in completed_calls)
        avg_duration = total_duration / len(completed_calls) if completed_calls else 0

        # Calls by day (for charts)
        calls_by_day = {}
        for cl in call_logs:
            day = cl.call_started_at.date().isoformat()
            calls_by_day[day] = calls_by_day.get(day, 0) + 1

        return {
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "total_calls": total_calls,
            "inbound": inbound,
            "outbound": outbound,
            "by_status": status_counts,
            "total_duration_seconds": total_duration,
            "total_duration_formatted": self._format_duration(total_duration),
            "avg_duration_seconds": round(avg_duration),
            "avg_duration_formatted": self._format_duration(int(avg_duration)),
            "calls_by_day": calls_by_day,
            "pending_follow_ups": sum(1 for cl in call_logs if cl.follow_up_required)
        }

    def _serialize_call_log(self, call_log) -> Dict[str, Any]:
        """Serialize a call log to a dictionary."""
        return {
            "id": call_log.id,
            "client_id": call_log.client_id,
            "client_name": f"{call_log.client.first_name} {call_log.client.last_name}" if call_log.client else None,
            "staff_id": call_log.staff_id,
            "staff_name": call_log.staff.name if call_log.staff else None,
            "direction": call_log.direction,
            "phone_number": call_log.phone_number,
            "call_started_at": call_log.call_started_at.isoformat() if call_log.call_started_at else None,
            "call_ended_at": call_log.call_ended_at.isoformat() if call_log.call_ended_at else None,
            "duration_seconds": call_log.duration_seconds,
            "duration_formatted": self._format_duration(call_log.duration_seconds) if call_log.duration_seconds else "0:00",
            "status": call_log.status,
            "outcome": call_log.outcome,
            "subject": call_log.subject,
            "notes": call_log.notes,
            "follow_up_required": call_log.follow_up_required,
            "follow_up_date": call_log.follow_up_date.isoformat() if call_log.follow_up_date else None,
            "follow_up_notes": call_log.follow_up_notes,
            "recording_url": call_log.recording_url,
            "recording_duration": call_log.recording_duration,
            "created_at": call_log.created_at.isoformat() if call_log.created_at else None,
            "updated_at": call_log.updated_at.isoformat() if call_log.updated_at else None,
        }

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable string."""
        if seconds < 60:
            return f"0:{seconds:02d}"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"


def get_call_log_service(db: Session) -> CallLogService:
    """Factory function to get a CallLogService instance."""
    return CallLogService(db)
