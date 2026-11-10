# The map (agora app)

*Builder draft by Claude, 27 Oct 2026, from Alex's asks: first "a good quality viewer for the map … a very agora native component … easy to inspect, edit, and augment, manage layers, and add places, events etc through the desk language … malleable, that's the key"; then, the same evening, "get rid of the curved world, make it flat … missing a fair number of structures … cover more area (at least California) … load it live? … no transparency … an interface that encourages people to modify and expand on the map … structures should be clickable and have their own little pages … a town hall which when clicked shows upcoming meetings, debates in comments … a house could show a party". The design page Alex was shown: https://claude.ai/artifact/W1s98XVfo5PFc7ADDYatRu.*

A flat 3D map of the whole world, opening on Seabright, as a window on the kernel desktop. It holds nothing of its own. Everything it shows is a world thing or open map data, and everything it does is a line.

## The ideas

1. **Anything can have a place.** A thing is on the map when it says `lat=` and `lon=`; or `at=` naming a placed thing (a party at a house moves with the house); or, approximately, a `location=` the map can find by name (drawn with a striped pin).
2. **The ground is live.** Streets, water, land and names come from OpenStreetMap through OpenFreeMap's vector tiles; buildings come from Overture Maps, which adds machine-traced footprints where OpenStreetMap has none (in Seabright's tile, 515 of 1,263 buildings). Tiles are fetched only where someone looks, then kept on disk. California, or anywhere, works the same way; nothing is downloaded up front.
3. **A building is ground until someone needs it.** Press any building to see what it is. The first time something is put at it (a party, a note), or someone gives it a page, it becomes a world thing: `kind=structure ref=overture:<id>`, named by its OpenStreetMap name or its address. Anything can then point at it, and posts can be about it.
4. **A place has a page, and the page is a lens.** A structure opens in a page window (`window.open <page> <structure>`). Which page: its own `page=`, else the page whose window widget says `places=` with its kind (town halls open the town-hall page: meetings, agenda, debates; houses open the home page: parties, guestbook), else the general place page. A community adds a page for its library by writing a lens and a widget with `places="library"`; no code changes.
5. **Layers are things.** `kind=map-layer`: a reading (`rows event`, `rows spot tags=dogs`, `map.near "Seabright & Murray"`, `board.…`) plus a look (pin, dot, little house, name, path) and a colour. **+ Add a layer** starts from a gallery, shows how many things the reading finds, and makes it for everyone or only you. Hiding a layer is your own view preference; the layer stays for everyone.
6. **The window is arranged.** `map.lens` is an ordinary component lens: map, search, inspector, route planner and layers, each gesture naming the line it runs (and every card prints its lines). Change a line and "Add" does something else.

## Words (module `map`, `modules/map/map.py`)

| Line | What comes back |
|---|---|
| `map.find Seabright & Murray` | the corner, `36.96702, -122.00785` (ran). Things, places, streets and corners near the map, then towns and addresses further away (Nominatim) |
| `map.where 36.9640,-122.0050` | `16 m from 4th Avenue, 56 m from East Cliff Accent` (ran) |
| `map.near <thing> within=300` | placed things you can see, nearest first, with metres |
| `map.place <structure or overture:id> [lat= lon=]` | a building's facts, which page it opens in, the things at it and the posts about it |
| `map.add <place> kind=event title="Halloween party" start=…` | puts something at a place; a building becomes a structure on first use (ran: two things made in one act) |
| `map.adopt overture:<id> lat= lon= [name=]` | makes a building a world thing without adding anything |
| `map.path stops="a > b > c" [mode=bike]` | a street path as a reading (nothing is made) |
| `map.route name="…" stops="a > b > c"` | makes a route thing that keeps its path, metres and minutes |
| `map.layers Seabright` | the map, then every layer with its placed rows (what the window watches) |
| `map.hide <layer>` / `map.unhide <layer>` | your own view only; also `buildings`, `shadows`, `labels`, `places` |
| `map.style day\|dusk\|night\|paper` | how your own map looks |
| `map.show <thing\|name\|lat,lon>` | turns your open map window there |
| `map.tile 14/2639/6379` | one tile, as the window draws it (format `agora-tile/1`, see `modules/map/tiles.py`) |
| `map.cache [trim=2]` | how much ground this machine keeps; trim forgets the oldest tiles down to 2 GB |

Kinds: `spot`, `map`, `map-layer`, `route`, `structure` (and the world's own `event`, `note`, `post`).

## The window

`window.open seabright-map`, or the **Seabright map** button on the taskbar.

- Drag to move, scroll to zoom, right-drag (or Ctrl-drag) to turn and tilt, double-click to zoom in. Keys: arrows/WASD, `+`/`-`, `Q`/`E` turn, `N` north, `T` tilt, `Esc`. Buttons along the bottom: zoom, north, 2D/3D, back to Seabright, all of California.
- **Look**: press a building, street, park, name or pin. A building's card says what it is (and if it was traced from imagery), what is at it, the talk about it, and **+ Event here**, **+ Note**, **Give it a page** or **Open its page**.
- **Add**: a spot, an event, a note, or any kind, at a building or a point. The sheet prints the line it runs.
- **Route**: press stops; the planner shows metres and minutes; Save makes the route; a route's flag opens it and **Fly along it** rides the street.
- **Layers** (right): tick for you, `⋯` to change, copy or remove, **+ Add a layer**, the ground's own layers, and the look (Day, Dusk, Night, Paper).
- **New on the map** (left, when nothing is pressed): the latest placed things, who added them, and when.

A place's page: a small live 3D view of the building (highlighted), its name and kind, Show on the map, Rename, and the page's sections (each a `place-list` or `place-talk` part with its own add line).

## Files

| File | |
|---|---|
| `geo-worker.js` | builds one tile's GL geometry off the window's thread (earcut after Mapbox's, ISC) |
| `geo-engine.js` | flat Web Mercator world, tile choice by distance, stand-in tiles while loading, roads with a minimum on-screen width, buildings, shadows, picking, names and pins, four looks |
| `map-components.js` | the ten components (map window and place pages) |
| `map.lens`, `pages/*.lens` | the map window; the place, town-hall and home pages |
| `install.py` | everything above as lines; `--live` installs into the desktop world (opens nothing) |
| `scratch.py`, `look.py`, `proof.py`, `say.py` | hidden scratch world, hidden browser, the evening below, one line to a kept-up scratch world |
| `../../modules/map/map.py`, `tiles.py`, `mvt.py`, `ground.py` | the words; live tiles (fetch, cache, cut); a vector-tile reader; finding names, `where`, routes (A* over streets) |
| `research/map-lab/seabright/` | the first pass's one-file Seabright ground (still readable: a map may name `ground=<file>`) |

Data and licences: OpenStreetMap contributors (ODbL), tiles by OpenFreeMap; buildings by the Overture Maps Foundation (OpenStreetMap and machine-traced footprints); place search by Nominatim (once a second at most, answers kept). The window's footer says so.

## Evidence

- **ran** `proof.py`, 27 Oct evening, hidden world and headless Chrome with a software GPU (SwiftShader): 26 of 26 steps pass (`evidence/proof-output.txt`). A person opens the window on live tiles; presses a house and sees nobody has put anything there; puts a Halloween party at it (the house becomes a structure, the party points at it); says something in the card; opens its page in a window; leaves a note on the page; City Hall, adopted in a line, opens in the town-hall page by its kind; a meeting and a debate post there; + Add a layer (Notes) and an only-me layer; Dusk; Buildings hidden for you; Capitola found and flown to; a walk planned and saved (1.1 km); all of California and back; a line-made spot appears live; a pin dragged; no script errors. Pictures: `evidence/proof-*.png`.
- **ran** routing over the live tiles, Seabright & Murray to the east harbour: first 3,870 m (only 64% of the street network connected: vector tiles keep no topology), then 1,113 m after noding crossings and loose ends (98.5% connected), against 1,105 m over the first pass's OpenStreetMap extract.
- **ran** a frame over Seabright in 3D: 0.9 ms median on the software GPU; first open 3.5–4.8 s with a warm cache (the first visit to a place fetches its tiles: about 1 s a tile, four at once).
- **ran** the painter suite (8 tests) and the widget/window suites (10) after the three-file source edit below.
- **not verified**: frame time on Alex's GPU; a second person's view (the hidden desk has one person); a real native window opening on a target (the hidden desk keeps windows in memory only); phones.

## Rough spots

Kernel and painter frictions (no kernel source edited for the map, except the one window edit noted):

1. **View state takes plain values only.** Selection, stops and focus travel as JSON text.
2. **`personal-view` refuses a module's line.** `map.hide`/`map.style`/`map.show` make the `view-preference` themselves.
3. **No word gives a module a file's bytes**, and no channel gives a part bytes from a module: tiles travel as readings (`map.tile`, about 250 KB of JSON for a town tile). Fine at this size; a `bytes` reading would be lighter.
4. **One-time GPU set-up does not fit the 32 ms part budget.** It runs once, just after the first layers reading, outside the part's ownership.
5. **`api.redraw()` does not repaint an unchanged plan**, so panels repaint themselves.
6. **A lens and its widget share a name**, so `look seabright-map` finds the widget; the module asks `rows lens name=…`.
7. **A module's made thing says `by=map`**; whose it is is in `for=`. The module now shows the person (`for=`) wherever it lists things.
8. **Every owned animation frame adds a disposer** until the part is rebuilt.
9. Forms do nothing in the frame without `api.P.submit`.
10. **A repaint cancels a part's pending frame**; the engine forgets its "frame asked" flag on every mount.
11. **`look "Seabright & Murray"` finds the thing named "Seabright"**; the module asks the ground first for names that are not ids.
12. **A module's do-answer text does not reach the receipt.**
13. **No word edits one line of a lens.**
14. **A window opened on a thing did not tell its lens which thing** (source edit, logged in `painter/ROUGH-SPOTS.md`): `kd_window.py`, `widget-host.js` and `painter.js` now hand it over as `$view.target`.
15. **`sees=` is not readable**, so a layer made only for you also says `only=me` for the panel to label it.
16. **A refused reading stops a whole page from painting**; `map.place` answers empty, not refused, when no place is chosen.
17. **A watched reading cannot follow a selection** (it would need a view value inside the reading), so a building's card reads its place again itself after you Say something.
18. **A page window is named after its lens** ("Place"), not the place it shows. Missing: a window name from its target.
19. Data, not kernel: **vector tiles keep no topology**, so `tiles.node_roads` splits crossings and snaps loose ends before routing.
20. **Code swapped under an open window can quarantine its parts.** Installing writes a component's code, then reviews it; an open window repaints in between, runs the unreviewed code isolated (no `api.draft`), fails, and after two failures the part is quarantined, also for the next window (ran, 27 Oct, live: `component-action seabright-map path=root/map action=clear` then `retry` mended it). `install.py --live` now closes the map's own windows first and reopens them after. Missing: writing code and its review as one act.

21. **A long-lived surface was always quarantined in the end** (28 Oct, Alex: "your map shows blue only"). Every slow callback counted for the life of the window; on a 4K screen the map was quarantined, and in quarantine it cannot draw (no WebGL in a worker). The painter now counts slowness only when it repeats within 10 s (source edit, `painter/ROUGH-SPOTS.md`), and a paused map says so and offers **Start the map again** (`on resume do component-action … action=clear`, a steward's word). Missing: a part's frame budget; the first error kept, not only the latest.

## Later, and kept possible

A tour of the neighbourhood (a route through layer things), events on a timeline scrubber, drawing areas (`ring=`), fog over streets nobody has walked, sun by time of day, photos on a place's page, a library page and a shop page by `places=`, prefetching a whole county (`map.cache keep=`), routes across counties (a routing service), and a phone layout once the desk window host has one. Each is a layer look, a page lens or a word, not a rewrite.
