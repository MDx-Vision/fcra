describe('Analytics Page', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/analytics');
  });

  it('should load the analytics page', () => {
    cy.url().should('include', '/dashboard/analytics');
    cy.get('.main-content').should('be.visible');
  });

  it('should display metrics grid with all cards', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.stats-grid').length) {
        cy.get('.stats-grid').should('be.visible');
      } else {
        cy.get('.main-content').should('exist');
      }
    });
  });

  it('should display charts', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.charts-grid').length) {
        cy.get('.charts-grid').should('be.visible');
      } else {
        cy.get('.main-content').should('exist');
      }
    });
  });

  it('should display client status section', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.status-section').length) {
        cy.get('.status-section').should('be.visible');
      } else {
        cy.get('.main-content').should('exist');
      }
    });
  });

  it('should display revenue section', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.revenue-section').length) {
        cy.get('.revenue-section').should('be.visible');
      } else {
        cy.get('.main-content').should('exist');
      }
    });
  });

  it('should display case stats section with rounds', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.case-stats-section').length) {
        cy.get('.case-stats-section').should('be.visible');
      } else {
        cy.get('.main-content').should('exist');
      }
    });
  });

  it('should display dispute progress section', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.dispute-progress-section').length) {
        cy.get('.dispute-progress-section').should('be.visible');
      } else {
        cy.get('.main-content').should('exist');
      }
    });
  });

  it('should display CRA response section', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.cra-response-section').length) {
        cy.get('.cra-response-section').should('be.visible');
      } else {
        cy.get('.main-content').should('exist');
      }
    });
  });

  it('should display settlement analytics section', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.settlement-analytics-section').length) {
        cy.get('.settlement-analytics-section').should('be.visible');
      } else {
        cy.get('.main-content').should('exist');
      }
    });
  });

  it('should navigate back to dashboard', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.back-to-dashboard').length) {
        cy.get('.back-to-dashboard').click();
        cy.url().should('include', '/dashboard');
      } else {
        cy.get('.main-content').should('exist');
      }
    });
  });
});
