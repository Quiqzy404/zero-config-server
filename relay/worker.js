// ZERO Marker Relay — Cloudflare Worker (+ KV)
// Bindings: KV-Namespace an "MARKERS" binden. Optional Secret "ZK" (gemeinsamer Schlüssel).
// Endpunkte:  POST /pub  (Body = Marker-Payload "C ..." / "P ...")   GET /sub  (JSON-Liste)
const TTL_MS = 5 * 60 * 1000;  // Marker leben 5 Minuten
const CACHE_TTL = 5;           // /sub Edge-Cache in Sekunden -> viele Viewer, wenige KV-Reads
const KEY = "markers";

export default {
  async fetch(req, env) {
    const url = new URL(req.url);

    // optionaler gemeinsamer Schlüssel
    const ok = env.ZK ? req.headers.get("X-ZK") === env.ZK : true;
    if (!ok) return new Response("forbidden", { status: 403 });

    // ---- Marker posten ----
    if (url.pathname === "/pub" && req.method === "POST") {
      const payload = (await req.text()).trim();
      if (!payload || payload.length > 200) return new Response("bad", { status: 400 });
      const now = Date.now();
      let list = [];
      try { list = JSON.parse((await env.MARKERS.get(KEY)) || "[]"); } catch (e) {}
      // gleiche Payload ersetzen (frischt Zeitstempel auf), Abgelaufene raus
      list = list.filter((m) => m.p !== payload && now - m.t < TTL_MS);
      list.push({ p: payload, t: now });
      if (list.length > 200) list = list.slice(-200);
      await env.MARKERS.put(KEY, JSON.stringify(list), { expirationTtl: 600 });
      return new Response("ok", { status: 200 });
    }

    // ---- Marker abholen ----
    if (url.pathname === "/sub" && req.method === "GET") {
      const cache = caches.default;
      const cacheKey = new Request(url.toString(), { method: "GET" });
      const hit = await cache.match(cacheKey);
      if (hit) return hit;
      const now = Date.now();
      let list = [];
      try { list = JSON.parse((await env.MARKERS.get(KEY)) || "[]"); } catch (e) {}
      list = list.filter((m) => now - m.t < TTL_MS);
      const res = new Response(JSON.stringify(list), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": `public, max-age=${CACHE_TTL}`,
        },
      });
      await cache.put(cacheKey, res.clone());
      return res;
    }

    return new Response("ZERO Relay OK", { status: 200 });
  },
};
