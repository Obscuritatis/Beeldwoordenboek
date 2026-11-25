// Vertalen op het toestel zelf met de Firefox-vertaalmodellen (Bergamot, MPL-2.0).
// Er gaat geen tekst naar het internet: alleen de taalpakketten worden een keer van deze site gedownload.
import { LatencyOptimisedTranslator } from "./lib/translator.js";

let tr = null;
export async function translate(from, to, text) {
  tr = tr || new LatencyOptimisedTranslator({ registryUrl: new URL("./registry.json", import.meta.url).href, downloadTimeout: 0, pivotLanguage: "en" });
  const r = await tr.translate({ from, to, text, html: false });
  return r.target.text;
}
