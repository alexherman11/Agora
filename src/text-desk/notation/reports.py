"""reports: what each viewer's painter last reported (POST /api/observe), kept by the house beside the world, never in it.

a4869 (14 Oct): a report is a viewer's own value, witnessed and not kept (a2870): not an event, not undoable, in no
history, and not the world. Until now it was saved inside the world's file (desk._views), so every report was a
whole-file write (a4838 measured 85 ms on each Enter). Now each viewer's last report is one small file of its own,

    house-state/reports/<session>/<viewer>.json      what the viewer's painter last said (the last one wins)
    house-state/reports/<session>/host.json          which house received them, and when it started

written by deskd alone and read by whoever builds a scene (deskd, or explore.py with DESKD=off).

A report does not outlive the house that received it. The house is the door deskd runs behind (DESKD_PARENT, door.py),
or a deskd run alone: a deskd the door swaps in on a landing is the same house and keeps them. The first time a deskd
of another house touches a session (a report, or a scene built), the reports of the house before are removed and
host.json says when this one started, so `scene` says no viewer has reported since then, never a report from before.
A reader outside deskd (explore.py with DESKD=off) shows none when the house named in host.json no longer runs.
"""
import json
import os
import re
import threading
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent / "house-state" / "reports"
HOST = None            # set by deskd (serve): the house this process receives reports for; None in any other reader
STARTED = None         # when this house started, as ISO seconds
_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_@-]{0,63}$")     # deskd's SESSION_NAME
_claimed, _lock, _read = set(), threading.Lock(), {}


def serve(host, started=None):
    """deskd: reports from now on are received by `host` (the door's pid, or this deskd's own)."""
    global HOST, STARTED
    HOST = str(host)
    STARTED = started or time.strftime("%Y-%m-%dT%H:%M:%S")
    _claimed.clear()


def _dir(session):
    return ROOT / session if session and _NAME.match(str(session)) else None


def _write(p, obj):
    tmp = p.with_name(p.name + f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    for i in range(20):               # Windows: a reader holding the file open refuses the replace for a moment
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            time.sleep(0.01 * (i + 1))
    tmp.unlink(missing_ok=True)


def _host(d):
    try:
        return json.loads((d / "host.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _stopped(d):
    """A reader outside deskd: has the house that kept these stopped? Its reports are then from before whatever house
    comes next, and are not shown (a4869, Sable c4900). The house is a pid (the door's, or a lone deskd's)."""
    if HOST is not None:
        return False                      # deskd claims instead
    host = str(_host(d).get("host") or "")
    if not host.isdigit():
        return False
    import explore
    return not explore._alive(int(host))


def claim(session):
    """In deskd, once per session: reports a house before this one received are removed (they do not outlive it)."""
    d = _dir(session)
    if HOST is None or d is None or session in _claimed:
        return
    with _lock:
        if session in _claimed:
            return
        if _host(d).get("host") != HOST:
            d.mkdir(parents=True, exist_ok=True)
            for p in d.glob("*.json"):
                if p.name != "host.json":
                    p.unlink(missing_ok=True)
            _write(d / "host.json", {"host": HOST, "since": STARTED})
        _claimed.add(session)


def keep(session, viewer, report):
    """The viewer's last report, in place of the one before."""
    d = _dir(session)
    if d is None:
        return
    claim(session)
    d.mkdir(parents=True, exist_ok=True)
    _write(d / f"{quote(viewer, safe='') or '_'}.json", {"viewer": viewer, **report})


def since(session):
    """When the house that keeps this session's reports started (ISO), or None when none has kept any."""
    d = _dir(session)
    if d is None:
        return None
    claim(session)
    return None if _stopped(d) else _host(d).get("since")


def views(session):
    """{viewer: report} as last reported, one per viewer. A file unchanged since it was last read is not read again."""
    d = _dir(session)
    if d is None:
        return {}
    claim(session)
    if _stopped(d):
        return {}
    out = {}
    try:
        files = [p for p in d.glob("*.json") if p.name != "host.json"]
    except OSError:
        return {}
    for p in files:
        try:
            st = p.stat()
            key = (st.st_mtime_ns, st.st_size)
            if _read.get(p, (None,))[0] != key:
                if len(_read) > 500:
                    _read.clear()
                _read[p] =(key, json.loads(p.read_text(encoding="utf-8")))
            r = dict(_read[p][1])
        except (OSError, ValueError):
            continue
        out[str(r.pop("viewer", p.stem))] = r
    return out
