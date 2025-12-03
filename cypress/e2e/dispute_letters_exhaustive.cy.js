/// <reference types="cypress" />

describe('DISPUTE_LETTERS - Letter Generation & CRUD Operations', () => {
  beforeEach(() => {
    // Clear session and login as admin
    cy.clearCookies()
    cy.clearLocalStorage()
    cy.visit('/staff/login')
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('testpass123')
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
    
    // Navigate to dispute letters section
    cy.visit('/dashboard/dispute-letters')
    cy.wait(1000)
  })

  describe('Happy Path Tests - Letter Generation', () => {
    it('should successfully generate initial dispute letter for new case', () => {
      cy.get('[data-cy="generate-letter-btn"]').click()
      cy.get('[data-cy="letter-type-select"]').select('initial_dispute')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('experian')
      cy.get('[data-cy="template-select"]').select('fcra_standard')
      cy.get('[data-cy="generate-submit"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="success-message"]').should('contain', 'Letter generated successfully')
      cy.url().should('include', '/dashboard/dispute-letters')
      cy.get('[data-cy="letters-table"]').should('contain', 'initial_dispute')
    })

    it('should generate MOV request letter for round 2 dispute', () => {
      cy.get('[data-cy="generate-letter-btn"]').click()
      cy.get('[data-cy="letter-type-select"]').select('mov_request')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('transunion')
      cy.get('[data-cy="template-select"]').select('mov_standard')
      cy.get('[data-cy="custom-content"]').type('This is a Method of Verification request under FCRA Section 611(a)(3)(A).')
      cy.get('[data-cy="generate-submit"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="letters-table"]').should('contain', 'mov_request')
      cy.get('[data-cy="letters-table"]').should('contain', 'transunion')
    })

    it('should generate pre-litigation warning letter', () => {
      cy.get('[data-cy="generate-letter-btn"]').click()
      cy.get('[data-cy="letter-type-select"]').select('pre_litigation')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('equifax')
      cy.get('[data-cy="template-select"]').select('pre_litigation_warning')
      cy.get('[data-cy="custom-content"]').type('Failure to comply will result in legal action under FCRA Section 616.')
      cy.get('[data-cy="generate-submit"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="letters-table"]').should('contain', 'pre_litigation')
      cy.get('[data-cy="letters-table"]').should('contain', 'equifax')
      cy.get('[data-cy="letter-status"]').should('contain', 'draft')
    })

    it('should generate final demand letter with litigation threat', () => {
      cy.get('[data-cy="generate-letter-btn"]').click()
      cy.get('[data-cy="letter-type-select"]').select('final_demand')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('all_bureaus')
      cy.get('[data-cy="template-select"]').select('final_demand_litigation')
      cy.get('[data-cy="damages-amount"]').type('5000')
      cy.get('[data-cy="deadline-date"]').type('2024-12-31')
      cy.get('[data-cy="generate-submit"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="letters-table"]').should('contain', 'final_demand')
      cy.get('[data-cy="letters-table"]').should('contain', '$5,000')
    })

    it('should generate furnisher dispute letter', () => {
      cy.get('[data-cy="generate-letter-btn"]').click()
      cy.get('[data-cy="letter-type-select"]').select('furnisher_dispute')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('furnisher')
      cy.get('[data-cy="furnisher-name"]').type('Capital One Bank')
      cy.get('[data-cy="account-number"]').type('****1234')
      cy.get('[data-cy="template-select"]').select('furnisher_standard')
      cy.get('[data-cy="generate-submit"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="letters-table"]').should('contain', 'furnisher_dispute')
      cy.get('[data-cy="letters-table"]').should('contain', 'Capital One Bank')
    })

    it('should preview letter before generating', () => {
      cy.get('[data-cy="generate-letter-btn"]').click()
      cy.get('[data-cy="letter-type-select"]').select('initial_dispute')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('experian')
      cy.get('[data-cy="template-select"]').select('fcra_standard')
      cy.get('[data-cy="preview-btn"]').click()
      
      cy.get('[data-cy="preview-modal"]').should('be.visible')
      cy.get('[data-cy="preview-content"]').should('contain', 'Dear Experian')
      cy.get('[data-cy="preview-content"]').should('contain', 'Fair Credit Reporting Act')
      cy.get('[data-cy="confirm-generate"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
    })

    it('should generate letter with custom template variables', () => {
      cy.get('[data-cy="generate-letter-btn"]').click()
      cy.get('[data-cy="letter-type-select"]').select('custom')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('experian')
      cy.get('[data-cy="custom-variables"]').click()
      cy.get('[data-cy="variable-client-name"]').type('John Q. Public')
      cy.get('[data-cy="variable-account-number"]').type('123-456-789')
      cy.get('[data-cy="variable-dispute-reason"]').type('Account not mine')
      cy.get('[data-cy="generate-submit"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="letters-table"]').should('contain', 'John Q. Public')
    })

    it('should bulk generate letters for multiple bureaus', () => {
      cy.get('[data-cy="bulk-generate-btn"]').click()
      cy.get('[data-cy="bulk-case-select"]').select('1')
      cy.get('[data-cy="bulk-letter-type"]').select('initial_dispute')
      cy.get('[data-cy="bulk-recipients"]').check(['experian', 'transunion', 'equifax'])
      cy.get('[data-cy="bulk-template"]').select('fcra_standard')
      cy.get('[data-cy="bulk-generate-submit"]').click()
      
      cy.get('[data-cy="bulk-progress"]').should('be.visible')
      cy.get('[data-cy="bulk-success"]').should('be.visible')
      cy.get('[data-cy="letters-table"] tbody tr').should('have.length.greaterThan', 2)
    })

    it('should generate letter with AI assistance', () => {
      cy.get('[data-cy="ai-assisted-btn"]').click()
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="ai-prompt"]').type('Generate an aggressive dispute letter focusing on FCRA violations')
      cy.get('[data-cy="ai-tone"]').select('aggressive')
      cy.get('[data-cy="ai-generate"]').click()
      
      cy.get('[data-cy="ai-loading"]').should('be.visible')
      cy.get('[data-cy="ai-result"]').should('be.visible')
      cy.get('[data-cy="ai-content"]').should('not.be.empty')
      cy.get('[data-cy="use-ai-content"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
    })
  })

  describe('CRUD Operations - Create', () => {
    it('should create new dispute letter manually', () => {
      cy.get('[data-cy="create-manual-btn"]').click()
      cy.get('[data-cy="letter-title"]').type('Custom Dispute Letter')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="letter-type-select"]').select('custom')
      cy.get('[data-cy="recipient-select"]').select('experian')
      cy.get('[data-cy="content-editor"]').type('This is a custom dispute letter content.')
      cy.get('[data-cy="save-letter"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Letter created successfully')
      cy.url().should('include', '/dispute-letters')
      cy.get('[data-cy="letters-table"]').should('contain', 'Custom Dispute Letter')
    })

    it('should create letter from template', () => {
      cy.get('[data-cy="create-from-template-btn"]').click()
      cy.get('[data-cy="template-library"]').should('be.visible')
      cy.get('[data-cy="template-fcra-standard"]').click()
      cy.get('[data-cy="use-template"]').click()
      
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('transunion')
      cy.get('[data-cy="content-editor"]').should('contain', 'Dear TransUnion')
      cy.get('[data-cy="save-letter"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
    })

    it('should save letter as draft', () => {
      cy.get('[data-cy="create-manual-btn"]').click()
      cy.get('[data-cy="letter-title"]').type('Draft Letter')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="letter-type-select"]').select('initial_dispute')
      cy.get('[data-cy="recipient-select"]').select('experian')
      cy.get('[data-cy="content-editor"]').type('Draft content')
      cy.get('[data-cy="save-as-draft"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Draft saved')
      cy.get('[data-cy="letters-table"]').should('contain', 'Draft Letter')
      cy.get('[data-cy="letter-status"]').should('contain', 'draft')
    })

    it('should create letter with attachments', () => {
      cy.get('[data-cy="create-manual-btn"]').click()
      cy.get('[data-cy="letter-title"]').type('Letter with Attachments')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="letter-type-select"]').select('mov_request')
      cy.get('[data-cy="recipient-select"]').select('experian')
      cy.get('[data-cy="content-editor"]').type('Please find attached documents.')
      
      cy.fixture('test-document.pdf').then(fileContent => {
        cy.get('[data-cy="attachment-upload"]').attachFile({
          fileContent: fileContent.toString(),
          fileName: 'dispute-evidence.pdf',
          mimeType: 'application/pdf'
        })
      })
      
      cy.get('[data-cy="attachment-list"]').should('contain', 'dispute-evidence.pdf')
      cy.get('[data-cy="save-letter"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
    })

    it('should create scheduled letter for future sending', () => {
      cy.get('[data-cy="create-manual-btn"]').click()
      cy.get('[data-cy="letter-title"]').type('Scheduled Letter')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="letter-type-select"]').select('follow_up')
      cy.get('[data-cy="recipient-select"]').select('transunion')
      cy.get('[data-cy="content-editor"]').type('Scheduled letter content')
      cy.get('[data-cy="schedule-toggle"]').check()
      cy.get('[data-cy="schedule-date"]').type('2024-12-25')
      cy.get('[data-cy="schedule-time"]').type('09:00')
      cy.get('[data-cy="save-letter"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="letter-status"]').should('contain', 'scheduled')
    })
  })

  describe('CRUD Operations - Read/View', () => {
    it('should display letters list with pagination', () => {
      cy.get('[data-cy="letters-table"]').should('be.visible')
      cy.get('[data-cy="letters-table"] thead').should('contain', 'Title')
      cy.get('[data-cy="letters-table"] thead').should('contain', 'Case')
      cy.get('[data-cy="letters-table"] thead').should('contain', 'Recipient')
      cy.get('[data-cy="letters-table"] thead').should('contain', 'Status')
      cy.get('[data-cy="letters-table"] thead').should('contain', 'Created')
      cy.get('[data-cy="letters-table"] thead').should('contain', 'Actions')
      
      cy.get('[data-cy="pagination"]').should('be.visible')
      cy.get('[data-cy="page-info"]').should('contain', 'Page 1')
    })

    it('should view letter details', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="view-letter"]').click()
      })
      
      cy.get('[data-cy="letter-detail-modal"]').should('be.visible')
      cy.get('[data-cy="letter-title"]').should('not.be.empty')
      cy.get('[data-cy="letter-content"]').should('not.be.empty')
      cy.get('[data-cy="letter-metadata"]').should('be.visible')
      cy.get('[data-cy="close-modal"]').click()
      
      cy.get('[data-cy="letter-detail-modal"]').should('not.be.visible')
    })

    it('should filter letters by type', () => {
      cy.get('[data-cy="filter-type"]').select('initial_dispute')
      cy.get('[data-cy="apply-filters"]').click()
      
      cy.get('[data-cy="letters-table"] tbody tr').each(($row) => {
        cy.wrap($row).should('contain', 'initial_dispute')
      })
      
      cy.get('[data-cy="clear-filters"]').click()
      cy.get('[data-cy="letters-table"] tbody tr').should('have.length.greaterThan', 0)
    })

    it('should filter letters by recipient', () => {
      cy.get('[data-cy="filter-recipient"]').select('experian')
      cy.get('[data-cy="apply-filters"]').click()
      
      cy.get('[data-cy="letters-table"] tbody tr').each(($row) => {
        cy.wrap($row).should('contain', 'experian')
      })
    })

    it('should filter letters by status', () => {
      cy.get('[data-cy="filter-status"]').select('sent')
      cy.get('[data-cy="apply-filters"]').click()
      
      cy.get('[data-cy="letters-table"] tbody tr').each(($row) => {
        cy.wrap($row).find('[data-cy="letter-status"]').should('contain', 'sent')
      })
    })

    it('should filter letters by date range', () => {
      cy.get('[data-cy="filter-date-from"]').type('2024-01-01')
      cy.get('[data-cy="filter-date-to"]').type('2024-12-31')
      cy.get('[data-cy="apply-filters"]').click()
      
      cy.get('[data-cy="letters-table"] tbody tr').should('have.length.greaterThan', 0)
      cy.get('[data-cy="filter-results-count"]').should('be.visible')
    })

    it('should search letters by content', () => {
      cy.get('[data-cy="search-input"]').type('FCRA violation')
      cy.get('[data-cy="search-btn"]').click()
      
      cy.get('[data-cy="search-results"]').should('be.visible')
      cy.get('[data-cy="search-highlight"]').should('contain', 'FCRA violation')
    })

    it('should sort letters by different columns', () => {
      cy.get('[data-cy="sort-title"]').click()
      cy.get('[data-cy="letters-table"] tbody tr').first().should('not.be.empty')
      
      cy.get('[data-cy="sort-date"]').click()
      cy.get('[data-cy="sort-direction"]').should('contain', 'desc')
      
      cy.get('[data-cy="sort-status"]').click()
      cy.url().should('include', 'sort=status')
    })

    it('should export letters to PDF', () => {
      cy.get('[data-cy="export-pdf"]').click()
      cy.get('[data-cy="export-options"]').should('be.visible')
      cy.get('[data-cy="export-confirm"]').click()
      
      cy.get('[data-cy="export-progress"]').should('be.visible')
      cy.get('[data-cy="download-link"]').should('be.visible')
    })

    it('should preview letter in print format', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="print-preview"]').click()
      })
      
      cy.get('[data-cy="print-preview-modal"]').should('be.visible')
      cy.get('[data-cy="preview-content"]').should('have.css', 'font-family')
      cy.get('[data-cy="print-btn"]').should('be.visible')
      cy.get('[data-cy="close-preview"]').click()
    })
  })

  describe('CRUD Operations - Update/Edit', () => {
    it('should edit existing letter', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="edit-letter"]').click()
      })
      
      cy.get('[data-cy="edit-form"]').should('be.visible')
      cy.get('[data-cy="letter-title"]').clear().type('Updated Letter Title')
      cy.get('[data-cy="content-editor"]').clear().type('Updated letter content with new information.')
      cy.get('[data-cy="save-changes"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Letter updated successfully')
      cy.get('[data-cy="letters-table"]').should('contain', 'Updated Letter Title')
    })

    it('should update letter status', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="status-dropdown"]').click()
      })
      
      cy.get('[data-cy="status-sent"]').click()
      cy.get('[data-cy="status-confirm"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Status updated')
      cy.get('[data-cy="letter-status"]').should('contain', 'sent')
    })

    it('should add tracking information to sent letter', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="add-tracking"]').click()
      })
      
      cy.get('[data-cy="tracking-modal"]').should('be.visible')
      cy.get('[data-cy="tracking-number"]').type('1234567890123456789')
      cy.get('[data-cy="sent-date"]').type('2024-01-15')
      cy.get('[data-cy="delivery-method"]').select('certified_mail')
      cy.get('[data-cy="save-tracking"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="tracking-info"]').should('contain', '1234567890123456789')
    })

    it('should update letter priority', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="priority-select"]').select('high')
      })
      
      cy.get('[data-cy="priority-updated"]').should('be.visible')
      cy.get('[data-cy="high-priority-badge"]').should('be.visible')
    })

    it('should edit letter template', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="edit-template"]').click()
      })
      
      cy.get('[data-cy="template-editor"]').should('be.visible')
      cy.get('[data-cy="template-content"]').clear().type('Updated template content with {{client_name}} variable.')
      cy.get('[data-cy="test-template"]').click()
      
      cy.get('[data-cy="template-preview"]').should('contain', 'John Doe')
      cy.get('[data-cy="save-template"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Template updated')
    })

    it('should reschedule letter sending', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="reschedule-btn"]').click()
      })
      
      cy.get('[data-cy="reschedule-modal"]').should('be.visible')
      cy.get('[data-cy="new-schedule-date"]').type('2024-02-15')
      cy.get('[data-cy="new-schedule-time"]').type('10:30')
      cy.get('[data-cy="reschedule-reason"]').type('Client requested delay')
      cy.get('[data-cy="confirm-reschedule"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Letter rescheduled')
      cy.get('[data-cy="letter-status"]').should('contain', 'scheduled')
    })

    it('should bulk update letter status', () => {
      cy.get('[data-cy="select-all-checkbox"]').check()
      cy.get('[data-cy="bulk-actions"]').select('update_status')
      cy.get('[data-cy="bulk-status-select"]').select('review')
      cy.get('[data-cy="bulk-apply"]').click()
      
      cy.get('[data-cy="bulk-confirm"]').should('be.visible')
      cy.get('[data-cy="confirm-bulk-update"]').click()
      
      cy.get('[data-cy="bulk-success"]').should('contain', 'letters updated')
    })

    it('should version control letter edits', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="version-history"]').click()
      })
      
      cy.get('[data-cy="version-modal"]').should('be.visible')
      cy.get('[data-cy="version-list"]').should('contain', 'Version 1.0')
      cy.get('[data-cy="compare-versions"]').click()
      
      cy.get('[data-cy="version-diff"]').should('be.visible')
      cy.get('[data-cy="restore-version"]').click()
      cy.get('[data-cy="confirm-restore"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Version restored')
    })
  })

  describe('CRUD Operations - Delete', () => {
    it('should delete single letter', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="delete-letter"]').click()
      })
      
      cy.get('[data-cy="delete-confirm-modal"]').should('be.visible')
      cy.get('[data-cy="delete-reason"]').type('No longer needed')
      cy.get('[data-cy="confirm-delete"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Letter deleted')
      cy.get('[data-cy="letters-table"] tbody tr').should('have.length.lessThan', 10)
    })

    it('should bulk delete letters', () => {
      cy.get('[data-cy="letter-checkbox"]').first().check()
      cy.get('[data-cy="letter-checkbox"]').eq(1).check()
      cy.get('[data-cy="bulk-delete"]').click()
      
      cy.get('[data-cy="bulk-delete-modal"]').should('be.visible')
      cy.get('[data-cy="delete-count"]').should('contain', '2 letters')
      cy.get('[data-cy="bulk-delete-reason"]').type('Cleanup old letters')
      cy.get('[data-cy="confirm-bulk-delete"]').click()
      
      cy.get('[data-cy="bulk-success"]').should('contain', '2 letters deleted')
    })

    it('should soft delete letter (mark as deleted)', () => {
      cy.get('[data-cy="letters-table"] tbody tr').first().within(() => {
        cy.get('[data-cy="soft-delete"]').click()
      })
      
      cy.get('[data-cy="soft-delete-confirm"]').click()
      cy.get('[data-cy="success-message"]').should('contain', 'Letter archived')
      cy.get('[data-cy="show-deleted"]').check()
      cy.get('[data-cy="deleted-letter-badge"]').should('be.visible')
    })

    it('should restore deleted letter', () => {
      cy.get('[data-cy="show-deleted"]').check()
      cy.get('[data-cy="deleted-letters"]').should('be.visible')
      
      cy.get('[data-cy="restore-letter"]').first().click()
      cy.get('[data-cy="restore-confirm"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Letter restored')
      cy.get('[data-cy="active-letters"]').should('contain.text', 'restored')
    })

    it('should permanently delete letter', () => {
      cy.get('[data-cy="show-deleted"]').check()
      cy.get('[data-cy="deleted-letters"] tbody tr').first().within(() => {
        cy.get('[data-cy="permanent-delete"]').click()
      })
      
      cy.get('[data-cy="permanent-delete-modal"]').should('be.visible')
      cy.get('[data-cy="confirm-text"]').type('PERMANENTLY DELETE')
      cy.get('[data-cy="final-delete"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Letter permanently deleted')
    })
  })

  describe('Negative Tests - Validation Errors', () => {
    it('should show error for empty letter title', () => {
      cy.get('[data-cy="create-manual-btn"]').click()
      cy.get('[data-cy="letter-title"]').focus().blur()
      
      cy.get('[data-cy="title-error"]').should('contain', 'Title is required')
      cy.get('[data-cy="save-letter"]').should('be.disabled')
    })

    it('should show error for missing case selection', () => {
      cy.get('[data-cy="create-manual-btn"]').click()
      cy.get('[data-cy="letter-title"]').type('Test Letter')
      cy.get('[data-cy="save-letter"]').click()
      
      cy.get('[data-cy="case-error"]').should('contain', 'Please select a case')
      cy.get('[data-cy="error-message"]').should('be.visible')
    })

    it('should show error for invalid recipient selection', () => {
      cy.get('[data-cy="create-manual-btn"]').click()
      cy.get('[data-cy="letter-title"]').type('Test Letter')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('')
      cy.get('[data-cy="save-letter"]').click()
      
      cy.get('[data-cy="recipient-error"]').should('contain', 'Please select a recipient')
    })

    it('should show error for empty letter content', () => {
      cy.get('[data-cy="create-manual-btn"]').click()
      cy.get('[data-cy="letter-title"]').type('Test Letter')
      cy.get('[data-cy="case-select"]').select('1')
      cy.get('[data-cy="recipient-select"]').select('experian')
      cy.get('[data-cy="content-editor"]').clear()
      cy.get('[data-cy="save-letter"]').click()
      
      cy.get('[data-cy="content-error"]').should('contain', 'Letter content cannot be empty')
    })

    it('should show error for invalid date format', () => {
      cy.get('[data-cy="create-manual-btn"]').click