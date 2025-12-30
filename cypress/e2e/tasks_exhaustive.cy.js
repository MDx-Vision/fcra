// Exhaustive test for /dashboard/tasks
describe('Task Queue Page - /dashboard/tasks', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/tasks');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/tasks');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Task');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/tasks').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('h1').should('contain.text', 'Task Queue');
    });

    it('should display Refresh button', () => {
      cy.get('.btn-secondary').contains('Refresh').should('be.visible');
    });

    it('should display Process Tasks button', () => {
      cy.get('.btn-secondary').contains('Process').should('be.visible');
    });

    it('should display New Task button', () => {
      cy.get('.btn-primary').contains('New Task').should('be.visible');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display pending stat', () => {
      cy.get('#stat-pending').should('exist');
    });

    it('should display running stat', () => {
      cy.get('#stat-running').should('exist');
    });

    it('should display completed today stat', () => {
      cy.get('#stat-completed-today').should('exist');
    });
  });

  describe('Content Card Tests', () => {
    it('should display content card', () => {
      cy.get('.content-card').should('be.visible');
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

  describe('Filter Tests', () => {
    it('should display filters section', () => {
      cy.get('.filters').should('exist');
    });

    it('should have filter select elements', () => {
      cy.get('.filter-select').should('have.length.at.least', 1);
    });
  });

  describe('Modal Tests', () => {
    it('should have modal overlay element', () => {
      cy.get('.modal-overlay').should('exist');
    });

    it('should have modal hidden by default', () => {
      cy.get('.modal-overlay.active').should('not.exist');
    });

    it('should have modal close button', () => {
      cy.get('.modal-close').should('exist');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have clickable Refresh button', () => {
      cy.get('.btn-secondary').contains('Refresh').should('not.be.disabled');
    });

    it('should have clickable New Task button', () => {
      cy.get('.btn-primary').contains('New Task').should('not.be.disabled');
    });

    it('should have primary button styling', () => {
      cy.get('.btn-primary').should('exist');
    });

    it('should have secondary button styling', () => {
      cy.get('.btn-secondary').should('exist');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
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
      cy.get('h1').should('be.visible');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
    });

    it('should have accessible table if exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Action Buttons Tests', () => {
    it('should display action buttons in table if tasks exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table tbody tr').length > 0) {
          cy.get('.action-btn').should('have.length.at.least', 1);
        }
      });
    });
  });
});
