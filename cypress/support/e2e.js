// Import custom commands
import './commands'

// Only seed database once before all tests in a spec file
before(() => {
  cy.exec('npm run db:seed', { timeout: 60000, failOnNonZeroExit: false })
})

// Handle uncaught exceptions gracefully
Cypress.on('uncaught:exception', (err, runnable) => {
  return false
})

// Set up console.error spy on each page load for "has no console errors" checks
Cypress.on('window:before:load', (win) => {
  cy.spy(win.console, 'error').as('consoleError')
})
