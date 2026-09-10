# Objects and facets

**Agora reference documentation — object-layer design ledger.**
Version 0.5 (revised September 10, 2026). Companion to [[Agora Spec]],
[[Design Commitments]], [[Extensions]], [[Reconcilers]], [[Security]] and
[[Native Development]]. Appendix A carries the everyday worked examples.

> **Status.** This document preserves a detailed candidate object model, reasons,
> alternatives and pressure tests. It is not a universal future protocol.
> [[Runtime Guide]] owns the implemented Agora3 API: object-level revisions,
> register replacement and a bounded schema subset. Examples below are
> illustrative unless explicitly labeled current. Alternative models are welcome
> when they preserve the identity, authority, continuity and honesty commitments
> in [[Design Commitments]].

---

## Contents

1. [Ten-minute introduction](#1-ten-minute-introduction)
2. [Core concepts](#2-core-concepts)
   2.1 Entities · 2.2 Identity · 2.3 References · 2.4 Facets · 2.5 Kinds and profiles · 2.6 Identity on demand
3. [Facet reference](#3-facet-reference)
   3.1 The facet definition · 3.2 Authority modes · 3.3 Merge classes · 3.4 Instances and overlays · 3.5 Composition rules · 3.6 A candidate common facet set · 3.7 Minting a vernacular facet · 3.8 Application schemas in the first runtime
4. [Working with objects](#4-working-with-objects)
   4.1 Minting · 4.2 Attaching, updating, detaching · 4.3 Reading · 4.4 Copying · 4.5 Moving · 4.6 Forgetting · 4.7 Sharing across worlds
5. [Actions](#5-actions)
   5.1 The capability contract · 5.2 Effect classes · 5.3 Capability status and parity · 5.4 One-time effects
6. [Relationships and collections](#6-relationships-and-collections)
7. [Projection](#7-projection)
8. [State dimensions](#8-state-dimensions)
9. [Concurrency and conflicts](#9-concurrency-and-conflicts)
10. [Storage and the record](#10-storage-and-the-record)
11. [Interoperability](#11-interoperability)
12. [Invariants](#12-invariants)
13. [Open decisions](#13-open-decisions)
14. [Glossary](#14-glossary)
15. [Appendix A — Everyday subjects (worked examples)](#appendix-a-everyday-subjects-worked-examples)

---

## 1. Ten-minute introduction

In a conventional operating system the unit of persistence is the file: a blob of bytes, a path, and an extension that binds the blob to one application. In Agora the unit is the **entity**: a permanent identity plus an open set of typed components called **facets**. An entity has no class. What a thing *is* — a note, a playlist, a print job, a running prototype — is a reading of which facets are present.

```python
>>> note = world.mint(intent="capture idea from voice note")
>>> note.attach("core.name", {"name": "db latency idea"})
>>> note.attach("core.text", "what if we cached the db queries?")
>>> note.attach("core.tags", ["db", "perf"])
>>> note.reads_as()
'a note'

>>> note.attach("process.spec", {"serve": "/projects/demo", "port": 5173})
>>> world.settle()                       # reconcilers run
>>> note.facets.keys()
['core.name', 'core.text', 'core.tags', 'process.spec', 'process.status', 'core.capability']
>>> note.reads_as()
'a note that is also a running program'
```

Assume the process handler is installed, its source exists and current grants permit execution. Nothing converted. A facet was written through the gateway, a reconciler noticed, and two verbs (`start`, `stop`) appeared in the human's menu and the agent's toolset from the same registry. Views and JEFF refresh that registry; invocation rechecks current authority.

Five things carry the rest of the model:

- **Identity is stable and content-independent.** An id is a name, not a
  credential, and is not silently rebound to an unrelated subject.
- **Facets are one useful model for attributed structured claims.** Independent
  facet revisions, instances and merge classes are candidate machinery; the
  current runtime uses object-level revisions and register replacement.
- **Every native write is an event.** The native log and retained payloads reconstruct native state; independent guest files and external systems have separate retention contracts.
- **Content may live in retained records, ordinary files, blobs or external
  resources.** The object layer should not imprison content or confuse a path
  with a backup.
- **Objects remain usefully inspectable by people and JEFF.** Generic projection
  can precede specialized interfaces; every facet need not ship bespoke pixel
  and token renderers.

If you read nothing else, read §3.5 (composition rules), §5.2 (effect classes), and §12 (invariants).

---

## 2. Core concepts

### 2.1 Entities

An entity is the persistent subject of everyday computing: a document, a recording, a message, an appointment occurrence, a device, a running service, an idea. It has:

| Field | Type | Notes |
|---|---|---|
| `id` | opaque, uniquely issued | Never reused. See §2.2. |
| `genesis` | event ref | The mint event. Carries authenticated origin and world-line. |
| `lineage` | world-line ref | Which branch history the entity was born on. Survives rollback (§10). |
| `lifecycle` | `active` · `dormant` · `archived` · `tombstone` | Projected management state, not age or another immutable identity field. See §4.6. |
| `policy_ref` | grant-set ref | Reference to host policy lookup, not writable authority in the object. The grant language is versioned separately. |
| `facets` | map `(type, key) → instance` | The open bag. See §3. |

This table is the read envelope, not a second mutable object core: lifecycle is derived from native records; effective policy comes from the keep. Deliberately absent: `kind`, `name`, position, content, process handles. All of those are facets or scene records, and therefore evolvable.

An entity identifies a subject **at a useful boundary**, not every piece of implementation state associated with it. A microphone's entity does not replace its driver; a document's entity does not carry each keystroke. See §2.6 for where the boundary goes.

### 2.2 Identity

- **Never reused.** Not across edits, rollbacks, imports, forks, or world-lines. A rolled-back entity resolves to a tombstone that says where and when it existed (§10).
- **A name, not a credential.** Knowing an id grants nothing. Authority comes from grants (§5.1); the id merely designates.
- **Content-free.** Identical bytes do not imply identical subjects; two attachments may share a blob and keep separate histories. Conversely, two encodings may be one recording. Semantic matching may *suggest* relationships; it must never silently merge identities, permissions, or history.
- **Authenticated at issuance.** Issuance handles cloned snapshots and imported data: a copied id string does not establish identity, and an importer that cannot prove origin receives a new id plus a `derived_from` edge.

**Runtime handles are not durable subject identity.** PIDs, connection ids,
compositor surfaces and provider session ids are observations with an
*incarnation*. They may live in status records or domain runtime state; a
reconciler is one possible owner, not the only architecture.

### 2.3 References

A reference names a subject *and says how it means it*:

```
reference:
  entity:    id
  branch:    selected | pinned(branch_id)
  revision:  live | pinned(revision)
  anchor:    optional (facet, key, locator, locator_context)
```

| Interpretation | Answers | Example |
|---|---|---|
| live | "this thing as it currently is" | a desktop shortcut |
| pinned revision | "the version that was attached" | an attachment in a sent message |
| pinned branch | "the one on that world-line" | a citation into a discarded experiment |
| anchor | "this part of it" | a highlight on page 4 of revision 3 |

The human-facing label can be simple ("Travel itinerary"); the distinction must survive serialization and sharing. A message that pins revision 3 is a promise to its recipients that later edits cannot rewrite.

**Resolving is not retrieving.** Resolving a reference, reading retained state, fetching remote content, and invoking an operation are four distinct requests. A persistent id is not a transparent pointer to a live remote object; local inspection discloses missing or stale data without starting network work, and remote fetches carry deadlines, cancellation, and partial-failure semantics.

### 2.4 Facets

A facet is a typed, versioned component describing one aspect of an entity. Each **facet instance** on an entity carries:

| Field | Meaning |
|---|---|
| `type` | Namespaced facet type id, e.g. `core.text`, `sam.trip-meta`. |
| `key` | Instance key, when the type permits several instances (participant, language, device). `-` for singletons. |
| `schema_version` | Which version of the facet definition the body conforms to. Describes *format*. |
| `revision` | Monotonic per instance. Describes *edits*. Never confused with `schema_version`. |
| `body` | Inline value, or a blob reference for large content. |
| `written_by` | Authenticated writer: a person, the daemon, a worker id, a reconciler, an adapter. |
| `via` | The event that produced this revision. |
| `depends_on` | For derived facets: source facet instances and the revisions they were computed from. |

Facets are **claims with authors**, not fields of a globally consistent record. Two facets may disagree; provenance says who said what.

### 2.5 Kinds and profiles

`core.kind-tag` is advisory. It labels the entity for humans and search; no behavior may depend on it. Changing it changes no bytes, grants no access, and makes nothing executable.

A **profile** is a named, tested combination of facets with defaults — "note", "photo", "appointment", "running prototype". Profiles exist for interoperability and convenience. They are not classes: an entity may satisfy several, none, or a profile plus extras.

```python
>>> world.profile("note").facets
['core.name', 'core.text', 'core.tags']
>>> entity.satisfies("note")
True
```

### 2.6 Identity on demand

Not every paragraph, cell, sample, or widget is a top-level entity. Agora uses a gradient of thingness, with promotion upward on demand:

```
content   — data inside a facet body; no identity; free
   ↑ promoted when something references it
anchor    — a stable address: (entity, facet, key, locator)
   ↑ promoted when it needs its own facets, grants, or lifetime
entity    — a full citizen
```

**Rule.** Anything referenced, granted upon, or tracked has identity; nothing needs identity before that.

Anchors require a **domain locator contract**. A character offset or a row number is not stable under edits. Text facets stored as sequence CRDTs provide position ids that survive edits; media uses timestamps; tables use keys. A facet definition that supports anchors declares its locator scheme (§3.1). An anchor also records the revision it was created against so that, after unmappable edits, it resolves to its old revision rather than to a wrong place in the new one.

---

## 3. Facet reference

### 3.1 The facet definition

In this candidate protocol, each facet type has a definition—a **facet-def**.
Built-in definitions ship with the runtime; vernacular definitions can be
retained in the world (§3.7). A facet-def may declare:

| Field | Required | Description |
|---|---|---|
| `type` | yes | Namespaced id. Namespaces prevent `status` collisions across domains. |
| `schema` | yes | Body schema and current `schema_version`. |
| `instances` | yes | `singleton` or `keyed(by: participant \| language \| device \| custom)`. |
| `authority` | yes | Who may write. See §3.2. |
| `merge` | for this protocol | Concurrency semantics. See §3.3. |
| `projection` | yes | How to render at a token budget: a template, a projector ref, or `generic`. See §7. |
| `export` | yes | Serialization for bundles (§11.2): `json`, `blob`, `omit`, `derived`. |
| `locator` | no | Anchor scheme if the facet supports subobject addressing. |
| `depends` | no | Declares this facet as derived, with source facet types. |
| `limits` | yes | Size, compute, and retention bounds. |
| `migrations` | no | Explicit transformations between schema versions, bidirectional where possible. |
| `critical` | no | Supported operation constraints whose absence blocks dependent writes; cannot install arbitrary host code. |

> **Note.** `schema_version` and `revision` are different axes. Upgrading `core.text` from schema v2 to v3 touches nothing else in the system; editing a text bumps its revision and touches no schema.

### 3.2 Authority modes

| Mode | Who writes | Examples |
|---|---|---|
| `intent` | Humans, the daemon, and workers holding a grant | `core.name`, `core.text`, `process.spec` |
| `reconciler` | Only the named reconciler, as an observation with observer, incarnation, time, freshness | `process.status`, `core.file-backing.status`, `core.capability.status` |
| `system` | The platform | `core.provenance`, `core.presence` |
| `derived` | A reproducible transformation naming its inputs | `core.summary`, thumbnails |
| `adapter` | A source adapter observing an external authority | `core.remote-ref` |

**Authority is admitted, not declared.** A facet-def may request `intent` freely. `reconciler`, `system`, and `adapter` modes are granted only when a component is actually installed with the corresponding grants. An invented facet cannot make its author a trusted observer by naming itself `status`.

An observation can be wrong or stale. Reconciler-written facets always carry the desired-state revision they concern and a freshness policy; consumers treat them as evidence, not truth.

### 3.3 Merge classes

| Class | Semantics | Typical facets |
|---|---|---|
| `register` | Multi-value register. Concurrent writes both survive and surface as a conflict object (§9). May declare `lww` for trivial fields. | `core.name`, spec fields, settings |
| `sequence` | Sequence CRDT. Also supplies anchor locators. | `core.text`, `core.collection.entries` |
| `set` | Add-wins observed-remove set. | `core.tags`, membership |
| `reconciled` | One currently admitted writer/incarnation; stale writers are refused. | all `reconciler`/`system` facets |
| `bytes` | Never auto-merged. Divergence forks. | `core.blob`, file-backed content |
| `domain` | Domain contract supplies merge and validation. | structured documents, schedules |

The first local runtime may implement conditional register writes before
multi-writer merging: stale writes return a conflict with the current revision
and append nothing. It must advertise that limitation. A definition cannot select
a merge engine the runtime does not implement; `domain` is not permission to run
arbitrary merge code inside the host.

### 3.4 Instances and overlays

A facet type declared `keyed` may have several instances on one entity. This is how private state attaches to shared subjects without copying them:

```
document_17
  core.reading-position [alex]  {page: 4, anchored_rev: 3}
  core.reading-position [sam]   {page: 1, anchored_rev: 5}
  core.caption [en]  "…"
  core.caption [pt]  "…"
```

An instance keyed by participant is an **overlay**: readable and writable only by that participant (and their daemon), never disclosed through projections to other viewers (§7). Unread state, reading position, scoped presentation preferences, and personal annotations are overlays. A tool updates only the instances it understands and is authorized for; whole-entity replacement is not a write API.

### 3.5 Composition rules

1. **Preserve admitted unknown data.** A reader keeps facets it does not understand — bounded, inert, inspectable through the generic envelope, exportable under applicable permissions.
2. **Unknown action-critical constraints block the dependent operation.** Preserving a signature facet does not keep a signature valid after its content changes. If a facet-def marks a constraint `critical`, tools that do not understand it may read but may not perform the operations it governs. If the platform cannot enforce a required rule, the behavior is not activated.
3. **Track dependencies.** Derived values name their input revisions and become `stale` when inputs change. Stale is a visible state, not an error.
4. **Empty is legal.** A newly minted entity with no facets is a bare identity, not a tombstone. A disconnected device or an unsupported format is an entity with limited operations.
5. **Validate at the operation boundary.** Any set of admitted facets may be retained; not every combination is executable. Coupled invariants (an occurrence must belong to its series) are validated by the domain, atomically, when an operation runs.
6. **Descriptions never grant power.** Authority comes from the registry and policy service. See §3.2.
7. **Make multiple writers explicit.** One authority per value is the simplest
   policy. Two writable representations may coexist when they share a declared
   version, reconciliation and conflict protocol. Independent writers must not
   masquerade as one truth. See §4.5.3 for file-backed content.

### 3.6 A candidate common facet set

Illustrative built-in vocabulary, namespaced `core`. This table records a design
language, not a constitutional promotion or the exact current schemas.

| Type | Body | Instances | Authority | Merge |
|---|---|---|---|---|
| `core.name` | `{name, aliases[]}` | singleton | intent | register |
| `core.kind-tag` | `{kind}` advisory | singleton | intent | register (lww) |
| `core.text` | sequence of text with position ids | singleton | intent | sequence |
| `core.blob` | `{hash, media_type, size}` | keyed by role | intent | bytes |
| `core.doc` | structured document | singleton | intent | domain |
| `core.file-backing` | `spec {path}` · `status {path, inode, hash, checked_at}` | singleton | spec: intent · status: reconciler | spec: register · status: reconciled |
| `core.remote-ref` | `{provider, account, provider_id, incarnation}` · `status {fetched_at, freshness}` | keyed by provider | adapter | reconciled |
| `core.tags` | `set<string>` | singleton | intent | set |
| `core.summary` | `{text, from: [facet@rev]}` | keyed by producer | derived | register |
| `core.provenance` | `{created_by, on_behalf_of, derived_from[]}` | singleton | system | reconciled |
| `core.presence` | `{focused_at, salience, checkpoints[]}` | keyed by participant | system | reconciled |
| `core.reading-position` | `{page \| anchor, anchored_rev}` | keyed by participant (overlay) | intent | register |
| `core.collection` | explicit `entries: sequence<{entry_id, target ref}>` **or** a saved `query`; query results are derived | singleton | intent for definition | sequence for entries; register for query |
| `core.capability` | `spec {declared verbs}` · `status {effective verbs}` | singleton | spec: intent · status: reconciler | spec: register · status: reconciled |
| `core.retention` | `{pinned_until, reason, dependents[]}` | singleton | intent or system | register |

**The liveness pair is a pattern, not a facet.** Any domain that maintains intent declares `<domain>.spec` (authority `intent`) and `<domain>.status` (authority `reconciler`): `process.spec/status`, `download.spec/status`, `playback.spec/status`. See §5.2.

**Appearances need independent semantics.** Separate scene records are the richer
candidate model because one subject may appear in several places with different
transforms. The current bootstrap instead stores `core.appearance` on note
subjects. Facets, scene records and adapters are all possible encodings if they
preserve the identity and lifecycle of distinct uses.

The scene itself can carry a proposed `core.scene` facet: scene settings and
appearance references, with intent authority. Settings use register semantics;
appearance membership uses a sequence. Placements remain separate scene records,
for example:

```json
{
  "id": "a17",
  "scene": "scene_desk",
  "subject": {"entity": "note_12", "revision": "live"},
  "revision": 8,
  "transform": {"x": 40, "y": 30, "scale": 1}
}
```

A placement operation should check the relevant revision it read. A batch
arrangement may commit several placements together. The richer appearance model
would keep independent uses distinct; the current bootstrap stores position on
the note's `core.appearance` facet. Indexes and query results remain derived.

### 3.7 Minting a vernacular facet

A vernacular facet type is created by minting a `facet-def` entity — an ordinary event.

```python
>>> world.mint_facet_def(
...   type="sam.trip-meta",
...   schema={"days": "int", "hotels": "int", "notes?": "text"},
...   instances="singleton",
...   authority="intent",
...   merge="register",
...   projection="{days}-day trip, {hotels} hotels",
...   export="json",
...   limits={"max_bytes": 4096},
... )
facet-def sam.trip-meta v1
>>> document_17.attach("sam.trip-meta", {"days": 5, "hotels": 2})
```

Once the definition is validated and admitted, authorized writers may attach `sam.trip-meta`. No global schema migration or new host code is needed. To evolve it, mint an immutable v2 definition; instances on v1 remain v1 and readable. Read translations are explicit derived views. Persisted migrations are separate revision-checked actions, not code executed during replay.

Soft semantics is the nursery for schema. Free tags, annotations, and ad-hoc key-values need no definition and cost nothing to write; when the same shape recurs across many objects, that recurrence is the signal to mint a vernacular facet-def for it rather than keep hand-writing its projection. The recurrence thresholds, and the search-before-mint rule that decides whether to reuse, extend, or mint, are in [[Extensions]] §4.1–4.2.

> **Warning.** Requesting `authority: reconciler` in a vernacular facet-def is refused unless the requesting component is installed as a reconciler with grants (§3.2).

### 3.8 Application schemas in the first runtime

The shorthand schema in §3.7 explains the idea. A proposed stored definition uses
a bounded JSON Schema subset, for example:

```json
{
  "type": "alex.review",
  "schema_version": 1,
  "schema": {
    "type": "object",
    "properties": {
      "state": {"type": "string", "enum": ["draft", "review", "done"]},
      "comment": {"type": "string", "maxLength": 2000}
    },
    "required": ["state"],
    "additionalProperties": false
  },
  "instances": "singleton",
  "authority": "intent",
  "merge": "register",
  "projection": "generic",
  "export": "json",
  "limits": {"max_bytes": 4096}
}
```

Agora3 now implements application-schema admission with a bounded JSON Schema
subset. This example explains the longer design and is not the exact operation
envelope; [[Runtime Guide]] owns current fields and limits. Records, strings,
numbers, booleans, enums and lists have explicit size and nesting bounds. Remote
schema references do not trigger implicit fetches.
Unknown schema features are refused at definition admission; already retained
unknown facets remain inert and inspectable.

```python
review_def = world.mint_facet_def(review_definition)
note.attach(review_def, {"state": "draft"}, if_absent=True)
revision = note.facet("alex.review").revision
note.update("alex.review", {"state": "review"}, expected_revision=revision)
# A competing edit makes the last operation refuse, rather than overwrite.
```

A generic inspector shows the type/version, field values, writer and revision.
JEFF reads the same facts in its projection. Calling the field `state` or `status`
does not make it a privileged runtime observation: this is user-authored review
content. Migration to a later definition records resulting facet writes; installing
an older package cannot silently restore older data.

---

## 4. Working with objects

### 4.1 Minting

A mint is an event before it is anything else. It records who minted, on whose behalf, from what, and why.

```python
>>> proto = world.mint(
...   intent="spin up a demo of the caching idea",
...   derived_from=[idea_37, paper_8],
...   on_behalf_of=alex,
... )
```

| Path | Who | Notes |
|---|---|---|
| direct | humans, the daemon | free |
| granted | workers | requires a mint grant with quota |
| ingest | source adapters | one entity per source item, matched by provider binding (§11.1) |
| promotion | anyone with a reference | anchor → entity (§2.6) |
| fork / cast / stamp | see §4.4 | records kinship |
| nursery | worker swarms | provisional world-line; see below |

**Nurseries.** High-volume minting (a research worker tagging ten thousand candidates) happens in a provisional world-line with its own log. Objects promote into the world when something outside the nursery references, adopts, or grants on them. On close, the nursery is swept in one recorded event; its log compacts to a summary; ids are never reused; later references to swept ids resolve to the sweep event. Nothing referenced is ever swept.

**Templates.** Minting from a template copies facet defaults and records `instance_of`. Template updates propagate by offer and consent, never by push (§4.4).

**Living queries.** A saved-query collection records its query; the index maintains a derived result, never another writable membership list. Sharing one requires either freezing membership as of an event or explicitly granting the dynamic view (§6).

### 4.2 Attaching, updating, detaching

All three are the same mechanism: a facet write producing a new revision, recorded as an event.

```python
>>> note.attach("process.spec", {"serve": "/projects/demo", "port": 5173})
event e6120 (intent: attach process.spec) → note_12 process.spec rev 1
>>> note.update("process.spec", {"port": 5174})
event e6131 → rev 2
>>> note.detach("process.spec")
event e6140 → retracted (rev 3); body retained in history
```

Pipeline for every write:

1. **Authority check.** The facet-def's mode admits this writer; the writer holds a grant covering this entity and facet.
2. **Validation.** Body conforms to `schema_version`; domain invariants declared `critical` are checked; coupled writes are grouped under one intent (§10.2).
3. **Append.** The event is written with intent, effects, writer, and revision.
4. **Fold.** The materialized store applies the effect. Indexes update. Subscribed lenses re-render.
5. **Reconcile.** Reconcilers whose inputs changed wake: attaching `process.spec` causes the process reconciler to attach `process.status`; the capability reconciler recomputes `core.capability.status`.

Concurrency uses optimistic compare-and-set on the instance revision in single-writer situations and the merge class otherwise (§9).

**Undo** is an inverse event, never log revision. Selective undo in shared sequences is an open decision.

### 4.3 Reading

```python
>>> document_17.facets                       # all instances, as claims
>>> document_17.facet("core.text")            # current revision
>>> document_17.facet("core.text", rev=3)     # retained revision
>>> document_17.facet("core.reading-position", key=alex)
>>> document_17.project(viewer=alex, budget=50)   # see §7
>>> document_17.capabilities(participant=alex)    # effective verbs
```

Reading never triggers remote fetches implicitly. A remote-backed facet reports `availability` (§8) and fetches only on an explicit, cancellable request.

### 4.4 Copying

People can use an ordinary Copy or Duplicate operation. Its domain contract
chooses among several semantics; the four verbs below are a useful vocabulary,
not the only allowable interface:

| Verb | Result | Use |
|---|---|---|
| **reference** | same entity, another appearance or membership | "on the desk *and* in the project" |
| **fork** | new id; `derived_from` + fork event | divergent sibling with a shared past |
| **cast** | new immutable id pinned to an event | citation, export, audit — the PDF of a living thing |
| **stamp** | new id; `instance_of` template; updates by offer | instance of a pattern |

What transfers:

| | reference | fork | cast | stamp |
|---|---|---|---|---|
| content | shared | copied (lazy bytes) | frozen copy | from template |
| provenance | shared | kept + fork event | kept + cast event | `instance_of` recorded |
| outbound edges | shared | optionally re-asserted as *inherited* | frozen snapshot | — |
| inbound edges | shared | never | never | never |
| presence / overlays | shared per participant | never | never | never |
| **grants** | same object | **never** | **never** | **never** |

**Content transfer does not silently transfer grants.** A reference may retain
the authority already attached to the same subject, while a new copy, fork, cast
or stamp receives authority through its own operation. Forking shared words does
not automatically copy their audience or executable capabilities.

Bytes are lazy: content-addressed blobs fork for free; file-backed content uses filesystem reflinks where available and copy-on-first-write otherwise.

### 4.5 Moving

"Move" names four unrelated operations.

**4.5.1 Scene.** Changing an appearance's transform. Cheapest event in the system. Never touches the entity.

**4.5.2 Collections.** Membership is non-exclusive: one entity may sit in many collections without copies. Ordered collections give each **entry** its own identity distinct from its target, so a recording may appear twice and moving one entry moves nothing else. Exclusivity ("a section belongs to one document") is a constraint a collection may declare, not a system rule.

**4.5.3 Bytes.** `core.file-backing` can be modeled as desired binding plus
observed state. A file watcher or other adapter may observe renames and attempt
to preserve continuity. One writer is simplest, but a native facet and external
file may both be writable when they participate in one explicit revision,
conflict and reconciliation protocol. Historical bytes require retained payloads
or a verifiable snapshot, not merely a path.

**4.5.4 Worlds.** See §4.7.

### 4.6 Forgetting

`lifecycle` is a management state, not an age. Transitions are deliberate and recorded:

```
active ⇄ dormant ⇄ archived → tombstone
```

- **Attention is never sufficient reason.** An object untouched for years may be pinned by `core.retention`, required by a dependent record, or simply chosen. The lifecycle reconciler proposes; it does not dispose.
- **Verbs are distinct.** *Close* a view, *stop* an activity, *disconnect* a device, *remove from this collection*, *drop local bytes*, *cancel future occurrences*, *archive*, and *erase* are different operations with different targets. Action contracts preserve the distinction.
- **Tombstones resolve honestly.** A tombstone keeps the frozen core plus a **terminal projection** — a last gist so references from memory resolve to meaning, not to a husk — *unless erasure was requested*, in which case only permitted minimal resolution information remains.
- **Erasure must become real.** A person's erasure request should reach retained
  revisions, derived content, attachments, indexes, memory and backups within a
  declared horizon. The interaction among evidence, erasure, shared history and
  fork rights remains an open implementation and policy obligation
  ([[Constitution]] Articles I, IV and V).

Old references resolve to exactly one of: current subject · pinned historical revision · absent on this branch · content unavailable · content erased · inaccessible-or-unknown. Never to a similar object substituted for the one that is gone. Privacy may require inaccessible and unknown to be indistinguishable.

### 4.7 Sharing across worlds

**Residency needs a declared contract.** One log of record is the current
simplifying proposal. Replicated or distributed authority remains open, while
visibility may be plural.

| | Lending (guest) | Giving (custody transfer) |
|---|---|---|
| mechanism | a grant to the room | a two-log handshake event |
| log of record | stays home | moves to the room |
| edits made in the room | events in the home log with `via: room` provenance; the room records a witness event | events in the room log |
| on leaving | grant lapses; guest goes home; the room's witness record remains | n/a — it lives there now |
| id | unchanged | unchanged; `lineage` notes the emigration |

Imported objects are quarantine-tagged at adoption: facets written by unvetted writers carry foreign provenance until deliberately promoted, because durable writes cannot be untagged into trust later.

On dissolution (a room forks), guests return home automatically and residents fork to both successors, each fork recording the divergence.

---

## 5. Actions

### 5.1 The capability contract

A **handler** is a component that performs one verb on entities with certain facets. It registers a **manifest**:

```yaml
verb:        video.trim
applies_to:  { facet: core.blob, media_type: video/*, schema_version: ">=2" }
params:      { start: time, end: time }
effect:      content-edit
needs:       [read core.blob, write core.blob.revision]
describe:    "Trim a video to a range"
```

| Field | Meaning |
|---|---|
| `verb` | Namespaced verb id. |
| `applies_to` | Supported inputs. Structural facet requirements are dependable; advisory tags may assist selection but do not prove semantics or authority. |
| `params` | JSON-schema parameters. Generates both form fields and tool schemas. |
| `effect` | Effect class (§5.2). Determines undo, confirmation, and replay behavior. |
| `needs` | Grants requested. A request, never a grant. |
| `describe` | Human- and model-readable description. |

The manifest format is deliberately shaped like the tool-description format language models are trained on, so projection into an agent's context is nearly the identity function and the agent can author manifests fluently.

### 5.2 Effect classes

| Class | Example | Required semantics |
|---|---|---|
| `content-edit` | change a caption | revision-aware; undo is a new revision |
| `organization` | move a playlist entry | stable entry identity; order and membership rules |
| `view` | open another reader | session scope; no content copy |
| `maintained-intent` | keep a download progressing, serve a demo | writes a `spec`; a reconciler drives `status` toward it within allowed effects, ownership, limits, and stop conditions |
| `one-time-effect` | send, print, pay, deliver a reminder | frozen payload; operation identity; durable outcome; see §5.4 |
| `resource-use` | start a call, route audio | current grants; session identity; explicit fallback policy for requested vs effective resource |
| `setting-change` | choose default output | preference scope and effective-value derivation; never retargets already-submitted operations |

> **Warning.** Do not apply `maintained-intent` semantics to a `one-time-effect`. A reconciler that retries "send" until it observes success is how a rebooted machine mails an email twice.

### 5.3 Capability status and parity

One candidate models `core.capability` as a spec/status pair:

- `capability.spec` — verbs *offered*, declared by handlers and authors.
- `capability.status` — verbs *effective* for a participant on this entity now,
  possibly computed from installed manifests, supported inputs and grants.

Human controls and daemon tools should share semantic action contracts where
useful, filtered by caller authority. They need not be identical projections,
and local gestures need not all become public actions. Installed actions remain
discoverable when their lens closes. Uninstalling disables new calls without
deleting subject data; running invocations and dependent installations follow
[[Native Development]] §4.

Registry changes carry a revision so JEFF can refresh discovery within a session. A listed verb still executes through its pinned handler revision and may fail; failure is a recorded outcome, and a manifest that over-claims gains nothing from claiming.

### 5.4 One-time effects

```
send_operation_7:
  operation_id:  op-91f4            # idempotency key
  payload:       message body @ rev 3, attachments [document_17 @ rev 3]   # frozen
  target:        conversation_5 via account alex@…
  outcome:       pending | accepted | rejected | unknown
  receipts:      [...]
```

- The payload is a cast. Editing the draft after submission changes nothing already sent.
- `unknown` is a meaningful, durable outcome. Absence of a local receipt is never evidence the effect did not happen.
- Restore, replay, and reboot never repeat an effect. Resolution of `unknown` is an explicit verify-by-operation-id request under the domain's retry policy.
- Related verbs — *retract*, *recall*, *cancel* — are separate one-time effects with their own outcomes, and none promise recall of content already held by independent recipients.

---

## 6. Relationships and collections

An **edge** is a first-class record:

```
edge:
  id
  from / to:    entity ids or anchored references
  predicate:    namespaced; open vocabulary
  asserted_by:  authenticated writer
  via:          event ref
  confidence:   optional
  retracted:    optional event ref
```

- **Retraction, not deletion.** An edge is unsaid by a later event; the store shows only active edges; history keeps both.
- **Typed vs loose predicates.** Typed relations (`core.member_of`, `core.attached_to`, `core.derived_from`) declare operational semantics. Loose predicates (`reminds_me_of`) aid retrieval and never govern deletion, access, or traversal into private content. Inferred edges are claims, marked as such.
- **One authoritative encoding.** Explicit collection membership lives in `entries`; a saved-query collection instead stores a query whose results are derived. Back-edges and query caches are never a second writable authority.
- **Edges promote.** An edge that needs annotation, dispute, or grants becomes an entity carrying `core.edge-of` (§2.6).
- **Edges age.** Salience decay applies to relations; never-traversed loose edges thin toward archival like objects do.
- **Many edges are views of events.** `derived_from` is born from the mint event; n-ary origins are one event referencing several sources.

**Ordered collections** give each entry its own identity. **Saved-query collections** store the query and support membership-as-of; "share these results" freezes the members or explicitly grants the dynamic view — later matches must not silently become new disclosures.

**Cross-world references** are `(world-line, entity)`. Humans and daemons use **petnames**: local names bound to global ids, maintained per person, exchanged socially. There is no global namespace to capture.

### 6.1 A notes lens that follows the scene

A live binding stores a query rather than enumerating today's note IDs.
A proposed query record is:

```json
{
  "scope": {"scene": "scene_desk"},
  "require_facets": ["core.text"],
  "result": "appearances",
  "order": [{"field": "appearance.id", "direction": "asc"}],
  "limit": 200
}
```

The first query vocabulary is intentionally small: scene or collection scope,
required facets, typed field comparisons, ordering and a bound. A review board can
add a predicate on `alex.review.state`. Query predicates are data interpreted by
the protected read service, not arbitrary SQL or package code running there.

Use appearance results when placement matters. Two appearances of the same note
stay distinct. An entity-result query explicitly deduplicates by entity instead.
Stable ordering needs a tie-breaker, and derived result keys come from underlying
identities rather than being minted on every refresh.

A subscription supplies an authorized snapshot, an opaque watermark, bounded
items, a completeness flag and an optional cursor. Changes after that watermark
must either arrive without gaps or signal that a new snapshot is required.
Pagination uses the same snapshot; it must not silently mix several revisions.

| Change after installation | Lens behavior |
|---|---|
| A matching note is placed in the scene | A result appears without a source or binding rewrite |
| The same note gains a second appearance | Appearance mode shows two placements; entity mode still shows one note |
| A selected appearance is removed | Report that it left the view; do not select a neighboring result silently |
| More matches exist than the limit | Show truncation/pagination rather than implying the result is complete |
| A connection or authorization changes | Recheck access and resume safely or obtain a fresh filtered snapshot |

Queries select; grants authorize. The development profile may cover current and
future local notes, but narrower sharing must specify whether future matches
are included. A shared query does not disclose unauthorized items through result
counts, cursors, thumbnails or notifications.

Transient query indexes are replay-derived caches. Freezing a result is an explicit
native operation that creates retained membership. That distinction keeps the
live board useful without adding another source of truth.

---

## 7. Projection

Every useful subject needs an understandable human and agent representation, but
not every facet requires its own bespoke renderer. Generic inspection is a valid
first representation. Specialized views and token projections can be supplied by
trusted runtime code or admitted packages under an explicit execution boundary;
imported data does not gain authority by describing a projector.

```
project(reference, viewer, purpose, budget)
  → observed facts and their freshness
    attributed claims with sources
    permitted actions (or discovery refs)
    omissions, conflicts, stale dependencies
```

Rules:

1. **Filter before summarizing.** Overlays, presence, and room-private history are removed for the viewer and destination *before* any summary is composed. Derived summaries inherit the restrictions and revision dependencies of their sources.
2. **Attribute untrusted claims.** A `core.summary` written by a low-trust worker renders with its `written_by` visible. Provenance indicates origin, not correctness.
3. **Never shorten away uncertainty.** A print job's `outcome: unknown` is never projected as "done"; a call's projection preserves whether the microphone is live.
4. **Tiers.** Approximately `[12 / 60 / 250 / 2000]` tokens; cache keys include the selected revisions, purpose and effective access policy, not merely a coarse viewer class. Invalidate on data or authority change. The context assembler allocates across entities by salience; the entity projector allocates across facets by class weights.
5. **Terminal projection.** Archived and tombstoned entities keep a final gist unless erased (§4.6).

```
>>> document_17.project(viewer=alex, budget=12)
'Travel itinerary, r5, local; your spot: page 4'
>>> document_17.project(viewer=room_R, budget=12)
'Travel itinerary, r5, local'
```

Deixis resolves against interaction context — the focused appearance, selection, and recency — not against the pointer's position after speech recognition finishes. "The next one" resolves against a particular collection ordering.

---

## 8. State dimensions

One lifecycle field cannot describe an object. Six independent dimensions apply; domains supply the meaningful values.

| Dimension | Question | Example values |
|---|---|---|
| existence | Does this subject exist in the selected history? | active · archived · tombstone · absent on this branch |
| revision | Which content or claim is this? | current · pinned · conflicted · derived from old inputs |
| availability | Can the bytes or resource be reached? | local · remote · offline · partially cached · missing |
| activity | What is happening? | playing · idle · connecting · pending · outcome unknown |
| attention | How is it presented to this participant? | focused · recent · muted · hidden |
| authority | What may this participant read or cause? | owner · read-only · restricted · expired grant |

An archived recording may be playing. An active document may be offline. A hidden process may be consuming resources. Low attention is never, by itself, evidence that an object may be deleted.

---

## 9. Concurrency and conflicts

Merge policy belongs to the facet-def (§3.3). Supported sequence and set contracts can merge automatically. Conditional local writes refuse stale revisions without mutation; admitted concurrent branches use the following conflict representation:

**Conflict-as-object** is useful when competing intent must remain durable and
addressable. Many technical races are better handled by a stale refusal, compact
diagnostic or domain merge without minting another object. When alternatives do
become a conflict entity, retain their authorship and resolve through an explicit
operation.

Operations declare their reads as well as their writes. Validation checks the read revisions and commits coupled changes atomically, or records a proposed change awaiting reconciliation. Domain undo must not erase another participant's unrelated changes.

Because sequence facets are built from authored operations, per-span provenance (who wrote this word) exists structurally; showing it is a lens choice.

Views and adapters need bounded observation protocols: a snapshot at a known
revision, ordered changes or an explicit gap, and resynchronization after loss.
Scoped queries and subscriptions reduce broad scans, but a bounded enumeration can
be legitimate during prototyping or for small worlds. Duplicate deliveries must
not become duplicate domain effects.

---

## 10. Storage and the record

### 10.1 The stack

```
protected authority and recovery evidence
  grants, revocation generations, genesis evidence, effect outcomes
        │
protected native event log                 ← authoritative native record
        │ fold
materialized store (SQLite-class)          ← rebuildable
  entities · facets · edges · anchors · conflicts
        │ references
bytes
  content-addressed blob store (immutable artifacts)
  real filesystem via core.file-backing (documents, projects, code)
        │ indexed by
derived indexes                            ← disposable
  full-text · embeddings · graph · event query
        │
runtime adapters and controllers
  expiring observations, transient activity streams
```

The authoritative event log and retained native payloads are outside guest-root authority; guest clients use the host gateway. Guest filesystem resources are independent unless explicitly captured. Protection and restore domains must be real: excluding a directory from snapshots does not protect it from root inside the VM (see [[Security]] and [[Native Development]] §2).

### 10.2 Events are intents

The unit of the log is an intent under which effects group:

```
e6120  intent: "spin up a demo of the caching idea"   by: jeff  for: alex
       effects:
         mint prototype_117
         edge prototype_117 derived_from idea_37
         write prototype_117 process.spec rev 1
         write prototype_117 core.name rev 1
```

Native changes in one transaction commit atomically. Grants live in the keep and external effects use separate operation records; neither is made atomic with native data by placing it under the same intent label. A task can group several committed transactions and receipts. The log reads as reasons. Durability and human-readable history differ in granularity: accepted edits persist per the durability promise; an editing session presents as one coalesced activity without losing recovery information. Continuous media and input streams stay outside ordinary facet mutation except for explicit checkpoints.

### 10.3 Restore and replay

- **Current replay is pure reconstruction.** It rebuilds native records without
  executing package source or model calls. Current delegation and revocation live
  outside that replay.
- A richer branch restore could select a prior native state and retain enough
  provenance for references into the abandoned future to fail or resolve honestly.
  Exact world branching is not implemented by Agora3.
- A future witness or other JEFF-memory mechanism should retain useful reasons for
  recovery subject to correction, retention and erasure. No irreversible witness
  store is implemented or required.
- **The current journal is append-only.** Compaction and payload erasure are future
  contracts; if introduced, they must state what remains and preserve promised
  reference semantics.

---

## 11. Interoperability

### 11.1 Source adapters

An adapter maintains explicit bindings — `(account, provider object id, incarnation)` — in `core.remote-ref`. Repeated observation of the same source item updates the binding rather than minting duplicates. A source without durable identifiers needs a documented matching policy and an explicit `uncertain-match` state. Adapters handle missed events, renames, and replacements explicitly; a directory watch is not a history.

### 11.2 Export bundles

A future portable entity, collection or world export could use a bundle like:

```
bundle/
  manifest.json      ids, facets (per facet-def export mode), edges, provenance
  blobs/<hash>       fully included content
  refs.json          references that still require another service, marked as such
```

The manifest distinguishes fully included content from references. A useful export
should remain readable when the original tool and daemon are unavailable
([[Constitution]] I.2, III.6, V.1). Agora3 does not yet establish this general
bundle or an independent deployable export path.

### 11.3 Compatibility

- Declare supported `schema_version`s and migrations. Read-only inspection is preferable to a lossy edit disguised as support.
- An operation contract that changes its effect — "share this frozen revision" becoming "share this live subject" — is a new contract version requiring fresh authorization; old approval never silently broadens.
- Code rollback and data rollback are different operations. Restoring an older tool after newer data exists requires a compatible reader, a declared translation, or an explicit read-only state. A failed migration never leaves half the authoritative facets in each format.
- The OS should remain useful without the daemon: identity resolution, basic
  search, direct controls, inspection and export should not require a model. The
  daemon helps with discovery, explanation and proposing adaptations; authorization
  and validity remain machine-checkable at their trusted boundary.

---

## 12. Invariants

The durable object-layer commitments are:

1. Stable identity is distinct from content and authority; an id is a name, not a credential, and is not silently rebound to an unrelated subject.
2. A reference says enough to preserve what the person meant—live or pinned, subject or occurrence, with domain anchor context where it matters.
3. Unsupported semantics block the operations that depend on them, not safe inspection of otherwise inert data. Revision and merge granularity may be object-, facet-, field- or domain-specific.
4. Important accepted claims retain useful authorship and provenance. Observations remain distinguishable from intent and may need observer, incarnation and freshness.
5. Per-participant state has explicit scope and stays private by default; copying or publishing includes it only through a deliberate authorized operation.
6. Existence, revision, availability, activity, attention and authority remain distinguishable; low attention is not sufficient reason to delete.
7. Replay reconstructs recorded native state without executing code or restoring revoked authority. External operation retry follows the actual protocol rather than replay.
8. Copy, reference, fork, cast and template instantiation may all be valid domain operations. Content transfer does not silently transfer audience, presence or executable authority.
9. Stale conditional writes are refused or explicitly rebased. Domains that admit concurrent work expose, preserve or resolve alternatives under a declared policy rather than silently losing them.
10. Subjects remain inspectable to people and JEFF, filtered by viewer where needed; generic representations may precede specialized ones.
11. Human controls and daemon actions share semantic contracts where useful while retaining different projections, gestures and principal authority.
12. Retained bytes, files, blobs and external sources state the availability, authority and export guarantees they actually make. A path or hash alone is not a backup.
13. The object layer remains usable and inspectable without a model; practical export is a commitment whose concrete path still needs evidence.

The remaining detailed rules in this note—kind-free dispatch, facet-level writers,
spec/status pairs, dependency staleness, singular residency, conflict entities,
nurseries, projection tiers and one computed action list—are candidate contracts.
They may become local invariants when an implementation or interoperability domain
adopts and tests them; they are not universal prerequisites for Agora.

---

## 13. Open decisions

Left open until exercised by conformance cases:

- exact id encoding and issuance protocol across hosts;
- canonical serialization and the bounded application-schema vocabulary proposed in §3.8;
- sequence CRDT selection and anchor locator formats per facet family; preserve creation revision and quoted context where a locator alone is insufficient;
- conflict-object UX and the daemon's adjudication limits;
- projection tier sizes and budget negotiation between assembler and salience;
- custody handshake protocol across federated hosts and its failure modes;
- nursery promotion thresholds and worker quotas;
- edge decay function;
- retention, compaction, and erasure horizons, and their reconciliation with the record and fork rights;
- per-span provenance storage cost and compaction;
- stamp-update consent defaults;
- whether casting another participant's shared object is a right or a grant;
- entity store engine and log framing, with replay equivalence and crash recovery as acceptance obligations.

---

## 14. Glossary

**Anchor** — a stable address into a facet: `(entity, facet, key, locator, revision context)`.
**Appearance** — a scene record placing an entity on a surface with a transform. Entities have no position of their own.
**Cast** — an immutable entity pinned to an event; a frozen witness of another entity.
**Conflict entity** — an object holding every branch of an unmergeable concurrent write, awaiting a resolution event.
**Custody** — the log of record for an entity. Transfer is a two-log handshake.
**Daemon** — a person's persistent agent (JEFF). Loyal to its person; informs, never votes.
**Effect class** — the lifecycle category of a verb: content-edit, organization, view, maintained-intent, one-time-effect, resource-use, setting-change.
**Entity** — a permanent identity plus an open bag of facets.
**Entry** — an element of an ordered collection, with identity distinct from its target.
**Facet** — a typed, versioned, instance-keyed claim about one aspect of an entity.
**Facet-def** — the definition of a facet type: schema, authority, merge, projection, export, limits.
**Fork** — a new entity with a shared past, recorded by a fork event.
**Guest** — an entity visible in a world where it is not resident, by grant.
**Handler** — a component that performs one verb; registers a manifest.
**Lens** — a surface plus its bindings and exposed capabilities; subject data survives its closure, and view-instance state has an explicit owner.
**Manifest** — a handler's typed declaration: verb, applies-to, params, effect, needs.
**Nursery** — a provisional world-line for high-volume minting.
**Operation identity** — the idempotency key of a one-time effect.
**Overlay** — a participant-keyed facet instance; private state on a shared subject.
**Petname** — a local, human name bound to a global id.
**Profile** — a named, tested facet combination with defaults; not a class.
**Projection** — rendering an entity into pixels or tokens at a budget, for a viewer.
**Reconciler** — the sole writer of a status facet; drives observed state toward spec within allowed effects.
**Residency** — the world-line whose log is an entity's log of record.
**Stamp** — an instance of a template, with standing `instance_of` and update-by-offer.
**Terminal projection** — the last gist retained by an archived or tombstoned entity, subject to erasure.
**Tombstone** — the frozen core of a departed entity, resolving references honestly.
**World-line** — a branch of history with its own log.

---

## Appendix A. Everyday subjects (worked examples)

*These examples live with the contracts they exercise. They omit wire-format details and illustrate equally important cases, not a sequence every object passes through. [[Object Use Cases]] pressures each of these cases further; [[Native Development]] adds the authored notes-board lifecycle.*

### A.1 What an object identifies

An entity has a stable identity and a set of typed facets. It identifies a subject at a useful boundary, not every piece of implementation state associated with that subject.

| Distinction | Example |
|---|---|
| Subject and revision | A document remains the same document after an edit; a citation may pin its earlier revision. |
| Subject and representation | A photo appears in an album, a search result, and an editor without becoming three photos. |
| Subject and activity | A recording exists when nothing is playing it; a playback session can move between recordings. |
| Subject and location | A file move changes a binding; a new file at the old path is not automatically the old document. |
| Subject and occurrence | A playlist can contain the same recording twice; each entry has a distinct position and identity. |
| Subject and access | A remote document can remain known while its contents are offline or permission has expired. |
| Subject and role | A particular printer is different from the preference “default printer.” |

Identity stability does not mean every property stays fixed. It means references continue to designate the subject they were issued for, and changes of subject are explicit.

### A.2 A document being read

```text
document_17:
  name: Travel itinerary
  content: retained PDF revision 3
  source: attachment source with its own provenance
  annotations: highlights anchored to content revisions

reading state, scoped to Alex:
  subject: document_17
  anchor: page 4 in revision 3

reader_session_2:
  subject: document_17, live revision policy
  view: Alex's desktop
  current selection: a versioned region
```

The document can remain unchanged for years. Reading enriches personal position and optional annotations without changing shared content. If the source is revised, an old anchor remains tied to its old revision until safely mapped or explicitly reattached. Closing the reader does not archive the document. Removing a download does not erase the subject if another source remains.

### A.3 Music and playback

```text
recording_8:
  media: duration, content/source identities, supported representations
  description: title and artist assertions

playlist_4:
  entries:
    entry_11 -> recording_8
    entry_12 -> recording_9
    entry_13 -> recording_8

playback_session_2:
  selected entry: playlist_4 / entry_13
  intent: playing, requested output headphones_2
  observation: buffering; output not yet connected
  resume policy: remember position, do not auto-play after reboot
```

Moving `entry_13` does not move `entry_11`. Pausing playback does not mutate the recording. Requested output and effective output are separate; headphones disappearing must follow an explicit fallback policy, particularly during private listening or calls. Playback time is sampled activity state, not a permanent content edit for every audio frame.

### A.4 Messages and conversations

```text
conversation_5:
  participant references and message relationships

draft_12:
  editable body and attachment selections
  intended conversation: conversation_5

send_operation_7:
  frozen body and attachment revision references
  account and destination
  operation identity
  outcome: pending | accepted | rejected | unknown

message_19:
  source binding and sent-content provenance
  delivery observations
```

The domain protocol must specify whether submission preserves a draft's identity or creates a message linked to it; it must not silently retarget old draft references. Editing a draft after submission must not alter the frozen payload already sent. One person's unread state is a private overlay, not a claim that everyone has read the message. A conversation and its active call have independent lifetimes. Deleting a local message view does not retract a remotely delivered message.

### A.5 Appointments and reminders

```text
appointment_series_6:
  schedule: local civil time, time zone, recurrence definition
  participants and exceptions

occurrence_21:
  belongs to appointment_series_6
  stable occurrence key
  scheduled time and any explicit exception

reminder_12:
  target: occurrence_21
  timing and delivery policy
  delivery-operation references
```

A series is not one occurrence. Moving a single occurrence must not detach old references or move the whole series. A recurrence edit needs explicit scope: this occurrence, future occurrences, or the series. Reopening a calendar does not create new reminder deliveries. An overdue reminder after restart needs a catch-up policy rather than automatic repeated notification.

### A.6 Devices and jobs

```text
printer_3:
  device binding and identity evidence
  supported operations
  connection/capability observations with freshness

preference, scoped to Alex:
  default printing target: printer_3

print_job_9:
  target: printer_3
  input: document_17 revision 3
  requested copies: 1
  submission identity and observed outcome
```

Changing the default printer does not retarget an already submitted job. A new device at the same address is not automatically the same trusted printer. If the printer accepted the job but the acknowledgment was lost, a restart must not silently produce another physical copy. Unknown outcome is meaningful state.

### A.7 Creation remains supported

A code project may have file bindings and optional service intent; a worker job may produce a changeset; a prototype may be derived from a note. These use the same reference, operation, and authority rules. They are one family among the preceding uses, not the reference example for every mechanism.
---

*This reference preserves the full object-model argument. [[Design Commitments]]
names the durable ends; [[Runtime Guide]] and [[Implementation Status]] distinguish
the implemented subset from worked designs and open mechanisms.*
