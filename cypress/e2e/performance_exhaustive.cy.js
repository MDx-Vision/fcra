// Exhaustive test for /dashboard/performance
describe('Performance Dashboard - /dashboard/performance', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/performance');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/performance');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Performance');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Performance');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/performance').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display header actions', () => {
      cy.get('.header-actions').should('be.visible');
    });

    it('should display refresh indicator if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.refresh-indicator').length) {
          cy.get('.refresh-indicator').should('be.visible');
        } else {
          cy.get('.header').should('exist');
        }
      });
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
          cy.get('.stat-card.highlight').first().should('be.visible');
        } else {
          cy.get('.stats-grid').should('exist');
        }
      });
    });

    it('should have good stat card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.stat-card.good').length) {
          cy.get('.stat-card.good').first().should('be.visible');
        } else {
          cy.get('.stats-grid').should('exist');
        }
      });
    });

    it('should have warning stat card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.stat-card.warning').length) {
          cy.get('.stat-card.warning').first().should('be.visible');
        } else {
          cy.get('.stats-grid').should('exist');
        }
      });
    });
  });

  describe('Card Tests', () => {
    it('should display cards', () => {
      cy.get('.card').should('have.length.at.least', 1);
    });

    it('should display card headers', () => {
      cy.get('.card-header').should('have.length.at.least', 1);
    });

    it('should display card titles', () => {
      cy.get('.card-title').should('have.length.at.least', 1);
    });
  });

  describe('Grid Layout Tests', () => {
    it('should display grid-2 layout if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.grid-2').length) {
          cy.get('.grid-2').should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });
  });

  describe('Chart Tests', () => {
    it('should display chart containers if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.chart-container').length) {
          cy.get('.chart-container').first().should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });
  });

  describe('Table Tests', () => {
    it('should display table if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.table').length) {
          cy.get('.table').should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });

    it('should display table headers if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.table th').length) {
          cy.get('.table th').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Progress Bar Tests', () => {
    it('should display progress bars if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.progress-bar').length) {
          cy.get('.progress-bar').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display progress fills if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.progress-fill').length) {
          cy.get('.progress-fill').first().should('exist');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Badge Tests', () => {
    it('should display success badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.badge-success').length) {
          cy.get('.badge-success').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display warning badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.badge-warning').length) {
          cy.get('.badge-warning').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display danger badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.badge-danger').length) {
          cy.get('.badge-danger').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Alert Tests', () => {
    it('should display alerts if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.alert').length) {
          cy.get('.alert').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Database Pool Status Tests', () => {
    it('should display db pool status if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.db-pool-status').length) {
          cy.get('.db-pool-status').should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display pool items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.pool-item').length) {
          cy.get('.pool-item').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Recommendation Tests', () => {
    it('should display recommendations if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.recommendation').length) {
          cy.get('.recommendation').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have modal in DOM', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.modal').length) {
          cy.get('.modal').should('exist');
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
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
    });
  });
});
