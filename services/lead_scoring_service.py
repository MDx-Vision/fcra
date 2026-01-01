"""
Lead Scoring Service

Automatically scores leads (clients) based on credit report analysis.
Higher scores indicate higher priority/value clients.

Scoring factors:
- Collections: +15 points each (high success rate, quick wins)
- Charge-offs: +12 points each
- Late payments: +5 points each
- Public records: +20 points each (bankruptcies, judgments = high value)
- Inquiries: +2 points each
- Violations found: +10 points each (litigation potential)
- Credit score range adjustments
- Dispute complexity bonus
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import (
    Analysis,
    Client,
    CreditReport,
    DisputeItem,
    SessionLocal,
    TradelineStatus,
    Violation,
    get_db,
)


class LeadScoringService:
    """Service for calculating and managing lead scores"""

    # Scoring weights for different factors
    SCORING_WEIGHTS = {
        # Item types from DisputeItem
        "collection": 15,
        "charge_off": 12,
        "late_payment": 5,
        "public_record": 20,
        "inquiry": 2,
        "repossession": 15,
        "foreclosure": 20,
        "judgment": 20,
        "tax_lien": 18,
        "bankruptcy": 10,  # Lower because harder to dispute
        "medical_debt": 12,
        "student_loan": 8,

        # Violations (litigation potential)
        "violation": 10,
        "willful_violation": 15,

        # Credit score ranges (bonus points)
        "score_below_500": 25,
        "score_500_549": 20,
        "score_550_599": 15,
        "score_600_649": 10,
        "score_650_699": 5,
        "score_700_plus": 0,

        # Engagement indicators
        "has_report": 10,
        "has_analysis": 5,
        "multiple_bureaus": 10,
    }

    # Maximum score cap
    MAX_SCORE = 100

    @staticmethod
    def calculate_score(client_id: int, session: Optional[Session] = None) -> Dict[str, Any]:
        """
        Calculate lead score for a client based on their credit report data.

        Args:
            client_id: The client ID to score
            session: Optional database session

        Returns:
            Dict with score, factors breakdown, and metadata
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {
                    "success": False,
                    "error": f"Client {client_id} not found",
                    "score": 0,
                    "factors": {},
                }

            factors = {}
            total_score = 0

            # Factor 1: Dispute Items by type
            item_counts = LeadScoringService._count_dispute_items(session, client_id)
            for item_type, count in item_counts.items():
                if count > 0:
                    weight = LeadScoringService.SCORING_WEIGHTS.get(item_type, 5)
                    points = min(count * weight, 40)  # Cap per category
                    factors[f"{item_type}_count"] = {
                        "count": count,
                        "weight": weight,
                        "points": points,
                    }
                    total_score += points

            # Factor 2: Violations found
            violation_counts = LeadScoringService._count_violations(session, client_id)
            if violation_counts["total"] > 0:
                violation_points = min(
                    violation_counts["total"] * LeadScoringService.SCORING_WEIGHTS["violation"],
                    30
                )
                factors["violations"] = {
                    "count": violation_counts["total"],
                    "willful": violation_counts["willful"],
                    "points": violation_points,
                }
                total_score += violation_points

                # Bonus for willful violations
                if violation_counts["willful"] > 0:
                    willful_bonus = min(violation_counts["willful"] * 5, 15)
                    factors["willful_violations_bonus"] = {
                        "count": violation_counts["willful"],
                        "points": willful_bonus,
                    }
                    total_score += willful_bonus

            # Factor 3: Tradelines (active accounts being disputed)
            tradeline_count = LeadScoringService._count_tradelines(session, client_id)
            if tradeline_count > 0:
                tradeline_points = min(tradeline_count * 3, 20)
                factors["tradelines"] = {
                    "count": tradeline_count,
                    "points": tradeline_points,
                }
                total_score += tradeline_points

            # Factor 4: Has credit report uploaded
            has_report = LeadScoringService._has_credit_report(session, client_id)
            if has_report:
                factors["has_report"] = {
                    "points": LeadScoringService.SCORING_WEIGHTS["has_report"],
                }
                total_score += LeadScoringService.SCORING_WEIGHTS["has_report"]

            # Factor 5: Has analysis completed
            has_analysis = LeadScoringService._has_analysis(session, client_id)
            if has_analysis:
                factors["has_analysis"] = {
                    "points": LeadScoringService.SCORING_WEIGHTS["has_analysis"],
                }
                total_score += LeadScoringService.SCORING_WEIGHTS["has_analysis"]

            # Factor 6: Multiple bureaus affected
            bureau_count = LeadScoringService._count_bureaus_affected(session, client_id)
            if bureau_count > 1:
                multi_bureau_bonus = min((bureau_count - 1) * 5, 10)
                factors["multiple_bureaus"] = {
                    "count": bureau_count,
                    "points": multi_bureau_bonus,
                }
                total_score += multi_bureau_bonus

            # Factor 7: Dispute status bonus (active clients get priority)
            status_bonus = LeadScoringService._get_status_bonus(client)
            if status_bonus > 0:
                factors["status_bonus"] = {
                    "status": client.dispute_status,
                    "points": status_bonus,
                }
                total_score += status_bonus

            # Cap the score at MAX_SCORE
            final_score = min(total_score, LeadScoringService.MAX_SCORE)

            return {
                "success": True,
                "score": final_score,
                "raw_score": total_score,
                "factors": factors,
                "calculated_at": datetime.utcnow().isoformat(),
                "priority": LeadScoringService._get_priority_label(final_score),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "score": 0,
                "factors": {},
            }

        finally:
            if close_session:
                session.close()

    @staticmethod
    def _count_dispute_items(session: Session, client_id: int) -> Dict[str, int]:
        """Count dispute items by type for a client"""
        items = (
            session.query(DisputeItem.item_type, func.count(DisputeItem.id))
            .filter(DisputeItem.client_id == client_id)
            .group_by(DisputeItem.item_type)
            .all()
        )

        counts = {}
        for item_type, count in items:
            if item_type:
                # Normalize item type
                normalized = item_type.lower().replace(" ", "_").replace("-", "_")
                counts[normalized] = count

        return counts

    @staticmethod
    def _count_violations(session: Session, client_id: int) -> Dict[str, int]:
        """Count violations for a client"""
        total = (
            session.query(func.count(Violation.id))
            .filter(Violation.client_id == client_id)
            .scalar()
            or 0
        )

        willful = (
            session.query(func.count(Violation.id))
            .filter(Violation.client_id == client_id, Violation.is_willful == True)
            .scalar()
            or 0
        )

        return {"total": total, "willful": willful}

    @staticmethod
    def _count_tradelines(session: Session, client_id: int) -> int:
        """Count tradelines being tracked for a client"""
        return (
            session.query(func.count(TradelineStatus.id))
            .filter(TradelineStatus.client_id == client_id)
            .scalar()
            or 0
        )

    @staticmethod
    def _has_credit_report(session: Session, client_id: int) -> bool:
        """Check if client has a credit report uploaded"""
        return (
            session.query(CreditReport.id)
            .filter(CreditReport.client_id == client_id)
            .first()
            is not None
        )

    @staticmethod
    def _has_analysis(session: Session, client_id: int) -> bool:
        """Check if client has a completed analysis"""
        return (
            session.query(Analysis.id)
            .filter(Analysis.client_id == client_id)
            .first()
            is not None
        )

    @staticmethod
    def _count_bureaus_affected(session: Session, client_id: int) -> int:
        """Count how many bureaus have dispute items"""
        bureaus = (
            session.query(DisputeItem.bureau)
            .filter(DisputeItem.client_id == client_id)
            .distinct()
            .all()
        )
        return len([b for b in bureaus if b[0]])

    @staticmethod
    def _get_status_bonus(client: Client) -> int:
        """Get bonus points based on client status"""
        status_bonuses = {
            "active": 10,
            "waiting_response": 8,
            "report_uploaded": 5,
            "lead": 3,
            "new": 2,
            "complete": 0,
            "cancelled": 0,
        }
        return status_bonuses.get(client.dispute_status or "new", 0)

    @staticmethod
    def _get_priority_label(score: int) -> str:
        """Get priority label based on score"""
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    @staticmethod
    def update_client_score(client_id: int, session: Optional[Session] = None) -> Dict[str, Any]:
        """
        Calculate and save the lead score for a client.

        Args:
            client_id: The client ID to score
            session: Optional database session

        Returns:
            Dict with updated score information
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            result = LeadScoringService.calculate_score(client_id, session)

            if result["success"]:
                client = session.query(Client).filter(Client.id == client_id).first()
                if client:
                    client.lead_score = result["score"]
                    client.lead_score_factors = result["factors"]
                    client.lead_scored_at = datetime.utcnow()
                    session.commit()

                    result["saved"] = True

            return result

        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "error": str(e),
                "score": 0,
                "factors": {},
            }

        finally:
            if close_session:
                session.close()

    @staticmethod
    def score_all_clients(limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Score all clients (or a limited batch).

        Args:
            limit: Optional limit on number of clients to score

        Returns:
            Dict with summary of scoring operation
        """
        session = SessionLocal()
        try:
            query = session.query(Client.id)
            if limit:
                query = query.limit(limit)

            client_ids = [c.id for c in query.all()]

            scored = 0
            errors = 0
            high_priority = 0
            medium_priority = 0
            low_priority = 0

            for client_id in client_ids:
                result = LeadScoringService.update_client_score(client_id, session)
                if result["success"]:
                    scored += 1
                    priority = result.get("priority", "LOW")
                    if priority == "HIGH":
                        high_priority += 1
                    elif priority == "MEDIUM":
                        medium_priority += 1
                    else:
                        low_priority += 1
                else:
                    errors += 1

            return {
                "success": True,
                "total_clients": len(client_ids),
                "scored": scored,
                "errors": errors,
                "high_priority": high_priority,
                "medium_priority": medium_priority,
                "low_priority": low_priority,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

        finally:
            session.close()

    @staticmethod
    def get_top_leads(limit: int = 10, session: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        Get the top leads by score.

        Args:
            limit: Number of leads to return
            session: Optional database session

        Returns:
            List of top leads with their scores
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            clients = (
                session.query(Client)
                .filter(Client.lead_score > 0)
                .order_by(Client.lead_score.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "score": c.lead_score,
                    "priority": LeadScoringService._get_priority_label(c.lead_score or 0),
                    "status": c.dispute_status,
                    "scored_at": c.lead_scored_at.isoformat() if c.lead_scored_at else None,
                }
                for c in clients
            ]

        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_score_distribution(session: Optional[Session] = None) -> Dict[str, int]:
        """
        Get distribution of lead scores across priority levels.

        Returns:
            Dict with counts per priority level
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            high = (
                session.query(func.count(Client.id))
                .filter(Client.lead_score >= 70)
                .scalar()
                or 0
            )

            medium = (
                session.query(func.count(Client.id))
                .filter(Client.lead_score >= 40, Client.lead_score < 70)
                .scalar()
                or 0
            )

            low = (
                session.query(func.count(Client.id))
                .filter(Client.lead_score > 0, Client.lead_score < 40)
                .scalar()
                or 0
            )

            unscored = (
                session.query(func.count(Client.id))
                .filter((Client.lead_score == 0) | (Client.lead_score == None))
                .scalar()
                or 0
            )

            return {
                "high": high,
                "medium": medium,
                "low": low,
                "unscored": unscored,
                "total": high + medium + low + unscored,
            }

        finally:
            if close_session:
                session.close()


# Convenience functions for external use
def score_client(client_id: int) -> Dict[str, Any]:
    """Score a single client and save the result"""
    return LeadScoringService.update_client_score(client_id)


def get_client_score(client_id: int) -> Dict[str, Any]:
    """Get the current score for a client (without saving)"""
    return LeadScoringService.calculate_score(client_id)


def rescore_all_clients() -> Dict[str, Any]:
    """Rescore all clients in the database"""
    return LeadScoringService.score_all_clients()
