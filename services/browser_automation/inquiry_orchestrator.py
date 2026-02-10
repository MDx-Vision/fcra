"""
Inquiry Dispute Orchestrator

Coordinates the browser automation flow for disputing unauthorized hard inquiries:
1. FTC Identity Theft Report (one per inquiry)
2. CFPB Complaint (one per bureau reporting the inquiry)

Simpler than 5KO - no bureau portal submissions needed.
Inquiries are typically removed faster since they're easier to prove unauthorized.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_automation import AutomationError, AutomationResult
from .cfpb_automation import CFPBAutomation
from .ftc_automation import FTCAutomation

logger = logging.getLogger(__name__)


@dataclass
class InquiryDisputeStatus:
    """Status of an inquiry dispute run"""

    client_id: int
    inquiry: Dict[str, Any]
    started_at: datetime = None
    completed_at: datetime = None

    # Step results
    ftc_result: AutomationResult = None
    cfpb_results: Dict[str, AutomationResult] = field(default_factory=dict)

    # Tracking
    ftc_report_number: str = None
    cfpb_confirmations: Dict[str, str] = field(default_factory=dict)

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
        )

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        total = 1 + len(self.cfpb_results)  # FTC + CFPB complaints
        successful = 0
        if self.ftc_result and self.ftc_result.success:
            successful += 1
        successful += sum(1 for r in self.cfpb_results.values() if r.success)
        return successful / total if total > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "client_id": self.client_id,
            "inquiry": self.inquiry,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "current_step": self.current_step,
            "is_complete": self.is_complete,
            "success_rate": self.success_rate,
            "ftc_report_number": self.ftc_report_number,
            "cfpb_confirmations": self.cfpb_confirmations,
            "error": self.error,
            "ftc": self.ftc_result.to_dict() if self.ftc_result else None,
            "cfpb": {k: v.to_dict() for k, v in self.cfpb_results.items()},
        }


class InquiryDisputeOrchestrator:
    """
    Orchestrates the inquiry dispute process.

    Flow:
    1. File FTC Identity Theft Report → Get report number
    2. File CFPB Complaint for each bureau reporting the inquiry
    3. Update client timeline fields throughout

    Timeline Fields Updated:
    - inquiry_dispute_started_at: When process begins
    - inquiry_ftc_filed_at: When FTC report is filed
    - inquiry_cfpb_filed_at: When CFPB complaints are filed

    Note: Unlike 5KO, inquiry disputes don't require bureau portal submissions.
    Inquiries are removed by the bureaus based on CFPB complaints and FTC reports.
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

    async def run_inquiry_dispute(
        self,
        inquiry: Dict[str, Any],
        skip_ftc: bool = False,
        skip_cfpb: bool = False,
        bureaus_to_file: List[str] = None,
    ) -> InquiryDisputeStatus:
        """
        Run the complete inquiry dispute process for a single unauthorized inquiry.

        Args:
            inquiry: Inquiry details dictionary with:
                - creditor_name: Name of company that pulled credit
                - inquiry_date: Date of the inquiry
                - bureaus: List of bureaus showing the inquiry (e.g., ['equifax', 'transunion'])
            skip_ftc: Skip FTC filing (if already done)
            skip_cfpb: Skip CFPB filing
            bureaus_to_file: Specific bureaus to file against (default: all in inquiry['bureaus'])

        Returns:
            InquiryDisputeStatus with results of all steps
        """
        self.status = InquiryDisputeStatus(
            client_id=self.client_id,
            inquiry=inquiry,
            started_at=datetime.utcnow(),
        )

        # Update client timeline - process started
        self._update_client_field("inquiry_dispute_started_at", datetime.utcnow())
        self._update_client_field("inquiry_dispute_status", "in_progress")

        bureaus = bureaus_to_file or inquiry.get(
            "bureaus", ["equifax", "transunion", "experian"]
        )

        try:
            # Step 1: FTC Identity Theft Report
            if not skip_ftc:
                self.status.current_step = "ftc"
                logger.info(
                    f"Step 1/2: Filing FTC inquiry report for client {self.client_id}"
                )
                await self._run_ftc_step(inquiry)
                await asyncio.sleep(self.delay_between_steps)

            # Step 2: CFPB Complaints
            if not skip_cfpb:
                self.status.current_step = "cfpb"
                logger.info(
                    f"Step 2/2: Filing CFPB inquiry complaints for client {self.client_id}"
                )
                await self._run_cfpb_step(inquiry, bureaus)

            # Mark complete
            self.status.current_step = "complete"
            self.status.completed_at = datetime.utcnow()

            # Update client timeline
            if self.status.is_complete:
                self._update_client_field("inquiry_dispute_status", "completed")
                self._update_client_field(
                    "inquiry_dispute_completed_at", datetime.utcnow()
                )
            else:
                self._update_client_field("inquiry_dispute_status", "partial")

            logger.info(
                f"Inquiry dispute complete for client {self.client_id}. "
                f"Success rate: {self.status.success_rate:.0%}"
            )

            return self.status

        except Exception as e:
            self.status.error = str(e)
            self.status.current_step = "failed"
            self._update_client_field("inquiry_dispute_status", "stalled")
            logger.error(f"Inquiry dispute failed for client {self.client_id}: {e}")
            raise

    async def _run_ftc_step(self, inquiry: Dict[str, Any]):
        """Run the FTC filing step for an inquiry"""
        try:
            async with FTCAutomation(
                client_id=self.client_id,
                staff_id=self.staff_id,
                headless=self.headless,
            ) as ftc:
                result = await ftc.file_identity_theft_report(inquiry, is_inquiry=True)
                self.status.ftc_result = result

                if result.success and result.confirmation_number:
                    self.status.ftc_report_number = result.confirmation_number
                    self._update_client_field("inquiry_ftc_filed_at", datetime.utcnow())
                    self._update_client_field(
                        "inquiry_ftc_report_number", result.confirmation_number
                    )
                    logger.info(
                        f"FTC inquiry report filed: {result.confirmation_number}"
                    )

        except Exception as e:
            logger.error(f"FTC step failed: {e}")
            self.status.ftc_result = AutomationResult(
                success=False,
                message=str(e),
                error_code="FTC_FAILED",
            )

    async def _run_cfpb_step(self, inquiry: Dict[str, Any], bureaus: List[str]):
        """Run the CFPB filing step for all bureaus"""
        try:
            async with CFPBAutomation(
                client_id=self.client_id,
                staff_id=self.staff_id,
                headless=self.headless,
            ) as cfpb:
                results = await cfpb.file_complaints_all_bureaus(
                    account=inquiry,
                    bureaus=bureaus,
                    is_inquiry=True,
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
                    self._update_client_field(
                        "inquiry_cfpb_filed_at", datetime.utcnow()
                    )

                logger.info(
                    f"CFPB inquiry complaints filed: {sum(1 for r in results.values() if r.success)}/{len(bureaus)} successful"
                )

        except Exception as e:
            logger.error(f"CFPB step failed: {e}")
            for bureau in bureaus:
                self.status.cfpb_results[bureau] = AutomationResult(
                    success=False,
                    message=str(e),
                    error_code="CFPB_FAILED",
                )

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

    async def run_ftc_only(self, inquiry: Dict[str, Any]) -> AutomationResult:
        """Run only the FTC step"""
        async with FTCAutomation(
            client_id=self.client_id,
            staff_id=self.staff_id,
            headless=self.headless,
        ) as ftc:
            return await ftc.file_identity_theft_report(inquiry, is_inquiry=True)

    async def run_cfpb_only(
        self,
        inquiry: Dict[str, Any],
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
                account=inquiry,
                is_inquiry=True,
                ftc_report_number=ftc_report_number,
            )


async def run_inquiry_dispute_for_client(
    client_id: int,
    inquiry: Dict[str, Any],
    staff_id: int = None,
    headless: bool = False,
) -> InquiryDisputeStatus:
    """
    Convenience function to run inquiry dispute for a client.

    Args:
        client_id: The client ID
        inquiry: Inquiry details
        staff_id: Staff member who initiated
        headless: Run in headless mode

    Returns:
        InquiryDisputeStatus
    """
    orchestrator = InquiryDisputeOrchestrator(
        client_id=client_id,
        staff_id=staff_id,
        headless=headless,
    )
    return await orchestrator.run_inquiry_dispute(inquiry)


async def run_batch_inquiry_disputes(
    client_id: int,
    inquiries: List[Dict[str, Any]],
    staff_id: int = None,
    headless: bool = False,
    delay_between_inquiries: int = 120,
) -> List[InquiryDisputeStatus]:
    """
    Run inquiry disputes for multiple inquiries.

    Args:
        client_id: The client ID
        inquiries: List of inquiry details
        staff_id: Staff member who initiated
        headless: Run in headless mode
        delay_between_inquiries: Delay in seconds between inquiries

    Returns:
        List of InquiryDisputeStatus objects
    """
    results = []

    for i, inquiry in enumerate(inquiries):
        logger.info(
            f"Processing inquiry {i+1}/{len(inquiries)}: {inquiry.get('creditor_name', 'Unknown')}"
        )

        try:
            result = await run_inquiry_dispute_for_client(
                client_id=client_id,
                inquiry=inquiry,
                staff_id=staff_id,
                headless=headless,
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Inquiry dispute {i+1} failed: {e}")
            results.append(
                InquiryDisputeStatus(
                    client_id=client_id,
                    inquiry=inquiry,
                    started_at=datetime.utcnow(),
                    current_step="failed",
                    error=str(e),
                )
            )

        # Delay between inquiries
        if i < len(inquiries) - 1:
            logger.info(f"Waiting {delay_between_inquiries}s before next inquiry...")
            await asyncio.sleep(delay_between_inquiries)

    return results
