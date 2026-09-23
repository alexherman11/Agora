# Editing: the smallest pleasant model, tested against ordinary work

2026-09-23. Exploration only. No code, live desk, installation, schema migration or docs_2 change. Command examples below are invented notation, not executable syntax or executed evidence. This note revises round seven's preference for facets into a comparison that facets must earn.

## Full-reading receipt and changed implications

Read in full before this analysis:

- `C:/Projects/Agora/docs/docs_2/Agora.md` — 19,607 bytes.
- `C:/Projects/Agora/docs/docs_2/Dynamic Desk.md` — 5,863 bytes.
- `C:/Projects/Agora/docs/docs_2/Current Implementation.md` — 1,766 bytes; unfinished template, not evidence.
- `C:/Projects/Agora/docs/docs_2/Agora Constitution.md` — empty, 0 bytes.

Three implications differ from my previous emphasis. First, the new Dynamic Desk explicitly calls its object model tentative. Durable facets are a contender, not a conclusion. Second, subsequent edits becoming easier is a central test: a scheme can preserve every version perfectly and still fail by making a small modification too difficult. Third, familiar everyday applications, local experimentation and independent forks are central. A first personal date or comment should not require the machinery that might eventually coordinate an ecosystem of publishers.

The wider community vision raises long-term questions, but phase-one work should not pay for an imagined global standard every time a person makes a notebook. At the same time, a small working model should admit later growth without requiring the user's notes to be re-created as different subjects.

## A fair baseline and what is being compared

Compare three deliberately capable candidates:

1. **Facet plus capability environment.** One retained subject can carry independently contributed aspects. Editors offer operations against supported contracts. Views observe the same accepted state.
2. **Good structured document plus plugins.** A retained document/resource has extensible structured content and metadata, stable identity or location, commands, transactions, plugin contributions, multiple readers and explicit migrations. Give it an opaque extension envelope, independent storage from editor installation, reusable UI, and a command interface for the agent. These are engineering choices a conventional system can make; do not forbid them merely to give facets an advantage. This baseline is a proposed composition, not a claim that an unmodified named library already supplies it all.
3. **Live objects with inspectable behavior.** Retained objects expose slots/properties, messages and reusable behavior. A person can change a local definition, copy it or delegate to shared behavior. Give this candidate persistence, transaction/recovery support and an honest account of what remains shared after a fork. Do not caricature it as unrestricted mutation without recovery.

These overlap. A structured document can internally use live objects; an object can expose a document representation and acquire facets. The decision is which common concepts ordinary work and extension authors must learn, where reuse actually happens, and what burdens remain explicit.

## The ordinary notebook trace

Assume Notes and Outline can edit the same text contract, a due-date feature and comments are available, and there is one unambiguous selected passage. This is the **reuse pass**. No hidden feature invention is counted as free.

Invented syntax:

```text
new notebook "Garden"
write Garden "Buy seeds. Ask Lee about the raised bed."
set Garden due 2026-10-03
comment selection "Check shade before choosing plants."
open Garden with Outline
fork Garden as "Garden autumn"
write "Garden autumn" replace "Buy seeds" with "Buy bulbs"
open "Garden autumn" with Notes@1
remove application Review
examine "Garden autumn"
```

This trace has ten commands and eight distinct verb spellings. Those are counts of this illustrative script, not measured interaction costs. A graphical interface may use fewer or more gestures. It also requires selecting a passage and choosing a fork name, and deliberately names an older application version. All three candidates can expose this exact interface. Short syntax is therefore not evidence for an object model.

The visible concepts are ordinary ones: notebook/text, due date, selected passage/comment, another editor, and an independent copy. Application version and removal appear only because the user deliberately tests those cases. No schema identity, facet key, binding identifier or migration plan should need to appear in the routine trace. The target is zero manually repaired view bindings or refresh instructions after any accepted edit.

| Step | Facets/capabilities: work that must exist somewhere | Structured document/plugins: work that must exist somewhere | Live objects: work that must exist somewhere |
|---|---|---|---|
| Notebook/text | A content representation and editing operation | A document model and editing command | Retained content plus editing behavior |
| Due date | Optional aspect or existing field; discoverable meaning | Optional metadata/node extension and control | Slot/property and optional behavior |
| Comment | Anchor contract, storage, rendering and edit mapping | Range/annotation plugin, storage and transform mapping | Reference/anchor plus behavior keeping its interpretation current |
| Second editor | Adapter to a shared content/edit protocol | Adapter to a shared document/edit protocol | Messages/protocol shared by both clients |
| Fork | Policy for identity, shared assets and copied/interpreted aspects | Copy policy for identity, resources and extension metadata | Copy/delegation policy for mutable state and behavior |
| Old editor/removal | Compatibility limits and retained data/definitions | Compatibility limits and retained serialization/plugin data | Version/delegation limits and retained state/behavior references |

No row is uniquely solved by facets. A date is especially weak evidence for adopting a new object architecture. The potential advantage appears when independently authored capabilities combine across several representations with less integration work than the baseline.

## The invention pass: where the price becomes visible

Repeat the workflow with comments absent. A natural request such as “add comments to this notebook” may be one agent instruction, but it does not erase implementation work. Count the actual new artifacts or changed definitions, the contracts the author has to understand, and the work needed to reuse the result elsewhere.

A comment feature requires at least a target interpretation, retained comment data, an action, a visual contribution, and rules for edits that move or remove the target. One declaration may generate several of those; then count the declaration and the genuinely reusable generator, not five arbitrary boilerplate files. Also count hand-authored glue hidden in a supplied example.

For the structured-document baseline, a shared text engine may already provide range mapping, transactions, controls and command applicability. It could be the cheapest way to add good comments. For live objects, editing a retained local method or visual definition may make trying an idea fastest. For facets, an independent annotation component may travel best if other applications already implement its target protocol. Each advantage is conditional, not inherent.

The next reuse should be meaningful: add the comment feature to an independently authored reader, then alter comment sorting once and observe both uses. Media's reaction is precise: charge for one target-protocol adapter per independently structured editor, not zero glue. If every pair of comment feature and reader requires bespoke integration, the common substrate has not earned its claimed reuse.

The date case should also expose progressive meaning. A personal label `garden date: Saturday` may stay loose text. Calendar participation needs an agreed interpretation: due date versus appointment, date-only versus instant, and whose calendar. That boundary can be handled once when the person requests calendar behavior. It is unreasonable to require a new nominal schema release for the first private label, and equally unreasonable to silently invent scheduling semantics from it.

## What primary mechanisms actually establish

The [ProseMirror commands guide source](https://github.com/ProseMirror/website/blob/master/markdown/guide/commands.md) was read in full. Commands can report applicability without dispatching an edit, and many work without a view; command chains choose among behaviors. This gives the conventional baseline a concrete way to share agent, keyboard and menu action logic. It does not itself provide Agora-wide durability or arbitrary unknown-plugin preservation.

The [ProseMirror transform guide source](https://github.com/ProseMirror/website/blob/master/markdown/guide/transform.md) was also read in full. Recorded steps provide change history and position maps; mapping has boundary choices, and rebasing can still fail. This is useful reusable machinery for annotations, while showing why a generic object reference alone is insufficient. The proposed baseline must separately retain unsupported extension payloads: I have not assumed ProseMirror automatically round-trips every unknown node or plugin.

The [Common Lisp HyperSpec on effective methods](https://www.lispworks.com/documentation/HyperSpec/Body/07_ffa.htm) and [precedence](https://www.lispworks.com/documentation/HyperSpec/Body/07_ffab.htm) were read completely, with their short parent section. A generic function selects applicable methods, orders them, and combines them; argument precedence is itself configurable. This is a real mechanism for extensible vocabulary, but “same verb” can mean different or combined code. It does not prove semantic interchangeability.

The [Self language reference](https://handbook.selflanguage.org/2024.1/langref.html) was read selectively for objects, data/method slots, assignment and parent slots, not as a full language or persistence audit. Uniform messaging can conceal whether a property access is data or behavior, making local evolution attractive. The long-lived update, fork and history properties discussed here remain requirements on a proposed live-object system, not claims proved by that language reference.

## Same verb, same code: choose the reusable middle

A useful goal is one familiar verb with a shared operation protocol and as much common implementation as its meaning permits. It is not one function forced to handle every meaning of a word.

`tile` can share a layout planner, preview and input behavior if a target exports compatible geometry, coordinate interpretation, constraints and a way to accept placement. The target still supplies where accepted placement lives. A new handwritten-card family might need that adapter once. The user should not bind it separately for every new card. An application that means tiling image pixels is invoking a different operation despite the spelling.

`replace` is another limit. Replacing selected words, replacing an image asset and replacing an application implementation should not be routed together merely because each takes two arguments. They can share selection, discovery and invocation conventions; each has different target meaning and consequences.

Dynamic multimethod dispatch can reduce handwritten switches, but it creates questions about overlap, precedence and effects of later installation. An object satisfying two protocols may acquire two applicable methods. Picking whichever was registered last is simple code and poor semantics. At the other extreme, a new dialog for every overlap makes the language unpleasant.

Use an established context and explicit target to select the normal semantic operation; let that operation dispatch through its declared protocol. Defaults can follow later installations for new invocations. A captured selection or ongoing edit should retain its resolved meaning. Explicit inspection should explain which operation is selected and why. Fine-grained protocol machinery may stay internal until an author or an actual ambiguity needs it. Broad multiargument dispatch across subject, appearance, app, schema revision and context should earn its complexity against simpler explicit adapters.

## Strong safeguards have everyday costs

- **Per-definition immutable identity everywhere** creates naming and version bookkeeping for private experiments. Preserve interpretation when it crosses an independent reader/writer boundary; allow local loose fields and unpublished definitions. A centralized registry is optional. Removing it does not remove the need to know what an externally shared value means.
- **Read-only fallback for every unknown extension** protects bytes by stopping useful work. Preserve unknown material and restrict only operations whose relevant semantics cannot be maintained. An old editor should usually still rename a notebook containing unfamiliar comments.
- **Object-wide revision fencing** is simple but makes independent date and text edits conflict. Finer dependencies reduce needless retries at the price of more protocol work. Start with a simple boundary and measure actual collisions before expanding granularity.
- **Pinning every visual edit to a package generation** burdens small local changes and can obstruct the direct, playful environment. Local color, ordering and panel changes can use retained editable definitions. Stable interpretation matters at active work and shared-contract boundaries, not because every label needs a deployment ceremony.
- **Whole-environment snapshots as undo** are easy to explain but can remove independent later work. Domain operations need useful undo scope; a universal arbitrary selective-undo guarantee would be expensive and is not necessary to start.
- **Opaque preservation** keeps information but may leave a person with data no available tool can use. A readable historical fallback is useful; it must not be called successful editing support.

Defaults should do more of the ordinary work: current subject/view, usual editor, simple date display, private scope, comment-panel presentation, and a familiar content-fork policy. They should not silently decide an ambiguous date's scheduling meaning, approval of copied content, hidden external effects, or whether a fork follows future behavioral changes.

## Forks, partial adoption and the peer challenges

Foundations challenged the long-term price of nominal contracts: three community forks could accumulate incompatible due-date and review definitions for decades. This is a real argument against making a global schema registry the center of ordinary work. A document/resource can own an explicit local representation and expose a few useful shared operations. Retained interpretation identity matters at interchange boundaries, but a central authority and mandatory public version for every local slot do not follow.

A park-profile example makes partial adoption concrete. One group wants another group's guestbook panel and append-entry feature while retaining its own map appearance and event calendar. Adoption should depend on the guestbook interface alone. If the feature requires upgrading the entire park record, the implementation is too coupled for this request. Optional aliases or an adapter may connect different local layouts, but this cost is real and should be visible to the builder once.

I challenged Foundations in return: can a live fork inherit future guestbook fixes without also inheriting changed deletion or visibility semantics? Their answer rejects automatic safety. Local appearance can be an override; following compatible behavioral fixes is a standing preference with evidence, while changed semantics becomes a meaningful adoption choice. An accessibility fix entangled with a moderation change cannot be automatically separated by a graph model. This is a reason to discover component boundaries through use, not pre-pin the whole desk or promise arbitrary feature extraction.

Media similarly distinguishes replacing a comment panel or sort policy from replacing anchor semantics. The latter affects storage, ranges, history and undo. A retained local definition with references, defaults and overrides may be sufficient for the former; the latter needs a real protocol boundary. A user can be told “this changes how comments follow edited text” instead of being shown a package-dependency closure. Genuine coupling cannot be wished away by a simpler label.

For the notebook fork, separate content from the feature configuration. A content fork creates independent working text while copying applicable comments under a known policy. A feature fork changes how the user's comment panel behaves. The usual command can default sensibly from the selected subject, but the system should not clone executable behavior merely because the person duplicated their notebook.

## From notebook to workspace: the binding must survive the thought

Root's additional Embark-inspired challenge is that a set of composable widgets can still lose the thought connecting them. This is a constructed counterexample, not a new observation of Embark or the current desk.

Garden has a deliberately interpreted garden-plan date of October 3. The user asks for a view showing the plan beside the available seed orders for that week. A builder reads October 3 and puts that literal into the order query. Later the person changes the plan to October 10. Garden updates correctly, but the order view silently continues to show the earlier week. Every widget works locally; the workspace no longer represents the intended relationship. A binding that merely says “current selection” creates another error: selecting a different notebook retargets the working query without the person asking.

The smallest candidate mechanism is a retained binding in the view/workspace definition with three inspectable facts: **which stable subject supplies the value, which explicit value/interpretation is read, and what transformation turns it into this view's input**. The definition can also record whether it follows accepted changes or deliberately uses a captured value. This is not a demand for a global dependency language on every object. A simple view binding can be a short expression with an inspectable source relationship.

Invented explanatory notation, not a proposed API:

```text
Orders.query.week = week-containing(Garden.plan-date)
source: Garden's date-only planning field
mode: follow accepted changes
purpose: available orders for the garden plan's week
```

The notebook's stable identity is captured when creating the view; it does not track later selection. The date's agreed local interpretation is explicit. A raw user field named `due` is not automatically a deadline, calendar event or date-only planning field. If its meaning is merely a note, it can be displayed as text. Calendar arithmetic requires an established interpretation or a meaningful one-time choice. Renaming or removing the source field must either preserve the binding through a declared rename or expose an unresolved source; it must not silently bind to a similarly named replacement.

Defaults may infer this binding from the task. The person should not have to author it manually. But “why is this showing October 10?” should answer “It follows Garden's planning date through week-containing,” with access to the editable binding. “Keep this week fixed” can change the binding to a captured value. Those are visual/workspace-definition edits; ordinary `set Garden plan-date ...` remains an object edit whose downstream views update automatically.

If the binding fails, retain a useful last result only with a stale/unresolved indication. Do not label it current. The purpose note helps explain why a view exists; it is context, not a magical executable interpretation of intent. Where the notebook note itself captures the reasoning, a reference to that note may be more useful than duplicating an explanation into every widget.

This case changes the comparison: each candidate must retain and inspect cross-component relationships, not merely compose controls. A good document host can put the binding beside the notes; facets can reference the same subjects across hosts; live objects can expose the relationship as inspectable behavior. If any candidate requires manual query repair after routine date changes, it fails this workflow regardless of its elegance elsewhere.

## Dealbreakers and what would change my mind

The smallest model can win. I would prefer the structured-document baseline for an initial slice if it supplies the whole notebook workflow and the missing-feature experiment with fewer authored mappings and equivalent continuity. It is not disqualified because its implementation looks like a toolkit.

I would reconsider world-wide facets if a third independent consumer still needs representation-specific bridges for nearly every feature, if private extensions demand published schema/version work, or if facet identity proliferates while ordinary compatibility decisions remain hand-coded. Nominal names alone do not prevent adapter explosion.

I would favor the live-object model if inspecting and changing a local feature substantially reduces authoring work and users can understand what a fork shares. I would reject its default update model if editing a parent silently changes retained user work in unrelated places or normal recovery requires understanding a deep delegation graph.

Across all models, dealbreakers include silent unknown-data loss, comments confidently pointing at the wrong text, reinstalling an editor changing old data without an explicit operation, fresh installation changing the meaning of a captured command, or routine object edits requiring manual visual repair. A simpler model may handle unsupported cases by retaining a clear historical or limited view; it need not solve every domain first.

A bounded comparison should run the same ordinary trace, then remove comments and have independent authors add them, reuse them in a second unrelated reader, make a local feature fork, update the original, and remove its provider. Record actual authoring time, concepts consulted, declarations/glue changed, user decisions, manual refreshes, preserved drafts and wrong-target incidents. Also record when a refusal interrupts otherwise useful work. Those are proposed measurements, not results. Do not substitute command count, test count or claims of decades-long extensibility for use evidence.

The current preference is therefore a small common vocabulary with local extensibility and selective shared protocols. Whether its retained data are called facets, document extensions or live-object slots is still open. The winning model should make the second useful change cheaper while keeping the first one easy.

## Latest-reading alignment receipt

After the initial analysis, reread `C:/Projects/Agora/docs/docs_2/Dynamic Desk.md` completely. This later snapshot is 5,779 bytes, SHA256 `5513206EA05472C9D9EEEB8AE273F2CB77F3D3956AF52BA5F54A8BA883AA6CC9`. The earlier 5,863-byte reading receipt above remains a record of the source initially read.

The revision removes two introductory questions under Verbs and capabilities and lightly adjusts the following paragraph, including verbs becoming visible when entering a context. It does not change this analysis: contextual discovery, shared behavior/code where meanings align, and a tentative object model remain the relevant directions. No additional implementation claim or architectural commitment was introduced. Agora.md was unchanged according to the coordinator; it was not reread for this bounded check.
