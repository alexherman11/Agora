"""The Seabright ground: one read-only fetch from OpenStreetMap (Alex allowed it, 27 Oct 2026).

ONE HTTPS POST to the public Overpass API with the bounded query below: no key, no account, no retry,
no redirect followed, response capped at 32 MiB. 'out body', never 'meta', so no mapper names or user ids
are saved. It refuses to run a second time once the extract exists. Writes:
  extract/osm-seabright.json   the response, byte for byte
  extract/acquisition.json     when, what, how big, its SHA-256 (SOURCE.md quotes it)
"""
import datetime
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "extract" / "osm-seabright.json"
LOG = HERE / "extract" / "acquisition.json"
ENDPOINT = "https://overpass-api.de/api/interpreter"
# Seabright, Santa Cruz: San Lorenzo river mouth (west) to the harbour (east), the beach (south) to Soquel Ave (north).
BBOX = (36.9590, -122.0230, 36.9800, -121.9990)
QUERY = ("[out:json][timeout:90][bbox:%s,%s,%s,%s];"
         "(way[building];relation[building];way[highway];way[railway];"
         "way[leisure];relation[leisure];way[landuse];way[natural];relation[natural];"
         "way[waterway];way[water];relation[water];way[amenity];way[man_made=pier];"
         "node[name];node[amenity];node[shop];node[tourism];);"
         "out body;>;out skel qt;") % BBOX
CAP = 32 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None                     # a redirect is a refusal here, not a second fetch


def main():
    if OUT.exists():
        sys.exit(f"the extract exists already ({OUT.name}); one fetch only")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "User-Agent": "Agora research extract (one neighbourhood, single request)",
        "Content-Type": "application/x-www-form-urlencoded"})
    started = datetime.datetime.now(datetime.timezone.utc)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=150) as r:
            status = r.status
            data = r.read(CAP + 1)
    except urllib.error.HTTPError as e:
        sys.exit(f"refused: HTTP {e.code} {e.reason}; stopping, no retry")
    except Exception as e:
        sys.exit(f"failed: {type(e).__name__}: {e}; stopping, no retry")
    done = datetime.datetime.now(datetime.timezone.utc)
    if len(data) > CAP:
        sys.exit(f"oversized: more than {CAP} bytes; nothing saved, stopping")
    doc = json.loads(data)
    if any("user" in e or "uid" in e for e in doc.get("elements", [])):
        sys.exit("the response carries mapper metadata; nothing saved")
    OUT.write_bytes(data)
    log = {"endpoint": ENDPOINT, "method": "POST", "query": QUERY, "bbox_south_west_north_east": BBOX,
           "http_status": status,
           "requested_utc": started.isoformat(timespec="seconds"), "received_utc": done.isoformat(timespec="seconds"),
           "osm_base": doc.get("osm3s", {}).get("timestamp_osm_base"),
           "generator": doc.get("generator"), "copyright_in_response": doc.get("osm3s", {}).get("copyright"),
           "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
           "elements": len(doc.get("elements", []))}
    LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()
