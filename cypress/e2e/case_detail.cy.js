describe('Case Detail Page - Comprehensive Tests', () => {
  let caseId = null

  before(() => {
    // Login and find a valid case ID
    cy.visit('/staff/login')
    cy.get('[data-testid="email-input"]').type('test@example.com')
    cy.get('[data-testid="password-input"]').type('password123')
    cy.get('[data-testid="login-button"]').click()
    cy.url().should('include', '/dashboard')

    // Visit clients page and get first case ID
    cy.visit('/dashboard/clients')
    cy.get('body').then(($body) => {
      if ($body.find('[data-testid^="view-btn-"]').length > 0) {
        cy.get('[data-testid^="view-btn-"]').first().invoke('attr', 'data-testid').then((testid) => {
          caseId = testid.replace('view-btn-', '')
        })
      }
    })
  })

  beforeEach(() => {
    cy.visit('/staff/login')
    cy.get('[data-testid="email-input"]').type('test@example.com')
    cy.get('[data-testid="password-input"]').type('password123')
    cy.get('[data-testid="login-button"]').click()
    cy.url().should('include', '/dashboard')

    // Visit case detail if we have a valid case ID
      cy.visit(`/dashboard/case/${caseId}`)
      cy.visit(`/dashboard/case/${caseId}`)
    } else {
      // Fallback: go to clients and click first view button
      cy.visit('/dashboard/clients')
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="view-btn-"]').length > 0) {
          cy.get('[data-testid^="view-btn-"]').first().click()
        }
      })
    }
  })

  describe('Page Load & Structure', () => {
    it('should load the case detail page', () => {
      cy.get('[data-testid="case-detail-page"]').should('exist')
    })

    it('should display the page title with client name', () => {
      cy.get('[data-testid="page-title"]').should('exist')
    })

    it('should display back button', () => {
      cy.get('[data-testid="back-button"]').should('be.visible')
    })

    it('should have correct URL pattern', () => {
      cy.url().should('match', /\/dashboard\/case\/\d+/)
    })
  })

  describe('Navigation', () => {
    it('should navigate back when clicking back button', () => {
      cy.get('[data-testid="back-button"]').click()
      cy.url().should('include', '/dashboard/clients')
    })
  })

  describe('Case Score Section', () => {
    it('should display case score title', () => {
      cy.get('[data-testid="case-score-title"]').should('exist')
    })

    it('should display case score value or no score message', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="case-score-value"]').length > 0) {
          cy.get('[data-testid="case-score-value"]').should('be.visible')
        } else {
          cy.contains('No score available').should('exist')
        }
      })
    })

    it('should show score breakdown when score exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="case-score-value"]').length > 0) {
          cy.contains('Standing Score').should('exist')
          cy.contains('Violation Quality').should('exist')
          cy.contains('Willfulness').should('exist')
          cy.contains('Documentation').should('exist')
        }
      })
    })

    it('should apply correct color class based on score', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="case-score-value"]').length > 0) {
          cy.get('[data-testid="case-score-value"]').then(($el) => {
            const hasScoreClass = $el.hasClass('score-high') || 
                                  $el.hasClass('score-medium') || 
                                  $el.hasClass('score-low')
            expect(hasScoreClass).to.be.true
          })
        }
      })
    })
  })

  describe('Damages Exposure Section', () => {
    it('should display damages title', () => {
      cy.get('[data-testid="damages-title"]').should('exist')
    })

    it('should display total exposure or no damages message', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="total-exposure"]').length > 0) {
          cy.get('[data-testid="total-exposure"]').should('be.visible')
          cy.get('[data-testid="total-exposure"]').invoke('text').should('contain', '$')
        } else {
          cy.contains('No damages calculated').should('exist')
        }
      })
    })

    it('should show damages breakdown when available', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="total-exposure"]').length > 0) {
          cy.contains('Actual Damages').should('exist')
          cy.contains('Statutory Damages').should('exist')
          cy.contains('Punitive Damages').should('exist')
          cy.contains('Settlement Target').should('exist')
        }
      })
    })
  })

  describe('Standing Analysis Section', () => {
    it('should display standing title', () => {
      cy.get('[data-testid="standing-title"]').should('exist')
    })

    it('should show standing analysis elements', () => {
      cy.get('body').then(($body) => {
        if ($body.text().includes('Concrete Harm')) {
          cy.contains('Concrete Harm').should('exist')
          cy.contains('Dissemination').should('exist')
          cy.contains('Causation').should('exist')
        }
      })
    })
  })

  describe('Generated Letters Section', () => {
    it('should display letters title', () => {
      cy.get('[data-testid="letters-title"]').should('exist')
    })

    it('should show letters or empty message', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.letter-item').length > 0) {
          cy.get('.letter-item').should('have.length.at.least', 1)
        } else {
          cy.contains('No letters generated yet').should('exist')
        }
      })
    })

    it('should have download button for each letter', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.letter-item').length > 0) {
          cy.get('.letter-item').first().find('.download-btn').should('exist')
        }
      })
    })
  })

  describe('SOL Status Section', () => {
    it('should display SOL status section', () => {
      cy.get('[data-testid="sol-status-section"]').should('exist')
    })

    it('should display safe count', () => {
      cy.get('[data-testid="sol-safe-count"]').should('exist')
    })

    it('should display caution count', () => {
      cy.get('[data-testid="sol-caution-count"]').should('exist')
    })

    it('should display warning count', () => {
      cy.get('[data-testid="sol-warning-count"]').should('exist')
    })

    it('should display critical count', () => {
      cy.get('[data-testid="sol-critical-count"]').should('exist')
    })

    it('should have link to SOL dashboard', () => {
      cy.contains('View All SOL Deadlines').should('exist')
    })
  })

  describe('Settlement Section', () => {
    it('should display settlement section', () => {
      cy.get('[data-testid="settlement-section"]').should('exist')
    })

    it('should display settlement content', () => {
      cy.get('[data-testid="settlement-content"]').should('exist')
    })

    it('should load settlement data', () => {
      // Wait for async load
      cy.wait(2000)
      cy.get('[data-testid="settlement-content"]').should('not.contain', 'Loading settlement data...')
    })
  })

  describe('Escalation Section', () => {
    it('should display escalation section', () => {
      cy.get('[data-testid="escalation-section"]').should('exist')
    })

    it('should display escalation content', () => {
      cy.get('[data-testid="escalation-content"]').should('exist')
    })

    it('should have generate recommendations button', () => {
      cy.get('[data-testid="generate-recommendations-btn"]').should('exist')
    })

    it('should have link to escalation dashboard', () => {
      cy.contains('View All').should('exist')
    })
  })

  describe('Violations Section', () => {
    it('should display violations title', () => {
      cy.get('[data-testid="violations-title"]').should('exist')
    })

    it('should have calculate SOL button', () => {
      cy.get('[data-testid="calculate-sol-btn"]').should('exist')
    })

    it('should show violations or empty message', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.violation-item').length > 0) {
          cy.get('.violation-item').should('have.length.at.least', 1)
        } else {
          cy.contains('No violations found').should('exist')
        }
      })
    })

    it('should show violation details when violations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.violation-item').length > 0) {
          cy.get('.violation-item').first().within(() => {
            cy.get('.violation-bureau').should('exist')
            cy.get('.violation-section').should('exist')
          })
        }
      })
    })
  })

  describe('Dispute Timeline Section', () => {
    it('should display timeline title', () => {
      cy.get('[data-testid="timeline-title"]').should('exist')
    })

    it('should display timeline summary', () => {
      cy.get('[data-testid="timeline-summary"]').should('exist')
    })

    it('should display letters sent count', () => {
      cy.get('[data-testid="timeline-letters-sent"]').should('exist')
    })

    it('should display responses count', () => {
      cy.get('[data-testid="timeline-responses"]').should('exist')
    })

    it('should display deleted count', () => {
      cy.get('[data-testid="timeline-deleted"]').should('exist')
    })

    it('should display updated count', () => {
      cy.get('[data-testid="timeline-updated"]').should('exist')
    })

    it('should display overdue count', () => {
      cy.get('[data-testid="timeline-overdue"]').should('exist')
    })

    it('should display timeline container', () => {
      cy.get('[data-testid="timeline-container"]').should('exist')
    })

    it('should load timeline data', () => {
      cy.wait(2000)
      cy.get('[data-testid="timeline-container"]').should('not.contain', 'Loading timeline...')
    })
  })

  describe('SOL Calculator Modal', () => {
    it('should open SOL calculator when clicking button', () => {
      cy.get('[data-testid="calculate-sol-btn"]').click()
      cy.get('#solCalculatorModal').should('exist')
    })

    it('should have violation date input in modal', () => {
      cy.get('[data-testid="calculate-sol-btn"]').click()
      cy.get('#solViolationDate').should('exist')
    })

    it('should have discovery date input in modal', () => {
      cy.get('[data-testid="calculate-sol-btn"]').click()
      cy.get('#solDiscoveryDate').should('exist')
    })

    it('should close modal when clicking X', () => {
      cy.get('[data-testid="calculate-sol-btn"]').click()
      cy.get('#solCalculatorModal').should('exist')
      cy.get('#solCalculatorModal button').contains('×').click()
      cy.get('#solCalculatorModal').should('not.exist')
    })

    it('should allow entering violation date', () => {
      cy.get('[data-testid="calculate-sol-btn"]').click()
      cy.get('#solViolationDate').type('2023-01-15')
      cy.get('#solViolationDate').should('have.value', '2023-01-15')
    })

    it('should allow entering discovery date', () => {
      cy.get('[data-testid="calculate-sol-btn"]').click()
      cy.get('#solDiscoveryDate').type('2023-02-01')
      cy.get('#solDiscoveryDate').should('have.value', '2023-02-01')
    })
  })

  describe('Generate Recommendations', () => {
    it('should click generate recommendations button', () => {
      cy.get('[data-testid="generate-recommendations-btn"]').click()
      // Should show loading or generate recommendations
      cy.wait(1000)
      cy.get('[data-testid="escalation-content"]').should('exist')
    })
  })

  describe('Page Sections Visibility', () => {
    it('should have all main sections visible', () => {
      cy.get('[data-testid="case-score-title"]').scrollIntoView().should('be.visible')
      cy.get('[data-testid="damages-title"]').scrollIntoView().should('be.visible')
      cy.get('[data-testid="standing-title"]').scrollIntoView().should('be.visible')
      cy.get('[data-testid="letters-title"]').scrollIntoView().should('be.visible')
      cy.get('[data-testid="sol-status-section"]').scrollIntoView().should('be.visible')
      cy.get('[data-testid="settlement-section"]').scrollIntoView().should('be.visible')
      cy.get('[data-testid="escalation-section"]').scrollIntoView().should('be.visible')
      cy.get('[data-testid="violations-title"]').scrollIntoView().should('be.visible')
      cy.get('[data-testid="timeline-title"]').scrollIntoView().should('be.visible')
    })
  })

  describe('Responsive Layout', () => {
    it('should have grid layout', () => {
      cy.get('.grid').should('exist')
    })

    it('should have full-width sections', () => {
      cy.get('.full-width').should('have.length.at.least', 1)
    })
  })
})