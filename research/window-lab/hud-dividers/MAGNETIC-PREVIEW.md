# Magnetic preview — staged, deployment blocked

21 October 2026, worker-a8588. Base `2637cdd`. No live apply, ready,
landing, HEAD movement, backend swap or restart is authorized.

## Read / decision

Read the current partition solver/adapter, live home-tiling, JEFF's compact
direction, window-values and explicit-selection handoffs. Coordination
message m8603 names the exact source areas to the window, selection and tiling
owners. That message reaching an inbox is not an owner acknowledgment.

The missing generic capability is **a reversible candidate allocation of the
existing partition**, not another layout owner. The world still declares
membership, minima, gap, focus/companions and its fenced arrange action.
Existing partition JSON, ordinary command emission and world permissions are
unchanged. No new layout record, window-value store or chat context is added.

Only partition.js and partition-ui.js production files change:

- Use the existing drop tree and geometry for the real neighboring panel DOM
  while hovering; retain editor nodes and parents. The ghost remains a copy,
  with media/frame elements removed as before.
- Freeze pickup hit boxes and bounds. A 12 CSS-pixel spatial deadband retains
  a target across its boundary; deliberate movement leaves it. This is not a
  delay or animation. Outside bounds or no receiver clears it immediately.
  Reflow cannot move its own targets underneath a stationary pointer.
- Recompute layout only for changed targets/candidates. Ghost motion still
  follows each pointer move. Remove obsolete divider/Fit hit targets during
  preview and pending release.
- Release uses that same stored candidate once, with the original fence.
  External receivers restore the original internal allocation and retain their
  existing source/receiver fences. No arrangement writes occur on hover.
- Cancel restores original tree projection/focus and local reading offsets;
  refusal ultimately paints authoritative world state. A newer scene wins
  after a stale drop refuses. Keep busy/pending exclusion. Restore body-only
  focus loss without stealing an intentional new editor; never replay an old
  caret over typing during a pending answer.

The new `previewPlan` applies strict declared minima only to carry proposals.
Existing model, geometry and divider semantics are unchanged. An infeasible
edge can propose the existing centre-tab operation **only if the complete
remaining tree fits**, retaining its subtree structure and weights. The box
and candidate both describe tabs, not a split that will secretly change later.
If tabs cannot fit either, no candidate is offered. Do not flatten the remaining
tree, clip controls or scale below minima to manufacture a result.

This is a generic conservative solver fallback, not a responsive app policy.
At the historically measured small allocation (~202 px height), many current
trees still cannot fit. JEFF's authored compact header/dock/shelf and explicit
focus/tab policy remain prerequisites for those cases. No viewport expression,
compact lens or app-specific breakpoint was invented.

## Preserved seams

No lens.js, viewer.js, compiler, house, provider, transport or runtime changes.
Selection/contextmenu and window-value hot hunks remain separate.

READ the preserved a7987 DRAG-STALL-CHECKPOINT.md and a7925 c8331/c8401.
The 13-added/4-removed lens.js repair is **not in this checkout's base**.
It must be composed as its narrow reviewed hunk in the disposable review copy,
not by overwriting a newer whole lens.js. Its recorded repaired SHA256 was
5BC4388DE58F1B318A37CC7400857E2F67C0DDE3CE52D3621EF8BF7A26976F78.
That hash applies before any separately composed selection/tab changes.
Recompute the combined hash and run its controlled style-await regression.

Without that hold recheck, style acquisition can cross into a new carry and
paint the scene during the preview. This patch does not claim to repair it.
Existing full-scene cost and pickup cost also remain unsolved.

## Ran

- `node research/window-lab/hud-dividers/test_partition_ui.js`:
  **347 partition DOM gesture checks passed (stand-in; no browser)**.
  Added whole-neighbor hover geometry, no hover write, stable-target solve
  avoidance, frozen hit frame, sync hold, exact cancel geometry/scroll,
  320/420/600 px keyboard candidates, physical fallback, newer-world refusal
  convergence and focus/caret policy tests. Existing delayed writes, dock,
  controls, pin/focus, busy/cancel and fence tests remain.
- `node research/window-lab/hud-dividers/test_magnetic_preview.js`:
  **104 magnetic preview geometry checks passed (no browser)**.
  Bidirectional boundary jitter, escape, all sides and centre, requested
  2560x1440/1280x800 bounds, minima, tabs/strict refusal, encoding equality,
  preserved unrelated subtree/focus weights and no new identities.
- Existing `test_partition.js`: **167 partition geometry/model checks passed**.
- `node --check .../partition-ui.js`: exit 0.

`bench_magnetic_preview.js` ran 2,000 warmed CPU samples per path per requested
bound, five panels. It compares old plan-only work with new candidate plus
geometry work; neither includes DOM, ghost creation, layout, network or frames:

| Bounds | Original plan p50/p95 ms | Preview plan + geometry p50/p95 ms |
|---|---|---|
| 2560x1440 | 0.0137 / 0.0205 | 0.0217 / 0.0452 |
| 1280x800 | 0.0080 / 0.0165 | 0.0123 / 0.0219 |

These are CPU samples, not a before/after browser performance claim.
The new preview does additional geometry/DOM work; its real cost is unproved.

READ predecessor browser baseline c8331: held frames p95 16.8–16.9 ms;
1280 pickup handler 100–113 ms unchanged by the race repair; scenes
1.33–1.40 MB; release round trip 240–760 ms plus 90–185 ms paint, completion
still over 300 ms when a scene is pending. The overlapping before/after ranges
did not prove a latency gain. Those are predecessor measurements, not rerun.

## Exact staged world passage / reversal

No functional world/schema change is required for the preview. JEFF may stage
this instruction-only replacement in home-tiling after source acceptance.
The Desk read reported changes through e19301 this round; re-read and
match OLD exactly once before any future apply. Never replace the entire lens.

OLD:

```text
        tip "Panels" "Drag dividers to resize. Drag a title to a desk edge, a panel edge, or its centre for tabs; double-click to fill or restore. Fit toggles content size; ◆ pins a companion; – shelves a panel."
```

NEW:

```text
        tip "Panels" "Drag dividers to resize. Drag a title to preview the neighboring panels at a desk edge, panel edge, or centre for tabs. If a split cannot fit, the preview may offer tabs; Escape cancels. Double-click fills or restores; Fit toggles content size; ◆ pins a companion; – shelves a panel."
```

Reversal is exact NEW -> OLD after a fresh read; do not reset tree/membership,
focus, pins, music bodies or tilefoot. Source reversal is the reviewed
SOURCE.patch in reverse only after drift check and separate lifecycle approval.
New test/benchmark files are inert; no generated rules or timer exist.

## Remaining guarded acceptance / handoff

**No browser launched this round.** Previous Codex lane failed before
document.readyState/DevTools, with no measured viewport. Do not retry it.
No hidden desktop, Alex screen, account/media actions or Conversation send.
Full health and real engine input/frame/drop measurements were not run.

An admitted browser-capable worker must use a current-world disposable copy,
without resetting Alex's tree or duplicating the old eight-run baseline:

1. Preflight current hot files and compose only reviewed narrow hunks:
   a7987 paint-hold/settle repair plus this partition patch; preserve any
   accepted selection/window-value hunks. Verify hashes and syntax/tests.
2. Hidden Guard, measured 2560x1440 and 1280x800 CSS at DPR1.5. Record actual
   viewport, copy event/tree/lens identities, guard receipt and source hashes.
3. Hover global/local edges and centre in both directions; all affected live
   panels must occupy the solver allocation before release. Oscillate near
   boundaries; stop the pointer and prove no target churn. Release must match
   the last preview. Test feasible tabs and honest impossible-minimum refusal.
4. Escape, pointercancel, blur, resize, outside and external dock; delayed,
   busy, lost/refused writes and changed world/receiver fences. Check original
   tree/focus/pins and latest-scene convergence without a second commit.
5. Unsent composer words, current caret, native text/control gestures and
   viewer scroll through hover/cancel/drop/refusal; no sends. Check filled
   versus compact body continuity: hover changes outer allocations only, and
   world-guarded body variants still update on authoritative scene commit.
6. Reuse dragtimes/trace methodology for preview frame distributions, pickup
   handler, candidate-change work, pointerup-to-write/paint and long frames.
   Compare the prior read baseline honestly; no assumed improvement or waits.
   Capture before/hover/drop/cancel shots at both sizes.

Not certified by doubles: native selection/caret/focus behavior, iframe/media
continuity, actual viewport/dock clipping, visual snap quality or browser
latency. Preserve those gaps rather than labeling the feature accepted.

The lifecycle finding blocks even an inert landing: all HEAD moves can swap
deskd. Keep files preserved here and hand off the review; never set ready or
restart a host to activate this card.
