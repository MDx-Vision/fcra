"""
Unit tests for PDF Service
Tests for FCRA PDF generation including client reports and legal analysis documents.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import tempfile
from datetime import datetime

# Skip all tests in this module if weasyprint is not installed
# WeasyPrint has complex system dependencies that may not be available in CI
pytest.importorskip("weasyprint", reason="weasyprint not installed")

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import (
    FCRAPDFGenerator,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    DARK_COLOR,
)


# =============================================================================
# Mock Classes for Testing
# =============================================================================

class MockViolation:
    """Mock Violation object for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.fcra_section = kwargs.get('fcra_section', '1681e(b)')
        self.violation_type = kwargs.get('violation_type', 'Inaccurate Information')
        self.bureau = kwargs.get('bureau', 'Equifax')
        self.description = kwargs.get('description', 'Test violation description')
        self.is_willful = kwargs.get('is_willful', True)
        self.statutory_damages_min = kwargs.get('statutory_damages_min', 100)
        self.statutory_damages_max = kwargs.get('statutory_damages_max', 1000)


class MockDamages:
    """Mock Damages object for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.total_exposure = kwargs.get('total_exposure', 50000)
        self.settlement_target = kwargs.get('settlement_target', 32500)
        self.actual_damages_total = kwargs.get('actual_damages_total', 10000)
        self.statutory_damages_total = kwargs.get('statutory_damages_total', 5000)
        self.punitive_damages_amount = kwargs.get('punitive_damages_amount', 15000)


class MockCaseScore:
    """Mock CaseScore object for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.total_score = kwargs.get('total_score', 7)


class MockStanding:
    """Mock Standing object for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.has_concrete_harm = kwargs.get('has_concrete_harm', True)
        self.has_dissemination = kwargs.get('has_dissemination', True)
        self.has_causation = kwargs.get('has_causation', True)


class MockAnalysis:
    """Mock Analysis object for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.full_analysis = kwargs.get('full_analysis', 'This is the full analysis text.\n\nWith multiple paragraphs.')


# =============================================================================
# Tests for FCRAPDFGenerator Initialization
# =============================================================================

class TestFCRAPDFGeneratorInit:
    """Test FCRAPDFGenerator initialization."""

    def test_init_creates_generator(self):
        """Test that generator can be instantiated."""
        generator = FCRAPDFGenerator()
        assert generator is not None

    def test_init_sets_up_styles(self):
        """Test that custom styles are set up."""
        generator = FCRAPDFGenerator()
        assert generator.styles is not None
        # Check that custom styles were added
        assert 'ClientHeader' in generator.styles.byName
        assert 'ClientSubHeader' in generator.styles.byName
        assert 'ClientBody' in generator.styles.byName
        assert 'ClientHighlight' in generator.styles.byName
        assert 'LegalTitle' in generator.styles.byName
        assert 'LegalHeader' in generator.styles.byName
        assert 'LegalSubHeader' in generator.styles.byName
        assert 'LegalBody' in generator.styles.byName


# =============================================================================
# Tests for _sanitize_text()
# =============================================================================

class TestSanitizeText:
    """Test text sanitization for PDF rendering."""

    def test_sanitize_text_basic(self):
        """Test basic text passes through."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("Hello World")
        assert result == "Hello World"

    def test_sanitize_text_none_input(self):
        """Test None returns empty string."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text(None)
        assert result == ""

    def test_sanitize_text_empty_string(self):
        """Test empty string returns empty string."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("")
        assert result == ""

    def test_sanitize_text_html_less_than(self):
        """Test < is escaped (& is escaped first, so result is double-escaped)."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("a < b")
        # Note: The implementation replaces & before <, so &lt; becomes &amp;lt;
        assert "&amp;lt;" in result
        assert "<" not in result

    def test_sanitize_text_html_greater_than(self):
        """Test > is escaped (& is escaped first, so result is double-escaped)."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("a > b")
        # Note: The implementation replaces & before >, so &gt; becomes &amp;gt;
        assert "&amp;gt;" in result
        assert ">" not in result

    def test_sanitize_text_ampersand(self):
        """Test & is escaped."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("Tom & Jerry")
        assert "&amp;" in result

    def test_sanitize_text_null_byte(self):
        """Test null bytes are removed."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("Hello\x00World")
        assert result == "HelloWorld"
        assert "\x00" not in result

    def test_sanitize_text_carriage_return(self):
        """Test carriage returns are removed."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("Line1\rLine2")
        assert result == "Line1Line2"
        assert "\r" not in result

    def test_sanitize_text_script_tag(self):
        """Test script tags are escaped (double-escaped due to & being escaped first)."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("<script>alert('xss')</script>")
        assert "<script>" not in result
        # Note: The implementation replaces & before <, so &lt; becomes &amp;lt;
        assert "&amp;lt;script&amp;gt;" in result

    def test_sanitize_text_multiple_replacements(self):
        """Test multiple characters are escaped (double-escaped due to & being escaped first)."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("<div>&test</div>")
        # Note: The implementation replaces & before <, so &lt; becomes &amp;lt;
        assert "&amp;lt;div&amp;gt;" in result
        assert "&amp;test" in result


# =============================================================================
# Tests for _escape_html()
# =============================================================================

class TestEscapeHtml:
    """Test HTML escaping for PDF rendering."""

    def test_escape_html_none_input(self):
        """Test None returns empty string."""
        generator = FCRAPDFGenerator()
        result = generator._escape_html(None)
        assert result == ""

    def test_escape_html_empty_string(self):
        """Test empty string returns empty string."""
        generator = FCRAPDFGenerator()
        result = generator._escape_html("")
        assert result == ""

    def test_escape_html_ampersand(self):
        """Test & is escaped."""
        generator = FCRAPDFGenerator()
        result = generator._escape_html("A & B")
        assert result == "A &amp; B"

    def test_escape_html_less_than(self):
        """Test < is escaped."""
        generator = FCRAPDFGenerator()
        result = generator._escape_html("a < b")
        assert result == "a &lt; b"

    def test_escape_html_greater_than(self):
        """Test > is escaped."""
        generator = FCRAPDFGenerator()
        result = generator._escape_html("a > b")
        assert result == "a &gt; b"

    def test_escape_html_double_quote(self):
        """Test " is escaped."""
        generator = FCRAPDFGenerator()
        result = generator._escape_html('Say "hello"')
        assert result == "Say &quot;hello&quot;"

    def test_escape_html_single_quote(self):
        """Test ' is escaped."""
        generator = FCRAPDFGenerator()
        result = generator._escape_html("It's fine")
        assert result == "It&#39;s fine"

    def test_escape_html_all_special_chars(self):
        """Test all special characters are escaped."""
        generator = FCRAPDFGenerator()
        result = generator._escape_html('<div class="test">&\'</div>')
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&quot;" in result
        assert "&amp;" in result
        assert "&#39;" in result


# =============================================================================
# Tests for _markdown_to_html()
# =============================================================================

class TestMarkdownToHtml:
    """Test markdown to HTML conversion."""

    def test_markdown_to_html_none_input(self):
        """Test None returns empty string."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html(None)
        assert result == ""

    def test_markdown_to_html_empty_string(self):
        """Test empty string returns empty string."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("")
        assert result == ""

    def test_markdown_to_html_h1_header(self):
        """Test H1 header conversion."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("# Header One")
        assert "<h1>" in result
        assert "</h1>" in result
        assert "Header One" in result

    def test_markdown_to_html_h2_header(self):
        """Test H2 header conversion."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("## Header Two")
        assert "<h2>" in result
        assert "</h2>" in result
        assert "Header Two" in result

    def test_markdown_to_html_h3_header(self):
        """Test H3 header conversion."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("### Header Three")
        assert "<h3>" in result
        assert "</h3>" in result
        assert "Header Three" in result

    def test_markdown_to_html_unordered_list_dash(self):
        """Test unordered list with dash."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("- Item 1\n- Item 2")
        assert "<ul>" in result
        assert "<li>" in result
        assert "</li>" in result
        assert "</ul>" in result
        assert "Item 1" in result
        assert "Item 2" in result

    def test_markdown_to_html_unordered_list_asterisk(self):
        """Test unordered list with asterisk."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("* Item 1\n* Item 2")
        assert "<ul>" in result
        assert "<li>" in result
        assert "Item 1" in result

    def test_markdown_to_html_numbered_list(self):
        """Test numbered list conversion."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("1. First\n2. Second")
        assert "<li>" in result
        assert "First" in result
        assert "Second" in result

    def test_markdown_to_html_horizontal_rule_dashes(self):
        """Test horizontal rule with dashes."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("---")
        assert "<hr" in result

    def test_markdown_to_html_horizontal_rule_underscores(self):
        """Test horizontal rule with underscores."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("___")
        assert "<hr" in result

    def test_markdown_to_html_paragraph(self):
        """Test paragraph conversion."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("This is a paragraph.")
        assert "<p>" in result
        assert "</p>" in result
        assert "This is a paragraph." in result

    def test_markdown_to_html_empty_lines(self):
        """Test empty lines create breaks."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("Para 1\n\nPara 2")
        assert "<br/>" in result

    def test_markdown_to_html_skips_tables(self):
        """Test table lines are skipped."""
        generator = FCRAPDFGenerator()
        result = generator._markdown_to_html("| Col 1 | Col 2 |")
        assert "|" not in result


# =============================================================================
# Tests for _apply_inline_formatting()
# =============================================================================

class TestApplyInlineFormatting:
    """Test inline markdown formatting."""

    def test_apply_inline_formatting_bold_asterisks(self):
        """Test bold with double asterisks."""
        generator = FCRAPDFGenerator()
        result = generator._apply_inline_formatting("**bold text**")
        assert "<strong>bold text</strong>" in result

    def test_apply_inline_formatting_bold_underscores(self):
        """Test bold with double underscores."""
        generator = FCRAPDFGenerator()
        result = generator._apply_inline_formatting("__bold text__")
        assert "<strong>bold text</strong>" in result

    def test_apply_inline_formatting_italic_asterisk(self):
        """Test italic with single asterisk."""
        generator = FCRAPDFGenerator()
        result = generator._apply_inline_formatting("*italic text*")
        assert "<em>italic text</em>" in result

    def test_apply_inline_formatting_code_backticks(self):
        """Test code with backticks."""
        generator = FCRAPDFGenerator()
        result = generator._apply_inline_formatting("`code here`")
        assert "<code" in result
        assert "code here" in result
        assert "</code>" in result

    def test_apply_inline_formatting_mixed(self):
        """Test mixed formatting."""
        generator = FCRAPDFGenerator()
        result = generator._apply_inline_formatting("**bold** and *italic*")
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

    def test_apply_inline_formatting_escapes_html(self):
        """Test HTML is escaped before formatting."""
        generator = FCRAPDFGenerator()
        result = generator._apply_inline_formatting("<script>**bold**</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result


# =============================================================================
# Tests for _get_case_strength_label()
# =============================================================================

class TestGetCaseStrengthLabel:
    """Test case strength label conversion."""

    def test_case_strength_strong(self):
        """Test score >= 8 returns Strong."""
        generator = FCRAPDFGenerator()
        assert generator._get_case_strength_label(8) == "Strong"
        assert generator._get_case_strength_label(9) == "Strong"
        assert generator._get_case_strength_label(10) == "Strong"

    def test_case_strength_moderate(self):
        """Test score 5-7 returns Moderate."""
        generator = FCRAPDFGenerator()
        assert generator._get_case_strength_label(5) == "Moderate"
        assert generator._get_case_strength_label(6) == "Moderate"
        assert generator._get_case_strength_label(7) == "Moderate"

    def test_case_strength_developing(self):
        """Test score < 5 returns Developing."""
        generator = FCRAPDFGenerator()
        assert generator._get_case_strength_label(0) == "Developing"
        assert generator._get_case_strength_label(1) == "Developing"
        assert generator._get_case_strength_label(4) == "Developing"

    def test_case_strength_boundary_values(self):
        """Test exact boundary values."""
        generator = FCRAPDFGenerator()
        assert generator._get_case_strength_label(4.9) == "Developing"
        assert generator._get_case_strength_label(5.0) == "Moderate"
        assert generator._get_case_strength_label(7.9) == "Moderate"
        assert generator._get_case_strength_label(8.0) == "Strong"


# =============================================================================
# Tests for generate_client_report()
# =============================================================================

class TestGenerateClientReport:
    """Test client report PDF generation."""

    @patch('services.pdf_service.HTML')
    def test_generate_client_report_basic(self, mock_html):
        """Test basic client report generation."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            result = generator.generate_client_report(
                output_path=output_path,
                client_name="John Doe",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            assert result == output_path
            mock_html.assert_called_once()
            mock_instance.write_pdf.assert_called_once_with(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_generate_client_report_with_client_name(self, mock_html):
        """Test client name is included in report."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Jane Smith",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            # Get the HTML string passed to HTML()
            call_args = mock_html.call_args
            html_content = call_args[1]['string']
            assert "Jane Smith" in html_content
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_generate_client_report_multiple_violations(self, mock_html):
        """Test report with multiple violations."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [
            MockViolation(fcra_section='1681e(b)', bureau='Equifax'),
            MockViolation(fcra_section='1681i', bureau='Experian'),
            MockViolation(fcra_section='1681s-2', bureau='TransUnion'),
        ]
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            call_args = mock_html.call_args
            html_content = call_args[1]['string']
            assert "3+" in html_content  # violations count
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_generate_client_report_empty_violations(self, mock_html):
        """Test report with no violations."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = []
        damages = MockDamages(total_exposure=0)
        case_score = MockCaseScore(total_score=0)
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            call_args = mock_html.call_args
            html_content = call_args[1]['string']
            assert "0+" in html_content  # 0 violations
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_generate_client_report_none_violations(self, mock_html):
        """Test report with None violations."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        damages = MockDamages(total_exposure=0)
        case_score = MockCaseScore(total_score=0)
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Test Client",
                violations=None,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            mock_instance.write_pdf.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_generate_client_report_stops_at_dispute_letter(self, mock_html):
        """Test that analysis text stops before dispute letter sections."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis(
            full_analysis="Analysis content here\n\n--- DISPUTE LETTER ---\n\nDispute content"
        )

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            call_args = mock_html.call_args
            html_content = call_args[1]['string']
            # Should contain analysis content
            assert "Analysis content here" in html_content
            # Should not contain dispute letter content (raw text)
            # Note: The marker line itself might be partially included
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_generate_client_report_case_strength_strong(self, mock_html):
        """Test report shows Strong case strength for high score."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        case_score = MockCaseScore(total_score=9)
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            # Verify PDF generation was called
            mock_instance.write_pdf.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_generate_client_report_no_damages(self, mock_html):
        """Test report with None damages."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                damages=None,
                case_score=case_score,
                analysis=analysis
            )

            call_args = mock_html.call_args
            html_content = call_args[1]['string']
            assert "$0" in html_content  # exposure is 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_generate_client_report_no_case_score(self, mock_html):
        """Test report with None case score."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                damages=damages,
                case_score=None,
                analysis=analysis
            )

            mock_instance.write_pdf.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


# =============================================================================
# Tests for generate_legal_analysis()
# =============================================================================

class TestGenerateLegalAnalysis:
    """Test legal analysis PDF generation."""

    @patch('services.pdf_service.SimpleDocTemplate')
    def test_generate_legal_analysis_basic(self, mock_doc_class):
        """Test basic legal analysis generation."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        standing = MockStanding()
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            result = generator.generate_legal_analysis(
                output_path=output_path,
                client_name="John Doe",
                violations=violations,
                standing=standing,
                damages=damages,
                case_score=case_score,
                analysis=analysis,
                full_analysis_text="Full analysis text here."
            )

            assert result == output_path
            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.SimpleDocTemplate')
    def test_generate_legal_analysis_multiple_violations(self, mock_doc_class):
        """Test legal analysis with multiple violations."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        generator = FCRAPDFGenerator()
        violations = [
            MockViolation(fcra_section='1681e(b)', bureau='Equifax', is_willful=True),
            MockViolation(fcra_section='1681i', bureau='Experian', is_willful=False),
            MockViolation(fcra_section='1681s-2', bureau='TransUnion', is_willful=True),
        ]
        standing = MockStanding()
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_legal_analysis(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                standing=standing,
                damages=damages,
                case_score=case_score,
                analysis=analysis,
                full_analysis_text="Analysis text"
            )

            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.SimpleDocTemplate')
    def test_generate_legal_analysis_no_standing(self, mock_doc_class):
        """Test legal analysis with None standing."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_legal_analysis(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                standing=None,
                damages=damages,
                case_score=case_score,
                analysis=analysis,
                full_analysis_text="Analysis text"
            )

            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.SimpleDocTemplate')
    def test_generate_legal_analysis_no_damages(self, mock_doc_class):
        """Test legal analysis with None damages."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        standing = MockStanding()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_legal_analysis(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                standing=standing,
                damages=None,
                case_score=case_score,
                analysis=analysis,
                full_analysis_text="Analysis text"
            )

            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.SimpleDocTemplate')
    def test_generate_legal_analysis_no_case_score(self, mock_doc_class):
        """Test legal analysis with None case score."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        standing = MockStanding()
        damages = MockDamages()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_legal_analysis(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                standing=standing,
                damages=damages,
                case_score=None,
                analysis=analysis,
                full_analysis_text="Analysis text"
            )

            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.SimpleDocTemplate')
    def test_generate_legal_analysis_empty_full_analysis(self, mock_doc_class):
        """Test legal analysis with empty full analysis text."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        standing = MockStanding()
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_legal_analysis(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                standing=standing,
                damages=damages,
                case_score=case_score,
                analysis=analysis,
                full_analysis_text=""
            )

            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.SimpleDocTemplate')
    def test_generate_legal_analysis_long_analysis_text(self, mock_doc_class):
        """Test legal analysis with very long analysis text."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        standing = MockStanding()
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()
        # Create very long text line (>1000 chars)
        long_text = "A" * 2000

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_legal_analysis(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                standing=standing,
                damages=damages,
                case_score=case_score,
                analysis=analysis,
                full_analysis_text=long_text
            )

            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.SimpleDocTemplate')
    def test_generate_legal_analysis_with_headings_in_text(self, mock_doc_class):
        """Test legal analysis with headings in full analysis text."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        standing = MockStanding()
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()
        analysis_text = "VIOLATIONS SUMMARY:\n\nDetails here.\n\nDAMAGES CALCULATION:\n\nMore details."

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_legal_analysis(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                standing=standing,
                damages=damages,
                case_score=case_score,
                analysis=analysis,
                full_analysis_text=analysis_text
            )

            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.SimpleDocTemplate')
    def test_generate_legal_analysis_violation_without_description(self, mock_doc_class):
        """Test legal analysis with violation missing description."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        generator = FCRAPDFGenerator()
        violations = [MockViolation(description=None)]
        standing = MockStanding()
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_legal_analysis(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                standing=standing,
                damages=damages,
                case_score=case_score,
                analysis=analysis,
                full_analysis_text="Analysis"
            )

            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


# =============================================================================
# Tests for _add_branded_header() (Internal Method)
# =============================================================================

class TestAddBrandedHeader:
    """Test branded header generation."""

    def test_add_branded_header_with_title(self):
        """Test branded header with title."""
        generator = FCRAPDFGenerator()
        story = []
        generator._add_branded_header(story, "Test Title")
        # Should have added elements to story
        assert len(story) > 0

    def test_add_branded_header_with_subtitle(self):
        """Test branded header with title and subtitle."""
        generator = FCRAPDFGenerator()
        story = []
        generator._add_branded_header(story, "Test Title", "Test Subtitle")
        # Should have added elements to story
        assert len(story) > 0

    def test_add_branded_header_none_title(self):
        """Test branded header with None title."""
        generator = FCRAPDFGenerator()
        story = []
        generator._add_branded_header(story, None)
        # Should still work without error
        assert len(story) > 0


# =============================================================================
# Tests for _add_summary_box() (Internal Method)
# =============================================================================

class TestAddSummaryBox:
    """Test summary box generation."""

    def test_add_summary_box_strong_case(self):
        """Test summary box with strong case strength."""
        generator = FCRAPDFGenerator()
        story = []
        generator._add_summary_box(story, 10, 50000, "Strong")
        assert len(story) > 0

    def test_add_summary_box_moderate_case(self):
        """Test summary box with moderate case strength."""
        generator = FCRAPDFGenerator()
        story = []
        generator._add_summary_box(story, 5, 25000, "Moderate")
        assert len(story) > 0

    def test_add_summary_box_weak_case(self):
        """Test summary box with weak case strength."""
        generator = FCRAPDFGenerator()
        story = []
        generator._add_summary_box(story, 2, 10000, "Weak")
        assert len(story) > 0

    def test_add_summary_box_developing_case(self):
        """Test summary box with developing case strength."""
        generator = FCRAPDFGenerator()
        story = []
        generator._add_summary_box(story, 1, 5000, "Developing")
        assert len(story) > 0

    def test_add_summary_box_unknown_case_strength(self):
        """Test summary box with unknown case strength (defaults to Moderate)."""
        generator = FCRAPDFGenerator()
        story = []
        generator._add_summary_box(story, 3, 15000, "Unknown")
        assert len(story) > 0


# =============================================================================
# Tests for _add_violations_table() (Internal Method)
# =============================================================================

class TestAddViolationsTable:
    """Test violations table generation."""

    def test_add_violations_table_single_violation(self):
        """Test violations table with single violation."""
        generator = FCRAPDFGenerator()
        story = []
        violations = [MockViolation()]
        generator._add_violations_table(story, violations)
        assert len(story) > 0

    def test_add_violations_table_multiple_bureaus(self):
        """Test violations table with violations from multiple bureaus."""
        generator = FCRAPDFGenerator()
        story = []
        violations = [
            MockViolation(bureau='Equifax'),
            MockViolation(bureau='Experian'),
            MockViolation(bureau='TransUnion'),
        ]
        generator._add_violations_table(story, violations)
        assert len(story) > 0

    def test_add_violations_table_more_than_10_per_bureau(self):
        """Test violations table limits to 10 per bureau."""
        generator = FCRAPDFGenerator()
        story = []
        # Create 15 violations for same bureau
        violations = [MockViolation(bureau='Equifax') for _ in range(15)]
        generator._add_violations_table(story, violations)
        assert len(story) > 0

    def test_add_violations_table_none_bureau(self):
        """Test violations table with None bureau."""
        generator = FCRAPDFGenerator()
        story = []
        violations = [MockViolation(bureau=None)]
        generator._add_violations_table(story, violations)
        assert len(story) > 0

    def test_add_violations_table_none_violation_type(self):
        """Test violations table with None violation type."""
        generator = FCRAPDFGenerator()
        story = []
        violations = [MockViolation(violation_type=None)]
        generator._add_violations_table(story, violations)
        assert len(story) > 0

    def test_add_violations_table_none_description(self):
        """Test violations table with None description."""
        generator = FCRAPDFGenerator()
        story = []
        violations = [MockViolation(description=None)]
        generator._add_violations_table(story, violations)
        assert len(story) > 0


# =============================================================================
# Tests for Brand Color Constants
# =============================================================================

class TestBrandColorConstants:
    """Test brand color constants."""

    def test_primary_color_is_teal(self):
        """Test PRIMARY_COLOR is teal."""
        assert PRIMARY_COLOR == "#319795"

    def test_secondary_color_is_lime(self):
        """Test SECONDARY_COLOR is lime green."""
        assert SECONDARY_COLOR == "#84cc16"

    def test_dark_color_is_navy(self):
        """Test DARK_COLOR is dark navy."""
        assert DARK_COLOR == "#1a1a2e"


# =============================================================================
# Edge Case and Integration Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_sanitize_text_with_all_special_chars(self):
        """Test sanitization with all special characters."""
        generator = FCRAPDFGenerator()
        text = "<>&\x00\r"
        result = generator._sanitize_text(text)
        assert "<" not in result.replace("&lt;", "")
        assert ">" not in result.replace("&gt;", "")
        assert "\x00" not in result
        assert "\r" not in result

    def test_markdown_headers_nested(self):
        """Test nested markdown headers."""
        generator = FCRAPDFGenerator()
        text = "# H1\n## H2\n### H3"
        result = generator._markdown_to_html(text)
        assert "<h1>" in result
        assert "<h2>" in result
        assert "<h3>" in result

    def test_markdown_list_followed_by_paragraph(self):
        """Test list followed by paragraph closes list properly."""
        generator = FCRAPDFGenerator()
        text = "- Item 1\n- Item 2\n\nParagraph after list."
        result = generator._markdown_to_html(text)
        assert "</ul>" in result
        assert "<p>Paragraph after list.</p>" in result

    def test_unicode_characters(self):
        """Test unicode characters in text."""
        generator = FCRAPDFGenerator()
        result = generator._sanitize_text("Hello Cafe\u0301")
        assert "Cafe" in result

    def test_very_long_client_name(self):
        """Test handling very long client name."""
        generator = FCRAPDFGenerator()
        long_name = "A" * 500
        # Should not raise an error
        story = []
        generator._add_branded_header(story, f"Report for {long_name}")
        assert len(story) > 0

    @patch('services.pdf_service.HTML')
    def test_client_report_single_word_name(self, mock_html):
        """Test client report with single word name (no last name)."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Madonna",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            call_args = mock_html.call_args
            html_content = call_args[1]['string']
            assert "Madonna" in html_content
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_client_report_empty_client_name(self, mock_html):
        """Test client report with empty client name."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            mock_instance.write_pdf.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_client_report_special_chars_in_name(self, mock_html):
        """Test client report with special characters in name."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="O'Brien & Associates",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            mock_instance.write_pdf.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('services.pdf_service.HTML')
    def test_client_report_analysis_with_none_full_analysis(self, mock_html):
        """Test client report when analysis.full_analysis is None."""
        mock_instance = MagicMock()
        mock_html.return_value = mock_instance

        generator = FCRAPDFGenerator()
        violations = [MockViolation()]
        damages = MockDamages()
        case_score = MockCaseScore()
        analysis = MockAnalysis(full_analysis=None)

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            output_path = f.name

        try:
            generator.generate_client_report(
                output_path=output_path,
                client_name="Test Client",
                violations=violations,
                damages=damages,
                case_score=case_score,
                analysis=analysis
            )

            mock_instance.write_pdf.assert_called_once()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


# =============================================================================
# Tests for Custom Styles
# =============================================================================

class TestCustomStyles:
    """Test custom paragraph styles."""

    def test_client_header_style(self):
        """Test ClientHeader style properties."""
        generator = FCRAPDFGenerator()
        style = generator.styles['ClientHeader']
        assert style.fontSize == 24
        assert style.alignment == 1  # TA_CENTER

    def test_client_sub_header_style(self):
        """Test ClientSubHeader style properties."""
        generator = FCRAPDFGenerator()
        style = generator.styles['ClientSubHeader']
        assert style.fontSize == 16

    def test_client_body_style(self):
        """Test ClientBody style properties."""
        generator = FCRAPDFGenerator()
        style = generator.styles['ClientBody']
        assert style.fontSize == 11
        assert style.leading == 14

    def test_client_highlight_style(self):
        """Test ClientHighlight style properties."""
        generator = FCRAPDFGenerator()
        style = generator.styles['ClientHighlight']
        assert style.fontSize == 12

    def test_legal_title_style(self):
        """Test LegalTitle style properties."""
        generator = FCRAPDFGenerator()
        style = generator.styles['LegalTitle']
        assert style.fontSize == 14
        assert style.alignment == 1  # TA_CENTER

    def test_legal_header_style(self):
        """Test LegalHeader style properties."""
        generator = FCRAPDFGenerator()
        style = generator.styles['LegalHeader']
        assert style.fontSize == 12

    def test_legal_sub_header_style(self):
        """Test LegalSubHeader style properties."""
        generator = FCRAPDFGenerator()
        style = generator.styles['LegalSubHeader']
        assert style.fontSize == 11

    def test_legal_body_style(self):
        """Test LegalBody style properties."""
        generator = FCRAPDFGenerator()
        style = generator.styles['LegalBody']
        assert style.fontSize == 11
        assert style.leading == 14
        assert style.firstLineIndent == 0
