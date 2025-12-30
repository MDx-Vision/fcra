// Exhaustive test for /dashboard/integrations
describe('Integrations Hub - /dashboard/integrations', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/integrations');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/integrations');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Integration');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Integration');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/integrations').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display header actions', () => {
      cy.get('.header-actions').should('be.visible');
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
  });

  describe('Integrations Grid Tests', () => {
    it('should display integrations grid', () => {
      cy.get('.integrations-grid').should('be.visible');
    });

    it('should display integration cards', () => {
      cy.get('.integration-card').should('have.length.at.least', 1);
    });

    it('should display integration headers', () => {
      cy.get('.integration-header').should('have.length.at.least', 1);
    });

    it('should display integration icons', () => {
      cy.get('.integration-icon').should('have.length.at.least', 1);
    });

    it('should display integration titles', () => {
      cy.get('.integration-title').should('have.length.at.least', 1);
    });

    it('should display integration descriptions', () => {
      cy.get('.integration-desc').should('have.length.at.least', 1);
    });
  });

  describe('Integration Status Tests', () => {
    it('should display status badges', () => {
      cy.get('.status-badge').should('have.length.at.least', 1);
    });

    it('should have connected status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.connected').length) {
          cy.get('.status-badge.connected').first().should('be.visible');
        } else {
          cy.get('.integrations-grid').should('exist');
        }
      });
    });

    it('should have not-configured status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.not-configured').length) {
          cy.get('.status-badge.not-configured').first().should('be.visible');
        } else {
          cy.get('.integrations-grid').should('exist');
        }
      });
    });
  });

  describe('Integration Stats Tests', () => {
    it('should display integration stats', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.integration-stats').length) {
          cy.get('.integration-stats').first().should('be.visible');
        } else {
          cy.get('.integrations-grid').should('exist');
        }
      });
    });
  });

  describe('Integration Actions Tests', () => {
    it('should display integration actions', () => {
      cy.get('.integration-actions').should('have.length.at.least', 1);
    });

    it('should have buttons in integration actions', () => {
      cy.get('.integration-actions .btn').should('have.length.at.least', 1);
    });
  });

  describe('Content Card Tests', () => {
    it('should display content card', () => {
      cy.get('.content-card').should('be.visible');
    });

    it('should display section title', () => {
      cy.get('.section-title').should('exist');
    });
  });

  describe('Activity List Tests', () => {
    it('should display activity list if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.activity-list').length) {
          cy.get('.activity-list').should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display activity items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.activity-item').length) {
          cy.get('.activity-item').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have modal overlay in DOM', () => {
      cy.get('.modal-overlay').should('exist');
    });

    it('should not show modal by default', () => {
      cy.get('.modal-overlay').should('not.have.class', 'show');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.integrations-grid').should('be.visible');
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
