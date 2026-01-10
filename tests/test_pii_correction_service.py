"""
Unit tests for PII Correction Service
Tests for generating PII correction letters for the Big 3 CRAs.
"""

import os
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from services.pii_correction_service import (
    CRA_ADDRESSES,
    PII_TYPES,
    PIICorrectionPDF,
    get_client_pii,
    generate_pii_correction_letter,
    generate_pii_correction_letters,
    generate_pii_correction_for_bureau,
    get_pii_discrepancies_from_report,
    generate_pii_only_dispute,
)


class TestCRAAddresses:
    """Tests for CRA address constants."""

    def test_cra_addresses_has_three_bureaus(self):
        """Test that CRA_ADDRESSES contains exactly 3 bureaus."""
        assert len(CRA_ADDRESSES) == 3

    def test_cra_addresses_has_equifax(self):
        """Test that Equifax is in CRA_ADDRESSES."""
        assert "Equifax" in CRA_ADDRESSES

    def test_cra_addresses_has_experian(self):
        """Test that Experian is in CRA_ADDRESSES."""
        assert "Experian" in CRA_ADDRESSES

    def test_cra_addresses_has_transunion(self):
        """Test that TransUnion is in CRA_ADDRESSES."""
        assert "TransUnion" in CRA_ADDRESSES

    def test_each_bureau_has_required_fields(self):
        """Test that each bureau has all required fields."""
        required_fields = ["name", "dispute_address", "city", "state", "zip", "phone"]
        for bureau_name, bureau_info in CRA_ADDRESSES.items():
            for field in required_fields:
                assert field in bureau_info, f"{bureau_name} missing field: {field}"

    def test_equifax_address_is_correct(self):
        """Test Equifax dispute address."""
        equifax = CRA_ADDRESSES["Equifax"]
        assert equifax["dispute_address"] == "P.O. Box 740256"
        assert equifax["city"] == "Atlanta"
        assert equifax["state"] == "GA"

    def test_experian_address_is_correct(self):
        """Test Experian dispute address."""
        experian = CRA_ADDRESSES["Experian"]
        assert experian["dispute_address"] == "P.O. Box 4500"
        assert experian["city"] == "Allen"
        assert experian["state"] == "TX"

    def test_transunion_address_is_correct(self):
        """Test TransUnion dispute address."""
        transunion = CRA_ADDRESSES["TransUnion"]
        assert transunion["dispute_address"] == "P.O. Box 2000"
        assert transunion["city"] == "Chester"
        assert transunion["state"] == "PA"


class TestPIITypes:
    """Tests for PII type constants."""

    def test_pii_types_list_exists(self):
        """Test that PII_TYPES list exists."""
        assert PII_TYPES is not None

    def test_pii_types_has_name(self):
        """Test that 'name' is in PII_TYPES."""
        assert "name" in PII_TYPES

    def test_pii_types_has_address(self):
        """Test that 'address' is in PII_TYPES."""
        assert "address" in PII_TYPES

    def test_pii_types_has_ssn(self):
        """Test that 'ssn' is in PII_TYPES."""
        assert "ssn" in PII_TYPES

    def test_pii_types_has_dob(self):
        """Test that 'dob' is in PII_TYPES."""
        assert "dob" in PII_TYPES

    def test_pii_types_has_phone(self):
        """Test that 'phone' is in PII_TYPES."""
        assert "phone" in PII_TYPES

    def test_pii_types_has_employer(self):
        """Test that 'employer' is in PII_TYPES."""
        assert "employer" in PII_TYPES


class TestPIICorrectionPDF:
    """Tests for PIICorrectionPDF class."""

    def test_pdf_instance_creation(self):
        """Test that PDF instance can be created."""
        pdf = PIICorrectionPDF()
        assert pdf is not None

    def test_pdf_has_auto_page_break(self):
        """Test that PDF has auto page break enabled."""
        pdf = PIICorrectionPDF()
        assert pdf.auto_page_break is True


class TestGetClientPII:
    """Tests for get_client_pii function."""

    def test_get_pii_from_dict(self):
        """Test extracting PII from a dictionary."""
        client_dict = {
            "first_name": "John",
            "last_name": "Doe",
            "address_street": "123 Main St",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "90210",
            "ssn_last_four": "1234",
            "email": "john@example.com",
            "phone": "555-123-4567",
        }
        pii = get_client_pii(client_dict)

        assert pii["name"] == "John Doe"
        assert pii["first_name"] == "John"
        assert pii["last_name"] == "Doe"
        assert pii["ssn_last_four"] == "1234"

    def test_get_pii_with_name_field(self):
        """Test extracting PII when name field is provided."""
        client_dict = {
            "name": "Jane Smith",
            "first_name": "Jane",
            "last_name": "Smith",
        }
        pii = get_client_pii(client_dict)
        assert pii["name"] == "Jane Smith"

    def test_get_pii_defaults_for_missing_fields(self):
        """Test that defaults are used for missing fields."""
        client_dict = {}
        pii = get_client_pii(client_dict)

        assert pii["name"] == ""
        assert pii["ssn_last_four"] == "XXXX"
        assert pii["email"] == ""

    def test_get_pii_from_mock_client_object(self):
        """Test extracting PII from a client-like object."""
        client = MagicMock()
        client.name = "Bob Johnson"
        client.first_name = "Bob"
        client.last_name = "Johnson"
        client.address_street = "456 Oak Ave"
        client.address_city = "Somewhere"
        client.address_state = "TX"
        client.address_zip = "75001"
        client.ssn_last_four = "5678"
        client.date_of_birth = datetime(1990, 5, 15)
        client.email = "bob@example.com"
        client.phone = "555-987-6543"

        pii = get_client_pii(client)

        assert pii["name"] == "Bob Johnson"
        assert pii["ssn_last_four"] == "5678"
        assert pii["date_of_birth"] == datetime(1990, 5, 15)


class TestGeneratePIICorrectionLetter:
    """Tests for generate_pii_correction_letter function."""

    def test_generate_letter_for_equifax(self):
        """Test generating a letter for Equifax."""
        client = {
            "name": "Test User",
            "address_street": "123 Test St",
            "address_city": "Testville",
            "address_state": "CA",
            "address_zip": "90210",
            "ssn_last_four": "1234",
        }
        incorrect_pii = {
            "names": ["WRONG NAME", "BAD NAME"],
            "addresses": ["OLD ADDRESS"],
        }

        letter = generate_pii_correction_letter(client, "Equifax", incorrect_pii)

        assert letter["bureau_name"] == "Equifax Information Services LLC"
        assert letter["client_name"] == "Test User"
        assert "names" in letter["incorrect_pii"]
        assert len(letter["incorrect_pii"]["names"]) == 2

    def test_generate_letter_for_experian(self):
        """Test generating a letter for Experian."""
        client = {"name": "Test User", "ssn_last_four": "1234"}
        incorrect_pii = {"names": ["WRONG"]}

        letter = generate_pii_correction_letter(client, "Experian", incorrect_pii)

        assert letter["bureau_name"] == "Experian"
        assert "Allen" in letter["bureau_address"]

    def test_generate_letter_for_transunion(self):
        """Test generating a letter for TransUnion."""
        client = {"name": "Test User", "ssn_last_four": "1234"}
        incorrect_pii = {"names": ["WRONG"]}

        letter = generate_pii_correction_letter(client, "TransUnion", incorrect_pii)

        assert letter["bureau_name"] == "TransUnion LLC"
        assert "Chester" in letter["bureau_address"]

    def test_invalid_bureau_raises_error(self):
        """Test that invalid bureau name raises ValueError."""
        client = {"name": "Test User"}
        incorrect_pii = {"names": ["WRONG"]}

        with pytest.raises(ValueError) as exc_info:
            generate_pii_correction_letter(client, "InvalidBureau", incorrect_pii)

        assert "Unknown bureau" in str(exc_info.value)

    def test_letter_includes_case_number(self):
        """Test that letter includes case number."""
        client = {"name": "Test User", "ssn_last_four": "1234"}
        incorrect_pii = {"names": ["WRONG"]}

        letter = generate_pii_correction_letter(
            client, "Equifax", incorrect_pii, case_number="PII-TEST-123"
        )

        assert letter["case_number"] == "PII-TEST-123"

    def test_letter_auto_generates_case_number(self):
        """Test that case number is auto-generated if not provided."""
        client = {"name": "Test User", "ssn_last_four": "1234"}
        incorrect_pii = {"names": ["WRONG"]}

        letter = generate_pii_correction_letter(client, "Equifax", incorrect_pii)

        assert letter["case_number"] is not None
        assert "PII-" in letter["case_number"]
        assert "1234" in letter["case_number"]

    def test_letter_uses_provided_correct_pii(self):
        """Test that provided correct PII is used."""
        client = {"name": "Test User", "ssn_last_four": "1234"}
        incorrect_pii = {"names": ["WRONG"]}
        correct_pii = {
            "name": "Correct Name",
            "phone": "555-111-2222",
        }

        letter = generate_pii_correction_letter(
            client, "Equifax", incorrect_pii, correct_pii=correct_pii
        )

        assert letter["correct_pii"]["name"] == "Correct Name"
        assert letter["correct_pii"]["phone"] == "555-111-2222"

    def test_letter_defaults_correct_pii_from_client(self):
        """Test that correct PII defaults to client data."""
        client = {
            "name": "Test User",
            "ssn_last_four": "1234",
            "phone": "555-333-4444",
        }
        incorrect_pii = {"names": ["WRONG"]}

        letter = generate_pii_correction_letter(client, "Equifax", incorrect_pii)

        assert letter["correct_pii"]["name"] == "Test User"
        assert letter["correct_pii"]["ssn"] == "XXX-XX-1234"


class TestGeneratePIICorrectionLetters:
    """Tests for generate_pii_correction_letters function."""

    @patch("services.pii_correction_service.get_db")
    def test_client_not_found_returns_error(self, mock_get_db):
        """Test that missing client returns error."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        result = generate_pii_correction_letters(
            client_id=999,
            incorrect_pii={"names": ["WRONG"]},
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("services.pii_correction_service.get_db")
    @patch("services.pii_correction_service.PIICorrectionPDF")
    @patch("services.pii_correction_service.Document")
    @patch("os.makedirs")
    def test_successful_generation(self, mock_makedirs, mock_doc, mock_pdf, mock_get_db):
        """Test successful letter generation."""
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = "Test User"
        mock_client.first_name = "Test"
        mock_client.last_name = "User"
        mock_client.address_street = "123 Test St"
        mock_client.address_city = "Testville"
        mock_client.address_state = "CA"
        mock_client.address_zip = "90210"
        mock_client.ssn_last_four = "1234"
        mock_client.date_of_birth = None
        mock_client.email = "test@example.com"
        mock_client.phone = "555-123-4567"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        # Mock PDF and Document
        mock_pdf_instance = MagicMock()
        mock_pdf.return_value = mock_pdf_instance
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance

        result = generate_pii_correction_letters(
            client_id=1,
            incorrect_pii={"names": ["WRONG NAME"]},
        )

        assert result["success"] is True
        assert result["total_letters"] == 3
        assert "Equifax" in result["bureaus_included"]
        assert "Experian" in result["bureaus_included"]
        assert "TransUnion" in result["bureaus_included"]

    @patch("services.pii_correction_service.get_db")
    @patch("services.pii_correction_service.PIICorrectionPDF")
    @patch("services.pii_correction_service.Document")
    @patch("os.makedirs")
    def test_specific_bureaus_only(self, mock_makedirs, mock_doc, mock_pdf, mock_get_db):
        """Test generating letters for specific bureaus only."""
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = "Test User"
        mock_client.first_name = "Test"
        mock_client.last_name = "User"
        mock_client.address_street = "123 Test St"
        mock_client.address_city = "Testville"
        mock_client.address_state = "CA"
        mock_client.address_zip = "90210"
        mock_client.ssn_last_four = "1234"
        mock_client.date_of_birth = None
        mock_client.email = "test@example.com"
        mock_client.phone = "555-123-4567"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        # Mock PDF and Document
        mock_pdf_instance = MagicMock()
        mock_pdf.return_value = mock_pdf_instance
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance

        result = generate_pii_correction_letters(
            client_id=1,
            incorrect_pii={"names": ["WRONG"]},
            bureaus=["Equifax"],
        )

        assert result["success"] is True
        assert result["total_letters"] == 1
        assert result["bureaus_included"] == ["Equifax"]

    @patch("services.pii_correction_service.get_db")
    def test_invalid_bureaus_returns_error(self, mock_get_db):
        """Test that invalid bureaus return error."""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_get_db.return_value = mock_db

        result = generate_pii_correction_letters(
            client_id=1,
            incorrect_pii={"names": ["WRONG"]},
            bureaus=["InvalidBureau"],
        )

        assert result["success"] is False
        assert "No valid bureaus" in result["error"]


class TestGeneratePIICorrectionForBureau:
    """Tests for generate_pii_correction_for_bureau function."""

    @patch("services.pii_correction_service.generate_pii_correction_letters")
    def test_calls_generate_with_single_bureau(self, mock_generate):
        """Test that function calls generate with single bureau."""
        mock_generate.return_value = {"success": True}

        result = generate_pii_correction_for_bureau(
            client_id=1,
            bureau_name="Equifax",
            incorrect_pii={"names": ["WRONG"]},
        )

        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        assert call_args.kwargs["bureaus"] == ["Equifax"]


class TestGetPIIDiscrepanciesFromReport:
    """Tests for get_pii_discrepancies_from_report function."""

    def test_extracts_name_variations(self):
        """Test extracting name variations from report."""
        report = {
            "personal_info": {
                "names": ["JOHN DOE", "J DOE", "JOHNNY DOE"],
            }
        }

        discrepancies = get_pii_discrepancies_from_report(report)

        # First name is assumed correct, rest are variations
        assert len(discrepancies["names"]) == 2
        assert "J DOE" in discrepancies["names"]
        assert "JOHNNY DOE" in discrepancies["names"]

    def test_extracts_address_variations(self):
        """Test extracting address variations from report."""
        report = {
            "personal_info": {
                "addresses": [
                    {"full_address": "123 CURRENT ST"},
                    {"full_address": "456 OLD AVE"},
                ],
            }
        }

        discrepancies = get_pii_discrepancies_from_report(report)

        # Current address is first, previous are issues
        assert len(discrepancies["addresses"]) == 1
        assert "456 OLD AVE" in discrepancies["addresses"]

    def test_extracts_phones(self):
        """Test extracting phone numbers from report."""
        report = {
            "personal_info": {
                "phones": ["555-111-2222", "555-333-4444"],
            }
        }

        discrepancies = get_pii_discrepancies_from_report(report)

        assert len(discrepancies["phones"]) == 2

    def test_empty_report_returns_empty_discrepancies(self):
        """Test that empty report returns empty discrepancies."""
        report = {}

        discrepancies = get_pii_discrepancies_from_report(report)

        assert discrepancies["names"] == []
        assert discrepancies["addresses"] == []
        assert discrepancies["phones"] == []
        assert discrepancies["employers"] == []


class TestGeneratePIIOnlyDispute:
    """Tests for generate_pii_only_dispute function."""

    @patch("services.pii_correction_service.generate_pii_correction_letters")
    def test_calls_generate_letters(self, mock_generate):
        """Test that function calls generate_pii_correction_letters."""
        mock_generate.return_value = {"success": True}

        result = generate_pii_only_dispute(
            client_id=1,
            incorrect_items={"names": ["WRONG"]},
        )

        mock_generate.assert_called_once_with(
            client_id=1,
            incorrect_pii={"names": ["WRONG"]},
        )


class TestIntegration:
    """Integration tests for PII correction service."""

    def test_letter_content_structure(self):
        """Test that letter content has expected structure."""
        client = {
            "name": "Integration Test",
            "ssn_last_four": "9999",
        }
        incorrect_pii = {
            "names": ["WRONG1", "WRONG2"],
            "addresses": ["BAD ADDRESS"],
            "phones": ["555-000-0000"],
            "employers": ["OLD JOB"],
        }

        letter = generate_pii_correction_letter(client, "Equifax", incorrect_pii)

        # Check all required fields
        assert "date" in letter
        assert "bureau_name" in letter
        assert "bureau_address" in letter
        assert "client_name" in letter
        assert "ssn" in letter
        assert "case_number" in letter
        assert "incorrect_pii" in letter
        assert "correct_pii" in letter

        # Check incorrect PII
        assert len(letter["incorrect_pii"]["names"]) == 2
        assert len(letter["incorrect_pii"]["addresses"]) == 1
        assert len(letter["incorrect_pii"]["phones"]) == 1
        assert len(letter["incorrect_pii"]["employers"]) == 1

        # Check correct PII
        assert letter["correct_pii"]["name"] == "Integration Test"
        assert "9999" in letter["correct_pii"]["ssn"]

    def test_multiple_bureaus_have_different_addresses(self):
        """Test that different bureaus have different addresses in letters."""
        client = {"name": "Test", "ssn_last_four": "1234"}
        incorrect_pii = {"names": ["WRONG"]}

        equifax_letter = generate_pii_correction_letter(client, "Equifax", incorrect_pii)
        experian_letter = generate_pii_correction_letter(client, "Experian", incorrect_pii)
        transunion_letter = generate_pii_correction_letter(client, "TransUnion", incorrect_pii)

        # All three should have different addresses
        assert equifax_letter["bureau_address"] != experian_letter["bureau_address"]
        assert experian_letter["bureau_address"] != transunion_letter["bureau_address"]
        assert equifax_letter["bureau_address"] != transunion_letter["bureau_address"]

        # But same client info
        assert equifax_letter["client_name"] == experian_letter["client_name"]
        assert equifax_letter["client_name"] == transunion_letter["client_name"]
