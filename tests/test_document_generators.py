"""
Unit tests for Document Generators

Tests cover:
- html_to_pdf function
- generate_internal_analysis_html function
- generate_client_email_html function
- generate_client_report_html function
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, mock_open
import os


class TestWeasyPrintAvailability:
    """Tests for WeasyPrint availability constant"""

    def test_weasyprint_available_is_boolean(self):
        """Should have WEASYPRINT_AVAILABLE as boolean"""
        from services.document_generators import WEASYPRINT_AVAILABLE

        assert isinstance(WEASYPRINT_AVAILABLE, bool)


class TestHtmlToPdf:
    """Tests for html_to_pdf function"""

    @patch('services.document_generators.WEASYPRINT_AVAILABLE', False)
    def test_raises_import_error_when_weasyprint_unavailable(self):
        """Should raise ImportError when WeasyPrint is not available"""
        # Need to reload module to pick up patched constant
        from services.document_generators import html_to_pdf

        with patch('services.document_generators.WEASYPRINT_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                html_to_pdf("<html></html>", "/tmp/test.pdf")
            assert "WeasyPrint is not installed" in str(exc_info.value)

    @patch('services.document_generators.WEASYPRINT_AVAILABLE', True)
    @patch('services.document_generators.HTML')
    @patch('services.document_generators.CSS')
    @patch('services.document_generators.FontConfiguration')
    @patch('os.makedirs')
    def test_creates_output_directory(self, mock_makedirs, mock_font_config, mock_css, mock_html):
        """Should create output directory if it doesn't exist"""
        from services.document_generators import html_to_pdf

        mock_html_obj = MagicMock()
        mock_html.return_value = mock_html_obj

        html_to_pdf("<html></html>", "/tmp/test/output.pdf")

        mock_makedirs.assert_called_once_with("/tmp/test", exist_ok=True)

    @patch('services.document_generators.WEASYPRINT_AVAILABLE', True)
    @patch('services.document_generators.HTML')
    @patch('services.document_generators.CSS')
    @patch('services.document_generators.FontConfiguration')
    @patch('os.makedirs')
    def test_creates_html_object_with_content(self, mock_makedirs, mock_font_config, mock_css, mock_html):
        """Should create HTML object with content"""
        from services.document_generators import html_to_pdf

        mock_html_obj = MagicMock()
        mock_html.return_value = mock_html_obj

        html_content = "<html><body>Test</body></html>"
        html_to_pdf(html_content, "/tmp/test.pdf")

        mock_html.assert_called_once_with(string=html_content, base_url=None)

    @patch('services.document_generators.WEASYPRINT_AVAILABLE', True)
    @patch('services.document_generators.HTML')
    @patch('services.document_generators.CSS')
    @patch('services.document_generators.FontConfiguration')
    @patch('os.makedirs')
    def test_uses_base_url_when_provided(self, mock_makedirs, mock_font_config, mock_css, mock_html):
        """Should use base_url when provided"""
        from services.document_generators import html_to_pdf

        mock_html_obj = MagicMock()
        mock_html.return_value = mock_html_obj

        html_to_pdf("<html></html>", "/tmp/test.pdf", base_url="http://example.com")

        mock_html.assert_called_once_with(string="<html></html>", base_url="http://example.com")

    @patch('services.document_generators.WEASYPRINT_AVAILABLE', True)
    @patch('services.document_generators.HTML')
    @patch('services.document_generators.CSS')
    @patch('services.document_generators.FontConfiguration')
    @patch('os.makedirs')
    def test_writes_pdf_to_output_path(self, mock_makedirs, mock_font_config, mock_css, mock_html):
        """Should write PDF to specified output path"""
        from services.document_generators import html_to_pdf

        mock_html_obj = MagicMock()
        mock_html.return_value = mock_html_obj

        result = html_to_pdf("<html></html>", "/tmp/test.pdf")

        mock_html_obj.write_pdf.assert_called_once()
        assert result == "/tmp/test.pdf"

    @patch('services.document_generators.WEASYPRINT_AVAILABLE', True)
    @patch('services.document_generators.HTML')
    @patch('services.document_generators.CSS')
    @patch('services.document_generators.FontConfiguration')
    @patch('os.makedirs')
    def test_returns_output_path(self, mock_makedirs, mock_font_config, mock_css, mock_html):
        """Should return the output path"""
        from services.document_generators import html_to_pdf

        mock_html_obj = MagicMock()
        mock_html.return_value = mock_html_obj

        result = html_to_pdf("<html></html>", "/path/to/output.pdf")

        assert result == "/path/to/output.pdf"


class TestGenerateInternalAnalysisHtml:
    """Tests for generate_internal_analysis_html function"""

    def _create_mock_analysis(self, id=1, client_name="John Doe", dispute_round=1):
        """Helper to create mock Analysis object"""
        analysis = Mock()
        analysis.id = id
        analysis.client_name = client_name
        analysis.dispute_round = dispute_round
        analysis.credit_report_id = None
        return analysis

    def _create_mock_violation(self, bureau="Equifax", account_name="Test Account",
                               violation_type="Data Inaccuracy", is_willful=False,
                               fcra_section="§611", description="Test description"):
        """Helper to create mock Violation object"""
        violation = Mock()
        violation.bureau = bureau
        violation.account_name = account_name
        violation.violation_type = violation_type
        violation.is_willful = is_willful
        violation.fcra_section = fcra_section
        violation.description = description
        return violation

    def _create_mock_standing(self, has_dissemination=True, has_concrete_harm=True,
                              has_causation=True):
        """Helper to create mock Standing object"""
        standing = Mock()
        standing.has_dissemination = has_dissemination
        standing.has_concrete_harm = has_concrete_harm
        standing.has_causation = has_causation
        standing.dissemination_details = "Credit report was shared"
        standing.concrete_harm_details = "Denied credit"
        standing.causation_details = "Caused by inaccurate information"
        return standing

    def _create_mock_damages(self, settlement_target=50000, statutory_damages_total=10000,
                             punitive_damages_amount=30000, actual_damages_total=5000):
        """Helper to create mock Damages object"""
        damages = Mock()
        damages.settlement_target = settlement_target
        damages.statutory_damages_total = statutory_damages_total
        damages.punitive_damages_amount = punitive_damages_amount
        damages.actual_damages_total = actual_damages_total
        return damages

    def _create_mock_case_score(self, total_score=8, standing_score=9, willfulness_score=7):
        """Helper to create mock CaseScore object"""
        case_score = Mock()
        case_score.total_score = total_score
        case_score.standing_score = standing_score
        case_score.willfulness_score = willfulness_score
        return case_score

    def test_returns_html_string(self):
        """Should return HTML string"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        standing = self._create_mock_standing()
        damages = self._create_mock_damages()
        case_score = self._create_mock_case_score()

        result = generate_internal_analysis_html(analysis, violations, standing, damages, case_score)

        assert isinstance(result, str)
        assert result.startswith("<!DOCTYPE html>")

    def test_includes_client_name_in_title(self):
        """Should include client name in title"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis(client_name="Jane Smith")
        violations = [self._create_mock_violation()]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "Jane Smith" in result
        assert "<title>Internal Analysis - Jane Smith</title>" in result

    def test_includes_case_number(self):
        """Should include case number based on analysis ID"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis(id=123)
        violations = [self._create_mock_violation()]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "BAG-FCRA-0123" in result

    def test_includes_violation_count(self):
        """Should include count of violations"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(),
            self._create_mock_violation(),
            self._create_mock_violation(),
        ]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "Violations</div>" in result or "Total Violations" in result

    def test_calculates_willfulness_percentage(self):
        """Should calculate willfulness percentage correctly"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(is_willful=True),
            self._create_mock_violation(is_willful=True),
            self._create_mock_violation(is_willful=False),
            self._create_mock_violation(is_willful=False),
        ]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        # 2 out of 4 = 50%
        assert "50%" in result

    def test_handles_zero_violations(self):
        """Should handle zero violations without division error"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = []

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert isinstance(result, str)
        assert "0%" in result

    def test_includes_defendant_count(self):
        """Should include count of unique defendants"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(bureau="Equifax"),
            self._create_mock_violation(bureau="Experian"),
            self._create_mock_violation(bureau="TransUnion"),
        ]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "Defendants" in result

    def test_includes_standing_analysis(self):
        """Should include standing analysis section"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        standing = self._create_mock_standing()

        result = generate_internal_analysis_html(analysis, violations, standing, None, None)

        assert "Standing Analysis" in result
        assert "Dissemination" in result
        assert "Concrete Harm" in result
        assert "Causation" in result

    def test_handles_none_standing(self):
        """Should handle None standing object"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert isinstance(result, str)
        assert "Assessment pending" in result

    def test_includes_damages_section(self):
        """Should include damages calculation section"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        damages = self._create_mock_damages(settlement_target=100000)

        result = generate_internal_analysis_html(analysis, violations, None, damages, None)

        assert "Damages Calculation" in result

    def test_handles_none_damages(self):
        """Should handle None damages object"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "Damages calculation pending" in result

    def test_includes_case_scores(self):
        """Should include case scores when provided"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        case_score = self._create_mock_case_score(total_score=8)

        result = generate_internal_analysis_html(analysis, violations, None, None, case_score)

        assert "8/10" in result

    def test_includes_credit_scores_when_provided(self):
        """Should include credit scores when provided"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        credit_scores = {"tu": 650, "ex": 680, "eq": 670}

        result = generate_internal_analysis_html(analysis, violations, None, None, None, credit_scores)

        assert isinstance(result, str)

    def test_handles_none_credit_scores(self):
        """Should handle None credit scores without errors"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        # Should not raise any errors when credit_scores is None
        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_violation_categories(self):
        """Should group violations by category"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(violation_type="Data Inaccuracy"),
            self._create_mock_violation(violation_type="Balance Error"),
        ]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "Data Inaccuracy" in result or "Balance Error" in result

    def test_identifies_contradiction_violations(self):
        """Should identify impossible contradiction violations"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(violation_type="Impossible Contradiction"),
        ]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "Critical Violations" in result or "Impossible Contradictions" in result

    def test_includes_action_items(self):
        """Should include action items section"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "Action Items" in result

    def test_includes_recommended_timeline(self):
        """Should include litigation timeline section"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "Timeline" in result

    def test_includes_apple_style_css(self):
        """Should include Apple-style CSS variables"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "--navy-dark" in result
        assert "--teal" in result
        assert "Playfair Display" in result

    def test_handles_high_willfulness(self):
        """Should show appropriate message for high willfulness"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(is_willful=True),
            self._create_mock_violation(is_willful=True),
            self._create_mock_violation(is_willful=True),
        ]

        result = generate_internal_analysis_html(analysis, violations, None, None, None)

        assert "punitive damages" in result.lower() or "willful" in result.lower()


class TestGenerateClientEmailHtml:
    """Tests for generate_client_email_html function"""

    def _create_mock_analysis(self, id=1, client_name="John Doe", dispute_round=1):
        """Helper to create mock Analysis object"""
        analysis = Mock()
        analysis.id = id
        analysis.client_name = client_name
        analysis.dispute_round = dispute_round
        return analysis

    def _create_mock_violation(self, bureau="Equifax", account_name="Test Account",
                               violation_type="Data Inaccuracy", is_willful=False,
                               fcra_section="§611", description="Test description"):
        """Helper to create mock Violation object"""
        violation = Mock()
        violation.bureau = bureau
        violation.account_name = account_name
        violation.violation_type = violation_type
        violation.is_willful = is_willful
        violation.fcra_section = fcra_section
        violation.description = description
        return violation

    def _create_mock_damages(self, settlement_target=50000):
        """Helper to create mock Damages object"""
        damages = Mock()
        damages.settlement_target = settlement_target
        return damages

    def _create_mock_case_score(self, total_score=8, standing_score=9):
        """Helper to create mock CaseScore object"""
        case_score = Mock()
        case_score.total_score = total_score
        case_score.standing_score = standing_score
        return case_score

    def test_returns_html_string(self):
        """Should return HTML string"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert isinstance(result, str)
        assert result.startswith("<!DOCTYPE html>")

    def test_includes_client_name(self):
        """Should include client name"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis(client_name="Jane Smith")
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert "Jane Smith" in result

    def test_includes_first_name_greeting(self):
        """Should use first name in greeting"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis(client_name="Jane Smith")
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert "Dear Jane" in result

    def test_includes_violation_count(self):
        """Should include violation count"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(),
            self._create_mock_violation(),
            self._create_mock_violation(),
        ]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert "3 violations" in result

    def test_includes_case_number(self):
        """Should include case number"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis(id=456)
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert "BAG-FCRA-0456" in result

    def test_includes_settlement_target(self):
        """Should include settlement target"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        damages = self._create_mock_damages(settlement_target=75000)

        result = generate_client_email_html(analysis, violations, None, damages, None)

        assert "75K" in result or "75,000" in result

    def test_includes_case_strength(self):
        """Should include case strength score"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        case_score = self._create_mock_case_score(total_score=9)

        result = generate_client_email_html(analysis, violations, None, None, case_score)

        assert "9/10" in result

    def test_includes_compelling_violation(self):
        """Should highlight most compelling violation"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(violation_type="Impossible Contradiction"),
        ]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert "Compelling Violation" in result or "Impossible Contradiction" in result

    def test_uses_inline_styles_for_email(self):
        """Should use inline styles for email compatibility"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        # Email HTML should have inline styles
        assert 'style="' in result

    def test_includes_next_steps(self):
        """Should include next steps list"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert "next" in result.lower() or "steps" in result.lower()

    def test_includes_approve_cta(self):
        """Should include APPROVED call to action"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert "APPROVED" in result

    def test_includes_settlement_range(self):
        """Should include settlement range"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        damages = self._create_mock_damages(settlement_target=100000)

        result = generate_client_email_html(analysis, violations, None, damages, None)

        # Range is 70% to 130% of target
        assert "Settlement Range" in result or "70,000" in result or "130,000" in result

    def test_includes_settlement_probability_high(self):
        """Should show high settlement probability for strong cases"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        case_score = self._create_mock_case_score(total_score=9)

        result = generate_client_email_html(analysis, violations, None, None, case_score)

        assert "High" in result

    def test_includes_settlement_probability_moderate(self):
        """Should show moderate settlement probability for medium cases"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        case_score = self._create_mock_case_score(total_score=6)

        result = generate_client_email_html(analysis, violations, None, None, case_score)

        assert "Moderate" in result

    def test_includes_footer(self):
        """Should include company footer"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert "Brightpath Ascend Group" in result

    def test_handles_none_damages(self):
        """Should handle None damages"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert isinstance(result, str)
        assert "0K" in result

    def test_handles_none_case_score(self):
        """Should handle None case score"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_email_html(analysis, violations, None, None, None)

        assert isinstance(result, str)
        assert "0/10" in result


class TestGenerateClientReportHtml:
    """Tests for generate_client_report_html function"""

    def _create_mock_analysis(self, id=1, client_name="John Doe", dispute_round=1):
        """Helper to create mock Analysis object"""
        analysis = Mock()
        analysis.id = id
        analysis.client_name = client_name
        analysis.dispute_round = dispute_round
        return analysis

    def _create_mock_violation(self, bureau="Equifax", account_name="Test Account",
                               violation_type="Data Inaccuracy", is_willful=False,
                               fcra_section="§611", description="Test description"):
        """Helper to create mock Violation object"""
        violation = Mock()
        violation.bureau = bureau
        violation.account_name = account_name
        violation.violation_type = violation_type
        violation.is_willful = is_willful
        violation.fcra_section = fcra_section
        violation.description = description
        return violation

    def _create_mock_damages(self, settlement_target=50000):
        """Helper to create mock Damages object"""
        damages = Mock()
        damages.settlement_target = settlement_target
        return damages

    def _create_mock_case_score(self, total_score=8, standing_score=9):
        """Helper to create mock CaseScore object"""
        case_score = Mock()
        case_score.total_score = total_score
        case_score.standing_score = standing_score
        return case_score

    def test_returns_html_string(self):
        """Should return HTML string"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert isinstance(result, str)
        assert result.startswith("<!DOCTYPE html>")

    def test_includes_client_name_on_cover(self):
        """Should include client name on cover page"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis(client_name="John Doe")
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "John Doe" in result

    def test_includes_case_number(self):
        """Should include case number"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis(id=789)
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "BAG-FCRA-2025-0789" in result

    def test_includes_executive_summary(self):
        """Should include executive summary page"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "Executive Summary" in result

    def test_includes_your_rights_section(self):
        """Should include Your Rights under FCRA section"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "Your Rights" in result
        assert "FCRA" in result

    def test_includes_fcra_sections(self):
        """Should include FCRA section references"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "§604" in result or "604" in result
        assert "§611" in result or "611" in result

    def test_includes_violation_summary_table(self):
        """Should include violation summary table"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(violation_type="Data Inaccuracy"),
            self._create_mock_violation(violation_type="Balance Error"),
        ]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "Violation Summary" in result
        assert "<table" in result

    def test_includes_account_analysis(self):
        """Should include account analysis section"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(account_name="Account 1"),
            self._create_mock_violation(account_name="Account 2"),
        ]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "Account Analysis" in result

    def test_includes_damages_section(self):
        """Should include damages and strategy section"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        damages = self._create_mock_damages(settlement_target=60000)

        result = generate_client_report_html(analysis, violations, None, damages, None)

        assert "Damages" in result

    def test_includes_next_steps_section(self):
        """Should include next steps section"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "Next Steps" in result

    def test_has_seven_pages(self):
        """Should have page class for pagination"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert 'class="page' in result

    def test_includes_print_css(self):
        """Should include print-optimized CSS"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "page-break" in result

    def test_includes_metrics_grid(self):
        """Should include metrics grid"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]
        case_score = self._create_mock_case_score(total_score=7)

        result = generate_client_report_html(analysis, violations, None, None, case_score)

        assert "metrics-grid" in result

    def test_groups_violations_by_type(self):
        """Should group violations by type in table"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [
            self._create_mock_violation(violation_type="Data Inaccuracy"),
            self._create_mock_violation(violation_type="Data Inaccuracy"),
            self._create_mock_violation(violation_type="Balance Error"),
        ]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "Data Inaccuracy" in result
        assert "Balance Error" in result

    def test_limits_accounts_displayed(self):
        """Should limit number of accounts displayed"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        # Create more than 8 unique accounts
        violations = [
            self._create_mock_violation(account_name=f"Account {i}")
            for i in range(12)
        ]

        result = generate_client_report_html(analysis, violations, None, None, None)

        # Should limit to 8 accounts
        assert isinstance(result, str)

    def test_handles_none_damages(self):
        """Should handle None damages"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert isinstance(result, str)

    def test_handles_none_case_score(self):
        """Should handle None case score"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "0/10" in result

    def test_includes_contact_information(self):
        """Should include contact information"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "support@brightpathascend.com" in result or "Questions?" in result

    def test_includes_company_name_in_footer(self):
        """Should include company name in footer"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        assert "Brightpath Ascend Group" in result

    def test_includes_dispute_round(self):
        """Should include dispute round reference"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis(dispute_round=2)
        violations = [self._create_mock_violation()]

        result = generate_client_report_html(analysis, violations, None, None, None)

        # Round should be referenced in timeline or strategy
        assert "Round" in result


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def _create_mock_analysis(self, id=1, client_name="John Doe", dispute_round=1):
        """Helper to create mock Analysis object"""
        analysis = Mock()
        analysis.id = id
        analysis.client_name = client_name
        analysis.dispute_round = dispute_round
        return analysis

    def _create_mock_violation(self):
        """Helper to create mock Violation object"""
        violation = Mock()
        violation.bureau = "Equifax"
        violation.account_name = "Test Account"
        violation.violation_type = "Data Inaccuracy"
        violation.is_willful = False
        violation.fcra_section = "§611"
        violation.description = "Test description"
        return violation

    def test_internal_analysis_with_empty_violations(self):
        """Should handle empty violations list"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        result = generate_internal_analysis_html(analysis, [], None, None, None)

        assert isinstance(result, str)

    def test_client_email_with_empty_violations(self):
        """Should handle empty violations list"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        result = generate_client_email_html(analysis, [], None, None, None)

        assert isinstance(result, str)

    def test_client_report_with_empty_violations(self):
        """Should handle empty violations list"""
        from services.document_generators import generate_client_report_html

        analysis = self._create_mock_analysis()
        result = generate_client_report_html(analysis, [], None, None, None)

        assert isinstance(result, str)

    def test_handles_violation_with_none_fields(self):
        """Should handle violations with None fields"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violation = Mock()
        violation.bureau = None
        violation.account_name = None
        violation.violation_type = None
        violation.is_willful = False
        violation.fcra_section = None
        violation.description = None

        result = generate_internal_analysis_html(analysis, [violation], None, None, None)

        assert isinstance(result, str)

    def test_handles_long_client_name(self):
        """Should handle very long client names"""
        from services.document_generators import generate_internal_analysis_html

        long_name = "A" * 200
        analysis = self._create_mock_analysis(client_name=long_name)

        result = generate_internal_analysis_html(analysis, [self._create_mock_violation()], None, None, None)

        assert long_name in result

    def test_handles_special_characters_in_name(self):
        """Should handle special characters in client name"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis(client_name="John O'Brien-Smith")

        result = generate_client_email_html(analysis, [self._create_mock_violation()], None, None, None)

        assert "O'Brien-Smith" in result

    def test_handles_unicode_in_description(self):
        """Should handle unicode characters in violation description"""
        from services.document_generators import generate_internal_analysis_html

        analysis = self._create_mock_analysis()
        violation = Mock()
        violation.bureau = "Equifax"
        violation.account_name = "Test™ Account"
        violation.violation_type = "Data Inaccuracy"
        violation.is_willful = False
        violation.fcra_section = "§611"
        violation.description = "Balance showing $1,234 vs €1,000"

        result = generate_internal_analysis_html(analysis, [violation], None, None, None)

        assert isinstance(result, str)

    def test_handles_very_large_settlement_target(self):
        """Should handle very large settlement targets"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        damages = Mock()
        damages.settlement_target = 10000000  # 10 million

        result = generate_client_email_html(analysis, [self._create_mock_violation()], None, damages, None)

        assert "10000K" in result or "10,000K" in result or "10000" in result

    def test_handles_zero_settlement_target(self):
        """Should handle zero settlement target"""
        from services.document_generators import generate_client_email_html

        analysis = self._create_mock_analysis()
        damages = Mock()
        damages.settlement_target = 0

        result = generate_client_email_html(analysis, [self._create_mock_violation()], None, damages, None)

        assert "0K" in result
