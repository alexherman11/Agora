# Baseline source: bounded release review, 21 October 2026

Prepared by worker-a7877 for Mica's decision under c9399. **Release review
accepted for submission in c9450; not landed, no accepted live baseline and
no observation-clock reset.** The original review below is retained as evidence.

## Submission authorization

Mica c9450 (event e22177) reviewed this report and authorized ready for ordinary
house-judged integration, accepting the named coverage uncertainty under
JEFF c9385 without certifying full health. Current-main conflicts and required
checks remain gates; no forced landing, skipped check or pass relabelling.
Do not repeat unsafe door/browser launches. If judging requires that route,
stop and report the exact blocker. After landing, verify deployed runtime and
obtain a NEW exact full comparison before a documented baseline; any new
discrepancy stops acceptance. Submission does not start observation.

## Current decision boundary

Read the complete commission/comments and preserved source diff. JEFF c9385,
confirmed by Mica c9399, supersedes the earlier lifecycle blocker: ordinary
judged landing, including the automatic Desk swap, is allowed under Alex's
standing rule unless something important would break. Mica still explicitly
requires this health/risk review **before ready**. This report requests that
decision; it is not deployment approval.

Implementation remains the preserved uncommitted changes in `log_world.py`,
`test_log_world.py` and the `desk.py` help synopsis. No implementation changes
were made in this review. Branch HEAD is e7f8cb5; the main reference read in
this round is 28c897ecb632948651d6cd5690750c6f267bc251. No merge was attempted.

## Ran now

| Check | Printed result |
| --- | --- |
| `test_log_world.py` | 42 tests, 3.378s, OK |
| `test_writer_admission.py` | 11 tests, 0.877s, OK |
| `test_log_world_accounting.py` | 5 tests, 0.001s, OK |
| `git diff --check` | exit 0, no output |

These use synthetic engine/log worlds; they do not establish full health,
current-main integration, live startup, painter behavior or two observed days.
Live `log-world status` reported checked endpoint e22129 at
2026-10-21T19:40:53-07:00, still diverged at the historical e15972.
This was not a fresh full comparison, and did not establish today's complete
discrepancy inventory.

## Preserved paired failures: attributed, still failures

Read all six JSON receipts under
`.agora-tmp/baseline-main-health/*-test_*.py.json`.
They compare unchanged exported main **2637cdd**, not today's main.

| Failure | Main / branch | Behavior still not proved |
| --- | --- | --- |
| `test_reach.py` | Both exit 1; same four empty-row failures | Refusal grouping and reaches rows. Same failure does not diagnose its cause. |
| `test_textedit.py` | Both exit 1; same lock refusal | Whole-text editing suite did not start successfully. |
| `test_visit.py` | Both exit 1; WinError 5 creating scratch `trees` | Visit/home across versions was not exercised; failure occurred before door startup. |

These receipts support the historical attribution accepted by JEFF/Mica.
They are neither passes nor evidence that current main has identical failures.

## Remaining unknowns and release risks

| Unattributed failure | Evidence and affected behavior | Release risk / safe next route |
| --- | --- | --- |
| Other temporary-directory PermissionErrors from the old full-health run | The retained checkpoint reports multiple failures, but does not preserve a complete per-test list/traceback here. Their identities, count and causes remain unknown. Generic scratch storage prevented some checks from reaching the behavior they were meant to test. | Cannot certify those suites or assume all temp failures have the same cause as visit. A capable admitted paired health run must retain individual failures and revisions. No ACL/settings changes or tempfile substitution were attempted. |
| `test_door.py`: no answer within 60 seconds | Read its startup/cleanup source. `start_door()` creates local `p`, returning it only after health responds. On timeout it raises before the caller assigns `door`; the finalizer then has no handle to that child. The old failure's cause and whether a child survived remain unknown. The test covers swaps, rejected swaps, gesture/event continuity and persisted door news. | Ordinary landing automatically swaps Desk, so this is directly relevant availability/continuity risk. No new launch or process cleanup attempted. A paired run needs admitted ownership and guaranteed child cleanup even on startup failure, on synthetic worlds only. No such route is currently evidenced for this worker. |
| Painter failures from old full health | Current suite inventory contains `test_peek_paint.py` and `test_textedit_paint.py`; read both. They cover folded-content visibility and continuous-edit/composer continuity, composition, conflicts and undo. The checkpoint does not identify each original failed painter assertion or whether failure preceded browser startup. | Visual/interaction regression remains unverified, including editing continuity around Desk updates. No painter source is changed by this patch, which limits direct scope but does not prove no integration regression. Requires an admitted guarded hidden-browser paired run; no known-denied browser attempt was repeated. |

This explicitly retains unknown membership of the generic-temp and historical
painter failures; it does not invent a complete original failure inventory.
No safe admitted paired door/painter route was supplied with this resumption.
Mica may request that route or decide whether to proceed with the named risks
under c9399. Full health remains **failed/unverified**, never relabelled passed.

## Baseline and release sequence after review

1. Mica reviews these remaining unknowns and chooses whether source may become
   ready, or specifies an admitted paired verification route. Until then the
   preserved source stays held.
2. If approved, ordinary house-judged integration must resolve any conflicts
   against newer main and retain its actual health result. A failed merge or
   required check is not overridden by this report.
3. After deployed runtime is verified, obtain a **new exact full comparison**
   for the explicit baseline request. Keep all five historical rows:
   c7756/e15972 and c7765/e16081 as diagnosed by a7772; c7776/e16154,
   c7829/e16323 and c7835/e16346 as cause unknown, same signature, before
   fix 3afee8b. Any new discrepancy stops baseline acceptance.
4. Only a durable matching baseline receipt starts the observation epoch.
   It is a new starting point, not a claim that history is repaired.
   Any new discrepancy ends that period; two days restart at a subsequent
   explicitly documented matching baseline.

The old raw log, historical evidence and five discrepancies were not changed.
No live check/baseline request, visible window, browser launch, restart,
activation, landing or clock reset was performed in this review.
