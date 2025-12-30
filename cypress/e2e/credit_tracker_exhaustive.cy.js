// Exhaustive test for /dashboard/credit-tracker
describe('Credit Score Tracker Page - /dashboard/credit-tracker', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/credit-tracker');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/credit-tracker');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Credit Score Tracker');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/credit-tracker').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.page-header h1').should('contain.text', 'Credit Score Improvement Tracker');
    });

    it('should display header subtitle', () => {
      cy.get('.page-header-subtitle').should('contain.text', 'Track and estimate');
    });
  });

  describe('Tabs Tests', () => {
    it('should display tabs container', () => {
      cy.get('.tabs').should('be.visible');
    });

    it('should have 3 tab buttons', () => {
      cy.get('.tab-btn').should('have.length', 3);
    });

    it('should have Quick Estimate tab', () => {
      cy.get('.tab-btn').contains('Quick Estimate').should('exist');
    });

    it('should have Detailed Calculator tab', () => {
      cy.get('.tab-btn').contains('Detailed Calculator').should('exist');
    });

    it('should have Client Progress tab', () => {
      cy.get('.tab-btn').contains('Client Progress').should('exist');
    });

    it('should have Quick Estimate tab active by default', () => {
      cy.get('.tab-btn').contains('Quick Estimate').should('have.class', 'active');
    });

    it('should switch to Detailed Calculator tab when clicked', () => {
      cy.get('.tab-btn').contains('Detailed Calculator').click();
      cy.get('.tab-btn').contains('Detailed Calculator').should('have.class', 'active');
      cy.get('#detailed-tab').should('have.class', 'active');
    });

    it('should switch to Client Progress tab when clicked', () => {
      cy.get('.tab-btn').contains('Client Progress').click();
      cy.get('.tab-btn').contains('Client Progress').should('have.class', 'active');
      cy.get('#clients-tab').should('have.class', 'active');
    });
  });

  describe('Quick Estimate Tab Tests', () => {
    it('should display quick estimate section', () => {
      cy.get('.quick-estimate').should('be.visible');
    });

    it('should display Quick Score Improvement Estimator title', () => {
      cy.get('.quick-estimate h2').should('contain.text', 'Quick Score Improvement Estimator');
    });

    it('should have estimate form', () => {
      cy.get('.estimate-form').should('be.visible');
    });

    it('should have current score input', () => {
      cy.get('#currentScore').should('exist');
    });

    it('should have number of negatives input', () => {
      cy.get('#numNegatives').should('exist');
    });

    it('should have Calculate Estimate button', () => {
      cy.get('.btn-estimate').contains('Calculate Estimate').should('be.visible');
    });

    it('should accept input in current score field', () => {
      cy.get('#currentScore').type('580').should('have.value', '580');
    });

    it('should accept input in negatives field', () => {
      cy.get('#numNegatives').type('8').should('have.value', '8');
    });

    it('should have estimate result section (hidden initially)', () => {
      cy.get('#estimateResult').should('exist');
      cy.get('#estimateResult').should('not.have.class', 'show');
    });
  });

  describe('Detailed Calculator Tab Tests', () => {
    beforeEach(() => {
      cy.get('.tab-btn').contains('Detailed Calculator').click();
    });

    it('should display item selector section', () => {
      cy.get('.item-selector').should('be.visible');
    });

    it('should display Detailed Score Impact Calculator title', () => {
      cy.get('.item-selector h2').should('contain.text', 'Detailed Score Impact Calculator');
    });

    it('should have detailed current score input', () => {
      cy.get('#detailedCurrentScore').should('exist');
    });

    it('should have selected items container', () => {
      cy.get('#selectedItems').should('exist');
    });

    it('should have item categories container', () => {
      cy.get('#itemCategories').should('exist');
    });

    it('should have Calculate Detailed Estimate button', () => {
      cy.get('.btn-estimate').contains('Calculate Detailed Estimate').should('be.visible');
    });

    it('should accept input in detailed score field', () => {
      cy.get('#detailedCurrentScore').clear().type('600').should('have.value', '600');
    });
  });

  describe('Client Progress Tab Tests', () => {
    beforeEach(() => {
      cy.get('.tab-btn').contains('Client Progress').click();
    });

    it('should display clients section', () => {
      cy.get('.clients-section').should('be.visible');
    });

    it('should display Client Score Progress title', () => {
      cy.get('.clients-section h2').should('contain.text', 'Client Score Progress');
    });

    it('should have search box', () => {
      cy.get('.search-box').should('be.visible');
    });

    it('should have search input', () => {
      cy.get('#searchClients').should('exist');
    });

    it('should have client grid container', () => {
      cy.get('#clientGrid').should('exist');
    });

    it('should accept input in search field', () => {
      cy.get('#searchClients').type('test').should('have.value', 'test');
    });
  });

  describe('Form Groups Tests', () => {
    it('should have form group styling', () => {
      cy.get('.form-group').should('have.length.at.least', 1);
    });

    it('should have form labels', () => {
      cy.get('.form-group label').should('have.length.at.least', 1);
    });
  });

  describe('Result Display Tests', () => {
    it('should have result grid structure', () => {
      cy.get('.result-grid').should('exist');
    });

    it('should have result items', () => {
      cy.get('.result-item').should('have.length.at.least', 1);
    });

    it('should have current score result element', () => {
      cy.get('#resCurrentScore').should('exist');
    });

    it('should have projected score result element', () => {
      cy.get('#resProjectedScore').should('exist');
    });

    it('should have potential gain result element', () => {
      cy.get('#resPotentialGain').should('exist');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.page-header').should('be.visible');
      cy.get('.tabs').should('be.visible');
      cy.get('.quick-estimate').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.tabs').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.page-header h1').should('be.visible');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have clickable Calculate Estimate button', () => {
      cy.get('.btn-estimate').first().should('not.be.disabled');
    });

    it('should have clickable tab buttons', () => {
      cy.get('.tab-btn').each(($btn) => {
        cy.wrap($btn).should('not.be.disabled');
      });
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
      cy.get('h2').should('have.length.at.least', 1);
    });

    it('should have form labels', () => {
      cy.get('label').should('have.length.at.least', 1);
    });

    it('should have proper input types', () => {
      cy.get('input[type="number"]').should('have.length.at.least', 1);
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have switchTab function', () => {
      cy.window().should('have.property', 'switchTab');
    });

    it('should have calculateEstimate function', () => {
      cy.window().should('have.property', 'calculateEstimate');
    });

    it('should have filterClients function', () => {
      cy.window().should('have.property', 'filterClients');
    });
  });
});
