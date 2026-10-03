"""deskd: one live world for everyone (round four).

    python deskd.py [port] [static_dir]

GET  /api/snapshot?session=<name>&as=<actor>    the world as JSON (rules, each with its note, and the clock included), plus the
                                                 outline text exactly as the actor would read it
POST /api/do   {"session": "...", "as": "...", "line": "..."}    run desk commands; returns the receipt text and
                                                 the number of events so far; "whole": true runs the line as one
                                                 command, a ; in it being words (a resident's > line, a736);
                                                 "gesture": "<id>" (a1008) is recorded on the events it made, and a
                                                 second post with that id does nothing and answers "already done, as eN"
GET  /api/events?session=<name>&since=<n>       events after index n (poll this; it is cheap: an unchanged world file
                                                 is not loaded)
GET  /api/version, /api/health                  the code this runs, the painter's files' hash and scene shape; ok
Under the keeper it runs behind door.py (a1505), which swaps it for one on new code; see door.py.
GET  /anything-else                              static files from static_dir (the shell)

The server and `python explore.py <session> --as <name>` share sessions: both take the same per-session lock from
load to save, so a person in the browser and an agent in a terminal work in one world. Every gesture the shell
makes must arrive here as a command line; there is no other way to change the world.
"""

import json
import os
import pickle
import re
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import scene
from desk import aspects_of, aspects_meet, event_aspects

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
    return any(aspects_meet(set(fields), event_aspects(seen_as(e))) for e in recent)


def same_answer(desk, q, answer, keep=None, by=None):
    """A membership read (sable-8 amended): the selection `q` a gesture's chain bound, re-asked now. -> (same, now).
    Sable (sable-10): a clamped repeat recorded the shown prefix, so only the first `keep` are compared; answers compare
    as sets, since a move changes no membership. A repeat ordered `by` props (a1069) is re-ordered the same way first."""
    try:
        named = scene._named(desk.world, q)
        now = [list(x) for x in named] if named is not None else list((desk._parse_selection(q) or ([], ""))[0])
    except Exception as e:                # the selection itself no longer parses (a title it named is gone)
        return False, f"unanswerable: {e}"
    if by:
        import moo
        w = desk.world
        now = sorted(now, key=lambda x: tuple(moo.order_value(moo.props_of(w, x[0] if isinstance(x, list) else x).get(k)) for k in by))
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
        style = (lens.get("props") or {}).get("style")          # F18: the part is parsed under the lens's own style
        return scene.defpart_hash(lens.get("text") or "", dp["path"], scene.style_roles(desk, style), style) == dp["hash"]
    except scene.LensRefusal:
        return False


def _code_version():
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).resolve().parent,
                              capture_output=True, text=True, timeout=10).stdout.strip() or "dev"
    except Exception:
        return "dev"


# a1505: the door (door.py) starts each deskd with DESKD_CODE set to the commit it swapped to, so a receipt and the
# quiet line name the same code even if HEAD moved again while this one was starting
CODE_VERSION = os.environ.get("DESKD_CODE") or _code_version()
_PAINTER = [None, ""]


def painter_version():
    """The painter's own code: a hash of every file under the static dir. A page offers its person the new painter only
    when this changes (a1505); a landing that changes only Python leaves the page as it is."""
    import hashlib
    files = sorted(p for p in STATIC.rglob("*") if p.is_file())
    key = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in files)
    if key != _PAINTER[0]:
        h = hashlib.sha1()
        for p in files:
            h.update(str(p.relative_to(STATIC)).encode() + b"\0" + p.read_bytes() + b"\0")
        _PAINTER[:] = [key, h.hexdigest()[:12]]
    return _PAINTER[1]


SESSION_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_@-]{0,63}$")    # frontier-x, a@b, try-t, _test_x: no . / \ or ..


class BadRequest(ValueError):
    pass


# 30 Sep (Alex: the 1500-node budget kept blanking the Desktop): the painter asks for its scene every 1.5 s, and each ask
# loaded the 8 MB world, built the whole lens and pickled the world twice (0.5-0.7 s for the Desktop's 1387 nodes, 723
# KB), though nothing had changed. A scene is now built again only when something it can show changed: the world file
# (a request that changes nothing doesn't write it), the house's state apart from its heartbeat, whether the house is
# alive, or the minute (times print as 08:15). The answer for anything else is the one already built.
_SCENES, _EVENTS = {}, {}


def _scene_key(q):
    name = q.get("session", "desktop")
    if not SESSION_NAME.match(str(name)):
        return None
    try:
        st = (SESSIONS / f"{name}.pickle").stat()
    except OSError:
        return None
    house = None
    try:
        h = json.loads((HERE / "house-state" / name.split("@")[0] / "house.json").read_text(encoding="utf-8"))
        beat = float(h.pop("beat", 0) or 0)
        h.pop("pid", None)
        house = (json.dumps(h, sort_keys=True, default=str), time.time() - beat < 30)
    except (OSError, ValueError, TypeError):
        pass
    try:                                         # a2844: who is away in a version (the door's visits.json) is shown too
        visits = (HERE / "house-state" / "visits.json").stat().st_mtime_ns
    except OSError:
        visits = None
    return (name, (q.get("as") or "alex").lower(), q.get("lens", ""), q.get("view"), st.st_mtime_ns, st.st_size, house,
            int(time.time() // 60), visits)


def snapshot_for(desk):
    """The world as JSON for the Desktop (core.js asks at start, after each of its own acts, and at every change)."""
    snap = desk.snapshot()
    snap["events_total"] = len(desk.world.events)
    # Lark: each person's reading position is a fact others may see (how far into the log they have looked)
    wt = getattr(desk, "_wt", None)
    snap["worktree"] = {k: (len(v) if k == "journal" else v) for k, v in wt.items()} if wt else None
    snap["readers"] = {a: v[2] for a, v in (getattr(desk, "_per", None) or {}).items()}
    # reading for the renderer must not count as the actor looking. a2872: nor what the fence reads (_seen_idx); left
    # out, every refresh marked each outline line's title and props seen, and alex's next retitle passed unrefused.
    # A shallow copy is enough: _note_seen replaces a key's dict, never changes one in place.
    seen, header, idx = dict(desk.seen), desk.last_event_seen, getattr(desk, "_seen_idx", None)
    idx = dict(idx) if idx is not None else None
    snap["outline"] = desk.outline(desk.world.root, 2, deep=True)
    desk.seen, desk.last_event_seen = seen, header
    if idx is None:
        desk.__dict__.pop("_seen_idx", None)     # absent before: absent after, so an unchanged world is not rewritten
    else:
        desk._seen_idx = idx
    return snap


class Session:
    """Load under the lock, act, save, release: the same discipline explore.py follows."""

    def __init__(self, name, actor):
        if not SESSION_NAME.match(str(name)):
            # review 29 Sep: any string became a file path, `..` included, and was created and saved
            raise BadRequest(f"no session named {str(name)[:80]!r}: a session name is letters, digits, _ @ - (at most 64; no . or slashes)")
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
        # 29 Sep, three residents live: every request rewrote the whole world, a painter's poll included, and each
        # rewrite moved the file's time so the house reloaded it under the lock on every pass. A request that
        # changed nothing now writes nothing.
        per[self.actor] = (desk.seen, desk.open, desk.last_event_seen)
        self.before = pickle.dumps(desk) if self.path.exists() else None
        return desk

    def __exit__(self, *exc):
        try:
            d = self.desk
            self.per[self.actor] = (d.seen, d.open, d.last_event_seen)
            now = pickle.dumps(d)
            if now != self.before:
                explore.save_desk(self.path, d, now)
        finally:
            explore.release_lock(self.lock)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(STATIC), **kw)

    def log_message(self, *a):
        pass

    def end_headers(self):
        # the painter's files change under live building: a browser must ask again each time (a 304 is cheap), or a
        # page reloaded for new code runs yesterday's lens.js (29 Sep: the fold label did not appear until a hard reload)
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def _json(self, obj, code=200, body=None):
        body = body if body is not None else json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _foreign(self):
        """A request a page from another site sent. Browsers name the sender (Origin, Sec-Fetch-Site); deskd's own
        pages are same-origin. Review 29 Sep: any web page could POST a command to /api/do. Local programs that send
        neither header (explore.py, the house) are not browsers and are let through, as before: nothing authenticates."""
        port = self.server.server_address[1]
        origin = self.headers.get("Origin")
        own = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
        return (origin is not None and origin not in own) or self.headers.get("Sec-Fetch-Site") == "cross-site"

    def do_GET(self):
        if self.path.startswith("/api/") and self._foreign():
            return self._json({"error": "deskd answers only its own pages"}, 403)
        try:
            return self._get()
        except BadRequest as e:
            return self._json({"error": str(e)}, 400)

    def do_POST(self):
        if self._foreign():
            return self._json({"error": "deskd answers only its own pages"}, 403)
        try:
            return self._post()
        except BadRequest as e:
            return self._json({"error": str(e)}, 400)
        except ValueError:
            return self._json({"error": "the body must be JSON"}, 400)

    def _get(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/api/snapshot":
            with Session(q.get("session", "desktop"), q.get("as")) as desk:
                snap = snapshot_for(desk)
            return self._json(snap)
        if u.path == "/api/scene":
            import scene
            key = _scene_key(q)
            if key is not None and key in _SCENES:
                gen, body = _SCENES[key]
                if q.get("have") == gen:                 # the painter already has this build: say so in a few bytes
                    return self._json({"same": True, "gen": gen})
                return self._json(None, body=body)       # the bytes already built: no load, no build, no encode
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
            # names this build, so a painter compares a word, not 700 KB. a1505: by its content, so the same scene from
            # a deskd started after a landing has the same name, and the painter is told `same` in a few bytes
            import hashlib
            out["gen"] = "g" + hashlib.sha1(json.dumps(out, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
            body = json.dumps(out, ensure_ascii=False).encode("utf-8")
            if key is not None and key == _scene_key(q):     # unchanged while it was built: keep it (a few, the newest)
                _SCENES[key] = (out["gen"], body)
                while len(_SCENES) > 16:
                    _SCENES.pop(next(iter(_SCENES)))
            if q.get("have") == out["gen"]:
                return self._json({"same": True, "gen": out["gen"]})
            return self._json(None, body=body)
        if u.path == "/api/version":
            # live building: the code this deskd runs (a1505: the commit the door started it on), `painter`, the hash
            # of the painter's own files (a page offers its person the new one when it changes), and `shape`, the
            # scene shape this code sends (a page reloads on its own only when it can't read that)
            import scene
            return self._json({"code": CODE_VERSION, "painter": painter_version(), "shape": scene.PAINTER_SHAPE})
        if u.path == "/api/health":
            # a1505: the door asks this of a deskd it has just started, before any page is sent to it (and then the
            # scenes it has recently served, built by this process). Loads no session.
            return self._json({"ok": True, "code": CODE_VERSION, "pid": os.getpid()})
        if u.path == "/api/commission":
            # a3198: the door's `home` asks whose commission a visitor is back from, to say whose word lived= is
            import promises
            with Session(q.get("session", "desktop"), q.get("as")) as desk:
                return self._json(promises.commission_of(desk.world, q.get("card", "")))
        if u.path == "/api/style":
            # F7: a style is world data (a note tagged style); the seed file answers only when the world has none
            import scene
            with Session(q.get("session", "desktop"), q.get("as")) as desk:
                st = scene.style_source(desk, q.get("name") or "calm")
            return self._json(st or {"refused": f"no style {q.get('name')!r}"})
        if u.path == "/api/events":
            since = int(q.get("since", 0))
            # a1505: the door asks this twice a second for each page it holds; a world file unchanged since the last
            # answer has no new events, and is not loaded (8 MB) to say so
            name = q.get("session", "desktop")
            try:
                st = (SESSIONS / f"{name}.pickle").stat() if SESSION_NAME.match(str(name)) else None
            except OSError:
                st = None
            seen = _EVENTS.get(name)
            if st is not None and seen and seen[:2] == (st.st_mtime_ns, st.st_size) and since >= seen[2]:
                return self._json({"events": [], "total": seen[2]})
            with Session(name, q.get("as")) as desk:
                evs = [{k: v for k, v in e.items() if k != "undo"} for e in desk.world.events[since:]]
                total = len(desk.world.events)
            if st is not None:
                _EVENTS[name] = (st.st_mtime_ns, st.st_size, total)
            return self._json({"events": evs, "total": total})
        return super().do_GET()

    def _post(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if not isinstance(body, dict):
            raise BadRequest("the body must be a JSON object")
        if urlparse(self.path).path == "/api/observe":
            # a painter reports what happened on its screen. Not an event, not undoable, not the world: a viewer's observation.
            with Session(body.get("session", "desktop"), body.get("as")) as desk:
                views = getattr(desk, "_views", None)
                if views is None:
                    views = desk._views = {}
                facts = {str(k)[:200]: str(v)[:60] for k, v in list((body.get("facts") or {}).items())[:400]}
                # a1473: each painted part's box ("WxH sh=.. cut=n/m" or "hidden"), and the lens frame it was painted at
                boxes = {str(k)[:200]: str(v)[:60] for k, v in list((body.get("boxes") or {}).items())[:6000]}
                p = body.get("painted") if isinstance(body.get("painted"), dict) else {}
                views[(body.get("as") or "alex").lower()] = {"lens": str(body.get("lens", "")).lower(), "at": int(body.get("at", 0)),
                                                            "time": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                                                            "viewport": body.get("viewport"), "facts": facts, "boxes": boxes,
                                                            "painted": {"frame": str(p.get("frame") or "")[:400], "style": str(p.get("style") or "")[:80]} if p else None}
            return self._json({"ok": True, "kept": len(facts)})
        if urlparse(self.path).path != "/api/do":
            return self._json({"error": "POST /api/do or /api/observe"}, 404)
        line = str(body.get("line", "")).strip()
        if not line:
            return self._json({"error": "line is required: every gesture is a command"}, 400)
        # a1008: one intent, one event. A gesture carries an id minted where the person pressed, kept unchanged across
        # repaints and retries. If an event already carries it, nothing new is done and the answer names that event.
        # Judged before any fence: the world may have moved because of the first send itself. By id only, never by
        # words (the same words pressed twice are two lines). The id is kept on the event, so a restart forgets nothing.
        gid = body.get("gesture")
        if gid is not None and not (isinstance(gid, str) and 0 < len(gid) <= 80):
            raise BadRequest("gesture must be a short string (at most 80 characters), minted where the person pressed")
        sess = Session(body.get("session", "desktop"), body.get("as"))
        with sess as desk:
            before, n0 = set(desk.world.nodes), len(desk.world.events)
            done = [e for e in desk.world.events if gid and e.get("gesture") == gid]
            if done:
                return self._json({"text": f"already done, as {done[0]['id']}: this gesture was acted on at {done[0].get('at', '?')}; "
                                   "nothing new was done", "error": None, "events_total": n0, "line": line,
                                   "as": (body.get("as") or "alex"), "created": [], "events": [], "already": [e["id"] for e in done],
                                   "code": CODE_VERSION})
            ob = body.get("observed") or {}
            d = ob.get("def") or {}
            lens_id = d.get("id")                   # a990: the lens a gesture was painted by (d may be reassigned below)
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
                    if not same_answer(desk, rev, fields, entry[3] if len(entry) > 3 else None, entry[4] if len(entry) > 4 else None)[0]:
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
                else:
                    # 30 Sep (Alex's wake/rest buttons were always refused): unchanged since it was painted means what
                    # was painted is current, so it is seen now. Noting nothing left every aspect unseen since event 0,
                    # and the desk's own fence then refused the press over any old change to it (e903, a prop of mine).
                    desk._note_seen(ob["item"], len(desk.world.events), None, obs=sess.actor)
            for entry in (ob.get("reads") or []):
                # Pike F1: a gesture is judged on every value its line was built from, not only the clicked item.
                # Juniper's stale "move to Sun": the item and the lens were unchanged, the trip's start had moved.
                sid, rev, fields = (list(entry) + [None, None])[:3]
                if sid == "select":
                    # sable-8 amended: the chain's bind is a membership read; "mark done" must not land on a task that
                    # left the person's list, and `the` must not act through a match that became ambiguous
                    same, now = same_answer(desk, rev, fields, entry[3] if len(entry) > 3 else None, entry[4] if len(entry) > 4 else None)
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
                # a990 (3): a lens act is a template that stands in its own home: a bare word in it is looked up from
                # the room its lens lives in, strictly, never from where the person clicking is
                import verbs
                desk._act_home = (verbs.room_holding(desk.world, lens_id),) if lens_id in desk.world.subjects else None
                # a1156: and its words mean what they were bound to when the lens was saved (the lenses it was built
                # from too, the painted one first); a wake the house sends (stored=<corner>) stands in its corner
                desk._act_binds = verbs.lens_binds(desk.world, [lens_id] + [c.get("id") for c in (ob.get("def") or {}).get("closure") or []]) \
                    if desk._act_home else None
                if body.get("stored") in desk.world.nodes:
                    desk._act_home, desk._act_binds = verbs.stored_at(desk.world, body["stored"])
                # a1581 (Sable c1579): a chat line keeps the press it came from, so the world itself refuses a second
                # line from one Enter, whichever door brought it
                desk.world.intent, desk.world._intent_k = gid, 0
                try:
                    r = desk.dispatch("desk", {"line": line, "whole": bool(body.get("whole")),    # a736: a > line is one command
                                               "reply": str(body.get("reply") or "") or None})   # a806: $new within one reply
                finally:
                    desk._act_home = desk._act_binds = None
                    desk.world.intent = None
                worktree.record(desk, line, sess.actor, allids, n0)
            total = len(desk.world.events)
            created = [i for i in desk.world.nodes if i not in before]      # Wren: the ids a command made, machine-readably
            events = [e["id"] for e in desk.world.events[n0:]]
            if gid:
                for e in desk.world.events[n0:]:
                    e["gesture"] = gid          # a1008: kept on what it made, saved with the world
        text = r.get("text") or ""
        # Rook: a parse failure came back as error=null. And a refusal in the second step of `look x; do y` hid in the text.
        bad = [l for l in text.splitlines() if l.startswith("ERR")]
        refused = r.get("error") or (bad[0] if bad else None)
        self._json({"text": r.get("text"), "error": refused, "events_total": total, "line": line,
                    "as": (body.get("as") or "alex"), "created": created, "events": events,
                    "code": CODE_VERSION})       # a1505 (vii, Sable a1201): which code answered, told apart across a swap


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8780
    SESSIONS.mkdir(exist_ok=True)
    STATIC.mkdir(exist_ok=True)
    print(f"deskd on http://localhost:{port}  static={STATIC}", flush=True)
    if os.environ.get("DESKD_PARENT"):
        # a1505: a deskd the door started goes when the door goes (a stopped door on Windows leaves its children running)
        def orphaned(pid=int(os.environ["DESKD_PARENT"])):
            while explore._alive(pid):
                time.sleep(3)
            os._exit(0)
        __import__("threading").Thread(target=orphaned, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
