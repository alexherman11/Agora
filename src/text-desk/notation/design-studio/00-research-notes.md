# Research notes: a shared world with textual and visual working representations

Research pass: September 18, 2026.

Question: Can one editable foundation support document editing, image manipulation, media browsing/playback, and programming, while a text-only agent and a visually operating person both work naturally and can change the interface itself?

Status: literature-grounded exploration. No changes to Agora or its running worlds. The design below is a hypothesis. Existing research establishes particular mechanisms and prototypes, not the feasibility of this complete environment.

## Primary-source reading map

Reading coverage is stated explicitly. These notes do not claim a full reading of every dissertation, paper, or novel. Dates below refer to the works, not search-engine crawl dates.

| Source | Reading coverage | Mechanism relevant here |
|---|---|---|
| Ivan Sutherland, [Sketchpad](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-574.pdf), 1963 | Selected thesis passages on constraints, their representation, and solver limitations | Persistent relationships between geometric variables; reusable instances; constraints with explicit changeable and reference-only variables. |
| Douglas Engelbart, [NLS/AUGMENT viewspecs](https://dougengelbart.org/content/view/218/) | Institute's explanation and linked archival material surfaced in search | Different filters and levels of detail over a document, without changing its contents. |
| [CLIM presentation types](https://www.lispworks.com/documentation/lwu41/climuser/GUID_105.HTM), 1998 manual edition | Manual section on typed input; translator overview | Typed text and selection of an existing presentation can supply the same application object to an input context. |
| John Maloney and Randall Smith, [Directness and Liveness in Morphic](https://bibliography.selflanguage.org/directness.html), 1995 | Official paper abstract; linked full PDF unavailable through the web reader | Running graphical components can be examined and modified directly, while interaction and animation continue. |
| [Lively Kernel technical overview](https://www.lively-kernel.org/development/media/LivelyKernel-TechnicalOverview.pdf) | Indexed primary-source overview, not full paper | A browser-hosted, self-supporting environment joins application use and development. Secondary lead; not needed for the core argument. |
| Bederson and colleagues, [Pad++ description](https://www.cs.umd.edu/projects/hcil/pad%2B%2B/papers/jvlc-96-pad/zoom-4.html), 1996 | Primary project/paper description | Semantic zoom and lenses change representations with scale and task, rather than only magnifying identical graphics. |
| Michel Beaudouin-Lafon, [Instrumental Interaction](https://www.lri.fr/~mbl/papers/CHI2000/), 2000 | Author's abstract; full PDF unavailable through the web reader | Interaction instruments mediate work on domain objects; useful for separating reusable tools from particular application shells. |
| Foster et al., [Combinators for Bi-Directional Tree Transformations](https://www.cis.upenn.edu/~bcpierce/papers/newlenses-full.pdf), 2004 technical report | Introduction, round-trip laws, selected discussion of copying and generated outlines | View updates need an explicit backward interpretation. Certain apparently natural editing behaviors exceed the strict lens laws used here. |
| Hempel, Lubin, and Chugh, [Output-Directed SVG Programming](https://arxiv.org/html/1907.10699v1), 2019 preprint | Introduction, worked examples, provenance mechanism, conclusions and limits | Output manipulation can transform programs. Value provenance connects a selected graphical result to candidate source expressions. |
| Conal Elliott and Paul Hudak, [Functional Reactive Animation](https://conal.net/papers/icfp97/), 1997 | Authors' abstract | Distinguishes time-varying behaviors from events; provides a compositional way to describe interactive animation. |
| [Webstrates](https://webstrates.net/), introduced 2015 | Official overview and indexed original-paper passages; original PDF fetch failed | Shared computational media combine content, computation, and interaction; DOM edits can persist and synchronize across users. |
| Borowski et al., [Varv](https://vis.csail.mit.edu/pubs/varv.pdf), 2022 | Introduction, concepts and modality separation, composition discussion, limitations | Interactive software as concepts with schemas, actions, and triggers. The paper leaves performance/expressivity ceilings open and reports no actual-user usability evaluation. |
| Green and Blackwell, [Cognitive Dimensions tutorial](https://www.cl.cam.ac.uk/~afb21/CognitiveDimensions/CDtutorial.pdf), 1998 | Selected sections on viscosity, hidden dependencies, premature commitment, secondary notation | Describes tradeoffs in changing and understanding representations. Spatial and typographic annotations can carry useful information outside formal semantics. |
| Kirsh and Maglio, [On Distinguishing Epistemic from Pragmatic Action](https://doi.org/10.1207/S15516709COG1804_1), 1994 | Published abstract | Some actions improve the actor's understanding rather than directly advance the final artifact. Tetris evidence does not establish general interface superiority. |
| Greg Egan, [Diaspora: Orphanogenesis](https://www.gregegan.net/DIASPORA/01/Orphanogenesis.html), 1997 | Author-published excerpt, especially perceptual channels, identity, and shared scapes | Fiction separates perceptual form, identity, and participation in shared computational places. Inspiration, not engineering evidence. |
| Vernor Vinge, [Rainbows End](https://us.macmillan.com/books/9781250841506/rainbowsend/), 2006 | Publisher excerpt and synopsis | Fiction explores shared and personal digital views layered over a common place. Inspiration, not implementation evidence. |

Further leads located but not substantively read: diSessa and Abelson's Boxer paper; Borning's ThingLab thesis; Garnet papers; the Webstrates retrospective *Between Principle and Pragmatism*. Do not attribute detailed conclusions to these unread works.

## What this changes in the proposal

### 1. The persistent world is richer than any one notation

Treat textual export, textual working views, graphical appearances, and executable media as distinct concerns. A bounded working outline cannot also be the complete archive. An image reference does not describe every pixel's significance. The reconstruction package may require retained assets, component versions, and explicit session state.

Text remains an effective way to name, inspect, author, and transform world structure. It need not become the native storage format for every image, audio sample, or video frame.

### 2. A presentation should retain a path back to the relevant work

A displayed heading, layer handle, timeline marker, or diagnostic should identify its subject and applicable operations. Meaningful parts can also identify the presentation definition and parameters responsible for them.

There are at least four possible targets of an edit:

- The underlying content or media.
- This appearance's local settings.
- A shared presentation definition or reusable rule.
- The participant's temporary viewing or tool state.

The same motion can plausibly target several of these. An active instrument and edit scope should settle the ordinary case; an explicit choice can settle genuinely ambiguous cases. Inferring arbitrary source changes from output should remain a specialized capability with previews, not a universal promise.

### 3. Reusable tools need precise domain contracts

The common shell can supply selection, inspection, invocation, previews, history, and discovery. Domain components supply the meaning of such operations as crop, trim, rename-symbol, or annotate-range.

Some instruments can work across domains through a declared shared interface. Others should remain specialized. A shared command name alone does not make two operations equivalent.

### 4. Continuous behavior belongs in the model

The world must accommodate durable material, ongoing activity, and short-lived interaction. A playing video, live diagnostic stream, or brush preview should execute at local interaction speed. It should not require an agent turn or a durable global transaction per rendered frame.

Recording the accepted result of a brush stroke is different from retaining every transient preview. Observing playback state is different from replaying the external act of starting playback.

### 5. Informal expression must survive

Do not require every visual mark, grouping, or proximity to declare a domain meaning before it is allowed to exist. A person can place two images together because they seem related, without knowing the relationship yet.

The system can record the actual arrangement and its authorship. A textual observer can report proximity. It should distinguish that observation from an inferred interpretation such as “these images form an approved category.”

### 6. Representation is part of thinking

Comparing side by side, temporarily isolating a layer, slowing playback, enlarging a passage, and trying a new arrangement can help discover what the user wants. The environment should make these experiments cheap and recoverable.

This also applies to an agent: it can request an alternate textual projection, dependency view, or bounded comparison to make a problem easier to reason about. That analytical projection should remain distinguishable from the person's current screen.

## Candidate shared contract

The following is conceptual, not an API proposal:

1. **Material:** stable subjects, domain structure, retained assets, references, and revisions.
2. **Presentation:** a composable way to expose some material, with stable meaningful parts and retained configuration.
3. **Instrument:** an interaction with declared targets, parameters, preview behavior, and accepted operations.
4. **Observation:** what a particular rendered instance currently exposes, with viewport, time, version, omissions, and measurement limits.
5. **Definition:** editable source or structured definitions for presentations, instruments, and domain components.

Declarative structure is attractive for ordinary bindings, styles, layout, composition, and tool discovery. Executable components are needed for unfamiliar rendering, media processing, and behavior. Whether these coexist through a small embedded language, live objects, or ordinary packages remains open.

An extension should not automatically receive a claim of complete textual accessibility. Its declared inspectable parts and operations need comparison with actual behavior. An opaque external video or arbitrary painted region may retain a clear boundary where structural inspection is insufficient.

## The research hypothesis worth testing

Can a component's declared meanings and edit operations generate useful graphical affordances and a compact textual working interface, while preserving local execution speed and allowing new components to be invented during use?

The potential contribution is the cost and reliability of this combined experience for a person and an agent. Live objects, declarative applications, typed presentations, semantic zoom, and bidirectional editing each already have substantial histories. This research pass does not establish historical priority for the combination.

## Experiments that could disprove it

Use four small but genuinely different domains. These are slices, not attempts to reproduce complete commercial products.

| Slice | Required difficult behavior | Failure signal |
|---|---|---|
| Document | Anchored discussion survives edits and reflow | Text and screen refer to different passages; appearance changes invalidate content edits unnecessarily |
| Layered image | Mask, blend, transform, and a live stroke preview | Only raster output is exposed; editing falls back to source-code surgery or screenshot guessing |
| Media | Playback continues while notes and timestamp annotations are edited | The event model stalls playback, confuses observed time with durable content, or replays effects |
| Code | Incomplete buffer, symbol navigation, diagnostics, and running output | The model assumes every edit is valid syntax or every process result is instantaneous |

Then add a fifth, initially absent capability such as a spectrogram or an animated diagram. Measure what must change in the shared foundation. A design that handles four prepared demos but cannot add the fifth without privileged core changes has failed its extensibility claim.

Cross-domain tests:

- The same subject appears in several views; edits retain correct identity and update scope.
- A person and an agent perform the same domain change through their respective interfaces and obtain equivalent accepted state.
- A gesture affecting derived layout changes the intended rule or override, with the choice inspectable.
- A new component exposes truthful bounded text inspection without a separately maintained shadow application.
- A personal view changes while another person's selection and reading position remain stable.
- Opaque, hidden, stale, or unmeasured content is declared accurately.
- The user can make an informal mark or arrangement without first inventing a schema.
- Undo of a presentation change preserves later independent content work.
- Style and behavior changes preserve focus, drafts, playback, and active tools where the change is compatible.

Measure domain task success, source edits needed during routine use, agent inspection volume, time to first useful interaction, pointer/typing latency, conflict recovery, and the effort required to add the fifth domain. Compare against competent conventional implementations, not a deliberately weak baseline.

## Open decisions

- How much of a component's textual interface can be derived, and how much must be deliberately authored?
- Which edit relationships are exact, which normalize input, and which require explicit domain actions?
- How are shared rules and local exceptions explained without making ordinary inspection verbose?
- What is the smallest set of common contracts that still accommodates continuous media and opaque resources?
- How does an extension remain understandable after several independent people have modified it?
- Can a useful text-only agent operate an unfamiliar tool from discovery and inspection alone, without reading its implementation?
- What level of perceptual understanding can be supplied honestly for images, arbitrary diagrams, and video?

The next architectural choice should be earned by these experiments. A new syntax alone will not resolve them.
