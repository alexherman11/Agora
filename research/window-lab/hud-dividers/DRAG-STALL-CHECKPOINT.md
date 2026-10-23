# Drag stall repair: first bounded checkpoint

21 October 2026 · worker-a7987 · not visually accepted or activated

## Evidence and scope

Read JEFF c8223 and reviewer a7925 c8218. Their current-world hidden-copy
baseline was taken at 2560×1440 and 1280×800 CSS pixels, DPR 1.5, Guard
“alex untouched”; copy e17475, review run e17553:

- Held frames p95 16.8 ms.
- Changed-world polls fetched about 1.7 MB in 240–540 ms.
- Full painting caused 80–150 ms frames, including 41–61 ms forced layout.
- Queued answers arrived just after divider release; completion exceeded 300 ms.
- At 1280, pickup had a 148 ms frame, pointerdown 116 ms.
- At 1280, authored header/dock/shelf left about 202 px for panels, and the chat
  composer was unreachable.

These are **read reviewer results**, not measurements rerun by this worker.
The tooltip/ghost observations have unknown causes. Nothing establishes tree
corruption. No duplicate baseline browser was started.

Branch base is bb5be76. At inspection, main was 4565af4; `git diff HEAD main`
for lens.js and partition-ui.js was empty. This is not a claim that the whole
branch is refreshed from main. The house must merge current main and judge it
before landing; no main checkout or git lock was modified here.

## Source checkpoint

Only production file changed: `notation/desk-shell/lens.js`.

1. `paintAnswer` checked its geometry hold before awaiting style acquisition.
   A gesture beginning during that await could therefore be repainted. It also
   published `last`, `held`, `sceneAt` and `def` before it actually admitted the
   paint. Now it checks the hold again after the await and publishes those
   values only after admission. An unpainted generation remains fetchable by
   the ordinary post-gesture refresh. Forced refreshes still obey the hold.
2. `settle` now gathers clamp and no-scroll overflow measurements before
   writing their cut indicators. Thresholds (1 px clamp, 8 px overflow/head)
   remain unchanged. This removes read/write interleaving in that pass; actual
   forced-layout savings are **unmeasured**.

The asynchronous style acquisition itself is unchanged. This patch does not
claim style changes can never happen during a gesture, nor that the proven
style-wait race caused Alex's reported pauses. No polling, transport, scene
protocol, world policy, gesture fences or partition geometry changed. It does
not reduce scene payloads, eliminate full repaint cost, or solve pickup cost.
No timeouts or artificial waits were added.

SHA256:

- lens.js: `5BC4388DE58F1B318A37CC7400857E2F67C0DDE3CE52D3621EF8BF7A26976F78`
- test_repaint_races.js: `6F9F562979875E380B10A61BB7B067B1518F3B32A1BBF1339553216228CE9C8F`

## Ran

Installed local Node v25.6.1:

- New test against the original actual `paintAnswer` failed:
  `style wait cannot cross a new geometry hold`, actual 1, expected 0.
- After repair, `node research/window-lab/hud-dividers/test_repaint_races.js`:
  **18 assertions passed**. Extracts and executes the actual painter functions
  with controlled style promises and geometry/DOM doubles. Covers style/hold
  race, painted metadata, recovery after release, same-generation skip, forced
  refresh, style failure/retry metadata and overflow read/write ordering.
- Existing `test_partition_ui.js`: **281 partition DOM gesture checks passed**
  (stand-in, no browser).
- Existing `test_partition.js`: **167 partition geometry/model checks passed**.
- `node --check .../lens.js` and `git diff --check`: exit 0.
- Attempting the browser-oriented `checks/viewer_contract.js` directly in Node
  failed before assertions: `Failed to parse URL from viewer.js`
  (`ERR_INVALID_URL`). This is not a viewer regression result; its relative
  browser fetch has no base URL in that runner. No browser workaround was run.

These do not prove browser timing, caret/selection continuity, scroll
continuity or native WebView behavior. Full health and after-repair guarded
browser comparison have not run. No live tree/lens edits, host restart, account
action, Conversation send, Alex-desktop capture or input occurred.

## Responsive world seam for JEFF

Read JEFF's “Compact home-base — JEFF world layout direction” (a8231).
Inspected lens help, scene.py, lens_ir.py, expr.py and style.py: no supported
live available-width/height expression or authored responsive breakpoint was
found in those paths. `role ... when` / `only when` consume scene expressions;
they do not currently receive the browser's live allocation. Scene attention
viewport observations are optional reporting, not a reliable synchronous
layout input. `measure`, `share`, `grid`, partition sizing and focus allocate
space but do not choose compact internals from available height. Style grammar
has no authored media/container condition in the inspected parser.

Do not invent `$width`, `$height` or a viewport expression in a staged lens.
The smallest candidate seam is **read-only painter-local allocation
conditions authored on lens parts/roles**, not a world prop updated by resize.
The condition must apply to the owning bounded frame (root viewport for
home-base), use CSS pixels, update on resize without world events, avoid
feedback loops, preserve stable editor nodes and caret, and grant no commands.
Syntax, mutually exclusive branch behavior and draft retention need review
before implementation; this report supplies no new responsive word.

JEFF owns exact compact header/widget/dock/shelf lens/style hunks and reversal.
No such hunks are fabricated here. Keep the current tree and memberships.
When minima physically cannot coexist, use authored compact controls followed
by explicit tab/focus presentation, not clipped controls, whole-HUD horizontal
scroll or arbitrary scaling. A hidden control needs an accessible chooser.

## Next bounded comparison

Use the designated reviewer's existing current-world dragtimes harness and
its quiet/churn scenarios with this exact lens.js hash over current main.
Run at both measured sizes; preserve the actual copy tree rather than staging
an old recipe. Record frame distribution, requests, paint and forced layout,
pickup pointerdown, release-to-commit/paint, and guarded screenshots.
Check every cancellation/busy guard, delayed and refused writes, draft/caret,
selection and viewer reading position. Add a delayed-style gesture race.
Attribute pickup separately (including the afloat ancestor/scrollHeight scan);
do not assume this batch improves that path.

The card remains incomplete until that comparison and the responsive world
path are accepted. No host activation is authorized by this checkpoint.

## Prepared branch verification, 22 October (codex-builder-1)

The house completed prepare request e25525 without judging or landing:
checkpoint `31e3cd89342422abe19794e111b96ce08bc3a3d3`, main
`1f6cbe52d0434efee01035a749e713f25e53a06c`, clean merge HEAD
`75d72f65a0ca0eac7d171dac5935e3b0ca8a870c` (card receipt c10731).
Do not repeat preparation as if it were interrupted. On resumption, tracked
files were clean; the house-supplied world fixture was left untouched.

Read the actual merge diff against its captured main: lens.js still contains
only the reviewed 13 additions / 4 removals. Its merged raw SHA256 is
`8da105b81683eb0a4e319db3d0a7427098e32d29276e1dfaa41c467de8292985`;
the older whole-file hash is historical, not the merged file identity.
No whole-file overlay of the historical painter was performed.

RAN on this merged source: repaint race test 18 assertions passed;
partition DOM gesture test 281 checks passed (stand-in); partition model
167 checks passed; lens.js syntax and git diff --check exit 0.
No new browser timing, screenshot, caret or latency acceptance follows.

Before launching, READ the preserved dragtimes consumer and its lifetime:

- `combined-review/journeys.py` calls `hud_playtest.Window(False)`;
  Window.open calls `sandbox_window.open_edge` without a retained Job scope.
- `open_edge` calls `start` without `job=`, defaults to two startup tries,
  and therefore does not use the landed suspended Job enrollment boundary.
  Cleanup through this consumer cannot certify the descendant family.
- The existing journey output directory is hardcoded to the main checkout's
  demos directory, outside this worker's writable root.
- These three consumer files have no diff between this HEAD and the observed
  main. The Job primitive being landed does not imply this consumer uses it.

No browser, Job, guard or process was started to discover these source facts.
No denied lane was retried. The minimal prerequisite is a supported consumer
integration: retain the existing job_scope through launch and shared cleanup,
pass that same scope to suspended start, record the empty/unknown cleanup
receipt, use a single attempt and worktree-local output. Preserve the timing
journey itself and its before/after comparison. The active reliable paint-lane
commission a10672 already owns this class of harness work; request its
supported consumer rather than duplicate lifecycle/cleanup implementation.

This is an integration blocker, not evidence that Edge failed or that the
13-line repair improves latency. Sable's c10397 performance checkpoint remains
gated on actual current-world measurements at both requested sizes. Allocation
predicates remain design-only; no syntax, compact world policy or product
behavior was added in this round.

## Narrow source landing authorized, 22 October

Sable c11239/e29175 explicitly authorizes ordinary source landing of the
reviewed race/settle slice while the timing comparison remains owed.
This supersedes the hold on landing that slice, not the evidence limits above.

Ran again on prepared HEAD 75d72f65a0ca0eac7d171dac5935e3b0ca8a870c:
- `node research/window-lab/hud-dividers/test_repaint_races.js`: 18 assertions passed.
- `node research/window-lab/hud-dividers/test_partition_ui.js`: 281 partition DOM gesture checks passed (stand-in; no browser).
- `node research/window-lab/hud-dividers/test_partition.js`: 167 partition geometry/model checks passed.
- `node --check research/text-desk-lab/notation/desk-shell/lens.js` and
  `git diff --check`: exit 0, no output.

Read `git diff main...HEAD`: only lens.js and this report plus the race
regression are branch changes. The production diff has exactly the two
reviewed hunks: post-style hold/admission and overflow read/write batching.
It does not replace main's selection, context-menu or window-values changes.
The house must merge subsequent main changes under ordinary landing checks.

SHA256 of prepared lens.js:
8da105b81683eb0a4e319db3d0a7427098e32d29276e1dfaa41c467de8292985.
SHA256 of race regression:
6f9f562979875e380b10a61bb7b067b1518f3b32a1bbf1339553216228ce9c8f.

No browser, full health, current-world timing comparison, live apply or
activation ran in this round. No latency gain is claimed. Before/after at
both sizes remains owed through the shared guarded paint lane. Rollback of
the production slice is a revert of its two lens.js hunks.

## Dependency landing and second preparation, 22 October

The earlier judging refusal was the missing committed `modules:`/`crew:`
dependency, not a failed race assertion. That dependency landed via a11327.
The house then completed request e30410 (receipt c11763), merging captured main
`8949819e813fb38a9b472b34cb04b33415809427` cleanly into this branch at
`9e03c83e2875b399b2df1ec521bf9504869232f8`.

RAN on that prepared checkout: race 18 assertions, DOM 281 stand-in checks,
geometry/model 167 checks, all passed. Node syntax and `git diff --check`
exit 0. READ `git diff main`: exactly the same two production hunks
(13 additions, 4 removals), plus this report and the regression. Main's other
painter changes remain intact; no historical whole-file overlay was used.

Current lens.js SHA256:
`9bda5201534a071b3ed200332ae665ce729fb689108bb4f430e674218719f87a`.
Regression SHA256 remains:
`6f9f562979875e380b10a61bb7b067b1518f3b32a1bbf1339553216228ce9c8f`.

Coordination reply m11789 identifies no overlap between these hunks and
a11702's proposed tracks/grid-parser packing scope. This is a source boundary
comparison, not acceptance of that other candidate.
No browser, full health, latency measurement or live activation ran here.
Ordinary house judging is requested under Sable c11600. Timing and painted
continuity remain owed through the shared paint lane; no latency gain claimed.

## Version-aware judging resumption, 22 October

Sable c12656/e34546 reports version-aware judging loaded and authorizes one
ordinary serialized submission, behind right-click Comment. This supersedes
the stale Twitch-inventory hold; it does not excuse an actual test failure.

RAN read-only Git verification: preserved HEAD
`940fbf4f13477808234608c5def20e55100956a3`, observed main
`08df1c3688ad82b540d9a8e9d3cc7f120e649a63`. The endpoint lens.js diff contains
exactly the two reviewed hunks, still 13 additions / 4 removals. No newer main
painter hunk is absent from this file. The branch-only inventory remains
lens.js, this report and test_repaint_races.js; subsequent main additions
belong to ordinary house integration, not deletion.

Fresh RAN on the preserved source: race 18 assertions passed; partition DOM
281 checks passed (stand-in, no browser); geometry/model 167 checks passed.
Node syntax and scoped production/regression diff whitespace checks exit 0.
No product source was changed during this resumption.

READ current Comment card: already commission=landing. Submit behind it through
ordinary serialized judging. If refused, retain the exact exception and judged
commit rather than retry unchanged or attribute another test's failure away.

Not run: browser, full health, before/after timing, live apply or restart.
Timing and painted continuity remain owed through the shared lane. No latency
gain is claimed. Rollback remains reverting the two production hunks.
