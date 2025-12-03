/// <reference types="cypress" />

describe('Client Management - CRUD Operations', () => {
  beforeEach(() => {
    cy.visit('/staff/login')
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('testpass123')
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
  })

  describe('Client Listing and Search - Happy Path Tests', () => {
    it('should display clients list page with navigation menu', () => {
      cy.visit('/dashboard/clients')
      cy.url().should('include', '/dashboard/clients')
      cy.get('h1').should('contain.text', 'Clients')
      cy.get('[data-cy="clients-table"]').should('be.visible')
      cy.get('[data-cy="add-client-btn"]').should('be.visible')
    })

    it('should display client table headers correctly', () => {
      cy.visit('/dashboard/clients')
      cy.get('table thead th').should('contain.text', 'Name')
      cy.get('table thead th').should('contain.text', 'Email')
      cy.get('table thead th').should('contain.text', 'Phone')
      cy.get('table thead th').should('contain.text', 'Created')
      cy.get('table thead th').should('contain.text', 'Actions')
    })

    it('should show empty state when no clients exist', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="empty-state"]').should('be.visible')
      cy.get('[data-cy="empty-state"]').should('contain.text', 'No clients found')
      cy.get('[data-cy="add-first-client-btn"]').should('be.visible')
    })

    it('should display client data in table rows when clients exist', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="client-row"]').should('have.length.at.least', 1)
      cy.get('[data-cy="client-row"]').first().within(() => {
        cy.get('[data-cy="client-name"]').should('not.be.empty')
        cy.get('[data-cy="client-email"]').should('not.be.empty')
        cy.get('[data-cy="client-phone"]').should('not.be.empty')
      })
    })

    it('should navigate to client details when clicking client name', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="client-name"]').first().click()
      cy.url().should('include', '/dashboard/clients/')
      cy.get('h1').should('contain.text', 'Client Details')
    })

    it('should display client statistics correctly', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="total-clients-stat"]').should('be.visible')
      cy.get('[data-cy="active-cases-stat"]').should('be.visible')
      cy.get('[data-cy="new-this-month-stat"]').should('be.visible')
    })

    it('should show pagination when more than 25 clients', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="pagination"]').should('be.visible')
      cy.get('[data-cy="page-info"]').should('contain.text', 'of')
      cy.get('[data-cy="next-page"]').should('be.visible')
      cy.get('[data-cy="prev-page"]').should('be.visible')
    })

    it('should navigate through pagination pages', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="next-page"]').click()
      cy.get('[data-cy="page-info"]').should('contain.text', 'Page 2')
      cy.get('[data-cy="prev-page"]').click()
      cy.get('[data-cy="page-info"]').should('contain.text', 'Page 1')
    })

    it('should search clients by name successfully', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').type('John')
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="client-row"]').should('have.length.at.least', 1)
      cy.get('[data-cy="search-results-count"]').should('contain.text', 'results found')
    })

    it('should search clients by email successfully', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').type('john@example.com')
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="client-row"]').should('have.length.at.least', 1)
      cy.get('[data-cy="client-email"]').should('contain.text', 'john@example.com')
    })

    it('should search clients by phone number successfully', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').type('555-123-4567')
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="client-row"]').should('have.length.at.least', 1)
      cy.get('[data-cy="client-phone"]').should('contain.text', '555-123-4567')
    })
  })

  describe('Client Search - Negative Tests', () => {
    it('should show no results for non-existent client search', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').type('NonExistentClient123')
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="no-results"]').should('be.visible')
      cy.get('[data-cy="no-results"]').should('contain.text', 'No clients found matching')
      cy.get('[data-cy="clear-search-btn"]').should('be.visible')
    })

    it('should handle empty search gracefully', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').clear()
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="client-row"]').should('have.length.at.least', 1)
      cy.get('[data-cy="search-results-count"]').should('not.exist')
    })

    it('should handle special characters in search', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').type('!@#$%^&*()')
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="no-results"]').should('be.visible')
      cy.url().should('include', '/dashboard/clients')
    })

    it('should handle very long search terms', () => {
      cy.visit('/dashboard/clients')
      const longSearch = 'a'.repeat(255)
      cy.get('[data-cy="search-input"]').type(longSearch)
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="no-results"]').should('be.visible')
      cy.get('[data-cy="search-input"]').should('have.value', longSearch)
    })

    it('should handle SQL injection attempts in search', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').type("'; DROP TABLE clients; --")
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="no-results"]').should('be.visible')
      cy.url().should('include', '/dashboard/clients')
    })

    it('should handle XSS attempts in search', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').type('<script>alert("xss")</script>')
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="no-results"]').should('be.visible')
      cy.on('window:alert', (str) => {
        throw new Error('XSS vulnerability detected')
      })
    })

    it('should handle unicode characters in search', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').type('José María')
      cy.get('[data-cy="search-btn"]').click()
      cy.get('[data-cy="no-results"]').should('be.visible')
      cy.get('[data-cy="search-input"]').should('have.value', 'José María')
    })

    it('should preserve search term after page refresh', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="search-input"]').type('John')
      cy.get('[data-cy="search-btn"]').click()
      cy.reload()
      cy.get('[data-cy="search-input"]').should('have.value', 'John')
    })
  })

  describe('Client Creation - Happy Path Tests', () => {
    it('should open add client modal when clicking add button', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="client-modal"]').should('be.visible')
      cy.get('[data-cy="modal-title"]').should('contain.text', 'Add New Client')
      cy.get('[data-cy="client-form"]').should('be.visible')
    })

    it('should create client with all required fields', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').type('John')
      cy.get('[data-cy="last-name-input"]').type('Doe')
      cy.get('[data-cy="email-input"]').type('john.doe@example.com')
      cy.get('[data-cy="phone-input"]').type('555-123-4567')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="success-message"]').should('contain.text', 'Client created successfully')
      cy.get('[data-cy="client-modal"]').should('not.exist')
      cy.get('[data-cy="client-name"]').should('contain.text', 'John Doe')
    })

    it('should create client with all optional fields filled', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').type('Jane')
      cy.get('[data-cy="last-name-input"]').type('Smith')
      cy.get('[data-cy="email-input"]').type('jane.smith@example.com')
      cy.get('[data-cy="phone-input"]').type('555-987-6543')
      cy.get('[data-cy="address-input"]').type('123 Main St')
      cy.get('[data-cy="city-input"]').type('Los Angeles')
      cy.get('[data-cy="state-select"]').select('CA')
      cy.get('[data-cy="zip-input"]').type('90210')
      cy.get('[data-cy="dob-input"]').type('1985-01-15')
      cy.get('[data-cy="ssn-input"]').type('1234')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="success-message"]').should('contain.text', 'Client created successfully')
    })

    it('should auto-format phone number during entry', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="phone-input"]').type('5551234567')
      cy.get('[data-cy="phone-input"]').should('have.value', '(555) 123-4567')
    })

    it('should validate email format during entry', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="email-input"]').type('valid@example.com')
      cy.get('[data-cy="email-validation"]').should('contain.text', 'Valid email')
      cy.get('[data-cy="email-validation"]').should('have.class', 'success')
    })

    it('should save form data as draft while typing', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').type('Draft')
      cy.get('[data-cy="last-name-input"]').type('Client')
      cy.get('[data-cy="close-modal-btn"]').click()
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').should('have.value', 'Draft')
      cy.get('[data-cy="last-name-input"]').should('have.value', 'Client')
    })
  })

  describe('Client Creation - Validation Tests', () => {
    it('should require first name field', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="last-name-input"]').type('Doe')
      cy.get('[data-cy="email-input"]').type('john@example.com')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="first-name-error"]').should('contain.text', 'First name is required')
      cy.get('[data-cy="first-name-input"]').should('have.class', 'error')
    })

    it('should require last name field', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').type('John')
      cy.get('[data-cy="email-input"]').type('john@example.com')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="last-name-error"]').should('contain.text', 'Last name is required')
      cy.get('[data-cy="last-name-input"]').should('have.class', 'error')
    })

    it('should require email field', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').type('John')
      cy.get('[data-cy="last-name-input"]').type('Doe')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="email-error"]').should('contain.text', 'Email is required')
      cy.get('[data-cy="email-input"]').should('have.class', 'error')
    })

    it('should validate email format', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="email-input"]').type('invalid-email')
      cy.get('[data-cy="first-name-input"]').click()
      cy.get('[data-cy="email-error"]').should('contain.text', 'Please enter a valid email')
      cy.get('[data-cy="email-input"]').should('have.class', 'error')
    })

    it('should validate phone number format', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="phone-input"]').type('123')
      cy.get('[data-cy="first-name-input"]').click()
      cy.get('[data-cy="phone-error"]').should('contain.text', 'Please enter a valid phone number')
      cy.get('[data-cy="phone-input"]').should('have.class', 'error')
    })

    it('should validate SSN last 4 digits format', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="ssn-input"]').type('12345')
      cy.get('[data-cy="first-name-input"]').click()
      cy.get('[data-cy="ssn-error"]').should('contain.text', 'Enter last 4 digits only')
      cy.get('[data-cy="ssn-input"]').should('have.class', 'error')
    })

    it('should validate zip code format', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="zip-input"]').type('123')
      cy.get('[data-cy="first-name-input"]').click()
      cy.get('[data-cy="zip-error"]').should('contain.text', 'Please enter a valid zip code')
      cy.get('[data-cy="zip-input"]').should('have.class', 'error')
    })

    it('should validate date of birth format', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="dob-input"]').type('invalid-date')
      cy.get('[data-cy="first-name-input"]').click()
      cy.get('[data-cy="dob-error"]').should('contain.text', 'Please enter a valid date')
      cy.get('[data-cy="dob-input"]').should('have.class', 'error')
    })

    it('should prevent future date of birth', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      const futureDate = new Date()
      futureDate.setFullYear(futureDate.getFullYear() + 1)
      cy.get('[data-cy="dob-input"]').type(futureDate.toISOString().split('T')[0])
      cy.get('[data-cy="first-name-input"]').click()
      cy.get('[data-cy="dob-error"]').should('contain.text', 'Date of birth cannot be in the future')
    })

    it('should validate minimum age requirement', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      const recentDate = new Date()
      recentDate.setFullYear(recentDate.getFullYear() - 10)
      cy.get('[data-cy="dob-input"]').type(recentDate.toISOString().split('T')[0])
      cy.get('[data-cy="first-name-input"]').click()
      cy.get('[data-cy="dob-error"]').should('contain.text', 'Client must be at least 18 years old')
    })

    it('should check for duplicate email addresses', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').type('Duplicate')
      cy.get('[data-cy="last-name-input"]').type('Email')
      cy.get('[data-cy="email-input"]').type('johndoe@test.com')
      cy.get('[data-cy="phone-input"]').type('555-999-8888')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="error-message"]').should('contain.text', 'Email address already exists')
      cy.get('[data-cy="email-input"]').should('have.class', 'error')
    })
  })

  describe('Client Creation - Edge Case Tests', () => {
    it('should handle very long name fields', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      const longName = 'a'.repeat(100)
      cy.get('[data-cy="first-name-input"]').type(longName)
      cy.get('[data-cy="first-name-input"]').should('have.value', longName.substring(0, 50))
      cy.get('[data-cy="first-name-error"]').should('contain.text', 'Maximum 50 characters')
    })

    it('should handle special characters in name fields', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').type("O'Connor-Smith")
      cy.get('[data-cy="last-name-input"]').type('José María')
      cy.get('[data-cy="email-input"]').type('jose@example.com')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="success-message"]').should('be.visible')
    })

    it('should handle international phone numbers', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').type('International')
      cy.get('[data-cy="last-name-input"]').type('Client')
      cy.get('[data-cy="email-input"]').type('intl@example.com')
      cy.get('[data-cy="phone-input"]').type('+44 20 7946 0958')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="success-message"]').should('be.visible')
    })

    it('should handle network timeout during save', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.intercept('POST', '/api/clients', { delay: 30000 }).as('slowSave')
      cy.get('[data-cy="first-name-input"]').type('Timeout')
      cy.get('[data-cy="last-name-input"]').type('Test')
      cy.get('[data-cy="email-input"]').type('timeout@example.com')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="save-client-btn"]').should('be.disabled')
      cy.get('[data-cy="loading-spinner"]').should('be.visible')
    })

    it('should handle server error during save', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.intercept('POST', '/api/clients', { statusCode: 500 }).as('serverError')
      cy.get('[data-cy="first-name-input"]').type('Server')
      cy.get('[data-cy="last-name-input"]').type('Error')
      cy.get('[data-cy="email-input"]').type('error@example.com')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="error-message"]').should('contain.text', 'Server error occurred')
      cy.get('[data-cy="save-client-btn"]').should('not.be.disabled')
    })

    it('should preserve form data after server error', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="add-client-btn"]').click()
      cy.intercept('POST', '/api/clients', { statusCode: 500 }).as('serverError')
      cy.get('[data-cy="first-name-input"]').type('Preserved')
      cy.get('[data-cy="last-name-input"]').type('Data')
      cy.get('[data-cy="email-input"]').type('preserved@example.com')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="first-name-input"]').should('have.value', 'Preserved')
      cy.get('[data-cy="last-name-input"]').should('have.value', 'Data')
      cy.get('[data-cy="email-input"]').should('have.value', 'preserved@example.com')
    })
  })

  describe('Client Update - Happy Path Tests', () => {
    it('should open edit modal when clicking edit button', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="client-modal"]').should('be.visible')
      cy.get('[data-cy="modal-title"]').should('contain.text', 'Edit Client')
      cy.get('[data-cy="client-form"]').should('be.visible')
    })

    it('should pre-populate form with existing client data', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="first-name-input"]').should('have.value', 'John')
      cy.get('[data-cy="last-name-input"]').should('have.value', 'Doe')
      cy.get('[data-cy="email-input"]').should('have.value', 'johndoe@test.com')
      cy.get('[data-cy="phone-input"]').should('not.be.empty')
    })

    it('should update client with modified data', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="first-name-input"]').clear().type('Johnny')
      cy.get('[data-cy="phone-input"]').clear().type('555-111-2222')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="success-message"]').should('contain.text', 'Client updated successfully')
      cy.get('[data-cy="client-name"]').should('contain.text', 'Johnny Doe')
    })

    it('should update only changed fields', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="address-input"]').clear().type('456 New Street')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="success-message"]').should('contain.text', 'Client updated successfully')
      cy.get('[data-cy="client-modal"]').should('not.exist')
    })

    it('should show confirmation for major changes', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="email-input"]').clear().type('newemail@example.com')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="confirm-modal"]').should('be.visible')
      cy.get('[data-cy="confirm-message"]').should('contain.text', 'Changing email address')
      cy.get('[data-cy="confirm-save-btn"]').click()
      cy.get('[data-cy="success-message"]').should('be.visible')
    })

    it('should track modification history', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="first-name-input"]').clear().type('Modified')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="view-client-btn"]').first().click()
      cy.get('[data-cy="history-tab"]').click()
      cy.get('[data-cy="modification-entry"]').should('contain.text', 'First name changed')
      cy.get('[data-cy="modification-entry"]').should('contain.text', 'test@example.com')
    })
  })

  describe('Client Update - Validation Tests', () => {
    it('should validate required fields during update', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="first-name-input"]').clear()
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="first-name-error"]').should('contain.text', 'First name is required')
      cy.get('[data-cy="client-modal"]').should('be.visible')
    })

    it('should check for duplicate email during update', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="email-input"]').clear().type('existing@example.com')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="email-error"]').should('contain.text', 'Email address already exists')
      cy.get('[data-cy="email-input"]').should('have.class', 'error')
    })

    it('should validate email format during update', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="email-input"]').clear().type('invalid.email')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="email-error"]').should('contain.text', 'Please enter a valid email')
    })

    it('should validate phone format during update', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="phone-input"]').clear().type('invalid')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="phone-error"]').should('contain.text', 'Please enter a valid phone number')
    })

    it('should prevent updating to invalid SSN format', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[data-cy="ssn-input"]').clear().type('12345')
      cy.get('[data-cy="save-client-btn"]').click()
      cy.get('[data-cy="ssn-error"]').should('contain.text', 'Enter last 4 digits only')
    })

    it('should handle concurrent updates gracefully', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="edit-client-btn"]').first().click()
      cy.get('[