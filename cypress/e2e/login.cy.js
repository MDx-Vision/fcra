describe('Login', () => {
  it('should login successfully with valid credentials', () => {
    cy.visit('/staff/login')
    
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('button[type="submit"]').click()
    
    cy.url().should('include', '/dashboard')
  })

  it('should display welcome message after login', () => {
    cy.visit('/staff/login')
    
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('button[type="submit"]').click()
    
    cy.contains('Welcome').should('be.visible')
  })

  it('should reject invalid credentials', () => {
    cy.visit('/staff/login')
    
    cy.get('input[name="email"]').type('wrong@example.com')
    cy.get('input[name="password"]').type('wrongpassword')
    cy.get('button[type="submit"]').click()
    
    cy.url().should('include', '/staff/login')
  })
})
