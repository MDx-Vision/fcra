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
        'login_url': 'https://member.myscoreiq.com/login.aspx',
        'username_selector': '#txtUserName',
        'password_selector': '#txtPassword',
        'ssn_last4_selector': '#txtSSN',
        'login_button_selector': '#btnLogin',
        'report_download_flow': 'myscoreiq',
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
            await self.page.goto(config['login_url'], wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)
            
            username_field = await self.page.query_selector(config['username_selector'])
            if username_field:
                await username_field.fill(username)
            else:
                for selector in ['input[type="email"]', 'input[name="email"]', 'input[name="username"]', '#email', '#username']:
                    username_field = await self.page.query_selector(selector)
                    if username_field:
                        await username_field.fill(username)
                        break
            
            password_field = await self.page.query_selector(config['password_selector'])
            if password_field:
                await password_field.fill(password)
            else:
                for selector in ['input[type="password"]', 'input[name="password"]', '#password']:
                    password_field = await self.page.query_selector(selector)
                    if password_field:
                        await password_field.fill(password)
                        break
            
            if config.get('ssn_last4_selector') and ssn_last4:
                ssn_field = await self.page.query_selector(config['ssn_last4_selector'])
                if ssn_field:
                    await ssn_field.fill(ssn_last4)
                else:
                    for selector in ['input[name="ssn"]', 'input[name="ssn4"]', 'input[name="ssn_last4"]', '#ssn', '#ssn4']:
                        ssn_field = await self.page.query_selector(selector)
                        if ssn_field:
                            await ssn_field.fill(ssn_last4)
                            break
            
            await asyncio.sleep(1)
            
            login_button = await self.page.query_selector(config['login_button_selector'])
            if login_button:
                await login_button.click()
            else:
                for selector in ['button[type="submit"]', 'input[type="submit"]', '.login-button', '#login-btn']:
                    login_button = await self.page.query_selector(selector)
                    if login_button:
                        await login_button.click()
                        break
            
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            current_url = self.page.url.lower()
            if 'login' in current_url and 'dashboard' not in current_url and 'member' not in current_url:
                error_element = await self.page.query_selector('.error, .alert-danger, .login-error, #error-message')
                if error_element:
                    error_text = await error_element.text_content()
                    logger.error(f"Login error: {error_text}")
                    return False
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
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
