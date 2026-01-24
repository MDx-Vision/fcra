"""
ROI Calculator Service
Calculate potential settlement/recovery value for clients based on violations, items, and historical data.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from database import (
    Analysis,
    Client,
    CreditScoreSnapshot,
    Damages,
    DisputeItem,
    ROICalculation,
    Settlement,
    Staff,
    Violation,
    get_db,
)

# FCRA Statutory Damages
FCRA_WILLFUL_MIN = 100  # $100 minimum per willful violation
FCRA_WILLFUL_MAX = 1000  # $1,000 maximum per willful violation
FCRA_NEGLIGENT_ACTUAL = True  # Only actual damages for negligent

# Punitive damages multiplier (varies by jurisdiction, typically 2-5x)
PUNITIVE_MULTIPLIER_LOW = 1.5
PUNITIVE_MULTIPLIER_MID = 2.5
PUNITIVE_MULTIPLIER_HIGH = 5.0

# Historical deletion rates (based on industry data)
HISTORICAL_DELETION_RATES = {
    "collection": 0.65,
    "charge_off": 0.45,
    "late_payment": 0.40,
    "inquiry": 0.80,
    "public_record": 0.30,
    "mixed_file": 0.85,
    "identity_theft": 0.90,
    "default": 0.50,
}

# High-value account thresholds
HIGH_VALUE_COLLECTION_THRESHOLD = 1000
HIGH_VALUE_CHARGEOFF_THRESHOLD = 2500

# Score improvement estimates per deleted item
SCORE_IMPROVEMENT_PER_COLLECTION = 10
SCORE_IMPROVEMENT_PER_CHARGEOFF = 8
SCORE_IMPROVEMENT_PER_LATE = 5
SCORE_IMPROVEMENT_PER_INQUIRY = 3
SCORE_IMPROVEMENT_PER_PUBLIC_RECORD = 15

# Credit value improvement (savings from better rates over lifetime)
CREDIT_VALUE_PER_SCORE_POINT = 250  # Estimated lifetime savings per score point


class ROICalculatorService:
    """Service for calculating ROI and potential recovery value"""

    def __init__(self, db: Session = None):
        self.db = db or get_db()
        self._owns_session = db is None

    def __del__(self):
        if self._owns_session and self.db:
            self.db.close()

    def calculate_roi(
        self,
        client_id: int,
        staff_id: Optional[int] = None,
        actual_damages: Optional[Dict[str, float]] = None,
        save: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate complete ROI for a client.

        Args:
            client_id: Client ID
            staff_id: Staff member performing calculation
            actual_damages: Optional dict with actual damages inputs
            save: Whether to save the calculation to database

        Returns:
            Complete ROI calculation dictionary
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {"success": False, "error": "Client not found"}

        # Get violations
        violations = self._get_violations(client_id)

        # Get dispute items
        items = self._get_dispute_items(client_id)

        # Get damages from analysis
        analysis_damages = self._get_analysis_damages(client_id)

        # Calculate violation counts by type
        violation_counts = self._count_violations_by_type(violations)

        # Calculate statutory damages
        statutory = self._calculate_statutory_damages(violations)

        # Calculate actual damages
        actual = self._calculate_actual_damages(analysis_damages, actual_damages or {})

        # Calculate attorney fees estimate
        attorney_fees = self._estimate_attorney_fees(
            violation_counts["total"], statutory["max"], actual["total"]
        )

        # Analyze dispute items
        items_analysis = self._analyze_dispute_items(items)

        # Calculate settlement estimates
        estimates = self._calculate_settlement_estimates(
            statutory, actual, attorney_fees, violation_counts, items_analysis
        )

        # Calculate litigation potential
        litigation = self._calculate_litigation_potential(
            violations, violation_counts, statutory, actual, items_analysis
        )

        # Estimate score improvement
        score_improvement = self._estimate_score_improvement(items_analysis)

        # Calculate credit value improvement
        credit_value = self._calculate_credit_value_improvement(score_improvement)

        # Calculate total estimated value
        total_value = estimates["most_likely"] + credit_value

        # Determine confidence level
        confidence = self._determine_confidence_level(
            violation_counts["total"], items_analysis["total"], len(violations)
        )

        # Build result
        result = {
            "success": True,
            "client_id": client_id,
            "client_name": client.name,
            "calculated_at": datetime.utcnow().isoformat(),
            # Violation counts
            "violations": {
                "fcra": violation_counts["fcra"],
                "fdcpa": violation_counts["fdcpa"],
                "tcpa": violation_counts["tcpa"],
                "fcba": violation_counts["fcba"],
                "other": violation_counts["other"],
                "total": violation_counts["total"],
                "willful": violation_counts["willful"],
                "negligent": violation_counts["negligent"],
            },
            # Statutory damages
            "statutory_damages": {
                "min": statutory["min"],
                "max": statutory["max"],
                "punitive_potential": statutory["punitive"],
            },
            # Actual damages
            "actual_damages": {
                "credit_denial": actual["credit_denial"],
                "higher_interest": actual["higher_interest"],
                "emotional_distress": actual["emotional_distress"],
                "time_lost": actual["time_lost"],
                "other": actual["other"],
                "total": actual["total"],
            },
            # Attorney fees
            "attorney_fees": attorney_fees,
            # Items analysis
            "items": {
                "total_negative": items_analysis["total"],
                "disputable": items_analysis["disputable"],
                "high_value": items_analysis["high_value"],
                "estimated_deletion_rate": items_analysis["deletion_rate"],
                "by_type": items_analysis["by_type"],
            },
            # Settlement estimates
            "estimates": {
                "conservative": estimates["conservative"],
                "moderate": estimates["moderate"],
                "aggressive": estimates["aggressive"],
                "most_likely": estimates["most_likely"],
            },
            # Litigation potential
            "litigation": {
                "score": litigation["score"],
                "recommended": litigation["recommended"],
                "notes": litigation["notes"],
                "factors": litigation["factors"],
            },
            # Score improvement
            "score_improvement": {
                "estimated_points": score_improvement,
                "credit_value": credit_value,
            },
            # Summary
            "total_estimated_value": total_value,
            "confidence_level": confidence,
        }

        # Save to database if requested
        if save:
            calculation = self._save_calculation(client_id, staff_id, result)
            result["calculation_id"] = calculation.id

        return result

    def _get_violations(self, client_id: int) -> List[Violation]:
        """Get all violations for a client"""
        return self.db.query(Violation).filter(Violation.client_id == client_id).all()

    def _get_dispute_items(self, client_id: int) -> List[DisputeItem]:
        """Get all dispute items for a client"""
        return (
            self.db.query(DisputeItem).filter(DisputeItem.client_id == client_id).all()
        )

    def _get_analysis_damages(self, client_id: int) -> Optional[Damages]:
        """Get damages from latest analysis"""
        analysis = (
            self.db.query(Analysis)
            .filter(Analysis.client_id == client_id)
            .order_by(Analysis.created_at.desc())
            .first()
        )

        if analysis:
            return (
                self.db.query(Damages)
                .filter(Damages.analysis_id == analysis.id)
                .first()
            )
        return None

    def _count_violations_by_type(self, violations: List[Violation]) -> Dict[str, int]:
        """Count violations by type"""
        counts = {
            "fcra": 0,
            "fdcpa": 0,
            "tcpa": 0,
            "fcba": 0,
            "other": 0,
            "total": 0,
            "willful": 0,
            "negligent": 0,
        }

        for v in violations:
            counts["total"] += 1

            # Count by type
            violation_type = (v.violation_type or "").lower()
            fcra_section = (v.fcra_section or "").lower()

            if "fcra" in violation_type or fcra_section.startswith("1681"):
                counts["fcra"] += 1
            elif "fdcpa" in violation_type:
                counts["fdcpa"] += 1
            elif "tcpa" in violation_type:
                counts["tcpa"] += 1
            elif "fcba" in violation_type:
                counts["fcba"] += 1
            else:
                counts["other"] += 1

            # Count by severity
            if v.is_willful:
                counts["willful"] += 1
            else:
                counts["negligent"] += 1

        return counts

    def _calculate_statutory_damages(
        self, violations: List[Violation]
    ) -> Dict[str, float]:
        """Calculate statutory damages range"""
        min_damages = 0
        max_damages = 0
        punitive_potential = 0

        for v in violations:
            if v.is_willful:
                # Use violation's stored values if available
                if v.statutory_damages_min:
                    min_damages += v.statutory_damages_min
                else:
                    min_damages += FCRA_WILLFUL_MIN

                if v.statutory_damages_max:
                    max_damages += v.statutory_damages_max
                else:
                    max_damages += FCRA_WILLFUL_MAX

        # Calculate punitive damages potential (only for willful violations)
        if max_damages > 0:
            punitive_potential = max_damages * PUNITIVE_MULTIPLIER_MID

        return {
            "min": min_damages,
            "max": max_damages,
            "punitive": punitive_potential,
        }

    def _calculate_actual_damages(
        self, analysis_damages: Optional[Damages], user_inputs: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate actual damages from analysis and user inputs"""
        result = {
            "credit_denial": 0,
            "higher_interest": 0,
            "emotional_distress": 0,
            "time_lost": 0,
            "other": 0,
            "total": 0,
        }

        # Use analysis damages as base
        if analysis_damages:
            result["credit_denial"] = analysis_damages.credit_denials_amount or 0
            result["higher_interest"] = analysis_damages.higher_interest_amount or 0
            result["emotional_distress"] = (
                analysis_damages.time_stress_amount or 0
            )  # Mapped from time_stress
            result["other"] = analysis_damages.other_actual_amount or 0

        # Override with user inputs if provided
        if user_inputs.get("credit_denial") is not None:
            result["credit_denial"] = user_inputs["credit_denial"]
        if user_inputs.get("higher_interest") is not None:
            result["higher_interest"] = user_inputs["higher_interest"]
        if user_inputs.get("emotional_distress") is not None:
            result["emotional_distress"] = user_inputs["emotional_distress"]
        if user_inputs.get("time_lost") is not None:
            result["time_lost"] = user_inputs["time_lost"]
        if user_inputs.get("other") is not None:
            result["other"] = user_inputs["other"]

        result["total"] = sum(
            [
                result["credit_denial"],
                result["higher_interest"],
                result["emotional_distress"],
                result["time_lost"],
                result["other"],
            ]
        )

        return result

    def _estimate_attorney_fees(
        self, violation_count: int, statutory_max: float, actual_total: float
    ) -> float:
        """Estimate attorney fees (FCRA allows fee shifting)"""
        # Base estimate: $350/hour * estimated hours
        base_hours = 20 + (violation_count * 2)  # Base + per violation
        hourly_rate = 350

        # Fee estimate capped at damages potential
        fee_estimate = base_hours * hourly_rate
        damages_cap = (statutory_max + actual_total) * 0.5

        return min(fee_estimate, max(damages_cap, 5000))

    def _analyze_dispute_items(self, items: List[DisputeItem]) -> Dict[str, Any]:
        """Analyze dispute items for ROI calculation"""
        result = {
            "total": 0,
            "disputable": 0,
            "high_value": 0,
            "deletion_rate": 0,
            "by_type": {
                "collections": 0,
                "charge_offs": 0,
                "late_payments": 0,
                "inquiries": 0,
                "public_records": 0,
                "other": 0,
            },
            "by_status": {
                "pending": 0,
                "in_progress": 0,
                "deleted": 0,
                "verified": 0,
                "updated": 0,
            },
        }

        total_deletion_rate = 0

        for item in items:
            result["total"] += 1

            # Count by type
            item_type = (item.account_type or "").lower()
            if "collection" in item_type:
                result["by_type"]["collections"] += 1
                total_deletion_rate += HISTORICAL_DELETION_RATES["collection"]

                # Check for high value
                balance = item.balance or 0
                if balance >= HIGH_VALUE_COLLECTION_THRESHOLD:
                    result["high_value"] += 1

            elif "charge" in item_type or "off" in item_type:
                result["by_type"]["charge_offs"] += 1
                total_deletion_rate += HISTORICAL_DELETION_RATES["charge_off"]

                balance = item.balance or 0
                if balance >= HIGH_VALUE_CHARGEOFF_THRESHOLD:
                    result["high_value"] += 1

            elif "late" in item_type or "payment" in item_type:
                result["by_type"]["late_payments"] += 1
                total_deletion_rate += HISTORICAL_DELETION_RATES["late_payment"]

            elif "inquiry" in item_type or "inq" in item_type:
                result["by_type"]["inquiries"] += 1
                total_deletion_rate += HISTORICAL_DELETION_RATES["inquiry"]

            elif (
                "public" in item_type
                or "record" in item_type
                or "judgment" in item_type
                or "lien" in item_type
            ):
                result["by_type"]["public_records"] += 1
                total_deletion_rate += HISTORICAL_DELETION_RATES["public_record"]

            else:
                result["by_type"]["other"] += 1
                total_deletion_rate += HISTORICAL_DELETION_RATES["default"]

            # Count by status
            status = (item.status or "pending").lower()
            if "delete" in status or "removed" in status:
                result["by_status"]["deleted"] += 1
            elif "verified" in status:
                result["by_status"]["verified"] += 1
            elif "updated" in status or "modified" in status:
                result["by_status"]["updated"] += 1
            elif "progress" in status or "disputed" in status:
                result["by_status"]["in_progress"] += 1
            else:
                result["by_status"]["pending"] += 1

            # Count disputable items (not already deleted or verified)
            if status not in ["deleted", "removed", "verified"]:
                result["disputable"] += 1

        # Calculate average deletion rate
        if result["total"] > 0:
            result["deletion_rate"] = round(total_deletion_rate / result["total"], 2)

        return result

    def _calculate_settlement_estimates(
        self,
        statutory: Dict[str, float],
        actual: Dict[str, float],
        attorney_fees: float,
        violations: Dict[str, int],
        items: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate settlement estimates"""
        # Base damages pool
        base_damages = statutory["max"] + actual["total"] + attorney_fees

        # Factor in violation count and type
        violation_multiplier = 1.0
        if violations["willful"] > 0:
            violation_multiplier = 1.2
        if violations["total"] >= 5:
            violation_multiplier *= 1.1
        if violations["total"] >= 10:
            violation_multiplier *= 1.1

        # Factor in high-value items
        if items["high_value"] >= 3:
            violation_multiplier *= 1.15

        adjusted_base = base_damages * violation_multiplier

        # Conservative: 20-30% of potential damages (quick settlement)
        conservative = adjusted_base * 0.25

        # Moderate: 40-50% (negotiated settlement)
        moderate = adjusted_base * 0.45

        # Aggressive: 70-80% (with litigation threat or actual)
        aggressive = adjusted_base * 0.75

        # Most likely: weighted average (favor moderate)
        most_likely = (conservative * 0.2) + (moderate * 0.6) + (aggressive * 0.2)

        # Add punitive damages potential to aggressive estimate
        if violations["willful"] > 0:
            aggressive += statutory["punitive"] * 0.3  # 30% of punitive potential

        return {
            "conservative": round(conservative, 2),
            "moderate": round(moderate, 2),
            "aggressive": round(aggressive, 2),
            "most_likely": round(most_likely, 2),
        }

    def _calculate_litigation_potential(
        self,
        violations: List[Violation],
        counts: Dict[str, int],
        statutory: Dict[str, float],
        actual: Dict[str, float],
        items: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate litigation potential score (0-100)"""
        score = 0
        factors = []
        notes = []

        # Willful violations (high value for litigation)
        if counts["willful"] >= 3:
            score += 30
            factors.append({"name": "Multiple willful violations", "points": 30})
        elif counts["willful"] >= 1:
            score += 20
            factors.append({"name": "Willful violation present", "points": 20})

        # Total violation count
        if counts["total"] >= 10:
            score += 20
            factors.append({"name": "10+ violations", "points": 20})
        elif counts["total"] >= 5:
            score += 10
            factors.append({"name": "5+ violations", "points": 10})

        # High statutory damages potential
        if statutory["max"] >= 10000:
            score += 15
            factors.append({"name": "High statutory damages ($10k+)", "points": 15})
        elif statutory["max"] >= 5000:
            score += 10
            factors.append({"name": "Moderate statutory damages ($5k+)", "points": 10})

        # Actual damages documented
        if actual["total"] >= 5000:
            score += 15
            factors.append({"name": "Significant actual damages ($5k+)", "points": 15})
        elif actual["total"] >= 1000:
            score += 10
            factors.append({"name": "Documented actual damages ($1k+)", "points": 10})

        # High-value negative items
        if items["high_value"] >= 5:
            score += 10
            factors.append({"name": "5+ high-value items", "points": 10})
        elif items["high_value"] >= 2:
            score += 5
            factors.append({"name": "Multiple high-value items", "points": 5})

        # Low deletion rate (indicates resistant bureaus)
        if items["deletion_rate"] < 0.3:
            score += 10
            factors.append(
                {"name": "Low deletion rate (resistant bureaus)", "points": 10}
            )
            notes.append("Bureaus appear resistant - litigation may be effective")

        # Generate notes
        if score >= 70:
            notes.append(
                "Strong litigation potential - recommend attorney consultation"
            )
        elif score >= 50:
            notes.append(
                "Moderate litigation potential - may benefit from attorney review"
            )
        elif score >= 30:
            notes.append(
                "Some litigation factors present - dispute process may be sufficient"
            )
        else:
            notes.append("Low litigation indicators - focus on dispute process")

        return {
            "score": min(score, 100),
            "recommended": score >= 60,
            "notes": " ".join(notes),
            "factors": factors,
        }

    def _estimate_score_improvement(self, items: Dict[str, Any]) -> int:
        """Estimate credit score improvement from deletions"""
        estimated_deletions = {
            "collections": round(
                items["by_type"]["collections"]
                * HISTORICAL_DELETION_RATES["collection"]
            ),
            "charge_offs": round(
                items["by_type"]["charge_offs"]
                * HISTORICAL_DELETION_RATES["charge_off"]
            ),
            "late_payments": round(
                items["by_type"]["late_payments"]
                * HISTORICAL_DELETION_RATES["late_payment"]
            ),
            "inquiries": round(
                items["by_type"]["inquiries"] * HISTORICAL_DELETION_RATES["inquiry"]
            ),
            "public_records": round(
                items["by_type"]["public_records"]
                * HISTORICAL_DELETION_RATES["public_record"]
            ),
        }

        score_improvement = (
            estimated_deletions["collections"] * SCORE_IMPROVEMENT_PER_COLLECTION
            + estimated_deletions["charge_offs"] * SCORE_IMPROVEMENT_PER_CHARGEOFF
            + estimated_deletions["late_payments"] * SCORE_IMPROVEMENT_PER_LATE
            + estimated_deletions["inquiries"] * SCORE_IMPROVEMENT_PER_INQUIRY
            + estimated_deletions["public_records"]
            * SCORE_IMPROVEMENT_PER_PUBLIC_RECORD
        )

        # Cap at realistic maximum
        return min(score_improvement, 150)

    def _calculate_credit_value_improvement(self, score_improvement: int) -> float:
        """Calculate monetary value of credit score improvement"""
        return round(score_improvement * CREDIT_VALUE_PER_SCORE_POINT, 2)

    def _determine_confidence_level(
        self, violation_count: int, item_count: int, violation_records: int
    ) -> str:
        """Determine confidence level of calculation"""
        if violation_records >= 5 and item_count >= 10:
            return "high"
        elif violation_records >= 2 or item_count >= 5:
            return "medium"
        else:
            return "low"

    def _save_calculation(
        self, client_id: int, staff_id: Optional[int], result: Dict[str, Any]
    ) -> ROICalculation:
        """Save calculation to database"""
        calculation = ROICalculation(
            client_id=client_id,
            calculated_by_staff_id=staff_id,
            calculation_type="automatic" if staff_id is None else "manual",
            # Violation counts
            fcra_violations_count=result["violations"]["fcra"],
            fdcpa_violations_count=result["violations"]["fdcpa"],
            tcpa_violations_count=result["violations"]["tcpa"],
            fcba_violations_count=result["violations"]["fcba"],
            other_violations_count=result["violations"]["other"],
            total_violations=result["violations"]["total"],
            willful_violations=result["violations"]["willful"],
            negligent_violations=result["violations"]["negligent"],
            # Statutory damages
            statutory_damages_min=result["statutory_damages"]["min"],
            statutory_damages_max=result["statutory_damages"]["max"],
            punitive_damages_potential=result["statutory_damages"][
                "punitive_potential"
            ],
            # Actual damages
            credit_denial_damages=result["actual_damages"]["credit_denial"],
            higher_interest_damages=result["actual_damages"]["higher_interest"],
            emotional_distress_damages=result["actual_damages"]["emotional_distress"],
            time_lost_damages=result["actual_damages"]["time_lost"],
            other_actual_damages=result["actual_damages"]["other"],
            total_actual_damages=result["actual_damages"]["total"],
            # Attorney fees
            estimated_attorney_fees=result["attorney_fees"],
            # Items
            total_negative_items=result["items"]["total_negative"],
            disputable_items=result["items"]["disputable"],
            high_value_items=result["items"]["high_value"],
            estimated_deletion_rate=result["items"]["estimated_deletion_rate"],
            # Estimates
            conservative_estimate=result["estimates"]["conservative"],
            moderate_estimate=result["estimates"]["moderate"],
            aggressive_estimate=result["estimates"]["aggressive"],
            most_likely_estimate=result["estimates"]["most_likely"],
            # Litigation
            litigation_score=result["litigation"]["score"],
            litigation_recommended=result["litigation"]["recommended"],
            litigation_notes=result["litigation"]["notes"],
            # Score improvement
            estimated_score_improvement=result["score_improvement"]["estimated_points"],
            credit_value_improvement=result["score_improvement"]["credit_value"],
            # Summary
            total_estimated_value=result["total_estimated_value"],
            confidence_level=result["confidence_level"],
            # Store inputs for audit
            calculation_inputs=result,
        )

        self.db.add(calculation)
        self.db.commit()
        self.db.refresh(calculation)

        return calculation

    def get_client_calculations(
        self, client_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get calculation history for a client"""
        calculations = (
            self.db.query(ROICalculation)
            .filter(ROICalculation.client_id == client_id)
            .order_by(ROICalculation.calculated_at.desc())
            .limit(limit)
            .all()
        )

        return [c.to_dict() for c in calculations]

    def get_calculation(self, calculation_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific calculation"""
        calculation = (
            self.db.query(ROICalculation)
            .filter(ROICalculation.id == calculation_id)
            .first()
        )

        if calculation:
            return calculation.to_dict()
        return None

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary of all calculations"""
        # Total calculations
        total_calcs = self.db.query(func.count(ROICalculation.id)).scalar() or 0

        # Recent calculations (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_calcs = (
            self.db.query(func.count(ROICalculation.id))
            .filter(ROICalculation.calculated_at >= thirty_days_ago)
            .scalar()
            or 0
        )

        # Average estimates
        avg_values = self.db.query(
            func.avg(ROICalculation.conservative_estimate),
            func.avg(ROICalculation.moderate_estimate),
            func.avg(ROICalculation.aggressive_estimate),
            func.avg(ROICalculation.most_likely_estimate),
            func.avg(ROICalculation.total_estimated_value),
            func.avg(ROICalculation.litigation_score),
        ).first()

        # Clients with high litigation potential
        high_litigation = (
            self.db.query(func.count(ROICalculation.id))
            .filter(ROICalculation.litigation_recommended == True)
            .scalar()
            or 0
        )

        # Total estimated value across all clients
        total_value = (
            self.db.query(func.sum(ROICalculation.total_estimated_value)).scalar() or 0
        )

        # Recent calculations for display
        recent = (
            self.db.query(ROICalculation)
            .order_by(ROICalculation.calculated_at.desc())
            .limit(10)
            .all()
        )

        # Get client names for recent calculations
        recent_with_names = []
        for calc in recent:
            client = self.db.query(Client).filter(Client.id == calc.client_id).first()
            data = calc.to_dict()
            data["client_name"] = client.name if client else "Unknown"
            recent_with_names.append(data)

        return {
            "total_calculations": total_calcs,
            "recent_calculations": recent_calcs,
            "averages": {
                "conservative": round(avg_values[0] or 0, 2),
                "moderate": round(avg_values[1] or 0, 2),
                "aggressive": round(avg_values[2] or 0, 2),
                "most_likely": round(avg_values[3] or 0, 2),
                "total_value": round(avg_values[4] or 0, 2),
                "litigation_score": round(avg_values[5] or 0, 1),
            },
            "high_litigation_count": high_litigation,
            "total_estimated_value": round(total_value, 2),
            "recent": recent_with_names,
        }

    def get_aggregate_stats(self, period: str = "all") -> Dict[str, Any]:
        """Get aggregate statistics for ROI calculations"""
        query = self.db.query(ROICalculation)

        # Apply period filter
        if period == "week":
            cutoff = datetime.utcnow() - timedelta(days=7)
            query = query.filter(ROICalculation.calculated_at >= cutoff)
        elif period == "month":
            cutoff = datetime.utcnow() - timedelta(days=30)
            query = query.filter(ROICalculation.calculated_at >= cutoff)
        elif period == "quarter":
            cutoff = datetime.utcnow() - timedelta(days=90)
            query = query.filter(ROICalculation.calculated_at >= cutoff)
        elif period == "year":
            cutoff = datetime.utcnow() - timedelta(days=365)
            query = query.filter(ROICalculation.calculated_at >= cutoff)

        calculations = query.all()

        if not calculations:
            return {
                "count": 0,
                "total_violations": 0,
                "total_items": 0,
                "avg_estimate": 0,
                "max_estimate": 0,
                "min_estimate": 0,
                "litigation_recommended_pct": 0,
            }

        total_violations = sum(c.total_violations for c in calculations)
        total_items = sum(c.total_negative_items for c in calculations)
        estimates = [c.most_likely_estimate for c in calculations]
        litigation_recommended = sum(
            1 for c in calculations if c.litigation_recommended
        )

        return {
            "count": len(calculations),
            "total_violations": total_violations,
            "total_items": total_items,
            "avg_estimate": (
                round(sum(estimates) / len(estimates), 2) if estimates else 0
            ),
            "max_estimate": max(estimates) if estimates else 0,
            "min_estimate": min(estimates) if estimates else 0,
            "total_estimated_value": round(
                sum(c.total_estimated_value for c in calculations), 2
            ),
            "litigation_recommended_pct": (
                round(litigation_recommended / len(calculations) * 100, 1)
                if calculations
                else 0
            ),
            "by_confidence": {
                "high": sum(1 for c in calculations if c.confidence_level == "high"),
                "medium": sum(
                    1 for c in calculations if c.confidence_level == "medium"
                ),
                "low": sum(1 for c in calculations if c.confidence_level == "low"),
            },
        }

    def quick_estimate(
        self,
        violations_count: int = 0,
        willful_count: int = 0,
        collections_count: int = 0,
        chargeoffs_count: int = 0,
        late_payments_count: int = 0,
        inquiries_count: int = 0,
        public_records_count: int = 0,
        actual_damages: float = 0,
    ) -> Dict[str, Any]:
        """Quick ROI estimate without client data"""
        # Statutory damages
        statutory_min = willful_count * FCRA_WILLFUL_MIN
        statutory_max = willful_count * FCRA_WILLFUL_MAX
        punitive = statutory_max * PUNITIVE_MULTIPLIER_MID if willful_count > 0 else 0

        # Attorney fees estimate
        attorney_fees = min(15000, 7000 + (violations_count * 300))

        # Total items
        total_items = (
            collections_count
            + chargeoffs_count
            + late_payments_count
            + inquiries_count
            + public_records_count
        )

        # Base damages
        base_damages = statutory_max + actual_damages + attorney_fees

        # Calculate estimates
        conservative = base_damages * 0.25
        moderate = base_damages * 0.45
        aggressive = base_damages * 0.75 + (punitive * 0.3 if willful_count > 0 else 0)
        most_likely = (conservative * 0.2) + (moderate * 0.6) + (aggressive * 0.2)

        # Score improvement estimate
        score_improvement = (
            min(collections_count, 5) * SCORE_IMPROVEMENT_PER_COLLECTION
            + min(chargeoffs_count, 3) * SCORE_IMPROVEMENT_PER_CHARGEOFF
            + min(late_payments_count, 10) * SCORE_IMPROVEMENT_PER_LATE
            + min(inquiries_count, 5) * SCORE_IMPROVEMENT_PER_INQUIRY
            + min(public_records_count, 2) * SCORE_IMPROVEMENT_PER_PUBLIC_RECORD
        )
        score_improvement = min(score_improvement, 100)

        credit_value = score_improvement * CREDIT_VALUE_PER_SCORE_POINT

        return {
            "success": True,
            "quick_estimate": True,
            "statutory_damages": {
                "min": statutory_min,
                "max": statutory_max,
                "punitive": punitive,
            },
            "actual_damages": actual_damages,
            "attorney_fees": attorney_fees,
            "estimates": {
                "conservative": round(conservative, 2),
                "moderate": round(moderate, 2),
                "aggressive": round(aggressive, 2),
                "most_likely": round(most_likely, 2),
            },
            "score_improvement": {
                "estimated_points": score_improvement,
                "credit_value": credit_value,
            },
            "total_estimated_value": round(most_likely + credit_value, 2),
            "items_analyzed": total_items,
            "violations_count": violations_count,
        }

    def export_calculations(
        self, client_ids: Optional[List[int]] = None, period: str = "all"
    ) -> List[Dict[str, Any]]:
        """Export calculations for CSV download"""
        query = self.db.query(ROICalculation)

        if client_ids:
            query = query.filter(ROICalculation.client_id.in_(client_ids))

        if period == "week":
            cutoff = datetime.utcnow() - timedelta(days=7)
            query = query.filter(ROICalculation.calculated_at >= cutoff)
        elif period == "month":
            cutoff = datetime.utcnow() - timedelta(days=30)
            query = query.filter(ROICalculation.calculated_at >= cutoff)
        elif period == "quarter":
            cutoff = datetime.utcnow() - timedelta(days=90)
            query = query.filter(ROICalculation.calculated_at >= cutoff)

        calculations = query.order_by(ROICalculation.calculated_at.desc()).all()

        export_data = []
        for calc in calculations:
            client = self.db.query(Client).filter(Client.id == calc.client_id).first()
            export_data.append(
                {
                    "calculation_id": calc.id,
                    "client_id": calc.client_id,
                    "client_name": client.name if client else "Unknown",
                    "calculated_at": (
                        calc.calculated_at.isoformat() if calc.calculated_at else ""
                    ),
                    "total_violations": calc.total_violations,
                    "willful_violations": calc.willful_violations,
                    "total_items": calc.total_negative_items,
                    "statutory_min": calc.statutory_damages_min,
                    "statutory_max": calc.statutory_damages_max,
                    "actual_damages": calc.total_actual_damages,
                    "attorney_fees": calc.estimated_attorney_fees,
                    "conservative_estimate": calc.conservative_estimate,
                    "moderate_estimate": calc.moderate_estimate,
                    "aggressive_estimate": calc.aggressive_estimate,
                    "most_likely_estimate": calc.most_likely_estimate,
                    "litigation_score": calc.litigation_score,
                    "litigation_recommended": (
                        "Yes" if calc.litigation_recommended else "No"
                    ),
                    "score_improvement": calc.estimated_score_improvement,
                    "credit_value": calc.credit_value_improvement,
                    "total_estimated_value": calc.total_estimated_value,
                    "confidence": calc.confidence_level,
                }
            )

        return export_data
