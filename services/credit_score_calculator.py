"""
Credit Score Improvement Calculator Service
Estimates credit score improvements based on negative item removal
and tracks progress from beginning to end.
"""

from datetime import datetime

from database import (
    Analysis,
    Client,
    CreditScoreProjection,
    CreditScoreSnapshot,
    Violation,
    get_db,
)

SCORE_IMPACT_BY_TYPE = {
    "late_payment_30": {
        "min": 15,
        "max": 40,
        "avg": 25,
        "label": "30-Day Late Payment",
        "description": "Payment 30 days past due",
        "category": "payment_history",
        "severity": "moderate",
    },
    "late_payment_60": {
        "min": 25,
        "max": 65,
        "avg": 45,
        "label": "60-Day Late Payment",
        "description": "Payment 60 days past due",
        "category": "payment_history",
        "severity": "high",
    },
    "late_payment_90": {
        "min": 35,
        "max": 85,
        "avg": 60,
        "label": "90-Day Late Payment",
        "description": "Payment 90+ days past due",
        "category": "payment_history",
        "severity": "severe",
    },
    "late_payment_120": {
        "min": 45,
        "max": 95,
        "avg": 70,
        "label": "120-Day Late Payment",
        "description": "Payment 120+ days past due",
        "category": "payment_history",
        "severity": "severe",
    },
    "collection": {
        "min": 50,
        "max": 110,
        "avg": 80,
        "label": "Collection Account",
        "description": "Account sent to collections",
        "category": "derogatory",
        "severity": "severe",
    },
    "medical_collection": {
        "min": 25,
        "max": 65,
        "avg": 45,
        "label": "Medical Collection",
        "description": "Medical debt in collections (reduced impact since 2022)",
        "category": "derogatory",
        "severity": "moderate",
    },
    "paid_collection": {
        "min": 15,
        "max": 40,
        "avg": 25,
        "label": "Paid Collection",
        "description": "Collection account that has been paid",
        "category": "derogatory",
        "severity": "low",
    },
    "charge_off": {
        "min": 55,
        "max": 120,
        "avg": 85,
        "label": "Charge-Off",
        "description": "Creditor wrote off the debt as a loss",
        "category": "derogatory",
        "severity": "severe",
    },
    "repossession": {
        "min": 60,
        "max": 130,
        "avg": 95,
        "label": "Repossession",
        "description": "Vehicle or property repossessed",
        "category": "derogatory",
        "severity": "severe",
    },
    "foreclosure": {
        "min": 85,
        "max": 160,
        "avg": 120,
        "label": "Foreclosure",
        "description": "Home foreclosure",
        "category": "public_record",
        "severity": "critical",
    },
    "short_sale": {
        "min": 50,
        "max": 105,
        "avg": 75,
        "label": "Short Sale",
        "description": "Property sold for less than owed",
        "category": "derogatory",
        "severity": "severe",
    },
    "deed_in_lieu": {
        "min": 55,
        "max": 110,
        "avg": 80,
        "label": "Deed in Lieu",
        "description": "Deed in lieu of foreclosure",
        "category": "derogatory",
        "severity": "severe",
    },
    "bankruptcy_ch7": {
        "min": 130,
        "max": 240,
        "avg": 180,
        "label": "Chapter 7 Bankruptcy",
        "description": "Liquidation bankruptcy",
        "category": "public_record",
        "severity": "critical",
    },
    "bankruptcy_ch13": {
        "min": 100,
        "max": 200,
        "avg": 150,
        "label": "Chapter 13 Bankruptcy",
        "description": "Reorganization bankruptcy",
        "category": "public_record",
        "severity": "critical",
    },
    "bankruptcy": {
        "min": 130,
        "max": 240,
        "avg": 180,
        "label": "Bankruptcy",
        "description": "Bankruptcy filing",
        "category": "public_record",
        "severity": "critical",
    },
    "judgment": {
        "min": 50,
        "max": 100,
        "avg": 75,
        "label": "Civil Judgment",
        "description": "Court judgment against consumer",
        "category": "public_record",
        "severity": "severe",
    },
    "tax_lien": {
        "min": 40,
        "max": 90,
        "avg": 65,
        "label": "Tax Lien",
        "description": "Federal or state tax lien",
        "category": "public_record",
        "severity": "severe",
    },
    "hard_inquiry": {
        "min": 5,
        "max": 15,
        "avg": 10,
        "label": "Hard Inquiry",
        "description": "Credit check from application",
        "category": "inquiry",
        "severity": "low",
    },
    "multiple_inquiries": {
        "min": 15,
        "max": 35,
        "avg": 25,
        "label": "Multiple Hard Inquiries",
        "description": "Several credit checks in short period",
        "category": "inquiry",
        "severity": "moderate",
    },
    "inquiry": {
        "min": 5,
        "max": 15,
        "avg": 10,
        "label": "Hard Inquiry",
        "description": "Credit application inquiry",
        "category": "inquiry",
        "severity": "low",
    },
    "high_utilization": {
        "min": 20,
        "max": 50,
        "avg": 35,
        "label": "High Credit Utilization",
        "description": "Balance over 30% of credit limit",
        "category": "utilization",
        "severity": "moderate",
    },
    "maxed_out": {
        "min": 35,
        "max": 75,
        "avg": 55,
        "label": "Maxed Out Account",
        "description": "Balance at or near credit limit",
        "category": "utilization",
        "severity": "high",
    },
    "over_limit": {
        "min": 40,
        "max": 85,
        "avg": 60,
        "label": "Over Limit Account",
        "description": "Balance exceeds credit limit",
        "category": "utilization",
        "severity": "high",
    },
    "closed_negative": {
        "min": 10,
        "max": 30,
        "avg": 20,
        "label": "Closed Account (Negative)",
        "description": "Account closed by creditor",
        "category": "account_status",
        "severity": "low",
    },
    "settled_less": {
        "min": 35,
        "max": 75,
        "avg": 55,
        "label": "Settled for Less",
        "description": "Debt settled for less than owed",
        "category": "derogatory",
        "severity": "moderate",
    },
    "mixed_file": {
        "min": 30,
        "max": 80,
        "avg": 50,
        "label": "Mixed File Error",
        "description": "Another persons info mixed in report",
        "category": "error",
        "severity": "high",
    },
    "inaccurate_info": {
        "min": 15,
        "max": 60,
        "avg": 35,
        "label": "Inaccurate Information",
        "description": "General data inaccuracy",
        "category": "error",
        "severity": "moderate",
    },
    "duplicate_account": {
        "min": 20,
        "max": 50,
        "avg": 35,
        "label": "Duplicate Account",
        "description": "Same account reported twice",
        "category": "error",
        "severity": "moderate",
    },
    "wrong_balance": {
        "min": 10,
        "max": 40,
        "avg": 25,
        "label": "Wrong Balance",
        "description": "Incorrect balance reported",
        "category": "error",
        "severity": "low",
    },
    "wrong_status": {
        "min": 15,
        "max": 50,
        "avg": 30,
        "label": "Wrong Account Status",
        "description": "Account status incorrectly reported",
        "category": "error",
        "severity": "moderate",
    },
    "wrong_date": {
        "min": 10,
        "max": 35,
        "avg": 20,
        "label": "Wrong Date",
        "description": "Incorrect date of first delinquency or other date",
        "category": "error",
        "severity": "low",
    },
    "obsolete_info": {
        "min": 25,
        "max": 75,
        "avg": 50,
        "label": "Obsolete Information",
        "description": "Item past 7-year reporting limit",
        "category": "error",
        "severity": "high",
    },
    "reaged_debt": {
        "min": 30,
        "max": 80,
        "avg": 55,
        "label": "Re-aged Debt",
        "description": "Debt illegally re-aged to extend reporting",
        "category": "error",
        "severity": "high",
    },
    "identity_error": {
        "min": 25,
        "max": 70,
        "avg": 45,
        "label": "Identity Error",
        "description": "Wrong name, address, or SSN",
        "category": "error",
        "severity": "moderate",
    },
    "identity_theft": {
        "min": 50,
        "max": 150,
        "avg": 100,
        "label": "Identity Theft Account",
        "description": "Fraudulent account from identity theft",
        "category": "fraud",
        "severity": "critical",
    },
    "authorized_user_negative": {
        "min": 15,
        "max": 45,
        "avg": 30,
        "label": "Authorized User Negative",
        "description": "Negative item from authorized user account",
        "category": "account_status",
        "severity": "moderate",
    },
    "student_loan_default": {
        "min": 65,
        "max": 130,
        "avg": 95,
        "label": "Student Loan Default",
        "description": "Federal or private student loan in default",
        "category": "derogatory",
        "severity": "severe",
    },
    "profit_loss": {
        "min": 45,
        "max": 100,
        "avg": 70,
        "label": "Profit and Loss Write-Off",
        "description": "Account written off as profit/loss",
        "category": "derogatory",
        "severity": "severe",
    },
    "unknown": {
        "min": 10,
        "max": 30,
        "avg": 20,
        "label": "Other Negative Item",
        "description": "Unclassified negative item",
        "category": "other",
        "severity": "low",
    },
}

ITEM_CATEGORIES = {
    "payment_history": {"label": "Payment History", "weight": 0.35, "color": "#ef4444"},
    "derogatory": {"label": "Derogatory Marks", "weight": 0.30, "color": "#dc2626"},
    "public_record": {"label": "Public Records", "weight": 0.15, "color": "#991b1b"},
    "utilization": {"label": "Credit Utilization", "weight": 0.30, "color": "#f97316"},
    "inquiry": {"label": "Credit Inquiries", "weight": 0.10, "color": "#eab308"},
    "account_status": {"label": "Account Status", "weight": 0.10, "color": "#84cc16"},
    "error": {"label": "Reporting Errors", "weight": 0.15, "color": "#06b6d4"},
    "fraud": {"label": "Fraud/Identity Theft", "weight": 0.25, "color": "#8b5cf6"},
    "other": {"label": "Other", "weight": 0.05, "color": "#6b7280"},
}

SEVERITY_LEVELS = {
    "low": {"label": "Low Impact", "color": "#22c55e", "multiplier": 1.0},
    "moderate": {"label": "Moderate Impact", "color": "#eab308", "multiplier": 1.0},
    "high": {"label": "High Impact", "color": "#f97316", "multiplier": 1.0},
    "severe": {"label": "Severe Impact", "color": "#ef4444", "multiplier": 1.0},
    "critical": {"label": "Critical Impact", "color": "#dc2626", "multiplier": 1.0},
}

SCORE_RANGES = {
    "poor": {"min": 300, "max": 579, "label": "Poor"},
    "fair": {"min": 580, "max": 669, "label": "Fair"},
    "good": {"min": 670, "max": 739, "label": "Good"},
    "very_good": {"min": 740, "max": 799, "label": "Very Good"},
    "excellent": {"min": 800, "max": 850, "label": "Excellent"},
}


def get_score_range_label(score):
    """Get the credit score range label"""
    if not score:
        return "Unknown"
    for range_key, range_data in SCORE_RANGES.items():
        if range_data["min"] <= score <= range_data["max"]:
            return range_data["label"]
    return "Unknown"


def categorize_violation_type(violation_text):
    """Map violation description to impact category"""
    text = violation_text.lower() if violation_text else ""

    if "chapter 7" in text or "ch 7" in text or "ch7" in text:
        return "bankruptcy_ch7"
    elif "chapter 13" in text or "ch 13" in text or "ch13" in text:
        return "bankruptcy_ch13"
    elif "bankruptcy" in text:
        return "bankruptcy"
    elif "foreclosure" in text:
        return "foreclosure"
    elif "short sale" in text:
        return "short_sale"
    elif "deed in lieu" in text:
        return "deed_in_lieu"
    elif "repossession" in text or "repo" in text:
        return "repossession"
    elif "profit" in text and "loss" in text:
        return "profit_loss"
    elif "charge" in text and "off" in text:
        return "charge_off"
    elif "student loan" in text and ("default" in text or "delinq" in text):
        return "student_loan_default"
    elif "medical" in text and "collection" in text:
        return "medical_collection"
    elif "paid" in text and "collection" in text:
        return "paid_collection"
    elif "collection" in text or "collect" in text:
        return "collection"
    elif "settled" in text and "less" in text:
        return "settled_less"
    elif "120" in text and ("day" in text or "late" in text):
        return "late_payment_120"
    elif "90" in text and ("day" in text or "late" in text):
        return "late_payment_90"
    elif "60" in text and ("day" in text or "late" in text):
        return "late_payment_60"
    elif "30" in text and ("day" in text or "late" in text):
        return "late_payment_30"
    elif "late" in text or "delinquen" in text:
        return "late_payment_30"
    elif "judgment" in text or "court" in text:
        return "judgment"
    elif "tax" in text and "lien" in text:
        return "tax_lien"
    elif "identity theft" in text or "fraud" in text:
        return "identity_theft"
    elif "multiple" in text and "inquir" in text:
        return "multiple_inquiries"
    elif "hard" in text and "inquir" in text:
        return "hard_inquiry"
    elif "inquiry" in text or "inquir" in text:
        return "inquiry"
    elif "maxed" in text or "max" in text:
        return "maxed_out"
    elif "over" in text and "limit" in text:
        return "over_limit"
    elif "utilization" in text or ("high" in text and "balance" in text):
        return "high_utilization"
    elif "reaged" in text or "re-aged" in text:
        return "reaged_debt"
    elif "obsolete" in text or ("7 year" in text or "seven year" in text):
        return "obsolete_info"
    elif "mixed" in text and "file" in text:
        return "mixed_file"
    elif "duplicate" in text:
        return "duplicate_account"
    elif "wrong" in text and "date" in text:
        return "wrong_date"
    elif "wrong" in text and "balance" in text:
        return "wrong_balance"
    elif "wrong" in text and "status" in text:
        return "wrong_status"
    elif "authorized user" in text:
        return "authorized_user_negative"
    elif "closed" in text and ("creditor" in text or "negative" in text):
        return "closed_negative"
    elif "identity" in text or (
        "wrong" in text and ("name" in text or "ssn" in text or "address" in text)
    ):
        return "identity_error"
    elif "inaccurate" in text or "error" in text or "wrong" in text:
        return "inaccurate_info"
    else:
        return "unknown"


def get_all_item_types():
    """Return all negative item types with their impact data for the UI"""
    items_by_category = {}
    for type_key, type_data in SCORE_IMPACT_BY_TYPE.items():
        category = type_data.get("category", "other")
        if category not in items_by_category:
            cat_info = ITEM_CATEGORIES.get(
                category, {"label": "Other", "color": "#6b7280"}
            )
            items_by_category[category] = {
                "label": cat_info["label"],
                "color": cat_info["color"],
                "items": [],
            }
        items_by_category[category]["items"].append(
            {
                "key": type_key,
                "label": type_data.get("label", type_key.replace("_", " ").title()),
                "description": type_data.get("description", ""),
                "impact": {
                    "min": type_data["min"],
                    "max": type_data["max"],
                    "avg": type_data["avg"],
                },
                "severity": type_data.get("severity", "moderate"),
                "severity_color": SEVERITY_LEVELS.get(
                    type_data.get("severity", "moderate"), {}
                ).get("color", "#eab308"),
            }
        )

    for cat in items_by_category.values():
        cat["items"].sort(key=lambda x: x["impact"]["avg"], reverse=True)

    return items_by_category


def estimate_by_item_types(current_score, selected_items):
    """
    Estimate score improvement based on specific item types selected.

    Args:
        current_score: Current credit score
        selected_items: List of dicts with 'type' and 'count' keys

    Returns:
        Detailed projection with per-item breakdown
    """
    if not current_score:
        current_score = 550

    total_min = 0
    total_max = 0
    total_avg = 0
    item_breakdown = []
    total_count = 0

    for item in selected_items:
        item_type = item.get("type", "unknown")
        count = item.get("count", 1)
        total_count += count

        impact = SCORE_IMPACT_BY_TYPE.get(item_type, SCORE_IMPACT_BY_TYPE["unknown"])
        item_min = impact["min"] * count
        item_max = impact["max"] * count
        item_avg = impact["avg"] * count

        total_min += item_min
        total_max += item_max
        total_avg += item_avg

        item_breakdown.append(
            {
                "type": item_type,
                "label": impact.get("label", item_type.replace("_", " ").title()),
                "count": count,
                "impact": {
                    "min": item_min,
                    "max": item_max,
                    "avg": item_avg,
                    "per_item": impact["avg"],
                },
                "severity": impact.get("severity", "moderate"),
                "category": impact.get("category", "other"),
            }
        )

    diminishing_factor = max(0.5, 1 - (total_count * 0.02))
    total_min = int(total_min * diminishing_factor)
    total_max = int(total_max * diminishing_factor)
    total_avg = int(total_avg * diminishing_factor)

    projected_min = min(850, current_score + total_min)
    projected_max = min(850, current_score + total_max)
    projected_avg = min(850, current_score + total_avg)

    item_breakdown.sort(key=lambda x: x["impact"]["avg"], reverse=True)

    return {
        "current_score": current_score,
        "current_range": get_score_range_label(current_score),
        "total_items": total_count,
        "improvement": {
            "min": total_min,
            "max": total_max,
            "avg": total_avg,
        },
        "projected": {
            "min": projected_min,
            "max": projected_max,
            "avg": projected_avg,
        },
        "projected_range": get_score_range_label(projected_avg),
        "item_breakdown": item_breakdown,
        "diminishing_factor": round(diminishing_factor, 2),
        "confidence": "high",
    }


def estimate_score_improvement(current_score, negatives_to_remove, negative_types=None):
    """
    Estimate potential score improvement based on negative items to be removed.

    Args:
        current_score: Current credit score
        negatives_to_remove: Number of negative items to remove
        negative_types: Optional list of negative item types for more accurate estimate

    Returns:
        dict with min, max, avg projected scores and improvement
    """
    if not current_score:
        current_score = 550

    if not negative_types:
        points_per_negative = 20
        total_min = negatives_to_remove * 10
        total_max = negatives_to_remove * 35
        total_avg = negatives_to_remove * points_per_negative
    else:
        total_min = 0
        total_max = 0
        total_avg = 0
        for neg_type in negative_types:
            impact = SCORE_IMPACT_BY_TYPE.get(neg_type, SCORE_IMPACT_BY_TYPE["unknown"])
            total_min += impact["min"]
            total_max += impact["max"]
            total_avg += impact["avg"]

    diminishing_factor = max(0.5, 1 - (negatives_to_remove * 0.03))
    total_min = int(total_min * diminishing_factor)
    total_max = int(total_max * diminishing_factor)
    total_avg = int(total_avg * diminishing_factor)

    projected_min = min(850, current_score + total_min)
    projected_max = min(850, current_score + total_max)
    projected_avg = min(850, current_score + total_avg)

    return {
        "current_score": current_score,
        "current_range": get_score_range_label(current_score),
        "negatives_to_remove": negatives_to_remove,
        "improvement": {
            "min": total_min,
            "max": total_max,
            "avg": total_avg,
        },
        "projected": {
            "min": projected_min,
            "max": projected_max,
            "avg": projected_avg,
        },
        "projected_range": get_score_range_label(projected_avg),
        "confidence": "high" if negative_types else "medium",
    }


def calculate_client_projection(client_id):
    """
    Calculate comprehensive score projection for a client based on their violations.
    """
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return None

        analyses = db.query(Analysis).filter_by(client_id=client_id).all()
        analysis_ids = [a.id for a in analyses]
        violations = (
            db.query(Violation).filter(Violation.analysis_id.in_(analysis_ids)).all()
            if analysis_ids
            else []
        )

        snapshots = (
            db.query(CreditScoreSnapshot)
            .filter_by(client_id=client_id)
            .order_by(CreditScoreSnapshot.created_at.desc())
            .all()
        )

        if snapshots:
            latest = snapshots[0]
            current_eq = latest.equifax_score
            current_ex = latest.experian_score
            current_tu = latest.transunion_score
            current_avg = latest.average_score
            current_negatives = latest.total_negatives
        else:
            current_eq = None
            current_ex = None
            current_tu = None
            current_avg = 550
            current_negatives = len(violations)

        negative_types = []
        for v in violations:
            neg_type = categorize_violation_type(
                v.violation_type or v.description or ""
            )
            negative_types.append(neg_type)

        projection = estimate_score_improvement(
            current_avg or 550, len(violations), negative_types
        )

        starting_score = None
        starting_negatives = 0
        if len(snapshots) > 1:
            oldest = snapshots[-1]
            starting_score = oldest.average_score
            starting_negatives = oldest.total_negatives
        elif len(snapshots) == 1:
            starting_score = snapshots[0].average_score
            starting_negatives = snapshots[0].total_negatives

        total_removed = 0
        if snapshots:
            total_removed = snapshots[0].total_removed or 0

        score_gained = 0
        if starting_score and current_avg:
            score_gained = current_avg - starting_score

        return {
            "client_id": client_id,
            "client_name": client.name,
            "scores": {
                "starting": {
                    "average": starting_score,
                    "range": get_score_range_label(starting_score),
                },
                "current": {
                    "equifax": current_eq,
                    "experian": current_ex,
                    "transunion": current_tu,
                    "average": current_avg,
                    "range": get_score_range_label(current_avg),
                },
                "projected": {
                    "min": projection["projected"]["min"],
                    "max": projection["projected"]["max"],
                    "avg": projection["projected"]["avg"],
                    "range": projection["projected_range"],
                },
            },
            "negatives": {
                "starting": starting_negatives,
                "current": current_negatives,
                "removed": total_removed,
                "remaining": max(0, current_negatives - total_removed),
            },
            "improvement": {
                "points_gained": score_gained,
                "potential_min": projection["improvement"]["min"],
                "potential_max": projection["improvement"]["max"],
                "potential_avg": projection["improvement"]["avg"],
            },
            "progress_percentage": round(
                (
                    (total_removed / starting_negatives * 100)
                    if starting_negatives > 0
                    else 0
                ),
                1,
            ),
            "violation_breakdown": get_violation_breakdown(violations),
            "timeline": get_score_timeline(client_id),
            "confidence": projection["confidence"],
        }
    finally:
        db.close()


def get_violation_breakdown(violations):
    """Break down violations by type for the calculator"""
    breakdown = {}
    for v in violations:
        neg_type = categorize_violation_type(
            v.violation_type or getattr(v, "description", "") or ""
        )
        if neg_type not in breakdown:
            breakdown[neg_type] = {
                "count": 0,
                "impact": SCORE_IMPACT_BY_TYPE.get(
                    neg_type, SCORE_IMPACT_BY_TYPE["unknown"]
                ),
                "label": neg_type.replace("_", " ").title(),
            }
        breakdown[neg_type]["count"] += 1
    return breakdown


def get_score_timeline(client_id):
    """Get score history timeline for charts"""
    db = get_db()
    try:
        snapshots = (
            db.query(CreditScoreSnapshot)
            .filter_by(client_id=client_id)
            .order_by(CreditScoreSnapshot.created_at.asc())
            .all()
        )

        timeline = []
        for s in snapshots:
            timeline.append(
                {
                    "date": s.created_at.isoformat() if s.created_at else None,
                    "equifax": s.equifax_score,
                    "experian": s.experian_score,
                    "transunion": s.transunion_score,
                    "average": s.average_score,
                    "negatives": s.total_negatives,
                    "removed": s.total_removed,
                    "milestone": s.milestone,
                    "round": s.dispute_round,
                }
            )

        return timeline
    finally:
        db.close()


def add_score_snapshot(
    client_id,
    equifax=None,
    experian=None,
    transunion=None,
    negatives=0,
    removed=0,
    milestone=None,
    dispute_round=0,
    snapshot_type="manual",
    source=None,
    notes=None,
):
    """Add a new credit score snapshot for a client"""
    db = get_db()
    try:
        scores = [s for s in [equifax, experian, transunion] if s is not None]
        average = round(sum(scores) / len(scores)) if scores else None

        snapshot = CreditScoreSnapshot(
            client_id=client_id,
            equifax_score=equifax,
            experian_score=experian,
            transunion_score=transunion,
            average_score=average,
            total_negatives=negatives,
            total_removed=removed,
            milestone=milestone,
            dispute_round=dispute_round,
            snapshot_type=snapshot_type,
            source=source,
            notes=notes,
        )

        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return {
            "success": True,
            "snapshot_id": snapshot.id,
            "average_score": average,
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_improvement_summary(client_id):
    """Get a quick summary of client's credit improvement journey"""
    db = get_db()
    try:
        snapshots = (
            db.query(CreditScoreSnapshot)
            .filter_by(client_id=client_id)
            .order_by(CreditScoreSnapshot.created_at.asc())
            .all()
        )

        if not snapshots:
            return {
                "has_data": False,
                "message": "No credit score data recorded yet",
            }

        first = snapshots[0]
        latest = snapshots[-1]

        starting_avg = first.average_score or 0
        current_avg = latest.average_score or 0
        points_gained = current_avg - starting_avg

        starting_negatives = first.total_negatives or 0
        current_negatives = latest.total_negatives or 0
        items_removed = latest.total_removed or 0

        return {
            "has_data": True,
            "starting_score": starting_avg,
            "starting_range": get_score_range_label(starting_avg),
            "current_score": current_avg,
            "current_range": get_score_range_label(current_avg),
            "points_gained": points_gained,
            "points_gained_text": (
                f"+{points_gained}" if points_gained > 0 else str(points_gained)
            ),
            "starting_negatives": starting_negatives,
            "current_negatives": current_negatives,
            "items_removed": items_removed,
            "removal_percentage": round(
                (
                    (items_removed / starting_negatives * 100)
                    if starting_negatives > 0
                    else 0
                ),
                1,
            ),
            "snapshots_count": len(snapshots),
            "first_snapshot_date": (
                first.created_at.isoformat() if first.created_at else None
            ),
            "latest_snapshot_date": (
                latest.created_at.isoformat() if latest.created_at else None
            ),
            "current_round": latest.dispute_round or 0,
        }
    finally:
        db.close()


def quick_estimate(current_score, num_negatives):
    """Quick estimate without detailed violation types"""
    return estimate_score_improvement(current_score, num_negatives)
