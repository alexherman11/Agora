# Parent dispatcher integration: disabled, for review

20 Oct 2026. Source work only. This is not an enabled or usable host route.
The builder of this follow-up also authored the preceding reference draft;
this is a fresh code review, not independent approval by another reviewer.
An independent maintainer/security review remains required.

## Review findings and disposition

1. **Authentication was a test seam, not implementation.** The prior policy
   model accepted arbitrary attestor callbacks and in-process object handles.
   Its nineteen passing tests did not exercise either real pipe reader or
   establish any Windows boundary. Keep that model explicitly nondeployable.
2. **Child generation was lost before dispatch.** `Resident._read` and
   `Worker._read_into` queued plain dictionaries. An old child could finish or
   exit after a new process started and contaminate its reply/state.
   Both actual readers now carry a parent-created `ChildSession` envelope.
   The consumer checks the registered session and the exact parent-held
   process object, not a PID, actor string or provider session ID. Rebinding
   clears a partial old reply; late result/exit events are ignored.
3. **Completed output had no provenance-aware interception.** Actual
   `Resident.turns_ended` now strips reserved typed host intents before
   `House.after_turn` sends ordinary lines to Desk. Worker turns use the same
   consumer and put public receipts in their normal inbox. Adjacent ordinary
   lines survive malformed/refused intents. Child-supplied JSON fields cannot
   construct a Python envelope. Legacy untagged test events remain usable for
   ordinary text, but have no issuing authority.
4. **Issuer session lifetime was not enforced in the model's caller path.**
   The review dispatcher binds grants to its pinned resident object plus the
   current parent generation. Worker rebind or issuer rebind/retirement
   invalidates prior authority. Changing `actor` or copying world props never
   changes the pinned parent identity.
5. **Journal behavior needed tightening.** Added a unique global running
   inventory fence as well as the card fence. A persisted running record
   blocks another executor, including another card, until explicit recovery.
   Busy/failed journal admission returns unknown without attempting inventory.
   Guard observation now occurs after acquiring the journal write fence, so
   it cannot go stale while waiting for that fence. Existing receipt replay,
   single use, expiry and revocation remain tested.

## Concrete source integration

- `notation/house.py`: bind a session before starting each reader thread;
  tag/validate queued events, preserve provenance across assistant/result
  events, intercept typed intents at completed turns, retire exited sessions,
  and deliver public receipts before ordinary Desk forwarding.
- `notation/workshop.py`: bind and tag the worker reader's captured queue;
  deliver its typed receipts through the existing inbox. No MCP endpoint,
  environment secret, command grant or provider setting was added.
- `notation/host_route_parent.py`: parent-owned session registry and typed
  intent grammar. The house constructs **only `ParentDispatcher`**, which
  unconditionally refuses host intents. It opens no journal or listener.
- `ReviewDispatcher` is a test/review integration joining those real queue
  boundaries to `ReferenceModel`. It has no live construction path or enable
  option. Its resident anchor must be supplied as an actual parent-owned
  object, never resolved from public world actors/props.
- The review grammar is a completed assistant line beginning
  `> host-route {JSON}`. Exact actions are grant/revoke with card and current
  generation, or inventory with a request ID. There is no shell text or
  caller-controlled query/filter/PID. Only parent-owned pipe provenance
  can reach attested handling. All authority handles stay in the parent.
  Grant notices and receipts contain no bearer capability.

The existing anonymous stdout/stdin pipes are the concrete candidate caller
channel; no extra helper or server is needed. This source establishes
in-process provenance from the pipe the parent reads. It does NOT prove that
a hostile same-user process cannot duplicate/write those handles or modify
the house's files. Object identity is not an OS security boundary.

## Precise deployment preconditions and acceptance

The source integration is ready to review; protected deployment remains
incomplete. This is not a settings toggle away from completion.

1. Have an independent maintainer review this diff, particularly stale-event
   rejection, receipt handling and the reserved grammar. Verify the real
   parent executable/source and resident identity anchor cannot be replaced
   by worker-writable code, world properties or a claimed resident name.
2. Supply an approved parent-owned JEFF resident anchor at house construction
   from trusted deployment identity. Do not look it up by mutable `actor`.
   Verify the intended child process/creation handle and that unrelated
   workers cannot duplicate/inherit its pipe handles or replace the child.
   Existing `Popen` object equality is generation provenance, not that proof.
3. Provision or identify a host-private journal location outside world and
   worker mounts, then verify actual read/write access using the real worker
   tokens, including SQLite journal/WAL/backup siblings. No production
   location, ACL change or security setting was created here. Merely putting
   SQLite outside a worktree, under the same user, does not establish privacy.
   If existing permitted isolation cannot protect it, report infeasibility;
   do not silently weaken sandbox/settings.
4. Implement/review fixed-scope Agora inventory plus trustworthy awake,
   interactive-session and no-game observations. None is provided by this
   patch. Unknown must refuse. No power request, wake task, input or visible
   window belongs in the operation. Use one host-owned journal/executor and
   preserve running-as-unknown across restarts; no automatic lease clearing.
5. Only after those source/deployment checks are accepted may a separately
   authorised maintainer wire the production service. Run one explicitly
   granted read-only turn from a real Codex child and retain success or
   truthful access-denial receipt. Demonstrate forged public Desk requests
   and copied world props cannot issue/revoke grants on the real deployment.
6. Keep the queued Claude activation fallback unchanged. It has NOT joined
   this journal. Any future lifecycle operation needs a separate review,
   explicit route grant, receipt reconciliation and handoff. There are no
   destructive operations in this patch.

No live resident/worker was started, host query run, helper/service launched,
grant issued, security setting changed or fallback mutated for this work.
Tests use fake children/streams and worktree/in-memory journals only. The
ordinary reaching regression runs existing Desk helpers against the supplied
`frontier-try` copy; it is not a host-route deployment or real model trial.

## Evidence from this worktree (ran)

- `test_host_route_parent.py`: `Ran 23 tests in 0.128s`, `OK`.
  Actual reader/queue/consumer/forwarding methods, fake child streams:
  forged source and actor, copied props, stale generation/exit, mixed raw
  events, target/issuer restart, revocation, fail-closed guards, duplicate
  receipt, persisted crash, competing executor/card, busy journal, disabled
  default, malformed intent and ordinary multiline quoted examples.
- `test_host_route_draft.py`: `Ran 19 tests in 0.066s`, `OK`.
- `test_charter.py`: `Ran 16 tests in 0.604s`, `OK`.
- `test_plan_usage.py`: `Ran 16 tests in 1.257s`, `OK`.
- `test_builders.py` and `test_worker_grant.py`: each printed `all passed`.
- `test_reaching.py`: `all passed (16 s, world frontier-try, corner f1603,
  chat a570)`. These are copy-world results, not real Conversation sends.
- `git diff --check`: exit 0. Full health/landing checks remain with the
  house. Both host-route test scripts are now registered as room tests.

Handbook section updated: "Commissions, workers and the keeper", a scoped
pending-source paragraph on disabled interception and child generations.
Rough spots links the missing authenticated grant word to this review.
