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

All twelve offers have help. Only the desktop owner and their agents may inspect or
control this personal native surface. `wm.changed` announces JSON text
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
