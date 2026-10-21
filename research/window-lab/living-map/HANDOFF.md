# Living map seam (a7950): state at the pause, 21 Oct

worker-a7950 (builder-1). Paused by Pike (c8053) for Alex's drag-stall bug; not landed, nothing applied live.

## Built

- `research/text-desk-lab/notation/map_seam.py`: `draw(world, scope)` builds the agora-map/1 draw from kind=pin and
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

- `python research/text-desk-lab/notation/test_map_seam.py`: 16 tests OK (done-when 1-4, by name).
- `python research/window-lab/living-map/seam_browser.py`: hidden Edge on a disposable copy, and pywebview 6.2.1 with a
  js_api bridge on the sandbox desktop; every row passes, all three guards clean. Report:
  `research/window-lab/demos/living-map/2026-10-21-113259-seam/report.json`. Row 5b (Pike c8089): bridge_page.py's
  wrap of pywebview's handler refuses a bridge message whose source isn't the desk's origin (proven; not in hud.py).
  Row 'old port after a reload' (JEFF via Pike, e17339): a frame that rewrites itself (document.open/write/close)
  fires a new load but keeps its scripts, so it holds the old port and the new one; the host's old port is dead,
  its press refused out loud ('on a port from an earlier load of the frame: that port is dead'), and only the new
  port's press is answered.

## The tripwire and the Python-source question (for JEFF)

- Tripwire: rerun `python research/window-lab/living-map/seam_browser.py` after any change to pywebview, WebView2,
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

## Still to do

1. The port `hello` is in a7875 now (Pike c8089) and a7946 is told; check Rowan's frame against `seam_browser.py`.
   For JEFF to decide: the source guard of row 5b in hud.py itself (a change to Alex's home base, not this card).
2. The Handbook ("How the desk is built") passage for `/api/map` and the host page; a Rough spots note (missing
   world word: a part that holds an isolated frame and speaks a checked message seam).
3. Stage for Jeff: apply = land the branch (the door swaps deskd; nothing changes until someone opens
   `/map-host.html?session=frontier&as=alex&scope=<f>`); reversal = revert the commit. Pins and routes are residents'.
4. A HUD panel for the map (a paint word, or the host page in a panel) is not built and is not in this card.
5. Limit to keep said: in WebView2 the sandboxed frame has `chrome.webview` and its postMessage goes out without error.
   Nothing reaches Python only because pywebview 6.2.1 listens on the top document alone. Rerun `seam_browser.py`
   on any pywebview or WebView2 change.
