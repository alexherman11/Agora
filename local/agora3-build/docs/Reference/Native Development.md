# Native development and the Linux workspace

**Agora reference documentation — from a request to a working capability.**
Version 0.1 (design specification). Companion to [[Agora Spec]] §2, §7, §12–16,
[[Objects and Facets]], [[Extensions]], [[Reconcilers]] and [[Security]].

> **Status.** Selected direction, awaiting implementation. The schemas, identifiers
> and SDK calls below are illustrative contracts, not existing APIs or successful
> demonstrations. [[Implementation Status]] is the evidence inventory.
>
> **Scope.** This document brings the VM, authored applications, full-shell editing
> and development feedback loop together. The established references still own
> object semantics, package declarations and authority; this is not another
> competing object model.

## Contents

1. [Start with a request](#1-start-with-a-request)
2. [A real computer and a protected native world](#2-a-real-computer-and-a-protected-native-world)
3. [Source, builds and installations](#3-source-builds-and-installations)
4. [Tools that remain after the view closes](#4-tools-that-remain-after-the-view-closes)
5. [The candidate loop](#5-the-candidate-loop)
6. [The whole shell, including chat](#6-the-whole-shell-including-chat)
7. [JEFF stays present while development runs](#7-jeff-stays-present-while-development-runs)
8. [Rebuilding and moving to another device](#8-rebuilding-and-moving-to-another-device)
9. [First runnable proofs](#9-first-runnable-proofs)
10. [Open decisions](#10-open-decisions)

---

## 1. Start with a request

> “JEFF, can you make it so I can click and drag the notes around?”

The request should not fail because the platform lacks a “draggable notes”
template. JEFF inspects the scene, its note appearances, and the installed lens.
He edits the lens's native source, builds a candidate, exercises real pointer
input, and activates the tested revision under the person's development delegation.

The note remains a note. Its content does not move between databases. Position
belongs to an appearance in the scene, not to the entity. Pointer motion stays
local; releasing the pointer commits the final placement through a native verb.

A second request — “now let me zoom with the wheel,” or “give yourself a tool to
arrange these” — changes authored code through the same runtime. It must not require
another special case in the host.

The useful split is **general mechanisms in the platform, application behavior in
native source**. Linux provides execution beyond the platform's current vocabulary.
Native packages make what JEFF builds inspectable, reusable and recoverable.

### 1.1 Creating the missing capability is ordinary development

JEFF's installed tool list is a starting point, not the ceiling of the environment.
When a needed action or observation is absent, JEFF can discover the available
execution surfaces, author an extension, exercise it, install it and invoke it in
the same conversation. This applies to development tools themselves: inspectors,
test drivers, diagnostics, dependency computations, package editors and skills.
Broad standing development delegation authorizes that loop without a new approval
for every locally invented tool. A missing permission or unavailable resource is
reported separately from a missing implementation.

Prefer editing native declarations, bindings and compositions where they express
the intent. A new executable behavior can instead be retained as package source
and an immutable artifact, edited through native operations. This is program
creation inside the world; it does not require JEFF to patch the Agora platform
repository. Ordinary guest files and guest runtime modifications remain an escape
path for experiments, with useful results captured back into packages or recipes.
No finite formula vocabulary is the final limit of authored behavior.

The bootstrap must therefore expose general native read/write, package authoring,
execution, installation and runtime discovery, together with access to the actual
guest resources permitted by the development delegation. An opaque runtime that
can neither be instrumented nor accessed through an authorized lower-level bridge
would recreate the capability ceiling. Missing new host authority still requires
the person's authority; minting a tool does not create that authority.

**Worked example: invent display inspection.** JEFF needs note dimensions, but no
installed action reports them. It inspects the authored view's source and runtime,
adds an adapter using that runtime's measurement facilities, binds measurements
to native appearance IDs, and installs `alex.display.inspect`. For an owned browser
view this could use element bounds and the view's coordinate transform; a canvas
view may need instrumentation of its drawing model. A separate renderer or legacy
application needs an accessible bridge or adapter, not a fictitious universal DOM.

The authored tool reports view identity, coordinate system, observation generation,
appearance IDs, bounds and missing/stale results. It validates its mapping with
actual input and visual evidence. It becomes discoverable and reusable without
restarting JEFF. Persisted measurements are attributed observations under an
admitted observer contract; they are not canonical geometry or new authority.
A closed view may require a measurement surface and cannot supply invented live
dimensions. These are requirements on the tool JEFF builds, not a requirement that
the platform ship a dedicated display-inspection tool before JEFF can proceed.

**Worked example: invent maintained relationships.** “Keep this note 24 units to
the right of that note” creates a native binding. “Make my total update when these
items change” uses the same dependency mechanism with different authored logic.
JEFF can mint the facet definitions, transformations, installation and editing
actions. [[Objects and Facets]] §3.9 owns their value and dependency contract;
[[Reconcilers]] §10.1 distinguishes pure derivation from maintained effects.
Neither example should require a new domain-specific verb in the protected host.

## 2. A real computer and a protected native world

Agora runs over stock Linux. It does not need a new kernel or its own drivers.
The Linux guest is a real working computer: files, packages, processes, terminals,
browsers and conventional applications. The person may give JEFF root there.

The canonical native world is served outside that guest's root authority:

```text
person ── ordinary conversation / authored shell ── JEFF and native applications
  │                                                     │
  │ independent recovery                               │ authenticated requests
  ▼                                                     ▼
protected host: supervisor + world gateway + keep + declared resource brokers
  │                     │                         │
  │ guest lifecycle     │ event log / payloads     │ current authority / receipts
  ▼                     │                         │
Linux guest: root-capable development workspace, clients and execution
```

This is a placement decision with consequences. The host can preserve native
history and deny a guest permission to change external delegation. It cannot
make every process inside a root-capable guest mutually isolated. [[Security]] §3
defines what the broad profile exposes.

### 2.1 Where each kind of state lives

| State | Authority | How it returns |
|---|---|---|
| Entity/facet revisions, package source, scene placements, installation choices | Protected native history plus retained payloads | Replay recorded changes |
| Current grants, revocations, consumed approvals, external receipts | Keep, outside world rollback | Retain current policy; issue fresh session authority |
| JEFF's retained memories and lessons | Separately versioned witness records, subject to erasure | Survive a world rollback without becoming authority |
| OS packages, service setup and environment configuration | Versioned machine recipe and captured inputs | Rebuild a compatible guest |
| Guest files and legacy application data | Filesystem/resource contract | Retained artifacts or a consistent backup |
| Processes, devices and connections | Live machine or external system | Reobserve, then apply explicit resume policy |
| Pointer motion, animation and uncommitted gesture state | Current view | Usually discarded; not replayed |
| VM checkpoint | Supervisor | Restore captured machine state, then reconnect to current authority |

A native log is not a transcript capable of reconstructing every shell command's
effects. A guest command can edit a file without an adapter understanding the edit.
Record the request and observed outcome honestly, then capture useful work as
source, an artifact or a machine recipe.

### 2.2 Restoration is coordinated, not magical

Restoring a VM checkpoint does not implicitly rewind the native world. The restored
guest reconnects against the selected world branch and the host's current execution
epoch. Stale writes, old leases and duplicate invocations are refused or revalidated.

Restoring a native branch reconstructs its recorded state without executing code.
It does not repeat a send, rejoin a call, or retry an uncertain deployment. Current
revocations and known external outcomes remain in the keep. Reinstalling old code
is different again: it requires compatibility with current data or a separately
authorized data migration.

## 3. Source, builds and installations

Use the [[Extensions|extension package]], not a parallel “program object” universe.
Source files, UI entry points, callable handlers, assets, schemas, skills and tests
are optional parts of that package. Small packages stay small.

The version chain should be visible:

```text
alex.notes-board                  stable package identity
  source revision 12              board.js, actions.js, board.css
    build b7                      source r12 + locked dependencies + toolchain
      artifact sha256:…           immutable executable output
        desk-board installation r3
          view instance board-1   bindings + view state
          arrange invocation j8   pinned installation r3, independent of view
```

Source edits use an expected revision. File paths are package-relative; “patch
board.js” is not permission to patch the host filesystem. Large source/assets may
use retained blobs. Export includes the bytes it promises, not just hashes whose
only copy was in a deleted build directory.

Builds resolve dependencies to an explicit lock and retain provenance. The first
dependency graph can be acyclic and reject ambiguity. Runtime contracts name
language/bridge versions and resource assumptions. A recorded dependency hash
does not prove a hermetic build; uncaptured environment inputs must be reported.

A proposed installation record:

```yaml
desk_board:
  installation.spec:
    package: alex.notes-board
    source_revision: 12
    artifact: build-b7
    dependency_lock: lock-4
    runtime_contract: browser-contract-1
    ui:
      mount: shell.desk
      entry: board
      bindings:
        notes: query-notes-in-desk
    actions: [alex.notes-board.arrange]
    state: board-state-1
  installation.status:
    concerns: installation.spec@3
    observer: package-runtime
    incarnation: guest-9/runtime-2
    state: running
    observed_at: "2026-09-06T18:00:00Z"
    fresh_until: "2026-09-06T18:00:30Z"
    evidence: [startup-receipt-41]
```

Activation changes the desired installation and registry atomically in native
state. Startup is observed afterward. “Installed” is not proof that its process
is healthy. Services follow the maintained-intent contract in [[Reconcilers]].

Application data, installation configuration, per-view state and per-person
overlays have different owners. Closing a view deletes none of its subjects.
Uninstalling disables new invocations and handles running work and dependents
explicitly; data retention is a separate decision.

## 4. Tools that remain after the view closes

The package's `arrange` action is registered by installation, not by mounting the
lens. It has typed arguments and results, declared effect semantics and a headless
entry point ([[Extensions]] §2.2). JEFF can call it after every board view closes.

A proposed handler, showing the relevant boundaries:

```javascript
export async function arrange({ columns }, context) {
  const result = await context.query({
    scope: { scene: context.subject },
    require_facets: ["core.text"],
    result: "appearances",
    order: [{ field: "appearance.id", direction: "asc" }],
    limit: 200,
  });
  if (!result.complete) {
    throw new Error("Choose a smaller scope or use the paginated arrangement tool.");
  }
  const placements = result.items.map((item, index) => ({
    appearance: item.appearance_id,
    x: (index % columns) * 260,
    y: Math.floor(index / columns) * 180,
  }));
  await context.invoke("scene.place_many", {
    expected_scene_revision: result.scope_revision,
    placements,
  });
  return { moved: placements.length };
}
```

The runtime validates `columns` against the action schema before dispatch.
The fixed spacing here only illustrates action invocation. It does not establish
that notes fit or that the result is a good layout. JEFF can author measurement
and arrangement tools (§1.1); a maintained relationship uses a binding rather than
repeatedly overwriting placements (§4.2).
The scene operation validates target identities and the expected scene revision
before committing. This is an illustrative bounded handler, not a required host
implementation of “arrange.”

Installed tools can call other installed tools. Resolve and pin the called
installation version; preserve caller/delegation and invocation ancestry. Track
resource budget and call depth so a tool cannot multiply its authority or create
unbounded recursion by calling itself through another package.

The registry has a revision. JEFF refreshes discovery during its session, and
invocation checks that the requested contract still exists. If a package has several installations, a call identifies the intended installation; an ambiguous alias is refused. New capability should
not require a new model conversation. A model adapter can expose generic discovery
and invocation operations while keeping Agora in control of the tool loop.

### 4.1 What a live view binds to

`query-notes-in-desk` is the saved query in [[Objects and Facets]] §6.1. It follows
notes added later. It does not bake today's note IDs into source code.

Code dependencies are pinned; data can be live. Those are different policies.
A new note appearing in a live query does not mean the package source changed,
and should not by itself invalidate an otherwise compatible candidate.

### 4.2 Native bindings and authored computation

An installed transformation is callable independently of a view. Binding an input
facet to its output makes the computation persistent, with a declared resumption
policy and visible dependency state. The package contains its implementation;
the binding contains the person's chosen inputs, parameters and target. Changing
an offset edits native data. Inventing a new transformation uses the package loop.

A read exposes the binding and its effective value together, including dependency
revisions, producer version and readiness. JEFF can inspect why a value has its
current value and change, pause, replace or detach the relationship through native
actions. A failed computation stays inspectable and does not silently turn into
a literal value. Closing the view does not delete the relationship. Computation
that needs a live display reports unavailable inputs when that display is absent.

Start with explicit dependencies and acyclic graphs. General guest execution is
the extensibility path for new evaluators and adapters; it does not move arbitrary
code into the protected gateway. Build the reusable scheduling, invalidation and
binding mechanisms as foundations, rather than implementing a separate host rule
for relative placement, totals or any other requested relationship.

## 5. The candidate loop

Source access alone is insufficient. JEFF needs build errors, runtime stack traces,
logs, screenshots, interface inspection and actual browser interaction.

```text
inspect → edit source → build → exercise candidate → inspect evidence
               ↑                            │
               └──────── fix/debug ─────────┘
                                            ↓
                           activate exact artifact → observe health
```

A candidate describes what was tested:

```json
{
  "candidate": "candidate-18",
  "package": "alex.notes-board",
  "source_revision": 12,
  "artifact": "build-b7",
  "dependency_lock": "lock-4",
  "base_installation_revision": 2,
  "test_world": "candidate-world-18",
  "execution_environment": "yard-6",
  "evidence": ["build-log-7", "drag-trace-9", "screenshot-12"],
  "checks": {
    "pointer_drag": "passed",
    "placement_survives_reload": "passed",
    "new_note_appears": "passed",
    "closed_view_action": "passed"
  }
}
```

This example shows the intended evidence format; no such run has happened yet.
Evidence is bound to source, dependencies and environment. A native world fork
isolates native test data; a disposable guest is needed when tests change machine
files or processes. External effects need explicit test capabilities and disclosed
limits. Do not label a live network test “disposable” merely because its UI is.

### 5.1 The dragging acceptance exercise

| Step | Expected observation |
|---|---|
| Press on appearance `a17` at scene position (40, 30) | Capture target identity, starting transform and current revision |
| Move the pointer | Local preview follows; no durable write per motion frame |
| Release at scene position (240, 130) | One authorized placement commits the final scene coordinates |
| Reload the lens | `a17` renders at the committed position; note text is unchanged |
| Another editor moved `a17` during the gesture | Reject the stale commit or apply an explicit rebase policy; no silent overwrite |
| Cancel the gesture or lose the surface | Preview is discarded; no stray final placement |
| Add a note after installation | It appears through the query, without a source patch |

Wheel zoom is a separate follow-up using the same browser runtime. Test actual
wheel input, focus and pointer-to-scene coordinate conversion, not just a called
JavaScript handler.

### 5.2 Activation and failure

Activation checks the candidate's artifact, current installation revision and any
declared data preconditions. If JEFF or the person changed the installation during
the build, return a stale-candidate result. Rebase and test the affected behavior;
do not overwrite newer work.

A failed build leaves the working installation selected. A failed startup remains
visible and can fall back to the previous compatible installation. Track listeners,
subscriptions and invocation IDs so replacement does not duplicate work.

The person's request or broad standing delegation can authorize routine activation.
Data migrations and new external authority still follow their own contracts.
Recovery must explain which part it restores: code, native data or machine state.

## 6. The whole shell, including chat

Chat is not permanently privileged application chrome. The desk, navigation,
message list, composer, inspectors, styles and interaction modules are native
packages the person and JEFF can change.

The durable conversation is independent of its rendering:

```yaml
conversation_5:
  messages: ordered references with authorship and content revisions
  tasks: [development_task_8]
draft_12:
  conversation: conversation_5
  author: alex
  body_revision: 4
  retention: person-selected
chat_view_2:
  conversation: conversation_5
  draft: draft_12
  installation: chat-package@7
model_activity_3:
  conversation: conversation_5
  incarnation: session-31
  state: streaming
  transport_ref: opaque-host-reference
```

“Move chat to the bottom and make the composer wider” edits the view and its
placement. Replacing that view must preserve messages, the current retained draft
and the connection to active work. It must not start another model run or replay
previous tool calls. Opaque transport state and credentials are not editable
conversation facets.

The protected host retains stop, delegation control and restoration of a known
working shell. Those controls remain usable if authored code loops, crashes or
hides its own buttons. A browser sandbox alone is not a CPU scheduling guarantee.

### 6.1 Skills and agent behavior

Skills are versioned procedures with source, examples and tool references:

```yaml
skill:
  id: alex.native-development
  instructions: package-source:skills/develop.md@6
  examples: [case-dragging, case-review-board]
  requires: [package.inspect, package.patch, candidate.build, candidate.exercise]
  scope: explicit-development-tasks
```

Installing a skill changes JEFF's procedural context at a defined boundary.
Reading a note, tool result or web page does not install it as instructions.
Ongoing tasks retain their selected skill revision unless deliberately updated.

JEFF may improve skills, routing, tool preferences and guest-side agent behavior
through native source. A skill cannot grant permission or alter the host's
authentication and recovery boundary.

### 6.2 Authored memory and a growing working collection

These are different user experiences, both authorable through native packages.
Neither requires a dedicated platform implementation of the example application.

**“JEFF, remember this.”** JEFF can build a small memory package with operations
to remember, find, inspect, correct and forget a claim. An illustrative record is:

```yaml
memory_7:
  claim: Alex prefers the music queue in a narrow left sidebar.
  source: conversation_5/message_42
  basis: explicit-request
  revision: 1
  state: active
  scope: alex-private
```

The package persists the record through authorized native operations in the
separately retained witness domain (§2.1), then confirms what it saved. Generic
record storage and authorized retrieval must exist there; the model cannot create
a new retention domain simply by naming a facet. JEFF authors the memory schema,
indexing, retrieval policy and tools on top of that foundation. A plain collection
and text lookup are a valid first implementation; a sophisticated memory graph or
embedding service is not required to remember an explicitly requested fact.

Storage alone does not fulfill remembering. The authored guest-side context
assembly can invoke a bounded retrieval operation at a defined turn boundary,
or JEFF can explicitly search memory when relevant. Retrieved claims retain their
source and correction state, enter context as data, and do not become system
instructions. JEFF can improve that retrieval behavior through the same package
loop. Test recall in a fresh conversation without supplying the earlier transcript.
Correction must supersede the old claim; forgetting must cover the package's
retained content and indexes under the erasure contract. A memory projection is
not a second independently writable record. A successful write is confirmed only
after persistence, not because JEFF expressed an intention to remember.

**“Create a list called AlexBench; I'll add benchmark questions over time.”** This
is a persistent work product in the ordinary native world, distinct from witness
memory and from transient model context. It requires no open view or running
background model. A minimal proposed shape is:

```yaml
alexbench:
  name: AlexBench
  entries:
    - id: entry_1
      subject: question_1
question_1:
  text: Can you identify the contradictory assumptions in this argument?
  source: conversation_8/message_14
  revision: 1
```

JEFF may initially use existing text and collection facets, then introduce an
application schema if categories, expected answers or rubrics become useful.
“Add this to AlexBench” resolves the existing collection and appends an identified
entry through its native action, even when the view is closed or in a later
conversation. Ambiguous collection names need resolution; matching a name is not
permission to mint a duplicate. Edits address entry/question identities and use
the ordinary stale-write rules. Creating the list does not start benchmark runs.

Calling it a working file is natural. A text/Markdown export or file view can
represent the collection; choose one authoritative representation and route
edits through it rather than keeping an unrelated file and collection in sync by
guesswork. The person can open, edit, reorder and export the work without JEFF.
Remembering that Alex uses AlexBench may create a memory reference to the
collection; it should not copy all benchmark questions into personal memory.
Restoring an older world can change the collection while retained memories about
it remain historical claims; references and retrieval must expose that distinction.

**Acceptance.** With the domain tools initially absent, JEFF authors the packages,
saves and recalls a requested fact across conversations, corrects and forgets it,
then creates AlexBench and appends questions over several conversations with its
view closed. Reopening shows the accumulated work without duplicates or lost
edits. A smaller agent can use the resulting documented actions with ordinary
world context and invocation permission, without source access or development
privileges. The person authors JEFF's system prompt; this example specifies
capabilities, not replacement system-prompt text.

### 6.3 An authored music application that becomes a sidebar

**Request.** “Make my Spotify view a skinny list on the left: current track,
upcoming songs and the current playlist.” Spotify is the desired example provider,
not an assertion that its integration already exists or exposes every operation.
JEFF, or another authorized agent, should be able to build the native application
and then make this change through its package and native view configuration.

The application has separate parts that can evolve independently:

| Part | Native meaning |
|---|---|
| Recording | Media identity and metadata, with provider bindings. |
| Playlist | Ordered entry identities referencing recordings. |
| Playback session | Current recording, output and observed playback state. |
| Upcoming queue | Ordered upcoming occurrences; distinct from the playlist that supplied some of them. |
| Adapter and actions | Observes the provider and exposes the operations actually supported by the authorized integration. |
| Lens and placement | Presentation, controls, width, docking and selection; editable without replacing the media subjects. |

The existing music example in [[Objects and Facets]] Appendix A and [[The Web]] §5
owns identity and remote-observation semantics. A recording may occur twice; moving
one queue occurrence must not move both. If the provider cannot distinguish
occurrences reliably, the adapter must report the limitation rather than invent
stable editable identities. A local queue model is possible, but is not silently
presented as the provider's authoritative queue. Current playlist context may be
unavailable; it must not be guessed from a track's membership in some playlist.

If a compact lens or docking tool is missing, JEFF authors it. If changing width
and visible fields suffices, it edits configuration rather than source. The result
is an installed Agora application revision or view setting, not a one-off image
or a modification of an unrelated vendor window. Track/queue data and playback
remain independent of the view. Changing the layout must not restart playback,
reset the queue, duplicate subscriptions, or lose the person's selection.

The application should have a clear current-track area, legible track/artist rows,
an upcoming section, and playlist context when available. Narrow width must not
make controls unclickable or hide how to reveal a long title. Docking reserves or
explicitly overlays workspace space according to the chosen shell behavior; it
must not accidentally cover chat or steal keyboard focus. Expansion, resizing and
undocking remain ordinary controls. Styles and layout conventions may be reusable
native assets, but the application can introduce its own rendering and interaction.

Test with a clearly labeled local provider fixture first: duplicate tracks, long
titles, empty/loading/disconnected states, updates during use and multiple view
sizes. Then verify the actual provider's current API, account authorization and
supported operations when integrating it. Fixture success is not Spotify success.
Detailed external-effect uncertainty remains deferred (§9); these examples do not
make it a prerequisite for native application development.

### 6.4 Malleability must preserve design quality

A native application is a coherent product, not merely a generic facet editor.
Customizability must preserve legibility, hierarchy, discoverability and efficient
ordinary use. The person should not need to understand facets to use AlexBench,
read remembered claims, or control the music view.

Candidate acceptance includes keyboard operation, focus continuity, accessible
names, usable targets, content overflow, responsive layouts and honest empty,
loading and error states. Exercise real input and inspect rendered results at
representative sizes; schema validation and a screenshot alone cannot establish
usability. Replacement views preserve relevant data, drafts, selection and activity
under declared lifecycle contracts. The person can recover the prior presentation
without silently restoring old application data.

JEFF should turn repeated development work into reusable actions, templates,
bindings, design assets and concise skills, while retaining an executable path for
new behavior. Evaluate an improvement by how easily the next agent or person uses
it. Fewer source edits help only if the resulting interface is clearer. A smaller
agent should need the tool contract and examples, not the implementation or a
transcript of how the stronger agent built it. Good defaults and reusable design
assets support quality; they must not become a fixed catalog that blocks invention.

## 7. JEFF stays present while development runs

The long-term workflow delegates coding to another agent. Conversational JEFF
owns the person's intent and remains available while the worker builds, inspects
results, debugs and tests. Worker model choice is configurable and evaluated for
that role; GPT-4 was suggested as a candidate, not selected as a hard dependency.

A task is a native subject, not a promise buried in the model's context:

```yaml
development_task_8:
  task.spec:
    brief: Let me group notes by review state, while keeping drag placement
    owner: jeff-for-alex
    package: alex.notes-board
    base_revision: 12
    acceptance: [existing-drag-still-works, review-groups-live, no-chat-draft-loss]
    candidate_world: yard-world-8
    delegation_ref: task-grant-8
    budget: {wall_time_seconds: 900, max_parallel_jobs: 2}
    cancel_generation: 0
  task.status:
    concerns: task.spec@1
    observer: work-manager
    incarnation: worker-run-8
    state: testing
    progress: Grouping works; checking drag behavior across groups
    candidate: candidate-19
    evidence: [build-log-8, interaction-trace-10]
```

JEFF can answer another question, accept a clarification or cancel the task.
A changed brief gets a new revision; a cancelled or outdated result cannot quietly
activate. Concurrent workers need separate candidate workspaces and explicit
conflict resolution.

The worker returns source changes, an artifact, evidence and unresolved problems.
JEFF adopts it within current delegation or explains what remains missing. A
separate worker does not need to be implemented now: first build durable jobs,
progress, cancellation and reconnection so asynchronous work is not tied to a
single model turn.

## 8. Rebuilding and moving to another device

A package becomes durable when it can work without its author's memory of how
it was assembled. Capture source, dependency locks, retained artifacts and the
machine recipe. Guest-root experiments are welcome; undocumented manual installs
are a reproducibility limit to expose and then reduce.

A world export and a VM image are different artifacts. Export native subjects and
selected history, source and promised payloads. Retain a recipe and optional
checkpoints for the execution environment. Credentials, current grants and
external-effect replay are excluded.

Not every device needs a full VM. A small device may provide a browser surface
while a compatible machine hosts execution. Make latency, disconnected operation,
unsupported resources and computation placement explicit. An offline view can
retain drafts or proposals without pretending it can use an expired grant.

Room installation follows the room's authority, not the author's guest-root
profile. Sharing a tool offers source and behavior; sharing data is a separate
decision. The full social vision remains in [[Rooms]], [[Democracy]] and
[[Ownership]], with technical obligations in the references.

The initial model adapter should retain the person's requested Astra/OpenAI
account path and Agora-controlled tools/loop. Supported SDK and authentication
transport must be demonstrated, not inferred from having an account. Do not
silently replace that path with another billing mode or copy tokens into images.

## 9. First runnable proofs

These are immediate dependencies, not a complete product schedule:

**Deferred for now:** external-effect uncertainty infrastructure, including durable
delivery receipts, provider deduplication and uncertain-outcome recovery. It is not
a prerequisite for the capability-creation exercises below. Focus current work on
JEFF authoring tools, native bindings, executable packages and the programmable
environment. The external-effect reference contracts remain future design; this
deferral does not imply delivery guarantees or change the rule that replay never
executes actions.

1. **Protected native world.** Minimal identities, facets, revisions, verbs,
   retained payloads and inspection. Prove replay, refusal atomicity and restart.
2. **Linux workspace.** Select a hypervisor/image through a local prototype.
   Prove guest administration, authenticated native edits, revocation, independent
   recovery and reconstruction from a versioned machine recipe.
3. **Native development.** Implement one package/runtime contract, application
   schema admission, live queries, a persistent action registry and candidate
   feedback, plus native bindings and dependency evaluation. Run the dragging
   example and the capability-creation exercises below.
4. **Programmable daily shell.** Move desk and chat onto that same application
   runtime. Replace chat while preserving a draft and ongoing work; demonstrate
   recovery from a broken candidate.

Capability-creation acceptance must begin with the relevant domain tools absent:

- Ask JEFF to inspect the display. It authors and installs the missing adapter,
  uses it successfully, and reuses it in the same session without a host patch.
- Ask for B's placement to follow A plus an offset. JEFF installs an authored
  transformation and native binding. Moving A updates B without another model
  call; changing the offset, manual dragging, closure/reopen and restart honor the
  binding contract. Missing input, stale evaluation and a cycle are visible.
- Ask for an unrelated computation, such as a total over application-defined
  amount facets. JEFF mints its definition and computation through the same path.
  The host contains no special case for notes, relative placement or totals.
- Have JEFF revise one of its own installed tools and its associated skill. The
  revised capability is discoverable mid-session; failed or stale activation
  preserves the previous installation. Retained source and bindings are editable
  and recoverable through Agora, without opening the platform repository.

These are tests of general extensibility, not a requirement to ship these tools
as built-ins. Domain success requires real execution and model evidence.

The memory, AlexBench and music-application examples (§6.2–6.4) are concrete
acceptance targets as the relevant slices arrive, not a requirement to build every
application before the foundation is useful. A technically functioning but awkward
interface does not satisfy their product-quality target.

Detailed distributed governance, every broker class and multi-agent scheduling
are not prerequisites for these proofs. [[Agora Spec]] §22 retains the unordered
feature horizon: everyday computing, JEFF's continuity, social spaces, devices,
ownership and distribution.

## 10. Open decisions

- Which Linux image, hypervisor and recipe make rebuilding practical on the
  development machine?
- Which browser/headless runtime and bridge provide expressive UI and durable
  tools with the smallest trusted host surface?
- What artifacts and test evidence must be retained, and for how long?
- How do view upgrades, data migrations and long-running invocations coexist?
- What can the broad development profile honestly enforce, and when do shared
  packages require separate isolation?
- How much build/candidate ceremony can be generated so a small customization
  still feels immediate?
- Which model/authentication adapter supports the requested account path while
  keeping capabilities discoverable during the session?

Resolve these with running examples. The architecture succeeds when JEFF can
introduce a useful capability and the person can inspect, revise, keep and recover
it without returning to the platform repository for each new interaction.
