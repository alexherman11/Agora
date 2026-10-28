"""Live ground for the map: vector tiles fetched on demand, kept on disk, and cut into chunks the window can draw.

Two sources, both open data, both read without keys:
  base       OpenFreeMap (OpenMapTiles schema, from OpenStreetMap): water, land, roads, names, places. z0..14.
             https://openfreemap.org; tiles are plain URLs named by a TileJSON.
  buildings  Overture Maps buildings (OpenStreetMap plus machine-traced footprints, so far more houses), one PMTiles
             archive read by HTTP range requests: only the bytes of the tiles asked for. z5..14.
Every tile fetched is kept under <home>/cache/, so a place seen once draws again without the network, and nothing
is fetched that nobody looked at. `Tiles.size()` and `Tiles.trim()` keep the cache under a limit.

A chunk (format agora-tile/1) is one tile's drawing data, in tile units (0..4096, y downward), clipped exactly to the
tile so neighbours meet without overlap:
  a  areas      [[class, [ring, hole, ...], name?], ...]     rings as flat [x0, y0, x1, y1, ...]
  l  lines      [[class, points, flags], ...]                roads, rail, rivers; flags: b bridge, t tunnel, o oneway
  s  names      [[name, class, points], ...]                 street names along their lines
  b  buildings  [[id, height, min height, class, rings, name, extra], ...]   heights in true metres
  p  points     [[name, class, subclass, rank, x, y], ...]   places, shops, parks, peaks
Area and line classes are the map's own small vocabulary (see AREA_* and ROAD_* below), so another source can be cut
into the same chunk.
"""
import gzip
import http.client
import json
import math
import os
import re
import struct
import threading
import time
import urllib.parse
from pathlib import Path

import mvt

E = 4096                                     # chunk units per tile side
UA = "Agora-map/0.2 (a personal desktop map; tiles cached locally)"
OFM_TILEJSON = "https://tiles.openfreemap.org/planet"
OVERTURE = "https://overturemaps-extras-us-west-2.s3.amazonaws.com/tiles/2026-10-21.0/buildings.pmtiles"
R = 6378137.0
WORLD = 2 * math.pi * R


# --- tile maths ---------------------------------------------------------------------------------------------------
def lonlat_to_tile(lon, lat, z):
    n = 1 << z
    x = (lon + 180.0) / 360.0 * n
    lr = math.radians(max(-85.05112878, min(85.05112878, lat)))
    y = (1.0 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2.0 * n
    return x, y


def tile_to_lonlat(x, y, z):
    n = 1 << z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


def tile_id(z, x, y):
    """PMTiles v3 tile id: tiles of lower zooms first, then the Hilbert curve index within the zoom."""
    acc = ((1 << (2 * z)) - 1) // 3
    n = 1 << z
    d, s, tx, ty = 0, n >> 1, x, y
    while s > 0:
        rx = 1 if tx & s else 0
        ry = 1 if ty & s else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                tx, ty = n - 1 - tx, n - 1 - ty
            tx, ty = ty, tx
        s >>= 1
    return acc + d


# --- fetching -----------------------------------------------------------------------------------------------------
class Http:
    """One kept-alive HTTPS connection per host and thread; a few requests at once at most."""

    def __init__(self, at_once=6):
        self.local = threading.local()
        self.gate = threading.BoundedSemaphore(at_once)
        self.fetched = 0
        self.bytes = 0

    def get(self, url, rng=None, timeout=8):
        u = urllib.parse.urlsplit(url)
        path = u.path + ("?" + u.query if u.query else "")
        headers = {"User-Agent": UA, "Accept-Encoding": "gzip"}
        if rng:
            headers["Range"] = "bytes=%d-%d" % rng
        with self.gate:
            for attempt in range(3):
                conns = getattr(self.local, "conns", None)
                if conns is None:
                    conns = self.local.conns = {}
                c = conns.get(u.netloc)
                if c is None:
                    c = conns[u.netloc] = http.client.HTTPSConnection(u.netloc, timeout=timeout)
                try:
                    c.request("GET", path, headers=headers)
                    r = c.getresponse()
                    body = r.read()
                except (http.client.HTTPException, OSError):
                    c.close()
                    conns.pop(u.netloc, None)
                    if attempt == 2:
                        raise
                    time.sleep(0.3 * (attempt + 1))
                    continue
                if r.status in (500, 502, 503, 504) and attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                if r.getheader("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                self.fetched += 1
                self.bytes += len(body)
                return r.status, body
        raise OSError("unreachable")


def ungzip(b):
    return gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b


class PMTiles:
    """A PMTiles v3 archive over HTTP range requests. Directories are kept in memory and on disk."""

    def __init__(self, url, http, cache):
        self.url, self.http, self.cache = url, http, Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.dirs = {}
        self.lock = threading.Lock()
        self.head = None

    def _range(self, off, length, keep=None):
        if keep:
            p = self.cache / keep
            if p.exists():
                return p.read_bytes()
        status, body = self.http.get(self.url, (off, off + length - 1))
        if status not in (200, 206):
            raise OSError("buildings archive answered %d" % status)
        if keep:
            tmp = self.cache / (keep + ".%d.tmp" % threading.get_ident())
            tmp.write_bytes(body)
            os.replace(tmp, self.cache / keep)
        return body

    def header(self):
        if self.head is None:
            h = self._range(0, 127, keep="header.bin")
            if h[:7] != b"PMTiles" or h[7] != 3:
                raise ValueError("not a PMTiles v3 archive")
            f = struct.unpack("<11Q", h[8:96])
            self.head = dict(root=(f[0], f[1]), leaves=f[4], data=f[6], icomp=h[97], tcomp=h[98],
                             minz=h[100], maxz=h[101])
        return self.head

    def _dir(self, off, length):
        key = (off, length)
        d = self.dirs.get(key)
        if d is None:
            raw = self._range(off, length, keep="dir-%d-%d.bin" % key)
            raw = ungzip(raw) if self.header()["icomp"] == 2 else raw
            d = self.dirs[key] = _read_dir(raw)
            if len(self.dirs) > 400:
                self.dirs.pop(next(iter(self.dirs)))
        return d

    def get(self, z, x, y):
        h = self.header()
        if z < h["minz"] or z > h["maxz"]:
            return None
        tid = tile_id(z, x, y)
        off, length = h["root"]
        for _ in range(4):
            ids, runs, lens, offs = self._dir(off, length)
            i = _bisect(ids, tid)
            if i < 0:
                return None
            if runs[i] == 0:                               # a leaf directory
                off, length = h["leaves"] + offs[i], lens[i]
                continue
            if tid < ids[i] + runs[i]:
                _, body = self.http.get(self.url, (h["data"] + offs[i], h["data"] + offs[i] + lens[i] - 1))
                return ungzip(body) if h["tcomp"] == 2 else body
            return None
        return None


def _read_dir(b):
    i = 0

    def v():
        nonlocal i
        shift = res = 0
        while True:
            c = b[i]
            i += 1
            res |= (c & 0x7F) << shift
            if c < 0x80:
                return res
            shift += 7
    n = v()
    ids, last = [], 0
    for _ in range(n):
        last += v()
        ids.append(last)
    runs = [v() for _ in range(n)]
    lens = [v() for _ in range(n)]
    offs = []
    for k in range(n):
        o = v()
        offs.append(offs[k - 1] + lens[k - 1] if o == 0 and k > 0 else o - 1)
    return ids, runs, lens, offs


def _bisect(ids, t):
    lo, hi = 0, len(ids) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if ids[mid] < t:
            lo = mid + 1
        elif ids[mid] > t:
            hi = mid - 1
        else:
            return mid
    return hi


class Tiles:
    """The live ground: raw tiles from both sources on disk, and chunks made from them in memory."""

    def __init__(self, home, offline=False):
        self.home = Path(home)
        self.cache = self.home / "cache"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.http = Http()
        self.offline = offline
        self.buildings = PMTiles(OVERTURE, self.http, self.cache / "overture")
        self.chunks = {}
        self.lock = threading.Lock()
        self.busy = {}
        self.tilejson = None
        self.errors = []

    # raw tiles ------------------------------------------------------------------------------------------------
    def _base_url(self):
        if self.tilejson and time.time() - self.tilejson[0] < 86400:
            return self.tilejson[1]
        p = self.cache / "openfreemap.json"
        if p.exists() and time.time() - p.stat().st_mtime < 86400:
            tj = json.loads(p.read_text("utf-8"))
        else:
            status, body = self.http.get(OFM_TILEJSON)
            if status != 200:
                raise OSError("OpenFreeMap answered %d" % status)
            tj = json.loads(body)
            p.write_text(json.dumps(tj), "utf-8")
        self.tilejson = (time.time(), tj["tiles"][0])
        return self.tilejson[1]

    def raw(self, source, z, x, y):
        """The tile's protobuf bytes (b'' when the source has no tile there), from disk or the network."""
        p = self.cache / source / str(z) / str(x) / ("%d.pbf" % y)
        if p.exists():
            return p.read_bytes()
        if self.offline:
            return b""
        if source == "base":
            if z > 14:
                return b""
            status, body = self.http.get(self._base_url().format(z=z, x=x, y=y))
            if status == 404 or status == 204:
                body = b""
            elif status != 200:
                raise OSError("OpenFreeMap answered %d for %d/%d/%d" % (status, z, x, y))
            body = ungzip(body)
        else:
            body = self.buildings.get(z, x, y) or b""
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".%d.tmp" % threading.get_ident())
        tmp.write_bytes(body)
        os.replace(tmp, p)
        return body

    # chunks ---------------------------------------------------------------------------------------------------
    def chunk(self, z, x, y):
        """The tile's chunk as compact JSON text (made once, then kept in memory, and on disk)."""
        key = (z, x, y)
        with self.lock:
            hit = self.chunks.get(key)
            if hit is not None:
                self.chunks[key] = self.chunks.pop(key)   # most recently used last
                return hit
            ev = self.busy.get(key)
            mine = ev is None
            if mine:
                ev = self.busy[key] = threading.Event()
        if not mine:
            ev.wait(20)
            with self.lock:
                if key in self.chunks:
                    return self.chunks[key]
            raise OSError("tile %d/%d/%d did not arrive" % key)
        try:
            disk = self.cache / "chunks" / CHUNK_VERSION / str(z) / str(x) / ("%d.json" % y)
            if disk.exists():
                text = disk.read_text("utf-8")
            else:
                base = self.raw("base", z, x, y) if z <= 14 else b""
                bld = self.raw("overture", z, x, y) if 13 <= z <= 14 else b""
                text = json.dumps(cut(z, x, y, base, bld), separators=(",", ":"))
                disk.parent.mkdir(parents=True, exist_ok=True)
                tmp = disk.with_suffix(".%d.tmp" % threading.get_ident())
                tmp.write_text(text, "utf-8")
                os.replace(tmp, disk)
            with self.lock:
                self.chunks[key] = text
                while len(self.chunks) > 300:
                    self.chunks.pop(next(iter(self.chunks)))
            return text
        finally:
            with self.lock:
                self.busy.pop(key, None)
            ev.set()

    def size(self):
        total = files = 0
        for root, _, names in os.walk(self.cache):
            for n in names:
                try:
                    total += os.path.getsize(os.path.join(root, n))
                    files += 1
                except OSError:
                    pass
        return total, files

    def trim(self, limit_bytes):
        """Forget the least recently used cached tiles until the cache is under the limit."""
        entries = []
        for root, _, names in os.walk(self.cache):
            for n in names:
                if n.endswith((".pbf", ".json")) and "chunks" in root or n.endswith(".pbf"):
                    p = os.path.join(root, n)
                    try:
                        st = os.stat(p)
                        entries.append((st.st_atime, st.st_size, p))
                    except OSError:
                        pass
        total = sum(e[1] for e in entries)
        entries.sort()
        gone = 0
        for _, size, p in entries:
            if total <= limit_bytes:
                break
            try:
                os.remove(p)
                total -= size
                gone += 1
            except OSError:
                pass
        return gone, total


CHUNK_VERSION = "c2"

# --- cutting a tile into a chunk ----------------------------------------------------------------------------------
WATER = {"ocean": "sea", "swimming_pool": "pool"}
COVER = {"grass": "green", "wood": "wood", "forest": "wood", "wetland": "wetland", "sand": "beach", "farmland": "farm",
         "rock": "rock", "ice": "ice", "scrub": "scrub"}
COVER_SUB = {"beach": "beach", "park": "park", "garden": "park", "golf_course": "green", "meadow": "green",
             "allotments": "farm", "orchard": "farm", "vineyard": "farm", "dune": "beach", "bare_rock": "rock",
             "scree": "rock", "heath": "scrub", "scrub": "scrub", "recreation_ground": "green",
             "village_green": "green", "grass": "green", "playground": "play"}
USE = {"residential": "residential", "suburb": "residential", "neighbourhood": "residential", "quarter": "residential",
       "commercial": "commercial", "retail": "commercial", "industrial": "industrial", "railway": "industrial",
       "military": "industrial", "garages": "parking", "school": "school", "university": "school",
       "college": "school", "kindergarten": "school", "library": "school", "hospital": "hospital",
       "cemetery": "cemetery", "stadium": "pitch", "pitch": "pitch", "playground": "play", "zoo": "park",
       "theme_park": "park", "bus_station": "parking", "dam": "industrial"}
# areas are written lowest first; a later one paints over an earlier one
AREA_ORDER = ["residential", "commercial", "industrial", "parking", "school", "hospital", "cemetery", "farm", "scrub",
              "rock", "ice", "green", "wood", "park", "wetland", "beach", "pitch", "play", "airport", "water", "sea",
              "pool"]
ROAD = {"motorway": "motorway", "trunk": "motorway", "primary": "major", "secondary": "major", "tertiary": "major",
        "minor": "street", "service": "service", "track": "path", "path": "path", "raceway": "service",
        "busway": "street", "bus_guideway": "street", "pier": "walk", "ferry": "ferry"}
PATH_SUB = {"footway": "walk", "pedestrian": "walk", "cycleway": "cycle", "steps": "steps", "bridleway": "path",
            "corridor": "walk", "platform": "walk"}


def clip_ring(ring, lo=0, hi=E):
    """Sutherland-Hodgman against the tile box; ring is a flat list, closed implicitly."""
    pts = [(ring[i], ring[i + 1]) for i in range(0, len(ring), 2)]
    if all(lo <= x <= hi and lo <= y <= hi for x, y in pts):
        return ring
    for axis, bound, keep_low in ((0, lo, False), (0, hi, True), (1, lo, False), (1, hi, True)):
        if not pts:
            break
        inside = (lambda p: p[axis] <= bound) if keep_low else (lambda p: p[axis] >= bound)
        out = []
        prev = pts[-1]
        pin = inside(prev)
        for cur in pts:
            cin = inside(cur)
            if cin != pin:
                t = (bound - prev[axis]) / (cur[axis] - prev[axis])
                q = [0, 0]
                q[axis] = bound
                q[1 - axis] = prev[1 - axis] + (cur[1 - axis] - prev[1 - axis]) * t
                out.append((q[0], q[1]))
            if cin:
                out.append(cur)
            prev, pin = cur, cin
        pts = out
    if len(pts) < 3:
        return None
    flat = []
    for x, y in pts:
        rx, ry = round(x), round(y)
        if len(flat) >= 2 and flat[-2] == rx and flat[-1] == ry:
            continue
        flat += [rx, ry]
    if len(flat) >= 4 and flat[0] == flat[-2] and flat[1] == flat[-1]:
        flat = flat[:-2]
    return flat if len(flat) >= 6 else None


def clip_line(line, lo=0, hi=E):
    """Liang-Barsky per segment; returns the runs that stay inside the tile box."""
    runs, cur = [], []
    for i in range(0, len(line) - 2, 2):
        x0, y0, x1, y1 = line[i], line[i + 1], line[i + 2], line[i + 3]
        t0, t1, dx, dy = 0.0, 1.0, x1 - x0, y1 - y0
        ok = True
        for p, q in ((-dx, x0 - lo), (dx, hi - x0), (-dy, y0 - lo), (dy, hi - y0)):
            if p == 0:
                if q < 0:
                    ok = False
                    break
            else:
                r = q / p
                if p < 0:
                    if r > t1:
                        ok = False
                        break
                    t0 = max(t0, r)
                else:
                    if r < t0:
                        ok = False
                        break
                    t1 = min(t1, r)
        if not ok:
            if len(cur) >= 4:
                runs.append(cur)
            cur = []
            continue
        ax, ay = round(x0 + dx * t0), round(y0 + dy * t0)
        bx, by = round(x0 + dx * t1), round(y0 + dy * t1)
        if cur and (cur[-2] != ax or cur[-1] != ay):
            if len(cur) >= 4:
                runs.append(cur)
            cur = []
        if not cur:
            cur = [ax, ay]
        if bx != cur[-2] or by != cur[-1]:
            cur += [bx, by]
        if t1 < 1.0:
            if len(cur) >= 4:
                runs.append(cur)
            cur = []
    if len(cur) >= 4:
        runs.append(cur)
    return runs


def _scale(geom, k, gtype):
    if k == 1:
        return geom
    if gtype == 1:
        return [(x * k, y * k) for x, y in geom]
    if gtype == 2:
        return [[v * k for v in part] for part in geom]
    return [[[v * k for v in ring] for ring in poly] for poly in geom]


def _height(p):
    h = p.get("height") or p.get("render_height")
    if isinstance(h, (int, float)) and h > 0:
        return float(h)
    f = p.get("num_floors")
    if isinstance(f, (int, float)) and f > 0:
        return f * 3.1 + 1.0
    c = str(p.get("class") or p.get("subtype") or "")
    return {"house": 6.5, "detached": 6.5, "semidetached_house": 7, "residential": 7, "apartments": 12,
            "terrace": 8, "garage": 3, "garages": 3, "shed": 2.6, "carport": 2.6, "hut": 3, "commercial": 8,
            "retail": 7, "office": 12, "industrial": 9, "warehouse": 9, "school": 8, "church": 12,
            "cathedral": 22, "civic": 10, "government": 10, "hospital": 15, "hotel": 14, "university": 12,
            "train_station": 9, "stadium": 16, "parking": 8, "barn": 6, "greenhouse": 4,
            "transportation": 6}.get(c, 6.0)


def _src(p):
    """Where a building's shape came from, and its OpenStreetMap id when it has one."""
    src = str(p.get("@geometry_source") or "")
    osm = ""
    s = p.get("sources")
    if isinstance(s, str) and "record_id" in s:
        m = re.search(r'"record_id"\s*:\s*"([nwr])(\d+)', s)
        if m:
            osm = {"n": "node", "w": "way", "r": "relation"}[m.group(1)] + "/" + m.group(2)
    return src, osm


def cut(z, x, y, base, bld):
    """One tile's chunk from its base and buildings protobufs."""
    out = dict(f="agora-tile/1", z=z, x=x, y=y, e=E, a=[], l=[], s=[], b=[], p=[])
    areas = {k: [] for k in AREA_ORDER}
    if base:
        layers = mvt.decode(base)
        for name, (extent, feats) in layers.items():
            k = E / extent
            for gtype, p, g in feats:
                g = _scale(g, k, gtype)
                cls = None
                if name == "water" and gtype == 3:
                    if p.get("intermittent") == 1:
                        continue
                    cls = WATER.get(p.get("class"), "water")
                elif name == "landcover" and gtype == 3:
                    cls = COVER_SUB.get(p.get("subclass")) or COVER.get(p.get("class"))
                elif name == "landuse" and gtype == 3:
                    cls = USE.get(p.get("class"))
                elif name == "park" and gtype == 3:
                    cls = "park"
                elif name == "aeroway" and gtype == 3:
                    cls = "airport" if p.get("class") in ("aerodrome",) else ("parking" if p.get("class") == "apron" else None)
                if cls and gtype == 3:
                    nm = p.get("name") if name in ("park", "water", "landuse") else None
                    for poly in g:
                        rings = [r for r in (clip_ring(ring) for ring in poly) if r]
                        if rings and len(rings[0]) >= 6:
                            areas[cls].append((rings, nm) if nm else rings)
                    continue
                if name == "transportation" and gtype == 2:
                    c = p.get("class")
                    if c in ("rail", "transit"):
                        cls = "rail" if p.get("subclass") not in ("subway",) or p.get("brunnel") != "tunnel" else None
                    elif c == "path":
                        cls = PATH_SUB.get(p.get("subclass"), "path")
                    else:
                        cls = ROAD.get(c)
                    if not cls:
                        continue
                    flags = ""
                    if p.get("brunnel") == "bridge":
                        flags += "b"
                    if p.get("brunnel") == "tunnel":
                        flags += "t"
                    if p.get("oneway") == 1:
                        flags += "o"
                    if p.get("access") == "no" or p.get("foot") == "no":
                        flags += "p"
                    if p.get("ramp") == 1:
                        flags += "r"
                    for part in g:
                        for run in clip_line(part):
                            out["l"].append([cls, run, flags])
                elif name == "transportation" and gtype == 3 and p.get("class") == "pier":
                    for poly in g:
                        rings = [r for r in (clip_ring(ring) for ring in poly) if r]
                        if rings:
                            areas["parking"].append(rings)
                elif name == "waterway" and gtype == 2:
                    c = p.get("class")
                    cls = "river" if c in ("river", "canal") else "stream"
                    if p.get("brunnel") == "tunnel":
                        continue
                    for part in g:
                        for run in clip_line(part):
                            out["l"].append([cls, run, ""])
                elif name == "aeroway" and gtype == 2 and p.get("class") in ("runway", "taxiway"):
                    for part in g:
                        for run in clip_line(part):
                            out["l"].append(["runway" if p.get("class") == "runway" else "taxiway", run, ""])
                elif name == "transportation_name" and gtype == 2 and p.get("name"):
                    c = p.get("class")
                    cls = ROAD.get(c) or (PATH_SUB.get(p.get("subclass"), "path") if c == "path" else "street")
                    for part in g:
                        for run in clip_line(part):
                            out["s"].append([p["name"], cls, run])
                elif gtype == 1 and name in ("place", "poi", "water_name", "mountain_peak", "aerodrome_label",
                                             "housenumber"):
                    for px, py in g:
                        if not (0 <= px < E and 0 <= py < E):
                            continue
                        px, py = round(px), round(py)
                        if name == "housenumber":
                            out.setdefault("h", []).append([str(p.get("housenumber", "")), px, py])
                            continue
                        n = p.get("name") or p.get("name_en") or ""
                        if name == "mountain_peak" and p.get("ele"):
                            n = (n + " · " if n else "") + "%d m" % p["ele"]
                        if not n:
                            continue
                        cls = {"place": "place", "water_name": "water", "mountain_peak": "peak",
                               "aerodrome_label": "airport"}.get(name, "poi")
                        sub = str(p.get("class") or "") if name != "poi" else str(p.get("subclass") or p.get("class") or "")
                        if name == "poi":
                            cls = str(p.get("class") or "poi")
                        rank = p.get("rank") or p.get("capital") or 0
                        out["p"].append([n, cls, sub, rank if isinstance(rank, int) else 0, px, py])
        # OpenStreetMap buildings from the base, used only when the buildings archive had nothing here
        if not bld and "building" in layers and z >= 13:
            extent, feats = layers["building"]
            k = E / extent
            for i, (gtype, p, g) in enumerate(feats):
                if gtype != 3 or p.get("hide_3d"):
                    continue
                for poly in _scale(g, k, 3):
                    rings = [r for r in (clip_ring(ring) for ring in poly) if r]
                    if rings:
                        out["b"].append(["osm-%d-%d-%d-%d" % (z, x, y, i), round(_height(p), 1),
                                         round(float(p.get("render_min_height") or 0), 1), "", rings, "", {}])
    out["a"] = [[cls, a[0], a[1]] if isinstance(a, tuple) else [cls, a] for cls in AREA_ORDER for a in areas[cls]]
    if bld:
        layers = mvt.decode(bld)
        parted = set()
        for lname in ("building_part", "building"):
            if lname not in layers:
                continue
            extent, feats = layers[lname]
            k = E / extent
            for gtype, p, g in feats:
                if gtype != 3 or p.get("is_underground"):
                    continue
                bid = str(p.get("building_id") if lname == "building_part" else p.get("id") or "")
                if lname == "building_part":
                    parted.add(bid)
                elif bid in parted:
                    continue                      # its parts are drawn instead of its shell
                src, osm = _src(p)
                extra = {}
                if src:
                    extra["src"] = src
                if osm:
                    extra["osm"] = osm
                for key in ("num_floors", "roof_shape", "roof_color", "facade_color", "subtype"):
                    if p.get(key) not in (None, ""):
                        extra[key] = p[key]
                if lname == "building_part":
                    extra["part"] = 1
                name = p.get("@name") or ""
                cls = str(p.get("class") or p.get("subtype") or "")
                for poly in _scale(g, k, 3):
                    rings = [r for r in (clip_ring(ring) for ring in poly) if r]
                    if rings:
                        out["b"].append([bid, round(_height(p), 1), round(float(p.get("min_height") or 0), 1), cls,
                                         rings, name, extra])
    # house numbers to the building they stand in (the base's number points)
    hn = out.pop("h", [])
    if hn and out["b"]:
        grid = {}
        for bi, b in enumerate(out["b"]):
            r = b[4][0]
            xs, ys = r[0::2], r[1::2]
            for gx in range(int(min(xs)) // 128, int(max(xs)) // 128 + 1):
                for gy in range(int(min(ys)) // 128, int(max(ys)) // 128 + 1):
                    grid.setdefault((gx, gy), []).append(bi)
        for num, px, py in hn:
            for bi in grid.get((px // 128, py // 128), ()):
                if _inside(px, py, out["b"][bi][4][0]):
                    out["b"][bi][6].setdefault("number", num)
                    break
    return out


def _inside(px, py, ring):
    inside = False
    n = len(ring) // 2
    j = n - 1
    for i in range(n):
        xi, yi, xj, yj = ring[2 * i], ring[2 * i + 1], ring[2 * j], ring[2 * j + 1]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi:
            inside = not inside
        j = i
    return inside


# --- a ground (agora-ground/1, ground.py) from the chunks around a place, for finding, where and routes -------------
GROUND_ROAD = {"motorway": None, "major": "major", "street": "street", "service": "service", "walk": "walk",
               "path": "path", "cycle": "cycle", "steps": "steps"}


def ground_doc(tiles, lat, lon, radius_m, z=14):
    """An agora-ground/1 document over the z14 tiles within radius_m of (lat, lon), in decimetres around it."""
    mlat = 110574.0 + 1110.0 * math.sin(math.radians(lat)) ** 2      # metres a degree, near enough at this size
    mlon = 111320.0 * math.cos(math.radians(lat))
    dlat, dlon = radius_m / mlat, radius_m / mlon
    x0, y0 = lonlat_to_tile(lon - dlon, lat + dlat, z)
    x1, y1 = lonlat_to_tile(lon + dlon, lat - dlat, z)
    xs, ys = range(int(x0), int(x1) + 1), range(int(y0), int(y1) + 1)
    if len(xs) * len(ys) > 144:
        raise ValueError("that is too large an area to walk at once (%d tiles)" % (len(xs) * len(ys)))
    doc = dict(format="agora-ground/1", name="live", frame=dict(origin=dict(lat=lat, lon=lon), m_per_deg_lat=mlat,
                                                                 m_per_deg_lon=mlon),
               bounds=[-radius_m * 10, -radius_m * 10, radius_m * 10, radius_m * 10],
               buildings=[], roads=[], pois=[], props=[], areas=[], rail=[], streams=[])
    from concurrent.futures import ThreadPoolExecutor
    keys = [(tx, ty) for tx in xs for ty in ys]
    with ThreadPoolExecutor(6) as pool:
        chunks = list(pool.map(lambda k: json.loads(tiles.chunk(z, k[0], k[1])), keys))
    n = 1 << z
    for (tx, ty), c in zip(keys, chunks):
        def dm(px, py, tx=tx, ty=ty):
            lo = (tx + px / E) / n * 360.0 - 180.0
            la = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ty + py / E) / n))))
            return round((lo - lon) * mlon * 10), round((la - lat) * mlat * 10)

        def flat(run):
            o = []
            for i in range(0, len(run), 2):
                o += dm(run[i], run[i + 1])
            return o
        for i, (cls, run, flags) in enumerate(c["l"]):
            g = GROUND_ROAD.get(cls)
            if g:
                r = dict(id="t%d.%d.%d" % (tx, ty, i), c=g, p=flat(run))
                if "o" in flags:
                    r["one"] = 1
                if "p" in flags:
                    r["pv"] = 1
                if "b" in flags or "t" in flags:
                    r["br"] = 1
                doc["roads"].append(r)
        for i, (name, cls, run) in enumerate(c["s"]):
            doc["roads"].append(dict(id="n%d.%d.%d" % (tx, ty, i), c="name", n=name, p=flat(run)))
        for name, cls, sub, rank, px, py in c["p"]:
            if cls == "place" and sub in ("city", "town", "village", "suburb", "neighbourhood", "hamlet", "quarter"):
                what = "place"
            else:
                what = sub or cls
            x, y = dm(px, py)
            doc["pois"].append(dict(id="p%d.%d.%d.%d" % (tx, ty, px, py), n=name, c=what, x=x, y=y))
        for b in c["b"]:
            if b[5] or b[6].get("number"):
                doc["buildings"].append(dict(id=b[0], n=b[5], a=b[6].get("number", ""), h=b[1], k=b[3],
                                             r=[flat(b[4][0])]))
    node_roads(doc["roads"])
    return doc


def node_roads(roads, snap=20, cell=400):
    """Vector tiles keep no topology: two streets that cross may share no point once simplified, a sidewalk may stop
    a metre short of the street, and a line cut at a tile edge may not meet its neighbour exactly. Make the network
    walkable again: split lines where they cross at grade (not bridges or tunnels), and snap each loose end onto the
    nearest other line within `snap` decimetres. Coordinates are integer decimetres; inserted points are rounded the
    same way in both lines, so they become shared nodes."""
    walk = [r for r in roads if r.get("c") != "name" and len(r["p"]) >= 4]
    grid = {}
    for ri, r in enumerate(walk):
        p = r["p"]
        for si in range(0, len(p) - 2, 2):
            ax, ay, bx, by = p[si], p[si + 1], p[si + 2], p[si + 3]
            for gx in range((min(ax, bx) - snap) // cell, (max(ax, bx) + snap) // cell + 1):
                for gy in range((min(ay, by) - snap) // cell, (max(ay, by) + snap) // cell + 1):
                    grid.setdefault((gx, gy), []).append((ri, si // 2))
    inserts = {}                                       # ri -> [(segment, t, x, y)]
    moves = {}                                         # (ri, vertex index) -> (x, y)
    seen = set()

    def seg(ri, s):
        p = walk[ri]["p"]
        return p[2 * s], p[2 * s + 1], p[2 * s + 2], p[2 * s + 3]
    for items in grid.values():
        n = len(items)
        for i in range(n):
            ri, si = items[i]
            ax, ay, bx, by = seg(ri, si)
            for j in range(i + 1, n):
                rj, sj = items[j]
                if ri == rj or (ri, si, rj, sj) in seen:
                    continue
                seen.add((ri, si, rj, sj))
                if walk[ri].get("br") or walk[rj].get("br"):
                    continue
                cx, cy, dx, dy = seg(rj, sj)
                if max(ax, bx) < min(cx, dx) or max(cx, dx) < min(ax, bx) or max(ay, by) < min(cy, dy) or max(cy, dy) < min(ay, by):
                    continue
                d = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)
                if d == 0:
                    continue
                t = ((cx - ax) * (dy - cy) - (cy - ay) * (dx - cx)) / d
                u = ((cx - ax) * (by - ay) - (cy - ay) * (bx - ax)) / d
                if 0 < t < 1 and 0 < u < 1:
                    x, y = round(ax + t * (bx - ax)), round(ay + t * (by - ay))
                    inserts.setdefault(ri, []).append((si, t, x, y))
                    inserts.setdefault(rj, []).append((sj, u, x, y))
    # loose ends onto the nearest other line
    for ri, r in enumerate(walk):
        p = r["p"]
        for vi in (0, len(p) // 2 - 1):
            x, y = p[2 * vi], p[2 * vi + 1]
            best = None
            for rj, sj in grid.get((x // cell, y // cell), ()):
                if rj == ri:
                    continue
                cx, cy, dx, dy = seg(rj, sj)
                L = (dx - cx) ** 2 + (dy - cy) ** 2
                t = 0 if L == 0 else max(0.0, min(1.0, ((x - cx) * (dx - cx) + (y - cy) * (dy - cy)) / L))
                px, py = cx + t * (dx - cx), cy + t * (dy - cy)
                dd = (px - x) ** 2 + (py - y) ** 2
                if dd <= snap * snap and (best is None or dd < best[0]):
                    best = (dd, rj, sj, t, round(px), round(py))
            if best and best[0] > 0:
                _, rj, sj, t, px, py = best
                moves[(ri, vi)] = (px, py)
                if 0 < t < 1:
                    inserts.setdefault(rj, []).append((sj, t, px, py))
    for ri, r in enumerate(walk):
        p = r["p"]
        add = sorted(inserts.get(ri, ()))
        if not add and not any((ri, vi) in moves for vi in (0, len(p) // 2 - 1)):
            continue
        out, k = [], 0
        for si in range(len(p) // 2):
            x, y = moves.get((ri, si), (p[2 * si], p[2 * si + 1]))
            if not out or out[-2:] != [x, y]:
                out += [x, y]
            while k < len(add) and add[k][0] == si:
                _, _, ix, iy = add[k]
                if out[-2:] != [ix, iy]:
                    out += [ix, iy]
                k += 1
        r["p"] = out
