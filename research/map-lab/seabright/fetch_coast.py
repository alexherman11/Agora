"""The coastline near Seabright: one more read-only Overpass request (Alex allowed OpenStreetMap reads, 27 Oct 2026).

The neighbourhood query (fetch_extract.py) came back with only two of the coastline ways that cross its box, so the
sea could not be closed. This asks for coastline ways alone in a slightly larger box, with their geometry inline.
One POST, no retry, no redirect, 'out tags geom' (no mapper metadata). Writes extract/osm-seabright-coast.json and
adds its record to extract/acquisition-coast.json.
"""
import datetime
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "extract" / "osm-seabright-coast.json"
LOG = HERE / "extract" / "acquisition-coast.json"
ENDPOINT = "https://overpass-api.de/api/interpreter"
QUERY = "[out:json][timeout:60];way[natural=coastline](36.950,-122.035,36.985,-121.990);out tags geom;"

if OUT.exists():
    sys.exit("the coastline extract exists already; one fetch only")
req = urllib.request.Request(ENDPOINT, data=urllib.parse.urlencode({"data": QUERY}).encode(), headers={
    "User-Agent": "Agora research extract (coastline, single request)"})
started = datetime.datetime.now(datetime.timezone.utc)
data = urllib.request.urlopen(req, timeout=90).read(4 * 1024 * 1024)
doc = json.loads(data)
OUT.write_bytes(data)
LOG.write_text(json.dumps({"endpoint": ENDPOINT, "query": QUERY, "requested_utc": started.isoformat(timespec="seconds"),
                           "osm_base": doc.get("osm3s", {}).get("timestamp_osm_base"), "bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest(), "elements": len(doc["elements"])}, indent=2),
               encoding="utf-8")
print(LOG.read_text())
