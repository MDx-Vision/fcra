/**
 * SOP Screenshot Capture Script
 *
 * Run this script to automatically capture all 20 screenshots for the Client Portal SOP.
 *
 * Usage:
 *   npx cypress run --spec "cypress/e2e/capture_sop_screenshots.cy.js"
 *
 * Screenshots will be saved to: static/images/sop/
 */

describe('Client Portal SOP Screenshot Capture', () => {
  const screenshotDir = 'static/images/sop';

  // Screenshot helper with consistent settings
  const captureScreenshot = (filename, options = {}) => {
    cy.screenshot(filename, {
      capture: 'viewport',
      overwrite: true,
      ...options
    });
  };

  // Wait for page animations to complete
  const waitForAnimations = () => {
    cy.wait(500);
  };

  // =========================================================================
  // STAGE 1: Getting Started
  // =========================================================================

  describe('Stage 1: Getting Started', () => {

    it('01 - Signup Form', () => {
      cy.visit('/get-started');
      waitForAnimations();

      // Fill in some example data to show the form in use
      cy.get('input[name="first_name"]').type('John', { delay: 0 });
      cy.get('input[name="last_name"]').type('Smith', { delay: 0 });
      cy.get('input[name="email"]').type('john.smith@example.com', { delay: 0 });
      cy.get('input[name="phone"]').type('555-123-4567', { delay: 0 });

      captureScreenshot(`${screenshotDir}/01-signup-form`);
    });

    it('02 - Login Page', () => {
      cy.visit('/portal/login');
      waitForAnimations();

      captureScreenshot(`${screenshotDir}/02-login-page`);
    });
  });

  // =========================================================================
  // STAGE 2: Onboarding (requires login)
  // =========================================================================

  describe('Stage 2: Onboarding', () => {
    // In CI mode, portal auto-authenticates - no login needed

    it('03 - Onboarding Navigation', () => {
      cy.visit('/portal/onboarding');
      waitForAnimations();

      // Capture just the navigation area
      captureScreenshot(`${screenshotDir}/03-onboarding-nav`);
    });

    it('04 - Personal Information Form', () => {
      cy.visit('/portal/onboarding');
      waitForAnimations();

      // Scroll to personal info section if needed
      cy.get('body').then($body => {
        if ($body.find('[data-testid="personal-info"]').length) {
          cy.get('[data-testid="personal-info"]').scrollIntoView();
        }
      });

      captureScreenshot(`${screenshotDir}/04-personal-info`);
    });

    it('05 - ID Upload Section', () => {
      cy.visit('/portal/onboarding');
      waitForAnimations();

      // Scroll to ID upload section if it exists
      cy.get('body').then($body => {
        if ($body.find('[data-testid="id-upload"]').length) {
          cy.get('[data-testid="id-upload"]').scrollIntoView();
        }
      });

      captureScreenshot(`${screenshotDir}/05-id-upload`);
    });

    it('06 - Credit Monitoring Setup', () => {
      cy.visit('/portal/onboarding');
      waitForAnimations();

      // Scroll to credit monitoring section
      cy.get('body').then($body => {
        if ($body.find('[data-testid="credit-monitoring"]').length) {
          cy.get('[data-testid="credit-monitoring"]').scrollIntoView();
        }
      });

      captureScreenshot(`${screenshotDir}/06-credit-monitoring`);
    });

    it('07 - Agreements Page', () => {
      cy.visit('/portal/agreements');
      waitForAnimations();

      captureScreenshot(`${screenshotDir}/07-agreements`);
    });

    it('08 - Cancellation Notice', () => {
      cy.visit('/portal/agreements');
      waitForAnimations();

      // Scroll down to see cancellation notice if visible
      cy.scrollTo('bottom');
      cy.wait(300);

      captureScreenshot(`${screenshotDir}/08-cancellation`);
    });

    it('09 - Payment Form', () => {
      cy.visit('/portal/onboarding');
      waitForAnimations();

      // Scroll to payment section
      cy.get('body').then($body => {
        if ($body.find('[data-testid="payment-section"]').length) {
          cy.get('[data-testid="payment-section"]').scrollIntoView();
        }
      });

      captureScreenshot(`${screenshotDir}/09-payment`);
    });
  });

  // =========================================================================
  // STAGE 3: Active Client Portal
  // =========================================================================

  describe('Stage 3: Active Client Portal', () => {
    // In CI mode, portal auto-authenticates - no login needed

    it('10 - Active Navigation', () => {
      cy.visit('/portal/dashboard');
      waitForAnimations();

      // Focus on the navigation bar
      captureScreenshot(`${screenshotDir}/10-active-nav`);
    });

    it('11 - Case Dashboard', () => {
      cy.visit('/portal/dashboard');
      waitForAnimations();

      captureScreenshot(`${screenshotDir}/11-case-dashboard`);
    });

    it('12 - Bureau Status Detail', () => {
      cy.visit('/portal/status');
      waitForAnimations();

      captureScreenshot(`${screenshotDir}/12-bureau-status`);
    });
  });

  // =========================================================================
  // STAGE 4: Ongoing Tasks
  // =========================================================================

  describe('Stage 4: Ongoing Tasks', () => {
    // In CI mode, portal auto-authenticates - no login needed

    it('13 - CRA Response Upload', () => {
      cy.visit('/portal/documents');
      waitForAnimations();

      // Click CRA Response option if available
      cy.get('body').then($body => {
        if ($body.find('input[value="cra_response"]').length) {
          cy.get('input[value="cra_response"]').click({ force: true });
        }
      });

      captureScreenshot(`${screenshotDir}/13-cra-upload`);
    });

    it('14 - Documents List', () => {
      cy.visit('/portal/documents');
      waitForAnimations();

      // Scroll to documents list
      cy.get('body').then($body => {
        if ($body.find('[data-testid="documents-list"]').length) {
          cy.get('[data-testid="documents-list"]').scrollIntoView();
        }
      });

      captureScreenshot(`${screenshotDir}/14-documents-list`);
    });

    it('15 - Messages Interface', () => {
      cy.visit('/portal/messages');
      waitForAnimations();

      captureScreenshot(`${screenshotDir}/15-messages`);
    });

    it('16 - Booking Calendar', () => {
      cy.visit('/portal/booking');
      waitForAnimations();

      captureScreenshot(`${screenshotDir}/16-booking`);
    });

    it('17 - Journey Timeline', () => {
      cy.visit('/portal/timeline');
      waitForAnimations();

      captureScreenshot(`${screenshotDir}/17-timeline`);
    });
  });

  // =========================================================================
  // STAGE 5: Profile & Settings
  // =========================================================================

  describe('Stage 5: Profile & Settings', () => {
    // In CI mode, portal auto-authenticates - no login needed

    it('18 - Profile Settings', () => {
      cy.visit('/portal/profile');
      waitForAnimations();

      captureScreenshot(`${screenshotDir}/18-profile`);
    });

    it('19 - Freeze Status', () => {
      cy.visit('/portal/status');
      waitForAnimations();

      // Scroll to secondary bureaus section
      cy.scrollTo('bottom');
      cy.wait(300);

      captureScreenshot(`${screenshotDir}/19-freeze-status`);
    });

    it('20 - Billing & Invoices', () => {
      cy.visit('/portal/invoices');
      waitForAnimations();

      captureScreenshot(`${screenshotDir}/20-billing`);
    });
  });
});
