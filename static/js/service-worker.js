const CACHE_NAME = 'gls-v1';
const OFFLINE_URL = '/offline/';

const urlsToCache = [
  '/',
  '/static/css/base.css',
  '/static/css/pwa.css',
  '/static/js/pwa.js',
  '/static/images/logo.png',
  OFFLINE_URL
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match(OFFLINE_URL);
        })
    );
  } else {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          return response || fetch(event.request);
        })
    );
  }
});