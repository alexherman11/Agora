"""Raw Overpass extracts -> seabright-ground.json, the ground a map draws and routes on (format agora-ground/1).

The ground is a file the world holds (a `file` thing named in a `map` thing), so a community swaps it without code.
It is a derived database of OpenStreetMap data (ODbL 1.0, (c) OpenStreetMap contributors), and says so inside.

Coordinates: a local flat frame around `origin`, x east and y north, in DECIMETRES as integers, as flat arrays
[x, y, x, y, ...]. lat = origin.lat + y/10 / m_per_deg_lat; lon = origin.lon + x/10 / m_per_deg_lon (both in `frame`).
At this size (2 km) the flat frame is off by well under a centimetre. Every feature keeps its OSM id ("way/123").

  python research/map-lab/seabright/build_ground.py     -> seabright-ground.json, and prints the counts
"""
import collections
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW, ACQ = HERE / "extract" / "osm-seabright.json", HERE / "extract" / "acquisition.json"
COAST, ACQ_COAST = HERE / "extract" / "osm-seabright-coast.json", HERE / "extract" / "acquisition-coast.json"
OUT = HERE / "seabright-ground.json"

SOUTH, WEST, NORTH, EAST = 36.9590, -122.0230, 36.9800, -121.9990
ORIGIN = ((SOUTH + NORTH) / 2, (WEST + EAST) / 2)
MARGIN = 0.0015                       # keep lines and areas a little past the box, so edges fade instead of stopping
LEVEL_M, ROOF_LEVEL_M = 3.0, 2.2
GUESS_M = {"house": 6.5, "detached": 6.5, "semidetached_house": 6.5, "residential": 7.0, "terrace": 7.0,
           "bungalow": 4.5, "apartments": 9.5, "dormitory": 9.5, "hotel": 9.0, "motel": 7.0, "commercial": 6.5,
           "retail": 6.0, "office": 8.0, "industrial": 7.0, "warehouse": 7.5, "church": 11.0, "school": 7.0,
           "garage": 3.0, "garages": 3.0, "carport": 3.0, "shed": 2.6, "hut": 2.8, "roof": 4.0, "boathouse": 5.0,
           "kiosk": 3.0, "toilets": 3.2, "service": 3.5, "construction": 4.0, "greenhouse": 3.0}
GUESS_DEFAULT = 6.0

ROAD = {"motorway": "major", "trunk": "major", "primary": "major", "secondary": "major", "primary_link": "major",
        "secondary_link": "major", "tertiary": "street", "tertiary_link": "street", "residential": "street",
        "unclassified": "street", "living_street": "street", "service": "service", "pedestrian": "walk",
        "footway": "path", "path": "path", "cycleway": "cycle", "steps": "steps", "track": "path",
        "bridleway": "path"}

AREA_RULES = [  # (tag, values or None for any, class); first match wins
    ("natural", {"water"}, "water"), ("water", None, "water"), ("waterway", {"riverbank"}, "water"),
    ("leisure", {"swimming_pool"}, "pool"), ("leisure", {"marina"}, "marina"),
    ("natural", {"wetland"}, "wetland"), ("natural", {"beach", "sand"}, "beach"),
    ("leisure", {"pitch", "track"}, "pitch"), ("leisure", {"playground"}, "play"),
    ("leisure", {"park", "garden", "nature_reserve", "common", "dog_park", "recreation_ground"}, "park"),
    ("landuse", {"grass", "meadow", "village_green", "recreation_ground", "cemetery", "allotments"}, "green"),
    ("natural", {"wood", "scrub", "grassland", "heath"}, "wood"), ("landuse", {"forest"}, "wood"),
    ("amenity", {"parking"}, "parking"), ("landuse", {"commercial", "retail"}, "commercial"),
    ("landuse", {"residential"}, "residential"), ("landuse", {"railway", "industrial"}, "industrial"),
    ("amenity", {"school", "college", "kindergarten"}, "school"),
]
SKIP_RELATIONS = {"boundary"}         # the marine sanctuary's 731-member boundary is a legal line, not ground

PROP_NODES = {"bench", "toilets", "drinking_water", "bicycle_parking", "waste_basket", "bus_stop", "viewpoint",
              "artwork", "picnic_table", "fountain", "post_box", "information"}


def num(v):
    m = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", v or "")
    return float(m.group(1)) if m else None


lat0 = math.radians(ORIGIN[0])
M_LAT = 111132.954 - 559.822 * math.cos(2 * lat0) + 1.175 * math.cos(4 * lat0)
M_LON = 111412.84 * math.cos(lat0) - 93.5 * math.cos(3 * lat0) + 0.118 * math.cos(5 * lat0)


def xy(p):
    return round((p[1] - ORIGIN[1]) * M_LON * 10), round((p[0] - ORIGIN[0]) * M_LAT * 10)


def flat(pts):
    out = []
    for p in pts:
        x, y = xy(p)
        if len(out) >= 2 and out[-2] == x and out[-1] == y:
            continue
        out += [x, y]
    return out


def inside(p, m=0.0):
    return SOUTH - m <= p[0] <= NORTH + m and WEST - m <= p[1] <= EAST + m


def join(segs):
    """Join open node lists end to end into rings (multipolygon members)."""
    rings, segs = [], [list(s) for s in segs]
    while segs:
        ring = segs.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[::-1][1:]
                elif s[-1] == ring[0]:
                    ring = s + ring[1:]
                elif s[0] == ring[0]:
                    ring = s[::-1] + ring[1:]
                else:
                    continue
                segs.pop(i)
                changed = True
                break
        if ring[0] == ring[-1] and len(ring) >= 4:
            rings.append(ring)
    return rings


def centroid(pts):
    a = cx = cy = 0.0
    for (y1, x1), (y2, x2) in zip(pts, pts[1:]):
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    if abs(a) < 1e-14:
        return pts[0]
    return cy / (3 * a), cx / (3 * a)


def height(t):
    h = num(t.get("height")) or num(t.get("building:height"))
    if h:
        return round(h, 1), "tag"
    lv = num(t.get("building:levels"))
    if lv:
        return round(lv * LEVEL_M + (num(t.get("roof:levels")) or 0) * ROOF_LEVEL_M + 0.6, 1), "levels"
    return GUESS_M.get(t.get("building", "yes"), GUESS_DEFAULT), "guess"


def area_class(t):
    for k, vals, cls in AREA_RULES:
        if k in t and (vals is None or t[k] in vals):
            return cls
    return None


def address(t):
    if "addr:street" not in t:
        return ""
    return (t.get("addr:housenumber", "") + " " + t["addr:street"]).strip()


def category(t):
    for k in ("amenity", "shop", "tourism", "leisure", "craft", "office", "historic", "man_made", "highway"):
        if k in t:
            return t[k] if k != "shop" else "shop:" + t[k]
    return "place"


def sea_ring(coast):
    """Chain the coastline (land on the left, so the sea is on the right going east here), clip it to the margin box,
    and close it round the box's south side. Returns one ring of (lat, lon) or None."""
    by_start = {}
    ways = [[(g["lat"], g["lon"]) for g in w["geometry"]] for w in coast]
    for w in ways:
        by_start[w[0]] = w
    ends = {w[-1] for w in ways}
    heads = [w for w in ways if w[0] not in ends]
    best = []
    for h in heads:
        chain, cur = list(h), h
        while cur[-1] in by_start and by_start[cur[-1]] is not cur and len(chain) < 5000:
            cur = by_start[cur[-1]]
            chain += cur[1:]
        if len(chain) > len(best):
            best = chain
    s, w, n, e = SOUTH - MARGIN, WEST - MARGIN, NORTH + MARGIN, EAST + MARGIN
    # keep the part between the first and last points inside the box, then run west/east to the box edges
    idx = [i for i, p in enumerate(best) if w <= p[1] <= e and s <= p[0] <= n]
    if not idx:
        return None
    part = best[max(0, idx[0] - 1):idx[-1] + 2]
    part = [(max(s, min(n, la)), max(w, min(e, lo))) for la, lo in part]
    if part[0][1] > part[-1][1]:
        part = part[::-1]
    ring = [(part[0][0], w)] + part + [(part[-1][0], e), (s, e), (s, w), (part[0][0], w)]
    return ring


def main():
    raw = RAW.read_bytes()
    acq = json.loads(ACQ.read_text(encoding="utf-8"))
    assert hashlib.sha256(raw).hexdigest() == acq["sha256"], "the extract is not the one fetched"
    coast_raw = COAST.read_bytes()
    acq_coast = json.loads(ACQ_COAST.read_text(encoding="utf-8"))
    assert hashlib.sha256(coast_raw).hexdigest() == acq_coast["sha256"], "the coastline is not the one fetched"
    els = json.loads(raw)["elements"]
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in els if e["type"] == "node"}
    node_tags = {e["id"]: e.get("tags", {}) for e in els if e["type"] == "node" and e.get("tags")}
    ways = {e["id"]: e for e in els if e["type"] == "way"}
    rels = [e for e in els if e["type"] == "relation"]
    pts = lambda ids: [nodes[i] for i in ids if i in nodes]
    skipped = collections.Counter()

    # --- buildings ---------------------------------------------------------------------------------------------
    cands = []
    for w in ways.values():
        t = w.get("tags", {})
        if "building" in t and w["nodes"][0] == w["nodes"][-1]:
            cands.append(("way/%d" % w["id"], t, [w["nodes"]], []))
    for r in rels:
        t = r.get("tags", {})
        if "building" in t:
            mem = lambda role: [ways[m["ref"]]["nodes"] for m in r["members"]
                                if m["type"] == "way" and m["role"] == role and m["ref"] in ways]
            cands.append(("relation/%d" % r["id"], t, join(mem("outer")), join(mem("inner"))))
    buildings = []
    for osm, t, outers, inners in cands:
        for o in outers:
            ring = pts(o)
            if len(ring) < 4:
                skipped["building without a closed ring"] += 1
                continue
            if not inside(centroid(ring)):
                skipped["building outside the box"] += 1
                continue
            h, src = height(t)
            b = {"id": osm, "h": h, "hs": src, "k": t.get("building", "yes"), "r": [flat(ring)]}
            b["r"] += [flat(pts(i)) for i in inners]
            if t.get("name"):
                b["n"] = t["name"]
            if address(t):
                b["a"] = address(t)
            if t.get("roof:shape"):
                b["roof"] = t["roof:shape"]
            buildings.append(b)

    # --- roads, rail, streams ----------------------------------------------------------------------------------
    roads, rail, streams = [], [], []
    for w in ways.values():
        t = w.get("tags", {})
        p = pts(w["nodes"])
        if not p or not any(inside(q, MARGIN) for q in p):
            continue
        # trim very long ways (the river runs 30 km) to the run near the box
        keep = [q for q in p if inside(q, MARGIN * 3)]
        if len(keep) < 2:
            continue
        cls = ROAD.get(t.get("highway"))
        if cls and t.get("area") != "yes":
            r = {"id": "way/%d" % w["id"], "c": cls, "p": flat(keep)}
            if t.get("name"):
                r["n"] = t["name"]
            if t.get("oneway") in ("yes", "1") and cls in ("major", "street", "service"):
                r["one"] = 1
            if t.get("footway") == "crossing" or t.get("cycleway") == "crossing":
                r["x"] = 1
            if t.get("bridge") == "yes":
                r["br"] = 1
            if t.get("access") in ("private", "no"):
                r["pv"] = 1
            roads.append(r)
        elif t.get("railway") in ("rail", "light_rail", "disused", "abandoned") and t.get("area") != "yes":
            rail.append({"id": "way/%d" % w["id"], "p": flat(keep), **({"br": 1} if t.get("bridge") == "yes" else {})})
        elif t.get("waterway") in ("stream", "river", "canal", "drain", "ditch"):
            streams.append({"id": "way/%d" % w["id"], "c": t["waterway"], "p": flat(keep),
                            **({"n": t["name"]} if t.get("name") else {})})

    # --- areas -------------------------------------------------------------------------------------------------
    areas = []
    in_rel = set()
    for r in rels:
        t = r.get("tags", {})
        if t.get("type") in SKIP_RELATIONS:
            skipped["boundary relation"] += 1
            continue
        cls = area_class(t)
        if not cls or "building" in t:
            continue
        mem = lambda role: [ways[m["ref"]]["nodes"] for m in r["members"]
                            if m["type"] == "way" and m["role"] == role and m["ref"] in ways]
        outers, inners = join(mem("outer")), join(mem("inner"))
        for m in r["members"]:
            if m["type"] == "way":
                in_rel.add(m["ref"])
        for o in outers:
            ring = pts(o)
            if len(ring) >= 4 and any(inside(q, MARGIN) for q in ring):
                a = {"id": "relation/%d" % r["id"], "k": cls, "r": [flat(ring)] + [flat(pts(i)) for i in inners]}
                if t.get("name"):
                    a["n"] = t["name"]
                areas.append(a)
    for w in ways.values():
        t = w.get("tags", {})
        cls = area_class(t)
        if not cls or "building" in t or w["nodes"][0] != w["nodes"][-1]:
            continue
        if w["id"] in in_rel and not t.get("name"):
            continue
        ring = pts(w["nodes"])
        if len(ring) >= 4 and any(inside(q, MARGIN) for q in ring):
            a = {"id": "way/%d" % w["id"], "k": cls, "r": [flat(ring)]}
            if t.get("name"):
                a["n"] = t["name"]
            areas.append(a)
    coast = json.loads(coast_raw)["elements"]
    sea = sea_ring(coast)
    if sea:
        areas.insert(0, {"id": "coastline", "k": "sea", "n": "Monterey Bay", "r": [flat(sea)]})
    else:
        skipped["sea could not be closed"] += 1
    order = ["sea", "residential", "commercial", "industrial", "school", "green", "park", "wood", "wetland", "beach",
             "pitch", "play", "parking", "marina", "water", "pool"]
    areas.sort(key=lambda a: order.index(a["k"]))

    # --- places people name: shops, cafes, parks' names, and small props --------------------------------------
    pois, props = [], []
    for nid, t in node_tags.items():
        p = nodes.get(nid)
        if not p or not inside(p):
            continue
        x, y = xy(p)
        kind = t.get("amenity") or t.get("highway") or t.get("tourism") or t.get("leisure")
        if t.get("name") and not t.get("highway") == "crossing":
            c = category(t)
            if c in ("bus_stop",):
                props.append({"id": "node/%d" % nid, "k": "bus_stop", "x": x, "y": y, "n": t["name"]})
                continue
            item = {"id": "node/%d" % nid, "n": t["name"], "c": c, "x": x, "y": y}
            if address(t):
                item["a"] = address(t)
            pois.append(item)
        elif kind in PROP_NODES:
            props.append({"id": "node/%d" % nid, "k": kind, "x": x, "y": y})
    for w in ways.values():                     # named shops, amenities, parks and beaches drawn as areas
        t = w.get("tags", {})
        if t.get("name") and (any(k in t for k in ("amenity", "shop", "tourism", "leisure", "historic"))
                              or area_class(t) in ("beach", "water", "park", "wetland", "wood")) \
                and w["nodes"][0] == w["nodes"][-1]:
            ring = pts(w["nodes"])
            c = centroid(ring)
            if inside(c):
                x, y = xy(c)
                c = category(t)
                item = {"id": "way/%d" % w["id"], "n": t["name"], "c": area_class(t) if c == "place" else c,
                        "x": x, "y": y}
                if address(t):
                    item["a"] = address(t)
                pois.append(item)
    for r in rels:
        t = r.get("tags", {})
        if t.get("name") and t.get("type") == "multipolygon" and area_class(t) in ("park", "beach", "water", "marina"):
            ring = next((pts(o) for o in join([ways[m["ref"]]["nodes"] for m in r["members"]
                                                if m["type"] == "way" and m["role"] == "outer" and m["ref"] in ways])), None)
            if ring and inside(centroid(ring)):
                x, y = xy(centroid(ring))
                pois.append({"id": "relation/%d" % r["id"], "n": t["name"], "c": area_class(t), "x": x, "y": y})

    bx0, by0 = xy((SOUTH, WEST))
    bx1, by1 = xy((NORTH, EAST))
    ground = {
        "format": "agora-ground/1",
        "name": "Seabright, Santa Cruz",
        "attribution": "© OpenStreetMap contributors · ODbL",
        "licence": "Open Database License 1.0. This ground is a derived database of OpenStreetMap data.",
        "source": {"osm_base": acq["osm_base"], "extract_sha256": acq["sha256"],
                   "coast_osm_base": acq_coast["osm_base"], "coast_sha256": acq_coast["sha256"],
                   "bbox": {"south": SOUTH, "west": WEST, "north": NORTH, "east": EAST}},
        "frame": {"origin": {"lat": ORIGIN[0], "lon": ORIGIN[1]}, "unit": "dm",
                  "m_per_deg_lat": round(M_LAT, 4), "m_per_deg_lon": round(M_LON, 4)},
        "bounds": [bx0, by0, bx1, by1],
        "heights": {"tag": "a mapper's height tag", "levels": f"estimated from levels ({LEVEL_M} m each)",
                    "guess": "estimated from the building's kind alone"},
        "buildings": buildings, "roads": roads, "rail": rail, "streams": streams, "areas": areas,
        "pois": sorted(pois, key=lambda p: p["n"]), "props": props,
    }
    text = json.dumps(ground, separators=(",", ":"), ensure_ascii=False)
    OUT.write_text(text, encoding="utf-8")
    print(json.dumps({"buildings": len(buildings), "heights": dict(collections.Counter(b["hs"] for b in buildings)),
                      "roads": len(roads), "named_roads": len({r.get("n") for r in roads if r.get("n")}),
                      "rail": len(rail), "streams": len(streams),
                      "areas": dict(collections.Counter(a["k"] for a in areas)), "pois": len(pois),
                      "props": dict(collections.Counter(p["k"] for p in props)), "skipped": dict(skipped),
                      "bytes": len(text.encode()), "box_m": [round((bx1 - bx0) / 10), round((by1 - by0) / 10)]},
                     indent=1))


if __name__ == "__main__":
    main()
