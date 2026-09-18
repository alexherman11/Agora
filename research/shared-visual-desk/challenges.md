# Coordinator challenges and comparison protocol

Status: proposed evaluation, not results. The researchers should contest this protocol where it biases the architecture.

## What would be a substantive advance?

An application toolkit with good APIs can already expose rich pixels to a person and structured operations to an agent. That is a necessary baseline. A novel text-and-screen medium must demonstrate a useful improvement over it: lower authoring duplication, cross-representation editing, runtime recombination, simpler extension, or materially better joint work. Merely wrapping four prepared applications in the same command envelope is weak evidence.

Conversely, requiring all applications to use one semantic tree can make the demo look elegant by excluding difficult material. Rich text can have ranges crossing the block hierarchy; an image has continuous coordinates and overlapping layers; a video has several clocks; a code buffer is often invalid as a program. We should count awkward exceptions rather than hide them.

## Four comparisons

| Candidate family | Its best credible argument | What could defeat it |
|---|---|---|
| Conventional component toolkit plus authored text adapters | Mature specialist engines, straightforward integration, easy access to existing software | Maintaining two separate interaction models repeatedly causes divergence |
| Declarative retained model with generated representations and instruments | One authored relationship generates several interfaces and exposes dependencies | Novel behavior needs privileged core patches or large opaque escapes |
| Live object environment with inspectable and editable behaviors | New tools can emerge while work continues; concrete objects can be directly explored | Interface mutation damages work continuity, creates untraceable behavior or overwhelms text inspection |
| Relational or constraint medium with multiple projections | No privileged tree; independently authored capabilities can compose around shared facts | Inference, conflict resolution and update scope become impossible to understand locally |

A hybrid may prove useful. It should name which boundary it chooses and why, not claim every family's advantages without their costs.

## One workspace, not four disconnected demonstrations

Use a report containing an embedded image and a time-coded video excerpt. A code editor exposes the script that transforms the image. The layered image is simultaneously open in a canvas. Two people or a person and agent have different viewports and active tools.

1. In the document, drag the image edge to change the embedded frame. The source image dimensions stay unchanged.
2. Activate crop-source and make a second edit. The source changes, with consequences visible in each embedding.
3. Change the shared image-frame rule. Identify affected and unaffected occurrences without listing the whole implementation.
4. Reflow the report while another participant edits a stable text range. A geometry-dependent stale drag can fail while a still-valid identity-based edit proceeds.
5. Undo the frame-rule change after independent paragraph text was edited. Preserve the paragraph edit.
6. Keep video playing while annotating a captured presented frame. Distinguish the frame receipt from an estimated current playback position.
7. Edit a code buffer into an invalid intermediate state. Keep the text and reading position; label old diagnostics against their buffer revision.
8. Edit the brush or renderer while a stroke is in progress. Preserve the accepted interpretation, defer incompatible replacement or explicitly cancel/migrate the gesture.

The specific operations above are test intentions, not prescribed API spellings or universal ownership rules.

## Observation should support action

A text projection should answer what the participant can productively do next. Measuring honesty only by the quantity of caveats rewards unusable output. Conversely, a short answer that omits stale, speculative or hidden state can be dangerously misleading.

Measure routine operation volume separately from presentation-authoring volume. A useful routine report might give selected material, active instrument, a few relevant actions and state changes. On request, follow a visual part to its controlling definition, provenance and editable scope. Track whether those relations come from one authoring fact or independently maintained adapters.

For continuously changing media, compare bounded transport summaries and meaningful discontinuity notices against frame-by-frame deltas. Exact observations should be obtainable when the task calls for them; do not pretend a predicted clock is exact visual evidence.

## Extension test

Only after a candidate core and four domain adapters are frozen, ask an independent author to add a new domain chosen then. A previously announced spectrogram or diagram is a rehearsal, not a blind holdout. Count:

- Core changes and private knowledge required.
- Separate visual and textual definitions for each operation.
- New kinds of address, selection, observation or ongoing activity.
- Missing inspectable state or visually possible operations.
- Authoring time and failures, with baselines using comparable specialist libraries.

Do not forbid core revisions in research. If needed, record them as evidence against the original generality claim and revise the hypothesis.

## Root's additional literature observation

Toby Schachman's [2018 Dynamicland research note](https://dynamicland.org/2018/Social_Dynamics_of_Programming_Together/) describes independently authored pieces combined through claims and spatial referencing. The full short text was read. It supports investigating recombination and shared attention, not claiming arbitrary compatibility or proving usefulness for text-only agents.

Inference for this desk: a useful extension test should include spontaneous reuse of another person's work, not only implementing a preassigned interface. It must expose the meaning and origin of the coupling. A spatially inferred relation should remain distinguishable from an explicitly authored association.

The GNU Emacs manual's [text-properties section](https://www.gnu.org/software/emacs/manual/html_node/elisp/Text-Properties.html) and [display-property section](https://www.gnu.org/s/emacs/manual/html_node/elisp/Display-Property.html) were available through indexed primary-source passages; direct full-page fetches timed out. They describe structured properties on text and rich display specifications. This is a reminder that textual substrate and rich appearance have longstanding precedents; it does not establish this project's collaboration or extensibility claims.

## Research evidence boundaries

A deterministic Python state model can test its edit and observation rules. It cannot establish low latency, pixel fidelity, usable focus behavior, stable font measurement, actual media playback or new-user discoverability. Those need a later real renderer, realistic interaction, and independent extension work. Keep these categories separate in the final synthesis.

## Revision after media peer review

The media researcher challenged an overly strong equivalence interpretation. When the same explicit semantic input is supplied through a graphical adapter and a text adapter, compare the accepted operation and state under the operation's declared semantics. When a person and an agent independently perform a continuous activity, compare the intended postcondition, declared tolerances and retained evidence; do not require identical pointer samples or timing. Exact replay is a separate promise.

A second peer issue concerns dependency meaning. Inputs validated at acceptance do not automatically establish lasting causal dependence for undo. Declaring every read as an undo blocker is too broad; silently omitting consequential dependencies is too weak. Candidate designs must expose their chosen policy and test a caption or sampled stroke whose accepted result depended on earlier state.
