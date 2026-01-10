/**
 * Push Notifications Client
 * Brightpath Ascend FCRA Platform
 *
 * Usage:
 *   <script src="/static/js/push-notifications.js"></script>
 *   <button onclick="PushNotifications.subscribe()">Enable Notifications</button>
 */

const PushNotifications = {
    swRegistration: null,
    subscription: null,
    isSupported: false,
    isSubscribed: false,

    /**
     * Initialize push notifications
     */
    async init() {
        // Check browser support
        if (!('serviceWorker' in navigator)) {
            console.log('[Push] Service workers not supported');
            return false;
        }

        if (!('PushManager' in window)) {
            console.log('[Push] Push notifications not supported');
            return false;
        }

        this.isSupported = true;

        try {
            // Register service worker
            this.swRegistration = await navigator.serviceWorker.register('/static/sw.js');
            console.log('[Push] Service worker registered');

            // Check current subscription status
            this.subscription = await this.swRegistration.pushManager.getSubscription();
            this.isSubscribed = this.subscription !== null;

            console.log('[Push] Subscription status:', this.isSubscribed);

            // Update UI
            this.updateUI();

            return true;
        } catch (error) {
            console.error('[Push] Initialization error:', error);
            return false;
        }
    },

    /**
     * Subscribe to push notifications
     */
    async subscribe() {
        if (!this.isSupported) {
            this.showMessage('Push notifications are not supported in this browser', 'error');
            return false;
        }

        try {
            // Get VAPID public key from server
            const keyResponse = await fetch('/api/push/vapid-public-key');
            const keyData = await keyResponse.json();

            if (!keyData.success) {
                this.showMessage('Push notifications are not configured on the server', 'error');
                return false;
            }

            // Convert VAPID key to Uint8Array
            const vapidPublicKey = this.urlBase64ToUint8Array(keyData.publicKey);

            // Request permission
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                this.showMessage('Notification permission denied', 'error');
                return false;
            }

            // Subscribe to push
            this.subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: vapidPublicKey,
            });

            console.log('[Push] Subscription created:', this.subscription);

            // Send subscription to server
            const subscribeResponse = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    endpoint: this.subscription.endpoint,
                    keys: {
                        p256dh: this.arrayBufferToBase64(this.subscription.getKey('p256dh')),
                        auth: this.arrayBufferToBase64(this.subscription.getKey('auth')),
                    },
                }),
            });

            const subscribeData = await subscribeResponse.json();

            if (subscribeData.success) {
                this.isSubscribed = true;
                this.updateUI();
                this.showMessage('Push notifications enabled!', 'success');
                return true;
            } else {
                throw new Error(subscribeData.error || 'Failed to save subscription');
            }
        } catch (error) {
            console.error('[Push] Subscribe error:', error);
            this.showMessage('Failed to enable notifications: ' + error.message, 'error');
            return false;
        }
    },

    /**
     * Unsubscribe from push notifications
     */
    async unsubscribe() {
        if (!this.subscription) {
            return true;
        }

        try {
            // Unsubscribe from push manager
            await this.subscription.unsubscribe();

            // Notify server
            await fetch('/api/push/unsubscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ endpoint: this.subscription.endpoint }),
            });

            this.subscription = null;
            this.isSubscribed = false;
            this.updateUI();
            this.showMessage('Push notifications disabled', 'success');

            return true;
        } catch (error) {
            console.error('[Push] Unsubscribe error:', error);
            this.showMessage('Failed to disable notifications', 'error');
            return false;
        }
    },

    /**
     * Toggle subscription
     */
    async toggle() {
        if (this.isSubscribed) {
            return this.unsubscribe();
        } else {
            return this.subscribe();
        }
    },

    /**
     * Update notification preferences
     */
    async updatePreferences(preferences) {
        try {
            const response = await fetch('/api/push/subscriptions');
            const data = await response.json();

            if (!data.success || !data.subscriptions.length) {
                return false;
            }

            const subscriptionId = data.subscriptions[0].id;

            const updateResponse = await fetch(`/api/push/subscriptions/${subscriptionId}/preferences`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preferences),
            });

            return (await updateResponse.json()).success;
        } catch (error) {
            console.error('[Push] Update preferences error:', error);
            return false;
        }
    },

    /**
     * Get current subscription info
     */
    async getSubscriptionInfo() {
        try {
            const response = await fetch('/api/push/subscriptions');
            const data = await response.json();
            return data.success ? data.subscriptions : [];
        } catch (error) {
            console.error('[Push] Get subscriptions error:', error);
            return [];
        }
    },

    /**
     * Update UI elements based on subscription status
     */
    updateUI() {
        // Update all notification toggle buttons
        document.querySelectorAll('[data-push-toggle]').forEach((btn) => {
            if (this.isSubscribed) {
                btn.classList.add('active', 'subscribed');
                btn.textContent = btn.dataset.subscribedText || 'Notifications On';
            } else {
                btn.classList.remove('active', 'subscribed');
                btn.textContent = btn.dataset.unsubscribedText || 'Enable Notifications';
            }
        });

        // Update status indicators
        document.querySelectorAll('[data-push-status]').forEach((el) => {
            el.textContent = this.isSubscribed ? 'Enabled' : 'Disabled';
            el.className = this.isSubscribed ? 'push-status-enabled' : 'push-status-disabled';
        });

        // Show/hide preference panels
        document.querySelectorAll('[data-push-preferences]').forEach((panel) => {
            panel.style.display = this.isSubscribed ? 'block' : 'none';
        });
    },

    /**
     * Show a message to the user
     */
    showMessage(message, type = 'info') {
        // Check for existing toast container
        let container = document.getElementById('push-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'push-toast-container';
            container.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 10000;
            `;
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `push-toast push-toast-${type}`;
        toast.style.cssText = `
            padding: 12px 20px;
            margin-top: 10px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
        `;
        toast.textContent = message;

        container.appendChild(toast);

        // Add animation keyframes if not exists
        if (!document.getElementById('push-toast-styles')) {
            const style = document.createElement('style');
            style.id = 'push-toast-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        // Auto-remove after 4 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },

    /**
     * Convert URL-safe base64 to Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
    },

    /**
     * Convert ArrayBuffer to base64
     */
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary)
            .replace(/\+/g, '-')
            .replace(/\//g, '_')
            .replace(/=+$/, '');
    },
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => PushNotifications.init());
} else {
    PushNotifications.init();
}
