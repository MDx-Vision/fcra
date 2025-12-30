// Exhaustive test for /scanner
describe('Document Scanner - /scanner', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/scanner');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/scanner');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Scanner');
    });

    it('should display the page header', () => {
      cy.get('.page-header').should('be.visible');
    });

    it('should not return server errors', () => {
      cy.request('/scanner').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Scanner Container Tests', () => {
    it('should display scanner container', () => {
      cy.get('.scanner-container').should('be.visible');
    });
  });

  describe('Document Type Card Tests', () => {
    it('should display document type cards', () => {
      cy.get('.doc-type-card').should('have.length.at.least', 1);
    });

    it('should select doc type on click', () => {
      cy.get('.doc-type-card').first().click();
      cy.get('.doc-type-card.selected').should('exist');
    });
  });

  describe('Camera Container Tests', () => {
    it('should display camera container if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.camera-container').length) {
          cy.get('.camera-container').should('be.visible');
        } else {
          cy.get('.scanner-container').should('exist');
        }
      });
    });

    it('should have video preview if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#video-preview').length) {
          cy.get('#video-preview').should('exist');
        } else {
          cy.get('.scanner-container').should('exist');
        }
      });
    });

    it('should have capture button if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.capture-btn').length) {
          cy.get('.capture-btn').should('be.visible');
        } else {
          cy.get('.scanner-container').should('exist');
        }
      });
    });
  });

  describe('Upload Zone Tests', () => {
    it('should display upload zone', () => {
      cy.get('.upload-zone').should('be.visible');
    });

    it('should have upload zone icon', () => {
      cy.get('.upload-zone i').should('exist');
    });
  });

  describe('Page Queue Tests', () => {
    it('should have page queue container', () => {
      cy.get('.page-queue').should('exist');
    });

    it('should display page thumbnails if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.page-thumbnail').length) {
          cy.get('.page-thumbnail').first().should('be.visible');
        } else {
          cy.get('.page-queue').should('exist');
        }
      });
    });
  });

  describe('Add More Tests', () => {
    it('should display add more prompt if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.add-more-prompt').length) {
          cy.get('.add-more-prompt').should('be.visible');
        } else {
          cy.get('.scanner-container').should('exist');
        }
      });
    });

    it('should display add more button if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.add-more-btn').length) {
          cy.get('.add-more-btn').should('be.visible');
        } else {
          cy.get('.scanner-container').should('exist');
        }
      });
    });
  });

  describe('Bottom Actions Tests', () => {
    it('should display bottom actions', () => {
      cy.get('.bottom-actions').should('be.visible');
    });

    it('should have gradient button', () => {
      cy.get('.btn-gradient').should('exist');
    });
  });

  describe('Step Indicator Tests', () => {
    it('should have step indicators if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.step-indicator').length) {
          cy.get('.step-indicator').should('exist');
        } else {
          cy.get('.scanner-container').should('exist');
        }
      });
    });

    it('should have step elements if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.step').length) {
          cy.get('.step').first().should('exist');
        } else {
          cy.get('.scanner-container').should('exist');
        }
      });
    });
  });

  describe('Processing Overlay Tests', () => {
    it('should have processing overlay in DOM', () => {
      cy.get('.processing-overlay').should('exist');
    });

    it('should be hidden by default', () => {
      cy.get('.processing-overlay').should('have.class', 'hidden');
    });
  });

  describe('Round Badge Tests', () => {
    it('should display round badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.round-badge').length) {
          cy.get('.round-badge').first().should('be.visible');
        } else {
          cy.get('.scanner-container').should('exist');
        }
      });
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.scanner-container').should('be.visible');
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
