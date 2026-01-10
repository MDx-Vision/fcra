"""
LRM Contact Import Service
Migrates contacts from Lead Roster Manager (LRM) CSV to BAG/FCRA platform
"""

import csv
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError

from database import Client, ClientNote, get_db


class LRMImportService:
    """Service for importing contacts from LRM CSV"""

    # Status mapping from LRM to BAG/FCRA
    STATUS_MAP = {
        "C": "active",  # Active Client
        "I": "paused",  # Inactive
        "L": "lead",  # Lead
        "X": "cancelled",  # Cancelled
    }

    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date in multiple formats"""
        if not date_str or date_str.strip() == "":
            return None

        date_str = date_str.strip()

        # Try multiple date formats
        formats = [
            "%m/%d/%Y",  # 12/31/2025
            "%Y-%m-%d",  # 2025-12-31
            "%m-%d-%Y",  # 12-31-2025
            "%Y/%m/%d",  # 2025/12/31
            "%m/%d/%y",  # 12/31/25
            "%d/%m/%Y",  # 31/12/2025
            "%B %d, %Y",  # December 31, 2025
            "%b %d, %Y",  # Dec 31, 2025
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # If no format works, return None
        return None

    @staticmethod
    def clean_phone(phone: Optional[str]) -> Optional[str]:
        """Clean and format phone number"""
        if not phone or phone.strip() == "":
            return None

        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone)

        # Must be 10 digits (US phone)
        if len(digits) == 10:
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == "1":
            # Remove leading 1
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"

        # Return as-is if not standard format
        return phone.strip()

    @staticmethod
    def clean_ssn(ssn: Optional[str]) -> Optional[str]:
        """Clean SSN format"""
        if not ssn or ssn.strip() == "":
            return None

        # Remove all non-digit characters
        digits = re.sub(r"\D", "", ssn)

        # Must be 9 digits
        if len(digits) == 9:
            return f"{digits[0:3]}-{digits[3:5]}-{digits[5:9]}"

        # Return as-is if not standard format
        return ssn.strip()

    @staticmethod
    def import_from_csv(csv_path: str) -> Dict[str, Any]:
        """
        Import contacts from LRM CSV file

        Args:
            csv_path: Path to the CSV file

        Returns:
            Dictionary with import statistics
        """
        db = get_db()

        stats: Dict[str, Any] = {
            "total": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "error_details": [],
        }

        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                # Read CSV with DictReader
                reader = csv.DictReader(f)

                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 (header is row 1)
                    stats["total"] += 1

                    try:
                        # Extract and clean email (required field)
                        email = row.get("email", "").strip().lower()
                        if not email:
                            stats["skipped"] += 1
                            stats["error_details"].append(
                                {
                                    "row": row_num,
                                    "email": "MISSING",
                                    "error": "No email provided",
                                }
                            )
                            continue

                        # Check for duplicate
                        existing = (
                            db.query(Client).filter(Client.email == email).first()
                        )
                        if existing:
                            stats["skipped"] += 1
                            stats["error_details"].append(
                                {
                                    "row": row_num,
                                    "email": email,
                                    "error": "Email already exists",
                                }
                            )
                            continue

                        # Build full name
                        first_name = row.get("first_name", "").strip()
                        last_name = row.get("last_name", "").strip()
                        full_name = f"{first_name} {last_name}".strip()

                        if not full_name:
                            full_name = email.split("@")[
                                0
                            ]  # Use email username as fallback

                        # Get phone (prefer phone field, fallback to mobile)
                        phone = (
                            row.get("phone", "").strip()
                            or row.get("mobile", "").strip()
                        )
                        phone = LRMImportService.clean_phone(phone)

                        # Parse date of birth
                        dob_str = row.get("dob", "").strip()
                        dob = LRMImportService.parse_date(dob_str)

                        # Parse follow-up date
                        follow_up_str = row.get("follow_up", "").strip()
                        follow_up_date = LRMImportService.parse_date(follow_up_str)

                        # Map status
                        lrm_status = row.get("type", "").strip().upper()
                        status = LRMImportService.STATUS_MAP.get(lrm_status, "lead")

                        # Clean SSN
                        ssn = LRMImportService.clean_ssn(row.get("social_security", ""))

                        # Create client record
                        client = Client(
                            name=full_name,
                            email=email,
                            phone=phone,
                            address_line1=row.get("address", "").strip() or None,
                            city=row.get("city", "").strip() or None,
                            state=row.get("state", "").strip() or None,
                            zip_code=row.get("postal_code", "").strip() or None,
                            ssn=ssn,
                            date_of_birth=dob,
                            status=status,
                            referred_by=row.get("affiliate", "").strip() or None,
                            credit_monitoring_service=row.get("cr_provider", "").strip()
                            or None,
                            credit_monitoring_username=row.get(
                                "cr_username", ""
                            ).strip()
                            or None,
                            credit_monitoring_password=row.get(
                                "cr_password", ""
                            ).strip()
                            or None,
                            follow_up_date=follow_up_date,
                            external_id=row.get("contact_id", "").strip() or None,
                            created_at=datetime.utcnow(),
                        )

                        db.add(client)
                        db.flush()  # Get client ID

                        # Create migration note
                        comment = row.get("comment", "").strip()
                        dispute_notes = row.get("dispute_center_notes", "").strip()

                        combined_notes = []
                        if comment:
                            combined_notes.append(f"LRM Comment: {comment}")
                        if dispute_notes:
                            combined_notes.append(f"LRM Dispute Notes: {dispute_notes}")

                        note_content = (
                            f"🔄 Migrated from LRM/CMM on {datetime.utcnow().strftime('%B %d, %Y')}\n"
                            f"Original LRM ID: {row.get('contact_id', 'N/A')}\n"
                            f"Original Status: {lrm_status} ({row.get('status_1', 'N/A')})\n\n"
                        )

                        if combined_notes:
                            note_content += "\n".join(combined_notes)

                        migration_note = ClientNote(
                            client_id=client.id,
                            staff_id=None,  # System-generated
                            note_type="system",
                            content=note_content,
                            created_at=datetime.utcnow(),
                        )

                        db.add(migration_note)
                        db.commit()

                        stats["imported"] += 1

                    except IntegrityError as e:
                        db.rollback()
                        stats["errors"] += 1
                        stats["error_details"].append(
                            {
                                "row": row_num,
                                "email": email if "email" in locals() else "UNKNOWN",
                                "error": f"Database integrity error: {str(e)}",
                            }
                        )

                    except Exception as e:
                        db.rollback()
                        stats["errors"] += 1
                        stats["error_details"].append(
                            {
                                "row": row_num,
                                "email": row.get("email", "UNKNOWN"),
                                "error": str(e),
                            }
                        )

        except FileNotFoundError:
            stats["errors"] += 1
            stats["error_details"].append(
                {"row": 0, "email": "N/A", "error": f"CSV file not found: {csv_path}"}
            )

        except Exception as e:
            stats["errors"] += 1
            stats["error_details"].append(
                {"row": 0, "email": "N/A", "error": f"File reading error: {str(e)}"}
            )

        finally:
            db.close()

        return stats

    @staticmethod
    def validate_csv(csv_path: str) -> Dict[str, Any]:
        """
        Validate CSV format before import

        Returns:
            Dictionary with validation results
        """
        required_fields = ["email"]
        recommended_fields = ["first_name", "last_name", "phone", "type"]

        validation: Dict[str, Any] = {
            "valid": False,
            "row_count": 0,
            "has_required_fields": False,
            "missing_fields": [],
            "available_fields": [],
            "sample_rows": [],
        }

        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                validation["available_fields"] = reader.fieldnames or []

                # Check required fields
                missing = [
                    f
                    for f in required_fields
                    if f not in validation["available_fields"]
                ]
                validation["missing_fields"] = missing
                validation["has_required_fields"] = len(missing) == 0

                # Count rows and get sample
                for i, row in enumerate(reader):
                    validation["row_count"] += 1
                    if i < 3:  # First 3 rows as sample
                        validation["sample_rows"].append(
                            {
                                "email": row.get("email", ""),
                                "name": f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                                "phone": row.get("phone", "") or row.get("mobile", ""),
                                "status": row.get("type", ""),
                            }
                        )

                validation["valid"] = (
                    validation["has_required_fields"] and validation["row_count"] > 0
                )

        except FileNotFoundError:
            validation["error"] = f"CSV file not found: {csv_path}"
        except Exception as e:
            validation["error"] = str(e)

        return validation


def import_lrm_contacts(csv_path: str) -> Dict[str, Any]:
    """
    Convenience function for importing LRM contacts

    Args:
        csv_path: Path to the CSV file

    Returns:
        Import statistics dictionary
    """
    return LRMImportService.import_from_csv(csv_path)


def validate_lrm_csv(csv_path: str) -> Dict[str, Any]:
    """
    Convenience function for validating LRM CSV

    Args:
        csv_path: Path to the CSV file

    Returns:
        Validation results dictionary
    """
    return LRMImportService.validate_csv(csv_path)
