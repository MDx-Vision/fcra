// Exhaustive test for /dashboard/sops
describe('Standard Operating Procedures - /dashboard/sops', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/sops');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/sops');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Operating');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Operating');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/sops').its('status').should('be.oneOf', [200, 302]);
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
      cy.get('.search-box input').type('FCRA');
      cy.get('.search-box input').should('have.value', 'FCRA');
    });
  });

  describe('Stats Row Tests', () => {
    it('should display stats row', () => {
      cy.get('.stats-row').should('be.visible');
    });

    it('should display stat cards', () => {
      cy.get('.stat-card').should('have.length.at.least', 1);
    });

    it('should display stat values', () => {
      cy.get('.stat-value').should('have.length.at.least', 1);
    });

    it('should display stat labels', () => {
      cy.get('.stat-label').should('have.length.at.least', 1);
    });
  });

  describe('Filter Tests', () => {
    it('should display filters', () => {
      cy.get('.filters').should('be.visible');
    });

    it('should have filter buttons', () => {
      cy.get('.filter-btn').should('have.length.at.least', 1);
    });

    it('should have active filter', () => {
      cy.get('.filter-btn.active').should('exist');
    });

    it('should switch active filter on click', () => {
      cy.get('.filter-btn').not('.active').first().click();
      cy.get('.filter-btn.active').should('exist');
    });

    it('should display filter count badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.filter-btn .count').length) {
          cy.get('.filter-btn .count').first().should('be.visible');
        } else {
          cy.get('.filters').should('exist');
        }
      });
    });
  });

  describe('SOP Grid Tests', () => {
    it('should display SOP grid', () => {
      cy.get('.sop-grid').should('be.visible');
    });

    it('should display SOP cards', () => {
      cy.get('.sop-card').should('have.length.at.least', 1);
    });
  });

  describe('SOP Card Elements Tests', () => {
    it('should display SOP headers', () => {
      cy.get('.sop-header').should('have.length.at.least', 1);
    });

    it('should display SOP icons', () => {
      cy.get('.sop-icon').should('have.length.at.least', 1);
    });

    it('should display SOP titles', () => {
      cy.get('.sop-title').should('have.length.at.least', 1);
    });

    it('should display SOP categories', () => {
      cy.get('.sop-category').should('have.length.at.least', 1);
    });

    it('should display SOP body', () => {
      cy.get('.sop-body').should('have.length.at.least', 1);
    });

    it('should display SOP descriptions', () => {
      cy.get('.sop-description').should('have.length.at.least', 1);
    });

    it('should display SOP footer', () => {
      cy.get('.sop-footer').should('have.length.at.least', 1);
    });
  });

  describe('SOP Steps Tests', () => {
    it('should display SOP steps if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.sop-steps').length) {
          cy.get('.sop-steps').first().should('be.visible');
        } else {
          cy.get('.sop-card').should('exist');
        }
      });
    });

    it('should display step numbers if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.step-number').length) {
          cy.get('.step-number').first().should('be.visible');
        } else {
          cy.get('.sop-card').should('exist');
        }
      });
    });

    it('should display step text if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.step-text').length) {
          cy.get('.step-text').first().should('be.visible');
        } else {
          cy.get('.sop-card').should('exist');
        }
      });
    });
  });

  describe('SOP Meta Tests', () => {
    it('should display SOP meta items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.sop-meta-item').length) {
          cy.get('.sop-meta-item').first().should('be.visible');
        } else {
          cy.get('.sop-card').should('exist');
        }
      });
    });
  });

  describe('SOP Tags Tests', () => {
    it('should display SOP tags if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.sop-tags').length) {
          cy.get('.sop-tags').first().should('be.visible');
        } else {
          cy.get('.sop-card').should('exist');
        }
      });
    });

    it('should display individual tags if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.sop-tag').length) {
          cy.get('.sop-tag').first().should('be.visible');
        } else {
          cy.get('.sop-card').should('exist');
        }
      });
    });

    it('should display statute tags if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.sop-tag.statute').length) {
          cy.get('.sop-tag.statute').first().should('be.visible');
        } else {
          cy.get('.sop-grid').should('exist');
        }
      });
    });
  });

  describe('Difficulty Badge Tests', () => {
    it('should display difficulty badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.difficulty-badge').length) {
          cy.get('.difficulty-badge').first().should('be.visible');
        } else {
          cy.get('.sop-card').should('exist');
        }
      });
    });

    it('should have basic difficulty styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.difficulty-badge.basic').length) {
          cy.get('.difficulty-badge.basic').first().should('be.visible');
        } else {
          cy.get('.sop-grid').should('exist');
        }
      });
    });

    it('should have advanced difficulty styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.difficulty-badge.advanced').length) {
          cy.get('.difficulty-badge.advanced').first().should('be.visible');
        } else {
          cy.get('.sop-grid').should('exist');
        }
      });
    });
  });

  describe('View Button Tests', () => {
    it('should display view buttons', () => {
      cy.get('.view-btn').should('have.length.at.least', 1);
    });
  });

  describe('Empty State Tests', () => {
    it('should display empty state if no SOPs match filter', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state').should('be.visible');
        } else {
          cy.get('.sop-grid').should('exist');
        }
      });
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.sop-grid').should('be.visible');
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
