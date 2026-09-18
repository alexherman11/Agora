# Alternative foundations for a shared visual and textual desk

Research: 18 September 2026. Status: comparative design research, not a runtime contract. Author: foundations researcher, with critiques from editing, media, and coordinator peers.

## Position after the first reading round

The strongest common requirement is not a universal scene tree or a fixed separation between content and presentation. It is a recoverable correspondence between what somebody is attending to, which changes they can make there, and the subjects and definitions those changes affect. A theme is content when designing a theme; image pixels are content when painting; a code result can become an input to the next computation. Categories such as material, presentation, and instrument are useful roles in an activity, but premature as exclusive classes of things.

The original text desk demonstrates a working notation over its particular state model according to the supplied handoff. This research did not rerun its trials, open its home, or inspect private sessions. A text reconstruction format, a compact textual working view, and sufficient understanding to judge an image are three different claims. The first does not imply the third.

At least four foundations deserve competent prototypes. The live-object and relational alternatives should survive as actual competitors, not decorative ancestors of a preselected document architecture. A hybrid is not automatically better: it can inherit every abstraction boundary and every failure mode.

## Reading coverage and source findings

I read the local AGENTS.md, Start Here, Constitution, Design Commitments, Agora Spec, Implementation Status, Presentation and Operators, supplied handoff, and initial literature note. These establish project commitments and dated evidence; they are not proof of the proposed foundation. Memory was used only to locate earlier placement and presentation distinctions, then checked against current local documents.

External reading below goes beyond source abstracts. All interpretations and proposed mechanisms in later sections are this researcher's design reasoning, not claims made by these sources.

1. **Boxer: A Reconstructible Computational Medium**, diSessa and Abelson, 1986. Read all ten pages of extracted text, including figure captions; figures were not separately image-inspected. The paper treats text, programs, graphics, and tools as a medium people can modify in small pieces. Graphics have an alternate editable data representation. Containment gives scope, but the authors explicitly identify its inability to represent sharing and introduce ports. Ports provide linked views, including simultaneous graphics/data views. High-quality moving pictures and sound are future aspirations here, not demonstrated coverage. Important corrective: the paper explicitly subordinates formal uniformity to usefulness and expressive variety. [Primary paper, project archive](https://boxer-project.github.io/boxer-literature/papers/Boxer,%20A%20Reconstructible%20Computational%20Medium%20(diSessa%20&%20Abelson,%201986).pdf).

2. **Directness and Liveness in the Morphic User Interface Construction Environment**, Maloney and Smith, 1995. Read all eight pages of extracted text, including captions. Graphical components and layout policies are manipulable components; running behavior and editing coexist. Direct object references preserve control connections through rearrangement; copying must retarget references within the copied composite. Its core sampler disambiguates nested and overlapping components. Intrinsic autonomous behavior is distinguished from externally applied animation. Polling observations avoid coupling computation speed to display speed. The authors explicitly acknowledge ambiguity between a morph and the outliner for its implementing object. This is substantive precedent, not just a claim that everything is live. [Paper](https://worrydream.com/refs/Maloney_1995_-_Directness_and_Liveness_in_Morphic.pdf), [official bibliography](https://bibliography.selflanguage.org/directness.html).

3. **CLIM User Guide, sections 8.1 and 8.2**. Read both full sections, including nested contexts/presentations. A displayed value becomes useful input through translators whose applicability depends on its type, current input context, and gesture. Nested contexts and overlapping presentations require an explicit resolution policy. CLIM uses priorities when several translators match; that mechanism is not evidence that the highest-priority interpretation is a user's intended edit. [Conceptual overview](https://www.lispworks.com/documentation/lw80/clim/clim-ch8-1.htm), [applicability](https://www.lispworks.com/documentation/lw81/clim/clim-ch8-2.htm).

4. **Incremental Relational Lenses**, Horn, Perera, and Cheney, 2018. Read introduction and section 2's example, integrity constraints, and incremental-update motivation; did not read all proofs or experimental results. The example is particularly important: editing a rating through a selected view changes another row outside that view because of a functional dependency. View laws and dependency constraints can provide coherent updating without implying that the visible subset is the whole effect scope. The section also disallows certain edits that violate the view predicate. Such refusal is mathematical consistency, not necessarily a satisfactory everyday editing interaction. [Primary paper](https://arxiv.org/html/1807.01948).

5. **Using the ThingLab Reproduction**, Alan Borning, current author documentation checked this session. Read the whole page. It distinguishes picture, annotated picture, structure, and values views and describes verbs plus target kinds. It explicitly compares the reproduction with the original. Multiple solvers cover different constraint classes; none subsumes the others cheaply. The documented cursor-control limitation changes an interaction that worked on the Alto. This is valuable evidence that preserving data and declarative relations does not preserve the interaction experience across platforms. The 108-page 1979 thesis was located but not substantively read, so this report does not claim a thesis-level review. [Author documentation](https://homes.cs.washington.edu/~borning/thinglab/directions.html), [thesis link](https://constraints.cs.washington.edu/ui/thinglab-tr.pdf).

6. **ZigZag Commands, version 0.49**, Ted Nelson, 1998. Read the whole command document. The structure can have many dimensions while a window maps a selected few onto viewing axes. Changing the viewing mode does not change structure. Clones share text while participating in other connections. Containment is represented by designated dimensions rather than assumed to be the only organization. The manual labels itself preliminary and documents bugs; it does not establish a polished universal desktop. An additional internals page was located but failed full decoding and was not used for conclusions. [Primary manual](https://www.xanadu.com/zigzag/zzDirex.html).

7. **The Social Dynamics of Programming Together in Dynamicland**, Toby Schachman, 2018. Read the complete short note supplied by the coordinator; images/video were not interaction-tested. The note gives a concrete case of independently authored creations composing by proximity and claims about their roles. This makes spontaneous coupling a serious rival to centrally designed package interfaces. It is a report of examples in one communal setting, not proof of arbitrary interoperability, authorization, or an agent's understanding. [Primary account](https://dynamicland.org/2018/Social_Dynamics_of_Programming_Together/).

No new fictional source was substantively read in this bounded round. The initial note's Egan and Vinge references remain inspiration inherited from that note, not independent evidence here.

## Four serious alternatives

### A. A document calculus with explicit derived views

**Proposal.** The shared desk is an extensible structured document language. Nodes include text, references, media instances, code buffers, controls, and executable components. Definitions transform that structure into visual and textual views. Domain edits target nodes and anchors; presentation edits target definitions or local parameters. Retained assets supplement the text reconstruction package.

This is the most direct successor to the supplied text desk. It makes export, diffs, traversal, selection, and a quiet default outline easy to explain. Google Docs is its natural home. A layered image can be represented as an edit graph embedded within a document node, and a video player can be an executing component with retained media references.

Its serious weakness is the temptation to force every relation into containment. A symbol belongs to several program analyses, an image is embedded in multiple reports, and one comment can refer to a span crossing nested nodes. Adding references fixes representability while undermining the simple-tree mental model. Incomplete code also cannot be reduced to a valid syntax tree unless the language includes explicit incomplete/error forms or retains source text as its own material.

**What would make this win?** The fifth domain can be added through ordinary language extension, while inspection remains short and users can edit the result without routinely encountering node plumbing. It wins only if the conceptual simplicity survives real cross-domain composition.

**What would falsify it?** Every serious domain installs an opaque node with a separate editor and separate textual inspector. Then the common document language has become packaging, and should be judged against simpler packaging.

### B. A live object ecology with textual and graphical inspectors

**Proposal.** The primary medium is a running ecology of objects. Views, controls, tools, recipes, and layout behaviors are objects that can be extracted, rearranged, connected, copied, and inspected. Text is a controllable inspection and command interface to that world, plus a reconstruction notation. No single textual syntax is required to be the complete everyday representation.

This makes changing the environment while using it natural. A control taken from one application can be rebound to another compatible subject; a video player can keep playing while its controls are rearranged. Appearance authoring need not require departure to a separate source-code project.

Its weakness is also its strength: unconstrained object graphs can become difficult to reconstruct, share, and understand. A copy operation must decide which references point inside the copy and which remain shared. Closures, resource handles, transient callbacks, and live process identity are not portable just because the objects have inspectors. A deterministic state export must therefore expose boundaries where reconstruction stops and re-observation begins.

**What would make this win?** An ordinary person and text-only agent can collaboratively modify a running tool, reuse the modification elsewhere, and preserve focus/playback without a source-level rebuild dance. These benefits must outweigh inspecting a graph of incidental implementation objects.

**What would falsify it?** A good interface requires privileged components that resist ordinary disassembly, or the agent must inspect implementation slots for routine user tasks. Then direct manipulability has not yielded a calm shared medium.

### C. A relational world of partial organizations and editable correspondences

**Proposal.** The world does not privilege a document tree. Stable subjects participate in independently authored vocabularies: report order, paint layers, semantic references, temporal intervals, spatial adjacency, discussion, and role membership. A working view selects an organization and exposes editable relations. Definitions state how a view edit changes the underlying organization; constraints maintain declared relations where useful.

For example, one image can participate in report-flow, image-edit, and archival-provenance vocabularies. An application is a chosen work context across these relations. A text desk can be a compact relational view without forcing every tool's internal data into its outline. Novel couplings can start informally and become explicit reusable relations when useful.

The advantage is plural organization without copying the subject. The cost is that global meaning becomes difficult to predict. Two independently authored vocabularies can each be coherent while their composed edits interfere. A shared relation name does not prove equivalent semantics; a shared identifier does not imply shared ownership of every property. Constraints do not remove update ambiguity and can make a small local edit cause distant changes.

**What would make this win?** Two extensions written without coordination can expose a useful new joint activity by adding a small explicit correspondence, without migrating both to a core ontology. Participants can inspect the coupling and predict which other work an edit affects.

**What would falsify it?** The integration burden simply moves into a proliferating set of bespoke bridges, or ordinary users cannot distinguish local edits from changes to shared relations. A graph is not an explanation.

### D. A federation of capable domain engines behind a common desk

**Proposal.** Keep mature domain engines with their own state models and expose shared identity, discovery, inspection, invocation, references, and view-definition controls. The common substrate is an editing protocol, not a universal representation language. Native domains can support stronger contracts; opaque tools explicitly expose weaker ones.

This is a credible baseline. Code editing can preserve buffer and language-server behavior; image editing can preserve specialized GPU pipelines; media playback can preserve decoder and device behavior. Textual authoring of the shell and protocols can still be extensive.

The cost is that application boundaries may survive in every difficult place. Cross-domain undo, embedded editing, and tool reuse may require custom integration. Worse, the agent's inspector can become a second application maintained independently from the visual one.

**What would make this win?** It provides essentially the same shared-desk experience at lower invention and maintenance cost, while honest weaker boundaries are rare enough to be acceptable. A new ontology must demonstrate benefits beyond aesthetic uniformity to beat it.

**What would falsify it?** Basic cross-domain tasks require export/import, loss of identity, or separate routines for human and agent that drift apart.

## The image-edge ambiguity, worked in all four alternatives

An image appears inside a report and is open in a layered canvas. Dragging an edge could change source crop, this report's framing, a shared frame rule, or the observer's zoom. A source-location link alone does not select the right operation.

The unit to settle is an **edit route for a work context**. This is a proposal, not a new global type: a selected part, active tool, declared target scope, interpretation of the gesture, and its current revision dependencies. The context can stay active through many gestures. It should expose a short scope indicator such as “Frame in this report,” with a deliberate way to enter source editing or rule editing. Most gestures need no question because the person has already chosen the work context. A conflict between routes must not be hidden behind a global priority number.

| Alternative | Ordinary frame drag | Enter source edit | Distinct failure risk |
|---|---|---|---|
| Document calculus | Changes embed-node frame | Follow the referenced image and activate its crop operation | Confusing a node occurrence with its referenced subject |
| Live ecology | Frame control targets this occurrence object | Retarget a crop tool to the image object | Copied controls retain unintended old targets |
| Relational world | Changes the report/image occurrence relation | Select image-edit vocabulary and image crop relation | A coupling expands effects beyond visible scope |
| Federation | Calls report engine's embed-resize action | Opens image engine's crop context through a stable reference | Cross-engine handoff loses identity, draft, or preview |

This common explanation does not imply that the four implementations are interchangeable. Their different failure modes should be measured, not abstracted out of the experiment.

## One subject in several independently authored vocabularies

Identity is the meeting point, not a universal schema. Suppose a diagram extension treats a rectangle as a node; a typography extension treats it as a frame; a simulation treats it as a moving body. Each can attach a vocabulary-specific role to the same subject. Their fields should not become aliases merely because all use the word `position`.

There are at least three possible contracts: independent properties; one explicit shared property with units and frame; or a correspondence that converts between properties. These are different choices. Composition must reveal which is in effect. A transform to screen coordinates is not necessarily reversible to a world-space position, particularly with projection, clipping, or layout constraints.

Copying is a good discriminator. A copied diagram should probably copy its internal node-edge relations, retain a shared theme, and create a new playback/simulation activity only if asked. This is not a general deep-copy/shallow-copy question: the desired closure depends on the meaning of each relationship. A viable foundation needs an inspectable copy policy, but should test a small domain-specific policy before inventing a universal graph-copy language.

## A more precise meaning of a quiet text interface

Let `R_t(W)` be a textual working representation of world state `W` for task context `t`. Quietness comes from omitting irrelevant distinctions. If two worlds have the same representation but require different answers to a supported task question, the representation is insufficient for that question. The remedy is a richer observation, a narrower supported task claim, or an honest unknown; it is not claiming that the agent already knows what the person sees.

This is elementary information reasoning, not a new theorem. It nevertheless gives an experimental standard stronger than “the export is text.” A content-rewrite task can omit most style details. A contrast, clipping, or print-layout task cannot. A photograph can have identical metadata and layer structure while its pixels depict entirely different things. Structural inspectability does not establish perceptual knowledge.

One promising design is task-indexed textual observation with an explicit route to request missing evidence. It can initially show the passage and open comments, then reveal framing or typography only when the task requires them. A useful compact view need not enumerate every hidden field; it must expose relevant omissions and avoid implying unsupported certainty. The same principle applies to visual editors: their affordances should not claim an edit will succeed when the required route or resource is unavailable.

## Critiques exchanged and changed positions

**Editing peer:** lens round-trip laws do not choose the intended source update; several update policies can satisfy the laws. Agreed. My initial “addressable provenance” claim was too weak. The candidate invariant now includes selected edit interpretation and its dependencies. I also challenged making a generic compensation protocol a substitute for domain semantics: restoring old numeric values can be wrong after later content or rule edits.

**Media peer:** a predicted brush stroke may be visible yet not accepted material; requested playhead, decoded frame, and presented frame differ. This changes my proposal. Correspondence must carry producer/epoch and evidence status when needed; a bare link from pixels to a source object is insufficient. The same is true of provisional code diagnostics and a previewed layout.

**Coordinator:** the same edge gesture has four plausible meanings, and independently authored vocabularies need attention. The worked table above is the response. The coordinator also supplied Dynamicland as a concrete challenge to assuming all composition must begin from formal APIs. I now distinguish spontaneous coupling from retained declared coupling; both may be useful, but their persistence and observability need different evidence.

**Unresolved disagreement:** how much common mechanism is worth standardizing before proving a fifth domain. My preference is to compare A, B, and C with the same small task and use D as the cost baseline. A union of all four is not yet an architecture. In particular, an invariant phrased so broadly that every application with an API satisfies it contributes little unless its conformance tests expose a real experiential difference.

## Experiments that would change this position

1. **The two-window image.** Implement the four edge-edit routes above. Alternate human and textual actions, including one stale gesture and a shared-rule edit. Measure incorrect target scope, extra choices required, and whether the unaffected context continues working. Do not give the text interface private knowledge absent from ordinary inspection.
2. **Copy a living tool.** Copy an annotated image viewer with a running slideshow, shared theme, local crop preview, and references to two external images. Inspect the copy boundary. The copied tool must identify which references stay shared and must not silently duplicate external execution.
3. **Uncoordinated extension.** Two authors independently add a diagram-frame vocabulary and a simulation-body vocabulary. A third combines them. Count privileged core changes, vocabulary translations, unexplained effects, and what the agent must read before acting. Failure to combine automatically is acceptable; dishonest compatibility is not.
4. **Change the relevant question.** Begin with a document rewrite using a compact text view. Then ask whether a caption is clipped, whether an image is visually distinguishable, and which video frame was actually displayed. Evaluate whether missing evidence becomes explicit and obtainable. No task should pass on metadata alone when it requires perception.
5. **Informal mark becomes a tool.** Start with an unexplained drawn bracket around two items. Later turn it into a repeatable grouping or comparison instrument. Test whether early expression is allowed without schema invention and whether subsequent formalization preserves the original mark and attribution.
6. **Extension rehearsal.** After preparing documents, layers, media, and code, add a time-varying spectrogram with an editable frequency selection and linked playback. This should reveal whether the common foundation supports new relationships or merely hides four custom applications.

No executable model was added by this researcher: the editing peer owns a targeted model of scoped edits and compensation, and duplicating it would add little evidence. No Agora runtime, private world, resident session, deployment, live-model trial, or live media device was touched or initiated. No claim of historical priority is made. The novelty worth testing is a low-friction shared practice across representations and independently authored tools, not the renaming of long-established mechanisms.

## Second-pass review: existing Tessera, peers, and protocol bias

After writing the first report I read the current [Tessera language contract](../../tessera-lab/LANGUAGE.md). It is explicitly a standalone experiment, not current Agora runtime. It already supplies contributed property claims, stable addresses, dormant dependencies, pure derivations, actions and reactions evaluated against one pre-action snapshot, candidate constraints, views, styles, gestures and pulses. The relational alternative above is therefore a rival/reuse path for an existing local experiment, not a newly discovered research direction.

What this round adds beyond that language description is an evaluation problem: correspondence from an actually rendered part to the intended edit scope; truthful treatment of speculative/observed output; operation-specific freshness; continuity of an active interaction through definition changes; and support for domain material that does not fit a prepared widget catalog. Tessera's claim composition might help implement these, but its documented composition rules do not by themselves prove them. It may be more informative to extend this existing lab than to create another declarative language.

I reviewed editing/model.py and both peer reports. The editing fixture is a useful bounded test of explicit routes, fine-grained guards and compensation. Two limitations deserve care. First, semantic causal dependence is manually declared; a read fence on a style value does not establish whether a later caption depends on that style for its meaning. Second, compensation is itself an event: allowing undo of a compensation needs a deliberate history/status interpretation. The editing peer acknowledged both: causal dependence is explicitly declared, and full undo/redo is intentionally unmodeled. Neither invalidates the fixture's narrower tested claims. I endorse the report's refusal to treat every read as an irrevocable dependency, which would make normal work almost impossible to undo.

The media report changes the extension criterion. Adding a spectrogram that merely paints and labels axes is insufficient; selected regions must retain meaningful time/frequency coordinates while analysis windows and display transformations change. Conversely, requiring every medium to expose semantically complete content would disqualify ordinary painting before research begins. The target should be a declared and useful set of tasks with an honest boundary. I do not yet know a cheap general conformance test for a renderer's claims about its output.

The coordinator's challenges are strong but favor prepared, structured material. The eight proposed tasks begin with stable objects, usable addresses, and known edit routes. They can demonstrate correspondence reliability without showing whether inventing and sustaining those structures is worthwhile. Add an informal artifact before it has domain semantics; then ask collaborators to reinterpret and reuse it. Add a perceptual judgment for which the existing textual observation is deliberately insufficient. Finally, include a longer ordinary writing/reading session: an architecture can pass eight carefully chosen transformations while being unpleasant to inhabit.

The coordinator correctly distinguishes a genuinely withheld extension from our announced spectrogram example. The spectrogram in this report should therefore be called a rehearsal; choose an independent fifth domain only after freezing the candidates. I accept this correction.

## The next discriminating experiment

For foundational novelty, my most interesting unresolved comparison is **live object ecology versus relational composition**. This is not a recommendation to implement either as production architecture. The document calculus may still be the simplest useful starting point, and federation remains the cost baseline.

Build one small viewer containing a layered image and a playing time-based effect, plus a separate numeric control authored independently. Ask a third participant to reuse the control to adjust the effect, put that viewer inside a report, duplicate it, and make the duplicate use a different effect range while retaining a shared theme. Then change the control's definition during ordinary use.

In the live-object version, the participant manipulates/rebinds concrete controls and copies an object graph according to an explicit reference policy. In the relational version, the participant establishes scoped claims/correspondences and copies a declared relation closure. Neither version may require a global special case for this viewer. Both can use the same mature renderer and media timing code so performance engineering does not dominate the comparison.

Measure: time to a working reuse; number of unrelated concepts exposed; incorrect shared-versus-copied relations; whether a text-only collaborator can predict the change from normal inspection; and whether a person keeps using the effect during control modification. Record all authored correspondence code, including the supposedly reusable plumbing.

My current weak preference for the live-object candidate is experiential: it may make reuse and interface authorship concrete. I would reverse it if explicit relational composition produces equally direct interaction with fewer reference-copy errors and substantially clearer text inspection. I would instead reject the relational candidate for this use if understanding a small reuse requires inspecting a large dependency network or inventing schemas first. If both lose to a competent ordinary component toolkit on reuse, continuity and authoring effort, do not build a new foundation merely to preserve the research vocabulary.
