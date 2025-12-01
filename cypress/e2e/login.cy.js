describe('Login', () => {
  it('should login successfully with valid credentials', () => {
    cy.visit('/staff/login')

    cy.get('[data-testid="email-input"]').type('test@example.com')
    cy.get('[data-testid="password-input"]').type('password123')
    cy.get('[data-testid="login-button"]').click()

    cy.url().should('include', '/dashboard')
  })

  it('should display dashboard after login', () => {
    cy.visit('/staff/login')

    cy.get('[data-testid="email-input"]').type('test@example.com')
    cy.get('[data-testid="password-input"]').type('password123')
    cy.get('[data-testid="login-button"]').click()

    cy.contains('Dashboard').should('be.visible')
  })

  it('should reject invalid credentials', () => {
    cy.visit('/staff/login')

    cy.get('[data-testid="email-input"]').type('wrong@example.com')
    cy.get('[data-testid="password-input"]').type('wrongpassword')
    cy.get('[data-testid="login-button"]').click()

    cy.url().should('include', '/staff/login')
  })
})