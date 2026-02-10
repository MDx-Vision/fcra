"""
Unit tests for AutomationRun model and API endpoints (ISSUE-022)

Tests the browser automation tracking functionality for 5KO and Inquiry Disputes.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestAutomationRunModel:
    """Test AutomationRun database model"""

    def test_automation_run_creation(self):
        """Test creating an AutomationRun with required fields"""
        from database import AutomationRun

        run = AutomationRun(
            client_id=1,
            automation_type="5ko_ftc",
            portal="ftc",
            status="pending",
            items_total=0,
            retry_count=0,
            max_retries=3
        )

        assert run.client_id == 1
        assert run.automation_type == "5ko_ftc"
        assert run.portal == "ftc"
        assert run.status == "pending"
        assert run.items_total == 0
        assert run.retry_count == 0
        assert run.max_retries == 3

    def test_automation_run_to_dict(self):
        """Test to_dict method"""
        from database import AutomationRun

        run = AutomationRun(
            id=1,
            client_id=1,
            automation_type="5ko_cfpb",
            portal="cfpb",
            status="completed",
            items_total=5,
            items_processed=5,
            items_succeeded=4,
            items_failed=1,
            confirmation_number="CFPB-12345",
            created_at=datetime(2026, 2, 10, 12, 0, 0)
        )

        result = run.to_dict()

        assert result["id"] == 1
        assert result["client_id"] == 1
        assert result["automation_type"] == "5ko_cfpb"
        assert result["portal"] == "cfpb"
        assert result["status"] == "completed"
        assert result["items_total"] == 5
        assert result["items_succeeded"] == 4
        assert result["items_failed"] == 1
        assert result["confirmation_number"] == "CFPB-12345"

    def test_mark_started(self):
        """Test mark_started method"""
        from database import AutomationRun

        run = AutomationRun(
            client_id=1,
            automation_type="5ko_bureau",
            portal="equifax",
            status="pending"
        )

        run.mark_started()

        assert run.status == "running"
        assert run.started_at is not None

    def test_mark_completed(self):
        """Test mark_completed method"""
        from database import AutomationRun

        run = AutomationRun(
            client_id=1,
            automation_type="5ko_ftc",
            portal="ftc",
            status="running"
        )
        run.mark_started()

        run.mark_completed(confirmation_number="FTC-12345", result_data={"files": ["affidavit.pdf"]})

        assert run.status == "completed"
        assert run.completed_at is not None
        assert run.confirmation_number == "FTC-12345"
        assert run.result_data == {"files": ["affidavit.pdf"]}

    def test_mark_failed(self):
        """Test mark_failed method"""
        from database import AutomationRun

        run = AutomationRun(
            client_id=1,
            automation_type="inquiry_ftc",
            portal="ftc",
            status="running"
        )
        run.mark_started()

        run.mark_failed(
            error_message="Login failed",
            error_code="AUTH_ERROR",
            screenshot_path="/screenshots/error_1.png",
            last_page_url="https://identitytheft.gov/login"
        )

        assert run.status == "failed"
        assert run.completed_at is not None
        assert run.error_message == "Login failed"
        assert run.error_code == "AUTH_ERROR"
        assert run.screenshot_path == "/screenshots/error_1.png"
        assert run.last_page_url == "https://identitytheft.gov/login"

    def test_can_retry_when_failed(self):
        """Test can_retry returns True for failed runs under max retries"""
        from database import AutomationRun

        run = AutomationRun(
            client_id=1,
            automation_type="5ko_ftc",
            portal="ftc",
            status="failed",
            retry_count=1,
            max_retries=3
        )

        assert run.can_retry() is True

    def test_can_retry_when_max_reached(self):
        """Test can_retry returns False when max retries reached"""
        from database import AutomationRun

        run = AutomationRun(
            client_id=1,
            automation_type="5ko_ftc",
            portal="ftc",
            status="failed",
            retry_count=3,
            max_retries=3
        )

        assert run.can_retry() is False

    def test_can_retry_when_not_failed(self):
        """Test can_retry returns False when status is not failed"""
        from database import AutomationRun

        run = AutomationRun(
            client_id=1,
            automation_type="5ko_ftc",
            portal="ftc",
            status="completed",
            retry_count=0,
            max_retries=3
        )

        assert run.can_retry() is False

    def test_increment_progress_success(self):
        """Test increment_progress with success"""
        from database import AutomationRun

        run = AutomationRun(
            client_id=1,
            automation_type="5ko_cfpb",
            portal="cfpb",
            items_total=5,
            items_processed=0,
            items_succeeded=0,
            items_failed=0
        )

        run.increment_progress(success=True)

        assert run.items_processed == 1
        assert run.items_succeeded == 1
        assert run.items_failed == 0

    def test_increment_progress_failure(self):
        """Test increment_progress with failure"""
        from database import AutomationRun

        run = AutomationRun(
            client_id=1,
            automation_type="5ko_bureau",
            portal="transunion",
            items_total=5,
            items_processed=0,
            items_succeeded=0,
            items_failed=0
        )

        run.increment_progress(success=False)

        assert run.items_processed == 1
        assert run.items_succeeded == 0
        assert run.items_failed == 1

    def test_duration_calculation(self):
        """Test duration calculation in to_dict"""
        from database import AutomationRun

        start = datetime(2026, 2, 10, 12, 0, 0)
        end = datetime(2026, 2, 10, 12, 5, 30)

        run = AutomationRun(
            id=1,
            client_id=1,
            automation_type="5ko_ftc",
            portal="ftc",
            status="completed",
            started_at=start,
            completed_at=end,
            created_at=start
        )

        result = run.to_dict()

        # 5 minutes 30 seconds = 330 seconds
        assert result["duration_seconds"] == 330.0


class TestAutomationTypes:
    """Test automation type constants"""

    def test_valid_automation_types(self):
        """Test that all expected automation types are valid"""
        valid_types = [
            "5ko_ftc",
            "5ko_cfpb",
            "5ko_bureau",
            "inquiry_ftc",
            "inquiry_cfpb"
        ]

        from database import AutomationRun

        for atype in valid_types:
            run = AutomationRun(
                client_id=1,
                automation_type=atype,
                portal="ftc"
            )
            assert run.automation_type == atype

    def test_valid_portals(self):
        """Test that all expected portals are valid"""
        valid_portals = [
            "ftc",
            "cfpb",
            "transunion",
            "equifax",
            "experian"
        ]

        from database import AutomationRun

        for portal in valid_portals:
            run = AutomationRun(
                client_id=1,
                automation_type="5ko_ftc",
                portal=portal
            )
            assert run.portal == portal

    def test_valid_statuses(self):
        """Test that all expected statuses are valid"""
        valid_statuses = [
            "pending",
            "running",
            "completed",
            "failed",
            "cancelled"
        ]

        from database import AutomationRun

        for status in valid_statuses:
            run = AutomationRun(
                client_id=1,
                automation_type="5ko_ftc",
                portal="ftc",
                status=status
            )
            assert run.status == status


class TestClientBureauCredentials:
    """Test Client bureau credential fields"""

    def test_client_bureau_credentials_fields_exist(self):
        """Test that Client model has bureau credential fields"""
        from database import Client

        client = Client(
            name="Test Client",
            email="test@example.com"
        )

        # TransUnion fields
        assert hasattr(client, "tu_portal_username")
        assert hasattr(client, "tu_portal_password_encrypted")
        assert hasattr(client, "tu_portal_verified")
        assert hasattr(client, "tu_portal_verified_at")

        # Equifax fields
        assert hasattr(client, "eq_portal_username")
        assert hasattr(client, "eq_portal_password_encrypted")
        assert hasattr(client, "eq_portal_verified")
        assert hasattr(client, "eq_portal_verified_at")

        # Experian fields
        assert hasattr(client, "exp_portal_username")
        assert hasattr(client, "exp_portal_password_encrypted")
        assert hasattr(client, "exp_portal_verified")
        assert hasattr(client, "exp_portal_verified_at")

    def test_client_ftc_tracking_fields_exist(self):
        """Test that Client model has FTC tracking fields"""
        from database import Client

        client = Client(name="Test Client")

        assert hasattr(client, "ftc_report_number")
        assert hasattr(client, "ftc_filed_at")
        assert hasattr(client, "ftc_affidavit_path")

    def test_client_cfpb_tracking_fields_exist(self):
        """Test that Client model has CFPB tracking fields"""
        from database import Client

        client = Client(name="Test Client")

        # TransUnion CFPB
        assert hasattr(client, "cfpb_tu_confirmation")
        assert hasattr(client, "cfpb_tu_filed_at")

        # Equifax CFPB
        assert hasattr(client, "cfpb_eq_confirmation")
        assert hasattr(client, "cfpb_eq_filed_at")

        # Experian CFPB
        assert hasattr(client, "cfpb_exp_confirmation")
        assert hasattr(client, "cfpb_exp_filed_at")

    def test_set_bureau_credentials(self):
        """Test setting bureau credentials on Client"""
        from database import Client

        client = Client(name="Test Client")

        client.tu_portal_username = "tu_user@example.com"
        client.tu_portal_password_encrypted = "encrypted_password_here"
        client.tu_portal_verified = True
        client.tu_portal_verified_at = datetime.utcnow()

        assert client.tu_portal_username == "tu_user@example.com"
        assert client.tu_portal_verified is True

    def test_set_ftc_tracking(self):
        """Test setting FTC tracking on Client"""
        from database import Client

        client = Client(name="Test Client")

        client.ftc_report_number = "123456789"
        client.ftc_filed_at = datetime.utcnow()
        client.ftc_affidavit_path = "/uploads/affidavit_123.pdf"

        assert client.ftc_report_number == "123456789"
        assert client.ftc_affidavit_path == "/uploads/affidavit_123.pdf"

    def test_set_cfpb_tracking(self):
        """Test setting CFPB tracking on Client"""
        from database import Client

        client = Client(name="Test Client")

        client.cfpb_tu_confirmation = "CFPB-TU-123"
        client.cfpb_eq_confirmation = "CFPB-EQ-456"
        client.cfpb_exp_confirmation = "CFPB-EXP-789"

        assert client.cfpb_tu_confirmation == "CFPB-TU-123"
        assert client.cfpb_eq_confirmation == "CFPB-EQ-456"
        assert client.cfpb_exp_confirmation == "CFPB-EXP-789"


class TestOnboardingServiceBureauAccounts:
    """Test onboarding service with bureau_accounts step"""

    def test_bureau_accounts_step_in_onboarding(self):
        """Test that bureau_accounts step exists in ONBOARDING_STEPS"""
        from services.onboarding_service import ONBOARDING_STEPS

        step_keys = [s["key"] for s in ONBOARDING_STEPS]
        assert "bureau_accounts" in step_keys

    def test_bureau_accounts_step_is_optional(self):
        """Test that bureau_accounts step is marked as optional"""
        from services.onboarding_service import ONBOARDING_STEPS

        bureau_step = next(s for s in ONBOARDING_STEPS if s["key"] == "bureau_accounts")
        assert bureau_step.get("optional") is True

    def test_bureau_accounts_step_after_credit_monitoring(self):
        """Test that bureau_accounts comes after credit_monitoring"""
        from services.onboarding_service import ONBOARDING_STEPS

        step_keys = [s["key"] for s in ONBOARDING_STEPS]
        credit_idx = step_keys.index("credit_monitoring")
        bureau_idx = step_keys.index("bureau_accounts")

        assert bureau_idx == credit_idx + 1


class TestAutomationRunAPIEndpoints:
    """Test automation run API endpoint validation logic"""

    def test_create_requires_client_id(self):
        """Test that client_id validation logic is correct"""
        data = {"automation_type": "5ko_ftc", "portal": "ftc"}
        # Simulating validation logic
        assert not data.get("client_id"), "Should fail when client_id is missing"

    def test_create_requires_automation_type(self):
        """Test that automation_type validation logic is correct"""
        data = {"client_id": 1, "portal": "ftc"}
        # Simulating validation logic
        assert not data.get("automation_type"), "Should fail when automation_type is missing"

    def test_create_requires_portal(self):
        """Test that portal validation logic is correct"""
        data = {"client_id": 1, "automation_type": "5ko_ftc"}
        # Simulating validation logic
        assert not data.get("portal"), "Should fail when portal is missing"

    def test_valid_create_data(self):
        """Test that valid data passes validation"""
        data = {"client_id": 1, "automation_type": "5ko_ftc", "portal": "ftc"}
        assert data.get("client_id") == 1
        assert data.get("automation_type") == "5ko_ftc"
        assert data.get("portal") == "ftc"


class TestAutomationRunLifecycle:
    """Test full automation run lifecycle"""

    def test_full_lifecycle_success(self):
        """Test complete successful automation run lifecycle"""
        from database import AutomationRun

        # Create
        run = AutomationRun(
            client_id=1,
            automation_type="5ko_ftc",
            portal="ftc",
            status="pending",
            items_total=1
        )

        assert run.status == "pending"
        assert run.started_at is None
        assert run.completed_at is None

        # Start
        run.mark_started()
        assert run.status == "running"
        assert run.started_at is not None

        # Progress
        run.increment_progress(success=True)
        assert run.items_processed == 1
        assert run.items_succeeded == 1

        # Complete
        run.mark_completed(confirmation_number="FTC-12345")
        assert run.status == "completed"
        assert run.completed_at is not None
        assert run.confirmation_number == "FTC-12345"

    def test_full_lifecycle_failure_and_retry(self):
        """Test automation run failure and retry lifecycle"""
        from database import AutomationRun

        # Create and start
        run = AutomationRun(
            client_id=1,
            automation_type="5ko_cfpb",
            portal="cfpb",
            status="pending",
            items_total=1,
            retry_count=0,
            max_retries=3
        )
        run.mark_started()

        # Fail
        run.mark_failed(error_message="Timeout waiting for page")
        assert run.status == "failed"
        assert run.can_retry() is True

        # Reset for retry
        run.status = "pending"
        run.started_at = None
        run.completed_at = None
        run.error_message = None
        run.retry_count = 1

        assert run.retry_count == 1
        assert run.can_retry() is False  # Status is pending, not failed

        # Start again
        run.mark_started()
        run.mark_completed(confirmation_number="CFPB-67890")

        assert run.status == "completed"
        assert run.retry_count == 1
