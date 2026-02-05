# SINGLE TASK: TEST ALL MODALS

---

## ⚠️ PREVIOUS RUN FAILED ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   LAST RUN: Said "0 modals found"                                ║
║   REALITY: 53 custom modals exist in templates                   ║
║                                                                  ║
║   THE PROBLEM:                                                   ║
║   Script looked for Bootstrap modals (data-bs-toggle="modal")    ║
║   But this app uses CUSTOM modals with onclick="openModal()"     ║
║                                                                  ║
║   THIS TIME:                                                     ║
║   - Find ALL modals (custom pattern, not Bootstrap)              ║
║   - Open EACH one                                                ║
║   - Test that it displays correctly                              ║
║   - Test that it closes correctly                                ║
║   - Test any forms inside the modal                              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## YOUR ONE TASK

Test every modal: open it, verify it displays, close it.

---

## STEP 1: Find all modals in templates

```bash
# Find modal elements
grep -rn 'class="modal-overlay"\|class="modal"\|id=".*Modal"' templates/ | head -60

# Count them
grep -rn 'id=".*Modal"' templates/ | wc -l
```

This app uses custom modals with this pattern:
```html
<div id="someModal" class="modal-overlay">
    <div class="modal">
        <div class="modal-header">...</div>
        <div class="modal-body">...</div>
    </div>
</div>
```

Opened with: `onclick="openModal('someModal')"`
Closed with: `onclick="closeModal('someModal')"` or clicking overlay

---

## STEP 2: Find all modal triggers

```bash
# Find buttons that open modals
grep -rn "openModal\|showModal" templates/ | head -60
```

---

## STEP 3: Create the test script

Create `tests/mandatory/test_modals_thorough.py`:

```python
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5001"

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "modals_found": 0,
    "modals_tested": 0,
    "modals_opened": 0,
    "modals_closed": 0,
    "modals_with_forms": 0,
    "status_counts": {
        "working": 0,
        "broken": 0,
        "no_trigger": 0,
    },
    "pages": [],
    "issues": []
}

# Known modals from templates (from grep results)
KNOWN_MODALS = [
    {"page": "/dashboard/calendar", "modal_id": "deadlineModal", "trigger": "openModal('deadlineModal')"},
    {"page": "/dashboard/contacts", "modal_id": "contactModal", "trigger": "openModal('contactModal')"},
    {"page": "/dashboard/contacts", "modal_id": "notesModal", "trigger": "openModal('notesModal')"},
    {"page": "/dashboard/contacts", "modal_id": "taskModal", "trigger": "openModal('taskModal')"},
    {"page": "/dashboard/contacts", "modal_id": "docsModal", "trigger": "openModal('docsModal')"},
    {"page": "/dashboard/affiliates", "modal_id": "addAffiliateModal", "trigger": "openModal('addAffiliateModal')"},
    {"page": "/dashboard/settlements", "modal_id": "settlementModal", "trigger": "openModal('settlementModal')"},
    {"page": "/dashboard/settlements", "modal_id": "offerModal", "trigger": "openModal('offerModal')"},
    {"page": "/dashboard/settlements", "modal_id": "settleModal", "trigger": "openModal('settleModal')"},
    {"page": "/dashboard/settlements", "modal_id": "paymentModal", "trigger": "openModal('paymentModal')"},
    {"page": "/dashboard/documents", "modal_id": "uploadModal", "trigger": "openModal('uploadModal')"},
    {"page": "/dashboard/staff", "modal_id": "addModal", "trigger": "openModal('addModal')"},
    {"page": "/dashboard/staff", "modal_id": "editModal", "trigger": "openModal('editModal')"},
    {"page": "/dashboard/furnishers", "modal_id": "addModal", "trigger": "openModal('addModal')"},
    {"page": "/dashboard/case-law", "modal_id": "viewModal", "trigger": "openModal('viewModal')"},
    {"page": "/dashboard/case-law", "modal_id": "addModal", "trigger": "openModal('addModal')"},
    {"page": "/dashboard/letter-queue", "modal_id": "dismissModal", "trigger": "openModal('dismissModal')"},
    {"page": "/dashboard/triage", "modal_id": "reviewModal", "trigger": "openModal('reviewModal')"},
    {"page": "/dashboard/suspense-accounts", "modal_id": "uploadModal", "trigger": "openModal('uploadModal')"},
    {"page": "/dashboard/suspense-accounts", "modal_id": "analyzeModal", "trigger": "openModal('analyzeModal')"},
    {"page": "/dashboard/suspense-accounts", "modal_id": "detailModal", "trigger": "openModal('detailModal')"},
    {"page": "/dashboard/billing", "modal_id": "createPlanModal", "trigger": "openModal('createPlanModal')"},
    {"page": "/dashboard/frivolousness", "modal_id": "addModal", "trigger": "openModal('addModal')"},
    {"page": "/dashboard/frivolousness", "modal_id": "viewModal", "trigger": "openModal('viewModal')"},
    {"page": "/dashboard/ml-insights", "modal_id": "recordOutcomeModal", "trigger": "openModal('recordOutcomeModal')"},
    {"page": "/dashboard/specialty-bureaus", "modal_id": "disputeModal", "trigger": "openModal('disputeModal')"},
    {"page": "/dashboard/franchise", "modal_id": "createOrgModal", "trigger": "openModal('createOrgModal')"},
    {"page": "/dashboard/franchise", "modal_id": "editOrgModal", "trigger": "openModal('editOrgModal')"},
    {"page": "/dashboard/franchise", "modal_id": "membersModal", "trigger": "openModal('membersModal')"},
    {"page": "/dashboard/franchise", "modal_id": "consolidatedReportModal", "trigger": "openModal('consolidatedReportModal')"},
    {"page": "/dashboard/franchise", "modal_id": "transferModal", "trigger": "openModal('transferModal')"},
    {"page": "/dashboard/integrations", "modal_id": "configModal", "trigger": "openModal('configModal')"},
    {"page": "/dashboard/white-label", "modal_id": "tenantModal", "trigger": "openModal('tenantModal')"},
    {"page": "/dashboard/white-label", "modal_id": "usersModal", "trigger": "openModal('usersModal')"},
    {"page": "/dashboard/white-label", "modal_id": "statsModal", "trigger": "openModal('statsModal')"},
    {"page": "/dashboard/patterns", "modal_id": "createModal", "trigger": "openModal('createModal')"},
    {"page": "/dashboard/patterns", "modal_id": "detailModal", "trigger": "openModal('detailModal')"},
    {"page": "/dashboard/patterns", "modal_id": "addViolationModal", "trigger": "openModal('addViolationModal')"},
    {"page": "/dashboard/chexsystems", "modal_id": "newDisputeModal", "trigger": "openModal('newDisputeModal')"},
    {"page": "/dashboard/sops", "modal_id": "sopModal", "trigger": "openModal('sopModal')"},
    {"page": "/dashboard/performance", "modal_id": "clearCacheModal", "trigger": "openModal('clearCacheModal')"},
    {"page": "/dashboard/credit-import", "modal_id": "credentialModal", "trigger": "openModal('credentialModal')"},
]

async def test_all_modals():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # First, scan all pages to find modals dynamically
        await scan_for_modals(page)

        # Then test each known modal
        for modal_info in KNOWN_MODALS:
            await test_single_modal(page, modal_info)

        await browser.close()

    save_results()

async def scan_for_modals(page):
    """Scan pages to find all modal elements"""

    pages_to_scan = [
        "/dashboard",
        "/dashboard/clients",
        "/dashboard/contacts",
        "/dashboard/calendar",
        "/dashboard/settlements",
        "/dashboard/staff",
        "/dashboard/documents",
        "/dashboard/affiliates",
        "/dashboard/case-law",
        "/dashboard/letter-queue",
        "/dashboard/triage",
        "/dashboard/suspense-accounts",
        "/dashboard/billing",
        "/dashboard/frivolousness",
        "/dashboard/ml-insights",
        "/dashboard/specialty-bureaus",
        "/dashboard/franchise",
        "/dashboard/integrations",
        "/dashboard/white-label",
        "/dashboard/patterns",
        "/dashboard/chexsystems",
        "/dashboard/sops",
        "/dashboard/performance",
        "/dashboard/credit-import",
        "/dashboard/furnishers",
    ]

    print("Scanning for modals...")

    for url in pages_to_scan:
        try:
            await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=15000)

            # Find modal elements
            modals = await page.query_selector_all("[id*='Modal'], .modal-overlay, [class*='modal']")

            if modals:
                print(f"  {url}: Found {len(modals)} modal elements")
                RESULTS["modals_found"] += len(modals)

        except Exception as e:
            print(f"  {url}: Error - {str(e)[:50]}")

async def test_single_modal(page, modal_info):
    """Test a single modal: open, verify, close"""

    url = modal_info["page"]
    modal_id = modal_info["modal_id"]

    print(f"\n{'='*60}")
    print(f"Testing Modal: {modal_id} on {url}")
    print(f"{'='*60}")

    result = {
        "page": url,
        "modal_id": modal_id,
        "status": "",
        "opened": False,
        "closed": False,
        "has_form": False,
        "notes": ""
    }

    try:
        await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=15000)

        # Check if modal element exists
        modal = await page.query_selector(f"#{modal_id}")

        if not modal:
            result["status"] = "NOT_FOUND"
            result["notes"] = "Modal element not found in DOM"
            RESULTS["status_counts"]["broken"] += 1
            print(f"  ❌ Modal element not found")
            RESULTS["pages"].append(result)
            return

        # Try to open the modal using JavaScript
        try:
            await page.evaluate(f"openModal('{modal_id}')")
            await page.wait_for_timeout(500)

            # Check if modal is now visible
            is_visible = await page.evaluate(f"""() => {{
                const modal = document.getElementById('{modal_id}');
                if (!modal) return false;
                const style = window.getComputedStyle(modal);
                return style.display !== 'none' && style.visibility !== 'hidden';
            }}""")

            if is_visible:
                result["opened"] = True
                RESULTS["modals_opened"] += 1
                print(f"  ✅ Modal opened successfully")

                # Check for form inside modal
                form = await modal.query_selector("form")
                if form:
                    result["has_form"] = True
                    RESULTS["modals_with_forms"] += 1
                    print(f"  📝 Modal contains a form")

                # Try to close the modal
                try:
                    await page.evaluate(f"closeModal('{modal_id}')")
                    await page.wait_for_timeout(300)

                    # Verify closed
                    is_still_visible = await page.evaluate(f"""() => {{
                        const modal = document.getElementById('{modal_id}');
                        if (!modal) return false;
                        const style = window.getComputedStyle(modal);
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    }}""")

                    if not is_still_visible:
                        result["closed"] = True
                        RESULTS["modals_closed"] += 1
                        print(f"  ✅ Modal closed successfully")
                        result["status"] = "WORKING"
                        RESULTS["status_counts"]["working"] += 1
                    else:
                        result["notes"] = "Modal did not close"
                        result["status"] = "CLOSE_FAILED"
                        RESULTS["status_counts"]["broken"] += 1
                        print(f"  ⚠️ Modal did not close")

                except Exception as close_error:
                    result["notes"] = f"Close error: {str(close_error)[:50]}"
                    result["status"] = "CLOSE_ERROR"
                    RESULTS["status_counts"]["broken"] += 1
                    print(f"  ❌ Error closing modal")
                    # Try Escape key
                    await page.keyboard.press("Escape")

            else:
                result["status"] = "OPEN_FAILED"
                result["notes"] = "openModal() called but modal not visible"
                RESULTS["status_counts"]["broken"] += 1
                print(f"  ❌ Modal did not open")

        except Exception as open_error:
            # openModal function might not exist
            result["status"] = "NO_FUNCTION"
            result["notes"] = f"openModal() error: {str(open_error)[:50]}"
            RESULTS["status_counts"]["no_trigger"] += 1
            print(f"  ⚠️ openModal() function error")

    except Exception as e:
        result["status"] = "PAGE_ERROR"
        result["notes"] = str(e)[:100]
        RESULTS["status_counts"]["broken"] += 1
        print(f"  ❌ Error: {str(e)[:50]}")

    RESULTS["modals_tested"] += 1
    RESULTS["pages"].append(result)

def save_results():
    # Save JSON
    with open("tests/mandatory/MODALS_THOROUGH_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)

    # Generate report
    total = RESULTS["modals_tested"] or 1

    report = f"""# MODAL TESTING - COMPLETE INVENTORY

**Date:** {RESULTS['timestamp']}
**Purpose:** Verify all modals open and close correctly

---

## Summary

| Metric | Count |
|--------|-------|
| Modals Found (scan) | {RESULTS['modals_found']} |
| Modals Tested | {RESULTS['modals_tested']} |
| Modals Opened | {RESULTS['modals_opened']} |
| Modals Closed | {RESULTS['modals_closed']} |
| Modals with Forms | {RESULTS['modals_with_forms']} |

## Status Breakdown

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Working | {RESULTS['status_counts']['working']} | {RESULTS['status_counts']['working']/total*100:.1f}% |
| ❌ Broken | {RESULTS['status_counts']['broken']} | {RESULTS['status_counts']['broken']/total*100:.1f}% |
| ⚠️ No Trigger | {RESULTS['status_counts']['no_trigger']} | {RESULTS['status_counts']['no_trigger']/total*100:.1f}% |

---

## Modal Details

| Page | Modal ID | Opened | Closed | Has Form | Status |
|------|----------|--------|--------|----------|--------|
"""

    for modal in RESULTS["pages"]:
        opened = "✅" if modal["opened"] else "❌"
        closed = "✅" if modal["closed"] else "❌"
        has_form = "📝" if modal["has_form"] else "-"
        report += f"| {modal['page']} | {modal['modal_id']} | {opened} | {closed} | {has_form} | {modal['status']} |\n"

    # Issues section
    issues = [m for m in RESULTS["pages"] if m["status"] != "WORKING"]

    if issues:
        report += """

---

## Issues Found

| Page | Modal | Issue |
|------|-------|-------|
"""
        for issue in issues:
            report += f"| {issue['page']} | {issue['modal_id']} | {issue['notes']} |\n"

    report += f"""

---

## Conclusion

- **Working Modals:** {RESULTS['status_counts']['working']}/{total} ({RESULTS['status_counts']['working']/total*100:.1f}%)
- **Modals with Forms:** {RESULTS['modals_with_forms']}
- **Issues to Fix:** {len(issues)}

"""

    with open("tests/mandatory/MODALS_INVENTORY_REPORT.md", "w") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print("MODAL TESTING COMPLETE")
    print(f"{'='*60}")
    print(f"Tested: {RESULTS['modals_tested']}")
    print(f"✅ Working: {RESULTS['status_counts']['working']}")
    print(f"❌ Broken: {RESULTS['status_counts']['broken']}")
    print(f"⚠️ No Trigger: {RESULTS['status_counts']['no_trigger']}")

if __name__ == "__main__":
    asyncio.run(test_all_modals())
```

---

## STEP 4: Run the tests

```bash
# Make sure app is running
CI=true python app.py &
sleep 5

# Run modal tests
python tests/mandatory/test_modals_thorough.py
```

---

## STEP 5: Check results

```bash
cat tests/mandatory/MODALS_INVENTORY_REPORT.md
```

---

## STEP 6: The report must show

For EVERY modal:
- Page it's on
- Modal ID
- Whether it opened ✅/❌
- Whether it closed ✅/❌
- Whether it has a form
- Status (Working / Broken / No Trigger)

---

## ⚠️ RULES ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. Use the CUSTOM modal pattern (openModal/closeModal)         ║
║   2. NOT Bootstrap (data-bs-toggle)                              ║
║   3. Test EVERY modal in the KNOWN_MODALS list                   ║
║   4. Also scan pages to find any we missed                       ║
║   5. Report exactly what works and what doesn't                  ║
║                                                                  ║
║   THIS IS YOUR ONLY TASK.                                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**TEST ALL MODALS. OPEN AND CLOSE EACH ONE. NO SHORTCUTS.**
