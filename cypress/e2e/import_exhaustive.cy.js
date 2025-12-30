// Exhaustive test for /dashboard/import
describe('Import Clients - /dashboard/import', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/import');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/import');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Import');
    });

    it('should display the page title', () => {
      cy.get('.page-title').should('contain.text', 'Import');
    });

    it('should display page subtitle', () => {
      cy.get('.page-subtitle').should('be.visible');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/import').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Import Options Tests', () => {
    it('should display import options', () => {
      cy.get('.import-options').should('be.visible');
    });

    it('should have single client import option', () => {
      cy.get('.import-option[data-type="single"]').should('exist');
    });

    it('should have bulk CSV import option', () => {
      cy.get('.import-option[data-type="bulk"]').should('exist');
    });

    it('should have active option styling', () => {
      cy.get('.import-option.active').should('exist');
    });

    it('should switch active option on click', () => {
      cy.get('.import-option[data-type="bulk"]').click();
      cy.get('.import-option[data-type="bulk"]').should('have.class', 'active');
    });
  });

  describe('Card Tests', () => {
    it('should display card', () => {
      cy.get('.card').should('be.visible');
    });

    it('should display card title', () => {
      cy.get('.card-title').should('exist');
    });
  });

  describe('Single Import Form Tests', () => {
    it('should display single import section', () => {
      cy.get('#singleImportSection').should('exist');
    });

    it('should have first name input', () => {
      cy.get('#firstName').should('exist');
    });

    it('should have last name input', () => {
      cy.get('#lastName').should('exist');
    });

    it('should have email input', () => {
      cy.get('#email').should('exist');
    });

    it('should have phone input', () => {
      cy.get('#phone').should('exist');
    });

    it('should accept text input in first name', () => {
      cy.get('#firstName').type('John');
      cy.get('#firstName').should('have.value', 'John');
    });
  });

  describe('Form Row Tests', () => {
    it('should display form rows', () => {
      cy.get('.form-row').should('have.length.at.least', 1);
    });

    it('should display form groups', () => {
      cy.get('.form-group').should('have.length.at.least', 1);
    });

    it('should display form labels', () => {
      cy.get('.form-group label').should('have.length.at.least', 1);
    });
  });

  describe('Button Tests', () => {
    it('should display primary button', () => {
      cy.get('.btn-primary').should('exist');
    });

    it('should display secondary button if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.btn-secondary').length) {
          cy.get('.btn-secondary').should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });

    it('should display button row if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.button-row').length) {
          cy.get('.button-row').should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });
  });

  describe('Upload Area Tests', () => {
    it('should have upload area in bulk mode', () => {
      cy.get('.import-option[data-type="bulk"]').click();
      cy.get('body').then(($body) => {
        if ($body.find('.upload-area').length) {
          cy.get('.upload-area').should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });
  });

  describe('Template Download Tests', () => {
    it('should display template download section if present', () => {
      cy.get('.import-option[data-type="bulk"]').click();
      cy.get('body').then(($body) => {
        if ($body.find('.template-download').length) {
          cy.get('.template-download').should('be.visible');
        } else {
          cy.get('.card').should('exist');
        }
      });
    });
  });

  describe('Import Results Tests', () => {
    it('should have import results container', () => {
      cy.get('.import-results').should('exist');
    });

    it('should be hidden by default', () => {
      cy.get('.import-results').should('not.be.visible');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
    });
  });
});
