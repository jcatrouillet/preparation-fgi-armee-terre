#!/usr/bin/env python3
"""Serveur du jeu "Preparation a la FGI de l'armee de Terre" + API des meilleurs scores.

- GET  /              -> index.html
- GET  /api/scores    -> liste JSON du Top 20
- POST /api/scores    -> ajoute un score {name,pct,score,total,timer}, renvoie {scores, ts}

Les scores sont stockes cote serveur dans scores.json (partages entre tous
les navigateurs/appareils qui se connectent a ce serveur).

Lancement :  python server.py            (port 8123 par defaut)
             python server.py 9000        (port personnalise)
"""
import json
import os
import sys
import time
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
try:
    from http.server import ThreadingHTTPServer       # Python >= 3.7
except ImportError:                                    # vieux Python du NAS
    ThreadingHTTPServer = HTTPServer
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
SCORES_FILE = os.path.join(BASE, "scores.json")
MAX_SCORES = 20
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
# Interface d'ecoute :
#   - derriere un reverse proxy sur le NAS  -> "127.0.0.1" (plus sur, defaut)
#   - expose directement / dans Docker      -> "0.0.0.0"
# Surchargeable :  GRADES_HOST=0.0.0.0 python server.py
HOST = os.environ.get("GRADES_HOST", "127.0.0.1")

_lock = threading.Lock()


def load_scores():
    try:
        with open(SCORES_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_scores(data):
    tmp = SCORES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)
    os.replace(tmp, SCORES_FILE)  # ecriture atomique


def sort_key(e):
    # meilleur % d'abord, puis plus de bonnes reponses, puis plus ancien
    return (-int(e.get("pct", 0)), -int(e.get("score", 0)), int(e.get("ts", 0)))


MAX_TOTAL = 50          # un quiz ne depasse jamais ce nombre de questions
ALLOWED_TIMERS = (0, 3, 5, 10)
ALLOWED_GAMES = ("grades", "generale", "militaire", "vehicules")


def category(game):
    # trois classements separes : "grades", "vehicules" et "culture" (generale + militaire)
    if game in ("grades", "vehicules"):
        return game
    return "culture"


def add_score(raw):
    """Valide et enregistre un score. Renvoie (data, ts) ou (None, None) si invalide.

    Le serveur ne fait PAS confiance au % envoye par le client : il le recalcule
    a partir de score/total et rejette tout ce qui est impossible. Cela empeche
    l'injection de scores aberrants (200 %, 99/10, etc.) via une requete forgee.
    """
    try:
        score = int(raw.get("score", -1))
        total = int(raw.get("total", -1))
        timer = int(raw.get("timer", 0))
    except (TypeError, ValueError):
        return None, None

    if not (1 <= total <= MAX_TOTAL):
        return None, None
    if not (0 <= score <= total):
        return None, None
    if timer not in ALLOWED_TIMERS:
        timer = 0

    game = raw.get("game", "grades")
    if game not in ALLOWED_GAMES:
        game = "grades"

    entry = {
        "name": (str(raw.get("name", "")).strip()[:16] or "Anonyme"),
        "pct": round(score / total * 100),   # recalcule cote serveur
        "score": score,
        "total": total,
        "timer": timer,
        "game": game,
        "ts": int(time.time() * 1000),
    }
    with _lock:
        data = load_scores()
        data.append(entry)
        data.sort(key=sort_key)
        # garder un Top MAX_SCORES par categorie (grades / culture)
        counts, kept = {}, []
        for e in data:
            c = category(e.get("game", "grades"))
            counts[c] = counts.get(c, 0) + 1
            if counts[c] <= MAX_SCORES:
                kept.append(e)
        save_scores(kept)
    return kept, entry["ts"]


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def do_GET(self):
        self._guard(self._get)

    def do_POST(self):
        self._guard(self._post)

    def _guard(self, fn):
        """Toute exception est tracee dans la console ET renvoyee en 500
        (au lieu d'un 'Internal Server Error' opaque)."""
        try:
            fn()
        except Exception as e:
            tb = traceback.format_exc()
            sys.stderr.write(tb + "\n")
            sys.stderr.flush()
            try:
                self._json(500, {"error": "server error", "detail": str(e)})
            except Exception:
                pass

    def _get(self):
        path = urlparse(self.path).path
        if path == "/api/scores":
            self._json(200, load_scores())
            return
        if path in ("/", "/index.html", ""):
            self._serve_file("index.html")
            return
        self._serve_file(path.lstrip("/"))

    def _post(self):
        if urlparse(self.path).path != "/api/scores":
            self._json(404, {"error": "not found"})
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            raw = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception:
            self._json(400, {"error": "bad json"})
            return
        scores, ts = add_score(raw)
        if scores is None:
            self._json(400, {"error": "invalid score"})
            return
        self._json(200, {"scores": scores, "ts": ts})

    def _serve_file(self, rel):
        # empeche la remontee de repertoire
        fp = os.path.normpath(os.path.join(BASE, rel))
        if not fp.startswith(BASE) or not os.path.isfile(fp):
            self._json(404, {"error": "not found"})
            return
        ctype = "text/html; charset=utf-8" if fp.endswith(".html") else "application/octet-stream"
        with open(fp, "rb") as f:
            self._send(200, f.read(), ctype)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Preparation FGI : ecoute sur {HOST}:{PORT}  (scores -> {SCORES_FILE})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
