const CACHE = "bwb-20261124082536";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "fonts/fonts.css", "fonts/lato-latin-1.woff2", "fonts/lato-latin-3.woff2", "fonts/lato-latin-ext-0.woff2", "fonts/lato-latin-ext-2.woff2", "fonts/montserrat-latin-5.woff2", "fonts/montserrat-latin-ext-4.woff2"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => { e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const fresh = url.origin === location.origin && (url.pathname.endsWith("/") || url.pathname.endsWith(".html") || url.pathname.endsWith("woorden.json"));
  if (fresh) {
    // eerst netwerk, zodat nieuwe woorden meteen verschijnen; offline uit de cache
    e.respondWith(fetch(req).then((r) => { const copy = r.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); return r; }).catch(() => caches.match(req)));
  } else {
    // foto's, geluid, lettertypes: eerst cache
    e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((r) => { if (r.ok || r.type === "opaque") { const copy = r.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); } return r; })));
  }
});
