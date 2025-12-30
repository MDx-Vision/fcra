// Exhaustive test for /dashboard/letter-queue
describe('Letter Queue Page - /dashboard/letter-queue', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/letter-queue');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/letter-queue');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Letter Queue');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/letter-queue').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Letter Queue');
    });

    it('should display header subtitle', () => {
      cy.get('.header p').should('contain.text', 'Review and approve');
    });

    it('should display Run Trigger Check button', () => {
      cy.get('.btn-secondary').contains('Run Trigger Check').should('be.visible');
    });

    it('should display Approve Selected button', () => {
      cy.get('.btn-success').contains('Approve Selected').should('be.visible');
    });

    it('should have Approve Selected button initially disabled', () => {
      cy.get('#btnBulkApprove').should('be.disabled');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display stat cards', () => {
      cy.get('.stat-card').should('have.length', 4);
    });

    it('should display Pending Letters stat', () => {
      cy.get('.stat-label').contains('Pending Letters').should('exist');
    });

    it('should display Urgent stat', () => {
      cy.get('.stat-label').contains('Urgent').should('exist');
    });

    it('should display Approved Today stat', () => {
      cy.get('.stat-label').contains('Approved Today').should('exist');
    });

    it('should display Generated Today stat', () => {
      cy.get('.stat-label').contains('Generated Today').should('exist');
    });

    it('should have highlight card styling', () => {
      cy.get('.stat-card.highlight').should('exist');
    });

    it('should have urgent card styling', () => {
      cy.get('.stat-card.urgent').should('exist');
    });

    it('should have success card styling', () => {
      cy.get('.stat-card.success').should('exist');
    });

    it('should have purple card styling', () => {
      cy.get('.stat-card.purple').should('exist');
    });
  });

  describe('Card Tests', () => {
    it('should display main card', () => {
      cy.get('.card').should('be.visible');
    });

    it('should display card header', () => {
      cy.get('.card-header').should('be.visible');
    });

    it('should display Pending Letters title', () => {
      cy.get('.card-title').should('contain.text', 'Pending Letters');
    });

    it('should display Select All checkbox', () => {
      cy.get('#selectAll').should('exist');
    });

    it('should have Select All label', () => {
      cy.get('label[for="selectAll"]').should('contain.text', 'Select All');
    });
  });

  describe('Filter Bar Tests', () => {
    it('should display filter bar', () => {
      cy.get('.filter-bar').should('be.visible');
    });

    it('should have priority filter dropdown', () => {
      cy.get('#filterPriority').should('be.visible');
    });

    it('should have priority filter options', () => {
      cy.get('#filterPriority option').should('have.length.at.least', 5);
    });

    it('should have letter type filter dropdown', () => {
      cy.get('#filterLetterType').should('be.visible');
    });

    it('should have letter type filter options', () => {
      cy.get('#filterLetterType option').should('have.length.at.least', 7);
    });

    it('should allow selection of priority filter', () => {
      cy.get('#filterPriority').select('urgent');
      cy.get('#filterPriority').should('have.value', 'urgent');
    });

    it('should allow selection of letter type filter', () => {
      cy.get('#filterLetterType').select('mov_request');
      cy.get('#filterLetterType').should('have.value', 'mov_request');
    });
  });

  describe('Queue Container Tests', () => {
    it('should display queue container', () => {
      cy.get('#queueContainer').should('exist');
    });

    it('should show loading or queue content', () => {
      cy.get('#queueContainer').then(($container) => {
        const hasLoading = $container.find('.loading').length > 0;
        const hasQueue = $container.find('.queue-list').length > 0;
        const hasEmpty = $container.find('.empty-state').length > 0;
        expect(hasLoading || hasQueue || hasEmpty).to.be.true;
      });
    });
  });

  describe('Action Buttons Section Tests', () => {
    it('should display action buttons section', () => {
      cy.get('.btn-sm').should('have.length.at.least', 1);
    });

    it('should have Download PDF button', () => {
      cy.get('.btn-sm').contains('Download PDF').should('exist');
    });

    it('should have Print button', () => {
      cy.get('.btn-sm').contains('Print').should('exist');
    });

    it('should have Mark as Sent button', () => {
      cy.get('.btn-sm').contains('Mark as Sent').should('exist');
    });

    it('should have Resend button', () => {
      cy.get('.btn-sm').contains('Resend').should('exist');
    });
  });

  describe('Modal Tests', () => {
    it('should have dismiss modal element', () => {
      cy.get('#dismissModal').should('exist');
    });

    it('should have modal hidden by default', () => {
      cy.get('.modal-overlay.active').should('not.exist');
    });

    it('should have dismiss reason textarea', () => {
      cy.get('#dismissReason').should('exist');
    });

    it('should have modal action buttons', () => {
      cy.get('.modal-actions .btn').should('have.length.at.least', 2);
    });
  });

  describe('Toast Tests', () => {
    it('should have toast element', () => {
      cy.get('#toast').should('exist');
    });

    it('should have toast hidden by default', () => {
      cy.get('#toast').should('not.have.class', 'show');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.card').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.card').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.header h1').should('be.visible');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have clickable Run Trigger Check button', () => {
      cy.get('.btn-secondary').contains('Run Trigger Check').should('not.be.disabled');
    });

    it('should have secondary button styling', () => {
      cy.get('.btn-secondary').should('exist');
    });

    it('should have success button styling', () => {
      cy.get('.btn-success').should('exist');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
    });

    it('should have checkbox labels', () => {
      cy.get('label[for="selectAll"]').should('exist');
    });

    it('should have filter labels', () => {
      cy.get('.filter-bar select').should('have.length.at.least', 2);
    });
  });

  describe('Empty State Tests', () => {
    it('should display empty state when no pending letters', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length > 0) {
          cy.get('.empty-state').should('be.visible');
          cy.get('.empty-state h3').should('contain.text', 'No Pending Letters');
        }
      });
    });
  });
});
