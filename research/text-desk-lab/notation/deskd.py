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
import worktree

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
        desk._session = self.name
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
                # Lark: each person's reading position is a fact others may see (how far into the log they have looked)
                wt = getattr(desk, "_wt", None)
                snap["worktree"] = {k: (len(v) if k == "journal" else v) for k, v in wt.items()} if wt else None
                snap["readers"] = {a: v[2] for a, v in (getattr(desk, "_per", None) or {}).items()}
                seen, header = dict(desk.seen), desk.last_event_seen      # reading for the renderer must not count as the actor looking
                snap["outline"] = desk.outline(desk.world.root, 2, deep=True)
                desk.seen, desk.last_event_seen = seen, header
            return self._json(snap)
        if u.path == "/api/scene":
            import scene
            with Session(q.get("session", "desktop"), q.get("as")) as desk:
                try:
                    sc, text = scene.scene_for(desk, q.get("lens", ""))
                    out = {"scene": sc, "text": text, "events_total": len(desk.world.events)}
                except scene.LensRefusal as e:
                    out = {"refused": str(e), "events_total": len(desk.world.events)}
                except Exception as e:      # Astra: a compiler fault must arrive as a refusal, not as a dead endpoint
                    out = {"refused": f"the lens compiler failed ({type(e).__name__}: {e}); this is a bug in scene.py, not in your lens",
                           "events_total": len(desk.world.events)}
            return self._json(out)
        if u.path == "/api/events":
            since = int(q.get("since", 0))
            with Session(q.get("session", "desktop"), q.get("as")) as desk:
                evs = [{k: v for k, v in e.items() if k != "undo"} for e in desk.world.events[since:]]
                total = len(desk.world.events)
            return self._json({"events": evs, "total": total})
        return super().do_GET()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if urlparse(self.path).path == "/api/observe":
            # a painter reports what happened on its screen. Not an event, not undoable, not the world: a viewer's observation.
            with Session(body.get("session", "desktop"), body.get("as")) as desk:
                views = getattr(desk, "_views", None)
                if views is None:
                    views = desk._views = {}
                facts = {str(k)[:200]: str(v)[:60] for k, v in list((body.get("facts") or {}).items())[:400]}
                views[(body.get("as") or "alex").lower()] = {"lens": str(body.get("lens", "")).lower(), "at": int(body.get("at", 0)),
                                                            "time": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                                                            "viewport": body.get("viewport"), "facts": facts}
            return self._json({"ok": True, "kept": len(facts)})
        if urlparse(self.path).path != "/api/do":
            return self._json({"error": "POST /api/do or /api/observe"}, 404)
        line = str(body.get("line", "")).strip()
        if not line:
            return self._json({"error": "line is required: every gesture is a command"}, 400)
        sess = Session(body.get("session", "desktop"), body.get("as"))
        with sess as desk:
            before, n0 = set(desk.world.nodes), len(desk.world.events)
            ob = body.get("observed") or {}
            d = ob.get("def") or {}
            cur = desk.world.subjects.get(d.get("id"))
            if d and (cur is None or cur["rev"] != d.get("rev")):
                return self._json({"text": None, "error": f"refused: lens {d.get('lens')} changed since this was painted "
                                   f"(you saw revision {d.get('rev')}, it is now {cur['rev'] if cur else 'gone'}); the gesture may no longer mean what it said. "
                                   f"Nothing was done. The view will repaint.", "events_total": len(desk.world.events), "line": line})
            if ob.get("item") in desk.world.nodes and isinstance(ob.get("rev"), int):
                # Astra: a gesture acts on the generation its maker SAW. The painter used to prefix `look item;`, which
                # turned stale pixels into fresh permission. Now the act carries what was observed and the fence judges that.
                desk.seen[ob["item"]] = ob["rev"]
                idx = getattr(desk, "_seen_idx", None)
                if idx is None:
                    idx = desk._seen_idx = {}
                idx[(sess.actor, ob["item"])] = int(ob.get("at", 0))
            if line.lower().split(" ")[0] == "worktree":
                text, desk = worktree.handle(line, sess.name, desk, sess.actor)
                sess.desk = desk
                desk._per = sess.per
                r = {"text": text}
            else:
                allids = worktree.ids_of(desk)
                r = desk.dispatch("desk", {"line": line})
                worktree.record(desk, line, sess.actor, allids, n0)
            total = len(desk.world.events)
            created = [i for i in desk.world.nodes if i not in before]      # Wren: the ids a command made, machine-readably
            events = [e["id"] for e in desk.world.events[n0:]]
        text = r.get("text") or ""
        # Rook: a parse failure came back as error=null. And a refusal in the second step of `look x; do y` hid in the text.
        bad = [l for l in text.splitlines() if l.startswith("ERR")]
        refused = r.get("error") or (bad[0] if bad else None)
        self._json({"text": r.get("text"), "error": refused, "events_total": total, "line": line,
                    "as": (body.get("as") or "alex"), "created": created, "events": events})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8780
    SESSIONS.mkdir(exist_ok=True)
    STATIC.mkdir(exist_ok=True)
    print(f"deskd on http://localhost:{port}  static={STATIC}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
