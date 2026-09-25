# Shared Lens compiler: pressure test from four visual views

25 September 2026 · Astra team synthesis for Alex. **Research review, not an adopted design contract.**

## Alex's steering, in his words

These are Alex's statements and questions from this work, kept separate from the team's conclusions:

> "you should not focus on the finished product (making something pretty), you should work together to imagine, think through, ideate, prototype, and refine a way for Lens to be represented visually."

> "okay the 150 line limit is obviously silly"

> **Agora doesn't necessarily need to build a collection of AI-generated applications.**
> It might instead build a sufficiently expressive **shared object world + Lens system**, where application-like interfaces *emerge as useful views over that world*.

> "Lenses are important for the user to see the world, but they also structure it for JEFF and agents to see it as well no?"

> "see how they fit into the vision of making it not get heavier over time."

The first two changed how we framed and judged the prototype. The shared-world statement is the proposition we tested, not a claim that the tests proved it. The question about JEFF makes the text scene an essential reader of every Lens, not an optional description of a visual application. The growth question motivates the measurement below. None of these quotes adopts an implementation mechanism on Alex's behalf.

## The answer in brief

The visual bridge supports a useful claim: one set of native objects can appear in substantially different Lens views, with the same addressed edit visible in both. It does **not** yet show that arbitrary applications can be assembled without new host code. The four views were deliberately bounded: the Studio did not navigate, the ledger did not calculate its totals, the discussion pane opened fixed subjects, and the spatial board had no paths or pan/zoom.

The branch started from `008eeb8`, where `scene.scene_for` **already delegated to the staged compiler**. What the branch did *without* was the completed shared-compiler vision: a complete read boundary, independent IR semantics, library-defined composition and calculation, and measured cheap extension. The branch's four new visual words still needed coordinated edits in the parser, evaluator, text printer, paint projection and browser. That is the pressure test, rather than evidence that staging was unnecessary.

The experimental code and browser receipts are on `research/visual-bridge-collaboration` at `112a182` in the existing `C:/Projects/Agora4-collaboration` checkout. They have not been integrated into the running `frontier` Desk. Main is `008eeb8` for this review. We made no source edits or native-world events during this investigation; reading the shared Desk updated the caller's per-actor read state.

## What building the views cost

| View | Authored Lens | What it showed | Additional host need |
| --- | ---: | --- | --- |
| Research Studio | 30 lines | Three panes, native block editors, tasks, metric | The shared columns, button, editor and meter primitives |
| Household ledger | 24 lines | The same block, task and metric parts over different objects | No ledger-specific renderer; amounts and caps were stored fixtures, not calculations |
| Discussion | 24 lines | Addressed event rows, responses and a keyboard action | A 139-line `attention.py` routing provider and registration in `scene.py` |
| Spatial board | 8 lines | Read-only previews of the Studio's same block subjects | Existing `free`, `spread` and `clamp`; no new spatial renderer |

**Read:** These are 86 lines of view definitions, not four finished applications. The fixture builder deliberately repeats 14 lines of Studio component definitions in the ledger. Placed Lenses have no explicit input parameters today, so this is an opportunity to test reusable parts, not proof that the duplication was unavoidable. One edit of `s03` in the Studio appeared in an already open board in an isolated browser test (`shared-views-observation.json`). The four new words changed generic host code; no Studio, ledger or Inbox case was added to the painter. The discussion routing logic is a real semantic addition, not just styling.

**Read:** Ignoring line-ending normalization, the branch changes 13 production files by +650/−83 lines across visual primitives, routing, draft and observation safety, and a Windows session-lock repair. It also adds 785 Python test lines. Dividing that total by four views or four words would falsely treat discovered safety repairs and the routing provider as the cost of a paint word. The prototypes show *some reuse after a platform investment*; four chosen views cannot establish a long-term cost curve.

The safe editor reveals why a genuine new primitive has a legitimate cost. It must identify its complete native edit target, print that scope for an agent, render a usable multiline control, retain the person's original observation through a refused or delayed save, and send one addressed action. The branch's admission currently recognizes the exact whole-text rewrite shape. Another editable aspect would need a declared operation/effect-scope contract rather than another command-string special case.

## What the staged compiler does now

**Read and ran:** Main has table-driven Lens parsing, name resolution, a lowering pass with `bind`, `lets`, `guard`, `emit`, `acts` and `place` fields, and an active `lens_ir` evaluator. `scene.scene_for()` calls it. The old evaluator remains as a comparison path. The read-set repair was checked in 948 in-memory gesture perturbation trials with zero unsound results for that trial's scope. These are meaningful steps. **On the visual branch**, the new words entered that shared scene, and meter values and invalid states were interpreted once for text and pixels.

The staging is incomplete in ways that matter to future growth:

- The lowered part still carries the original AST. Evaluation still has feature-specific branches; the text printer and paint emitter also learned the new visual kinds. A new surface word is not yet merely a parse row and a small lowering.
- The recorded `Accessor` is not the evaluator's only route to the world. Geometry and relation reads use `w.nodes` and `w.relations` directly. **Ran in memory:** keeping accessor answers and its recorded `R` fixed while changing an appearance width changed the emitted box from 1264 to 321. The current read log is therefore not a complete account of scene inputs. The 948-trial gesture test does not claim otherwise.
- `Accessor.rows` records the source and row count, not stable row identities, values, actor inputs or provider generation. That is especially visible for `attention`, whose routing depends on event history and the addressed actor. This is a dependency-contract gap, **not** a demonstrated stale-write exploit.
- The branch improved the compiler receipt to hash both `scene.py` and `lens_ir.py`, but `attention.py` is still outside that identity. A frame should identify the implementation and inputs that actually produced it.
- Scenes still reparse, resolve, lower and evaluate in full. Incremental rebuilding from a shared read log is a proposed benefit, not a current result. Compiler-local `_lens_good` also remains hidden fallback state.

**Ran:** The existing `experiments/growth/measure.py` reports `scene.py` at 1,164 lines, the *old* `make()` at 217, and `lens.js` at 150. It omits the active 455-line `lens_ir.py` and counts old branch syntax rather than parse-table entries. Its post-refactor zero parse branches is not evidence that extension got cheaper. The proposed median of at most 20 core lines per new word has not been verified.

## What “doesn't get heavier” should mean

The useful target is **less host work per new application**, with complexity paid once for capabilities that are genuinely shared. A button's keyboard, action and refusal behavior deserves a common implementation. A fifth application should be able to use that implementation without new Python or JavaScript branches. A new path or image primitive may also deserve host code; a fifth app-specific chart should not.

Measure three costs separately:

1. **New platform capability:** changed host modules and semantic cases, including text account, painter, action/fence, accessibility and continuity. A genuinely new paint primitive is not comparable to a syntax alias; the proposed 20-line word threshold needs that distinction.
2. **New application assembly:** host changes versus Lens/library definitions, native objects and data. Ledger and the spatial board are encouraging reuse examples; the `attention` provider shows where it stopped.
3. **Later change:** how many places must change when a view gains a new field, selection, formula or control? Duplicated component text and hardcoded detail subjects are small warnings here.

The compiler should share **meaning**, not force every concern into one file. A common evaluator can resolve names, queries, typed values and dependencies; Lens composition can emit addressed scene parts; the text and pixel readers can consume those same parts; native effects still need the gateway; viewer-local navigation needs an explicit private state contract. New host code is justified for a new primitive or trustworthy source of facts, but not for each application name or chart shape.

A Lens also organizes what JEFF and other agents can perceive. The text scene should identify the same native targets, source values, omissions, viewer choices and possible actions that shape the person's picture. The branch printed the complete editor target and meter inputs, but it did not solve viewer selection or give a full text account of future paths and graphics. Test an agent doing the same task through the text scene alongside browser input; matching source JSON alone is not enough.

## Which advanced features would have helped these tasks

| Feature under discussion | Concrete gain in these views | Limit it does not solve |
| --- | --- | --- |
| **Viewer-local state and identity-based selection** | Studio contents and Inbox rows could open a chosen native subject; two viewers could keep different panes open without writing shared props. Agent text could name the selected subject. | Requires a declared viewer input, local action, stable identity and draft-switching rules; it is more than a visual word. |
| **Arithmetic, aggregation and total `if`** | Ledger totals and remaining amounts could derive from metric rows and respond to added categories or missing values. A meter would then show computed data rather than hand-maintained props. | Financial units, rounding, allocation checks and valid time still need explicit semantics. |
| **Named, parameterized library parts** | Studio and ledger could share one block editor, task row and metric card with explicit inputs and pinned definition identity. | A library cannot invent a safe edit target or an attention event stream that the world does not expose. |
| **Generic row queries over native events and relations** | Some attention routing could become authored, reusable query logic instead of a dedicated `attention` Python branch. | Historical addressing and participation need well-defined event identities, time and authority; listing a row does not prove delivery or reading. |
| **Shared read-set and proposals** | Text and pixels could explain the same formula and action; compound commands could preview their whole cascade and refuse atomically when stale. | A complete dependency log must be established before incremental reuse. It does not create paragraph-level edits. |
| **Anchored text units** | Two people could edit distinct paragraphs of one document while the document remains assembled for reading. | This changes native identity, conflict and undo semantics; a richer Lens alone cannot make whole-text replacement concurrent. |
| **Path/image/transform primitives** | The spatial board could show actual links, scaling and spatial relationships; charts could be composed from general marks. | Pan/zoom and navigation also need viewer state and local actions. Each primitive needs a truthful text account, stable hit targets, input handling and performance limits. |

Nesting is useful syntax for the calculated ledger, provided the compiler lowers it to printed steps. It is less urgent than getting correct input dependencies, missing-value behavior, and a real sum. A single expression evaluator for pure Lens reads and proposed actions is a direction in the round-six proposition, not an installed behavior language.

## A bounded next sequence

1. **Make the existing boundary true.** Either route every scene-affecting read through the accessor or temporarily record a conservative identity for *all* effective inputs: world state, actor/viewer and clock facts, external provider data, fallback-definition state and loaded implementation generations. A world snapshot alone is insufficient. Test geometry, relation, membership, row-content and viewer-input perturbations. Identical declared inputs must give identical scenes, actions and dependency records before incremental caching is attempted. Keep this scene invalidation separate from the narrower fence on an action, so unrelated edits do not block a person.
2. **Repair the growth instrument.** Count active `lens_ir` plus parse/check, text and paint emission, browser primitives, providers and continuity. Keep the retained old evaluator as reference-maintenance cost. Report surface sugar, semantic operators, data sources and paint/input primitives in different cohorts.
3. **Make one sketch navigable and one computed.** In disposable sessions, test two viewers opening different Studio or Inbox subjects while one holds a draft; test a ledger total that changes when an amount changes and when a new category appears. Require matching agent text, pixels, native targets and no navigation event in the shared world.
4. **Test actual reuse.** Build three independently chosen applications with a frozen primitive set and parameterized library parts. Record every host edit, including a new provider disguised as “generic.” Include one case that genuinely needs a new primitive, so the boundary can be argued rather than assumed.
5. **Test collaboration separately.** Use stable document anchors for two independent edits and one deliberate collision, including insertion/reordering and an omitted paragraph in a preview. Require complete assembled reading, attributable recovery and no silent replacement.

This sequence does not assume the 150-line painter cap or a permanent ban on `if`, arithmetic or nesting. It makes the proposed shared compiler earn its value against the applications that exposed the pressure.

## Team cross-review and what would change our minds

- Awareness challenged applying one lines-per-word ceiling to a new editor or graphic primitive: the branch shows platform cost followed by limited reuse, not a smooth per-word cost curve.
- Communication initially proposed a richer provider registry, then narrowed the recommendation after Awareness's fixed-accessor counterexample: first make the current read boundary enforceable; a registry without that would move the hole.
- Editing stressed that parameterized libraries could reduce host work, while viewer state and paragraph anchors still need their own system contracts.

We would weaken the “Lens-first applications” thesis if the next unlike applications each require bespoke host readers or renderer branches, if agents cannot recover the selected object and exact action from the text scene, or if attractive controls keep hiding the actual edit scope. We would strengthen it if application assembly increasingly changes only Lens/library definitions and native objects while text and pixel views remain equivalent about values, identity, omitted content and effects.

## Primary evidence

- Main: `research/text-desk-lab/notation/scene.py`, `lens_ir.py`, and `research/object-facet-frontier/PROPOSITION-lens-language.md` (proposal; decisions remain Alex's).
- Main: `research/object-facet-frontier/experiments/growth/measure.py` and `experiments/soundness/soundness.py` (the measurement and its scope).
- Experimental branch: `research/visual-bridge-lab/awareness/{studio-bridge,ledger-bridge,spatial-bridge}.lens`, `communication/inbox-bridge.lens`, `BRIDGE-NOTES.md`, `shared-views-observation.json`, and `editing/README.md`.
- Branch source diff: `git diff --ignore-space-at-eol 008eeb8..112a182 -- research/text-desk-lab/notation`.
