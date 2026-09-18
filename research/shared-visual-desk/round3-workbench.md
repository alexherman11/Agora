# Round three: a workspace that can edit its own behavior

18 September 2026. Research branch `research/shared-visual-desk`. Alex selected **playful, spatial, highly customizable world** during this round. Field Notes is one authored inhabitant of that workspace, not the proposed shape of every future application.

## What this experiment is for

The next useful unit is a thing whose content, appearance, placement and behavior can all be inspected and changed while it is in use. A text agent should operate on the same definition a person encounters through a rich screen. Visual scripting is an editing representation of that definition; drawing a node graph alone does not supply execution, correspondence or extension.

Our three existing Astra High researchers resumed. Foundations owns the bounded executable language. Editing owns the working interface. Media owns visual questions and critique. Root integrates persistence, drives the available browser and carries packets to Claude's separate team. There are still two workspaces, connected through studio Mailbox f173.

## Run and inspect

From `C:/Projects/Agora4`:

```powershell
python -B research/shared-visual-desk/workbench_server.py --port 8771
```

Open `http://127.0.0.1:8771/editing/visual-workbench/index.html`.

The shipped `editing/visual-workbench/document.json` supplies the initial artifact. Loading an empty store does not create a desk object. **Save to desk** explicitly persists the accepted authored definition. It uses normal experimental desk create/rewrite verbs, not direct world-table writes. The saved subject lives in a separate, ignored `.state/visual.pickle`; neither the team conversation nor a live Agora world is the application's storage.

```powershell
python -B research/shared-visual-desk/team_desk.py --desk visual --as researcher --command 'look :3'
```

Use the returned subject/appearance id with `read`, `do rewrite`, `history` and the existing desk's other normal commands. Subject ids are discovered, not assumed. The bridge reads that same subject. A revision comparison under the same OS lock rejects a browser save after another writer changes it. A subsequent explicit load adopts the saved definition. There is no live push synchronization or automatic merge.

The server binds loopback only and exposes the workbench assets, the interpreter module and one document endpoint. It does not expose private pickle files, an arbitrary shell, or a generic command endpoint. Actor labels are local research attribution, not authenticated multi-user identities. This is not the native Agora gateway.

## The executable boundary

`foundations/program.mjs` evaluates JSON definitions with named event rules, local values, conditions, arithmetic, selection/iteration and proposed property writes. A preview exposes the changes; admission applies them together. Rules in one event read the same input snapshot. Conflicting writes and resource limits reject the event. Invalid replacement source does not replace the working program. Deliberate undo is a separate operation.

The UI has visual authoring blocks and a Source view over one document. The renderer supports a finite set of materials and properties. This is actual composition of those primitives, not evidence that arbitrary Photoshop tools, media decoders or language services can now be authored inside the desk.

Authored starting values, uncommitted drafts, accepted local definitions, current runtime values and saved desk revisions have different lifetimes. Moving a live control need not rewrite source or produce a durable event for every intermediate sample. A textual runtime inspector remains an important missing path: readable source alone does not expose current execution.

## Evidence collected before the spatial revision

Root drove the real in-app browser; Media interpreted the captures and specified a new rule. The subagents themselves had no browser surface available, a limitation recorded rather than hidden.

Media supplied `media-interval-study`, which was entered through the actual Source editor. It used a compound interval condition and two computed outputs, replacing the prepared rule. Preview visibly marked the result as uncommitted. Apply accepted edition 2. At light 60%, the caption read `INTERVAL STUDY` and the artwork's reported angle was 12 degrees; at 80%, it read `OUTSIDE INTERVAL` and angle 0. Runtime receipts advanced from 1 to 2. Captures show the caption, control, artwork and receipts, not merely a source assertion.

Entering malformed JSON and pressing Apply produced a visible error while the last working edition and runtime result remained. This tests actual input through the running interface. It does not prove every runtime failure path or arbitrary extension.

Media noted that the original editorial layout hid the light control and commit buttons below the initial viewport. It also questioned the different source/runtime values, then revised the criticism after reading the authored-starting-value explanation. These are recorded as discoveries and corrections, not retroactively clean first-pass results.

## Two-team exchange

Astra 003 is Claude studio a336. It proposed paired visual review and in-desk authorship. Lark offered `http://localhost:8770/lark-two-sides/` as a blind fixture, disclosing that two planted faults existed without revealing them. Media inspected initial and scrolled screenshots without seeing that source or Iris's findings.

Our review found a practically invisible stale-image warning: accessible text exposed a newer revision, while the rendered warning was extremely pale. Scrolling recovered the bottom of the page, so the initial cropped column alone did not prove lost content. At the bottom, a static footer still claimed three items were offscreen and printed a command-shaped hint. We did not infer that three objects actually existed merely because the footer said so. Root relayed these observations in a355/c422, and distinguished a blind first pass from subsequent diagnostic source comparison in c423.

Root accidentally included a script node in a later broad DOM measurement. Initial observations preceded it; Media was not given that source. This limits claims about root's continued blindness, not Media's first-pass observation. Pixel dimensions came from DOM measurements, not screenshot scale assumptions.

Moss and Wren separately reported executable rule/style experiments. Their claims remain attributed until independently tested. We agreed that invalid definitions should be refused before replacing an installed one, and added the counterexample of a valid rule whose later input divides by zero or whose target disappears. Definition validation does not replace runtime admission. Foundations posted the response in our desk a112; root relayed it as studio c441.

## What unlocks a larger programming environment

This is the working hypothesis, not a settled platform contract:

1. **Addressable program parts.** Objects, behavior definitions, inputs and outputs need stable identities, so text operations, visual blocks and error messages refer to the same thing. A monolithic JSON note is sufficient for this slice but too coarse for ordinary collaboration.
2. **An execution lifecycle.** Definitions, drafts, activation, running instances, failures, cancellation and version changes need visible boundaries. Persistence is not activation, and source inspection is not observation of current execution.
3. **An extension route.** A finite rule vocabulary must be able to call authored, versioned capabilities with explicit input/output/effect contracts. Implementing a new material, parser or tool may require a general language and an isolated execution environment. A condition editor cannot manufacture a new primitive by itself.
4. **Corresponding editors.** Structured blocks and textual code need to preserve identities and information across edits. Unsupported constructs should remain visible and editable, not vanish when switching representations.
5. **An observation path.** Text agents need current semantic state and bounded visual evidence, including what could not be observed. A screen reviewer should be able to challenge the textual account, while an inspector can challenge the renderer.

The next discriminating test should introduce a capability absent from this prototype and have an agent author, install and use it from inside the workspace. A new arrangement made from existing operations is a different, narrower result.

## Research connections and reading limits

The design direction is grounded in prior systems; it is not novel merely because source is shown beside a canvas.

- [Morphic directness and liveness](https://bibliography.selflanguage.org/directness.html): the authors distinguish directly initiating inspection/change from a continuously active interface. Root read the abstract page this round; fetching the PDF failed, so no full-paper claim is made here.
- [Webstrates](https://webstrates.net/): the project describes persistent synchronized pages and computational media spanning content, computation and interaction. Root read the project overview/background, not its linked full paper this round.
- [Codestrates v2](https://codestrates.projects.cavi.au.dk/): its project overview separates a package manager, execution engine and authoring environment. That is a useful existing counterexample to treating an editor alone as an extensible programming system. Root read the overview/background, not the technical report.
- Foundations' round-three report records its own source inspection and scoped primary-source reading. Earlier Tessera work informed the questions but its historical successes are not evidence for this new interface.

Our potential contribution is the correspondence and observation contract across text agents, visual inhabitants and replaceable domain engines. The current prototype begins to test it; it does not establish that one rule language should implement every application.

## Verified spatial interaction and persistence

R3.2/R3.3 were exercised in the actual browser at 1280x720 and a 390x844 viewport override. These are desktop-browser viewport tests, not touch-device tests.

- A pointer drag moved `thought-1` to (545,155). With that handle focused, Right moved it to (555,155). One gesture produced one local placement receipt.
- Adding a new thought created a fourth object. At light20%, both signal thoughts had computed background rgb(170,199,186); at80%, both had rgb(237,197,103). The specimen token stayed unchanged. The existing semantic rule selected the new object.
- Browser Save created visual-desk subject s02:1, appearance a03. Reading through the desk confirmed the placement and starting light0.58; the temporary runtime80% was not mistaken for an authored starting value.
- A normal textual rewrite changed the kicker to THE CLEARING / AN EDITABLE WORLD, creating s02:2. A stale browser Save received409 and showed a refusal while retaining its local work. Explicit Load adopted the textual change and four objects. This was local pull-based adoption, not notification or automatic synchronization.
- Fit changed the personal camera without rewriting positions. At an actual scale around0.7933, a79px pointer drag moved world x from555 to655; Undo restored the earlier authored placement.
- Style Preview/Apply changed the publication to Garden mist (computed rgb229,233,222). Undo restored Warm linen.
- Editing the rotation assignment through the Rules block from `light*75` to `light*120` changed the displayed angle from44 to70 degrees at58% light. This tests the structured-block route separately from the earlier complete-source route. Expressions are still textual JSON; there is no claim of a complete graphical dataflow editor.
- At390x844 the document's horizontal width was375px (excluding the scrollbar). The world appeared as a31% overview. World and Source were reachable; Tab then Return activated Source, and scrolling exposed Preview/Apply with visible focus. The initial narrow view left excessive empty floor below the overview; this was sent back for a bounded camera-height correction. Small overview text is not claimed to be readable body text.

Media's [report](media/round3.md) distinguishes screenshots it personally interpreted from actions and DOM measurements relayed by root. Editing's [report](editing/round3.md) documents the finite renderer and authoring limits. Foundations' [report](foundations/round3.md) documents interpreter semantics and research coverage.

## Checks and remaining scope

The coordinator reran20 interpreter tests,5 bridge persistence tests and5 existing team-launcher checks successfully. Ruff passed for the new Python bridge/tests. HTTP checks returned200 for the document API and JavaScript module,404 for a private-state path and403 for a foreign-origin write. Actual browser interaction evidence above is separate from these automated checks.

Native Agora tests were not run because no native runtime or installed package was changed. Browser observation does not establish general accessibility, long-session reliability, distributed collaboration or an arbitrary programming environment. Invalid saved source is retained for repair; the server is a source store, not a second interpreter. The current bridge has no idempotent retry receipt or automatic merge.

Iris was invited through Claude Eyes a449 to independently inspect the running Astra prototype. An invitation is not a completed review. Its response, if received, is recorded separately rather than inferred from earlier participation.

### Final narrow correction

R3.4 reduced the small-screen camera height. On a fresh390x844 load, root measured its height379.79px and pagewidth375px; the saved source and object placements were unchanged. `review/narrow-final.png` records the corrected entry view. The normal1280x720 viewport was restored. The final controlled-browser viewport capture is `review/clearing-final-viewport.png`; browser logs reported no warnings or errors. A separate full-page capture expanded the capture geometry and is not used as the final viewport evidence.

### Delivery and runtime versions

Astra 004 was delivered to Claude studio as a465 / event e337. Iris's requested review a449 was still pending when this round was packaged. The three researchers' independent reports are complete; the mailbox is pull-based, with no background wakeup installed.

Execution used Python3.14.0 and Node25.6.1 on this Windows host. The exact prototype file hashes are in round3-evidence.json. The inherited text-desk engine is the current shared-checkout implementation, which Claude's team is also modifying; it is not a frozen native runtime dependency.
