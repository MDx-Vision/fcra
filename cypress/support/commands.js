Cypress.Commands.add('login', (email = 'test@example.com', password = 'testpass123') => {
  cy.clearCookies();
  cy.visit('/staff/login');
  cy.get('input[type="email"]:visible, input[name="email"]:visible').first().type(email);
  cy.get('input[type="password"]:visible').first().type(password);
  cy.get('button[type="submit"]:visible').first().click();
  cy.url().should('include', '/dashboard');
});