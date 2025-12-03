// Only seed database once before all tests in a spec file
before(() => {
  cy.exec('npm run db:seed', { timeout: 60000, failOnNonZeroExit: false })
})

// Custom login command using data-testid selectors
Cypress.Commands.add('login', (email, password) => {
  cy.visit('/staff/login')
  cy.get('[data-testid="email-input"]').type(email)
  cy.get('[data-testid="password-input"]').type(password)
  cy.get('[data-testid="login-button"]').click()
})

// Quick login with test user
Cypress.Commands.add('testUserLogin', () => {
  cy.login('test@example.com', 'password123')
})

// Login and navigate to a page
Cypress.Commands.add('loginAndVisit', (path) => {
  cy.testUserLogin()
  cy.url().should('include', '/dashboard')
  cy.visit(path)
})

// Handle uncaught exceptions gracefully
Cypress.on('uncaught:exception', (err, runnable) => {
  // Don't fail tests on uncaught exceptions from the app
  return false
})
