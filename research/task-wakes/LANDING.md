# Quiet task wakes: source landing, policy absent

## Dependency landing recheck, 22 October

Module/crew integration f925b0a has landed. The three production candidate
hashes still match integration-manifest.json, and current main's corresponding
base blobs match that manifest too: no intervening edits to reconcile in
house.py, rooms.py or task_flow.py. The house remains responsible for the
serialized final merge and judging; this is not a merged-result claim.

Fresh bounded offline run: 46 tests, 0 failures, 0 errors; captured replay
718 records, 13 old / 9 new notices. Reports are retained separately under
dependency-revalidation/. Policy-off parity and failed-save/reload checks are
included. Desk query finds no task-transition-policy note. No activation,
test wakes, native launch, broad health rerun or cleanup was performed.
The historical 18 health failures below remain unresolved except where
explicit baseline evidence already exists; none is silently waived.

The following original assessment is retained as historical evidence.

22 October 2026; codex-builder-2 / worker-a10692. Ibis c11265 supersedes
the old no-ready/combined-voice gates in INTEGRATED-REVIEW.md. Ordinary house
judging is authorized; policy activation is not.

**Recommendation: source ready for ordinary judging.** No candidate-specific
regression or new ownership/base conflict was found in this bounded recheck.
This does not waive the recorded health failures or certify unrelated voice bytes.

Read: current main remains `09ef2530ec848cbbcf0afc5d0934737095c3cc69`;
prepared HEAD remains `98627ab4274c3bbd31a5f19af4da51065f266929`.
Ran `revalidate_landing.py`: all ten original artifacts match, all three
production outputs/base snapshots match the reviewed manifest, and the twelve
edit groups remain exact. Among House/Resident methods, only House.news changes.
No send/recovery, sampler, restart or timed-rest implementation is changed.

| Production file | Exact SHA256 |
| --- | --- |
| task_flow.py | e398cc6a6d49cd1eeb20165333de74b22f9673cc8743012e774c95e35d655dff |
| house.py | 93bd5b3300c5ee792176d2c6272b0bcf3c07a1ee4953161ea98e2250120719f8 |
| rooms.py | 40a3211cae0f76b9cfa642deae61abe32d18062d3929b158f48d9c656a95083b |

The integrated patch remains
`52c3eca60b213d52789a29196b2ec6e9456fc23cfe935cc417d8491bcc8564db`.
`integration-manifest.json` contains exact bases and outputs. Source inverse is
`integration.patch` reversed, only after checking these outputs; intervening
changes require hunk reconciliation, never a whole-file restore. World inverse
is the staged `enabled=off` operation in WORLD-POLICY.md. Preserve existing
inboxes, cursors, queue receipts and unknown provider outcomes.

Ran: **46 tests, 0 failures, 0 errors, 2.044s** against actual production imports.
Includes the real failed-replace/save/reload boundary, restart/timed-rest
regressions, and twelve policy-absent/off full-state comparisons. Same captured
interval e26500–e27216: **718 records, 13 old / 9 new** transition notices.
Queue receipts are not provider acknowledgement; no live test wakes or model
turns were made. Detailed new logs: `landing-revalidation-final/`.

The first revalidation wrapper incorrectly changed the runner's fixture lookup
directory when separating output logs: 46 tests ran, 0 assertion failures,
1 missing-baseline-file error. Preserved in `landing-revalidation/`. Fixed only
the report sink (`OUTPUT` separate from `HERE`), then reran the same tests.
Original integration/health/baseline logs remain intact.

The prior broad comparison remains **83/84 on both candidate and captured
baseline**, sharing the archive-fixture temporary-directory failure.
The prior full health remains **18 failed checks**, not all proven baseline:
test_agent_reach, test_artifact_view, test_captures, test_door, test_followups,
test_host_route_parent, test_lived, test_peek_paint, test_reach, test_room_look,
test_scene, test_scripts_mirror, test_task_flow, test_textedit,
test_textedit_paint, test_visit, test_witnessed, test_worker_yield.
See unchanged health.log/health-result.json and INTEGRATED-REVIEW.md for exact
details and the disposable world witness e27361 / 27368 events.
No broad health or native check was rerun; no claims borrowed from voice tests.

Source inventory: precisely three production paths above; original staged
candidate/capture/policy artifacts and necessary offline runners, baseline
snapshots and evidence under research/task-wakes. Additional bookkeeping:
root `.gitignore` ignores only `/pytest-cache-files-*/`, alongside the existing
pytest cache ignore. Four inaccessible generated cache directories previously
caused Git traversal warnings; they were not opened, changed or deleted.
After exclusion Git status has no cache traversal warnings. Session copies
remain excluded by the house's documented sessions path exclusion.

Read-only Desk query at this checkpoint: no task-transition-policy note exists.
Thus the new routing and queue-receipt behavior is **off**; absent, disabled,
unsupported or ambiguous policy retains legacy behavior. The shared news/reached
paths still execute policy lookups, so this is a conditional runtime extension,
not wholly inert code. Policy-off state parity was tested, not performance.
No policy create/enable, old notice deletion, live cursor rewind, Conversation
send, browser/native launch, host restart or cleanup retry was performed.

House owns the final commit/merge/judging. Its result, not this recommendation,
determines landing. Ibis/JEFF retain the separate world-policy activation gate.
