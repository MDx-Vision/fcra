describe('Create Item (Staff Member)', () => {
  beforeEach(() => {
    cy.visit('/staff/login')
    cy.get('[data-testid="email-input"]').type('test@example.com')
    cy.get('[data-testid="password-input"]').type('password123')
    cy.get('[data-testid="login-button"]').click()
    cy.url().should('include', '/dashboard')
  })

  it('should create a new staff member successfully', () => {
    cy.visit('/dashboard/staff')

    cy.get('[data-testid="add-staff-button"]').click()

    cy.get('[data-testid="add-modal"]').should('be.visible')

    const uniqueId = Date.now()
    const testEmail = `teststaff${uniqueId}@example.com`

    cy.get('[data-testid="add-first-name"]').type('Test')
    cy.get('[data-testid="add-last-name"]').type('Product A')
    cy.get('[data-testid="add-email"]').type(testEmail)
    cy.get('[data-testid="add-role"]').select('paralegal')
    cy.get('[data-testid="add-password"]').type('TestPassword123!')

    cy.get('[data-testid="add-submit-button"]').click()

    cy.url().should('include', '/dashboard/staff')
    cy.contains('Test Product A').should('be.visible')
  })

  it('should display the new item in the staff list after creation', () => {
    cy.visit('/dashboard/staff')

    cy.get('[data-testid="add-staff-button"]').click()
    cy.get('[data-testid="add-modal"]').should('be.visible')

    const uniqueId = Date.now()
    const firstName = 'NewItem'
    const lastName = `Staff${uniqueId}`
    const testEmail = `newitem${uniqueId}@example.com`

    cy.get('[data-testid="add-first-name"]').type(firstName)
    cy.get('[data-testid="add-last-name"]').type(lastName)
    cy.get('[data-testid="add-email"]').type(testEmail)
    cy.get('[data-testid="add-role"]').select('viewer')
    cy.get('[data-testid="add-password"]').type('SecurePass456!')

    cy.get('[data-testid="add-submit-button"]').click()

    cy.get('[data-testid="staff-table"]').should('be.visible')
    cy.get('[data-testid="staff-table"]').contains(`${firstName} ${lastName}`).should('be.visible')
    cy.get('[data-testid="staff-table"]').contains(testEmail).should('be.visible')
  })

  it('should show validation error for missing required fields', () => {
    cy.visit('/dashboard/staff')

    cy.get('[data-testid="add-staff-button"]').click()
    cy.get('[data-testid="add-modal"]').should('be.visible')

    cy.get('[data-testid="add-email"]').type('incomplete@example.com')

    cy.get('[data-testid="add-submit-button"]').click()

    cy.get('[data-testid="add-modal"]').should('be.visible')
  })
})