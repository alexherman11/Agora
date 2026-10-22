"""Counts in the raw extract: what kinds of thing, which height tags, how many footprints (a look, not the build)."""
import collections
import json
from pathlib import Path

doc = json.loads((Path(__file__).resolve().parent / "extract" / "osm-bloomsbury.json").read_text(encoding="utf-8"))
els = doc["elements"]
c = collections.Counter(e["type"] for e in els)
print("types", dict(c))
tagged = [e for e in els if e.get("tags")]
b = [e for e in tagged if "building" in e["tags"]]
print("building ways", sum(e["type"] == "way" for e in b), "relations", sum(e["type"] == "relation" for e in b))
print("building values", collections.Counter(e["tags"]["building"] for e in b).most_common(15))
for k in ("height", "building:levels", "roof:levels", "min_height", "building:min_level", "roof:shape", "building:colour"):
    print(k, sum(k in e["tags"] for e in b))
print("highway", collections.Counter(e["tags"]["highway"] for e in tagged if "highway" in e["tags"]).most_common(20))
print("areas", sum("leisure" in e["tags"] or "landuse" in e["tags"] for e in tagged))
for e in b:
    if e["tags"].get("name"):
        print(" named:", e["type"], e["id"], e["tags"].get("name"), e["tags"].get("building"),
              e["tags"].get("height"), e["tags"].get("building:levels"))
for e in tagged:
    if e["type"] == "relation":
        print(" rel", e["id"], e["tags"].get("type"), e["tags"].get("name"), len(e.get("members", [])),
              collections.Counter(m["role"] for m in e.get("members", [])))
