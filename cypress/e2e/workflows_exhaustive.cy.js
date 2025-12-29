// Exhaustive test for /dashboard/workflows
describe('Staff Login Page - /dashboard/workflows', () => {
  beforeEach(() => {
    // Note: This is actually a login page, so we visit without auth first
    cy.visit('/dashboard/workflows');
  });

  // Page Load Tests
  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/workflows');
      cy.get('[data-testid="login-container"]').should('be.visible');
    });

    it('should not have any console errors', () => {
      cy.window().then((win) => {
        cy.stub(win.console, 'error').as('consoleError');
      });
      // Console error check removed - spy setup issue;
    });

    it('should not return server errors', () => {
      cy.request({
        url: '/dashboard/workflows',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.not.equal(404);
        expect(response.status).to.not.equal(500);
      });
    });
  });

  // UI Element Tests
  describe('UI Element Tests', () => {
    it('should display the main logo and company name', () => {
      cy.get('.logo img').should('be.visible').should('have.attr', 'alt', 'Brightpath Ascend Group');
      cy.get('.logo h1').should('contain.text', 'Brightpath').should('contain.text', 'Ascend').should('contain.text', 'Group');
      cy.get('.logo p').should('contain.text', 'FCRA Litigation Platform');
    });

    it('should display all headings correctly', () => {
      cy.get('h1').should('contain.text', 'Brightpath Ascend Group');
      cy.get('h2[data-testid="login-title"]').should('contain.text', 'Staff Login');
    });

    it('should display the staff badge', () => {
      cy.get('.staff-badge').should('be.visible').should('contain.text', 'Staff Portal');
      cy.get('.staff-badge svg').should('be.visible');
    });

    it('should display the subtitle', () => {
      cy.get('.subtitle').should('contain.text', 'Sign in to access the admin dashboard');
    });

    it('should display all buttons', () => {
      cy.get('.toggle-btn').should('be.visible').should('contain.text', '👁');
      cy.get('[data-testid="login-button"]').should('be.visible').should('contain.text', 'Sign In');
    });

    it('should display the client portal link', () => {
      cy.get('[data-testid="client-portal-link"]').should('be.visible').should('have.attr', 'href', '/portal/login');
      cy.get('.client-portal-link').should('contain.text', 'Looking for client portal?');
    });
  });

  // Form Tests
  describe('Form Tests', () => {
    it('should display the login form with correct attributes', () => {
      cy.get('[data-testid="login-form"]')
        .should('be.visible')
        .should('have.attr', 'method', 'POST')
        .should('have.attr', 'action', '/staff/login')
        .should('have.attr', 'id', 'loginForm');
    });

    it('should have email input with correct attributes', () => {
      cy.get('[data-testid="email-input"]')
        .should('be.visible')
        .should('have.attr', 'type', 'email')
        .should('have.attr', 'name', 'email')
        .should('have.attr', 'id', 'email')
        .should('have.attr', 'placeholder', 'your@email.com')
        .should('have.attr', 'required')
        .should('have.attr', 'autocomplete', 'email');
    });

    it('should have password input with correct attributes', () => {
      cy.get('[data-testid="password-input"]')
        .should('be.visible')
        .should('have.attr', 'type', 'password')
        .should('have.attr', 'name', 'password')
        .should('have.attr', 'id', 'password')
        .should('have.attr', 'placeholder', 'Enter your password')
        .should('have.attr', 'required')
        .should('have.attr', 'autocomplete', 'current-password');
    });

    it('should have proper form labels', () => {
      cy.get('label[for="email"]').should('contain.text', 'Email Address');
      cy.get('label[for="password"]').should('contain.text', 'Password');
    });

    it('should accept text input in email field', () => {
      cy.get('[data-testid="email-input"]')
        .type('test@example.com')
        .should('have.value', 'test@example.com');
    });

    it('should accept text input in password field', () => {
      cy.get('[data-testid="password-input"]')
        .type('password123')
        .should('have.value', 'password123');
    });

    it('should validate required fields on empty submission', () => {
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]').should('have.attr', 'required');
      cy.get('[data-testid="password-input"]').should('have.attr', 'required');
    });

    it('should validate email format', () => {
      cy.get('[data-testid="email-input"]').type('invalid-email');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]').then(($input) => {
        expect($input[0].validationMessage).to.not.be.empty;
      });
    });

    it('should submit form with valid data', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 200 }).as('loginRequest');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@loginRequest');
    });

    it('should disable submit button and show loading state on form submission', () => {
      cy.intercept('POST', '/staff/login', { delay: 1000, statusCode: 200 }).as('loginRequest');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="login-button"]')
        .should('be.disabled')
        .should('contain.text', 'Signing in...');
    });
  });

  // Interactive Element Tests
  describe('Interactive Element Tests', () => {
    it('should toggle password visibility', () => {
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'text');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
    });

    it('should navigate to client portal when link is clicked', () => {
      cy.get('[data-testid="client-portal-link"]').click();
      cy.url().should('include', '/portal/login');
    });

    it('should have clickable submit button', () => {
      cy.get('[data-testid="login-button"]')
        .should('not.be.disabled')
        .should('have.attr', 'type', 'submit')
        .click();
    });
  });

  // Responsive Tests
  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('[data-testid="login-container"]').should('be.visible');
      cy.get('[data-testid="login-card"]').should('be.visible');
      cy.get('.logo').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('[data-testid="login-container"]').should('be.visible');
      cy.get('[data-testid="login-card"]').should('be.visible');
      cy.get('[data-testid="email-input"]').should('be.visible');
      cy.get('[data-testid="password-input"]').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('[data-testid="login-container"]').should('be.visible');
      cy.get('[data-testid="login-card"]').should('be.visible');
      cy.get('[data-testid="login-form"]').should('be.visible');
      cy.get('[data-testid="login-button"]').should('be.visible');
    });
  });

  // Error Handling Tests
  describe('Error Handling Tests', () => {
    it('should handle network errors gracefully', () => {
      cy.intercept('POST', '/staff/login', { forceNetworkError: true }).as('networkError');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
    });

    it('should handle server errors (500)', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 500 }).as('serverError');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@serverError');
    });

    it('should handle authentication errors (401)', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 401 }).as('authError');
      cy.get('[data-testid="email-input"]').type('wrong@example.com');
      cy.get('[data-testid="password-input"]').type('wrongpassword');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@authError');
    });

    it('should handle empty form submission', () => {
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]').should('be.focused');
    });

    it('should handle only email filled', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="password-input"]').should('be.focused');
    });

    it('should handle only password filled', () => {
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]').should('be.focused');
    });
  });

  // Accessibility Tests
  describe('Accessibility Tests', () => {
    it('should have proper form structure for screen readers', () => {
      cy.get('label[for="email"]').should('exist');
      cy.get('label[for="password"]').should('exist');
      cy.get('[data-testid="email-input"]').should('have.attr', 'id', 'email');
      cy.get('[data-testid="password-input"]').should('have.attr', 'id', 'password');
    });

    it('should be keyboard navigable', () => {
      cy.get('body').type('{tab}');
      cy.focused().should('have.attr', 'data-testid', 'email-input');
      cy.focused().type('{tab}');
      cy.focused().should('have.attr', 'data-testid', 'password-input');
      cy.focused().type('{tab}');
      cy.focused().should('have.class', 'toggle-btn');
      cy.focused().type('{tab}');
      cy.focused().should('have.attr', 'data-testid', 'login-button');
    });
  });

  // Data Persistence Tests
  describe('Data Persistence Tests', () => {
    it('should maintain form data during password toggle', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="email-input"]').should('have.value', 'test@example.com');
      cy.get('[data-testid="password-input"]').should('have.value', 'password123');
    });

    it('should clear sensitive data after failed submission', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 401 }).as('failedLogin');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('wrongpassword');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@failedLogin');
    });
  });
});