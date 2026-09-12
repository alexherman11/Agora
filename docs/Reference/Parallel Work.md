# Parallel work prototype

**Isolated experimental worldline; September 12, 2026.** This is an implemented
prototype with bounded live evidence, not a claim that every future request or
untrusted program is supported. It does not change the original worldline.

## Product contract

JEFF keeps one continuing conversation and delegates independent assignments to
native tasks. A task has a stable identity, a versioned brief, exact object/package
grants, collaborators, optional prerequisites and named exclusive resources. An
attempt is one execution of that brief in a separate candidate world. Two attempts
may run at once. The person can keep talking to JEFF during their work.

The authored Work panel shows actual states, wait reasons, public progress, task
scope, results and attempt history. It supports messages to active workers,
cancellation, explicit retry and candidate adoption. Its draft survives polling.
The protected header/recovery also offers Stop workers independently of this panel.
Stop JEFF stops the foreground conversation; Stop workers cancels queued/active
tasks. Neither rolls back committed work.

| State | Meaning |
|---|---|
| queued | Waiting for capacity, a named resource, a prerequisite, or an old attempt to stop. |
| starting/running | A current attempt owns a worker slot and a private candidate. |
| waiting_resource | The current attempt is waiting to use the clean yard; the holder is named. |
| ready | A completed candidate is retained; its changes are not live. |
| adopted | Candidate object/source changes were committed; package activation is separate. |
| blocked/failed | A worker reported a blocker or execution failed; explicit retry is required. |
| cancelled/interrupted | Further candidate authority is fenced; retained work is inspectable. |

## Implemented boundaries

`work_specs.py` supplies the operation registry, `work.py` owns protected task
records and adoption, `work_scope.py` constructs and fences candidates, and
`work_scheduler.py` manages attempts and resource leases. Every native mutation
still uses `Gateway.commit` and the journal. Replay never starts an agent or runs
candidate source. Result blobs live beside the world under `work/`; task records
retain their digest. Back up that directory with the database to retain exact diffs.

A worker sees granted object/package snapshots and its own output namespace.
Previously adopted outputs in that namespace remain editable in later attempts.
Schema definitions needed for native validation are copied as runtime metadata.
Workers receive world get/query/transact, scoped package source/build/check tools,
and worker communication operations. They cannot install packages, use arbitrary
guest commands, control the live browser, or create grants. Code checks run in a
separate resettable Linux yard without live-world credentials. This is scoped
native access, not a general network or hostile-code security claim.

Prerequisites must be ready/adopted before launch. Predeclared resources are
acquired together before a worker slot is consumed. The clean yard also has a
dynamic lease. Resource ownership persists until the runner finishes cleanup;
cancelling does not pretend a still-running guest operation has released it.
Priority is considered at launch; there is no general starvation guarantee.
The visible queue accounts for managed workers. Existing direct executive/guest
operations retain their underlying yard serialization, not a unified resource UI.

All baseline object/package/installation revisions are checked atomically at
adoption. A changed prerequisite result or brief also invalidates adoption. The
system refuses stale results instead of guessing a merge. A revised brief fences
the old attempt. Old messages stay inspectable but do not become instructions for
the revised brief; an explicit retry retains messages for the same brief.

Linked collaborators may exchange reports and inspect public task results. They
receive no additional object access. Delivery distinguishes saved messages from
runtime acceptance; acceptance does not itself prove incorporation. Ready,
failed, blocked and question updates are delivered to JEFF, including during his
active turn. Routine progress/evidence remains inspectable without waking him.
Notifications are not an exactly-once external-effects protocol.

The prototype bounds concurrency to two, unfinished tasks to 24, attempts per task
to 12, task messages to 100, retained updates to 40, candidate result snapshots to
1,000 objects, and atomic adoption to 199 changed objects plus the task record.
Call/time exhaustion is failure, never candidate readiness. Interrupted work does
not restart silently. Protected revoke closes workers before changing authority;
resume creates a supervisor for the new generation without replaying interrupted
attempts. Unexpected runtime item envelopes are tolerated, while genuine model
failures remain failures.

## Live rounds and corrections

1. JEFF delegated an investigator and reviewer sharing `review-bench`, plus an
   unrelated writer. Two workers ran concurrently; the reviewer waited without
   occupying a slot. All three produced separate candidate notes. Friction:
   the protected frame omitted work operations, and evidence reports woke JEFF
   prematurely. The frame now derives those operations from the registry;
   evidence alone no longer triggers an executive turn.
2. A scoped builder and linked reviewer developed `parallel.split`. The reviewer
   sent edge cases and obtained an actual refusal when probing the synthetic
   out-of-scope object. The builder incorporated the browser-sent River stone
   clarification. A draft survived polling and JEFF answered ordinary chat while
   the workers ran. The candidate retained 26 passing checks in the cloned yard.
   Peer delivery exposed authority-lock contention; delivery was moved outside
   the world transaction. A subsequent live peer ping during a wait succeeded.
3. Real browser controls cancelled a worker and released its resource to the
   queued successor. Brief revision stopped an old attempt. An intervening
   fixture edit made adoption fail without overwriting it; another revision
   used the current input. Browser adoption followed by JEFF's build/install and
   actual invocation returned `[4, 3, 3]` for `split(10, 3)`. An old peer message
   resurfaced after brief revision; messages are now associated with their brief.
   Shutdown/cleanup, budget outcomes and recovery-generation checks were tightened
   during this round.

4. A real UI retry was interrupted by service restart and remained interrupted
   with exactly two retained attempts. The final revised worker saw zero
   current-brief messages while old messages stayed in history. It updated the
   same previously adopted output, which adopted successfully at revision 2;
   no old peer instruction was sent. A queued task's draft survived polling and
   laptop resizing, and protected Stop workers cancelled it without execution.
   Historical worker reports are labelled explicitly to distinguish them from
   later live installation state.

Verification: the complete suite passed **185 tests** (two opt-in runtime inventory
cases skipped); both actual-runtime inventory cases passed separately. The final
work/recovery regression subset passed 21 tests after the last consistency edits.
Ruff passed. The candidate receipts record 10 + 10 + 6 passing Linux checks,
with zero native application writes. Final native replay matched all 1,406 objects.
All 168 baseline source-file hashes in the original checkout matched, its service
responded, its managed conversation binding was unchanged, and `parallel.split`
was absent there. The prototype supervisor was online with zero active workers
and no error after its final reload.

The durable tasks/attempts and exact candidate receipts remain in the prototype
world. Additional browser inputs, observations and result snapshots are retained
in `C:\Projects\Agora\worlds\parallel-desk\evidence`. This evidence used real Edge
input through the Desk's browser tools. The separate native Windows computer-use
app approval timed out; no successful native desktop-control test is claimed.

## Returning and reproducing

The original launcher is
`C:\Projects\Agora\worlds\jeff0-desk\Open Agora Desk.ps1` (port 8873).
The prototype launcher is
`C:\Projects\Agora\worlds\parallel-desk\Open Agora Desk.ps1` (port 8874).
The prototype has a separate database, managed model-conversation fork, source
checkout and cloned live/yard VMs. Do not copy its database or conversation binding
back over the original to switch worlds. Launch the world you want.

The prototype launcher sets `AGORA_WORKERS=1`; generic new worlds do not enable the
supervisor automatically. The Work UI is retained in this world's installed shell
package, with its source also supplied in `src/agora3/builtin/work.js` and `.css`.
Run `uv run pytest`, `uv run ruff check src tests`, and the optional actual-runtime
inventory tests in `tests/test_jeff.py` with `AGORA_CODEX_BIN` configured. Those
inventory tests use local mock inference; they are separate from the live rounds.
