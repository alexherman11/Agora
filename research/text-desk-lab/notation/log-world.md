# Is the log world in step?

Source checkpoint for commission a7573, 20 October. This is an observer, not
the change from snapshot storage to log storage. Paired live-prefix proof,
activation evidence, live lock measurements and **two observed days** are
still acceptance gates. Nothing here claims they have run.

## Isolation and checking

`log_world.Replay` starts empty and builds an unserved `World` using only
`store.apply` on the first log record and every subsequent record. It validates
sequence, shape, before-value hashes, splices and whole-state digests. It has
no Desk, session, actor, notification sink or reference to the live World.
Detached observations never become replay facts.

The existing writer attaches the checker only when the pre-existing
“Log world: is it in step with the live world?” note exists. The store's safe
bridge captures touched entities after a record and a detached pre-command
image. Comparisons run on one ordered background consumer, in both directions.
The pre-image matters: the logger can absorb an unlogged edit into a normal
record, leaving equal final states. Outside-log repair records also retain
the difference they repaired. Historical repairs during the initial replay
are not misrepresented as newly observed failures.

A full comparison runs at writer attachment and house startup. Anyone can
request another with `log-world check`; `log-world status` returns the current
answer. A request immediately makes the answer unavailable until its full
check completes. No timer, polling or resident wake is added.

Incremental checks cover the touched entities, their expanded placement groups,
links and world facts. An unrelated bypass edit outside that scope needs a
full check or a later record touching it. Startup replay validates every
historical record but cannot compare historical live states that were never
captured. An outside repair and the following command can share one captured
endpoint; the repair's recorded discrepancy is preserved separately.

## Exclusions, including the boxes

The log deliberately omits standing/presence, personal seen marks, folds and
views, painter reports, undo revisions and indexes, chat text derived by
joining its lines, and boxes/z-order inside a non-free parent layout.
Stated flow order remains checked. Free-surface boxes, world/node/subject
props, definitions, links, comments and chat lines remain checked.

The copy benchmark at e15303 found 23,526 facts, zero round-trip fact
differences and 29 differing boxes. Each of those 29 has a non-free parent;
the private JSON receipt lists its name, parent, layout and both boxes.
This settles the class of today's 29. The identities from the 13 October
check are unavailable, so this is not a claimed individual comparison to
that historical list. The paired live-prefix audit must repeat this
classification after landing and report any free-box or fact discrepancy.

## Quiet status and retained evidence

The bridge edits only the existing status note, as house-owned bookkeeping,
through the ordinary logger. It sets `state`, `checked_event`, `evidence`,
`observed` and `unavailable`. Its text begins with the plain status line;
details preserve the first and every later discrepancy, including the
triggering command/author. Its own report records are replayed and checked
without recursively producing another report.

JEFF owns the HUD projection. This implementation adds no waiting tag, knock,
notification or addressing. The comparison worker cannot reclaim a writer
lease to publish its report; publication uses only the existing lease.
Graceful release marks unavailable. A crash cannot update a dead writer's
note; the next attachment marks startup unavailable and records the restart
gap. Forced-death/live UI behaviour has not been exercised.

Checker receipts live in the ignored
`house-state/<world>/log-world.jsonl`, separately from the unchanged source
log. They retain divergences across restarts. Malformed receipts, missing or
torn log boundaries, capture errors and unsupported records fail unavailable.
The bounded queue never blocks a press: overflow records an unavailable gap,
then a full recovery when the backlog drains. Dropped intermediate live
states are not claimed as checked.

Observation counts independent checked endpoints, not replayed historical
records. Time counts consecutive in-step observations within one process,
at most 60 seconds apart, with consistent monotonic/wall clocks. Longer
idle/sleep intervals, unavailable spans and restart gaps do not count.
This is deliberately conservative and may need more than two elapsed days.
No heartbeat is added merely to accumulate acceptance time.

## Lock cost and switch

Only capture and normal status-note publication hold the ordinary writer
lock. Replay, flattening full observations, log copying, hashing and receipt
fsync run outside it. Pre-command capture serializes stated world data into
private in-process bytes; these are never loaded from external files and
contain neither Desk nor undo/event history.

Copy benchmark, 20 samples, e15303: pre-image plus one-subject capture
median 14.4954 ms, maximum 19.8678 ms; full freeze median 12.5700 ms,
maximum 17.8125 ms. These are capture measurements, **not total live lock
holds**. A real press may also publish an earlier status report. The live
report includes capture timings and the previous actual publication lock
duration (`publication_lock_ms`); actual foreground traces still need review.

The one off switch is `DESK_LOG_WORLD=off` in the writer's launch environment.
It leaves ordinary logging enabled, writes unavailable on the next writer
entry and attaches no checker. Changing the launch environment/restarting
the host belongs to the house; no host/settings action was run by this worker.
Re-enabling or recovering a stopped checker requires a fresh writer process.

## House-owned paired fixture and remaining acceptance

Grant c7602 authorizes one fixed house-owned export for this commission.
`log_world_fixture.house_copy` is an internal writer-start hook, **not a
Desk command or actor-claimed host API**. Only the frontier writer exports,
to this existing commission worktree's ignored
`.agora-tmp/log-world-proof/<event>-<suffix>/`. It refuses redirected roots.
It captures a live image and exact whole-record log boundary under one lock,
then copies the immutable prefix and hashes it off-lock. Manifest publication
is last. Failed/truncated/unsupported/event-mismatched copies have no usable
manifest. No raw log is put in a note or source control. The status note's
`paired_fixture` evidence supplies its event and manifest path.

After normal source landing/house activation, the builder should:

1. Read the status note. Record its actual startup event, paired manifest
   event/hash and any unavailable/diverged answer. Do not infer activation
   from a passing source test.
2. Run, with the supplied directory, from this worktree:

   ```
   C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/log_world_proof.py --fixture <directory> --out .agora-tmp/log-world-proof/paired-audit.json
   ```

   It verifies all file hashes and the entire prefix before comparing facts.
   Report actual records, facts, differences and per-box classification.
   It never serves or opens a replay session.
3. The synthetic corruption regression already forces a bypass edit and
   catches/names it at the next touched record, including when the logger
   absorbs it. Retain that proof separately from the real paired audit.
4. Inspect live capture/publication timings and ordinary deskd foreground
   trace holds before concluding Alex cannot feel the overhead. No live
   latency claim follows from the copy benchmark.
5. Let real use advance the status. Keep first/later divergences; never reset
   evidence to manufacture success. Acceptance is 172,800 observed seconds
   with the independent endpoint count and unavailable spans, or a named
   divergence. No timer, synthetic live traffic or wake is needed.

## Ran versus read

Ran: targeted `test_log_world.py` (22 tests, including quiet house routing,
outer-check hash chain, replay isolation, bypass/repair, retained history,
recovery, off switch and paired-export refusal); public-loader copy benchmark.
An additional private synthetic receipt rebuilt 217 facts through 9 records
in step, then caught a forced `prop:unlogged` bypass at record 10, event e49:
live “forced copy-only bypass” versus absent from the log, attributed to the
next edit command by jeff. It is in the ignored
`.agora-tmp/log-world-proof/synthetic.json`; the targeted bypass regression
reproduces the same mechanism without needing that private runner.
The legacy `test_store.py --quick` could not begin: its tempfile log append
was denied before its assertions. No workaround was attempted.

Read: store fact schema/replay/repair machinery; deskd writer leases/locking;
house startup/news/knock routing; the live charter, commission contract,
builders' notebook and Handbook “The log: records of facts”.

Not run: real paired frontier fixture/audit, live activation, total foreground
lock timing, forced writer death, two observed days, HUD rendering or historical
13 October box identities. No browser, personal session transcript, account,
credentials, model call, live migration or host restart was used.
