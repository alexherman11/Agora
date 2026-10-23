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
GET  /api/map?session=&as=&scope=<f123>         a7950: the living map's agora-map/1 draw from pin and route notes, and
                                                 the problems (map_seam.py); reads only
POST /api/map  {"session", "as", "scope", "message"}   one map-frame message checked: the line and
                                                 fence it means, or {"refused": why}; it runs nothing (the host sends
                                                 the line to /api/do)
Under the keeper it runs behind door.py (a1505), which swaps it for one on new code; see door.py.
GET  /anything-else                              static files from static_dir (the shell); /map/ground/<four files>
                                                 from research/map-lab/ground (a7950: the map frame)

The server and `python explore.py <session> --as <name>` share sessions: both take the same per-session lock from
load to save, so a person in the browser and an agent in a terminal work in one world. Every gesture the shell
makes must arrive here as a command line; there is no other way to change the world.
"""

import json
import os
import pickle
import re
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import deployment_preflight
# Capture before loading selectors/desk modules. Only the explicit installer
# route uses this receipt; ordinary world gestures keep their existing fences.
_SOURCE_ROOT = Path(__file__).resolve().parents[3]
_STARTUP_SOURCES = deployment_preflight.runtime_sources(_SOURCE_ROOT)

import reports
import scene
from desk import aspects_of, aspects_meet, event_aspects

import explore
import store
import worktree

HERE = Path(__file__).resolve().parent
SESSIONS = HERE / "sessions"
STATIC = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else HERE / "desk-shell"
MAP_GROUND = HERE.parents[1] / "map-lab" / "ground"          # a7950: the map frame, ground's (a7946)
MAP_GROUND_FILES = ("map.html", "map.js", "geo.js", "fixture.js")


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
        now = moo.sort_by(now, by, lambda x, k: moo.props_of(w, x[0] if isinstance(x, list) else x).get(k))
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
        return scene.defpart_hash(lens.get("text") or "", dp["path"], scene.style_roles(desk, style, scene.room_of_thing(desk.world, lens)), style) == dp["hash"]
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
    who = (q.get("as") or "alex").lower()
    import witnessed                             # a5052: rows a program keeps beside the house (`windows`) are read too
    return (name, who, q.get("lens", ""), q.get("on", ""), q.get("view"), q.get("text"), st.st_mtime_ns, st.st_size, _VERSION.get(name, 0), _LOOKED.get((name, who), 0), house,
            int(time.time() // 60), visits, q.get("keys"), witnessed.stamp(name))


_STARTED = time.strftime("%Y-%m-%dT%H:%M:%S")
_HOUSE = []


def _house():
    """a4869: the first request this process answers makes it the receiver of painters' reports (reports.py) for its
    house: the door it runs behind (DESKD_PARENT), or itself when it runs alone. A test that only opens Sessions is not
    a house, and leaves the reports kept beside the live world alone."""
    if not _HOUSE:
        _HOUSE.append(True)
        reports.serve(os.environ.get("DESKD_PARENT") or os.getpid(), _STARTED)


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


_DESKS = {}      # world file -> ((its time, its size), the desk as this process last saved or loaded it, {actor: its pickle})

# 14 Oct (Alex: 'the whole interface is super slow'; the lock was held 41% of 20 s, 39 holds, median 191 ms): one line
# per request that takes a world's lock, saying what asked, how long it waited and held, and whether it saved, so the
# queue's makeup is read, not guessed. house-state/deskd-trace.log, cut to its last 2 MB. DESKD_TRACE=off stops it.
_REQ = __import__("threading").local()
TRACE = Path(__file__).resolve().parent / "house-state" / "deskd-trace.log"


# 14 Oct (Snappy Desk, stage 1, step 2; Alex approved: the log is the world's record, and one writer). The deskd that
# holds a world's writer lease (<world>.writer beside it) keeps the world in memory: a command appends its record to
# the log (store.py, flushed to disk before anyone is answered) and the world's file is saved in the background, at
# a second's pause (or every ten while busy), instead of the whole world being copied and written on every request. Any other process that
# reads the file puts on the records written since (store.catch_up); any other writer is refused (explore.save_desk).
# A new deskd (a landing) asks the holder to save and let go at its first change; a holder that died is replaced, and
# its world is read back with its log. DESKD_HOLD=off keeps the old way: copy and save on every request.
HOLD = [False]           # set by the server's main: a Session opened by a test or a tool in-process never holds
PORT = [None]
LEASES, RELEASED, _DIRTY, _VERSION = {}, set(), {}, {}
_LOOKS_UNSAVED = {}              # world -> looked at since its file was saved (saved when it is let go, not for that alone)
_LOOKED = {}                     # (world, person) -> how many times they looked without changing it (their views' cache)
_CHANGED, _SNAPPED = {}, {}      # world -> when it last changed in memory / was last saved to its file
SNAPSHOT_QUIET, SNAPSHOT_MOST = 1.0, 10.0       # saved after a second with no change, or every ten while busy


def _trim():
    """At most three worlds kept in memory, the oldest let go first; never one held with changes its file lacks."""
    for key in list(_DESKS):
        if len(_DESKS) <= 3:
            return
        name = Path(key).stem
        if not (LEASES.get(name) and _DIRTY.get(name)):
            _DESKS.pop(key, None)


def _lease_file(name):
    return SESSIONS / f"{name}.writer"


def _ask_release(name):
    """Another live deskd holds the lease (the one before a landing): ask it to save and let go. -> True if it did."""
    try:
        lease = json.loads(_lease_file(name).read_text(encoding="utf-8"))
        port = int(lease.get("port"))
        req = __import__("urllib.request").request.Request(f"http://127.0.0.1:{port}/api/release",
                                                           json.dumps({"session": name}).encode(),
                                                           {"Content-Type": "application/json"})
        with __import__("urllib.request").request.urlopen(req, timeout=15) as r:
            return bool(json.loads(r.read()).get("released"))
    except Exception:      # noqa: BLE001
        return False


def _hold(name):
    """Called before a change takes the world's lock. -> True when this process holds the lease (it may keep the world
    in memory); False when it must save as before. Refuses (BadRequest) when another live deskd holds it and will not
    let go, since a second writer would lose its newer world."""
    if not HOLD[0] or os.environ.get("DESKD_HOLD") == "off" or name in RELEASED:
        return False
    if LEASES.get(name):
        return True
    path, until = SESSIONS / f"{name}.pickle", time.time() + 20
    if not store.log_path(path).exists():
        return False          # a world with no log has no record but its file: saved at every change, as before
    other = explore.holder_of(path)
    while other is not None and other != os.getpid() and not _ask_release(name):
        # the one before may be going (the door stops it after it saves): asked again until it is gone or answers
        if time.time() > until:
            raise BadRequest(f"{name} is held by another world server (pid {other}) that did not let go; nothing was "
                             f"done, try again in a moment")
        time.sleep(0.1)
        other = explore.holder_of(path)
    return None          # free now: taken under the lock (Session.__enter__), where no one else can take it between


def _take_lease(name):
    other = explore.holder_of(SESSIONS / f"{name}.pickle")
    if other is not None and other != os.getpid():
        return False
    _lease_file(name).write_text(json.dumps({"pid": os.getpid(), "port": PORT[0], "code": CODE_VERSION,
                                             "since": time.strftime("%Y-%m-%dT%H:%M:%S")}), encoding="utf-8")
    LEASES[name] = True
    return True


def _snapshot(name, under_lock=False, looks=False):
    """Save the world this process holds in memory to its file, when something changed since the last save."""
    path, lock = SESSIONS / f"{name}.pickle", SESSIONS / f"{name}.lock"
    if not under_lock:
        _take(name, lock)
    try:
        t0 = time.time()
        held = _DESKS.get(str(path))
        if held is None or not (_DIRTY.get(name) or (looks and _LOOKS_UNSAVED.get(name))):
            return False
        d = held[1]
        import kept
        kept.sweep(d.world, path)
        store.mark_snapshot(d, path)
        data = pickle.dumps(d)
        explore.save_desk(path, d, data)
        st = path.stat()
        _DESKS[str(path)] = ((st.st_mtime_ns, st.st_size), d, {})
        _DIRTY[name], _SNAPPED[name], _LOOKS_UNSAVED[name] = False, time.time(), False
        _trace(f"{time.strftime('%H:%M:%S')} {name} - snapshot wait=0 held={(time.time() - t0) * 1000:.0f} saved=yes")
        return True
    finally:
        if not under_lock:
            _give(name, lock)


def _snapshotter():
    while True:
        time.sleep(0.25)
        now = time.time()
        for name in [n for n, dirty in list(_DIRTY.items()) if dirty and LEASES.get(n)]:
            if now - _CHANGED.get(name, 0) < SNAPSHOT_QUIET and now - _SNAPPED.get(name, 0) < SNAPSHOT_MOST:
                continue          # still being changed: the log has it, and the file waits for a pause
            try:
                _snapshot(name)
            except Exception:      # noqa: BLE001
                store._fault(store.log_path(SESSIONS / f"{name}.pickle"), f"snapshot of {name}")


def _release(name):
    """Asked by the deskd that comes next: save now, give the lease back, and never take it again."""
    lock = SESSIONS / f"{name}.lock"
    _take(name, lock)
    try:
        if LEASES.get(name):
            import log_world
            held = _DESKS.get(str(SESSIONS / f"{name}.pickle"))
            if held:
                try:
                    log_world.detach(held[1], SESSIONS / f"{name}.pickle", "writer lease released")
                except Exception:
                    store._fault(store.log_path(SESSIONS / f"{name}.pickle"), "log-world release report failed")
            _snapshot(name, under_lock=True, looks=True)       # its people's seen marks too: the next one starts from them
            LEASES[name] = False
            try:
                if explore.holder_of(SESSIONS / f"{name}.pickle") == os.getpid():
                    _lease_file(name).unlink()
            except OSError:
                pass
        RELEASED.add(name)
        _DESKS.pop(str(SESSIONS / f"{name}.pickle"), None)
        return True
    finally:
        _give(name, lock)


# a6153: the world's lock was a file alone, tried every 50 ms, so two requests of this one process (a press behind a
# page's build, or behind the background save) waited in steps of 50 ms: live, Alex's requests waited a median 58 ms
# and up to 1.3 s while the lock was held under 1% of the time. Threads of this process now queue on a lock of their
# own first, woken the moment it is let go; the file lock is still taken after it, for any other process.
_LOCKS, _LOCKS_GUARD = {}, __import__("threading").Lock()


def _take(name, lock):
    with _LOCKS_GUARD:
        mine = _LOCKS.setdefault(name, __import__("threading").RLock())
    if not mine.acquire(timeout=60):
        raise SystemExit(f"could not take {lock.name} after 60s; a request of this server holds it")
    try:
        explore.take_lock(lock, tries=1200, pause=0.05)
    except BaseException:
        mine.release()
        raise


def _give(name, lock):
    try:
        explore.release_lock(lock)
    finally:
        _LOCKS[name].release()


def _trace(line):
    if os.environ.get("DESKD_TRACE") == "off":
        return
    try:
        if TRACE.exists() and TRACE.stat().st_size > 2_000_000:
            TRACE.write_text(TRACE.read_text(encoding="utf-8")[-1_000_000:], encoding="utf-8")
        with TRACE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


class ObserverReleased(RuntimeError):
    pass


class Session:
    """Load under the lock, act, save, release: the same discipline explore.py follows."""

    def __init__(self, name, actor, read=False, observer=False):
        # 14 Oct (deskd trace: page builds and event checks held the lock 21 s in 3 minutes, a third of it pickling the
        # whole world twice to learn they had changed nothing): `read` is a request that only looks. It copies nothing
        # and saves nothing; whatever it touched in memory (a viewer's seen-marks) is saved with the next change to the
        # world, and a deskd swapped for new code before then forgets it (the viewer sees 'since your last look' again)
        self.read, self.hold = read, False
        self.observer = observer
        if not SESSION_NAME.match(str(name)):
            # review 29 Sep: any string became a file path, `..` included, and was created and saved
            raise BadRequest(f"no session named {str(name)[:80]!r}: a session name is letters, digits, _ @ - (at most 64; no . or slashes)")
        # interned: a line's event keeps its actor's name, and a pickle writes one string object once; the same name as a
        # new object in the next request pickled the same world to different bytes (a4465: every read after a line saved)
        self.name, self.actor = sys.intern(str(name)), sys.intern(str(actor or "alex").lower())
        self.path = SESSIONS / f"{name}.pickle"
        self.lock = SESSIONS / f"{name}.lock"

    def __enter__(self):
        self._t0 = time.perf_counter()
        hold = True if self.observer else False if self.read else _hold(self.name)
        _take(self.name, self.lock)
        self._t1 = time.perf_counter()
        try:
            if self.observer and not LEASES.get(self.name):
                raise ObserverReleased("the writer lease ended")
            desk = self._enter_locked(hold)
            self._writer_thread = threading.get_ident()
            self._atomic_unknown = False
            return desk
        except BaseException:
            _give(self.name, self.lock)          # a6153: never left held (the in-process lock has no stale-age escape)
            raise

    def _enter_locked(self, hold):
        if not self.read:
            try:
                explore.admit_writer(self.path)
            except RuntimeError as exc:
                raise BadRequest(str(exc)) from None
        self.hold = _take_lease(self.name) if hold is None else hold
        # 7 Oct: the desk this process last saved or loaded is kept in memory, and used again while the file is still
        # that one (same time and size: nobody else wrote it). Reading and unpickling 13 MB was 80 to 110 ms a request.
        # Always under the session's lock, as before; the file stays the truth, and any other writer's save is seen
        key, desk = str(self.path), None
        try:
            st = self.path.stat()
            self.stamp = (st.st_mtime_ns, st.st_size)
        except OSError:
            self.stamp = None
        held = _DESKS.get(key)
        self.pickled, before = {}, None
        if hold is None and held is not None:
            # the lease taken just now: what this process kept from before (a read, while another held the world) may
            # be behind the log the other wrote. Read again, file and log (test_door: one press in 72 was lost here)
            _DESKS.pop(key, None)
            held = None
        elif held is not None and not LEASES.get(self.name) and held[0] == self.stamp and store.catch_up(held[1], self.path):
            held = _DESKS[key] = (held[0], held[1], {})      # another holds it: what it logged since is put on
        if held is not None and self.stamp is not None and held[0] != self.stamp and LEASES.get(self.name):
            # the lease's holder is the one writer: a file changed under it was written by someone who should not have,
            # and the world in memory is newer than it. Kept; said in the log's faults
            store._fault(store.log_path(self.path), f"{self.name}: the file changed under the world server that holds it")
            self.stamp = held[0]
        if held is not None and self.stamp is not None and held[0] == self.stamp:
            desk = held[1]
            # 13 Oct (a4465: a click took 600 ms, 100 of each request pickling the 18 MB world twice, reads too): the
            # pickle this actor's last request ended with is the `before` of their next one, while the desk in memory
            # is still that one. Only for an actor the desk already knows: entering as them then changes nothing
            self.pickled = held[2]
            before = self.pickled.get(self.actor) if self.actor in (getattr(desk, "_per", None) or {}) else None
        else:
            _DESKS.pop(key, None)
            desk = explore.load_desk(self.path) if self.stamp is not None else explore.fresh()
            # a4869: painters' reports were kept in the world until 14 Oct; now beside it (reports.py). Dropped before
            # `before` is taken, so it costs no write of its own: it leaves the file with the next change
            desk.__dict__.pop("_views", None)
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
        # Snappy Desk stage 4 (14 Oct, looking never writes): what the world was before, cheaply, so a held request that
        # changed no fact of it (a look, a read, a view's request) is not a reason to save it
        self._facts0 = (len(desk.world.events), store.log_path(self.path).stat().st_size if store.log_path(self.path).exists() else 0)
        # The checker belongs to the single writer, never to a served/copied
        # replay session. Full replay/comparison and receipt I/O run off-lock.
        if not self.read and self.hold:
            import log_world

            def publish(name=self.name):
                try:
                    with Session(name, "house", observer=True):
                        pass              # may use this lease, never ask another writer to release its lease
                except ObserverReleased:
                    pass

            try:
                log_world.attach(desk, self.path, publish)
                log_world.project(desk, self.path)
            except Exception:
                # An observer cannot refuse the person's press.
                checker = log_world._CHECKERS.get(str(self.path))
                if checker:
                    checker.unavailable("writer bridge could not finish publishing its report")
                store._fault(store.log_path(self.path), "log-world bridge failed")
        if self.read or (self.hold and self.stamp is not None):
            self.before = None
            return desk
        self.before = before if before is not None else pickle.dumps(desk) if self.path.exists() else None
        return desk

    def atomic(self, operation_id, observed, steps):
        """Internal admission, not a public route or caller authentication.

        A future public adapter still needs ordinary source/actor/receiver checks.
        """
        if self.read or self.observer or getattr(self, "_writer_thread", None) != threading.get_ident():
            raise BadRequest("atomic admission needs this thread's active writer Session")
        if self._atomic_unknown:
            raise BadRequest("reopen the Session to reconcile an unknown atomic outcome")
        import atomic_world
        try:
            return atomic_world.execute(self, operation_id, observed, steps)
        except atomic_world.UnknownCommit:
            self._atomic_unknown = True
            raise

    def atomic_undo(self, operation_id, observed, original_operation):
        """Whole-record undo through the same strict, isolated admission."""
        if self.read or self.observer or getattr(self, "_writer_thread", None) != threading.get_ident():
            raise BadRequest("atomic undo needs this thread's active writer Session")
        if self._atomic_unknown:
            raise BadRequest("reopen the Session to reconcile an unknown atomic outcome")
        import atomic_world
        try:
            return atomic_world.undo(self, operation_id, observed, original_operation)
        except atomic_world.UnknownCommit:
            self._atomic_unknown = True
            raise

    def atomic_status(self, operation_id):
        """Reconcile a durable operation identity without admitting a mutation."""
        if self.read or self.observer or getattr(self, "_writer_thread", None) != threading.get_ident():
            raise BadRequest("atomic reconciliation needs this thread's active writer Session")
        if self._atomic_unknown:
            raise BadRequest("reopen the Session to reconcile an unknown atomic outcome")
        import atomic_world
        try:
            return atomic_world.status(self, operation_id)
        except atomic_world.UnknownCommit:
            self._atomic_unknown = True
            raise

    def __exit__(self, *exc):
        try:
            if getattr(self, "_atomic_unknown", False):
                # A full durable record may exist despite a failed response.
                _DESKS.pop(str(self.path), None)
                return
            d = self.desk
            self.per[self.actor] = (d.seen, d.open, d.last_event_seen)
            if self.read:
                # the desk in memory may now differ from the file (seen-marks): kept, and no one's last pickle stands
                # for it any more, so the next request that changes anything compares against a fresh one and saves
                if self.stamp is not None:
                    _DESKS[str(self.path)] = (self.stamp, d, {})
                    _trim()
                return
            if self.hold and self.stamp is not None and getattr(d, "_snap_at", None):
                # the world stays in memory (a file that does not yet say which record of the log it holds is saved
                # once the old way below, so that a world read back from it knows which records to put on); its record is on the log already, and the file is saved in the background
                # A request that added no event and no record changed no fact (a look moves only that person's seen
                # marks, kept in memory and saved with the next change): nothing to save, and no view is stale
                lp = store.log_path(self.path)
                if (len(d.world.events), lp.stat().st_size if lp.exists() else 0) != self._facts0:
                    _DIRTY[self.name], _CHANGED[self.name] = True, time.time()
                    _VERSION[self.name] = _VERSION.get(self.name, 0) + 1
                    _SNAPPED.setdefault(self.name, time.time())
                else:
                    self._looked = True           # only this person's view of it may differ (since-your-last-look)
                    _LOOKED[(self.name, self.actor)] = _LOOKED.get((self.name, self.actor), 0) + 1
                    _LOOKS_UNSAVED[self.name] = True
                _DESKS[str(self.path)] = (self.stamp, d, {})
                return
            import kept
            kept.sweep(d.world, self.path)      # 7 Oct: the copies undo keeps go beside the file (kept.py), before it is saved
            store.mark_snapshot(d, self.path)   # which record of the log the file holds (store.catch_up reads it)
            now = pickle.dumps(d)
            key = str(self.path)
            if now != self.before:
                _DESKS.pop(key, None)             # if the save fails, what is in memory is not what the file says
                explore.save_desk(self.path, d, now)
                self._saved = True
                _VERSION[self.name] = _VERSION.get(self.name, 0) + 1
                st = self.path.stat()
                self.stamp = (st.st_mtime_ns, st.st_size)
                self.pickled = {}                 # the world moved: nobody else's last pickle is of this one
            if self.stamp is not None:
                self.pickled.pop(self.actor, None)
                self.pickled[self.actor] = now
                while len(self.pickled) > 2:      # the two who asked last: each is the whole world's size
                    self.pickled.pop(next(iter(self.pickled)))
                _DESKS[key] = (self.stamp, d, self.pickled)
                _trim()
        except BaseException:
            _DESKS.pop(str(self.path), None)
            raise
        finally:
            self._writer_thread = None
            try:
                if self.observer:
                    import log_world
                    checker = log_world._CHECKERS.get(str(self.path))
                    if checker:
                        ms = (time.perf_counter() - self._t1) * 1000
                        checker.publish_lock_ms = {"last": ms, "max": max(ms, checker.publish_lock_ms["max"])}
            finally:
                _give(self.name, self.lock)
            t2 = time.perf_counter()
            _trace(f"{time.strftime('%H:%M:%S')} {self.name} {self.actor} {getattr(_REQ, 'what', '?')} "
                   f"wait={(self._t1 - self._t0) * 1000:.0f} held={(t2 - self._t1) * 1000:.0f} "
                   f"saved={'yes' if getattr(self, '_saved', False) else 'looked' if getattr(self, '_looked', False) else 'held' if self.hold else 'no'}")


def _map_scope(v):
    """a7950: a map's scope is one surface id (f123), or nothing for the whole world."""
    if v in (None, ""):
        return None
    if not isinstance(v, str) or not re.fullmatch(r"f[0-9]{1,9}", v):
        raise BadRequest("scope must be a surface id (f123), or empty")
    return v


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(STATIC), **kw)

    def log_message(self, *a):
        pass

    def translate_path(self, path):
        # a7950 (Pike c8178): the living map's real frame is ground's (research/map-lab/ground, a7946), served under
        # /map/ground/ for the map host to hold sandboxed. These four files only; nothing else of that folder
        p = urlparse(path).path
        if p.startswith("/map/ground/") and p[len("/map/ground/"):] in MAP_GROUND_FILES:
            return str(MAP_GROUND / p[len("/map/ground/"):])
        return super().translate_path(path)

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
        _house()
        if (self.path.startswith("/api/") or self.path.startswith("/media/")) and self._foreign():
            return self._json({"error": "deskd answers only its own pages"}, 403)
        try:
            return self._get()
        except BadRequest as e:
            return self._json({"error": str(e)}, 400)

    def do_POST(self):
        _house()
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
        _REQ.what = u.path.rsplit("/", 1)[-1] + (":" + q["lens"] if q.get("lens") else "")
        if u.path == "/api/snapshot":
            with Session(q.get("session", "desktop"), q.get("as")) as desk:
                snap = snapshot_for(desk)
            return self._json(snap)
        if u.path == "/api/map":
            # a7950: the living map's 'draw', built from pin and route notes (map_seam.py); reads only
            import map_seam
            scope = _map_scope(q.get("scope"))
            with Session(q.get("session", "desktop"), q.get("as"), read=True) as desk:
                return self._json(map_seam.draw(desk.world, scope))
        if u.path == "/api/scene":
            import scene
            key = _scene_key(q)
            if key is not None and key in _SCENES:
                gen, body = _SCENES[key]
                if q.get("have") == gen:                 # the painter already has this build: say so in a few bytes
                    return self._json({"same": True, "gen": gen})
                return self._json(None, body=body)       # the bytes already built: no load, no build, no encode
            with Session(q.get("session", "desktop"), q.get("as"), read=True) as desk:
                try:
                    # a5949 (Sable's a4270): on=<id> in the address stands the lens on that thing
                    # a6153: text=0 from a painter that shows no scene text (lens.html with its inspector off)
                    build = lambda: scene.scene_for(desk, q.get("lens", ""), on=q.get("on") or None, text=q.get("text") != "0")  # noqa: E731
                    if os.environ.get("DESKD_PROFILE_SCENES"):
                        # a6153: each build profiled into that folder (scene-<n>-<lens>.prof), to read where a real page's
                        # builds go (research/window-lab/press-speed/read_profiles.py); off unless set
                        import cProfile
                        pr = cProfile.Profile()
                        sc, text = pr.runcall(build)
                        d = Path(os.environ["DESKD_PROFILE_SCENES"])
                        d.mkdir(parents=True, exist_ok=True)
                        pr.dump_stats(str(d / f"scene-{time.time_ns()}-{q.get('lens', '')}.prof"))
                    else:
                        import lens_ir
                        k0, m0 = lens_ir._STATS["kept"], lens_ir._STATS["made"]
                        sc, text = build()
                        # a6153: the trace says how much of each build was kept from the last (views by change)
                        _REQ.what += f" kept={lens_ir._STATS['kept'] - k0} made={lens_ir._STATS['made'] - m0}"
                    if q.get("view") == "painter":      # Pike a494: key, paint, acts, fence, kids; the root keeps its def
                        sc = dict(scene.painter_view(sc), **{"def": sc.get("def")})
                        # A retained page may still run the previous painter while
                        # its person types. Offer only key semantics it implements.
                        keys = set(q.get("keys", "Enter,Tab,Shift+Tab,Backspace").split(","))
                        for node in scene._walk(sc):
                            node["acts"] = [a for a in node["acts"] if a.get("on") != "key" or a.get("label") in keys]
                    out = {"scene": sc, "text": text, "events_total": len(desk.world.events)}
                except scene.LensRefusal as e:
                    out = {"refused": str(e), "events_total": len(desk.world.events)}
                except Exception as e:      # Astra: a compiler fault must arrive as a refusal, not as a dead endpoint
                    out = {"refused": f"the lens compiler failed ({type(e).__name__}: {e}); this is a bug in scene.py, not in your lens",
                           "events_total": len(desk.world.events)}
            # names this build, so a painter compares a word, not 700 KB. a1505: by its content, so the same scene from
            # a deskd started after a landing has the same name, and the painter is told `same` in a few bytes
            import hashlib
            # a6153: encoded once (it was twice, sorted for the name and again to send, ~14 ms each for the home base's
            # 1.4 MB): the name is of the bytes sent, which the same code builds in the same order
            body = json.dumps(out, ensure_ascii=False).encode("utf-8")
            out["gen"] = "g" + hashlib.sha1(body).hexdigest()[:16]
            body = body[:-1] + b', "gen": "' + out["gen"].encode() + b'"}'
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
            # F7: a style is world data (a note tagged style); the seed file answers only when the world has none.
            # 8 Oct: the answer carries `looks`, the style read once by style.py, so no painter parses style text;
            # a text the reader refuses comes with `refusal` and no looks, and the painter keeps its last style
            import scene
            import style
            with Session(q.get("session", "desktop"), q.get("as"), read=True) as desk:
                st = scene.style_source(desk, q.get("name") or "calm")
            return self._json(style.for_painter(st, q.get("theme")) if st else {"refused": f"no style {q.get('name')!r}"})
        if u.path == "/api/events":
            since = int(q.get("since", 0))
            # a1505: the door asks this twice a second for each page it holds; a world file unchanged since the last
            # answer has no new events, and is not loaded (8 MB) to say so
            name = q.get("session", "desktop")
            try:
                st = (SESSIONS / f"{name}.pickle").stat() if SESSION_NAME.match(str(name)) else None
            except OSError:
                st = None
            held = _DESKS.get(str(SESSIONS / f"{name}.pickle")) if st is not None else None
            if held is not None and LEASES.get(name):
                # Snappy Desk: the world this process holds is ahead of its file (saved in the background), and is the
                # world; read with no lock, since events are only ever appended
                evs_all = held[1].world.events
                total = len(evs_all)
                return self._json({"events": [{k: v for k, v in e.items() if k != "undo"} for e in evs_all[since:total]],
                                   "total": total})
            seen = _EVENTS.get(name)
            if st is not None and seen and seen[:2] == (st.st_mtime_ns, st.st_size) and since >= seen[2]:
                return self._json({"events": [], "total": seen[2]})
            # 14 Oct: the desk this process holds is the file's (same time and size): the events are read from it with
            # no lock, since events are only ever appended (58 checks by one page held the lock 6 s in 3 minutes)
            held = _DESKS.get(str(SESSIONS / f"{name}.pickle")) if st is not None else None
            if held is not None and held[0] == (st.st_mtime_ns, st.st_size):
                evs_all = held[1].world.events
                total = len(evs_all)
                evs = [{k: v for k, v in e.items() if k != "undo"} for e in evs_all[since:total]]
                _EVENTS[name] = (st.st_mtime_ns, st.st_size, total)
                return self._json({"events": evs, "total": total})
            with Session(name, q.get("as"), read=True) as desk:
                evs = [{k: v for k, v in e.items() if k != "undo"} for e in desk.world.events[since:]]
                total = len(desk.world.events)
            if st is not None:
                _EVENTS[name] = (st.st_mtime_ns, st.st_size, total)
            return self._json({"events": evs, "total": total})
        if u.path.startswith("/media/"):
            # a5941: a film or picture a `media` text names, from the folders the desk may show (media_links.FOLDERS)
            # and nowhere else; ranges, so a film seeks. Loads no session
            import media_links
            return media_links.serve(self, u.path)
        return super().do_GET()

    def _post(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        _REQ.what = urlparse(self.path).path.rsplit("/", 1)[-1] + (":" + "_".join(str(body.get("line") or "").split()[:2])[:40]
                                                                   if isinstance(body, dict) and body.get("line") else "")
        if not isinstance(body, dict):
            raise BadRequest("the body must be a JSON object")
        if urlparse(self.path).path == "/api/selection":
            import selection_snapshot
            with Session(body.get("session", "desktop"), body.get("as"), read=True) as desk:
                try:
                    return self._json({"selection": selection_snapshot.capture(desk, body.get("selection"))})
                except scene.Refusal as e:
                    return self._json({"error": str(e)})
        if urlparse(self.path).path == "/api/observe":
            # a painter reports what happened on its screen. Not an event, not undoable, not the world: a viewer's observation.
            # a4869: so it is kept beside the world by the house (reports.py), and the world file is neither loaded nor written
            name = body.get("session", "desktop")
            if not SESSION_NAME.match(str(name)) or not (SESSIONS / f"{name}.pickle").exists():
                raise BadRequest(f"no world named {str(name)[:80]!r} to report a view of")
            facts = {str(k)[:200]: str(v)[:60] for k, v in list((body.get("facts") or {}).items())[:400]}
            # a1473: each painted part's box ("WxH sh=.. cut=n/m" or "hidden"), and the lens frame it was painted at
            boxes = {str(k)[:200]: str(v)[:60] for k, v in list((body.get("boxes") or {}).items())[:6000]}
            p = body.get("painted") if isinstance(body.get("painted"), dict) else {}
            # a5047: the page's inner size and device pixel ratio, with every report (a page's size is not attention)
            g = body.get("page") if isinstance(body.get("page"), dict) else {}
            try:
                page = {"w": round(float(g["w"])), "h": round(float(g["h"])), "dpr": round(float(g.get("dpr") or 1), 3)} if g else None
            except (KeyError, TypeError, ValueError):
                page = None
            reports.keep(name, str(body.get("as") or "alex").lower(),
                         {"lens": str(body.get("lens", "")).lower(), "at": int(body.get("at", 0)),
                          "time": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                          "viewport": body.get("viewport"), "page": page, "facts": facts, "boxes": boxes,
                          "painted": {"frame": str(p.get("frame") or "")[:400], "style": str(p.get("style") or "")[:80]} if p else None})
            return self._json({"ok": True, "kept": len(facts)})
        if urlparse(self.path).path == "/api/release":
            # Snappy Desk: the deskd after this one (a landing) asks it to save the world it holds and let go
            if body.get("all"):           # the door, before it stops this deskd
                return self._json({"released": [n for n in [n for n, h in list(LEASES.items()) if h] if _release(n)]})
            name = str(body.get("session", ""))
            if not SESSION_NAME.match(name):
                raise BadRequest("release needs a session")
            return self._json({"released": _release(name)})
        if urlparse(self.path).path == "/api/style":
            # 8 Oct: a style text read by the one reader, for a page that edits a style it has not saved (the windowed
            # shell's style panel); nothing is stored
            import style
            return self._json(style.for_painter({"text": str(body.get("text", ""))}, body.get("theme")))
        if urlparse(self.path).path == "/api/map":
            # a7950: one message from a map frame, checked (map_seam.check). Nothing is run here: the answer is the one
            # line and the fence it was drawn at, which the host page sends to /api/do like any press, so the door's
            # routing, the fence, the event and its undo are the ones every gesture has
            import map_seam
            scope = _map_scope(body.get("scope"))
            with Session(body.get("session", "desktop"), body.get("as"), read=True) as desk:
                try:
                    return self._json(map_seam.check(desk.world, body.get("message"), scope))
                except map_seam.Refused as e:
                    return self._json({"refused": str(e)})
        deployment = urlparse(self.path).path == "/api/deploy"
        if urlparse(self.path).path not in ("/api/do", "/api/deploy"):
            return self._json({"error": "POST /api/do, /api/map, /api/observe or /api/style"}, 404)
        if deployment:
            try:
                deployment_preflight.require_activation(_SOURCE_ROOT, body.get("source_dependencies"),
                                                        CODE_VERSION, _STARTUP_SOURCES)
            except (deployment_preflight.SourceNotIntegrated, OSError) as exc:
                return self._json({"error": str(exc), "source_verified": False}, 409)
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
            if body.get("source_quote") is not None:
                import selection_snapshot
                try:
                    selection_snapshot.capture(desk, body["source_quote"])
                except scene.Refusal as e:
                    return self._json({"error": str(e), "events_total": n0})
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
                unchanged = cur is not None and (cur["rev"] == rev or (fields and not touched_aspects(desk.world, sid, rev, cur["rev"], fields)))
                if not unchanged:
                    return self._json({"text": None, "error": f"refused: a value this gesture was built from has changed: {sid} (you saw revision {rev}, "
                                       f"it is now {cur['rev'] if cur else 'gone'}); nothing was done. The view will repaint.",
                                       "events_total": len(desk.world.events), "line": line})
                # Each validated read belongs to its own thing. A command may change
                # several things shown together; recording every read on the clicked
                # item left the other targets unseen (and the command refused).
                desk.seen[sid] = cur["rev"]
                desk._note_seen(sid, len(desk.world.events), sorted(fields) if fields else None, obs=sess.actor)
            if car.get("item"):
                line = line.replace("$carried", car["item"])
            # 7 Oct: a world that has a log (store.py) gets one record per line: the facts it changed, written beside
            # the pickle. The world as facts before the line, and after it below; a fault in either is written down
            # and never refuses the line
            import store
            ctx = store.safe_begin(desk, sess.path)
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
                # a4164: a line the gate passed on is a human's; their person, if this act makes it, is kind=human
                desk.world.through_gate = sess.actor if body.get("came") == "gate" else None
                # a5068: where a resident's turn began (the house's news cursor), so its chat line is judged on that
                desk._as_of = int(body["as_of"]) if str(body.get("as_of", "")).strip().isdigit() else None
                try:
                    r = desk.dispatch("desk", {"line": line, "whole": bool(body.get("whole")),    # a736: a > line is one command
                                               "reply": str(body.get("reply") or "") or None,
                                               "image_context": body.get("image_context")})
                finally:
                    desk._act_home = desk._act_binds = desk._as_of = None
                    desk.world.intent = desk.world.through_gate = None
                worktree.record(desk, line, sess.actor, allids, n0)
            total = len(desk.world.events)
            created = [i for i in desk.world.nodes if i not in before]      # Wren: the ids a command made, machine-readably
            events = [e["id"] for e in desk.world.events[n0:]]
            if gid:
                for e in desk.world.events[n0:]:
                    e["gesture"] = gid          # a1008: kept on what it made, saved with the world
            store.safe_commit(ctx, desk, line, sess.actor, gid)
        text = r.get("text") or ""
        # Rook: a parse failure came back as error=null. And a refusal in the second step of `look x; do y` hid in the text.
        bad = [l for l in text.splitlines() if l.startswith("ERR")]
        refused = r.get("error") or (bad[0] if bad else None)
        self._json({"text": r.get("text"), "error": refused, "events_total": total, "line": line,
                    "as": (body.get("as") or "alex"), "created": created, "events": events,
                    "code": CODE_VERSION, **({"source_verified": True} if deployment else {})})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8780
    SESSIONS.mkdir(exist_ok=True)
    STATIC.mkdir(exist_ok=True)
    print(f"deskd on http://localhost:{port}  static={STATIC}", flush=True)
    HOLD[0], PORT[0] = os.environ.get("DESKD_HOLD") != "off", port
    __import__("threading").Thread(target=_snapshotter, daemon=True).start()

    def take_over():
        # a new deskd (a landing) asks the one before to save what it holds and let go as soon as it starts, before
        # the door stops it (a door older than 14 Oct stops it without asking); the one before saves at every change
        # until then, and this one takes the lease at its first change
        for f in SESSIONS.glob("*.writer") if HOLD[0] else ():
            if explore.holder_of(f.with_suffix(".pickle")) not in (None, os.getpid()):
                _ask_release(f.stem)
    __import__("threading").Thread(target=take_over, daemon=True).start()
    if os.environ.get("DESKD_PARENT"):
        # a1505: a deskd the door started goes when the door goes (a stopped door on Windows leaves its children running)
        def orphaned(pid=int(os.environ["DESKD_PARENT"])):
            while explore._alive(pid):
                time.sleep(3)
            for name in [n for n, h in LEASES.items() if h]:      # what is held in memory is saved before going
                try:
                    _snapshot(name, looks=True)
                except Exception:      # noqa: BLE001
                    pass
            os._exit(0)
        __import__("threading").Thread(target=orphaned, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
