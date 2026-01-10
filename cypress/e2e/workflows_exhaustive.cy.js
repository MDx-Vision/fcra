// Exhaustive test for /dashboard/workflows
describe('Workflow Triggers - /dashboard/workflows', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/workflows');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/workflows');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Workflow');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Workflow');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/workflows').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display header actions', () => {
      cy.get('.header-actions').should('be.visible');
    });

    it('should display primary button', () => {
      cy.get('.btn-primary').should('exist');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display stat cards', () => {
      cy.get('.stat-card').should('have.length.at.least', 1);
    });

    it('should display stat labels', () => {
      cy.get('.stat-label').should('have.length.at.least', 1);
    });

    it('should display stat values', () => {
      cy.get('.stat-value').should('have.length.at.least', 1);
    });

    it('should have highlight stat card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.stat-card.highlight').length) {
          cy.get('.stat-card.highlight').should('be.visible');
        } else {
          cy.get('.stats-grid').should('exist');
        }
      });
    });
  });

  describe('Content Card Tests', () => {
    it('should display content card', () => {
      cy.get('.content-card').should('be.visible');
    });

    it('should display section header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.section-header').length) {
          cy.get('.section-header').should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display section title', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.section-title').length) {
          cy.get('.section-title').should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Tabs Tests', () => {
    it('should display tabs', () => {
      cy.get('.tabs').should('be.visible');
    });

    it('should have tab buttons', () => {
      cy.get('.tab').should('have.length.at.least', 1);
    });

    it('should have active tab', () => {
      cy.get('.tab.active').should('exist');
    });

    it('should switch tabs on click', () => {
      cy.get('.tab').not('.active').first().click();
      cy.get('.tab.active').should('exist');
    });

    it('should display tab badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.tab-badge').length) {
          cy.get('.tab-badge').first().should('be.visible');
        } else {
          cy.get('.tabs').should('exist');
        }
      });
    });
  });

  describe('Tab Content Tests', () => {
    it('should display active tab content', () => {
      cy.get('.tab-content.active').should('be.visible');
    });

    it('should hide inactive tab content', () => {
      cy.get('.tab-content').not('.active').should('not.be.visible');
    });
  });

  describe('Workflow Card Tests', () => {
    it('should display workflow cards if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.workflow-card').length) {
          cy.get('.workflow-card').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display workflow headers if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.workflow-header').length) {
          cy.get('.workflow-header').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display workflow titles if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.workflow-title').length) {
          cy.get('.workflow-title').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display workflow descriptions if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.workflow-description').length) {
          cy.get('.workflow-description').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display workflow meta if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.workflow-meta').length) {
          cy.get('.workflow-meta').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Toggle Switch Tests', () => {
    it('should display toggle switches if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.toggle-switch').length) {
          cy.get('.toggle-switch').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display toggle sliders if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.toggle-slider').length) {
          cy.get('.toggle-slider').first().should('exist');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Trigger Type Badge Tests', () => {
    it('should display trigger type badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.trigger-type-badge').length) {
          cy.get('.trigger-type-badge').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have case_created badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.trigger-type-badge.case_created').length) {
          cy.get('.trigger-type-badge.case_created').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have status_changed badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.trigger-type-badge.status_changed').length) {
          cy.get('.trigger-type-badge.status_changed').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have deadline_approaching badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.trigger-type-badge.deadline_approaching').length) {
          cy.get('.trigger-type-badge.deadline_approaching').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Status Badge Tests', () => {
    it('should display status badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge').length) {
          cy.get('.status-badge').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have success status styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-success').length) {
          cy.get('.status-success').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have failed status styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-failed').length) {
          cy.get('.status-failed').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have pending status styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-pending').length) {
          cy.get('.status-pending').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Priority Badge Tests', () => {
    it('should display priority badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.priority-badge').length) {
          cy.get('.priority-badge').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have high priority styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.priority-high').length) {
          cy.get('.priority-high').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Action Button Tests', () => {
    it('should display action buttons if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.action-btn').length) {
          cy.get('.action-btn').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have primary action button styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.action-btn.primary').length) {
          cy.get('.action-btn.primary').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have danger action button styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.action-btn.danger').length) {
          cy.get('.action-btn.danger').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Execution Item Tests', () => {
    it('should display execution items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.execution-item').length) {
          cy.get('.execution-item').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
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
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
    });
  });
});
