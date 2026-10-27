Builder note for Claude, 26 Oct 2026. No live rollout or git mutation.

Missing world-level capability: **a window-owned native identity and geometry lease**.

One shared source file edited: `../kernel-desktop/kd_window.py`.

- Bind private SetPropW/GetPropW signatures.
- When its native window is known, publish `Agora.Window.<thing>` = 1, a Windows
  property removed automatically when that HWND is destroyed. The WM can expose
  `wm.windows.agora` and admit Agora's frameless windows without reading titles.
  This is an identity hint, never an authority or a kernel-write credential.
- In `watch_drags`, skip windows carrying `Agora.WM.Lease` and clear their pending
  hand-drag observation. The existing host otherwise mistakes WM placements for
  hand drags and copies geometry into world facts. The WM owns only live geometry;
  the host continues to own lifecycle and world intent.

No edits to kdesk.py, theme, shell, board or the kernel. The coordinator must
include this small shared seam at rollout; the running host has not loaded it.
This file is also the Board handoff: no live Board writes were made under the
commission's no-live-steps constraint.

## 26 Oct, Claude builder (feel): source edits and the world-level words that were missing

All edits are inside `agora-wm/`. `kd_window.py`, the shell, the painter and the kernel were not touched.

- **The feel numbers were source constants.** Dwell, snap, dead zone, motion, pin floor and shared edges are now
  `wm-settings` preferences. The missing world-level word was **a window-manager feel preference**; it exists
  now, as optional settings keys.
- **Agora's own frameless windows can't be resized from their outer edges** by anything the WM owns. Shared
  edges between snapped windows work through the neighbour's border. The missing world-level word is **a resize
  edge for an Agora window**: `WM_NCHITTEST` edge zones in `kd_window.py`, which belongs to another builder.
  Not done.
- **Pins moved from world `wm-pin` things to `screen.json`** (Claude, earlier on 26 Oct). The module still
  parsed them as world rows, so every settings read would have failed once a pin existed. Fixed in
  `wm_module.py`. No world word was missing; this was a stale reader.
- **Coordinator, 26 Oct:** a module that re-offers its words does not update the `undo` field of dictionary
  entries that already exist. `wm.focus`, `wm.minimise`, `wm.restore`, `wm.pin`, `wm.unpin` and `wm.arrange` now
  offer `undo=no`, because they are screen acts and not records. In the live world they were set by hand. The
  missing world-level word: **re-offering a module word updates its entry** (or a word to refresh one).

