/**
 * Theme Service - Light/Dark Mode Toggle
 *
 * Handles theme switching, localStorage persistence, and system preference detection.
 *
 * Usage:
 *   ThemeService.init()   - Initialize on page load (call this in DOMContentLoaded)
 *   ThemeService.toggle() - Toggle between light and dark mode
 *   ThemeService.setTheme('dark') - Set a specific theme
 *   ThemeService.getTheme() - Get current theme
 */

const ThemeService = {
    STORAGE_KEY: 'brightpath-theme',
    THEMES: {
        LIGHT: 'light',
        DARK: 'dark'
    },

    /**
     * Initialize the theme service.
     * Should be called on DOMContentLoaded.
     */
    init() {
        // Apply saved theme or system preference
        const theme = this.getSavedTheme() || this.getSystemPreference();
        this.applyTheme(theme, false); // Don't save on init to preserve system preference behavior

        // Watch for system preference changes
        this.watchSystemPreference();

        // Set up toggle button listeners
        this.setupToggleListeners();

        console.log('[ThemeService] Initialized with theme:', theme);
    },

    /**
     * Get the saved theme from localStorage.
     * @returns {string|null} The saved theme or null if not set
     */
    getSavedTheme() {
        try {
            return localStorage.getItem(this.STORAGE_KEY);
        } catch (e) {
            // localStorage might be blocked
            console.warn('[ThemeService] localStorage not available:', e);
            return null;
        }
    },

    /**
     * Get the system color scheme preference.
     * @returns {string} 'dark' or 'light'
     */
    getSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return this.THEMES.DARK;
        }
        return this.THEMES.LIGHT;
    },

    /**
     * Get the current theme.
     * @returns {string} The current theme
     */
    getTheme() {
        return document.documentElement.getAttribute('data-theme') || this.THEMES.LIGHT;
    },

    /**
     * Apply a theme to the document.
     * @param {string} theme - The theme to apply ('light' or 'dark')
     * @param {boolean} save - Whether to save to localStorage (default: true)
     */
    applyTheme(theme, save = true) {
        // Validate theme
        if (theme !== this.THEMES.LIGHT && theme !== this.THEMES.DARK) {
            theme = this.THEMES.LIGHT;
        }

        // Apply to document
        document.documentElement.setAttribute('data-theme', theme);

        // Update toggle buttons
        this.updateToggleButtons(theme);

        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);

        // Save preference
        if (save) {
            try {
                localStorage.setItem(this.STORAGE_KEY, theme);
            } catch (e) {
                console.warn('[ThemeService] Could not save theme:', e);
            }
        }

        // Dispatch custom event for other scripts to react
        window.dispatchEvent(new CustomEvent('themechange', {
            detail: { theme }
        }));
    },

    /**
     * Set a specific theme.
     * @param {string} theme - The theme to set ('light' or 'dark')
     */
    setTheme(theme) {
        this.applyTheme(theme, true);
    },

    /**
     * Toggle between light and dark mode.
     */
    toggle() {
        const current = this.getTheme();
        const newTheme = current === this.THEMES.DARK ? this.THEMES.LIGHT : this.THEMES.DARK;
        this.applyTheme(newTheme, true);
        console.log('[ThemeService] Toggled to:', newTheme);
    },

    /**
     * Reset to system preference.
     */
    resetToSystem() {
        try {
            localStorage.removeItem(this.STORAGE_KEY);
        } catch (e) {
            // Ignore
        }
        const systemTheme = this.getSystemPreference();
        this.applyTheme(systemTheme, false);
    },

    /**
     * Watch for system preference changes.
     */
    watchSystemPreference() {
        if (!window.matchMedia) return;

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

        const handleChange = (e) => {
            // Only auto-switch if user hasn't set a preference
            if (!this.getSavedTheme()) {
                this.applyTheme(e.matches ? this.THEMES.DARK : this.THEMES.LIGHT, false);
            }
        };

        // Modern browsers
        if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', handleChange);
        } else if (mediaQuery.addListener) {
            // Legacy Safari
            mediaQuery.addListener(handleChange);
        }
    },

    /**
     * Update all toggle buttons to reflect the current theme.
     * @param {string} theme - The current theme
     */
    updateToggleButtons(theme) {
        const buttons = document.querySelectorAll('[data-theme-toggle]');
        const isDark = theme === this.THEMES.DARK;

        buttons.forEach(btn => {
            // Update aria-label
            btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
            btn.setAttribute('title', isDark ? 'Switch to light mode' : 'Switch to dark mode');

            // Update icon (supports both emoji and icon elements)
            const iconEl = btn.querySelector('.theme-icon');
            if (iconEl) {
                iconEl.innerHTML = isDark ? this.getSunIcon() : this.getMoonIcon();
            } else if (btn.classList.contains('theme-toggle-emoji')) {
                btn.textContent = isDark ? '☀️' : '🌙';
            }

            // Update button state
            btn.setAttribute('data-current-theme', theme);
        });
    },

    /**
     * Set up click listeners for toggle buttons.
     */
    setupToggleListeners() {
        document.addEventListener('click', (e) => {
            const toggleBtn = e.target.closest('[data-theme-toggle]');
            if (toggleBtn) {
                e.preventDefault();
                this.toggle();
            }
        });
    },

    /**
     * Update meta theme-color for mobile browsers.
     * @param {string} theme - The current theme
     */
    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');

        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }

        // Set appropriate color for mobile browser UI
        metaThemeColor.content = theme === this.THEMES.DARK ? '#0f172a' : '#ffffff';
    },

    /**
     * Get sun icon SVG for light mode indicator.
     * @returns {string} SVG markup
     */
    getSunIcon() {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>`;
    },

    /**
     * Get moon icon SVG for dark mode indicator.
     * @returns {string} SVG markup
     */
    getMoonIcon() {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
        </svg>`;
    }
};

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ThemeService.init());
} else {
    // DOM already loaded
    ThemeService.init();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeService;
}
