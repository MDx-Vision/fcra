/// <reference types="cypress" />

describe('Cases - CRUD Operations', () => {
  beforeEach(() => {
    cy.visit('/staff/login')
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('testpass123')
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
  })

  describe('Case Creation - Happy Path', () => {
    it('should create a new case with all required fields', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="case-description"]').type('Test case description')
      cy.get('[data-cy="case-bureau-select"]').select('Experian')
      cy.get('[data-cy="case-creditor"]').type('Test Creditor')
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.url().should('include', '/cases/')
      cy.get('[data-cy="success-message"]').should('contain', 'Case created successfully')
      cy.get('[data-cy="case-status"]').should('contain', 'Open')
    })

    it('should create case with minimal required fields only', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('TCPA')
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.url().should('include', '/cases/')
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="case-id"]').should('exist')
    })

    it('should create case with all case types', () => {
      const caseTypes = ['FCRA', 'FDCPA', 'TCPA', 'FCBA']
      caseTypes.forEach(type => {
        cy.get('[data-cy="cases-menu"]').click()
        cy.get('[data-cy="new-case-btn"]').click()
        cy.get('[data-cy="case-client-select"]').select('1')
        cy.get('[data-cy="case-type-select"]').select(type)
        cy.get('[data-cy="case-description"]').type(`Test ${type} case`)
        cy.get('[data-cy="save-case-btn"]').click()
        
        cy.get('[data-cy="case-type-display"]').should('contain', type)
        cy.url().should('include', '/cases/')
      })
    })

    it('should create case with all bureau options', () => {
      const bureaus = ['Experian', 'TransUnion', 'Equifax']
      bureaus.forEach(bureau => {
        cy.get('[data-cy="cases-menu"]').click()
        cy.get('[data-cy="new-case-btn"]').click()
        cy.get('[data-cy="case-client-select"]').select('1')
        cy.get('[data-cy="case-type-select"]').select('FCRA')
        cy.get('[data-cy="case-bureau-select"]').select(bureau)
        cy.get('[data-cy="save-case-btn"]').click()
        
        cy.get('[data-cy="case-bureau-display"]').should('contain', bureau)
      })
    })

    it('should auto-assign case to current staff member', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="case-assigned-to"]').should('contain', 'CI Test Admin')
    })
  })

  describe('Case Creation - Validation Errors', () => {
    it('should show error when client is not selected', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="client-error"]').should('contain', 'Client is required')
      cy.url().should('include', '/cases/new')
    })

    it('should show error when case type is not selected', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="case-type-error"]').should('contain', 'Case type is required')
      cy.url().should('include', '/cases/new')
    })

    it('should validate description max length', () => {
      const longDescription = 'a'.repeat(5001)
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="case-description"]').type(longDescription)
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="description-error"]').should('contain', 'Description cannot exceed 5000 characters')
    })

    it('should sanitize XSS attempts in description', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="case-description"]').type('<script>alert("xss")</script>')
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="case-description-display"]').should('not.contain', '<script>')
      cy.get('[data-cy="case-description-display"]').should('contain', 'alert("xss")')
    })

    it('should handle SQL injection attempts in creditor field', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="case-creditor"]').type("'; DROP TABLE cases; --")
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="case-creditor-display"]').should('contain', "'; DROP TABLE cases; --")
    })

    it('should validate special characters in all text fields', () => {
      const specialChars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="case-description"]').type(specialChars)
      cy.get('[data-cy="case-creditor"]').type(specialChars)
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="case-description-display"]').should('contain', specialChars)
    })

    it('should handle Unicode characters in text fields', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="case-description"]').type('测试 Ñoël Café 🏦 💳')
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="success-message"]').should('be.visible')
      cy.get('[data-cy="case-description-display"]').should('contain', '测试 Ñoël Café 🏦 💳')
    })

    it('should handle empty string submissions', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-description"]').type('   ')
      cy.get('[data-cy="case-creditor"]').type('   ')
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="client-error"]').should('be.visible')
      cy.get('[data-cy="case-type-error"]').should('be.visible')
    })
  })

  describe('Case Reading/Viewing', () => {
    beforeEach(() => {
      // Create a test case first
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="case-description"]').type('Test case for viewing')
      cy.get('[data-cy="save-case-btn"]').click()
      cy.get('[data-cy="case-id"]').then($el => {
        cy.wrap($el.text()).as('caseId')
      })
    })

    it('should display case details correctly', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}`)
        cy.get('[data-cy="case-id"]').should('contain', caseId)
        cy.get('[data-cy="case-type-display"]').should('contain', 'FCRA')
        cy.get('[data-cy="case-description-display"]').should('contain', 'Test case for viewing')
        cy.get('[data-cy="case-status"]').should('contain', 'Open')
        cy.get('[data-cy="case-client-name"]').should('contain', 'John Doe')
      })
    })

    it('should show case timeline/events', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}`)
        cy.get('[data-cy="case-timeline"]').should('be.visible')
        cy.get('[data-cy="timeline-event"]').should('contain', 'Case created')
      })
    })

    it('should display all case metadata', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}`)
        cy.get('[data-cy="case-created-date"]').should('be.visible')
        cy.get('[data-cy="case-updated-date"]').should('be.visible')
        cy.get('[data-cy="case-assigned-to"]').should('be.visible')
      })
    })

    it('should handle viewing non-existent case', () => {
      cy.visit('/cases/99999')
      cy.get('[data-cy="error-message"]').should('contain', 'Case not found')
      cy.get('[data-cy="back-to-cases-btn"]').should('be.visible')
    })

    it('should handle invalid case ID format', () => {
      cy.visit('/cases/abc')
      cy.get('[data-cy="error-message"]').should('contain', 'Invalid case ID')
    })
  })

  describe('Case Updating', () => {
    beforeEach(() => {
      // Create a test case first
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="case-description"]').type('Original description')
      cy.get('[data-cy="save-case-btn"]').click()
      cy.get('[data-cy="case-id"]').then($el => {
        cy.wrap($el.text()).as('caseId')
      })
    })

    it('should update case description', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}/edit`)
        cy.get('[data-cy="case-description"]').clear().type('Updated description')
        cy.get('[data-cy="save-case-btn"]').click()
        
        cy.get('[data-cy="success-message"]').should('contain', 'Case updated successfully')
        cy.get('[data-cy="case-description-display"]').should('contain', 'Updated description')
      })
    })

    it('should update case type', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}/edit`)
        cy.get('[data-cy="case-type-select"]').select('FDCPA')
        cy.get('[data-cy="save-case-btn"]').click()
        
        cy.get('[data-cy="case-type-display"]').should('contain', 'FDCPA')
        cy.get('[data-cy="success-message"]').should('be.visible')
      })
    })

    it('should update case bureau', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}/edit`)
        cy.get('[data-cy="case-bureau-select"]').select('TransUnion')
        cy.get('[data-cy="save-case-btn"]').click()
        
        cy.get('[data-cy="case-bureau-display"]').should('contain', 'TransUnion')
      })
    })

    it('should update case creditor', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}/edit`)
        cy.get('[data-cy="case-creditor"]').clear().type('Updated Creditor')
        cy.get('[data-cy="save-case-btn"]').click()
        
        cy.get('[data-cy="case-creditor-display"]').should('contain', 'Updated Creditor')
      })
    })

    it('should prevent updating with invalid data', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}/edit`)
        cy.get('[data-cy="case-description"]').clear().type('a'.repeat(5001))
        cy.get('[data-cy="save-case-btn"]').click()
        
        cy.get('[data-cy="description-error"]').should('be.visible')
        cy.url().should('include', '/edit')
      })
    })

    it('should show updated timestamp after edit', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}`)
        cy.get('[data-cy="case-updated-date"]').then($original => {
          const originalTime = $original.text()
          
          cy.visit(`/cases/${caseId}/edit`)
          cy.get('[data-cy="case-description"]').clear().type('New description')
          cy.get('[data-cy="save-case-btn"]').click()
          
          cy.get('[data-cy="case-updated-date"]').should('not.contain', originalTime)
        })
      })
    })

    it('should create audit trail for updates', () => {
      cy.get('@caseId').then(caseId => {
        cy.visit(`/cases/${caseId}/edit`)
        cy.get('[data-cy="case-description"]').clear().type('Audited change')
        cy.get('[data-cy="save-case-btn"]').click()
        
        cy.get('[data-cy="case-timeline"]').should('contain', 'Case updated')
        cy.get('[data-cy="timeline-event"]').should('contain', 'CI Test Admin')
      })
    })
  })

  describe('Case Status Management', () => {
    beforeEach(() => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="save-case-btn"]').click()
      cy.get('[data-cy="case-id"]').then($el => {
        cy.wrap($el.text()).as('caseId')
      })
    })

    it('should start with Open status by default', () => {
      cy.get('[data-cy="case-status"]').should('contain', 'Open')
      cy.get('[data-cy="status-badge"]').should('have.class', 'status-open')
    })

    it('should update status to In Progress', () => {
      cy.get('[data-cy="status-dropdown"]').click()
      cy.get('[data-cy="status-option-in-progress"]').click()
      cy.get('[data-cy="confirm-status-change"]').click()
      
      cy.get('[data-cy="case-status"]').should('contain', 'In Progress')
      cy.get('[data-cy="success-message"]').should('contain', 'Status updated')
    })

    it('should update status to Closed', () => {
      cy.get('[data-cy="status-dropdown"]').click()
      cy.get('[data-cy="status-option-closed"]').click()
      cy.get('[data-cy="confirm-status-change"]').click()
      
      cy.get('[data-cy="case-status"]').should('contain', 'Closed')
      cy.get('[data-cy="status-badge"]').should('have.class', 'status-closed')
    })

    it('should update status to Settled', () => {
      cy.get('[data-cy="status-dropdown"]').click()
      cy.get('[data-cy="status-option-settled"]').click()
      cy.get('[data-cy="confirm-status-change"]').click()
      
      cy.get('[data-cy="case-status"]').should('contain', 'Settled')
      cy.get('[data-cy="status-badge"]').should('have.class', 'status-settled')
    })

    it('should update status to On Hold', () => {
      cy.get('[data-cy="status-dropdown"]').click()
      cy.get('[data-cy="status-option-on-hold"]').click()
      cy.get('[data-cy="confirm-status-change"]').click()
      
      cy.get('[data-cy="case-status"]').should('contain', 'On Hold')
    })

    it('should require confirmation for status changes', () => {
      cy.get('[data-cy="status-dropdown"]').click()
      cy.get('[data-cy="status-option-closed"]').click()
      cy.get('[data-cy="cancel-status-change"]').click()
      
      cy.get('[data-cy="case-status"]').should('contain', 'Open')
      cy.get('[data-cy="status-modal"]').should('not.be.visible')
    })

    it('should log status changes in timeline', () => {
      cy.get('[data-cy="status-dropdown"]').click()
      cy.get('[data-cy="status-option-in-progress"]').click()
      cy.get('[data-cy="confirm-status-change"]').click()
      
      cy.get('[data-cy="case-timeline"]').should('contain', 'Status changed to In Progress')
      cy.get('[data-cy="timeline-event"]').should('contain', 'CI Test Admin')
    })

    it('should show status history', () => {
      cy.get('[data-cy="status-dropdown"]').click()
      cy.get('[data-cy="status-option-in-progress"]').click()
      cy.get('[data-cy="confirm-status-change"]').click()
      
      cy.get('[data-cy="status-history-btn"]').click()
      cy.get('[data-cy="status-history"]').should('contain', 'Open → In Progress')
    })

    it('should prevent invalid status transitions', () => {
      cy.get('[data-cy="status-dropdown"]').click()
      cy.get('[data-cy="status-option-closed"]').click()
      cy.get('[data-cy="confirm-status-change"]').click()
      
      cy.get('[data-cy="status-dropdown"]').click()
      cy.get('[data-cy="status-option-open"]').should('be.disabled')
    })
  })

  describe('Case Assignment', () => {
    beforeEach(() => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="save-case-btn"]').click()
      cy.get('[data-cy="case-id"]').then($el => {
        cy.wrap($el.text()).as('caseId')
      })
    })

    it('should show current assignment', () => {
      cy.get('[data-cy="case-assigned-to"]').should('contain', 'CI Test Admin')
      cy.get('[data-cy="assignee-avatar"]').should('be.visible')
    })

    it('should allow reassigning to different staff member', () => {
      cy.get('[data-cy="reassign-btn"]').click()
      cy.get('[data-cy="staff-select"]').select('2')
      cy.get('[data-cy="confirm-reassign"]').click()
      
      cy.get('[data-cy="success-message"]').should('contain', 'Case reassigned successfully')
      cy.get('[data-cy="case-assigned-to"]').should('not.contain', 'CI Test Admin')
    })

    it('should show unassigned state', () => {
      cy.get('[data-cy="reassign-btn"]').click()
      cy.get('[data-cy="staff-select"]').select('')
      cy.get('[data-cy="confirm-reassign"]').click()
      
      cy.get('[data-cy="case-assigned-to"]').should('contain', 'Unassigned')
      cy.get('[data-cy="unassigned-badge"]').should('be.visible')
    })

    it('should log assignment changes', () => {
      cy.get('[data-cy="reassign-btn"]').click()
      cy.get('[data-cy="staff-select"]').select('2')
      cy.get('[data-cy="confirm-reassign"]').click()
      
      cy.get('[data-cy="case-timeline"]').should('contain', 'Case reassigned')
    })

    it('should handle self-assignment', () => {
      cy.get('[data-cy="reassign-btn"]').click()
      cy.get('[data-cy="staff-select"]').select('1')
      cy.get('[data-cy="confirm-reassign"]').click()
      
      cy.get('[data-cy="case-assigned-to"]').should('contain', 'CI Test Admin')
    })

    it('should show assignment options based on staff role', () => {
      cy.get('[data-cy="reassign-btn"]').click()
      cy.get('[data-cy="staff-select"] option').should('have.length.greaterThan', 1)
      cy.get('[data-cy="staff-select"] option[value="1"]').should('contain', 'CI Test Admin')
    })
  })

  describe('Case Deletion', () => {
    beforeEach(() => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="save-case-btn"]').click()
      cy.get('[data-cy="case-id"]').then($el => {
        cy.wrap($el.text()).as('caseId')
      })
    })

    it('should require confirmation before deleting', () => {
      cy.get('[data-cy="case-actions-menu"]').click()
      cy.get('[data-cy="delete-case-btn"]').click()
      cy.get('[data-cy="delete-confirmation-modal"]').should('be.visible')
      cy.get('[data-cy="confirm-delete-text"]').should('contain', 'This action cannot be undone')
    })

    it('should cancel deletion when user clicks cancel', () => {
      cy.get('[data-cy="case-actions-menu"]').click()
      cy.get('[data-cy="delete-case-btn"]').click()
      cy.get('[data-cy="cancel-delete"]').click()
      
      cy.get('[data-cy="delete-confirmation-modal"]').should('not.be.visible')
      cy.get('[data-cy="case-id"]').should('be.visible')
    })

    it('should delete case when confirmed', () => {
      cy.get('[data-cy="case-actions-menu"]').click()
      cy.get('[data-cy="delete-case-btn"]').click()
      cy.get('[data-cy="confirm-delete"]').click()
      
      cy.url().should('include', '/cases')
      cy.get('[data-cy="success-message"]').should('contain', 'Case deleted successfully')
    })

    it('should require typing DELETE to confirm', () => {
      cy.get('[data-cy="case-actions-menu"]').click()
      cy.get('[data-cy="delete-case-btn"]').click()
      cy.get('[data-cy="delete-confirmation-input"]').type('delete')
      cy.get('[data-cy="confirm-delete"]').should('be.disabled')
      
      cy.get('[data-cy="delete-confirmation-input"]').clear().type('DELETE')
      cy.get('[data-cy="confirm-delete"]').should('not.be.disabled')
    })

    it('should prevent deletion of cases with violations', () => {
      // First add a violation to the case
      cy.get('[data-cy="add-violation-btn"]').click()
      cy.get('[data-cy="violation-type"]').select('Inaccurate Information')
      cy.get('[data-cy="violation-description"]').type('Test violation')
      cy.get('[data-cy="save-violation-btn"]').click()
      
      cy.get('[data-cy="case-actions-menu"]').click()
      cy.get('[data-cy="delete-case-btn"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Cannot delete case with existing violations')
    })
  })

  describe('Role-Based Access Control', () => {
    it('should allow admin to access all case functions', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').should('be.visible')
      cy.get('[data-cy="cases-table"]').should('be.visible')
      
      // Create a case to test edit/delete access
      cy.get('[data-cy="new-case-btn"]').click()
      cy.get('[data-cy="case-client-select"]').select('1')
      cy.get('[data-cy="case-type-select"]').select('FCRA')
      cy.get('[data-cy="save-case-btn"]').click()
      
      cy.get('[data-cy="edit-case-btn"]').should('be.visible')
      cy.get('[data-cy="case-actions-menu"]').should('be.visible')
    })

    it('should restrict viewer role from creating/editing cases', () => {
      // Login as viewer (would need to create viewer user first)
      cy.get('[data-cy="staff-menu"]').click()
      cy.get('[data-cy="logout"]').click()
      
      // This test would need a viewer user to be seeded
      // Keeping the structure for completeness
      cy.visit('/staff/login')
      cy.get('input[name="email"]').type('viewer@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="new-case-btn"]').should('not.exist')
    })

    it('should show different options for different roles', () => {
      cy.get('[data-cy="cases-menu"]').click()
      cy.get('[data-cy="role-based-actions"]').should('be.visible')
      cy.get('[data-cy="admin-only-section"]').should('be.visible')
    })
  })

  describe('Case Filtering and Search', () => {
    beforeEach(() => {
      // Create multiple test cases
      const cases = [
        { type: 'FCRA', status: 'Open', client: '1' },
        { type: 'FDCPA', status: 'Closed', client: '1' },
        { type: 'TCPA', status: 'In Progress', client: '1' }
      ]
      
      cases.forEach(caseData => {
        cy.get('[data-cy="cases-menu"]').click()
        cy.get('[data-cy="new-case-btn"]').click()
        cy.get('[data-cy="case-client-select"]').select(caseData.client)
        cy.get('[data