# Documented comparison baselines

This source adds an explicit observation epoch; it does not repair historical
log records. It must land and be loaded by the ordinary writer before use.
No restart, activation, historical repair or live baseline was performed by
this source change.

## Runtime evidence read on 21 October

- The live door's `/door/status` reported code `9ab1bb0`, up since
  `2026-10-21 09:38:29`; `/api/health` reported PID `71312` and the same code.
  `git merge-base 9ab1bb0 3afee8b` returned the full hash of `3afee8b`,
  the refused-writer/parent-receipt fix.
- The house heartbeat identified PID `91800`. Read-only `Get-Process` reported
  start `2026-10-20T23:07:41-07:00`, matching the keeper's restart record.
  Startup main base `e7f8cb5` is inferred from commit/start timing, not an
  imported-code attestation: that commit was made at 23:06:01, the next landing
  at 23:07:47. Both include the fix. A fresh compaction receipt on this card
  (`c7930`) has its new parent-written source/read-identity format.

The house does not publish its imported commit. The timing inference and the
receipt evidence are not an exact memory/code measurement.

## Use after landing

1. Read `log-world status` and Evidence through the live Desk. Verify the
   runtime contains this source; do not restart anything for this commission.
2. Prepare a note with `role=log-world-baseline-request`. Its text must say why
   this boundary is justified and enumerate **every** retained discrepancy.
   Set its `divergence_hash` to `retained_divergence_hash` from the status
   response. The hash identifies the whole retained list, in order; it is
   consistency bookkeeping, not an authentication credential.
3. Submit `log-world baseline <request-note-appearance>`. It queues a detached
   full observation under the existing writer serialization, like `check`.
   A queued response is not acceptance. No worker file loader is used.
4. Read the result and Evidence. Acceptance requires an exact full fact match,
   the reviewed retained-list fingerprint and no known broken log integrity.
   A changed list, outstanding recovery or mismatch refuses the baseline.
   Ordinary writer admission and the final save guard remain unchanged.

An accepted append-only checker receipt contains the event/sequence/log offset,
state digest, full fact count, zero current differences, request identity and
reason, every historical discrepancy set aside, prior totals and date. Evidence
projects this receipt into the world together with the unchanged historical
discrepancies. The request note alone never changes the verdict.

An unprojected receipt can survive a crash: startup reloads it, checks that its
fingerprint identifies the retained prefix, and projects it on the next full
check. A malformed/torn journal or failed append makes comparison unavailable.
Neither raw journal nor raw world log is rewritten. Repeated delivery of an
accepted request identity cannot reset counters again.

Every queued attempt has a durable result: `baseline_attempt` records the last
attempt's request, reason, reviewed-list hash, event, date, full-check flag,
difference count and result. `last_baseline_refusal` separately retains the
latest refused attempt even after a later success or duplicate delivery.
`baseline_result` is the readable result of the last attempt. All three remain
available from `log-world status` after ordinary updates and checker restart;
the two full attempt records are also projected into Evidence. Syntactically
invalid requests that never queue remain ordinary Desk command refusals, not
baseline attempts. The witnessed row keeps only the short result and baseline
event, not copies of all reasons/evidence.

If acceptance is fsynced but writing the following attempt result fails, the
checker becomes unavailable. Restart reconstructs the acceptance result from
the durable baseline receipt and requires a new full comparison before saying
in-step; it never creates another baseline just to repair missing publication.
World-note publication is separate from durable acceptance. A later projection
can publish the already accepted receipt; a failed projection is not a second
baseline or permission to claim the note updated.

## What changes after acceptance

The retained `divergences` list and all old journal rows stay as they were.
`active_divergences` is the suffix after the accepted boundary; only that suffix
determines the verdict and first-divergence field. All accepted baselines remain
in Evidence, including their complete reasons and set-aside lists.

Observation seconds/records start at zero. The baseline endpoint itself is not
counted. Independent checked endpoints can subsequently advance counts under
the existing monotonic-clock, sleep/idle and checker-self-write exclusions.
Restart coverage remains a gap; old totals and gaps remain in old receipts.
The receipt states: **a new starting point, not a claim that history is
repaired**. A new discrepancy ends this observation period, freezing its totals.
Even if later records reconcile the current facts, this period cannot resume:
the retained active discrepancy keeps the verdict diverged. Two observed days
must begin again from a subsequent explicitly documented matching full-check
baseline, not continue from where the broken period stopped.

The status note drops its old `checked_event` property once. Thereafter that
moving field lives in `witnessed:log-world`, along with counters and gaps.
Only changed state, line or active first discrepancy changes the verdict.
Evidence still updates at full checks or new discrepancies.

## Current historical inventory — not a live baseline

The live full check requested through Desk completed at `e16940`, dated
`2026-10-21T11:11:16-07:00`. Evidence still contained exactly these five rows,
with no newly added full-comparison discrepancy:

| Retained aspect | Boundary label | Log sequence |
| --- | --- | --- |
| `comment:c7756` on `s7730` | `e15972` | 8859 |
| `comment:c7765` on `s7543` | `e16081` | 8932 |
| `comment:c7776` on `s7665` | `e16154` | 8983 |
| `comment:c7829` on `s7815` | `e16323` | 9137 |
| `comment:c7835` on `s7044` | `e16346` | 9161 |

All five retained rows describe absent live compaction receipts followed by
logger reconciliation. The cause-first diagnosis on a7772 reproduces the
refused foreign write path and attributes the first two historical cases by
inference; it does not recover original helper memory/stderr. The additional
three have the same retained signature and predate the fix, but have not had
independent historical attribution. A request must disclose that limit, not
claim five individually proven causes. Event/comment labels were reused;
these are historical log boundary labels, not proof that today's live comment
with the same label was lost.

Do not restore these comments or delete/rewrite any evidence. A future matching
baseline means the *current* full state agrees and future observation counts
again; it does not turn the historical faults into successful writes.

## Evidence from this worktree

Ran on synthetic room worlds with the real log/replay/Desk implementation:
`test_log_world.py`, including accepted/full mismatch/stale inventory, duplicate
queued requests, restart counters and new first divergence, failed durable
receipt, malformed baseline prefix, non-full refusal, broken integrity refusal,
and a command journey through a documented world note. Provider transports and
leases in `test_writer_admission.py` remain fakes; that suite uses the real
engine/log boundary. Test counts and broader checks are reported on the card.

Not run here: an accepted live baseline or two observed days. The live preflight
full check did not reset the retained verdict. Landing/loading and the explicit
request/result are separate steps; no runtime activation is implied by tests.

## Resumed round, 21 October — still staged

Juniper's c8837/c8841 explicitly accepts a *future* matching baseline setting
aside all five listed rows: two as diagnosed in a7772; the other three as
**cause unknown, same signature, before fix 3afee8b**. This is the epic holder's
historical-scope decision, not new causal evidence or an accepted live baseline.

A fresh live `log-world check` completed at **e20019, 15:48:29 -07:00**:
exactly the same five retained discrepancies, no additional rows. The status
remains diverged. This check does not authorize using that old endpoint as the
baseline after deployment; another full check must accompany the actual request.

Read-only runtime evidence refreshed in this round:

- `/door/status`: up, code `2637cdd`, since `2026-10-21 14:46:36`.
  `/api/health`: OK, PID `79440`, code `2637cdd`. Its ancestry includes `3afee8b`.
- Main's house heartbeat at `2026-10-21T15:49:10.561848-07:00` names PID
  `57804`. `Get-Process` reports start `2026-10-21T12:13:53.652000-07:00`.
  The preceding main commit is `f6b8fb7` (12:09:26), also descended from
  `3afee8b`. This is startup-code inference, not an in-process commit
  attestation. Fresh parent compaction receipts retain source/read identity.

Ran:

- Real synthetic engine/replay tests: **42 tests / 4.110s, OK**.
- Writer admission/parent receipt suite: **11 / 0.792s, OK**.
- Observation accounting: **5 / 0.000s, OK**.
- Focused Ruff F/E9 for `log_world.py` and `test_log_world.py`: passed.
  Including `desk.py` reports F841 (line 923), F401 (1242), F541 (1919);
  unchanged exported main reports the exact same three diagnostics. The only
  `desk.py` edit here is its command-help synopsis. `git diff --check` passed.
- Exported unchanged main `2637cdd3e2599afe255f44d080850562e4057271`
  as tracked source into this worktree's ignored scratch directory (no main
  checkout mutation or supplied-world copy). Compared diagnostic failures:

| Check | Main | Branch | Attribution limit |
| --- | --- | --- | --- |
| `test_reach.py` | exit 1, 0.732s | exit 1, 0.201s | Same four named failures: empty rows; does not prove filesystem cause |
| `test_textedit.py` | exit 1, 7.249s | exit 1, 6.888s | Same `could not take textedit-test.lock after 60s` text; 60s is the diagnostic wording, not measured wall time |
| `test_visit.py` | exit 1, 0.620s | exit 1, 0.212s | Same WinError 5 at tempfile-created `test-visit-*/trees` before its test door starts |

Complete stdout/stderr, main revision and elapsed times are preserved under
`.agora-tmp/baseline-main-health/*-test_*.py.json`; diagnostic runner:
`.agora-tmp/baseline-health-compare.py`. The runner's own exit is not the test
exit; the retained `exit` field is the test result. It sets inherited-ACL
worktree TMP/TEMP/TMPDIR/AGORA_TMP but does not replace the tests' own tempfile
calls or weaken checks.

**Not certified:** all other prior full-health temp failures, the door no-answer
case and painter checks still lack a fresh paired main attribution here.
`test_door.start_door` can leave an unreturned child on startup timeout; no new
door-timeout reproduction was attempted. No known-blocked browser lane was
relaunched. This is selected diagnostic evidence, not a full health pass.

Deployment also remains blocked: these paths are not `workshop.HOUSE_FILES`,
but `door.watch` swaps deskd on **any HEAD movement**. Juniper's honest-health
requirement and the later lifecycle bootstrap finding must both be satisfied;
no ready/landing, swap, restart or observation-clock reset occurred. Ordinary
unchanged-runtime recovery is outside this patch and is not disabled.

## Current release review, 21 October, 19:41

The lifecycle blocker above is superseded by JEFF c9385 and Mica c9399:
ordinary judged landing/Desk swap is allowed unless something important
would break. Mica still requires review before ready. See
`log-world-baseline-release-review.md` for the named unknown temp/door/painter
failures, affected behavior and release risks. Historical paired failures
against main2637cdd remain failures, not current-main attribution or passes.

Ran preserved source: baseline 42 tests/3.378s OK; admission 11/0.877s OK;
accounting 5/0.001s OK; diff check clean. No implementation changes, unsafe
retries, landing or baseline. Live status at e22129 remains historically
diverged; a new exact full comparison after deployment still gates the epoch.
