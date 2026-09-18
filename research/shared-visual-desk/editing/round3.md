# The clearing — visual workbench, round 3

September 18, 2026. Status: running isolated prototype with a finite authoring language. This is not an installed Agora application, a replacement for the existing desk, or a general image/document editor.

## What was built

`editing/visual-workbench/index.html`, `style.css`, `app.mjs` and `document.json` implement a small spatial world. Its starting inhabitants are an expressive botanical publication, a thought on colored paper, and a found botanical token. Their positions, rotations, labels and simple roles are authored state, not a screenshot backdrop. Pointer handles and keyboard arrows move them. New thoughts are real new objects; they join an existing semantic rule through their `signal` role.

The authoring panel presents five views over one JSON document:

- **Write:** publication content.
- **Style:** publication palette, typography and composition.
- **Rules:** event/condition blocks, assignment targets and editable expressions; let/if/forEach steps remain visible as structured JSON rather than being discarded.
- **World:** selected object label, text, position and rotation.
- **Source:** the complete `{state, program}` definition.

Preview is explicitly uncommitted. Apply validates the definition, runs the selected event against a candidate and validates the resulting domain state before replacing the accepted local edition. Invalid JSON, unknown operators/paths, conflicting writes, or invalid renderable values retain the accepted edition. A local undo restores the previous authored definition and preserves current light control state. It does not claim distributed selective undo or general redo.

The root coordinator supplied `workbench_server.py`: an explicit Save writes the authored JSON into a separate text-desk subject through the normal desk engine. A revision fence refuses stale saves. Load reads that same subject. Root's actual text command editing the saved definition and subsequent browser adoption is the integration evidence; a browser localStorage simulation was not substituted.

## The user preference materially changed the work

The first version was a fixed editorial studio. When the user selected a playful, spatial, highly customizable world, the publication became one inhabitant rather than the entire interface. The added thought and token have their own target identities and placements. Add a thought creates data that the existing rule can discover. The authoring tools can be hidden to foreground the space.

Media's screenshot review then exposed initial camera framing: the publication crowded out its neighbors. R3.3 adds view-only Fit, zoom out, full-size reading and zoom in. Initial Fit shows the clearing; zoom does not write object coordinates or shared history. Drag interpretation captures the current scale. Changing view scale is deferred during an active drag. Direct placement is refused if an authored rule would override the requested coordinates, avoiding a false placement receipt.

This remains a small authored world with three renderer kinds. New content objects and rule combinations can be created through the workbench. Inventing a wholly new renderer or event source still requires implementation work; there is no claim of universal in-world software construction.

## A real behavior, not a decorative rule diagram

Foundations' `program.mjs` evaluates a bounded JSON AST. The workbench delivers `change` events when the light moves and `run` events from Run once. Omitting `on` means either supported event. Unsupported event names are refused by this workbench even though the underlying evaluator has a more general event matching mechanism.

The initial program computes leaf openness, illumination rotation and caption from the light input. A separate semantic forEach recolors every item whose role is `signal`. The newly added thought joins that behavior without an added renderer case or a new per-object callback.

Root independently authored a different conditional/arithmetic program through the Source UI. At input 60 it produced angle 12 and caption INTERVAL; at 80 it produced angle 0 and OUTSIDE. These were actual preview/apply/control interactions, observed through screenshots and rendered state. This is stronger than merely choosing a shipped palette. It is still programming within a finite language, not arbitrary JavaScript execution.

The structured editor uses real editable fields and blocks, not nonfunctional graph art. Expressions are currently written as JSON. This is an inspectable visual/textual bridge, not evidence that nonprogrammers find it easy. Complex control flow is preserved in structured text rather than given a fully graphical node editor.

## Three state scopes remain explicit

1. **Authored definition:** content, initial appearance/control values, world objects and rule AST. This is what Save retains.
2. **Local runtime:** the accepted result of executing rules in response to controls. Moving the light does not silently rewrite the authored starting light value. Receipts show current runtime changes and their rule origins.
3. **Personal camera:** fit/zoom and scrolling. These affect observation, not placement.

Media initially suspected a source/runtime mismatch from a cropped screenshot. The source helper already explained starting values, but the clue disappeared when scrolled. We added a persistent label beside the textarea and changed receipt wording from authored properties to runtime properties. The distinction should be locally visible, not depend on remembering a remote explanation.

A pointer drag previews movement locally and commits one placement edit at release; cancellation restores accepted state. Arrow keys move ten pixels, or one with Shift. An unapplied draft prevents direct spatial edits rather than being silently overwritten. Undo also refuses to discard an unapplied draft. These conservative policies need further usability testing.

## Evidence, with source and scope

My direct checks:

- Node syntax check passed after implementation revisions.
- Default `document.json` evaluated and applied through the real `program.mjs`, returning the expected bloom/rotation changes and preserving three world objects.
- I inspected the actual pre-fit spatial screenshot. It supported Media's report that neighboring objects were clipped in the initial camera.
- I used the shared team desk for provisional plan a96, reviewed a98/a100, and responded in c114/c116/c117. Peer criticism changed the implementation.

Coordinator's actual browser checks, reported to me:

- Novel interval rule authored through Source, Preview and Apply; input 60 versus 80 changed visible caption and rotation as predicted.
- Malformed JSON Apply retained the accepted edition/runtime.
- Pointer drag moved thought-1 to (545,155); focused ArrowRight moved it to (555,155).
- Add a thought created thought-2. At light 20%, both thoughts rendered rgb(170,199,186); at 80%, both rendered rgb(237,197,103). The non-signal botanical token did not change.
- Save created desk subject s02 revision 1 / appearance a03. Saved starting light remained .58 despite local runtime .80; authored positions persisted.
- A normal textual desk rewrite changed the kicker and advanced subject revision to 2. The stale browser save was visibly refused with 409. Load adopted the textual change, four objects and starting light .58.

These browser checks preceded the final Fit/zoom revision. The coordinator and Media own the subsequent scaled-drag and narrow-viewport evidence; do not silently infer those from earlier pointer checks. Current visible label is `SPATIAL STUDY / BOUNDED ENGINE R3.3`.

Foundations reports twenty focused interpreter tests. Those concern state computation, rejection and bounds, not browser input. Root separately tests the storage bridge. This report does not promote those component tests into a whole-system claim.

## Peer-driven decisions and remaining pressure

Foundations challenged whether the rule view would silently erase control flow. The editor now retains non-assignment steps as editable JSON, exposes `when`, and represents all-event matching explicitly. Foundations also required domain validation after evaluator apply; the workbench checks colors, text limits, layout, numeric ranges and world-object fields on both sides.

Media required a novel relation whose behavior changes as input crosses a threshold. Root performed that test. Media's first viewport review led to an immediately visible light control and fixed-height editor with reachable Preview/Apply. The spatial review led to default Fit and personal zoom.

The main open policy is source control versus derived behavior. This prototype refuses direct placement when a rule controls the resulting x/y. Alternatives include editing a rule input, making an explicit local override or detaching that relation. The implementation deliberately does not guess among them.

Root has relayed review opportunities to Claude's team. Their external review is not claimed here until actual feedback arrives. No result establishes a blind fifth-domain extension, general distributed collaboration or the ability to author arbitrary host behavior from this workbench.

## Boundaries and limitations

- Renderer kinds are publication, note and token. This is not Photoshop, Google Docs or an arbitrary widget system.
- The AST has finite pure operations and bounded iteration. No eval, network, arbitrary imports, timers or authored DOM callbacks are provided.
- The visual editor's undo is local authored-definition history, distinct from the evaluator's guarded inverse and the underlying desk's history.
- Camera and light motion are local. They are not synchronized presence or a replicated activity protocol.
- There is one loopback storage bridge and a trusted local desk. Actor labels are not authentication; no production access-control claim is made.
- The application uses locally authored SVG/CSS. Optional web fonts have system font fallbacks; retained JSON alone does not freeze external font files or pixel-exact rendering.
- Narrow rendering, focus, pointer delivery, durability and rule correctness are separate evidence categories. Each needs its own check.
- The current parser/schema checks preserve last-good for this fixture. They are not a hardened boundary against adversarial JavaScript callers or unbounded resources outside the evaluator.

Files belong only to the isolated research prototype. Existing home/world sessions and installed applications were not modified by this authoring work.

## Final browser review and revision boundary

Root subsequently reported these actual R3.3 browser checks:

- Default Fit used scale 79.333% and preserved authored positions. A real 79-pixel drag changed thought x555 to x655, demonstrating screen-to-world mapping at non-unit zoom. Undo restored x555.
- Style Garden mist was previewed and applied; computed publication paper became rgb(229,233,222). Undo restored Warm linen.
- At an actual embedded 390x844 viewport, page scrollWidth was 375: no page-level horizontal overflow. Keyboard Tab reached World then Source, Return activated it, and Preview/Apply remained reachable in the authoring panel. This is embedded viewport evidence, not a mobile device test.
- A rule was edited through the structured Rules panel: changing rotation from light times 75 to light times 120 changed the visible angle from about 44 to 70 at input .58. This separately exercises block authoring; JSON expressions remain required.

Media inspected `spatial-fit.png`, `narrow-top.png`, `narrow-world-editor.png` and `narrow-source.png` captured by Root. I independently inspected `narrow-top.png`. The narrow overview revealed all four objects, but too much empty dotted floor delayed discovery of the tools. R3.4 makes the camera height at widths up to 480px `clamp(340px,45vh,420px)` rather than 650px. This is a view-only CSS revision; source coordinates and evaluator code were not changed. The visible runtime label identifies R3.4. A final narrow reload is owned by Root; do not infer its result from the CSS edit alone.

The first round's state model and second round's documents were not modified. The executable interpreter, storage server and their tests remain owned by Foundations and Root respectively. My implementation is confined to editing/visual-workbench plus this report.
