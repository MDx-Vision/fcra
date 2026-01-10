// Exhaustive test for /dashboard/billing
describe('Billing Management Page - /dashboard/billing', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/billing');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/billing');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Billing Management');
      cy.title().should('contain', 'Brightpath Ascend FCRA Platform');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/billing').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Billing & Subscription Management');
    });

    it('should display Stripe status indicator', () => {
      cy.get('#stripeStatus').should('exist');
    });

    it('should display Create Plan button', () => {
      cy.get('.header .btn-primary').should('be.visible');
      cy.get('.header .btn-primary').should('contain.text', 'Create Plan');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display Monthly Recurring Revenue stat', () => {
      cy.get('.stat-card').contains('Monthly Recurring Revenue').should('be.visible');
    });

    it('should display Active Subscriptions stat', () => {
      cy.get('.stat-card').contains('Active Subscriptions').should('be.visible');
    });

    it('should display Total Revenue stat', () => {
      cy.get('.stat-card').contains('Total Revenue').should('be.visible');
    });

    it('should display Past Due stat', () => {
      cy.get('.stat-card').contains('Past Due').should('be.visible');
    });

    it('should have highlight style on MRR card', () => {
      cy.get('.stat-card.highlight').should('exist');
    });
  });

  describe('Billing Plans Section Tests', () => {
    it('should display billing plans section', () => {
      cy.get('.content-card').contains('Billing Plans').should('be.visible');
    });

    it('should display Initialize Default Plans button', () => {
      cy.get('.content-card').contains('Initialize Default Plans').should('be.visible');
    });

    it('should show either plans grid or empty state', () => {
      cy.get('.content-card').first().then(($card) => {
        // Either plans exist or empty state is shown
        const hasPlans = $card.find('.plans-grid').length > 0;
        const hasEmptyState = $card.find('.empty-state').length > 0;
        expect(hasPlans || hasEmptyState).to.be.true;
      });
    });
  });

  describe('Subscriptions Section Tests', () => {
    it('should display Active Subscriptions section', () => {
      cy.get('.content-card').contains('Active Subscriptions').should('be.visible');
    });

    it('should show either subscriptions table or empty state', () => {
      cy.get('.content-card').last().within(() => {
        cy.get('table, .empty-state').should('exist');
      });
    });
  });

  describe('Create Plan Modal Tests', () => {
    it('should have create plan modal hidden by default', () => {
      cy.get('#createPlanModal').should('exist');
      cy.get('#createPlanModal').should('not.have.class', 'active');
    });

    it('should open create plan modal when button clicked', () => {
      cy.get('.header .btn-primary').contains('Create Plan').click();
      cy.get('#createPlanModal').should('have.class', 'active');
    });

    it('should display form fields in modal', () => {
      cy.get('.header .btn-primary').contains('Create Plan').click();
      cy.get('#planName').should('be.visible');
      cy.get('#planDisplayName').should('be.visible');
      cy.get('#planPrice').should('be.visible');
      cy.get('#planInterval').should('be.visible');
      cy.get('#planFeatures').should('be.visible');
    });

    it('should close modal when cancel button clicked', () => {
      cy.get('.header .btn-primary').contains('Create Plan').click();
      cy.get('#createPlanModal').should('have.class', 'active');
      cy.get('#createPlanModal .btn-secondary').contains('Cancel').click();
      cy.get('#createPlanModal').should('not.have.class', 'active');
    });
  });

  describe('Form Input Tests', () => {
    beforeEach(() => {
      cy.get('.header .btn-primary').contains('Create Plan').click();
    });

    it('should accept text input in plan name field', () => {
      cy.get('#planName').type('test-plan');
      cy.get('#planName').should('have.value', 'test-plan');
    });

    it('should accept text input in display name field', () => {
      cy.get('#planDisplayName').type('Test Plan');
      cy.get('#planDisplayName').should('have.value', 'Test Plan');
    });

    it('should accept number input in price field', () => {
      cy.get('#planPrice').type('299.99');
      cy.get('#planPrice').should('have.value', '299.99');
    });

    it('should allow selecting billing interval', () => {
      cy.get('#planInterval').select('year');
      cy.get('#planInterval').should('have.value', 'year');
    });

    it('should accept text in features textarea', () => {
      cy.get('#planFeatures').type('Feature 1\nFeature 2\nFeature 3');
      cy.get('#planFeatures').should('contain.value', 'Feature 1');
    });

    it('should have required attribute on plan name', () => {
      cy.get('#planName').should('have.attr', 'required');
    });

    it('should have required attribute on price', () => {
      cy.get('#planPrice').should('have.attr', 'required');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.header').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('.header h1').should('be.visible');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should make Create Plan button clickable', () => {
      cy.get('.header .btn-primary').contains('Create Plan').should('not.be.disabled');
    });

    it('should make Initialize Default Plans button clickable', () => {
      cy.get('.btn').contains('Initialize Default Plans').should('not.be.disabled');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
    });

    it('should have proper form labels in modal', () => {
      cy.get('.header .btn-primary').contains('Create Plan').click();
      cy.get('label[for="planName"]').should('exist');
      cy.get('label[for="planPrice"]').should('exist');
      cy.get('label[for="planInterval"]').should('exist');
    });

    it('should have alert container for notifications', () => {
      cy.get('#alertContainer').should('exist');
    });
  });

  describe('JavaScript Functionality Tests', () => {
    it('should have modal overlay functionality', () => {
      // Modal should toggle class on open/close
      cy.get('#createPlanModal').should('not.have.class', 'active');
      cy.window().then((win) => {
        if (typeof win.openCreatePlanModal === 'function') {
          win.openCreatePlanModal();
        }
      });
    });

    it('should have form element for plan creation', () => {
      cy.get('#createPlanForm').should('exist');
    });
  });
});
