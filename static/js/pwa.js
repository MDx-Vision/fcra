/**
 * PWA Install & Service Worker Management
 * Brightpath Ascend Group Client Portal
 */

const PWA = {
    deferredPrompt: null,
    isInstalled: false,
    swRegistration: null,

    /**
     * Initialize PWA features
     */
    init() {
        this.checkIfInstalled();
        this.registerServiceWorker();
        this.setupInstallPrompt();
        this.setupUpdateHandler();
    },

    /**
     * Check if app is already installed
     */
    checkIfInstalled() {
        // Check if running in standalone mode (installed PWA)
        if (window.matchMedia('(display-mode: standalone)').matches) {
            this.isInstalled = true;
            console.log('[PWA] App is installed and running in standalone mode');
            return;
        }

        // Check iOS standalone
        if (window.navigator.standalone === true) {
            this.isInstalled = true;
            console.log('[PWA] App is installed (iOS standalone)');
            return;
        }

        // Listen for display mode changes
        window.matchMedia('(display-mode: standalone)').addEventListener('change', (e) => {
            if (e.matches) {
                this.isInstalled = true;
                this.hideInstallPrompt();
            }
        });
    },

    /**
     * Register service worker
     */
    async registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.log('[PWA] Service workers not supported');
            return;
        }

        try {
            this.swRegistration = await navigator.serviceWorker.register('/static/sw.js', {
                scope: '/'
            });

            console.log('[PWA] Service worker registered:', this.swRegistration.scope);

            // Check for updates periodically
            setInterval(() => {
                this.swRegistration.update();
            }, 60 * 60 * 1000); // Check every hour

        } catch (error) {
            console.error('[PWA] Service worker registration failed:', error);
        }
    },

    /**
     * Setup install prompt handler
     */
    setupInstallPrompt() {
        // Capture the install prompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('[PWA] Install prompt captured');

            // Prevent default browser prompt
            e.preventDefault();

            // Store for later use
            this.deferredPrompt = e;

            // Show custom install UI
            this.showInstallPrompt();
        });

        // Handle successful installation
        window.addEventListener('appinstalled', () => {
            console.log('[PWA] App installed successfully');
            this.isInstalled = true;
            this.deferredPrompt = null;
            this.hideInstallPrompt();

            // Track installation (if analytics available)
            if (typeof gtag !== 'undefined') {
                gtag('event', 'pwa_install', {
                    event_category: 'PWA',
                    event_label: 'App Installed'
                });
            }
        });
    },

    /**
     * Show custom install prompt UI
     */
    showInstallPrompt() {
        // Don't show if already installed or prompt not available
        if (this.isInstalled || !this.deferredPrompt) return;

        // Check if user has dismissed before (24 hour cooldown)
        const dismissedAt = localStorage.getItem('pwa-prompt-dismissed');
        if (dismissedAt) {
            const hoursSinceDismissed = (Date.now() - parseInt(dismissedAt)) / (1000 * 60 * 60);
            if (hoursSinceDismissed < 24) return;
        }

        // Create install banner if not exists
        let banner = document.getElementById('pwa-install-banner');
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'pwa-install-banner';
            banner.innerHTML = `
                <div class="pwa-install-content">
                    <img src="/static/images/pwa/icon-72x72.png" alt="Brightpath" class="pwa-install-icon">
                    <div class="pwa-install-text">
                        <strong>Install Brightpath</strong>
                        <span>Add to home screen for quick access</span>
                    </div>
                    <div class="pwa-install-buttons">
                        <button class="pwa-install-btn" onclick="PWA.triggerInstall()">Install</button>
                        <button class="pwa-dismiss-btn" onclick="PWA.dismissInstallPrompt()">Not now</button>
                    </div>
                </div>
            `;
            document.body.appendChild(banner);
        }

        // Show with animation
        setTimeout(() => banner.classList.add('show'), 100);
    },

    /**
     * Hide install prompt
     */
    hideInstallPrompt() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.classList.remove('show');
            setTimeout(() => banner.remove(), 300);
        }
    },

    /**
     * Dismiss install prompt with cooldown
     */
    dismissInstallPrompt() {
        localStorage.setItem('pwa-prompt-dismissed', Date.now().toString());
        this.hideInstallPrompt();
    },

    /**
     * Trigger native install prompt
     */
    async triggerInstall() {
        if (!this.deferredPrompt) {
            console.log('[PWA] No install prompt available');
            return;
        }

        // Show native prompt
        this.deferredPrompt.prompt();

        // Wait for user response
        const { outcome } = await this.deferredPrompt.userChoice;
        console.log('[PWA] Install prompt outcome:', outcome);

        // Clear the prompt
        this.deferredPrompt = null;
        this.hideInstallPrompt();
    },

    /**
     * Setup update handler for new service worker versions
     */
    setupUpdateHandler() {
        if (!('serviceWorker' in navigator)) return;

        navigator.serviceWorker.addEventListener('controllerchange', () => {
            console.log('[PWA] New service worker activated');
            // Optionally show update notification
            this.showUpdateNotification();
        });
    },

    /**
     * Show update notification
     */
    showUpdateNotification() {
        // Create update toast if not exists
        let toast = document.getElementById('pwa-update-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'pwa-update-toast';
            toast.innerHTML = `
                <div class="pwa-toast-content">
                    <span>New version available!</span>
                    <button onclick="PWA.reloadApp()">Refresh</button>
                    <button onclick="PWA.dismissUpdate()">Later</button>
                </div>
            `;
            document.body.appendChild(toast);
        }

        setTimeout(() => toast.classList.add('show'), 100);
    },

    /**
     * Dismiss update notification
     */
    dismissUpdate() {
        const toast = document.getElementById('pwa-update-toast');
        if (toast) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }
    },

    /**
     * Reload app with new version
     */
    reloadApp() {
        window.location.reload();
    },

    /**
     * Clear all caches (for debugging)
     */
    async clearCaches() {
        if (this.swRegistration && this.swRegistration.active) {
            this.swRegistration.active.postMessage({ type: 'CLEAR_CACHE' });
        }

        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(name => caches.delete(name)));
        console.log('[PWA] All caches cleared');
    },

    /**
     * Check online status
     */
    isOnline() {
        return navigator.onLine;
    },

    /**
     * Setup online/offline handlers
     */
    setupConnectivityHandlers() {
        window.addEventListener('online', () => {
            console.log('[PWA] Back online');
            this.showConnectivityToast('Back online', 'success');
        });

        window.addEventListener('offline', () => {
            console.log('[PWA] Went offline');
            this.showConnectivityToast('You are offline', 'warning');
        });
    },

    /**
     * Show connectivity toast
     */
    showConnectivityToast(message, type) {
        let toast = document.getElementById('pwa-connectivity-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'pwa-connectivity-toast';
            document.body.appendChild(toast);
        }

        toast.className = `pwa-connectivity-toast ${type}`;
        toast.textContent = message;
        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
};

// Add PWA styles
const pwaStyles = document.createElement('style');
pwaStyles.textContent = `
    /* PWA Install Banner */
    #pwa-install-banner {
        position: fixed;
        bottom: 80px;
        left: 16px;
        right: 16px;
        background: var(--theme-bg-card, #fff);
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        z-index: 9999;
        transform: translateY(200%);
        transition: transform 0.3s ease;
        border: 1px solid var(--theme-border, #e2e8f0);
    }

    #pwa-install-banner.show {
        transform: translateY(0);
    }

    .pwa-install-content {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
    }

    .pwa-install-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
    }

    .pwa-install-text {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .pwa-install-text strong {
        font-size: 16px;
        color: var(--theme-text, #1a1a2e);
    }

    .pwa-install-text span {
        font-size: 13px;
        color: var(--theme-text-secondary, #64748b);
    }

    .pwa-install-buttons {
        display: flex;
        gap: 8px;
    }

    .pwa-install-btn {
        background: #14b8a6;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        font-size: 14px;
    }

    .pwa-install-btn:hover {
        background: #0d9488;
    }

    .pwa-dismiss-btn {
        background: transparent;
        color: var(--theme-text-secondary, #64748b);
        border: none;
        padding: 8px 12px;
        cursor: pointer;
        font-size: 14px;
    }

    /* PWA Update Toast */
    #pwa-update-toast {
        position: fixed;
        top: 16px;
        left: 50%;
        transform: translateX(-50%) translateY(-200%);
        background: #0f172a;
        color: white;
        padding: 12px 20px;
        border-radius: 12px;
        z-index: 10000;
        transition: transform 0.3s ease;
    }

    #pwa-update-toast.show {
        transform: translateX(-50%) translateY(0);
    }

    .pwa-toast-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .pwa-toast-content button {
        background: #14b8a6;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
    }

    .pwa-toast-content button:last-child {
        background: transparent;
        color: #94a3b8;
    }

    /* Connectivity Toast */
    .pwa-connectivity-toast {
        position: fixed;
        top: 16px;
        left: 50%;
        transform: translateX(-50%) translateY(-100px);
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 10000;
        font-weight: 500;
        transition: transform 0.3s ease;
    }

    .pwa-connectivity-toast.show {
        transform: translateX(-50%) translateY(0);
    }

    .pwa-connectivity-toast.success {
        background: #22c55e;
        color: white;
    }

    .pwa-connectivity-toast.warning {
        background: #f59e0b;
        color: white;
    }

    /* Mobile adjustments */
    @media (max-width: 480px) {
        #pwa-install-banner {
            left: 8px;
            right: 8px;
            bottom: 70px;
        }

        .pwa-install-content {
            flex-wrap: wrap;
        }

        .pwa-install-buttons {
            width: 100%;
            justify-content: flex-end;
            margin-top: 8px;
        }
    }
`;
document.head.appendChild(pwaStyles);

// Initialize PWA when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => PWA.init());
} else {
    PWA.init();
}

// Also setup connectivity handlers
PWA.setupConnectivityHandlers();

// Export for global access
window.PWA = PWA;
