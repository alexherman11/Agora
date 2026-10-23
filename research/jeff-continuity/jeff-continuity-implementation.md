> **Live implementation checkpoint, 23 October 2026 (supersedes the pending handoffs below).**
> This is an implementation/deployment task. Alex explicitly carried that approval forward;
> the original audit-only scope is superseded. The combined workflow and continuity source
> landed and activated as `c70ace59866a695f3c0361d0a874dd24dba884b3`. Five world verbs were
> installed through `/api/deploy`, and Jeff's `next_steps=on` is live. All eight temporary
> dispatch settings were restored. Historical receipts below remain historical.

# Jeff continuity and task ownership — implementation record

23 October 2026. Authored by architecture-audit from Alex's request and parent delegation.

**Implemented and privately tested; integration and live activation are still pending.**
This is one bounded continuation path built on existing tasks, promises and delivery.
It does not add a task database, background agent, memory store, model provider or poller.

## What changed

Task cards retain `goal`, `request_ref`, `next_action`, `acceptance`, optional
`parent_task`, and an explicit `review_at` timestamp. Existing owner/lead, priority,
status, commission, blocker, resolver, resume condition, dependency and evidence
properties remain canonical. The new fields are ordinary world properties.

Five editable world verb seeds implement the writing workflow:

- `task-next <task> "<next action>" "<acceptance>"`
- `task-revise <task> "<goal>" "<acceptance>" <request-ref> "<next action>"`
- `task-review <task> <current-basis> "<next action>"` also clears the old review deadline.
- `task-verify <task> <current-basis> <evidence-note>`
- `task-followup <task> <ISO-datetime-with-timezone>`

The seeds use existing expression guards and native `prop`/`read`; importing the
module never installs or edits world notes. Owner, lead or asker can maintain a
card. A delegated result is considered reviewed/verified only when its current
lead (otherwise asker, otherwise owner) authored the attestation. A worker's own
completion or attestation cannot review its result on behalf of the lead.

`rows nextsteps:<actor>` exposes the complete projection as a standard source.
An opted-in resident (`next_steps=on` on its own corner) receives the same current
projection on wake/entry/provider handoff and when its content changes. The packet
contains at most eight whole rows and fewer than 6,000 characters, including an
overflow count and the inspection command. It never truncates the incoming user
instruction or unresolved delivery packet. Explicit priority sorts first; error
volume and recency cannot promote a project. Open linked promises remain visible
even when a card is cancelled or done. Unlinked promises get their own rows.

The packet carries next actions, acceptance, review/verification status, blockers,
resolvers, resume conditions and waiting-on references. It does not invent a
"stale" threshold: a review is due only at an authored timezone-bearing deadline.
Malformed deadlines are visible as a diagnostic and do not trigger a guessed wake.
`next_steps=off` disables the host hooks without deleting any canonical task data.

## Received, reviewed and verified

**Received/queued:** the existing scheduler journals event receipt with its inbox
and cursor, stages consumed messages, saves pending delivery before a pipe write,
and marks delivery after flush. This is transport evidence. It is not proof that
the model understood a result or checked acceptance.

**Reviewed:** a current lead/owner authors `reviewed_basis` for the current task
intent and child result version. Successful model turns do not write this field.
It remains pending until that explicit act.

**Verified:** the authorized reviewer authors `verified_basis`, acceptance exists,
and `verified_evidence` resolves to a current world subject. Changes to the task's
material intent, owner/lead, child result or referenced result evidence invalidate
old attestations. Editing verification evidence after the attestation also makes
it unverified. An arbitrary token or a worker attesting for its lead does not count.
Undone attestations do not count. Undoing a material change restores its prior basis.
The verification token and canonical evidence reference must occur in the same
authorized event. Swapping only the current evidence property cannot borrow an
older verification. The world verb invalidates the prior basis before writing
the new pair, allowing explicit re-attestation even when the current property
values would otherwise make native `prop` a no-op. Interruption between these
writes leaves the task unverified.

Verification is an attributed, inspectable owner claim. The host cannot decide
whether arbitrary prose evidence actually proves arbitrary prose acceptance.
That judgment remains the owner's job. No new verb automatically marks a task
done, closes a parent, confirms a native promise or starts an external action.
Tracked cards marked done without valid verification remain visible. Existing
legacy closed cards are not mass-reopened.

## Event handling

This is an independently proposed event model grounded in Jeff's code, not a
description of another assistant's private infrastructure.

| Event | Existing source / new behavior | Correlation and replay | Next action and user update |
|---|---|---|---|
| User instruction, correction or cancellation | Existing native conversation and stale-turn interrupt gates; owner reconciles task fields through `task-revise` and normal status edits. New authored priority changes request a next-steps review. | Native task/subject references and material basis; current cancellation/hold wins over old results. Natural language is not automatically classified into task edits. | Reconcile changed intent before continuing. Acknowledge material scope changes; no full task dump. |
| Child progress, completion or failure | Existing `task_flow` quiet material notices remain intact. Completion/failure also requests bounded cross-project attention review. | Native child task and optional `parent_task`; cursor plus new per-task event high-water marks. | Inspect evidence and author review; worker ending never closes the whole user task. User update only for meaningful progress, blocker, choice or verified outcome. |
| Blocker, permission hold or unknown effect | Existing blocker/resolver/resume fields and native delivery uncertainty gates. Projection keeps the hold visible. | Current task state, current authority and existing pending/relay receipts. | Wait for the stated resolver. Never treat a wake as permission, auto-resume held work or replay unknown effects. |
| Executor loss/recovery or provider quota | Existing retry/backoff, singleton lease, unknown-relay barriers and explicit quota-only provider policy. New task context is regenerated on handoff and failed-send recovery. | Existing resident state and provider generation; native tasks do not depend on provider tokens. | Reconcile delivery before retry. No new retry loop, credentials, provider selection or paid fallback. |
| Explicit task follow-up | New `review_at`, observed on an ordinary house pass. One durable request per task/deadline. | Receipt stored with inbox/cursor; changing the deadline explicitly re-arms it. | Review the task, not automatically execute it. Paused/cancelled/permission-held/unknown work does not trigger a follow-up. No OS wake timer. |
| Relevant external-source change | Existing sources can already create native task updates/notices. No new watcher is implemented here. | Require a native task link and source evidence. | Add a watcher only for an authorized concrete need; this slice adds no unsolicited monitoring. |
| Task ends/fails or priorities change | New compact review request after current-task lifecycle changes, including the owner's own completion event. | Existing durable inbox plus per-task high-water receipt. All unfinished siblings remain in the projection. | Return attention to explicit priorities and pending reviews. Do not auto-start another project. |

## Host versus world

The world owns intent, task state, evidence, priorities, deadlines and editable
workflow verbs. The standard row-source seam supplies inspection; a future module
can render these rows without another task schema or event subscription.

Two small host hooks are necessary: `Resident.send` attaches current context at a
real delivery/handoff boundary; `House.news` queues due/lifecycle attention under
the same atomic save as its existing inbox and cursor. A purely world-side note
cannot guarantee either boundary across process death or provider replacement.
`workshop.HOUSE_FILES` includes the helper so normal code activation detects it.

Code references (all under `research/text-desk-lab/notation/`):

- `task_next_steps.py`: `basis`, `attested`, `rows`, `packet`, `context`, `collect`.
- `task_next_steps_verbs.py`: world-editable seed bodies, with no import effects.
- `sources/nextsteps.py`: the ordinary inspectable row-source adapter.
- `house.py`: import and hooks around lines 593 and 1065.
- `workshop.py`: reload dependency declaration near line 60; drain logic unchanged.
- `test_task_next_steps.py`: native lifecycle and real scheduler/fake-transport fixtures.

## Evidence and acceptance

**RAN:** scoped final suite after independent review fixes:
**136 passed, 29 subtests passed in 5.29s**.
This includes new fixtures and existing task flow, portable residents, requested
restart admission, completion draining, conversation flow, quota repair,
unknown-transport and resident handover tests.

**RAN:** standard repository suite: **201 passed, 2 skipped in 32.91s**.
**RAN:** subscription-worker dependencies and scene sources: **70 passed in 3.41s**.
The standard/dependency checks preceded the two review fixes; the affected scoped
suite above was repeated after them. **RAN:** both new review regressions failed
on the prior candidate (**2 failed, 12 deselected in 0.85s**) before the fixes.
**RAN:** Ruff on the four new files: **All checks passed!**
**RAN:** removing only the new hooks from `house.py` and `workshop.py` reconstructs
the exact runtime repair owner's supplied hashes (allowing LF/CRLF normalization).
The repair's singleton, relay, quota and drain logic was preserved, not reimplemented.

Acceptance covered by the private fixtures:

1. A delegated task blocks with resolver/resume condition; the owner records a
   correction; child completion remains awaiting review; a current owner reviews
   and verifies against evidence; a further correction invalidates both old acts.
2. A child marked done remains visible until owner review, including a child
   without its own next-action/acceptance fields. Reviewing that child does not
   verify or close its parent. Twelve urgent-sounding dashboard
   failure updates do not outrank the explicitly urgent harness task.
3. A one-shot deadline survives JSON state reload, queues once, and re-arms only
   with a changed deadline. Pauses, cancellations, permission holds, unknown
   effects and malformed/zoneless dates do not wake it.
4. Own-task completion requests cross-project review. Repeated event passes and
   an earlier cursor cannot duplicate the same review notification.
5. Native source inspection works; undoing a result restores the prior material
   basis. The full row source retains overflow even when the packet is bounded.
6. Editing evidence or supplying a false basis does not verify acceptance. An
   open native promise remains visible beside its cancelled card.
7. Actual `Resident` JSON save/reload and `House.step` execute provider handoff
   and `send` with fake pipes. Identity, complete unresolved user correction,
   deadlines and current high-priority task survive. No old provider token is
   reused. A successful model turn still leaves the result unreviewed/unverified.
8. A failed pipe write re-includes current context on delivery recovery; the
   helper neither clears quota backoff nor performs an external effect.
9. After the lead verifies evidence A, a worker or lead swapping only the pointer
   to older unchanged evidence B makes verification false. The lead can explicitly
   re-attest B, and repeat that attestation safely through the native world verb.
10. `approval_required=True`, `true`, or `yes` matches the workshop's existing
    hold semantics. It suppresses due-review and lifecycle wakes without consuming
    the deadline; explicit release permits one review request.

The tests use bounded private in-memory worlds, native command dispatch, durable
resident JSON files, and fake model processes. They do **not** prove live model
reasoning quality, live activation, real external exactly-once execution, or a
long-running user's full workflow. The prior audit's 13 probes were diagnosis,
not evidence that this new implementation had shipped.

## Deliberate limits and alternatives rejected

- No second durable task ledger: existing native tasks and promise lifecycle
  already carry identity, ownership and unresolved obligations.
- No global periodic "anything else?" wake. Only material lifecycle/priority
  events and explicitly authored deadlines add review requests.
- No long prompt or compressed private memory reconstruction. Current canonical
  facts supply the resume packet, with named evidence and overflow inspection.
- No automatic reprioritization by noisy failures, inferred urgency or recency.
- No automatic task closure, verification of prose by a boolean heuristic, or
  assumption that a worker's final message finishes the user's request.
- No forced restart or independent scheduler repair. Existing owner handles
  landing safety and activation; this slice preserves that dependency.

Remaining model judgment is explicit: select relevant tasks, turn direct
instructions into maintained task fields, assess evidence, and decide when a
human update is useful. This first slice does not semantically parse every user
correction, validate arbitrary external evidence URLs, propagate every deep
descendant into a root basis, or define a new cross-project priority authority.
The basis includes direct linked children. Existing native authority remains the
security boundary; these convenience verbs and the row source do not grant access.

## Integration and activation handoff

The Board has **Jeff continuity and task ownership** (lead Jeff, explicit urgent
priority) and Rough spots has **Task-linked next steps were missing from resident
continuity**. The task is not marked complete.

The candidate must preserve the prior uncommitted runtime repair dependencies:
house lease, quota policy, plan usage, non-replay `explore` transport, subscription
guard and completion drain, plus their tests. The prepared landing manifest names
exact files and hashes. Unrelated dashboard/launcher/source changes are excluded.
The ordinary `landing.hand` preparer preserves the tested slice and these repair
dependencies on a candidate branch without promoting main, judging in the locked
room or triggering activation. Its exact branch/commit is in the task's final
handoff receipt. The earlier preliminary candidate is superseded by that receipt.

**Integration checkpoint (supersedes the earlier lock-blocker account):**
The orphan transient Git index lock was recovered once at 01:00:23 UTC by a
reversible rename, under the ordinary landing mutex. The queue was empty, the
previously observed Git child had exited, a fresh process snapshot had no Git
processes, and Windows Restart Manager reported zero users of the exact file.
Jeff acknowledged the receipt. No lifetime House lease or active process changed.
`landing.lock` is a per-batch mutex; `house-owner.lock` is the lifetime lease.
The original creating writer remains historically unattributed, which is distinct
from the verified absence of a current resource user at recovery.

The first ordinary full judgment refused publication. Fresh baseline health took
266.8 seconds and reported existing artifact-view, follow-up and host-route
failures. Full candidate health took 286.4 seconds and added two offline fixture
errors. The builder double did not answer the restored subscription auth probe;
the Guard loop double lacked the private directory and owned-loop method required
by the restored lifetime lease. Those doubles are updated without changing runtime
code, removing assertions, bypassing the subscription check, or skipping health.
The isolated Guard suite reports **Ran 20 tests in 1.330s; OK** and the full
offline builder script reports **all passed**. The revised candidate must still
pass ordinary comparative health before publication.

Jeff authorized a bounded quiet window: preserve exact resident `want` values
and worker capacity outside the restarting House, temporarily suppress new dispatch,
let existing turns finish, verify zero active turns and normal Guard admission,
publish, then restore exact values after verified activation or promptly on failure.
The restoration receipt is saved; no settings have been changed yet. The candidate
is judged under normal queue serialization with an additional hold before its
unchanged publication function. No health or authority checks are bypassed.

The normal landing mechanism also has a grace-cut restart path for House files.
Do not promote during active work merely because a candidate is ready. After the
owner confirms safe integration: land the prepared candidate through the normal
queue, verify the code commit, install the editable world verbs, then enable
`next_steps=on` on Jeff's corner and verify the next normal delivery contains the
current task packet. Do not change provider/model/quota routing or wake paused
projects. Off switch: `next_steps=off`.

Implementation, tests, candidate preparation, promotion and activation are
separate states. This report records only the first two as completed until the
landing/activation receipts say otherwise.

## Current handoff after Alex reprioritized integration workflow

At the parent's latest direction, no second harness landing is being launched.
The first judge exited and released its own lock. A separate House-owned landing
for the integration-workflow audit is now being judged; it is not this worker's
process and is not being interrupted. The revised harness, runtime dependencies,
two corrected offline fixtures and this evidence are preserved with the ordinary
hand-candidate preparer. Main promotion, runtime activation, verb installation and
the live continuity opt-in have not occurred.

No quiet-window setting was applied: the restoration receipt has empty changed
and restored lists. All prior settings remain under their existing owners. This
worker is not editing landing.py or health.py. Its only post-review edits are the
two test doubles and its continuity research record. The workflow worker may own
the landing/health path; the parent coordinates the next combined rejudgment and
idle activation after that work. The task is not finished or verified live.


## Observed live results and bounded recovery follow-up

**Ran:** ordinary serialized landing accepted the combined candidate on current main.
Frozen baseline took **236.5 s**, candidate **243.1 s**. Both reported the same three
known failures: artifact-view (11 errors), follow-ups (integration base changed), and
host-route-parent (21 errors). No new failure was introduced; this was not a clean suite.
All seven resident session hashes and queued inboxes survived idle activation. Runtime
source verification preceded world changes; each install receipt has source_verified=true.

**Read:** Jeff's authored comments c12607, c12608 and c12610 confirm the actual normal
task-linked review wake, inspection of nextsteps rows, and distinct review/verification
on the completed delivery audit. Jeff did not independently attest the deployment hashes.
The live projection had 142 inspectable rows; the urgent continuity task was within the
bounded eight-row packet. A received worker result still does not finish its parent.

**Ran:** the HTTP desk, door, and home-base scene answer. After Alex reported the Windows
key no longer opening Agora, the exact idle hidden HUD was refreshed through the existing
identity-checked lifecycle. The replacement is responsive and logged hook installation;
the draft and all observed backend/House/supervisor identities were preserved. Physical
keypress success awaits user observation. The old HUD was responsive but held roughly
11 GB private memory. An exception/block in its toggle path is a hypothesis, not a proven
cause. No simulated input, screenshot, focus action or OBS operation was performed.

Three small follow-up fixes address observed remaining boundaries:

* An applied relay receipt can be staged atomically into the existing delivery path,
  preserving its original journal and identity. Received/applying/ambiguous journals
  remain held. Commands are never replayed. Quota, provider and asleep gates still apply.
* A legacy worker's host process-lifecycle journal can prove its owner stopped after
  restart lost the in-memory process object. Every recorded PID must be positively gone;
  missing/partial evidence, access uncertainty and PID reuse hold. Existing worker leases,
  request recheck and landing serialization still gate a transfer.
* The world review/verify verbs now use the projection's same designated reviewer rule:
  lead, otherwise asker, otherwise owner. A non-lead requester cannot clear a review
  deadline or overwrite a lead attestation while receiving a misleading success.

**Ran:** private regression fixtures report **74 passed, 7 subtests passed in 2.36s**,
covering receipt restart/retry without command execution, ambiguous state preservation,
save failure, asleep/provider gates, stopped/live/unknown legacy ownership, and native
review attribution. Follow-up source must still land and load before claiming those two
live holds resolved. Comment's start-time Node grant is already observed: send receipts
2/2 passed; composer passed six scenarios before reporting two missing fixture inputs.

The module installer's additional read-only gate probe was denied before execution twice.
The second automatic review rejected its POST /api/deploy boundary despite an offline
proof that its sole line was `look a11307 :1`. That action was stopped; modules were not
reinstalled. The core /api/deploy path was independently verified by the actual harness
installation. Selected installer adoption is not universal enforcement of /api/do.


## Recovery activation and overnight continuation - 23 October

This supersedes the pending follow-up language above; historical evidence is retained.

**Ran:** recovery candidate `66a4bc5` landed and activated as `08df1c3`. Comparative
health retained the same three failures, with no new ones; refreshed baseline world
checks took 18.9 seconds and candidate health 234.0 seconds. Source and running-byte
verification passed before updating only the existing task-review/task-verify bodies
(events e34444/e34445). All eight temporary settings were restored; seven resident
identities/inboxes survived. Focused groups printed 74 passed/7 subtests and a separate
74 passed/26 subtests; the 43 passed/10 subtests exit-tail follow-up overlaps earlier
coverage and is not an additional unique-test total.

**Ran/read:** Ibis's retained applied receipt (39,315 characters) and original command
hash matched, its session was preserved, recovery-needed cleared, and subsequent turns
completed. Ibis c12642 acknowledged receipt continuation without saved-command replay.
The supplemental Comment transfer applied its two exact fixture hashes; its original
18-file import was not repeated. Comment source landed as 47d53c8, and Sable applied
paired world hunks. Actual clicking/quoted sending remained unverified at this checkpoint.
Jeff c12655 accepted the scoped continuity evidence in world note a12649, explicitly
excluding universal exactly-once, painted, physical-key and sibling-feature guarantees.

**Ran/read:** the six browser/tiling siblings are now owned together by overnight task
`a12732`, with existing feature owners retained. Drag-stall source landed as 3319834;
packed-grid source landed as bab33e8; backend subsequently reported c60a142. Those are
source/runtime milestones, not painted timing or Board-world activation evidence.
Magnetic reflow was restored through the ordinary asked-state path and prepared as
77d41f4, still default off. Item carry has resumed real implementation; it is unfinished.

Browser's original verifier import was proven applied and ancestral; only the stale
completed request was retired. Its two conflict repairs were reviewed by Rowan, then
committed under the normal worker lease as d7cb13d, preserving parents 3ac1a72 and
09ef253 plus all prior staged work. No native browser execution or ready claim follows.
The exact receipt was supplied to Rowan; native interpreter inventory remains unapproved.

**Ran:** panel activation's old startup diagnostic could not attribute the cause because
it discarded child output. Its worker's exact retained-directory listing was denied
(OS error 5) and was not retried. A fresh, separately owned paired diagnostic used exact
parent6f6cc7 and candidatea73b1a3 source, synthetic worlds/free loopback ports, existing
child lifetime pipes and retained output. All nine acceptance ASTs and instrumentation
hashes matched. Parent: 143 gestures, one missing, no duplicates/errors, 8/9 checks pass,
26.487 seconds. Candidate: 144 gestures, all nine pass,26.016 seconds. Both completed;
all fourteen recorded listeners closed and four recorded door launcher PIDs were absent.
This is bounded cleanup evidence, not continuous descendant containment certification.
The candidate tree equals worker/a9352. Fresh evidence is world note a12796; it supports
ordinary source review while keeping the intermittent baseline defect visible. It does
not explain the old timeout or prove the defect eliminated.

No production diagnostic patch, live test message, screenshot, simulated input, focus
change, OBS action, forced lease or new credential was used. Physical Windows-key
confirmation remains pending with Alex. The module-wrapper gate-only probe remains
stopped after the recorded denial; no new attempt or module reinstall occurred.

Exact private receipts are under Documents/Codex/2026-10-22/task-3/continuity;
readable world notes a12649/a12796 and the overnight task contain the user-facing facts.
This continuation is unfinished until the existing feature owners supply actual remaining
native/painted/world-activation evidence or a precise unresolved authorization decision.


### Paint handoff natural-exit correction

**Read:** the existing Claude paint acceptance worker a11403 has a delivered pending
message whose matching-session successful terminal result was recorded after last_sent,
followed by host-recorded exit code0. Its completion was not drained into state. This is
distinct from the prior Ibis relay receipt and Comment transfer; those are already resolved.

The existing ownership check recognized explicit stop but not this natural exit. The
narrow source correction recognizes an integer-code exit of the latest recorded start
PID, still requiring every recorded PID positively absent. A stale/wrong PID, missing
exit code, later start, live PID or uncertain absence stays held. This does not consume
pending delivery, review a result, waive a worker lease or bypass landing serialization.
Existing interrupted-delivery recovery will preserve the already-delivered input for
same-session continuation without replay before the original transfer is retried.

**Ran:** affected lifecycle/preserved-transfer tests:57 passed,30 subtests passed in
129.26s. Whitespace clean. Exact main/current lint comparison:551 existing workshop
diagnostics on each side, zero added; transfer test file has no lint diagnostics.
At this source checkpoint, correction is tested but not yet landed/loaded. Native paint
and its empty remote allowlist remain unchanged; no attempt was repeated.
