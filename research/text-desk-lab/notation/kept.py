"""kept: the copies undo keeps, out of the world file (7 Oct 2026, Claude with Alex: 'I want to see the speed gain').

    python kept.py begin <world>      move every kept copy out of the world's file into <world>.undo.sqlite beside it
                                      (the file as it was is kept as <world>.pickle.before-kept)
    python kept.py check <world>      every event that says its copy is kept finds it
    python kept.py restore <world>    put the copies back in the file (the way back; the archive is left)

Measured on 7 Oct: frontier's world is 3.2 MB and its file 124 MB. 122 MB of that is one key, `restore_subject`: every
edit keeps a whole copy of the thing as it was, so one line added to Shop talk kept the whole chat again (0.7 MB). Each
request loads the file once and serialises it twice, so every line cost 0.7 s whatever it did.

The copies are still wanted: the verbs' own undo restores from them (events older than the log, and worlds without
one), and three readers ask what an edit changed (world.written, desk._edit_said, rooms' members-then). So they are
kept, beside the file. In a world that has an archive, an event's `undo` holds, in place of the copy,

    {"kept": "<the archive's world>", "kept_id": "<the subject's id>", ...its other keys as they were}

and `kept.copy_of(e)` reads the copy when someone asks: one reader for all of them. `kept.sweep(world, path)` moves
the copies of new events out, just before a world is saved (explore.save_desk, deskd's Session); between a command
and its save the copy is still on the event. A world is treated so only once `begin` made its archive (a fork gets an
empty one of its own and still reads its base's by name); a world without the file is untouched, so the tests'
throwaway worlds and the frozen ones are as they were.

Not a deletion: `restore` puts every copy back. What this is not: the flip. The world is still loaded from a pickle,
whole, on every request; it is now a small one.
"""
import pickle
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SESSIONS = HERE / "sessions"
BIG = "restore_subject"
_RECENT = {}          # (archive file, event id) -> copy: the few a reader asks for again and again in one process


def archive_path(pickle_path):
    p = Path(pickle_path)
    name = p.name[:-len(".pickle")] if p.name.endswith(".pickle") else p.name
    return p.with_name(name + ".undo.sqlite")


def _name(pickle_path):
    p = Path(pickle_path)
    return p.name[:-len(".pickle")] if p.name.endswith(".pickle") else p.name


def _open(file):
    con = sqlite3.connect(str(file), timeout=60)
    con.execute("CREATE TABLE IF NOT EXISTS kept (eid TEXT PRIMARY KEY, body BLOB)")
    return con


def on(pickle_path):
    return archive_path(pickle_path).exists()


def sweep(world, pickle_path):
    """Move the copies new events hold into the archive. -> how many moved. Nothing, for a world with no archive.
    The archive is written before the world is saved: a save that never happens leaves a row no event points at."""
    file = archive_path(pickle_path)
    if not file.exists():
        return 0
    todo = [e for e in world.events if isinstance(e.get("undo"), dict) and BIG in e["undo"]]
    if not todo:
        return 0
    name = _name(pickle_path)
    con = _open(file)
    try:
        with con:
            con.executemany("INSERT OR REPLACE INTO kept (eid, body) VALUES (?, ?)",
                            [(e["id"], pickle.dumps(e["undo"][BIG])) for e in todo])
    finally:
        con.close()
    for e in todo:
        copy = e["undo"].pop(BIG)
        e["undo"]["kept"], e["undo"]["kept_id"] = name, (copy or {}).get("id")
        _RECENT.pop((str(file), e["id"]), None)
    return len(todo)


def is_kept(e):
    u = e.get("undo")
    return isinstance(u, dict) and (BIG in u or bool(u.get("kept")))


def subject_id(e):
    """The subject an event kept a copy of, without reading the copy."""
    u = e.get("undo") if isinstance(e.get("undo"), dict) else {}
    if BIG in u:
        return (u[BIG] or {}).get("id")
    return u.get("kept_id") if u.get("kept") else None


def copy_of(e, sessions=None):
    """The whole subject as it was before event `e`, or None when the event kept none (or its archive is not here:
    a copy of a world taken without it)."""
    u = e.get("undo") if isinstance(e.get("undo"), dict) else {}
    if BIG in u:
        return u[BIG]
    name = u.get("kept")
    if not name:
        return None
    file = Path(sessions or SESSIONS) / f"{name}.undo.sqlite"
    key = (str(file), e["id"])
    if key in _RECENT:
        return _RECENT[key]
    if not file.exists():
        return None
    con = sqlite3.connect(str(file), timeout=60)
    try:
        row = con.execute("SELECT body FROM kept WHERE eid = ?", (e["id"],)).fetchone()
    except sqlite3.Error:
        row = None
    finally:
        con.close()
    copy = pickle.loads(row[0]) if row else None
    if len(_RECENT) > 400:
        _RECENT.clear()
    _RECENT[key] = copy
    return copy


def fork(base_pickle, fork_pickle):
    """A fork of a world that has an archive gets an empty one of its own: its events made before the fork still name
    the base's, and what it makes from here is kept in its own."""
    if on(base_pickle) and not on(fork_pickle):
        _open(archive_path(fork_pickle)).close()


def _locked(world_name):
    import explore
    lock = SESSIONS / f"{world_name}.lock"
    explore.take_lock(lock)
    return lock


def main(argv):
    if len(argv) < 2 or argv[0] not in ("begin", "check", "restore"):
        print(__doc__.split("\n\n")[1])
        return 2
    import explore
    cmd, name = argv[0], argv[1]
    path = SESSIONS / f"{name}.pickle"
    lock = _locked(name)
    try:
        raw = path.read_bytes()
        desk = pickle.loads(raw)
        events = desk.world.events
        if cmd == "begin":
            if on(path):
                print(f"{archive_path(path).name} is already there; new copies are moved at every save")
                return 1
            was = path.with_name(path.name + ".before-kept")
            was.write_bytes(raw)
            _open(archive_path(path)).close()
            n = sweep(desk.world, path)
            explore.save_desk(path, desk)
            now = path.stat().st_size
            print(f"{name}: {n} copies moved to {archive_path(path).name} ({archive_path(path).stat().st_size / 1e6:.1f} MB); "
                  f"the world's file went from {len(raw) / 1e6:.1f} MB to {now / 1e6:.1f} MB; as it was: {was.name}")
            return 0
        if cmd == "check":
            kept_ = [e for e in events if (e.get("undo") or {}).get("kept")]
            inline = sum(1 for e in events if BIG in (e.get("undo") or {}))
            lost = [e["id"] for e in kept_ if copy_of(e) is None]
            wrong = [e["id"] for e in kept_ if copy_of(e) is not None and (copy_of(e) or {}).get("id") != e["undo"].get("kept_id")]
            print(f"{name}: {len(events)} events; {len(kept_)} say their copy is kept, {inline} still hold one; "
                  f"{len(lost)} not found, {len(wrong)} of another subject" + (f": {(lost + wrong)[:8]}" if lost or wrong else ""))
            return 1 if lost or wrong else 0
        if cmd == "restore":
            n = 0
            for e in events:
                u = e.get("undo") or {}
                if u.get("kept"):
                    copy = copy_of(e)
                    if copy is None:
                        print(f"{e['id']}: its copy is not in the archive; left as it is")
                        continue
                    u.pop("kept"), u.pop("kept_id", None)
                    u[BIG] = copy
                    n += 1
            archive_path(path).rename(archive_path(path).with_name(archive_path(path).name + ".restored"))
            explore.save_desk(path, desk)
            print(f"{name}: {n} copies put back; the file is {path.stat().st_size / 1e6:.1f} MB; the archive is set aside as .restored")
            return 0
    finally:
        explore.release_lock(lock)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
