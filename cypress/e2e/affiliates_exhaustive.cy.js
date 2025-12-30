// Exhaustive test for /dashboard/affiliates
describe('Affiliate Management Page - /dashboard/affiliates', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/affiliates');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/affiliates');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Affiliate');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/affiliates').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Affiliate Management');
    });

    it('should display Add Affiliate button', () => {
      cy.get('.btn-primary').contains('Add Affiliate').should('be.visible');
    });

    it('should have clickable Add Affiliate button', () => {
      cy.get('.btn-primary').contains('Add Affiliate').should('not.be.disabled');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display stat cards', () => {
      cy.get('.stat-card').should('have.length', 4);
    });

    it('should display Total Pending Payouts stat', () => {
      cy.get('.stat-card.highlight .stat-label').should('contain.text', 'Total Pending Payouts');
    });

    it('should display Total Affiliates stat', () => {
      cy.get('.stat-label').contains('Total Affiliates').should('exist');
    });

    it('should display Total Referrals stat', () => {
      cy.get('.stat-label').contains('Total Referrals').should('exist');
    });

    it('should display Total Paid Out stat', () => {
      cy.get('.stat-label').contains('Total Paid Out').should('exist');
    });

    it('should display stat values', () => {
      cy.get('.stat-value').should('have.length.at.least', 4);
    });

    it('should display stat change indicators', () => {
      cy.get('.stat-change').should('have.length.at.least', 1);
    });
  });

  describe('Content Card Tests', () => {
    it('should display main content card', () => {
      cy.get('.content-card').should('be.visible');
    });

    it('should display All Affiliates section title', () => {
      cy.get('.section-title').contains('All Affiliates').should('be.visible');
    });
  });

  describe('Filter Tests', () => {
    it('should display filters section', () => {
      cy.get('.filters').should('exist');
    });

    it('should display filter buttons', () => {
      cy.get('.filter-btn').should('have.length.at.least', 1);
    });

    it('should have All filter', () => {
      cy.get('.filter-btn').contains('All').should('exist');
    });

    it('should have Active filter', () => {
      cy.get('.filter-btn').contains('Active').should('exist');
    });

    it('should have Pending filter', () => {
      cy.get('.filter-btn').contains('Pending').should('exist');
    });

    it('should have Suspended filter', () => {
      cy.get('.filter-btn').contains('Suspended').should('exist');
    });

    it('should have clickable filter buttons', () => {
      cy.get('.filter-btn').first().should('not.be.disabled');
    });

    it('should have active filter highlighted', () => {
      cy.get('.filter-btn.active').should('exist');
    });
  });

  describe('Search Tests', () => {
    it('should display search box', () => {
      cy.get('.search-box').should('be.visible');
    });

    it('should have search input', () => {
      cy.get('.search-box input').should('exist');
    });

    it('should have placeholder text', () => {
      cy.get('.search-box input').should('have.attr', 'placeholder', 'Search affiliates...');
    });

    it('should accept input in search field', () => {
      cy.get('.search-box input').type('test').should('have.value', 'test');
    });
  });

  describe('Table Tests', () => {
    it('should display table or empty state', () => {
      cy.get('.content-card').then(($card) => {
        const hasTable = $card.find('table').length > 0;
        const hasEmptyState = $card.find('.empty-state').length > 0;
        expect(hasTable || hasEmptyState).to.be.true;
      });
    });

    it('should display table headers if table exists', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').should('have.length.at.least', 1);
        }
      });
    });

    it('should have Affiliate column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').contains('Affiliate').should('exist');
        }
      });
    });

    it('should have Code column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').contains('Code').should('exist');
        }
      });
    });

    it('should have Referrals column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').contains('Referrals').should('exist');
        }
      });
    });

    it('should have Earnings column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').contains('Earnings').should('exist');
        }
      });
    });

    it('should have Status column header', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').contains('Status').should('exist');
        }
      });
    });
  });

  describe('Badge Tests', () => {
    it('should display status badges if affiliates exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table tbody tr').length > 0) {
          cy.get('.status-badge').should('have.length.at.least', 1);
        }
      });
    });

    it('should display code badges if affiliates exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table tbody tr').length > 0) {
          cy.get('.code-badge').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Action Button Tests', () => {
    it('should display action buttons if affiliates exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table tbody tr').length > 0) {
          cy.get('.action-btn').should('have.length.at.least', 1);
        }
      });
    });

    it('should have View button if affiliates exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table tbody tr').length > 0) {
          cy.get('.action-btn').contains('View').should('exist');
        }
      });
    });

    it('should have Edit button if affiliates exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table tbody tr').length > 0) {
          cy.get('.action-btn').contains('Edit').should('exist');
        }
      });
    });
  });

  describe('Modal Tests', () => {
    it('should have add affiliate modal element', () => {
      cy.get('#addAffiliateModal').should('exist');
    });

    it('should have modal hidden by default', () => {
      cy.get('.modal-overlay.active').should('not.exist');
    });

    it('should open modal when Add Affiliate is clicked', () => {
      cy.get('.btn-primary').contains('Add Affiliate').click();
      cy.get('#addAffiliateModal.active').should('be.visible');
    });

    it('should have modal close button', () => {
      cy.get('.modal-close').should('exist');
    });

    it('should close modal when close button is clicked', () => {
      cy.get('.btn-primary').contains('Add Affiliate').click();
      cy.get('#addAffiliateModal.active').should('be.visible');
      cy.get('.modal-close').click();
      cy.get('#addAffiliateModal.active').should('not.exist');
    });
  });

  describe('Add Affiliate Form Tests', () => {
    beforeEach(() => {
      cy.get('.btn-primary').contains('Add Affiliate').click();
    });

    it('should display form in modal', () => {
      cy.get('#addAffiliateForm').should('be.visible');
    });

    it('should have name input', () => {
      cy.get('#addAffiliateForm input[name="name"]').should('exist');
    });

    it('should have email input', () => {
      cy.get('#addAffiliateForm input[name="email"]').should('exist');
    });

    it('should have phone input', () => {
      cy.get('#addAffiliateForm input[name="phone"]').should('exist');
    });

    it('should have company name input', () => {
      cy.get('#addAffiliateForm input[name="company_name"]').should('exist');
    });

    it('should have commission rate inputs', () => {
      cy.get('#addAffiliateForm input[name="commission_rate_1"]').should('exist');
      cy.get('#addAffiliateForm input[name="commission_rate_2"]').should('exist');
    });

    it('should have status select', () => {
      cy.get('#addAffiliateForm select[name="status"]').should('exist');
    });

    it('should have payout method select', () => {
      cy.get('#addAffiliateForm select[name="payout_method"]').should('exist');
    });

    it('should have Create Affiliate submit button', () => {
      cy.get('#addAffiliateForm .btn-primary').contains('Create Affiliate').should('be.visible');
    });

    it('should have Cancel button', () => {
      cy.get('#addAffiliateForm .btn-secondary').contains('Cancel').should('be.visible');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.content-card').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.content-card').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.header h1').should('be.visible');
    });
  });

  describe('Button Functionality Tests', () => {
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
      cy.get('.btn-primary').contains('Add Affiliate').click();
      cy.get('#addAffiliateForm label').should('have.length.at.least', 1);
    });

    it('should have table headers for accessibility', () => {
      cy.get('body').then(($body) => {
        if ($body.find('table').length) {
          cy.get('table th').should('have.length.at.least', 1);
        }
      });
    });
  });

  describe('Empty State Tests', () => {
    it('should display empty state when no affiliates', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.empty-state').length > 0) {
          cy.get('.empty-state').should('be.visible');
          cy.get('.empty-state h3').should('contain.text', 'No affiliates yet');
        }
      });
    });
  });
});
