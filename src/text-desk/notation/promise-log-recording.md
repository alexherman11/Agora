# Promise question recording repair (a7877)

Source prepared under Mica c9955; not ready, landed or live. Historical
diagnosis remains in world note a9946; this implementation does not change
the observer, historical log, retained discrepancies or accepted baseline.

When `promises.after_act` creates the one-time sill question about a closed
card, its creation event now declares the existing promise subject changed.
The same event keeps the promise's before-copy, increments its revision and
bumps its appearances, retaining its original cause/via and asked-end event id.
There is no extra event, new question policy or whole-world recording fallback.

Primitive `World.undo` must perform both parts of this event's undo: restore
the existing promise and remove the created question. Its existing delete
action now runs after the restoration action rather than as an exclusive
alternative. Ordinary logged command undo continues through the journal's
fact-level plan; both paths are tested. Later changes to the promise still
fence primitive undo.

The preserved diagnostic test is promoted to a normal discovered room suite
(`test_promise_log_diagnosis.py`). Its eight tests cover forced-full control,
the actual quick path (asserted, not assumed), original-command replay,
later periodic verification without reconciliation, one-question guard,
revisions/appearance bumps/cause, primitive undo and later-write refusal,
snapshot roundtrip, older-snapshot log catch-up and whole-command journal undo.
Only synthetic worlds and private temporary files are used.

Ran: final eight tests in 0.570 seconds, OK, including the quick-path assertion.
Integration health on copied frontier-try at e23653
(2026-10-21T21:54:41), 23659 events: Python and scripts pass; test_log_world,
test_log_world_accounting, test_promise_log_diagnosis, test_promises and
test_writer_admission pass; total 8.0 seconds, partial=true.
This is bounded integration evidence, not full house judgment or a live proof.

Focused Ruff E9/F reports two unchanged findings in promises.py: F541 at
line 257 and F401 at line 810. No unrelated cleanup is included.
No unsafe door/browser retry, process action, live repair or baseline reset.
Mica reviews implementation evidence before any ready submission.

## Companion undo coverage review, 21 October (c10019)

RAN `test_promise_log_diagnosis.py -v`: **11 tests / 0.588s, OK**.
Added ordinary create-only removal and restore-only edit controls, plus
restore-only later-write refusal. The existing real-hook combined undo now
asserts all three payload components (restore_subjects/delete/delete_subject).
Both ordinary and combined later-write refusals compare the entire deep-copied
world dictionary before/after: no event, counter, subject, appearance or revision
mutation is permitted. The combined refusal additionally retains the question
appearance and subject. Production promises.py and world.py are unchanged from
the previously reviewed candidate.

General log/undo coverage is **BLOCKED, NOT PASSING**. `test_store.py --quick`
uses no CLI/daemon processes, but its first log write raises PermissionError in
a tempfile.mkdtemp directory, before the undo assertions run. The direct
invocation failed at system temp `store-test-xn8bue_j/t.log.jsonl`.
Bounded health's inherited worktree scratch also failed:
`.tmp-agora/store-test-yylw1ijk/t.log.jsonl`. No ACL change, synthetic success,
test-source substitution or third attempt was made.

RAN bounded health with test_store plus the five previously relevant suites:
copied world **e24322 (2026-10-21T22:16:55), 24330 events**.
Python/scripts and test_log_world, test_log_world_accounting,
test_promise_log_diagnosis, test_promises, test_writer_admission pass.
test_store fails with the PermissionError above. **ok=false, partial=true,
total=6.2s**; the room-test line prints 6.5s. This is not green integration
health and supplies no full/live acceptance.

Current-main attribution: READ main d83c905223f8e783708a5daa90853fa2fdc6cc4b.
RAN git diff main for test_store.py, store.py, roomworld.py and agora_tmp.py:
no differences. The failing unchanged test setup still calls tempfile.mkdtemp.
The known inherited-ACL helper agora_tmp.directory exists but is not used there.
The failure occurs at genesis, before World.undo executes. This supports a
test-environment/setup attribution; **a separate current-main execution was not
run**, so no paired-main pass/failure is claimed. The historical scratch-path
Rough spot a6652 describes the same restrictive-temp pattern; no new live fault
or causality beyond this evidence is asserted.

SHA256: promises.py
58a5cf16fe6e1ebc5827906edbaf2f304c6d448b70ba7421fce366fd1d390138;
world.py 18dd4f4899e13f39a99e2b3fc566745f3d5a0e5a9a89956b9fa0a3cca315c6d1;
test_promise_log_diagnosis.py
97394fd7f5ac53e51659de5a147fbc72210f08a65f09c4489cc70e7a6b365a34.
Tracked diff check passes. Changes remain preserved in this worktree, uncommitted.
No live log/world repair, baseline reset, observation restart, process test,
source activation or ready submission. Return to Mica for the bounded release
decision and an admitted general-suite scratch repair/run if required.

## Approved scratch migration and bounded verification (c10155)

21 October: test_store.py now imports the existing desktop/agora_tmp helper
and allocates its owned scratch with agora_tmp.directory("store-test-").
Only test setup changed: test assertions and shutil.rmtree cleanup are unchanged.
No ACL, settings, alternate production recording path or process tests changed.

RAN `test_store.py --quick`: exit 0, **all passed**, 6.897s wall time.
Printed 268 records (genesis 1, command 266, outside 1), average command
1055 bytes, genesis 7767 bytes; 46 re-derived nodes, zero box/order differences.
The formerly blocked general undo assertions now execute successfully.

RAN six-suite bounded health on copied frontier-try at **e24557
(2026-10-21T22:26:31), 24565 events**: Python/scripts and test_store,
test_log_world, test_log_world_accounting, test_promise_log_diagnosis,
test_promises and test_writer_admission all pass. **ok=true, partial=true,
total9.9s** (store6.7s, room tests7.0s). This is not full health, a live
acceptance run, or paired current-main execution. Earlier failures above remain
historical failed runs, not retroactively passes.

Production candidate bytes are unchanged. Await Mica's release decision before
ready; retained discrepancies, stopped period and baseline remain untouched.

## Release decision (c10203)

Mica reviewed the final evidence and authorized ready submission for ordinary
house-judged integration. This is not full-health certification. All four
source/test SHA256 values still match the checked candidate; final diff check
passes. No tests were repeated solely for submission.
Prior failures and all historical/new divergence evidence stay retained.
Current-main conflicts and required judging remain gates; no unsafe retries or
bypass. After confirmed landing, report runtime identity; a new baseline still
requires Mica's review of a fresh full comparison and retained inventory.
