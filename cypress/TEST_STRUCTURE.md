# Cypress Test Suite Structure

## Overview
**Total Files:** 29 test files
**Current Status:** 738 passing, 18 pending, 0 failing
**Last Updated:** December 10, 2025

## Test File Organization

### Naming Convention

The test suite uses three distinct file naming patterns:

1. **`*_exhaustive.cy.js`** (9 files)
   - Generic template tests that validate basic functionality across multiple routes
   - Test common patterns: page load, UI elements, forms, error handling, responsive design
   - Often have skipped tests for features not present on all pages
   - Examples: `analysis_exhaustive.cy.js`, `auth_exhaustive.cy.js`

2. **`*_crud.cy.js`** (3 files)
   - Targeted tests for Create, Read, Update, Delete operations
   - Test modal forms, validation, data persistence
   - More specific and detailed than exhaustive tests
   - Examples: `staff_crud.cy.js`, `settlements_crud.cy.js`, `clients_crud.cy.js`

3. **Regular/Feature-Specific** (17 files)
   - Tests for individual features or pages
   - Focused on specific user workflows
   - Examples: `login.cy.js`, `dispute_letters.cy.js`, `credit_reports.cy.js`

---

## Complete File Listing

### Exhaustive Template Tests (9 files)

| File | Routes Covered | Description |
|------|----------------|-------------|
| `analysis_exhaustive.cy.js` | 2 routes | Tests analysis-related pages for basic functionality |
| `auth_exhaustive.cy.js` | 4 routes | Tests authentication pages (login, logout, password change, portal) |
| `automation_exhaustive.cy.js` | 3 routes | Tests automation tools, letter queue, and automation dashboard |
| `cases_exhaustive.cy.js` | 3 routes | Tests case management and case law pages |
| `clients_exhaustive.cy.js` | 2 routes | Tests client listing and management pages |
| `dashboard_exhaustive.cy.js` | 47 routes | Tests all dashboard-related routes comprehensively |
| `other_exhaustive.cy.js` | 22 routes | Tests miscellaneous routes (webhooks, admin, signup, scanner, etc.) |
| `settlements_exhaustive.cy.js` | 1 route | Tests settlements listing page |
| `staff_exhaustive.cy.js` | 1 route | Tests staff management listing page |

**Total Routes Covered:** 85+ routes across all exhaustive tests

### CRUD Operation Tests (3 files)

| File | Description |
|------|-------------|
| `clients_crud.cy.js` | Tests client creation, editing, deletion, and search functionality |
| `settlements_crud.cy.js` | Tests settlement record CRUD operations with modal forms |
| `staff_crud.cy.js` | Tests staff member creation, password setup, login, editing, and deletion |

### Feature-Specific Tests (17 files)

| File | Description |
|------|-------------|
| `analytics.cy.js` | Tests analytics dashboard metrics and visualizations |
| `api_endpoints.cy.js` | Tests API endpoint responses and data structure |
| `client_portal.cy.js` | Tests client-facing portal functionality |
| `clients.cy.js` | Tests client management workflows and interactions |
| `create_item.cy.js` | Tests item creation flows across different entity types |
| `credit_report_viewer.cy.js` | Tests credit report viewing and navigation interface |
| `credit_reports.cy.js` | Tests credit report import, parsing, and display |
| `dashboard.cy.js` | Tests main dashboard layout, widgets, and navigation |
| `dispute_letters.cy.js` | Tests dispute letter generation, preview, and document management |
| `edge_cases.cy.js` | Tests edge cases, error conditions, and boundary scenarios |
| `login.cy.js` | Tests staff login flow, session management, and authentication |
| `payments.cy.js` | Tests payment processing, billing, and transaction workflows |
| `portal_login.cy.js` | Tests client portal login and access control |
| `settlements.cy.js` | Tests settlement tracking and management features |
| `signup_flow.cy.js` | Tests new client signup and onboarding process |
| `smoke.cy.js` | Quick smoke tests for critical functionality |
| `welcome_page.cy.js` | Tests landing page and initial user experience |

---

## Pending/Skipped Tests Breakdown

### Total: 18 pending tests

#### 1. Modal Validation Tests (9 tests)
**Files:** All 9 exhaustive test files
**Reason:** `page has no modal forms`
**Explanation:** Exhaustive files are generic templates that test many routes. Most pages don't have modal forms. Modal validation is properly tested in the specific `*_crud.cy.js` files instead.

#### 2. Redirect Tests (3 tests)
**Files:** `auth_exhaustive.cy.js`
- `should load /staff/login - redirects when logged in`
- `should load /staff/logout - redirects when logged in`

**File:** `other_exhaustive.cy.js`
- Various redirect scenarios

**Reason:** These routes redirect when the user is already logged in
**Explanation:** Tests need special handling for redirect behavior, currently skipped

#### 3. JSON Endpoint Tests (6 tests)
**Files:** `other_exhaustive.cy.js`, `dashboard_exhaustive.cy.js`
**Reason:** `JSON endpoint` - not suitable for browser testing
**Explanation:** These endpoints return JSON data rather than HTML pages. Should be tested via API tests in `api_endpoints.cy.js` instead of browser tests.

Examples:
- `/history`
- `/test`
- `/admin/clients`
- `/manifest.json`
- `/sw.js`

---

## Test Statistics by Category

### Exhaustive Tests
- **Total Tests:** ~150 tests across 9 files
- **Common Sections:**
  - Page Load & Navigation
  - UI Elements
  - Forms & Inputs
  - Error Handling
  - Responsive Design
- **Pending:** 9 (modal validation tests)

### CRUD Tests
- **Total Tests:** ~40 tests across 3 files
- **Focus Areas:**
  - Create operations with form validation
  - Read operations with search/filter
  - Update operations with data persistence
  - Delete operations with confirmation
- **Pending:** 0

### Feature Tests
- **Total Tests:** ~550 tests across 17 files
- **Coverage:** Specific user workflows and features
- **Pending:** 9 (various reasons)

---

## When to Use Each Test Type

### Use Exhaustive Tests When:
- Adding a new route that follows standard patterns
- Validating basic page structure and navigation
- Ensuring responsive design works across routes
- Testing error handling consistency

### Use CRUD Tests When:
- Building features with modal forms
- Testing data persistence and validation
- Verifying create/update/delete workflows
- Testing complex form interactions

### Use Feature Tests When:
- Testing specific user workflows
- Validating complex business logic
- Testing integrations between components
- Covering unique features or edge cases

---

## Adding New Tests

### For New Routes
1. Add to appropriate `*_exhaustive.cy.js` file if it follows standard patterns
2. Create new feature-specific test file if it has unique functionality

### For New CRUD Features
1. Create new `*_crud.cy.js` file
2. Include create, read, update, delete test coverage
3. Test form validation and error handling

### For New Features
1. Create descriptive test file name (e.g., `feature_name.cy.js`)
2. Group related tests in describe blocks
3. Use beforeEach for common setup
4. Document any skipped tests with clear reasons

---

## Maintenance Notes

### Regular Checks
- Run full test suite before deployments
- Review pending tests quarterly - fix or document why still pending
- Update test counts in this document when adding/removing tests
- Keep naming conventions consistent

### When Tests Fail
1. Check if it's a test independence issue (passes alone, fails in suite)
2. Verify selectors match actual HTML
3. Ensure proper waits for async operations
4. Review journal.txt for similar past issues

### Best Practices
- Always use `beforeEach` to establish clean state
- Prefer data-testid attributes over complex CSS selectors
- Document why tests are skipped, not just that they are
- Keep tests focused and independent
- Use descriptive test names that explain what's being tested
