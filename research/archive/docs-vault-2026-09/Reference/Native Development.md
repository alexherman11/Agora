# Native development and the Linux workspace

**Agora reference documentation — from a request to a working capability.**
Restored design reference, revised September 10, 2026. Companion to [[Agora Spec]] §2, §7, §12–16,
[[Objects and Facets]], [[Extensions]], [[Reconcilers]] and [[Security]].

> **Status.** A substantial local slice is implemented: protected native state,
> retained packages, browser and Python execution, a main Linux development VM,
> an authority-free resettable candidate VM, an authored shell, managed JEFF
> adapter, installed actions and live JEFF-authored dragging. The YAML/JSON and
> handler APIs below remain illustrative unless [[Runtime Guide]] names them.
> [[Implementation Status]] separates recorded demonstrations from future design.
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
9. [What is proved and what remains](#9-what-is-proved-and-what-remains)
10. [Open decisions](#10-open-decisions)

---

## 0. Current implementation

Agora3's protected service owns the native event journal, derived cache, package
receipts, current authority and independent recovery. The Linux workspace supplies
general root-capable development execution. Installed browser entries run in an
authored frame; installed Python actions run in the guest; a separate resettable
candidate VM has no live native bridge. Source, build and installation are distinct
retained identities. Editing source does not activate it, and restoring package
code does not rewind note data.

The current system uses whole-package source replacement, self-contained browser
HTML, bounded paginated reads and object-level revisions. Its Python action input
is a broad snapshot capped at 1,000 objects. Queries are not subscriptions, and
general modules/dependency loading is absent. These are measured properties of one
working slice, not permanent design laws. Exact operations and dated limitations
live in [[Runtime Guide]] and [[Implementation Status]].

The detailed workflow below preserves the larger design that motivated that slice.
Where it proposes richer schemas, workers, live bindings, build locks or device
portability, it is a direction to test rather than a hidden claim about current code.

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

This example shows a richer evidence format than the current API. Corresponding
work has now happened: real account-backed JEFF authored, exercised and installed
a counter package; later it authored dragging, and independent real pointer input
verified persistence, editing and draft continuity. Those runs used the concrete
receipts described in [[Implementation Status]], not the illustrative identifiers
above. Evidence should stay bound to the source, environment and behavior actually
tested. A native world copy isolates native data; a resettable guest is needed when
tests change machine files or processes. External effects need explicit test
capabilities and disclosed limits. A live network test is not disposable merely
because its UI is.

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

### 5.3 Measured current friction

Current friction is concrete. Each row is a direction worth testing, not a mandate
for every future implementation:

| Current mechanism | Useful direction to test |
|---|---|
| Whole-package `package.save` | Revision-aware file reads, search and surgical edits; fewer repeated source bytes. |
| Self-contained HTML browser entry | Retained assets, modules or component reuse when an application needs them. |
| Separate Python-action and browser execution paths | Shared contracts or evaluators where useful, without requiring one universal runtime. |
| Actions snapshot at most 1,000 world objects | Declared scoped inputs and relevant dependency guards. |
| Object-level stale-write checks | Targeted or finer conflict scopes when content and presentation contend. |
| Polling and paginated queries | Bounded invalidation or subscriptions justified by actual use. |
| Appearance attached to note subjects | Adapters and independent uses with an explicit compatibility path. |
| Correct native actions but fragile human plumbing | Shared registry adapters and rendered-state inspection; test actual human controls. |

Stable named surface parts and reusable native UI clients could reduce repeated DOM
work. Preview should expose real effective values, not merely validate data. The
presentation experiment found duplicated evaluator updates and a broken human
registry path even when JEFF's action path worked; [[Presentation and Operators]]
retains the evidence and narrower declarative direction.

### 5.4 Comparative development

Start a candidate from the accepted baseline, compare both on the same application
task, and carry forward the better verified result. Record correctness before
speed, complete versus partial outcomes, model/tool time, source traffic, failures
and repair effort. Keep preparation separate from timed use, and freeze task and
check definitions before execution.

Human and agent checks remain distinct. In the September 9 presentation experiment,
both agent paths completed nine matched requests, while human testing found
selection loss, a registry lookup failure and a limited preview. The later repair
build fixed those findings; it did not rewrite the measured run. One trajectory per
variant is useful evidence, not a statistical benchmark. Include requests beyond a
candidate's prepared vocabulary and preserve ties, rejected candidates and failed
harness routes rather than manufacturing a win.

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

## 7. JEFF stays present while development runs

The current runtime has one foreground JEFF turn. A useful future workflow may
delegate coding to another agent so conversational JEFF can remain available while
work builds and tests, but this is not the only topology and is not implemented as
durable background work today. Workers may be stateful, temporary, deterministic
or model-driven. Choose their model and lifetime from measured responsiveness,
continuity and cost rather than fixing one architecture in advance.

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

When a worker is used, it returns source changes, an artifact, evidence and
unresolved problems. JEFF adopts it within current delegation or explains what
remains missing. Durable jobs, progress, cancellation and reconnection should be
proved before claiming that asynchronous work survives a model turn. Stopping the
current foreground turn rejects later callbacks but does not undo completed native
changes or terminate every independent guest process.

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

The current managed path uses the official Codex SDK with ChatGPT-account sign-in;
Agora owns native dispatch, cancellation and budgets while the SDK owns its inner
inference loop. Its compiled runtime inventory has been tested separately from a
real account-backed authoring run. Do not extract OAuth tokens or silently replace
the requested account path with API-key billing. The Agents SDK/API-key adapter
remains an alternative with a different loop contract, not evidence about the
managed path.

## 9. What is proved and what remains

The initial vertical slice now has recorded evidence, with important limits:

| Area | Recorded proof | Not established by that proof |
|---|---|---|
| Protected native world | identities, schemas, revision-checked atomic writes, replay/rebuild, refusal atomicity, authentication, revocation and independent recovery | multiple people, arbitrary migration, general erasure or external backup |
| Linux workspace | root execution in a dedicated VM, pinned SSH bridge, bounded output, timeout cleanup, poweroff/start and reconnection | per-package isolation, frozen dependencies or whole-machine reproducibility |
| Native development | retained package lifecycle, browser/Python execution, candidate isolation, real JEFF-authored counter and dragging | general modules, live subscriptions, scoped action input or large-world behavior |
| Programmable shell | authored desk/chat, independent parent recovery, Markdown/progress, real pointer persistence, draft/focus continuity and shell replacement | every interaction pattern, background task continuity or a universal UI runtime |
| Managed JEFF | account-backed authoring plus compiled inventory checks showing only Agora-native actions and clock/composition support | proof that every future host configuration excludes ambient capabilities |

The next experiments should be chosen from observed use: narrower source edits,
scoped action inputs, reusable UI parts, justified subscriptions, richer recovery
and ordinary browser/source workflows. Each must preserve the current invariants
while testing whether it actually reduces friction. Detailed distributed
governance, every external broker and one fixed multi-agent topology are not
prerequisites. [[Agora Spec]] §22 retains the unordered feature horizon: everyday
computing, JEFF's continuity, social spaces, devices, ownership and distribution.

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
