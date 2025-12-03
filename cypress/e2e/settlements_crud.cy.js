describe('Settlements Page - Comprehensive Tests', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123')
    cy.url().should('include', '/dashboard')
    cy.visit('/dashboard/settlements')
  })

  describe('Page Load & Structure', () => {
    it('should load the settlements page', () => {
      cy.get('[data-testid="settlements-page"]').should('be.visible')
    })

    it('should display the page title', () => {
      cy.get('[data-testid="page-title"]').should('be.visible')
      cy.get('[data-testid="page-title"]').should('contain', 'Settlement')
    })

    it('should display back to dashboard button', () => {
      cy.get('[data-testid="back-to-dashboard"]').should('be.visible')
    })

    it('should have correct page URL', () => {
      cy.url().should('include', '/dashboard/settlements')
    })

    it('should display stats grid', () => {
      cy.get('[data-testid="stats-grid"]').should('be.visible')
    })

    it('should display pipeline section', () => {
      cy.get('[data-testid="pipeline-section"]').should('be.visible')
    })

    it('should display settlements section', () => {
      cy.get('[data-testid="settlements-section"]').should('be.visible')
    })
  })

  describe('Navigation', () => {
    it('should navigate back to dashboard when clicking back button', () => {
      cy.get('[data-testid="back-to-dashboard"]').click()
      cy.url().should('include', '/dashboard')
      cy.url().should('not.include', '/settlements')
    })
  })

  describe('Stats Grid - Structure', () => {
    it('should display Total Settled stat card', () => {
      cy.get('[data-testid="stat-total-settled"]').should('be.visible')
    })

    it('should display Pipeline Value stat card', () => {
      cy.get('[data-testid="stat-pipeline-value"]').should('be.visible')
    })

    it('should display Average Settlement stat card', () => {
      cy.get('[data-testid="stat-avg-settlement"]').should('be.visible')
    })

    it('should display Contingency Earned stat card', () => {
      cy.get('[data-testid="stat-contingency"]').should('be.visible')
    })
  })

  describe('Stats Grid - Values', () => {
    it('should display Total Settled value with dollar sign', () => {
      cy.get('[data-testid="stat-total-settled-value"]').invoke('text').should('match', /\$[\d,]+/)
    })

    it('should display Pipeline Value with dollar sign', () => {
      cy.get('[data-testid="stat-pipeline-value-amount"]').invoke('text').should('match', /\$[\d,]+/)
    })

    it('should display Average Settlement value with dollar sign', () => {
      cy.get('[data-testid="stat-avg-settlement-value"]').invoke('text').should('match', /\$[\d,]+/)
    })

    it('should display Contingency value with dollar sign', () => {
      cy.get('[data-testid="stat-contingency-value"]').invoke('text').should('match', /\$[\d,]+/)
    })

    it('should have success class on Total Settled card', () => {
      cy.get('[data-testid="stat-total-settled"]').should('have.class', 'success')
    })

    it('should have highlight class on Pipeline Value card', () => {
      cy.get('[data-testid="stat-pipeline-value"]').should('have.class', 'highlight')
    })
  })

  describe('Pipeline Stages - Structure', () => {
    it('should display pipeline stages container', () => {
      cy.get('[data-testid="pipeline-stages"]').should('be.visible')
    })

    it('should display Pending stage', () => {
      cy.get('[data-testid="stage-pending"]').should('be.visible')
    })

    it('should display Demand Sent stage', () => {
      cy.get('[data-testid="stage-demand-sent"]').should('be.visible')
    })

    it('should display Negotiating stage', () => {
      cy.get('[data-testid="stage-negotiating"]').should('be.visible')
    })

    it('should display Accepted stage', () => {
      cy.get('[data-testid="stage-accepted"]').should('be.visible')
    })

    it('should display Rejected stage', () => {
      cy.get('[data-testid="stage-rejected"]').should('be.visible')
    })

    it('should display Litigated stage', () => {
      cy.get('[data-testid="stage-litigated"]').should('be.visible')
    })

    it('should display 6 pipeline stages total', () => {
      cy.get('[data-testid="pipeline-stages"]').children().should('have.length', 6)
    })
  })

  describe('Pipeline Stages - Content', () => {
    it('should display numeric count in Pending stage', () => {
      cy.get('[data-testid="stage-pending"]').find('.stage-count').invoke('text').should('match', /\d+/)
    })

    it('should display numeric count in Demand Sent stage', () => {
      cy.get('[data-testid="stage-demand-sent"]').find('.stage-count').invoke('text').should('match', /\d+/)
    })

    it('should display numeric count in Negotiating stage', () => {
      cy.get('[data-testid="stage-negotiating"]').find('.stage-count').invoke('text').should('match', /\d+/)
    })

    it('should display numeric count in Accepted stage', () => {
      cy.get('[data-testid="stage-accepted"]').find('.stage-count').invoke('text').should('match', /\d+/)
    })

    it('should display numeric count in Rejected stage', () => {
      cy.get('[data-testid="stage-rejected"]').find('.stage-count').invoke('text').should('match', /\d+/)
    })

    it('should display numeric count in Litigated stage', () => {
      cy.get('[data-testid="stage-litigated"]').find('.stage-count').invoke('text').should('match', /\d+/)
    })

    it('should have Pending label text', () => {
      cy.get('[data-testid="stage-pending"]').should('contain', 'Pending')
    })

    it('should have Demand Sent label text', () => {
      cy.get('[data-testid="stage-demand-sent"]').should('contain', 'Demand Sent')
    })

    it('should have Negotiating label text', () => {
      cy.get('[data-testid="stage-negotiating"]').should('contain', 'Negotiating')
    })

    it('should have Accepted label text', () => {
      cy.get('[data-testid="stage-accepted"]').should('contain', 'Accepted')
    })

    it('should have Rejected label text', () => {
      cy.get('[data-testid="stage-rejected"]').should('contain', 'Rejected')
    })

    it('should have Litigated label text', () => {
      cy.get('[data-testid="stage-litigated"]').should('contain', 'Litigated')
    })
  })

  describe('Pipeline Stages - Interaction', () => {
    it('should add active class when clicking Pending stage', () => {
      cy.get('[data-testid="stage-pending"]').click()
      cy.get('[data-testid="stage-pending"]').should('have.class', 'active')
    })

    it('should add active class when clicking Demand Sent stage', () => {
      cy.get('[data-testid="stage-demand-sent"]').click()
      cy.get('[data-testid="stage-demand-sent"]').should('have.class', 'active')
    })

    it('should add active class when clicking Negotiating stage', () => {
      cy.get('[data-testid="stage-negotiating"]').click()
      cy.get('[data-testid="stage-negotiating"]').should('have.class', 'active')
    })

    it('should add active class when clicking Accepted stage', () => {
      cy.get('[data-testid="stage-accepted"]').click()
      cy.get('[data-testid="stage-accepted"]').should('have.class', 'active')
    })

    it('should add active class when clicking Rejected stage', () => {
      cy.get('[data-testid="stage-rejected"]').click()
      cy.get('[data-testid="stage-rejected"]').should('have.class', 'active')
    })

    it('should add active class when clicking Litigated stage', () => {
      cy.get('[data-testid="stage-litigated"]').click()
      cy.get('[data-testid="stage-litigated"]').should('have.class', 'active')
    })

    it('should update status filter when clicking pipeline stage', () => {
      cy.get('[data-testid="stage-pending"]').click()
      cy.get('[data-testid="filter-status"]').should('have.value', 'pending')
    })

    it('should remove active from other stages when clicking new stage', () => {
      cy.get('[data-testid="stage-pending"]').click()
      cy.get('[data-testid="stage-accepted"]').click()
      cy.get('[data-testid="stage-pending"]').should('not.have.class', 'active')
    })
  })

  describe('Filters Bar - Structure', () => {
    it('should display filters bar', () => {
      cy.get('[data-testid="filters-bar"]').should('be.visible')
    })

    it('should display status filter dropdown', () => {
      cy.get('[data-testid="filter-status"]').should('be.visible')
    })

    it('should display date from filter', () => {
      cy.get('[data-testid="filter-date-from"]').should('be.visible')
    })

    it('should display date to filter', () => {
      cy.get('[data-testid="filter-date-to"]').should('be.visible')
    })

    it('should display clear filters button', () => {
      cy.get('[data-testid="clear-filters-button"]').should('be.visible')
    })
  })

  describe('Status Filter - Options', () => {
    it('should have All Statuses option', () => {
      cy.get('[data-testid="filter-status"]').find('option').contains('All Statuses')
    })

    it('should have Pending option', () => {
      cy.get('[data-testid="filter-status"]').find('option[value="pending"]').should('exist')
    })

    it('should have Demand Sent option', () => {
      cy.get('[data-testid="filter-status"]').find('option[value="demand_sent"]').should('exist')
    })

    it('should have Negotiating option', () => {
      cy.get('[data-testid="filter-status"]').find('option[value="negotiating"]').should('exist')
    })

    it('should have Accepted option', () => {
      cy.get('[data-testid="filter-status"]').find('option[value="accepted"]').should('exist')
    })

    it('should have Rejected option', () => {
      cy.get('[data-testid="filter-status"]').find('option[value="rejected"]').should('exist')
    })

    it('should have Litigated option', () => {
      cy.get('[data-testid="filter-status"]').find('option[value="litigated"]').should('exist')
    })

    it('should have 7 options total', () => {
      cy.get('[data-testid="filter-status"]').find('option').should('have.length', 7)
    })
  })

  describe('Status Filter - Functionality', () => {
    it('should allow selecting Pending status', () => {
      cy.get('[data-testid="filter-status"]').select('pending')
      cy.get('[data-testid="filter-status"]').should('have.value', 'pending')
    })

    it('should allow selecting Demand Sent status', () => {
      cy.get('[data-testid="filter-status"]').select('demand_sent')
      cy.get('[data-testid="filter-status"]').should('have.value', 'demand_sent')
    })

    it('should allow selecting Negotiating status', () => {
      cy.get('[data-testid="filter-status"]').select('negotiating')
      cy.get('[data-testid="filter-status"]').should('have.value', 'negotiating')
    })

    it('should allow selecting Accepted status', () => {
      cy.get('[data-testid="filter-status"]').select('accepted')
      cy.get('[data-testid="filter-status"]').should('have.value', 'accepted')
    })

    it('should allow selecting Rejected status', () => {
      cy.get('[data-testid="filter-status"]').select('rejected')
      cy.get('[data-testid="filter-status"]').should('have.value', 'rejected')
    })

    it('should allow selecting Litigated status', () => {
      cy.get('[data-testid="filter-status"]').select('litigated')
      cy.get('[data-testid="filter-status"]').should('have.value', 'litigated')
    })

    it('should return to All Statuses', () => {
      cy.get('[data-testid="filter-status"]').select('pending')
      cy.get('[data-testid="filter-status"]').select('')
      cy.get('[data-testid="filter-status"]').should('have.value', '')
    })
  })

  describe('Date Filters - Functionality', () => {
    it('should allow setting date from', () => {
      cy.get('[data-testid="filter-date-from"]').type('2024-01-01')
      cy.get('[data-testid="filter-date-from"]').should('have.value', '2024-01-01')
    })

    it('should allow setting date to', () => {
      cy.get('[data-testid="filter-date-to"]').type('2024-12-31')
      cy.get('[data-testid="filter-date-to"]').should('have.value', '2024-12-31')
    })

    it('should allow setting date range', () => {
      cy.get('[data-testid="filter-date-from"]').type('2024-01-01')
      cy.get('[data-testid="filter-date-to"]').type('2024-12-31')
      cy.get('[data-testid="filter-date-from"]').should('have.value', '2024-01-01')
      cy.get('[data-testid="filter-date-to"]').should('have.value', '2024-12-31')
    })

    it('should clear date from', () => {
      cy.get('[data-testid="filter-date-from"]').type('2024-01-01')
      cy.get('[data-testid="filter-date-from"]').clear()
      cy.get('[data-testid="filter-date-from"]').should('have.value', '')
    })

    it('should clear date to', () => {
      cy.get('[data-testid="filter-date-to"]').type('2024-12-31')
      cy.get('[data-testid="filter-date-to"]').clear()
      cy.get('[data-testid="filter-date-to"]').should('have.value', '')
    })
  })

  describe('Clear Filters', () => {
    it('should clear status filter when clicking clear', () => {
      cy.get('[data-testid="filter-status"]').select('pending')
      cy.get('[data-testid="clear-filters-button"]').click()
      cy.get('[data-testid="filter-status"]').should('have.value', '')
    })

    it('should clear date from when clicking clear', () => {
      cy.get('[data-testid="filter-date-from"]').type('2024-01-01')
      cy.get('[data-testid="clear-filters-button"]').click()
      cy.get('[data-testid="filter-date-from"]').should('have.value', '')
    })

    it('should clear date to when clicking clear', () => {
      cy.get('[data-testid="filter-date-to"]').type('2024-12-31')
      cy.get('[data-testid="clear-filters-button"]').click()
      cy.get('[data-testid="filter-date-to"]').should('have.value', '')
    })

    it('should clear all filters at once', () => {
      cy.get('[data-testid="filter-status"]').select('pending')
      cy.get('[data-testid="filter-date-from"]').type('2024-01-01')
      cy.get('[data-testid="filter-date-to"]').type('2024-12-31')
      cy.get('[data-testid="clear-filters-button"]').click()
      cy.get('[data-testid="filter-status"]').should('have.value', '')
      cy.get('[data-testid="filter-date-from"]').should('have.value', '')
      cy.get('[data-testid="filter-date-to"]').should('have.value', '')
    })

    it('should remove active class from pipeline stages when clearing', () => {
      cy.get('[data-testid="stage-pending"]').click()
      cy.get('[data-testid="clear-filters-button"]').click()
      cy.get('[data-testid="stage-pending"]').should('not.have.class', 'active')
    })
  })

  describe('Settlements Table - Structure', () => {
    it('should display settlements table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid="settlements-table"]').should('be.visible')
        } else {
          cy.get('[data-testid="empty-state"]').should('be.visible')
        }
      })
    })

    it('should have Client column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid="settlements-table"] thead').should('contain', 'Client')
        }
      })
    })

    it('should have Target column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid="settlements-table"] thead').should('contain', 'Target')
        }
      })
    })

    it('should have Current Offer column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid="settlements-table"] thead').should('contain', 'Current Offer')
        }
      })
    })

    it('should have Status column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid="settlements-table"] thead').should('contain', 'Status')
        }
      })
    })

    it('should have Final Amount column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid="settlements-table"] thead').should('contain', 'Final Amount')
        }
      })
    })

    it('should have Contingency column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid="settlements-table"] thead').should('contain', 'Contingency')
        }
      })
    })

    it('should have Actions column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid="settlements-table"] thead').should('contain', 'Actions')
        }
      })
    })

    it('should display table body', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid="settlements-table-body"]').should('exist')
        }
      })
    })
  })

  describe('Settlement Table Rows', () => {
    it('should display settlement rows', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlements-table"]').length > 0) {
          cy.get('[data-testid^="settlement-row-"]').should('have.length.at.least', 1)
        }
      })
    })

    it('should display client name in each row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="settlement-row-"]').length > 0) {
          cy.get('[data-testid^="settlement-client-"]').first().should('exist')
        }
      })
    })

    it('should display target amount in each row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="settlement-row-"]').length > 0) {
          cy.get('[data-testid^="settlement-target-"]').first().should('exist')
        }
      })
    })

    it('should display status badge in each row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="settlement-row-"]').length > 0) {
          cy.get('[data-testid^="settlement-status-"]').first().should('exist')
        }
      })
    })

    it('should display target amount with dollar sign', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="settlement-target-"]').length > 0) {
          cy.get('[data-testid^="settlement-target-"]').first().invoke('text').should('contain', '$')
        }
      })
    })

    it('should display View button for each settlement', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="settlement-row-"]').length > 0) {
          cy.get('[data-testid^="view-settlement-"]').should('have.length.at.least', 1)
        }
      })
    })

    it('should have View button with correct text', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="view-settlement-"]').length > 0) {
          cy.get('[data-testid^="view-settlement-"]').first().should('contain', 'View')
        }
      })
    })
  })

  describe('Settlement Details Modal - Opening & Closing', () => {
    it('should open settlement modal when clicking View', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="view-settlement-"]').length > 0) {
          cy.get('[data-testid^="view-settlement-"]').first().click()
          cy.get('[data-testid="settlement-modal"]').should('have.class', 'active')
        }
      })
    })

    it('should close settlement modal when clicking X', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="view-settlement-"]').length > 0) {
          cy.get('[data-testid^="view-settlement-"]').first().click()
          cy.get('[data-testid="settlement-modal"]').should('have.class', 'active')
          cy.get('[data-testid="settlement-modal-close"]').click()
          cy.get('[data-testid="settlement-modal"]').should('not.have.class', 'active')
        }
      })
    })

    it('should close settlement modal when clicking Cancel', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="view-settlement-"]').length > 0) {
          cy.get('[data-testid^="view-settlement-"]').first().click()
          cy.get('[data-testid="settlement-modal"]').should('have.class', 'active')
          cy.get('[data-testid="settlement-modal-cancel"]').click()
          cy.get('[data-testid="settlement-modal"]').should('not.have.class', 'active')
        }
      })
    })
  })

  describe('Settlement Details Modal - Form Fields', () => {
    beforeEach(() => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="view-settlement-"]').length > 0) {
          cy.get('[data-testid^="view-settlement-"]').first().click()
          cy.get('[data-testid="settlement-modal"]').should('have.class', 'active')
        }
      })
    })

    it('should display client name field', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="modal-client-name"]').should('be.visible')
        }
      })
    })

    it('should have client name field as readonly', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="modal-client-name"]').should('have.attr', 'readonly')
        }
      })
    })

    it('should display status dropdown', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="modal-status"]').should('be.visible')
        }
      })
    })

    it('should display target amount field', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="modal-target-amount"]').should('be.visible')
        }
      })
    })

    it('should display minimum acceptable field', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="modal-minimum-acceptable"]').should('be.visible')
        }
      })
    })

    it('should display initial demand field', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="modal-initial-demand"]').should('be.visible')
        }
      })
    })

    it('should display final amount field', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="modal-final-amount"]').should('be.visible')
        }
      })
    })

    it('should display notes textarea', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="modal-notes"]').should('be.visible')
        }
      })
    })

    it('should display offers timeline', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="offers-timeline"]').should('be.visible')
        }
      })
    })

    it('should display save button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="settlement-modal"].active').length > 0) {
          cy.get('[data-testid="settlement-modal-save"]').should('be.visible')
        }
      })
    })
  })

  describe('Add Offer Modal', () => {
    it('should display offer modal when exists', () => {
      cy.get('[data-testid="offer-modal"]').should('exist')
    })

    it('should have offer amount input', () => {
      cy.get('[data-testid="offer-amount-input"]').should('exist')
    })

    it('should have offer notes input', () => {
      cy.get('[data-testid="offer-notes-input"]').should('exist')
    })

    it('should have offer modal close button', () => {
      cy.get('[data-testid="offer-modal-close"]').should('exist')
    })

    it('should have offer modal cancel button', () => {
      cy.get('[data-testid="offer-modal-cancel"]').should('exist')
    })

    it('should have offer modal submit button', () => {
      cy.get('[data-testid="offer-modal-submit"]').should('exist')
    })

    it('should open offer modal when clicking Add Offer button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="add-offer-"]').length > 0) {
          cy.get('[data-testid^="add-offer-"]').first().click()
          cy.get('[data-testid="offer-modal"]').should('have.class', 'active')
        }
      })
    })

    it('should close offer modal when clicking X', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="add-offer-"]').length > 0) {
          cy.get('[data-testid^="add-offer-"]').first().click()
          cy.get('[data-testid="offer-modal"]').should('have.class', 'active')
          cy.get('[data-testid="offer-modal-close"]').click()
          cy.get('[data-testid="offer-modal"]').should('not.have.class', 'active')
        }
      })
    })

    it('should close offer modal when clicking Cancel', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="add-offer-"]').length > 0) {
          cy.get('[data-testid^="add-offer-"]').first().click()
          cy.get('[data-testid="offer-modal"]').should('have.class', 'active')
          cy.get('[data-testid="offer-modal-cancel"]').click()
          cy.get('[data-testid="offer-modal"]').should('not.have.class', 'active')
        }
      })
    })

    it('should allow typing in offer amount', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="add-offer-"]').length > 0) {
          cy.get('[data-testid^="add-offer-"]').first().click()
          cy.get('[data-testid="offer-amount-input"]').type('5000')
          cy.get('[data-testid="offer-amount-input"]').should('have.value', '5000')
        }
      })
    })

    it('should allow typing in offer notes', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="add-offer-"]').length > 0) {
          cy.get('[data-testid^="add-offer-"]').first().click()
          cy.get('[data-testid="offer-notes-input"]').type('Test offer notes')
          cy.get('[data-testid="offer-notes-input"]').should('have.value', 'Test offer notes')
        }
      })
    })
  })

  describe('Settle Modal', () => {
    it('should display settle modal when exists', () => {
      cy.get('[data-testid="settle-modal"]').should('exist')
    })

    it('should have settle amount input', () => {
      cy.get('[data-testid="settle-amount-input"]').should('exist')
    })

    it('should have settle notes input', () => {
      cy.get('[data-testid="settle-notes-input"]').should('exist')
    })

    it('should have settle modal close button', () => {
      cy.get('[data-testid="settle-modal-close"]').should('exist')
    })

    it('should have settle modal cancel button', () => {
      cy.get('[data-testid="settle-modal-cancel"]').should('exist')
    })

    it('should have settle modal submit button', () => {
      cy.get('[data-testid="settle-modal-submit"]').should('exist')
    })
  })

  describe('Payment Modal', () => {
    it('should display payment modal when exists', () => {
      cy.get('[data-testid="payment-modal"]').should('exist')
    })

    it('should have payment amount input', () => {
      cy.get('[data-testid="payment-amount-input"]').should('exist')
    })

    it('should have payment notes input', () => {
      cy.get('[data-testid="payment-notes-input"]').should('exist')
    })

    it('should have payment modal close button', () => {
      cy.get('[data-testid="payment-modal-close"]').should('exist')
    })

    it('should have payment modal cancel button', () => {
      cy.get('[data-testid="payment-modal-cancel"]').should('exist')
    })

    it('should have payment modal submit button', () => {
      cy.get('[data-testid="payment-modal-submit"]').should('exist')
    })
  })

  describe('Empty State', () => {
    it('should display empty state when no settlements exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="empty-state"]').length > 0) {
          cy.get('[data-testid="empty-state"]').should('be.visible')
        }
      })
    })

    it('should have appropriate message in empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="empty-state"]').length > 0) {
          cy.get('[data-testid="empty-state"]').should('contain', 'No Settlements')
        }
      })
    })

    it('should hide table when empty state is shown', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="empty-state"]').length > 0) {
          cy.get('[data-testid="settlements-table"]').should('not.exist')
        }
      })
    })
  })

  describe('Combined Filtering', () => {
    it('should combine status and date filters', () => {
      cy.get('[data-testid="filter-status"]').select('pending')
      cy.get('[data-testid="filter-date-from"]').type('2024-01-01')
      cy.get('[data-testid="filter-status"]').should('have.value', 'pending')
      cy.get('[data-testid="filter-date-from"]').should('have.value', '2024-01-01')
    })

    it('should clear both filters at once', () => {
      cy.get('[data-testid="filter-status"]').select('pending')
      cy.get('[data-testid="filter-date-from"]').type('2024-01-01')
      cy.get('[data-testid="clear-filters-button"]').click()
      cy.get('[data-testid="filter-status"]').should('have.value', '')
      cy.get('[data-testid="filter-date-from"]').should('have.value', '')
    })
  })

  describe('Accessibility', () => {
    it('should have focusable status filter', () => {
      cy.get('[data-testid="filter-status"]').focus()
      cy.get('[data-testid="filter-status"]').should('be.focused')
    })

    it('should have focusable date from filter', () => {
      cy.get('[data-testid="filter-date-from"]').focus()
      cy.get('[data-testid="filter-date-from"]').should('be.focused')
    })

    it('should have focusable date to filter', () => {
      cy.get('[data-testid="filter-date-to"]').focus()
      cy.get('[data-testid="filter-date-to"]').should('be.focused')
    })

    it('should have clickable clear filters button', () => {
      cy.get('[data-testid="clear-filters-button"]').should('not.be.disabled')
    })

    it('should have clickable pipeline stages', () => {
      cy.get('[data-testid="stage-pending"]').click()
      cy.get('[data-testid="stage-pending"]').should('have.class', 'active')
    })
  })
})
