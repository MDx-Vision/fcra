"""
ML Learning Service for FCRA Litigation Platform.
Learns from case outcomes to improve predictions using lightweight statistical methods.
Uses historical averages, Bayesian updating, and pattern matching.
"""

import json
import math
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_, func, or_

from database import (
    Analysis,
    CaseOutcome,
    CaseScore,
    Client,
    Damages,
    Furnisher,
    FurnisherStats,
    OutcomePrediction,
    SessionLocal,
    Staff,
    Standing,
    Violation,
)


class MLLearningService:
    """Service for ML-powered outcome predictions and learning"""

    MODEL_VERSION = "v1.0"

    OUTCOME_TYPES = ["won", "lost", "settled", "dismissed"]

    VIOLATION_WEIGHTS = {
        "reinsertion": 2.5,
        "identity_theft": 3.0,
        "mixed_file": 2.0,
        "611_failure": 1.5,
        "605b_failure": 1.8,
        "623_failure": 1.3,
        "inaccurate_reporting": 1.0,
        "default": 1.0,
    }

    def __init__(self):
        self._cache = {}
        self._cache_expiry = {}
        self._cache_duration = timedelta(minutes=15)
        self._cleanup_counter = 0
        self._cleanup_frequency = 10  # Cleanup every 10 cache sets

    def _get_cache(self, key):
        if key in self._cache and datetime.utcnow() < self._cache_expiry.get(
            key, datetime.min
        ):
            return self._cache[key]
        # Remove expired entry on read
        if key in self._cache:
            del self._cache[key]
            del self._cache_expiry[key]
        return None

    def _set_cache(self, key, value):
        self._cache[key] = value
        self._cache_expiry[key] = datetime.utcnow() + self._cache_duration
        # Periodically cleanup expired entries
        self._cleanup_counter += 1
        if self._cleanup_counter >= self._cleanup_frequency:
            self._cleanup_expired()
            self._cleanup_counter = 0

    def _cleanup_expired(self) -> int:
        """Remove all expired cache entries"""
        now = datetime.utcnow()
        expired_keys = [k for k, exp in self._cache_expiry.items() if now > exp]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._cache_expiry.pop(key, None)
        return len(expired_keys)

    def record_outcome(self, client_id: int, outcome_data: dict) -> dict:
        """
        Record a completed case outcome for ML training.

        Args:
            client_id: The client ID
            outcome_data: Dict with case outcome details

        Returns:
            Dict with success status and outcome record ID
        """
        db = SessionLocal()
        try:
            outcome = CaseOutcome(
                client_id=client_id,
                case_type=outcome_data.get("case_type", "fcra_dispute"),
                violation_types=outcome_data.get("violation_types", []),
                furnisher_id=outcome_data.get("furnisher_id"),
                initial_score=outcome_data.get("initial_score", 0),
                final_outcome=outcome_data.get("final_outcome", "settled"),
                settlement_amount=outcome_data.get("settlement_amount", 0),
                actual_damages=outcome_data.get("actual_damages", 0),
                time_to_resolution_days=outcome_data.get("time_to_resolution_days", 0),
                attorney_id=outcome_data.get("attorney_id"),
                key_factors=outcome_data.get("key_factors", {}),
                dispute_rounds_completed=outcome_data.get(
                    "dispute_rounds_completed", 0
                ),
                bureaus_involved=outcome_data.get("bureaus_involved", []),
                violation_count=outcome_data.get("violation_count", 0),
                willfulness_score=outcome_data.get("willfulness_score", 0),
                documentation_quality=outcome_data.get("documentation_quality", 0),
            )

            db.add(outcome)
            db.commit()
            db.refresh(outcome)

            self._update_predictions_with_actual(db, client_id, outcome)

            self._cache.clear()

            return {
                "success": True,
                "outcome_id": outcome.id,
                "message": "Outcome recorded successfully",
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def _update_predictions_with_actual(self, db, client_id: int, outcome: CaseOutcome):
        """Update pending predictions with actual outcome values"""
        predictions = (
            db.query(OutcomePrediction)
            .filter(
                OutcomePrediction.client_id == client_id,
                OutcomePrediction.actual_value.is_(None),
            )
            .all()
        )

        for pred in predictions:
            if pred.prediction_type == "outcome":
                pred.actual_value = outcome.final_outcome
                pred.was_accurate = pred.predicted_value == outcome.final_outcome
            elif pred.prediction_type == "settlement_amount":
                pred.actual_value = str(outcome.settlement_amount)
                try:
                    predicted = float(pred.predicted_value)
                    pred.prediction_error = abs(predicted - outcome.settlement_amount)
                    pred.was_accurate = (
                        pred.prediction_error / max(outcome.settlement_amount, 1) < 0.25
                    )
                except:
                    pass
            elif pred.prediction_type == "resolution_time":
                pred.actual_value = str(outcome.time_to_resolution_days)
                try:
                    predicted = float(pred.predicted_value)
                    pred.prediction_error = abs(
                        predicted - outcome.time_to_resolution_days
                    )
                    pred.was_accurate = pred.prediction_error < 30
                except:
                    pass

            pred.resolved_at = datetime.utcnow()

        db.commit()

    def get_similar_cases(
        self,
        violation_types: Optional[list[Any]] = None,
        furnisher_id: Optional[int] = None,
        limit: int = 10,
    ) -> list[Any]:
        """
        Find similar historical cases for comparison.

        Uses violation type overlap and furnisher matching.
        """
        db = SessionLocal()
        try:
            query = db.query(CaseOutcome)

            if furnisher_id:
                query = query.filter(CaseOutcome.furnisher_id == furnisher_id)

            outcomes = query.order_by(CaseOutcome.created_at.desc()).limit(100).all()

            if not violation_types:
                return [o.to_dict() for o in outcomes[:limit]]

            violation_set = set(violation_types)
            scored_outcomes = []

            for outcome in outcomes:
                outcome_violations = set(outcome.violation_types or [])
                overlap = len(violation_set & outcome_violations)
                union = len(violation_set | outcome_violations)
                similarity = overlap / max(union, 1)

                if furnisher_id and outcome.furnisher_id == furnisher_id:
                    similarity += 0.2

                scored_outcomes.append((similarity, outcome))

            scored_outcomes.sort(key=lambda x: x[0], reverse=True)

            return [o.to_dict() for _, o in scored_outcomes[:limit]]

        except Exception as e:
            return []
        finally:
            db.close()

    def calculate_success_rate(
        self, filters: Optional[dict[Any, Any]] = None
    ) -> dict[str, Any]:
        """
        Calculate success rates by various dimensions.

        Args:
            filters: Optional dict with violation_type, furnisher_id, attorney_id, date_range

        Returns:
            Dict with success rates and breakdown
        """
        cache_key = f"success_rate_{json.dumps(filters or {}, sort_keys=True)}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        db = SessionLocal()
        try:
            query = db.query(CaseOutcome)

            filters = filters or {}

            if filters.get("furnisher_id"):
                query = query.filter(
                    CaseOutcome.furnisher_id == filters["furnisher_id"]
                )

            if filters.get("attorney_id"):
                query = query.filter(CaseOutcome.attorney_id == filters["attorney_id"])

            if filters.get("date_from"):
                query = query.filter(CaseOutcome.created_at >= filters["date_from"])

            if filters.get("date_to"):
                query = query.filter(CaseOutcome.created_at <= filters["date_to"])

            outcomes = query.all()

            if not outcomes:
                return {
                    "total_cases": 0,
                    "success_rate": 0,
                    "settlement_rate": 0,
                    "won_rate": 0,
                    "lost_rate": 0,
                    "dismissed_rate": 0,
                    "by_violation_type": {},
                    "by_furnisher": {},
                    "confidence": 0,
                }

            total = len(outcomes)
            won = sum(1 for o in outcomes if o.final_outcome == "won")
            settled = sum(1 for o in outcomes if o.final_outcome == "settled")
            lost = sum(1 for o in outcomes if o.final_outcome == "lost")
            dismissed = sum(1 for o in outcomes if o.final_outcome == "dismissed")

            success = won + settled

            by_violation: dict[str, Any] = {}
            for outcome in outcomes:
                for vtype in list(outcome.violation_types or []):
                    if vtype not in by_violation:
                        by_violation[vtype] = {"total": 0, "success": 0}
                    by_violation[vtype]["total"] += 1
                    if outcome.final_outcome in ["won", "settled"]:
                        by_violation[vtype]["success"] += 1

            for vtype in by_violation:
                data = by_violation[vtype]
                data["rate"] = round(data["success"] / max(data["total"], 1), 3)

            by_furnisher: dict[Any, dict[str, Any]] = {}
            for outcome in outcomes:
                fid: Any = outcome.furnisher_id or "unknown"
                if fid not in by_furnisher:
                    by_furnisher[fid] = {"total": 0, "success": 0}
                by_furnisher[fid]["total"] += 1
                if outcome.final_outcome in ["won", "settled"]:
                    by_furnisher[fid]["success"] += 1

            for fid in by_furnisher:
                data = by_furnisher[fid]
                data["rate"] = round(data["success"] / max(data["total"], 1), 3)

            confidence = min(1.0, total / 100)

            result = {
                "total_cases": total,
                "success_rate": round(success / max(total, 1), 3),
                "settlement_rate": round(settled / max(total, 1), 3),
                "won_rate": round(won / max(total, 1), 3),
                "lost_rate": round(lost / max(total, 1), 3),
                "dismissed_rate": round(dismissed / max(total, 1), 3),
                "by_violation_type": by_violation,
                "by_furnisher": by_furnisher,
                "confidence": round(confidence, 3),
            }

            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def get_average_settlement(
        self, filters: Optional[dict[Any, Any]] = None
    ) -> dict[str, Any]:
        """
        Calculate average settlement amounts with statistical breakdown.
        """
        db = SessionLocal()
        try:
            query = db.query(CaseOutcome).filter(
                CaseOutcome.final_outcome.in_(["won", "settled"]),
                CaseOutcome.settlement_amount > 0,
            )

            filters = filters or {}

            if filters.get("violation_type"):
                pass

            if filters.get("furnisher_id"):
                query = query.filter(
                    CaseOutcome.furnisher_id == filters["furnisher_id"]
                )

            outcomes = query.all()

            if not outcomes:
                return {
                    "count": 0,
                    "average": 0,
                    "median": 0,
                    "min": 0,
                    "max": 0,
                    "std_dev": 0,
                    "percentile_25": 0,
                    "percentile_75": 0,
                    "by_violation_type": {},
                }

            amounts: list[float] = sorted(
                [float(o.settlement_amount) for o in outcomes]
            )
            n = len(amounts)

            avg = sum(amounts) / n
            median = (
                amounts[n // 2]
                if n % 2
                else (amounts[n // 2 - 1] + amounts[n // 2]) / 2
            )

            variance = sum((x - avg) ** 2 for x in amounts) / max(n - 1, 1)
            std_dev = math.sqrt(variance)

            p25_idx = int(n * 0.25)
            p75_idx = int(n * 0.75)

            by_violation: dict[str, Any] = {}
            for outcome in outcomes:
                for vtype in list(outcome.violation_types or []):
                    if vtype not in by_violation:
                        by_violation[vtype] = []
                    by_violation[vtype].append(outcome.settlement_amount)

            for vtype in list(by_violation.keys()):
                vals: list[Any] = by_violation[vtype]
                by_violation[vtype] = {
                    "count": len(vals),
                    "average": round(sum(vals) / len(vals), 2),
                    "max": max(vals),
                }

            return {
                "count": n,
                "average": round(avg, 2),
                "median": round(median, 2),
                "min": round(min(amounts), 2),
                "max": round(max(amounts), 2),
                "std_dev": round(std_dev, 2),
                "percentile_25": round(amounts[p25_idx], 2),
                "percentile_75": round(amounts[p75_idx], 2),
                "by_violation_type": by_violation,
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def get_resolution_time_estimate(
        self, violation_types: Optional[list[Any]] = None
    ) -> dict[str, Any]:
        """
        Estimate time to resolution based on historical data.
        """
        db = SessionLocal()
        try:
            query = db.query(CaseOutcome).filter(
                CaseOutcome.time_to_resolution_days > 0
            )

            outcomes = query.all()

            if not outcomes:
                return {
                    "estimated_days": 90,
                    "confidence": 0.3,
                    "range_min": 30,
                    "range_max": 180,
                    "sample_size": 0,
                }

            relevant_outcomes = []
            violation_set = set(violation_types or [])

            for outcome in outcomes:
                outcome_violations = set(outcome.violation_types or [])
                if not violation_types or (violation_set & outcome_violations):
                    relevant_outcomes.append(outcome)

            if not relevant_outcomes:
                relevant_outcomes = outcomes

            days = [o.time_to_resolution_days for o in relevant_outcomes]
            n = len(days)

            avg = sum(days) / n
            sorted_days = sorted(days)

            p10 = sorted_days[int(n * 0.1)] if n > 10 else sorted_days[0]
            p90 = sorted_days[int(n * 0.9)] if n > 10 else sorted_days[-1]

            confidence = min(1.0, n / 50)

            return {
                "estimated_days": round(avg),
                "confidence": round(confidence, 3),
                "range_min": round(p10),
                "range_max": round(p90),
                "sample_size": n,
                "median_days": sorted_days[n // 2],
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def generate_prediction_features(self, client_id: int) -> dict[str, Any]:
        """
        Extract ML features from a client's case for prediction.
        """
        db = SessionLocal()
        try:
            violations = (
                db.query(Violation).filter(Violation.client_id == client_id).all()
            )
            standing = (
                db.query(Standing).filter(Standing.client_id == client_id).first()
            )
            damages = db.query(Damages).filter(Damages.client_id == client_id).first()
            case_score = (
                db.query(CaseScore).filter(CaseScore.client_id == client_id).first()
            )
            client = db.query(Client).filter(Client.id == client_id).first()

            violation_types_list: list[str] = list(
                set(str(v.violation_type) for v in violations if v.violation_type)
            )
            features: dict[str, Any] = {
                "violation_count": len(violations),
                "violation_types": violation_types_list,
                "bureaus_affected": list(set(v.bureau for v in violations if v.bureau)),
                "bureaus_count": len(set(v.bureau for v in violations if v.bureau)),
                "willful_count": sum(1 for v in violations if v.is_willful),
                "willfulness_ratio": sum(1 for v in violations if v.is_willful)
                / max(len(violations), 1),
                "has_concrete_harm": standing.has_concrete_harm if standing else False,
                "has_dissemination": standing.has_dissemination if standing else False,
                "denial_letters": standing.denial_letters_count if standing else 0,
                "total_damages": 0,
                "actual_damages": 0,
                "statutory_damages": 0,
                "case_score": 0,
                "settlement_probability": 0,
                "dispute_round": client.current_dispute_round if client else 0,
            }

            if damages:
                actual_dmg = damages.actual_damages_total or 0
                statutory_dmg = damages.statutory_damages_total or 0
                features["actual_damages"] = actual_dmg
                features["statutory_damages"] = statutory_dmg
                features["total_damages"] = actual_dmg + statutory_dmg

            if case_score:
                features["case_score"] = case_score.total_score or 0
                features["settlement_probability"] = (
                    case_score.settlement_probability or 0
                )

            weighted_score: float = 0.0
            for vtype in violation_types_list:
                vtype_lower = vtype.lower() if vtype else ""
                weight = self.VIOLATION_WEIGHTS.get(
                    vtype_lower, self.VIOLATION_WEIGHTS["default"]
                )
                weighted_score += weight
            features["weighted_violation_score"] = round(weighted_score, 2)

            features["has_reinsertion"] = any(
                "reinsertion" in (v or "").lower() for v in violation_types_list
            )
            features["has_identity_theft"] = any(
                "identity" in (v or "").lower() for v in violation_types_list
            )

            return features

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def predict_outcome(self, client_id: int) -> dict:
        """
        Predict the likely outcome for a case using Bayesian inference.
        """
        db = SessionLocal()
        try:
            features = self.generate_prediction_features(client_id)
            if "error" in features:
                return features

            success_data = self.calculate_success_rate()

            base_success_rate = success_data.get("success_rate", 0.5)

            score = base_success_rate
            confidence_factors = []

            if features["violation_count"] >= 5:
                score += 0.1
                confidence_factors.append("Multiple violations (+10%)")
            elif features["violation_count"] == 0:
                score -= 0.3
                confidence_factors.append("No violations identified (-30%)")

            if features["willfulness_ratio"] >= 0.5:
                score += 0.15
                confidence_factors.append("High willfulness ratio (+15%)")

            if features["has_concrete_harm"]:
                score += 0.1
                confidence_factors.append("Concrete harm documented (+10%)")

            if features["has_dissemination"]:
                score += 0.05
                confidence_factors.append("Dissemination proven (+5%)")

            if features["denial_letters"] >= 2:
                score += 0.1
                confidence_factors.append("Multiple denial letters (+10%)")

            if features["has_reinsertion"]:
                score += 0.15
                confidence_factors.append("Reinsertion violation (+15%)")

            if features["has_identity_theft"]:
                score += 0.1
                confidence_factors.append("Identity theft violation (+10%)")

            if features["bureaus_count"] >= 3:
                score += 0.05
                confidence_factors.append("All 3 bureaus affected (+5%)")

            score = max(0.1, min(0.95, score))

            if score >= 0.7:
                predicted_outcome = "settled"
            elif score >= 0.5:
                predicted_outcome = "settled"
            elif score >= 0.3:
                predicted_outcome = "dismissed"
            else:
                predicted_outcome = "lost"

            base_confidence = min(
                0.9,
                success_data.get("confidence", 0.5)
                + (features["violation_count"] * 0.02),
            )

            prediction = OutcomePrediction(
                client_id=client_id,
                prediction_type="outcome",
                predicted_value=predicted_outcome,
                confidence_score=round(base_confidence, 3),
                features_used=features,
                model_version=self.MODEL_VERSION,
            )
            db.add(prediction)
            db.commit()

            return {
                "predicted_outcome": predicted_outcome,
                "success_probability": round(score, 3),
                "confidence": round(base_confidence, 3),
                "confidence_factors": confidence_factors,
                "features_summary": {
                    "violations": features["violation_count"],
                    "willful_violations": features["willful_count"],
                    "bureaus": features["bureaus_count"],
                    "total_damages": features["total_damages"],
                    "has_strong_standing": features["has_concrete_harm"],
                },
                "prediction_id": prediction.id,
            }

        except Exception as e:
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()

    def predict_settlement_range(self, client_id: int) -> dict:
        """
        Predict settlement range based on case features and historical data.
        """
        db = SessionLocal()
        try:
            features = self.generate_prediction_features(client_id)
            if "error" in features:
                return features

            settlement_stats = self.get_average_settlement()

            if settlement_stats.get("count", 0) == 0:
                base_min = 1000
                base_avg = 5000
                base_max = 15000
            else:
                base_min = settlement_stats.get("percentile_25", 1000)
                base_avg = settlement_stats.get("average", 5000)
                base_max = settlement_stats.get("percentile_75", 15000)

            multiplier = 1.0

            multiplier += (features["violation_count"] - 1) * 0.15

            multiplier += features["willful_count"] * 0.25

            if features["has_reinsertion"]:
                multiplier += 0.5

            if features["has_identity_theft"]:
                multiplier += 0.4

            if features["has_concrete_harm"]:
                multiplier += 0.2

            multiplier += features["denial_letters"] * 0.1

            if features["bureaus_count"] >= 3:
                multiplier += 0.15

            multiplier = max(0.5, min(3.0, multiplier))

            predicted_min = round(base_min * multiplier)
            predicted_avg = round(base_avg * multiplier)
            predicted_max = round(base_max * multiplier)

            confidence = min(0.9, settlement_stats.get("count", 0) / 100 + 0.3)

            prediction = OutcomePrediction(
                client_id=client_id,
                prediction_type="settlement_amount",
                predicted_value=str(predicted_avg),
                confidence_score=round(confidence, 3),
                features_used={
                    "multiplier": multiplier,
                    "base_avg": base_avg,
                    **features,
                },
                model_version=self.MODEL_VERSION,
            )
            db.add(prediction)
            db.commit()

            return {
                "settlement_range": {
                    "min": predicted_min,
                    "average": predicted_avg,
                    "max": predicted_max,
                },
                "multiplier": round(multiplier, 2),
                "confidence": round(confidence, 3),
                "historical_comparison": {
                    "base_average": round(base_avg, 2),
                    "sample_size": settlement_stats.get("count", 0),
                },
                "prediction_id": prediction.id,
            }

        except Exception as e:
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()

    def update_model_accuracy(self) -> dict:
        """
        Analyze model accuracy by comparing predictions to actual outcomes.
        """
        db = SessionLocal()
        try:
            predictions = (
                db.query(OutcomePrediction)
                .filter(OutcomePrediction.actual_value.isnot(None))
                .all()
            )

            if not predictions:
                return {
                    "total_predictions": 0,
                    "accuracy": 0,
                    "by_type": {},
                    "message": "No resolved predictions yet",
                }

            by_type: dict[str, dict[str, Any]] = {}
            for pred in predictions:
                ptype: str = str(pred.prediction_type)
                if ptype not in by_type:
                    by_type[ptype] = {"total": 0, "accurate": 0, "errors": []}

                by_type[ptype]["total"] = int(by_type[ptype]["total"]) + 1
                if pred.was_accurate:
                    by_type[ptype]["accurate"] = int(by_type[ptype]["accurate"]) + 1

                if pred.prediction_error is not None:
                    errors_list: list[Any] = by_type[ptype]["errors"]
                    errors_list.append(pred.prediction_error)

            for ptype_key in by_type:
                data = by_type[ptype_key]
                data["accuracy_rate"] = round(
                    int(data["accurate"]) / max(int(data["total"]), 1), 3
                )
                errors_list = data["errors"]
                if errors_list:
                    data["mean_error"] = round(sum(errors_list) / len(errors_list), 2)
                else:
                    data["mean_error"] = None
                del data["errors"]

            total = len(predictions)
            accurate = sum(1 for p in predictions if p.was_accurate)

            return {
                "total_predictions": total,
                "accuracy": round(accurate / max(total, 1), 3),
                "by_type": by_type,
                "model_version": self.MODEL_VERSION,
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def get_learning_stats(self) -> dict:
        """
        Get comprehensive ML model performance metrics.
        """
        db = SessionLocal()
        try:
            total_outcomes = db.query(CaseOutcome).count()
            total_predictions = db.query(OutcomePrediction).count()
            resolved_predictions = (
                db.query(OutcomePrediction)
                .filter(OutcomePrediction.actual_value.isnot(None))
                .count()
            )

            accuracy_data = self.update_model_accuracy()
            success_rates = self.calculate_success_rate()
            settlement_stats = self.get_average_settlement()

            outcomes = db.query(CaseOutcome).all()
            outcomes_by_type: dict[str, int] = {}
            for o in outcomes:
                otype: str = str(o.final_outcome)
                outcomes_by_type[otype] = outcomes_by_type.get(otype, 0) + 1

            predictions_last_30 = (
                db.query(OutcomePrediction)
                .filter(
                    OutcomePrediction.created_at
                    >= datetime.utcnow() - timedelta(days=30)
                )
                .count()
            )

            predictions_last_7 = (
                db.query(OutcomePrediction)
                .filter(
                    OutcomePrediction.created_at
                    >= datetime.utcnow() - timedelta(days=7)
                )
                .count()
            )

            return {
                "training_data": {
                    "total_outcomes": total_outcomes,
                    "outcomes_by_type": outcomes_by_type,
                    "avg_settlement": settlement_stats.get("average", 0),
                    "success_rate": success_rates.get("success_rate", 0),
                },
                "predictions": {
                    "total": total_predictions,
                    "resolved": resolved_predictions,
                    "pending": total_predictions - resolved_predictions,
                    "last_30_days": predictions_last_30,
                    "last_7_days": predictions_last_7,
                },
                "model_performance": accuracy_data,
                "model_info": {
                    "version": self.MODEL_VERSION,
                    "type": "Bayesian Statistical Model",
                    "features": [
                        "violation_count",
                        "violation_types",
                        "willfulness_ratio",
                        "concrete_harm",
                        "denial_letters",
                        "bureaus_count",
                        "case_score",
                        "settlement_probability",
                    ],
                    "last_updated": datetime.utcnow().isoformat(),
                },
                "confidence_level": min(0.9, total_outcomes / 100),
                "recommendation": self._get_model_recommendation(total_outcomes),
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def _get_model_recommendation(self, total_outcomes: int) -> str:
        """Get recommendation based on training data size"""
        if total_outcomes < 10:
            return "Need more training data. Record at least 10 case outcomes for reliable predictions."
        elif total_outcomes < 50:
            return "Model is learning. Continue recording outcomes to improve accuracy."
        elif total_outcomes < 100:
            return "Good training progress. Predictions are becoming more reliable."
        else:
            return "Model is well-trained. Predictions should be highly reliable."


def record_outcome(client_id: int, outcome_data: dict[str, Any]) -> dict[str, Any]:
    """Convenience function to record a case outcome."""
    service = MLLearningService()
    return service.record_outcome(client_id, outcome_data)


def get_similar_cases(
    violation_types: Optional[list[Any]] = None,
    furnisher_id: Optional[int] = None,
    limit: int = 10,
) -> list[Any]:
    """Convenience function to find similar cases."""
    service = MLLearningService()
    return service.get_similar_cases(violation_types, furnisher_id, limit)


def calculate_success_rate(filters: Optional[dict[Any, Any]] = None) -> dict[str, Any]:
    """Convenience function to calculate success rates."""
    service = MLLearningService()
    return service.calculate_success_rate(filters)


def get_average_settlement(filters: Optional[dict[Any, Any]] = None) -> dict[str, Any]:
    """Convenience function to get average settlements."""
    service = MLLearningService()
    return service.get_average_settlement(filters)


def predict_outcome(client_id: int) -> dict:
    """Convenience function to predict case outcome."""
    service = MLLearningService()
    return service.predict_outcome(client_id)


def predict_settlement_range(client_id: int) -> dict:
    """Convenience function to predict settlement range."""
    service = MLLearningService()
    return service.predict_settlement_range(client_id)


def get_learning_stats() -> dict:
    """Convenience function to get ML stats."""
    service = MLLearningService()
    return service.get_learning_stats()
