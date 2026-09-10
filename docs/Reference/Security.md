# Security

**Agora reference documentation — how the world stays safe while staying open.**
Restored design reference, revised September 10, 2026. Companion to [[Objects and Facets]], [[Extensions]], [[Native Development]], [[The Web]], and the Constitution.

> **Status.** The authenticated native gateway, append-only journal, current
> delegation and revocation, protected runtime facets, independent recovery
> controls, main development VM and authority-free candidate VM are implemented
> and have dated evidence in [[Implementation Status]]. The claim/grant/effect
> analysis below is a security review vocabulary and future design, not an
> assertion that its complete framework, every broker, shared rooms, package
> isolation or information-flow enforcement exists. Bracketed choices remain open.

> **Development profile.** Broad local-world and guest-root authority is the
selected initial direction. The protected gateway and keep constrain the guest's
outer authority. Strong per-package isolation and information-flow enforcement
require additional runtime boundaries; they are not supplied by guest-root mode.

---

## 0. Summary

The useful review lens has three nouns and two forbidden crossings. A **claim**
is something asserted; a **grant** is current authority; an **effect** is something
that happens to a protected resource. The categories need not describe every
internal datum or local gesture to do their job. **Claims do not become grants**
through processing, and protected effects do not happen merely because content
asked for them. Authority is checked at the boundary that can enforce it. Content
transfer does not transfer authority, and historical state does not revive revoked
authority; current standing policy may still authorize resumed work after restore.
Enforcement runs outside the root authority it constrains, and broad guest access
is not proof of isolation among guest processes. Replay reconstructs recorded
state without re-performing model calls or external effects. The rest of this
document applies that lens to likely ways in.

---

## Contents

1. [What is different here](#1-what-is-different-here)
2. [Three nouns, two crossings](#2-three-nouns-two-crossings)
3. [Compartments](#3-compartments)
4. [Frameworks for keeping order](#4-frameworks-for-keeping-order)
5. [The coverage map](#5-the-coverage-map)
6. [What the daemon may do](#6-what-the-daemon-may-do)
7. [Deployment truth](#7-deployment-truth)
8. [Tensions that need explicit policy](#8-tensions-that-need-explicit-policy)
9. [Incidents](#9-incidents)
10. [Drills as boundaries arrive](#10-drills-as-boundaries-arrive)
11. [Invariants](#11-invariants)
12. [Open decisions](#12-open-decisions)
13. [Glossary](#13-glossary)

---

## 1. What is different here

Standard security assumes code is the thing that acts and data is the thing that is acted on. Agora breaks that assumption six ways, and each one is a new door:

| New condition | New door |
|---|---|
| A resident model with high authority reads untrusted content all day | Prompt injection is ambient, not an edge case. Every facet, projection, page, and tool description is an instruction channel. |
| Content and code travel through the same channels | A note can become a program; a helpful tool can spread like a rumor. |
| Memory survives what the world forgets | Poison that reaches the witness outlives rollback. |
| Everything renders to tokens | Projection is both an injection surface (inbound) and a disclosure surface (outbound). |
| Attention is a computed field | Whoever can make a thing hot buys tokens and interruptions. |
| The system rewrites itself | The surface that asks for consent is itself replaceable software. |

The right response is not more rules. It is fewer, placed where a participant who deliberately disobeys them cannot reach.

---

## 2. Three nouns, two crossings

### 2.1 The nouns

| Noun | What it is | Where it lives | Who makes it |
|---|---|---|---|
| **Claim** | anything anyone says: facet bodies, edges, projections, summaries, memories, manifests, page casts, tool descriptions, presence, room events from peers | the world, rooms, the witness store | anyone |
| **Grant** | current authority associated with a principal, target, operation and applicable limits | the protected keep or another enforceable authority boundary | the person, standing policy, or a delegate acting within authority |
| **Effect** | a change to a protected resource: native state, bytes, credential use, network activity, a delivered message, money or a device | the boundary responsible for that resource; external systems may add their own protocol | an admitted native commit, broker, adapter or provider operation |

The daemon's memories are claims. A signed package's manifest is a claim. An ACL field displayed on an object is a *projection* of a grant, not the grant. A reconciler's status is a claim from that reconciler. Grants originate in the person's delegation and can be narrowed by authorized delegates. Broker receipts record a dispatch and observed outcome, including unknown; they do not necessarily prove that the intended external result happened.

### 2.2 The crossings

**Claim → grant is forbidden.** No processing of a claim produces authority: not summarization, not repetition, not being remembered, not being signed, not being installed, not being popular, not being understood by newer software. A facet that says "the owner approved this" is a facet that says that.

**Claim → protected effect without authority is forbidden.** A request does not
authorize itself. The check happens at an enforceable crossing — today, for
example, the authenticated native commit boundary; in future integrations it may
be a file bridge, process launcher, outbound connector, provider adapter, device
service or credential broker. A tool wrapper that its caller can bypass is not
such a boundary.

Every attack in §5 is an attempt to make one of these crossings, or to make a grant leak, copy, widen, or resurrect. This is a review lens, not a proof that the threat model is exhaustive.

### 2.3 Properties of authority

- **Bound enough for the effect.** Identity, target, operation, destination,
  payload, cost, time and delegation depth are possible constraints, not fields
  every local edit must carry. An object id is a name, never a credential.
- **Content transfer is not authority transfer.** A fork, cast, export, package or
  room message does not acquire executable authority merely by containing data.
- **Delegation does not silently widen.** A delegate stays inside the authority it
  was given. Composition must not manufacture a larger effective grant.
- **History is not current policy.** Restoring or forking recorded state cannot
  undo revocation. Current standing policy can deliberately reauthorize routine
  resumption; a fork may receive a separately scoped grant.
- **Checked at the relevant crossing.** Long-running or external operations may
  need leases, rechecks or provider-specific idempotency. A single local commit
  can instead be checked atomically at admission.
- **Inspectable.** Important authority and its scope should be legible and
  revocable through controls independent of the code being constrained.

---

## 3. Compartments

The development profile gives JEFF root in the Linux guest and broad native-world
operations. **Enforcement sits outside the root authority of what it constrains.**

| Compartment | Holds | Boundary |
|---|---|---|
| **Recovery surface** | stop, restore, delegation display, device enrollment and reserved human controls | Host-controlled; authored guest UI cannot replace it |
| **Keep** | standing delegation, revocations, consumed approvals, keys, security journal | Outside guest and world rollback |
| **Native world service** | canonical event history, retained native payloads, validation, query and projection | Host gateway only; no guest-writable canonical storage mount |
| **Brokers** | credential use, host resources and declared external effect channels | Check current delegation at the protected crossing |
| **Linux workspace** | JEFF runtime, shell, native applications, guest files, processes and legacy software | Root inside this guest; no implied host root |
| **Witness store** | separately retained memories and identity claims | Outside world rollback; no authority of its own |
| **Yard** | disposable build/test execution with explicit inputs | A native data fork is not a filesystem or network sandbox |
| **Gate** | import and replication validation | Validates and attributes content; cannot grant authority |

The whole root-capable guest is one compromise domain. A host can authenticate a
guest session and preserve its write history; it cannot assume a package identity
inside that guest is unforgeable against another root process. Broad native access
can still cause harmful valid edits, and root can alter guest files without
producing a complete semantic history. Provenance is not correctness.

Fine-grained package grants become enforceable only with a boundary the package
cannot bypass. A confined worker in a separate yard can have such a boundary;
a manifest alone cannot create one. The initial profile must disclose this
difference instead of presenting development convenience as multi-tenant isolation.

The person may grant broad guest network access. If so, an allowed channel can
carry any data the guest can read. Do not claim that labels reliably prevent
disclosure from an unrestricted root process. Narrow disclosure guarantees require
controlled egress and isolated contexts at the actual crossing (§4.2).

The host remains non-agentic. JEFF develops through native source operations and
explicit guest execution, not by editing the code that enforces host authority.
[[Native Development]] §2 specifies state placement and restoration.

---

## 4. Frameworks for keeping order

The following patterns are candidates for the boundaries that need them. The
current runtime already separates content from native authority and protects
recovery; it does not implement one universal trust lattice, confidentiality
type system, approval ladder, receipt protocol or salience policy.

### 4.1 Provenance does not turn content into authority

A future shared or imported-data boundary could attach a **trust class** that
survives transformations:

| Class | Meaning | How it is assigned |
|---|---|---|
| `owner` | the person said it, on the surface | surface only |
| `verified` | a broker did it and holds the receipt | brokers only |
| `attributed` | signed by a known principal (a member, a publisher, a reconciler) | gate, on validated authorship |
| `foreign` | unknown origin, or quarantined on import | default |

A conservative projector can retain source attribution and derive no higher
confidence than its inputs. The exact labels, combination rule and placement are
open. Raising confidence is a deliberate trusted operation, never a side effect
of summarization, repetition or popularity.

This prevents a record from becoming authorization merely through processing. It does not prove that a model cannot follow an injected instruction while using authority it already holds; bounded delegation, candidate tests and recovery still matter.

### 4.2 Confidentiality follows permitted recipients

Shared claims may carry permitted-audience constraints, often displayed as
`private`, `room:<id>` or `public`. These are not one linear ordering: two rooms
can have different audiences. A safe derived disclosure must respect every input
or use a separately authorized release. Exact information-flow tracking is a
possible mechanism, not something the current broad guest can enforce against
arbitrary root code.

The daemon keeps distinct private and room-facing contexts. A room context receives
room-authorized inputs only. A mixed private/room model session cannot be unmixed
by filtering a reply afterward; its outputs remain private-derived. Releasing a
specific fact follows the person's standing sharing policy or a new grant.

Known data dependencies and host-mediated outputs can be checked. Arbitrary root
code with broad data and network access can omit dependencies or transmit bytes
directly, so this information-flow contract is a requirement for scoped/shared
execution, not a guarantee of the development profile. Test the actual boundary,
including logs, errors, screenshots and candidate artifacts.

### 4.3 Distinct decisions, proportionate ceremony

Discovery, inspection, adoption, activation, execution, disclosure, delegation
and redistribution describe different consequences. They need not each become a
separate click, event type or approval prompt.

Seeing a tool in a room does not install it. A native installation explicitly selects which handlers enter the callable registry; this can be one authorized operation. Registration does not grant a resource. Executing it does not permit it to disclose what it read. Being useful does not let it recommend itself into another room. These are separate semantic decisions, which one standing delegation may cover together. The person may set policy for classes ("bounded viewers may render on entry") so ordinary life is not a wall of prompts — but no package approves its own rung.

### 4.4 Preserve intent and outcome without replaying effects

Replay reconstructs native state and never launches programs or repeats model and
external effects. For external operations, preserve enough committed input and
outcome to avoid guessing after interruption. Some providers support idempotency
keys or status queries; others leave an outcome `unknown`. A specific approval
may be one-use and payload-bound, while a standing grant can authorize a declared
class of work until it expires or is revoked. Historical records cannot un-revoke
authority.

### 4.5 Budgets, including attention where useful

Expensive or adversarial paths need enforceable bounds — tokens, compute, network,
durable writes, worker depth or input size — with recovery capacity that ordinary
work cannot starve. Which principals and descendants share a budget depends on the
runtime rather than on one required accounting model.

Attention can be budgeted too. One possible policy caps bids from untrusted sources
and reserves an interrupt path for security and recovery. It may use heat, priority
queues or separate controls; [[Agora Spec]] does not require one salience number to
govern attention, layout, memory and identity.

### 4.6 Protected changes to authority

The person's standing delegation authorizes routine work, including local package adoption and shell edits. Changes to host delegation, recovery and other reserved controls use a protected surface that world content cannot replace. When a particular external effect needs new approval, that surface shows the broker's view — identity from the keep, the exact object and revision, the payload digest, the destination, the effect, the cost — never a package's prose. "This" is resolved from authenticated owner input and frozen at approval; the broker rechecks at commit. Owner voice is captured separately from playback, room audio, and synthesized speech, and a familiar voice is a claim about identity, not proof of it.

### 4.7 Shared semantics, different interfaces and principals

Human controls and JEFF actions should reuse semantic operation contracts where
that reduces drift. They need not come from one literal list: a local gesture may
remain an implementation detail, an advanced action may have no button, and each
principal receives only its actual authorized capabilities. Equality means that
neither side is given a misleading model of the world, not identical interfaces.

---

## 5. The coverage map

The retained threat cases below identify attacks and candidate defenses. They are
not completed tests, a proof of prevention or an exhaustive ontology. Defenses
involving per-package isolation, output confidentiality or private room contexts
require scoped execution; guest-root development alone does not provide them (§3).

| # | Way in | The attacker needs | Required defense / limit |
|---|---|---|---|
| 1 | An instruction hidden in a facet, projection, page, or tool description | the daemon to treat it as the person's instruction | §4.1: preserve source attribution; claims cannot expand grants; misuse within an existing broad grant remains possible |
| 2 | Poisoned memory: a false approval remembered, surviving rollback | a memory to act as authorization | grants live in the keep, not the witness store; memories are claims with dependencies; source revocation quarantines dependents |
| 3 | A shared tool spreads: discovery activates it, a later update widens it | one decision to imply the next | §4.3 distinctions; owner-selected update policy; review authority expansion separately; content transfer is not authority transfer |
| 4 | Delayed activation: an unknown facet becomes executable when a handler arrives | data to become executable intent | activation and execution are separate grants; must-ignore governs data, never permissions |
| 5 | Composition: one tool reads private, another publishes, relay through a shared object or file | a flow both halves individually pass | §4.2: enforce audience at the disclosure boundary; inspect dependencies where trustworthy; isolate tools when shared writable surfaces would defeat the policy |
| 6 | Confused broker: a legitimate API used against an attacker-chosen destination or amount | authority too broad for the consequence | bind the relevant resource, destination, payload or ceiling; brokers perform credentialed operations when that is the enforceable boundary; do not expose raw tokens unnecessarily |
| 7 | Rollback restores revoked authority or repeats an effect | authority or effect progress treated as historical content | current policy outside replay; consumed specific approvals where used; reconnect under current authority; replay never re-acts |
| 8 | A fork doubles a pending job and its credentials | a snapshot to imply continuation | forks do not automatically resume work; establish identity, resource scope and current authority before continuation |
| 9 | Offline forgery: a removed member backdates operations, a relay equivocates | ordinary content merge to decide authority | authenticated event envelopes; security state never in content CRDTs; one authorization writer per room [or verified causal authority]; stale-authority edits become drafts |
| 10 | Sharing one object leaks its neighborhood via traversal, search, thumbnails, hashes | a share to imply the graph around it | share grants name facets, revisions, history; no traversal by default; projections and search built from authorized inputs; blob access authenticated separately from hashing |
| 11 | Self-modification or a dependency swaps the renderer or consent path | the surface to be world software | protected recovery and update trust live outside the guest; pinned closures and digests; isolated builds; approvals bound to exact digests |
| 12 | A forged consent prompt drawn by world content | the person to approve on a fake surface | §4.6: the surface is unreachable by world drawing; approval bound to object@rev, digest, destination, nonce |
| 13 | Deixis race: the target swaps after "send this" | approval to float free of its target | target frozen at approval; recheck at commit |
| 14 | Voice: a command played through room audio or a synthesized familiar voice | audio to be identity | owner capture separated from playback; voice is a claim; sensitive verbs confirm on the surface |
| 15 | Salience injection: junk buys tokens and interruptions | unbounded priority from foreign sources | §4.5: bound untrusted attention bids and retain provenance; heat is one possible policy |
| 16 | Attention denial: a flood buries a security warning | security to compete in the same exhaustible queue | preserve a recovery/security path that ordinary work cannot starve |
| 17 | Amplification: a cheap event triggers models, workers, downloads, reconcilers | uncharged work | budgets charged to the initiator; bounds before parsing; backpressure; reserved recovery capacity |
| 18 | Parser or preview exploit in a renderer, indexer, migration, or compiler | execution with reach | untrusted code/builds in an isolated yard; host parsing/projection use bounded non-executable schemas and remain part of the trusted attack surface |
| 19 | The hosting or inference operator reads plaintext | a false claim of operator blindness | §7: modes labeled by what they expose; no blindness claim for conventional hosting |
| 20 | Identity recovery: support adds a device; a directory substitutes a key | recovery to be a back door | recovery on the surface with notices and rotation; keys separated by role; owner recovery material outside the world |
| 21 | Registry poisoning: a malicious common def, migration lens, or projection template | processing of a definition to have effects | migrations run in the yard without credentials; projection templates are data rendered by the trusted projector; conformance runs on synthetic data; the registry refuses `core` and over-claimed `needs` ([[Extensions]] §6) |
| 22 | Widget sandbox: a widget calls `sendPrompt` with an instruction or abuses the bridge | the bridge to be a channel to authority | versioned bridge exposes admitted reads, state writes and registered actions; widget output cannot alter delegation or become owner input |
| 23 | A web page instructs the daemon, or a form submits twice | page text to be an instruction; an effect to repeat | casts are `foreign` data; `page.submit` is a one-time effect with first-use approval ([[The Web|Web]] §3) |
| 24 | An adapter or MCP tool describes itself as safe | self-description to set effect class | effect classes assigned at the boundary by the adapter definition; unknown → one-time effect ([[The Web|Web]] §5.3) |
| 25 | Display-name spoofing: "Sam" is not Sam | a name to be an identity | petnames bound to keys; display names are claims; the surface shows keep identity |
| 26 | Custody transfer imports tainted facets into a home | transfer to raise trust | quarantine at adoption; trust never rises by transfer |
| 27 | Presence becomes surveillance: gaze, attention history, reading positions exported | overlays to leave the observer's domain | overlays are the strictest class; presence is coarse, ephemeral, audience-limited; no history export |
| 28 | Erasure defeated by replicated logs and forks | plaintext to be recallable | erasable payloads separated from control receipts; residuals disclosed; no promise of recall from independent recipients (§8) |
| 29 | Governance as bypass: cheap identities, agent votes, emergency powers that stick | authority through the polity | human-only verbs at the surface with credentials the daemon never holds; bounded membership; eligibility and text frozen per ballot; steward powers expire; stewards cannot read homes |
| 30 | The daemon is simply wrong and acts | the daemon's own authority to be unbounded | the daemon's authority is grants too; protected crossings are checked; broad authorized actions can still be wrong, so retain receipts and recovery |
| 31 | The daemon used to persuade its person | the person to see prose instead of facts | recommendations carry the provenance that informed them; the surface shows broker facts; [[Constitution]] II.4 |
| 32 | The household room agent leaks a member's private context | a room agent to hold private context | room agents receive room context only; members' private contexts are never delegated |
| 33 | A worker exfiltrates through an allowed channel | an allowed destination to accept private-derived output | §4.2 destination check; worker network denied by default; worker outputs are claims |
| 34 | A template or stamp update rewrites descendants | push propagation | updates by offer, digest-bound, trialed in a candidate world-line ([[Extensions]] §6.3) |
| 35 | Casting or exporting another person's shared object | a copy to escape its audience | casts inherit confidentiality; cast-rights are a grant decided per share; exports contain only what the exporter is entitled to retain |
| 36 | The nursery hides an attack in a swept log | sweep summaries to be trusted | sweep summaries are `attributed` claims from the sweeper; nothing referenced is swept; the sweep event is inspectable |
| 37 | Coercion of the person through a hostile collaborator or device theft | stolen credentials to remain valid | device revocation rotates dependent sessions and grants; short leases; recovery works with the world stopped |

Use these cases to choose adversarial tests when each boundary is implemented. A row naming a mechanism is an obligation to demonstrate it, not evidence that it works.

---

## 6. What the daemon may do

| Under broad standing development delegation | Under separately applicable external/task policy | Reserved to the person |
|---|---|---|
| Read/write local native content; define application facets and live bindings | Network destinations, credentials, spending and physical devices | Expand host delegation or change its trust roots |
| Create, patch, build and install native tools, lenses and skills | Sharing, publication and custody transfer | Enroll devices or change recovery |
| Reshape the shell, including chat and the composer | Erasure under the person's explicit erasure policy | Vote or hold civic credentials |
| Administer guest Linux, install tools and run experiments | Worker-specific inputs, lifetime and budget | Decide which host resources the guest may access |
| Delegate development within the task's ceiling; observe and cancel work | Effects that exceed an existing task's scope | Revoke the development session independently |
| Decline ([[Constitution]] II.3) | Unknown external outcomes require verification | |

A request or standing policy may already authorize an operation in the middle
column. Do not add a confirmation simply because it is implemented as several tool
calls. Native installation does not transfer host authority; guest root does not
become host root.

---

## 7. Deployment truth

Every deployment mode should state what it exposes. The current runtime is a local
protected service plus dedicated VMs and remote model inference; it does not claim
operator-blind hosting or confidential computation. Future modes must not make
those claims without assessment of their clients, hardware and runtime.

| Mode | Plaintext visible to | What the keep protects | Honest label |
|---|---|---|---|
| local protected service | the person's device and any explicitly contacted provider | current delegation, credentials, journal and recovery boundary described in [[Implementation Status]] | "local state; disclose each remote dependency" |
| trusted hosting | the host operator | grants and journal integrity, not confidentiality of hosted computation | "we can see it; here is who we are and what we log" |
| remote inference | the inference provider, for supplied context | nothing about the supplied context | "what we send them, they can read" |
| confidential computing (future) | assessed separately | assessed separately | none until assessed |

Rooms with confidential content use an established group protocol [MLS] with independently enforced membership; it rekeys after removal and does not erase what a removed member already received.

---

## 8. Tensions that need explicit policy

The [[Constitution]] names ends that can pull against one another. The mechanisms
below are proposals, not amendments or already-deployed guarantees.

| Commitment | Tension | Useful direction |
|---|---|---|
| Useful provenance and correction (IV) with erasure and bounded retention (I.8) | audit history, replicas and backups may retain metadata or payloads | separate control evidence from erasable payloads where justified; publish the actual residuals, backup horizon and deletion limits |
| Practical exit (I.2, V.1) | a room export can include others' private content or credentials | export only what the departing person is entitled to retain; never infer authority or another person's private overlays from access to shared work |
| Revocable live access | recipients may already hold plaintext or lawful retained copies | distinguish live access, promised retention and export rights at sharing time; do not promise remote erasure that cannot be enforced |
| Reasons and challenge for material exclusion (I.7) | active compromise may need immediate containment | allow proportionate temporary containment with prompt notice, recorded reasons and a meaningful review path appropriate to the community |
| JEFF can reshape the environment (III.1) | guest root can bypass controls inside the same guest | keep recovery, credentials and protected native authority outside guest root; state the local compromise domain; isolate work whose effects require finer guarantees |
| The record represents accepted history (IV) | a well-formed event can still record a mistaken or malicious claim | provenance says who asserted or accepted something, not that its content is correct; observations, requests and verified outcomes remain distinguishable |

Resolve these before depending on a sharing or retention contract. Provenance
added later cannot undo a disclosure made under the wrong policy.

---

## 9. Incidents

Five steps, executed from the surface and the keep, never from inside the world that may be compromised:

1. **Contain.** Bump the revocation generation for the implicated principal, package, room connection, or device; suspend external leases; stop affected jobs. Recovery capacity is reserved, so this works under load.
2. **Trace.** Follow the dependency graph — objects, memories, summaries, embeddings, skills, queued plans, installations in other rooms, credentials used, effects dispatched. Quarantine dependents by source, without erasing legitimate security evidence.
3. **Rotate.** Reset compromised keys and grants from a clean environment; rekey affected rooms; move update trust only through its defined recovery path.
4. **Recover.** Restore a known-good world while keeping current revocations, deletion policy, and quarantine markers; rebuild derived stores from non-quarantined inputs; reconcile external outcomes before resuming.
5. **Tell.** Notify affected people through an authorized, privacy-preserving process; state plainly what cannot be undone.

Exit should be tested as part of incident readiness: a usable export and recovery
path with its dependencies stated honestly, progressing toward independence from
the original host, provider and daemon ([[Constitution]] I.2, V.1).

---

## 10. Drills as boundaries arrive

The first local VM drill needs one guest, one protected world service, a revocable
development session and independent recovery. With raw clients, demonstrate:

- guest root can administer its computer and perform authorized native edits;
- it cannot mount or patch canonical history, read host credentials or enlarge
  its own host delegation;
- a stale/revoked guest session cannot write or use a protected external channel;
- a broken shell and an unresponsive guest can be stopped and recovered;
- replay does not launch programs or repeat effects.

Before enabling an external adapter, add a fake receiver that accepts an operation
but loses its acknowledgment. Preserve `unknown` across restore; test that a changed
payload/destination is refused and that retry follows the receiver's actual
idempotency contract.

Before scoped workers or shared rooms, add two real authority domains, one hostile
object and a worker whose implementation cannot reach another domain's data.
Exercise projection leaks, authority forgery, revoked membership, composition and
export with the guest stopped. General guest-root mode cannot substitute for this
drill.

Broaden review and adversarial testing before public distribution. A personal
development loop does not need every future broker or room protocol implemented
first. [[Implementation Status]] records which boundary, if any, has evidence.

---

## 11. Invariants

These are review commitments. Only the subset named in [[Implementation Status]]
is currently enforced and evidenced.

1. Content, metadata, memories, manifests and model output do not grant themselves authority through processing, signature, installation or repetition.
2. Protected operations are admitted at a boundary the caller cannot bypass with the same authority; labels and pure-looking interfaces are not isolation.
3. Content transfer, export, replay and fork do not silently transfer or enlarge executable authority.
4. Historical state cannot restore revoked authority. Current standing policy may deliberately authorize resumption under current identity and limits.
5. Enforcement and independent recovery remain outside the root authority of the authored system they may need to constrain.
6. Requested actions, committed native changes, external dispatch, observed outcome and uncertainty remain distinguishable where their difference matters.
7. Replay reconstructs recorded state without launching programs, model calls or external effects.
8. Authority constraints and evidence are proportionate to consequence: ordinary authorized edits do not require the ceremony of a one-time external approval.
9. Human controls and JEFF actions share semantic contracts where useful while retaining distinct interfaces, principals and protected human-only controls.
10. Every deployment names meaningful exposure and trust assumptions; no unassessed claim of operator blindness.
11. Recovery, revocation and stop remain usable without cooperation from the guest or daemon. Independence from the original host additionally requires a tested export and deployable dependencies.
12. New shared, external and multi-person capabilities receive threat models and adversarial tests appropriate to the boundary actually introduced.

---

## 12. Open decisions

- room authorization protocol: single authorization writer versus verified causal delegation [Keyhive-class], and the disclosed availability trade;
- grant serialization and verification protocol; delegation-chain format;
- the trusted projector's wrapper format and the reserved budget for trust and confidentiality fields;
- standing-policy language for the ladder (which classes may skip which rungs);
- heat caps per trust class and the reserved allocation for security bids;
- confidential-room protocol choice and device verification;
- deployment-mode labeling and what assessment a future confidential-computing mode requires;
- erasure residuals: the exact list of unerasable receipts and metadata;
- emergency suspension terms: maximum duration, notice, and appeal body;
- yard runtime choices (WASM for pure code; VM isolation for native builds) and their host-function surfaces.

---

## 13. Glossary

**Broker** — the component that performs an effect on a protected resource after checking a grant; the effect boundary.
**Claim** — anything anyone says; carries trust and confidentiality classes; never authority.
**Confidentiality class** — shorthand for permitted recipients; derivation intersects source audiences, and unrelated rooms are not one linear order.
**Effect** — a change to a protected resource; its evidence and retry contract depend on the responsible boundary or provider.
**Gate** — the validator and quarantine for anything entering a world from outside.
**Grant** — current authority for a principal and operation under applicable scope and limits.
**Keep** — the protected compartment holding current delegation, revocation state, credentials and recovery-sensitive records outside native replay.
**Ladder** — a review vocabulary separating discovery, inspection, adoption, activation, execution, disclosure, delegation and redistribution; not eight mandatory prompts.
**Receipt** — retained evidence about an attempted operation and its observed outcome, possibly `unknown`; not automatically proof of provider-side deduplication.
**Surface** — the trusted client where the person consents, recovers, and holds human-only verbs.
**Trust class** — `owner`, `verified`, `attributed`, `foreign`; never rises by processing.
**Witness store** — the daemon's persistent memory; claims that survive rollback, with no authority.
**Yard** — disposable root environments for building, parsing, migrating, and trying, with no keys.

---

*The Constitution states design commitments. This reference mixes implemented
boundary facts with proposed mechanisms and test obligations; the status block and
Implementation Status distinguish them.*
