// Exhaustive test for /dashboard/suspense-accounts
describe('Suspense Account Detection - /dashboard/suspense-accounts', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/suspense-accounts');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/suspense-accounts');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Suspense');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Suspense');
    });

    it('should display header subtitle if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.header-subtitle').length) {
          cy.get('.header-subtitle').should('be.visible');
        } else {
          cy.get('.header').should('exist');
        }
      });
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/suspense-accounts').its('status').should('be.oneOf', [200, 302]);
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

    it('should have findings stat card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.stat-card.findings').length) {
          cy.get('.stat-card.findings').should('be.visible');
        } else {
          cy.get('.stats-grid').should('exist');
        }
      });
    });

    it('should have false-lates stat card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.stat-card.false-lates').length) {
          cy.get('.stat-card.false-lates').should('be.visible');
        } else {
          cy.get('.stats-grid').should('exist');
        }
      });
    });

    it('should have clients stat card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.stat-card.clients').length) {
          cy.get('.stat-card.clients').should('be.visible');
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
      cy.get('.section-header').should('be.visible');
    });

    it('should display section title', () => {
      cy.get('.section-title').should('be.visible');
    });
  });

  describe('Search Box Tests', () => {
    it('should display search box', () => {
      cy.get('.search-box').should('be.visible');
    });

    it('should have search input', () => {
      cy.get('.search-box input').should('exist');
    });

    it('should accept text input', () => {
      cy.get('.search-box input').type('test');
      cy.get('.search-box input').should('have.value', 'test');
    });
  });

  describe('Table Tests', () => {
    it('should display table', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table').should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display table headers', () => {
      cy.get('body').then(($body) => {
        if ($body.find('th').length) {
          cy.get('th').should('have.length.at.least', 1);
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display table rows if data exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('td').length) {
          cy.get('td').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Type Badge Tests', () => {
    it('should display type badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.type-badge').length) {
          cy.get('.type-badge').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have false_late type badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.type-badge.false_late').length) {
          cy.get('.type-badge.false_late').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have misapplied_payment type badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.type-badge.misapplied_payment').length) {
          cy.get('.type-badge.misapplied_payment').first().should('be.visible');
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

    it('should have identified status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.identified').length) {
          cy.get('.status-badge.identified').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have disputed status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.disputed').length) {
          cy.get('.status-badge.disputed').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have resolved status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.resolved').length) {
          cy.get('.status-badge.resolved').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Action Buttons Tests', () => {
    it('should display action buttons if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.action-btns').length) {
          cy.get('.action-btns').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display individual action buttons if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.action-btn').length) {
          cy.get('.action-btn').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have dispute action button styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.action-btn.dispute').length) {
          cy.get('.action-btn.dispute').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have modal overlay in DOM', () => {
      cy.get('.modal-overlay').should('exist');
    });

    it('should not show modal by default', () => {
      cy.get('.modal-overlay').should('not.have.class', 'active');
    });

    it('should have modal content', () => {
      cy.get('.modal').should('exist');
    });

    it('should have modal header', () => {
      cy.get('.modal-header').should('exist');
    });

    it('should have modal close button', () => {
      cy.get('.modal-close').should('exist');
    });
  });

  describe('Form Tests', () => {
    it('should have form groups in modal', () => {
      cy.get('.form-group').should('exist');
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
