"""
Pattern Analyzer Service for FCRA Litigation Platform.
Identifies patterns in furnisher behavior, seasonal trends, and winning strategies.
"""

import json
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

from sqlalchemy import and_, extract, func

from database import (
    CaseOutcome,
    Client,
    Furnisher,
    FurnisherPattern,
    FurnisherStats,
    SessionLocal,
    Staff,
    Violation,
)


class PatternAnalyzerService:
    """Service for analyzing patterns in FCRA case data"""

    PATTERN_TYPES = [
        "response_behavior",
        "settlement_tendency",
        "verification_pattern",
        "seasonal_trend",
        "violation_correlation",
        "attorney_performance",
    ]

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=30)

    def _get_cache(self, key: str) -> Optional[Any]:
        if key in self._cache and datetime.utcnow() < self._cache_expiry.get(
            key, datetime.min
        ):
            return self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._cache_expiry[key] = datetime.utcnow() + self._cache_duration

    def analyze_furnisher_behavior(
        self, furnisher_id: Optional[int] = None, furnisher_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a furnisher's response patterns and tendencies.

        Returns patterns like:
        - Response time patterns
        - Settlement tendencies
        - Verification vs deletion rates
        - Reinsertion frequency
        """
        db = SessionLocal()
        try:
            query = db.query(CaseOutcome)

            if furnisher_id:
                query = query.filter(CaseOutcome.furnisher_id == furnisher_id)
                furnisher = (
                    db.query(Furnisher).filter(Furnisher.id == furnisher_id).first()
                )
                fname = furnisher.name if furnisher else f"Furnisher #{furnisher_id}"
            elif furnisher_name:
                furnisher = (
                    db.query(Furnisher)
                    .filter(Furnisher.name.ilike(f"%{furnisher_name}%"))
                    .first()
                )
                if furnisher:
                    query = query.filter(CaseOutcome.furnisher_id == furnisher.id)
                    furnisher_id = int(furnisher.id)  # type: ignore[arg-type]
                    fname = str(furnisher.name)
                else:
                    fname = furnisher_name
            else:
                return {"error": "Must provide furnisher_id or furnisher_name"}

            outcomes = query.all()

            if not outcomes:
                return {
                    "furnisher_id": furnisher_id,
                    "furnisher_name": fname,
                    "sample_size": 0,
                    "patterns": [],
                    "insights": "No historical data available for this furnisher",
                }

            total = len(outcomes)
            settled = sum(1 for o in outcomes if o.final_outcome == "settled")
            won = sum(1 for o in outcomes if o.final_outcome == "won")
            lost = sum(1 for o in outcomes if o.final_outcome == "lost")

            settlement_amounts = [
                o.settlement_amount for o in outcomes if o.settlement_amount > 0
            ]
            avg_settlement = (
                sum(settlement_amounts) / len(settlement_amounts)
                if settlement_amounts
                else 0
            )

            resolution_times = [
                o.time_to_resolution_days
                for o in outcomes
                if o.time_to_resolution_days > 0
            ]
            avg_resolution = (
                sum(resolution_times) / len(resolution_times) if resolution_times else 0
            )

            patterns: List[Dict[str, Any]] = []
            insights: List[str] = []

            settlement_rate = (settled + won) / total
            if settlement_rate >= 0.7:
                patterns.append(
                    {
                        "type": "high_settlement_tendency",
                        "value": round(settlement_rate, 3),
                        "description": "This furnisher tends to settle cases frequently",
                    }
                )
                insights.append(
                    f"High settlement rate ({round(settlement_rate * 100)}%). Consider aggressive initial demands."
                )
            elif settlement_rate <= 0.3:
                patterns.append(
                    {
                        "type": "low_settlement_tendency",
                        "value": round(settlement_rate, 3),
                        "description": "This furnisher rarely settles - prepare for litigation",
                    }
                )
                insights.append(
                    "Low settlement rate. Prepare comprehensive litigation documentation."
                )

            if avg_resolution > 0:
                if avg_resolution < 45:
                    patterns.append(
                        {
                            "type": "fast_resolution",
                            "value": round(avg_resolution),
                            "description": "Cases resolve quickly with this furnisher",
                        }
                    )
                    insights.append(
                        f"Fast resolution time ({round(avg_resolution)} days avg). Quick action recommended."
                    )
                elif avg_resolution > 120:
                    patterns.append(
                        {
                            "type": "slow_resolution",
                            "value": round(avg_resolution),
                            "description": "Cases take longer to resolve with this furnisher",
                        }
                    )
                    insights.append(
                        f"Slow resolution ({round(avg_resolution)} days avg). Prepare for extended timeline."
                    )

            if avg_settlement > 0:
                patterns.append(
                    {
                        "type": "settlement_amount_pattern",
                        "value": round(avg_settlement, 2),
                        "min": min(settlement_amounts) if settlement_amounts else 0,
                        "max": max(settlement_amounts) if settlement_amounts else 0,
                        "description": f"Average settlement: ${avg_settlement:,.2f}",
                    }
                )

            violation_success: Dict[str, Dict[str, int]] = {}
            for outcome in outcomes:
                violation_types_list = (
                    outcome.violation_types if outcome.violation_types else []
                )
                for vtype in violation_types_list:
                    if vtype not in violation_success:
                        violation_success[vtype] = {"total": 0, "success": 0}
                    violation_success[vtype]["total"] += 1
                    if outcome.final_outcome in ["won", "settled"]:
                        violation_success[vtype]["success"] += 1

            best_violation: Optional[str] = None
            best_rate: float = 0
            for vtype, data in violation_success.items():
                if data["total"] >= 3:
                    rate = data["success"] / data["total"]
                    if rate > best_rate:
                        best_rate = rate
                        best_violation = vtype

            if best_violation:
                patterns.append(
                    {
                        "type": "most_effective_violation",
                        "value": best_violation,
                        "success_rate": round(best_rate, 3),
                        "description": f"{best_violation} has highest success rate against this furnisher",
                    }
                )
                insights.append(
                    f"Focus on {best_violation} violations - highest success rate ({round(best_rate * 100)}%)."
                )

            self._save_pattern(
                db,
                furnisher_id,
                str(fname),
                "response_behavior",
                {
                    "settlement_rate": round(settlement_rate, 3),
                    "avg_settlement": round(avg_settlement, 2),
                    "avg_resolution_days": round(avg_resolution),
                    "best_violation_type": best_violation,
                },
                total,
                min(0.9, total / 20),
            )

            confidence = min(0.9, total / 20)

            return {
                "furnisher_id": furnisher_id,
                "furnisher_name": fname,
                "sample_size": total,
                "statistics": {
                    "total_cases": total,
                    "settled": settled,
                    "won": won,
                    "lost": lost,
                    "settlement_rate": round(settlement_rate, 3),
                    "avg_settlement": round(avg_settlement, 2),
                    "avg_resolution_days": round(avg_resolution),
                },
                "patterns": patterns,
                "insights": insights,
                "confidence": round(confidence, 3),
                "recommendation": (
                    insights[0]
                    if insights
                    else "Continue gathering data for this furnisher."
                ),
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def _save_pattern(
        self,
        db: Any,
        furnisher_id: Optional[int],
        furnisher_name: str,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        sample_size: int,
        confidence: float,
    ) -> None:
        """Save or update a pattern record"""
        try:
            existing = (
                db.query(FurnisherPattern)
                .filter(
                    FurnisherPattern.furnisher_id == furnisher_id,
                    FurnisherPattern.pattern_type == pattern_type,
                )
                .first()
            )

            if existing:
                existing.pattern_data = pattern_data
                existing.sample_size = sample_size
                existing.confidence = confidence
                existing.last_updated = datetime.utcnow()
            else:
                pattern = FurnisherPattern(
                    furnisher_id=furnisher_id,
                    furnisher_name=furnisher_name,
                    pattern_type=pattern_type,
                    pattern_data=pattern_data,
                    sample_size=sample_size,
                    confidence=confidence,
                )
                db.add(pattern)

            db.commit()
        except Exception as e:
            db.rollback()

    def detect_seasonal_trends(self) -> Dict[str, Any]:
        """
        Identify seasonal patterns in case outcomes and settlements.

        Analyzes:
        - Monthly settlement rates
        - Quarterly outcome patterns
        - Best/worst months for filing
        """
        cache_key = "seasonal_trends"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        db = SessionLocal()
        try:
            outcomes = db.query(CaseOutcome).all()

            if len(outcomes) < 12:
                return {
                    "message": "Need at least 12 cases for seasonal analysis",
                    "sample_size": len(outcomes),
                    "trends": [],
                    "recommendations": [],
                }

            monthly_data: Dict[int, Dict[str, Any]] = {}
            for month in range(1, 13):
                monthly_data[month] = {
                    "total": 0,
                    "success": 0,
                    "settlements": cast(List[float], []),
                    "resolution_days": cast(List[int], []),
                }

            for outcome in outcomes:
                if outcome.created_at:
                    month = outcome.created_at.month
                    mdata = monthly_data[month]
                    mdata["total"] = cast(int, mdata["total"]) + 1
                    if outcome.final_outcome in ["won", "settled"]:
                        mdata["success"] = cast(int, mdata["success"]) + 1
                    settlement_amt = (
                        float(outcome.settlement_amount)
                        if outcome.settlement_amount
                        else 0
                    )
                    if settlement_amt > 0:
                        cast(List[float], mdata["settlements"]).append(settlement_amt)
                    resolution_days = (
                        int(outcome.time_to_resolution_days)
                        if outcome.time_to_resolution_days
                        else 0
                    )
                    if resolution_days > 0:
                        cast(List[int], mdata["resolution_days"]).append(
                            resolution_days
                        )

            monthly_stats: Dict[int, Dict[str, Any]] = {}
            for month, data in monthly_data.items():
                total = cast(int, data["total"])
                if total > 0:
                    success = cast(int, data["success"])
                    settlements = cast(List[float], data["settlements"])
                    resolution_days_list = cast(List[int], data["resolution_days"])
                    monthly_stats[month] = {
                        "cases": total,
                        "success_rate": round(success / total, 3),
                        "avg_settlement": (
                            round(sum(settlements) / len(settlements), 2)
                            if settlements
                            else 0
                        ),
                        "avg_resolution": (
                            round(sum(resolution_days_list) / len(resolution_days_list))
                            if resolution_days_list
                            else 0
                        ),
                    }

            month_names = [
                "",
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]

            trends: List[Dict[str, Any]] = []
            recommendations: List[str] = []

            best_month: Optional[int] = max(
                monthly_stats.keys(),
                key=lambda m: cast(float, monthly_stats[m]["success_rate"]),
                default=None,
            )
            worst_month: Optional[int] = min(
                monthly_stats.keys(),
                key=lambda m: cast(float, monthly_stats[m]["success_rate"]),
                default=None,
            )

            if best_month and monthly_stats[best_month]["success_rate"] > 0.6:
                trends.append(
                    {
                        "type": "best_month",
                        "month": best_month,
                        "month_name": month_names[best_month],
                        "success_rate": monthly_stats[best_month]["success_rate"],
                        "description": f"{month_names[best_month]} has highest success rate",
                    }
                )
                recommendations.append(
                    f"Consider timing filings around {month_names[best_month]} for better outcomes."
                )

            if worst_month and monthly_stats[worst_month]["success_rate"] < 0.4:
                trends.append(
                    {
                        "type": "worst_month",
                        "month": worst_month,
                        "month_name": month_names[worst_month],
                        "success_rate": monthly_stats[worst_month]["success_rate"],
                        "description": f"{month_names[worst_month]} has lowest success rate",
                    }
                )
                recommendations.append(
                    f"Avoid major filings in {month_names[worst_month]} if possible."
                )

            q1: List[Dict[str, Any]] = [monthly_stats.get(m, {}) for m in [1, 2, 3]]
            q2: List[Dict[str, Any]] = [monthly_stats.get(m, {}) for m in [4, 5, 6]]
            q3: List[Dict[str, Any]] = [monthly_stats.get(m, {}) for m in [7, 8, 9]]
            q4: List[Dict[str, Any]] = [monthly_stats.get(m, {}) for m in [10, 11, 12]]

            def quarter_avg(qdata: List[Dict[str, Any]]) -> float:
                rates: List[float] = [d.get("success_rate", 0) for d in qdata if d]
                return sum(rates) / len(rates) if rates else 0

            quarterly: Dict[str, float] = {
                "Q1": round(quarter_avg(q1), 3),
                "Q2": round(quarter_avg(q2), 3),
                "Q3": round(quarter_avg(q3), 3),
                "Q4": round(quarter_avg(q4), 3),
            }

            best_quarter = max(quarterly.keys(), key=lambda q: quarterly[q])
            if quarterly[best_quarter] > 0.5:
                trends.append(
                    {
                        "type": "best_quarter",
                        "quarter": best_quarter,
                        "success_rate": quarterly[best_quarter],
                        "description": f"{best_quarter} shows strongest outcomes",
                    }
                )

            result = {
                "sample_size": len(outcomes),
                "monthly_stats": monthly_stats,
                "quarterly_summary": quarterly,
                "trends": trends,
                "recommendations": recommendations,
                "confidence": min(0.9, len(outcomes) / 100),
            }

            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def identify_winning_strategies(
        self, violation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identify strategies that lead to successful outcomes.

        Analyzes:
        - Violation type effectiveness
        - Documentation quality impact
        - Round completion patterns
        - Attorney involvement effects
        """
        db = SessionLocal()
        try:
            query = db.query(CaseOutcome)

            if violation_type:
                pass

            outcomes = query.all()

            if len(outcomes) < 5:
                return {
                    "message": "Need more case data for strategy analysis",
                    "sample_size": len(outcomes),
                    "strategies": [],
                }

            successful = [o for o in outcomes if o.final_outcome in ["won", "settled"]]
            unsuccessful = [
                o for o in outcomes if o.final_outcome in ["lost", "dismissed"]
            ]

            strategies: List[Dict[str, Any]] = []

            success_by_violation: Dict[str, Dict[str, Any]] = {}
            for outcome in outcomes:
                violation_types_list = (
                    outcome.violation_types if outcome.violation_types else []
                )
                for vtype in violation_types_list:
                    if vtype not in success_by_violation:
                        success_by_violation[vtype] = {
                            "success": 0,
                            "total": 0,
                            "settlements": cast(List[float], []),
                        }
                    vdata = success_by_violation[vtype]
                    vdata["total"] = cast(int, vdata["total"]) + 1
                    if outcome.final_outcome in ["won", "settled"]:
                        vdata["success"] = cast(int, vdata["success"]) + 1
                        settlement_amt = (
                            float(outcome.settlement_amount)
                            if outcome.settlement_amount
                            else 0
                        )
                        if settlement_amt > 0:
                            cast(List[float], vdata["settlements"]).append(
                                settlement_amt
                            )

            for vtype, data in success_by_violation.items():
                total = cast(int, data["total"])
                if total >= 3:
                    success = cast(int, data["success"])
                    settlements = cast(List[float], data["settlements"])
                    rate = success / total
                    avg_settlement = (
                        sum(settlements) / len(settlements) if settlements else 0
                    )
                    strategies.append(
                        {
                            "type": "violation_effectiveness",
                            "violation_type": vtype,
                            "success_rate": round(rate, 3),
                            "sample_size": data["total"],
                            "avg_settlement": round(avg_settlement, 2),
                            "recommendation": f"Include {vtype} claims when applicable (success rate: {round(rate*100)}%)",
                        }
                    )

            strategies.sort(key=lambda x: x.get("success_rate", 0), reverse=True)

            high_doc = [o for o in successful if (o.documentation_quality or 0) >= 0.7]
            low_doc = [o for o in unsuccessful if (o.documentation_quality or 0) < 0.5]

            if high_doc:
                high_doc_settlements = [
                    o.settlement_amount for o in high_doc if o.settlement_amount > 0
                ]
                if high_doc_settlements:
                    strategies.append(
                        {
                            "type": "documentation_impact",
                            "finding": "Strong documentation correlates with higher settlements",
                            "avg_settlement_high_doc": round(
                                sum(high_doc_settlements) / len(high_doc_settlements), 2
                            ),
                            "recommendation": "Prioritize thorough documentation and evidence collection",
                        }
                    )

            with_attorney = [o for o in outcomes if o.attorney_id is not None]
            without_attorney = [o for o in outcomes if o.attorney_id is None]

            if with_attorney and without_attorney:
                with_rate = sum(
                    1 for o in with_attorney if o.final_outcome in ["won", "settled"]
                ) / len(with_attorney)
                without_rate = sum(
                    1 for o in without_attorney if o.final_outcome in ["won", "settled"]
                ) / len(without_attorney)

                if with_rate > without_rate + 0.1:
                    strategies.append(
                        {
                            "type": "attorney_involvement",
                            "with_attorney_rate": round(with_rate, 3),
                            "without_attorney_rate": round(without_rate, 3),
                            "recommendation": "Attorney involvement increases success rate by "
                            + f"{round((with_rate - without_rate) * 100)}%",
                        }
                    )

            rounds_data: Dict[int, Dict[str, Any]] = {}
            for outcome in successful:
                rounds = int(outcome.dispute_rounds_completed or 0)
                if rounds not in rounds_data:
                    rounds_data[rounds] = {
                        "count": 0,
                        "settlements": cast(List[float], []),
                    }
                rdata = rounds_data[rounds]
                rdata["count"] = cast(int, rdata["count"]) + 1
                settlement_amt = (
                    float(outcome.settlement_amount) if outcome.settlement_amount else 0
                )
                if settlement_amt > 0:
                    cast(List[float], rdata["settlements"]).append(settlement_amt)

            if rounds_data:
                best_round = max(
                    rounds_data.keys(),
                    key=lambda r: (
                        sum(cast(List[float], rounds_data[r]["settlements"]))
                        / max(len(cast(List[float], rounds_data[r]["settlements"])), 1)
                        if rounds_data[r]["settlements"]
                        else 0
                    ),
                )
                best_round_settlements = cast(
                    List[float], rounds_data[best_round]["settlements"]
                )
                if best_round_settlements:
                    strategies.append(
                        {
                            "type": "optimal_rounds",
                            "best_round": best_round,
                            "avg_settlement": round(
                                sum(best_round_settlements)
                                / len(best_round_settlements),
                                2,
                            ),
                            "recommendation": f"Round {best_round} disputes show highest average settlements",
                        }
                    )

            return {
                "sample_size": len(outcomes),
                "successful_cases": len(successful),
                "strategies": strategies[:10],
                "top_violation_types": [
                    s for s in strategies if s["type"] == "violation_effectiveness"
                ][:5],
                "confidence": min(0.9, len(outcomes) / 50),
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def find_attorney_strengths(self) -> Dict[str, Any]:
        """
        Analyze which attorneys excel in different areas.

        Returns:
        - Success rates by attorney
        - Specialization patterns
        - Settlement performance
        """
        db = SessionLocal()
        try:
            outcomes = (
                db.query(CaseOutcome).filter(CaseOutcome.attorney_id.isnot(None)).all()
            )

            if len(outcomes) < 5:
                return {
                    "message": "Need more attorney-linked cases for analysis",
                    "sample_size": len(outcomes),
                    "attorneys": [],
                }

            attorney_data: Dict[Any, Dict[str, Any]] = {}
            for outcome in outcomes:
                aid = outcome.attorney_id
                if aid not in attorney_data:
                    attorney_data[aid] = {
                        "total": 0,
                        "success": 0,
                        "settlements": cast(List[float], []),
                        "violation_types": cast(Dict[str, Dict[str, int]], {}),
                        "resolution_times": cast(List[int], []),
                    }

                adata = attorney_data[aid]
                adata["total"] = cast(int, adata["total"]) + 1

                if outcome.final_outcome in ["won", "settled"]:
                    adata["success"] = cast(int, adata["success"]) + 1

                settlement_amt = (
                    float(outcome.settlement_amount) if outcome.settlement_amount else 0
                )
                if settlement_amt > 0:
                    cast(List[float], adata["settlements"]).append(settlement_amt)

                resolution_days = (
                    int(outcome.time_to_resolution_days)
                    if outcome.time_to_resolution_days
                    else 0
                )
                if resolution_days > 0:
                    cast(List[int], adata["resolution_times"]).append(resolution_days)

                violation_types = cast(
                    Dict[str, Dict[str, int]], adata["violation_types"]
                )
                violation_types_list = (
                    outcome.violation_types if outcome.violation_types else []
                )
                for vtype in violation_types_list:
                    if vtype not in violation_types:
                        violation_types[vtype] = {"total": 0, "success": 0}
                    violation_types[vtype]["total"] += 1
                    if outcome.final_outcome in ["won", "settled"]:
                        violation_types[vtype]["success"] += 1

            attorneys: List[Dict[str, Any]] = []
            for aid, data in attorney_data.items():
                staff = db.query(Staff).filter(Staff.id == aid).first()
                attorney_name = staff.full_name if staff else f"Attorney #{aid}"

                total = cast(int, data["total"])
                success = cast(int, data["success"])
                settlements = cast(List[float], data["settlements"])
                resolution_times = cast(List[int], data["resolution_times"])
                violation_types = cast(
                    Dict[str, Dict[str, int]], data["violation_types"]
                )

                success_rate = success / max(total, 1)
                avg_settlement = (
                    sum(settlements) / len(settlements) if settlements else 0
                )
                avg_resolution = (
                    sum(resolution_times) / len(resolution_times)
                    if resolution_times
                    else 0
                )

                best_violation: Optional[str] = None
                best_rate: float = 0
                for vtype, vdata in violation_types.items():
                    if vdata["total"] >= 2:
                        rate = vdata["success"] / vdata["total"]
                        if rate > best_rate:
                            best_rate = rate
                            best_violation = vtype

                attorneys.append(
                    {
                        "attorney_id": aid,
                        "name": attorney_name,
                        "total_cases": total,
                        "success_rate": round(success_rate, 3),
                        "avg_settlement": round(avg_settlement, 2),
                        "avg_resolution_days": round(avg_resolution),
                        "specialization": best_violation,
                        "specialization_success_rate": (
                            round(best_rate, 3) if best_violation else None
                        ),
                        "strengths": self._identify_attorney_strengths(
                            data, success_rate, avg_settlement
                        ),
                    }
                )

            attorneys.sort(key=lambda x: x["success_rate"], reverse=True)

            return {
                "sample_size": len(outcomes),
                "attorneys": attorneys,
                "top_performer": attorneys[0] if attorneys else None,
                "insights": self._generate_attorney_insights(attorneys),
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def _identify_attorney_strengths(
        self, data: Dict[str, Any], success_rate: float, avg_settlement: float
    ) -> List[str]:
        """Identify specific strengths for an attorney"""
        strengths: List[str] = []

        if success_rate >= 0.8:
            strengths.append("High overall success rate")
        elif success_rate >= 0.6:
            strengths.append("Good success rate")

        if avg_settlement >= 10000:
            strengths.append("Strong settlement negotiator")

        resolution_times = cast(List[int], data.get("resolution_times", []))
        if resolution_times and sum(resolution_times) / len(resolution_times) < 60:
            strengths.append("Fast case resolution")

        violation_types = cast(
            Dict[str, Dict[str, int]], data.get("violation_types", {})
        )
        for vtype, vdata in violation_types.items():
            if vdata["total"] >= 3:
                rate = vdata["success"] / vdata["total"]
                if rate >= 0.9:
                    strengths.append(f"Expert in {vtype} cases")

        return strengths[:3]

    def _generate_attorney_insights(self, attorneys: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from attorney data"""
        insights: List[str] = []

        if not attorneys:
            return insights

        if len(attorneys) >= 2:
            top = attorneys[0]
            insights.append(
                f"{top['name']} has the highest success rate at {round(top['success_rate'] * 100)}%"
            )

        high_settlers = [a for a in attorneys if a["avg_settlement"] >= 5000]
        if high_settlers:
            best_settler = max(high_settlers, key=lambda x: x["avg_settlement"])
            insights.append(
                f"{best_settler['name']} achieves highest average settlements (${best_settler['avg_settlement']:,.2f})"
            )

        specialists = [a for a in attorneys if a.get("specialization")]
        for spec in specialists[:2]:
            insights.append(
                f"{spec['name']} specializes in {spec['specialization']} cases ({round(spec['specialization_success_rate'] * 100)}% success)"
            )

        return insights

    def get_pattern_insights(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get actionable insights based on identified patterns.

        Args:
            filters: Optional dict with furnisher_id, violation_type, date_range

        Returns:
            Dict with categorized insights and recommendations
        """
        db = SessionLocal()
        try:
            patterns = (
                db.query(FurnisherPattern)
                .order_by(FurnisherPattern.confidence.desc())
                .limit(50)
                .all()
            )

            filters = filters or {}

            if filters.get("furnisher_id"):
                patterns = [
                    p for p in patterns if p.furnisher_id == filters["furnisher_id"]
                ]

            if filters.get("pattern_type"):
                patterns = [
                    p for p in patterns if p.pattern_type == filters["pattern_type"]
                ]

            seasonal = self.detect_seasonal_trends()
            strategies = self.identify_winning_strategies(filters.get("violation_type"))

            categorized_insights: Dict[str, List[Any]] = {
                "furnisher_patterns": [],
                "seasonal_insights": [],
                "strategy_insights": [],
                "high_confidence": [],
                "actionable_recommendations": [],
            }

            for pattern in patterns:
                insight = {
                    "id": pattern.id,
                    "furnisher": pattern.furnisher_name,
                    "type": pattern.pattern_type,
                    "data": pattern.pattern_data,
                    "confidence": pattern.confidence,
                    "sample_size": pattern.sample_size,
                    "last_updated": (
                        pattern.last_updated.isoformat()
                        if pattern.last_updated
                        else None
                    ),
                }

                categorized_insights["furnisher_patterns"].append(insight)

                if pattern.confidence >= 0.7:
                    categorized_insights["high_confidence"].append(insight)

            if seasonal.get("trends"):
                categorized_insights["seasonal_insights"] = seasonal["trends"]

            if strategies.get("strategies"):
                categorized_insights["strategy_insights"] = strategies["strategies"][:5]

            recommendations: List[Dict[str, Any]] = []

            for pattern in patterns:
                if pattern.confidence >= 0.6:
                    pattern_data_raw = (
                        pattern.pattern_data if pattern.pattern_data else {}
                    )
                    data: Dict[str, Any] = (
                        dict(pattern_data_raw)
                        if isinstance(pattern_data_raw, dict)
                        else {}
                    )
                    if data.get("settlement_rate", 0) >= 0.7:
                        recommendations.append(
                            {
                                "type": "aggressive_approach",
                                "furnisher": pattern.furnisher_name,
                                "recommendation": f"Consider aggressive initial demands with {pattern.furnisher_name} - high settlement tendency",
                                "confidence": pattern.confidence,
                            }
                        )
                    elif data.get("settlement_rate", 0) <= 0.3:
                        recommendations.append(
                            {
                                "type": "litigation_prep",
                                "furnisher": pattern.furnisher_name,
                                "recommendation": f"Prepare litigation documentation early for {pattern.furnisher_name} - low settlement tendency",
                                "confidence": pattern.confidence,
                            }
                        )

            if seasonal.get("recommendations"):
                for rec in seasonal["recommendations"]:
                    recommendations.append(
                        {
                            "type": "timing",
                            "recommendation": rec,
                            "confidence": seasonal.get("confidence", 0.5),
                        }
                    )

            categorized_insights["actionable_recommendations"] = recommendations[:10]

            return {
                "insights": categorized_insights,
                "total_patterns": len(patterns),
                "filters_applied": filters,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def refresh_all_patterns(self) -> Dict[str, Any]:
        """
        Refresh all furnisher patterns by re-analyzing recent data.
        """
        db = SessionLocal()
        try:
            furnishers = db.query(Furnisher).all()

            updated = 0
            errors: List[Dict[str, Any]] = []

            for furnisher in furnishers:
                try:
                    result = self.analyze_furnisher_behavior(furnisher_id=int(furnisher.id))  # type: ignore[arg-type]
                    if result.get("sample_size", 0) > 0:
                        updated += 1
                except Exception as e:
                    errors.append({"furnisher_id": furnisher.id, "error": str(e)})

            self.detect_seasonal_trends()
            self.identify_winning_strategies()

            return {
                "success": True,
                "furnishers_updated": updated,
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()


def analyze_furnisher_behavior(
    furnisher_id: Optional[int] = None, furnisher_name: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to analyze furnisher behavior."""
    service = PatternAnalyzerService()
    return service.analyze_furnisher_behavior(furnisher_id, furnisher_name)


def detect_seasonal_trends() -> Dict[str, Any]:
    """Convenience function to detect seasonal trends."""
    service = PatternAnalyzerService()
    return service.detect_seasonal_trends()


def identify_winning_strategies(violation_type: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to identify winning strategies."""
    service = PatternAnalyzerService()
    return service.identify_winning_strategies(violation_type)


def find_attorney_strengths() -> Dict[str, Any]:
    """Convenience function to find attorney strengths."""
    service = PatternAnalyzerService()
    return service.find_attorney_strengths()


def get_pattern_insights(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function to get pattern insights."""
    service = PatternAnalyzerService()
    return service.get_pattern_insights(filters)
