# Kernel House builders — implementation, 27 October

## Adopting main's existing edits (6 November, dk3913)

`house.adopt <path> [<path>...] text=<message>` is a steward-only Git seam.
Paths are literal repository-relative files (forward slashes; quote spaces),
including additions and deletions. It reads the author name and email from the
repository's Git configuration, ignoring inherited Git identity overrides.
It preserves the supplied commit message.

The command refuses a busy landing queue, publication lock or Git lock, an
external Git lock/merge/rebase, paths outside main, directories, symlinks, or a
named file whose working content has no change from HEAD. It holds all three
House locks and the real index lock while running the existing House baseline
on the dirty main checkout with the pinned interpreter and hidden subprocesses.
No source is copied into main for the checks.

Private indexes select exactly the named files and preserve unnamed staged
entries. Failed checks do not change HEAD, the real index or working files.
Successful checks are followed by a checkout-change check, a new single-parent
commit, a compare-and-swap advance of main, and replacement of the selected
index entries. There is no stash, reset, checkout, hook execution or history
rewrite. The command itself never writes working files. Tests that themselves
edit source cause refusal, not an attempted restoration of their edits.

Long requests use the accepted-call protocol. `house.adoptions` (stewards only)
reads durable receipts, including commit, exact files, configured author,
named checks and their output paths. A resident requester also receives a wake.
Evidence and private indexes live under the House's `adoptions/` directory.
An interrupted request is not automatically replayed. If publication succeeds
but installing the prepared index fails, the receipt retains the commit and
error and the index lock remains for explicit inspection.

`test_adopt.py` uses scratch repositories under the worker's `.tmp/` only.
No fixture runs adoption on the real main. The Lines/module boundary now
also carries `positional`, preserving quoted argument boundaries for any
module that needs exact file names; existing `target`, `words` and `kv` remain.
Activation requires the normal kernel and House reload after landing.

## Restart reconciliation (builder implementation, 6 November, dk3639)

Shutdown saves every active worker's interrupted phase before stopping children.
Startup also recognises the older blocked `House shutting down; preserve work
and reconcile before retry` receipt. It repairs stopped workers' stale card
build fields through the existing House bookkeeping channel and claim/revision
guards. Refused writes remain pending and use the existing bookkeeping notices;
there is no alternate credential or grant path.

An interrupted working turn resumes its existing session and worktree, with its
last public words included in the continuation. Age is no longer a cutoff.
Current ownership, holds, manager approval, process exit and provider capacity
still apply. A full pool keeps the continuation queued and the summary names
its actual phase and queue state; admission is not reported as an authenticated
running turn. Interrupted preparation, review, landing, unresolved transfers,
unknown effects and possibly live processes wait for their owner.

The stream records tool start/completion correlation ids, without arguments or
results. An unfinished or uncorrelated tool, a lost send/result, or an older
worker with tool activity but no completion receipts prevents automatic replay.
This is conservative: an operation may have completed even though the House
never observed its completion. It must be reconciled by the owner.

Each startup produces one restart wake and one reconciliation summary for the
agent with the general-manager role. Owners receive a grouped receipt naming
waiting cards and reasons. Structured receipts use the existing live Agent Book
`Someone woke them` heading; continuation prose uses `When a restart cut it off`.
No book edit is required. Receipt data survives a missing template.
`builders/restart-receipts.json` retains undelivered destinations. Agent
`wake_once` persists the delivery key and message together before acknowledging
acceptance, including while busy or asleep. The ordinary House tick retries
receipts and card writes without issuing another model turn for a reconciled
worker. Finished/superseded cards are not resumed.

Hidden coverage is in `test_restart_recovery.py`, with the three-worker restart,
legacy shutdown failures, stale card fields, repeated restarts, capacity, unsafe
effects, failed delivery, card-write retry and durable busy-agent inboxes.
Activation is a House restart after landing; for this card the owner requested
landing with no other work running. These fixtures do not restart the live House.

## Bounded landing attempts (builder draft, 5 November, dk3384)

`house.land` saves an attempt id and a `started` activity before starting its
thread. Its answer and `house.who` include the receipt. `land_attempts` retains
earlier receipts. Before launching the thread, the card receives `land_attempt`,
`land_step`, `land_receipt`, outcome and build phase through the House module's
own `see`/`do` channel. All lifecycle build updates use that same channel,
constrained to build bookkeeping fields, the current `build_run` and a fresh
card revision. Requester credentials are not needed for these writes. The
requester's authority still gates lifecycle commands, claims and handoffs.
Manager runs retain their existing task approval, ownership and hold checks.
If the module write refuses, the attempt blocks before Git/checks; the refusal
is retained as `land_sync_error` and remains readable in `house.who`. There is
no fallback to a person's session. Both the owner and the steward who requested the
attempt receive its terminal receipt. Notification failure remains pending
for the ordinary tick; repeated delivery is deduplicated.

Every failed build-field write also queues an independent durable notice for
the **current card lead** and the coordination chat named by House settings
`bookkeeping_failure_chat` (Shop talk in this desktop). Resident leads receive
a House wake; other leads receive `notification.send`, keyed by the failure.
The chat receives a House-authored `say` about the card. Each destination is
retried independently on the ordinary tick, even for managed runs and even
after a later card write succeeds. A lost chat reply is reconciled by reading
the matching notice before another send. A lead wake interrupted before its
delivery checkpoint can be repeated after a crash. Missing routes or refused
notification grants remain visible in `house.who`'s `bookkeeping_notices`;
they never trigger another person's session. The prose comes from the live
Agent Book section **House card write failed**; the structured failure evidence
is included even if that section is missing.

Build bookkeeping uses an explicitly scoped module grant: `set` on
`kind:taskboard-task` and only these fields:
`builder,build,build_run,build_phase,build_detail,builder_chat,result_received,reviewed_commit,landed_commit,outcome,land_attempt,land_step,land_receipt`.
`grants.json` declares it alongside the module source. Desktop startup
(`kdesk.after_genesis`) installs that extra scope once through the ordinary
steward `grant` command. The module's `asks_scoped` remembers each command and
scope separately; an existing `set` grant on another object cannot mask a
missing scope. Repeated startup does not duplicate it, a revoked scope stays
revoked (even across source removal/readdition), and an off module gets no
new grants. The House cannot grant itself authority. This requires the desktop
kernel's next authorized startup after landing; restarting House alone does
not run the installer. No live startup is part of the worker's checks.

Equivalent manual line, if needed by a steward:

```text
grant house words=set only="kind:taskboard-task;fields:builder,build,build_run,build_phase,build_detail,builder_chat,result_received,reviewed_commit,landed_commit,outcome,land_attempt,land_step,land_receipt"
```

For notices, `say` must reach only the configured chat;
`notification.send` must reach the relevant cards for nonresident leads.
Set `bookkeeping_failure_chat` to the coordination chat in House settings.
These notice routes remain world configuration for an authorized steward.
They are not fallback authority to acquire after a refusal. Fixtures prove
that `text`, ownership and other unrelated fields cannot be written through
the build update path, and that the shipped grant rejects non-card targets
and mixed writes containing an unrelated field.

The initial fix exposed a specific silent failure: steward admission did not change the
saved requester used for card writes or wake routing. A saved owner who could
no longer write the card left its old `landing, received` facts intact, while
the actual blocked state stayed private and the caller heard nothing. The
6 November correction routes those writes through the House itself and records
the started card receipt synchronously. The House still needs the
kernel `set` grant installed by desktop startup or an authorized steward.
Without one, it reports the refusal and does not
launch the landing. Duplicate
builder chats are a separate handoff refusal; landing does not resolve chats.
Neither a desktop suite nor WM activation is reached after this early refusal.

House settings `landing_timeout` and `landing_wait_timeout` are positive finite
seconds, reread per attempt. Defaults are data in `landing-defaults.json`
(1800 seconds overall, 120 seconds per lock wait). A landing records
`started`, `waiting`, `commit`, `merge` when needed, `checks`, `publication`,
and `activation`. Overall cancellation/deadline checks surround Git, checks,
publication and activation inspection. Existing network door timeouts still
bound in-flight requests; cancellation may wait for such a request to finish.
Named suite timeouts continue to apply independently.
The same settings data supplies `landing_cleanup_timeout` (30 seconds per
termination/exit wait) and `landing_poll_interval` (0.1 seconds between
cancellation checks).

`house.land-cancel <card>` is a steward-only cancellation request. The owning
thread stops its own child tree, unwinds and releases its locks, then records
`blocked` with a reason and wake. It does not undo a commit already published.
Child exit, timeout, spawn failure, thread `BaseException` and interrupted
attempts found at House startup all retain terminal receipts. A restart during
activation is recovered even though publication already set the phase to
`landed`. Retrying/handing/replacing a worker cannot overtake a settling attempt.

Reviews queue on their own bounded lock. Imports share only the short
publication lock, so a long check does not monopolize `house.import`.
Notification acquisition on lifecycle paths is nonblocking, avoiding the
notification-lock / state-lock inversion; the tick retries delivery.

OS termination denial is an explicit exception to automatic cleanup. It is
reported with the child PID; the House thread settles promptly, while locks
protecting a possibly writing child remain fenced until it exits. A persisted
child PID also fences Git and imports after a House crash until exit is known.
No alternate authority or termination method follows a denial. The parent
process exiting is not proof about independently detached descendants; suite
scripts still own their hidden-desktop cleanup contract.

`test_ghost_landing.py` includes a real in-process kernel permission mismatch,
immediate and duplicate receipts, thread failure/crash recovery, bounded queue
and Git waits, cancellation, denied termination fencing, wake routing, and
import availability during review. Process-tree termination is exercised with
process doubles in the worker sandbox; a host-side hidden check is still needed
to verify actual Windows tree termination.

`test_bookkeeping.py` adds the four-person case (maker, lead, landing steward
and saved worker owner are distinct), lead/Shop talk delivery, independent
retry, and lost-reply reconciliation. Its memory variant runs real kernel
permission checks and transactions with storage doubled; the disk variant
also uses the existing isolated kernel fixture. Neither starts a worker or
activates a desktop component.

## Recoverable ownership handoffs (builder draft, 5 November, dk3259)

`house.hand` uses the existing word; this is a mechanism fix (`Source: fix`,
`Missing-word: none`). The saved worker `requester` is the owner used by
landing admission, notifications and `house.who`; House-owned lifecycle facts
are written through the module's own grants. Listings also expose its person id as
`owner`, alongside `owner_name`, and `handoff_status`/`handoff_to` while unresolved.
Editing a card's `who` alone never grants worker authority.

The House persists a handoff intent, recovers or creates the recipient's private
chat, then writes `who`, `lead` and `builder_chat` together under the card's
revision fence. Only the authenticated caller writes the card; an explicit
denial never causes a retry under another person's session. Existing chats are
read through the recipient's door, including chats created before a lost reply.
A deduplicated `make` can return an empty `made` list; that is no longer indexed.
The saved owner changes only after read-back confirms the intended card, run,
recipient and chat. A failed save leaves the old in-memory authority intact.

An uncertain card write is retained, not replayed. Lifecycle calls return an
explicit unresolved refusal; queued worker starts skip that worker. Neither
waits for the transfer to finish. Repeating the handoff
with the same recipient reads it back; a different transfer cannot overtake it.
The ordinary tick and House startup also reconcile a completed write. A write
that cannot be confirmed remains explicitly unresolved; neither a display name
nor a failed response is treated as proof of ownership.

The module acknowledges a slow request through the existing accepted-call
protocol, so the ten-second deadline returns `starting` rather than a false
refusal. Completion notices to the recipient and caller survive restart;
notification failure does not undo the transfer or report it as refused.
Quick refusals remain refusals. Quick successful receipts distinguish completed
ownership from pending notification. Repeating a completed transfer is harmless.
Handoff delivery attempts take the shared notification lock without waiting.
If another notice owns it, the confirmed transfer returns with notification
pending; refused or unresolved request notices remain queued for the tick.
This is recovery across two stores, not an atomic transaction between them.

Hidden coverage in `test_handover.py` uses real in-process kernels for the empty
deduplication receipt, legacy partial handoffs, both lost-write timings, restart
and failed-save recovery, authority checks, prompt refusals from all six lifecycle
calls during a transfer, startup with an unresolved intent, notification retry
and lock contention, and the real ten-second module deadline. No model or native
window starts.

## Committed definition import (builder draft, dk2393)

`house.import <thing> field=code|text from=<landed-card> path=<repository-file>`
copies one UTF-8 Git blob into `component.code` or `lens.text`. This replaces the
discarded installer proposal. It never runs an installer, reviews a component,
changes a grant, launches a window or joins automatic switch-on.

The six admission checks:

1. The published word is steward-only; the handler also verifies the authenticated
   caller is a direct person or that person's agent. Module/widget callers refuse:
   the existing kernel's nested-module path does not recursively preserve all
   upstream grant restrictions. This change does not widen or repair that path.
   The shared gaming gate runs before Git inspection and before returning
   the proposed edit. No credentials or requester sessions are read.
2. The visible card's `landed_commit` must match a House-owned landed receipt with
   `review_base`. Superseded workers' saved receipts are included. A missing or
   ambiguous receipt refuses; a merge parent or task text is never substituted.
3. The landed commit must be an ancestor of committed `refs/heads/main`; its base
   must precede it. Only added/modified files in that recorded diff qualify.
   The file's blob and regular-file mode must still match main. Reads use immutable
   Git objects, with replacement objects, external diffs and text conversion disabled.
   Checkout edits are never inputs. Paths reject traversal, absolute paths, drive
   paths and backslashes; symlinks, submodules, non-UTF-8/NUL data and files over
   1 MiB refuse. All Git commands are read-only and have no visible console.
4. Only the two supported definition fields qualify. No security, grant, identity,
   review-mark or settings fields qualify. The answer is an ordinary `set`, admitted
   as the caller narrowed to House, with destination and source-card revision fences
   checked even on equality. The kernel preserves/checks its existing participant
   fence marker on module answers, so a concurrent identical edit cannot masquerade
   as this import's change. House needs
   the field grant; it cannot borrow the caller's authority or bypass a refusal.
5. Equality still goes through normal field authorization but writes no record.
   Reviews and all widget grants remain untouched. The receipt says whether the
   component's existing review hash matches the imported bytes.
6. Successful receipts carry card, recorded base/commit, inspected main, path,
   blob, destination, old/new SHA-256, changed/unchanged, review status and unchanged
   grants. The kernel now retains declarative modules' answer text/rows **after**
   admission; a rejected edit never returns a successful import receipt. The
   ordinary world record retains the import Line, set bytes and revision evidence;
   undo reverses the field edit.

Import refuses while House is publishing or a surviving landing child may still
write, pins main during inspection and rechecks
it before returning. Git and kernel are separate stores: no cross-store atomic
transaction is claimed. A later landing does not retroactively change the imported
blob; the receipt identifies exactly which committed snapshot was inspected.
Synchronous timeout/late-answer handling remains the kernel's existing fail-closed
module behavior.

Proposed prerequisite grants, **not applied by this worker** (skip any already
covered by active grants):

```text
grant house words=set only="kind:component;fields:code"
grant house words=set only="kind:lens;fields:text"
```

House's existing `rows look` grants remain necessary. No `make`, `component`,
`widget`, `off`, broad app/settings `set` or session-token authority is requested.

### Search repair Lines for JEFF, after review and deployment

Read the receipt after each import and stop on refusal. These select the old
Search landing through the card's recorded commit, not its newer worker.

```text
house.import dk2402 field=code from=dk1625 path=research/kernel-lab/apps/smart-search/lexical.js
house.import dk2403 field=text from=dk1625 path=research/kernel-lab/apps/smart-search/search.lens
look dk2402
set dk2402 gestures="evidence open"
```

The imported lens must be:

```text
root : smart-search
  on evidence do window.open thing $id
  on open do window.open $lens
```

If the component receipt says `review=required`, refresh and review:

```text
look dk2402
component dk2402
```

For the already-on Search widget, first inspect active grants:

```text
look dk2404
rows grant to=dk2404
```

Only if its active grants do not already cover `hear:view`, add:

```text
grant dk2404 words=hear:view
```

Read live during this task: the existing grant already covers `window.open` and
the other requested words; only `hear:view` is missing. This additive grant keeps
the existing grants and widget owner. Repeating `widget ... grants=...` would
revoke/recreate grants and rebind `for` to the acting steward, so it is not the
repair for this already-on widget. Both the component review and grant addition
are conditional steward actions, not an unconditional batch. Import's gate covers
the import only; it does not gate subsequent standalone kernel words.

`test_imports.py` exercises actual in-process kernel admission, refusal/equality,
module and caller narrowing, review/grant preservation, undo and receipt handling.
Its Git fixture is read-only/in-memory; one test also reads real main Git blobs.
No fixture starts a host process or opens any window.

Builder draft implementing approved MOVING-IN step 3. The missing world word was `task.build`: the House could run residents but could not claim or execute a coding task. This is the corresponding Rough spots record. It does not revive Frontier.

`task.build <card>` is a world alias for `house.build`. House validates visible, unheld ownership, persists a request, then returns promptly. An asynchronous runner claims the card with the kernel's revision fence, creates its own Git worktree, and starts the existing ChatGPT-authenticated Codex coding adapter. Two simultaneous builders are allowed. No session, credential, module grant, security setting or paid fallback is added. A requester must already have exactly one agent session mapped to their account. Today Alex has one; JEFF does not have a separate builder-agent session, so that request is explicitly refused rather than borrowing Alex's identity.

Work uses `house.who` and `house.log`. Adapter startup remains “preparing” until Codex acknowledges a thread. Each task has a private requester chat. Human chat messages or `house.tell <card> <words>` retain a same-task follow-up; a successful idle result can continue its existing Codex thread. Paused, uncertain, reviewed and landed work never wakes implicitly. Corrections require explicit acknowledgement before review. Public activity stores text/tool names and allowlisted sanitized command/path records, never private reasoning or whole raw tool inputs. Logs require visibility of the worker chat; inventory requires visibility of its task.

**Worker command activity (builder draft, 4 Nov, awaiting independent review).** Rough spots: `house.log` discarded the command/path information before the world could display it; no world word could recover it. The adapter now extracts Codex command text and completed file-change paths, and the builder extracts Claude Bash/Read/Write/Edit/MultiEdit command/path fields. Redaction precedes both the 120-character summary and full-detail persistence. The console uses `act-detail` JSON records with native click/keyboard expansion. Historic tool-name-only entries remain unchanged, with a note that their command/path detail was not saved. No raw file content, replacement strings, reasoning or arbitrary tool input is added to activity. Source inspection only after the initial pytest run aborted on a sandbox permission error; regression and hidden browser evidence remain for the House.

Completion is three distinct steps:

1. **Received:** the model ended successfully. Its task remains open. The builder supplies committed source and `BUILD-RESULT.md` self-proof.
2. **Reviewed:** `house.review` independently runs kernel chat/painter tests and hidden desktop tests against the exact candidate. It preserves failures and test output. Current main is merged into the worker tree before checks when necessary; conflicts remain for reconciliation.
3. **Landed:** `house.land` publishes that exact checked commit only if main still matches and user edits do not overlap. It does not reload a runtime or mark the user's outcome verified. The coordinator checks the task-specific proof, safely activates the affected component, and verifies the observable outcome before closure.

Interrupted operations are retained as recovery-needed after restart. An uncertain network/process outcome is not replayed. Worktrees and evidence remain available; no automatic deletion or forced lock recovery exists. Full dynamic revocation of native tools is not claimed: the worker must check live task authority before effects, while the harness fences claim/review/publication and prevents held follow-up wakes.

**Ran:** 21 builder tests, including a private real-kernel/Git lifecycle with a scripted model, independent subprocess test and preservation of an unrelated dirty file. Earlier affected regressions: 25 desktop/adapter tests; 26 initial builder/chat/painter tests. Follow-up/correction checks supersede the initial builder count. Real House module proof: three checks passed, including world alias dispatch and permission-held refusal with no model launch. These tests do not prove the two requested tasks or physical UI behavior; real worker execution and outcome checks are recorded on their cards.

Reproduce with the pinned interpreter: `python -B -m pytest -q research/kernel-lab/modules/house/test_builders.py`; `python -B -m pytest -q research/window-lab/kernel-desktop/test_kdesk.py research/codex-residents/test_worker.py`. All desktop tests are headless. Temporary fixture evidence is retained, not cleaned by a broad deletion.

**House commits for the worker (Claude, 27 Oct, hourly check-in).** All three first builders (dk954, dk1022, dk1027) finished and then stopped at `git add`: the Codex sandbox cannot create `.git/worktrees/<run>/index.lock` (the old desk hit the same on 1 Oct; README "Later live limits"). The old workshop answered it by telling workers not to commit and committing for them; this port had dropped that. Now `review` first commits whatever the worker left to its own `worker/<run>` branch (never main), leaving out `BUILD-RESULT.md` and top-level dot-folders, records `house_commit` and a `committed` activity line, then runs the independent checks on that exact commit. The prompt tells workers not to stage or commit. No sandbox or permission change. Missing world word: none; this was a lost source behaviour. **Ran:** `test_house_commits_what_a_sandboxed_worker_left` plus the existing builder, worker and runtime tests, 35 passed.

**No auto gc in the House's git (Claude, 27 Oct).** The first House commit (dk1022) succeeded but timed out: git's automatic background repack of the ~900 MB repo kept the subprocess pipe open past 120 s, so the run was marked `uncertain`. The House's git now runs with `gc.auto=0` and `maintenance.auto=false`. dk1022 was reconciled by hand (commit f953920cf verified as exactly the worker's five files; activity line `reconciled`), nothing replayed.

**Telling a worker is not the owner's alone (Claude, 28 Oct, dk1491 for Alex's dk1489).** Ownership now means being woken at each turn end and making sure someone checks in; it no longer locks out others. `house.tell <card> <words>` is open to the worker's owner, the card's `lead`, a steward (a place leader) and Alex (the `desktop:alex` account's person); anyone else is refused. A non-owner's words reach the worker prefixed with who said them and that the owner stays in charge; the activity log records the teller and how they hold authority. When the worker next ends a turn its owner is woken as before (noting who else spoke), and each non-owner teller whose words that turn followed is woken too (`told_by`, moved to `tellers` when the words are delivered). `house.tell` also resumes a stopped worker in a new turn on the same worktree and thread: received as before, and now blocked (e.g. `BUILD-RESULT.md is missing`) or reviewed. A resumed reviewed or review-failed run moves its review receipts (`review_base`, `candidate`, `checks`) into `earlier_reviews`, so nothing claims to be reviewed that has since changed; review again afterwards. Still refused: landed or released (start a new run), reviewing or landing (the House is acting on it), uncertain or recovery-needed (a process may still be alive or a write's outcome is unknown), and a run blocked before its worktree existed (use `house.retry`). `house.retry`, `house.review` and `house.land` keep the owner-or-steward rule.
