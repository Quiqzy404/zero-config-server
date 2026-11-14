#!/usr/bin/env python3
"""
ZERO Config Server – winziger Backend-Server zum Teilen von Client-Configs.
Nur Python-Standardbibliothek, keine Abhaengigkeiten. Speichert Configs als JSON-Dateien.

Start:   python3 zero_config_server.py            (Port 8787, Daten in ./data)
         PORT=80 DATA=/var/zero python3 zero_config_server.py

Endpunkte (JSON):
  POST   /api/configs            Body {name, author, data}        -> {id, code, token}
  GET    /api/configs           (?q=suche&limit=100&sort=new|top) -> [{id, name, author, code, downloads, created}]
  GET    /api/configs/<idOrCode> Eintrag inkl. data (ohne token); zaehlt einen Download
  DELETE /api/configs/<id>      (?token=...)                       -> {ok:true}  (nur mit richtigem Token)
  GET    /api/health             {ok:true}

Sicherheit/Limits: max 256 KB pro Config, einfache Feldpruefung, Rate-Limit pro IP.
"""
import json
import os
import re
import time
import uuid
import threading
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("PORT", "8787"))
DATA = os.environ.get("DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
MAX_BYTES = 256 * 1024
NAME_RE = re.compile(r"^[\w .\-()\[\]#]{1,40}$")
AUTHOR_RE = re.compile(r"^[A-Za-z0-9_]{1,16}$")

os.makedirs(DATA, exist_ok=True)
_lock = threading.Lock()
_rate = {}  # ip -> [timestamps]


def _path(cid):
    return os.path.join(DATA, cid + ".json")


def _code_taken(code):
    for fn in os.listdir(DATA):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(DATA, fn), encoding="utf-8") as f:
                    if json.load(f).get("code") == code:
                        return True
            except Exception:
                pass
    return False


def _new_code():
    for _ in range(50):
        c = "".join(random.choice("0123456789") for _ in range(5))
        if not _code_taken(c):
            return c
    return uuid.uuid4().hex[:5]


def _list():
    out = []
    for fn in os.listdir(DATA):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(DATA, fn), encoding="utf-8") as f:
                e = json.load(f)
            out.append({k: e.get(k) for k in ("id", "name", "author", "code", "downloads", "created")})
        except Exception:
            pass
    return out


def _find(key):
    p = _path(key)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    for fn in os.listdir(DATA):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(DATA, fn), encoding="utf-8") as f:
                    e = json.load(f)
                if e.get("code") == key:
                    return e
            except Exception:
                pass
    return None


def _rate_ok(ip):
    now = time.time()
    with _lock:
        hist = [t for t in _rate.get(ip, []) if now - t < 60]
        if len(hist) >= 40:
            _rate[ip] = hist
            return False
        hist.append(now)
        _rate[ip] = hist
        return True


class Handler(BaseHTTPRequestHandler):
    server_version = "ZeroConfig/1.0"

    def _send(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/health":
            return self._send(200, {"ok": True})
        if u.path == "/api/configs":
            q = parse_qs(u.query)
            items = _list()
            term = (q.get("q", [""])[0] or "").lower()
            if term:
                items = [i for i in items if term in (i.get("name") or "").lower() or term in (i.get("author") or "").lower()]
            if q.get("sort", ["new"])[0] == "top":
                items.sort(key=lambda i: i.get("downloads", 0), reverse=True)
            else:
                items.sort(key=lambda i: i.get("created", 0), reverse=True)
            try:
                lim = max(1, min(300, int(q.get("limit", ["100"])[0])))
            except ValueError:
                lim = 100
            return self._send(200, items[:lim])
        m = re.match(r"^/api/configs/([\w-]{1,40})$", u.path)
        if m:
            e = _find(m.group(1))
            if not e:
                return self._send(404, {"error": "not found"})
            with _lock:
                e["downloads"] = e.get("downloads", 0) + 1
                try:
                    with open(_path(e["id"]), "w", encoding="utf-8") as f:
                        json.dump(e, f)
                except Exception:
                    pass
            pub = {k: v for k, v in e.items() if k != "token"}  # Token nie ausliefern
            return self._send(200, pub)
        return self._send(404, {"error": "unknown endpoint"})

    def do_POST(self):
        u = urlparse(self.path)
        ip = self.client_address[0]
        if u.path != "/api/configs":
            return self._send(404, {"error": "unknown endpoint"})
        if not _rate_ok(ip):
            return self._send(429, {"error": "too many uploads, slow down"})
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0 or length > MAX_BYTES:
            return self._send(413, {"error": "config too large (max 256 KB)"})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return self._send(400, {"error": "invalid json"})
        name = str(body.get("name", "")).strip()
        author = str(body.get("author", "")).strip()
        data = body.get("data")
        if not NAME_RE.match(name):
            return self._send(400, {"error": "bad name"})
        if not AUTHOR_RE.match(author):
            return self._send(400, {"error": "bad author"})
        if not isinstance(data, (dict, list)):
            return self._send(400, {"error": "data must be an object"})
        entry = {
            "id": uuid.uuid4().hex[:12],
            "name": name,
            "author": author,
            "code": _new_code(),
            "token": uuid.uuid4().hex,
            "downloads": 0,
            "created": int(time.time()),
            "data": data,
        }
        with _lock:
            with open(_path(entry["id"]), "w", encoding="utf-8") as f:
                json.dump(entry, f)
        return self._send(200, {"id": entry["id"], "code": entry["code"], "token": entry["token"]})

    def do_DELETE(self):
        u = urlparse(self.path)
        m = re.match(r"^/api/configs/([\w-]{1,40})$", u.path)
        if not m:
            return self._send(404, {"error": "unknown endpoint"})
        token = parse_qs(u.query).get("token", [""])[0]
        with _lock:
            e = _find(m.group(1))
            if not e:
                return self._send(404, {"error": "not found"})
            if not token or token != e.get("token"):
                return self._send(403, {"error": "wrong token"})
            try:
                os.remove(_path(e["id"]))
            except Exception:
                pass
        return self._send(200, {"ok": True})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"ZERO Config Server listening on :{PORT}  (data: {DATA})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
