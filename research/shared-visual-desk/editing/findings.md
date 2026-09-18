# Editing by explicit correspondence: a competing proposal

Status: bounded research, September 18, 2026. This is a design hypothesis plus an executable state model, not a proposed replacement spec or implemented Agora capability. No runtime, live world, session, or home desk was opened. The important result is a set of failures that any foundation has to confront.

## Position

The foundation should not promise that arbitrary visible output can be edited backwards into its generating text. It should support **explicit editing correspondences**: relationships between a selected subject or rendered part, the operation currently meant, and the state that operation may change. Direct manipulation and textual invocation should meet at the same domain edit implementation. Generic inversion is an optional instrument built above that boundary.

This differs from making every application one semantic tree, every pixel an addressable node, or every useful change a general-purpose source rewrite. The common substrate carries identity, correspondence, operation context, accepted change and evidence. Specialist representations remain legitimate. This may initially look like a particularly disciplined application toolkit. Its claimed improvement must be earned by lower duplication and easier recombination, not by renaming APIs.

A theme is editable content when designing a theme. Typography may be authored document material for printing but a personal viewing adjustment for reading. Thus material/presentation/instrument are roles in a particular relationship, not an exhaustive static partition of objects. Foundations' critique changed my initial formulation here.

## Primary evidence and reading coverage

These historical sources support mechanisms, not the entire proposed desk. No historical-priority claim is made.

- Foster et al., [Combinators for Bi-Directional Tree Transformations](https://www.cis.upenn.edu/~bcpierce/papers/newlenses-full.pdf), 2004 technical report. Read the formal well-behavedness definition and round-trip discussion, pp. 4–5; this is not a full reading of its 75 pages. GetPut constrains unchanged-view updates; PutGet requires an accepted view update to be reflected when read back. These are useful laws for deliberately constructed relationships. They do not identify which editable relationship a person intended.
- Hempel, Lubin and Chugh, [Output-Directed SVG Programming](https://arxiv.org/html/1907.10699v1), 2019. Read introduction and sections 4–6, especially provenance, roles and limitations. The implementation separates SVG-specific selection-to-value mapping from general provenance interpretation. Program transformations were individually authored, and the paper reports missing capabilities and visual clutter. This is evidence that output-directed editing can grow beyond literal parameter tweaks, while also exposing domain mapping and authoring costs that a generic abstraction cannot assume away.
- Prakash and Knister, [Undoing Actions in Collaborative Work](https://web.eecs.umich.edu/~aprakash/papers/prakash-knister-cscw92.pdf), 1992. Read indexed first-page abstract/introduction; full fetch failed. Their framing separates selecting whose operation to undo, finding its changed location, and resolving dependencies/conflicts. This supports treating selective undo as a semantic problem rather than restoring a global snapshot.
- Shao, Li and Gu, [An Algorithm for Selective Undo of Any Operation in Collaborative Applications](https://www.binshao.info/download/undo-group2010.pdf), 2010. Read the general principles, correctness conditions, worked text example and operation structure; not the full proof. Their mechanism concerns insert/delete operations in a replicated linear document. Its convergence and causality account does not establish correct undo for arbitrary image filters or rule systems. The example reinforces that undo must preserve ordering relationships established before deleted content is restored.
- Beaudouin-Lafon, [Instrumental Interaction](https://www.lri.fr/~mbl/papers/CHI2000/), 2000. Read author's abstract only. Instruments mediate between users and domain objects. My use here is an architectural inference: a persistent instrument can carry edit scope so every drag does not require a new ambiguity dialog.
- LispWorks, [CLIM presentation translator applicability](https://www.lispworks.com/documentation/lw81/clim/clim-ch8-2.htm), manual section 8.2. Read the short section following a lead from Foundations. Typed presentations, input contexts and gestures constrain applicable translators. This is a concrete precedent for context-sensitive edit routes; translator priority by itself is not evidence of a particular person's intention.

Read project orientation: AGENTS.md; Start Here; Constitution; Design Commitments; Agora Spec; Implementation Status; Presentation and Operators; supplied user handoff and initial literature; coordinator challenges. Existing implementation status reports object-level replacement and limited concurrency; nothing here promotes this fixture to an existing runtime contract. Prior placement memory supplied the already-known ABA and intent-level undo cautions; current model exercises them independently.

## An edit relationship, illustrated

Consider one photograph in a report, open simultaneously in a layered image editor. Dragging its right edge could change the report frame, scale the source layer, crop source material, or modify the shared image-frame style. Those changes can have identical immediate pixels and radically different later effects.

A correspondence therefore needs enough context to answer:

1. Which subject and stable part is meant, and through which occurrence?
2. Which operation and scope are active? What alternative routes are available?
3. Which dependencies make this interpretation valid: binding identity, selected range, geometry mapping, rule revision, sampled media or instrument version?
4. Which state is proposed to change, and which other appearances or maintained rules may be affected?
5. What is accepted, and how can its consequences be inspected or compensated?

This is a conceptual checklist, not a required verbose envelope for every invocation. Routine text work can report `paragraph p, edit-text; document r12` while appearance authoring expands the contributing rules and alternatives. Selection and operation discovery must be bounded without silently omitting applicable routes.

The shared authoring fact should be concrete. A frame-width binding names a state slot, its unit and constraints, and an edit implementation. A generated numeric control, a drag instrument and a textual `set frame width` command all construct the same accepted edit against that binding. Domain authors still define hit-testing, how a drag maps to a parameter, and what deserves textual inspection. Arbitrary images and custom executables do not automatically acquire meaningful textual descriptions. A manifest or accessible label alone does not prove correspondence.

An ordinary toolkit with separate adapters is a serious baseline. Measure authored mappings per operation, errors after changing the operation contract, and the ability to reuse a new instrument in a second representation. If our design still requires two independently maintained behavior models, it has not established the claimed benefit.

## Why lens laws do not decide scope

The executable counterexample uses `get(a,b) = a+b`. Both backward maps below obey GetPut and PutGet:

    put_left(v, (a,b))  = (v-b, b)
    put_right(v, (a,b)) = (a, v-a)

Starting at `(2,3)`, setting the displayed sum to 8 yields `(5,3)` or `(2,6)`. Round-trip correctness cannot choose between them. This is our constructed example, not an example attributed to Foster et al.

Likewise, the viewed width may come from a theme plus an occurrence adjustment. Provenance can reveal candidate origins, but it does not settle whether to modify the shared theme, retain an exception, or author a new rule. An active instrument can choose the normal route; ambiguous output synthesis should expose alternatives and consequences. Source-level freedom remains valuable, but ordinary work should not require editing source.

## Freshness is operation-specific

A reflow invalidates a pointer coordinate without necessarily invalidating paragraph identity. A content edit should survive irrelevant changes to typography or viewport. A graphical crop sampled against an old transform must freeze that mapping, transform the operation explicitly, or refuse/repreview. A blanket renderer-generation fence is too broad; a bare subject ID is too weak.

Targets need lifecycle identity as well as labels. Deleting a layer then creating another called Background must not retarget an old stroke. Rebinding an occurrence must invalidate old references even if the label and pixels match. Fresh observations of a rebind must resolve the new binding, not just check a version token and edit a hardcoded old target. The coordinator found exactly that latter defect in the first fixture; it was corrected and retained as a regression test.

Range identities, glyph positions, image regions and timeline intervals are different domain addresses. A stable paragraph ID does not solve concurrent insertion inside that paragraph. The fixture deliberately stops at whole-text cell replacement; it is not a text editor or CRDT.

## Undo is compensation, with a domain policy

Undoing a local width override should remove that override. If another participant changed the shared rule in the meantime, the occurrence should reveal the current rule. Restoring the old rendered width would silently author a new exception.

Undoing a shared style edit should preserve later independent paragraph work. Restoring the whole document snapshot fails that case. Checking only current equality fails an ABA case: another actor can change width 150 to 160 and back to 150, and the old operation no longer owns the last write. The fixture uses cell epochs and actor-scoped compensation to expose these distinctions.

Dependencies complicate this. Suppose the other actor rewrites a caption specifically to fit the new width. Whether reverting width is allowed is a domain/product decision. Ordinary reads are not automatically irrevocable dependencies: observing a style while fixing a spelling mistake should not block style undo. A maintained layout can recompute; an accepted operation may record a stronger semantic dependence and request joint review. The model has explicit causal dependencies to demonstrate refusal, but does not infer them. That inference/authoring burden is an unresolved cost.

Strict compensation can be too conservative: later compatible edits to the same cell will block undo although a domain transform might safely commute them. Selective text undo, vector transform undo, stroke-layer deletion, and destructive raster undo should retain domain-specific implementations behind common history inspection. A global universal inverse is not proposed.

## Continuous gestures and model changes

Media's critique adds obligations beyond versioned state. A brush stroke needs stable layer identity, an instrument definition, the relevant coordinate mapping, real input samples and any sampled dependencies. Preview may run locally at input speed. Predicted samples may be drawn speculatively but must not be accepted as real events. Pointer-up is a useful stroke boundary, not a universal boundary: cancellation, capture loss, undo grouping and long-running gestures need explicit policy.

A clone or smudge brush reads existing image material. Appending a stroke record is insufficient if its sampled backdrop changed concurrently. Retain sampled inputs or reject/recompute with a new preview; domain semantics decide which is appropriate. A seed and brush version are insufficient for portable exact rendering if the rendering engine or retained assets change.

Changing the renderer during an active stroke can preserve pixels while changing coordinate or pressure interpretation. Finish against pinned interpretation, defer incompatible activation, or explicitly migrate/cancel. Actual pointer capture, text composition, focus and latency need browser/native tests. Serialization compatibility cannot prove any of those. These are documented requirements, not implemented in model.py.

## Executed evidence and boundaries

Command: `python -B C:\Projects\Agora4\research\shared-visual-desk\editing\model.py`

Result after independent coordinator review: **14 tests passed**. Tests cover the two-lawful-backward-map ambiguity, explicit scope, shared/local fanout, stable content through reflow, rejected stale graphical mapping, repeated appearances, stale binding, fresh rebinding, style undo with later text, override undo revealing current style, ABA rejection, declared causal dependency refusal, all-or-nothing compensation, actor/double-undo checks, and negative dependency rejection. The algebraic test enumerates 343 sum-update cases per backward map.

Assumptions: serialized in-memory authority; trusted Python callers; monotone cell epochs; small fixture with whole-value writes; explicit named routes; no renderer, real media, durable log, packet loss or multiprocess races. The fixture's seed method deliberately simulates external state changes and bypasses normal commits. It is not a write gateway.

Unknown route refusal is tested. Unknown parameter discovery, schema/type/range validation, unrecognized capabilities, authentication, authority revocation, token authenticity and package isolation are **not** modeled. Dictionary lookups and actor strings are not security boundaries. The generic compensation record does not implement a complete undo/redo policy or robust untrusted-input validation. No performance, usability, new-user discoverability or whole-system conclusion follows from these tests.

## Collaborative revisions and live disputes

- Foundations changed my language from static content versus presentation classes to contextual roles and explicit relations. I agree, while retaining domain-owned edits rather than promising generic relational inversion.
- Root challenged a universal generation fence; the fixture now distinguishes mapping-sensitive gestures from identity-based content writes. Root also found fresh-rebinding misrouting and negative dependency indexing; both were repaired before freezing the first reviewed model.
- Media added prediction, sampled-backdrop and hot-upgrade cases; I challenged any claim that a state-only continuity fixture demonstrates actual capture/focus preservation. We agree those need later real input evidence.
- The open disagreement is architectural emphasis: a live/relational medium may make reuse feel fundamentally different from an API toolkit, but editing correctness still needs authored relationships and scoped policy. It remains unproven whether these can be made sufficiently cheap to author and understand. Neither the existing sketch nor this model settles that.
- Coordinator challenges fairly demand one cross-domain workflow and a blind extension after the core is frozen. I add a failure test: change a domain operation after two independent instruments consume it. Count which mappings require repair and whether their divergence is detected before user data changes.

The next decisive experiment should build the image-in-report workflow with a competent conventional toolkit as a baseline, then compare one shared edit definition against separately authored controls. Add actual reflow during typing, override undo after rule changes, and held strokes during definition replacement. A syntax decision can wait for that evidence.

## Follow-up peer review after model freeze

Media and Foundations independently identified the same declared-causality boundary: guarding a read of `theme.width` does not automatically record that a caption semantically depends on the width. The caller must also supply the strong dependency. Omitting it allows width compensation; the model does not claim automatic causal undo safety. Automatically retaining read provenance would improve diagnosis but would still not decide which reads should forbid a later undo.

Foundations also noted a specific undo/redo limitation: undoing a compensation event restores values but leaves the original event's `undone` flag true. Thus the fixture cannot claim complete history-state consistency for redo. Its tested contract is a single guarded compensation of an accepted edit, not an unrestricted do/undo calculus. This remains visible in the frozen model rather than being silently generalized into correctness.

I read Media's seven counterexample tests and Foundations' completed comparison. My critique of Media: its chosen black second stroke makes recomputation coincide with the initial snapshot, so that case demonstrates lost operation provenance but not wrong final pixels from snapshot restoration. A nonzero second pigment would expose both. My critique of Foundations: a spectrogram named before freezing cannot be a blind holdout; retain it as rehearsal and choose the independent domain afterward. These are bounded improvements to the evaluation, not reasons to discard either result.

Media subsequently reported repairing the raster case before its freeze: second pigment .2 gives accepted .35, recomputed .1, snapshot 0 and naive subtraction -.15. That revision makes the final-pixel counterexample decisive. Media also refined frame evidence: a browser frame callback establishes submission for composition under its documented timing limits, not proof of what a person's physical display showed. References to an exact frame should therefore name the capture boundary.
