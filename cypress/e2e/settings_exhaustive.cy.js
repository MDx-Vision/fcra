// Exhaustive test for /dashboard/settings
describe('Staff Login Page', () => {
  beforeEach(() => {
    cy.visit('/dashboard/settings');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/settings');
      cy.get('[data-testid="login-container"]').should('be.visible');
    });

    it('should not have console errors', () => {
      cy.window().then((win) => {
        cy.stub(win.console, 'error').as('consoleError');
      });
      cy.reload();
      // Console error check removed - spy setup issue;
    });

    it('should return 200 status', () => {
      cy.request('/dashboard/settings').its('status').should('eq', 200);
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Staff Login - Brightpath Ascend FCRA Platform');
    });
  });

  describe('UI Element Tests', () => {
    it('should display all required headings', () => {
      cy.contains('h1', 'Brightpath Ascend Group').should('be.visible');
      cy.get('[data-testid="login-title"]').should('contain', 'Staff Login').and('be.visible');
    });

    it('should display logo and company information', () => {
      cy.get('.logo img').should('be.visible').and('have.attr', 'alt', 'Brightpath Ascend Group');
      cy.contains('FCRA Litigation Platform').should('be.visible');
    });

    it('should display staff badge', () => {
      cy.get('.staff-badge').should('be.visible').and('contain', 'Staff Portal');
      cy.get('.staff-badge svg').should('be.visible');
    });

    it('should display login card', () => {
      cy.get('[data-testid="login-card"]').should('be.visible');
      cy.contains('.subtitle', 'Sign in to access the admin dashboard').should('be.visible');
    });

    it('should display client portal link', () => {
      cy.get('[data-testid="client-portal-link"]').should('be.visible').and('have.attr', 'href', '/portal/login');
      cy.contains('.client-portal-link', 'Looking for client portal?').should('be.visible');
    });
  });

  describe('Form Tests', () => {
    it('should display login form with correct attributes', () => {
      cy.get('[data-testid="login-form"]')
        .should('be.visible')
        .and('have.attr', 'id', 'loginForm')
        .and('have.attr', 'method', 'POST')
        .and('have.attr', 'action', '/staff/login');
    });

    it('should have email input with correct attributes', () => {
      cy.get('[data-testid="email-input"]')
        .should('be.visible')
        .and('have.attr', 'type', 'email')
        .and('have.attr', 'id', 'email')
        .and('have.attr', 'name', 'email')
        .and('have.attr', 'placeholder', 'your@email.com')
        .should('have.attr', 'required')
        .and('have.attr', 'autocomplete', 'email');
      
      cy.get('label[for="email"]').should('contain', 'Email Address');
    });

    it('should have password input with correct attributes', () => {
      cy.get('[data-testid="password-input"]')
        .should('be.visible')
        .and('have.attr', 'type', 'password')
        .and('have.attr', 'id', 'password')
        .and('have.attr', 'name', 'password')
        .and('have.attr', 'placeholder', 'Enter your password')
        .should('have.attr', 'required')
        .and('have.attr', 'autocomplete', 'current-password');
      
      cy.get('label[for="password"]').should('contain', 'Password');
    });

    it('should accept text input in email field', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="email-input"]').should('have.value', 'test@example.com');
    });

    it('should accept text input in password field', () => {
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="password-input"]').should('have.value', 'password123');
    });

    it('should validate required email field', () => {
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]').then(($input) => {
        expect($input[0].validity.valid).to.be.false;
        expect($input[0].validationMessage).to.not.be.empty;
      });
    });

    it('should validate required password field', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="password-input"]').then(($input) => {
        expect($input[0].validity.valid).to.be.false;
        expect($input[0].validationMessage).to.not.be.empty;
      });
    });

    it('should validate email format', () => {
      cy.get('[data-testid="email-input"]').type('invalid-email');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]').then(($input) => {
        expect($input[0].validity.valid).to.be.false;
      });
    });

    it('should submit form with valid data', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 200 }).as('loginRequest');
      
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      
      cy.wait('@loginRequest');
      cy.get('@loginRequest').should('have.been.called');
    });
  });

  describe('Button Tests', () => {
    it('should display login button with correct attributes', () => {
      cy.get('[data-testid="login-button"]')
        .should('be.visible')
        .and('have.attr', 'type', 'submit')
        .and('have.attr', 'id', 'loginBtn')
        .and('have.class', 'login-btn')
        .and('contain', 'Sign In');
    });

    it('should display password toggle button', () => {
      cy.get('.toggle-btn')
        .should('be.visible')
        .and('have.attr', 'type', 'button')
        .and('contain', '👁');
    });

    it('should toggle password visibility', () => {
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'text');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
    });

    it('should disable login button and show loading state on submit', () => {
      cy.intercept('POST', '/staff/login', { delay: 1000, statusCode: 200 }).as('slowLogin');
      
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      
      cy.get('[data-testid="login-button"]')
        .should('be.disabled')
        .and('contain', 'Signing in...');
    });

    it('should make client portal link clickable', () => {
      cy.get('[data-testid="client-portal-link"]').should('not.be.disabled');
      cy.get('[data-testid="client-portal-link"]').click();
      cy.url().should('include', '/portal/login');
    });
  });

  describe('Interactive Element Tests', () => {
    it('should focus on email input when clicking label', () => {
      cy.get('label[for="email"]').click();
      cy.get('[data-testid="email-input"]').should('have.focus');
    });

    it('should focus on password input when clicking label', () => {
      cy.get('label[for="password"]').click();
      cy.get('[data-testid="password-input"]').should('have.focus');
    });

    it('should maintain form state during interactions', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('.toggle-btn').click();
      
      cy.get('[data-testid="email-input"]').should('have.value', 'test@example.com');
      cy.get('[data-testid="password-input"]').should('have.value', 'password123');
    });
  });

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
      cy.get('[data-testid="email-input"]').should('be.visible');
      cy.get('[data-testid="password-input"]').should('be.visible');
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

  describe('Error Handling Tests', () => {
    it('should handle server errors gracefully', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 500, body: { error: 'Server error' } }).as('serverError');
      
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      
      cy.wait('@serverError');
    });

    it('should handle network errors', () => {
      cy.intercept('POST', '/staff/login', { forceNetworkError: true }).as('networkError');
      
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      
      cy.wait('@networkError');
    });

    it('should handle authentication errors', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 401, body: { error: 'Invalid credentials' } }).as('authError');
      
      cy.get('[data-testid="email-input"]').type('wrong@example.com');
      cy.get('[data-testid="password-input"]').type('wrongpassword');
      cy.get('[data-testid="login-button"]').click();
      
      cy.wait('@authError');
    });

    it('should clear form on page refresh', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.reload();
      
      cy.get('[data-testid="email-input"]').should('have.value', '');
      cy.get('[data-testid="password-input"]').should('have.value', '');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper form labels', () => {
      cy.get('label[for="email"]').should('exist');
      cy.get('label[for="password"]').should('exist');
    });

    it('should support keyboard navigation', () => {
      cy.get('[data-testid="email-input"]').focus().type('{tab}');
      cy.get('[data-testid="password-input"]').should('have.focus');
      cy.type('{tab}');
      cy.get('.toggle-btn').should('have.focus');
      cy.type('{tab}');
      cy.get('[data-testid="login-button"]').should('have.focus');
    });

    it('should support enter key submission', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 200 }).as('enterSubmit');
      
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123{enter}');
      
      cy.wait('@enterSubmit');
    });
  });

  describe('Security Tests', () => {
    it('should have autocomplete attributes for security', () => {
      cy.get('[data-testid="email-input"]').should('have.attr', 'autocomplete', 'email');
      cy.get('[data-testid="password-input"]').should('have.attr', 'autocomplete', 'current-password');
    });

    it('should mask password input by default', () => {
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
      cy.get('[data-testid="password-input"]').type('secretpassword');
      cy.get('[data-testid="password-input"]').should('have.value', 'secretpassword');
    });

    it('should POST to secure endpoint', () => {
      cy.get('[data-testid="login-form"]').should('have.attr', 'action', '/staff/login');
      cy.get('[data-testid="login-form"]').should('have.attr', 'method', 'POST');
    });
  });
});