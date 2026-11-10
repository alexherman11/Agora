# A non-owner logs a comment before its save is refused

Diagnosis for a7772, 20 October, source `229b24a`. **No repair implemented or
live data restored.** Proposed boundary repair is on the card as c7799.

The failure is a late ownership check. A compaction helper runs a file-based
Desk in a separate process, appends its change to the shared log, then is
refused permission to save the world. The active writer never receives that
change. Its next normal logger begin reconciles the log to its own memory,
deleting the orphan fact from the log. A concurrent snapshot overwrite is
unnecessary to produce the reported divergence.

## The two live comments

Read through the Desk, not raw session files:

| Missing fact | Charter snapshot | Checker evidence | Current live event with that number |
|---|---|---|---|
| `s7730 comment:c7756` | e15971 | log sequence 8859, e15972, absent live, compaction receipt logged | e15972 is the house setting a7544 `commission=waiting` |
| `s7543 comment:c7765` | e16080 | log sequence 8932, e16081, absent live, compaction receipt logged | e16081 is the house updating a6866 `as_of` |

The sequence numbers above identify the **outside reconciliation records**,
not a claimed original comment command. Their author/command are `?` / empty,
exactly as `store.begin` writes those records. The observer's boundary event
label does not establish that the live world accepted a comment event.

The first card ran on Codex; the second card's history records Claude. Both
provider compaction paths call `charter.live`, and both worker processes
inherit `DESKD=off`. This is not a Codex-only failure. The evidence note also
retains a third matching discrepancy: `s7665 comment:c7776`, sequence 8983,
boundary e16154, charter snapshot e16153. I did not rewrite that evidence or
classify unrelated differences as this fault.

**Evidence limit:** the live receipt process's original stderr/exit status
and an image of its memory were not supplied. Exact original command records
were not read from the live log. Attribution of these historical incidents
to this path is a source-and-live-signature inference, supported by an exact
mechanism reproduction below; it is not an observation of those past processes.
There is no evidence here of two successful snapshot saves racing.

## The call path (read)

1. `workshop.py:1660` sets the worker process's `DESKD=off`.
2. Claude's compact hook invokes `charter.main`; Codex's
   `codex_resident.refresh_charter` (also used by codex_worker) calls
   `charter.live(..., "compaction")`.
3. `charter.py:192` reads a detached world through `export_docs.load`, then
   `collect` / `report` issue `look; do comment ... to=nobody` as house through
   `desk_mcp.run_desk`.
4. `desk_mcp.py:94` launches `explore.py`, inheriting the environment.
   `explore.via_deskd` returns false for `DESKD=off`; it does not reach the
   in-memory world's owner. The CLI locks, loads/catches up its own Desk, and
   executes the command there.
5. `explore.main` calls `store.safe_commit` **before** `save_desk`.
   `explore.py:95` only then checks the writer lease and raises
   “held by its world server … send the line through the door”.
   The append has already been flushed; no rollback removes it.
6. `desk_mcp.run_desk` returns an error receipt. `charter.live` discards its
   error flag and `collect` does not check the report's result. Charter
   injection can therefore succeed while its world receipt failed.

The comment really existed in the helper's temporary Desk. It was not a
fabricated fact, but neither was it an accepted live-owner write. Calling
it “a live comment subsequently erased by a later save” would confuse those
two worlds. The test proves the active owner and snapshot can stay unchanged
throughout.

## What “repaired by logger” does (read and ran)

`store.begin` (701) sees that the log head digest differs from the active
Desk's flattened facts. It appends a `cause=outside` record changing the
**log** to match that Desk. In this case the change removes the orphan
comment. It does not recreate a comment in the active world or rewind that
world. The following ordinary command then appends normally.

`log_world.Replay.consume` (126) reads that outside record into its private,
unserved world and preserves the pre-reconciliation discrepancy. Its text
“unlogged edit repaired by logger” is a description of a generic logger
reconciliation, not proof that someone edited live memory or that the
checker repaired live state. Replay equality after reconciliation does not
erase the retained divergence.

**There already is automatic replay outside the checker.**
`explore.load_desk` calls `store.catch_up` (848), applying the post-snapshot
log tail to a freshly loaded Desk. Read-only `export_docs.load` does this
under its lock but saves nothing. The copy test shows a reader can temporarily
see the orphan, then not see it after the owner reconciles. A newly loading
writer can also use this recovery path; an orphan could be adopted if loaded
before reconciliation. The held owner's cached world deliberately skips that
catch-up (`deskd.Session._enter_locked`, 435). None of this was invoked against
the live world by this diagnostic.

## Scope and minimum proposed fix

The underlying fault is shared by any file fallback reaching these same
CLI/store calls while another process holds the lease. Ordinary house calls
prefer `House.act` -> `deskd_do` -> `/api/do`, but their connection-failure
fallback is `desk_mcp.run_desk`. A CLI `--window` request also bypasses the
normal server path. These have the same late-save-check exposure.

Normal home-base gestures use `/api/do` (`desk-shell/lens.js:62,103`) and
`deskd.Session`; normal ownership admission happens before the command.
No separate direct HUD log writer was found. However non-reading deskd
sessions with holding disabled or released can also defer rejection to
save time. This is a reachable risk in source, **not evidence that HUD or
host operations have already lost writes**. This was a focused entrypoint
audit, not an audit of every external program.

Proposed on c7799, not applied:

- Check ownership under the world lock **before any fallback command/log
  begin**, including non-reading deskd operation without a lease. Retain
  the final save check. Foreign-owned requests must leave no event, record,
  or snapshot change. Do not override worker environment restrictions,
  reclaim a lease, or invent automatic replay as a workaround.
- Keep provider compaction helpers read/inject-only. Let the existing parent
  house compact/charter-read handlers write their receipts via `House.act`,
  carrying the actual charter read provenance. Surface receipt failure;
  do not silently claim it was saved. Cover both providers and deduplicate
  the compact boundary.

Tests for that future repair: foreign-owned requests have zero effects;
authorized owner and genuinely offline worlds still work; offline reads
do not mutate; both providers produce one parent-owned receipt; receipt
failure is distinguishable from successful injection. Keep the current
diverged verdict, full evidence and stopped two-day acceptance clock.
Restoring comments requires a separate reviewed decision, not this checker.

## Reproduction (ran)

```
C:/Projects/Agora4/.venv/Scripts/python.exe src/text-desk/notation/diagnose_receipt_writer.py
```

The real charter, MCP wrapper, CLI, saver, logger and Replay code run against
one synthetic room and disposable files under this worktree's `.agora-tmp`.
The subprocess boundary is driven in-process with its session root redirected;
the foreign lease identity is a stand-in. No actual second host is started.
The test reads only its own generated fixture pickle, never a live/try session.

Printed: return code **1**; temporary Desk held comment **true**; active
owner held comment **false**; snapshot unchanged **true**; leaked record
**2**; repair record **3**. Ghost comment **c48** / event **e42**; the next
ordinary owner event also **e42**. A read-only catch-up temporarily shows
the ghost; after reconciliation it is absent. Final log matches owner
**true**, divergence retained **true**. The charter context was returned
despite the failed receipt **true**.

The first probe attempt used `repl` incorrectly for a semicolon batch and
stopped before the owner's follow-up act; its disposable fixture was removed.
The corrected probe uses separate ordinary reads/acts and passed. This is a
diagnostic reproduction, not a repair test, browser proof, live process trace,
full health judgment or claim that all log/state divergence has this cause.
