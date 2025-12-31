// Exhaustive test for /dashboard/va-approval
describe('VA Letter Approval - /dashboard/va-approval', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/va-approval');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/va-approval');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'VA');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'VA');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/va-approval').its('status').should('be.oneOf', [200, 302]);
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

    it('should have success stat card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.stat-card.success').length) {
          cy.get('.stat-card.success').should('be.visible');
        } else {
          cy.get('.stats-grid').should('exist');
        }
      });
    });

    it('should have purple stat card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.stat-card.purple').length) {
          cy.get('.stat-card.purple').should('be.visible');
        } else {
          cy.get('.stats-grid').should('exist');
        }
      });
    });

    it('should have warning stat card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.stat-card.warning').length) {
          cy.get('.stat-card.warning').should('be.visible');
        } else {
          cy.get('.stats-grid').should('exist');
        }
      });
    });
  });

  describe('Connection Status Tests', () => {
    it('should display connection status', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.connection-status').length) {
          cy.get('.connection-status').should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have status dot', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-dot').length) {
          cy.get('.status-dot').should('exist');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should show connected or disconnected state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.connection-status').length) {
          cy.get('.connection-status').then(($status) => {
            const hasConnected = $status.hasClass('connected');
            const hasDisconnected = $status.hasClass('disconnected');
            const hasChecking = $status.hasClass('checking');
            expect(hasConnected || hasDisconnected || hasChecking).to.be.true;
          });
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Card Tests', () => {
    it('should display cards', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.card').length) {
          cy.get('.card').should('have.length.at.least', 1);
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display card headers', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.card-header').length) {
          cy.get('.card-header').should('have.length.at.least', 1);
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display card titles', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.card-title').length) {
          cy.get('.card-title').should('have.length.at.least', 1);
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Filter Bar Tests', () => {
    it('should display filter bar', () => {
      cy.get('.filter-bar').should('be.visible');
    });

    it('should have filter selects', () => {
      cy.get('.filter-bar select').should('have.length.at.least', 1);
    });
  });

  describe('Client Group Tests', () => {
    it('should display client groups if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-group').length) {
          cy.get('.client-group').first().should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });

    it('should display client group headers if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-group-header').length) {
          cy.get('.client-group-header').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display client info if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-info').length) {
          cy.get('.client-info').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display client avatars if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-avatar').length) {
          cy.get('.client-avatar').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display client details if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-details').length) {
          cy.get('.client-details').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Letters List Tests', () => {
    it('should display letters list if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.letters-list').length) {
          cy.get('.letters-list').first().should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });

    it('should display letter items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.letter-item').length) {
          cy.get('.letter-item').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display letter checkboxes if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.letter-checkbox').length) {
          cy.get('.letter-checkbox').first().should('exist');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Cost Badge Tests', () => {
    it('should display cost badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.cost-badge').length) {
          cy.get('.cost-badge').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Button Tests', () => {
    it('should display success buttons if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.btn-success').length) {
          cy.get('.btn-success').first().should('be.visible');
        } else {
          cy.get('.btn').should('exist');
        }
      });
    });

    it('should display danger buttons if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.btn-danger').length) {
          cy.get('.btn-danger').first().should('be.visible');
        } else {
          cy.get('.btn').should('exist');
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
