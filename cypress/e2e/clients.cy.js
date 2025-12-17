describe('Clients Page', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123')
    cy.url().should('include', '/dashboard')
  })

  it('should load the clients page', () => {
    cy.visit('/dashboard/clients')
    cy.get('[data-testid="clients-page"]').should('be.visible')
    cy.get('[data-testid="page-title"]').should('contain', 'All Clients')
  })

  it('should display filters', () => {
    cy.visit('/dashboard/clients')
    cy.get('[data-testid="filters"]').should('be.visible')
    cy.get('[data-testid="filter-all"]').should('be.visible')
    cy.get('[data-testid="filter-needs-review"]').should('be.visible')
    cy.get('[data-testid="filter-ready-to-deliver"]').should('be.visible')
  })

  it('should have search input', () => {
    cy.visit('/dashboard/clients')
    cy.get('[data-testid="search-input"]').should('be.visible')
    cy.get('[data-testid="search-input"]').type('test')
    cy.get('[data-testid="search-input"]').should('have.value', 'test')
  })

  it('should display clients table or empty state', () => {
    cy.visit('/dashboard/clients')
    cy.get('[data-testid="clients-card"]').should('be.visible')
    cy.get('body').then(($body) => {
      if ($body.find('[data-testid="clients-table"]').length > 0) {
        cy.get('[data-testid="clients-table"]').should('be.visible')
        cy.get('[data-testid="clients-table-body"]').should('exist')
      } else {
        cy.get('[data-testid="empty-state"]').should('be.visible')
      }
    })
  })

  it('should navigate back to dashboard', () => {
    cy.visit('/dashboard/clients')
    cy.get('[data-testid="back-to-dashboard"]').click()
    cy.url().should('include', '/dashboard')
    cy.url().should('not.include', '/clients')
  })

  it('should filter by needs review', () => {
    cy.visit('/dashboard/clients')
    cy.get('[data-testid="filter-needs-review"]').click()
    cy.url().should('include', 'status=stage1_complete')
  })

  it('should filter by ready to deliver', () => {
    cy.visit('/dashboard/clients')
    cy.get('[data-testid="filter-ready-to-deliver"]').click()
    cy.url().should('include', 'status=stage2_complete')
  })
})
