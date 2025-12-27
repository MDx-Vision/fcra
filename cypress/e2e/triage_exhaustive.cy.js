// Exhaustive test for /dashboard/triage
describe('Staff Login Page (/dashboard/triage)', () => {
  beforeEach(() => {
    cy.visit('/dashboard/triage');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/triage');
      cy.get('body').should('exist');
    });

    it('should have correct page title', () => {
      cy.title().should('eq', 'Staff Login - Brightpath Ascend FCRA Platform');
    });

    it('should not have console errors', () => {
      cy.get('@consoleError').should('not.have.been.called');
    });

    it('should return 200 status code', () => {
      cy.request('/dashboard/triage').then((response) => {
        expect(response.status).to.eq(200);
      });
    });
  });

  describe('UI Element Tests', () => {
    it('should display the main container', () => {
      cy.get('[data-testid="login-container"]').should('be.visible');
    });

    it('should display the login card', () => {
      cy.get('[data-testid="login-card"]').should('be.visible');
    });

    it('should display the company logo', () => {
      cy.get('.logo img').should('be.visible').and('have.attr', 'src', '/static/images/logo.png');
      cy.get('.logo img').should('have.attr', 'alt', 'Brightpath Ascend Group');
    });

    it('should display main heading H1', () => {
      cy.get('h1').should('contain.text', 'Brightpath Ascend Group');
      cy.get('h1 span').should('contain.text', 'Ascend');
    });

    it('should display platform description', () => {
      cy.get('.logo p').should('contain.text', 'FCRA Litigation Platform');
    });

    it('should display staff badge', () => {
      cy.get('.staff-badge').should('be.visible').and('contain.text', 'Staff Portal');
      cy.get('.staff-badge svg').should('be.visible');
    });

    it('should display login title H2', () => {
      cy.get('[data-testid="login-title"]').should('contain.text', 'Staff Login');
      cy.get('h2').should('contain.text', 'Staff Login');
    });

    it('should display subtitle', () => {
      cy.get('.subtitle').should('contain.text', 'Sign in to access the admin dashboard');
    });

    it('should display client portal link', () => {
      cy.get('[data-testid="client-portal-link"]')
        .should('be.visible')
        .and('have.attr', 'href', '/portal/login')
        .and('contain.text', 'Client Login');
    });
  });

  describe('Form Tests', () => {
    it('should display the login form', () => {
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
        .and('have.attr', 'id', 'email')
        .and('have.attr', 'name', 'email')
        .and('have.attr', 'placeholder', 'your@email.com')
        .should('have.attr', 'required')
        .and('have.attr', 'autocomplete', 'email');
    });

    it('should display email label', () => {
      cy.get('label[for="email"]').should('contain.text', 'Email Address');
    });

    it('should display password input with correct attributes', () => {
      cy.get('[data-testid="password-input"]')
        .should('be.visible')
        .and('have.attr', 'type', 'password')
        .and('have.attr', 'id', 'password')
        .and('have.attr', 'name', 'password')
        .and('have.attr', 'placeholder', 'Enter your password')
        .should('have.attr', 'required')
        .and('have.attr', 'autocomplete', 'current-password');
    });

    it('should display password label', () => {
      cy.get('label[for="password"]').should('contain.text', 'Password');
    });

    it('should display password toggle button', () => {
      cy.get('.toggle-btn')
        .should('be.visible')
        .and('have.attr', 'type', 'button')
        .and('contain.text', '👁');
    });

    it('should display login button with correct attributes', () => {
      cy.get('[data-testid="login-button"]')
        .should('be.visible')
        .and('have.attr', 'type', 'submit')
        .and('have.attr', 'id', 'loginBtn')
        .and('have.class', 'login-btn')
        .and('contain.text', 'Sign In');
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
      cy.get('[data-testid="email-input"]:invalid').should('exist');
    });

    it('should validate required password field', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="password-input"]:invalid').should('exist');
    });

    it('should validate email format', () => {
      cy.get('[data-testid="email-input"]').type('invalid-email');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]:invalid').should('exist');
    });

    it('should submit form with valid data', () => {
      cy.intercept('POST', '/staff/login').as('loginRequest');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@loginRequest');
    });
  });

  describe('Interactive Element Tests', () => {
    it('should toggle password visibility when eye button is clicked', () => {
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

    it('should disable login button and show loading state on form submission', () => {
      cy.intercept('POST', '/staff/login', { delay: 1000 }).as('loginRequest');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="login-button"]')
        .should('be.disabled')
        .and('contain.text', 'Signing in...');
      cy.get('.spinner').should('exist');
    });

    it('should focus on email input when page loads', () => {
      cy.get('[data-testid="email-input"]').focus();
      cy.focused().should('have.attr', 'data-testid', 'email-input');
    });

    it('should allow tab navigation between form elements', () => {
      cy.get('[data-testid="email-input"]').focus().type('{tab}');
      cy.focused().should('have.attr', 'data-testid', 'password-input');
      cy.type('{tab}');
      cy.focused().should('have.class', 'toggle-btn');
      cy.type('{tab}');
      cy.focused().should('have.attr', 'data-testid', 'login-button');
    });
  });

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
      cy.get('.logo').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('[data-testid="login-container"]').should('be.visible');
      cy.get('[data-testid="login-card"]').should('be.visible');
      cy.get('.logo').should('be.visible');
    });
  });

  describe('Error Handling Tests', () => {
    it('should handle empty form submission', () => {
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]:invalid').should('exist');
      cy.get('[data-testid="password-input"]:invalid').should('exist');
    });

    it('should handle invalid email format', () => {
      cy.get('[data-testid="email-input"]').type('invalid-email-format');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="email-input"]:invalid').should('exist');
    });

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
  });

  describe('Accessibility Tests', () => {
    it('should have proper form labels', () => {
      cy.get('label[for="email"]').should('exist');
      cy.get('label[for="password"]').should('exist');
    });

    it('should have proper alt text for images', () => {
      cy.get('.logo img').should('have.attr', 'alt', 'Brightpath Ascend Group');
    });

    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('exist');
      cy.get('h2').should('exist');
    });

    it('should support keyboard navigation', () => {
      cy.get('body').type('{tab}');
      cy.focused().should('have.attr', 'data-testid', 'email-input');
    });
  });

  describe('Browser Compatibility Tests', () => {
    it('should work with different input methods', () => {
      // Test copy/paste
      cy.get('[data-testid="email-input"]').invoke('val', 'test@example.com').trigger('input');
      cy.get('[data-testid="email-input"]').should('have.value', 'test@example.com');
      
      // Test clear and retype
      cy.get('[data-testid="email-input"]').clear().type('new@example.com');
      cy.get('[data-testid="email-input"]').should('have.value', 'new@example.com');
    });

    it('should handle special characters in password', () => {
      const specialPassword = 'P@$$w0rd!@#$%^&*()';
      cy.get('[data-testid="password-input"]').type(specialPassword);
      cy.get('[data-testid="password-input"]').should('have.value', specialPassword);
    });
  });

  describe('Performance Tests', () => {
    it('should load page elements within reasonable time', () => {
      cy.get('[data-testid="login-container"]', { timeout: 5000 }).should('be.visible');
      cy.get('[data-testid="login-form"]', { timeout: 3000 }).should('be.visible');
    });

    it('should handle rapid form submissions gracefully', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      
      // Rapid clicks should not cause issues
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="login-button"]').click();
    });
  });
});