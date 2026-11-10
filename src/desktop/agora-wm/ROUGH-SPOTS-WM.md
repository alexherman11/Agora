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

- **Claude, 27 Oct: the WM grabbed the dock and minimised Alex's Claude window after a window-module restart.**
  Two moments when a window looked like something it was not: a bar was shown before it became a tool window, so
  for a tick it was a visible frameless Agora window, and the WM planned it as a tile (the dock ended up
  3818×36); and a window tucked before the restart was shown and only then tucked, so the WM took it for a new
  window and minimised the least recently used one, Alex's Claude window, to make room. Fixed in `kd_window.py`:
  bars are tool windows before they are shown, and tucked windows come back already tucked. The missing world-level
  word: **a window's role (bar, tile, layer) that the host declares and the WM reads**, instead of the WM inferring
  it from window styles at whatever instant it looks.


## 27 October 2026 — adaptive visibility

See [adaptive WM handoff](ADAPTIVE-20261027.md). Missing world words: preserve-visible placement and causal displacement restoration. Source changes confined to engine.py / manager.py and focused tests/proof. No live activation.

## 28 October 2026 — live comes back by itself (Claude)

Alex: "the window manager keeps booting into non-live mode (bruh)". Every restart of the wm module (about 19 in two
days: kdesk restarts, module restarts by other sessions) came back in shadow, and a lease lost to a missed heartbeat
went off and stayed off, because only a *new* `wm.mode live` request could arm it. Source edit in `wm_module.py`: the
world's mode is the standing choice; restarts and non-panic lease ends re-arm from it once the gate is clear; the panic
chord holds it out until a new request. Missing world-level word: **a standing intent versus a one-time request**: a
setting a module should keep honouring across its own restarts, kept apart from a request that happened once.

## 28 October 2026 — restore intent survives pending native work

Builder draft for review. Missing world-level handle: **the latest window visibility
intent supersedes an outstanding native operation**. `wm.restore` previously only
cleared displacement and called Windows; the layout could keep the window minimised.
`manager.py` now solves explicit restore/minimise intent, replaces stale pending
work, and recognises an external restore during the acknowledgement interval.
Both restore routes wait for native geometry to settle before placement, using the
existing restore acknowledgement. Regressions live in `test_adaptive.py`; the
guarded, HWND-allowlisted `hidden_restore.py` exercises four native fixtures and
repeated dock/external restore races. No live activation or real Spotify launch.

## 2 November 2026 — policy handoff without geometry release (dk1706)

Builder draft for independent review. Missing world words: **reload compatible
WM policy while retaining its screen state and lease**, and **return to the
previous policy generation**. `policy_reload.py`, `wm_module.py` and the strict
read-only context in `win32_host.py` add wm.policy/reload/rollback using the
existing WM thread and watchdog. Constructors, native safety and controller/
engine/lease ABI are frozen. No process replacement or live activation occurred;
the old live module lacks a receiver, so bootstrap remains blocked.

`shell-kit.js` also retains plain focus for pinned dock entries; the landed
share route rejected them. Focused fake-native/controller and dock-component
checks are supplied for House execution. See `POLICY-RELOAD-dk1706.md` for
refusals, rollback, exact guard rejection and remaining native acceptance.

## 2 November 2026 — review correction: live replacement is unavailable

Supersedes the preceding handoff design. The missing world capability cannot
be provided safely by the existing watchdog lifecycle within current bounds.
Removed live staging/class swapping and its native helper. wm.reload/rollback
now refuse before source/native/lease/queue work; wm.policy reports scoped
imported code objects instead of relabeling disk bytes as loaded code.
The ordinary WM runtime/native safety/watchdog is retained. Memory-only
provenance/refusal checks passed (8 tests); focused fullscreen/native acceptance
remains separate and unrun. POLICY-RELOAD-dk1706.md records the exact WM-only
lifecycle exception and geometry/claim effects that JEFF would need separately
authorized; no such operation occurred.
