/// <reference types="cypress" />

describe('FCRA Authentication System', () => {
  beforeEach(() => {
    cy.visit('/staff/login')
  })

  describe('Staff Login Page', () => {
    it('should display login form with all required elements', () => {
      cy.get('[data-cy="login-form"]').should('exist')
      cy.get('input[name="email"]').should('exist')
      cy.get('input[name="password"]').should('exist')
      cy.get('button[type="submit"]').should('exist')
      cy.url().should('include', '/staff/login')
      cy.title().should('contain', 'Login')
    })

    it('should redirect authenticated users to dashboard', () => {
      cy.window().then((win) => {
        win.sessionStorage.setItem('staff_id', '1')
        win.sessionStorage.setItem('staff_role', 'admin')
      })
      cy.visit('/staff/login')
      cy.url().should('include', '/dashboard')
      cy.get('[data-cy="dashboard"]').should('be.visible')
    })

    it('should have proper form validation attributes', () => {
      cy.get('input[name="email"]').should('have.attr', 'type', 'email')
      cy.get('input[name="password"]').should('have.attr', 'type', 'password')
      cy.get('input[name="email"]').should('have.attr', 'required')
      cy.get('input[name="password"]').should('have.attr', 'required')
      cy.get('form').should('have.attr', 'novalidate').should('not.exist')
    })

    it('should display proper labels and placeholders', () => {
      cy.get('label[for="email"]').should('contain', 'Email')
      cy.get('label[for="password"]').should('contain', 'Password')
      cy.get('input[name="email"]').should('have.attr', 'placeholder')
      cy.get('input[name="password"]').should('have.attr', 'placeholder')
      cy.get('button[type="submit"]').should('contain.text', 'Sign In')
    })

    it('should show loading state during form submission', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.get('button[type="submit"]').should('be.disabled')
      cy.get('[data-cy="loading-spinner"]').should('be.visible')
      cy.get('button[type="submit"]').should('contain', 'Signing In...')
    })
  })

  describe('Empty Field Validation', () => {
    it('should show error for empty email field', () => {
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Please enter email and password')
      cy.url().should('include', '/staff/login')
      cy.get('input[name="email"]').should('have.class', 'error')
    })

    it('should show error for empty password field', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Please enter email and password')
      cy.url().should('include', '/staff/login')
      cy.get('input[name="password"]').should('have.class', 'error')
    })

    it('should show error for both empty fields', () => {
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Please enter email and password')
      cy.url().should('include', '/staff/login')
      cy.get('input[name="email"]').should('have.class', 'error')
      cy.get('input[name="password"]').should('have.class', 'error')
    })

    it('should show error for whitespace-only email', () => {
      cy.get('input[name="email"]').type('   ')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Please enter email and password')
      cy.url().should('include', '/staff/login')
    })

    it('should show error for whitespace-only password', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('   ')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Please enter email and password')
      cy.url().should('include', '/staff/login')
    })

    it('should preserve email value after empty password error', () => {
      const testEmail = 'test@example.com'
      cy.get('input[name="email"]').type(testEmail)
      cy.get('button[type="submit"]').click()
      cy.get('input[name="email"]').should('have.value', testEmail)
      cy.get('input[name="password"]').should('have.value', '')
    })
  })

  describe('Invalid Email Format Validation', () => {
    const invalidEmails = [
      'invalid-email',
      '@domain.com',
      'user@',
      'user..name@domain.com',
      'user@domain',
      'user@.com',
      'user@domain.',
      'user name@domain.com',
      'user@domain .com',
      'user@@domain.com',
      '<script>alert("xss")</script>@domain.com'
    ]

    invalidEmails.forEach((email) => {
      it(`should reject invalid email format: ${email}`, () => {
        cy.get('input[name="email"]').type(email)
        cy.get('input[name="password"]').type('testpass123')
        cy.get('button[type="submit"]').click()
        cy.get('[data-cy="error-message"]').should('be.visible')
        cy.url().should('include', '/staff/login')
        cy.get('input[name="email"]').should('have.value', email)
      })
    })

    it('should handle extremely long email addresses', () => {
      const longEmail = 'a'.repeat(250) + '@' + 'b'.repeat(250) + '.com'
      cy.get('input[name="email"]').type(longEmail.substring(0, 100))
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('be.visible')
      cy.url().should('include', '/staff/login')
    })

    it('should handle special characters in email', () => {
      cy.get('input[name="email"]').type('test+user@domain.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Invalid email or password')
      cy.url().should('include', '/staff/login')
    })

    it('should handle Unicode characters in email', () => {
      cy.get('input[name="email"]').type('tëst@dömäin.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('be.visible')
      cy.url().should('include', '/staff/login')
    })
  })

  describe('SQL Injection Protection', () => {
    const sqlInjectionAttempts = [
      "'; DROP TABLE Staff; --",
      "' OR '1'='1",
      "' UNION SELECT * FROM Staff --",
      "admin'; DELETE FROM Staff WHERE '1'='1",
      "' OR 1=1 --",
      "'; INSERT INTO Staff VALUES ('hacker', 'admin'); --",
      "' OR EXISTS(SELECT * FROM Staff) --"
    ]

    sqlInjectionAttempts.forEach((injection) => {
      it(`should prevent SQL injection attempt: ${injection}`, () => {
        cy.get('input[name="email"]').type(injection)
        cy.get('input[name="password"]').type('testpass123')
        cy.get('button[type="submit"]').click()
        cy.get('[data-cy="error-message"]').should('contain', 'Invalid email or password')
        cy.url().should('include', '/staff/login')
        cy.get('body').should('not.contain', 'SQL Error')
      })
    })

    it('should prevent SQL injection in password field', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type("'; DROP TABLE Staff; --")
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Invalid email or password')
      cy.url().should('include', '/staff/login')
    })
  })

  describe('XSS Protection', () => {
    const xssAttempts = [
      '<script>alert("XSS")</script>',
      '<img src=x onerror=alert("XSS")>',
      'javascript:alert("XSS")',
      '<svg onload=alert("XSS")>',
      '<iframe src="javascript:alert(\'XSS\')">',
      '<body onload=alert("XSS")>',
      '<div onclick=alert("XSS")>test</div>'
    ]

    xssAttempts.forEach((xss) => {
      it(`should prevent XSS attempt in email: ${xss}`, () => {
        cy.get('input[name="email"]').type(xss)
        cy.get('input[name="password"]').type('testpass123')
        cy.get('button[type="submit"]').click()
        cy.get('[data-cy="error-message"]').should('be.visible')
        cy.get('body').should('not.contain', 'XSS')
        cy.window().then((win) => {
          expect(win.document.body.innerHTML).to.not.contain('<script>')
        })
      })
    })

    it('should prevent XSS attempt in password field', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('<script>alert("XSS")</script>')
      cy.get('button[type="submit"]').click()
      cy.get('body').should('not.contain', 'XSS')
    })

    it('should sanitize error message output', () => {
      cy.get('input[name="email"]').type('<b>bold@test.com</b>')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('not.contain', '<b>')
      cy.get('[data-cy="error-message"] b').should('not.exist')
    })
  })

  describe('Successful Login - Valid Credentials', () => {
    it('should login successfully with admin credentials', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/dashboard')
      cy.get('[data-cy="user-menu"]').should('contain', 'CI Test Admin')
      cy.get('[data-cy="user-role"]').should('contain', 'admin')
    })

    it('should create session data after successful login', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.getCookie('session').should('exist')
      cy.window().its('sessionStorage').should('not.be.empty')
    })

    it('should redirect to dashboard with proper navigation', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.url().should('eq', Cypress.config().baseUrl + '/dashboard')
      cy.get('[data-cy="sidebar"]').should('be.visible')
      cy.get('[data-cy="main-content"]').should('be.visible')
    })

    it('should set permanent session with proper expiry', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.getCookie('session').should('have.property', 'httpOnly', true)
      cy.getCookie('session').should('have.property', 'secure', true)
      cy.getCookie('session').should('have.property', 'sameSite', 'lax')
    })

    it('should update last login timestamp', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.visit('/dashboard/profile')
      cy.get('[data-cy="last-login"]').should('contain', new Date().toDateString())
    })

    it('should handle case-insensitive email login', () => {
      cy.get('input[name="email"]').type('TEST@EXAMPLE.COM')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/dashboard')
      cy.get('[data-cy="user-email"]').should('contain', 'test@example.com')
    })

    it('should trim whitespace from email before login', () => {
      cy.get('input[name="email"]').type('  test@example.com  ')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/dashboard')
      cy.get('[data-cy="user-email"]').should('contain', 'test@example.com')
    })
  })

  describe('Failed Login Attempts', () => {
    it('should show error for non-existent user', () => {
      cy.get('input[name="email"]').type('nonexistent@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Invalid email or password')
      cy.url().should('include', '/staff/login')
      cy.get('input[name="email"]').should('have.value', 'nonexistent@example.com')
    })

    it('should show error for incorrect password', () => {
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('wrongpassword')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Invalid email or password')
      cy.url().should('include', '/staff/login')
      cy.get('input[name="password"]').should('have.value', '')
    })

    it('should preserve email after failed password attempt', () => {
      const testEmail = 'test@example.com'
      cy.get('input[name="email"]').type(testEmail)
      cy.get('input[name="password"]').type('wrongpassword')
      cy.get('button[type="submit"]').click()
      cy.get('input[name="email"]').should('have.value', testEmail)
      cy.get('input[name="password"]').should('have.value', '')
    })

    it('should not reveal if user exists or not', () => {
      // Test with non-existent user
      cy.get('input[name="email"]').type('fake@example.com')
      cy.get('input[name="password"]').type('wrongpass')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Invalid email or password')
      
      // Test with existing user but wrong password
      cy.get('input[name="email"]').clear().type('test@example.com')
      cy.get('input[name="password"]').clear().type('wrongpass')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Invalid email or password')
    })

    it('should handle login attempt with disabled account', () => {
      // Assuming we have a disabled test account
      cy.get('input[name="email"]').type('disabled@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Account is disabled')
      cy.url().should('include', '/staff/login')
    })
  })

  describe('Rate Limiting Protection', () => {
    it('should implement rate limiting after multiple failed attempts', () => {
      const attempts = 5
      for (let i = 0; i < attempts; i++) {
        cy.get('input[name="email"]').clear().type('test@example.com')
        cy.get('input[name="password"]').clear().type(`wrongpass${i}`)
        cy.get('button[type="submit"]').click()
        cy.wait(500)
      }
      cy.get('[data-cy="error-message"]').should('contain', 'Too many login attempts')
      cy.get('button[type="submit"]').should('be.disabled')
    })

    it('should show countdown timer for rate limiting', () => {
      // Trigger rate limit
      for (let i = 0; i < 5; i++) {
        cy.get('input[name="email"]').clear().type('test@example.com')
        cy.get('input[name="password"]').clear().type('wrongpass')
        cy.get('button[type="submit"]').click()
        cy.wait(200)
      }
      cy.get('[data-cy="rate-limit-timer"]').should('be.visible')
      cy.get('[data-cy="rate-limit-timer"]').should('contain', 'Try again in')
    })

    it('should rate limit by IP address', () => {
      // Multiple different emails from same IP should trigger rate limit
      const emails = ['user1@test.com', 'user2@test.com', 'user3@test.com']
      emails.forEach((email) => {
        for (let i = 0; i < 2; i++) {
          cy.get('input[name="email"]').clear().type(email)
          cy.get('input[name="password"]').clear().type('wrongpass')
          cy.get('button[type="submit"]').click()
          cy.wait(200)
        }
      })
      cy.get('[data-cy="error-message"]').should('contain', 'Too many login attempts')
    })

    it('should reset rate limit after timeout period', () => {
      // Trigger rate limit
      for (let i = 0; i < 5; i++) {
        cy.get('input[name="email"]').clear().type('test@example.com')
        cy.get('input[name="password"]').clear().type('wrongpass')
        cy.get('button[type="submit"]').click()
        cy.wait(200)
      }
      
      // Wait for rate limit to expire (assuming 5 minute timeout)
      cy.wait(300000) // 5 minutes
      
      cy.get('input[name="email"]').clear().type('test@example.com')
      cy.get('input[name="password"]').clear().type('testpass123')
      cy.get('button[type="submit"]').should('not.be.disabled')
    })
  })

  describe('Session Management', () => {
    beforeEach(() => {
      // Login first
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/dashboard')
    })

    it('should maintain session across page refreshes', () => {
      cy.reload()
      cy.url().should('include', '/dashboard')
      cy.get('[data-cy="user-menu"]').should('be.visible')
    })

    it('should maintain session across browser navigation', () => {
      cy.visit('/dashboard/clients')
      cy.get('[data-cy="clients-page"]').should('be.visible')
      cy.go('back')
      cy.get('[data-cy="dashboard"]').should('be.visible')
    })

    it('should expire session after configured timeout', () => {
      // Mock session expiration
      cy.window().then((win) => {
        win.sessionStorage.clear()
      })
      cy.clearCookies()
      cy.reload()
      cy.url().should('include', '/staff/login')
      cy.get('[data-cy="session-expired-message"]').should('be.visible')
    })

    it('should handle concurrent sessions properly', () => {
      // Open second window/tab
      cy.window().then((win) => {
        const newWin = win.open('/dashboard', '_blank')
        expect(newWin).to.not.be.null
      })
      
      // Both should maintain valid sessions
      cy.get('[data-cy="user-menu"]').should('be.visible')
    })

    it('should invalidate session on password change', () => {
      cy.visit('/dashboard/profile')
      cy.get('[data-cy="change-password-btn"]').click()
      cy.get('input[name="current_password"]').type('testpass123')
      cy.get('input[name="new_password"]').type('newpassword123')
      cy.get('input[name="confirm_password"]').type('newpassword123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/staff/login')
      cy.get('[data-cy="password-changed-message"]').should('be.visible')
    })

    it('should handle session fixation attacks', () => {
      // Store original session ID
      cy.getCookie('session').then((originalCookie) => {
        const originalSessionId = originalCookie?.value
        
        // Logout and login again
        cy.visit('/staff/logout')
        cy.visit('/staff/login')
        cy.get('input[name="email"]').type('test@example.com')
        cy.get('input[name="password"]').type('testpass123')
        cy.get('button[type="submit"]').click()
        
        // Session ID should be different
        cy.getCookie('session').then((newCookie) => {
          expect(newCookie?.value).to.not.equal(originalSessionId)
        })
      })
    })
  })

  describe('Logout Functionality', () => {
    beforeEach(() => {
      // Login first
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/dashboard')
    })

    it('should logout successfully from user menu', () => {
      cy.get('[data-cy="user-menu"]').click()
      cy.get('[data-cy="logout-btn"]').click()
      cy.url().should('include', '/staff/login')
      cy.get('[data-cy="logout-success-message"]').should('be.visible')
    })

    it('should clear session data on logout', () => {
      cy.get('[data-cy="user-menu"]').click()
      cy.get('[data-cy="logout-btn"]').click()
      cy.getCookie('session').should('not.exist')
      cy.window().its('sessionStorage').should('be.empty')
    })

    it('should redirect to login when accessing protected pages after logout', () => {
      cy.get('[data-cy="user-menu"]').click()
      cy.get('[data-cy="logout-btn"]').click()
      cy.visit('/dashboard')
      cy.url().should('include', '/staff/login')
    })

    it('should handle logout from direct URL access', () => {
      cy.visit('/staff/logout')
      cy.url().should('include', '/staff/login')
      cy.get('[data-cy="logout-success-message"]').should('be.visible')
    })

    it('should log audit trail for logout event', () => {
      cy.get('[data-cy="user-menu"]').click()
      cy.get('[data-cy="logout-btn"]').click()
      
      // Re-login as admin to check audit logs
      cy.get('input[name="email"]').type('test@example.com')
      cy.get('input[name="password"]').type('testpass123')
      cy.get('button[type="submit"]').click()
      cy.visit('/dashboard/audit-logs')
      cy.get('[data-cy="audit-log"]').first().should('contain', 'LOGOUT')
    })

    it('should handle logout with JavaScript disabled', () => {
      cy.visit('/staff/logout', {
        onBeforeLoad: (win) => {
          delete win.fetch
          win.XMLHttpRequest = undefined
        }
      })
      cy.url().should('include', '/staff/login')
    })
  })

  describe('Force Password Change Flow', () => {
    it('should redirect to password change for new admin account', () => {
      cy.get('input[name="email"]').type('admin@brightpathascend.com')
      cy.get('input[name="password"]').type('ChangeMe123!')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="force-password-change"]').should('be.visible')
      cy.get('input[name="new_password"]').should('be.visible')
      cy.get('input[name="confirm_password"]').should('be.visible')
    })

    it('should validate new password meets requirements', () => {
      cy.get('input[name="email"]').type('admin@brightpathascend.com')
      cy.get('input[name="password"]').type('ChangeMe123!')
      cy.get('button[type="submit"]').click()
      
      cy.get('input[name="new_password"]').type('weak')
      cy.get('input[name="confirm_password"]').type('weak')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Password must be at least 8 characters')
    })

    it('should validate password confirmation matches', () => {
      cy.get('input[name="email"]').type('admin@brightpathascend.com')
      cy.get('input[name="password"]').type('ChangeMe123!')
      cy.get('button[type="submit"]').click()
      
      cy.get('input[name="new_password"]').type('newpassword123')
      cy.get('input[name="confirm_password"]').type('differentpassword123')
      cy.get('button[type="submit"]').click()
      cy.get('[data-cy="error-message"]').should('contain', 'Passwords do not match')
    })

    it('should successfully change password and redirect to dashboard', () => {
      cy.get('input[name="email"]').type('admin@brightpathascend.com')
      cy.get('input[name="password"]').type('ChangeMe123!')
      cy.get('button[type="submit"]').click()
      
      cy.get('input[name="new_password"]').type('mynewpassword123')
      cy.get('input[name="confirm_password"]').type('mynewpassword123')
      cy.get('button[type="submit"]').click()
      cy.url().should('include', '/dashboard')
      cy.get('[data-cy="password-changed-success"]').should('be.visible')
    })

    it('should not allow skipping force password change', () => {
      cy.get('input[name="email"]').type('admin@brightpathascend.com')
      cy.get('input[name="password"]').type('ChangeMe123!')
      cy.get('button[type="submit"]').click()
      
      cy.visit('/dashboard')
      cy.get('[data-cy="force-password-change"]').should('be.visible')
      cy.url().should('include', '/staff/login')
    })
  })

  describe('API Authentication Endpoints', () => {
    it('should authenticate via API login endpoint', () => {
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
        expect(response.body.staff).to.have.property('role', 'admin')
      })
    })

    it('should return error for invalid API credentials', () => {
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

    it('should return error for disabled account via API', () => {
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

    it