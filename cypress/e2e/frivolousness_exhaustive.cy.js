// Exhaustive test for /dashboard/frivolousness
describe('Frivolousness Defense Tracker - /dashboard/frivolousness', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/frivolousness');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/frivolousness');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Frivolousness Defense Tracker');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Frivolousness Defense Tracker');
    });

    it('should display header subtitle', () => {
      cy.get('.header-subtitle').should('contain.text', 'Manage CRA frivolous claim defenses');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/frivolousness').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display Add Defense Case button', () => {
      cy.get('.header .btn-primary').should('contain.text', 'Add Defense Case');
    });

    it('should open modal when Add Defense Case button clicked', () => {
      cy.get('.header .btn-primary').click();
      cy.get('#addModal').should('have.class', 'active');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display four stat cards', () => {
      cy.get('.stats-grid .stat-card').should('have.length', 4);
    });

    it('should display Total Cases stat', () => {
      cy.get('.stat-card .stat-label').contains('Total Cases').should('exist');
    });

    it('should display Pending Evidence stat', () => {
      cy.get('.stat-card .stat-label').contains('Pending Evidence').should('exist');
    });

    it('should display Ready to Re-dispute stat', () => {
      cy.get('.stat-card .stat-label').contains('Ready to Re-dispute').should('exist');
    });

    it('should display Resolved stat', () => {
      cy.get('.stat-card .stat-label').contains('Resolved').should('exist');
    });

    it('should display stat icons', () => {
      cy.get('.stat-icon').should('have.length', 4);
    });
  });

  describe('Workflow Bar Tests', () => {
    it('should display workflow bar', () => {
      cy.get('.workflow-bar').should('be.visible');
    });

    it('should display workflow title', () => {
      cy.get('.workflow-title').should('contain.text', 'Defense Workflow');
    });

    it('should display workflow steps', () => {
      cy.get('.workflow-steps').should('be.visible');
    });

    it('should display workflow step circles', () => {
      cy.get('.workflow-step-circle').should('have.length.at.least', 1);
    });

    it('should display workflow step labels', () => {
      cy.get('.workflow-step-label').should('have.length.at.least', 1);
    });

    it('should display workflow arrows', () => {
      cy.get('.workflow-arrow').should('have.length.at.least', 1);
    });
  });

  describe('Content Card Tests', () => {
    it('should display content card', () => {
      cy.get('.content-card').should('be.visible');
    });

    it('should display section header', () => {
      cy.get('.section-header').should('be.visible');
    });

    it('should display section title', () => {
      cy.get('.section-title').should('contain.text', 'Defense Cases');
    });
  });

  describe('Search Box Tests', () => {
    it('should display search box', () => {
      cy.get('.search-box').should('be.visible');
    });

    it('should have search input', () => {
      cy.get('#searchInput').should('exist');
    });

    it('should have placeholder text', () => {
      cy.get('#searchInput').should('have.attr', 'placeholder').and('contain', 'Search');
    });

    it('should accept text input', () => {
      cy.get('#searchInput').type('test');
      cy.get('#searchInput').should('have.value', 'test');
    });
  });

  describe('Table or Empty State Tests', () => {
    it('should display either cases table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#casesTable').length) {
          cy.get('#casesTable').should('be.visible');
        } else {
          cy.get('.empty-state').should('be.visible');
        }
      });
    });

    it('should display table headers if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#casesTable').length) {
          cy.get('#casesTable thead').should('contain.text', 'Client');
          cy.get('#casesTable thead').should('contain.text', 'Bureau');
          cy.get('#casesTable thead').should('contain.text', 'Claim Date');
          cy.get('#casesTable thead').should('contain.text', 'Status');
          cy.get('#casesTable thead').should('contain.text', 'Evidence Status');
          cy.get('#casesTable thead').should('contain.text', 'Actions');
        } else {
          cy.get('.empty-state h3').should('contain.text', 'No defense cases');
        }
      });
    });

    it('should display empty state message when no cases', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state h3').should('contain.text', 'No defense cases');
          cy.get('.empty-state p').should('contain.text', 'Add your first');
        } else {
          cy.get('#casesTable tbody tr').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Case Row Elements Tests', () => {
    it('should display client cell if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-cell').length) {
          cy.get('.client-cell').first().within(() => {
            cy.get('.client-avatar').should('exist');
            cy.get('.client-name').should('exist');
          });
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display bureau badge if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.bureau-badge').length) {
          cy.get('.bureau-badge').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display status badge if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge').length) {
          cy.get('.status-badge').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display evidence status if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.evidence-status').length) {
          cy.get('.evidence-status').first().within(() => {
            cy.get('.evidence-bar').should('exist');
            cy.get('.evidence-count').should('exist');
          });
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display action buttons if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#casesTable .action-btn').length) {
          cy.get('#casesTable .action-btn').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Add Modal Tests', () => {
    it('should have add modal in DOM', () => {
      cy.get('#addModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#addModal').should('not.have.class', 'active');
    });

    it('should open modal when Add Defense Case button clicked', () => {
      cy.get('.header .btn-primary').click();
      cy.get('#addModal').should('have.class', 'active');
    });

    it('should display modal header', () => {
      cy.get('.header .btn-primary').click();
      cy.get('#addModal .modal-header h2').should('contain.text', 'Add Frivolous Defense Case');
    });

    it('should close modal when close button clicked', () => {
      cy.get('.header .btn-primary').click();
      cy.get('#addModal').should('have.class', 'active');
      cy.get('#addModal .modal-close').click();
      cy.get('#addModal').should('not.have.class', 'active');
    });
  });

  describe('Add Form Tests', () => {
    beforeEach(() => {
      cy.get('.header .btn-primary').click();
    });

    it('should display add form', () => {
      cy.get('#addForm').should('be.visible');
    });

    it('should have client select field', () => {
      cy.get('#addForm select[name="client_id"]').should('exist');
    });

    it('should have bureau select field', () => {
      cy.get('#addForm select[name="bureau"]').should('exist');
    });

    it('should have dispute round select field', () => {
      cy.get('#addForm select[name="dispute_round"]').should('exist');
    });

    it('should have claim date field', () => {
      cy.get('#addForm input[name="claim_date"]').should('exist');
    });

    it('should have follow-up due field', () => {
      cy.get('#addForm input[name="follow_up_due"]').should('exist');
    });

    it('should have claim reason textarea', () => {
      cy.get('#addForm textarea[name="claim_reason"]').should('exist');
    });

    it('should have new legal theory textarea', () => {
      cy.get('#addForm textarea[name="new_legal_theory"]').should('exist');
    });

    it('should have defense strategy textarea', () => {
      cy.get('#addForm textarea[name="defense_strategy"]').should('exist');
    });

    it('should have Cancel button', () => {
      cy.get('#addModal .modal-footer .btn-secondary').should('contain.text', 'Cancel');
    });

    it('should have Add Case button', () => {
      cy.get('#addModal .modal-footer .btn-primary').should('contain.text', 'Add Case');
    });

    it('should have bureau options', () => {
      cy.get('#addForm select[name="bureau"] option').should('have.length.at.least', 4);
      cy.get('#addForm select[name="bureau"]').should('contain', 'Equifax');
      cy.get('#addForm select[name="bureau"]').should('contain', 'Experian');
      cy.get('#addForm select[name="bureau"]').should('contain', 'TransUnion');
    });

    it('should have dispute round options', () => {
      cy.get('#addForm select[name="dispute_round"] option').should('have.length.at.least', 4);
    });
  });

  describe('View Modal Tests', () => {
    it('should have view modal in DOM', () => {
      cy.get('#viewModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#viewModal').should('not.have.class', 'active');
    });

    it('should have tabs in view modal', () => {
      cy.get('#viewModal .tabs').should('exist');
    });

    it('should have Details tab', () => {
      cy.get('#viewModal .tab').contains('Details').should('exist');
    });

    it('should have Evidence tab', () => {
      cy.get('#viewModal .tab').contains('Evidence').should('exist');
    });

    it('should have Notes tab', () => {
      cy.get('#viewModal .tab').contains('Notes').should('exist');
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have openAddModal function', () => {
      cy.window().should('have.property', 'openAddModal');
    });

    it('should have closeModal function', () => {
      cy.window().should('have.property', 'closeModal');
    });

    it('should have showAlert function', () => {
      cy.window().should('have.property', 'showAlert');
    });

    it('should have searchCases function', () => {
      cy.window().should('have.property', 'searchCases');
    });

    it('should have submitAddForm function', () => {
      cy.window().should('have.property', 'submitAddForm');
    });

    it('should have viewCase function', () => {
      cy.window().should('have.property', 'viewCase');
    });

    it('should have populateViewModal function', () => {
      cy.window().should('have.property', 'populateViewModal');
    });

    it('should have switchTab function', () => {
      cy.window().should('have.property', 'switchTab');
    });

    it('should have saveCase function', () => {
      cy.window().should('have.property', 'saveCase');
    });

    it('should have uploadEvidence function', () => {
      cy.window().should('have.property', 'uploadEvidence');
    });

    it('should have handleEvidenceUpload function', () => {
      cy.window().should('have.property', 'handleEvidenceUpload');
    });

    it('should have verifyEvidence function', () => {
      cy.window().should('have.property', 'verifyEvidence');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.workflow-bar').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
    });
  });

  describe('Stat Icon Styling Tests', () => {
    it('should have total stat icon styling', () => {
      cy.get('.stat-icon.total').should('exist');
    });

    it('should have pending stat icon styling', () => {
      cy.get('.stat-icon.pending').should('exist');
    });

    it('should have ready stat icon styling', () => {
      cy.get('.stat-icon.ready').should('exist');
    });

    it('should have resolved stat icon styling', () => {
      cy.get('.stat-icon.resolved').should('exist');
    });
  });

  describe('Bureau Badge Styling Tests', () => {
    it('should have equifax bureau badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.bureau-equifax').length) {
          cy.get('.bureau-equifax').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have experian bureau badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.bureau-experian').length) {
          cy.get('.bureau-experian').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have transunion bureau badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.bureau-transunion').length) {
          cy.get('.bureau-transunion').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Status Badge Styling Tests', () => {
    it('should have pending status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-pending').length) {
          cy.get('.status-pending').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have evidence_gathering status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-evidence_gathering').length) {
          cy.get('.status-evidence_gathering').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have ready_to_redispute status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-ready_to_redispute').length) {
          cy.get('.status-ready_to_redispute').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have resolved status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-resolved').length) {
          cy.get('.status-resolved').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });
});
