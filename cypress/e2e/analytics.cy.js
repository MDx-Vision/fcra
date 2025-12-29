describe('Analytics Page', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123')
    cy.visit('/dashboard')
  })

  it('should load the analytics page', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="analytics-page"]').should('be.visible')
    cy.get('[data-testid="page-title"]').should('contain', 'Analytics Dashboard')
  })

  it('should display metrics grid with all cards', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="metrics-grid"]').should('be.visible')
    cy.get('[data-testid="metric-total-clients"]').should('be.visible')
    cy.get('[data-testid="metric-total-revenue"]').should('be.visible')
    cy.get('[data-testid="metric-total-analyses"]').should('be.visible')
    cy.get('[data-testid="metric-success-rate"]').should('be.visible')
  })

  it('should display charts', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="charts-grid-1"]').should('be.visible')
    cy.get('[data-testid="chart-signups"]').should('be.visible')
    cy.get('[data-testid="chart-status"]').should('be.visible')
    cy.get('[data-testid="charts-grid-2"]').should('be.visible')
    cy.get('[data-testid="chart-revenue"]').should('be.visible')
    cy.get('[data-testid="chart-scores"]').should('be.visible')
  })

  it('should display client status section', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="client-status-section"]').should('be.visible')
    cy.get('[data-testid="status-grid"]').should('be.visible')
    cy.get('[data-testid="status-active"]').should('be.visible')
    cy.get('[data-testid="status-signup"]').should('be.visible')
    cy.get('[data-testid="status-paused"]').should('be.visible')
    cy.get('[data-testid="status-complete"]').should('be.visible')
  })

  it('should display revenue section', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="revenue-section"]').should('be.visible')
    cy.get('[data-testid="revenue-stats-grid"]').should('be.visible')
    cy.get('[data-testid="revenue-this-month"]').should('be.visible')
    cy.get('[data-testid="revenue-last-month"]').should('be.visible')
    cy.get('[data-testid="revenue-all-time"]').should('be.visible')
  })

  it('should display case stats section with rounds', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="case-stats-section"]').should('be.visible')
    cy.get('[data-testid="round-grid"]').should('be.visible')
    cy.get('[data-testid="round-1"]').should('be.visible')
    cy.get('[data-testid="round-2"]').should('be.visible')
    cy.get('[data-testid="round-3"]').should('be.visible')
    cy.get('[data-testid="round-4"]').should('be.visible')
  })

  it('should display dispute progress section', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="dispute-progress-section"]').should('be.visible')
    cy.get('[data-testid="success-rate-container"]').should('be.visible')
    cy.get('[data-testid="progress-grid"]').should('be.visible')
    cy.get('[data-testid="progress-sent"]').should('be.visible')
    cy.get('[data-testid="progress-deleted"]').should('be.visible')
  })

  it('should display CRA response section', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="cra-response-section"]').should('be.visible')
    cy.get('[data-testid="cra-stats-grid"]').should('be.visible')
    cy.get('[data-testid="cra-total-responses"]').should('be.visible')
  })

  it('should display settlement analytics section', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="settlement-analytics-section"]').should('be.visible')
    cy.get('[data-testid="settlement-stats-grid"]').should('be.visible')
    cy.get('[data-testid="settlement-pipeline"]').should('be.visible')
  })

  it('should navigate back to dashboard', () => {
    cy.visit('/dashboard/analytics')
    cy.get('[data-testid="back-to-dashboard"]').click()
    cy.url().should('include', '/dashboard')
  })
})
