# Agora objects

*Core design for persistent objects, facets, references, and their storage. Revised around everyday OS use. This is a design specification, not a claim that these mechanisms are implemented. The Constitution remains authoritative; unresolved enforcement and retention choices are identified below and in [[Security Model]].*

## 1. Purpose and scope

**Objects are the persistent subjects of everyday computing.** A person reads a document, listens to a recording, receives a message, moves an appointment, chooses an output device, and returns to a folder. Those subjects should retain understandable identities across views, applications, sessions, and machine restarts.

An object need not belong to a project, originate in an idea, acquire behavior, or produce another object. Most everyday objects may never be edited. Software creation and Agora improving itself are supported uses of this foundation, not the foundation's organizing workflow.

The model must support creation, receipt, consumption, communication, organization, scheduling, resource use, and maintenance. No single example validates it. [[Object Use Cases]] works through these different uses and the boundaries they require.

The design priority is stable reference and operation semantics. A small core matters, but freezing a particular six-field record before exercising these cases would confuse a compact representation with a stable OS contract. Schema evolution, export, and compatibility are required capabilities from the beginning.

## 2. What an object identifies

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

### 2.1 Entity boundaries and internal structure

Create an independent entity when a subject needs durable independent reference, lifetime, history, or operations. Scope a facet or overlay when the difference is only whose annotation, position, or preference is being represented. Different privacy requirements do not automatically require separate copies of the subject.

Not every paragraph, audio sample, spreadsheet cell, GPU texture, or application widget should become a top-level OS entity. Domain models may retain efficient internal structure and expose stable subobject anchors. Promote an internal item when independent reference is useful. Stable anchors require a domain contract; a character offset or current row number alone does not remain valid after arbitrary edits.

Events, activities, resources, grants, and representations retain distinct semantics even when some have entities for inspection. An object record for a microphone does not replace its driver or transport audio samples through facet writes. The OS exposes meaningful boundaries without forcing its kernel, media pipeline, or every application heap into one storage format.

### 2.2 Identity issuance and matching

IDs are never reused, including across rollback and import. Issuance must handle cloned snapshots and authenticated origin; a copied string or display name does not establish identity. An entity ID is a name, not a credential.

Source adapters maintain explicit bindings such as `(account, provider object ID, incarnation if applicable)`. Repeated observation of the same source item should update that binding rather than create endless duplicate entities. A source without durable identifiers needs a documented matching policy and an explicit uncertain-match state.

Identical bytes do not imply identical subjects. Two attachment occurrences may share content storage but retain separate senders and history. Conversely, two different encodings may represent the same recording. Semantic matching can suggest relationships; it must not silently merge identities, permissions, or history. If a user consolidates duplicate records, preserve the old references and distinguish consolidation from access grants.

### 2.3 Logical envelope and references

The following is a logical model; storage layout and serialization remain open:

```text
entity identity:
  id
  authenticated origin and genesis event

entity state at a branch head:
  entity_id, branch_id, revision
  lifecycle
  policy_ref
  facet instances

reference:
  entity_id
  branch interpretation: selected branch or explicitly pinned branch
  revision interpretation: live or pinned revision
  optional subobject anchor and its version context
```

A live reference answers “this document as it currently is.” A pinned reference answers “the version attached to this message.” The human-facing label can be simple, but the distinction must survive serialization and sharing. Runtime handles such as PIDs, connection IDs, and compositor surfaces also require an incarnation and cannot replace persistent identity.

Resolving a reference, reading retained state, fetching remote content, and invoking an operation are distinct requests. A persistent ID is not a transparent pointer to a live remote object. Local inspection should disclose missing or stale data without silently starting arbitrary network work. Remote fetches and invocations need explicit cancellation, deadlines, and partial-failure semantics; naming an object cannot promise its service will respond.

## 3. Facets and composition

A facet is a typed, versioned component describing an aspect of an entity. Entities have no mandatory class hierarchy. Facet contracts still have types, requirements, and validation rules.

“Photo,” “appointment,” and “playlist” can be conventional profiles of facets. A `kind-tag` is advisory: changing it does not change bytes, grant access, or turn an object into an executable resource. Operations inspect supported contracts and current state.

### 3.1 Facet families

These are coverage areas, not a requirement that every entity carry every family:

| Family | Examples |
|---|---|
| Display identity | Name, aliases, advisory labels |
| Content | Text, structured document, media descriptor, retained content revision |
| Source and availability | File binding, provider binding, local materialization, fetch state |
| Organization | Collection membership, ordered entry, saved query |
| Communication | Message body, participants, attachment references, delivery observation |
| Time | Schedule, recurrence, occurrence exception, reminder policy |
| Interaction | Reading position, selection anchor, scoped presentation preferences |
| Activity and resources | Playback intent, call session, download, device observations |
| System settings | Preference value, scope, effective-value derivation |
| Semantics | Tags, attributed annotations, summaries, suggested relationships |
| Provenance | Authenticated mutation references, derivations, source evidence |
| Actions | Discoverable operation contracts and compatible handler bindings |

Examples use short names for readability. Implementations need namespaced facet type IDs so that task status, message delivery status, and runtime observations do not collide under a generic `status` name.

### 3.2 Facet contract

Each admitted facet type specifies:

- schema identity/version, cardinality, and instance identity;
- canonical value representation and authority mode;
- readable/writable scope, supported operations, and validation;
- value revision, dependencies, and invalidation rules;
- concurrency, merge, and conflict behavior;
- compatible handlers, generic inspection, and export behavior;
- size, computation, and retention limits.

Schema version describes the data format; value revision describes an edit. They are not interchangeable. Initially, keep one authoritative current representation per facet instance at a branch head. Older representations can be retained revisions or derived translations, not independently writable competing truths.

An entity may have several instances of the same facet type—for example, captions in different languages or annotations belonging to different participants. Instances need explicit keys and scope. Whole-entity replacement is not the default write API: a tool should update only the instances it understands and is authorized to change.

### 3.3 Composition rules

1. **Preserve admitted unknown data.** Readers do not discard unfamiliar facets. Unknown data remains bounded, inert, inspectable through a generic envelope, and exportable under applicable permissions.
2. **Require understanding for operations that depend on it.** An unknown action-critical constraint blocks that operation. Preserving a signature facet does not keep the signature valid after its content changes.
3. **Track dependencies.** Derived text, thumbnails, summaries, signatures, and computed values identify their input revisions and become stale when those inputs change.
4. **Allow incomplete subjects.** An empty facet bag can be a newly created entity, not automatically a tombstone. A disconnected device or unsupported format remains an entity with limited operations.
5. **Validate combinations at the operation boundary.** Arbitrary admitted facets may be retained; not every combination is valid or executable. Coupled invariants can require an atomic transaction across facets or entities.
6. **Do not let descriptions grant power.** The trusted registry and policy service admit contracts and authority. An invented facet cannot declare itself a trusted observation or install runnable behavior.

Optional profiles can provide defaults and tested combinations without becoming hidden classes. Their value is interoperability and convenience, not enforcing a universal ontology.

## 4. Everyday objects in practice

These sketches omit wire-format details. They illustrate equally important cases rather than a sequence through which every object progresses.

### 4.1 A document being read

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

### 4.2 Music and playback

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

### 4.3 Messages and conversations

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

### 4.4 Appointments and reminders

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

### 4.5 Devices and jobs

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

### 4.6 Creation remains supported

A code project may have file bindings and optional service intent; a worker job may produce a changeset; a prototype may be derived from a note. These use the same reference, operation, and authority rules. They are one family among the preceding uses, not the reference example for every mechanism.

## 5. State has several independent dimensions

One lifecycle enum cannot describe everything that matters about an object:

| Dimension | Question | Example |
|---|---|---|
| Identity/lifecycle | Does this subject exist in the selected history? | Active, archived, tombstone, absent on this branch |
| Revision/validity | Which content or claim is this? | Current, pinned, conflicted, derived from an old revision |
| Availability | Can these bytes or this resource be reached? | Local, remote, offline, partially cached, missing |
| Activity | What is happening? | Playing, paused, connecting, idle, pending, outcome unknown |
| Attention | How is it presented to this participant? | Visible, selected, muted, hidden, recent |
| Authority | What may this participant read or cause? | Readable, editable, restricted, expired grant |

These are semantic dimensions, not prescribed universal fields. A domain supplies meaningful states and operations. An archived recording may still be playable; an active document may be offline; a hidden process may still consume resources. Low attention is never by itself evidence that an object can be deleted.

## 6. Actions, intent, and observations

JEFF and the human use the same semantic action definitions. Neither gets authority merely from a descriptor. Installed handlers, compatible data, current policy, target revisions, and resource budgets determine whether a call can run. [[Security Model]] describes the proposed enforcement boundaries.

The command model must cover different operations:

| Operation family | Example | Required semantics |
|---|---|---|
| Content edit | Change a caption | Revision-aware validation and undo/merge policy |
| Organization | Move a playlist entry | Stable entry identity, order and membership rules |
| View interaction | Open another reader | View/session scope without copying content |
| Maintained intent | Keep a download progressing | Bounded reconciliation toward a named result |
| One-time effect | Send or print | Frozen target/payload, operation identity, outcome handling |
| Resource use | Start a call, route audio | Current grants, session identity, explicit resume/fallback policy |
| Setting change | Choose a default output | Explicit preference scope and effective-value derivation |

### 6.1 Spec/status has a specific role

Use a desired-state facet and reconciler-owned observations when a domain supports maintained intent. Do not apply process-management semantics to every subject or assume every recorded request should be repeated until it appears successful.

An observation includes the desired-state revision it concerns, its observer, resource/runtime incarnation, time, and freshness policy. An observer can be wrong or out of date. A type declaring itself `status` cannot make its author authoritative.

Reconciliation requires allowed effects, ownership, resource limits, and stop conditions. It may fail or remain blocked. Local restore can recreate a reader window while leaving playback paused and a call disconnected. Print, send, and reminder delivery need durable operation outcomes and safe retry policies separate from restoring UI state.

### 6.2 Verbs must have distinct targets

“Close,” “stop,” “disconnect,” “remove from this collection,” “remove local bytes,” “cancel future occurrences,” and “erase this object” are not interchangeable versions of delete. The UI and agent must preserve these distinctions in their action contracts.

Ordinary actions should remain fast. A previously granted local read or volume adjustment does not need a new conversational confirmation on every use. Higher-consequence effects need the appropriate explicit grant or approval bound to the actual target and payload. Domain semantics determine the boundary; a generic object menu does not decide it.

## 7. Content authority and relationships

### 7.1 One authority per value

Each binding declares how its value is maintained:

- **Native content:** accepted object operations and retained content revisions are authoritative; ordinary files expose usable materializations/export.
- **External file:** the file is authoritative until captured; the adapter records observations and versions and checks for competing writes.
- **Remote resource:** the provider is authoritative for remote facts; local proposed changes and last observed state remain distinct.
- **Derived value:** a reproducible or inspectable transformation names its inputs and revision dependencies.
- **Attributed claim:** a person, JEFF, or another source asserted something; acceptance into storage does not establish its truth.

Do not keep two independently writable primary copies of the same logical text in a facet and a backing file. A directory watch is not a perfect history: adapters need reconciliation, missed-event handling, and explicit rename/replace policies. Historical bytes require retained payloads or a verifiable snapshot, not just a path.

### 7.2 Relationships and occurrences

Cross-subject relationships have identity, endpoints or anchored references, a namespaced predicate, authenticated asserter, event provenance, and retraction semantics. Inferred relationships remain claims. Essential structure is not an LLM guess.

Typed relations such as collection membership or attachment containment declare their operational semantics. Loose predicates such as “reminds me of” remain useful without governing deletion or access. A `related-to` edge must not implicitly mean ownership, lifecycle dependency, or permission to traverse private content.

There must be one authoritative encoding for a relationship. A relationship table and a convenient facet projection must not both be independently writable sources for the same membership. Domain-internal references, such as anchors within a document, can remain in its structured content; not every internal pointer becomes a global semantic edge.

Ordered collections need entry identities distinct from target identities. Saved-query collections need a stored query definition and membership-as-of semantics when an action requires a stable set. “Share these results” must freeze the chosen members or explicitly grant a dynamic view; later query matches must not silently become new recipients or disclosures.

## 8. Soft semantics, projections, and attention

Free annotations, tags, informal descriptions, and suggested links should be easy to add. They still obey provenance, access, resource, and retention limits. Loose meaning can help retrieval without becoming an execution contract. A fuzzy description can nominate an appointment; changing its time requires a precise target and valid schedule operation.

Every facet must remain inspectable in visual and token form, including through a generic safe fallback when a specialized tool is missing. This is a platform obligation; imported data must not execute its own projector by default.

```text
project(reference, viewer, purpose, budget)
  -> observed facts and their freshness
     attributed claims and source references
     permitted actions or action-discovery references
     omissions, conflicts, and stale dependencies
```

For example, a short projection of `document_17` can say “Travel itinerary, revision 3, cached; your reading position: page 4.” More detail can include permitted annotations and available source revisions. A short projection of a call must preserve whether the microphone is currently active; a projection of a print job must not shorten “outcome unknown” into “done.” Budget examples are not exact tokenizer counts.

Filter by viewer and destination before summarization. Private reading position, unread state, room history, and annotations must not leak through otherwise public object descriptions. Derived summaries retain their source restrictions and revision dependencies. Provenance indicates origin, not correctness or permission.

Presence is scoped to participant, view, session, and time. Resolve “this” against the relevant interaction context, not simply the pointer's position after speech recognition finishes. Resolve “the next one” against a particular collection ordering; its meaning is not inherent in the target object. High-rate presence can be transient, with deliberate durable checkpoints rather than an eternal record of every gaze or pointer movement.

## 9. Lifecycle, retention, and long-lived references

`active`, `dormant`, `archived`, and `tombstone` express management of a subject, not an inevitable progression driven by age. Archived objects can be deliberately reopened. An object with no recent attention can remain pinned or required by another retained record.

Closing a view is not lifecycle change. Removing a source binding is not erasure of all other copies. Dropping a cache is allowed only when doing so does not silently destroy the last copy the system promised to retain. Dependency records, retention promises, user choices, and resource policies govern cleanup.

Deletion must account for retained revisions, attachments, derived content, memory, and backups. A tombstone preserves only permitted minimal resolution information; retaining all old payloads would not satisfy an erasure request. The interaction between the Constitution's record, erasure, and fork rights remains an explicit design obligation. Do not promise recall of plaintext already held by independent recipients.

Old references should resolve honestly: current subject, pinned historical revision, absent on selected branch, unavailable content, erased content, or inaccessible/unknown according to policy. Do not substitute a similar subject because the original can no longer be reached. Privacy may require indistinguishable errors for inaccessible and unknown identities.

## 10. History, recovery, and storage

The canonical event record describes accepted object mutations and observed outcomes. Materialized entity state and indexes are rebuildable within the declared recovery and retention horizon, using retained events, referenced payloads, and checkpoints. External reality is not a cache of Agora's event log.

Ordinary file interoperability remains essential. Keep media and other payloads in accessible filesystem storage, with documented export of facets and relationships. Native content may use retained revisions; remote bindings must reveal when bytes have not been captured. An export manifest distinguishes fully included content from references that still require another service.

Logical storage responsibilities:

```text
protected authority and recovery evidence
  -> grants, revocation generations, branch/genesis evidence, effect outcomes

retained object history + filesystem payloads/checkpoints
  -> materialized entity and relation state
  -> rebuildable text, graph, and other indexes

runtime adapters and controllers
  -> expiring observations and transient activity streams
```

These are not necessarily separate databases. Protection and restore domains must be real, however: excluding a directory from snapshots does not protect it from root in that VM. Follow the enforcement design in [[Security Model]] rather than trusting a facet declaration.

Restore selects a state in a branch and records that transition. Required genesis evidence must survive so references into the abandoned future resolve historically. Old grants and callbacks do not regain validity; runtime observations are revalidated. A previously sent message, heard reminder, or printed page is not undone by restoring local state.

Replaying retained events is pure reconstruction. Execution happens through separately authorized operations, with operation identities and external receipts where available. If a remote effect may have happened but cannot be verified, retain uncertainty and apply the domain's retry policy. Never infer that absence of a local receipt means absence of the effect.

Durability and human-readable history have different granularity. Persist accepted edits/checkpoints according to the durability promise; present a coalesced reading session or editing activity without losing the underlying recovery information. Continuous media and input streams stay outside ordinary facet mutation paths except for explicitly recorded content or checkpoints.

## 11. Concurrency and compatibility

Merge policy belongs to a domain contract. Text operations, playlist order, appointment exceptions, device selection, and access grants do not have interchangeable conflict semantics. Some can merge automatically; some need a conditional write or explicit conflict; some require a single ordering authority.

Operations specify both reads and writes. Validating only the modified facet misses invariants that depend on other facets or entities. Check the relevant read revisions and commit coupled changes atomically, or record a proposed change awaiting reconciliation. Domain-specific undo must not erase unrelated changes made by another participant.

Preserve unknown data, but do not assert that independently upgraded tools are semantically compatible merely because each can parse the envelope. Declare supported schema versions and migrations. Read-only inspection is preferable to a lossy edit disguised as full support. Removing a tool leaves data and provenance intact and makes unavailable operations explicit.

Compatibility includes effects. Changing an operation from “share this frozen revision” to “share this live subject” changes its contract even if the argument shape stays the same. Such a change needs a new contract version and fresh compatibility/authorization evaluation; old approval must not silently acquire a broader meaning. See [[Security Model]] for update adoption and exact-configuration requirements.

An extension's critical requirements and dependencies must be represented in a gate the installed operation service understands. For example, preserving an unfamiliar signature payload while editing its signed content is insufficient: the dependency must invalidate the signature or prevent the edit according to the admitted contract. If the platform cannot enforce a required extension rule, it must not activate that behavior. An unrelated private reading-position update can remain available.

Code rollback and data rollback are different operations. Updating a reader must not require replacing the user's current document history with a preview snapshot. Restoring an older reader after newer data has been written requires a compatible reader, a declared translation, or an explicit read-only/unavailable state. A failed migration must not leave half the authoritative facets in each format.

Views and adapters need bounded observation protocols: a snapshot at a known revision, ordered changes or an explicit gap indication, and resynchronization after loss. Duplicate deliveries must not become duplicate domain effects. A presence stream can discard obsolete cursor positions; a content subscription must reveal that accepted edits were missed. No client should have to enumerate the entire world to update one view.

Object storage, indexing, projections, and background handlers need quotas and backpressure. The OS scheduler, device services, and storage layer still supply resource isolation and durability; describing them as objects does not implement them. A failed index or unavailable model must not prevent a known local recording from being paused through its direct control path. Basic inspection and recovery need defined degraded operation rather than a dependency on every facet provider being healthy.

The OS should remain useful without JEFF. Deterministic identity resolution, basic search, direct controls, inspection, and export do not require an LLM to interpret loose metadata. JEFF can help with discovery, explanation, and proposing adaptations across contracts; authorization and validity stay machine-checkable.

## 12. Principles to stabilize and questions to leave open

Stabilize these principles through conformance examples:

1. A subject's identity is independent of names, locations, views, process handles, and whether it is being used.
2. A reference distinguishes live state, pinned revision, occurrence, and subobject context where those differ.
3. No object needs a project, derivation chain, worker, or executable facet.
4. Facets compose through explicit contracts; kind labels are advisory.
5. Unknown admitted data is preserved; unsupported action-critical semantics block the affected operation.
6. Shared facts, private overlays, transient observations, and effective settings retain their scopes.
7. A value or relationship has one declared authority; derived copies identify dependencies.
8. Identity, availability, attention, activity, retention, and authority cannot be collapsed into one lifecycle.
9. UI and agent actions share semantic implementations and current authorization checks.
10. Replay restores records; it does not repeat external effects or restore revoked power.
11. Data remains inspectable and exportable when its original tool or JEFF is unavailable.
12. Ordinary use in unrelated domains is the acceptance test for any supposedly general abstraction.

Leave exact ID encoding, facet IDL, on-disk layout, CRDT choices, subobject-anchor formats, and most domain vocabularies open until their contracts have been exercised. The shared protocol needs a small stable base and explicit extension rules, not a universal schema for all human activity.

Historical comparisons can inform questions, but do not establish that a particular predecessor failed for one reason or that an LLM solves every interoperability problem. This revision derives its requirements from everyday cases without making new historical claims.
