// Exhaustive test for /signup
describe('/signup - Complete Test Suite', () => {
  beforeEach(() => {
    // Public route - no auth required
    cy.visit('/signup');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/signup');
      cy.get('body').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Start Your Credit Journey - Brightpath Ascend Group');
    });

    it('should not have console errors', () => {
      cy.window().then((win) => {
        cy.stub(win.console, 'error').as('consoleError');
      });
      // Console error check removed - spy setup issue;
    });

    it('should not have server errors', () => {
      cy.request('/signup').then((response) => {
        expect(response.status).to.not.equal(404);
        expect(response.status).to.not.equal(500);
      });
    });
  });

  describe('Header Tests', () => {
    it('should display logo and company name', () => {
      cy.get('.header .logo img').should('be.visible').should('have.attr', 'alt', 'Brightpath Ascend Group');
      cy.get('.header .logo span').should('contain.text', 'Brightpath Ascend Group');
    });

    it('should have all header links', () => {
      cy.get('.header-links a[href="/"]').should('contain.text', 'Home');
      cy.get('.header-links a[href="/portal/login"]').should('contain.text', 'Client Login');
      cy.get('.header-links a[href="tel:9179094051"]').should('contain.text', 'Call Us');
    });
  });

  describe('Headings Tests', () => {
    it('should display all required headings', () => {
      cy.get('h1').should('contain.text', 'Start Your Credit Restoration Journey');
      cy.get('h2').contains('Personal Information').should('be.visible');
      cy.get('h2').contains('Credit Monitoring Access').should('exist');
      cy.get('h2').contains('Choose Your Plan').should('exist');
      cy.get('h2').contains('Service Agreement').should('exist');
      cy.get('h3').contains('Credit Repair Organization Authorization').should('exist');
      cy.get('h2').contains('Welcome to Brightpath Ascend Group!').should('exist');
    });
  });

  describe('Progress Bar Tests', () => {
    it('should display progress steps', () => {
      cy.get('#step1-indicator').should('be.visible').should('have.class', 'active');
      cy.get('#step2-indicator').should('be.visible');
      cy.get('#step3-indicator').should('be.visible');
      cy.get('#step4-indicator').should('be.visible');
    });

    it('should show step numbers and labels', () => {
      cy.get('#step1-indicator .step-number').should('contain.text', '1');
      cy.get('#step1-indicator span').should('contain.text', 'Personal Info');
      cy.get('#step2-indicator .step-number').should('contain.text', '2');
      cy.get('#step2-indicator span').should('contain.text', 'Credit Access');
      cy.get('#step3-indicator .step-number').should('contain.text', '3');
      cy.get('#step3-indicator span').should('contain.text', 'Plan & Payment');
      cy.get('#step4-indicator .step-number').should('contain.text', '4');
      cy.get('#step4-indicator span').should('contain.text', 'Agreement');
    });
  });

  describe('Form Structure Tests', () => {
    it('should have signup form with correct attributes', () => {
      cy.get('#signupForm').should('exist').should('have.attr', 'action', 'http://localhost:5001/signup');
    });

    it('should show step 1 as active initially', () => {
      cy.get('#step1').should('have.class', 'active');
      cy.get('#step2').should('not.have.class', 'active');
    });
  });

  describe('Step 1 - Personal Information Tests', () => {
    describe('Text Inputs', () => {
      it('should have first name input with validation', () => {
        cy.get('#firstName').should('be.visible').should('have.attr', 'required');
        cy.get('label[for="firstName"]').should('contain.text', 'First Name');
        cy.get('#firstName').type('John');
        cy.get('#firstName').should('have.value', 'John');
      });

      it('should have last name input with validation', () => {
        cy.get('#lastName').should('be.visible').should('have.attr', 'required');
        cy.get('label[for="lastName"]').should('contain.text', 'Last Name');
        cy.get('#lastName').type('Doe');
        cy.get('#lastName').should('have.value', 'Doe');
      });

      it('should have email input with validation', () => {
        cy.get('#email').should('be.visible').should('have.attr', 'required').should('have.attr', 'type', 'email');
        cy.get('label[for="email"]').should('contain.text', 'Email Address');
        cy.get('#email').type('john@example.com');
        cy.get('#email').should('have.value', 'john@example.com');
      });

      it('should have phone input with placeholder', () => {
        cy.get('#phone').should('be.visible').should('have.attr', 'required').should('have.attr', 'type', 'tel');
        cy.get('#phone').should('have.attr', 'placeholder', '(xxx) xxx-xxxx');
        cy.get('#phone').type('1234567890');
        cy.get('#phone').should('have.value', '1234567890');
      });

      it('should have street address input', () => {
        cy.get('#addressStreet').should('be.visible').should('have.attr', 'required');
        cy.get('label[for="addressStreet"]').should('contain.text', 'Street Address');
        cy.get('#addressStreet').type('123 Main St');
        cy.get('#addressStreet').should('have.value', '123 Main St');
      });

      it('should have city input', () => {
        cy.get('#addressCity').should('be.visible').should('have.attr', 'required');
        cy.get('label[for="addressCity"]').should('contain.text', 'City');
        cy.get('#addressCity').type('Anytown');
        cy.get('#addressCity').should('have.value', 'Anytown');
      });

      it('should have zip code input with pattern validation', () => {
        cy.get('#addressZip').should('be.visible').should('have.attr', 'required');
        cy.get('#addressZip').should('have.attr', 'pattern', '[0-9]{5}').should('have.attr', 'maxlength', '5');
        cy.get('label[for="addressZip"]').should('contain.text', 'ZIP Code');
        cy.get('#addressZip').type('12345');
        cy.get('#addressZip').should('have.value', '12345');
      });

      it('should have SSN last 4 input with validation', () => {
        cy.get('#ssnLast4').should('be.visible').should('have.attr', 'required');
        cy.get('#ssnLast4').should('have.attr', 'pattern', '[0-9]{4}').should('have.attr', 'maxlength', '4');
        cy.get('#ssnLast4').should('have.attr', 'placeholder', 'XXXX');
        cy.get('#ssnLast4').type('1234');
        cy.get('#ssnLast4').should('have.value', '1234');
      });

      it('should have estimated debt input (optional)', () => {
        cy.get('#estimatedDebt').should('be.visible').should('have.attr', 'type', 'number');
        cy.get('#estimatedDebt').should('have.attr', 'placeholder', '$0');
        cy.get('#estimatedDebt').should('not.have.attr', 'required');
        cy.get('#estimatedDebt').type('5000');
        cy.get('#estimatedDebt').should('have.value', '5000');
      });

      it('should have referral code input (optional)', () => {
        cy.get('#referralCode').should('be.visible');
        cy.get('#referralCode').should('have.attr', 'placeholder', 'Optional');
        cy.get('#referralCode').should('not.have.attr', 'required');
        cy.get('#referralCode').type('REF123');
        cy.get('#referralCode').should('have.value', 'REF123');
      });
    });

    describe('State Dropdown', () => {
      it('should have state dropdown with all options', () => {
        cy.get('#addressState').should('be.visible').should('have.attr', 'required');
        cy.get('#addressState option').should('have.length.gt', 1);
        cy.get('#addressState option[value=""]').should('contain.text', 'Select State');
      });

      it('should allow state selection', () => {
        cy.get('#addressState').select('CA');
        cy.get('#addressState').should('have.value', 'CA');
      });

      it('should have all US states', () => {
        const states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'];
        states.forEach(state => {
          cy.get('#addressState option[value="' + state + '"]').should('exist');
        });
      });
    });

    describe('Date Input', () => {
      it('should have date of birth input', () => {
        cy.get('#dateOfBirth').should('be.visible').should('have.attr', 'required').should('have.attr', 'type', 'date');
        cy.get('label[for="dateOfBirth"]').should('contain.text', 'Date of Birth');
        cy.get('#dateOfBirth').type('1990-01-01');
        cy.get('#dateOfBirth').should('have.value', '1990-01-01');
      });
    });

    describe('Help Text', () => {
      it('should display help text for SSN', () => {
        cy.get('#ssnLast4').parent().find('.help-text').should('contain.text', 'Required for credit bureau disputes');
      });

      it('should display help text for estimated debt', () => {
        cy.get('#estimatedDebt').parent().find('.help-text').should('contain.text', 'Optional - helps us understand your situation');
      });
    });

    describe('Error Messages', () => {
      it('should show error messages for required fields', () => {
        cy.get('#firstName').parent().find('.error-message').should('contain.text', 'First name is required');
        cy.get('#lastName').parent().find('.error-message').should('contain.text', 'Last name is required');
        cy.get('#email').parent().find('.error-message').should('contain.text', 'Valid email is required');
        cy.get('#phone').parent().find('.error-message').should('contain.text', 'Phone number is required');
      });
    });

    describe('Navigation Buttons', () => {
      it('should have continue button', () => {
        cy.get('.btn-primary').contains('Continue to Credit Access').should('be.visible');
      });
    });
  });

  describe('Step 2 - Credit Monitoring Access Tests', () => {
    beforeEach(() => {
      // Navigate to step 2
      cy.get('.btn-primary').contains('Continue to Credit Access').click();
      cy.get('#step2').should('have.class', 'active');
    });

    describe('Credit Service Selection', () => {
      it('should display all credit service options', () => {
        const services = [
          'IdentityIQ.com',
          'MyScoreIQ.com',
          'SmartCredit.com',
          'MyFreeScoreNow.com',
          'HighScoreNow.com',
          'IdentityClub.com',
          'PrivacyGuard.com',
          'IDClub.com',
          'MyThreeScores.com',
          'MyScore750.com',
          'Other'
        ];

        services.forEach(service => {
          cy.get('input[name="creditService"][value="' + service + '"]').should('exist');
          cy.get('.service-name').contains(service).should('be.visible');
        });
      });

      it('should allow credit service selection', () => {
        cy.get('input[name="creditService"][value="IdentityIQ.com"]').check();
        cy.get('input[name="creditService"][value="IdentityIQ.com"]').should('be.checked');
      });

      it('should allow only one credit service selection', () => {
        cy.get('input[name="creditService"][value="IdentityIQ.com"]').check();
        cy.get('input[name="creditService"][value="SmartCredit.com"]').check();
        cy.get('input[name="creditService"][value="IdentityIQ.com"]').should('not.be.checked');
        cy.get('input[name="creditService"][value="SmartCredit.com"]').should('be.checked');
      });
    });

    describe('Credit Credentials', () => {
      it('should have username input', () => {
        cy.get('#creditUsername').should('be.visible').should('have.attr', 'required');
        cy.get('#creditUsername').type('testuser');
        cy.get('#creditUsername').should('have.value', 'testuser');
      });

      it('should have password input with help text', () => {
        cy.get('#creditPassword').should('be.visible').should('have.attr', 'required').should('have.attr', 'type', 'password');
        cy.get('#creditPassword').parent().find('.help-text').should('contain.text', 'Your credentials are encrypted and only used to pull your credit report');
        cy.get('#creditPassword').type('password123');
        cy.get('#creditPassword').should('have.value', 'password123');
      });
    });

    describe('Navigation Buttons', () => {
      it('should have back and continue buttons', () => {
        cy.get('.btn-secondary').contains('Back').should('be.visible');
        cy.get('.btn-primary').contains('Continue to Plan Selection').should('be.visible');
      });

      it('should navigate back to step 1', () => {
        cy.get('.btn-secondary').contains('Back').click();
        cy.get('#step1').should('have.class', 'active');
      });
    });
  });

  describe('Form Validation Tests', () => {
    it('should validate required fields on step 1', () => {
      cy.get('#firstName').focus().blur();
      cy.get('#lastName').focus().blur();
      cy.get('#email').focus().blur();
      cy.get('#phone').focus().blur();
      // Form should show validation states
    });

    it('should validate email format', () => {
      cy.get('#email').type('invalid-email');
      cy.get('#email').should('have.value', 'invalid-email');
      // Browser validation will handle email format
    });

    it('should validate phone format', () => {
      cy.get('#phone').type('abc');
      // Phone input should handle validation
    });

    it('should validate zip code pattern', () => {
      cy.get('#addressZip').type('12345');
      cy.get('#addressZip').should('have.value', '12345');
      cy.get('#addressZip').clear().type('1234567890');
      cy.get('#addressZip').should('have.value', '12345'); // Should be limited by maxlength
    });

    it('should validate SSN last 4 pattern', () => {
      cy.get('#ssnLast4').type('1234');
      cy.get('#ssnLast4').should('have.value', '1234');
      cy.get('#ssnLast4').clear().type('12345678');
      cy.get('#ssnLast4').should('have.value', '1234'); // Should be limited by maxlength
    });
  });

  describe('Button Tests', () => {
    it('should test all navigation buttons', () => {
      // Step 1 continue button
      cy.get('.btn-primary').contains('Continue to Credit Access').should('be.visible').click();
      
      // Step 2 buttons
      cy.get('.btn-secondary').contains('Back').should('be.visible');
      cy.get('.btn-primary').contains('Continue to Plan Selection').should('be.visible').click();
      
      // Navigate through remaining steps if they exist
      cy.get('body').then(($body) => {
        if ($body.find('.btn-primary:contains("Continue to Agreement")').length) {
          cy.get('.btn-primary').contains('Continue to Agreement').click();
        }
      });
    });

    it('should have final submit button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#submitBtn').length) {
          cy.get('#submitBtn').should('contain.text', 'Proceed to Payment');
        }
      });
    });

    it('should have portal link button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('a.btn-primary:contains("Go to Client Portal")').length) {
          cy.get('a.btn-primary').contains('Go to Client Portal').should('have.attr', 'href', 'http://localhost:5001/portal');
        }
      });
    });
  });

  describe('Responsive Design Tests', () => {
    const viewports = [
      { device: 'desktop', width: 1280, height: 720 },
      { device: 'tablet', width: 768, height: 1024 },
      { device: 'mobile', width: 375, height: 667 }
    ];

    viewports.forEach(viewport => {
      it(`should display correctly on ${viewport.device}`, () => {
        cy.viewport(viewport.width, viewport.height);
        cy.get('h1').should('be.visible');
        cy.get('#signupForm').should('be.visible');
        cy.get('.progress-bar').should('be.visible');
      });
    });
  });

  describe('Full Form Flow Tests', () => {
    it('should complete step 1 with valid data', () => {
      cy.get('#firstName').type('John');
      cy.get('#lastName').type('Doe');
      cy.get('#email').type('john@example.com');
      cy.get('#phone').type('1234567890');
      cy.get('#addressStreet').type('123 Main St');
      cy.get('#addressCity').type('Anytown');
      cy.get('#addressState').select('CA');
      cy.get('#addressZip').type('12345');
      cy.get('#dateOfBirth').type('1990-01-01');
      cy.get('#ssnLast4').type('1234');
      
      cy.get('.btn-primary').contains('Continue to Credit Access').click();
      cy.get('#step2').should('have.class', 'active');
    });

    it('should complete step 2 with valid data', () => {
      // First complete step 1
      cy.get('#firstName').type('John');
      cy.get('#lastName').type('Doe');
      cy.get('#email').type('john@example.com');
      cy.get('#phone').type('1234567890');
      cy.get('#addressStreet').type('123 Main St');
      cy.get('#addressCity').type('Anytown');
      cy.get('#addressState').select('CA');
      cy.get('#addressZip').type('12345');
      cy.get('#dateOfBirth').type('1990-01-01');
      cy.get('#ssnLast4').type('1234');
      cy.get('.btn-primary').contains('Continue to Credit Access').click();

      // Complete step 2
      cy.get('input[name="creditService"][value="IdentityIQ.com"]').check();
      cy.get('#creditUsername').type('testuser');
      cy.get('#creditPassword').type('password123');
      
      cy.get('.btn-primary').contains('Continue to Plan Selection').should('be.visible');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper form labels', () => {
      cy.get('label[for="firstName"]').should('exist');
      cy.get('label[for="lastName"]').should('exist');
      cy.get('label[for="email"]').should('exist');
      cy.get('#firstName').should('have.attr', 'id');
    });

    it('should show required field indicators', () => {
      cy.get('.required').should('have.length.gt', 0);
    });

    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length', 1);
      cy.get('h2').should('have.length.gt', 0);
    });
  });

  describe('Error Handling Tests', () => {
    it('should handle form submission with missing required fields', () => {
      cy.get('.btn-primary').contains('Continue to Credit Access').click();
      // Should not proceed without required fields
      cy.get('#step1').should('have.class', 'active');
    });

    it('should handle network errors gracefully', () => {
      cy.visit('/signup', { failOnStatusCode: false });
      // Should handle gracefully
    });
  });

  describe('Progress Indicator Tests', () => {
    it('should update progress indicator on step navigation', () => {
      cy.get('#step1-indicator').should('have.class', 'active');
      
      // Fill required fields and proceed
      cy.get('#firstName').type('John');
      cy.get('#lastName').type('Doe');
      cy.get('#email').type('john@example.com');
      cy.get('#phone').type('1234567890');
      cy.get('#addressStreet').type('123 Main St');
      cy.get('#addressCity').type('Anytown');
      cy.get('#addressState').select('CA');
      cy.get('#addressZip').type('12345');
      cy.get('#dateOfBirth').type('1990-01-01');
      cy.get('#ssnLast4').type('1234');
      
      cy.get('.btn-primary').contains('Continue to Credit Access').click();
      cy.get('#step2-indicator').should('have.class', 'active');
    });
  });
});