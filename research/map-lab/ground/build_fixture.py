"""Raw Overpass extract -> fixture.js, the only data the map frame reads.

Coordinate order everywhere in the fixture: lat, lon (WGS84 degrees), as flat arrays [lat, lon, lat, lon, ...],
rounded to 7 decimals (OSM's own precision). Each feature keeps its OSM id ("way/123"); Agora ids are a different
thing and never appear here. A footprint is kept whole when its centroid lies in the square (topology is never cut);
roads are clipped to the square. Heights: 'tag' from a height tag; 'levels' estimated from the level count; 'guess'
estimated from the building's kind alone. Only 'tag' is a mapper's measurement, and even that is not surveyed by us.

  python research/map-lab/ground/build_fixture.py      -> fixture.js, and prints the counts
"""
import collections
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "extract" / "osm-bloomsbury.json"
ACQ = HERE / "extract" / "acquisition.json"
OUT = HERE / "fixture.js"

SOUTH, WEST, NORTH, EAST = 51.51715, -0.13061, 51.52165, -0.12339        # the granted query's bbox
CENTRE = (51.5194, -0.1270)
LEVEL_M, ROOF_LEVEL_M = 3.2, 2.6             # metres a storey, and a roof storey (estimates, said in the legend)
GUESS_M = {"house": 10, "terrace": 10, "residential": 12, "apartments": 15, "retail": 12, "commercial": 14,
           "office": 16, "hotel": 18, "university": 18, "college": 18, "school": 12, "museum": 20, "church": 16,
           "shed": 3, "roof": 4, "garage": 3}
GUESS_DEFAULT = 12
MAX_FOOTPRINTS = 500

ROAD_CLASS = {"primary": "major", "secondary": "major", "tertiary": "street", "residential": "street",
              "unclassified": "street", "service": "service", "pedestrian": "walk", "footway": "path",
              "cycleway": "path", "steps": "path", "living_street": "street", "path": "path"}


def num(v):
    m = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", v or "")
    return float(m.group(1)) if m else None


def rnd(x):
    return round(x, 7)


def rings_of_relation(rel, ways, nodes):
    """Outer and inner rings from a multipolygon's member ways, joining open ways end to end."""
    out = {"outer": [], "inner": []}
    for role in out:
        segs = [[n for n in ways[m["ref"]]["nodes"]] for m in rel["members"]
                if m["type"] == "way" and m["role"] == role and m["ref"] in ways]
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
                out[role].append(ring)
    return out


def area_centroid(pts):
    """Centroid of a closed ring of (lat, lon) in a local flat frame; area in m² (signed)."""
    lat0 = pts[0][0]
    k = math.cos(math.radians(lat0))
    a = cx = cy = 0.0
    for (y1, x1), (y2, x2) in zip(pts, pts[1:]):
        x1, x2 = x1 * k, x2 * k
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    if abs(a) < 1e-18:
        return pts[0], 0.0
    return (cy / (3 * a), cx / (3 * a) / k), a / 2 * 111320 * 111320


def clip(p, q):
    """Liang-Barsky: the part of segment p-q (lat, lon) inside the square, or None."""
    t0, t1 = 0.0, 1.0
    dy, dx = q[0] - p[0], q[1] - p[1]
    for pp, qq in ((-dx, p[1] - WEST), (dx, EAST - p[1]), (-dy, p[0] - SOUTH), (dy, NORTH - p[0])):
        if pp == 0:
            if qq < 0:
                return None
            continue
        r = qq / pp
        if pp < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return None
    return (p[0] + t0 * dy, p[1] + t0 * dx), (p[0] + t1 * dy, p[1] + t1 * dx)


def clip_line(pts):
    runs, cur = [], []
    for p, q in zip(pts, pts[1:]):
        c = clip(p, q)
        if not c:
            if cur:
                runs.append(cur)
                cur = []
            continue
        a, b = c
        if not cur or cur[-1] != a:
            if cur:
                runs.append(cur)
            cur = [a]
        cur.append(b)
        if b != q:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def flat(pts):
    return [v for p in pts for v in (rnd(p[0]), rnd(p[1]))]


def height(tags):
    h = num(tags.get("height")) or num(tags.get("building:height"))
    if h:
        return h, "tag", f"height tag {tags.get('height') or tags.get('building:height')}"
    lv = num(tags.get("building:levels"))
    if lv:
        rl = num(tags.get("roof:levels")) or 0
        return (round(lv * LEVEL_M + rl * ROOF_LEVEL_M, 1), "levels",
                f"estimated: {lv:g} levels x {LEVEL_M} m" + (f" + {rl:g} roof levels x {ROOF_LEVEL_M} m" if rl else ""))
    kind = tags.get("building", "yes")
    g = GUESS_M.get(kind, GUESS_DEFAULT)
    return g, "guess", f"estimated: no height or levels; {g} m guessed for building={kind}"


def main():
    raw = RAW.read_bytes()
    acq = json.loads(ACQ.read_text(encoding="utf-8"))
    assert hashlib.sha256(raw).hexdigest() == acq["sha256"], "the extract is not the one fetched"
    els = json.loads(raw)["elements"]
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in els if e["type"] == "node"}
    ways = {e["id"]: e for e in els if e["type"] == "way"}
    rels = [e for e in els if e["type"] == "relation"]
    pts = lambda ids: [nodes[i] for i in ids if i in nodes]

    buildings, dropped = [], collections.Counter()
    in_rel = {m["ref"] for r in rels for m in r.get("members", []) if m["type"] == "way"}
    cands = []
    for w in ways.values():
        t = w.get("tags", {})
        if "building" in t and w["nodes"][0] == w["nodes"][-1]:
            cands.append(("way/%d" % w["id"], t, {"outer": [w["nodes"]], "inner": []}))
    for r in rels:
        t = r.get("tags", {})
        if "building" in t:
            cands.append(("relation/%d" % r["id"], t, rings_of_relation(r, ways, nodes)))
    for osm, t, rings in cands:
        outer = [pts(r) for r in rings["outer"]]
        if not outer or any(len(o) < 4 for o in outer):
            dropped["no closed outer ring"] += 1
            continue
        (clat, clon), a = area_centroid(outer[0])
        if not (SOUTH <= clat <= NORTH and WEST <= clon <= EAST):
            dropped["centroid outside the square"] += 1
            continue
        h, src, note = height(t)
        for o in outer:                              # one footprint per outer ring, its inners with it
            buildings.append({"osm": osm, "kind": t.get("building"), "name": t.get("name", ""),
                              "h": h, "h_src": src, "h_note": note,
                              "rings": [flat(o)] + [flat(pts(i)) for i in rings["inner"]]})
    if len(buildings) > MAX_FOOTPRINTS:
        raise SystemExit(f"{len(buildings)} footprints: over the {MAX_FOOTPRINTS} budget; say so on the card")

    roads = []
    for w in ways.values():
        t = w.get("tags", {})
        cls = ROAD_CLASS.get(t.get("highway"))
        if not cls or t.get("area") == "yes":
            continue
        for run in clip_line(pts(w["nodes"])):
            roads.append({"osm": "way/%d" % w["id"], "cls": cls, "name": t.get("name", ""), "pts": flat(run)})
    areas = []
    for w in ways.values():
        t = w.get("tags", {})
        if (t.get("leisure") == "park" or t.get("landuse") == "grass") and w["nodes"][0] == w["nodes"][-1] \
                and w["id"] not in in_rel:
            areas.append({"osm": "way/%d" % w["id"], "cls": "green", "name": t.get("name", ""),
                          "rings": [flat(pts(w["nodes"]))]})

    lat0 = math.radians(CENTRE[0])
    meta = {
        "title": "Bloomsbury, London: a 500 m square around the British Museum",
        "source": "OpenStreetMap, via one Overpass API query (" + acq["endpoint"] + ")",
        "licence": "Open Database License 1.0 (ODbL); this fixture is a derived database under the same licence",
        "attribution": "© OpenStreetMap contributors",
        "osm_base": acq["osm_base"], "acquired_utc": acq["received_utc"], "extract_sha256": acq["sha256"],
        "bbox": {"south": SOUTH, "west": WEST, "north": NORTH, "east": EAST},
        "centre": {"lat": CENTRE[0], "lon": CENTRE[1]},
        "coord_order": "lat,lon (flat arrays: lat, lon, lat, lon, ...)",
        "ground": "flat: no terrain data; all ground is drawn at 0 m",
        "heights": {"tag": "from a mapper's height tag", "levels": f"estimated from levels ({LEVEL_M} m each)",
                    "guess": "estimated from the building's kind alone"},
        "m_per_deg_lat": 111132.954 - 559.822 * math.cos(2 * lat0) + 1.175 * math.cos(4 * lat0),
        "m_per_deg_lon": 111412.84 * math.cos(lat0) - 93.5 * math.cos(3 * lat0) + 0.118 * math.cos(5 * lat0),
    }
    fx = {"meta": meta, "buildings": buildings, "roads": roads, "areas": areas}
    text = "// generated by build_fixture.py from OpenStreetMap data, ODbL 1.0, (c) OpenStreetMap contributors\n" \
           "window.MAP_FIXTURE = " + json.dumps(fx, separators=(",", ":"), ensure_ascii=False) + ";\n"
    OUT.write_text(text, encoding="utf-8")
    src = collections.Counter(b["h_src"] for b in buildings)
    w_m = (EAST - WEST) * meta["m_per_deg_lon"]
    h_m = (NORTH - SOUTH) * meta["m_per_deg_lat"]
    print(json.dumps({"footprints": len(buildings), "dropped": dict(dropped), "heights": dict(src),
                      "roads": len(roads), "areas": len(areas), "fixture_bytes": len(text.encode()),
                      "square_m": [round(w_m, 1), round(h_m, 1)]}))


if __name__ == "__main__":
    main()
