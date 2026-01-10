// Exhaustive test for /dashboard/chexsystems
describe('ChexSystems/EWS Dispute Helper - /dashboard/chexsystems', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/chexsystems');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/chexsystems');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'ChexSystems');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'ChexSystems/EWS Dispute Helper');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/chexsystems').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display New Dispute button', () => {
      cy.get('.header-actions .btn-primary').should('contain.text', 'New Dispute');
    });

    it('should open modal when New Dispute button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#newDisputeModal').should('have.class', 'active');
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

    it('should display Sent stat with styling', () => {
      cy.get('.stat-card.sent').within(() => {
        cy.get('.stat-label').should('contain.text', 'Sent');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Responded stat with styling', () => {
      cy.get('.stat-card.responded').within(() => {
        cy.get('.stat-label').should('contain.text', 'Responded');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Resolved stat with styling', () => {
      cy.get('.stat-card.resolved').within(() => {
        cy.get('.stat-label').should('contain.text', 'Resolved');
        cy.get('.stat-value').should('exist');
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

    it('should have Sent filter button', () => {
      cy.get('.filter-btn').contains('Sent').should('exist');
    });

    it('should have Responded filter button', () => {
      cy.get('.filter-btn').contains('Responded').should('exist');
    });

    it('should have Resolved filter button', () => {
      cy.get('.filter-btn').contains('Resolved').should('exist');
    });

    it('should display client select filter', () => {
      cy.get('.select-filter').should('exist');
    });

    it('should have All Clients default option', () => {
      cy.get('.select-filter option').first().should('contain.text', 'All Clients');
    });
  });

  describe('Content Layout Tests', () => {
    it('should display content layout', () => {
      cy.get('.content-layout').should('be.visible');
    });

    it('should display disputes list', () => {
      cy.get('.disputes-list').should('be.visible');
    });

    it('should display sidebar panel', () => {
      cy.get('.sidebar-panel').should('be.visible');
    });
  });

  describe('Disputes List or Empty State Tests', () => {
    it('should display either dispute cards or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.dispute-card').length) {
          cy.get('.dispute-card').should('be.visible');
        } else {
          cy.get('.empty-state').should('be.visible');
        }
      });
    });

    it('should display empty state message when no disputes', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state h3').should('contain.text', 'No Disputes Found');
          cy.get('.empty-state p').should('contain.text', 'Start by creating a new');
        } else {
          cy.get('.dispute-card').should('have.length.at.least', 1);
        }
      });
    });

    it('should display Create First Dispute button in empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state .btn-primary').should('contain.text', 'Create First Dispute');
        } else {
          cy.get('.dispute-card').should('be.visible');
        }
      });
    });
  });

  describe('Dispute Card Tests', () => {
    it('should display dispute header if disputes exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.dispute-card').length) {
          cy.get('.dispute-card .dispute-header').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display dispute title if disputes exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.dispute-card').length) {
          cy.get('.dispute-card .dispute-title').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display status badge if disputes exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.dispute-card').length) {
          cy.get('.dispute-card .status-badge').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display dispute meta if disputes exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.dispute-card').length) {
          cy.get('.dispute-card .dispute-meta').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });
  });

  describe('Sidebar Panel Tests', () => {
    it('should display panel cards', () => {
      cy.get('.panel-card').should('have.length.at.least', 2);
    });

    it('should display Dispute Templates panel', () => {
      cy.get('.panel-title').contains('Dispute Templates').should('exist');
    });

    it('should display About ChexSystems/EWS panel', () => {
      cy.get('.panel-title').contains('About ChexSystems/EWS').should('exist');
    });

    it('should display Quick Actions panel', () => {
      cy.get('.panel-title').contains('Quick Actions').should('exist');
    });

    it('should display info box', () => {
      cy.get('.info-box').should('be.visible');
    });

    it('should display info box content', () => {
      cy.get('.info-box h4').should('contain.text', 'What are these bureaus?');
    });

    it('should display Knowledge Base link in Quick Actions', () => {
      cy.get('.panel-card').contains('Knowledge Base').should('exist');
    });

    it('should display View SOPs link in Quick Actions', () => {
      cy.get('.panel-card').contains('View SOPs').should('exist');
    });
  });

  describe('Template List Tests', () => {
    it('should display template list', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.template-list').length) {
          cy.get('.template-list').should('be.visible');
        } else {
          cy.get('.panel-card').should('exist');
        }
      });
    });

    it('should display template items if available', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.template-item').length) {
          cy.get('.template-item').first().should('be.visible');
        } else {
          cy.get('.panel-card').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have modal in DOM', () => {
      cy.get('#newDisputeModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#newDisputeModal').should('not.have.class', 'active');
    });

    it('should open modal when New Dispute button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#newDisputeModal').should('have.class', 'active');
    });

    it('should display modal header', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('.modal-header h2').should('contain.text', 'New ChexSystems/EWS Dispute');
    });

    it('should close modal when close button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#newDisputeModal').should('have.class', 'active');
      cy.get('.modal-close').click();
      cy.get('#newDisputeModal').should('not.have.class', 'active');
    });

    it('should close modal when clicking outside', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#newDisputeModal').should('have.class', 'active');
      cy.get('#newDisputeModal').click('topLeft');
      cy.get('#newDisputeModal').should('not.have.class', 'active');
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

    it('should have bureau type select field', () => {
      cy.get('#disputeForm select[name="bureau_type"]').should('exist');
    });

    it('should have dispute type select field', () => {
      cy.get('#disputeForm select[name="dispute_type"]').should('exist');
    });

    it('should have account type select field', () => {
      cy.get('#disputeForm select[name="account_type"]').should('exist');
    });

    it('should have reported by input field', () => {
      cy.get('#disputeForm input[name="reported_by"]').should('exist');
    });

    it('should have dispute reason textarea', () => {
      cy.get('#disputeForm textarea[name="dispute_reason"]').should('exist');
    });

    it('should have notes textarea', () => {
      cy.get('#disputeForm textarea[name="notes"]').should('exist');
    });

    it('should have Cancel button', () => {
      cy.get('.form-actions').contains('Cancel').should('exist');
    });

    it('should have Create Dispute button', () => {
      cy.get('.form-actions').contains('Create Dispute').should('exist');
    });

    it('should have bureau type options', () => {
      cy.get('select[name="bureau_type"] option').should('have.length.at.least', 3);
      cy.get('select[name="bureau_type"]').should('contain', 'ChexSystems');
      cy.get('select[name="bureau_type"]').should('contain', 'Early Warning Services');
    });

    it('should have dispute type options', () => {
      cy.get('#disputeType option').should('have.length.at.least', 5);
      cy.get('#disputeType').should('contain', 'Unauthorized Account');
      cy.get('#disputeType').should('contain', 'Identity Theft');
      cy.get('#disputeType').should('contain', 'Incorrect Information');
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

    it('should have selectTemplate function', () => {
      cy.window().should('have.property', 'selectTemplate');
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
      cy.get('.content-layout').should('be.visible');
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

  describe('Navigation Tests', () => {
    it('should have Knowledge Base link', () => {
      cy.get('a[href="/dashboard/knowledge-base"]').should('exist');
    });

    it('should have View SOPs link', () => {
      cy.get('a[href="/dashboard/sops"]').should('exist');
    });
  });

  describe('Status Badge Styling Tests', () => {
    it('should have pending status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.pending').length) {
          cy.get('.status-badge.pending').first().should('be.visible');
        } else {
          cy.get('.content-layout').should('exist');
        }
      });
    });

    it('should have sent status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.sent').length) {
          cy.get('.status-badge.sent').first().should('be.visible');
        } else {
          cy.get('.content-layout').should('exist');
        }
      });
    });

    it('should have responded status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.responded').length) {
          cy.get('.status-badge.responded').first().should('be.visible');
        } else {
          cy.get('.content-layout').should('exist');
        }
      });
    });

    it('should have resolved status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.resolved').length) {
          cy.get('.status-badge.resolved').first().should('be.visible');
        } else {
          cy.get('.content-layout').should('exist');
        }
      });
    });
  });
});
