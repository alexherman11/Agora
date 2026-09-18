# Rich media pressure tests for a shared visual desk

Status: independent research findings, September 18, 2026. These are hypotheses and counterexamples, not implemented Agora capabilities. The only executable artifact here is a seven-case, standard-library counterexample fixture. No running world, model session, browser, Photoshop installation, or media pipeline was exercised.

## Main result

A useful common foundation can provide identity, revisioned definitions, discovery, bounded observation, editable routes, and continuity. It cannot replace domain semantics with a universal scene tree or a list of rectangles. The difficult common property is that a person and an agent can identify what their action refers to and what interpretation will be applied, while the person continues to interact at local speed.

The material/presentation/instrument/observation/definition proposal is a useful set of questions, but should not become five mutually exclusive kinds. A Photoshop blend mode belongs to the authored image, a reader's contrast mode belongs to a view, and an animation easing function may be either. Scope and intended consequence determine the distinction. The same datum can participate in several roles.

The stronger claim that whatever the person sees can be known by a text-only agent has two different meanings. Complete retained assets and execution definitions may permit reconstruction. Bounded text inspection does not thereby communicate every perceptual distinction or its meaning. Even listing all pixels does not supply automatic visual understanding. This is a limit to articulate and design around, not a reason to settle for a text-only product.

## Primary sources actually inspected

| Source | Coverage in this round | Direct finding and limit |
|---|---|---|
| [W3C Pointer Events Level 3](https://www.w3.org/TR/pointerevents3/) | Introduction; interface; coalesced/predicted-event sections; pointer-capture and layout-change sections located, not fully analyzed | Applications can draw predictions ahead of actual input and discard them when new input arrives. Device input includes pressure/tilt. This specifies input behavior, not semantic editing or collaborative undo. |
| [Video frame callbacks draft](https://wicg.github.io/video-rvfc/) | Introduction, complete metadata definitions and callback timing procedures | Frame callbacks concern presentation for composition, with timing metadata. This is not proof of physical pixels on a monitor or of human perception. It is a community draft, not a W3C standard. |
| [Web Animations](https://www.w3.org/TR/web-animations-1/#timing-model) | Timing overview, stateless/hierarchical sections and caveats | A timing function can derive progress from time independently of frame rate; pause/finish and timing edits introduce state. This does not solve arbitrary simulation or network playback. |
| [OpenTimelineIO Time Ranges](https://opentimelineio.readthedocs.io/en/latest/tutorials/time-ranges.html) | Complete short tutorial | Clip, source, parent and visible ranges differ. Transitions can extend visible source range beyond the ordinary trim. Markers have a reference coordinate frame. |
| [Photoshop UXP modal execution](https://developer.adobe.com/photoshop/uxp/2022/ps-reference/media/executeasmodal) | Complete page | Real Photoshop editing includes exclusive modal scope, cancellation and grouped history, with notification suppression in some scopes. This supports testing contention/cancellation; it does not establish that Agora should copy Photoshop's global exclusivity. |
| [Functional Reactive Animation](https://conal.net/papers/icfp97/) | Author landing-page abstract only | Historical lead for time-varying behavior and events. No implementation conclusions in this note depend on a full-paper reading. |

WebCodecs and the LSP 3.17 landing page were opened but not substantively analyzed. No detailed claims are attributed to them. Morphic and Boxer conclusions below are peer reports from foundations, not my independent source readings. No science-fiction text was read in this round.

Project reading: AGENTS, Start Here, Constitution, Design Commitments, Agora Spec (all sections across multiple reads), Implementation Status, Runtime Guide, Presentation and Operators, supplied handoff and initial literature. These establish existing boundaries and distinguish source from deployed evidence. Runtime Guide and Implementation Status themselves have dated historical sections; this work does not turn those into current live observations.

Memory quick pass found prior placement lessons: application/view ownership; content identity distinct from occurrence; actual input is separate evidence. The registry was used for orientation, then the current project documents were read. No prior live identifiers were targeted.

## Four application demands that break plausible simple foundations

### Documents: reflow is usually irrelevant to the edit target

A comment on a passage should survive toolbar styling, pagination and a second reader's different width. A screen rectangle is the wrong canonical passage identity. Conversely, "move this margin comment away from that diagram" genuinely concerns this presentation's geometry. A semantic anchor and an appearance occurrence are both needed; one is not a replacement for the other.

An inspector should show the passage, anchor resolution, discussion and applicable operations without all CSS. A style inspection should show the responsible definitions, effective values and override scope. Arbitrary low-level layout data is neither always noise nor always necessary.

Hard case: text has been replaced while an input-method composition or local unsaved edit is active. Merely retaining focus ID after remount is insufficient. Compatibility must include the editor's live interaction state. This round did not test an editor, IME or anchor algorithm.

### Photoshop-like work: a stroke is an interaction, an operation and sometimes a computation

A brush preview can contain confirmed samples plus speculative future samples. Therefore "everything visible is accepted world state" is false even in a well-behaved ordinary application. A remote agent should be able to know that a stroke is in progress, on which layer, with which instrument, and whether an attempted action would conflict. It need not consume every preview point unless its task requires them.

A completed stroke may retain points, pressure, selected layer incarnation, brush definition, transform, assets, random seed and sampled material dependencies. That list is an example, not a compulsory wire format. Destructive brushes, clone tools and smudges may depend on the image produced by earlier marks. Preserving operation records alone does not establish that selective undo or concurrent recomputation preserves intention.

A shared object log does not remove the need for tiles, GPU surfaces, dependency invalidation, cancellation or bounded resource use. A renderer that accepts only declarative rectangles has failed this case. An unrestricted canvas with a layer-count summary has also failed meaningful text operation.

### YouTube-like use: a clock is not an observation

A playing media session has a transport state, media source, current activity incarnation, available controls, and observations from its actual pipeline. A formula derived from the last playhead and playback rate estimates progress; it cannot distinguish normal playback from an unobserved stall. The requested seek position can also differ from the frame available to compose.

A compact useful look might say:

```
player interview / session 7 / source recording@r3
playing 1x; transport anchor 82.40s at local clock 120.0
last submitted-for-composition frame report 82.36s, sampled 0.06s ago
selection: source 80.00..86.00s; annotations: 2
controls: pause, seek, set-rate, annotate-range, capture-current-frame
contents: transcript available; visual scene interpretation unavailable
```

These are conceptual fields, not a new syntax proposal. Predictable playback should not flood change deltas. Report seek/pause/stall/end, source replacement, changed control availability, invalidated selection, or thresholds explicitly relevant to the current task. If the request is "annotate this exact frame", obtain a frozen frame receipt from the media runtime, including source/time/session context. An extrapolated playhead must not silently stand in for it.

### VS Code-like work: imperfect material and asynchronous evidence are ordinary

An incomplete buffer is valid work even when it is invalid program syntax. A diagnostic, symbol range or debugger value belongs to an analysis/runtime version, which may lag the buffer. Textual inspection should let the agent edit the buffer directly and request derived views; it must not imply that displayed diagnostics are current just because the file ID is stable.

A terminal or debugger also has an ongoing process lifetime. Restoring its visible transcript does not rerun the process. The shared foundation should admit these ordinary cases without inventing a platform-level code-editor object class. Exact LSP/editor contracts require a later implementation reading and test; this is a pressure case, not evidence of support.

## Hot changes during a gesture

A gesture must not silently switch its interpretation halfway through. Consider a stroke begun with image-to-screen transform A, then a theme update changes the toolbar height and shifts the image to transform B. Reinterpreting the next pointer sample under B changes the authored path, even though the human continued one motion.

Possible policies are to defer relevant layout changes, pin a mapping for the interaction, deliberately rebase it with continuity, or cancel with retained recoverable work. Pinning is not always visually comfortable, so it is not a universal answer. Cosmetic updates can often leave the active instrument and surface resident. An interpreter update that changes pressure handling or coordinate semantics should wait for an interaction boundary unless it supplies a tested migration. Selection, pointer capture, keyboard focus, input composition, playback and resource handles require continuity beyond a JSON schema match.

Deletion/recreation of a layer with the same title must not cause an old stroke to land on the new layer. Similarly, identical media timestamp and frame number in a new session do not identify the old frame. Incarnations and operation dependencies matter.

## Inspection must expose useful behavior, not just enough nouns to claim parity

A native component should declare bounded material inspection, stable targets where they exist, applicable actions, definition provenance and relevant activity state. Its graphical controls and textual operations should reach the same accepted semantics. Observations should distinguish accepted, speculative, derived and measured claims, each with producer and revision/time context where relevant. Unknown perceptual content is an honest boundary; endlessly saying "opaque" is not a successful implementation of the requested native tool.

A practical acceptance test should ask the agent to complete actual domain work through those interfaces, change appearance intentionally, and diagnose a discrepancy. Count missing domain information and source surgery. A layer-count summary that cannot support changing a mask is insufficient. Exposing every shader line is not automatically sufficient either.

The renderer must help expose what it actually laid out and interpreted; application schemas cannot simply testify that the screen agrees. Independent comparison is needed at selected boundaries. No universal textual summarizer can derive all useful semantics from arbitrary executable output.

## The fifth domain should strain assumptions

A spectrogram editor is a useful extension rehearsal, but because it is announced here it cannot be the blind fifth-domain holdout. For the holdout, an independent author chooses a different domain only after the candidate core and prepared adapters are frozen. It needs source samples, time/frequency coordinates, transforms and window parameters, asynchronous analysis, a selectable region, and a domain action such as attenuating a frequency band. A selected rectangle in logarithmic frequency display is not a rectangle in Hertz, and a new analysis window can change the derived bins while the intended time/frequency region survives.

Success: an ordinary authored extension defines the material, analysis, rendering, inspection and action routes; unchanged shared machinery handles discovery, references, observations and continuity. Failure: privileged core code gets a new spectrogram case, or the extension can draw but cannot expose useful editable meaning. This experiment has not been built. It is better than another document-shaped demo, but it still would not prove arbitrary-domain extensibility.

## Executed counterexamples

[counterexamples.py](counterexamples.py) checks seven explicit counterexamples: mid-gesture coordinate change; visible predicted points differing from accepted points; clock extrapolation failing under a stall; frame-number reuse across activity generations; naive raster selective undo; identical structural summaries of different pixels; source-time versus timeline-time anchoring. These are mathematical/toy-state demonstrations. They do not implement a media engine, concurrency protocol, export format, real pointer handling or browser rendering.

The raster undo case is deliberately small: restoring the initial snapshot loses the later pigment, while subtracting a prior pigment delta from the later blend produces an invalid result. Replaying retained later operations is one candidate, but tools that sample earlier pixels require explicit dependency and intention choices. Even equal final pixels do not establish preserved authorship.

## Collaboration and changed views

Foundations proposed addressable edit provenance instead of one semantic scene tree. I agreed but challenged provenance alone: visible predicted output and running media require producer, time and accepted/speculative status. Foundations incorporated this and reported Morphic's distinction between intrinsic behavior and observation. That historical report supports investigation, not a claimed media implementation here.

Editing independently proposed captured transforms, layer incarnation, brush revision and sampled dependencies. I added hot interpreter changes, recreation and actual input continuity. We agree that append-only strokes are insufficient for every destructive or sampling operation.

Root asked what an agent should actually learn, beyond warning labels. That changed the recommendation from merely timestamped observation to task-relevant discontinuities plus on-demand exact snapshots. Normal playback should remain quiet; the agent receives enough control state to act. No agreement yet establishes one universal observation subscription policy, accepted gesture representation or self-modification lifecycle.

Unresolved: how much inspection can be derived rather than separately authored; how to test truthfulness affordably; which resource/lifecycle contracts are common; when an update should pin, defer or migrate; whether text-only assistance is sufficient for particular perceptual tasks. These are experimental questions, not missing syntax features.

### Cross-review and coordinator corrections

Root found the first raster example numerically weak: the second stroke painted zero, so recomputation without the first stroke happened to equal the initial snapshot. I changed the second pigment to 0.2; now the accepted output is 0.35, preserving only the second stroke gives 0.1, snapshot restoration gives 0, and naive delta subtraction gives -0.15. Both naive routes visibly fail. Seven tests pass after this correction.

In editing/model.py, expected read epochs validate inputs at acceptance, while a separate depends list governs future compensating undo. A caption can read a theme width and later lose that assumed width when undo occurs if its author omitted depends. This is not solved by treating every read as a permanent blocker: many valid reads should not forbid later revision. The design needs visible distinctions between read provenance and lasting semantic dependence, and domain policy for the latter. I sent this critique to editing and root; it is not a claim that the toy model implements automatic causal inference.

I challenged a too-strong parity test: independent human and agent brush gestures need not produce identical samples. Root accepted separating deterministic parity for the same supplied semantic input from intent/postcondition equivalence with declared tolerance for continuous interactions. The later browser experiment still needs real held-pointer input and hot compatible/incompatible upgrades; serialized state tests cannot establish those properties.

A further media observation limit from the video-callback draft: submitted-for-composition metadata is not a strict simultaneous capture of what a person physically saw. Callbacks can be late or miss frames. An exact-frame workflow must specify its snapshot boundary and retained pixels/receipt; an API named capture-current-frame alone cannot establish stronger synchronization.

Check command: `python research/shared-visual-desk/media/counterexamples.py` from Agora4. Result on September 18, 2026: 7 tests passed. No third-party dependencies or native-world writes.
