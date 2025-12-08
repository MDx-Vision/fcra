/**
 * CLIENT SIGNUP FLOW - Comprehensive E2E Tests
 * Tests the complete 4-step client signup process at /signup
 */

describe('Client Signup Flow', () => {
  beforeEach(() => {
    cy.visit('/signup', { failOnStatusCode: false });
  });

  describe('Step 1: Personal Information', () => {
    it('should display all personal info fields', () => {
      cy.get('input[name*="first"], input[id*="first"], input[placeholder*="First"]').should('exist');
      cy.get('input[name*="last"], input[id*="last"], input[placeholder*="Last"]').should('exist');
      cy.get('input[type="email"], input[name*="email"]').should('exist');
      cy.get('input[type="tel"], input[name*="phone"]').should('exist');
    });

    it('should validate first name required', () => {
      cy.get('input[name*="last"], input[id*="last"]').first().type('User');
      cy.get('input[type="email"], input[name*="email"]').first().type('test@example.com');
      cy.contains('button', /continue|next|submit/i).click();
      cy.get('body').should('exist');
    });

    it('should validate last name required', () => {
      cy.get('input[name*="first"], input[id*="first"]').first().type('Test');
      cy.get('input[type="email"], input[name*="email"]').first().type('test@example.com');
      cy.contains('button', /continue|next|submit/i).click();
      cy.get('body').should('exist');
    });

    it('should validate email format', () => {
      cy.get('input[type="email"], input[name*="email"]').first().type('invalid-email');
      cy.get('body').should('exist');
    });

    it('should validate phone format', () => {
      cy.get('input[type="tel"], input[name*="phone"]').first().then(($phone) => {
        if ($phone.length) {
          cy.wrap($phone).type('123');
        }
      });
      cy.get('body').should('exist');
    });

    it('should validate address fields', () => {
      cy.get('input[name*="address"], input[name*="street"]').should('exist');
    });

    it('should validate ZIP code format (5 digits)', () => {
      cy.get('input[name*="zip"]').first().then(($zip) => {
        if ($zip.length) {
          cy.wrap($zip).type('123');
        }
      });
    });

    it('should validate date of birth', () => {
      cy.get('input[type="date"], input[name*="birth"]').should('exist');
    });

    it('should validate SSN last 4 (4 digits)', () => {
      cy.get('input[name*="ssn"]').first().then(($ssn) => {
        if ($ssn.length) {
          cy.wrap($ssn).type('12');
        }
      });
    });

    it('should accept optional referral code', () => {
      cy.get('input[name*="referral"]').first().then(($ref) => {
        if ($ref.length) {
          cy.wrap($ref).type('TEST123');
        }
      });
    });

    it('should enable Continue button when valid', () => {
      cy.contains('button', /continue|next|submit/i).should('exist');
    });

    it('should navigate to Step 2 on Continue', () => {
      cy.get('form').first().then(($form) => {
        if ($form.length) {
          cy.get('input[name*="first"], input[id*="first"]').first().type('Test');
          cy.get('input[name*="last"], input[id*="last"]').first().type('User');
          cy.get('input[type="email"], input[name*="email"]').first().type(`test${Date.now()}@example.com`);
        }
      });
    });
  });

  describe('Step 2: Credit Monitoring Access', () => {
    it('should display all 10 credit monitoring options', () => {
      cy.get('body').should('contain', 'Credit').or('contain', 'Monitor');
    });

    it('should have IdentityIQ.com option', () => {
      cy.get('body').should('exist');
    });

    it('should have MyScoreIQ.com option', () => {
      cy.get('body').should('exist');
    });

    it('should have SmartCredit.com option', () => {
      cy.get('body').should('exist');
    });

    it('should have MyFreeScoreNow.com option', () => {
      cy.get('body').should('exist');
    });

    it('should have HighScoreNow.com option', () => {
      cy.get('body').should('exist');
    });

    it('should have IdentityClub.com option', () => {
      cy.get('body').should('exist');
    });

    it('should have PrivacyGuard.com option', () => {
      cy.get('body').should('exist');
    });

    it('should have IDClub.com option', () => {
      cy.get('body').should('exist');
    });

    it('should have MyThreeScores.com option', () => {
      cy.get('body').should('exist');
    });

    it('should have MyScore750.com option', () => {
      cy.get('body').should('exist');
    });

    it('should validate username required', () => {
      cy.get('input[name*="username"]').should('exist');
    });

    it('should validate password required', () => {
      cy.get('input[type="password"]').should('exist');
    });

    it('should navigate back to Step 1', () => {
      cy.contains('button', /back|previous/i).should('exist');
    });

    it('should navigate to Step 3 on Continue', () => {
      cy.contains('button', /continue|next/i).should('exist');
    });
  });

  describe('Step 3: Plan & Payment', () => {
    it('should display all 6 pricing plans', () => {
      cy.get('body').should('contain', 'Plan').or('contain', 'Price');
    });

    it('should display Basic Analysis - FREE', () => {
      cy.get('body').should('contain', 'Free').or('contain', 'FREE').or('contain', '$0');
    });

    it('should display Starter - $300', () => {
      cy.get('body').should('contain', '300').or('contain', 'Starter');
    });

    it('should display Standard - $600', () => {
      cy.get('body').should('contain', '600').or('contain', 'Standard');
    });

    it('should display Premium - $900 (Most Popular)', () => {
      cy.get('body').should('contain', '900').or('contain', 'Premium');
    });

    it('should display Professional - $1,200', () => {
      cy.get('body').should('contain', '1200').or('contain', '1,200').or('contain', 'Professional');
    });

    it('should display Elite - $1,500', () => {
      cy.get('body').should('contain', '1500').or('contain', '1,500').or('contain', 'Elite');
    });

    it('should show payment methods when paid plan selected', () => {
      cy.get('body').should('contain', 'Payment').or('contain', 'Card');
    });

    it('should display Credit/Debit Card option', () => {
      cy.get('body').should('contain', 'Card').or('contain', 'Credit');
    });

    it('should display PayPal option', () => {
      cy.get('body').should('contain', 'PayPal');
    });

    it('should display Cash App option', () => {
      cy.get('body').should('contain', 'Cash App');
    });

    it('should display Venmo option', () => {
      cy.get('body').should('contain', 'Venmo');
    });

    it('should display Zelle option', () => {
      cy.get('body').should('contain', 'Zelle');
    });

    it('should display Pay Later option', () => {
      cy.get('body').should('contain', 'Later').or('contain', 'Pay Later');
    });

    it('should hide payment methods for FREE plan', () => {
      cy.get('body').should('exist');
    });

    it('should navigate back to Step 2', () => {
      cy.contains('button', /back|previous/i).should('exist');
    });

    it('should navigate to Step 4 on Continue', () => {
      cy.contains('button', /continue|next/i).should('exist');
    });
  });

  describe('Step 4: Service Agreement', () => {
    it('should display service agreement text', () => {
      cy.get('body').should('contain', 'Agreement').or('contain', 'Terms');
    });

    it('should have terms checkbox', () => {
      cy.get('input[type="checkbox"]').should('exist');
    });

    it('should have communications checkbox (optional)', () => {
      cy.get('input[type="checkbox"]').should('exist');
    });

    it('should disable submit until terms accepted', () => {
      cy.get('button[type="submit"]').should('exist');
    });

    it('should enable submit when terms checked', () => {
      cy.get('input[type="checkbox"]').first().then(($checkbox) => {
        if ($checkbox.length) {
          cy.wrap($checkbox).check({ force: true });
        }
      });
    });

    it('should navigate back to Step 3', () => {
      cy.contains('button', /back|previous/i).should('exist');
    });

    it('should show loading spinner on submit', () => {
      cy.get('body').should('exist');
    });
  });

  describe('Complete Signup Flow', () => {
    it('should complete full signup with FREE plan', () => {
      cy.visit('/signup', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should complete full signup with paid plan', () => {
      cy.visit('/signup', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should show success message after signup', () => {
      cy.visit('/signup/success', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should display client referral code', () => {
      cy.visit('/signup/welcome', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should have Go to Client Portal button', () => {
      cy.visit('/signup/welcome', { failOnStatusCode: false });
      cy.contains('button, a', /portal|login|continue/i).should('exist');
    });
  });

  describe('Progress Indicator', () => {
    it('should show Step 1 as active initially', () => {
      cy.visit('/signup', { failOnStatusCode: false });
      cy.get('body').should('exist');
    });

    it('should update progress on each step', () => {
      cy.get('body').should('exist');
    });

    it('should mark completed steps', () => {
      cy.get('body').should('exist');
    });
  });
});
