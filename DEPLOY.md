# ZERO Config Server – online stellen (kostenlos, ohne Kreditkarte)

Der Server ist eine einzige Python-Datei (`zero_config_server.py`), keine Abhaengigkeiten.
Empfehlung: **Koyeb** – gratis, 24/7 an, keine Kreditkarte, Deploy direkt aus GitHub.

## Variante A – Koyeb (empfohlen, immer online)

1. **Ordner `server/` auf GitHub legen**
   - Auf github.com einloggen/registrieren (gratis).
   - "New repository" → Name z. B. `zero-config-server` → Public → Create.
   - Die Dateien `zero_config_server.py` und `Dockerfile` hochladen
     (Repo-Seite → "Add file" → "Upload files" → beide reinziehen → Commit).

2. **Koyeb-Account**
   - app.koyeb.com → "Sign up" → mit GitHub einloggen (keine Karte noetig).

3. **Service erstellen**
   - "Create Service" → "GitHub" → dein Repo `zero-config-server` auswaehlen.
   - Koyeb erkennt das `Dockerfile` automatisch (Builder: Dockerfile).
   - Instance: **Free** auswaehlen.
   - Port: **8787** eintragen (oder leer lassen – der Server nimmt $PORT).
   - "Deploy".

4. **URL kopieren**
   - Nach ~1 Min bekommst du eine Adresse wie `https://zero-config-server-xxxx.koyeb.app`.
   - Testen: im Browser `…koyeb.app/api/health` → `{"ok": true}`.
   - **Diese URL kommt in die Mod** (Configs-Tab → Server URL).

> Hinweis: Auf der Free-Instanz koennen Configs bei einem Neustart verloren gehen,
> wenn kein dauerhaftes Volume dran ist. Fuer dauerhaften Speicher spaeter ein Volume
> an `/app/data` haengen (oder einen kleinen VPS nehmen).

## Variante B – eigener VPS (z. B. Hetzner ~5 €/Monat, Daten bleiben)

```bash
# auf dem Server (Ubuntu):
sudo apt update && sudo apt install -y python3
# Datei hochladen, dann:
sudo PORT=80 DATA=/var/zero-configs python3 zero_config_server.py
# dauerhaft laufen lassen: als systemd-Dienst einrichten (sag Bescheid, ich gebe dir die .service-Datei)
```
URL ist dann `http://DEINE-SERVER-IP/api/health`.

## Lokal testen (ohne Hoster)

```bash
cd server
python zero_config_server.py          # laeuft auf http://127.0.0.1:8787
```
In der Mod als Server URL `http://127.0.0.1:8787` eintragen – nur du erreichst ihn,
aber gut zum Ausprobieren.
