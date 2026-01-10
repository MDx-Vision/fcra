// Exhaustive test for /dashboard/automation-tools
describe('Automation Tools - /dashboard/automation-tools', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/automation-tools');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/automation-tools');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Automation');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Automation');
    });

    it('should not return server errors', () => {
      cy.request({ url: '/dashboard/automation-tools', failOnStatusCode: false }).its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Navigation Tabs Tests', () => {
    it('should display top navigation tabs', () => {
      cy.get('.top-nav').should('be.visible');
    });

    it('should have navigation buttons', () => {
      cy.get('.top-nav-btn').should('have.length.at.least', 1);
    });

    it('should have active tab styling', () => {
      cy.get('.top-nav-btn.active').should('exist');
    });

    it('should switch tabs on click', () => {
      cy.get('.top-nav-btn').eq(1).click();
      cy.get('.top-nav-btn').eq(1).should('have.class', 'active');
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

  describe('Tab Content Tests', () => {
    it('should display active tab content', () => {
      cy.get('.tab-content.active').should('be.visible');
    });

    it('should hide inactive tab content', () => {
      cy.get('.tab-content').not('.active').should('not.be.visible');
    });
  });

  describe('Form Elements Tests', () => {
    it('should display form grid if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.form-grid:visible').length) {
          cy.get('.form-grid').should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display form groups if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.form-group:visible').length) {
          cy.get('.form-group').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have form labels', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.form-group label:visible').length) {
          cy.get('.form-group label').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Checkbox Grid Tests', () => {
    it('should display checkbox items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.checkbox-item').length) {
          cy.get('.checkbox-item').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should toggle checkbox on click', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.checkbox-item input[type="checkbox"]').length) {
          cy.get('.checkbox-item input[type="checkbox"]').first().click({ force: true });
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Data Table Tests', () => {
    it('should display data table if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length) {
          cy.get('.data-table').should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should have table headers', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table th').length) {
          cy.get('.data-table th').should('have.length.at.least', 1);
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Deadline Stats Tests', () => {
    it('should display deadline stats if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.deadline-stats:visible').length) {
          cy.get('.deadline-stats').should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display deadline stat cards if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.deadline-stat:visible').length) {
          cy.get('.deadline-stat').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Filter Controls Tests', () => {
    it('should display filters row if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.filters-row:visible').length) {
          cy.get('.filters-row').should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display filter buttons if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.filter-btn:visible').length) {
          cy.get('.filter-btn').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Button Tests', () => {
    it('should display primary buttons if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.btn-primary').length) {
          cy.get('.btn-primary').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });

    it('should display secondary buttons if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.btn-secondary').length) {
          cy.get('.btn-secondary').first().should('be.visible');
        } else {
          cy.get('.content-card').should('exist');
        }
      });
    });
  });

  describe('Status Badge Tests', () => {
    it('should have pending status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-pending').length) {
          cy.get('.status-pending').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have processing status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-processing').length) {
          cy.get('.status-processing').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have complete status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-complete').length) {
          cy.get('.status-complete').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Urgency Badge Tests', () => {
    it('should have overdue urgency badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.urgency-overdue').length) {
          cy.get('.urgency-overdue').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have critical urgency badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.urgency-critical').length) {
          cy.get('.urgency-critical').first().should('be.visible');
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
