"""
Attorney Referral Handoff Service

Manages attorney network and FCRA litigation referrals under §§616-617.
Handles the complete lifecycle from referral to settlement/judgment.

Key Features:
- Attorney network database management
- Case package generation with evidence
- Referral status tracking
- Fee agreement and commission tracking
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AttorneyReferralServiceError(Exception):
    """Custom exception for attorney referral service errors"""

    def __init__(self, message: str, error_code: str, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# Referral status workflow
REFERRAL_STATUSES = {
    "pending": "Pending - Not yet contacted",
    "contacted": "Contacted - Awaiting response",
    "accepted": "Accepted - Attorney took case",
    "declined": "Declined - Attorney passed",
    "intake": "Intake - Gathering client info",
    "retainer_signed": "Retainer Signed - Agreement in place",
    "filed": "Filed - Complaint filed in court",
    "discovery": "Discovery - Case in progress",
    "mediation": "Mediation - Settlement negotiations",
    "trial": "Trial - Case going to trial",
    "settled": "Settled - Case resolved via settlement",
    "won": "Won - Judgment for client",
    "lost": "Lost - Judgment for defendant",
    "dismissed": "Dismissed - Case dismissed",
    "withdrawn": "Withdrawn - Client withdrew",
    "closed": "Closed - Case complete",
}

# Violation types for case packages
VIOLATION_TYPES = {
    "failure_to_investigate": "Failure to conduct reasonable investigation (§611)",
    "inaccurate_reporting": "Reporting inaccurate information (§623)",
    "failure_to_correct": "Failure to correct after dispute (§611)",
    "reinsertion": "Reinsertion without proper notice (§611)",
    "willful_noncompliance": "Willful noncompliance (§616)",
    "negligent_noncompliance": "Negligent noncompliance (§617)",
    "obsolete_info": "Reporting obsolete information (§605)",
    "mixed_file": "Mixed file - reporting another person's data",
    "unauthorized_access": "Unauthorized access to credit report (§604)",
    "failure_to_notify": "Failure to notify of adverse action (§615)",
}

# Fee arrangement types
FEE_ARRANGEMENTS = {
    "contingency": "Contingency - No fee unless recovery",
    "hourly": "Hourly - Billed by the hour",
    "hybrid": "Hybrid - Reduced hourly + contingency",
    "flat": "Flat Fee - Fixed amount",
}

# Practice areas for attorney matching
PRACTICE_AREAS = ["FCRA", "FDCPA", "TCPA", "FCBA", "RESPA", "TILA", "SCRA"]


class AttorneyReferralService:
    """Service for managing attorney referrals and network"""

    def __init__(self, session: Session = None):
        """Initialize with optional database session"""
        self._session = session
        self._owns_session = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._owns_session and self._session:
            self._session.close()

    @property
    def session(self) -> Session:
        """Get or create database session"""
        if self._session is None:
            from database import get_db

            self._session = next(get_db())
        return self._session

    def _success_response(
        self, data: Any = None, message: str = None
    ) -> Dict[str, Any]:
        """Create a standardized success response"""
        response = {"success": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        return response

    def _error_response(
        self, message: str, error_code: str, details: Dict = None
    ) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "success": False,
            "error": message,
            "error_code": error_code,
            "details": details or {},
        }

    # ==================== Attorney Network CRUD ====================

    def create_attorney(
        self,
        first_name: str,
        last_name: str,
        email: str,
        firm_name: str = None,
        bar_number: str = None,
        bar_state: str = None,
        phone: str = None,
        practice_areas: List[str] = None,
        states_licensed: List[str] = None,
        fee_structure: str = "contingency",
        contingency_percent: float = None,
        referral_fee_percent: float = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Add a new attorney to the network"""
        from database import AttorneyNetworkMember

        try:
            # Validate fee structure
            if fee_structure and fee_structure not in FEE_ARRANGEMENTS:
                return self._error_response(
                    "Invalid fee structure",
                    "INVALID_FEE_STRUCTURE",
                    {"valid_structures": list(FEE_ARRANGEMENTS.keys())},
                )

            attorney = AttorneyNetworkMember(
                first_name=first_name,
                last_name=last_name,
                email=email,
                firm_name=firm_name,
                bar_number=bar_number,
                bar_state=bar_state.upper() if bar_state else None,
                phone=phone,
                practice_areas=practice_areas or ["FCRA"],
                states_licensed=states_licensed or [],
                fee_structure=fee_structure,
                contingency_percent=contingency_percent,
                referral_fee_percent=referral_fee_percent,
                onboarded_at=datetime.utcnow(),
                **kwargs,
            )

            self.session.add(attorney)
            self.session.commit()

            logger.info(
                f"Created attorney: {first_name} {last_name} (ID: {attorney.id})"
            )

            return self._success_response(
                attorney.to_dict(), "Attorney added to network"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating attorney: {e}")
            return self._error_response(str(e), "CREATE_ERROR")

    def get_attorney(self, attorney_id: int) -> Optional[Dict[str, Any]]:
        """Get an attorney by ID"""
        from database import AttorneyNetworkMember

        attorney = (
            self.session.query(AttorneyNetworkMember).filter_by(id=attorney_id).first()
        )

        return attorney.to_dict() if attorney else None

    def get_all_attorneys(
        self,
        status: str = None,
        practice_area: str = None,
        state: str = None,
        preferred_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get all attorneys with optional filtering"""
        from database import AttorneyNetworkMember

        query = self.session.query(AttorneyNetworkMember)

        if status:
            query = query.filter(AttorneyNetworkMember.status == status)
        if preferred_only:
            query = query.filter(AttorneyNetworkMember.is_preferred == True)

        attorneys = query.order_by(
            AttorneyNetworkMember.is_preferred.desc(),
            AttorneyNetworkMember.cases_won.desc(),
        ).all()

        # Filter by practice area and state (JSON fields)
        results = []
        for a in attorneys:
            if practice_area and practice_area not in (a.practice_areas or []):
                continue
            if state and state.upper() not in (a.states_licensed or []):
                continue
            results.append(a.to_dict())

        return results

    def update_attorney(
        self, attorney_id: int, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update attorney information"""
        from database import AttorneyNetworkMember

        try:
            attorney = (
                self.session.query(AttorneyNetworkMember)
                .filter_by(id=attorney_id)
                .first()
            )

            if not attorney:
                return self._error_response(
                    "Attorney not found",
                    "ATTORNEY_NOT_FOUND",
                    {"attorney_id": attorney_id},
                )

            # Update allowed fields
            allowed_fields = [
                "first_name",
                "last_name",
                "email",
                "phone",
                "fax",
                "firm_name",
                "firm_website",
                "bar_number",
                "bar_state",
                "address_line1",
                "address_line2",
                "city",
                "state",
                "zip_code",
                "practice_areas",
                "states_licensed",
                "fee_structure",
                "contingency_percent",
                "referral_fee_percent",
                "status",
                "is_preferred",
                "specialties_notes",
                "intake_requirements",
                "notes",
            ]

            for field, value in updates.items():
                if field in allowed_fields and hasattr(attorney, field):
                    setattr(attorney, field, value)

            self.session.commit()

            return self._success_response(attorney.to_dict(), "Attorney updated")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating attorney: {e}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def find_matching_attorneys(
        self,
        client_state: str,
        violation_types: List[str] = None,
        min_acceptance_rate: float = 0,
    ) -> List[Dict[str, Any]]:
        """Find attorneys who match case criteria"""
        from database import AttorneyNetworkMember

        attorneys = (
            self.session.query(AttorneyNetworkMember)
            .filter(AttorneyNetworkMember.status == "active")
            .all()
        )

        matches = []
        for a in attorneys:
            # Check state license
            if client_state and client_state.upper() not in (a.states_licensed or []):
                continue

            # Check FCRA practice
            if "FCRA" not in (a.practice_areas or []):
                continue

            # Check acceptance rate
            if a.cases_referred > 0:
                rate = (a.cases_accepted / a.cases_referred) * 100
                if rate < min_acceptance_rate:
                    continue

            match_data = a.to_dict()
            match_data["match_score"] = self._calculate_match_score(a, violation_types)
            matches.append(match_data)

        # Sort by match score and preferred status
        matches.sort(
            key=lambda x: (x.get("is_preferred", False), x.get("match_score", 0)),
            reverse=True,
        )

        return matches

    def _calculate_match_score(
        self, attorney, violation_types: List[str] = None
    ) -> int:
        """Calculate how well an attorney matches a case"""
        score = 0

        # Preferred attorneys get a boost
        if attorney.is_preferred:
            score += 50

        # Win rate
        if attorney.cases_referred > 0:
            acceptance = attorney.cases_accepted / attorney.cases_referred
            score += int(acceptance * 30)

        # Settlement track record
        if attorney.cases_settled > 0 and attorney.total_recoveries > 0:
            if attorney.avg_settlement > 10000:
                score += 20
            elif attorney.avg_settlement > 5000:
                score += 10

        # Fast resolution
        if attorney.avg_resolution_days and attorney.avg_resolution_days < 180:
            score += 10

        return min(score, 100)

    # ==================== Referral CRUD ====================

    def create_referral(
        self,
        client_id: int,
        attorney_id: int = None,
        referral_reason: str = None,
        estimated_value: float = None,
        violation_types: List[str] = None,
        bureaus_involved: List[str] = None,
        furnishers_involved: List[str] = None,
        dispute_rounds: int = 0,
        case_id: int = None,
        staff_id: int = None,
    ) -> Dict[str, Any]:
        """Create a new attorney referral"""
        from database import AttorneyNetworkMember, AttorneyReferral, Client

        try:
            # Validate client
            client = self.session.query(Client).filter_by(id=client_id).first()
            if not client:
                return self._error_response(
                    "Client not found", "CLIENT_NOT_FOUND", {"client_id": client_id}
                )

            # Get attorney info if provided
            attorney_name = None
            attorney_firm = None
            attorney_email = None
            attorney_phone = None

            if attorney_id:
                attorney = (
                    self.session.query(AttorneyNetworkMember)
                    .filter_by(id=attorney_id)
                    .first()
                )
                if attorney:
                    attorney_name = f"{attorney.first_name} {attorney.last_name}"
                    attorney_firm = attorney.firm_name
                    attorney_email = attorney.email
                    attorney_phone = attorney.phone

            referral = AttorneyReferral(
                client_id=client_id,
                case_id=case_id,
                attorney_id=attorney_id,
                attorney_name=attorney_name,
                attorney_firm=attorney_firm,
                attorney_email=attorney_email,
                attorney_phone=attorney_phone,
                referral_reason=referral_reason,
                estimated_value=estimated_value,
                violation_types=violation_types or [],
                violation_count=len(violation_types) if violation_types else 0,
                bureaus_involved=bureaus_involved or [],
                furnishers_involved=furnishers_involved or [],
                dispute_rounds=dispute_rounds,
                status="pending",
                referred_at=datetime.utcnow(),
                assigned_staff_id=staff_id,
            )

            self.session.add(referral)
            self.session.commit()

            # Update attorney stats
            if attorney_id:
                self._update_attorney_referral_count(attorney_id)

            logger.info(f"Created referral {referral.id} for client {client_id}")

            return self._success_response(referral.to_dict(), "Referral created")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating referral: {e}")
            return self._error_response(str(e), "CREATE_ERROR")

    def get_referral(self, referral_id: int) -> Optional[Dict[str, Any]]:
        """Get a referral by ID"""
        from database import AttorneyReferral

        referral = (
            self.session.query(AttorneyReferral).filter_by(id=referral_id).first()
        )

        return referral.to_dict() if referral else None

    def get_client_referrals(self, client_id: int) -> List[Dict[str, Any]]:
        """Get all referrals for a client"""
        from database import AttorneyReferral

        referrals = (
            self.session.query(AttorneyReferral)
            .filter_by(client_id=client_id)
            .order_by(AttorneyReferral.created_at.desc())
            .all()
        )

        return [r.to_dict() for r in referrals]

    def get_attorney_referrals(self, attorney_id: int) -> List[Dict[str, Any]]:
        """Get all referrals to a specific attorney"""
        from database import AttorneyReferral

        referrals = (
            self.session.query(AttorneyReferral)
            .filter_by(attorney_id=attorney_id)
            .order_by(AttorneyReferral.created_at.desc())
            .all()
        )

        return [r.to_dict() for r in referrals]

    def update_referral(
        self, referral_id: int, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a referral"""
        from database import AttorneyReferral

        try:
            referral = (
                self.session.query(AttorneyReferral).filter_by(id=referral_id).first()
            )

            if not referral:
                return self._error_response("Referral not found", "REFERRAL_NOT_FOUND")

            # Update allowed fields
            allowed_fields = [
                "referral_reason",
                "case_summary",
                "estimated_value",
                "violation_types",
                "violation_count",
                "bureaus_involved",
                "furnishers_involved",
                "notes",
                "assigned_staff_id",
                "fee_arrangement",
                "contingency_percent",
                "referral_fee_percent",
                "referral_fee_flat",
            ]

            for field, value in updates.items():
                if field in allowed_fields and hasattr(referral, field):
                    setattr(referral, field, value)

            self.session.commit()

            return self._success_response(referral.to_dict(), "Referral updated")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating referral: {e}")
            return self._error_response(str(e), "UPDATE_ERROR")

    # ==================== Status Workflow ====================

    def update_referral_status(
        self, referral_id: int, new_status: str, notes: str = None
    ) -> Dict[str, Any]:
        """Update referral status with timestamp tracking"""
        from database import AttorneyReferral

        try:
            referral = (
                self.session.query(AttorneyReferral).filter_by(id=referral_id).first()
            )

            if not referral:
                return self._error_response("Referral not found", "REFERRAL_NOT_FOUND")

            if new_status not in REFERRAL_STATUSES:
                return self._error_response(
                    "Invalid status",
                    "INVALID_STATUS",
                    {"valid_statuses": list(REFERRAL_STATUSES.keys())},
                )

            old_status = referral.status
            referral.status = new_status
            now = datetime.utcnow()

            # Update appropriate timestamps
            if new_status == "contacted":
                referral.attorney_contacted_at = now
            elif new_status == "accepted":
                referral.attorney_response_at = now
                referral.attorney_accepted = True
                self._update_attorney_acceptance(referral.attorney_id, True)
            elif new_status == "declined":
                referral.attorney_response_at = now
                referral.attorney_accepted = False
            elif new_status == "intake":
                referral.intake_completed_at = now
            elif new_status == "retainer_signed":
                referral.retainer_signed_at = now
                referral.fee_agreement_signed = True
            elif new_status == "filed":
                referral.complaint_filed_at = now
            elif new_status == "discovery":
                referral.discovery_started_at = now
            elif new_status in [
                "settled",
                "won",
                "lost",
                "dismissed",
                "withdrawn",
                "closed",
            ]:
                referral.resolved_at = now
                referral.outcome = new_status

            if notes:
                existing_notes = referral.notes or ""
                referral.notes = f"{existing_notes}\n[{now.isoformat()}] {old_status} -> {new_status}: {notes}".strip()

            self.session.commit()

            return self._success_response(
                referral.to_dict(), f"Status updated to {new_status}"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating status: {e}")
            return self._error_response(str(e), "STATUS_UPDATE_ERROR")

    def mark_attorney_response(
        self, referral_id: int, accepted: bool, decline_reason: str = None
    ) -> Dict[str, Any]:
        """Record attorney's response to referral"""
        from database import AttorneyReferral

        try:
            referral = (
                self.session.query(AttorneyReferral).filter_by(id=referral_id).first()
            )

            if not referral:
                return self._error_response("Referral not found", "REFERRAL_NOT_FOUND")

            referral.attorney_response_at = datetime.utcnow()
            referral.attorney_accepted = accepted

            if accepted:
                referral.status = "accepted"
                self._update_attorney_acceptance(referral.attorney_id, True)
            else:
                referral.status = "declined"
                referral.decline_reason = decline_reason

            self.session.commit()

            return self._success_response(
                referral.to_dict(), "Accepted" if accepted else "Declined"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error marking response: {e}")
            return self._error_response(str(e), "RESPONSE_ERROR")

    def record_case_filed(
        self, referral_id: int, court_case_number: str = None
    ) -> Dict[str, Any]:
        """Record when complaint is filed in court"""
        from database import AttorneyReferral

        try:
            referral = (
                self.session.query(AttorneyReferral).filter_by(id=referral_id).first()
            )

            if not referral:
                return self._error_response("Referral not found", "REFERRAL_NOT_FOUND")

            referral.complaint_filed_at = datetime.utcnow()
            referral.court_case_number = court_case_number
            referral.status = "filed"

            self.session.commit()

            return self._success_response(referral.to_dict(), "Case filed recorded")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording case filed: {e}")
            return self._error_response(str(e), "FILE_ERROR")

    def record_settlement(
        self,
        referral_id: int,
        settlement_amount: float,
        actual_damages: float = None,
        statutory_damages: float = None,
        punitive_damages: float = None,
        attorney_fees_awarded: float = None,
    ) -> Dict[str, Any]:
        """Record case settlement"""
        from database import AttorneyReferral

        try:
            referral = (
                self.session.query(AttorneyReferral).filter_by(id=referral_id).first()
            )

            if not referral:
                return self._error_response("Referral not found", "REFERRAL_NOT_FOUND")

            referral.resolved_at = datetime.utcnow()
            referral.status = "settled"
            referral.outcome = "settled"
            referral.settlement_amount = settlement_amount
            referral.actual_damages = actual_damages
            referral.statutory_damages = statutory_damages
            referral.punitive_damages = punitive_damages
            referral.attorney_fees_awarded = attorney_fees_awarded

            # Calculate referral fee
            referral.referral_fee_earned = referral.calculate_referral_fee()

            # Update attorney stats
            self._update_attorney_settlement_stats(
                referral.attorney_id, referral.get_total_recovery()
            )

            self.session.commit()

            return self._success_response(
                referral.to_dict(), f"Settlement recorded: ${settlement_amount:,.2f}"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording settlement: {e}")
            return self._error_response(str(e), "SETTLEMENT_ERROR")

    def record_fee_received(self, referral_id: int, amount: float) -> Dict[str, Any]:
        """Record referral fee payment received"""
        from database import AttorneyReferral

        try:
            referral = (
                self.session.query(AttorneyReferral).filter_by(id=referral_id).first()
            )

            if not referral:
                return self._error_response("Referral not found", "REFERRAL_NOT_FOUND")

            referral.referral_fee_received = amount
            referral.referral_fee_received_at = datetime.utcnow()

            self.session.commit()

            return self._success_response(
                referral.to_dict(), f"Fee received: ${amount:,.2f}"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording fee: {e}")
            return self._error_response(str(e), "FEE_ERROR")

    # ==================== Case Package Generation ====================

    def generate_case_package(self, referral_id: int) -> Dict[str, Any]:
        """Generate a case package for attorney intake"""
        from database import AttorneyReferral, Client, CRAResponse, DisputeItem

        try:
            referral = (
                self.session.query(AttorneyReferral).filter_by(id=referral_id).first()
            )

            if not referral:
                return self._error_response("Referral not found", "REFERRAL_NOT_FOUND")

            client = self.session.query(Client).filter_by(id=referral.client_id).first()

            if not client:
                return self._error_response("Client not found", "CLIENT_NOT_FOUND")

            # Build case package
            package = {
                "generated_at": datetime.utcnow().isoformat(),
                "referral_id": referral_id,
                # Client Info
                "client": {
                    "name": f"{client.first_name} {client.last_name}",
                    "email": client.email,
                    "phone": client.phone,
                    "address": {
                        "street": client.address_street,
                        "city": client.address_city,
                        "state": client.address_state,
                        "zip": client.address_zip,
                    },
                    "ssn_last_four": client.ssn_last_four,
                },
                # Case Summary
                "case_summary": {
                    "referral_reason": referral.referral_reason,
                    "estimated_value": referral.estimated_value,
                    "dispute_rounds": referral.dispute_rounds,
                    "bureaus_involved": referral.bureaus_involved or [],
                    "furnishers_involved": referral.furnishers_involved or [],
                },
                # Violations
                "violations": {
                    "types": referral.violation_types or [],
                    "count": referral.violation_count,
                    "details": [
                        {"code": v, "description": VIOLATION_TYPES.get(v, v)}
                        for v in (referral.violation_types or [])
                    ],
                },
                # Timeline
                "timeline": self._build_dispute_timeline(referral.client_id),
                # Evidence
                "evidence": self._gather_evidence(referral.client_id),
            }

            # Store package path (would be actual file in production)
            referral.case_package_generated_at = datetime.utcnow()

            self.session.commit()

            return self._success_response(package, "Case package generated")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error generating case package: {e}")
            return self._error_response(str(e), "PACKAGE_ERROR")

    def _build_dispute_timeline(self, client_id: int) -> List[Dict]:
        """Build timeline of dispute activity"""
        from database import BureauDisputeTracking, CRAResponse, DisputeItem

        timeline = []

        # Get dispute items
        items = (
            self.session.query(DisputeItem)
            .filter_by(client_id=client_id)
            .order_by(DisputeItem.created_at)
            .all()
        )

        for item in items:
            timeline.append(
                {
                    "date": item.created_at.isoformat() if item.created_at else None,
                    "type": "dispute_created",
                    "description": f"Dispute created for {item.creditor_name}",
                    "status": item.status,
                }
            )

        # Get bureau tracking
        tracking = (
            self.session.query(BureauDisputeTracking)
            .filter_by(client_id=client_id)
            .order_by(BureauDisputeTracking.sent_date)
            .all()
        )

        for t in tracking:
            timeline.append(
                {
                    "date": t.sent_date.isoformat() if t.sent_date else None,
                    "type": "letter_sent",
                    "description": f"Dispute letter sent to {t.bureau}",
                    "round": t.dispute_round,
                }
            )
            if t.response_date:
                timeline.append(
                    {
                        "date": t.response_date.isoformat(),
                        "type": "response_received",
                        "description": f"Response from {t.bureau}: {t.response_type}",
                    }
                )

        # Sort by date
        timeline.sort(key=lambda x: x.get("date") or "")

        return timeline

    def _gather_evidence(self, client_id: int) -> Dict[str, Any]:
        """Gather evidence documents for the case"""
        from database import ClientUpload, CRAResponse, DisputeLetter

        evidence = {
            "dispute_letters": [],
            "bureau_responses": [],
            "supporting_documents": [],
            "credit_reports": [],
        }

        # Dispute letters
        letters = self.session.query(DisputeLetter).filter_by(client_id=client_id).all()

        for letter in letters:
            evidence["dispute_letters"].append(
                {
                    "id": letter.id,
                    "bureau": letter.bureau,
                    "date": (
                        letter.created_at.isoformat() if letter.created_at else None
                    ),
                    "round": letter.dispute_round,
                    "path": letter.letter_path,
                }
            )

        # Bureau responses
        responses = self.session.query(CRAResponse).filter_by(client_id=client_id).all()

        for response in responses:
            evidence["bureau_responses"].append(
                {
                    "id": response.id,
                    "bureau": response.bureau,
                    "date": (
                        response.received_at.isoformat()
                        if response.received_at
                        else None
                    ),
                    "result": response.result_type,
                    "path": response.document_path,
                }
            )

        # Client uploads
        uploads = self.session.query(ClientUpload).filter_by(client_id=client_id).all()

        for upload in uploads:
            evidence["supporting_documents"].append(
                {
                    "id": upload.id,
                    "type": upload.document_type,
                    "date": (
                        upload.created_at.isoformat() if upload.created_at else None
                    ),
                    "path": upload.file_path,
                }
            )

        return evidence

    # ==================== Statistics ====================

    def get_referral_statistics(self) -> Dict[str, Any]:
        """Get overall referral statistics"""
        from sqlalchemy import func

        from database import AttorneyReferral

        try:
            # By status
            status_counts = dict(
                self.session.query(
                    AttorneyReferral.status, func.count(AttorneyReferral.id)
                )
                .group_by(AttorneyReferral.status)
                .all()
            )

            # Total settlements
            total_settlements = (
                self.session.query(func.sum(AttorneyReferral.settlement_amount))
                .filter(AttorneyReferral.settlement_amount.isnot(None))
                .scalar()
                or 0
            )

            # Total fees earned
            total_fees = (
                self.session.query(func.sum(AttorneyReferral.referral_fee_received))
                .filter(AttorneyReferral.referral_fee_received.isnot(None))
                .scalar()
                or 0
            )

            # Fees pending
            fees_pending = (
                self.session.query(func.sum(AttorneyReferral.referral_fee_earned))
                .filter(
                    AttorneyReferral.referral_fee_earned.isnot(None),
                    AttorneyReferral.referral_fee_received.is_(None),
                )
                .scalar()
                or 0
            )

            # Active cases
            active_statuses = [
                "accepted",
                "intake",
                "retainer_signed",
                "filed",
                "discovery",
                "mediation",
                "trial",
            ]
            active_count = (
                self.session.query(AttorneyReferral)
                .filter(AttorneyReferral.status.in_(active_statuses))
                .count()
            )

            # Acceptance rate
            total_referred = self.session.query(AttorneyReferral).count()
            total_accepted = status_counts.get("accepted", 0) + sum(
                status_counts.get(s, 0) for s in active_statuses if s != "accepted"
            )
            acceptance_rate = (
                (total_accepted / total_referred * 100) if total_referred > 0 else 0
            )

            return self._success_response(
                {
                    "by_status": status_counts,
                    "total_referrals": total_referred,
                    "active_cases": active_count,
                    "total_settlements": total_settlements,
                    "total_fees_received": total_fees,
                    "fees_pending": fees_pending,
                    "acceptance_rate": round(acceptance_rate, 1),
                }
            )

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return self._error_response(str(e), "STATS_ERROR")

    def get_pending_referrals(self) -> List[Dict[str, Any]]:
        """Get referrals awaiting attorney response"""
        from database import AttorneyReferral

        referrals = (
            self.session.query(AttorneyReferral)
            .filter(AttorneyReferral.status.in_(["pending", "contacted"]))
            .order_by(AttorneyReferral.referred_at)
            .all()
        )

        return [r.to_dict() for r in referrals]

    def get_active_cases(self) -> List[Dict[str, Any]]:
        """Get cases that are currently in litigation"""
        from database import AttorneyReferral

        active_statuses = [
            "accepted",
            "intake",
            "retainer_signed",
            "filed",
            "discovery",
            "mediation",
            "trial",
        ]

        referrals = (
            self.session.query(AttorneyReferral)
            .filter(AttorneyReferral.status.in_(active_statuses))
            .order_by(AttorneyReferral.complaint_filed_at.desc())
            .all()
        )

        return [r.to_dict() for r in referrals]

    # ==================== Helper Methods ====================

    def _update_attorney_referral_count(self, attorney_id: int):
        """Update attorney's referral count"""
        from database import AttorneyNetworkMember

        if not attorney_id:
            return

        attorney = (
            self.session.query(AttorneyNetworkMember).filter_by(id=attorney_id).first()
        )

        if attorney:
            attorney.cases_referred = (attorney.cases_referred or 0) + 1
            attorney.last_referral_at = datetime.utcnow()

    def _update_attorney_acceptance(self, attorney_id: int, accepted: bool):
        """Update attorney's acceptance count"""
        from database import AttorneyNetworkMember

        if not attorney_id:
            return

        attorney = (
            self.session.query(AttorneyNetworkMember).filter_by(id=attorney_id).first()
        )

        if attorney and accepted:
            attorney.cases_accepted = (attorney.cases_accepted or 0) + 1

    def _update_attorney_settlement_stats(
        self, attorney_id: int, recovery_amount: float
    ):
        """Update attorney's settlement statistics"""
        from database import AttorneyNetworkMember

        if not attorney_id:
            return

        attorney = (
            self.session.query(AttorneyNetworkMember).filter_by(id=attorney_id).first()
        )

        if attorney:
            attorney.cases_settled = (attorney.cases_settled or 0) + 1
            attorney.total_recoveries = (
                attorney.total_recoveries or 0
            ) + recovery_amount

            # Recalculate average
            if attorney.cases_settled > 0:
                attorney.avg_settlement = (
                    attorney.total_recoveries / attorney.cases_settled
                )


def get_attorney_referral_service(session: Session = None) -> AttorneyReferralService:
    """Factory function to get AttorneyReferralService instance"""
    return AttorneyReferralService(session=session)
