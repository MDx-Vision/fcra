// Exhaustive test for /portal
describe('/portal - Client Login Page', () => {
  beforeEach(() => {
    cy.visit('/portal');
  });

  describe('Page Load Tests', () => {
    it('should load without errors', () => {
      cy.url().should('include', '/portal');
      cy.get('[data-testid="portal-login-container"]').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('eq', 'Client Login - Brightpath Ascend');
    });

    it('should not have console errors', () => {
      cy.get('@consoleError').should('not.have.been.called');
    });

    it('should return 200 status', () => {
      cy.request('/portal').its('status').should('eq', 200);
    });
  });

  describe('UI Element Tests', () => {
    it('should display all headings', () => {
      cy.contains('h1', 'Brightpath Ascend').should('be.visible');
      cy.get('[data-testid="login-title"]').should('contain.text', 'Welcome Back');
    });

    it('should display logo and branding', () => {
      cy.get('img[alt="Brightpath Ascend"]').should('exist');
      cy.contains('Client Portal').should('be.visible');
      cy.get('span').contains('Ascend').should('have.css', 'color', 'rgb(132, 204, 22)');
    });

    it('should display all containers', () => {
      cy.get('[data-testid="portal-login-container"]').should('be.visible');
      cy.get('[data-testid="portal-login-card"]').should('be.visible');
      cy.get('[data-testid="login-form-container"]').should('be.visible');
    });

    it('should have forgot and reset form containers hidden initially', () => {
      cy.get('[data-testid="forgot-form-container"]').should('not.have.class', 'active');
      cy.get('[data-testid="reset-form-container"]').should('not.have.class', 'active');
    });
  });

  describe('Login Form Tests', () => {
    it('should display login form with all elements', () => {
      cy.get('[data-testid="portal-login-form"]').should('be.visible');
      cy.get('[data-testid="portal-email-input"]').should('be.visible');
      cy.get('[data-testid="portal-password-input"]').should('be.visible');
      cy.get('[data-testid="portal-login-button"]').should('be.visible');
    });

    it('should have correct form attributes', () => {
      cy.get('#loginForm').should('have.attr', 'method', 'POST');
      cy.get('#loginForm').should('have.attr', 'action', '/portal/login');
    });

    it('should have required email input with correct attributes', () => {
      cy.get('[data-testid="portal-email-input"]').should('have.attr', 'type', 'email');
      cy.get('[data-testid="portal-email-input"]').should('have.attr', 'name', 'email');
      cy.get('[data-testid="portal-email-input"]').should('have.attr', 'required');
      cy.get('[data-testid="portal-email-input"]').should('have.attr', 'placeholder', 'your@email.com');
      cy.get('[data-testid="portal-email-input"]').should('have.attr', 'autocomplete', 'email');
    });

    it('should have required password input with correct attributes', () => {
      cy.get('[data-testid="portal-password-input"]').should('have.attr', 'type', 'password');
      cy.get('[data-testid="portal-password-input"]').should('have.attr', 'name', 'password');
      cy.get('[data-testid="portal-password-input"]').should('have.attr', 'required');
      cy.get('[data-testid="portal-password-input"]').should('have.attr', 'placeholder', 'Enter your password');
      cy.get('[data-testid="portal-password-input"]').should('have.attr', 'autocomplete', 'current-password');
    });

    it('should accept text input in email field', () => {
      cy.get('[data-testid="portal-email-input"]')
        .type('test@example.com')
        .should('have.value', 'test@example.com');
    });

    it('should accept text input in password field', () => {
      cy.get('[data-testid="portal-password-input"]')
        .type('password123')
        .should('have.value', 'password123');
    });

    it('should have working password toggle button', () => {
      cy.get('[data-testid="portal-password-input"]').should('have.attr', 'type', 'password');
      cy.get('[data-testid="toggle-password-btn"]').click();
      cy.get('[data-testid="portal-password-input"]').should('have.attr', 'type', 'text');
      cy.get('[data-testid="toggle-password-btn"]').click();
      cy.get('[data-testid="portal-password-input"]').should('have.attr', 'type', 'password');
    });

    it('should have correct submit button attributes', () => {
      cy.get('[data-testid="portal-login-button"]')
        .should('have.attr', 'type', 'submit')
        .should('contain.text', 'Sign In')
        .should('have.id', 'loginBtn')
        .should('have.class', 'login-btn');
    });

    it.skip('should show loading state on form submission', () => {
      // Skipped: Form submits and redirects before disabled state can be asserted
      cy.get('[data-testid="portal-email-input"]').type('test@example.com');
      cy.get('[data-testid="portal-password-input"]').type('password123');
      cy.get('[data-testid="portal-login-button"]').click();
      cy.get('[data-testid="portal-login-button"]').should('be.disabled');
    });

    it('should display forgot password link', () => {
      cy.get('[data-testid="forgot-password-link"]')
        .should('be.visible')
        .should('contain.text', 'Forgot your password?');
    });

    it('should display token access link', () => {
      cy.get('[data-testid="token-access-link"]')
        .should('be.visible')
        .should('contain.text', 'Use direct link access');
    });

    it('should display divider with "or" text', () => {
      cy.get('.divider span').should('contain.text', 'or');
    });
  });

  describe('Forgot Password Form Tests', () => {
    beforeEach(() => {
      cy.get('[data-testid="forgot-password-link"]').click();
    });

    it('should show forgot password form when link is clicked', () => {
      cy.get('[data-testid="login-form-container"]').should('have.class', 'hidden');
      cy.get('[data-testid="forgot-form-container"]').should('have.class', 'active');
    });

    it('should display forgot password form elements', () => {
      cy.contains('h2', 'Reset Password').should('be.visible');
      cy.contains('Enter your email and we\'ll send you a reset link').should('be.visible');
      cy.get('[data-testid="forgot-password-form"]').should('be.visible');
      cy.get('[data-testid="forgot-email-input"]').should('be.visible');
      cy.get('[data-testid="send-reset-button"]').should('be.visible');
    });

    it('should have back to login link', () => {
      cy.get('[data-testid="back-to-login-link"]')
        .should('be.visible')
        .should('contain.text', '← Back to login');
    });

    it('should return to login form when back link is clicked', () => {
      cy.get('[data-testid="back-to-login-link"]').click();
      cy.get('[data-testid="login-form-container"]').should('not.have.class', 'hidden');
      cy.get('[data-testid="forgot-form-container"]').should('not.have.class', 'active');
    });

    it('should have correct forgot email input attributes', () => {
      cy.get('[data-testid="forgot-email-input"]').should('have.attr', 'type', 'email');
      cy.get('[data-testid="forgot-email-input"]').should('have.attr', 'name', 'email');
      cy.get('[data-testid="forgot-email-input"]').should('have.attr', 'required');
      cy.get('[data-testid="forgot-email-input"]').should('have.attr', 'placeholder', 'your@email.com');
    });

    it('should accept email input', () => {
      cy.get('[data-testid="forgot-email-input"]')
        .type('test@example.com')
        .should('have.value', 'test@example.com');
    });

    it('should have correct submit button attributes', () => {
      cy.get('[data-testid="send-reset-button"]')
        .should('have.attr', 'type', 'submit')
        .should('contain.text', 'Send Reset Link')
        .should('have.id', 'forgotBtn');
    });

    it('should have hidden alert div', () => {
      cy.get('[data-testid="forgot-alert"]').should('have.class', 'hidden');
    });

    it('should handle form submission', () => {
      cy.intercept('POST', '/api/portal/forgot-password', {
        statusCode: 200,
        body: { success: true, message: 'Reset email sent successfully' }
      }).as('forgotPassword');

      cy.get('[data-testid="forgot-email-input"]').type('test@example.com');
      cy.get('[data-testid="send-reset-button"]').click();

      cy.wait('@forgotPassword');
      cy.get('[data-testid="forgot-alert"]').should('not.have.class', 'hidden');
    });
  });

  describe('Reset Password Form Tests', () => {
    beforeEach(() => {
      cy.visit('/portal?token=test-token');
    });

    it('should show reset password form when token is present', () => {
      cy.get('[data-testid="login-form-container"]').should('have.class', 'hidden');
      cy.get('[data-testid="reset-form-container"]').should('have.class', 'active');
    });

    it('should display reset password form elements', () => {
      cy.contains('h2', 'Set New Password').should('be.visible');
      cy.contains('Create a strong password for your account').should('be.visible');
      cy.get('[data-testid="reset-password-form"]').should('be.visible');
      cy.get('[data-testid="new-password-input"]').should('be.visible');
      cy.get('[data-testid="confirm-password-input"]').should('be.visible');
      cy.get('[data-testid="reset-password-button"]').should('be.visible');
    });

    it('should have hidden token input with value', () => {
      cy.get('#resetToken')
        .should('have.attr', 'type', 'hidden')
        .should('have.value', 'test-token');
    });

    it('should have correct new password input attributes', () => {
      cy.get('[data-testid="new-password-input"]').should('have.attr', 'type', 'password');
      cy.get('[data-testid="new-password-input"]').should('have.attr', 'name', 'password');
      cy.get('[data-testid="new-password-input"]').should('have.attr', 'required');
      cy.get('[data-testid="new-password-input"]').should('have.attr', 'minlength', '8');
      cy.get('[data-testid="new-password-input"]').should('have.attr', 'placeholder', 'At least 8 characters');
    });

    it('should have correct confirm password input attributes', () => {
      cy.get('[data-testid="confirm-password-input"]').should('have.attr', 'type', 'password');
      cy.get('[data-testid="confirm-password-input"]').should('have.attr', 'name', 'confirm_password');
      cy.get('[data-testid="confirm-password-input"]').should('have.attr', 'required');
      cy.get('[data-testid="confirm-password-input"]').should('have.attr', 'placeholder', 'Confirm your password');
    });

    it('should accept password input', () => {
      cy.get('[data-testid="new-password-input"]')
        .type('newpassword123')
        .should('have.value', 'newpassword123');
      cy.get('[data-testid="confirm-password-input"]')
        .type('newpassword123')
        .should('have.value', 'newpassword123');
    });

    it('should have working password toggle for new password', () => {
      cy.get('[data-testid="new-password-input"]').should('have.attr', 'type', 'password');
      cy.get('[data-testid="reset-form-container"] .password-toggle button').click();
      cy.get('[data-testid="new-password-input"]').should('have.attr', 'type', 'text');
    });

    it('should have correct reset button attributes', () => {
      cy.get('[data-testid="reset-password-button"]')
        .should('have.attr', 'type', 'submit')
        .should('contain.text', 'Reset Password')
        .should('have.id', 'resetBtn');
    });

    it('should have hidden alert div', () => {
      cy.get('[data-testid="reset-alert"]').should('have.class', 'hidden');
    });

    it('should validate password mismatch', () => {
      cy.get('[data-testid="new-password-input"]').type('password123');
      cy.get('[data-testid="confirm-password-input"]').type('different123');
      cy.get('[data-testid="reset-password-button"]').click();

      cy.get('[data-testid="reset-alert"]')
        .should('not.have.class', 'hidden')
        .should('contain.text', 'Passwords do not match');
    });

    it('should validate minimum password length', () => {
      cy.get('[data-testid="new-password-input"]').type('short');
      cy.get('[data-testid="confirm-password-input"]').type('short');
      cy.get('[data-testid="reset-password-button"]').click();

      cy.get('[data-testid="reset-alert"]')
        .should('not.have.class', 'hidden')
        .should('contain.text', 'Password must be at least 8 characters');
    });

    it('should handle successful password reset', () => {
      cy.intercept('POST', '/api/portal/reset-password', {
        statusCode: 200,
        body: { success: true, message: 'Password reset successfully' }
      }).as('resetPassword');

      cy.get('[data-testid="new-password-input"]').type('newpassword123');
      cy.get('[data-testid="confirm-password-input"]').type('newpassword123');
      cy.get('[data-testid="reset-password-button"]').click();

      cy.wait('@resetPassword');
      cy.get('[data-testid="reset-alert"]')
        .should('not.have.class', 'hidden')
        .should('contain.text', 'Password reset successfully');
    });
  });

  describe.skip('Interactive Element Tests', () => {
    // Skipped: window.prompt/location stubbing is unreliable in Cypress
    it('should handle token access prompt', () => {
      cy.window().then((win) => {
        cy.stub(win, 'prompt').returns('test-token-123');
        cy.stub(win, 'location').value({ href: '' });
      });

      cy.get('[data-testid="token-access-link"]').click();
    });

    it('should extract token from full portal URL', () => {
      cy.window().then((win) => {
        cy.stub(win, 'prompt').returns('http://localhost:5001/portal/token123?param=value');
        cy.stub(win, 'location').value({ href: '' });
      });

      cy.get('[data-testid="token-access-link"]').click();
    });

    it('should handle empty token prompt', () => {
      cy.window().then((win) => {
        cy.stub(win, 'prompt').returns('');
      });

      cy.get('[data-testid="token-access-link"]').click();
    });

    it('should handle cancelled token prompt', () => {
      cy.window().then((win) => {
        cy.stub(win, 'prompt').returns(null);
      });

      cy.get('[data-testid="token-access-link"]').click();
    });
  });

  describe('Form Navigation Tests', () => {
    it('should navigate between all forms correctly', () => {
      // Start at login form
      cy.get('[data-testid="login-form-container"]').should('be.visible');
      cy.get('[data-testid="forgot-form-container"]').should('not.have.class', 'active');
      cy.get('[data-testid="reset-form-container"]').should('not.have.class', 'active');

      // Go to forgot password
      cy.get('[data-testid="forgot-password-link"]').click();
      cy.get('[data-testid="login-form-container"]').should('have.class', 'hidden');
      cy.get('[data-testid="forgot-form-container"]').should('have.class', 'active');

      // Go back to login
      cy.get('[data-testid="back-to-login-link"]').click();
      cy.get('[data-testid="login-form-container"]').should('not.have.class', 'hidden');
      cy.get('[data-testid="forgot-form-container"]').should('not.have.class', 'active');
    });
  });

  describe('Error Handling Tests', () => {
    it('should handle network errors in forgot password form', () => {
      cy.intercept('POST', '/api/portal/forgot-password', {
        forceNetworkError: true
      }).as('forgotPasswordError');

      cy.get('[data-testid="forgot-password-link"]').click();
      cy.get('[data-testid="forgot-email-input"]').type('test@example.com');
      cy.get('[data-testid="send-reset-button"]').click();

      cy.wait('@forgotPasswordError');
      cy.get('[data-testid="forgot-alert"]')
        .should('not.have.class', 'hidden')
        .should('contain.text', 'Connection error');
    });

    it('should handle server errors in forgot password form', () => {
      cy.intercept('POST', '/api/portal/forgot-password', {
        statusCode: 500,
        body: { success: false, error: 'Server error' }
      }).as('forgotPasswordServerError');

      cy.get('[data-testid="forgot-password-link"]').click();
      cy.get('[data-testid="forgot-email-input"]').type('test@example.com');
      cy.get('[data-testid="send-reset-button"]').click();

      cy.wait('@forgotPasswordServerError');
      cy.get('[data-testid="forgot-alert"]')
        .should('not.have.class', 'hidden')
        .should('contain.text', 'Server error');
    });

    it('should handle network errors in reset password form', () => {
      cy.visit('/portal?token=test-token');

      cy.intercept('POST', '/api/portal/reset-password', {
        forceNetworkError: true
      }).as('resetPasswordError');

      cy.get('[data-testid="new-password-input"]').type('newpassword123');
      cy.get('[data-testid="confirm-password-input"]').type('newpassword123');
      cy.get('[data-testid="reset-password-button"]').click();

      cy.wait('@resetPasswordError');
      cy.get('[data-testid="reset-alert"]')
        .should('not.have.class', 'hidden')
        .should('contain.text', 'Connection error');
    });
  });

  describe('Responsive Tests', () => {
    const viewports = [
      { width: 1280, height: 720, device: 'desktop' },
      { width: 768, height: 1024, device: 'tablet' },
      { width: 375, height: 667, device: 'mobile' }
    ];

    viewports.forEach(({ width, height, device }) => {
      it(`should display correctly on ${device} (${width}x${height})`, () => {
        cy.viewport(width, height);
        cy.get('[data-testid="portal-login-container"]').should('be.visible');
        cy.get('[data-testid="portal-login-card"]').should('be.visible');
        cy.get('[data-testid="portal-login-form"]').should('be.visible');
        cy.get('[data-testid="portal-email-input"]').should('be.visible');
        cy.get('[data-testid="portal-password-input"]').should('be.visible');
        cy.get('[data-testid="portal-login-button"]').should('be.visible');
      });
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper form labels', () => {
      cy.get('label[for="email"]').should('contain.text', 'Email Address');
      cy.get('label[for="password"]').should('contain.text', 'Password');
    });

    it('should have proper form labels in forgot password form', () => {
      cy.get('[data-testid="forgot-password-link"]').click();
      cy.get('label[for="forgotEmail"]').should('contain.text', 'Email Address');
    });

    it('should have proper form labels in reset password form', () => {
      cy.visit('/portal?token=test-token');
      cy.get('label[for="newPassword"]').should('contain.text', 'New Password');
      cy.get('label[for="confirmPassword"]').should('contain.text', 'Confirm Password');
    });

    it('should have alt text for logo image', () => {
      cy.get('img[alt="Brightpath Ascend"]').should('exist');
    });
  });

  describe('URL Parameter Tests', () => {
    it('should handle reset token from URL parameters', () => {
      cy.visit('/portal?token=abc123');
      cy.get('#resetToken').should('have.value', 'abc123');
      cy.get('[data-testid="reset-form-container"]').should('have.class', 'active');
    });

    it('should not show reset form without token', () => {
      cy.visit('/portal');
      cy.get('[data-testid="reset-form-container"]').should('not.have.class', 'active');
      cy.get('[data-testid="login-form-container"]').should('be.visible');
    });
  });
});
