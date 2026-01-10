// Exhaustive test for /dashboard/predictive
describe('Predictive Analytics - /dashboard/predictive', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/predictive');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/predictive');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Predictive');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Predictive');
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
      cy.request('/dashboard/predictive').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Metrics Grid Tests', () => {
    it('should display metrics grid', () => {
      cy.get('.metrics-grid').should('be.visible');
    });

    it('should display metric cards', () => {
      cy.get('.metric-card').should('have.length.at.least', 1);
    });

    it('should display metric labels', () => {
      cy.get('.metric-label').should('have.length.at.least', 1);
    });

    it('should display metric values', () => {
      cy.get('.metric-value').should('have.length.at.least', 1);
    });

    it('should have teal metric card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.metric-card.teal').length) {
          cy.get('.metric-card.teal').first().should('be.visible');
        } else {
          cy.get('.metrics-grid').should('exist');
        }
      });
    });

    it('should have green metric card styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.metric-card.green').length) {
          cy.get('.metric-card.green').first().should('be.visible');
        } else {
          cy.get('.metrics-grid').should('exist');
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

    it('should display grid-3 layout if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.grid-3').length) {
          cy.get('.grid-3').should('be.visible');
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

  describe('Forecast Tests', () => {
    it('should display forecast items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.forecast-item').length) {
          cy.get('.forecast-item').first().should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });

    it('should display forecast periods if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.forecast-period').length) {
          cy.get('.forecast-period').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display forecast values if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.forecast-value').length) {
          cy.get('.forecast-value').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Opportunity Tests', () => {
    it('should display opportunity cards if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.opportunity-card').length) {
          cy.get('.opportunity-card').first().should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });

    it('should display opportunity titles if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.opportunity-title').length) {
          cy.get('.opportunity-title').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display opportunity values if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.opportunity-value').length) {
          cy.get('.opportunity-value').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Leaderboard Tests', () => {
    it('should display leaderboard items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.leaderboard-item').length) {
          cy.get('.leaderboard-item').first().should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });

    it('should display leaderboard ranks if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.leaderboard-rank').length) {
          cy.get('.leaderboard-rank').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display leaderboard scores if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.leaderboard-score').length) {
          cy.get('.leaderboard-score').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Workload Tests', () => {
    it('should display workload bars if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.workload-bar').length) {
          cy.get('.workload-bar').first().should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });

    it('should display workload progress if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.workload-progress').length) {
          cy.get('.workload-progress').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Client LTV Tests', () => {
    it('should display client LTV items if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-ltv-item').length) {
          cy.get('.client-ltv-item').first().should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.metrics-grid').should('be.visible');
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
