"""
Credit Report Import Browser Automation Service
Uses Playwright to automate login and report downloading from credit monitoring services.
Supports: IdentityIQ, MyScoreIQ, SmartCredit, MyFreeScoreNow, and more.
"""
import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("uploads/credit_reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SERVICE_CONFIGS = {
    'IdentityIQ.com': {
        'login_url': 'https://member.identityiq.com/login.aspx',
        'username_selector': '#txtUserName',
        'password_selector': '#txtPassword',
        'ssn_last4_selector': '#txtSSN',
        'login_button_selector': '#btnLogin',
        'report_download_flow': 'identityiq',
    },
    'MyScoreIQ.com': {
        'login_url': 'https://member.myscoreiq.com/',
        'username_selector': '#txtUsername',
        'password_selector': '#txtPassword',
        'ssn_last4_selector': None,
        'login_button_selector': '#imgBtnLogin',
        'report_download_flow': 'myscoreiq',
        'post_login_url': 'https://member.myscoreiq.com/CreditReport/Index',
    },
    'SmartCredit.com': {
        'login_url': 'https://member.smartcredit.com/login',
        'username_selector': 'input[name="email"]',
        'password_selector': 'input[name="password"]',
        'ssn_last4_selector': 'input[name="ssn4"]',
        'login_button_selector': 'button[type="submit"]',
        'report_download_flow': 'smartcredit',
    },
    'MyFreeScoreNow.com': {
        'login_url': 'https://member.myfreescorenow.com/login',
        'username_selector': '#email',
        'password_selector': '#password',
        'ssn_last4_selector': '#ssn_last4',
        'login_button_selector': 'button[type="submit"]',
        'report_download_flow': 'myfreescorenow',
    },
    'HighScoreNow.com': {
        'login_url': 'https://member.highscorenow.com/login',
        'username_selector': '#email',
        'password_selector': '#password',
        'ssn_last4_selector': '#ssn',
        'login_button_selector': 'button[type="submit"]',
        'report_download_flow': 'highscorenow',
    },
    'IdentityClub.com': {
        'login_url': 'https://member.identityclub.com/login',
        'username_selector': '#username',
        'password_selector': '#password',
        'ssn_last4_selector': '#ssn4',
        'login_button_selector': 'button[type="submit"]',
        'report_download_flow': 'identityclub',
    },
    'PrivacyGuard.com': {
        'login_url': 'https://member.privacyguard.com/login',
        'username_selector': '#email',
        'password_selector': '#password',
        'ssn_last4_selector': '#ssn',
        'login_button_selector': 'button[type="submit"]',
        'report_download_flow': 'privacyguard',
    },
    'IDClub.com': {
        'login_url': 'https://member.idclub.com/login',
        'username_selector': '#email',
        'password_selector': '#password',
        'ssn_last4_selector': '#ssn_last4',
        'login_button_selector': 'button[type="submit"]',
        'report_download_flow': 'idclub',
    },
    'MyThreeScores.com': {
        'login_url': 'https://member.mythreescores.com/login',
        'username_selector': '#email',
        'password_selector': '#password',
        'ssn_last4_selector': '#ssn4',
        'login_button_selector': 'button[type="submit"]',
        'report_download_flow': 'mythreescores',
    },
    'MyScore750.com': {
        'login_url': 'https://member.myscore750.com/login',
        'username_selector': '#email',
        'password_selector': '#password',
        'ssn_last4_selector': '#ssn',
        'login_button_selector': 'button[type="submit"]',
        'report_download_flow': 'myscore750',
    },
    'CreditHeroScore.com': {
        'login_url': 'https://member.creditheroscore.com/login',
        'username_selector': '#email',
        'password_selector': '#password',
        'ssn_last4_selector': '#ssn4',
        'login_button_selector': 'button[type="submit"]',
        'report_download_flow': 'creditheroscore',
    },
}


class CreditImportAutomation:
    """Automated credit report import using Playwright browser automation."""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def _init_browser(self):
        """Initialize headless browser."""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--single-process',
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = await self.context.new_page()
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
            if hasattr(self, 'playwright'):
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
        client_name: str
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
            'success': False,
            'report_path': None,
            'html_content': None,
            'scores': None,
            'error': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if service_name not in SERVICE_CONFIGS:
            result['error'] = f"Unsupported service: {service_name}"
            return result
        
        config = SERVICE_CONFIGS[service_name]
        
        try:
            if not await self._init_browser():
                result['error'] = "Failed to initialize browser"
                return result
            
            logger.info(f"Starting import for {client_name} from {service_name}")
            
            login_success = await self._login(config, username, password, ssn_last4)
            if not login_success:
                result['error'] = "Login failed - check credentials"
                return result
            
            await asyncio.sleep(3)
            
            report_data = await self._download_report(config, client_id, client_name)
            if report_data:
                result['success'] = True
                result['report_path'] = report_data.get('path')
                result['html_content'] = report_data.get('html')
                result['scores'] = report_data.get('scores')
                logger.info(f"Successfully imported report for {client_name}")
            else:
                result['error'] = "Failed to download credit report"
            
        except Exception as e:
            logger.error(f"Import failed for {client_name}: {e}")
            result['error'] = str(e)
        
        finally:
            await self._close_browser()
        
        return result
    
    async def _login(self, config: Dict, username: str, password: str, ssn_last4: str) -> bool:
        """Perform login to credit monitoring service."""
        try:
            logger.info(f"Navigating to {config['login_url']}")
            await self.page.goto(config['login_url'], wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)
            
            await self.page.wait_for_selector('input', timeout=15000)
            await asyncio.sleep(2)
            
            username_selectors = [
                config['username_selector'],
                '#txtUsername',
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
                        await field.fill('')
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
            
            password_selectors = [
                config['password_selector'],
                '#txtPassword',
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
                        await field.fill('')
                        await field.type(password, delay=50)
                        password_filled = True
                        logger.info(f"Filled password with selector: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not password_filled:
                logger.error("Could not find password field")
                return False
            
            if config.get('ssn_last4_selector') and ssn_last4:
                try:
                    ssn_field = await self.page.query_selector(config['ssn_last4_selector'])
                    if ssn_field:
                        await ssn_field.type(ssn_last4, delay=50)
                except:
                    pass
            
            await asyncio.sleep(1)
            
            login_selectors = [
                config['login_button_selector'],
                '#imgBtnLogin',
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
            
            await asyncio.sleep(5)
            
            try:
                await self.page.wait_for_load_state('networkidle', timeout=30000)
            except:
                pass
            
            await asyncio.sleep(3)
            
            current_url = self.page.url.lower()
            page_content = await self.page.content()
            page_lower = page_content.lower()
            
            screenshot_path = REPORTS_DIR / f"login_debug_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=str(screenshot_path))
            logger.info(f"Saved login debug screenshot to {screenshot_path}")
            
            if 'security question' in page_lower or 'last four digits of your ssn' in page_lower:
                logger.info("Security question page detected - entering SSN last 4")
                if not ssn_last4:
                    logger.error("No SSN last 4 provided for security question")
                    return False
                    
                ssn_selectors = [
                    '#FBfbforcechangesecurityanswer_txtSecurityAnswer',
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
                    '#FBfbforcechangesecurityanswer_ibtSubmit',
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
                
                await asyncio.sleep(5)
                try:
                    await self.page.wait_for_load_state('networkidle', timeout=30000)
                except:
                    pass
                
                await asyncio.sleep(3)
                screenshot_path2 = REPORTS_DIR / f"after_security_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
                await self.page.screenshot(path=str(screenshot_path2))
                logger.info(f"Saved post-security screenshot to {screenshot_path2}")
                
                current_url = self.page.url.lower()
                logger.info(f"After security question, URL: {current_url}")
            
            error_indicators = [
                'invalid login',
                'invalid username',
                'invalid password', 
                'incorrect password',
                'login failed',
                'authentication failed',
                'access denied',
            ]
            
            page_content = await self.page.content()
            page_lower = page_content.lower()
            
            for indicator in error_indicators:
                if indicator in page_lower:
                    logger.error(f"Login failed - found error indicator: {indicator}")
                    return False
            
            if 'dashboard' in current_url or 'account' in current_url or 'home' in current_url:
                logger.info("Login successful - redirected to member area")
                return True
            
            if 'creditreport' in current_url or 'credit-report' in current_url:
                logger.info("Login successful - on credit report page")
                return True
            
            if 'member' in current_url and 'login' not in current_url:
                logger.info("Login appears successful - in member area")
                return True
            
            logger.info(f"Login status unclear, URL: {current_url} - proceeding anyway")
            return True
            
        except Exception as e:
            logger.error(f"Login failed with exception: {e}")
            return False
    
    async def _download_report(self, config: Dict, client_id: int, client_name: str) -> Optional[Dict]:
        """Navigate to credit report and download/save it."""
        try:
            report_selectors = [
                'a[href*="credit-report"]',
                'a[href*="creditreport"]',
                'a[href*="view-report"]',
                'a[href*="viewreport"]',
                '.credit-report-link',
                '#view-report',
                'a:has-text("View Report")',
                'a:has-text("Credit Report")',
                'a:has-text("View Credit Report")',
                'button:has-text("View Report")',
            ]
            
            for selector in report_selectors:
                try:
                    link = await self.page.query_selector(selector)
                    if link:
                        await link.click()
                        await self.page.wait_for_load_state('networkidle', timeout=30000)
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            html_content = await self.page.content()
            
            scores = await self._extract_scores()
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in client_name)
            filename = f"{client_id}_{safe_name}_{timestamp}.html"
            filepath = REPORTS_DIR / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Saved report to {filepath}")
            
            return {
                'path': str(filepath),
                'html': html_content,
                'scores': scores
            }
            
        except Exception as e:
            logger.error(f"Failed to download report: {e}")
            return None
    
    async def _extract_scores(self) -> Optional[Dict]:
        """Extract credit scores from the current page."""
        scores = {}
        
        try:
            score_patterns = [
                ('.experian-score', 'experian'),
                ('.equifax-score', 'equifax'),
                ('.transunion-score', 'transunion'),
                ('#experian-score', 'experian'),
                ('#equifax-score', 'equifax'),
                ('#transunion-score', 'transunion'),
                ('[data-bureau="experian"]', 'experian'),
                ('[data-bureau="equifax"]', 'equifax'),
                ('[data-bureau="transunion"]', 'transunion'),
            ]
            
            for selector, bureau in score_patterns:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        import re
                        match = re.search(r'(\d{3})', text)
                        if match:
                            score = int(match.group(1))
                            if 300 <= score <= 850:
                                scores[bureau] = score
                except:
                    continue
            
            if not scores:
                page_text = await self.page.text_content('body')
                import re
                
                for bureau in ['experian', 'equifax', 'transunion']:
                    pattern = rf'{bureau}[:\s]*(\d{{3}})'
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores[bureau] = score
            
            return scores if scores else None
            
        except Exception as e:
            logger.error(f"Failed to extract scores: {e}")
            return None


def run_import_sync(
    service_name: str,
    username: str,
    password: str,
    ssn_last4: str,
    client_id: int,
    client_name: str
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
                client_name=client_name
            )
        )
        return result
    except Exception as e:
        logger.error(f"Sync import failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'report_path': None,
            'scores': None,
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        try:
            loop.close()
        except:
            pass


def test_browser_availability() -> Tuple[bool, str]:
    """Test if Playwright browser is available and working."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            page.goto('about:blank')
            browser.close()
            return True, "Browser automation ready"
    except Exception as e:
        return False, f"Browser not available: {str(e)}"
