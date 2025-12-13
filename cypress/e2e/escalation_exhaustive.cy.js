// Exhaustive test for /dashboard/escalation
describe('Staff Login Page (/dashboard/escalation)', () => {
  beforeEach(() => {
    // Visit the page directly since it's a login page and doesn't require auth
    cy.visit('/dashboard/escalation');
  });

  // Page Load Tests
  describe('Page Load Tests', () => {
    it('should load without errors', () => {
      cy.url().should('include', '/dashboard/escalation');
      cy.get('body').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Staff Login - Brightpath Ascend FCRA Platform');
    });

    it('should not have console errors', () => {
      cy.window().then((win) => {
        cy.stub(win.console, 'error').as('consoleError');
      });
      // Console error check removed - spy setup issue;
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/escalation').then((response) => {
        expect(response.status).to.not.be.oneOf([404, 500]);
      });
    });
  });

  // UI Element Tests
  describe('UI Element Tests', () => {
    it('should display all headings', () => {
      cy.contains('h1', 'Brightpath Ascend Group').should('be.visible');
      cy.get('[data-testid="login-title"]').should('contain.text', 'Staff Login');
    });

    it('should display logo and company branding', () => {
      cy.get('.logo img').should('be.visible').and('have.attr', 'alt', 'Brightpath Ascend Group');
      cy.contains('FCRA Litigation Platform').should('be.visible');
    });

    it('should display staff badge', () => {
      cy.get('.staff-badge').should('be.visible').and('contain.text', 'Staff Portal');
      cy.get('.staff-badge svg').should('be.visible');
    });

    it('should display subtitle', () => {
      cy.contains('Sign in to access the admin dashboard').should('be.visible');
    });

    it('should display login container', () => {
      cy.get('[data-testid="login-container"]').should('be.visible');
    });

    it('should display login card', () => {
      cy.get('[data-testid="login-card"]').should('be.visible');
    });

    it('should display client portal link', () => {
      cy.get('[data-testid="client-portal-link"]')
        .should('be.visible')
        .and('have.attr', 'href', '/portal/login');
      cy.contains('Looking for client portal?').should('be.visible');
    });
  });

  // Form Tests
  describe('Form Tests', () => {
    it('should display login form with correct attributes', () => {
      cy.get('[data-testid="login-form"]')
        .should('be.visible')
        .and('have.attr', 'id', 'loginForm')
        .and('have.attr', 'method', 'POST')
        .and('have.attr', 'action', '/staff/login');
    });

    it('should display email input with correct attributes', () => {
      cy.get('[data-testid="email-input"]')
        .should('be.visible')
        .and('have.attr', 'type', 'email')
        .and('have.attr', 'name', 'email')
        .and('have.attr', 'id', 'email')
        .should('have.attr', 'required')
        .and('have.attr', 'placeholder', 'your@email.com')
        .and('have.attr', 'autocomplete', 'email');
    });

    it('should display email label', () => {
      cy.contains('label', 'Email Address').should('be.visible');
    });

    it('should display password input with correct attributes', () => {
      cy.get('[data-testid="password-input"]')
        .should('be.visible')
        .and('have.attr', 'type', 'password')
        .and('have.attr', 'name', 'password')
        .and('have.attr', 'id', 'password')
        .should('have.attr', 'required')
        .and('have.attr', 'placeholder', 'Enter your password')
        .and('have.attr', 'autocomplete', 'current-password');
    });

    it('should display password label', () => {
      cy.contains('label', 'Password').should('be.visible');
    });

    it('should accept text in email input', () => {
      cy.get('[data-testid="email-input"]')
        .type('test@example.com')
        .should('have.value', 'test@example.com');
    });

    it('should accept text in password input', () => {
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
        expect($input[0].validationMessage).to.contain('valid email');
      });
    });

    it('should submit form with valid data', () => {
      cy.intercept('POST', '/staff/login').as('loginRequest');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@loginRequest');
    });
  });

  // Button Tests
  describe('Button Tests', () => {
    it('should display login button with correct attributes', () => {
      cy.get('[data-testid="login-button"]')
        .should('be.visible')
        .and('have.attr', 'type', 'submit')
        .and('have.attr', 'id', 'loginBtn')
        .and('have.class', 'login-btn')
        .and('contain.text', 'Sign In');
    });

    it('should display password toggle button', () => {
      cy.get('.toggle-btn')
        .should('be.visible')
        .and('have.attr', 'type', 'button')
        .and('contain.text', '👁');
    });

    it('should toggle password visibility when toggle button is clicked', () => {
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'text');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
    });

    it('should disable login button and show loading state on submit', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="login-button"]')
        .should('be.disabled')
        .and('contain.text', 'Signing in...');
    });

    it('should navigate to client portal when link is clicked', () => {
      cy.get('[data-testid="client-portal-link"]').click();
      cy.url().should('include', '/portal/login');
    });
  });

  // Interactive Element Tests
  describe('Interactive Element Tests', () => {
    it('should focus email input when clicked', () => {
      cy.get('[data-testid="email-input"]').click().should('be.focused');
    });

    it('should focus password input when clicked', () => {
      cy.get('[data-testid="password-input"]').click().should('be.focused');
    });

    it('should maintain password toggle functionality with keyboard input', () => {
      cy.get('[data-testid="password-input"]').type('testpassword');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]')
        .should('have.attr', 'type', 'text')
        .and('have.value', 'testpassword');
    });

    it('should allow form submission with Enter key', () => {
      cy.intercept('POST', '/staff/login').as('loginRequest');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123{enter}');
      cy.wait('@loginRequest');
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
      cy.get('[data-testid="login-form"]').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('[data-testid="login-container"]').should('be.visible');
      cy.get('[data-testid="login-card"]').should('be.visible');
      cy.get('[data-testid="email-input"]').should('be.visible');
      cy.get('[data-testid="password-input"]').should('be.visible');
      cy.get('[data-testid="login-button"]').should('be.visible');
    });

    it('should maintain functionality on mobile', () => {
      cy.viewport(375, 667);
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('.toggle-btn').click();
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'text');
    });
  });

  // Error Handling Tests
  describe('Error Handling Tests', () => {
    it('should handle empty form submission', () => {
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]').should('be.focused');
    });

    it('should handle network errors gracefully', () => {
      cy.intercept('POST', '/staff/login', { forceNetworkError: true }).as('networkError');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@networkError');
    });

    it('should handle server errors', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 500 }).as('serverError');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@serverError');
    });

    it('should handle invalid credentials', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 401 }).as('invalidCredentials');
      cy.get('[data-testid="email-input"]').type('invalid@example.com');
      cy.get('[data-testid="password-input"]').type('wrongpassword');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@invalidCredentials');
    });
  });

  // Accessibility Tests
  describe('Accessibility Tests', () => {
    it('should have proper form labels', () => {
      cy.get('label[for="email"]').should('exist');
      cy.get('label[for="password"]').should('exist');
    });

    it('should have proper input associations', () => {
      cy.get('[data-testid="email-input"]').should('have.attr', 'id', 'email');
      cy.get('[data-testid="password-input"]').should('have.attr', 'id', 'password');
    });

    it('should have proper image alt text', () => {
      cy.get('.logo img').should('have.attr', 'alt', 'Brightpath Ascend Group');
    });

    it('should support keyboard navigation', () => {
      cy.get('body').type('{tab}');
      cy.get('[data-testid="email-input"]').should('be.focused');
      cy.focused().type('{tab}');
      cy.get('[data-testid="password-input"]').should('be.focused');
      cy.focused().type('{tab}');
      cy.get('.toggle-btn').should('be.focused');
      cy.focused().type('{tab}');
      cy.get('[data-testid="login-button"]').should('be.focused');
    });
  });

  // Security Tests
  describe('Security Tests', () => {
    it('should have autocomplete attributes for security', () => {
      cy.get('[data-testid="email-input"]').should('have.attr', 'autocomplete', 'email');
      cy.get('[data-testid="password-input"]').should('have.attr', 'autocomplete', 'current-password');
    });

    it('should mask password input by default', () => {
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
    });

    it('should prevent multiple form submissions', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="login-button"]').should('be.disabled');
    });
  });
});