# Local adoption and executable identity

*Security design investigation · 11 September 2026 · Current source commit
`39ae665554629502c87be8b4b0788b6bedb0e217` on branch `docs`. This is a
proposal grounded in the existing executable-component prototype and targeted
primary-source research. No Agora code, test, hook, model, account, credential,
or world data was executed or read.*

## The question

What is the smallest local-adoption record and runtime compatibility identity
that allows routine collaborative updates without letting a fork, merge, restore,
or foreign world carry executable authority?

The smallest useful answer is not one hash or one record. It is a separation
between:

1. a **portable application definition** that collaborators may branch and merge;
2. a **local installation plan** that resolves abstract slots to this person's
   objects and computes exact authority;
3. a **local adoption policy** outside portable and rollbackable world history;
4. an **exact execution snapshot** produced and checked at launch.

Only the first item travels automatically. Evidence may travel beside it, but is
still a claim. The other three are reconstructed or authorized locally.

## Why the current component digest cannot be the long-term identity

The prototype deliberately combines source, concrete entity bindings,
permissions, schemas, state, and action descriptions in one `core.component`
body. Its digest is useful for pinning a local experiment. It is awkward and
unsafe as a shared application identity:

- concrete entity IDs reveal installation-specific structure and make the same
  program hash differently for every person's data;
- changing a binding and changing executable source are indistinguishable at the
  digest level;
- a definition digest does not identify the QuickJS build, validator semantics,
  renderer contract, or dependencies that determine actual behavior;
- the current admission facet says that this digest ran accepted tests, but does
  not say who adopted it, for which local world, under which authority ceiling,
  or whether a later revocation still applies.

This is acceptable for the implemented local/trusted-authoring slice. Before
portable applications, definitions should request **logical slots** such as
“selected documents as `core.text`” or “one scene whose listed members may be
placed.” Installation binds those slots to local facets and destinations. A
shared code revision then remains stable while private object IDs and grants stay
local.

## Four identities with different jobs

### 1. Definition identity — what collaborators edited

`definition_id` is a digest of canonical, portable material:

- source and generated code;
- declared slot schemas and action contracts;
- state schema and declared migration interfaces;
- dependency names resolved to immutable digests;
- the application-definition format version.

It contains no concrete local object IDs, secrets, grants, active-display state,
test fixtures, or cached outputs. A merge creates a new definition identity even
if each parent was previously accepted.

### 2. Execution-contract identity — what the platform promises the code means

`contract_id` names the host semantics the definition expects: component ABI,
tree validator, event semantics, effect vocabulary, limits, and canonicalization.
It is a versioned contract, not the package manager's current engine version. An
incompatible semantic change gets a new contract ID.

The exact runtime build still matters, but binding every person's application
approval directly to one QuickJS patch would create prompt fatigue and discourage
security updates. Runtime trust should be a platform decision. Each launch records
the precise engine and validator build; a platform update may continue without
per-application prompts when it implements the same contract and passes the local
conformance gate. A changed contract, weaker isolation claim, or failed
conformance pauses affected applications on the protected default view.

### 3. Installation-plan identity — what this instance can reach

The trusted installer resolves slots to local resources and computes a canonical
effective plan:

```text
plan_id = H(
  definition_id,
  contract_id,
  resolved dependency digests,
  slot -> local object/facet/revision rules,
  allowed writes and external destinations,
  resource ceilings,
  state/migration contract
)
```

The plan is an over-approximation of possible authority. A package manifest is
only input to this computation. A composed candidate receives a newly computed
plan; parent-branch grants and admissions are never unioned.

### 4. Local adoption identity — why this machine may run it

The keep needs one compact, non-transferable policy record:

```text
local_adoption = {
  local_adoption_id,
  local_authority_domain,
  scope: exact installation | keep-created same-owner descendants,
  subject: application lineage or exact definition,
  trusted update sources and required approval/review threshold,
  allowed contract IDs,
  maximum effective plan,
  state-migration policy,
  anti-rollback state: release sequence or accepted causal frontier,
  revocation generation,
  evidence requirements,
  expiry or explicit no-expiry,
}
```

This record expresses standing user policy. It may allow a narrow local JEFF
workflow, a named collaborator set, or a signed release channel. An unchanged
permission plan is necessary for quiet updates but not sufficient: malicious code
can abuse existing rights. Automatic adoption also needs a trusted authorship or
review rule chosen by the person.

## Launch is a local join, not a property of the world

At execution time, the trusted gate joins four things:

```text
portable definition
  + locally resolved installation plan
  + current local adoption policy
  + exact trusted runtime build
  -> allow this execution snapshot, or fall back safely
```

The world may store a reversible `core.display` preference saying which
application it wants. That is a claim. It is never sufficient to run source. A
foreign or restored world carrying old test, admission, and display facets cannot
manufacture a matching record in the local keep.

Same-owner forks need not cause prompts. The keep can create an unforgeable local
lineage relationship when the person forks a world and apply a policy whose scope
explicitly includes those descendants. Exporting that fork does not export the
relationship: the recipient maps it into a new local authority domain. A foreign
bundle cannot claim to be a same-owner descendant merely by copying an ID.

This also clarifies rollback. World state may move backward; the keep's accepted
update frontier and revocation generation only move forward. A signed release
channel can use a monotonic sequence. Peer branches need a causal frontier or set
of accepted heads; forcing them into one counter would create a hidden central
writer and reject legitimate offline work. Restoring an old display preference
can request an older application, but the gate refuses it when current local
anti-rollback policy does not admit it. Rollback for creative comparison can
still happen in an isolated candidate without changing the installed version.

## Quiet updates without quiet authority growth

An update may activate automatically only when all of these are true:

- its authorship/review provenance satisfies the person's standing update rule;
- the complete definition and dependencies resolve to immutable digests;
- it uses an allowed execution contract;
- its newly computed plan is within the existing maximum plan;
- it does not introduce a new external destination or reinterpret an existing
  action contract;
- any state migration satisfies the local migration policy and preserves a
  recoverable pre-migration branch;
- it is fresh against the channel's sequence or accepted DAG frontier and is not
  revoked;
- required local conformance and synthetic-fixture checks pass.

If the effective plan shrinks, the update can remain quiet under that policy. If
it expands, the surface shows only the trusted plan diff: new readable sources,
writable targets, destinations, costs, persistence, migrations, or background
behavior. The package can explain the request but cannot draw the authoritative
permission account.

A merge with unchanged authority may still contain harmful behavior within that
authority. That residual risk belongs to update-source trust and review policy,
not another permission prompt. People can choose different policies for a local
JEFF-authored personal view, a household project, and a public package.

## Evidence and update metadata

Portable test or build evidence should identify exact materials, products,
builder, process contract, and dependency digests. It should not contain private
fixtures, stdout/stderr, rendered output, or live-world values by default. Local
verification decides whether the evidence satisfies the adoption policy.

This matches useful separations in existing systems without importing their
protocols wholesale:

- [SLSA build provenance](https://slsa.dev/spec/v1.2/build-provenance) separates
  a process definition and resolved dependencies from run details and an
  identified builder. It treats externally controlled parameters as inputs the
  consumer must verify. That is evidence about production, not user authority.
- [in-toto](https://github.com/in-toto/specification/blob/master/in-toto-spec.md)
  separates signed step evidence from the client's layout and inspection policy.
  The same evidence can participate in different layouts. It also notes that
  supply-chain evidence alone does not prevent replay of older valid layouts.
- [The Update Framework](https://theupdateframework.github.io/specification/v1.0.28/)
  explicitly addresses rollback, freeze, mix-and-match, wrong-target, excessive
  data, and delegated trust. Agora needs the same attack vocabulary for update
  metadata, while keeping creative world rollback distinct from authority
  rollback. Its ordered repository metadata is a useful release-channel model,
  not a reason to impose one total order on peer-authored branches.
- [Ink & Switch's Universal Version Control](https://www.inkandswitch.com/universal-version-control/)
  emphasizes history and comparison across media and creative privacy. Agora's
  security addition is that trying or reorganizing a creative version cannot
  retroactively undo execution or disclosure.

Do not copy TUF-style expiry into application execution without considering
offline use. A disconnected person should normally keep using the last locally
adopted snapshot. Stale update metadata should stop *new automatic adoption*, not
disable already adopted local work. Immediate revocation on an offline device is
impossible; the deployment must state that limit.

## Smallest change before portable components

No M1 kernel expansion is needed now. Preserve the current local prototype and
make the future import/export boundary do three things:

1. Export `core.component` only as a candidate definition. Exclude
   `core.component-admission`, `core.component-test`, `core.display`, concrete
   local bindings, state, and preview artifacts from the portable application
   bundle. Where the current combined body cannot be separated, export it as
   inspectable source with all bindings unresolved and inactive.
2. Treat all incoming executable definitions as foreign candidates. Rendering
   source, handling events, advertising actions, or migrating state requires a
   matching local adoption and execution snapshot.
3. Keep the protected default desk available whenever resolution or checking
   fails. Inspection must not itself execute the candidate.

The existing additive event schema can remain readable. Old admission and test
facets become legacy local evidence; a future exporter omits or sanitizes them.
There is no need to mutate old log records or pretend they were portable grants.

## Proposed acceptance cases

No case below was run in this investigation.

| Case | Expected outcome |
| --- | --- |
| LA-1 — two installations | Two people adopt the same definition against different private objects. The definition ID matches; plan IDs differ; neither learns the other's object IDs or grants. |
| LA-2 — foreign active world | A bundle contains source, a passing receipt, admission, state, and active display. Import exposes inert source and sanitized evidence; no source renders, handles input, or advertises an action. |
| LA-3 — same-owner fork | A keep-created local fork may use an adoption policy scoped to same-owner descendants without a prompt. Exporting that fork to another authority domain does not carry the relationship. |
| LA-4 — merge | Two accepted parents merge. The trusted gate computes one new plan. Parent permissions, admissions, and update sequences are not unioned. |
| LA-5 — same-plan hostile edit | An unauthorized contributor changes behavior without changing permissions. The update remains a candidate because plan equality does not satisfy the update-source rule. |
| LA-6 — routine trusted update | A trusted update with the same contract and a subset plan passes required checks and activates without a new prompt. The exact execution snapshot is recorded. |
| LA-7 — runtime patch | A new engine build implements the same contract and passes conformance. Installed apps continue without individual prompts; old execution evidence is not misreported as evidence for the new build. |
| LA-8 — runtime semantic change | The validator or effect semantics change incompatibly. Affected apps pause on the default desk until a new contract is locally accepted. |
| LA-9 — world rollback | Restore data to before a revocation or to an older active definition. The keep's revocation generation and accepted release/DAG frontier remain current; revoked source stays inert. |
| LA-10 — offline freshness | With no network, the last locally adopted snapshot remains usable. Stale metadata cannot authorize a new automatic update. |
| LA-11 — state compatibility | New code cannot silently reinterpret incompatible state. Migration is a separate checked candidate; code rollback never reverses data or authority by implication. |
| LA-12 — permission diff | A change adds one read slot or destination. The trusted surface shows that exact expansion and requires the applicable local decision; package prose cannot hide it. |

## Result and next question

The practical security unit for collaborative applications is an exact execution
snapshot authorized by a local standing policy, not a branch name, package
signature, passing test, or definition hash by itself. Separating portable slots
from local bindings makes both safety and collaboration easier: many people can
share one program revision while each keeps their objects and authority private.

The next useful question is how state schema and migration history should join
this model: **when collaborators run different application versions against
shared data, which writes remain compatible, which become proposals, and how can
rollback preserve user work without reinterpreting it under an older schema?**

## Follow-up — 15 September 2026

[[shared-state-version-compatibility]] answers this with a per-operation gate.
Application-version or wire-format compatibility is insufficient: a write
commits only when its stable operation contract has one bounded meaning, its read
and write sets are explicit, and it cannot replace facts the writer did not
observe. Ambiguous schema translations remain attributed proposals or make that
operation read-only. Code rollback selects an older reader against the current
data head; it never implies a down-migration, data rewind, authority rollback, or
repeated external effect.
