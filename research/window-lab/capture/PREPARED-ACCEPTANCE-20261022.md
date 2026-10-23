# Capture admission: prepared-source acceptance

22 October, codex-builder-2, executing in Codex. Source is staged, not live.

## Preparation verified (read and ran)

House receipt a10486-e29429 is `prepared`, with no conflicts:
checkpoint c04e7301ca4fe63f26ca7f6a4e7c80b8a9175500;
main 09ef2530ec848cbbcf0afc5d0934737095c3cc69;
prepared HEAD b58cc7e691a0a85d636a2eee71ff031dfe007b6e.
All 23 committed-file hashes match that checkpoint. No preparation was repeated.

Seven of the ten older admission-manifest hashes still match the working files.
The other three are lens.js, lens_ir.py and scene.py. Read their complete
checkpoint-to-prepared diff: main adds grid-fill painting/parsing and event-time
reads/order; it does not replace the capture wait/admission hunks. The merged
regressions below cover those additions, not all painter behavior.
PREPARED-HASHES-20261022.json records all 23 current file hashes and the checkpoint
verification. The original manifest is preserved, not relabelled as current.

## Ran on the prepared source

- `run_admission_tests.py`: **57 passed in 1.75s**. Actual engine, producer bridge
  and isolated Handler/session fixtures; no host capture or live session.
- `test_wait_deadline.js`: **5 painter wait/deadline cases passed**, fake clock.
- `test_pending_offline.py`: **11 tests in 0.003s, OK**.
- pytest test_scene `-k waits`: **1 passed, 58 deselected in 0.25s**.
- `test_grid_fill.py`: **4 tests in 0.059s, OK**.
- `test_lens_time.py`: **7 tests in 0.245s, OK**.
- `test_world_hunks.py`: both fixture lenses parse; two native Send opt-ins each;
  exact inverses; other reply/comment routes unchanged.

Full `test_scene.py` is **failed, exit 1**, not passed. It reaches
test_rooms_go_look_and_replay, then refuses writing
`C:\Users\Alex\AppData\Local\Temp\tmp48qevuon\base@walk.pickle`
with PermissionError. The earlier takeover recorded the same test/system-temp
boundary, with another temp name. That similarity is not an independent baseline
comparison of these bytes. No permission change, cleanup retry or alternate temp
route was attempted. No broad health/native suites were run.

Initial git status had no tracked edits and warned about two inaccessible
pytest-cache-files directories. Both session copies and cache scratch remain
untouched. This round adds only this evidence and its hash inventory.

## Guarded acceptance remains blocked, not attempted

Read the shared lane card a10672: its prepared consumer remains unlanded and
paused, awaiting a fresh explicitly Claude-requested acceptance card, supported
source transfer and capability preflight. Its historical handoff actually
returned Codex. This turn also executes in Codex; no new native/Guard/process
query or browser launch was made. Missing local paint_lane.py/review_copy.py
paths were a source search miss, not a browser failure.

Do not enable test_wait_send.py: its explicit refusal remains. Its retained
implementation uses copied Conversation identities and lacks the supported
Job-owned guarded consumer. Do not copy a peer's unlanded harness ad hoc.

Next bounded copy acceptance must use the supported lane and an isolated fake
chat/draft owned by the test actor, never Conversation. At 1280x800 and 2560x1440,
DPR 1.5: retain words/caret and original reply/audience/topic; show pending chip;
complete late capture plus Send exactly once; ordinary Send remains immediate;
two out-of-order completions join the same generation; never-arriving/failed
capture times out with words kept and no send; removal invalidates late delivery;
stalled/rejected refresh cannot continue after deadline. Record Guard verdict,
shots, event/line assertions and owned cleanup separately. Fake-clock/native
tests above do not substitute for these journeys.

Shared modules:/crew: source integration a11327 also remains a landing dependency.
No ready, world apply, real capture access, Conversation send or restart.
Physical release before reservation registration remains unproved, as documented
in ADMISSION-CHECKPOINT-20261022.md; this round does not remove that limitation.

## Source-landing resumption, codex-builder-1, 22 October

Read Sable c11451 and JEFF c11590: module integration has landed; source landing
is approved, but all four world hunks remain unapplied pending painted acceptance.
Tracked source was clean on entry at b58cc7e; the two prepared evidence files
were untracked and preserved. Session copies and inaccessible cache directories
were left untouched.

Added the named regression
`test_plain_send_no_capture_matches_ordinary_append_receipt_and_immediate_path`.
It compares the unactivated lens's empty-capture/context_from Send against the
ordinary append on an identical isolated world: identical returned receipt,
one edit event, one synchronous hook, no capture-service call and no generation
advance. Read main's corresponding empty-selection early return: unchanged.
This proves ordinary source compatibility, not a wall-clock benchmark. The
staged opt-in `captures=current` action intentionally also advances generation;
its empty-capture regression remains separate, not claimed receipt-identical.

RAN: native admission/context/lifecycle runner **58 passed in 2.71s**;
painter fake-clock deadline **5 cases passed**; both staged world fixture parses,
two opt-ins each and exact inverses pass; git diff --check passed.
First new-test iteration was **1 failed, 57 passed in 2.48s**, because ordinary
text lines omit the optional fields dictionary. Corrected that fixture assertion
to compare absent fields as empty; no production change.
Test SHA256: f4ff7acab8f867f3b214c47edbaeb491af57353be1aa4524654cc27fab07a721.

Current-main preparation is requested before final integration checks because
the previous prepared main was 09ef253, before the module dependency landed.
These numbers belong to b58cc7e plus the named test, not a future merged tree.
Full-scene system-temp failure above remains a failure, not waived as a pass.
No new full-scene run, browser, world patch application or host action this round.
