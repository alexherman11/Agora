"""The map module: words that read a map's ground and the placed things of the world.

A map is a world thing (`kind=map`) naming a ground file (`ground=<file thing>`, format agora-ground/1, see ground.py)
and the lens that shows it. A thing is placed when it says `lat`/`lon`, or `at`/`place` naming a placed thing, or
(approximately) a `location` the ground can find by name. Layers (`kind=map-layer`) are a reading plus a look.
Routes (`kind=route`) keep their street path as facts. This process keeps no state of its own except a parsed copy of
each ground file it has read, keyed by the file's digest.

Words (all readings run as the caller, so nobody sees a placed thing they could not already see):
  map.find <text> [map=]            names in the ground and placed things, best first
  map.where <thing|lat,lon> [map=]  a sentence: the street and nearest named place
  map.near <thing|lat,lon> [within=300] [kind=] [map=]   placed things nearby, nearest first
  map.path stops="a > b > c" [mode=walk|bike] [map=]     a street path, as a reading (the planner's preview)
  map.route [<route>] name= stops= [mode=] [map=]        make a route thing, or replan one
  map.layers [<map>]                every layer with its placed rows: what a map window watches
  map.hide <layer> / map.unhide <layer>   hide a layer from your own view (others still see it)
  map.show <thing>                  turn your map window to a thing

Not contained here (see SHAPE section 11): the process can read the machine's files. It reads exactly one kind of
file: the world's own blob store, by the digest a file thing names, and it checks that digest before using a byte.
"""
import datetime
import hashlib
import json
import re
import sys
import threading
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ground import Ground, parse_points, polyline  # noqa: E402

out_lock = threading.Lock()
pending = {}
hello = {}
grounds = {}            # blob digest -> Ground
KEEP = ("kind", "title", "name", "label", "start", "end", "location", "place", "at", "path", "metres", "minutes",
        "stops", "mode", "streets", "color", "icon", "by", "who", "done", "seats", "osm", "tags", "ring", "approx")
SHOWS_START = ("rows ", "board.", "map.near ", "map.find ")


def send(msg):
    with out_lock:
        print(json.dumps(msg, ensure_ascii=True), flush=True)


def q(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


class Call:
    """One call: reads go out as the caller, under this call's `use`, and come back in order."""

    def __init__(self, msg):
        self.use = msg["use"]
        self.person = (msg.get("caller") or {}).get("person", "")
        self.saw = {}
        self.looked = {}

    def see(self, line):
        slot = [threading.Event(), None]
        key = self.use + ":" + uuid.uuid4().hex[:6]
        pending[key] = slot
        pending.setdefault(self.use + ":queue", []).append(key)
        send(dict(t="see", use=self.use, line=line))
        try:
            if not slot[0].wait(9):
                raise ValueError("the kernel did not answer " + line.split()[0])
            if slot[1].get("refused"):
                raise ValueError(slot[1]["refused"])
            return slot[1].get("rows", []), slot[1].get("text", "")
        finally:
            pending.pop(key, None)

    def look(self, ref):
        """One thing by id or name (names work where ids go), or None. Remembered for this call."""
        if ref in self.looked:
            return self.looked[ref]
        try:
            rows, _ = self.see("look " + q(ref) if not re.fullmatch(r"[A-Za-z]+\d+", ref) else "look " + ref)
        except ValueError:
            rows = []
        row = rows[0] if rows else None
        self.looked[ref] = row
        if row and row.get("id"):
            self.looked[row["id"]] = row
        return row


# reads from the kernel come back on stdout's reader thread, matched to the oldest open read of that use
def deliver(msg):
    queue = pending.get(msg.get("use", "") + ":queue") or []
    while queue:
        key = queue.pop(0)
        if key in pending:
            pending[key][1] = msg
            pending[key][0].set()
            return


# --- the map and its ground -------------------------------------------------------------------------------------
def the_map(call, name=None):
    if name:
        m = call.look(name)
        if not m or m.get("kind") != "map":
            raise ValueError(f"{name} is not a map (make kind=map name=… ground=<file>)")
        return m
    maps, _ = call.see("rows map")
    if not maps:
        raise ValueError("there is no map here yet: make kind=map name=… ground=<ground file>")
    return maps[0]


def ground_of(call, m):
    ref = m.get("ground")
    if not ref:
        raise ValueError(f"{m.get('name') or m['id']} has no ground= file")
    f = call.look(ref)
    if not f or not f.get("blob_hash"):
        raise ValueError(f"the ground {ref} is not a file you can read")
    digest = f["blob_hash"]
    if digest not in grounds:
        if not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError("the ground file's digest is not valid")
        path = Path(hello["home"]).parent.parent / "blobs" / digest
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("the ground file failed its integrity check")
        grounds[digest] = Ground(json.loads(data.decode("utf-8-sig")))
    return grounds[digest]


def num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def position(call, g, row, depth=0):
    """(lat, lon, approx) for a row, or None: its own lat/lon; else the thing its at=/place= names; else its
    location text found in the ground (approximate)."""
    lat, lon = num(row.get("lat")), num(row.get("lon"))
    if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon, False
    for key in ("at", "place"):
        ref = row.get(key)
        if ref and depth < 2:
            other = call.look(str(ref))
            if other and other.get("id") != row.get("id"):
                if other.get("rev") is not None:
                    call.saw[other["id"]] = other["rev"]
                p = position(call, g, other, depth + 1)
                if p:
                    return p
            if g and not re.fullmatch(r"[a-z]{2,4}\d+", str(ref)):
                # at="Seabright & Murray": a name on the ground, said where an id could go (a corner or a named
                # place is a point, so it is not marked approximate; a text location below is)
                hits = g.find(str(ref), 1)
                if hits:
                    return hits[0]["lat"], hits[0]["lon"], False
    if row.get("location") and g:
        hits = g.find(str(row["location"]), 1)
        if hits:
            return hits[0]["lat"], hits[0]["lon"], True
    return None


def point_of(call, g, text):
    """A stop or a centre: 'lat,lon', a thing (id or name), or a name in the ground."""
    text = str(text).strip()
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1)), float(m.group(2)), text
    thing = call.look(text)
    if thing:
        p = position(call, g, thing)
        if p:
            return p[0], p[1], thing.get("name") or thing.get("title") or thing["id"]
    hits = g.find(text, 1)
    if hits:
        return hits[0]["lat"], hits[0]["lon"], hits[0]["name"]
    raise ValueError(f"{text}: not a place this map knows (try map.find {text})")


def placed(call, g, rows, layer=None):
    out = []
    for r in rows:
        if not isinstance(r, dict) or not r.get("id"):
            continue
        item = {k: r[k] for k in KEEP if r.get(k) not in (None, "")}
        item["id"], item["rev"] = r["id"], r.get("rev", 0)
        if r.get("text") and "title" not in item and "name" not in item:
            item["text"] = str(r["text"])[:140]
        if r.get("kind") == "route" and r.get("path"):
            pts = parse_points(r["path"])
            if pts:
                item["lat"], item["lon"] = pts[0]
            out.append(item)
            continue
        p = position(call, g, r)
        if not p:
            continue
        item["lat"], item["lon"] = round(p[0], 7), round(p[1], 7)
        if p[2]:
            item["approx"] = "yes"
        out.append(item)
    return out


# --- the words --------------------------------------------------------------------------------------------------
def w_find(call, a):
    text = a["words"].strip() or a["kv"].get("text", "")
    if not text:
        raise ValueError("map.find <words>: a street, a corner (Seabright & Murray) or a place's name")
    g = ground_of(call, the_map(call, a["kv"].get("map")))
    rows = []
    words = [w for w in re.findall(r"[a-z0-9']+", text.lower())]
    for kind in ("spot",):
        things, _ = call.see("rows " + kind)
        for t in placed(call, g, things):
            hay = (str(t.get("name") or t.get("title") or "")).lower()
            if words and all(w in hay for w in words):
                rows.append(dict(name=t.get("name") or t.get("title"), what=t.get("kind"), id=t["id"],
                                 lat=t["lat"], lon=t["lon"]))
    rows += g.find(text, int(a["kv"].get("limit", 8)))
    rows = rows[:int(a["kv"].get("limit", 8))]
    if not rows:
        return dict(text=f"nothing called {text} on this map", rows=[])
    lines = [f"{r['name']} · {r['what']} · {r['lat']:.5f}, {r['lon']:.5f}" for r in rows]
    return dict(text="\n".join(lines), rows=rows)


def w_where(call, a):
    m = the_map(call, a["kv"].get("map"))
    g = ground_of(call, m)
    target = a["target"] or a["words"].strip()
    if not target:
        raise ValueError("map.where <thing> or map.where 36.967,-122.008")
    lat, lon, label = point_of(call, g, target)
    said = g.where(lat, lon)
    return dict(text=f"{label}: {said}", rows=[dict(name=label, lat=lat, lon=lon, where=said)])


def w_near(call, a):
    m = the_map(call, a["kv"].get("map"))
    g = ground_of(call, m)
    target = a["target"] or a["words"].strip()
    lat, lon, label = point_of(call, g, target)
    within = num(a["kv"].get("within")) or 300
    kind = a["kv"].get("kind")
    things, _ = call.see("rows " + (kind or "any"))
    me = call.look(target) if not re.fullmatch(r"-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?", target) else None
    rows = []
    for t in placed(call, g, [t for t in things if t.get("kind") not in ("map", "map-layer", "lens", "kind")]):
        if me and t["id"] == me.get("id"):
            continue                                   # not the thing itself
        if t.get("kind") == "route" and t.get("path"):
            # a route is near when any of its path is: measure to its nearest point
            d = min(g.metres((lat, lon), p) for p in parse_points(t["path"]))
        else:
            d = g.metres((lat, lon), (t["lat"], t["lon"]))
        if d <= within:
            rows.append(dict(t, metres=round(d)))
    rows.sort(key=lambda r: r["metres"])
    text = "\n".join(f"{r['metres']} m · {r.get('name') or r.get('title') or r['id']} · {r.get('kind')}" for r in rows)
    return dict(text=(f"{len(rows)} within {within:g} m of {label}\n" + text) if rows else
                f"nothing placed within {within:g} m of {label}", rows=rows)


def plan(call, g, stops_text, mode):
    bits = [s for s in re.split(r"\s*(?:>|→|;)\s*", str(stops_text)) if s.strip()]
    if len(bits) < 2:
        raise ValueError('stops="first > second > …" (things, names on the map, or lat,lon)')
    pts = [point_of(call, g, b) for b in bits]
    r = g.route([(p[0], p[1]) for p in pts], mode)
    r["labels"] = [p[2] for p in pts]
    r["stop_points"] = " ".join(f"{p[0]:.6f},{p[1]:.6f}" for p in pts)
    return r


def w_path(call, a):
    m = the_map(call, a["kv"].get("map"))
    g = ground_of(call, m)
    mode = a["kv"].get("mode", "walk")
    r = plan(call, g, a["kv"].get("stops", a["words"]), mode)
    row = dict(path=polyline(r["path"]), metres=r["metres"], minutes=r["minutes"], legs=r["legs"],
               streets=r["streets"], stops=r["labels"], stop_points=r["stop_points"], mode=mode)
    return dict(text=f"{r['metres']} m · {r['minutes']} min {'on foot' if mode == 'walk' else 'by bike'} · "
                     + " > ".join(r["labels"]) + (" · via " + ", ".join(r["streets"][:6]) if r["streets"] else ""),
                rows=[row])


def w_route(call, a):
    kv = a["kv"]
    existing = call.look(a["target"]) if a["target"] else None
    if a["target"] and (not existing or existing.get("kind") != "route"):
        raise ValueError(f"{a['target']} is not a route")
    m = the_map(call, kv.get("map") or (existing or {}).get("map"))
    g = ground_of(call, m)
    mode = kv.get("mode") or (existing or {}).get("mode") or "walk"
    stops = kv.get("stops") or (existing or {}).get("stops")
    if not stops:
        raise ValueError('map.route name="…" stops="a > b > c" [mode=walk|bike]')
    r = plan(call, g, stops, mode)
    facts = dict(stops=stops, stop_points=r["stop_points"], mode=mode, path=polyline(r["path"]),
                 metres=str(r["metres"]), minutes=str(r["minutes"]), streets=", ".join(r["streets"][:12]),
                 planned=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    said = f"{r['metres']} m · {r['minutes']} min {'on foot' if mode == 'walk' else 'by bike'}"
    if existing:
        call.saw[existing["id"]] = existing.get("rev", 0)
        if kv.get("name"):
            facts["name"] = kv["name"]
        line = "set " + existing["id"] + "".join(f" {k}={q(v)}" for k, v in facts.items())
        return dict(lines=[line], saw=call.saw, text="replanned " + (existing.get("name") or existing["id"]) + " · " + said)
    name = kv.get("name") or " to ".join([r["labels"][0], r["labels"][-1]])
    line = "make kind=route map=" + m["id"] + " name=" + q(name) + "".join(f" {k}={q(v)}" for k, v in facts.items())
    call.saw[m["id"]] = m.get("rev", 0)
    return dict(lines=[line], saw=call.saw, text=f"route {name} · {said}")


def w_layers(call, a):
    m = the_map(call, a["target"] or a["words"].strip() or a["kv"].get("map"))
    g = None
    try:
        g = ground_of(call, m)
    except (ValueError, OSError) as exc:
        ground_error = str(exc)
    else:
        ground_error = ""
    layers, _ = call.see("rows map-layer map=" + m["id"])
    named, _ = call.see("rows map-layer map=" + q(m.get("name", "")))
    seen = set()
    rows = []
    for layer in sorted(layers + named, key=lambda r: (num(r.get("order")) or 99, r["id"])):
        if layer["id"] in seen:
            continue
        seen.add(layer["id"])
        row = {k: layer[k] for k in ("id", "rev", "name", "shows", "look", "color", "icon", "label", "order", "on", "by",
                                     "size", "sees") if layer.get(k) not in (None, "")}
        shows = str(layer.get("shows", "")).strip()
        try:
            if not shows.startswith(SHOWS_START):
                raise ValueError("a layer shows a reading: rows <kind> …, board.…, map.near … or map.find …")
            found, _ = call.see(shows)
            row["items"] = placed(call, g, found, layer) if g else []
            row["count"] = len(row["items"])
            row["unplaced"] = len([f for f in found if isinstance(f, dict) and f.get("id")]) - row["count"]
        except ValueError as exc:
            row["items"], row["count"], row["error"] = [], 0, str(exc)[:200]
        rows.append(row)
    head = dict(id=m["id"], rev=m.get("rev", 0), kind="map", name=m.get("name"), ground=m.get("ground"),
                lens=m.get("lens"), centre=m.get("centre", ""), ground_error=ground_error, layers=len(rows))
    pref = my_preference(call, m["lens"]) if m.get("lens") else None
    if pref:
        head["hidden"] = pref.get("map.hide", "")
        head["focus"] = pref.get("map.focus", "")
        hidden = set(head["hidden"].split())
        for r in rows:
            if r["id"] in hidden:
                r["hidden_for_you"] = "yes"
        ground_hidden = [h.split(":", 1)[1] for h in hidden if h.startswith("ground:")]
        if ground_hidden:
            head["ground_hidden_for_you"] = " ".join(sorted(ground_hidden))
    text = "\n".join(f"{r.get('name')} · {r['count']} placed" + (" · hidden for you" if r.get("hidden_for_you") else "")
                     + (f" · {r['error']}" if r.get("error") else "") for r in rows)
    return dict(text=f"{m.get('name')}: {len(rows)} layers\n" + text, rows=[head] + rows)


def my_preference(call, lens):
    """The caller's own view preference for this map's lens that holds map.* settings (the newest), or None.
    A preference names its lens by id; a map names it by name, so both are tried."""
    names = {lens}
    try:
        names.add(lens_id(call, lens))
    except ValueError:
        pass
    prefs, _ = call.see("rows view-preference")
    # whose it is: made_by when the person made it (personal-view), for= when this module made it for them
    who = call.person
    mine = [p for p in prefs if p.get("lens") in names and who and who in (p.get("for"), p.get("made_by"))
            and any(k.startswith("map.") for k in p)]
    return mine[-1] if mine else None


def lens_id(call, lens):
    """personal-view refuses a module's line (it takes any module for a painter), so the map module makes the
    view-preference itself, exactly as personal-view would: sees=me, lens=<the lens's id>."""
    # a lens shares its name with its widget (and look takes the first), so ask for the lens by kind
    if re.fullmatch(r"[a-z]{2,4}\d+", lens):
        return lens
    rows, _ = call.see("rows lens name=" + q(lens))
    if not rows:
        raise ValueError(f"the map's lens {lens} is not a lens you can see")
    return rows[0]["id"]


def w_hide(call, a, hide=True):
    m = the_map(call, a["kv"].get("map"))
    lens = m.get("lens")
    if not lens:
        raise ValueError(f"{m.get('name')} names no lens=, so there is no window to hide it from")
    target = a["target"] or a["words"].strip()
    layer = call.look(target)
    if layer and layer.get("kind") == "map-layer":
        key = layer["id"]
        label = layer.get("name") or key
    elif target in ("buildings", "streets", "labels", "places", "props", "water", "green"):
        key, label = "ground:" + target, target
    else:
        raise ValueError(f"{target}: name a map-layer, or one of buildings, streets, labels, places, props")
    pref = my_preference(call, lens)
    hidden = set(str((pref or {}).get("map.hide", "")).split())
    (hidden.add if hide else hidden.discard)(key)
    value = " ".join(sorted(hidden))
    if pref:
        call.saw[pref["id"]] = pref.get("rev", 0)
        line = f"set {pref['id']} map.hide={q(value)}"
    else:
        line = f"make kind=view-preference sees=me lens={lens_id(call, lens)} map.hide={q(value)}"
    return dict(lines=[line], saw=call.saw, text=("hidden for you: " if hide else "showing again for you: ") + label)


def w_show(call, a):
    m = the_map(call, a["kv"].get("map"))
    lens = m.get("lens")
    if not lens:
        raise ValueError(f"{m.get('name')} names no lens=")
    target = a["target"] or a["words"].strip()
    g = ground_of(call, m)
    lat, lon, label = point_of(call, g, target)
    focus = f"{lat:.6f},{lon:.6f}@{datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S%f')}"
    pref = my_preference(call, lens)
    if pref:
        call.saw[pref["id"]] = pref.get("rev", 0)
        line = f"set {pref['id']} map.focus={q(focus)}"
    else:
        line = f"make kind=view-preference sees=me lens={lens_id(call, lens)} map.focus={q(focus)}"
    return dict(lines=[line], saw=call.saw, text=f"your map turns to {label}")


WORDS = [
    ("map.find", "see", "<words> [map=] [limit=8]", w_find,
     "map.find <words>: places, streets and corners on the map, best first, with lat/lon. "
     "Two streets joined by & find where they cross: map.find Seabright & Murray."),
    ("map.where", "see", "<thing|lat,lon> [map=]", w_where,
     "map.where <thing>: where it is, in words: the street and the nearest named place."),
    ("map.near", "see", "<thing|lat,lon|name> [within=300] [kind=] [map=]", w_near,
     "map.near <thing> within=300: placed things you can see near it, nearest first, with metres."),
    ("map.path", "see", 'stops="a > b > c" [mode=walk|bike] [map=]', w_path,
     'map.path stops="Seabright Station > Java Junction": a street path as a reading (nothing is made).'),
    ("map.route", "do", '[<route>] name= stops="a > b > c" [mode=walk|bike] [map=]', w_route,
     'map.route name="Flyers north" stops="a > b > c": makes a route thing that keeps its street path, length and '
     "minutes. map.route <route> replans it (after its stops moved or changed). Undo takes it back."),
    ("map.layers", "see", "[<map>]", w_layers,
     "map.layers <map>: every layer of the map with the placed things its reading finds, as you may see them."),
    ("map.hide", "do", "<layer|buildings|streets|labels|places|props> [map=]", lambda c, a: w_hide(c, a, True),
     "map.hide <layer>: hide a layer from your own map window only. map.unhide shows it again."),
    ("map.unhide", "do", "<layer|buildings|streets|labels|places|props> [map=]", lambda c, a: w_hide(c, a, False),
     "map.unhide <layer>: show a layer you hid in your own map window."),
    ("map.show", "do", "<thing|name|lat,lon> [map=]", w_show,
     "map.show <thing>: turn your own map window to a thing or a place."),
]
BY_WORD = {w[0]: w for w in WORDS}


def answer(msg):
    call = Call(msg)
    try:
        word = BY_WORD[msg["word"]]
        result = word[3](call, msg.get("args") or {"target": "", "words": "", "kv": {}})
    except Exception as exc:          # every refusal is said, and the process carries on
        result = dict(refused=str(exc) or type(exc).__name__)
    send(dict(result, t="answer", use=msg["use"]))


def main():
    for raw in sys.stdin:
        msg = json.loads(raw)
        t = msg.get("t")
        if t == "hello":
            hello.update(msg)
            send(dict(t="offer", words=[dict(word=w, kind=k, takes=takes, help=h) for w, k, takes, _, h in WORDS]))
        elif t == "call":
            args = msg.get("args") or {}
            msg["args"] = dict(target=args.get("target") or "", words=args.get("words") or "", kv=args.get("kv") or {})
            threading.Thread(target=answer, args=(msg,), daemon=True).start()
        elif t == "rows":
            deliver(msg)
        elif t == "status?":
            send(dict(t="status", use=msg.get("use"), doing=f"map words; {len(grounds)} ground(s) read"))
        elif t == "off":
            return


if __name__ == "__main__":
    main()
