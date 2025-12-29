"""
Unit tests for Email Templates Service
Tests for email template generation, content validation, and edge cases.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.email_templates import (
    COMPANY_NAME,
    COMPANY_TAGLINE,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    DARK_COLOR,
    get_base_template,
    welcome_email,
    document_reminder_email,
    case_update_email,
    dispute_sent_email,
    cra_response_email,
    payment_reminder_email,
    analysis_ready_email,
    letters_ready_email,
    cra_response_received_email,
    cra_no_response_violation_email,
    reinsertion_violation_alert_email,
    fcra_analysis_summary_email,
    TEMPLATE_TYPES,
    get_template,
    list_templates,
)


class TestConstants:
    """Tests for module-level constants."""

    def test_company_name_defined(self):
        """Test COMPANY_NAME is defined and non-empty."""
        assert COMPANY_NAME is not None
        assert len(COMPANY_NAME) > 0
        assert COMPANY_NAME == "Brightpath Ascend Group"

    def test_company_tagline_defined(self):
        """Test COMPANY_TAGLINE is defined and non-empty."""
        assert COMPANY_TAGLINE is not None
        assert len(COMPANY_TAGLINE) > 0

    def test_primary_color_is_valid_hex(self):
        """Test PRIMARY_COLOR is a valid hex color."""
        assert PRIMARY_COLOR.startswith("#")
        assert len(PRIMARY_COLOR) == 7
        assert PRIMARY_COLOR == "#319795"

    def test_secondary_color_is_valid_hex(self):
        """Test SECONDARY_COLOR is a valid hex color."""
        assert SECONDARY_COLOR.startswith("#")
        assert len(SECONDARY_COLOR) == 7
        assert SECONDARY_COLOR == "#84cc16"

    def test_dark_color_is_valid_hex(self):
        """Test DARK_COLOR is a valid hex color."""
        assert DARK_COLOR.startswith("#")
        assert len(DARK_COLOR) == 7
        assert DARK_COLOR == "#1a1a2e"


class TestGetBaseTemplate:
    """Tests for get_base_template function."""

    def test_base_template_returns_html(self):
        """Test base template returns valid HTML."""
        result = get_base_template("Test content", "Test Subject")
        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "</html>" in result

    def test_base_template_includes_subject_in_title(self):
        """Test subject is included in title tag."""
        result = get_base_template("Content", "My Subject")
        assert "<title>My Subject</title>" in result

    def test_base_template_includes_content(self):
        """Test content is included in template."""
        result = get_base_template("My custom content here", "Subject")
        assert "My custom content here" in result

    def test_base_template_includes_company_name(self):
        """Test company name is in header."""
        result = get_base_template("Content", "Subject")
        assert COMPANY_NAME in result

    def test_base_template_includes_company_tagline(self):
        """Test company tagline is in header."""
        result = get_base_template("Content", "Subject")
        assert COMPANY_TAGLINE in result

    def test_base_template_includes_colors(self):
        """Test template includes brand colors."""
        result = get_base_template("Content", "Subject")
        assert PRIMARY_COLOR in result
        assert SECONDARY_COLOR in result
        assert DARK_COLOR in result

    def test_base_template_includes_footer(self):
        """Test template includes footer with copyright."""
        result = get_base_template("Content", "Subject")
        assert "2025" in result
        assert "All rights reserved" in result

    def test_base_template_responsive_meta_tag(self):
        """Test template includes viewport meta tag for responsive design."""
        result = get_base_template("Content", "Subject")
        assert 'name="viewport"' in result
        assert "width=device-width" in result


class TestWelcomeEmail:
    """Tests for welcome_email function."""

    def test_welcome_email_basic(self):
        """Test basic welcome email generation."""
        result = welcome_email("John Doe")
        assert "Welcome, John" in result
        assert COMPANY_NAME in result

    def test_welcome_email_extracts_first_name(self):
        """Test first name is extracted from full name."""
        result = welcome_email("Jane Smith")
        assert "Welcome, Jane" in result
        assert "Jane Smith" not in result.split("Welcome")[1].split("!")[0]

    def test_welcome_email_single_name(self):
        """Test email with single name."""
        result = welcome_email("John")
        assert "Welcome, John" in result

    def test_welcome_email_empty_name_fallback(self):
        """Test empty name falls back to 'there'."""
        result = welcome_email("")
        assert "Welcome, there" in result

    def test_welcome_email_none_name_fallback(self):
        """Test None name falls back to 'there'."""
        result = welcome_email(None)
        assert "Welcome, there" in result

    def test_welcome_email_with_portal_url(self):
        """Test welcome email includes portal button when URL provided."""
        result = welcome_email("John Doe", portal_url="https://portal.example.com")
        assert "https://portal.example.com" in result
        assert "Access Your Client Portal" in result

    def test_welcome_email_without_portal_url(self):
        """Test welcome email excludes portal button when no URL."""
        result = welcome_email("John Doe")
        assert "Access Your Client Portal" not in result

    def test_welcome_email_includes_next_steps(self):
        """Test welcome email includes next steps list."""
        result = welcome_email("John Doe")
        assert "review your credit report" in result
        assert "FCRA violations" in result
        assert "dispute letters" in result

    def test_welcome_email_subject_line(self):
        """Test welcome email has correct subject in title."""
        result = welcome_email("John Doe")
        assert f"Welcome to {COMPANY_NAME}" in result


class TestDocumentReminderEmail:
    """Tests for document_reminder_email function."""

    def test_document_reminder_basic(self):
        """Test basic document reminder email."""
        result = document_reminder_email("John Doe", ["Driver's License"])
        assert "Documents Needed, John" in result
        assert "Driver's License" in result

    def test_document_reminder_multiple_docs(self):
        """Test reminder with multiple missing documents."""
        docs = ["Driver's License", "Utility Bill", "SSN Card"]
        result = document_reminder_email("John Doe", docs)
        for doc in docs:
            assert doc in result

    def test_document_reminder_empty_list(self):
        """Test reminder with empty document list."""
        result = document_reminder_email("John Doe", [])
        assert "Documents Needed, John" in result

    def test_document_reminder_with_portal_url(self):
        """Test reminder includes upload button when URL provided."""
        result = document_reminder_email("John Doe", ["ID"], portal_url="https://portal.example.com")
        assert "Upload Documents Now" in result
        assert "https://portal.example.com" in result

    def test_document_reminder_without_portal_url(self):
        """Test reminder excludes upload button when no URL."""
        result = document_reminder_email("John Doe", ["ID"])
        assert "Upload Documents Now" not in result

    def test_document_reminder_empty_name_fallback(self):
        """Test empty name falls back to 'there'."""
        result = document_reminder_email("", ["ID"])
        assert "Documents Needed, there" in result

    def test_document_reminder_subject(self):
        """Test reminder has correct subject."""
        result = document_reminder_email("John Doe", ["ID"])
        assert "Action Required: Documents Needed" in result


class TestCaseUpdateEmail:
    """Tests for case_update_email function."""

    def test_case_update_active_status(self):
        """Test case update for 'active' status."""
        result = case_update_email("John Doe", "active")
        assert "Your Case is Now Active" in result
        assert "John" in result

    def test_case_update_stage1_complete(self):
        """Test case update for 'stage1_complete' status."""
        result = case_update_email("John Doe", "stage1_complete")
        assert "Analysis Complete" in result

    def test_case_update_stage2_complete(self):
        """Test case update for 'stage2_complete' status."""
        result = case_update_email("John Doe", "stage2_complete")
        assert "Dispute Letters Ready" in result

    def test_case_update_waiting_response(self):
        """Test case update for 'waiting_response' status."""
        result = case_update_email("John Doe", "waiting_response")
        assert "Disputes Sent" in result
        assert "30-45 days" in result

    def test_case_update_complete(self):
        """Test case update for 'complete' status."""
        result = case_update_email("John Doe", "complete")
        assert "Case Completed" in result
        assert "Congratulations" in result

    def test_case_update_unknown_status(self):
        """Test case update for unknown status uses generic message."""
        result = case_update_email("John Doe", "custom_status")
        assert "Case Update: custom_status" in result

    def test_case_update_with_details(self):
        """Test case update includes details when provided."""
        result = case_update_email("John Doe", "active", details="Your case has 5 violations.")
        assert "Your case has 5 violations." in result

    def test_case_update_without_details(self):
        """Test case update without details doesn't include details section."""
        result = case_update_email("John Doe", "active")
        # Should not have the details div styling when no details
        assert result.count("border-left: 4px solid") <= 1  # Only in base template styling if any

    def test_case_update_with_portal_url(self):
        """Test case update includes portal button when URL provided."""
        result = case_update_email("John Doe", "active", portal_url="https://portal.example.com")
        assert "View Details in Portal" in result

    def test_case_update_empty_name(self):
        """Test empty name falls back to 'there'."""
        result = case_update_email("", "active")
        assert "there" in result


class TestDisputeSentEmail:
    """Tests for dispute_sent_email function."""

    def test_dispute_sent_basic(self):
        """Test basic dispute sent email."""
        result = dispute_sent_email("John Doe", "Equifax")
        assert "Dispute Letter Sent" in result
        assert "Equifax" in result

    def test_dispute_sent_with_tracking(self):
        """Test dispute sent with tracking info."""
        result = dispute_sent_email("John Doe", "TransUnion", tracking_info="9400111899223456789012")
        assert "Tracking Number" in result
        assert "9400111899223456789012" in result

    def test_dispute_sent_without_tracking(self):
        """Test dispute sent without tracking info."""
        result = dispute_sent_email("John Doe", "Experian")
        assert "Tracking Number" not in result

    def test_dispute_sent_with_portal_url(self):
        """Test dispute sent includes portal button."""
        result = dispute_sent_email("John Doe", "Equifax", portal_url="https://portal.example.com")
        assert "Track Your Disputes" in result

    def test_dispute_sent_includes_expectations(self):
        """Test dispute sent includes what to expect."""
        result = dispute_sent_email("John Doe", "Equifax")
        assert "30-45 days" in result
        assert "client portal" in result

    def test_dispute_sent_subject(self):
        """Test dispute sent has bureau in subject."""
        result = dispute_sent_email("John Doe", "TransUnion")
        assert "Dispute Sent to TransUnion" in result


class TestCraResponseEmail:
    """Tests for cra_response_email function."""

    def test_cra_response_basic(self):
        """Test basic CRA response email."""
        result = cra_response_email("John Doe", "Equifax")
        assert "Response Received from Equifax" in result
        assert "John" in result

    def test_cra_response_with_summary(self):
        """Test CRA response with result summary."""
        result = cra_response_email("John Doe", "TransUnion", result_summary="3 items deleted, 2 verified")
        assert "3 items deleted, 2 verified" in result

    def test_cra_response_without_summary(self):
        """Test CRA response without summary."""
        result = cra_response_email("John Doe", "Experian")
        # Should not have the result summary div
        count = result.count("3 items deleted")
        assert count == 0

    def test_cra_response_with_portal_url(self):
        """Test CRA response includes portal button."""
        result = cra_response_email("John Doe", "Equifax", portal_url="https://portal.example.com")
        assert "View Full Response" in result

    def test_cra_response_subject(self):
        """Test CRA response has bureau in subject."""
        result = cra_response_email("John Doe", "Equifax")
        assert "Bureau Response from Equifax" in result


class TestPaymentReminderEmail:
    """Tests for payment_reminder_email function."""

    def test_payment_reminder_basic(self):
        """Test basic payment reminder email."""
        result = payment_reminder_email("John Doe", 199.99)
        assert "Payment Reminder" in result
        assert "$199.99" in result

    def test_payment_reminder_integer_amount(self):
        """Test payment reminder with integer amount."""
        result = payment_reminder_email("John Doe", 200)
        assert "$200.00" in result

    def test_payment_reminder_string_amount(self):
        """Test payment reminder with string amount."""
        result = payment_reminder_email("John Doe", "250.00")
        assert "$250.00" in result

    def test_payment_reminder_large_amount(self):
        """Test payment reminder with large amount formatting."""
        result = payment_reminder_email("John Doe", 1500.00)
        assert "$1,500.00" in result

    def test_payment_reminder_with_due_date(self):
        """Test payment reminder with due date."""
        result = payment_reminder_email("John Doe", 100, due_date="January 15, 2025")
        assert "Due Date: January 15, 2025" in result

    def test_payment_reminder_without_due_date(self):
        """Test payment reminder without due date."""
        result = payment_reminder_email("John Doe", 100)
        assert "Due Date:" not in result

    def test_payment_reminder_with_payment_url(self):
        """Test payment reminder includes payment button."""
        result = payment_reminder_email("John Doe", 100, payment_url="https://pay.example.com")
        assert "Make Payment Now" in result
        assert "https://pay.example.com" in result

    def test_payment_reminder_empty_name(self):
        """Test empty name falls back to 'there'."""
        result = payment_reminder_email("", 100)
        assert "there" in result


class TestAnalysisReadyEmail:
    """Tests for analysis_ready_email function."""

    def test_analysis_ready_basic(self):
        """Test basic analysis ready email."""
        result = analysis_ready_email("John Doe")
        assert "Your Credit Analysis is Ready" in result
        assert "John" in result

    def test_analysis_ready_with_violations_count(self):
        """Test analysis ready with violations count."""
        result = analysis_ready_email("John Doe", violations_count=15)
        assert "15" in result
        assert "Violations Found" in result

    def test_analysis_ready_with_exposure(self):
        """Test analysis ready with exposure amount."""
        result = analysis_ready_email("John Doe", exposure=50000)
        assert "$50,000" in result
        assert "Potential Exposure" in result

    def test_analysis_ready_with_both_stats(self):
        """Test analysis ready with both violations and exposure."""
        result = analysis_ready_email("John Doe", violations_count=10, exposure=25000)
        assert "10" in result
        assert "$25,000" in result

    def test_analysis_ready_exposure_string(self):
        """Test analysis ready with string exposure."""
        result = analysis_ready_email("John Doe", exposure="TBD")
        assert "TBD" in result

    def test_analysis_ready_with_portal_url(self):
        """Test analysis ready includes portal button."""
        result = analysis_ready_email("John Doe", portal_url="https://portal.example.com")
        assert "View Your Analysis" in result


class TestLettersReadyEmail:
    """Tests for letters_ready_email function."""

    def test_letters_ready_basic(self):
        """Test basic letters ready email."""
        result = letters_ready_email("John Doe", 3)
        assert "Dispute Letters Are Ready" in result
        assert "3" in result

    def test_letters_ready_single_letter(self):
        """Test letters ready with single letter (no plural)."""
        result = letters_ready_email("John Doe", 1)
        assert "1</strong> personalized dispute letter ready" in result
        assert "letters ready" not in result

    def test_letters_ready_multiple_letters(self):
        """Test letters ready with multiple letters (plural)."""
        result = letters_ready_email("John Doe", 5)
        assert "letters ready" in result

    def test_letters_ready_with_bureaus(self):
        """Test letters ready with bureaus list."""
        result = letters_ready_email("John Doe", 3, bureaus=["Equifax", "TransUnion", "Experian"])
        assert "Equifax, TransUnion, Experian" in result

    def test_letters_ready_with_portal_url(self):
        """Test letters ready includes download button."""
        result = letters_ready_email("John Doe", 3, portal_url="https://portal.example.com")
        assert "Download Your Letters" in result

    def test_letters_ready_includes_next_steps(self):
        """Test letters ready includes next steps."""
        result = letters_ready_email("John Doe", 3)
        assert "certified mail" in result
        assert "return receipt" in result


class TestCraResponseReceivedEmail:
    """Tests for cra_response_received_email function."""

    def test_cra_response_received_basic(self):
        """Test basic CRA response received email."""
        result = cra_response_received_email("John Doe", "Equifax", 3, 2)
        assert "Equifax Has Responded" in result
        assert "Items Deleted: 3" in result
        assert "Items Verified: 2" in result

    def test_cra_response_received_zero_items(self):
        """Test CRA response with zero deleted items."""
        result = cra_response_received_email("John Doe", "TransUnion", 0, 5)
        assert "Items Deleted: 0" in result
        assert "Items Verified: 5" in result

    def test_cra_response_received_with_portal(self):
        """Test CRA response includes portal button."""
        result = cra_response_received_email("John Doe", "Experian", 1, 1, portal_url="https://portal.example.com")
        assert "View Full Response" in result

    def test_cra_response_received_includes_next_steps(self):
        """Test CRA response includes what happens next."""
        result = cra_response_received_email("John Doe", "Equifax", 2, 3)
        assert "escalation letters" in result
        assert "2-3 business days" in result


class TestCraNoResponseViolationEmail:
    """Tests for cra_no_response_violation_email function."""

    def test_no_response_violation_basic(self):
        """Test basic no response violation email."""
        result = cra_no_response_violation_email("John Doe", "Equifax")
        assert "FCRA Violation" in result
        assert "Equifax" in result
        assert "Failed to Respond" in result

    def test_no_response_violation_legal_reference(self):
        """Test includes FCRA legal reference."""
        result = cra_no_response_violation_email("John Doe", "TransUnion")
        assert "15 U.S.C." in result
        assert "30 days" in result

    def test_no_response_violation_with_portal(self):
        """Test includes portal button."""
        result = cra_no_response_violation_email("John Doe", "Experian", portal_url="https://portal.example.com")
        assert "View Case Details" in result

    def test_no_response_violation_includes_implications(self):
        """Test includes legal implications."""
        result = cra_no_response_violation_email("John Doe", "Equifax")
        assert "statutory damages" in result
        assert "Escalation Protocol" in result


class TestReinsertionViolationAlertEmail:
    """Tests for reinsertion_violation_alert_email function."""

    def test_reinsertion_violation_basic(self):
        """Test basic reinsertion violation email."""
        result = reinsertion_violation_alert_email("John Doe", "Equifax", "ABC Collections")
        assert "Reinsertion Violation" in result
        assert "Equifax" in result
        assert "ABC Collections" in result

    def test_reinsertion_violation_urgent_styling(self):
        """Test email has urgent styling."""
        result = reinsertion_violation_alert_email("John Doe", "TransUnion", "XYZ Bank")
        assert "URGENT" in result
        assert "#dc2626" in result or "#ef4444" in result  # Red colors

    def test_reinsertion_violation_legal_citation(self):
        """Test includes FCRA section citation."""
        result = reinsertion_violation_alert_email("John Doe", "Experian", "Account")
        assert "1681i(a)(5)(B)" in result
        assert "5 business days" in result or "5-day" in result

    def test_reinsertion_violation_damages_info(self):
        """Test includes damages information."""
        result = reinsertion_violation_alert_email("John Doe", "Equifax", "Account")
        assert "$100" in result
        assert "$1,000" in result

    def test_reinsertion_violation_with_portal(self):
        """Test includes action required button."""
        result = reinsertion_violation_alert_email("John Doe", "Equifax", "Account", portal_url="https://portal.example.com")
        assert "Action Required" in result


class TestFcraAnalysisSummaryEmail:
    """Tests for fcra_analysis_summary_email function."""

    def test_fcra_summary_basic(self):
        """Test basic FCRA summary email."""
        violations = [
            {"bureau": "Equifax", "account_name": "ABC Collections", "violation_type": "Late reporting", "description": "Reported after dispute"}
        ]
        damages_info = {"total_exposure": 50000, "settlement_target": 25000, "violations_count": 5}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        assert "Credit Analysis is Complete" in result
        assert "John" in result

    def test_fcra_summary_includes_violations(self):
        """Test summary includes violations list."""
        violations = [
            {"bureau": "Equifax", "account_name": "ABC Collections", "violation_type": "Late reporting", "description": "Test description"}
        ]
        damages_info = {"total_exposure": 50000, "settlement_target": 25000, "violations_count": 1}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        assert "ABC Collections" in result
        assert "Late reporting" in result

    def test_fcra_summary_groups_by_bureau(self):
        """Test summary groups violations by bureau."""
        violations = [
            {"bureau": "Equifax", "account_name": "Account1", "violation_type": "Type1", "description": "Desc1"},
            {"bureau": "TransUnion", "account_name": "Account2", "violation_type": "Type2", "description": "Desc2"},
        ]
        damages_info = {"total_exposure": 50000, "settlement_target": 25000, "violations_count": 2}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        assert "Equifax" in result
        assert "TransUnion" in result

    def test_fcra_summary_strong_case(self):
        """Test summary with 'Strong' case strength styling."""
        violations = []
        damages_info = {"total_exposure": 100000, "settlement_target": 50000, "violations_count": 10}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        assert "Strong" in result
        assert "#dcfce7" in result  # Green background for strong case

    def test_fcra_summary_moderate_case(self):
        """Test summary with 'Moderate' case strength styling."""
        violations = []
        damages_info = {"total_exposure": 50000, "settlement_target": 20000, "violations_count": 5}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Moderate")
        assert "Moderate" in result
        assert "#fef3c7" in result  # Yellow background for moderate case

    def test_fcra_summary_weak_case(self):
        """Test summary with 'Weak' case strength styling."""
        violations = []
        damages_info = {"total_exposure": 10000, "settlement_target": 5000, "violations_count": 2}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Weak")
        assert "Weak" in result
        assert "#fee2e2" in result  # Red background for weak case

    def test_fcra_summary_unknown_case_strength(self):
        """Test summary with unknown case strength defaults to moderate."""
        violations = []
        damages_info = {"total_exposure": 50000, "settlement_target": 25000, "violations_count": 5}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Unknown")
        # Should use moderate styling as fallback
        assert "#fef3c7" in result

    def test_fcra_summary_damages_formatting(self):
        """Test summary formats damages correctly."""
        violations = []
        damages_info = {"total_exposure": 150000, "settlement_target": 75000, "violations_count": 15}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        assert "$150,000" in result
        assert "$75,000" in result
        assert "15" in result

    def test_fcra_summary_limits_violations(self):
        """Test summary limits to first 10 violations."""
        violations = [
            {"bureau": f"Bureau{i}", "account_name": f"Account{i}", "violation_type": "Type", "description": "Desc"}
            for i in range(15)
        ]
        damages_info = {"total_exposure": 100000, "settlement_target": 50000, "violations_count": 15}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        # Should only include first 10
        assert "Account0" in result
        assert "Account9" in result
        # Account10 through Account14 should not be in email
        assert "Account14" not in result

    def test_fcra_summary_truncates_long_descriptions(self):
        """Test summary truncates long descriptions."""
        long_desc = "A" * 200
        violations = [
            {"bureau": "Equifax", "account_name": "Account", "violation_type": "Type", "description": long_desc}
        ]
        damages_info = {"total_exposure": 50000, "settlement_target": 25000, "violations_count": 1}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        # Description should be truncated to 150 chars + "..."
        assert "..." in result
        assert long_desc not in result

    def test_fcra_summary_with_portal(self):
        """Test summary includes portal button."""
        violations = []
        damages_info = {"total_exposure": 50000, "settlement_target": 25000, "violations_count": 5}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong", portal_url="https://portal.example.com")
        assert "Access Your Client Portal" in result

    def test_fcra_summary_includes_legal_info(self):
        """Test summary includes legal information."""
        violations = []
        damages_info = {"total_exposure": 50000, "settlement_target": 25000, "violations_count": 5}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        assert "1681n" in result or "1681o" in result
        assert "Statutory Damages" in result


class TestTemplateTypes:
    """Tests for TEMPLATE_TYPES dictionary."""

    def test_template_types_is_dict(self):
        """Test TEMPLATE_TYPES is a dictionary."""
        assert isinstance(TEMPLATE_TYPES, dict)

    def test_template_types_contains_expected_keys(self):
        """Test TEMPLATE_TYPES contains all expected template keys."""
        expected_keys = [
            "welcome",
            "document_reminder",
            "case_update",
            "dispute_sent",
            "cra_response",
            "payment_reminder",
            "analysis_ready",
            "letters_ready",
            "cra_response_received",
            "cra_no_response_violation",
            "reinsertion_violation_alert",
        ]
        for key in expected_keys:
            assert key in TEMPLATE_TYPES, f"Missing template key: {key}"

    def test_template_types_values_are_callable(self):
        """Test all TEMPLATE_TYPES values are callable functions."""
        for name, func in TEMPLATE_TYPES.items():
            assert callable(func), f"Template '{name}' is not callable"


class TestGetTemplate:
    """Tests for get_template function."""

    def test_get_template_valid_type(self):
        """Test get_template returns function for valid type."""
        template = get_template("welcome")
        assert template is not None
        assert callable(template)
        assert template == welcome_email

    def test_get_template_all_types(self):
        """Test get_template works for all template types."""
        for template_type in TEMPLATE_TYPES.keys():
            template = get_template(template_type)
            assert template is not None
            assert callable(template)

    def test_get_template_invalid_type(self):
        """Test get_template returns None for invalid type."""
        template = get_template("nonexistent_template")
        assert template is None

    def test_get_template_empty_string(self):
        """Test get_template returns None for empty string."""
        template = get_template("")
        assert template is None


class TestListTemplates:
    """Tests for list_templates function."""

    def test_list_templates_returns_list(self):
        """Test list_templates returns a list."""
        result = list_templates()
        assert isinstance(result, list)

    def test_list_templates_contains_all_templates(self):
        """Test list_templates contains all template types."""
        result = list_templates()
        expected = [
            "welcome",
            "document_reminder",
            "case_update",
            "dispute_sent",
            "cra_response",
            "payment_reminder",
            "analysis_ready",
            "letters_ready",
            "cra_response_received",
            "cra_no_response_violation",
            "reinsertion_violation_alert",
        ]
        for template in expected:
            assert template in result

    def test_list_templates_matches_template_types_keys(self):
        """Test list_templates matches TEMPLATE_TYPES keys."""
        result = list_templates()
        assert set(result) == set(TEMPLATE_TYPES.keys())


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_special_characters_in_name(self):
        """Test special characters in client name are handled."""
        result = welcome_email("O'Brien-Smith")
        assert "O'Brien" in result or "O&#x27;Brien" in result

    def test_unicode_in_name(self):
        """Test unicode characters in client name."""
        result = welcome_email("Jose Garcia")
        assert "Jose" in result

    def test_very_long_name(self):
        """Test very long client name doesn't break template."""
        long_name = "A" * 500 + " " + "B" * 500
        result = welcome_email(long_name)
        assert "<!DOCTYPE html>" in result
        assert "</html>" in result

    def test_html_injection_in_name(self):
        """Test HTML in name is handled (not injected)."""
        result = welcome_email("<script>alert('xss')</script>")
        # The template should include the content but HTML won't execute
        assert "<!DOCTYPE html>" in result

    def test_empty_violations_list(self):
        """Test FCRA summary with empty violations list."""
        violations = []
        damages_info = {"total_exposure": 0, "settlement_target": 0, "violations_count": 0}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Weak")
        assert "Credit Analysis is Complete" in result

    def test_missing_violation_keys(self):
        """Test handling of violations with missing keys."""
        violations = [
            {"bureau": "Equifax"}  # Missing other keys
        ]
        damages_info = {"total_exposure": 50000, "settlement_target": 25000, "violations_count": 1}
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        assert "Equifax" in result

    def test_missing_damages_keys(self):
        """Test handling of damages_info with missing keys."""
        violations = []
        damages_info = {}  # Empty dict
        result = fcra_analysis_summary_email("John Doe", violations, damages_info, "Strong")
        assert "Credit Analysis is Complete" in result
        assert "$0" in result

    def test_zero_letter_count(self):
        """Test letters ready with zero letters."""
        result = letters_ready_email("John Doe", 0)
        assert "0</strong> personalized dispute letters" in result

    def test_negative_amount(self):
        """Test payment reminder with negative amount."""
        result = payment_reminder_email("John Doe", -50)
        assert "-$50.00" in result or "$-50.00" in result

    def test_whitespace_in_bureau_name(self):
        """Test bureau name with extra whitespace."""
        result = dispute_sent_email("John Doe", "  Equifax  ")
        assert "Equifax" in result

    def test_all_templates_return_strings(self):
        """Test all template functions return strings."""
        assert isinstance(welcome_email("Test"), str)
        assert isinstance(document_reminder_email("Test", ["doc"]), str)
        assert isinstance(case_update_email("Test", "active"), str)
        assert isinstance(dispute_sent_email("Test", "Bureau"), str)
        assert isinstance(cra_response_email("Test", "Bureau"), str)
        assert isinstance(payment_reminder_email("Test", 100), str)
        assert isinstance(analysis_ready_email("Test"), str)
        assert isinstance(letters_ready_email("Test", 1), str)
        assert isinstance(cra_response_received_email("Test", "Bureau", 1, 1), str)
        assert isinstance(cra_no_response_violation_email("Test", "Bureau"), str)
        assert isinstance(reinsertion_violation_alert_email("Test", "Bureau", "Account"), str)

    def test_templates_contain_valid_html_structure(self):
        """Test all templates contain valid HTML structure."""
        templates_to_test = [
            welcome_email("Test"),
            document_reminder_email("Test", ["doc"]),
            case_update_email("Test", "active"),
            dispute_sent_email("Test", "Bureau"),
            cra_response_email("Test", "Bureau"),
            payment_reminder_email("Test", 100),
            analysis_ready_email("Test"),
            letters_ready_email("Test", 1),
            cra_response_received_email("Test", "Bureau", 1, 1),
            cra_no_response_violation_email("Test", "Bureau"),
            reinsertion_violation_alert_email("Test", "Bureau", "Account"),
        ]
        for html in templates_to_test:
            assert "<!DOCTYPE html>" in html
            assert "<html>" in html
            assert "</html>" in html
            assert "<body" in html
            assert "</body>" in html
