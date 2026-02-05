"""
Client Success Service

Tracks and calculates client success metrics including:
- Items deleted vs initial negative items
- Credit score improvements
- Per-client success summaries
- Aggregate reports for dashboard
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session

from database import (
    Analysis,
    Case,
    Client,
    ClientSuccessMetric,
    CRAResponse,
    CreditScoreSnapshot,
    DisputeItem,
    Violation,
)


class ClientSuccessService:
    """Service for tracking and calculating client success metrics"""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # METRIC CALCULATION
    # =========================================================================

    def calculate_client_metrics(self, client_id: int) -> Dict[str, Any]:
        """
        Calculate current success metrics for a client based on their data.
        Returns calculated metrics without saving.
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {"error": "Client not found"}

        # Get initial data (first analysis/credit snapshot)
        initial_data = self._get_initial_data(client_id)

        # Get current data
        current_data = self._get_current_data(client_id)

        # Calculate item metrics
        item_metrics = self._calculate_item_metrics(client_id)

        # Calculate score changes
        score_changes = self._calculate_score_changes(initial_data, current_data)

        # Calculate deletion rate
        deletion_rate = 0
        if initial_data.get("total_negatives", 0) > 0:
            deletion_rate = (
                item_metrics["total_deleted"] / initial_data["total_negatives"]
            )

        # Calculate days in program
        days_in_program = 0
        if client.created_at:
            days_in_program = (datetime.utcnow() - client.created_at).days

        # Get estimated value from violations
        estimated_value = self._calculate_estimated_value(client_id)

        return {
            "client_id": client_id,
            "client_name": client.name,
            # Initial state
            "initial_negative_items": initial_data.get("total_negatives", 0),
            "initial_equifax_score": initial_data.get("equifax_score"),
            "initial_experian_score": initial_data.get("experian_score"),
            "initial_transunion_score": initial_data.get("transunion_score"),
            "initial_avg_score": initial_data.get("avg_score"),
            # Current state
            "current_negative_items": current_data.get("total_negatives", 0),
            "current_equifax_score": current_data.get("equifax_score"),
            "current_experian_score": current_data.get("experian_score"),
            "current_transunion_score": current_data.get("transunion_score"),
            "current_avg_score": current_data.get("avg_score"),
            # Items breakdown
            "items_deleted": item_metrics["total_deleted"],
            "items_verified": item_metrics["total_verified"],
            "items_updated": item_metrics["total_updated"],
            "items_in_progress": item_metrics["total_in_progress"],
            # Items by bureau
            "equifax_items_deleted": item_metrics["equifax_deleted"],
            "experian_items_deleted": item_metrics["experian_deleted"],
            "transunion_items_deleted": item_metrics["transunion_deleted"],
            # Score changes
            "equifax_score_change": score_changes["equifax"],
            "experian_score_change": score_changes["experian"],
            "transunion_score_change": score_changes["transunion"],
            "avg_score_change": score_changes["avg"],
            # Success metrics
            "deletion_rate": round(deletion_rate * 100, 1),  # As percentage
            "dispute_rounds_completed": client.current_dispute_round or 0,
            "days_in_program": days_in_program,
            "estimated_value_recovered": estimated_value,
            # Status
            "is_active": client.status == "active",
            "case_complete": client.status == "complete",
            "dispute_status": client.dispute_status,
        }

    def _get_initial_data(self, client_id: int) -> Dict[str, Any]:
        """Get initial credit data from first snapshot or analysis"""
        # Try to get first credit score snapshot
        first_snapshot = (
            self.db.query(CreditScoreSnapshot)
            .filter(CreditScoreSnapshot.client_id == client_id)
            .order_by(CreditScoreSnapshot.created_at.asc())
            .first()
        )

        if first_snapshot:
            avg_score = None
            scores = [
                s
                for s in [
                    first_snapshot.equifax_score,
                    first_snapshot.experian_score,
                    first_snapshot.transunion_score,
                ]
                if s
            ]
            if scores:
                avg_score = sum(scores) // len(scores)

            return {
                "equifax_score": first_snapshot.equifax_score,
                "experian_score": first_snapshot.experian_score,
                "transunion_score": first_snapshot.transunion_score,
                "avg_score": first_snapshot.average_score or avg_score,
                "total_negatives": first_snapshot.total_negatives or 0,
                "equifax_negatives": first_snapshot.equifax_negatives or 0,
                "experian_negatives": first_snapshot.experian_negatives or 0,
                "transunion_negatives": first_snapshot.transunion_negatives or 0,
            }

        # Fallback: count initial dispute items
        initial_items = (
            self.db.query(DisputeItem)
            .filter(DisputeItem.client_id == client_id, DisputeItem.dispute_round == 1)
            .count()
        )

        return {
            "equifax_score": None,
            "experian_score": None,
            "transunion_score": None,
            "avg_score": None,
            "total_negatives": initial_items,
        }

    def _get_current_data(self, client_id: int) -> Dict[str, Any]:
        """Get current credit data from latest snapshot"""
        # Get latest credit score snapshot
        latest_snapshot = (
            self.db.query(CreditScoreSnapshot)
            .filter(CreditScoreSnapshot.client_id == client_id)
            .order_by(CreditScoreSnapshot.created_at.desc())
            .first()
        )

        if latest_snapshot:
            avg_score = None
            scores = [
                s
                for s in [
                    latest_snapshot.equifax_score,
                    latest_snapshot.experian_score,
                    latest_snapshot.transunion_score,
                ]
                if s
            ]
            if scores:
                avg_score = sum(scores) // len(scores)

            return {
                "equifax_score": latest_snapshot.equifax_score,
                "experian_score": latest_snapshot.experian_score,
                "transunion_score": latest_snapshot.transunion_score,
                "avg_score": latest_snapshot.average_score or avg_score,
                "total_negatives": latest_snapshot.total_negatives or 0,
            }

        # Fallback: count remaining negative items
        remaining_items = (
            self.db.query(DisputeItem)
            .filter(
                DisputeItem.client_id == client_id,
                DisputeItem.status.notin_(["deleted", "positive"]),
            )
            .count()
        )

        return {
            "equifax_score": None,
            "experian_score": None,
            "transunion_score": None,
            "avg_score": None,
            "total_negatives": remaining_items,
        }

    def _calculate_item_metrics(self, client_id: int) -> Dict[str, int]:
        """Calculate item deletion/verification metrics from DisputeItems and CRAResponses"""
        # From DisputeItem statuses
        dispute_items = (
            self.db.query(DisputeItem).filter(DisputeItem.client_id == client_id).all()
        )

        total_deleted = 0
        total_verified = 0
        total_updated = 0
        total_in_progress = 0
        equifax_deleted = 0
        experian_deleted = 0
        transunion_deleted = 0

        for item in dispute_items:
            if item.status == "deleted":
                total_deleted += 1
                if item.bureau and "equifax" in item.bureau.lower():
                    equifax_deleted += 1
                elif item.bureau and "experian" in item.bureau.lower():
                    experian_deleted += 1
                elif item.bureau and "transunion" in item.bureau.lower():
                    transunion_deleted += 1
            elif item.status == "verified" or item.status == "no_change":
                total_verified += 1
            elif item.status == "updated":
                total_updated += 1
            elif item.status in ["sent", "in_progress", "to_do"]:
                total_in_progress += 1

        # Also count from CRAResponses
        cra_responses = (
            self.db.query(CRAResponse).filter(CRAResponse.client_id == client_id).all()
        )

        for response in cra_responses:
            if response.items_deleted:
                total_deleted += response.items_deleted
            if response.items_verified:
                total_verified += response.items_verified
            if response.items_updated:
                total_updated += response.items_updated

        return {
            "total_deleted": total_deleted,
            "total_verified": total_verified,
            "total_updated": total_updated,
            "total_in_progress": total_in_progress,
            "equifax_deleted": equifax_deleted,
            "experian_deleted": experian_deleted,
            "transunion_deleted": transunion_deleted,
        }

    def _calculate_score_changes(self, initial: Dict, current: Dict) -> Dict[str, int]:
        """Calculate score changes between initial and current state"""
        changes = {
            "equifax": 0,
            "experian": 0,
            "transunion": 0,
            "avg": 0,
        }

        if initial.get("equifax_score") and current.get("equifax_score"):
            changes["equifax"] = current["equifax_score"] - initial["equifax_score"]
        if initial.get("experian_score") and current.get("experian_score"):
            changes["experian"] = current["experian_score"] - initial["experian_score"]
        if initial.get("transunion_score") and current.get("transunion_score"):
            changes["transunion"] = (
                current["transunion_score"] - initial["transunion_score"]
            )
        if initial.get("avg_score") and current.get("avg_score"):
            changes["avg"] = current["avg_score"] - initial["avg_score"]

        return changes

    def _calculate_estimated_value(self, client_id: int) -> float:
        """Calculate estimated value recovered based on violations"""
        violations = (
            self.db.query(Violation).filter(Violation.client_id == client_id).all()
        )

        total_value = 0
        for v in violations:
            # Use average of min and max statutory damages
            min_dam = v.statutory_damages_min or 0
            max_dam = v.statutory_damages_max or 0
            if min_dam or max_dam:
                total_value += (min_dam + max_dam) / 2

        return round(total_value, 2)

    # =========================================================================
    # METRIC SNAPSHOTS
    # =========================================================================

    def create_snapshot(
        self, client_id: int, snapshot_type: str = "periodic"
    ) -> Optional[ClientSuccessMetric]:
        """Create a new success metric snapshot for a client"""
        metrics = self.calculate_client_metrics(client_id)
        if "error" in metrics:
            return None

        snapshot = ClientSuccessMetric(
            client_id=client_id,
            snapshot_date=date.today(),
            snapshot_type=snapshot_type,
            initial_negative_items=metrics["initial_negative_items"],
            initial_equifax_score=metrics["initial_equifax_score"],
            initial_experian_score=metrics["initial_experian_score"],
            initial_transunion_score=metrics["initial_transunion_score"],
            initial_avg_score=metrics["initial_avg_score"],
            current_negative_items=metrics["current_negative_items"],
            current_equifax_score=metrics["current_equifax_score"],
            current_experian_score=metrics["current_experian_score"],
            current_transunion_score=metrics["current_transunion_score"],
            current_avg_score=metrics["current_avg_score"],
            items_deleted=metrics["items_deleted"],
            items_verified=metrics["items_verified"],
            items_updated=metrics["items_updated"],
            items_in_progress=metrics["items_in_progress"],
            equifax_items_deleted=metrics["equifax_items_deleted"],
            experian_items_deleted=metrics["experian_items_deleted"],
            transunion_items_deleted=metrics["transunion_items_deleted"],
            equifax_score_change=metrics["equifax_score_change"],
            experian_score_change=metrics["experian_score_change"],
            transunion_score_change=metrics["transunion_score_change"],
            avg_score_change=metrics["avg_score_change"],
            deletion_rate=metrics["deletion_rate"] / 100,  # Store as decimal
            dispute_rounds_completed=metrics["dispute_rounds_completed"],
            days_in_program=metrics["days_in_program"],
            estimated_value_recovered=metrics["estimated_value_recovered"],
            is_active=metrics["is_active"],
            case_complete=metrics["case_complete"],
        )

        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        return snapshot

    def get_latest_snapshot(self, client_id: int) -> Optional[ClientSuccessMetric]:
        """Get the most recent snapshot for a client"""
        return (
            self.db.query(ClientSuccessMetric)
            .filter(ClientSuccessMetric.client_id == client_id)
            .order_by(ClientSuccessMetric.created_at.desc())
            .first()
        )

    def get_snapshot_history(
        self, client_id: int, limit: int = 12
    ) -> List[ClientSuccessMetric]:
        """Get snapshot history for a client"""
        return (
            self.db.query(ClientSuccessMetric)
            .filter(ClientSuccessMetric.client_id == client_id)
            .order_by(ClientSuccessMetric.snapshot_date.desc())
            .limit(limit)
            .all()
        )

    def update_all_clients(self, snapshot_type: str = "periodic") -> Dict[str, Any]:
        """Create snapshots for all active clients"""
        active_clients = (
            self.db.query(Client)
            .filter(Client.status.in_(["active", "pending", "signup"]))
            .all()
        )

        created = 0
        errors = 0

        for client in active_clients:
            try:
                snapshot = self.create_snapshot(client.id, snapshot_type)
                if snapshot:
                    created += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1

        return {
            "total_clients": len(active_clients),
            "snapshots_created": created,
            "errors": errors,
        }

    # =========================================================================
    # CLIENT SUCCESS SUMMARY
    # =========================================================================

    def get_client_summary(self, client_id: int) -> Dict[str, Any]:
        """Get comprehensive success summary for a client"""
        # Get current calculated metrics
        metrics = self.calculate_client_metrics(client_id)
        if "error" in metrics:
            return metrics

        # Get historical snapshots for trend
        history = self.get_snapshot_history(client_id, limit=6)

        # Build trend data
        trend_data = []
        for snapshot in reversed(history):
            trend_data.append(
                {
                    "date": (
                        snapshot.snapshot_date.isoformat()
                        if snapshot.snapshot_date
                        else None
                    ),
                    "items_deleted": snapshot.items_deleted,
                    "avg_score": snapshot.current_avg_score,
                    "deletion_rate": round((snapshot.deletion_rate or 0) * 100, 1),
                }
            )

        # Calculate success grade
        grade = self._calculate_success_grade(metrics)

        return {
            **metrics,
            "success_grade": grade,
            "trend_data": trend_data,
            "has_score_data": metrics.get("initial_avg_score") is not None,
        }

    def _calculate_success_grade(self, metrics: Dict) -> str:
        """Calculate an A-F success grade based on metrics"""
        score = 0

        # Deletion rate (up to 40 points)
        deletion_rate = metrics.get("deletion_rate", 0)
        if deletion_rate >= 80:
            score += 40
        elif deletion_rate >= 60:
            score += 30
        elif deletion_rate >= 40:
            score += 20
        elif deletion_rate >= 20:
            score += 10

        # Score improvement (up to 40 points)
        avg_change = metrics.get("avg_score_change", 0)
        if avg_change >= 100:
            score += 40
        elif avg_change >= 75:
            score += 35
        elif avg_change >= 50:
            score += 30
        elif avg_change >= 30:
            score += 20
        elif avg_change >= 10:
            score += 10

        # Items deleted (up to 20 points)
        items_deleted = metrics.get("items_deleted", 0)
        if items_deleted >= 20:
            score += 20
        elif items_deleted >= 15:
            score += 15
        elif items_deleted >= 10:
            score += 12
        elif items_deleted >= 5:
            score += 8
        elif items_deleted >= 1:
            score += 4

        # Convert to grade
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C+"
        elif score >= 40:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"

    # =========================================================================
    # AGGREGATE REPORTS
    # =========================================================================

    def get_aggregate_report(self, period: str = "all") -> Dict[str, Any]:
        """Get aggregate success metrics across all clients"""
        # Define date filter
        date_filter = None
        if period == "month":
            date_filter = datetime.utcnow() - timedelta(days=30)
        elif period == "quarter":
            date_filter = datetime.utcnow() - timedelta(days=90)
        elif period == "year":
            date_filter = datetime.utcnow() - timedelta(days=365)

        # Base query for clients
        client_query = self.db.query(Client).filter(
            Client.status.in_(["active", "complete"])
        )
        if date_filter:
            client_query = client_query.filter(Client.created_at >= date_filter)

        clients = client_query.all()

        # Aggregate metrics
        total_clients = len(clients)
        total_items_deleted = 0
        total_items_verified = 0
        total_initial_negatives = 0
        total_score_improvement = 0
        clients_with_scores = 0
        completed_cases = 0
        total_estimated_value = 0

        grade_counts = {
            "A+": 0,
            "A": 0,
            "B+": 0,
            "B": 0,
            "C+": 0,
            "C": 0,
            "D": 0,
            "F": 0,
        }

        for client in clients:
            metrics = self.calculate_client_metrics(client.id)
            if "error" not in metrics:
                total_items_deleted += metrics.get("items_deleted", 0)
                total_items_verified += metrics.get("items_verified", 0)
                total_initial_negatives += metrics.get("initial_negative_items", 0)
                total_estimated_value += metrics.get("estimated_value_recovered", 0)

                if metrics.get("avg_score_change"):
                    total_score_improvement += metrics["avg_score_change"]
                    clients_with_scores += 1

                if metrics.get("case_complete"):
                    completed_cases += 1

                grade = self._calculate_success_grade(metrics)
                if grade in grade_counts:
                    grade_counts[grade] += 1

        # Calculate averages
        avg_deletion_rate = 0
        if total_initial_negatives > 0:
            avg_deletion_rate = (total_items_deleted / total_initial_negatives) * 100

        avg_score_improvement = 0
        if clients_with_scores > 0:
            avg_score_improvement = total_score_improvement / clients_with_scores

        return {
            "period": period,
            "total_clients": total_clients,
            "completed_cases": completed_cases,
            "completion_rate": round(
                (completed_cases / total_clients * 100) if total_clients > 0 else 0, 1
            ),
            "total_items_deleted": total_items_deleted,
            "total_items_verified": total_items_verified,
            "total_initial_negatives": total_initial_negatives,
            "avg_deletion_rate": round(avg_deletion_rate, 1),
            "avg_score_improvement": round(avg_score_improvement, 1),
            "total_estimated_value": round(total_estimated_value, 2),
            "grade_distribution": grade_counts,
        }

    def get_top_performers(
        self, limit: int = 10, metric: str = "deletion_rate"
    ) -> List[Dict]:
        """Get top performing clients by specified metric"""
        # Get latest snapshot for each client
        subquery = (
            self.db.query(
                ClientSuccessMetric.client_id,
                func.max(ClientSuccessMetric.id).label("max_id"),
            )
            .group_by(ClientSuccessMetric.client_id)
            .subquery()
        )

        query = self.db.query(ClientSuccessMetric).join(
            subquery,
            and_(
                ClientSuccessMetric.client_id == subquery.c.client_id,
                ClientSuccessMetric.id == subquery.c.max_id,
            ),
        )

        # Order by metric
        if metric == "deletion_rate":
            query = query.order_by(desc(ClientSuccessMetric.deletion_rate))
        elif metric == "items_deleted":
            query = query.order_by(desc(ClientSuccessMetric.items_deleted))
        elif metric == "score_improvement":
            query = query.order_by(desc(ClientSuccessMetric.avg_score_change))
        elif metric == "estimated_value":
            query = query.order_by(desc(ClientSuccessMetric.estimated_value_recovered))
        else:
            query = query.order_by(desc(ClientSuccessMetric.deletion_rate))

        snapshots = query.limit(limit).all()

        results = []
        for snapshot in snapshots:
            client = (
                self.db.query(Client).filter(Client.id == snapshot.client_id).first()
            )
            if client:
                results.append(
                    {
                        "client_id": client.id,
                        "client_name": client.name,
                        "deletion_rate": round((snapshot.deletion_rate or 0) * 100, 1),
                        "items_deleted": snapshot.items_deleted,
                        "avg_score_change": snapshot.avg_score_change,
                        "estimated_value": snapshot.estimated_value_recovered,
                        "days_in_program": snapshot.days_in_program,
                        "dispute_rounds": snapshot.dispute_rounds_completed,
                    }
                )

        return results

    def get_success_trend(
        self, period: str = "month", granularity: str = "week"
    ) -> List[Dict]:
        """Get success metrics trend over time"""
        # Determine date range
        end_date = date.today()
        if period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "quarter":
            start_date = end_date - timedelta(days=90)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)

        # Get snapshots in range
        snapshots = (
            self.db.query(ClientSuccessMetric)
            .filter(
                ClientSuccessMetric.snapshot_date >= start_date,
                ClientSuccessMetric.snapshot_date <= end_date,
            )
            .order_by(ClientSuccessMetric.snapshot_date)
            .all()
        )

        # Group by date
        date_groups = {}
        for snapshot in snapshots:
            date_key = snapshot.snapshot_date.isoformat()
            if date_key not in date_groups:
                date_groups[date_key] = {
                    "date": date_key,
                    "total_deleted": 0,
                    "total_verified": 0,
                    "avg_deletion_rate": [],
                    "avg_score_change": [],
                    "count": 0,
                }

            date_groups[date_key]["total_deleted"] += snapshot.items_deleted or 0
            date_groups[date_key]["total_verified"] += snapshot.items_verified or 0
            if snapshot.deletion_rate:
                date_groups[date_key]["avg_deletion_rate"].append(
                    snapshot.deletion_rate
                )
            if snapshot.avg_score_change:
                date_groups[date_key]["avg_score_change"].append(
                    snapshot.avg_score_change
                )
            date_groups[date_key]["count"] += 1

        # Calculate averages
        trend_data = []
        for date_key in sorted(date_groups.keys()):
            group = date_groups[date_key]
            avg_del_rate = (
                sum(group["avg_deletion_rate"]) / len(group["avg_deletion_rate"])
                if group["avg_deletion_rate"]
                else 0
            )
            avg_score = (
                sum(group["avg_score_change"]) / len(group["avg_score_change"])
                if group["avg_score_change"]
                else 0
            )

            trend_data.append(
                {
                    "date": date_key,
                    "total_deleted": group["total_deleted"],
                    "total_verified": group["total_verified"],
                    "avg_deletion_rate": round(avg_del_rate * 100, 1),
                    "avg_score_change": round(avg_score, 1),
                    "snapshots_count": group["count"],
                }
            )

        return trend_data

    # =========================================================================
    # DASHBOARD SUMMARY
    # =========================================================================

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary data for success metrics dashboard"""
        # Get aggregate stats
        aggregate = self.get_aggregate_report("all")
        monthly = self.get_aggregate_report("month")

        # Get top performers
        top_by_deletion = self.get_top_performers(5, "deletion_rate")
        top_by_score = self.get_top_performers(5, "score_improvement")

        # Get trend data
        trend = self.get_success_trend("month", "day")

        # Count active clients
        active_clients = self.db.query(Client).filter(Client.status == "active").count()

        # Get recent completions
        recent_completions = (
            self.db.query(Client)
            .filter(
                Client.status == "complete",
                Client.updated_at >= datetime.utcnow() - timedelta(days=30),
            )
            .count()
        )

        return {
            "stats": {
                "total_clients": aggregate["total_clients"],
                "active_clients": active_clients,
                "completed_cases": aggregate["completed_cases"],
                "completion_rate": aggregate["completion_rate"],
                "total_items_deleted": aggregate["total_items_deleted"],
                "avg_deletion_rate": aggregate["avg_deletion_rate"],
                "avg_score_improvement": aggregate["avg_score_improvement"],
                "total_estimated_value": aggregate["total_estimated_value"],
                "recent_completions": recent_completions,
            },
            "monthly_stats": {
                "items_deleted": monthly["total_items_deleted"],
                "avg_deletion_rate": monthly["avg_deletion_rate"],
                "avg_score_improvement": monthly["avg_score_improvement"],
            },
            "top_by_deletion_rate": top_by_deletion,
            "top_by_score_improvement": top_by_score,
            "trend_data": trend,
            "grade_distribution": aggregate["grade_distribution"],
        }

    def get_bureau_breakdown(self) -> Dict[str, Any]:
        """Get success metrics broken down by bureau"""
        # Get latest snapshot for each client
        subquery = (
            self.db.query(
                ClientSuccessMetric.client_id,
                func.max(ClientSuccessMetric.id).label("max_id"),
            )
            .group_by(ClientSuccessMetric.client_id)
            .subquery()
        )

        snapshots = (
            self.db.query(ClientSuccessMetric)
            .join(
                subquery,
                and_(
                    ClientSuccessMetric.client_id == subquery.c.client_id,
                    ClientSuccessMetric.id == subquery.c.max_id,
                ),
            )
            .all()
        )

        equifax_total = 0
        experian_total = 0
        transunion_total = 0
        equifax_score_total = 0
        experian_score_total = 0
        transunion_score_total = 0
        score_count = 0

        for snapshot in snapshots:
            equifax_total += snapshot.equifax_items_deleted or 0
            experian_total += snapshot.experian_items_deleted or 0
            transunion_total += snapshot.transunion_items_deleted or 0

            if snapshot.equifax_score_change:
                equifax_score_total += snapshot.equifax_score_change
            if snapshot.experian_score_change:
                experian_score_total += snapshot.experian_score_change
            if snapshot.transunion_score_change:
                transunion_score_total += snapshot.transunion_score_change
            if any(
                [
                    snapshot.equifax_score_change,
                    snapshot.experian_score_change,
                    snapshot.transunion_score_change,
                ]
            ):
                score_count += 1

        return {
            "items_deleted": {
                "equifax": equifax_total,
                "experian": experian_total,
                "transunion": transunion_total,
                "total": equifax_total + experian_total + transunion_total,
            },
            "avg_score_improvement": {
                "equifax": (
                    round(equifax_score_total / score_count, 1) if score_count else 0
                ),
                "experian": (
                    round(experian_score_total / score_count, 1) if score_count else 0
                ),
                "transunion": (
                    round(transunion_score_total / score_count, 1) if score_count else 0
                ),
            },
            "total_snapshots": len(snapshots),
        }

    # =========================================================================
    # EXPORT
    # =========================================================================

    def export_success_data(self, client_ids: Optional[List[int]] = None) -> List[Dict]:
        """Export success metrics for specified clients or all"""
        query = self.db.query(Client)
        if client_ids:
            query = query.filter(Client.id.in_(client_ids))

        clients = query.all()

        export_data = []
        for client in clients:
            metrics = self.calculate_client_metrics(client.id)
            if "error" not in metrics:
                grade = self._calculate_success_grade(metrics)
                export_data.append(
                    {
                        "client_id": client.id,
                        "client_name": client.name,
                        "email": client.email,
                        "status": client.status,
                        "dispute_status": client.dispute_status,
                        "initial_negatives": metrics["initial_negative_items"],
                        "current_negatives": metrics["current_negative_items"],
                        "items_deleted": metrics["items_deleted"],
                        "items_verified": metrics["items_verified"],
                        "deletion_rate": metrics["deletion_rate"],
                        "initial_avg_score": metrics["initial_avg_score"],
                        "current_avg_score": metrics["current_avg_score"],
                        "score_improvement": metrics["avg_score_change"],
                        "dispute_rounds": metrics["dispute_rounds_completed"],
                        "days_in_program": metrics["days_in_program"],
                        "estimated_value": metrics["estimated_value_recovered"],
                        "success_grade": grade,
                    }
                )

        return export_data


# =========================================================================
# STANDALONE FUNCTIONS (for use by other services)
# =========================================================================


def get_client_success_metrics(client_id: int) -> Optional[Dict[str, Any]]:
    """
    Standalone function to get client success metrics.
    Used by testimonial_service and other services that need simple metrics.

    Returns dict with:
        - total_deleted: Number of negative items deleted
        - score_improvement: Average score improvement
        - items_deleted: Same as total_deleted (for compatibility)
        - avg_score_change: Same as score_improvement (for compatibility)
    """
    from database import get_db

    try:
        db = get_db()
        service = ClientSuccessService(db)
        metrics = service.calculate_client_metrics(client_id)

        if "error" in metrics:
            return None

        return {
            "total_deleted": metrics.get("items_deleted", 0),
            "score_improvement": metrics.get("avg_score_change", 0),
            "items_deleted": metrics.get("items_deleted", 0),
            "avg_score_change": metrics.get("avg_score_change", 0),
            "deletion_rate": metrics.get("deletion_rate", 0),
            "days_in_program": metrics.get("days_in_program", 0),
        }
    except Exception:
        return None
