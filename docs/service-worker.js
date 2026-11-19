
const CACHE_NAME = "cerita-rakyat-v2";

const FILES_TO_CACHE = [
    "./",
    "./index.html",
    "./about.html",
    "./manifest.json",
    "./static/style.css",
    "./static/script.js",
    "./static/images/logo.png",
    "./static/images/icon-192.png",
    "./static/images/icon-512.png"
];

// Install Service Worker dan simpan file ke cache
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(FILES_TO_CACHE);
        })
    );

    self.skipWaiting();
});

// Aktifkan Service Worker
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );

    self.clients.claim();
});

// Ambil file dari cache jika tersedia
self.addEventListener("fetch", (event) => {
    if (event.request.method !== "GET") return;

    // Biarkan permintaan ke server API berjalan normal
    if (new URL(event.request.url).origin !== self.location.origin) return;

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                if (response && response.ok) {
                    const responseCopy = response.clone();

                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseCopy);
                    });
                }

                return response;
            })
            .catch(() => {
                return caches.match(event.request).then((cachedResponse) => {
                    return cachedResponse || new Response(
                        "Halaman tidak tersedia saat offline.",
                        {
                            status: 503,
                            headers: {
                                "Content-Type": "text/plain; charset=utf-8"
                            }
                        }
                    );
                });
            })
    );
});