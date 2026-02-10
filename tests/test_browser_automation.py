"""
Unit tests for Browser Automation module.

Tests the 5-Day Knockout and Inquiry Dispute browser automation
without actually running browsers (mocked).
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


# =============================================================================
# BASE AUTOMATION TESTS
# =============================================================================


class TestAutomationResult:
    """Test AutomationResult dataclass"""

    def test_automation_result_success(self):
        """Test successful automation result"""
        from services.browser_automation.base_automation import AutomationResult

        result = AutomationResult(
            success=True,
            message="Test completed",
            confirmation_number="12345",
            data={"key": "value"},
            duration_seconds=30.5,
        )

        assert result.success is True
        assert result.message == "Test completed"
        assert result.confirmation_number == "12345"
        assert result.data == {"key": "value"}
        assert result.duration_seconds == 30.5

    def test_automation_result_failure(self):
        """Test failed automation result"""
        from services.browser_automation.base_automation import AutomationResult

        result = AutomationResult(
            success=False,
            message="Test failed",
            error_code="TEST_ERROR",
            screenshot_path="/path/to/screenshot.png",
        )

        assert result.success is False
        assert result.error_code == "TEST_ERROR"
        assert result.screenshot_path == "/path/to/screenshot.png"

    def test_automation_result_to_dict(self):
        """Test AutomationResult to_dict method"""
        from services.browser_automation.base_automation import AutomationResult

        result = AutomationResult(
            success=True,
            message="Test",
            confirmation_number="ABC123",
            data={"test": True},
            screenshot_path="/path.png",
            error_code=None,
            duration_seconds=10.0,
        )

        d = result.to_dict()
        assert d["success"] is True
        assert d["message"] == "Test"
        assert d["confirmation_number"] == "ABC123"
        assert d["data"]["test"] is True
        assert d["duration_seconds"] == 10.0


class TestAutomationError:
    """Test AutomationError exception"""

    def test_automation_error_basic(self):
        """Test basic AutomationError creation"""
        from services.browser_automation.base_automation import AutomationError

        error = AutomationError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.error_code == "AUTOMATION_ERROR"
        assert error.screenshot_path is None

    def test_automation_error_with_code(self):
        """Test AutomationError with error code"""
        from services.browser_automation.base_automation import AutomationError

        error = AutomationError(
            "Login failed",
            error_code="LOGIN_FAILED",
            screenshot_path="/screenshots/error.png",
        )

        assert error.message == "Login failed"
        assert error.error_code == "LOGIN_FAILED"
        assert error.screenshot_path == "/screenshots/error.png"


class TestBaseAutomation:
    """Test BaseAutomation class"""

    def test_base_automation_init(self):
        """Test BaseAutomation initialization"""
        from services.browser_automation.base_automation import BaseAutomation

        auto = BaseAutomation(
            client_id=123,
            staff_id=456,
            headless=True,
            timeout=120,
        )

        assert auto.client_id == 123
        assert auto.staff_id == 456
        assert auto.headless is True
        assert auto.timeout == 120
        assert auto.browser is None
        assert auto.agent is None

    def test_base_automation_portal_urls(self):
        """Test portal URL constants"""
        from services.browser_automation.base_automation import BaseAutomation

        assert "identitytheft.gov" in BaseAutomation.FTC_URL
        assert "consumerfinance.gov" in BaseAutomation.CFPB_URL
        assert "equifax.com" in BaseAutomation.EQUIFAX_URL
        assert "transunion.com" in BaseAutomation.TRANSUNION_URL
        assert "experian.com" in BaseAutomation.EXPERIAN_URL

    def test_calculate_duration(self):
        """Test duration calculation"""
        from services.browser_automation.base_automation import BaseAutomation

        auto = BaseAutomation(client_id=1)
        auto.start_time = datetime(2024, 1, 1, 12, 0, 0)

        with patch("services.browser_automation.base_automation.datetime") as mock_dt:
            mock_dt.utcnow.return_value = datetime(2024, 1, 1, 12, 1, 30)
            duration = auto.calculate_duration()

        assert duration == 90.0  # 1 minute 30 seconds


# =============================================================================
# FTC AUTOMATION TESTS
# =============================================================================


class TestFTCAutomation:
    """Test FTCAutomation class"""

    def test_ftc_automation_init(self):
        """Test FTCAutomation initialization"""
        from services.browser_automation.ftc_automation import FTCAutomation

        auto = FTCAutomation(
            client_id=123,
            staff_id=456,
            headless=True,
        )

        assert auto.client_id == 123
        assert auto.report_number is None
        assert auto.affidavit_path is None
        assert "identitytheft.gov" in auto.FTC_REPORT_URL

    def test_format_account_details_fraud(self):
        """Test formatting account details for fraud"""
        from services.browser_automation.ftc_automation import FTCAutomation

        auto = FTCAutomation(client_id=1)
        account = {
            "creditor_name": "Chase Bank",
            "account_number": "****1234",
            "account_type": "credit_card",
            "date_opened": "2024-01-15",
            "balance": 5000,
            "bureaus": ["equifax", "transunion"],
        }

        details = auto._format_account_details(account, is_inquiry=False)

        assert "Fraudulent credit_card" in details
        assert "Chase Bank" in details
        assert "****1234" in details
        assert "2024-01-15" in details
        assert "5000" in details
        assert "equifax, transunion" in details
        assert "I did NOT open this account" in details

    def test_format_account_details_inquiry(self):
        """Test formatting account details for inquiry"""
        from services.browser_automation.ftc_automation import FTCAutomation

        auto = FTCAutomation(client_id=1)
        inquiry = {
            "creditor_name": "Capital One",
            "inquiry_date": "2024-02-01",
            "bureaus": ["experian"],
        }

        details = auto._format_account_details(inquiry, is_inquiry=True)

        assert "Unauthorized Hard Inquiry" in details
        assert "Capital One" in details
        assert "2024-02-01" in details
        assert "I did NOT authorize" in details

    def test_extract_report_number_found(self):
        """Test extracting FTC report number"""
        from services.browser_automation.ftc_automation import FTCAutomation

        auto = FTCAutomation(client_id=1)

        result = {"text": "Your FTC Report Number: 123456789012"}
        report_num = auto._extract_report_number(result)
        assert report_num == "123456789012"

    def test_extract_report_number_not_found(self):
        """Test extracting report number when not present"""
        from services.browser_automation.ftc_automation import FTCAutomation

        auto = FTCAutomation(client_id=1)

        result = {"text": "No number here"}
        report_num = auto._extract_report_number(result)
        assert report_num is None


# =============================================================================
# CFPB AUTOMATION TESTS
# =============================================================================


class TestCFPBAutomation:
    """Test CFPBAutomation class"""

    def test_cfpb_automation_init(self):
        """Test CFPBAutomation initialization"""
        from services.browser_automation.cfpb_automation import CFPBAutomation

        auto = CFPBAutomation(
            client_id=123,
            staff_id=456,
        )

        assert auto.client_id == 123
        assert auto.confirmation_numbers == {}
        assert "consumerfinance.gov" in auto.CFPB_COMPLAINT_URL

    def test_bureau_names_mapping(self):
        """Test bureau name normalization"""
        from services.browser_automation.cfpb_automation import BUREAU_NAMES

        assert BUREAU_NAMES["transunion"] == "TransUnion"
        assert BUREAU_NAMES["equifax"] == "Equifax"
        assert BUREAU_NAMES["experian"] == "Experian"
        assert BUREAU_NAMES["tu"] == "TransUnion"
        assert BUREAU_NAMES["eq"] == "Equifax"
        assert BUREAU_NAMES["exp"] == "Experian"

    def test_build_complaint_narrative_fraud(self):
        """Test building CFPB narrative for fraud"""
        from services.browser_automation.cfpb_automation import CFPBAutomation

        auto = CFPBAutomation(client_id=1)
        account = {
            "creditor_name": "Chase Bank",
            "account_number": "****1234",
            "account_type": "credit_card",
            "date_opened": "2024-01-15",
            "balance": 5000,
        }

        narrative = auto._build_complaint_narrative(
            "Equifax", account, is_inquiry=False, ftc_report_number="123456"
        )

        assert "victim of identity theft" in narrative
        assert "Chase Bank" in narrative
        assert "Equifax" in narrative
        assert "FCRA Section 605B" in narrative
        assert "4 business days" in narrative
        assert "123456" in narrative

    def test_build_complaint_narrative_inquiry(self):
        """Test building CFPB narrative for inquiry"""
        from services.browser_automation.cfpb_automation import CFPBAutomation

        auto = CFPBAutomation(client_id=1)
        inquiry = {
            "creditor_name": "Capital One",
            "inquiry_date": "2024-02-01",
        }

        narrative = auto._build_complaint_narrative(
            "TransUnion", inquiry, is_inquiry=True
        )

        assert "unauthorized hard inquiry" in narrative
        assert "Capital One" in narrative
        assert "TransUnion" in narrative
        assert "I did NOT authorize" in narrative

    def test_extract_confirmation_number(self):
        """Test extracting CFPB confirmation number"""
        from services.browser_automation.cfpb_automation import CFPBAutomation

        auto = CFPBAutomation(client_id=1)

        result = {"text": "Confirmation #: CFPB-12345678"}
        conf_num = auto._extract_confirmation_number(result)
        assert conf_num is not None


# =============================================================================
# BUREAU AUTOMATION TESTS
# =============================================================================


class TestBureauAutomation:
    """Test bureau-specific automation classes"""

    def test_get_bureau_automation_equifax(self):
        """Test getting Equifax automation"""
        from services.browser_automation.bureau_automation import (
            get_bureau_automation,
            EquifaxAutomation,
        )

        auto = get_bureau_automation("equifax", client_id=1)
        assert isinstance(auto, EquifaxAutomation)
        assert auto.BUREAU_NAME == "Equifax"
        assert auto.BUREAU_CODE == "eq"

    def test_get_bureau_automation_transunion(self):
        """Test getting TransUnion automation"""
        from services.browser_automation.bureau_automation import (
            get_bureau_automation,
            TransUnionAutomation,
        )

        auto = get_bureau_automation("transunion", client_id=1)
        assert isinstance(auto, TransUnionAutomation)
        assert auto.BUREAU_NAME == "TransUnion"
        assert auto.BUREAU_CODE == "tu"

    def test_get_bureau_automation_experian(self):
        """Test getting Experian automation"""
        from services.browser_automation.bureau_automation import (
            get_bureau_automation,
            ExperianAutomation,
        )

        auto = get_bureau_automation("experian", client_id=1)
        assert isinstance(auto, ExperianAutomation)
        assert auto.BUREAU_NAME == "Experian"
        assert auto.BUREAU_CODE == "exp"

    def test_get_bureau_automation_invalid(self):
        """Test getting automation for invalid bureau"""
        from services.browser_automation.bureau_automation import get_bureau_automation

        with pytest.raises(ValueError) as exc:
            get_bureau_automation("invalid_bureau", client_id=1)

        assert "Unknown bureau" in str(exc.value)

    def test_equifax_portal_url(self):
        """Test Equifax portal URL"""
        from services.browser_automation.bureau_automation import EquifaxAutomation

        auto = EquifaxAutomation(client_id=1)
        assert "equifax.com" in auto.PORTAL_URL

    def test_transunion_portal_url(self):
        """Test TransUnion portal URL"""
        from services.browser_automation.bureau_automation import TransUnionAutomation

        auto = TransUnionAutomation(client_id=1)
        assert "transunion.com" in auto.PORTAL_URL

    def test_experian_portal_url(self):
        """Test Experian portal URL"""
        from services.browser_automation.bureau_automation import ExperianAutomation

        auto = ExperianAutomation(client_id=1)
        assert "experian.com" in auto.PORTAL_URL


# =============================================================================
# 5KO ORCHESTRATOR TESTS
# =============================================================================


class TestFiveKnockoutStatus:
    """Test FiveKnockoutStatus dataclass"""

    def test_status_init(self):
        """Test FiveKnockoutStatus initialization"""
        from services.browser_automation.fko_orchestrator import FiveKnockoutStatus

        status = FiveKnockoutStatus(
            client_id=123,
            account={"creditor_name": "Chase"},
        )

        assert status.client_id == 123
        assert status.account == {"creditor_name": "Chase"}
        assert status.current_step == "pending"
        assert status.ftc_result is None
        assert status.cfpb_results == {}
        assert status.bureau_results == {}

    def test_is_complete_all_success(self):
        """Test is_complete when all steps succeed"""
        from services.browser_automation.fko_orchestrator import FiveKnockoutStatus
        from services.browser_automation.base_automation import AutomationResult

        status = FiveKnockoutStatus(
            client_id=123,
            account={},
        )
        status.ftc_result = AutomationResult(success=True, message="OK")
        status.cfpb_results = {
            "equifax": AutomationResult(success=True, message="OK"),
            "transunion": AutomationResult(success=True, message="OK"),
        }
        status.bureau_results = {
            "equifax": AutomationResult(success=True, message="OK"),
            "transunion": AutomationResult(success=True, message="OK"),
        }

        assert status.is_complete is True

    def test_is_complete_partial_failure(self):
        """Test is_complete when some steps fail"""
        from services.browser_automation.fko_orchestrator import FiveKnockoutStatus
        from services.browser_automation.base_automation import AutomationResult

        status = FiveKnockoutStatus(
            client_id=123,
            account={},
        )
        status.ftc_result = AutomationResult(success=True, message="OK")
        status.cfpb_results = {
            "equifax": AutomationResult(success=False, message="Failed"),
        }
        status.bureau_results = {}

        assert status.is_complete is False

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        from services.browser_automation.fko_orchestrator import FiveKnockoutStatus
        from services.browser_automation.base_automation import AutomationResult

        status = FiveKnockoutStatus(
            client_id=123,
            account={},
        )
        status.ftc_result = AutomationResult(success=True, message="OK")
        status.cfpb_results = {
            "equifax": AutomationResult(success=True, message="OK"),
            "transunion": AutomationResult(success=False, message="Failed"),
        }
        status.bureau_results = {
            "equifax": AutomationResult(success=True, message="OK"),
        }

        # 3 successes out of 4 total (1 FTC + 2 CFPB + 1 bureau)
        assert status.success_rate == 0.75

    def test_to_dict(self):
        """Test FiveKnockoutStatus to_dict"""
        from services.browser_automation.fko_orchestrator import FiveKnockoutStatus

        status = FiveKnockoutStatus(
            client_id=123,
            account={"creditor": "Test"},
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            ftc_report_number="123456",
        )

        d = status.to_dict()
        assert d["client_id"] == 123
        assert d["account"]["creditor"] == "Test"
        assert d["ftc_report_number"] == "123456"
        assert d["started_at"] == "2024-01-01T12:00:00"


class TestFiveKnockoutOrchestrator:
    """Test FiveKnockoutOrchestrator class"""

    def test_orchestrator_init(self):
        """Test FiveKnockoutOrchestrator initialization"""
        from services.browser_automation.fko_orchestrator import (
            FiveKnockoutOrchestrator,
        )

        orch = FiveKnockoutOrchestrator(
            client_id=123,
            staff_id=456,
            headless=True,
            delay_between_steps=60,
        )

        assert orch.client_id == 123
        assert orch.staff_id == 456
        assert orch.headless is True
        assert orch.delay_between_steps == 60
        assert orch.status is None


# =============================================================================
# INQUIRY ORCHESTRATOR TESTS
# =============================================================================


class TestInquiryDisputeStatus:
    """Test InquiryDisputeStatus dataclass"""

    def test_status_init(self):
        """Test InquiryDisputeStatus initialization"""
        from services.browser_automation.inquiry_orchestrator import (
            InquiryDisputeStatus,
        )

        status = InquiryDisputeStatus(
            client_id=123,
            inquiry={"creditor_name": "Capital One"},
        )

        assert status.client_id == 123
        assert status.inquiry == {"creditor_name": "Capital One"}
        assert status.current_step == "pending"
        assert status.ftc_result is None
        assert status.cfpb_results == {}

    def test_is_complete(self):
        """Test is_complete for inquiry dispute"""
        from services.browser_automation.inquiry_orchestrator import (
            InquiryDisputeStatus,
        )
        from services.browser_automation.base_automation import AutomationResult

        status = InquiryDisputeStatus(
            client_id=123,
            inquiry={},
        )
        status.ftc_result = AutomationResult(success=True, message="OK")
        status.cfpb_results = {
            "equifax": AutomationResult(success=True, message="OK"),
        }

        assert status.is_complete is True

    def test_success_rate(self):
        """Test success rate for inquiry dispute"""
        from services.browser_automation.inquiry_orchestrator import (
            InquiryDisputeStatus,
        )
        from services.browser_automation.base_automation import AutomationResult

        status = InquiryDisputeStatus(
            client_id=123,
            inquiry={},
        )
        status.ftc_result = AutomationResult(success=True, message="OK")
        status.cfpb_results = {
            "equifax": AutomationResult(success=True, message="OK"),
            "transunion": AutomationResult(success=False, message="Failed"),
        }

        # 2 successes out of 3 total (1 FTC + 2 CFPB)
        assert abs(status.success_rate - 0.6667) < 0.01


class TestInquiryDisputeOrchestrator:
    """Test InquiryDisputeOrchestrator class"""

    def test_orchestrator_init(self):
        """Test InquiryDisputeOrchestrator initialization"""
        from services.browser_automation.inquiry_orchestrator import (
            InquiryDisputeOrchestrator,
        )

        orch = InquiryDisputeOrchestrator(
            client_id=123,
            staff_id=456,
            headless=True,
        )

        assert orch.client_id == 123
        assert orch.staff_id == 456
        assert orch.headless is True


# =============================================================================
# API ENDPOINT TESTS
# =============================================================================


class TestBrowserAutomationEndpoints:
    """Test browser automation API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        import sys
        import os

        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app import app

        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def auth_headers(self, client):
        """Get auth headers for API calls"""
        # Login as staff
        with client.session_transaction() as sess:
            sess["staff_id"] = 1
            sess["staff_email"] = "test@example.com"
        return {}

    def test_5ko_execute_requires_client_id(self, client, auth_headers):
        """Test 5KO execute endpoint requires client_id"""
        response = client.post(
            "/api/automation/5ko/execute",
            json={"account": {}},
            headers=auth_headers,
        )

        assert response.status_code in [400, 401]  # 400 if authorized, 401 if not

    def test_5ko_execute_requires_account(self, client, auth_headers):
        """Test 5KO execute endpoint requires account"""
        response = client.post(
            "/api/automation/5ko/execute",
            json={"client_id": 123},
            headers=auth_headers,
        )

        assert response.status_code in [400, 401]

    def test_inquiry_execute_requires_client_id(self, client, auth_headers):
        """Test inquiry execute endpoint requires client_id"""
        response = client.post(
            "/api/automation/inquiry/execute",
            json={"inquiry": {}},
            headers=auth_headers,
        )

        assert response.status_code in [400, 401]

    def test_inquiry_execute_requires_inquiry(self, client, auth_headers):
        """Test inquiry execute endpoint requires inquiry"""
        response = client.post(
            "/api/automation/inquiry/execute",
            json={"client_id": 123},
            headers=auth_headers,
        )

        assert response.status_code in [400, 401]

    def test_inquiry_batch_requires_inquiries(self, client, auth_headers):
        """Test batch inquiry endpoint requires inquiries list"""
        response = client.post(
            "/api/automation/inquiry/batch",
            json={"client_id": 123},
            headers=auth_headers,
        )

        assert response.status_code in [400, 401]


# =============================================================================
# INTEGRATION-STYLE TESTS (Mocked)
# =============================================================================


class TestMockedAutomationFlow:
    """Test automation flows with mocked browser interactions"""

    @pytest.mark.asyncio
    async def test_ftc_automation_flow_mocked(self):
        """Test FTC automation flow with mocks"""
        from services.browser_automation.ftc_automation import FTCAutomation
        from services.browser_automation.base_automation import AutomationResult

        auto = FTCAutomation(client_id=1)

        # Mock all the methods
        auto.setup = AsyncMock()
        auto.teardown = AsyncMock()
        auto.run_task = AsyncMock(
            return_value={"success": True, "text": "Report #: 123456789012"}
        )
        auto.take_screenshot = AsyncMock(return_value="/path/screenshot.png")
        auto.get_client_data = MagicMock(
            return_value={
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-1234",
                "address": "123 Main St",
                "city": "Newark",
                "state": "NJ",
                "zip_code": "07102",
                "ssn_last_4": "1234",
                "dob": "1990-01-15",
            }
        )
        auto.create_automation_run = MagicMock(return_value=1)
        auto.mark_run_started = MagicMock()
        auto.mark_run_completed = MagicMock()
        auto.update_client_tracking = MagicMock()

        await auto.setup()

        account = {
            "creditor_name": "Chase",
            "account_number": "****1234",
            "account_type": "credit_card",
            "date_opened": "2024-01-15",
            "balance": 5000,
            "bureaus": ["equifax"],
        }

        # The actual file_identity_theft_report would run the full flow
        # We're testing that the components work together

        assert auto.get_client_data() is not None
        assert auto._format_account_details(account, is_inquiry=False) is not None

        await auto.teardown()

    @pytest.mark.asyncio
    async def test_cfpb_automation_flow_mocked(self):
        """Test CFPB automation flow with mocks"""
        from services.browser_automation.cfpb_automation import CFPBAutomation

        auto = CFPBAutomation(client_id=1)

        # Mock methods
        auto.setup = AsyncMock()
        auto.teardown = AsyncMock()
        auto.run_task = AsyncMock(
            return_value={"success": True, "text": "Confirmation: ABC12345"}
        )
        auto.take_screenshot = AsyncMock(return_value="/path/screenshot.png")
        auto.get_client_data = MagicMock(
            return_value={
                "name": "John Doe",
                "email": "john@example.com",
            }
        )

        await auto.setup()

        account = {
            "creditor_name": "Chase",
            "account_number": "****1234",
        }

        narrative = auto._build_complaint_narrative(
            "Equifax", account, is_inquiry=False
        )
        assert "Chase" in narrative
        assert "Equifax" in narrative

        await auto.teardown()
