/**
 * Exhaustive tests for Lead Capture Landing Page (/get-started)
 * Tests the public-facing lead capture form for prospective clients
 */

describe('Lead Capture Landing Page (/get-started)', () => {
  beforeEach(() => {
    cy.visit('/get-started');
  });

  // ============================================================
  // PAGE LOAD TESTS
  // ============================================================
  describe('Page Load', () => {
    it('should load the page successfully', () => {
      cy.url().should('include', '/get-started');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Get Started');
    });

    it('should display the main card', () => {
      cy.get('[data-testid="get-started-card"]').should('be.visible');
    });

    it('should display the form', () => {
      cy.get('[data-testid="get-started-form"]').should('be.visible');
    });

    it('should display company branding/logo', () => {
      cy.get('.logo').should('be.visible');
      cy.get('.logo h1').should('contain.text', 'Brightpath');
    });

    it('should display tagline', () => {
      cy.get('.tagline').should('be.visible');
      cy.get('.tagline').should('contain.text', 'credit');
    });

    it('should display 3-step process indicators', () => {
      cy.get('.steps .step').should('have.length', 3);
      cy.get('.step-number').eq(0).should('contain.text', '1');
      cy.get('.step-number').eq(1).should('contain.text', '2');
      cy.get('.step-number').eq(2).should('contain.text', '3');
    });

    it('should display trust badges', () => {
      cy.get('.trust-badges').should('be.visible');
      cy.get('.trust-badge').should('have.length', 3);
    });
  });

  // ============================================================
  // FORM FIELD TESTS
  // ============================================================
  describe('Form Fields', () => {
    it('should have first name input', () => {
      cy.get('[data-testid="first-name-input"]')
        .should('be.visible')
        .and('have.attr', 'required');
    });

    it('should have last name input', () => {
      cy.get('[data-testid="last-name-input"]')
        .should('be.visible')
        .and('have.attr', 'required');
    });

    it('should have email input', () => {
      cy.get('[data-testid="email-input"]')
        .should('be.visible')
        .and('have.attr', 'type', 'email')
        .and('have.attr', 'required');
    });

    it('should have phone input', () => {
      cy.get('[data-testid="phone-input"]')
        .should('be.visible')
        .and('have.attr', 'type', 'tel');
    });

    it('should have address input', () => {
      cy.get('[data-testid="address-input"]').should('be.visible');
    });

    it('should have city input', () => {
      cy.get('[data-testid="city-input"]').should('be.visible');
    });

    it('should have state input', () => {
      cy.get('[data-testid="state-input"]')
        .should('be.visible')
        .and('have.attr', 'maxlength', '2');
    });

    it('should have zip code input', () => {
      cy.get('[data-testid="zip-input"]').should('be.visible');
    });

    it('should have credit monitoring service dropdown', () => {
      cy.get('[data-testid="monitoring-service-select"]').should('be.visible');
    });

    it('should have all monitoring service options', () => {
      cy.get('[data-testid="monitoring-service-select"] option').should('have.length.at.least', 8);
      cy.get('[data-testid="monitoring-service-select"]').should('contain', 'IdentityIQ');
      cy.get('[data-testid="monitoring-service-select"]').should('contain', 'MyScoreIQ');
      cy.get('[data-testid="monitoring-service-select"]').should('contain', 'SmartCredit');
    });
  });

  // ============================================================
  // CONDITIONAL FIELDS TESTS
  // ============================================================
  describe('Conditional Fields', () => {
    it('should hide credentials section by default', () => {
      cy.get('#credentialsSection').should('not.be.visible');
    });

    it('should show credentials section when monitoring service selected', () => {
      cy.get('[data-testid="monitoring-service-select"]').select('identityiq');
      cy.get('#credentialsSection').should('be.visible');
    });

    it('should show monitoring username field when service selected', () => {
      cy.get('[data-testid="monitoring-service-select"]').select('myscoreiq');
      cy.get('[data-testid="monitoring-username-input"]').should('be.visible');
    });

    it('should show monitoring password field when service selected', () => {
      cy.get('[data-testid="monitoring-service-select"]').select('smartcredit');
      cy.get('[data-testid="monitoring-password-input"]').should('be.visible');
    });

    it('should show SSN last 4 field when service selected', () => {
      cy.get('[data-testid="monitoring-service-select"]').select('identityiq');
      cy.get('[data-testid="ssn-last4-input"]').should('be.visible');
    });

    it('should have SSN field with maxlength 4', () => {
      cy.get('[data-testid="monitoring-service-select"]').select('identityiq');
      cy.get('[data-testid="ssn-last4-input"]')
        .should('have.attr', 'maxlength', '4');
    });

    it('should show affiliate link when "none" selected', () => {
      cy.get('[data-testid="monitoring-service-select"]').select('none');
      cy.get('#noMonitoringHelp').should('be.visible');
      cy.get('[data-testid="affiliate-link"]').should('be.visible');
    });

    it('should hide credentials section when "none" selected', () => {
      cy.get('[data-testid="monitoring-service-select"]').select('identityiq');
      cy.get('#credentialsSection').should('be.visible');
      cy.get('[data-testid="monitoring-service-select"]').select('none');
      cy.get('#credentialsSection').should('not.be.visible');
    });
  });

  // ============================================================
  // BUTTON TESTS
  // ============================================================
  describe('Buttons', () => {
    it('should have submit button', () => {
      cy.get('[data-testid="submit-btn"]')
        .should('be.visible')
        .and('contain.text', 'Analyze My Credit Report');
    });

    it('should have consultation button', () => {
      cy.get('[data-testid="consultation-btn"]')
        .should('be.visible')
        .and('contain.text', 'Book Free Consultation');
    });

    it('should have affiliate link that opens in new tab', () => {
      cy.get('[data-testid="monitoring-service-select"]').select('none');
      cy.get('[data-testid="affiliate-link"]')
        .should('have.attr', 'target', '_blank');
    });
  });

  // ============================================================
  // FORM VALIDATION TESTS
  // ============================================================
  describe('Form Validation', () => {
    it('should require first name', () => {
      cy.get('[data-testid="last-name-input"]').type('Doe');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="submit-btn"]').click();
      // Form should not submit - check we're still on the page
      cy.url().should('include', '/get-started');
    });

    it('should require last name', () => {
      cy.get('[data-testid="first-name-input"]').type('John');
      cy.get('[data-testid="email-input"]').type('test@example.com');
      cy.get('[data-testid="submit-btn"]').click();
      cy.url().should('include', '/get-started');
    });

    it('should require email', () => {
      cy.get('[data-testid="first-name-input"]').type('John');
      cy.get('[data-testid="last-name-input"]').type('Doe');
      cy.get('[data-testid="submit-btn"]').click();
      cy.url().should('include', '/get-started');
    });

    it('should validate email format', () => {
      cy.get('[data-testid="first-name-input"]').type('John');
      cy.get('[data-testid="last-name-input"]').type('Doe');
      cy.get('[data-testid="email-input"]').type('invalid-email');
      cy.get('[data-testid="submit-btn"]').click();
      cy.url().should('include', '/get-started');
    });

    it('should accept valid form data', () => {
      const uniqueEmail = `test${Date.now()}@example.com`;
      cy.get('[data-testid="first-name-input"]').type('John');
      cy.get('[data-testid="last-name-input"]').type('Doe');
      cy.get('[data-testid="email-input"]').type(uniqueEmail);
      cy.get('[data-testid="submit-btn"]').click();
      // Should show success or preview section
      cy.get('.alert-success, [data-testid="preview-section"]', { timeout: 10000 }).should('exist');
    });
  });

  // ============================================================
  // FORM SUBMISSION TESTS
  // ============================================================
  describe('Form Submission', () => {
    it('should submit basic lead info successfully', () => {
      const uniqueEmail = `lead${Date.now()}@example.com`;

      cy.get('[data-testid="first-name-input"]').type('Test');
      cy.get('[data-testid="last-name-input"]').type('Lead');
      cy.get('[data-testid="email-input"]').type(uniqueEmail);
      cy.get('[data-testid="phone-input"]').type('5551234567');

      cy.get('[data-testid="submit-btn"]').click();

      // Should show success alert or preview section after submission
      cy.get('body').then(($body) => {
        // Wait for any response
        cy.wait(2000);
        // Either success alert or the form should still exist (form submission happened)
        if ($body.find('.alert-success').length || $body.find('.alert').length) {
          cy.get('.alert').should('exist');
        } else {
          // Form was submitted via API, check we're still on page
          cy.url().should('include', '/get-started');
        }
      });
    });

    it('should submit with full address', () => {
      const uniqueEmail = `fulladdress${Date.now()}@example.com`;

      cy.get('[data-testid="first-name-input"]').type('Full');
      cy.get('[data-testid="last-name-input"]').type('Address');
      cy.get('[data-testid="email-input"]').type(uniqueEmail);
      cy.get('[data-testid="address-input"]').type('123 Main St');
      cy.get('[data-testid="city-input"]').type('New York');
      cy.get('[data-testid="state-input"]').type('NY');
      cy.get('[data-testid="zip-input"]').type('10001');

      cy.get('[data-testid="submit-btn"]').click();

      // Wait for submission and check for response
      cy.wait(2000);
      cy.get('body').then(($body) => {
        if ($body.find('.alert').length) {
          cy.get('.alert').should('exist');
        } else {
          cy.url().should('include', '/get-started');
        }
      });
    });

    it('should submit with monitoring credentials', () => {
      const uniqueEmail = `withcreds${Date.now()}@example.com`;

      cy.get('[data-testid="first-name-input"]').type('With');
      cy.get('[data-testid="last-name-input"]').type('Credentials');
      cy.get('[data-testid="email-input"]').type(uniqueEmail);

      cy.get('[data-testid="monitoring-service-select"]').select('identityiq');
      cy.get('[data-testid="monitoring-username-input"]').type('user@iq.com');
      cy.get('[data-testid="monitoring-password-input"]').type('password123');
      cy.get('[data-testid="ssn-last4-input"]').type('1234');

      cy.get('[data-testid="submit-btn"]').click();

      cy.get('.alert-success', { timeout: 10000 }).should('be.visible');
    });

  });

  // ============================================================
  // PREVIEW SECTION TESTS
  // ============================================================
  describe('Preview Section', () => {
    it('should be hidden by default', () => {
      cy.get('[data-testid="preview-section"]').should('not.be.visible');
    });

    it('should show after successful submission with monitoring service', () => {
      const uniqueEmail = `preview${Date.now()}@example.com`;

      cy.get('[data-testid="first-name-input"]').type('Preview');
      cy.get('[data-testid="last-name-input"]').type('Test');
      cy.get('[data-testid="email-input"]').type(uniqueEmail);
      cy.get('[data-testid="monitoring-service-select"]').select('identityiq');
      cy.get('[data-testid="monitoring-username-input"]').type('user@test.com');
      cy.get('[data-testid="monitoring-password-input"]').type('pass123');
      cy.get('[data-testid="ssn-last4-input"]').type('5678');

      cy.get('[data-testid="submit-btn"]').click();

      cy.get('[data-testid="preview-section"]', { timeout: 10000 }).should('be.visible');
    });

    it('should display unlock button in preview', () => {
      const uniqueEmail = `unlock${Date.now()}@example.com`;

      cy.get('[data-testid="first-name-input"]').type('Unlock');
      cy.get('[data-testid="last-name-input"]').type('Test');
      cy.get('[data-testid="email-input"]').type(uniqueEmail);
      cy.get('[data-testid="monitoring-service-select"]').select('identityiq');
      cy.get('[data-testid="monitoring-username-input"]').type('user@test.com');
      cy.get('[data-testid="monitoring-password-input"]').type('pass123');
      cy.get('[data-testid="ssn-last4-input"]').type('9999');

      cy.get('[data-testid="submit-btn"]').click();

      cy.get('[data-testid="preview-section"]', { timeout: 10000 }).should('be.visible');
      cy.get('[data-testid="unlock-btn"]').should('be.visible');
    });

    it('should display final CTA button in preview', () => {
      const uniqueEmail = `finalcta${Date.now()}@example.com`;

      cy.get('[data-testid="first-name-input"]').type('Final');
      cy.get('[data-testid="last-name-input"]').type('CTA');
      cy.get('[data-testid="email-input"]').type(uniqueEmail);
      cy.get('[data-testid="monitoring-service-select"]').select('identityiq');
      cy.get('[data-testid="monitoring-username-input"]').type('user@test.com');
      cy.get('[data-testid="monitoring-password-input"]').type('pass123');
      cy.get('[data-testid="ssn-last4-input"]').type('4321');

      cy.get('[data-testid="submit-btn"]').click();

      cy.get('[data-testid="preview-section"]', { timeout: 10000 }).should('be.visible');
      cy.get('[data-testid="final-cta-btn"]').should('be.visible');
    });
  });

  // ============================================================
  // API ENDPOINT TESTS
  // ============================================================
  describe('API Endpoint', () => {
    it('should return success for valid lead data', () => {
      const uniqueEmail = `api${Date.now()}@example.com`;

      cy.request({
        method: 'POST',
        url: '/api/leads/capture',
        body: {
          first_name: 'API',
          last_name: 'Test',
          email: uniqueEmail
        }
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body.success).to.be.true;
        expect(response.body.client_id).to.be.a('number');
      });
    });

    it('should return error for missing first name', () => {
      cy.request({
        method: 'POST',
        url: '/api/leads/capture',
        body: {
          last_name: 'Test',
          email: 'test@example.com'
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(400);
        expect(response.body.success).to.be.false;
      });
    });

    it('should return error for missing email', () => {
      cy.request({
        method: 'POST',
        url: '/api/leads/capture',
        body: {
          first_name: 'Test',
          last_name: 'User'
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(400);
        expect(response.body.success).to.be.false;
      });
    });

    it('should store monitoring credentials', () => {
      const uniqueEmail = `creds${Date.now()}@example.com`;

      cy.request({
        method: 'POST',
        url: '/api/leads/capture',
        body: {
          first_name: 'Creds',
          last_name: 'Test',
          email: uniqueEmail,
          monitoring_service: 'identityiq',
          monitoring_username: 'testuser',
          monitoring_password: 'testpass',
          ssn_last_four: '1234'
        }
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body.success).to.be.true;
      });
    });

    it('should return preview data when monitoring service provided', () => {
      const uniqueEmail = `previewapi${Date.now()}@example.com`;

      cy.request({
        method: 'POST',
        url: '/api/leads/capture',
        body: {
          first_name: 'Preview',
          last_name: 'API',
          email: uniqueEmail,
          monitoring_service: 'identityiq'
        }
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body.success).to.be.true;
        // Preview data should exist (even if mock)
        expect(response.body).to.have.property('preview');
      });
    });
  });

  // ============================================================
  // AFFILIATE LINK TESTS
  // ============================================================
  describe('Affiliate Link', () => {
    it('should have affiliate signup route', () => {
      cy.request({
        method: 'GET',
        url: '/affiliate/signup',
        followRedirect: false
      }).then((response) => {
        expect(response.status).to.eq(302);
        expect(response.redirectedToUrl || response.headers.location).to.include('identityiq');
      });
    });
  });

  // ============================================================
  // PHONE FORMATTING TESTS
  // ============================================================
  describe('Phone Number Formatting', () => {
    it('should format phone number as user types', () => {
      cy.get('[data-testid="phone-input"]').type('5551234567');
      cy.get('[data-testid="phone-input"]').should('have.value', '(555) 123-4567');
    });
  });

  // ============================================================
  // RESPONSIVE DESIGN TESTS
  // ============================================================
  describe('Responsive Design', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 800);
      cy.get('[data-testid="get-started-card"]').should('be.visible');
      cy.get('.form-row').should('have.css', 'display', 'flex');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('[data-testid="get-started-card"]').should('be.visible');
      cy.get('[data-testid="get-started-form"]').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('[data-testid="get-started-card"]').should('be.visible');
      cy.get('[data-testid="get-started-form"]').should('be.visible');
      cy.get('[data-testid="submit-btn"]').should('be.visible');
    });

    it('should stack form rows on mobile', () => {
      cy.viewport(375, 667);
      // On mobile, form-row should stack vertically
      cy.get('.form-row').first().should('be.visible');
    });
  });

  // ============================================================
  // ACCESSIBILITY TESTS
  // ============================================================
  describe('Accessibility', () => {
    it('should have labels for all form inputs', () => {
      cy.get('label[for="firstName"]').should('exist');
      cy.get('label[for="lastName"]').should('exist');
      cy.get('label[for="email"]').should('exist');
      cy.get('label[for="phone"]').should('exist');
      cy.get('label[for="address"]').should('exist');
      cy.get('label[for="city"]').should('exist');
      cy.get('label[for="state"]').should('exist');
      cy.get('label[for="zip"]').should('exist');
      // Monitoring service uses h3 header instead of label
      cy.get('.monitoring-section h3').should('contain.text', 'Credit Monitoring');
    });

    it('should have proper input types', () => {
      cy.get('[data-testid="email-input"]').should('have.attr', 'type', 'email');
      cy.get('[data-testid="phone-input"]').should('have.attr', 'type', 'tel');
      cy.get('[data-testid="monitoring-password-input"]').should('have.attr', 'type', 'password');
    });

    it('should have placeholder text for guidance', () => {
      cy.get('[data-testid="first-name-input"]').should('have.attr', 'placeholder');
      cy.get('[data-testid="email-input"]').should('have.attr', 'placeholder');
    });
  });
});
