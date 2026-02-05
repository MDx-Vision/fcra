"""
Unit tests for PDF Generator Service

Tests cover:
- BrandedPDFTemplate class
- SectionPDFGenerator class
- LetterPDFGenerator class
- CreditAnalysisPDFGenerator class
"""

import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch


class TestConstants:
    """Tests for module constants"""

    def test_brightpath_logo_path_exists(self):
        """Should have logo path constant"""
        from services.pdf_generator import BRIGHTPATH_LOGO_PATH

        assert BRIGHTPATH_LOGO_PATH is not None
        assert isinstance(BRIGHTPATH_LOGO_PATH, str)
        assert "logo" in BRIGHTPATH_LOGO_PATH.lower()

    def test_brightpath_tagline_exists(self):
        """Should have tagline constant"""
        from services.pdf_generator import BRIGHTPATH_TAGLINE

        assert BRIGHTPATH_TAGLINE is not None
        assert isinstance(BRIGHTPATH_TAGLINE, str)
        assert len(BRIGHTPATH_TAGLINE) > 0

    def test_brightpath_copyright_exists(self):
        """Should have copyright constant"""
        from services.pdf_generator import BRIGHTPATH_COPYRIGHT

        assert BRIGHTPATH_COPYRIGHT is not None
        assert "Brightpath Ascend Group" in BRIGHTPATH_COPYRIGHT

    def test_brightpath_teal_is_hex_color(self):
        """Should have teal color constant"""
        from services.pdf_generator import BRIGHTPATH_TEAL

        assert BRIGHTPATH_TEAL is not None

    def test_brightpath_lime_is_hex_color(self):
        """Should have lime color constant"""
        from services.pdf_generator import BRIGHTPATH_LIME

        assert BRIGHTPATH_LIME is not None


class TestBrandedPDFTemplate:
    """Tests for BrandedPDFTemplate class"""

    def test_initialization_with_default_logo(self):
        """Should initialize with default logo path"""
        from services.pdf_generator import BrandedPDFTemplate, BRIGHTPATH_LOGO_PATH

        mock_doc = Mock()
        template = BrandedPDFTemplate(mock_doc)

        assert template.doc == mock_doc
        assert template.logo_path == BRIGHTPATH_LOGO_PATH

    def test_initialization_with_custom_logo(self):
        """Should accept custom logo path"""
        from services.pdf_generator import BrandedPDFTemplate

        mock_doc = Mock()
        custom_logo = "/path/to/custom/logo.png"
        template = BrandedPDFTemplate(mock_doc, logo_path=custom_logo)

        assert template.logo_path == custom_logo

    def test_page_dimensions_are_letter_size(self):
        """Should use letter page size"""
        from services.pdf_generator import BrandedPDFTemplate
        from reportlab.lib.pagesizes import letter

        mock_doc = Mock()
        template = BrandedPDFTemplate(mock_doc)

        assert template.page_width == letter[0]
        assert template.page_height == letter[1]

    @patch('services.pdf_generator.os.path.exists', return_value=False)
    def test_add_header_footer_without_logo(self, mock_exists):
        """Should add header/footer without logo"""
        from services.pdf_generator import BrandedPDFTemplate

        mock_doc = Mock()
        mock_doc.leftMargin = 72
        mock_doc.rightMargin = 72
        mock_doc.page = 1

        mock_canvas = Mock()

        template = BrandedPDFTemplate(mock_doc)
        template.add_header_footer(mock_canvas, mock_doc)

        mock_canvas.saveState.assert_called_once()
        mock_canvas.restoreState.assert_called_once()
        mock_canvas.setFont.assert_called()

    @patch('services.pdf_generator.os.path.exists', return_value=True)
    def test_add_header_footer_with_logo(self, mock_exists):
        """Should add header/footer with logo when file exists"""
        from services.pdf_generator import BrandedPDFTemplate

        mock_doc = Mock()
        mock_doc.leftMargin = 72
        mock_doc.rightMargin = 72
        mock_doc.page = 1

        mock_canvas = Mock()

        template = BrandedPDFTemplate(mock_doc)
        template.add_header_footer(mock_canvas, mock_doc)

        mock_canvas.saveState.assert_called_once()
        mock_canvas.restoreState.assert_called_once()

    @patch('services.pdf_generator.os.path.exists', return_value=True)
    def test_add_header_footer_draws_company_name(self, mock_exists):
        """Should draw company name in header"""
        from services.pdf_generator import BrandedPDFTemplate

        mock_doc = Mock()
        mock_doc.leftMargin = 72
        mock_doc.rightMargin = 72
        mock_doc.page = 1

        mock_canvas = Mock()
        mock_canvas.drawImage = Mock(side_effect=Exception("Image error"))

        template = BrandedPDFTemplate(mock_doc)
        template.add_header_footer(mock_canvas, mock_doc)

        # Should still draw company name even if logo fails
        mock_canvas.drawString.assert_called()


class TestSectionPDFGenerator:
    """Tests for SectionPDFGenerator class"""

    def test_initialization(self):
        """Should initialize without errors"""
        from services.pdf_generator import SectionPDFGenerator

        generator = SectionPDFGenerator()

        assert generator is not None

    def test_create_pdf_returns_path(self):
        """Should return output path"""
        from services.pdf_generator import SectionPDFGenerator

        generator = SectionPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.pdf")
            result = generator.create_pdf("Test Title", "Test content", output_path)

            assert result == output_path
            assert os.path.exists(result)

    def test_create_pdf_creates_file(self):
        """Should create PDF file"""
        from services.pdf_generator import SectionPDFGenerator

        generator = SectionPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.pdf")
            generator.create_pdf("Test Title", "Test content", output_path)

            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

    @patch('services.pdf_generator.FPDF')
    @patch('os.makedirs')
    def test_create_pdf_with_multiline_content(self, mock_makedirs, mock_fpdf_class):
        """Should handle multiline content by splitting and rendering each line"""
        from services.pdf_generator import SectionPDFGenerator

        mock_pdf = MagicMock()
        mock_fpdf_class.return_value = mock_pdf

        generator = SectionPDFGenerator()
        content = "Line 1\nLine 2\nLine 3"

        result = generator.create_pdf("Test Title", content, "/tmp/test.pdf")

        # Verify multi_cell was called for each line
        assert mock_pdf.multi_cell.call_count == 3
        mock_pdf.output.assert_called_once()

    def test_create_pdf_creates_directory(self):
        """Should create output directory if it doesn't exist"""
        from services.pdf_generator import SectionPDFGenerator

        generator = SectionPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "test.pdf")
            result = generator.create_pdf("Test Title", "Content", output_path)

            assert os.path.exists(result)
            assert os.path.isdir(os.path.join(tmpdir, "subdir"))


class TestLetterPDFGenerator:
    """Tests for LetterPDFGenerator class"""

    def test_initialization(self):
        """Should initialize with default values"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        assert generator.use_branding == False
        assert generator.custom_color is not None

    def test_sanitize_text_removes_unicode(self):
        """Should sanitize unicode characters"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        # Test bullet replacement
        assert generator.sanitize_text_for_pdf("• item") == "* item"

        # Test smart quotes
        assert generator.sanitize_text_for_pdf('"quoted"') == '"quoted"'

        # Test em dash
        assert generator.sanitize_text_for_pdf("foo—bar") == "foo - bar"

    def test_sanitize_text_handles_none(self):
        """Should handle None input"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        result = generator.sanitize_text_for_pdf(None)

        assert result == ""

    def test_sanitize_text_handles_empty_string(self):
        """Should handle empty string"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        result = generator.sanitize_text_for_pdf("")

        assert result == ""

    def test_sanitize_text_preserves_ascii(self):
        """Should preserve ASCII characters"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        text = "Hello, World! 123"
        result = generator.sanitize_text_for_pdf(text)

        assert result == text

    def test_sanitize_text_replaces_trademark(self):
        """Should replace trademark symbol"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        result = generator.sanitize_text_for_pdf("Brand™")

        assert result == "Brand(TM)"

    def test_sanitize_text_replaces_copyright(self):
        """Should replace copyright symbol"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        result = generator.sanitize_text_for_pdf("©2025")

        assert result == "(C)2025"

    def test_sanitize_text_replaces_ellipsis(self):
        """Should replace ellipsis"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        result = generator.sanitize_text_for_pdf("Wait…")

        assert result == "Wait..."

    def test_generate_dispute_letter_pdf_creates_file(self):
        """Should create dispute letter PDF"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "dispute.pdf")
            result = generator.generate_dispute_letter_pdf(
                letter_content="This is the dispute content.",
                client_name="John Doe",
                bureau="Equifax",
                round_number=1,
                output_path=output_path
            )

            assert result == output_path
            assert os.path.exists(result)

    def test_generate_dispute_letter_pdf_with_paragraphs(self):
        """Should handle multiple paragraphs"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        content = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "dispute.pdf")
            result = generator.generate_dispute_letter_pdf(
                letter_content=content,
                client_name="Jane Doe",
                bureau="Experian",
                round_number=2,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_dispute_letter_pdf_with_section_headings(self):
        """Should handle uppercase section headings"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        content = "SECTION HEADING\n\nRegular paragraph text."

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "dispute.pdf")
            result = generator.generate_dispute_letter_pdf(
                letter_content=content,
                client_name="Client Name",
                bureau="TransUnion",
                round_number=1,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_dispute_letter_pdf_sanitizes_content(self):
        """Should sanitize unicode in content"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        # Use escaped unicode characters to avoid syntax errors
        content = "Content with \u2022 bullets and \u201csmart quotes\u201d"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "dispute.pdf")
            result = generator.generate_dispute_letter_pdf(
                letter_content=content,
                client_name="Client Name",
                bureau="Equifax",
                round_number=1,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_dispute_letter_pdf_with_branding(self):
        """Should add branding when enabled"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        generator.use_branding = True

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "dispute.pdf")
            result = generator.generate_dispute_letter_pdf(
                letter_content="Content",
                client_name="Client Name",
                bureau="Equifax",
                round_number=1,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_batch_letters_success(self):
        """Should generate multiple letters"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            letters_data = [
                {
                    "content": "Letter 1 content",
                    "client_name": "Client 1",
                    "bureau": "Equifax",
                    "round": 1,
                    "output_path": os.path.join(tmpdir, "letter1.pdf"),
                },
                {
                    "content": "Letter 2 content",
                    "client_name": "Client 2",
                    "bureau": "Experian",
                    "round": 1,
                    "output_path": os.path.join(tmpdir, "letter2.pdf"),
                },
            ]

            results = generator.generate_batch_letters(letters_data)

            assert len(results) == 2
            assert all(r["success"] for r in results)
            assert os.path.exists(results[0]["filepath"])
            assert os.path.exists(results[1]["filepath"])

    def test_generate_batch_letters_handles_errors(self):
        """Should handle errors in batch processing"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        letters_data = [
            {
                "content": "Content",
                "client_name": "Client",
                "bureau": "Equifax",
                "round": 1,
                "output_path": "/invalid/path/that/does/not/exist/letter.pdf",
            },
        ]

        results = generator.generate_batch_letters(letters_data)

        assert len(results) == 1
        assert results[0]["success"] == False
        assert "error" in results[0]

    def test_generate_batch_letters_returns_bureau_info(self):
        """Should include bureau info in results"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            letters_data = [
                {
                    "content": "Content",
                    "client_name": "Client",
                    "bureau": "TransUnion",
                    "round": 2,
                    "output_path": os.path.join(tmpdir, "letter.pdf"),
                },
            ]

            results = generator.generate_batch_letters(letters_data)

            assert results[0]["bureau"] == "TransUnion"


class TestCreditAnalysisPDFGenerator:
    """Tests for CreditAnalysisPDFGenerator class"""

    def test_initialization(self):
        """Should initialize with default company info"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        assert generator.company_name == "Brightpath Ascend Group"
        assert generator.company_phone is not None
        assert generator.company_email is not None
        assert generator.company_website is not None
        assert generator.use_branding == True

    def test_sanitize_text_removes_unicode(self):
        """Should sanitize unicode characters"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        result = generator.sanitize_text("Test • bullet")
        assert result == "Test * bullet"

    def test_sanitize_text_handles_none(self):
        """Should handle None input"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()
        result = generator.sanitize_text(None)

        assert result == ""

    def test_sanitize_text_handles_empty_string(self):
        """Should handle empty string"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()
        result = generator.sanitize_text("")

        assert result == ""

    def test_sanitize_text_replaces_smart_quotes(self):
        """Should replace smart quotes"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()
        result = generator.sanitize_text('"quoted"')

        assert result == '"quoted"'

    def test_generate_credit_analysis_pdf_creates_file(self):
        """Should create credit analysis PDF"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="John Doe",
                report_date="January 15, 2026",
                credit_scores={"equifax": 650, "experian": 680, "transunion": 670},
                negative_items=[],
                output_path=output_path
            )

            assert result == output_path
            assert os.path.exists(result)

    def test_generate_credit_analysis_pdf_with_negative_items(self):
        """Should include negative items in report"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        negative_items = [
            {
                "account_name": "Collection Account",
                "bureau": "Equifax",
                "type": "Collection",
                "balance": 1500,
                "status": "Open",
                "notes": "Disputed"
            },
            {
                "account_name": "Late Payment",
                "bureau": "Experian",
                "type": "Late Payment",
                "balance": 0,
                "status": "Closed",
                "notes": ""
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="Jane Doe",
                report_date="January 15, 2026",
                credit_scores={"equifax": 580, "experian": 590, "transunion": 585},
                negative_items=negative_items,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_credit_analysis_pdf_handles_missing_scores(self):
        """Should handle missing credit scores"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="Client Name",
                report_date="January 15, 2026",
                credit_scores={},  # Empty scores
                negative_items=[],
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_credit_analysis_pdf_creates_directory(self):
        """Should create output directory if needed"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="Client Name",
                report_date="January 15, 2026",
                credit_scores={"equifax": 650},
                negative_items=[],
                output_path=output_path
            )

            assert os.path.exists(result)
            assert os.path.isdir(os.path.join(tmpdir, "subdir"))

    def test_generate_credit_analysis_pdf_sanitizes_client_name(self):
        """Should sanitize client name"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="John \u201cSmart\u201d Doe",  # Contains smart quotes (unicode escaped)
                report_date="January 15, 2026",
                credit_scores={"equifax": 650},
                negative_items=[],
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_credit_analysis_pdf_handles_single_name(self):
        """Should handle single-word client names"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="Cher",  # Single name
                report_date="January 15, 2026",
                credit_scores={"equifax": 700},
                negative_items=[],
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_credit_analysis_pdf_without_branding(self):
        """Should work without branding"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()
        generator.use_branding = False

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="Client Name",
                report_date="January 15, 2026",
                credit_scores={"equifax": 650},
                negative_items=[],
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_credit_analysis_pdf_handles_item_with_numeric_balance(self):
        """Should handle numeric balance in negative items"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        negative_items = [
            {
                "account_name": "Test Account",
                "bureau": "Equifax",
                "type": "Collection",
                "balance": 1234.56,
                "status": "Open",
                "notes": ""
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="Client Name",
                report_date="January 15, 2026",
                credit_scores={"equifax": 600},
                negative_items=negative_items,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_credit_analysis_pdf_handles_item_with_string_balance(self):
        """Should handle string balance in negative items"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        negative_items = [
            {
                "account_name": "Test Account",
                "bureau": "Equifax",
                "type": "Collection",
                "balance": "N/A",
                "status": "Open",
                "notes": ""
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="Client Name",
                report_date="January 15, 2026",
                credit_scores={"equifax": 600},
                negative_items=negative_items,
                output_path=output_path
            )

            assert os.path.exists(result)


class TestEdgeCases:
    """Tests for edge cases"""

    def test_letter_generator_empty_content(self):
        """Should handle empty letter content"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "letter.pdf")
            result = generator.generate_dispute_letter_pdf(
                letter_content="",
                client_name="Client",
                bureau="Equifax",
                round_number=1,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_section_generator_empty_content(self):
        """Should handle empty section content"""
        from services.pdf_generator import SectionPDFGenerator

        generator = SectionPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "section.pdf")
            result = generator.create_pdf("Title", "", output_path)

            assert os.path.exists(result)

    def test_letter_generator_special_characters_in_bureau(self):
        """Should handle special characters in bureau name"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "letter.pdf")
            result = generator.generate_dispute_letter_pdf(
                letter_content="Content",
                client_name="Client",
                bureau="Bureau™ Name",
                round_number=1,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_credit_analysis_handles_missing_item_fields(self):
        """Should handle negative items with missing fields"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        # Negative item with minimal fields
        negative_items = [
            {"account_name": "Test"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="Client",
                report_date="January 15, 2026",
                credit_scores={},
                negative_items=negative_items,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_letter_generator_long_content(self):
        """Should handle very long content"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()
        long_content = "This is a paragraph.\n\n" * 100

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "letter.pdf")
            result = generator.generate_dispute_letter_pdf(
                letter_content=long_content,
                client_name="Client",
                bureau="Equifax",
                round_number=1,
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_credit_analysis_many_negative_items(self):
        """Should handle many negative items"""
        from services.pdf_generator import CreditAnalysisPDFGenerator

        generator = CreditAnalysisPDFGenerator()

        negative_items = [
            {
                "account_name": f"Account {i}",
                "bureau": "Equifax",
                "type": "Collection",
                "balance": i * 100,
                "status": "Open",
                "notes": f"Note {i}"
            }
            for i in range(50)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "analysis.pdf")
            result = generator.generate_credit_analysis_pdf(
                client_name="Client",
                report_date="January 15, 2026",
                credit_scores={"equifax": 500, "experian": 520, "transunion": 510},
                negative_items=negative_items,
                output_path=output_path
            )

            assert os.path.exists(result)


class TestSanitizeTextComprehensive:
    """Comprehensive tests for text sanitization"""

    def test_sanitize_currency_symbols(self):
        """Should replace currency symbols"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        assert "EUR" in generator.sanitize_text_for_pdf("€100")
        assert "GBP" in generator.sanitize_text_for_pdf("£100")
        assert "JPY" in generator.sanitize_text_for_pdf("¥100")

    def test_sanitize_mathematical_symbols(self):
        """Should replace mathematical symbols"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        assert "x" in generator.sanitize_text_for_pdf("2×2")
        assert "/" in generator.sanitize_text_for_pdf("4÷2")
        assert "!=" in generator.sanitize_text_for_pdf("≠")
        assert "<=" in generator.sanitize_text_for_pdf("≤")
        assert ">=" in generator.sanitize_text_for_pdf("≥")

    def test_sanitize_degree_symbol(self):
        """Should replace degree symbol"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        assert "deg" in generator.sanitize_text_for_pdf("90°")

    def test_sanitize_removes_high_unicode(self):
        """Should remove high unicode characters"""
        from services.pdf_generator import LetterPDFGenerator

        generator = LetterPDFGenerator()

        # Characters with ordinal > 127 that aren't in replacements should be removed
        result = generator.sanitize_text_for_pdf("Test\u200bZero")  # Zero-width space
        assert "\u200b" not in result
