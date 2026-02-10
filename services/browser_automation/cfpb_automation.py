"""
CFPB Complaint Portal Automation (consumerfinance.gov/complaint)

Automates the filing of CFPB complaints against credit bureaus
for 5-Day Knockout and Inquiry Disputes.

Files ONE complaint per bureau (TransUnion, Equifax, Experian).
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_automation import AutomationError, AutomationResult, BaseAutomation

logger = logging.getLogger(__name__)


# Bureau names as they appear in CFPB complaint forms
BUREAU_NAMES = {
    "transunion": "TransUnion",
    "equifax": "Equifax",
    "experian": "Experian",
    "tu": "TransUnion",
    "eq": "Equifax",
    "exp": "Experian",
}


class CFPBAutomation(BaseAutomation):
    """
    Automates CFPB Complaint filing at consumerfinance.gov/complaint

    Flow (5 Steps):
    1. Select product type (Credit Reporting)
    2. Select issue (Incorrect information / Improper use)
    3. Fill company (bureau name) + narrative
    4. Fill victim info
    5. Submit and capture confirmation number

    For 5KO: Files complaints about incorrect information
    For Inquiry Disputes: Files complaints about improper use of report
    """

    CFPB_COMPLAINT_URL = "https://www.consumerfinance.gov/complaint/"

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
        self.confirmation_numbers = {}  # bureau -> confirmation number

    async def file_cfpb_complaint(
        self,
        bureau: str,
        account: Dict[str, Any],
        is_inquiry: bool = False,
        ftc_report_number: str = None,
    ) -> AutomationResult:
        """
        File a CFPB complaint against a specific credit bureau.

        Args:
            bureau: The bureau to complain about ('transunion', 'equifax', 'experian')
            account: Dictionary with account/inquiry details
            is_inquiry: True if this is an inquiry dispute
            ftc_report_number: FTC report number to reference

        Returns:
            AutomationResult with confirmation number
        """
        start_time = datetime.utcnow()

        # Normalize bureau name
        bureau_lower = bureau.lower()
        bureau_name = BUREAU_NAMES.get(bureau_lower, bureau)

        # Create automation run record
        automation_type = "inquiry_cfpb" if is_inquiry else "5ko_cfpb"
        self.create_automation_run(automation_type, "cfpb")
        self.mark_run_started()

        try:
            # Get client data
            client = self.get_client_data()

            # Build narrative based on dispute type
            narrative = self._build_complaint_narrative(
                bureau_name, account, is_inquiry, ftc_report_number
            )

            # Step 1: Navigate and select product type
            task_1 = f"""
            Navigate to {self.CFPB_COMPLAINT_URL}

            On the CFPB Complaint page:
            1. Look for "Credit reporting, credit repair services, or other personal consumer reports" option
            2. Select it
            3. Click Continue or Next

            This is for filing a complaint about credit bureau reporting.
            """
            await self.run_task(task_1, max_steps=10)
            await self.take_screenshot(f"cfpb_{bureau_lower}_step1")

            # Step 2: Select issue type
            if is_inquiry:
                issue_task = """
                Select the issue:
                1. Look for "Improper use of your report" or "Problem with a company's investigation"
                2. Or select "Incorrect information on your report"
                3. Then select "Information belongs to someone else" or similar unauthorized inquiry option
                4. Click Continue/Next
                """
            else:
                issue_task = """
                Select the issue:
                1. Look for "Incorrect information on your report"
                2. Select "Information belongs to someone else" or "Account status incorrect" or "Account information incorrect"
                3. This is for reporting fraudulent/incorrect account information
                4. Click Continue/Next
                """

            task_2 = issue_task
            await self.run_task(task_2, max_steps=10)
            await self.take_screenshot(f"cfpb_{bureau_lower}_step2")

            # Step 3: Select company and write narrative
            task_3 = f"""
            Select the company and describe the issue:

            1. Company Name: {bureau_name}
               - Search for "{bureau_name}" in the company field
               - Select the main {bureau_name} company (not a subsidiary)

            2. In the "What happened?" or narrative field, enter:
            {narrative}

            3. Fill in any additional required fields about the issue
            4. Click Continue/Next
            """
            await self.run_task(task_3, max_steps=15)
            await self.take_screenshot(f"cfpb_{bureau_lower}_step3")

            # Step 4: Fill contact information
            task_4 = f"""
            Fill in your contact information:

            - First Name: {client.get('name', '').split()[0] if client.get('name') else ''}
            - Last Name: {client.get('name', '').split()[-1] if client.get('name') and len(client.get('name', '').split()) > 1 else ''}
            - Email: {client.get('email', '')}
            - Phone: {client.get('phone', '')}
            - Address: {client.get('address', '')}
            - City: {client.get('city', '')}
            - State: {client.get('state', '')}
            - ZIP: {client.get('zip_code', '')}

            Fill in all required fields and click Continue/Next.
            """
            await self.run_task(task_4, max_steps=15)
            await self.take_screenshot(f"cfpb_{bureau_lower}_step4")

            # Step 5: Review and submit
            task_5 = """
            Review and submit the complaint:

            1. Review all the information entered
            2. Check any required consent/certification boxes
            3. Look for and click "Submit complaint" or "Submit" button

            After submission, note the confirmation number displayed.
            The confirmation number is usually a long number or alphanumeric code.
            """
            result_5 = await self.run_task(task_5, max_steps=10)
            screenshot_5 = await self.take_screenshot(
                f"cfpb_{bureau_lower}_confirmation"
            )

            # Extract confirmation number
            confirmation = self._extract_confirmation_number(result_5)
            self.confirmation_numbers[bureau_lower] = confirmation

            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()

            # Update client tracking fields
            if confirmation:
                tracking_field = f"cfpb_{bureau_lower[:2] if bureau_lower in ['transunion'] else bureau_lower[:3]}_confirmation"
                # Map to correct field names
                field_map = {
                    "transunion": "cfpb_tu_confirmation",
                    "equifax": "cfpb_eq_confirmation",
                    "experian": "cfpb_exp_confirmation",
                }
                if bureau_lower in field_map:
                    self.update_client_tracking(field_map[bureau_lower], confirmation)
                    self.update_client_tracking(
                        field_map[bureau_lower].replace("_confirmation", "_filed_at"),
                        datetime.utcnow(),
                    )

            # Mark run as completed
            self.mark_run_completed(
                confirmation_number=confirmation,
                result_data={
                    "bureau": bureau_name,
                    "account": account,
                    "is_inquiry": is_inquiry,
                    "ftc_reference": ftc_report_number,
                },
            )

            return AutomationResult(
                success=True,
                message=f"CFPB complaint filed successfully against {bureau_name}",
                confirmation_number=confirmation,
                data={
                    "bureau": bureau_name,
                    "confirmation_number": confirmation,
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
            screenshot = await self.take_screenshot(f"cfpb_{bureau_lower}_error")
            error_msg = f"CFPB automation failed for {bureau_name}: {str(e)}"
            self.mark_run_failed(error_msg, "UNEXPECTED_ERROR", screenshot)
            raise AutomationError(error_msg, "UNEXPECTED_ERROR", screenshot)

    def _build_complaint_narrative(
        self,
        bureau_name: str,
        account: Dict[str, Any],
        is_inquiry: bool,
        ftc_report_number: str = None,
    ) -> str:
        """Build the complaint narrative for the CFPB form"""

        ftc_reference = (
            f"\n\nFTC Identity Theft Report Number: {ftc_report_number}"
            if ftc_report_number
            else ""
        )

        if is_inquiry:
            return f"""
I am a victim of identity theft. An unauthorized hard inquiry from {account.get('creditor_name', 'a company')} appears on my credit report with {bureau_name}.

I did NOT authorize this company to access my credit report. This inquiry was made without my knowledge or consent and is the result of identity theft.

Under FCRA Section 605B, I am requesting that {bureau_name} block this fraudulent inquiry within 4 business days as required by law.

Inquiry Details:
- Company: {account.get('creditor_name', 'Unknown')}
- Date of Inquiry: {account.get('inquiry_date', account.get('date_opened', 'Unknown'))}
{ftc_reference}

I have filed an FTC Identity Theft Report and request immediate removal of this unauthorized inquiry.
"""
        else:
            return f"""
I am a victim of identity theft. A fraudulent account from {account.get('creditor_name', 'a creditor')} appears on my credit report with {bureau_name}.

I did NOT open this account. This is identity theft and I am requesting immediate blocking under FCRA Section 605B.

Under FCRA Section 605B, credit reporting agencies must block fraudulent information within 4 business days of receiving proper documentation.

Account Details:
- Creditor: {account.get('creditor_name', 'Unknown')}
- Account Number: {account.get('account_number', 'Unknown')}
- Account Type: {account.get('account_type', 'Unknown')}
- Date Opened: {account.get('date_opened', 'Unknown')}
- Balance: ${account.get('balance', 'Unknown')}
{ftc_reference}

I have filed an FTC Identity Theft Report and a police report. I am requesting immediate blocking of this fraudulent account.
"""

    def _extract_confirmation_number(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract CFPB confirmation number from the result"""
        import re

        if result and isinstance(result, dict):
            result_text = str(result)

            # CFPB confirmation patterns
            patterns = [
                r"Confirmation\s*#?\s*:?\s*([A-Z0-9-]{8,20})",
                r"Complaint\s*#?\s*:?\s*([A-Z0-9-]{8,20})",
                r"Reference\s*#?\s*:?\s*([A-Z0-9-]{8,20})",
                r"CFPB-([0-9]{6,12})",
                r"([0-9]{6,12})",  # Fallback: any long number
            ]

            for pattern in patterns:
                match = re.search(pattern, result_text, re.IGNORECASE)
                if match:
                    return match.group(1)

        return None

    async def file_complaints_all_bureaus(
        self,
        account: Dict[str, Any],
        bureaus: List[str] = None,
        is_inquiry: bool = False,
        ftc_report_number: str = None,
        delay_seconds: int = 60,
    ) -> Dict[str, AutomationResult]:
        """
        File CFPB complaints for all bureaus reporting an account.

        Args:
            account: Account details
            bureaus: List of bureaus to file against (default: all 3)
            is_inquiry: True for inquiry dispute
            ftc_report_number: FTC report number
            delay_seconds: Delay between submissions

        Returns:
            Dictionary mapping bureau name to AutomationResult
        """
        if bureaus is None:
            bureaus = account.get("bureaus", ["transunion", "equifax", "experian"])

        results = {}

        for i, bureau in enumerate(bureaus):
            bureau_lower = bureau.lower()
            logger.info(f"Filing CFPB complaint {i+1}/{len(bureaus)} against {bureau}")

            try:
                result = await self.file_cfpb_complaint(
                    bureau=bureau,
                    account=account,
                    is_inquiry=is_inquiry,
                    ftc_report_number=ftc_report_number,
                )
                results[bureau_lower] = result
            except Exception as e:
                logger.error(f"Failed to file CFPB complaint against {bureau}: {e}")
                results[bureau_lower] = AutomationResult(
                    success=False,
                    message=str(e),
                    error_code="CFPB_FILING_FAILED",
                )

            # Delay between submissions
            if i < len(bureaus) - 1:
                logger.info(f"Waiting {delay_seconds}s before next bureau...")
                await asyncio.sleep(delay_seconds)

        return results


async def run_cfpb_automation(
    client_id: int,
    bureau: str,
    account: Dict[str, Any],
    staff_id: int = None,
    is_inquiry: bool = False,
    ftc_report_number: str = None,
    headless: bool = False,
) -> AutomationResult:
    """
    Convenience function to run CFPB automation for a single bureau.

    Args:
        client_id: The client ID
        bureau: The bureau to complain about
        account: Account details
        staff_id: Staff member who initiated
        is_inquiry: True for inquiry dispute
        ftc_report_number: FTC report number
        headless: Run in headless mode

    Returns:
        AutomationResult
    """
    async with CFPBAutomation(
        client_id=client_id,
        staff_id=staff_id,
        headless=headless,
    ) as automation:
        return await automation.file_cfpb_complaint(
            bureau=bureau,
            account=account,
            is_inquiry=is_inquiry,
            ftc_report_number=ftc_report_number,
        )
