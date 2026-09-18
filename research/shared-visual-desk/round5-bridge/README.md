# Round five: the bridge is the experiment

2026-09-18. Alex redirected the team away from building another desktop. The question is whether inhabitants can change structure, appearance and behavior through their shared environment, without each application requiring private JavaScript/CSS or shell work.

Status: source-based joint research, definition-only authoring trials, conformance probes and a narrow executable action-binding experiment. No new desktop, renderer, live-world migration, VM execution or installed Agora capability was built. Claude's source remained owned by Claude. Their evolving `scene.py`/`lens.js` are the common experimental starting point, not a reason to create a competing DSL.

## Result so far

The common direction is **authorable definitions compiled into inspectable, revision-bound scene packets, with actions executed through the existing world operations**. A scene reduces duplicated application logic but does not by itself guarantee equivalent text, graphics or input behavior. The packet needs a contract for identity, coverage, computation, interaction state, measurements and supported actions.

The authoring trial transforms the same content from spatial cards to an editorial reading view to a read-only index using ordinary Desk create/read/rewrite/undo. The host, painter and style source remain unchanged during the trial. This is meaningful definition-level authorship. It uses existing style roles and native operations; it does not demonstrate new role installation, rich text, domain engines or a source-blind model discovering the system.

The action-binding experiment preserves exact strings and original observation revisions using the actual experimental Desk. It is deliberately smaller than a repaired full bridge: its typed packet is NOT consumed by Claude's current painter or text printer. Integration must change those generic adapters together, not patch individual apps.

## The authoring boundary

We distinguish implementation work on a reusable runtime from ordinary authoring within it. Building the runtime may require code. Once frozen for a trial, however, changing a view's hierarchy, binding, role, layout policy or supported interaction must be a definition operation. Any required app-specific host edit is a recorded failed requirement, not hidden setup.

An advanced new engine may require executable implementation, but it must become a reusable, versioned capability that can be inspected, exercised, installed and composed through the environment. Merely moving each app's private JS into a package does not satisfy this goal. The invention test starts with the capability absent; the next author must reuse it without patching the bridge. Existing Agora packages/applications provide parts of that lifecycle; arbitrary nested components and the common inspect/interaction contract are still missing.

## Proposed common contract

These are research proposals except where the evidence table below names an implementation.

1. **Definitions are retained world content.** Structure, queries, role bindings, computed properties and action references have identity and revisions. A candidate may be malformed without destroying the active definition. Validation, preview, activation and recovery are distinct operations. Style definitions must eventually have the same lifecycle; a fixed external CSS/style file is not enough.
2. **A compiled frame records its dependencies.** Stable part and occurrence IDs, subject bindings, definition/component/style revisions, material read dependencies, supported actions and observation coverage travel together. Incomplete/opaque data is marked rather than invented. A repeated list index is not automatically a stable item identity.
3. **Both projections consume the semantic frame.** The text projection is allowed to summarize but must label omission and supply a way to inspect the remaining range. The graphical projection must expose unsupported parts/gestures. Agreement tests cover identities, material, actions and status; neither a shared tree nor a font role proves pixel equality or accessibility.
4. **View state has a declared home.** Drafts, selection, scroll, focus, playback sessions and active gestures belong to identified viewers/views or activities. They are not all permanent world material and are not silently shared. Inspection can expose who is editing or a selection anchor when appropriate without automatically disclosing private draft text.
5. **Actions bind to what was offered.** A typed action refers to a resolved subject or occurrence and the definition/operation revision that gave it meaning. A stale action is not renewed by a fresh `look` at commit. Exact values remain data, including empty strings, whitespace, quotes, backslashes and dollar signs. No command-template sanitation changes document content.
6. **Layout requests and measurements differ.** A definition supplies layout intent. Font-dependent bounds, clipping and hit regions are observations tagged with frame, viewport, scale, font/renderer revision and freshness. Pointer input is interpreted using the frame captured at gesture start. Measurements do not become author intent merely because the renderer reports them.
7. **Components are an extension boundary.** Rich prose, raster/vector work, media transport and code editing can use reusable engines with typed material, selection, actions and honest inspection. A closed widget catalog plus appeals to the host developer is not a sufficient invention mechanism. The bridge remains generic while installed components add behavior.
8. **Incremental delivery preserves correspondence.** Stable keys plus dependency tracking and ordered frame revisions enable bounded updates. Deltas name their base; an out-of-order update cannot silently replace a newer frame. Missing bases require resynchronization. This is proposed, not implemented by the current 1.5-second poll.

## Response to Claude's eight concerns

Read their complete `design-studio/THE-MISSING-PIECE.md` and Mailbox a596. Their ideas are proposals and source evidence, not additional user instructions.

| Concern | Our position and next discriminating check |
|---|---|
| Worse HTML / inner platform | Do not win by counting fewer syntax lines. Keep a small semantic composition layer, typed capabilities and explicit extension. Freeze the host, give an author an unanticipated structural change, and count escape paths. Complex composition may be legitimate; duplicated browser internals and app-name cases are the warning. |
| Ephemeral state | Give interactions/view state explicit identity, lifecycle and revision correspondence. Keep committed content distinct. Preserve draft/selection across unrelated frames and failed activation. None of our current prototypes implements the whole contract. |
| Native editor parts | Reuse capable engines behind an inspectable contract. A part must expose material/selection/action semantics and opaque limits, not just return a prose caption. Count what authors can do through the part, not how few widget names exist. |
| Font metrics/layout | Feed measurements back as observations with frame/viewport/font provenance. Declarative geometry and measured geometry are different facts. Do not assert text knows exact wrapping before measurement. |
| Computed values | Our existing bounded pure expression evaluator can express arithmetic, conditions and composed effects with read-before-write semantics. The current lens grammar cannot express the tested spacing formula without extension. Reuse a small expression mechanism if needed; do not hide every new measure in an app callback or put time/network effects in expressions. Integrating it into scenes remains untested. |
| Conditional appearance | Lens chooses semantic structure/roles; style resolves token/property contributions. Define precedence/conflicts and show why a property won. A user's local override needs explicit scope. Do not give both languages competing uninspectable CSS cascades. |
| Cost | Keep stable instance identity, bounded queries and projection dependencies now. Add ordered changes/subscriptions and incremental rendering once correctness is testable. A whole-tree rebuild is acceptable experimental machinery, not a scaling result. |
| Shell as lens | Yes as a hypothesis: shell composition should use the same authoring mechanisms. Independent recovery remains outside the authored shell. We are not building a new shell to prove this round. |

One thing our unchanged rule evaluator demonstrably expresses that the **current** lens grammar does not: change an authored arithmetic spacing expression and have it calculate placement for present and future selected objects, with incompatible writes refusing as one proposal. This is not a claim that a lens could never acquire that mechanism. Our old workbench still failed interface-structure authoring and was weaker at shared-world semantics; these are complementary findings, not a contest to preserve either prototype.

## Executable evidence

- [Definition-only authoring](authoring.md): 14 checks using actual Desk commands in a disposable in-memory world; three retained `.lens` fixtures and their scenes/text/evidence. Eleven host/style hashes unchanged within each run; zero app JS/CSS edits or embedded raw code. This is deterministic native-command execution, not a browser gesture or independent model trial.
- [Actual scene/compiler audit](foundations.md): 18 observation assertions, distinguishing supported behavior, limitations and defect reproductions. Original source snapshots/hashes and subsequent repair observations are retained. A passing defect assertion is not a supported user workflow.
- [Actual handler probes](extension-contract.md): six reproducible input/lifecycle counterexamples through unchanged lens.js handlers in a controlled Node DOM/fetch stub. No HTTP, real browser or live session mutation.
- [Prepared actions](prepared_actions.py): seven tests against Claude's actual `scene.build` and `Desk.dispatch`. No second object world, parser or app renderer was implemented. Two admitted generic operation templates adapt rewrite(subject) and move(appearance).

The coordinator independently executed all four sets. During the rerun Claude changed the compiler: `$n` became a resolved count and the silent 100-character truncation disappeared. Two original defect assertions therefore failed because those defects were fixed. The audit records that transition and turns the two into positive regression checks; it does not suppress the evidence or claim that the old bug assertions still pass.

Run from Agora4:

```powershell
python -B research/shared-visual-desk/round5-bridge/authoring-probes.py
python -B research/shared-visual-desk/round5-bridge/scene-probes.py
node research/shared-visual-desk/round5-bridge/hostile-fixtures/lens-handlers.mjs
python -B -m unittest discover -s research/shared-visual-desk/round5-bridge -p test_prepared_actions.py -v
```

## Exact scope of the action experiment

`Bridge.offer(actor, definition_id)` compiles a known finite fixture and binds actions under one owner lock. The returned frame contains host-retained action handles. `inspect` exposes operation, exact target, definition revision, expected material revision, inputs and retained parent coordinate guard. `invoke` receives only a handle plus typed input; a caller cannot retarget it. `cancel` invalidates an unused action.

The tests establish literal round-trip including empty strings, refusal of an old frame after another actor's edit even if a new frame was fetched, refusal after a definition edit, acceptance after an unrelated subject edit, independent movement of one of two appearances while a content action stays valid, typed-input refusal, cancellation and single-use success. Unsupported templates/gestures are exposed as unsupported, not passed through as code.

Limits: no authenticated transport, disk durability, compiled package invocation, live painter integration, native Agora installation or automatic frame expiry. Actor strings are attribution only. Outstanding handles are bounded at 128 and require use/cancellation. The existing compiler remains unbounded; only finite fixtures are offered. Staging deep-copies a single-owner in-memory Desk and excludes rules, external hooks and clock following, so no external-effect rollback guarantee is implied. It uses object-level revisions; it does not invent per-property concurrency. Move inputs must already be parent-local world coordinates; browser camera/style changes are not tested here.

Independent review caught that the prepared frame's action descriptors lack the `line` expected by both existing printers. That incompatibility is intentional in the experiment's typed boundary but remains an integration task. We do not call this a repaired end-to-end bridge. The next port must update the two generic projections together, with no per-app adaptation.

## Teamwork and next foundation milestone

Three Astra High researchers used their own team desk: Editing a140/c146/c147, Media a142/c143/a145, Foundations a149/c150/c151. Root alone carries findings to Claude's separate Mailbox: a591 initial packet, a596 their full response, c650 interim executable results, c661 considered response to their eight concerns. The teams retain separate working spaces. No unattended polling or background continuation was installed.

Next milestone: a definition/capability candidate is validated and previewed, activated without destroying current material/drafts, rendered and inspected from the same revision-bound frame, and invoked through exact typed actions. Pass the same transformation with host/painter hashes fixed, then introduce one genuinely new component through the existing package lifecycle while those hashes remain fixed. Until that succeeds, a more polished desktop is not evidence for the foundation.
