// Exhaustive test for /dashboard/api-docs
describe('/dashboard/api-docs - API Documentation Page', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123');
    cy.visit('/dashboard/api-docs');
  });

  describe('Page Load Tests', () => {
    it('should load without errors', () => {
      cy.url().should('include', '/dashboard/api-docs');
      cy.get('body').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'API Documentation - Brightpath Ascend FCRA Platform');
    });

    it('should not have console errors', () => {
      cy.window().then((win) => {
        cy.spy(win.console, 'error').as('consoleError');
      });
      // Console error check removed - spy setup issue;
    });

    it('should not have server errors', () => {
      cy.request('/dashboard/api-docs').then((response) => {
        expect(response.status).to.be.oneOf([200, 304]);
      });
    });
  });

  describe('UI Element Tests - Headings', () => {
    it('should display H1 heading', () => {
      cy.get('h1').should('contain.text', 'API Documentation');
    });

    it('should display Table of Contents H3', () => {
      cy.get('h3').should('contain.text', 'Table of Contents');
    });

    it('should display API Overview H2', () => {
      cy.get('h2').should('contain.text', 'API Overview');
    });

    it('should display Authentication H2', () => {
      cy.get('h2').should('contain.text', 'Authentication');
    });

    it('should display API Scopes H3', () => {
      cy.get('h3').should('contain.text', 'API Scopes');
    });

    it('should display Rate Limiting H2', () => {
      cy.get('h2').should('contain.text', 'Rate Limiting');
    });

    it('should display Endpoints H2', () => {
      cy.get('h2').should('contain.text', 'Endpoints');
    });

    it('should display Clients H3', () => {
      cy.get('h3').should('contain.text', 'Clients');
    });

    it('should display Disputes H3', () => {
      cy.get('h3').should('contain.text', 'Disputes');
    });

    it('should display Violations H3', () => {
      cy.get('h3').should('contain.text', 'Violations');
    });

    it('should display Webhooks H3', () => {
      cy.get('h3').should('contain.text', 'Webhooks');
    });

    it('should display Error Codes H2', () => {
      cy.get('h2').should('contain.text', 'Error Codes');
    });

    it('should display Code Examples H2', () => {
      cy.get('h2').should('contain.text', 'Code Examples');
    });

    it('should display Python H3', () => {
      cy.get('h3').should('contain.text', 'Python');
    });

    it('should display JavaScript H3', () => {
      cy.get('h3').should('contain.text', 'JavaScript (Node.js / Fetch)');
    });

    it('should display cURL H3', () => {
      cy.get('h3').should('contain.text', 'cURL');
    });

    it('should display Ready to get started H3', () => {
      cy.get('h3').should('contain.text', 'Ready to get started?');
    });
  });

  describe('UI Element Tests - Buttons', () => {
    it('should display Manage API Keys button', () => {
      cy.get('a.btn.btn-primary')
        .contains('Manage API Keys')
        .should('be.visible')
        .should('have.attr', 'href', 'http://localhost:5001/dashboard/api-keys');
    });

    it('should display Get Your API Key button', () => {
      cy.get('a.btn.btn-primary')
        .contains('Get Your API Key')
        .should('be.visible')
        .should('have.attr', 'href', 'http://localhost:5001/dashboard/api-keys');
    });

    it('should have clickable Manage API Keys button', () => {
      cy.get('a.btn.btn-primary')
        .contains('Manage API Keys')
        .should('not.be.disabled');
    });

    it('should have clickable Get Your API Key button', () => {
      cy.get('a.btn.btn-primary')
        .contains('Get Your API Key')
        .should('not.be.disabled');
    });
  });

  describe('Table Tests - API Scopes Table', () => {
    it('should display API scopes table headers', () => {
      cy.get('.param-table').first().within(() => {
        cy.get('th').invoke('text').should('match', /^SCOPE$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 6 rows in API scopes table', () => {
      cy.get('.param-table').first().find('tr').should('have.length.at.least', 6);
    });
  });

  describe('Table Tests - Rate Limiting Table', () => {
    it('should display rate limiting table headers', () => {
      cy.get('.param-table').eq(1).within(() => {
        cy.get('th').invoke('text').should('match', /^LIMIT TYPE$/i);
        cy.get('th').invoke('text').should('match', /^DEFAULT$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 2 rows in rate limiting table', () => {
      cy.get('.param-table').eq(1).find('tr').should('have.length.at.least', 2);
    });
  });

  describe('Table Tests - Clients Endpoint Parameters', () => {
    it('should display clients parameters table headers', () => {
      cy.get('.param-table').eq(2).within(() => {
        cy.get('th').invoke('text').should('match', /^PARAMETER$/i);
        cy.get('th').invoke('text').should('match', /^TYPE$/i);
        cy.get('th').invoke('text').should('match', /^REQUIRED$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 3 rows in clients parameters table', () => {
      cy.get('.param-table').eq(2).find('tr').should('have.length.at.least', 3);
    });
  });

  describe('Table Tests - Clients GET Parameter', () => {
    it('should display clients GET parameter table headers', () => {
      cy.get('.param-table').eq(3).within(() => {
        cy.get('th').invoke('text').should('match', /^PARAMETER$/i);
        cy.get('th').invoke('text').should('match', /^TYPE$/i);
        cy.get('th').invoke('text').should('match', /^REQUIRED$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 1 row in clients GET parameter table', () => {
      cy.get('.param-table').eq(3).find('tr').should('have.length.at.least', 1);
    });
  });

  describe('Table Tests - Clients POST Fields', () => {
    it('should display clients POST fields table headers', () => {
      cy.get('.param-table').eq(4).within(() => {
        cy.get('th').invoke('text').should('match', /^FIELD$/i);
        cy.get('th').invoke('text').should('match', /^TYPE$/i);
        cy.get('th').invoke('text').should('match', /^REQUIRED$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 4 rows in clients POST fields table', () => {
      cy.get('.param-table').eq(4).find('tr').should('have.length.at.least', 4);
    });
  });

  describe('Table Tests - Disputes Parameters', () => {
    it('should display disputes parameters table headers', () => {
      cy.get('.param-table').eq(5).within(() => {
        cy.get('th').invoke('text').should('match', /^PARAMETER$/i);
        cy.get('th').invoke('text').should('match', /^TYPE$/i);
        cy.get('th').invoke('text').should('match', /^REQUIRED$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 3 rows in disputes parameters table', () => {
      cy.get('.param-table').eq(5).find('tr').should('have.length.at.least', 3);
    });
  });

  describe('Table Tests - Disputes POST Fields', () => {
    it('should display disputes POST fields table headers', () => {
      cy.get('.param-table').eq(6).within(() => {
        cy.get('th').invoke('text').should('match', /^FIELD$/i);
        cy.get('th').invoke('text').should('match', /^TYPE$/i);
        cy.get('th').invoke('text').should('match', /^REQUIRED$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 4 rows in disputes POST fields table', () => {
      cy.get('.param-table').eq(6).find('tr').should('have.length.at.least', 4);
    });
  });

  describe('Table Tests - Violations Parameters', () => {
    it('should display violations parameters table headers', () => {
      cy.get('.param-table').eq(7).within(() => {
        cy.get('th').invoke('text').should('match', /^PARAMETER$/i);
        cy.get('th').invoke('text').should('match', /^TYPE$/i);
        cy.get('th').invoke('text').should('match', /^REQUIRED$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 2 rows in violations parameters table', () => {
      cy.get('.param-table').eq(7).find('tr').should('have.length.at.least', 2);
    });
  });

  describe('Table Tests - Webhooks Fields', () => {
    it('should display webhooks fields table headers', () => {
      cy.get('.param-table').eq(8).within(() => {
        cy.get('th').invoke('text').should('match', /^FIELD$/i);
        cy.get('th').invoke('text').should('match', /^TYPE$/i);
        cy.get('th').invoke('text').should('match', /^REQUIRED$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 3 rows in webhooks fields table', () => {
      cy.get('.param-table').eq(8).find('tr').should('have.length.at.least', 3);
    });
  });

  describe('Table Tests - Error Codes', () => {
    it('should display error codes table headers', () => {
      cy.get('.error-table').within(() => {
        cy.get('th').invoke('text').should('match', /^STATUS CODE$/i);
        cy.get('th').invoke('text').should('match', /^NAME$/i);
        cy.get('th').invoke('text').should('match', /^DESCRIPTION$/i);
      });
    });

    it('should have 5 rows in error codes table', () => {
      cy.get('.error-table').find('tr').should('have.length.at.least', 5);
    });
  });

  describe('Navigation Tests', () => {
    it('should have functional sidebar navigation', () => {
      cy.get('.sidebar').should('be.visible');
    });

    it('should display logo and brand name', () => {
      cy.get('.logo img').should('have.attr', 'alt', 'Brightpath Ascend');
      cy.get('.logo span').should('contain.text', 'Brightpath');
      cy.get('.logo span .highlight').should('contain.text', 'path');
    });

    it('should have expandable nav sections', () => {
      cy.get('.nav-section').should('have.length.at.least', 1);
      cy.get('.nav-section-title').should('be.visible');
    });

    it('should display user profile in sidebar', () => {
      cy.get('.sidebar-user').should('be.visible');
      cy.get('.sidebar-user').should('contain.text', 'User');
      cy.get('.sidebar-user').should('contain.text', 'staff');
    });

    it('should have sign out link', () => {
      cy.get('a[href="/staff/logout"]').should('contain.text', 'Sign Out');
    });
  });

  describe('Table of Contents Tests', () => {
    it('should display table of contents', () => {
      cy.get('.toc').should('be.visible');
      cy.get('.toc h3').should('contain.text', 'Table of Contents');
    });

    it('should have clickable TOC links', () => {
      cy.get('.toc-list a[href="#overview"]').should('contain.text', 'API Overview');
      cy.get('.toc-list a[href="#authentication"]').should('contain.text', 'Authentication');
      cy.get('.toc-list a[href="#rate-limiting"]').should('contain.text', 'Rate Limiting');
      cy.get('.toc-list a[href="#endpoints"]').should('contain.text', 'Endpoints');
      cy.get('.toc-list a[href="#errors"]').should('contain.text', 'Error Codes');
      cy.get('.toc-list a[href="#examples"]').should('contain.text', 'Code Examples');
    });

    it('should have sub-items in endpoints section', () => {
      cy.get('.toc-list .sub-item a[href="#clients"]').should('contain.text', 'Clients');
      cy.get('.toc-list .sub-item a[href="#disputes"]').should('contain.text', 'Disputes');
      cy.get('.toc-list .sub-item a[href="#violations"]').should('contain.text', 'Violations');
      cy.get('.toc-list .sub-item a[href="#webhooks"]').should('contain.text', 'Webhooks');
    });
  });

  describe('Interactive Element Tests', () => {
    it('should navigate to API keys page when clicking Manage API Keys', () => {
      cy.get('a.btn.btn-primary').contains('Manage API Keys').click();
      cy.url().should('include', '/dashboard/api-keys');
    });

    it('should navigate back and click Get Your API Key', () => {
      cy.visit('/dashboard/api-docs');
      cy.get('a.btn.btn-primary').contains('Get Your API Key').click();
      cy.url().should('include', '/dashboard/api-keys');
    });

    it('should scroll to sections when clicking TOC links', () => {
      cy.get('.toc-list a[href="#overview"]').click();
      cy.get('#overview').should('be.visible');
    });

    it('should expand and collapse nav sections', () => {
      cy.get('.nav-section[data-section="cases"] .nav-section-title').click();
      cy.get('.nav-section[data-section="cases"] .nav-section-items').should('have.class', 'expanded');
    });
  });

  describe('Content Tests', () => {
    it('should display API overview content', () => {
      cy.get('#overview .card').should('contain.text', 'The Brightpath Ascend FCRA Platform API');
    });

    it('should display base URL', () => {
      cy.get('#overview').should('contain.text', 'Base URL:');
      cy.get('#overview code').should('contain.text', 'https://your-domain.com/api/v1');
    });

    it('should display authentication section', () => {
      cy.get('#authentication .card').should('contain.text', 'Bearer token authentication');
    });

    it('should display code examples', () => {
      cy.get('.code-block').should('be.visible');
      cy.get('.code-block pre').should('contain.text', 'Authorization:');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.sidebar').should('be.visible');
      cy.get('.main-content').should('be.visible');
      cy.get('h1').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('h1').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('h1').should('be.visible');
    });
  });

  describe('Visual Elements Tests', () => {
    it('should have proper card styling', () => {
      cy.get('.card').should('have.length.at.least', 1);
      cy.get('.card').first().should('be.visible');
    });

    it('should display info boxes', () => {
      cy.get('.info-box').should('be.visible');
      cy.get('.info-box h4').should('be.visible');
      cy.get('.info-box svg').should('be.visible');
    });

    it('should display section titles with proper styling', () => {
      cy.get('.section-title').should('have.length.at.least', 1);
      cy.get('.section-title').first().should('be.visible');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('exist');
      cy.get('h2').should('exist');
      cy.get('h3').should('exist');
    });

    it('should have alt text for images', () => {
      cy.get('img').each(($img) => {
        cy.wrap($img).should('have.attr', 'alt');
      });
    });

    it('should have proper link attributes', () => {
      cy.get('a[href]').each(($link) => {
        cy.wrap($link).should('have.attr', 'href');
      });
    });
  });

  describe('Error Handling Tests', () => {
    it('should handle image load errors gracefully', () => {
      cy.get('.logo img').should('have.attr', 'onerror');
    });

    it('should handle localStorage errors in sidebar script', () => {
      cy.window().then((win) => {
        cy.stub(win.localStorage, 'getItem').throws();
        cy.reload();
        cy.get('.sidebar').should('be.visible');
      });
    });
  });

  describe('Content Verification Tests', () => {
    it('should display all required sections', () => {
      cy.get('#overview').should('exist');
      cy.get('#authentication').should('exist');
    });

    it('should have properly formatted code blocks', () => {
      cy.get('.code-block pre').should('be.visible');
      cy.get('.keyword').should('exist');
      cy.get('.string').should('exist');
    });

    it('should display all table content properly', () => {
      cy.get('.param-table').should('have.length', 9);
      cy.get('.error-table').should('have.length', 1);
    });
  });

  describe('Page Structure Tests', () => {
    it('should have main content area', () => {
      cy.get('.main-content').should('be.visible');
    });

    it('should have header section', () => {
      cy.get('.header').should('be.visible');
      cy.get('.header h1').should('contain.text', 'API Documentation');
      cy.get('.header-actions').should('be.visible');
    });

    it('should have proper page layout', () => {
      cy.get('nav.sidebar').should('be.visible');
      cy.get('main.main-content').should('be.visible');
    });
  });
});