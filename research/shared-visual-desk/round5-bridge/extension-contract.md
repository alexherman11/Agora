# Round five: a bridge that can acquire new capabilities

Media's independent extension and action review. Proposal, source inspection and executed probes are separated below. No Claude source, live world, native package or runtime was modified. This report specifies a foundation boundary; it does not propose another finished desktop.

## The useful boundary

A scene definition should compose installed capabilities and say how world material appears and what actions mean. It should not force every future domain into text on cards. A new document arrangement can be a definition change; a text shaping engine, raster compositor or media transport remains an engine. Making an engine reusable and installable through the desk is different from making it disappear.

The minimum extension is a **versioned component reference with typed material, view, selection and action contracts**, plus bounded inspection and an activation/recovery protocol. The scene bridge should resolve that reference through the installed capability registry. Unknown capability kinds must remain inspectable and refuse activation, not silently render as an empty card. Authoring happens through world/package operations; a missing engine is an explicit capability-installation task. Neither ordinary lens authoring nor an implicit fallback may write host JS/CSS or mutate the shell.

This does not promise invention without executable implementation. Definitions can invent compositions and algorithms expressible by their installed evaluators. A genuinely missing primitive needs an implementation packaged as an explicit reusable capability and activated through the desk. Choosing or adding that implementation runtime is a separate architectural decision. The current browser-package facility demonstrates retained executable packages; it is not permission to bypass the user's definition-first direction by generating a new application in HTML for each task.

## Four pressure cases

These are domain requirements used to challenge the proposed bridge, not claims that integrations with Google Docs, Photoshop, YouTube or VS Code were built.

| Work | Definition-level authoring once capabilities exist | Reusable capability required | Discriminating failure |
|---|---|---|---|
| A Google-Docs-like document | Page/outline/comment composition; styles; toolbar action bindings | Structured text with stable span/range identity, shaping and selection mapping, editing/composition operations, explicit draft and conflict policy | Insert text before an active range, change wrapping, then bold the selected words. Pixel rectangle or old character index must not silently select a different passage. Whole-text rewrite can be a declared fallback, but is not range editing. |
| Photoshop-like work | Arrange layer/tools panels; bind brush and visibility controls; define reusable effects from existing operators | Vector paths and transformations, raster/tile resources, compositing/blend semantics, masks, versioned brush interpretation and stroke operations | Paint on layer L while pan/zoom or instrument definition changes. Accepted samples must retain the intended coordinate frame/layer incarnation/instrument. A raster preview or text label cannot stand in for this meaning. |
| YouTube-like transport | Compose player, controls, captions, queue, timeline and commentary views | Playback clock, decode/composite service, buffering/seek state, caption/time mapping, bounded observations | User seeks while a buffered frame still shows the old time. Inspection distinguishes requested time, accepted transport state and presented frame; predictable playback does not append one world event per frame. |
| VS-Code-like editing | Compose file/tree/editor/diagnostic/terminal panes; author key bindings and command palettes | Exact text buffer/ranges, syntax and language-service versions, selection/IME behavior, typed edit operations, process/resource observations | Replace a range containing quotes, indentation and an empty final value. Preserve bytes/declared newline policy; do not rename visual coordinates into textual selection. A running terminal is an observed external process, not replayable native state. |

None of these calls for an app-name branch in the scene painter. A component can be a text editor, timeline, vector surface or a newly invented domain capability. The common contract governs reference, input, observation and lifecycle. The installed engine governs the domain semantics. A later component must be addable through the registry without editing the painter for each app; this remains proposed and requires a real unseen-component trial.

## Minimal proposed component contract

A definition instance contains only references and authored parameters:

    instance identity + definition revision
    component reference: package, installation revision, exported component
    binding: subject identity, optional appearance identity, material facet/type
    parameters and named slots validated by the component schema
    selection/view state references separate from committed material
    typed action bindings with input schema and declared effect scope

The component descriptor supplies four obligations. These are proposed obligations, not already enforced fields of today's manifests:

1. **Inspect:** accept bounded context and return stable targets, current bindings, supported actions and observation coverage. Include material, definition and engine revisions. Report omitted ranges, opaque assets and unsupported operations. A raster asset may have dimensions/layers/tile versions without an invented semantic caption. A timed result reports observed clock/frame separately. The pixel renderer may reveal facts the text projection cannot infer; it must identify that boundary.
2. **Preview:** validate typed input and dependencies, produce bounded proposed effects plus any provisional rendering. Preview must not silently commit or launch external effects. Mark predicted pointer samples and speculative frames. Reuse the host's transaction/candidate mechanisms where applicable; do not call an arbitrary side-effecting engine and rename its output a preview.
3. **Activate:** pin an executable build and schema/contract version, check compatible bindings, then adopt at a declared interaction boundary. Running gestures and drafts must either finish under their pinned interpretation, migrate through an explicit supported transform, or remain retained while activation defers. A rule that changes tomorrow's brush does not reinterpret today's held stroke.
4. **Recover:** retain the previous working definition/build and outstanding draft/gesture state. An invalid candidate remains editable but does not erase the active picture. Restoring executable code preserves current material; it is not a rollback of everyone else's edits or a replay of external effects.

These obligations are enough to open an extension seam; they do not prescribe one scene tree as the internal representation of all engines. A specialized renderer may be opaque internally, but its inputs, typed actions, observation limits and revision correspondence must be inspectable. If an engine cannot expose a selection operation or a material dependency, the bridge must report that limit rather than invent an editable correspondence.

## Typed actions: smallest useful envelope

For an installed-capability version, the proposed envelope is conceptually:

    handle: host-prepared binding to a resolved target and definition
    capability: package + installation revision + action
    expected: observed subject/appearance revisions and definition revision
    args: schema-checked JSON, preserving strings exactly
    interaction: id, phase, optional coordinate-frame/selection revision

The handle can retain fields server-side rather than repeat all of them on the wire. The key is what it binds. It must not resolve an old selector against a new world and call that the same gesture. Subject changes and appearance changes have distinct target types. An empty string is valid data when the action schema permits it; quotes, dollar signs, whitespace and newline policy belong to the domain, not command-template sanitation.

Root's bounded round-five bridge uses existing experimental Desk dispatch and an in-memory lock, with generic rewrite(subject) and move(appearance) adapters. That is appropriately bridge code: it adapts existing native meanings and revision guards, not Notes-specific behavior. It is not an authenticated service or installed component runtime. Its host-issued handle should bind the lens definition revision, observed target revision and subject/appearance relation. For moves, supplied coordinates must have a declared frame; a later zoom/style change must not reinterpret an old gesture. Parsed but unsupported gestures should refuse explicitly.

Do not prepend a fresh look at commit. Seeing a painted revision and authorizing an operation on that revision is different from refreshing the actor's seen state immediately before an old draft is sent. Observation can establish a guard; it must not silently replace the old guard. A typed action adapter also avoids replacement-string expansion, ambiguous quoting and accidental command composition.

## Exact existing Agora pieces worth reusing

Read docs/Reference/Runtime Guide.md, the relevant current Implementation Status sections, and current source. The Runtime Guide contains an older statement that general application mounting is absent; that statement is contradicted by application_schema.py, applications.py and the recorded integration evidence. The source and newer status sections take precedence for this comparison. No installed process or live tool inventory was queried, so these are checkout implementation findings, not claims about the user's active runtime.

| Existing mechanism | Verified source and precise reuse | Remaining gap |
|---|---|---|
| Retained source/build/installation | packages.py: package.save/build/install/restore; distinct source revision, immutable receipt and installation revision; tools discovery pins action revision | General dependency resolution remains absent; a component descriptor must not invent resolved dependencies |
| Typed headless capabilities | packages.py invoke validates input/output schemas and proposes atomic changes; current actions may declare reads via queries/ids/arg_ids; scoped_context.py guards object revisions, query membership and absence | A renderer/selection/gesture contract is not supplied by these action schemas alone |
| Isolated candidate exercise | candidate.exercise runs Python in the separate yard and validates proposed writes against disposable native state; native_writes:0 result | Not a generic browser-input test or complete isolation of external effects |
| Typed application material | schema.define/world.transact; application_schema.py application schemas/defaults/read/write facets and bounded relations | Register facets do not implement collaborative text ranges, tile storage or time services |
| Existing browser applications and appearances | application.open binds an installed package to a subject; application.position changes one view's bounds; surface returns pinned artifact/context; close/reopen/refresh/uninstall preserve declared material/state | Whole application mounts exist; arbitrary nested scene-component mounting and the proposed common inspect/selection contract are not thereby implemented |
| Scoped application transport | application.request checks lease and scope; application_data.py supports subject read/transact, state.get/state.set and declared related.* routes | Do not widen a lens action to management or guest authority merely because the definition names a method |
| Retained drafts and compatible update | applications.py retains view state and preserves compatible leases; host/frame.html and builtin shell implement prepare-reload/reload-ready; Implementation Status records separate-browser draft/update checks | Those historical tests do not prove a held brush, codec or IME upgrade; domain-specific continuity still needs tests |
| Retained browser assets | current packages.py/browser_assembly.py accept ordered package-local classic scripts/styles assembled into retained HTML | This is reusable engine packaging, not a reason for ordinary application authoring to edit JS/CSS; binary media resources need a separate explicit resource contract |

Current application.contracts is a bounded descriptive object, not an enforcement engine for the proposed obligations. Current python-1 actions and browser-1 UI have separate runtime shapes; do not pretend one manifest already exports an arbitrary browser component and Python action pair with automatic dependency resolution. A descriptor can reference pinned capabilities explicitly while the bridge adds only the missing generic contract checks.

## Independent hostile handler probes

Command from C:/Projects/Agora4:

    node research/shared-visual-desk/round5-bridge/hostile-fixtures/lens-handlers.mjs

The fixture loads actual unchanged lens.js into a Node VM, provides minimal DOM objects and a controlled fetch implementation, then invokes its installed handlers. No browser, HTTP, live desk or Claude file write occurs. Six expected counterexamples reproduced:

| Actual handler path | Observed outcome |
|---|---|
| Edit `  print("hi")  ` | Sends `print('hi')`: trim and quote replacement change literal material |
| Edit to empty string | Sends no command; deletion cannot settle |
| Edit `a$&b` | Sends `a$valueb`: JavaScript replacement-string metacharacters corrupt input |
| Declared drop action | No drop listener installed |
| Begin drag then pointer cancellation | No pointercancel handler; busy remains set and normal refresh stays blocked in the controlled handler execution |
| Receive refused lens after valid scene | Painter removes its last working picture rather than retaining it while reporting candidate refusal |

These are handler-level executable counterexamples, not claims about physical pointer capture, browser focus or an observed live user failure. The first three establish literal-input loss without relying on any supposed command-injection exploit. Root's exact typed adapter is the narrow repair direction; foundations independently tests scene parsing/building and stale guards. This fixture intentionally records the old source boundary and should not be read as testing root's adapter.

Read coverage: scene.py and lens.js in full; lens.html; current core/style integration entry points; complete relevant Runtime Guide; Implementation Status integration/update sections; package validation/invoke/build identity sections; application schema, specs, data requests and dispatch; scoped-context validation. No full external media engine or complete native runtime suite was reviewed or run.

SHA256 evidence snapshot:

- scene.py: 4957D5218F539CCA2F91B04DFC35F99F80D034A52CAE1C8E7A432D9F4C06E68D
- lens.js: ED3E88FCD83C8AB7EE93642AC231440C2DAB8632C8794276FC182FFC81F4D97F
- hostile-fixtures/lens-handlers.mjs: EFA5C11EC3C09E3F67667F2448FD2894CFE78150C61ED857D9083D508BA86760

Team discussion: a142 records early findings. Editing's definition-only trial accepts the distinction between role styling and semantic keyboard controls and does not treat a successful direct desk rewrite as a painter round-trip. Foundations owns parser/scene probes; root owns prepared-action bridge and external liaison. The useful next proof is one small new component installed through the desk and then composed by a definition while bridge/painter hashes remain fixed. It should begin with that capability absent and expose an operation the old vocabulary cannot express; otherwise it is reuse, not extension evidence.
