importScripts('https://storage.googleapis.com/workbox-cdn/releases/5.1.2/workbox-sw.js');

const cacheName = 'ChocolatePWACache';

const offlineFallbackPage = '/offline';

const filesToCache = [
    '/',

    '/static/css/style.css',

    '/static/js/actor.js',
    '/static/js/allFilms.js',
    '/static/js/allSeries.js',
    '/static/js/consoles.js',
    '/static/js/createAccount.js',
    '/static/js/game.js',
    '/static/js/games.js',
    '/static/js/login.js',
    '/static/js/main.js',
    '/static/js/movie.js',
    '/static/js/profil.js',
    '/static/js/season.js',
    '/static/js/serie.js',
    '/static/js/settings.js',

    
    '/templates/index.html',
    '/templates/actor.html',
    '/templates/allFilms.html',
    '/templates/allSeries.html',
    '/templates/consoles.html',
    '/templates/createAccount.html',
    '/templates/film.html',
    '/templates/game.html',
    '/templates/games.html',
    '/templates/header.html',
    '/templates/index.html',
    '/templates/login.html',
    '/templates/popup.html',
    '/templates/profil.html',
    '/templates/season.html',
    '/templates/serie.html',
    '/templates/settings.html',

    '/static/images/broken.png',
    '/static/images/brokenBanner.png',
    '/static/images/defaultUserProfilePic.png',
    '/static/images/loader.gif',
    '/static/images/logo.ico',
    '/static/images/logo.png',
];


self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener('install', async (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.add(offlineFallbackPage))
  );
});

if (workbox.navigationPreload.isSupported()) {
  workbox.navigationPreload.enable();
}

self.addEventListener('activate', function(e) {
  console.log('[ServiceWorker] Activate');
    e.waitUntil(
    caches.keys().then(function(keyList) {
      return Promise.all(keyList.map(function(key) {
        if (key !== cacheName) {
          console.log('[ServiceWorker] Removing old cache', key);
          return caches.delete(key);
        }
      }));
    })
  );
  return self.clients.claim();
});
  
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const preloadResp = await event.preloadResponse;

        if (preloadResp) {
          return preloadResp;
        }

        const networkResp = await fetch(event.request);
        return networkResp;
      } catch (error) {

        const cache = await caches.open(CACHE);
        const cachedResp = await cache.match(offlineFallbackPage);
        return cachedResp;
      }
    })());
  }
});