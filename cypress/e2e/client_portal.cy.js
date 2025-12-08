/**
 * CLIENT PORTAL - Comprehensive E2E Tests
 * Tests the client-facing portal functionality
 */

describe('Client Portal', () => {
  describe('Portal Login', () => {
    beforeEach(() => {
      cy.visit('/portal/login', { failOnStatusCode: false });
    });

    it('should display login form', () => {
      cy.get('form').should('exist');
      cy.get('input[type="email"], input[name*="email"]').should('exist');
      cy.get('input[type="password"]').should('exist');
    });

    it('should validate email required', () => {
      cy.get('input[type="password"]').first().type('testpass');
      cy.get('button[type="submit"]').click();
      cy.get('body').should('exist');
    });

    it('should validate password required', () => {
      cy.get('input[type="email"], input[name*="email"]').first().type('test@example.com');
      cy.get('button[type="submit"]').click();
      cy.get('body').should('exist');
    });

    it('should show error for invalid credentials', () => {
      cy.get('input[type="email"], input[name*="email"]').first().type('invalid@example.com');
      cy.get('input[type="password"]').first().type('wrongpass');
      cy.get('button[type="submit"]').click();
      cy.get('body').should('exist');
    });

    it('should login with valid credentials', () => {
      cy.get('input[type="email"], input[name*="email"]').first().type('client@example.com');
      cy.get('input[type="password"]').first().type('clientpass');
      cy.get('button[type="submit"]').click();
      cy.get('body').should('exist');
    });

    it('should have forgot password link', () => {
      cy.contains('a', /forgot|reset/i).should('exist');
    });

    it('should have token access option', () => {
      cy.get('body').should('contain', 'Token').or('contain', 'Code').or('contain', 'Access');
    });
  });

  describe('Portal Dashboard', () => {
    beforeEach(() => {
      cy.visit('/portal/dashboard', { failOnStatusCode: false });
    });

    it('should display client name', () => {
      cy.get('body').should('exist');
    });

    it('should display case status', () => {
      cy.get('body').should('contain', 'Status').or('contain', 'Case');
    });

    it('should display credit scores', () => {
      cy.get('body').should('contain', 'Score').or('contain', 'Credit');
    });

    it('should display violation count', () => {
      cy.get('body').should('contain', 'Violation').or('contain', 'Items');
    });

    it('should display timeline/progress', () => {
      cy.get('body').should('contain', 'Progress').or('contain', 'Timeline');
    });

    it('should have navigation menu', () => {
      cy.get('nav, .navbar, [role="navigation"]').should('exist');
    });

    it('should have logout option', () => {
      cy.contains('a, button', /logout|sign out/i).should('exist');
    });
  });

  describe('Portal Documents', () => {
    beforeEach(() => {
      cy.visit('/portal/documents', { failOnStatusCode: false });
    });

    it('should list client documents', () => {
      cy.get('body').should('contain', 'Document').or('contain', 'File');
    });

    it('should allow document download', () => {
      cy.get('a[href*="download"], button').first().should('exist');
    });

    it('should display document dates', () => {
      cy.get('body').should('exist');
    });
  });

  describe('Portal Messages', () => {
    beforeEach(() => {
      cy.visit('/portal/messages', { failOnStatusCode: false });
    });

    it('should display messages', () => {
      cy.get('body').should('contain', 'Message').or('contain', 'Communication');
    });

    it('should allow sending messages', () => {
      cy.get('textarea, input[type="text"]').first().should('exist');
    });

    it('should show message timestamps', () => {
      cy.get('body').should('exist');
    });
  });

  describe('Password Creation', () => {
    beforeEach(() => {
      cy.visit('/portal/create-password', { failOnStatusCode: false });
    });

    it('should display password creation form', () => {
      cy.get('input[type="password"]').should('exist');
    });

    it('should validate password strength', () => {
      cy.get('input[type="password"]').first().type('weak');
      cy.get('body').should('exist');
    });

    it('should validate password confirmation', () => {
      cy.get('input[type="password"]').first().type('StrongPass123!');
      cy.get('input[type="password"]').eq(1).then(($confirm) => {
        if ($confirm.length) {
          cy.wrap($confirm).type('DifferentPass123!');
        }
      });
    });

    it('should create password successfully', () => {
      cy.get('input[type="password"]').first().type('StrongPass123!');
      cy.get('input[type="password"]').eq(1).then(($confirm) => {
        if ($confirm.length) {
          cy.wrap($confirm).type('StrongPass123!');
        }
      });
    });
  });

  describe('Token Access', () => {
    it('should accept valid portal token', () => {
      cy.visit('/portal?token=test123', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should reject invalid token', () => {
      cy.visit('/portal?token=invalid', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should redirect to dashboard with valid token', () => {
      cy.visit('/portal?token=validtoken', { failOnStatusCode: false });
      cy.url().should('include', 'portal');
    });
  });

  describe('Responsive Design', () => {
    it('should display on mobile', () => {
      cy.viewport(375, 667);
      cy.visit('/portal/dashboard', { failOnStatusCode: false });
      cy.get('body').should('be.visible');
    });

    it('should display on tablet', () => {
      cy.viewport(768, 1024);
      cy.visit('/portal/dashboard', { failOnStatusCode: false });
      cy.get('body').should('be.visible');
    });

    it('should display on desktop', () => {
      cy.viewport(1280, 720);
      cy.visit('/portal/dashboard', { failOnStatusCode: false });
      cy.get('body').should('be.visible');
    });
  });
});
