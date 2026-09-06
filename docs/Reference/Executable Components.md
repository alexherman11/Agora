# Executable Components

**Implemented local prototype contract — September 5, 2026.** Companion to
[[Personal Lenses]], [[Extensions]], and [[Agora Spec]] §22. The person approved
executable authorship after clarifying that inventing unanticipated abilities
during use is essential to Agora. A fixed vocabulary of view templates cannot
fulfill that intention by itself.

## What the first slice enables

JEFF can write JavaScript as an object's `core.component` facet, exercise it in
a disposable candidate world, and activate its exact definition revision. The
program computes a view and handles interactions; it can request changes to
explicitly bound objects and retain its own state. Named actions become tools in
the existing JEFF conversation. The platform supplies a small set of primitives,
while the program supplies the behavior. Dragging is an acceptance example, not
a built-in operation or an authored program shipped to JEFF as a template.

The existing declarative lens remains useful for simple list/detail views.
Executable components cover behaviors that those templates cannot express.
This version occupies the workspace; the conversation panel is still shell code.

## Definition and execution contract

`core.component` contains `version: 1`, `title`, `source`, `bindings`,
`permissions`, `state_schema`, `initial_state`, and `actions`. The source is a
single JavaScript object expression:

```javascript
({
  render(ctx) { /* return a tree */ },
  handle(ctx, event) { /* return proposed local/state/effects */ },
  actions: { /* manifest-declared functions (ctx, args) */ }
})
```

The context contains `objects`, `state`, `local`, and `viewport`. `objects` maps
actual entity IDs to `{entity, facets: {type: {body, revision, written_by}}}`.
Only declared bindings are included. Readable types currently are `core.name`,
`core.text`, and `core.scene`; text storage snapshots are omitted. Scene bodies
contain their appearances, including references to other objects. Binding a scene
therefore exposes those references, but does not grant reads of their facets.

`local` starts as `{}` and lasts only through the interaction session. Initialize
its individual optional fields, rather than relying on `ctx.local || defaults`.
`render` is pure: mutating its context does not save state. Saved scene positions
must remain the default when drawing objects after reload or external changes.

A tree has unique node IDs, tags, and optional text, value, label, entity,
children, styles, and event-handler names. The supported tags are `div`, `span`,
`p`, `button`, `h1`, `h2`, `h3`, `pre`, `label`, `input`, and `textarea`. Styles
are validated strings from the property allowlist in `component_tree.py`.
Raw HTML, executable attributes, resource URLs, and fixed/sticky positioning are
refused. The trusted shell creates DOM nodes and forwards input; generated code
never runs in the browser or receives the DOM, session token, or conversation.

`handle` and named actions return `{local?, state?, effects?, selected?, value?}`.
Inputs include the rendered node ID, event type, handler, and bound entity;
pointer coordinates are relative to the workspace. The host resolves the handler
and entity from the current tree, rather than trusting caller-supplied claims.
Pointer capture keeps a gesture targeted at its original handler node.

Supported inputs are click, pointerdown/move/up/cancel, keydown, input, and change.
Pointer motion may update `local` but cannot produce durable effects or state.
Commit a drag on release and discard it on cancellation. Other authored programs
must also keep high-frequency input transient; a general input batching facility
is not yet implemented.

## Real authority at the component boundary

Bindings map entity IDs to readable facet arrays. Permissions can authorize:

- `place: {scene, entities}` for a bound scene and specified bound objects.
- `attach: {entity: [facet_type]}` for explicitly readable name/text facets.
- `state: true` for the component's own persistent state.

Effects may only request those operations with validated arguments. They cannot
mint objects, change permissions or display admission, import files, supply CRDT
snapshots, claim an actor, or call arbitrary verbs. The complete batch and its
resulting render are checked before one `component-committed` event is appended
through the verb gateway. A failed batch leaves no partial placement or state.
The event attributes execution to `component:<entity>@<revision>`, records the
requesting caller, and pins source provenance. Replay applies recorded facts;
it never reruns executable source.

`core.component-state`, `core.component-test`, and `core.component-admission`
are runtime-owned facets. Ordinary mint/attach cannot manufacture them. State
schemas declare an exact set of required fields with primitive JSON types.
Definition changes and restoration must be compatible with existing state;
there is no implicit reset or migration. Restoration restores code, not earlier
data or effects. Explicit state migration remains future work.

This enforcement is a local component boundary, not the full multi-user grant
system described in [[Security]]. The operator and JEFF can author local
manifests; the general authority hooks remain stubs. Remote users, institutional
admission, and hostile host processes are outside this implementation's claims.

## Candidate testing, activation, and recovery

The public operations are `component_view`, `test_component`,
`activate_component`, `component_event`, `component_actions`, `invoke_component`,
`open_component_candidate`, `candidate_event`, and `close_component_candidate`.
They are registered verbs available through the same CLI and JEFF tool derivation
as the rest of the world. Input schemas are derived from facet definitions;
new active action tools are derived from the manifest on every model step.
JEFF retains a simple finite loop: at most 24 model steps per turn and 8192
output tokens per model response, with the existing stop and timeout behavior.

`test_component` copies a stable event log to a temporary world, runs 1–24
sequential event/action cases, and checks explicit observations: rendered text or
nodes (recursive matching of requested fields), placement, persistent state, effect count, or returned value. Only passing
cases produce a protected receipt in the source world. The receipt binds the
complete definition and its current input fingerprint. Tests authored by JEFF
are evidence of their assertions, not independent proof that the user got a good
interface; human interaction and additional regression cases still matter.

Interactive previews use separate disposable worlds, bound to the calling actor
and source world. At most eight sessions are retained, with a five-minute idle
expiry. Closing a preview discards its placements and state. Preview edits are
never merged into the live world by activation.

First activation requires a matching test receipt, exact source revision, and a
precondition on the current display revision. Changed bound inputs invalidate the
receipt. Draft edits do not replace active code. `core.display` records
`{lens: component_id, revision, kind: "component"}`; the existing field name is
retained for additive compatibility. Previously admitted definitions can be
restored if their bindings and current state remain valid. Stale interaction
fingerprints and calls to an inactive component are refused.

Stop, Default desk, and restoration controls remain outside generated views.
Stop prevents further queued interactions; a request already being processed may
complete. The interpreter's deadlines bound a failed invocation. Active views
and owned state survive server restart and operate without the model. Only the
active component's actions are currently advertised to JEFF; a general installed
capability registry and simultaneous component composition remain future work.

## Runtime limits and deployment scope

The interpreter is [quickjs-ng 0.16.2.1](https://pypi.org/project/quickjs-ng/0.16.2.1/)
in a separate Python process. Each request creates a fresh JavaScript context,
with no host callbacks, filesystem/network API, packages, timers, or credentials.
The subprocess receives a minimal environment, not model-provider secrets.

Limits currently include 32 MiB interpreter memory, 512 KiB stack, 150 ms CPU per
evaluation, a two-second response deadline, 100,000 source characters, 64 bound
objects, 500 tree nodes, depth 20, 64 effects per interaction, and 32,000-character
JSON local/owned state. Input/output limits are 1.5 million/500,000 characters.
These are experimental defaults, not performance targets for all future devices.

This is interpreter isolation, **not an OS sandbox against native engine
vulnerabilities**. The subprocess is not placed in a container or restricted OS
account. Rendering is constrained and clipped but not a proof against every
browser resource-exhaustion pattern. UI events currently round-trip to the local
server; remote latency and high-frequency animation need a different execution
placement experiment. The source can compute new behavior, but its available
effects remain deliberately finite.

The broader vision includes full display composition, conversation UI,
dependencies, background work, additional object operations, external adapters,
shared tools, and portable/offline execution. Expand those capabilities with
their own authority, cancellation, compatibility, and distribution contracts
when useful experiments require them; they are not a fixed build sequence.

## Evidence

`tests/test_components.py` exercises replay, batch refusal, scoped effects,
candidate isolation, stale activation, retained definitions, interpreter failure,
and action discovery within a running JEFF turn. Browser and real-provider
results, including failed authoring attempts, belong in
[[executable-component-validation-2026-09-05]]. A scripted program demonstrates
runtime capability; only an actual model trial demonstrates that JEFF authored it.
