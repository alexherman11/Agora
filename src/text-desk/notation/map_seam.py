"""map_seam.py (a7950): the living map's seam. Pins and routes are world notes; the map frame keeps no copy of its own.

The shared contract is the world note a7875 ("Living map: the shared contract", THE SEAM). In short:
  - one channel, agora-map/1; every message is a JSON object with `channel` and `op`;
  - in, host to frame: {channel, op: 'draw', pins: [{id, rev, lat, lon, height, label, icon, colour}],
    routes: [{id, rev, label, pins: [pin ids in order]}]}; each draw replaces the whole picture;
  - out, frame to host: {channel, op: 'press', id}; {channel, op: 'drop', lat, lon}; {channel, op: 'move', id, rev, lat, lon};
  - coordinates are named fields, never arrays; numbers are finite; lat -90..90, lon -180..180;
  - nothing else crosses: no command strings, no other ops, no other fields.

A pin is a note of kind pin (lat, lon in WGS84 degrees, label, optional height in metres above the drawn ground, icon,
colour). A route is a note of kind route whose lines name its pins by id, one per line, in order: the id is the pin
itself, so renaming a pin breaks nothing. Kind notes describe and never enforce (kinds.py), so every value read here is
parsed and checked; a pin that cannot be placed is left out of the draw and named in `problems`, for the host, never
for the frame.

`draw` reads; `check` turns one frame message into one ordinary line and the fence it was painted at, or refuses with
the reason. The line runs through deskd's own /api/do path (observed item and rev), so the fence, the event and its
undo are the ones every press uses. This file decides nothing else and writes nothing.
"""
import math
import re

CHANNEL = "agora-map/1"
ID = re.compile(r"[a][0-9]{1,9}")                       # a world id of a note's appearance: nothing else is an id here
# a route's line: one id, bare or as a [[wikilink]], and nothing else on the line
ROUTE_LINE = re.compile(r"\s*(?:\[\[\s*([as][0-9]{1,9})\s*\]\]|([as][0-9]{1,9}))\s*")
WORD = re.compile(r"[A-Za-z0-9#][A-Za-z0-9#._-]{0,39}")  # icon and colour: one short word, or omitted
FIELDS = {"press": {"channel", "op", "id"},
          "drop": {"channel", "op", "lat", "lon"},
          "move": {"channel", "op", "id", "rev", "lat", "lon"}}
HEIGHT = (-500.0, 10000.0)                               # metres above the drawn ground (not an elevation)


class Refused(Exception):
    """A message the seam will not act on; the words say why."""


def _num(v, lo, hi, what):
    """A finite number in [lo, hi] from a JSON value: a real number, never a string, a bool or an array."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise Refused(f"{what} must be a number, not {type(v).__name__}")
    v = float(v)
    if not math.isfinite(v):
        raise Refused(f"{what} must be finite")
    if not lo <= v <= hi:
        raise Refused(f"{what} {v} is out of range ({lo} to {hi})")
    return v


def _prop_num(props, key, lo, hi):
    """A number from a note's prop (props are words: '51.5194'); None when absent; Refused when not a place."""
    raw = props.get(key)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        v = float(str(raw).strip())
    except ValueError:
        raise Refused(f"{key}={raw!r} is not a number")
    if not math.isfinite(v) or not lo <= v <= hi:
        raise Refused(f"{key}={raw!r} is out of range ({lo} to {hi})")
    return v


def _kind(world, sid):
    return (world.subjects.get(sid) or {}).get("kind")


def _appearances(world, sid):
    return sorted((nid for nid, n in world.nodes.items() if n.get("type") == "appearance" and n.get("subject") == sid),
                  key=lambda i: int(i[1:]))


def _pin_id(world, ident):
    """The appearance id a pin is drawn by, from an appearance or a subject id; None if it names no pin."""
    if ident in world.nodes:
        n = world.nodes[ident]
        if n.get("type") == "appearance" and _kind(world, n.get("subject")) == "pin":
            return ident
        return None
    if ident in world.subjects and _kind(world, ident) == "pin":
        apps = _appearances(world, ident)
        return apps[0] if apps else None
    return None


def _in_scope(world, nid, scope):
    """scope None: everywhere; else a surface id: the thing is in it or under it."""
    if scope is None:
        return True
    seen, at = set(), world.nodes.get(nid, {}).get("parent")
    while at and at not in seen:
        if at == scope:
            return True
        seen.add(at)
        at = world.nodes.get(at, {}).get("parent")
    return False


def pin_feature(world, nid):
    """-> the draw entry of the pin appearance `nid`, or Refused with why it cannot be placed."""
    n = world.nodes[nid]
    s = world.subjects[n["subject"]]
    p = s.get("props") or {}
    lat, lon = _prop_num(p, "lat", -90.0, 90.0), _prop_num(p, "lon", -180.0, 180.0)
    if lat is None or lon is None:
        raise Refused("a pin needs both lat and lon")
    height = _prop_num(p, "height", *HEIGHT)
    label = str(p.get("label") or s.get("title") or "").strip()
    out = {"id": nid, "rev": n["rev"], "lat": lat, "lon": lon, "height": height if height is not None else 0.0,
           "label": label[:200]}
    for k in ("icon", "colour"):
        v = str(p.get(k) or "").strip()
        if v:
            if not WORD.fullmatch(v):
                raise Refused(f"{k}={v!r} is not one short word")
            out[k] = v
    return out


def draw(world, scope=None):
    """-> {'draw': the agora-map/1 draw message, 'problems': [(id, why)] for the host}. Reads only.

    scope: None for every pin and route in the world, or a surface id: the pins and routes in it, and every pin a
    route there names (wherever that pin is kept)."""
    pins, routes, problems, wanted = {}, [], [], []
    for nid, n in sorted(world.nodes.items(), key=lambda x: int(x[0][1:]) if x[0][1:].isdigit() else 0):
        if n.get("type") != "appearance" or not _in_scope(world, nid, scope):
            continue
        k = _kind(world, n.get("subject"))
        if k == "pin":
            wanted.append(nid)
        elif k == "route":
            s = world.subjects[n["subject"]]
            order, bad = [], None
            for i, line in enumerate((s.get("text") or "").splitlines(), 1):
                if not line.strip():
                    continue
                m = ROUTE_LINE.fullmatch(line)
                pid = _pin_id(world, (m.group(1) or m.group(2))) if m else None
                if pid is None:
                    bad = f"line {i} ({line.strip()[:40]!r}) does not name one pin"
                    break
                order.append(pid)
            if bad or len(order) < 2:
                problems.append((nid, bad or "a route needs at least two pins"))
                continue
            routes.append({"id": nid, "rev": n["rev"], "label": str((s.get("props") or {}).get("label") or s.get("title") or "")[:200],
                           "pins": order})
            wanted += order
    for nid in wanted:
        if nid in pins or nid in dict(problems):
            continue
        try:
            pins[nid] = pin_feature(world, nid)
        except Refused as e:
            problems.append((nid, str(e)))
    # a route that names a pin which cannot be placed is not drawn either (no stop is silently skipped)
    bad = {p for p, _ in problems}
    kept = []
    for r in routes:
        missing = [p for p in r["pins"] if p in bad]
        if missing:
            problems.append((r["id"], f"its pin {missing[0]} cannot be placed"))
        else:
            kept.append(r)
    return {"draw": {"channel": CHANNEL, "op": "draw", "pins": list(pins.values()), "routes": kept},
            "problems": problems}


def check(world, msg, scope=None):
    """One message from the frame -> {'op', 'line', 'observed' or None, 'id'?}. Refused with the reason otherwise.

    Pike decided (c7997): a press views the pin (`do view <pin>`); a drop is one ordinary create of a pin in the scope
    surface, labelled 'New pin', at lat and lon rounded to 6 decimals (no new verb; one undo); a move is
    `do prop <pin> lat=<lat> lon=<lon>`, fenced at the revision the frame saw."""
    if not isinstance(msg, dict):
        raise Refused("a message is a JSON object")
    if msg.get("channel") != CHANNEL:
        raise Refused(f"wrong channel {str(msg.get('channel'))[:40]!r}: only {CHANNEL}")
    op = msg.get("op")
    if not isinstance(op, str) or op not in FIELDS:
        raise Refused(f"unknown op {str(op)[:40]!r}: only press, drop and move come from the frame")
    extra = set(msg) - FIELDS[op]
    if extra:
        raise Refused(f"{op} carries only {', '.join(sorted(FIELDS[op]))}; not {', '.join(sorted(map(str, extra)))[:80]}")
    missing = FIELDS[op] - set(msg)
    if missing:
        raise Refused(f"{op} needs {', '.join(sorted(missing))}")
    if op == "drop":
        lat, lon = _num(msg["lat"], -90, 90, "lat"), _num(msg["lon"], -180, 180, "lon")
        if scope is None or world.nodes.get(scope, {}).get("type") != "surface":
            raise Refused("a drop needs the map's scope surface to make the pin in")
        # fenced on the scope surface as it is now: the map shows it, and the desk acts only on what was seen (ran in
        # the browser: without it the create was refused 'you have not looked at f...')
        return {"op": op, "line": f'do create {scope} kind=pin title="New pin" label="New pin" lat={_fmt(lat, 6)} lon={_fmt(lon, 6)}',
                "observed": {"item": scope, "rev": world.nodes[scope]["rev"]}}
    pid = msg["id"]
    if not isinstance(pid, str) or not ID.fullmatch(pid):
        raise Refused("id must be a world id (a123), nothing else")
    if _pin_id(world, pid) != pid or not _in_scope(world, pid, scope):
        raise Refused(f"{pid} is not a pin on this map")
    if op == "press":
        return {"op": op, "id": pid, "line": f"do view {pid}", "observed": None}
    rev = msg["rev"]
    if isinstance(rev, bool) or not isinstance(rev, int):
        raise Refused("rev must be a whole number: the revision the frame was drawn at")
    lat, lon = _num(msg["lat"], -90, 90, "lat"), _num(msg["lon"], -180, 180, "lon")
    now = world.nodes[pid]["rev"]
    if rev != now:
        raise Refused(f"stale: {pid} was moved from revision {rev}, and it is now {now}; nothing was changed. The map is drawn again.")
    return {"op": op, "id": pid, "line": f"do prop {pid} lat={_fmt(lat)} lon={_fmt(lon)}",
            "observed": {"item": pid, "rev": rev}}


def _fmt(v, places=7):
    """A coordinate as words a line can carry: plain decimal, at most 7 places (about a centimetre), never 1e-05."""
    s = f"{v:.{places}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
