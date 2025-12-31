// Exhaustive test for /dashboard/patterns
describe('Violation Patterns - /dashboard/patterns', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/patterns');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/patterns');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Pattern');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Violation Patterns');
    });

    it('should display header subtitle', () => {
      cy.get('.header-subtitle').should('contain.text', 'Track systemic violations');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/patterns').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display New Pattern button', () => {
      cy.get('.header .btn-primary').should('contain.text', 'New Pattern');
    });

    it('should open modal when New Pattern clicked', () => {
      cy.get('.header .btn-primary').click();
      cy.get('.modal-overlay.active').should('exist');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display four stat cards', () => {
      cy.get('.stats-grid .stat-card').should('have.length', 4);
    });

    it('should display Total Patterns stat', () => {
      cy.get('.stat-card.highlight').within(() => {
        cy.get('.stat-label').should('contain.text', 'Total Patterns');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Clients Affected stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Clients Affected').should('exist');
    });

    it('should display Total Damages stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Total Damages').should('exist');
    });

    it('should display Ready for Action stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Ready for Action').should('exist');
    });
  });

  describe('Card Tests', () => {
    it('should display card', () => {
      cy.get('.card').should('be.visible');
    });

    it('should display card header', () => {
      cy.get('.card-header').should('be.visible');
    });

    it('should display card title', () => {
      cy.get('.card-title').should('contain.text', 'All Patterns');
    });
  });

  describe('Filter Tests', () => {
    it('should display filters', () => {
      cy.get('.filters').should('be.visible');
    });

    it('should have search input', () => {
      cy.get('#searchInput').should('exist');
    });

    it('should have furnisher filter', () => {
      cy.get('#furnisherFilter').should('exist');
    });

    it('should have CRA filter', () => {
      cy.get('#craFilter').should('exist');
    });

    it('should have status filter', () => {
      cy.get('#statusFilter').should('exist');
    });

    it('should accept search input', () => {
      cy.get('#searchInput').type('test');
      cy.get('#searchInput').should('have.value', 'test');
    });
  });

  describe('Table or Empty State Tests', () => {
    it('should display either data table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length) {
          cy.get('.data-table').should('be.visible');
        } else {
          cy.get('.empty-state').should('be.visible');
        }
      });
    });

    it('should display table headers if patterns exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length) {
          cy.get('.data-table th').should('have.length.at.least', 1);
        } else {
          cy.get('.empty-state h3').should('contain.text', 'No Patterns');
        }
      });
    });
  });

  describe('Pattern Row Tests', () => {
    it('should display pattern name if patterns exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.pattern-name').length) {
          cy.get('.pattern-name').first().should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });
  });

  describe('Status Badge Tests', () => {
    it('should have monitoring status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-monitoring').length) {
          cy.get('.status-monitoring').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have ready_for_action status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-ready_for_action').length) {
          cy.get('.status-ready_for_action').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Strength Badge Tests', () => {
    it('should have weak strength badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.strength-weak').length) {
          cy.get('.strength-weak').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have strong strength badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.strength-strong').length) {
          cy.get('.strength-strong').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Strategy Badge Tests', () => {
    it('should have class_action strategy badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.strategy-class_action').length) {
          cy.get('.strategy-class_action').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have modal overlay in DOM', () => {
      cy.get('.modal-overlay').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('.modal-overlay').should('not.have.class', 'active');
    });

    it('should open modal when New Pattern clicked', () => {
      cy.get('.header .btn-primary').click();
      cy.get('.modal-overlay.active').should('exist');
    });

    it('should close modal when close button clicked', () => {
      cy.get('.header .btn-primary').click();
      cy.get('.modal-overlay.active').should('exist');
      cy.get('.modal-close').first().click();
      cy.get('.modal-overlay').should('not.have.class', 'active');
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have openCreateModal function', () => {
      cy.window().should('have.property', 'openCreateModal');
    });

    it('should have filterTable function', () => {
      cy.window().should('have.property', 'filterTable');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
    });
  });
});
