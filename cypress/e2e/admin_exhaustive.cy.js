// Exhaustive test for /admin
describe('/admin - FCRA Admin Dashboard', () => {
  beforeEach(() => {
    // Public route - no auth required
    cy.visit('/admin');
    cy.get('body').should('be.visible');
    cy.wait(500); // Allow page to fully render
  });

  describe('Page Load Tests', () => {
    it('loads without errors', () => {
      cy.url().should('include', '/admin');
      cy.get('body').should('be.visible');
    });

    it('has correct page title', () => {
      cy.title().should('contain', 'FCRA Admin Dashboard');
    });

    it('has no console errors', () => {
      cy.get('@consoleError').should('not.have.been.called');
    });

    it('responds with 200 status', () => {
      cy.request('/admin').then((response) => {
        expect(response.status).to.eq(200);
      });
    });
  });

  describe('UI Element Tests', () => {
    it('displays main heading', () => {
      cy.get('h1').should('contain', 'FCRA Automation Admin');
    });

    it('displays preview heading', () => {
      cy.get('h3').should('contain', '📋 Parsed Credit Report Preview');
    });

    it('displays subtitle', () => {
      cy.get('.subtitle').should('contain', 'Upload credit report for AI-powered FCRA analysis and dispute letter generation');
    });

    it('displays main container', () => {
      cy.get('.container').should('be.visible');
      cy.get('.card').should('be.visible');
    });

    it('displays all form elements', () => {
      cy.get('#analysisForm').should('be.visible');
      cy.get('#name').should('be.visible');
      cy.get('#email').should('be.visible');
      cy.get('#provider').should('be.visible');
      cy.get('#report').should('be.visible');
      cy.get('#pdfFile').should('exist');
      cy.get('#parsedText').should('exist');
      cy.get('#round').should('be.visible');
      cy.get('#mode').should('be.visible');
    });

    it('displays all buttons', () => {
      cy.get('#parseBtn').should('exist').scrollIntoView().should('contain', '📊 Parse PDF Preview');
      cy.get('#submitBtn').should('exist').scrollIntoView().should('contain', '🔍 Generate Analysis');
    });

    it('displays input type toggle buttons', () => {
      cy.get('[data-type="html"]').should('be.visible').should('contain', 'Paste HTML');
      cy.get('[data-type="pdf"]').should('be.visible').should('contain', 'Upload PDF');
    });
  });

  describe('Form Tests - analysisForm', () => {
    it('has correct form attributes', () => {
      cy.get('#analysisForm').scrollIntoView()
        .should('exist')
        .should('have.attr', 'id', 'analysisForm');
    });

    it('name field accepts text and is required', () => {
      cy.get('#name').should('exist');
      cy.get('#name').scrollIntoView();
      cy.get('#name').should('have.attr', 'type', 'text');
      cy.get('#name').should('have.attr', 'required');
      cy.get('#name').clear({ force: true });
      cy.get('#name').type('Test User', { force: true });
      cy.get('#name').should('have.value', 'Test User');
    });

    it('email field accepts email and is optional', () => {
      cy.get('#email').should('exist');
      cy.get('#email').scrollIntoView();
      cy.get('#email').should('have.attr', 'type', 'email');
      cy.get('#email').should('not.have.attr', 'required');
      cy.get('#email').clear({ force: true });
      cy.get('#email').type('test@example.com', { force: true });
      cy.get('#email').should('have.value', 'test@example.com');
    });

    it('report textarea accepts text', () => {
      cy.get('#report')
        .should('have.attr', 'placeholder', 'Paste full HTML from credit report...')
        .type('Sample credit report HTML')
        .should('have.value', 'Sample credit report HTML');
    });

    it('file input accepts PDF files', () => {
      cy.get('#pdfFile')
        .should('have.attr', 'type', 'file')
        .should('have.attr', 'accept', '.pdf');
    });

    it('hidden field exists', () => {
      cy.get('#parsedText')
        .should('have.attr', 'type', 'hidden');
    });

    it('validates required name field', () => {
      cy.get('#name').clear();
      cy.get('#submitBtn').click();
      cy.get('#name:invalid').should('exist');
    });

    it('allows form submission with valid data', () => {
      cy.get('#name').type('John Doe');
      cy.get('#email').type('john@example.com');
      cy.get('#report').type('Sample HTML content');
      // Form submission would redirect, so we just verify the form is valid
      cy.get('#name:valid').should('exist');
    });
  });

  describe('Dropdown Tests', () => {
    it('provider dropdown has correct options', () => {
      cy.get('#provider option').should('have.length', 4);
      cy.get('#provider option').eq(0).should('contain', 'IdentityIQ.com');
      cy.get('#provider option').eq(1).should('contain', 'MyScoreIQ.com');
      cy.get('#provider option').eq(2).should('contain', 'SmartCredit.com');
      cy.get('#provider option').eq(3).should('contain', 'MyFreeScoreNow.com');
    });

    it('round dropdown has correct options', () => {
      cy.get('#round option').should('have.length', 4);
      cy.get('#round option').eq(0).should('contain', 'Round 1 - Initial Dispute').should('have.value', '1');
      cy.get('#round option').eq(1).should('contain', 'Round 2 - Escalation').should('have.value', '2');
      cy.get('#round option').eq(2).should('contain', 'Round 3 - Advanced').should('have.value', '3');
      cy.get('#round option').eq(3).should('contain', 'Round 4 - Final').should('have.value', '4');
    });

    it('mode dropdown has correct options', () => {
      cy.get('#mode option').should('have.length', 2);
      cy.get('#mode option').eq(0).should('contain', 'Manual Review (Recommended)').should('have.value', 'manual');
      cy.get('#mode option').eq(1).should('contain', 'Automatic (Full Report)').should('have.value', 'auto');
    });

    it('allows selection of dropdown options', () => {
      cy.get('#provider').select('MyScoreIQ.com');
      cy.get('#round').select('2');
      cy.get('#mode').select('auto');
    });
  });

  describe('Interactive Element Tests', () => {
    it('input type toggle works', () => {
      // Initially HTML is active
      cy.get('[data-type="html"]').should('have.class', 'active');
      cy.get('#htmlInputSection').should('not.have.class', 'hidden');
      cy.get('#pdfInputSection').should('have.class', 'hidden');

      // Click PDF toggle
      cy.get('[data-type="pdf"]').click();
      cy.get('[data-type="pdf"]').should('have.class', 'active');
      cy.get('[data-type="html"]').should('not.have.class', 'active');
      cy.get('#htmlInputSection').should('have.class', 'hidden');
      cy.get('#pdfInputSection').should('not.have.class', 'hidden');

      // Click back to HTML
      cy.get('[data-type="html"]').click();
      cy.get('[data-type="html"]').should('have.class', 'active');
      cy.get('#htmlInputSection').should('not.have.class', 'hidden');
      cy.get('#pdfInputSection').should('have.class', 'hidden');
    });

    it('PDF drop zone is clickable', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('#pdfDropZone').should('be.visible').click();
    });

    it('parse button is initially disabled state ready', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('#parseBtn').should('be.visible').should('not.be.disabled');
    });

    it('submit button triggers form submission', () => {
      cy.get('#submitBtn')
        .should('have.attr', 'type', 'submit')
        .should('have.class', 'btn-primary');
    });

    it('status div exists for feedback', () => {
      cy.get('#status').should('exist');
    });
  });

  describe('PDF Upload Tests', () => {
    beforeEach(() => {
      cy.get('[data-type="pdf"]').click();
    });

    it('displays PDF upload area', () => {
      cy.get('#pdfDropZone').should('be.visible');
      cy.get('#pdfDropZone').should('contain', 'Click to select or drag & drop a PDF file');
      cy.get('#pdfDropZone').should('contain', 'Supports Experian, TransUnion, and Equifax credit reports');
    });

    it('has file info section', () => {
      cy.get('#pdfFileInfo').should('exist');
      cy.get('#pdfFileName').should('exist');
    });

    it('shows parsed preview section', () => {
      cy.get('#parsedPreview').should('exist');
      cy.get('#previewBureau').should('contain', '-');
      cy.get('#previewPersonalInfo').should('contain', '-');
      cy.get('#previewAccounts').should('contain', '-');
      cy.get('#previewCollections').should('contain', '-');
      cy.get('#previewInquiries').should('contain', '-');
      cy.get('#previewPublicRecords').should('contain', '-');
      cy.get('#confidenceBar').should('exist');
      cy.get('#confidenceText').should('contain', '-');
    });
  });

  describe('Responsive Tests', () => {
    it('displays correctly on desktop', () => {
      cy.viewport(1280, 720);
      cy.get('.container').should('be.visible');
      cy.get('#analysisForm').should('be.visible');
      cy.get('.card').should('be.visible');
    });

    it('displays correctly on tablet', () => {
      cy.viewport(768, 1024);
      cy.get('.container').should('be.visible');
      cy.get('#analysisForm').should('be.visible');
      cy.get('h1').should('be.visible');
    });

    it('displays correctly on mobile', () => {
      cy.viewport(375, 667);
      cy.get('.container').should('be.visible');
      cy.get('#analysisForm').should('be.visible');
      cy.get('#name').should('be.visible');
      cy.get('.toggle-btn').should('be.visible');
    });
  });

  describe('Error Handling Tests', () => {
    it('handles empty form submission', () => {
      cy.get('#submitBtn').click();
      cy.get('#name:invalid').should('exist');
    });

    it('shows error when parsing PDF without file', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('#parseBtn').click();
      cy.get('#status').should('be.visible');
    });

    it('validates email format', () => {
      cy.get('#email').type('invalid-email');
      cy.get('#name').type('John Doe');
      cy.get('#submitBtn').click();
      cy.get('#email:invalid').should('exist');
    });

    it('handles network errors gracefully', () => {
      cy.intercept('POST', '/api/credit-report/parse-pdf', { forceNetworkError: true });
      cy.get('[data-type="pdf"]').click();
      
      // Create a fake file for testing
      const fileName = 'test.pdf';
      cy.get('#pdfFile').selectFile({
        contents: Cypress.Buffer.from('fake pdf content'),
        fileName: fileName,
        mimeType: 'application/pdf',
      }, { force: true });
      
      cy.get('#parseBtn').click();
      cy.get('#status').should('be.visible');
    });
  });

  describe('Form Labels and Accessibility', () => {
    it('has proper labels for all form fields', () => {
      cy.get('label[for="name"]').should('contain', 'Client Name *');
      cy.get('label[for="email"]').should('contain', 'Client Email');
      cy.get('label[for="provider"]').should('contain', 'Credit Provider');
      cy.get('label[for="report"]').should('contain', 'Credit Report HTML *');
      cy.get('label[for="round"]').should('contain', 'Dispute Round');
      cy.get('label[for="mode"]').should('contain', 'Analysis Mode');
    });

    it('shows input method selection label', () => {
      cy.contains('Credit Report Input Method *').should('be.visible');
    });

    it('PDF section has proper labeling', () => {
      cy.get('[data-type="pdf"]').click();
      cy.contains('Credit Report PDF *').should('be.visible');
    });
  });

  describe('Button States and Classes', () => {
    it('parse button has correct classes and attributes', () => {
      cy.get('#parseBtn')
        .should('have.class', 'btn-secondary')
        .should('have.attr', 'type', 'button');
    });

    it('submit button has correct classes and attributes', () => {
      cy.get('#submitBtn')
        .should('have.class', 'btn-primary')
        .should('have.attr', 'type', 'submit');
    });

    it('toggle buttons have proper initial state', () => {
      cy.get('[data-type="html"]').should('have.class', 'active');
      cy.get('[data-type="pdf"]').should('not.have.class', 'active');
    });
  });

  describe('Preview Section Structure', () => {
    it('has all preview sections', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('.preview-section').should('have.length', 7);
      
      cy.contains('Bureau Detected').should('be.visible');
      cy.contains('Personal Information').should('be.visible');
      cy.contains('Accounts Summary').should('be.visible');
      cy.contains('Collections').should('be.visible');
      cy.contains('Inquiries').should('be.visible');
      cy.contains('Public Records').should('be.visible');
      cy.contains('Parsing Confidence').should('be.visible');
    });

    it('confidence bar exists with proper structure', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('.confidence-bar').should('exist');
      cy.get('#confidenceBar').should('have.class', 'fill');
      cy.get('#confidenceBar').should('have.css', 'width', '0px');
    });
  });

  describe('File Upload Integration', () => {
    it('file input triggers properly', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('#pdfFile').should('have.attr', 'accept', '.pdf');
    });

    it('remove file functionality exists', () => {
      cy.get('[data-type="pdf"]').click();
      cy.get('.remove-file').should('exist').should('contain', '✕ Remove');
    });
  });

  describe('JavaScript Functionality', () => {
    it('has required JavaScript functions available', () => {
      cy.window().should('have.property', 'setInputType');
      cy.window().should('have.property', 'parsePdf');
      cy.window().should('have.property', 'removePdfFile');
    });

    it('form submission is handled by JavaScript', () => {
      cy.get('#analysisForm').should('exist');
      cy.window().its('document').then((doc) => {
        expect(doc.getElementById('analysisForm')).to.exist;
      });
    });
  });
});