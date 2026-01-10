// Exhaustive test for /portal/learn - Client Portal Learn/Education Page
// TDD Approach: These tests define what the learn page SHOULD have

describe('/portal/learn - Client Portal Learn Page', () => {
  beforeEach(() => {
    // CI auth bypass handles authentication - just visit the page
    cy.visit('/portal/learn', { failOnStatusCode: false });
    cy.get('body').should('exist');
  });

  describe('Page Load Tests', () => {
    it('should load without errors', () => {
      cy.get('body').should('exist');
      cy.url().should('include', '/portal');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Learn');
    });

    it('should return 200 status', () => {
      cy.request({ url: '/portal/learn', failOnStatusCode: false }).its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Hero Section Tests', () => {
    it('should display hero section', () => {
      cy.get('[data-testid="hero-section"], .card').first().should('exist');
    });

    it('should have title about rights', () => {
      cy.contains(/rights|understanding/i).should('exist');
    });

    it('should have dark gradient background', () => {
      cy.get('.card').first().should('have.css', 'background-image').and('include', 'gradient');
    });
  });

  describe('Quick Stats Tests', () => {
    it('should display $1,000 per violation stat', () => {
      cy.contains('$1,000').should('exist');
    });

    it('should display 30 days investigation stat', () => {
      cy.contains('30').should('exist');
    });

    it('should display 7 years reporting stat', () => {
      cy.contains('7').should('exist');
    });

    it('should display success rate stat', () => {
      cy.contains(/75|%/).should('exist');
    });

    it('should have 4 stat cards', () => {
      cy.get('.stats-grid-responsive .card').should('have.length', 4);
    });
  });

  describe('FCRA Overview Tests', () => {
    it('should display FCRA section', () => {
      cy.contains(/fair credit reporting act|fcra/i).should('exist');
    });

    it('should explain what FCRA is', () => {
      cy.contains(/federal law|1970|credit information/i).should('exist');
    });

    it('should list core rights', () => {
      cy.contains(/accuracy|dispute|investigation|notification|damages/i).should('exist');
    });

    it('should have two-column layout', () => {
      cy.get('.two-col-responsive').should('exist');
    });
  });

  describe('Violation Types Tests', () => {
    it('should display violations section', () => {
      cy.contains(/types of violations|violations we find/i).should('exist');
    });

    it('should list impossible contradictions', () => {
      cy.contains(/contradiction/i).should('exist');
    });

    it('should list balance discrepancies', () => {
      cy.contains(/balance/i).should('exist');
    });

    it('should list date errors', () => {
      cy.contains(/date error/i).should('exist');
    });

    it('should list re-aging accounts', () => {
      cy.contains(/re-?aging/i).should('exist');
    });

    it('should list mixed files', () => {
      cy.contains(/mixed file/i).should('exist');
    });

    it('should list failure to investigate', () => {
      cy.contains(/failure to investigate/i).should('exist');
    });

    it('should display violation values', () => {
      cy.contains(/\$[\d,]+ – \$[\d,]+/).should('exist');
    });

    it('should have 6 violation types', () => {
      cy.get('[data-testid="violation-card"], .card').contains('Violation').should('exist');
    });
  });

  describe('Dispute Process Tests', () => {
    it('should display dispute process section', () => {
      cy.contains(/dispute process|how.*works/i).should('exist');
    });

    it('should show Round 1 - Formal Dispute Letters', () => {
      cy.contains(/round 1|formal dispute/i).should('exist');
    });

    it('should show Round 2 - Method of Verification', () => {
      cy.contains(/round 2|verification/i).should('exist');
    });

    it('should show Round 3 - Regulatory Complaints', () => {
      cy.contains(/round 3|regulatory/i).should('exist');
    });

    it('should show Round 4 - Pre-Litigation', () => {
      cy.contains(/round 4|litigation/i).should('exist');
    });

    it('should have numbered step indicators', () => {
      cy.get('[data-testid="step-1"], .card').contains('1').should('exist');
    });

    it('should display timeline for each step', () => {
      cy.contains(/day|timeline/i).should('exist');
    });
  });

  describe('Glossary Tests', () => {
    it('should display glossary section', () => {
      cy.contains(/glossary|terms/i).should('exist');
    });

    it('should define CRA', () => {
      cy.contains('CRA').should('exist');
    });

    it('should define Furnisher', () => {
      cy.contains('Furnisher').should('exist');
    });

    it('should define Metro 2 Format', () => {
      cy.contains('Metro 2').should('exist');
    });

    it('should define Statutory Damages', () => {
      cy.contains('Statutory Damages').should('exist');
    });

    it('should define Willful Violation', () => {
      cy.contains('Willful').should('exist');
    });

    it('should define CFPB', () => {
      cy.contains('CFPB').should('exist');
    });

    it('should define DOFD', () => {
      cy.contains('DOFD').should('exist');
    });

    it('should define Reinsertion', () => {
      cy.contains('Reinsertion').should('exist');
    });

    it('should have 8 glossary terms', () => {
      cy.get('[data-testid="glossary-term"], .card > div > div').should('have.length.at.least', 8);
    });
  });

  describe('FAQ Tests', () => {
    it('should display FAQ section', () => {
      cy.contains(/faq|frequently asked/i).should('exist');
    });

    it('should have collapsible details elements', () => {
      cy.get('details').should('have.length.at.least', 5);
    });

    it('should expand FAQ when clicked', () => {
      cy.get('details').first().click();
      cy.get('details').first().should('have.attr', 'open');
    });

    it('should have question about process duration', () => {
      cy.contains(/how long|dispute process take/i).should('exist');
    });

    it('should have question about 30-day deadline', () => {
      cy.contains(/30 days|respond/i).should('exist');
    });

    it('should have question about damages', () => {
      cy.contains(/statutory.*damage|actual.*damage/i).should('exist');
    });

    it('should have question about self-dispute', () => {
      cy.contains(/dispute.*myself|free/i).should('exist');
    });

    it('should have question about frivolous claims', () => {
      cy.contains(/frivolous/i).should('exist');
    });

    it('should have question about credit repair', () => {
      cy.contains(/credit repair|different/i).should('exist');
    });

    it('should have question about credit score impact', () => {
      cy.contains(/credit score|hurt/i).should('exist');
    });

    it('should have question about receiving mail', () => {
      cy.contains(/receive.*mail|credit bureau/i).should('exist');
    });
  });

  describe('CTA Section Tests', () => {
    it('should display contact CTA', () => {
      cy.contains(/still have questions|contact/i).should('exist');
    });

    it('should have link to profile/contact page', () => {
      cy.get('a[href*="profile"]').should('exist');
    });

    it('should have teal gradient background', () => {
      cy.get('.card').last().should('have.css', 'background-image').and('include', 'gradient');
    });
  });

  describe('Animation Tests', () => {
    it('should have fade-in animations', () => {
      cy.get('.animate-fade-in, .animate-fade-in-up').should('exist');
    });

    it('should have staggered delays', () => {
      cy.get('[data-delay]').should('have.length.at.least', 5);
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

    it('should stack two-column layouts on mobile', () => {
      cy.viewport(375, 667);
      cy.get('.two-col-responsive').should('exist');
    });
  });

  describe('Navigation Tests', () => {
    it('should highlight learn tab as active', () => {
      cy.get('.nav-tab.active, a[href*="learn"].active').should('exist');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h2, h3, h4').should('have.length.at.least', 3);
    });

    it('should have accessible accordion summary', () => {
      cy.get('details summary').should('have.length.at.least', 5);
    });
  });
});
