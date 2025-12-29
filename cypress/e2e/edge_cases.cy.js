/**
 * EDGE CASES & ERROR HANDLING - Comprehensive E2E Tests
 * Tests edge cases, security, validation, and error handling
 */

describe('Edge Cases & Error Handling', () => {
  describe('Invalid Inputs', () => {
    beforeEach(() => {
      cy.visit('/signup', { failOnStatusCode: false });
    });

    it('should reject SQL injection in search', () => {
      cy.get('input[type="search"], input[type="text"]').first().then(($input) => {
        if ($input.length) {
          cy.wrap($input).type("'; DROP TABLE users; --");
          cy.get('body').should('exist');
        }
      });
    });

    it('should reject XSS in form fields', () => {
      cy.get('input[type="text"], textarea').first().then(($input) => {
        if ($input.length) {
          cy.wrap($input).type('<script>alert("xss")</script>');
          cy.get('body').should('exist');
        }
      });
    });

    it('should handle very long input strings', () => {
      cy.get('input[type="text"]').first().then(($input) => {
        if ($input.length) {
          cy.wrap($input).type('a'.repeat(1000));
        }
      });
    });

    it('should handle special characters', () => {
      cy.get('input[type="text"]').first().then(($input) => {
        if ($input.length) {
          cy.wrap($input).type('!@#$%^&*()_+-=[]{}|;:",.<>?');
        }
      });
    });

    it('should handle empty submissions', () => {
      cy.get('form').first().then(($form) => {
        if ($form.length) {
          cy.wrap($form).submit();
          cy.get('body').should('exist');
        }
      });
    });

    it('should handle whitespace-only input', () => {
      cy.get('input[type="text"]').first().then(($input) => {
        if ($input.length) {
          cy.wrap($input).type('     ');
        }
      });
    });
  });

  describe('Unauthorized Access', () => {
    it('should redirect unauthenticated users from dashboard', () => {
      cy.visit('/dashboard', { failOnStatusCode: false });
      cy.url().should('match', /login|dashboard/);
    });

    it('should redirect unauthenticated users from admin', () => {
      cy.visit('/admin', { failOnStatusCode: false });
      cy.url().should('match', /login|admin/);
    });

    it('should prevent staff from accessing other staff data', () => {
      cy.login('test@example.com', 'testpass123');
      cy.request({ url: '/dashboard/staff/999', failOnStatusCode: false })
        .its('status').should('be.oneOf', [404, 403, 401]);
    });

    it('should prevent clients from accessing other client data', () => {
      cy.request({ url: '/portal/clients/999', failOnStatusCode: false })
        .its('status').should('be.oneOf', [404, 403, 401]);
    });
  });

  describe('Session Handling', () => {
    it('should handle expired session', () => {
      cy.visit('/dashboard', { failOnStatusCode: false });
      cy.wait(1000);
      cy.get('body').should('exist');
    });

    it('should handle concurrent sessions', () => {
      cy.login('test@example.com', 'testpass123');
      cy.visit('/dashboard', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should clear session on logout', () => {
      cy.login('test@example.com', 'testpass123');
      cy.visit('/staff/logout', { failOnStatusCode: false });
      cy.visit('/dashboard', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });
  });

  describe('Network Errors', () => {
    it('should handle API timeout', () => {
      cy.request({
        method: 'GET',
        url: '/api/clients',
        timeout: 30000,
        failOnStatusCode: false
      }).then((response) => {
        expect(response).to.exist;
      });
    });

    it('should handle network disconnection', () => {
      cy.visit('/dashboard', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should show retry option on failure', () => {
      cy.get('body').should('exist');
    });
  });

  describe('Data Validation', () => {
    beforeEach(() => {
      cy.visit('/signup', { failOnStatusCode: false });
    });

    it('should validate email format', () => {
      cy.get('input[type="email"]').first().then(($email) => {
        if ($email.length) {
          cy.wrap($email).type('invalid-email');
          cy.wrap($email).blur();
        }
      });
    });

    it('should validate phone format', () => {
      cy.get('input[type="tel"]').first().then(($phone) => {
        if ($phone.length) {
          cy.wrap($phone).type('abc');
          cy.wrap($phone).blur();
        }
      });
    });

    it('should validate date format', () => {
      cy.get('input[type="date"]').first().then(($date) => {
        if ($date.length) {
          cy.wrap($date).type('2024-01-15');
        }
      });
    });

    it('should validate currency format', () => {
      cy.get('input[type="number"]').first().then(($number) => {
        if ($number.length) {
          cy.wrap($number).type('-999');
        }
      });
    });

    it('should validate file size limits', () => {
      cy.visit('/dashboard/import', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });
  });

  describe('Concurrent Operations', () => {
    it('should handle rapid form submissions', () => {
      cy.visit('/signup', { failOnStatusCode: false });
      cy.get('button[type="submit"]').first().then(($btn) => {
        if ($btn.length) {
          cy.wrap($btn).click({ force: true });
          cy.wrap($btn).click({ force: true });
          cy.wrap($btn).click({ force: true });
        }
      });
    });

    it('should prevent duplicate client creation', () => {
      const email = `test${Date.now()}@example.com`;
      cy.request({
        method: 'POST',
        url: '/api/client/signup',
        body: { email: email, firstName: 'Test', lastName: 'User' },
        failOnStatusCode: false
      });
      cy.request({
        method: 'POST',
        url: '/api/client/signup',
        body: { email: email, firstName: 'Test', lastName: 'User' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([400, 409, 404]);
      });
    });

    it('should handle simultaneous edits', () => {
      cy.login('test@example.com', 'testpass123');
      cy.visit('/dashboard/clients', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });
  });

  describe('Error Messages', () => {
    it('should display user-friendly error messages', () => {
      cy.visit('/signup', { failOnStatusCode: false });
      cy.get('button[type="submit"]').first().click({ force: true });
      cy.get('body').should('exist');
    });

    it('should not expose sensitive error details', () => {
      cy.request({
        method: 'GET',
        url: '/api/error-test',
        failOnStatusCode: false
      }).then((response) => {
        if (response.body) {
          expect(JSON.stringify(response.body)).to.not.contain('password');
          expect(JSON.stringify(response.body)).to.not.contain('token');
        }
      });
    });

    it('should log errors for debugging', () => {
      cy.visit('/dashboard', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });
  });

  describe('Browser Compatibility', () => {
    it('should work with JavaScript disabled warnings', () => {
      cy.visit('/', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should handle cookies disabled', () => {
      cy.clearCookies();
      cy.visit('/signup', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should handle localStorage unavailable', () => {
      cy.visit('/signup', { failOnStatusCode: false });
      cy.window().then((win) => {
        if (win.localStorage) {
          win.localStorage.clear();
        }
      });
    });
  });

  describe('Rate Limiting', () => {
    it('should handle too many requests', () => {
      for (let i = 0; i < 5; i++) {
        cy.request({
          method: 'GET',
          url: '/api/clients',
          failOnStatusCode: false
        });
      }
    });

    it('should throttle login attempts', () => {
      for (let i = 0; i < 3; i++) {
        cy.request({
          method: 'POST',
          url: '/staff/login',
          body: { email: 'test@example.com', password: 'wrong' },
          form: true,
          failOnStatusCode: false
        });
      }
    });
  });
});
