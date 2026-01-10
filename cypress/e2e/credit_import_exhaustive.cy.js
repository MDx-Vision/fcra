// Exhaustive test for /dashboard/credit-import
describe('Credit Report Auto-Import Page - /dashboard/credit-import', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/credit-import');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/credit-import');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Credit Report Auto-Import');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/credit-import').its('status').should('be.oneOf', [200, 302]);
    });

    it('should have data-testid on page', () => {
      cy.get('[data-testid="credit-import-page"]').should('exist');
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Credit Report Auto-Import');
    });

    it('should have page title data-testid', () => {
      cy.get('[data-testid="page-title"]').should('exist');
    });

    it('should display Import All Due button', () => {
      cy.get('[data-testid="import-all-due-btn"]').should('be.visible');
    });

    it('should display Add Credential button', () => {
      cy.get('[data-testid="add-credential-btn"]').should('be.visible');
    });

    it('should display Back to Dashboard button', () => {
      cy.get('[data-testid="back-btn"]').should('be.visible');
    });

    it('should have working back button link', () => {
      cy.get('[data-testid="back-btn"]').should('have.attr', 'href', '/dashboard');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should have data-testid on stats grid', () => {
      cy.get('[data-testid="stats-grid"]').should('exist');
    });

    it('should display stat cards', () => {
      cy.get('.stat-card').should('have.length', 4);
    });

    it('should display Total Credentials stat', () => {
      cy.get('.stat-label').contains('Total Credentials').should('exist');
    });

    it('should display Active stat', () => {
      cy.get('.stat-label').contains('Active').should('exist');
    });

    it('should display Last 24h Imports stat', () => {
      cy.get('.stat-label').contains('Last 24h Imports').should('exist');
    });

    it('should display Failed stat', () => {
      cy.get('.stat-label').contains('Failed').should('exist');
    });

    it('should have highlight card styling', () => {
      cy.get('.stat-card.highlight').should('exist');
    });

    it('should display stat values', () => {
      cy.get('.stat-value').should('have.length.at.least', 4);
    });
  });

  describe('Content Card Tests', () => {
    it('should display content card', () => {
      cy.get('.content-card').should('be.visible');
    });

    it('should have data-testid on credentials card', () => {
      cy.get('[data-testid="credentials-card"]').should('exist');
    });

    it('should display card header', () => {
      cy.get('.card-header').should('be.visible');
    });

    it('should display Stored Credentials title', () => {
      cy.get('.card-title').should('contain.text', 'Stored Credentials');
    });
  });

  describe('Table Tests', () => {
    it('should display credentials table', () => {
      cy.get('[data-testid="credentials-table"]').should('exist');
    });

    it('should have table headers', () => {
      cy.get('table th').should('have.length.at.least', 1);
    });

    it('should have Client column header', () => {
      cy.get('table th').contains('Client').should('exist');
    });

    it('should have Service column header', () => {
      cy.get('table th').contains('Service').should('exist');
    });

    it('should have Username column header', () => {
      cy.get('table th').contains('Username').should('exist');
    });

    it('should have Status column header', () => {
      cy.get('table th').contains('Status').should('exist');
    });

    it('should have Last Import column header', () => {
      cy.get('table th').contains('Last Import').should('exist');
    });

    it('should have Frequency column header', () => {
      cy.get('table th').contains('Frequency').should('exist');
    });

    it('should have Actions column header', () => {
      cy.get('table th').contains('Actions').should('exist');
    });

    it('should display table rows or empty state', () => {
      cy.get('table tbody').then(($tbody) => {
        const hasRows = $tbody.find('tr').length > 0;
        const hasEmptyState = $tbody.find('.empty-state').length > 0;
        expect(hasRows || hasEmptyState).to.be.true;
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have credential modal element', () => {
      cy.get('#credentialModal').should('exist');
    });

    it('should have data-testid on modal', () => {
      cy.get('[data-testid="credential-modal"]').should('exist');
    });

    it('should have modal hidden by default', () => {
      cy.get('.modal-overlay.active').should('not.exist');
    });

    it('should open modal when Add Credential is clicked', () => {
      cy.get('[data-testid="add-credential-btn"]').click();
      cy.get('#credentialModal.active').should('be.visible');
    });

    it('should have modal close button', () => {
      cy.get('.modal-close').should('exist');
    });

    it('should close modal when close button is clicked', () => {
      cy.get('[data-testid="add-credential-btn"]').click();
      cy.get('#credentialModal.active').should('be.visible');
      cy.get('.modal-close').click();
      cy.get('#credentialModal.active').should('not.exist');
    });
  });

  describe('Add Credential Form Tests', () => {
    beforeEach(() => {
      cy.get('[data-testid="add-credential-btn"]').click();
    });

    it('should display form in modal', () => {
      cy.get('#credentialForm').should('be.visible');
    });

    it('should have client select', () => {
      cy.get('[data-testid="client-select"]').should('exist');
    });

    it('should have service select', () => {
      cy.get('[data-testid="service-select"]').should('exist');
    });

    it('should have username input', () => {
      cy.get('[data-testid="username-input"]').should('exist');
    });

    it('should have password input', () => {
      cy.get('[data-testid="password-input"]').should('exist');
    });

    it('should have SSN last 4 input', () => {
      cy.get('[data-testid="ssn-last4-input"]').should('exist');
    });

    it('should have frequency select', () => {
      cy.get('[data-testid="frequency-select"]').should('exist');
    });

    it('should have Save Credential button', () => {
      cy.get('[data-testid="save-credential-btn"]').scrollIntoView().should('exist');
    });

    it('should have Cancel button', () => {
      cy.get('.modal-footer .btn-secondary').contains('Cancel').scrollIntoView().should('exist');
    });

    it('should have frequency options', () => {
      cy.get('[data-testid="frequency-select"] option').should('have.length.at.least', 3);
    });
  });

  describe('Alert Container Tests', () => {
    it('should have alert container', () => {
      cy.get('#alertContainer').should('exist');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
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
      cy.get('.header h1').should('be.visible');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have clickable Import All Due button', () => {
      cy.get('[data-testid="import-all-due-btn"]').should('not.be.disabled');
    });

    it('should have clickable Add Credential button', () => {
      cy.get('[data-testid="add-credential-btn"]').should('not.be.disabled');
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
    });

    it('should have form labels in modal', () => {
      cy.get('[data-testid="add-credential-btn"]').click();
      cy.get('#credentialForm label').should('have.length.at.least', 1);
    });

    it('should have table headers for accessibility', () => {
      cy.get('table th').should('have.length.at.least', 1);
    });
  });

  describe('Empty State Tests', () => {
    it('should display empty state when no credentials', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length > 0) {
          cy.get('.empty-state').should('be.visible');
          cy.get('.empty-state h3').should('contain.text', 'No Credentials Stored');
        }
      });
    });
  });
});
