# Where the map's data came from

**Source:** OpenStreetMap. The data was fetched with one query to the public Overpass API, `https://overpass-api.de/api/interpreter`. JEFF granted exactly that fetch on the commission (c7984); Pike supported it (c7981). It was an HTTPS POST: read-only, with no key, no account, no retry and no redirect followed.

**Query** (exactly as granted; `out body`, never `meta`, so no mapper names or user ids were saved):

```
[out:json][timeout:60][bbox:51.51715,-0.13061,51.52165,-0.12339];(way[building];relation[building];way[highway];way[leisure=park];way[landuse=grass];);out body;>;out skel qt;
```

**Bounds:** south 51.51715, west -0.13061, north 51.52165, east -0.12339 (WGS84 degrees). This is a square of 501.1 m east-west by 500.7 m north-south, centred on 51.5194, -0.1270, the British Museum.

**Dates (UTC):**
- Requested 2026-10-21T18:10:15.
- Received 2026-10-21T18:10:57.
- The data is as of `osm_base` 2026-10-21T18:10:10Z, the time of the OpenStreetMap database the server answered from.

**The saved extract:**
- File: `extract/osm-bloomsbury.json`. These are the bytes as received.
- Size: 761,822 bytes, 5,378 elements.
- SHA-256: `48e8aab84353b20f72c1888fb3d48183942ebff68504582237bcdc366312b5e6`.
- `extract/acquisition.json` records all of the above. `build_fixture.py` refuses to build if the extract's hash differs from the recorded one.

**Licence:**
- OpenStreetMap data is © OpenStreetMap contributors and available under the **Open Database License 1.0 (ODbL)**. Read 21 Oct at https://www.openstreetmap.org/copyright. The response itself says: "The data included in this document is from www.openstreetmap.org. The data is made available under ODbL."
- The saved extract stays under ODbL.
- `fixture.js` is a **derived database** (filtered, clipped, rounded to 7 decimals, with estimated heights added), so it is also under ODbL 1.0. If it is shared, it is shared under that same licence.
- The pictures the frame draws are a produced work. They carry the attribution "© OpenStreetMap contributors · ODbL", which is visible on the map in 3D and in the flat plan.

**Usage policy:** read 21 Oct at https://wiki.openstreetmap.org/wiki/Overpass_API. One query is far inside its limits. The map never fetches anything: `map.html`'s Content-Security-Policy sets `connect-src 'none'`, and the measured frame's `fetch` was blocked.

**What is ours, not OpenStreetMap's:**
- the colours, outlines, shadows and cartoon style;
- the heights. Only 2 buildings carry a height tag; 280 are estimated from `building:levels` at 3.2 m a level plus 2.6 m per roof level; 53 are guessed from the building's kind alone;
- the flat ground. There is no terrain data, so everything stands at 0 m.

The legend says all of this on the map, and pressing a building shows how its height was made.
