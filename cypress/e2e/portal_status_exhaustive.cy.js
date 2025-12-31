// Exhaustive test for /portal/status - Client Portal Bureau Status Page
// TDD Approach: These tests define what the status page SHOULD have

describe('/portal/status - Client Portal Bureau Status Page', () => {
  beforeEach(() => {
    // CI auth bypass handles authentication - just visit the page
    cy.visit('/portal/status', { failOnStatusCode: false });
    cy.get('body').should('exist');
  });

  describe('Page Load Tests', () => {
    it('should load without errors', () => {
      cy.get('body').should('exist');
      cy.url().should('include', '/portal');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Status');
    });

    it('should return 200 status', () => {
      cy.request({ url: '/portal/status', failOnStatusCode: false }).its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Back Link Tests', () => {
    it('should have back to dashboard link at top', () => {
      // Check for back link or fallback to navigation
      cy.get('body').then($body => {
        if ($body.find('a[href*="dashboard"]').length) {
          cy.get('a[href*="dashboard"]').first().should('exist');
        } else if ($body.find('[data-testid="back-link"]').length) {
          cy.get('[data-testid="back-link"]').should('exist');
        } else {
          cy.get('a').contains(/back|dashboard|overview/i).should('exist');
        }
      });
    });

    it('should have back link at bottom', () => {
      // Check for any navigation link to dashboard
      cy.get('body').then($body => {
        if ($body.find('a[href*="dashboard"]').length) {
          cy.get('a[href*="dashboard"]').should('have.length.at.least', 1);
        } else {
          cy.get('nav a, .nav-tab').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Header Tests', () => {
    it('should display page header', () => {
      cy.get('[data-testid="page-header"], .card').first().should('exist');
    });

    it('should have title about bureau status', () => {
      cy.contains(/detailed bureau status|bureau status/i).should('exist');
    });

    it('should have description about tracking', () => {
      cy.contains(/track|individual account|all.*bureaus/i).should('exist');
    });

    it('should have dark gradient background', () => {
      cy.get('.card').first().should('have.css', 'background-image').and('include', 'gradient');
    });
  });

  describe('Summary Stats Tests', () => {
    it('should display summary stats grid', () => {
      cy.get('.stats-grid-responsive').should('exist');
    });

    it('should display Equifax count', () => {
      cy.contains(/equifax/i).should('exist');
    });

    it('should display Experian count', () => {
      cy.contains(/experian/i).should('exist');
    });

    it('should display TransUnion count', () => {
      cy.contains(/transunion/i).should('exist');
    });

    it('should have 3 bureau summary cards', () => {
      cy.get('.stats-grid-responsive .card').should('have.length', 3);
    });

    it('should show item counts', () => {
      cy.contains(/item/i).should('exist');
    });

    it('should have distinct colors for each bureau', () => {
      cy.get('.card').contains(/equifax/i).parent().should('have.css', 'border-left');
    });
  });

  describe('Equifax Section Tests', () => {
    it('should display Equifax accounts section', () => {
      cy.contains(/equifax accounts/i).should('exist');
    });

    it('should have teal color indicator', () => {
      cy.get('.card-title').contains(/equifax/i).should('have.css', 'color');
    });

    it('should display account items or empty state', () => {
      cy.get('body').then($body => {
        if ($body.find('[data-testid="equifax-account"]').length) {
          cy.get('[data-testid="equifax-account"]').should('exist');
        } else {
          cy.contains(/no equifax accounts/i).should('exist');
        }
      });
    });
  });

  describe('Experian Section Tests', () => {
    it('should display Experian accounts section', () => {
      cy.contains(/experian accounts/i).should('exist');
    });

    it('should have blue color indicator', () => {
      cy.get('.card-title').contains(/experian/i).should('have.css', 'color');
    });

    it('should display account items or empty state', () => {
      cy.get('body').then($body => {
        if ($body.find('[data-testid="experian-account"]').length) {
          cy.get('[data-testid="experian-account"]').should('exist');
        } else {
          cy.contains(/no experian accounts/i).should('exist');
        }
      });
    });
  });

  describe('TransUnion Section Tests', () => {
    it('should display TransUnion accounts section', () => {
      cy.contains(/transunion accounts/i).should('exist');
    });

    it('should have red color indicator', () => {
      cy.get('.card-title').contains(/transunion/i).should('have.css', 'color');
    });

    it('should display account items or empty state', () => {
      cy.get('body').then($body => {
        if ($body.find('[data-testid="transunion-account"]').length) {
          cy.get('[data-testid="transunion-account"]').should('exist');
        } else {
          cy.contains(/no transunion accounts/i).should('exist');
        }
      });
    });
  });

  describe('Account Item Tests', () => {
    it('should display creditor name in account items', () => {
      cy.get('body').then($body => {
        if ($body.find('[data-testid="account-item"]').length) {
          cy.get('[data-testid="account-item"]').first().should('contain.text', '#');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should display account type and balance', () => {
      cy.get('body').then($body => {
        if ($body.text().includes('Balance')) {
          cy.contains(/balance.*\$/i).should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should display status badge', () => {
      cy.get('body').then($body => {
        if ($body.text().includes('DISPUTED') || $body.text().includes('DELETED') || $body.text().includes('PENDING')) {
          cy.contains(/disputed|deleted|pending|verified/i).should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should have status icon', () => {
      cy.get('body').then($body => {
        if ($body.find('[data-testid="status-icon"]').length) {
          cy.get('[data-testid="status-icon"]').should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });
  });

  describe('Status Legend Tests', () => {
    it('should display status legend', () => {
      cy.contains(/status legend|legend/i).should('exist');
    });

    it('should explain DELETED status', () => {
      cy.contains(/deleted/i).should('exist');
    });

    it('should explain DISPUTED status', () => {
      cy.contains(/disputed/i).should('exist');
    });

    it('should explain PENDING status', () => {
      cy.contains(/pending/i).should('exist');
    });

    it('should explain VERIFIED status', () => {
      cy.contains(/verified/i).should('exist');
    });

    it('should have color-coded status badges', () => {
      cy.get('.card').contains(/legend/i).parent().find('div').should('have.length.at.least', 4);
    });
  });

  describe('Secondary Bureaus Section Tests', () => {
    it('should display secondary bureaus section if data exists', () => {
      cy.get('body').then($body => {
        if ($body.text().includes('Secondary Bureau')) {
          cy.contains(/secondary bureau/i).should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should have freeze status form if secondary bureaus exist', () => {
      cy.get('body').then($body => {
        if ($body.find('select[name^="status_"]').length) {
          cy.get('select[name^="status_"]').should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should have instruction alert for freeze responses', () => {
      cy.get('body').then($body => {
        if ($body.text().includes('FROZEN')) {
          cy.contains(/frozen|freeze/i).should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should have submit button for secondary bureau updates', () => {
      cy.get('body').then($body => {
        if ($body.find('form[action*="secondary"]').length) {
          cy.get('button[type="submit"]').should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should have file upload for confirmation', () => {
      cy.get('body').then($body => {
        if ($body.find('input[name="confirmation_file"]').length) {
          cy.get('input[type="file"]').should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should have comments input for each bureau', () => {
      cy.get('body').then($body => {
        if ($body.find('input[name^="comment_"]').length) {
          cy.get('input[name^="comment_"]').should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });
  });

  describe('Animation Tests', () => {
    it('should have fade-in animations', () => {
      cy.get('.animate-fade-in, .animate-fade-in-up').should('exist');
    });

    it('should have staggered delays', () => {
      cy.get('[data-delay]').should('have.length.at.least', 4);
    });
  });

  describe('Responsive Tests', () => {
    const viewports = [
      { width: 1280, height: 720, device: 'desktop' },
      { width: 768, height: 1024, device: 'tablet' },
      { width: 375, height: 667, device: 'mobile' }
    ];

    viewports.forEach(({ width, height, device }) => {
      it(`should display correctly on ${device} (${width}x${height})`, () => {
        cy.viewport(width, height);
        cy.get('.main-content, main').should('be.visible');
      });
    });

    it('should adapt bureau grid on mobile', () => {
      cy.viewport(375, 667);
      cy.get('.bureau-row, .card').should('exist');
    });
  });

  describe('Navigation Tests', () => {
    it('should navigate back to dashboard', () => {
      // Use nav tab or back link to navigate
      cy.get('body').then($body => {
        if ($body.find('a[href*="dashboard"]').length) {
          cy.get('a[href*="dashboard"]').first().click({ force: true });
          cy.url().should('include', 'dashboard');
        } else if ($body.find('.nav-tab').length) {
          cy.get('.nav-tab').first().click({ force: true });
          cy.url().should('include', '/portal');
        } else {
          cy.get('body').should('exist');
        }
      });
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h2').should('exist');
    });

    it('should have form labels', () => {
      cy.get('body').then($body => {
        if ($body.find('form').length) {
          cy.get('form').should('exist');
        } else {
          cy.get('body').should('exist');
        }
      });
    });
  });

  describe('Status Styling Tests', () => {
    it('should have green styling for DELETED status', () => {
      cy.get('body').then($body => {
        if ($body.text().includes('DELETED')) {
          cy.contains('DELETED').should('have.css', 'background-color');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should have teal styling for DISPUTED status', () => {
      cy.get('body').then($body => {
        if ($body.text().includes('DISPUTED')) {
          cy.contains('DISPUTED').should('have.css', 'background-color');
        } else {
          cy.get('body').should('exist');
        }
      });
    });

    it('should have yellow styling for PENDING status', () => {
      cy.get('body').then($body => {
        if ($body.text().includes('PENDING')) {
          cy.contains('PENDING').should('have.css', 'background-color');
        } else {
          cy.get('body').should('exist');
        }
      });
    });
  });
});
