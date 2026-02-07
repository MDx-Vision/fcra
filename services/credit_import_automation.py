"""
Credit Report Import Browser Automation Service
Uses Playwright to automate login and report downloading from credit monitoring services.
Supports: IdentityIQ, MyScoreIQ, SmartCredit, MyFreeScoreNow, and more.
"""

import asyncio
import logging
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Cache duration for recent reports (reuse instead of re-pulling)
CACHE_HOURS = 12  # Reuse reports pulled within last 12 hours

logger = logging.getLogger(__name__)

# Activity logging for human-readable debugging
from services.activity_logger import (
    log_activity,
    log_credit_import,
    log_credit_import_failed,
)

REPORTS_DIR = Path("uploads/credit_reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SERVICE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "IdentityIQ.com": {
        "login_url": "https://member.identityiq.com/login.aspx",
        "username_selector": "#txtUserName",
        "password_selector": "#txtPassword",
        "ssn_last4_selector": "#txtSSN",
        "login_button_selector": "#btnLogin",
        "report_download_flow": "identityiq",
    },
    "MyScoreIQ.com": {
        "login_url": "https://member.myscoreiq.com/",
        "username_selector": "#txtUsername",
        "password_selector": "#txtPassword",
        "ssn_last4_selector": None,
        "login_button_selector": "#imgBtnLogin",
        "report_download_flow": "myscoreiq",
        "post_login_url": "https://member.myscoreiq.com/CreditReport/Index",
    },
    "SmartCredit.com": {
        "login_url": "https://member.smartcredit.com/login",
        "username_selector": 'input[name="email"]',
        "password_selector": 'input[name="password"]',
        "ssn_last4_selector": 'input[name="ssn4"]',
        "login_button_selector": 'button[type="submit"]',
        "report_download_flow": "smartcredit",
    },
    "MyFreeScoreNow.com": {
        "login_url": "https://member.myfreescorenow.com/login",
        "username_selector": 'input[type="email"]:visible, input[name="email"]:visible, #email',
        "password_selector": 'input[type="password"]:visible, input[name="password"]:visible, #password',
        "ssn_last4_selector": 'input[name="ssn"]:visible, #ssn_last4, #ssn, input[placeholder*="SSN"]:visible',
        "login_button_selector": 'button[type="submit"]:visible, button:has-text("Sign In"), button:has-text("Log In")',
        "report_download_flow": "myfreescorenow",
        "post_login_url": "https://member.myfreescorenow.com/dashboard",  # Dashboard after login
        # Note: No hardcoded report_page_url - will search for link dynamically
    },
    "HighScoreNow.com": {
        "login_url": "https://member.highscorenow.com/login",
        "username_selector": "#email",
        "password_selector": "#password",
        "ssn_last4_selector": "#ssn",
        "login_button_selector": 'button[type="submit"]',
        "report_download_flow": "highscorenow",
    },
    "IdentityClub.com": {
        "login_url": "https://member.identityclub.com/login",
        "username_selector": "#username",
        "password_selector": "#password",
        "ssn_last4_selector": "#ssn4",
        "login_button_selector": 'button[type="submit"]',
        "report_download_flow": "identityclub",
    },
    "PrivacyGuard.com": {
        "login_url": "https://member.privacyguard.com/login",
        "username_selector": "#email",
        "password_selector": "#password",
        "ssn_last4_selector": "#ssn",
        "login_button_selector": 'button[type="submit"]',
        "report_download_flow": "privacyguard",
    },
    "IDClub.com": {
        "login_url": "https://member.idclub.com/login",
        "username_selector": "#email",
        "password_selector": "#password",
        "ssn_last4_selector": "#ssn_last4",
        "login_button_selector": 'button[type="submit"]',
        "report_download_flow": "idclub",
    },
    "MyThreeScores.com": {
        "login_url": "https://member.mythreescores.com/login",
        "username_selector": "#email",
        "password_selector": "#password",
        "ssn_last4_selector": "#ssn4",
        "login_button_selector": 'button[type="submit"]',
        "report_download_flow": "mythreescores",
    },
    "MyScore750.com": {
        "login_url": "https://member.myscore750.com/login",
        "username_selector": "#email",
        "password_selector": "#password",
        "ssn_last4_selector": "#ssn",
        "login_button_selector": 'button[type="submit"]',
        "report_download_flow": "myscore750",
    },
    "CreditHeroScore.com": {
        "login_url": "https://member.creditheroscore.com/login",
        "username_selector": "#email",
        "password_selector": "#password",
        "ssn_last4_selector": "#ssn4",
        "login_button_selector": 'button[type="submit"]',
        "report_download_flow": "creditheroscore",
    },
}


class CreditImportAutomation:
    """Automated credit report import using Playwright browser automation."""

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.current_flow = (
            None  # Track which service flow we're using for score extraction
        )

    async def _init_browser(self):
        """Initialize headless browser with speed optimizations."""
        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",
                    "--single-process",
                    # Speed optimizations
                    "--disable-images",
                    "--blink-settings=imagesEnabled=false",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-sync",
                    "--disable-translate",
                    "--disable-background-networking",
                    "--disable-default-apps",
                ],
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                # Block images and other resources for speed
                bypass_csp=True,
            )
            self.page = await self.context.new_page()

            # Note: Don't block images - "View Report" buttons may be image-based
            # Only block fonts and large non-essential resources
            await self.page.route(
                "**/*.{woff,woff2,ttf,eot}", lambda route: route.abort()
            )

            return True
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return False

    async def _close_browser(self):
        """Close browser and cleanup."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, "playwright"):
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def import_report(
        self,
        service_name: str,
        username: str,
        password: str,
        ssn_last4: str,
        client_id: int,
        client_name: str,
    ) -> Dict:
        """
        Import credit report from a monitoring service.

        Args:
            service_name: Name of the credit monitoring service
            username: Login username/email
            password: Login password
            ssn_last4: Last 4 digits of SSN or security word
            client_id: Client ID for file naming
            client_name: Client name for logging

        Returns:
            Dict with success status, report path, scores, and any errors
        """
        result = {
            "success": False,
            "report_path": None,
            "html_content": None,
            "scores": None,
            "error": None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if service_name not in SERVICE_CONFIGS:
            result["error"] = f"Unsupported service: {service_name}"
            log_activity(
                "Credit Import",
                f"Unsupported service: {service_name}",
                client_id=client_id,
                status="error",
            )
            return result

        config = SERVICE_CONFIGS[service_name]
        self.current_flow = config.get(
            "report_download_flow", ""
        )  # Set flow for extraction

        try:
            log_activity(
                "Credit Import Started",
                f"{client_name} | {service_name}",
                client_id=client_id,
                status="info",
            )

            log_activity(
                "Initialize Browser",
                "Launching Playwright browser...",
                client_id=client_id,
                status="info",
            )
            if not await self._init_browser():
                result["error"] = "Failed to initialize browser"
                log_activity(
                    "Browser Init Failed",
                    "Could not launch browser",
                    client_id=client_id,
                    status="error",
                )
                return result

            log_activity(
                "Browser Ready",
                "Navigating to login page...",
                client_id=client_id,
                status="success",
            )
            logger.info(f"Starting import for {client_name} from {service_name}")

            log_activity(
                "Login Attempt",
                f"Logging into {service_name}...",
                client_id=client_id,
                status="info",
            )
            login_success = await self._login(config, username, password, ssn_last4)
            if not login_success:
                result["error"] = "Login failed - check credentials"
                log_credit_import_failed(
                    client_id, service_name, "Login failed - invalid credentials"
                )
                return result

            log_activity(
                "Login Success",
                f"Authenticated to {service_name}",
                client_id=client_id,
                status="success",
            )
            await asyncio.sleep(1)  # Reduced from 3s

            log_activity(
                "Download Report",
                "Navigating to credit report...",
                client_id=client_id,
                status="info",
            )
            report_data = await self._download_report(config, client_id, client_name)
            if report_data and report_data.get("success") != False:
                result["success"] = True
                result["report_path"] = report_data.get("path")
                result["html_content"] = report_data.get("html")
                result["scores"] = report_data.get("scores")
                logger.info(f"Successfully imported report for {client_name}")
            elif report_data and report_data.get("error"):
                result["error"] = report_data.get("error")
                log_credit_import_failed(
                    client_id, service_name, report_data.get("error")
                )

                # Log success with scores
                log_credit_import(client_id, service_name, result["scores"])
            else:
                result["error"] = "Failed to download credit report"
                log_credit_import_failed(
                    client_id, service_name, "Failed to download report"
                )

        except Exception as e:
            logger.error(f"Import failed for {client_name}: {e}")
            result["error"] = str(e)
            log_credit_import_failed(client_id, service_name, str(e))

        finally:
            await self._close_browser()

        return result

    async def _login(
        self, config: Dict[str, Any], username: str, password: str, ssn_last4: str
    ) -> bool:
        """Perform login to credit monitoring service."""
        try:
            logger.info(f"Navigating to {config['login_url']}")
            await self.page.goto(
                config["login_url"], wait_until="domcontentloaded", timeout=30000
            )
            await asyncio.sleep(1)  # Reduced from 3s

            # Wait for visible input fields (not hidden CSRF tokens)
            try:
                await self.page.wait_for_selector(
                    'input[type="email"]:visible, input[type="password"]:visible, input[name="email"]:visible, input[name="username"]:visible',
                    timeout=10000,
                )
            except:
                # Fallback to any visible input
                await self.page.wait_for_selector("input:visible", timeout=10000)
            await asyncio.sleep(0.5)  # Reduced from 2s

            # Handle comma-separated selectors in config
            config_username_selectors = []
            if config["username_selector"]:
                if "," in config["username_selector"]:
                    config_username_selectors = [
                        s.strip() for s in config["username_selector"].split(",")
                    ]
                else:
                    config_username_selectors = [config["username_selector"]]

            username_selectors = config_username_selectors + [
                "#txtUsername",
                'input[name="username"]',
                'input[type="email"]',
                'input[name="email"]',
                'input[id*="user"]',
                'input[id*="User"]',
            ]

            username_filled = False
            for selector in username_selectors:
                if not selector:
                    continue
                try:
                    field = await self.page.query_selector(selector)
                    if field:
                        await field.click()
                        await field.fill("")
                        await field.type(username, delay=50)
                        username_filled = True
                        logger.info(f"Filled username with selector: {selector}")
                        break
                except Exception as e:
                    continue

            if not username_filled:
                logger.error("Could not find username field")
                return False

            await asyncio.sleep(1)

            # Handle comma-separated password selectors
            config_password_selectors = []
            if config["password_selector"]:
                if "," in config["password_selector"]:
                    config_password_selectors = [
                        s.strip() for s in config["password_selector"].split(",")
                    ]
                else:
                    config_password_selectors = [config["password_selector"]]

            password_selectors = config_password_selectors + [
                "#txtPassword",
                'input[type="password"]',
                'input[name="password"]',
            ]

            password_filled = False
            for selector in password_selectors:
                if not selector:
                    continue
                try:
                    field = await self.page.query_selector(selector)
                    if field:
                        await field.click()
                        await field.fill("")
                        await field.type(password, delay=50)
                        password_filled = True
                        logger.info(f"Filled password with selector: {selector}")
                        break
                except Exception as e:
                    continue

            if not password_filled:
                logger.error("Could not find password field")
                return False

            if config.get("ssn_last4_selector") and ssn_last4:
                # Handle comma-separated SSN selectors
                ssn_selectors = []
                if "," in config["ssn_last4_selector"]:
                    ssn_selectors = [
                        s.strip() for s in config["ssn_last4_selector"].split(",")
                    ]
                else:
                    ssn_selectors = [config["ssn_last4_selector"]]

                for selector in ssn_selectors:
                    try:
                        ssn_field = await self.page.query_selector(selector)
                        if ssn_field:
                            await ssn_field.type(ssn_last4, delay=50)
                            logger.info(f"Filled SSN with selector: {selector}")
                            break
                    except:
                        continue

            await asyncio.sleep(1)

            # Handle comma-separated login button selectors
            config_login_selectors = []
            if config["login_button_selector"]:
                if "," in config["login_button_selector"]:
                    config_login_selectors = [
                        s.strip() for s in config["login_button_selector"].split(",")
                    ]
                else:
                    config_login_selectors = [config["login_button_selector"]]

            login_selectors = config_login_selectors + [
                "#imgBtnLogin",
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'input[type="submit"]',
            ]

            for selector in login_selectors:
                if not selector:
                    continue
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        logger.info(f"Clicking login button: {selector}")
                        await button.click()
                        break
                except:
                    continue

            await asyncio.sleep(2)  # Reduced from 5s

            try:
                await self.page.wait_for_load_state("networkidle", timeout=30000)
            except:
                pass

            await asyncio.sleep(1)  # Reduced from 3s

            current_url = self.page.url.lower()
            page_content = await self.page.content()
            page_lower = page_content.lower()

            screenshot_path = (
                REPORTS_DIR
                / f"login_debug_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
            )
            await self.page.screenshot(path=str(screenshot_path))
            logger.info(f"Saved login debug screenshot to {screenshot_path}")

            if (
                "security question" in page_lower
                or "last four digits of your ssn" in page_lower
            ):
                logger.info("Security question page detected - entering SSN last 4")
                if not ssn_last4:
                    logger.error("No SSN last 4 provided for security question")
                    return False

                ssn_selectors = [
                    "#FBfbforcechangesecurityanswer_txtSecurityAnswer",
                    'input[name="userSecurityAnswer"]',
                    'input[id*="SecurityAnswer"]',
                    'input[id*="ssn"]',
                ]

                ssn_entered = False
                for selector in ssn_selectors:
                    try:
                        ssn_field = await self.page.query_selector(selector)
                        if ssn_field:
                            await ssn_field.click()
                            await ssn_field.fill(ssn_last4)
                            ssn_entered = True
                            logger.info(f"Entered SSN with selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue

                if not ssn_entered:
                    logger.error("Could not find SSN input field")
                    return False

                await asyncio.sleep(1)

                submit_selectors = [
                    "#FBfbforcechangesecurityanswer_ibtSubmit",
                    'button[type="submit"]:not([disabled])',
                    'button:has-text("Submit")',
                ]

                for selector in submit_selectors:
                    try:
                        submit_btn = await self.page.query_selector(selector)
                        if submit_btn:
                            await submit_btn.click()
                            logger.info(f"Clicked submit with selector: {selector}")
                            break
                    except:
                        continue

                await asyncio.sleep(2)  # Reduced from 5s
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=30000)
                except:
                    pass

                await asyncio.sleep(1)  # Reduced from 3s
                screenshot_path2 = (
                    REPORTS_DIR
                    / f"after_security_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
                )
                await self.page.screenshot(path=str(screenshot_path2))
                logger.info(f"Saved post-security screenshot to {screenshot_path2}")

                current_url = self.page.url.lower()
                logger.info(f"After security question, URL: {current_url}")

            error_indicators = [
                "invalid login",
                "invalid username",
                "invalid password",
                "incorrect password",
                "login failed",
                "authentication failed",
                "access denied",
            ]

            # Check for site maintenance/downtime - require BOTH a maintenance keyword AND context
            page_content = await self.page.content()
            page_lower = page_content.lower()

            # Only flag as maintenance if we see clear maintenance page indicators
            # Must have BOTH a status word AND a time-related word to avoid false positives
            is_maintenance_page = False
            if "maintenance" in page_lower or "upgrade in progress" in page_lower:
                if any(
                    w in page_lower
                    for w in [
                        "scheduled",
                        "performing",
                        "please check back",
                        "temporarily",
                        "we'll be back",
                    ]
                ):
                    is_maintenance_page = True

            # Also check for server errors
            if (
                "503 service" in page_lower
                or "502 bad gateway" in page_lower
                or "site is down" in page_lower
            ):
                is_maintenance_page = True

            if is_maintenance_page:
                logger.error("SITE DOWN - Maintenance page detected")
                logger.error(
                    "Credit monitoring site is under maintenance. Try again later."
                )
                return False

            for indicator in error_indicators:
                if indicator in page_lower:
                    logger.error(f"Login failed - found error indicator: {indicator}")
                    return False

            if (
                "dashboard" in current_url
                or "account" in current_url
                or "home" in current_url
            ):
                logger.info("Login successful - redirected to member area")
                return True

            if "creditreport" in current_url or "credit-report" in current_url:
                logger.info("Login successful - on credit report page")
                return True

            if "member" in current_url and "login" not in current_url:
                logger.info("Login appears successful - in member area")
                return True

            # Get page title for better logging
            page_title = await self.page.title()
            logger.warning(
                f"Login status unclear - URL: {current_url}, Title: '{page_title}'"
            )
            logger.warning(f"Page content length: {len(page_content)} bytes")

            # If still on login page, login likely failed
            if "login" in current_url.lower():
                logger.error(
                    f"Still on login page after login attempt - check credentials"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Login failed with exception: {e}")
            return False

    async def _download_report(
        self, config: Dict[str, Any], client_id: int, client_name: str
    ) -> Optional[Dict[str, Any]]:
        """Navigate to credit report and download/save it."""
        try:
            flow = config.get("report_download_flow", "")
            captured_data: Dict[str, List[Any]] = {"responses": []}

            async def capture_response(response):
                """Capture XHR responses that might contain credit data."""
                try:
                    url = response.url
                    content_type = response.headers.get("content-type", "")

                    if (
                        "json" in content_type
                        or url.endswith(".json")
                        or "api" in url.lower()
                        or "data" in url.lower()
                    ):
                        try:
                            body = await response.text()
                            if body and len(body) > 100:
                                import json

                                try:
                                    json_data = json.loads(body)
                                    captured_data["responses"].append(
                                        {"url": url, "data": json_data}
                                    )
                                    logger.info(
                                        f"Captured JSON response from: {url[:100]}"
                                    )
                                except:
                                    pass
                        except:
                            pass
                except Exception as e:
                    pass

            self.page.on("response", capture_response)

            if flow == "myscoreiq":
                logger.info("Navigating to MyScoreIQ credit report page...")
                await self.page.goto(
                    "https://member.myscoreiq.com/CreditReport.aspx",
                    wait_until="networkidle",
                    timeout=60000,
                )

                logger.info("Waiting for score elements to render...")
                try:
                    await self.page.wait_for_selector(
                        "td.info.ng-binding", state="visible", timeout=45000
                    )
                except Exception as e:
                    logger.warning(f"Initial selector wait failed: {e}")

                logger.info("Waiting for Angular to render and scores to populate...")
                # Wait for Angular to fully render - 30 attempts x 2 seconds = 60 seconds max
                max_attempts = 30
                for attempt in range(max_attempts):
                    try:
                        # Check both: scores are present AND no unrendered {{}} templates
                        check_result = await self.page.evaluate(
                            """() => {
                            // Check for unrendered Angular templates
                            const bodyText = document.body.textContent;
                            const hasUnrenderedTemplates = bodyText.includes('{{') && bodyText.includes('}}');

                            const tds = document.querySelectorAll('td.info.ng-binding');
                            let scoreCount = 0;
                            tds.forEach(td => {
                                const text = td.textContent.trim();
                                if (/^[3-8]\\d{2}$/.test(text)) {
                                    scoreCount++;
                                }
                            });
                            return { scoreCount, hasUnrenderedTemplates };
                        }"""
                        )
                        score_count = check_result.get("scoreCount", 0)
                        has_templates = check_result.get("hasUnrenderedTemplates", True)

                        logger.info(
                            f"Attempt {attempt + 1}: Found {score_count} scores, unrendered templates: {has_templates}"
                        )

                        # If we have 3 scores, proceed even if some templates haven't rendered
                        # (some parts of MyScoreIQ pages have templates that never render)
                        if score_count >= 3:
                            if not has_templates:
                                logger.info(
                                    "All three bureau scores detected and Angular fully rendered!"
                                )
                            else:
                                logger.info(
                                    "All three bureau scores detected (some templates still unrendered, but proceeding)"
                                )
                            break
                    except Exception as e:
                        logger.warning(f"Score check attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(2)  # Wait 2 seconds between attempts
                else:
                    # Loop completed without finding 3 scores - fail the import
                    logger.error(
                        "FAILED: Could not find credit score data after 30 attempts. Page may not have loaded properly."
                    )
                    return {
                        "success": False,
                        "error": "Page failed to load credit report data. Please try again.",
                    }

                await asyncio.sleep(1)  # Reduced from 3s

                try:
                    show_all = await self.page.query_selector('a:has-text("Show All")')
                    if show_all:
                        await show_all.click()
                        await asyncio.sleep(1)  # Reduced from 3s
                except:
                    pass

            elif flow == "identityiq":
                logger.info("IdentityIQ: Navigating to credit report page...")

                # IdentityIQ uses Angular.js similar to MyScoreIQ
                # Navigate to the credit report page
                await self.page.goto(
                    "https://member.identityiq.com/CreditReport.aspx",
                    wait_until="networkidle",
                    timeout=60000,
                )

                logger.info("Waiting for IdentityIQ Angular content to render...")
                try:
                    await self.page.wait_for_selector(
                        "td.info.ng-binding", state="visible", timeout=45000
                    )
                except Exception as e:
                    logger.warning(f"Initial selector wait failed: {e}")

                # Wait for Angular to render scores - same logic as MyScoreIQ
                max_attempts = 30
                for attempt in range(max_attempts):
                    try:
                        check_result = await self.page.evaluate(
                            """() => {
                            const bodyText = document.body.textContent;
                            const hasUnrenderedTemplates = bodyText.includes('{{') && bodyText.includes('}}');

                            const tds = document.querySelectorAll('td.info.ng-binding');
                            let scoreCount = 0;
                            tds.forEach(td => {
                                const text = td.textContent.trim();
                                if (/^[3-8]\\d{2}$/.test(text)) {
                                    scoreCount++;
                                }
                            });
                            return { scoreCount, hasUnrenderedTemplates };
                        }"""
                        )
                        score_count = check_result.get("scoreCount", 0)
                        has_templates = check_result.get("hasUnrenderedTemplates", True)

                        logger.info(
                            f"IdentityIQ attempt {attempt + 1}: Found {score_count} scores, unrendered: {has_templates}"
                        )

                        if score_count >= 3:
                            logger.info("IdentityIQ: All three bureau scores detected!")
                            break
                    except Exception as e:
                        logger.warning(
                            f"IdentityIQ score check attempt {attempt + 1} failed: {e}"
                        )
                    await asyncio.sleep(2)
                else:
                    logger.error(
                        "IdentityIQ: Could not find credit score data after 30 attempts."
                    )
                    return {
                        "success": False,
                        "error": "IdentityIQ page failed to load credit report data. Please try again.",
                    }

                await asyncio.sleep(1)

                # Try to click "Show All" to expand all sections
                try:
                    show_all = await self.page.query_selector('a:has-text("Show All")')
                    if show_all:
                        await show_all.click()
                        await asyncio.sleep(1)
                except:
                    pass

                report_found = True

            elif flow == "myfreescorenow":
                logger.info("MyFreeScoreNow: Navigating directly to 3B Report page...")

                # DIRECT NAVIGATION to 3B page (has all 3 bureau scores)
                # This is more reliable than clicking links
                three_b_url = (
                    "https://member.myfreescorenow.com/member/credit-report/smart-3b/"
                )
                logger.info(f"Navigating directly to: {three_b_url}")

                try:
                    await self.page.goto(
                        three_b_url, wait_until="domcontentloaded", timeout=30000
                    )
                    await asyncio.sleep(2)  # Wait for Vue.js to initialize
                    await self.page.wait_for_load_state("networkidle", timeout=30000)

                    page_title = await self.page.title()
                    current_url = self.page.url
                    logger.info(f"Navigated to: {page_title} at {current_url}")

                    # Take debug screenshot of 3B page
                    debug_path = f"uploads/credit_reports/debug_3b_{client_id}.png"
                    await self.page.screenshot(path=debug_path, full_page=True)
                    logger.info(f"Saved 3B page screenshot to {debug_path}")

                except Exception as e:
                    logger.warning(
                        f"Direct 3B navigation failed: {e}, trying Smart Credit Report..."
                    )
                    # Fallback to Smart Credit Report
                    fallback_url = "https://member.myfreescorenow.com/member/smart-credit-report.htm"
                    await self.page.goto(
                        fallback_url, wait_until="networkidle", timeout=30000
                    )

                report_found = True

                logger.info("Waiting for credit report page to load...")
                await asyncio.sleep(2)  # Reduced from 5s

                # MyFreeScoreNow uses Vue.js with client-side rendering
                # We MUST wait for Vue to render content inside #smartcredit-app
                logger.info("Waiting for Vue.js to render content...")

                # Wait for Vue.js app to populate with actual content
                vue_content_selectors = [
                    ".account-container",  # Account cards
                    ".bureau-score",  # Score display
                    ".report-header",  # Report header section
                    "[data-test-account-name]",  # Account names
                    ".credit-score-container",  # Score containers
                    ".account-section",  # Account sections
                ]

                vue_rendered = False
                max_vue_attempts = 20  # Wait up to 60 seconds for Vue to render
                for attempt in range(max_vue_attempts):
                    try:
                        # Check if Vue has rendered content inside #smartcredit-app
                        has_content = await self.page.evaluate(
                            """() => {
                            const app = document.querySelector('#smartcredit-app');
                            if (!app) return false;

                            // Check if Vue has rendered actual content (not just the shell)
                            const innerContent = app.innerHTML.trim();
                            if (innerContent.length < 100) return false;  // Empty or minimal

                            // Look for Vue-rendered elements
                            const hasAccounts = app.querySelectorAll('.account-container').length > 0;
                            const hasScores = app.querySelectorAll('[class*="score"]').length > 0;
                            const hasReportData = app.querySelectorAll('[data-test-account-name]').length > 0;

                            return hasAccounts || hasScores || hasReportData || innerContent.length > 500;
                        }"""
                        )

                        if has_content:
                            logger.info(
                                f"Vue.js content detected after {attempt + 1} attempts"
                            )
                            vue_rendered = True
                            break
                        else:
                            logger.info(
                                f"Vue attempt {attempt + 1}: Waiting for content to render..."
                            )
                    except Exception as e:
                        logger.warning(f"Vue check attempt {attempt + 1} failed: {e}")

                    await asyncio.sleep(1)  # Reduced from 3s

                if not vue_rendered:
                    logger.warning(
                        "Vue.js may not have fully rendered - proceeding anyway..."
                    )

                # Additional wait for any lazy-loaded content
                await asyncio.sleep(1)  # Reduced from 3s

                # MyFreeScoreNow uses modern React/Vue, different selectors than Angular
                score_selectors = [
                    ".score-value",
                    ".credit-score",
                    '[class*="score"]',
                    ".score-number",
                    'div[class*="Score"]',
                    'span[class*="score"]',
                ]

                logger.info("Waiting for score elements to render...")
                score_found = False
                for selector in score_selectors:
                    try:
                        await self.page.wait_for_selector(
                            selector, state="visible", timeout=10000
                        )
                        logger.info(f"Found score elements with selector: {selector}")
                        score_found = True
                        break
                    except Exception as e:
                        logger.debug(f"Selector {selector} not found: {e}")
                        continue

                if not score_found:
                    logger.warning(
                        "Could not find score elements with known selectors, continuing anyway..."
                    )

                # Wait for scores to populate
                logger.info("Waiting for scores to populate with numeric values...")
                max_attempts = 15
                for attempt in range(max_attempts):
                    try:
                        score_count = await self.page.evaluate(
                            """() => {
                            // Try multiple patterns to find scores
                            const allText = document.body.innerText;
                            const scorePattern = /\\b([3-8]\\d{2})\\b/g;
                            const matches = allText.match(scorePattern) || [];
                            // Look for exactly 3 scores in typical range
                            const validScores = matches.filter(s => {
                                const num = parseInt(s);
                                return num >= 300 && num <= 850;
                            });
                            return validScores.length >= 3 ? 3 : validScores.length;
                        }"""
                        )
                        logger.info(
                            f"Attempt {attempt + 1}: Found {score_count} score values"
                        )
                        if score_count >= 3:
                            logger.info("All three bureau scores detected!")
                            break
                    except Exception as e:
                        logger.warning(f"Score check attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(1)  # Reduced from 3s

                await asyncio.sleep(1)  # Reduced from 3s

                # Try to expand all account details
                try:
                    expand_buttons = [
                        'button:has-text("Show All")',
                        'button:has-text("View All")',
                        'button:has-text("Expand")',
                        'a:has-text("Show All")',
                        ".expand-all",
                        '[class*="expand"]',
                    ]
                    for btn_selector in expand_buttons:
                        try:
                            expand_btn = await self.page.query_selector(btn_selector)
                            if expand_btn:
                                await expand_btn.click()
                                await asyncio.sleep(2)
                                logger.info(f"Clicked expand button: {btn_selector}")
                                break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"No expand button found: {e}")

            else:
                report_selectors = [
                    'a[href*="credit-report"]',
                    'a[href*="creditreport"]',
                    'a[href*="CreditReport"]',
                    'a[href*="view-report"]',
                    'a[href*="viewreport"]',
                    ".credit-report-link",
                    "#view-report",
                    'a:has-text("View Report")',
                    'a:has-text("Credit Report")',
                    'a:has-text("View Credit Report")',
                    'a:has-text("3 Bureau Credit Report")',
                    'button:has-text("View Report")',
                ]

                for selector in report_selectors:
                    try:
                        link = await self.page.query_selector(selector)
                        if link:
                            await link.click()
                            await self.page.wait_for_load_state(
                                "networkidle", timeout=30000
                            )
                            await asyncio.sleep(2)
                            break
                    except:
                        continue

            await asyncio.sleep(2)  # Reduced from 5s

            # MyFreeScoreNow: Try to switch to Classic View which shows ALL data including inquiries/contacts
            try:
                classic_btn = await self.page.query_selector(
                    'button:has-text("Classic View"), button:has-text("Switch to Classic")'
                )
                if classic_btn:
                    logger.info(
                        "Found 'Switch to Classic View' button - clicking to load full report..."
                    )
                    await classic_btn.click()
                    await asyncio.sleep(5)  # Wait for classic view to load
                    # Wait for the classic report format to render
                    await self.page.wait_for_selector(
                        ".rpt_content_wrapper, #CreditorContacts, #Inquiries, table.rpt_content_header",
                        timeout=10000,
                    )
                    logger.info("Switched to Classic View successfully")
            except Exception as e:
                logger.info(f"Classic view switch not available or failed: {e}")

            # Scroll to load ALL sections including Inquiries and Creditor Contacts at bottom
            logger.info(
                "Scrolling page to load ALL sections (accounts, inquiries, contacts)..."
            )
            try:
                previous_height = 0
                # Scroll more aggressively to ensure we get to the bottom
                for attempt in range(20):  # Increased from 10
                    await self.page.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )
                    await asyncio.sleep(1.5)  # Faster scrolling
                    new_height = await self.page.evaluate("document.body.scrollHeight")
                    if new_height == previous_height:
                        # Double-check by trying to scroll again
                        await asyncio.sleep(2)
                        await self.page.evaluate(
                            "window.scrollTo(0, document.body.scrollHeight)"
                        )
                        await asyncio.sleep(1)
                        final_height = await self.page.evaluate(
                            "document.body.scrollHeight"
                        )
                        if final_height == new_height:
                            logger.info(
                                f"Scrolling complete after {attempt + 1} attempts"
                            )
                            break
                        new_height = final_height
                    previous_height = new_height
                    logger.info(
                        f"Scroll attempt {attempt + 1}: page height {new_height}px"
                    )

                # Try to scroll to specific sections by clicking nav links
                try:
                    inquiries_link = await self.page.query_selector(
                        "li:has-text('Inquiries')"
                    )
                    if inquiries_link:
                        await inquiries_link.click()
                        await asyncio.sleep(2)
                        logger.info("Clicked Inquiries nav link to load section")
                except:
                    pass

                try:
                    contacts_link = await self.page.query_selector(
                        "li:has-text('Creditor Contacts')"
                    )
                    if contacts_link:
                        await contacts_link.click()
                        await asyncio.sleep(2)
                        logger.info(
                            "Clicked Creditor Contacts nav link to load section"
                        )
                except:
                    pass

                await self.page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Scroll failed: {e}")

            # Expand all "View all details" sections to capture full account data
            # IMPORTANT: Must click each button sequentially with waits so Vue.js can render each modal
            logger.info(
                "Expanding all account details (clicking each sequentially with Playwright)..."
            )
            try:
                # Get all view-more-link elements using Playwright locator
                view_more_links = await self.page.locator(".view-more-link").all()
                view_details_count = len(view_more_links)
                logger.info(
                    f"Found {view_details_count} 'View all details' links to click"
                )

                # Click each one sequentially using Playwright's native click() method
                # Limit to first 10 to avoid long waits - the HTML capture will still get all data
                max_expand = min(10, len(view_more_links))
                expanded_count = 0
                for i, link in enumerate(view_more_links[:max_expand]):
                    try:
                        # Scroll the link into view and click it with timeout
                        await link.scroll_into_view_if_needed()
                        await link.click(timeout=5000)
                        expanded_count += 1
                        logger.info(f"Expanded {expanded_count}/{max_expand}")

                        # Brief wait for Vue.js
                        await asyncio.sleep(0.3)

                        if (i + 1) % 5 == 0:
                            logger.info(
                                f"Expanded {i + 1}/{view_details_count} account details..."
                            )
                    except Exception as e:
                        logger.debug(f"Failed to click link {i}: {e}")
                        continue

                if expanded_count > 0:
                    logger.info(
                        f"Clicked {expanded_count}/{view_details_count} 'View all details' links"
                    )
                    # Final wait for all content to settle
                    await asyncio.sleep(1)  # Reduced from 3s

                    # Verify payment history sections were loaded
                    payment_history_count = await self.page.evaluate(
                        """() => {
                        return document.querySelectorAll('.account-modal .payment-history').length;
                    }"""
                    )
                    logger.info(
                        f"Found {payment_history_count} payment history sections in modals after expansion"
                    )
            except Exception as e:
                logger.warning(f"Failed to expand account details: {e}")

            # JavaScript-based modal expansion - more reliable than clicking
            # This injects CSS/JS to make ALL modals visible regardless of Vue state
            logger.info(
                "Force-expanding all account modals via JavaScript injection..."
            )
            try:
                expanded_via_js = await self.page.evaluate(
                    """() => {
                    let expandedCount = 0;

                    // Method 1: Click all "View all details" links programmatically
                    const viewLinks = document.querySelectorAll('.view-more-link, .view-more-link p');
                    viewLinks.forEach((link, i) => {
                        try {
                            link.click();
                            expandedCount++;
                        } catch(e) {}
                    });

                    // Method 2: Force all account-modal elements to be visible via CSS
                    const modals = document.querySelectorAll('.account-modal, .account-modal-bg');
                    modals.forEach(modal => {
                        modal.style.display = 'block';
                        modal.style.visibility = 'visible';
                        modal.style.opacity = '1';
                        modal.style.position = 'relative';
                        modal.style.height = 'auto';
                    });

                    // Method 3: Try to trigger Vue component expansion if available
                    const containers = document.querySelectorAll('.account-container');
                    containers.forEach(container => {
                        // Look for Vue instance data
                        const vueInstance = container.__vue__;
                        if (vueInstance && typeof vueInstance.showDetails !== 'undefined') {
                            vueInstance.showDetails = true;
                        }
                    });

                    return {
                        clickedLinks: viewLinks.length,
                        modalsForced: modals.length,
                        containers: containers.length
                    };
                }"""
                )
                logger.info(f"JS modal expansion result: {expanded_via_js}")

                # Wait for Vue to re-render after our changes
                await asyncio.sleep(2)

                # Verify modals are now visible
                modal_count = await self.page.evaluate(
                    """() => {
                    const visibleModals = document.querySelectorAll('.account-modal');
                    let visibleCount = 0;
                    visibleModals.forEach(m => {
                        const style = window.getComputedStyle(m);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            visibleCount++;
                        }
                    });
                    return { total: visibleModals.length, visible: visibleCount };
                }"""
                )
                logger.info(f"After JS expansion: {modal_count}")

            except Exception as e:
                logger.warning(f"JS modal expansion failed: {e}")

            # Expand Creditor Contacts section if it has a "Show" toggle button
            try:
                show_result = await self.page.evaluate(
                    """() => {
                    let clicked = false;
                    // Find the Creditor Contacts section and click the Show button
                    document.querySelectorAll('h5.fw-bold, h5').forEach(h => {
                        if (h.textContent.includes('Creditor Contacts')) {
                            const section = h.closest('section') || h.parentElement?.parentElement;
                            if (section) {
                                const showBtn = section.querySelector('.creditor-toggle span, small span');
                                if (showBtn && showBtn.textContent.trim() === 'Show') {
                                    showBtn.click();
                                    clicked = true;
                                }
                            }
                        }
                    });
                    return clicked;
                }"""
                )
                if show_result:
                    logger.info(
                        "Clicked 'Show' button to expand Creditor Contacts section"
                    )
                    await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"Creditor Contacts expansion: {e}")

            logger.info(f"Captured {len(captured_data['responses'])} XHR responses")
            for resp in captured_data["responses"]:
                logger.info(f"  - {resp['url'][:80]}")

            # Final verification: Check that we have rendered content before capturing
            logger.info("Verifying page content before capture...")
            try:
                content_check = await self.page.evaluate(
                    """() => {
                    const result = {
                        hasSmartCreditApp: false,
                        appContentLength: 0,
                        accountCount: 0,
                        scoreElementCount: 0,
                        pageTitle: document.title,
                        bodyLength: document.body.innerHTML.length
                    };

                    const app = document.querySelector('#smartcredit-app');
                    if (app) {
                        result.hasSmartCreditApp = true;
                        result.appContentLength = app.innerHTML.length;
                        result.accountCount = app.querySelectorAll('.account-container, [data-test-account-name]').length;
                        result.scoreElementCount = app.querySelectorAll('[class*="score"], .bureau-score').length;
                    }

                    return result;
                }"""
                )
                logger.info(f"Content verification: {content_check}")

                # If #smartcredit-app exists but has minimal content, wait more
                if (
                    content_check.get("hasSmartCreditApp")
                    and content_check.get("appContentLength", 0) < 1000
                ):
                    logger.warning(
                        "Vue app exists but content is minimal - waiting longer..."
                    )
                    await asyncio.sleep(10)  # Extra wait for slow rendering

            except Exception as e:
                logger.warning(f"Content verification failed: {e}")

            # Take a debug screenshot
            debug_screenshot = (
                REPORTS_DIR / f"debug_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
            )
            await self.page.screenshot(path=str(debug_screenshot), full_page=True)
            logger.info(f"Saved debug screenshot to {debug_screenshot}")

            html_content = await self.page.content()

            scores = await self._extract_scores()
            accounts = self._extract_accounts_from_xhr(captured_data["responses"])

            if not accounts:
                accounts = await self._extract_accounts_data()

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(
                c if c.isalnum() or c in ("-", "_") else "_" for c in client_name
            )
            filename = f"{client_id}_{safe_name}_{timestamp}.html"
            filepath = REPORTS_DIR / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            import json

            xhr_filename = f"{client_id}_{safe_name}_{timestamp}_xhr.json"
            xhr_filepath = REPORTS_DIR / xhr_filename
            with open(xhr_filepath, "w", encoding="utf-8") as f:
                json.dump(captured_data["responses"], f, indent=2)
            logger.info(f"Saved XHR data to {xhr_filepath}")

            # Extract personal info (names, addresses, DOB, employers, inquiries, creditor contacts)
            personal_info = {}
            summary_info = {}
            inquiries = []
            creditor_contacts = []
            try:
                personal_data = await self.page.evaluate(
                    """() => {
                    const data = {
                        names: [],
                        addresses: [],
                        dob: null,
                        employers: [],
                        ssn_last4: null,
                        // Per-bureau data for MyScoreIQ format
                        transunion: { names: [], dob: null, current_address: null, previous_addresses: [], employers: [] },
                        experian: { names: [], dob: null, current_address: null, previous_addresses: [], employers: [] },
                        equifax: { names: [], dob: null, current_address: null, previous_addresses: [], employers: [] }
                    };
                    const summary = {
                        total_accounts: null,
                        open_accounts: null,
                        closed_accounts: null,
                        delinquent_accounts: null,
                        derogatory_accounts: null,
                        collection: null,
                        total_balances: null,
                        total_payments: null,
                        public_records: null,
                        total_inquiries: null,
                        // Per-bureau summary data
                        transunion: {},
                        experian: {},
                        equifax: {}
                    };
                    const inquiries = [];

                    // Parse Personal Information section
                    const personalSection = document.querySelector('.attribute-collection');
                    if (personalSection) {
                        const rows = personalSection.querySelectorAll('.attribute-row');
                        rows.forEach(row => {
                            const label = row.querySelector('.text-gray-900')?.textContent.toLowerCase() || '';
                            const value = row.querySelector('.display-attribute p')?.textContent.trim();

                            if (label.includes('name') && value) {
                                data.names.push(value);
                                // Check for aliases
                                const aliasLink = row.querySelector('.text-link');
                                if (aliasLink && aliasLink.textContent.includes('aliases')) {
                                    // Would need to click to expand - note presence
                                    data.has_aliases = true;
                                }
                            }
                            if (label.includes('birth') && value) {
                                data.dob = value;
                            }
                            if (label.includes('address') && value) {
                                data.addresses.push(value.replace(/\\s+/g, ' '));
                                const priorLink = row.querySelector('.text-link');
                                if (priorLink && priorLink.textContent.includes('prior')) {
                                    data.has_prior_addresses = true;
                                }
                            }
                            if (label.includes('employer') && value) {
                                const empDivs = row.querySelectorAll('.title-case');
                                empDivs.forEach(e => {
                                    if (e.textContent.trim()) data.employers.push(e.textContent.trim());
                                });
                            }
                        });
                    }

                    // Parse Summary section - Modern View
                    const summaryRows = document.querySelectorAll('.attribute-collection .attribute-row');
                    summaryRows.forEach(row => {
                        const label = row.querySelector('.text-gray-900')?.textContent.toLowerCase() || '';
                        const value = row.querySelector('.display-attribute p')?.textContent.trim();
                        if (!value) return;

                        if (label.includes('total accounts')) summary.total_accounts = value;
                        if (label.includes('open accounts')) summary.open_accounts = value;
                        if (label.includes('closed accounts')) summary.closed_accounts = value;
                        if (label.includes('delinquent')) summary.delinquent_accounts = value;
                        if (label.includes('derogatory')) summary.derogatory_accounts = value;
                        if (label.includes('balances')) summary.total_balances = value;
                        if (label.includes('payments') && !label.includes('late')) summary.total_payments = value;
                        if (label.includes('inquiries')) summary.total_inquiries = value;
                    });

                    // Parse Summary section - Classic/Original View fallback
                    if (!summary.total_accounts) {
                        let summarySection = null;
                        document.querySelectorAll('h5.fw-bold, h5').forEach(h => {
                            if (h.textContent.trim() === 'Summary' || h.textContent.trim() === ' Summary ') {
                                summarySection = h.closest('section') || h.parentElement?.parentElement;
                            }
                        });
                        if (summarySection) {
                            const grid = summarySection.querySelector('.d-grid.grid-cols-4');
                            if (grid) {
                                // Labels are in first column, TU values in 2nd column
                                // But first row is header (bureau names), data starts at row 2
                                const labels = grid.querySelectorAll('.labels .grid-cell');
                                const tuDiv = grid.querySelector('.d-contents:nth-child(2)');
                                if (tuDiv) {
                                    const tuCells = tuDiv.querySelectorAll('.grid-cell');
                                    // tuCells[0] is header "transunion", tuCells[1] is Total Accounts value, etc.
                                    labels.forEach((labelCell, i) => {
                                        const label = labelCell.textContent.toLowerCase();
                                        // i+1 because tuCells[0] is the header
                                        const value = tuCells[i + 1]?.textContent.trim();
                                        if (!value || value.includes('transunion') || value.includes('experian') || value.includes('equifax')) return;
                                        if (label.includes('total accounts')) summary.total_accounts = value;
                                        if (label.includes('open accounts')) summary.open_accounts = value;
                                        if (label.includes('closed accounts')) summary.closed_accounts = value;
                                        if (label.includes('delinquent')) summary.delinquent_accounts = value;
                                        if (label.includes('derogatory')) summary.derogatory_accounts = value;
                                        if (label.includes('balances')) summary.total_balances = value;
                                        if (label.includes('payments') && !label.includes('late')) summary.total_payments = value;
                                        if (label.includes('inquiries')) summary.total_inquiries = value;
                                    });
                                }
                            }
                        }
                    }

                    // MYSCOREIQ Summary fallback - uses #Summary id and rpt_content_table
                    if (!summary.total_accounts) {
                        const summaryHeader = document.querySelector('#Summary, .rpt_fullReport_header[id="Summary"]');
                        if (summaryHeader) {
                            // Find the rpt_content_table within the wrapper or after the summary header
                            let summaryTable = null;
                            // First try: look in the wrapper
                            const wrapper = summaryHeader.closest('.rpt_content_wrapper');
                            if (wrapper) {
                                summaryTable = wrapper.querySelector('table.rpt_content_table.rpt_table4column');
                            }
                            // Fallback: walk through siblings
                            if (!summaryTable) {
                                let el = summaryHeader.nextElementSibling;
                                while (el && !summaryTable) {
                                    if (el.tagName === 'TABLE' && el.classList?.contains('rpt_content_table') && !el.classList?.contains('help_text')) {
                                        summaryTable = el;
                                    }
                                    el = el.nextElementSibling;
                                }
                            }
                            if (summaryTable) {
                                const rows = summaryTable.querySelectorAll('tr');
                                rows.forEach(row => {
                                    const labelCell = row.querySelector('td.label');
                                    if (!labelCell) return;
                                    const label = labelCell.textContent.toLowerCase().trim();
                                    // Get all info cells (TransUnion, Experian, Equifax columns)
                                    const infoCells = row.querySelectorAll('td.info');
                                    if (infoCells.length === 0) return;

                                    // Column order: TransUnion, Experian, Equifax
                                    const bureaus = ['transunion', 'experian', 'equifax'];

                                    // Parse values for each bureau
                                    infoCells.forEach((cell, idx) => {
                                        if (idx >= 3) return;
                                        const bureau = bureaus[idx];
                                        const value = cell.textContent.trim();
                                        if (!value || value === '-') return;

                                        // Store per-bureau values
                                        if (label.includes('total accounts')) {
                                            summary[bureau].total_accounts = value;
                                            if (!summary.total_accounts) summary.total_accounts = value;
                                        }
                                        else if (label.includes('open accounts')) {
                                            summary[bureau].open_accounts = value;
                                            if (!summary.open_accounts) summary.open_accounts = value;
                                        }
                                        else if (label.includes('closed accounts')) {
                                            summary[bureau].closed_accounts = value;
                                            if (!summary.closed_accounts) summary.closed_accounts = value;
                                        }
                                        else if (label.includes('delinquent')) {
                                            summary[bureau].delinquent = value;
                                            if (!summary.delinquent_accounts) summary.delinquent_accounts = value;
                                        }
                                        else if (label.includes('derogatory')) {
                                            summary[bureau].derogatory = value;
                                            if (!summary.derogatory_accounts) summary.derogatory_accounts = value;
                                        }
                                        else if (label.includes('collection')) {
                                            summary[bureau].collection = value;
                                            if (!summary.collection) summary.collection = value;
                                        }
                                        else if (label.includes('balance')) {
                                            summary[bureau].balances = value;
                                            if (!summary.total_balances) summary.total_balances = value;
                                        }
                                        else if (label.includes('payment') && !label.includes('late')) {
                                            summary[bureau].payments = value;
                                            if (!summary.total_payments) summary.total_payments = value;
                                        }
                                        else if (label.includes('public record')) {
                                            summary[bureau].public_records = value;
                                            if (!summary.public_records) summary.public_records = value;
                                        }
                                        else if (label.includes('inquir')) {
                                            summary[bureau].inquiries = value;
                                            if (!summary.total_inquiries) summary.total_inquiries = value;
                                        }
                                    });
                                });
                            }
                        }
                    }

                    // Parse Inquiries section - try multiple formats
                    // Method 1: MyScoreIQ format - uses #Inquiries wrapper with table rows
                    // Columns: Creditor Name | Type of Business | Date of Inquiry | Credit Bureau
                    const classicInquiries = document.querySelector('#Inquiries, .rpt_content_wrapper[id="Inquiries"]');
                    if (classicInquiries) {
                        // Get the table inside the inquiries wrapper
                        const inquiryTable = classicInquiries.querySelector('table.rpt_content_table');
                        if (inquiryTable) {
                            const rows = inquiryTable.querySelectorAll('tr');
                            rows.forEach(row => {
                                // Skip header rows (th elements)
                                if (row.querySelector('th')) return;

                                const cells = row.querySelectorAll('td.info');
                                if (cells.length >= 4) {
                                    const company = cells[0]?.textContent.trim();
                                    const type = cells[1]?.textContent.trim();  // Type of Business
                                    const date = cells[2]?.textContent.trim();  // Date of Inquiry
                                    const bureau = cells[3]?.textContent.trim();  // Credit Bureau

                                    if (company && company.length > 2 && !company.includes('Creditor')) {
                                        // Parse bureau to set flags
                                        const bureauLower = (bureau || '').toLowerCase();
                                        inquiries.push({
                                            company,
                                            type: type || null,
                                            date: date || null,
                                            bureau: bureau || null,
                                            transunion: bureauLower.includes('transunion'),
                                            experian: bureauLower.includes('experian'),
                                            equifax: bureauLower.includes('equifax'),
                                            source: 'myscoreiq'
                                        });
                                    }
                                }
                            });
                        }
                    }

                    // Method 2: Modern 3B View - look for Inquiries headline section
                    if (inquiries.length === 0) {
                        let inquirySection = null;
                        let inquirySectionParent = null;
                        document.querySelectorAll('h2.headline, h2, h3').forEach(h => {
                            if (h.textContent.trim() === 'Inquiries' || h.textContent.includes('Inquiries')) {
                                inquirySection = h;
                                inquirySectionParent = h.closest('.col-xs-12, .col-lg-8, div');
                            }
                        });

                        if (inquirySection && inquirySectionParent) {
                            const inquiryContainers = inquirySectionParent.querySelectorAll('.inquiry-container, .inquiry-row, .attribute-row, [class*="inquiry"]');
                            inquiryContainers.forEach(inq => {
                                const company = inq.querySelector('[data-test-inquiry-name], strong, .creditor, .company-name, .fw-bold, .fw-semi')?.textContent.trim();
                                const dateEl = inq.querySelector('.date, .inquiry-date, .text-gray-600, small');
                                const date = dateEl?.textContent.trim();
                                const tuPresent = !!inq.querySelector('.text-transunion, [class*="transunion"]');
                                const exPresent = !!inq.querySelector('.text-experian, [class*="experian"]');
                                const eqPresent = !!inq.querySelector('.text-equifax, [class*="equifax"]');

                                if (company && company.length > 1 && !company.includes('Inquiries')) {
                                    inquiries.push({
                                        company,
                                        date: date || null,
                                        transunion: tuPresent,
                                        experian: exPresent,
                                        equifax: eqPresent,
                                        source: 'modern'
                                    });
                                }
                            });
                        }
                    }

                    // Method 3: Look for inquiry-collection divs (common pattern)
                    if (inquiries.length === 0) {
                        document.querySelectorAll('.inquiry-collection .account-container, [class*="inquiry"] .account-heading').forEach(inq => {
                            const company = inq.querySelector('strong, .fs-16')?.textContent.trim();
                            const date = inq.querySelector('small, .text-gray-600, p:last-child')?.textContent.trim();
                            if (company) {
                                inquiries.push({ company, date, source: 'collection' });
                            }
                        });
                    }

                    // Also try to find inquiries from the account list (some reports list them there)
                    if (inquiries.length === 0) {
                        const allAccounts = document.querySelectorAll('.account-container');
                        allAccounts.forEach(acc => {
                            const accType = acc.querySelector('.account-type, [class*="type"]')?.textContent.toLowerCase() || '';
                            if (accType.includes('inquiry') || accType.includes('inq')) {
                                const company = acc.querySelector('.creditor-name, .company, strong')?.textContent.trim();
                                const date = acc.querySelector('.date, .inquiry-date')?.textContent.trim();
                                if (company) {
                                    inquiries.push({ company, date, type: 'inquiry' });
                                }
                            }
                        });
                    }

                    // Method 4: Classic/Original View - h5.fw-bold "Inquiries" with .d-grid.grid-cols-3 rows
                    if (inquiries.length === 0) {
                        let inquirySection = null;
                        document.querySelectorAll('h5.fw-bold, h5').forEach(h => {
                            const text = h.textContent.trim();
                            if (text === 'Inquiries' || text === ' Inquiries ') {
                                inquirySection = h.closest('section') || h.parentElement?.parentElement;
                            }
                        });

                        if (inquirySection) {
                            // Get all grid-cols-3 divs (skip first one which is header)
                            const grids = inquirySection.querySelectorAll('.d-grid.grid-cols-3');
                            grids.forEach((grid, index) => {
                                if (index === 0) return; // Skip header row
                                const cells = grid.querySelectorAll('.grid-cell, p');
                                if (cells.length >= 3) {
                                    const company = cells[0]?.textContent.trim();
                                    const date = cells[1]?.textContent.trim();
                                    const bureau = cells[2]?.textContent.trim().toLowerCase();
                                    if (company && company.length > 1 &&
                                        !company.includes('Creditor') && !company.includes('Date') && !company.includes('Bureau')) {
                                        inquiries.push({
                                            company,
                                            date: date || null,
                                            bureau: bureau || null,
                                            transunion: bureau?.includes('transunion'),
                                            experian: bureau?.includes('experian'),
                                            equifax: bureau?.includes('equifax'),
                                            source: 'original-view'
                                        });
                                    }
                                }
                            });
                        }
                    }

                    // Method 5: MyScoreIQ format - uses rpt_content_table with headerTUC, headerEXP, headerEQF columns
                    if (inquiries.length === 0) {
                        // Find Inquiries section header
                        let inquiryTable = null;
                        document.querySelectorAll('.rpt_fullReport_header, h3, h4').forEach(header => {
                            if (header.textContent.includes('Inquiries') || header.textContent.includes('INQUIRIES')) {
                                // Find the next table.rpt_content_table after this header
                                let el = header.nextElementSibling;
                                while (el && !inquiryTable) {
                                    if (el.classList?.contains('rpt_content_table')) {
                                        inquiryTable = el;
                                    } else if (el.querySelector) {
                                        inquiryTable = el.querySelector('table.rpt_content_table');
                                    }
                                    el = el.nextElementSibling;
                                }
                                // Also check parent's siblings
                                if (!inquiryTable) {
                                    let parent = header.parentElement;
                                    let sib = parent?.nextElementSibling;
                                    while (sib && !inquiryTable) {
                                        if (sib.tagName === 'TABLE' && sib.classList?.contains('rpt_content_table')) {
                                            inquiryTable = sib;
                                        } else if (sib.querySelector) {
                                            inquiryTable = sib.querySelector('table.rpt_content_table');
                                        }
                                        sib = sib.nextElementSibling;
                                    }
                                }
                            }
                        });

                        if (inquiryTable) {
                            const rows = inquiryTable.querySelectorAll('tr');
                            rows.forEach(row => {
                                const labelCell = row.querySelector('td.label');
                                if (!labelCell) return;
                                const label = labelCell.textContent.trim().toLowerCase();

                                // Skip header rows
                                if (label.includes('creditor') || label.includes('inquiry') || label.includes('date')) return;

                                const infoCells = row.querySelectorAll('td.info');
                                if (infoCells.length >= 3) {
                                    // Column order: TransUnion, Experian, Equifax
                                    const bureaus = ['transunion', 'experian', 'equifax'];
                                    infoCells.forEach((cell, idx) => {
                                        if (idx >= 3) return;
                                        const bureau = bureaus[idx];
                                        const text = cell.textContent.replace(/\\s+/g, ' ').trim();
                                        if (!text || text === '-' || text === 'N/A') return;

                                        // Parse creditor name and date from the cell
                                        // Format could be "CREDITOR NAME\\n01/15/2024" or just "CREDITOR NAME"
                                        const lines = text.split(/[\\n\\r]+/);
                                        const company = lines[0]?.trim();
                                        const date = lines.length > 1 ? lines[1]?.trim() : null;

                                        if (company && company.length > 2) {
                                            // Check if this inquiry already exists for this company
                                            const existing = inquiries.find(i => i.company === company);
                                            if (existing) {
                                                // Add bureau flag to existing
                                                existing[bureau] = true;
                                            } else {
                                                inquiries.push({
                                                    company,
                                                    date: date || null,
                                                    transunion: bureau === 'transunion',
                                                    experian: bureau === 'experian',
                                                    equifax: bureau === 'equifax',
                                                    source: 'myscoreiq'
                                                });
                                            }
                                        }
                                    });
                                }
                            });
                        }
                    }

                    // Parse Creditor Contacts section (addresses/phones at bottom of report)
                    const creditorContacts = [];

                    // Method 1: Classic View - uses #CreditorContacts wrapper with table
                    const classicContacts = document.querySelector('#CreditorContacts, .rpt_content_wrapper[id*="Creditor"]');
                    if (classicContacts) {
                        const rows = classicContacts.querySelectorAll('tr');
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 2) {
                                const name = cells[0]?.textContent.trim();
                                const address = cells[1]?.textContent.trim();
                                const phone = cells.length > 2 ? cells[2]?.textContent.trim() : null;
                                if (name && name.length > 2 && !name.includes('Creditor Name') && !name.includes('Address')) {
                                    creditorContacts.push({ name, address, phone, source: 'classic' });
                                }
                            }
                        });
                    }

                    // Method 2: Modern View - look for Creditor Contacts headline
                    if (creditorContacts.length === 0) {
                        let contactsSection = null;
                        document.querySelectorAll('h2.headline, h2, h3').forEach(h => {
                            if (h.textContent.includes('Creditor Contacts') || h.textContent.includes('Creditor Contact')) {
                                contactsSection = h.closest('.col-xs-12, .col-lg-8, div');
                            }
                        });
                        if (contactsSection) {
                            const contactRows = contactsSection.querySelectorAll('.attribute-row, .contact-row, .creditor-contact, tr');
                            contactRows.forEach(row => {
                                const name = row.querySelector('strong, .creditor-name, .fw-bold, td:first-child')?.textContent.trim();
                                const address = row.querySelector('.address, p:nth-child(2), td:nth-child(2)')?.textContent.trim();
                                const phone = row.querySelector('.phone, [href^="tel:"], td:nth-child(3)')?.textContent.trim();
                                if (name && name.length > 1 && !name.includes('Creditor')) {
                                    creditorContacts.push({ name, address, phone, source: 'modern' });
                                }
                            });
                        }
                    }

                    // Method 3: Fallback - look for any contact-collection divs
                    if (creditorContacts.length === 0) {
                        document.querySelectorAll('.contact-collection, .creditor-list').forEach(container => {
                            container.querySelectorAll('.contact-item, .creditor-item, li').forEach(item => {
                                const name = item.querySelector('strong, .name')?.textContent.trim();
                                const address = item.querySelector('.address, p')?.textContent.trim();
                                if (name) {
                                    creditorContacts.push({ name, address, source: 'fallback' });
                                }
                            });
                        });
                    }

                    // Method 4: Classic/Original View - h5.fw-bold "Creditor Contacts" with .d-grid structure
                    if (creditorContacts.length === 0) {
                        let contactsSection = null;
                        document.querySelectorAll('h5.fw-bold, h5').forEach(h => {
                            const text = h.textContent.trim();
                            if (text.includes('Creditor Contacts') || text.includes('Creditor Contact')) {
                                contactsSection = h.closest('section') || h.parentElement?.parentElement;
                            }
                        });

                        if (contactsSection) {
                            // Click the Show button if it exists and content is hidden
                            const showBtn = contactsSection.querySelector('.creditor-toggle span, small span');
                            if (showBtn && showBtn.textContent.includes('Show')) {
                                showBtn.click();
                            }

                            // Look for creditor contact items - could be in .creditor-contacts or .d-grid
                            const creditorContainer = contactsSection.querySelector('.creditor-contacts') || contactsSection;
                            const contactItems = creditorContainer.querySelectorAll('.d-grid, .contact-item, .creditor-row, [class*="contact"]');

                            contactItems.forEach(item => {
                                // Try to get name and address from grid cells or spans
                                const cells = item.querySelectorAll('.grid-cell, p, span');
                                if (cells.length >= 2) {
                                    const name = cells[0]?.textContent.trim();
                                    const address = cells[1]?.textContent.trim();
                                    const phone = cells.length > 2 ? cells[2]?.textContent.trim() : null;

                                    if (name && name.length > 2 && !name.includes('Creditor') && !name.includes('Name')) {
                                        creditorContacts.push({
                                            name,
                                            address: address || null,
                                            phone: phone || null,
                                            source: 'original-view'
                                        });
                                    }
                                }
                            });
                        }
                    }

                    // Also extract Personal Info for Original View - .d-grid.grid-cols-4 with labels and bureau columns
                    // ORGANIZED BY BUREAU: col-start-2=TransUnion, col-start-3=Experian, col-start-4=Equifax
                    if (data.names.length === 0) {
                        // Initialize per-bureau structure
                        data.transunion = { names: [], dob: null, current_address: null, previous_addresses: [], employers: [] };
                        data.experian = { names: [], dob: null, current_address: null, previous_addresses: [], employers: [] };
                        data.equifax = { names: [], dob: null, current_address: null, previous_addresses: [], employers: [] };

                        // Find Personal Information section
                        let personalSection = null;
                        document.querySelectorAll('h5.fw-bold, h5.m-0.fw-bold').forEach(h => {
                            if (h.textContent.includes('Personal Information')) {
                                personalSection = h.closest('section') || h.parentElement?.parentElement;
                            }
                        });

                        if (personalSection) {
                            const grid = personalSection.querySelector('.d-grid.grid-cols-4');
                            if (grid) {
                                // Get all cells and organize by bureau column
                                const allCells = grid.querySelectorAll('.grid-cell');
                                allCells.forEach(cell => {
                                    const className = cell.className || '';

                                    // Determine which bureau based on col-start class
                                    let bureau = null;
                                    if (className.includes('col-start-2')) bureau = 'transunion';
                                    else if (className.includes('col-start-3')) bureau = 'experian';
                                    else if (className.includes('col-start-4')) bureau = 'equifax';

                                    if (!bureau) return; // Skip label column

                                    const span = cell.querySelector('span');
                                    if (!span) return;

                                    const html = span.innerHTML;
                                    const text = span.textContent.trim();

                                    // Extract names - row-start-3 (Name + Also Known As)
                                    if (className.includes('row-start-3')) {
                                        const names = html.split(/<br\\s*\\/?>/i)
                                            .map(n => n.trim())
                                            .filter(n => n.length > 2 && !n.includes('<'));
                                        names.forEach(name => {
                                            if (!data[bureau].names.includes(name)) {
                                                data[bureau].names.push(name);
                                            }
                                            // Also add to flat list for backward compatibility
                                            if (!data.names.includes(name)) {
                                                data.names.push(name);
                                            }
                                        });
                                    }

                                    // Extract DOB - row-start-4
                                    if (className.includes('row-start-4')) {
                                        const fullDateMatch = text.match(/(\\d{1,2}\\/\\d{1,2}\\/\\d{4})/);
                                        if (fullDateMatch) {
                                            data[bureau].dob = fullDateMatch[1];
                                            if (!data.dob) data.dob = fullDateMatch[1];
                                        } else {
                                            const yearMatch = text.match(/(19[4-9]\\d|20[0-2]\\d)/);
                                            if (yearMatch) {
                                                data[bureau].dob = yearMatch[1];
                                                if (!data.dob) data.dob = yearMatch[1];
                                            }
                                        }
                                    }

                                    // Extract Current Address - row-start-5
                                    if (className.includes('row-start-5')) {
                                        const addrText = html
                                            .replace(/<br\\s*\\/?>/gi, ', ')
                                            .replace(/<[^>]*>/g, '')
                                            .trim();
                                        if (addrText && addrText.length > 5) {
                                            data[bureau].current_address = addrText;
                                            if (!data.addresses.includes(addrText)) {
                                                data.addresses.push(addrText);
                                            }
                                        }
                                    }

                                    // Extract Previous Addresses - row-start-6
                                    if (className.includes('row-start-6')) {
                                        const addrBlocks = html.split(/<br\\s*\\/?><br\\s*\\/?>/gi);
                                        addrBlocks.forEach(block => {
                                            const addr = block
                                                .replace(/<br\\s*\\/?>/gi, ', ')
                                                .replace(/<[^>]*>/g, '')
                                                .trim();
                                            if (addr && addr.length > 5) {
                                                if (!data[bureau].previous_addresses.includes(addr)) {
                                                    data[bureau].previous_addresses.push(addr);
                                                }
                                                if (!data.addresses.includes(addr)) {
                                                    data.addresses.push(addr);
                                                }
                                            }
                                        });
                                    }

                                    // Extract Employers - row-start-7
                                    if (className.includes('row-start-7')) {
                                        const empBlocks = html.split(/<br\\s*\\/?><br\\s*\\/?>/gi);
                                        empBlocks.forEach(block => {
                                            const parts = block.split(/<br\\s*\\/?>/i);
                                            const empName = parts[0].replace(/<[^>]*>/g, '').trim();
                                            if (empName && empName.length > 1 &&
                                                !empName.toLowerCase().includes('date updated')) {
                                                let dateUpdated = null;
                                                for (const part of parts) {
                                                    const dateMatch = part.match(/Date Updated:\\s*([\\d\\/]+)/i);
                                                    if (dateMatch) {
                                                        dateUpdated = dateMatch[1];
                                                        break;
                                                    }
                                                }
                                                const empObj = { name: empName, date_updated: dateUpdated };
                                                // Add to bureau-specific list
                                                if (!data[bureau].employers.find(e => e.name === empName)) {
                                                    data[bureau].employers.push(empObj);
                                                }
                                                // Add to flat list for backward compatibility
                                                if (!data.employers.find(e => e.name === empName)) {
                                                    data.employers.push(empObj);
                                                }
                                            }
                                        });
                                    }
                                });
                            }
                        }

                        // MYSCOREIQ FALLBACK: If still no names, try MyScoreIQ format
                        // MyScoreIQ uses tables with class rpt_content_table and columns headerTUC, headerEXP, headerEQF
                        if (data.names.length === 0) {
                            // Find all headers and look for Personal Information
                            let personalTable = null;
                            document.querySelectorAll('.rpt_fullReport_header').forEach(header => {
                                if (header.textContent.includes('Personal Information')) {
                                    // Find the next table.rpt_content_table after this header (skip help_text tables)
                                    // Look in parent wrapper first
                                    const wrapper = header.closest('.rpt_content_wrapper');
                                    if (wrapper) {
                                        // Find table.rpt_content_table.rpt_table4column within the wrapper
                                        personalTable = wrapper.querySelector('table.rpt_content_table.rpt_table4column');
                                    }
                                    // Fallback: Walk through siblings
                                    if (!personalTable) {
                                        let el = header.nextElementSibling;
                                        while (el && !personalTable) {
                                            // Skip help_text tables
                                            if (el.tagName === 'TABLE' && el.classList?.contains('rpt_content_table') && !el.classList?.contains('help_text')) {
                                                personalTable = el;
                                            } else if (el.querySelector) {
                                                personalTable = el.querySelector('table.rpt_content_table.rpt_table4column');
                                            }
                                            el = el.nextElementSibling;
                                        }
                                    }
                                    // Also check parent's siblings
                                    if (!personalTable) {
                                        let parent = header.parentElement;
                                        let sib = parent?.nextElementSibling;
                                        while (sib && !personalTable) {
                                            if (sib.tagName === 'TABLE' && sib.classList?.contains('rpt_content_table') && !sib.classList?.contains('help_text')) {
                                                personalTable = sib;
                                            } else if (sib.querySelector) {
                                                personalTable = sib.querySelector('table.rpt_content_table.rpt_table4column');
                                            }
                                            sib = sib.nextElementSibling;
                                        }
                                    }
                                }
                            });

                            // Also try direct table selection with 4-column layout
                            if (!personalTable) {
                                // Get the first 4-column table that follows a Personal Information header
                                const piWrapper = document.querySelector('.rpt_content_wrapper:has(.rpt_fullReport_header)');
                                if (piWrapper && piWrapper.textContent.includes('Personal Information')) {
                                    personalTable = piWrapper.querySelector('table.rpt_content_table.rpt_table4column');
                                }
                            }
                            if (!personalTable) {
                                personalTable = document.querySelector('table.rpt_content_table.rpt_table4column');
                            }

                            if (personalTable) {
                                // Initialize per-bureau data if not already
                                if (!data.transunion) data.transunion = { names: [], also_known_as: [], former_names: [], dob: null, current_address: null, current_address_date: null, previous_addresses: [], employers: [] };
                                if (!data.experian) data.experian = { names: [], also_known_as: [], former_names: [], dob: null, current_address: null, current_address_date: null, previous_addresses: [], employers: [] };
                                if (!data.equifax) data.equifax = { names: [], also_known_as: [], former_names: [], dob: null, current_address: null, current_address_date: null, previous_addresses: [], employers: [] };

                                // Helper function to clean text - removes trailing " -" from MyScoreIQ Angular templates
                                const cleanText = (text) => {
                                    if (!text) return '';
                                    return text.replace(/\\s+-\\s*$/, '').replace(/\\s+/g, ' ').trim();
                                };

                                // Helper function to extract name from ng-include template (ignores hidden "-" elements)
                                const extractName = (cell) => {
                                    const nameInclude = cell.querySelector('ng-include[src*="personNameTemplate"]');
                                    if (nameInclude) {
                                        // Get text from ng-if elements inside the template
                                        const parts = [];
                                        nameInclude.querySelectorAll('ng-if').forEach(el => {
                                            const txt = el.textContent.replace(/&nbsp;/g, ' ').trim();
                                            if (txt && txt !== '-') parts.push(txt);
                                        });
                                        return parts.join(' ').replace(/\\s+/g, ' ').trim();
                                    }
                                    return cleanText(cell.textContent);
                                };

                                // Helper function to extract address with date separated
                                const extractAddress = (cell) => {
                                    const result = { address: null, date: null };
                                    // First ng-repeat contains the address div
                                    const addrContainer = cell.querySelector('ng-repeat');
                                    if (addrContainer) {
                                        // ng-include contains the address parts
                                        const addrInclude = addrContainer.querySelector('ng-include');
                                        if (addrInclude) {
                                            const parts = [];
                                            addrInclude.querySelectorAll('ng-if').forEach(el => {
                                                const txt = el.textContent.replace(/&nbsp;/g, ' ').trim();
                                                if (txt && txt !== '-') parts.push(txt);
                                            });
                                            result.address = parts.join(' ').replace(/\\s+/g, ' ').trim();
                                        }
                                        // Date is in a separate div with ng-if containing the date
                                        const dateDiv = addrContainer.querySelector('div[ng-if*="date_last_updated"], div[ng-if*="date_first_reported"]');
                                        if (dateDiv) {
                                            result.date = dateDiv.textContent.trim();
                                        }
                                    }
                                    // Fallback: just get the address from text content, clean it
                                    if (!result.address) {
                                        const text = cleanText(cell.textContent);
                                        // Try to separate date from address (MM/YYYY pattern at end)
                                        const dateMatch = text.match(/\\s+(\\d{2}\\/\\d{4})\\s*$/);
                                        if (dateMatch) {
                                            result.address = text.replace(dateMatch[0], '').trim();
                                            result.date = dateMatch[1];
                                        } else {
                                            result.address = text;
                                        }
                                    }
                                    return result;
                                };

                                // Helper function to extract multiple addresses from a cell (for Previous Addresses)
                                const extractMultipleAddresses = (cell) => {
                                    const addresses = [];
                                    // Each address is in a separate ng-repeat div
                                    const addrContainers = cell.querySelectorAll('ng-repeat');
                                    addrContainers.forEach(container => {
                                        const addrInclude = container.querySelector('ng-include');
                                        if (addrInclude) {
                                            const parts = [];
                                            addrInclude.querySelectorAll('ng-if').forEach(el => {
                                                const txt = el.textContent.replace(/&nbsp;/g, ' ').trim();
                                                if (txt && txt !== '-') parts.push(txt);
                                            });
                                            const addrText = parts.join(' ').replace(/\\s+/g, ' ').trim();
                                            // Get date if present
                                            const dateDiv = container.querySelector('div[ng-if*="date_last_updated"], div[ng-if*="date_first_reported"]');
                                            const dateText = dateDiv ? dateDiv.textContent.trim() : null;
                                            if (addrText) {
                                                addresses.push({ address: addrText, date: dateText });
                                            }
                                        }
                                    });
                                    return addresses;
                                };

                                const rows = personalTable.querySelectorAll('tr');
                                rows.forEach(row => {
                                    const labelCell = row.querySelector('td.label');
                                    if (!labelCell) return;
                                    const label = labelCell.textContent.trim();

                                    const infoCells = row.querySelectorAll('td.info');
                                    if (infoCells.length >= 3) {
                                        // Column order: TransUnion, Experian, Equifax
                                        const bureaus = ['transunion', 'experian', 'equifax'];
                                        infoCells.forEach((cell, idx) => {
                                            if (idx >= 3) return;
                                            const bureau = bureaus[idx];
                                            const rawText = cell.textContent.replace(/\\s+/g, ' ').trim();
                                            // Skip if cell only contains "-" (placeholder)
                                            if (!rawText || rawText === '-') return;

                                            // Primary Name (not AKA or Former)
                                            if (label === 'Name:' || label.match(/^Name$/i)) {
                                                const nameText = extractName(cell);
                                                if (nameText && nameText.length > 2 && nameText !== '-') {
                                                    if (!data[bureau].names.includes(nameText)) {
                                                        data[bureau].names.push(nameText);
                                                    }
                                                    if (!data.names.includes(nameText)) {
                                                        data.names.push(nameText);
                                                    }
                                                }
                                            }
                                            // Also Known As names - get all names beyond index 0
                                            else if (label.includes('Also Known As')) {
                                                // AKA names are in ng-repeat with ng-if="$index > 0"
                                                const akaRepeats = cell.querySelectorAll('ng-repeat[ng-if*="$index > 0"]');
                                                akaRepeats.forEach(rep => {
                                                    const nameInclude = rep.querySelector('ng-include');
                                                    if (nameInclude) {
                                                        const parts = [];
                                                        nameInclude.querySelectorAll('ng-if').forEach(el => {
                                                            const txt = el.textContent.replace(/&nbsp;/g, ' ').trim();
                                                            if (txt && txt !== '-') parts.push(txt);
                                                        });
                                                        const akaName = parts.join(' ').replace(/\\s+/g, ' ').trim();
                                                        if (akaName && akaName !== '-' && !data[bureau].also_known_as.includes(akaName)) {
                                                            data[bureau].also_known_as.push(akaName);
                                                        }
                                                    }
                                                });
                                            }
                                            // Former names
                                            else if (label.includes('Former')) {
                                                const formerRepeats = cell.querySelectorAll('ng-repeat');
                                                formerRepeats.forEach(rep => {
                                                    const nameInclude = rep.querySelector('ng-include');
                                                    if (nameInclude) {
                                                        const parts = [];
                                                        nameInclude.querySelectorAll('ng-if').forEach(el => {
                                                            const txt = el.textContent.replace(/&nbsp;/g, ' ').trim();
                                                            if (txt && txt !== '-') parts.push(txt);
                                                        });
                                                        const formerName = parts.join(' ').replace(/\\s+/g, ' ').trim();
                                                        if (formerName && formerName !== '-' && !data[bureau].former_names.includes(formerName)) {
                                                            data[bureau].former_names.push(formerName);
                                                        }
                                                    }
                                                });
                                            }
                                            else if (label.includes('Date of Birth') || label.includes('Birth Year')) {
                                                // DOB is in ng-repeat > div.ng-binding
                                                const dobDiv = cell.querySelector('ng-repeat div.ng-binding');
                                                let dobText = dobDiv ? dobDiv.textContent.trim() : cleanText(rawText);
                                                const dateMatch = dobText.match(/(\\d{1,2}\\/\\d{1,2}\\/\\d{4})/);
                                                const yearMatch = dobText.match(/(19[4-9]\\d|20[0-2]\\d)/);
                                                if (dateMatch) {
                                                    data[bureau].dob = dateMatch[1];
                                                    if (!data.dob) data.dob = dateMatch[1];
                                                } else if (yearMatch) {
                                                    data[bureau].dob = yearMatch[1];
                                                    if (!data.dob) data.dob = yearMatch[1];
                                                }
                                            }
                                            // Current Address(es) - first address only
                                            else if (label.includes('Current Address')) {
                                                if (!data[bureau].current_address) {
                                                    const addrData = extractAddress(cell);
                                                    if (addrData.address && addrData.address.length > 5) {
                                                        data[bureau].current_address = addrData.address;
                                                        data[bureau].current_address_date = addrData.date;
                                                        if (!data.addresses.includes(addrData.address)) {
                                                            data.addresses.push(addrData.address);
                                                        }
                                                    }
                                                }
                                            }
                                            // Previous Address(es) - can have multiple
                                            else if (label.includes('Previous Address')) {
                                                const prevAddrs = extractMultipleAddresses(cell);
                                                prevAddrs.forEach(addrData => {
                                                    if (addrData.address && addrData.address.length > 5) {
                                                        // Store as object with address and date
                                                        const addrObj = { address: addrData.address, date: addrData.date };
                                                        const exists = data[bureau].previous_addresses.find(a => a.address === addrData.address);
                                                        if (!exists) {
                                                            data[bureau].previous_addresses.push(addrObj);
                                                        }
                                                        if (!data.addresses.includes(addrData.address)) {
                                                            data.addresses.push(addrData.address);
                                                        }
                                                    }
                                                });
                                            }
                                            else if (label.includes('Employer')) {
                                                // Employers are in ng-repeat elements, each with ng-if for the name
                                                const empRepeats = cell.querySelectorAll('ng-repeat');
                                                empRepeats.forEach(rep => {
                                                    const nameEl = rep.querySelector('ng-if[ng-if*="emp[\\'name\\']"]');
                                                    if (nameEl) {
                                                        const empName = nameEl.textContent.replace(/&nbsp;/g, ' ').trim();
                                                        if (empName && empName.length > 2 && empName !== '-') {
                                                            const empObj = { name: empName, date_updated: null };
                                                            if (!data[bureau].employers.find(e => e.name === empName)) {
                                                                data[bureau].employers.push(empObj);
                                                            }
                                                            if (!data.employers.find(e => e.name === empName)) {
                                                                data.employers.push(empObj);
                                                            }
                                                        }
                                                    }
                                                });
                                                // Fallback: if no ng-repeat found, try cleanText approach
                                                if (data[bureau].employers.length === 0) {
                                                    const empText = cleanText(rawText);
                                                    if (empText && empText.length > 2 && empText !== '-') {
                                                        const empObj = { name: empText, date_updated: null };
                                                        if (!data[bureau].employers.find(e => e.name === empText)) {
                                                            data[bureau].employers.push(empObj);
                                                        }
                                                        if (!data.employers.find(e => e.name === empText)) {
                                                            data.employers.push(empObj);
                                                        }
                                                    }
                                                }
                                            }
                                        });
                                    }
                                });
                            }
                        }
                    }

                    return { personal: data, summary: summary, inquiries: inquiries, creditor_contacts: creditorContacts };
                }"""
                )
                if personal_data:
                    personal_info = personal_data.get("personal", {})
                    summary_info = personal_data.get("summary", {})
                    inquiries = personal_data.get("inquiries", [])
                    creditor_contacts = personal_data.get("creditor_contacts", [])
                    logger.info(
                        f"Extracted personal info: {len(personal_info.get('names', []))} names, {len(personal_info.get('addresses', []))} addresses"
                    )
                    logger.info(
                        f"Extracted {len(inquiries)} inquiries, {len(creditor_contacts)} creditor contacts"
                    )
            except Exception as e:
                logger.warning(f"Personal info extraction failed: {e}")

            # Payment history conversion is now handled in _extract_accounts_data()
            # This is a no-op safety net if payment_history is already in unified format

            json_filename = f"{client_id}_{safe_name}_{timestamp}.json"
            json_filepath = REPORTS_DIR / json_filename
            extracted_data = {
                "client_id": client_id,
                "client_name": client_name,
                "extracted_at": datetime.utcnow().isoformat(),
                "scores": scores or {},
                "personal_info": personal_info,
                "summary": summary_info,
                "accounts": accounts or [],
                "inquiries": inquiries,
                "creditor_contacts": creditor_contacts,
            }
            with open(json_filepath, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=2)

            logger.info(f"Saved report to {filepath}")
            logger.info(f"Saved extracted data to {json_filepath}")

            return {
                "path": str(filepath),
                "json_path": str(json_filepath),
                "html": html_content,
                "scores": scores,
                "accounts": accounts,
            }

        except Exception as e:
            logger.error(f"Failed to download report: {e}")
            return None

    async def _extract_scores(self) -> Optional[Dict[str, Any]]:
        """Extract credit scores from the current page after JS rendering."""
        scores = {}

        try:
            html_content = await self.page.content()

            # Flow-aware extraction for MyFreeScoreNow
            if self.current_flow == "myfreescorenow":
                logger.info("Using MyFreeScoreNow extraction method")
                try:
                    js_scores = await self.page.evaluate(
                        """() => {
                        const scores = {};

                        // Method 1: MyFreeScoreNow 3B page - exact structure
                        // <div class="bureau-score border-transunion">
                        //   <h6 class="text-transunion">TransUnion</h6>
                        //   <h1 class="fw-bold">706</h1>
                        // </div>
                        const bureauScoreDivs = document.querySelectorAll('.bureau-score');
                        for (const div of bureauScoreDivs) {
                            const className = div.className || '';
                            const h1 = div.querySelector('h1');
                            if (!h1) continue;

                            const scoreText = h1.textContent.trim();
                            const scoreMatch = scoreText.match(/^([3-8]\\d{2})$/);
                            if (!scoreMatch) continue;

                            const score = parseInt(scoreMatch[1]);
                            if (className.includes('transunion') || className.includes('border-transunion')) {
                                scores.transunion = score;
                            } else if (className.includes('experian') || className.includes('border-experian')) {
                                scores.experian = score;
                            } else if (className.includes('equifax') || className.includes('border-equifax')) {
                                scores.equifax = score;
                            }
                        }

                        // Method 2: Fallback - look for h6 with bureau name followed by h1 with score
                        if (Object.keys(scores).length < 3) {
                            const allH6 = document.querySelectorAll('h6');
                            for (const h6 of allH6) {
                                const text = h6.textContent.toLowerCase();
                                const parent = h6.parentElement;
                                if (!parent) continue;

                                const h1 = parent.querySelector('h1');
                                if (!h1) continue;

                                const scoreMatch = h1.textContent.trim().match(/^([3-8]\\d{2})$/);
                                if (!scoreMatch) continue;

                                const score = parseInt(scoreMatch[1]);
                                if (text.includes('transunion') && !scores.transunion) {
                                    scores.transunion = score;
                                } else if (text.includes('experian') && !scores.experian) {
                                    scores.experian = score;
                                } else if (text.includes('equifax') && !scores.equifax) {
                                    scores.equifax = score;
                                }
                            }
                        }

                        // Method 3: Classic/Original View - dt.bg-bureau with dd containing h5 score
                        if (Object.keys(scores).length < 3) {
                            const allDt = document.querySelectorAll('dt.bg-transunion, dt.bg-experian, dt.bg-equifax');
                            for (const dt of allDt) {
                                const className = dt.className || '';
                                const dd = dt.nextElementSibling;
                                if (!dd) continue;

                                const h5 = dd.querySelector('h5');
                                if (!h5) continue;

                                const scoreMatch = h5.textContent.trim().match(/^([3-8]\\d{2})$/);
                                if (!scoreMatch) continue;

                                const score = parseInt(scoreMatch[1]);
                                if (className.includes('transunion') && !scores.transunion) {
                                    scores.transunion = score;
                                } else if (className.includes('experian') && !scores.experian) {
                                    scores.experian = score;
                                } else if (className.includes('equifax') && !scores.equifax) {
                                    scores.equifax = score;
                                }
                            }
                        }

                        return scores;
                    }"""
                    )
                    if js_scores and len(js_scores) > 0:
                        scores.update(js_scores)
                        logger.info(f"MyFreeScoreNow extraction successful: {scores}")
                except Exception as e:
                    logger.warning(f"MyFreeScoreNow JS extraction failed: {e}")

            # Default extraction for MyScoreIQ and other Angular-based services
            if not scores:
                scores = self._extract_scores_from_html(html_content)

            # Always run MyScoreIQ-specific JavaScript to extract lender rank and scale
            # This also extracts scores if they weren't found above
            try:
                js_scores = await self.page.evaluate(
                    """() => {
                    const result = {
                        transunion: null,
                        experian: null,
                        equifax: null,
                        lender_rank: { transunion: null, experian: null, equifax: null },
                        score_scale: { transunion: null, experian: null, equifax: null }
                    };

                    // Find the score table - look for rpt_content_table with 4 columns
                    const tables = document.querySelectorAll('table.rpt_content_table.rpt_table4column');

                    for (const table of tables) {
                        const rows = table.querySelectorAll('tr');

                        for (const row of rows) {
                            const labelCell = row.querySelector('td.label');
                            if (!labelCell) continue;

                            const labelText = labelCell.textContent.toLowerCase();
                            const infoCells = row.querySelectorAll('td.info, td.info.ng-binding');

                            if (infoCells.length >= 3) {
                                const values = Array.from(infoCells).map(td => td.textContent.trim());

                                // FICO Score row (MyScoreIQ) or Credit Score row (IdentityIQ)
                                if ((labelText.includes('fico') && labelText.includes('score')) ||
                                    (labelText.includes('credit score') && !labelText.includes('factor'))) {
                                    const tuMatch = values[0]?.match(/^([3-8]\\d{2})$/);
                                    const exMatch = values[1]?.match(/^([3-8]\\d{2})$/);
                                    const eqMatch = values[2]?.match(/^([3-8]\\d{2})$/);

                                    if (tuMatch) result.transunion = parseInt(tuMatch[1]);
                                    if (exMatch) result.experian = parseInt(exMatch[1]);
                                    if (eqMatch) result.equifax = parseInt(eqMatch[1]);
                                }

                                // Lender Rank row
                                if (labelText.includes('lender') && labelText.includes('rank')) {
                                    result.lender_rank.transunion = values[0] || null;
                                    result.lender_rank.experian = values[1] || null;
                                    result.lender_rank.equifax = values[2] || null;
                                }

                                // Score Scale row
                                if (labelText.includes('scale')) {
                                    result.score_scale.transunion = values[0] || null;
                                    result.score_scale.experian = values[1] || null;
                                    result.score_scale.equifax = values[2] || null;
                                }
                            }
                        }
                    }

                    return result;
                }"""
                )
                if js_scores:
                    # Merge: keep existing scores, add lender_rank and score_scale
                    if not scores:
                        scores = {}
                    if js_scores.get("transunion") and not scores.get("transunion"):
                        scores["transunion"] = js_scores["transunion"]
                    if js_scores.get("experian") and not scores.get("experian"):
                        scores["experian"] = js_scores["experian"]
                    if js_scores.get("equifax") and not scores.get("equifax"):
                        scores["equifax"] = js_scores["equifax"]
                    # Always add lender_rank and score_scale
                    if js_scores.get("lender_rank"):
                        scores["lender_rank"] = js_scores["lender_rank"]
                    if js_scores.get("score_scale"):
                        scores["score_scale"] = js_scores["score_scale"]
            except Exception as e:
                logger.warning(f"MyScoreIQ lender rank extraction failed: {e}")

            logger.info(f"Final extracted scores: {scores}")
            return scores if scores else None

        except Exception as e:
            logger.error(f"Failed to extract scores: {e}")
            return None

    def _extract_scores_from_html(self, html_content: str) -> Dict[str, Any]:
        """Extract scores directly from HTML content using regex patterns."""
        import re

        scores = {}

        pattern = r'<th[^>]*class="header(TUC|EXP|EQF)"[^>]*>.*?</th>'
        header_pattern = re.compile(pattern, re.DOTALL | re.IGNORECASE)

        table_pattern = re.compile(
            r'<th[^>]*class="headerTUC"[^>]*>.*?TransUnion.*?</th>\s*'
            r'<th[^>]*class="headerEXP"[^>]*>.*?Experian.*?</th>\s*'
            r'<th[^>]*class="headerEQF"[^>]*>.*?Equifax.*?</th>\s*'
            r".*?<tr[^>]*>.*?"
            r'<td[^>]*class="info[^"]*"[^>]*>\s*(\d{3})\s*</td>\s*'
            r'<td[^>]*class="info[^"]*"[^>]*>\s*(\d{3})\s*</td>\s*'
            r'<td[^>]*class="info[^"]*"[^>]*>\s*(\d{3})\s*</td>',
            re.DOTALL | re.IGNORECASE,
        )

        match = table_pattern.search(html_content)
        if match:
            tu_score = int(match.group(1))
            exp_score = int(match.group(2))
            eq_score = int(match.group(3))

            if 300 <= tu_score <= 850:
                scores["transunion"] = tu_score
            if 300 <= exp_score <= 850:
                scores["experian"] = exp_score
            if 300 <= eq_score <= 850:
                scores["equifax"] = eq_score

            logger.info(f"Extracted scores from HTML table: {scores}")
            return scores

        info_td_pattern = re.compile(
            r'<td\s+class="info\s+ng-binding"[^>]*>\s*(\d{3})\s*</td>', re.IGNORECASE
        )

        matches = info_td_pattern.findall(html_content)
        score_values = [int(m) for m in matches if 300 <= int(m) <= 850]

        if len(score_values) >= 3:
            scores["transunion"] = score_values[0]
            scores["experian"] = score_values[1]
            scores["equifax"] = score_values[2]
            logger.info(f"Extracted scores from td.info pattern: {scores}")

        return scores

    def _extract_accounts_from_xhr(
        self, responses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract accounts from captured XHR responses."""
        accounts = []

        for resp in responses:
            try:
                data = resp.get("data", {})

                if isinstance(data, dict):
                    for key in [
                        "tradelines",
                        "accounts",
                        "tradeLines",
                        "Accounts",
                        "TradeLines",
                        "creditAccounts",
                        "CreditAccounts",
                        "tpartitions",
                        "TPartitions",
                        "trades",  # MyFreeScoreNow format
                        "Trades",
                    ]:
                        if key in data:
                            items = data[key]
                            if isinstance(items, list):
                                for item in items:
                                    account = self._parse_account_item(item)
                                    if account:
                                        accounts.append(account)

                    if "reportData" in data or "ReportData" in data:
                        report_data = data.get("reportData") or data.get(
                            "ReportData", {}
                        )
                        if isinstance(report_data, dict):
                            for key in ["tradelines", "accounts", "tradeLines"]:
                                if key in report_data:
                                    items = report_data[key]
                                    if isinstance(items, list):
                                        for item in items:
                                            account = self._parse_account_item(item)
                                            if account:
                                                accounts.append(account)

                elif isinstance(data, list):
                    for item in data:
                        account = self._parse_account_item(item)
                        if account:
                            accounts.append(account)

            except Exception as e:
                logger.warning(f"Error parsing XHR response: {e}")

        logger.info(f"Extracted {len(accounts)} accounts from XHR data")
        return accounts

    def _parse_account_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single account/tradeline item from XHR data."""
        if not isinstance(item, dict):
            return None

        name_keys = [
            "name",
            "creditorName",
            "creditor",
            "Name",
            "CreditorName",
            "accountName",
            "memberCodeShortName",  # MyFreeScoreNow format
        ]
        name = None
        for key in name_keys:
            if key in item and item[key]:
                name = str(item[key]).strip()
                break

        # MyFreeScoreNow nested structure for full creditor name
        if not name:
            try:
                member_account = item.get("memberCodeAccount", {})
                creditor_contact = member_account.get("creditorContact", {})
                name = creditor_contact.get("memberCodeLongName", "").strip()
            except:
                pass

        if not name:
            return None

        account: Dict[str, Any] = {
            "creditor": name,
            "account_number": None,
            "account_type": None,
            "account_type_detail": None,
            "bureau_code": None,
            "account_status": None,
            "status": None,
            "balance": None,
            "credit_limit": None,
            "high_credit": None,
            "monthly_payment": None,
            "payment_status": None,
            "date_opened": None,
            "last_reported": None,
            "last_active": None,
            "last_payment": None,
            "past_due": None,
            "term_length": None,
            "comments": None,
            "bureaus": {},
        }

        number_keys = [
            "number",
            "accountNumber",
            "AccountNumber",
            "acctNumber",
            "maskedAccountNumber",
        ]
        for key in number_keys:
            if key in item and item[key]:
                account["account_number"] = str(item[key]).strip()
                break

        type_keys = ["type", "accountType", "AccountType", "classification"]
        for key in type_keys:
            if key in item and item[key]:
                account["account_type"] = str(item[key]).strip()
                break

        status_keys = [
            "status",
            "paymentStatus",
            "Status",
            "PaymentStatus",
            "condition",
        ]
        for key in status_keys:
            if key in item and item[key]:
                account["status"] = str(item[key]).strip()
                break

        balance_keys = [
            "balance",
            "currentBalance",
            "Balance",
            "CurrentBalance",
            "currentBalanceAmount",
        ]
        for key in balance_keys:
            if key in item and item[key]:
                try:
                    account["balance"] = float(
                        str(item[key]).replace("$", "").replace(",", "")
                    )
                except:
                    account["balance"] = str(item[key])
                break

        for bureau in ["TUC", "EXP", "EQF", "transunion", "experian", "equifax"]:
            if bureau in item and isinstance(item[bureau], dict):
                bureau_key = (
                    bureau.lower()
                    .replace("tuc", "transunion")
                    .replace("exp", "experian")
                    .replace("eqf", "equifax")
                )
                account["bureaus"][bureau_key] = item[bureau]

        return account

    async def _extract_accounts_data(self) -> List[Dict[str, Any]]:
        """Extract account/tradeline data from the credit report page."""
        accounts = []

        try:
            js_accounts = await self.page.evaluate(
                """() => {
                const accounts = [];

                // MyScoreIQ uses Angular with sub_header divs for account names
                const headers = document.querySelectorAll('.sub_header.ng-binding, div.sub_header');

                headers.forEach((header) => {
                    const creditorName = header.textContent.trim()
                        .replace(/\\s+/g, ' ')
                        .replace(/\\(Original Creditor:.*\\)/gi, '')
                        .trim();

                    // Skip empty or template-only entries
                    if (!creditorName || creditorName.includes('{{') || creditorName.length < 2) {
                        return;
                    }
                    // Skip section headers that aren't actual accounts
                    const skipHeaders = ['SCORE FACTORS', 'FACTORS', 'SUMMARY', 'INQUIRIES',
                                        'COLLECTIONS', 'PUBLIC RECORDS', 'PERSONAL INFORMATION',
                                        'ACCOUNT HISTORY', 'CREDITOR CONTACTS'];
                    if (skipHeaders.includes(creditorName.toUpperCase())) {
                        return;
                    }

                    // Find the associated data table
                    const table = header.closest('ng-include')?.querySelector('table.rpt_content_table')
                               || header.nextElementSibling;

                    const account = {
                        creditor: creditorName,
                        account_number: null,
                        account_type: null,
                        account_type_detail: null,
                        bureau_code: null,
                        account_status: null,
                        balance: null,
                        credit_limit: null,
                        high_credit: null,
                        monthly_payment: null,
                        payment_status: null,
                        date_opened: null,
                        last_reported: null,
                        last_active: null,
                        last_payment: null,
                        past_due: null,
                        date_closed: null,
                        account_rating: null,
                        creditor_type: null,
                        term_length: null,
                        comments: null,
                        bureaus: {
                            transunion: { present: false },
                            experian: { present: false },
                            equifax: { present: false }
                        }
                    };

                    if (table && table.tagName === 'TABLE') {
                        const rows = table.querySelectorAll('tr');
                        rows.forEach(row => {
                            const label = row.querySelector('td.label');
                            const infoCells = row.querySelectorAll('td.info');

                            if (label && infoCells.length >= 1) {
                                const labelText = label.textContent.trim().toLowerCase();

                                // Get values from bureau columns (TU, EXP, EQF)
                                const values = Array.from(infoCells).map(cell =>
                                    cell.textContent.trim().replace(/\\s+/g, ' ')
                                );

                                if (labelText.includes('account number') || labelText.includes('account #') || labelText === 'number') {
                                    account.account_number = values.find(v => v && v !== '-') || null;
                                    if (values[0] && values[0] !== '-') account.bureaus.transunion.number = values[0];
                                    if (values[1] && values[1] !== '-') account.bureaus.experian.number = values[1];
                                    if (values[2] && values[2] !== '-') account.bureaus.equifax.number = values[2];
                                }

                                // Account Type (not detail)
                                if (labelText === 'account type:' || labelText === 'account type' || labelText.includes('classification')) {
                                    account.account_type = values.find(v => v && v !== '-') || null;
                                    if (values[0] && values[0] !== '-') account.bureaus.transunion.type = values[0];
                                    if (values[1] && values[1] !== '-') account.bureaus.experian.type = values[1];
                                    if (values[2] && values[2] !== '-') account.bureaus.equifax.type = values[2];
                                }

                                // Account Type - Detail
                                if (labelText.includes('account type - detail') || labelText.includes('type - detail') || labelText.includes('account type detail')) {
                                    account.account_type_detail = values.find(v => v && v !== '-') || null;
                                    if (values[0] && values[0] !== '-') account.bureaus.transunion.type_detail = values[0];
                                    if (values[1] && values[1] !== '-') account.bureaus.experian.type_detail = values[1];
                                    if (values[2] && values[2] !== '-') account.bureaus.equifax.type_detail = values[2];
                                }

                                // Bureau Code (e.g., Individual Account, Joint Account)
                                if (labelText.includes('bureau code')) {
                                    account.bureau_code = values.find(v => v && v !== '-') || null;
                                    if (values[0] && values[0] !== '-') account.bureaus.transunion.bureau_code = values[0];
                                    if (values[1] && values[1] !== '-') account.bureaus.experian.bureau_code = values[1];
                                    if (values[2] && values[2] !== '-') account.bureaus.equifax.bureau_code = values[2];
                                }

                                // Account Status (separate from Payment Status)
                                if (labelText === 'account status:' || labelText === 'account status') {
                                    account.account_status = values.find(v => v && v !== '-') || null;
                                    if (values[0] && values[0] !== '-') account.bureaus.transunion.account_status = values[0];
                                    if (values[1] && values[1] !== '-') account.bureaus.experian.account_status = values[1];
                                    if (values[2] && values[2] !== '-') account.bureaus.equifax.account_status = values[2];
                                }

                                // Comments
                                if (labelText === 'comments:' || labelText === 'comments') {
                                    account.comments = values.find(v => v && v !== '-') || null;
                                    if (values[0] && values[0] !== '-') account.bureaus.transunion.comments = values[0];
                                    if (values[1] && values[1] !== '-') account.bureaus.experian.comments = values[1];
                                    if (values[2] && values[2] !== '-') account.bureaus.equifax.comments = values[2];
                                }

                                if (labelText.includes('balance')) {
                                    const balVal = values.find(v => v && v !== '-' && /\\$|\\d/.test(v));
                                    if (balVal) {
                                        account.balance = balVal;
                                        if (values[0] && values[0] !== '-') account.bureaus.transunion.balance = values[0];
                                        if (values[1] && values[1] !== '-') account.bureaus.experian.balance = values[1];
                                        if (values[2] && values[2] !== '-') account.bureaus.equifax.balance = values[2];
                                    }
                                }

                                if (labelText.includes('credit limit') && !labelText.includes('high')) {
                                    const limVal = values.find(v => v && v !== '-' && /\\$|\\d/.test(v));
                                    if (limVal) {
                                        account.credit_limit = limVal;
                                    }
                                }

                                if (labelText.includes('high credit') || labelText.includes('high balance')) {
                                    const highVal = values.find(v => v && v !== '-' && /\\$|\\d/.test(v));
                                    if (highVal) {
                                        account.high_credit = highVal;
                                    }
                                }

                                if (labelText.includes('payment status')) {
                                    account.payment_status = values.find(v => v && v !== '-') || null;
                                }

                                if (labelText.includes('monthly payment') || labelText === 'payment') {
                                    const payVal = values.find(v => v && v !== '-' && /\\$|\\d/.test(v));
                                    if (payVal) {
                                        account.monthly_payment = payVal;
                                    }
                                }

                                if (labelText.includes('date opened') || labelText.includes('opened')) {
                                    account.date_opened = values.find(v => v && v !== '-' && v.includes('/')) || null;
                                }

                                if (labelText.includes('last reported') || labelText.includes('reported')) {
                                    account.last_reported = values.find(v => v && v !== '-' && v.includes('/')) || null;
                                }

                                if (labelText.includes('last active') || labelText.includes('last activity')) {
                                    account.last_active = values.find(v => v && v !== '-' && v.includes('/')) || null;
                                }

                                if (labelText.includes('last payment') || labelText.includes('date of last payment')) {
                                    account.last_payment = values.find(v => v && v !== '-' && v.includes('/')) || null;
                                }

                                if (labelText.includes('past due')) {
                                    const dueVal = values.find(v => v && v !== '-' && /\\$|\\d/.test(v));
                                    if (dueVal) {
                                        account.past_due = dueVal;
                                    }
                                }

                                if (labelText.includes('date closed') || labelText.includes('closed date')) {
                                    account.date_closed = values.find(v => v && v !== '-' && v.includes('/')) || null;
                                }

                                if (labelText.includes('rating') || labelText.includes('account rating')) {
                                    account.account_rating = values.find(v => v && v !== '-') || null;
                                }

                                if (labelText.includes('creditor type') || labelText.includes('type of creditor')) {
                                    account.creditor_type = values.find(v => v && v !== '-') || null;
                                }

                                if (labelText.includes('term') || labelText.includes('term length') || labelText.includes('terms') || labelText.includes('no. of months') || labelText.includes('number of months') || labelText.includes('months')) {
                                    account.term_length = values.find(v => v && v !== '-') || null;
                                    if (values[0] && values[0] !== '-') account.bureaus.transunion.term_length = values[0];
                                    if (values[1] && values[1] !== '-') account.bureaus.experian.term_length = values[1];
                                    if (values[2] && values[2] !== '-') account.bureaus.equifax.term_length = values[2];
                                }

                                // Check bureau presence
                                if (values[0] && values[0] !== '-') account.bureaus.transunion.present = true;
                                if (values[1] && values[1] !== '-') account.bureaus.experian.present = true;
                                if (values[2] && values[2] !== '-') account.bureaus.equifax.present = true;
                            }
                        });
                    }

                    // Extract Extended Payment History for MyScoreIQ
                    // The payment history is inside the same parent container (ng-include or table wrapper)
                    // We need to find the hstry-header that follows this account's sub_header
                    let historyHeader = null;
                    let sibling = header.nextElementSibling;

                    // Walk through siblings until we find the history header or another sub_header
                    while (sibling) {
                        if (sibling.classList?.contains('sub_header')) {
                            // Found another account, stop looking
                            break;
                        }
                        if (sibling.classList?.contains('hstry-header') ||
                            sibling.querySelector?.('.hstry-header')) {
                            historyHeader = sibling.classList?.contains('hstry-header') ?
                                            sibling : sibling.querySelector('.hstry-header');
                            break;
                        }
                        // Also check inside tables for the history header
                        if (sibling.tagName === 'TABLE') {
                            const innerHeader = sibling.parentElement?.querySelector('.hstry-header');
                            if (innerHeader) {
                                historyHeader = innerHeader;
                                break;
                            }
                        }
                        sibling = sibling.nextElementSibling;
                    }

                    // If not found as sibling, try within the container
                    if (!historyHeader) {
                        const container = header.closest('ng-include') || header.closest('td') || header.parentElement;
                        historyHeader = container?.querySelector('.hstry-header, .hstry-header-2yr');
                    }

                    if (historyHeader) {
                        // Find the payment history table (has class addr_hsrty)
                        let historyTable = historyHeader.nextElementSibling;
                        if (!historyTable || historyTable.tagName !== 'TABLE') {
                            // Try finding it as a sibling or in parent
                            historyTable = historyHeader.parentElement?.querySelector('table.addr_hsrty');
                        }

                        if (historyTable && historyTable.tagName === 'TABLE') {
                            const rows = historyTable.querySelectorAll('tr');
                            const months = [];
                            const years = [];
                            const tuValues = [];
                            const expValues = [];
                            const eqfValues = [];

                            rows.forEach(row => {
                                const headerCell = row.querySelector('td.label.leftHeader, td.leftHeader');
                                const dataCells = row.querySelectorAll('td.info');

                                if (headerCell) {
                                    const headerText = headerCell.textContent.trim().toLowerCase();
                                    const cellValues = Array.from(dataCells).map(c => c.textContent.trim());

                                    if (headerText === 'month') {
                                        months.push(...cellValues);
                                    } else if (headerText === 'year') {
                                        years.push(...cellValues);
                                    } else if (headerText.includes('transunion')) {
                                        tuValues.push(...cellValues);
                                    } else if (headerText.includes('experian')) {
                                        expValues.push(...cellValues);
                                    } else if (headerText.includes('equifax')) {
                                        eqfValues.push(...cellValues);
                                    }
                                }
                            });

                            // Build unified payment history array
                            if (months.length > 0) {
                                const paymentHistory = [];
                                for (let i = 0; i < months.length; i++) {
                                    const month = months[i] || '';
                                    const year = years[i] || '';
                                    const tu = tuValues[i] || '';
                                    const exp = expValues[i] || '';
                                    const eqf = eqfValues[i] || '';

                                    // Map empty or dash to empty string, keep OK/30/60/90/CO/CL
                                    const mapVal = (v) => {
                                        if (!v || v === '-' || v === '') return '';
                                        return v.toUpperCase();
                                    };

                                    paymentHistory.push({
                                        month: month + (year ? ' \\'' + year : ''),
                                        transunion: mapVal(tu),
                                        experian: mapVal(exp),
                                        equifax: mapVal(eqf)
                                    });
                                }
                                account.payment_history = paymentHistory;
                            }
                        }
                    }

                    accounts.push(account);
                });

                return accounts;
            }"""
            )

            if js_accounts:
                logger.info(f"Extracted {len(js_accounts)} accounts from DOM")
                accounts.extend(js_accounts)

        except Exception as e:
            logger.warning(f"Account extraction failed: {e}")

        # If no accounts found, try MyFreeScoreNow 3B Report structure
        if not accounts:
            try:
                mfsn_accounts = await self.page.evaluate(
                    """() => {
                    const accounts = [];

                    // MyFreeScoreNow 3B Report uses .account-container divs
                    const containers = document.querySelectorAll('.account-container');

                    containers.forEach((container) => {
                        const account = {
                            creditor: null,
                            account_number: null,
                            account_type: null,
                            status: null,
                            balance: null,
                            credit_limit: null,
                            high_balance: null,
                            date_opened: null,
                            date_reported: null,
                            date_closed: null,
                            last_activity: null,
                            last_payment: null,
                            payment_amount: null,
                            past_due: null,
                            payment_status: null,
                            account_rating: null,
                            creditor_type: null,
                            dispute_status: null,
                            term_length: null,
                            is_negative: container.classList.contains('negative-account') ||
                                        container.querySelector('.uppercase.negative') !== null,
                            bureaus: {
                                transunion: { present: false },
                                experian: { present: false },
                                equifax: { present: false }
                            },
                            payment_history: {
                                transunion: [],
                                experian: [],
                                equifax: []
                            },
                            late_payments: {
                                transunion: { days_30: 0, days_60: 0, days_90: 0 },
                                experian: { days_30: 0, days_60: 0, days_90: 0 },
                                equifax: { days_30: 0, days_60: 0, days_90: 0 }
                            }
                        };

                        // Get creditor name
                        const nameEl = container.querySelector('[data-test-account-name]')
                                    || container.querySelector('.account-heading strong');
                        if (nameEl) {
                            account.creditor = nameEl.textContent.trim();
                        }

                        // Get status
                        const statusEl = container.querySelector('[data-test-account-status]');
                        if (statusEl) {
                            account.status = statusEl.textContent.trim();
                        }

                        // Get basic balance info from container
                        const balanceRow = container.querySelector('.attribute-row.balance .display-attribute p');
                        if (balanceRow) {
                            const balText = balanceRow.textContent.trim();
                            const match = balText.match(/\\$[\\d,]+/);
                            if (match) account.balance = match[0];
                            const origMatch = balText.match(/Orig\\.?\\s*\\$[\\d,]+/i);
                            if (origMatch) account.high_balance = origMatch[0].replace(/Orig\\.?\\s*/i, '');
                        }

                        // Get payment from container
                        const paymentRow = container.querySelector('.attribute-row.payment .display-attribute p');
                        if (paymentRow) {
                            const match = paymentRow.textContent.match(/\\$[\\d,]+/);
                            if (match) account.payment_amount = match[0];
                        }

                        // Parse the EXPANDED MODAL for full bureau-specific data
                        const modal = container.querySelector('.account-modal');
                        if (modal) {
                            // Parse the attributes table grid (4 columns: label, TU, EX, EQ)
                            const gridCells = modal.querySelectorAll('.attributes-table .d-grid > div');
                            const fieldMap = {
                                'account #': 'account_number',
                                'high balance': 'high_balance',
                                'date opened': 'date_opened',
                                'date reported': 'date_reported',
                                'closed date': 'date_closed',
                                'date of last activity': 'last_activity',
                                'balance owed': 'balance',
                                'credit limit': 'credit_limit',
                                'payment amount': 'payment_amount',
                                'last payment': 'last_payment',
                                'past due amount': 'past_due',
                                'account type': 'account_type',
                                'account rating': 'account_rating',
                                'account status': 'status',
                                'payment status': 'payment_status',
                                'creditor type': 'creditor_type',
                                'dispute status': 'dispute_status',
                                'term length': 'term_length',
                                // MyFreeScoreNow-specific fields
                                'last verified': 'last_verified',
                                'account description': 'account_description',
                                'creditor remarks': 'creditor_remarks',
                                'payment frequency': 'payment_frequency'
                            };

                            let currentLabel = null;
                            let colIndex = 0;
                            gridCells.forEach((cell, i) => {
                                const text = cell.textContent.trim();
                                const isLabel = cell.classList.contains('attribute-label');

                                if (isLabel) {
                                    currentLabel = text.toLowerCase();
                                    colIndex = 0;
                                } else if (currentLabel) {
                                    colIndex++;
                                    const val = text === '--' || text === '-' ? null : text;

                                    // Map to account field
                                    const fieldName = fieldMap[currentLabel];
                                    if (fieldName && val && !account[fieldName]) {
                                        account[fieldName] = val;
                                    }

                                    // Store bureau-specific value
                                    const bureauName = colIndex === 1 ? 'transunion' :
                                                       colIndex === 2 ? 'experian' :
                                                       colIndex === 3 ? 'equifax' : null;
                                    if (bureauName && val) {
                                        account.bureaus[bureauName].present = true;
                                        if (fieldName) {
                                            account.bureaus[bureauName][fieldName] = val;
                                        }
                                    }
                                }
                            });

                            // Parse payment history timeline
                            const historyDivs = modal.querySelectorAll('.payment-history .d-flex.flex-wrap');
                            historyDivs.forEach(div => {
                                const bureauP = div.querySelector('p.payment-history-heading, p.fw-bold');
                                if (!bureauP) return;
                                const bureauText = bureauP.textContent.toLowerCase();
                                const bureauName = bureauText.includes('transunion') ? 'transunion' :
                                                   bureauText.includes('experian') ? 'experian' :
                                                   bureauText.includes('equifax') ? 'equifax' : null;
                                if (!bureauName) return;

                                const monthDivs = div.querySelectorAll('[class^="status-"]');
                                monthDivs.forEach(md => {
                                    const status = md.className.match(/status-(\\w+)/)?.[1] || 'U';
                                    const badge = md.querySelector('.month-badge')?.textContent.trim() || '';
                                    const month = md.querySelector('.month-label')?.textContent.trim() || '';
                                    account.payment_history[bureauName].push({
                                        month: month,
                                        status: status,
                                        badge: badge
                                    });
                                });
                            });

                            // Parse late payment counts (30/60/90)
                            const lateDivs = modal.querySelectorAll('.late-history > div');
                            lateDivs.forEach(div => {
                                const bureauP = div.querySelector('p.fw-bold, p.text-transunion, p.text-experian, p.text-equifax');
                                if (!bureauP) return;
                                const bureauText = bureauP.textContent.toLowerCase();
                                const bureauName = bureauText.includes('transunion') ? 'transunion' :
                                                   bureauText.includes('experian') ? 'experian' :
                                                   bureauText.includes('equifax') ? 'equifax' : null;
                                if (!bureauName) return;

                                const gridText = div.querySelector('.d-grid')?.textContent || '';
                                const match30 = gridText.match(/30:\\s*(\\d+)/);
                                const match60 = gridText.match(/60:\\s*(\\d+)/);
                                const match90 = gridText.match(/90:\\s*(\\d+)/);
                                if (match30) account.late_payments[bureauName].days_30 = parseInt(match30[1]);
                                if (match60) account.late_payments[bureauName].days_60 = parseInt(match60[1]);
                                if (match90) account.late_payments[bureauName].days_90 = parseInt(match90[1]);
                            });

                            // Merge per-bureau payment history into unified format for template
                            const unifiedHistory = [];
                            const tuHist = account.payment_history.transunion || [];
                            const exHist = account.payment_history.experian || [];
                            const eqHist = account.payment_history.equifax || [];
                            const maxLen = Math.max(tuHist.length, exHist.length, eqHist.length);

                            // Map status codes to display values
                            const mapStatus = (entry) => {
                                if (!entry) return '';
                                if (entry.badge === 'OK' || entry.status === 'C') return 'OK';
                                if (entry.status === '1' || entry.status === '30') return '30';
                                if (entry.status === '2' || entry.status === '60') return '60';
                                if (entry.status === '3' || entry.status === '90') return '90';
                                if (entry.status === '4' || entry.status === '5' || entry.status === 'CO' || entry.status === 'CL') return 'CO';
                                return entry.badge || entry.status || '';
                            };

                            for (let i = 0; i < maxLen; i++) {
                                const tu = tuHist[i] || {};
                                const ex = exHist[i] || {};
                                const eq = eqHist[i] || {};

                                unifiedHistory.push({
                                    month: tu.month || ex.month || eq.month || '',
                                    transunion: mapStatus(tu),
                                    experian: mapStatus(ex),
                                    equifax: mapStatus(eq)
                                });
                            }
                            account.payment_history = unifiedHistory;
                        }

                        if (account.creditor) {
                            accounts.push(account);
                        }
                    });

                    return accounts;
                }"""
                )

                if mfsn_accounts:
                    logger.info(
                        f"Extracted {len(mfsn_accounts)} accounts from MyFreeScoreNow DOM"
                    )
                    accounts.extend(mfsn_accounts)

                # If still no accounts, try Classic View format extraction
                if not accounts:
                    logger.info(
                        "Trying Classic View extraction (original-view format)..."
                    )
                    classic_accounts = await self.page.evaluate(
                        """() => {
                        const accounts = [];

                        // Classic View uses sections with .d-grid.grid-cols-4 directly
                        // Account names are in .h6 > strong or .mb-3.h6 > strong
                        const accountBlocks = document.querySelectorAll('.mb-5 .border-b.border-5, .original-view .my-3.border-b');

                        accountBlocks.forEach(block => {
                            const nameEl = block.querySelector('p.h6 > strong, .h6 > strong, .mb-3.h6 > strong');
                            if (!nameEl) return;

                            const account = {
                                creditor: nameEl.textContent.trim(),
                                _from_classic_view: true,
                                bureaus: {
                                    transunion: { present: false },
                                    experian: { present: false },
                                    equifax: { present: false }
                                },
                                payment_history: {
                                    transunion: [],
                                    experian: [],
                                    equifax: []
                                },
                                late_payments: {
                                    transunion: {},
                                    experian: {},
                                    equifax: {}
                                }
                            };

                            // Parse the grid-cols-4 data
                            const grid = block.querySelector('.d-grid.grid-cols-4');
                            if (grid) {
                                // Classic View structure: labels in .labels div, values in 3 bureau columns
                                const labelCells = grid.querySelectorAll('.labels .grid-cell');
                                const tuCells = grid.querySelectorAll('.d-contents:nth-child(2) .grid-cell');
                                const exCells = grid.querySelectorAll('.d-contents:nth-child(3) .grid-cell');
                                const eqCells = grid.querySelectorAll('.d-contents:nth-child(4) .grid-cell');

                                const fieldMap = {
                                    'account #': 'account_number',
                                    'high balance:': 'high_balance',
                                    'date opened:': 'date_opened',
                                    'date reported:': 'date_reported',
                                    'closed date:': 'date_closed',
                                    'date of last activity:': 'last_activity',
                                    'balance owed:': 'balance',
                                    'credit limit:': 'credit_limit',
                                    'payment amount:': 'payment_amount',
                                    'last payment:': 'last_payment',
                                    'past due amount:': 'past_due',
                                    'account type:': 'account_type',
                                    'account rating:': 'account_rating',
                                    'account status:': 'status',
                                    'payment status:': 'payment_status',
                                    'creditor type:': 'creditor_type',
                                    'term length:': 'term_length',
                                    // MyFreeScoreNow-specific fields (Classic View)
                                    'last verified:': 'last_verified',
                                    'account description:': 'account_description',
                                    'creditor remarks:': 'creditor_remarks',
                                    'payment frequency:': 'payment_frequency'
                                };

                                // Parse each row by index
                                labelCells.forEach((labelCell, i) => {
                                    const labelText = labelCell.textContent.trim().toLowerCase();
                                    const fieldName = fieldMap[labelText];

                                    // Get values from each bureau column (same row index + 1 for header)
                                    const tuVal = tuCells[i + 1]?.textContent.trim();
                                    const exVal = exCells[i + 1]?.textContent.trim();
                                    const eqVal = eqCells[i + 1]?.textContent.trim();

                                    const cleanVal = (v) => (v && v !== '--' && v !== '-') ? v : null;

                                    if (fieldName) {
                                        // Use first non-null value for main field
                                        account[fieldName] = cleanVal(tuVal) || cleanVal(exVal) || cleanVal(eqVal);

                                        // Store bureau-specific values
                                        if (cleanVal(tuVal)) {
                                            account.bureaus.transunion.present = true;
                                            account.bureaus.transunion[fieldName] = cleanVal(tuVal);
                                        }
                                        if (cleanVal(exVal)) {
                                            account.bureaus.experian.present = true;
                                            account.bureaus.experian[fieldName] = cleanVal(exVal);
                                        }
                                        if (cleanVal(eqVal)) {
                                            account.bureaus.equifax.present = true;
                                            account.bureaus.equifax[fieldName] = cleanVal(eqVal);
                                        }
                                    }
                                });
                            }

                            // Parse payment history from .payment-history divs
                            const paymentHistoryDivs = block.querySelectorAll('.payment-history');
                            paymentHistoryDivs.forEach(phDiv => {
                                const bureauP = phDiv.querySelector('.payment-history-heading, .fw-bold');
                                if (!bureauP) return;

                                const bureauText = bureauP.textContent.toLowerCase();
                                let bureauName = null;
                                if (bureauText.includes('transunion')) bureauName = 'transunion';
                                else if (bureauText.includes('experian')) bureauName = 'experian';
                                else if (bureauText.includes('equifax')) bureauName = 'equifax';
                                if (!bureauName) return;

                                // Find the flex container with month status divs
                                const monthsContainer = phDiv.querySelector('.d-flex.gap-1.flex-wrap, .d-flex.flex-wrap.flex-1');
                                if (!monthsContainer) return;

                                const monthDivs = monthsContainer.querySelectorAll('[class^="status-"], [class*=" status-"]');
                                monthDivs.forEach(md => {
                                    const classMatch = md.className.match(/status-(\\w+)/);
                                    const status = classMatch ? classMatch[1] : 'U';
                                    const badge = md.querySelector('.month-badge')?.textContent.trim() || '';
                                    const month = md.querySelector('.month-label')?.textContent.trim() || '';
                                    account.payment_history[bureauName].push({
                                        month: month,
                                        status: status,
                                        badge: badge
                                    });
                                });
                            });

                            // Merge per-bureau payment history into unified format for template
                            try {
                                const unifiedHistory = [];
                                const tuHist = account.payment_history.transunion || [];
                                const exHist = account.payment_history.experian || [];
                                const eqHist = account.payment_history.equifax || [];
                                const maxLen = Math.max(tuHist.length, exHist.length, eqHist.length);

                                // Map status codes to display values
                                const mapStatus = (entry) => {
                                    if (!entry) return '';
                                    if (entry.badge === 'OK' || entry.status === 'C') return 'OK';
                                    if (entry.status === '1' || entry.status === '30') return '30';
                                    if (entry.status === '2' || entry.status === '60') return '60';
                                    if (entry.status === '3' || entry.status === '90') return '90';
                                    if (entry.status === '4' || entry.status === '5' || entry.status === 'CO' || entry.status === 'CL') return 'CO';
                                    return entry.badge || entry.status || '';
                                };

                                for (let i = 0; i < maxLen; i++) {
                                    const tu = tuHist[i] || {};
                                    const ex = exHist[i] || {};
                                    const eq = eqHist[i] || {};

                                    unifiedHistory.push({
                                        month: tu.month || ex.month || eq.month || '',
                                        transunion: mapStatus(tu),
                                        experian: mapStatus(ex),
                                        equifax: mapStatus(eq)
                                    });
                                }
                                account.payment_history = unifiedHistory;
                                account._merge_ran = true;
                            } catch (mergeErr) {
                                account._merge_error = mergeErr.message;
                            }

                            if (account.creditor) {
                                accounts.push(account);
                            }
                        });

                        return accounts;
                    }"""
                    )
                    if classic_accounts:
                        logger.info(
                            f"Extracted {len(classic_accounts)} accounts from Classic View"
                        )
                        accounts.extend(classic_accounts)

            except Exception as e:
                logger.warning(f"MyFreeScoreNow account extraction failed: {e}")

        # Convert payment history from per-bureau dict to unified list format for template
        def _convert_ph(acct):
            ph = acct.get("payment_history", {})
            if isinstance(ph, dict) and "transunion" in ph:
                tu = ph.get("transunion", [])
                ex = ph.get("experian", [])
                eq = ph.get("equifax", [])
                max_len = max(len(tu), len(ex), len(eq), default=0)
                unified = []
                for i in range(max_len):
                    t = tu[i] if i < len(tu) else {}
                    e = ex[i] if i < len(ex) else {}
                    q = eq[i] if i < len(eq) else {}

                    # Map status: C/OK -> OK, 1/30 -> 30, etc
                    def _map(entry):
                        if not entry:
                            return ""
                        b = entry.get("badge", "")
                        s = entry.get("status", "")
                        if b == "OK" or s == "C":
                            return "OK"
                        if s in ("1", "30"):
                            return "30"
                        if s in ("2", "60"):
                            return "60"
                        if s in ("3", "90"):
                            return "90"
                        if s in ("4", "5", "CO", "CL"):
                            return "CO"
                        return b or s or ""

                    unified.append(
                        {
                            "month": t.get("month")
                            or e.get("month")
                            or q.get("month")
                            or "",
                            "transunion": _map(t),
                            "experian": _map(e),
                            "equifax": _map(q),
                        }
                    )
                acct["payment_history"] = unified
            return acct

        if accounts:
            accounts = [_convert_ph(a) for a in accounts]
            logger.info(
                f"Converted payment history for {len(accounts)} accounts to unified format"
            )

        return accounts


def run_import_sync(
    service_name: str,
    username: str,
    password: str,
    ssn_last4: str,
    client_id: int,
    client_name: str,
) -> Dict:
    """
    Synchronous wrapper for the async import function.
    Use this when calling from Flask routes.
    """
    automation = CreditImportAutomation()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            automation.import_report(
                service_name=service_name,
                username=username,
                password=password,
                ssn_last4=ssn_last4,
                client_id=client_id,
                client_name=client_name,
            )
        )
        return result
    except Exception as e:
        logger.error(f"Sync import failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "report_path": None,
            "scores": None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        try:
            loop.close()
        except:
            pass


def check_cached_report(client_id: int) -> Optional[Dict]:
    """
    Check if a recent report exists for this client (within CACHE_HOURS).
    Returns cached data if found, None if fresh pull needed.
    """
    try:
        import json

        from database import CreditMonitoringCredential, SessionLocal

        db = SessionLocal()
        cred = (
            db.query(CreditMonitoringCredential)
            .filter(
                CreditMonitoringCredential.client_id == client_id,
                CreditMonitoringCredential.is_active == True,
            )
            .first()
        )

        if not cred or not cred.last_import_at:
            db.close()
            return None

        # Check if report is recent enough to reuse
        cache_cutoff = datetime.utcnow() - timedelta(hours=CACHE_HOURS)
        if cred.last_import_at < cache_cutoff:
            db.close()
            return None

        # Check if the last import was successful and has a report
        if cred.last_import_status != "success" or not cred.last_report_path:
            db.close()
            return None

        # Try to load the cached JSON data
        json_path = cred.last_report_path.replace(".html", ".json")
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                cached_data = json.load(f)

            logger.info(
                f"Using cached report for client {client_id} from {cred.last_import_at}"
            )
            log_activity(
                "Credit Import (Cached)",
                f"Using cached report from {cred.last_import_at.strftime('%Y-%m-%d %H:%M')}",
                client_id=client_id,
                status="success",
            )

            result = {
                "success": True,
                "cached": True,
                "report_path": cred.last_report_path,
                "scores": cached_data.get("scores", {}),
                "accounts": cached_data.get("accounts", []),
                "timestamp": cred.last_import_at.isoformat(),
            }
            db.close()
            return result

        db.close()
        return None

    except Exception as e:
        logger.error(f"Error checking cached report: {e}")
        return None


def run_import_background(
    service_name: str,
    username: str,
    password: str,
    ssn_last4: str,
    client_id: int,
    client_name: str,
    credential_id: int = None,
) -> None:
    """
    Run import in background thread. Updates database when complete.
    """
    try:
        from database import CreditMonitoringCredential, SessionLocal

        logger.info(f"Background import started for {client_name}")

        # Run the actual import
        result = run_import_sync(
            service_name=service_name,
            username=username,
            password=password,
            ssn_last4=ssn_last4,
            client_id=client_id,
            client_name=client_name,
        )

        # Update credential status in database
        if credential_id:
            db = SessionLocal()
            cred = (
                db.query(CreditMonitoringCredential).filter_by(id=credential_id).first()
            )
            if cred:
                cred.last_import_at = datetime.utcnow()
                # Check for success - result has "report_path" key when successful
                report_path = result.get("report_path") or result.get("path")
                if result and report_path:
                    cred.last_import_status = "success"
                    cred.last_import_error = None
                    cred.last_report_path = report_path
                    logger.info(
                        f"Updated credential {credential_id} with report path: {report_path}"
                    )
                else:
                    cred.last_import_status = "failed"
                    cred.last_import_error = (
                        result.get("error") if result else "Import returned None"
                    )
                db.commit()
            db.close()

        logger.info(
            f"Background import completed for {client_name}: success={result.get('success')}"
        )

    except Exception as e:
        logger.error(f"Background import failed for {client_name}: {e}")


def run_import_async(
    service_name: str,
    username: str,
    password: str,
    ssn_last4: str,
    client_id: int,
    client_name: str,
    credential_id: int = None,
    use_cache: bool = True,
) -> Dict:
    """
    Start import and return immediately. Import runs in background.
    Checks cache first - returns cached data instantly if available.

    Returns:
        Dict with status. If cached, returns full data immediately.
        If not cached, returns "processing" status while import runs in background.
    """
    # Check cache first
    if use_cache:
        cached = check_cached_report(client_id)
        if cached:
            return cached

    # No cache - start background import
    log_activity(
        "Credit Import Queued",
        f"{client_name} | {service_name} | Running in background",
        client_id=client_id,
        status="info",
    )

    # Start background thread
    thread = threading.Thread(
        target=run_import_background,
        args=(
            service_name,
            username,
            password,
            ssn_last4,
            client_id,
            client_name,
            credential_id,
        ),
        daemon=True,
    )
    thread.start()

    return {
        "success": True,
        "processing": True,
        "message": "Import started in background. Check back in 1-2 minutes.",
        "timestamp": datetime.utcnow().isoformat(),
    }


def test_browser_availability() -> Tuple[bool, str]:
    """Test if Playwright browser is available and working."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = browser.new_page()
            page.goto("about:blank")
            browser.close()
            return True, "Browser automation ready"
    except Exception as e:
        return False, f"Browser not available: {str(e)}"
