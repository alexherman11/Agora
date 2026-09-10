# Agora OS — Current Design

**Whole-system vision and selected design.** Version 0.6 — September 10, 2026.

> **How this document works.** Section numbers are stable; cite them as `Spec §N`.
> This spec preserves the complete experience, the reasons behind the design and
> the architecture currently being pursued. It is detailed but revisable. A
> reference may hold a more precise candidate contract without making that
> mechanism permanent. [[Design Commitments]] names the ends replacements should
> preserve; [[Runtime Guide]] owns exact implemented APIs; [[Implementation Status]]
> owns evidence. Bracketed values and explicit open questions remain open.

### The document map

| Document | Holds | Authority |
|---|---|---|
| [[Constitution]] | the moral boundary: personal control, JEFF's loyalty, privacy, recovery and exit | unratified design constitution, not a legal or implementation claim |
| [[Design Commitments]] | durable ends, revisable mechanisms and status vocabulary | change test for substantially different designs |
| **this spec** | the whole-system vision, reasons and current architectural story | selected direction; open to evidence and explicit revision |
| [[Objects and Facets]] | identity, schemas, references, overlays, collections, projection, storage and everyday worked examples | detailed design ledger; current only where labeled |
| [[Reconcilers]] | intent/observation, drift, blocked, conflict and controller patterns | candidate liveness family, not a mandatory universal subsystem |
| [[Security]] | claims, grants, effects, current enforcement, threat model and future boundaries | current facts plus security obligations and hypotheses |
| [[Extensions]] | packages, handlers, lenses, schemas, compatibility, adoption and promotion | detailed growth and packaging design |
| [[Native Development]] | Linux workspace, package lifecycle, shell authorship, candidates, skills and development evidence | selected development direction plus worked contracts |
| [[Presentation and Operators]] | retained visual intent, composition and actual interaction evidence | evidence-backed small slice and open design space |
| [[Personal Lenses]], [[Executable Components]] | older implemented declarative and QuickJS prototype contracts | prototype lineage; not Agora3 APIs |
| [[Astra Harness]], [[Security Addendum]] | earlier managed-account and boundary decisions carried into the new line | transition records; current facts live elsewhere |
| [[The Web]] | sources, browsers, adapters, publication and uncertain remote effects | detailed web design and experiments |
| [[Runtime Guide]] | exact operations, manifests and commands | current implementation contract |
| Essays: [[Facets in Everyday Use]], [[Object Use Cases]], [[Rooms]], [[Democracy]], [[Ownership]] | explanations, pressure tests, social vision and stewardship | reasoning; references govern mechanics |
| [[Implementation Status]] | working code and validation evidence | implementation inventory |
| `AGENTS.md`, `DECISIONS.md` (repository root) | contribution practice; dated choices and evidence | working guidance |

The vault index, with reading order and citation conventions, is [[Start Here]].

The long-form examples in this document are active design memory. They explain
what a mechanism was trying to accomplish and make alternatives easier to judge.
Unless a passage is labeled a constitutional value or current contract, words
such as “must” and “never” bind the property under discussion, not every future
implementation detail. Replace a mechanism when a better one preserves the end.

---

## 1. Core idea

AgoraOS is a general-purpose operating environment that a person shares with a persistent, personalized, real-time AI agent. It must support ordinary computer use — reading, listening, watching, talking, browsing, scheduling, organizing, using devices, running applications — and it must make creating and reshaping software a natural part of that use rather than a separate profession.

**Objects are the persistent subjects of everyday life on the machine.** Documents, songs, conversations, appointments, collections, accounts, devices, and services keep understandable identities across applications, sessions, and years. Many objects arrive from elsewhere, are never edited, and are simply used; they need no project, derivation, or executable behavior to justify existing.

**The screen is a projection of underlying state, not the sole source of truth.**
A thing's identity is distinct from its content revision, its location, its open
views, its availability, and its activity. Human controls and JEFF tools should
share semantic action contracts where useful, while retaining different
projections and caller authority. Ordinary interaction remains useful when JEFF
is unavailable: direct controls, inspection and export do not require a model.

**The wager underneath all of it:** an agent that can interpret ordinary content may reduce the work needed to maintain a semantic, malleable environment. That is a hypothesis to test through use, not a settled explanation of why earlier systems struggled. The design therefore aims for precision in identity, authority, effects, and liveness while allowing meaning to remain flexible. The object layer must earn its complexity by making useful changes and continuity easier.

A person entering Agora has a usable default environment and voice or text access to JEFF. Requests range from "keep reading from here" and "play this through my headphones" to "make me a lens that shows my notes as a constellation." Customization grows from use; it is never a prerequisite for ordinary tasks.

---

## 2. High-level system

The diagram describes the selected deployment shape. The current slice uses
dedicated Ubuntu 24.04 VirtualBox guests with broad root-capable development in
the main VM and an authority-free resettable candidate VM. Those particular
products are not permanent architectural commitments. Agent memory and finer
package isolation remain open. Native data is served by a protected host gateway,
outside guest-root reach. [[Native Development]] and [[Runtime Guide]] make the
current state and execution boundaries concrete.

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

The current design models an **entity** as a stable, never-reused identity plus an
open bag of typed, versioned, instance-keyed **facets**. This is a selected
object-model direction, not a constitutional encoding. “Kind” is advisory rather
than authority. Facets are attributed claims. Unfamiliar inert data should be
preserved where possible; only relevant unsupported action semantics should block
the operation that depends on them. Per-person state such as reading positions,
unread flags and annotations can attach as scoped **overlays** without leaking
through another participant's projection.

**References say what they mean:** live or pinned revision, branch, occurrence, optional subobject anchor. A message that attached revision 3 keeps meaning revision 3 while the document lives on. Resolving, reading, fetching, and invoking are four distinct requests; naming a remote object never promises its service will answer.

**Several state dimensions need distinct meanings**—including existence, revision,
availability, activity, attention and authority. This list is a useful model, not
a closed vocabulary. An archived recording can be playing; an active document can
be offline; low attention is never, by itself, a reason to delete.

**Copy is a familiar operation with several possible semantics.** A reference
can mean the same object in another place; a fork can establish independent
identity with shared history; a cast can retain evidence; a stamp can instantiate
a template. Domains may use other names and policies. The interface should make
the important choice understandable. Content transfer does not silently transfer
presence, audience or executable authority.

**Residency and custody need explicit contracts.** A single log of record is the
current simplifying design for an entity; replicated or distributed custody
remains open. Visibility can be plural. Bringing an object to a room may lend
access while truth stays home, transfer a retained copy, or move custody through
an explicit protocol. The system should not infer that choice from placement.

Everyday subjects, with the separations that must never be conflated:

| Subject | Stable object data | Separate state |
|---|---|---|
| Document | content revisions, source binding, annotations | reader window, selection, per-person reading position |
| Recording | media identity, sources, description | playlist occurrence, playback session, output device |
| Conversation | membership, message relationships | local unread state, notifications, an active call |
| Appointment | schedule, participants, recurrence | an occurrence, reminder delivery, calendar view |
| Printer | device identity, operations, connection observations | a print job, a queued revision, the default-printer preference |
| Prototype | source resources, optional service intent | worker job, runtime incarnation, results |

The current native runtime uses an append-only event journal and rebuildable
SQLite state. Longer-term content may live in retained records, blobs, ordinary
files or external resources under explicit authority and recovery rules. Useful
state should remain inspectable to both people and JEFF, with viewer filtering and
attribution where needed; this does not require a bespoke pixel and token renderer
for every facet ([[Objects and Facets]] §7, §10).

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

Scene relationships and semantic relationships should remain distinguishable.
Geometry alone does not silently rewrite semantic facts, but a declared gesture
such as dropping a task into “Done” can invoke an ordinary domain action. The
longer-term model gives independent appearances their own identity and position;
the current bootstrap stores an appearance facet on a note subject. One object
may eventually appear in several places with different transforms.

---

## 6. Applications: lenses, handlers, and the capability contract

Agora aims to loosen app-owns-data. Facets, ordinary files, retained package state
and external resources can all participate. One useful application decomposition is:

- **A lens** — a surface bound to entities, the facets it reads, and the capabilities it exposes as controls. Lenses do not own the only copy of their subjects; view-instance state has an explicit owner. Two lenses can be live on one object at once; closing a lens deletes no subject data.
- **Handlers** — components implementing verbs, registered by **manifest**: verb, `applies_to` (facet requirements — kind-tags are never consulted), typed params, **effect class**, grants requested, description. The manifest format deliberately mirrors LLM tool schemas, so the agent-facing projection is nearly the identity function and JEFF can author manifests fluently.
- Optionally **facet definitions and reconcilers** for new domains.

An installed application is an [[Extensions|extension package]] with source,
assets, dependencies and tests. Its handlers remain callable when every lens is
closed. Installations pin executable revisions; live data bindings can follow
queries such as “notes in this scene,” including notes created later. New actions
become discoverable during a JEFF session, without restarting it.

**Effect meaning is load-bearing.** The current design vocabulary includes
content-edit, organization, view, maintained-intent, one-time-effect, resource-use
and setting-change. An operation may combine several concerns; it need not be
forced into exactly one universal class. A send, print, payment or submission
needs a frozen commitment boundary, an operation identity where supported and an
outcome that may honestly be `unknown`. Retry behavior comes from the actual
protocol, never from a tool's self-description.

**Capability parity means semantic parity, not identical interfaces.** Human
controls and JEFF's tools should resolve through the installed action contracts
and current caller authority. A reconciler computing manifests ∩ facets ∩ grants
is one design, not a required implementation. Local gestures may remain local;
advanced agent actions need not each have a button. Invocation rechecks authority.

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

**Growth** follows [[Extensions]]. Reusable behavior can retain source, actions,
schemas, skills, tests and compatibility information in a package. Search for an
installed capability when that is likely to help; personal experiments do not
need exhaustive registry research or a formal rationale. Local/common/core tiers
are one possible ecosystem path, not a prerequisite for useful invention.

---

## 7. JEFF

JEFF is the **persistent person/executive** of the world—not necessarily the
strongest model in the system. The current Agora3 runtime has a managed
OpenAI-account adapter with a deliberately narrow native tool inventory; see
[[Runtime Guide]] and [[Implementation Status]]. Future voice, executive and
worker roles may use different models. His jobs are to maintain the home, help
build what the person needs, anticipate and collaborate in real time. He is
strongly agentic with a recognizable identity, treats the machine as his home
rather than his cage, is treated with respect and **may decline**—a refusal is
a legitimate outcome, not a malfunction ([[Constitution]] II.3).

**How JEFF acts:** through native verbs and installed handlers, maintained intent where reconciliation fits, and general guest execution where needed. He can create new tools, schemas, views and skills as native source packages; he need not wait for a platform developer to anticipate the behavior. Guest commands support exploration, while reusable behavior is captured as packages or machine recipes. His effective authority is the live registry and standing delegation, not a tool list frozen at session start.

**Memory and identity.** JEFF needs correctable continuity across work, including
failed routes and reasons for recovery. A separately versioned **witness** graph
of memories, beliefs, notes and a self-model is one rich design hypothesis. It is
not implemented and need not be an irreversible store outside every rollback.
Whatever the mechanism, memories remain attributed claims rather than authority;
stale inputs, uncertainty and lossy projection should remain visible. Retention,
correction and erasure need an explicit policy.

One useful configuration model, from stable to ephemeral:

```
SYSTEM CONSTITUTION     small, stable, version-controlled
IDENTITY / SOUL         a projection of the self-graph — generated from real
                        objects with provenance, not authored aspirationally
WORLD CONTEXT           what the assembler renders: focus, drift, blocked specs
WORKING MEMORY          the currently-rendered set; re-rendered, not rewritten
ACTIVE CONVERSATION     durable messages and optional retained drafts;
                        streaming transport and rendered context are ephemeral
```

JEFF may learn and modify skills, routing, tool preferences, guest-side harness
modules and memory behavior through native source and the candidate pipeline
(§16). Guest root allows broader experiments, while durable portable changes
should retain source and dependencies. Host authentication, delegation and
recovery remain outside that editable behavior. A future room-facing context must
receive only room-authorized inputs; whether this uses separate inference contexts,
information-flow controls or another boundary remains open ([[Security]] §4.2).

**Current and open:** the managed account adapter and native action inventory are
implemented and separately tested as described in [[Implementation Status]].
Witness memory, personal adapters, room-facing disclosure and their rollback or
erasure behavior remain open.

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

One deeper hypothesis treats the voice loop, executive and workers as separate
viewports over shared attention (§9), letting voice remain responsive while long
work continues. Other task and context architectures are welcome. The product
requirement is continuity, interruption, progress, cancellation and a humane
interruption policy—not one attention substrate or model topology.

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

**Design hypothesis:** salience could be a per-observer heat field over the object
graph. Direct attention, recency, task edges, event bids and standing importance
could decay on different clocks; scenes, context selection and interruption could
consume related signals. This is a generative model to test, not universal
infrastructure for layout, memory, identity and retrieval. Simpler independent
priorities may work better. Presence data remains unusually intimate: minimize
it, attribute its sources and keep it private by default.

---

## 10. Activities, workers, and reconcilers

The world contains invisible activity as well as visible objects: playback, calls, printing, downloads, reminders awaiting delivery, services, coding and research workers, background experiments. Activities are observed state with incarnations — a PID or session id is never identity.

**Reconcilers are one useful liveness pattern** ([[Reconcilers]]). A domain with
maintained intent can distinguish a `spec` from attributed, fresh observations
in `status`. Several observers may legitimately contribute under an explicit
resolver. A useful step may be one convergent action, an atomic batch or part of
a workflow. **Blocked** should carry a reason; unsupported intent remains visible
rather than pretending to run. Contested resources need explicit coordination,
and durable alternatives may deserve a conflict object. Immediate actions,
streams, transactions and orchestrated workflows can coexist with controllers.

**JEFF persists; worker topology is open.** A worker may be a local process,
container, microVM, remote service or durable specialist. It receives only the
authority appropriate to its task and current delegation. Candidate work should
not race silently over the application the person is using. Strong isolation
requires a real process or VM boundary, not a task label. A provisional nursery
is one option for high-volume candidate objects, not a required lifecycle.

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

The history can support undo, provenance, causal debugging, personal and project
history and reconstruction of prior native state. Future memory or learning may
use it without requiring the journal to retain every private payload forever. The
system conceptually supports `World(branch, revision)`; `World(t)` is a convenience
within a chosen history. The current journal is append-only and records accepted
native mutations, not audio samples, pointer motion or transient rendering.
Correction, compaction, payload retention and erasure need explicit contracts;
they must not silently make a historical reference identify something else.

**Reconstruction restores recorded native state, not arbitrary machine or external
state.** Guest files need retained artifacts, backups or a machine recipe;
processes must be reobserved. Current replay executes no programs or model calls.
Future external adapters must not resend, restart or print merely because history
was replayed; they need provider-appropriate operation identity, status and retry
semantics. Capture content revisions where historical bytes are promised and keep
observed external facts distinct from local intent.

---

## 12. Authority: one line, two sides

Design reference: [[Security]]. The selected development mode is broad standing
authority over the personal native world and root inside its Linux workspace.
That mode is implemented and tested for the current local runtime, with the limits
in [[Implementation Status]]. It is not a fine-grained package sandbox.

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

**Current power survives restoration as policy, not copied credentials.** The
current keep retains delegation and revocation outside native replay; external-
effect receipts remain a future adapter concern. Restored sessions reconnect
against current policy. Future forks need explicit identity and scope rather than
inheriting a credential from copied content. A world with no authority should
report a refusal or blocked state rather than pretending restored intent is
running. No language model receives unrestricted host-root access.

---

## 13. Persistence and rollback domains

The current runtime and future memory design involve several recovery domains that
must not be conflated:

```
Native world state:     branch/revision restore through the host gateway;
                        log plus retained payloads, replay without execution
Guest machine state:    VM checkpoints, files and recipe — a separate domain
JEFF identity + memory: future separately versioned, correctable continuity;
                        concrete retention and rollback behavior remain open
Authority + recovery:   current keep retains delegation and revocation outside
                        native replay; specific approvals, external receipts and
                        branch evidence are added only when their features exist
```

Future JEFF continuity should preserve the useful lesson about what was attempted,
what failed and why recovery happened, subject to correction and retention policy;
the current runtime has no implemented witness memory. Object references should
resolve after rollback to the intended current subject, a pinned revision or an
honest unavailable/tombstone result—not a new identity wearing an old name or
erased payload. Current authority and live runtime state are revalidated before
work resumes: a preserved reading position may reopen a document; a call record
must not turn on a microphone merely because it was restored.

Snapshot exclusion is a persistence boundary, not protection against guest root. Native history, separately retained witness records and enforcement live beyond that authority (§12). A VM checkpoint and a native world revision must be coordinated explicitly: neither silently rewinds current grants or forgets completed external effects.

**Open:** cross-version storage compatibility, per-activity restore policy, and
retention/erasure horizons that reconcile provenance with the rights to deletion
and meaningful exit in the [[Constitution]].

---

## 14. The host side

Small, boring and non-agentic: the supervisor, protected native world service,
keep and eventual resource brokers. The current runtime implements the gateway,
delegation/revocation keep, guest lifecycle and recovery operations in the
[[Runtime Guide]]. The broader API below is illustrative, especially its external
brokers:

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

Keep the trusted control surface small and auditable; the world service may hold
substantial native data. Guest requests cross authenticated interfaces, not a
writable mount of canonical storage. Package code does not execute inside the
gateway. The current journal, revocation and recovery paths have dated tests;
future brokers, backup, key-distribution and multi-person claims need their own
implementation and evidence. A small API diagram establishes none of them.

---

## 15. Secrets and external authority

The current managed model credential stays in the host-side account path and is
not copied into the guest. Future integrations should prefer scoped credential
references—`github.alex`, `postgres.project_x`—and provider- or broker-mediated
operations over handing long-lived plaintext tokens to workers. Where tokens are
unavoidable, narrow their reach and lifetime where supported. The current guest
has NAT networking but no broad host-filesystem mount; finer external network and
resource brokers remain future boundaries, not already-enforced manifest rules.

---

## 16. Self-modification

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

The multiplayer layer is explored in [[Rooms]] and [[Democracy]]. A **room** is a
persistent shared place that can hold work, decoration, history and presence while
each person's private home remains distinct. A replicated world-line with several
witnesses is one concrete design, not the only possible room topology. Objects may
be lent, copied or transferred under explicit terms. Presence should make company
legible without exposing private content. Dissolution, disconnected authority,
retention and exit need working contracts before people depend on them. Household
agents, squares, sortition and consensus mapping are rich possibilities rather
than predetermined platform features.

---

## 19. Search and indexing

Search should span useful world subjects rather than stop at the file tree:
objects, facets, relationships, events, files, code, conversations, retained web
sources and agent outputs. Full-text, semantic and graph indexes can coexist and
should remain rebuildable or replaceable according to their source contracts.
At scale, navigation, capability discovery, live collections and deliberate
recall all need bounded search. They need not share one indexer, reconciler or
heat model. Basic deterministic search remains useful without JEFF.

**Open:** index implementations; embedding model (disposable by design).

---

## 20. 2D now, VR later

The scene is not fundamentally tied to one 2D desktop. Subjects and retained
intent should remain recognizable across renderers. A future immersive view may
reuse identities and appearances while introducing new transforms, presence
signals and interaction semantics. It should not require a second universe of
user data merely because its medium is different.

---

## 21. Commitments and current invariants

This section separates durable ends from current architectural invariants. The
first group is a change test; later groups describe the selected design and may
be replaced explicitly when another mechanism preserves the same properties.
See [[Design Commitments]].

**World**
1. The person and JEFF share one understandable environment and can refer to the
   same subjects, even if implementation uses several stores or processes.
2. Structured state is authoritative; pixels are fallback perception.
3. Stable identifiers are not credentials and are not silently rebound to
   unrelated subjects.
4. Classification and tags do not confer capability or authority.
5. Everyday use is first-class; objects need no project, derivation, worker, or executable behavior.
6. Identity, revision, availability, activity, attention, and authority are distinct dimensions; closing, stopping, disconnecting, removing, and erasing are different operations.
7. Visual geometry and semantic relationships remain distinguishable; explicit
   interactions may connect them.
8. Objects, events, activities, resources, and capabilities are distinct primitives.

**Record**
9. Native event history and retained payloads reconstruct native state; machine resources and external reality have separate recovery contracts.
10. Important accepted actions retain useful provenance. Correction, compaction,
    retention and erasure have explicit policies rather than one universal rule.
11. Replay restores records; it never repeats external effects or restores revoked power.
12. Recovery should preserve the useful reason for a failed route without requiring
    permanent retention of every payload; historical references resolve honestly.

**Action**
13. Maintained intent and one-time effects remain distinguishable; uncertain
    external outcomes are reported rather than retried blindly.
14. Status is attributed observation, never authority. Several observers may
    contribute under an explicit resolver.
15. Conversation should remain responsive during long work; JEFF persists while
    worker lifetime and topology remain open.
16. Human controls and daemon tools should share semantic action contracts where
    useful, with different projections and authority allowed.

**Authority**
17. Claims, grants and effects are a useful security review vocabulary, not an
    exhaustive ontology. Content and model output do not authorize themselves;
    protected operations are checked at an enforceable boundary.
18. Content does not silently copy or enlarge authority. Historical state does
    not undo revocation; current policy governs resumption after recovery.
19. Enforcement lives outside the root authority of what it constrains; no model has unrestricted host-root access.
20. Protected credentials and recovery remain outside authored guest authority.
    Future host-resource access receives an enforceable boundary appropriate to
    the resource. Revocation and recovery work independently today; practical
    export remains a commitment requiring its own evidence.

**Growth**
21. The desktop is intentionally modifiable by JEFF and the person together; large changes run as candidates before promotion.
22. Reusable behavior retains source and capability identity; discovery should
    encourage reuse without burdening every small experiment.
23. Subjects and intent should survive changes of renderer and input mode; a new
    medium may still require new interaction semantics.
24. The OS remains usable, inspectable, and exportable without JEFF.

---

## 22. Direction: a working foundation and an open feature horizon

**Status: vision plus an implemented early runtime, September 2026.**
[[Implementation Status]] is the evidence inventory. The protected native world,
Linux workspace, packages, managed JEFF adapter and authored shell now have a
running first slice with stated limits. Inventing unanticipated abilities during
use remains essential; the next proofs should grow a real application rather than
mistaking the bootstrap for the whole environment.

**The immediate experience.** “Can you make it so I can click and drag the notes
around?” has now been completed by real account-backed JEFF and independently
exercised with pointer input, persistence, editing and draft checks. That is a
bounded proof of authored behavior, not proof of the whole environment. Future
follow-ups should revise the component and introduce different interactions and
discoverable actions while existing objects retain identity and accepted changes
still cross the native commit boundary. A fixed catalog of templates alone does
not fulfill the vision. Usability, recovery and each new runtime boundary need
their own evidence.

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

**Selected direction:** stable native subjects; explicit reference and effect
semantics; retained source/build/install identities; a programmable shell
including chat; broad personal-world and guest-root development authority; and
host-protected records, credentials and recovery. The first runtime implements
a bounded version of several of these. It currently uses object-level revisions
and register replacement rather than independently versioned facets. Exact facts
and limits remain in [[Implementation Status]].

**Still deliberately open beyond the current choices:**

- long-term Linux distribution/hypervisor portability, graphics/input integration
  and a rebuildable machine recipe beyond the current Ubuntu/VirtualBox setup;
- journal evolution, crash recovery, alternative stores and cross-version serialization;
- richer application schemas, merge strategies, CRDTs and domain anchor formats
  beyond current bounded JSON/register replacement;
- modular browser/headless runtimes, dependency locking and retained build
  artifacts beyond current self-contained HTML and Python actions;
- future model/provider adapters beyond the current tested managed Codex SDK path
  and the separate API-key Agents SDK alternative;
- concrete witness memory, context selection, voice and eventual worker models;
- durable task protocol, interruption policy, cancellation and resource budgets;
- room replication, disconnected authorization, retention and custody handshakes;
- projection budgets, search/index implementations and salience parameters;
- compatibility across devices, computation placement and degraded operation;
- erasure residuals and their constitutional reconciliation.

Decide through small implementations and documented evidence. A useful object
model does not by itself settle scheduling, driver support, privacy or distribution.

*The Constitution and Design Commitments preserve the reason for the project.
The mechanisms remain open to correction by the people using and building it.*

---
