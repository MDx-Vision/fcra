describe('Create Item (Staff Member)', () => {
  beforeEach(() => {
    cy.visit('/staff/login')
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
  })

  it('should create a new staff member successfully', () => {
    cy.visit('/dashboard/staff')
    
    cy.contains('button', 'Add Staff Member').click()
    
    cy.get('#addModal').should('be.visible')
    
    const uniqueId = Date.now()
    const testEmail = `teststaff${uniqueId}@example.com`
    
    cy.get('#addModal input[name="first_name"]').type('Test')
    cy.get('#addModal input[name="last_name"]').type('Product A')
    cy.get('#addModal input[name="email"]').type(testEmail)
    cy.get('#addModal select[name="role"]').select('paralegal')
    cy.get('#addModal input[name="password"]').type('TestPassword123!')
    
    cy.get('#addModal button[type="submit"]').click()
    
    cy.url().should('include', '/dashboard/staff')
    cy.contains('Test Product A').should('be.visible')
  })

  it('should display the new item in the staff list after creation', () => {
    cy.visit('/dashboard/staff')
    
    cy.contains('button', 'Add Staff Member').click()
    cy.get('#addModal').should('be.visible')
    
    const uniqueId = Date.now()
    const firstName = 'NewItem'
    const lastName = `Staff${uniqueId}`
    const testEmail = `newitem${uniqueId}@example.com`
    
    cy.get('#addModal input[name="first_name"]').type(firstName)
    cy.get('#addModal input[name="last_name"]').type(lastName)
    cy.get('#addModal input[name="email"]').type(testEmail)
    cy.get('#addModal select[name="role"]').select('viewer')
    cy.get('#addModal input[name="password"]').type('SecurePass456!')
    
    cy.get('#addModal button[type="submit"]').click()
    
    cy.get('#staffTable').should('be.visible')
    cy.get('#staffTable').contains(`${firstName} ${lastName}`).should('be.visible')
    cy.get('#staffTable').contains(testEmail).should('be.visible')
  })

  it('should show validation error for missing required fields', () => {
    cy.visit('/dashboard/staff')
    
    cy.contains('button', 'Add Staff Member').click()
    cy.get('#addModal').should('be.visible')
    
    cy.get('#addModal input[name="email"]').type('incomplete@example.com')
    
    cy.get('#addModal button[type="submit"]').click()
    
    cy.get('#addModal').should('be.visible')
  })
})
