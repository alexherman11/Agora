"""witnessed: rows a program outside the desk keeps beside the house, for lenses to read, never in the world.

a5052 (14 Oct, the window manager prototype): the windows a host has on Alex's screen are the rows a layout lens repeats
over, and they are the host's to say, as a painter's report is the painter's (reports.py, a4869): witnessed, with age,
not an event, not undoable, in no history, and not the world. One small file per source,

    house-state/<world>/witnessed/<name>.json     {"by": <who writes it>, "pid": <its process>, "at": <unix time>,
                                                   "rows": [{field: value, ...}, ...]}

written whole by its one writer (write(), atomically) and read by whoever builds a scene (read()). A source whose writer
no longer runs has no rows: what a stopped program last said is not what is on the screen now.

The scene names each source it reads (scene.SOURCES, e.g. `windows`), with its fields, so a lens is checked against
them as against any row source; this module only keeps and reads the files. stamp() is what deskd folds into a scene's
cache key, so a changed file is a new scene.
"""
import json
import os
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "house-state"
_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]{0,63}$")


def _dir(world):
    world = str(world or "").split("@")[0]
    return ROOT / world / "witnessed" if _NAME.match(world) else None


def path(world, name):
    d = _dir(world)
    return d / f"{name}.json" if d is not None and _NAME.match(str(name)) else None


def write(world, name, rows, by):
    """Keep `rows` as what `by` (this process) witnesses now, in place of what it said before."""
    p = path(world, name)
    if p is None:
        raise ValueError(f"not a world and source name: {world!r} {name!r}")
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"by": by, "pid": os.getpid(), "at": time.time(), "rows": rows}, ensure_ascii=False),
                   encoding="utf-8")
    for i in range(20):               # Windows: a reader holding the file open refuses the replace for a moment
        try:
            os.replace(tmp, p)
            return p
        except PermissionError:
            time.sleep(0.01 * (i + 1))
    tmp.unlink(missing_ok=True)
    raise PermissionError(f"{p} stayed open; not replaced")


def clear(world, name):
    p = path(world, name)
    if p is not None:
        p.unlink(missing_ok=True)


def read(world, name):
    """-> {"by", "pid", "at", "age" (seconds, rounded), "rows"} as last written, or None when there is no such file,
    it cannot be read, or its writer has stopped."""
    p = path(world, name)
    try:
        doc = json.loads(p.read_text(encoding="utf-8")) if p is not None else None
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict) or not isinstance(doc.get("rows"), list):
        return None
    pid = doc.get("pid")
    if pid is not None and int(pid) != os.getpid():
        import explore
        if not explore._alive(int(pid)):
            return None
    doc["age"] = max(0, round(time.time() - float(doc.get("at") or 0)))
    return doc


def stamp(world):
    """What changes when any witnessed source of `world` is rewritten or removed: for a scene's cache key."""
    d = _dir(world)
    try:
        return tuple(sorted((p.name, p.stat().st_mtime_ns) for p in d.glob("*.json"))) if d is not None else ()
    except OSError:
        return ()
