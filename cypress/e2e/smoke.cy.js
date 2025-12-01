describe('Smoke Tests', () => {
  it('loads the home page', () => {
    cy.visit('/')
    cy.get('body').should('be.visible')
  })

  it('loads the staff login page', () => {
    cy.visit('/staff/login')
    cy.get('[data-testid="email-input"]').should('be.visible')
    cy.get('[data-testid="password-input"]').should('be.visible')
    cy.get('[data-testid="login-button"]').should('be.visible')
  })

  it('loads the Metro 2 reference API', () => {
    cy.request('/api/metro2/reference?type=all').then((response) => {
      expect(response.status).to.eq(200)
      expect(response.body.success).to.eq(true)
      expect(response.body.data).to.have.property('account_status_codes')
    })
  })
})