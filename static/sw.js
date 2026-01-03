/**
 * Service Worker for Brightpath Ascend PWA
 * Handles push notifications, offline caching, and background sync
 */

const CACHE_VERSION = 'v2';
const STATIC_CACHE = `brightpath-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `brightpath-dynamic-${CACHE_VERSION}`;
const API_CACHE = `brightpath-api-${CACHE_VERSION}`;

// Static assets to cache on install
const STATIC_ASSETS = [
    '/portal/offline',
    '/static/css/portal-redesign.css',
    '/static/css/theme-variables.css',
    '/static/js/theme-service.js',
    '/static/js/push-notifications.js',
    '/static/images/pwa/icon-192x192.png',
    '/static/images/pwa/icon-512x512.png',
    '/static/images/pwa/apple-touch-icon.png',
    '/static/images/logo.png',
    '/static/manifest.json',
];

// API endpoints to cache (network-first)
const API_ROUTES = [
    '/portal/api/',
    '/api/portal/',
];

// Pages to cache on visit (stale-while-revalidate)
const CACHEABLE_PAGES = [
    '/portal/dashboard',
    '/portal/documents',
    '/portal/status',
    '/portal/profile',
    '/portal/messages',
    '/portal/booking',
    '/portal/learn',
];

// ============================================================================
// INSTALL EVENT - Cache critical static assets
// ============================================================================
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');

    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS.map(url => {
                    return new Request(url, { cache: 'reload' });
                })).catch(err => {
                    console.warn('[SW] Some static assets failed to cache:', err);
                });
            })
            .then(() => self.skipWaiting())
    );
});

// ============================================================================
// ACTIVATE EVENT - Clean up old caches
// ============================================================================
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');

    const currentCaches = [STATIC_CACHE, DYNAMIC_CACHE, API_CACHE];

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => !currentCaches.includes(name))
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// ============================================================================
// FETCH EVENT - Handle network requests with caching strategies
// ============================================================================
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Skip external requests
    if (!url.origin.includes(self.location.origin)) {
        return;
    }

    // Handle API requests - Network First
    if (isApiRequest(url.pathname)) {
        event.respondWith(networkFirst(event.request, API_CACHE));
        return;
    }

    // Handle static assets - Cache First
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirst(event.request, STATIC_CACHE));
        return;
    }

    // Handle navigation requests - Stale While Revalidate
    if (event.request.mode === 'navigate' || isPortalPage(url.pathname)) {
        event.respondWith(staleWhileRevalidate(event.request, DYNAMIC_CACHE));
        return;
    }

    // Default - Network First with fallback
    event.respondWith(networkFirst(event.request, DYNAMIC_CACHE));
});

// ============================================================================
// CACHING STRATEGIES
// ============================================================================

// Cache First - Good for static assets that rarely change
async function cacheFirst(request, cacheName) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network request failed:', error);
        return new Response('Offline', { status: 503 });
    }
}

// Network First - Good for dynamic content and API calls
async function networkFirst(request, cacheName) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // For navigation requests, return offline page
        if (request.mode === 'navigate') {
            return caches.match('/portal/offline');
        }

        return new Response(JSON.stringify({ error: 'Offline' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Stale While Revalidate - Good for pages that need to be fast but also fresh
async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);

    const fetchPromise = fetch(request)
        .then((networkResponse) => {
            if (networkResponse.ok) {
                cache.put(request, networkResponse.clone());
            }
            return networkResponse;
        })
        .catch(() => {
            // If network fails and we have no cache, return offline page
            if (!cachedResponse && request.mode === 'navigate') {
                return caches.match('/portal/offline');
            }
            return cachedResponse;
        });

    // Return cached response immediately, or wait for network
    return cachedResponse || fetchPromise;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function isApiRequest(pathname) {
    return API_ROUTES.some(route => pathname.startsWith(route));
}

function isStaticAsset(pathname) {
    return pathname.startsWith('/static/') ||
           pathname.endsWith('.js') ||
           pathname.endsWith('.css') ||
           pathname.endsWith('.png') ||
           pathname.endsWith('.jpg') ||
           pathname.endsWith('.svg') ||
           pathname.endsWith('.woff2') ||
           pathname.endsWith('.ico');
}

function isPortalPage(pathname) {
    return pathname.startsWith('/portal/');
}

// ============================================================================
// PUSH NOTIFICATIONS
// ============================================================================

self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');

    let data = {
        title: 'Brightpath Ascend',
        body: 'You have a new notification',
        icon: '/static/images/pwa/notification.png',
        badge: '/static/images/pwa/badge.png',
        tag: 'default',
        data: { url: '/portal/dashboard' },
    };

    if (event.data) {
        try {
            const payload = event.data.json();
            data = {
                title: payload.title || data.title,
                body: payload.body || data.body,
                icon: payload.icon || data.icon,
                badge: payload.badge || data.badge,
                tag: payload.tag || data.tag,
                data: payload.data || data.data,
            };
        } catch (e) {
            console.error('[SW] Error parsing push data:', e);
        }
    }

    const options = {
        body: data.body,
        icon: data.icon,
        badge: data.badge,
        tag: data.tag,
        data: data.data,
        vibrate: [100, 50, 100],
        requireInteraction: false,
        actions: [
            { action: 'open', title: 'View' },
            { action: 'close', title: 'Dismiss' },
        ],
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked');

    event.notification.close();

    if (event.action === 'close') {
        return;
    }

    const urlToOpen = event.notification.data?.url || '/portal/dashboard';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.navigate(urlToOpen);
                        return client.focus();
                    }
                }
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Notification close handler
self.addEventListener('notificationclose', (event) => {
    console.log('[SW] Notification closed');
});

// ============================================================================
// BACKGROUND SYNC (for offline form submissions)
// ============================================================================

self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync triggered:', event.tag);

    if (event.tag === 'sync-messages') {
        event.waitUntil(syncMessages());
    }

    if (event.tag === 'sync-documents') {
        event.waitUntil(syncDocuments());
    }
});

async function syncMessages() {
    // Get pending messages from IndexedDB and send them
    console.log('[SW] Syncing offline messages...');
    // Implementation would use IndexedDB to store and sync
}

async function syncDocuments() {
    // Get pending document uploads from IndexedDB and upload them
    console.log('[SW] Syncing offline documents...');
    // Implementation would use IndexedDB to store and sync
}

// ============================================================================
// MESSAGE HANDLER (for communication with main thread)
// ============================================================================

self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((name) => caches.delete(name))
                );
            })
        );
    }

    if (event.data.type === 'CACHE_URLS') {
        const urls = event.data.urls || [];
        event.waitUntil(
            caches.open(DYNAMIC_CACHE).then((cache) => {
                return cache.addAll(urls);
            })
        );
    }
});

console.log('[SW] Service worker loaded');
