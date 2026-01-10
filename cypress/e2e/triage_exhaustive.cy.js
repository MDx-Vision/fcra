// Exhaustive test for /dashboard/triage
describe('Case Triage - /dashboard/triage', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/triage');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/triage');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Case Triage');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Case Triage');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/triage').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display Refresh button', () => {
      cy.get('.header-actions .btn-secondary').contains('Refresh').should('exist');
    });

    it('should display Back to Dashboard link', () => {
      cy.get('.header-actions a.btn-secondary').should('contain.text', 'Back to Dashboard');
    });

    it('should have correct link for Back to Dashboard', () => {
      cy.get('.header-actions a.btn-secondary').should('have.attr', 'href', '/dashboard');
    });
  });

  describe('Stats Grid Tests - Queue Stats', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display Fast Track stat card', () => {
      cy.get('.stat-card.fast-track').within(() => {
        cy.get('.stat-label').should('contain.text', 'Fast Track');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Standard Queue stat card', () => {
      cy.get('.stat-card.standard').within(() => {
        cy.get('.stat-label').should('contain.text', 'Standard Queue');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Review Needed stat card', () => {
      cy.get('.stat-card.review').within(() => {
        cy.get('.stat-label').should('contain.text', 'Review Needed');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display On Hold stat card', () => {
      cy.get('.stat-card.hold').within(() => {
        cy.get('.stat-label').should('contain.text', 'On Hold');
        cy.get('.stat-value').should('exist');
      });
    });
  });

  describe('Stats Grid Tests - Summary Stats', () => {
    it('should display Total Cases Triaged stat', () => {
      cy.get('.stat-card.highlight').within(() => {
        cy.get('.stat-label').should('contain.text', 'Total Cases Triaged');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display High Priority stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'High Priority').should('exist');
    });

    it('should display Pending Review stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Pending Review').should('exist');
    });

    it('should display Total Estimated Value stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Total Estimated Value').should('exist');
    });
  });

  describe('Queue Section Tests', () => {
    it('should display queue section', () => {
      cy.get('.queue-section').should('be.visible');
    });

    it('should display section header', () => {
      cy.get('.section-header').should('be.visible');
    });

    it('should display section title with badge', () => {
      cy.get('.section-title').should('contain.text', 'Case Queue');
      cy.get('.section-title .badge').should('exist');
    });
  });

  describe('Queue Tabs Tests', () => {
    it('should display queue tabs', () => {
      cy.get('.queue-tabs').should('be.visible');
    });

    it('should display Fast Track tab', () => {
      cy.get('.queue-tab').contains('Fast Track').should('exist');
    });

    it('should display Standard tab', () => {
      cy.get('.queue-tab').contains('Standard').should('exist');
    });

    it('should display Review Needed tab', () => {
      cy.get('.queue-tab').contains('Review Needed').should('exist');
    });

    it('should display On Hold tab', () => {
      cy.get('.queue-tab').contains('On Hold').should('exist');
    });

    it('should have Fast Track tab active by default', () => {
      cy.get('.queue-tab').contains('Fast Track').should('have.class', 'active');
    });

    it('should switch active tab on click', () => {
      cy.get('.queue-tab').contains('Standard').click();
      cy.get('.queue-tab').contains('Standard').should('have.class', 'active');
      cy.get('.queue-tab').contains('Fast Track').should('not.have.class', 'active');
    });

    it('should display tab counts', () => {
      cy.get('.queue-tab .count').should('have.length.at.least', 4);
    });
  });

  describe('Queue Content Tests', () => {
    it('should display fast track queue content by default', () => {
      cy.get('#queue-fast_track').should('be.visible');
    });

    it('should hide other queue contents by default', () => {
      cy.get('#queue-standard').should('not.be.visible');
      cy.get('#queue-review_needed').should('not.be.visible');
      cy.get('#queue-hold').should('not.be.visible');
    });

    it('should show standard queue when tab clicked', () => {
      cy.get('.queue-tab').contains('Standard').click();
      cy.get('#queue-standard').should('be.visible');
      cy.get('#queue-fast_track').should('not.be.visible');
    });

    it('should show review needed queue when tab clicked', () => {
      cy.get('.queue-tab').contains('Review Needed').click();
      cy.get('#queue-review_needed').should('be.visible');
    });

    it('should show hold queue when tab clicked', () => {
      cy.get('.queue-tab').contains('On Hold').click();
      cy.get('#queue-hold').should('be.visible');
    });
  });

  describe('Case Table or Empty State Tests', () => {
    it('should display either case table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.case-table').length) {
          cy.get('.case-table').should('be.visible');
        } else {
          cy.get('.empty-state').should('be.visible');
        }
      });
    });

    it('should display table headers if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.case-table').length) {
          cy.get('.case-table thead').should('contain.text', 'Priority');
          cy.get('.case-table thead').should('contain.text', 'Client');
          cy.get('.case-table thead').should('contain.text', 'Est. Value');
          cy.get('.case-table thead').should('contain.text', 'Complexity');
          cy.get('.case-table thead').should('contain.text', 'Actions');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display empty state message when no cases', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.queue-content:visible .empty-state').length) {
          cy.get('.queue-content:visible .empty-state p').should('exist');
        } else {
          cy.get('.case-table').should('be.visible');
        }
      });
    });
  });

  describe('Case Row Elements Tests', () => {
    it('should display priority stars if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.priority-stars').length) {
          cy.get('.priority-stars').first().should('be.visible');
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });

    it('should display client info if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-info').length) {
          cy.get('.client-info').first().within(() => {
            cy.get('.client-name').should('exist');
            cy.get('.client-email').should('exist');
          });
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });

    it('should display value badge if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.value-badge').length) {
          cy.get('.value-badge').first().should('be.visible');
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });

    it('should display complexity badge if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.complexity-badge').length) {
          cy.get('.complexity-badge').first().should('be.visible');
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });

    it('should display queue badge if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.queue-badge').length) {
          cy.get('.queue-badge').first().should('be.visible');
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });

    it('should display action buttons if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.action-btns').length) {
          cy.get('.action-btns').first().within(() => {
            cy.get('.action-btn.view').should('exist');
            cy.get('.action-btn.review').should('exist');
          });
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have review modal in DOM', () => {
      cy.get('#reviewModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#reviewModal').should('not.have.class', 'active');
    });

    it('should display modal header', () => {
      cy.get('#reviewModal .modal-header h2').should('contain.text', 'Review Case Triage');
    });

    it('should have star rating in modal', () => {
      cy.get('#starRating').should('exist');
      cy.get('#starRating .star').should('have.length', 5);
    });

    it('should have review notes textarea', () => {
      cy.get('#reviewNotes').should('exist');
    });

    it('should have modal footer buttons', () => {
      cy.get('#reviewModal .modal-footer .btn-secondary').should('contain.text', 'Cancel');
      cy.get('#reviewModal .modal-footer .btn-primary').should('contain.text', 'Submit Review');
    });

    it('should close modal when close button clicked', () => {
      // Open modal if there are cases, or just verify modal exists
      cy.get('body').then(($body) => {
        if ($body.find('.action-btn.review').length) {
          cy.get('.action-btn.review').first().click();
          cy.get('#reviewModal').should('have.class', 'active');
          cy.get('.modal-close').first().click();
          cy.get('#reviewModal').should('not.have.class', 'active');
        } else {
          cy.get('#reviewModal').should('exist');
        }
      });
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have showQueue function', () => {
      cy.window().should('have.property', 'showQueue');
    });

    it('should have viewAnalysis function', () => {
      cy.window().should('have.property', 'viewAnalysis');
    });

    it('should have openReviewModal function', () => {
      cy.window().should('have.property', 'openReviewModal');
    });

    it('should have closeModal function', () => {
      cy.window().should('have.property', 'closeModal');
    });

    it('should have setRating function', () => {
      cy.window().should('have.property', 'setRating');
    });

    it('should have submitReview function', () => {
      cy.window().should('have.property', 'submitReview');
    });

    it('should have refreshData function', () => {
      cy.window().should('have.property', 'refreshData');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.queue-section').should('be.visible');
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

  describe('Badge Styling Tests', () => {
    it('should have queue badge fast-track styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.queue-badge.fast-track').length) {
          cy.get('.queue-badge.fast-track').first().should('be.visible');
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });

    it('should have queue badge standard styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.queue-badge.standard').length) {
          cy.get('.queue-badge.standard').first().should('be.visible');
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });

    it('should have complexity badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.complexity-badge').length) {
          cy.get('.complexity-badge').first().should('be.visible');
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });

    it('should have value badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.value-badge').length) {
          cy.get('.value-badge').first().should('be.visible');
        } else {
          cy.get('.queue-section').should('exist');
        }
      });
    });
  });

  describe('Stat Card Styling Tests', () => {
    it('should have fast-track stat card styling', () => {
      cy.get('.stat-card.fast-track').should('exist');
    });

    it('should have standard stat card styling', () => {
      cy.get('.stat-card.standard').should('exist');
    });

    it('should have review stat card styling', () => {
      cy.get('.stat-card.review').should('exist');
    });

    it('should have hold stat card styling', () => {
      cy.get('.stat-card.hold').should('exist');
    });

    it('should have highlight stat card styling', () => {
      cy.get('.stat-card.highlight').should('exist');
    });
  });
});
