Cypress.Commands.add('login', (email = 'test@example.com', password = 'testpass123') => {
  cy.request({
    method: 'POST',
    url: '/staff/login',
    form: true,
    body: {
      email: email,
      password: password
    }
  });
  cy.visit('/dashboard');
});