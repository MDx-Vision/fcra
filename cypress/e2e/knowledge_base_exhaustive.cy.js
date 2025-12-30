// Exhaustive test for /dashboard/knowledge-base
describe('Legal Strategy Knowledge Base - /dashboard/knowledge-base', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/knowledge-base');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/knowledge-base');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Knowledge');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Knowledge');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/knowledge-base').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Search Box Tests', () => {
    it('should display search box', () => {
      cy.get('.search-box').should('be.visible');
    });

    it('should have search input', () => {
      cy.get('.search-box input').should('exist');
    });

    it('should accept text input in search', () => {
      cy.get('.search-box input').type('FCRA');
      cy.get('.search-box input').should('have.value', 'FCRA');
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
      cy.get('.tab').eq(1).click();
      cy.get('.tab').eq(1).should('have.class', 'active');
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

  describe('Content Grid Tests', () => {
    it('should display content grid', () => {
      cy.get('.content-grid').should('be.visible');
    });

    it('should display cards', () => {
      cy.get('.card').should('have.length.at.least', 1);
    });
  });

  describe('Card Elements Tests', () => {
    it('should display card headers', () => {
      cy.get('.card-header').should('have.length.at.least', 1);
    });

    it('should display card icons', () => {
      cy.get('.card-icon').should('have.length.at.least', 1);
    });

    it('should display card titles', () => {
      cy.get('.card-title').should('have.length.at.least', 1);
    });

    it('should display card content', () => {
      cy.get('.card-content').should('have.length.at.least', 1);
    });
  });

  describe('Highlight Box Tests', () => {
    it('should display highlight boxes if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.highlight-box').length) {
          cy.get('.highlight-box').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });

  describe('Statute Reference Tests', () => {
    it('should display statute references if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.statute-ref').length) {
          cy.get('.statute-ref').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });

  describe('Timeline Tests', () => {
    it('should display timeline items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.timeline-item').length) {
          cy.get('.timeline-item').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should display timeline days badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.timeline-days').length) {
          cy.get('.timeline-days').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });

  describe('Metro2 Code Tests', () => {
    it('should display metro2 codes if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.metro2-code').length) {
          cy.get('.metro2-code').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });

  describe('Quick Reference Table Tests', () => {
    it('should display quick reference table if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.quick-ref-table').length) {
          cy.get('.quick-ref-table').should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });

  describe('Escalation Path Tests', () => {
    it('should display escalation path if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.escalation-path').length) {
          cy.get('.escalation-path').should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });

    it('should display escalation steps if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.escalation-step').length) {
          cy.get('.escalation-step').first().should('be.visible');
        } else {
          cy.get('.content-grid').should('exist');
        }
      });
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.content-grid').should('be.visible');
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
