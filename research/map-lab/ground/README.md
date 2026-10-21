# Living map, ground (a7946): Bloomsbury as a cartoon 3D map in an isolated frame

This is the geography half of the first slice (map card a7858; contract a7875). `map.html` is the frame. It draws a 500 m square around the British Museum from a local OpenStreetMap extract. It also draws the pins and routes that a `draw` message brings, and nothing else. `host.html` is a stand-in sender for testing: it is not the seam, which a7950 builds.

## Files

| File | What it is |
| --- | --- |
| `map.html`, `map.js` | The frame. |
| `geo.js` | lat/lon ↔ metres, the tiny-earth curve and its exact inverse, and footprint triangulation. |
| `fixture.js` | The only data the frame reads. Built by `build_fixture.py` from `extract/`. See SOURCE.md. |
| `host.html`, `host.js`, `stand_in_draw.json` | The stand-in sender: three test pins and one route, held in memory. |
| `measure.py` | All the checks below, on the hidden desktop under the guard. Writes `results/measure.json` and `shots/`. |
| `demo.py` | A film for Alex, made on the hidden desktop: `research/window-lab/demos/map-ground-a7946.mp4` in the main checkout. |
| `fetch_extract.py` | The one granted fetch. It refuses to run again. |
| `pins.py` | The three pin coordinates, taken from the extract. |

## How it works

- **Coordinates.**
  - Storage is WGS84 lat, lon. The fixture uses flat arrays in the order lat, lon. Messages use named `lat` and `lon` fields, never arrays.
  - The drawing uses a local tangent frame in metres around the centre (east, north). Its scale comes from the WGS84 metres-per-degree series at 51.5194° N.
  - Every feature keeps its OSM id (`way/…`, `relation/…`). Agora ids never enter the fixture.
- **Curve.**
  - The tiny-earth view wraps the flat ground onto a sphere of radius 800 m. Distance along the ground is kept (azimuthal equidistant), and the sphere touches the plane at the centre.
  - It is done in the vertex shader, from a uniform. Toggling it rebuilds nothing and changes no stored number.
  - The wrap has an exact inverse, so a drop or drag picks the ground on the sphere and maps it back to the same lat/lon.
- **Cartoon.**
  - Buildings are extruded footprints: flat roofs, our own pastel palette chosen by a hash of the OSM id, light from the south-west, and dark outline edges on roofs and corners.
  - Courtyards are kept as holes, as OSM draws them. A footprint is kept whole when its centroid is inside the square, and never cut.
  - The ground is one 2048² canvas texture: roads by class, green areas, a soft shadow under each building, and a dashed line where the data ends.
  - That same canvas drawing, with filled footprints, is the static plan.
- **No render loop.**
  - A frame is drawn only when something changes: input, a message, a toggle or a resize. Each change asks for one animation frame.
  - The one deliberate loop is `__map.bench()`, which the measuring script runs for 240 frames.
- **Static fallback.**
  - `?nogl=1` refuses WebGL, as a machine without it would. `?static=1`, or the "Flat plan (no 3D)" button, shows the plan.
  - The plan has pins, the route, the pin list, dropping, the building info and the attribution, all without 3D.
- **The seam** (a7875, THE SEAM; channel `agora-map/1`, carried as a field named `channel`):
  - In: `{channel, op:'draw', pins:[{id, rev, lat, lon, height, label, icon, colour}], routes:[{id, rev, label, pins:[ids]}]}`. Each draw replaces the whole picture.
  - Out: `{channel, op:'press', id}`, `{channel, op:'drop', lat, lon}` and `{channel, op:'move', id, rev, lat, lon}`. A move carries the rev the frame drew.
  - Who is speaking (c8088): each time the frame loads, the host makes a new MessageChannel and sends one `{channel, op:'hello'}` to the frame's window, carrying a port. The frame keeps that port, takes draws only from it, and sends press, drop and move only on it. Anything posted to the window is refused, in both directions.
  - A message on the port that is not a draw on the right channel is refused whole.
  - Inside a draw, a bad pin or route is refused alone, and the rest draws. Unknown fields are dropped, labels are set as text only, and colours must be `#rrggbb`.
  - `host.html` holds the frame with `sandbox="allow-scripts"` and no `allow-same-origin`. The frame gets an opaque origin (`null`), cannot touch its parent or storage, and its CSP allows no network.

## Results (ran 21 Oct 2026, `results/measure.json`)

Hardware:
- Windows 11 26200, Intel64 Family 6 Model 165 (20 logical CPUs), 31.9 GiB RAM.
- GPU: NVIDIA GeForce RTX 2080 Ti through ANGLE/D3D11.
- Edge InPrivate on the hidden desktop, device pixel ratio 1.5.
- Guard: "alex: untouched by the sandbox" on every run.

| Measure | Target | 800x600 | 1280x720 |
| --- | --- | --- | --- |
| footprints | ≤ 500 | 335 | 335 |
| triangles | ≤ 100,000 | 19,314 (11,122 buildings + 8,192 ground), plus 13,446 outline segments | same |
| fixture size | ≤ 5 MiB | 207,985 B (0.198 MiB); 262,008 B for the whole page | same |
| cold load to first drawn frame | (record) | 501.4 ms | 708.9 ms |
| p95 draw time (CPU + GPU, `gl.finish`), real mouse drag, 90 frames | ≤ 33 ms | 0.4 ms | 0.4 ms |
| p95 draw time, 240-frame spin | ≤ 33 ms | 0.3 ms | 0.4 ms |
| p95 frame interval, spin | ≤ 33 ms | 16.7 ms (vsync) | 16.7 ms |
| p95 frame interval, drag | | 33.5 ms | 33.5 ms |
| frames drawn while idle, 3 s after load and after input | 0 | 0 and 0 | 0 and 0 |
| static plan, WebGL refused | works | 3 pins, list, attribution, 0 idle frames | same |

The drag's frame interval of 33.5 ms is the driver's input rate, not the map's speed: each DevTools mouse event is one round trip, about 33 ms apart, and the map draws exactly one frame per move. The spin, which asks for a frame every frame, runs at the display's 60 Hz.

**Curve test.** The anchor is the British Museum pin, 51.519371, -0.127114.
- lat/lon → world → lat/lon: error 0 m with the curve off, and 0 m with it on.
- The ground point in local metres is identical with and without the curve: difference 0 m. With the curve on, the point lies on the sphere to within 4e-5 m.
- Through the screen (project to a pixel, then pick the ground under it): error 0 m and 0 m at 800x600, and 2e-12 m and 0 m at 1280x720.
- The drawn ground mesh is at most 0.012 m from the true sphere: 8.8 m grid cells give a chord sag of s²/8R.
- The pins and the fixture are byte-identical before and after toggling.

**Frame round trip** (host.html at both sizes):
- The draw arrives, with three pins and a route in order p1, p2, p3.
- A real mouse drag of pin 2 sends exactly one `move`. The host accepts it at rev 1 → 2, and the frame then shows rev 2.
- Then the host makes a newer edit the frame has not seen (rev 2 → 3), and a second real drag of the same pin sends rev 2. It is refused ("changed since"), the host's pin is unchanged, and the frame is redrawn at rev 3.
- A well-formed press posted to the window, and a draw posted to the frame's window, are both refused ("posted to the window, not on the port"). The frame keeps its 3 pins.
- A click on pin 1 sends `press`.
- Across the day's 6 runs, cold load to first frame was 501 to 709 ms.
- From inside the frame, `parent.document`, `parent.__host` and `localStorage` all throw SecurityError, and `fetch` is blocked.

## Images

`shots/`:
- `map-800x600.png`, `map-1280x720.png`: the 3D map with the stand-in pins and route;
- `…-curve.png`: the tiny-earth curve;
- `…-estimates.png`: which heights are estimated;
- `…-static.png`: the flat plan with WebGL refused;
- `host-…png`: the frame inside the stand-in host, after a pin drag and a press.

These are a worker's report on style, not a review. Pixel review waits on a7940 or Alex's eye.

## Not checked

- Frame time on weaker hardware. Only the RTX 2080 Ti was measured. Software WebGL (SwiftShader) was not tried, because the sandbox launcher takes no extra browser flags.
- Visible selection response within 100 ms. A press reached the host within the 0.4 s wait, but the latency was not timed.
- Touch input.
- Screen readers. The pin list and the canvas have labels, but no screen reader was run.
- Heights against reality. The British Museum, for one, is a 20 m guess.
- The real seam (a7950), and world notes as the source of pins.
