"""The ground a map stands on (format agora-ground/1): finding names, measuring, and walking its streets.

Pure functions over one parsed ground file, no world access. The map module (map.py) reads the file through the
kernel and calls these; tests call them directly. Coordinates inside the ground are integer decimetres east/north
of `frame.origin`; everything that leaves this file is lat/lon (WGS84 degrees) or metres.
"""
import heapq
import math
import re

WALK = {"major": 1.0, "street": 1.0, "service": 1.05, "walk": 0.95, "path": 0.97, "cycle": 1.0, "steps": 1.3}
BIKE = {"major": 1.1, "street": 1.0, "service": 1.05, "walk": 1.6, "path": 1.4, "cycle": 0.85}
SPEED = {"walk": 1.33, "bike": 4.5}          # metres a second: 4.8 km/h on foot, 16 km/h by bike
ABBREV = {"ave": "avenue", "av": "avenue", "st": "street", "dr": "drive", "rd": "road", "blvd": "boulevard",
          "ln": "lane", "ct": "court", "pl": "place", "hwy": "highway"}


class Ground:
    def __init__(self, doc):
        if doc.get("format") != "agora-ground/1":
            raise ValueError("not an agora-ground/1 file")
        self.doc = doc
        f = doc["frame"]
        self.lat0, self.lon0 = f["origin"]["lat"], f["origin"]["lon"]
        self.mlat, self.mlon = f["m_per_deg_lat"], f["m_per_deg_lon"]
        self._graphs = {}
        self._names = None

    # --- frames ---------------------------------------------------------------------------------------------
    def latlon(self, x, y):
        return round(self.lat0 + y / 10 / self.mlat, 7), round(self.lon0 + x / 10 / self.mlon, 7)

    def xy(self, lat, lon):
        return (lon - self.lon0) * self.mlon * 10, (lat - self.lat0) * self.mlat * 10

    def contains(self, lat, lon, margin_m=0):
        x, y = self.xy(lat, lon)
        x0, y0, x1, y1 = self.doc["bounds"]
        m = margin_m * 10
        return x0 - m <= x <= x1 + m and y0 - m <= y <= y1 + m

    @staticmethod
    def metres(a, b):
        """Distance in metres between two (lat, lon), on the sphere (good to centimetres at this size)."""
        la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
        h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
        return 2 * 6371008.8 * math.asin(math.sqrt(h))

    # --- names ----------------------------------------------------------------------------------------------
    def names(self):
        """Everything with a name in the ground: places (shops, parks, stops), streets, and building addresses."""
        if self._names is None:
            out = []
            for p in self.doc["pois"]:
                out.append(dict(name=p["n"], what=p["c"], osm=p["id"], at=(p["x"], p["y"]),
                                address=p.get("a", "")))
            for p in self.doc.get("props", []):
                if p.get("n"):
                    out.append(dict(name=p["n"], what=p["k"], osm=p["id"], at=(p["x"], p["y"])))
            streets = {}
            for r in self.doc["roads"]:
                if r.get("n"):
                    streets.setdefault(r["n"], []).append(r["p"])
            for name, runs in streets.items():
                pts = [(run[i], run[i + 1]) for run in runs for i in range(0, len(run), 2)]
                mid = pts[len(pts) // 2]
                out.append(dict(name=name, what="street", osm="street:" + name, at=mid, runs=runs))
            for b in self.doc["buildings"]:
                if b.get("a") or b.get("n"):
                    r = b["r"][0]
                    cx = sum(r[0::2]) / (len(r) // 2)
                    cy = sum(r[1::2]) / (len(r) // 2)
                    out.append(dict(name=b.get("n") or b["a"], what="building", osm=b["id"], at=(cx, cy),
                                    address=b.get("a", "")))
            self._names = out
        return self._names

    def find(self, text, limit=8):
        """Names that match the words of `text`, best first. 'Seabright & Murray' finds the corner; 'java' the cafe.
        Two street names joined by & / and / at find where they cross."""
        text = text.strip()
        if not text:
            return []
        corner = re.split(r"\s+(?:&|and|at|/|x)\s+", text, flags=re.I)
        if len(corner) == 2:
            hit = self.crossing(*corner)
            if hit:
                return [hit]
        words = [ABBREV.get(w, w) for w in re.findall(r"[a-z0-9']+", text.lower()) if w != "the"]
        scored = []
        for n in self.names():
            hay = (n["name"] + " " + n.get("address", "")).lower()
            hay_words = re.findall(r"[a-z0-9']+", hay)
            if not all(any(h.startswith(w) for h in hay_words) for w in words):
                continue
            score = 0
            if n["name"].lower() == text.lower():
                score -= 100
            if n["name"].lower().startswith(text.lower()):
                score -= 30
            score += {"street": 0, "building": 25}.get(n["what"], 5) + len(n["name"]) / 10
            scored.append((score, n))
        scored.sort(key=lambda s: s[0])
        out, seen = [], set()
        for _, n in scored:
            key = (n["name"], n["what"])
            if key in seen:
                continue
            seen.add(key)
            out.append(self.row(n))
            if len(out) >= limit:
                break
        return out

    def row(self, n):
        lat, lon = self.latlon(*n["at"])
        r = dict(name=n["name"], what=n["what"], osm=n["osm"], lat=lat, lon=lon)
        if n.get("address"):
            r["address"] = n["address"]
        return r

    def street_points(self, name):
        name = " ".join(ABBREV.get(w, w) for w in re.findall(r"[a-z0-9']+", name.lower()))
        hits = [n for n in self.names() if n["what"] == "street" and
                (n["name"].lower() == name or n["name"].lower().startswith(name + " ") or
                 n["name"].lower().split(" ")[0] == name.split(" ")[0] and len(name.split(" ")) == 1)]
        return hits

    def crossing(self, a, b):
        """Where two streets meet: the shared point of their lines (or the closest pair of points)."""
        sa, sb = self.street_points(a), self.street_points(b)
        if not sa or not sb:
            return None
        best = None
        for na in sa:
            pa = {(run[i], run[i + 1]) for run in na["runs"] for i in range(0, len(run), 2)}
            for nb in sb:
                for run in nb["runs"]:
                    for i in range(0, len(run), 2):
                        q = (run[i], run[i + 1])
                        if q in pa:
                            best = (0, q, na, nb)
                            break
                        if best is None or best[0] > 0:
                            d = min((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 for p in pa)
                            if best is None or d < best[0]:
                                best = (d, q, na, nb)
        if best is None or best[0] > 400 ** 2:      # streets that come no nearer than 40 m do not meet
            return None
        lat, lon = self.latlon(*best[1])
        return dict(name=best[2]["name"] + " & " + best[3]["name"], what="corner", osm="corner", lat=lat, lon=lon)

    # --- where is this --------------------------------------------------------------------------------------
    def nearest_street(self, lat, lon):
        x, y = self.xy(lat, lon)
        best = None
        for r in self.doc["roads"]:
            if not r.get("n") or r["c"] in ("path", "steps", "cycle"):
                continue
            p = r["p"]
            for i in range(0, len(p) - 2, 2):
                d = _seg_dist(x, y, p[i], p[i + 1], p[i + 2], p[i + 3])
                if best is None or d < best[0]:
                    best = (d, r["n"])
        return (best[1], best[0] / 10) if best else (None, None)

    def where(self, lat, lon):
        """A sentence a neighbour would say: the street, the nearest named place, and how far."""
        if not self.contains(lat, lon, 200):
            return "outside this map's ground"
        street, d = self.nearest_street(lat, lon)
        near = None
        for n in self.doc["pois"]:
            if n["c"].startswith("shop:") or n["c"] in ("bench", "waste_basket", "place") \
                    or not re.search(r"[A-Za-z]{2}", n["n"]):
                continue
            nlat, nlon = self.latlon(n["x"], n["y"])
            m = self.metres((lat, lon), (nlat, nlon))
            if near is None or m < near[0]:
                near = (m, n["n"])
        bits = []
        if street:
            bits.append(("on " if d < 15 else f"{round(d)} m from ") + street)
        if near:
            bits.append(("at " if near[0] < 20 else f"{round(near[0])} m from ") + near[1])
        return ", ".join(bits) or "on open ground"

    # --- routes ---------------------------------------------------------------------------------------------
    def graph(self, mode="walk"):
        if mode in self._graphs:
            return self._graphs[mode]
        cost = WALK if mode == "walk" else BIKE
        adj = {}
        for r in self.doc["roads"]:
            if r["c"] not in cost or r.get("pv"):
                continue
            k = cost[r["c"]]
            p = r["p"]
            pts = [(p[i], p[i + 1]) for i in range(0, len(p), 2)]
            for a, b in zip(pts, pts[1:]):
                d = math.hypot(a[0] - b[0], a[1] - b[1]) / 10
                adj.setdefault(a, []).append((b, d * k, d, r.get("n", "")))
                if mode == "walk" or not r.get("one"):
                    adj.setdefault(b, []).append((a, d * k, d, r.get("n", "")))
        self._graphs[mode] = adj
        return adj

    def snap(self, lat, lon, mode="walk"):
        """The nearest point of the network that is connected to most of it."""
        adj = self.graph(mode)
        x, y = self.xy(lat, lon)
        main = self._main(mode)
        best = min(main, key=lambda q: (q[0] - x) ** 2 + (q[1] - y) ** 2)
        return best, math.hypot(best[0] - x, best[1] - y) / 10

    def _main(self, mode):
        key = "main:" + mode
        if key not in self._graphs:
            adj = self.graph(mode)
            seen, biggest = set(), set()
            for start in adj:
                if start in seen:
                    continue
                comp, stack = {start}, [start]
                while stack:
                    a = stack.pop()
                    for b, *_ in adj.get(a, ()):
                        if b not in comp:
                            comp.add(b)
                            stack.append(b)
                seen |= comp
                if len(comp) > len(biggest):
                    biggest = comp
            self._graphs[key] = biggest
        return self._graphs[key]

    def route(self, stops, mode="walk"):
        """Stops are (lat, lon). Returns dict(path=[(lat, lon)...], metres, minutes, legs=[metres...], streets=[...])
        following the streets and paths, or raises ValueError when two stops are not connected."""
        if mode not in SPEED:
            raise ValueError("mode is walk or bike")
        if len(stops) < 2:
            raise ValueError("a route needs at least two stops")
        adj = self.graph(mode)
        path, legs, streets, total = [], [], [], 0.0
        for a, b in zip(stops, stops[1:]):
            sa, da = self.snap(*a, mode)
            sb, db = self.snap(*b, mode)
            nodes, metres, names = _astar(adj, sa, sb)
            if nodes is None:
                raise ValueError("no way through between two of the stops")
            leg = metres + da + db
            legs.append(round(leg))
            total += leg
            seg = [tuple(a)] + [self.latlon(*n) for n in nodes] + [tuple(b)]
            path += seg if not path else seg[1:]
            runs = []                               # (street, metres) along this leg
            for i, n in enumerate(names):
                if i + 1 >= len(nodes):
                    break
                (ax, ay), (bx, by) = nodes[i], nodes[i + 1]
                if not n:
                    # a sidewalk or crossing has no name of its own: it takes the street it runs beside
                    street, d = self.nearest_street(*self.latlon((ax + bx) / 2, (ay + by) / 2))
                    n = street if street and d is not None and d < 20 else ""
                m = math.hypot(bx - ax, by - ay) / 10
                if runs and runs[-1][0] == n:
                    runs[-1][1] += m
                else:
                    runs.append([n, m])
            # a few metres of a cross street at a corner is not a street you walk along
            for n, m in runs:
                if n and m >= 35 and (not streets or streets[-1] != n):
                    streets.append(n)
        return dict(path=[(round(la, 6), round(lo, 6)) for la, lo in path], metres=round(total),
                    minutes=max(1, round(total / SPEED[mode] / 60)), legs=legs, streets=streets)


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _astar(adj, start, goal):
    if start == goal:
        return [start], 0.0, []
    h = lambda q: math.hypot(q[0] - goal[0], q[1] - goal[1]) / 10 * 0.85
    best = {start: 0.0}
    came = {}
    heap = [(h(start), 0.0, start)]
    while heap:
        _, g, a = heapq.heappop(heap)
        if a == goal:
            break
        if g > best.get(a, 1e18):
            continue
        for b, w, d, name in adj.get(a, ()):
            ng = g + w
            if ng < best.get(b, 1e18):
                best[b] = ng
                came[b] = (a, d, name)
                heapq.heappush(heap, (ng + h(b), ng, b))
    if goal not in came:
        return None, 0, []
    nodes, metres, names = [goal], 0.0, []
    q = goal
    while q != start:
        a, d, name = came[q]
        metres += d
        names.append(name)
        nodes.append(a)
        q = a
    return nodes[::-1], metres, names[::-1]


def polyline(path):
    """(lat, lon) pairs -> the compact text a route keeps: 'lat,lon lat,lon ...' (6 decimals, ~10 cm)."""
    return " ".join(f"{la:.6f},{lo:.6f}" for la, lo in path)


def parse_points(text):
    out = []
    for bit in str(text).split():
        la, lo = bit.split(",")
        out.append((float(la), float(lo)))
    return out
