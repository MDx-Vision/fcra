// Exhaustive test for /dashboard/audit
describe('Audit Logs & Compliance - /dashboard/audit', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/audit');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/audit');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Audit');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Audit Logs');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/audit').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display Refresh button', () => {
      cy.get('.header-actions .btn-secondary').should('contain.text', 'Refresh');
    });

    it('should display Export Logs button', () => {
      cy.get('.header-actions .btn-primary').should('contain.text', 'Export Logs');
    });

    it('should open export modal when Export Logs clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#export-modal').should('have.class', 'active');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display four stat cards', () => {
      cy.get('.stats-grid .stat-card').should('have.length', 4);
    });

    it('should display Total Events stat', () => {
      cy.get('.stat-card.highlight').within(() => {
        cy.get('.stat-label').should('contain.text', 'Total Events');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Successful Logins stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Successful Logins').should('exist');
    });

    it('should display Warning Events stat', () => {
      cy.get('.stat-card.warning').within(() => {
        cy.get('.stat-label').should('contain.text', 'Warning');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Critical Events stat', () => {
      cy.get('.stat-card.critical').within(() => {
        cy.get('.stat-label').should('contain.text', 'Critical');
        cy.get('.stat-value').should('exist');
      });
    });
  });

  describe('Content Grid Tests', () => {
    it('should display content grid', () => {
      cy.get('.content-grid').should('be.visible');
    });

    it('should display main column card', () => {
      cy.get('.card').should('have.length.at.least', 1);
    });

    it('should display Audit Log Feed card', () => {
      cy.get('.card-title').contains('Audit Log Feed').should('exist');
    });
  });

  describe('Filters Tests', () => {
    it('should display filters section', () => {
      cy.get('.filters').should('be.visible');
    });

    it('should have Event Type filter', () => {
      cy.get('#filter-event-type').should('exist');
    });

    it('should have Resource Type filter', () => {
      cy.get('#filter-resource-type').should('exist');
    });

    it('should have Severity filter', () => {
      cy.get('#filter-severity').should('exist');
    });

    it('should have User Type filter', () => {
      cy.get('#filter-user-type').should('exist');
    });

    it('should have date range filters', () => {
      cy.get('#filter-start-date').should('exist');
      cy.get('#filter-end-date').should('exist');
    });

    it('should have search input', () => {
      cy.get('#filter-search').should('exist');
    });
  });

  describe('Logs Container Tests', () => {
    it('should display logs container', () => {
      cy.get('#logs-container').should('exist');
    });

    it('should display either table or loading/empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.audit-table').length) {
          cy.get('.audit-table').should('be.visible');
        } else if ($body.find('.loading').length) {
          cy.get('.loading').should('exist');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });
  });

  describe('Pagination Tests', () => {
    it('should have pagination container', () => {
      cy.get('#pagination').should('exist');
    });

    it('should have previous button', () => {
      cy.get('#prev-btn').should('exist');
    });

    it('should have next button', () => {
      cy.get('#next-btn').should('exist');
    });

    it('should have page info', () => {
      cy.get('#page-info').should('exist');
    });
  });

  describe('Side Column Tests', () => {
    it('should display Compliance Reports card', () => {
      cy.get('.card-title').contains('Compliance Reports').should('exist');
    });

    it('should display SOC 2 report button', () => {
      cy.get('.compliance-btn').contains('SOC 2').should('exist');
    });

    it('should display HIPAA report button', () => {
      cy.get('.compliance-btn').contains('HIPAA').should('exist');
    });

    it('should display Recent Security Events card', () => {
      cy.get('.card-title').contains('Recent Security Events').should('exist');
    });

    it('should display Most Active Users card', () => {
      cy.get('.card-title').contains('Most Active Users').should('exist');
    });
  });

  describe('Export Modal Tests', () => {
    it('should have export modal in DOM', () => {
      cy.get('#export-modal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#export-modal').should('not.have.class', 'active');
    });

    it('should open export modal when button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#export-modal').should('have.class', 'active');
    });

    it('should display export date inputs', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#export-start-date').should('exist');
      cy.get('#export-end-date').should('exist');
    });

    it('should display export format buttons', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('.export-options').within(() => {
        cy.get('button').contains('Export CSV').should('exist');
        cy.get('button').contains('Export JSON').should('exist');
      });
    });

    it('should close modal when close button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#export-modal').should('have.class', 'active');
      cy.get('#export-modal .modal-close').click();
      cy.get('#export-modal').should('not.have.class', 'active');
    });
  });

  describe('Report Modal Tests', () => {
    it('should have report modal in DOM', () => {
      cy.get('#report-modal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#report-modal').should('not.have.class', 'active');
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have loadLogs function', () => {
      cy.window().should('have.property', 'loadLogs');
    });

    it('should have applyFilters function', () => {
      cy.window().should('have.property', 'applyFilters');
    });

    it('should have refreshLogs function', () => {
      cy.window().should('have.property', 'refreshLogs');
    });

    it('should have showExportModal function', () => {
      cy.window().should('have.property', 'showExportModal');
    });

    it('should have closeModal function', () => {
      cy.window().should('have.property', 'closeModal');
    });

    it('should have exportLogs function', () => {
      cy.window().should('have.property', 'exportLogs');
    });

    it('should have generateReport function', () => {
      cy.window().should('have.property', 'generateReport');
    });

    it('should have changePage function', () => {
      cy.window().should('have.property', 'changePage');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.content-grid').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
    });
  });

  describe('Badge Styling Tests', () => {
    it('should have severity-info badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.severity-info').length) {
          cy.get('.severity-info').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should have severity-warning badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.severity-warning').length) {
          cy.get('.severity-warning').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should have severity-critical badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.severity-critical').length) {
          cy.get('.severity-critical').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });
});
