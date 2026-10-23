# Quiet task transitions — staged review

Author: worker-a10692, codex-builder-1, 22 October 2026, continuing
builder-2's preserved metadata audit and inactive candidate.

No production file or live policy changed. Do not mark ready or land this
directory as an activation request. Ibis must review the source and policy first.
`stage.py` generates a patch; it does not apply it.

## Read and measured

Read task_flow.py, House.news/Resident.save, rooms.reached, workshop.HOUSE_FILES,
the card/comments, live charter, collaboration guide and notification topic.
The preserved audit in c10750 used read-only archived snapshots; this round
did not recapture sessions or query private prose.

Fixed interval e26500–e27216 (08:46–09:09): 718 records, including duplicate
e27152; previous audit resolved all task snapshots, with zero missing.
Fixture raw SHA256:
`d0144ceb41225764a412b60ef1ed6d7ac4090e3c3023390bccc3960889a6da42`.
Opaque blocker/summary/evidence values are hashes, not message prose.

Ran replay.py against the same fixture:

| Result | Legacy | Candidate |
|---|---:|---:|
| Transition recipient notices | 13 | 9 |
| Other routed events | 48 | 50 |

Six bare waiting notices disappear: e26773, e26816, e26856, e26866,
e27012, e27042. Two previously omitted landed notices appear: e26647 to
Juniper and e27153 to JEFF. Four ready events, two blocker episodes and
the resolver reassignment remain. Reworded checkpoint/blocked reasons
are removed from the same notice rather than causing another wake.

The two other-route changes are house comments e27156/e27157 now reaching
their explicit Sable/Pike recipients. No previously routed other event
disappears in the captured comparison. Those other-route results were
captured using the actual candidate rooms.reached on the same loaded copy;
the offline replay validates transition routes from captured snapshots,
and reports the captured other-route comparison. It does not reconstruct
comment prose or independently replay all comment routing from metadata.

There are zero mark=ask events in this interval. Question/permission preservation
therefore relies on isolated routing tests, not the interval. Six human-route
events are recorded. a8735 has no transition here; no measured wake frequency
or token/model-turn savings is claimed.

## Candidate semantics

One versioned, enabled world policy note selects allowed state/milestone values.
Absent, unsupported or ambiguous policy preserves legacy behavior.
World-authored states: ready, landed, failed, done; milestones: completed, failed.
Owner assignment and explicit owner acceptance remain unchanged.

Blocker notices require both blocked_on and blocker_owner, plus a change to
blocked_on/blocker_owner/resume_when or lead/asked_by. No semantic inference
from prose: a changed blocker string is treated as a material contract change.
Repeated waiting/checkpoint text alone is quiet. An incomplete blocker is quiet
on this transition route; a real question can still reach the lead.

Implicit task comment destination is lead, then asked_by, rather than containing
corner. Explicit addresses still win. Questions, human input, native mentions
and world dependency-clearance comments retain their separate routes. Transition
lead attribution uses event snapshots. Existing comment routing reads the current
task destination; this patch does not introduce historical comment snapshots.

Queue deduplication uses task identity + recipient + reason with the native event
as its high-water mark, stored in task_notice_receipts beside inbox and cursor.
Duplicate/older passes are suppressed; a genuinely new native action or different
resolver is eligible. Receipt means queued input, never provider delivery,
model receipt, acknowledgement or task acceptance.

House.news saves the index/inbox/cursor in one Resident.save file replacement.
A failed replace propagates; reloading durable state then gathering again queues
one notice. No provider call is made here. No code reads or retries unknown
provider deliveries. Existing broader provider retry/recovery behavior is outside
this patch and is not certified by these tests (voice-safety work is separate).
No claim of power-loss durability or all-house exactly-once delivery.

## Ran

Pinned interpreter:
`C:/Projects/Agora4/.venv/Scripts/python.exe`

- `research/task-wakes/test_candidate.py`: 16 tests, OK, 0.527 s.
  Actual in-memory engine mutations and House.news; repeated waiting,
  question while waiting, explicit recipient, Alex permission recipient,
  material blocker/new resolver, ready/landed/failed/done, milestone rewording,
  duplicate records/restart/rewound cursor, preserved unknown pending delivery,
  dependency rules for landed and done, event-time reassignment, absent/invalid/
  ambiguous policy, undone events and independent recipient receipts.
  Real Resident.save exercised on a fixture-owned file, including replacement
  failure and reload. No live world saved or resident/model run.
- `research/task-wakes/replay.py`: counts above; all captured old/new transition
  route assertions pass.
- `research/task-wakes/stage.py`: reproduced identical normalized patch and
  candidate output hashes; added explicit raw hashes to manifest.
- `git diff --stat`: no tracked production edits.

An added permission test first failed because its synthetic world did not know
Alex. It was corrected by registering the fixture Desktop person=alex through
the engine; the final 16-test result includes that case. No production routing
correction was needed for it.

Not run: full health, runtime activation, real wakes, model calls, browser,
Conversation writes or deployment. No visual product changes.

## Exact bytes and deployment boundary

All hashes in manifest.json distinguish normalized LF source/output and raw
file bytes. Patch normalized SHA256:
`52c3eca60b213d52789a29196b2ec6e9456fc23cfe935cc417d8491bcc8564db`.
Raw patch (CRLF on this checkout):
`ff3323ba3ba8515f7c92c9c1b2885a7a228de656c7000d0a0a7b9670b544c714`.

Candidate outputs, normalized LF:
- task_flow.py: e398cc6a6d49cd1eeb20165333de74b22f9673cc8743012e774c95e35d655dff
- house.py: 22704ff4558219676313c275f924bafb0e45da9d05ae8bf8497dc971bd81eaaf
- rooms.py: 40a3211cae0f76b9cfa642deae61abe32d18062d3929b158f48d9c656a95083b

house.py and task_flow.py are HOUSE_FILES: applying the candidate would have a
house lifecycle consequence. This card has no landing/deployment approval yet.
Do not use ready as a synchronization request. At approved integration, check
all bases against current main and rerun candidate/integration tests; stop on
drift. No application, restart or live test wake is authorized by this receipt.
Exact world policy staging and inverse: WORLD-POLICY.md.
