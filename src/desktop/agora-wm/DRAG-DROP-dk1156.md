# Drag destinations and continuous motion — dk1156

Worker handoff, 4 November 2026. Source: word/fix/seam.
Missing-word implemented: `wm.size` / `wm.sizes` over `wm-settings sizes`.
This extends the existing general tiling mechanism and its OS/browser seams.
It is not activated on Alex's desktop, and Alex has not judged the feel.

## Slice 1 research and choices

Research was completed and recorded as task note dk2227 before this slice's
source edits. **Read**, not a claim of running these projects:

- [FancyZones documentation](https://learn.microsoft.com/en-us/windows/powertoys/fancyzones)
  and [ZonesOverlay.cpp](https://raw.githubusercontent.com/microsoft/PowerToys/main/src/modules/fancyzones/FancyZonesLib/ZonesOverlay.cpp):
  dragging exposes zones, mouse hover highlights one, release fills it. The
  overlay paints fill and border separately and has a 200 ms fade. Borrow
  cursor selection and distinct candidate/selected glass; Alex requested
  automatic pickup, so no Shift requirement.
- [Komorebi placement](https://raw.githubusercontent.com/LGUG2Z/komorebi/master/komorebi/src/windows_api.rs)
  and [window animation dispatch](https://raw.githubusercontent.com/LGUG2Z/komorebi/master/komorebi/src/window.rs):
  visible bounds account for shadow borders; placement uses NO_ACTIVATE,
  preserves z-order unless explicitly requested, and can queue asynchronously
  to avoid blocking on the target application's thread. Borrow those boundary
  properties, already present in Agora's Native.place. Do not copy focus or
  workspace operations.
- [GlazeWM NativeWindow interface](https://raw.githubusercontent.com/glzr-io/glazewm/main/packages/wm-platform/src/native_window.rs):
  exposes shadow-border deltas, frame-with-shadows and a SetWindowPos wrapper;
  restore can receive an outer frame to avoid restore-then-reposition flicker.
  Its [historical Electron report](https://github.com/glzr-io/glazewm/issues/73)
  shows why invisible-border assumptions need app-specific proof. This is not
  evidence of current GlazeWM Electron animation behavior. Borrow measured
  frame compensation, not a guessed constant border.
- [Hyprland 0.48 animation configuration](https://wiki.hypr.land/0.48.0/Configuring/Animations/):
  named cubic-bezier curves, decisecond durations and window-movement animation
  inheritance. Borrow tunable easing; this versioned reference is not a claim
  about current defaults.
- [Niri animations](https://niri-wm.github.io/niri/Configuration:-Animations.html):
  distinct move/resize effects, critically damped movement springs, and
  150 ms opening/closing easings. Borrow continuous retargeting and non-bouncy
  motion. A compositor's texture animation does not prove that repeatedly
  resizing a foreign Electron HWND will be smooth.

**Chosen:** nested half/column zones select by distance to their horizontal
centre under the cursor. This makes the middle of a side choose that side and
the outer edge choose its narrower column. The dragged centre still governs
whether a neighbour yields. Half-width means half of usable content width after
outer margins and the shared gutter; otherwise two half-width browsers cannot
fit together.

**Built:** the size capability accepts named, ordered matching rules (executable
globs, native class, browser-host flag, Agora marker, or app name). Width, height,
minimum fractions and compact intent are world facts. Later matching kinds
override earlier ones. Live settings reads update the policy without source
reload; an explicit drag's chosen size is remembered for that live window.
Per-window geometry remains screen state, not world churn. Compact arrivals fit
free space first and retain their preferred dimensions when packing is needed.
Two movable windows use columns on open/share; startup repairs an old stacked
pair, and close reflow can grow the remaining tiles.

The authored initial choices are [size-policies.json](size-policies.json).
The module does not seed these at startup. The installer prints/installs them
explicitly. The attempt to publish them to dk531 was **refused**: only the maker,
lead or desktop leaders may set that thing. No alternate route was attempted.
House needs the settings owner's/leader's authority to apply the exact line
printed by `install.py --sizes-line dk531`. Existing live motion_ms=250 was not
changed. Slice 2 still needs the requested 180 ms setting and slow-app
move-then-resize delivery.

**Read:** AGENTS.md; live charter dk838; task dk1156 and its November centre
crossing requirement; wm-settings dk531; both installed taskboard arrangements
(dk88 and dk262). The current settings cannot replace dwell-based move yielding
or make real windows follow animated ghosts. Both boards sort cards by priority
and their drop word changes the lane only. A pointer-selected arbitrary insertion
box would therefore promise a position the next reading cannot preserve.

**Implemented interpretation:** compare the dragged rectangle's centre with the
neighbour's centre along the approach axis, using pickup geometry. Equality is
not a crossing. Perpendicular overlap is required. Waiting, shallow overlap,
pointer position alone and the neighbour's animated position cannot trigger a
swap. Reversing the drag returns neighbours continuously. Resize dwell and shared
edges retain their existing policy.

The engine offers maximal open areas and legal half-screen/third-column
subdivisions. The native pointer selects an area as described above; callers
without a pointer retain the earlier centre-based fallback. Existing minima, pins, fixed
obstacles and gaps still constrain the choices. A move hover cannot minimise a
neighbour or move an uncrossed neighbour to manufacture space. Equal-tile swaps
retain the destination tile instead of expanding into unrelated vacant area.

Manager previews now move real neighbours through the eased frame positions.
Release continues from the last issued position to the preview plan; it does not
apply final rectangles in one jump. The module keeps its 60 Hz path running for
settling motion. Native placement uses the existing no-activate/no-z-order seam.
Off, gates, disappearing windows and native refusal stop the relevant motion.
Gate checks precede glass construction, and explicit sharing cannot exempt a
named game. Cheap foreground, notification and fullscreen changes invalidate
the cached process gate before drawing; process discovery otherwise retains the
existing half-second polling interval. This is not a zero-latency process-start
guarantee.
The existing `drag=ghost` setting remains compatible: glass describes destinations,
while real neighbours move. The previously rejected `drag=live` option is not
newly enabled.

Both browser painters call the same Python geometry engine through an
authenticated, read-only preview seam. A sorted repeat supplies only each shown
item's compiler sort tuple and stable tie position; it does not rewrite priority
or add a new task-move verb. Crossing the actual insertion boundary starts the
lane's displacement, including the downstream cards that need that space.
The release captures current painted positions, clears temporary transforms
during repaint and animates into the new reading. The existing fenced world drop
remains the mutation. Responses for an earlier pointer position or a cancelled
drag cannot repaint. Empty repeat wrappers provide the empty-lane landing area.
Native and browser motion use `wm-settings motion_ms`; reads add no world records.

## Evidence

**Ran (Slice 1):** WM unittest discovery: 124 tests passed. The suite printed
`L0 fuzz: 2000 sequences x 30 events = 60000 events; invariants passed`
and `feel WYSIWYG: 300/300 releases matched the ghosts; differing seeds []`.
These are geometry/protocol/manager checks, not Alex's usability acceptance.
Old dwell-based move expectations were changed to the requested centre boundary.
Size policy tests cover changed rules, invalid fractions, compact free-space
insertion, compact packing, portrait/odd-width columns and startup repair.
The real module/kernel test covers `wm.size`, readback, undo and unauthorized
callers. The kernel-process fixture uses the running pinned interpreter, since
worker worktrees have no local venv.

**Ran:** kernel tiling route/compiler suite: 6 tests passed, including both
compilers before and after a real lane change, equal-priority ties, authenticated
geometry requests, invalid requests, no write records, and live timing changes.
Widget broker suite: 6 tests passed, including instance/principal guards and the
geometry call. Node adapter lifetime checks: 12 checks passed. Syntax checks passed
for both painters, the shared carry helper and widget-host.js.

**Ran before this slice, earlier source:** `hidden_drop_proof.py .tmp/hidden-drop` printed
`hidden native drop: 6 checks passed` and `feel L1 passed; alex: untouched`.
It uses the shared never-shown desktop fixture, allowlisted fixture windows,
real native placement, the production manager and production glass. It verifies
pickup glass, stationary overlap before the boundary, intermediate neighbour
positions, exact final landing, valid final layout and unchanged foreground.
The observed final landing was `[1928,73,1896,1945]`; the neighbouring tile
finished at `[16,73,1896,1945]`. The wrapper reported input desktop `Default`
unchanged and zero foreground/focus handles on both observations. Those zeros
limit this to the fixture's observable focus evidence, not a claim that Alex's
actual foreground application was inspected.

**Written for House, not run here:** the native proof now also drives fake
pointer samples (no cursor/input injection), checks actual glass extended styles,
and settles into both a side and a column on allowlisted windows. Its expected
count is 8. The earlier 6-check result does not verify these new checks or the
current native source.

**Blocked, not passed:** `hidden_card_drop_proof.py` uses the approved
`widget_browser.Browser` headless helper. Chrome failed before a page could run:
`FATAL:mojo\public\cpp\platform\platform_channel.cc:112 ... Access is denied. (0x5)`.
No sandbox flags, permissions or security settings were changed to get around
that denial. Node checks are not browser paint evidence. Browser animation,
empty/sorted lane geometry and the final handoff still need visual verification.

Scratch commands used the pinned
`C:\Projects\Agora4\.venv\Scripts\python.exe`.
The local `.tmp/run_checks.py` redirects unittest tempfile fixtures through the
repository's `kernel.scratch` helper. Initial standard tempfile directories were
inaccessible in this sandbox; their ACLs were not changed. Logs, disposable worlds,
profiles and native proof JSON remain under `.tmp`, which is not for landing.

## Coordinator work remaining

Run `hidden_card_drop_proof.py` through the approved hidden runner in an environment
where its Chrome Mojo IPC is allowed. Also exercise the actual legacy and component
boards: before/exactly/after centre, reversing, empty destination, unequal heights,
equal-priority order, cancellation, stale drop and final landing/focus. The helper
proof alone does not establish those complete application flows.

After source review and landing, activate the WM/kernel/browser seams together.
Regenerate the component painter widget from `painter.install.widget_source`;
existing stored widget bytes do not automatically gain the shared carry helper.
Preserve the installed arrangements and task facts. The worker did not restart
any live program or change the installed widgets.

Then have Alex try Agora and native top bars, particularly his Spotify
side-to-column example. His “feels natural” acceptance remains open. An observed
teleport, wrong landing size, focus change, or lag on a real native app would
invalidate the corresponding fixture-based confidence and needs correction.
