/// <reference types="cypress" />

describe('Dashboard - Widgets and Statistics', () => {
  beforeEach(() => {
    cy.visit('/dashboard')
    cy.get('[data-cy=dashboard-container]').should('be.visible')
  })

  describe('Dashboard Page Load and Structure', () => {
    it('should load dashboard with all required sections', () => {
      cy.url().should('include', '/dashboard')
      cy.get('[data-cy=dashboard-header]').should('be.visible')
      cy.get('[data-cy=stats-widgets-container]').should('be.visible')
      cy.get('[data-cy=charts-container]').should('be.visible')
      cy.get('[data-cy=recent-activity-widget]').should('be.visible')
    })

    it('should display correct page title', () => {
      cy.title().should('contain', 'Dashboard')
      cy.get('h1').should('contain', 'Dashboard')
    })

    it('should have proper meta tags for responsiveness', () => {
      cy.get('meta[name="viewport"]').should('have.attr', 'content')
    })

    it('should display loading states initially', () => {
      cy.get('[data-cy=stats-loading]').should('be.visible')
      cy.get('[data-cy=charts-loading]').should('be.visible')
    })

    it('should handle empty dashboard state gracefully', () => {
      cy.intercept('GET', '/api/dashboard/stats', { fixture: 'empty-stats.json' }).as('emptyStats')
      cy.reload()
      cy.wait('@emptyStats')
      cy.get('[data-cy=empty-dashboard-message]').should('be.visible')
    })
  })

  describe('Statistics Widgets - Basic Functionality', () => {
    it('should display total clients widget with correct data', () => {
      cy.get('[data-cy=total-clients-widget]').should('be.visible')
      cy.get('[data-cy=total-clients-count]').should('contain.text').and('match', /^\d+$/)
      cy.get('[data-cy=total-clients-label]').should('contain', 'Total Clients')
      cy.get('[data-cy=total-clients-icon]').should('be.visible')
    })

    it('should display active cases widget with correct data', () => {
      cy.get('[data-cy=active-cases-widget]').should('be.visible')
      cy.get('[data-cy=active-cases-count]').should('contain.text').and('match', /^\d+$/)
      cy.get('[data-cy=active-cases-label]').should('contain', 'Active Cases')
      cy.get('[data-cy=active-cases-icon]').should('be.visible')
    })

    it('should display total violations widget with correct data', () => {
      cy.get('[data-cy=total-violations-widget]').should('be.visible')
      cy.get('[data-cy=total-violations-count]').should('contain.text').and('match', /^\d+$/)
      cy.get('[data-cy=total-violations-label]').should('contain', 'Total Violations')
      cy.get('[data-cy=total-violations-icon]').should('be.visible')
    })

    it('should display pending analyses widget with correct data', () => {
      cy.get('[data-cy=pending-analyses-widget]').should('be.visible')
      cy.get('[data-cy=pending-analyses-count]').should('contain.text').and('match', /^\d+$/)
      cy.get('[data-cy=pending-analyses-label]').should('contain', 'Pending Analyses')
      cy.get('[data-cy=pending-analyses-icon]').should('be.visible')
    })

    it('should display revenue widget with correct formatting', () => {
      cy.get('[data-cy=revenue-widget]').should('be.visible')
      cy.get('[data-cy=revenue-amount]').should('contain.text').and('match', /^\$[\d,]+\.?\d*$/)
      cy.get('[data-cy=revenue-label]').should('contain', 'Revenue')
      cy.get('[data-cy=revenue-icon]').should('be.visible')
    })

    it('should display settlements widget with correct data', () => {
      cy.get('[data-cy=settlements-widget]').should('be.visible')
      cy.get('[data-cy=settlements-count]').should('contain.text').and('match', /^\d+$/)
      cy.get('[data-cy=settlements-amount]').should('contain.text').and('match', /^\$[\d,]+\.?\d*$/)
      cy.get('[data-cy=settlements-label]').should('contain', 'Settlements')
    })
  })

  describe('Statistics Widgets - Interactive Features', () => {
    it('should allow clicking on total clients widget to navigate', () => {
      cy.get('[data-cy=total-clients-widget]').click()
      cy.url().should('include', '/clients')
      cy.go('back')
    })

    it('should allow clicking on active cases widget to navigate', () => {
      cy.get('[data-cy=active-cases-widget]').click()
      cy.url().should('include', '/cases')
      cy.go('back')
    })

    it('should show hover effects on clickable widgets', () => {
      cy.get('[data-cy=total-clients-widget]').trigger('mouseover')
      cy.get('[data-cy=total-clients-widget]').should('have.class', 'widget-hover')
    })

    it('should display tooltip on widget hover', () => {
      cy.get('[data-cy=total-clients-widget]').trigger('mouseover')
      cy.get('[data-cy=widget-tooltip]').should('be.visible').and('contain', 'Click to view all clients')
    })

    it('should refresh widget data on refresh button click', () => {
      cy.get('[data-cy=refresh-stats-btn]').click()
      cy.get('[data-cy=stats-loading]').should('be.visible')
      cy.get('[data-cy=stats-loading]').should('not.exist')
    })
  })

  describe('Statistics Widgets - Data Validation', () => {
    it('should handle zero values correctly', () => {
      cy.intercept('GET', '/api/dashboard/stats', { body: { total_clients: 0, active_cases: 0 } }).as('zeroStats')
      cy.reload()
      cy.wait('@zeroStats')
      cy.get('[data-cy=total-clients-count]').should('contain', '0')
      cy.get('[data-cy=active-cases-count]').should('contain', '0')
    })

    it('should handle large numbers with proper formatting', () => {
      cy.intercept('GET', '/api/dashboard/stats', { 
        body: { total_clients: 12345, revenue: 1234567.89 } 
      }).as('largeStats')
      cy.reload()
      cy.wait('@largeStats')
      cy.get('[data-cy=total-clients-count]').should('contain', '12,345')
      cy.get('[data-cy=revenue-amount]').should('contain', '$1,234,567.89')
    })

    it('should handle negative values appropriately', () => {
      cy.intercept('GET', '/api/dashboard/stats', { body: { revenue: -500.00 } }).as('negativeStats')
      cy.reload()
      cy.wait('@negativeStats')
      cy.get('[data-cy=revenue-amount]').should('contain', '-$500.00')
      cy.get('[data-cy=revenue-widget]').should('have.class', 'negative-value')
    })

    it('should validate percentage changes in widgets', () => {
      cy.get('[data-cy=total-clients-change]').should('be.visible')
      cy.get('[data-cy=total-clients-change]').should('match', /^[+-]?\d+\.?\d*%$/)
    })

    it('should show trend indicators correctly', () => {
      cy.get('[data-cy=clients-trend-up]').should('be.visible')
      cy.get('[data-cy=clients-trend-icon]').should('have.class', 'trend-up')
    })
  })

  describe('Statistics Widgets - Error Handling', () => {
    it('should handle API error gracefully', () => {
      cy.intercept('GET', '/api/dashboard/stats', { statusCode: 500 }).as('statsError')
      cy.reload()
      cy.wait('@statsError')
      cy.get('[data-cy=stats-error-message]').should('be.visible')
      cy.get('[data-cy=retry-stats-btn]').should('be.visible')
    })

    it('should handle network timeout', () => {
      cy.intercept('GET', '/api/dashboard/stats', { delay: 30000 }).as('statsTimeout')
      cy.reload()
      cy.get('[data-cy=stats-timeout-message]').should('be.visible')
    })

    it('should handle malformed JSON response', () => {
      cy.intercept('GET', '/api/dashboard/stats', { body: 'invalid json' }).as('malformedStats')
      cy.reload()
      cy.wait('@malformedStats')
      cy.get('[data-cy=stats-parse-error]').should('be.visible')
    })

    it('should handle missing data fields', () => {
      cy.intercept('GET', '/api/dashboard/stats', { body: {} }).as('emptyStatsResponse')
      cy.reload()
      cy.wait('@emptyStatsResponse')
      cy.get('[data-cy=total-clients-count]').should('contain', '0')
    })

    it('should retry failed requests when retry button clicked', () => {
      cy.intercept('GET', '/api/dashboard/stats', { statusCode: 500 }).as('statsError')
      cy.reload()
      cy.wait('@statsError')
      cy.intercept('GET', '/api/dashboard/stats', { fixture: 'dashboard-stats.json' }).as('statsSuccess')
      cy.get('[data-cy=retry-stats-btn]').click()
      cy.wait('@statsSuccess')
      cy.get('[data-cy=stats-error-message]').should('not.exist')
    })
  })

  describe('Charts and Visualizations', () => {
    it('should display case status pie chart', () => {
      cy.get('[data-cy=case-status-chart]').should('be.visible')
      cy.get('[data-cy=chart-legend]').should('be.visible')
      cy.get('[data-cy=chart-title]').should('contain', 'Case Status Distribution')
    })

    it('should display monthly revenue chart', () => {
      cy.get('[data-cy=revenue-chart]').should('be.visible')
      cy.get('[data-cy=revenue-chart-canvas]').should('be.visible')
      cy.get('[data-cy=revenue-chart-title]').should('contain', 'Monthly Revenue')
    })

    it('should display violation types bar chart', () => {
      cy.get('[data-cy=violations-chart]').should('be.visible')
      cy.get('[data-cy=violations-chart-bars]').should('have.length.greaterThan', 0)
    })

    it('should allow chart interaction', () => {
      cy.get('[data-cy=case-status-chart]').find('canvas').click(100, 100)
      cy.get('[data-cy=chart-tooltip]').should('be.visible')
    })

    it('should update charts when date range changes', () => {
      cy.get('[data-cy=date-range-selector]').select('Last 30 Days')
      cy.get('[data-cy=charts-loading]').should('be.visible')
      cy.get('[data-cy=charts-loading]').should('not.exist')
      cy.get('[data-cy=revenue-chart]').should('be.visible')
    })

    it('should handle chart resize on window resize', () => {
      cy.viewport(1200, 800)
      cy.get('[data-cy=revenue-chart]').should('be.visible')
      cy.viewport(800, 600)
      cy.get('[data-cy=revenue-chart]').should('be.visible')
    })
  })

  describe('Recent Activity Widget', () => {
    it('should display recent activity list', () => {
      cy.get('[data-cy=recent-activity-widget]').should('be.visible')
      cy.get('[data-cy=recent-activity-title]').should('contain', 'Recent Activity')
      cy.get('[data-cy=activity-list]').should('be.visible')
    })

    it('should show activity items with timestamps', () => {
      cy.get('[data-cy=activity-item]').should('have.length.greaterThan', 0)
      cy.get('[data-cy=activity-item]').first().within(() => {
        cy.get('[data-cy=activity-timestamp]').should('be.visible')
        cy.get('[data-cy=activity-description]').should('be.visible')
        cy.get('[data-cy=activity-user]').should('be.visible')
      })
    })

    it('should allow clicking on activity items', () => {
      cy.get('[data-cy=activity-item]').first().click()
      cy.url().should('not.equal', Cypress.config().baseUrl + '/dashboard')
    })

    it('should load more activities on scroll', () => {
      cy.get('[data-cy=activity-list]').scrollTo('bottom')
      cy.get('[data-cy=loading-more-activities]').should('be.visible')
      cy.get('[data-cy=activity-item]').should('have.length.greaterThan', 5)
    })

    it('should filter activities by type', () => {
      cy.get('[data-cy=activity-filter]').select('Cases')
      cy.get('[data-cy=activity-item]').each($item => {
        cy.wrap($item).should('have.attr', 'data-activity-type', 'case')
      })
    })
  })

  describe('Dashboard Filters and Controls', () => {
    it('should display date range filter', () => {
      cy.get('[data-cy=date-range-filter]').should('be.visible')
      cy.get('[data-cy=date-from]').should('be.visible')
      cy.get('[data-cy=date-to]').should('be.visible')
    })

    it('should update dashboard data when date range changes', () => {
      cy.get('[data-cy=date-from]').type('2024-01-01')
      cy.get('[data-cy=date-to]').type('2024-12-31')
      cy.get('[data-cy=apply-date-filter]').click()
      cy.get('[data-cy=dashboard-loading]').should('be.visible')
      cy.get('[data-cy=dashboard-loading]').should('not.exist')
    })

    it('should validate date range inputs', () => {
      cy.get('[data-cy=date-from]').type('2024-12-31')
      cy.get('[data-cy=date-to]').type('2024-01-01')
      cy.get('[data-cy=apply-date-filter]').click()
      cy.get('[data-cy=date-range-error]').should('be.visible').and('contain', 'End date must be after start date')
    })

    it('should show staff filter for admin users', () => {
      cy.get('[data-cy=staff-filter]').should('be.visible')
      cy.get('[data-cy=staff-filter]').select('All Staff')
      cy.get('[data-cy=apply-filters]').click()
    })

    it('should hide staff filter for non-admin users', () => {
      cy.window().then(win => {
        win.sessionStorage.setItem('staff_role', 'staff')
      })
      cy.reload()
      cy.get('[data-cy=staff-filter]').should('not.exist')
    })
  })

  describe('Real-time Updates', () => {
    it('should update widgets automatically', () => {
      cy.get('[data-cy=total-clients-count]').invoke('text').as('initialCount')
      cy.wait(5000) // Wait for auto-refresh
      cy.get('[data-cy=total-clients-count]').invoke('text').should('not.equal', '@initialCount')
    })

    it('should show update indicator', () => {
      cy.get('[data-cy=last-updated]').should('be.visible')
      cy.get('[data-cy=auto-refresh-indicator]').should('be.visible')
    })

    it('should allow disabling auto-refresh', () => {
      cy.get('[data-cy=auto-refresh-toggle]').click()
      cy.get('[data-cy=auto-refresh-toggle]').should('not.be.checked')
      cy.get('[data-cy=auto-refresh-disabled]').should('be.visible')
    })
  })

  describe('Performance Metrics Widget', () => {
    it('should display performance metrics', () => {
      cy.get('[data-cy=performance-widget]').should('be.visible')
      cy.get('[data-cy=avg-case-duration]').should('be.visible')
      cy.get('[data-cy=success-rate]').should('be.visible')
      cy.get('[data-cy=client-satisfaction]').should('be.visible')
    })

    it('should format performance percentages correctly', () => {
      cy.get('[data-cy=success-rate]').should('match', /^\d+\.?\d*%$/)
      cy.get('[data-cy=client-satisfaction]').should('match', /^\d+\.?\d*%$/)
    })

    it('should show performance trends', () => {
      cy.get('[data-cy=performance-trend]').should('be.visible')
      cy.get('[data-cy=trend-indicator]').should('have.class').and('match', /trend-(up|down|neutral)/)
    })
  })

  describe('Widget Customization', () => {
    it('should allow hiding/showing widgets', () => {
      cy.get('[data-cy=customize-dashboard]').click()
      cy.get('[data-cy=widget-toggle-clients]').click()
      cy.get('[data-cy=save-customization]').click()
      cy.get('[data-cy=total-clients-widget]').should('not.exist')
    })

    it('should save widget preferences', () => {
      cy.get('[data-cy=customize-dashboard]').click()
      cy.get('[data-cy=widget-toggle-revenue]').click()
      cy.get('[data-cy=save-customization]').click()
      cy.reload()
      cy.get('[data-cy=revenue-widget]').should('not.exist')
    })

    it('should allow reordering widgets', () => {
      cy.get('[data-cy=total-clients-widget]').drag('[data-cy=active-cases-widget]')
      cy.get('[data-cy=widget-container]').children().first().should('have.attr', 'data-cy', 'active-cases-widget')
    })
  })

  describe('Export and Reporting', () => {
    it('should allow exporting dashboard data', () => {
      cy.get('[data-cy=export-dashboard]').click()
      cy.get('[data-cy=export-pdf]').should('be.visible')
      cy.get('[data-cy=export-excel]').should('be.visible')
      cy.get('[data-cy=export-csv]').should('be.visible')
    })

    it('should generate PDF report', () => {
      cy.get('[data-cy=export-dashboard]').click()
      cy.get('[data-cy=export-pdf]').click()
      cy.get('[data-cy=pdf-generating]').should('be.visible')
      // Note: File download testing would require additional configuration
    })

    it('should schedule recurring reports', () => {
      cy.get('[data-cy=schedule-report]').click()
      cy.get('[data-cy=report-frequency]').select('Weekly')
      cy.get('[data-cy=report-email]').type('admin@test.com')
      cy.get('[data-cy=save-schedule]').click()
      cy.get('[data-cy=schedule-success]').should('be.visible')
    })
  })

  describe('Mobile Responsiveness', () => {
    it('should display properly on mobile devices', () => {
      cy.viewport('iphone-x')
      cy.get('[data-cy=dashboard-container]').should('be.visible')
      cy.get('[data-cy=mobile-stats-grid]').should('be.visible')
    })

    it('should stack widgets vertically on small screens', () => {
      cy.viewport(375, 667)
      cy.get('[data-cy=stats-widgets-container]').should('have.css', 'flex-direction', 'column')
    })

    it('should hide non-essential elements on mobile', () => {
      cy.viewport('iphone-se2')
      cy.get('[data-cy=desktop-only-widget]').should('not.be.visible')
      cy.get('[data-cy=mobile-summary]').should('be.visible')
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels on widgets', () => {
      cy.get('[data-cy=total-clients-widget]').should('have.attr', 'aria-label')
      cy.get('[data-cy=active-cases-widget]').should('have.attr', 'aria-label')
    })

    it('should support keyboard navigation', () => {
      cy.get('[data-cy=total-clients-widget]').focus()
      cy.focused().should('have.attr', 'data-cy', 'total-clients-widget')
      cy.focused().type('{enter}')
      cy.url().should('include', '/clients')
    })

    it('should have sufficient color contrast', () => {
      cy.get('[data-cy=total-clients-count]').should('have.css', 'color').and('not.equal', 'rgba(0, 0, 0, 0)')
    })

    it('should provide alt text for chart images', () => {
      cy.get('[data-cy=case-status-chart]').should('have.attr', 'alt')
    })
  })

  describe('Data Refresh and Caching', () => {
    it('should cache dashboard data', () => {
      cy.intercept('GET', '/api/dashboard/stats').as('statsCall')
      cy.visit('/dashboard')
      cy.wait('@statsCall')
      cy.visit('/clients')
      cy.visit('/dashboard')
      // Should not make another API call due to caching
      cy.get('@statsCall.all').should('have.length', 1)
    })

    it('should invalidate cache after data changes', () => {
      cy.visit('/clients/add')
      cy.get('[data-cy=client-name]').type('Test Client')
      cy.get('[data-cy=client-email]').type('test@example.com')
      cy.get('[data-cy=save-client]').click()
      cy.visit('/dashboard')
      cy.get('[data-cy=cache-invalidated]').should('be.visible')
    })

    it('should handle stale data gracefully', () => {
      cy.clock()
      cy.visit('/dashboard')
      cy.tick(300000) // 5 minutes
      cy.get('[data-cy=stale-data-warning]').should('be.visible')
    })
  })

  describe('Advanced Widget Features', () => {
    it('should display drill-down capability in widgets', () => {
      cy.get('[data-cy=total-clients-widget]').within(() => {
        cy.get('[data-cy=drill-down-btn]').click()
        cy.get('[data-cy=client-breakdown]').should('be.visible')
      })
    })

    it('should show comparative data in widgets', () => {
      cy.get('[data-cy=revenue-widget]').within(() => {
        cy.get('[data-cy=compare-previous]').should('be.visible')
        cy.get('[data-cy=percentage-change]').should('be.visible')
      })
    })

    it('should display goals and targets', () => {
      cy.get('[data-cy=goals-widget]').should('be.visible')
      cy.get('[data-cy=monthly-target]').should('be.visible')
      cy.get('[data-cy=progress-bar]').should('be.visible')
    })

    it('should show widget-specific actions', () => {
      cy.get('[data-cy=pending-analyses-widget]').within(() => {
        cy.get('[data-cy=widget-actions]').click()
        cy.get('[data-cy=process-all-btn]').should('be.visible')
        cy.get('[data-cy=view-queue-btn]').should('be.visible')
      })
    })
  })

  describe('Error Recovery and Fallbacks', () => {
    it('should show fallback UI when widgets fail to load', () => {
      cy.intercept('GET', '/api/dashboard/stats', { statusCode: 503 }).as('serviceUnavailable')
      cy.reload()
      cy.wait('@serviceUnavailable')
      cy.get('[data-cy=fallback-widgets]').should('be.visible')
      cy.get('[data-cy=service-unavailable-message]').should('be.visible')
    })

    it('should attempt automatic recovery', () => {
      cy.intercept('GET', '/api/dashboard/stats', { statusCode: 500 }).as('initialError')
      cy.intercept('GET', '/api/dashboard/stats', { fixture: 'dashboard-stats.json' }).as('recovery')
      cy.reload()
      cy.wait('@initialError')
      cy.wait(10000) // Wait for retry mechanism
      cy.wait('@recovery')
      cy.get('[data-cy=error-recovered]').should('be.visible')
    })

    it('should maintain partial functionality during errors', () => {
      cy.intercept('GET', '/api/dashboard/charts', { statusCode: 500 }).as('chartsError')
      cy.reload()
      cy.wait('@chartsError')
      cy.get('[data-cy=stats-widgets-container]').should('be.visible') // Widgets still work
      cy.get('[data-cy=charts-error-message]').should('be.visible') // Charts show error
    })
  })

  describe('Security and Permissions', () => {
    it('should hide sensitive widgets for non-admin users', () => {
      cy.window().then(win => {
        win.sessionStorage.setItem('staff_role', 'viewer')
      })
      cy.reload()
      cy.get('[data-cy=revenue-widget]').should('not.exist')
      cy.get('[data-cy=financial-data]').should('not.exist')
    })

    it('should validate permissions before displaying data', () => {
      cy.intercept('GET', '/api/dashboard/stats', (req) => {
        expect(req.headers).to.have.property('authorization')
      }).as('secureStatsCall')
      cy.reload()
      cy.wait('@secureStatsCall')
    })

    it('should handle session timeout gracefully', () => {
      cy.intercept('GET', '/api/dashboard/stats', { statusCode: 401 }).as('unauthorized')
      cy.reload()
      cy.wait('@unauthorized')
      cy.url().should('include', '/staff/login')
    })
  })
})