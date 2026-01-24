"""
Letter Template Builder Service

Manage customizable dispute letter templates with variable substitution,
versioning, and letter generation capabilities.
"""

import json
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from database import (
    Case,
    Client,
    DisputeItem,
    GeneratedLetter,
    LetterTemplate,
    LetterTemplateVersion,
    Staff,
    Violation,
    get_db,
)

# Template categories
CATEGORIES = {
    "initial_dispute": {
        "name": "Initial Dispute",
        "description": "First dispute letters to bureaus",
        "rounds": [1],
    },
    "mov_demand": {
        "name": "Method of Verification (MOV)",
        "description": "Cushman-style MOV demand letters",
        "rounds": [2],
    },
    "escalation": {
        "name": "Regulatory Escalation",
        "description": "CFPB, state AG, FTC complaints",
        "rounds": [3, 4],
    },
    "follow_up": {
        "name": "Follow-Up",
        "description": "Follow-up on pending disputes",
        "rounds": None,  # Any round
    },
    "pre_litigation": {
        "name": "Pre-Litigation",
        "description": "Pre-lawsuit demand letters",
        "rounds": [4],
    },
    "furnisher": {
        "name": "Furnisher Dispute",
        "description": "Direct disputes to furnishers",
        "rounds": None,
    },
    "collector": {
        "name": "Debt Collector",
        "description": "FDCPA debt validation letters",
        "rounds": None,
    },
    "general": {
        "name": "General",
        "description": "General purpose templates",
        "rounds": None,
    },
}

# Target types
TARGET_TYPES = {
    "bureau": "Credit Bureau",
    "furnisher": "Furnisher/Creditor",
    "collector": "Debt Collector",
    "all": "All Targets",
}

# Common template variables
COMMON_VARIABLES = [
    {
        "name": "client_name",
        "description": "Full name of the client",
        "example": "John Smith",
    },
    {
        "name": "client_first_name",
        "description": "Client first name",
        "example": "John",
    },
    {"name": "client_last_name", "description": "Client last name", "example": "Smith"},
    {
        "name": "client_address",
        "description": "Full mailing address",
        "example": "123 Main St, Anytown, CA 90210",
    },
    {
        "name": "client_street",
        "description": "Street address",
        "example": "123 Main St",
    },
    {"name": "client_city", "description": "City", "example": "Anytown"},
    {"name": "client_state", "description": "State", "example": "CA"},
    {"name": "client_zip", "description": "ZIP code", "example": "90210"},
    {"name": "client_dob", "description": "Date of birth", "example": "01/15/1980"},
    {"name": "client_ssn_last4", "description": "Last 4 of SSN", "example": "1234"},
    {
        "name": "client_phone",
        "description": "Phone number",
        "example": "(555) 123-4567",
    },
    {
        "name": "client_email",
        "description": "Email address",
        "example": "john@example.com",
    },
    {"name": "current_date", "description": "Today's date", "example": "01/03/2026"},
    {"name": "bureau_name", "description": "Target bureau name", "example": "Equifax"},
    {
        "name": "bureau_address",
        "description": "Bureau mailing address",
        "example": "P.O. Box 740241, Atlanta, GA 30374",
    },
    {"name": "dispute_round", "description": "Current dispute round", "example": "2"},
    {
        "name": "account_name",
        "description": "Creditor/account name",
        "example": "Capital One",
    },
    {
        "name": "account_number",
        "description": "Account number (masked)",
        "example": "XXXX-XXXX-1234",
    },
    {
        "name": "dispute_items",
        "description": "List of disputed items",
        "example": "1. Capital One - $5,000\n2. Chase Bank - $2,500",
    },
    {
        "name": "violation_summary",
        "description": "Summary of FCRA violations",
        "example": "Re-aging of account, Inaccurate balance",
    },
    {
        "name": "deadline_date",
        "description": "Response deadline",
        "example": "02/02/2026",
    },
    {
        "name": "company_name",
        "description": "Your company name",
        "example": "Brightpath Ascend Group",
    },
    {"name": "staff_name", "description": "Staff member name", "example": "Jane Doe"},
]

# Bureau addresses
BUREAU_ADDRESSES = {
    "equifax": {
        "name": "Equifax Information Services LLC",
        "address": "P.O. Box 740241\nAtlanta, GA 30374-0241",
    },
    "experian": {
        "name": "Experian",
        "address": "P.O. Box 4500\nAllen, TX 75013",
    },
    "transunion": {
        "name": "TransUnion LLC",
        "address": "P.O. Box 2000\nChester, PA 19016",
    },
}


class LetterTemplateService:
    """Service for managing letter templates and generating letters"""

    def __init__(self):
        self.db = None

    def _get_db(self):
        if not self.db:
            self.db = get_db()
        return self.db

    def _close_db(self):
        if self.db:
            self.db.close()
            self.db = None

    # =========================================================================
    # TEMPLATE CRUD OPERATIONS
    # =========================================================================

    def create_template(
        self,
        name: str,
        code: str,
        category: str,
        content: str,
        dispute_round: Optional[int] = None,
        target_type: str = "bureau",
        subject: Optional[str] = None,
        footer: Optional[str] = None,
        variables: Optional[List[Dict]] = None,
        required_attachments: Optional[List[str]] = None,
        recommended_for: Optional[List[str]] = None,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        legal_basis: Optional[str] = None,
        is_system: bool = False,
        created_by_staff_id: Optional[int] = None,
    ) -> Dict:
        """Create a new letter template"""
        db = self._get_db()
        try:
            # Check for duplicate code
            existing = (
                db.query(LetterTemplate).filter(LetterTemplate.code == code).first()
            )
            if existing:
                return {
                    "success": False,
                    "error": f'Template code "{code}" already exists',
                }

            template = LetterTemplate(
                name=name,
                code=code,
                category=category,
                content=content,
                dispute_round=dispute_round,
                target_type=target_type,
                subject=subject,
                footer=footer,
                variables=variables or self._extract_variables(content),
                required_attachments=required_attachments,
                recommended_for=recommended_for,
                description=description,
                instructions=instructions,
                legal_basis=legal_basis,
                is_system=is_system,
                is_active=True,
                version=1,
                use_count=0,
                created_by_staff_id=created_by_staff_id,
            )

            db.add(template)
            db.commit()
            db.refresh(template)

            # Create initial version
            self._create_version(template, "Initial version", created_by_staff_id)

            return {
                "success": True,
                "template": template.to_dict(),
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            self._close_db()

    def update_template(
        self,
        template_id: int,
        updates: Dict,
        change_summary: Optional[str] = None,
        staff_id: Optional[int] = None,
    ) -> Dict:
        """Update an existing template"""
        db = self._get_db()
        try:
            template = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.id == template_id)
                .first()
            )

            if not template:
                return {"success": False, "error": "Template not found"}

            # Check if content changed (requires new version)
            content_changed = (
                "content" in updates and updates["content"] != template.content
            )

            # Apply updates
            allowed_fields = [
                "name",
                "category",
                "content",
                "dispute_round",
                "target_type",
                "subject",
                "footer",
                "variables",
                "required_attachments",
                "recommended_for",
                "description",
                "instructions",
                "legal_basis",
                "is_active",
            ]

            for field in allowed_fields:
                if field in updates:
                    setattr(template, field, updates[field])

            # Auto-extract variables if content changed
            if content_changed:
                if "variables" not in updates:
                    template.variables = self._extract_variables(template.content)
                template.version += 1

            template.updated_at = datetime.utcnow()
            db.commit()

            # Create version if content changed
            if content_changed:
                self._create_version(
                    template, change_summary or "Content updated", staff_id
                )

            db.refresh(template)
            return {
                "success": True,
                "template": template.to_dict(),
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            self._close_db()

    def delete_template(self, template_id: int) -> Dict:
        """Delete a template (soft delete by setting is_active=False for system templates)"""
        db = self._get_db()
        try:
            template = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.id == template_id)
                .first()
            )

            if not template:
                return {"success": False, "error": "Template not found"}

            if template.is_system:
                # Soft delete for system templates
                template.is_active = False
                db.commit()
                return {"success": True, "message": "System template deactivated"}
            else:
                # Hard delete for custom templates
                db.delete(template)
                db.commit()
                return {"success": True, "message": "Template deleted"}

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            self._close_db()

    def get_template(self, template_id: int) -> Optional[Dict]:
        """Get a template by ID"""
        db = self._get_db()
        try:
            template = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.id == template_id)
                .first()
            )

            if not template:
                return None

            return template.to_dict()
        finally:
            self._close_db()

    def get_template_by_code(self, code: str) -> Optional[Dict]:
        """Get a template by code"""
        db = self._get_db()
        try:
            template = (
                db.query(LetterTemplate).filter(LetterTemplate.code == code).first()
            )

            if not template:
                return None

            return template.to_dict()
        finally:
            self._close_db()

    def list_templates(
        self,
        category: Optional[str] = None,
        dispute_round: Optional[int] = None,
        target_type: Optional[str] = None,
        is_active: Optional[bool] = True,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """List templates with filtering"""
        db = self._get_db()
        try:
            query = db.query(LetterTemplate)

            if category:
                query = query.filter(LetterTemplate.category == category)
            if dispute_round:
                query = query.filter(
                    (LetterTemplate.dispute_round == dispute_round)
                    | (LetterTemplate.dispute_round.is_(None))
                )
            if target_type:
                query = query.filter(
                    (LetterTemplate.target_type == target_type)
                    | (LetterTemplate.target_type == "all")
                )
            if is_active is not None:
                query = query.filter(LetterTemplate.is_active == is_active)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (LetterTemplate.name.ilike(search_term))
                    | (LetterTemplate.code.ilike(search_term))
                    | (LetterTemplate.description.ilike(search_term))
                )

            query = query.order_by(LetterTemplate.category, LetterTemplate.name)
            query = query.limit(limit).offset(offset)

            return [t.to_dict() for t in query.all()]
        finally:
            self._close_db()

    def duplicate_template(
        self,
        template_id: int,
        new_name: str,
        new_code: str,
        staff_id: Optional[int] = None,
    ) -> Dict:
        """Duplicate an existing template"""
        db = self._get_db()
        try:
            original = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.id == template_id)
                .first()
            )

            if not original:
                return {"success": False, "error": "Original template not found"}

            # Check for duplicate code
            existing = (
                db.query(LetterTemplate).filter(LetterTemplate.code == new_code).first()
            )
            if existing:
                return {
                    "success": False,
                    "error": f'Template code "{new_code}" already exists',
                }

            # Create new template
            new_template = LetterTemplate(
                name=new_name,
                code=new_code,
                category=original.category,
                content=original.content,
                dispute_round=original.dispute_round,
                target_type=original.target_type,
                subject=original.subject,
                footer=original.footer,
                variables=original.variables,
                required_attachments=original.required_attachments,
                recommended_for=original.recommended_for,
                description=f"Duplicated from: {original.name}",
                instructions=original.instructions,
                legal_basis=original.legal_basis,
                is_system=False,  # Always custom
                is_active=True,
                version=1,
                parent_id=original.id,
                use_count=0,
                created_by_staff_id=staff_id,
            )

            db.add(new_template)
            db.commit()
            db.refresh(new_template)

            # Create initial version
            self._create_version(
                new_template, f"Duplicated from {original.name}", staff_id
            )

            return {
                "success": True,
                "template": new_template.to_dict(),
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            self._close_db()

    # =========================================================================
    # VERSION MANAGEMENT
    # =========================================================================

    def _create_version(
        self,
        template: LetterTemplate,
        change_summary: str,
        staff_id: Optional[int] = None,
    ) -> None:
        """Create a version snapshot of the template"""
        db = self._get_db()
        try:
            version = LetterTemplateVersion(
                template_id=template.id,
                version_number=template.version,
                name=template.name,
                content=template.content,
                footer=template.footer,
                variables=template.variables,
                change_summary=change_summary,
                changed_by_staff_id=staff_id,
            )
            db.add(version)
            db.commit()
        except Exception:
            db.rollback()

    def get_template_versions(self, template_id: int) -> List[Dict]:
        """Get version history for a template"""
        db = self._get_db()
        try:
            versions = (
                db.query(LetterTemplateVersion)
                .filter(LetterTemplateVersion.template_id == template_id)
                .order_by(LetterTemplateVersion.version_number.desc())
                .all()
            )

            return [v.to_dict() for v in versions]
        finally:
            self._close_db()

    def get_version(self, version_id: int) -> Optional[Dict]:
        """Get a specific version"""
        db = self._get_db()
        try:
            version = (
                db.query(LetterTemplateVersion)
                .filter(LetterTemplateVersion.id == version_id)
                .first()
            )

            return version.to_dict() if version else None
        finally:
            self._close_db()

    def restore_version(
        self,
        template_id: int,
        version_id: int,
        staff_id: Optional[int] = None,
    ) -> Dict:
        """Restore a template to a previous version"""
        db = self._get_db()
        try:
            template = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.id == template_id)
                .first()
            )

            if not template:
                return {"success": False, "error": "Template not found"}

            version = (
                db.query(LetterTemplateVersion)
                .filter(
                    LetterTemplateVersion.id == version_id,
                    LetterTemplateVersion.template_id == template_id,
                )
                .first()
            )

            if not version:
                return {"success": False, "error": "Version not found"}

            # Update template with version content
            template.name = version.name
            template.content = version.content
            template.footer = version.footer
            template.variables = version.variables
            template.version += 1
            template.updated_at = datetime.utcnow()

            db.commit()

            # Create new version entry for the restore
            self._create_version(
                template, f"Restored from version {version.version_number}", staff_id
            )

            db.refresh(template)
            return {
                "success": True,
                "template": template.to_dict(),
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            self._close_db()

    # =========================================================================
    # VARIABLE HANDLING
    # =========================================================================

    def _extract_variables(self, content: str) -> List[Dict]:
        """Extract variable placeholders from content"""
        if not content:
            return []

        # Find all {variable_name} placeholders
        pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
        matches = re.findall(pattern, content)

        # Get unique variables
        unique_vars = list(set(matches))

        # Map to common variable definitions or create generic ones
        variables = []
        common_var_map = {v["name"]: v for v in COMMON_VARIABLES}

        for var_name in unique_vars:
            if var_name in common_var_map:
                variables.append(common_var_map[var_name])
            else:
                variables.append(
                    {
                        "name": var_name,
                        "description": f"Custom variable: {var_name}",
                        "example": f"[{var_name}]",
                    }
                )

        return sorted(variables, key=lambda x: x["name"])

    def render_template(
        self,
        template_id: int,
        variables: Dict[str, Any],
    ) -> Dict:
        """Render a template with variable substitution"""
        db = self._get_db()
        try:
            template = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.id == template_id)
                .first()
            )

            if not template:
                return {"success": False, "error": "Template not found"}

            content = template.content
            subject = template.subject or ""
            footer = template.footer or ""

            # Substitute variables
            for var_name, var_value in variables.items():
                placeholder = "{" + var_name + "}"
                content = content.replace(
                    placeholder, str(var_value) if var_value else ""
                )
                subject = subject.replace(
                    placeholder, str(var_value) if var_value else ""
                )
                footer = footer.replace(
                    placeholder, str(var_value) if var_value else ""
                )

            return {
                "success": True,
                "subject": subject,
                "content": content,
                "footer": footer,
                "full_content": f"{content}\n\n{footer}".strip(),
            }

        finally:
            self._close_db()

    def get_client_variables(
        self, client_id: int, bureau: Optional[str] = None
    ) -> Dict:
        """Get variable values for a client"""
        db = self._get_db()
        try:
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {}

            # Build address
            address_parts = []
            if client.address_street:
                address_parts.append(client.address_street)
            city_state_zip = []
            if client.address_city:
                city_state_zip.append(client.address_city)
            if client.address_state:
                city_state_zip.append(client.address_state)
            if client.address_zip:
                city_state_zip.append(client.address_zip)
            if city_state_zip:
                address_parts.append(
                    ", ".join(city_state_zip[:2])
                    + " "
                    + (city_state_zip[2] if len(city_state_zip) > 2 else "")
                )

            # Get dispute items
            items = (
                db.query(DisputeItem).filter(DisputeItem.client_id == client_id).all()
            )
            dispute_items_text = (
                "\n".join(
                    [
                        f"{i+1}. {item.creditor_name or item.account_name} - ${item.balance or 'N/A'}"
                        for i, item in enumerate(items)
                    ]
                )
                if items
                else "No items listed"
            )

            # Get violations
            violations = (
                db.query(Violation).filter(Violation.client_id == client_id).all()
            )
            violation_summary = (
                ", ".join([v.violation_type for v in violations])
                if violations
                else "None identified"
            )

            # Bureau info
            bureau_info = BUREAU_ADDRESSES.get(bureau.lower() if bureau else "", {})

            variables = {
                "client_name": client.name
                or f"{client.first_name} {client.last_name}".strip(),
                "client_first_name": client.first_name or "",
                "client_last_name": client.last_name or "",
                "client_address": "\n".join(address_parts),
                "client_street": client.address_street or "",
                "client_city": client.address_city or "",
                "client_state": client.address_state or "",
                "client_zip": client.address_zip or "",
                "client_dob": (
                    client.date_of_birth.strftime("%m/%d/%Y")
                    if client.date_of_birth
                    else ""
                ),
                "client_ssn_last4": client.ssn_last_four or "",
                "client_phone": client.phone or "",
                "client_email": client.email or "",
                "current_date": date.today().strftime("%m/%d/%Y"),
                "bureau_name": bureau_info.get("name", bureau or ""),
                "bureau_address": bureau_info.get("address", ""),
                "dispute_round": str(client.current_dispute_round or 1),
                "dispute_items": dispute_items_text,
                "violation_summary": violation_summary,
                "deadline_date": (
                    date.today().replace(day=date.today().day + 30)
                ).strftime("%m/%d/%Y"),
                "company_name": "Brightpath Ascend Group",
                "staff_name": "",  # To be filled by caller
            }

            return variables

        finally:
            self._close_db()

    # =========================================================================
    # LETTER GENERATION
    # =========================================================================

    def generate_letter(
        self,
        template_id: int,
        client_id: int,
        target_type: str,
        target_name: str,
        custom_variables: Optional[Dict] = None,
        staff_id: Optional[int] = None,
        case_id: Optional[int] = None,
    ) -> Dict:
        """Generate a letter from a template for a client"""
        db = self._get_db()
        try:
            template = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.id == template_id)
                .first()
            )

            if not template:
                return {"success": False, "error": "Template not found"}

            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {"success": False, "error": "Client not found"}

            # Get base variables
            variables = self.get_client_variables(client_id, target_name)

            # Add staff name if provided
            if staff_id:
                staff = db.query(Staff).filter(Staff.id == staff_id).first()
                if staff:
                    variables["staff_name"] = (
                        f"{staff.first_name} {staff.last_name}".strip()
                    )

            # Override with custom variables
            if custom_variables:
                variables.update(custom_variables)

            # Render content
            render_result = self.render_template(template_id, variables)
            if not render_result.get("success"):
                return render_result

            # Create generated letter record
            generated = GeneratedLetter(
                template_id=template_id,
                template_version=template.version,
                client_id=client_id,
                case_id=case_id,
                dispute_round=client.current_dispute_round,
                target_type=target_type,
                target_name=target_name,
                subject=render_result["subject"],
                content=render_result["full_content"],
                variables_used=variables,
                status="draft",
            )

            db.add(generated)

            # Update template usage
            template.use_count = (template.use_count or 0) + 1
            template.last_used_at = datetime.utcnow()

            db.commit()
            db.refresh(generated)

            return {
                "success": True,
                "letter": generated.to_dict(),
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            self._close_db()

    def get_generated_letter(self, letter_id: int) -> Optional[Dict]:
        """Get a generated letter by ID"""
        db = self._get_db()
        try:
            letter = (
                db.query(GeneratedLetter)
                .filter(GeneratedLetter.id == letter_id)
                .first()
            )

            return letter.to_dict() if letter else None
        finally:
            self._close_db()

    def list_generated_letters(
        self,
        client_id: Optional[int] = None,
        template_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """List generated letters with filtering"""
        db = self._get_db()
        try:
            query = db.query(GeneratedLetter)

            if client_id:
                query = query.filter(GeneratedLetter.client_id == client_id)
            if template_id:
                query = query.filter(GeneratedLetter.template_id == template_id)
            if status:
                query = query.filter(GeneratedLetter.status == status)

            query = query.order_by(GeneratedLetter.created_at.desc())
            query = query.limit(limit).offset(offset)

            return [l.to_dict() for l in query.all()]
        finally:
            self._close_db()

    def update_letter_status(
        self,
        letter_id: int,
        status: str,
        sent_method: Optional[str] = None,
        tracking_number: Optional[str] = None,
        staff_id: Optional[int] = None,
    ) -> Dict:
        """Update the status of a generated letter"""
        db = self._get_db()
        try:
            letter = (
                db.query(GeneratedLetter)
                .filter(GeneratedLetter.id == letter_id)
                .first()
            )

            if not letter:
                return {"success": False, "error": "Letter not found"}

            letter.status = status
            if sent_method:
                letter.sent_method = sent_method
            if tracking_number:
                letter.tracking_number = tracking_number
            if status == "sent":
                letter.sent_date = datetime.utcnow()
                letter.sent_by_staff_id = staff_id

            letter.updated_at = datetime.utcnow()
            db.commit()

            return {
                "success": True,
                "letter": letter.to_dict(),
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            self._close_db()

    # =========================================================================
    # DASHBOARD & STATS
    # =========================================================================

    def get_dashboard_summary(self) -> Dict:
        """Get dashboard summary statistics"""
        db = self._get_db()
        try:
            total = db.query(LetterTemplate).count()
            active = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.is_active == True)
                .count()
            )
            system = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.is_system == True)
                .count()
            )
            custom = total - system

            # Generated letters stats
            total_generated = db.query(GeneratedLetter).count()
            letters_today = (
                db.query(GeneratedLetter)
                .filter(
                    GeneratedLetter.created_at
                    >= datetime.utcnow().replace(hour=0, minute=0, second=0)
                )
                .count()
            )
            letters_sent = (
                db.query(GeneratedLetter)
                .filter(GeneratedLetter.status == "sent")
                .count()
            )

            # Category breakdown
            from sqlalchemy import func

            category_counts = (
                db.query(LetterTemplate.category, func.count(LetterTemplate.id))
                .filter(LetterTemplate.is_active == True)
                .group_by(LetterTemplate.category)
                .all()
            )

            categories = {cat: count for cat, count in category_counts}

            # Most used templates
            most_used = (
                db.query(LetterTemplate)
                .filter(LetterTemplate.is_active == True)
                .order_by(LetterTemplate.use_count.desc())
                .limit(5)
                .all()
            )

            return {
                "total_templates": total,
                "active_templates": active,
                "system_templates": system,
                "custom_templates": custom,
                "total_generated": total_generated,
                "letters_today": letters_today,
                "letters_sent": letters_sent,
                "categories": categories,
                "most_used": [t.to_dict() for t in most_used],
            }

        finally:
            self._close_db()

    # =========================================================================
    # SEED DEFAULT TEMPLATES
    # =========================================================================

    def seed_default_templates(self) -> Dict:
        """Seed the database with default system templates"""
        db = self._get_db()
        try:
            templates_created = 0

            default_templates = [
                {
                    "name": "Initial Dispute - FCRA Section 611",
                    "code": "initial_dispute_611",
                    "category": "initial_dispute",
                    "dispute_round": 1,
                    "target_type": "bureau",
                    "description": "Standard initial dispute letter citing FCRA Section 611",
                    "content": """Re: Dispute of Inaccurate Information - FCRA Section 611

Dear {bureau_name},

I am writing to dispute inaccurate information in my credit file. I am exercising my rights under the Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681i, which requires you to conduct a reasonable investigation of disputed items.

My Information:
Name: {client_name}
Address: {client_address}
Date of Birth: {client_dob}
SSN (last 4): XXX-XX-{client_ssn_last4}

I am disputing the following items:

{dispute_items}

These items are inaccurate because:
{violation_summary}

Pursuant to FCRA Section 611(a), you are required to:
1. Conduct a reasonable investigation of the disputed items
2. Forward all relevant information to the furnisher
3. Provide me with written results within 30 days
4. Delete or modify any item found to be inaccurate or unverifiable

Please investigate these matters and correct my credit report accordingly.

Sincerely,

{client_name}
{client_address}
{current_date}""",
                    "legal_basis": "FCRA Section 611 (15 U.S.C. § 1681i)",
                },
                {
                    "name": "Method of Verification Demand",
                    "code": "mov_demand",
                    "category": "mov_demand",
                    "dispute_round": 2,
                    "target_type": "bureau",
                    "description": "Cushman-style MOV demand letter for Round 2",
                    "content": """Re: Demand for Method of Verification - FCRA Section 611(a)(7)

Dear {bureau_name},

I previously disputed the following items on my credit report, and you indicated they were "verified." However, FCRA Section 611(a)(7) requires you to provide me with a description of the procedure used to determine the accuracy of the disputed information, including the business name and address of any furnisher contacted.

Previously Disputed Items:
{dispute_items}

I am formally requesting that you provide me with:

1. The method of verification used for each disputed item
2. The name, address, and telephone number of each furnisher contacted
3. All documentation received from furnishers during your investigation
4. The date your investigation was completed

Per FCRA Section 611(a)(7), this information must be provided within 15 days of your receipt of this request.

If you cannot provide this documentation, the disputed items must be deleted pursuant to FCRA Section 611(a)(5).

Failure to comply with this request will be documented and may be used in any future legal proceedings.

Sincerely,

{client_name}
{client_address}
{current_date}""",
                    "legal_basis": "FCRA Section 611(a)(7) (15 U.S.C. § 1681i(a)(7))",
                },
                {
                    "name": "CFPB Complaint Draft",
                    "code": "cfpb_complaint",
                    "category": "escalation",
                    "dispute_round": 3,
                    "target_type": "bureau",
                    "description": "CFPB complaint draft for regulatory escalation",
                    "content": """Consumer Financial Protection Bureau Complaint

Consumer Information:
Name: {client_name}
Address: {client_address}
Phone: {client_phone}
Email: {client_email}

Company Being Complained About:
{bureau_name}

Issue:
I have previously disputed inaccurate items on my credit report. Despite multiple disputes, {bureau_name} has failed to conduct a reasonable investigation as required by FCRA Section 611.

Specific Issues:
{dispute_items}

What Happened:
1. I sent my initial dispute on [DATE]
2. The bureau claimed to "verify" the items without providing proof
3. I requested Method of Verification documentation
4. The bureau failed to provide adequate documentation
5. The inaccurate items remain on my report

FCRA Violations:
{violation_summary}

Desired Resolution:
1. Delete all inaccurate items from my credit report
2. Provide documentation of investigation procedures
3. Correct any procedural failures

Supporting Documents:
- Copy of initial dispute letter
- Copy of MOV request
- All responses from bureau

{current_date}
{client_name}""",
                    "legal_basis": "FCRA Section 611, Consumer Financial Protection Act",
                },
                {
                    "name": "Pre-Litigation Demand",
                    "code": "pre_litigation_demand",
                    "category": "pre_litigation",
                    "dispute_round": 4,
                    "target_type": "bureau",
                    "description": "Final demand letter before filing lawsuit",
                    "content": """FINAL DEMAND BEFORE LEGAL ACTION

SENT VIA CERTIFIED MAIL - RETURN RECEIPT REQUESTED

{current_date}

{bureau_name}
{bureau_address}

Re: Final Demand - {client_name}

Dear Sir or Madam:

This letter serves as FINAL DEMAND before I pursue legal action against {bureau_name} for willful and negligent violations of the Fair Credit Reporting Act.

Despite multiple good-faith disputes, {bureau_name} has failed to:
1. Conduct reasonable investigations of disputed items
2. Provide method of verification documentation
3. Delete inaccurate, unverifiable information

DISPUTED ITEMS STILL APPEARING:
{dispute_items}

FCRA VIOLATIONS DOCUMENTED:
{violation_summary}

LEGAL REMEDIES AVAILABLE:
- Statutory damages: $100-$1,000 per willful violation (15 U.S.C. § 1681n)
- Punitive damages for willful noncompliance
- Actual damages for negligent violations (15 U.S.C. § 1681o)
- Attorney's fees and costs

DEMAND:
You have TEN (10) DAYS from receipt of this letter to:
1. Delete all disputed inaccurate items
2. Provide written confirmation of deletions
3. Provide method of verification for any items not deleted

Failure to respond will result in immediate filing of a federal lawsuit without further notice.

This letter is written without prejudice to any and all rights and remedies available under law.

Sincerely,

{client_name}
{client_address}

CC: Attorney of Record""",
                    "legal_basis": "FCRA Sections 616-617 (15 U.S.C. §§ 1681n-1681o)",
                },
                {
                    "name": "Debt Validation Letter",
                    "code": "debt_validation",
                    "category": "collector",
                    "target_type": "collector",
                    "description": "FDCPA debt validation request",
                    "content": """DEBT VALIDATION REQUEST
SENT VIA CERTIFIED MAIL - RETURN RECEIPT REQUESTED

{current_date}

{account_name}
[Collector Address]

Re: Account Number: {account_number}

Dear Sir or Madam:

I am writing in response to your communication regarding the above-referenced account. Pursuant to the Fair Debt Collection Practices Act (FDCPA), 15 U.S.C. § 1692g, I am requesting validation of this debt.

Please provide the following:
1. The amount of the debt and an itemized accounting
2. The name of the original creditor
3. Proof that you are licensed to collect in my state
4. A copy of the original signed agreement
5. Documentation showing the chain of ownership
6. Proof that the statute of limitations has not expired

IMPORTANT NOTICE:
Until you provide validation, you must:
- Cease all collection activities
- Not report this debt to any credit bureau
- Not sell or transfer this debt

If you cannot validate this debt within 30 days, you must delete any reporting to credit bureaus and cease all collection efforts.

This is not a refusal to pay, but a request for verification as provided under federal law.

Sincerely,

{client_name}
{client_address}""",
                    "legal_basis": "FDCPA Section 809 (15 U.S.C. § 1692g)",
                },
                {
                    "name": "Furnisher Direct Dispute",
                    "code": "furnisher_dispute",
                    "category": "furnisher",
                    "target_type": "furnisher",
                    "description": "Direct dispute letter to furnisher/creditor",
                    "content": """Re: Dispute of Inaccurate Information - Direct Dispute to Furnisher

{current_date}

{account_name}
[Furnisher Address]

Re: Account Number: {account_number}

Dear Sir or Madam:

I am writing to dispute inaccurate information you are furnishing to credit reporting agencies regarding my account. Under FCRA Section 623(a)(8), as a furnisher of information, you are required to investigate disputes sent directly by consumers.

DISPUTED INFORMATION:
{dispute_items}

REASON FOR DISPUTE:
{violation_summary}

LEGAL REQUIREMENTS:
Pursuant to FCRA Section 623(b), upon receiving notice of a dispute from a credit reporting agency, you must:
1. Conduct an investigation of the disputed information
2. Review all relevant information provided
3. Report the results to all credit bureaus
4. Modify, delete, or permanently block reporting of inaccurate information

I am requesting that you:
1. Investigate this dispute within 30 days
2. Correct the inaccurate information with all credit bureaus
3. Provide me with written confirmation of your investigation results

Please be advised that I am documenting all communications and may pursue legal remedies if you fail to comply with FCRA requirements.

Sincerely,

{client_name}
{client_address}""",
                    "legal_basis": "FCRA Section 623 (15 U.S.C. § 1681s-2)",
                },
            ]

            for template_data in default_templates:
                # Check if already exists
                existing = (
                    db.query(LetterTemplate)
                    .filter(LetterTemplate.code == template_data["code"])
                    .first()
                )

                if not existing:
                    template = LetterTemplate(
                        name=template_data["name"],
                        code=template_data["code"],
                        category=template_data["category"],
                        dispute_round=template_data.get("dispute_round"),
                        target_type=template_data.get("target_type", "bureau"),
                        content=template_data["content"],
                        description=template_data.get("description"),
                        legal_basis=template_data.get("legal_basis"),
                        is_system=True,
                        is_active=True,
                        version=1,
                        variables=self._extract_variables(template_data["content"]),
                    )
                    db.add(template)
                    templates_created += 1

            db.commit()

            return {
                "success": True,
                "templates_created": templates_created,
                "message": f"Created {templates_created} default templates",
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            self._close_db()

    # =========================================================================
    # STATIC HELPER METHODS
    # =========================================================================

    @staticmethod
    def get_categories() -> Dict:
        """Get available template categories"""
        return CATEGORIES

    @staticmethod
    def get_target_types() -> Dict:
        """Get available target types"""
        return TARGET_TYPES

    @staticmethod
    def get_common_variables() -> List[Dict]:
        """Get common template variables"""
        return COMMON_VARIABLES

    @staticmethod
    def get_bureau_addresses() -> Dict:
        """Get credit bureau addresses"""
        return BUREAU_ADDRESSES
