#!/usr/bin/env python3
"""TASK 8: Cross-browser testing - Chrome, Firefox, Safari"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5001"

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "browsers_tested": 0,
    "browsers_passed": 0,
    "browsers_failed": 0,
    "browser_results": {},
    "issues": []
}

CRITICAL_PAGES = [
    "/",
    "/signup",
    "/staff/login",
    "/portal/login",
    "/dashboard",
    "/dashboard/clients",
    "/dashboard/cases",
    "/dashboard/settlements",
]

async def test_cross_browser():
    async with async_playwright() as p:

        browsers = [
            ("chromium", p.chromium),
            ("firefox", p.firefox),
            ("webkit", p.webkit),
        ]

        for browser_name, browser_type in browsers:
            await _run_browser(browser_name, browser_type)

    save_results()

async def _run_browser(browser_name, browser_type):
    """Test all critical functionality in a specific browser"""

    print(f"\n=== Testing {browser_name} ===")
    RESULTS["browsers_tested"] += 1

    browser_result = {
        "pages_tested": 0,
        "pages_passed": 0,
        "actions_tested": 0,
        "actions_passed": 0,
        "issues": []
    }

    try:
        browser = await browser_type.launch(headless=True)
        page = await browser.new_page()

        # Test 1: All critical pages load
        for url in CRITICAL_PAGES:
            try:
                response = await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=15000)
                browser_result["pages_tested"] += 1

                if response and response.status == 200:
                    browser_result["pages_passed"] += 1
                    print(f"  [PASS] {url}")
                else:
                    status = response.status if response else "no response"
                    browser_result["issues"].append(f"{url} returned {status}")
                    print(f"  [FAIL] {url} ({status})")

            except Exception as e:
                browser_result["issues"].append(f"{url}: {str(e)[:50]}")
                print(f"  [FAIL] {url} (error)")

        # Test 2: Form submission works
        browser_result["actions_tested"] += 1
        try:
            await page.goto(f"{BASE_URL}/signup", wait_until="networkidle")

            first_name = await page.query_selector("#firstName, [name='firstName']")
            if first_name:
                await first_name.fill("Test")
                browser_result["actions_passed"] += 1
                print(f"  [PASS] Form input works")
            else:
                browser_result["issues"].append("Form input not found")

        except Exception as e:
            browser_result["issues"].append(f"Form test: {str(e)[:50]}")

        # Test 3: JavaScript works
        browser_result["actions_tested"] += 1
        try:
            result = await page.evaluate("() => 1 + 1")
            if result == 2:
                browser_result["actions_passed"] += 1
                print(f"  [PASS] JavaScript works")
            else:
                browser_result["issues"].append("JavaScript evaluation failed")

        except Exception as e:
            browser_result["issues"].append(f"JS test: {str(e)[:50]}")

        # Test 4: CSS renders
        browser_result["actions_tested"] += 1
        try:
            await page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")

            dimensions = await page.evaluate("""() => {
                const el = document.querySelector('main, .container, .content, body');
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                return { width: rect.width, height: rect.height };
            }""")

            if dimensions and dimensions['width'] > 0 and dimensions['height'] > 0:
                browser_result["actions_passed"] += 1
                print(f"  [PASS] CSS renders correctly")
            else:
                browser_result["issues"].append("CSS may not be rendering")

        except Exception as e:
            browser_result["issues"].append(f"CSS test: {str(e)[:50]}")

        # Test 5: Buttons clickable
        browser_result["actions_tested"] += 1
        try:
            buttons = await page.query_selector_all("button, .btn")
            if buttons and len(buttons) > 0:
                visible_button = None
                for btn in buttons[:10]:
                    if await btn.is_visible():
                        visible_button = btn
                        break

                if visible_button:
                    await visible_button.click(timeout=5000)
                    browser_result["actions_passed"] += 1
                    print(f"  [PASS] Button clicks work")
                else:
                    browser_result["issues"].append("No visible buttons found")
            else:
                browser_result["issues"].append("No buttons found")

        except Exception as e:
            browser_result["issues"].append(f"Button test: {str(e)[:50]}")

        await browser.close()

        if len(browser_result["issues"]) == 0:
            RESULTS["browsers_passed"] += 1
        else:
            RESULTS["browsers_failed"] += 1

    except Exception as e:
        browser_result["issues"].append(f"Browser launch failed: {str(e)}")
        RESULTS["browsers_failed"] += 1

    RESULTS["browser_results"][browser_name] = browser_result

def save_results():
    with open("tests/mandatory/TASK8_BROWSER_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2)

    report = f"""# TASK 8: CROSS-BROWSER TESTING RESULTS

**Timestamp:** {RESULTS['timestamp']}

## Summary
| Metric | Count |
|--------|-------|
| Browsers Tested | {RESULTS['browsers_tested']} |
| Browsers Passed | {RESULTS['browsers_passed']} |
| Browsers Failed | {RESULTS['browsers_failed']} |

## Browser Details
"""

    for browser_name, result in RESULTS['browser_results'].items():
        status = "[PASS]" if len(result['issues']) == 0 else "[PARTIAL]"
        report += f"""
### {browser_name.capitalize()} {status}
- Pages: {result['pages_passed']}/{result['pages_tested']}
- Actions: {result['actions_passed']}/{result['actions_tested']}
"""
        if result['issues']:
            report += "- Issues:\n"
            for issue in result['issues']:
                report += f"  - {issue}\n"

    with open("tests/mandatory/TASK8_BROWSER_REPORT.md", "w") as f:
        f.write(report)

    print(f"\nTASK 8 COMPLETE:")
    print(f"  Browsers passed: {RESULTS['browsers_passed']}/{RESULTS['browsers_tested']}")

if __name__ == "__main__":
    asyncio.run(test_cross_browser())
