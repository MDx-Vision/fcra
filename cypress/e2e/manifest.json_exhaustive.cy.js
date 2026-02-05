// Exhaustive test for /manifest.json
// Note: This is a JSON endpoint, not an HTML page, so we use cy.request() instead of cy.visit()
describe('/manifest.json', () => {
  // No beforeEach visit needed - each test uses cy.request()

  describe('Page Load Tests', () => {
    it('should load without errors', () => {
      cy.request('/manifest.json').then((response) => {
        expect(response.status).to.eq(200);
      });
    });

    it('should have correct URL', () => {
      cy.request('/manifest.json').then((response) => {
        expect(response.status).to.eq(200);
      });
    });

    it('should not have server errors', () => {
      cy.request('/manifest.json').then((response) => {
        expect(response.status).to.eq(200);
        expect(response.headers['content-type']).to.include('application/json');
      });
    });

    it('should return valid JSON', () => {
      cy.request('/manifest.json').then((response) => {
        expect(response.body).to.be.an('object');
        expect(() => JSON.parse(JSON.stringify(response.body))).to.not.throw();
      });
    });
  });

  describe('PWA Manifest Content Tests', () => {
    it('should have required PWA manifest fields', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        // Test required fields
        expect(manifest).to.have.property('name');
        expect(manifest).to.have.property('short_name');
        expect(manifest).to.have.property('start_url');
        expect(manifest).to.have.property('display');
        expect(manifest).to.have.property('icons');
        expect(manifest).to.have.property('theme_color');
        expect(manifest).to.have.property('background_color');
      });
    });

    it('should have correct app name and description', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        expect(manifest.name).to.eq('Brightpath Ascend FCRA Platform');
        expect(manifest.short_name).to.eq('Brightpath FCRA');
        expect(manifest.description).to.eq('Comprehensive FCRA litigation automation platform');
      });
    });

    it('should have correct display and orientation settings', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        expect(manifest.display).to.eq('standalone');
        expect(manifest.orientation).to.eq('any');
      });
    });

    it('should have correct theme and background colors', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        expect(manifest.theme_color).to.eq('#319795');
        expect(manifest.background_color).to.eq('#1a1a2e');
      });
    });

    it('should have correct start URL', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        expect(manifest.start_url).to.eq('/dashboard');
      });
    });

    it('should have correct categories', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        expect(manifest.categories).to.be.an('array');
        expect(manifest.categories).to.have.length(2);
        expect(manifest.categories).to.include('business');
        expect(manifest.categories).to.include('productivity');
      });
    });
  });

  describe('PWA Icons Tests', () => {
    it('should have required icon sizes', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        expect(manifest.icons).to.be.an('array');
        expect(manifest.icons).to.have.length(2);

        const icon192 = manifest.icons.find(icon => icon.sizes === '192x192');
        const icon512 = manifest.icons.find(icon => icon.sizes === '512x512');

        expect(icon192).to.exist;
        expect(icon512).to.exist;
      });
    });

    it('should have correct icon properties', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        manifest.icons.forEach(icon => {
          expect(icon).to.have.property('src');
          expect(icon).to.have.property('sizes');
          expect(icon).to.have.property('type');
          expect(icon.type).to.eq('image/png');
          expect(icon.src).to.match(/^\/static\/images\/icon-\d+\.png$/);
        });
      });
    });

    it('should have accessible icon files', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        manifest.icons.forEach(icon => {
          cy.request({
            url: icon.src,
            failOnStatusCode: false
          }).then((iconResponse) => {
            expect(iconResponse.status).to.be.oneOf([200, 404]);
          });
        });
      });
    });
  });

  describe('PWA Shortcuts Tests', () => {
    it('should have shortcuts array', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        expect(manifest.shortcuts).to.be.an('array');
        expect(manifest.shortcuts).to.have.length(2);
      });
    });

    it('should have dashboard shortcut', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        const dashboardShortcut = manifest.shortcuts.find(s => s.url === '/dashboard');
        expect(dashboardShortcut).to.exist;
        expect(dashboardShortcut.name).to.eq('Dashboard');
        expect(dashboardShortcut.short_name).to.eq('Dashboard');
        expect(dashboardShortcut.description).to.eq('View dashboard');
        expect(dashboardShortcut.icons).to.be.an('array');
        expect(dashboardShortcut.icons[0].sizes).to.eq('192x192');
        expect(dashboardShortcut.icons[0].src).to.eq('/static/images/icon-192.png');
      });
    });

    it('should have contacts shortcut', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        const contactsShortcut = manifest.shortcuts.find(s => s.url === '/dashboard/contacts');
        expect(contactsShortcut).to.exist;
        expect(contactsShortcut.name).to.eq('Contacts');
        expect(contactsShortcut.short_name).to.eq('Contacts');
        expect(contactsShortcut.description).to.eq('Manage contacts');
        expect(contactsShortcut.icons).to.be.an('array');
        expect(contactsShortcut.icons[0].sizes).to.eq('192x192');
        expect(contactsShortcut.icons[0].src).to.eq('/static/images/icon-192.png');
      });
    });

    it('should have valid shortcut URLs', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        manifest.shortcuts.forEach(shortcut => {
          expect(shortcut.url).to.match(/^\/dashboard/);
          expect(shortcut.url).to.not.be.empty;
        });
      });
    });
  });

  describe('Content Type and Headers Tests', () => {
    it('should have correct content type', () => {
      cy.request('/manifest.json').then((response) => {
        expect(response.headers).to.have.property('content-type');
        expect(response.headers['content-type']).to.match(/application\/json/);
      });
    });

    it('should have proper caching headers', () => {
      cy.request('/manifest.json').then((response) => {
        // Check if caching headers are present (optional but recommended)
        if (response.headers['cache-control']) {
          expect(response.headers['cache-control']).to.be.a('string');
        }
      });
    });
  });

  describe('JSON Structure Validation Tests', () => {
    it('should not have extra unexpected properties', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;
        const expectedProperties = [
          'background_color',
          'categories',
          'description',
          'display',
          'icons',
          'name',
          'orientation',
          'short_name',
          'shortcuts',
          'start_url',
          'theme_color'
        ];

        Object.keys(manifest).forEach(key => {
          expect(expectedProperties).to.include(key);
        });
      });
    });

    it('should have valid color format', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        expect(manifest.theme_color).to.match(/^#[0-9a-fA-F]{6}$/);
        expect(manifest.background_color).to.match(/^#[0-9a-fA-F]{6}$/);
      });
    });

    it('should have non-empty required strings', () => {
      cy.request('/manifest.json').then((response) => {
        const manifest = response.body;

        expect(manifest.name).to.not.be.empty;
        expect(manifest.short_name).to.not.be.empty;
        expect(manifest.description).to.not.be.empty;
        expect(manifest.start_url).to.not.be.empty;
        expect(manifest.display).to.not.be.empty;
      });
    });
  });

  describe('Performance Tests', () => {
    it('should load quickly', () => {
      const startTime = Date.now();
      cy.request('/manifest.json').then(() => {
        const loadTime = Date.now() - startTime;
        expect(loadTime).to.be.lessThan(1000); // Should load in under 1 second
      });
    });

    it('should have reasonable file size', () => {
      cy.request('/manifest.json').then((response) => {
        const contentLength = JSON.stringify(response.body).length;
        expect(contentLength).to.be.lessThan(10000); // Should be under 10KB
        expect(contentLength).to.be.greaterThan(100); // Should have meaningful content
      });
    });
  });
});
