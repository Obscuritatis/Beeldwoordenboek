#!/usr/bin/env python3
"""Bouwt de publieke website (PWA) uit de app-bron.

Gebruik: python3 build_site.py <artifact-bron.html> <site-map>
Schrijft index.html, manifest.webmanifest en sw.js. woorden.json en media/ blijven staan.
"""
import json, sys, time, pathlib

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
(out / "media").mkdir(exist_ok=True)
body = src.read_text(encoding="utf-8")
version = time.strftime("%Y%m%d%H%M%S")

head = f"""<!doctype html>
<html lang="nl" data-site="1">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1f4e79">
<meta name="description" content="Foto's en pictogrammen met het Nederlandse woord en de uitspraak.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Woordenboek">
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
"""
(out / "index.html").write_text(head + body + "\n</body>\n</html>\n", encoding="utf-8")

manifest = {
    "name": "Beeldwoordenboek",
    "short_name": "Woordenboek",
    "description": "Foto's en pictogrammen met het Nederlandse woord en de uitspraak.",
    "lang": "nl",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#f3f5f7",
    "theme_color": "#1f4e79",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
(out / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

sw = """const CACHE = "bwb-%s";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png"];
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
""" % version
(out / "sw.js").write_text(sw, encoding="utf-8")
if not (out / "woorden.json").exists():
    (out / "woorden.json").write_text(json.dumps({"words": []}, indent=2), encoding="utf-8")
print("site gebouwd in", out, "versie", version)
