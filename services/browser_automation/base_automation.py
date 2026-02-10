"""
Base Browser Automation Class

Provides common functionality for all browser automation tasks.
Uses browser-use library for LLM-controlled browser automation.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AutomationError(Exception):
    """Custom exception for automation errors"""

    def __init__(
        self,
        message: str,
        error_code: str = "AUTOMATION_ERROR",
        screenshot_path: str = None,
    ):
        self.message = message
        self.error_code = error_code
        self.screenshot_path = screenshot_path
        super().__init__(self.message)


@dataclass
class AutomationResult:
    """Result of an automation run"""

    success: bool
    message: str
    confirmation_number: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    screenshot_path: Optional[str] = None
    error_code: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "confirmation_number": self.confirmation_number,
            "data": self.data,
            "screenshot_path": self.screenshot_path,
            "error_code": self.error_code,
            "duration_seconds": self.duration_seconds,
        }


class BaseAutomation:
    """
    Base class for browser automation tasks.

    Provides common functionality:
    - Browser setup and teardown
    - Screenshot capture
    - Error handling
    - Logging
    - Database integration for AutomationRun tracking
    """

    # Portal URLs
    FTC_URL = "https://www.identitytheft.gov"
    CFPB_URL = "https://www.consumerfinance.gov/complaint"
    EQUIFAX_URL = "https://my.equifax.com"
    TRANSUNION_URL = "https://www.transunion.com"
    EXPERIAN_URL = "https://www.experian.com"

    # Screenshot directory
    SCREENSHOT_DIR = "uploads/automation_screenshots"

    def __init__(
        self,
        client_id: int,
        staff_id: int = None,
        headless: bool = False,
        timeout: int = 60,
        anthropic_api_key: str = None,
    ):
        """
        Initialize the automation.

        Args:
            client_id: The client ID for this automation
            staff_id: The staff member who initiated the automation
            headless: Run browser in headless mode (default False for oversight)
            timeout: Default timeout in seconds for browser operations
            anthropic_api_key: API key for Claude (used by browser-use)
        """
        self.client_id = client_id
        self.staff_id = staff_id
        self.headless = headless
        self.timeout = timeout
        self.anthropic_api_key = anthropic_api_key or os.environ.get(
            "ANTHROPIC_API_KEY"
        )

        self.browser = None
        self.agent = None
        self.start_time = None
        self.automation_run_id = None

        # Ensure screenshot directory exists
        Path(self.SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)

    async def setup(self):
        """Set up the browser and agent"""
        try:
            from browser_use import Agent
            from langchain_anthropic import ChatAnthropic

            # Initialize the LLM
            llm = ChatAnthropic(
                model_name="claude-sonnet-4-20250514",
                anthropic_api_key=self.anthropic_api_key,
                timeout=self.timeout,
            )

            # Initialize the agent
            self.agent = Agent(
                task="",  # Will be set per-action
                llm=llm,
                headless=self.headless,
            )

            self.start_time = datetime.utcnow()
            logger.info(
                f"Browser automation setup complete for client {self.client_id}"
            )

        except ImportError as e:
            raise AutomationError(
                f"browser-use library not installed: {e}",
                error_code="DEPENDENCY_MISSING",
            )
        except Exception as e:
            raise AutomationError(
                f"Failed to setup browser: {e}",
                error_code="SETUP_FAILED",
            )

    async def teardown(self):
        """Clean up browser resources"""
        try:
            if self.agent:
                await self.agent.close()
                self.agent = None
            logger.info(
                f"Browser automation teardown complete for client {self.client_id}"
            )
        except Exception as e:
            logger.error(f"Error during teardown: {e}")

    async def take_screenshot(self, name: str) -> str:
        """
        Take a screenshot and save it.

        Args:
            name: Name for the screenshot file

        Returns:
            Path to the saved screenshot
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.client_id}_{name}_{timestamp}.png"
        filepath = os.path.join(self.SCREENSHOT_DIR, filename)

        try:
            if self.agent and self.agent.browser:
                page = self.agent.browser.current_page
                if page:
                    await page.screenshot(path=filepath)
                    logger.info(f"Screenshot saved: {filepath}")
                    return filepath
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")

        return None

    async def run_task(self, task: str, max_steps: int = 20) -> Dict[str, Any]:
        """
        Run a browser task using the LLM agent.

        Args:
            task: Natural language description of the task
            max_steps: Maximum number of steps the agent can take

        Returns:
            Result dictionary with success status and any extracted data
        """
        if not self.agent:
            raise AutomationError(
                "Agent not initialized. Call setup() first.",
                error_code="NOT_INITIALIZED",
            )

        try:
            # Update agent task
            self.agent.task = task

            # Run the agent
            result = await self.agent.run(max_steps=max_steps)

            return {
                "success": True,
                "result": result,
                "steps_taken": len(result.history) if hasattr(result, "history") else 0,
            }

        except Exception as e:
            screenshot_path = await self.take_screenshot("error")
            raise AutomationError(
                f"Task failed: {e}",
                error_code="TASK_FAILED",
                screenshot_path=screenshot_path,
            )

    def get_client_data(self) -> Dict[str, Any]:
        """
        Get client data from database.

        Returns:
            Dictionary with client information
        """
        from database import Client, get_db

        db = get_db()
        try:
            client = db.query(Client).filter(Client.id == self.client_id).first()
            if not client:
                raise AutomationError(
                    f"Client {self.client_id} not found", error_code="CLIENT_NOT_FOUND"
                )

            return {
                "id": client.id,
                "name": client.name,
                "email": client.email,
                "phone": client.phone,
                "address": client.address,
                "city": client.city,
                "state": client.state,
                "zip_code": client.zip_code,
                "ssn_last_4": client.ssn_last_4,
                "dob": client.dob.isoformat() if client.dob else None,
                # Bureau credentials
                "tu_username": client.tu_portal_username,
                "eq_username": client.eq_portal_username,
                "exp_username": client.exp_portal_username,
                # FTC tracking
                "ftc_report_number": client.ftc_report_number,
                # CFPB tracking
                "cfpb_tu_confirmation": client.cfpb_tu_confirmation,
                "cfpb_eq_confirmation": client.cfpb_eq_confirmation,
                "cfpb_exp_confirmation": client.cfpb_exp_confirmation,
            }
        finally:
            db.close()

    def get_decrypted_password(self, bureau: str) -> Optional[str]:
        """
        Get decrypted bureau portal password.

        Args:
            bureau: 'tu', 'eq', or 'exp'

        Returns:
            Decrypted password or None
        """
        from database import Client, get_db
        from services.encryption_service import decrypt_value

        db = get_db()
        try:
            client = db.query(Client).filter(Client.id == self.client_id).first()
            if not client:
                return None

            encrypted_field = f"{bureau}_portal_password_encrypted"
            encrypted_value = getattr(client, encrypted_field, None)

            if encrypted_value:
                return decrypt_value(encrypted_value)
            return None
        finally:
            db.close()

    def create_automation_run(self, automation_type: str, portal: str) -> int:
        """
        Create an AutomationRun record in the database.

        Args:
            automation_type: Type of automation (5ko_ftc, 5ko_cfpb, etc.)
            portal: Portal being automated (ftc, cfpb, equifax, etc.)

        Returns:
            The automation run ID
        """
        from database import AutomationRun, get_db

        db = get_db()
        try:
            run = AutomationRun(
                client_id=self.client_id,
                automation_type=automation_type,
                portal=portal,
                status="pending",
                staff_id=self.staff_id,
            )
            db.add(run)
            db.commit()
            self.automation_run_id = run.id
            return run.id
        finally:
            db.close()

    def update_automation_run(self, **kwargs):
        """Update the current automation run record"""
        if not self.automation_run_id:
            return

        from database import AutomationRun, get_db

        db = get_db()
        try:
            run = (
                db.query(AutomationRun)
                .filter(AutomationRun.id == self.automation_run_id)
                .first()
            )
            if run:
                for key, value in kwargs.items():
                    if hasattr(run, key):
                        setattr(run, key, value)
                db.commit()
        finally:
            db.close()

    def mark_run_started(self):
        """Mark the automation run as started"""
        from database import AutomationRun, get_db

        if not self.automation_run_id:
            return

        db = get_db()
        try:
            run = (
                db.query(AutomationRun)
                .filter(AutomationRun.id == self.automation_run_id)
                .first()
            )
            if run:
                run.mark_started()
                db.commit()
        finally:
            db.close()

    def mark_run_completed(
        self, confirmation_number: str = None, result_data: Dict = None
    ):
        """Mark the automation run as completed"""
        from database import AutomationRun, get_db

        if not self.automation_run_id:
            return

        db = get_db()
        try:
            run = (
                db.query(AutomationRun)
                .filter(AutomationRun.id == self.automation_run_id)
                .first()
            )
            if run:
                run.mark_completed(
                    confirmation_number=confirmation_number, result_data=result_data
                )
                db.commit()
        finally:
            db.close()

    def mark_run_failed(
        self, error_message: str, error_code: str = None, screenshot_path: str = None
    ):
        """Mark the automation run as failed"""
        from database import AutomationRun, get_db

        if not self.automation_run_id:
            return

        db = get_db()
        try:
            run = (
                db.query(AutomationRun)
                .filter(AutomationRun.id == self.automation_run_id)
                .first()
            )
            if run:
                run.mark_failed(
                    error_message=error_message,
                    error_code=error_code,
                    screenshot_path=screenshot_path,
                )
                db.commit()
        finally:
            db.close()

    def update_client_tracking(self, field: str, value: Any):
        """
        Update a tracking field on the client record.

        Args:
            field: The field name to update (e.g., 'ftc_report_number')
            value: The value to set
        """
        from database import Client, get_db

        db = get_db()
        try:
            client = db.query(Client).filter(Client.id == self.client_id).first()
            if client and hasattr(client, field):
                setattr(client, field, value)
                db.commit()
                logger.info(f"Updated client {self.client_id} {field} = {value}")
        finally:
            db.close()

    def calculate_duration(self) -> float:
        """Calculate the duration of the automation run in seconds"""
        if self.start_time:
            return (datetime.utcnow() - self.start_time).total_seconds()
        return 0.0

    async def __aenter__(self):
        """Async context manager entry"""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.teardown()
        return False
