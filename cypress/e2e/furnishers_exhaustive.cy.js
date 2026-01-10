// Exhaustive test for /dashboard/furnishers
describe('Furnisher Intelligence Database Page - /dashboard/furnishers', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/furnishers');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/furnishers');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Furnisher Intelligence Database');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/furnishers').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Furnisher Intelligence Database');
    });

    it('should display header subtitle', () => {
      cy.get('.header-subtitle').should('contain.text', 'Track creditor behavior patterns');
    });

    it('should display Sync from Cases button', () => {
      cy.get('.btn-secondary').contains('Sync from Cases').should('be.visible');
    });

    it('should display Add Furnisher button', () => {
      cy.get('.btn-primary').contains('Add Furnisher').should('be.visible');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display stat cards', () => {
      cy.get('.stat-card').should('have.length', 4);
    });

    it('should display Total Furnishers stat', () => {
      cy.get('.stat-label').contains('Total Furnishers').should('exist');
    });

    it('should display Most Common stat', () => {
      cy.get('.stat-label').contains('Most Common').should('exist');
    });

    it('should display Best Deletion Rate stat', () => {
      cy.get('.stat-label').contains('Best Deletion Rate').should('exist');
    });

    it('should display Slowest Response stat', () => {
      cy.get('.stat-label').contains('Slowest Response').should('exist');
    });

    it('should have highlight card styling', () => {
      cy.get('.stat-card.highlight').should('exist');
    });

    it('should display stat values', () => {
      cy.get('.stat-value').should('have.length.at.least', 4);
    });

    it('should display stat details', () => {
      cy.get('.stat-detail').should('have.length.at.least', 1);
    });
  });

  describe('Card Tests', () => {
    it('should display main card', () => {
      cy.get('.card').should('be.visible');
    });

    it('should display card header', () => {
      cy.get('.card-header').should('be.visible');
    });

    it('should display All Furnishers title', () => {
      cy.get('.card-title').should('contain.text', 'All Furnishers');
    });
  });

  describe('Filter Tests', () => {
    it('should display filters section', () => {
      cy.get('.filters').should('be.visible');
    });

    it('should have search input', () => {
      cy.get('#searchInput').should('be.visible');
    });

    it('should have industry filter dropdown', () => {
      cy.get('#industryFilter').should('be.visible');
    });

    it('should accept input in search field', () => {
      cy.get('#searchInput').type('test').should('have.value', 'test');
    });

    it('should have industry filter options', () => {
      cy.get('#industryFilter option').should('have.length.at.least', 1);
    });
  });

  describe('Table Tests', () => {
    it('should display table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table').should('be.visible');
        } else {
          cy.get('.empty-state').should('be.visible');
        }
      });
    });

    it('should have table headers if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table th').should('have.length.at.least', 1);
        }
      });
    });

    it('should have Furnisher Name column if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table th').contains('Furnisher Name').should('exist');
        }
      });
    });

    it('should have Industry column if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table th').contains('Industry').should('exist');
        }
      });
    });

    it('should have Disputes column if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table th').contains('Disputes').should('exist');
        }
      });
    });

    it('should have R1 Delete% column if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table th').contains('R1 Delete%').should('exist');
        }
      });
    });

    it('should have R2 Delete% column if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table th').contains('R2 Delete%').should('exist');
        }
      });
    });

    it('should have Avg Response column if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table th').contains('Avg Response').should('exist');
        }
      });
    });

    it('should have Settlements column if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table th').contains('Settlements').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have add modal element', () => {
      cy.get('#addModal').should('exist');
    });

    it('should have modal hidden by default', () => {
      cy.get('.modal-overlay.active').should('not.exist');
    });

    it('should open modal when Add Furnisher is clicked', () => {
      cy.get('.btn-primary').contains('Add Furnisher').click();
      cy.get('#addModal.active').should('be.visible');
    });

    it('should have modal close button', () => {
      cy.get('.modal-close').should('exist');
    });

    it('should close modal when close button is clicked', () => {
      cy.get('.btn-primary').contains('Add Furnisher').click();
      cy.get('#addModal.active').should('be.visible');
      cy.get('.modal-close').click();
      cy.get('#addModal.active').should('not.exist');
    });

    it('should display Add New Furnisher title in modal', () => {
      cy.get('.btn-primary').contains('Add Furnisher').click();
      cy.get('.modal-header h2').should('contain.text', 'Add New Furnisher');
    });
  });

  describe('Add Furnisher Form Tests', () => {
    beforeEach(() => {
      cy.get('.btn-primary').contains('Add Furnisher').click();
    });

    it('should have company name input', () => {
      cy.get('#furnisherName').should('exist');
    });

    it('should have industry select', () => {
      cy.get('#furnisherIndustry').should('exist');
    });

    it('should have parent company input', () => {
      cy.get('#furnisherParent').should('exist');
    });

    it('should have address textarea', () => {
      cy.get('#furnisherAddress').should('exist');
    });

    it('should have phone input', () => {
      cy.get('#furnisherPhone').should('exist');
    });

    it('should have fax input', () => {
      cy.get('#furnisherFax').should('exist');
    });

    it('should have email input', () => {
      cy.get('#furnisherEmail').should('exist');
    });

    it('should have website input', () => {
      cy.get('#furnisherWebsite').should('exist');
    });

    it('should have notes textarea', () => {
      cy.get('#furnisherNotes').should('exist');
    });

    it('should have Save Furnisher button', () => {
      cy.get('.modal-footer .btn-primary').contains('Save Furnisher').scrollIntoView().should('exist');
    });

    it('should have Cancel button', () => {
      cy.get('.modal-footer .btn-secondary').contains('Cancel').scrollIntoView().should('exist');
    });

    it('should accept input in company name field', () => {
      cy.get('#furnisherName').type('Test Company').should('have.value', 'Test Company');
    });

    it('should accept input in phone field', () => {
      cy.get('#furnisherPhone').type('555-123-4567').should('have.value', '555-123-4567');
    });

    it('should accept input in email field', () => {
      cy.get('#furnisherEmail').type('test@company.com').should('have.value', 'test@company.com');
    });
  });

  describe('Empty State Tests', () => {
    it('should display empty state when no furnishers', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length > 0) {
          cy.get('.empty-state').should('be.visible');
          cy.get('.empty-state h3').should('contain.text', 'No Furnishers Yet');
        }
      });
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.card').should('be.visible');
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
    it('should have clickable Sync from Cases button', () => {
      cy.get('.btn-secondary').contains('Sync from Cases').should('not.be.disabled');
    });

    it('should have clickable Add Furnisher button', () => {
      cy.get('.btn-primary').contains('Add Furnisher').should('not.be.disabled');
    });

    it('should have primary button styling', () => {
      cy.get('.btn-primary').should('exist');
    });

    it('should have secondary button styling', () => {
      cy.get('.btn-secondary').should('exist');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
    });

    it('should have form labels in modal', () => {
      cy.get('.btn-primary').contains('Add Furnisher').click();
      cy.get('.form-label').should('have.length.at.least', 1);
    });

    it('should have table headers for accessibility', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.data-table').length > 0) {
          cy.get('.data-table th').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have filterTable function', () => {
      cy.window().should('have.property', 'filterTable');
    });

    it('should have openAddModal function', () => {
      cy.window().should('have.property', 'openAddModal');
    });

    it('should have closeAddModal function', () => {
      cy.window().should('have.property', 'closeAddModal');
    });

    it('should have saveFurnisher function', () => {
      cy.window().should('have.property', 'saveFurnisher');
    });

    it('should have populateFromExisting function', () => {
      cy.window().should('have.property', 'populateFromExisting');
    });
  });
});
