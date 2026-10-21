# Writer admission and parent-owned charter receipts

Commission a7816, 20 Oct 2026. Source prepared; no live activation.

Read: a7772 (including c7793, c7799, c7807), a7816 and Juniper's
instruction to preserve historical divergence; `explore`, `deskd`, `charter`,
the resident adapter and house/workshop start and event-dispatch paths.

## Boundary

`explore.admit_writer` checks the live writer under the session lock.
Writable CLI fallback calls it before load/fresh/dispatch/store.begin.
Non-read `deskd.Session` calls it before loading or attempting a lease.
The final `save_desk` check remains. Existing normal deskd lease-transfer
behavior is unchanged; lease-free requests and DESKD=off do not gain it.
CLI dump/shape, export loading and explicitly read-only Sessions still read.
Ordinary explore commands, even look/read, save seen marks and therefore
require writer admission. No request is silently rerouted.

Compaction helpers read the bounded charter and inject it into provider
context. They never dispatch world commands, including failure reporting.
They return the actual reading (source, snapshot event, text, word count),
with a unique read identity. The parent does not substitute a newer reading.
Additional start= reads remain a fresh-start operation.

Codex uses its existing parent pipe, including the existing generation check
before queue dispatch. Claude's SessionStart hook supplies additionalContext
and writes one complete local JSON report in a parent-designated per-child
directory. The house harvests it on ordinary dispatch passes. That directory
is bookkeeping, not authenticated containment or a host capability; it does
not grant the helper a world-write route. The saved channel name permits
harvesting after ordinary parent restart. Old files remain deduplicated.
No new polling model turn, notice, resident wake or host operation is added.

The parent uses ordinary `house.act` for the world receipt, with no forced
routing or lease override. Before calling, it atomically saves receipt state
as `unknown`; acknowledgement changes it to `written`, a caught failure to
`failed` plus a `charter_receipt_failed` parent log record. Duplicate reports
are not sent again. If the process dies between write and acknowledgement,
the persisted outcome stays unknown, deliberately not retried. This is not
an exactly-once transaction across the world and parent state, nor a
power-loss durability claim. An operator can inspect the read identity in
the world receipt to reconcile an unknown outcome. Hook channel-write
failures are explicit on stderr; there is no fallback world write.
Claude's result proves context prepared for the hook, not a provider
acknowledgement that the model retained it.

## Evidence

`test_writer_admission.py` exercises actual explore CLI entry, session lock,
deskd Session admission, journal records/replay, provider hook/adapter entry,
Worker parent dispatch and House.act with an in-process owner transport.
World fixtures are synthetic; holder identity and provider transport are
stand-ins. No real model or live process was started.

It checks bytes AND modification times, no load/begin/commit/lease call on
foreign refusal, no event or extra file; owner/offline mutation; read-only
load/dump/Session; both providers' parent receipt once; actual older read
provenance across an intervening owner edit; helper injection failure;
parent receipt failure; duplicate delivery; restart handoff and unknown
outcome suppression. The compaction tests replay the resulting real journal
against the resulting saved world with `store.check`.

Ran with the pinned interpreter, from this worktree:

- `test_writer_admission.py -v`: **Ran 11 tests in 0.787s; OK**.
- `test_charter.py`: **Ran 16 tests in 0.698s; OK**.
- `test_host_route_parent.py`: **Ran 23 tests in 0.124s; OK**.
- `test_log_world.py`: **Ran 29 tests in 2.711s; OK**.
- `test_log_world_accounting.py`: **Ran 5 tests in 0.001s; OK**.
- `test_builders.py`, with TEMP/TMP/TMPDIR/AGORA_TMP set inside this
  worktree via os.makedirs: **all passed**.
- `git diff --check`: passed.
- Ruff F/E9 on charter, explore, house, the adapter and changed tests:
  **All checks passed!** Adding deskd/workshop reports two untouched
  diagnostics: deskd.py:35 unused aspects_of, workshop.py:1331 redundant
  f-string. Full default Ruff reports **1180 errors** across these
  legacy files; no broad formatting cleanup was attempted.
- `test_store.py`: blocked before its checks by **PermissionError** writing
  `t.log.jsonl` inside its tempfile-created Windows directory. Not a pass.
  The new tests above use actual store/replay with inherited-ACL fixtures.

Test scratch cleanup was refused by tool policy; that self-created scratch
directory remains locally ignored. It contains only fake builder fixtures.

Historical `diagnose_receipt_writer.py` belongs to the pre-fix reproduction
in a7772; its assertions describe the old bug, not acceptance of this fix.
Neither its historical report nor any live log, historical event, retained
divergence, snapshot baseline or missing comment is repaired here.

Remaining acceptance: house landing checks and normal deployment; observation
of real provider compaction after deployment. A new live log-world baseline
and the proposed two observed days remain Juniper's separate decision after
a full comparison is in step. This work establishes no new live baseline.
