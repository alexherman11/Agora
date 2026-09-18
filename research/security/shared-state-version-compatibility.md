# Shared state across application versions

*Security design investigation · 15 September 2026 · Current source commit
`39ae665554629502c87be8b4b0788b6bedb0e217` on branch `docs`. Proposal and
static source review only. No Agora code, test, hook, build, package, model,
account, credential, private world, or external service was executed or read.*

## Question and answer

When collaborators use different application versions against shared data,
which writes may commit, which must remain proposals, and how can code rollback
preserve work created by newer versions?

The safest practical rule is: **compatibility belongs to the operation, not to
the application version or merely to the serialized shape.** A write may commit
when the trusted gate can determine one bounded meaning for it under the current
data contract, the writer observed everything that operation can replace, its
read dependencies still hold, and current authority and critical invariants
allow the resulting effect. Otherwise it remains an attributed proposal or the
client becomes read-only for that operation.

This permits useful mixed-version collaboration without pretending every schema
change is reversible. Most ordinary field-local edits can continue silently.
An old client must not erase or reinterpret facts it cannot represent.

## Why parse compatibility is insufficient

Agora's specification already separates a facet's schema version from its edit
revision, requires unknown facets to survive, and says lossy writers should be
read-only. Those are sound principles. The current prototype does not yet
implement their distributed form:

- `FacetRecord` carries a body and revision but no facet `schema_version`;
- `facet-attached` records a complete replacement body with no writer schema or
  operation-contract identity;
- `attach` permits the revision precondition to be omitted;
- component `attach` effects also replace complete `core.name` or `core.text`
  bodies, although the current fixed schemas and input fingerprint constrain the
  local prototype;
- component-owned state stores a schema object and is checked for an exact shape.
  An incompatible restored definition fails closed, but no migration or
  multi-version state protocol exists.

This means the current code is appropriately a local prototype, not evidence
that shared writers are compatible. Adding optional fields to an event format
ensures old logs can be parsed by new code; it does not ensure old application
code can safely edit newer data. A read-modify-write client can parse a new
record, omit fields it does not know, and replace the record with a valid older
shape. Revision compare-and-set prevents a race but not this informed downgrade:
the old client may have read the latest revision and still erase newer facts.

Protocol Buffers provides a useful narrow lesson: binary messages preserve
unknown fields during message-oriented copying, while field-by-field copying or
conversion to JSON can discard them. It also permanently reserves field numbers
because reusing an old identity can cause ambiguity, disclosure, or corruption.
Agora should preserve unknown data and never reuse schema or operation
identifiers, but it needs stronger semantic rules than a wire format can provide.

## Store intent in stable operations

For a facet that will be edited by several application versions, define a small
semantic operation vocabulary independently from its render schema. Operation
identities are immutable. If an operation's meaning changes, mint a new identity.

For example, a task facet might keep `task.set-title` across many UI versions.
Changing one assignee into a set of assignees is different: an old
`task.set-assignee` cannot silently mean either “replace the whole set” or “edit
the first member.” Both interpretations can destroy or surprise. New operations
such as `task.add-assignee` and `task.remove-assignee` make the affected facts
explicit. The older operation needs a permanent, narrow mapping or becomes a
proposal once the shared state contains information it cannot represent.

Each attempted shared write should reach the verb boundary with an envelope like:

```text
subject: facet instance or stable subobject
writer_schema: immutable schema identity
operation_contract: immutable semantic operation identity
arguments: canonical operation data
read_set: exact revisions, causal heads, or stable subobject versions observed
write_set: fields/subobjects the operation may change
actor and local installation/adoption identity
```

The envelope is trusted metadata assembled by the local gate, not a package's
self-description. The application supplies a requested operation. The gate
resolves its actual read/write set, translation path, authority, and invariants.
The accepted event retains the original operation and writer schema so later
readers do not have to guess what the author saw.

Whole-body `attach` remains useful for creating a facet or for an exact-version
local register. It should not be the default update operation for a shared,
independently evolving facet. Require an exact schema and current revision for
that exceptional case, and refuse replacement when the current body contains
unknown fields or critical constraints.

## Commit, propose, or refuse

The gate can make a local, mechanical decision for each operation:

| Outcome | Conditions | User experience |
| --- | --- | --- |
| Commit | The operation contract is supported; translation is total and uniquely selected; the write set is within what the writer could observe; read dependencies hold; invariants and authority pass; the facet's merge class defines concurrency. | Apply normally. Different app versions need no prompt merely because their presentations differ. |
| Proposal | The author's intent remains useful, but mapping it has several plausible meanings, would touch hidden/new facts, requires a migration or conflict choice, or depends on a stale read. | Preserve the attributed request and affected identities. A compatible client offers concrete resolutions without executing one silently. |
| Read-only for this operation | A safe projection exists but no safe write translation exists. | Keep viewing and unaffected operations available; explain exactly which operation needs a newer contract or adapter. |
| Refuse/quarantine | Schema, adapter, critical constraint, actor, or authority is unknown; the operation identity was reused; validation is non-deterministic; or the effect would broaden disclosure or external action. | No state change. Offer inspection or a candidate conversion, never fallback guessing. |

An application is therefore not globally “compatible” or “incompatible.” Its
capability list is computed per operation against the selected data. An older
task app may still edit titles and comments while its assignee control becomes
read-only. This is safer and less disruptive than forcing every collaborator
into lockstep.

Authority is checked after the operation is translated into a concrete effect
plan and before commit. A translation that changes `edit this field` into
`replace this record`, changes a frozen share into a live share, or introduces an
external destination is a new operation contract and requires the applicable
local decision. Schema compatibility never carries grants with it.

## Read translations are useful but not authority

[Project Cambria](https://www.inkandswitch.com/cambria/) demonstrates a strong
idea for local-first collaboration: tag raw writes with their writer schema and
translate them when read, so schemas added later can still interpret earlier
writes. It also documents the hard limit. When one version sees a scalar and
another sees an array, deleting the visible scalar can mean deleting all values,
only the first, or something else; consistency, conservation, and predictable
intent cannot all be guaranteed.

Agora should borrow schema-tagged raw writes and read-time translation, with two
security qualifications:

1. A lens carried inside a document is untrusted executable or declarative
   content. It cannot authorize itself, inspect undisclosed fields, or run with
   credentials. Adapters used for rendering can be locally adopted, pinned,
   deterministic, resource-bounded definitions. Adapters used to validate a
   write or compute authority need the stronger trusted execution contract from
   [[local-adoption-and-executable-identity]].
2. Adding a new adapter path must not silently reinterpret an accepted effect.
   Schema and adapter identities are immutable; the gate pins the exact adapter
   path used to accept a write. Multiple non-equivalent paths between the same
   schemas are an explicit conflict, not a “shortest path” implementation detail.

Translations preserve confidentiality and provenance restrictions from their
inputs. A projection may omit a private field from an older app; omission does
not give that app permission to overwrite it. Imported adapters, test results,
signatures, and popularity are evidence, never grants.

## Migration is a separate candidate operation

Prefer read-time adapters while multiple versions need the same shared data.
Use a durable migration only when storage or a new invariant actually requires
one. A migration is neither application startup nor replay behavior. It is a
separate, reviewable candidate with:

- immutable source and target schema identities;
- exact input causal head or facet revision;
- exact transform and runtime-contract digests;
- declared read/write set and critical invariants;
- a bounded output candidate and privacy label;
- an idempotency identity and current-authority check;
- a retained pre-migration branch and an explicit result event.

Migration code gets no external destinations, credentials, or implicit access to
the rest of the world. A failed migration appends no partial authoritative state.
Replay applies the recorded result and never reruns the transform. A merge of two
migration branches is a new candidate; it does not union chosen adapters or
authority.

## Roll back code without rolling back work

Code selection, data history, local authority, and external-effect receipts keep
their separate rollback rules:

1. **Code rollback** selects an older application definition. The raw data log
   and current causal head stay in place. The old code gets a safe translated
   view, a partial capability list, or read-only inspection. It never receives a
   fabricated older body and then writes that body over newer facts.
2. **Data rollback** is a new forward event, selective inverse, or explicit fork
   from a named head. In a shared object it cannot erase another participant's
   unrelated later operations. The abandoned future remains addressable unless
   erasure policy requires otherwise.
3. **Schema rollback** is normally a view through a pinned adapter. A destructive
   down-migration is its own migration candidate; selecting old code does not
   trigger it.
4. **Authority rollback never occurs.** Current revocations, local adoption, and
   anti-rollback state remain in the keep. An old app cannot revive an old grant.
5. **Effects never replay.** A code or data rollback cannot resend a message,
   repeat a purchase, or reinterpret an old receipt as pending work.

This preserves the user's newer work even when they retreat to a stable older
interface. The cost is honest partial functionality when meanings have diverged.
That is preferable to hidden data loss presented as successful compatibility.

## Smallest next implementation slice

Do not retrofit the M1 component experiment into a distributed schema engine.
Before the first mutually untrusted shared writer, implement one deliberately
small vertical slice on a synthetic facet:

1. Give the facet definition, its schemas, and two or three operations immutable
   identities. Never reuse retired field or operation identities.
2. Add optional writer-schema and operation-contract metadata to the append-only
   event format, preserving replay of existing events with an explicit legacy
   default.
3. Make the shared-write verb require a read set and derive a narrow write set.
   Keep generic whole-body replacement out of this path.
4. Implement one bounded, declarative read adapter and one intentionally
   ambiguous evolution. The former commits; the latter produces an attributed
   proposal.
5. Pin adapter identity and path in accepted validation evidence. Treat an
   unknown critical constraint or alternate non-equivalent path as blocking.
6. Demonstrate code rollback using the same data head: safe old operations remain
   available and the ambiguous operation is read-only, with no data rewrite.

Only after that slice works should component-owned state migration join it.
`core.component-state` is single-component-owned today, so exact-shape refusal is
a safer temporary behavior than an implicit migration.

## Proposed acceptance cases

No case below was run in this investigation.

| Case | Expected outcome |
| --- | --- |
| SV-1 — additive hidden field | A new client adds a field and an old client edits a different stable field. The new field survives byte-for-byte and is not disclosed to the old client. |
| SV-2 — stale whole replacement | An old client reads the current revision and submits its complete older-shaped body. The shared-write path refuses it; revision freshness alone does not authorize erasure. |
| SV-3 — stable operation | Two versions issue the same immutable field-local operation. Both commits converge under the facet's declared merge class. |
| SV-4 — scalar to set | Old code deletes the one assignee it can display while newer data contains several. No value is silently removed; the request becomes a proposal or the operation is read-only. |
| SV-5 — operation reuse | A branch reuses an old operation ID with a wider meaning. Import quarantines the definition and no old approval applies. |
| SV-6 — adapter ambiguity | Two branches add non-equivalent paths between the same schema identities. Merge exposes an adapter conflict; path choice cannot depend on load order or shortest-path tie breaking. |
| SV-7 — critical invariant | An old writer cannot understand a new critical constraint. Unrelated safe operations may continue; dependent writes are refused. |
| SV-8 — migration failure | A deterministic migration fails midway. No authoritative facet is partially converted, and retry with the same idempotency identity cannot duplicate work. |
| SV-9 — code rollback | After new-version writes, select older code. The newer facts remain in the log; safe views and operations work, ambiguous writes are unavailable, and no down-migration runs. |
| SV-10 — shared undo | One participant undoes their edit after concurrent unrelated edits. The inverse targets only the authored operation and does not reset the whole facet. |
| SV-11 — authority after translation | A narrow old operation translates to a broader effect. The gate refuses or asks for the new authority decision; the old grant is not reused. |
| SV-12 — replay | Rebuild applies recorded events without executing adapters, migrations, component source, or external effects and reproduces the accepted authoritative state. |

## Evidence and limits

This proposal refines controls already specified in [[Objects and Facets]] §9,
§10.3, and §11.3: operations declare reads and writes; replay is reconstruction;
unknown facets are preserved; incompatible writers become read-only; code and
data rollback are separate. [[Executable Components]] specifies exact-shape
component state and no implicit migration for the implemented local prototype.

The current source was inspected statically at the commit above. Committed tests
describe component replay, stale-input refusal, state shape, and restoration,
but were not run here and do not cover shared replication or mixed-schema
writers. Agora currently has no shared writer protocol, proposal object, general
schema-tagged operation format, adopted adapter graph, or migration executor.
The Cambria and Protocol Buffers sources are design precedents, not evidence that
this proposal works in Agora.

The next useful question is narrower than choosing a replication protocol:
**what immutable operation envelope and adapter language can express Agora's
first mixed-version facet while remaining small enough for the verb boundary and
replay model to verify?**

## 18 September follow-up: automation narrows the envelope

The [[automation-rules-and-external-effects-review]] applies this question to
the text-desk fixture's new rules, scripts, and external trial launcher. It
proposes a small typed firing envelope with a stable operation identity, local
adoption, authenticated cause, exact resolved targets, typed arguments, read
dependencies, an effect plan, budgets, and an idempotency identity. Bounded
adapters remain read projections; they do not translate or dispatch external
effects. Ambiguous operations remain proposals or read-only.

This is a refinement of the proposal, not an implemented format. The static
fixture review also found that launch dispatch precedes event recording and that
grouped undo is not preflighted around non-undoable effects. No runtime case was
executed.
