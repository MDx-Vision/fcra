"""
Batch Processing Service
Brightpath Ascend FCRA Platform

Handles bulk operations on clients including:
- Status updates
- Email sending
- Staff assignment
- Tag management
- Delete operations

Created: 2026-01-03
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from database import (
    BatchJob,
    BatchJobItem,
    Client,
    ClientTag,
    ClientTagAssignment,
    EmailTemplate,
    SessionLocal,
    Staff,
)

logger = logging.getLogger(__name__)


# Supported batch action types
ACTION_TYPES = {
    "update_status": {
        "name": "Update Status",
        "description": "Change dispute status for selected clients",
        "params": ["new_status"],
    },
    "update_dispute_round": {
        "name": "Update Dispute Round",
        "description": "Change dispute round for selected clients",
        "params": ["new_round"],
    },
    "send_email": {
        "name": "Send Email",
        "description": "Send email using template to selected clients",
        "params": ["template_id", "subject", "body"],
    },
    "send_sms": {
        "name": "Send SMS",
        "description": "Send SMS message to selected clients",
        "params": ["message"],
    },
    "assign_staff": {
        "name": "Assign Staff",
        "description": "Assign a staff member to selected clients",
        "params": ["staff_id"],
    },
    "add_tag": {
        "name": "Add Tag",
        "description": "Add a tag to selected clients",
        "params": ["tag_id", "tag_name"],
    },
    "remove_tag": {
        "name": "Remove Tag",
        "description": "Remove a tag from selected clients",
        "params": ["tag_id"],
    },
    "add_note": {
        "name": "Add Note",
        "description": "Add admin note to selected clients",
        "params": ["note"],
    },
    "export": {
        "name": "Export",
        "description": "Export selected clients to CSV",
        "params": ["fields"],
    },
    "delete": {
        "name": "Delete",
        "description": "Delete selected clients (use with caution)",
        "params": [],
    },
}

# Status options for batch update
STATUS_OPTIONS = [
    "new",
    "lead",
    "report_uploaded",
    "analysis_pending",
    "analysis_complete",
    "onboarding",
    "pending_payment",
    "active",
    "waiting_response",
    "round_complete",
    "paused",
    "cancelled",
    "complete",
]


class BatchProcessingService:
    """Service for batch processing operations on clients"""

    def __init__(self, session: Session = None):
        self._session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self._session:
            return self._session
        return SessionLocal()

    def _close_session(self, session: Session):
        if self._owns_session and session:
            session.close()

    # -------------------------------------------------------------------------
    # Action Types & Configuration
    # -------------------------------------------------------------------------

    def get_action_types(self) -> Dict[str, Any]:
        """Get all available batch action types"""
        return ACTION_TYPES

    def get_status_options(self) -> List[str]:
        """Get all available status options"""
        return STATUS_OPTIONS

    # -------------------------------------------------------------------------
    # Job Management
    # -------------------------------------------------------------------------

    def create_job(
        self,
        name: str,
        action_type: str,
        client_ids: List[int],
        action_params: Dict[str, Any],
        staff_id: int,
        selection_type: str = "manual",
        selection_filter: Dict = None,
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new batch job

        Args:
            name: Human-readable job name
            action_type: One of ACTION_TYPES keys
            client_ids: List of client IDs to process
            action_params: Parameters for the action
            staff_id: ID of staff member creating the job
            selection_type: 'manual', 'filter', or 'all'
            selection_filter: Filter criteria if selection_type='filter'

        Returns:
            Tuple of (success, message, job_dict)
        """
        if action_type not in ACTION_TYPES:
            return False, f"Invalid action type: {action_type}", None

        if not client_ids:
            return False, "No clients selected", None

        session = self._get_session()
        try:
            # Create the batch job
            job = BatchJob(
                job_uuid=str(uuid.uuid4()),
                name=name,
                action_type=action_type,
                action_params=action_params,
                selection_type=selection_type,
                selection_filter=selection_filter,
                total_items=len(client_ids),
                status="pending",
                created_by_id=staff_id,
            )
            session.add(job)
            session.flush()  # Get the job ID

            # Create batch job items
            for client_id in client_ids:
                item = BatchJobItem(
                    batch_job_id=job.id, client_id=client_id, status="pending"
                )
                session.add(item)

            session.commit()

            logger.info(
                f"Created batch job {job.job_uuid}: {name} ({action_type}) for {len(client_ids)} clients"
            )
            return True, "Batch job created successfully", job.to_dict()

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating batch job: {e}")
            return False, f"Error creating batch job: {str(e)}", None
        finally:
            self._close_session(session)

    def get_job(self, job_id: int = None, job_uuid: str = None) -> Optional[Dict]:
        """Get a batch job by ID or UUID"""
        session = self._get_session()
        try:
            if job_id:
                job = session.query(BatchJob).filter(BatchJob.id == job_id).first()
            elif job_uuid:
                job = (
                    session.query(BatchJob)
                    .filter(BatchJob.job_uuid == job_uuid)
                    .first()
                )
            else:
                return None

            if not job:
                return None

            result = job.to_dict()
            result["items"] = [item.to_dict() for item in job.items]
            return result
        finally:
            self._close_session(session)

    def list_jobs(
        self,
        status: str = None,
        action_type: str = None,
        created_by_id: int = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """List batch jobs with optional filtering"""
        session = self._get_session()
        try:
            query = session.query(BatchJob)

            if status:
                query = query.filter(BatchJob.status == status)
            if action_type:
                query = query.filter(BatchJob.action_type == action_type)
            if created_by_id:
                query = query.filter(BatchJob.created_by_id == created_by_id)

            jobs = (
                query.order_by(BatchJob.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [job.to_dict() for job in jobs]
        finally:
            self._close_session(session)

    def get_job_progress(self, job_id: int) -> Optional[Dict]:
        """Get real-time progress of a batch job"""
        session = self._get_session()
        try:
            job = session.query(BatchJob).filter(BatchJob.id == job_id).first()
            if not job:
                return None

            return {
                "job_id": job.id,
                "job_uuid": job.job_uuid,
                "status": job.status,
                "total_items": job.total_items,
                "items_processed": job.items_processed,
                "items_succeeded": job.items_succeeded,
                "items_failed": job.items_failed,
                "progress_percent": job.progress_percent,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": (
                    job.completed_at.isoformat() if job.completed_at else None
                ),
                "error_message": job.error_message,
            }
        finally:
            self._close_session(session)

    def cancel_job(self, job_id: int, staff_id: int) -> Tuple[bool, str]:
        """Cancel a pending or running batch job"""
        session = self._get_session()
        try:
            job = session.query(BatchJob).filter(BatchJob.id == job_id).first()
            if not job:
                return False, "Job not found"

            if job.status in ["completed", "cancelled"]:
                return False, f"Cannot cancel job with status: {job.status}"

            job.status = "cancelled"
            job.completed_at = datetime.utcnow()
            job.error_message = f"Cancelled by staff ID {staff_id}"

            # Mark remaining pending items as skipped
            session.query(BatchJobItem).filter(
                and_(
                    BatchJobItem.batch_job_id == job_id,
                    BatchJobItem.status == "pending",
                )
            ).update({"status": "skipped"})

            session.commit()
            return True, "Job cancelled successfully"
        except Exception as e:
            session.rollback()
            return False, f"Error cancelling job: {str(e)}"
        finally:
            self._close_session(session)

    # -------------------------------------------------------------------------
    # Job Execution
    # -------------------------------------------------------------------------

    def execute_job(self, job_id: int) -> Tuple[bool, str]:
        """
        Execute a batch job synchronously

        For large jobs, consider running this in a background task.
        """
        session = self._get_session()
        try:
            job = session.query(BatchJob).filter(BatchJob.id == job_id).first()
            if not job:
                return False, "Job not found"

            if job.status != "pending":
                return False, f"Job is not pending (current status: {job.status})"

            # Start the job
            job.status = "running"
            job.started_at = datetime.utcnow()
            session.commit()

            # Get all pending items
            items = (
                session.query(BatchJobItem)
                .filter(
                    and_(
                        BatchJobItem.batch_job_id == job_id,
                        BatchJobItem.status == "pending",
                    )
                )
                .all()
            )

            processed = 0
            succeeded = 0
            failed = 0

            for item in items:
                # Check if job was cancelled
                session.refresh(job)
                if job.status == "cancelled":
                    break

                try:
                    success, error = self._process_item(session, job, item)
                    item.status = "completed" if success else "failed"
                    item.processed_at = datetime.utcnow()
                    if not success:
                        item.error_message = error
                        failed += 1
                    else:
                        succeeded += 1
                except Exception as e:
                    item.status = "failed"
                    item.error_message = str(e)
                    item.processed_at = datetime.utcnow()
                    failed += 1
                    logger.error(f"Error processing item {item.id}: {e}")

                processed += 1

                # Update progress
                job.items_processed = processed
                job.items_succeeded = succeeded
                job.items_failed = failed
                job.progress_percent = (
                    (processed / job.total_items) * 100 if job.total_items > 0 else 100
                )

                # Commit after each item for real-time progress
                session.commit()

            # Finalize job
            job.status = (
                "completed" if failed == 0 else "completed"
            )  # Still complete even with failures
            job.completed_at = datetime.utcnow()
            if failed > 0:
                job.error_message = f"{failed} of {job.total_items} items failed"
            session.commit()

            return True, f"Job completed: {succeeded} succeeded, {failed} failed"

        except Exception as e:
            session.rollback()
            # Mark job as failed
            try:
                job = session.query(BatchJob).filter(BatchJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    session.commit()
            except:
                pass
            logger.error(f"Error executing batch job {job_id}: {e}")
            return False, f"Job failed: {str(e)}"
        finally:
            self._close_session(session)

    def _process_item(
        self, session: Session, job: BatchJob, item: BatchJobItem
    ) -> Tuple[bool, Optional[str]]:
        """
        Process a single batch job item

        Returns:
            Tuple of (success, error_message)
        """
        client = session.query(Client).filter(Client.id == item.client_id).first()
        if not client:
            return False, "Client not found"

        action_type = job.action_type
        params = job.action_params or {}

        # Save before state
        item.before_state = self._get_client_state(client)

        if action_type == "update_status":
            return self._action_update_status(session, client, item, params)
        elif action_type == "update_dispute_round":
            return self._action_update_round(session, client, item, params)
        elif action_type == "send_email":
            return self._action_send_email(session, client, item, params)
        elif action_type == "send_sms":
            return self._action_send_sms(session, client, item, params)
        elif action_type == "assign_staff":
            return self._action_assign_staff(session, client, item, params)
        elif action_type == "add_tag":
            return self._action_add_tag(session, client, item, params)
        elif action_type == "remove_tag":
            return self._action_remove_tag(session, client, item, params)
        elif action_type == "add_note":
            return self._action_add_note(session, client, item, params)
        elif action_type == "delete":
            return self._action_delete(session, client, item, params)
        else:
            return False, f"Unknown action type: {action_type}"

    def _get_client_state(self, client: Client) -> Dict:
        """Get relevant client state for rollback"""
        return {
            "dispute_status": client.dispute_status,
            "current_dispute_round": client.current_dispute_round,
            "status": client.status,
            "assigned_staff_id": getattr(client, "assigned_staff_id", None),
            "admin_notes": client.admin_notes,
        }

    # -------------------------------------------------------------------------
    # Action Handlers
    # -------------------------------------------------------------------------

    def _action_update_status(
        self, session: Session, client: Client, item: BatchJobItem, params: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Update client dispute status"""
        new_status = params.get("new_status")
        if not new_status:
            return False, "No new_status specified"

        client.dispute_status = new_status
        item.after_state = self._get_client_state(client)
        return True, None

    def _action_update_round(
        self, session: Session, client: Client, item: BatchJobItem, params: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Update client dispute round"""
        new_round = params.get("new_round")
        if new_round is None:
            return False, "No new_round specified"

        try:
            new_round = int(new_round)
        except ValueError:
            return False, "Invalid round number"

        if new_round < 0 or new_round > 10:
            return False, "Round must be between 0 and 10"

        client.current_dispute_round = new_round
        if new_round > 0:
            client.round_started_at = datetime.utcnow()
        item.after_state = self._get_client_state(client)
        return True, None

    def _action_send_email(
        self, session: Session, client: Client, item: BatchJobItem, params: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Send email to client"""
        if not client.email:
            return False, "Client has no email address"

        try:
            from services.email_service import send_email

            template_id = params.get("template_id")
            subject = params.get("subject", "Message from Brightpath Ascend")
            body = params.get("body", "")

            # If template ID provided, load template
            if template_id:
                template = (
                    session.query(EmailTemplate)
                    .filter(EmailTemplate.id == template_id)
                    .first()
                )
                if template:
                    subject = template.subject or subject
                    body = template.html_content or template.content or body

            # Variable substitution
            body = body.replace("{client_name}", client.name or "")
            body = body.replace(
                "{first_name}",
                client.first_name or client.name.split()[0] if client.name else "",
            )
            body = body.replace("{email}", client.email or "")

            success = send_email(
                to_email=client.email, subject=subject, html_content=body
            )

            if success:
                item.after_state = {"email_sent": True, "to": client.email}
                return True, None
            else:
                return False, "Failed to send email"
        except Exception as e:
            return False, f"Email error: {str(e)}"

    def _action_send_sms(
        self, session: Session, client: Client, item: BatchJobItem, params: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Send SMS to client"""
        if not client.phone:
            return False, "Client has no phone number"

        if not getattr(client, "sms_opt_in", False):
            return False, "Client has not opted in to SMS"

        try:
            from services.sms_service import send_sms

            message = params.get("message", "")
            if not message:
                return False, "No message specified"

            # Variable substitution
            message = message.replace("{client_name}", client.name or "")
            message = message.replace(
                "{first_name}",
                client.first_name or client.name.split()[0] if client.name else "",
            )

            success = send_sms(client.phone, message)

            if success:
                item.after_state = {"sms_sent": True, "to": client.phone}
                return True, None
            else:
                return False, "Failed to send SMS"
        except Exception as e:
            return False, f"SMS error: {str(e)}"

    def _action_assign_staff(
        self, session: Session, client: Client, item: BatchJobItem, params: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Assign staff member to client"""
        staff_id = params.get("staff_id")
        if not staff_id:
            return False, "No staff_id specified"

        # Verify staff exists
        staff = session.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            return False, f"Staff member {staff_id} not found"

        # Set assigned staff (if field exists)
        if hasattr(client, "assigned_staff_id"):
            client.assigned_staff_id = staff_id
        else:
            # Add to admin notes as fallback
            note = f"\n[{datetime.utcnow().isoformat()}] Assigned to: {staff.full_name}"
            client.admin_notes = (client.admin_notes or "") + note

        item.after_state = self._get_client_state(client)
        return True, None

    def _action_add_tag(
        self, session: Session, client: Client, item: BatchJobItem, params: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Add tag to client"""
        tag_id = params.get("tag_id")
        tag_name = params.get("tag_name")

        if not tag_id and not tag_name:
            return False, "No tag_id or tag_name specified"

        try:
            # Find or create tag
            if tag_id:
                tag = session.query(ClientTag).filter(ClientTag.id == tag_id).first()
            else:
                tag = (
                    session.query(ClientTag).filter(ClientTag.name == tag_name).first()
                )
                if not tag:
                    # Create new tag
                    tag = ClientTag(name=tag_name)
                    session.add(tag)
                    session.flush()

            if not tag:
                return False, "Tag not found"

            # Check if already assigned
            existing = (
                session.query(ClientTagAssignment)
                .filter(
                    and_(
                        ClientTagAssignment.client_id == client.id,
                        ClientTagAssignment.tag_id == tag.id,
                    )
                )
                .first()
            )

            if existing:
                return True, None  # Already has tag, not an error

            # Create assignment
            assignment = ClientTagAssignment(client_id=client.id, tag_id=tag.id)
            session.add(assignment)

            item.after_state = {"tag_added": tag.name}
            return True, None
        except Exception as e:
            return False, f"Tag error: {str(e)}"

    def _action_remove_tag(
        self, session: Session, client: Client, item: BatchJobItem, params: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Remove tag from client"""
        tag_id = params.get("tag_id")
        if not tag_id:
            return False, "No tag_id specified"

        try:
            # Find and delete assignment
            assignment = (
                session.query(ClientTagAssignment)
                .filter(
                    and_(
                        ClientTagAssignment.client_id == client.id,
                        ClientTagAssignment.tag_id == tag_id,
                    )
                )
                .first()
            )

            if assignment:
                session.delete(assignment)
                item.after_state = {"tag_removed": True}
            else:
                item.after_state = {"tag_not_found": True}

            return True, None
        except Exception as e:
            return False, f"Tag removal error: {str(e)}"

    def _action_add_note(
        self, session: Session, client: Client, item: BatchJobItem, params: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Add admin note to client"""
        note = params.get("note", "")
        if not note:
            return False, "No note specified"

        timestamp = datetime.utcnow().isoformat()
        formatted_note = f"\n[{timestamp}] {note}"

        client.admin_notes = (client.admin_notes or "") + formatted_note
        item.after_state = self._get_client_state(client)
        return True, None

    def _action_delete(
        self, session: Session, client: Client, item: BatchJobItem, params: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Delete client (soft delete by setting status)"""
        # For safety, we do a soft delete by changing status
        # Hard delete should require additional confirmation
        hard_delete = params.get("hard_delete", False)

        if hard_delete:
            session.delete(client)
            item.after_state = {"deleted": True, "hard": True}
        else:
            client.status = "deleted"
            client.dispute_status = "deleted"
            item.after_state = {"deleted": True, "hard": False, "status": "deleted"}

        return True, None

    # -------------------------------------------------------------------------
    # Batch History & Stats
    # -------------------------------------------------------------------------

    def get_job_history(self, days: int = 30, limit: int = 100) -> List[Dict]:
        """Get batch job history for the last N days"""
        session = self._get_session()
        try:
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(days=days)

            jobs = (
                session.query(BatchJob)
                .filter(BatchJob.created_at >= cutoff)
                .order_by(BatchJob.created_at.desc())
                .limit(limit)
                .all()
            )

            return [job.to_dict() for job in jobs]
        finally:
            self._close_session(session)

    def get_stats(self) -> Dict:
        """Get batch processing statistics"""
        session = self._get_session()
        try:
            from sqlalchemy import func

            total_jobs = session.query(func.count(BatchJob.id)).scalar() or 0
            pending_jobs = (
                session.query(func.count(BatchJob.id))
                .filter(BatchJob.status == "pending")
                .scalar()
                or 0
            )
            running_jobs = (
                session.query(func.count(BatchJob.id))
                .filter(BatchJob.status == "running")
                .scalar()
                or 0
            )
            completed_jobs = (
                session.query(func.count(BatchJob.id))
                .filter(BatchJob.status == "completed")
                .scalar()
                or 0
            )
            failed_jobs = (
                session.query(func.count(BatchJob.id))
                .filter(BatchJob.status == "failed")
                .scalar()
                or 0
            )

            total_items = session.query(func.sum(BatchJob.total_items)).scalar() or 0
            succeeded_items = (
                session.query(func.sum(BatchJob.items_succeeded)).scalar() or 0
            )
            failed_items = session.query(func.sum(BatchJob.items_failed)).scalar() or 0

            return {
                "total_jobs": total_jobs,
                "pending_jobs": pending_jobs,
                "running_jobs": running_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "total_items_processed": succeeded_items + failed_items,
                "items_succeeded": succeeded_items,
                "items_failed": failed_items,
                "success_rate": (
                    (succeeded_items / (succeeded_items + failed_items) * 100)
                    if (succeeded_items + failed_items) > 0
                    else 0
                ),
            }
        finally:
            self._close_session(session)

    def retry_failed_items(self, job_id: int) -> Tuple[bool, str]:
        """Retry failed items in a batch job"""
        session = self._get_session()
        try:
            job = session.query(BatchJob).filter(BatchJob.id == job_id).first()
            if not job:
                return False, "Job not found"

            if job.status not in ["completed", "failed"]:
                return False, "Can only retry completed or failed jobs"

            # Reset failed items to pending
            failed_items = (
                session.query(BatchJobItem)
                .filter(
                    and_(
                        BatchJobItem.batch_job_id == job_id,
                        BatchJobItem.status == "failed",
                    )
                )
                .all()
            )

            if not failed_items:
                return False, "No failed items to retry"

            for item in failed_items:
                item.status = "pending"
                item.error_message = None
                item.retry_count += 1

            # Reset job status
            job.status = "pending"
            job.items_failed = 0
            job.items_processed = job.items_succeeded
            job.progress_percent = (
                (job.items_processed / job.total_items) * 100
                if job.total_items > 0
                else 0
            )
            job.error_message = None
            job.completed_at = None

            session.commit()

            return True, f"Reset {len(failed_items)} failed items for retry"
        except Exception as e:
            session.rollback()
            return False, f"Error retrying items: {str(e)}"
        finally:
            self._close_session(session)


# Convenience functions
def create_batch_job(
    name: str,
    action_type: str,
    client_ids: List[int],
    action_params: Dict,
    staff_id: int,
) -> Tuple[bool, str, Optional[Dict]]:
    """Create and optionally execute a batch job"""
    service = BatchProcessingService()
    return service.create_job(name, action_type, client_ids, action_params, staff_id)


def execute_batch_job(job_id: int) -> Tuple[bool, str]:
    """Execute a batch job"""
    service = BatchProcessingService()
    return service.execute_job(job_id)


def get_batch_job_progress(job_id: int) -> Optional[Dict]:
    """Get batch job progress"""
    service = BatchProcessingService()
    return service.get_job_progress(job_id)


def get_batch_stats() -> Dict:
    """Get batch processing statistics"""
    service = BatchProcessingService()
    return service.get_stats()
