// Exhaustive test for /admin
describe('FCRA Admin Dashboard - /admin', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/admin');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/admin');
      cy.get('body').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'FCRA Admin Dashboard');
    });

    it('should not return server errors', () => {
      cy.request('/admin').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display main heading', () => {
      cy.get('h1').should('contain.text', 'FCRA Automation Admin');
    });

    it('should display subtitle', () => {
      cy.get('.subtitle').should('contain.text', 'Upload credit report');
    });
  });

  describe('Container Tests', () => {
    it('should display container', () => {
      cy.get('.container').should('be.visible');
    });

    it('should display card', () => {
      cy.get('.card').should('be.visible');
    });
  });

  describe('Form Tests', () => {
    it('should display analysis form', () => {
      cy.get('#analysisForm').should('be.visible');
    });

    it('should have name input', () => {
      cy.get('#name').should('be.visible');
    });

    it('should have email input', () => {
      cy.get('#email').should('be.visible');
    });

    it('should have provider dropdown', () => {
      cy.get('#provider').should('be.visible');
    });

    it('should have report textarea', () => {
      cy.get('#report').should('be.visible');
    });

    it('should have round dropdown', () => {
      cy.get('#round').should('be.visible');
    });

    it('should have mode dropdown', () => {
      cy.get('#mode').should('be.visible');
    });

    it('should have submit button', () => {
      cy.get('#submitBtn').should('be.visible');
    });

    it('should accept input in name field', () => {
      cy.get('#name').type('Test User').should('have.value', 'Test User');
    });

    it('should accept input in email field', () => {
      cy.get('#email').type('test@example.com').should('have.value', 'test@example.com');
    });

    it('should accept input in report textarea', () => {
      cy.get('#report').type('Sample report').should('have.value', 'Sample report');
    });

    it('should have name field as required', () => {
      cy.get('#name').should('have.attr', 'required');
    });
  });

  describe('Input Type Toggle Tests', () => {
    it('should display input type toggle', () => {
      cy.get('.input-type-toggle').should('be.visible');
    });

    it('should have HTML toggle button', () => {
      cy.get('[data-type="html"]').should('be.visible');
    });

    it('should have PDF toggle button', () => {
      cy.get('[data-type="pdf"]').should('be.visible');
    });

    it('should have HTML toggle active by default', () => {
      cy.get('[data-type="html"]').should('have.class', 'active');
    });

    it('should toggle to PDF mode when clicked', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('[data-type="pdf"]').should('have.class', 'active');
      cy.get('[data-type="html"]').should('not.have.class', 'active');
    });

    it('should show HTML section by default', () => {
      cy.get('#htmlInputSection').should('not.have.class', 'hidden');
    });

    it('should show PDF section when toggled', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('#pdfInputSection').should('not.have.class', 'hidden');
      cy.get('#htmlInputSection').should('have.class', 'hidden');
    });
  });

  describe('PDF Upload Section Tests', () => {
    beforeEach(() => {
      cy.get('[data-type="pdf"]').click();
    });

    it('should display PDF drop zone', () => {
      cy.get('#pdfDropZone').should('be.visible');
    });

    it('should have file input for PDF', () => {
      cy.get('#pdfFile').should('exist');
    });

    it('should have file input accept PDF only', () => {
      cy.get('#pdfFile').should('have.attr', 'accept', '.pdf');
    });

    it('should have parse button', () => {
      cy.get('#parseBtn').should('be.visible');
    });

    it('should have PDF file info section', () => {
      cy.get('#pdfFileInfo').should('exist');
    });

    it('should have remove file button', () => {
      cy.get('.remove-file').should('exist');
    });
  });

  describe('Parsed Preview Section Tests', () => {
    it('should have parsed preview section', () => {
      cy.get('#parsedPreview').should('exist');
    });

    it('should have preview bureau section', () => {
      cy.get('#previewBureau').should('exist');
    });

    it('should have preview personal info section', () => {
      cy.get('#previewPersonalInfo').should('exist');
    });

    it('should have preview accounts section', () => {
      cy.get('#previewAccounts').should('exist');
    });

    it('should have preview collections section', () => {
      cy.get('#previewCollections').should('exist');
    });

    it('should have preview inquiries section', () => {
      cy.get('#previewInquiries').should('exist');
    });

    it('should have preview public records section', () => {
      cy.get('#previewPublicRecords').should('exist');
    });

    it('should have confidence bar', () => {
      cy.get('#confidenceBar').should('exist');
    });

    it('should have hidden parsed text field', () => {
      cy.get('#parsedText').should('have.attr', 'type', 'hidden');
    });
  });

  describe('Dropdown Options Tests', () => {
    it('should have provider options', () => {
      cy.get('#provider option').should('have.length', 4);
    });

    it('should have IdentityIQ option', () => {
      cy.get('#provider option').contains('IdentityIQ').should('exist');
    });

    it('should have round options', () => {
      cy.get('#round option').should('have.length', 4);
    });

    it('should have Round 1 option', () => {
      cy.get('#round option').contains('Round 1').should('exist');
    });

    it('should have mode options', () => {
      cy.get('#mode option').should('have.length', 2);
    });

    it('should have Manual Review option', () => {
      cy.get('#mode option').contains('Manual Review').should('exist');
    });

    it('should allow selection of provider', () => {
      cy.get('#provider').select('MyScoreIQ.com');
      cy.get('#provider').should('have.value', 'MyScoreIQ.com');
    });

    it('should allow selection of round', () => {
      cy.get('#round').select('2');
      cy.get('#round').should('have.value', '2');
    });

    it('should allow selection of mode', () => {
      cy.get('#mode').select('auto');
      cy.get('#mode').should('have.value', 'auto');
    });
  });

  describe('Button Tests', () => {
    it('should have primary button styling on submit', () => {
      cy.get('#submitBtn').should('have.class', 'btn-primary');
    });

    it('should have submit type on submit button', () => {
      cy.get('#submitBtn').should('have.attr', 'type', 'submit');
    });

    it('should have secondary button styling on parse', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('#parseBtn').should('have.class', 'btn-secondary');
    });

    it('should have button type on parse button', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('#parseBtn').should('have.attr', 'type', 'button');
    });
  });

  describe('Status Section Tests', () => {
    it('should have status div', () => {
      cy.get('#status').should('exist');
    });
  });

  describe('Form Validation Tests', () => {
    it('should validate required name field', () => {
      cy.get('#name').clear();
      cy.get('#submitBtn').click();
      cy.get('#name:invalid').should('exist');
    });

    it('should validate email format', () => {
      cy.get('#name').type('Test User');
      cy.get('#email').type('invalid-email');
      cy.get('#submitBtn').click();
      cy.get('#email:invalid').should('exist');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.container').should('be.visible');
      cy.get('.card').should('be.visible');
      cy.get('#analysisForm').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.container').should('be.visible');
      cy.get('.card').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.container').should('be.visible');
      cy.get('h1').should('be.visible');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
    });

    it('should have labels for form fields', () => {
      cy.get('label[for="name"]').should('exist');
      cy.get('label[for="email"]').should('exist');
      cy.get('label[for="provider"]').should('exist');
      cy.get('label[for="round"]').should('exist');
      cy.get('label[for="mode"]').should('exist');
    });

    it('should have label for report field', () => {
      cy.get('label[for="report"]').should('exist');
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have setInputType function', () => {
      cy.window().should('have.property', 'setInputType');
    });

    it('should have parsePdf function', () => {
      cy.window().should('have.property', 'parsePdf');
    });

    it('should have removePdfFile function', () => {
      cy.window().should('have.property', 'removePdfFile');
    });
  });
});
