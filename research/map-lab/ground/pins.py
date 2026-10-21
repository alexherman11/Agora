"""Three public pin coordinates taken from the extract itself (no invented survey facts): the area centroid of each
named footprint, checked to lie inside that footprint. Prints lat, lon (WGS84, in that order) and the OSM source."""
import json
from pathlib import Path

import build_fixture as bf

PLACES = [("British Museum", "relation/177044"), ("Museum Tavern", "way/553157392"),
          ("St George's Bloomsbury", "way/51755264")]


def inside(ring, p):
    c = False
    for (y1, x1), (y2, x2) in zip(ring, ring[1:]):
        if (y1 > p[0]) != (y2 > p[0]) and p[1] < (x2 - x1) * (p[0] - y1) / (y2 - y1) + x1:
            c = not c
    return c


def main():
    text = (bf.HERE / "fixture.js").read_text(encoding="utf-8")
    fx = json.loads(text[text.index("{"):text.rindex("}") + 1])
    out = []
    for name, osm in PLACES:
        b = next(b for b in fx["buildings"] if b["osm"] == osm)
        outer = [(b["rings"][0][i], b["rings"][0][i + 1]) for i in range(0, len(b["rings"][0]), 2)]
        (lat, lon), area = bf.area_centroid(outer)
        holes = [[(r[i], r[i + 1]) for i in range(0, len(r), 2)] for r in b["rings"][1:]]
        ok = inside(outer, (lat, lon)) and not any(inside(h, (lat, lon)) for h in holes)
        out.append({"label": name, "lat": round(lat, 6), "lon": round(lon, 6), "source": f"OpenStreetMap {osm}",
                    "how": "area centroid of the footprint" + ("" if ok else " (NOT inside it: in a courtyard)"),
                    "inside_footprint": ok, "footprint_m2": round(abs(area))})
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
