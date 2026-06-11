/* Footballisimo Service Worker v4 — офлайн-кэш */
const CACHE = 'footballisimo-v4';  // ← увеличена версия, сбрасывает старый кэш
const ASSETS = ['./', './index.html', './manifest.json'];

self.addEventListener('install', (e) => {
  self.skipWaiting();  // активируем сразу, не ждём закрытия вкладок
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(ASSETS).catch(() => {}))
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())  // немедленно берём контроль над всеми вкладками
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // Динамические данные — всегда из сети
  if (url.pathname.endsWith('api_data.json')) {
    e.respondWith(
      fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // HTML — сначала сеть (чтобы всегда получать свежую версию), потом кэш
  if (url.pathname.endsWith('.html') || url.pathname.endsWith('/')) {
    e.respondWith(
      fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // Остальное: сначала кэш, затем сеть
  e.respondWith(
    caches.match(e.request).then((hit) =>
      hit || fetch(e.request).then((res) => {
        if (e.request.method === 'GET' && res.status === 200 && url.origin === location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      }).catch(() => caches.match('./index.html'))
    )
  );
});
