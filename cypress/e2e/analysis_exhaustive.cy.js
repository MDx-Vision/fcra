/// <reference types="cypress" />

describe('Analysis CRUD Operations', () => {
  let testClient, testCase

  beforeEach(() => {
    cy.visit('/staff/login')
    cy.get('[data-cy=email-input]').type('test@example.com')
    cy.get('[data-cy=password-input]').type('testpass123')
    cy.get('[data-cy=login-button]').click()
    cy.url().should('include', '/dashboard')

    // Create test client and case
    cy.request('POST', '/api/clients/add', {
      first_name: 'Analysis',
      last_name: 'Test',
      email: 'analysis@test.com',
      phone: '555-123-4567',
      ssn_last_four: '1234',
      date_of_birth: '1990-01-01'
    }).then(response => {
      testClient = response.body.client
      
      return cy.request('POST', '/api/cases/add', {
        client_id: testClient.id,
        case_type: 'FCRA',
        status: 'active',
        description: 'Test analysis case'
      })
    }).then(response => {
      testCase = response.body.case
    })
  })

  describe('Analysis Creation - Happy Path Tests', () => {
    it('should create new analysis with all required fields', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Credit Report Review')
      cy.get('[data-cy=findings-textarea]').type('Test findings content')
      cy.get('[data-cy=recommendations-textarea]').type('Test recommendations content')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.url().should('include', `/cases/${testCase.id}`)
      cy.get('[data-cy=success-message]').should('contain', 'Analysis created successfully')
      cy.get('[data-cy=analysis-list]').should('contain', 'Credit Report Review')
      cy.get('[data-cy=analysis-list]').should('contain', 'Test findings content')
    })

    it('should create analysis with comprehensive findings', () => {
      const comprehensiveFindings = 'Comprehensive analysis findings including multiple violations, timeline issues, and detailed recommendations for client case.'
      
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Violation Analysis')
      cy.get('[data-cy=findings-textarea]').type(comprehensiveFindings)
      cy.get('[data-cy=recommendations-textarea]').type('Detailed recommendations based on findings')
      cy.get('[data-cy=analysis-status-select]').select('complete')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('be.visible')
      cy.get('[data-cy=analysis-item]').first().should('contain', 'Violation Analysis')
      cy.get('[data-cy=analysis-item]').first().should('contain', 'complete')
    })

    it('should create analysis with legal strategy type', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Legal Strategy')
      cy.get('[data-cy=findings-textarea]').type('Strategic legal analysis findings')
      cy.get('[data-cy=recommendations-textarea]').type('Strategic recommendations')
      cy.get('[data-cy=priority-level-select]').select('high')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=analysis-list]').should('contain', 'Legal Strategy')
      cy.get('[data-cy=analysis-list]').should('contain', 'high')
    })

    it('should create analysis with damage assessment type', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Damage Assessment')
      cy.get('[data-cy=findings-textarea]').type('Detailed damage assessment findings')
      cy.get('[data-cy=recommendations-textarea]').type('Damage mitigation recommendations')
      cy.get('[data-cy=estimated-damages-input]').type('15000')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('contain', 'Analysis created')
      cy.get('[data-cy=analysis-item]').should('contain', '$15,000')
    })

    it('should create analysis and auto-save draft', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Settlement Analysis')
      cy.get('[data-cy=findings-textarea]').type('Settlement analysis findings')
      cy.wait(2000) // Auto-save delay
      
      cy.get('[data-cy=draft-saved-indicator]').should('be.visible')
      cy.get('[data-cy=draft-saved-indicator]').should('contain', 'Draft saved')
    })

    it('should create analysis with multiple attachments', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Evidence Review')
      cy.get('[data-cy=findings-textarea]').type('Evidence review findings')
      cy.get('[data-cy=recommendations-textarea]').type('Evidence recommendations')
      
      // Upload multiple files
      cy.get('[data-cy=attachment-upload]').selectFile([
        'cypress/fixtures/test-document.pdf',
        'cypress/fixtures/test-image.jpg'
      ])
      
      cy.get('[data-cy=save-analysis-button]').click()
      cy.get('[data-cy=success-message]').should('be.visible')
      cy.get('[data-cy=attachment-list]').should('contain', '2 files')
    })

    it('should create analysis with structured JSON findings', () => {
      const structuredFindings = JSON.stringify({
        violations: ['FCRA Section 611', 'FCRA Section 623'],
        timeline: '30-day investigation period exceeded',
        damages: { actual: 5000, statutory: 1000 }
      })
      
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Technical Analysis')
      cy.get('[data-cy=structured-findings-toggle]').click()
      cy.get('[data-cy=findings-json-editor]').type(structuredFindings)
      cy.get('[data-cy=recommendations-textarea]').type('Technical recommendations')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('be.visible')
      cy.get('[data-cy=analysis-item]').should('contain', 'Technical Analysis')
    })

    it('should create analysis with timeline and milestones', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Timeline Analysis')
      cy.get('[data-cy=findings-textarea]').type('Timeline analysis findings')
      cy.get('[data-cy=recommendations-textarea]').type('Timeline recommendations')
      
      // Add timeline milestones
      cy.get('[data-cy=add-milestone-button]').click()
      cy.get('[data-cy=milestone-date-input]').type('2024-01-15')
      cy.get('[data-cy=milestone-description-input]').type('Initial dispute filed')
      cy.get('[data-cy=add-milestone-confirm]').click()
      
      cy.get('[data-cy=save-analysis-button]').click()
      cy.get('[data-cy=success-message]').should('be.visible')
      cy.get('[data-cy=timeline-milestones]').should('contain', 'Initial dispute filed')
    })

    it('should create analysis with client collaboration notes', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Client Consultation')
      cy.get('[data-cy=findings-textarea]').type('Client consultation findings')
      cy.get('[data-cy=recommendations-textarea]').type('Client action items')
      cy.get('[data-cy=client-notes-textarea]').type('Client expressed concerns about timeline')
      cy.get('[data-cy=follow-up-required-checkbox]').check()
      cy.get('[data-cy=follow-up-date-input]').type('2024-02-01')
      
      cy.get('[data-cy=save-analysis-button]').click()
      cy.get('[data-cy=success-message]').should('be.visible')
      cy.get('[data-cy=analysis-item]').should('contain', 'Follow-up required')
    })

    it('should create analysis with case law references', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Legal Research')
      cy.get('[data-cy=findings-textarea]').type('Legal research findings')
      cy.get('[data-cy=recommendations-textarea]').type('Legal strategy recommendations')
      
      // Add case law references
      cy.get('[data-cy=add-case-law-button]').click()
      cy.get('[data-cy=case-name-input]').type('Spokeo v. Robins')
      cy.get('[data-cy=citation-input]').type('578 U.S. 330 (2016)')
      cy.get('[data-cy=relevance-textarea]').type('Standing requirements for FCRA claims')
      cy.get('[data-cy=add-case-law-confirm]').click()
      
      cy.get('[data-cy=save-analysis-button]').click()
      cy.get('[data-cy=success-message]').should('be.visible')
      cy.get('[data-cy=case-law-references]').should('contain', 'Spokeo v. Robins')
    })
  })

  describe('Analysis Creation - Validation Tests', () => {
    it('should reject analysis without analysis type', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=findings-textarea]').type('Test findings')
      cy.get('[data-cy=recommendations-textarea]').type('Test recommendations')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=error-message]').should('contain', 'Analysis type is required')
      cy.get('[data-cy=analysis-type-select]').should('have.class', 'error')
    })

    it('should reject analysis without findings', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Credit Report Review')
      cy.get('[data-cy=recommendations-textarea]').type('Test recommendations')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=error-message]').should('contain', 'Findings are required')
      cy.get('[data-cy=findings-textarea]').should('have.class', 'error')
    })

    it('should reject analysis without recommendations', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Credit Report Review')
      cy.get('[data-cy=findings-textarea]').type('Test findings')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=error-message]').should('contain', 'Recommendations are required')
      cy.get('[data-cy=recommendations-textarea]').should('have.class', 'error')
    })

    it('should reject findings that are too short', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Credit Report Review')
      cy.get('[data-cy=findings-textarea]').type('Too short')
      cy.get('[data-cy=recommendations-textarea]').type('Test recommendations')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=error-message]').should('contain', 'Findings must be at least 50 characters')
      cy.get('[data-cy=findings-textarea]').should('have.class', 'error')
    })

    it('should reject recommendations that are too short', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Credit Report Review')
      cy.get('[data-cy=findings-textarea]').type('Detailed findings content that meets minimum requirements')
      cy.get('[data-cy=recommendations-textarea]').type('Too short')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=error-message]').should('contain', 'Recommendations must be at least 50 characters')
      cy.get('[data-cy=recommendations-textarea]').should('have.class', 'error')
    })

    it('should reject findings that exceed maximum length', () => {
      const longText = 'A'.repeat(10001)
      
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Credit Report Review')
      cy.get('[data-cy=findings-textarea]').type(longText)
      cy.get('[data-cy=recommendations-textarea]').type('Test recommendations content')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=error-message]').should('contain', 'Findings cannot exceed 10,000 characters')
      cy.get('[data-cy=character-count]').should('contain', '10001/10000')
    })

    it('should validate invalid JSON in structured findings', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Technical Analysis')
      cy.get('[data-cy=structured-findings-toggle]').click()
      cy.get('[data-cy=findings-json-editor]').type('{ invalid json }')
      cy.get('[data-cy=recommendations-textarea]').type('Test recommendations')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=error-message]').should('contain', 'Invalid JSON format in findings')
      cy.get('[data-cy=findings-json-editor]').should('have.class', 'error')
    })

    it('should validate negative damage amounts', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Damage Assessment')
      cy.get('[data-cy=findings-textarea]').type('Damage assessment findings')
      cy.get('[data-cy=recommendations-textarea]').type('Damage recommendations')
      cy.get('[data-cy=estimated-damages-input]').type('-5000')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=error-message]').should('contain', 'Estimated damages must be positive')
      cy.get('[data-cy=estimated-damages-input]').should('have.class', 'error')
    })

    it('should validate invalid date formats in milestones', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Timeline Analysis')
      cy.get('[data-cy=findings-textarea]').type('Timeline analysis findings')
      cy.get('[data-cy=recommendations-textarea]').type('Timeline recommendations')
      
      cy.get('[data-cy=add-milestone-button]').click()
      cy.get('[data-cy=milestone-date-input]').type('invalid-date')
      cy.get('[data-cy=milestone-description-input]').type('Test milestone')
      cy.get('[data-cy=add-milestone-confirm]').click()
      
      cy.get('[data-cy=error-message]').should('contain', 'Invalid date format')
      cy.get('[data-cy=milestone-date-input]').should('have.class', 'error')
    })

    it('should validate file upload size limits', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Evidence Review')
      cy.get('[data-cy=findings-textarea]').type('Evidence review findings')
      cy.get('[data-cy=recommendations-textarea]').type('Evidence recommendations')
      
      // Try to upload oversized file
      cy.get('[data-cy=attachment-upload]').selectFile('cypress/fixtures/oversized-file.pdf', { force: true })
      
      cy.get('[data-cy=error-message]').should('contain', 'File size exceeds 10MB limit')
      cy.get('[data-cy=upload-error-list]').should('contain', 'oversized-file.pdf')
    })
  })

  describe('Analysis Reading/Viewing Tests', () => {
    beforeEach(() => {
      // Create test analysis
      cy.request('POST', `/api/cases/${testCase.id}/analyses`, {
        analysis_type: 'Credit Report Review',
        findings: 'Test analysis findings content',
        recommendations: 'Test analysis recommendations content',
        status: 'complete'
      })
    })

    it('should display analysis list for case', () => {
      cy.visit(`/cases/${testCase.id}`)
      
      cy.get('[data-cy=analysis-section]').should('be.visible')
      cy.get('[data-cy=analysis-list]').should('contain', 'Credit Report Review')
      cy.get('[data-cy=analysis-list]').should('contain', 'Test analysis findings')
      cy.get('[data-cy=analysis-status-badge]').should('contain', 'complete')
    })

    it('should show analysis details in modal', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().click()
      
      cy.get('[data-cy=analysis-modal]').should('be.visible')
      cy.get('[data-cy=analysis-modal-title]').should('contain', 'Credit Report Review')
      cy.get('[data-cy=analysis-findings-content]').should('contain', 'Test analysis findings content')
      cy.get('[data-cy=analysis-recommendations-content]').should('contain', 'Test analysis recommendations content')
      cy.get('[data-cy=analysis-created-date]').should('be.visible')
    })

    it('should display analysis metadata correctly', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().click()
      
      cy.get('[data-cy=analysis-modal]').should('be.visible')
      cy.get('[data-cy=analysis-created-by]').should('contain', 'CI Test Admin')
      cy.get('[data-cy=analysis-created-date]').should('be.visible')
      cy.get('[data-cy=analysis-last-modified]').should('be.visible')
      cy.get('[data-cy=analysis-word-count]').should('be.visible')
    })

    it('should show analysis attachments', () => {
      // Create analysis with attachment
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=add-analysis-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Evidence Review')
      cy.get('[data-cy=findings-textarea]').type('Evidence findings with attachment')
      cy.get('[data-cy=recommendations-textarea]').type('Evidence recommendations')
      cy.get('[data-cy=attachment-upload]').selectFile('cypress/fixtures/test-document.pdf')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=analysis-item]').first().click()
      cy.get('[data-cy=analysis-modal]').should('be.visible')
      cy.get('[data-cy=attachment-list]').should('contain', 'test-document.pdf')
      cy.get('[data-cy=attachment-download-link]').should('have.attr', 'href')
    })

    it('should display analysis in full-page view', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=view-full-button]').click()
      
      cy.url().should('include', '/analysis/')
      cy.get('[data-cy=analysis-full-view]').should('be.visible')
      cy.get('[data-cy=analysis-title]').should('contain', 'Credit Report Review')
      cy.get('[data-cy=analysis-findings-section]').should('be.visible')
      cy.get('[data-cy=analysis-recommendations-section]').should('be.visible')
    })

    it('should show analysis history and versions', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().click()
      
      cy.get('[data-cy=analysis-modal]').should('be.visible')
      cy.get('[data-cy=analysis-history-tab]').click()
      cy.get('[data-cy=version-history]').should('be.visible')
      cy.get('[data-cy=version-item]').should('contain', 'v1.0')
      cy.get('[data-cy=version-created-date]').should('be.visible')
    })

    it('should export analysis to PDF', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().click()
      
      cy.get('[data-cy=analysis-modal]').should('be.visible')
      cy.get('[data-cy=export-pdf-button]').click()
      
      // Check that PDF download started
      cy.get('[data-cy=download-progress]').should('be.visible')
      cy.get('[data-cy=success-message]').should('contain', 'PDF generated successfully')
    })

    it('should print analysis', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=view-full-button]').click()
      
      cy.get('[data-cy=print-analysis-button]').click()
      
      // Verify print dialog opens (can't test actual printing)
      cy.window().its('print').should('exist')
    })

    it('should search analyses by content', () => {
      cy.visit(`/cases/${testCase.id}`)
      
      cy.get('[data-cy=analysis-search-input]').type('findings content')
      cy.get('[data-cy=analysis-search-button]').click()
      
      cy.get('[data-cy=analysis-list]').should('contain', 'Credit Report Review')
      cy.get('[data-cy=search-results-count]').should('contain', '1 result')
    })

    it('should filter analyses by type', () => {
      cy.visit(`/cases/${testCase.id}`)
      
      cy.get('[data-cy=analysis-filter-select]').select('Credit Report Review')
      
      cy.get('[data-cy=analysis-list]').should('contain', 'Credit Report Review')
      cy.get('[data-cy=analysis-list]').find('[data-cy=analysis-item]').should('have.length', 1)
    })
  })

  describe('Analysis Update Tests', () => {
    let analysisId

    beforeEach(() => {
      cy.request('POST', `/api/cases/${testCase.id}/analyses`, {
        analysis_type: 'Credit Report Review',
        findings: 'Original findings content',
        recommendations: 'Original recommendations content',
        status: 'draft'
      }).then(response => {
        analysisId = response.body.analysis.id
      })
    })

    it('should update analysis findings', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=edit-button]').click()
      
      cy.get('[data-cy=findings-textarea]').clear()
      cy.get('[data-cy=findings-textarea]').type('Updated findings content')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('contain', 'Analysis updated successfully')
      cy.get('[data-cy=analysis-list]').should('contain', 'Updated findings content')
    })

    it('should update analysis recommendations', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=edit-button]').click()
      
      cy.get('[data-cy=recommendations-textarea]').clear()
      cy.get('[data-cy=recommendations-textarea]').type('Updated recommendations content')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('contain', 'Analysis updated successfully')
      cy.get('[data-cy=analysis-list]').should('contain', 'Updated recommendations')
    })

    it('should update analysis type', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=edit-button]').click()
      
      cy.get('[data-cy=analysis-type-select]').select('Legal Strategy')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('contain', 'Analysis updated successfully')
      cy.get('[data-cy=analysis-list]').should('contain', 'Legal Strategy')
    })

    it('should update analysis status', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=edit-button]').click()
      
      cy.get('[data-cy=analysis-status-select]').select('complete')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('contain', 'Analysis updated successfully')
      cy.get('[data-cy=analysis-status-badge]').should('contain', 'complete')
    })

    it('should update analysis priority level', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=edit-button]').click()
      
      cy.get('[data-cy=priority-level-select]').select('high')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('contain', 'Analysis updated successfully')
      cy.get('[data-cy=analysis-priority-badge]').should('contain', 'high')
      cy.get('[data-cy=analysis-priority-badge]').should('have.class', 'priority-high')
    })

    it('should add attachments to existing analysis', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=edit-button]').click()
      
      cy.get('[data-cy=attachment-upload]').selectFile('cypress/fixtures/test-document.pdf')
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('contain', 'Analysis updated successfully')
      cy.get('[data-cy=analysis-item]').first().click()
      cy.get('[data-cy=attachment-list]').should('contain', 'test-document.pdf')
    })

    it('should remove attachments from analysis', () => {
      // First add attachment
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=edit-button]').click()
      cy.get('[data-cy=attachment-upload]').selectFile('cypress/fixtures/test-document.pdf')
      cy.get('[data-cy=save-analysis-button]').click()
      
      // Then remove it
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=edit-button]').click()
      cy.get('[data-cy=attachment-remove-button]').click()
      cy.get('[data-cy=confirm-remove-attachment]').click()
      cy.get('[data-cy=save-analysis-button]').click()
      
      cy.get('[data-cy=success-message]').should('contain', 'Analysis updated successfully')
      cy.get('[data-cy=analysis-item]').first().click()
      cy.get('[data-cy=attachment-list]').should('not.exist')
    })

    it('should update analysis with version tracking', () => {
      cy.visit(`/cases/${testCase.id}`)
      cy.get('[data-cy=analysis-item]').first().find('[data-cy=edit-