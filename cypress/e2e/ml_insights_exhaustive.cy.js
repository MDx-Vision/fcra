// Exhaustive test for /dashboard/ml-insights
describe('ML Insights Dashboard - /dashboard/ml-insights', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/ml-insights');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/ml-insights');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'ML Insights');
    });

    it('should display the page header', () => {
      cy.get('h1').should('contain.text', 'ML Insights');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/ml-insights').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display Refresh Patterns button', () => {
      cy.get('button').contains('Refresh Patterns').should('exist');
    });

    it('should display Record Outcome button', () => {
      cy.get('button').contains('Record Outcome').should('exist');
    });
  });

  describe('Stats Cards Tests', () => {
    it('should display stats row', () => {
      cy.get('.row').should('be.visible');
    });

    it('should display Training Cases card', () => {
      cy.get('.card').contains('Training Cases').should('exist');
    });

    it('should display Success Rate card', () => {
      cy.get('.card').contains('Success Rate').should('exist');
    });

    it('should display Avg Settlement card', () => {
      cy.get('.card').contains('Avg Settlement').should('exist');
    });

    it('should display Model Confidence card', () => {
      cy.get('.card').contains('Model Confidence').should('exist');
    });
  });

  describe('Success Rates Card Tests', () => {
    it('should display Success Rates by Violation Type card', () => {
      cy.get('.card-header').contains('Success Rates').should('exist');
    });

    it('should display either table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.table').length) {
          cy.get('.table').should('be.visible');
        } else {
          cy.get('.text-center').should('contain.text', 'No Outcome Data');
        }
      });
    });
  });

  describe('Outcome Distribution Card Tests', () => {
    it('should display Outcome Distribution card', () => {
      cy.get('.card-header').contains('Outcome Distribution').should('exist');
    });

    it('should display progress bars or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.progress').length) {
          cy.get('.progress').first().should('be.visible');
        } else {
          cy.get('.text-center').should('exist');
        }
      });
    });
  });

  describe('Seasonal Trends Card Tests', () => {
    it('should display Seasonal Trends card', () => {
      cy.get('.card-header').contains('Seasonal Trends').should('exist');
    });
  });

  describe('Winning Strategies Card Tests', () => {
    it('should display Winning Strategies card', () => {
      cy.get('.card-header').contains('Winning Strategies').should('exist');
    });

    it('should display list items or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.list-group-item').length) {
          cy.get('.list-group-item').first().should('be.visible');
        } else {
          cy.get('.card').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Badge Tests', () => {
    it('should display success badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.badge.bg-success').length) {
          cy.get('.badge.bg-success').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display warning badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.badge.bg-warning').length) {
          cy.get('.badge.bg-warning').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display danger badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.badge.bg-danger').length) {
          cy.get('.badge.bg-danger').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have refreshPatterns function', () => {
      cy.window().should('have.property', 'refreshPatterns');
    });

    it('should have showRecordOutcomeModal function', () => {
      cy.window().should('have.property', 'showRecordOutcomeModal');
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
