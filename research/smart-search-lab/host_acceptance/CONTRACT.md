# Authenticated hidden search acceptance — source candidate

This is a separately commissioned harness for dk1625/dk1774. **Unexecuted.
No feature approval, host approval, activation, or semantic acceptance.** The
reviewed product files and prior projection manifest remain unchanged.

Independent static review **dk1783 REJECTED the prior c9990903… manifest**.
This revision corrects its four assertion defects and exact action deltas;
it has not received independent re-review. That rejection was a source finding,
not an observed host failure. The prior 473 dependency entries were not verified
by that five-file independent review. No admission dependency approval follows.

## Commands for independent review

From this worktree, the source-only check is:

```powershell
& C:\Projects\Agora4\.venv\Scripts\python.exe -B research/smart-search-lab/host_acceptance/runner.py --verify-harness-source
```

This reads exactly the five named harness files, compares the four source
entries in the manifest and AST-parses three Python sources. It imports no
product or guard module and executes no host checks, observation, publication
or provisioning. An evaluator can instead use their own stdlib hashing/AST
script over the same five files without executing candidate code.
`--verify-source` is the separate full-manifest hash check; it requires scope
to read all 473 named sources and cannot stand in for independent byte review.
`freeze_source.py` reuses that existing fixed list with **no directory iteration**;
it refuses any non-harness dependency or product drift, then updates only the
four harness source entries and manifest metadata. Repeating it is deterministic.
Any changed byte requires a new manifest and independent review, including a
House landing that reconciles the shared kernel with Board/Documents work.

The callable **future host command**, withheld from execution this round, is:

```powershell
# JEFF/House first authorizes this exact fresh path and single attempt.
# Setting this process-local variable is part of that future authority.
$env:AGORA_TMP = 'C:\Projects\Agora4\.worktrees\kernel-dk1625-a4919333cb\.scratch\search-host-AUTHORIZED-ATTEMPT'
& C:\Projects\Agora4\.venv\Scripts\python.exe -B research/smart-search-lab/host_acceptance/runner.py --run --authority-record 'JEFF-WORLD-EXECUTION-RECORD' --attempt search-AUTHORIZEDATTEMPT
```

The placeholders must be replaced by the reviewed, named authority/path. No
directory in this example has been created. Neither the record string nor a
manifest authenticates authorization: the trusted operator/execution service
must enforce the external grant. A CLI flag cannot grant a worker host power.
There is no default execution, path fallback, alternate model or alternate
provider. This is not a retry route for any denied fixture.

## Required authority before the first host attempt

JEFF must resolve/assign the evaluator discovery denial from dk1774 separately;
this source commission does not transfer that blocked review. A trusted owner
must independently reconcile the admission producer/consumer bytes, authoritative
policy, publication ownership and deployment. This harness reads the existing
fixed-path `guard_context.read()` unchanged. It does not call `house.admission`,
publish/rotate a snapshot, replace a missing policy or certify that dependency.
The manifest binds this worktree's consumer, not the unresolved repair in another
worktree. Drift there or here blocks adoption until reviewed.

Independent source review must approve the exact manifest and command plus
these **future synthetic-only effects**: one isolated fixture directory; three
test-mode accounts/sessions; new synthetic kernel/genesis, grants and widgets;
two loopback listeners and the browser's ephemeral loopback CDP endpoint; one headless window module; one
headless InPrivate installed Edge with a fresh profile; CDP DOM input in the
hidden desktop; an inherited live Job; bounded receipts and owned cleanup.
None of those effects is authorized by the present source-only commission.
No real account, live world, real credential, external model or external data
is needed. External networking must also be constrained by the execution
environment: browser switches/CDP are defense in depth, not a network sandbox.
The fixture has no `.env`/live-session lookup and no stand-in entry service.

The operator must certify the installed interpreter/browser and all permitted
local ports as part of execution authority. The file manifest deliberately does not
pretend to bind installed binaries, imported standard library/site-packages, or
the live admission producer. The pinned interpreter invokes a measured base
interpreter child using existing guarded machinery; the whole family must stay
inside the live Job. No worker is created.

## Binding and assertions

`runner.py` verifies the exact source manifest before importing guarded host
machinery. It checks the unchanged fixed-path guard before scratch-configuring
imports, fixture directory, Job, suspended owned child birth, each bounded wait,
off and postflight. It holds `sandbox_window.Guard`, `job_scope` and the measured
`sandbox_birth.bound` root identity. It never adopts a PID or a saved Job handle.
Every false, missing, malformed or exceptional admission observation is latched
irreversibly as non-PASS in that process, including observations during cleanup.
A later admitted read cannot clear it. Both processes use a thread-safe latch.
On loss, only receipt recording and one cleanup of the established owned live
Job may continue; no new admitted host work or waiting for recovery.
The child also records a sticky attempt-owned `admission-lost.json` failure
receipt (not an admission attestation). The parent checks it at its boundaries
and again after owned job closure. Before publishing its final result, the child
closes its observation gate under the same lock, rejecting further host work;
the parent requires closed child observations and an empty child failure list.
This prevents a late asynchronous observation from silently changing a published
clear child outcome. It does not certify continuous safety between observations
or cancel an already-running imported helper operation.

`fixture.py` runs the **real** entry `App`, `Service` one-use code redemption
and `Seam`, real `EntryClient` with zero session cache, kernel HTTP door,
desktop HTTP widget broker, `Principal`, arrangement compiler, frozen painter
and lexical component. Test-mode identity provisioning is fixture setup, not
proof of email ownership on the internet or third-party SSO. It does not use
`StandInEntry`, fabricated caller objects, token dictionaries, emulated `api.rows`,
emulated `api.fire` or mocked renderer results. The ordinary trusted fixture
owner seeds this new world via the real join/door words. Viewer identities come
from verified bearer sessions, never body `as`. Widget principals are minted
by the production broker and narrowed by real grants/caller permissions.
The isolated kernel listener first uses the production shared-secret join
handler, then binds the production desktop handler before widget traffic;
the desktop handler itself intentionally does not expose that join secret.

Admission wrappers around HTTP and production module message/birth boundaries
delegate to the original implementations; they add guard refusal, not success
responses. Headless Edge uses the existing CDP transport, never the browser
helper that retries PermissionError/profile cleanup. Every CDP call and request
continuation rechecks the guard. CDP allows only the fixture origin plus local
document bootstrap schemes. It never navigates real content. A refused guard,
unexpected denial, source mismatch, timeout or missing executable fails this
attempt. No alternate path or process launch is attempted.

The runner is designed to assert:

- Successful owner, viewer and forged-viewer `who` calls must have the expected
  canonical principal/person/account identities. A trace keyed to each request
  observes the real production resolver's returned actor and canonical kernel
  account mapping; it neither supplies an actor nor changes the response.
  Display names and the response `as` field are never identity oracles.
  A successful owner-only operation must create the exact expected target
  window; the forged viewer must be refused that same operation with no window
  ID/target change. Another viewer cannot steal a widget instance.
- Actual caller-visible projected search labels/snippets exclude field-private
  and whole-private sentinels; a visibility change removes evidence from an
  existing module and the real search UI.
- Module grants cannot change source evidence. Grant revocation uses an existing
  instance with a successful exact-source search baseline. Widget-off uses a
  **different**, independently seeded widget with the same frozen painter/lens
  and original requested grants, provisioned before revocation of the first
  widget. Its grants must remain unchanged and a successful exact-source search
  must immediately precede off. Refusal after off therefore cannot be masked
  by the other widget's revoked grant. No revoked grant is restored or broadened.
  Disabling a synthetic entry account rejects its existing session.
- A fresh owner evidence action succeeds before testing the stale revision
  refusal into the real headless `window.open` module. Nonowner refusal alone
  cannot masquerade as a passing fence test. A real UI Enter searches without
  action; a changed hit abstains; a fresh evidence click opens the requested
  target. Fresh actions require exactly one added window ID with that target,
  no removed IDs and unchanged targets for every prior ID. Stale actions require
  equality of the entire window-ID-to-target map, not a count or any matching
  historical window. Actual deltas are recorded in the fixture outcome.
  A missing production revision fence must fail acceptance.
- A separate UI revocation record has an exact-source-ID query baseline and a
  uniquely named, connected real UI button visible **before** the independent
  writer revokes access. Its genuine retained button/closure is clicked stale;
  explicit unavailable status and a zero window-ID/target delta are required.
  Then a new real Enter search must finish and show no hit, with the exact source
  absent from a successful module reading too. Initially absent results, a
  detached/no-op button, UI remount alone or a failed reading cannot pass this
  case. No `api.fire` or result API is replaced to manufacture a stale action.
- Recovery of a foreign lens refuses. Two **synthetically submitted** health
  failures quarantine only that viewer, without log records; off creates a
  private preference, retry cannot clear quarantine, and a nonsteward cannot
  clear it. These exercise real health admission/state; they do not prove
  detection of a browser hang, genuine watchdog timing or quarantine UI.
- The child checks an 80-second monotonic deadline at its gates; the outer
  90-second deadline bounds only its result-wait loop after child birth.
  These are **not a proven hard whole-lifecycle cancellation guarantee**: setup,
  blocking HTTP/CDP/imported helpers, evidence processing and cleanup have
  separate/unverified bounds. One owned off must yield successful cleanup plus live Job `active=0`, `pids=[]`
  and an archived `job_closure="proven empty"` receipt. Guard continuity and a
  fresh postflight must pass. Missing foreground telemetry is UNKNOWN/failure.

All requirements fail on assertion; none is a claimed result. Unexpected
refusal or a genuine product defect is useful rejection evidence, not a reason
to broaden grants, edit the frozen product or retry a denied path.

## Limits and review outcome

**Freshness remains unresolved:** the unchanged consumer's five-second
attestation validity is not an 80/90-second lease. No supported freshness plan
covering actual setup, checks and cleanup has been established here. A separately
authorized producer/dependency owner must supply and review that contract or
an approved phase plan before execution. This worker adds no sampler, refresh
authority, request rotation, publication or admission retry. Expiry/unknown/loss
permanently fails this attempt even if a later sample is clear.

Exact helper/dispatcher source, process birth, inherited-job containment,
handle ownership, unknown partial launch/cleanup effects and timeout evidence
still require independent review under their own authority. A separate trusted
execution service must bound the full lifecycle and enforce the allowed fresh
paths, synthetic provisioning, listener/CDP ports and owned-cleanup scope.
The harness's guard calls, function wrappers and file hashes do not prove those
imported helper properties or resolve dk1774's denied discovery.

This targets lexical evidence delivery only; semantic inference/intent quality,
hard capability validation, private connectors and semantic activation remain
held. Prior 6/6 mocked UI checks and 8/8 in-memory projection checks retain their
original scope. A source hash or generic House pass establishes no host behavior.

Job closure certifies only the enrolled process family, not delegation to an
external engine. Environment-level egress control must cover background browser
traffic, workers, WebSockets, debug endpoints and delegated processes as
applicable; CDP interception and browser switches cannot establish it.
Receipts/profiles are retained, never traversed recursively or
deleted. This harness cannot certify network non-egress or Alex-screen continuity
when required telemetry is unavailable. Such outcomes must stay UNKNOWN.
The source author has not executed the fixture, browser, guard read, job,
listener or authenticated checks. Independent review may reject this harness
before execution. JEFF owns execution and any subsequent scoped activation;
the parent search task remains incomplete.
