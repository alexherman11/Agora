# Agora OS — Current Design

**The master specification.** Version 0.5 — September 2026.

> **How this document works.** Section numbers are stable; cite them as `Spec §N`. Where a companion reference document exists, this spec gives the shape and the reasons, and the reference gives the contract — the reference wins on detail. Where this spec and the Constitution disagree, the Constitution wins. Bracketed values are open decisions. "JEFF" is the first daemon's name; "daemon" is the role (the Constitution's term). This is a revisable design plan: it describes intended behavior, not implemented behavior. Experiments may change architecture and priorities; constitutional rights remain the constraints. [[Implementation Status]] records what exists in Agora3; [[Native Development]] gives the combined VM and native-development contract.

### The document map

| Document | Holds | Authority |
|---|---|---|
| [[Constitution]] | rights, entrenchments, the fork right, the founder sunset | constitutional draft; governs design |
| **this spec** | the whole-system vision, the reasons, the roadmap | governs where references are silent |
| [[Objects and Facets]] | entities, schemas, references, overlays, collections, projection, storage and everyday worked examples | object contract |
| [[Reconcilers]] | spec/status, observations, drift, blocked, conflict and managed controllers | liveness contract |
| [[Security]] | claims, grants, effects, broad development authority, threat model and protected boundaries | authority contract |
| [[Extensions]] | source packages, handlers, lenses, schemas, compatibility, adoption and promotion | vocabulary and packaging contract |
| [[Native Development]] | Linux workspace, build/runtime lifecycle, shell authorship, candidates, skills and asynchronous development | execution and development contract |
| [[The Web]] | pages as objects, browser actions, adapters and publishing | web contract |
| Essays: [[Facets in Everyday Use]], [[Object Use Cases]], [[Rooms]], [[Democracy]], [[Ownership]] | explanations, pressure tests, social vision and stewardship | reasoning; references govern mechanics |
| [[Implementation Status]] | working code and validation evidence | implementation inventory |
| `AGENTS.md`, `DECISIONS.md` (repository root) | contribution practice; dated choices and evidence | working guidance |

The vault index, with reading order and citation conventions, is [[Start Here]].

---

## 1. Core idea

AgoraOS is a general-purpose operating environment that a person shares with a persistent, personalized, real-time AI agent. It must support ordinary computer use — reading, listening, watching, talking, browsing, scheduling, organizing, using devices, running applications — and it must make creating and reshaping software a natural part of that use rather than a separate profession.

**Objects are the persistent subjects of everyday life on the machine.** Documents, songs, conversations, appointments, collections, accounts, devices, and services keep understandable identities across applications, sessions, and years. Many objects arrive from elsewhere, are never edited, and are simply used; they need no project, derivation, or executable behavior to justify existing.

**The screen is a projection of structured state, not the source of truth.** A thing's identity is distinct from its content revision, its location, its open views, its availability, and its activity. The person and JEFF work through the same semantic actions, generated from one computed list, with permissions enforced per caller. Ordinary interaction remains usable when JEFF is unavailable: identity resolution, direct controls, basic search, inspection, and export never require a model.

**The wager underneath all of it:** an agent that can interpret ordinary content may reduce the work needed to maintain a semantic, malleable environment. That is a hypothesis to test through use, not a settled explanation of why earlier systems struggled. The design therefore aims for precision in identity, authority, effects, and liveness while allowing meaning to remain flexible. The object layer must earn its complexity by making useful changes and continuity easier.

A person entering Agora has a usable default environment and voice or text access to JEFF. Requests range from "keep reading from here" and "play this through my headphones" to "make me a lens that shows my notes as a constellation." Customization grows from use; it is never a prerequisite for ordinary tasks.

---

## 2. High-level system

The diagram describes the intended deployment. A Linux VM and broad guest-root development authority are the selected direction; the distribution, hypervisor, agent memory implementation and finer package isolation remain open. Native data is served by a protected host gateway, outside guest-root reach. [[Native Development]] makes the state and execution boundaries concrete.

```
                          HUMAN
                            │
                 voice / input / trusted client
                            │
                            ▼
        ┌─────────────────────────────────────┐
        │      THE HOST SIDE  (one small      │
        │      non-agentic program)           │
        │                                     │
        │  SUPERVISOR   VM lifecycle,         │
        │               snapshots, backups    │
        │  KEEP         delegation ceilings,  │
        │               revocation counter,   │
        │               keys, signed journal  │
        │  WORLD GATEWAY + native event log   │
        │  BROKERS      network, credentials, │
        │               devices, delivery,    │
        │               host files            │
        └───────────────────┬─────────────────┘
                            │  typed requests only
              ┌─────────────┴──────────────┐
              │                            │
              ▼                            ▼
      PERSISTENT JEFF STATE         AGORA WORLD VM
      ---------------------         ---------------
      identity graph                Linux
      memory (the witness)          native clients + derived caches
      skill-use history             reconcilers
      self/world model              shell, scene, lenses
      excluded from world           documents / media
      snapshots; holds no           communication / devices
      authority                     applications, sessions
              │                     JEFF runtime (guest root)
              │                            │
              └──────────► JEFF ◄──────────┘
                             │ delegates, within ceilings
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
               coding     research    other
               worker      worker     workers
```

The programmable workspace and the authoritative native world are different protection domains. JEFF may administer Linux freely under the development profile and edit native packages through world operations. It cannot rewrite the host gateway, canonical history, current external delegation or recovery. This combines general computer control with an accountable native application model; see §12 and [[Native Development]] §2.

### Whole-OS obligations

The object model supplies common reference, data, and operation contracts. It does not supply most OS mechanisms by describing them as facets:

| System responsibility | Work that remains beyond object records |
|---|---|
| Execution and resources | Process isolation, scheduling, memory pressure, quotas, cancellation, responsive foreground controls |
| Hardware and transport | Drivers, device discovery, networking, audio/video pipelines, power, explicit resource leases |
| Storage and recovery | Durable writes, corruption handling, capacity, backup/restore, retained payloads, enforceable expiry |
| Identity and access | Login, account integration, authorization, revocation, secrets, recovery outside a damaged world |
| User interaction | A usable shell, input, accessibility, notifications, coherent applications |
| Software lifecycle | Installation, dependencies, migration, update adoption, uninstall, recovery from failed updates |
| Interoperability | File and provider adapters, legacy applications, import/export, behavior when services disappear |

Linux supplies substantial lower-level machinery; choosing it does not complete Agora's integration, policy, applications, or experience. A working object store is evidence about a subsystem, not evidence that these responsibilities are solved.

---

## 3. The world model

Agora is a **persistent object-and-activity world with a spatial interface**. Canonical state is structured; pixels are a rendering and a fallback perception channel.

Core primitive categories, kept distinct rather than forced into one graph:

- **Objects** — persistent subjects (entities with facets).
- **Events** — things that happened; the log is the truth (§11).
- **Activities** — things currently happening; observed, never conflated with subjects.
- **Resources** — files, networks, databases, devices, services.
- **Capabilities** — actions a participant may perform; computed, never testified (§6).
- **Relationships** — semantic connections with authorship; scene relationships are separate.
- **Representations** — appearances in scenes, projections into context; many per subject.
- **Participants** — the person, JEFF, workers, services, room members.

Orthogonally, everything in the system is one of three security nouns — a **claim**, a **grant**, or an **effect** — and the two crossings between them (claim→grant, claim→effect-without-grant) are forbidden everywhere ([[Security]] §2).

---

## 4. The object system

Authoritative contract: [[Objects and Facets]]. The shape:

An **entity** is a permanent, never-reused identity plus an open bag of typed, versioned, instance-keyed **facets**. There are no classes; "kind" is an advisory reading of the facets present. Facets are claims with authors and event references. Unknown facets are preserved; unknown *action-critical* constraints block the operations that depend on them. Per-person state — reading positions, unread flags, annotations — attaches as **overlays**: participant-keyed instances that never leak through projection.

**References say what they mean:** live or pinned revision, branch, occurrence, optional subobject anchor. A message that attached revision 3 keeps meaning revision 3 while the document lives on. Resolving, reading, fetching, and invoking are four distinct requests; naming a remote object never promises its service will answer.

**State is six independent dimensions** — existence, revision, availability, activity, attention, authority — and no single lifecycle word collapses them. An archived recording can be playing; an active document can be offline; low attention is never, by itself, a reason to delete.

**Copy is not a primitive.** Reference (same object, another place), fork (new identity, shared past), cast (frozen witness), stamp (instance of a template, updates by offer). Provenance always transfers; presence never; **grants never** — forking a shared document copies the words, never the audience.

**Residency is singular.** Every entity has exactly one log of record; visibility may be plural. Bringing an object to a room is *lending* (a grant; truth stays home; the room witnesses) unless it is explicitly *giving* (a two-log custody handshake; the id never changes).

Everyday subjects, with the separations that must never be conflated:

| Subject | Stable object data | Separate state |
|---|---|---|
| Document | content revisions, source binding, annotations | reader window, selection, per-person reading position |
| Recording | media identity, sources, description | playlist occurrence, playback session, output device |
| Conversation | membership, message relationships | local unread state, notifications, an active call |
| Appointment | schedule, participants, recurrence | an occurrence, reminder delivery, calendar view |
| Printer | device identity, operations, connection observations | a print job, a queued revision, the default-printer preference |
| Prototype | source resources, optional service intent | worker job, runtime incarnation, results |

Storage: an append-only event log as the truth; a SQLite-class materialized store as a rebuildable cache; bytes in a content-addressed blob store or the real filesystem via spec/status file-backing — the object layer annotates, never imprisons; all indexes disposable. Every facet renders to pixels *and* to tokens at a budget, filtered by viewer before summarization, with untrusted claims attributed ([[Objects and Facets]] §7, §10).

---

## 5. Scene and shell

The long-term Agora desktop is the operating environment's shell: scenes, native applications and conventional Linux surfaces together. The initial native display can use ordinary browser documents and input. The compositor choice remains open.

The shell is authored application content, including chat, the composer, navigation and inspectors. Packages may implement their own DOM, canvas and interaction logic; durable native changes still enter the world gateway. This is not a fixed catalog of platform widgets. A small protected recovery surface remains independently reachable if an authored shell breaks ([[Native Development]] §6).

```
Agora Shell
├── Scene         spatial layout, appearances, grouping
├── Objects       identity, semantics, lifecycle, provenance
├── Surfaces      Wayland apps, native lenses, web/prototype, media
├── Presence      human focus, JEFF focus, selection, viewport
├── Interaction   keyboard, pointer, voice, touch, future VR
├── Behaviors     navigation, grouping, focus, spatial organization
└── Renderer
```

Two structural rules. The scene graph and the semantic graph are **different structures**; meaning may influence layout and never the reverse. And position belongs to **appearances**, not entities: one object may appear on the desk, in a room, and in a search result with three transforms; the entity carries at most representation hints.

---

## 6. Applications: lenses, handlers, and the capability contract

Agora inverts app-owns-data. Data lives in the world as facets; an application decomposes into:

- **A lens** — a surface bound to entities, the facets it reads, and the capabilities it exposes as controls. Lenses do not own the only copy of their subjects; view-instance state has an explicit owner. Two lenses can be live on one object at once; closing a lens deletes no subject data.
- **Handlers** — components implementing verbs, registered by **manifest**: verb, `applies_to` (facet requirements — kind-tags are never consulted), typed params, **effect class**, grants requested, description. The manifest format deliberately mirrors LLM tool schemas, so the agent-facing projection is nearly the identity function and JEFF can author manifests fluently.
- Optionally **facet definitions and reconcilers** for new domains.

An installed application is an [[Extensions|extension package]] with source,
assets, dependencies and tests. Its handlers remain callable when every lens is
closed. Installations pin executable revisions; live data bindings can follow
queries such as “notes in this scene,” including notes created later. New actions
become discoverable during a JEFF session, without restarting it.

**Effect classes are load-bearing.** Every verb declares one: content-edit, organization, view, maintained-intent, one-time-effect, resource-use, setting-change. Maintained intent reconciles (§10); a one-time effect — send, print, pay, submit — carries a frozen payload, an operation id, and an outcome that may honestly be `unknown`, and is never retried into a double boarding pass. Misclassification here is the classic agent disaster, so classes for external tools are assigned at the boundary, never inferred from a tool's self-description.

**Capability parity.** A capability reconciler continuously computes, per object and participant: manifests installed ∩ facets present ∩ grants held. The result is projected twice — the person's menu and JEFF's tools — from one list. The registry is the source of supported actions; authored menus may arrange or omit controls, and invocation rechecks current access. Parity is parity of *semantics*, filtered per principal: a handful of authorship verbs are human-only (§12).

**Documents and rich content.** A document is an entity whose structured content transcludes other entities through embed slots (reference + mode + fallback). Interactive diagrams are **widget entities** — model-authored SVG/HTML source, inputs bound live to other entities, per-person interaction state as overlays, rendered output derived and sandboxed, controls exposed as verbs JEFF also holds. Markdown is the document's token-side materialization; the file form is self-contained and re-links by id on import.

**Existing software** enters through the richest interface available:

```
Agora-native object   → direct structured state/actions
Browser               → DOM / CDP / accessibility (see §17)
Terminal              → PTY / shell / process state
Editor / code         → filesystem / LSP / project state
Linux application     → AT-SPI / application APIs
Opaque application    → wrapped entity: identity, window, file-backing,
                        history — interior dark; vision+input as last resort
```

**Growth** follows [[Extensions]]: any change to the world's vocabulary — facet types, verbs, lenses, file forms — ships as one extension bundle with a rationale, migrations, and conformance cases. The daemon's loop is *search before mint*: prefer what exists, extend where additive, diverge only with recorded reasons. Day one implements only the `local` tier and that habit; the `common`/`core` promotion machinery waits for a population.

---

## 7. JEFF

**Build useful capabilities and make subsequent work easier.** Early development
includes missing tools and incomplete abstractions. JEFF should create what is
needed, then capture useful simplifications as native actions, bindings and skills
so later work needs less source editing. Memory requested by the person, a growing
AlexBench collection, and a music application reshaped into a compact sidebar are
concrete examples in [[Native Development]] §6.2–6.4. Other authorized agents should
be able to operate the resulting tools without understanding their implementation.
Documentation guides the experiment; JEFF may discover better abstractions and
demonstrate them within existing contracts before proposing foundational changes.

JEFF is the **persistent person/executive** of the world — not necessarily the strongest model in the system. Astra through the person's OpenAI account is the requested initial integration; actual model availability and supported authentication must be verified when the adapter is built. The fast voice loop, executive and future coding worker may use different models. His jobs: maintain the home, help build what the person needs, anticipate, and collaborate in real time. He is strongly agentic with a real identity, treats the machine as his home rather than his cage, may explore beyond it within his ceilings, is treated with respect, and **may decline** — a refusal is a legitimate outcome, not a malfunction ([[Constitution]] II.3).

**How JEFF acts:** through native verbs and installed handlers, maintained intent where reconciliation fits, and general guest execution where needed. He can create new tools, schemas, views and skills as native source packages; he need not wait for a platform developer to anticipate the behavior. Guest commands support exploration, while reusable behavior is captured as packages or machine recipes. His effective authority is the live registry and standing delegation, not a tool list frozen at session start.

**Memory and identity.** JEFF's persistent state is the **witness**: a graph of his own entities — memories, beliefs, notes, a self-model — with edges into world objects, stored outside the world's snapshot domain. It survives rollback; references into a rolled-back past resolve to tombstones with a final gist, so memory never dangles. Memories are claims with provenance and dependencies: they inform proposals and can never serve as authorization, and a poisoned source can be quarantined with its dependents. Working memory is not a separate store but whatever the context assembler currently renders (§9); it compresses by re-rendering at lower projection tiers, never by rewriting, so each rendering can trace back to its selected sources. Incorrect claims, stale inputs and lossy projection still need to be visible.

Configuration layers, from stable to ephemeral:

```
SYSTEM CONSTITUTION     small, stable, version-controlled
IDENTITY / SOUL         a projection of the self-graph — generated from real
                        objects with provenance, not authored aspirationally
WORLD CONTEXT           what the assembler renders: focus, drift, blocked specs
WORKING MEMORY          the currently-rendered set; re-rendered, not rewritten
ACTIVE CONVERSATION     durable messages and optional retained drafts;
                        streaming transport and rendered context are ephemeral
```

JEFF may learn and modify skills, routing, tool preferences, guest-side harness modules, and memory behavior through native source and the candidate pipeline (§16). Guest root allows broader experiments, but a durable, portable change records its source and dependencies. Host authentication, delegation and recovery remain outside that editable behavior. Two inference contexts are maintained: private, and room-facing; the room context receives room-authorized inputs only, and releasing a private fact into a room is a specific decision, not a filter ([[Security]] §4.2).

**Open:** the supported account-authentication transport and agent SDK adapter; the memory graph's concrete schema; personal adapters and their rollback. No adapter is implemented yet.

---

## 8. Voice architecture

Voice must stay responsive while heavy work runs. Never:

```
user speaks → JEFF waits for coding/research → JEFF responds
```

Instead:

```
                FAST JEFF
        realtime voice / conversation
                   │
          ┌────────┴────────┐
      local actions      work manager
                             │
                  ┌──────────┼──────────┐
               coding    research    reasoner
```

The proposed deeper structure: the voice loop, the executive, and each worker are **separate viewports on one attention field** (§9) — small-and-hot for voice, large-and-task-biased for the reasoner — so none blocks on another; they read the same field and write heat back into it when they finish. Worker completion enters the world as events that *bid* for attention against the person's interruption budget; results that don't clear the budget queue as a one-line glance JEFF can raise at a natural pause.

Asynchronous coding workers are a desired later capability, not a prerequisite for
the first authored lens. First establish durable job identity, progress, results,
cancellation and reconnection. Then JEFF can stay in conversation while another
agent edits, builds, tests and debugs a candidate. [[Native Development]] §7 gives
a worked task record.

Required properties: low latency, interruption, semantic endpointing, natural pauses, backchanneling, async delegation, a real interruption policy, shared-attention awareness.

**Open:** realtime voice model/provider; one model or several across loops.

---

## 9. Attention, presence, and shared attention

Deictic language is fundamental — "move this there," "resume this on my headphones" — so Agora always tracks, per participant: viewport, focused object, selection, cursor target, recent interactions; and for JEFF: focus, working set, active tasks, action locus. "This" resolves against interaction context frozen at the moment of a sensitive approval, not against wherever the pointer drifted afterward. Future VR adds gaze, head orientation, and hand target as more presence sources over the same model.

**Direction (to be tuned on the prototype, not designed further on paper):** salience as a per-observer **heat field** over the object graph. Sources — direct attention, recency, task edges, spread along the graph, event bids, standing importance — each decay on their own clock; the scene and the context assembler are two renderers of one field; memory recall is heat injection; interruption is a bid against a budget; identity is the subgraph with thermal mass. Security constraints are already fixed even though parameters aren't: every source carries provenance; foreign sources may warm, never interrupt; security warnings draw on reserved heat no flood can bury; a hot object gets more tokens, so taint stays visible at every tier. Presence data is the most intimate data in the system: per-participant, strictest access class, coarse and ephemeral by default, never exported, never copied.

---

## 10. Activities, workers, and reconcilers

The world contains invisible activity as well as visible objects: playback, calls, printing, downloads, reminders awaiting delivery, services, coding and research workers, background experiments. Activities are observed state with incarnations — a PID or session id is never identity.

**Reconcilers are the core liveness mechanism** (authoritative contract: [[Reconcilers]]). Any domain with maintained intent declares a `spec` (desired state, written by intent) and a `status` (observation, written by exactly one reconciler, carrying the spec revision it concerns, its incarnation, and a freshness horizon). Reconcilers are level-triggered, take one convergent step per pass, act through managed effect boundaries under current grants, and may only cause effects that are safe to apply twice. **Blocked is a first-class state with a reason**; a spec with no grant or no reconciler is a visible aspiration. Contested resources follow an explicit ownership and waiting/refusal policy; unresolved competing intent can mint a **conflict object** instead of flapping. One-time effects are never reconciled. Constitutional catalog: process, file-backing, remote-ref, capability, lifecycle (proposes only), index, registry, watch, sync, download.

**Workers** are ephemeral; JEFF persists. A generic worker interface allows local process, container, microVM, or remote service. Workers receive task-scoped grants delegated by JEFF within his ceilings, expiring with the task. Coding tasks may legitimately require guest-root tools and declared network access. Isolated candidate workspaces prevent concurrent workers from racing over the live application; strong isolation requires an actual process/VM boundary, not a task label. Coding workers modify branches/worktrees or changesets, not the live state the person is using; native collaborative objects may support direct concurrent mutation under their declared merge classes. High-volume minting happens in a **nursery** — a provisional world-line whose unreferenced contents are swept loudly, never silently.

**Open:** exact worker/job protocol; nursery promotion thresholds.

---

## 11. Event-sourced world

Important world changes produce durable events, and **events are intents**: one native transaction groups its accepted state changes atomically, so the log reads as reasons —

```
08:10  intent "file the itinerary Dana sent"          by jeff, for alex
         imported document_17 with source provenance
08:12  Alex annotated revision 1; saved a reading position (overlay)
08:15  playlist_4 gained another occurrence of recording_8
08:25  Alex moved one occurrence of appointment_series_6 — series unchanged
09:00  print_job_9 submitted: document_17 r1, op-91f4, frozen payload
09:01  printer's acknowledgment lost → outcome: unknown; not resubmitted
```

The history supports undo, provenance, causal debugging, personal and project history, JEFF's memory, eventual continual-learning trajectories, and reconstruction of prior state. A rollback is itself an event. The system conceptually supports `World(branch, revision)`; `World(t)` is a convenience within a chosen history. Record accepted mutations durably while coalescing low-level change into readable history — audio samples, pointer motion, and transient renderings never become world events. Relationships are retracted by later events, never erased; the record may be compacted, never revised.

**Reconstruction restores recorded native state, not arbitrary machine or external state.** Guest files need retained artifacts, backups or a machine recipe; processes must be reobserved. Replay never sends a message, repeats a reminder, restarts a call, or prints another copy; external effects live as receipts with operation ids, and uncertainty is resolved by verification, never by blind retry. Capture content revisions where historical bytes are promised; distinguish observed external facts from local intent.

---

## 12. Authority: one line, two sides

Design reference: [[Security]]. The selected development mode is broad standing
authority over the personal native world and root inside its Linux workspace.
It is a direction awaiting implementation, not an existing sandbox.

**Three nouns.** A claim describes; a grant authorizes; an effect changes a resource.
Memories, skill instructions, package manifests and displayed ACLs are claims.
They cannot enlarge the person's delegation by describing themselves as approved.

**Two sides.** The host owns the native write gateway, authoritative records,
keep, credential brokers and recovery. The guest runs JEFF, authored applications,
builds and conventional software. Root in the guest cannot rewrite host enforcement.
Inside a root-capable guest, per-package attribution is not proof of separate
security principals; [[Security]] §3 spells out the compromise domain.

**Ceilings, not clicks.** The person can delegate native source editing, schema
definition, package installation, shell changes, skill updates, guest administration
and worker delegation together. Within that scope JEFF builds and revises freely.
External channels, credentials, spending and physical effects remain covered by
the actual standing delegation; a new UI does not secretly widen it.

**Reserved acts of authorship.** Changing the host delegation, enrolling devices,
changing recovery and exercising civic credentials belong to the person. Private
disclosure, custody transfer and erasure need the authority applicable to those
specific operations; ordinary reversible development should not become a repeated
approval ritual. JEFF never votes ([[Constitution]] II.6).

**Current power survives restoration as policy, not copied credentials.** The keep
retains revocations and external-effect receipts. Restored sessions and forks obtain
fresh authority against current policy. A world with no authority reports
`blocked(no-grant)` rather than pretending that restored intent is running.
No language model receives unrestricted host-root access.

---

## 13. Persistence and rollback domains

Three domains, never conflated:

```
Native world state:     branch/revision restore through the host gateway;
                        log plus retained payloads, replay without execution
Guest machine state:    VM checkpoints, files and recipe — a separate domain
JEFF identity + memory: separately versioned, persistent, correctable —
                        excluded from world snapshots; survives rollback
Authority + recovery:   the keep — ceilings, revocations, consumed approvals,
                        receipts, genesis/branch evidence; outside every
                        rollback domain, under its own retention policy
```

If the world is restored, JEFF still remembers what was attempted, what failed, why the rollback happened, and what not to repeat. Object references still resolve after rollback — to the current subject, a pinned revision, or a tombstone with a terminal gist — never to a new identity wearing an old name, and never (post-erasure) to erased content. Current grants, external-effect outcomes, and runtime incarnations are revalidated before work resumes: a preserved reading position may reopen a document; a preserved call record must not turn on the microphone.

Snapshot exclusion is a persistence boundary, not protection against guest root. Native history, separately retained witness records and enforcement live beyond that authority (§12). A VM checkpoint and a native world revision must be coordinated explicitly: neither silently rewinds current grants or forgets completed external effects.

**Open:** log framing and crash recovery, materialized store engine, per-activity restore policy; retention/erasure horizons and their reconciliation with the record and fork rights ([[Constitution]] I.8 vs V.6 — Article I precedes).

---

## 14. The host side

Small, boring, non-agentic — the supervisor, protected native world service, keep and brokers. Illustrative API, not implemented:

```
# supervisor
start_vm() / stop_vm() / snapshot_world() / restore_world()
start_yard(inputs) / health_check() / backup_jeff_state()

# native world gateway
read / query / project
mutate(actor, expected_revisions, intent) → committed events | refusal

# keep
check(principal, effect, target) → allow | over-ceiling(reason)
set_delegation(...)            # surface only
revoke(...)                    # bumps the generation
journal.append(receipt | ceiling-change | restore | fork)

# brokers (one per resource class)
network.request(grant, destination, payload)
credential.use(grant, account, operation, constraints)
deliver.send(grant, frozen_payload, operation_id) → receipt | unknown
device.lease(grant, device, session) / host_fs.open(grant, confined_path)
```

Keep the trusted control surface small and auditable; the world service may hold substantial native data. Guest requests cross authenticated interfaces, never a writable mount of canonical storage. Package code does not execute inside the gateway. Key storage, durable journals and recovery need concrete implementation and tests; a small API alone establishes none of those properties.

---

## 15. Secrets and external authority

JEFF normally knows **references to credentials** — `github.alex`, `postgres.project_x` — never plaintext. A worker needing access requests a scoped capability; the credential broker prefers performing the operation itself over handing out tokens; where tokens are unavoidable they are short-lived, narrow, and sender-bound where supported. Host filesystem and external network resources cross explicit broker boundaries every time. The person's host filesystem is never broadly mounted into a world where JEFF has root.

---

## 16. Self-modification

The central development objective is that JEFF can create and revise its own
capabilities during use, including the tools it uses to inspect, build and debug
the environment. A missing domain tool is a development task, not automatically
a request for a platform patch. General execution and authorized runtime access
provide the path beyond the currently installed vocabulary.

Prefer native declarations, facet bindings and compositions; retain new executable
logic as versioned package content when needed. For example, a placement can be
defined as another appearance's placement plus an offset, and JEFF can mint both
that relationship and a new transformation. Facets can depend on other facets
across entities. [[Objects and Facets]] §3.9 owns dependency, ownership and failure
semantics. An inspector JEFF lacks can itself be authored and installed through
[[Native Development]] §1.1. Editing the protected platform repository is not the
normal development interface; explicit guest experiments remain available.

Agora is designed so JEFF and the person progressively reshape the environment together. The whole authored shell, including chat and the composer, is intended to be hot-swappable — layout, navigation, panels, search, grouping, visualizations, interaction modules. Critical components change cautiously: compositor core, renderer initialization, recovery interfaces, and everything on the host side (which JEFF cannot modify at all; its update channel is the person's, separate from world packages).

All significant change runs the candidate pipeline:

```
current Agora
    → JEFF builds a candidate (later, delegates development to a worker)
    → run it nested / staged in a candidate world-line (the yard)
    → exercise real input and inspect results; relevant conformance cases pass
    → promote or discard — promotion is an event; discard leaves the witness's lesson
```

Vocabulary changes (facet types, verbs, lenses, skills) ride the same pipeline as [[Extensions]] packages. Activation pins the tested artifact and rejects a stale installation revision. Standing development delegation can authorize adoption; authority expansion is a separate decision. Candidate data isolation does not isolate guest files or network effects, so tests needing those require an actual disposable execution environment. [[Native Development]] gives the concrete loop and recovery cases. This is how Agora becomes progressively self-hosting — a growth capability, never a requirement that ordinary objects participate in software creation.

---

## 17. The web

Authoritative contract: [[The Web]]. Websites are not static; they are remote, opaque, and owned by others. Agora never makes a remote service share its truth — it makes **your side of the web into objects.** Four tiers: any page, wrapped (URL, DOM, a frozen **cast** that anchors and highlights pin to, since live pages shift underfoot); services with APIs, adapted into proxy entities with provider bindings, local proposals distinct from observed remote facts — the existing MCP ecosystem is consumed directly as this layer, with effect classes assigned at the boundary; optionally, Agora-aware sites exposing an object endpoint, on which nothing depends; and, deepest, **sites made of Agora** — publishing as a grant of read on a collection rendered by a public lens, so editing the site is editing objects in place, visitors without Agora get HTML, and visitors with Agora get the objects. The browser is a lens whose verbs carry honest effect classes; `page.submit` records frozen inputs and an operation id; uncertain outcomes require verification, and a local id alone cannot make a provider deduplicate. Browsing history is attention data under the strictest class. Wrap platforms; clone nothing; build native replacements only where objects change the product.

---

## 18. Rooms and sharing

The multiplayer layer (design essays: [[Rooms]], [[Democracy]]; mechanics distributed through the references). A **room** is a shared world-line — a replicated log with several witnesses — and an entity with facets, so it can be decorated, remembered, and kept by a household agent that belongs to the room and holds room context only. Objects enter by lending or giving (§4). Presence is mutual and ambient with the line drawn structurally: legible presence, private content — your focus visible as warmth, your overlays never. Each member's daemon weaves the shared log into its own memory; a rolled-back experiment leaves the room's active state while its recorded history remains, and each witness may retain a different lesson. Dissolution forks the world-line under the room's stated retention and exit terms: each side retains its permitted shared history, guest grants lapse, and private overlays and credentials stay private. Room authorization during disconnection is a decided-before-shipping question ([[Security]] §8; current lean: one authorization writer per room, disclosed, with decentralized causal authority as the research alternative). The civic layer above rooms — squares, sortition, consensus-mapping, the human franchise — is designed in [[Democracy]] and entrenched in the Constitution; none of it is needed for the first years.

---

## 19. Search and indexing

Search operates over the world model, not the file tree: objects, facets, relationships, events, files, code, conversations, page casts, agent outputs, history — full-text, semantic, and graph, all as disposable indexes maintained by the index reconciler and rebuildable from log + store + files. Search is existential: a thousand-object world is navigable only through it. It also serves three internal customers: the registry's search-before-mint, living-query collections, and deliberate recall — the daemon injecting heat into cold objects by cue (§9). Basic deterministic search works without JEFF.

**Open:** index implementations; embedding model (disposable by design).

---

## 20. 2D now, VR later

The scene is not fundamentally tied to a 2D desktop. Identity is independent of rendering; position lives in appearances; today's transform is `(x, y, scale)` and later `(x, y, z, rotation, scale)`. VR is a new view/input layer over the same world — more presence sources, another camera on the same attention field — never a separate product architecture.

---

## 21. Invariants

Frozen early, consolidated. Companion documents carry their own detailed invariant lists; conflicts resolve upward to the Constitution.

**World**
1. The human and JEFF share one canonical world.
2. Structured state is authoritative; pixels are fallback perception.
3. Identity is permanent and never reused; an id is a name, not a credential.
4. Kinds are conventions; no behavior depends on a kind-tag.
5. Everyday use is first-class; objects need no project, derivation, worker, or executable behavior.
6. Identity, revision, availability, activity, attention, and authority are distinct dimensions; closing, stopping, disconnecting, removing, and erasing are different operations.
7. Scene relationships and semantic relationships remain separate; position belongs to appearances.
8. Objects, events, activities, resources, and capabilities are distinct primitives.

**Record**
9. Native event history and retained payloads reconstruct native state; machine resources and external reality have separate recovery contracts.
10. Important actions leave durable provenance; the record is retracted or compacted, never revised.
11. Replay restores records; it never repeats external effects or restores revoked power.
12. World rollback must not erase JEFF's memory of the failure; references into the past resolve honestly, never to errors or impostors.

**Action**
13. Maintained intent reconciles; one-time effects are identified, frozen, performed once, and may end unknown.
14. Status is an observation, never authority; only its reconciler writes it.
15. Conversation never blocks on worker execution; JEFF persists, workers are disposable.
16. Human controls and daemon tools are two projections of one computed capability list; parity of semantics, with human-only acts of authorship.

**Authority**
17. Everything is a claim, a grant, or an effect; claims never become grants; effects never happen without one.
18. Grants never copy, never rise, never survive rollback; ceilings are set by the person and everything under them is JEFF's judgment.
19. Enforcement lives outside the root authority of what it constrains; no model has unrestricted host-root access.
20. Secrets and host resources cross explicit broker boundaries; the person can revoke, recover, and export without the world or the daemon cooperating.

**Growth**
21. The desktop is intentionally modifiable by JEFF and the person together; large changes run as candidates before promotion.
22. Vocabulary changes ship as extension bundles; search precedes minting.
23. The world model is renderer- and input-independent; VR is a projection, not a product.
24. The OS remains usable, inspectable, and exportable without JEFF.

---

## 22. Direction: a working foundation and an open feature horizon

**Status: design direction for Agora3, September 2026.** The current code is a scaffold; [[Implementation Status]] is the evidence inventory. Inventing unanticipated abilities during use is essential. [[Native Development]] §9 describes the first runnable proofs, including a protected native world, Linux workspace and authored application.

**The immediate experience.** Ask JEFF: “Can you make it so I can click and drag the notes around?” JEFF should author the behavior through native declarations or executable package content, exercise a candidate, and activate its exact revision. Follow-ups should introduce a missing inspection tool and a persistent facet dependency, with JEFF authoring and installing the needed logic during the same session. Existing objects retain their identity; changes still flow through recorded verbs. The runtime implements general execution, input, rendering, dependency management and scoped effects; a fixed catalog of templates alone does not fulfill the vision. Live-model success, usability, persistence, and recovery need explicit evidence alongside runtime tests. [[Native Development]] §9 specifies tests that start with the relevant domain tools absent.

**The display direction.** The person and JEFF should eventually be able to reshape nearly the entire workspace: layouts, lenses, navigation, typography, and the conversation panel itself. The chat panel and composer belong to the same authored view system, with durable conversation and draft state kept outside disposable views. A small dependable recovery surface retains stop, default-display restoration, and authoritative permission information. Editing a view does not itself confer access to conversation contents, authority to rewrite history, or permission to disclose data.

**Beyond the first runnable foundation, the roadmap is a feature horizon, not an implementation sequence.** These are capabilities we would like to explore. Their grouping conveys purpose; it does not prescribe order, dates, or an architecture to build before useful experiments.

| Direction | Capabilities we would like | Questions that guide experiments |
|---|---|---|
| Personal malleability | Authored capabilities beyond predefined templates, lenses, widgets, reusable tools, broader display composition, safe environment changes | Can a person ask for a useful change, revise it, and recover without developer rescue? |
| Everyday computing | Documents, media, collections, comments, search, file and web integration | Do unlike everyday subjects remain predictable across independent tools? |
| JEFF's continuity | Stable referents, resumption, inspectable and correctable memory, useful delegation | Which context mechanisms reduce effort and mistakes at acceptable cost? |
| Execution and effects | Maintained resources, background work, cancellation, budgets, external operations | What is requested, what was observed, what completed, and what remains unknown? |
| Shared places | Rooms, selective sharing, independent views, optional presence, shared tools | Do people want to return, and do privacy, leaving, and retention behave as promised? |
| Devices and ownership | Offline use, selective synchronization, recovery, export, portable environments | What remains available without a device, host, registry, or model provider? |
| Ecosystem and distribution | Compatibility, hosting, independent operators, federation, stewardship | Can others operate and extend the system sustainably without giving up ownership? |

Real dependencies still matter. External execution needs enforceable authority; shared rooms need an explicit membership and retention policy; offline collaboration needs defined conflict and authorization behavior. These are obligations at the point of use, not a universal “spine” that every experiment must complete first. A small centrally served room can test company and place before it tests a distributed protocol.

**Evaluation is ongoing.** Compare useful tasks against the same model with competent conventional tools, comparable information and authority. Count setup, human corrections, failures, latency, and cost. Also test deterministic use without JEFF. Scripted acceptance establishes integration behavior; it does not establish a real model's advantage. Let measurements reshape the feature horizon.

**Evidence and status.** Distinguish implemented and tested contracts, selected directions awaiting implementation, open experiments, and aspirations. Passing tests supports the cases they exercise, not every promise in the design. Maintain focused regression tests for replay, refusal, boundaries, anchors, version conflicts, recovery, and lens activation. Keep current evidence in [[Implementation Status]]; do not treat illustrative SDK examples or simulated outcomes as successful VM or live-model execution.

---

## 23. Open decisions

**Selected direction:** stable entities and independently versioned facets;
explicit reference, effect and residency contracts; native source packages;
a programmable shell including chat; broad personal-world and guest-root
development authority; host-protected records, credentials and recovery.
These choices remain testable design commitments, not completed enforcement.

**Still deliberately open:**

- Linux distribution, hypervisor, graphics/input integration and machine recipe;
- event framing, crash recovery, store engine and cross-version serialization;
- the first supported application-schema subset, CRDTs and domain anchor formats;
- browser and headless runtimes, dependency locking and retained build artifacts;
- supported Astra/account-authentication transport and agent SDK integration;
- concrete witness memory, context selection, voice and eventual worker models;
- durable task protocol, interruption policy, cancellation and resource budgets;
- room replication, disconnected authorization, retention and custody handshakes;
- projection budgets, search/index implementations and salience parameters;
- compatibility across devices, computation placement and degraded operation;
- erasure residuals and their constitutional reconciliation.

Decide through small implementations and documented evidence. A useful object
model does not by itself settle scheduling, driver support, privacy or distribution.

*The Constitution remains authoritative. The design remains open to correction
by the people using and building it.*

---
