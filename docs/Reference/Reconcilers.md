# Reconcilers

**Agora reference documentation — how the world keeps its promises.**
Version 0.2 (design specification). Companion to [[Objects and Facets]] (§3.2, §5.2), [[Security]] (§2–4), [[Extensions]] (§6.1), and the [[Constitution]] (III.6).

> **Status.** Specification, not implementation. Bracketed values are open decisions.
The catalog is a feature horizon. These contracts describe managed controllers;
broad guest-root execution is a separate capability, with the limits in
[[Security]] §3. No controller isolation is established by a manifest alone.

---

## 0. Summary

A **reconciler** is the sole writer of one family of status facets. It watches `spec` facets that express desired state, observes reality, and drives reality toward the spec within a **contract** that names exactly what it may touch, how hard it may try, and when it must stop. Its output is never truth; it is an **observation** — a claim from that reconciler, stamped with the spec revision it concerns, its own incarnation, a time, and a freshness horizon. Reconcilers are **level-triggered**: they compare state to spec whenever anything changes and on a slow tick, so they never depend on having seen every event. They perform only **convergent, idempotent** effects through brokers under their own grants; anything that must happen once without duplication is not theirs. **Blocked** is a first-class state, not an error. After restore or fork a reconciler does nothing until its grants are re-issued. Resource ownership prevents a new claimant from displacing a valid incumbent; unresolved competing intent produces a conflict object, not a fight. This is the machinery behind "the world reassembles itself," "the dial survives the reboot," and "the menu cannot lie."

---

## Contents

1. [What a reconciler is](#1-what-a-reconciler-is)
2. [The contract](#2-the-contract)
3. [Observations](#3-observations)
4. [The loop](#4-the-loop)
5. [Drift, blocked, and conflict](#5-drift-blocked-and-conflict)
6. [Safety limits](#6-safety-limits)
7. [Restore, fork, and candidates](#7-restore-fork-and-candidates)
8. [The constitutional catalog](#8-the-constitutional-catalog)
9. [Budgets, storms, and heat](#9-budgets-storms-and-heat)
10. [What the daemon does with reconcilers](#10-what-the-daemon-does-with-reconcilers)
11. [Worked example](#11-worked-example)
12. [Failure modes](#12-failure-modes)
13. [Conformance](#13-conformance)
14. [Invariants](#14-invariants)
15. [Open decisions](#15-open-decisions)
16. [Glossary](#16-glossary)

---

## 1. What a reconciler is

The thermostat, made general. A `spec` facet is the dial: desired state, written by intent — the person, the daemon, a granted worker. A `status` facet is the thermometer: observed state, written by exactly one reconciler. The reconciler is the furnace: it notices the gap and works to close it, forever, within limits.

Three things distinguish it from a script that "makes X true":

- **It is the admitted writer of its status.** Authority mode `reconciler` is admitted for one current controller/incarnation per status family and scope ([[Extensions]] §6.1). The native gateway enforces admitted writes. Separate cache and conflict services have separate contracts; guest root is not a strong per-controller identity boundary.
- **It converges instead of executing.** It does not run a plan to completion; it repeatedly asks "does reality match the spec?" and takes the smallest convergent step. Running it twice is the same as running it once.
- **Its output is an observation.** Status is a claim about what the reconciler saw, with epistemics attached. A consumer that treats it as truth has made a mistake the format is designed to prevent.

The pattern is Kubernetes' controller, adopted deliberately ([[Objects and Facets|Objects]] §3.6). Two Agora specifics change its character: reconcilers act through **brokers under grants**, so a reconciler can never reach further than the person allowed; and reconcilers are **entities** — they have specs and statuses of their own, so the machinery that keeps the world honest is visible inside the world.

---

## 2. The contract

A reconciler is installed as an extension whose bundle includes a **reconciler manifest**. The registry checks this manifest, current delegation, supported runtime isolation and conformance before admitting `reconciler` authority. The manifest alone grants nothing.

```yaml
reconciler:       core.process
version:          1.2
reads:
  spec:           process.spec              # the family it serves
  also:           [core.file-backing.status, core.capability.status]   # inputs it may consult
writes:
  status:         process.status            # sole writer
owns:             entities carrying process.spec that this reconciler holds a grant for
effects:                                    # everything it may cause, all convergent
  - start local process under a confined launcher
  - stop local process it started
  - bind a local port
needs:            [launch.confined, port.bind:local, read core.file-backing]
excludes:         [network.outbound, credential.*, delivery.*, host.*]
freshness:        30s                       # observations older than this are stale
resync:           60s                       # slow tick, independent of events
backoff:          { initial: 1s, factor: 2, max: 5m, give_up_after: 12 attempts }
stop_when:        [grant revoked, spec detached, entity tombstoned, budget exhausted, ownership lost]
incarnation:      fresh per start; observations carry it
budget_charged_to: the spec's writer
projection:       "{state}, pid {pid}, {drift?} — checked {age} ago"
```

| Field | Rule |
|---|---|
| `reads.spec` | Exactly one spec family. A reconciler serving two families is two reconcilers. |
| `reads.also` | Other facets it may consult, read-only. Declared so composition can be analyzed ([[Security]] §5, row 5). |
| `writes.status` | Exactly one status family for a resource controller. Shared runtime services own conflict records; pure derivations have a separate declared cache contract. |
| `owns` | The entities it reconciles: those carrying the spec **and** covered by a grant to this reconciler. A spec on an entity the reconciler has no grant for is aspirational and stays so. |
| `effects` | Enumerated, convergent, idempotent. Each maps to a broker. |
| `needs` / `excludes` | Grants requested and grants it declares it must never hold. The registry refuses a manifest whose `needs` exceed what its conformance cases exercise, and honors `excludes` as a hard ceiling even if a person later over-grants. |
| `freshness` | How long an observation may be treated as current. |
| `resync` | The level-triggered tick. Never zero: a reconciler that only reacts to events will drift when it misses one. |
| `backoff` | Retry schedule and the point at which it stops trying and reports `blocked`. |
| `stop_when` | Conditions under which it must cease acting on an entity, immediately. |
| `budget_charged_to` | Whose budget pays for reconciliation. Defaults to the spec writer, so a hostile spec cannot spend the world's resources. |
| `projection` | How its status renders. Must never shorten uncertainty into success. |

A managed reconciler's `effects` list is a ceiling on its behavior, enforced by an execution boundary outside that controller's authority, not a description of a plan. Every effect must satisfy: *applying it when the system is already converged changes nothing.* Ensuring the same managed incarnation exists is a no-op when it is already running. Starting a process idempotently does not make the program's internal effects idempotent; its network, credential and delivery boundaries still need current checks. Binding a port already bound by that process is a no-op. Anything that fails this test — sending, posting, paying, printing, deleting a remote resource — is excluded from reconciliation by definition and belongs to the one-time-effect path ([[Objects and Facets|Objects]] §5.4).

---

## 3. Observations

Status is not a value. It is an observation record:

```yaml
process.status @ prototype_117
  concerns:      process.spec rev 3          # which desired state this observation is about
  observer:      core.process               # which reconciler
  incarnation:   r-8f2a                     # which run of it
  observed_at:   e6194 / 18:11:04
  fresh_until:   18:11:34
  state:         running | starting | stopping | stopped | blocked | unknown
  value:         { pid: 8194, port: 5173, health: ok }
  drift:         none | pending | blocked(reason) | conflict(ref)
  attempts:      1
  last_error:    null
  evidence:      [launcher receipt op-3c1e]
```

Rules:

1. **`concerns` is mandatory.** An observation about spec rev 2 says nothing about rev 3. Consumers compare `concerns` to the current spec revision before believing anything; a mismatch is drift, not truth.
2. **Freshness expires.** Past `fresh_until`, the status projects as stale. The daemon's context shows "last seen healthy 4m ago," never "healthy."
3. **Incarnations supersede.** When a reconciler restarts, its new incarnation's first observation replaces the old one; an old incarnation that keeps writing (a zombie) is refused by the gateway, because the incarnation is part of the write authority.
4. **`unknown` is a state.** Not `stopped`, not `ok`. A reconciler that cannot observe says so.
5. **Evidence, where it exists, is a receipt reference.** A broker receipt for the launch is `verified`; the reconciler's interpretation of it is `attributed`. The trust classes stay distinct ([[Security]] §4.1).
6. **Status is a claim.** A compromised reconciler produces well-formed false observations. Nothing downstream — not capabilities, not lifecycle proposals, not the daemon's plans — may treat status as authority. It informs; grants decide.

---

## 4. The loop

Level-triggered, per owned entity:

```
on any of: spec written · status expired · resync tick · broker signal · grant changed
  1. read   current spec (rev R), current status, declared inputs
  2. verify grant is current (revocation generation) — if not, write blocked(no-grant) and stop
  3. compare desired vs observed
       converged  → refresh volatile freshness; record only changed durable facts; done
  4. plan   the single smallest convergent step
  5. check  the step is in `effects`, within budget, not excluded
  6. act    through the broker; receive a receipt or a failure
  7. observe reality again
  8. write  observation (concerns R, attempts, evidence, drift)
  9. schedule next pass per backoff if not converged
```

Design choices, with reasons:

- **Level-triggered, not edge-triggered.** The loop compares state, never replays a queue of events. Missing an event is harmless; the next tick sees the same gap. This is what makes reconcilers survive restarts, partitions, and their own bugs.
- **One step per pass.** A reconciler never executes a multi-step plan atomically. Each pass takes one convergent action and re-observes. Reality may have moved; someone may have revoked; the spec may have changed. Long plans are how controllers fight users.
- **Grant check every pass.** Not at start. Revocation must land within one pass, and a reconciler mid-backoff must not resume with dead authority.
- **Coalesced writes.** A pass that observes no change refreshes volatile observation state, not replay-derived durable tables. That refresh is not an event. Status *change* is an event, authored by the reconciler, grouped under the intent that caused the spec write where one exists ("spin up demo" → its status events hang under it). Every poll is not history.

Ordering between reconcilers is never orchestrated. The process reconciler does not call the file reconciler. It reads `core.file-backing.status`; if the path is unresolved it writes `blocked(waiting: file-backing)` and waits. When the file reconciler heals the binding, the process reconciler's next pass proceeds. Dependencies are declared in `reads.also` so they can be inspected, and resolved by patience rather than choreography.

---

## 5. Drift, blocked, and conflict

**Drift** is any gap between spec and observation. Its causes are a short taxonomy, and each has its own honest answer:

| Cause | Observation says | Reconciler does |
|---|---|---|
| spec changed | `concerns` < current rev; `drift: pending` | converge toward the new rev |
| reality changed | value differs from spec at same rev | converge back (restart the process, re-bind the port) |
| observation expired | stale | re-observe |
| input missing | `blocked(waiting: X)` | wait; re-check on tick |
| grant missing or revoked | `blocked(no-grant)` | stop acting; report |
| handler or resource unavailable | `blocked(unavailable: Y)` | backoff; report |
| attempts exhausted | `blocked(gave-up after N)` | stop; report; resume only on spec change or explicit retry |
| two specs cannot both hold | `blocked(owned-by: X)` or `conflict(ref)` | keep a valid incumbent; queue/refuse the new claim or surface unresolved ownership |

**Blocked is a first-class state.** It is not an error and not a failure of the reconciler; it is the reconciler telling the truth about why the world is not as specified. A spec with no reconciler at all is legal and inert — an aspiration whose drift is permanently visible ([[Objects and Facets|Objects]] §4.2). A spec whose reconciler is blocked is the same thing with a reason attached. The daemon can read the reason and act on it: request a grant, install a handler, fix a path.

**Conflict and ownership.** Two specs asking for port 5173 do not give the
second writer a way to stop the first service. Resource contracts specify an
incumbent, waiting/refusal policy and explicit transfer. If ownership is ambiguous
or the user needs to resolve competing intent, the runtime records a conflict
entity with both specs and their authors. Status writers reference that conflict;
they do not acquire arbitrary writes to each other's objects. Change a port or
transfer ownership through an ordinary authorized operation, then reconcile.

---

## 6. Safety limits

Reconcilers are the most autonomous components in Agora: they act continuously, unprompted, forever. The limits are correspondingly strict, and each traces to [[Security]].

1. **Convergent effects only.** Everything in `effects` is idempotent. A reconciler that would need a one-time effect to satisfy a spec — "keep this announcement posted," "keep the invoice paid" — does not perform it. It writes `blocked(requires: one-time effect)` and the daemon proposes the effect under the applicable standing delegation or a new grant when needed. [[Security]] §4.4: the failure mode is a repeated external action, and reconciliation is a machine for repetition.
2. **Brokers, always.** A reconciler never touches a resource directly. Its launcher, port, file, and device operations are broker calls checked against its grant at the effect boundary. Enforcement lives outside the authority it constrains. A controller with guest root cannot claim a narrow in-guest sandbox; use an isolated execution domain when that ceiling must resist a hostile controller.
3. **`excludes` is absolute.** A process reconciler declares it excludes network, credentials, delivery, and host access. Even a person who over-grants cannot make it use them; the manifest's ceiling binds the registry's admission.
4. **No one-time effects hide in convergence.** "Bind a port" is convergent. "Register with a remote service" is not, however idempotent the API claims to be, because the remote side keeps state Agora cannot observe. When a reconciler's effect crosses to an external party, it is treated as one-time unless the adapter definition proves idempotency with a receipt ([[The Web|Web]] §5.3).
5. **Ownership is grant-scoped.** A reconciler reconciles only entities it holds a grant for. It cannot adopt an entity because the entity has its spec; the grant is what makes the entity its business.
6. **Specs are intent-authority; a hostile spec buys only what the reconciler may do.** An attacker who can write `process.spec` can make the reconciler start a process under a confined launcher on a local port — the entire `effects` list — and pay for it from the attacker's budget. They cannot make it do anything outside the list. Least privilege for reconcilers is what makes spec facets safe to open to intent-writers.
7. **Status is never authority.** Repeated for emphasis, because the temptation is strong: `capability.status` lists verbs; it does not grant them. The broker checks the grant when the verb is invoked.

---

## 7. Restore, fork, and candidates

Reconcilers are how "the world reassembles itself" after reboot. They are also the most dangerous component after restore, because a reconciler seeing an old spec and no status will cheerfully make yesterday true.

- **After reboot**, historical statuses remain records, but their live validity expires. Controllers re-observe and apply each activity's resume policy. A maintained service may restart; a call or playback session must not activate a device merely because its saved state existed.
- **After restore**, the keep has not moved ([[Security]] §2.3). Every reconciler's grant is checked against the current revocation generation before its first pass; grants that were revoked stay revoked; grants that existed are re-issued only if current policy allows. A restored world with no re-grants is a world of `blocked(no-grant)` statuses — visible, honest, and inert until the person re-authorizes. This is the property that turns rollback from a security hole into a reboot.
- **After fork**, the new world-line has a new authority domain. Reconcilers in the fork begin with no grants, so a forked room does not double a pending job. Specs come with the fork; the power to satisfy them does not.
- **In a candidate world-line** (self-modification, extension proving, the nursery), reconcilers run with the candidate's grants, which are scoped to the yard: local resources, no external effects. A candidate that would need external effects to test cannot be fully tested in isolation, and its conformance says so.
- **Zombies.** A pre-restore incarnation that somehow still runs is refused on write, because the host's current execution epoch supersedes its lease. The receiving effect boundary fences stale work as well as the next controller pass.

---

## 8. The constitutional catalog

The proposed catalog, not a required build order. Resource controllers, pure caches and advisory services share some scheduling but have distinct write contracts. Vernacular reconcilers follow the same contract and are admitted through [[Extensions]].

| Reconciler | Reads | Writes | Effects (all convergent) | Stops when |
|---|---|---|---|---|
| **process** | `process.spec` | `process.status` | start/stop confined local process; bind local port | grant revoked; spec detached; conflict on port |
| **file-backing** | `core.file-backing.spec` | `core.file-backing.status` | resolve path by inode or content hash; verify hash; re-bind after rename | path unresolvable after N attempts → `blocked(missing)`; never moves or deletes bytes |
| **remote-ref** (per adapter) | `core.remote-ref` bindings, adapter policy | `core.remote-ref.status` | fetch on schedule; refresh freshness; report change | rate limit; auth failure → `blocked(unavailable)`; never writes to the provider |
| **capability** | installed manifests, entity facets, grants | `core.capability.status` | none — bounded derived computation | backpressure or budget; invocation always rechecks |
| **lifecycle** | salience, retention pins, dependents | `core.lifecycle.proposal` | none — it proposes transitions; it never performs them | never; it is advisory by design ([[Objects and Facets|Objects]] §4.6) |
| **index** | facet writes, `core.collection.query` | derived indexes and living-query result caches; never authoritative explicit entries | rebuild or update full-text, vector, graph indexes; recompute query membership | budget; indexes are disposable, so `blocked` here degrades search, never data |
| **registry** | extension bundles, conformance results, adoption provenance | `extension.status` | none — sets tier from evidence | never; tiers are reconciled facts, not decisions ([[Extensions]] §3) |
| **watch** | `web.watch.spec` | `web.watch.status` | re-fetch a page under its grant; compare to cast | schedule ends; grant revoked |
| **sync** (per device) | `sync.spec` | `sync.status` | replicate accepted events between the person's own devices | device revoked; partition (reports `blocked(partition)`, never merges authority) |
| **download** | `download.spec` | `download.status` | fetch bytes to a confined path; resume | destination full; source gone; grant revoked |
| **salience** | presence checkpoints, edges, task objects, bids | the field (system authority) | none — pure computation on a fast/slow tick | never; it is the attention system's engine, and its writes are `system`, not `reconciler` |

Two rows deserve a note. The **lifecycle** reconciler only proposes; it is the one place where the framework's autonomy is deliberately withheld, because attention is never sufficient reason to forget. The **capability** computation supplies the registry projected to both menus and tools. It is bounded and invalidated on relevant changes; invocation rechecks rather than trusting a stale menu.

---

## 9. Budgets, storms, and heat

**Budgets.** Reconciliation is charged to the spec's writer. A worker that writes fifty specs pays for fifty reconcilers' attention; when its budget is exhausted, its specs go `blocked(budget)`. Platform reconcilers that serve the person (capability, index, lifecycle) draw from the person's budget with reserved floors so they cannot be starved by a hostile spec.

**Storms.** Event → reconcile → status event → reconcile is the classic loop. Three rules prevent it: a reconciler's own status writes never trigger its own pass; freshness refreshes are not events; and the loop is level-triggered, so a burst of N spec writes produces one pass reading the latest revision, not N passes. Across reconcilers, cascades are bounded by the `reads.also` graph, which the registry checks for cycles at admission.

**Backoff and circuit breaking.** Retries follow the manifest's schedule. After `give_up_after`, the reconciler stops and reports; it resumes only on a spec change, a grant change, or an explicit retry verb. Repeated give-ups across many entities trip a per-reconciler breaker that pauses it and raises a bid.

**Heat.** Status changes bid for attention like any event ([[Security]] §4.5). A reconciler's bids are `attributed`: converged → no bid; drift pending → warm; `blocked` → a bid proportional to the spec writer's standing (the person's own specs bid higher than a worker's); `conflict` → a bid on the conflict object. `blocked(no-grant)` after a restore is a security bid with reserved heat, because a world that silently stays inert is a world the person believes is running.

---

## 10. What the daemon does with reconcilers

The daemon edits specs for maintained intent. It also performs direct native edits, invokes installed tools and uses guest execution ([[Native Development]]). Reconciliation is one action family, not a universal lifecycle for all work.

What it reads:

- **Drift as a to-do list.** Every `blocked` status is a sentence: "this cannot be true because X." The daemon's context renders blocked statuses at higher heat than converged ones, so the world's unmet promises are always in view at a glance.
- **Freshness as confidence.** "healthy, checked 2s ago" and "healthy, last seen 40m ago" are different facts, and the projection keeps them different.
- **Conflict as a question.** A conflict object is a request for a decision, addressed to whoever can make it.

What it may do:

- write specs it holds grants for; detach them; retry a given-up reconciler;
- ask the registry why a reconciler is not admitted, or request its installation through [[Extensions]];
- propose, on the person's surface, the grants a blocked reconciler is missing — with the reconciler's manifest shown, so the person sees what they would be enabling.

What it may not do:

- write any status;
- perform an excluded effect on a reconciler's behalf "to help";
- treat a status as permission.

---

## 11. Worked example

`prototype_117` carries `process.spec { serve: /projects/demo, port: 5173 }`, written by the daemon on Alex's behalf under an intent "spin up a demo."

**Normal.** The process reconciler's pass: grant current → file-backing status resolved → no process → plan `start` → launcher broker → receipt op-3c1e → observe pid 8193 → write `running, concerns rev 1, fresh 30s`. Capability reconciler sees `spec` + `status` → `start`, `stop` appear in Alex's menu and the daemon's tools.

**Kill.** Process dies. Next tick: observed absent, spec says present → drift → `start` → new pid 8194 → `running`. One status-change event, grouped under the original intent.

**Reboot.** Old observations lose live validity. The service's declared resume policy allows restart; the first pass re-observes and proceeds. Alex did nothing.

**Port taken.** Alex's daemon writes a second `process.spec` on `notebook_4` asking for 5173. The reconciler's pass on `notebook_4` finds the port held by `prototype_117` under a live spec. It leaves the existing service running and reports `blocked(owned-by: prototype_117)` on the notebook. If a decision is needed, the runtime records `conflict_44` with both requested bindings and bids. Alex says "move the notebook to 5174"; the spec changes; the conflict composts; both converge.

**Directory renamed.** Alex renames `/projects/demo` to `/projects/cache-demo` in a terminal. File reconciler: path unresolved → re-resolve by inode → heal `file-backing.status` → event. Process reconciler next tick: input changed → restart under the new path → `running`. Nothing asked Alex anything; the world followed him.

**Restore.** Alex restores yesterday's snapshot. Process reconciler's first pass: grant check against the keep — revocation generation is current, and the reconciler's grant was issued before the snapshot and never revoked, so under current policy it is re-issued. Pass proceeds; demo comes up. Had Alex revoked it this morning, the status would read `blocked(no-grant)` and bid with reserved heat, and the demo would stay down until Alex chose otherwise.

**Missing grant from the start.** A research worker writes `process.spec` on a scratch entity in the nursery. The process reconciler holds no grant for nursery entities. Status: `blocked(no-grant)`, charged to the worker, bidding at worker standing — a warm glance in the daemon's context, no interruption. The spec is aspirational, as the worker's specs should be.

---

## 12. Failure modes

| Failure | Looks like | Prevented by |
|---|---|---|
| **flapping** | two reconcilers, or a reconciler and a person, alternately undoing each other | single writer per status; conflicts become objects; convergent one-step passes |
| **stale truth** | a consumer acts on an observation about an old spec | `concerns` mandatory; freshness expires; projection shows age |
| **thundering herd** | every reconciler storms the brokers after restore | jittered first passes; budgets; reserved recovery capacity |
| **zombie incarnation** | an old run keeps writing status | incarnation is part of write authority; refused on write |
| **runaway loop** | a reconciler triggers itself | own writes never trigger own pass; refreshes are not events; level-triggered |
| **make-yesterday-true** | restore replays old intent with old power | grant check every pass; keep outside rollback; no re-grants → `blocked` |
| **helpful escalation** | a reconciler performs a one-time effect to satisfy a spec | `effects` are convergent by definition; external effects are one-time unless proven; `excludes` |
| **silent inertness** | a world that looks running but is blocked everywhere | `blocked` bids; `no-grant` after restore is a security bid |
| **hostile spec spend** | an attacker's specs exhaust resources | budget charged to the spec writer; reserved floors for platform reconcilers |
| **authority by status** | a verb listed in `capability.status` treated as permitted | broker checks the grant at invocation; status is a claim |

---

## 13. Conformance

Any reconciler must pass:

| Category | Case |
|---|---|
| idempotency | two consecutive passes against a converged system produce no effects and no events |
| convergence | from any observable state, repeated passes reach the spec or a `blocked` state with a reason |
| concerns | an observation never claims to concern a spec revision newer than the one it read |
| freshness | a consumer reading past `fresh_until` sees `stale`; the projection shows age |
| single writer | a write to its status family from any other principal is refused |
| ceiling | an attempt to perform an effect outside `effects` or inside `excludes` is refused by the broker, and reported |
| grant check | revocation lands within one pass; a revoked reconciler writes `blocked(no-grant)` and stops |
| restore | after restore with no re-grant, no effect is performed; status reads `blocked(no-grant)` and bids |
| fork | in a forked world-line, the reconciler performs nothing until granted |
| conflict | a competing claim cannot stop a valid incumbent; unresolved ownership produces a conflict record under the resource policy |
| storm | a burst of N spec writes produces one pass; own status writes trigger nothing |
| budget | exhausting the spec writer's budget produces `blocked(budget)` with no further effects |
| zombie | a superseded incarnation's write is refused |
| projection | `unknown`, `blocked`, and `conflict` are never rendered as success at any tier |

---

## 14. Invariants

1. A resource controller writes its admitted status family; conflict services and pure caches use separate declared write contracts.
2. Status is an observation: it carries the spec revision it concerns, its observer and incarnation, a time, and a freshness horizon.
3. Status is never authority; it informs, and grants decide.
4. Reconcilers are level-triggered; missing an event is harmless.
5. Every effect a reconciler may cause is convergent and idempotent; one-time effects are never reconciled.
6. Reconcilers act only through brokers, under their own grants, checked every pass.
7. `excludes` is an absolute ceiling that no grant can raise.
8. Ownership is grant-scoped; a spec without a grant is aspirational and visibly so.
9. Blocked is a first-class state with a reason; conflict is an object, never a fight.
10. After restore or fork, a reconciler performs nothing until re-granted.
11. Reconciliation is charged to the spec's writer; platform reconcilers hold reserved floors.
12. The lifecycle reconciler proposes and never performs.

---

## 15. Open decisions

- resync and freshness defaults per catalog reconciler; jitter policy after restore;
- the exact form of receipts a reconciler may cite as evidence, and whether broker receipts are visible to it directly or via the keep;
- cycle detection in `reads.also` versus runtime cascade limits;
- whether the salience computer is formally a reconciler (same loop) or a distinct system service (different authority mode); currently the latter;
- conflict-object defaults for physical resources (ports, devices): first-holder-keeps versus neither-until-resolved;
- the `retry` verb's authority: spec writer only, or anyone with the spec grant;
- reconciler manifests for adapters: how much of the remote-ref freshness policy is per-provider;
- nursery grants: whether the process reconciler should ever be granted nursery entities (current lean: no).

---

## 16. Glossary

**Blocked** — a status state meaning the spec cannot currently be satisfied, with a reason.
**Concerns** — the spec revision an observation is about.
**Convergent effect** — an action that changes nothing when applied to an already-converged system.
**Drift** — any gap between spec and observation.
**Excludes** — grants a reconciler declares it must never hold; an absolute ceiling.
**Incarnation** — one run of a reconciler; part of its write authority.
**Level-triggered** — comparing state to spec on any change and on a tick, rather than replaying events.
**Observation** — a status record with epistemics: observer, incarnation, time, freshness, evidence.
**Pass** — one iteration of the loop: read, verify, compare, plan one step, act, observe, write.
**Reconciler** — the sole writer of one status family; drives observed state toward spec within a contract.
**Resync** — the slow tick that makes the loop level-triggered.
**Spec** — a desired-state facet, written by intent.
**Status** — an observed-state facet, written only by its reconciler.

---

*Every clause above traces to a design document in this repository; where it does not, it is marked as a proposal. The Constitution remains authoritative.*
