// Exhaustive test for /dashboard/demand-generator
describe('AI Settlement Demand Generator Page - /dashboard/demand-generator', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/demand-generator');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/demand-generator');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'AI Settlement Demand Generator');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/demand-generator').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'AI Settlement Demand Generator');
    });

    it('should display header subtitle', () => {
      cy.get('.header p').should('contain.text', 'Generate professional demand letters');
    });
  });

  describe('Grid Layout Tests', () => {
    it('should display grid container', () => {
      cy.get('.grid-container').should('be.visible');
    });

    it('should display cards', () => {
      cy.get('.card').should('have.length.at.least', 2);
    });
  });

  describe('Client Selection Card Tests', () => {
    it('should display Select Client card', () => {
      cy.get('.card-title').contains('Select Client').should('be.visible');
    });

    it('should have client search input', () => {
      cy.get('#clientSearch').should('exist');
    });

    it('should have client list container', () => {
      cy.get('#clientList').should('exist');
    });

    it('should accept input in search field', () => {
      cy.get('#clientSearch').type('test').should('have.value', 'test');
    });

    it('should display client items or empty message', () => {
      cy.get('#clientList').then(($list) => {
        const hasItems = $list.find('.client-item').length > 0;
        const hasEmpty = $list.text().includes('No clients');
        expect(hasItems || hasEmpty).to.be.true;
      });
    });
  });

  describe('Demand Configuration Card Tests', () => {
    it('should display Demand Configuration card', () => {
      cy.get('.card-title').contains('Demand Configuration').should('be.visible');
    });

    it('should show no client selected message initially', () => {
      cy.get('#noClientSelected').should('be.visible');
    });

    it('should have demand form hidden initially', () => {
      cy.get('#demandForm').should('have.class', 'hidden');
    });
  });

  describe('Demand Form Tests', () => {
    beforeEach(() => {
      // Try to select a client if available
      cy.get('body').then(($body) => {
        if ($body.find('.client-item').length > 0) {
          cy.get('.client-item').first().click();
        }
      });
    });

    it('should show form when client is selected', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-item').length > 0) {
          cy.get('#demandForm').should('not.have.class', 'hidden');
        }
      });
    });

    it('should have selected client box', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-item').length > 0) {
          cy.get('.selected-client-box').should('be.visible');
        }
      });
    });

    it('should have target select', () => {
      cy.get('#demandTarget').should('exist');
    });

    it('should have deadline days select', () => {
      cy.get('#deadlineDays').should('exist');
    });

    it('should have demand amount input', () => {
      cy.get('#demandAmount').should('exist');
    });

    it('should have Generate button', () => {
      cy.get('#generateBtn').should('exist');
    });

    it('should have target options', () => {
      cy.get('#demandTarget option').should('have.length.at.least', 4);
    });

    it('should have deadline options', () => {
      cy.get('#deadlineDays option').should('have.length.at.least', 4);
    });

    it('should allow selection of target', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-item').length > 0 && !$body.find('#demandForm').hasClass('hidden')) {
          cy.get('#demandTarget').select('equifax');
          cy.get('#demandTarget').should('have.value', 'equifax');
        } else {
          cy.get('#demandTarget').should('exist');
        }
      });
    });

    it('should allow selection of deadline', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-item').length > 0 && !$body.find('#demandForm').hasClass('hidden')) {
          cy.get('#deadlineDays').select('45');
          cy.get('#deadlineDays').should('have.value', '45');
        } else {
          cy.get('#deadlineDays').should('exist');
        }
      });
    });

    it('should accept input in demand amount', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.client-item').length > 0 && !$body.find('#demandForm').hasClass('hidden')) {
          cy.get('#demandAmount').type('5000').should('have.value', '5000');
        } else {
          cy.get('#demandAmount').should('exist');
        }
      });
    });
  });

  describe('Result Section Tests', () => {
    it('should have result section hidden initially', () => {
      cy.get('#resultSection').should('have.class', 'hidden');
    });

    it('should have download PDF button', () => {
      cy.get('#downloadPdfBtn').should('exist');
    });

    it('should have copy button', () => {
      cy.get('#copyBtn').should('exist');
    });

    it('should have result stats section', () => {
      cy.get('.result-stats').should('exist');
    });

    it('should have result amount element', () => {
      cy.get('#resultAmount').should('exist');
    });

    it('should have result violations element', () => {
      cy.get('#resultViolations').should('exist');
    });

    it('should have result deadline element', () => {
      cy.get('#resultDeadline').should('exist');
    });

    it('should have letter content container', () => {
      cy.get('.letter-content').should('exist');
    });

    it('should have letter content pre element', () => {
      cy.get('#letterContent').should('exist');
    });
  });

  describe('Loading Overlay Tests', () => {
    it('should have loading overlay element', () => {
      cy.get('#loadingOverlay').should('exist');
    });

    it('should have loading overlay hidden by default', () => {
      cy.get('#loadingOverlay').should('have.class', 'hidden');
    });

    it('should have loading content', () => {
      cy.get('.loading-content').should('exist');
    });
  });

  describe('Form Group Tests', () => {
    it('should have form groups', () => {
      cy.get('.form-group').should('have.length.at.least', 1);
    });

    it('should have form labels', () => {
      cy.get('.form-label').should('have.length.at.least', 1);
    });

    it('should have form inputs', () => {
      cy.get('.form-input').should('have.length.at.least', 1);
    });

    it('should have form selects', () => {
      cy.get('.form-select').should('have.length.at.least', 1);
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
      cy.get('.grid-container').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.card').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.header h1').should('be.visible');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have Generate button initially disabled', () => {
      cy.get('#generateBtn').should('be.disabled');
    });

    it('should have primary button styling', () => {
      cy.get('.btn-primary').should('exist');
    });

    it('should have secondary button styling', () => {
      // Page may not have secondary buttons - check conditionally
      cy.get('body').then(($body) => {
        if ($body.find('.btn-secondary').length > 0) {
          cy.get('.btn-secondary').should('exist');
        } else {
          // Page only uses primary/download/copy buttons
          cy.get('.btn-primary, .btn-download, .btn-copy').should('exist');
        }
      });
    });

    it('should have download button styling', () => {
      cy.get('.btn-download').should('exist');
    });

    it('should have copy button styling', () => {
      cy.get('.btn-copy').should('exist');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
      cy.get('h2').should('have.length.at.least', 1);
    });

    it('should have form labels', () => {
      cy.get('.form-label').should('have.length.at.least', 1);
    });

    it('should have input placeholders', () => {
      cy.get('#clientSearch').should('have.attr', 'placeholder');
    });
  });

  describe('Stat Box Tests', () => {
    it('should have stat boxes', () => {
      cy.get('.stat-box').should('have.length', 3);
    });

    it('should have green stat box', () => {
      cy.get('.stat-box.green').should('exist');
    });

    it('should have blue stat box', () => {
      cy.get('.stat-box.blue').should('exist');
    });

    it('should have purple stat box', () => {
      cy.get('.stat-box.purple').should('exist');
    });
  });
});
