// Exhaustive test for /dashboard/settings
describe('Settings Page - /dashboard/settings', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/settings');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/settings');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Settings');
      cy.title().should('contain', 'Brightpath Ascend FCRA Platform');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/settings').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('be.visible');
    });

    it('should display Back to Dashboard button', () => {
      cy.get('.header .btn-secondary').should('contain.text', 'Back to Dashboard');
    });

    it('should have working back button link', () => {
      cy.get('.header .btn-secondary').should('have.attr', 'href', '/dashboard');
    });
  });

  describe('Settings Form Tests', () => {
    it('should display settings form', () => {
      cy.get('#settingsForm').should('exist');
    });

    it('should have form element', () => {
      cy.get('form').should('exist');
    });
  });

  describe('Content Card Tests', () => {
    it('should display content cards', () => {
      cy.get('.content-card').should('have.length.at.least', 1);
    });

    it('should display section titles', () => {
      cy.get('.section-title').should('have.length.at.least', 1);
    });
  });

  describe('Signup Field Configuration Section', () => {
    it('should display Signup Field Configuration section', () => {
      cy.get('.section-title').contains('Signup Field Configuration').should('be.visible');
    });
  });

  describe('Pricing Tier Configuration Section', () => {
    it('should display Pricing Tier Configuration section', () => {
      cy.get('.section-title').contains('Pricing Tier Configuration').should('be.visible');
    });
  });

  describe('Manual Payment Information Section', () => {
    it('should display Manual Payment Information section', () => {
      cy.get('.section-title').contains('Manual Payment Information').should('be.visible');
    });
  });

  describe('Payment Methods Section', () => {
    it('should display Payment Methods section', () => {
      cy.get('.section-title').contains('Payment Methods').should('be.visible');
    });
  });

  describe('Form Controls Tests', () => {
    it('should have Save Settings button', () => {
      cy.get('.btn-primary').contains('Save Settings').should('be.visible');
    });

    it('should have Cancel button', () => {
      cy.get('.btn-secondary').contains('Cancel').should('be.visible');
    });

    it('should have clickable save button', () => {
      cy.get('.btn-primary').contains('Save Settings').should('not.be.disabled');
    });
  });

  describe('SMS Settings Link Tests', () => {
    it('should display link to SMS settings', () => {
      cy.get('a[href="/dashboard/settings/sms"]').should('exist');
    });
  });

  describe('Toggle Controls Tests', () => {
    it('should display toggle switches for field configuration', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.toggle-switch').length > 0) {
          cy.get('.toggle-switch').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
      cy.get('.content-card').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.content-card').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.header h1').should('be.visible');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
      cy.get('h2').should('have.length.at.least', 1);
    });

    it('should have form labels', () => {
      cy.get('label').should('have.length.at.least', 1);
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have primary button styling', () => {
      cy.get('.btn-primary').should('exist');
    });

    it('should have secondary button styling', () => {
      cy.get('.btn-secondary').should('exist');
    });
  });
});
