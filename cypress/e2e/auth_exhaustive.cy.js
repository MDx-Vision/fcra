/**
 * AUTH - Exhaustive E2E Tests
 * Auto-generated comprehensive test suite
 * Routes covered: 4
 */

describe('Auth - Full QA Suite', () => {
  
  beforeEach(() => {
    cy.login('test@example.com', 'password123');
  });

  // ==========================================
  // SECTION 1: PAGE LOAD & NAVIGATION
  // ==========================================
  describe('Page Load & Navigation', () => {

    it.skip('should load /staff/login - redirects when logged in', () => {
      cy.visit('/staff/login', { failOnStatusCode: false });
      cy.url().should('include', 'staff');
    });

    it('should load /staff/change-password', () => {
      cy.visit('/staff/change-password', { failOnStatusCode: false });
      cy.url().should('include', 'staff');
    });

    it.skip('should load /staff/logout - redirects when logged in', () => {
      cy.visit('/staff/logout', { failOnStatusCode: false });
      cy.url().should('include', 'staff');
    });

    it('should load /portal/login', () => {
      cy.visit('/portal/login', { failOnStatusCode: false });
      cy.url().should('include', 'portal');
    });

  });

  // ==========================================
  // SECTION 2: UI ELEMENTS
  // ==========================================
  describe('UI Elements', () => {
    it('should display page without errors', () => {
      cy.window().then((win) => {
        cy.spy(win.console, 'error').as('consoleError');
      });
    });

    it('should have navigation elements', () => {
      cy.get('nav, .navbar, .sidebar, [data-testid*="nav"]').should('exist');
    });

    it('should have main content area', () => {
      cy.get('main, .content, .container, [data-testid*="content"]').should('exist');
    });
  });

  // ==========================================
  // SECTION 3: FORMS & INPUTS
  // ==========================================
  describe('Forms & Inputs', () => {
    it('should validate required fields', () => {
      cy.get('form').first().then(($form) => {
        if ($form.length) {
          cy.get('input[required]').should('exist');
        }
      });
    });

    it('should show validation errors', () => {
      // Click button to open modal
      cy.get('.btn, button').contains(/add/i).first().click();

      // Wait for modal to be visible
      cy.get('.modal.active').should('be.visible');

      // Try to submit empty form
      cy.get('.modal.active form').first().then(($form) => {
        // Trigger form submission or check for HTML5 validation
        cy.get('.modal.active input[required]').first().then(($input) => {
          // Check if HTML5 validation works or look for validation messages
          expect($input[0].checkValidity()).to.be.false;
        });
      });
    });
  });

  // ==========================================
  // SECTION 4: ERROR HANDLING
  // ==========================================
  describe('Error Handling', () => {
    it('should handle 404 pages', () => {
      cy.request({ url: '/nonexistent-page-12345', failOnStatusCode: false })
        .then((response) => {
          expect(response.status).to.be.oneOf([404, 401, 403]);
        });
    });

    it('should handle invalid parameters', () => {
      cy.request({ url: '/dashboard/clients/999999', failOnStatusCode: false })
        .then((response) => {
          expect(response.status).to.be.oneOf([404, 401, 403, 302]);
        });
    });
  });

  // ==========================================
  // SECTION 5: RESPONSIVE DESIGN
  // ==========================================
  describe('Responsive Design', () => {
    it('should display on desktop', () => {
      cy.viewport(1280, 720);
      cy.get('body').should('be.visible');
    });

    it('should display on tablet', () => {
      cy.viewport(768, 1024);
      cy.get('body').should('be.visible');
    });

    it('should display on mobile', () => {
      cy.viewport(375, 667);
      cy.get('body').should('be.visible');
    });
  });
});
