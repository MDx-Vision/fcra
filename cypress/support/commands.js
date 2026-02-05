Cypress.Commands.add('login', (email = 'test@example.com', password = 'testpass123') => {
  cy.session([email, password], () => {
    cy.visit('/staff/login');
    cy.get('[data-testid="email-input"]').type(email);
    cy.get('[data-testid="password-input"]').type(password);
    cy.get('[data-testid="login-button"]').click();
    cy.url().should('include', '/dashboard');
    // Verify we're actually logged in by checking for dashboard content
    cy.get('body').should('not.contain', 'Sign In');
  }, {
    validate() {
      // Validate the session is still valid
      cy.visit('/dashboard');
      cy.url().should('include', '/dashboard');
    }
  });
});

// Login as staff member
Cypress.Commands.add('loginAsStaff', () => {
  cy.session('staff', () => {
    cy.visit('/staff/login');
    cy.get('#email, input[type="email"], input[name="email"]').first().type('admin@example.com');
    cy.get('#password, input[type="password"], input[name="password"]').first().type('admin123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  });
});

// Login as client
Cypress.Commands.add('loginAsClient', (email, password) => {
  cy.session(['client', email], () => {
    cy.visit('/portal/login');
    cy.get('#email, input[type="email"], input[name="email"]').first().type(email);
    cy.get('#password, input[type="password"], input[name="password"]').first().type(password);
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/portal');
  });
});

// Complete signup Step 1
Cypress.Commands.add('fillSignupStep1', () => {
  cy.get('#firstName, input[name*="first"]').first().type('Test');
  cy.get('#lastName, input[name*="last"]').first().type('User');
  cy.get('#email, input[type="email"]').first().type(`test${Date.now()}@example.com`);
  cy.get('#phone, input[type="tel"]').first().type('5551234567');
  cy.get('#addressStreet, input[name*="street"]').first().type('123 Test St');
  cy.get('#addressCity, input[name*="city"]').first().type('Test City');
  cy.get('#addressState, select[name*="state"]').first().select('CA');
  cy.get('#addressZip, input[name*="zip"]').first().type('90210');
  cy.get('#dateOfBirth, input[type="date"]').first().type('1990-01-01');
  cy.get('#ssnLast4, input[name*="ssn"]').first().type('1234');
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
