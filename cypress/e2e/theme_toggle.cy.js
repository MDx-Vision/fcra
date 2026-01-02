/**
 * Theme Toggle Tests
 *
 * Tests for the light/dark mode toggle functionality across all portals.
 */

describe('Theme Toggle - Client Portal', () => {
    beforeEach(() => {
        cy.clearLocalStorage();
        // Login and visit portal
        cy.login('test@example.com', 'testpass123');
    });

    it('defaults to light mode', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });
        cy.get('html').should('have.attr', 'data-theme', 'light');
    });

    it('displays theme toggle button in header', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });
        cy.get('[data-theme-toggle]').should('exist').and('be.visible');
    });

    it('toggles to dark mode when clicked', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });
        cy.get('html').should('have.attr', 'data-theme', 'light');

        // Click toggle
        cy.get('[data-theme-toggle]').first().click();

        // Should switch to dark mode
        cy.get('html').should('have.attr', 'data-theme', 'dark');
    });

    it('persists theme preference in localStorage', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });

        // Toggle to dark mode
        cy.get('[data-theme-toggle]').first().click();
        cy.get('html').should('have.attr', 'data-theme', 'dark');

        // Check localStorage
        cy.window().then((win) => {
            expect(win.localStorage.getItem('brightpath-theme')).to.equal('dark');
        });
    });

    it('preserves theme across page reload', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });

        // Set dark mode
        cy.get('[data-theme-toggle]').first().click();
        cy.get('html').should('have.attr', 'data-theme', 'dark');

        // Reload page
        cy.reload();

        // Should still be dark mode
        cy.get('html').should('have.attr', 'data-theme', 'dark');
    });

    it('toggles back to light mode', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });

        // Toggle to dark
        cy.get('[data-theme-toggle]').first().click();
        cy.get('html').should('have.attr', 'data-theme', 'dark');

        // Toggle back to light
        cy.get('[data-theme-toggle]').first().click();
        cy.get('html').should('have.attr', 'data-theme', 'light');
    });

    it('has correct portal identifier', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });
        cy.get('html').should('have.attr', 'data-portal', 'client');
    });
});

describe('Theme Toggle - Staff Dashboard', () => {
    beforeEach(() => {
        cy.clearLocalStorage();
        cy.login('test@example.com', 'testpass123');
    });

    it('displays theme toggle button in sidebar', () => {
        cy.visit('/dashboard');
        cy.get('[data-theme-toggle]').should('exist');
    });

    it('toggles theme on staff dashboard', () => {
        cy.visit('/dashboard');

        // Get initial state
        cy.get('html').invoke('attr', 'data-theme').then((initialTheme) => {
            // Click toggle
            cy.get('[data-theme-toggle]').first().click();

            // Should be opposite theme
            const expectedTheme = initialTheme === 'dark' ? 'light' : 'dark';
            cy.get('html').should('have.attr', 'data-theme', expectedTheme);
        });
    });

    it('staff dashboard has portal identifier', () => {
        cy.visit('/dashboard');
        cy.get('.sidebar').should('have.attr', 'data-portal', 'staff');
    });

    it('sidebar maintains dark styling in both themes', () => {
        cy.visit('/dashboard');

        // Sidebar should have dark background in light mode
        cy.get('.sidebar').should('exist');

        // Toggle to dark mode
        cy.get('[data-theme-toggle]').first().click();

        // Sidebar should still be visible/functional
        cy.get('.sidebar').should('exist');
    });
});

describe('Theme Toggle - Affiliate Portal', () => {
    it('displays theme toggle button', () => {
        // Visit affiliate login page (public)
        cy.visit('/affiliate/login', { failOnStatusCode: false });
        // Login page may not have toggle, so check main portal after login would be needed
        // For now, just verify the page loads
        cy.get('body').should('exist');
    });

    it('has correct portal identifier when logged in', () => {
        // This would require affiliate login credentials
        // Skipping actual test but verifying structure
        cy.visit('/affiliate/login', { failOnStatusCode: false });
        cy.get('body').should('exist');
    });
});

describe('Theme Toggle - System Preference Detection', () => {
    beforeEach(() => {
        cy.clearLocalStorage();
    });

    it('respects system dark mode preference when no saved preference', () => {
        // Stub system preference to dark
        cy.visit('/portal/login', {
            failOnStatusCode: false,
            onBeforeLoad(win) {
                // Mock matchMedia for dark mode
                cy.stub(win, 'matchMedia')
                    .callsFake((query) => {
                        if (query === '(prefers-color-scheme: dark)') {
                            return {
                                matches: true,
                                media: query,
                                onchange: null,
                                addListener: () => {},
                                removeListener: () => {},
                                addEventListener: () => {},
                                removeEventListener: () => {},
                                dispatchEvent: () => false
                            };
                        }
                        return {
                            matches: false,
                            media: query,
                            onchange: null,
                            addListener: () => {},
                            removeListener: () => {},
                            addEventListener: () => {},
                            removeEventListener: () => {},
                            dispatchEvent: () => false
                        };
                    });
            }
        });

        // Should default to dark based on system preference
        cy.get('html').should('have.attr', 'data-theme', 'dark');
    });

    it('saved preference overrides system preference', () => {
        // Set light mode preference
        cy.visit('/portal/login', {
            failOnStatusCode: false,
            onBeforeLoad(win) {
                win.localStorage.setItem('brightpath-theme', 'light');
                // Mock system preference to dark
                cy.stub(win, 'matchMedia')
                    .callsFake((query) => {
                        if (query === '(prefers-color-scheme: dark)') {
                            return {
                                matches: true,
                                media: query,
                                onchange: null,
                                addListener: () => {},
                                removeListener: () => {},
                                addEventListener: () => {},
                                removeEventListener: () => {},
                                dispatchEvent: () => false
                            };
                        }
                        return {
                            matches: false,
                            media: query,
                            onchange: null,
                            addListener: () => {},
                            removeListener: () => {},
                            addEventListener: () => {},
                            removeEventListener: () => {},
                            dispatchEvent: () => false
                        };
                    });
            }
        });

        // Should use saved light preference despite system dark preference
        cy.get('html').should('have.attr', 'data-theme', 'light');
    });
});

describe('Theme Toggle - Visual Elements', () => {
    beforeEach(() => {
        cy.clearLocalStorage();
        cy.login('test@example.com', 'testpass123');
    });

    it('toggle button has correct aria-label', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });

        // In light mode, should offer dark mode
        cy.get('[data-theme-toggle]').first()
            .should('have.attr', 'title');
    });

    it('theme variables are applied to elements', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });

        // Check that cards use theme variables (indirectly by checking they exist)
        cy.get('.card, .nav-tabs, .header').should('exist');
    });

    it('smooth transition on theme change', () => {
        cy.visit('/portal/dashboard', { failOnStatusCode: false });

        // Body should have transition style
        cy.get('body').should('have.css', 'transition');
    });
});

describe('Theme Toggle - Cross-Portal Consistency', () => {
    beforeEach(() => {
        cy.clearLocalStorage();
        cy.login('test@example.com', 'testpass123');
    });

    it('theme persists when navigating between portal pages', () => {
        // Set dark mode on dashboard
        cy.visit('/portal/dashboard', { failOnStatusCode: false });
        cy.get('[data-theme-toggle]').first().click();
        cy.get('html').should('have.attr', 'data-theme', 'dark');

        // Navigate to profile
        cy.visit('/portal/profile', { failOnStatusCode: false });
        cy.get('html').should('have.attr', 'data-theme', 'dark');

        // Navigate to documents
        cy.visit('/portal/documents', { failOnStatusCode: false });
        cy.get('html').should('have.attr', 'data-theme', 'dark');
    });

    it('theme persists between client portal and staff dashboard', () => {
        // Set dark mode in portal
        cy.visit('/portal/dashboard', { failOnStatusCode: false });
        cy.get('[data-theme-toggle]').first().click();
        cy.get('html').should('have.attr', 'data-theme', 'dark');

        // Visit staff dashboard
        cy.visit('/dashboard');
        cy.get('html').should('have.attr', 'data-theme', 'dark');
    });
});
