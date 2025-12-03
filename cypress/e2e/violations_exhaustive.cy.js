/// <reference types="cypress" />

describe('FCRA Violations Management', () => {
  beforeEach(() => {
    cy.visit('/staff/login')
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('testpass123')
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
  })

  describe('Violation CRUD Operations - Happy Path', () => {
    it('should display violations list page', () => {
      cy.visit('/violations')
      cy.get('h1').should('contain', 'Violations')
      cy.url().should('include', '/violations')
      cy.get('[data-cy="violations-table"]').should('be.visible')
      cy.get('[data-cy="add-violation-btn"]').should('be.visible')
    })

    it('should create new violation with all required fields', () => {
      cy.visit('/violations/new')
      cy.get('[data-cy="violation-form"]').should('be.visible')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Failure to conduct reasonable investigation within 30 days')
      cy.get('input[name="statute"]').type('15 USC 1681i(a)(1)(A)')
      cy.get('input[name="damages_estimate"]').type('2500.00')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/violations')
      cy.get('.alert-success').should('contain', 'Violation created successfully')
      cy.get('[data-cy="violations-table"]').should('contain', 'FCRA_Section_611')
    })

    it('should edit existing violation successfully', () => {
      cy.visit('/violations')
      cy.get('[data-cy="edit-violation-btn"]').first().click()
      cy.get('[data-cy="violation-form"]').should('be.visible')
      cy.get('textarea[name="description"]').clear().type('Updated violation description with more details')
      cy.get('input[name="damages_estimate"]').clear().type('3500.00')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/violations')
      cy.get('.alert-success').should('contain', 'Violation updated successfully')
      cy.get('[data-cy="violations-table"]').should('contain', 'Updated violation description')
    })

    it('should view violation details page', () => {
      cy.visit('/violations')
      cy.get('[data-cy="view-violation-btn"]').first().click()
      cy.get('[data-cy="violation-details"]').should('be.visible')
      cy.get('[data-cy="violation-type"]').should('not.be.empty')
      cy.get('[data-cy="violation-description"]').should('not.be.empty')
      cy.get('[data-cy="violation-statute"]').should('not.be.empty')
      cy.get('[data-cy="violation-damages"]').should('not.be.empty')
      cy.get('[data-cy="back-to-violations"]').should('be.visible')
    })

    it('should delete violation with confirmation', () => {
      cy.visit('/violations')
      cy.get('[data-cy="delete-violation-btn"]').first().click()
      cy.get('[data-cy="confirm-delete-modal"]').should('be.visible')
      cy.get('[data-cy="confirm-delete-yes"]').click()
      cy.get('.alert-success').should('contain', 'Violation deleted successfully')
      cy.url().should('include', '/violations')
    })

    it('should filter violations by violation type', () => {
      cy.visit('/violations')
      cy.get('[data-cy="filter-violation-type"]').select('FCRA_Section_611')
      cy.get('[data-cy="apply-filters-btn"]').click()
      cy.get('[data-cy="violations-table"] tbody tr').should('have.length.at.least', 1)
      cy.get('[data-cy="violations-table"]').should('contain', 'FCRA_Section_611')
      cy.get('[data-cy="clear-filters-btn"]').click()
    })

    it('should filter violations by case', () => {
      cy.visit('/violations')
      cy.get('[data-cy="filter-case-id"]').type('1')
      cy.get('[data-cy="apply-filters-btn"]').click()
      cy.get('[data-cy="violations-table"] tbody tr').should('have.length.at.least', 1)
      cy.get('[data-cy="clear-filters-btn"]').should('be.visible')
    })

    it('should paginate through violations list', () => {
      cy.visit('/violations')
      cy.get('[data-cy="violations-table"] tbody tr').should('have.length.at.least', 1)
      cy.get('[data-cy="next-page-btn"]').should('exist')
      cy.get('[data-cy="page-info"]').should('contain', 'Page')
    })

    it('should sort violations by different columns', () => {
      cy.visit('/violations')
      cy.get('[data-cy="sort-violation-type"]').click()
      cy.url().should('include', 'sort=violation_type')
      cy.get('[data-cy="sort-damages"]').click()
      cy.url().should('include', 'sort=damages_estimate')
      cy.get('[data-cy="sort-created"]').click()
      cy.url().should('include', 'sort=created_at')
    })

    it('should export violations to CSV', () => {
      cy.visit('/violations')
      cy.get('[data-cy="export-violations-btn"]').click()
      cy.readFile('cypress/downloads/violations.csv').should('exist')
    })
  })

  describe('Violation Form Validation - Negative Tests', () => {
    it('should show error when submitting empty violation form', () => {
      cy.visit('/violations/new')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Please fill in all required fields')
      cy.get('input[name="case_id"]').should('have.class', 'is-invalid')
      cy.get('select[name="violation_type"]').should('have.class', 'is-invalid')
      cy.get('textarea[name="description"]').should('have.class', 'is-invalid')
      cy.url().should('include', '/violations/new')
    })

    it('should validate case_id field is numeric', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('invalid_text')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Test description')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Case ID must be a valid number')
      cy.get('input[name="case_id"]').should('have.class', 'is-invalid')
    })

    it('should validate case_id exists', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('99999')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Test description')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Case not found')
      cy.get('input[name="case_id"]').should('have.class', 'is-invalid')
    })

    it('should validate description minimum length', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('a')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Description must be at least 10 characters')
      cy.get('textarea[name="description"]').should('have.class', 'is-invalid')
    })

    it('should validate description maximum length', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('a'.repeat(2001))
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Description cannot exceed 2000 characters')
      cy.get('textarea[name="description"]').should('have.class', 'is-invalid')
    })

    it('should validate damages_estimate is numeric', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Valid description text')
      cy.get('input[name="damages_estimate"]').type('invalid_amount')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Damages estimate must be a valid number')
      cy.get('input[name="damages_estimate"]').should('have.class', 'is-invalid')
    })

    it('should validate damages_estimate is positive', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Valid description text')
      cy.get('input[name="damages_estimate"]').type('-100')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Damages estimate must be positive')
      cy.get('input[name="damages_estimate"]').should('have.class', 'is-invalid')
    })

    it('should validate damages_estimate maximum value', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Valid description text')
      cy.get('input[name="damages_estimate"]').type('10000001')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Damages estimate cannot exceed $10,000,000')
      cy.get('input[name="damages_estimate"]').should('have.class', 'is-invalid')
    })

    it('should validate statute field format', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Valid description text')
      cy.get('input[name="statute"]').type('invalid statute format')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Invalid statute format')
      cy.get('input[name="statute"]').should('have.class', 'is-invalid')
    })

    it('should handle XSS attempt in description field', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('<script>alert("XSS")</script>Violation description')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-success').should('contain', 'Violation created successfully')
      cy.get('[data-cy="violations-table"]').should('not.contain', '<script>')
      cy.get('[data-cy="violations-table"]').should('contain', 'Violation description')
    })

    it('should handle SQL injection attempt in statute field', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Valid description text')
      cy.get('input[name="statute"]').type("'; DROP TABLE violations; --")
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('be.visible')
      cy.visit('/violations')
      cy.get('[data-cy="violations-table"]').should('be.visible')
    })
  })

  describe('Violation Types Management', () => {
    it('should display all available violation types', () => {
      cy.visit('/violations/new')
      cy.get('select[name="violation_type"]').click()
      cy.get('select[name="violation_type"] option').should('contain', 'FCRA_Section_611')
      cy.get('select[name="violation_type"] option').should('contain', 'FCRA_Section_613')
      cy.get('select[name="violation_type"] option').should('contain', 'FCRA_Section_615')
      cy.get('select[name="violation_type"] option').should('contain', 'FDCPA_Section_807')
      cy.get('select[name="violation_type"] option').should('contain', 'FDCPA_Section_809')
    })

    it('should validate required violation type selection', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('textarea[name="description"]').type('Valid description text')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Violation type is required')
      cy.get('select[name="violation_type"]').should('have.class', 'is-invalid')
    })

    it('should show violation type descriptions', () => {
      cy.visit('/violations/new')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('[data-cy="violation-type-description"]').should('contain', 'Procedure in case of disputed accuracy')
      cy.get('select[name="violation_type"]').select('FCRA_Section_613')
      cy.get('[data-cy="violation-type-description"]').should('contain', 'Public record information')
    })

    it('should auto-populate statute field based on violation type', () => {
      cy.visit('/violations/new')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('input[name="statute"]').should('have.value', '15 USC 1681i')
      cy.get('select[name="violation_type"]').select('FCRA_Section_613')
      cy.get('input[name="statute"]').should('have.value', '15 USC 1681k')
    })

    it('should filter violation types by statute category', () => {
      cy.visit('/violations/new')
      cy.get('[data-cy="filter-statute-category"]').select('FCRA')
      cy.get('select[name="violation_type"] option').should('contain', 'FCRA_Section_611')
      cy.get('select[name="violation_type"] option').should('not.contain', 'FDCPA_Section_807')
      cy.get('[data-cy="filter-statute-category"]').select('FDCPA')
      cy.get('select[name="violation_type"] option').should('contain', 'FDCPA_Section_807')
      cy.get('select[name="violation_type"] option').should('not.contain', 'FCRA_Section_611')
    })

    it('should show damages ranges for violation types', () => {
      cy.visit('/violations/new')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('[data-cy="damages-range"]').should('contain', '$100 - $1,000')
      cy.get('[data-cy="suggested-damages"]').should('be.visible')
    })

    it('should create custom violation type', () => {
      cy.visit('/violations/new')
      cy.get('[data-cy="add-custom-violation-type"]').click()
      cy.get('[data-cy="custom-violation-modal"]').should('be.visible')
      cy.get('input[name="custom_violation_name"]').type('Custom TCPA Violation')
      cy.get('textarea[name="custom_violation_description"]').type('Telephone Consumer Protection Act violation')
      cy.get('input[name="custom_statute"]').type('47 USC 227')
      cy.get('[data-cy="save-custom-violation"]').click()
      cy.get('select[name="violation_type"] option').should('contain', 'Custom TCPA Violation')
    })
  })

  describe('Statutes Management', () => {
    it('should display statute information correctly', () => {
      cy.visit('/violations/statutes')
      cy.get('[data-cy="statutes-list"]').should('be.visible')
      cy.get('[data-cy="statute-item"]').should('have.length.at.least', 1)
      cy.get('[data-cy="statute-code"]').should('not.be.empty')
      cy.get('[data-cy="statute-title"]').should('not.be.empty')
    })

    it('should search statutes by code', () => {
      cy.visit('/violations/statutes')
      cy.get('[data-cy="search-statutes"]').type('1681i')
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="statute-item"]').should('contain', '1681i')
      cy.get('[data-cy="clear-search"]').click()
      cy.get('[data-cy="search-statutes"]').should('have.value', '')
    })

    it('should search statutes by title', () => {
      cy.visit('/violations/statutes')
      cy.get('[data-cy="search-statutes"]').type('disputed accuracy')
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="statute-item"]').should('contain', 'disputed accuracy')
    })

    it('should view detailed statute information', () => {
      cy.visit('/violations/statutes')
      cy.get('[data-cy="view-statute-btn"]').first().click()
      cy.get('[data-cy="statute-details-modal"]').should('be.visible')
      cy.get('[data-cy="statute-full-text"]').should('not.be.empty')
      cy.get('[data-cy="statute-penalties"]').should('be.visible')
      cy.get('[data-cy="related-cases"]').should('be.visible')
      cy.get('[data-cy="close-statute-details"]').click()
    })

    it('should add new statute', () => {
      cy.visit('/violations/statutes')
      cy.get('[data-cy="add-statute-btn"]').click()
      cy.get('[data-cy="statute-form"]').should('be.visible')
      cy.get('input[name="statute_code"]').type('15 USC 1681a')
      cy.get('input[name="statute_title"]').type('Definitions; rules of construction')
      cy.get('textarea[name="statute_text"]').type('For purposes of this subchapter...')
      cy.get('select[name="statute_category"]').select('FCRA')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-success').should('contain', 'Statute added successfully')
    })

    it('should validate statute code format', () => {
      cy.visit('/violations/statutes')
      cy.get('[data-cy="add-statute-btn"]').click()
      cy.get('input[name="statute_code"]').type('invalid format')
      cy.get('input[name="statute_title"]').type('Valid title')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Invalid statute code format')
      cy.get('input[name="statute_code"]').should('have.class', 'is-invalid')
    })

    it('should check for duplicate statute codes', () => {
      cy.visit('/violations/statutes')
      cy.get('[data-cy="add-statute-btn"]').click()
      cy.get('input[name="statute_code"]').type('15 USC 1681i')
      cy.get('input[name="statute_title"]').type('Duplicate statute')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-danger').should('contain', 'Statute code already exists')
    })

    it('should edit existing statute', () => {
      cy.visit('/violations/statutes')
      cy.get('[data-cy="edit-statute-btn"]').first().click()
      cy.get('[data-cy="statute-form"]').should('be.visible')
      cy.get('textarea[name="statute_text"]').clear().type('Updated statute text with modifications')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-success').should('contain', 'Statute updated successfully')
    })

    it('should delete statute with confirmation', () => {
      cy.visit('/violations/statutes')
      cy.get('[data-cy="delete-statute-btn"]').last().click()
      cy.get('[data-cy="confirm-delete-modal"]').should('be.visible')
      cy.get('[data-cy="confirm-delete-yes"]').click()
      cy.get('.alert-success').should('contain', 'Statute deleted successfully')
    })
  })

  describe('Role-Based Access Control', () => {
    it('should allow admin full access to violations', () => {
      cy.visit('/violations')
      cy.get('[data-cy="add-violation-btn"]').should('be.visible')
      cy.get('[data-cy="edit-violation-btn"]').should('exist')
      cy.get('[data-cy="delete-violation-btn"]').should('exist')
      cy.get('[data-cy="export-violations-btn"]').should('be.visible')
    })

    it('should restrict manager access to violations', () => {
      cy.window().then((win) => {
        win.sessionStorage.setItem('staff_role', 'manager')
      })
      cy.visit('/violations')
      cy.get('[data-cy="add-violation-btn"]').should('be.visible')
      cy.get('[data-cy="edit-violation-btn"]').should('exist')
      cy.get('[data-cy="delete-violation-btn"]').should('not.exist')
      cy.get('[data-cy="export-violations-btn"]').should('be.visible')
    })

    it('should restrict staff access to violations', () => {
      cy.window().then((win) => {
        win.sessionStorage.setItem('staff_role', 'staff')
      })
      cy.visit('/violations')
      cy.get('[data-cy="add-violation-btn"]').should('be.visible')
      cy.get('[data-cy="edit-violation-btn"]').should('not.exist')
      cy.get('[data-cy="delete-violation-btn"]').should('not.exist')
      cy.get('[data-cy="export-violations-btn"]').should('not.exist')
    })

    it('should deny access to unauthorized users', () => {
      cy.clearCookies()
      cy.visit('/violations')
      cy.url().should('include', '/staff/login')
      cy.get('.alert-warning').should('contain', 'Please log in to access this page')
    })
  })

  describe('Violations State Management', () => {
    it('should handle empty violations list', () => {
      cy.intercept('GET', '/api/violations*', { violations: [], total: 0 })
      cy.visit('/violations')
      cy.get('[data-cy="empty-state"]').should('be.visible')
      cy.get('[data-cy="empty-state-message"]').should('contain', 'No violations found')
      cy.get('[data-cy="add-first-violation-btn"]').should('be.visible')
    })

    it('should handle single violation display', () => {
      cy.intercept('GET', '/api/violations*', { 
        violations: [{
          id: 1,
          case_id: 1,
          violation_type: 'FCRA_Section_611',
          description: 'Test violation',
          statute: '15 USC 1681i',
          damages_estimate: 1000
        }],
        total: 1
      })
      cy.visit('/violations')
      cy.get('[data-cy="violations-table"] tbody tr').should('have.length', 1)
      cy.get('[data-cy="pagination"]').should('not.exist')
    })

    it('should handle loading state', () => {
      cy.intercept('GET', '/api/violations*', { delay: 2000, violations: [], total: 0 })
      cy.visit('/violations')
      cy.get('[data-cy="loading-spinner"]').should('be.visible')
      cy.get('[data-cy="loading-message"]').should('contain', 'Loading violations...')
    })

    it('should handle error state', () => {
      cy.intercept('GET', '/api/violations*', { statusCode: 500 })
      cy.visit('/violations')
      cy.get('[data-cy="error-state"]').should('be.visible')
      cy.get('[data-cy="error-message"]').should('contain', 'Error loading violations')
      cy.get('[data-cy="retry-btn"]').should('be.visible')
    })

    it('should retry loading after error', () => {
      cy.intercept('GET', '/api/violations*', { statusCode: 500 }).as('failedRequest')
      cy.visit('/violations')
      cy.wait('@failedRequest')
      
      cy.intercept('GET', '/api/violations*', { violations: [], total: 0 }).as('successRequest')
      cy.get('[data-cy="retry-btn"]').click()
      cy.wait('@successRequest')
      
      cy.get('[data-cy="empty-state"]').should('be.visible')
    })
  })

  describe('Edge Cases and Error Handling', () => {
    it('should handle very long violation descriptions', () => {
      const longDescription = 'a'.repeat(2000)
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type(longDescription)
      cy.get('button[type="submit"]').click()
      cy.get('.alert-success').should('contain', 'Violation created successfully')
    })

    it('should handle unicode characters in violation fields', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Violation with unicode: 测试 🎯 €')
      cy.get('input[name="statute"]').type('15 USC 1681i § α')
      cy.get('button[type="submit"]').click()
      cy.get('.alert-success').should('contain', 'Violation created successfully')
    })

    it('should handle concurrent violation creation', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Concurrent test violation 1')
      
      cy.window().then((win) => {
        const form = win.document.querySelector('[data-cy="violation-form"]')
        form.submit()
        form.submit()
      })
      
      cy.get('.alert').should('have.length', 1)
    })

    it('should handle network timeout during violation creation', () => {
      cy.intercept('POST', '/api/violations', { delay: 10000 }).as('slowRequest')
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Test violation')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="form-loading"]').should('be.visible')
      cy.get('button[type="submit"]').should('be.disabled')
    })

    it('should handle session expiration during form submission', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('Test violation')
      
      cy.clearCookies()
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/staff/login')
      cy.get('.alert-warning').should('contain', 'Session expired')
    })

    it('should handle malformed JSON responses', () => {
      cy.intercept('GET', '/api/violations*', 'invalid json response')
      cy.visit('/violations')
      cy.get('[data-cy="error-state"]').should('be.visible')
      cy.get('[data-cy="error-message"]').should('contain', 'Invalid server response')
    })

    it('should preserve form data on validation errors', () => {
      cy.visit('/violations/new')
      cy.get('input[name="case_id"]').type('1')
      cy.get('select[name="violation_type"]').select('FCRA_Section_611')
      cy.get('textarea[name="description"]').type('a')
      cy.get('input[name="damages_estimate"]').type('1000')
      cy.get('button[type="submit"]').click()
      
      cy.get('input[name="case_id"]').should('have.value', '1')
      cy.get('select[name="violation_type"]').should('have.value', 'FCRA_Section_611')
      cy.get('input[name="damages_estimate"]').should('have.value', '1000')
    })

    it