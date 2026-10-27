# The map (kernel-lab app)

*Builder draft by Claude, 27 Oct 2026, from Alex's ask: "a good quality viewer for the map … a very agora native component … easy to inspect, edit, and augment, manage layers, and add places, events etc through the desk language … malleable, that's the key." The design page Alex was shown: https://claude.ai/artifact/W1s98XVfo5PFc7ADDYatRu (his answers to its four questions are still open).*

A 3D, cozy map of Seabright as a window on the kernel desktop. It holds nothing of its own. Everything it shows is a world thing, and everything it does is a line.

## The ideas

1. **Anything can have a place.** A thing is on the map when it says `lat=` and `lon=`; or `at=`/`place=` naming a placed thing (an event at the garden moves with the garden); or, approximately, a `location=` the ground can find by name (drawn with a striped pin).
2. **The ground is a file.** Streets, buildings, water and named places come from OpenStreetMap as one file thing (format `agora-ground/1`), named by a `map` thing. Another community uses another file; no code changes. A building or a shop becomes a world thing only when someone adds to it ("Add as a spot" keeps `osm=way/…`).
3. **Layers are things.** `kind=map-layer`: a reading (`shows="rows spot"`, `rows event title="Council night"`, `board.…`) plus a look (`color`, `look=pin|dot|label|path`). Hiding a layer is your own view preference; the layer stays for everyone.
4. **Routes are things.** `map.route` walks the ground's streets and keeps the path, metres, minutes and streets as facts. Undo takes it back; `map.route <route>` replans it.
5. **The window is arranged.** `map.lens` is an ordinary component lens: the map surface, search, inspector, route planner and layers are six components, and each gesture names the line it runs. Change a line and "add here" does something else.

## Words (module `map`, `modules/map/map.py`)

| Line | What comes back |
|---|---|
| `map.find Seabright & Murray` | the corner, `36.96728, -122.00786` (ran). Places, streets, corners, spots, best first |
| `map.where "Tide pools"` | `74 m from East Cliff Drive, 176 m from The Crow's Nest` (ran) |
| `map.near "Java Junction" within=300` | placed things you can see, nearest first, with metres |
| `map.path stops="a > b > c" [mode=bike]` | a street path as a reading (nothing is made) |
| `map.route name="…" stops="a > b > c"` | makes a route thing: `948 m · 12 min on foot` (ran, three stops) |
| `map.layers Seabright` | the map, then every layer with its placed rows (what the window watches) |
| `map.hide <layer>` / `map.unhide <layer>` | your own view only; also `buildings`, `labels`, `places` |
| `map.show <thing\|name\|lat,lon>` | turns your open map window there |

Stops and centres can be things (ids or names), names on the ground, or `lat,lon`. All readings run as the caller, so nobody sees a placed thing they could not already see.

Kinds: `spot` (a named point), `map`, `map-layer`, `route`. `place` already means the community itself, so a pin-worthy point is a `spot` (one of the open questions for Alex).

## The window

`window.open seabright-map`, or the **Seabright map** button on the taskbar.

- Drag to move, scroll to zoom, right-drag (or Ctrl-drag) to turn and tilt, double-click to zoom in. Keys: arrows/WASD move, `+`/`-` zoom, `Q`/`E` turn, `N` north, `T` tilt, `Esc` stops a tool. Two fingers pinch and turn.
- **Look**: press a pin, building, street, park or name. The inspector shows every fact (ids shown as names you can press), where it is in words, what is near, and its actions, each with the line it runs.
- **Add a spot**: press the map, name it; or choose "An event" and say when ("Sat 10am").
- **Plan a route**: press pins or the map for each stop; the planner shows metres and minutes as you go; Save makes the route. A route's flag in the map opens it; **Fly along it** rides the camera down the street.
- **Layers**: tick to show or hide (for you), `⋯` to change a layer's name, reading, look and colour, or remove it; **New layer** makes one.
- Search flies to the answer, placed in the open part of the map beside the panels.

Styling is ordinary `part-style`. Pins are parts with their facts: `make kind=part-style lens=seabright-map target=geo-map.pin[kind=event] size=22px` (ran).

## Files

| File | |
|---|---|
| `geo-worker.js` | builds the GL geometry from a ground file, off the window's thread (earcut after Mapbox's, ISC) |
| `geo-engine.js` | camera, WebGL passes (land, areas, roads, shadows, buildings, outlines, routes), picking, names and pins |
| `map-components.js` | the six components |
| `map.lens` | the window's arrangement |
| `install.py` | everything above as lines; `--live` installs into the desktop world (opens nothing) |
| `scratch.py`, `look.py`, `proof.py`, `say.py` | hidden scratch world, hidden browser, the evening below, one line to a kept-up scratch world |
| `../../modules/map/map.py`, `ground.py` | the words; finding names, `where`, routes (A* over the ground's streets) |
| `research/map-lab/seabright/` | the two OpenStreetMap fetches, `build_ground.py`, `seabright-ground.json` (860 KB) |

## Evidence

- **ran** `proof.py`, 27 Oct, hidden world and headless Chrome with a software GPU (SwiftShader): 27 of 27 steps pass (`evidence/proof-output.txt`). A person opens the window, presses pins and a building, searches, adds a spot and an event, drags and undoes, plans and saves a three-stop route, flies along it, hides and shows a layer, a line (`map.show`) turns the window, a layer made in a line appears live, a layer is recoloured in the window, a `part-style` line restyles event pins, a building is adopted as a spot, keys zoom, 2D flattens; the map loaded once through it all; no script errors. Pictures: `evidence/proof-*.png`.
- **ran** the ground: 2,835 buildings (175 with mapped levels, the rest guessed by kind), 2,133 street pieces (164 named streets), 403 named places, the sea closed from the coastline; geometry built in 0.5 s (Node).
- **ran** a fresh agent with only the line language (no source, no README), 27 Oct, in a scratch world: it did all 8 tasks (find a corner, place a spot by name, an event at a spot, a route, a new layer, hide it for itself, what is near, restyle pins). What it hit, and what changed: `make` could not take a place name (now `at=` places a thing); `map.layers` did not say which layers were hidden (now "· hidden for you"); `map.near` listed the thing itself and left out routes (fixed); street names along sidewalks came out wrong (route streets now come from runs of 35 m or more per leg). Still open: rough spots 11–13 below; "Forbes Street" was named for a point on Seabright Avenue once (not reproduced).
- **ran** live on Alex's desktop world (kdesk, 8810), 27 Oct: `install.py --live` made the kinds, the ground file, the map, three layers, six components, the lens, the widget and the **Seabright map** taskbar button; nothing was opened. Then `map.find Seabright & Murray` → `Seabright Avenue & Murray Street · corner · 36.96728, -122.00786`; `map.layers Seabright` → `3 layers`; `look-view seabright-map` → the five parts. Off switch: `off map` stops the words; `forget` the Seabright map button, the widget and the lens to remove the window (or `undo` each act); the map and layers are ordinary things anyone can forget.
- **not verified**: frame time on Alex's real GPU (headless used software rendering); a second person's view (the scratch world has one person and his agent); phones (the desk window host has no phone layout).

## Rough spots (frictions found; no kernel source was edited)

1. **View state takes plain values only.** The widget broker refuses objects, arrays and null in `api.select`, so selection, stops and focus travel as JSON text. Missing: structured view values, or a documented rule (ARRANGEMENT.md says "transient selection" without the limit).
2. **`personal-view` refuses a module's line** (it takes any module actor for a painter). `map.hide`/`map.show` make the `view-preference` themselves (`sees=me`, the lens id). Missing: personal-view for a module acting for its caller.
3. **No word gives a module a file's bytes.** The map module reads the ground from the world's blob store by the digest the file thing names, and checks it. Missing: a `file-bytes` reading for granted modules.
4. **One-time GPU set-up does not fit the 32 ms part budget** (context creation and shader compiles cannot be split). It runs once, outside the part's ownership, in the ground's load continuation; everything after (input, frames, data) is owned. Missing: a declared one-time setup phase.
5. **`api.redraw()` does not repaint when the plan is unchanged**, so a panel's local toggles (an editor open) repaint the card themselves.
6. **A lens and its widget share a name**, so `look seabright-map` finds the widget; the module asks `rows lens name=…`.
7. **A module's made thing has `made_by` = the module**; whose it is shows in `for=`.
8. **Every owned animation frame adds a disposer** to the part until it is rebuilt; a long camera glide grows that list.
9. Forms do nothing in the frame without `api.P.submit` (documented; easy to miss).
10. **A repaint cancels a part's pending animation frame** but the part's own "a frame is asked" flag survives, so an on-demand renderer froze after any repaint. The engine now forgets the flag on every mount. Missing: a documented rule that owned frames end with the mount.
11. **`look "Seabright & Murray"` finds the thing named "Seabright"** (loose name match). The module now asks the ground first for any reference that is not an id. Missing: an exact-name reading, or `look` saying how sure it is.
12. **A module's do-answer text does not reach the receipt**, so `map.route` says only what it made, not `948 m · 12 min`. Missing: a module's answer line on its receipt.
13. **No word edits one line of a lens.** Changing what "add here" does means rewriting the lens text. Missing: `lens.line <lens> part=… on=add do="…"` or similar.

## Later, and kept possible

Fog over unexplored streets, spots only visible when near, a time scrubber, drawing areas (`ring=`), claiming route stretches, sun by time of day, hidden layers and lore, neighbours mapping missing buildings. Each is a layer look or a word, not a rewrite.
