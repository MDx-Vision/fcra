"""
5-Day Knockout Orchestrator

Coordinates the full 5-Day Knockout (5KO) browser automation flow:
1. FTC Identity Theft Report
2. CFPB Complaints (one per bureau)
3. Bureau Portal Disputes (Equifax, TransUnion, Experian)

Files ONE item per submission across all portals.
Updates client timeline fields in chronological order.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_automation import AutomationError, AutomationResult
from .bureau_automation import (
    EquifaxAutomation,
    ExperianAutomation,
    TransUnionAutomation,
    get_bureau_automation,
)
from .cfpb_automation import CFPBAutomation
from .ftc_automation import FTCAutomation

logger = logging.getLogger(__name__)


@dataclass
class FiveKnockoutStatus:
    """Status of a 5-Day Knockout run"""

    client_id: int
    account: Dict[str, Any]
    started_at: datetime = None
    completed_at: datetime = None

    # Step results
    ftc_result: AutomationResult = None
    cfpb_results: Dict[str, AutomationResult] = field(default_factory=dict)
    bureau_results: Dict[str, AutomationResult] = field(default_factory=dict)

    # Tracking
    ftc_report_number: str = None
    cfpb_confirmations: Dict[str, str] = field(default_factory=dict)
    bureau_confirmations: Dict[str, str] = field(default_factory=dict)

    # Status
    current_step: str = "pending"
    error: str = None

    @property
    def is_complete(self) -> bool:
        """Check if all steps completed successfully"""
        return (
            self.ftc_result
            and self.ftc_result.success
            and all(r.success for r in self.cfpb_results.values())
            and all(r.success for r in self.bureau_results.values())
        )

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        total = (
            1 + len(self.cfpb_results) + len(self.bureau_results)
        )  # FTC + CFPB + Bureaus
        successful = 0
        if self.ftc_result and self.ftc_result.success:
            successful += 1
        successful += sum(1 for r in self.cfpb_results.values() if r.success)
        successful += sum(1 for r in self.bureau_results.values() if r.success)
        return successful / total if total > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "client_id": self.client_id,
            "account": self.account,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "current_step": self.current_step,
            "is_complete": self.is_complete,
            "success_rate": self.success_rate,
            "ftc_report_number": self.ftc_report_number,
            "cfpb_confirmations": self.cfpb_confirmations,
            "bureau_confirmations": self.bureau_confirmations,
            "error": self.error,
            "ftc": self.ftc_result.to_dict() if self.ftc_result else None,
            "cfpb": {k: v.to_dict() for k, v in self.cfpb_results.items()},
            "bureaus": {k: v.to_dict() for k, v in self.bureau_results.items()},
        }


class FiveKnockoutOrchestrator:
    """
    Orchestrates the complete 5-Day Knockout process for a single account.

    Flow:
    1. File FTC Identity Theft Report → Get report number
    2. File CFPB Complaint for each bureau reporting the account
    3. Submit disputes to bureau portals (respecting limits)
    4. Update client timeline fields throughout

    Timeline Fields Updated:
    - fko_started_at: When process begins
    - fko_ftc_filed_at: When FTC report is filed
    - fko_cfpb_filed_at: When CFPB complaints are filed
    - fko_letters_sent_at: When bureau disputes are submitted
    """

    def __init__(
        self,
        client_id: int,
        staff_id: int = None,
        headless: bool = False,
        delay_between_steps: int = 30,
    ):
        """
        Initialize the orchestrator.

        Args:
            client_id: The client ID
            staff_id: Staff member who initiated
            headless: Run browsers in headless mode (default False for oversight)
            delay_between_steps: Seconds to wait between major steps
        """
        self.client_id = client_id
        self.staff_id = staff_id
        self.headless = headless
        self.delay_between_steps = delay_between_steps
        self.status = None

    async def run_full_knockout(
        self,
        account: Dict[str, Any],
        skip_ftc: bool = False,
        skip_cfpb: bool = False,
        skip_bureaus: bool = False,
        bureaus_to_file: List[str] = None,
    ) -> FiveKnockoutStatus:
        """
        Run the complete 5-Day Knockout process for a single account.

        Args:
            account: Account details dictionary with:
                - creditor_name: Name of creditor
                - account_number: Account number
                - account_type: Type of account
                - date_opened: When opened
                - balance: Current balance
                - bureaus: List of bureaus reporting (e.g., ['equifax', 'transunion', 'experian'])
            skip_ftc: Skip FTC filing (if already done)
            skip_cfpb: Skip CFPB filing
            skip_bureaus: Skip bureau portal disputes
            bureaus_to_file: Specific bureaus to file with (default: all in account['bureaus'])

        Returns:
            FiveKnockoutStatus with results of all steps
        """
        self.status = FiveKnockoutStatus(
            client_id=self.client_id,
            account=account,
            started_at=datetime.utcnow(),
        )

        # Update client timeline - process started
        self._update_client_field("fko_started_at", datetime.utcnow())
        self._update_client_field("fko_status", "in_progress")

        bureaus = bureaus_to_file or account.get(
            "bureaus", ["equifax", "transunion", "experian"]
        )

        try:
            # Step 1: FTC Identity Theft Report
            if not skip_ftc:
                self.status.current_step = "ftc"
                logger.info(f"Step 1/3: Filing FTC report for client {self.client_id}")
                await self._run_ftc_step(account)
                await asyncio.sleep(self.delay_between_steps)

            # Step 2: CFPB Complaints
            if not skip_cfpb:
                self.status.current_step = "cfpb"
                logger.info(
                    f"Step 2/3: Filing CFPB complaints for client {self.client_id}"
                )
                await self._run_cfpb_step(account, bureaus)
                await asyncio.sleep(self.delay_between_steps)

            # Step 3: Bureau Portal Disputes
            if not skip_bureaus:
                self.status.current_step = "bureaus"
                logger.info(
                    f"Step 3/3: Filing bureau disputes for client {self.client_id}"
                )
                await self._run_bureau_step(account, bureaus)

            # Mark complete
            self.status.current_step = "complete"
            self.status.completed_at = datetime.utcnow()

            # Update client timeline
            if self.status.is_complete:
                self._update_client_field("fko_status", "completed")
                self._update_client_field("fko_completed_at", datetime.utcnow())
            else:
                self._update_client_field("fko_status", "partial")

            logger.info(
                f"5KO complete for client {self.client_id}. "
                f"Success rate: {self.status.success_rate:.0%}"
            )

            return self.status

        except Exception as e:
            self.status.error = str(e)
            self.status.current_step = "failed"
            self._update_client_field("fko_status", "stalled")
            logger.error(f"5KO failed for client {self.client_id}: {e}")
            raise

    async def _run_ftc_step(self, account: Dict[str, Any]):
        """Run the FTC filing step"""
        try:
            async with FTCAutomation(
                client_id=self.client_id,
                staff_id=self.staff_id,
                headless=self.headless,
            ) as ftc:
                result = await ftc.file_identity_theft_report(account, is_inquiry=False)
                self.status.ftc_result = result

                if result.success and result.confirmation_number:
                    self.status.ftc_report_number = result.confirmation_number
                    self._update_client_field("fko_ftc_filed_at", datetime.utcnow())
                    logger.info(f"FTC report filed: {result.confirmation_number}")

        except Exception as e:
            logger.error(f"FTC step failed: {e}")
            self.status.ftc_result = AutomationResult(
                success=False,
                message=str(e),
                error_code="FTC_FAILED",
            )

    async def _run_cfpb_step(self, account: Dict[str, Any], bureaus: List[str]):
        """Run the CFPB filing step for all bureaus"""
        try:
            async with CFPBAutomation(
                client_id=self.client_id,
                staff_id=self.staff_id,
                headless=self.headless,
            ) as cfpb:
                results = await cfpb.file_complaints_all_bureaus(
                    account=account,
                    bureaus=bureaus,
                    is_inquiry=False,
                    ftc_report_number=self.status.ftc_report_number,
                    delay_seconds=60,
                )
                self.status.cfpb_results = results

                # Collect confirmations
                for bureau, result in results.items():
                    if result.success and result.confirmation_number:
                        self.status.cfpb_confirmations[bureau] = (
                            result.confirmation_number
                        )

                # Update timeline if any CFPB was successful
                if any(r.success for r in results.values()):
                    self._update_client_field("fko_cfpb_filed_at", datetime.utcnow())

                logger.info(
                    f"CFPB complaints filed: {sum(1 for r in results.values() if r.success)}/{len(bureaus)} successful"
                )

        except Exception as e:
            logger.error(f"CFPB step failed: {e}")
            for bureau in bureaus:
                self.status.cfpb_results[bureau] = AutomationResult(
                    success=False,
                    message=str(e),
                    error_code="CFPB_FAILED",
                )

    async def _run_bureau_step(self, account: Dict[str, Any], bureaus: List[str]):
        """Run the bureau portal dispute step"""
        for bureau in bureaus:
            try:
                automation = get_bureau_automation(
                    bureau=bureau,
                    client_id=self.client_id,
                    staff_id=self.staff_id,
                    headless=self.headless,
                )

                async with automation:
                    result = await automation.submit_dispute(
                        account=account,
                        ftc_report_number=self.status.ftc_report_number,
                    )
                    self.status.bureau_results[bureau] = result

                    if result.success and result.confirmation_number:
                        self.status.bureau_confirmations[bureau] = (
                            result.confirmation_number
                        )

                logger.info(
                    f"Bureau {bureau} dispute: {'Success' if result.success else 'Failed'}"
                )

                # Delay between bureaus
                await asyncio.sleep(30)

            except AutomationError as e:
                if e.error_code == "DISPUTE_LIMIT_REACHED":
                    logger.warning(f"Bureau {bureau}: {e.message}")
                else:
                    logger.error(f"Bureau {bureau} failed: {e}")

                self.status.bureau_results[bureau] = AutomationResult(
                    success=False,
                    message=e.message,
                    error_code=e.error_code,
                )
            except Exception as e:
                logger.error(f"Bureau {bureau} failed unexpectedly: {e}")
                self.status.bureau_results[bureau] = AutomationResult(
                    success=False,
                    message=str(e),
                    error_code="BUREAU_FAILED",
                )

        # Update timeline if any bureau was successful
        if any(r.success for r in self.status.bureau_results.values()):
            self._update_client_field("fko_letters_sent_at", datetime.utcnow())

    def _update_client_field(self, field: str, value: Any):
        """Update a field on the client record"""
        from database import Client, get_db

        db = get_db()
        try:
            client = db.query(Client).filter(Client.id == self.client_id).first()
            if client and hasattr(client, field):
                setattr(client, field, value)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update client field {field}: {e}")
        finally:
            db.close()

    async def run_ftc_only(self, account: Dict[str, Any]) -> AutomationResult:
        """Run only the FTC step"""
        async with FTCAutomation(
            client_id=self.client_id,
            staff_id=self.staff_id,
            headless=self.headless,
        ) as ftc:
            return await ftc.file_identity_theft_report(account, is_inquiry=False)

    async def run_cfpb_only(
        self,
        account: Dict[str, Any],
        bureau: str,
        ftc_report_number: str = None,
    ) -> AutomationResult:
        """Run only the CFPB step for a single bureau"""
        async with CFPBAutomation(
            client_id=self.client_id,
            staff_id=self.staff_id,
            headless=self.headless,
        ) as cfpb:
            return await cfpb.file_cfpb_complaint(
                bureau=bureau,
                account=account,
                is_inquiry=False,
                ftc_report_number=ftc_report_number,
            )

    async def run_bureau_only(
        self,
        account: Dict[str, Any],
        bureau: str,
        ftc_report_number: str = None,
    ) -> AutomationResult:
        """Run only the bureau portal step"""
        automation = get_bureau_automation(
            bureau=bureau,
            client_id=self.client_id,
            staff_id=self.staff_id,
            headless=self.headless,
        )

        async with automation:
            return await automation.submit_dispute(
                account=account,
                ftc_report_number=ftc_report_number,
            )


async def run_5ko_for_client(
    client_id: int,
    account: Dict[str, Any],
    staff_id: int = None,
    headless: bool = False,
) -> FiveKnockoutStatus:
    """
    Convenience function to run full 5KO for a client.

    Args:
        client_id: The client ID
        account: Account details
        staff_id: Staff member who initiated
        headless: Run in headless mode

    Returns:
        FiveKnockoutStatus
    """
    orchestrator = FiveKnockoutOrchestrator(
        client_id=client_id,
        staff_id=staff_id,
        headless=headless,
    )
    return await orchestrator.run_full_knockout(account)
