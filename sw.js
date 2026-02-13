const CACHE_NAME = 'sabellesings-v3';
const ASSETS = [
  '/',
  '/index.html',
  '/retro-styles.css',
  '/retro-scripts.js',
  '/favicon.ico',
  '/favicon.svg',
  '/favicon-96x96.png',
  '/apple-touch-icon.png',
  '/site.webmanifest',
  '/images/party-boy.png',
  '/images/tell-me-your-heart.png',
  '/images/im-blushin.png',
  '/images/tainted.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((key) => (key !== CACHE_NAME ? caches.delete(key) : null)))
    )
  );
  self.clients.claim();
});

/**
 * Caching strategies:
 *   Network-first  → HTML, CSS, JS  (always fresh when online, cache fallback offline)
 *   Cache-first    → images, fonts, favicons  (rarely change, saves bandwidth)
 */
const CACHE_FIRST_EXTENSIONS = /\.(?:png|jpe?g|gif|webp|svg|ico|woff2?|ttf|eot|webmanifest)$/i;

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const requestUrl = new URL(request.url);
  if (requestUrl.origin !== self.location.origin) return;

  // Determine strategy based on file type
  const useCacheFirst = CACHE_FIRST_EXTENSIONS.test(requestUrl.pathname);

  if (useCacheFirst) {
    // Cache-first: serve from cache instantly, fetch only on miss
    event.respondWith(
      caches.match(request).then((cached) =>
        cached || fetch(request).then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          return response;
        })
      )
    );
  } else {
    // Network-first: always try fresh content, fall back to cache offline
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() => caches.match(request).then((r) => r || caches.match('/index.html')))
    );
  }
});

