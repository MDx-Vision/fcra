describe('Smoke Tests', () => {
  it('loads the home page', () => {
    cy.visit('/')
    cy.get('body').should('be.visible')
  })

  it('loads the staff login page', () => {
    cy.visit('/staff/login')
    cy.get('input[name="email"]').should('be.visible')
    cy.get('input[name="password"]').should('be.visible')
  })

  it('loads the Metro 2 reference API', () => {
    cy.request('/api/metro2/reference?type=all').then((response) => {
      expect(response.status).to.eq(200)
      expect(response.body.success).to.eq(true)
      expect(response.body.data).to.have.property('account_status_codes')
    })
  })
})
