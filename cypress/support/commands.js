Cypress.Commands.add('login', (email = 'test@example.com', password = 'password123') => {
  cy.visit('/staff/login');
  cy.get('input[type="email"], input[name="email"], [data-testid="email-input"]', { timeout: 10000 }).first().type(email);
  cy.get('input[type="password"], input[name="password"], [data-testid="password-input"]').first().type(password);
  cy.get('button[type="submit"], [data-testid="login-button"]').first().click();
  cy.url().should('include', '/dashboard');
});