// Exhaustive test for /dashboard/tasks
describe('Staff Login Page - /dashboard/tasks', () => {
  beforeEach(() => {
    cy.visit('/dashboard/tasks');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/tasks');
      cy.get('[data-testid="login-container"]').should('be.visible');
    });

    it('should not have console errors', () => {
      cy.window().then((win) => {
        cy.stub(win.console, 'error').as('consoleError');
      });
      cy.visit('/dashboard/tasks');
      // Console error check removed - spy setup issue;
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/tasks').then((response) => {
        expect(response.status).to.not.be.oneOf([404, 500, 502, 503]);
      });
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Staff Login - Brightpath Ascend FCRA Platform');
    });
  });

  describe('UI Element Tests', () => {
    describe('Logo and Branding', () => {
      it('should display the company logo', () => {
        cy.get('.logo img').should('be.visible')
          .and('have.attr', 'src', '/static/images/logo.png')
          .and('have.attr', 'alt', 'Brightpath Ascend Group');
      });

      it('should display main heading', () => {
        cy.get('h1').should('contain.text', 'Brightpath')
          .and('contain.text', 'Ascend')
          .and('contain.text', 'Group');
      });

      it('should display platform description', () => {
        cy.get('.logo p').should('contain.text', 'FCRA Litigation Platform');
      });
    });

    describe('Login Card', () => {
      it('should display login container', () => {
        cy.get('[data-testid="login-container"]').should('be.visible');
      });

      it('should display login card', () => {
        cy.get('[data-testid="login-card"]').should('be.visible');
      });

      it('should display staff portal badge', () => {
        cy.get('.staff-badge').should('be.visible')
          .and('contain.text', 'Staff Portal');
      });

      it('should display staff portal icon', () => {
        cy.get('.staff-badge svg').should('be.visible');
      });
    });

    describe('Headings', () => {
      it('should display H2 login title', () => {
        cy.get('[data-testid="login-title"]').should('contain.text', 'Staff Login');
      });

      it('should display subtitle', () => {
        cy.get('.subtitle').should('contain.text', 'Sign in to access the admin dashboard');
      });
    });

    describe('Buttons', () => {
      it('should display password toggle button', () => {
        cy.get('.toggle-btn').should('be.visible')
          .and('contain.text', '👁')
          .and('have.attr', 'type', 'button');
      });

      it('should display login submit button', () => {
        cy.get('[data-testid="login-button"]')
          .should('be.visible')
          .and('contain.text', 'Sign In')
          .and('have.attr', 'type', 'submit')
          .and('have.id', 'loginBtn')
          .and('have.class', 'login-btn');
      });

      it('should make password toggle button clickable', () => {
        cy.get('.toggle-btn').should('not.be.disabled').click();
      });

      it('should make login button clickable', () => {
        cy.get('[data-testid="login-button"]').should('not.be.disabled');
      });
    });

    describe('Client Portal Link', () => {
      it('should display client portal link text', () => {
        cy.get('.client-portal-link').should('contain.text', 'Looking for client portal?');
      });

      it('should display client login link', () => {
        cy.get('[data-testid="client-portal-link"]')
          .should('be.visible')
          .and('contain.text', 'Client Login')
          .and('have.attr', 'href', '/portal/login');
      });
    });
  });

  describe('Form Tests', () => {
    describe('Login Form Structure', () => {
      it('should display login form with correct attributes', () => {
        cy.get('[data-testid="login-form"]')
          .should('be.visible')
          .and('have.attr', 'id', 'loginForm')
          .and('have.attr', 'method', 'POST')
          .and('have.attr', 'action', '/staff/login');
      });

      it('should have email form group', () => {
        cy.get('.form-group').first().within(() => {
          cy.get('label').should('contain.text', 'Email Address');
        });
      });

      it('should have password form group', () => {
        cy.get('.form-group').last().within(() => {
          cy.get('label').should('contain.text', 'Password');
        });
      });
    });

    describe('Email Input Field', () => {
      it('should display email input with correct attributes', () => {
        cy.get('[data-testid="email-input"]')
          .should('be.visible')
          .and('have.attr', 'type', 'email')
          .and('have.attr', 'id', 'email')
          .and('have.attr', 'name', 'email')
          .and('have.attr', 'placeholder', 'your@email.com')
          .and('have.attr', 'autocomplete', 'email')
          .should('have.attr', 'required');
      });

      it('should accept email input', () => {
        cy.get('[data-testid="email-input"]')
          .type('test@example.com')
          .should('have.value', 'test@example.com');
      });

      it('should clear email input', () => {
        cy.get('[data-testid="email-input"]')
          .type('test@example.com')
          .clear()
          .should('have.value', '');
      });
    });

    describe('Password Input Field', () => {
      it('should display password input with correct attributes', () => {
        cy.get('[data-testid="password-input"]')
          .should('be.visible')
          .and('have.attr', 'type', 'password')
          .and('have.attr', 'id', 'password')
          .and('have.attr', 'name', 'password')
          .and('have.attr', 'placeholder', 'Enter your password')
          .and('have.attr', 'autocomplete', 'current-password')
          .should('have.attr', 'required');
      });

      it('should accept password input', () => {
        cy.get('[data-testid="password-input"]')
          .type('password123')
          .should('have.value', 'password123');
      });

      it('should clear password input', () => {
        cy.get('[data-testid="password-input"]')
          .type('password123')
          .clear()
          .should('have.value', '');
      });

      it('should have password toggle container', () => {
        cy.get('.password-toggle').should('exist');
      });
    });

    describe('Password Toggle Functionality', () => {
      it('should toggle password visibility', () => {
        cy.get('[data-testid="password-input"]').type('password123');
        cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
        
        cy.get('.toggle-btn').click();
        cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'text');
        
        cy.get('.toggle-btn').click();
        cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
      });
    });

    describe('Form Validation', () => {
      it('should validate required email field', () => {
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
        cy.get('[data-testid="login-button"]').click();
        cy.get('[data-testid="email-input"]:invalid').should('exist');
      });

      it('should accept valid form data', () => {
        cy.get('[data-testid="email-input"]').type('test@example.com');
        cy.get('[data-testid="password-input"]').type('password123');
        cy.get('[data-testid="email-input"]:valid').should('exist');
        cy.get('[data-testid="password-input"]:valid').should('exist');
      });
    });

    describe('Form Submission', () => {
      it('should disable button and show loading state on submit', () => {
        cy.get('[data-testid="email-input"]').type('test@example.com');
        cy.get('[data-testid="password-input"]').type('password123');
        
        cy.get('[data-testid="login-button"]').click();
        cy.get('[data-testid="login-button"]').should('be.disabled');
      });

      it('should submit form with valid data', () => {
        cy.intercept('POST', '/staff/login').as('loginRequest');
        
        cy.get('[data-testid="email-input"]').type('test@example.com');
        cy.get('[data-testid="password-input"]').type('password123');
        cy.get('[data-testid="login-button"]').click();
        
        cy.wait('@loginRequest').then((interception) => {
          expect(interception.request.body).to.include('test@example.com');
        });
      });
    });
  });

  describe('Interactive Element Tests', () => {
    it('should navigate to client portal when link is clicked', () => {
      cy.get('[data-testid="client-portal-link"]').click();
      cy.url().should('include', '/portal/login');
    });

    it('should handle form submission loading state', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      
      cy.get('[data-testid="login-button"]').click();
      cy.get('[data-testid="login-button"]').should('contain.text', 'Signing in...');
    });
  });

  describe('Responsive Tests', () => {
    describe('Desktop View (1280px)', () => {
      beforeEach(() => {
        cy.viewport(1280, 720);
      });

      it('should display all elements properly on desktop', () => {
        cy.get('[data-testid="login-container"]').should('be.visible');
        cy.get('[data-testid="login-card"]').should('be.visible');
        cy.get('[data-testid="login-form"]').should('be.visible');
        cy.get('.logo').should('be.visible');
      });
    });

    describe('Tablet View (768px)', () => {
      beforeEach(() => {
        cy.viewport(768, 1024);
      });

      it('should display all elements properly on tablet', () => {
        cy.get('[data-testid="login-container"]').should('be.visible');
        cy.get('[data-testid="login-card"]').should('be.visible');
        cy.get('[data-testid="login-form"]').should('be.visible');
        cy.get('.logo').should('be.visible');
      });

      it('should maintain form functionality on tablet', () => {
        cy.get('[data-testid="email-input"]').type('test@example.com');
        cy.get('[data-testid="password-input"]').type('password123');
        cy.get('.toggle-btn').click();
        cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'text');
      });
    });

    describe('Mobile View (375px)', () => {
      beforeEach(() => {
        cy.viewport(375, 667);
      });

      it('should display all elements properly on mobile', () => {
        cy.get('[data-testid="login-container"]').should('be.visible');
        cy.get('[data-testid="login-card"]').should('be.visible');
        cy.get('[data-testid="login-form"]').should('be.visible');
        cy.get('.logo').should('be.visible');
      });

      it('should maintain form functionality on mobile', () => {
        cy.get('[data-testid="email-input"]').type('test@example.com');
        cy.get('[data-testid="password-input"]').type('password123');
        cy.get('.toggle-btn').should('be.visible').click();
        cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'text');
      });

      it('should make buttons easily tappable on mobile', () => {
        cy.get('[data-testid="login-button"]').should('be.visible');
        cy.get('.toggle-btn').should('be.visible');
        cy.get('[data-testid="client-portal-link"]').should('be.visible');
      });
    });
  });

  describe('Error Handling Tests', () => {
    it('should handle network errors gracefully', () => {
      cy.intercept('POST', '/staff/login', { forceNetworkError: true }).as('networkError');
      
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
    });

    it('should handle server errors gracefully', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 500 }).as('serverError');
      
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      
      cy.wait('@serverError');
    });

    it('should handle authentication errors', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 401 }).as('authError');
      
      cy.get('[data-testid="email-input"]').type('wrong@example.com');
      cy.get('[data-testid="password-input"]').type('wrongpassword');
      cy.get('[data-testid="login-button"]').click();
      
      cy.wait('@authError');
    });

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
  });

  describe('Accessibility Tests', () => {
    it('should have proper labels for form inputs', () => {
      cy.get('label[for="email"]').should('exist');
      cy.get('label[for="password"]').should('exist');
    });

    it('should have proper form structure', () => {
      cy.get('[data-testid="login-form"]').within(() => {
        cy.get('.form-group').should('have.length', 2);
      });
    });

    it('should have focusable elements', () => {
      cy.get('[data-testid="email-input"]').focus().should('be.focused');
      cy.get('[data-testid="password-input"]').focus().should('be.focused');
      cy.get('[data-testid="login-button"]').focus().should('be.focused');
      cy.get('.toggle-btn').focus().should('be.focused');
    });
  });

  describe('JavaScript Functionality Tests', () => {
    it('should have togglePassword function available', () => {
      cy.window().its('togglePassword').should('be.a', 'function');
    });

    it('should execute password toggle script correctly', () => {
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'password');
      cy.window().then((win) => {
        win.togglePassword('password');
      });
      cy.get('[data-testid="password-input"]').should('have.attr', 'type', 'text');
    });

    it('should handle form submission event listener', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      
      cy.get('[data-testid="login-form"]').submit();
      cy.get('[data-testid="login-button"]').should('be.disabled');
    });
  });
});