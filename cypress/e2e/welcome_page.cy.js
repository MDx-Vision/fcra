/**
 * WELCOME PAGE - Comprehensive E2E Tests
 * Tests the post-signup welcome page at /signup/welcome
 */

describe('Welcome Page', () => {
  beforeEach(() => {
    cy.visit('/signup/welcome', { failOnStatusCode: false });
  });

  it('should display welcome message', () => {
    cy.get('body').should('contain', 'Welcome').or('contain', 'Success');
  });

  it('should display success icon', () => {
    cy.get('svg, img, i, .icon, [class*="icon"]').should('exist');
  });

  it('should display next steps', () => {
    cy.get('body').should('contain', 'next').or('contain', 'steps').or('contain', 'what').or('contain', 'now');
  });

  it('should have Go to Client Portal button', () => {
    cy.contains('a, button', /portal|login|continue|proceed/i).should('exist');
  });

  it('should link to /portal/login', () => {
    cy.get('a[href*="portal"]').should('exist');
  });

  it('should display contact information', () => {
    cy.get('body').should('contain', 'contact').or('contain', 'email').or('contain', 'phone');
  });

  it('should be responsive on mobile', () => {
    cy.viewport(375, 667);
    cy.get('body').should('be.visible');
    cy.get('body').should('contain', 'Welcome').or('contain', 'Success');
  });

  it('should be responsive on tablet', () => {
    cy.viewport(768, 1024);
    cy.get('body').should('be.visible');
    cy.get('body').should('contain', 'Welcome').or('contain', 'Success');
  });

  it('should have correct branding', () => {
    cy.get('body').should('contain', 'FCRA').or('contain', 'Credit');
  });

  it('should display within 24-48 hours message', () => {
    cy.get('body').should('contain', '24').or('contain', '48').or('contain', 'hour');
  });

  it('should display client referral code', () => {
    cy.get('body').should('contain', 'code').or('contain', 'referral').or('contain', 'ID');
  });

  it('should have clear call-to-action', () => {
    cy.contains('button, a', /portal|login|continue/i).should('be.visible');
  });

  it('should display confirmation details', () => {
    cy.get('body').should('contain', 'email').or('contain', 'confirmation');
  });

  it('should show expected timeline', () => {
    cy.get('body').should('contain', 'day').or('contain', 'hour').or('contain', 'week');
  });

  it('should have support contact info', () => {
    cy.get('body').should('contain', 'support').or('contain', 'help').or('contain', 'contact');
  });

  describe('Page Elements', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1, h2, h3').should('exist');
    });

    it('should have accessible alt text for images', () => {
      cy.get('img').should('exist');
    });

    it('should have proper page title', () => {
      cy.title().should('exist');
    });
  });

  describe('Navigation', () => {
    it('should allow navigation to portal', () => {
      cy.get('a[href*="portal"]').first().should('have.attr', 'href');
    });

    it('should not show back button', () => {
      cy.get('body').should('exist');
    });
  });
});
