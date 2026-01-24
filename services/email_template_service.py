"""
Email Template Service for Brightpath Ascend FCRA Platform

CRUD operations and template management for the Email Templates Library.
Allows staff to create, edit, and manage email templates used for client communications.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import EmailTemplate, SessionLocal
from services.email_templates import (
    COMPANY_NAME,
    DARK_COLOR,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    get_base_template,
)

# Template categories
TEMPLATE_CATEGORIES = {
    "welcome": "Welcome & Onboarding",
    "updates": "Case Updates",
    "reminders": "Reminders",
    "notifications": "Notifications",
    "payment": "Payment & Billing",
    "legal": "Legal & Compliance",
    "marketing": "Marketing",
    "general": "General",
}

# Common template variables that can be used
COMMON_VARIABLES = [
    {
        "name": "client_name",
        "description": "Client's full name",
        "example": "John Smith",
    },
    {"name": "first_name", "description": "Client's first name", "example": "John"},
    {
        "name": "email",
        "description": "Client's email address",
        "example": "john@example.com",
    },
    {
        "name": "phone",
        "description": "Client's phone number",
        "example": "(555) 123-4567",
    },
    {
        "name": "portal_url",
        "description": "Link to client portal",
        "example": "https://portal.example.com",
    },
    {"name": "company_name", "description": "Company name", "example": COMPANY_NAME},
    {
        "name": "current_date",
        "description": "Today's date",
        "example": "January 1, 2026",
    },
    {
        "name": "dispute_round",
        "description": "Current dispute round",
        "example": "Round 2",
    },
    {"name": "bureau", "description": "Credit bureau name", "example": "Equifax"},
    {"name": "status", "description": "Current case status", "example": "Active"},
]


class EmailTemplateService:
    """Service for managing email templates"""

    @staticmethod
    def get_categories() -> Dict[str, str]:
        """Get all template categories"""
        return TEMPLATE_CATEGORIES

    @staticmethod
    def get_common_variables() -> List[Dict[str, str]]:
        """Get list of common template variables"""
        return COMMON_VARIABLES

    @staticmethod
    def create_template(
        template_type: str,
        name: str,
        subject: str,
        html_content: str,
        category: str = "general",
        description: str = None,
        plain_text_content: str = None,
        variables: List[Dict] = None,
        is_custom: bool = True,
        session=None,
    ) -> Dict[str, Any]:
        """
        Create a new email template.

        Args:
            template_type: Unique identifier (e.g., 'custom_welcome')
            name: Human-readable name
            subject: Email subject line (can include variables)
            html_content: HTML body content
            category: Template category
            description: What this template is for
            plain_text_content: Plain text version
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
            existing = (
                session.query(EmailTemplate)
                .filter(EmailTemplate.template_type == template_type)
                .first()
            )
            if existing:
                return {
                    "success": False,
                    "error": f"Template type '{template_type}' already exists",
                }

            # Create new template
            template = EmailTemplate(
                template_type=template_type,
                name=name,
                category=category,
                description=description,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text_content,
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
        subject: str = None,
        html_content: str = None,
        category: str = None,
        description: str = None,
        plain_text_content: str = None,
        variables: List[Dict] = None,
        is_active: bool = None,
        session=None,
    ) -> Dict[str, Any]:
        """
        Update an existing email template.

        Returns:
            Dict with success status
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            template = (
                session.query(EmailTemplate)
                .filter(EmailTemplate.id == template_id)
                .first()
            )

            if not template:
                return {"success": False, "error": "Template not found"}

            # Update fields if provided
            if name is not None:
                template.name = name
            if subject is not None:
                template.subject = subject
            if html_content is not None:
                template.html_content = html_content
            if category is not None:
                template.category = category
            if description is not None:
                template.description = description
            if plain_text_content is not None:
                template.plain_text_content = plain_text_content
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
        Delete an email template.

        Note: System templates (is_custom=False) cannot be deleted.
        """
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            template = (
                session.query(EmailTemplate)
                .filter(EmailTemplate.id == template_id)
                .first()
            )

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
    def get_template(
        template_id: int = None, template_type: str = None, session=None
    ) -> Optional[Dict[str, Any]]:
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
            query = session.query(EmailTemplate)

            if template_id:
                template = query.filter(EmailTemplate.id == template_id).first()
            elif template_type:
                template = query.filter(
                    EmailTemplate.template_type == template_type
                ).first()
            else:
                return None

            if not template:
                return None

            return {
                "id": template.id,
                "template_type": template.template_type,
                "name": template.name,
                "category": template.category,
                "category_label": TEMPLATE_CATEGORIES.get(
                    template.category, template.category
                ),
                "description": template.description,
                "subject": template.subject,
                "html_content": template.html_content,
                "plain_text_content": template.plain_text_content,
                "variables": template.variables or [],
                "is_custom": template.is_custom,
                "is_active": template.is_active,
                "created_at": (
                    template.created_at.isoformat() if template.created_at else None
                ),
                "updated_at": (
                    template.updated_at.isoformat() if template.updated_at else None
                ),
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
            query = session.query(EmailTemplate)

            if category:
                query = query.filter(EmailTemplate.category == category)
            if is_active is not None:
                query = query.filter(EmailTemplate.is_active == is_active)
            if is_custom is not None:
                query = query.filter(EmailTemplate.is_custom == is_custom)
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (EmailTemplate.name.ilike(search_pattern))
                    | (EmailTemplate.description.ilike(search_pattern))
                )

            templates = query.order_by(EmailTemplate.category, EmailTemplate.name).all()

            return [
                {
                    "id": t.id,
                    "template_type": t.template_type,
                    "name": t.name,
                    "category": t.category,
                    "category_label": TEMPLATE_CATEGORIES.get(t.category, t.category),
                    "description": t.description,
                    "subject": t.subject,
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
            Dict with rendered subject, html, and plain text
        """
        template = EmailTemplateService.get_template(
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
        variables.setdefault("company_name", COMPANY_NAME)
        variables.setdefault("current_date", datetime.now().strftime("%B %d, %Y"))

        # Substitute variables in subject
        subject = template["subject"]
        for key, value in variables.items():
            subject = subject.replace(f"{{{key}}}", str(value))

        # Substitute variables in HTML content
        html_content = template["html_content"] or ""
        for key, value in variables.items():
            html_content = html_content.replace(f"{{{key}}}", str(value))

        # Wrap in base template if not already wrapped
        if "<html>" not in html_content.lower():
            html_content = get_base_template(html_content, subject)

        # Substitute variables in plain text
        plain_text = template["plain_text_content"] or ""
        for key, value in variables.items():
            plain_text = plain_text.replace(f"{{{key}}}", str(value))

        return {
            "success": True,
            "subject": subject,
            "html": html_content,
            "plain_text": plain_text,
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
        template = EmailTemplateService.get_template(
            template_id=template_id, session=session
        )

        if not template:
            return {"success": False, "error": "Template not found"}

        # Generate new type and name if not provided
        base_type = template["template_type"]
        base_name = template["name"]

        if not new_type:
            # Add _copy suffix or increment counter
            new_type = f"{base_type}_copy"
        if not new_name:
            new_name = f"{base_name} (Copy)"

        return EmailTemplateService.create_template(
            template_type=new_type,
            name=new_name,
            subject=template["subject"],
            html_content=template["html_content"],
            category=template["category"],
            description=template["description"],
            plain_text_content=template["plain_text_content"],
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
            total = session.query(EmailTemplate).count()
            active = (
                session.query(EmailTemplate)
                .filter(EmailTemplate.is_active == True)
                .count()
            )
            custom = (
                session.query(EmailTemplate)
                .filter(EmailTemplate.is_custom == True)
                .count()
            )
            system = (
                session.query(EmailTemplate)
                .filter(EmailTemplate.is_custom == False)
                .count()
            )

            # Count by category
            by_category = {}
            for category_key in TEMPLATE_CATEGORIES:
                count = (
                    session.query(EmailTemplate)
                    .filter(EmailTemplate.category == category_key)
                    .count()
                )
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


# Default system templates to seed
DEFAULT_TEMPLATES = [
    {
        "template_type": "welcome",
        "name": "Welcome Email",
        "category": "welcome",
        "description": "Sent to new clients after signup",
        "subject": "Welcome to {company_name}!",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "portal_url", "description": "Link to client portal"},
        ],
    },
    {
        "template_type": "document_reminder",
        "name": "Document Reminder",
        "category": "reminders",
        "description": "Remind clients to upload missing documents",
        "subject": "Action Required: Documents Needed",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "missing_docs", "description": "List of missing documents"},
            {"name": "portal_url", "description": "Link to upload documents"},
        ],
    },
    {
        "template_type": "case_update",
        "name": "Case Status Update",
        "category": "updates",
        "description": "Notify clients of case status changes",
        "subject": "Case Update: {status}",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "status", "description": "New case status"},
            {"name": "details", "description": "Additional details"},
            {"name": "portal_url", "description": "Link to view details"},
        ],
    },
    {
        "template_type": "dispute_sent",
        "name": "Dispute Letter Sent",
        "category": "updates",
        "description": "Notify when dispute letter is mailed",
        "subject": "Dispute Sent to {bureau}",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "bureau", "description": "Credit bureau name"},
            {"name": "tracking_number", "description": "Mail tracking number"},
            {"name": "portal_url", "description": "Link to track disputes"},
        ],
    },
    {
        "template_type": "cra_response",
        "name": "Bureau Response Received",
        "category": "updates",
        "description": "Notify when CRA responds to dispute",
        "subject": "Response Received from {bureau}",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "bureau", "description": "Credit bureau name"},
            {"name": "items_deleted", "description": "Number of items deleted"},
            {"name": "items_verified", "description": "Number of items verified"},
            {"name": "portal_url", "description": "Link to view response"},
        ],
    },
    {
        "template_type": "payment_reminder",
        "name": "Payment Reminder",
        "category": "payment",
        "description": "Remind clients about pending payment",
        "subject": "Payment Reminder - {amount} Due",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "amount", "description": "Amount due"},
            {"name": "due_date", "description": "Payment due date"},
            {"name": "payment_url", "description": "Link to make payment"},
        ],
    },
    {
        "template_type": "analysis_ready",
        "name": "Analysis Complete",
        "category": "updates",
        "description": "Notify when credit analysis is complete",
        "subject": "Your Credit Analysis is Ready!",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "violations_count", "description": "Number of violations found"},
            {"name": "exposure", "description": "Potential damage exposure"},
            {"name": "portal_url", "description": "Link to view analysis"},
        ],
    },
    {
        "template_type": "letters_ready",
        "name": "Dispute Letters Ready",
        "category": "updates",
        "description": "Notify when dispute letters are generated",
        "subject": "{letter_count} Dispute Letters Ready for You",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "letter_count", "description": "Number of letters"},
            {"name": "bureaus", "description": "List of bureaus"},
            {"name": "portal_url", "description": "Link to download letters"},
        ],
    },
    {
        "template_type": "deadline_approaching",
        "name": "Deadline Approaching",
        "category": "reminders",
        "description": "Alert about upcoming deadlines",
        "subject": "Important: Deadline Approaching for {bureau}",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "bureau", "description": "Bureau or entity name"},
            {"name": "deadline_date", "description": "The deadline date"},
            {"name": "days_remaining", "description": "Days until deadline"},
            {"name": "portal_url", "description": "Link to view details"},
        ],
    },
    {
        "template_type": "violation_alert",
        "name": "FCRA Violation Alert",
        "category": "legal",
        "description": "Alert about detected FCRA violations",
        "subject": "FCRA Violation Detected - {bureau}",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "bureau", "description": "Bureau name"},
            {"name": "violation_type", "description": "Type of violation"},
            {"name": "account_name", "description": "Related account"},
            {"name": "portal_url", "description": "Link to view details"},
        ],
    },
    {
        "template_type": "booking_confirmation",
        "name": "Call Booking Confirmation",
        "category": "notifications",
        "description": "Confirm scheduled Q&A call booking",
        "subject": "Your Call is Scheduled for {date}",
        "variables": [
            {"name": "client_name", "description": "Client's full name"},
            {"name": "date", "description": "Call date"},
            {"name": "time", "description": "Call time"},
            {"name": "duration", "description": "Call duration in minutes"},
            {"name": "portal_url", "description": "Link to manage booking"},
        ],
    },
]


def seed_default_templates(session=None) -> Dict[str, Any]:
    """
    Seed the database with default system templates.
    Only creates templates that don't already exist.

    Returns:
        Dict with results of seeding operation
    """
    from services.email_templates import (
        analysis_ready_email,
        case_update_email,
        cra_response_email,
        dispute_sent_email,
        document_reminder_email,
        letters_ready_email,
        payment_reminder_email,
        welcome_email,
    )

    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    created = 0
    skipped = 0
    errors = []

    try:
        for template_data in DEFAULT_TEMPLATES:
            # Check if already exists
            existing = (
                session.query(EmailTemplate)
                .filter(EmailTemplate.template_type == template_data["template_type"])
                .first()
            )

            if existing:
                skipped += 1
                continue

            # Get HTML content from existing template functions if available
            html_content = ""
            template_type = template_data["template_type"]

            if template_type == "welcome":
                html_content = welcome_email("{client_name}", "{portal_url}")
            elif template_type == "document_reminder":
                html_content = document_reminder_email(
                    "{client_name}", ["{missing_docs}"], "{portal_url}"
                )
            elif template_type == "case_update":
                html_content = case_update_email(
                    "{client_name}", "{status}", "{details}", "{portal_url}"
                )
            elif template_type == "dispute_sent":
                html_content = dispute_sent_email(
                    "{client_name}", "{bureau}", "{tracking_number}", "{portal_url}"
                )
            elif template_type == "cra_response":
                html_content = cra_response_email(
                    "{client_name}", "{bureau}", "{result_summary}", "{portal_url}"
                )
            elif template_type == "payment_reminder":
                html_content = payment_reminder_email(
                    "{client_name}", "{amount}", "{due_date}", "{payment_url}"
                )
            elif template_type == "analysis_ready":
                html_content = analysis_ready_email(
                    "{client_name}", "{violations_count}", "{exposure}", "{portal_url}"
                )
            elif template_type == "letters_ready":
                html_content = letters_ready_email(
                    "{client_name}", "{letter_count}", ["{bureaus}"], "{portal_url}"
                )
            else:
                # Generate basic HTML for templates without existing functions
                html_content = f"""
                <h2 style="color: #1a1a2e; margin: 0 0 20px 0; font-size: 24px;">Hi {{first_name}},</h2>
                <p style="color: #334155; line-height: 1.6; font-size: 16px;">
                    This is a notification from {{company_name}}.
                </p>
                """

            template = EmailTemplate(
                template_type=template_type,
                name=template_data["name"],
                category=template_data["category"],
                description=template_data["description"],
                subject=template_data["subject"],
                html_content=html_content,
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
            "message": f"Created {created} templates, skipped {skipped} existing",
        }

    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        if close_session:
            session.close()


# Convenience functions
def get_template(template_type: str) -> Optional[Dict]:
    """Get a template by type"""
    return EmailTemplateService.get_template(template_type=template_type)


def render_email(
    template_type: str, variables: Dict[str, str] = None
) -> Dict[str, Any]:
    """Render an email template with variables"""
    return EmailTemplateService.render_template(
        template_type=template_type, variables=variables
    )


def list_all_templates() -> List[Dict]:
    """List all active templates"""
    return EmailTemplateService.list_templates(is_active=True)
