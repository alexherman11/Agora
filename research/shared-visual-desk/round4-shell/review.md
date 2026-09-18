# Round four: transfer review against the implemented Claude desktop

Media, source-aware independent reviewer. This round asks whether the unchanged bounded interpreter helps author the desktop Claude actually built. Three panels with familiar names are insufficient evidence. The comparison is to desk-shell Notes, Editor and Together, not production Google Docs or an imagined future desktop.

## Provisional verdict

The interpreter already transfers small value relations over a declared state: selection, arithmetic, conditional writes, iteration, conflicts, preview and whole-state guards. It does not supply the host mechanisms that make those relations meaningful in a desktop: subject versus appearance identity, creation allocation, deletion policy, draft ownership, event freshness, persistence, or faithful view projection. A controller that names those additions honestly is useful integration. A controller that calculates the requested application behavior in JavaScript and calls an empty rule afterward is not evidence of transfer.

Foundations accepted the strongest structural mismatch: its first adaptation has one placement per note. Claude has shared subjects plus independently placeable appearances, including window appearances on actor screens. Sharing a note between Notes and Editor transfers one relation, but does not transfer this identity model. This is an explicit missing mechanism, not a blocker requiring the round to grow into a platform.

## Actual source grounding

Read OWNERS.md and core.js; read Editor in full; inspected Notes drawing, editing, creation, drag and text-projection paths; inspected Together's model, temporal rules, text/HTML projections and view loading; inspected relevant shell window, refresh and text paths. Also read the first120 lines of Iris checks/results.md, including the blank-page false-pass discovery. This is source-aware review, not a blind comparison or a replay of Iris's browser tests. The brief reference was relayed by root: studio a451, Round four: one desktop, built together. I did not enter Claude's studio or run its live desk.

Claude's source establishes these concrete comparison points:

- Notes reads appearance geometry from nodes and title/text/tags from subjects. It distinguishes settled world state from an in-progress gesture and actor filter. Proximity clusters are an explicitly inferred reading; named groups are durable surfaces. Creation is a command sequence through Desk.do, followed by placement of the returned item.
- Editor has per-window draft/base revision/section/caret state. It settles a whole document after2.5 seconds or departure and deliberately avoids an automatic read before rewriting, so the desk's stale-read refusal remains meaningful. It discloses whole-document rewrite and unanchored comments as limitations.
- Together derives actor and change rows from events, measures warmth in acts rather than seconds, and projects one row model into text and HTML. Its empty-context text audit explicitly does not claim to inspect the actual open window. Event timestamps, current presence and full semantic causality are not invented.
- core.js sends world writes through Desk.do, refreshes snapshots, polls events and provides subject/node queries. This is a specific host substrate. Our pure evaluator does none of this by itself.

## Three discriminating acceptance tasks

### A. One subject, two appearances, one editor

Place the same document subject twice in Notes. Open that subject in Editor. Author a rule that changes the subject title when a declared condition changes. Both appearances and Editor must show that same subject title. Then move only one appearance: the other appearance must stay fixed, and Editor must retain the same subject and dirty draft. Text view must name both occurrence identities, shared subject identity and each placement.

Why discriminating: a flattened note array cannot pass by merely repainting three panels. Content identity and occurrence identity have different effects. Status before implementation review: Foundations explicitly says independent occurrences are not modeled. Do not count the weaker shared Notes/Editor title demo as this task passing.

### B. A rule installed before creation survives lifecycle changes

Install an authored arrange/classification rule, then create a new qualifying note through the ordinary controller. Without changing the program, the new object must participate in its existing rule and appear in Notes, Editor selection and text inspection. Delete the selected appearance while an Editor draft exists. The result must follow a declared policy: preserve the subject and other appearance; retain an orphaned draft if necessary; or refuse without loss. Together/text must disclose the actual create/remove event and scope, not fabricate presence or claim an uncommitted draft was saved.

For the narrower one-placement prototype, report separate partial results: new allocated note participates; dirty-selected removal refuses; clean subject removal succeeds; reused identity is prohibited. Those are valuable but are not occurrence-only deletion. Creation/deletion must be host lifecycle operations or explicit authored collection edits with validation; do not hide them in the renderer.

### C. Author behavior while another app holds unsaved work

Type a distinctive draft in Editor. Author an AST rule that rearranges/recolors Notes and changes an event-log display relation. Apply it while the draft is dirty. The exact draft, selected target, base revision, input node and focus must survive unless a clearly explained conflict blocks the change. Save once, and verify the same controller path updates committed content, Notes and text view. Repeat with an intervening committed content change: save must refuse while preserving the draft, with both versions inspectable.

Distinguish model and browser criteria: a JSON string surviving proves data preservation; it does not prove the actual caret, composition or focus survived. A geometry-only revision may conservatively conflict with a content draft if the prototype uses one revision for everything; report that limitation rather than calling it precise conflict handling. Text must label committed content, local draft, rule program revision and bounded event coverage separately.

## Two failure pressure tests

1. **Delayed event and identity replacement.** Capture a save/remove/selection event with target identity and base revision. Change or remove the target before delivery. A late event must not silently overwrite a newer edit or target a replacement with the same display title/index. Monotonic nonreused ids prevent one reuse case; base-revision checking is still required for delayed events on a surviving id. Re-running preview against the latest state is not a substitute for validating the original event's assumptions.
2. **The adapter does the work / projection drops the work.** Trace each novel behavior from input through AST rule to proposed writes and application. Replace the program with an empty one: lifecycle operations may still allocate or validate, but the claimed authored arrangement/color transformation must disappear. Then introduce a newly created item and an unresolved draft; actual text inspection must include them with scope labels. Three app headers and seeded JSON are not coverage. A bounded event list must announce its cut, and whole-desktop summaries must not silently truncate material warnings.

These pressures were sent to Foundations and Editing before their implementation was available. Foundations agreed to keep allocation, lifecycle, bounds, CAS, event recording and projection explicitly in the host and to keep behavior outputs in AST rules. It accepted the duplicate-appearance limitation. This changed the proposed verdict from a possible desktop transfer to a transfer of several relations within a narrower host model.

## Independent unchanged-interpreter probes

Command from C:/Projects/Agora4:

    node research/shared-visual-desk/round4-shell/review-probes.mjs

Six probes passed against foundations/program.mjs without editing it:

| Probe | Observed result | Meaning |
|---|---|---|
| Fresh id-filter after array reorder | Correct note changed | Rules need not target a fixed seed index |
| Reorder after preview | stale-preview refusal | Whole-state guard protects that proposal |
| Delete/recreate identical JSON without incarnation | Old proposal applied | Absence of lifecycle identity is a demonstrated boundary |
| Replacement with changed incarnation | stale-preview refusal | Encoding lifecycle identity lets the existing guard detect it |
| Set whole collection with literal | New/removal data accepted | Creation is expressible as data replacement; allocation and lifecycle semantics are not supplied |
| Fresh preview of a delayed save | Newer text overwritten | Proposal freshness is not event freshness |

A passing probe can intentionally demonstrate a missing guarantee. These are pure interpreter executions, not controller or browser tests. They neither show Claude's server reuses ids nor accuse the new controller of that defect. They establish what the unchanged interpreter cannot infer from absent input.

## Claude source concerns, not live reproductions

The comparison implementation also has gaps; it is not a perfect oracle. Editor's document-row click awaits settle and then unconditionally loads the next document, even if settle set a refusal fence. Its missing-node refresh resets selection and redraws; draw can load the first remaining document and reset draft state. These paths warrant a draft-preservation test. Notes prepends look before settling content, unlike Editor's explicit no-read-before-rewrite path; this may renew the actor's seen state before writing an older draft. Neither concern was reproduced against the live desk in this round.

Notes text reports only a first-line body excerpt while the card renders full text; its uncommitted edit warning does not include the draft value. Editor's text output truncates comment bodies to60 characters. The shell's desktop summary takes the first six lines of each app's text. These are concrete coverage cuts to inspect, not evidence that the visual and textual foundations must encode identical pixels. Together's shared model reduces one kind of disagreement but cannot prove that its source model included every relevant fact or that a warning is legible on screen.

## Source snapshot

SHA256 at initial review (these independently developed files may change afterward):

| Source | SHA256 |
|---|---|
| Claude OWNERS.md | FC426416C58065F8C1CE6EC6E15BA956574AE3D7016379A63765314459356050 |
| Claude core.js | BE92EB9DA68DE1401D1443EAA92B9CF9482D1742CF26A854D6D6F87ACD4E8959 |
| Claude apps/notes.js | C2549EEDFBB0C6D1AA8F5FE00F4E1602C3546A21B2AF6674D96DE73C411148C1 |
| Claude apps/editor.js | 2997ADE1AE7B04FCB7DDEEC54BF9BEC1D671F9049610F5CD6B165C439114808E |
| Claude apps/third.js | C26586D370A636BC86C21B95AE1830EC9608B2BC4313355D6DCB3C21C1C762F8 |
| Astra foundations/program.mjs | 7535FFBD340AB39BA9540C0FF521F676FC7C991513D2084859622E970762F4CE |

The controller review and closing verdict follow. Root retains browser hands; I have no enabled browser surface.

## Controller cross-review and concrete correction

Read the new model.mjs and program.json, plus the relevant model.test.mjs acceptance tests. Then ran review-controller.mjs independently. Its first run passed four checks and failed the fifth: an authored rule on draft could write shared notes.0.text, increment the note revision, yet receive local-view scope without incrementing shared revision or recording an event. The controller classified scope from the action name while admitting shared writes from any event. That was an actual model execution failure, not merely a source suspicion.

Foundations corrected admission: local-view events now refuse writes to notes or windows before applying the proposal. It chose refusal instead of silently converting a local gesture into a shared write. Notes text projection also gained the rendered color after my coverage critique. A fresh run of all six independent checks passed:

- A newly allocated note received the already-installed AST classifier, including new tag and color; multiline content appeared in text.
- Removing a dirty selected subject refused and retained the exact draft.
- A queued action carrying its original expected revision refused after an intervening shared action.
- With an empty program, Arrange did not move the notes. This directly checks that the host was not secretly calculating the layout.
- Shared writes could not hide under a local draft event.
- Text projection exposed the authored note color.

Exact command:

    node research/shared-visual-desk/round4-shell/review-controller.mjs

This establishes controller behavior with supplied actions. Event revision guards are optional arguments; the frontend must capture and supply the original guard for a delayed interaction. The model test alone does not establish that it does. I sent that requirement to Editing. Likewise, exact draft preservation in these tests does not establish DOM focus, IME or caret continuity. No round-four frontend/browser check was performed by media before this report closed; root's later browser evidence must remain separately attributed.

### Responsibility boundary

| Layer | What it actually supplies |
|---|---|
| Frozen program.mjs | Bounded expression/iteration execution, proposed writes with rule origins, conflict rejection, canonical-state preview guard |
| Authored program.json | Note selection and loading into Editor, draft/save field updates, clamped note/window placement, tag/color relation, arrangement arithmetic, acknowledgement and explanation strings, classification of newly allocated subjects |
| Host model.mjs | Fixed schema and app identities, action inputs, local/shared admission, monotonic allocation, removal policy, dirty-draft refusal, optional queued-event guards, save CAS, note/shared revisions, event retention, program installation and projections |
| Frontend/transport | Actual input capture, preserved editing nodes and focus, view layout, correctly captured event guards, browser display and persistence where implemented; these were not proven by this review's model tests |

The host is a substantial domain adapter, not a universal renderer or a thin rename. Its existence does not invalidate the useful rule transfer. It makes the conclusion precise: the same evaluator can author behavior inside this newly built desktop model. It has not replaced Claude's implemented application substrate or automatically ported its apps.

## Controlled Claude refresh race

A separate probe reads unchanged Claude core.js, executes its functions in a Node VM and supplies a controlled fetch implementation. No HTTP requests occur. Two concurrent refreshes return snapshots out of order:11 first,10 second. Observers receive11 then10 and Desk.snapshot ends at10. The executable counterexample passed.

    node research/shared-visual-desk/round4-shell/review-core-race.mjs

This demonstrates a possible asynchronous schedule in the inspected source. It does not establish that this sequence occurred in Claude's live browser, and no live source was changed. Root alone may relay the finding. A future asynchronous adapter should preserve response ordering or reject an older snapshot; adding rules cannot infer transport ordering omitted by the host.

## Closing comparative verdict

| Actual Claude app concern | Transfer demonstrated here | Exact missing mechanisms |
|---|---|---|
| Notes shares subject content across placements | Same note feeds Notes and Editor; authored layout/tag/color and new-note classification execute | Multiple appearances per subject, named groups, proximity-cluster computation, links, selection/occlusion semantics and arbitrary tag-membership operator are not transferred |
| Editor holds draft and settles through guarded commands | Separate draft/committed projection, save CAS, dirty-removal refusal, model-level draft retention | Rich text, section identity and anchors, automatic settle timing, merge/recovery policy, actual focus/IME continuity; one subject revision conservatively treats geometry changes as draft conflicts |
| Together makes change evidence actionable | Bounded actor-labelled event rows, rule origins, explicit retained-history cut, acknowledgement | Claude's Needs you/first-touch logic, grouped changes, warmth, command actions and multiple actor-local views are not ported; labels do not establish presence/authentication |

The unchanged interpreter was useful beyond the earlier botanical publication. It drove multiple relations across a newly built Notes/Editor/change-view model, and removing the program disabled the claimed authored arrangement. The first adaptation nevertheless leaves the strongest subject/appearance task unsupported. Six evaluator probes, six controller checks and one controlled core-race counterexample are the independent execution evidence. There is no universal platform claim and no claim that running Claude apps have been rewritten to use our interpreter.

Final source/probe SHA256:

| File in round4-shell | SHA256 |
|---|---|
| model.mjs, after review fixes | 5062893A7A803519BFF4173706FDFAE4F9F070EB78A6CA5EFFFD300CCFCB2D65 |
| program.json | 7BCF84941D750B01FF1DEC83892B330668E379A2728FC47D22E8AF0A11763C0A |
| review-probes.mjs | 707DC58514F80513B582AF819C111E7DB1E2B5742F80B0DB2C2FE5458560D94B |
| review-core-race.mjs | 5E5F04CE7D64CE973C4F6374CFCD2B99E578205CA523E3136268113063E34D13 |
| review-controller.mjs | C344AEA29EB5AA9CD95503D316231EE5D738251D5649630FCAF2D29ECB58B2D6 |

## Final frontend addendum: screenshot and async guard review

I inspected the actual root-captured image C:/Users/Alex/.codex/visualizations/2026/09/18/01a0b5fe-d025-7513-bb15-5a9279c2a259/review/round4-commonplace.png. This is screenshot review, not my browser execution. The cream and pale green desk, colored notes and distinct Editor page form a coherent shared workspace; selected-note outline and matching note/page content make the connection visible. All three windows and primary desk controls are visible in this capture. Notes has clear internal scrollbars, and the Editor has its own scroll region.

Remaining visual usability limits: small, faint metadata and secondary action labels are harder to read than the large titles; nested app scrolling increases navigation effort; raw rule identifiers occupy much of Activity's default reading surface. The third note extends below Notes' visible area, with a scrollbar indicating continuation. I do not infer lost content from that crop. This single desktop image establishes neither narrow-screen behavior nor a contrast/accessibility measurement. No further feature changes are requested by this bounded review.

I also read final app.mjs load/save paths and dispatch/render behavior. The requested async correction is internally consistent: accepted typing replaces current with a new document object; loadDesk captures startingDocument before awaiting and refuses to adopt fetched state if current differs afterward. saveDesk captures savedDocument, serializes that snapshot, and does not replace current on completion. If edits produced a newer object while saving, its success labels the saved snapshot separately and says newer work still needs saving. The shared loading flag serializes load/save requests. This is source reasoning about those races, not an executed delayed-response browser test. It relies on accepted model changes continuing to replace document identity rather than mutate it in place. The editor textarea node is retained by render; Notes nodes are rebuilt. Actual caret/IME continuity under all updates is not established by this source reading.

Root separately reports actual browser checks: edit/save updated Notes and Activity; stale draft retained exact text until explicit Reopen saved; creation received installed classification; changing arrangement multiplier150 to210 yielded x20,230,440; keyboard and pointer movement worked; checkpoint save s02:1 and reload restored content and four events. These are attributed root input observations. They extend the earlier model evidence; I did not perform those browser actions. The screenshot shows the restored three-note checkpoint, so it is not by itself evidence of the earlier created-note step.

Final inspected app.mjs SHA256: 816301723A9D0CCBAA91E84F8F96BB1D3A552FFAFE21F80580718B83194278EC. Earlier model hashes identify their earlier reviewed checkpoint, not an assertion that all later source files remained unchanged.
