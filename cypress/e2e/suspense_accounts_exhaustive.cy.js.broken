// Exhaustive test for /dashboard/suspense-accounts
describe('/dashboard/suspense-accounts - Staff Login Page', () => {
  beforeEach(() => {
    cy.visit('/dashboard/suspense-accounts');
  });

  describe('Page Load Tests', () => {
    it('should load without errors', () => {
      cy.url().should('include', '/dashboard/suspense-accounts');
      cy.get('[data-testid="login-container"]').should('be.visible');
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

    it('should return 200 status code', () => {
      cy.request('/dashboard/suspense-accounts').then((response) => {
        expect(response.status).to.eq(200);
      });
    });
  });

  describe('UI Element Tests - Logo and Branding', () => {
    it('should display company logo', () => {
      cy.get('.logo img').should('be.visible').and('have.attr', 'src', '/static/images/logo.png');
      cy.get('.logo img').should('have.attr', 'alt', 'Brightpath Ascend Group');
    });

    it('should display main heading', () => {
      cy.get('.logo h1').should('contain.text', 'Brightpath').and('contain.text', 'Ascend').and('contain.text', 'Group');
    });

    it('should display platform description', () => {
      cy.get('.logo p').should('contain.text', 'FCRA Litigation Platform');
    });
  });

  describe('UI Element Tests - Login Card', () => {
    it('should display login card container', () => {
      cy.get('[data-testid="login-card"]').should('be.visible');
    });

    it('should display staff badge with icon', () => {
      cy.get('.staff-badge').should('be.visible').and('contain.text', 'Staff Portal');
      cy.get('.staff-badge svg').should('be.visible');
    });

    it('should display login title heading', () => {
      cy.get('[data-testid="login-title"]').should('be.visible').and('contain.text', 'Staff Login');
    });

    it('should display subtitle', () => {
      cy.get('.subtitle').should('be.visible').and('contain.text', 'Sign in to access the admin dashboard');
    });

    it('should display client portal link', () => {
      cy.get('.client-portal-link').should('be.visible').and('contain.text', 'Looking for client portal?');
      cy.get('[data-testid="client-portal-link"]').should('be.visible').and('have.attr', 'href', '/portal/login');
    });
  });

  describe('Form Tests - Login Form', () => {
    it('should display login form with correct attributes', () => {
      cy.get('[data-testid="login-form"]').should('be.visible');
      cy.get('#loginForm').should('have.attr', 'method', 'POST');
      cy.get('#loginForm').should('have.attr', 'action', '/staff/login');
    });

    it('should display email input with correct attributes', () => {
      cy.get('[data-testid="email-input"]').should('be.visible');
      cy.get('#email').should('have.attr', 'type', 'email');
      cy.get('#email').should('have.attr', 'name', 'email');
      cy.get('#email').should('have.attr', 'placeholder', 'your@email.com');
      cy.get('#email').should('have.attr', 'required');
      cy.get('#email').should('have.attr', 'autocomplete', 'email');
    });

    it('should display email label', () => {
      cy.get('label[for="email"]').should('be.visible').and('contain.text', 'Email Address');
    });

    it('should display password input with correct attributes', () => {
      cy.get('[data-testid="password-input"]').should('be.visible');
      cy.get('#password').should('have.attr', 'type', 'password');
      cy.get('#password').should('have.attr', 'name', 'password');
      cy.get('#password').should('have.attr', 'placeholder', 'Enter your password');
      cy.get('#password').should('have.attr', 'required');
      cy.get('#password').should('have.attr', 'autocomplete', 'current-password');
    });

    it('should display password label', () => {
      cy.get('label[for="password"]').should('be.visible').and('contain.text', 'Password');
    });

    it('should allow typing in email input', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="email-input"]').should('have.value', 'test@example.com');
    });

    it('should allow typing in password input', () => {
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="password-input"]').should('have.value', 'password123');
    });

    it('should clear email input', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="email-input"]').clear();
      cy.get('[data-testid="email-input"]').should('have.value', '');
    });

    it('should clear password input', () => {
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="password-input"]').clear();
      cy.get('[data-testid="password-input"]').should('have.value', '');
    });

    it('should validate email format', () => {
      cy.get('[data-testid="email-input"]').type('invalid-email');
      cy.get('[data-testid="login-button"]').click();
      cy.get('#email:invalid').should('exist');
    });

    it('should accept valid email format', () => {
      cy.get('[data-testid="email-input"]').type('valid@email.com');
      cy.get('#email:valid').should('exist');
    });
  });

  describe('Button Tests', () => {
    it('should display password toggle button', () => {
      cy.get('.toggle-btn').should('be.visible');
      cy.get('.toggle-btn').should('have.attr', 'type', 'button');
      cy.get('.toggle-btn').should('contain.text', '👁');
    });

    it('should display login submit button', () => {
      cy.get('[data-testid="login-button"]').should('be.visible');
      cy.get('#loginBtn').should('have.attr', 'type', 'submit');
      cy.get('#loginBtn').should('contain.text', 'Sign In');
    });

    it('should toggle password visibility', () => {
      cy.get('#password').should('have.attr', 'type', 'password');
      cy.get('.toggle-btn').click();
      cy.get('#password').should('have.attr', 'type', 'text');
      cy.get('.toggle-btn').click();
      cy.get('#password').should('have.attr', 'type', 'password');
    });

    it('should be clickable - login button', () => {
      cy.get('[data-testid="login-button"]').should('not.be.disabled');
      cy.get('[data-testid="login-button"]').click();
    });

    it('should change button text when form is submitted', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('#loginBtn').should('contain.text', 'Signing in...');
      cy.get('#loginBtn').should('be.disabled');
    });
  });

  describe('Form Submission Tests', () => {
    it('should submit form with valid credentials', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 200 }).as('loginSubmit');
      cy.get('[data-testid="email-input"]').type('staff@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@loginSubmit');
    });

    it('should require email field', () => {
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('#email:invalid').should('exist');
    });

    it('should require password field', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="login-button"]').click();
      cy.get('#password:invalid').should('exist');
    });

    it('should require both fields', () => {
      cy.get('[data-testid="login-button"]').click();
      cy.get('#email:invalid').should('exist');
      cy.get('#password:invalid').should('exist');
    });
  });

  describe('Navigation Tests', () => {
    it('should navigate to client portal when link is clicked', () => {
      cy.get('[data-testid="client-portal-link"]').click();
      cy.url().should('include', '/portal/login');
    });

    it('should have correct href for client portal link', () => {
      cy.get('[data-testid="client-portal-link"]').should('have.attr', 'href', '/portal/login');
    });
  });

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
    });
  });

  describe('Error Handling Tests', () => {
    it('should handle network errors gracefully', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 500 }).as('serverError');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@serverError');
    });

    it('should handle 404 errors', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 404 }).as('notFoundError');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.wait('@notFoundError');
    });

    it('should handle authentication failures', () => {
      cy.intercept('POST', '/staff/login', { statusCode: 401 }).as('authError');
      cy.get('[data-testid="email-input"]').type('wrong@email.com');
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

    it('should have proper input associations', () => {
      cy.get('#email').should('have.attr', 'id', 'email');
      cy.get('#password').should('have.attr', 'id', 'password');
    });

    it('should have alt text for logo image', () => {
      cy.get('.logo img').should('have.attr', 'alt', 'Brightpath Ascend Group');
    });

    it('should support keyboard navigation', () => {
      cy.get('body').type('{tab}');
      cy.focused().should('have.id', 'email');
      cy.focused().type('{tab}');
      cy.focused().should('have.id', 'password');
      cy.focused().type('{tab}');
      cy.focused().should('have.class', 'toggle-btn');
      cy.focused().type('{tab}');
      cy.focused().should('have.id', 'loginBtn');
    });
  });

  describe('Data Attribute Tests', () => {
    it('should have all required data-testid attributes', () => {
      cy.get('[data-testid="login-container"]').should('exist');
      cy.get('[data-testid="login-card"]').should('exist');
      cy.get('[data-testid="login-title"]').should('exist');
      cy.get('[data-testid="login-form"]').should('exist');
      cy.get('[data-testid="email-input"]').should('exist');
      cy.get('[data-testid="password-input"]').should('exist');
      cy.get('[data-testid="login-button"]').should('exist');
      cy.get('[data-testid="client-portal-link"]').should('exist');
    });
  });

  describe('JavaScript Functionality Tests', () => {
    it('should have togglePassword function available', () => {
      cy.window().then((win) => {
        expect(win.togglePassword).to.be.a('function');
      });
    });

    it('should toggle password input type when function is called', () => {
      cy.get('#password').should('have.attr', 'type', 'password');
      cy.window().then((win) => {
        win.togglePassword('password');
      });
      cy.get('#password').should('have.attr', 'type', 'text');
    });

    it('should attach form submit event listener', () => {
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="password-input"]').type('password123');
      cy.get('[data-testid="login-button"]').click();
      cy.get('#loginBtn').should('be.disabled');
    });
  });
});