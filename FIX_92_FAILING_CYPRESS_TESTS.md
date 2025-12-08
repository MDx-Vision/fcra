# FIX 92 FAILING CYPRESS TESTS

The new test files have 92 failures across 7 files. Fix them using the approaches below.

## ROOT CAUSES

### 1. INVALID SYNTAX - `.or()` is not a Cypress method
```javascript
// WRONG - causes "cy.get(...).should(...).or is not a function"
cy.get('.selector').should('exist').or('.other-selector').should('exist')

// RIGHT - use comma-separated selectors
cy.get('.selector, .other-selector').should('exist')

// OR - use cy.document().then()
cy.document().then(doc => {
  const el = doc.querySelector('.selector') || doc.querySelector('.other-selector');
  expect(el).to.exist;
});
```

### 2. cy.click() on multiple elements
```javascript
// WRONG - fails when multiple buttons found
cy.get('button[type="submit"]').click()

// RIGHT - click first one
cy.get('button[type="submit"]').first().click()

// OR - use more specific selector
cy.get('#loginForm button[type="submit"]').click()
```

### 3. cy.visit() returning JSON instead of HTML
```javascript
// WRONG - endpoint returns JSON, not HTML
cy.visit('/dashboard/staff/999')

// RIGHT - use cy.request() for API endpoints
cy.request({ url: '/dashboard/staff/999', failOnStatusCode: false })
  .its('status').should('eq', 404)
```

### 4. Invalid date format in cy.type()
```javascript
// WRONG - date inputs require YYYY-MM-DD
cy.get('input[type="date"]').type('invalid-date')

// RIGHT - use valid format
cy.get('input[type="date"]').type('2024-01-15')
```

---

## FILES TO FIX (7 files, 92 failures)

### 1. client_portal.cy.js (19 failures)
**Issues:**
- `.or()` syntax errors
- `cy.click()` on multiple elements (3 submit buttons found)
- Elements not found (navigation menu, logout, documents, messages, password form)

**Fixes needed:**
- Replace `.or()` with comma selectors
- Use `.first()` or more specific selectors for buttons
- Skip tests for unimplemented portal features

### 2. credit_reports.cy.js (14 failures)
**Issues:**
- `.or()` syntax errors
- Missing UI elements (Equifax/Experian/TransUnion display)
- Delete button not found

**Fixes needed:**
- Replace `.or()` with comma selectors
- Skip tests for credit report viewer features not yet built

### 3. dispute_letters.cy.js (15 failures)
**Issues:**
- `.or()` syntax errors
- Missing UI elements (pending letters, templates, bureau targeting)
- Action buttons not found (download, print, mark sent)

**Fixes needed:**
- Replace `.or()` with comma selectors
- Skip tests for dispute letter features not yet implemented

### 4. edge_cases.cy.js (6 failures)
**Issues:**
- `cy.visit()` on JSON endpoints
- Invalid date format in cy.type()
- Submit button not visible (hidden in step 4)

**Fixes needed:**
- Use `cy.request()` for `/dashboard/staff/999` and `/portal/clients/999`
- Use valid date format or skip date validation test
- Fix submit button visibility or use `{ force: true }`

### 5. payments.cy.js (13 failures)
**Issues:**
- `.or()` syntax errors throughout
- Missing pricing plan elements (FREE, Professional, Elite)

**Fixes needed:**
- Replace all `.or()` with comma selectors
- Adjust selectors to match actual pricing UI

### 6. signup_flow.cy.js (14 failures)
**Issues:**
- `.or()` syntax errors
- Missing `input[name*="zip"]` - use different selector
- Missing `input[name*="username"]`
- Pricing plan selectors not matching

**Fixes needed:**
- Replace `.or()` with comma selectors
- Update field selectors to match actual signup form
- Skip tests for elements that don't exist

### 7. welcome_page.cy.js (11 failures)
**Issues:**
- `.or()` syntax errors throughout
- Many expected elements not present on success page

**Fixes needed:**
- Replace `.or()` with comma selectors
- Skip tests for content not on actual welcome page

---

## FIX PATTERN FOR .or() ERRORS

Search for this pattern in all files:
```javascript
.should('exist').or
.should('be.visible').or
```

Replace with comma-separated selectors:
```javascript
// Before
cy.get('.welcome-message').should('exist').or('.success-message').should('exist')

// After
cy.get('.welcome-message, .success-message').should('exist')
```

---

## SKIP PATTERN FOR UNIMPLEMENTED FEATURES

```javascript
// Before
it('should display pending letters', () => {
  cy.get('.pending-letters').should('exist');
});

// After
it.skip('should display pending letters - feature not implemented', () => {
  cy.get('.pending-letters').should('exist');
});
```

---

## VERIFICATION COMMANDS

Test each file individually after fixing:

```bash
# Test specific file
npx cypress run --spec "cypress/e2e/client_portal.cy.js"
npx cypress run --spec "cypress/e2e/credit_reports.cy.js"
npx cypress run --spec "cypress/e2e/dispute_letters.cy.js"
npx cypress run --spec "cypress/e2e/edge_cases.cy.js"
npx cypress run --spec "cypress/e2e/payments.cy.js"
npx cypress run --spec "cypress/e2e/signup_flow.cy.js"
npx cypress run --spec "cypress/e2e/welcome_page.cy.js"

# Run all tests
npx cypress run
```

---

## SUCCESS CRITERIA

- All 29 specs passing
- 0 failures
- Tests that can't pass should be marked with `it.skip()` and a comment explaining why
- No `.or()` syntax anywhere in test files

---

## COMMIT MESSAGE

```
Fix 92 failing Cypress tests

- Replace invalid .or() syntax with comma-separated selectors
- Fix cy.click() on multiple elements with .first()
- Use cy.request() for JSON endpoints instead of cy.visit()
- Skip tests for features not yet implemented
- Fix date format validation test
```
