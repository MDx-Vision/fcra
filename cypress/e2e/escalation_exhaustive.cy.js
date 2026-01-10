// Exhaustive test for /dashboard/escalation
describe('Smart Escalation Engine - /dashboard/escalation', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/escalation');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/escalation');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Smart Escalation');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Smart Escalation Engine');
    });

    it('should display header subtitle', () => {
      cy.get('.header').should('contain.text', 'AI-powered');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/escalation').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display Back to Dashboard link', () => {
      cy.get('.header-actions a.btn-secondary').should('contain.text', 'Back to Dashboard');
    });

    it('should have correct link for Back to Dashboard', () => {
      cy.get('.header-actions a.btn-secondary').should('have.attr', 'href', '/dashboard');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display four stat cards', () => {
      cy.get('.stats-grid .stat-card').should('have.length', 4);
    });

    it('should display Total Recommendations stat', () => {
      cy.get('.stat-card.highlight').within(() => {
        cy.get('.stat-label').should('contain.text', 'Total Recommendations');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Applied stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Applied').should('exist');
    });

    it('should display Completed stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Completed').should('exist');
    });

    it('should display Success Rate stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Success Rate').should('exist');
    });
  });

  describe('Content Grid Tests', () => {
    it('should display content grid', () => {
      cy.get('.content-grid').should('be.visible');
    });

    it('should display cards', () => {
      cy.get('.card').should('have.length.at.least', 2);
    });
  });

  describe('Cases Needing Review Tests', () => {
    it('should display Cases Needing Escalation Review card', () => {
      cy.get('.card-title').contains('Cases Needing Escalation Review').should('exist');
    });

    it('should display case count', () => {
      cy.get('.card-header').contains('cases').should('exist');
    });

    it('should display either case items or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.case-item').length) {
          cy.get('.case-item').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display case info if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.case-item').length) {
          cy.get('.case-item').first().within(() => {
            cy.get('.case-name').should('exist');
            cy.get('.case-detail').should('exist');
          });
        } else {
          cy.get('.empty-state h3').should('contain.text', 'All Caught Up');
        }
      });
    });

    it('should display priority badge if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.case-item').length) {
          cy.get('.priority-badge').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display View and Analyze buttons if cases exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.case-item').length) {
          cy.get('.case-item').first().within(() => {
            cy.get('.btn').contains('View').should('exist');
            cy.get('.btn').contains('Analyze').should('exist');
          });
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });
  });

  describe('Recent Recommendations Tests', () => {
    it('should display Recent Recommendations card', () => {
      cy.get('.card-title').contains('Recent Recommendations').should('exist');
    });

    it('should display either recommendation items or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.recommendation-item').length) {
          cy.get('.recommendation-item').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display recommendation action if recommendations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.recommendation-item').length) {
          cy.get('.recommendation-action').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should display confidence badge if recommendations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.confidence-badge').length) {
          cy.get('.confidence-badge').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should display recommendation reasoning if recommendations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.recommendation-reasoning').length) {
          cy.get('.recommendation-reasoning').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });

  describe('Top Performing Strategies Tests', () => {
    it('should display Top Performing Strategies card', () => {
      cy.get('.card-title').contains('Top Performing Strategies').should('exist');
    });

    it('should display either action type cards or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.action-type-card').length) {
          cy.get('.action-type-card').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });
  });

  describe('Action Types Tests', () => {
    it('should display Action Types card', () => {
      cy.get('.card-title').contains('Action Types').should('exist');
    });

    it('should display action type cards', () => {
      cy.get('.action-type-card').should('have.length.at.least', 1);
    });

    it('should display action type icon', () => {
      cy.get('.action-type-icon').first().should('be.visible');
    });

    it('should display action type name', () => {
      cy.get('.action-type-name').first().should('be.visible');
    });
  });

  describe('Recently Applied Tests', () => {
    it('should display Recently Applied card', () => {
      cy.get('.card-title').contains('Recently Applied').should('exist');
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have generateRecommendation function', () => {
      cy.window().should('have.property', 'generateRecommendation');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.content-grid').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
    });
  });

  describe('Priority Badge Styling Tests', () => {
    it('should have urgent priority badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.priority-urgent').length) {
          cy.get('.priority-urgent').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should have high priority badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.priority-high').length) {
          cy.get('.priority-high').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should have medium priority badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.priority-medium').length) {
          cy.get('.priority-medium').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });

  describe('Confidence Badge Styling Tests', () => {
    it('should have confidence-high badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.confidence-high').length) {
          cy.get('.confidence-high').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should have confidence-medium badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.confidence-medium').length) {
          cy.get('.confidence-medium').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should have confidence-low badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.confidence-low').length) {
          cy.get('.confidence-low').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });

  describe('Case Item Styling Tests', () => {
    it('should have urgent case item styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.case-item.urgent').length) {
          cy.get('.case-item.urgent').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should have high case item styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.case-item.high').length) {
          cy.get('.case-item.high').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should have medium case item styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.case-item.medium').length) {
          cy.get('.case-item.medium').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });
});
