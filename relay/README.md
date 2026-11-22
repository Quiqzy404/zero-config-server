# ZERO Marker Relay — Cloudflare Worker (kostenlos)

Damit **alle** ZERO-Clients (full + public/viewer) geteilte Marker sehen — ohne Freund-Namen,
serverübergreifend, unsichtbar für Nicht-ZERO-Spieler. Einmal einrichten, dann läuft's.

## Einrichtung (ca. 5 Min, im Browser, alles gratis)

1. **Account:** https://dash.cloudflare.com → kostenlos registrieren/einloggen.
2. **KV anlegen:** Links **Storage & Databases → KV** → **Create a namespace** → Name z.B. `zero-markers` → anlegen.
3. **Worker anlegen:** Links **Compute (Workers) → Workers & Pages → Create → Worker**.
   - Name z.B. `zero-relay` → **Deploy** (nimmt erst den Beispiel-Code).
4. **Code einfügen:** Beim Worker **Edit code** → ALLES löschen → Inhalt von `worker.js` (neben dieser Datei) reinkopieren → **Deploy**.
5. **KV binden:** Worker → **Settings → Bindings → Add → KV namespace**
   - **Variable name:** `MARKERS`  (genau so!)
   - **KV namespace:** `zero-markers`
   - **Save / Deploy**.
6. *(Optional, empfohlen)* **Schlüssel setzen:** Worker → **Settings → Variables and Secrets → Add → Secret**
   - **Name:** `ZK`  **Value:** irgendein geheimes Wort (z.B. `zerosecret123`).
   - Deploy. (Verhindert, dass Fremde Marker spammen.)

## Deine Worker-URL

Oben beim Worker steht die URL, z.B.:
```
https://zero-relay.DEINNAME.workers.dev
```
**Diese URL (und ggf. den ZK-Wert) an mich geben** — ich trage sie in `dist/relay.json` ein:
```json
{ "url": "https://zero-relay.DEINNAME.workers.dev", "key": "zerosecret123" }
```
Danach sehen **alle** ZERO-Clients beim nächsten Game-Start automatisch die geteilten Marker.
Kein Client-Rebuild nötig — die Clients lesen die URL aus `relay.json`.

## Test
- `https://DEINE-URL/sub`  → sollte `[]` zeigen (leere Liste).
- Wenn du mit `ZK` arbeitest, zeigt der direkte Browser-Aufruf `forbidden` (korrekt — Header fehlt).

## Kosten/Limits (Free-Tier)
- /sub wird 5 Sek am Edge gecacht → egal wie viele Viewer, nur ~1 KV-Read / 5 Sek.
- Reicht locker im Gratis-Rahmen (100k Reads + 1k Writes/Tag).
