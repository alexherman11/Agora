# Requested window management while gaming

Builder evidence, 5 November 2026; task dk2547. Supersedes the first-turn
game-only exclusive-fullscreen restriction. Alex recovered Rocket League
himself through Windows (task update attributed to dk2568); do not restore it
again. The current goal is requested management of games and companion windows.
Source: word/fix. New word: `wm.move`; no second window manager or tiling engine.

## One request path, background gate retained

The admitted module request marks focus/restore/move as explicit. During
gaming these affect only the named target through `Manager._requested_action`:

- `wm.restore <key>` / `wm.focus <key>` restore the target if minimised and ask
  Windows to focus it. The existing dock's `share=yes` requests use this path.
- `wm.move <key> at=x,y [size=w,h]` places only that visible target, without
  focus or neighbour movement. Omitted size retains its observed dimensions.
  Coordinates must fit the current WM work area. Restore a minimised target
  first; pins, exclusions and owned/inaccessible windows still refuse.
- The bar's existing `wm.arrange expect=<exe|agora>` arms a five-second request
  before launching. While gaming it activates only the uniquely matching new
  window. Nothing moves merely because it was armed. Expiry, ambiguity, a hard
  desktop gate or native refusal never triggers another action or fallback.
  A game starting after arming changes the request to target-only behaviour.

Game-process reasons come from the shared gate, with no hardcoded game list or
caller-supplied gate override. Exclusive fullscreen is an allowed reason for
an explicit target action, including a companion. It is never permission for
layout, probes, auto-minimise, motion or focus on other windows. Ordinary
non-game shared layout retains its existing behaviour. `wm.arrange` without a
named launch target refuses while gated.

Locked, presentation, failed-inspection and unknown gates still refuse.
Native identity/elevation checks, owner/steward admission, live-mode arming,
settings, and permissions remain unchanged. Focus/restore/move neither close
programs nor change settings nor inject input. No overlays or animation are
added. Explicit requests cancel stale layout debt. Expired/cancelled controller
queue entries cannot act after the caller receives a timeout.

Requested moves can be rejected or ignored by app-owned fullscreen, and
Windows can refuse focus. A game may minimise itself when focus is explicitly
switched away; this code never issues a minimise to it as part of switching.
Native success means submission, not visible outcome. No retry or settings
change is used to force an app to comply.

## Minimisation investigation

**Read:** the old gate rejected restore even for a minimised running game.
`Sharing timed out` describes a bounded share attempt and does not identify
who minimised a window.

**Ran, fake state:** the existing solver can minimise an ordinary managed
window under capacity pressure when a new window cannot fit. It has no game
classification; that protection belongs to the manager's gate. This reproduces
a possible mechanism, not Alex's historical event.

**Fixed:** the half-second gate cache could still contain an earlier clear
result when a newly observed executable appeared. Ingest now invalidates that
cache before solving its first layout. A fresh request's gate observation also
replaces the cache before the following tick. Mocked checks establish zero
native mutations in the new-executable gated case. No live logs or observations
established whether this caused Alex's original minimisation.

**Follow-up fixed:** capacity pressure without an explicit arrangement now
holds the entire native plan if it would minimise any currently visible window.
This also protects an unrecognised windowed game when the process/fullscreen
gate reports clear. The pure solver remains unchanged; ordinary background
capacity eviction no longer reaches Windows. Observed geometry is rebuilt on
the next tick so space becoming available permits layout again. Explicit
ungated shared arrangements retain their capacity policy.

The combined test
`test_capacity_pressure_while_gated_never_moves_or_minimises_game_or_companion`
first proves that the fixture needs eviction, then checks both eviction orders,
game/fullscreen gates, a precomputed plan, and repeated controller ticks.
`test_ungated_capacity_cannot_hide_unrecognised_game_or_companion` checks the
clear-gate fallback and recovery when space becomes available.

## Gate-aware lease release

The common `watchdog.release_all` path now reads the shared gate before any
window restoration. A gate or inspection exception latches release-only
behaviour for the remaining lease entries: identity/cookie checking and marker
removal, with no saved placement, styling, minimise or focus call. Those entries
are marked released; clearing the gate later cannot replay old geometry.
This covers off/shadow, independent watchdog termination and recovery through
the same function. With a clear gate, existing lease restoration remains.

`test_off_while_gated_releases_game_and_companion_without_window_changes`
exercises actual Manager mode switching through Lease.release and the shared
cleanup, with all native APIs mocked. Further tests cover clear release,
border-only leases, and a gate appearing between release entries.

## Evidence and activation

**Ran:** fake-native controller checks cover game/companion requests, exclusive
fullscreen, target-only moves, exact launch matching, timeout/cancellation,
source capacity pressure, identity/native failures and subsequent ticks with
no background writes. The Node bar check loads shipped `shell-kit.js` with a
fake transport/DOM; it creates no window or browser. The full WM suite includes
a disposable headless kernel process. See BUILD-RESULT.md for final counts.

First-turn Discord research remains: [Game Overlay 101](https://support.discord.com/hc/en-us/articles/217659737-Game-Overlay-101)
documents the built-in Windows overlay and **User Settings > Overlay > Enable
Overlay**. [Discord's fullscreen limitation](https://support.discord.com/hc/en-us/articles/25289844838551--Known-Issue-Game-Overlay)
describes its windowed/borderless requirement. Local `settings.json` exposed
no top-level overlay field; actual enabled state remains unknown. No game,
Discord, security or permission setting was changed.

The first-turn live `wm.policy` read was refused for this Pike worker. No
repeat or alternate native route was used. Coordination notes are on dk1156;
its unlanded drag code was not imported.

Pike/JEFF must review and safely activate. **First activation still executes
the old running watchdog's unsafe shutdown code.** The dk2547 restart hold
remains: land only after Alex is out of the game or approves an interruption.
Patched shutdown tests do not make that first activation safe. Hot reload is
unavailable; new live arming still refuses while game-gated. No global gate is
weakened. Changes remain uncommitted for House landing.

No live restore, switch, move or test is authorised by this follow-up. After
safe activation, verify outcomes only on Alex's next actual requests; do not
replay his old recovery request. Performance figures are fixture measurements,
not evidence about the running game's FPS.
