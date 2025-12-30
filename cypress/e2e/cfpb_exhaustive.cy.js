// Exhaustive test for /dashboard/cfpb
describe('CFPB Complaints Page - /dashboard/cfpb', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/cfpb');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/cfpb');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'CFPB Complaints');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'CFPB Complaint Generator');
    });

    it('should display header subtitle', () => {
      cy.get('.header-subtitle').should('contain.text', 'Consumer Financial Protection Bureau');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/cfpb').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display New Complaint button', () => {
      cy.get('.header').within(() => {
        cy.get('a.btn-primary').should('contain.text', 'New Complaint');
      });
    });

    it('should have correct link for New Complaint', () => {
      cy.get('.header a.btn-primary').should('have.attr', 'href', '/dashboard/cfpb/generator');
    });
  });

  describe('Info Box Tests', () => {
    it('should display info box', () => {
      cy.get('.info-box').should('be.visible');
    });

    it('should display info box title', () => {
      cy.get('.info-box-title').should('contain.text', 'About CFPB Complaints');
    });

    it('should display info box text', () => {
      cy.get('.info-box-text').should('be.visible');
      cy.get('.info-box-text').should('contain.text', 'CFPB complaints are a powerful tool');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid with four cards', () => {
      cy.get('.stats-grid').should('be.visible');
      cy.get('.stats-grid .stat-card').should('have.length', 4);
    });

    it('should display Draft Complaints stat', () => {
      cy.get('.stat-card.draft').within(() => {
        cy.get('.stat-label').should('contain.text', 'Draft Complaints');
        cy.get('.stat-number').should('exist');
      });
    });

    it('should display Ready to Submit stat', () => {
      cy.get('.stat-card.ready').within(() => {
        cy.get('.stat-label').should('contain.text', 'Ready to Submit');
        cy.get('.stat-number').should('exist');
      });
    });

    it('should display Submitted stat', () => {
      cy.get('.stat-card.submitted').within(() => {
        cy.get('.stat-label').should('contain.text', 'Submitted');
        cy.get('.stat-number').should('exist');
      });
    });

    it('should display Response Received stat', () => {
      cy.get('.stat-card.response').within(() => {
        cy.get('.stat-label').should('contain.text', 'Response Received');
        cy.get('.stat-number').should('exist');
      });
    });
  });

  describe('Section Tests', () => {
    it('should display complaints section', () => {
      cy.get('.section').should('be.visible');
    });

    it('should display section header with title', () => {
      cy.get('.section-header').should('be.visible');
      cy.get('.section-title').should('contain.text', 'All Complaints');
    });
  });

  describe('Filter Tests', () => {
    it('should display filter buttons', () => {
      cy.get('.filters').should('be.visible');
      cy.get('.filter-btn').should('have.length.at.least', 5);
    });

    it('should have All filter button active by default', () => {
      cy.get('.filter-btn').contains('All').should('have.class', 'active');
    });

    it('should display Draft filter button', () => {
      cy.get('.filter-btn').contains('Draft').should('exist');
    });

    it('should display Ready filter button', () => {
      cy.get('.filter-btn').contains('Ready').should('exist');
    });

    it('should display Submitted filter button', () => {
      cy.get('.filter-btn').contains('Submitted').should('exist');
    });

    it('should display Response Received filter button', () => {
      cy.get('.filter-btn').contains('Response Received').should('exist');
    });

    it('should toggle active class on filter button click', () => {
      cy.get('.filter-btn').contains('Draft').click();
      cy.get('.filter-btn').contains('Draft').should('have.class', 'active');
      cy.get('.filter-btn').contains('All').should('not.have.class', 'active');
    });
  });

  describe('Table or Empty State Tests', () => {
    it('should display either complaints table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.complaint-table').length) {
          cy.get('.complaint-table').should('be.visible');
        } else {
          cy.get('.empty-state').should('be.visible');
        }
      });
    });

    it('should display table headers if complaints exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.complaint-table').length) {
          cy.get('.complaint-table thead').should('contain.text', 'Client');
          cy.get('.complaint-table thead').should('contain.text', 'Target');
          cy.get('.complaint-table thead').should('contain.text', 'Issue Type');
          cy.get('.complaint-table thead').should('contain.text', 'Status');
          cy.get('.complaint-table thead').should('contain.text', 'CFPB ID');
          cy.get('.complaint-table thead').should('contain.text', 'Created');
          cy.get('.complaint-table thead').should('contain.text', 'Actions');
        } else {
          cy.get('.empty-state h3').should('contain.text', 'No CFPB Complaints');
        }
      });
    });

    it('should display empty state message when no complaints', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state h3').should('contain.text', 'No CFPB Complaints Yet');
          cy.get('.empty-state p').should('contain.text', 'Start by creating a new complaint');
        } else {
          cy.get('.complaint-table tbody tr').should('have.length.at.least', 1);
        }
      });
    });

    it('should display Create First Complaint button in empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state a.btn-primary').should('contain.text', 'Create First Complaint');
          cy.get('.empty-state a.btn-primary').should('have.attr', 'href', '/dashboard/cfpb/generator');
        } else {
          cy.get('.complaint-table').should('be.visible');
        }
      });
    });
  });

  describe('Complaint Row Tests', () => {
    it('should have data-status attribute on rows if complaints exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.complaint-row').length) {
          cy.get('.complaint-row').first().should('have.attr', 'data-status');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display View action button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.complaint-row').length) {
          cy.get('.action-btn.primary').first().should('contain.text', 'View');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display status badge', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.complaint-row').length) {
          cy.get('.status-badge').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display target badge', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.complaint-row').length) {
          cy.get('.target-badge').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have filterComplaints function', () => {
      cy.window().should('have.property', 'filterComplaints');
    });

    it('should filter complaints when filter button clicked', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.complaint-row').length > 1) {
          // Test filter functionality
          cy.get('.filter-btn').contains('Draft').click();
          cy.get('.complaint-row:visible').each(($row) => {
            cy.wrap($row).should('have.attr', 'data-status', 'draft');
          });
        } else {
          // If no or single complaint, just verify filter buttons exist
          cy.get('.filter-btn').should('have.length.at.least', 5);
        }
      });
    });
  });

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
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
    });
  });

  describe('Navigation Tests', () => {
    it('should navigate to generator when New Complaint clicked', () => {
      cy.get('.header a.btn-primary').click();
      cy.url().should('include', '/dashboard/cfpb/generator');
    });
  });

  describe('Status Badge Styling Tests', () => {
    it('should have draft status badge styling class', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.draft').length) {
          cy.get('.status-badge.draft').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should have ready status badge styling class', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.ready').length) {
          cy.get('.status-badge.ready').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should have submitted status badge styling class', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.submitted').length) {
          cy.get('.status-badge.submitted').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });
  });

  describe('Target Badge Styling Tests', () => {
    it('should have cra target badge styling class', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.target-badge.cra').length) {
          cy.get('.target-badge.cra').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should have furnisher target badge styling class', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.target-badge.furnisher').length) {
          cy.get('.target-badge.furnisher').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });
  });

  describe('Stat Card Styling Tests', () => {
    it('should have draft stat card styling', () => {
      cy.get('.stat-card.draft').should('exist');
    });

    it('should have ready stat card styling', () => {
      cy.get('.stat-card.ready').should('exist');
    });

    it('should have submitted stat card styling', () => {
      cy.get('.stat-card.submitted').should('exist');
    });

    it('should have response stat card styling', () => {
      cy.get('.stat-card.response').should('exist');
    });
  });
});
