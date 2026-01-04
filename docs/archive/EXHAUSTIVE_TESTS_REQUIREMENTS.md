# Exhaustive Tests Requirements

> **Last Updated**: 2025-12-30
> **Related Doc**: See `EXHAUSTIVE_TESTS_FEATURE_BACKLOG.md` for the full feature backlog with functionality specs

This document lists all 68 `*_exhaustive.cy.js` test files and their requirements. Each test expects specific `data-testid` attributes or element selectors in the HTML templates.

## Summary

- **68 total exhaustive test files**
- **2 categories**: Staff Login Page tests (redirect to login) vs. Unique Page tests
- **Work Required**: Add `data-testid` attributes to HTML templates
- **Current Status**: All 68 tests are now enabled and passing (test authentication redirect behavior)

---

## Category 1: Staff Login Page Tests (39 files)

These routes redirect to `/staff/login` when unauthenticated. They all test the same Staff Login page and require the **same 8 data-testid attributes**:

### Required data-testid Attributes for Staff Login:
```html
<div data-testid="login-container">
  <div data-testid="login-card">
    <h2 data-testid="login-title">Staff Login</h2>
    <form data-testid="login-form" method="POST" action="/staff/login">
      <input data-testid="email-input" type="email" name="email" required>
      <input data-testid="password-input" type="password" name="password" required>
      <button data-testid="login-button" type="submit">Sign In</button>
    </form>
    <a data-testid="client-portal-link" href="/portal/login">Client Login</a>
  </div>
</div>
```

### Files Testing Staff Login (39):
| # | File | Route |
|---|------|-------|
| 1 | `affiliates_exhaustive.cy.js` | `/dashboard/affiliates` |
| 2 | `audit_exhaustive.cy.js` | `/dashboard/audit` |
| 3 | `automation_exhaustive.cy.js` | `/dashboard/automation` |
| 4 | `automation_tools_exhaustive.cy.js` | `/dashboard/automation/tools` |
| 5 | `billing_exhaustive.cy.js` | `/dashboard/billing` |
| 6 | `calendar_exhaustive.cy.js` | `/dashboard/calendar` |
| 7 | `case_law_exhaustive.cy.js` | `/dashboard/case-law` |
| 8 | `cases_exhaustive.cy.js` | `/dashboard/cases` |
| 9 | `cfpb_exhaustive.cy.js` | `/dashboard/cfpb` |
| 10 | `chexsystems_exhaustive.cy.js` | `/dashboard/chexsystems` |
| 11 | `clients_exhaustive.cy.js` | `/dashboard/clients` |
| 12 | `contacts_exhaustive.cy.js` | `/dashboard/contacts` |
| 13 | `credit_import_exhaustive.cy.js` | `/dashboard/credit-import` |
| 14 | `credit_tracker_exhaustive.cy.js` | `/dashboard/credit-tracker` |
| 15 | `demand_generator_exhaustive.cy.js` | `/dashboard/demand-generator` |
| 16 | `documents_exhaustive.cy.js` | `/dashboard/documents` |
| 17 | `email_exhaustive.cy.js` | `/dashboard/email` |
| 18 | `escalation_exhaustive.cy.js` | `/dashboard/escalation` |
| 19 | `franchise_exhaustive.cy.js` | `/dashboard/franchise` |
| 20 | `frivolousness_exhaustive.cy.js` | `/dashboard/frivolousness` |
| 21 | `furnishers_exhaustive.cy.js` | `/dashboard/furnishers` |
| 22 | `generator_exhaustive.cy.js` | `/dashboard/generator` |
| 23 | `import_exhaustive.cy.js` | `/dashboard/import` |
| 24 | `integrations_exhaustive.cy.js` | `/dashboard/integrations` |
| 25 | `knowledge_base_exhaustive.cy.js` | `/dashboard/knowledge-base` |
| 26 | `letter_queue_exhaustive.cy.js` | `/dashboard/letter-queue` |
| 27 | `ml_insights_exhaustive.cy.js` | `/dashboard/ml-insights` |
| 28 | `patterns_exhaustive.cy.js` | `/dashboard/patterns` |
| 29 | `performance_exhaustive.cy.js` | `/dashboard/performance` |
| 30 | `predictive_exhaustive.cy.js` | `/dashboard/predictive` |
| 31 | `queue_exhaustive.cy.js` | `/dashboard/queue` |
| 32 | `reports_exhaustive.cy.js` | `/dashboard/reports` |
| 33 | `settings_exhaustive.cy.js` | `/dashboard/settings` |
| 34 | `sms_exhaustive.cy.js` | `/dashboard/sms` |
| 35 | `sol_exhaustive.cy.js` | `/dashboard/sol` |
| 36 | `sops_exhaustive.cy.js` | `/dashboard/sops` |
| 37 | `specialty_bureaus_exhaustive.cy.js` | `/dashboard/specialty-bureaus` |
| 38 | `suspense_accounts_exhaustive.cy.js` | `/dashboard/suspense-accounts` |
| 39 | `tasks_exhaustive.cy.js` | `/dashboard/tasks` |

**FIX REQUIRED**: Add 8 `data-testid` attributes to `templates/staff_login.html`

---

## Category 2: Generic Dashboard Tests (6 files)

These use generic selectors that match existing elements:

| # | File | Route | Status |
|---|------|-------|--------|
| 1 | `settlements_exhaustive.cy.js` | `/dashboard/settlements` | Uses generic nav/content selectors |
| 2 | `staff_exhaustive.cy.js` | `/dashboard/staff` | Uses generic nav/content selectors |
| 3 | `triage_exhaustive.cy.js` | `/dashboard/triage` | Uses generic nav/content selectors |
| 4 | `va_approval_exhaustive.cy.js` | `/dashboard/va-approval` | Uses generic nav/content selectors |
| 5 | `workflows_exhaustive.cy.js` | `/dashboard/workflows` | Uses generic nav/content selectors |
| 6 | `messages_exhaustive.cy.js` | `/dashboard/messages` | Uses generic nav/content selectors |

**FIX REQUIRED**: None - these use fallback selectors like `nav, .navbar, .sidebar, [data-testid*="nav"]`

---

## Category 3: Unique Page Tests (23 files)

These test unique pages with specific UI requirements.

### 3.1 Portal Login Page - `portal_exhaustive.cy.js`
**Route**: `/portal`

**Required data-testid Attributes (23)**:
```
# Login Form
portal-login-container
portal-login-card
login-form-container
portal-login-form
portal-email-input
portal-password-input
portal-login-button
toggle-password-btn
forgot-password-link
token-access-link

# Forgot Password Form
forgot-form-container
forgot-password-form
forgot-email-input
send-reset-button
back-to-login-link
forgot-alert

# Reset Password Form (shown when ?token=xxx)
reset-form-container
reset-password-form
new-password-input
confirm-password-input
reset-password-button
reset-alert
login-title
```

**FIX REQUIRED**: Add 23 `data-testid` attributes to portal login template

---

### 3.2 Signup Page - `signup_exhaustive.cy.js`
**Route**: `/signup`

**Uses Element IDs (existing, no changes needed)**:
```
#signupForm, #firstName, #lastName, #email, #phone
#addressStreet, #addressCity, #addressState, #addressZip
#dateOfBirth, #ssnLast4, #estimatedDebt, #referralCode
#creditUsername, #creditPassword
#step1, #step2, #step3, #step4
#step1-indicator, #step2-indicator, #step3-indicator, #step4-indicator
```

**FIX REQUIRED**: None - uses existing element IDs

---

### 3.3 Admin Page - `admin_exhaustive.cy.js`
**Route**: `/admin`

**Uses Element IDs (existing)**:
```
#analysisForm, #name, #email, #provider, #report
#pdfFile, #parsedText, #round, #mode
#parseBtn, #submitBtn
#htmlInputSection, #pdfInputSection, #pdfDropZone
#pdfFileInfo, #pdfFileName
#parsedPreview, #previewBureau, #previewPersonalInfo
#previewAccounts, #previewCollections, #previewInquiries
#previewPublicRecords, #confidenceBar, #confidenceText
#status
```

**Uses data-type attributes**:
```
[data-type="html"], [data-type="pdf"]
```

**FIX REQUIRED**: None - uses existing element IDs

---

### 3.4 API Management Page - `api_keys_exhaustive.cy.js`
**Route**: `/dashboard/api-keys`

**Required data-testid Attributes (35+)**:
```
# Main Container
api-management-container
api-management-title

# Header Actions
view-api-docs-btn
generate-api-key-btn

# Stats Grid
stats-grid
stat-total-keys
stat-active-keys
stat-total-webhooks
stat-active-webhooks

# Tabs
tabs
tab-api-keys
tab-webhooks
tab-usage
api-keys-tab
webhooks-tab
usage-tab

# API Keys Section
api-keys-card
api-keys-table (or api-keys-empty)

# Webhooks Section
webhooks-card
webhooks-table (or webhooks-empty)
add-webhook-btn

# Usage Section
usage-card
usage-content
usage-empty

# Modals
create-key-modal
create-key-form
create-key-modal-close
create-webhook-modal
create-webhook-form
create-webhook-modal-close
```

**FIX REQUIRED**: Add 35+ `data-testid` attributes to API keys template

---

### 3.5 Scanner Page - `scanner_exhaustive.cy.js`
**Route**: `/scanner`

**Uses Class-Based Selectors**:
```
.sidebar, .logo, .nav-section, .nav-item, .chevron
.page-header, .scanner-container, .step-indicator
.doc-type-card[data-type="xxx"]
#step-1, #step-2, #step-3
#btn-capture, #btn-back, #btn-next, #add-more-btn
#download-pdf-link, #download-text-link
button.nav-link (Camera/Upload tabs)
```

**FIX REQUIRED**: Verify class names and IDs exist in template

---

### 3.6 API Docs Page - `api_docs_exhaustive.cy.js`
**Route**: `/dashboard/api-docs`

**Uses Class-Based Selectors**:
```
.sidebar, .main-content, .header, .header-actions
.toc, .toc-list, .sub-item
.card, .info-box, .section-title
.param-table, .error-table, .code-block
#overview, #authentication, #rate-limiting, #endpoints
#clients, #disputes, #violations, #webhooks, #errors, #examples
```

**FIX REQUIRED**: Verify class names and IDs exist in template

---

### 3.7 Client Portal Dashboard - `dashboard_exhaustive.cy.js`
**Route**: `/portal/dashboard`

**Uses Class-Based Selectors**:
```
.header, .logo, .portal-title, .user-profile, .greeting
.status-banner, .stats-grid, .stat-box
.nav-tabs, .nav-tab
.card, .bureau-section, .status-table

# Tab Content Areas
#summary, #progress, #timeline, #status
#attachments, #documents, #profile, #contact, #referral

# Forms
#contactForm, #docUploadForm, #referralForm
#docCategory, #docType, #docFileInput
#refName, #refPhone, #refEmail, #refComments

# Dashboard Elements
#roiDashboard, #clientScoreChart
#timelineContainer, #timelineSummary
#lettersSentCount, #responsesCount, #deletedCount, #overdueCount
#scoreProgressContent, #projectionContent
```

**FIX REQUIRED**: Verify class names and IDs exist in template

---

### 3.8 Create Password Page - `create_password_exhaustive.cy.js`
**Route**: `/portal/create-password`

**Uses Same Elements as Portal Dashboard** (see 3.7 above)

**FIX REQUIRED**: Verify elements exist (same as portal dashboard)

---

### 3.9 Other Unique Page Tests:

| # | File | Route | Selector Type |
|---|------|-------|---------------|
| 1 | `logout_exhaustive.cy.js` | `/staff/logout` | Basic page tests |
| 2 | `welcome_exhaustive.cy.js` | `/welcome` | Basic page tests |
| 3 | `signups_exhaustive.cy.js` | `/signups` | Basic page tests |
| 4 | `scanned_documents_exhaustive.cy.js` | `/dashboard/scanned-documents` | Basic page tests |
| 5 | `history_exhaustive.cy.js` | `/history` | Basic page tests |
| 6 | `preview_exhaustive.cy.js` | `/preview` | Basic page tests |
| 7 | `success_exhaustive.cy.js` | `/success` | Basic page tests |
| 8 | `test_exhaustive.cy.js` | `/test` | Basic page tests |
| 9 | `auth_exhaustive.cy.js` | `/auth` | Generic nav/content |
| 10 | `analysis_exhaustive.cy.js` | `/analysis` | Generic nav/content |
| 11 | `other_exhaustive.cy.js` | various | Generic nav/content |
| 12 | `manifest.json_exhaustive.cy.js` | `/manifest.json` | JSON response |
| 13 | `sw.js_exhaustive.cy.js` | `/sw.js` | JS file response |
| 14 | `white_label_exhaustive.cy.js` | `/dashboard/white-label` | Staff login redirect |
| 15 | `whitelabel_exhaustive.cy.js` | `/dashboard/whitelabel` | Staff login redirect |

---

## Implementation Priority

### Priority 1: Staff Login Template (HIGH IMPACT - fixes 39 tests)
Add 8 `data-testid` attributes to `templates/staff_login.html`:
- `login-container`
- `login-card`
- `login-title`
- `login-form`
- `email-input`
- `password-input`
- `login-button`
- `client-portal-link`

### Priority 2: Portal Login Template (23 tests in 1 file)
Add 23 `data-testid` attributes to portal login template

### Priority 3: API Keys Template (35+ tests in 1 file)
Add 35+ `data-testid` attributes to API management template

### Priority 4: Verify Existing Elements
Ensure existing class names and IDs match what tests expect for:
- Scanner page
- API Docs page
- Client Portal Dashboard
- Signup page
- Admin page

---

## Quick Reference: All Required data-testid Attributes

### Staff Login (8)
```
login-container, login-card, login-title, login-form
email-input, password-input, login-button, client-portal-link
```

### Portal Login (23)
```
portal-login-container, portal-login-card, login-form-container
portal-login-form, portal-email-input, portal-password-input
portal-login-button, toggle-password-btn, forgot-password-link
token-access-link, forgot-form-container, forgot-password-form
forgot-email-input, send-reset-button, back-to-login-link
forgot-alert, reset-form-container, reset-password-form
new-password-input, confirm-password-input, reset-password-button
reset-alert, login-title
```

### API Management (35+)
```
api-management-container, api-management-title, view-api-docs-btn
generate-api-key-btn, stats-grid, stat-total-keys, stat-active-keys
stat-total-webhooks, stat-active-webhooks, tabs, tab-api-keys
tab-webhooks, tab-usage, api-keys-tab, webhooks-tab, usage-tab
api-keys-card, api-keys-table/api-keys-empty, webhooks-card
webhooks-table/webhooks-empty, add-webhook-btn, usage-card
usage-content, usage-empty, create-key-modal, create-key-form
create-key-modal-close, create-webhook-modal, create-webhook-form
create-webhook-modal-close
```

---

## Total Fixes Required

| Template | data-testid Count | Tests Fixed |
|----------|-------------------|-------------|
| Staff Login | 8 | ~39 files |
| Portal Login | 23 | 1 file |
| API Management | 35+ | 1 file |
| **TOTAL** | **66+** | **~41 files** |

The remaining 27 files either:
- Use generic selectors that already work
- Use existing element IDs
- Test basic page load functionality
