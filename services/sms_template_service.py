"""
SMS Template Service for Brightpath Ascend FCRA Platform

CRUD operations and template management for SMS messages.
Allows staff to create, edit, and manage SMS templates used for client communications.
"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from database import SessionLocal, SMSTemplate


# Template categories
SMS_CATEGORIES = {
    "welcome": "Welcome & Onboarding",
    "updates": "Case Updates",
    "reminders": "Reminders",
    "notifications": "Notifications",
    "payment": "Payment & Billing",
    "general": "General",
}

# Common template variables that can be used
SMS_VARIABLES = [
    {"name": "client_name", "description": "Client's full name", "example": "John Smith"},
    {"name": "first_name", "description": "Client's first name", "example": "John"},
    {"name": "company_name", "description": "Company name", "example": "Brightpath Ascend"},
    {"name": "portal_url", "description": "Link to client portal", "example": "https://portal.example.com"},
    {"name": "phone", "description": "Support phone number", "example": "(555) 123-4567"},
    {"name": "status", "description": "Current case status", "example": "Active"},
    {"name": "bureau", "description": "Credit bureau name", "example": "Equifax"},
    {"name": "date", "description": "Relevant date", "example": "Jan 15, 2026"},
    {"name": "amount", "description": "Dollar amount", "example": "$99.00"},
]

# SMS character limits
SMS_CHAR_LIMIT = 160  # Standard SMS length
SMS_LONG_LIMIT = 320  # 2 segments max


class SMSTemplateService:
    """Service for managing SMS templates"""

    @staticmethod
    def get_categories() -> Dict[str, str]:
        """Get all template categories"""
        return SMS_CATEGORIES

    @staticmethod
    def get_common_variables() -> List[Dict[str, str]]:
        """Get list of common template variables"""
        return SMS_VARIABLES

    @staticmethod
    def create_template(
        template_type: str,
        name: str,
        message: str,
        category: str = "general",
        description: str = None,
        variables: List[Dict] = None,
        is_custom: bool = True,
        session=None,
    ) -> Dict[str, Any]:
        """
        Create a new SMS template.

        Args:
            template_type: Unique identifier (e.g., 'welcome_sms')
            name: Human-readable name
            message: SMS message content (max 320 chars recommended)
            category: Template category
            description: What this template is for
            variables: List of variables used in this template
            is_custom: True for user-created templates
            session: Optional database session

        Returns:
            Dict with success status and template data
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            # Check if template_type already exists
            existing = session.query(SMSTemplate).filter(
                SMSTemplate.template_type == template_type
            ).first()
            if existing:
                return {
                    "success": False,
                    "error": f"Template type '{template_type}' already exists",
                }

            # Warn if message is too long
            char_count = len(message)
            segments = 1 if char_count <= SMS_CHAR_LIMIT else (char_count // SMS_CHAR_LIMIT) + 1

            # Create new template
            template = SMSTemplate(
                template_type=template_type,
                name=name,
                category=category,
                description=description,
                message=message,
                variables=variables or [],
                is_custom=is_custom,
                is_active=True,
            )

            session.add(template)
            session.commit()
            session.refresh(template)

            return {
                "success": True,
                "template_id": template.id,
                "template_type": template.template_type,
                "char_count": char_count,
                "segments": segments,
                "message": f"Template '{name}' created successfully",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def update_template(
        template_id: int,
        name: str = None,
        message: str = None,
        category: str = None,
        description: str = None,
        variables: List[Dict] = None,
        is_active: bool = None,
        session=None,
    ) -> Dict[str, Any]:
        """
        Update an existing SMS template.

        Returns:
            Dict with success status
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            template = session.query(SMSTemplate).filter(
                SMSTemplate.id == template_id
            ).first()

            if not template:
                return {"success": False, "error": "Template not found"}

            # Update fields if provided
            if name is not None:
                template.name = name
            if message is not None:
                template.message = message
            if category is not None:
                template.category = category
            if description is not None:
                template.description = description
            if variables is not None:
                template.variables = variables
            if is_active is not None:
                template.is_active = is_active

            template.updated_at = datetime.utcnow()
            session.commit()

            return {
                "success": True,
                "message": f"Template '{template.name}' updated successfully",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def delete_template(template_id: int, session=None) -> Dict[str, Any]:
        """
        Delete an SMS template.

        Note: System templates (is_custom=False) cannot be deleted.
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            template = session.query(SMSTemplate).filter(
                SMSTemplate.id == template_id
            ).first()

            if not template:
                return {"success": False, "error": "Template not found"}

            if not template.is_custom:
                return {
                    "success": False,
                    "error": "System templates cannot be deleted. You can deactivate them instead.",
                }

            name = template.name
            session.delete(template)
            session.commit()

            return {"success": True, "message": f"Template '{name}' deleted"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_template(template_id: int = None, template_type: str = None, session=None) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID or type.

        Returns:
            Template data as dict or None if not found
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            query = session.query(SMSTemplate)

            if template_id:
                template = query.filter(SMSTemplate.id == template_id).first()
            elif template_type:
                template = query.filter(SMSTemplate.template_type == template_type).first()
            else:
                return None

            if not template:
                return None

            char_count = len(template.message) if template.message else 0
            segments = 1 if char_count <= SMS_CHAR_LIMIT else (char_count // SMS_CHAR_LIMIT) + 1

            return {
                "id": template.id,
                "template_type": template.template_type,
                "name": template.name,
                "category": template.category,
                "category_label": SMS_CATEGORIES.get(template.category, template.category),
                "description": template.description,
                "message": template.message,
                "variables": template.variables or [],
                "is_custom": template.is_custom,
                "is_active": template.is_active,
                "char_count": char_count,
                "segments": segments,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
            }

        finally:
            if close_session:
                session.close()

    @staticmethod
    def list_templates(
        category: str = None,
        is_active: bool = None,
        is_custom: bool = None,
        search: str = None,
        session=None,
    ) -> List[Dict[str, Any]]:
        """
        List all templates with optional filtering.

        Args:
            category: Filter by category
            is_active: Filter by active status
            is_custom: Filter by custom/system status
            search: Search in name or description

        Returns:
            List of template dicts
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            query = session.query(SMSTemplate)

            if category:
                query = query.filter(SMSTemplate.category == category)
            if is_active is not None:
                query = query.filter(SMSTemplate.is_active == is_active)
            if is_custom is not None:
                query = query.filter(SMSTemplate.is_custom == is_custom)
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (SMSTemplate.name.ilike(search_pattern)) |
                    (SMSTemplate.description.ilike(search_pattern))
                )

            templates = query.order_by(SMSTemplate.category, SMSTemplate.name).all()

            return [
                {
                    "id": t.id,
                    "template_type": t.template_type,
                    "name": t.name,
                    "category": t.category,
                    "category_label": SMS_CATEGORIES.get(t.category, t.category),
                    "description": t.description,
                    "message": t.message,
                    "char_count": len(t.message) if t.message else 0,
                    "is_custom": t.is_custom,
                    "is_active": t.is_active,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in templates
            ]

        finally:
            if close_session:
                session.close()

    @staticmethod
    def render_template(
        template_id: int = None,
        template_type: str = None,
        variables: Dict[str, str] = None,
        session=None,
    ) -> Dict[str, Any]:
        """
        Render a template with variable substitution.

        Args:
            template_id: Template ID
            template_type: Or template type
            variables: Dict of variable values to substitute

        Returns:
            Dict with rendered message
        """
        template = SMSTemplateService.get_template(
            template_id=template_id,
            template_type=template_type,
            session=session,
        )

        if not template:
            return {"success": False, "error": "Template not found"}

        if not template["is_active"]:
            return {"success": False, "error": "Template is not active"}

        variables = variables or {}

        # Add default variables
        variables.setdefault("company_name", "Brightpath Ascend")

        # Substitute variables in message
        message = template["message"]
        for key, value in variables.items():
            message = message.replace(f"{{{key}}}", str(value))

        char_count = len(message)
        segments = 1 if char_count <= SMS_CHAR_LIMIT else (char_count // SMS_CHAR_LIMIT) + 1

        return {
            "success": True,
            "message": message,
            "char_count": char_count,
            "segments": segments,
            "template_id": template["id"],
            "template_type": template["template_type"],
        }

    @staticmethod
    def duplicate_template(
        template_id: int,
        new_name: str = None,
        new_type: str = None,
        session=None,
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing template.

        Args:
            template_id: Source template ID
            new_name: Name for the copy
            new_type: Template type for the copy

        Returns:
            Dict with new template info
        """
        template = SMSTemplateService.get_template(template_id=template_id, session=session)

        if not template:
            return {"success": False, "error": "Template not found"}

        # Generate new type and name if not provided
        base_type = template["template_type"]
        base_name = template["name"]

        if not new_type:
            new_type = f"{base_type}_copy"
        if not new_name:
            new_name = f"{base_name} (Copy)"

        return SMSTemplateService.create_template(
            template_type=new_type,
            name=new_name,
            message=template["message"],
            category=template["category"],
            description=template["description"],
            variables=template["variables"],
            is_custom=True,
            session=session,
        )

    @staticmethod
    def get_template_stats(session=None) -> Dict[str, Any]:
        """Get statistics about templates"""
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            total = session.query(SMSTemplate).count()
            active = session.query(SMSTemplate).filter(SMSTemplate.is_active == True).count()
            custom = session.query(SMSTemplate).filter(SMSTemplate.is_custom == True).count()
            system = session.query(SMSTemplate).filter(SMSTemplate.is_custom == False).count()

            # Count by category
            by_category = {}
            for category_key in SMS_CATEGORIES:
                count = session.query(SMSTemplate).filter(
                    SMSTemplate.category == category_key
                ).count()
                if count > 0:
                    by_category[category_key] = count

            return {
                "total": total,
                "active": active,
                "inactive": total - active,
                "custom": custom,
                "system": system,
                "by_category": by_category,
            }

        finally:
            if close_session:
                session.close()


# Default SMS templates to seed
DEFAULT_SMS_TEMPLATES = [
    {
        "template_type": "welcome_sms",
        "name": "Welcome SMS",
        "category": "welcome",
        "description": "Initial welcome message for new clients",
        "message": "Welcome to {company_name}! Your account is ready. Access your portal: {portal_url} Questions? Call us anytime.",
        "variables": [
            {"name": "company_name", "description": "Company name"},
            {"name": "portal_url", "description": "Portal link"},
        ],
    },
    {
        "template_type": "document_reminder_sms",
        "name": "Document Reminder",
        "category": "reminders",
        "description": "Remind client to upload documents",
        "message": "Hi {first_name}, we need your documents to proceed with your case. Please upload them at {portal_url} - {company_name}",
        "variables": [
            {"name": "first_name", "description": "Client's first name"},
            {"name": "portal_url", "description": "Portal link"},
        ],
    },
    {
        "template_type": "case_update_sms",
        "name": "Case Update",
        "category": "updates",
        "description": "Notify client of case status change",
        "message": "Hi {first_name}, your case status has been updated to: {status}. Log in to view details: {portal_url} - {company_name}",
        "variables": [
            {"name": "first_name", "description": "Client's first name"},
            {"name": "status", "description": "New status"},
            {"name": "portal_url", "description": "Portal link"},
        ],
    },
    {
        "template_type": "dispute_sent_sms",
        "name": "Dispute Sent",
        "category": "updates",
        "description": "Confirm dispute letter was mailed",
        "message": "Good news {first_name}! Your dispute letter to {bureau} has been sent. Track progress at {portal_url} - {company_name}",
        "variables": [
            {"name": "first_name", "description": "Client's first name"},
            {"name": "bureau", "description": "Bureau name"},
            {"name": "portal_url", "description": "Portal link"},
        ],
    },
    {
        "template_type": "response_received_sms",
        "name": "Bureau Response Received",
        "category": "updates",
        "description": "Notify when bureau responds",
        "message": "Hi {first_name}, we received a response from {bureau}! Log in to see the results: {portal_url} - {company_name}",
        "variables": [
            {"name": "first_name", "description": "Client's first name"},
            {"name": "bureau", "description": "Bureau name"},
            {"name": "portal_url", "description": "Portal link"},
        ],
    },
    {
        "template_type": "payment_reminder_sms",
        "name": "Payment Reminder",
        "category": "payment",
        "description": "Remind client about payment",
        "message": "Hi {first_name}, your payment of {amount} is due on {date}. Pay now at {portal_url} - {company_name}",
        "variables": [
            {"name": "first_name", "description": "Client's first name"},
            {"name": "amount", "description": "Amount due"},
            {"name": "date", "description": "Due date"},
            {"name": "portal_url", "description": "Portal link"},
        ],
    },
    {
        "template_type": "appointment_reminder_sms",
        "name": "Appointment Reminder",
        "category": "reminders",
        "description": "Remind client of upcoming call",
        "message": "Reminder: Your call with {company_name} is scheduled for {date} at {time}. Questions? Reply to this message.",
        "variables": [
            {"name": "date", "description": "Appointment date"},
            {"name": "time", "description": "Appointment time"},
        ],
    },
    {
        "template_type": "analysis_ready_sms",
        "name": "Analysis Ready",
        "category": "notifications",
        "description": "Notify when analysis is complete",
        "message": "Hi {first_name}, your credit analysis is ready! We found items that may qualify for disputes. View now: {portal_url}",
        "variables": [
            {"name": "first_name", "description": "Client's first name"},
            {"name": "portal_url", "description": "Portal link"},
        ],
    },
    {
        "template_type": "deadline_reminder_sms",
        "name": "Deadline Reminder",
        "category": "reminders",
        "description": "Alert about approaching deadline",
        "message": "Hi {first_name}, deadline approaching for {bureau} response. Only {days} days left. Need help? {portal_url} - {company_name}",
        "variables": [
            {"name": "first_name", "description": "Client's first name"},
            {"name": "bureau", "description": "Bureau name"},
            {"name": "days", "description": "Days remaining"},
            {"name": "portal_url", "description": "Portal link"},
        ],
    },
    {
        "template_type": "quick_question_sms",
        "name": "Quick Question",
        "category": "general",
        "description": "Quick check-in message",
        "message": "Hi {first_name}, just checking in! Do you have any questions about your case? Reply here or call us. - {company_name}",
        "variables": [
            {"name": "first_name", "description": "Client's first name"},
        ],
    },
]


def seed_default_sms_templates(session=None) -> Dict[str, Any]:
    """
    Seed the database with default SMS templates.
    Only creates templates that don't already exist.

    Returns:
        Dict with results of seeding operation
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    created = 0
    skipped = 0
    errors = []

    try:
        for template_data in DEFAULT_SMS_TEMPLATES:
            # Check if already exists
            existing = session.query(SMSTemplate).filter(
                SMSTemplate.template_type == template_data["template_type"]
            ).first()

            if existing:
                skipped += 1
                continue

            template = SMSTemplate(
                template_type=template_data["template_type"],
                name=template_data["name"],
                category=template_data["category"],
                description=template_data["description"],
                message=template_data["message"],
                variables=template_data.get("variables", []),
                is_custom=False,
                is_active=True,
            )

            session.add(template)
            created += 1

        session.commit()

        return {
            "success": True,
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "message": f"Created {created} SMS templates, skipped {skipped} existing",
        }

    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        if close_session:
            session.close()


# Convenience functions
def get_sms_template(template_type: str) -> Optional[Dict]:
    """Get a template by type"""
    return SMSTemplateService.get_template(template_type=template_type)


def render_sms(template_type: str, variables: Dict[str, str] = None) -> Dict[str, Any]:
    """Render an SMS template with variables"""
    return SMSTemplateService.render_template(template_type=template_type, variables=variables)


def list_all_sms_templates() -> List[Dict]:
    """List all active templates"""
    return SMSTemplateService.list_templates(is_active=True)
