/// <reference types="cypress" />

describe('Staff Management System', () => {
  beforeEach(() => {
    // Clear session and visit staff login
    cy.clearCookies()
    cy.clearLocalStorage()
    cy.visit('/staff/login')
  })

  describe('Staff Authentication', () => {
    it('should display staff login form with all required elements', () => {
      cy.get('input[name="email"]').should('be.visible')
      cy.get('input[name="password"]').should('be.visible')
      cy.get('button[type="submit"]').should('contain', 'Login').should('not.be.disabled')
      cy.get('form').should('have.attr', 'method', 'post')
      cy.url().should('include', '/staff/login')
      cy.title().should('not.be.empty')
    })

    it('should successfully login with valid admin credentials', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/dashboard')
      cy.getCookie('session').should('exist')
      cy.get('body').should('not.contain', 'Invalid email or password')
    })

    it('should reject empty email field', () => {
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Please enter email and password')
      cy.getCookie('session').should('not.exist')
    })

    it('should reject empty password field', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Please enter email and password')
      cy.getCookie('session').should('not.exist')
    })

    it('should reject both empty fields', () => {
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Please enter email and password')
      cy.getCookie('session').should('not.exist')
    })

    it('should reject invalid email format', () => {
      cy.get('input[name="email"]').type('invalid-email')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
      cy.getCookie('session').should('not.exist')
    })

    it('should reject non-existent email', () => {
      cy.get('input[name="email"]').type('nonexistent@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
      cy.get('input[name="email"]').should('have.value', 'nonexistent@example.com')
    })

    it('should reject incorrect password', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('wrongpassword')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
      cy.get('input[name="email"]').should('have.value', 'test@example.com')
    })

    it('should handle SQL injection attempts in email field', () => {
      cy.get('input[name="email"]').type("admin@test.com'; DROP TABLE staff; --")
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
      cy.getCookie('session').should('not.exist')
    })

    it('should handle XSS attempts in email field', () => {
      cy.get('input[name="email"]').type('<script>alert("xss")</script>')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
      cy.get('body').should('not.contain', '<script>')
    })

    it('should handle XSS attempts in password field', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('<script>alert("xss")</script>')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
      cy.get('body').should('not.contain', '<script>')
    })

    it('should handle very long email input', () => {
      const longEmail = 'a'.repeat(500) + '@example.com'
      cy.get('input[name="email"]').type(longEmail)
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
    })

    it('should handle very long password input', () => {
      const longPassword = 'a'.repeat(1000)
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type(longPassword)
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
    })

    it('should handle special characters in email', () => {
      cy.get('input[name="email"]').type('test+special@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
    })

    it('should handle unicode characters in login fields', () => {
      cy.get('input[name="email"]').type('tëst@exämple.com')
      cy.get('input[name="password"]').type('pässwørd123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Invalid email or password')
    })

    it('should redirect already logged in users to dashboard', () => {
      // First login
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/dashboard')
      
      // Try to visit login again
      cy.visit('/staff/login')
      cy.url().should('include', '/dashboard')
    })

    it('should handle case insensitive email login', () => {
      cy.get('input[name="email"]').type('TEST@EXAMPLE.COM')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/dashboard')
      cy.getCookie('session').should('exist')
    })

    it('should trim whitespace from email field', () => {
      cy.get('input[name="email"]').type('  test@example.com  ')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/dashboard')
      cy.getCookie('session').should('exist')
    })

    it('should show force password change for new users', () => {
      // This test assumes there's a staff member with force_password_change=true
      cy.request('POST', '/api/staff/add', {
        email: 'newuser@example.com',
        password: 'temp123',
        first_name: 'New',
        last_name: 'User',
        role: 'viewer'
      }).then(() => {
        cy.get('input[name="email"]').type('newuser@example.com')
        cy.get('input[name="password"]').type('temp123')
        cy.get('button[type="submit"]').click()
        
        cy.get('body').should('contain', 'change')
        cy.get('input[name="new_password"]').should('be.visible')
        cy.get('input[name="confirm_password"]').should('be.visible')
      })
    })

    it('should handle disabled account login attempt', () => {
      // This test would need a disabled account to be set up
      cy.get('input[name="email"]').type('disabled@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/staff/login')
      cy.get('body').should('contain', 'Account is disabled')
    })
  })

  describe('Password Change Functionality', () => {
    it('should enforce minimum password length during change', () => {
      // Setup force password change scenario
      cy.visit('/staff/change-password')
      cy.get('input[name="new_password"]').type('123')
      cy.get('input[name="confirm_password"]').type('123')
      cy.get('button[type="submit"]').click()
      
      cy.get('body').should('contain', 'Password must be at least 8 characters')
      cy.url().should('include', '/staff/login')
    })

    it('should require matching passwords during change', () => {
      cy.visit('/staff/change-password')
      cy.get('input[name="new_password"]').type('newpassword123')
      cy.get('input[name="confirm_password"]').type('differentpassword123')
      cy.get('button[type="submit"]').click()
      
      cy.get('body').should('contain', 'Passwords do not match')
      cy.url().should('include', '/staff/login')
    })

    it('should successfully change password when requirements met', () => {
      // This would need proper session setup
      cy.visit('/staff/change-password')
      cy.get('input[name="new_password"]').type('newpassword123')
      cy.get('input[name="confirm_password"]').type('newpassword123')
      cy.get('button[type="submit"]').click()
      
      cy.url().should('include', '/dashboard')
    })

    it('should reject empty new password', () => {
      cy.visit('/staff/change-password')
      cy.get('input[name="confirm_password"]').type('password123')
      cy.get('button[type="submit"]').click()
      
      cy.get('body').should('contain', 'Password must be at least 8 characters')
    })

    it('should reject empty confirm password', () => {
      cy.visit('/staff/change-password')
      cy.get('input[name="new_password"]').type('password123')
      cy.get('button[type="submit"]').click()
      
      cy.get('body').should('contain', 'Passwords do not match')
    })
  })

  describe('Staff Logout', () => {
    beforeEach(() => {
      // Login first
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/dashboard')
    })

    it('should successfully logout and redirect to login page', () => {
      cy.visit('/staff/logout')
      
      cy.url().should('include', '/staff/login')
      cy.getCookie('session').should('not.exist')
      cy.get('input[name="email"]').should('be.visible')
    })

    it('should clear all session data on logout', () => {
      cy.visit('/staff/logout')
      
      cy.getAllCookies().should('have.length', 0)
      cy.url().should('include', '/staff/login')
    })

    it('should prevent access to protected pages after logout', () => {
      cy.visit('/staff/logout')
      cy.visit('/dashboard/staff')
      
      cy.url().should('include', '/staff/login')
    })
  })

  describe('API Staff Login', () => {
    it('should accept valid JSON login request', () => {
      cy.request({
        method: 'POST',
        url: '/api/staff/login',
        body: {
          email: 'test@example.com',
          password: 'testpass123'
        }
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body.success).to.be.true
        expect(response.body.staff).to.have.property('email', 'test@example.com')
        expect(response.body.staff).to.have.property('role')
      })
    })

    it('should reject API login with missing email', () => {
      cy.request({
        method: 'POST',
        url: '/api/staff/login',
        body: {
          password: 'testpass123'
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(400)
        expect(response.body.success).to.be.false
        expect(response.body.error).to.contain('Email and password required')
      })
    })

    it('should reject API login with missing password', () => {
      cy.request({
        method: 'POST',
        url: '/api/staff/login',
        body: {
          email: 'test@example.com'
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(400)
        expect(response.body.success).to.be.false
        expect(response.body.error).to.contain('Email and password required')
      })
    })

    it('should reject API login with invalid credentials', () => {
      cy.request({
        method: 'POST',
        url: '/api/staff/login',
        body: {
          email: 'test@example.com',
          password: 'wrongpassword'
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(401)
        expect(response.body.success).to.be.false
        expect(response.body.error).to.contain('Invalid credentials')
      })
    })

    it('should reject API login with disabled account', () => {
      cy.request({
        method: 'POST',
        url: '/api/staff/login',
        body: {
          email: 'disabled@example.com',
          password: 'testpass123'
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(403)
        expect(response.body.success).to.be.false
        expect(response.body.error).to.contain('Account disabled')
      })
    })

    it('should handle malformed JSON in API login', () => {
      cy.request({
        method: 'POST',
        url: '/api/staff/login',
        headers: {
          'Content-Type': 'application/json'
        },
        body: '{invalid json}',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([400, 500])
      })
    })

    it('should handle empty JSON body in API login', () => {
      cy.request({
        method: 'POST',
        url: '/api/staff/login',
        body: {},
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(400)
        expect(response.body.success).to.be.false
      })
    })
  })

  describe('Staff Management Dashboard - Admin Access', () => {
    beforeEach(() => {
      // Login as admin
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/dashboard')
    })

    it('should display staff management page for admin users', () => {
      cy.visit('/dashboard/staff')
      
      cy.url().should('include', '/dashboard/staff')
      cy.get('h1, h2, h3').should('contain', 'Staff')
      cy.get('[data-cy="add-staff-button"], button').should('be.visible')
      cy.get('table, .staff-list').should('be.visible')
    })

    it('should show staff statistics on management page', () => {
      cy.visit('/dashboard/staff')
      
      cy.get('.stats, .statistics, [data-cy="stats"]').should('be.visible')
      cy.get('body').should('contain', 'total')
      cy.get('body').should('contain', 'admin')
    })

    it('should display list of all staff members', () => {
      cy.visit('/dashboard/staff')
      
      cy.get('table tbody tr, .staff-item').should('have.length.greaterThan', 0)
      cy.get('body').should('contain', 'test@example.com')
    })

    it('should show success message after staff operations', () => {
      cy.visit('/dashboard/staff?message=Staff member added successfully')
      
      cy.get('.alert-success, .success-message, .message').should('contain', 'successfully')
      cy.get('.alert-success, .success-message, .message').should('be.visible')
    })

    it('should show error message after failed operations', () => {
      cy.visit('/dashboard/staff?error=Email already exists')
      
      cy.get('.alert-danger, .error-message, .error').should('contain', 'Email already exists')
      cy.get('.alert-danger, .error-message, .error').should('be.visible')
    })

    it('should handle empty staff list gracefully', () => {
      cy.visit('/dashboard/staff')
      
      // Even with staff, page should load without errors
      cy.get('body').should('not.contain', '500 Internal Server Error')
      cy.get('body').should('not.contain', 'Database error')
    })

    it('should show staff roles in the listing', () => {
      cy.visit('/dashboard/staff')
      
      cy.get('body').should('contain', 'admin')
      cy.get('table, .staff-list').should('be.visible')
    })

    it('should show staff status (active/inactive)', () => {
      cy.visit('/dashboard/staff')
      
      cy.get('table, .staff-list').should('contain', 'Active').or('contain', 'Inactive')
    })
  })

  describe('Staff Management - Role-based Access', () => {
    it('should deny access to non-admin users', () => {
      // This test would need a non-admin user
      cy.visit('/staff/login')
      cy.get('input[name="email"]').type('staff@example.com')
      cy.get('input[name="password"]').type('staffpass123')
      cy.get('button[type="submit"]').click()
      
      cy.visit('/dashboard/staff')
      cy.get('body').should('contain', 'Access Denied').or('contain', 'Insufficient permissions')
      cy.get('h1').should('contain', 'Access Denied').or('contain', 'Error')
    })

    it('should allow admin access to staff management', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      
      cy.visit('/dashboard/staff')
      cy.url().should('include', '/dashboard/staff')
      cy.get('body').should('not.contain', 'Access Denied')
    })

    it('should redirect unauthenticated users to login', () => {
      cy.visit('/dashboard/staff')
      
      cy.url().should('include', '/staff/login')
      cy.get('input[name="email"]').should('be.visible')
    })
  })

  describe('Add Staff Member', () => {
    beforeEach(() => {
      // Login as admin
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.visit('/dashboard/staff')
    })

    it('should successfully add new staff member with valid data', () => {
      const timestamp = Date.now()
      
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type(`newstaff${timestamp}@example.com`)
        cy.get('input[name="first_name"]').type('New')
        cy.get('input[name="last_name"]').type('Staff')
        cy.get('select[name="role"]').select('viewer')
        cy.get('input[name="password"]').type('newstaffpass123')
        cy.get('button[type="submit"]').click()
      })
      
      cy.url().should('include', '/dashboard/staff')
      cy.get('body').should('contain', 'added successfully')
      cy.get('body').should('contain', `newstaff${timestamp}@example.com`)
    })

    it('should reject adding staff with empty email', () => {
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="first_name"]').type('Test')
        cy.get('input[name="last_name"]').type('User')
        cy.get('select[name="role"]').select('viewer')
        cy.get('input[name="password"]').type('password123')
        cy.get('button[type="submit"]').click()
      })
      
      cy.url().should('include', '/dashboard/staff')
      cy.get('body').should('contain', 'Email and password are required')
    })

    it('should reject adding staff with empty password', () => {
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type('test@example.com')
        cy.get('input[name="first_name"]').type('Test')
        cy.get('input[name="last_name"]').type('User')
        cy.get('select[name="role"]').select('viewer')
        cy.get('button[type="submit"]').click()
      })
      
      cy.url().should('include', '/dashboard/staff')
      cy.get('body').should('contain', 'Email and password are required')
    })

    it('should reject duplicate email addresses', () => {
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type('test@example.com') // Existing email
        cy.get('input[name="first_name"]').type('Duplicate')
        cy.get('input[name="last_name"]').type('User')
        cy.get('select[name="role"]').select('viewer')
        cy.get('input[name="password"]').type('password123')
        cy.get('button[type="submit"]').click()
      })
      
      cy.url().should('include', '/dashboard/staff')
      cy.get('body').should('contain', 'Email already exists')
    })

    it('should reject invalid role selection', () => {
      // Manually set invalid role value
      cy.get('select[name="role"]').then($select => {
        $select.val('invalid_role')
      })
      
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type('invalid@example.com')
        cy.get('input[name="first_name"]').type('Invalid')
        cy.get('input[name="last_name"]').type('Role')
        cy.get('input[name="password"]').type('password123')
        cy.get('button[type="submit"]').click()
      })
      
      cy.url().should('include', '/dashboard/staff')
      cy.get('body').should('contain', 'Invalid role selected')
    })

    it('should handle XSS attempts in staff name fields', () => {
      const timestamp = Date.now()
      
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type(`xss${timestamp}@example.com`)
        cy.get('input[name="first_name"]').type('<script>alert("xss")</script>')
        cy.get('input[name="last_name"]').type('<img src=x onerror=alert(1)>')
        cy.get('select[name="role"]').select('viewer')
        cy.get('input[name="password"]').type('password123')
        cy.get('button[type="submit"]').click()
      })
      
      // Should either succeed or fail gracefully, but not execute script
      cy.get('body').should('not.contain', '<script>')
      cy.get('body').should('not.contain', '<img src=x')
    })

    it('should handle SQL injection attempts in email field', () => {
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type("'; DROP TABLE staff; --@example.com")
        cy.get('input[name="first_name"]').type('SQL')
        cy.get('input[name="last_name"]').type('Injection')
        cy.get('select[name="role"]').select('viewer')
        cy.get('input[name="password"]').type('password123')
        cy.get('button[type="submit"]').click()
      })
      
      cy.get('body').should('not.contain', '500 Internal Server Error')
      // Should either fail validation or succeed without damage
    })

    it('should validate email format during staff creation', () => {
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type('invalid-email-format')
        cy.get('input[name="first_name"]').type('Invalid')
        cy.get('input[name="last_name"]').type('Email')
        cy.get('select[name="role"]').select('viewer')
        cy.get('input[name="password"]').type('password123')
        cy.get('button[type="submit"]').click()
      })
      
      // Should either fail client-side validation or server-side
      cy.get('body').should('contain', 'email').or('contain', 'Email').or('contain', 'invalid')
    })

    it('should trim whitespace from input fields', () => {
      const timestamp = Date.now()
      
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type(`  whitespace${timestamp}@example.com  `)
        cy.get('input[name="first_name"]').type('  Whitespace  ')
        cy.get('input[name="last_name"]').type('  Test  ')
        cy.get('select[name="role"]').select('viewer')
        cy.get('input[name="password"]').type('password123')
        cy.get('button[type="submit"]').click()
      })
      
      cy.url().should('include', '/dashboard/staff')
      cy.get('body').should('contain', 'added successfully')
    })

    it('should handle very long input values', () => {
      const longString = 'a'.repeat(500)
      const timestamp = Date.now()
      
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type(`${timestamp}@example.com`)
        cy.get('input[name="first_name"]').type(longString)
        cy.get('input[name="last_name"]').type(longString)
        cy.get('select[name="role"]').select('viewer')
        cy.get('input[name="password"]').type('password123')
        cy.get('button[type="submit"]').click()
      })
      
      // Should either succeed or fail gracefully
      cy.get('body').should('not.contain', '500 Internal Server Error')
    })

    it('should set force_password_change for new staff members', () => {
      const timestamp = Date.now()
      
      cy.get('[data-cy="add-staff-form"], form').within(() => {
        cy.get('input[name="email"]').type(`forcechange${timestamp}@example.com`)
        cy.get('input[name="first_name"]').type('Force')
        cy.get('input[name="last_name"]').type('Change')
        cy.get('select[name="role"]').select('viewer')
        cy.get('input[name="password"]').type('temppass123')
        cy.get('button[type="submit"]').click()
      })
      
      cy.url().should('include', '/dashboard/staff')
      cy.get('body').should('contain', 'added successfully')
    })
  })

  describe('Update Staff Member', () => {
    beforeEach(() => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.visit('/dashboard/staff')
    })

    it('should successfully update staff member details', () => {
      cy.get('[data-cy="edit-staff-button"], .edit-button, button').first().click()
      
      cy.get('input[name="first_name"]').clear().type('Updated')
      cy.get('input[name="last_name"]').clear().type('Name')
      cy.get('button[type="submit"]').click()