# Kernel House builders — implementation, 27 October

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

Import refuses while House is landing, pins main during inspection and rechecks
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
