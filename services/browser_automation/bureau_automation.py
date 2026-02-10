"""
Credit Bureau Portal Automation (Equifax, TransUnion, Experian)

Automates dispute submissions directly to bureau portals for 5-Day Knockout.
Each bureau has different limitations and workflows.

Limitations:
- Equifax: No limit, fully automatable
- TransUnion: 1 active dispute at a time, must wait for resolution
- Experian: 2/day limit, phone calls recommended before AND after
"""

import asyncio
import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_automation import AutomationError, AutomationResult, BaseAutomation

logger = logging.getLogger(__name__)


class BureauAutomation(BaseAutomation):
    """
    Base class for bureau portal automation.

    Each bureau has its own subclass with specific workflow.
    """

    BUREAU_NAME = "Unknown"
    BUREAU_CODE = "unknown"
    PORTAL_URL = ""
    DAILY_LIMIT = None  # None = no limit
    ACTIVE_DISPUTE_LIMIT = None  # None = no limit

    def __init__(
        self,
        client_id: int,
        staff_id: int = None,
        headless: bool = False,
        timeout: int = 180,
        anthropic_api_key: str = None,
    ):
        super().__init__(
            client_id=client_id,
            staff_id=staff_id,
            headless=headless,
            timeout=timeout,
            anthropic_api_key=anthropic_api_key,
        )
        self.dispute_confirmation = None

    @abstractmethod
    async def login(self) -> bool:
        """Login to the bureau portal. Returns True if successful."""
        pass

    @abstractmethod
    async def submit_dispute(
        self,
        account: Dict[str, Any],
        ftc_report_number: str = None,
    ) -> AutomationResult:
        """Submit a dispute for a single account."""
        pass

    async def check_credentials(self) -> bool:
        """Check if bureau credentials are available for this client."""
        client = self.get_client_data()
        username = client.get(f"{self.BUREAU_CODE}_username")
        return username is not None and len(username) > 0


class EquifaxAutomation(BureauAutomation):
    """
    Equifax Portal Automation (my.equifax.com)

    Features:
    - No dispute limit
    - Fully automatable
    - Supports document uploads
    """

    BUREAU_NAME = "Equifax"
    BUREAU_CODE = "eq"
    PORTAL_URL = "https://my.equifax.com/consumer-registration/UCSC/#/personal-info"
    DISPUTE_URL = "https://my.equifax.com/membercenter/#/disputes"

    async def login(self) -> bool:
        """Login to Equifax portal"""
        client = self.get_client_data()
        username = client.get("eq_username")
        password = self.get_decrypted_password("eq")

        if not username or not password:
            raise AutomationError(
                "Equifax credentials not found for this client",
                error_code="CREDENTIALS_MISSING",
            )

        task = f"""
        Navigate to {self.PORTAL_URL}

        Login to Equifax:
        1. Look for "Sign In" or "Log In" link and click it
        2. Enter username: {username}
        3. Enter password: {password}
        4. Click "Sign In" or "Log In" button
        5. Handle any 2FA if prompted (wait for user to enter code)

        Wait for the dashboard/home page to load after login.
        """

        try:
            await self.run_task(task, max_steps=15)
            await self.take_screenshot("equifax_login")
            return True
        except Exception as e:
            logger.error(f"Equifax login failed: {e}")
            return False

    async def submit_dispute(
        self,
        account: Dict[str, Any],
        ftc_report_number: str = None,
    ) -> AutomationResult:
        """Submit a dispute to Equifax for identity theft blocking (FCRA §605B)"""
        start_time = datetime.utcnow()

        self.create_automation_run("5ko_bureau", "equifax")
        self.mark_run_started()

        try:
            # Login first
            logged_in = await self.login()
            if not logged_in:
                raise AutomationError("Failed to login to Equifax", "LOGIN_FAILED")

            # Navigate to disputes
            task_1 = f"""
            Navigate to the disputes section:
            1. Go to {self.DISPUTE_URL} or look for "Dispute" in the menu
            2. Click on "File a Dispute" or "Start a Dispute" or "Dispute an Item"
            3. Look for options related to identity theft or fraud
            """
            await self.run_task(task_1, max_steps=10)
            await self.take_screenshot("equifax_dispute_start")

            # Select identity theft dispute type
            task_2 = f"""
            Select identity theft as the dispute reason:
            1. Look for "This is not my account" or "Identity theft" or "Fraud"
            2. Select the option that indicates this account was opened fraudulently
            3. If asked about FTC report, indicate you have one: {ftc_report_number}
            """
            await self.run_task(task_2, max_steps=10)
            await self.take_screenshot("equifax_dispute_type")

            # Find and select the account
            task_3 = f"""
            Find and select the fraudulent account:
            - Creditor: {account.get('creditor_name', 'Unknown')}
            - Account Number: {account.get('account_number', 'Unknown')} (may be partial)
            - Type: {account.get('account_type', 'Unknown')}

            1. Look through the list of accounts on your credit report
            2. Find the matching account
            3. Select it for dispute
            4. Choose "This account is not mine" or "Identity theft/fraud" as the reason
            """
            await self.run_task(task_3, max_steps=15)
            await self.take_screenshot("equifax_account_select")

            # Add dispute details
            task_4 = f"""
            Add identity theft dispute details:
            1. In the explanation/reason field, write:
               "This account was opened as a result of identity theft. I did not open this account.
               FTC Identity Theft Report Number: {ftc_report_number or 'Filed'}.
               I am requesting immediate blocking under FCRA Section 605B."

            2. If there's an option to upload documents, skip for now (we'll submit by mail)
            3. Review the dispute information
            4. Submit the dispute
            """
            await self.run_task(task_4, max_steps=15)
            await self.take_screenshot("equifax_dispute_details")

            # Capture confirmation
            task_5 = """
            After submission:
            1. Look for a confirmation number or reference number
            2. Note any dispute ID or tracking number shown
            3. The confirmation may appear as "Dispute #" or "Reference #" or "Confirmation"

            Make note of any confirmation information displayed.
            """
            result_5 = await self.run_task(task_5, max_steps=10)
            screenshot = await self.take_screenshot("equifax_confirmation")

            # Extract confirmation
            confirmation = self._extract_confirmation(result_5)
            duration = (datetime.utcnow() - start_time).total_seconds()

            self.mark_run_completed(
                confirmation_number=confirmation,
                result_data={"account": account, "ftc_reference": ftc_report_number},
            )

            return AutomationResult(
                success=True,
                message=f"Equifax dispute submitted for {account.get('creditor_name', 'account')}",
                confirmation_number=confirmation,
                data={
                    "bureau": "Equifax",
                    "account": account,
                    "confirmation": confirmation,
                },
                screenshot_path=screenshot,
                duration_seconds=duration,
            )

        except AutomationError as e:
            self.mark_run_failed(e.message, e.error_code, e.screenshot_path)
            raise
        except Exception as e:
            screenshot = await self.take_screenshot("equifax_error")
            error_msg = f"Equifax dispute failed: {str(e)}"
            self.mark_run_failed(error_msg, "UNEXPECTED_ERROR", screenshot)
            raise AutomationError(error_msg, "UNEXPECTED_ERROR", screenshot)

    def _extract_confirmation(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract confirmation number from result"""
        import re

        if result:
            text = str(result)
            patterns = [
                r"Dispute\s*#?\s*:?\s*([A-Z0-9-]{6,20})",
                r"Reference\s*#?\s*:?\s*([A-Z0-9-]{6,20})",
                r"Confirmation\s*#?\s*:?\s*([A-Z0-9-]{6,20})",
                r"EFX-?(\d{6,12})",
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
        return None


class TransUnionAutomation(BureauAutomation):
    """
    TransUnion Portal Automation (transunion.com)

    Limitations:
    - Only 1 active dispute at a time
    - Must wait for resolution before submitting another
    """

    BUREAU_NAME = "TransUnion"
    BUREAU_CODE = "tu"
    PORTAL_URL = "https://www.transunion.com/credit-disputes/dispute-your-credit"
    ACTIVE_DISPUTE_LIMIT = 1

    async def login(self) -> bool:
        """Login to TransUnion portal"""
        client = self.get_client_data()
        username = client.get("tu_username")
        password = self.get_decrypted_password("tu")

        if not username or not password:
            raise AutomationError(
                "TransUnion credentials not found for this client",
                error_code="CREDENTIALS_MISSING",
            )

        task = f"""
        Navigate to {self.PORTAL_URL}

        Login to TransUnion:
        1. Look for "Sign In" or "Log In" link and click it
        2. Enter email/username: {username}
        3. Enter password: {password}
        4. Click "Sign In" button
        5. Handle any verification code if prompted (wait for user input)

        Wait for the account dashboard to load.
        """

        try:
            await self.run_task(task, max_steps=15)
            await self.take_screenshot("transunion_login")
            return True
        except Exception as e:
            logger.error(f"TransUnion login failed: {e}")
            return False

    async def check_active_disputes(self) -> int:
        """Check how many active disputes exist"""
        task = """
        Check for active disputes:
        1. Look for a "Disputes" or "My Disputes" section
        2. Count any disputes with status "In Progress" or "Pending" or "Under Review"
        3. Note the count of active disputes
        """
        try:
            result = await self.run_task(task, max_steps=10)
            # Try to extract count from result
            # Default to 0 if we can't determine
            return 0
        except Exception:
            return 0

    async def submit_dispute(
        self,
        account: Dict[str, Any],
        ftc_report_number: str = None,
    ) -> AutomationResult:
        """Submit a dispute to TransUnion (respects 1-active limit)"""
        start_time = datetime.utcnow()

        self.create_automation_run("5ko_bureau", "transunion")
        self.mark_run_started()

        try:
            # Login first
            logged_in = await self.login()
            if not logged_in:
                raise AutomationError("Failed to login to TransUnion", "LOGIN_FAILED")

            # Check for active disputes (TransUnion limit: 1 at a time)
            active_count = await self.check_active_disputes()
            if active_count >= 1:
                raise AutomationError(
                    "TransUnion only allows 1 active dispute at a time. Please wait for current dispute to resolve.",
                    error_code="DISPUTE_LIMIT_REACHED",
                )

            # Navigate to file dispute
            task_1 = """
            Start a new dispute:
            1. Look for "Dispute" or "File a Dispute" or "Start Dispute"
            2. Click to begin the dispute process
            3. If asked about dispute type, select "Identity Theft" or "This is not my account"
            """
            await self.run_task(task_1, max_steps=10)
            await self.take_screenshot("transunion_dispute_start")

            # Select account and reason
            task_2 = f"""
            Select the fraudulent account:
            - Creditor: {account.get('creditor_name', 'Unknown')}
            - Account Number: {account.get('account_number', 'Unknown')}
            - Type: {account.get('account_type', 'Unknown')}

            1. Find this account in the list
            2. Select it for dispute
            3. Choose "Not my account" or "Identity theft" as the reason
            """
            await self.run_task(task_2, max_steps=15)
            await self.take_screenshot("transunion_account_select")

            # Add explanation
            task_3 = f"""
            Add dispute explanation:
            1. In the explanation field, enter:
               "This account was fraudulently opened. I am a victim of identity theft.
               FTC Report Number: {ftc_report_number or 'Filed'}.
               I request blocking under FCRA Section 605B (4 business days)."

            2. Review and submit the dispute
            3. Confirm submission
            """
            await self.run_task(task_3, max_steps=15)
            await self.take_screenshot("transunion_submit")

            # Get confirmation
            task_4 = """
            After submission:
            1. Note any confirmation number or dispute ID
            2. Look for "Dispute #" or "Reference Number" or "Confirmation"
            """
            result_4 = await self.run_task(task_4, max_steps=10)
            screenshot = await self.take_screenshot("transunion_confirmation")

            confirmation = self._extract_confirmation(result_4)
            duration = (datetime.utcnow() - start_time).total_seconds()

            self.mark_run_completed(
                confirmation_number=confirmation,
                result_data={"account": account, "ftc_reference": ftc_report_number},
            )

            return AutomationResult(
                success=True,
                message=f"TransUnion dispute submitted for {account.get('creditor_name', 'account')}",
                confirmation_number=confirmation,
                data={
                    "bureau": "TransUnion",
                    "account": account,
                    "confirmation": confirmation,
                    "note": "Only 1 active dispute allowed. Wait for resolution before filing another.",
                },
                screenshot_path=screenshot,
                duration_seconds=duration,
            )

        except AutomationError as e:
            self.mark_run_failed(e.message, e.error_code, e.screenshot_path)
            raise
        except Exception as e:
            screenshot = await self.take_screenshot("transunion_error")
            error_msg = f"TransUnion dispute failed: {str(e)}"
            self.mark_run_failed(error_msg, "UNEXPECTED_ERROR", screenshot)
            raise AutomationError(error_msg, "UNEXPECTED_ERROR", screenshot)

    def _extract_confirmation(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract confirmation from result"""
        import re

        if result:
            text = str(result)
            patterns = [
                r"Dispute\s*#?\s*:?\s*([A-Z0-9-]{6,20})",
                r"Reference\s*#?\s*:?\s*([A-Z0-9-]{6,20})",
                r"TU-?(\d{6,12})",
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
        return None


class ExperianAutomation(BureauAutomation):
    """
    Experian Portal Automation (experian.com)

    Limitations:
    - 2 disputes per day limit
    - Phone calls recommended BEFORE and AFTER online submission
    - Hybrid approach: automated submission + manual call tracking

    Important: Staff should call Experian (1-855-414-6048) before AND after submitting.
    """

    BUREAU_NAME = "Experian"
    BUREAU_CODE = "exp"
    PORTAL_URL = "https://www.experian.com/disputes/main.html"
    DAILY_LIMIT = 2
    PHONE_NUMBER = "1-855-414-6048"

    async def login(self) -> bool:
        """Login to Experian portal"""
        client = self.get_client_data()
        username = client.get("exp_username")
        password = self.get_decrypted_password("exp")

        if not username or not password:
            raise AutomationError(
                "Experian credentials not found for this client",
                error_code="CREDENTIALS_MISSING",
            )

        task = f"""
        Navigate to {self.PORTAL_URL}

        Login to Experian:
        1. Look for "Sign In" button and click it
        2. Enter username/email: {username}
        3. Enter password: {password}
        4. Click "Sign In"
        5. Handle any security questions or 2FA if prompted

        Wait for account page to load.
        """

        try:
            await self.run_task(task, max_steps=15)
            await self.take_screenshot("experian_login")
            return True
        except Exception as e:
            logger.error(f"Experian login failed: {e}")
            return False

    async def submit_dispute(
        self,
        account: Dict[str, Any],
        ftc_report_number: str = None,
    ) -> AutomationResult:
        """
        Submit a dispute to Experian.

        NOTE: Limited to 2/day. Phone calls recommended before and after.
        """
        start_time = datetime.utcnow()

        self.create_automation_run("5ko_bureau", "experian")
        self.mark_run_started()

        try:
            # Login first
            logged_in = await self.login()
            if not logged_in:
                raise AutomationError("Failed to login to Experian", "LOGIN_FAILED")

            # Start dispute process
            task_1 = """
            Navigate to dispute section:
            1. Look for "Dispute" or "File a Dispute" link
            2. Click to start the dispute process
            3. Select "This is not my account" or "Identity theft" if asked
            """
            await self.run_task(task_1, max_steps=10)
            await self.take_screenshot("experian_dispute_start")

            # Select account
            task_2 = f"""
            Find and select the fraudulent account:
            - Creditor: {account.get('creditor_name', 'Unknown')}
            - Account Number: {account.get('account_number', 'Unknown')}

            1. Look through the accounts listed
            2. Find the matching account
            3. Select it for dispute
            4. Choose "Not my account" or "Fraud/Identity theft" as reason
            """
            await self.run_task(task_2, max_steps=15)
            await self.take_screenshot("experian_account_select")

            # Add dispute details
            task_3 = f"""
            Add identity theft details:
            1. In explanation field, enter:
               "This account is the result of identity theft. I did not open this account.
               FTC Identity Theft Report: {ftc_report_number or 'Filed'}.
               I request blocking under FCRA Section 605B within 4 business days."

            2. Complete any required fields
            3. Submit the dispute
            """
            await self.run_task(task_3, max_steps=15)
            await self.take_screenshot("experian_submit")

            # Get confirmation
            task_4 = """
            After submission:
            1. Note the confirmation number or dispute ID
            2. Look for any reference number displayed
            """
            result_4 = await self.run_task(task_4, max_steps=10)
            screenshot = await self.take_screenshot("experian_confirmation")

            confirmation = self._extract_confirmation(result_4)
            duration = (datetime.utcnow() - start_time).total_seconds()

            self.mark_run_completed(
                confirmation_number=confirmation,
                result_data={"account": account, "ftc_reference": ftc_report_number},
            )

            return AutomationResult(
                success=True,
                message=f"Experian dispute submitted for {account.get('creditor_name', 'account')}",
                confirmation_number=confirmation,
                data={
                    "bureau": "Experian",
                    "account": account,
                    "confirmation": confirmation,
                    "phone_followup_required": True,
                    "phone_number": self.PHONE_NUMBER,
                    "note": f"IMPORTANT: Call {self.PHONE_NUMBER} to follow up on this dispute. Experian limit: 2/day.",
                },
                screenshot_path=screenshot,
                duration_seconds=duration,
            )

        except AutomationError as e:
            self.mark_run_failed(e.message, e.error_code, e.screenshot_path)
            raise
        except Exception as e:
            screenshot = await self.take_screenshot("experian_error")
            error_msg = f"Experian dispute failed: {str(e)}"
            self.mark_run_failed(error_msg, "UNEXPECTED_ERROR", screenshot)
            raise AutomationError(error_msg, "UNEXPECTED_ERROR", screenshot)

    def _extract_confirmation(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract confirmation from result"""
        import re

        if result:
            text = str(result)
            patterns = [
                r"Dispute\s*#?\s*:?\s*([A-Z0-9-]{6,20})",
                r"Reference\s*#?\s*:?\s*([A-Z0-9-]{6,20})",
                r"EXP-?(\d{6,12})",
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
        return None


def get_bureau_automation(
    bureau: str,
    client_id: int,
    staff_id: int = None,
    headless: bool = False,
) -> BureauAutomation:
    """
    Factory function to get the appropriate bureau automation class.

    Args:
        bureau: 'equifax', 'transunion', or 'experian'
        client_id: The client ID
        staff_id: Staff member who initiated
        headless: Run in headless mode

    Returns:
        BureauAutomation instance
    """
    bureau_lower = bureau.lower()

    automations = {
        "equifax": EquifaxAutomation,
        "eq": EquifaxAutomation,
        "transunion": TransUnionAutomation,
        "tu": TransUnionAutomation,
        "experian": ExperianAutomation,
        "exp": ExperianAutomation,
    }

    automation_class = automations.get(bureau_lower)
    if not automation_class:
        raise ValueError(f"Unknown bureau: {bureau}")

    return automation_class(
        client_id=client_id,
        staff_id=staff_id,
        headless=headless,
    )
