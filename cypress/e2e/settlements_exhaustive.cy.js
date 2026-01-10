// Exhaustive test for /dashboard/settlements
describe('Settlement Tracking Page - /dashboard/settlements', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/settlements');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/settlements');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Settlement');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/settlements').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Settlement Tracking');
    });

    it('should display header subtitle', () => {
      cy.get('.header-subtitle').should('be.visible');
    });

    it('should display Back to Dashboard button', () => {
      cy.get('.btn-secondary').contains('Back to Dashboard').should('be.visible');
    });

    it('should have working back button link', () => {
      cy.get('.btn-secondary').contains('Back to Dashboard').should('have.attr', 'href', '/dashboard');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display stat cards', () => {
      cy.get('.stat-card').should('have.length', 4);
    });

    it('should display Total Settled stat', () => {
      cy.get('.stat-label').contains('Total Settled').should('exist');
    });

    it('should display Pipeline Value stat', () => {
      cy.get('.stat-label').contains('Pipeline Value').should('exist');
    });

    it('should display Avg Settlement stat', () => {
      cy.get('.stat-label').contains('Avg Settlement').should('exist');
    });

    it('should display Contingency Earned stat', () => {
      cy.get('.stat-label').contains('Contingency Earned').should('exist');
    });

    it('should display stat values', () => {
      cy.get('.stat-value').should('have.length.at.least', 4);
    });

    it('should have success highlight card', () => {
      cy.get('.stat-card.success').should('exist');
    });

    it('should have highlight card', () => {
      cy.get('.stat-card.highlight').should('exist');
    });
  });

  describe('Pipeline Section Tests', () => {
    it('should display pipeline section', () => {
      cy.get('.pipeline-section').should('be.visible');
    });

    it('should display Settlement Pipeline title', () => {
      cy.get('.section-title').contains('Settlement Pipeline').should('exist');
    });

    it('should display pipeline stages', () => {
      cy.get('.pipeline-stages').should('be.visible');
    });

    it('should have 6 pipeline stages', () => {
      cy.get('.pipeline-stage').should('have.length', 6);
    });

    it('should have Pending stage', () => {
      cy.get('.pipeline-stage.pending').should('exist');
      cy.get('.pipeline-stage.pending .stage-label').should('contain.text', 'Pending');
    });

    it('should have Demand Sent stage', () => {
      cy.get('.pipeline-stage.demand_sent').should('exist');
      cy.get('.pipeline-stage.demand_sent .stage-label').should('contain.text', 'Demand Sent');
    });

    it('should have Negotiating stage', () => {
      cy.get('.pipeline-stage.negotiating').should('exist');
      cy.get('.pipeline-stage.negotiating .stage-label').should('contain.text', 'Negotiating');
    });

    it('should have Accepted stage', () => {
      cy.get('.pipeline-stage.accepted').should('exist');
      cy.get('.pipeline-stage.accepted .stage-label').should('contain.text', 'Accepted');
    });

    it('should have Rejected stage', () => {
      cy.get('.pipeline-stage.rejected').should('exist');
      cy.get('.pipeline-stage.rejected .stage-label').should('contain.text', 'Rejected');
    });

    it('should have Litigated stage', () => {
      cy.get('.pipeline-stage.litigated').should('exist');
      cy.get('.pipeline-stage.litigated .stage-label').should('contain.text', 'Litigated');
    });

    it('should display stage counts', () => {
      cy.get('.stage-count').should('have.length', 6);
    });

    it('should have clickable pipeline stages', () => {
      cy.get('.pipeline-stage').first().should('not.be.disabled');
    });
  });

  describe('Filters Tests', () => {
    it('should display filters bar', () => {
      cy.get('.filters-bar').should('be.visible');
    });

    it('should have status filter dropdown', () => {
      cy.get('#filterStatus').should('exist');
    });

    it('should have status filter options', () => {
      cy.get('#filterStatus option').should('have.length.at.least', 7);
    });

    it('should have date from filter', () => {
      cy.get('#filterDateFrom').should('exist');
    });

    it('should have date to filter', () => {
      cy.get('#filterDateTo').should('exist');
    });

    it('should have Clear Filters button', () => {
      cy.get('.btn-secondary').contains('Clear Filters').should('be.visible');
    });

    it('should accept input in date filters', () => {
      cy.get('#filterDateFrom').type('2025-01-01').should('have.value', '2025-01-01');
    });
  });

  describe('Settlements Section Tests', () => {
    it('should display settlements section', () => {
      cy.get('.pipeline-section').contains('All Settlements').should('exist');
    });

    it('should display table or empty state', () => {
      cy.get('.pipeline-section').then(($section) => {
        const hasTable = $section.find('.settlement-table').length > 0;
        const hasEmptyState = $section.find('.empty-state').length > 0;
        expect(hasTable || hasEmptyState).to.be.true;
      });
    });

    it('should display table headers if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.settlement-table').length) {
          cy.get('.settlement-table th').should('have.length.at.least', 1);
        }
      });
    });

    it('should have Client column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.settlement-table').length) {
          cy.get('.settlement-table th').contains('Client').should('exist');
        }
      });
    });

    it('should have Target column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.settlement-table').length) {
          cy.get('.settlement-table th').contains('Target').should('exist');
        }
      });
    });

    it('should have Status column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.settlement-table').length) {
          cy.get('.settlement-table th').contains('Status').should('exist');
        }
      });
    });
  });

  describe('Badge Tests', () => {
    it('should display status badges if settlements exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.settlement-table tbody tr').length > 0) {
          cy.get('.status-badge').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Action Button Tests', () => {
    it('should display action buttons if settlements exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.settlement-table tbody tr').length > 0) {
          cy.get('.action-btn').should('have.length.at.least', 1);
        }
      });
    });

    it('should have View button if settlements exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.settlement-table tbody tr').length > 0) {
          cy.get('.action-btn').contains('View').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have settlement modal element', () => {
      cy.get('#settlementModal').should('exist');
    });

    it('should have offer modal element', () => {
      cy.get('#offerModal').should('exist');
    });

    it('should have settle modal element', () => {
      cy.get('#settleModal').should('exist');
    });

    it('should have payment modal element', () => {
      cy.get('#paymentModal').should('exist');
    });

    it('should have modals hidden by default', () => {
      cy.get('.modal-overlay.active').should('not.exist');
    });

    it('should have modal close buttons', () => {
      cy.get('.modal-close').should('have.length.at.least', 1);
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.pipeline-section').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.pipeline-section').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.header h1').should('be.visible');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have clickable back button', () => {
      cy.get('.btn-secondary').contains('Back to Dashboard').should('not.be.disabled');
    });

    it('should have primary button styling', () => {
      cy.get('.btn-primary').should('exist');
    });

    it('should have secondary button styling', () => {
      cy.get('.btn-secondary').should('exist');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
      cy.get('h2').should('have.length.at.least', 1);
    });

    it('should have filter labels', () => {
      cy.get('.filter-group label').should('have.length.at.least', 1);
    });

    it('should have table headers for accessibility', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.settlement-table').length) {
          cy.get('.settlement-table th').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Empty State Tests', () => {
    it('should display empty state when no settlements', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length > 0) {
          cy.get('.empty-state').should('be.visible');
          cy.get('.empty-state h3').should('contain.text', 'No Settlements Yet');
        }
      });
    });
  });
});
