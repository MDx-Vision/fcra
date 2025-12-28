describe('Login', () => {
  it('should login successfully with valid credentials', () => {
    cy.login('test@example.com', 'testpass123')
    cy.url().should('include', '/staff')
  })

  it('should display staff portal after login', () => {
    cy.login('test@example.com', 'testpass123')
    cy.get('body').should('be.visible')
  })

  it('should reject invalid credentials', () => {
    cy.visit('/staff/login')
    cy.get('[data-testid="login-form"]').should('be.visible')
    cy.get('[data-testid="email-input"]').type('wrong@example.com')
    cy.get('[data-testid="password-input"]').type('wrongpassword')
    cy.get('[data-testid="login-button"]').click()
    cy.url().should('include', '/staff/login')
  })

  it('should display login form elements', () => {
    cy.visit('/staff/login')
    cy.get('[data-testid="login-container"]').should('be.visible')
    cy.get('[data-testid="login-card"]').should('be.visible')
    cy.get('[data-testid="login-form"]').should('be.visible')
    cy.get('[data-testid="email-input"]').should('be.visible')
    cy.get('[data-testid="password-input"]').should('be.visible')
    cy.get('[data-testid="login-button"]').should('be.visible')
  })

  it('should have client portal link', () => {
    cy.visit('/staff/login')
    cy.get('[data-testid="client-portal-link"]').should('be.visible')
    cy.get('[data-testid="client-portal-link"]').should('have.attr', 'href', '/portal/login')
  })
})
