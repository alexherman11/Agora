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

import scene
from desk import aspects_of, aspects_meet

import explore
import worktree

HERE = Path(__file__).resolve().parent
SESSIONS = HERE / "sessions"
STATIC = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else HERE / "desk-shell"


def _brief(answer, top=6):
    if isinstance(answer, str):
        return answer
    ids = [x[0] if isinstance(x, (list, tuple)) else x for x in answer]
    return "nothing" if not ids else ", ".join(ids[:top]) + (f" and {len(ids) - top} more" if len(ids) > top else "")


def touched_aspects(w, sid, seen, now, fields):
    """Did any of `fields` (aspects, as desk.aspects_of names them) change on `sid` between revision `seen` and `now`?
    Pike a308: a retitle used to refuse a gesture that had only read a prop. Until Sable's journal records one row per
    (thing, aspect), the events touching the thing are taken from the end, one per revision step."""
    names = {sid} if isinstance(sid, str) else set(sid)        # a thing, or an appearance with its subject
    by_id = {e["id"]: e for e in w.events}

    def seen_as(e):
        # Sable's baseline (3): an undo's target is an event id; it touches what the reverted event touched
        return by_id.get(e["target"], e) if e["verb"] == "undo" else e

    hits = [e for e in w.events if not e.get("undone")
            and (seen_as(e)["target"] in names or names & set(seen_as(e).get("changed") or []))]
    step = max(0, int(now) - int(seen))
    recent = hits[-step:] if 0 < step <= len(hits) else hits
    return any(aspects_meet(set(fields), aspects_of(seen_as(e).get("via") or seen_as(e)["verb"], seen_as(e).get("args"))) for e in recent)


def same_answer(desk, q, answer, keep=None):
    """A membership read (sable-8 amended): the selection `q` a gesture's chain bound, re-asked now. -> (same, now).
    Sable (sable-10): a clamped repeat recorded the shown prefix, so only the first `keep` are compared; answers compare
    as sets, since a move changes no membership."""
    try:
        named = scene._named(desk.world, q)
        now = [list(x) for x in named] if named is not None else list((desk._parse_selection(q) or ([], ""))[0])
    except Exception as e:                # the selection itself no longer parses (a title it named is gone)
        return False, f"unanswerable: {e}"
    if keep:
        now = now[:keep]
    key = lambda xs: {tuple(x) if isinstance(x, list) else x for x in xs}
    return key(now) == key(answer), now


def same_part(desk, dp):
    """A gesture carries the identity of the part that painted it: lens id, part path and the hash of the lines that
    bind it. If the lens changed elsewhere, the part is the same and the gesture still means what it said."""
    if not (dp and dp.get("id") and dp.get("path") and dp.get("hash")):
        return False
    lens = desk.world.subjects.get(dp["id"])
    if lens is None:
        return False
    try:
        return scene.defpart_hash(lens.get("text") or "", dp["path"]) == dp["hash"]
    except scene.LensRefusal:
        return False


class Session:
    """Load under the lock, act, save, release: the same discipline explore.py follows."""

    def __init__(self, name, actor):
        self.name, self.actor = name, (actor or "alex").lower()
        self.path = SESSIONS / f"{name}.pickle"
        self.lock = SESSIONS / f"{name}.lock"

    def __enter__(self):
        explore.take_lock(self.lock, tries=1200, pause=0.05)
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
            explore.save_desk(self.path, d)
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
                    if q.get("view") == "painter":      # Pike a494: key, paint, acts, fence, kids; the root keeps its def
                        sc = dict(scene.painter_view(sc), **{"def": sc.get("def")})
                    out = {"scene": sc, "text": text, "events_total": len(desk.world.events)}
                except scene.LensRefusal as e:
                    out = {"refused": str(e), "events_total": len(desk.world.events)}
                except Exception as e:      # Astra: a compiler fault must arrive as a refusal, not as a dead endpoint
                    out = {"refused": f"the lens compiler failed ({type(e).__name__}: {e}); this is a bug in scene.py, not in your lens",
                           "events_total": len(desk.world.events)}
            return self._json(out)
        if u.path == "/api/style":
            # F7: a style is world data (a note tagged style); the seed file answers only when the world has none
            import scene
            with Session(q.get("session", "desktop"), q.get("as")) as desk:
                st = scene.style_source(desk, q.get("name") or "calm")
            return self._json(st or {"refused": f"no style {q.get('name')!r}"})
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
            if d and d.get("status") == "fallback":
                return self._json({"text": None, "error": f"refused: this view is showing a fallback of lens {d.get('lens')} because the current one does not compile; "
                                   "it is for reading. Nothing was done.", "events_total": len(desk.world.events), "line": line})
            part_ok = same_part(desk, ob.get("defpart"))     # Pike a308: judged per part, not per lens
            for c in d.get("closure") or []:      # every definition the frame was built from must still be the current one
                now = desk.world.subjects.get(c.get("id"))
                if now is None or now["rev"] != c.get("rev"):
                    d, cur = c, now
                    break
            if d and not part_ok and (cur is None or cur["rev"] != d.get("rev")):
                return self._json({"text": None, "error": f"refused: lens {d.get('lens')} changed since this was painted "
                                   f"(you saw revision {d.get('rev')}, it is now {cur['rev'] if cur else 'gone'}); the gesture may no longer mean what it said. "
                                   f"Nothing was done. The view will repaint.", "events_total": len(desk.world.events), "line": line})
            # Pike a361/c368: a drop carries the thing in hand and the receiver it lands on; both are fenced first, in the
            # receiver's words (Pike a494: the person dropped on a day, so a stale trip is told as the day's), then $carried fills
            car, rcv = ob.get("carried") or {}, ob.get("receiver") or {}
            if car.get("item") in desk.world.nodes and isinstance(car.get("rev"), int):
                cn = desk.world.nodes[car["item"]]
                now_c, cnames = cn["rev"], {car["item"]} | ({cn["subject"]} if cn.get("subject") else set())
                cf = set()
                for entry in (car.get("reads") or []):
                    sid, _r, fl = (list(entry) + [None, None])[:3]
                    if sid in cnames and fl:
                        cf |= set(fl)
                if now_c != car["rev"] and not (cf and not touched_aspects(desk.world, cnames, car["rev"], now_c, cf)):
                    return self._json({"text": None, "error": f"refused: the carried thing {car['item']} changed while it was in the air "
                                       f"(you picked up revision {car['rev']}, it is now {now_c}); nothing was done. The view will repaint.",
                                       "events_total": len(desk.world.events), "line": line})
                desk.seen[car["item"]] = now_c          # judged as picked up: the drop's line may name it
                desk._note_seen(car["item"], len(desk.world.events), sorted(cf) or None, obs=sess.actor)
            if rcv and rcv.get("item") in desk.world.nodes and isinstance(rcv.get("rev"), int):
                rn = desk.world.nodes[rcv["item"]]
                now_r, rnames = rn["rev"], {rcv["item"]} | ({rn["subject"]} if rn.get("subject") else set())
                rf = set()
                for entry in (rcv.get("reads") or []):
                    sid, _r, fl = (list(entry) + [None, None])[:3]
                    if sid in rnames and fl:
                        rf |= set(fl)
                if now_r != rcv["rev"] and not (rf and not touched_aspects(desk.world, rnames, rcv["rev"], now_r, rf)):
                    return self._json({"text": None, "error": f"refused: the place this was dropped on no longer means what it did: {rcv['item']} "
                                       f"(you saw revision {rcv['rev']}, it is now {now_r}); nothing was done. The view will repaint.",
                                       "events_total": len(desk.world.events), "line": line})
            for entry in (rcv.get("reads") or []):
                sid, rev, fields = (list(entry) + [None, None])[:3]
                if sid == "select":
                    if not same_answer(desk, rev, fields, entry[3] if len(entry) > 3 else None)[0]:
                        return self._json({"text": None, "error": f"refused: the place this was dropped on is no longer under what it was painted under "
                                           f"(`{rev}` answers differently now); nothing was done. The view will repaint.",
                                           "events_total": len(desk.world.events), "line": line})
                    continue
                cur = desk.world.subjects.get(sid) or desk.world.nodes.get(sid)
                if cur is not None and cur["rev"] != rev and fields and not touched_aspects(desk.world, sid, rev, cur["rev"], fields):
                    continue
                if cur is None or cur["rev"] != rev:
                    return self._json({"text": None, "error": f"refused: the place this was dropped on no longer means what it did: {sid} "
                                       f"(you saw revision {rev}, it is now {cur['rev'] if cur else 'gone'}); nothing was done. The view will repaint.",
                                       "events_total": len(desk.world.events), "line": line})
            if rcv.get("defpart") and not same_part(desk, rcv.get("defpart")):
                return self._json({"text": None, "error": "refused: the part this was dropped on changed in the lens since it was painted; "
                                   "nothing was done. The view will repaint.", "events_total": len(desk.world.events), "line": line})
            if ob.get("item") in desk.world.nodes and isinstance(ob.get("rev"), int):
                # Astra: a gesture acts on the generation its maker SAW. The painter used to prefix `look item;`, which
                # turned stale pixels into fresh permission. Now the act carries what was observed and the fence judges that.
                now = desk.world.nodes[ob["item"]]["rev"]
                nd = desk.world.nodes[ob["item"]]
                names = {ob["item"]} | ({nd["subject"]} if nd.get("subject") else set())
                fields = set()
                for entry in (ob.get("reads") or []):
                    sid, _rev, fl = (list(entry) + [None, None])[:3]
                    if sid in names and fl:
                        fields |= set(fl)
                # Pike rerun (S5): the whole-item check ran before the reads had a say, so a title edit was refused because
                # another actor set a prop the lens never shows. The item is judged on the aspects the gesture read; the
                # whole revision only fences a gesture that read nothing.
                if now != ob["rev"] and not (fields and not touched_aspects(desk.world, names, ob["rev"], now, fields)):
                    # Pike: the item fence exempted the actor's own edits, so one person with two windows was unprotected.
                    # A painted gesture is judged on what was painted, whoever changed it since.
                    last = [e for e in desk.world.events if e["target"] == ob["item"] or ob["item"] in (e.get("changed") or [])]
                    who = f" ({last[-1]['id']} {last[-1]['verb']} by {last[-1]['by']})" if last else ""
                    return self._json({"text": None, "error": f"refused: {ob['item']} changed since this was painted (you saw revision {ob['rev']}, "
                                       f"it is now {now}{who}); nothing was done. The view will repaint.", "events_total": len(desk.world.events), "line": line})
                # Pike report 2 (S5): after the aspect fence accepts, the desk's own staleness check still saw the old
                # revision; what was judged is now seen.
                desk.seen[ob["item"]] = now if now != ob["rev"] else ob["rev"]
                if now != ob["rev"]:
                    desk._note_seen(ob["item"], len(desk.world.events), sorted(fields) or None, obs=sess.actor)
            for entry in (ob.get("reads") or []):
                # Pike F1: a gesture is judged on every value its line was built from, not only the clicked item.
                # Juniper's stale "move to Sun": the item and the lens were unchanged, the trip's start had moved.
                sid, rev, fields = (list(entry) + [None, None])[:3]
                if sid == "select":
                    # sable-8 amended: the chain's bind is a membership read; "mark done" must not land on a task that
                    # left the person's list, and `the` must not act through a match that became ambiguous
                    same, now = same_answer(desk, rev, fields, entry[3] if len(entry) > 3 else None)
                    if not same:
                        return self._json({"text": None, "error": f"refused: what this gesture was under has changed: `{rev}` "
                                           f"answered {_brief(fields)} when it was painted and answers {_brief(now)} now; nothing was done. The view will repaint.",
                                           "events_total": len(desk.world.events), "line": line})
                    continue
                cur = desk.world.subjects.get(sid) or desk.world.nodes.get(sid)
                if cur is not None and cur["rev"] != rev and fields and not touched_aspects(desk.world, sid, rev, cur["rev"], fields):
                    continue              # it moved, but on an aspect this gesture never read
                if cur is None or cur["rev"] != rev:
                    return self._json({"text": None, "error": f"refused: a value this gesture was built from has changed: {sid} (you saw revision {rev}, "
                                       f"it is now {cur['rev'] if cur else 'gone'}); nothing was done. The view will repaint.",
                                       "events_total": len(desk.world.events), "line": line})
                desk._note_seen(ob["item"], int(ob.get("at", 0)), sorted(fields) if fields else None, obs=sess.actor)
            if car.get("item"):
                line = line.replace("$carried", car["item"])
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
