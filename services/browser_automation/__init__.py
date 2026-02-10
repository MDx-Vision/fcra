"""
Browser Automation Module for 5-Day Knockout and Inquiry Disputes

Uses browser-use library for LLM-controlled browser automation.
"""

from .base_automation import AutomationError, AutomationResult, BaseAutomation
from .bureau_automation import (
    BureauAutomation,
    EquifaxAutomation,
    ExperianAutomation,
    TransUnionAutomation,
)
from .cfpb_automation import CFPBAutomation
from .fko_orchestrator import FiveKnockoutOrchestrator
from .ftc_automation import FTCAutomation
from .inquiry_orchestrator import InquiryDisputeOrchestrator

__all__ = [
    "BaseAutomation",
    "AutomationError",
    "AutomationResult",
    "FTCAutomation",
    "CFPBAutomation",
    "BureauAutomation",
    "EquifaxAutomation",
    "TransUnionAutomation",
    "ExperianAutomation",
    "FiveKnockoutOrchestrator",
    "InquiryDisputeOrchestrator",
]
