"""
Unit tests for PDF Client Report Builder

Tests cover:
- BasePDFBuilder class (pdf/base.py)
- ClientReportBuilder class (pdf/client_report.py)
"""

import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch


class TestBasePDFBuilderConstants:
    """Tests for BasePDFBuilder class constants"""

    def test_company_name_exists(self):
        """Should have company name constant"""
        from services.pdf.base import BasePDFBuilder

        assert BasePDFBuilder.COMPANY_NAME is not None
        assert "Brightpath" in BasePDFBuilder.COMPANY_NAME

    def test_company_contact_info(self):
        """Should have company contact information"""
        from services.pdf.base import BasePDFBuilder

        assert BasePDFBuilder.COMPANY_ADDRESS is not None
        assert BasePDFBuilder.COMPANY_PHONE is not None
        assert BasePDFBuilder.COMPANY_EMAIL is not None
        assert BasePDFBuilder.COMPANY_WEBSITE is not None

    def test_color_constants_exist(self):
        """Should have color constants"""
        from services.pdf.base import BasePDFBuilder

        assert BasePDFBuilder.PRIMARY_COLOR is not None
        assert BasePDFBuilder.ACCENT_COLOR is not None
        assert BasePDFBuilder.BLUE_COLOR is not None
        assert BasePDFBuilder.WARNING_COLOR is not None


class TestBasePDFBuilderInit:
    """Tests for BasePDFBuilder initialization"""

    def test_initialization(self):
        """Should initialize with styles"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert builder.styles is not None
        assert builder.title_style is not None
        assert builder.body_style is not None

    def test_custom_styles_created(self):
        """Should create custom styles"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert builder.title_style is not None
        assert builder.subtitle_style is not None
        assert builder.heading1_style is not None
        assert builder.heading2_style is not None
        assert builder.heading3_style is not None
        assert builder.body_style is not None
        assert builder.bullet_style is not None
        assert builder.warning_style is not None
        assert builder.center_style is not None
        assert builder.footer_style is not None


class TestBasePDFBuilderSanitizeText:
    """Tests for text sanitization"""

    def test_sanitize_text_handles_none(self):
        """Should handle None input"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        result = builder.sanitize_text(None)

        assert result == ""

    def test_sanitize_text_handles_empty_string(self):
        """Should handle empty string"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        result = builder.sanitize_text("")

        assert result == ""

    def test_sanitize_text_preserves_ascii(self):
        """Should preserve ASCII characters"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        text = "Hello, World! 123"
        result = builder.sanitize_text(text)

        assert result == text

    def test_sanitize_text_replaces_bullets(self):
        """Should replace bullet characters"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert "*" in builder.sanitize_text("\u2022 item")  # bullet
        assert "-" in builder.sanitize_text("\u25e6 item")  # white bullet

    def test_sanitize_text_replaces_smart_quotes(self):
        """Should replace smart quotes"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        result = builder.sanitize_text('\u201c"quoted"\u201d')
        assert '\u201c' not in result
        assert '\u201d' not in result

    def test_sanitize_text_replaces_dashes(self):
        """Should replace em and en dashes"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert " - " in builder.sanitize_text("foo\u2014bar")  # em dash
        assert "-" in builder.sanitize_text("foo\u2013bar")  # en dash

    def test_sanitize_text_replaces_special_symbols(self):
        """Should replace special symbols"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert "(TM)" in builder.sanitize_text("\u2122")  # trademark
        assert "(R)" in builder.sanitize_text("\u00ae")  # registered
        assert "(C)" in builder.sanitize_text("\u00a9")  # copyright

    def test_sanitize_text_replaces_checkmarks(self):
        """Should replace checkmark symbols"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert "[Y]" in builder.sanitize_text("\u2713")  # checkmark
        assert "[N]" in builder.sanitize_text("\u2717")  # X mark

    def test_sanitize_text_replaces_arrows(self):
        """Should replace arrow symbols"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert "->" in builder.sanitize_text("\u2192")  # right arrow
        assert "<-" in builder.sanitize_text("\u2190")  # left arrow


class TestBasePDFBuilderDocument:
    """Tests for document creation"""

    def test_create_document_returns_doc(self):
        """Should return SimpleDocTemplate"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.pdf")
            doc = builder.create_document(output_path)

            assert doc is not None

    def test_create_document_creates_directory(self):
        """Should create output directory"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "test.pdf")
            doc = builder.create_document(output_path)

            assert os.path.isdir(os.path.join(tmpdir, "subdir"))


class TestBasePDFBuilderHelpers:
    """Tests for helper methods"""

    def test_format_currency_with_number(self):
        """Should format number as currency"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert builder.format_currency(1000) == "$1,000.00"
        assert builder.format_currency(1234.56) == "$1,234.56"
        assert builder.format_currency(0) == "$0.00"

    def test_format_currency_with_string(self):
        """Should handle string input"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert builder.format_currency("1000") == "$1,000.00"

    def test_format_currency_with_invalid_input(self):
        """Should handle invalid input"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert builder.format_currency("invalid") == "$0.00"
        assert builder.format_currency(None) == "$0.00"

    def test_format_date_with_datetime(self):
        """Should format datetime object"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        date_obj = datetime(2026, 1, 15)

        result = builder.format_date(date_obj)

        assert "January" in result
        assert "15" in result
        assert "2026" in result

    def test_format_date_with_string(self):
        """Should handle string input"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        result = builder.format_date("2026-01-15")

        assert "2026-01-15" in result

    def test_format_date_with_none(self):
        """Should handle None"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()

        assert builder.format_date(None) == "N/A"


class TestBasePDFBuilderStoryMethods:
    """Tests for story building methods"""

    def test_add_cover_page(self):
        """Should add cover page to story"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []

        builder.add_cover_page(story, "Test Title", "Test Client")

        assert len(story) > 0

    def test_add_cover_page_with_date(self):
        """Should use provided date"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []

        builder.add_cover_page(story, "Test Title", "Test Client", "January 15, 2026")

        assert len(story) > 0

    def test_add_section_header_level_1(self):
        """Should add level 1 header"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []

        builder.add_section_header(story, "Test Header", level=1)

        assert len(story) == 1

    def test_add_section_header_level_2(self):
        """Should add level 2 header"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []

        builder.add_section_header(story, "Test Header", level=2)

        assert len(story) == 1

    def test_add_section_header_level_3(self):
        """Should add level 3 header"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []

        builder.add_section_header(story, "Test Header", level=3)

        assert len(story) == 1

    def test_add_paragraph_default_style(self):
        """Should add paragraph with default style"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []

        builder.add_paragraph(story, "Test paragraph")

        assert len(story) == 1

    def test_add_paragraph_custom_style(self):
        """Should add paragraph with custom style"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []

        builder.add_paragraph(story, "Test paragraph", builder.warning_style)

        assert len(story) == 1

    def test_add_bullet_list(self):
        """Should add bullet list items"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []
        items = ["Item 1", "Item 2", "Item 3"]

        builder.add_bullet_list(story, items)

        assert len(story) == 3

    def test_add_numbered_list(self):
        """Should add numbered list items"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []
        items = ["First", "Second", "Third"]

        builder.add_numbered_list(story, items)

        assert len(story) == 3

    def test_add_table(self):
        """Should add table to story"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []
        data = [
            ["Header 1", "Header 2"],
            ["Row 1 Col 1", "Row 1 Col 2"],
        ]

        builder.add_table(story, data)

        assert len(story) == 2  # Table + Spacer

    def test_add_table_with_widths(self):
        """Should add table with custom widths"""
        from services.pdf.base import BasePDFBuilder
        from reportlab.lib.units import inch

        builder = BasePDFBuilder()
        story = []
        data = [["A", "B"], ["1", "2"]]

        builder.add_table(story, data, col_widths=[1 * inch, 2 * inch])

        assert len(story) == 2

    def test_add_info_box(self):
        """Should add info box"""
        from services.pdf.base import BasePDFBuilder

        builder = BasePDFBuilder()
        story = []

        builder.add_info_box(story, "Box Title", "Box content")

        assert len(story) == 2  # Table + Spacer


class TestClientReportBuilder:
    """Tests for ClientReportBuilder class"""

    def test_initialization(self):
        """Should initialize from BasePDFBuilder"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()

        assert builder.styles is not None
        assert builder.title_style is not None

    def test_generate_creates_pdf(self):
        """Should generate PDF file"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "John Doe",
            "report_date": "January 15, 2026",
            "credit_scores": {"equifax": 650, "experian": 680, "transunion": 670},
            "violations": [],
            "standing": {},
            "damages": {},
            "case_score": {},
            "dispute_round": 1,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert result == output_path
            assert os.path.exists(result)

    def test_generate_with_minimal_data(self):
        """Should handle minimal client data"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_generate_with_violations(self):
        """Should include violations in report"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "Jane Doe",
            "violations": [
                {
                    "account_name": "Test Account",
                    "bureau": "Equifax",
                    "violation_type": "Data Inaccuracy",
                    "fcra_section": "611",
                    "is_willful": True,
                    "description": "Test description",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_generate_with_multiple_violations(self):
        """Should handle multiple violations"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "Test Client",
            "violations": [
                {
                    "account_name": f"Account {i}",
                    "bureau": ["Equifax", "Experian", "TransUnion"][i % 3],
                    "violation_type": "Type " + str(i),
                    "fcra_section": f"{605 + i}",
                    "is_willful": i % 2 == 0,
                    "description": f"Description {i}",
                }
                for i in range(10)
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_generate_with_damages(self):
        """Should include damages calculation"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "Test Client",
            "damages": {
                "actual_damages_total": 5000,
                "statutory_damages_total": 10000,
                "punitive_damages_amount": 25000,
                "settlement_target": 30000,
                "total_exposure": 45000,
                "minimum_acceptable": 20000,
            },
            "violations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_generate_with_standing(self):
        """Should include standing analysis"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "Test Client",
            "standing": {
                "has_concrete_harm": True,
                "concrete_harm_type": "Credit denial",
                "has_dissemination": True,
                "has_causation": True,
            },
            "violations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_generate_with_case_score(self):
        """Should include case score"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "Test Client",
            "case_score": {
                "total_score": 8,
                "recommendation": "litigate",
            },
            "violations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_generate_different_dispute_rounds(self):
        """Should handle different dispute rounds"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()

        for round_num in [1, 2, 3, 4]:
            client_data = {
                "client_name": "Test Client",
                "dispute_round": round_num,
                "violations": [],
            }

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, f"report_round_{round_num}.pdf")
                result = builder.generate(output_path, client_data)

                assert os.path.exists(result)


class TestClientReportBuilderPrivateMethods:
    """Tests for private helper methods"""

    def test_add_cover_page_adds_elements(self):
        """Should add cover page elements"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []

        builder._add_cover_page(story, "Test Client", "January 15, 2026")

        assert len(story) > 0

    def test_add_table_of_contents(self):
        """Should add table of contents"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []

        builder._add_table_of_contents(story)

        # Should have items for each TOC entry plus header and page break
        assert len(story) > 10

    def test_add_executive_summary(self):
        """Should add executive summary"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []
        client_data = {
            "client_name": "Test Client",
            "violations": [],
            "standing": {},
            "damages": {},
            "case_score": {},
        }

        builder._add_executive_summary(story, client_data)

        assert len(story) > 0

    def test_add_fcra_rights(self):
        """Should add FCRA rights section"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []

        builder._add_fcra_rights(story)

        assert len(story) > 0

    def test_add_bureau_analysis(self):
        """Should add bureau analysis section"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []
        client_data = {
            "violations": [
                {"bureau": "Equifax", "account_name": "Test", "fcra_section": "611", "violation_type": "Error"},
            ],
            "credit_scores": {"equifax": 650},
        }

        builder._add_bureau_analysis(story, client_data)

        assert len(story) > 0

    def test_add_violation_categories(self):
        """Should add violation categories section"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []
        client_data = {
            "violations": [
                {
                    "fcra_section": "611",
                    "account_name": "Test",
                    "bureau": "Equifax",
                    "violation_type": "Error",
                    "is_willful": False,
                    "description": "Test",
                },
            ],
        }

        builder._add_violation_categories(story, client_data)

        assert len(story) > 0

    def test_add_account_analysis(self):
        """Should add account analysis section"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []
        client_data = {
            "violations": [
                {"account_name": "Account 1", "bureau": "Equifax", "violation_type": "Type A"},
            ],
        }

        builder._add_account_analysis(story, client_data)

        assert len(story) > 0

    def test_add_legal_framework(self):
        """Should add legal framework section"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []

        builder._add_legal_framework(story)

        assert len(story) > 0

    def test_add_damages_assessment(self):
        """Should add damages assessment section"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []
        client_data = {
            "damages": {
                "statutory_damages_total": 5000,
                "actual_damages_total": 2000,
            },
            "violations": [{"is_willful": True}],
        }

        builder._add_damages_assessment(story, client_data)

        assert len(story) > 0

    def test_add_strategic_recommendations(self):
        """Should add strategic recommendations section"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []
        client_data = {
            "case_score": {},
            "violations": [],
            "dispute_round": 1,
        }

        builder._add_strategic_recommendations(story, client_data)

        assert len(story) > 0

    def test_add_next_steps(self):
        """Should add next steps section"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []
        client_data = {"dispute_round": 1}

        builder._add_next_steps(story, client_data)

        assert len(story) > 0

    def test_add_appendix(self):
        """Should add appendix section"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        story = []
        client_data = {}

        builder._add_appendix(story, client_data)

        assert len(story) > 0


class TestClientReportEdgeCases:
    """Tests for edge cases"""

    def test_handles_unicode_in_client_name(self):
        """Should handle unicode in client name"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "John \u201cNickname\u201d Doe",
            "violations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_handles_empty_violations_list(self):
        """Should handle empty violations list"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "Test Client",
            "violations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_handles_missing_violation_fields(self):
        """Should handle violations with missing fields"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "Test Client",
            "violations": [
                {"account_name": "Test"},  # Minimal violation
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_handles_long_account_names(self):
        """Should handle long account names by truncating"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "Test Client",
            "violations": [
                {
                    "account_name": "A" * 100,  # Very long name
                    "bureau": "Equifax",
                    "fcra_section": "611",
                    "violation_type": "B" * 50,
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)

    def test_handles_high_dispute_round(self):
        """Should handle high dispute round numbers"""
        from services.pdf.client_report import ClientReportBuilder

        builder = ClientReportBuilder()
        client_data = {
            "client_name": "Test Client",
            "dispute_round": 10,
            "violations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.pdf")
            result = builder.generate(output_path, client_data)

            assert os.path.exists(result)
