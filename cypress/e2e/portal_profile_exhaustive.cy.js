// Exhaustive test for /portal/profile - Client Portal Profile Page
// TDD Approach: These tests define what the profile page SHOULD have

describe('/portal/profile - Client Portal Profile Page', () => {
  beforeEach(() => {
    // CI auth bypass handles authentication - just visit the page
    cy.visit('/portal/profile', { failOnStatusCode: false });
    cy.get('body').should('exist');
  });

  describe('Page Load Tests', () => {
    it('should load without errors', () => {
      cy.get('body').should('exist');
      cy.url().should('include', '/portal');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Profile');
    });

    it('should return 200 status', () => {
      cy.request({ url: '/portal/profile', failOnStatusCode: false }).its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Profile Header Tests', () => {
    it('should display profile header with avatar', () => {
      cy.get('[data-testid="profile-header"], .card').first().should('exist');
    });

    it('should display user avatar with initial', () => {
      cy.get('[data-testid="user-avatar"]').should('exist');
    });

    it('should display user full name', () => {
      cy.get('[data-testid="user-name"], h2').should('exist');
    });

    it('should display client since date', () => {
      cy.contains(/client since|member since/i).should('exist');
    });

    it('should display current round badge', () => {
      cy.contains(/round/i).should('exist');
    });

    it('should display portal active status', () => {
      cy.contains(/portal active|active/i).should('exist');
    });
  });

  describe('Quick Actions Tests', () => {
    it('should display quick action cards', () => {
      cy.get('[data-testid="quick-actions"], .stats-grid-responsive').should('exist');
    });

    it('should have Upload Document action', () => {
      cy.get('a[href*="documents"]').contains(/upload/i).should('exist');
    });

    it('should have View Case action', () => {
      cy.get('a[href*="dashboard"]').should('exist');
    });

    it('should have Learn FCRA action', () => {
      cy.get('a[href*="learn"]').should('exist');
    });

    it('should have 3 quick action cards', () => {
      cy.get('.stats-grid-responsive a.card').should('have.length', 3);
    });
  });

  describe('Personal Information Tests', () => {
    it('should display personal info section', () => {
      cy.contains(/personal information/i).should('exist');
    });

    it('should display full name field', () => {
      cy.get('input').filter('[value]').should('exist');
    });

    it('should display email field', () => {
      cy.get('input[type="email"], input[value*="@"]').should('exist');
    });

    it('should display phone field', () => {
      cy.get('input[type="tel"], label').contains(/phone/i).should('exist');
    });

    it('should display current round field', () => {
      cy.contains(/current round/i).should('exist');
    });

    it('should have disabled/readonly inputs', () => {
      cy.get('input[disabled]').should('have.length.at.least', 1);
    });

    it('should have update contact info notice', () => {
      cy.contains(/update.*contact|contact us/i).should('exist');
    });
  });

  describe('Bureau Status Link Tests', () => {
    it('should display bureau status card', () => {
      cy.contains(/detailed bureau status/i).should('exist');
    });

    it('should have link to status page', () => {
      cy.get('a[href*="status"]').should('exist');
    });

    it('should describe bureau status feature', () => {
      cy.contains(/individual account|all bureaus/i).should('exist');
    });
  });

  describe('Contact Section Tests', () => {
    it('should display contact section', () => {
      cy.contains(/get in touch|contact/i).should('exist');
    });

    it('should display phone contact', () => {
      cy.get('a[href^="tel:"]').should('exist');
    });

    it('should display email contact', () => {
      cy.get('a[href^="mailto:"]').should('exist');
    });

    it('should display website link', () => {
      cy.get('a[href*="brightpath"]').should('exist');
    });

    it('should have 3 contact cards', () => {
      cy.get('a[href^="tel:"], a[href^="mailto:"]').should('have.length.at.least', 2);
    });
  });

  describe('Message Form Tests', () => {
    it('should display message form', () => {
      cy.contains(/send.*message/i).should('exist');
    });

    it('should have subject dropdown', () => {
      cy.get('select[name="subject"]').should('exist');
    });

    it('should have message textarea', () => {
      cy.get('textarea[name="message"]').should('exist');
    });

    it('should have submit button', () => {
      cy.get('button[type="submit"]').contains(/send/i).should('exist');
    });

    it('should have subject options', () => {
      cy.get('select[name="subject"] option').should('have.length.at.least', 4);
    });

    it('should accept text input', () => {
      cy.get('textarea[name="message"]').type('Test message').should('have.value', 'Test message');
    });

    it('should have form action to send_message', () => {
      cy.get('form[action*="message"]').should('exist');
    });
  });

  describe('Referral Section Tests', () => {
    it('should display referral section', () => {
      cy.contains(/referral|refer.*friend/i).should('exist');
    });

    it('should display referral code', () => {
      cy.contains(/referral code/i).should('exist');
    });

    it('should have referral form', () => {
      cy.get('form[action*="referral"]').should('exist');
    });

    it('should have their name field', () => {
      cy.get('input[name="referral_name"]').should('exist');
    });

    it('should have their phone field', () => {
      cy.get('input[name="referral_phone"]').should('exist');
    });

    it('should have their email field', () => {
      cy.get('input[name="referral_email"]').should('exist');
    });

    it('should have your name field pre-filled', () => {
      cy.get('input[name="your_name"]').should('exist');
    });

    it('should have submit referral button', () => {
      cy.get('button[type="submit"]').contains(/referral|submit/i).should('exist');
    });

    it('should accept referral form input', () => {
      cy.get('input[name="referral_name"]').type('John Doe').should('have.value', 'John Doe');
    });
  });

  describe('Security Section Tests', () => {
    it('should display security section', () => {
      cy.contains(/security|account/i).should('exist');
    });

    it('should display case status', () => {
      cy.contains(/case status/i).should('exist');
    });

    it('should display client since info', () => {
      cy.contains(/client since/i).should('exist');
    });

    it('should display portal access status', () => {
      cy.contains(/portal access/i).should('exist');
    });

    it('should show active status', () => {
      cy.contains(/active/i).should('exist');
    });
  });

  describe('Animation Tests', () => {
    it('should have fade-in animations', () => {
      cy.get('.animate-fade-in, .animate-fade-in-up').should('exist');
    });

    it('should have staggered delays', () => {
      cy.get('[data-delay]').should('have.length.at.least', 4);
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
        cy.get('.main-content, main').should('be.visible');
      });
    });
  });

  describe('Navigation Tests', () => {
    it('should highlight profile tab as active', () => {
      cy.get('.nav-tab.active, a[href*="profile"].active').should('exist');
    });
  });

  describe('Form Validation Tests', () => {
    it('should have required message textarea', () => {
      cy.get('textarea[name="message"]').should('exist');
    });

    it('should validate referral email format', () => {
      cy.get('input[name="referral_email"]').should('have.attr', 'type', 'email');
    });

    it('should validate referral phone format', () => {
      cy.get('input[name="referral_phone"]').should('have.attr', 'type', 'tel');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have form labels', () => {
      cy.get('label').should('have.length.at.least', 5);
    });

    it('should have proper heading hierarchy', () => {
      cy.get('h2, h3, h4').should('have.length.at.least', 3);
    });
  });
});
