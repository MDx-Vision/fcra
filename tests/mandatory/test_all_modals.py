#!/usr/bin/env python3
"""TASK 3: Test ALL modals"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5001"

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "modals_found": 0,
    "modals_opened": 0,
    "modals_closed": 0,
    "modals_with_forms": 0,
    "issues": [],
    "log": []
}

async def test_all_modals():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        pages = [
            "/dashboard", "/dashboard/clients", "/dashboard/cases",
            "/dashboard/settlements", "/dashboard/staff", "/dashboard/contacts",
            "/dashboard/tasks", "/dashboard/calendar", "/dashboard/documents",
            "/dashboard/billing", "/dashboard/settings", "/dashboard/integrations",
            "/dashboard/signups", "/dashboard/automation-tools", "/dashboard/letter-queue",
            "/dashboard/demand-generator", "/dashboard/import", "/dashboard/analytics",
        ]

        for url in pages:
            await test_modals_on_page(page, url)

        await browser.close()

    save_results()

async def test_modals_on_page(page, url):
    """Find and test every modal on a page"""

    RESULTS["log"].append(f"\n=== Testing modals on: {url} ===")

    try:
        await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=15000)

        triggers = await page.query_selector_all(
            "[data-bs-toggle='modal'], "
            "[data-toggle='modal']"
        )

        RESULTS["log"].append(f"  Found {len(triggers)} modal triggers")

        for i, trigger in enumerate(triggers):
            try:
                target = await trigger.get_attribute("data-bs-target") or await trigger.get_attribute("data-target") or ""
                trigger_text = ""
                try:
                    trigger_text = await trigger.inner_text() or ""
                    trigger_text = trigger_text.strip()[:30]
                except:
                    pass

                is_visible = await trigger.is_visible()
                if not is_visible:
                    continue

                RESULTS["modals_found"] += 1

                await trigger.click()
                await page.wait_for_timeout(500)

                modal = await page.query_selector(".modal.show, .modal.in, .modal[style*='display: block']")

                if modal:
                    RESULTS["modals_opened"] += 1
                    RESULTS["log"].append(f"    OPENED: {trigger_text} -> {target}")

                    form = await modal.query_selector("form")
                    if form:
                        RESULTS["modals_with_forms"] += 1

                    # Close modal
                    close = await modal.query_selector(
                        "[data-bs-dismiss='modal'], "
                        "[data-dismiss='modal'], "
                        ".btn-close, "
                        ".close"
                    )

                    if close:
                        await close.click()
                        await page.wait_for_timeout(300)

                        still_open = await page.query_selector(".modal.show, .modal.in")
                        if not still_open:
                            RESULTS["modals_closed"] += 1
                            RESULTS["log"].append(f"    CLOSED")
                        else:
                            await page.keyboard.press("Escape")
                            await page.wait_for_timeout(200)
                    else:
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(300)
                        RESULTS["modals_closed"] += 1
                else:
                    RESULTS["issues"].append({
                        "url": url,
                        "trigger": trigger_text,
                        "issue": "Modal did not open"
                    })

            except Exception as e:
                RESULTS["issues"].append({
                    "url": url,
                    "trigger_index": i,
                    "error": str(e)[:100]
                })
                await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=10000)

    except Exception as e:
        RESULTS["log"].append(f"  ERROR: {str(e)[:50]}")

def save_results():
    with open("tests/mandatory/TASK3_MODALS_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2)

    report = f"""# TASK 3: MODAL TESTING RESULTS

**Timestamp:** {RESULTS['timestamp']}

## Summary
| Metric | Count |
|--------|-------|
| Modal Triggers Found | {RESULTS['modals_found']} |
| Modals Opened | {RESULTS['modals_opened']} |
| Modals Closed | {RESULTS['modals_closed']} |
| Modals with Forms | {RESULTS['modals_with_forms']} |
| Issues | {len(RESULTS['issues'])} |

## Log
```
{chr(10).join(RESULTS['log'])}
```

## Issues
"""
    for issue in RESULTS['issues']:
        report += f"- {issue}\n"

    with open("tests/mandatory/TASK3_MODALS_REPORT.md", "w") as f:
        f.write(report)

    print(f"\nTASK 3 COMPLETE:")
    print(f"  Modals opened: {RESULTS['modals_opened']}")
    print(f"  Modals closed: {RESULTS['modals_closed']}")

if __name__ == "__main__":
    asyncio.run(test_all_modals())
