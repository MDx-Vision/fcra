"""
Staff Performance Service
Brightpath Ascend FCRA Platform

Track and analyze staff performance metrics including:
- Cases handled per staff member
- Response times
- Activity tracking
- Leaderboard rankings
- Performance trends

Created: 2026-01-03
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session

from database import Case, Client, ClientMessage, SessionLocal, Staff, StaffActivity

logger = logging.getLogger(__name__)


# Activity types with display names and point values
ACTIVITY_TYPES = {
    "case_assigned": {"name": "Case Assigned", "points": 5},
    "case_completed": {"name": "Case Completed", "points": 20},
    "document_reviewed": {"name": "Document Reviewed", "points": 3},
    "letter_sent": {"name": "Letter Sent", "points": 10},
    "response_processed": {"name": "Response Processed", "points": 8},
    "message_sent": {"name": "Message Sent", "points": 2},
    "call_completed": {"name": "Call Completed", "points": 5},
    "note_added": {"name": "Note Added", "points": 1},
    "status_changed": {"name": "Status Changed", "points": 2},
    "analysis_reviewed": {"name": "Analysis Reviewed", "points": 15},
    "dispute_filed": {"name": "Dispute Filed", "points": 12},
}


class StaffPerformanceService:
    """Service for tracking and analyzing staff performance"""

    def __init__(self, session: Session = None):
        self._session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self._session:
            return self._session
        return SessionLocal()

    def _close_session(self, session: Session):
        if self._owns_session and session:
            session.close()

    # -------------------------------------------------------------------------
    # Activity Logging
    # -------------------------------------------------------------------------

    def log_activity(
        self,
        staff_id: int,
        activity_type: str,
        description: str = None,
        client_id: int = None,
        metadata: Dict = None,
        request_received_at: datetime = None,
        quality_score: int = None,
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Log a staff activity

        Args:
            staff_id: The staff member's ID
            activity_type: One of ACTIVITY_TYPES keys
            description: Human-readable description
            client_id: Optional related client ID
            metadata: Optional additional data
            request_received_at: When the task was assigned (for response time)
            quality_score: Optional 1-10 quality rating

        Returns:
            Tuple of (success, message, activity_dict)
        """
        if activity_type not in ACTIVITY_TYPES:
            return False, f"Invalid activity type: {activity_type}", None

        session = self._get_session()
        try:
            now = datetime.utcnow()

            # Calculate response time if request_received_at is provided
            response_time_minutes = None
            if request_received_at:
                delta = now - request_received_at
                response_time_minutes = int(delta.total_seconds() / 60)

            activity = StaffActivity(
                staff_id=staff_id,
                client_id=client_id,
                activity_type=activity_type,
                description=description or ACTIVITY_TYPES[activity_type]["name"],
                metadata=metadata,
                request_received_at=request_received_at,
                response_completed_at=now if request_received_at else None,
                response_time_minutes=response_time_minutes,
                quality_score=quality_score,
            )
            session.add(activity)
            session.commit()

            logger.info(f"Logged activity {activity_type} for staff {staff_id}")
            return True, "Activity logged", activity.to_dict()

        except Exception as e:
            session.rollback()
            logger.error(f"Error logging activity: {e}")
            return False, f"Error logging activity: {str(e)}", None
        finally:
            self._close_session(session)

    def mark_escalated(self, activity_id: int) -> Tuple[bool, str]:
        """Mark an activity as escalated"""
        session = self._get_session()
        try:
            activity = (
                session.query(StaffActivity)
                .filter(StaffActivity.id == activity_id)
                .first()
            )
            if not activity:
                return False, "Activity not found"

            activity.was_escalated = True
            session.commit()
            return True, "Marked as escalated"
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            self._close_session(session)

    def mark_revision_required(self, activity_id: int) -> Tuple[bool, str]:
        """Mark an activity as requiring revision"""
        session = self._get_session()
        try:
            activity = (
                session.query(StaffActivity)
                .filter(StaffActivity.id == activity_id)
                .first()
            )
            if not activity:
                return False, "Activity not found"

            activity.required_revision = True
            session.commit()
            return True, "Marked as requiring revision"
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            self._close_session(session)

    # -------------------------------------------------------------------------
    # Performance Metrics
    # -------------------------------------------------------------------------

    def get_staff_metrics(
        self, staff_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for a staff member

        Args:
            staff_id: The staff member's ID
            start_date: Start of period (defaults to 30 days ago)
            end_date: End of period (defaults to now)

        Returns:
            Dictionary of performance metrics
        """
        session = self._get_session()
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            # Get staff info
            staff = session.query(Staff).filter(Staff.id == staff_id).first()
            if not staff:
                return {"error": "Staff not found"}

            # Get activities in period
            activities = (
                session.query(StaffActivity)
                .filter(
                    and_(
                        StaffActivity.staff_id == staff_id,
                        StaffActivity.created_at >= start_date,
                        StaffActivity.created_at <= end_date,
                    )
                )
                .all()
            )

            # Calculate metrics
            total_activities = len(activities)
            total_points = sum(
                ACTIVITY_TYPES.get(a.activity_type, {}).get("points", 0)
                for a in activities
            )

            # Activity breakdown
            activity_breakdown = {}
            for activity_type, info in ACTIVITY_TYPES.items():
                count = len([a for a in activities if a.activity_type == activity_type])
                activity_breakdown[activity_type] = {
                    "name": info["name"],
                    "count": count,
                    "points": count * info["points"],
                }

            # Response time metrics
            response_times = [
                a.response_time_minutes
                for a in activities
                if a.response_time_minutes is not None
            ]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            # Quality metrics
            quality_scores = [
                a.quality_score for a in activities if a.quality_score is not None
            ]
            avg_quality_score = (
                sum(quality_scores) / len(quality_scores) if quality_scores else 0
            )

            escalations = len([a for a in activities if a.was_escalated])
            revisions = len([a for a in activities if a.required_revision])

            # Cases handled (from activities)
            cases_completed = len(
                [a for a in activities if a.activity_type == "case_completed"]
            )
            letters_sent = len(
                [a for a in activities if a.activity_type == "letter_sent"]
            )

            # Calculate daily average
            days_in_period = max((end_date - start_date).days, 1)
            daily_avg_activities = total_activities / days_in_period
            daily_avg_points = total_points / days_in_period

            return {
                "staff_id": staff_id,
                "staff_name": staff.full_name,
                "staff_role": staff.role,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days_in_period,
                },
                "summary": {
                    "total_activities": total_activities,
                    "total_points": total_points,
                    "daily_avg_activities": round(daily_avg_activities, 1),
                    "daily_avg_points": round(daily_avg_points, 1),
                },
                "cases": {
                    "completed": cases_completed,
                    "letters_sent": letters_sent,
                },
                "response_time": {
                    "average_minutes": round(avg_response_time, 1),
                    "average_hours": (
                        round(avg_response_time / 60, 1) if avg_response_time else 0
                    ),
                    "total_tracked": len(response_times),
                },
                "quality": {
                    "average_score": round(avg_quality_score, 1),
                    "total_scored": len(quality_scores),
                    "escalations": escalations,
                    "revisions": revisions,
                    "escalation_rate": (
                        round(escalations / total_activities * 100, 1)
                        if total_activities
                        else 0
                    ),
                },
                "activity_breakdown": activity_breakdown,
            }
        finally:
            self._close_session(session)

    def get_team_metrics(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get aggregate metrics for all staff"""
        session = self._get_session()
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            # Get all active staff
            staff_members = session.query(Staff).filter(Staff.is_active == True).all()

            # Get all activities in period
            activities = (
                session.query(StaffActivity)
                .filter(
                    and_(
                        StaffActivity.created_at >= start_date,
                        StaffActivity.created_at <= end_date,
                    )
                )
                .all()
            )

            total_activities = len(activities)
            total_points = sum(
                ACTIVITY_TYPES.get(a.activity_type, {}).get("points", 0)
                for a in activities
            )

            # Response times
            response_times = [
                a.response_time_minutes
                for a in activities
                if a.response_time_minutes is not None
            ]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            # Activity by type
            activity_by_type = {}
            for activity_type, info in ACTIVITY_TYPES.items():
                count = len([a for a in activities if a.activity_type == activity_type])
                activity_by_type[activity_type] = {"name": info["name"], "count": count}

            # Per-staff breakdown
            staff_breakdown = []
            for staff in staff_members:
                staff_activities = [a for a in activities if a.staff_id == staff.id]
                staff_points = sum(
                    ACTIVITY_TYPES.get(a.activity_type, {}).get("points", 0)
                    for a in staff_activities
                )
                staff_breakdown.append(
                    {
                        "staff_id": staff.id,
                        "name": staff.full_name,
                        "role": staff.role,
                        "activities": len(staff_activities),
                        "points": staff_points,
                    }
                )

            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "summary": {
                    "total_staff": len(staff_members),
                    "total_activities": total_activities,
                    "total_points": total_points,
                    "avg_response_time_minutes": round(avg_response_time, 1),
                },
                "activity_by_type": activity_by_type,
                "staff_breakdown": sorted(
                    staff_breakdown, key=lambda x: x["points"], reverse=True
                ),
            }
        finally:
            self._close_session(session)

    # -------------------------------------------------------------------------
    # Leaderboard
    # -------------------------------------------------------------------------

    def get_leaderboard(
        self, period: str = "month", metric: str = "points", limit: int = 10
    ) -> List[Dict]:
        """
        Get staff leaderboard

        Args:
            period: 'day', 'week', 'month', 'quarter', 'year', 'all'
            metric: 'points', 'activities', 'response_time', 'cases'
            limit: Number of staff to return

        Returns:
            List of staff with rankings
        """
        session = self._get_session()
        try:
            # Determine date range
            now = datetime.utcnow()
            if period == "day":
                start_date = now - timedelta(days=1)
            elif period == "week":
                start_date = now - timedelta(weeks=1)
            elif period == "month":
                start_date = now - timedelta(days=30)
            elif period == "quarter":
                start_date = now - timedelta(days=90)
            elif period == "year":
                start_date = now - timedelta(days=365)
            else:  # 'all'
                start_date = datetime(2000, 1, 1)

            # Get all active staff with their activities
            staff_members = session.query(Staff).filter(Staff.is_active == True).all()

            leaderboard = []
            for staff in staff_members:
                activities = (
                    session.query(StaffActivity)
                    .filter(
                        and_(
                            StaffActivity.staff_id == staff.id,
                            StaffActivity.created_at >= start_date,
                        )
                    )
                    .all()
                )

                if not activities and metric != "response_time":
                    continue

                # Calculate metrics
                total_points = sum(
                    ACTIVITY_TYPES.get(a.activity_type, {}).get("points", 0)
                    for a in activities
                )
                total_activities = len(activities)
                cases_completed = len(
                    [a for a in activities if a.activity_type == "case_completed"]
                )

                response_times = [
                    a.response_time_minutes
                    for a in activities
                    if a.response_time_minutes is not None
                ]
                avg_response_time = (
                    sum(response_times) / len(response_times)
                    if response_times
                    else None
                )

                # Skip staff with no response time data for that metric
                if metric == "response_time" and avg_response_time is None:
                    continue

                leaderboard.append(
                    {
                        "staff_id": staff.id,
                        "name": staff.full_name,
                        "role": staff.role,
                        "initials": staff.initials,
                        "points": total_points,
                        "activities": total_activities,
                        "cases_completed": cases_completed,
                        "avg_response_time": (
                            round(avg_response_time, 1) if avg_response_time else None
                        ),
                    }
                )

            # Sort by metric
            if metric == "points":
                leaderboard.sort(key=lambda x: x["points"], reverse=True)
            elif metric == "activities":
                leaderboard.sort(key=lambda x: x["activities"], reverse=True)
            elif metric == "response_time":
                leaderboard.sort(key=lambda x: x["avg_response_time"] or float("inf"))
            elif metric == "cases":
                leaderboard.sort(key=lambda x: x["cases_completed"], reverse=True)

            # Add ranks
            for i, entry in enumerate(leaderboard[:limit]):
                entry["rank"] = i + 1

            return leaderboard[:limit]
        finally:
            self._close_session(session)

    # -------------------------------------------------------------------------
    # Activity History
    # -------------------------------------------------------------------------

    def get_staff_activities(
        self, staff_id: int, limit: int = 50, offset: int = 0, activity_type: str = None
    ) -> List[Dict]:
        """Get recent activities for a staff member"""
        session = self._get_session()
        try:
            query = session.query(StaffActivity).filter(
                StaffActivity.staff_id == staff_id
            )

            if activity_type:
                query = query.filter(StaffActivity.activity_type == activity_type)

            activities = (
                query.order_by(StaffActivity.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [a.to_dict() for a in activities]
        finally:
            self._close_session(session)

    def get_recent_team_activities(self, limit: int = 20) -> List[Dict]:
        """Get recent activities across all staff"""
        session = self._get_session()
        try:
            activities = (
                session.query(StaffActivity)
                .order_by(StaffActivity.created_at.desc())
                .limit(limit)
                .all()
            )

            result = []
            for activity in activities:
                staff = (
                    session.query(Staff).filter(Staff.id == activity.staff_id).first()
                )

                data = activity.to_dict()
                data["staff_name"] = staff.full_name if staff else "Unknown"
                data["staff_initials"] = staff.initials if staff else "?"
                result.append(data)

            return result
        finally:
            self._close_session(session)

    # -------------------------------------------------------------------------
    # Trends
    # -------------------------------------------------------------------------

    def get_performance_trend(self, staff_id: int = None, days: int = 30) -> List[Dict]:
        """
        Get daily performance trend

        Args:
            staff_id: Optional staff ID (None for team)
            days: Number of days to include

        Returns:
            List of daily stats
        """
        session = self._get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            trend = []
            current_date = start_date

            while current_date <= datetime.utcnow():
                day_start = current_date.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                day_end = day_start + timedelta(days=1)

                query = session.query(StaffActivity).filter(
                    and_(
                        StaffActivity.created_at >= day_start,
                        StaffActivity.created_at < day_end,
                    )
                )

                if staff_id:
                    query = query.filter(StaffActivity.staff_id == staff_id)

                activities = query.all()

                points = sum(
                    ACTIVITY_TYPES.get(a.activity_type, {}).get("points", 0)
                    for a in activities
                )

                trend.append(
                    {
                        "date": day_start.strftime("%Y-%m-%d"),
                        "activities": len(activities),
                        "points": points,
                    }
                )

                current_date += timedelta(days=1)

            return trend
        finally:
            self._close_session(session)

    # -------------------------------------------------------------------------
    # Dashboard Summary
    # -------------------------------------------------------------------------

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary data for staff performance dashboard"""
        session = self._get_session()
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = now - timedelta(days=7)
            month_start = now - timedelta(days=30)

            # Today's stats
            today_activities = (
                session.query(StaffActivity)
                .filter(StaffActivity.created_at >= today_start)
                .all()
            )
            today_points = sum(
                ACTIVITY_TYPES.get(a.activity_type, {}).get("points", 0)
                for a in today_activities
            )

            # This week's stats
            week_activities = (
                session.query(StaffActivity)
                .filter(StaffActivity.created_at >= week_start)
                .all()
            )
            week_points = sum(
                ACTIVITY_TYPES.get(a.activity_type, {}).get("points", 0)
                for a in week_activities
            )

            # This month's stats
            month_activities = (
                session.query(StaffActivity)
                .filter(StaffActivity.created_at >= month_start)
                .all()
            )
            month_points = sum(
                ACTIVITY_TYPES.get(a.activity_type, {}).get("points", 0)
                for a in month_activities
            )

            # Active staff count
            active_today = len(set(a.staff_id for a in today_activities))
            total_staff = session.query(Staff).filter(Staff.is_active == True).count()

            # Average response time (month)
            response_times = [
                a.response_time_minutes
                for a in month_activities
                if a.response_time_minutes is not None
            ]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            # Top performers this month
            leaderboard = self.get_leaderboard(period="month", limit=5)

            # Recent activities
            recent = self.get_recent_team_activities(limit=10)

            return {
                "today": {
                    "activities": len(today_activities),
                    "points": today_points,
                    "active_staff": active_today,
                },
                "week": {
                    "activities": len(week_activities),
                    "points": week_points,
                },
                "month": {
                    "activities": len(month_activities),
                    "points": month_points,
                    "avg_response_time_minutes": round(avg_response_time, 1),
                },
                "team": {
                    "total_staff": total_staff,
                },
                "top_performers": leaderboard,
                "recent_activities": recent,
            }
        finally:
            self._close_session(session)


# Convenience functions
def log_staff_activity(
    staff_id: int,
    activity_type: str,
    description: str = None,
    client_id: int = None,
    metadata: Dict = None,
) -> Tuple[bool, str, Optional[Dict]]:
    """Log a staff activity"""
    service = StaffPerformanceService()
    return service.log_activity(
        staff_id=staff_id,
        activity_type=activity_type,
        description=description,
        client_id=client_id,
        metadata=metadata,
    )


def get_staff_leaderboard(period: str = "month", limit: int = 10) -> List[Dict]:
    """Get staff leaderboard"""
    service = StaffPerformanceService()
    return service.get_leaderboard(period=period, limit=limit)


def get_performance_dashboard() -> Dict[str, Any]:
    """Get performance dashboard summary"""
    service = StaffPerformanceService()
    return service.get_dashboard_summary()
