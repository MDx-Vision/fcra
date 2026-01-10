// Exhaustive test for /dashboard/documents
describe('Document Center Page - /dashboard/documents', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/documents');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/documents');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Document Center');
      cy.title().should('contain', 'Brightpath Ascend FCRA Platform');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/documents').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Document Center');
    });

    it('should display header buttons', () => {
      cy.get('.header .btn').should('exist');
    });
  });

  describe('Stats Row Tests', () => {
    it('should display stats row', () => {
      cy.get('.stats-row').should('be.visible');
    });

    it('should display stat cards', () => {
      cy.get('.stat-card').should('have.length.at.least', 1);
    });

    it('should display stat values', () => {
      cy.get('.stat-value').should('have.length.at.least', 1);
    });

    it('should display stat labels', () => {
      cy.get('.stat-label').should('have.length.at.least', 1);
    });

    it('should have urgent stat card styling', () => {
      cy.get('.stat-card.urgent').should('exist');
    });

    it('should have action stat card styling', () => {
      cy.get('.stat-card.action').should('exist');
    });
  });

  describe('Content Card Tests', () => {
    it('should display main content card', () => {
      cy.get('.content-card').should('be.visible');
    });
  });

  describe('Filter Tests', () => {
    it('should display filters section', () => {
      cy.get('.filters').should('exist');
    });

    it('should display filter buttons', () => {
      cy.get('.filter-btn').should('have.length.at.least', 1);
    });

    it('should have Pending Review filter', () => {
      cy.get('.filter-btn').contains('Pending Review').should('exist');
    });

    it('should have Reviewed filter', () => {
      cy.get('.filter-btn').contains('Reviewed').should('exist');
    });

    it('should have Urgent filter', () => {
      cy.get('.filter-btn').contains('Urgent').should('exist');
    });

    it('should have Needs Action filter', () => {
      cy.get('.filter-btn').contains('Needs Action').should('exist');
    });

    it('should have clickable filter buttons', () => {
      cy.get('.filter-btn').first().should('not.be.disabled');
    });
  });

  describe('Table Tests', () => {
    it('should display table or empty state', () => {
      cy.get('.content-card').then(($card) => {
        const hasTable = $card.find('table').length > 0;
        const hasEmptyState = $card.find('.empty-state').length > 0;
        expect(hasTable || hasEmptyState).to.be.true;
      });
    });

    it('should display table headers if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have upload modal element', () => {
      cy.get('.upload-modal').should('exist');
    });

    it('should have modal hidden by default', () => {
      cy.get('.upload-modal.active').should('not.exist');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
      cy.get('.stats-row').should('be.visible');
      cy.get('.content-card').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.content-card').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.header h1').should('be.visible');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have clickable header buttons', () => {
      cy.get('.header .btn').first().should('not.be.disabled');
    });

    it('should have primary button style', () => {
      cy.get('.btn-primary').should('exist');
    });
  });

  describe('Category Badge Tests', () => {
    it('should display category badges if documents exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table tbody tr').length > 0) {
          cy.get('.category-badge').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
    });

    it('should have table headers for accessibility', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Empty State Tests', () => {
    it('should display empty state when no documents', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length > 0) {
          cy.get('.empty-state').should('be.visible');
        }
      });
    });
  });
});
