"""
Drip Campaign Service for Brightpath Ascend FCRA Platform

Manages automated email sequences (drip campaigns) for client follow-ups.
Handles campaign CRUD, enrollment, and scheduled email sending.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import (
    Client,
    DripCampaign,
    DripEmailLog,
    DripEnrollment,
    DripStep,
    EmailTemplate,
    SessionLocal,
)
from services.email_service import send_email
from services.email_template_service import EmailTemplateService

# Trigger types for campaigns
TRIGGER_TYPES = {
    "signup": "New Client Signup",
    "status_change": "Status Change",
    "report_uploaded": "Credit Report Uploaded",
    "analysis_complete": "Analysis Complete",
    "dispute_sent": "Dispute Sent",
    "response_received": "Bureau Response Received",
    "manual": "Manual Enrollment",
    "tag_added": "Tag Added",
}

# Status values for enrollments
ENROLLMENT_STATUSES = {
    "active": "Active",
    "paused": "Paused",
    "completed": "Completed",
    "cancelled": "Cancelled",
}


class DripCampaignService:
    """Service for managing drip campaigns"""

    @staticmethod
    def get_trigger_types() -> Dict[str, str]:
        """Get all trigger types"""
        return TRIGGER_TYPES

    @staticmethod
    def get_enrollment_statuses() -> Dict[str, str]:
        """Get all enrollment statuses"""
        return ENROLLMENT_STATUSES

    # ==================== CAMPAIGN CRUD ====================

    @staticmethod
    def create_campaign(
        name: str,
        trigger_type: str,
        trigger_value: str = None,
        description: str = None,
        send_window_start: int = 9,
        send_window_end: int = 17,
        send_on_weekends: bool = False,
        created_by_id: int = None,
        steps: List[Dict] = None,
        session=None,
    ) -> Dict[str, Any]:
        """
        Create a new drip campaign.

        Args:
            name: Campaign name
            trigger_type: What triggers enrollment (signup, status_change, etc.)
            trigger_value: Value for the trigger (e.g., status value)
            description: Campaign description
            send_window_start: Hour to start sending (0-23)
            send_window_end: Hour to stop sending (0-23)
            send_on_weekends: Whether to send on weekends
            created_by_id: Staff ID who created this
            steps: Optional list of step dicts to create

        Returns:
            Dict with success status and campaign data
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            if trigger_type not in TRIGGER_TYPES:
                return {
                    "success": False,
                    "error": f"Invalid trigger type: {trigger_type}",
                }

            campaign = DripCampaign(
                name=name,
                description=description,
                trigger_type=trigger_type,
                trigger_value=trigger_value,
                send_window_start=send_window_start,
                send_window_end=send_window_end,
                send_on_weekends=send_on_weekends,
                created_by_id=created_by_id,
                is_active=True,
            )

            session.add(campaign)
            session.flush()  # Get the campaign ID

            # Create steps if provided
            if steps:
                for i, step_data in enumerate(steps):
                    step = DripStep(
                        campaign_id=campaign.id,
                        step_order=i + 1,
                        name=step_data.get("name"),
                        delay_days=step_data.get("delay_days", 1),
                        delay_hours=step_data.get("delay_hours", 0),
                        email_template_id=step_data.get("email_template_id"),
                        subject=step_data.get("subject"),
                        html_content=step_data.get("html_content"),
                        condition_type=step_data.get("condition_type"),
                        condition_value=step_data.get("condition_value"),
                        is_active=True,
                    )
                    session.add(step)

            session.commit()
            session.refresh(campaign)

            return {
                "success": True,
                "campaign_id": campaign.id,
                "message": f"Campaign '{name}' created successfully",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def update_campaign(
        campaign_id: int,
        name: str = None,
        description: str = None,
        trigger_type: str = None,
        trigger_value: str = None,
        send_window_start: int = None,
        send_window_end: int = None,
        send_on_weekends: bool = None,
        is_active: bool = None,
        session=None,
    ) -> Dict[str, Any]:
        """Update a campaign"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            campaign = (
                session.query(DripCampaign)
                .filter(DripCampaign.id == campaign_id)
                .first()
            )

            if not campaign:
                return {"success": False, "error": "Campaign not found"}

            if name is not None:
                campaign.name = name
            if description is not None:
                campaign.description = description
            if trigger_type is not None:
                if trigger_type not in TRIGGER_TYPES:
                    return {
                        "success": False,
                        "error": f"Invalid trigger type: {trigger_type}",
                    }
                campaign.trigger_type = trigger_type
            if trigger_value is not None:
                campaign.trigger_value = trigger_value
            if send_window_start is not None:
                campaign.send_window_start = send_window_start
            if send_window_end is not None:
                campaign.send_window_end = send_window_end
            if send_on_weekends is not None:
                campaign.send_on_weekends = send_on_weekends
            if is_active is not None:
                campaign.is_active = is_active

            campaign.updated_at = datetime.utcnow()
            session.commit()

            return {"success": True, "message": f"Campaign '{campaign.name}' updated"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def delete_campaign(campaign_id: int, session=None) -> Dict[str, Any]:
        """Delete a campaign and all its steps/enrollments"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            campaign = (
                session.query(DripCampaign)
                .filter(DripCampaign.id == campaign_id)
                .first()
            )

            if not campaign:
                return {"success": False, "error": "Campaign not found"}

            name = campaign.name
            session.delete(campaign)
            session.commit()

            return {"success": True, "message": f"Campaign '{name}' deleted"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_campaign(
        campaign_id: int, include_steps: bool = True, session=None
    ) -> Optional[Dict[str, Any]]:
        """Get a campaign by ID"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            campaign = (
                session.query(DripCampaign)
                .filter(DripCampaign.id == campaign_id)
                .first()
            )

            if not campaign:
                return None

            result = {
                "id": campaign.id,
                "name": campaign.name,
                "description": campaign.description,
                "trigger_type": campaign.trigger_type,
                "trigger_type_label": TRIGGER_TYPES.get(
                    campaign.trigger_type, campaign.trigger_type
                ),
                "trigger_value": campaign.trigger_value,
                "is_active": campaign.is_active,
                "send_window_start": campaign.send_window_start,
                "send_window_end": campaign.send_window_end,
                "send_on_weekends": campaign.send_on_weekends,
                "total_enrolled": campaign.total_enrolled,
                "total_completed": campaign.total_completed,
                "created_by_id": campaign.created_by_id,
                "created_at": (
                    campaign.created_at.isoformat() if campaign.created_at else None
                ),
                "updated_at": (
                    campaign.updated_at.isoformat() if campaign.updated_at else None
                ),
            }

            if include_steps:
                result["steps"] = [
                    {
                        "id": s.id,
                        "step_order": s.step_order,
                        "name": s.name,
                        "delay_days": s.delay_days,
                        "delay_hours": s.delay_hours,
                        "email_template_id": s.email_template_id,
                        "subject": s.subject,
                        "has_custom_content": bool(s.html_content),
                        "condition_type": s.condition_type,
                        "condition_value": s.condition_value,
                        "is_active": s.is_active,
                    }
                    for s in sorted(campaign.steps, key=lambda x: x.step_order)
                ]
                result["step_count"] = len(result["steps"])

            return result

        finally:
            if close_session:
                session.close()

    @staticmethod
    def list_campaigns(
        is_active: bool = None,
        trigger_type: str = None,
        session=None,
    ) -> List[Dict[str, Any]]:
        """List all campaigns"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            query = session.query(DripCampaign)

            if is_active is not None:
                query = query.filter(DripCampaign.is_active == is_active)
            if trigger_type:
                query = query.filter(DripCampaign.trigger_type == trigger_type)

            campaigns = query.order_by(DripCampaign.name).all()

            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "trigger_type": c.trigger_type,
                    "trigger_type_label": TRIGGER_TYPES.get(
                        c.trigger_type, c.trigger_type
                    ),
                    "trigger_value": c.trigger_value,
                    "is_active": c.is_active,
                    "step_count": len(c.steps),
                    "total_enrolled": c.total_enrolled,
                    "total_completed": c.total_completed,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in campaigns
            ]

        finally:
            if close_session:
                session.close()

    # ==================== STEP MANAGEMENT ====================

    @staticmethod
    def add_step(
        campaign_id: int,
        delay_days: int = 1,
        delay_hours: int = 0,
        name: str = None,
        email_template_id: int = None,
        subject: str = None,
        html_content: str = None,
        condition_type: str = None,
        condition_value: str = None,
        session=None,
    ) -> Dict[str, Any]:
        """Add a step to a campaign"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            campaign = (
                session.query(DripCampaign)
                .filter(DripCampaign.id == campaign_id)
                .first()
            )

            if not campaign:
                return {"success": False, "error": "Campaign not found"}

            # Get next step order
            max_order = (
                session.query(DripStep)
                .filter(DripStep.campaign_id == campaign_id)
                .count()
            )

            step = DripStep(
                campaign_id=campaign_id,
                step_order=max_order + 1,
                name=name,
                delay_days=delay_days,
                delay_hours=delay_hours,
                email_template_id=email_template_id,
                subject=subject,
                html_content=html_content,
                condition_type=condition_type,
                condition_value=condition_value,
                is_active=True,
            )

            session.add(step)
            session.commit()
            session.refresh(step)

            return {
                "success": True,
                "step_id": step.id,
                "step_order": step.step_order,
                "message": f"Step {step.step_order} added to campaign",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def update_step(
        step_id: int,
        name: str = None,
        delay_days: int = None,
        delay_hours: int = None,
        email_template_id: int = None,
        subject: str = None,
        html_content: str = None,
        condition_type: str = None,
        condition_value: str = None,
        is_active: bool = None,
        session=None,
    ) -> Dict[str, Any]:
        """Update a step"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            step = session.query(DripStep).filter(DripStep.id == step_id).first()

            if not step:
                return {"success": False, "error": "Step not found"}

            if name is not None:
                step.name = name
            if delay_days is not None:
                step.delay_days = delay_days
            if delay_hours is not None:
                step.delay_hours = delay_hours
            if email_template_id is not None:
                step.email_template_id = email_template_id
            if subject is not None:
                step.subject = subject
            if html_content is not None:
                step.html_content = html_content
            if condition_type is not None:
                step.condition_type = condition_type
            if condition_value is not None:
                step.condition_value = condition_value
            if is_active is not None:
                step.is_active = is_active

            step.updated_at = datetime.utcnow()
            session.commit()

            return {"success": True, "message": "Step updated"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def delete_step(step_id: int, session=None) -> Dict[str, Any]:
        """Delete a step and reorder remaining steps"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            step = session.query(DripStep).filter(DripStep.id == step_id).first()

            if not step:
                return {"success": False, "error": "Step not found"}

            campaign_id = step.campaign_id
            deleted_order = step.step_order

            session.delete(step)

            # Reorder remaining steps
            remaining_steps = (
                session.query(DripStep)
                .filter(
                    DripStep.campaign_id == campaign_id,
                    DripStep.step_order > deleted_order,
                )
                .all()
            )

            for s in remaining_steps:
                s.step_order -= 1

            session.commit()

            return {
                "success": True,
                "message": "Step deleted and remaining steps reordered",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def reorder_steps(
        campaign_id: int, step_ids: List[int], session=None
    ) -> Dict[str, Any]:
        """Reorder steps in a campaign"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            for i, step_id in enumerate(step_ids):
                step = (
                    session.query(DripStep)
                    .filter(DripStep.id == step_id, DripStep.campaign_id == campaign_id)
                    .first()
                )
                if step:
                    step.step_order = i + 1

            session.commit()
            return {"success": True, "message": "Steps reordered"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    # ==================== ENROLLMENT MANAGEMENT ====================

    @staticmethod
    def enroll_client(
        campaign_id: int,
        client_id: int,
        session=None,
    ) -> Dict[str, Any]:
        """Enroll a client in a campaign"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            # Check campaign exists and is active
            campaign = (
                session.query(DripCampaign)
                .filter(DripCampaign.id == campaign_id, DripCampaign.is_active == True)
                .first()
            )

            if not campaign:
                return {"success": False, "error": "Campaign not found or inactive"}

            # Check client exists
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {"success": False, "error": "Client not found"}

            # Check if already enrolled
            existing = (
                session.query(DripEnrollment)
                .filter(
                    DripEnrollment.campaign_id == campaign_id,
                    DripEnrollment.client_id == client_id,
                    DripEnrollment.status.in_(["active", "paused"]),
                )
                .first()
            )

            if existing:
                return {
                    "success": False,
                    "error": "Client already enrolled in this campaign",
                }

            # Get first step to calculate next send time
            first_step = (
                session.query(DripStep)
                .filter(DripStep.campaign_id == campaign_id, DripStep.is_active == True)
                .order_by(DripStep.step_order)
                .first()
            )

            next_send_at = None
            if first_step:
                next_send_at = datetime.utcnow() + timedelta(
                    days=first_step.delay_days, hours=first_step.delay_hours
                )

            enrollment = DripEnrollment(
                campaign_id=campaign_id,
                client_id=client_id,
                current_step=0,
                status="active",
                next_send_at=next_send_at,
            )

            session.add(enrollment)

            # Update campaign stats
            campaign.total_enrolled += 1

            session.commit()
            session.refresh(enrollment)

            return {
                "success": True,
                "enrollment_id": enrollment.id,
                "next_send_at": next_send_at.isoformat() if next_send_at else None,
                "message": f"Client enrolled in '{campaign.name}'",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def pause_enrollment(
        enrollment_id: int, reason: str = None, session=None
    ) -> Dict[str, Any]:
        """Pause an enrollment"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            enrollment = (
                session.query(DripEnrollment)
                .filter(DripEnrollment.id == enrollment_id)
                .first()
            )

            if not enrollment:
                return {"success": False, "error": "Enrollment not found"}

            enrollment.status = "paused"
            enrollment.paused_reason = reason
            enrollment.updated_at = datetime.utcnow()
            session.commit()

            return {"success": True, "message": "Enrollment paused"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def resume_enrollment(enrollment_id: int, session=None) -> Dict[str, Any]:
        """Resume a paused enrollment"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            enrollment = (
                session.query(DripEnrollment)
                .filter(DripEnrollment.id == enrollment_id)
                .first()
            )

            if not enrollment:
                return {"success": False, "error": "Enrollment not found"}

            if enrollment.status != "paused":
                return {"success": False, "error": "Enrollment is not paused"}

            # Calculate next send time from now
            next_step = (
                session.query(DripStep)
                .filter(
                    DripStep.campaign_id == enrollment.campaign_id,
                    DripStep.step_order == enrollment.current_step + 1,
                    DripStep.is_active == True,
                )
                .first()
            )

            if next_step:
                enrollment.next_send_at = datetime.utcnow() + timedelta(
                    days=next_step.delay_days, hours=next_step.delay_hours
                )

            enrollment.status = "active"
            enrollment.paused_reason = None
            enrollment.updated_at = datetime.utcnow()
            session.commit()

            return {"success": True, "message": "Enrollment resumed"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def cancel_enrollment(
        enrollment_id: int, reason: str = None, session=None
    ) -> Dict[str, Any]:
        """Cancel an enrollment"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            enrollment = (
                session.query(DripEnrollment)
                .filter(DripEnrollment.id == enrollment_id)
                .first()
            )

            if not enrollment:
                return {"success": False, "error": "Enrollment not found"}

            enrollment.status = "cancelled"
            enrollment.cancelled_reason = reason
            enrollment.updated_at = datetime.utcnow()
            session.commit()

            return {"success": True, "message": "Enrollment cancelled"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_enrollment(enrollment_id: int, session=None) -> Optional[Dict[str, Any]]:
        """Get enrollment details"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            enrollment = (
                session.query(DripEnrollment)
                .filter(DripEnrollment.id == enrollment_id)
                .first()
            )

            if not enrollment:
                return None

            return {
                "id": enrollment.id,
                "campaign_id": enrollment.campaign_id,
                "campaign_name": (
                    enrollment.campaign.name if enrollment.campaign else None
                ),
                "client_id": enrollment.client_id,
                "client_name": enrollment.client.name if enrollment.client else None,
                "client_email": enrollment.client.email if enrollment.client else None,
                "current_step": enrollment.current_step,
                "status": enrollment.status,
                "status_label": ENROLLMENT_STATUSES.get(
                    enrollment.status, enrollment.status
                ),
                "enrolled_at": (
                    enrollment.enrolled_at.isoformat()
                    if enrollment.enrolled_at
                    else None
                ),
                "next_send_at": (
                    enrollment.next_send_at.isoformat()
                    if enrollment.next_send_at
                    else None
                ),
                "last_sent_at": (
                    enrollment.last_sent_at.isoformat()
                    if enrollment.last_sent_at
                    else None
                ),
                "completed_at": (
                    enrollment.completed_at.isoformat()
                    if enrollment.completed_at
                    else None
                ),
                "emails_sent": enrollment.emails_sent,
                "emails_opened": enrollment.emails_opened,
                "emails_clicked": enrollment.emails_clicked,
                "paused_reason": enrollment.paused_reason,
                "cancelled_reason": enrollment.cancelled_reason,
            }

        finally:
            if close_session:
                session.close()

    @staticmethod
    def list_enrollments(
        campaign_id: int = None,
        client_id: int = None,
        status: str = None,
        session=None,
    ) -> List[Dict[str, Any]]:
        """List enrollments with optional filtering"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            query = session.query(DripEnrollment)

            if campaign_id:
                query = query.filter(DripEnrollment.campaign_id == campaign_id)
            if client_id:
                query = query.filter(DripEnrollment.client_id == client_id)
            if status:
                query = query.filter(DripEnrollment.status == status)

            enrollments = query.order_by(DripEnrollment.enrolled_at.desc()).all()

            return [
                {
                    "id": e.id,
                    "campaign_id": e.campaign_id,
                    "campaign_name": e.campaign.name if e.campaign else None,
                    "client_id": e.client_id,
                    "client_name": e.client.name if e.client else None,
                    "current_step": e.current_step,
                    "status": e.status,
                    "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
                    "next_send_at": (
                        e.next_send_at.isoformat() if e.next_send_at else None
                    ),
                    "emails_sent": e.emails_sent,
                }
                for e in enrollments
            ]

        finally:
            if close_session:
                session.close()

    # ==================== EMAIL PROCESSING ====================

    @staticmethod
    def process_due_emails(session=None) -> Dict[str, Any]:
        """
        Process all due drip emails.
        This should be called by a scheduled job.
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        sent = 0
        skipped = 0
        errors = []
        now = datetime.utcnow()
        current_hour = now.hour

        try:
            # Get all active enrollments with due emails
            due_enrollments = (
                session.query(DripEnrollment)
                .filter(
                    DripEnrollment.status == "active",
                    DripEnrollment.next_send_at <= now,
                )
                .all()
            )

            for enrollment in due_enrollments:
                try:
                    campaign = enrollment.campaign
                    client = enrollment.client

                    if not campaign or not client:
                        skipped += 1
                        continue

                    # Check send window
                    if not (
                        campaign.send_window_start
                        <= current_hour
                        < campaign.send_window_end
                    ):
                        skipped += 1
                        continue

                    # Check weekend setting
                    if not campaign.send_on_weekends and now.weekday() >= 5:
                        skipped += 1
                        continue

                    # Check email opt-in
                    if hasattr(client, "email_opt_in") and not client.email_opt_in:
                        skipped += 1
                        continue

                    # Get next step
                    next_step = (
                        session.query(DripStep)
                        .filter(
                            DripStep.campaign_id == campaign.id,
                            DripStep.step_order == enrollment.current_step + 1,
                            DripStep.is_active == True,
                        )
                        .first()
                    )

                    if not next_step:
                        # Campaign complete
                        enrollment.status = "completed"
                        enrollment.completed_at = now
                        campaign.total_completed += 1
                        session.commit()
                        continue

                    # Get email content
                    subject = next_step.subject
                    html_content = next_step.html_content

                    if next_step.email_template_id:
                        # Use template
                        template_result = EmailTemplateService.render_template(
                            template_id=next_step.email_template_id,
                            variables={
                                "client_name": client.name,
                                "first_name": (
                                    client.name.split()[0] if client.name else ""
                                ),
                                "email": client.email,
                            },
                            session=session,
                        )
                        if template_result.get("success"):
                            subject = template_result.get("subject", subject)
                            html_content = template_result.get("html", html_content)

                    if not subject or not html_content:
                        errors.append(
                            f"Step {next_step.id}: Missing subject or content"
                        )
                        continue

                    # Send email
                    email_result = send_email(
                        to_email=client.email,
                        subject=subject,
                        html_content=html_content,
                    )

                    # Log the email
                    log = DripEmailLog(
                        enrollment_id=enrollment.id,
                        step_id=next_step.id,
                        subject=subject,
                        status="sent" if email_result else "failed",
                        error_message=None if email_result else "Send failed",
                    )
                    session.add(log)

                    if email_result:
                        # Update enrollment
                        enrollment.current_step = next_step.step_order
                        enrollment.last_sent_at = now
                        enrollment.emails_sent += 1

                        # Calculate next send time
                        following_step = (
                            session.query(DripStep)
                            .filter(
                                DripStep.campaign_id == campaign.id,
                                DripStep.step_order == next_step.step_order + 1,
                                DripStep.is_active == True,
                            )
                            .first()
                        )

                        if following_step:
                            enrollment.next_send_at = now + timedelta(
                                days=following_step.delay_days,
                                hours=following_step.delay_hours,
                            )
                        else:
                            # No more steps
                            enrollment.status = "completed"
                            enrollment.completed_at = now
                            campaign.total_completed += 1

                        sent += 1
                    else:
                        errors.append(f"Failed to send to {client.email}")

                    session.commit()

                except Exception as e:
                    errors.append(f"Enrollment {enrollment.id}: {str(e)}")
                    continue

            return {
                "success": True,
                "sent": sent,
                "skipped": skipped,
                "errors": errors,
                "processed_at": now.isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_campaign_stats(campaign_id: int, session=None) -> Dict[str, Any]:
        """Get detailed stats for a campaign"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            campaign = (
                session.query(DripCampaign)
                .filter(DripCampaign.id == campaign_id)
                .first()
            )

            if not campaign:
                return {"success": False, "error": "Campaign not found"}

            active = (
                session.query(DripEnrollment)
                .filter(
                    DripEnrollment.campaign_id == campaign_id,
                    DripEnrollment.status == "active",
                )
                .count()
            )

            paused = (
                session.query(DripEnrollment)
                .filter(
                    DripEnrollment.campaign_id == campaign_id,
                    DripEnrollment.status == "paused",
                )
                .count()
            )

            completed = (
                session.query(DripEnrollment)
                .filter(
                    DripEnrollment.campaign_id == campaign_id,
                    DripEnrollment.status == "completed",
                )
                .count()
            )

            cancelled = (
                session.query(DripEnrollment)
                .filter(
                    DripEnrollment.campaign_id == campaign_id,
                    DripEnrollment.status == "cancelled",
                )
                .count()
            )

            # Get email stats from logs
            from sqlalchemy import func

            email_stats = (
                session.query(
                    func.count(DripEmailLog.id).label("total_sent"),
                    func.count(DripEmailLog.opened_at).label("total_opened"),
                    func.count(DripEmailLog.clicked_at).label("total_clicked"),
                )
                .join(DripEnrollment)
                .filter(DripEnrollment.campaign_id == campaign_id)
                .first()
            )

            return {
                "success": True,
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "enrollments": {
                    "total": campaign.total_enrolled,
                    "active": active,
                    "paused": paused,
                    "completed": completed,
                    "cancelled": cancelled,
                },
                "emails": {
                    "sent": email_stats.total_sent if email_stats else 0,
                    "opened": email_stats.total_opened if email_stats else 0,
                    "clicked": email_stats.total_clicked if email_stats else 0,
                    "open_rate": (
                        round(
                            (email_stats.total_opened / email_stats.total_sent * 100), 1
                        )
                        if email_stats and email_stats.total_sent > 0
                        else 0
                    ),
                    "click_rate": (
                        round(
                            (email_stats.total_clicked / email_stats.total_sent * 100),
                            1,
                        )
                        if email_stats and email_stats.total_sent > 0
                        else 0
                    ),
                },
                "step_count": len(campaign.steps),
            }

        finally:
            if close_session:
                session.close()


# ==================== TRIGGER INTEGRATION ====================


def check_drip_triggers(
    trigger_type: str, client_id: int, trigger_value: str = None, session=None
):
    """
    Check if any drip campaigns should be triggered for a client.
    Called from workflow triggers or status change hooks.
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        # Find matching active campaigns
        query = session.query(DripCampaign).filter(
            DripCampaign.is_active == True, DripCampaign.trigger_type == trigger_type
        )

        if trigger_value:
            query = query.filter(
                (DripCampaign.trigger_value == trigger_value)
                | (DripCampaign.trigger_value == None)
            )

        campaigns = query.all()

        enrolled = []
        for campaign in campaigns:
            result = DripCampaignService.enroll_client(
                campaign_id=campaign.id,
                client_id=client_id,
                session=session,
            )
            if result.get("success"):
                enrolled.append(campaign.name)

        return {"enrolled_in": enrolled}

    finally:
        if close_session:
            session.close()


# Convenience functions
def enroll_client(campaign_id: int, client_id: int):
    """Enroll a client in a campaign"""
    return DripCampaignService.enroll_client(campaign_id, client_id)


def process_drip_emails():
    """Process all due drip emails"""
    return DripCampaignService.process_due_emails()


# Task handler for scheduled job
try:
    from services.task_queue_service import register_task_handler

    @register_task_handler("process_drip_emails")
    def handle_process_drip_emails(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Task handler for processing due drip emails"""
        return DripCampaignService.process_due_emails()

except ImportError:
    # Task queue not available, handlers will be registered elsewhere
    pass
