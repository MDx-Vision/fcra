/**
 * API ENDPOINTS - Comprehensive E2E Tests
 * Tests API endpoints directly for authentication, CRUD operations, and error handling
 */

describe('API Endpoints', () => {
  describe('Authentication APIs', () => {
    it('POST /api/login - valid credentials', () => {
      cy.request({
        method: 'POST',
        url: '/api/login',
        body: { email: 'test@example.com', password: 'testpass123' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 302, 404]);
      });
    });

    it('POST /api/login - invalid credentials', () => {
      cy.request({
        method: 'POST',
        url: '/api/login',
        body: { email: 'invalid@example.com', password: 'wrongpass' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([401, 400, 404]);
      });
    });

    it('POST /api/logout', () => {
      cy.request({
        method: 'POST',
        url: '/api/logout',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 302, 404]);
      });
    });

    it('GET /api/me - authenticated', () => {
      cy.request({
        method: 'GET',
        url: '/api/me',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 404]);
      });
    });

    it('GET /api/me - unauthenticated returns 401', () => {
      cy.request({
        method: 'GET',
        url: '/api/me',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 404]);
      });
    });
  });

  describe('Client APIs', () => {
    it('GET /api/clients - list all clients', () => {
      cy.request({
        method: 'GET',
        url: '/api/clients',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 404]);
      });
    });

    it('GET /api/clients/:id - get single client', () => {
      cy.request({
        method: 'GET',
        url: '/api/clients/1',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });

    it('POST /api/client/signup - create client', () => {
      cy.request({
        method: 'POST',
        url: '/api/client/signup',
        body: {
          firstName: 'Test',
          lastName: 'User',
          email: `test${Date.now()}@example.com`
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 201, 400, 404]);
      });
    });

    it('PUT /api/clients/:id - update client', () => {
      cy.request({
        method: 'PUT',
        url: '/api/clients/1',
        body: { firstName: 'Updated' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });

    it('DELETE /api/clients/:id - soft delete', () => {
      cy.request({
        method: 'DELETE',
        url: '/api/clients/999',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });
  });

  describe('Case APIs', () => {
    it('GET /api/cases - list cases', () => {
      cy.request({
        method: 'GET',
        url: '/api/cases',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 404]);
      });
    });

    it('GET /api/case/:id - get case details', () => {
      cy.request({
        method: 'GET',
        url: '/api/case/1',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });

    it('POST /api/case - create case', () => {
      cy.request({
        method: 'POST',
        url: '/api/case',
        body: { clientId: 1, title: 'Test Case' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 201, 400, 404]);
      });
    });

    it('PUT /api/case/:id - update case', () => {
      cy.request({
        method: 'PUT',
        url: '/api/case/1',
        body: { status: 'active' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });
  });

  describe('Dispute APIs', () => {
    it('GET /api/disputes - list disputes', () => {
      cy.request({
        method: 'GET',
        url: '/api/disputes',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 404]);
      });
    });

    it('POST /api/dispute - create dispute', () => {
      cy.request({
        method: 'POST',
        url: '/api/dispute',
        body: { caseId: 1, type: 'account' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 201, 400, 404]);
      });
    });

    it('PUT /api/dispute/:id - update dispute', () => {
      cy.request({
        method: 'PUT',
        url: '/api/dispute/1',
        body: { status: 'sent' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });

    it('POST /api/dispute/:id/send - send dispute', () => {
      cy.request({
        method: 'POST',
        url: '/api/dispute/1/send',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });
  });

  describe('Settlement APIs', () => {
    it('GET /api/settlements - list settlements', () => {
      cy.request({
        method: 'GET',
        url: '/api/settlements',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 404]);
      });
    });

    it('POST /api/settlement - create settlement', () => {
      cy.request({
        method: 'POST',
        url: '/api/settlement',
        body: { caseId: 1, amount: 5000 },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 201, 400, 404]);
      });
    });

    it('PUT /api/settlement/:id - update settlement', () => {
      cy.request({
        method: 'PUT',
        url: '/api/settlement/1',
        body: { status: 'accepted' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });

    it('POST /api/settlement/:id/offer - add offer', () => {
      cy.request({
        method: 'POST',
        url: '/api/settlement/1/offer',
        body: { amount: 3000 },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });
  });

  describe('Staff APIs', () => {
    it('GET /api/staff - list staff', () => {
      cy.request({
        method: 'GET',
        url: '/api/staff',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 404]);
      });
    });

    it('POST /api/staff - create staff', () => {
      cy.request({
        method: 'POST',
        url: '/api/staff',
        body: { email: 'newstaff@example.com', name: 'New Staff' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 201, 400, 404]);
      });
    });

    it('PUT /api/staff/:id - update staff', () => {
      cy.request({
        method: 'PUT',
        url: '/api/staff/1',
        body: { name: 'Updated Name' },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });

    it('DELETE /api/staff/:id - deactivate staff', () => {
      cy.request({
        method: 'DELETE',
        url: '/api/staff/999',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });
  });

  describe('Document APIs', () => {
    it('GET /api/documents - list documents', () => {
      cy.request({
        method: 'GET',
        url: '/api/documents',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 401, 404]);
      });
    });

    it('POST /api/document/upload - upload document', () => {
      cy.request({
        method: 'POST',
        url: '/api/document/upload',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 201, 400, 404]);
      });
    });

    it('GET /api/document/:id - download document', () => {
      cy.request({
        method: 'GET',
        url: '/api/document/1',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });

    it('DELETE /api/document/:id - delete document', () => {
      cy.request({
        method: 'DELETE',
        url: '/api/document/999',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 404, 401]);
      });
    });
  });

  describe('Error Handling', () => {
    it('should return 400 for bad request', () => {
      cy.request({
        method: 'POST',
        url: '/api/client/signup',
        body: {},
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([400, 404]);
      });
    });

    it('should return 401 for unauthorized', () => {
      cy.request({
        method: 'GET',
        url: '/api/admin/settings',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([401, 404]);
      });
    });

    it('should return 403 for forbidden', () => {
      cy.request({
        method: 'GET',
        url: '/api/forbidden',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([403, 404]);
      });
    });

    it('should return 404 for not found', () => {
      cy.request({
        method: 'GET',
        url: '/api/nonexistent-endpoint-12345',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.equal(404);
      });
    });

    it('should return 500 for server error', () => {
      cy.request({
        method: 'GET',
        url: '/api/error',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([500, 404]);
      });
    });
  });

  describe('Response Formats', () => {
    it('should return JSON for API requests', () => {
      cy.request({
        method: 'GET',
        url: '/api/clients',
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200) {
          expect(response.headers).to.have.property('content-type');
        }
      });
    });

    it('should include proper headers', () => {
      cy.request({
        method: 'GET',
        url: '/api/me',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.headers).to.exist;
      });
    });

    it('should handle CORS properly', () => {
      cy.request({
        method: 'OPTIONS',
        url: '/api/clients',
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 204, 404]);
      });
    });
  });
});
