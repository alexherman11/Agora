# Where the Seabright ground came from

**Source:** OpenStreetMap, through the public Overpass API (`https://overpass-api.de/api/interpreter`). Alex allowed OpenStreetMap reads on 27 Oct 2026. Two read-only requests, no key or account, `out body` / `out tags geom` (never `meta`, so no mapper names or ids were saved):

1. `fetch_extract.py`: the neighbourhood, box south 36.9590, west -122.0230, north 36.9800, east -121.9990 (about 2.1 km by 2.3 km: the San Lorenzo river mouth to the harbour, the beach to Soquel Avenue). Buildings, streets, rail, leisure, land use, natural features, water, amenities, and named or useful points. Requested 2026-10-27T16:40:15Z; `osm_base` 2026-10-27T16:39:40Z; 8,248,617 bytes, 75,573 elements. Record: `extract/acquisition.json`.
2. `fetch_coast.py`: the coastline alone in a slightly larger box, because request 1 returned only two of the coastline ways crossing it, so the sea could not be closed. The first try got HTTP 502; one retry 20 s later succeeded. Requested 2026-10-27T16:46:23Z; `osm_base` 2026-10-27T16:45:50Z; 25,042 bytes, 23 ways. Record: `extract/acquisition-coast.json`.

`build_ground.py` refuses to build if either extract's SHA-256 differs from its record.

**Licence:** OpenStreetMap data is © OpenStreetMap contributors under the Open Database License 1.0. `seabright-ground.json` is a derived database (filtered, projected to a local frame in decimetres, heights estimated), so it is under ODbL 1.0 too, and says so inside. The map draws "© OpenStreetMap contributors · ODbL" at all times.

**Ours, not OpenStreetMap's:** colours, shadows, outlines and the cartoon look; the heights (175 buildings from mapped levels at 3 m a level; 2,660 guessed from the building's kind); the flat ground (no terrain); the land slab and its earth sides.

**Known gaps (read from the data):** several blocks east of Seabright Avenue have streets but few or no buildings mapped. The map shows them empty rather than inventing buildings.
