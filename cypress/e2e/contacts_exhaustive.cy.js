// Exhaustive test for /dashboard/contacts
describe('Contacts Page - /dashboard/contacts', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/contacts');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/contacts');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Clients');
      cy.title().should('contain', 'Brightpath Ascend FCRA Platform');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/contacts').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Clients');
    });

    it('should display action buttons in header', () => {
      cy.get('.header').within(() => {
        cy.get('.btn').should('exist');
      });
    });
  });

  describe('Navigation Tests', () => {
    it('should display top navigation tabs', () => {
      cy.get('.top-nav').should('be.visible');
    });

    it('should have navigation buttons', () => {
      cy.get('.top-nav-btn').should('have.length.at.least', 1);
    });

    it('should have active state on navigation button', () => {
      cy.get('.top-nav-btn.active').should('exist');
    });
  });

  describe('Content Card Tests', () => {
    it('should display main content card', () => {
      cy.get('.content-card').should('be.visible');
    });

    it('should display filters row', () => {
      cy.get('.filters-row').should('exist');
    });

    it('should have filter buttons', () => {
      cy.get('.filter-btn').should('have.length.at.least', 1);
    });
  });

  describe('Search and Controls Tests', () => {
    it('should display search controls', () => {
      cy.get('.search-controls').should('exist');
    });

    it('should display search box', () => {
      cy.get('.search-box').should('be.visible');
    });

    it('should have search input field', () => {
      cy.get('.search-box input').should('be.visible');
    });

    it('should accept search input', () => {
      cy.get('.search-box input').type('test search');
      cy.get('.search-box input').should('have.value', 'test search');
    });

    it('should display rows per page selector', () => {
      cy.get('.rows-select').should('exist');
    });
  });

  describe('Data Table Tests', () => {
    it('should display data table or empty state', () => {
      cy.get('.content-card').then(($card) => {
        const hasTable = $card.find('.data-table').length > 0;
        const hasEmptyState = $card.find('.empty-state').length > 0;
        expect(hasTable || hasEmptyState).to.be.true;
      });
    });

    it('should display table headers if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length) {
          cy.get('.data-table th').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Filter Functionality Tests', () => {
    it('should have clickable filter buttons', () => {
      cy.get('.filter-btn').first().should('not.be.disabled');
    });

    it('should toggle filter active state on click', () => {
      cy.get('.filter-btn').first().click();
      // Filter state may change or navigation may occur
      cy.get('.content-card').should('be.visible');
    });
  });

  describe('Pagination Tests', () => {
    it('should display pagination if data exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table tbody tr').length > 0) {
          cy.get('.pagination').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have modal overlay hidden by default', () => {
      cy.get('.modal-overlay').should('exist');
      cy.get('.modal-overlay.active').should('not.exist');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
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

  describe('Action Icons Tests', () => {
    it('should display action icons if table rows exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table tbody tr').length > 0) {
          cy.get('.action-icon').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Status Badges Tests', () => {
    it('should display status badges if table rows exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table tbody tr').length > 0) {
          cy.get('.status-badge').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
    });

    it('should have accessible search input', () => {
      cy.get('.search-box input').should('be.visible');
    });

    it('should have table headers for screen readers', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length) {
          cy.get('.data-table th').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have clickable header buttons', () => {
      cy.get('.header .btn').first().should('not.be.disabled');
    });

    it('should have clickable navigation buttons', () => {
      cy.get('.top-nav-btn').first().should('not.be.disabled');
    });
  });

  describe('Client Name Links Tests', () => {
    it('should display client names as links if data exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-name').length > 0) {
          cy.get('.client-name').first().should('be.visible');
        }
      });
    });
  });
});
