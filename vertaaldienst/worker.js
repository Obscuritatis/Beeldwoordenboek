// Vertaaldienst voor het Beeldwoordenboek (Cloudflare Worker).
// Houdt de API-sleutels geheim: de app stuurt de tekst hierheen, de worker vraagt
// eerst DeepL en valt terug op Microsoft Translator als DeepL op is of faalt.
// Geheimen (Settings > Variables and Secrets): DEEPL_KEY, MS_KEY, MS_REGION.

const ORIGINS = ["https://obscuritatis.github.io"];
const LANGS = ["nl", "fr", "en"];
const MAX_CHARS = 1000;
const PER_MIN = 30; // vragen per minuut per IP (per worker-instantie)
const hits = new Map();

const DEEPL_TARGET = { nl: "NL", fr: "FR", en: "EN-GB" };

function cors(origin) {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}
const json = (obj, status, origin) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json", ...cors(origin) } });

function tooMany(ip) {
  const now = Date.now();
  const list = (hits.get(ip) || []).filter((t) => now - t < 60000);
  list.push(now);
  hits.set(ip, list);
  if (hits.size > 5000) hits.clear();
  return list.length > PER_MIN;
}

async function viaDeepL(env, from, to, text) {
  if (!env.DEEPL_KEY) throw new Error("geen DeepL-sleutel");
  const host = env.DEEPL_KEY.endsWith(":fx") ? "api-free.deepl.com" : "api.deepl.com";
  const body = { text: [text], source_lang: from.toUpperCase(), target_lang: DEEPL_TARGET[to] };
  if (to === "fr" || to === "nl") body.formality = "prefer_less"; // "tu" en "je" in plaats van "vous" en "u"
  const r = await fetch(`https://${host}/v2/translate`, {
    method: "POST",
    headers: { Authorization: "DeepL-Auth-Key " + env.DEEPL_KEY, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error("DeepL " + r.status);
  const d = await r.json();
  return d.translations[0].text;
}

async function viaMicrosoft(env, from, to, text) {
  if (!env.MS_KEY) throw new Error("geen Microsoft-sleutel");
  const headers = { "Ocp-Apim-Subscription-Key": env.MS_KEY, "Content-Type": "application/json" };
  if (env.MS_REGION) headers["Ocp-Apim-Subscription-Region"] = env.MS_REGION;
  const r = await fetch(`https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&from=${from}&to=${to}`, {
    method: "POST",
    headers,
    body: JSON.stringify([{ Text: text }]),
  });
  if (!r.ok) throw new Error("Microsoft " + r.status);
  const d = await r.json();
  return d[0].translations[0].text;
}

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    if (!ORIGINS.includes(origin)) return new Response("Niet toegestaan", { status: 403 });
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
    if (req.method !== "POST") return json({ error: "methode" }, 405, origin);
    if (tooMany(req.headers.get("CF-Connecting-IP") || "?")) return json({ error: "te veel vragen" }, 429, origin);
    let q;
    try { q = await req.json(); } catch (_) { return json({ error: "ongeldig" }, 400, origin); }
    const from = String(q.from || ""), to = String(q.to || ""), text = String(q.text || "").trim();
    if (!LANGS.includes(from) || !LANGS.includes(to) || from === to || !text || text.length > MAX_CHARS)
      return json({ error: "ongeldig" }, 400, origin);
    const fouten = [];
    for (const [via, fn] of [["deepl", viaDeepL], ["microsoft", viaMicrosoft]]) {
      try { return json({ text: await fn(env, from, to, text), via }, 200, origin); }
      catch (e) { fouten.push(e.message); }
    }
    return json({ error: "geen dienst beschikbaar", detail: fouten }, 502, origin);
  },
};
