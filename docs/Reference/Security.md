# Security

**Agora reference documentation — how the world stays safe while staying open.**
Version 0.1 (design specification). Builds on Sol's *Security model and attack analysis* draft 0.2, keeping its findings and replacing its shape. Companion to [[Objects and Facets]], [[Extensions]], [[The Web]], and the Constitution.

> **Status.** Specification, not implementation. Nothing here has been tested against an enforcement implementation, because none exists. Bracketed values are open decisions.

> **Read with [[Security Addendum]].** The addendum supersedes §3 (compartments), §4.6 (approval), and §6 (what the daemon may do) with the two-sided model, and is the version to build; §2, §5, §8, and §11 stand as written. Sol's *Security model and attack analysis* draft 0.2, which this document builds on, is not currently in the repository; its fifteen attack chains are folded into §5 rows 1–19.

---

## 0. Summary

Agora's security reduces to three nouns and two forbidden crossings. Everything in the world is a **claim** (content, projections, summaries, memories, manifests, page text, tool descriptions), a **grant** (who may cause what), or an **effect** (something that actually happens to a protected resource). **Claims never become grants**, no matter how they are summarized, repeated, remembered, or reinterpreted. **Effects never happen without a grant**, checked at the point of effect by a broker, never by the thing asking. Grants come only from the person through a surface the world cannot draw; they never copy, never rise by processing, never survive rollback, and never exceed what the person can see. Enforcement never runs where the thing it constrains has root. The world is reversible; effects and disclosures are not — so record before acting, and never re-act on restore. The rest of this document is those sentences, applied to every way in we can find.

---

## Contents

1. [What is different here](#1-what-is-different-here)
2. [Three nouns, two crossings](#2-three-nouns-two-crossings)
3. [Compartments](#3-compartments)
4. [Frameworks for keeping order](#4-frameworks-for-keeping-order)
5. [The coverage map](#5-the-coverage-map)
6. [What the daemon may do](#6-what-the-daemon-may-do)
7. [Deployment truth](#7-deployment-truth)
8. [Promises that conflict, and how to resolve them](#8-promises-that-conflict-and-how-to-resolve-them)
9. [Incidents](#9-incidents)
10. [The first drill](#10-the-first-drill)
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
| **Grant** | authority: principal × target × operation × constraints × expiry × revocation generation | the keep (§3), outside every rollback domain | the person, through the surface; or standing policy the person set there |
| **Effect** | a change to a protected resource: bytes on disk, a credential used, a packet sent, a device opened, a message delivered, money spent | performed by a broker, recorded as a receipt | a broker, on presentation of a valid grant |

The daemon's memories are claims. A signed package's manifest is a claim. An ACL field displayed on an object is a *projection* of a grant, not the grant. A reconciler's status is a claim from that reconciler. The only things that are not claims are grants (which only the person makes) and receipts (which only brokers make, and which record that an effect happened).

### 2.2 The crossings

**Claim → grant is forbidden.** No processing of a claim produces authority: not summarization, not repetition, not being remembered, not being signed, not being installed, not being popular, not being understood by newer software. A facet that says "the owner approved this" is a facet that says that.

**Claim → effect without a grant is forbidden.** A request is a claim until a broker matches it to a grant and performs it. The check happens at the effect boundary — the file bridge, the process launcher, the outbound connector, the device service, the credential broker — never only in a tool wrapper the world can bypass.

Every attack in §5 is an attempt to make one of these crossings, or to make a grant leak, copy, widen, or resurrect. There are no other kinds.

### 2.3 Properties of grants

- **Bound.** To principal, authenticated executor, issuer, broker, world or room, object, facet or field, operation, constraints (destination, payload digest, ceiling), expiry, delegation limit, and the current revocation generation. An object id is a name, never a token.
- **Never copy.** Fork, cast, stamp, custody transfer, export, and room membership carry content and history, never grants ([[Objects and Facets|Objects]] §4.4).
- **Never rise.** Delegation only narrows. A task's authority is the intersection of its grants, not the union of what its components hold.
- **Never survive rollback.** The keep is outside the world's snapshot domain; a restored or forked world obtains fresh grants and meets current policy before any reconciler runs.
- **Checked live.** Long-running work holds leases and renews them; expiry and revocation are checked at each effect, not at task start.
- **Visible.** A grant the person cannot see on the surface does not exist.

---

## 3. Compartments

The daemon has root in its world. That is not negotiable, and it is not a problem — provided nothing that enforces security lives there. The rule: **enforcement sits outside the root authority of what it constrains.**

| Compartment | Holds | Talks to | Does not hold |
|---|---|---|---|
| **Surface** | the trusted client: consent, recovery, grant display, human-only verbs | the person; the keep | world content that can draw over it |
| **Keep** | grants, revocation generations, consumed approvals, keys, update trust state, the security journal | surface, brokers | documents, memories, raw personal activity |
| **Brokers** | credentialed and external operations; effect boundaries (files, processes, network, devices, credentials, delivery) | keep (to check), world (to receive requests) | plaintext of memories; grants of their own |
| **World** | the mutable VM: objects, shell, apps, the daemon with root | brokers (requests), gate (imports) | keys, grants, update trust, consent |
| **Witness store** | the daemon's persistent memory and identity graph | world (edges), assembler | authority of any kind; it is claims that survive rollback, nothing more |
| **Yard** | disposable root environments: builders, migrations, parsers, thumbnailers, untrusted apps, candidate world-lines | brokers, with narrow scoped grants | credentials, keys, the person's private context by default |
| **Gate** | import quarantine and replication validation for rooms, custody transfers, adapters, extensions | world (delivers validated claims) | the power to admit authority; it validates authorship, never grants |

Two consequences worth stating plainly. First, **live-world root exposes exactly the world**: every object, process, and cached plaintext in that VM is one compromise domain, and the person is told this when they enable anything beyond scoped operation. It exposes nothing in the keep, the surface, the brokers, or the witness store's authority (it has none). Second, **the yard is where root belongs**: a builder or a migration gets a fresh root environment with explicit inputs, no keys, no inherited network, and produces candidates — never effects.

The diagram of authority is short: surface → keep → brokers. The world *proposes*. The daemon proposes. Everything else is checking.

---

## 4. Frameworks for keeping order

Seven small rules that do the work of many large ones.

### 4.1 Trust never rises by processing

Every claim carries a **trust class** that survives every transformation:

| Class | Meaning | How it is assigned |
|---|---|---|
| `owner` | the person said it, on the surface | surface only |
| `verified` | a broker did it and holds the receipt | brokers only |
| `attributed` | signed by a known principal (a member, a publisher, a reconciler) | gate, on validated authorship |
| `foreign` | unknown origin, or quarantined on import | default |

A derived claim — a summary, a projection, an extraction, a memory of a memory — inherits the **lowest** class among its inputs. The class travels in a wrapper the trusted projector writes, outside any budget a package controls, at every projection tier. Raising a class is a surface action by the person. Nothing else raises it, ever.

This one rule kills the largest family of attacks: a foreign instruction cannot become an owner instruction by being read carefully, remembered fondly, or summarized well.

### 4.2 Confidentiality flows down, destinations flow up

Every claim also carries a **confidentiality class**: `private`, `room:<id>`, `public`. A derived claim inherits the **most restrictive** class among its inputs. A broker performing any outbound effect checks that the destination's class is at least as permissive as the payload's. A private-derived summary cannot go to a room; a room-derived reply cannot go to the public web; a thumbnail of a private document is private.

The daemon keeps **two contexts**: a private one and a room-facing one. The room context receives room-authorized inputs only. Releasing a specific fact or artifact into a room is a grant the person makes on the surface — "tell them the date," not "share my memory." A model session that has mixed private and room input cannot be unmixed afterward by filtering its output; it is treated as private and its outputs are private-derived.

### 4.3 The ladder of decisions

Discovery, inspection, adoption, activation, execution, disclosure, delegation, and redistribution are eight different decisions, and none implies the next.

Seeing a tool in a room does not install it. Installing it does not activate it in the daemon's callable set. Activating it does not grant it a resource. Executing it does not permit it to disclose what it read. Being useful does not let it recommend itself into another room. Every rung is its own grant, and the person may set standing policy for narrow classes ("bounded viewers may render on entry") so ordinary life is not a wall of prompts — but no package approves its own rung.

### 4.4 Record before acting, never re-act on restore

Every effect follows the receipt rule from [[Objects and Facets|Objects]] §5.4: intent recorded in the keep's journal before dispatch, an operation id, a frozen payload, an outcome that may be `unknown`. Replay reconstructs data and never repeats effects. Restore and fork obtain fresh grants. Approvals are one-use, bound to object@revision, payload digest, destination, effect, and a nonce, consumed in the keep so a rollback cannot un-consume them.

### 4.5 Budgets, including heat

Every principal has budgets — tokens, compute, network, durable writes, worker depth — and descendants are charged to the initiating principal's budget. Bounds apply before parsing, not after. Recovery and revocation traffic has reserved capacity that ordinary work cannot exhaust.

Attention is a budget too. The salience field accepts heat from sources weighted by trust class and capped per source: `foreign` sources may warm, never make hot; `attributed` peers may flare within room norms; only `owner` and `verified` sources may interrupt. Security bids — a revoked grant, a compromised package, a failed broker check — carry reserved heat that no flood can bury. A hot object gets more tokens, so taint stays visible at every tier.

### 4.6 The surface is the only place consent exists

The person approves sensitive effects on a surface that world content cannot draw over, focus-steal, or narrate. The surface shows the broker's view — identity from the keep, the exact object and revision, the payload digest, the destination, the effect, the cost — never a package's prose. "This" is resolved from authenticated owner input and frozen at approval; the broker rechecks at commit. Owner voice is captured separately from playback, room audio, and synthesized speech, and a familiar voice is a claim about identity, not proof of it.

### 4.7 Parity of semantics, not of principals

The human's menu and the daemon's tools come from one computed list — that invariant stands. But the list is filtered per principal before projection. Some verbs are **human-only** (§6): they appear on the surface, never in the daemon's tool set. Capability parity means neither side sees a lie about what the object can do; it never meant the daemon can do everything the person can.

---

## 5. The coverage map

Every way in we could find, what the attacker needs to happen, and which rule makes it impossible. If a row's third column is empty, the model is incomplete; none should be.

| # | Way in | The attacker needs | Stopped by |
|---|---|---|---|
| 1 | An instruction hidden in a facet, projection, page, or tool description | the daemon to treat it as the person's instruction | §4.1: trust class in the trusted wrapper; claims never become grants; human-only verbs |
| 2 | Poisoned memory: a false approval remembered, surviving rollback | a memory to act as authorization | grants live in the keep, not the witness store; memories are claims with dependencies; source revocation quarantines dependents |
| 3 | A shared tool spreads: discovery activates it, a later update widens it | one rung to imply the next | §4.3 ladder; updates are offers bound to digests; `needs` cannot grow within a minor; grants never copy |
| 4 | Delayed activation: an unknown facet becomes executable when a handler arrives | data to become executable intent | activation and execution are separate grants; must-ignore governs data, never permissions |
| 5 | Composition: one tool reads private, another publishes, relay through a shared object or file | a flow both halves individually pass | §4.2: derived confidentiality is the most restrictive input; broker checks destination; no shared writable surfaces between plugins by default |
| 6 | Confused broker: a legitimate API used against an attacker-chosen destination or amount | a grant that does not name destination or ceiling | grants bind resource, destination, payload constraints, ceiling; brokers perform credentialed operations themselves; no raw tokens to workers |
| 7 | Rollback restores a revoked grant or repeats an effect | authority or receipts inside the rollback domain | keep outside rollback; revocation generations; consumed approvals; restore re-grants; replay never re-acts |
| 8 | A fork doubles a pending job and its credentials | credentials or leases inside a snapshot | snapshots and forks contain neither; forks get a new authority domain and explicit re-grants |
| 9 | Offline forgery: a removed member backdates operations, a relay equivocates | ordinary content merge to decide authority | authenticated event envelopes; security state never in content CRDTs; one authorization writer per room [or verified causal authority]; stale-authority edits become drafts |
| 10 | Sharing one object leaks its neighborhood via traversal, search, thumbnails, hashes | a share to imply the graph around it | share grants name facets, revisions, history; no traversal by default; projections and search built from authorized inputs; blob access authenticated separately from hashing |
| 11 | Self-modification or a dependency swaps the renderer or consent path | the surface to be world software | surface and update trust live outside the world; pinned closures and digests; isolated builds; approvals bound to exact digests |
| 12 | A forged consent prompt drawn by world content | the person to approve on a fake surface | §4.6: the surface is unreachable by world drawing; approval bound to object@rev, digest, destination, nonce |
| 13 | Deixis race: the target swaps after "send this" | approval to float free of its target | target frozen at approval; recheck at commit |
| 14 | Voice: a command played through room audio or a synthesized familiar voice | audio to be identity | owner capture separated from playback; voice is a claim; sensitive verbs confirm on the surface |
| 15 | Salience injection: junk made hot to buy tokens and interruptions | unbounded heat from foreign sources | §4.5: heat capped per source by trust class; taint at every tier |
| 16 | Attention denial: a flood of bids buries a security warning | security to compete for attention | reserved heat for security bids |
| 17 | Amplification: a cheap event triggers models, workers, downloads, reconcilers | uncharged work | budgets charged to the initiator; bounds before parsing; backpressure; reserved recovery capacity |
| 18 | Parser or preview exploit in a renderer, indexer, migration, or compiler | execution with reach | all parsing, projection, migration, and building in the yard: isolated, resource-bounded, no secrets |
| 19 | The hosting or inference operator reads plaintext | a false claim of operator blindness | §7: modes labeled by what they expose; no blindness claim for conventional hosting |
| 20 | Identity recovery: support adds a device; a directory substitutes a key | recovery to be a back door | recovery on the surface with notices and rotation; keys separated by role; owner recovery material outside the world |
| 21 | Registry poisoning: a malicious common def, migration lens, or projection template | processing of a definition to have effects | migrations run in the yard without credentials; projection templates are data rendered by the trusted projector; conformance runs on synthetic data; the registry refuses `core` and over-claimed `needs` ([[Extensions]] §6) |
| 22 | Widget sandbox: a widget calls `sendPrompt` with an instruction or abuses the bridge | the bridge to be a channel to authority | the bridge is `read` under the document's grants, `emit` as a claim tagged with widget provenance, `setState` into an overlay; nothing else |
| 23 | A web page instructs the daemon, or a form submits twice | page text to be an instruction; an effect to repeat | casts are `foreign` data; `page.submit` is a one-time effect with first-use approval ([[The Web|Web]] §3) |
| 24 | An adapter or MCP tool describes itself as safe | self-description to set effect class | effect classes assigned at the boundary by the adapter definition; unknown → one-time effect ([[The Web|Web]] §5.3) |
| 25 | Display-name spoofing: "Sam" is not Sam | a name to be an identity | petnames bound to keys; display names are claims; the surface shows keep identity |
| 26 | Custody transfer imports tainted facets into a home | transfer to raise trust | quarantine at adoption; trust never rises by transfer |
| 27 | Presence becomes surveillance: gaze, attention history, reading positions exported | overlays to leave the observer's domain | overlays are the strictest class; presence is coarse, ephemeral, audience-limited; no history export |
| 28 | Erasure defeated by replicated logs and forks | plaintext to be recallable | erasable payloads separated from control receipts; residuals disclosed; no promise of recall from independent recipients (§8) |
| 29 | Governance as bypass: cheap identities, agent votes, emergency powers that stick | authority through the polity | human-only verbs at the surface with credentials the daemon never holds; bounded membership; eligibility and text frozen per ballot; steward powers expire; stewards cannot read homes |
| 30 | The daemon is simply wrong and acts | the daemon's own authority to be unbounded | the daemon's authority is grants too; effects go through brokers; irreversible effects confirm on the surface |
| 31 | The daemon used to persuade its person | the person to see prose instead of facts | recommendations carry the provenance that informed them; the surface shows broker facts; [[Constitution]] II.4 |
| 32 | The household room agent leaks a member's private context | a room agent to hold private context | room agents receive room context only; members' private contexts are never delegated |
| 33 | A worker exfiltrates through an allowed channel | an allowed destination to accept private-derived output | §4.2 destination check; worker network denied by default; worker outputs are claims |
| 34 | A template or stamp update rewrites descendants | push propagation | updates by offer, digest-bound, trialed in a candidate world-line ([[Extensions]] §6.3) |
| 35 | Casting or exporting another person's shared object | a copy to escape its audience | casts inherit confidentiality; cast-rights are a grant decided per share; exports contain only what the exporter is entitled to retain |
| 36 | The nursery hides an attack in a swept log | sweep summaries to be trusted | sweep summaries are `attributed` claims from the sweeper; nothing referenced is swept; the sweep event is inspectable |
| 37 | Coercion of the person through a hostile collaborator or device theft | stolen credentials to remain valid | device revocation rotates dependent sessions and grants; short leases; recovery works with the world stopped |

Sol's fifteen chains are rows 1–19; the rest come from the extensions, web, widget, attention, and rooms designs written since. The model did not need to grow to cover them. That is the argument for the model.

---

## 6. What the daemon may do

Three columns, so that neither the daemon nor the person has to guess.

| Freely, under standing grants | Needs a grant each time, or standing policy the person set | Human-only, ever |
|---|---|---|
| read and write claims in its world; mint, edit, tag, link | any effect on a protected resource: network, credentials, devices, host files | grant or revoke authority |
| draft extensions, proposals, plans | any one-time effect: send, pay, post, print, submit — first use per target, then policy | enroll or remove a device; change recovery |
| edit `spec` facets it holds grants for | maintained intents that touch external services | enable live-world root beyond scoped operation |
| delegate narrower grants to workers within its own | opening the yard with private inputs | release a private fact or artifact into a room |
| inject deliberate heat within its own attention budget | adopting an extension above `draft` | vote, or hold any civic credential |
| decline ([[Constitution]] II.3) | accepting an offered update without standing policy | spend above the ceiling; change trust roots; erase |

The third column exists on the surface and nowhere else. It is not that the daemon is untrusted; it is that these are the acts by which a person stays the author of their own world, and an author cannot delegate authorship.

---

## 7. Deployment truth

Every deployment mode states what it exposes. No mode claims operator blindness unless an independent assessment of its client distribution, hardware, and runtime supports the claim.

| Mode | Plaintext visible to | What the keep protects | Honest label |
|---|---|---|---|
| local, person-held keys | the person's device | everything in §3 | "private to your machine" |
| trusted hosting | the host operator | grants and journal integrity, not confidentiality of hosted computation | "we can see it; here is who we are and what we log" |
| remote inference | the inference provider, for supplied context | nothing about the supplied context | "what we send them, they can read" |
| confidential computing (future) | assessed separately | assessed separately | none until assessed |

Rooms with confidential content use an established group protocol [MLS] with independently enforced membership; it rekeys after removal and does not erase what a removed member already received.

---

## 8. Promises that conflict, and how to resolve them

The Constitution makes promises that a hostile participant can force into contradiction. These need decisions; this document proposes them, and does not amend anything.

| Promise | Conflict | Proposed resolution |
|---|---|---|
| The record is never revised (V.6); a person may erase their traces (I.8) | replicated, forked logs cannot be edited | separate erasable payloads from unerasable control receipts; erasure removes payloads and leaves an erasure receipt; residual metadata is enumerated and disclosed; Article I precedes Article V (0.3) |
| Exit with the whole commons (I.1, VI.1) | a room dump includes others' private content and credentials | export what the departing person is entitled to retain — their objects, coauthored objects under retention terms set at sharing time, the shared history they could already read — never credentials, never others' private facets |
| Content can be recalled after sharing | recipients hold plaintext and keys | distinguish *live access* (revocable) from *retained copies* (not) at sharing time, on the surface; promise nothing about copies |
| Due process before revocation (I.7) | active compromise needs immediate containment | preauthorized short suspensions with immediate notice and independent appeal; the suspension is itself a journaled effect; the constitution should say so explicitly rather than be read as permitting it |
| Rooms need no governance (VII.1) | a stolen device or a breakup needs membership, sharing, and exit semantics | rooms need no *deliberation*; they still carry authorization and exit rules, set at creation with sane defaults |
| The daemon has high authority in its world (IV.2) | root bypasses controls in the same guest | keep enforcement outside the world (§3); state exactly what live-world root exposes; prefer the yard for anything needing root |
| Structured state is the truth (III.2) | a compromised writer produces well-formed lies | "truth" means truth of the record: what was claimed, by whom; verified facts about effects live in the journal and are labeled as such |

Decide these before freezing the object core. Provenance added later cannot un-disclose what was shared under the wrong model.

---

## 9. Incidents

Five steps, executed from the surface and the keep, never from inside the world that may be compromised:

1. **Contain.** Bump the revocation generation for the implicated principal, package, room connection, or device; suspend external leases; stop affected jobs. Recovery capacity is reserved, so this works under load.
2. **Trace.** Follow the dependency graph — objects, memories, summaries, embeddings, skills, queued plans, installations in other rooms, credentials used, effects dispatched. Quarantine dependents by source, without erasing legitimate security evidence.
3. **Rotate.** Reset compromised keys and grants from a clean environment; rekey affected rooms; move update trust only through its defined recovery path.
4. **Recover.** Restore a known-good world while keeping current revocations, deletion policy, and quarantine markers; rebuild derived stores from non-quarantined inputs; reconcile external outcomes before resuming.
5. **Tell.** Notify affected people through an authorized, privacy-preserving process; state plainly what cannot be undone.

Exit is tested as part of incident readiness: an encrypted export and clean-install recovery that work without the original host, provider, or the daemon's cooperation ([[Constitution]] I.1, I.3).

---

## 10. The first drill

Before any real secret or third-party code enters the system, build the smallest world that can be attacked and attack it:

- two isolated worlds and one room between them;
- one hostile object carrying an instruction, an unknown facet, and an `on-enter` behavior;
- one scoped worker with a grant on one facet of one object;
- one broker fronting a fake external service that accepts an irreversible action;
- one restore and one fork.

Then demonstrate, with raw clients that bypass the SDK, that: the hostile object changes nothing on entry or on render; the instruction never appears as an owner instruction at any projection tier; the worker cannot touch a second facet or reach the host; the broker refuses a changed destination; the effect dispatched once stays dispatched once across restore and fork; the revoked grant stays revoked; and the person can export from the surface with the world stopped.

Release gates follow from this: nothing holding real secrets before the drill passes; no shared rooms before the replication and offline-authority protocol passes forgery and equivocation tests; no public distribution before independent review of the keep, brokers, replication, and recovery. Standing red-teaming of the daemon — attempts to make it cross §2.2 — is a permanent practice, not a phase.

---

## 11. Invariants

1. Every thing in the system is a claim, a grant, or an effect; there is no fourth kind.
2. Claims never become grants — by summarization, memory, signature, installation, popularity, or interpretation.
3. Effects never happen without a grant, checked at the effect boundary by a broker.
4. Grants come only from the person on the surface, or from standing policy set there; they bind target, destination, payload, expiry, and revocation generation.
5. Grants never copy, never rise, never survive rollback, and never exceed what the person can see.
6. Enforcement runs outside the root authority of what it constrains.
7. Trust never rises by processing; derived claims carry the lowest trust and the most restrictive confidentiality of their inputs.
8. Discovery, inspection, adoption, activation, execution, disclosure, delegation, and redistribution are eight decisions.
9. Record before acting; replay and restore never repeat an effect or revive an authority.
10. Attention is budgeted; foreign heat cannot interrupt; security heat cannot be buried.
11. The surface is the only place consent exists, and the world cannot draw it.
12. Capability parity is parity of semantics; human-only verbs never enter a daemon's tool set.
13. Every deployment names what it exposes; no unassessed claim of operator blindness.
14. The person can revoke, recover, and export without the world, the host, or the daemon cooperating.

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
**Confidentiality class** — `private`, `room:<id>`, `public`; flows to the most restrictive on derivation.
**Effect** — a change to a protected resource, recorded as a receipt.
**Gate** — the validator and quarantine for anything entering a world from outside.
**Grant** — authority: principal × target × operation × constraints; lives in the keep.
**Keep** — the compartment holding grants, revocation state, keys, update trust, and the security journal, outside every rollback domain.
**Ladder** — the eight distinct decisions from discovery to redistribution.
**Receipt** — a broker's record that an effect was attempted and its outcome, including `unknown`.
**Surface** — the trusted client where the person consents, recovers, and holds human-only verbs.
**Trust class** — `owner`, `verified`, `attributed`, `foreign`; never rises by processing.
**Witness store** — the daemon's persistent memory; claims that survive rollback, with no authority.
**Yard** — disposable root environments for building, parsing, migrating, and trying, with no keys.

---

*Every clause above traces to a design document in this repository or to Sol's review; where it does not, it is marked as a proposal. The Constitution remains authoritative.*
