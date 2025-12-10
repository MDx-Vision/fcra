# Debugging Cypress Tests - Practical Guide

## Quick Reference

**Current Status:** 738 passing, 18 pending, 0 failing
**Last Updated:** December 10, 2025

---

## Running Tests Locally

### Run All Tests
```bash
# Open Cypress Test Runner (GUI)
npx cypress open

# Run all tests headlessly
npx cypress run

# Run with specific browser
npx cypress run --browser chrome
npx cypress run --browser firefox
```

### Run Single Test File
```bash
# Run one specific test file
npx cypress run --spec "cypress/e2e/login.cy.js"

# Run multiple specific files
npx cypress run --spec "cypress/e2e/login.cy.js,cypress/e2e/dashboard.cy.js"

# Run all tests matching a pattern
npx cypress run --spec "cypress/e2e/*_crud.cy.js"
```

### Run Single Test
```bash
# Open Cypress Test Runner, then:
# 1. Click on the test file
# 2. In the browser, click on the specific test you want to run
# 3. Or use .only in your test file temporarily:

it.only('should test this specific thing', () => {
  // your test code
});
```

### Useful Options
```bash
# Run with video recording
npx cypress run --record

# Run without video (faster)
npx cypress run --video=false

# Run with specific viewport
npx cypress run --config viewportWidth=1280,viewportHeight=720

# Run with increased timeout
npx cypress run --config defaultCommandTimeout=10000
```

---

## Common Failure Patterns & Fixes

### 1. "Element Not Visible" Error

**Symptom:**
```
CypressError: cy.click() failed because this element is not visible
```

**Common Causes:**
- Element is hidden behind a modal
- Element is in a collapsed accordion/tab
- Element hasn't loaded yet
- Element is off-screen

**Fixes:**

#### A. Modal Needs to be Opened First
```javascript
// ❌ WRONG - modal not opened
it('should fill form', () => {
  cy.get('input[name="email"]').type('test@example.com');
});

// ✅ CORRECT - open modal first
it('should fill form', () => {
  cy.get('.btn').contains(/add/i).click();  // Open modal
  cy.get('.modal.active').should('be.visible');  // Wait for modal
  cy.get('.modal.active input[name="email"]').type('test@example.com');
});
```

#### B. Tab Needs to be Activated
```javascript
// ❌ WRONG - content in inactive tab
it('should see documents', () => {
  cy.get('.document-list').should('exist');
});

// ✅ CORRECT - switch to tab first
it('should see documents', () => {
  cy.contains('Client Documents').click();  // Switch tab
  cy.get('.document-list').should('be.visible');
});
```

#### C. Element Not Loaded Yet
```javascript
// ❌ WRONG - element might not be loaded
it('should see data', () => {
  cy.visit('/dashboard/clients');
  cy.get('.client-row').should('have.length', 5);
});

// ✅ CORRECT - wait for element to exist first
it('should see data', () => {
  cy.visit('/dashboard/clients');
  cy.get('.client-row').should('exist');  // Wait for at least one
  cy.get('.client-row').should('have.length.at.least', 1);
});
```

---

### 2. "Element Not Found" Error

**Symptom:**
```
CypressError: Timed out retrying: Expected to find element: '.some-class', but never found it
```

**Common Causes:**
- Selector doesn't match actual HTML
- Wrong assumption about HTML structure
- Typo in selector
- Element removed or renamed

**Fixes:**

#### A. Verify Selector Matches HTML
```javascript
// ❌ WRONG - assumes text that doesn't exist
it('should click documents tab', () => {
  cy.contains('Documents').click();
});

// ✅ CORRECT - check actual HTML first
it('should click documents tab', () => {
  cy.contains('Client Documents').click();  // Actual text in HTML
});
```

**Debugging Steps:**
1. Open Cypress Test Runner
2. Let test fail
3. Look at the screenshot - is the element there?
4. Use browser DevTools to inspect actual HTML
5. Update selector to match what's actually in the HTML

#### B. Use More Specific Selectors
```javascript
// ❌ WRONG - too generic, might match wrong element
it('should click button', () => {
  cy.get('button').click();
});

// ✅ CORRECT - more specific
it('should click button', () => {
  cy.get('.modal.active button[type="submit"]').click();
});

// ✅ EVEN BETTER - use data attributes
it('should click button', () => {
  cy.get('[data-testid="submit-button"]').click();
});
```

---

### 3. Test Passes Alone But Fails in Suite

**Symptom:**
```bash
# This passes
npx cypress run --spec "cypress/e2e/dispute_letters.cy.js" --grep "should preview letter"

# This fails
npx cypress run --spec "cypress/e2e/dispute_letters.cy.js"
```

**Root Cause:** Test independence issue - tests are modifying shared state

**Fix: Add `beforeEach` Hooks**

```javascript
// ❌ WRONG - tests depend on previous test state
describe('Dispute Letters', () => {
  it('should navigate to client', () => {
    cy.visit('/dashboard/clients');
    cy.get('.client-row').first().click();
  });

  it('should see credit analysis', () => {
    // Assumes previous test ran
    cy.contains('Credit Analysis').click();
  });

  it('should generate letter', () => {
    // Assumes previous tests ran
    cy.get('.generate-btn').click();
  });
});

// ✅ CORRECT - each test is independent
describe('Dispute Letters', () => {
  beforeEach(() => {
    // Establish clean state for EVERY test
    cy.login('test@example.com', 'password123');
    cy.visit('/dashboard/clients');
    cy.get('.client-row').first().click();
    cy.contains('Credit Analysis').click();
  });

  it('should see credit analysis', () => {
    cy.get('.analysis-content').should('be.visible');
  });

  it('should generate letter', () => {
    cy.get('.generate-btn').click();
    cy.get('.letter-preview').should('be.visible');
  });
});
```

**Key Principle:** Every test should be able to run in isolation. Use `beforeEach` to set up required state.

---

### 4. Flaky Tests (Pass Sometimes, Fail Sometimes)

**Common Causes:**
- Race conditions with async operations
- Animations interfering with interactions
- Network timing issues
- Random data causing selector mismatches

**Fixes:**

#### A. Add Proper Waits
```javascript
// ❌ WRONG - doesn't wait for operation to complete
it('should create item', () => {
  cy.get('form').submit();
  cy.get('.success-message').should('be.visible');  // Might be too fast
});

// ✅ CORRECT - wait for API call to complete
it('should create item', () => {
  cy.intercept('POST', '/api/items').as('createItem');
  cy.get('form').submit();
  cy.wait('@createItem');  // Wait for API
  cy.get('.success-message').should('be.visible');
});
```

#### B. Wait for Animations
```javascript
// ❌ WRONG - click during animation
it('should click menu item', () => {
  cy.get('.menu-toggle').click();
  cy.get('.menu-item').click();  // Menu might still be animating
});

// ✅ CORRECT - ensure menu is fully visible
it('should click menu item', () => {
  cy.get('.menu-toggle').click();
  cy.get('.menu').should('be.visible');
  cy.get('.menu-item').should('be.visible').click();
});
```

---

### 5. Form Validation Not Working

**Symptom:** HTML5 validation or custom validation not being tested properly

**Fix: Test Validation Properly**

```javascript
// ❌ WRONG - form might submit despite validation
it('should show validation error', () => {
  cy.get('form').submit();
  cy.get('.error').should('be.visible');
});

// ✅ CORRECT - test HTML5 validation
it('should show validation error', () => {
  cy.get('input[required]').first().then(($input) => {
    expect($input[0].checkValidity()).to.be.false;
  });
});

// ✅ ALSO CORRECT - test custom validation
it('should show validation error', () => {
  cy.get('form').submit();
  cy.get('.alert-error').should('contain', 'Email is required');
});
```

---

## Reading CI Output

### CI Test Logs Structure
```
1. Test Suite Name
   └─ Test File: login.cy.js
      ├─ ✓ should display login form
      ├─ ✓ should validate email format
      └─ ✗ should login with valid credentials
         └─ Error: Element not found: button[type="submit"]
```

### Finding Failures in CI
1. Scroll to bottom for summary: `X passing, Y failing`
2. Search for `(failing)` to find failed tests
3. Look at the error message and stack trace
4. Check screenshots/videos if available
5. Note which file and line number failed

### Common CI-Specific Issues
- **Timing:** CI might be slower than local - add waits
- **Data:** CI database might be empty - seed data properly
- **Resolution:** CI viewport might differ - test responsive views
- **State:** CI runs might have stale state - ensure proper cleanup

---

## When to Skip vs Fix vs Delete

### Skip a Test When:
- Feature is temporarily broken but will be fixed soon
- Test requires environment setup not available yet
- Test covers edge case that's not critical right now

**Always document WHY:**
```javascript
it.skip('should export to PDF - PDF library not configured yet', () => {
  // Will enable when PDF service is set up in staging
});
```

### Fix a Test When:
- Test is failing due to wrong selector (quick fix)
- Test is failing due to test independence issue (add beforeEach)
- Test is failing due to timing issue (add proper waits)
- Feature works but test is broken

**Most tests should be fixed, not skipped!**

### Delete a Test When:
- Feature no longer exists
- Test duplicates coverage in another test
- Test is testing implementation details rather than behavior
- Test is fundamentally flawed and can't be fixed

---

## Debugging Workflow

### Step-by-Step Process

1. **Identify the Failure**
   ```bash
   npx cypress run --spec "path/to/failing-test.cy.js"
   ```

2. **Run in GUI Mode**
   ```bash
   npx cypress open
   # Click on failing test file
   # Watch test run and fail
   ```

3. **Inspect at Point of Failure**
   - Test pauses at failure
   - Use browser DevTools to inspect HTML
   - Check console for errors
   - Look at network tab for failed requests

4. **Add `.only` to Isolate**
   ```javascript
   it.only('should test failing thing', () => {
     // Only this test runs
   });
   ```

5. **Add `cy.pause()` for Step-Through**
   ```javascript
   it('should test thing', () => {
     cy.visit('/dashboard');
     cy.pause();  // Pauses here - click "Next" to step through
     cy.get('.client-row').click();
   });
   ```

6. **Check Test Independence**
   ```bash
   # Run test alone
   npx cypress run --spec "file.cy.js" --grep "specific test"

   # Run full file
   npx cypress run --spec "file.cy.js"

   # If alone passes but full fails = independence issue
   ```

7. **Fix and Verify**
   ```bash
   # Run the fixed test multiple times
   for i in {1..5}; do npx cypress run --spec "file.cy.js"; done
   ```

---

## Useful Debugging Commands

### Get Information About Elements
```javascript
// Log element details
cy.get('.my-element').then($el => {
  console.log($el);
  console.log($el.text());
  console.log($el.attr('class'));
});

// Check if element exists (doesn't fail if missing)
cy.get('body').then($body => {
  if ($body.find('.my-element').length > 0) {
    cy.log('Element exists!');
  } else {
    cy.log('Element does not exist');
  }
});

// Get all matching elements
cy.get('.client-row').then($rows => {
  cy.log(`Found ${$rows.length} rows`);
});
```

### Debug Network Requests
```javascript
// Intercept and log all API calls
cy.intercept('/api/**', (req) => {
  console.log('API Request:', req.method, req.url);
  req.continue((res) => {
    console.log('API Response:', res.statusCode, res.body);
  });
});

// Wait for specific request
cy.intercept('POST', '/api/clients').as('createClient');
cy.get('form').submit();
cy.wait('@createClient').then((interception) => {
  console.log('Request body:', interception.request.body);
  console.log('Response:', interception.response.body);
});
```

### Take Screenshots During Test
```javascript
it('should do something', () => {
  cy.visit('/dashboard');
  cy.screenshot('01-initial-state');

  cy.get('.btn').click();
  cy.screenshot('02-after-click');

  // Screenshots saved to cypress/screenshots/
});
```

---

## Getting Help

### Resources
- **Cypress Docs:** https://docs.cypress.io/
- **Cypress Best Practices:** https://docs.cypress.io/guides/references/best-practices
- **Project Journal:** Check `journal.txt` for similar past issues
- **Test Structure:** See `TEST_STRUCTURE.md` for test organization

### Before Asking for Help
1. Read the error message carefully
2. Check if selector matches HTML
3. Try running test in isolation
4. Check journal.txt for similar issues
5. Review this debugging guide

### When Asking for Help, Provide:
- Full error message and stack trace
- Test file and line number
- Steps to reproduce
- Screenshot of failure
- What you've already tried

---

## Prevention Tips

### Write Better Tests from the Start

1. **Always use `beforeEach` for setup**
2. **Use explicit waits, not arbitrary timeouts**
3. **Prefer data-testid over complex CSS selectors**
4. **Make tests independent - no shared state**
5. **Test behavior, not implementation**
6. **Add descriptive test names**
7. **Keep tests focused and simple**
8. **Document why tests are skipped**

### Regular Maintenance

- Run tests before every commit
- Fix flaky tests immediately
- Review pending tests monthly
- Update selectors when HTML changes
- Keep test documentation current
