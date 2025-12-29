# BUTTON INVENTORY - COMPLETE STATUS REPORT

**Date:** 2025-12-29T01:40:15.793630
**Purpose:** Know exactly what works, what's broken, what needs building

---

## Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Buttons Found | 463 | - |
| Buttons Tested | 463 | 100% |
| WORKING | 79 | 17.1% |
| NOT BUILT | 12 | 2.6% |
| BROKEN | 242 | 52.3% |
| DISABLED | 2 | 0.4% |
| HIDDEN | 127 | 27.4% |
| DANGEROUS (tested safely) | 1 | 0.2% |

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
| /dashboard/contacts | ADD CONTACT | Click timeout - may not be wired up |
| /dashboard/integrations | Test Connection | Click timeout - may not be wired up |
| /dashboard/billing | Initialize Default Plans | Click timeout - may not be wired up |
| /dashboard/tasks | New Task | Click timeout - may not be wired up |
| /dashboard/white-label | Create First Tenant | Click timeout - may not be wired up |
| /dashboard/franchise | Create Organization | Click timeout - may not be wired up |
| /dashboard/affiliates | All | Click timeout - may not be wired up |
| /dashboard/case-law | Populate Default Cases | Click timeout - may not be wired up |
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
| /dashboard/contacts | unnamed | ElementHandle.inner_text: Execution cont |
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
Found: 13 buttons | Tested: 13

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

### /dashboard/clients
Found: 8 buttons | Tested: 8

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Apply | HIDDEN | Button not visible on page (likely  |
| 1 | Delete Selected | HIDDEN | Button not visible on page (likely  |
| 2 | ALL | WORKING | Has onclick: quickFilter('all') |
| 3 | ACTIVE | WORKING | Has onclick: quickFilter('active') |
| 4 | LEADS | WORKING | Has onclick: quickFilter('leads') |
| 5 | FOLLOW UP | WORKING | Has onclick: quickFilter('followup' |
| 6 | SIGNUPS | WORKING | Has onclick: quickFilter('signups') |
| 7 | × | HIDDEN | Button not visible on page (likely  |

### /dashboard/cases
Found: 8 buttons | Tested: 8

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Apply | HIDDEN | Button not visible on page (likely  |
| 1 | Delete Selected | HIDDEN | Button not visible on page (likely  |
| 2 | ALL | WORKING | Has onclick: quickFilter('all') |
| 3 | ACTIVE | WORKING | Has onclick: quickFilter('active') |
| 4 | LEADS | WORKING | Has onclick: quickFilter('leads') |
| 5 | FOLLOW UP | WORKING | Has onclick: quickFilter('followup' |
| 6 | SIGNUPS | WORKING | Has onclick: quickFilter('signups') |
| 7 | × | HIDDEN | Button not visible on page (likely  |

### /dashboard/settlements
Found: 13 buttons | Tested: 13

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Clear Filters | WORKING | Opens modal |
| 1 | × | HIDDEN | Button not visible on page (likely  |
| 2 | Cancel | HIDDEN | Button not visible on page (likely  |
| 3 | Save Changes | HIDDEN | Button not visible on page (likely  |
| 4 | × | HIDDEN | Button not visible on page (likely  |
| 5 | Cancel | HIDDEN | Button not visible on page (likely  |
| 6 | Add Offer | HIDDEN | Button not visible on page (likely  |
| 7 | × | HIDDEN | Button not visible on page (likely  |
| 8 | Cancel | HIDDEN | Button not visible on page (likely  |
| 9 | Confirm Settlement | HIDDEN | Button not visible on page (likely  |
| 10 | × | HIDDEN | Button not visible on page (likely  |
| 11 | Cancel | HIDDEN | Button not visible on page (likely  |
| 12 | Record Payment | HIDDEN | Button not visible on page (likely  |

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
Found: 29 buttons | Tested: 29

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
| 28 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

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
Found: 10 buttons | Tested: 10

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Upload Document | WORKING | Opens modal |
| 1 | × | WORKING | Opens modal |
| 2 | CRA Response | HIDDEN | Button not visible on page (likely  |
| 3 | Collection Letter | HIDDEN | Button not visible on page (likely  |
| 4 | Legal/Lawsuit | HIDDEN | Button not visible on page (likely  |
| 5 | Credit Report | HIDDEN | Button not visible on page (likely  |
| 6 | ID/Proof | HIDDEN | Button not visible on page (likely  |
| 7 | Other | HIDDEN | Button not visible on page (likely  |
| 8 | Back | HIDDEN | Button not visible on page (likely  |
| 9 | Next | HIDDEN | Button not visible on page (likely  |

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
Found: 5 buttons | Tested: 5

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Create Plan | WORKING | Opens modal |
| 1 | Initialize Default Plans | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

### /dashboard/tasks
Found: 50 buttons | Tested: 50

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
Found: 11 buttons | Tested: 11

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Add Tenant | WORKING | Opens modal |
| 1 | Create First Tenant | NOT_BUILT | Click timeout - may not be wired up |
| 2 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

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
Found: 9 buttons | Tested: 9

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
Found: 12 buttons | Tested: 12

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 0 | Populate Default Cases | WORKING | Opens modal |
| 1 | Add Citation | WORKING | Opens modal |
| 2 | Populate Default Cases | NOT_BUILT | Click timeout - may not be wired up |
| 3 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 4 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 5 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 6 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 7 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 8 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 9 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 10 | unnamed | BROKEN | ElementHandle.inner_text: Execution |
| 11 | unnamed | BROKEN | ElementHandle.inner_text: Execution |

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

- **Total Buttons Found:** 463
- **Total Buttons Tested:** 463
- **Working:** 79 (17.1%)
- **Need Building:** 12
- **Need Fixing:** 242
- **Hidden (in modals):** 127
- **Disabled:** 2
- **Dangerous (tested safely):** 1

