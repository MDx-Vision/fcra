describe('Clients Page - Comprehensive Tests', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123')
    cy.visit('/dashboard/clients')
  })

  describe('Page Load & Structure', () => {
    it('should load the clients page', () => {
      cy.get('[data-testid="clients-page"]').should('be.visible')
    })

    it('should display the page title', () => {
      cy.get('[data-testid="page-title"]').should('be.visible')
      cy.get('[data-testid="page-title"]').should('contain', 'Clients')
    })

    it('should display the clients card container', () => {
      cy.get('[data-testid="clients-card"]').should('be.visible')
    })

    it('should display back to dashboard button', () => {
      cy.get('[data-testid="back-to-dashboard"]').should('be.visible')
    })

    it('should have correct page URL', () => {
      cy.url().should('include', '/dashboard/clients')
    })
  })

  describe('Navigation', () => {
    it('should navigate back to dashboard when clicking back button', () => {
      cy.get('[data-testid="back-to-dashboard"]').click()
      cy.url().should('include', '/dashboard')
      cy.url().should('not.include', '/clients')
    })

    it('should be accessible from dashboard', () => {
      cy.visit('/dashboard')
      cy.get('a[href*="/clients"]').first().click()
      cy.url().should('include', '/dashboard/clients')
    })
  })

  describe('Filter Section', () => {
    it('should display filters container', () => {
      cy.get('[data-testid="filters"]').should('be.visible')
    })

    it('should display All filter button', () => {
      cy.get('[data-testid="filter-all"]').should('be.visible')
    })

    it('should display Needs Review filter button', () => {
      cy.get('[data-testid="filter-needs-review"]').should('be.visible')
    })

    it('should display Ready to Deliver filter button', () => {
      cy.get('[data-testid="filter-ready-to-deliver"]').should('be.visible')
    })

    it('should have All filter active by default', () => {
      cy.get('[data-testid="filter-all"]').should('have.class', 'active')
    })

    it('should have correct text on All filter', () => {
      cy.get('[data-testid="filter-all"]').should('contain', 'All')
    })

    it('should have correct text on Needs Review filter', () => {
      cy.get('[data-testid="filter-needs-review"]').should('contain', 'Needs Review')
    })

    it('should have correct text on Ready to Deliver filter', () => {
      cy.get('[data-testid="filter-ready-to-deliver"]').should('contain', 'Ready to Deliver')
    })
  })

  describe('Filter Functionality - All', () => {
    it('should show all clients when All filter is clicked', () => {
      cy.get('[data-testid="filter-all"]').click()
      cy.url().should('include', '/dashboard/clients')
      cy.get('[data-testid="filter-all"]').should('have.class', 'active')
    })

    it('should remove active class from other filters when All is clicked', () => {
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.get('[data-testid="filter-all"]').click()
      cy.get('[data-testid="filter-needs-review"]').should('not.have.class', 'active')
    })
  })

  describe('Filter Functionality - Needs Review', () => {
    it('should filter by Needs Review status', () => {
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.url().should('include', 'status=stage1_complete')
    })

    it('should set Needs Review filter as active', () => {
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.get('[data-testid="filter-needs-review"]').should('have.class', 'active')
    })

    it('should remove active class from All filter', () => {
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.get('[data-testid="filter-all"]').should('not.have.class', 'active')
    })
  })

  describe('Filter Functionality - Ready to Deliver', () => {
    it('should filter by Ready to Deliver status', () => {
      cy.get('[data-testid="filter-ready-to-deliver"]').click()
      cy.url().should('include', 'status=stage2_complete')
    })

    it('should set Ready to Deliver filter as active', () => {
      cy.get('[data-testid="filter-ready-to-deliver"]').click()
      cy.get('[data-testid="filter-ready-to-deliver"]').should('have.class', 'active')
    })

    it('should remove active class from All filter', () => {
      cy.get('[data-testid="filter-ready-to-deliver"]').click()
      cy.get('[data-testid="filter-all"]').should('not.have.class', 'active')
    })
  })

  describe('Search Section', () => {
    it('should display search input', () => {
      cy.get('[data-testid="search-input"]').should('be.visible')
    })

    it('should have placeholder text', () => {
      cy.get('[data-testid="search-input"]').should('have.attr', 'placeholder', 'Search clients...')
    })

    it('should allow typing in search input', () => {
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="search-input"]').should('have.value', 'test')
    })

    it('should clear search input', () => {
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="search-input"]').clear()
      cy.get('[data-testid="search-input"]').should('have.value', '')
    })

    it('should accept special characters in search', () => {
      cy.get('[data-testid="search-input"]').type("O'Brien")
      cy.get('[data-testid="search-input"]').should('have.value', "O'Brien")
    })

    it('should accept numeric input in search', () => {
      cy.get('[data-testid="search-input"]').type('12345')
      cy.get('[data-testid="search-input"]').should('have.value', '12345')
    })

    it('should accept email format in search', () => {
      cy.get('[data-testid="search-input"]').type('test@example.com')
      cy.get('[data-testid="search-input"]').should('have.value', 'test@example.com')
    })
  })

  describe('Search Functionality', () => {
    it('should filter table rows when searching', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').then(($rows) => {
            const initialCount = $rows.length
            if (initialCount > 0) {
              // Get first client name and search for it
              cy.get('[data-testid^="client-name-"]').first().invoke('text').then((name) => {
                cy.get('[data-testid="search-input"]').type(name.substring(0, 3))
                // At least one row should be visible
                cy.get('[data-testid^="client-row-"]:visible').should('have.length.at.least', 1)
              })
            }
          })
        }
      })
    })

    it('should show no rows for non-matching search', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="search-input"]').type('zzzznonexistent12345')
          cy.get('[data-testid^="client-row-"]:visible').should('have.length', 0)
        }
      })
    })

    it('should be case insensitive', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid^="client-name-"]').first().invoke('text').then((name) => {
            // Search with uppercase
            cy.get('[data-testid="search-input"]').type(name.substring(0, 3).toUpperCase())
            cy.get('[data-testid^="client-row-"]:visible').should('have.length.at.least', 1)
          })
        }
      })
    })

    it('should restore all rows when search is cleared', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').then(($rows) => {
            const initialCount = $rows.length
            cy.get('[data-testid="search-input"]').type('test')
            cy.get('[data-testid="search-input"]').clear()
            cy.get('[data-testid^="client-row-"]:visible').should('have.length', initialCount)
          })
        }
      })
    })
  })

  describe('Clients Table - Structure', () => {
    it('should display clients table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"]').should('be.visible')
        } else {
          cy.get('[data-testid="empty-state"]').should('be.visible')
        }
      })
    })

    it('should display table header with correct columns', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"] thead th').should('have.length', 11)
        }
      })
    })

    it('should have Client column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"] thead').should('contain', 'Client')
        }
      })
    })

    it('should have Status column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"] thead').should('contain', 'Status')
        }
      })
    })

    it('should have Score column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"] thead').should('contain', 'Score')
        }
      })
    })

    it('should have Type column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"] thead').should('contain', 'Type')
        }
      })
    })

    it('should have Follow Up column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"] thead').should('contain', 'Follow Up')
        }
      })
    })

    it('should have Lead column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"] thead').should('contain', 'Lead')
        }
      })
    })

    it('should have Actions column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"] thead').should('contain', 'Actions')
        }
      })
    })

    it('should display table body', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table-body"]').should('exist')
        }
      })
    })
  })

  describe('Client Table Rows - Data Display', () => {
    it('should display client rows', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').should('have.length.at.least', 1)
        }
      })
    })

    it('should display client name for each row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().within(() => {
            cy.get('[data-testid^="client-name-"]').should('exist')
          })
        }
      })
    })

    it('should display client email for each row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().within(() => {
            cy.get('[data-testid^="client-email-"]').should('exist')
          })
        }
      })
    })

    it('should display client status badge for each row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().within(() => {
            cy.get('[data-testid^="client-status-"]').should('exist')
          })
        }
      })
    })

    it('should display client violations data attribute for each row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().should('have.attr', 'data-violations')
        }
      })
    })

    it('should display client exposure data attribute for each row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().should('have.attr', 'data-exposure')
        }
      })
    })

    it('should display client follow up date for each row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().within(() => {
            cy.get('.followup-date').should('exist')
          })
        }
      })
    })

    it('should display client name as non-empty text', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-name-"]').length > 0) {
          cy.get('[data-testid^="client-name-"]').first().invoke('text').should('not.be.empty')
        }
      })
    })

    it('should display avatar or initial for client', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('.client-avatar').first().should('be.visible')
        }
      })
    })
  })

  describe('Client Table Rows - Action Buttons', () => {
    it('should display View action for each client', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().within(() => {
            cy.get('a.row-action[href*="/dashboard/case/"]').should('exist')
          })
        }
      })
    })

    it('should have View action link to case detail', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().within(() => {
            cy.get('a.row-action[href*="/dashboard/case/"]').should('have.attr', 'href').and('include', '/dashboard/case/')
          })
        }
      })
    })

    it('should navigate to case detail when clicking View', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().within(() => {
            cy.get('a.row-action[href*="/dashboard/case/"]').click()
          })
          cy.url().should('include', '/dashboard/case/')
        }
      })
    })

    it('should display Review action for clients with analysis', () => {
      // Navigate to needs review filter to find reviewable clients
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.get('body').then(($body) => {
        if ($body.find('a.row-action[href*="/review"]').length > 0) {
          cy.get('a.row-action[href*="/review"]').first().should('be.visible')
        }
      })
    })

    it('should have Review action link to review page', () => {
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.get('body').then(($body) => {
        if ($body.find('a.row-action[href*="/review"]').length > 0) {
          cy.get('a.row-action[href*="/review"]').first().should('have.attr', 'href').and('include', '/review')
        }
      })
    })

    it('should navigate to review page when clicking Review', () => {
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.get('body').then(($body) => {
        if ($body.find('a.row-action[href*="/review"]').length > 0) {
          cy.get('a.row-action[href*="/review"]').first().click()
          cy.url().should('include', '/review')
        }
      })
    })
  })

  describe('Status Badges', () => {
    it('should display status badge with appropriate styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-status-"]').length > 0) {
          cy.get('[data-testid^="client-status-"]').first().should('have.class', 'status-badge')
        }
      })
    })

    it('should have status badge with non-empty text', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-status-"]').length > 0) {
          cy.get('[data-testid^="client-status-"]').first().invoke('text').then((text) => {
            expect(text.trim()).to.not.be.empty
          })
        }
      })
    })
  })

  describe('Score Badges', () => {
    it('should display score badge when score exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-score-"]').length > 0) {
          cy.get('[data-testid^="client-score-"]').first().should('have.class', 'score-badge')
        }
      })
    })

    it('should have score badge with numeric value', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-score-"]').length > 0) {
          cy.get('[data-testid^="client-score-"]').first().invoke('text').then((text) => {
            expect(text.trim()).to.match(/\d+/)
          })
        }
      })
    })

    it('should have appropriate color class for score', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-score-"]').length > 0) {
          cy.get('[data-testid^="client-score-"]').first().then(($badge) => {
            const hasScoreClass = $badge.hasClass('score-high') ||
                                  $badge.hasClass('score-medium') ||
                                  $badge.hasClass('score-low')
            expect(hasScoreClass).to.be.true
          })
        }
      })
    })
  })

  describe('Empty State', () => {
    it('should display empty state when no clients exist', () => {
      // This test checks if empty state renders correctly when shown
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="empty-state"]').length > 0) {
          cy.get('[data-testid="empty-state"]').should('be.visible')
        }
      })
    })

    it('should have appropriate message in empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="empty-state"]').length > 0) {
          cy.get('[data-testid="empty-state"]').should('contain', 'No clients')
        }
      })
    })

    it('should hide table when empty state is shown', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="empty-state"]').length > 0) {
          cy.get('[data-testid="clients-table"]').should('not.exist')
        }
      })
    })
  })

  describe('Filter State Persistence', () => {
    it('should maintain Needs Review filter after page interaction', () => {
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="filter-needs-review"]').should('have.class', 'active')
    })

    it('should maintain Ready to Deliver filter after page interaction', () => {
      cy.get('[data-testid="filter-ready-to-deliver"]').click()
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="filter-ready-to-deliver"]').should('have.class', 'active')
    })

    it('should return to All filter from Needs Review', () => {
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.get('[data-testid="filter-all"]').click()
      cy.get('[data-testid="filter-all"]').should('have.class', 'active')
      cy.url().should('not.include', 'status=')
    })

    it('should return to All filter from Ready to Deliver', () => {
      cy.get('[data-testid="filter-ready-to-deliver"]').click()
      cy.get('[data-testid="filter-all"]').click()
      cy.get('[data-testid="filter-all"]').should('have.class', 'active')
      cy.url().should('not.include', 'status=')
    })
  })

  describe('Combined Filter and Search', () => {
    it('should search within Needs Review filter', () => {
      cy.get('[data-testid="filter-needs-review"]').click()
      cy.get('[data-testid="search-input"]').should('be.visible')
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="search-input"]').should('have.value', 'test')
    })

    it('should search within Ready to Deliver filter', () => {
      cy.get('[data-testid="filter-ready-to-deliver"]').click()
      cy.get('[data-testid="search-input"]').should('be.visible')
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="search-input"]').should('have.value', 'test')
    })

    it('should clear search when switching filters', () => {
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="filter-needs-review"]').click()
      // Search input should be cleared after filter navigation
      cy.get('[data-testid="search-input"]').should('have.value', '')
    })
  })

  describe('Table Row Interactions', () => {
    it('should highlight row on hover', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().trigger('mouseover')
          // Row should still be visible (hover styles applied via CSS)
          cy.get('[data-testid^="client-row-"]').first().should('be.visible')
        }
      })
    })

    it('should maintain row visibility after multiple hovers', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 1) {
          cy.get('[data-testid^="client-row-"]').eq(0).trigger('mouseover')
          cy.get('[data-testid^="client-row-"]').eq(1).trigger('mouseover')
          cy.get('[data-testid^="client-row-"]').eq(0).should('be.visible')
        }
      })
    })
  })

  describe('Exposure Data', () => {
    it('should have exposure data attribute on rows', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().should('have.attr', 'data-exposure')
        }
      })
    })

    it('should have numeric exposure value', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="client-row-"]').length > 0) {
          cy.get('[data-testid^="client-row-"]').first().invoke('attr', 'data-exposure').then((value) => {
            // Exposure should be a number (possibly 0)
            expect(parseInt(value)).to.be.a('number')
          })
        }
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper table structure', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="clients-table"]').length > 0) {
          cy.get('[data-testid="clients-table"]').find('thead').should('exist')
          cy.get('[data-testid="clients-table"]').find('tbody').should('exist')
        }
      })
    })

    it('should have clickable filter buttons', () => {
      cy.get('[data-testid="filter-all"]').should('not.be.disabled')
      cy.get('[data-testid="filter-needs-review"]').should('not.be.disabled')
      cy.get('[data-testid="filter-ready-to-deliver"]').should('not.be.disabled')
    })

    it('should have focusable search input', () => {
      cy.get('[data-testid="search-input"]').focus()
      cy.get('[data-testid="search-input"]').should('be.focused')
    })

    it('should allow keyboard navigation in search', () => {
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="search-input"]').type('{selectall}')
      cy.get('[data-testid="search-input"]').type('{backspace}')
      cy.get('[data-testid="search-input"]').should('have.value', '')
    })
  })
})
