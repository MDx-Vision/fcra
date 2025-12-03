// Custom Cypress commands for FCRA Platform

// Login command - waits for page to load then enters credentials
Cypress.Commands.add('login', (email, password) => {
  cy.visit('/staff/login')
  cy.get('[data-testid="login-form"]').should('be.visible')
  cy.get('[data-testid="email-input"]').should('be.visible').clear().type(email)
  cy.get('[data-testid="password-input"]').should('be.visible').clear().type(password)
  cy.get('[data-testid="login-button"]').should('be.visible').click()
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

// Alternative login using ID selectors (fallback)
Cypress.Commands.add('loginById', (email, password) => {
  cy.visit('/staff/login')
  cy.get('#email').should('be.visible').clear().type(email)
  cy.get('#password').should('be.visible').clear().type(password)
  cy.get('#loginBtn, [data-testid="login-button"]').first().click()
})
