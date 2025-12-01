describe('Settlements Page', () => {
  beforeEach(() => {
    cy.visit('/staff/login')
    cy.get('[data-testid="email-input"]').type('test@example.com')
    cy.get('[data-testid="password-input"]').type('password123')
    cy.get('[data-testid="login-button"]').click()
    cy.url().should('include', '/dashboard')
  })

  it('should load the settlements page', () => {
    cy.visit('/dashboard/settlements')
    cy.get('[data-testid="settlements-page"]').should('be.visible')
    cy.get('[data-testid="page-title"]').should('contain', 'Settlement Tracking')
  })

  it('should display stats grid with all cards', () => {
    cy.visit('/dashboard/settlements')
    cy.get('[data-testid="stats-grid"]').should('be.visible')
    cy.get('[data-testid="stat-total-settled"]').should('be.visible')
    cy.get('[data-testid="stat-pipeline-value"]').should('be.visible')
    cy.get('[data-testid="stat-avg-settlement"]').should('be.visible')
    cy.get('[data-testid="stat-contingency"]').should('be.visible')
  })

  it('should display pipeline section with all stages', () => {
    cy.visit('/dashboard/settlements')
    cy.get('[data-testid="pipeline-section"]').should('be.visible')
    cy.get('[data-testid="pipeline-stages"]').should('be.visible')
    cy.get('[data-testid="stage-pending"]').should('be.visible')
    cy.get('[data-testid="stage-demand-sent"]').should('be.visible')
    cy.get('[data-testid="stage-negotiating"]').should('be.visible')
    cy.get('[data-testid="stage-accepted"]').should('be.visible')
    cy.get('[data-testid="stage-rejected"]').should('be.visible')
    cy.get('[data-testid="stage-litigated"]').should('be.visible')
  })

  it('should display filters bar', () => {
    cy.visit('/dashboard/settlements')
    cy.get('[data-testid="filters-bar"]').should('be.visible')
    cy.get('[data-testid="filter-status"]').should('be.visible')
    cy.get('[data-testid="filter-date-from"]').should('be.visible')
    cy.get('[data-testid="filter-date-to"]').should('be.visible')
    cy.get('[data-testid="clear-filters-button"]').should('be.visible')
  })

  it('should display settlements table or empty state', () => {
    cy.visit('/dashboard/settlements')
    cy.get('[data-testid="settlements-section"]').should('be.visible')
    cy.get('body').then(($body) => {
      if ($body.find('[data-testid="settlements-table"]').length > 0) {
        cy.get('[data-testid="settlements-table"]').should('be.visible')
        cy.get('[data-testid="settlements-table-body"]').should('exist')
      } else {
        cy.get('[data-testid="empty-state"]').should('be.visible')
      }
    })
  })

  it('should navigate back to dashboard', () => {
    cy.visit('/dashboard/settlements')
    cy.get('[data-testid="back-to-dashboard"]').click()
    cy.url().should('include', '/dashboard')
  })

  it('should filter by status using dropdown', () => {
    cy.visit('/dashboard/settlements')
    cy.get('[data-testid="filter-status"]').select('pending')
    cy.get('[data-testid="filter-status"]').should('have.value', 'pending')
  })

  it('should filter by clicking pipeline stage', () => {
    cy.visit('/dashboard/settlements')
    cy.get('[data-testid="stage-pending"]').click()
    cy.get('[data-testid="stage-pending"]').should('have.class', 'active')
    cy.get('[data-testid="filter-status"]').should('have.value', 'pending')
  })

  it('should clear filters', () => {
    cy.visit('/dashboard/settlements')
    cy.get('[data-testid="filter-status"]').select('pending')
    cy.get('[data-testid="clear-filters-button"]').click()
    cy.get('[data-testid="filter-status"]').should('have.value', '')
  })
})
