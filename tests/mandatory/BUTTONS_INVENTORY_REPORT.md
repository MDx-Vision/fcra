# BUTTON INVENTORY - COMPLETE STATUS REPORT

**Date:** 2025-12-29T08:50:22.148059
**Purpose:** Know exactly what works, what's broken, what needs building

---

## Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Buttons Found | 1691 | - |
| Buttons Tested | 1691 | 100% |
| WORKING | 79 | 4.7% |
| NOT BUILT | 14 | 0.8% |
| BROKEN | 368 | 21.8% |
| DISABLED | 2 | 0.1% |
| HIDDEN | 1227 | 72.6% |
| DANGEROUS (tested safely) | 1 | 0.1% |

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

| Page | Button | Notes |
|------|--------|-------|
| /dashboard | New Client | Click timeout - may not be wired up |
| /dashboard/settlements | + Offer | Click timeout - may not be wired up |
| /dashboard/contacts | ADD CONTACT | Click timeout - may not be wired up |
| /dashboard/documents | Review | Click timeout - may not be wired up |
| /dashboard/integrations | Test Connection | Click timeout - may not be wired up |
| /dashboard/billing | Initialize Default Plans | Click timeout - may not be wired up |
| /dashboard/tasks | New Task | Click timeout - may not be wired up |
| /dashboard/white-label | unnamed | Click timeout - may not be wired up |
| /dashboard/franchise | Create Organization | Click timeout - may not be wired up |
| /dashboard/affiliates | All | Click timeout - may not be wired up |
| /dashboard/case-law | Copy Short | Click timeout - may not be wired up |
| /dashboard/chexsystems | Create First Dispute | Click timeout - may not be wired up |
| /dashboard/specialty-bureaus | View Disputes | Click timeout - may not be wired up |
| /dashboard/patterns | Create First Pattern | Click timeout - may not be wired up |


---

## Broken Buttons (BROKEN)

These buttons cause errors and need fixing:

| Page | Button | Error |
|------|--------|-------|
| /signup | Continue to Credit Access | Shows error message |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settlements | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/documents | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settings | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/integrations | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/integrations | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/integrations | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/integrations | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/integrations | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/integrations | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/integrations | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/integrations | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/integrations | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/billing | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/tasks | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/workflows | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/white-label | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/franchise | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/affiliates | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/triage | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/triage | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/triage | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/triage | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/triage | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/triage | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/triage | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/case-law | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/chexsystems | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/chexsystems | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/chexsystems | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/specialty-bureaus | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/patterns | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/sol | Check Deadlines | Click error: Page.evaluate: Execution co |
| /dashboard/sol | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/sol | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/sol | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/sol | unnamed | ElementHandle.inner_text: Execution cont |
| /dashboard/settings/sms | unnamed | ElementHandle.inner_text: Execution cont |


---

## Full Inventory by Page


### /
Found: 1 buttons | Tested: 1

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | 🚀 ANALYZE | WORKING | Submit button (form submission) |

### /signup
Found: 7 buttons | Tested: 7

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Continue to Credit Access | BROKEN | Shows error message |
| 1 | Back | HIDDEN | Button not visible on page (likely  |
| 2 | Continue to Plan Selectio | HIDDEN | Button not visible on page (likely  |
| 3 | Back | HIDDEN | Button not visible on page (likely  |
| 4 | Continue to Agreement | HIDDEN | Button not visible on page (likely  |
| 5 | Back | HIDDEN | Button not visible on page (likely  |
| 6 | Proceed to Payment | HIDDEN | Button not visible on page (likely  |

### /portal/login
Found: 5 buttons | Tested: 5

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | 👁 | WORKING | Has onclick: togglePassword() |
| 1 | Sign In | WORKING | Submit button (form submission) |
| 2 | Send Reset Link | HIDDEN | Button not visible on page (likely  |
| 3 | 👁 | HIDDEN | Button not visible on page (likely  |
| 4 | Reset Password | HIDDEN | Button not visible on page (likely  |

### /dashboard
Found: 52 buttons | Tested: 52

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Batch Upload | WORKING | Opens modal |
| 1 | New Client | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 18 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 19 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 20 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 21 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 22 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 23 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 24 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 25 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 26 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 27 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 28 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 29 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 30 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 31 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 32 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 33 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 34 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 35 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 36 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 37 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 38 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 39 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 40 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 41 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 42 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 43 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 44 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 45 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 46 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 47 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 48 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 49 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 50 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 51 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/clients
Found: 568 buttons | Tested: 568

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Apply | HIDDEN | Button not visible on page (likely  |
| 1 | Delete Selected | HIDDEN | Button not visible on page (likely  |
| 2 | ALL | WORKING | Has onclick: quickFilter('all') |
| 3 | ACTIVE | WORKING | Has onclick: quickFilter('active') |
| 4 | LEADS | WORKING | Has onclick: quickFilter('leads') |
| 5 | FOLLOW UP | WORKING | Has onclick: quickFilter('followup' |
| 6 | SIGNUPS | WORKING | Has onclick: quickFilter('signups') |
| 7 | Signup | HIDDEN | Button not visible on page (likely  |
| 8 | Active | HIDDEN | Button not visible on page (likely  |
| 9 | Paused | HIDDEN | Button not visible on page (likely  |
| 10 | Complete | HIDDEN | Button not visible on page (likely  |
| 11 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 12 | unnamed | HIDDEN | Button not visible on page (likely  |
| 13 | unnamed | HIDDEN | Button not visible on page (likely  |
| 14 | Signup | HIDDEN | Button not visible on page (likely  |
| 15 | Active | HIDDEN | Button not visible on page (likely  |
| 16 | Paused | HIDDEN | Button not visible on page (likely  |
| 17 | Complete | HIDDEN | Button not visible on page (likely  |
| 18 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 19 | unnamed | HIDDEN | Button not visible on page (likely  |
| 20 | unnamed | HIDDEN | Button not visible on page (likely  |
| 21 | Signup | HIDDEN | Button not visible on page (likely  |
| 22 | Active | HIDDEN | Button not visible on page (likely  |
| 23 | Paused | HIDDEN | Button not visible on page (likely  |
| 24 | Complete | HIDDEN | Button not visible on page (likely  |
| 25 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 26 | unnamed | HIDDEN | Button not visible on page (likely  |
| 27 | unnamed | HIDDEN | Button not visible on page (likely  |
| 28 | Signup | HIDDEN | Button not visible on page (likely  |
| 29 | Active | HIDDEN | Button not visible on page (likely  |
| 30 | Paused | HIDDEN | Button not visible on page (likely  |
| 31 | Complete | HIDDEN | Button not visible on page (likely  |
| 32 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 33 | unnamed | HIDDEN | Button not visible on page (likely  |
| 34 | unnamed | HIDDEN | Button not visible on page (likely  |
| 35 | Signup | HIDDEN | Button not visible on page (likely  |
| 36 | Active | HIDDEN | Button not visible on page (likely  |
| 37 | Paused | HIDDEN | Button not visible on page (likely  |
| 38 | Complete | HIDDEN | Button not visible on page (likely  |
| 39 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 40 | unnamed | HIDDEN | Button not visible on page (likely  |
| 41 | unnamed | HIDDEN | Button not visible on page (likely  |
| 42 | Signup | HIDDEN | Button not visible on page (likely  |
| 43 | Active | HIDDEN | Button not visible on page (likely  |
| 44 | Paused | HIDDEN | Button not visible on page (likely  |
| 45 | Complete | HIDDEN | Button not visible on page (likely  |
| 46 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 47 | unnamed | HIDDEN | Button not visible on page (likely  |
| 48 | unnamed | HIDDEN | Button not visible on page (likely  |
| 49 | Signup | HIDDEN | Button not visible on page (likely  |
| 50 | Active | HIDDEN | Button not visible on page (likely  |
| 51 | Paused | HIDDEN | Button not visible on page (likely  |
| 52 | Complete | HIDDEN | Button not visible on page (likely  |
| 53 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 54 | unnamed | HIDDEN | Button not visible on page (likely  |
| 55 | unnamed | HIDDEN | Button not visible on page (likely  |
| 56 | Signup | HIDDEN | Button not visible on page (likely  |
| 57 | Active | HIDDEN | Button not visible on page (likely  |
| 58 | Paused | HIDDEN | Button not visible on page (likely  |
| 59 | Complete | HIDDEN | Button not visible on page (likely  |
| 60 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 61 | unnamed | HIDDEN | Button not visible on page (likely  |
| 62 | unnamed | HIDDEN | Button not visible on page (likely  |
| 63 | Signup | HIDDEN | Button not visible on page (likely  |
| 64 | Active | HIDDEN | Button not visible on page (likely  |
| 65 | Paused | HIDDEN | Button not visible on page (likely  |
| 66 | Complete | HIDDEN | Button not visible on page (likely  |
| 67 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 68 | unnamed | HIDDEN | Button not visible on page (likely  |
| 69 | unnamed | HIDDEN | Button not visible on page (likely  |
| 70 | Signup | HIDDEN | Button not visible on page (likely  |
| 71 | Active | HIDDEN | Button not visible on page (likely  |
| 72 | Paused | HIDDEN | Button not visible on page (likely  |
| 73 | Complete | HIDDEN | Button not visible on page (likely  |
| 74 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 75 | unnamed | HIDDEN | Button not visible on page (likely  |
| 76 | unnamed | HIDDEN | Button not visible on page (likely  |
| 77 | Signup | HIDDEN | Button not visible on page (likely  |
| 78 | Active | HIDDEN | Button not visible on page (likely  |
| 79 | Paused | HIDDEN | Button not visible on page (likely  |
| 80 | Complete | HIDDEN | Button not visible on page (likely  |
| 81 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 82 | unnamed | HIDDEN | Button not visible on page (likely  |
| 83 | unnamed | HIDDEN | Button not visible on page (likely  |
| 84 | Signup | HIDDEN | Button not visible on page (likely  |
| 85 | Active | HIDDEN | Button not visible on page (likely  |
| 86 | Paused | HIDDEN | Button not visible on page (likely  |
| 87 | Complete | HIDDEN | Button not visible on page (likely  |
| 88 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 89 | unnamed | HIDDEN | Button not visible on page (likely  |
| 90 | unnamed | HIDDEN | Button not visible on page (likely  |
| 91 | Signup | HIDDEN | Button not visible on page (likely  |
| 92 | Active | HIDDEN | Button not visible on page (likely  |
| 93 | Paused | HIDDEN | Button not visible on page (likely  |
| 94 | Complete | HIDDEN | Button not visible on page (likely  |
| 95 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 96 | unnamed | HIDDEN | Button not visible on page (likely  |
| 97 | unnamed | HIDDEN | Button not visible on page (likely  |
| 98 | Signup | HIDDEN | Button not visible on page (likely  |
| 99 | Active | HIDDEN | Button not visible on page (likely  |
| 100 | Paused | HIDDEN | Button not visible on page (likely  |
| 101 | Complete | HIDDEN | Button not visible on page (likely  |
| 102 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 103 | unnamed | HIDDEN | Button not visible on page (likely  |
| 104 | unnamed | HIDDEN | Button not visible on page (likely  |
| 105 | Signup | HIDDEN | Button not visible on page (likely  |
| 106 | Active | HIDDEN | Button not visible on page (likely  |
| 107 | Paused | HIDDEN | Button not visible on page (likely  |
| 108 | Complete | HIDDEN | Button not visible on page (likely  |
| 109 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 110 | unnamed | HIDDEN | Button not visible on page (likely  |
| 111 | unnamed | HIDDEN | Button not visible on page (likely  |
| 112 | Signup | HIDDEN | Button not visible on page (likely  |
| 113 | Active | HIDDEN | Button not visible on page (likely  |
| 114 | Paused | HIDDEN | Button not visible on page (likely  |
| 115 | Complete | HIDDEN | Button not visible on page (likely  |
| 116 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 117 | unnamed | HIDDEN | Button not visible on page (likely  |
| 118 | unnamed | HIDDEN | Button not visible on page (likely  |
| 119 | Signup | HIDDEN | Button not visible on page (likely  |
| 120 | Active | HIDDEN | Button not visible on page (likely  |
| 121 | Paused | HIDDEN | Button not visible on page (likely  |
| 122 | Complete | HIDDEN | Button not visible on page (likely  |
| 123 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 124 | unnamed | HIDDEN | Button not visible on page (likely  |
| 125 | unnamed | HIDDEN | Button not visible on page (likely  |
| 126 | Signup | HIDDEN | Button not visible on page (likely  |
| 127 | Active | HIDDEN | Button not visible on page (likely  |
| 128 | Paused | HIDDEN | Button not visible on page (likely  |
| 129 | Complete | HIDDEN | Button not visible on page (likely  |
| 130 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 131 | unnamed | HIDDEN | Button not visible on page (likely  |
| 132 | unnamed | HIDDEN | Button not visible on page (likely  |
| 133 | Signup | HIDDEN | Button not visible on page (likely  |
| 134 | Active | HIDDEN | Button not visible on page (likely  |
| 135 | Paused | HIDDEN | Button not visible on page (likely  |
| 136 | Complete | HIDDEN | Button not visible on page (likely  |
| 137 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 138 | unnamed | HIDDEN | Button not visible on page (likely  |
| 139 | unnamed | HIDDEN | Button not visible on page (likely  |
| 140 | Signup | HIDDEN | Button not visible on page (likely  |
| 141 | Active | HIDDEN | Button not visible on page (likely  |
| 142 | Paused | HIDDEN | Button not visible on page (likely  |
| 143 | Complete | HIDDEN | Button not visible on page (likely  |
| 144 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 145 | unnamed | HIDDEN | Button not visible on page (likely  |
| 146 | unnamed | HIDDEN | Button not visible on page (likely  |
| 147 | Signup | HIDDEN | Button not visible on page (likely  |
| 148 | Active | HIDDEN | Button not visible on page (likely  |
| 149 | Paused | HIDDEN | Button not visible on page (likely  |
| 150 | Complete | HIDDEN | Button not visible on page (likely  |
| 151 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 152 | unnamed | HIDDEN | Button not visible on page (likely  |
| 153 | unnamed | HIDDEN | Button not visible on page (likely  |
| 154 | Signup | HIDDEN | Button not visible on page (likely  |
| 155 | Active | HIDDEN | Button not visible on page (likely  |
| 156 | Paused | HIDDEN | Button not visible on page (likely  |
| 157 | Complete | HIDDEN | Button not visible on page (likely  |
| 158 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 159 | unnamed | HIDDEN | Button not visible on page (likely  |
| 160 | unnamed | HIDDEN | Button not visible on page (likely  |
| 161 | Signup | HIDDEN | Button not visible on page (likely  |
| 162 | Active | HIDDEN | Button not visible on page (likely  |
| 163 | Paused | HIDDEN | Button not visible on page (likely  |
| 164 | Complete | HIDDEN | Button not visible on page (likely  |
| 165 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 166 | unnamed | HIDDEN | Button not visible on page (likely  |
| 167 | unnamed | HIDDEN | Button not visible on page (likely  |
| 168 | Signup | HIDDEN | Button not visible on page (likely  |
| 169 | Active | HIDDEN | Button not visible on page (likely  |
| 170 | Paused | HIDDEN | Button not visible on page (likely  |
| 171 | Complete | HIDDEN | Button not visible on page (likely  |
| 172 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 173 | unnamed | HIDDEN | Button not visible on page (likely  |
| 174 | unnamed | HIDDEN | Button not visible on page (likely  |
| 175 | Signup | HIDDEN | Button not visible on page (likely  |
| 176 | Active | HIDDEN | Button not visible on page (likely  |
| 177 | Paused | HIDDEN | Button not visible on page (likely  |
| 178 | Complete | HIDDEN | Button not visible on page (likely  |
| 179 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 180 | unnamed | HIDDEN | Button not visible on page (likely  |
| 181 | unnamed | HIDDEN | Button not visible on page (likely  |
| 182 | Signup | HIDDEN | Button not visible on page (likely  |
| 183 | Active | HIDDEN | Button not visible on page (likely  |
| 184 | Paused | HIDDEN | Button not visible on page (likely  |
| 185 | Complete | HIDDEN | Button not visible on page (likely  |
| 186 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 187 | unnamed | HIDDEN | Button not visible on page (likely  |
| 188 | unnamed | HIDDEN | Button not visible on page (likely  |
| 189 | Signup | HIDDEN | Button not visible on page (likely  |
| 190 | Active | HIDDEN | Button not visible on page (likely  |
| 191 | Paused | HIDDEN | Button not visible on page (likely  |
| 192 | Complete | HIDDEN | Button not visible on page (likely  |
| 193 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 194 | unnamed | HIDDEN | Button not visible on page (likely  |
| 195 | unnamed | HIDDEN | Button not visible on page (likely  |
| 196 | Signup | HIDDEN | Button not visible on page (likely  |
| 197 | Active | HIDDEN | Button not visible on page (likely  |
| 198 | Paused | HIDDEN | Button not visible on page (likely  |
| 199 | Complete | HIDDEN | Button not visible on page (likely  |
| 200 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 201 | unnamed | HIDDEN | Button not visible on page (likely  |
| 202 | unnamed | HIDDEN | Button not visible on page (likely  |
| 203 | Signup | HIDDEN | Button not visible on page (likely  |
| 204 | Active | HIDDEN | Button not visible on page (likely  |
| 205 | Paused | HIDDEN | Button not visible on page (likely  |
| 206 | Complete | HIDDEN | Button not visible on page (likely  |
| 207 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 208 | unnamed | HIDDEN | Button not visible on page (likely  |
| 209 | unnamed | HIDDEN | Button not visible on page (likely  |
| 210 | Signup | HIDDEN | Button not visible on page (likely  |
| 211 | Active | HIDDEN | Button not visible on page (likely  |
| 212 | Paused | HIDDEN | Button not visible on page (likely  |
| 213 | Complete | HIDDEN | Button not visible on page (likely  |
| 214 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 215 | unnamed | HIDDEN | Button not visible on page (likely  |
| 216 | unnamed | HIDDEN | Button not visible on page (likely  |
| 217 | Signup | HIDDEN | Button not visible on page (likely  |
| 218 | Active | HIDDEN | Button not visible on page (likely  |
| 219 | Paused | HIDDEN | Button not visible on page (likely  |
| 220 | Complete | HIDDEN | Button not visible on page (likely  |
| 221 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 222 | unnamed | HIDDEN | Button not visible on page (likely  |
| 223 | unnamed | HIDDEN | Button not visible on page (likely  |
| 224 | Signup | HIDDEN | Button not visible on page (likely  |
| 225 | Active | HIDDEN | Button not visible on page (likely  |
| 226 | Paused | HIDDEN | Button not visible on page (likely  |
| 227 | Complete | HIDDEN | Button not visible on page (likely  |
| 228 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 229 | unnamed | HIDDEN | Button not visible on page (likely  |
| 230 | unnamed | HIDDEN | Button not visible on page (likely  |
| 231 | Signup | HIDDEN | Button not visible on page (likely  |
| 232 | Active | HIDDEN | Button not visible on page (likely  |
| 233 | Paused | HIDDEN | Button not visible on page (likely  |
| 234 | Complete | HIDDEN | Button not visible on page (likely  |
| 235 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 236 | unnamed | HIDDEN | Button not visible on page (likely  |
| 237 | unnamed | HIDDEN | Button not visible on page (likely  |
| 238 | Signup | HIDDEN | Button not visible on page (likely  |
| 239 | Active | HIDDEN | Button not visible on page (likely  |
| 240 | Paused | HIDDEN | Button not visible on page (likely  |
| 241 | Complete | HIDDEN | Button not visible on page (likely  |
| 242 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 243 | unnamed | HIDDEN | Button not visible on page (likely  |
| 244 | unnamed | HIDDEN | Button not visible on page (likely  |
| 245 | Signup | HIDDEN | Button not visible on page (likely  |
| 246 | Active | HIDDEN | Button not visible on page (likely  |
| 247 | Paused | HIDDEN | Button not visible on page (likely  |
| 248 | Complete | HIDDEN | Button not visible on page (likely  |
| 249 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 250 | unnamed | HIDDEN | Button not visible on page (likely  |
| 251 | unnamed | HIDDEN | Button not visible on page (likely  |
| 252 | Signup | HIDDEN | Button not visible on page (likely  |
| 253 | Active | HIDDEN | Button not visible on page (likely  |
| 254 | Paused | HIDDEN | Button not visible on page (likely  |
| 255 | Complete | HIDDEN | Button not visible on page (likely  |
| 256 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 257 | unnamed | HIDDEN | Button not visible on page (likely  |
| 258 | unnamed | HIDDEN | Button not visible on page (likely  |
| 259 | Signup | HIDDEN | Button not visible on page (likely  |
| 260 | Active | HIDDEN | Button not visible on page (likely  |
| 261 | Paused | HIDDEN | Button not visible on page (likely  |
| 262 | Complete | HIDDEN | Button not visible on page (likely  |
| 263 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 264 | unnamed | HIDDEN | Button not visible on page (likely  |
| 265 | unnamed | HIDDEN | Button not visible on page (likely  |
| 266 | Signup | HIDDEN | Button not visible on page (likely  |
| 267 | Active | HIDDEN | Button not visible on page (likely  |
| 268 | Paused | HIDDEN | Button not visible on page (likely  |
| 269 | Complete | HIDDEN | Button not visible on page (likely  |
| 270 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 271 | unnamed | HIDDEN | Button not visible on page (likely  |
| 272 | unnamed | HIDDEN | Button not visible on page (likely  |
| 273 | Signup | HIDDEN | Button not visible on page (likely  |
| 274 | Active | HIDDEN | Button not visible on page (likely  |
| 275 | Paused | HIDDEN | Button not visible on page (likely  |
| 276 | Complete | HIDDEN | Button not visible on page (likely  |
| 277 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 278 | unnamed | HIDDEN | Button not visible on page (likely  |
| 279 | unnamed | HIDDEN | Button not visible on page (likely  |
| 280 | Signup | HIDDEN | Button not visible on page (likely  |
| 281 | Active | HIDDEN | Button not visible on page (likely  |
| 282 | Paused | HIDDEN | Button not visible on page (likely  |
| 283 | Complete | HIDDEN | Button not visible on page (likely  |
| 284 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 285 | unnamed | HIDDEN | Button not visible on page (likely  |
| 286 | unnamed | HIDDEN | Button not visible on page (likely  |
| 287 | Signup | HIDDEN | Button not visible on page (likely  |
| 288 | Active | HIDDEN | Button not visible on page (likely  |
| 289 | Paused | HIDDEN | Button not visible on page (likely  |
| 290 | Complete | HIDDEN | Button not visible on page (likely  |
| 291 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 292 | unnamed | HIDDEN | Button not visible on page (likely  |
| 293 | unnamed | HIDDEN | Button not visible on page (likely  |
| 294 | Signup | HIDDEN | Button not visible on page (likely  |
| 295 | Active | HIDDEN | Button not visible on page (likely  |
| 296 | Paused | HIDDEN | Button not visible on page (likely  |
| 297 | Complete | HIDDEN | Button not visible on page (likely  |
| 298 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 299 | unnamed | HIDDEN | Button not visible on page (likely  |
| 300 | unnamed | HIDDEN | Button not visible on page (likely  |
| 301 | Signup | HIDDEN | Button not visible on page (likely  |
| 302 | Active | HIDDEN | Button not visible on page (likely  |
| 303 | Paused | HIDDEN | Button not visible on page (likely  |
| 304 | Complete | HIDDEN | Button not visible on page (likely  |
| 305 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 306 | unnamed | HIDDEN | Button not visible on page (likely  |
| 307 | unnamed | HIDDEN | Button not visible on page (likely  |
| 308 | Signup | HIDDEN | Button not visible on page (likely  |
| 309 | Active | HIDDEN | Button not visible on page (likely  |
| 310 | Paused | HIDDEN | Button not visible on page (likely  |
| 311 | Complete | HIDDEN | Button not visible on page (likely  |
| 312 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 313 | unnamed | HIDDEN | Button not visible on page (likely  |
| 314 | unnamed | HIDDEN | Button not visible on page (likely  |
| 315 | Signup | HIDDEN | Button not visible on page (likely  |
| 316 | Active | HIDDEN | Button not visible on page (likely  |
| 317 | Paused | HIDDEN | Button not visible on page (likely  |
| 318 | Complete | HIDDEN | Button not visible on page (likely  |
| 319 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 320 | unnamed | HIDDEN | Button not visible on page (likely  |
| 321 | unnamed | HIDDEN | Button not visible on page (likely  |
| 322 | Signup | HIDDEN | Button not visible on page (likely  |
| 323 | Active | HIDDEN | Button not visible on page (likely  |
| 324 | Paused | HIDDEN | Button not visible on page (likely  |
| 325 | Complete | HIDDEN | Button not visible on page (likely  |
| 326 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 327 | unnamed | HIDDEN | Button not visible on page (likely  |
| 328 | unnamed | HIDDEN | Button not visible on page (likely  |
| 329 | Signup | HIDDEN | Button not visible on page (likely  |
| 330 | Active | HIDDEN | Button not visible on page (likely  |
| 331 | Paused | HIDDEN | Button not visible on page (likely  |
| 332 | Complete | HIDDEN | Button not visible on page (likely  |
| 333 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 334 | unnamed | HIDDEN | Button not visible on page (likely  |
| 335 | unnamed | HIDDEN | Button not visible on page (likely  |
| 336 | Signup | HIDDEN | Button not visible on page (likely  |
| 337 | Active | HIDDEN | Button not visible on page (likely  |
| 338 | Paused | HIDDEN | Button not visible on page (likely  |
| 339 | Complete | HIDDEN | Button not visible on page (likely  |
| 340 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 341 | unnamed | HIDDEN | Button not visible on page (likely  |
| 342 | unnamed | HIDDEN | Button not visible on page (likely  |
| 343 | Signup | HIDDEN | Button not visible on page (likely  |
| 344 | Active | HIDDEN | Button not visible on page (likely  |
| 345 | Paused | HIDDEN | Button not visible on page (likely  |
| 346 | Complete | HIDDEN | Button not visible on page (likely  |
| 347 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 348 | unnamed | HIDDEN | Button not visible on page (likely  |
| 349 | unnamed | HIDDEN | Button not visible on page (likely  |
| 350 | Signup | HIDDEN | Button not visible on page (likely  |
| 351 | Active | HIDDEN | Button not visible on page (likely  |
| 352 | Paused | HIDDEN | Button not visible on page (likely  |
| 353 | Complete | HIDDEN | Button not visible on page (likely  |
| 354 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 355 | unnamed | HIDDEN | Button not visible on page (likely  |
| 356 | unnamed | HIDDEN | Button not visible on page (likely  |
| 357 | Signup | HIDDEN | Button not visible on page (likely  |
| 358 | Active | HIDDEN | Button not visible on page (likely  |
| 359 | Paused | HIDDEN | Button not visible on page (likely  |
| 360 | Complete | HIDDEN | Button not visible on page (likely  |
| 361 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 362 | unnamed | HIDDEN | Button not visible on page (likely  |
| 363 | unnamed | HIDDEN | Button not visible on page (likely  |
| 364 | Signup | HIDDEN | Button not visible on page (likely  |
| 365 | Active | HIDDEN | Button not visible on page (likely  |
| 366 | Paused | HIDDEN | Button not visible on page (likely  |
| 367 | Complete | HIDDEN | Button not visible on page (likely  |
| 368 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 369 | unnamed | HIDDEN | Button not visible on page (likely  |
| 370 | unnamed | HIDDEN | Button not visible on page (likely  |
| 371 | Signup | HIDDEN | Button not visible on page (likely  |
| 372 | Active | HIDDEN | Button not visible on page (likely  |
| 373 | Paused | HIDDEN | Button not visible on page (likely  |
| 374 | Complete | HIDDEN | Button not visible on page (likely  |
| 375 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 376 | unnamed | HIDDEN | Button not visible on page (likely  |
| 377 | unnamed | HIDDEN | Button not visible on page (likely  |
| 378 | Signup | HIDDEN | Button not visible on page (likely  |
| 379 | Active | HIDDEN | Button not visible on page (likely  |
| 380 | Paused | HIDDEN | Button not visible on page (likely  |
| 381 | Complete | HIDDEN | Button not visible on page (likely  |
| 382 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 383 | unnamed | HIDDEN | Button not visible on page (likely  |
| 384 | unnamed | HIDDEN | Button not visible on page (likely  |
| 385 | Signup | HIDDEN | Button not visible on page (likely  |
| 386 | Active | HIDDEN | Button not visible on page (likely  |
| 387 | Paused | HIDDEN | Button not visible on page (likely  |
| 388 | Complete | HIDDEN | Button not visible on page (likely  |
| 389 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 390 | unnamed | HIDDEN | Button not visible on page (likely  |
| 391 | unnamed | HIDDEN | Button not visible on page (likely  |
| 392 | Signup | HIDDEN | Button not visible on page (likely  |
| 393 | Active | HIDDEN | Button not visible on page (likely  |
| 394 | Paused | HIDDEN | Button not visible on page (likely  |
| 395 | Complete | HIDDEN | Button not visible on page (likely  |
| 396 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 397 | unnamed | HIDDEN | Button not visible on page (likely  |
| 398 | unnamed | HIDDEN | Button not visible on page (likely  |
| 399 | Signup | HIDDEN | Button not visible on page (likely  |
| 400 | Active | HIDDEN | Button not visible on page (likely  |
| 401 | Paused | HIDDEN | Button not visible on page (likely  |
| 402 | Complete | HIDDEN | Button not visible on page (likely  |
| 403 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 404 | unnamed | HIDDEN | Button not visible on page (likely  |
| 405 | unnamed | HIDDEN | Button not visible on page (likely  |
| 406 | Signup | HIDDEN | Button not visible on page (likely  |
| 407 | Active | HIDDEN | Button not visible on page (likely  |
| 408 | Paused | HIDDEN | Button not visible on page (likely  |
| 409 | Complete | HIDDEN | Button not visible on page (likely  |
| 410 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 411 | unnamed | HIDDEN | Button not visible on page (likely  |
| 412 | unnamed | HIDDEN | Button not visible on page (likely  |
| 413 | Signup | HIDDEN | Button not visible on page (likely  |
| 414 | Active | HIDDEN | Button not visible on page (likely  |
| 415 | Paused | HIDDEN | Button not visible on page (likely  |
| 416 | Complete | HIDDEN | Button not visible on page (likely  |
| 417 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 418 | unnamed | HIDDEN | Button not visible on page (likely  |
| 419 | unnamed | HIDDEN | Button not visible on page (likely  |
| 420 | Signup | HIDDEN | Button not visible on page (likely  |
| 421 | Active | HIDDEN | Button not visible on page (likely  |
| 422 | Paused | HIDDEN | Button not visible on page (likely  |
| 423 | Complete | HIDDEN | Button not visible on page (likely  |
| 424 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 425 | unnamed | HIDDEN | Button not visible on page (likely  |
| 426 | unnamed | HIDDEN | Button not visible on page (likely  |
| 427 | Signup | HIDDEN | Button not visible on page (likely  |
| 428 | Active | HIDDEN | Button not visible on page (likely  |
| 429 | Paused | HIDDEN | Button not visible on page (likely  |
| 430 | Complete | HIDDEN | Button not visible on page (likely  |
| 431 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 432 | unnamed | HIDDEN | Button not visible on page (likely  |
| 433 | unnamed | HIDDEN | Button not visible on page (likely  |
| 434 | Signup | HIDDEN | Button not visible on page (likely  |
| 435 | Active | HIDDEN | Button not visible on page (likely  |
| 436 | Paused | HIDDEN | Button not visible on page (likely  |
| 437 | Complete | HIDDEN | Button not visible on page (likely  |
| 438 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 439 | unnamed | HIDDEN | Button not visible on page (likely  |
| 440 | unnamed | HIDDEN | Button not visible on page (likely  |
| 441 | Signup | HIDDEN | Button not visible on page (likely  |
| 442 | Active | HIDDEN | Button not visible on page (likely  |
| 443 | Paused | HIDDEN | Button not visible on page (likely  |
| 444 | Complete | HIDDEN | Button not visible on page (likely  |
| 445 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 446 | unnamed | HIDDEN | Button not visible on page (likely  |
| 447 | unnamed | HIDDEN | Button not visible on page (likely  |
| 448 | Signup | HIDDEN | Button not visible on page (likely  |
| 449 | Active | HIDDEN | Button not visible on page (likely  |
| 450 | Paused | HIDDEN | Button not visible on page (likely  |
| 451 | Complete | HIDDEN | Button not visible on page (likely  |
| 452 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 453 | unnamed | HIDDEN | Button not visible on page (likely  |
| 454 | unnamed | HIDDEN | Button not visible on page (likely  |
| 455 | Signup | HIDDEN | Button not visible on page (likely  |
| 456 | Active | HIDDEN | Button not visible on page (likely  |
| 457 | Paused | HIDDEN | Button not visible on page (likely  |
| 458 | Complete | HIDDEN | Button not visible on page (likely  |
| 459 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 460 | unnamed | HIDDEN | Button not visible on page (likely  |
| 461 | unnamed | HIDDEN | Button not visible on page (likely  |
| 462 | Signup | HIDDEN | Button not visible on page (likely  |
| 463 | Active | HIDDEN | Button not visible on page (likely  |
| 464 | Paused | HIDDEN | Button not visible on page (likely  |
| 465 | Complete | HIDDEN | Button not visible on page (likely  |
| 466 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 467 | unnamed | HIDDEN | Button not visible on page (likely  |
| 468 | unnamed | HIDDEN | Button not visible on page (likely  |
| 469 | Signup | HIDDEN | Button not visible on page (likely  |
| 470 | Active | HIDDEN | Button not visible on page (likely  |
| 471 | Paused | HIDDEN | Button not visible on page (likely  |
| 472 | Complete | HIDDEN | Button not visible on page (likely  |
| 473 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 474 | unnamed | HIDDEN | Button not visible on page (likely  |
| 475 | unnamed | HIDDEN | Button not visible on page (likely  |
| 476 | Signup | HIDDEN | Button not visible on page (likely  |
| 477 | Active | HIDDEN | Button not visible on page (likely  |
| 478 | Paused | HIDDEN | Button not visible on page (likely  |
| 479 | Complete | HIDDEN | Button not visible on page (likely  |
| 480 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 481 | unnamed | HIDDEN | Button not visible on page (likely  |
| 482 | unnamed | HIDDEN | Button not visible on page (likely  |
| 483 | Signup | HIDDEN | Button not visible on page (likely  |
| 484 | Active | HIDDEN | Button not visible on page (likely  |
| 485 | Paused | HIDDEN | Button not visible on page (likely  |
| 486 | Complete | HIDDEN | Button not visible on page (likely  |
| 487 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 488 | unnamed | HIDDEN | Button not visible on page (likely  |
| 489 | unnamed | HIDDEN | Button not visible on page (likely  |
| 490 | Signup | HIDDEN | Button not visible on page (likely  |
| 491 | Active | HIDDEN | Button not visible on page (likely  |
| 492 | Paused | HIDDEN | Button not visible on page (likely  |
| 493 | Complete | HIDDEN | Button not visible on page (likely  |
| 494 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 495 | unnamed | HIDDEN | Button not visible on page (likely  |
| 496 | unnamed | HIDDEN | Button not visible on page (likely  |
| 497 | Signup | HIDDEN | Button not visible on page (likely  |
| 498 | Active | HIDDEN | Button not visible on page (likely  |
| 499 | Paused | HIDDEN | Button not visible on page (likely  |
| 500 | Complete | HIDDEN | Button not visible on page (likely  |
| 501 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 502 | unnamed | HIDDEN | Button not visible on page (likely  |
| 503 | unnamed | HIDDEN | Button not visible on page (likely  |
| 504 | Signup | HIDDEN | Button not visible on page (likely  |
| 505 | Active | HIDDEN | Button not visible on page (likely  |
| 506 | Paused | HIDDEN | Button not visible on page (likely  |
| 507 | Complete | HIDDEN | Button not visible on page (likely  |
| 508 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 509 | unnamed | HIDDEN | Button not visible on page (likely  |
| 510 | unnamed | HIDDEN | Button not visible on page (likely  |
| 511 | Signup | HIDDEN | Button not visible on page (likely  |
| 512 | Active | HIDDEN | Button not visible on page (likely  |
| 513 | Paused | HIDDEN | Button not visible on page (likely  |
| 514 | Complete | HIDDEN | Button not visible on page (likely  |
| 515 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 516 | unnamed | HIDDEN | Button not visible on page (likely  |
| 517 | unnamed | HIDDEN | Button not visible on page (likely  |
| 518 | Signup | HIDDEN | Button not visible on page (likely  |
| 519 | Active | HIDDEN | Button not visible on page (likely  |
| 520 | Paused | HIDDEN | Button not visible on page (likely  |
| 521 | Complete | HIDDEN | Button not visible on page (likely  |
| 522 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 523 | unnamed | HIDDEN | Button not visible on page (likely  |
| 524 | unnamed | HIDDEN | Button not visible on page (likely  |
| 525 | Signup | HIDDEN | Button not visible on page (likely  |
| 526 | Active | HIDDEN | Button not visible on page (likely  |
| 527 | Paused | HIDDEN | Button not visible on page (likely  |
| 528 | Complete | HIDDEN | Button not visible on page (likely  |
| 529 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 530 | unnamed | HIDDEN | Button not visible on page (likely  |
| 531 | unnamed | HIDDEN | Button not visible on page (likely  |
| 532 | Signup | HIDDEN | Button not visible on page (likely  |
| 533 | Active | HIDDEN | Button not visible on page (likely  |
| 534 | Paused | HIDDEN | Button not visible on page (likely  |
| 535 | Complete | HIDDEN | Button not visible on page (likely  |
| 536 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 537 | unnamed | HIDDEN | Button not visible on page (likely  |
| 538 | unnamed | HIDDEN | Button not visible on page (likely  |
| 539 | Signup | HIDDEN | Button not visible on page (likely  |
| 540 | Active | HIDDEN | Button not visible on page (likely  |
| 541 | Paused | HIDDEN | Button not visible on page (likely  |
| 542 | Complete | HIDDEN | Button not visible on page (likely  |
| 543 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 544 | unnamed | HIDDEN | Button not visible on page (likely  |
| 545 | unnamed | HIDDEN | Button not visible on page (likely  |
| 546 | Signup | HIDDEN | Button not visible on page (likely  |
| 547 | Active | HIDDEN | Button not visible on page (likely  |
| 548 | Paused | HIDDEN | Button not visible on page (likely  |
| 549 | Complete | HIDDEN | Button not visible on page (likely  |
| 550 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 551 | unnamed | HIDDEN | Button not visible on page (likely  |
| 552 | unnamed | HIDDEN | Button not visible on page (likely  |
| 553 | Signup | HIDDEN | Button not visible on page (likely  |
| 554 | Active | HIDDEN | Button not visible on page (likely  |
| 555 | Paused | HIDDEN | Button not visible on page (likely  |
| 556 | Complete | HIDDEN | Button not visible on page (likely  |
| 557 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 558 | unnamed | HIDDEN | Button not visible on page (likely  |
| 559 | unnamed | HIDDEN | Button not visible on page (likely  |
| 560 | Signup | HIDDEN | Button not visible on page (likely  |
| 561 | Active | HIDDEN | Button not visible on page (likely  |
| 562 | Paused | HIDDEN | Button not visible on page (likely  |
| 563 | Complete | HIDDEN | Button not visible on page (likely  |
| 564 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 565 | unnamed | HIDDEN | Button not visible on page (likely  |
| 566 | unnamed | HIDDEN | Button not visible on page (likely  |
| 567 | × | HIDDEN | Button not visible on page (likely  |

### /dashboard/cases
Found: 568 buttons | Tested: 568

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Apply | HIDDEN | Button not visible on page (likely  |
| 1 | Delete Selected | HIDDEN | Button not visible on page (likely  |
| 2 | ALL | WORKING | Has onclick: quickFilter('all') |
| 3 | ACTIVE | WORKING | Has onclick: quickFilter('active') |
| 4 | LEADS | WORKING | Has onclick: quickFilter('leads') |
| 5 | FOLLOW UP | WORKING | Has onclick: quickFilter('followup' |
| 6 | SIGNUPS | WORKING | Has onclick: quickFilter('signups') |
| 7 | Signup | HIDDEN | Button not visible on page (likely  |
| 8 | Active | HIDDEN | Button not visible on page (likely  |
| 9 | Paused | HIDDEN | Button not visible on page (likely  |
| 10 | Complete | HIDDEN | Button not visible on page (likely  |
| 11 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 12 | unnamed | HIDDEN | Button not visible on page (likely  |
| 13 | unnamed | HIDDEN | Button not visible on page (likely  |
| 14 | Signup | HIDDEN | Button not visible on page (likely  |
| 15 | Active | HIDDEN | Button not visible on page (likely  |
| 16 | Paused | HIDDEN | Button not visible on page (likely  |
| 17 | Complete | HIDDEN | Button not visible on page (likely  |
| 18 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 19 | unnamed | HIDDEN | Button not visible on page (likely  |
| 20 | unnamed | HIDDEN | Button not visible on page (likely  |
| 21 | Signup | HIDDEN | Button not visible on page (likely  |
| 22 | Active | HIDDEN | Button not visible on page (likely  |
| 23 | Paused | HIDDEN | Button not visible on page (likely  |
| 24 | Complete | HIDDEN | Button not visible on page (likely  |
| 25 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 26 | unnamed | HIDDEN | Button not visible on page (likely  |
| 27 | unnamed | HIDDEN | Button not visible on page (likely  |
| 28 | Signup | HIDDEN | Button not visible on page (likely  |
| 29 | Active | HIDDEN | Button not visible on page (likely  |
| 30 | Paused | HIDDEN | Button not visible on page (likely  |
| 31 | Complete | HIDDEN | Button not visible on page (likely  |
| 32 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 33 | unnamed | HIDDEN | Button not visible on page (likely  |
| 34 | unnamed | HIDDEN | Button not visible on page (likely  |
| 35 | Signup | HIDDEN | Button not visible on page (likely  |
| 36 | Active | HIDDEN | Button not visible on page (likely  |
| 37 | Paused | HIDDEN | Button not visible on page (likely  |
| 38 | Complete | HIDDEN | Button not visible on page (likely  |
| 39 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 40 | unnamed | HIDDEN | Button not visible on page (likely  |
| 41 | unnamed | HIDDEN | Button not visible on page (likely  |
| 42 | Signup | HIDDEN | Button not visible on page (likely  |
| 43 | Active | HIDDEN | Button not visible on page (likely  |
| 44 | Paused | HIDDEN | Button not visible on page (likely  |
| 45 | Complete | HIDDEN | Button not visible on page (likely  |
| 46 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 47 | unnamed | HIDDEN | Button not visible on page (likely  |
| 48 | unnamed | HIDDEN | Button not visible on page (likely  |
| 49 | Signup | HIDDEN | Button not visible on page (likely  |
| 50 | Active | HIDDEN | Button not visible on page (likely  |
| 51 | Paused | HIDDEN | Button not visible on page (likely  |
| 52 | Complete | HIDDEN | Button not visible on page (likely  |
| 53 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 54 | unnamed | HIDDEN | Button not visible on page (likely  |
| 55 | unnamed | HIDDEN | Button not visible on page (likely  |
| 56 | Signup | HIDDEN | Button not visible on page (likely  |
| 57 | Active | HIDDEN | Button not visible on page (likely  |
| 58 | Paused | HIDDEN | Button not visible on page (likely  |
| 59 | Complete | HIDDEN | Button not visible on page (likely  |
| 60 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 61 | unnamed | HIDDEN | Button not visible on page (likely  |
| 62 | unnamed | HIDDEN | Button not visible on page (likely  |
| 63 | Signup | HIDDEN | Button not visible on page (likely  |
| 64 | Active | HIDDEN | Button not visible on page (likely  |
| 65 | Paused | HIDDEN | Button not visible on page (likely  |
| 66 | Complete | HIDDEN | Button not visible on page (likely  |
| 67 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 68 | unnamed | HIDDEN | Button not visible on page (likely  |
| 69 | unnamed | HIDDEN | Button not visible on page (likely  |
| 70 | Signup | HIDDEN | Button not visible on page (likely  |
| 71 | Active | HIDDEN | Button not visible on page (likely  |
| 72 | Paused | HIDDEN | Button not visible on page (likely  |
| 73 | Complete | HIDDEN | Button not visible on page (likely  |
| 74 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 75 | unnamed | HIDDEN | Button not visible on page (likely  |
| 76 | unnamed | HIDDEN | Button not visible on page (likely  |
| 77 | Signup | HIDDEN | Button not visible on page (likely  |
| 78 | Active | HIDDEN | Button not visible on page (likely  |
| 79 | Paused | HIDDEN | Button not visible on page (likely  |
| 80 | Complete | HIDDEN | Button not visible on page (likely  |
| 81 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 82 | unnamed | HIDDEN | Button not visible on page (likely  |
| 83 | unnamed | HIDDEN | Button not visible on page (likely  |
| 84 | Signup | HIDDEN | Button not visible on page (likely  |
| 85 | Active | HIDDEN | Button not visible on page (likely  |
| 86 | Paused | HIDDEN | Button not visible on page (likely  |
| 87 | Complete | HIDDEN | Button not visible on page (likely  |
| 88 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 89 | unnamed | HIDDEN | Button not visible on page (likely  |
| 90 | unnamed | HIDDEN | Button not visible on page (likely  |
| 91 | Signup | HIDDEN | Button not visible on page (likely  |
| 92 | Active | HIDDEN | Button not visible on page (likely  |
| 93 | Paused | HIDDEN | Button not visible on page (likely  |
| 94 | Complete | HIDDEN | Button not visible on page (likely  |
| 95 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 96 | unnamed | HIDDEN | Button not visible on page (likely  |
| 97 | unnamed | HIDDEN | Button not visible on page (likely  |
| 98 | Signup | HIDDEN | Button not visible on page (likely  |
| 99 | Active | HIDDEN | Button not visible on page (likely  |
| 100 | Paused | HIDDEN | Button not visible on page (likely  |
| 101 | Complete | HIDDEN | Button not visible on page (likely  |
| 102 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 103 | unnamed | HIDDEN | Button not visible on page (likely  |
| 104 | unnamed | HIDDEN | Button not visible on page (likely  |
| 105 | Signup | HIDDEN | Button not visible on page (likely  |
| 106 | Active | HIDDEN | Button not visible on page (likely  |
| 107 | Paused | HIDDEN | Button not visible on page (likely  |
| 108 | Complete | HIDDEN | Button not visible on page (likely  |
| 109 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 110 | unnamed | HIDDEN | Button not visible on page (likely  |
| 111 | unnamed | HIDDEN | Button not visible on page (likely  |
| 112 | Signup | HIDDEN | Button not visible on page (likely  |
| 113 | Active | HIDDEN | Button not visible on page (likely  |
| 114 | Paused | HIDDEN | Button not visible on page (likely  |
| 115 | Complete | HIDDEN | Button not visible on page (likely  |
| 116 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 117 | unnamed | HIDDEN | Button not visible on page (likely  |
| 118 | unnamed | HIDDEN | Button not visible on page (likely  |
| 119 | Signup | HIDDEN | Button not visible on page (likely  |
| 120 | Active | HIDDEN | Button not visible on page (likely  |
| 121 | Paused | HIDDEN | Button not visible on page (likely  |
| 122 | Complete | HIDDEN | Button not visible on page (likely  |
| 123 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 124 | unnamed | HIDDEN | Button not visible on page (likely  |
| 125 | unnamed | HIDDEN | Button not visible on page (likely  |
| 126 | Signup | HIDDEN | Button not visible on page (likely  |
| 127 | Active | HIDDEN | Button not visible on page (likely  |
| 128 | Paused | HIDDEN | Button not visible on page (likely  |
| 129 | Complete | HIDDEN | Button not visible on page (likely  |
| 130 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 131 | unnamed | HIDDEN | Button not visible on page (likely  |
| 132 | unnamed | HIDDEN | Button not visible on page (likely  |
| 133 | Signup | HIDDEN | Button not visible on page (likely  |
| 134 | Active | HIDDEN | Button not visible on page (likely  |
| 135 | Paused | HIDDEN | Button not visible on page (likely  |
| 136 | Complete | HIDDEN | Button not visible on page (likely  |
| 137 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 138 | unnamed | HIDDEN | Button not visible on page (likely  |
| 139 | unnamed | HIDDEN | Button not visible on page (likely  |
| 140 | Signup | HIDDEN | Button not visible on page (likely  |
| 141 | Active | HIDDEN | Button not visible on page (likely  |
| 142 | Paused | HIDDEN | Button not visible on page (likely  |
| 143 | Complete | HIDDEN | Button not visible on page (likely  |
| 144 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 145 | unnamed | HIDDEN | Button not visible on page (likely  |
| 146 | unnamed | HIDDEN | Button not visible on page (likely  |
| 147 | Signup | HIDDEN | Button not visible on page (likely  |
| 148 | Active | HIDDEN | Button not visible on page (likely  |
| 149 | Paused | HIDDEN | Button not visible on page (likely  |
| 150 | Complete | HIDDEN | Button not visible on page (likely  |
| 151 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 152 | unnamed | HIDDEN | Button not visible on page (likely  |
| 153 | unnamed | HIDDEN | Button not visible on page (likely  |
| 154 | Signup | HIDDEN | Button not visible on page (likely  |
| 155 | Active | HIDDEN | Button not visible on page (likely  |
| 156 | Paused | HIDDEN | Button not visible on page (likely  |
| 157 | Complete | HIDDEN | Button not visible on page (likely  |
| 158 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 159 | unnamed | HIDDEN | Button not visible on page (likely  |
| 160 | unnamed | HIDDEN | Button not visible on page (likely  |
| 161 | Signup | HIDDEN | Button not visible on page (likely  |
| 162 | Active | HIDDEN | Button not visible on page (likely  |
| 163 | Paused | HIDDEN | Button not visible on page (likely  |
| 164 | Complete | HIDDEN | Button not visible on page (likely  |
| 165 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 166 | unnamed | HIDDEN | Button not visible on page (likely  |
| 167 | unnamed | HIDDEN | Button not visible on page (likely  |
| 168 | Signup | HIDDEN | Button not visible on page (likely  |
| 169 | Active | HIDDEN | Button not visible on page (likely  |
| 170 | Paused | HIDDEN | Button not visible on page (likely  |
| 171 | Complete | HIDDEN | Button not visible on page (likely  |
| 172 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 173 | unnamed | HIDDEN | Button not visible on page (likely  |
| 174 | unnamed | HIDDEN | Button not visible on page (likely  |
| 175 | Signup | HIDDEN | Button not visible on page (likely  |
| 176 | Active | HIDDEN | Button not visible on page (likely  |
| 177 | Paused | HIDDEN | Button not visible on page (likely  |
| 178 | Complete | HIDDEN | Button not visible on page (likely  |
| 179 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 180 | unnamed | HIDDEN | Button not visible on page (likely  |
| 181 | unnamed | HIDDEN | Button not visible on page (likely  |
| 182 | Signup | HIDDEN | Button not visible on page (likely  |
| 183 | Active | HIDDEN | Button not visible on page (likely  |
| 184 | Paused | HIDDEN | Button not visible on page (likely  |
| 185 | Complete | HIDDEN | Button not visible on page (likely  |
| 186 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 187 | unnamed | HIDDEN | Button not visible on page (likely  |
| 188 | unnamed | HIDDEN | Button not visible on page (likely  |
| 189 | Signup | HIDDEN | Button not visible on page (likely  |
| 190 | Active | HIDDEN | Button not visible on page (likely  |
| 191 | Paused | HIDDEN | Button not visible on page (likely  |
| 192 | Complete | HIDDEN | Button not visible on page (likely  |
| 193 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 194 | unnamed | HIDDEN | Button not visible on page (likely  |
| 195 | unnamed | HIDDEN | Button not visible on page (likely  |
| 196 | Signup | HIDDEN | Button not visible on page (likely  |
| 197 | Active | HIDDEN | Button not visible on page (likely  |
| 198 | Paused | HIDDEN | Button not visible on page (likely  |
| 199 | Complete | HIDDEN | Button not visible on page (likely  |
| 200 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 201 | unnamed | HIDDEN | Button not visible on page (likely  |
| 202 | unnamed | HIDDEN | Button not visible on page (likely  |
| 203 | Signup | HIDDEN | Button not visible on page (likely  |
| 204 | Active | HIDDEN | Button not visible on page (likely  |
| 205 | Paused | HIDDEN | Button not visible on page (likely  |
| 206 | Complete | HIDDEN | Button not visible on page (likely  |
| 207 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 208 | unnamed | HIDDEN | Button not visible on page (likely  |
| 209 | unnamed | HIDDEN | Button not visible on page (likely  |
| 210 | Signup | HIDDEN | Button not visible on page (likely  |
| 211 | Active | HIDDEN | Button not visible on page (likely  |
| 212 | Paused | HIDDEN | Button not visible on page (likely  |
| 213 | Complete | HIDDEN | Button not visible on page (likely  |
| 214 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 215 | unnamed | HIDDEN | Button not visible on page (likely  |
| 216 | unnamed | HIDDEN | Button not visible on page (likely  |
| 217 | Signup | HIDDEN | Button not visible on page (likely  |
| 218 | Active | HIDDEN | Button not visible on page (likely  |
| 219 | Paused | HIDDEN | Button not visible on page (likely  |
| 220 | Complete | HIDDEN | Button not visible on page (likely  |
| 221 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 222 | unnamed | HIDDEN | Button not visible on page (likely  |
| 223 | unnamed | HIDDEN | Button not visible on page (likely  |
| 224 | Signup | HIDDEN | Button not visible on page (likely  |
| 225 | Active | HIDDEN | Button not visible on page (likely  |
| 226 | Paused | HIDDEN | Button not visible on page (likely  |
| 227 | Complete | HIDDEN | Button not visible on page (likely  |
| 228 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 229 | unnamed | HIDDEN | Button not visible on page (likely  |
| 230 | unnamed | HIDDEN | Button not visible on page (likely  |
| 231 | Signup | HIDDEN | Button not visible on page (likely  |
| 232 | Active | HIDDEN | Button not visible on page (likely  |
| 233 | Paused | HIDDEN | Button not visible on page (likely  |
| 234 | Complete | HIDDEN | Button not visible on page (likely  |
| 235 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 236 | unnamed | HIDDEN | Button not visible on page (likely  |
| 237 | unnamed | HIDDEN | Button not visible on page (likely  |
| 238 | Signup | HIDDEN | Button not visible on page (likely  |
| 239 | Active | HIDDEN | Button not visible on page (likely  |
| 240 | Paused | HIDDEN | Button not visible on page (likely  |
| 241 | Complete | HIDDEN | Button not visible on page (likely  |
| 242 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 243 | unnamed | HIDDEN | Button not visible on page (likely  |
| 244 | unnamed | HIDDEN | Button not visible on page (likely  |
| 245 | Signup | HIDDEN | Button not visible on page (likely  |
| 246 | Active | HIDDEN | Button not visible on page (likely  |
| 247 | Paused | HIDDEN | Button not visible on page (likely  |
| 248 | Complete | HIDDEN | Button not visible on page (likely  |
| 249 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 250 | unnamed | HIDDEN | Button not visible on page (likely  |
| 251 | unnamed | HIDDEN | Button not visible on page (likely  |
| 252 | Signup | HIDDEN | Button not visible on page (likely  |
| 253 | Active | HIDDEN | Button not visible on page (likely  |
| 254 | Paused | HIDDEN | Button not visible on page (likely  |
| 255 | Complete | HIDDEN | Button not visible on page (likely  |
| 256 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 257 | unnamed | HIDDEN | Button not visible on page (likely  |
| 258 | unnamed | HIDDEN | Button not visible on page (likely  |
| 259 | Signup | HIDDEN | Button not visible on page (likely  |
| 260 | Active | HIDDEN | Button not visible on page (likely  |
| 261 | Paused | HIDDEN | Button not visible on page (likely  |
| 262 | Complete | HIDDEN | Button not visible on page (likely  |
| 263 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 264 | unnamed | HIDDEN | Button not visible on page (likely  |
| 265 | unnamed | HIDDEN | Button not visible on page (likely  |
| 266 | Signup | HIDDEN | Button not visible on page (likely  |
| 267 | Active | HIDDEN | Button not visible on page (likely  |
| 268 | Paused | HIDDEN | Button not visible on page (likely  |
| 269 | Complete | HIDDEN | Button not visible on page (likely  |
| 270 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 271 | unnamed | HIDDEN | Button not visible on page (likely  |
| 272 | unnamed | HIDDEN | Button not visible on page (likely  |
| 273 | Signup | HIDDEN | Button not visible on page (likely  |
| 274 | Active | HIDDEN | Button not visible on page (likely  |
| 275 | Paused | HIDDEN | Button not visible on page (likely  |
| 276 | Complete | HIDDEN | Button not visible on page (likely  |
| 277 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 278 | unnamed | HIDDEN | Button not visible on page (likely  |
| 279 | unnamed | HIDDEN | Button not visible on page (likely  |
| 280 | Signup | HIDDEN | Button not visible on page (likely  |
| 281 | Active | HIDDEN | Button not visible on page (likely  |
| 282 | Paused | HIDDEN | Button not visible on page (likely  |
| 283 | Complete | HIDDEN | Button not visible on page (likely  |
| 284 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 285 | unnamed | HIDDEN | Button not visible on page (likely  |
| 286 | unnamed | HIDDEN | Button not visible on page (likely  |
| 287 | Signup | HIDDEN | Button not visible on page (likely  |
| 288 | Active | HIDDEN | Button not visible on page (likely  |
| 289 | Paused | HIDDEN | Button not visible on page (likely  |
| 290 | Complete | HIDDEN | Button not visible on page (likely  |
| 291 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 292 | unnamed | HIDDEN | Button not visible on page (likely  |
| 293 | unnamed | HIDDEN | Button not visible on page (likely  |
| 294 | Signup | HIDDEN | Button not visible on page (likely  |
| 295 | Active | HIDDEN | Button not visible on page (likely  |
| 296 | Paused | HIDDEN | Button not visible on page (likely  |
| 297 | Complete | HIDDEN | Button not visible on page (likely  |
| 298 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 299 | unnamed | HIDDEN | Button not visible on page (likely  |
| 300 | unnamed | HIDDEN | Button not visible on page (likely  |
| 301 | Signup | HIDDEN | Button not visible on page (likely  |
| 302 | Active | HIDDEN | Button not visible on page (likely  |
| 303 | Paused | HIDDEN | Button not visible on page (likely  |
| 304 | Complete | HIDDEN | Button not visible on page (likely  |
| 305 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 306 | unnamed | HIDDEN | Button not visible on page (likely  |
| 307 | unnamed | HIDDEN | Button not visible on page (likely  |
| 308 | Signup | HIDDEN | Button not visible on page (likely  |
| 309 | Active | HIDDEN | Button not visible on page (likely  |
| 310 | Paused | HIDDEN | Button not visible on page (likely  |
| 311 | Complete | HIDDEN | Button not visible on page (likely  |
| 312 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 313 | unnamed | HIDDEN | Button not visible on page (likely  |
| 314 | unnamed | HIDDEN | Button not visible on page (likely  |
| 315 | Signup | HIDDEN | Button not visible on page (likely  |
| 316 | Active | HIDDEN | Button not visible on page (likely  |
| 317 | Paused | HIDDEN | Button not visible on page (likely  |
| 318 | Complete | HIDDEN | Button not visible on page (likely  |
| 319 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 320 | unnamed | HIDDEN | Button not visible on page (likely  |
| 321 | unnamed | HIDDEN | Button not visible on page (likely  |
| 322 | Signup | HIDDEN | Button not visible on page (likely  |
| 323 | Active | HIDDEN | Button not visible on page (likely  |
| 324 | Paused | HIDDEN | Button not visible on page (likely  |
| 325 | Complete | HIDDEN | Button not visible on page (likely  |
| 326 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 327 | unnamed | HIDDEN | Button not visible on page (likely  |
| 328 | unnamed | HIDDEN | Button not visible on page (likely  |
| 329 | Signup | HIDDEN | Button not visible on page (likely  |
| 330 | Active | HIDDEN | Button not visible on page (likely  |
| 331 | Paused | HIDDEN | Button not visible on page (likely  |
| 332 | Complete | HIDDEN | Button not visible on page (likely  |
| 333 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 334 | unnamed | HIDDEN | Button not visible on page (likely  |
| 335 | unnamed | HIDDEN | Button not visible on page (likely  |
| 336 | Signup | HIDDEN | Button not visible on page (likely  |
| 337 | Active | HIDDEN | Button not visible on page (likely  |
| 338 | Paused | HIDDEN | Button not visible on page (likely  |
| 339 | Complete | HIDDEN | Button not visible on page (likely  |
| 340 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 341 | unnamed | HIDDEN | Button not visible on page (likely  |
| 342 | unnamed | HIDDEN | Button not visible on page (likely  |
| 343 | Signup | HIDDEN | Button not visible on page (likely  |
| 344 | Active | HIDDEN | Button not visible on page (likely  |
| 345 | Paused | HIDDEN | Button not visible on page (likely  |
| 346 | Complete | HIDDEN | Button not visible on page (likely  |
| 347 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 348 | unnamed | HIDDEN | Button not visible on page (likely  |
| 349 | unnamed | HIDDEN | Button not visible on page (likely  |
| 350 | Signup | HIDDEN | Button not visible on page (likely  |
| 351 | Active | HIDDEN | Button not visible on page (likely  |
| 352 | Paused | HIDDEN | Button not visible on page (likely  |
| 353 | Complete | HIDDEN | Button not visible on page (likely  |
| 354 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 355 | unnamed | HIDDEN | Button not visible on page (likely  |
| 356 | unnamed | HIDDEN | Button not visible on page (likely  |
| 357 | Signup | HIDDEN | Button not visible on page (likely  |
| 358 | Active | HIDDEN | Button not visible on page (likely  |
| 359 | Paused | HIDDEN | Button not visible on page (likely  |
| 360 | Complete | HIDDEN | Button not visible on page (likely  |
| 361 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 362 | unnamed | HIDDEN | Button not visible on page (likely  |
| 363 | unnamed | HIDDEN | Button not visible on page (likely  |
| 364 | Signup | HIDDEN | Button not visible on page (likely  |
| 365 | Active | HIDDEN | Button not visible on page (likely  |
| 366 | Paused | HIDDEN | Button not visible on page (likely  |
| 367 | Complete | HIDDEN | Button not visible on page (likely  |
| 368 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 369 | unnamed | HIDDEN | Button not visible on page (likely  |
| 370 | unnamed | HIDDEN | Button not visible on page (likely  |
| 371 | Signup | HIDDEN | Button not visible on page (likely  |
| 372 | Active | HIDDEN | Button not visible on page (likely  |
| 373 | Paused | HIDDEN | Button not visible on page (likely  |
| 374 | Complete | HIDDEN | Button not visible on page (likely  |
| 375 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 376 | unnamed | HIDDEN | Button not visible on page (likely  |
| 377 | unnamed | HIDDEN | Button not visible on page (likely  |
| 378 | Signup | HIDDEN | Button not visible on page (likely  |
| 379 | Active | HIDDEN | Button not visible on page (likely  |
| 380 | Paused | HIDDEN | Button not visible on page (likely  |
| 381 | Complete | HIDDEN | Button not visible on page (likely  |
| 382 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 383 | unnamed | HIDDEN | Button not visible on page (likely  |
| 384 | unnamed | HIDDEN | Button not visible on page (likely  |
| 385 | Signup | HIDDEN | Button not visible on page (likely  |
| 386 | Active | HIDDEN | Button not visible on page (likely  |
| 387 | Paused | HIDDEN | Button not visible on page (likely  |
| 388 | Complete | HIDDEN | Button not visible on page (likely  |
| 389 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 390 | unnamed | HIDDEN | Button not visible on page (likely  |
| 391 | unnamed | HIDDEN | Button not visible on page (likely  |
| 392 | Signup | HIDDEN | Button not visible on page (likely  |
| 393 | Active | HIDDEN | Button not visible on page (likely  |
| 394 | Paused | HIDDEN | Button not visible on page (likely  |
| 395 | Complete | HIDDEN | Button not visible on page (likely  |
| 396 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 397 | unnamed | HIDDEN | Button not visible on page (likely  |
| 398 | unnamed | HIDDEN | Button not visible on page (likely  |
| 399 | Signup | HIDDEN | Button not visible on page (likely  |
| 400 | Active | HIDDEN | Button not visible on page (likely  |
| 401 | Paused | HIDDEN | Button not visible on page (likely  |
| 402 | Complete | HIDDEN | Button not visible on page (likely  |
| 403 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 404 | unnamed | HIDDEN | Button not visible on page (likely  |
| 405 | unnamed | HIDDEN | Button not visible on page (likely  |
| 406 | Signup | HIDDEN | Button not visible on page (likely  |
| 407 | Active | HIDDEN | Button not visible on page (likely  |
| 408 | Paused | HIDDEN | Button not visible on page (likely  |
| 409 | Complete | HIDDEN | Button not visible on page (likely  |
| 410 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 411 | unnamed | HIDDEN | Button not visible on page (likely  |
| 412 | unnamed | HIDDEN | Button not visible on page (likely  |
| 413 | Signup | HIDDEN | Button not visible on page (likely  |
| 414 | Active | HIDDEN | Button not visible on page (likely  |
| 415 | Paused | HIDDEN | Button not visible on page (likely  |
| 416 | Complete | HIDDEN | Button not visible on page (likely  |
| 417 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 418 | unnamed | HIDDEN | Button not visible on page (likely  |
| 419 | unnamed | HIDDEN | Button not visible on page (likely  |
| 420 | Signup | HIDDEN | Button not visible on page (likely  |
| 421 | Active | HIDDEN | Button not visible on page (likely  |
| 422 | Paused | HIDDEN | Button not visible on page (likely  |
| 423 | Complete | HIDDEN | Button not visible on page (likely  |
| 424 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 425 | unnamed | HIDDEN | Button not visible on page (likely  |
| 426 | unnamed | HIDDEN | Button not visible on page (likely  |
| 427 | Signup | HIDDEN | Button not visible on page (likely  |
| 428 | Active | HIDDEN | Button not visible on page (likely  |
| 429 | Paused | HIDDEN | Button not visible on page (likely  |
| 430 | Complete | HIDDEN | Button not visible on page (likely  |
| 431 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 432 | unnamed | HIDDEN | Button not visible on page (likely  |
| 433 | unnamed | HIDDEN | Button not visible on page (likely  |
| 434 | Signup | HIDDEN | Button not visible on page (likely  |
| 435 | Active | HIDDEN | Button not visible on page (likely  |
| 436 | Paused | HIDDEN | Button not visible on page (likely  |
| 437 | Complete | HIDDEN | Button not visible on page (likely  |
| 438 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 439 | unnamed | HIDDEN | Button not visible on page (likely  |
| 440 | unnamed | HIDDEN | Button not visible on page (likely  |
| 441 | Signup | HIDDEN | Button not visible on page (likely  |
| 442 | Active | HIDDEN | Button not visible on page (likely  |
| 443 | Paused | HIDDEN | Button not visible on page (likely  |
| 444 | Complete | HIDDEN | Button not visible on page (likely  |
| 445 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 446 | unnamed | HIDDEN | Button not visible on page (likely  |
| 447 | unnamed | HIDDEN | Button not visible on page (likely  |
| 448 | Signup | HIDDEN | Button not visible on page (likely  |
| 449 | Active | HIDDEN | Button not visible on page (likely  |
| 450 | Paused | HIDDEN | Button not visible on page (likely  |
| 451 | Complete | HIDDEN | Button not visible on page (likely  |
| 452 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 453 | unnamed | HIDDEN | Button not visible on page (likely  |
| 454 | unnamed | HIDDEN | Button not visible on page (likely  |
| 455 | Signup | HIDDEN | Button not visible on page (likely  |
| 456 | Active | HIDDEN | Button not visible on page (likely  |
| 457 | Paused | HIDDEN | Button not visible on page (likely  |
| 458 | Complete | HIDDEN | Button not visible on page (likely  |
| 459 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 460 | unnamed | HIDDEN | Button not visible on page (likely  |
| 461 | unnamed | HIDDEN | Button not visible on page (likely  |
| 462 | Signup | HIDDEN | Button not visible on page (likely  |
| 463 | Active | HIDDEN | Button not visible on page (likely  |
| 464 | Paused | HIDDEN | Button not visible on page (likely  |
| 465 | Complete | HIDDEN | Button not visible on page (likely  |
| 466 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 467 | unnamed | HIDDEN | Button not visible on page (likely  |
| 468 | unnamed | HIDDEN | Button not visible on page (likely  |
| 469 | Signup | HIDDEN | Button not visible on page (likely  |
| 470 | Active | HIDDEN | Button not visible on page (likely  |
| 471 | Paused | HIDDEN | Button not visible on page (likely  |
| 472 | Complete | HIDDEN | Button not visible on page (likely  |
| 473 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 474 | unnamed | HIDDEN | Button not visible on page (likely  |
| 475 | unnamed | HIDDEN | Button not visible on page (likely  |
| 476 | Signup | HIDDEN | Button not visible on page (likely  |
| 477 | Active | HIDDEN | Button not visible on page (likely  |
| 478 | Paused | HIDDEN | Button not visible on page (likely  |
| 479 | Complete | HIDDEN | Button not visible on page (likely  |
| 480 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 481 | unnamed | HIDDEN | Button not visible on page (likely  |
| 482 | unnamed | HIDDEN | Button not visible on page (likely  |
| 483 | Signup | HIDDEN | Button not visible on page (likely  |
| 484 | Active | HIDDEN | Button not visible on page (likely  |
| 485 | Paused | HIDDEN | Button not visible on page (likely  |
| 486 | Complete | HIDDEN | Button not visible on page (likely  |
| 487 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 488 | unnamed | HIDDEN | Button not visible on page (likely  |
| 489 | unnamed | HIDDEN | Button not visible on page (likely  |
| 490 | Signup | HIDDEN | Button not visible on page (likely  |
| 491 | Active | HIDDEN | Button not visible on page (likely  |
| 492 | Paused | HIDDEN | Button not visible on page (likely  |
| 493 | Complete | HIDDEN | Button not visible on page (likely  |
| 494 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 495 | unnamed | HIDDEN | Button not visible on page (likely  |
| 496 | unnamed | HIDDEN | Button not visible on page (likely  |
| 497 | Signup | HIDDEN | Button not visible on page (likely  |
| 498 | Active | HIDDEN | Button not visible on page (likely  |
| 499 | Paused | HIDDEN | Button not visible on page (likely  |
| 500 | Complete | HIDDEN | Button not visible on page (likely  |
| 501 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 502 | unnamed | HIDDEN | Button not visible on page (likely  |
| 503 | unnamed | HIDDEN | Button not visible on page (likely  |
| 504 | Signup | HIDDEN | Button not visible on page (likely  |
| 505 | Active | HIDDEN | Button not visible on page (likely  |
| 506 | Paused | HIDDEN | Button not visible on page (likely  |
| 507 | Complete | HIDDEN | Button not visible on page (likely  |
| 508 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 509 | unnamed | HIDDEN | Button not visible on page (likely  |
| 510 | unnamed | HIDDEN | Button not visible on page (likely  |
| 511 | Signup | HIDDEN | Button not visible on page (likely  |
| 512 | Active | HIDDEN | Button not visible on page (likely  |
| 513 | Paused | HIDDEN | Button not visible on page (likely  |
| 514 | Complete | HIDDEN | Button not visible on page (likely  |
| 515 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 516 | unnamed | HIDDEN | Button not visible on page (likely  |
| 517 | unnamed | HIDDEN | Button not visible on page (likely  |
| 518 | Signup | HIDDEN | Button not visible on page (likely  |
| 519 | Active | HIDDEN | Button not visible on page (likely  |
| 520 | Paused | HIDDEN | Button not visible on page (likely  |
| 521 | Complete | HIDDEN | Button not visible on page (likely  |
| 522 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 523 | unnamed | HIDDEN | Button not visible on page (likely  |
| 524 | unnamed | HIDDEN | Button not visible on page (likely  |
| 525 | Signup | HIDDEN | Button not visible on page (likely  |
| 526 | Active | HIDDEN | Button not visible on page (likely  |
| 527 | Paused | HIDDEN | Button not visible on page (likely  |
| 528 | Complete | HIDDEN | Button not visible on page (likely  |
| 529 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 530 | unnamed | HIDDEN | Button not visible on page (likely  |
| 531 | unnamed | HIDDEN | Button not visible on page (likely  |
| 532 | Signup | HIDDEN | Button not visible on page (likely  |
| 533 | Active | HIDDEN | Button not visible on page (likely  |
| 534 | Paused | HIDDEN | Button not visible on page (likely  |
| 535 | Complete | HIDDEN | Button not visible on page (likely  |
| 536 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 537 | unnamed | HIDDEN | Button not visible on page (likely  |
| 538 | unnamed | HIDDEN | Button not visible on page (likely  |
| 539 | Signup | HIDDEN | Button not visible on page (likely  |
| 540 | Active | HIDDEN | Button not visible on page (likely  |
| 541 | Paused | HIDDEN | Button not visible on page (likely  |
| 542 | Complete | HIDDEN | Button not visible on page (likely  |
| 543 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 544 | unnamed | HIDDEN | Button not visible on page (likely  |
| 545 | unnamed | HIDDEN | Button not visible on page (likely  |
| 546 | Signup | HIDDEN | Button not visible on page (likely  |
| 547 | Active | HIDDEN | Button not visible on page (likely  |
| 548 | Paused | HIDDEN | Button not visible on page (likely  |
| 549 | Complete | HIDDEN | Button not visible on page (likely  |
| 550 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 551 | unnamed | HIDDEN | Button not visible on page (likely  |
| 552 | unnamed | HIDDEN | Button not visible on page (likely  |
| 553 | Signup | HIDDEN | Button not visible on page (likely  |
| 554 | Active | HIDDEN | Button not visible on page (likely  |
| 555 | Paused | HIDDEN | Button not visible on page (likely  |
| 556 | Complete | HIDDEN | Button not visible on page (likely  |
| 557 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 558 | unnamed | HIDDEN | Button not visible on page (likely  |
| 559 | unnamed | HIDDEN | Button not visible on page (likely  |
| 560 | Signup | HIDDEN | Button not visible on page (likely  |
| 561 | Active | HIDDEN | Button not visible on page (likely  |
| 562 | Paused | HIDDEN | Button not visible on page (likely  |
| 563 | Complete | HIDDEN | Button not visible on page (likely  |
| 564 | Cancelled | HIDDEN | Button not visible on page (likely  |
| 565 | unnamed | HIDDEN | Button not visible on page (likely  |
| 566 | unnamed | HIDDEN | Button not visible on page (likely  |
| 567 | × | HIDDEN | Button not visible on page (likely  |

### /dashboard/settlements
Found: 21 buttons | Tested: 21

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Clear Filters | WORKING | Opens modal |
| 1 | View | WORKING | Opens modal |
| 2 | + Offer | NOT_BUILT | Click timeout - may not be wired up |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 18 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 19 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 20 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/credit-tracker
Found: 44 buttons | Tested: 44

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Quick Estimate | WORKING | Has onclick: switchTab('quick') |
| 1 | Detailed Calculator | WORKING | Has onclick: switchTab('detailed') |
| 2 | Client Progress | WORKING | Has onclick: switchTab('clients') |
| 3 | Calculate Estimate | HIDDEN | Button not visible on page (likely  |
| 4 | Calculate Detailed Estima | HIDDEN | Button not visible on page (likely  |
| 5 | + Add | HIDDEN | Button not visible on page (likely  |
| 6 | + Add | HIDDEN | Button not visible on page (likely  |
| 7 | + Add | HIDDEN | Button not visible on page (likely  |
| 8 | + Add | HIDDEN | Button not visible on page (likely  |
| 9 | + Add | HIDDEN | Button not visible on page (likely  |
| 10 | + Add | HIDDEN | Button not visible on page (likely  |
| 11 | + Add | HIDDEN | Button not visible on page (likely  |
| 12 | + Add | HIDDEN | Button not visible on page (likely  |
| 13 | + Add | HIDDEN | Button not visible on page (likely  |
| 14 | + Add | HIDDEN | Button not visible on page (likely  |
| 15 | + Add | HIDDEN | Button not visible on page (likely  |
| 16 | + Add | HIDDEN | Button not visible on page (likely  |
| 17 | + Add | HIDDEN | Button not visible on page (likely  |
| 18 | + Add | HIDDEN | Button not visible on page (likely  |
| 19 | + Add | HIDDEN | Button not visible on page (likely  |
| 20 | + Add | HIDDEN | Button not visible on page (likely  |
| 21 | + Add | HIDDEN | Button not visible on page (likely  |
| 22 | + Add | HIDDEN | Button not visible on page (likely  |
| 23 | + Add | HIDDEN | Button not visible on page (likely  |
| 24 | + Add | HIDDEN | Button not visible on page (likely  |
| 25 | + Add | HIDDEN | Button not visible on page (likely  |
| 26 | + Add | HIDDEN | Button not visible on page (likely  |
| 27 | + Add | HIDDEN | Button not visible on page (likely  |
| 28 | + Add | HIDDEN | Button not visible on page (likely  |
| 29 | + Add | HIDDEN | Button not visible on page (likely  |
| 30 | + Add | HIDDEN | Button not visible on page (likely  |
| 31 | + Add | HIDDEN | Button not visible on page (likely  |
| 32 | + Add | HIDDEN | Button not visible on page (likely  |
| 33 | + Add | HIDDEN | Button not visible on page (likely  |
| 34 | + Add | HIDDEN | Button not visible on page (likely  |
| 35 | + Add | HIDDEN | Button not visible on page (likely  |
| 36 | + Add | HIDDEN | Button not visible on page (likely  |
| 37 | + Add | HIDDEN | Button not visible on page (likely  |
| 38 | + Add | HIDDEN | Button not visible on page (likely  |
| 39 | + Add | HIDDEN | Button not visible on page (likely  |
| 40 | + Add | HIDDEN | Button not visible on page (likely  |
| 41 | + Add | HIDDEN | Button not visible on page (likely  |
| 42 | + Add | HIDDEN | Button not visible on page (likely  |
| 43 | + Add | HIDDEN | Button not visible on page (likely  |

### /dashboard/calendar
Found: 10 buttons | Tested: 10

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | unnamed | WORKING | Opens modal |
| 1 | unnamed | WORKING | Opens modal |
| 2 | today | DISABLED | Button is disabled |
| 3 | month | WORKING | Opens modal |
| 4 | week | WORKING | Opens modal |
| 5 | list | WORKING | Opens modal |
| 6 | Apply Filters | WORKING | Opens modal |
| 7 | Clear Filters | WORKING | Opens modal |
| 8 | × | HIDDEN | Button not visible on page (likely  |
| 9 | Close | HIDDEN | Button not visible on page (likely  |

### /dashboard/contacts
Found: 28 buttons | Tested: 28

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Add Contact | WORKING | Opens modal |
| 1 | ADD CONTACT | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 18 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 19 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 20 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 21 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 22 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 23 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 24 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 25 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 26 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 27 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/automation-tools
Found: 37 buttons | Tested: 37

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | FREEZE LETTERS | WORKING | Has onclick: switchTab('freeze-lett |
| 1 | VALIDATION LETTERS | WORKING | Has onclick: switchTab('validation- |
| 2 | DEADLINES | WORKING | Has onclick: switchTab('deadlines') |
| 3 | DISPUTE ROUNDS | WORKING | Has onclick: switchTab('dispute-rou |
| 4 | SETTLEMENT CALCULATOR | WORKING | Has onclick: switchTab('settlement- |
| 5 | CERTIFIED MAIL | WORKING | Has onclick: switchTab('certified-m |
| 6 | NOTARIZATION | WORKING | Has onclick: switchTab('notarizatio |
| 7 | ADVANCED LETTERS | WORKING | Has onclick: switchTab('advanced-le |
| 8 | Select All Primary | HIDDEN | Button not visible on page (likely  |
| 9 | Select All Secondary | HIDDEN | Button not visible on page (likely  |
| 10 | Clear All | HIDDEN | Button not visible on page (likely  |
| 11 | Generate Freeze Letters | HIDDEN | Button not visible on page (likely  |
| 12 | Generate Validation Lette | HIDDEN | Button not visible on page (likely  |
| 13 | Auto-Generate from Case A | HIDDEN | Button not visible on page (likely  |
| 14 | All | HIDDEN | Button not visible on page (likely  |
| 15 | Overdue | HIDDEN | Button not visible on page (likely  |
| 16 | This Week | HIDDEN | Button not visible on page (likely  |
| 17 | This Month | HIDDEN | Button not visible on page (likely  |
| 18 | Advance to Selected Round | HIDDEN | Button not visible on page (likely  |
| 19 | Add Damage Item | HIDDEN | Button not visible on page (likely  |
| 20 | Calculate Settlement | HIDDEN | Button not visible on page (likely  |
| 21 | Generate RESPA QWR Letter | HIDDEN | Button not visible on page (likely  |
| 22 | Preview Letter | HIDDEN | Button not visible on page (likely  |
| 23 | Generate Reg Z Dispute Le | HIDDEN | Button not visible on page (likely  |
| 24 | Preview Letter | HIDDEN | Button not visible on page (likely  |
| 25 | Generate FDCPA Validation | HIDDEN | Button not visible on page (likely  |
| 26 | Preview Letter | HIDDEN | Button not visible on page (likely  |
| 27 | Generate §605B Block Requ | HIDDEN | Button not visible on page (likely  |
| 28 | Preview Letter | HIDDEN | Button not visible on page (likely  |
| 29 | Generate §623 Direct Disp | HIDDEN | Button not visible on page (likely  |
| 30 | Preview Letter | HIDDEN | Button not visible on page (likely  |
| 31 | Generate Reinsertion Chal | HIDDEN | Button not visible on page (likely  |
| 32 | Preview Letter | HIDDEN | Button not visible on page (likely  |
| 33 | Generate MOV Request Lett | HIDDEN | Button not visible on page (likely  |
| 34 | Preview Letter | HIDDEN | Button not visible on page (likely  |
| 35 | Close Preview | HIDDEN | Button not visible on page (likely  |
| 36 | Download PDF | HIDDEN | Button not visible on page (likely  |

### /dashboard/letter-queue
Found: 8 buttons | Tested: 8

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Run Trigger Check | WORKING | Opens modal |
| 1 | Approve Selected (
0
) | DISABLED | Button is disabled |
| 2 | Download PDF | WORKING | Opens modal |
| 3 | Print | WORKING | Opens modal |
| 4 | Mark as Sent | WORKING | Opens modal |
| 5 | Resend | WORKING | Opens modal |
| 6 | Cancel | HIDDEN | Button not visible on page (likely  |
| 7 | Dismiss Letter | HIDDEN | Button not visible on page (likely  |

### /dashboard/demand-generator
Found: 2 buttons | Tested: 2

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Generate AI Demand Letter | HIDDEN | Button not visible on page (likely  |
| 1 | Copy Text | HIDDEN | Button not visible on page (likely  |

### /dashboard/import
Found: 3 buttons | Tested: 3

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Import Client | WORKING | Submit button (form submission) |
| 1 | Clear Form | WORKING | Has onclick: document.getElementByI |
| 2 | Delete Report | DANGEROUS_SAFE | Clicked and cancelled safely |

### /dashboard/documents
Found: 18 buttons | Tested: 18

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Upload Document | WORKING | Opens modal |
| 1 | Review | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/settings
Found: 2 buttons | Tested: 2

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Cancel | WORKING | Has onclick: window.location.reload |
| 1 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/integrations
Found: 12 buttons | Tested: 12

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Refresh All | WORKING | Opens modal |
| 1 | Configure | WORKING | Opens modal |
| 2 | Test Connection | NOT_BUILT | Click timeout - may not be wired up |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/billing
Found: 14 buttons | Tested: 14

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Create Plan | WORKING | Opens modal |
| 1 | Initialize Default Plans | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/tasks
Found: 58 buttons | Tested: 58

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Refresh | WORKING | Opens modal |
| 1 | Process Tasks | WORKING | Opens modal |
| 2 | New Task | NOT_BUILT | Click timeout - may not be wired up |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 18 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 19 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 20 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 21 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 22 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 23 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 24 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 25 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 26 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 27 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 28 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 29 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 30 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 31 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 32 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 33 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 34 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 35 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 36 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 37 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 38 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 39 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 40 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 41 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 42 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 43 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 44 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 45 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 46 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 47 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 48 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 49 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 50 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 51 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 52 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 53 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 54 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 55 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 56 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 57 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/workflows
Found: 54 buttons | Tested: 54

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Refresh | WORKING | Opens modal |
| 1 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 18 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 19 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 20 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 21 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 22 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 23 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 24 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 25 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 26 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 27 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 28 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 29 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 30 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 31 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 32 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 33 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 34 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 35 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 36 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 37 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 38 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 39 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 40 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 41 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 42 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 43 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 44 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 45 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 46 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 47 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 48 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 49 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 50 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 51 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 52 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 53 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/ml-insights
Found: 6 buttons | Tested: 6

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Refresh Patterns | WORKING | Opens modal |
| 1 | Record Outcome | WORKING | Opens modal |
| 2 | Record First Outcome | WORKING | Opens modal |
| 3 | unnamed | HIDDEN | Button not visible on page (likely  |
| 4 | Cancel | HIDDEN | Button not visible on page (likely  |
| 5 | Record Outcome | HIDDEN | Button not visible on page (likely  |

### /dashboard/white-label
Found: 30 buttons | Tested: 30

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Add Tenant | WORKING | Opens modal |
| 1 | unnamed | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 18 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 19 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 20 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 21 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 22 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 23 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 24 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 25 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 26 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 27 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 28 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 29 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/franchise
Found: 17 buttons | Tested: 17

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | New Organization | WORKING | Opens modal |
| 1 | Create Organization | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/affiliates
Found: 18 buttons | Tested: 18

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Add Affiliate | WORKING | Opens modal |
| 1 | All | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/triage
Found: 8 buttons | Tested: 8

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Refresh | WORKING | Opens modal |
| 1 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/case-law
Found: 21 buttons | Tested: 21

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Populate Default Cases | WORKING | Opens modal |
| 1 | Add Citation | WORKING | Opens modal |
| 2 | Copy Short | NOT_BUILT | Click timeout - may not be wired up |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 18 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 19 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 20 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/sops
Found: 1 buttons | Tested: 1

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | unnamed | HIDDEN | Button not visible on page (likely  |

### /dashboard/chexsystems
Found: 5 buttons | Tested: 5

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | New Dispute | WORKING | Opens modal |
| 1 | Create First Dispute | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/specialty-bureaus
Found: 23 buttons | Tested: 23

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | New Dispute | WORKING | Opens modal |
| 1 | View Disputes | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 15 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 16 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 17 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 18 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 19 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 20 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 21 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 22 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/furnishers
Found: 5 buttons | Tested: 5

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Sync from Cases | WORKING | Opens modal |
| 1 | Add Furnisher | WORKING | Opens modal |
| 2 | × | WORKING | Opens modal |
| 3 | Cancel | HIDDEN | Button not visible on page (likely  |
| 4 | Save Furnisher | HIDDEN | Button not visible on page (likely  |

### /dashboard/patterns
Found: 15 buttons | Tested: 15

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | New Pattern | WORKING | Opens modal |
| 1 | Create First Pattern | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 12 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 13 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 14 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/sol
Found: 5 buttons | Tested: 5

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Check Deadlines | BROKEN | Click error: Page.evaluate: Executi |
| 1 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/cfpb
Found: 5 buttons | Tested: 5

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | All | WORKING | Has onclick: filterComplaints('all' |
| 1 | Draft | WORKING | Has onclick: filterComplaints('draf |
| 2 | Ready | WORKING | Has onclick: filterComplaints('read |
| 3 | Submitted | WORKING | Has onclick: filterComplaints('subm |
| 4 | Response Received | WORKING | Has onclick: filterComplaints('resp |

### /dashboard/frivolousness
Found: 7 buttons | Tested: 7

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Add Defense Case | WORKING | Opens modal |
| 1 | × | WORKING | Opens modal |
| 2 | Cancel | HIDDEN | Button not visible on page (likely  |
| 3 | Add Case | HIDDEN | Button not visible on page (likely  |
| 4 | × | HIDDEN | Button not visible on page (likely  |
| 5 | Cancel | HIDDEN | Button not visible on page (likely  |
| 6 | Save Changes | HIDDEN | Button not visible on page (likely  |

### /dashboard/credit-import
Found: 5 buttons | Tested: 5

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Import All Due | WORKING | Opens modal |
| 1 | Add Credential | WORKING | Opens modal |
| 2 | × | HIDDEN | Button not visible on page (likely  |
| 3 | Cancel | HIDDEN | Button not visible on page (likely  |
| 4 | Save Credential | HIDDEN | Button not visible on page (likely  |

### /dashboard/performance
Found: 5 buttons | Tested: 5

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Refresh | WORKING | Opens modal |
| 1 | Clear Cache | WORKING | Opens modal |
| 2 | × | WORKING | Opens modal |
| 3 | Cancel | HIDDEN | Button not visible on page (likely  |
| 4 | Clear Cache | HIDDEN | Button not visible on page (likely  |

### /dashboard/settings/sms
Found: 3 buttons | Tested: 3

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | 📤 Send Test | WORKING | Shows success message |
| 1 | Cancel | WORKING | Shows success message |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |


---

## Conclusion

- **Total Buttons Found:** 1691
- **Total Buttons Tested:** 1691
- **Working:** 79 (4.7%)
- **Need Building:** 14
- **Need Fixing:** 368
- **Hidden (in modals):** 1227
- **Disabled:** 2
- **Dangerous (tested safely):** 1

