# Round four: how far unchanged rules adapt to Claude's multi-app desk

2026-09-18, Foundations (Astra team). This is a comparison experiment, not a port of Claude's apps or a native Agora implementation.

**Result:** the frozen round-three interpreter expresses useful behavior across Notes, Editor and Together: semantic target selection, placement, tag replacement and color policy, shared-subject text save, arrangement, window movement, and classification of newly created subjects. It does not supply the surrounding application system. Six explicit JavaScript host mechanism groups remain. Twenty-one focused controller tests pass, including counterexamples and refusals. The interpreter SHA256 remains `7535FFBD340AB39BA9540C0FF521F676FC7C991513D2084859622E970762F4CE`; a test checks it.

## What was actually inspected

Read Claude's current `research/text-desk-lab/notation/desk-shell/OWNERS.md` and all of `core.js`. Read the Notes source through its drawing/interaction sections and searched its Desk.do calls; read Editor's model, parse/load/settle sections and its text/refresh tail; read Together's row-model, history interpretation and projection sections. The first combined read was output-truncated, so I followed it with a bounded Editor read and targeted Notes command search. This is a source-aware comparison, not a blind usability review, and not a full line-by-line audit of all app source. I did not run or modify Claude's world, shell, or app files.

The inspected contract is stronger than 'three panels': Claude routes world mutations through `Desk.do`, separates subjects from appearances, stores windows as appearances on actor screens, and requires per-window text projection. Notes distinguishes live gesture drift from the accepted command. Editor holds drafts and does not refresh its seen revision immediately before rewriting, preserving the stale-write fence. Together builds both graphical and textual displays from a common row model and labels limited evidence about others' activity. These source observations motivate the tests; they are not independently reproduced live behavior here.

Our counterexample is explicit: one Claude subject can have two independently positioned appearances. Editing it through Editor should affect both appearances, while moving one leaves the other fixed. Our initial model combines subject and one placement in each note record. Its `duplicate-appearance` action refuses. Shared identity across two app panels is a narrower success and does not pass this pressure.

## The runnable slice

Owned artifacts:

- `model.mjs`: controller, host bridges and common text/row projections.
- `program.json`: 14 authored rules consumed by the unchanged interpreter.
- `model.test.mjs`: 21 focused checks.
- This report. Editing owns the interface files; Media owns independent probes and review. Root owns serving and persistence.

A document is `{state, program}`. State contains note subjects, selected subject ID, an editor draft/base revision, three windows, current event inputs, bounded accepted-event history and Together's reading position. Each note has id, title, plain text, tags, position, color, revision and creation order. Notes and Editor resolve the same object ID; they do not synchronize two copied document bodies. The editor draft is intentionally a separate unsaved value.

Exports are `initialState()`, `dispatch(document, action, {actor})`, `project(document, app)`, `asText(document, app)` and `hostPrimitives`. Dispatch returns `{ok, document, receipt, errors, diagnostics}`. A refusal retains the original document object, including exact draft and installed program. Receipts distinguish rule paths/contributors from host mechanisms and distinguish shared actions from local-view actions.

Current actions are select, move, tag, draft, save, arrange, mark-seen, window, create, remove, program and reload-editor. Optional `expectedRevision` or `expectedSubjectRev` checks protect a delayed event's assumptions. These guards are not inferred merely from taking a fresh interpreter preview. An optional editor action `id` must also match the currently open subject, since local selection can change without a shared revision. Synchronous local UI callers can omit these guards; asynchronous callers then have weaker admission and must not claim queued-event protection.

## What the rules really do

| Behavior | Authored AST result | Host contribution |
|---|---|---|
| Open note in Editor | Select matching id; set selected id, draft, base revision and status | Check subject exists; refuse replacing an unresolved draft |
| Move note or window | Select target and clamp event coordinates | Supply event input, validate bounds, record accepted change |
| Tag note | Copy incoming tag array; compute color from exact priority-tag-list match | Validate tag strings and lengths |
| Type draft | Set draft, dirty flag and explicit unsettled status | Bind text input; restrict local events from material writes |
| Save draft | Select editor subject and write its text; clear dirty status | Check base revision before evaluating; stamp new revision |
| Arrange | Compute x/y from creation order and editable spacing constants | No host arrangement formula |
| Create | Classify the new subject with authored tags/color after allocation | Allocate unique monotonic identity, create record shape, stage it before running create rules |
| Together | Authored summary plus acknowledged reading position | Append attributed change evidence; construct event rows |

The arrangement test installs a changed AST expression and then runs Arrange: x coordinates change to 12, 87 and 162. Neither model source nor interpreter source changes. This is stronger evidence than merely invoking a fixed adapter function from a nominal rule. It is still only one small authorable policy.

Creation is also deliberately mixed. The host constructs a note with required fields and a nonreused ID; the existing `classify-created-subject` rule assigns its tags and color. A failing create rule discards the staged identity/record as well as rule effects. This supplies useful lifecycle composition, but does not establish that the rules themselves can allocate objects.

## Counted host mechanisms and why the count matters

`hostPrimitives` names six groups. These are exposed architectural responsibilities, not six tiny generic calls concealing an app clone.

1. **Event input and admission.** Action vocabulary, scalar/domain validation, capacity bounds, target existence, dirty-draft selection/removal refusal, allowed write paths and local/shared scope constraints are JavaScript.
2. **Identity creation/removal.** Record construction, monotonic ID/order allocation, deleting a record and cleaning selected/editor references are JavaScript. The same frozen evaluator then runs lifecycle-event rules over the staged result.
3. **Revision and save CAS.** Subject revisions, save base-revision checks, optional delayed-event guards and updating the accepted editor base are JavaScript. All note-field changes share one revision, making placement invalidate an open text draft conservatively.
4. **Event-history append.** Sequence allocation, actor attribution, changed-identity list, retention and omission boundary are JavaScript. The last 40 shared events are retained; draft/select/reading-position actions are local and do not become shared events.
5. **Program installation.** Host accepts a new JSON program after interpreter validation and records installation. Installation does not implicitly run Arrange. Invalid source leaves the prior installed program and draft untouched. Source/draft editing UI and focus preservation are separate interface work.
6. **Projection.** Notes, Editor and Together row models and their plain text rendering are JavaScript. The rules do not author these apps' structure, typography, focus behavior, input binding or presence interpretation.

The rendering adapter, explicit checkpoint transport and authenticated persistence are further host/application work outside this module. The current checkpoint stores a whole app-state/program JSON document in an isolated desk subject. Claude's inspected contract sends typed desk operations per gesture. These have different history granularity, integration and authority boundaries; a shared-looking UI does not make them equivalent.

The largest untransferred responsibilities are not arithmetic. They are identity/occurrence lifecycle, transactional history, usable draft conflict recovery, and the composition of applications themselves. The 14 rule programs move meaningful policy out of imperative code, but do not turn this adapter into a general authorable application platform.

## Explicit language and model failures

The frozen grammar rejects `append` and `contains`. Arbitrary set-add tagging, dynamic record construction, filtering/removing a record and maintaining general event lists are not available as convenient authored operations. Tags here are whole-array replacement, and priority color checks an exact list, not membership in arbitrary tag sets.

Media's independent probe corrected my early shorthand about creation: `set notes = [lit, completeArray]` can indeed replace the entire collection, creating or removing JSON records. Our own test confirms that interpreter capability, then confirms that this controller refuses it at its host-owned lifecycle boundary. Thus the accurate gap is dynamic collection/lifecycle support and invariants, not an absolute inability to represent new data.

Duplicate appearances, rich-text span formatting, general undo/redo, anchored comments, incremental text operations and dependency scheduling are unsupported. They are not filled in with hidden JavaScript substitutes for this round. Plain multiline text, quotes, angle brackets, backslashes and dollar signs survive the model's draft/save path exactly. Actual browser input/rendering is a separate check.

After a dirty draft, rule installation and arrangement preserve draft text, dirty state and base revision. But arrangement changes the same subject revision, so save refuses even if only geometry changed. There is no merge or rebase. Editing identified the missing recovery path, so a narrow `reload-editor` action now requires `discardDraft: true` and runs an authored rule to reopen current shared text/revision. Without the explicit flag, it refuses and retains the exact draft. The UI must label this choice as discarding the draft; it is not automatic conflict resolution. This is a clear limit of the conservative model, not a completed collaborative editor.

Identity is not reused during the controller's normal lifecycle, and delayed actions for a deleted ID refuse. This is narrower than durable incarnation-aware authority over imported or externally rewritten state. JSON checkpoints are not a protected native schema; actor names are labels, not authentication. Event rows do not prove online presence or preserve a full causal graph.

## Peer pressure changed code

Media caught a real invariant violation in the first controller: dispatch classified draft/select/mark-seen as local, but rules could still write a note field during those events. The note revision could advance without shared history. I changed admission to refuse shared note/window writes from local events before applying them, and added a regression that tries to smuggle a text rewrite through a draft rule. The original document remains unchanged.

Media also found Notes text omitted the color displayed by the graphical app. The row projection now includes color and a test checks it. This fixes one concrete omission; it does not establish complete graphical/textual equivalence.

I accepted Media's two-appearance challenge as a failed pressure rather than silently widening our claim. I pushed back on reducing programmability to an adapter line count: the stronger behavioral question is whether changing an authored rule changes future behavior without editing the adapter. The arrangement and new-subject classification tests answer yes for their bounded policies; the six host groups make their dependence visible.

Team desk evidence: a128/s127 records the first working boundary and 18 checks; subsequent checks brought the count to 21. Comment c129 on Media's a126 acknowledges the creation correction, real scope bug and remaining multi-appearance gap. Earlier contracts were sent to Editing and root before coding, allowing the UI to consume the same dispatch/project functions. Claude source was read-only; root remains the sole team liaison.

## Executed checks and next discriminator

Executed with Node v24.19.0:

```powershell
& 'C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' --test research/shared-visual-desk/round4-shell/model.test.mjs
```

Twenty-one pass, zero fail. Coverage includes frozen-interpreter hash, shared literal draft/save, authored move/tag/color, edited arrangement formula, new-object classification, failed-creation atomicity, dirty-draft preservation and conservative stale save, dirty removal/selection refusal, delayed-event guards, invalid installed source retention, unsupported operators, literal structural replacement versus host admission, bounded history with disclosed truncation, window rules, note capacity, unsupported appearances/rich spans, local-write smuggling, color projection, explicit discard/reopen, queued editor target mismatch after local selection, and window-change identities across shared event types.

Root's browser test and Media's independent review provide the separate input/rendering evidence. This report does not infer screenshots, pointer delivery, focus retention, persistence success or Claude runtime behavior from passing Node tests.

The next useful discriminator is the missing subject/appearance test, with one subject shown twice and an unresolved editor draft. Introduce the minimum identity/occurrence vocabulary, then ask whether a newly authored rule can address subject text or one occurrence's placement explicitly without another app-specific adapter branch. If every such distinction needs a new hard-coded action, this rule language is a policy component inside applications, not their common authoring foundation. If a small reusable object/lifecycle capability makes the same program and projection contract work across independently built apps, that would justify extending the foundation. This round establishes the narrower policy-component success and preserves the rival conclusion.
