"""deskd: one live world for everyone (round four).

    python deskd.py [port] [static_dir]

GET  /api/snapshot?session=<name>&as=<actor>    the world as JSON (rules, scripts, clock included), plus the
                                                 outline text exactly as the actor would read it
POST /api/do   {"session": "...", "as": "...", "line": "..."}    run desk commands; returns the receipt text and
                                                 the number of events so far
GET  /api/events?session=<name>&since=<n>       events after index n (poll this; it is cheap)
GET  /anything-else                              static files from static_dir (the shell)

The server and `python explore.py <session> --as <name>` share sessions: both take the same per-session lock from
load to save, so a person in the browser and an agent in a terminal work in one world. Every gesture the shell
makes must arrive here as a command line; there is no other way to change the world.
"""

import json
import os
import pickle
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import explore

HERE = Path(__file__).resolve().parent
SESSIONS = HERE / "sessions"
STATIC = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else HERE / "desk-shell"


class Session:
    """Load under the lock, act, save, release: the same discipline explore.py follows."""

    def __init__(self, name, actor):
        self.name, self.actor = name, (actor or "alex").lower()
        self.path = SESSIONS / f"{name}.pickle"
        self.lock = SESSIONS / f"{name}.lock"

    def __enter__(self):
        for _ in range(600):
            try:
                os.close(os.open(str(self.lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                break
            except FileExistsError:
                if time.time() - self.lock.stat().st_mtime > 60:
                    self.lock.unlink(missing_ok=True)
                time.sleep(0.05)
        desk = pickle.loads(self.path.read_bytes()) if self.path.exists() else explore.fresh()
        desk.world.me = self.actor
        per = getattr(desk, "_per", None) or {}
        if self.actor in per:
            desk.seen, desk.open, desk.last_event_seen = per[self.actor]
        elif self.actor != "jeff":
            desk.seen, desk.open, desk.last_event_seen = {}, {desk.world.root}, len(desk.world.events)
        desk._per = per
        self.desk, self.per = desk, per
        return desk

    def __exit__(self, *exc):
        try:
            d = self.desk
            self.per[self.actor] = (d.seen, d.open, d.last_event_seen)
            self.path.write_bytes(pickle.dumps(d))
        finally:
            self.lock.unlink(missing_ok=True)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(STATIC), **kw)

    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/api/snapshot":
            with Session(q.get("session", "desktop"), q.get("as")) as desk:
                snap = desk.snapshot()
                snap["events_total"] = len(desk.world.events)
                seen, header = dict(desk.seen), desk.last_event_seen      # reading for the renderer must not count as the actor looking
                snap["outline"] = desk.outline(desk.world.root, 2, deep=True)
                desk.seen, desk.last_event_seen = seen, header
            return self._json(snap)
        if u.path == "/api/events":
            since = int(q.get("since", 0))
            with Session(q.get("session", "desktop"), q.get("as")) as desk:
                evs = [{k: v for k, v in e.items() if k != "undo"} for e in desk.world.events[since:]]
                total = len(desk.world.events)
            return self._json({"events": evs, "total": total})
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/do":
            return self._json({"error": "POST /api/do only"}, 404)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        line = str(body.get("line", "")).strip()
        if not line:
            return self._json({"error": "line is required: every gesture is a command"}, 400)
        with Session(body.get("session", "desktop"), body.get("as")) as desk:
            r = desk.dispatch("desk", {"line": line})
            total = len(desk.world.events)
        self._json({"text": r.get("text"), "error": r.get("error"), "events_total": total, "line": line, "as": (body.get("as") or "alex")})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8780
    SESSIONS.mkdir(exist_ok=True)
    STATIC.mkdir(exist_ok=True)
    print(f"deskd on http://localhost:{port}  static={STATIC}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
