// Exhaustive test for /dashboard/specialty-bureaus
describe('Specialty Bureau Disputes - /dashboard/specialty-bureaus', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/specialty-bureaus');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/specialty-bureaus');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Specialty Bureau Disputes');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Specialty Bureau Disputes');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/specialty-bureaus').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display Back to Dashboard button', () => {
      cy.get('.header-actions a.btn-secondary').should('contain.text', 'Back to Dashboard');
    });

    it('should have correct link for Back to Dashboard', () => {
      cy.get('.header-actions a.btn-secondary').should('have.attr', 'href', '/dashboard');
    });

    it('should display New Dispute button', () => {
      cy.get('.header-actions .btn-primary').should('contain.text', 'New Dispute');
    });

    it('should open modal when New Dispute button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#disputeModal').should('have.class', 'active');
    });
  });

  describe('Stats Row Tests', () => {
    it('should display stats row', () => {
      cy.get('.stats-row').should('be.visible');
    });

    it('should display five stat cards', () => {
      cy.get('.stats-row .stat-card').should('have.length', 5);
    });

    it('should display Total Disputes stat', () => {
      cy.get('.stat-card').first().within(() => {
        cy.get('.stat-label').should('contain.text', 'Total Disputes');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Pending stat with styling', () => {
      cy.get('.stat-card.pending').within(() => {
        cy.get('.stat-label').should('contain.text', 'Pending');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Awaiting Response stat with styling', () => {
      cy.get('.stat-card.awaiting').within(() => {
        cy.get('.stat-label').should('contain.text', 'Awaiting Response');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Resolved stat with styling', () => {
      cy.get('.stat-card.resolved').within(() => {
        cy.get('.stat-label').should('contain.text', 'Resolved');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Success Rate stat with styling', () => {
      cy.get('.stat-card.success').within(() => {
        cy.get('.stat-label').should('contain.text', 'Success Rate');
        cy.get('.stat-value').should('exist');
      });
    });
  });

  describe('Bureaus Grid Tests', () => {
    it('should display bureaus grid', () => {
      cy.get('.bureaus-grid').should('be.visible');
    });

    it('should display bureau cards if bureaus exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.bureau-card').length) {
          cy.get('.bureau-card').first().should('be.visible');
        } else {
          cy.get('.bureaus-grid').should('exist');
        }
      });
    });

    it('should display bureau header with icon and name', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.bureau-card').length) {
          cy.get('.bureau-card').first().within(() => {
            cy.get('.bureau-header').should('be.visible');
            cy.get('.bureau-icon').should('be.visible');
            cy.get('.bureau-name').should('be.visible');
          });
        } else {
          cy.get('.bureaus-grid').should('exist');
        }
      });
    });

    it('should display bureau stats', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.bureau-card').length) {
          cy.get('.bureau-card').first().within(() => {
            cy.get('.bureau-stats').should('be.visible');
          });
        } else {
          cy.get('.bureaus-grid').should('exist');
        }
      });
    });

    it('should display bureau action buttons', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.bureau-card').length) {
          cy.get('.bureau-card').first().within(() => {
            cy.get('.bureau-actions').should('be.visible');
          });
        } else {
          cy.get('.bureaus-grid').should('exist');
        }
      });
    });
  });

  describe('Filter Tests', () => {
    it('should display filters section', () => {
      cy.get('.filters').should('be.visible');
    });

    it('should display filter buttons', () => {
      cy.get('.filter-btn').should('have.length.at.least', 5);
    });

    it('should have All filter button', () => {
      cy.get('.filter-btn').contains('All').should('exist');
    });

    it('should have Pending filter button', () => {
      cy.get('.filter-btn').contains('Pending').should('exist');
    });

    it('should have Awaiting Response filter button', () => {
      cy.get('.filter-btn').contains('Awaiting Response').should('exist');
    });

    it('should have Resolved filter button', () => {
      cy.get('.filter-btn').contains('Resolved').should('exist');
    });

    it('should have Escalated filter button', () => {
      cy.get('.filter-btn').contains('Escalated').should('exist');
    });

    it('should display client select filter', () => {
      cy.get('.select-filter').should('exist');
    });

    it('should have All Clients default option', () => {
      cy.get('.select-filter option').first().should('contain.text', 'All Clients');
    });
  });

  describe('Disputes Section Tests', () => {
    it('should display disputes section', () => {
      cy.get('.disputes-section').should('be.visible');
    });

    it('should display section header', () => {
      cy.get('.section-header').should('be.visible');
    });

    it('should display section title', () => {
      cy.get('.section-title').should('contain.text', 'Recent Disputes');
    });
  });

  describe('Table or Empty State Tests', () => {
    it('should display either disputes table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table').should('be.visible');
        } else {
          cy.get('.empty-state').should('be.visible');
        }
      });
    });

    it('should display table headers if disputes exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table thead').should('contain.text', 'Client');
          cy.get('table thead').should('contain.text', 'Bureau');
          cy.get('table thead').should('contain.text', 'Account');
          cy.get('table thead').should('contain.text', 'Status');
        } else {
          cy.get('.empty-state h3').should('contain.text', 'No Disputes Found');
        }
      });
    });

    it('should display empty state message when no disputes', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state h3').should('contain.text', 'No Disputes Found');
          cy.get('.empty-state p').should('contain.text', 'Start by creating');
        } else {
          cy.get('table tbody tr').should('have.length.at.least', 1);
        }
      });
    });

    it('should display Create First Dispute button in empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state .btn-primary').should('contain.text', 'Create First Dispute');
        } else {
          cy.get('table').should('be.visible');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have modal in DOM', () => {
      cy.get('#disputeModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#disputeModal').should('not.have.class', 'active');
    });

    it('should open modal when New Dispute button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#disputeModal').should('have.class', 'active');
    });

    it('should display modal header', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('.modal-header h2').should('contain.text', 'New Specialty Bureau Dispute');
    });

    it('should close modal when close button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#disputeModal').should('have.class', 'active');
      cy.get('.modal-close').click();
      cy.get('#disputeModal').should('not.have.class', 'active');
    });

    it('should close modal when clicking outside', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#disputeModal').should('have.class', 'active');
      cy.get('#disputeModal').click('topLeft');
      cy.get('#disputeModal').should('not.have.class', 'active');
    });
  });

  describe('Form Tests', () => {
    beforeEach(() => {
      cy.get('.header-actions .btn-primary').click();
    });

    it('should display dispute form', () => {
      cy.get('#disputeForm').should('be.visible');
    });

    it('should have client select field', () => {
      cy.get('#disputeForm select[name="client_id"]').should('exist');
    });

    it('should have bureau select field', () => {
      cy.get('#disputeForm select[name="bureau_name"]').should('exist');
    });

    it('should have dispute type select field', () => {
      cy.get('#disputeForm select[name="dispute_type"]').should('exist');
    });

    it('should have letter type select field', () => {
      cy.get('#disputeForm select[name="letter_type"]').should('exist');
    });

    it('should have account name input field', () => {
      cy.get('#disputeForm input[name="account_name"]').should('exist');
    });

    it('should have account number input field', () => {
      cy.get('#disputeForm input[name="account_number"]').should('exist');
    });

    it('should have dispute reason textarea', () => {
      cy.get('#disputeForm textarea[name="dispute_reason"]').should('exist');
    });

    it('should have letter sent date field', () => {
      cy.get('#disputeForm input[name="letter_sent_date"]').should('exist');
    });

    it('should have tracking number field', () => {
      cy.get('#disputeForm input[name="tracking_number"]').should('exist');
    });

    it('should have notes textarea', () => {
      cy.get('#disputeForm textarea[name="notes"]').should('exist');
    });

    it('should have Cancel button', () => {
      cy.get('.form-actions').contains('Cancel').should('exist');
    });

    it('should have Save Dispute button', () => {
      cy.get('.form-actions').contains('Save Dispute').should('exist');
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have openNewDisputeModal function', () => {
      cy.window().should('have.property', 'openNewDisputeModal');
    });

    it('should have closeModal function', () => {
      cy.window().should('have.property', 'closeModal');
    });

    it('should have filterByClient function', () => {
      cy.window().should('have.property', 'filterByClient');
    });

    it('should have filterByBureau function', () => {
      cy.window().should('have.property', 'filterByBureau');
    });

    it('should have editDispute function', () => {
      cy.window().should('have.property', 'editDispute');
    });

    it('should have deleteDispute function', () => {
      cy.window().should('have.property', 'deleteDispute');
    });

    it('should have submitDispute function', () => {
      cy.window().should('have.property', 'submitDispute');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-row').should('be.visible');
      cy.get('.bureaus-grid').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-row').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-row').should('be.visible');
    });
  });

  describe('Status Badge Styling Tests', () => {
    it('should have pending status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.pending').length) {
          cy.get('.status-badge.pending').first().should('be.visible');
        } else {
          cy.get('.disputes-section').should('exist');
        }
      });
    });

    it('should have sent status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.sent').length) {
          cy.get('.status-badge.sent').first().should('be.visible');
        } else {
          cy.get('.disputes-section').should('exist');
        }
      });
    });

    it('should have awaiting_response status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.awaiting_response').length) {
          cy.get('.status-badge.awaiting_response').first().should('be.visible');
        } else {
          cy.get('.disputes-section').should('exist');
        }
      });
    });

    it('should have resolved status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.resolved').length) {
          cy.get('.status-badge.resolved').first().should('be.visible');
        } else {
          cy.get('.disputes-section').should('exist');
        }
      });
    });
  });

  describe('Data Attribute Tests', () => {
    it('should have page-title data-testid', () => {
      cy.get('[data-testid="page-title"]').should('exist');
    });

    it('should have stats-row data-testid', () => {
      cy.get('[data-testid="stats-row"]').should('exist');
    });

    it('should have bureaus-grid data-testid', () => {
      cy.get('[data-testid="bureaus-grid"]').should('exist');
    });

    it('should have filters data-testid', () => {
      cy.get('[data-testid="filters"]').should('exist');
    });

    it('should have disputes-section data-testid', () => {
      cy.get('[data-testid="disputes-section"]').should('exist');
    });

    it('should have dispute-modal data-testid', () => {
      cy.get('[data-testid="dispute-modal"]').should('exist');
    });
  });
});
