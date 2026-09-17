# A composable arrangement contract

**Status:** proposed architecture informed by executable local trials, September 16,
2026. The tests narrow the uncertainty; they do not establish a future-proof design.

## 1. What should be homogeneous

Uniformity should live in how a capability identifies its subjects, describes its
effects, prepares a change, checks assumptions, commits, and explains reversal.
It should not require every application to store rectangles or use the same engine.

A calendar, desktop, outline, graph and task board can participate in one environment
while retaining different layout policies. Their common protocol should allow a
coordinator to ask:

1. What stable things can I address here, and what do they represent?
2. What operations are supported, and under which immutable contract?
3. Which observed facts and measurements does this proposal depend on?
4. What native changes would it make, with what domain meaning?
5. Can those changes compose with the other requested changes?
6. What was accepted, what was actually rendered, and what can now be reversed?

Applications own domain semantics; the native gateway owns admission. A package
cannot make a change admissible merely by describing it as a layout operation.
Operator libraries and interaction controllers are implementations of this contract,
not the enduring center of the architecture.

## 2. Identity and ownership

Distinguish subject, occurrence, arrangement, and open view:

| Identity | Example | Owns |
|---|---|---|
| Subject | OAS meeting notes | Text, tags, task state, semantic relationships |
| Arrangement | Planning board | Membership and authored organization |
| Occurrence | Second use of those notes on Planning | Subject reference and local placement intent |
| Open view | Alex's second window onto Planning | Camera, focus, selection, drafts and measurement context |

The same subject can have multiple occurrences in the same arrangement. The same
arrangement can have multiple open views. Neither relationship is one-to-one.

A useful address has a world/namespace, arrangement identity, occurrence identity,
and incarnation or equivalent never-reused identity. It need not mandate a separate
database row for each occurrence. Embedding is a storage choice; stable addresses
and well-defined effects are the interoperability choice.

The containing arrangement owns its immediate children's placement. Moving a board
window moves its descendants visually without changing their local coordinates.
An operation on the desktop does not recurse into every board by default. Cross-level
selection or moving between containers is explicit; a container tree cannot cycle.

An arrangement is retained user work. An application supplies its behavior and can
be replaced. Losing a package must not destroy the arrangement or its content. A
missing renderer should leave inspectable retained data and explicit unsupported
operations. A saved workspace must not embed live leases, credentials or adoption
authority. Recovery controls remain outside authored stacking and selection scope.

The current Agora4 application view bundles subject binding, bounds, UI state and
runtime lease. Splitting those responsibilities requires a migration, not just a
new name for the existing record. Closed views and restored workspaces need explicit
reopen/rebind semantics. This lab does not implement that lifecycle migration.

## 3. Walk through the actual scene

Assume the request refers to one identified open desktop view. Its arrangement has
forty occurrences, eight related to OAS, one mail-thread occurrence that is also
OAS-related, and thirty-one other occurrences.

First resolve a bounded universe U: the open occurrences of that desktop, not every
object in the world and not every descendant card. Resolve the intended mail thread
and one of its occurrences. If it is closed, opening it is an additional explicit
effect with its own lifecycle rules; do not pretend it was already selected.

Resolve three disjoint sets:

```
M = the selected mail-thread occurrence
P = OAS-related occurrences in U, excluding M
R = U minus (P union M)
```

Pinning M takes priority here. That is a declared decision for this request, not
a universal precedence rule hidden in the layout engine. A different request might
deliberately include an occurrence in two compatible operations.

The semantic resolver returns identities, evidence, uncertainty and completeness.
It may use tags, links, search, content or model inference. The geometry planner
receives concrete identities. This keeps probabilistic interpretation out of the
deterministic commit boundary without pretending interpretation itself is infallible.
When selection is incomplete, "everything else" cannot truthfully mean the complete
complement. Return an incomplete plan or use an explicitly bounded interpretation.

The lab chooses an **exact-scene** policy: if membership or relevant classification
changes before acceptance, the plan becomes stale. A future **captured-members**
policy could intentionally leave newly arriving appearances untouched. A maintained
selection would be a third policy. These are different contracts, not optimizations
that the implementation can interchange invisibly.

Prepare three semantic actions:

- Tile P in a measured region on the left.
- Place M in a useful region and ensure its stacking relationship supports visibility.
- Sink R below the selected work within each participating stratum.

This lowers to rectangle changes plus stacking constraints. "Three operations" is
a human-scale description, not a restriction to three low-level effects. Work and
event size still scale with the affected set. One intent reduces administrative
burden; it does not make forty state updates computationally constant-cost.

## 4. The intent envelope

Selection/operator/parameters remain a good authoring vocabulary. A reviewable
prepared plan also needs the following information, conceptually:

```
request identity and authenticated caller
purpose, original request reference, and structured operation descriptions
addressed surfaces, occurrence identities and resolved selection policy
immutable operation/adapter contracts
read dependencies and their versions
measurement identity, coordinate frame, units and generation
proposed native effects and conflict/join semantics
constraints, diagnostics, and declared semantic effects
undo recipe or honest reversibility limits
```

These need not be a large user-written DSL. The service can derive most fields
from scoped reads and known operator contracts. A small human/JEFF request expands
into a complete checked proposal.

The plan is immutable once previewed. A plan ID names its exact contents; it is
not authority to execute. Commit rechecks the current caller and delegation. A
stale explicit preview must not silently execute a newly computed layout. A fresh
direct command can replan under a documented policy, but its receipt must identify
the plan actually accepted.

History retains structured operations and concrete effects. A sentence renderer
can summarize those records with a pinned vocabulary. The sentence is explanatory,
not an alternative source of truth. Replay never reruns semantic resolution,
operator code, models or external effects.

## 5. Composition has two distinct forms

### Compatible contributions over one snapshot

Independent contributions read one immutable snapshot. Disjoint effects combine.
Equal effects on one register can coalesce. Unequal replacement effects conflict.
There is no implicit last-writer-wins based on package loading or model call order.

Structured effects may define a narrower join. The prototype merges stacking
constraints as a directed graph and computes a stable topological order. Existing
order breaks unconstrained ties. Cycles cause refusal rather than an arbitrary winner.

For example, "sink A below everything else" and "sink B below everything else" are
each valid alone but contradictory together. A below B and B below A cannot both
hold. Meanwhile sinking the complement and raising the mail thread are compatible.
The six-contribution test includes those two effects on the same stack register;
all 720 arrival orders produce the same plan digest.

Read/write interference also matters. If one contribution changes tags that another
used to select targets, the writes may be disjoint and still affect each other's
meaning. The first model missed this. Contributions now retain their individual
read/write footprints, and undeclared dependencies are rejected. The same principle
applies when one contribution changes the dimensions used by another's layout.

### Explicit stages over provisional state

Some requests are intentionally sequential: classify these items, then arrange the
result; enlarge the container, then lay out its children. Such operations cannot be
made independent by calling them a batch.

The model supports explicit stages. Each stage sees the preceding proposed state;
all stages remain in memory. External guards still refer to the original accepted
world. A failed stage yields no published partial plan, and the final native effect
set is committed once. The operation history retains the stage order.

No generic fixed-point solver is needed for this slice. A future layout that requires
iteration must specify a finite budget, convergence or failure behavior, and what
counts as a usable result. A universal cascade of reactions would reintroduce hidden
sequencing and is not justified by these tests.

## 6. Admission and concurrency

The coordinator gathers proposals; adapters do not perform native writes during
planning. At the gateway, under the native transaction boundary:

1. Resolve the issued plan and current caller authority.
2. Recognize an already accepted request and return its durable receipt, or reject
   reuse of the request identity for different contents.
3. Check identities, operation versions, membership, read dependencies and observations.
4. Construct the complete candidate state.
5. Validate domain invariants on that candidate, independently of operator names.
6. Append one event and materialize all native changes with its receipt atomically.

The actual authenticated gateway remains the write path. No new database writer is
needed. The lab simulates these steps with one in-process lock; production must use
the existing process-safe native transaction boundary.

Use revisions at meaningful semantic units, rather than automatically at every JSON
leaf. Text and placement should not invalidate each other. A placement rectangle can
be one coherent register. A stack permutation can initially be another. A sorted
view's order policy is not just a set of independently writable positions.

The prototype uses separate semantic registers to test these boundaries. Agora4
currently versions complete containing objects. Initial integration may conservatively
conflict at that granularity; splitting placement from view-state/lease records can
remove avoidable conflicts. Existing revision checks must never simply be bypassed.

An index or collection epoch is needed for negative selections. Checking only the
objects that happened to match does not detect a new member. The tests cover both
an occurrence leaving the selected universe and a new occurrence entering it.

Independent valid actions can violate a global invariant when combined: two proposed
parent changes can create a containment cycle. Candidate-state validation belongs at
admission, not only in each operator's local checks.

The native-world atomicity claim stops at the native world. Applications backed by
external services can join a workflow with explicit effect/uncertainty records; they
cannot promise atomic rollback of sent mail or a remote meeting change. A Tasks drag
that changes status must declare that semantic effect. An arrange-only request must
not silently acquire it from geometry or target location.

## 7. Geometry, order and visibility

Retain the kind of intent that matters: a free rectangle, a list order, a tile slot,
a grid policy, a graph anchor, or a domain-specific placement. Effective rectangles
are often derived. Selecting a universal rectangle schema would erase those meanings.

Keep at least three orders distinct: reading/navigation order, layout placement order,
and front-to-back stacking. Sinking a window should not rewrite keyboard navigation
or the underlying list order as an accidental side effect.

Stacks belong to their containing surface and stratum. Raising a normal window does
not place it above protected recovery, another stacking context, or an unrelated
modal. The model explicitly keeps an overlay stratum separate. A correct plan can
therefore still fail a stronger global visibility request. It must diagnose that
limitation or use an allowed operation on the relevant container.

Measurement records identify the actual open view, viewport, coordinate frame,
transform and generation. Missing measurements are not permission to assume 900px.
The first adapter accepts identity transforms only. Nested transforms, browser zoom,
scroll, reflow and clipping require real adapter work and browser evidence.

A browser can resize after a native commit. State atomicity cannot make physical
display geometry atomically immutable. Distinguish **accepted arrangement** from
**observed rendering**, and verify the rendered result against the request when it
matters. The lab tests stale observation rejection, not real display synchronization.

Forty readable windows cannot necessarily fit. Minimum size and accessibility cannot
be wished away by a solver. Offer grouping, scrolling, a different region or a
different presentation. The lab refuses impossible tiling instead of shrinking
below its declared minima. It uses eight OAS items on the left, not forty tiny cards.

## 8. One-time arrangement versus maintained layout

"Put these here" can be a one-time operation. "Keep OAS things here" creates an
ongoing policy with future membership, ownership, and lifecycle implications.
The former should work before the latter becomes a framework.

An effective placement needs an identifiable owner. If a grid owns placement, dragging
must mean reorder, change an offset, detach, or edit the rule. A manual coordinate
writer and a reactive rule cannot both silently own the same value.

The model uses a simple free/managed placement variant. Literal movement refuses
managed placement; an explicit detach changes the mode and retained placement in
one operation. Undo restores that retained mode. This is not a complete maintained
layout engine: deleting or editing the referenced rule needs additional dependencies
and lifetime checks before restoring its ownership can be considered safe.

## 9. One undo means a new, checked operation

Do not restore an old whole-world snapshot. Undo constructs a compensating proposal
for the exact semantic registers changed by the accepted intent. It uses the original
preimages and checks whether those registers still have that event as their last writer.
Unrelated document edits and changes to other arrangements remain intact.

Checking only that the current value equals the old result is insufficient. Someone
may have moved a window away and then back. The tested compensation detects this
ABA case through versions, preserving the later decision rather than erasing it.

Undo rechecks target identity/incarnation, compatible operation contract, current
authority and current domain invariants. A larger new minimum size can make the
old rectangle invalid even if nobody moved it. An upgrade may require explicit
translation; an unrecognized old operation should become inspectable and non-executable,
not be reinterpreted by a new contract with different meaning.

If one affected placement has been independently changed, the first implementation
refuses the whole compensation and explains the conflict. It does not silently undo
39 of 40 changes. Selective undo, preserving later relative movements, or restoring
only uncontested parts could be useful future contracts, but must name their semantics.

Stack order is initially a whole semantic register, so any later stack change can
block undo. This is conservative and potentially frustrating. A more selective
relation-based undo should be motivated by actual use and separately tested; it
must not be advertised as already solved by per-property writes.

## 10. What the trials changed

| Attractive assumption | Counterexample | Revised contract |
|---|---|---|
| Atomic persistence is enough | Failed planner leaves a partial proposal | Contribution failure invalidates the builder |
| Disjoint writes compose | One operation changes another's selection inputs | Track per-contribution reads; declare stages |
| Each valid ordering action composes | Two different "sink below all" requests cycle | Checked constraint join, explicit refusal |
| Matching current values make undo safe | Move away, then back to identical coordinates | Check last-writer versions and incarnation |
| One-time coordinates guarantee visibility | Higher stratum or later viewport change | Separate stacking and observed rendering |
| One snapshot solves every request | Child layout needs proposed parent dimensions | Explicit provisional stages, one final commit |
| Sharing one subject implies one placement | Two occurrences and two arrangements | Stable occurrence identity and local ownership |

The first two failures were reproduced against the first model and preserved in
`evidence/round-1-counterexamples.json`. The remaining rows are modeled rejection
or invariance cases, or explicitly identified rendering limits, not claimed live bugs.

## 11. Integration into Agora4

The current source already supplies appearance identity separate from content,
authenticated admission, atomic native batches, retained package versions and
replay. It does not expose the composed arrangement contract tested here.

Relevant inspected implementation points:

- `src/agora3/applications.py`: one-view `position`; protected application records;
  current 32-open-view cap; separate view and content identity.
- `src/agora3/application_specs.py`: no caller-observed revision in `position`.
- `src/agora3/gateway.py`: authenticated write callback, authority and protected records.
- `src/agora3/world.py`: 1–200 change atomic journal commits; object-level revisions.
- `examples/native-applications/desktop/desktop.js`: retained bounds, local z-index.
- `experiments/visual-presentation/presentation/`: retained rules, evaluator and bounded
  undo for the earlier note/card model, not an adapter for current application views.

Start with one native desk arrangement and a package-supplied layout planner. Add a
protected admission operation that accepts a prepared batch of authorized appearance
changes and records its structured intent/receipt. It should gather updates through
the existing gateway once, not call `application.position` repeatedly inside a loop.
Keep the old position operation as an adapter to the same semantics where compatible.

First production acceptance: actual visible OAS scene, stale preview, refused complete
batch, lost-response retry, document edit after arrangement, and one undo. Confirm
appearance/content continuity in the human browser, including held-pointer behavior.
The lab's forty-item case does not raise the production 32-view cap or prove the browser
can render forty independent applications well.

Then adapt an independently authored list or board. If its implementation requires a
second transaction protocol, source introspection, or surrendering its domain meaning,
the common contract is not yet adequate. Code reuse can be versioned source bundled
into pinned releases; a universal package dependency resolver need not come first.

## 12. Open questions before making the contract permanent

- Can a genuinely independent adapter use these concepts without this model's tuple
  keys, embedded membership lists or Python implementation? Not tested here.
- What scope and confidence policy lets semantic resolution feel immediate while
  keeping incomplete or ambiguous selection honest? Exact-tag fixtures do not answer it.
- How often will exact-scene guards reject under active collaboration? Should some
  commands default to captured-members instead, and how should that be conveyed?
- How should selective stack undo preserve later ordering decisions? The current
  whole-stack guard is intentionally conservative.
- What is the minimum protocol for nested measurement and parent/child reflow across
  sandboxed frames, without giving applications control over protected UI?
- How are occurrence creation, deletion, portable configurations and missing packages
  migrated without conflating authority with retained layout data?
- Which content changes should trigger remeasurement? Guarding all text defeats
  useful concurrency; ignoring content-dependent preferred size can invalidate a plan.
- How do contract upgrades retain useful historical undo without executing old,
  no-longer-adopted code? Retained data and explicit bounded translations are candidates.

The durable commitment is a common language for **what is being changed, why its
effects can compose, and how to recover**. Engines, storage granularity, concrete
operator catalogs and rendering technology should remain replaceable behind it.
