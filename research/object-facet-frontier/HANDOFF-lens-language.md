# Handoff: the lens language, and how we know we are on the right side

From the "Position.docx lesson" session (Claude) to the frontier coordinator, 24 September 2026. Alex read POSITION v2 as a lesson (artifact: https://claude.ai/artifact/UVhT2LedkL7mrD6TGncYNV) and reacted. This file records his reactions, one correction, the analysis that followed, and his request for the next round. Alex's words are marked as his; everything else is my reading and is open to challenge.

## Alex's reactions (his directions)

1. **Compiler growth is fine.** Treat `scene.py` as what it is, a compiler for a new language. Real compilers are far longer than 792 lines. Do not cap it; make sure it does not grow *linearly* per word.
2. **The painter should also be able to grow** to accommodate more complex geometries. Same rule: no cap, no linear growth.
3. **The "fifth interpretation not about dates" tripwire seemed dumb** to him. (My explanation: it was a proxy for "does every new domain bring its own words?", i.e. linear growth; the questionable decision sat one level up, in refusing arithmetic.)
4. **He likes Pike's line in the sand** (no evaluator until a task needs an `if` inside a derivation or more than five chained steps), but asks **why we are so against `if`**, which seems useful, and wants the case against **nesting** made properly.
5. He wanted the **expression-language design** explained with examples.
6. He did not follow POSITION's paragraph on the write path ("declare what you read, not emit keystrokes"); I re-explained it with an example.
7. Then the key question: **are we on our way to a worse JavaScript even without a scripting language? What in the design prevents it? What are the advantages of lenses?**
8. His request now: the team should work out **reasonable ways of knowing we are on the right side**, and bring back **ideas for how to build out the lens language and its structure**. He wants the same agents (Sable, Pike, Juniper) with their previous context.

## A correction to POSITION and SYNTHESIS

POSITION 8.1 and SYNTHESIS (round 3/4) say the bounded pure evaluator was "Astra's and Wren's bet". It was Astra's alone: the Codex team's `research/shared-visual-desk/foundations/program.mjs`, spec in `foundations/PROGRAM.md`, argued in `round5-bridge/README.md`. Wren argued the opposite in `text-desk-lab/notation/design-studio/wren-11-one-language-two-files.md` ("REFUSE — an expression language … No expression language, ever."). Wren is also the origin of the "no if, no arithmetic" growth rule and of the painter's 150-line budget. The lesson artifact repeats the misattribution and has not been fixed yet.

What Astra's evaluator is: JSON AST rules (`on` event, `when`, steps `let`/`set`/`if`/`forEach … where`); operators `add sub mul div min max clamp round abs`, comparisons, `and or not`, `if`, `concat`; hard bounds (8,192 ops, 512 iterations, 32 rules, no recursion); writes are proposals that all read one input state, equal writes coalesce, unequal writes to one address refuse the whole proposal (no last-rule-wins); preview, apply, undo receipt; missing paths refuse. Round 5 showed it could express an authored spacing formula that re-placed present and future objects, which the lens grammar could not. Never integrated into scenes; authored as raw JSON; whole-state fingerprint guard over-blocks.

## My analysis of "worse JavaScript" (a starting point, not a finding)

**Drift on the language side.** The lens already has the skeleton of a programming language, each feature crippled and specified only by its implementation: variables (`as`, `$x.f`), loops (`each`, `over`), conditionals (`only when`), calls (`derive … = day-n …`), composition (`lens X of thing`), event handlers (`on click do …`). The bugs so far are the classic bugs of an informally specified language, about names, scopes and meaning: the prop named `n` colliding with a Python keyword argument in `scene.py` and losing four accepted writes; `create … y=2025` silently not stored; `only when $wd=Mon` accepted and meaningless; `$item` versus `$it` scope confusion in Pike's own example; "that name is taken" without saying by what. `scene.py` is one `parse()` and one ~180-line `make()` in which each word is a branch; interpretations are hard-coded Python functions. That is the linear growth. When the language is too weak, people compute in data instead (Juniper minted "year" notes; stored `off=45` by hand), which is worse than JavaScript because nothing prints it. And complexity pushed out of lenses lands somewhere undefined: "behavior lives in definitions" and "a rotation proposal is code" do not say in what language. Wren's biggest fear, the native part as a hole in the wall, is the other escape hatch.

**What prevents worse JavaScript is properties, not weakness.** A JavaScript app reads anything, writes anything, keeps hidden state and paints pixels directly. The candidate "right side" properties I proposed to Alex:

1. A lens is pure: world to scene; it cannot write.
2. The only effects are desk commands through the gateway: attributed, fenced on what was read, undoable (Elm's view/update split).
3. Everything prints: one scene, two printers; every value carries its inputs and source.
4. No hidden state: state is world data or printed per-viewer drift.
5. A lens is world data: versioned, forkable, undoable, edited with the same verbs; installing an app is creating a note.
6. Customization without forking: bindings name referents; behavior in versioned definitions, pinned or following.
7. The host does not grow per app: the painter knows no application.
8. Evaluation is bounded and terminates.

Proposed consequences, all for the team to test or reject: replace the growth rules "no if, no arithmetic" with the properties (any feature that keeps them is admissible, `if` and arithmetic included, provided an `if` prints its test, inputs and branch taken); write the language down (grammar plus scope and namespace rules); rebuild the compiler as a staged pipeline (parse, resolve names, check, evaluate, scene) so new capability comes from general mechanisms and lens-written libraries rather than per-word branches; name the behavior language for definitions (Astra's proposal semantics as a template); grow the painter by drawing primitives (path, transform, clip, text run, image) composed freely, never by shape or app; use Wren's scene-node to painted-element ratio as the health metric for natives. On nesting: its real cost is unnamed intermediates (cannot be printed as `name = f(inputs) = result`, commented, captured or fenced); compilers already lower nested expressions to named steps (three-address code), so the surface could allow nesting while the printer shows lowered steps. Pike's one-operator-per-derive rule is then a printing rule, not a syntax rule.

## The request for the team

Alex wants two things back, as a proposition he can decide on:

1. **Reasonable ways of knowing we are on the right side.** Not a line cap. What properties, measures, tests or tripwires would tell us the lens language is staying a lens and not becoming a worse JavaScript, and that the compiler and painter are growing sublinearly? Each should be checkable, ideally executable in the desk, with what would count as failing it. Challenge my eight properties: which are wrong, redundant, missing, or unenforceable?
2. **How to build out the language and its structure.** The core mechanisms, what becomes library written in lens, the scope and namespace model, where `if`, arithmetic and nesting fit, the behavior language for definitions and gestures (one language or two), the painter's primitive set, the compiler's stages, and the build order. Juniper's household-budget task (bills split three ways, a housemate leaving mid-month, rent rising on the 1st) remains the proposed deciding test for quantities and valid time.

Suggested seats, if useful: Sable on the properties as a formal statement and their tie to the kernel (definitions' behavior language, effects as proposals, valid time); Pike on compiler and painter architecture for sublinear growth, lowering and printing, gestures; Juniper on adversarial tests of the properties (lenses that obey every property and still become unreadable; things the properties wrongly forbid), an audit of current violations in the prototype, and the household budget.
