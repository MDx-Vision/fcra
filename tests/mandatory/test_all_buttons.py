#!/usr/bin/env python3
"""TASK 2: Click ALL buttons"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5001"

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "buttons_found": 0,
    "buttons_clicked": 0,
    "buttons_skipped": 0,
    "errors": [],
    "log": []
}

SKIP_BUTTONS = ["delete", "remove", "logout", "sign out", "cancel subscription", "deactivate"]

async def click_all_buttons():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        pages = [
            "/", "/signup", "/staff/login", "/portal/login",
            "/dashboard", "/dashboard/clients", "/dashboard/signups",
            "/dashboard/cases", "/dashboard/settlements", "/dashboard/staff",
            "/dashboard/analytics", "/dashboard/credit-tracker", "/dashboard/calendar",
            "/dashboard/contacts", "/dashboard/automation-tools", "/dashboard/letter-queue",
            "/dashboard/demand-generator", "/dashboard/import", "/dashboard/documents",
            "/dashboard/settings", "/dashboard/integrations", "/dashboard/billing",
            "/dashboard/tasks", "/dashboard/workflows", "/dashboard/ml-insights",
            "/dashboard/white-label", "/dashboard/franchise", "/dashboard/affiliates",
            "/dashboard/triage", "/dashboard/escalation", "/dashboard/case-law",
            "/dashboard/knowledge-base", "/dashboard/sops", "/dashboard/chexsystems",
            "/dashboard/specialty-bureaus", "/dashboard/furnishers", "/dashboard/patterns",
            "/dashboard/sol", "/dashboard/cfpb", "/dashboard/frivolousness", "/dashboard/predictive",
            "/dashboard/credit-import", "/dashboard/performance", "/dashboard/suspense-accounts",
        ]

        for url in pages:
            await test_buttons_on_page(page, url)

        await browser.close()

    save_results()

async def test_buttons_on_page(page, url):
    """Find and click every button on a page"""

    RESULTS["log"].append(f"\n=== Scanning: {url} ===")

    try:
        await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=15000)

        # Find ALL clickable elements
        buttons = await page.query_selector_all(
            "button, "
            "[type='submit'], "
            "[type='button'], "
            ".btn, "
            "[role='button'], "
            "[onclick]"
        )

        page_buttons = len(buttons)
        RESULTS["log"].append(f"  Found {page_buttons} buttons")
        RESULTS["buttons_found"] += page_buttons

        clicked_on_page = 0
        for i, button in enumerate(buttons):
            try:
                text = ""
                try:
                    text = await button.inner_text() or ""
                    text = text.strip().lower()[:30]
                except:
                    pass

                btn_id = await button.get_attribute("id") or ""

                is_visible = await button.is_visible()
                is_enabled = await button.is_enabled()

                if not is_visible or not is_enabled:
                    RESULTS["buttons_skipped"] += 1
                    continue

                if any(skip in text for skip in SKIP_BUTTONS):
                    RESULTS["buttons_skipped"] += 1
                    continue

                await button.click(timeout=3000)
                RESULTS["buttons_clicked"] += 1
                clicked_on_page += 1

                await page.wait_for_timeout(200)

                # Close any modal that opened
                modal = await page.query_selector(".modal.show, .modal[style*='display: block']")
                if modal:
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(200)

                # Return to page if navigated
                if url not in page.url:
                    await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=10000)

            except Exception as e:
                RESULTS["errors"].append({
                    "url": url,
                    "button_index": i,
                    "error": str(e)[:50]
                })
                try:
                    await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=10000)
                except:
                    pass

        RESULTS["log"].append(f"  Clicked {clicked_on_page} buttons")

    except Exception as e:
        RESULTS["errors"].append({"url": url, "error": str(e)[:100]})

def save_results():
    with open("tests/mandatory/TASK2_BUTTONS_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)

    report = f"""# TASK 2: BUTTON CLICK RESULTS

**Target:** 1,584 buttons
**Timestamp:** {RESULTS['timestamp']}

## Summary
| Metric | Count |
|--------|-------|
| Buttons Found | {RESULTS['buttons_found']} |
| Buttons Clicked | {RESULTS['buttons_clicked']} |
| Buttons Skipped | {RESULTS['buttons_skipped']} |
| Errors | {len(RESULTS['errors'])} |

## Click Log
```
{chr(10).join(RESULTS['log'])}
```
"""

    with open("tests/mandatory/TASK2_BUTTONS_REPORT.md", "w") as f:
        f.write(report)

    print(f"\nTASK 2 COMPLETE:")
    print(f"  Buttons found: {RESULTS['buttons_found']}")
    print(f"  Buttons clicked: {RESULTS['buttons_clicked']}")

if __name__ == "__main__":
    asyncio.run(click_all_buttons())
