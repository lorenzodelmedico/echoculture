self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', (event) => {
  const headers = new Headers(event.request.headers);
  headers.set('ngrok-skip-browser-warning', '1');
  event.respondWith(fetch(event.request, { headers }));
});
