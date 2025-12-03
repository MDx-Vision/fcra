describe('Dashboard', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123')
    cy.url().should('include', '/dashboard')
  })

  it('should load the dashboard page', () => {
    cy.get('[data-testid="dashboard-page"]').should('be.visible')
    cy.get('[data-testid="page-title"]').should('contain', 'Dashboard')
  })

  it('should display stats grid with all cards', () => {
    cy.get('[data-testid="stats-grid"]').should('be.visible')
    cy.get('[data-testid="stat-total-value"]').should('be.visible')
    cy.get('[data-testid="stat-active-cases"]').should('be.visible')
    cy.get('[data-testid="stat-avg-score"]').should('be.visible')
    cy.get('[data-testid="stat-pending-review"]').should('be.visible')
  })

  it('should display pipeline section with all stages', () => {
    cy.get('[data-testid="pipeline-section"]').should('be.visible')
    cy.get('[data-testid="pipeline-stages"]').should('be.visible')
    cy.get('[data-testid="pipeline-intake"]').should('be.visible')
    cy.get('[data-testid="pipeline-stage1-pending"]').should('be.visible')
    cy.get('[data-testid="pipeline-stage1-complete"]').should('be.visible')
    cy.get('[data-testid="pipeline-stage2-pending"]').should('be.visible')
    cy.get('[data-testid="pipeline-stage2-complete"]').should('be.visible')
    cy.get('[data-testid="pipeline-delivered"]').should('be.visible')
  })

  it('should display quick actions section', () => {
    cy.get('[data-testid="quick-actions-section"]').should('be.visible')
    cy.get('[data-testid="quick-action-new-client"]').should('be.visible')
    cy.get('[data-testid="quick-action-batch"]').should('be.visible')
    cy.get('[data-testid="quick-action-review"]').should('be.visible')
    cy.get('[data-testid="quick-action-settlements"]').should('be.visible')
  })

  it('should display recent activity section', () => {
    cy.get('[data-testid="recent-activity-section"]').should('be.visible')
  })

  it('should open and close New Client modal', () => {
    cy.get('[data-testid="new-client-button"]').click()
    cy.get('[data-testid="intake-modal"]').should('be.visible')
    cy.get('[data-testid="intake-client-name"]').should('be.visible')
    cy.get('[data-testid="intake-modal-close"]').click()
    cy.get('[data-testid="intake-modal"]').should('not.be.visible')
  })

  it('should open and close Batch Upload modal', () => {
    cy.get('[data-testid="batch-upload-button"]').click()
    cy.get('[data-testid="batch-modal"]').should('be.visible')
    cy.get('[data-testid="batch-file-upload"]').should('be.visible')
    cy.get('[data-testid="batch-modal-close"]').click()
    cy.get('[data-testid="batch-modal"]').should('not.be.visible')
  })

  it('should have working search input', () => {
    cy.get('[data-testid="search-input"]').should('be.visible')
    cy.get('[data-testid="search-input"]').type('test')
    cy.get('[data-testid="search-input"]').should('have.value', 'test')
  })

  it('should have working filter buttons', () => {
    cy.get('[data-testid="case-filters"]').should('be.visible')
    cy.get('[data-testid="filter-all"]').should('have.class', 'active')
    cy.get('[data-testid="filter-needs-action"]').click()
    cy.get('[data-testid="filter-needs-action"]').should('have.class', 'active')
    cy.get('[data-testid="filter-all"]').should('not.have.class', 'active')
  })
})
