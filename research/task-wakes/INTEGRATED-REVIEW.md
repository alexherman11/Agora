# Quiet task wakes: prepared integration, not deployment

Worker-a10692 / codex-builder-1, 22 October. Ibis c10796 authorizes bounded
integration only. Live policy remains untouched. No ready, landing or restart.

## Bases and exact scope

Read the actual prepare receipt on the card (c10989 inventory; c10992 completed):
main `09ef2530ec848cbbcf0afc5d0934737095c3cc69`, prepared HEAD
`98627ab4274c3bbd31a5f19af4da51065f266929`, checkpoint
`1fb14a68426824d3ebd0dbf98346ab3f48caab6b`. No conflict.

Ran `integrate.py`: all ten preserved artifacts equal the checkpoint's committed
blobs after CRLF normalization. The original artifacts are unchanged. Verified
the old bases and outputs against the reviewed manifest, then compared every
insert/delete group against the prepared sources. All twelve groups are
identical; only surrounding main code changed. Resulting unified patch is
byte-identical to the reviewed normalized patch:

`52c3eca60b213d52789a29196b2ec6e9456fc23cfe935cc417d8491bcc8564db`.

Integrated output SHA256:

| File | Output |
| --- | --- |
| task_flow.py | e398cc6a6d49cd1eeb20165333de74b22f9673cc8743012e774c95e35d655dff |
| house.py | 93bd5b3300c5ee792176d2c6272b0bcf3c07a1ee4953161ea98e2250120719f8 |
| rooms.py | 40a3211cae0f76b9cfa642deae61abe32d18062d3929b158f48d9c656a95083b |

The only changed House/Resident method AST is `House.news`. No change to
send/recovery/portable input, restart, timed rest, `House.run` or guard-sampler
lifecycle. This preserves prepared main; it does not certify unlanded voice
safety in another branch. Base/output hashes and inventory are in
`integration-manifest.json`; `integration.patch` is reversible only against its
exact outputs. Reconcile future changes instead of restoring whole files.

## Executed checks

Pinned interpreter throughout.

- `run_integration.py`: **46 tests, zero failures/errors, 1.893s**. Imports
  actual production paths, not generated candidate modules. Runs the original
  sixteen candidate cases plus restart/timed-rest tests and a new policy-off
  full-state comparison. The comparison checks absent/off policy, three
  recipients, awake/resting (12 comparisons), multiple transitions and explicit
  and implicit questions against baseline House.news. Urgency, inbox, cursor,
  held/knock state and unknown pending match exactly.
- The original real-save test uses actual `Resident.save` and failed
  `os.replace`, verifies unchanged durable bytes, reloads, queues the actionable
  notice, reloads again, then rewinds the cursor. Receipt/inbox stay together:
  exactly one queued notice, unknown pending unchanged. No provider is invoked.
  This proves the tested process-restart/atomic-replace boundary, not power-loss
  durability or provider acknowledgement.
- Captured replay rerun against imported integrated task_flow: **718 records,
  13 old versus 9 new transition notices**, exactly the original expected
  changes. Six bare waiting notices suppressed, two landed notices added.
  Other-route 48→50 is the preserved earlier captured route comparison, not a
  fresh comment-prose replay. No questions exist in this interval; synthetic
  tests cover them. No token/model-turn savings claim.
- Eight-suite fake transport/integration: **83 passed, 1 failed**, 4.37s.
  Frozen prepared baseline: **83 passed, 1 failed**, 4.20s. Both fail
  `test_archived_native_props_keep_assignment_and_milestone_recipients`:
  TemporaryDirectory owner-only Windows ACL prevents SQLite opening the fixture,
  then cleanup is denied. This test remains failed, not excused as passed.
  Pytest tmp_path uses inherited-ACL owned scratch in this runner; the test's
  internal TemporaryDirectory is unchanged. Cache permission warnings retained.
- `git diff --check`: passes.

Full health ran without `--only`, `--fail-fast` or excuses. **Exit 1,
221.2s printed total (222.266s wrapper), 18 failed checks**. Its world witness
was **e27361 (2026-10-22T13:01:52), 27368 events**, on the disposable -try copy,
not a live-world claim. `partial=false`, `stopped=false`. Python/scripts passed;
103 lenses compiled, zero unexpected refusals, one expected; 95 help notes true.
Compilation is not painted acceptance.

Failed check names, retained exactly:

```
test_agent_reach test_artifact_view test_captures test_door test_followups
test_host_route_parent test_lived test_peek_paint test_reach test_room_look
test_scene test_scripts_mirror test_task_flow test_textedit test_textedit_paint
test_visit test_witnessed test_worker_yield
```

Direct error messages include denied Windows temporary paths; door no answer
within 60s; visit owned fixture cleanup denied; textedit lock unavailable after
60s; paint no-answer/assertion; four reach assertions; and fixture error counts
for artifact_view/host_route_parent/worker_yield. Do not label these green or
assume every failure is environmental. A full baseline-health comparison was
not run; these 18 are **not all independently attributed to main**.

Narrowly established attribution: the archived task-flow failure reproduces on
the prepared baseline in the eight-suite comparison. Also read
followups/integration.json: its frozen expected House hash is
`40b9a40364d3f4777226945e4469417336853b2bb4498033f1376034c8f36bd2`,
already different from prepared main `9ec463f3...` and integrated `93bd5b33...`.
Its guard necessarily refuses either base; this is a read/hash inference, not a
passing followups suite or authorization to change that guard.

Full output/JSON is in `health.log`; wrapper command/result in
`health-result.json`. The standard health runner includes hidden paint/fixture
subprocesses. They failed as recorded; no screenshot or browser success claim,
no manual retry/cleanup or native-screen interaction. The initial mistaken
knock-script import and the standard health checks both operate on disposable
test worlds; no results establish live wake delivery or policy activation.

The eight suites are house conversation flow, resident delivery handoff,
resident portable, conversation queue, charter, notice routing, task flow and
task-flow verbs. Logs and exact commands are retained in `integrated.log`,
`baseline.log`, their result JSON files, `integration-tests.log` and
`integration-replay.log`.

One erroneous first runner imported `test_knock.py` as though it were a
unittest module. It executes a stand-in House against the disposable -try world
at import time, emits numerous passing checks, then fails `KeyError: 'cause'`
in its final knock uniqueness assertion. It never reached the intended suite.
This is not a passing integration or an attributed main failure. Corrected the
runner to import only actual unittest modules and reran successfully. No live
model, Conversation or real world was used. No manual cleanup of denied scratch.

## Policy and lifecycle boundaries

`WORLD-POLICY.md` remains the exact staged policy and inverse; no policy creation
or enable act was executed. Absent/off/unsupported/ambiguous policy is legacy.
Do not rewind live cursors, clear inboxes or replay unknown provider deliveries.
Receipt means queued, not read, delivered or accepted. Existing dependency rules,
explicit recipients and direct human input have independent retained routes.

house.py and task_flow.py are HOUSE_FILES. **Do not ready/land this checkout**:
ordinary landing has a deployment/restart consequence. Ibis reviews this
evidence and health disposition first, with concurrent voice changes reconciled
at any subsequent preparation. No live test wakes, activation, browser evidence,
model calls or new policy scope.

All new research files are evidence/runners, not deployable services. The
copied world and automatically created session/test scratch are excluded from
source preservation; inaccessible temp paths remain for supported cleanup.
