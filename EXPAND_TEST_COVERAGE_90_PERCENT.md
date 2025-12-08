# EXPAND CYPRESS TEST COVERAGE TO 90%+

---

## CURRENT STATE

- 489 tests passing
- ~60-70% coverage
- Missing critical user flows

---

## YOUR TASK

Add 200-300 new tests to cover all missing areas. Work autonomously - create all test files, verify they pass, then push to git.

---

## NEW TEST FILES TO CREATE

### 1. `cypress/e2e/signup_flow.cy.js` (~50 tests)

Test the complete client signup at `/signup`:

```javascript
describe('Client Signup Flow', () => {
  beforeEach(() => {
    cy.visit('/signup');
  });

  describe('Step 1: Personal Information', () => {
    it('should display all personal info fields');
    it('should validate first name required');
    it('should validate last name required');
    it('should validate email format');
    it('should validate phone format');
    it('should validate address fields');
    it('should validate ZIP code format (5 digits)');
    it('should validate date of birth');
    it('should validate SSN last 4 (4 digits)');
    it('should accept optional referral code');
    it('should enable Continue button when valid');
    it('should navigate to Step 2 on Continue');
  });

  describe('Step 2: Credit Monitoring Access', () => {
    it('should display all 10 credit monitoring options');
    it('should have IdentityIQ.com option');
    it('should have MyScoreIQ.com option');
    it('should have SmartCredit.com option');
    it('should have MyFreeScoreNow.com option');
    it('should have HighScoreNow.com option');
    it('should have IdentityClub.com option');
    it('should have PrivacyGuard.com option');
    it('should have IDClub.com option');
    it('should have MyThreeScores.com option');
    it('should have MyScore750.com option');
    it('should validate username required');
    it('should validate password required');
    it('should navigate back to Step 1');
    it('should navigate to Step 3 on Continue');
  });

  describe('Step 3: Plan & Payment', () => {
    it('should display all 6 pricing plans');
    it('should display Basic Analysis - FREE');
    it('should display Starter - $300');
    it('should display Standard - $600');
    it('should display Premium - $900 (Most Popular)');
    it('should display Professional - $1,200');
    it('should display Elite - $1,500');
    it('should show payment methods when paid plan selected');
    it('should display Credit/Debit Card option');
    it('should display PayPal option');
    it('should display Cash App option');
    it('should display Venmo option');
    it('should display Zelle option');
    it('should display Pay Later option');
    it('should hide payment methods for FREE plan');
    it('should navigate back to Step 2');
    it('should navigate to Step 4 on Continue');
  });

  describe('Step 4: Service Agreement', () => {
    it('should display service agreement text');
    it('should have terms checkbox');
    it('should have communications checkbox (optional)');
    it('should disable submit until terms accepted');
    it('should enable submit when terms checked');
    it('should navigate back to Step 3');
    it('should show loading spinner on submit');
  });

  describe('Complete Signup Flow', () => {
    it('should complete full signup with FREE plan');
    it('should complete full signup with paid plan');
    it('should show success message after signup');
    it('should display client referral code');
    it('should have Go to Client Portal button');
  });

  describe('Progress Indicator', () => {
    it('should show Step 1 as active initially');
    it('should update progress on each step');
    it('should mark completed steps');
  });
});
```

### 2. `cypress/e2e/client_portal.cy.js` (~40 tests)

Test the client-facing portal:

```javascript
describe('Client Portal', () => {
  describe('Portal Login', () => {
    it('should display login form');
    it('should validate email required');
    it('should validate password required');
    it('should show error for invalid credentials');
    it('should login with valid credentials');
    it('should have forgot password link');
    it('should have token access option');
  });

  describe('Portal Dashboard', () => {
    beforeEach(() => {
      // Login as client or use token
      cy.visit('/portal/dashboard');
    });

    it('should display client name');
    it('should display case status');
    it('should display credit scores');
    it('should display violation count');
    it('should display timeline/progress');
    it('should have navigation menu');
    it('should have logout option');
  });

  describe('Portal Documents', () => {
    it('should list client documents');
    it('should allow document download');
    it('should display document dates');
  });

  describe('Portal Messages', () => {
    it('should display messages');
    it('should allow sending messages');
    it('should show message timestamps');
  });

  describe('Password Creation', () => {
    it('should display password creation form');
    it('should validate password strength');
    it('should validate password confirmation');
    it('should create password successfully');
  });

  describe('Token Access', () => {
    it('should accept valid portal token');
    it('should reject invalid token');
    it('should redirect to dashboard with valid token');
  });
});
```

### 3. `cypress/e2e/credit_reports.cy.js` (~30 tests)

Test credit report handling:

```javascript
describe('Credit Report Processing', () => {
  beforeEach(() => {
    cy.loginAsStaff();
    cy.visit('/dashboard/import');
  });

  describe('Upload Interface', () => {
    it('should display upload area');
    it('should accept PDF files');
    it('should accept HTML files');
    it('should reject invalid file types');
    it('should show upload progress');
    it('should display success message');
  });

  describe('Report Viewer', () => {
    it('should display credit scores');
    it('should display Equifax score');
    it('should display Experian score');
    it('should display TransUnion score');
    it('should display accounts list');
    it('should display inquiries');
    it('should display public records');
  });

  describe('Violation Detection', () => {
    it('should identify FCRA violations');
    it('should display violation count');
    it('should categorize violations by type');
    it('should calculate potential damages');
  });

  describe('Report List', () => {
    it('should list all imported reports');
    it('should filter by client');
    it('should filter by date');
    it('should allow report deletion');
  });
});
```

### 4. `cypress/e2e/dispute_letters.cy.js` (~35 tests)

Test dispute letter generation:

```javascript
describe('Dispute Letter Generation', () => {
  beforeEach(() => {
    cy.loginAsStaff();
  });

  describe('Letter Queue', () => {
    beforeEach(() => {
      cy.visit('/dashboard/letter-queue');
    });

    it('should display pending letters');
    it('should filter by status');
    it('should filter by client');
    it('should display letter type');
    it('should display target bureau');
  });

  describe('Letter Creation', () => {
    it('should select dispute items');
    it('should choose letter template');
    it('should customize letter content');
    it('should preview letter');
    it('should generate PDF');
  });

  describe('Letter Templates', () => {
    it('should list available templates');
    it('should display Round 1 templates');
    it('should display Round 2 templates');
    it('should display Round 3 templates');
    it('should display Round 4 templates');
  });

  describe('Bureau Targeting', () => {
    it('should target Equifax');
    it('should target Experian');
    it('should target TransUnion');
    it('should target all three bureaus');
    it('should target furnishers');
  });

  describe('Letter Actions', () => {
    it('should download letter as PDF');
    it('should print letter');
    it('should mark as sent');
    it('should track delivery status');
  });
});
```

### 5. `cypress/e2e/api_endpoints.cy.js` (~50 tests)

Test API endpoints directly:

```javascript
describe('API Endpoints', () => {
  describe('Authentication APIs', () => {
    it('POST /api/login - valid credentials');
    it('POST /api/login - invalid credentials');
    it('POST /api/logout');
    it('GET /api/me - authenticated');
    it('GET /api/me - unauthenticated returns 401');
  });

  describe('Client APIs', () => {
    it('GET /api/clients - list all clients');
    it('GET /api/clients/:id - get single client');
    it('POST /api/client/signup - create client');
    it('PUT /api/clients/:id - update client');
    it('DELETE /api/clients/:id - soft delete');
  });

  describe('Case APIs', () => {
    it('GET /api/cases - list cases');
    it('GET /api/case/:id - get case details');
    it('POST /api/case - create case');
    it('PUT /api/case/:id - update case');
  });

  describe('Dispute APIs', () => {
    it('GET /api/disputes - list disputes');
    it('POST /api/dispute - create dispute');
    it('PUT /api/dispute/:id - update dispute');
    it('POST /api/dispute/:id/send - send dispute');
  });

  describe('Settlement APIs', () => {
    it('GET /api/settlements - list settlements');
    it('POST /api/settlement - create settlement');
    it('PUT /api/settlement/:id - update settlement');
    it('POST /api/settlement/:id/offer - add offer');
  });

  describe('Staff APIs', () => {
    it('GET /api/staff - list staff');
    it('POST /api/staff - create staff');
    it('PUT /api/staff/:id - update staff');
    it('DELETE /api/staff/:id - deactivate staff');
  });

  describe('Document APIs', () => {
    it('GET /api/documents - list documents');
    it('POST /api/document/upload - upload document');
    it('GET /api/document/:id - download document');
    it('DELETE /api/document/:id - delete document');
  });

  describe('Error Handling', () => {
    it('should return 400 for bad request');
    it('should return 401 for unauthorized');
    it('should return 403 for forbidden');
    it('should return 404 for not found');
    it('should return 500 for server error');
  });
});
```

### 6. `cypress/e2e/payments.cy.js` (~25 tests)

Test payment flows:

```javascript
describe('Payment Processing', () => {
  describe('Payment Methods Display', () => {
    it('should show all 6 payment options');
    it('should highlight selected method');
    it('should show payment instructions for manual methods');
  });

  describe('Stripe Checkout', () => {
    it('should redirect to Stripe for card payment');
    it('should handle successful payment');
    it('should handle cancelled payment');
    it('should handle failed payment');
  });

  describe('Manual Payments', () => {
    it('should display Cash App handle');
    it('should display Venmo handle');
    it('should display Zelle handle');
    it('should display PayPal handle');
    it('should show correct amount');
  });

  describe('Pay Later', () => {
    it('should allow signup without immediate payment');
    it('should mark client as pending payment');
  });

  describe('Payment Confirmation', () => {
    it('should show success page after payment');
    it('should update client status');
    it('should send confirmation email');
  });
});
```

### 7. `cypress/e2e/edge_cases.cy.js` (~30 tests)

Test edge cases and error handling:

```javascript
describe('Edge Cases & Error Handling', () => {
  describe('Invalid Inputs', () => {
    it('should reject SQL injection in search');
    it('should reject XSS in form fields');
    it('should handle very long input strings');
    it('should handle special characters');
    it('should handle empty submissions');
    it('should handle whitespace-only input');
  });

  describe('Unauthorized Access', () => {
    it('should redirect unauthenticated users from dashboard');
    it('should redirect unauthenticated users from admin');
    it('should prevent staff from accessing other staff data');
    it('should prevent clients from accessing other client data');
  });

  describe('Session Handling', () => {
    it('should handle expired session');
    it('should handle concurrent sessions');
    it('should clear session on logout');
  });

  describe('Network Errors', () => {
    it('should handle API timeout');
    it('should handle network disconnection');
    it('should show retry option on failure');
  });

  describe('Data Validation', () => {
    it('should validate email format');
    it('should validate phone format');
    it('should validate date format');
    it('should validate currency format');
    it('should validate file size limits');
  });

  describe('Concurrent Operations', () => {
    it('should handle rapid form submissions');
    it('should prevent duplicate client creation');
    it('should handle simultaneous edits');
  });
});
```

### 8. `cypress/e2e/welcome_page.cy.js` (~15 tests)

Test the welcome page:

```javascript
describe('Welcome Page', () => {
  beforeEach(() => {
    cy.visit('/signup/welcome');
  });

  it('should display welcome message');
  it('should display success icon');
  it('should display next steps');
  it('should have Go to Client Portal button');
  it('should link to /portal/login');
  it('should display contact information');
  it('should be responsive on mobile');
  it('should be responsive on tablet');
  it('should have correct branding');
  it('should display within 24-48 hours message');
});
```

---

## HELPER COMMANDS TO ADD

Add to `cypress/support/commands.js`:

```javascript
// Login as staff member
Cypress.Commands.add('loginAsStaff', () => {
  cy.session('staff', () => {
    cy.visit('/staff/login');
    cy.get('#email').type('admin@example.com');
    cy.get('#password').type('admin123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  });
});

// Login as client
Cypress.Commands.add('loginAsClient', (email, password) => {
  cy.session(['client', email], () => {
    cy.visit('/portal/login');
    cy.get('#email').type(email);
    cy.get('#password').type(password);
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/portal');
  });
});

// Complete signup Step 1
Cypress.Commands.add('fillSignupStep1', () => {
  cy.get('#firstName').type('Test');
  cy.get('#lastName').type('User');
  cy.get('#email').type(`test${Date.now()}@example.com`);
  cy.get('#phone').type('5551234567');
  cy.get('#addressStreet').type('123 Test St');
  cy.get('#addressCity').type('Test City');
  cy.get('#addressState').select('CA');
  cy.get('#addressZip').type('90210');
  cy.get('#dateOfBirth').type('1990-01-01');
  cy.get('#ssnLast4').type('1234');
});

// Navigate through signup steps
Cypress.Commands.add('goToSignupStep', (step) => {
  cy.visit('/signup');
  for (let i = 1; i < step; i++) {
    if (i === 1) cy.fillSignupStep1();
    cy.contains('Continue').click();
    cy.wait(500);
  }
});

// API request with auth
Cypress.Commands.add('apiRequest', (method, url, body = null) => {
  return cy.request({
    method,
    url,
    body,
    failOnStatusCode: false
  });
});
```

---

## EXECUTION STEPS

1. **Create all test files** listed above
2. **Add helper commands** to `cypress/support/commands.js`
3. **Run tests locally** to verify:
   ```bash
   npx cypress run
   ```
4. **Fix any failing tests** - adjust selectors or expectations as needed
5. **Push to git**:
   ```bash
   git add .
   git commit -m "Add comprehensive test coverage - 200+ new tests for 90%+ coverage"
   git push
   ```

---

## VERIFICATION

After pushing, GitHub Actions should show:
- ~700+ total tests
- 90%+ coverage
- All critical user flows tested

---

## ⚠️ IMPORTANT NOTES ⚠️

1. **Use existing selectors** - check the app's HTML for correct IDs/classes
2. **Handle async operations** - use `cy.wait()` or intercepts as needed
3. **Test both success and failure paths**
4. **Keep tests independent** - each test should work in isolation
5. **Use descriptive test names** - clearly state what's being tested

---

**CREATE ALL TEST FILES AND PUSH TO GIT. WORK AUTONOMOUSLY - DON'T ASK QUESTIONS.**
