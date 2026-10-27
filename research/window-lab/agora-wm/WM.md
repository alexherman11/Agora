# Agora WM — builder handoff

Builder: Codex, 26 October 2026. For Claude's review and commit. **Nothing installed
into, stopped or restarted on the live desktop. No git operations.** All mutations
during proof targeted allowlisted windows on a never-shown desktop. The two-minute
real-desktop observations were read-only. No session pickle was read.

## Files and shared seam

New code in this folder:

| Files | Purpose |
|---|---|
| `engine.py` | Pure integer-pixel solver, state, events and invariant checker |
| `simulator.py`, `proof.py` | Pillow renderer, JSON replay, layered proof entry point |
| `win32_host.py`, `native_identity.py` | Private ctypes boundary, filtering, identity, frame compensation, events |
| `manager.py`, `ghost.py` | Shadow/live policy host and deferred click-through neighbour previews |
| `watchdog.py` | Independent recovery process, durable leases and panic hotkey |
| `wm_module.py`, `install.py` | Module protocol and print-only genesis/install preparation |
| `hidden_proof.py`, `test_*.py` | Real hidden windows, pure invariants, controller and kernel integration |
| `evidence/` | PNGs, replay, timing, transcripts, shadow report and runtime recovery receipts |

One shared source file changed: `../kernel-desktop/kd_window.py`. It publishes
`Agora.Window.<thing>` = 1 on its HWND, and its existing hand-drag watcher skips
windows carrying `Agora.WM.Lease`. This supplies `wm.windows.agora` without title
matching and prevents WM geometry from becoming world facts. Private SetPropW /
GetPropW signatures were added. See [Rough spots](ROUGH-SPOTS-WM.md). No changes to
`kdesk.py`, the kernel, theme, shell or board. The running host has not loaded this seam.

## Design as built

**Read:** [CONTRACTS §2](CONTRACTS.md), [RESEARCH](RESEARCH.md), the old `wm.py` /
`test_wm_release.py`, sandbox rig, module protocol and desktop host/guard sources.
The existing house door refused `read a6529 :3` with “no such id”; the supplied
standing-rule snapshot was used. No world was recreated or changed to find it.

`solve(state, event)` deep-copies its input and returns a `Result`. Unpacking gives
`placements, minimise, notes`; `result.state` is the next state. Rectangles are
`Rect(x, y, width, height)` in physical screen pixels. State holds preferred and
learned minimum dimensions, recency, pins, management, work area and fixed obstacles.
All event types in the commission are supported; resize events carry their final
rectangle, so the same mechanism handles every edge and corner.

The engine splits available space into maximal empty rectangles and scores fitting
candidates by displacement, unused space and coordinates, with deterministic ties.
An open preserves every surviving existing window. Full policies apply only when
the preferred size cannot fit. An impossible new window stays minimised and rolls
back unnecessary minimisations of existing windows.

A gesture first pushes only its collision-connected neighbours, preferring the axis
of least overlap. Bounded backtracking tries other directions, then minimum-size
shrinks, then LRU minimisation. If fixed geometry blocks it, the gesture clamps along
the path from its last legal rectangle. A search budget bounds cascades. `arrange`
preserves already legal rectangles. Gentle reflow only grows existing windows in
place, at most one eighth of preferred dimensions per close/minimise event.

Pins never move in the engine. Native pins are fixed at the person's actual
placement. Unmanaged windows are fixed obstacles. Existing obstacles may overlap
one another; the manager does not claim it can repair that without moving them.
Impossible fixed geometry produces an explicit note and the live host fails closed.
The movement tests prove zero avoidable moves for legal re-solves, free opens and
the unaffected component; **no global optimal-layout theorem is claimed**.

## Native boundary and drag

`Native()` cannot mutate unless explicitly armed. Every mutation checks PID,
creation time, executable, HWND, thread and class, and rejects elevated/inaccessible
processes. Hidden tests additionally supply an HWND allowlist. No window title is
read by this WM. The host admits visible, top-level, captioned, non-tool, non-child,
non-cloaked windows. A known Agora identity or a native app rule can admit frameless
windows; otherwise they are obstacles. App exclusions are world intent.

Out-of-context WinEvent hooks feed a bounded queue. A message pump delivers create,
show/hide, destroy, focus, minimise/restore, modal move/size start/end and location
events. Polling also reconciles lost events, disappearances, work-area changes,
self-resizers and actual placements. The primary work area comes from Windows'
SPI_GETWORKAREA, including Agora's existing AppBars. DPI awareness is per-monitor v2.

Placement measures GetWindowRect against DWMWA_EXTENDED_FRAME_BOUNDS, then uses
SetWindowPos with NOACTIVATE, NOZORDER, NOOWNERZORDER and ASYNCWINDOWPOS. Restore is
asynchronous and frame margins are measured afresh on the next tick. Read-back after
350 ms learns excess minimum dimensions; repeated size/position refusal, or refused
minimise/restore, removes the window from management. Minimise/restore are real
ShowWindowAsync operations, never cloak. Close posts WM_CLOSE; focus respects
Windows' foreground lock and reports refusal, without synthetic input.

During a native move/size gesture the base layout is retained. The moving window's
actual rectangle is solved against that base; click-through, no-activate, tool,
layered Agora windows preview neighbours. Neighbours move only at release.
`drag=live` is recognised but refuses activation until it passes a smoothness gate.
No live-drag execution was attempted. The hidden slow fixture exceeded a frame budget.
Transient cross-process placement is asynchronous: the pure/final layout invariant
does **not** prove that every intermediate compositor frame is overlap-free.

Theme delivery defaults to the sibling module's `theme/theme-native.json`, or the
explicit `--theme-native` path. Valid changes update gaps, border colours and corner
preference. Focused/unfocused/pinned colours are applied with DWM and reset on release.
Border-only leases do not restore geometry unless later upgraded for an actual move.
Gaps are used as physical pixels in this version. DWM's system border thickness is
not replaced with a custom-width overlay; `border_width` cannot control that API.

## Words, readings and intent

All twelve offers have help. Only the desktop owner, its stewards and their agents may
inspect or control this personal native surface.

*Claude, 27 Oct 2026:* Alex made JEFF a steward (`role dk827 leader in=dk1`) so JEFF could put
the desk in live mode. The module now also admits stewards, read once a second with `who`
(granted by `grant wm words="who"`). **ran**: before, JEFF's `wm.windows` was refused; after,
`20 windows; shadow`, and JEFF's own `wm.mode live` (r1560) left it `20 windows; live`. `wm.changed` announces JSON text
`{"keys":[...]}` at no more than ten announcements per second; it carries no titles.

| Word | Behaviour |
|---|---|
| `wm.windows` | Live rows, no world record or titles |
| `wm.focus <key>` | Request foreground; ordinary Windows restrictions apply |
| `wm.minimise <key>` / `wm.restore <key>` | Native actions in live mode |
| `wm.close <key>` | Polite close request, never process termination |
| `wm.pin <key>` / `wm.unpin <key>` | Undoable `wm-pin` intent; geometry stays in memory |
| `wm.arrange` | Re-solve, preserving legal windows |
| `wm.mode live|shadow|off` | Undoable mode request; applied only after admission |
| `wm.leave-alone <app>` / `wm.manage <app>` | Undoable exclusion / adoption intent |
| ~~`wm.changed`~~ | Removed 26 Oct (Claude, from Alex: "visual state should not live in the world"); the shell polls `wm.windows` each second |

Rows contain exactly `key, app, exe, icon, agora, state, focused, rect, space,
managed, why`. `icon` is the executable path for the shell to resolve. `agora` is
the window thing from the native marker, otherwise null. `space` is currently
`primary`. State is `normal|minimised|pinned`. No titles enter rows, shadow logs,
leases or module announcements.

One `kind=wm-settings`, named `wm-settings`, holds intent:

| Setting | Values | Default |
|---|---|---|
| `when_full` | minimise-oldest, fill, focus | minimise-oldest |
| `manage` | all, adopted | all |
| `drag` | ghost, live (activation refused for now) | ghost |
| `never` | App-name list (JSON list or comma-separated text) | [] |
| `reflow` | none, gentle | gentle |
| `mode` | shadow, live, off | shadow |

The module also maintains an admitted mode-request nonce and an adopted-key list.
World writes are returned as ordinary lines with `saw` fences. Pin notes contain
app/key/active intent, never rectangles. Undo is handled by the kernel. Native
focus/minimise/restore/close are external acts; undo cannot reverse those screen effects.

## Safety and recovery

Shadow is the default and has no lease, preview window or write-capable boundary.
`--allow-live` is required in addition to a newly admitted `wm.mode live` request.
A previous world's live setting never arms a restarted process automatically.
Panic or guard death ends management without rearming from that old request.

The independent watchdog starts through WMI outside the manager's process/job tree,
following `taskbar_guard.py`. A normal subprocess was insufficient: the crash proof
showed the venv launcher's job ending its child. The private loopback channel uses
an ephemeral token, newline JSON and acknowledgements; it is not a kernel endpoint.
Only the guard writes the lease. It fsyncs and atomically replaces the saved JSON
before acknowledging a save, with bounded retries for transient Windows reader locks.

Each lease contains process identity, WINDOWPLACEMENT, previous readable DWM values
and a per-HWND cookie. The cookie prevents reuse of a destroyed HWND within the same
process from restoring an unrelated new window. Release is idempotent, records
progress, and leaves unmatched identities/cookies untouched. Border colour resets
to DWMWA_COLOR_DEFAULT where Windows cannot read its previous value. Geometry
restoration uses asynchronous WINDOWPLACEMENT. The manager has mutual recovery if
the watchdog itself dies; that fallback is implemented but not crash-proven here.

The guard owns Ctrl+Alt+Backspace. It releases on manager identity loss, pipe loss,
three seconds without a heartbeat, explicit off, or WM_HOTKEY. `wm.mode off`, module
off and panic share the same release-all. Heartbeats continue during game gating;
gating must not accidentally cause a timeout restoration during a game.

The host combines `gaming_gate.py` and SHQueryUserNotificationState. Busy,
presentation, full-screen, unavailable or inaccessible notification states stop
layout processing and native actions. Resume starts from actual geometry, discarding
stale gestures. The two-minute live observation remained gated as state 2 (busy).

*Claude, 26 Oct 2026:* the busy state was not a game. **ran** a read-only scan: the foreground
window was `TextInputHost.exe` (the touch keyboard / emoji panel), a 3840×2160 CoreWindow, and
`NVIDIA Overlay.exe` holds two screen-sized windows too; Windows reports QUNS 2 while such a shell
window has the foreground. `gate()` now treats state 2 as gated only when the foreground program is
not one of `SHELL_OVERLAYS`; states 1, 3, 4 and 7 still gate. **ran** `shadow.py --seconds 120`
afterwards: 412 samples, `gated_samples: {}`, nine apps seen; it would move ChatGPT and Spotify and
minimise the rest (`evidence/shadow-ungated-20261026.summary.json`). That is the "screen full →
minimise oldest" rule applied to a desktop of overlapping windows all at once, including the Claude
window Alex is talking in. Before arming live, decide how the first solve treats windows that were
already open (adopt as they are, or arrange once with Alex watching).

*Claude, 26 Oct 2026, ~20:45: live.* Alex: "visual state should not live in the world, let the tiling manager
organize the existing windows." So `manage=all`, installed in his world (`wm-settings` dk531, `module wm` with
`--allow-live`) and armed with `wm.mode live`. Changes that went with it:
- **No screen state in the world.** Pins and adopted windows now live in `<home>/screen.json` (`wm.pin`/`unpin`
  are screen acts, not records); `wm.changed` is gone (it flooded Lines with window keys; the dock polls
  `wm.windows` each second); `kd_window` keeps window geometry in `state/geometry.json`, never `set at= size=`.
  `wm-settings` keeps preferences only (when_full, drag, reflow, never, mode).
- **Gate 2 again.** **ran**: QUNS 2 with `claude.exe` (an ordinary window) in front, while Agora's desktop layer and
  the Claude app's screen overlay were screen-sized. State 2 now gates only if the foreground window covers its
  monitor (`_foreground_covers_monitor`).
- **No squashing.** **ran** the first live arrange: Task board and Help came out 161 px tall (minimum 240×160). An
  arrange now minimises a window rather than give it under `SQUASH` (60 %) of its usual width or height;
  `test_engine.SquashTests` replays that desktop.
**ran** after: `17 windows; live`, four Agora windows tiled without overlap, none under 60 %. Not verified: a new
window opening onto a full screen live, drag push-aside live, the panic chord pressed by hand.
No Windows setting, taskbar, registry entry, driver, injection or wallpaper is changed.

## Reproduce and rollout — Claude operates these

All commands use `C:/Projects/Agora4/.venv/Scripts/python.exe`, from this folder.

```text
python proof.py --l0
python proof.py --l1
python -m unittest test_engine test_manager test_watchdog test_source_seam test_module_kernel -v
python shadow.py --seconds 120 --out evidence/<fresh-name>.jsonl
python shadow.py --report evidence/<name>.jsonl
python simulator.py evidence/day.replay.json evidence/replayed-day
python install.py
```

`install.py` only prints a genesis fragment; it does not connect to any desktop.
Merge its module and settings into the intended genesis, or review the ordinary
words printed by `--lines` for an existing world. Prefer the genesis fragment: it
includes the explicit `for=steward` and kind-narrowed grant. Use `--headless` for a
disposable protocol trial. Do not duplicate `wm-settings`.

For live rollout, Claude must review these changes and the shared native seam,
connect the shell to the words/row fields, confirm the theme sheet, then run a fresh
shadow interval while Alex works. Investigate the persistent busy gate before
claiming a useful live layout trial. With Alex present, explicitly use the module
spec generated with `install.py --allow-live` and issue a new `wm.mode live` request.
The hotkey must still be free at acquisition; the guard refuses if it is taken.
Keep the shell's off button wired to `wm.mode off`. Check real Chrome/Electron apps,
pins, restore and release with Alex before calling this live-accepted.

Recovery after a dead manager, if needed:

```text
python watchdog.py --release-all <world>/modules/wm/lease.json
```

It refuses a still-live owner; it does not steal an active lease. Never point it at
unrelated recovery files. Runtime lease fixtures in `evidence/` are proof receipts,
not deployment configuration.

## Evidence — ran, with boundaries

L0: **2,000 seeded sequences × 30 events = 60,000 events**. Random inner/outer gaps,
obstacles, all full policies, feasible work-area changes, pins, minima, drag/resize,
purity, replay determinism, in-bounds/gaps/non-overlap, finite completion, idempotent
re-solve and movement-preservation assertions. Six engine tests passed. Fifteen
host/module/recovery tests passed separately, including a real `wm` process behind
a disposable kernel HTTP door. Two existing headless desktop lifecycle/undo tests
passed (`Ran 2 tests in 6.217s`). See `evidence/*output.txt`.

Fourteen scenario PNGs and `day.replay.json` cover all commissioned scenes. I
inspected every scenario in the contact sheet, including the resize and drag pair.
See [contact sheet](evidence/contact.png); the individual PNGs remain in `evidence/`.

Solver timing, 200 updates per window count (the sparse timing case, not a worst-case
packing benchmark), printed by the final L0 run:

| Windows | Median ms | p95 ms | Max ms |
|---:|---:|---:|---:|
| 5 | 0.298 | 0.349 | 1.545 |
| 15 | 0.811 | 1.056 | 1.214 |
| 40 | 2.223 | 3.38 | 4.219 |

L1: ordinary, frameless, enforcing-minimum, self-resizing and slow native windows,
on a never-shown desktop. Final results and per-test foreground/focus/cursor/input-
desktop snapshots are in `evidence/l1.json` and `l1-output.txt`. An earlier complete
run printed **`L1 passed; alex: untouched`**. The latest run
printed **`L1 passed; alex: concurrent input; see per-test snapshots`**: foreground,
focus and input desktop remained identical, while Alex's cursor moved. These
changed snapshots are retained; the latest run cannot certify an unchanged cursor.

- Frame-compensated placement: requested/read back `[220,180,1000,720]`, **0 px error**.
- Real minimise/restore passed; frameless became an obstacle; the Agora marker admitted
  its tagged frameless fixture without a title read.
- Minimum refusal: asked `240×160`, read back and learned `482×341`; the integrated
  controller learned it and verified **actual and planned non-overlap** across five windows.
- Slow app: enqueue **0.398 ms**, settled **84.393 ms** in that run.
- Hidden hooks delivered **11 events**, including create/destroy, location, minimise,
  restore and modal start/end. Modal start/end came from fixture NotifyWinEvent,
  not a physical drag; show/focus delivery is not separately established hidden.
  Polling remains the reconciliation fallback.
- DWM set HRESULTs: **0 for both attributes**. Corner set/read/reset passed.
  Border-colour getter was unavailable here; reset to the system default was sent.
- Killing the manager: restore **43.313 ms**, repeated release no-op.
- Live manager with heartbeat withheld: restore **3057.995 ms**, reason `heartbeat expired`.
- Panic: registration, posted WM_HOTKEY dispatch and restoration passed. No physical
  key chord or SendInput was sent. The real-desktop momentary hotkey probe printed
  `{"free": true, "error": 0}`; availability is rechecked at live acquisition.
- Ghost: **120 updates, 58.591 Hz**, median **3.997 ms**, p95 **5.837 ms**. These are
  hidden API updates including solve/overlay work, not measured compositor presentation.
  Live drag FPS is unmeasured and live drag stays disabled.

L2: `shadow-apps-20261026.summary.json` printed **421 samples, 120.109 s,
2,872 hook events, native_mutating=false**. Apps: ChatGPT, Discord, Spotify,
WindowsTerminal, chrome, claude, explorer and python. All 421 samples were gated by
`notification gate 2`; **zero planned moves or minimisations**. An earlier independent
120.016 s interval likewise stayed gated (416 samples, 3,230 events). These prove
read-only observation and gate behaviour, not usable live layout on Alex's applications.

## Not done / limits for acceptance

No live installation, shell integration, desktop restart, commit or push. No real
Chrome/Electron layout acceptance, physical panic chord, visible drag/compositor
smoothness, multi-monitor placement or spaces. No global optimal-movement proof.
Native transitions can temporarily overlap while async placements settle.

The MIT application database was not supplied and was not fetched/copied. Native
app-rule support exists, but a distributed app-quirk seed and its MIT notice still
need coordinator review/provision. No komorebi source is incorporated. Currently
unknown frameless apps stay fixed rather than being guessed safe.

Theme `border_width`, attention flashing and custom-width native borders are not
implemented. Native gaps currently use sheet values as physical pixels; a shared
logical-pixel convention needs agreement before changing that. The geometry/identity
seam was tested with native fixtures and the actual shared watcher method, not a
new live WebView2 host launch.

What would change the rollout assessment: a clear, ungated shadow interval, then
Alex-present real-app tests showing stable placements and reliable release. Hidden
proof and a passing module protocol do not establish that live acceptance.

## Primary API sources read

Microsoft documentation informed the Win32 boundary, with no external implementation copied:
[SetWinEventHook](https://learn.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-setwineventhook),
[SetWindowPos](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos),
[DWM attributes](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute),
[SHQueryUserNotificationState](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shqueryusernotificationstate),
[RegisterHotKey](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey).

## Feel: resistance, dwell, snapping, pins (draft by Claude builder, 26 Oct 2026, for Alex to confirm)

Alex, 26 Oct: *"covering a tile with another doesn't immediately move it. It should feel more like moving
android or iphone apps around on the homescreen. Like there is a bit of resistance to things moving or resizing.
Things should be resizable from all corners and sides. Things should be able to snap together if you drag them
near each other (with a small gap). And pinning something should keep it on screen, though it might get made more
narrow if something big comes on screen."* And: *"make it so that the tiling manager doesn't flood the log."*

### What we can and cannot touch (the constraint that shapes everything)

A foreign window (Chrome, Discord) is dragged and sized by Windows' own modal loop, which follows the cursor. We
cannot add resistance to *that* window without injecting into its process (forbidden). So the feel lives in three
places we do own:
1. **The neighbours.** They move only when we say.
2. **The landing.** This is where the dragged window ends up when you let go: we place it once, at release.
3. **The ghost layer.** It shows both of the above, live, at 60 Hz.

During a drag the real neighbours stay put. Their translucent ghosts do the shuffling, and a fainter outline
shows the landing. At release the real windows go where the ghosts were. `drag=live` (real neighbours sliding
during the drag) stays refused until it is measured smooth on real Chromium windows. The engine already produces
the per-frame positions it would need.

### The drag, frame by frame (homescreen model)

1. **Dead zone.** Until the window has moved `deadzone_px` from where it started, nothing happens. That is 10 px
   at 100 %, so 15 px on Alex's 150 % screen. A release inside the dead zone puts it back exactly where it was,
   so a click on a title bar that wobbles 6 px is not a move. Windows' own drag threshold is 4 px (**ran**
   `GetSystemMetrics(SM_CXDRAG)` = 4). Android's touch slop is 8 dp (**recall**).
2. **Contact.** When the dragged window's rectangle covers a neighbour's *home* rectangle (closer than the gap),
   that neighbour is *in contact*. It does not move, and its ghost stays where it is.
3. **Dwell.** A neighbour in contact gives way only after the drag has rested on it for `dwell_ms` = **350 ms**,
   while moving slower than 600 px/s (at 100 %).
   - A drag that sweeps across a window in transit never moves it. A hover that pauses does.
   - Leaving contact resets the timer.
   - 350 ms is AOSP Launcher3's `REORDER_TIMEOUT` (**read**, through a search summary of an AOSP commit). A fork
     uses 650 ms.
4. **How it yields.** Pinned and unmanaged windows never yield: they are walls. Other neighbours yield in one of
   two ways:
   - **Swap.** If the dragged window's centre is *inside* the neighbour, the neighbour slides into the dragged
     window's vacated starting slot. It shrinks to fit that slot only if it keeps at least 60 % of its size;
     otherwise there is no swap.
   - **Slide aside.** Otherwise it moves along the axis of least overlap. This is the existing push solver, which
     cascades into its own neighbours, then shrinks to minimum size, then minimises the least recently used.
5. **Easing.** Every ghost move is one animation of `motion_ms` = **250 ms**, with Material 3's standard easing
   `cubic-bezier(0.2, 0, 0, 1)` (**read**, the `md-sys-motion` tokens: medium1 = 250 ms). A target that changes
   mid-flight restarts from where the ghost is now, so motion never jumps.
6. **Settling back.** When the drag leaves a neighbour that had yielded, the neighbour waits **250 ms**
   (`return_ms`), then eases home. Brush past and come back within that time, and it doesn't bounce.
7. **Release is what the ghosts showed.** Neighbours that gave way go where their ghosts were. Neighbours still
   resisting stay put, and the dragged window lands on its outline: the nearest free spot, out of whatever is
   still resisting. This is the resistance: a sloppy drop that clips a neighbour by 40 px moves *your* window,
   not theirs, and a quick drop onto a window lands beside it. To make a window give way, rest on it.

   One exception: a neighbour in its 250 ms settle-back delay goes home, because nothing needs it moved. The
   no-overlap rule holds whatever happens: if the outline cannot be made legal, the existing solver settles
   around it.

   *Later the same evening (ran):* each tick now computes one plan (layout and outline), and release settles to
   exactly that plan, never recomputing it. If the outline can't be legal (no free spot at its size, and a
   yielded neighbour took its starting slot), the windows it covers give way in that same tick, so the ghosts
   show it. WYSIWYG: 2000/2000 seeds.

   *Changed while building (ran):* the first draft yielded "deep" drops at release (33 % covered). The resize
   filmstrip showed why that is wrong: the ghost said "the edge stops here", and the release pushed the chat
   under the browser as a 160 px strip. A seeded property test now checks that release equals the last frame:
   **ran** 2000/2000 seeds matched once the release used the same bounded search as the preview. A bigger
   search at release had found different layouts in 2 of 300.
8. **When a neighbour can't slide cleanly**, it first gives way by shrinking its own facing side (never under
   60 %), instead of shoving a third window. It keeps the side it first chose while that still works, so its
   ghost doesn't flicker between "shorter" and "narrower". Past that, the push solver shrinks only down to 60 %
   (engine `SQUASH`); past *that*, the covered window is minimised rather than squashed into a strip.
   *Found in the hidden-desktop proof (ran):* the browser slid right and squeezed the chat from 1992 px to
   776 px. Now its bottom edge gives way (1300 → 1010 px) and the chat is untouched.

A hover that backs away before 350 ms moves nothing. A hover that waits, sees the neighbour slide, and then backs
away also ends with nothing moved: the neighbour slides home after 250 ms, or at release.

### Snapping

- **Radius.** `snap_px` = **16 px** at 100 % (24 px on Alex's screen). Within it, an edge snaps to one of:
  - the screen's outer gap;
  - a neighbour's facing edge, at exactly the inner gap (the "snap together with a small gap");
  - a neighbour's parallel edge (tops aligned, lefts aligned).

  The closest candidate wins. Ties break by order.
- **What snaps.** Snapping applies to the **landing**: it is shown as the ghost outline during the drag and
  applied at release. A move snaps whichever edge is closest on each axis. A resize snaps only the moving edges.
- **Escape.** Move past the radius. There is no modifier key, because that would mean reading global key state.
- **Never into an overlap.** A snap that would make the window overlap something is dropped for that axis.

### Resizing: all eight edges and corners

- **Foreign windows** keep Windows' own sizing border on all eight sides, about 11 px physical at 150 % (**ran**
  `SM_CXSIZEFRAME` = 5 + `SM_CXPADDEDBORDER` = 6). Chrome, Electron apps (Discord, Spotify, Claude, ChatGPT) and
  Windows Terminal all keep it (**recall**). The engine tells a resize from a move by the rectangle alone (the
  size changed), and works out which edges moved.
- **Resize resistance.**
  1. A moving edge that reaches a neighbour it isn't snapped to stops for `dwell_ms`: the landing clamps at the
     gap.
  2. Then the neighbour's facing edge gives way and **follows** the edge. The neighbour shrinks; it is not shoved.
  3. It shrinks down to its floor: 60 % of its size (the same `SQUASH` as arrange), never under its minimum.
  4. At the floor the edge stops again. A second dwell hands the neighbour to the push solver (slide aside,
     minimise the least recently used).
- **Shared edges** (`edges=shared`, the default). Two windows snapped exactly the gap apart share that edge.
  Resizing one across the shared edge moves both, with no dwell: grow one and the other recedes, shrink it and the
  other follows. This is the tiling feel: one drag makes the chat wider. `edges=free` turns this off.
- **Rubber band at the minimum.** The landing never goes below the window's minimum (learned from refusals). The
  ghost outline stops while the real frame overshoots, and release snaps it back.
- **Frameless windows with no border.** Agora's own WebView2 windows from `kd_window.py` can't be fixed from here
  without editing `kd_window.py`, which is another builder's file. They need `WM_NCHITTEST` edge zones in that
  host.
- **Considered and not built: WM-owned "gutter" handle windows in the gaps.** In the 12 px gap, the two windows'
  invisible sizing borders already cover the whole strip. A gutter would only win if it were raised above both.
  That means re-raising it on every focus change, and stealing clicks from dialogs that sit over a gap. Revisit
  this if the shared-edge rule above doesn't feel right by hand.

### Pins

A pin stays on screen. Nothing the WM does minimises it or moves it off the screen. Something big may make it
narrower:
- **Opening or restoring a window: fill first.** *This superseded my first order the same evening; the
  coordinator's live bug report and draft.* Live at ~21:55, restoring Lines, then Claude, then Help each
  minimised the others on a half-empty screen. Alex asked for "tile freely or fill the space", and minimise only
  "when the screen is full". So "full" now means *no room even at 60 %*. The order, each step tried only when
  every earlier one fails:
  1. Free space at its preferred size.
  2. Free space at **60 % or more** (the biggest such spot, then the nearest). Nobody is minimised.
  3. `when_full`: minimise the least recently used unpinned windows, one at a time, each time trying preferred,
     then 60 %. Minimisations it didn't need are given back.
  4. **Narrow pins**, keeping each pin's edge nearest the screen edge, by as little as gets the new window to
     60 % or more. A pin never goes under `pin_min` = **50 %** of its pinned width, nor under its minimum.
  5. Otherwise it stays minimised and says why.

  Why pins come after minimising (agreeing with the coordinator): a pin's width is the person's choice, while a
  new window's preferred size is the app's guess. So a pin narrows only when even 60 % of the newcomer won't fit
  beside it ("something big"). **Ran** the live sequence as `test_engine.FillFirstTests`, with theme gaps 12/14:
  - Lines fills the bottom-left at 90 %.
  - Claude (needs 541×1088) finds no room, so only Spotify, the least recently used, is minimised.
  - Help fills the right strip at 64 %.
  - Four windows stay on screen (live, it was two).

  Would change my mind: if Alex wants a pin to give up some width before *anything* is minimised, move step 4
  before step 3.
- **When space frees** (a close or a minimise), a narrowed pin grows back to its pinned width first.
- **A work-area change** (a bar appears) moves and narrows a pin only as far as needed to keep it on screen.
- **During drags, pins are walls.** You can drag a pin yourself; where you drop it becomes its new pinned place.

### Tunables

All values are at 100 % scale and are multiplied by the monitor's DPI scale (**ran**: 144 dpi, so 1.5 on Alex's
screen).

| wm-settings key | Default | Range | What it sets |
|---|---:|---|---|
| `dwell_ms` | 350 | 0–2000 | How long a drag rests on a window before it gives way |
| `snap_px` | 16 | 0–64 | Snap radius (0 turns snapping off) |
| `deadzone_px` | 10 | 0–64 | Movement before a drag or resize breaks free |
| `motion_ms` | 250 | 0–1000 | Ghost animation duration (0 = jump) |
| `pin_min` | 0.5 | 0.2–1.0 | Narrowest a pin may get, as a share of its pinned width |
| `edges` | shared | shared, free | Whether snapped windows share a resized edge |

Internal constants in `feel.py`:
- `return_ms` 250, `fling_px_s` 600, `bond_px` 2, `follow_px` 64;
- `idle_ms` 10000: a lost drag-end releases the gesture after this;
- easing `(0.2, 0, 0, 1)`.

### Owned dialogs and maximised windows (found while thinking this through)

- **Owned dialogs.** A Save dialog is an owned top-level window. It was managed like an app, so opening one on a
  full screen would minimise the oldest window.
- **Maximised windows.** A maximised window was "restored" on the next tick, because its rectangle didn't match
  its plan.

Both now float outside the layout. Owned windows are listed unmanaged (`why: owned dialog or popup`). A maximised
window leaves the layout until you un-maximise it, and then it comes back like a newly opened window.

### Log flooding

- **The world.** Nothing per tick reaches it: no records, no happenings. The kernel test now counts both across
  idle ticks.
- **stderr.** A refusal is said once, not every second. The live `stderr.log` said `wm settings refused:
  game/fullscreen gate is active` 98 times (**ran** `uniq -c`).
- **`shadow.jsonl`.** It had reached 448 KB after a few minutes (**ran** `ls`). It is now written only when the
  plan changes, and rotates at 2 MB.
- **A bug that would have flooded too.** Since pins moved to `screen.json`, any pin made every settings read fail
  (`'str' object has no attribute 'get'`). Fixed.

### What would change my mind, and the risks

- **Dwell timing.** If 350 ms feels sluggish by hand, lower `dwell_ms` (around 200 feels iOS-snappy, **recall**).
  If windows still shuffle in transit, raise it, or lower the fling speed. Only Alex's hand can judge this.
- **Ghost-only preview.** If it feels disconnected (the real neighbours jump at release), measure `drag=live`
  with translation-only moves on real Chrome and Electron windows. Translations are cheap; resizes are not.
- **Windows' own Snap** (drag to a screen edge for half a screen, or the snap-layouts bar at the top) fights the
  landing at release. Turning off *Settings → System → Multitasking → Snap windows* is Alex's call; we change no
  Windows settings.
- **Apps that refuse sizes** are learned as a minimum, or become obstacles, as before.
- **DPI changes.** A DPI change mid-session changes the scale at the next settings read, once a second.
- **Games.** The gate pauses everything, as before. A gesture is dropped, and its ghosts cleared, when the gate
  closes.
- **Foreground lock.** Nothing here needs focus. Ghost windows are click-through, no-activate tool windows.

### Built and measured (Claude builder, 26 Oct 2026)

**Files.**

| File | Change |
|---|---|
| `feel.py` (new) | The gesture: dead zone, dwell, swap/slide/cut, easing, settle-back, snap, shared edges, landing. Pure; time is an input |
| `engine.py` | `push` works on a rectangle dict (same search, ~20× cheaper), takes `held` and `budget`, shrinks only to `SQUASH`. Pins carry `home`: `narrow_pins` on open/restore, `regrow_pins` on close/minimise, clamped on screen at a work-area change. A big new window opens smaller (down to 60 %) before failing; minimisations it didn't need are given back |
| `manager.py` | Drives a `Gesture` from hook events. `drag_tick` is the 60 Hz path. Pins are placed (narrowed or regrown) and adopt your own moves. Owned and maximised windows float. Feel settings are validated. The gate is cached 0.5 s. The shadow log is written on change and rotates at 2 MB |
| `wm_module.py` | The 60 Hz drag path reads only the dragged window (a full tick each second still runs). stderr hears a refusal once (`say`). Pins are read as keys from `screen.json` (fixes the 'str'.get bug) |
| `win32_host.py` | `dpi_scale()`, `Native.scale()`, `Native.rect_of()`, rows carry `owned` and `maximised` (internal; not in `wm.windows`) |
| `ghost.py` | The landing outline (alpha 40) beside neighbour ghosts (alpha 70); unchanged boxes make no API calls |
| `simulator.py` | `film()`: a drag as a filmstrip (`evidence/feel-film-dwell.png`, `feel-film-resize.png`) |
| `hidden_feel_proof.py` (new) | Real windows, ghosts, placement and lease contract on a never-shown desktop |
| `test_feel.py` (new), `test_manager.py`, `test_engine.py`, `test_module_kernel.py` | Scenes from Alex's screen; WYSIWYG property; frame cost; quiet logs; nothing per tick reaches the world |

**Ran.**
- **Unit and kernel suites:** `python -m unittest test_engine test_feel test_manager test_watchdog
  test_source_seam test_module_kernel` printed `Ran 55 tests ... OK` (was 22); after the fill-first rework, `Ran 58 tests ... OK`.
- **Fuzz:** L0 fuzz 60,000 events, with the pin invariants rewritten (a pin may narrow or regrow, never be
  minimised by the WM or leave the screen).
- **Frame cost**, 20 windows in a packed 5×4 grid, slow diagonal drag, 300 ticks: median 1.5 ms, p95 3.8 ms,
  max 5.3 ms; release 5.7 ms. Before the push rewrite: median 16.4 ms, p95 29.3 ms.
- **WYSIWYG:** 300 seeds in the suite (2000 once, by hand: 2000/2000).
- **Hidden desktop** (`hidden_feel_proof.py`), printed `feel L1 passed; alex: untouched`:
  - shallow drop → notes `[216,1389,1000,629]`, neighbours untouched;
  - dwell 600 ms → browser `[16,73,1800,1010]`, chat untouched, actual windows overlap-free;
  - shared edge +300 → chat `[2132,73,1692,1300]`;
  - `drag_tick` with real ghost calls: median 0.64 ms, p95 4.1 ms;
  - off restored every fixture.
- **The real watchdog could not arm** on the hidden desktop: Alex's live guard holds Ctrl+Alt+Backspace
  (RegisterHotKey error 1409). So the feel proof uses an in-process lease with the same contract. The original
  `hidden_proof.py` passed its 9 native tests, and its watchdog tests failed for the same reason. Rerun it while
  the live WM is off.
- **Read-only on the real desktop:** 17 windows, none owned or maximised. Enumeration median 7.3 ms (max 11.6);
  gate 26 ms; DPI 144.

**Not verified** (needs a hand on the real screen):
- whether 350 ms / 250 ms / 24 px *feel* right;
- ghost visibility on the Dusk theme (a dark translucent box);
- Windows' own Snap fighting the landing;
- real Chrome/Electron hook timing during a physical drag;
- `rect_of` latency against a real modal move loop;
- the panic chord by hand.

**Roll-out (Claude).** The live module (pid 130396 at 20:48) still runs the old code; Python loaded it at start.
1. Restart only the `wm` module, not kdesk and not the kernel (**read** `kernel/words.py` `off`):
   - say `off wm`: its process stops and its grants are taken back;
   - then `undo r<that record>`: it turns on again with its grants, and the kernel starts the new code.

   The guard releases everything when the manager exits. The module comes back in shadow.
2. Send a fresh `wm.mode live` with Alex present. An old request never re-arms.
3. Optional: add the feel keys to the existing `wm-settings`, so Alex can see and tune them:
   `set <wm-settings id> dwell_ms=350 snap_px=16 deadzone_px=10 motion_ms=250 pin_min=0.5 edges=shared`.
   Missing keys use these defaults anyway.
4. Watch `<world>/modules/wm/stderr.log`: it should stay quiet. Recovery is unchanged:
   `python watchdog.py --release-all <world>/modules/wm/lease.json`.

