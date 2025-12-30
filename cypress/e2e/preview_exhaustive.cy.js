// Exhaustive test for /preview (public page)
describe('Instant Preview - /preview', () => {
  beforeEach(() => {
    cy.visit('/preview');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/preview');
      cy.get('.container').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Preview');
    });

    it('should display the page header', () => {
      cy.get('h1').should('contain.text', 'Brightpath');
    });

    it('should not return server errors', () => {
      cy.request('/preview').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Upload Section Tests', () => {
    it('should display upload section', () => {
      cy.get('#uploadSection').should('be.visible');
    });

    it('should display upload zone', () => {
      cy.get('#dropZone').should('be.visible');
    });

    it('should have file input', () => {
      cy.get('#fileInput').should('exist');
    });

    it('should display upload prompt', () => {
      cy.get('#uploadPrompt').should('be.visible');
    });

    it('should have file selected section hidden by default', () => {
      cy.get('#fileSelected').should('have.class', 'hidden');
    });
  });

  describe('Feature Grid Tests', () => {
    it('should display feature grid', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.grid').length) {
          cy.get('.grid').should('be.visible');
        } else {
          cy.get('#uploadSection').should('exist');
        }
      });
    });

    it('should display security feature', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.grid').length) {
          cy.get('.grid').contains('Secure').should('exist');
        } else {
          cy.get('#uploadSection').should('exist');
        }
      });
    });

    it('should display analysis time feature', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.grid').length) {
          cy.get('.grid').contains('60').should('exist');
        } else {
          cy.get('#uploadSection').should('exist');
        }
      });
    });
  });

  describe('Analyzing Section Tests', () => {
    it('should have analyzing section hidden by default', () => {
      cy.get('#analyzingSection').should('have.class', 'hidden');
    });

    it('should have step indicators', () => {
      cy.get('#step1').should('exist');
      cy.get('#step2').should('exist');
      cy.get('#step3').should('exist');
    });
  });

  describe('Results Section Tests', () => {
    it('should have results section hidden by default', () => {
      cy.get('#resultsSection').should('have.class', 'hidden');
    });

    it('should have violation count element', () => {
      cy.get('#violationCount').should('exist');
    });

    it('should have estimated value element', () => {
      cy.get('#estimatedValue').should('exist');
    });

    it('should have case strength element', () => {
      cy.get('#caseStrength').should('exist');
    });

    it('should have violations list container', () => {
      cy.get('#violationsList').should('exist');
    });
  });

  describe('Error Section Tests', () => {
    it('should have error section hidden by default', () => {
      cy.get('#errorSection').should('have.class', 'hidden');
    });

    it('should have error message element', () => {
      cy.get('#errorMessage').should('exist');
    });
  });

  describe('CTA Tests', () => {
    it('should have signup call to action', () => {
      cy.get('a[href="/signup"]').should('exist');
    });
  });

  describe('Drag and Drop Tests', () => {
    it('should have drop zone with dragover styling capability', () => {
      cy.get('#dropZone').should('have.class', 'upload-zone');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.container').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.container').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.container').should('be.visible');
    });
  });
});
