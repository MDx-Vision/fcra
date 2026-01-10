// Exhaustive test for /dashboard/affiliates
describe('Affiliate Dashboard Page - /dashboard/affiliates', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/affiliates');
    cy.get('.main-content').should('exist');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/affiliates');
      cy.get('.main-content').should('exist');
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
      cy.get('.header h1').should('exist').and('contain.text', 'Affiliate');
    });

    it('should display header subtitle', () => {
      cy.get('.header-subtitle').should('exist');
    });

    it('should display Add Affiliate button', () => {
      cy.get('[data-testid="add-affiliate-btn"]').should('exist').and('contain.text', 'Add Affiliate');
    });

    it('should have clickable Add Affiliate button', () => {
      cy.get('[data-testid="add-affiliate-btn"]').should('not.be.disabled');
    });
  });

  describe('Stats Row Tests', () => {
    it('should display stats row', () => {
      cy.get('.stats-row').should('exist');
    });

    it('should display stat cards', () => {
      cy.get('.stat-card').should('have.length', 4);
    });

    it('should display Total Affiliates stat', () => {
      cy.get('[data-testid="stat-total-affiliates"]').should('exist');
      cy.get('.stat-label').contains('Total Affiliates').should('exist');
    });

    it('should display Total Referrals stat', () => {
      cy.get('[data-testid="stat-total-referrals"]').should('exist');
      cy.get('.stat-label').contains('Total Referrals').should('exist');
    });

    it('should display Pending Payouts stat', () => {
      cy.get('[data-testid="stat-pending-payouts"]').should('exist');
      cy.get('.stat-label').contains('Pending Payouts').should('exist');
    });

    it('should display Total Paid Out stat', () => {
      cy.get('[data-testid="stat-total-paid"]').should('exist');
      cy.get('.stat-label').contains('Total Paid').should('exist');
    });

    it('should display stat values', () => {
      cy.get('.stat-value').should('have.length.at.least', 4);
    });

    it('should display stat change indicators', () => {
      cy.get('.stat-change').should('have.length.at.least', 1);
    });
  });

  describe('Tab Tests', () => {
    it('should display tabs', () => {
      cy.get('.tabs').should('exist');
    });

    it('should have Affiliates tab', () => {
      cy.get('.tab').contains('Affiliates').should('exist');
    });

    it('should have Commissions tab', () => {
      cy.get('.tab').contains('Commissions').should('exist');
    });

    it('should have Payouts tab', () => {
      cy.get('.tab').contains('Payouts').should('exist');
    });

    it('should have active tab highlighted', () => {
      cy.get('.tab.active').should('exist');
    });

    it('should switch tabs when clicked', () => {
      cy.get('.tab').contains('Commissions').click();
      cy.get('.tab').contains('Commissions').should('have.class', 'active');
      cy.get('#tab-commissions').should('have.class', 'active');
    });
  });

  describe('Affiliates Tab Tests', () => {
    it('should display affiliates tab content by default', () => {
      cy.get('#tab-affiliates').should('have.class', 'active');
    });

    it('should display card with title', () => {
      cy.get('.card').should('exist');
      cy.get('.card-title').contains('Affiliates').should('exist');
    });

    it('should display search box', () => {
      cy.get('.search-box').should('exist');
    });

    it('should have search input', () => {
      cy.get('[data-testid="affiliate-search"]').should('exist');
    });

    it('should have status filter dropdown', () => {
      cy.get('[data-testid="affiliate-status-filter"]').should('exist');
    });

    it('should have placeholder text in search', () => {
      cy.get('[data-testid="affiliate-search"]').should('have.attr', 'placeholder').and('contain', 'Search');
    });

    it('should accept input in search field', () => {
      cy.get('[data-testid="affiliate-search"]').type('test').should('have.value', 'test');
    });
  });

  describe('Table Tests', () => {
    it('should display affiliates table', () => {
      cy.get('[data-testid="affiliates-table"]').should('exist');
    });

    it('should display table headers', () => {
      cy.get('[data-testid="affiliates-table"] th').should('have.length.at.least', 1);
    });

    it('should have Name column header', () => {
      cy.get('[data-testid="affiliates-table"] th').contains('Name').should('exist');
    });

    it('should have Email column header', () => {
      cy.get('[data-testid="affiliates-table"] th').contains('Email').should('exist');
    });

    it('should have Code column header', () => {
      cy.get('[data-testid="affiliates-table"] th').contains('Code').should('exist');
    });

    it('should have Status column header', () => {
      cy.get('[data-testid="affiliates-table"] th').contains('Status').should('exist');
    });

    it('should have Rate column header', () => {
      cy.get('[data-testid="affiliates-table"] th').contains('Rate').should('exist');
    });

    it('should have Referrals column header', () => {
      cy.get('[data-testid="affiliates-table"] th').contains('Referrals').should('exist');
    });

    it('should have Actions column header', () => {
      cy.get('[data-testid="affiliates-table"] th').contains('Actions').should('exist');
    });
  });

  describe('Modal Tests', () => {
    it('should have affiliate modal element', () => {
      cy.get('[data-testid="affiliate-modal"]').should('exist');
    });

    it('should have modal hidden by default', () => {
      cy.get('[data-testid="affiliate-modal"]').should('not.have.class', 'active');
    });

    it('should open modal when Add Affiliate is clicked', () => {
      cy.get('[data-testid="add-affiliate-btn"]').click();
      cy.get('[data-testid="affiliate-modal"]').should('have.class', 'active');
    });

    it('should have modal close button', () => {
      cy.get('.modal-close').should('exist');
    });

    it('should close modal when close button is clicked', () => {
      cy.get('[data-testid="add-affiliate-btn"]').click();
      cy.get('[data-testid="affiliate-modal"]').should('have.class', 'active');
      cy.get('[data-testid="affiliate-modal"] .modal-close').click();
      cy.get('[data-testid="affiliate-modal"]').should('not.have.class', 'active');
    });
  });

  describe('Add Affiliate Form Tests', () => {
    beforeEach(() => {
      cy.get('[data-testid="add-affiliate-btn"]').click();
      cy.get('[data-testid="affiliate-modal"]').should('have.class', 'active');
    });

    it('should display form in modal', () => {
      cy.get('#affiliate-form').should('exist');
    });

    it('should have name input', () => {
      cy.get('[data-testid="affiliate-name-input"]').should('exist');
    });

    it('should have email input', () => {
      cy.get('[data-testid="affiliate-email-input"]').should('exist');
    });

    it('should have phone input', () => {
      cy.get('[data-testid="affiliate-phone-input"]').should('exist');
    });

    it('should have commission rate select', () => {
      cy.get('[data-testid="affiliate-rate-select"]').should('exist');
    });

    it('should have parent affiliate select', () => {
      cy.get('[data-testid="affiliate-parent-select"]').should('exist');
    });

    it('should have status select', () => {
      cy.get('[data-testid="affiliate-status-select"]').should('exist');
    });

    it('should have payout method select', () => {
      cy.get('[data-testid="affiliate-payout-method-select"]').should('exist');
    });

    it('should have payout details input', () => {
      cy.get('[data-testid="affiliate-payout-details-input"]').should('exist');
    });

    it('should have notes textarea', () => {
      cy.get('[data-testid="affiliate-notes-input"]').should('exist');
    });

    it('should have Save Affiliate submit button', () => {
      cy.get('[data-testid="affiliate-save-btn"]').should('exist');
    });

    it('should have Cancel button', () => {
      cy.get('#affiliate-form .btn-secondary').contains('Cancel').should('exist');
    });
  });

  describe('Commissions Tab Tests', () => {
    beforeEach(() => {
      cy.get('.tab').contains('Commissions').click();
    });

    it('should display commissions tab content', () => {
      cy.get('#tab-commissions').should('have.class', 'active');
    });

    it('should have commissions table', () => {
      cy.get('[data-testid="commissions-table"]').should('exist');
    });

    it('should have commission status filter', () => {
      cy.get('[data-testid="commission-status-filter"]').should('exist');
    });
  });

  describe('Payouts Tab Tests', () => {
    beforeEach(() => {
      cy.get('.tab').contains('Payouts').click();
    });

    it('should display payouts tab content', () => {
      cy.get('#tab-payouts').should('have.class', 'active');
    });

    it('should have payouts table', () => {
      cy.get('[data-testid="payouts-table"]').should('exist');
    });

    it('should have Create Payout button', () => {
      cy.get('[data-testid="create-payout-btn"]').should('exist');
    });

    it('should have payout status filter', () => {
      cy.get('[data-testid="payout-status-filter"]').should('exist');
    });
  });

  describe('Payout Modal Tests', () => {
    beforeEach(() => {
      cy.get('.tab').contains('Payouts').click();
    });

    it('should have payout modal element', () => {
      cy.get('[data-testid="payout-modal"]').should('exist');
    });

    it('should open payout modal when Create Payout is clicked', () => {
      cy.get('[data-testid="create-payout-btn"]').click();
      cy.get('[data-testid="payout-modal"]').should('have.class', 'active');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('exist');
      cy.get('.header').should('exist');
      cy.get('.stats-row').should('exist');
      cy.get('.card').should('exist');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('exist');
      cy.get('.card').should('exist');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('exist');
      cy.get('.header h1').should('exist');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have primary button styling', () => {
      cy.get('.btn-primary').should('exist');
    });

    it('should have secondary button styling', () => {
      cy.get('[data-testid="add-affiliate-btn"]').click();
      cy.get('.btn-secondary').should('exist');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
    });

    it('should have form labels in modal', () => {
      cy.get('[data-testid="add-affiliate-btn"]').click();
      cy.get('#affiliate-form label').should('have.length.at.least', 1);
    });

    it('should have table headers for accessibility', () => {
      cy.get('[data-testid="affiliates-table"] th').should('have.length.at.least', 1);
    });
  });

  describe('Empty State Tests', () => {
    it('should display loading or empty state in table', () => {
      cy.get('#affiliates-table-body').should('exist');
    });
  });
});
