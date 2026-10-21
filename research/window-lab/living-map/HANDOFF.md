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
  js_api bridge on the sandbox desktop; every row passes, guard clean on both. Report:
  `research/window-lab/demos/living-map/2026-10-21-112508-seam/report.json`.
- `test_scene.py`: 58 passed.

## Still to do

1. Pike puts the port `hello` in a7875 and tells a7946; check Rowan's frame against `seam_browser.py`.
2. The Handbook ("How the desk is built") passage for `/api/map` and the host page; a Rough spots note (missing
   world word: a part that holds an isolated frame and speaks a checked message seam).
3. Stage for Jeff: apply = land the branch (the door swaps deskd; nothing changes until someone opens
   `/map-host.html?session=frontier&as=alex&scope=<f>`); reversal = revert the commit. Pins and routes are residents'.
4. A HUD panel for the map (a paint word, or the host page in a panel) is not built and is not in this card.
5. Limit to keep said: in WebView2 the sandboxed frame has `chrome.webview` and its postMessage goes out without error.
   Nothing reaches Python only because pywebview 6.2.1 listens on the top document alone. Rerun `seam_browser.py`
   on any pywebview or WebView2 change.
