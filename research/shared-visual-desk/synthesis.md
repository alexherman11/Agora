# First research round: synthesis

18 September 2026. Three Astra High researchers worked in parallel, exchanged findings directly, and revised their proposals after critique. The coordinator supplied cross-domain challenges and independently reran the two frozen executable models. This document records a research direction, not a chosen architecture or installed feature.

## What changed in the idea

The most promising common foundation is an editable relationship between a working representation, the thing it refers to, and the changes someone can make through it. Text can expose that relationship compactly. A graphical instrument can use the same operation. The appearance definition can itself be selected and edited as material.

That sounds close to a well-designed application toolkit because it is. The research question is whether those relationships can become a medium people reuse and transform during ordinary work, at materially lower cost than maintaining separate visual and textual interfaces. None of the current models establishes that advantage.

Three refinements matter:

1. **Content and presentation are roles in a task.** A reading font can be a personal choice; typography in a poster is authored material. A fixed content/style ontology would obscure this. A theme, tool definition or view can itself be the subject of work.
2. **A visible thing does not uniquely determine its edit.** Dragging an image edge can change its source crop, one embedding, a shared rule or local zoom. The active tool and work context should settle ordinary interpretation and keep it stable during a gesture. Provenance can reveal alternatives; it cannot infer intention universally.
3. **What the screen means depends on time and evidence.** A preview can contain predicted points that are never accepted. An estimated playhead cannot prove which frame was submitted for composition, much less what a person physically saw. Observations need relevant origin and freshness, without streaming every frame into the agent's routine view.

These refinements preserve the original ambition: rich shared work with a quiet textual interface and editable appearance. They withdraw the unsupported implication that reconstructing pixels from text/assets guarantees a text-only agent understands everything depicted.

## The competing foundations remain open

| Family | Why keep it in contention | Most revealing failure |
|---|---|---|
| Structured document and derived views | Natural continuation of the text desk; understandable traversal, exports and anchors | Every demanding domain becomes an opaque escape with its own shadow inspector |
| Live object environment | Tools and visual behavior can be inspected, copied and changed during use | Incidental implementation structure overwhelms ordinary work or live changes damage continuity |
| Relational organizations and explicit correspondences | Subjects can participate in independently authored vocabularies without a privileged tree | Bespoke bridges multiply or local edits have unexplained distant consequences |
| Specialist engines behind a shared editing protocol | Strong practical baseline using mature domain capabilities | Boundaries force export/import, identity loss or duplicated human/agent behavior |

A hybrid is an option, not the default conclusion. It must identify which complexity it eliminates and which it merely relocates. The [foundations report](foundations/findings.md) keeps these alternatives distinct and gives primary-source reading coverage.

## One concrete workflow clarifies the ambition

Place an image inside a report while the same image is open in a layered editor. The document frame, source crop, shared framing rule and personal viewport are separately addressable work contexts.

An ordinary textual observation need only identify the selected occurrence, meaningful source, active tool, relevant state and available operations. Asking about appearance expands the framing rule and overrides. Both routes reach the same accepted domain operation, with domain-specific validation and undo.

Now change the toolbar layout during a stroke, revise the paragraph during an image-frame adjustment, and undo a local frame override after someone changes the shared rule. These operations reveal whether the common foundation is useful. They also expose why whole-object revision fences and snapshot undo are too blunt in some cases.

[Editing findings](editing/findings.md) explain explicit correspondences, operation-specific freshness and domain-owned compensation. [Media findings](media/findings.md) add real-time state, prediction, lifecycle continuity, domain pressure cases and observation limits.

## What the collaboration actually did

- Foundations challenged mutually exclusive material/presentation categories. Editing and media adopted contextual roles instead.
- Editing showed that two different backward updates can obey the same lens round-trip laws. Foundations expanded its candidate requirement from source provenance to explicit edit interpretation.
- Media distinguished speculative output, transport estimates and runtime frame evidence. The other proposals incorporated observation origin and time.
- Root found a fresh-rebinding defect in the editing fixture: an up-to-date observation could still write the old hardcoded subject. The owner fixed it and added a regression, along with rejection of negative dependency indices.
- Root challenged a raster-undo example whose chosen pigments accidentally made snapshot restore numerically correct. Media changed the fixture so both snapshot restore and naive delta subtraction visibly fail.
- Media challenged byte-identical parity for independently performed continuous gestures. The protocol now separates deterministic parity for identical semantic input from intent/postcondition comparison with declared tolerance.
- Foundations challenged prepared-task bias. The next experiment also needs informal marks, missing perceptual evidence and the cost of prolonged use, not only formally typed objects.

The group still disagrees about how much common structure to standardize before building a real cross-domain slice. It also leaves open how much inspection can be generated, how expensive truthful correspondence testing will be, and whether live/relational reuse beats a competent toolkit.

## Verified evidence

The coordinator independently executed:

- `python -B research/shared-visual-desk/editing/model.py`: **14 tests passed**, frozen SHA256 `5995CAC7DBBF71F5BF248359DC9532D0C92DCC6074538B7C4744748E35EF0400`.
- `python -B research/shared-visual-desk/media/counterexamples.py`: **7 tests passed**, frozen SHA256 `6C2FFE98E58B0E7359206D88CE03564E348967DD5A4BA1211A43652370A0615D`.

These 21 tests establish limited algebraic and serialized-state properties under explicit assumptions. They do not demonstrate four working applications, distributed editing, rendering fidelity, low latency, usable controls, authentic authorization, actual media playback or agent discoverability. The research models do not replace Agora's authenticated gateway or event journal.

The editing model requires an explicit lasting-dependency declaration separate from read validation. It cannot infer whether a caption's meaning depends on an earlier width. Conservative cell-epoch compensation also rejects some potentially commutative edits. The media fixture demonstrates counterexamples; it does not solve a media pipeline or destructive-brush concurrency.

## The next experiment worth doing

Build three bounded versions of the two-window image workflow: a live-object version, a relational-composition version, and a conventional component implementation with carefully authored adapters. Use comparable rendering libraries and give the baseline genuine engineering care. This is a proposed next phase, not completed work.

Exercise source crop, embedded framing, shared-rule edit and personal zoom; then make one instrument reusable in a second view. Change a domain operation after both visual and textual interfaces consume it. Measure wrong-target edits, mappings that need repair, extra scope choices, inspection volume and continuity during real input.

Include a rough informal annotation that later becomes a tool, and a task that needs visual evidence absent from the initial text view. Test held pointer input, active text composition and compatible/incompatible definition replacement in a real renderer. Do not conclude from schema compatibility that focus and capture survive.

Once one candidate and four domain adapters are frozen, choose an unannounced fifth domain with an independent author. The already-discussed spectrogram is a rehearsal and cannot count as a blind holdout. Record all core changes and integration work. Core revisions are valid research progress, but evidence against the earlier generality claim.

The fuller [comparison protocol](challenges.md) specifies the combined workflow and evaluation distinctions. Historical sources are linked with explicit reading coverage in the three reports and [initial literature map](references/initial-literature.md). Science-fiction ideas remain inspiration inherited from the earlier map; this round did not newly validate them as engineering evidence.
