"""
Comprehensive Unit Tests for LRM Import Service

Tests cover:
- LRMImportService.parse_date() - Date parsing in multiple formats
- LRMImportService.clean_phone() - Phone number formatting
- LRMImportService.clean_ssn() - SSN formatting
- LRMImportService.import_from_csv() - Full CSV import workflow
- LRMImportService.validate_csv() - CSV validation
- import_lrm_contacts() - Convenience function
- validate_lrm_csv() - Convenience function
- Edge cases and error handling
"""

import pytest
import csv
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.lrm_import_service import (
    LRMImportService,
    import_lrm_contacts,
    validate_lrm_csv,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock()
    db.query.return_value = db
    db.filter.return_value = db
    db.filter_by.return_value = db
    db.first.return_value = None
    db.all.return_value = []
    db.count.return_value = 0
    db.add.return_value = None
    db.commit.return_value = None
    db.flush.return_value = None
    db.rollback.return_value = None
    db.close.return_value = None
    db.refresh.return_value = None
    return db


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file and return its path."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_csv_data():
    """Return sample CSV data for testing."""
    return [
        {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "555-123-4567",
            "mobile": "",
            "type": "C",
            "status_1": "Active Client",
            "dob": "01/15/1985",
            "follow_up": "12/31/2025",
            "social_security": "123-45-6789",
            "address": "123 Main St",
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "90001",
            "affiliate": "Partner ABC",
            "cr_provider": "IdentityIQ",
            "cr_username": "johnd",
            "cr_password": "secret123",
            "contact_id": "LRM-001",
            "comment": "Good candidate",
            "dispute_center_notes": "Round 1 completed",
        }
    ]


def write_csv_file(path, data):
    """Write CSV data to a file."""
    if not data:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            f.write('')
        return

    fieldnames = data[0].keys()
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


# =============================================================================
# Test Class: parse_date() Method
# =============================================================================


class TestParseDate:
    """Tests for date parsing."""

    def test_parse_date_mm_dd_yyyy(self):
        """Test parsing MM/DD/YYYY format."""
        result = LRMImportService.parse_date("12/31/2025")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    def test_parse_date_yyyy_mm_dd(self):
        """Test parsing YYYY-MM-DD format."""
        result = LRMImportService.parse_date("2025-12-31")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    def test_parse_date_mm_dd_yyyy_dashes(self):
        """Test parsing MM-DD-YYYY format."""
        result = LRMImportService.parse_date("12-31-2025")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    def test_parse_date_yyyy_mm_dd_slashes(self):
        """Test parsing YYYY/MM/DD format."""
        result = LRMImportService.parse_date("2025/12/31")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    def test_parse_date_mm_dd_yy(self):
        """Test parsing MM/DD/YY format."""
        result = LRMImportService.parse_date("12/31/25")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    def test_parse_date_dd_mm_yyyy(self):
        """Test parsing DD/MM/YYYY format."""
        result = LRMImportService.parse_date("31/12/2025")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    def test_parse_date_full_month_name(self):
        """Test parsing 'December 31, 2025' format."""
        result = LRMImportService.parse_date("December 31, 2025")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    def test_parse_date_abbreviated_month(self):
        """Test parsing 'Dec 31, 2025' format."""
        result = LRMImportService.parse_date("Dec 31, 2025")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    def test_parse_date_none_input(self):
        """Test parsing None returns None."""
        result = LRMImportService.parse_date(None)
        assert result is None

    def test_parse_date_empty_string(self):
        """Test parsing empty string returns None."""
        result = LRMImportService.parse_date("")
        assert result is None

    def test_parse_date_whitespace_only(self):
        """Test parsing whitespace-only string returns None."""
        result = LRMImportService.parse_date("   ")
        assert result is None

    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format returns None."""
        result = LRMImportService.parse_date("not-a-date")
        assert result is None

    def test_parse_date_partial_date(self):
        """Test parsing partial date returns None."""
        result = LRMImportService.parse_date("12/2025")
        assert result is None

    def test_parse_date_strips_whitespace(self):
        """Test parsing strips leading/trailing whitespace."""
        result = LRMImportService.parse_date("  12/31/2025  ")
        assert result is not None
        assert result.year == 2025


# =============================================================================
# Test Class: clean_phone() Method
# =============================================================================


class TestCleanPhone:
    """Tests for phone number cleaning."""

    def test_clean_phone_with_dashes(self):
        """Test cleaning phone with dashes."""
        result = LRMImportService.clean_phone("555-123-4567")
        assert result == "(555) 123-4567"

    def test_clean_phone_with_parentheses(self):
        """Test cleaning phone with parentheses."""
        result = LRMImportService.clean_phone("(555) 123-4567")
        assert result == "(555) 123-4567"

    def test_clean_phone_plain_digits(self):
        """Test cleaning plain 10-digit phone."""
        result = LRMImportService.clean_phone("5551234567")
        assert result == "(555) 123-4567"

    def test_clean_phone_with_spaces(self):
        """Test cleaning phone with spaces."""
        result = LRMImportService.clean_phone("555 123 4567")
        assert result == "(555) 123-4567"

    def test_clean_phone_with_dots(self):
        """Test cleaning phone with dots."""
        result = LRMImportService.clean_phone("555.123.4567")
        assert result == "(555) 123-4567"

    def test_clean_phone_11_digits_with_leading_1(self):
        """Test cleaning 11-digit phone with leading 1."""
        result = LRMImportService.clean_phone("15551234567")
        assert result == "(555) 123-4567"

    def test_clean_phone_11_digits_with_plus_1(self):
        """Test cleaning phone with +1 prefix."""
        result = LRMImportService.clean_phone("+1 555-123-4567")
        assert result == "(555) 123-4567"

    def test_clean_phone_none_input(self):
        """Test cleaning None returns None."""
        result = LRMImportService.clean_phone(None)
        assert result is None

    def test_clean_phone_empty_string(self):
        """Test cleaning empty string returns None."""
        result = LRMImportService.clean_phone("")
        assert result is None

    def test_clean_phone_whitespace_only(self):
        """Test cleaning whitespace-only string returns None."""
        result = LRMImportService.clean_phone("   ")
        assert result is None

    def test_clean_phone_too_short(self):
        """Test cleaning phone with too few digits returns as-is."""
        result = LRMImportService.clean_phone("555-1234")
        assert result == "555-1234"

    def test_clean_phone_too_long(self):
        """Test cleaning phone with too many digits returns as-is."""
        result = LRMImportService.clean_phone("55512345678901")
        assert result == "55512345678901"

    def test_clean_phone_international_format_non_us(self):
        """Test cleaning international non-US phone returns as-is."""
        result = LRMImportService.clean_phone("+44 20 7946 0958")
        assert result == "+44 20 7946 0958"


# =============================================================================
# Test Class: clean_ssn() Method
# =============================================================================


class TestCleanSsn:
    """Tests for SSN cleaning."""

    def test_clean_ssn_with_dashes(self):
        """Test cleaning SSN with dashes."""
        result = LRMImportService.clean_ssn("123-45-6789")
        assert result == "123-45-6789"

    def test_clean_ssn_plain_digits(self):
        """Test cleaning plain 9-digit SSN."""
        result = LRMImportService.clean_ssn("123456789")
        assert result == "123-45-6789"

    def test_clean_ssn_with_spaces(self):
        """Test cleaning SSN with spaces."""
        result = LRMImportService.clean_ssn("123 45 6789")
        assert result == "123-45-6789"

    def test_clean_ssn_none_input(self):
        """Test cleaning None returns None."""
        result = LRMImportService.clean_ssn(None)
        assert result is None

    def test_clean_ssn_empty_string(self):
        """Test cleaning empty string returns None."""
        result = LRMImportService.clean_ssn("")
        assert result is None

    def test_clean_ssn_whitespace_only(self):
        """Test cleaning whitespace-only string returns None."""
        result = LRMImportService.clean_ssn("   ")
        assert result is None

    def test_clean_ssn_too_short(self):
        """Test cleaning SSN with too few digits returns as-is."""
        result = LRMImportService.clean_ssn("12345678")
        assert result == "12345678"

    def test_clean_ssn_too_long(self):
        """Test cleaning SSN with too many digits returns as-is."""
        result = LRMImportService.clean_ssn("1234567890")
        assert result == "1234567890"

    def test_clean_ssn_with_letters(self):
        """Test cleaning SSN with letters returns as-is after stripping."""
        result = LRMImportService.clean_ssn("123-45-XXXX")
        assert result == "123-45-XXXX"


# =============================================================================
# Test Class: STATUS_MAP
# =============================================================================


class TestStatusMap:
    """Tests for status mapping."""

    def test_status_map_active(self):
        """Test status C maps to active."""
        assert LRMImportService.STATUS_MAP["C"] == "active"

    def test_status_map_paused(self):
        """Test status I maps to paused."""
        assert LRMImportService.STATUS_MAP["I"] == "paused"

    def test_status_map_lead(self):
        """Test status L maps to lead."""
        assert LRMImportService.STATUS_MAP["L"] == "lead"

    def test_status_map_cancelled(self):
        """Test status X maps to cancelled."""
        assert LRMImportService.STATUS_MAP["X"] == "cancelled"


# =============================================================================
# Test Class: validate_csv() Method
# =============================================================================


class TestValidateCsv:
    """Tests for CSV validation."""

    def test_validate_csv_valid_file(self, temp_csv_file, sample_csv_data):
        """Test validating a valid CSV file."""
        write_csv_file(temp_csv_file, sample_csv_data)

        result = LRMImportService.validate_csv(temp_csv_file)

        assert result["valid"] is True
        assert result["row_count"] == 1
        assert result["has_required_fields"] is True
        assert "email" in result["available_fields"]
        assert len(result["missing_fields"]) == 0

    def test_validate_csv_missing_email_field(self, temp_csv_file):
        """Test validating CSV missing required email field."""
        data = [{"first_name": "John", "last_name": "Doe"}]
        write_csv_file(temp_csv_file, data)

        result = LRMImportService.validate_csv(temp_csv_file)

        assert result["valid"] is False
        assert result["has_required_fields"] is False
        assert "email" in result["missing_fields"]

    def test_validate_csv_empty_file(self, temp_csv_file):
        """Test validating empty CSV file."""
        with open(temp_csv_file, 'w', encoding='utf-8') as f:
            f.write("email,first_name,last_name\n")

        result = LRMImportService.validate_csv(temp_csv_file)

        assert result["valid"] is False
        assert result["row_count"] == 0

    def test_validate_csv_file_not_found(self):
        """Test validating non-existent file."""
        result = LRMImportService.validate_csv("/nonexistent/path/file.csv")

        assert result["valid"] is False
        assert "error" in result
        assert "not found" in result["error"]

    def test_validate_csv_sample_rows(self, temp_csv_file):
        """Test validation returns sample rows."""
        data = [
            {"email": "test1@example.com", "first_name": "Test", "last_name": "One", "phone": "555-111-1111", "type": "L"},
            {"email": "test2@example.com", "first_name": "Test", "last_name": "Two", "phone": "555-222-2222", "type": "C"},
            {"email": "test3@example.com", "first_name": "Test", "last_name": "Three", "phone": "555-333-3333", "type": "I"},
            {"email": "test4@example.com", "first_name": "Test", "last_name": "Four", "phone": "555-444-4444", "type": "X"},
        ]
        write_csv_file(temp_csv_file, data)

        result = LRMImportService.validate_csv(temp_csv_file)

        assert result["valid"] is True
        assert result["row_count"] == 4
        assert len(result["sample_rows"]) == 3  # First 3 rows

    def test_validate_csv_available_fields(self, temp_csv_file, sample_csv_data):
        """Test validation returns available fields."""
        write_csv_file(temp_csv_file, sample_csv_data)

        result = LRMImportService.validate_csv(temp_csv_file)

        assert "email" in result["available_fields"]
        assert "first_name" in result["available_fields"]
        assert "last_name" in result["available_fields"]
        assert "phone" in result["available_fields"]

    def test_validate_csv_with_mobile_fallback(self, temp_csv_file):
        """Test validation uses mobile as phone fallback."""
        data = [{"email": "test@example.com", "mobile": "555-123-4567"}]
        write_csv_file(temp_csv_file, data)

        result = LRMImportService.validate_csv(temp_csv_file)

        assert result["valid"] is True
        assert result["sample_rows"][0]["phone"] == "555-123-4567"


# =============================================================================
# Test Class: import_from_csv() Method
# =============================================================================


class TestImportFromCsv:
    """Tests for CSV import functionality."""

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_from_csv_success(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, sample_csv_data, mock_db):
        """Test successful CSV import."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        write_csv_file(temp_csv_file, sample_csv_data)

        # Mock client ID assignment
        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["total"] == 1
        assert result["imported"] == 1
        assert result["skipped"] == 0
        assert result["errors"] == 0
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        mock_db.close.assert_called()

    @patch('services.lrm_import_service.get_db')
    def test_import_from_csv_file_not_found(self, mock_get_db, mock_db):
        """Test import with non-existent file."""
        mock_get_db.return_value = mock_db

        result = LRMImportService.import_from_csv("/nonexistent/path/file.csv")

        assert result["errors"] == 1
        assert "CSV file not found" in result["error_details"][0]["error"]
        mock_db.close.assert_called()

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_from_csv_missing_email(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, mock_db):
        """Test import skips rows without email."""
        mock_get_db.return_value = mock_db
        data = [
            {"email": "", "first_name": "No", "last_name": "Email"},
            {"email": "valid@example.com", "first_name": "Valid", "last_name": "User"},
        ]
        write_csv_file(temp_csv_file, data)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["total"] == 2
        assert result["skipped"] == 1
        assert result["imported"] == 1
        assert any("No email provided" in d["error"] for d in result["error_details"])

    @patch('services.lrm_import_service.get_db')
    def test_import_from_csv_duplicate_email(self, mock_get_db, temp_csv_file, mock_db):
        """Test import skips duplicate emails."""
        mock_get_db.return_value = mock_db
        data = [{"email": "duplicate@example.com", "first_name": "Dupe", "last_name": "User"}]
        write_csv_file(temp_csv_file, data)

        # Return existing client for duplicate check
        existing_client = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_client

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["total"] == 1
        assert result["skipped"] == 1
        assert any("Email already exists" in d["error"] for d in result["error_details"])

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_status_mapping(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import correctly maps LRM status."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{"email": "test@example.com", "first_name": "Test", "last_name": "User", "type": "C"}]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        # Check that Client was called with status="active" for type "C"
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["status"] == "active"

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_status_default(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import uses 'lead' as default status."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{"email": "test@example.com", "first_name": "Test", "last_name": "User", "type": ""}]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["status"] == "lead"

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_phone_cleaned(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import cleans phone number."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{"email": "test@example.com", "phone": "5551234567"}]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["phone"] == "(555) 123-4567"

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_mobile_fallback(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import uses mobile as phone fallback."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{"email": "test@example.com", "phone": "", "mobile": "5551234567"}]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["phone"] == "(555) 123-4567"

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_ssn_cleaned(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import cleans SSN."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{"email": "test@example.com", "social_security": "123456789"}]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["ssn"] == "123-45-6789"

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_date_parsing(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import parses dates correctly."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{"email": "test@example.com", "dob": "01/15/1985", "follow_up": "12/31/2025"}]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["date_of_birth"].year == 1985
        assert call_kwargs["follow_up_date"].year == 2025

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_email_lowercase(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import lowercases email."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{"email": "TEST@EXAMPLE.COM", "first_name": "Test"}]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["email"] == "test@example.com"

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_name_fallback(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import uses email username as name fallback."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{"email": "johndoe@example.com", "first_name": "", "last_name": ""}]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["name"] == "johndoe"

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_creates_note(self, mock_client_class, mock_note_class, mock_get_db, temp_csv_file, mock_db):
        """Test import creates migration note."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        data = [{
            "email": "test@example.com",
            "contact_id": "LRM-001",
            "type": "C",
            "status_1": "Active Client",
            "comment": "Test comment",
            "dispute_center_notes": "Dispute notes",
        }]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        # Verify ClientNote was created
        mock_note_class.assert_called()
        note_kwargs = mock_note_class.call_args[1]
        assert note_kwargs["client_id"] == 1
        assert note_kwargs["note_type"] == "system"
        assert "Migrated from LRM/CMM" in note_kwargs["content"]
        assert "Test comment" in note_kwargs["content"]
        assert "Dispute notes" in note_kwargs["content"]

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_from_csv_integrity_error(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, mock_db):
        """Test import handles IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.side_effect = IntegrityError("", "", "")

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        data = [{"email": "test@example.com", "first_name": "Test"}]
        write_csv_file(temp_csv_file, data)

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["errors"] == 1
        assert any("Database integrity error" in d["error"] for d in result["error_details"])
        mock_db.rollback.assert_called()

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_from_csv_general_exception(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, mock_db):
        """Test import handles general exceptions."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add.side_effect = Exception("Unexpected error")

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        data = [{"email": "test@example.com", "first_name": "Test"}]
        write_csv_file(temp_csv_file, data)

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["errors"] == 1
        assert any("Unexpected error" in d["error"] for d in result["error_details"])
        mock_db.rollback.assert_called()

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_from_csv_multiple_rows(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, mock_db):
        """Test import handles multiple rows."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        data = [
            {"email": "user1@example.com", "first_name": "User", "last_name": "One"},
            {"email": "user2@example.com", "first_name": "User", "last_name": "Two"},
            {"email": "user3@example.com", "first_name": "User", "last_name": "Three"},
        ]
        write_csv_file(temp_csv_file, data)

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["total"] == 3
        assert result["imported"] == 3
        assert result["skipped"] == 0
        assert result["errors"] == 0

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_all_address_fields(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import includes all address fields."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{
            "email": "test@example.com",
            "address": "123 Main St",
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "90001",
        }]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["address_line1"] == "123 Main St"
        assert call_kwargs["city"] == "Los Angeles"
        assert call_kwargs["state"] == "CA"
        assert call_kwargs["zip_code"] == "90001"

    @patch('services.lrm_import_service.get_db')
    @patch('services.lrm_import_service.Client')
    def test_import_from_csv_credit_monitoring_fields(self, mock_client_class, mock_get_db, temp_csv_file, mock_db):
        """Test import includes credit monitoring fields."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = [{
            "email": "test@example.com",
            "cr_provider": "IdentityIQ",
            "cr_username": "testuser",
            "cr_password": "testpass",
        }]
        write_csv_file(temp_csv_file, data)

        LRMImportService.import_from_csv(temp_csv_file)

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["credit_monitoring_service"] == "IdentityIQ"
        assert call_kwargs["credit_monitoring_username"] == "testuser"
        assert call_kwargs["credit_monitoring_password"] == "testpass"


# =============================================================================
# Test Class: Convenience Functions
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @patch.object(LRMImportService, 'import_from_csv')
    def test_import_lrm_contacts(self, mock_import):
        """Test import_lrm_contacts calls LRMImportService.import_from_csv."""
        mock_import.return_value = {"imported": 5}

        result = import_lrm_contacts("/path/to/file.csv")

        mock_import.assert_called_once_with("/path/to/file.csv")
        assert result["imported"] == 5

    @patch.object(LRMImportService, 'validate_csv')
    def test_validate_lrm_csv(self, mock_validate):
        """Test validate_lrm_csv calls LRMImportService.validate_csv."""
        mock_validate.return_value = {"valid": True}

        result = validate_lrm_csv("/path/to/file.csv")

        mock_validate.assert_called_once_with("/path/to/file.csv")
        assert result["valid"] is True


# =============================================================================
# Test Class: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_date_boundary_dates(self):
        """Test parsing boundary dates."""
        # First day of year
        result = LRMImportService.parse_date("01/01/2000")
        assert result.month == 1
        assert result.day == 1

        # Last day of year
        result = LRMImportService.parse_date("12/31/2099")
        assert result.month == 12
        assert result.day == 31

    def test_clean_phone_various_formats(self):
        """Test phone cleaning with various formats."""
        test_cases = [
            ("1-555-123-4567", "(555) 123-4567"),
            ("+1 (555) 123-4567", "(555) 123-4567"),
            ("555.123.4567", "(555) 123-4567"),
            ("  555-123-4567  ", "(555) 123-4567"),
        ]
        for input_phone, expected in test_cases:
            result = LRMImportService.clean_phone(input_phone)
            assert result == expected, f"Failed for input: {input_phone}"

    def test_clean_ssn_various_formats(self):
        """Test SSN cleaning with various formats."""
        test_cases = [
            ("123 45 6789", "123-45-6789"),
            ("123.45.6789", "123-45-6789"),
            ("123/45/6789", "123-45-6789"),
        ]
        for input_ssn, expected in test_cases:
            result = LRMImportService.clean_ssn(input_ssn)
            assert result == expected, f"Failed for input: {input_ssn}"

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_csv_encoding_utf8_sig(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, mock_db):
        """Test import handles UTF-8 with BOM encoding."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        # Write CSV with UTF-8 BOM
        with open(temp_csv_file, 'w', encoding='utf-8-sig') as f:
            f.write("email,first_name,last_name\n")
            f.write("test@example.com,Test,User\n")

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["total"] == 1
        assert result["imported"] == 1

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_csv_with_unicode_characters(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, mock_db):
        """Test import handles Unicode characters."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        data = [{"email": "test@example.com", "first_name": "Jos\u00e9", "last_name": "Garc\u00eda"}]
        write_csv_file(temp_csv_file, data)

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["total"] == 1
        assert result["imported"] == 1

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_csv_empty_optional_fields(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, mock_db):
        """Test import handles empty optional fields."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        # Minimal CSV with only required email field
        with open(temp_csv_file, 'w', encoding='utf-8') as f:
            f.write("email\n")
            f.write("minimal@example.com\n")

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["total"] == 1
        assert result["imported"] == 1

    def test_status_map_case_sensitivity(self):
        """Test that STATUS_MAP is case-sensitive."""
        # Lowercase keys should not exist
        assert "c" not in LRMImportService.STATUS_MAP
        assert "i" not in LRMImportService.STATUS_MAP
        assert "l" not in LRMImportService.STATUS_MAP
        assert "x" not in LRMImportService.STATUS_MAP

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_csv_handles_missing_columns(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, mock_db):
        """Test import handles CSV with missing columns gracefully."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        # CSV with only some columns
        data = [{"email": "test@example.com", "first_name": "Test"}]
        write_csv_file(temp_csv_file, data)

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["total"] == 1
        assert result["imported"] == 1

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_import_csv_statistics_accuracy(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, mock_db):
        """Test import statistics are accurately calculated."""
        mock_get_db.return_value = mock_db

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        # Setup: 1 valid, 1 missing email, 1 duplicate
        # Row with missing email skips database check, so only 2 calls to first()
        existing_client = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # First row - no duplicate (imported)
            existing_client,  # Third row - duplicate (skipped)
        ]

        data = [
            {"email": "valid@example.com", "first_name": "Valid"},
            {"email": "", "first_name": "No Email"},
            {"email": "duplicate@example.com", "first_name": "Duplicate"},
        ]
        write_csv_file(temp_csv_file, data)

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["total"] == 3
        assert result["imported"] == 1
        assert result["skipped"] == 2
        assert len(result["error_details"]) == 2

    @patch('services.lrm_import_service.get_db')
    def test_import_csv_file_read_error(self, mock_get_db, temp_csv_file, mock_db):
        """Test import handles file read errors."""
        mock_get_db.return_value = mock_db

        # Create file then make it unreadable (by deleting)
        os.remove(temp_csv_file)

        result = LRMImportService.import_from_csv(temp_csv_file)

        assert result["errors"] == 1
        assert "not found" in result["error_details"][0]["error"]


# =============================================================================
# Test Class: Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    @patch('services.lrm_import_service.ClientNote')
    @patch('services.lrm_import_service.Client')
    @patch('services.lrm_import_service.get_db')
    def test_validate_then_import_workflow(self, mock_get_db, mock_client_class, mock_note_class, temp_csv_file, sample_csv_data, mock_db):
        """Test validating CSV then importing."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_client = Mock()
        mock_client.id = 1
        mock_client_class.return_value = mock_client

        write_csv_file(temp_csv_file, sample_csv_data)

        # Step 1: Validate
        validation = LRMImportService.validate_csv(temp_csv_file)
        assert validation["valid"] is True

        # Step 2: Import
        result = LRMImportService.import_from_csv(temp_csv_file)
        assert result["imported"] == 1

    def test_validate_csv_returns_consistent_structure(self, temp_csv_file, sample_csv_data):
        """Test validate_csv always returns consistent structure."""
        write_csv_file(temp_csv_file, sample_csv_data)

        result = LRMImportService.validate_csv(temp_csv_file)

        # Check all expected keys exist
        expected_keys = ["valid", "row_count", "has_required_fields",
                        "missing_fields", "available_fields", "sample_rows"]
        for key in expected_keys:
            assert key in result

    @patch('services.lrm_import_service.get_db')
    def test_import_returns_consistent_structure(self, mock_get_db, temp_csv_file, sample_csv_data, mock_db):
        """Test import_from_csv always returns consistent structure."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        write_csv_file(temp_csv_file, sample_csv_data)

        result = LRMImportService.import_from_csv(temp_csv_file)

        # Check all expected keys exist
        expected_keys = ["total", "imported", "skipped", "errors", "error_details"]
        for key in expected_keys:
            assert key in result

        # Check types
        assert isinstance(result["total"], int)
        assert isinstance(result["imported"], int)
        assert isinstance(result["skipped"], int)
        assert isinstance(result["errors"], int)
        assert isinstance(result["error_details"], list)
