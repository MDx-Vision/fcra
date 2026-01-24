"""
Onboarding Service

Manages client onboarding wizard progress and step completion.
Tracks 7 steps: personal_info, id_documents, ssn_card, proof_of_address,
credit_monitoring, agreement, payment.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from database import Client, ClientUpload, OnboardingProgress, SessionLocal

# Define onboarding steps in order
ONBOARDING_STEPS = [
    {
        "key": "personal_info",
        "name": "Personal Information",
        "description": "Basic details like name, date of birth, and address",
        "icon": "user",
        "required_fields": [
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "address_street",
            "address_city",
            "address_state",
            "address_zip",
        ],
    },
    {
        "key": "id_documents",
        "name": "ID Verification",
        "description": "Upload your driver's license or state ID (front and back)",
        "icon": "id-card",
        "required_docs": ["drivers_license_front", "drivers_license_back"],
    },
    {
        "key": "ssn_card",
        "name": "Social Security Card",
        "description": "Upload your Social Security card for identity verification",
        "icon": "credit-card",
        "required_docs": ["ssn_card_front"],
    },
    {
        "key": "proof_of_address",
        "name": "Proof of Address",
        "description": "Upload a recent utility bill or bank statement",
        "icon": "home",
        "required_docs": ["utility_bill"],
    },
    {
        "key": "credit_monitoring",
        "name": "Credit Monitoring",
        "description": "Connect your credit monitoring service for report access",
        "icon": "chart-line",
        "required_fields": ["credit_monitoring_service", "credit_monitoring_username"],
    },
    {
        "key": "agreement",
        "name": "Service Agreement",
        "description": "Review and sign the service agreement",
        "icon": "file-signature",
        "required_fields": ["agreement_signed"],
    },
    {
        "key": "payment",
        "name": "Payment Setup",
        "description": "Complete your payment to start the dispute process",
        "icon": "credit-card",
        "required_fields": ["payment_status"],
    },
]


class OnboardingService:
    """Service for managing client onboarding progress"""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_progress(self, client_id: int) -> Optional[OnboardingProgress]:
        """Get existing progress or create new one for client"""
        # Check if client exists first
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None

        progress = (
            self.db.query(OnboardingProgress)
            .filter(OnboardingProgress.client_id == client_id)
            .first()
        )

        if not progress:
            progress = OnboardingProgress(client_id=client_id)
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)

        return progress

    def get_progress(self, client_id: int) -> Optional[OnboardingProgress]:
        """Get onboarding progress for a client"""
        return (
            self.db.query(OnboardingProgress)
            .filter(OnboardingProgress.client_id == client_id)
            .first()
        )

    def get_progress_summary(self, client_id: int) -> Dict[str, Any]:
        """Get detailed progress summary for client"""
        progress = self.get_or_create_progress(client_id)
        client = self.db.query(Client).filter(Client.id == client_id).first()

        if not client:
            return {"error": "Client not found"}

        # Check each step's actual completion status
        steps_status = []
        completed_count = 0

        for step in ONBOARDING_STEPS:
            is_complete = self._check_step_completion(client, progress, step["key"])
            completed_at = getattr(progress, f"{step['key']}_completed_at", None)

            steps_status.append(
                {
                    "key": step["key"],
                    "name": step["name"],
                    "description": step["description"],
                    "icon": step["icon"],
                    "is_complete": is_complete,
                    "completed_at": completed_at.isoformat() if completed_at else None,
                }
            )

            if is_complete:
                completed_count += 1

        # Calculate percentage
        percentage = int((completed_count / len(ONBOARDING_STEPS)) * 100)

        # Determine current step (first incomplete)
        current_step = None
        for step in steps_status:
            if not step["is_complete"]:
                current_step = step["key"]
                break

        # If all complete, mark as finished
        if completed_count == len(ONBOARDING_STEPS):
            current_step = "complete"

        return {
            "client_id": client_id,
            "steps": steps_status,
            "completed_steps": completed_count,
            "total_steps": len(ONBOARDING_STEPS),
            "percentage": percentage,
            "current_step": current_step,
            "is_complete": completed_count == len(ONBOARDING_STEPS),
        }

    def _check_step_completion(
        self, client: Client, progress: OnboardingProgress, step_key: str
    ) -> bool:
        """Check if a specific step is complete based on actual data"""

        if step_key == "personal_info":
            # Check required personal fields
            return all(
                [
                    client.first_name,
                    client.last_name,
                    client.email,
                    client.address_street,
                    client.address_city,
                    client.address_state,
                    client.address_zip,
                ]
            )

        elif step_key == "id_documents":
            # Check for driver's license uploads
            uploads = (
                self.db.query(ClientUpload)
                .filter(
                    ClientUpload.client_id == client.id,
                    ClientUpload.document_type.in_(
                        [
                            "drivers_license",
                            "drivers_license_front",
                            "id_front",
                            "dl_front",
                        ]
                    ),
                )
                .count()
            )
            return uploads > 0

        elif step_key == "ssn_card":
            # Check for SSN card upload
            uploads = (
                self.db.query(ClientUpload)
                .filter(
                    ClientUpload.client_id == client.id,
                    ClientUpload.document_type.in_(
                        ["ssn_card", "ssn_card_front", "social_security"]
                    ),
                )
                .count()
            )
            return uploads > 0

        elif step_key == "proof_of_address":
            # Check for utility bill upload
            uploads = (
                self.db.query(ClientUpload)
                .filter(
                    ClientUpload.client_id == client.id,
                    ClientUpload.document_type.in_(
                        ["utility_bill", "proof_of_address", "bank_statement"]
                    ),
                )
                .count()
            )
            return uploads > 0

        elif step_key == "credit_monitoring":
            # Check for credit monitoring credentials
            return bool(
                client.credit_monitoring_service and client.credit_monitoring_username
            )

        elif step_key == "agreement":
            # Check if agreement is signed
            return bool(client.agreement_signed)

        elif step_key == "payment":
            # Check payment status
            return client.payment_status in ["paid", "completed", "active"]

        return False

    def complete_step(self, client_id: int, step_key: str) -> Dict[str, Any]:
        """Mark a step as complete"""
        if step_key not in [s["key"] for s in ONBOARDING_STEPS]:
            return {"success": False, "error": "Invalid step key"}

        progress = self.get_or_create_progress(client_id)

        # Set completion flag and timestamp
        setattr(progress, f"{step_key}_completed", True)
        setattr(progress, f"{step_key}_completed_at", datetime.utcnow())

        # Update overall progress
        self._update_overall_progress(progress)

        self.db.commit()
        self.db.refresh(progress)

        return {
            "success": True,
            "step": step_key,
            "completed_at": getattr(progress, f"{step_key}_completed_at").isoformat(),
            "percentage": progress.completion_percentage,
            "is_complete": progress.is_complete,
        }

    def _update_overall_progress(self, progress: OnboardingProgress):
        """Update overall completion percentage and status"""
        completed_count = 0
        first_incomplete = None

        for step in ONBOARDING_STEPS:
            if getattr(progress, f"{step['key']}_completed", False):
                completed_count += 1
            elif first_incomplete is None:
                first_incomplete = step["key"]

        progress.completion_percentage = int(
            (completed_count / len(ONBOARDING_STEPS)) * 100
        )
        progress.current_step = first_incomplete or "complete"

        if completed_count == len(ONBOARDING_STEPS):
            progress.is_complete = True
            progress.completed_at = datetime.utcnow()

    def sync_progress(self, client_id: int) -> Dict[str, Any]:
        """Sync progress based on actual client data (auto-detect completions)"""
        progress = self.get_or_create_progress(client_id)
        client = self.db.query(Client).filter(Client.id == client_id).first()

        if not client:
            return {"success": False, "error": "Client not found"}

        changes = []

        for step in ONBOARDING_STEPS:
            step_key = step["key"]
            is_complete = self._check_step_completion(client, progress, step_key)
            was_complete = getattr(progress, f"{step_key}_completed", False)

            if is_complete and not was_complete:
                setattr(progress, f"{step_key}_completed", True)
                setattr(progress, f"{step_key}_completed_at", datetime.utcnow())
                changes.append(step_key)

        if changes:
            self._update_overall_progress(progress)
            self.db.commit()
            self.db.refresh(progress)

        return {
            "success": True,
            "synced_steps": changes,
            "percentage": progress.completion_percentage,
            "is_complete": progress.is_complete,
        }

    def get_next_step(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Get the next incomplete step for a client"""
        summary = self.get_progress_summary(client_id)

        if summary.get("is_complete"):
            return None

        for step in summary["steps"]:
            if not step["is_complete"]:
                return step

        return None

    def reset_progress(self, client_id: int) -> Dict[str, Any]:
        """Reset all onboarding progress for a client"""
        progress = (
            self.db.query(OnboardingProgress)
            .filter(OnboardingProgress.client_id == client_id)
            .first()
        )

        if progress:
            self.db.delete(progress)
            self.db.commit()
            return {"success": True, "message": "Progress reset"}

        return {"success": True, "message": "No progress to reset"}

    def get_all_incomplete(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all clients with incomplete onboarding (most recent first)"""
        # Get clients who have onboarding progress but not complete
        incomplete = (
            self.db.query(OnboardingProgress)
            .filter(OnboardingProgress.is_complete == False)
            .order_by(OnboardingProgress.created_at.desc())
            .limit(limit)
            .all()
        )

        results = []
        for progress in incomplete:
            client = (
                self.db.query(Client).filter(Client.id == progress.client_id).first()
            )
            if client:
                results.append(
                    {
                        "client_id": client.id,
                        "client_name": f"{client.first_name or ''} {client.last_name or ''}".strip()
                        or client.name
                        or "Unknown",
                        "email": client.email,
                        "percentage": progress.completion_percentage,
                        "current_step": progress.current_step,
                        "created_at": (
                            progress.created_at.isoformat()
                            if progress.created_at
                            else None
                        ),
                    }
                )

        return results


def get_onboarding_service(db: Session = None) -> OnboardingService:
    """Factory function to get OnboardingService instance"""
    if db is None:
        db = SessionLocal()
    return OnboardingService(db)
