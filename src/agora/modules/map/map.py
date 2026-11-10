"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

The map module: words that read the live ground (tiles.py) and the placed things of the world.

A map is a world thing (`kind=map`): a name, a `centre=lat,lon` it opens at, and the lens that shows it. Its ground is
the live tiles (OpenStreetMap through OpenFreeMap, buildings through Overture), fetched only where someone looks and
kept on disk under this module's home. An older map may name a ground file instead (`ground=<file>`, agora-ground/1).

A thing is placed when it says `lat`/`lon`; or `at`/`place` naming a placed thing (an event at the town hall moves
with it); or, approximately, a `location` the ground can find by name. A building is ground until something needs it:
`map.add` and `map.adopt` make it a world thing (`kind=structure ref=overture:<id>`), and from then on it has a page.

Words (all readings run as the caller, so nobody sees a placed thing they could not already see):
  map.tile <z/x/y>                  one tile's chunk for a map window to draw (agora-tile/1)
  map.find <text> [near=lat,lon]    places, streets, corners and things; then the wider world (Nominatim)
  map.where <thing|lat,lon>         a sentence: the street and nearest named place
  map.near <thing|lat,lon> [within=300] [kind=]   placed things nearby, nearest first
  map.place <thing|overture:id> [lat= lon=]       a building or place: its facts, its page, and what is at it
  map.add <place> kind=<k> [facts]  put something at a place (a building becomes a structure thing on first use)
  map.adopt <overture:id> lat= lon= [name=]      make a building a world thing without adding anything yet
  map.path stops="a > b > c" [mode=walk|bike]     a street path, as a reading (the planner's preview)
  map.route [<route>] name= stops= [mode=]        make a route thing, or replan one
  map.layers [<map>]                every layer with its placed rows: what a map window watches
  map.hide <layer> / map.unhide <layer>   hide a layer from your own view (others still see it)
  map.show <thing>                  turn your map window to a thing
  map.cache [trim=<GB>]             how much ground is kept on this machine; trim forgets the oldest

Not contained here (see SHAPE section 11): the process reads and writes files under its own home (the tile cache),
reads the world's blob store by a file thing's digest (checked), and fetches tiles and searches over the network.
"""
import datetime
import hashlib
import json
import math
import re
import sys
import threading
import time
import urllib.parse
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ground import Ground, parse_points, polyline  # noqa: E402
import tiles as T  # noqa: E402

out_lock = threading.Lock()
pending = {}
hello = {}
grounds = {}            # blob digest -> Ground (maps that name a ground file)
areas = {}              # (lat, lon, radius) -> Ground over the live tiles there
areas_lock = threading.Lock()
live = None
geo_cache = {}
geo_lock = threading.Lock()
geo_last = [0.0]
KEEP = ("kind", "post_kind", "thread", "title", "name", "label", "start", "end", "location", "place", "at", "path", "metres", "minutes",
        "stops", "mode", "streets", "color", "icon", "by", "who", "done", "seats", "osm", "tags", "ring", "approx",
        "ref", "class", "type", "about", "text", "made", "number", "street")
SHOWS_START = ("rows ", "board.", "map.near ", "map.find ")
REF = re.compile(r"overture:[0-9a-f-]{8,40}")
DEFAULT_CENTRE = (36.9672, -122.0088)


def send(msg):
    with out_lock:
        print(json.dumps(msg, ensure_ascii=True), flush=True)


def q(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def tiles():
    global live
    if live is None:
        # AGORA_MAP_CACHE lets hidden test worlds share one cache instead of fetching every tile again
        import os
        live = T.Tiles(os.environ.get("AGORA_MAP_CACHE") or Path(hello.get("home") or ".") / "ground")
    return live


class Call:
    """One call: reads go out as the caller, under this call's `use`, and come back in order."""

    def __init__(self, msg):
        self.use = msg["use"]
        self.person = (msg.get("caller") or {}).get("person", "")
        self.saw = {}
        self.looked = {}
        self.refused = {}            # ref -> what the kernel said when a look of it was refused
        self.ground = None           # the ground around the map's centre, made when first needed

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
        except ValueError as exc:
            rows = []
            self.refused[ref] = str(exc)
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
        if (not m or m.get("kind") != "map") and not re.fullmatch(r"[A-Za-z]+\d+", name):
            # a name another thing shares (the place itself is often called what its map is) makes look refuse;
            # the maps of that name are what is meant here (found 5 Nov on the Seabright world)
            try:
                maps, _ = call.see("rows map name=" + q(name))
            except ValueError:
                maps = []
            m = maps[0] if len(maps) == 1 else m
        if not m or m.get("kind") != "map":
            raise ValueError(f"{name} is not a map (make kind=map name=… centre=lat,lon)")
        return m
    maps, _ = call.see("rows map")
    if not maps:
        raise ValueError("there is no map here yet: make kind=map name=… centre=lat,lon")
    return maps[0]


def centre_of(m):
    try:
        la, lo = [float(v) for v in str((m or {}).get("centre") or "").split(",")]
        return la, lo
    except ValueError:
        return DEFAULT_CENTRE


def area(lat, lon, radius=1500):
    """A Ground over the live tiles within `radius` metres of a point (snapped, so nearby asks share one)."""
    step = 0.01 if radius <= 1500 else 0.02
    key = (round(lat / step) * step, round(lon / step) * step, int(radius))
    with areas_lock:
        g = areas.get(key)
        if g is not None:
            areas[key] = areas.pop(key)
            return g
    g = Ground(T.ground_doc(tiles(), key[0], key[1], radius + step * 111000))
    with areas_lock:
        areas[key] = g
        while len(areas) > 10:
            areas.pop(next(iter(areas)))
    return g


def ground_file(call, m):
    ref = m.get("ground")
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


def home_ground(call, m, near=None):
    """The ground names are looked up in: around `near` (lat, lon) when given, else around the map's centre."""
    if m and m.get("ground") and not near:
        return ground_file(call, m)
    la, lo = near or centre_of(m)
    return area(la, lo, 1500)


def num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def latlon_text(text):
    m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*", str(text or ""))
    return (float(m.group(1)), float(m.group(2))) if m else None


def position(call, gf, row, depth=0):
    """(lat, lon, approx) for a row, or None: its own lat/lon; else the thing its at=/place= names; else a name on
    the ground said where an id could go; else its location text found on the ground (approximate).
    `gf()` gives the ground to look names up in (made only when a name needs it)."""
    lat, lon = num(row.get("lat")), num(row.get("lon"))
    if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon, False
    for key in ("at", "place"):
        ref = row.get(key)
        if ref and depth < 2:
            if not re.fullmatch(r"[a-z]{2,4}\d+", str(ref)):
                ll = latlon_text(ref)
                if ll:
                    return ll[0], ll[1], False
            other = call.look(str(ref)) if re.fullmatch(r"[a-z]{2,4}\d+", str(ref)) else None
            if other and other.get("id") != row.get("id"):
                if other.get("rev") is not None:
                    call.saw[other["id"]] = other["rev"]
                p = position(call, gf, other, depth + 1)
                if p:
                    return p
            if not re.fullmatch(r"[a-z]{2,4}\d+", str(ref)):
                # at="Seabright & Murray": a name on the ground, said where an id could go (a corner or a named
                # place is a point, so it is not marked approximate; a text location below is)
                g = gf()
                hits = g.find(str(ref), 1) if g else []
                if hits:
                    return hits[0]["lat"], hits[0]["lon"], False
                thing = call.look(str(ref))
                if thing and thing.get("id") != row.get("id"):
                    p = position(call, gf, thing, depth + 1)
                    if p:
                        return p
    if row.get("location"):
        g = gf()
        hits = g.find(str(row["location"]), 1) if g else []
        if hits:
            return hits[0]["lat"], hits[0]["lon"], True
        # not a name in the tiles here (a beach is an area, not a point): ask the wider world, a few new names a
        # call at most (each new one waits its turn at Nominatim; answers are kept, so later readings are instant).
        # Only a place text everyone here sees, or the asker's own, may go outside (Alex, 28 Oct: "Public, or my
        # own"); the kernel says which on each row it hands a module (kernel.outside_marks). A row without that
        # answer is treated as private.
        if row.get("outside") not in ("public", "yours") or "location" in (row.get("outside_not") or ()):
            return None
        text = str(row["location"])
        cached = (text.lower().strip(), None if not getattr(gf, "near", None) else (round(gf.near[0], 1), round(gf.near[1], 1)))
        if cached in geo_cache or getattr(call, "geocoded", 0) < 3:
            if cached not in geo_cache:
                call.geocoded = getattr(call, "geocoded", 0) + 1
            found = geocode(text, getattr(gf, "near", None), 1)
            if found:
                return found[0]["lat"], found[0]["lon"], True
    return None


def point_of(call, gf, text, search=True):
    """A stop or a centre: 'lat,lon', a thing (id or name), a building ref, or a name on the ground."""
    text = str(text).strip()
    ll = latlon_text(text)
    if ll:
        return ll[0], ll[1], text
    if REF.fullmatch(text):
        rows, _ = call.see("rows structure ref=" + text)
        if rows:
            p = position(call, gf, rows[0])
            if p:
                return p[0], p[1], rows[0].get("name") or text
        raise ValueError(f"{text}: say where it is (lat,lon), or adopt it first")
    g = gf()
    if g:
        hits = g.find(text, 1)
        if hits and (hits[0]["what"] == "corner" or not re.fullmatch(r"[a-z]{2,4}\d+", text)):
            thing = call.look(text) if re.fullmatch(r"[a-z]{2,4}\d+", text) else None
            if not thing:
                return hits[0]["lat"], hits[0]["lon"], hits[0]["name"]
    thing = call.look(text)
    if thing:
        p = position(call, gf, thing)
        if p:
            return p[0], p[1], thing.get("name") or thing.get("title") or thing["id"]
        # a thing it names is not a search: its title is not an address, and it may be private (security review,
        # 28 Oct: a private meeting's title went to Nominatim). Only text that names nothing goes outside.
        raise ValueError(f"{thing['id']} has no place the map can read; give it location=, at= or lat= lon=")
    why = call.refused.get(text, "")
    if "things are called" in why or "share the name" in why:
        raise ValueError(why)                      # which one? the caller picks; the name never goes outside
    if re.fullmatch(r"[a-z]{2,4}\d+", text):
        raise ValueError(f"{text}: no thing you can see has that id")     # an id is never a search
    if not search:
        # saved text (a route's stops, a layer's search) is its thing's, not typed now: it goes outside only when that
        # thing is public or the caller's own (approved-builds review H3, 28 Oct)
        raise ValueError(f"{text}: not a place this map knows here, and it isn't yours to look up outside")
    found = geocode(text)
    if found:
        return found[0]["lat"], found[0]["lon"], found[0]["name"]
    raise ValueError(f"{text}: not a place this map knows (try map.find {text})")


def who(call, r):
    """Whose a thing is, by name: the person a module made it for (for=), else its maker. A thing this module made
    says by=map; the person who asked is the one to show."""
    f = r.get("for")
    if f and re.fullmatch(r"[a-z]{2,4}\d+", str(f)):
        p = call.look(str(f))
        if p and p.get("name"):
            return p["name"]
    return r.get("by", "")


def placed(call, gf, rows):
    out = []
    for r in rows:
        if not isinstance(r, dict) or not r.get("id"):
            continue
        item = {k: r[k] for k in KEEP if r.get(k) not in (None, "")}
        if r.get("for"):
            item["by"] = who(call, r)
        if "text" in item:
            item["text"] = str(item["text"])[:140]
        item["id"], item["rev"] = r["id"], r.get("rev", 0)
        if r.get("kind") == "route" and r.get("path"):
            pts = parse_points(r["path"])
            if pts:
                item["lat"], item["lon"] = pts[0]
            out.append(item)
            continue
        p = position(call, gf, r)
        if not p:
            continue
        item["lat"], item["lon"] = round(p[0], 7), round(p[1], 7)
        if p[2]:
            item["approx"] = "yes"
        out.append(item)
    return out


def ground_getter(call, m, near=None):
    box = []

    def gf():
        if not box:
            try:
                box.append(home_ground(call, m, near))
            except (ValueError, OSError) as exc:
                sys.stderr.write(f"ground: {exc}\n")
                box.append(None)
        return box[0]
    gf.near = near or (centre_of(m) if m else None)
    return gf


# --- the wider world: Nominatim (OpenStreetMap's own search), at most once a second, answers kept -------------------
def geocode(text, near=None, limit=5):
    key = (text.lower().strip(), None if not near else (round(near[0], 1), round(near[1], 1)))
    with geo_lock:
        if key in geo_cache:
            return geo_cache[key]
        wait = 1.05 - (time.time() - geo_last[0])
        if wait > 0:
            time.sleep(wait)
        geo_last[0] = time.time()
    params = dict(q=text, format="jsonv2", limit=str(limit), addressdetails="0")
    if near:
        # the box around a rounded centre: its midpoint was the map's exact centre, sent with every query (for a home
        # map, Alex's address; security review H4, 28 Oct). 0.1 degrees is what the cache key already uses.
        lat0, lon0 = round(near[0], 1), round(near[1], 1)
        params["viewbox"] = "%.1f,%.1f,%.1f,%.1f" % (lon0 - 0.6, lat0 + 0.5, lon0 + 0.6, lat0 - 0.5)
    try:
        status, body = tiles().http.get("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params))
        rows = json.loads(body) if status == 200 else []
    except (OSError, ValueError):
        rows = []
    out = []
    for r in rows:
        name = r.get("name") or str(r.get("display_name", "")).split(",")[0]
        out.append(dict(name=name, what=str(r.get("type") or r.get("category") or "place"),
                        where=", ".join(str(r.get("display_name", "")).split(", ")[1:4]),
                        lat=round(float(r["lat"]), 6), lon=round(float(r["lon"]), 6),
                        osm=f"{r.get('osm_type', '')}/{r.get('osm_id', '')}"))
    with geo_lock:
        geo_cache[key] = out
    return out


# --- the words --------------------------------------------------------------------------------------------------
def w_tile(call, a):
    t = (a["target"] or a["words"]).strip()
    m = re.fullmatch(r"(\d{1,2})/(\d+)/(\d+)", t)
    if not m:
        raise ValueError("map.tile <z/x/y>")
    z, x, y = map(int, m.groups())
    if z > 14 or x >= 1 << z or y >= 1 << z:
        raise ValueError("no such tile")
    text = tiles().chunk(z, x, y)
    return dict(text=f"tile {z}/{x}/{y} · {len(text) // 1024} KB", rows=[dict(tile=t, chunk=text)])


def w_find(call, a):
    text = (a["words"].strip() or a["kv"].get("text", "")).strip()
    if not text:
        raise ValueError("map.find <words>: a street, a corner (Seabright & Murray), a place's name, or a town")
    limit = int(a["kv"].get("limit", 8))
    m = the_map(call, a["kv"].get("map"))
    near = latlon_text(a["kv"].get("near")) or centre_of(m)
    rows = []
    words = [w for w in re.findall(r"[a-z0-9']+", text.lower())]
    # searching what the world already places sends nothing out: other things' location text is placed from the ground
    # and from answers already kept, never geocoded on the side (security review H4, 28 Oct). Only the words the
    # person typed may go to the outside search, below.
    call.geocoded = 3
    for kind in ("spot", "structure", "event"):
        try:
            things, _ = call.see("rows " + kind)
        except ValueError:
            continue
        for t in placed(call, ground_getter(call, m, near), things):
            hay = (str(t.get("name") or t.get("title") or "")).lower()
            if words and all(w in hay for w in words):
                rows.append(dict(name=t.get("name") or t.get("title"), what=t.get("kind"), id=t["id"],
                                 lat=t["lat"], lon=t["lon"]))
    try:
        rows += home_ground(call, m, near).find(text, limit)
    except (ValueError, OSError) as exc:
        sys.stderr.write(f"find: {exc}\n")
    if len(rows) < limit and str(m.get("search", "nominatim")) != "off":
        seen = {(r["name"], round(r["lat"], 3), round(r["lon"], 3)) for r in rows}
        for r in geocode(text, near):
            if (r["name"], round(r["lat"], 3), round(r["lon"], 3)) not in seen:
                rows.append(r)
    rows = rows[:limit]
    if not rows:
        return dict(text=f"nothing called {text} on this map", rows=[])
    lines = [f"{r['name']} · {r['what']}" + (f" · {r['where']}" if r.get("where") else "")
             + f" · {r['lat']:.5f}, {r['lon']:.5f}" for r in rows]
    return dict(text="\n".join(lines), rows=rows)


def w_where(call, a):
    m = the_map(call, a["kv"].get("map"))
    target = a["target"] or a["words"].strip()
    if not target:
        raise ValueError("map.where <thing> or map.where 36.967,-122.008")
    lat, lon, label = point_of(call, ground_getter(call, m), target)
    said = area(lat, lon, 600).where(lat, lon)
    return dict(text=f"{label}: {said}", rows=[dict(name=label, lat=lat, lon=lon, where=said)])


def w_near(call, a):
    m = the_map(call, a["kv"].get("map"))
    gf = ground_getter(call, m)
    target = a["target"] or a["words"].strip()
    lat, lon, label = point_of(call, gf, target)
    within = num(a["kv"].get("within")) or 300
    kind = a["kv"].get("kind")
    things, _ = call.see("rows " + (kind or "any"))
    me = call.look(target) if not latlon_text(target) else None
    rows = []
    for t in placed(call, gf, [t for t in things if t.get("kind") not in ("map", "map-layer", "lens", "kind", "widget")]):
        if me and t["id"] == me.get("id"):
            continue                                   # not the thing itself
        if t.get("kind") == "route" and t.get("path"):
            d = min(Ground.metres((lat, lon), p) for p in parse_points(t["path"]))
        else:
            d = Ground.metres((lat, lon), (t["lat"], t["lon"]))
        if d <= within:
            rows.append(dict(t, metres=round(d)))
    rows.sort(key=lambda r: r["metres"])
    text = "\n".join(f"{r['metres']} m · {r.get('name') or r.get('title') or r['id']} · {r.get('kind')}" for r in rows)
    return dict(text=(f"{len(rows)} within {within:g} m of {label}\n" + text) if rows else
                f"nothing placed within {within:g} m of {label}", rows=rows)


# --- buildings and the things at them -----------------------------------------------------------------------------
def building_at(ref, lat, lon):
    """A building's facts from the z14 tile under (lat, lon): name, class, height, osm, number, and its centre."""
    bid = ref.split(":", 1)[1]
    fx, fy = T.lonlat_to_tile(lon, lat, 14)
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        tx, ty = int(fx) + dx, int(fy) + dy
        c = json.loads(tiles().chunk(14, tx, ty))
        hits = [b for b in c["b"] if b[0] == bid]
        if not hits:
            continue
        b = max(hits, key=lambda b: len(b[4][0]))
        ring = b[4][0]
        cx, cy = sum(ring[0::2]) / (len(ring) // 2), sum(ring[1::2]) / (len(ring) // 2)
        blon, blat = T.tile_to_lonlat(tx + cx / T.E, ty + cy / T.E, 14)
        out = dict(ref=ref, name=b[5], height=b[1], **{"class": b[3]}, lat=round(blat, 6), lon=round(blon, 6))
        for k in ("osm", "number", "num_floors", "src", "subtype", "roof_shape"):
            if b[6].get(k) not in (None, ""):
                out[k] = b[6][k]
        return out
    return None


def place_name(b, g):
    if b.get("name"):
        return b["name"]
    street, d = g.nearest_street(b["lat"], b["lon"]) if g else (None, None)
    if b.get("number") and street:
        return f"{b['number']} {street}"
    what = (b.get("class") or b.get("subtype") or "building").replace("_", " ")
    return f"A {what} on {street}" if street and d is not None and d < 60 else f"A {what}"


def structure_for(call, ref):
    rows, _ = call.see("rows structure ref=" + ref)
    return rows[0] if rows else None


def adopt_line(call, ref, kv, handle="place"):
    lat, lon = num(kv.get("lat")), num(kv.get("lon"))
    if lat is None or lon is None:
        raise ValueError(f"say where {ref} is: lat= lon= (any point inside it)")
    b = building_at(ref, lat, lon)
    if not b:
        raise ValueError(f"no building {ref} near {lat:.5f}, {lon:.5f}")
    g = area(b["lat"], b["lon"], 400)
    name = kv.get("name") or place_name(b, g)
    street, _ = g.nearest_street(b["lat"], b["lon"])
    facts = dict(name=name, ref=ref, lat=b["lat"], lon=b["lon"])
    for k in ("class", "osm", "number", "height", "subtype"):
        if b.get(k) not in (None, ""):
            facts[k] = b[k]
    if street:
        facts["street"] = street
    line = "make kind=structure" + "".join(f" {k}={q(v)}" for k, v in facts.items()) + (f" as={handle}" if handle else "")
    return line, facts


def page_for(call, facts):
    """Which page a place opens in: its own page=, else a page widget whose places= names its class, else place-page."""
    if facts.get("page"):
        return facts["page"]
    try:
        widgets, _ = call.see("rows widget")
    except ValueError:
        widgets = []
    # the most particular word first: a building's own class (townhall, house) before its broad subtype (civic)
    for k in ("type", "class", "what", "subtype"):
        word = str(facts.get(k) or "").lower()
        for w in widgets if word else ():
            if word in str(w.get("places") or "").lower().split():
                return w.get("name")
    return "place-page"


def w_place(call, a):
    kv = a["kv"]
    ref = (a["target"] or a["words"].strip() or kv.get("ref", "")).strip().strip('"')
    if not ref:
        # a page opened on nothing still paints: an empty answer, not a refusal
        return dict(text="map.place <thing|overture:id> [lat= lon=]: no place chosen", rows=[])
    thing, b = None, None
    if REF.fullmatch(ref):
        thing = structure_for(call, ref)
        if not thing:
            lat, lon = num(kv.get("lat")), num(kv.get("lon"))
            b = building_at(ref, lat, lon) if lat is not None and lon is not None else None
    else:
        thing = call.look(ref)
        if not thing:
            raise ValueError(f"{ref}: no such thing or building")
    head = dict(thing.items()) if thing else dict(b or dict(ref=ref))
    if thing:
        head["by"] = who(call, thing)
    head.setdefault("ref", ref if REF.fullmatch(ref) else "")
    head["thing"] = thing["id"] if thing else ""
    if not thing and b:
        try:
            g = area(b["lat"], b["lon"], 400)
            head["name"] = place_name(b, g)
            street, _ = g.nearest_street(b["lat"], b["lon"])
            if street:
                head["street"] = street
        except (ValueError, OSError):
            pass
    head["page"] = page_for(call, head)
    rows = [dict(head, row="place")]
    if thing:
        at, _ = call.see("rows any at=" + thing["id"])
        about, _ = call.see("rows post about=" + thing["id"])
        for r in at:
            if r.get("id") != thing["id"]:
                rows.append(dict({k: r[k] for k in KEEP if r.get(k) not in (None, "")}, id=r["id"], rev=r.get("rev", 0),
                                 row="at", by=who(call, r), made=r.get("made", "")))
        for r in about:
            rows.append(dict(id=r["id"], rev=r.get("rev", 0), row="talk", text=str(r.get("text", ""))[:600],
                             by=who(call, r), made=r.get("made", ""), likes=r.get("likes", 0)))
    name = head.get("name") or head.get("title") or ref
    n_at = sum(1 for r in rows if r["row"] == "at")
    n_talk = sum(1 for r in rows if r["row"] == "talk")
    text = (f"{name} · " + ("a world thing" if thing else "not a world thing yet") +
            (f" · {n_at} things at it" if n_at else "") + (f" · {n_talk} posts about it" if n_talk else "") +
            f" · page {head['page']}")
    return dict(text=text, rows=rows)


def w_add(call, a):
    kv = dict(a["kv"])
    ref = (a["target"] or kv.pop("place", "") or a["words"].strip()).strip()
    kind = kv.pop("kind", "")
    if not ref or not kind:
        raise ValueError('map.add <place> kind=<kind> [facts]: map.add overture:… lat= lon= kind=event title="Party" start="Sat 8pm"')
    if kind in ("structure", "map", "map-layer", "kind", "lens", "widget"):
        raise ValueError(f"map.add does not make a {kind}")
    lines, facts = [], {}
    if REF.fullmatch(ref):
        s = structure_for(call, ref)
        if s:
            at = s["id"]
            call.saw[s["id"]] = s.get("rev", 0)
            label = s.get("name") or ref
        else:
            line, b = adopt_line(call, ref, kv)
            lines.append(line)
            at, label = "$place", b["name"]
        kv.pop("lat", None)
        kv.pop("lon", None)
        facts["at"] = at
    elif re.fullmatch(r"[a-z]{2,4}\d+", ref):
        t = call.look(ref)
        if not t:
            raise ValueError(f"no thing {ref} here")
        facts["at"] = ref
        label = t.get("name") or t.get("title") or ref
    else:
        m = the_map(call, kv.pop("map", None))
        lat, lon, label = point_of(call, ground_getter(call, m), ref)
        facts.update(lat=f"{lat:.6f}", lon=f"{lon:.6f}")
        if not latlon_text(ref):
            facts["location"] = label
    for k, v in kv.items():
        if not re.fullmatch(r"[a-z_][a-z0-9_.-]*", k):
            raise ValueError(f"{k}: not a fact name")
        facts[k] = v
    line = f"make kind={kind}" + "".join(f" {k}={v if v == '$place' else q(v)}" for k, v in facts.items())
    lines.append(line)
    title = facts.get("title") or facts.get("name") or kind
    return dict(lines=lines, saw=call.saw, text=f"{title} at {label}")


def w_adopt(call, a):
    kv = dict(a["kv"])
    ref = (a["target"] or a["words"].strip() or kv.pop("ref", "")).strip()
    if not REF.fullmatch(ref):
        raise ValueError("map.adopt overture:<id> lat= lon= [name=]: make a building a world thing")
    s = structure_for(call, ref)
    if s:
        if kv.get("name") and kv["name"] != s.get("name"):
            call.saw[s["id"]] = s.get("rev", 0)
            return dict(lines=[f"set {s['id']} name={q(kv['name'])}"], saw=call.saw, text=f"renamed to {kv['name']}")
        return dict(text=f"{s.get('name')} is a world thing already ({s['id']})", rows=[s])
    line, facts = adopt_line(call, ref, kv, handle="")
    return dict(lines=[line], saw=call.saw, text=f"{facts['name']} is a world thing now")


# --- routes -------------------------------------------------------------------------------------------------------
def plan(call, m, stops_text, mode, search=True):
    bits = [s for s in re.split(r"\s*(?:>|→|;)\s*", str(stops_text)) if s.strip()]
    if len(bits) < 2:
        raise ValueError('stops="first > second > …" (things, names on the map, or lat,lon)')
    gf = ground_getter(call, m)
    pts = [point_of(call, gf, b, search) for b in bits]
    if m.get("ground") and all(ground_file(call, m).contains(p[0], p[1], 50) for p in pts):
        g = ground_file(call, m)
    else:
        lat = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
        lon = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
        span = max(Ground.metres((lat, lon), (p[0], p[1])) for p in pts)
        if span > 6000:
            raise ValueError(f"those stops are {span * 2 / 1000:.0f} km apart; a route walks streets up to about 12 km for now")
        g = area(lat, lon, max(800, span + 600))
    r = g.route([(p[0], p[1]) for p in pts], mode)
    r["labels"] = [p[2] for p in pts]
    r["stop_points"] = " ".join(f"{p[0]:.6f},{p[1]:.6f}" for p in pts)
    return r


def w_path(call, a):
    m = the_map(call, a["kv"].get("map"))
    mode = a["kv"].get("mode", "walk")
    r = plan(call, m, a["kv"].get("stops", a["words"]), mode)
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
    mode = kv.get("mode") or (existing or {}).get("mode") or "walk"
    stops = kv.get("stops") or (existing or {}).get("stops")
    if not stops:
        raise ValueError('map.route name="…" stops="a > b > c" [mode=walk|bike]')
    typed = bool(kv.get("stops"))
    r = plan(call, m, stops, mode, search=typed or (existing or {}).get("outside") in ("public", "yours"))
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


# --- layers and your own view -------------------------------------------------------------------------------------
def w_layers(call, a):
    m = the_map(call, a["target"] or a["words"].strip() or a["kv"].get("map"))
    gf = ground_getter(call, m)
    layers, _ = call.see("rows map-layer map=" + m["id"])
    named, _ = call.see("rows map-layer map=" + q(m.get("name", "")))
    seen = set()
    rows = []
    for layer in sorted(layers + named, key=lambda r: (num(r.get("order")) or 99, r["id"])):
        if layer["id"] in seen:
            continue
        seen.add(layer["id"])
        row = {k: layer[k] for k in ("id", "rev", "name", "shows", "look", "color", "icon", "label", "order", "on", "by",
                                     "size", "sees", "about", "only") if layer.get(k) not in (None, "")}
        shows = str(layer.get("shows", "")).strip()
        try:
            if not shows.startswith(SHOWS_START):
                raise ValueError("a layer shows a reading: rows <kind> …, board.…, map.near … or map.find …")
            if shows.startswith(("map.find", "map.near")) and layer.get("outside") not in ("public", "yours"):
                # a layer's saved search is its maker's text: it isn't sent outside for someone else (review H3)
                raise ValueError("this layer searches with its maker's text, which goes outside only for them or "
                                 "when the layer is public")
            found, _ = call.see(shows)
            row["items"] = placed(call, gf, found)
            row["count"] = len(row["items"])
            row["unplaced"] = len([f for f in found if isinstance(f, dict) and f.get("id")]) - row["count"]
        except ValueError as exc:
            row["items"], row["count"], row["error"] = [], 0, str(exc)[:200]
        rows.append(row)
    la, lo = centre_of(m)
    head = dict(id=m["id"], rev=m.get("rev", 0), kind="map", name=m.get("name"), lens=m.get("lens"),
                centre=m.get("centre", f"{la},{lo}"), ground="live" if not m.get("ground") else m["ground"],
                ground_error="", layers=len(rows), style=m.get("style", ""))
    pref = my_preference(call, m["lens"]) if m.get("lens") else None
    if pref:
        head["hidden"] = pref.get("map.hide", "")
        head["focus"] = pref.get("map.focus", "")
        head["mystyle"] = pref.get("map.style", "")
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


def set_pref(call, m, key, value):
    lens = m.get("lens")
    if not lens:
        raise ValueError(f"{m.get('name')} names no lens=, so there is no window for it")
    pref = my_preference(call, lens)
    if pref:
        call.saw[pref["id"]] = pref.get("rev", 0)
        return f"set {pref['id']} {key}={q(value)}"
    return f"make kind=view-preference sees=me lens={lens_id(call, lens)} {key}={q(value)}"


GROUND_LAYERS = ("buildings", "streets", "labels", "places", "props", "water", "green", "shadows", "names")


def w_hide(call, a, hide=True):
    m = the_map(call, a["kv"].get("map"))
    target = a["target"] or a["words"].strip()
    layer = call.look(target) if target not in GROUND_LAYERS else None
    if layer and layer.get("kind") == "map-layer":
        key = layer["id"]
        label = layer.get("name") or key
    elif target in GROUND_LAYERS:
        key, label = "ground:" + target, target
    else:
        raise ValueError(f"{target}: name a map-layer, or one of {', '.join(GROUND_LAYERS)}")
    pref = my_preference(call, m["lens"]) if m.get("lens") else None
    hidden = set(str((pref or {}).get("map.hide", "")).split())
    (hidden.add if hide else hidden.discard)(key)
    line = set_pref(call, m, "map.hide", " ".join(sorted(hidden)))
    return dict(lines=[line], saw=call.saw, text=("hidden for you: " if hide else "showing again for you: ") + label)


STYLES = ("day", "dusk", "night", "paper")


def w_style(call, a):
    m = the_map(call, a["kv"].get("map"))
    s = (a["target"] or a["words"]).strip().lower()
    if s not in STYLES:
        raise ValueError("map.style " + " | ".join(STYLES) + ": how your own map window looks")
    return dict(lines=[set_pref(call, m, "map.style", s)], saw=call.saw, text=f"your map looks like {s} now")


def w_show(call, a):
    m = the_map(call, a["kv"].get("map"))
    target = a["target"] or a["words"].strip()
    lat, lon, label = point_of(call, ground_getter(call, m), target)
    focus = f"{lat:.6f},{lon:.6f}@{datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S%f')}"
    return dict(lines=[set_pref(call, m, "map.focus", focus)], saw=call.saw, text=f"your map turns to {label}")


def w_cache(call, a):
    t = tiles()
    trim = num(a["kv"].get("trim"))
    if trim is not None:
        gone, total = t.trim(int(trim * 1e9))
        return dict(text=f"forgot {gone} tiles; {total / 1e6:.0f} MB kept")
    total, files = t.size()
    return dict(text=f"{total / 1e6:.1f} MB of ground kept on this machine ({files} files) · "
                     f"{t.http.fetched} fetched since the map module started",
                rows=[dict(bytes=total, files=files, fetched=t.http.fetched)])


WORDS = [
    ("map.tile", "see", "<z/x/y>", w_tile,
     "map.tile 14/2639/6379: one tile of the live ground, as a map window draws it (format agora-tile/1)."),
    ("map.find", "see", "<words> [near=lat,lon] [map=] [limit=8]", w_find,
     "map.find <words>: things, places, streets and corners near the map, then towns and addresses further away. "
     "Two streets joined by & find where they cross: map.find Seabright & Murray."),
    ("map.where", "see", "<thing|lat,lon> [map=]", w_where,
     "map.where <thing>: where it is, in words: the street and the nearest named place."),
    ("map.near", "see", "<thing|lat,lon|name> [within=300] [kind=] [map=]", w_near,
     "map.near <thing> within=300: placed things you can see near it, nearest first, with metres."),
    ("map.place", "see", "<thing|overture:id> [lat= lon=]", w_place,
     "map.place <building or thing>: its facts, which page it opens in, the things at it and the posts about it."),
    ("map.add", "do", "<place> kind=<kind> [facts…]", w_add,
     'map.add <place> kind=event title="Council night" start="Thu 6pm": puts something at a place: a building '
     "(overture:… with lat= lon=), a thing, a name on the map, or lat,lon. A building becomes a structure thing the "
     "first time something is put at it."),
    ("map.adopt", "do", "<overture:id> lat= lon= [name=]", w_adopt,
     "map.adopt overture:… lat= lon= name=\"Town hall\": makes a building a world thing (kind=structure), so it "
     "can be named, found, talked about and given a page."),
    ("map.path", "see", 'stops="a > b > c" [mode=walk|bike] [map=]', w_path,
     'map.path stops="Seabright Station > Java Junction": a street path as a reading (nothing is made).'),
    ("map.route", "do", '[<route>] name= stops="a > b > c" [mode=walk|bike] [map=]', w_route,
     'map.route name="Flyers north" stops="a > b > c": makes a route thing that keeps its street path, length and '
     "minutes. map.route <route> replans it (after its stops moved or changed). Undo takes it back."),
    ("map.layers", "see", "[<map>]", w_layers,
     "map.layers <map>: every layer of the map with the placed things its reading finds, as you may see them."),
    ("map.hide", "do", "<layer|" + "|".join(GROUND_LAYERS) + "> [map=]", lambda c, a: w_hide(c, a, True),
     "map.hide <layer>: hide a layer from your own map window only. map.unhide shows it again."),
    ("map.unhide", "do", "<layer|" + "|".join(GROUND_LAYERS) + "> [map=]", lambda c, a: w_hide(c, a, False),
     "map.unhide <layer>: show a layer you hid in your own map window."),
    ("map.style", "do", "<" + "|".join(STYLES) + "> [map=]", w_style,
     "map.style dusk: how your own map window looks (day, dusk, night, paper)."),
    ("map.show", "do", "<thing|name|lat,lon> [map=]", w_show,
     "map.show <thing>: turn your own map window to a thing or a place."),
    ("map.cache", "see", "[trim=<GB>]", w_cache,
     "map.cache: how much of the live ground is kept on this machine. map.cache trim=2 forgets the oldest tiles "
     "until 2 GB are left."),
]
BY_WORD = {w[0]: w for w in WORDS}


def answer(msg):
    call = Call(msg)
    try:
        word = BY_WORD[msg["word"]]
        result = word[3](call, msg.get("args") or {"target": "", "words": "", "kv": {}})
    except Exception as exc:          # every refusal is said, and the process carries on
        result = dict(refused=str(exc) or type(exc).__name__)
        if not isinstance(exc, ValueError):
            import traceback
            sys.stderr.write(traceback.format_exc())
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
            f = live.http.fetched if live else 0
            send(dict(t="status", use=msg.get("use"), doing=f"map words; {len(areas)} areas walked; {f} tiles fetched"))
        elif t == "off":
            return


if __name__ == "__main__":
    main()
