"""
Unit tests for Freeze Letter Service
Tests for freeze letter generation for credit bureaus, PDF and DOCX creation,
batch management, and bureau address retrieval.
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.freeze_letter_service import (
    CRA_ADDRESSES,
    get_all_bureau_addresses,
    get_primary_bureaus,
    get_secondary_bureaus,
    FreezeLetterPDF,
    generate_single_freeze_letter,
    _add_letter_to_pdf,
    _create_freeze_letter_docx,
    _add_freeze_letter_to_docx,
    generate_freeze_letters,
    generate_freeze_letters_for_primary_bureaus,
    generate_freeze_letters_for_secondary_bureaus,
    get_freeze_batch_status,
    list_client_freeze_batches,
)


# ============== Fixtures ==============


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock()
    db.query.return_value = db
    db.filter.return_value = db
    db.filter_by.return_value = db
    db.first.return_value = None
    db.all.return_value = []
    db.order_by.return_value = db
    return db


@pytest.fixture
def mock_client():
    """Create a mock Client with all required fields."""
    client = Mock()
    client.id = 1
    client.name = "John Doe"
    client.first_name = "John"
    client.last_name = "Doe"
    client.address_street = "123 Main Street"
    client.address_city = "New York"
    client.address_state = "NY"
    client.address_zip = "10001"
    client.ssn_last_four = "1234"
    client.date_of_birth = date(1985, 5, 15)
    return client


@pytest.fixture
def mock_client_dict():
    """Create a client as a dictionary."""
    return {
        "name": "Jane Smith",
        "first_name": "Jane",
        "last_name": "Smith",
        "address_street": "456 Oak Avenue",
        "address_city": "Los Angeles",
        "address_state": "CA",
        "address_zip": "90001",
        "ssn_last_four": "5678",
        "date_of_birth": date(1990, 8, 20),
    }


@pytest.fixture
def mock_client_minimal():
    """Create a mock Client with minimal data."""
    client = Mock()
    client.id = 2
    client.name = None
    client.first_name = "Test"
    client.last_name = "User"
    client.address_street = None
    client.address_city = None
    client.address_state = None
    client.address_zip = None
    client.ssn_last_four = None
    client.date_of_birth = None
    return client


@pytest.fixture
def mock_freeze_batch():
    """Create a mock FreezeLetterBatch."""
    batch = Mock()
    batch.id = 1
    batch.client_id = 1
    batch.batch_uuid = "test-uuid-1234-5678-abcd"
    batch.bureaus_included = ["Equifax", "Experian", "TransUnion"]
    batch.total_bureaus = 3
    batch.generated_pdf_path = "/path/to/letters.pdf"
    batch.generated_docx_path = "/path/to/letters.docx"
    batch.status = "generated"
    batch.mail_method = None
    batch.mailed_at = None
    batch.created_at = datetime(2025, 1, 15, 10, 30, 0)
    return batch


@pytest.fixture
def sample_bureau_address():
    """Return a sample bureau address dict."""
    return {
        "name": "Equifax Information Services LLC",
        "freeze_address": "P.O. Box 105788",
        "city": "Atlanta",
        "state": "GA",
        "zip": "30348",
        "phone": "1-800-685-1111",
        "website": "www.equifax.com/personal/credit-report-services/credit-freeze/",
        "type": "primary",
    }


# ============== Bureau Address Tests ==============


class TestCRAAddresses:
    """Tests for CRA_ADDRESSES constant."""

    def test_cra_addresses_contains_12_bureaus(self):
        """Test that CRA_ADDRESSES contains all 12 bureaus."""
        assert len(CRA_ADDRESSES) == 12

    def test_cra_addresses_has_primary_bureaus(self):
        """Test that CRA_ADDRESSES contains the 3 primary bureaus."""
        assert "Equifax" in CRA_ADDRESSES
        assert "Experian" in CRA_ADDRESSES
        assert "TransUnion" in CRA_ADDRESSES

    def test_cra_addresses_has_secondary_bureaus(self):
        """Test that CRA_ADDRESSES contains secondary bureaus."""
        secondary_bureaus = [
            "Innovis", "ChexSystems", "Clarity Services Inc",
            "LexisNexis", "CoreLogic Teletrack", "Factor Trust Inc",
            "MicroBilt/PRBC", "LexisNexis Risk Solutions", "DataX Ltd"
        ]
        for bureau in secondary_bureaus:
            assert bureau in CRA_ADDRESSES

    def test_cra_addresses_structure(self):
        """Test that each bureau has required fields."""
        required_fields = ["name", "freeze_address", "city", "state", "zip", "phone", "website", "type"]
        for bureau_name, bureau_info in CRA_ADDRESSES.items():
            for field in required_fields:
                assert field in bureau_info, f"Bureau {bureau_name} missing field {field}"

    def test_cra_addresses_type_values(self):
        """Test that bureau types are either 'primary' or 'secondary'."""
        for bureau_name, bureau_info in CRA_ADDRESSES.items():
            assert bureau_info["type"] in ["primary", "secondary"], f"Bureau {bureau_name} has invalid type"


class TestGetAllBureauAddresses:
    """Tests for get_all_bureau_addresses function."""

    def test_get_all_bureau_addresses_returns_copy(self):
        """Test that get_all_bureau_addresses returns a copy of CRA_ADDRESSES."""
        result = get_all_bureau_addresses()
        assert result == CRA_ADDRESSES
        assert result is not CRA_ADDRESSES  # Should be a copy

    def test_get_all_bureau_addresses_count(self):
        """Test that get_all_bureau_addresses returns 12 bureaus."""
        result = get_all_bureau_addresses()
        assert len(result) == 12


class TestGetPrimaryBureaus:
    """Tests for get_primary_bureaus function."""

    def test_get_primary_bureaus_returns_three(self):
        """Test that get_primary_bureaus returns exactly 3 bureaus."""
        result = get_primary_bureaus()
        assert len(result) == 3

    def test_get_primary_bureaus_names(self):
        """Test that get_primary_bureaus returns correct bureaus."""
        result = get_primary_bureaus()
        assert "Equifax" in result
        assert "Experian" in result
        assert "TransUnion" in result

    def test_get_primary_bureaus_types(self):
        """Test that all returned bureaus have type 'primary'."""
        result = get_primary_bureaus()
        for bureau_info in result.values():
            assert bureau_info["type"] == "primary"


class TestGetSecondaryBureaus:
    """Tests for get_secondary_bureaus function."""

    def test_get_secondary_bureaus_returns_nine(self):
        """Test that get_secondary_bureaus returns exactly 9 bureaus."""
        result = get_secondary_bureaus()
        assert len(result) == 9

    def test_get_secondary_bureaus_types(self):
        """Test that all returned bureaus have type 'secondary'."""
        result = get_secondary_bureaus()
        for bureau_info in result.values():
            assert bureau_info["type"] == "secondary"

    def test_get_secondary_bureaus_excludes_primary(self):
        """Test that secondary bureaus excludes primary bureaus."""
        result = get_secondary_bureaus()
        assert "Equifax" not in result
        assert "Experian" not in result
        assert "TransUnion" not in result


# ============== FreezeLetterPDF Class Tests ==============


class TestFreezeLetterPDF:
    """Tests for FreezeLetterPDF class."""

    def test_freeze_letter_pdf_initialization(self):
        """Test FreezeLetterPDF initializes correctly."""
        pdf = FreezeLetterPDF()
        assert pdf is not None

    def test_freeze_letter_pdf_auto_page_break(self):
        """Test that auto page break is enabled."""
        pdf = FreezeLetterPDF()
        # FPDF auto_page_break defaults to True; verify margin is set
        assert pdf.auto_page_break is True

    def test_freeze_letter_pdf_header_is_empty(self):
        """Test that header method does nothing (no header)."""
        pdf = FreezeLetterPDF()
        pdf.add_page()
        # Header should not add any content - verify no exception
        pdf.header()

    def test_freeze_letter_pdf_footer(self):
        """Test that footer adds page number."""
        pdf = FreezeLetterPDF()
        pdf.add_page()
        # Footer should work without exception
        pdf.footer()


# ============== Generate Single Freeze Letter Tests ==============


class TestGenerateSingleFreezeLetter:
    """Tests for generate_single_freeze_letter function."""

    def test_generate_single_freeze_letter_with_client_object(self, mock_client, sample_bureau_address):
        """Test generating letter content with Client object."""
        result = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)

        assert result["client_name"] == "John Doe"
        assert result["bureau_name"] == "Equifax Information Services LLC"
        assert result["ssn_last4"] == "1234"
        assert result["dob"] == "May 15, 1985"
        assert "New York" in result["client_address"]
        assert result["bureau_phone"] == "1-800-685-1111"

    def test_generate_single_freeze_letter_with_dict(self, mock_client_dict, sample_bureau_address):
        """Test generating letter content with client as dictionary."""
        result = generate_single_freeze_letter(mock_client_dict, "Equifax", sample_bureau_address)

        assert result["client_name"] == "Jane Smith"
        assert result["ssn_last4"] == "5678"
        assert "Los Angeles" in result["client_address"]

    def test_generate_single_freeze_letter_constructs_name_from_parts(self, sample_bureau_address):
        """Test that client name is constructed from first/last if name is empty."""
        client_dict = {
            "name": "",
            "first_name": "Bob",
            "last_name": "Wilson",
            "address_street": "789 Pine St",
            "address_city": "Chicago",
            "address_state": "IL",
            "address_zip": "60601",
            "ssn_last_four": "9999",
            "date_of_birth": None,
        }
        result = generate_single_freeze_letter(client_dict, "Equifax", sample_bureau_address)

        assert result["client_name"] == "Bob Wilson"

    def test_generate_single_freeze_letter_missing_dob(self, mock_client, sample_bureau_address):
        """Test letter generation when date of birth is missing."""
        mock_client.date_of_birth = None
        result = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)

        assert result["dob"] == "[DATE OF BIRTH]"

    def test_generate_single_freeze_letter_missing_ssn(self, mock_client, sample_bureau_address):
        """Test letter generation when SSN is missing."""
        mock_client.ssn_last_four = None
        result = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)

        assert result["ssn_last4"] == "XXXX"

    def test_generate_single_freeze_letter_missing_address(self, mock_client_minimal, sample_bureau_address):
        """Test letter generation when address is missing."""
        result = generate_single_freeze_letter(mock_client_minimal, "Equifax", sample_bureau_address)

        assert result["client_address"] == "[CLIENT ADDRESS]"

    def test_generate_single_freeze_letter_date_as_string(self, sample_bureau_address):
        """Test letter generation when date_of_birth is a string."""
        client_dict = {
            "name": "Test User",
            "first_name": "Test",
            "last_name": "User",
            "address_street": "123 Test St",
            "address_city": "Test City",
            "address_state": "TS",
            "address_zip": "12345",
            "ssn_last_four": "1111",
            "date_of_birth": "1990-01-01",  # String instead of date object
        }
        result = generate_single_freeze_letter(client_dict, "Equifax", sample_bureau_address)

        assert result["dob"] == "1990-01-01"

    def test_generate_single_freeze_letter_includes_date(self, mock_client, sample_bureau_address):
        """Test that letter includes current date."""
        result = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)

        # Date should be in format "Month DD, YYYY"
        assert result["date"] is not None
        assert len(result["date"]) > 0

    def test_generate_single_freeze_letter_bureau_address_format(self, mock_client, sample_bureau_address):
        """Test bureau address is formatted correctly."""
        result = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)

        assert "P.O. Box 105788" in result["bureau_address"]
        assert "Atlanta" in result["bureau_address"]
        assert "GA" in result["bureau_address"]
        assert "30348" in result["bureau_address"]


# ============== Add Letter to PDF Tests ==============


class TestAddLetterToPDF:
    """Tests for _add_letter_to_pdf function."""

    def test_add_letter_to_pdf_creates_page(self, mock_client, sample_bureau_address):
        """Test that _add_letter_to_pdf adds a page to PDF."""
        pdf = FreezeLetterPDF()
        letter_content = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)

        initial_pages = pdf.page
        _add_letter_to_pdf(pdf, letter_content)

        assert pdf.page > initial_pages

    def test_add_letter_to_pdf_multiple_letters(self, mock_client, sample_bureau_address):
        """Test adding multiple letters to PDF creates multiple pages."""
        pdf = FreezeLetterPDF()
        letter_content = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)

        initial_page = pdf.page
        _add_letter_to_pdf(pdf, letter_content)
        after_first = pdf.page
        _add_letter_to_pdf(pdf, letter_content)
        after_second = pdf.page
        _add_letter_to_pdf(pdf, letter_content)
        after_third = pdf.page

        # Each letter adds at least one page (may add more if content overflows)
        assert after_first > initial_page
        assert after_second > after_first
        assert after_third > after_second


# ============== Create Freeze Letter DOCX Tests ==============


class TestCreateFreezeLetterDocx:
    """Tests for _create_freeze_letter_docx function."""

    def test_create_freeze_letter_docx_returns_list(self, mock_client, sample_bureau_address):
        """Test that _create_freeze_letter_docx returns a list of content items."""
        letter_content = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)
        result = _create_freeze_letter_docx(letter_content)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_create_freeze_letter_docx_content_types(self, mock_client, sample_bureau_address):
        """Test that content items have valid types."""
        letter_content = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)
        result = _create_freeze_letter_docx(letter_content)

        for item in result:
            assert "type" in item
            assert item["type"] in ["paragraph", "spacing"]

    def test_create_freeze_letter_docx_includes_client_name(self, mock_client, sample_bureau_address):
        """Test that DOCX content includes client name."""
        letter_content = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)
        result = _create_freeze_letter_docx(letter_content)

        # Find paragraph with client name
        client_name_found = False
        for item in result:
            if item["type"] == "paragraph" and "John Doe" in item.get("text", ""):
                client_name_found = True
                break
        assert client_name_found

    def test_create_freeze_letter_docx_includes_bureau_name(self, mock_client, sample_bureau_address):
        """Test that DOCX content includes bureau name."""
        letter_content = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)
        result = _create_freeze_letter_docx(letter_content)

        # Find paragraph with bureau name
        bureau_name_found = False
        for item in result:
            if item["type"] == "paragraph" and "Equifax" in item.get("text", ""):
                bureau_name_found = True
                break
        assert bureau_name_found

    def test_create_freeze_letter_docx_includes_legal_sections(self, mock_client, sample_bureau_address):
        """Test that DOCX content includes legal authority section."""
        letter_content = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)
        result = _create_freeze_letter_docx(letter_content)

        # Find legal authority section
        legal_found = False
        for item in result:
            if item["type"] == "paragraph" and "LEGAL AUTHORITY" in item.get("text", ""):
                legal_found = True
                break
        assert legal_found


# ============== Add Freeze Letter to DOCX Tests ==============


class TestAddFreezeLetterToDocx:
    """Tests for _add_freeze_letter_to_docx function."""

    def test_add_freeze_letter_to_docx_with_page_break(self, mock_client, sample_bureau_address):
        """Test adding letter to DOCX with page break."""
        with patch('services.freeze_letter_service.Document') as MockDocument:
            mock_doc = Mock()
            mock_paragraph = Mock()
            mock_doc.add_paragraph.return_value = mock_paragraph
            mock_paragraph.add_run.return_value = Mock()
            mock_paragraph.paragraph_format = Mock()

            letter_content = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)
            _add_freeze_letter_to_docx(mock_doc, letter_content, add_page_break=True)

            mock_doc.add_page_break.assert_called_once()

    def test_add_freeze_letter_to_docx_without_page_break(self, mock_client, sample_bureau_address):
        """Test adding letter to DOCX without page break."""
        with patch('services.freeze_letter_service.Document') as MockDocument:
            mock_doc = Mock()
            mock_paragraph = Mock()
            mock_doc.add_paragraph.return_value = mock_paragraph
            mock_paragraph.add_run.return_value = Mock()
            mock_paragraph.paragraph_format = Mock()

            letter_content = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)
            _add_freeze_letter_to_docx(mock_doc, letter_content, add_page_break=False)

            mock_doc.add_page_break.assert_not_called()


# ============== Generate Freeze Letters Tests ==============


class TestGenerateFreezeLetters:
    """Tests for generate_freeze_letters function."""

    @patch('services.freeze_letter_service.get_db')
    @patch('services.freeze_letter_service.os.makedirs')
    @patch('services.freeze_letter_service.Document')
    def test_generate_freeze_letters_success(self, mock_document, mock_makedirs, mock_get_db, mock_client):
        """Test successful generation of freeze letters."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        # Mock document save
        mock_doc_instance = Mock()
        mock_document.return_value = mock_doc_instance
        mock_paragraph = Mock()
        mock_doc_instance.add_paragraph.return_value = mock_paragraph
        mock_paragraph.add_run.return_value = Mock()
        mock_paragraph.paragraph_format = Mock()

        with patch.object(FreezeLetterPDF, 'output'):
            result = generate_freeze_letters(1, bureaus=["Equifax", "Experian"])

        assert result["success"] is True
        assert "batch_id" in result
        assert result["total_letters"] == 2
        assert result["bureaus_included"] == ["Equifax", "Experian"]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('services.freeze_letter_service.get_db')
    def test_generate_freeze_letters_client_not_found(self, mock_get_db):
        """Test error when client is not found."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = generate_freeze_letters(999)

        assert result["success"] is False
        assert "Client with ID 999 not found" in result["error"]

    @patch('services.freeze_letter_service.get_db')
    def test_generate_freeze_letters_invalid_bureaus(self, mock_get_db, mock_client):
        """Test error when no valid bureaus specified."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        result = generate_freeze_letters(1, bureaus=["InvalidBureau1", "InvalidBureau2"])

        assert result["success"] is False
        assert "No valid bureaus specified" in result["error"]

    @patch('services.freeze_letter_service.get_db')
    @patch('services.freeze_letter_service.os.makedirs')
    @patch('services.freeze_letter_service.Document')
    def test_generate_freeze_letters_all_bureaus(self, mock_document, mock_makedirs, mock_get_db, mock_client):
        """Test generation for all 12 bureaus when bureaus=None."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        mock_doc_instance = Mock()
        mock_document.return_value = mock_doc_instance
        mock_paragraph = Mock()
        mock_doc_instance.add_paragraph.return_value = mock_paragraph
        mock_paragraph.add_run.return_value = Mock()
        mock_paragraph.paragraph_format = Mock()

        with patch.object(FreezeLetterPDF, 'output'):
            result = generate_freeze_letters(1, bureaus=None)

        assert result["success"] is True
        assert result["total_letters"] == 12

    @patch('services.freeze_letter_service.get_db')
    @patch('services.freeze_letter_service.os.makedirs')
    @patch('services.freeze_letter_service.Document')
    def test_generate_freeze_letters_filters_invalid_bureaus(self, mock_document, mock_makedirs, mock_get_db, mock_client):
        """Test that invalid bureaus are filtered out."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        mock_doc_instance = Mock()
        mock_document.return_value = mock_doc_instance
        mock_paragraph = Mock()
        mock_doc_instance.add_paragraph.return_value = mock_paragraph
        mock_paragraph.add_run.return_value = Mock()
        mock_paragraph.paragraph_format = Mock()

        with patch.object(FreezeLetterPDF, 'output'):
            result = generate_freeze_letters(1, bureaus=["Equifax", "InvalidBureau", "Experian"])

        assert result["success"] is True
        assert result["total_letters"] == 2
        assert "InvalidBureau" not in result["bureaus_included"]

    @patch('services.freeze_letter_service.get_db')
    def test_generate_freeze_letters_exception_handling(self, mock_get_db, mock_client):
        """Test that exceptions are handled and rolled back."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.commit.side_effect = Exception("Database error")

        with patch('services.freeze_letter_service.os.makedirs'):
            with patch('services.freeze_letter_service.Document'):
                with patch.object(FreezeLetterPDF, 'output'):
                    result = generate_freeze_letters(1, bureaus=["Equifax"])

        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_db.rollback.assert_called_once()


# ============== Generate Freeze Letters Convenience Function Tests ==============


class TestGenerateFreezeLettersForPrimaryBureaus:
    """Tests for generate_freeze_letters_for_primary_bureaus function."""

    @patch('services.freeze_letter_service.generate_freeze_letters')
    def test_generate_freeze_letters_for_primary_bureaus(self, mock_generate):
        """Test that function calls generate_freeze_letters with primary bureaus."""
        mock_generate.return_value = {"success": True}

        result = generate_freeze_letters_for_primary_bureaus(1)

        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        bureaus_arg = call_args[1]["bureaus"]
        assert len(bureaus_arg) == 3
        assert "Equifax" in bureaus_arg
        assert "Experian" in bureaus_arg
        assert "TransUnion" in bureaus_arg


class TestGenerateFreezeLettersForSecondaryBureaus:
    """Tests for generate_freeze_letters_for_secondary_bureaus function."""

    @patch('services.freeze_letter_service.generate_freeze_letters')
    def test_generate_freeze_letters_for_secondary_bureaus(self, mock_generate):
        """Test that function calls generate_freeze_letters with secondary bureaus."""
        mock_generate.return_value = {"success": True}

        result = generate_freeze_letters_for_secondary_bureaus(1)

        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        bureaus_arg = call_args[1]["bureaus"]
        assert len(bureaus_arg) == 9
        assert "Equifax" not in bureaus_arg
        assert "Experian" not in bureaus_arg
        assert "TransUnion" not in bureaus_arg


# ============== Get Freeze Batch Status Tests ==============


class TestGetFreezeBatchStatus:
    """Tests for get_freeze_batch_status function."""

    @patch('services.freeze_letter_service.get_db')
    def test_get_freeze_batch_status_success(self, mock_get_db, mock_freeze_batch):
        """Test successful batch status retrieval."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_freeze_batch

        result = get_freeze_batch_status("test-uuid-1234-5678-abcd")

        assert result["success"] is True
        assert result["batch_id"] == "test-uuid-1234-5678-abcd"
        assert result["client_id"] == 1
        assert result["bureaus_included"] == ["Equifax", "Experian", "TransUnion"]
        assert result["total_bureaus"] == 3
        assert result["status"] == "generated"

    @patch('services.freeze_letter_service.get_db')
    def test_get_freeze_batch_status_not_found(self, mock_get_db):
        """Test batch status retrieval when batch not found."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_freeze_batch_status("non-existent-uuid")

        assert result["success"] is False
        assert "Batch not found" in result["error"]

    @patch('services.freeze_letter_service.get_db')
    def test_get_freeze_batch_status_with_mailed_at(self, mock_get_db, mock_freeze_batch):
        """Test batch status when mailed_at is set."""
        mock_freeze_batch.mailed_at = datetime(2025, 1, 20, 14, 0, 0)
        mock_freeze_batch.mail_method = "certified"
        mock_freeze_batch.status = "mailed"

        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_freeze_batch

        result = get_freeze_batch_status("test-uuid-1234-5678-abcd")

        assert result["success"] is True
        assert result["mail_method"] == "certified"
        assert result["mailed_at"] == "2025-01-20T14:00:00"
        assert result["status"] == "mailed"

    @patch('services.freeze_letter_service.get_db')
    def test_get_freeze_batch_status_closes_db(self, mock_get_db, mock_freeze_batch):
        """Test that database session is closed after retrieval."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_freeze_batch

        get_freeze_batch_status("test-uuid-1234-5678-abcd")

        mock_db.close.assert_called_once()


# ============== List Client Freeze Batches Tests ==============


class TestListClientFreezeBatches:
    """Tests for list_client_freeze_batches function."""

    @patch('services.freeze_letter_service.get_db')
    def test_list_client_freeze_batches_success(self, mock_get_db, mock_freeze_batch):
        """Test successful listing of client freeze batches."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_freeze_batch]

        result = list_client_freeze_batches(1)

        assert len(result) == 1
        assert result[0]["batch_id"] == "test-uuid-1234-5678-abcd"
        assert result[0]["total_bureaus"] == 3
        assert result[0]["status"] == "generated"

    @patch('services.freeze_letter_service.get_db')
    def test_list_client_freeze_batches_empty(self, mock_get_db):
        """Test listing batches when client has none."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = list_client_freeze_batches(999)

        assert len(result) == 0

    @patch('services.freeze_letter_service.get_db')
    def test_list_client_freeze_batches_multiple(self, mock_get_db, mock_freeze_batch):
        """Test listing multiple batches for a client."""
        batch2 = Mock()
        batch2.batch_uuid = "batch-2-uuid"
        batch2.total_bureaus = 12
        batch2.generated_pdf_path = "/path/to/batch2.pdf"
        batch2.status = "mailed"
        batch2.created_at = datetime(2025, 1, 10, 9, 0, 0)

        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_freeze_batch, batch2
        ]

        result = list_client_freeze_batches(1)

        assert len(result) == 2
        assert result[0]["batch_id"] == "test-uuid-1234-5678-abcd"
        assert result[1]["batch_id"] == "batch-2-uuid"

    @patch('services.freeze_letter_service.get_db')
    def test_list_client_freeze_batches_closes_db(self, mock_get_db):
        """Test that database session is closed after listing."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        list_client_freeze_batches(1)

        mock_db.close.assert_called_once()

    @patch('services.freeze_letter_service.get_db')
    def test_list_client_freeze_batches_date_formatting(self, mock_get_db, mock_freeze_batch):
        """Test that created_at is properly formatted as ISO string."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_freeze_batch]

        result = list_client_freeze_batches(1)

        assert result[0]["created_at"] == "2025-01-15T10:30:00"

    @patch('services.freeze_letter_service.get_db')
    def test_list_client_freeze_batches_none_created_at(self, mock_get_db, mock_freeze_batch):
        """Test handling of None created_at."""
        mock_freeze_batch.created_at = None

        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_freeze_batch]

        result = list_client_freeze_batches(1)

        assert result[0]["created_at"] is None


# ============== Edge Cases and Integration Tests ==============


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_generate_single_freeze_letter_with_empty_client_name(self, sample_bureau_address):
        """Test letter generation with completely empty client name fields."""
        client_dict = {
            "name": "",
            "first_name": "",
            "last_name": "",
            "address_street": "123 Test St",
            "address_city": "Test City",
            "address_state": "TS",
            "address_zip": "12345",
            "ssn_last_four": "0000",
            "date_of_birth": date(2000, 1, 1),
        }
        result = generate_single_freeze_letter(client_dict, "Equifax", sample_bureau_address)

        # With empty name and empty first_name/last_name, name remains empty string
        # (the name construction from first/last only happens when name is falsy but first/last exist)
        assert result["client_name"] == ""

    def test_generate_single_freeze_letter_special_characters_in_name(self, sample_bureau_address):
        """Test letter generation with special characters in name."""
        client_dict = {
            "name": "O'Brien-McDonald Jr.",
            "first_name": "Patrick",
            "last_name": "O'Brien-McDonald",
            "address_street": "123 Test St",
            "address_city": "Test City",
            "address_state": "TS",
            "address_zip": "12345",
            "ssn_last_four": "1234",
            "date_of_birth": date(1985, 5, 15),
        }
        result = generate_single_freeze_letter(client_dict, "Equifax", sample_bureau_address)

        assert result["client_name"] == "O'Brien-McDonald Jr."

    def test_bureau_address_missing_fields(self, mock_client):
        """Test letter generation with bureau address missing some fields."""
        incomplete_bureau = {
            "name": "Test Bureau",
            "freeze_address": "P.O. Box 123",
            "city": "",
            "state": "",
            "zip": "",
            "phone": "",
            "website": "",
            "type": "secondary",
        }
        result = generate_single_freeze_letter(mock_client, "Test Bureau", incomplete_bureau)

        assert result["bureau_name"] == "Test Bureau"
        assert result["bureau_phone"] == ""

    def test_all_bureaus_have_freeze_addresses(self):
        """Test that all bureaus have non-empty freeze addresses."""
        for bureau_name, bureau_info in CRA_ADDRESSES.items():
            assert bureau_info["freeze_address"], f"{bureau_name} has empty freeze_address"
            assert bureau_info["city"], f"{bureau_name} has empty city"
            assert bureau_info["state"], f"{bureau_name} has empty state"
            assert bureau_info["zip"], f"{bureau_name} has empty zip"

    def test_all_bureaus_have_phone_numbers(self):
        """Test that all bureaus have phone numbers."""
        for bureau_name, bureau_info in CRA_ADDRESSES.items():
            assert bureau_info["phone"], f"{bureau_name} has empty phone"
            assert bureau_info["phone"].startswith("1-"), f"{bureau_name} phone doesn't start with 1-"

    def test_primary_and_secondary_bureaus_are_mutually_exclusive(self):
        """Test that primary and secondary bureau sets don't overlap."""
        primary = set(get_primary_bureaus().keys())
        secondary = set(get_secondary_bureaus().keys())

        assert primary.isdisjoint(secondary)
        assert len(primary) + len(secondary) == 12

    def test_client_address_partial_data(self, sample_bureau_address):
        """Test letter generation with partial address data."""
        client_dict = {
            "name": "Test User",
            "first_name": "Test",
            "last_name": "User",
            "address_street": "123 Main St",
            "address_city": "",
            "address_state": "NY",
            "address_zip": "",
            "ssn_last_four": "1234",
            "date_of_birth": None,
        }
        result = generate_single_freeze_letter(client_dict, "Equifax", sample_bureau_address)

        # Should include available address parts
        assert "123 Main St" in result["client_address"]
        assert "NY" in result["client_address"]


class TestIntegration:
    """Integration-style tests that verify multiple components work together."""

    def test_generate_letters_for_all_bureaus_creates_correct_count(self, mock_client, sample_bureau_address):
        """Test that generating letters for all bureaus creates correct number of letter contents."""
        all_bureaus = get_all_bureau_addresses()
        letter_contents = []

        for bureau_name, bureau_info in all_bureaus.items():
            letter_content = generate_single_freeze_letter(mock_client, bureau_name, bureau_info)
            letter_contents.append(letter_content)

        assert len(letter_contents) == 12

    def test_primary_bureau_letters_have_correct_names(self, mock_client):
        """Test that primary bureau letters have correct bureau names."""
        primary_bureaus = get_primary_bureaus()
        expected_names = {
            "Equifax": "Equifax Information Services LLC",
            "Experian": "Experian Security Freeze",
            "TransUnion": "TransUnion LLC",
        }

        for bureau_name, bureau_info in primary_bureaus.items():
            letter_content = generate_single_freeze_letter(mock_client, bureau_name, bureau_info)
            assert letter_content["bureau_name"] == expected_names[bureau_name]

    def test_letter_content_consistency(self, mock_client, sample_bureau_address):
        """Test that letter content is consistent across multiple generations."""
        letter1 = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)
        letter2 = generate_single_freeze_letter(mock_client, "Equifax", sample_bureau_address)

        # All fields except date should be identical
        assert letter1["client_name"] == letter2["client_name"]
        assert letter1["bureau_name"] == letter2["bureau_name"]
        assert letter1["client_address"] == letter2["client_address"]
        assert letter1["ssn_last4"] == letter2["ssn_last4"]
        assert letter1["dob"] == letter2["dob"]
        assert letter1["bureau_address"] == letter2["bureau_address"]
        assert letter1["bureau_phone"] == letter2["bureau_phone"]
