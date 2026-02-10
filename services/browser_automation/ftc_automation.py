"""
FTC Identity Theft Portal Automation (identitytheft.gov)

Automates the filing of identity theft reports for 5-Day Knockout and Inquiry Disputes.
Files ONE item per submission (not batch).
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_automation import AutomationError, AutomationResult, BaseAutomation

logger = logging.getLogger(__name__)


class FTCAutomation(BaseAutomation):
    """
    Automates FTC Identity Theft Report filing at identitytheft.gov

    Flow (6 Steps):
    1. Select "Someone used my info to open accounts"
    2. Fill victim info (name, address, SSN last 4, DOB, contact)
    3. Add fraudulent account details (one item)
    4. Review and submit
    5. Capture FTC report number
    6. Download affidavit PDF

    For 5KO: Files identity theft report for fraudulent accounts
    For Inquiry Disputes: Files identity theft report for unauthorized inquiries
    """

    FTC_REPORT_URL = "https://www.identitytheft.gov/Assistant"

    def __init__(
        self,
        client_id: int,
        staff_id: int = None,
        headless: bool = False,
        timeout: int = 120,
        anthropic_api_key: str = None,
    ):
        super().__init__(
            client_id=client_id,
            staff_id=staff_id,
            headless=headless,
            timeout=timeout,
            anthropic_api_key=anthropic_api_key,
        )
        self.report_number = None
        self.affidavit_path = None

    async def file_identity_theft_report(
        self,
        account: Dict[str, Any],
        is_inquiry: bool = False,
    ) -> AutomationResult:
        """
        File an FTC identity theft report for a single account or inquiry.

        Args:
            account: Dictionary with account details:
                - creditor_name: Name of the creditor
                - account_number: Account number (can be partial)
                - account_type: Type of account (credit_card, loan, etc.)
                - date_opened: When the fraudulent account was opened
                - balance: Current balance (optional)
                - bureaus: List of bureaus reporting this account
            is_inquiry: True if this is an inquiry dispute, False for account dispute

        Returns:
            AutomationResult with report number and affidavit path
        """
        start_time = datetime.utcnow()

        # Create automation run record
        automation_type = "inquiry_ftc" if is_inquiry else "5ko_ftc"
        self.create_automation_run(automation_type, "ftc")
        self.mark_run_started()

        try:
            # Get client data
            client = self.get_client_data()

            # Build the task description for the LLM
            if is_inquiry:
                item_description = f"unauthorized hard inquiry from {account.get('creditor_name', 'Unknown')}"
                task_type = "unauthorized inquiry"
            else:
                item_description = f"fraudulent {account.get('account_type', 'account')} from {account.get('creditor_name', 'Unknown')}"
                task_type = "fraudulent account"

            # Step 1: Navigate and start report
            task_1 = f"""
            Navigate to {self.FTC_REPORT_URL}

            On the FTC Identity Theft Report page:
            1. If there's a "Get Started" or "Start" button, click it
            2. Select "Someone used my info to open accounts or for other fraud" or similar option
            3. Continue to the next step

            Wait for the page to load completely before proceeding.
            """
            await self.run_task(task_1, max_steps=10)
            await self.take_screenshot("step1_start")

            # Step 2: Fill victim information
            task_2 = f"""
            Fill in the victim's personal information:

            - First Name: {client.get('name', '').split()[0] if client.get('name') else ''}
            - Last Name: {client.get('name', '').split()[-1] if client.get('name') and len(client.get('name', '').split()) > 1 else ''}
            - Date of Birth: {client.get('dob', '')}
            - SSN Last 4: {client.get('ssn_last_4', '')}
            - Address: {client.get('address', '')}
            - City: {client.get('city', '')}
            - State: {client.get('state', '')}
            - ZIP Code: {client.get('zip_code', '')}
            - Phone: {client.get('phone', '')}
            - Email: {client.get('email', '')}

            Fill in all available fields and click Continue/Next to proceed.
            """
            await self.run_task(task_2, max_steps=15)
            await self.take_screenshot("step2_victim_info")

            # Step 3: Add the fraudulent account/inquiry
            account_details = self._format_account_details(account, is_inquiry)
            task_3 = f"""
            Add the {task_type} details:

            {account_details}

            Look for:
            - "Add account" or "Add item" button
            - Fields for creditor/company name, account number, account type
            - Date fields for when the fraud occurred
            - Amount/balance fields if applicable

            Fill in the information and save/add the item.
            Then click Continue/Next to proceed.
            """
            await self.run_task(task_3, max_steps=15)
            await self.take_screenshot("step3_account_details")

            # Step 4: Review and submit
            task_4 = """
            Review the information entered:

            1. Check that all the victim information is correct
            2. Check that the fraudulent account/inquiry details are correct
            3. If there are any checkboxes for certifying the information is true, check them
            4. Look for and click the "Submit" or "File Report" button

            Make sure to complete any required certifications before submitting.
            """
            await self.run_task(task_4, max_steps=10)
            await self.take_screenshot("step4_review")

            # Step 5: Capture report number
            task_5 = """
            After submission, the page should show a confirmation with:
            - FTC Report Number (a long number, usually 9+ digits)
            - Confirmation message

            IMPORTANT: Find and note the FTC Report Number displayed on the screen.
            This number is critical and starts with numbers like "456..." or similar.

            Look for text like "Your FTC Report Number is:" or "Report #:" or "Confirmation Number:"
            """
            result_5 = await self.run_task(task_5, max_steps=10)
            screenshot_5 = await self.take_screenshot("step5_confirmation")

            # Extract report number from result
            self.report_number = self._extract_report_number(result_5)

            # Step 6: Download affidavit PDF
            task_6 = """
            Look for a button or link to download the Identity Theft Affidavit PDF:

            - Look for "Download Affidavit" or "Download PDF" or "Print" button
            - The affidavit is an official document needed for disputes
            - Click to download the PDF

            If there's no download option visible, look for a "Get your documents" section.
            """
            await self.run_task(task_6, max_steps=10)
            await self.take_screenshot("step6_affidavit")

            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()

            # Update client tracking fields
            if self.report_number:
                self.update_client_tracking("ftc_report_number", self.report_number)
                self.update_client_tracking("ftc_filed_at", datetime.utcnow())

            # Mark run as completed
            self.mark_run_completed(
                confirmation_number=self.report_number,
                result_data={
                    "account": account,
                    "is_inquiry": is_inquiry,
                    "affidavit_downloaded": self.affidavit_path is not None,
                },
            )

            return AutomationResult(
                success=True,
                message=f"FTC identity theft report filed successfully for {account.get('creditor_name', 'account')}",
                confirmation_number=self.report_number,
                data={
                    "report_number": self.report_number,
                    "affidavit_path": self.affidavit_path,
                    "account": account,
                    "is_inquiry": is_inquiry,
                },
                screenshot_path=screenshot_5,
                duration_seconds=duration,
            )

        except AutomationError as e:
            self.mark_run_failed(e.message, e.error_code, e.screenshot_path)
            raise
        except Exception as e:
            screenshot = await self.take_screenshot("error")
            error_msg = f"FTC automation failed: {str(e)}"
            self.mark_run_failed(error_msg, "UNEXPECTED_ERROR", screenshot)
            raise AutomationError(error_msg, "UNEXPECTED_ERROR", screenshot)

    def _format_account_details(self, account: Dict[str, Any], is_inquiry: bool) -> str:
        """Format account details for the LLM task"""
        if is_inquiry:
            return f"""
            Type: Unauthorized Hard Inquiry
            Creditor/Company: {account.get('creditor_name', 'Unknown')}
            Date of Inquiry: {account.get('inquiry_date', account.get('date_opened', 'Unknown'))}
            Bureaus Reporting: {', '.join(account.get('bureaus', ['Unknown']))}

            Note: I did NOT authorize this company to pull my credit report.
            """
        else:
            return f"""
            Type: Fraudulent {account.get('account_type', 'Account')}
            Creditor/Company: {account.get('creditor_name', 'Unknown')}
            Account Number: {account.get('account_number', 'Unknown')} (may be partial)
            Date Opened: {account.get('date_opened', 'Unknown')}
            Balance: ${account.get('balance', 'Unknown')}
            Bureaus Reporting: {', '.join(account.get('bureaus', ['Unknown']))}

            Note: I did NOT open this account. This is identity theft.
            """

    def _extract_report_number(self, result: Dict[str, Any]) -> Optional[str]:
        """
        Extract the FTC report number from the automation result.

        The report number is typically a 9-15 digit number.
        """
        import re

        # Try to find the report number in the result text
        if result and isinstance(result, dict):
            result_text = str(result)

            # Common patterns for FTC report numbers
            patterns = [
                r"Report\s*#?\s*:?\s*(\d{9,15})",
                r"FTC\s*Report\s*Number\s*:?\s*(\d{9,15})",
                r"Confirmation\s*#?\s*:?\s*(\d{9,15})",
                r"Reference\s*#?\s*:?\s*(\d{9,15})",
                r"(\d{9,15})",  # Fallback: any long number
            ]

            for pattern in patterns:
                match = re.search(pattern, result_text, re.IGNORECASE)
                if match:
                    return match.group(1)

        return None

    async def check_existing_report(self) -> Optional[str]:
        """
        Check if the client already has an FTC report number.

        Returns:
            Existing report number or None
        """
        client = self.get_client_data()
        return client.get("ftc_report_number")

    async def file_multiple_items(
        self,
        items: List[Dict[str, Any]],
        is_inquiry: bool = False,
        delay_seconds: int = 30,
    ) -> List[AutomationResult]:
        """
        File FTC reports for multiple items (one at a time).

        Args:
            items: List of account/inquiry dictionaries
            is_inquiry: True for inquiry disputes
            delay_seconds: Delay between submissions to avoid rate limiting

        Returns:
            List of AutomationResult objects
        """
        results = []

        for i, item in enumerate(items):
            logger.info(
                f"Filing FTC report {i+1}/{len(items)} for {item.get('creditor_name', 'item')}"
            )

            try:
                result = await self.file_identity_theft_report(item, is_inquiry)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to file FTC report for item {i+1}: {e}")
                results.append(
                    AutomationResult(
                        success=False,
                        message=str(e),
                        error_code="FTC_FILING_FAILED",
                    )
                )

            # Delay between submissions
            if i < len(items) - 1:
                logger.info(f"Waiting {delay_seconds}s before next submission...")
                await asyncio.sleep(delay_seconds)

        return results


async def run_ftc_automation(
    client_id: int,
    account: Dict[str, Any],
    staff_id: int = None,
    is_inquiry: bool = False,
    headless: bool = False,
) -> AutomationResult:
    """
    Convenience function to run FTC automation.

    Args:
        client_id: The client ID
        account: Account details dictionary
        staff_id: Staff member who initiated
        is_inquiry: True for inquiry dispute
        headless: Run in headless mode

    Returns:
        AutomationResult
    """
    async with FTCAutomation(
        client_id=client_id,
        staff_id=staff_id,
        headless=headless,
    ) as automation:
        return await automation.file_identity_theft_report(account, is_inquiry)
