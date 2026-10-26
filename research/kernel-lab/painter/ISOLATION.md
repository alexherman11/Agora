# Component isolation and general handles

Builder draft for Claude's review, 26 October 2026. No git add, commit, push,
checkout, worktree or index operation. `lens.js` is unchanged.

Small general kernel additions first: `component-health` and `component-action`
with private viewer-scoped `paint-report` facts; `personal-view` and
`personal-style`; style validation in ordinary `make`/`set`; compact `look-view`
with explicit `plan=yes`; health on component discovery/cards. Implementation is
in `painter/{arrangement,handles,health}.py` with dispatch hooks in `kernel/words.py`.
The guide and installed arrangement guide document these handles.

## Investigation before choosing a boundary

**Read:** Chromium documents isolating sandboxed opaque-origin frames beginning
in Chromium 127. WebView2's Runtime 129 release notes explicitly disabled
`IsolateSandboxedIframes`; its general process-model documentation delegates
renderer allocation to Chromium. Neither establishes this installation's
per-component independence:

- [Chromium process model](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/process_model_and_site_isolation.md)
- [WebView2 Runtime 129 notes](https://learn.microsoft.com/en-us/microsoft-edge/webview2/release-notes/runtime/129)
- [WebView2 process model](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/process-model)

**Ran:** `isolation_measure.py` creates never-shown native WebView2 windows,
using the pinned interpreter, normal runtime settings and the same native guard.
Separate disposable HTTP servers provide the separate loopback origins. Counts
are reported over HTTP, so a frozen renderer cannot block measurement. After a
confirmed `hang-start`, a 250 ms drain precedes the before snapshot, then a
3-second observation. Each child process tree is bounded and cleaned up without
touching resident WebViews. All report `hidden: true`.

Installed runtime: **155.0.4283.62**.

| Actual experiment | Before | After | Result |
| --- | ---: | ---: | --- |
| srcdoc parent heartbeat | 3 | 6 | parent answers and changes DOM/style |
| healthy sandboxed sibling frame | 3 | 3 | frozen by the other frame's infinite loop |
| looping sandboxed frame | 3 | 3 | frozen |
| separate healthy loopback window | 3 | 6 | survives |
| separate looping window | 3 | 3 | frozen |
| healthy Worker heartbeat | 41 | 101 | survives a looping sibling Worker |
| looping Worker heartbeat | 36 | 36 | frozen |
| Worker experiment's page heartbeat | 2 | 5 | survives |

The frame experiment has **2 Renderer processes** total: the parent is separate,
but its opaque sibling frames share a renderer. The two-window experiment also
has **2 Renderer processes**. The Worker experiment has **1 Renderer process**;
Workers isolate execution threads, not process memory. These are observed
allocation and liveness results, not a guarantee for every future runtime.

**Ran**, frame startup/cost, one cold disposable process group per count:

| Frames | Startup ms (printed) | Private bytes, complete runtime group | Working-set bytes, complete runtime group |
| ---: | ---: | ---: | ---: |
| 0 | 0 | 136990720 | 290496512 |
| 5 | 83.20000004768372 | 166653952 | 350826496 |
| 20 | 144.10000002384186 | 198459392 | 381407232 |
| 100 | 681 | 341090304 | 527994880 |

The frames contain a small button and readiness script, not a complete board
component/bridge. Startup is from inserting frames to their ready messages;
memory is sampled 500 ms later. Private bytes include browser/GPU/utility/
renderer processes, with PIDs retained in JSON. These are single-run measurements,
not per-frame exclusive memory, a statistically stable benchmark, or a prediction
of full production component costs. All nonempty frame counts still used only
two renderers. Source/results: `isolation_measure.py`,
`evidence/isolation-measurements.json`, `evidence/isolation-worker-measurement.json`.

## What was built

**Ran:** component boundaries catch module import/mount exceptions, missing
modules, settings validation, primitive-installed listeners, timers, microtasks,
animation callbacks and rejected callbacks. Each module has its own blob URL
and named sourceURL. A failure produces a themed stopped card with the component
in words, one-line error, retry, previous-version and off controls. Last good DOM
is retained inert and marked stale. Siblings continue to render and act.

Mount/update reconstruction and synchronous callbacks are measured against
**32 ms**, excluding nested child work from a parent's mount time. Two reported
failures/slow operations quarantine the instance. Unreviewed/new code and
`isolation=worker` definitions start quarantined. A quarantined Worker uses a
bounded DOM vocabulary and projected facts. Its 250 ms heartbeat is watched with
a **2500 ms** deadline; the Worker is terminated on timeout. Existing trusted
layout, nesting, menus and spring drag remain in-page.

**Ran:** the trusted native parent can survive a hung painter frame, record
quarantine first, and recover the board. Removing a hung iframe alone proved
insufficient: WebView2 can reuse the still-hung renderer. The native recovery
handler uses `GetProcessExtendedInfosAsync`, verifies every associated frame
belongs exclusively to that exact current widget host URL, and only then kills
that renderer. It refuses if any other view shares it. No browser-process kill,
arbitrary PID from JavaScript, focus change, code injection or topmost window is
used. Native recovery is accepted only from the top-level trusted local widget
host, never from its opaque child. Process ownership also makes a renderer
shared with another window a refusal rather than collateral damage.

The component watchdog uses 2500 ms for synchronous operations and 10000 ms for
module loading. **Ran:** the hidden native acceptance printed
`NATIVE RECOVERY 13187.0 ms; hidden=True; 25 cards restored` in the final run for a newly introduced,
reviewed in-page infinite loop. This includes detection, process replacement,
projection reload and the subsequent isolated Worker timeout. It is not a
2500 ms end-to-end recovery claim. Later final-run output is retained separately.

Whole widget hosts also ping their sandbox and show a trusted stopped card on a
5000 ms response timeout. Native `ProcessFailed` handles top renderer crashes/
unresponsiveness with one reload in 60 seconds, then a calm replacement. Frame
renderer failures are routed to the surviving parent. **Ran:** `--crash` used
the native CDP `Page.crash` on one never-shown window: its readiness count
**1 -> 2**, while its sibling's heartbeat **1 -> 4**. Only the crashed view
reloaded. Source/results: `widget_guard.py`, `pages/widget-host.js`,
`widgets.py`, `evidence/isolation-crash-measurement.json`.

## General editing handles

- Style writes validate before committing. Exact 3/4/6/8-digit hex and safe
  nonnegative CSS spacing shorthand are accepted. Legacy paint refusals are
  skipped and reported by `look-view`, preserving the view.
- `labels <setting> <JSON map>` separates displayed words from domain values.
  `format <setting> as initials|relative-date|count|text` supplies display values.
  Lane/card/catalogue content use `api.display`; facts and gesture identity stay
  unchanged.
- `personal-view` and `personal-style` create private owned overrides for the
  caller's person, including that person's agents. They are in ordinary help;
  personal styles apply after shared ones. Undo removes the override.
- `when fact <field> changes play <token>` and
  `when happening <word> play <token>` use bounded theme motion tokens and
  ordinary hear grants. Reduced-motion preferences apply.
- Compact `look-view` reports settings, parts, gestures, health and observed
  visible text/computed styles. `plan=yes` adds the full projection. Observations
  do not become projection changes/repaint loops.
- Failures are private facts and happenings. `components`/component cards derive
  health/last_error/quarantined for that viewer. A steward alone can clear
  quarantine; retry does not silently clear it. Previous-version recovery checks
  the current revision and restores only the relevant changed field.

Exact syntax and examples are in ARRANGEMENT.md and the kernel building guide.

## Verification

All commands use `C:/Projects/Agora4/.venv/Scripts/python.exe`. All injected faults
are in disposable scratch worlds. Native windows report never shown; the frame
and Worker measurements check the screen gate before every child. No test raises
or activates a window. Native hidden pointer tests deliver actual CDP pointer
events without waiting on compositor frames: hidden WebView2 intentionally stops
those frames, so a screenshot/rAF wait can hang a test despite responsive DOM.
Pixels for the mixed board are captured in the hidden Chromium driver, separately
from native WebView2 liveness evidence.

Verified outputs are retained in `evidence/isolation-*.txt/json`:

- Native mixed failures and editing handles: **20 of 20** (final run below).
- Hidden Chromium mixed failures and handles: **18 of 18** (final run below).
- Adversarial word/recovery/privacy contracts: **17 of 17**.
- Existing painter contracts: **11 of 11**; board proof: **28 of 28**.
- Purpose proof: **9 of 9**, its JS baseline **11 / 11**.
- Widget proof: **23 of 23**.
- Kernel suite: **Ran 67 tests in 116.919s — OK**.
- Model contracts: **Ran 7 tests in 0.025s — OK**; summary contracts:
  **Ran 7 tests in 0.001s — OK**.
- Existing task-board v2 proof: **34 of 34 checks passed**, explicitly
  `--minutes 0` development pass; no new ten-minute soak is claimed.
- Original pixel-guy studio proof: **PIXEL GUY PROOF: 11 checks passed**.
- Existing six proofs: five exited 0; local model cold-start failed its existing
  six-second summary deadline. After bounded warm-up, **LOCAL MODEL: 27/27 checks
  passed**. The cold failure is retained, not hidden or reclassified as a pass.

- Desktop suite: **Ran 53 tests in 172.191s — OK**.

An additional visual check caught a loading placeholder being retained as a
"last good" Worker rendering. The final implementation waits for the Worker's
first actual paint; a never-painted loop now has no fictitious stale snapshot.
The final mixed-failure proofs include that check. Native DOM and pointer
behaviour are tested without pixels; the separate hidden Chromium screenshot
`evidence/isolation-hidden.png` was opened and visually inspected.

One native checker initially inspected initials immediately after observing a
different preference's label update. That assertion raced the next projection
reread. Its failure is retained in `isolation-native-personal-check-race.txt`;
the final checker waits for the actual initials before asserting the domain name
is unchanged. No replacement model/trial or frozen ten-tweak request was run.

## Live adoption

**Ran:** all adoption screen-gate checks were clear. The resident kernel lacked
the new words and its window provider was **off**. The authorized desktop restart
and source installation preserved that off state; no board window was opened,
raised or activated. First-party component modules and painter widget bytes were
updated, with explicit review, while authored lens arrangements were retained.
The native mixed-failure scratch proof remained never-shown.

**Ran live:** **26 task identities/facts and exact histories unchanged**;
authored component arrangements and all saved window facts unchanged;
`look-view` answers compactly with **26 card, 3 lane, 1 board**. The live world has
the new words, guide, health/control grants and painter source. This verifies
installation and kernel readings, not a visibly painted live board while its
window provider is off. The provider was deliberately left off.

The first adoption preservation assertion failed on raw row equality. Investigation
found that restarting adopted the repository's pre-existing derived `groups`
column. Removing **only** that column from the current 26 task rows exactly
reproduces the original serialized hash
`1bcedb871a6d230d42cce35f56ad8281acf8fc12be242c4bd22cfaacfdf955dd`.
Histories were exactly unchanged even in that first attempt. The failed check is
retained in `evidence/isolation-live-first-check.json`; the corrected checks and
live source hash are in `evidence/isolation-live.json`. Normalized preservation
checks still include IDs, revisions and every task/window fact.

A final direct reading also printed `LIVE source matches repository: True`.
A Rough spots note and completed builder handoff task were recorded through the
ordinary live doors. Claude retains review/commit ownership. No git state changed.

## Limits and what would change the design

A first hang in reviewed in-page code pauses that view until the external host
recovers it. The component thread cannot interrupt itself. A Worker is not a
process-memory boundary: runaway memory or a browser-process failure can still
affect its runtime group. Native top-level widgets can request verified renderer
recovery; a nested bar-slot host cannot directly request that top-level native
operation, so it must stop/reopen instead of killing an unverified renderer.

The Worker vocabulary does not emulate the whole browser. Arbitrary nested
component modules, synchronous DOM measurement and direct rows/history reads stop
explicitly; use trusted wrappers or projected facts. Reviewed in-page components
retain ambient DOM and aggregate widget grants. Use the owner-preserving API or
`api.guard` after async continuations; arbitrary raw property handlers or ambient
work outside that API are not an adversarial execution boundary. A deleted or
newly hidden part is removed on projection reconciliation; a stopped card does
not make a hidden fact visible.

Paint observations are DOM/computed-style readings, not pixel truth, screen-reader
QA or proof against a lying component. Native hidden tests establish behaviour
without showing test windows, not visual animation smoothness. These changes do
not add a scheduler/process-memory quota or isolate the shared browser process.

If a future WebView2 provides independently killable component frame processes,
repeat these measurements before replacing the Worker boundary. If ownership
inspection, native message isolation, stale-revision recovery, private report
visibility or sibling liveness fails, the boundary must be corrected before
broader adoption. Preserve the passing DOM/door contracts during that change.
