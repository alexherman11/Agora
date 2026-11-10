# Living map seam (a7950)

worker-a7950: builder-1, paused by Pike (c8053); resumed by builder-2 (below: 'Resumed round'). Nothing applied live.

## Built

- `src/text-desk/notation/map_seam.py`: `draw(world, scope)` builds the agora-map/1 draw from kind=pin and
  kind=route notes (every value parsed and range-checked; a pin that cannot be placed and a route with any bad line
  are left out and named in `problems`, for the host only). `check(world, message, scope)` turns one frame message into
  one line plus its fence, or refuses with why.
- `deskd.py`: `GET /api/map` (the draw; reads only) and `POST /api/map` (checks one message; runs nothing). The host
  sends the answered line to `/api/do` with its `observed` fence and a gesture id, so the door's routing, the fence,
  the event and its undo are the ones every press uses.
- `desk-shell/map-host.html`, `map-host.js`: the host. The frame is `<iframe sandbox="allow-scripts">`. On every frame
  load a new MessageChannel's port goes to that frame alone in a `hello`; all traffic is on the port; anything posted
  to the window is refused.
- `desk-shell/map/standin.html`: a stand-in frame speaking the contract; `#probe` tries every hostile road.

## Contract decisions built to

Pike c7997: (A) one pin id per route line, bare `a123` or `[[a123]]`; any bad line skips the whole route, said on the
host. (B) rev is the thing's revision (the fence's counter). (C) one scope surface; routes there pull in the pins they
name. (D) press is `do view <pin>`; drop is one `do create <scope> kind=pin title="New pin" label="New pin"` at 6
decimals, fenced on the scope surface. JEFF c7998: the port is the per-instance channel (asked of Pike for a7875 in
c8085; Rowan's frame must take its port from the `hello`).

## Tested (ran)

- `python src/text-desk/notation/test_map_seam.py`: 16 tests OK (done-when 1-4, by name).
- `python src/desktop/living-map/seam_browser.py`: hidden Edge on a disposable copy, and pywebview 6.2.1 with a
  js_api bridge on the sandbox desktop; every row passes, all three guards clean. Report:
  `src/desktop/demos/living-map/2026-10-21-113259-seam/report.json`. Row 5b (Pike c8089): bridge_page.py's
  wrap of pywebview's handler refuses a bridge message whose source isn't the desk's origin (proven; not in hud.py).
  Row 'old port after a reload' (JEFF via Pike, e17339): a frame that rewrites itself (document.open/write/close)
  fires a new load but keeps its scripts, so it holds the old port and the new one; the host's old port is dead,
  its press refused out loud ('on a port from an earlier load of the frame: that port is dead'), and only the new
  port's press is answered.

## The tripwire and the Python-source question (for JEFF)

- Tripwire: rerun `python src/desktop/living-map/seam_browser.py` after any change to pywebview, WebView2,
  map-host.js or the frame. In WebView2 a sandboxed frame still has `window.chrome.webview`, whose postMessage goes
  out without error; it reaches no Python only because pywebview 6.2.1 listens on the top document alone. Rows 5 and
  5b turn red the day that changes.
- Python source: pywebview gives no caller to a js_api method, but its handler sees `args.Source` (the posting
  document). Wrapping `EdgeChrome.on_script_notify` from the caller, before the window exists, refuses any message
  whose source isn't the desk's origin (row 5b; bridge_page.py, about ten lines, no package change). The home base
  (hud.py) does not do this today, and pywebview injects its bridge into whatever top document loads: every HUD frame,
  web tabs included, sits behind that one thin boundary. Adding the wrap to hud.py is a change to Alex's home base,
  for JEFF to stage.
- `sandbox_window.Guard` now takes its first reading from a fresh thread: guarding two sandboxes in one process gave
  a false FAIL before (foreground 0, cursor (0, 0)).
- `test_scene.py`: 58 passed.

## Resumed round (builder-2, 21 Oct; Pike c8178, c8181, c8227)

- The real frame: deskd serves ground's four frame files (map.html, map.js, geo.js, fixture.js) from
  research/map-lab/ground under `/map/ground/`, nothing else of that folder; `map-host.html?...&frame=ground` holds it.
  The stand-in stays the default and the battery's frame.
- Found with Pike's real pins (f8161: icon=museum, pub, church): the frame refused every one, because its icon check
  took only up to 4 characters (a named colour would have been refused the same way). Now an icon or colour the frame
  cannot draw is left off and said, and the pin is still drawn; a word icon is drawn as its first letter, a colour is
  #rrggbb or a colour's name. The contract (a7875) says nothing of their form: asked of Pike (c8520).
- Found by timing: the frame rebuilds its pins on every draw, and the host sent one after every world event, changed
  or not; a draw landing between a pointer's down and up lost the press (2 of 20 real presses). The host now sends a
  draw only when it differs from the last, except after an answer (always: a refused move's pin must go back). It
  also draws an answer back at once, not after the 80 ms gather. A real change to a pin mid-press can still swap
  the element under the pointer: for ground, keeping unchanged pin elements across draws would close it.
- `real_frame.py` (ran, hidden Edge on a copy, guard clean; report demos/living-map/2026-10-21-143923-real): f8161 in
  the real frame. ready, 1 lat by line (the pin moved on screen), 2 a real drag is one event and is undone, 3 the route
  in order after a rename, press (do view), drop (a real double-click on ground, one create at 6 decimals, undone): all
  pass. Timing, 20 real presses, at 1280x800, scale 1.5, on Windows 11, an RTX 2080 Ti (ANGLE D3D11) and Edge in the
  sandbox: the pin marked selected p95 10 ms. Press to the world's answer drawn back: p50 150, p95 192, max 238 ms,
  over the contract's 100 ms. Of that, p50 is 18 ms for the host's check (/api/map), 119 ms for /api/do (the desk's
  own write path, which every press in the HUD pays) and 21 ms for the redraw.
- `seam_browser.py` again after the host changes (ran; demos/living-map/2026-10-21-144005-seam): every row passes,
  three guards clean.
- health frontier-try (e18856): all green.

## For JEFF: apply and reversal (nothing is live)

Apply: land the branch. The door swaps deskd at its next start (a landing restarts it; no restart is asked here).
Nothing changes for Alex until someone opens `/map-host.html?session=frontier&as=alex&scope=f8161&frame=ground`;
no HUD panel or lens points at it. Pins and routes are residents' notes and need nothing applied.
Reversal: revert the merge. The only world events the map makes are ordinary ones (prop on a pin, create in the
scope, view) and each is undone by its own event.

## Still to do (not this round)

1. For JEFF to decide: the source guard of row 5b in hud.py itself (a change to Alex's home base, not this card).
2. A HUD panel for the map (a paint word, or the host page in a panel) is not built and is not in this card.
3. Limit to keep said: in WebView2 the sandboxed frame has `chrome.webview` and its postMessage goes out without error.
   Nothing reaches Python only because pywebview 6.2.1 listens on the top document alone. Rerun `seam_browser.py`
   and `real_frame.py` on any pywebview, WebView2, map-host.js or frame change.
4. Ground's own measure.py was not rerun after the icon change (its draws use #hex colours and one-character icons,
   which take the same road as before).
