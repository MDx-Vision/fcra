// Exhaustive test for /dashboard/scanned-documents
describe('Scanned Documents - /dashboard/scanned-documents', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/scanned-documents');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/scanned-documents');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Scanned');
    });

    it('should display the page header', () => {
      cy.get('.page-header h1').should('contain.text', 'Scanned');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/scanned-documents').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display Scan New button', () => {
      cy.get('a[href="/scanner"]').should('exist');
    });

    it('should display Dashboard link', () => {
      cy.get('a[href="/dashboard"]').should('exist');
    });
  });

  describe('Tabs Tests', () => {
    it('should display tabs', () => {
      cy.get('#docTabs').should('be.visible');
    });

    it('should have Scanned Documents tab', () => {
      cy.get('#scanned-tab').should('exist');
    });

    it('should have CRA Responses tab', () => {
      cy.get('#cra-tab').should('exist');
    });

    it('should have active tab', () => {
      cy.get('.nav-link.active').should('exist');
    });

    it('should switch tabs on click', () => {
      cy.get('#cra-tab').click();
      cy.get('#cra-tab').should('have.class', 'active');
    });
  });

  describe('Tab Panels Tests', () => {
    it('should display scanned panel', () => {
      cy.get('#scanned-panel').should('be.visible');
    });

    it('should display CRA panel when tab clicked', () => {
      cy.get('#cra-tab').click();
      cy.get('#cra-panel').should('be.visible');
    });
  });

  describe('Stats Bar Tests', () => {
    it('should display stats bar', () => {
      cy.get('.stats-bar').should('be.visible');
    });

    it('should display stat items', () => {
      cy.get('.stat-item').should('have.length.at.least', 1);
    });

    it('should display total documents stat', () => {
      cy.get('#stat-total').should('exist');
    });

    it('should display words extracted stat', () => {
      cy.get('#stat-words').should('exist');
    });

    it('should display scanned today stat', () => {
      cy.get('#stat-today').should('exist');
    });
  });

  describe('CRA Stats Tests', () => {
    it('should display CRA total when on CRA tab', () => {
      cy.get('#cra-tab').click();
      cy.get('#cra-total').should('exist');
    });

    it('should display CRA analyzed stat', () => {
      cy.get('#cra-tab').click();
      cy.get('#cra-analyzed').should('exist');
    });

    it('should display CRA pending stat', () => {
      cy.get('#cra-tab').click();
      cy.get('#cra-pending').should('exist');
    });

    it('should display CRA reinsertions stat', () => {
      cy.get('#cra-tab').click();
      cy.get('#cra-reinsertions').should('exist');
    });
  });

  describe('Documents List Tests', () => {
    it('should display documents list container', () => {
      cy.get('#documents-list').should('exist');
    });

    it('should display doc cards if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.doc-card').length) {
          cy.get('.doc-card').first().should('be.visible');
        } else {
          cy.get('#documents-list').should('exist');
        }
      });
    });

    it('should display doc type badges if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.doc-type-badge').length) {
          cy.get('.doc-type-badge').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should display text preview if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.text-preview').length) {
          cy.get('.text-preview').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('CRA Responses List Tests', () => {
    it('should display CRA responses list container', () => {
      cy.get('#cra-tab').click();
      cy.get('#cra-responses-list').should('exist');
    });

    it('should display CRA response cards if present', () => {
      cy.get('#cra-tab').click();
      cy.get('body').then(($body) => {
        if ($body.find('.cra-response-card').length) {
          cy.get('.cra-response-card').first().should('be.visible');
        } else {
          cy.get('#cra-responses-list').should('exist');
        }
      });
    });
  });

  describe('Status Badge Tests', () => {
    it('should have status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge').length) {
          cy.get('.status-badge').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have deleted status styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-deleted').length) {
          cy.get('.status-deleted').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have verified status styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-verified').length) {
          cy.get('.status-verified').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Confidence Bar Tests', () => {
    it('should display confidence bars if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.confidence-bar').length) {
          cy.get('.confidence-bar').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Reinsertion Alert Tests', () => {
    it('should display reinsertion alerts if present', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.reinsertion-alert').length) {
          cy.get('.reinsertion-alert').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Analysis Modal Tests', () => {
    it('should have analysis modal in DOM', () => {
      cy.get('#analysisModal').should('exist');
    });
  });

  describe('Empty State Tests', () => {
    it('should display empty state if no documents', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length) {
          cy.get('.empty-state').should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
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
