// Exhaustive test for /dashboard/api-keys (API Management page)
// Note: In CI mode, the app auto-sets staff session via ci_mock_auth() in app.py
// This means we can directly visit authenticated pages without manual login
describe('API Management Page Tests', () => {
  beforeEach(() => {
    // In CI mode, ci_mock_auth() auto-sets staff_id in session for non-login pages
    // So we can directly visit the dashboard page
    cy.visit('/dashboard/api-keys');
    cy.url().should('include', '/dashboard/api-keys');
  });

  describe('Page Load Tests', () => {
    it('should load the API management page', () => {
      cy.get('[data-testid="api-management-container"]').should('be.visible');
      cy.url().should('include', '/dashboard/api-keys');
    });

    it('should display the page title', () => {
      cy.get('[data-testid="api-management-title"]').should('contain.text', 'API Management');
    });

    it('should not have server errors', () => {
      cy.request('/dashboard/api-keys').then((response) => {
        expect(response.status).to.eq(200);
      });
    });
  });

  describe('Header Actions', () => {
    it('should display View API Docs button', () => {
      cy.get('[data-testid="view-api-docs-btn"]')
        .should('be.visible')
        .and('have.attr', 'href', '/dashboard/api-docs');
    });

    it('should display Generate API Key button', () => {
      cy.get('[data-testid="generate-api-key-btn"]')
        .should('be.visible')
        .and('contain.text', 'Generate API Key');
    });
  });

  describe('Stats Grid', () => {
    it('should display stats grid', () => {
      cy.get('[data-testid="stats-grid"]').should('be.visible');
    });

    it('should display total keys stat', () => {
      cy.get('[data-testid="stat-total-keys"]').should('be.visible');
      cy.get('[data-testid="stat-total-keys"]').contains('Total API Keys');
    });

    it('should display active keys stat', () => {
      cy.get('[data-testid="stat-active-keys"]').should('be.visible');
      cy.get('[data-testid="stat-active-keys"]').contains('Active Keys');
    });

    it('should display total webhooks stat', () => {
      cy.get('[data-testid="stat-total-webhooks"]').should('be.visible');
      cy.get('[data-testid="stat-total-webhooks"]').contains('Total Webhooks');
    });

    it('should display active webhooks stat', () => {
      cy.get('[data-testid="stat-active-webhooks"]').should('be.visible');
      cy.get('[data-testid="stat-active-webhooks"]').contains('Active Webhooks');
    });
  });

  describe('Tabs', () => {
    it('should display tabs', () => {
      cy.get('[data-testid="tabs"]').should('be.visible');
    });

    it('should have API Keys tab active by default', () => {
      cy.get('[data-testid="tab-api-keys"]').should('have.class', 'active');
    });

    it('should switch to Webhooks tab when clicked', () => {
      cy.get('[data-testid="tab-webhooks"]').click();
      cy.get('[data-testid="tab-webhooks"]').should('have.class', 'active');
      cy.get('[data-testid="webhooks-tab"]').should('have.class', 'active');
    });

    it('should switch to Usage Analytics tab when clicked', () => {
      cy.get('[data-testid="tab-usage"]').click();
      cy.get('[data-testid="tab-usage"]').should('have.class', 'active');
      cy.get('[data-testid="usage-tab"]').should('have.class', 'active');
    });
  });

  describe('API Keys Tab', () => {
    it('should display API keys card', () => {
      cy.get('[data-testid="api-keys-card"]').should('be.visible');
    });

    it('should display API keys table or empty state', () => {
      cy.get('[data-testid="api-keys-card"]').then(($card) => {
        if ($card.find('[data-testid="api-keys-table"]').length) {
          cy.get('[data-testid="api-keys-table"]').should('be.visible');
        } else {
          cy.get('[data-testid="api-keys-empty"]').should('be.visible');
          cy.get('[data-testid="api-keys-empty"]').contains('No API Keys');
        }
      });
    });
  });

  describe('Webhooks Tab', () => {
    beforeEach(() => {
      cy.get('[data-testid="tab-webhooks"]').click();
    });

    it('should display webhooks card', () => {
      cy.get('[data-testid="webhooks-card"]').should('be.visible');
    });

    it('should display Add Webhook button', () => {
      cy.get('[data-testid="add-webhook-btn"]')
        .should('be.visible')
        .and('contain.text', 'Add Webhook');
    });

    it('should display webhooks table or empty state', () => {
      cy.get('[data-testid="webhooks-card"]').then(($card) => {
        if ($card.find('[data-testid="webhooks-table"]').length) {
          cy.get('[data-testid="webhooks-table"]').should('be.visible');
        } else {
          cy.get('[data-testid="webhooks-empty"]').should('be.visible');
          cy.get('[data-testid="webhooks-empty"]').contains('No Webhooks');
        }
      });
    });
  });

  describe('Usage Analytics Tab', () => {
    beforeEach(() => {
      cy.get('[data-testid="tab-usage"]').click();
    });

    it('should display usage card', () => {
      cy.get('[data-testid="usage-card"]').should('be.visible');
    });

    it('should display usage content with empty state initially', () => {
      cy.get('[data-testid="usage-content"]').should('be.visible');
      cy.get('[data-testid="usage-empty"]').should('be.visible');
      cy.get('[data-testid="usage-empty"]').contains('Select an API Key');
    });
  });

  describe('Create API Key Modal', () => {
    it('should open modal when Generate API Key is clicked', () => {
      cy.get('[data-testid="generate-api-key-btn"]').click();
      cy.get('[data-testid="create-key-modal"]').should('have.class', 'active');
    });

    it('should display create key form', () => {
      cy.get('[data-testid="generate-api-key-btn"]').click();
      cy.get('[data-testid="create-key-form"]').should('be.visible');
    });

    it('should close modal when close button is clicked', () => {
      cy.get('[data-testid="generate-api-key-btn"]').click();
      cy.get('[data-testid="create-key-modal-close"]').click();
      cy.get('[data-testid="create-key-modal"]').should('not.have.class', 'active');
    });
  });

  describe('Create Webhook Modal', () => {
    beforeEach(() => {
      cy.get('[data-testid="tab-webhooks"]').click();
    });

    it('should open modal when Add Webhook is clicked', () => {
      cy.get('[data-testid="add-webhook-btn"]').click();
      cy.get('[data-testid="create-webhook-modal"]').should('have.class', 'active');
    });

    it('should display create webhook form', () => {
      cy.get('[data-testid="add-webhook-btn"]').click();
      cy.get('[data-testid="create-webhook-form"]').should('be.visible');
    });

    it('should close modal when close button is clicked', () => {
      cy.get('[data-testid="add-webhook-btn"]').click();
      cy.get('[data-testid="create-webhook-modal-close"]').click();
      cy.get('[data-testid="create-webhook-modal"]').should('not.have.class', 'active');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('[data-testid="api-management-container"]').should('be.visible');
      cy.get('[data-testid="stats-grid"]').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('[data-testid="api-management-container"]').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('[data-testid="api-management-container"]').should('be.visible');
    });
  });

  describe('Navigation', () => {
    it('should navigate to API docs when View API Docs is clicked', () => {
      cy.get('[data-testid="view-api-docs-btn"]').click();
      cy.url().should('include', '/dashboard/api-docs');
    });
  });
});
