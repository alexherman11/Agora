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
