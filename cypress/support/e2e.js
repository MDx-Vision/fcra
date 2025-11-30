beforeEach(() => {
  cy.exec('npm run db:seed', { timeout: 60000 })
})

Cypress.Commands.add('login', (email, password) => {
  cy.visit('/staff/login')
  cy.get('input[name="email"]').type(email)
  cy.get('input[name="password"]').type(password)
  cy.get('button[type="submit"]').click()
})

Cypress.Commands.add('testUserLogin', () => {
  cy.login('test@example.com', 'password123')
})
