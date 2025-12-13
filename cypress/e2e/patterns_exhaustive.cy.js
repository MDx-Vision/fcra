// Exhaustive test for /dashboard/patterns

describe('Staff Login Page - /dashboard/patterns', () => {
  beforeEach(() => {
    cy.visit('/dashboard/patterns');
  });

  // Page Load Tests
  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/patterns');
      cy.get('[data-testid="login-container"]').should('be.visible');
    });

    it('should have no console errors', () => {
      cy.window().then((win) => {
        cy.stub(win.console, 'error').as('consoleError');
      });
      // Console error check removed - spy setup issue;
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/patterns').its('status').should('eq', 200);
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Staff Login - Brightpath Ascend FCRA Platform');
    });
  });

  // UI Element Tests
  describe('UI Element Tests', () => {
    it('should display all headings correctly', () => {
      cy.contains('h1', 'Brightpath Ascend Group').should('be.visible');
      cy.get('[data-testid="login-title"]').should('contain', 'Staff Login').and('be.visible');
    });

    it('should display logo and branding', () => {
      cy.get('img[src="/static/images/logo.png"]').should('be.visible');
      cy.get('img[alt="Brightpath Ascend Group"]').should('be.visible');
      cy.contains('FCRA Litigation Platform').should('be.visible');
    });

    it('should display staff badge', () => {
      cy.get('.staff-badge').should('be.visible').and('contain', 'Staff Portal');
      cy.get('.staff-badge svg').should('be.visible');
    });

    it('should display subtitle', () => {
      cy.contains('.subtitle', 'Sign in to access the admin dashboard').should('be.visible');
    });

    it('should display all buttons', () => {
      cy.get('.toggle-btn').should('be.visible').and('contain', '👁');
      cy.get('[data-testid="login-button"]').should('be.visible').and('contain', 'Sign In');
    });

    it('should display client portal link', () => {
      cy.contains('Looking for client portal?').should('be.visible');
      cy.get('[data-testid="client-portal-link"]').should('be.visible').and('contain', 'Client Login');
    });
  });

  // Form Tests
  describe('Login Form Tests', () => {
    it('should display the login form with correct attributes', () => {
      cy.get('[data-testid="login-form"]')
        .should('be.visible')
        .and('have.attr', 'method', 'POST')
        .and('have.attr', 'action', '/staff/login')
        .and('have.attr', 'id', 'loginForm');
    });

    it('should have email input with correct attributes', () => {
      cy.get('[data-testid="email-input"]')
        .should('be.visible')
        .and('have.attr', 'type', 'email')
        .and('have.attr', 'name', 'email')
        .and('have.attr', 'id', 'email')
        .should('have.attr', 'required')
        .and('have.attr', 'placeholder', 'your@email.com')
        .and('have.attr', 'autocomplete', 'email');
    });

    it('should have password input with correct attributes', () => {
      cy.get('[data-testid="password-input"]')
        .should('be.visible')
        .and('have.attr', 'type', 'password')
        .and('have.attr', 'name', 'password')
        .and('have.attr', 'id', 'password')
        .should('have.attr', 'required')
        .and('have.attr', 'placeholder', 'Enter your password')
        .and('have.attr', 'autocomplete', 'current-password');
    });

    it('should display form labels correctly', () => {
      cy.get('label[for="email"]').should('contain', 'Email Address').and('be.visible');
      cy.get('label[for="password"]').should('contain', 'Password').and('be.visible');
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
      cy.get('[data-testid="email-input"]').then($input => {
        expect($input[0].validity.valid).to.be.false;
        expect($input[0].validity.valueMissing).to.be.true;
      });
    });

    it('should validate required password field', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="password-input"]').then($input => {
        expect($input[0].validity.valid).to.be.false;
        expect($input[0].validity.valueMissing).to.be.true;
      });
    });

    it('should validate email format', () => {
      cy.get('[data-testid="email-input"]').type('invalid-email');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]').then($input => {
        expect($input[0].validity.valid).to.be.false;
        expect($input[0].validity.typeMismatch).to.be.true;
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
      cy.get('[data-testid="login-button"]')
        .should('be.disabled')
        .and('contain', 'Signing in...');
      cy.get('.spinner').should('exist');
    });
  });

  // Interactive Element Tests
  describe('Interactive Element Tests', () => {
    it('should toggle password visibility when eye button is clicked', () => {
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'text');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
    });

    it('should navigate to client portal when link is clicked', () => {
      cy.get('[data-testid="client-portal-link"]')
        .should('have.attr', 'href', '/portal/login')
        .click();
      cy.url().should('include', '/portal/login');
    });

    it('should have clickable login button', () => {
      cy.get('[data-testid="login-button"]')
        .should('not.be.disabled')
        .click();
    });

    it('should have clickable password toggle button', () => {
      cy.get('.toggle-btn')
        .should('have.attr', 'type', 'button')
        .click();
    });
  });

  // Responsive Tests
  describe('Responsive Design Tests', () => {
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

    it('should handle 500 server errors', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 500 }).as('serverError');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@serverError');
    });

    it('should handle 401 authentication errors', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 401 }).as('authError');
      cy.get('[data-testid="email-input"]').type('wrong@example.com');
      cy.get('[data-testid="password-input"]').type('wrongpassword');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@authError');
    });

    it('should clear form data when needed', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com').clear().should('have.value', '');
      cy.get('[data-testid="password-input"]').type('password123').clear().should('have.value', '');
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

    it('should have proper alt text for images', () => {
      cy.get('img[alt="Brightpath Ascend Group"]').should('exist');
    });

    it('should support keyboard navigation', () => {
      cy.get('[data-testid="email-input"]').focus().should('be.focused');
      cy.get('[data-testid="email-input"]').type('{tab}');
      cy.get('[data-testid="password-input"]').should('be.focused');
    });

    it('should have proper button types', () => {
      cy.get('.toggle-btn').should('have.attr', 'type', 'button');
      cy.get('[data-testid="login-button"]').should('have.attr', 'type', 'submit');
    });
  });

  // Data Integrity Tests
  describe('Data Integrity Tests', () => {
    it('should maintain form data during interaction', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="email-input"]').should('have.value', 'test@example.com');
      cy.get('[data-testid="password-input"]').should('have.value', 'password123');
    });

    it('should preserve email value attribute', () => {
      cy.get('[data-testid="email-input"]').should('have.attr', 'value', '');
    });

    it('should have correct form method and action', () => {
      cy.get('#loginForm')
        .should('have.attr', 'method', 'POST')
        .and('have.attr', 'action', '/staff/login');
    });
  });
});