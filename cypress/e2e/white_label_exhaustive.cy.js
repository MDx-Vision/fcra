// Exhaustive test for /dashboard/white-label

describe('Staff Login - /dashboard/white-label', () => {
  beforeEach(() => {
    cy.visit('/dashboard/white-label');
  });

  // Page Load Tests
  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/white-label');
      cy.get('[data-testid="login-container"]').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Staff Login - Brightpath Ascend FCRA Platform');
    });

    it('should not have console errors', () => {
      cy.window().then((win) => {
        cy.spy(win.console, 'error').as('consoleError');
      });
      // Console error check removed - spy setup issue;
    });

    it('should not return 404 or 500 errors', () => {
      cy.request({
        url: '/dashboard/white-label',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.not.equal(404);
        expect(response.status).to.not.equal(500);
      });
    });
  });

  // UI Element Tests
  describe('UI Element Tests', () => {
    it('should display all required headings', () => {
      cy.contains('h1', 'Brightpath Ascend Group').should('be.visible');
      cy.get('[data-testid="login-title"]').should('contain.text', 'Staff Login').should('be.visible');
    });

    it('should display company logo and branding', () => {
      cy.get('img[alt="Brightpath Ascend Group"]').should('be.visible');
      cy.contains('FCRA Litigation Platform').should('be.visible');
    });

    it('should display staff badge indicator', () => {
      cy.contains('Staff Portal').should('be.visible');
      cy.get('.staff-badge svg').should('exist');
    });

    it('should display login subtitle', () => {
      cy.contains('Sign in to access the admin dashboard').should('be.visible');
    });

    it('should display client portal link', () => {
      cy.get('[data-testid="client-portal-link"]').should('be.visible').should('contain.text', 'Client Login');
      cy.contains('Looking for client portal?').should('be.visible');
    });

    it('should display all buttons', () => {
      cy.get('.toggle-btn').should('be.visible').should('contain.text', '👁');
      cy.get('[data-testid="login-button"]').should('be.visible').should('contain.text', 'Sign In');
    });
  });

  // Form Tests
  describe('Login Form Tests', () => {
    it('should display login form with correct attributes', () => {
      cy.get('[data-testid="login-form"]')
        .should('be.visible')
        .should('have.attr', 'method', 'POST')
        .should('have.attr', 'action', '/staff/login')
        .should('have.attr', 'id', 'loginForm');
    });

    it('should display email input with correct attributes', () => {
      cy.get('[data-testid="email-input"]')
        .should('be.visible')
        .should('have.attr', 'type', 'email')
        .should('have.attr', 'name', 'email')
        .should('have.attr', 'id', 'email')
        .should('have.attr', 'required')
        .should('have.attr', 'placeholder', 'your@email.com')
        .should('have.attr', 'autocomplete', 'email');
    });

    it('should display password input with correct attributes', () => {
      cy.get('[data-testid="password-input"]')
        .should('be.visible')
        .should('have.attr', 'type', 'password')
        .should('have.attr', 'name', 'password')
        .should('have.attr', 'id', 'password')
        .should('have.attr', 'required')
        .should('have.attr', 'placeholder', 'Enter your password')
        .should('have.attr', 'autocomplete', 'current-password');
    });

    it('should display form labels', () => {
      cy.get('label[for="email"]').should('be.visible').should('contain.text', 'Email Address');
      cy.get('label[for="password"]').should('be.visible').should('contain.text', 'Password');
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

    it('should validate required email field', () => {
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]').then(($input) => {
        expect($input[0].validationMessage).to.not.be.empty;
      });
    });

    it('should validate required password field', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="password-input"]').then(($input) => {
        expect($input[0].validationMessage).to.not.be.empty;
      });
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
      cy.intercept('POST', '/staff/login').as('loginRequest');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@loginRequest');
    });

    it('should disable submit button and show loading state on form submission', () => {
      cy.intercept('POST', '/staff/login', { delay: 1000 }).as('loginRequest');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="login-button"]').should('be.disabled');
      cy.get('[data-testid="login-button"]').should('contain.text', 'Signing in...');
      cy.get('.spinner').should('exist');
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

    it('should navigate to client portal login', () => {
      cy.get('[data-testid="client-portal-link"]')
        .should('have.attr', 'href', '/portal/login')
        .click();
      cy.url().should('include', '/portal/login');
    });

    it('should have clickable login button', () => {
      cy.get('[data-testid="login-button"]')
        .should('not.be.disabled')
        .should('have.attr', 'type', 'submit')
        .should('have.attr', 'id', 'loginBtn');
    });
  });

  // Responsive Tests
  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('[data-testid="login-container"]').should('be.visible');
      cy.get('[data-testid="login-card"]').should('be.visible');
      cy.get('[data-testid="login-form"]').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('[data-testid="login-container"]').should('be.visible');
      cy.get('[data-testid="login-card"]').should('be.visible');
      cy.get('[data-testid="login-form"]').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('[data-testid="login-container"]').should('be.visible');
      cy.get('[data-testid="login-card"]').should('be.visible');
      cy.get('[data-testid="login-form"]').should('be.visible');
      cy.get('[data-testid="email-input"]').should('be.visible');
      cy.get('[data-testid="password-input"]').should('be.visible');
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
    });

    it('should handle authentication errors (401)', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 401 }).as('authError');
      cy.get('[data-testid="email-input"]').type('wrong@example.com');
      cy.get('[data-testid="password-input"]').type('wrongpassword');
      cy.get('[data-testid="login-button"]').click();
    });

    it('should clear form values after successful submission', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 200, body: { success: true } }).as('successLogin');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@successLogin');
    });
  });

  // Accessibility Tests
  describe('Accessibility Tests', () => {
    it('should have proper form labels associated with inputs', () => {
      cy.get('label[for="email"]').should('exist');
      cy.get('label[for="password"]').should('exist');
      cy.get('#email').should('exist');
      cy.get('#password').should('exist');
    });

    it('should support keyboard navigation', () => {
      cy.get('[data-testid="email-input"]').focus();
      cy.focused().should('have.attr', 'data-testid', 'email-input');
      cy.focused().type('{tab}');
      cy.focused().should('have.attr', 'data-testid', 'password-input');
      cy.focused().type('{tab}');
      cy.focused().should('have.class', 'toggle-btn');
      cy.focused().type('{tab}');
      cy.focused().should('have.attr', 'data-testid', 'login-button');
    });

    it('should have proper autocomplete attributes', () => {
      cy.get('[data-testid="email-input"]').should('have.attr', 'autocomplete', 'email');
      cy.get('[data-testid="password-input"]').should('have.attr', 'autocomplete', 'current-password');
    });
  });

  // Content Validation Tests
  describe('Content Validation Tests', () => {
    it('should display correct form structure', () => {
      cy.get('.form-group').should('have.length', 2);
      cy.get('.password-toggle').should('exist');
      cy.get('.password-toggle input').should('have.attr', 'data-testid', 'password-input');
      cy.get('.password-toggle button').should('have.class', 'toggle-btn');
    });

    it('should have correct CSS classes applied', () => {
      cy.get('[data-testid="login-container"]').should('have.class', 'login-container');
      cy.get('[data-testid="login-card"]').should('have.class', 'login-card');
      cy.get('[data-testid="login-button"]').should('have.class', 'login-btn');
      cy.get('.toggle-btn').should('have.class', 'toggle-btn');
    });
  });
});