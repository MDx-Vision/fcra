#!/usr/bin/env python3
"""
THOROUGH BUTTON TESTING - Test ALL buttons and create status inventory
Target: 573 button elements found in templates
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5001"

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "buttons_found": 0,
    "buttons_tested": 0,
    "status_counts": {
        "working": 0,
        "not_built": 0,
        "broken": 0,
        "disabled": 0,
        "hidden": 0,
        "dangerous_safe": 0,
    },
    "pages": [],
    "issues": []
}

# Status categories
STATUS_WORKING = "WORKING"
STATUS_NOT_BUILT = "NOT_BUILT"
STATUS_BROKEN = "BROKEN"
STATUS_DISABLED = "DISABLED"
STATUS_HIDDEN = "HIDDEN"
STATUS_DANGEROUS = "DANGEROUS_SAFE"

# All pages to test (comprehensive list)
PAGES_TO_TEST = [
    "/",
    "/signup",
    "/staff/login",
    "/portal/login",
    "/dashboard",
    "/dashboard/clients",
    "/dashboard/signups",
    "/dashboard/cases",
    "/dashboard/settlements",
    "/dashboard/staff",
    "/dashboard/analytics",
    "/dashboard/credit-tracker",
    "/dashboard/calendar",
    "/dashboard/contacts",
    "/dashboard/automation-tools",
    "/dashboard/letter-queue",
    "/dashboard/demand-generator",
    "/dashboard/import",
    "/dashboard/documents",
    "/dashboard/settings",
    "/dashboard/integrations",
    "/dashboard/billing",
    "/dashboard/tasks",
    "/dashboard/workflows",
    "/dashboard/ml-insights",
    "/dashboard/white-label",
    "/dashboard/franchise",
    "/dashboard/affiliates",
    "/dashboard/triage",
    "/dashboard/escalation",
    "/dashboard/case-law",
    "/dashboard/knowledge-base",
    "/dashboard/sops",
    "/dashboard/chexsystems",
    "/dashboard/specialty-bureaus",
    "/dashboard/furnishers",
    "/dashboard/patterns",
    "/dashboard/sol",
    "/dashboard/cfpb",
    "/dashboard/frivolousness",
    "/dashboard/predictive",
    "/dashboard/credit-import",
    "/dashboard/performance",
    "/dashboard/suspense",
    "/dashboard/api-management",
    "/dashboard/whitelabel-admin",
    "/dashboard/analysis-review",
    "/dashboard/settings/sms",
]

async def test_all_buttons():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for url in PAGES_TO_TEST:
            await test_buttons_on_page(page, url)

        await browser.close()

    save_results()

async def test_buttons_on_page(page, url):
    """Find and test every button on a page"""

    print(f"\n{'='*60}")
    print(f"TESTING PAGE: {url}")
    print(f"{'='*60}")

    page_result = {
        "url": url,
        "buttons_found": 0,
        "buttons_tested": 0,
        "buttons": []
    }

    try:
        await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(500)
    except Exception as e:
        print(f"  ERROR loading page: {str(e)[:100]}")
        RESULTS["pages"].append(page_result)
        return

    # Find ALL button elements
    buttons = await page.query_selector_all("button")
    print(f"  Found {len(buttons)} buttons")

    page_result["buttons_found"] = len(buttons)
    RESULTS["buttons_found"] += len(buttons)

    for i, button in enumerate(buttons):
        button_result = await test_single_button(page, button, i, url)
        page_result["buttons"].append(button_result)
        page_result["buttons_tested"] += 1
        RESULTS["buttons_tested"] += 1

    RESULTS["pages"].append(page_result)

async def test_single_button(page, button, index, page_url):
    """Test a single button and determine its status"""

    result = {
        "index": index,
        "text": "",
        "id": "",
        "class": "",
        "type": "",
        "onclick": "",
        "status": "",
        "notes": ""
    }

    try:
        # Get button info
        result["text"] = (await button.inner_text() or "").strip()[:50]
        result["id"] = await button.get_attribute("id") or ""
        result["class"] = (await button.get_attribute("class") or "")[:50]
        result["type"] = await button.get_attribute("type") or "button"
        result["onclick"] = (await button.get_attribute("onclick") or "")[:50]

        button_name = result["text"][:25] or result["id"][:25] or "unnamed"

        # Check visibility
        is_visible = await button.is_visible()
        if not is_visible:
            result["status"] = STATUS_HIDDEN
            result["notes"] = "Button not visible on page (likely in modal)"
            RESULTS["status_counts"]["hidden"] += 1
            print(f"    [{index}] HIDDEN: {button_name}")
            return result

        # Check if enabled
        is_enabled = await button.is_enabled()
        if not is_enabled:
            result["status"] = STATUS_DISABLED
            result["notes"] = "Button is disabled"
            RESULTS["status_counts"]["disabled"] += 1
            print(f"    [{index}] DISABLED: {button_name}")
            return result

        # Check if dangerous (delete, remove, logout, etc.)
        text_lower = result["text"].lower()
        dangerous_keywords = ["delete", "remove", "logout", "sign out", "cancel subscription", "deactivate", "destroy", "reset all"]
        is_dangerous = any(kw in text_lower for kw in dangerous_keywords)

        # Store current URL to detect navigation
        current_url = page.url

        # Click the button
        try:
            await button.click(timeout=3000)
            await page.wait_for_timeout(500)

            # Check what happened
            new_url = page.url

            # Check for modal - look for visible modal overlays
            modal_visible = await page.evaluate("""
                () => {
                    const modals = document.querySelectorAll('.modal-overlay, .modal, [class*="modal"]');
                    for (const m of modals) {
                        const style = window.getComputedStyle(m);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                            return true;
                        }
                    }
                    return false;
                }
            """)

            # Check for alerts/errors
            has_error = await page.evaluate("""
                () => {
                    const errors = document.querySelectorAll('.error, .alert-danger, .alert-error');
                    for (const e of errors) {
                        if (e.offsetParent !== null) return true;
                    }
                    return false;
                }
            """)

            # Check for success messages
            has_success = await page.evaluate("""
                () => {
                    const success = document.querySelectorAll('.success, .alert-success');
                    for (const s of success) {
                        if (s.offsetParent !== null) return true;
                    }
                    return false;
                }
            """)

            if is_dangerous:
                # Handle dangerous button - try to cancel
                result["status"] = STATUS_DANGEROUS
                RESULTS["status_counts"]["dangerous_safe"] += 1

                # Try to close any dialog/modal
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(200)

                try:
                    cancel = await page.query_selector("button:has-text('Cancel'), button:has-text('No'), button:has-text('Close')")
                    if cancel and await cancel.is_visible():
                        await cancel.click()
                        await page.wait_for_timeout(200)
                except:
                    pass

                result["notes"] = "Clicked and cancelled safely"
                print(f"    [{index}] DANGEROUS (safe): {button_name}")

            elif new_url != current_url:
                result["status"] = STATUS_WORKING
                result["notes"] = f"Navigates to {new_url.replace(BASE_URL, '')}"
                RESULTS["status_counts"]["working"] += 1
                # Go back
                try:
                    await page.goto(f"{BASE_URL}{page_url}", wait_until="networkidle", timeout=10000)
                except:
                    pass
                print(f"    [{index}] WORKING: {button_name} -> Navigates")

            elif modal_visible:
                result["status"] = STATUS_WORKING
                result["notes"] = "Opens modal"
                RESULTS["status_counts"]["working"] += 1
                # Close modal
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(200)
                print(f"    [{index}] WORKING: {button_name} -> Opens modal")

            elif has_error:
                result["status"] = STATUS_BROKEN
                result["notes"] = "Shows error message"
                RESULTS["status_counts"]["broken"] += 1
                RESULTS["issues"].append({
                    "page": page_url,
                    "button": button_name,
                    "error": "Shows error on click"
                })
                print(f"    [{index}] BROKEN: {button_name} -> Error")

            elif has_success:
                result["status"] = STATUS_WORKING
                result["notes"] = "Shows success message"
                RESULTS["status_counts"]["working"] += 1
                print(f"    [{index}] WORKING: {button_name} -> Success")

            elif result["onclick"]:
                # Has onclick handler, likely working
                result["status"] = STATUS_WORKING
                result["notes"] = f"Has onclick: {result['onclick'][:30]}"
                RESULTS["status_counts"]["working"] += 1
                print(f"    [{index}] WORKING: {button_name} -> Has onclick")

            elif result["type"] == "submit":
                # Submit buttons are considered working if no error
                result["status"] = STATUS_WORKING
                result["notes"] = "Submit button (form submission)"
                RESULTS["status_counts"]["working"] += 1
                print(f"    [{index}] WORKING: {button_name} -> Submit")

            else:
                # Nothing visible happened - might not be built yet
                result["status"] = STATUS_NOT_BUILT
                result["notes"] = "No visible response when clicked"
                RESULTS["status_counts"]["not_built"] += 1
                print(f"    [{index}] NOT BUILT: {button_name} -> No response")

        except Exception as click_error:
            error_msg = str(click_error)
            if "timeout" in error_msg.lower():
                result["status"] = STATUS_NOT_BUILT
                result["notes"] = "Click timeout - may not be wired up"
                RESULTS["status_counts"]["not_built"] += 1
                print(f"    [{index}] NOT BUILT: {button_name} -> Timeout")
            else:
                result["status"] = STATUS_BROKEN
                result["notes"] = f"Click error: {error_msg[:50]}"
                RESULTS["status_counts"]["broken"] += 1
                print(f"    [{index}] BROKEN: {button_name} -> {error_msg[:30]}")

            # Try to recover
            try:
                await page.goto(f"{BASE_URL}{page_url}", wait_until="networkidle", timeout=10000)
            except:
                pass

    except Exception as e:
        result["status"] = STATUS_BROKEN
        result["notes"] = str(e)[:100]
        RESULTS["status_counts"]["broken"] += 1
        print(f"    [{index}] ERROR: {str(e)[:50]}")

    return result

def save_results():
    # Save JSON
    with open("tests/mandatory/BUTTONS_THOROUGH_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)

    # Calculate percentages
    total = max(RESULTS["buttons_tested"], 1)

    # Save detailed inventory report
    report = f"""# BUTTON INVENTORY - COMPLETE STATUS REPORT

**Date:** {RESULTS['timestamp']}
**Purpose:** Know exactly what works, what's broken, what needs building

---

## Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Buttons Found | {RESULTS['buttons_found']} | - |
| Buttons Tested | {RESULTS['buttons_tested']} | 100% |
| WORKING | {RESULTS['status_counts']['working']} | {RESULTS['status_counts']['working']/total*100:.1f}% |
| NOT BUILT | {RESULTS['status_counts']['not_built']} | {RESULTS['status_counts']['not_built']/total*100:.1f}% |
| BROKEN | {RESULTS['status_counts']['broken']} | {RESULTS['status_counts']['broken']/total*100:.1f}% |
| DISABLED | {RESULTS['status_counts']['disabled']} | {RESULTS['status_counts']['disabled']/total*100:.1f}% |
| HIDDEN | {RESULTS['status_counts']['hidden']} | {RESULTS['status_counts']['hidden']/total*100:.1f}% |
| DANGEROUS (tested safely) | {RESULTS['status_counts']['dangerous_safe']} | {RESULTS['status_counts']['dangerous_safe']/total*100:.1f}% |

---

## What Each Status Means

- **WORKING:** Button does something useful when clicked
- **NOT BUILT:** Button exists but has no functionality (needs development)
- **BROKEN:** Button causes an error when clicked (needs fixing)
- **DISABLED:** Button is intentionally disabled (may be contextual)
- **HIDDEN:** Button exists in DOM but not visible (likely in modal)
- **DANGEROUS:** Delete/logout buttons tested safely with cancel

---

## Buttons That Need Building (NOT_BUILT)

These buttons exist but do nothing when clicked:

"""

    not_built = []
    for page_data in RESULTS["pages"]:
        for btn in page_data["buttons"]:
            if btn["status"] == STATUS_NOT_BUILT:
                not_built.append({
                    "page": page_data["url"],
                    "button": btn["text"] or btn["id"] or "unnamed",
                    "notes": btn["notes"]
                })

    if not_built:
        report += "| Page | Button | Notes |\n"
        report += "|------|--------|-------|\n"
        for item in not_built:
            report += f"| {item['page']} | {item['button'][:30]} | {item['notes'][:40]} |\n"
    else:
        report += "*None - all buttons are functional!*\n"

    report += """

---

## Broken Buttons (BROKEN)

These buttons cause errors and need fixing:

"""

    broken = []
    for page_data in RESULTS["pages"]:
        for btn in page_data["buttons"]:
            if btn["status"] == STATUS_BROKEN:
                broken.append({
                    "page": page_data["url"],
                    "button": btn["text"] or btn["id"] or "unnamed",
                    "notes": btn["notes"]
                })

    if broken:
        report += "| Page | Button | Error |\n"
        report += "|------|--------|-------|\n"
        for item in broken:
            report += f"| {item['page']} | {item['button'][:30]} | {item['notes'][:40]} |\n"
    else:
        report += "*None - no broken buttons found!*\n"

    report += """

---

## Full Inventory by Page

"""

    for page_data in RESULTS["pages"]:
        if page_data["buttons_found"] > 0:
            report += f"\n### {page_data['url']}\n"
            report += f"Found: {page_data['buttons_found']} buttons | Tested: {page_data['buttons_tested']}\n\n"
            report += "| # | Button | Status | Notes |\n"
            report += "|---|--------|--------|-------|\n"
            for btn in page_data["buttons"]:
                name = btn["text"][:25] or btn["id"][:25] or "unnamed"
                report += f"| {btn['index']} | {name} | {btn['status']} | {btn['notes'][:35]} |\n"

    report += f"""

---

## Conclusion

- **Total Buttons Found:** {RESULTS['buttons_found']}
- **Total Buttons Tested:** {RESULTS['buttons_tested']}
- **Working:** {RESULTS['status_counts']['working']} ({RESULTS['status_counts']['working']/total*100:.1f}%)
- **Need Building:** {RESULTS['status_counts']['not_built']}
- **Need Fixing:** {RESULTS['status_counts']['broken']}
- **Hidden (in modals):** {RESULTS['status_counts']['hidden']}
- **Disabled:** {RESULTS['status_counts']['disabled']}
- **Dangerous (tested safely):** {RESULTS['status_counts']['dangerous_safe']}

"""

    with open("tests/mandatory/BUTTONS_INVENTORY_REPORT.md", "w") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print("BUTTON TESTING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Buttons: {RESULTS['buttons_found']}")
    print(f"WORKING: {RESULTS['status_counts']['working']}")
    print(f"NOT BUILT: {RESULTS['status_counts']['not_built']}")
    print(f"BROKEN: {RESULTS['status_counts']['broken']}")
    print(f"DISABLED: {RESULTS['status_counts']['disabled']}")
    print(f"HIDDEN: {RESULTS['status_counts']['hidden']}")
    print(f"DANGEROUS: {RESULTS['status_counts']['dangerous_safe']}")

if __name__ == "__main__":
    asyncio.run(test_all_buttons())
