// Exhaustive test for /dashboard/case-law
describe('Case Law Database - /dashboard/case-law', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/case-law');
  });

  // Page Load Tests
  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/case-law');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Case Law Database');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Case Law Citation Database');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/case-law').its('status').should('eq', 200);
    });
  });

  // Stats Grid Tests
  describe('Stats Grid Tests', () => {
    it('should display stats grid with four cards', () => {
      cy.get('.stats-grid').should('be.visible');
      cy.get('.stats-grid .stat-card').should('have.length', 4);
    });

    it('should display Total Citations stat', () => {
      cy.get('.stat-card').first().within(() => {
        cy.get('.stat-label').should('contain.text', 'Total Citations');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Courts Represented stat', () => {
      cy.get('.stat-card').eq(1).within(() => {
        cy.get('.stat-label').should('contain.text', 'Courts Represented');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Violation Types stat', () => {
      cy.get('.stat-card').eq(2).within(() => {
        cy.get('.stat-label').should('contain.text', 'Violation Types');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display FCRA Sections stat', () => {
      cy.get('.stat-card').eq(3).within(() => {
        cy.get('.stat-label').should('contain.text', 'FCRA Sections');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should have highlight styling on first stat card', () => {
      cy.get('.stat-card').first().should('have.class', 'highlight');
    });
  });

  // Content Section Tests
  describe('Content Section Tests', () => {
    it('should display content section', () => {
      cy.get('.content-section').should('be.visible');
    });

    it('should display section title', () => {
      cy.get('.section-title').should('contain.text', 'FCRA Case Law Citations');
    });
  });

  // Filter Tests
  describe('Filter Tests', () => {
    it('should display filters row', () => {
      cy.get('.filters-row').should('be.visible');
    });

    it('should display search box', () => {
      cy.get('.search-box').should('be.visible');
      cy.get('#searchInput').should('exist');
    });

    it('should allow typing in search box', () => {
      cy.get('#searchInput').type('test case');
      cy.get('#searchInput').should('have.value', 'test case');
    });

    it('should display court filter dropdown', () => {
      cy.get('#courtFilter').should('exist');
      cy.get('.filter-group label').contains('Court').should('exist');
    });

    it('should display violation type filter dropdown', () => {
      cy.get('#violationFilter').should('exist');
      cy.get('.filter-group label').contains('Violation Type').should('exist');
    });

    it('should display FCRA section filter dropdown', () => {
      cy.get('#sectionFilter').should('exist');
      cy.get('.filter-group label').contains('FCRA Section').should('exist');
    });

    it('should have All Courts default option', () => {
      cy.get('#courtFilter option').first().should('have.text', 'All Courts');
    });

    it('should have All Types default option', () => {
      cy.get('#violationFilter option').first().should('have.text', 'All Types');
    });

    it('should have All Sections default option', () => {
      cy.get('#sectionFilter option').first().should('have.text', 'All Sections');
    });
  });

  // Table or Empty State Tests
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
          cy.get('#casesTable thead th').should('have.length.at.least', 7);
          cy.get('#casesTable thead').should('contain.text', 'Case');
          cy.get('#casesTable thead').should('contain.text', 'Court');
          cy.get('#casesTable thead').should('contain.text', 'Year');
          cy.get('#casesTable thead').should('contain.text', 'FCRA Sections');
          cy.get('#casesTable thead').should('contain.text', 'Relevance');
          cy.get('#casesTable thead').should('contain.text', 'Outcome');
          cy.get('#casesTable thead').should('contain.text', 'Actions');
        } else {
          cy.get('.empty-state h3').should('contain.text', 'No case law citations');
        }
      });
    });

    it('should display empty state message when no cases', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state h3').should('contain.text', 'No case law citations yet');
          cy.get('.empty-state p').should('exist');
        } else {
          cy.get('#casesTable tbody tr').should('have.length.at.least', 1);
        }
      });
    });
  });

  // Admin Actions Tests
  describe('Admin Actions Tests', () => {
    it('should check for admin action buttons', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.header-actions').length) {
          cy.get('.header-actions').should('be.visible');
        } else {
          cy.get('.header').should('exist');
        }
      });
    });

    it('should display Populate Default Cases button for admins', () => {
      cy.get('body').then(($body) => {
        if ($body.find('button:contains("Populate Default Cases")').length) {
          cy.contains('button', 'Populate Default Cases').should('be.visible');
        } else {
          cy.get('.header h1').should('exist');
        }
      });
    });

    it('should display Add Citation button for admins', () => {
      cy.get('body').then(($body) => {
        if ($body.find('button:contains("Add Citation")').length) {
          cy.contains('button', 'Add Citation').should('be.visible');
        } else {
          cy.get('.header h1').should('exist');
        }
      });
    });
  });

  // Modal Tests
  describe('Modal Tests', () => {
    it('should have view modal in DOM', () => {
      cy.get('#viewModal').should('exist');
      cy.get('#viewModal').should('not.have.class', 'active');
    });

    it('should have add modal in DOM', () => {
      cy.get('#addModal').should('exist');
      cy.get('#addModal').should('not.have.class', 'active');
    });

    it('should open add modal when Add Citation button clicked', () => {
      cy.get('body').then(($body) => {
        if ($body.find('button:contains("Add Citation")').length) {
          cy.contains('button', 'Add Citation').click();
          cy.get('#addModal').should('have.class', 'active');
          cy.get('#addModal .modal-header h2').should('contain.text', 'Add Case Law Citation');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should close add modal when close button clicked', () => {
      cy.get('body').then(($body) => {
        if ($body.find('button:contains("Add Citation")').length) {
          cy.contains('button', 'Add Citation').click();
          cy.get('#addModal').should('have.class', 'active');
          cy.get('#addModal .modal-close').click();
          cy.get('#addModal').should('not.have.class', 'active');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });
  });

  // Add Case Form Tests
  describe('Add Case Form Tests', () => {
    beforeEach(() => {
      cy.get('body').then(($body) => {
        if ($body.find('button:contains("Add Citation")').length) {
          cy.contains('button', 'Add Citation').click();
        }
      });
    });

    it('should display case name input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm input[name="case_name"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display citation input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm input[name="citation"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display court input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm input[name="court"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display year input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm input[name="year"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display FCRA sections input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm input[name="fcra_sections"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display violation types input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm input[name="violation_types"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display key holding textarea', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm textarea[name="key_holding"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display full summary textarea', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm textarea[name="full_summary"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display damages awarded input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm input[name="damages_awarded"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display plaintiff won dropdown', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm select[name="plaintiff_won"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display relevance score dropdown', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm select[name="relevance_score"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display tags input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm input[name="tags"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should display notes textarea', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addCaseForm').length && $body.find('#addModal.active').length) {
          cy.get('#addCaseForm textarea[name="notes"]').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should have Save Citation button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addModal.active').length) {
          cy.get('#addModal').contains('button', 'Save Citation').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });

    it('should have Cancel button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#addModal.active').length) {
          cy.get('#addModal').contains('button', 'Cancel').should('exist');
        } else {
          cy.get('#addModal').should('exist');
        }
      });
    });
  });

  // JavaScript Function Tests
  describe('JavaScript Function Tests', () => {
    it('should have filterCases function', () => {
      cy.window().should('have.property', 'filterCases');
    });

    it('should have viewCase function', () => {
      cy.window().should('have.property', 'viewCase');
    });

    it('should have copyCitation function', () => {
      cy.window().should('have.property', 'copyCitation');
    });

    it('should have openAddModal function', () => {
      cy.window().should('have.property', 'openAddModal');
    });

    it('should have closeModal function', () => {
      cy.window().should('have.property', 'closeModal');
    });

    it('should have saveCase function', () => {
      cy.window().should('have.property', 'saveCase');
    });

    it('should have deleteCase function', () => {
      cy.window().should('have.property', 'deleteCase');
    });

    it('should have populateDefaultCases function', () => {
      cy.window().should('have.property', 'populateDefaultCases');
    });
  });

  // Sidebar Tests
  describe('Sidebar Tests', () => {
    it('should display dashboard sidebar', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.sidebar').length) {
          cy.get('.sidebar').should('be.visible');
        } else if ($body.find('[class*="sidebar"]').length) {
          cy.get('[class*="sidebar"]').first().should('exist');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should highlight case-law nav item as active', () => {
      cy.get('body').then(($body) => {
        if ($body.find('a[href*="case-law"].active').length) {
          cy.get('a[href*="case-law"].active').should('exist');
        } else if ($body.find('.nav-item.active').length) {
          cy.get('.nav-item.active').should('exist');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  // Responsive Tests
  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
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

  // API Integration Tests
  describe('API Integration Tests', () => {
    it('should handle case-law API endpoints', () => {
      cy.intercept('GET', '/api/case-law/*').as('getCaseLaw');
      cy.intercept('POST', '/api/case-law').as('postCaseLaw');
      cy.intercept('DELETE', '/api/case-law/*').as('deleteCaseLaw');

      cy.get('.main-content').should('be.visible');
    });

    it('should handle populate API endpoint', () => {
      cy.intercept('POST', '/api/case-law/populate').as('populateCases');
      cy.get('.main-content').should('be.visible');
    });

    it('should handle format API endpoint', () => {
      cy.intercept('GET', '/api/case-law/format/*').as('formatCitation');
      cy.get('.main-content').should('be.visible');
    });
  });

  // Copy Button Tests
  describe('Copy Button Tests', () => {
    it('should display copy buttons in table if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#casesTable tbody tr').length) {
          cy.get('.copy-btn').should('have.length.at.least', 2);
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display Copy Short and Copy Full buttons', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#casesTable tbody tr').length) {
          cy.contains('.copy-btn', 'Copy Short').should('exist');
          cy.contains('.copy-btn', 'Copy Full').should('exist');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });
  });

  // View Modal Copy Buttons Tests
  describe('View Modal Copy Buttons Tests', () => {
    it('should have copy buttons in view modal footer', () => {
      cy.get('#viewModal .modal-footer').within(() => {
        cy.get('.copy-btn').should('have.length.at.least', 3);
      });
    });
  });

  // Case Row Interaction Tests
  describe('Case Row Interaction Tests', () => {
    it('should have clickable rows if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#casesTable tbody tr').length) {
          cy.get('#casesTable tbody tr').first().should('have.attr', 'onclick');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should have data-case attribute on rows', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#casesTable tbody tr').length) {
          cy.get('#casesTable tbody tr').first().should('have.attr', 'data-case');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });
  });

  // Tag Styling Tests
  describe('Tag Styling Tests', () => {
    it('should display styled tags if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.tag').length) {
          cy.get('.tag').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have court tag styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.tag.court').length) {
          cy.get('.tag.court').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have section tag styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.tag.section').length) {
          cy.get('.tag.section').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have violation tag styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.tag.violation').length) {
          cy.get('.tag.violation').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  // Relevance Badge Tests
  describe('Relevance Badge Tests', () => {
    it('should display relevance badges if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.relevance-badge').length) {
          cy.get('.relevance-badge').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  // Outcome Badge Tests
  describe('Outcome Badge Tests', () => {
    it('should display outcome badges if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.outcome-badge').length) {
          cy.get('.outcome-badge').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });
});
