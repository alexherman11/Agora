"""Open-ended exploration: an empty tiled desk, the lean REPL, and a session that persists between runs.

    python explore.py <session> < commands      run commands against the saved session (created empty if new)
    python explore.py <session> --reset         start the session over
    python explore.py <session> --dump          print the world snapshot as JSON

Never touches the task worlds; this is for building a desk from nothing and finding friction.
"""

import json
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import pickle
import os
import sys
from pathlib import Path

from desk_knife import DeskKnife
from world import World

HERE = Path(__file__).resolve().parent
SESSIONS = HERE / "sessions"


def _alive(pid):
    """Is a process with this id still running? A lock whose holder died is stale at once, not after a minute."""
    try:
        if sys.platform == "win32":
            import ctypes
            k = ctypes.windll.kernel32
            h = k.OpenProcess(0x1000, False, int(pid))   # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            # an exited process can still be opened while its parent holds a handle (the keeper does, until it polls):
            # only STILL_ACTIVE (259) is running
            code = ctypes.c_ulong()
            ok = k.GetExitCodeProcess(h, ctypes.byref(code))
            k.CloseHandle(h)
            return not ok or code.value == 259
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def take_lock(lock, tries=600, pause=0.1):
    """Take a session's lock file, writing our pid into it. Sable's baseline (1): a killed holder left its lock behind
    and the next run waited a minute; now a lock whose pid is gone is removed at once."""
    import time
    for _ in range(tries):
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except (FileExistsError, PermissionError):     # held; on Windows a lock being deleted refuses with PermissionError
            try:
                age = time.time() - lock.stat().st_mtime
            except OSError:
                time.sleep(0.005)                       # released just now: try again at once
                continue
            # 29 Sep, three residents live: every waiter opened the lock to read its pid, and Windows will not delete a
            # file another process has open, so the holder's release failed and everyone waited out the minute. A lock
            # under a second old is simply busy; only an older one is opened to see whether its holder died.
            if age > 1:
                try:
                    pid = lock.read_text().strip()
                except OSError:
                    pid = ""
                if (pid and not _alive(pid)) or age > 60:
                    release_lock(lock, anyone=True)     # a dead or crashed holder
            time.sleep(pause)
            continue
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return
    raise SystemExit(f"could not take {lock.name} after {tries * pause:.0f}s; another run holds it")


def release_lock(lock, anyone=False):
    """Remove the lock, ours unless `anyone`. Windows refuses to delete a file another process has open for a moment
    (a waiter reading it): try again briefly rather than leave a lock behind that makes everyone wait a minute."""
    import time
    if not anyone:
        try:
            if lock.read_text().strip() != str(os.getpid()):
                return                                  # not ours any more (it was taken as stale): leave it
        except OSError:
            return
    for _ in range(200):
        try:
            lock.unlink(missing_ok=True)
            return
        except PermissionError:
            time.sleep(0.01)


def save_desk(path, desk, data=None):
    """Write the session atomically: to a temp file, then rename over the old one. Sable's baseline (1): a write killed
    halfway left a pickle that would not load, and the whole session was lost. `data`: the pickled desk, if in hand."""
    writer = holder_of(path)
    if writer is not None and writer != os.getpid():
        # 14 Oct (Snappy Desk; Alex: one writer): a world server keeps this world in memory and saves it itself; a
        # second writer would put an older world over its newer one. Send the line through the door instead.
        raise RuntimeError(f"{path.stem} is held by its world server (pid {writer}), which saves it itself; "
                           f"send the line through the door (DESKD), not to the file")
    tmp = path.with_name(path.name + ".tmp")
    if data is None:
        import kept
        import store
        kept.sweep(desk.world, path)      # 7 Oct: the copies undo keeps go beside the file, when the world has an archive
        store.mark_snapshot(desk, path)   # which record of the log this file holds (store.catch_up reads it)
    tmp.write_bytes(data if data is not None else pickle.dumps(desk))
    # 1 Oct (worker-a1568 c1920, Pike e4506): on Windows the rename is refused while any other process has the world
    # open, even only to read it (a copy taken without the lock, a virus scan of a 58 MB file), and the write was lost.
    # Try again for up to ten seconds before giving up; the lock keeps every other writer out meanwhile
    import time
    for wait in [0.05] * 20 + [0.25] * 36:
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(wait)
    os.replace(tmp, path)


def holder_of(path):
    """The pid of the live world server holding this world's writer lease (<world>.writer beside it), or None."""
    p = Path(path).with_suffix(".writer")
    try:
        pid = int(json.loads(p.read_text(encoding="utf-8")).get("pid"))
    except (OSError, ValueError, TypeError, AttributeError):
        return None
    return pid if _alive(str(pid)) else None


def load_desk(path):
    """A world read from its file, with any log records written after the file was saved put on (store.catch_up)."""
    desk = pickle.loads(Path(path).read_bytes())
    import store
    try:
        store.catch_up(desk, path)
    except Exception:      # noqa: BLE001
        store._fault(store.log_path(path), "catch_up")
    return desk


def fresh():
    w = World()
    w.nodes[w.root]["layout"] = "row"   # a tiled top level, the round-8 lesson
    w.equal_share = False
    d = DeskKnife(w, "lean")
    d.batch = True
    d.lean = True
    d.read_cap = 4
    d.ids = {}
    return d


REPLY = __import__("uuid").uuid4().hex   # a806: the lines of one call are one reply; $new reaches no further back


def via_deskd(name, me, lines, whole=False, stored="", as_of=None):
    """When deskd is up it is the one owner of every world: send each line as one turn and hold nothing between
    turns. A refused line refuses only itself (a6437, carry_on): the lines after it run, as they do without deskd, and
    the receipt ends saying what ran, was refused or was skipped. Returns False when no server answers, and the caller
    falls back to the file lock."""
    import os, urllib.request, urllib.error
    import carry_on
    if os.environ.get("DESKD", "") == "off":
        return False
    url = os.environ.get("DESKD", "http://127.0.0.1:8780") + "/api/do"
    reply = REPLY
    tally = carry_on.Tally()
    for k, line in enumerate(lines):
        body = json.dumps({"session": name, "as": me, "line": line, "cli": True, "whole": whole,
                           "reply": reply, **({"stored": stored} if stored else {}),
                           **({"as_of": as_of} if as_of is not None else {})}).encode("utf-8")
        try:
            with urllib.request.urlopen(urllib.request.Request(url, body, {"Content-Type": "application/json"}), timeout=60) as f:
                r = json.loads(f.read().decode("utf-8"))
        except (urllib.error.URLError, OSError):
            if k == 0:
                return False
            print("ERR deskd stopped answering; the lines above were applied, this one and the rest were not")
            return True
        print(f"> {line}")
        said = r.get("text") or ("ERR " + str(r.get("error")))
        print(said)
        print()
        tally.add(line, said, r.get("error"))
    if tally.summary():
        print(tally.summary())
        print()
    return True


def away_in(name, who, state=None):
    """a2844: the version `who` is away in ('<commission>@<commit>'), by the door's record for world `name`, or None."""
    try:
        visits = json.loads((Path(state or HERE / "house-state") / "visits.json").read_text(encoding="utf-8"))
        there = (visits.get("away") or {}).get(who) if visits.get("world") == name else None
        return str(there.get("label")) if there else None
    except (OSError, ValueError, AttributeError):
        return None


def main():
    name = sys.argv[1]
    SESSIONS.mkdir(exist_ok=True)
    # --window <name>: Juniper's step 11. Two windows of one person are two readers; each keeps its own "what I saw",
    # so the second refuses a stale edit instead of overwriting the first. Events still say the same actor.
    window = sys.argv[sys.argv.index("--window") + 1] if "--window" in sys.argv[:-1] else ""
    # --whole (a736): each stdin line is one command; a ; in it is words. The house sends a resident's > lines so.
    whole = "--whole" in sys.argv
    # --stored <node> (a1156): the house runs a corner's wake as the stored text it is: it stands in that corner, and
    # its words mean what they were bound to when it was set
    stored = sys.argv[sys.argv.index("--stored") + 1] if "--stored" in sys.argv[:-1] else ""
    # --as-of <n> (a5068): the house says where a resident's turn began (its news had reached event n), so a chat line
    # or thread reply is judged on what that turn was shown
    as_of = int(sys.argv[sys.argv.index("--as-of") + 1]) if "--as-of" in sys.argv[:-1] else None
    if not [a for a in sys.argv[2:] if a.startswith("--") and a not in ("--as", "--window", "--whole", "--stored", "--as-of")]:
        lines = [l.rstrip("\n") for l in sys.stdin]
        lines = [l for l in lines if l.strip() and not l.startswith("#")]
        who = sys.argv[sys.argv.index("--as") + 1].lower() if "--as" in sys.argv[:-1] else "jeff"
        if not window and not any(l.startswith("!") for l in lines) and via_deskd(name, who, lines, whole, stored, as_of):
            return
        # a2844: someone away in a version of the code (the door's record) whose line arrives here was not answered by
        # the door. Run from these files it would change home's world from a visit, silently: it is refused instead
        there = away_in(name, who)
        if there:
            print(f"ERR you are away in {there} and the door did not answer, so nothing was run: {len(lines)} line(s) "
                  "would have changed home's world from a visit. When the door answers again it brings you home and says so.")
            return
        import io
        sys.stdin = io.StringIO("\n".join(lines) + "\n")
    path = SESSIONS / f"{name}.pickle"
    # several people may work one session at once: each invocation holds the session's lock from load to save
    import atexit
    lock = SESSIONS / f"{name}.lock"
    take_lock(lock)
    atexit.register(lambda: release_lock(lock))
    if "--reset" in sys.argv or not path.exists():
        desk = fresh()
    else:
        desk = load_desk(path)
    # --as <name>: a visitor works under their own name for this visit (events say by <name>); the owner is jeff
    me = desk.world.me = sys.argv[sys.argv.index("--as") + 1].lower() if "--as" in sys.argv[:-1] else "jeff"
    # what has been seen, what is open and the since-your-last-look mark belong to each person, not to the session
    desk._session = name
    slot = me + ("/" + window if window else "")       # the reader's slot: one person, one window
    per = getattr(desk, "_per", None) or {}
    if slot in per:
        desk.seen, desk.open, desk.last_event_seen = per[slot]
    elif me != "jeff":
        desk.seen, desk.open, desk.last_event_seen = {}, {desk.world.root}, len(desk.world.events)
    per[slot] = (desk.seen, desk.open, desk.last_event_seen)
    desk._per = per
    desk._window = window
    desk._as_of = as_of          # a5068: for this call only; cleared before the desk is saved
    if "--dump" in sys.argv:
        print(json.dumps(desk.snapshot(), indent=1))
        return
    if "--shape" in sys.argv:
        # the desk without ids: what a faithful replay must reproduce
        w = desk.world

        def walk(fid, depth):
            for k in w.children(fid):
                if k["type"] == "surface":
                    print("  " * depth + f"surface {k['title']!r} {k['layout']}" + (f" query={k['query']!r}" if k.get("query") else ""))
                    walk(k["id"], depth + 1)
                else:
                    s = w.subjects[k["subject"]]
                    bits = [s["kind"], repr(s["title"]), f"tags={s['tags']}", f"due={s.get('due')}", f"text={__import__('hashlib').md5(s['text'].encode()).hexdigest()[:6]}",
                            f"comments={[(c['by'], c['text'], c['resolved']) for c in s['comments']]}", "folded" if k["folded"] else "",
                            f"props={sorted((s.get('props') or {}).items())}" if s.get("props") else ""]
                    print("  " * depth + " ".join(b for b in bits if b))
        walk(w.root, 0)
        for l in w.links:
            print(f"link {w.subjects[l['from']]['title']!r} -> {w.subjects[l['to']]['title']!r} {l['kind']}")
        return          # a1027: rules are notes (tags=['rule'] above); scripts are retired into verbs
    if "--reset" in sys.argv and sys.stdin.isatty():
        save_desk(path, desk)
        print("reset")
        return
    # 7 Oct: a world that has a log (store.py) gets one record per line, as it does through deskd: the world as facts
    # before the line (logged), and the difference written when the next line begins or the lines end
    import store
    import carry_on
    logged = said = None
    tally = carry_on.Tally()

    def record():
        if logged is not None:
            store.safe_commit(logged, desk, said, said[1:].split()[0].lower() if said.startswith("!") and said[1:].split() else me,
                              None, window)

    for raw in sys.stdin:
        line = raw.rstrip("\n")   # the desk's own grammar handles \n inside values; do not pre-convert
        if not line.strip() or line.startswith("#"):
            continue
        record()
        logged, said = store.safe_begin(desk, path), line
        print(f"> {line}")
        if line.startswith("!"):
            # !priya append a10 line="..."   another actor writes to the world directly (a test injection)
            import shlex
            actor, verb, target, *rest = shlex.split(line[1:])
            kv = dict(a.partition("=")[::2] for a in rest)
            try:
                import moo
                # Sable's baseline (4): create and tag were signed as the session owner and kept _by as a prop. The
                # injected actor is the world's actor for the one act.
                owner, desk.world.me = desk.world.me, actor
                try:
                    if verb in moo.REGISTRY:   # registry verbs (prop, tag, due ...) sign with the world's actor
                        r = moo.REGISTRY[verb].run(desk.world, target, dict(kv))
                    else:
                        r = desk.world.apply(verb, target, None, kv, actor)
                finally:
                    desk.world.me = owner
                desk._after_mutation()
                print(f"({actor} did {verb} {target}: {r.get('note') or r.get('event')})")
                desk._run_rules(cause=None)   # rules watch other actors' events too
                if desk._rule_notes:
                    print("\n".join(desk._rule_notes))
                    desk._rule_notes = None
            except Exception as e:
                print("ERR", e)
            print()
            continue
        import worktree
        if line.strip().lower().split(" ")[0] == "worktree":
            text, desk = worktree.handle(line, name, desk, me)
            desk._per = per
            print(text)
            print()
            continue
        before, n0 = worktree.ids_of(desk), len(desk.world.events)
        if stored in desk.world.nodes:
            import verbs
            desk._act_home, desk._act_binds = verbs.stored_at(desk.world, stored)
        try:
            r = desk.dispatch("desk", {"line": line, "whole": whole, "reply": REPLY})
        finally:
            desk._act_home = desk._act_binds = None
        worktree.record(desk, line, me, before, n0)
        text = r.get("text") or ("ERR " + r["error"])
        print(text)
        print()
        # a6437 (Alex): a refused line refuses only itself; the lines after it run. Sable and Juniper's lesson (a refused
        # create, then a line on the previous $new) is kept by the desk, which skips a line that depends on it (carry_on)
        tally.add(line, text, r.get("error"))
    record()
    if tally.summary():
        print(tally.summary())
        print()
    per[slot] = (desk.seen, desk.open, desk.last_event_seen)
    desk._as_of = None
    save_desk(path, desk)


if __name__ == "__main__":
    main()
