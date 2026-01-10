"""
Smart Letter Escalation Engine Service

AI-powered recommendation logic for optimal dispute escalation strategies
based on case history, furnisher behavior patterns, and violation severity.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import (
    Analysis,
    CaseScore,
    Client,
    CRAResponse,
    Damages,
    DisputeItem,
    EscalationRecommendation,
    Furnisher,
    FurnisherStats,
    Standing,
    Violation,
    get_db,
)

DISPUTE_ACTIONS = {
    "standard_redispute": {
        "name": "Standard Re-dispute",
        "description": "Normal round 2+ dispute with additional evidence",
        "escalation_level": 1,
    },
    "mov_demand": {
        "name": "Method of Verification Demand",
        "description": "FCRA §611 demand for verification procedures used",
        "escalation_level": 2,
    },
    "direct_furnisher": {
        "name": "Direct Furnisher Dispute",
        "description": "Dispute sent directly to data furnisher under FCRA §623",
        "escalation_level": 2,
    },
    "regulatory_complaint": {
        "name": "Regulatory Complaint",
        "description": "File CFPB/FTC/State AG complaint against CRA or furnisher",
        "escalation_level": 3,
    },
    "intent_to_sue": {
        "name": "Intent to Sue Notice",
        "description": "Pre-litigation notice citing violations and damages",
        "escalation_level": 4,
    },
    "settlement_demand": {
        "name": "Settlement Demand",
        "description": "Formal settlement demand with calculated damages",
        "escalation_level": 4,
    },
    "media_pressure": {
        "name": "Media Pressure",
        "description": "Mention potential publicity for egregious cases",
        "escalation_level": 5,
    },
}

TIMING_ACTIONS = {
    "wait_response": {
        "name": "Wait for Response",
        "description": "Wait for CRA response within statutory timeframe",
        "days": 30,
    },
    "follow_up": {
        "name": "Send Follow-up",
        "description": "Send follow-up letter after deadline passes",
        "days": 35,
    },
    "escalate_immediately": {
        "name": "Escalate Immediately",
        "description": "Skip waiting period due to violation severity",
        "days": 0,
    },
}

DOCUMENTATION_ACTIONS = {
    "gather_evidence": {
        "name": "Gather Evidence",
        "description": "Collect additional supporting documentation",
    },
    "request_disclosures": {
        "name": "Request File Disclosure",
        "description": "Request complete consumer file under FCRA §609",
    },
    "prepare_litigation": {
        "name": "Prepare for Litigation",
        "description": "Begin formal litigation preparation",
    },
}


def get_dispute_history(db, client_id: int) -> List[Dict]:
    """Get complete dispute history for a client"""
    history = []

    cra_responses = (
        db.query(CRAResponse)
        .filter_by(client_id=client_id)
        .order_by(CRAResponse.created_at.desc())
        .all()
    )
    for response in cra_responses:
        history.append(
            {
                "type": "cra_response",
                "bureau": response.bureau,
                "round": response.dispute_round,
                "response_type": response.response_type,
                "date": response.received_date or response.created_at,
                "items_verified": response.items_verified or 0,
                "items_deleted": response.items_deleted or 0,
                "items_updated": response.items_updated or 0,
            }
        )

    dispute_items = (
        db.query(DisputeItem)
        .filter_by(client_id=client_id)
        .order_by(DisputeItem.created_at.desc())
        .all()
    )
    for item in dispute_items:
        history.append(
            {
                "type": "dispute_item",
                "bureau": item.bureau,
                "creditor": item.creditor_name,
                "status": item.status,
                "round": item.dispute_round or 1,
                "date": item.created_at,
            }
        )

    return history


def get_furnisher_performance(db, creditor_name: str) -> Dict:
    """Get furnisher statistics and deletion rates"""
    furnisher = (
        db.query(Furnisher).filter(Furnisher.name.ilike(f"%{creditor_name}%")).first()
    )

    if not furnisher or not furnisher.stats:
        return {
            "found": False,
            "name": creditor_name,
            "deletion_rate": 0.5,
            "avg_response_days": 25,
            "settlement_rate": 0.1,
            "violation_count": 0,
        }

    stats = furnisher.stats
    total_round1 = (
        stats.round_1_verified + stats.round_1_deleted + stats.round_1_updated
    )
    deletion_rate = stats.round_1_deleted / total_round1 if total_round1 > 0 else 0.5

    return {
        "found": True,
        "name": furnisher.name,
        "deletion_rate": deletion_rate,
        "avg_response_days": stats.avg_response_days or 25,
        "settlement_rate": (
            stats.settlement_count / stats.total_disputes
            if stats.total_disputes > 0
            else 0.1
        ),
        "settlement_avg": stats.settlement_avg or 0,
        "violation_count": stats.violation_count or 0,
        "mov_success_rate": (
            stats.mov_failed / stats.mov_requests_sent
            if stats.mov_requests_sent > 0
            else 0.5
        ),
        "total_disputes": stats.total_disputes or 0,
    }


def analyze_response_patterns(db, client_id: int) -> Dict:
    """Analyze bureau response patterns for the client"""
    responses = db.query(CRAResponse).filter_by(client_id=client_id).all()

    patterns: Dict[str, Any] = {
        "bureaus": {},
        "frivolous_count": 0,
        "no_response_count": 0,
        "verification_failures": 0,
        "total_responses": len(responses),
    }

    for response in responses:
        bureau = response.bureau or "Unknown"
        if bureau not in patterns["bureaus"]:
            patterns["bureaus"][bureau] = {
                "verified": 0,
                "deleted": 0,
                "updated": 0,
                "frivolous": 0,
                "no_response": 0,
            }

        if response.response_type == "verified":
            patterns["bureaus"][bureau]["verified"] += 1
        elif response.response_type == "deleted":
            patterns["bureaus"][bureau]["deleted"] += 1
        elif response.response_type == "updated":
            patterns["bureaus"][bureau]["updated"] += 1
        elif response.response_type == "frivolous":
            patterns["bureaus"][bureau]["frivolous"] += 1
            patterns["frivolous_count"] += 1
        elif response.response_type == "no_response":
            patterns["bureaus"][bureau]["no_response"] += 1
            patterns["no_response_count"] += 1

    return patterns


def calculate_violation_severity(db, client_id: int, analysis_id: Optional[int] = None) -> Dict:
    """Calculate severity of violations for the case"""
    query = db.query(Violation).filter_by(client_id=client_id)
    if analysis_id:
        query = query.filter_by(analysis_id=analysis_id)

    violations = query.all()

    severity: Dict[str, Any] = {
        "total_violations": len(violations),
        "willful_count": sum(1 for v in violations if v.is_willful),
        "section_counts": {},
        "total_statutory_min": sum(v.statutory_damages_min or 0 for v in violations),
        "total_statutory_max": sum(v.statutory_damages_max or 0 for v in violations),
        "severity_score": 0,
    }

    for v in violations:
        section = v.fcra_section or "Unknown"
        severity["section_counts"][section] = (
            severity["section_counts"].get(section, 0) + 1
        )

    severity["severity_score"] = min(
        10,
        (
            severity["total_violations"] * 0.5
            + severity["willful_count"] * 2
            + (severity["total_statutory_max"] / 10000)
        ),
    )

    return severity


def assess_documentation(db, client_id: int) -> Dict:
    """Assess strength of documentation for the case"""
    standing = db.query(Standing).filter_by(client_id=client_id).first()

    strength = {
        "has_concrete_harm": False,
        "has_dissemination": False,
        "has_causation": False,
        "denial_letters": 0,
        "adverse_action_notices": 0,
        "score": 0,
    }

    if standing:
        strength["has_concrete_harm"] = standing.has_concrete_harm or False
        strength["has_dissemination"] = standing.has_dissemination or False
        strength["has_causation"] = standing.has_causation or False
        strength["denial_letters"] = standing.denial_letters_count or 0
        strength["adverse_action_notices"] = standing.adverse_action_notices_count or 0

        score = 0
        if strength["has_concrete_harm"]:
            score += 3
        if strength["has_dissemination"]:
            score += 3
        if strength["has_causation"]:
            score += 2
        score += min(2, strength["denial_letters"])
        strength["score"] = score

    return strength


def estimate_damages(db, client_id: int, analysis_id: Optional[int] = None) -> Dict:
    """Estimate potential damages for the case"""
    query = db.query(Damages).filter_by(client_id=client_id)
    if analysis_id:
        query = query.filter_by(analysis_id=analysis_id)

    damages = query.first()

    if not damages:
        violation_severity = calculate_violation_severity(db, client_id, analysis_id)
        return {
            "actual_damages": 0,
            "statutory_damages": violation_severity["total_statutory_max"],
            "punitive_potential": 0,
            "total_exposure": violation_severity["total_statutory_max"],
            "settlement_target": violation_severity["total_statutory_max"] * 0.4,
        }

    return {
        "actual_damages": damages.actual_damages_total or 0,
        "statutory_damages": damages.statutory_damages_total or 0,
        "punitive_potential": damages.punitive_damages_amount or 0,
        "total_exposure": damages.total_exposure or 0,
        "settlement_target": damages.settlement_target or 0,
    }


def recommend_escalation(
    client_id: int, item_id: Optional[int] = None, bureau: Optional[str] = None
) -> Dict:
    """
    Main recommendation engine - analyzes case and returns optimal escalation strategy

    Returns a recommendation dict with action, confidence, reasoning, and alternatives
    """
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return {"error": "Client not found"}

        dispute_round = client.current_dispute_round or 1
        dispute_history = get_dispute_history(db, client_id)
        response_patterns = analyze_response_patterns(db, client_id)

        latest_analysis = (
            db.query(Analysis)
            .filter_by(client_id=client_id)
            .order_by(Analysis.created_at.desc())
            .first()
        )
        analysis_id = latest_analysis.id if latest_analysis else None

        violation_severity = calculate_violation_severity(db, client_id, analysis_id)
        doc_strength = assess_documentation(db, client_id)
        damages_estimate = estimate_damages(db, client_id, analysis_id)

        recommendations = []

        creditors_in_dispute = set()
        for item in dispute_history:
            if item.get("creditor"):
                creditors_in_dispute.add(item["creditor"])

        if not creditors_in_dispute:
            violations = db.query(Violation).filter_by(client_id=client_id).all()
            for v in violations:
                if v.account_name:
                    creditors_in_dispute.add(v.account_name)

        if not creditors_in_dispute:
            creditors_in_dispute.add("Unknown Creditor")

        bureaus_to_check = (
            ["Experian", "TransUnion", "Equifax"] if not bureau else [bureau]
        )

        for creditor_name in creditors_in_dispute:
            furnisher_stats = get_furnisher_performance(db, creditor_name)

            for bureau_name in bureaus_to_check:
                rec = _generate_recommendation(
                    dispute_round=dispute_round,
                    bureau=bureau_name,
                    creditor_name=creditor_name,
                    response_patterns=response_patterns,
                    furnisher_stats=furnisher_stats,
                    violation_severity=violation_severity,
                    doc_strength=doc_strength,
                    damages_estimate=damages_estimate,
                )

                if rec:
                    rec["client_id"] = client_id
                    rec["analysis_id"] = analysis_id
                    recommendations.append(rec)

        if not recommendations:
            recommendations.append(
                {
                    "client_id": client_id,
                    "analysis_id": analysis_id,
                    "dispute_round": dispute_round,
                    "bureau": bureau or "All",
                    "creditor_name": "General",
                    "current_status": "new",
                    "recommended_action": "standard_redispute",
                    "confidence_score": 0.6,
                    "reasoning": "Standard dispute process recommended for new case",
                    "supporting_factors": {"dispute_round": dispute_round},
                    "alternative_actions": ["gather_evidence", "mov_demand"],
                    "expected_outcome": "Under investigation",
                    "success_probability": 0.5,
                }
            )

        return {
            "success": True,
            "client_id": client_id,
            "dispute_round": dispute_round,
            "recommendations": recommendations,
            "summary": {
                "total_recommendations": len(recommendations),
                "highest_confidence": (
                    max(r["confidence_score"] for r in recommendations)
                    if recommendations
                    else 0
                ),
                "primary_action": (
                    recommendations[0]["recommended_action"]
                    if recommendations
                    else None
                ),
            },
        }

    finally:
        db.close()


def _generate_recommendation(
    dispute_round: int,
    bureau: str,
    creditor_name: str,
    response_patterns: Dict,
    furnisher_stats: Dict,
    violation_severity: Dict,
    doc_strength: Dict,
    damages_estimate: Dict,
) -> Optional[Dict]:
    """Generate a single recommendation based on factors"""

    recommended_action = "standard_redispute"
    confidence_score = 0.6
    reasoning = ""
    alternatives = []
    expected_outcome = "Under investigation"
    success_probability = 0.5

    bureau_pattern = response_patterns.get("bureaus", {}).get(bureau, {})
    verified_count = bureau_pattern.get("verified", 0)
    deleted_count = bureau_pattern.get("deleted", 0)
    frivolous_count = bureau_pattern.get("frivolous", 0)
    no_response_count = bureau_pattern.get("no_response", 0)

    deletion_rate = furnisher_stats.get("deletion_rate", 0.5)

    if frivolous_count > 0:
        recommended_action = "regulatory_complaint"
        confidence_score = 0.9
        reasoning = f"Bureau marked dispute as frivolous - FCRA violation (§611). Regulatory complaint strongly recommended."
        alternatives = ["intent_to_sue", "direct_furnisher"]
        expected_outcome = "Bureau compliance or settlement"
        success_probability = 0.75

    elif no_response_count > 0:
        recommended_action = "regulatory_complaint"
        confidence_score = 0.85
        reasoning = (
            f"No response within 30-day statutory period - clear FCRA §611 violation."
        )
        alternatives = ["follow_up", "intent_to_sue"]
        expected_outcome = "CFPB investigation or deletion"
        success_probability = 0.8

    elif dispute_round == 1:
        if deletion_rate < 0.3:
            recommended_action = "mov_demand"
            confidence_score = 0.7
            reasoning = f"{creditor_name} has low deletion rate ({deletion_rate*100:.0f}%). MOV demand will expose verification procedures."
            alternatives = ["standard_redispute", "direct_furnisher"]
        else:
            recommended_action = "standard_redispute"
            confidence_score = 0.75
            reasoning = f"{creditor_name} has reasonable deletion rate ({deletion_rate*100:.0f}%). Standard re-dispute likely effective."
            alternatives = ["mov_demand"]
        expected_outcome = "Deletion or update"
        success_probability = 0.4 + deletion_rate * 0.3

    elif dispute_round == 2:
        if verified_count > 0:
            if violation_severity["severity_score"] >= 7:
                recommended_action = "intent_to_sue"
                confidence_score = 0.8
                reasoning = f"Severe violations (score: {violation_severity['severity_score']}/10) with continued verification. Pre-litigation notice recommended."
                alternatives = ["regulatory_complaint", "settlement_demand"]
                expected_outcome = "Settlement negotiation"
                success_probability = 0.65
            else:
                recommended_action = "direct_furnisher"
                confidence_score = 0.75
                reasoning = f"Round 2 verification - bypass CRA and dispute directly with {creditor_name}."
                alternatives = ["regulatory_complaint", "mov_demand"]
                expected_outcome = "Furnisher deletion or update"
                success_probability = 0.5
        else:
            recommended_action = "standard_redispute"
            confidence_score = 0.7
            reasoning = "Continue standard dispute process with enhanced evidence."
            alternatives = ["mov_demand"]
            expected_outcome = "Deletion"
            success_probability = 0.55

    elif dispute_round >= 3:
        if damages_estimate["total_exposure"] > 25000 and doc_strength["score"] >= 6:
            recommended_action = "settlement_demand"
            confidence_score = 0.85
            reasoning = f"High-value case (${damages_estimate['total_exposure']:,.0f} exposure) with strong documentation (score: {doc_strength['score']}/10). Settlement demand recommended."
            alternatives = ["intent_to_sue", "prepare_litigation"]
            expected_outcome = "Settlement offer"
            success_probability = 0.7
        else:
            recommended_action = "intent_to_sue"
            confidence_score = 0.8
            reasoning = f"Round {dispute_round} with continued obstruction. Formal pre-litigation notice required."
            alternatives = ["regulatory_complaint", "settlement_demand"]
            expected_outcome = "Settlement negotiation or litigation"
            success_probability = 0.6

        if violation_severity["willful_count"] > 0:
            alternatives.append("media_pressure")
            reasoning += f" {violation_severity['willful_count']} willful violation(s) documented for punitive damages."

    current_status = (
        "verified"
        if verified_count > 0
        else "investigating" if dispute_round > 1 else "new"
    )

    return {
        "dispute_round": dispute_round,
        "bureau": bureau,
        "creditor_name": creditor_name,
        "current_status": current_status,
        "recommended_action": recommended_action,
        "confidence_score": confidence_score,
        "reasoning": reasoning,
        "supporting_factors": {
            "deletion_rate": deletion_rate,
            "verified_count": verified_count,
            "frivolous_count": frivolous_count,
            "violation_severity": violation_severity["severity_score"],
            "documentation_strength": doc_strength["score"],
            "damages_exposure": damages_estimate["total_exposure"],
        },
        "alternative_actions": alternatives,
        "expected_outcome": expected_outcome,
        "success_probability": success_probability,
    }


def get_escalation_timeline(client_id: int) -> Dict:
    """Generate timeline of recommended actions with deadlines"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return {"error": "Client not found"}

        timeline = []
        today = datetime.utcnow()

        last_response = (
            db.query(CRAResponse)
            .filter_by(client_id=client_id)
            .order_by(CRAResponse.created_at.desc())
            .first()
        )
        last_letter_date = (
            last_response.created_at
            if last_response
            else client.round_started_at or client.created_at
        )

        recommendations = recommend_escalation(client_id)

        if recommendations.get("success") and recommendations.get("recommendations"):
            primary_rec = recommendations["recommendations"][0]

            timeline.append(
                {
                    "date": today.isoformat(),
                    "action": "Review Recommendations",
                    "description": f"Review AI recommendation: {primary_rec['recommended_action']}",
                    "status": "pending",
                    "priority": "high",
                }
            )

            if primary_rec["recommended_action"] in [
                "wait_response",
                "standard_redispute",
            ]:
                deadline = last_letter_date + timedelta(days=30)
                timeline.append(
                    {
                        "date": deadline.isoformat(),
                        "action": "Response Deadline",
                        "description": "CRA must respond within 30 days per FCRA §611",
                        "status": "upcoming" if deadline > today else "overdue",
                        "priority": (
                            "high"
                            if deadline <= today + timedelta(days=5)
                            else "medium"
                        ),
                    }
                )

                follow_up = deadline + timedelta(days=5)
                timeline.append(
                    {
                        "date": follow_up.isoformat(),
                        "action": "Follow-up if No Response",
                        "description": "Send follow-up letter citing failure to respond",
                        "status": "pending",
                        "priority": "medium",
                    }
                )

            if primary_rec["recommended_action"] == "regulatory_complaint":
                timeline.append(
                    {
                        "date": (today + timedelta(days=3)).isoformat(),
                        "action": "File CFPB Complaint",
                        "description": "Submit CFPB complaint documenting violations",
                        "status": "pending",
                        "priority": "high",
                    }
                )

            if primary_rec["recommended_action"] in [
                "intent_to_sue",
                "settlement_demand",
            ]:
                timeline.append(
                    {
                        "date": (today + timedelta(days=7)).isoformat(),
                        "action": "Prepare Legal Notice",
                        "description": "Draft and send pre-litigation/settlement demand",
                        "status": "pending",
                        "priority": "high",
                    }
                )

                timeline.append(
                    {
                        "date": (today + timedelta(days=37)).isoformat(),
                        "action": "Review Response to Demand",
                        "description": "Evaluate response and determine next steps",
                        "status": "pending",
                        "priority": "high",
                    }
                )

        past_recs = (
            db.query(EscalationRecommendation)
            .filter_by(client_id=client_id, applied=True)
            .order_by(EscalationRecommendation.applied_at.desc())
            .limit(5)
            .all()
        )

        for rec in past_recs:
            timeline.append(
                {
                    "date": (
                        rec.applied_at.isoformat()
                        if rec.applied_at
                        else rec.created_at.isoformat()
                    ),
                    "action": f"Applied: {rec.recommended_action}",
                    "description": rec.reasoning[:100] if rec.reasoning else "",
                    "status": "completed",
                    "priority": "low",
                    "outcome": rec.outcome_actual,
                }
            )

        timeline.sort(key=lambda x: x["date"])

        return {
            "success": True,
            "client_id": client_id,
            "timeline": timeline,
            "current_round": client.current_dispute_round or 1,
        }

    finally:
        db.close()


def save_recommendation(recommendation: Dict) -> int:
    """Save a recommendation to the database"""
    db = get_db()
    try:
        rec = EscalationRecommendation(
            client_id=recommendation["client_id"],
            analysis_id=recommendation.get("analysis_id"),
            dispute_round=recommendation["dispute_round"],
            bureau=recommendation["bureau"],
            creditor_name=recommendation["creditor_name"],
            current_status=recommendation.get("current_status"),
            recommended_action=recommendation["recommended_action"],
            confidence_score=recommendation["confidence_score"],
            reasoning=recommendation["reasoning"],
            supporting_factors=recommendation.get("supporting_factors"),
            alternative_actions=recommendation.get("alternative_actions"),
            expected_outcome=recommendation.get("expected_outcome"),
            success_probability=recommendation.get("success_probability", 0.5),
        )
        db.add(rec)
        db.commit()
        return int(rec.id)  # type: ignore[arg-type]
    finally:
        db.close()


def apply_recommendation(recommendation_id: int) -> Dict:
    """Mark a recommendation as applied"""
    db = get_db()
    try:
        rec = db.query(EscalationRecommendation).filter_by(id=recommendation_id).first()
        if not rec:
            return {"error": "Recommendation not found"}

        rec.applied = True
        rec.applied_at = datetime.utcnow()
        rec.updated_at = datetime.utcnow()
        db.commit()

        return {"success": True, "recommendation": rec.to_dict()}
    finally:
        db.close()


def record_outcome(recommendation_id: int, outcome: str) -> Dict:
    """Record the actual outcome of an applied recommendation"""
    db = get_db()
    try:
        rec = db.query(EscalationRecommendation).filter_by(id=recommendation_id).first()
        if not rec:
            return {"error": "Recommendation not found"}

        rec.outcome_actual = outcome
        rec.outcome_recorded_at = datetime.utcnow()
        rec.updated_at = datetime.utcnow()
        db.commit()

        if rec.creditor_name:
            _update_furnisher_stats(
                db, rec.creditor_name, rec.recommended_action, outcome
            )

        return {"success": True, "recommendation": rec.to_dict()}
    finally:
        db.close()


def _update_furnisher_stats(db, creditor_name: str, action: str, outcome: str):
    """Update furnisher statistics based on outcome"""
    furnisher = (
        db.query(Furnisher).filter(Furnisher.name.ilike(f"%{creditor_name}%")).first()
    )
    if not furnisher:
        return

    if not furnisher.stats:
        stats = FurnisherStats(furnisher_id=furnisher.id)
        db.add(stats)
        furnisher.stats = stats

    stats = furnisher.stats
    stats.total_disputes = (stats.total_disputes or 0) + 1

    if outcome == "deleted":
        stats.round_1_deleted = (stats.round_1_deleted or 0) + 1
    elif outcome == "verified":
        stats.round_1_verified = (stats.round_1_verified or 0) + 1
    elif outcome == "updated":
        stats.round_1_updated = (stats.round_1_updated or 0) + 1

    if "settlement" in outcome.lower():
        stats.settlement_count = (stats.settlement_count or 0) + 1

    db.commit()


def get_escalation_stats() -> Dict:
    """Get overall escalation statistics"""
    db = get_db()
    try:
        all_recs = db.query(EscalationRecommendation).all()
        applied_recs = [r for r in all_recs if r.applied]
        completed_recs = [r for r in applied_recs if r.outcome_actual]

        action_stats: Dict[str, Dict[str, Any]] = {}
        for rec in completed_recs:
            action = rec.recommended_action
            if action not in action_stats:
                action_stats[action] = {"total": 0, "successful": 0, "outcomes": {}}
            action_stats[action]["total"] += 1

            outcome = rec.outcome_actual or "unknown"
            action_stats[action]["outcomes"][outcome] = (
                action_stats[action]["outcomes"].get(outcome, 0) + 1
            )

            if outcome in ["deleted", "updated", "settled", "settlement"]:
                action_stats[action]["successful"] += 1

        for action in action_stats:
            total = int(action_stats[action]["total"])
            successful = int(action_stats[action]["successful"])
            action_stats[action]["success_rate"] = (
                successful / total if total > 0 else 0
            )

        sorted_actions = sorted(
            action_stats.items(), key=lambda x: float(x[1]["success_rate"]), reverse=True
        )

        return {
            "success": True,
            "total_recommendations": len(all_recs),
            "applied_recommendations": len(applied_recs),
            "completed_recommendations": len(completed_recs),
            "action_stats": action_stats,
            "top_performing": [
                {"action": a, "success_rate": s["success_rate"], "total": s["total"]}
                for a, s in sorted_actions[:5]
            ],
            "overall_success_rate": (
                sum(int(s["successful"]) for s in action_stats.values())
                / len(completed_recs)
                if completed_recs
                else 0
            ),
        }
    finally:
        db.close()


def get_cases_needing_escalation_review() -> List[Dict]:
    """Get list of cases that need escalation review"""
    db = get_db()
    try:
        clients = (
            db.query(Client)
            .filter(
                Client.current_dispute_round >= 1,
                Client.dispute_status.in_(["active", "waiting_response"]),
            )
            .all()
        )

        cases_needing_review = []

        for client in clients:
            last_response = (
                db.query(CRAResponse)
                .filter_by(client_id=client.id)
                .order_by(CRAResponse.created_at.desc())
                .first()
            )

            needs_review = False
            reason = ""
            priority = "medium"

            if last_response:
                days_since_response = (
                    datetime.utcnow() - last_response.created_at
                ).days

                if (
                    last_response.response_type == "verified"
                    and days_since_response > 7
                ):
                    needs_review = True
                    reason = "Verified response needs escalation review"
                    priority = "high"
                elif last_response.response_type == "frivolous":
                    needs_review = True
                    reason = "Frivolous rejection - regulatory action needed"
                    priority = "urgent"
                elif (
                    last_response.response_type == "no_response"
                    or days_since_response > 35
                ):
                    needs_review = True
                    reason = "Response deadline passed"
                    priority = "urgent"
            else:
                if client.round_started_at:
                    days_since_start = (
                        datetime.utcnow() - client.round_started_at
                    ).days
                    if days_since_start > 35:
                        needs_review = True
                        reason = "No response after 35 days"
                        priority = "urgent"

            if needs_review:
                cases_needing_review.append(
                    {
                        "client_id": client.id,
                        "client_name": client.name,
                        "dispute_round": client.current_dispute_round or 1,
                        "reason": reason,
                        "priority": priority,
                        "last_response_date": (
                            last_response.created_at.isoformat()
                            if last_response
                            else None
                        ),
                        "last_response_type": (
                            last_response.response_type if last_response else None
                        ),
                    }
                )

        cases_needing_review.sort(
            key=lambda x: {"urgent": 0, "high": 1, "medium": 2, "low": 3}.get(
                x["priority"], 2
            )
        )

        return cases_needing_review
    finally:
        db.close()
