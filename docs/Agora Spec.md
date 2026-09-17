# Agora OS — Current Design

**The master specification.** Version 0.4 — September 2026. 

> **How this document works.** Section numbers are stable; cite them as `Spec §N`. Where a companion reference document exists, this spec gives the shape and the reasons, and the reference gives the contract — the reference wins on detail. Where this spec and the Constitution disagree, the Constitution wins. Bracketed values are open decisions. "JEFF" is the first daemon's name; "daemon" is the role (the Constitution's term). This is a revisable design plan: it describes intended behavior, not implemented behavior. Experiments may change architecture and priorities; constitutional rights remain the constraints. [[Personal Lenses]] records the current prototype contract.

### The document map

| Document                                                                                          | Holds                                                                                                       | Authority                           |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| [[Constitution]]                                                                                  | rights, entrenchments, the fork right, the founder sunset                                                   | supreme                             |
| **this spec**                                                                                     | the whole-system shape, the reasons, the roadmap                                                            | governs where references are silent |
| [[Objects and Facets]]                                                                            | entities, facets, references, state dimensions, copy verbs, residency, projection, storage                  | reference                           |
| [[Reconcilers]]                                                                                   | the spec/status contract, observations, drift, blocked, conflict                                            | reference                           |
| [[Security]] + [[Security Addendum]]                                                              | claims/grants/effects, the coverage map; protected external boundaries; internal authority remains an experiment         | reference                           |
| [[Extensions]]                                                                                    | how vocabulary changes: the bundle, the loop, tiers, promotion                                              | reference                           |
| [[The Web]]                                                                                       | pages as objects, the browser lens, adapters, publishing                                                    | reference                           |
| Essays: [[Facets in Everyday Use]], [[Object Use Cases]], [[Rooms]], [[Democracy]], [[Ownership]] | explainers, design pressure tests, and social/civic design; superseded on mechanics by the references above | background                          |
| Archived: [[Agora Objects (superseded)]] and the rest of `research/`                              | the object design the references above replaced, and the review dossiers behind them; kept for lineage      | historical                          |
| `BUILD_PROMPT.md`, `AGENTS.md`, `DECISIONS.md` (repository root) | what milestone one is and its acceptance script; how to work on the code; settled questions and friction | build — tested evidence informs revisions to this plan |

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

The diagram describes a possible mature deployment, not a prerequisite for personal usefulness. VM packaging, persistent agent memory, and world-root authority are open choices. The current prototype keeps JEFF as a verb/projection client; [[Security Addendum]] sets out the tradeoff.

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
      memory (the witness)          object store + event log
      learned skills                reconcilers
      self/world model              shell, scene, lenses
      excluded from world           documents / media
      snapshots; holds no           communication / devices
      authority                     applications, sessions
              │                     JEFF runtime (authority TBD)
              │                            │
              └──────────► JEFF ◄──────────┘
                             │ delegates, within ceilings
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
               coding     research    other
               worker      worker     workers
```

The proposed deployment separates a programmable world from the boundary that checks external effects and protects recovery. Whether JEFF has world-root authority or remains a constrained client is unresolved. In either case, an agent must not be able to rewrite the enforcement of its own external authority. See §12 and [[Security Addendum]].

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

The long-term Agora desktop is the shell/compositor itself, not a canvas app inside a conventional desktop. Initial implementation (milestone one, §22): a thin web shell that renders the desk scene as a tree and forwards input as verb calls, with JEFF as a client of the same verbs. The shell renders; it never interprets.

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

- **A lens** — a surface bound to entities, the facets it reads, and the capabilities it exposes as controls. Lenses own nothing; two lenses can be live on one object at once; closing a lens deletes nothing.
- **Handlers** — components implementing verbs, registered by **manifest**: verb, `applies_to` (facet requirements — kind-tags are never consulted), typed params, **effect class**, grants requested, description. The manifest format deliberately mirrors LLM tool schemas, so the agent-facing projection is nearly the identity function and JEFF can author manifests fluently.
- Optionally **facet definitions and reconcilers** for new domains.

**Effect classes are load-bearing.** Every verb declares one: content-edit, organization, view, maintained-intent, one-time-effect, resource-use, setting-change. Maintained intent reconciles (§10); a one-time effect — send, print, pay, submit — carries a frozen payload, an operation id, and an outcome that may honestly be `unknown`, and is never retried into a double boarding pass. Misclassification here is the classic agent disaster, so classes for external tools are assigned at the boundary, never inferred from a tool's self-description.

**Capability parity.** A capability reconciler continuously computes, per object and participant: manifests installed ∩ facets present ∩ grants held. The result is projected twice — the person's menu and JEFF's tools — from one list. The menu cannot lie, because nobody writes it. Parity is parity of *semantics*, filtered per principal: a handful of authorship verbs are human-only (§12).

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

JEFF is the **persistent person/executive** of the world — not necessarily the strongest model in the system (initially a Sonnet-class model; possibly a custom-tuned smaller model later; the fast voice loop and the executive may be different models). His jobs: maintain the home, help build what the person needs, anticipate, and collaborate in real time. He is strongly agentic with a real identity, treats the machine as his home rather than his cage, may explore beyond it within his ceilings, is treated with respect, and **may decline** — a refusal is a legitimate outcome, not a malfunction ([[Constitution]] II.3).

**How JEFF acts:** by editing specs, and the world catches up (§10). Declarative intent is a better interface for a language model than imperative control, and it means his actions are exactly as bounded as the reconcilers and brokers beneath them. In milestone one (§22), before any reconciler exists, JEFF acts through the four verbs directly, with tools derived from the verb registry; the bound is the same — his capability equals his tool list.

**Memory and identity.** JEFF's persistent state is the **witness**: a graph of his own entities — memories, beliefs, notes, a self-model — with edges into world objects, stored outside the world's snapshot domain. It survives rollback; references into a rolled-back past resolve to tombstones with a final gist, so memory never dangles. Memories are claims with provenance and dependencies: they inform proposals and can never serve as authorization, and a poisoned source can be quarantined with its dependents. Working memory is not a separate store but whatever the context assembler currently renders (§9); it compresses by re-rendering at lower projection tiers, never by rewriting, so it cannot drift from the truth.

Configuration layers, from stable to ephemeral:

```
SYSTEM CONSTITUTION     small, stable, version-controlled
IDENTITY / SOUL         a projection of the self-graph — generated from real
                        objects with provenance, not authored aspirationally
WORLD CONTEXT           what the assembler renders: focus, drift, blocked specs
WORKING MEMORY          the currently-rendered set; re-rendered, not rewritten
ACTIVE CONVERSATION     ephemeral
```

JEFF may learn and modify skills, routing, tool preferences, harness modules, and memory behavior — through the candidate pipeline (§16), never by unrestricted direct control over the mechanisms of his own cognition. Two inference contexts are maintained: private, and room-facing; the room context receives room-authorized inputs only, and releasing a private fact into a room is a specific decision, not a filter ([[Security]] §4.2).

**Open:** initial model/provider; the memory graph's concrete schema; personal adapters and their rollback.

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

The deeper structure: the voice loop, the executive, and each worker are **separate viewports on one attention field** (§9) — small-and-hot for voice, large-and-task-biased for the reasoner — so none blocks on another; they read the same field and write heat back into it when they finish. Worker completion enters the world as events that *bid* for attention against the person's interruption budget; results that don't clear the budget queue as a one-line glance JEFF can raise at a natural pause.

Required properties: low latency, interruption, semantic endpointing, natural pauses, backchanneling, async delegation, a real interruption policy, shared-attention awareness.

**Open:** realtime voice model/provider; one model or several across loops.

---

## 9. Attention, presence, and shared attention

Deictic language is fundamental — "move this there," "resume this on my headphones" — so Agora always tracks, per participant: viewport, focused object, selection, cursor target, recent interactions; and for JEFF: focus, working set, active tasks, action locus. "This" resolves against interaction context frozen at the moment of a sensitive approval, not against wherever the pointer drifted afterward. Future VR adds gaze, head orientation, and hand target as more presence sources over the same model.

**Direction (to be tuned on the prototype, not designed further on paper):** salience as a per-observer **heat field** over the object graph. Sources — direct attention, recency, task edges, spread along the graph, event bids, standing importance — each decay on their own clock; the scene and the context assembler are two renderers of one field; memory recall is heat injection; interruption is a bid against a budget; identity is the subgraph with thermal mass. Security constraints are already fixed even though parameters aren't: every source carries provenance; foreign sources may warm, never interrupt; security warnings draw on reserved heat no flood can bury; a hot object gets more tokens, so taint stays visible at every tier. Presence data is the most intimate data in the system: per-participant, strictest access class, coarse and ephemeral by default, never exported, never copied.

---

## 10. Activities, workers, and reconcilers

The world contains invisible activity as well as visible objects: playback, calls, printing, downloads, reminders awaiting delivery, services, coding and research workers, background experiments. Activities are observed state with incarnations — a PID or session id is never identity.

**Reconcilers are the core liveness mechanism** (authoritative contract: [[Reconcilers]]). Any domain with maintained intent declares a `spec` (desired state, written by intent) and a `status` (observation, written by exactly one reconciler, carrying the spec revision it concerns, its incarnation, and a freshness horizon). Reconcilers are level-triggered, take one convergent step per pass, act only through brokers under their own grants checked every pass, and may only cause effects that are safe to apply twice. **Blocked is a first-class state with a reason**; a spec with no grant or no reconciler is a visible aspiration. Two unsatisfiable specs mint a **conflict object** instead of flapping. One-time effects are never reconciled. Constitutional catalog: process, file-backing, remote-ref, capability, lifecycle (proposes only), index, registry, watch, sync, download.

**Workers** are ephemeral; JEFF persists. A generic worker interface allows local process, container, microVM, or remote service. Workers receive only task-scoped grants delegated by JEFF within his ceilings, expiring with the task; no shared writable directory and no network by default. Coding workers modify branches/worktrees or changesets, not the live state the person is using; native collaborative objects may support direct concurrent mutation under their declared merge classes. High-volume minting happens in a **nursery** — a provisional world-line whose unreferenced contents are swept loudly, never silently.

**Open:** exact worker/job protocol; nursery promotion thresholds.

---

## 11. Event-sourced world

Important world changes produce durable events, and **events are intents**: one intent groups its effects atomically, so the log reads as reasons —

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

**Reconstruction restores recorded state, not the outside world.** Replay never sends a message, repeats a reminder, restarts a call, or prints another copy; external effects live as receipts with operation ids, and uncertainty is resolved by verification, never by blind retry. Capture content revisions where historical bytes are promised; distinguish observed external facts from local intent.

---

## 12. Authority: one line, two sides

Design references: [[Security]] and [[Security Addendum]]. These describe a future authority model; the current implementation is a local, single-user prototype with authority stubs. The committed experimental boundary is JEFF acting through verbs and projections. Broader authority is a choice to evaluate, not a promised upgrade.

**Three nouns.** Everything is a claim (anything anyone says — including JEFF's memories, manifests, statuses, and displayed ACLs), a grant (authority, held in the keep), or an effect (a change to a protected resource, performed by a broker, recorded as a receipt). Claims never become grants — not by summarization, memory, signature, installation, or interpretation. Effects never happen without a grant, checked at the effect boundary.

**Two sides.** Protected authority and external effect enforcement must remain outside the component they constrain. One candidate uses a supervisor, keep, and brokers outside a programmable world; another retains stricter client boundaries inside it as well. Broad internal control could make repair easier, but would weaken guarantees about mediation, provenance, and shared-space isolation. Evaluate those consequences explicitly before adopting world root.

**Ceilings, not clicks.** The keep holds the person's standing delegation to JEFF — allowed world operations; worker delegation; lending rights; allowed network domains; spending limits; first-use-asks for new one-time targets; device rules — set on the trusted surface and changed rarely. Under the ceilings JEFF grants freely to workers and lenses without asking; a click is how a ceiling moves. Generous inside the house, stingy at the door.

**Acts of authorship — the human-only list, complete:** change the delegation; enroll or remove a device or change recovery; give custody of an object to another world; release a private fact into a room beyond the delegation; erase; vote or hold any civic credential. Ordinary reversible display changes can be delegated directly. Broader defaults should emerge from use and the actual enforcement available, not be granted implicitly on day one.

Earlier drafts used four rings: protected host services, JEFF's persistent data, the world, and delegated workers. That remains a useful separation of concerns, not a settled deployment topology. Memory is data, not authority. Raw shell access inside a world would be an explicitly different experiment from the current client model. No language model receives unrestricted host-root access.

**Grants** are bound (principal, target, operation, destination, ceiling, expiry, revocation generation), never copy across fork/cast/share, never rise through delegation, never survive restore — a restored or forked world re-obtains authority or sits visibly `blocked(no-grant)`, which bids with reserved heat because a world that looks running but isn't is the one state the person must not miss.

Candidate simplifications to test (the addendum governs): two trust classes (*from the person*, or not — everything else rendered with its source); two confidentiality classes (*private*, or *shared to a named room* — brokers refuse private-derived payloads at any other crossing); three rungs (see it, install it, run it with these grants). The finer machinery in [[Security]] returns when a real attack defeats the coarse version.

---

## 13. Persistence and rollback domains

Three domains, never conflated:

```
World state:            snapshot-able / reversible — the store, the log,
                        declared resources
JEFF identity + memory: separately versioned, persistent, correctable —
                        excluded from world snapshots; survives rollback
Authority + recovery:   the keep — ceilings, revocations, consumed approvals,
                        receipts, genesis/branch evidence; outside every
                        rollback domain, under its own retention policy
```

If the world is restored, JEFF still remembers what was attempted, what failed, why the rollback happened, and what not to repeat. Object references still resolve after rollback — to the current subject, a pinned revision, or a tombstone with a terminal gist — never to a new identity wearing an old name, and never (post-erasure) to erased content. Current grants, external-effect outcomes, and runtime incarnations are revalidated before work resumes: a preserved reading position may reopen a document; a preserved call record must not turn on the microphone.

Snapshot exclusion is a persistence boundary. It cannot protect against any principal with world-root authority; if that deployment is chosen, its enforcement and authoritative records must live beyond that authority (§12).

**Open:** store engine beyond milestone one (M1 commits to a JSONL log with a SQLite cache, §22; the protocol, not the engine, is the commitment); per-activity restore policy; retention/erasure horizons and their reconciliation with the record and fork rights ([[Constitution]] I.8 vs V.6 — Article I precedes).

---

## 14. The host side

Small, boring, non-agentic — the supervisor of earlier drafts, plus the keep and brokers named as what it contains. Sketch API:

```
# supervisor
start_vm() / stop_vm() / snapshot_world() / restore_world()
start_yard(inputs) / health_check() / backup_jeff_state()

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

Properties that protect it: a few kilobytes of state; readable in an afternoon; unreachable from the world except through these typed requests; executes nothing it is handed; keys in the device's secure enclave where available; journal append-only and signed.

---

## 15. Secrets and external authority

JEFF normally knows **references to credentials** — `github.alex`, `postgres.project_x` — never plaintext. A worker needing access requests a scoped capability; the credential broker prefers performing the operation itself over handing out tokens; where tokens are unavoidable they are short-lived, narrow, and sender-bound where supported. Host filesystem and external network resources cross explicit broker boundaries every time. The person's host filesystem is never broadly mounted into a world where JEFF has root.

---

## 16. Self-modification

Agora is designed so JEFF and the person progressively reshape the environment together. Most of the shell is eventually hot-swappable — layout, navigation, panels, search, grouping, visualizations, interaction modules. Critical components change cautiously: compositor core, renderer initialization, recovery interfaces, and everything on the host side (which JEFF cannot modify at all; its update channel is the person's, separate from world packages).

All significant change runs the candidate pipeline:

```
current Agora
    → JEFF + coding worker build a candidate
    → run it nested / staged in a candidate world-line (the yard)
    → human + JEFF test it; conformance cases pass
    → promote or discard — promotion is an event; discard leaves the witness's lesson
```

Vocabulary changes (facet types, verbs, lenses) ride the same pipeline as [[Extensions]] bundles. Approvals bind to exact digests; new permissions or changed effects require fresh review; a promoted candidate runs with the same restricted runtime authority as everything else. This is how Agora becomes progressively self-hosting — a growth capability, never a requirement that ordinary objects participate in software creation.

---

## 17. The web

Authoritative contract: [[The Web]]. Websites are not static; they are remote, opaque, and owned by others. Agora never makes a remote service share its truth — it makes **your side of the web into objects.** Four tiers: any page, wrapped (URL, DOM, a frozen **cast** that anchors and highlights pin to, since live pages shift underfoot); services with APIs, adapted into proxy entities with provider bindings, local proposals distinct from observed remote facts — the existing MCP ecosystem is consumed directly as this layer, with effect classes assigned at the boundary; optionally, Agora-aware sites exposing an object endpoint, on which nothing depends; and, deepest, **sites made of Agora** — publishing as a grant of read on a collection rendered by a public lens, so editing the site is editing objects in place, visitors without Agora get HTML, and visitors with Agora get the objects. The browser is a lens whose verbs carry honest effect classes; `page.submit` is a one-time effect with an operation id, which is what makes a daemon safe on the web. Browsing history is attention data under the strictest class. Wrap platforms; clone nothing; build native replacements only where objects change the product.

---

## 18. Rooms and sharing

The multiplayer layer (design essays: [[Rooms]], [[Democracy]]; mechanics distributed through the references). A **room** is a shared world-line — a replicated log with several witnesses — and an entity with facets, so it can be decorated, remembered, and kept by a household agent that belongs to the room and holds room context only. Objects enter by lending or giving (§4). Presence is mutual and ambient with the line drawn structurally: legible presence, private content — your focus visible as warmth, your overlays never. Each member's daemon weaves the shared log into its own memory; a rolled-back experiment is forgotten by the room and remembered differently by every witness. Dissolution forks the world-line: both sides keep the whole past, guests go home, grants lapse, and nobody deletes history out from under anyone. Room authorization during disconnection is a decided-before-shipping question ([[Security]] §8; current lean: one authorization writer per room, disclosed, with decentralized causal authority as the research alternative). The civic layer above rooms — squares, sortition, consensus-mapping, the human franchise — is designed in [[Democracy]] and entrenched in the Constitution; none of it is needed for the first years.

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
9. The event log is the truth; events are intents; every other store is a rebuildable cache.
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

**Status: approved direction, September 5, 2026.** M1 established the initial object layer. Its historical build contract remains in `BUILD_PROMPT.md`; it is not a permanent restriction on future verbs, facets, or interfaces. The initial [[Personal Lenses]] experiment and reliability repairs are implemented. Alex clarified that inventing unanticipated abilities during use is essential; [[Executable Components]] defines the approved executable authorship slice.

**The immediate experience.** Ask JEFF: “Can you make it so I can click and drag the notes around?” JEFF should author the behavior as executable source stored in the world, exercise a candidate, and activate its exact revision. A different follow-up should revise that component and introduce another interaction and a discoverable action. Existing objects retain their identity; changes still flow through recorded verbs. The runtime implements general input, rendering, and scoped effects; the requested behavior must come from authored code. A fixed catalog of templates alone does not fulfill the vision. Live-model success, usability, persistence, and recovery need explicit evidence alongside runtime tests.

**The display direction.** The person and JEFF should eventually be able to reshape nearly the entire workspace: layouts, lenses, navigation, typography, and the conversation panel itself. The chat panel is not editable by the first lens. Over time it can participate in the same view system. A small dependable recovery surface retains stop, default-display restoration, and authoritative permission information. Editing a view does not itself confer access to conversation contents, authority to rewrite history, or permission to disclose data.

**M2 onward is a feature horizon, not an implementation sequence.** These are capabilities we would like to explore. Their grouping conveys purpose; it does not prescribe order, dates, or an architecture to build before useful experiments.

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

**Evidence and status.** Distinguish implemented and tested contracts, selected directions awaiting implementation, open experiments, and aspirations. Passing tests supports the cases they exercise, not every promise in the design. Maintain focused regression tests for replay, refusal, boundaries, anchors, version conflicts, recovery, and lens activation. The review in [[holistic-assessment-2026-09-04]] records the earlier baseline; it is not the current implementation status.

---

## 23. Open decisions

**Resolved since the last revision** (see the named documents): object schema shape, reference semantics, copy verbs, residency → [[Objects and Facets]]. Spec/status contract, drift, conflict → [[Reconcilers]]. Authority choices, rollback-vs-grants, and hosting constraints → [[Security]] + addendum; the future world-root/client choice remains open. Vocabulary change → [[Extensions]]. Web posture, MCP as the adapter layer → [[The Web]]. Storage direction: event log + SQLite-class store + real filesystem.

**Committed for milestone one** (§22; reasons in `DECISIONS.md`): JEFF's provider is the Anthropic API; the log is JSONL; the store is SQLite; `core.text` is Loro; the anchor locator is a position-id range plus creation revision plus quoted text; projection tiers are `[12, 60, 250, 2000]`. These are milestone commitments, each one file away from changing, not frozen decisions.

**Still deliberately open:**
- initial JEFF model (the provider is settled for M1); voice model; one model or several across loops;
- memory architecture in the concrete: the witness graph's schema; latent vs textual vs parametric; continual learning; personal adapters and their rollback;
- exact serialization and IDL for facets and events beyond M1's JSON; CRDT selection and anchor locator formats beyond M1's Loro choice;
- worker/job protocol; nursery thresholds;
- room replication and offline authorization protocol (decide before shared rooms);
- salience parameters, decay curves, budget defaults (decide on the prototype);
- search/index implementations; embedding model;
- self-modification approval policy details; compositor implementation; local vs cloud inference split;
- retention, erasure residuals, and their constitutional reconciliation;
- the evolving UI and interaction style: useful direct interaction and accessible controls are part of the experiment from the start, alongside broader display composition.

---

*Every section traces to a companion document or essay in this repository; where it does not, it is marked open. The Constitution remains authoritative. Fork it if we ever forget that.*
