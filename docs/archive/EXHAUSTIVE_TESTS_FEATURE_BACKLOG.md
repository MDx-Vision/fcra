# Exhaustive Tests Feature Backlog

> Reverse-engineered from 68 Cypress exhaustive test files in `cypress/e2e/*_exhaustive.cy.js`
>
> Generated: 2025-12-30
>
> **Related Doc**: See `EXHAUSTIVE_TESTS_REQUIREMENTS.md` for implementation-focused data-testid requirements

## Overview

This document catalogs all features and UI elements specified in the exhaustive test suite. These tests define the intended functionality of the Brightpath Ascend FCRA Platform.

### Key Discovery

Most dashboard route test files (e.g., `/dashboard/clients`, `/dashboard/billing`) test the **Staff Login Page** because unauthenticated users are redirected to `/staff/login`. This means:
- The Staff Login page is fully specified and tested
- Dashboard-specific pages need to be built with authenticated test patterns

---

## Table of Contents

1. [Staff Login Page](#1-staff-login-page)
2. [Client Portal Login](#2-client-portal-login)
3. [API Management](#3-api-management)
4. [API Documentation](#4-api-documentation)
5. [PWA Assets](#5-pwa-assets)
6. [Dashboard Routes (Pending Implementation)](#6-dashboard-routes-pending-implementation)

---

## 1. Staff Login Page

**Route:** `/staff/login` (also tested via redirects from all `/dashboard/*` routes)
**Status:** Implemented and passing
**Files testing this page:** 50+ exhaustive test files

### Required UI Elements (data-testid)

| data-testid | Element Type | Description |
|-------------|--------------|-------------|
| `login-container` | div | Main container for login page |
| `login-card` | div | Card component containing login form |
| `login-title` | h2 | "Staff Login" heading |
| `login-form` | form | Login form with POST method to `/staff/login` |
| `email-input` | input[type=email] | Email field with autocomplete="email" |
| `password-input` | input[type=password] | Password field with autocomplete="current-password" |
| `login-button` | button[type=submit] | "Sign In" submit button |
| `client-portal-link` | a | Link to `/portal/login` |

### Form Attributes

```html
<form data-testid="login-form" id="loginForm" method="POST" action="/staff/login">
  <input data-testid="email-input"
         type="email"
         name="email"
         id="email"
         placeholder="your@email.com"
         autocomplete="email"
         required />

  <input data-testid="password-input"
         type="password"
         name="password"
         id="password"
         placeholder="Enter your password"
         autocomplete="current-password"
         required />

  <button data-testid="login-button" type="submit" id="loginBtn" class="login-btn">
    Sign In
  </button>
</form>
```

### Additional UI Elements (CSS selectors)

| Selector | Description |
|----------|-------------|
| `.logo img` | Company logo with alt="Brightpath Ascend Group" |
| `.staff-badge` | Badge showing "Staff Portal" with SVG icon |
| `.toggle-btn` | Password visibility toggle button |
| `.subtitle` | "Sign in to access the admin dashboard" |
| `.client-portal-link` | Container with "Looking for client portal?" text |

### Functionality Requirements

1. **Form Validation**
   - Email field: required, email format validation
   - Password field: required
   - Shows HTML5 validation messages

2. **Password Toggle**
   - Toggle button changes password field type between "password" and "text"
   - Uses `togglePassword('password')` JavaScript function

3. **Loading State**
   - Button becomes disabled on submit
   - Button text changes to "Signing in..."
   - Spinner element appears

4. **Navigation**
   - Client portal link navigates to `/portal/login`

5. **Responsive Design**
   - Desktop (1280px): Full layout
   - Tablet (768px): Adjusted layout
   - Mobile (375px): Mobile-optimized layout

---

## 2. Client Portal Login

**Route:** `/portal` or `/portal/login`
**Status:** Fully specified
**File:** `portal_exhaustive.cy.js`

### Required UI Elements (data-testid)

| data-testid | Element Type | Description |
|-------------|--------------|-------------|
| `portal-login-container` | div | Main container |
| `portal-login-card` | div | Login card |
| `login-form-container` | div | Container for login form (hidden when other forms active) |
| `forgot-form-container` | div | Container for forgot password form |
| `reset-form-container` | div | Container for reset password form |
| `portal-login-form` | form | Login form |
| `portal-email-input` | input[type=email] | Login email field |
| `portal-password-input` | input[type=password] | Login password field |
| `portal-login-button` | button[type=submit] | Login submit button |
| `toggle-password-btn` | button | Password visibility toggle |
| `forgot-password-link` | a | "Forgot your password?" link |
| `token-access-link` | a | "Use direct link access" link |
| `login-title` | h2 | "Welcome Back" heading |

### Forgot Password Form

| data-testid | Element Type | Description |
|-------------|--------------|-------------|
| `forgot-password-form` | form | Forgot password form |
| `forgot-email-input` | input[type=email] | Email for reset link |
| `send-reset-button` | button[type=submit] | "Send Reset Link" button |
| `back-to-login-link` | a | "Back to login" navigation |
| `forgot-alert` | div | Alert/message container (hidden by default) |

### Reset Password Form

| data-testid | Element Type | Description |
|-------------|--------------|-------------|
| `reset-password-form` | form | Reset password form |
| `new-password-input` | input[type=password] | New password field (minlength=8) |
| `confirm-password-input` | input[type=password] | Confirm password field |
| `reset-password-button` | button[type=submit] | "Reset Password" button |
| `reset-alert` | div | Alert/message container |

### Functionality Requirements

1. **Form Navigation**
   - Default: Login form visible, forgot/reset forms hidden
   - Clicking "Forgot your password?" shows forgot form, hides login
   - Back link returns to login form
   - URL with `?token=xxx` shows reset form directly

2. **Password Reset Flow**
   - Submit email to `/api/portal/forgot-password`
   - Display success/error in alert div
   - Reset form validates password match
   - Reset form validates minimum 8 characters
   - Submit to `/api/portal/reset-password`

3. **Token Access**
   - Prompt user for token/URL
   - Extract token from full portal URL
   - Handle empty/cancelled input

4. **Validation Messages**
   - "Passwords do not match"
   - "Password must be at least 8 characters"
   - "Connection error"
   - "Password reset successfully"

---

## 3. API Management

**Route:** `/dashboard/api-keys`
**Status:** Fully specified
**File:** `api_keys_exhaustive.cy.js`

### Required UI Elements (data-testid)

| data-testid | Element Type | Description |
|-------------|--------------|-------------|
| `api-management-container` | div | Main page container |
| `api-management-title` | h1 | "API Management" heading |
| `view-api-docs-btn` | a | Link to `/dashboard/api-docs` |
| `generate-api-key-btn` | button | Opens create key modal |
| `stats-grid` | div | Container for stats cards |
| `stat-total-keys` | div | Total API Keys stat |
| `stat-active-keys` | div | Active Keys stat |
| `stat-total-webhooks` | div | Total Webhooks stat |
| `stat-active-webhooks` | div | Active Webhooks stat |
| `tabs` | div | Tab navigation container |
| `tab-api-keys` | button | API Keys tab |
| `tab-webhooks` | button | Webhooks tab |
| `tab-usage` | button | Usage Analytics tab |
| `api-keys-card` | div | API Keys content card |
| `api-keys-table` | table | Table of API keys |
| `api-keys-empty` | div | Empty state "No API Keys" |
| `webhooks-tab` | div | Webhooks tab content |
| `webhooks-card` | div | Webhooks content card |
| `add-webhook-btn` | button | Add Webhook button |
| `webhooks-table` | table | Table of webhooks |
| `webhooks-empty` | div | Empty state "No Webhooks" |
| `usage-tab` | div | Usage Analytics tab content |
| `usage-card` | div | Usage content card |
| `usage-content` | div | Usage analytics content |
| `usage-empty` | div | Empty state "Select an API Key" |
| `create-key-modal` | div | Create API Key modal |
| `create-key-form` | form | Form inside modal |
| `create-key-modal-close` | button | Modal close button |
| `create-webhook-modal` | div | Create Webhook modal |
| `create-webhook-form` | form | Form inside modal |
| `create-webhook-modal-close` | button | Modal close button |

### Functionality Requirements

1. **Tabs**
   - API Keys tab active by default
   - Clicking tab switches content
   - Active tab has `.active` class

2. **Modals**
   - Click button opens modal (adds `.active` class)
   - Close button removes `.active` class
   - Forms inside modals

3. **Empty States**
   - Show appropriate message when no data

4. **Navigation**
   - View API Docs links to `/dashboard/api-docs`

---

## 4. API Documentation

**Route:** `/dashboard/api-docs`
**Status:** Fully specified
**File:** `api_docs_exhaustive.cy.js`

### Page Structure

| Element | Description |
|---------|-------------|
| `.sidebar` | Left navigation sidebar |
| `.main-content` | Main documentation content |
| `.header` | Page header with title and actions |
| `.toc` | Table of Contents |

### Required Sections (IDs)

| ID | Section |
|----|---------|
| `#overview` | API Overview |
| `#authentication` | Authentication |
| `#rate-limiting` | Rate Limiting |
| `#endpoints` | Endpoints |
| `#clients` | Clients endpoint |
| `#disputes` | Disputes endpoint |
| `#violations` | Violations endpoint |
| `#webhooks` | Webhooks endpoint |
| `#errors` | Error Codes |
| `#examples` | Code Examples |

### Required Tables

1. **API Scopes Table** - 6 rows
2. **Rate Limiting Table** - 2 rows
3. **Clients Endpoint Parameters** - 3 rows
4. **Clients GET Parameter** - 1 row
5. **Clients POST Fields** - 4 rows
6. **Disputes Parameters** - 3 rows
7. **Disputes POST Fields** - 4 rows
8. **Violations Parameters** - 2 rows
9. **Webhooks Fields** - 3 rows
10. **Error Codes Table** - 5 rows

### Functionality Requirements

1. **TOC Navigation**
   - Clicking TOC links scrolls to sections
   - Links: overview, authentication, rate-limiting, endpoints, errors, examples
   - Sub-items: clients, disputes, violations, webhooks

2. **Sidebar**
   - Expandable nav sections
   - User profile display
   - Sign out link

3. **Buttons**
   - "Manage API Keys" - links to `/dashboard/api-keys`
   - "Get Your API Key" - links to `/dashboard/api-keys`

---

## 5. PWA Assets

### 5.1 Manifest.json

**Route:** `/manifest.json`
**File:** `manifest.json_exhaustive.cy.js`

### Required Fields

```json
{
  "name": "Brightpath Ascend FCRA Platform",
  "short_name": "Brightpath FCRA",
  "description": "Comprehensive FCRA litigation automation platform",
  "start_url": "/dashboard",
  "display": "standalone",
  "orientation": "any",
  "theme_color": "#319795",
  "background_color": "#1a1a2e",
  "categories": ["business", "productivity"],
  "icons": [
    { "src": "/static/images/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/static/images/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ],
  "shortcuts": [
    {
      "name": "Dashboard",
      "short_name": "Dashboard",
      "description": "View dashboard",
      "url": "/dashboard",
      "icons": [{ "src": "/static/images/icon-192.png", "sizes": "192x192" }]
    },
    {
      "name": "Contacts",
      "short_name": "Contacts",
      "description": "Manage contacts",
      "url": "/dashboard/contacts",
      "icons": [{ "src": "/static/images/icon-192.png", "sizes": "192x192" }]
    }
  ]
}
```

### 5.2 Service Worker (sw.js)

**Route:** `/sw.js`
**File:** `sw.js_exhaustive.cy.js`

### Required Event Listeners

1. **install** - Cache assets
2. **activate** - Clean old caches
3. **fetch** - Network-first strategy with cache fallback
4. **push** - Handle push notifications
5. **notificationclick** - Handle notification actions

### Required Content

```javascript
const CACHE_NAME = 'brightpath-fcra-v1';
const urlsToCache = [
  '/',
  '/dashboard',
  '/static/images/logo.png',
  // fonts.googleapis.com
];
```

### Notification Options

- Title: "Brightpath Ascend" (default)
- Icon: `/static/images/icon-192.png`
- Actions: `[{ action: 'open', title: 'Open' }, { action: 'dismiss', title: 'Dismiss' }]`

---

## 6. Dashboard Routes (Pending Implementation)

These routes currently redirect to Staff Login. Each needs an authenticated page implementation.

### Routes Listed by File

| File | Route | Module |
|------|-------|--------|
| `affiliates_exhaustive.cy.js` | `/dashboard/affiliates` | Affiliates |
| `audit_exhaustive.cy.js` | `/dashboard/audit` | Audit |
| `automation_exhaustive.cy.js` | `/dashboard/automation` | Automation |
| `automation_tools_exhaustive.cy.js` | `/dashboard/automation-tools` | Automation Tools |
| `billing_exhaustive.cy.js` | `/dashboard/billing` | Billing |
| `calendar_exhaustive.cy.js` | `/dashboard/calendar` | Calendar |
| `case_law_exhaustive.cy.js` | `/dashboard/case-law` | Case Law |
| `cases_exhaustive.cy.js` | `/dashboard/cases` | Cases |
| `cfpb_exhaustive.cy.js` | `/dashboard/cfpb` | CFPB |
| `chexsystems_exhaustive.cy.js` | `/dashboard/chexsystems` | ChexSystems |
| `clients_exhaustive.cy.js` | `/dashboard/clients` | Clients |
| `contacts_exhaustive.cy.js` | `/dashboard/contacts` | Contacts |
| `credit_import_exhaustive.cy.js` | `/dashboard/credit-import` | Credit Import |
| `credit_tracker_exhaustive.cy.js` | `/dashboard/credit-tracker` | Credit Tracker |
| `demand_generator_exhaustive.cy.js` | `/dashboard/demand-generator` | Demand Generator |
| `documents_exhaustive.cy.js` | `/dashboard/documents` | Documents |
| `email_exhaustive.cy.js` | `/dashboard/email` | Email |
| `escalation_exhaustive.cy.js` | `/dashboard/escalation` | Escalation |
| `franchise_exhaustive.cy.js` | `/dashboard/franchise` | Franchise |
| `frivolousness_exhaustive.cy.js` | `/dashboard/frivolousness` | Frivolousness |
| `furnishers_exhaustive.cy.js` | `/dashboard/furnishers` | Furnishers |
| `generator_exhaustive.cy.js` | `/dashboard/generator` | Generator |
| `import_exhaustive.cy.js` | `/dashboard/import` | Import |
| `integrations_exhaustive.cy.js` | `/dashboard/integrations` | Integrations |
| `knowledge_base_exhaustive.cy.js` | `/dashboard/knowledge-base` | Knowledge Base |
| `letter_queue_exhaustive.cy.js` | `/dashboard/letter-queue` | Letter Queue |
| `ml_insights_exhaustive.cy.js` | `/dashboard/ml-insights` | ML Insights |
| `patterns_exhaustive.cy.js` | `/dashboard/patterns` | Patterns |
| `performance_exhaustive.cy.js` | `/dashboard/performance` | Performance |
| `predictive_exhaustive.cy.js` | `/dashboard/predictive` | Predictive |
| `queue_exhaustive.cy.js` | `/dashboard/queue` | Queue |
| `reports_exhaustive.cy.js` | `/dashboard/reports` | Reports |
| `scanned_documents_exhaustive.cy.js` | `/dashboard/scanned-documents` | Scanned Documents |
| `settings_exhaustive.cy.js` | `/dashboard/settings` | Settings |
| `settlements_exhaustive.cy.js` | `/dashboard/settlements` | Settlements |
| `signups_exhaustive.cy.js` | `/dashboard/signups` | Signups |
| `sms_exhaustive.cy.js` | `/dashboard/sms` | SMS |
| `sol_exhaustive.cy.js` | `/dashboard/sol` | Statute of Limitations |
| `sops_exhaustive.cy.js` | `/dashboard/sops` | SOPs |
| `specialty_bureaus_exhaustive.cy.js` | `/dashboard/specialty-bureaus` | Specialty Bureaus |
| `staff_exhaustive.cy.js` | `/dashboard/staff` | Staff |
| `suspense_accounts_exhaustive.cy.js` | `/dashboard/suspense-accounts` | Suspense Accounts |
| `tasks_exhaustive.cy.js` | `/dashboard/tasks` | Tasks |
| `triage_exhaustive.cy.js` | `/dashboard/triage` | Triage |
| `va_approval_exhaustive.cy.js` | `/dashboard/va-approval` | VA Approval |
| `white_label_exhaustive.cy.js` | `/dashboard/white-label` | White Label |
| `whitelabel_exhaustive.cy.js` | `/dashboard/whitelabel` | Whitelabel |
| `workflows_exhaustive.cy.js` | `/dashboard/workflows` | Workflows |

### Other Routes

| File | Route | Description |
|------|-------|-------------|
| `admin_exhaustive.cy.js` | `/admin` | Admin panel |
| `history_exhaustive.cy.js` | `/history` | History (JSON endpoint) |
| `logout_exhaustive.cy.js` | `/portal/logout` | Portal logout |
| `preview_exhaustive.cy.js` | `/preview` | Preview |
| `scanner_exhaustive.cy.js` | `/scanner` | Scanner |
| `signup_exhaustive.cy.js` | `/signup` | Signup |
| `success_exhaustive.cy.js` | `/signup/success` | Signup success |
| `test_exhaustive.cy.js` | `/test` | Test (JSON endpoint) |
| `welcome_exhaustive.cy.js` | `/welcome` | Welcome |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Total exhaustive test files | 68 |
| Fully specified pages | 5 |
| Dashboard routes (redirect to login) | 48 |
| Other routes | 15 |
| Unique data-testid selectors | ~80 |

### Fully Specified Pages

1. Staff Login (`/staff/login`)
2. Client Portal Login (`/portal`)
3. API Management (`/dashboard/api-keys`)
4. API Documentation (`/dashboard/api-docs`)
5. PWA Assets (`/manifest.json`, `/sw.js`)

### Implementation Priority

1. **High Priority** - Staff-facing dashboard pages (clients, cases, billing, etc.)
2. **Medium Priority** - Automation and integration features
3. **Low Priority** - Analytics and ML features
