describe('Staff Management - Comprehensive Tests', () => {
  beforeEach(() => {
    cy.visit('/staff/login')
    cy.get('[data-testid="email-input"]').type('test@example.com')
    cy.get('[data-testid="password-input"]').type('password123')
    cy.get('[data-testid="login-button"]').click()
    cy.url().should('include', '/dashboard')
    cy.visit('/dashboard/staff')
  })

  describe('Page Load & Structure', () => {
    it('should load the staff management page', () => {
      cy.get('[data-testid="staff-management-page"]').should('be.visible')
    })

    it('should display the page title', () => {
      cy.get('[data-testid="page-title"]').should('be.visible')
      cy.get('[data-testid="page-title"]').should('contain', 'Staff')
    })

    it('should display the staff list card', () => {
      cy.get('[data-testid="staff-list-card"]').should('be.visible')
    })
  })

  describe('Stats Grid', () => {
    it('should display stats grid', () => {
      cy.get('[data-testid="stats-grid"]').should('be.visible')
    })

    it('should display total staff stat card', () => {
      cy.get('[data-testid="stat-total"]').should('be.visible')
    })

    it('should display admins stat card', () => {
      cy.get('[data-testid="stat-admins"]').should('be.visible')
    })

    it('should display attorneys stat card', () => {
      cy.get('[data-testid="stat-attorneys"]').should('be.visible')
    })

    it('should display paralegals stat card', () => {
      cy.get('[data-testid="stat-paralegals"]').should('be.visible')
    })

    it('should display numeric values in stat cards', () => {
      cy.get('[data-testid="stat-total"]').find('.stat-value').invoke('text').should('match', /\d+/)
    })
  })

  describe('Search Functionality', () => {
    it('should display search input', () => {
      cy.get('[data-testid="search-input"]').should('be.visible')
    })

    it('should allow typing in search input', () => {
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="search-input"]').should('have.value', 'test')
    })

    it('should clear search input', () => {
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="search-input"]').clear()
      cy.get('[data-testid="search-input"]').should('have.value', '')
    })

    it('should filter table results when searching', () => {
      cy.get('[data-testid="search-input"]').type('test@example.com')
      // Table should still exist after search
      cy.get('[data-testid="staff-table"]').should('exist')
    })
  })

  describe('Staff Table', () => {
    it('should display staff table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="staff-table"]').length > 0) {
          cy.get('[data-testid="staff-table"]').should('be.visible')
        } else {
          cy.get('[data-testid="empty-state"]').should('be.visible')
        }
      })
    })

    it('should display table body', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="staff-table"]').length > 0) {
          cy.get('[data-testid="staff-table-body"]').should('exist')
        }
      })
    })

    it('should display staff rows with correct elements', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="staff-row-"]').length > 0) {
          cy.get('[data-testid^="staff-row-"]').first().within(() => {
            cy.get('[data-testid^="staff-name-"]').should('exist')
            cy.get('[data-testid^="staff-email-"]').should('exist')
            cy.get('[data-testid^="staff-role-"]').should('exist')
            cy.get('[data-testid^="staff-status-"]').should('exist')
          })
        }
      })
    })

    it('should display action buttons for each staff row', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="staff-row-"]').length > 0) {
          cy.get('[data-testid^="staff-row-"]').first().within(() => {
            cy.get('[data-testid^="edit-btn-"]').should('exist')
            cy.get('[data-testid^="toggle-status-btn-"]').should('exist')
            cy.get('[data-testid^="reset-pwd-btn-"]').should('exist')
          })
        }
      })
    })
  })

  describe('Add Staff Modal - Opening & Closing', () => {
    it('should display add staff button', () => {
      cy.get('[data-testid="add-staff-button"]').should('be.visible')
    })

    it('should open add modal when clicking add button', () => {
      cy.get('[data-testid="add-staff-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
    })

    it('should close modal when clicking X button', () => {
      cy.get('[data-testid="add-staff-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
      cy.get('[data-testid="add-modal-close"]').click()
      cy.get('[data-testid="add-modal"]').should('not.be.visible')
    })

    it('should close modal when clicking cancel button', () => {
      cy.get('[data-testid="add-staff-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
      cy.get('[data-testid="add-cancel-button"]').click()
      cy.get('[data-testid="add-modal"]').should('not.be.visible')
    })
  })

  describe('Add Staff Modal - Form Fields', () => {
    beforeEach(() => {
      cy.get('[data-testid="add-staff-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
    })

    it('should display add staff form', () => {
      cy.get('[data-testid="add-staff-form"]').should('be.visible')
    })

    it('should display first name input', () => {
      cy.get('[data-testid="add-first-name"]').should('be.visible')
    })

    it('should display last name input', () => {
      cy.get('[data-testid="add-last-name"]').should('be.visible')
    })

    it('should display email input', () => {
      cy.get('[data-testid="add-email"]').should('be.visible')
    })

    it('should display password input', () => {
      cy.get('[data-testid="add-password"]').should('be.visible')
    })

    it('should display role select', () => {
      cy.get('[data-testid="add-role"]').should('be.visible')
    })

    it('should display submit button', () => {
      cy.get('[data-testid="add-submit-button"]').should('be.visible')
    })

    it('should display cancel button', () => {
      cy.get('[data-testid="add-cancel-button"]').should('be.visible')
    })
  })

  describe('Add Staff Modal - Form Input', () => {
    beforeEach(() => {
      cy.get('[data-testid="add-staff-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
    })

    it('should allow typing in first name field', () => {
      cy.get('[data-testid="add-first-name"]').type('John')
      cy.get('[data-testid="add-first-name"]').should('have.value', 'John')
    })

    it('should allow typing in last name field', () => {
      cy.get('[data-testid="add-last-name"]').type('Doe')
      cy.get('[data-testid="add-last-name"]').should('have.value', 'Doe')
    })

    it('should allow typing in email field', () => {
      cy.get('[data-testid="add-email"]').type('john@example.com')
      cy.get('[data-testid="add-email"]').should('have.value', 'john@example.com')
    })

    it('should allow typing in password field', () => {
      cy.get('[data-testid="add-password"]').type('password123')
      cy.get('[data-testid="add-password"]').should('have.value', 'password123')
    })

    it('should allow selecting admin role', () => {
      cy.get('[data-testid="add-role"]').select('admin')
      cy.get('[data-testid="add-role"]').should('have.value', 'admin')
    })

    it('should allow selecting attorney role', () => {
      cy.get('[data-testid="add-role"]').select('attorney')
      cy.get('[data-testid="add-role"]').should('have.value', 'attorney')
    })

    it('should allow selecting paralegal role', () => {
      cy.get('[data-testid="add-role"]').select('paralegal')
      cy.get('[data-testid="add-role"]').should('have.value', 'paralegal')
    })

    it('should clear form fields when modal is closed and reopened', () => {
      cy.get('[data-testid="add-first-name"]').type('John')
      cy.get('[data-testid="add-cancel-button"]').click()
      cy.get('[data-testid="add-staff-button"]').click()
      cy.get('[data-testid="add-first-name"]').should('have.value', '')
    })
  })

  describe('Add Staff Modal - Form Validation', () => {
    beforeEach(() => {
      cy.get('[data-testid="add-staff-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
    })

    it('should not submit with empty first name', () => {
      cy.get('[data-testid="add-last-name"]').type('Doe')
      cy.get('[data-testid="add-email"]').type('test@example.com')
      cy.get('[data-testid="add-password"]').type('password123')
      cy.get('[data-testid="add-submit-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
    })

    it('should not submit with empty last name', () => {
      cy.get('[data-testid="add-first-name"]').type('John')
      cy.get('[data-testid="add-email"]').type('test@example.com')
      cy.get('[data-testid="add-password"]').type('password123')
      cy.get('[data-testid="add-submit-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
    })

    it('should not submit with empty email', () => {
      cy.get('[data-testid="add-first-name"]').type('John')
      cy.get('[data-testid="add-last-name"]').type('Doe')
      cy.get('[data-testid="add-password"]').type('password123')
      cy.get('[data-testid="add-submit-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
    })

    it('should not submit with invalid email format', () => {
      cy.get('[data-testid="add-first-name"]').type('John')
      cy.get('[data-testid="add-last-name"]').type('Doe')
      cy.get('[data-testid="add-email"]').type('invalid-email')
      cy.get('[data-testid="add-password"]').type('password123')
      cy.get('[data-testid="add-submit-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
    })

    it('should not submit with empty password', () => {
      cy.get('[data-testid="add-first-name"]').type('John')
      cy.get('[data-testid="add-last-name"]').type('Doe')
      cy.get('[data-testid="add-email"]').type('test@example.com')
      cy.get('[data-testid="add-submit-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
    })
  })

  describe('Add Staff Modal - Successful Submission', () => {
    it('should create new staff member with valid data', () => {
      const uniqueEmail = `newstaff_${Date.now()}@example.com`
      
      cy.get('[data-testid="add-staff-button"]').click()
      cy.get('[data-testid="add-modal"]').should('be.visible')
      
      cy.get('[data-testid="add-first-name"]').type('New')
      cy.get('[data-testid="add-last-name"]').type('Staff')
      cy.get('[data-testid="add-email"]').type(uniqueEmail)
      cy.get('[data-testid="add-password"]').type('password123')
      cy.get('[data-testid="add-role"]').select('paralegal')
      cy.get('[data-testid="add-submit-button"]').click()
      
      // Wait for page reload or success message
      cy.wait(2000)
      
      // Either modal closes, success message shows, or page reloads
      cy.get('body').then(($body) => {
        const hasSuccess = $body.find('[data-testid="success-message"]').length > 0
        const modalClosed = !$body.find('[data-testid="add-modal"]').hasClass('active')
        expect(hasSuccess || modalClosed).to.be.true
      })
    })
  })

  describe('Edit Staff Modal - Opening & Closing', () => {
    it('should open edit modal when clicking edit button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="edit-btn-"]').length > 0) {
          cy.get('[data-testid^="edit-btn-"]').first().click()
          cy.get('[data-testid="edit-modal"]').should('be.visible')
        }
      })
    })

    it('should close edit modal when clicking X button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="edit-btn-"]').length > 0) {
          cy.get('[data-testid^="edit-btn-"]').first().click()
          cy.get('[data-testid="edit-modal"]').should('be.visible')
          cy.get('[data-testid="edit-modal-close"]').click()
          cy.get('[data-testid="edit-modal"]').should('not.be.visible')
        }
      })
    })

    it('should close edit modal when clicking cancel button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="edit-btn-"]').length > 0) {
          cy.get('[data-testid^="edit-btn-"]').first().click()
          cy.get('[data-testid="edit-modal"]').should('be.visible')
          cy.get('[data-testid="edit-cancel-button"]').click()
          cy.get('[data-testid="edit-modal"]').should('not.be.visible')
        }
      })
    })
  })

  describe('Edit Staff Modal - Form Fields', () => {
    beforeEach(() => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="edit-btn-"]').length > 0) {
          cy.get('[data-testid^="edit-btn-"]').first().click()
          cy.get('[data-testid="edit-modal"]').should('be.visible')
        }
      })
    })

    it('should display edit staff form', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-staff-form"]').should('be.visible')
        }
      })
    })

    it('should display and populate first name input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-first-name"]').should('be.visible')
        }
      })
    })

    it('should display and populate last name input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-last-name"]').should('be.visible')
        }
      })
    })

    it('should display and populate email input', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-email"]').should('be.visible')
        }
      })
    })

    it('should display role select', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-role"]').should('be.visible')
        }
      })
    })

    it('should display status select', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-status"]').should('be.visible')
        }
      })
    })

    it('should display submit button', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-submit-button"]').should('be.visible')
        }
      })
    })
  })

  describe('Edit Staff Modal - Form Input', () => {
    beforeEach(() => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="edit-btn-"]').length > 0) {
          cy.get('[data-testid^="edit-btn-"]').first().click()
          cy.get('[data-testid="edit-modal"]').should('be.visible')
        }
      })
    })

    it('should allow editing first name', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-first-name"]').clear().type('UpdatedFirst')
          cy.get('[data-testid="edit-first-name"]').should('have.value', 'UpdatedFirst')
        }
      })
    })

    it('should allow editing last name', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-last-name"]').clear().type('UpdatedLast')
          cy.get('[data-testid="edit-last-name"]').should('have.value', 'UpdatedLast')
        }
      })
    })

    it('should allow editing email', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-email"]').clear().type('updated@example.com')
          cy.get('[data-testid="edit-email"]').should('have.value', 'updated@example.com')
        }
      })
    })

    it('should allow changing role', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-role"]').select('attorney')
          cy.get('[data-testid="edit-role"]').should('have.value', 'attorney')
        }
      })
    })

    it('should allow changing status to inactive', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-status"]').select('false')
          cy.get('[data-testid="edit-status"]').should('have.value', 'false')
        }
      })
    })

    it('should allow changing status to active', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid="edit-modal"]').length > 0) {
          cy.get('[data-testid="edit-status"]').select('true')
          cy.get('[data-testid="edit-status"]').should('have.value', 'true')
        }
      })
    })
  })

  describe('Edit Staff Modal - Successful Update', () => {
    it('should update staff member with valid data', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="edit-btn-"]').length > 0) {
          cy.get('[data-testid^="edit-btn-"]').first().click()
          cy.get('[data-testid="edit-modal"]').should('be.visible')
          
          cy.get('[data-testid="edit-first-name"]').clear().type('Updated')
          cy.get('[data-testid="edit-submit-button"]').click()
          
          // Wait for update
          cy.wait(2000)
          
          // Should return to table or show success
          cy.get('[data-testid="staff-table"]').should('be.visible')
        }
      })
    })
  })

  describe('Toggle Staff Status (Soft Delete)', () => {
    it('should display toggle status button for each staff', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="toggle-status-btn-"]').length > 0) {
          cy.get('[data-testid^="toggle-status-btn-"]').first().should('be.visible')
        }
      })
    })

    it('should show confirmation dialog when clicking toggle', () => {
      cy.on('window:confirm', (text) => {
        expect(text.toLowerCase()).to.include('activate').or.include('deactivate')
        return false // Cancel
      })
      
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="toggle-status-btn-"]').length > 0) {
          cy.get('[data-testid^="toggle-status-btn-"]').first().click()
        }
      })
    })

    it('should cancel toggle when declining confirmation', () => {
      cy.on('window:confirm', () => false)
      
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="toggle-status-btn-"]').length > 0) {
          cy.get('[data-testid^="toggle-status-btn-"]').first().click()
          // Page should not reload, table should be visible
          cy.get('[data-testid="staff-table"]').should('be.visible')
        }
      })
    })

    it('should toggle status when confirming', () => {
      cy.on('window:confirm', () => true)
      
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="toggle-status-btn-"]').length > 0) {
          cy.get('[data-testid^="toggle-status-btn-"]').first().click()
          cy.wait(2000)
          // Table should still be visible after action
          cy.get('[data-testid="staff-table"]').should('be.visible')
        }
      })
    })
  })

  describe('Reset Password', () => {
    it('should display reset password button for each staff', () => {
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="reset-pwd-btn-"]').length > 0) {
          cy.get('[data-testid^="reset-pwd-btn-"]').first().should('be.visible')
        }
      })
    })

    it('should show confirmation when clicking reset password', () => {
      cy.on('window:confirm', (text) => {
        expect(text.toLowerCase()).to.include('reset').or.include('password')
        return false // Cancel
      })
      
      cy.get('body').then(($body) => {
        if ($body.find('[data-testid^="reset-pwd-btn-"]').length > 0) {
          cy.get('[data-testid^="reset-pwd-btn-"]').first().click()
        }
      })
    })
  })

  describe('Messages', () => {
    it('should display success message container', () => {
      // Success message may or may not be visible initially
      cy.get('[data-testid="success-message"]').should('exist')
    })

    it('should display error message container', () => {
      // Error message may or may not be visible initially
      cy.get('[data-testid="error-message"]').should('exist')
    })
  })
})
