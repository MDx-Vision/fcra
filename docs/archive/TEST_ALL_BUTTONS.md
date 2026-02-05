# SINGLE TASK: TEST ALL BUTTONS AND CREATE STATUS INVENTORY

---

## ⚠️ PREVIOUS RUN FAILED ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   LAST RUN: Found 867 buttons but only clicked 66                ║
║                                                                  ║
║   THIS IS NOT ACCEPTABLE.                                        ║
║                                                                  ║
║   THIS TIME:                                                     ║
║   - Find ALL buttons (actual <button> elements, not CSS)         ║
║   - Click EVERY one (or document why you couldn't)               ║
║   - Create inventory showing status of EACH button               ║
║   - Edgar needs to know what works and what needs building       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## YOUR ONE TASK

Test every button and create a complete inventory showing what works, what's broken, and what needs building.

---

## STEP 1: Count actual buttons in templates

```bash
grep -rn "<button" templates/ | wc -l
```

This is your target. Write it down.

---

## STEP 2: Create the test script

Create `tests/mandatory/test_buttons_thorough.py`:

```python
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
STATUS_WORKING = "✅ Working"
STATUS_NOT_BUILT = "🔨 Not Built"
STATUS_BROKEN = "❌ Broken"
STATUS_DISABLED = "⚠️ Disabled"
STATUS_HIDDEN = "👻 Hidden"
STATUS_DANGEROUS = "🔒 Dangerous (tested safely)"

async def test_all_buttons():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # All pages to test
        pages_to_test = [
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
            "/dashboard/suspense-accounts",
        ]

        for url in pages_to_test:
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
    except Exception as e:
        print(f"  ERROR loading page: {e}")
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
        "status": "",
        "notes": ""
    }

    try:
        # Get button info
        result["text"] = (await button.inner_text() or "").strip()[:50]
        result["id"] = await button.get_attribute("id") or ""
        result["class"] = (await button.get_attribute("class") or "")[:50]
        result["type"] = await button.get_attribute("type") or "button"

        # Check visibility
        is_visible = await button.is_visible()
        if not is_visible:
            result["status"] = STATUS_HIDDEN
            result["notes"] = "Button not visible on page"
            RESULTS["status_counts"]["hidden"] += 1
            print(f"    [{index}] 👻 HIDDEN: {result['text'][:30] or result['id'] or 'unnamed'}")
            return result

        # Check if enabled
        is_enabled = await button.is_enabled()
        if not is_enabled:
            result["status"] = STATUS_DISABLED
            result["notes"] = "Button is disabled"
            RESULTS["status_counts"]["disabled"] += 1
            print(f"    [{index}] ⚠️ DISABLED: {result['text'][:30] or result['id'] or 'unnamed'}")
            return result

        # Check if dangerous (delete, remove, logout, etc.)
        text_lower = result["text"].lower()
        dangerous_keywords = ["delete", "remove", "logout", "sign out", "cancel subscription", "deactivate", "destroy"]
        is_dangerous = any(kw in text_lower for kw in dangerous_keywords)

        # Store current URL to detect navigation
        current_url = page.url

        # Click the button
        try:
            await button.click(timeout=3000)
            await page.wait_for_timeout(500)

            # Check what happened
            new_url = page.url

            # Check for modal
            modal = await page.query_selector(".modal.show, .modal-overlay:not([style*='display: none']), [class*='modal']:not([style*='display: none'])")

            # Check for error
            error = await page.query_selector(".error, .alert-danger, .alert-error, [class*='error']:not(input)")

            # Check for success
            success = await page.query_selector(".success, .alert-success, [class*='success']")

            if is_dangerous:
                # Handle dangerous button - try to cancel
                result["status"] = STATUS_DANGEROUS
                RESULTS["status_counts"]["dangerous_safe"] += 1

                # Try to close any dialog
                cancel = await page.query_selector("button:has-text('Cancel'), button:has-text('No'), button:has-text('Close'), .btn-secondary, [data-dismiss], [data-bs-dismiss]")
                if cancel:
                    try:
                        await cancel.click()
                        await page.wait_for_timeout(300)
                    except:
                        pass
                await page.keyboard.press("Escape")
                result["notes"] = "Clicked and cancelled safely"
                print(f"    [{index}] 🔒 DANGEROUS (safe): {result['text'][:30]}")

            elif modal:
                result["status"] = STATUS_WORKING
                result["notes"] = "Opens modal"
                RESULTS["status_counts"]["working"] += 1
                # Close modal
                close = await modal.query_selector("button:has-text('Close'), button:has-text('Cancel'), .btn-close, .close, [data-dismiss], [data-bs-dismiss]")
                if close:
                    try:
                        await close.click()
                        await page.wait_for_timeout(300)
                    except:
                        pass
                await page.keyboard.press("Escape")
                print(f"    [{index}] ✅ WORKING: {result['text'][:30]} -> Opens modal")

            elif new_url != current_url:
                result["status"] = STATUS_WORKING
                result["notes"] = f"Navigates to {new_url}"
                RESULTS["status_counts"]["working"] += 1
                # Go back
                await page.goto(f"{BASE_URL}{page_url}", wait_until="networkidle", timeout=10000)
                print(f"    [{index}] ✅ WORKING: {result['text'][:30]} -> Navigates")

            elif error:
                error_text = await error.inner_text()
                result["status"] = STATUS_BROKEN
                result["notes"] = f"Error: {error_text[:50]}"
                RESULTS["status_counts"]["broken"] += 1
                RESULTS["issues"].append({
                    "page": page_url,
                    "button": result["text"] or result["id"],
                    "error": error_text[:100]
                })
                print(f"    [{index}] ❌ BROKEN: {result['text'][:30]} -> Error")

            elif success:
                result["status"] = STATUS_WORKING
                result["notes"] = "Shows success message"
                RESULTS["status_counts"]["working"] += 1
                print(f"    [{index}] ✅ WORKING: {result['text'][:30]} -> Success")

            else:
                # Nothing visible happened - might not be built yet
                result["status"] = STATUS_NOT_BUILT
                result["notes"] = "No visible response"
                RESULTS["status_counts"]["not_built"] += 1
                print(f"    [{index}] 🔨 NOT BUILT: {result['text'][:30]} -> No response")

        except Exception as click_error:
            error_msg = str(click_error)
            if "timeout" in error_msg.lower():
                result["status"] = STATUS_NOT_BUILT
                result["notes"] = "Click timeout - may not be wired up"
                RESULTS["status_counts"]["not_built"] += 1
                print(f"    [{index}] 🔨 NOT BUILT: {result['text'][:30]} -> Timeout")
            else:
                result["status"] = STATUS_BROKEN
                result["notes"] = f"Click error: {error_msg[:50]}"
                RESULTS["status_counts"]["broken"] += 1
                print(f"    [{index}] ❌ BROKEN: {result['text'][:30]} -> Error")

            # Try to recover
            try:
                await page.goto(f"{BASE_URL}{page_url}", wait_until="networkidle", timeout=10000)
            except:
                pass

    except Exception as e:
        result["status"] = STATUS_BROKEN
        result["notes"] = str(e)[:100]
        RESULTS["status_counts"]["broken"] += 1
        print(f"    [{index}] ❌ ERROR: {str(e)[:50]}")

    return result

def save_results():
    # Save JSON
    with open("tests/mandatory/BUTTONS_THOROUGH_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)

    # Calculate percentages
    total = RESULTS["buttons_tested"]
    if total == 0:
        total = 1  # Avoid division by zero

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
| ✅ Working | {RESULTS['status_counts']['working']} | {RESULTS['status_counts']['working']/total*100:.1f}% |
| 🔨 Not Built Yet | {RESULTS['status_counts']['not_built']} | {RESULTS['status_counts']['not_built']/total*100:.1f}% |
| ❌ Broken | {RESULTS['status_counts']['broken']} | {RESULTS['status_counts']['broken']/total*100:.1f}% |
| ⚠️ Disabled | {RESULTS['status_counts']['disabled']} | {RESULTS['status_counts']['disabled']/total*100:.1f}% |
| 👻 Hidden | {RESULTS['status_counts']['hidden']} | {RESULTS['status_counts']['hidden']/total*100:.1f}% |
| 🔒 Dangerous (tested safely) | {RESULTS['status_counts']['dangerous_safe']} | {RESULTS['status_counts']['dangerous_safe']/total*100:.1f}% |

---

## What This Means

- **✅ Working:** Button does something useful when clicked
- **🔨 Not Built Yet:** Button exists but has no functionality (needs development)
- **❌ Broken:** Button causes an error when clicked (needs fixing)
- **⚠️ Disabled:** Button is intentionally disabled (may be contextual)
- **👻 Hidden:** Button exists in DOM but not visible (may be in modal)
- **🔒 Dangerous:** Delete/logout buttons tested safely with cancel

---

## Buttons That Need Building (🔨)

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
            report += f"| {item['page']} | {item['button']} | {item['notes']} |\n"
    else:
        report += "*None - all buttons are functional!*\n"

    report += """

---

## Broken Buttons (❌)

These buttons cause errors and need fixing:

"""

    if RESULTS["issues"]:
        report += "| Page | Button | Error |\n"
        report += "|------|--------|-------|\n"
        for issue in RESULTS["issues"]:
            report += f"| {issue['page']} | {issue['button']} | {issue['error'][:50]} |\n"
    else:
        report += "*None - no broken buttons found!*\n"

    report += """

---

## Full Inventory by Page

"""

    for page_data in RESULTS["pages"]:
        if page_data["buttons_found"] > 0:
            report += f"\n### {page_data['url']}\n"
            report += f"Found: {page_data['buttons_found']} buttons\n\n"
            report += "| # | Button | Status | Notes |\n"
            report += "|---|--------|--------|-------|\n"
            for btn in page_data["buttons"]:
                name = btn["text"][:25] or btn["id"][:25] or "unnamed"
                report += f"| {btn['index']} | {name} | {btn['status']} | {btn['notes'][:30]} |\n"

    report += f"""

---

## Conclusion

- **Total Buttons:** {RESULTS['buttons_found']}
- **Working:** {RESULTS['status_counts']['working']} ({RESULTS['status_counts']['working']/total*100:.1f}%)
- **Need Building:** {RESULTS['status_counts']['not_built']}
- **Need Fixing:** {RESULTS['status_counts']['broken']}

"""

    with open("tests/mandatory/BUTTONS_INVENTORY_REPORT.md", "w") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print("BUTTON TESTING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Buttons: {RESULTS['buttons_found']}")
    print(f"✅ Working: {RESULTS['status_counts']['working']}")
    print(f"🔨 Not Built: {RESULTS['status_counts']['not_built']}")
    print(f"❌ Broken: {RESULTS['status_counts']['broken']}")
    print(f"⚠️ Disabled: {RESULTS['status_counts']['disabled']}")
    print(f"👻 Hidden: {RESULTS['status_counts']['hidden']}")
    print(f"🔒 Dangerous: {RESULTS['status_counts']['dangerous_safe']}")

if __name__ == "__main__":
    asyncio.run(test_all_buttons())
```

---

## STEP 3: Run the tests

```bash
# Make sure app is running
CI=true python app.py &
sleep 5

# Run button tests
python tests/mandatory/test_buttons_thorough.py
```

---

## STEP 4: Check results

```bash
cat tests/mandatory/BUTTONS_INVENTORY_REPORT.md
```

---

## STEP 5: The report must show

For EVERY button:
- What page it's on
- What it's called
- Status (Working / Not Built / Broken / Disabled / Hidden / Dangerous)
- Notes on what happened

Edgar will use this to:
1. See what features work
2. Know what needs building
3. Find bugs to fix

---

## ⚠️ RULES ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. Test EVERY button, not just some                            ║
║   2. Click each one (handle dangerous ones safely)               ║
║   3. Categorize: Working / Not Built / Broken / Disabled / Hidden║
║   4. Create complete inventory report                            ║
║   5. Do not skip any buttons                                     ║
║                                                                  ║
║   THIS IS YOUR ONLY TASK.                                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**TEST ALL BUTTONS. CREATE COMPLETE INVENTORY. NO SHORTCUTS.**
