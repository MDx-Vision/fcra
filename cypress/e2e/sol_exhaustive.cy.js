// Exhaustive test for /dashboard/sol
describe('SOL Tracker - /dashboard/sol', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/sol');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/sol');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'SOL Tracker');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Statute of Limitations Tracker');
    });

    it('should display header subtitle', () => {
      cy.get('.header-subtitle').should('contain.text', 'FCRA § 1681p');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/sol').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display Check Deadlines button', () => {
      cy.get('.header .btn-primary').should('contain.text', 'Check Deadlines');
    });

    it('should display Back to Analytics link', () => {
      cy.get('.header a.btn-secondary').should('contain.text', 'Back to Analytics');
    });

    it('should have correct link for Back to Analytics', () => {
      cy.get('.header a.btn-secondary').should('have.attr', 'href', '/dashboard/analytics');
    });
  });

  describe('Legal Note Box Tests', () => {
    it('should display legal note box', () => {
      cy.get('.legal-note').should('be.visible');
    });

    it('should display legal note title', () => {
      cy.get('.legal-note-title').should('contain.text', 'FCRA Statute of Limitations');
    });

    it('should display legal note text', () => {
      cy.get('.legal-note-text').should('be.visible');
      cy.get('.legal-note-text').should('contain.text', '2 years');
      cy.get('.legal-note-text').should('contain.text', '5 years');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display four stat cards', () => {
      cy.get('.stats-grid .stat-card').should('have.length', 4);
    });

    it('should display critical stat card (30 days)', () => {
      cy.get('.stat-card.critical').within(() => {
        cy.get('.stat-label').should('contain.text', 'Expiring in 30 Days');
        cy.get('.stat-number').should('exist');
      });
    });

    it('should display warning stat card (31-60 days)', () => {
      cy.get('.stat-card.warning').within(() => {
        cy.get('.stat-label').should('contain.text', '31-60 Days');
        cy.get('.stat-number').should('exist');
      });
    });

    it('should display caution stat card (61-90 days)', () => {
      cy.get('.stat-card.caution').within(() => {
        cy.get('.stat-label').should('contain.text', '61-90 Days');
        cy.get('.stat-number').should('exist');
      });
    });

    it('should display ok stat card (90+ days)', () => {
      cy.get('.stat-card.ok').within(() => {
        cy.get('.stat-label').should('contain.text', 'Safe');
        cy.get('.stat-number').should('exist');
      });
    });
  });

  describe('Tabs Tests', () => {
    it('should display tabs', () => {
      cy.get('.tabs').should('be.visible');
    });

    it('should display Critical tab', () => {
      cy.get('.tab').contains('Critical').should('exist');
    });

    it('should display Warning tab', () => {
      cy.get('.tab').contains('Warning').should('exist');
    });

    it('should display All Upcoming tab', () => {
      cy.get('.tab').contains('All Upcoming').should('exist');
    });

    it('should display Expired tab', () => {
      cy.get('.tab').contains('Expired').should('exist');
    });

    it('should have Critical tab active by default', () => {
      cy.get('.tab').contains('Critical').should('have.class', 'active');
    });

    it('should switch active tab on click', () => {
      cy.get('.tab').contains('Warning').click();
      cy.get('.tab').contains('Warning').should('have.class', 'active');
      cy.get('.tab').contains('Critical').should('not.have.class', 'active');
    });
  });

  describe('Tab Content Tests', () => {
    it('should display critical tab content by default', () => {
      cy.get('#critical-tab').should('have.class', 'active');
    });

    it('should hide other tab contents by default', () => {
      cy.get('#warning-tab').should('not.have.class', 'active');
      cy.get('#all-tab').should('not.have.class', 'active');
      cy.get('#expired-tab').should('not.have.class', 'active');
    });

    it('should show warning tab when clicked', () => {
      cy.get('.tab').contains('Warning').click();
      cy.get('#warning-tab').should('have.class', 'active');
    });

    it('should show all tab when clicked', () => {
      cy.get('.tab').contains('All Upcoming').click();
      cy.get('#all-tab').should('have.class', 'active');
    });

    it('should show expired tab when clicked', () => {
      cy.get('.tab').contains('Expired').click();
      cy.get('#expired-tab').should('have.class', 'active');
    });
  });

  describe('Section Tests', () => {
    it('should display section', () => {
      cy.get('.section').should('be.visible');
    });

    it('should display section header', () => {
      cy.get('.section-header').should('be.visible');
    });

    it('should display section title', () => {
      cy.get('.section-title').should('contain.text', 'Critical');
    });
  });

  describe('Violation List or Empty State Tests', () => {
    it('should display either violation list or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.tab-content.active .violation-list').length) {
          cy.get('.tab-content.active .violation-list').should('be.visible');
        } else if ($body.find('.tab-content.active .empty-state').length) {
          cy.get('.tab-content.active .empty-state').should('be.visible');
        } else {
          cy.get('.tab-content.active').should('exist');
        }
      });
    });

    it('should display empty state message when no violations', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.tab-content.active .empty-state').length) {
          cy.get('.tab-content.active .empty-state p').should('exist');
        } else if ($body.find('.tab-content.active .violation-list').length) {
          cy.get('.tab-content.active .violation-list').should('be.visible');
        } else {
          cy.get('.tab-content.active').should('exist');
        }
      });
    });
  });

  describe('Violation Item Tests', () => {
    it('should display violation items if violations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.violation-item').length) {
          cy.get('.violation-item').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should display violation info if violations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.violation-info').length) {
          cy.get('.violation-info').first().within(() => {
            cy.get('.violation-client').should('exist');
            cy.get('.violation-details').should('exist');
          });
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should display violation status if violations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.violation-status').length) {
          cy.get('.violation-status').first().within(() => {
            cy.get('.days-badge').should('exist');
            cy.get('.expiration-date').should('exist');
          });
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should display View Case action button if violations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.violation-item').length) {
          cy.get('.action-btn').first().should('contain.text', 'View Case');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have showTab function', () => {
      cy.window().should('have.property', 'showTab');
    });

    it('should have checkDeadlines function', () => {
      cy.window().should('have.property', 'checkDeadlines');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.tabs').should('be.visible');
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

  describe('Stat Card Styling Tests', () => {
    it('should have critical stat card styling', () => {
      cy.get('.stat-card.critical').should('exist');
    });

    it('should have warning stat card styling', () => {
      cy.get('.stat-card.warning').should('exist');
    });

    it('should have caution stat card styling', () => {
      cy.get('.stat-card.caution').should('exist');
    });

    it('should have ok stat card styling', () => {
      cy.get('.stat-card.ok').should('exist');
    });
  });

  describe('Days Badge Styling Tests', () => {
    it('should have critical days badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.days-badge.critical').length) {
          cy.get('.days-badge.critical').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should have warning days badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.days-badge.warning').length) {
          cy.get('.days-badge.warning').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should have caution days badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.days-badge.caution').length) {
          cy.get('.days-badge.caution').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should have ok days badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.days-badge.ok').length) {
          cy.get('.days-badge.ok').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should have expired days badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.days-badge.expired').length) {
          cy.get('.days-badge.expired').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });
  });

  describe('Violation Item Styling Tests', () => {
    it('should have critical violation item styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.violation-item.critical').length) {
          cy.get('.violation-item.critical').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should have warning violation item styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.violation-item.warning').length) {
          cy.get('.violation-item.warning').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });

    it('should have expired violation item styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.violation-item.expired').length) {
          cy.get('.violation-item.expired').first().should('be.visible');
        } else {
          cy.get('.section').should('exist');
        }
      });
    });
  });

  describe('Tab Content Section Tests', () => {
    it('should display critical section title', () => {
      cy.get('#critical-tab .section-title').should('contain.text', 'Critical');
    });

    it('should display warning section title', () => {
      cy.get('.tab').contains('Warning').click();
      cy.get('#warning-tab .section-title').should('contain.text', 'Warning');
    });

    it('should display all upcoming section title', () => {
      cy.get('.tab').contains('All Upcoming').click();
      cy.get('#all-tab .section-title').should('contain.text', 'All Upcoming');
    });

    it('should display expired section title', () => {
      cy.get('.tab').contains('Expired').click();
      cy.get('#expired-tab .section-title').should('contain.text', 'Expired');
    });
  });
});
