describe('Portal Login (Client-Facing)', () => {
  it('should load the portal login page', () => {
    cy.visit('/portal/login')
    cy.get('[data-testid="portal-login-container"]').should('be.visible')
    cy.get('[data-testid="portal-login-card"]').should('be.visible')
  })

  it('should display login form with all fields', () => {
    cy.visit('/portal/login')
    cy.get('[data-testid="login-title"]').should('contain', 'Welcome Back')
    cy.get('[data-testid="portal-email-input"]').should('be.visible')
    cy.get('[data-testid="portal-password-input"]').should('be.visible')
    cy.get('[data-testid="portal-login-button"]').should('be.visible')
  })

  it('should have forgot password link', () => {
    cy.visit('/portal/login')
    cy.get('[data-testid="forgot-password-link"]').should('be.visible')
    cy.get('[data-testid="forgot-password-link"]').should('contain', 'Forgot your password')
  })

  it('should have token access link', () => {
    cy.visit('/portal/login')
    cy.get('[data-testid="token-access-link"]').should('be.visible')
    cy.get('[data-testid="token-access-link"]').should('contain', 'Use direct link access')
  })

  it('should toggle password visibility', () => {
    cy.visit('/portal/login')
    cy.get('[data-testid="portal-password-input"]').should('have.attr', 'type', 'password')
    cy.get('[data-testid="toggle-password-btn"]').click()
    cy.get('[data-testid="portal-password-input"]').should('have.attr', 'type', 'text')
    cy.get('[data-testid="toggle-password-btn"]').click()
    cy.get('[data-testid="portal-password-input"]').should('have.attr', 'type', 'password')
  })

  it('should show forgot password form when clicking forgot link', () => {
    cy.visit('/portal/login')
    cy.get('[data-testid="forgot-password-link"]').click()
    cy.get('[data-testid="forgot-form-container"]').should('be.visible')
    cy.get('[data-testid="forgot-email-input"]').should('be.visible')
    cy.get('[data-testid="send-reset-button"]').should('be.visible')
  })

  it('should go back to login form from forgot password', () => {
    cy.visit('/portal/login')
    cy.get('[data-testid="forgot-password-link"]').click()
    cy.get('[data-testid="forgot-form-container"]').should('be.visible')
    cy.get('[data-testid="back-to-login-link"]').click()
    cy.get('[data-testid="login-form-container"]').should('be.visible')
    cy.get('[data-testid="forgot-form-container"]').should('not.be.visible')
  })

  it('should allow typing in login form', () => {
    cy.visit('/portal/login')
    cy.get('[data-testid="portal-email-input"]').type('client@example.com')
    cy.get('[data-testid="portal-email-input"]').should('have.value', 'client@example.com')
    cy.get('[data-testid="portal-password-input"]').type('testpassword')
    cy.get('[data-testid="portal-password-input"]').should('have.value', 'testpassword')
  })
})
