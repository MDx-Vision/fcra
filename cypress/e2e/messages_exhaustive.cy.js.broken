// Exhaustive test for /portal/messages
describe('Client Portal - Messages Page', () => {
  
  beforeEach(() => {
    cy.visit('/portal/login');
    cy.get('input[name="email"]').type('client@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/portal');
    cy.visit('/portal/messages');
  });

  describe('Page Load Tests', () => {
    it('should load without errors', () => {
      cy.url().should('eq', 'http://localhost:5001/portal/messages');
      cy.get('body').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('eq', 'Client Portal - Brightpath Ascend');
    });

    it('should not have console errors', () => {
      cy.window().then((win) => {
        cy.stub(win.console, 'error');
        cy.reload();
        cy.window().its('console.error').should('not.have.been.called');
      });
    });

    it('should not have server errors', () => {
      cy.request('GET', '/portal/messages').its('status').should('eq', 200);
    });
  });

  describe('Header Tests', () => {
    it('should display logo and company name', () => {
      cy.get('.logo img').should('exist');
      cy.get('.logo span').should('contain', 'Brightpath Ascend');
    });

    it('should display portal title', () => {
      cy.get('.portal-title').should('contain', 'Client Portal');
    });

    it('should display user profile section', () => {
      cy.get('.user-profile').should('be.visible');
      cy.get('#headerAvatar').should('be.visible');
      cy.get('.greeting').should('contain', 'Hello, Client');
      cy.get('.date-display').should('contain', 'As of: 12/11/2025');
    });

    it('should have logout link', () => {
      cy.get('a[href="/portal/logout"]').should('be.visible').should('contain', 'Logout');
    });
  });

  describe('Navigation Tabs Tests', () => {
    const tabs = [
      { name: 'Summary', active: true },
      { name: 'Score Progress', active: false },
      { name: 'Dispute Timeline', active: false },
      { name: 'Status', active: false },
      { name: 'Attachments', active: false },
      { name: 'Upload Documents', active: false },
      { name: 'My Profile', active: false },
      { name: 'Contact Us', active: false },
      { name: 'Refer a Friend', active: false }
    ];

    tabs.forEach((tab) => {
      it(`should display ${tab.name} tab`, () => {
        cy.get('.nav-tab').contains(tab.name).should('be.visible');
        if (tab.active) {
          cy.get('.nav-tab').contains(tab.name).should('have.class', 'active');
        }
      });

      it(`should switch to ${tab.name} tab when clicked`, () => {
        cy.get('.nav-tab').contains(tab.name).click();
        cy.get('.nav-tab').contains(tab.name).should('have.class', 'active');
      });
    });
  });

  describe('Summary Tab Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('Summary').click();
    });

    it('should display welcome banner', () => {
      cy.get('.status-banner').should('be.visible');
      cy.get('h2').should('contain', 'Welcome to Your Portal');
      cy.get('.status-banner p').should('contain', "We're getting started on your case");
    });

    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
      cy.get('.stat-box').should('have.length', 4);
      
      cy.get('.stat-box').eq(0).find('.stat-label').should('contain', 'Violations Found');
      cy.get('.stat-box').eq(0).find('.stat-value').should('contain', '0');
      
      cy.get('.stat-box').eq(1).find('.stat-label').should('contain', 'Case Strength');
      cy.get('.stat-box').eq(1).find('.stat-value').should('contain', '-/10');
      
      cy.get('.stat-box').eq(2).find('.stat-label').should('contain', 'Dispute Round');
      cy.get('.stat-box').eq(2).find('.stat-value').should('contain', '1');
      
      cy.get('.stat-box').eq(3).find('.stat-label').should('contain', 'Potential Recovery');
      cy.get('.stat-box').eq(3).find('.stat-value').should('contain', '$0');
    });

    it('should display ROI dashboard', () => {
      cy.get('#roiDashboard').should('be.visible');
      cy.get('.card-title').contains('Your Case Value Analysis').should('be.visible');
    });
  });

  describe('Score Progress Tab Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('Score Progress').click();
    });

    it('should display score progress content', () => {
      cy.get('#scoreProgressContent').should('be.visible');
      cy.get('.card-title').contains('Your Credit Score Journey').should('be.visible');
    });

    it('should display score timeline chart', () => {
      cy.get('#clientScoreChart').should('exist');
      cy.get('.card-title').contains('Score Timeline').should('be.visible');
    });

    it('should display projected improvement', () => {
      cy.get('#projectionContent').should('be.visible');
      cy.get('.card-title').contains('Projected Improvement').should('be.visible');
    });
  });

  describe('Dispute Timeline Tab Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('Dispute Timeline').click();
    });

    it('should display timeline summary cards', () => {
      cy.get('#timelineSummary').should('be.visible');
      cy.get('#lettersSentCount').should('be.visible');
      cy.get('#responsesCount').should('be.visible');
      cy.get('#deletedCount').should('be.visible');
      cy.get('#overdueCount').should('be.visible');
    });

    it('should display timeline container', () => {
      cy.get('#timelineContainer').should('be.visible');
    });

    it('should display timeline legend', () => {
      cy.get('.card-title').contains('Timeline').should('be.visible');
    });
  });

  describe('Status Tab Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('Status').click();
    });

    it('should display status controls', () => {
      cy.get('.submit-btn').contains('Show all').should('be.visible');
      cy.get('.submit-btn').contains('Submit changes').should('be.visible');
    });

    it('should display Equifax table', () => {
      cy.get('.bureau-section').contains('EQUIFAX').should('be.visible');
      cy.get('.status-table').eq(0).should('be.visible');
      
      const equifaxHeaders = ['Follow up', 'Type', 'R', 'Creditor', 'Account ID', 'Status', 'Reason', 'Comments'];
      equifaxHeaders.forEach((header) => {
        cy.get('.status-table').eq(0).find('th').should('contain', header);
      });
    });

    it('should display Experian table', () => {
      cy.get('.bureau-section').contains('Experian').should('be.visible');
      cy.get('.status-table').eq(1).should('be.visible');
      
      const experianHeaders = ['Follow up', 'Type', 'R', 'Creditor', 'Account ID', 'Status', 'Reason', 'Comments'];
      experianHeaders.forEach((header) => {
        cy.get('.status-table').eq(1).find('th').should('contain', header);
      });
    });

    it('should show empty state for tables', () => {
      cy.get('.status-table').eq(0).should('contain', 'No items tracked yet for Equifax');
      cy.get('.status-table').eq(1).should('contain', 'No items tracked yet for Experian');
    });
  });

  describe('Upload Documents Tab Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('Upload Documents').click();
    });

    it('should display document category buttons', () => {
      cy.get('.doc-category-btn').should('have.length', 6);
      cy.get('.doc-category-btn').contains('CRA Response').should('be.visible');
      cy.get('.doc-category-btn').contains('Collection Letter').should('be.visible');
      cy.get('.doc-category-btn').contains('Legal/Lawsuit').should('be.visible');
      cy.get('.doc-category-btn').contains('Credit Report').should('be.visible');
      cy.get('.doc-category-btn').contains('ID/Proof').should('be.visible');
      cy.get('.doc-category-btn').contains('Other').should('be.visible');
    });

    it('should have upload form', () => {
      cy.get('#docUploadForm').should('exist');
      cy.get('#docFileInput').should('exist');
      cy.get('input[type="date"]').should('have.length', 2);
      cy.get('textarea[name="notes"]').should('exist');
    });

    it('should have back buttons', () => {
      cy.get('button').contains('← Back').should('have.length.at.least', 1);
    });

    it('should have upload document button', () => {
      cy.get('button').contains('Upload Document').should('be.visible');
    });
  });

  describe('My Profile Tab Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('My Profile').click();
    });

    it('should have avatar upload controls', () => {
      cy.get('.btn-upload').contains('Upload Photo').should('be.visible');
      cy.get('#removeAvatarBtn').should('be.visible');
    });

    it('should have set password button', () => {
      cy.get('button').contains('Set Password').should('be.visible');
    });
  });

  describe('Contact Us Tab Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('Contact Us').click();
    });

    it('should display contact form', () => {
      cy.get('#contactForm').should('exist');
    });

    it('should have required text input', () => {
      cy.get('#contactForm input[type="text"]').should('exist');
      cy.get('#contactForm input[type="text"]').should('have.attr', 'required');
      cy.get('#contactForm input[type="text"]').should('have.attr', 'placeholder', 'How can we help you?');
    });

    it('should have required textarea', () => {
      cy.get('#contactForm textarea').should('exist');
      cy.get('#contactForm textarea').should('have.attr', 'required');
      cy.get('#contactForm textarea').should('have.attr', 'placeholder', 'Type your message here...');
    });

    it('should have send message button', () => {
      cy.get('.submit-btn').contains('Send Message').should('be.visible');
    });
  });

  describe('Refer a Friend Tab Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('Refer a Friend').click();
    });

    it('should display referral form', () => {
      cy.get('#referralForm').should('exist');
    });

    it('should have required name field', () => {
      cy.get('#refName').should('exist');
      cy.get('#refName').should('have.attr', 'required');
      cy.get('#refName').should('have.attr', 'placeholder', "Friend's full name");
    });

    it('should have phone field', () => {
      cy.get('#refPhone').should('exist');
      cy.get('#refPhone').should('have.attr', 'type', 'tel');
      cy.get('#refPhone').should('have.attr', 'placeholder', '(xxx) xxx-xxxx');
    });

    it('should have required email field', () => {
      cy.get('#refEmail').should('exist');
      cy.get('#refEmail').should('have.attr', 'required');
      cy.get('#refEmail').should('have.attr', 'placeholder', 'friend@email.com');
    });

    it('should have comments textarea', () => {
      cy.get('#refComments').should('exist');
      cy.get('#refComments').should('have.attr', 'placeholder', 'Any additional information about your referral...');
    });

    it('should have submit referral button', () => {
      cy.get('.submit-btn').contains('Submit Referral').should('be.visible');
    });
  });

  describe('Form Validation Tests', () => {
    it('should validate contact form required fields', () => {
      cy.get('.nav-tab').contains('Contact Us').click();
      cy.get('.submit-btn').contains('Send Message').click();
      
      cy.get('#contactForm input[type="text"]:invalid').should('exist');
      cy.get('#contactForm textarea:invalid').should('exist');
    });

    it('should validate referral form required fields', () => {
      cy.get('.nav-tab').contains('Refer a Friend').click();
      cy.get('.submit-btn').contains('Submit Referral').click();
      
      cy.get('#refName:invalid').should('exist');
      cy.get('#refEmail:invalid').should('exist');
    });

    it('should accept valid contact form input', () => {
      cy.get('.nav-tab').contains('Contact Us').click();
      
      cy.get('#contactForm input[type="text"]').type('I need help with my account');
      cy.get('#contactForm textarea').type('Please provide more information about my case status');
      
      cy.get('#contactForm input[type="text"]').should('have.value', 'I need help with my account');
      cy.get('#contactForm textarea').should('have.value', 'Please provide more information about my case status');
    });

    it('should accept valid referral form input', () => {
      cy.get('.nav-tab').contains('Refer a Friend').click();
      
      cy.get('#refName').type('John Doe');
      cy.get('#refPhone').type('(555) 123-4567');
      cy.get('#refEmail').type('john.doe@example.com');
      cy.get('#refComments').type('My friend is interested in your services');
      
      cy.get('#refName').should('have.value', 'John Doe');
      cy.get('#refPhone').should('have.value', '(555) 123-4567');
      cy.get('#refEmail').should('have.value', 'john.doe@example.com');
      cy.get('#refComments').should('have.value', 'My friend is interested in your services');
    });
  });

  describe('Document Upload Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('Upload Documents').click();
    });

    it('should allow file selection', () => {
      const fileName = 'test-document.pdf';
      cy.get('#docFileInput').selectFile({
        contents: Cypress.Buffer.from('file contents'),
        fileName: fileName,
        mimeType: 'application/pdf'
      });
    });

    it('should accept date inputs', () => {
      cy.get('input[name="document_date"]').type('2024-01-15');
      cy.get('input[name="received_date"]').type('2024-01-20');
      
      cy.get('input[name="document_date"]').should('have.value', '2024-01-15');
      cy.get('input[name="received_date"]').should('have.value', '2024-01-20');
    });

    it('should accept notes input', () => {
      cy.get('textarea[name="notes"]').type('Important document for case review');
      cy.get('textarea[name="notes"]').should('have.value', 'Important document for case review');
    });
  });

  describe('Button Interaction Tests', () => {
    it('should make all submit buttons clickable', () => {
      const buttons = [
        { tab: 'Status', text: 'Show all' },
        { tab: 'Status', text: 'Submit changes' },
        { tab: 'My Profile', text: 'Upload Photo' },
        { tab: 'My Profile', text: 'Remove' },
        { tab: 'My Profile', text: 'Set Password' },
        { tab: 'Contact Us', text: 'Send Message' },
        { tab: 'Upload Documents', text: 'Upload Document' },
        { tab: 'Refer a Friend', text: 'Submit Referral' }
      ];

      buttons.forEach((btn) => {
        cy.get('.nav-tab').contains(btn.tab).click();
        cy.get('button').contains(btn.text).should('be.visible').should('not.be.disabled');
      });
    });

    it('should make document category buttons clickable', () => {
      cy.get('.nav-tab').contains('Upload Documents').click();
      
      const categories = ['CRA Response', 'Collection Letter', 'Legal/Lawsuit', 'Credit Report', 'ID/Proof', 'Other'];
      categories.forEach((category) => {
        cy.get('.doc-category-btn').contains(category).should('be.visible').should('not.be.disabled');
      });
    });
  });

  describe('Responsive Design Tests', () => {
    const viewports = [
      { width: 1280, height: 720, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];

    viewports.forEach((viewport) => {
      it(`should display correctly on ${viewport.name}`, () => {
        cy.viewport(viewport.width, viewport.height);
        
        cy.get('.header').should('be.visible');
        cy.get('.nav-tabs').should('be.visible');
        cy.get('.container').should('be.visible');
        
        cy.get('.nav-tab').contains('Summary').click();
        cy.get('#summary').should('be.visible');
        
        cy.get('.nav-tab').contains('Contact Us').click();
        cy.get('#contactForm').should('be.visible');
      });
    });
  });

  describe('Error Handling Tests', () => {
    it('should handle network errors gracefully', () => {
      cy.intercept('POST', '/portal/messages', { statusCode: 500 }).as('serverError');
      
      cy.get('.nav-tab').contains('Contact Us').click();
      cy.get('#contactForm input[type="text"]').type('Test message');
      cy.get('#contactForm textarea').type('Test content');
      cy.get('.submit-btn').contains('Send Message').click();
      
      cy.wait('@serverError');
    });

    it('should handle form submission errors', () => {
      cy.intercept('POST', '/portal/messages', { statusCode: 400, body: { error: 'Invalid input' } }).as('validationError');
      
      cy.get('.nav-tab').contains('Contact Us').click();
      cy.get('#contactForm input[type="text"]').type('Test');
      cy.get('#contactForm textarea').type('Test');
      cy.get('.submit-btn').contains('Send Message').click();
      
      cy.wait('@validationError');
    });
  });

  describe('User Profile Interaction Tests', () => {
    it('should allow clicking on user profile', () => {
      cy.get('.user-profile').click();
      cy.get('.nav-tab').contains('My Profile').should('have.class', 'active');
    });

    it('should display current date in header', () => {
      cy.get('.date-display').should('contain', '12/11/2025');
    });
  });

  describe('Table Functionality Tests', () => {
    beforeEach(() => {
      cy.get('.nav-tab').contains('Status').click();
    });

    it('should display all table headers correctly', () => {
      cy.get('.status-table').each(($table) => {
        cy.wrap($table).find('thead th').should('have.length.at.least', 6);
      });
    });

    it('should show empty states for tables', () => {
      cy.get('.status-table').should('contain', 'No items tracked');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper ARIA labels and roles', () => {
      cy.get('.nav-tabs').should('have.attr', 'role', 'navigation');
    });

    it('should be keyboard navigable', () => {
      cy.get('.nav-tab').first().focus();
      cy.focused().should('have.class', 'nav-tab');
    });

    it('should have proper form labels and structure', () => {
      cy.get('.nav-tab').contains('Contact Us').click();
      cy.get('#contactForm input').should('have.attr', 'placeholder');
      cy.get('#contactForm textarea').should('have.attr', 'placeholder');
    });
  });
});