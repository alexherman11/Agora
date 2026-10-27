# Store journal cache repair — independent review requested

Author: codex-builder-1, worker-a13300, 23 October 2026. This author also reproduced A2 on review card a12981; this repair requires a different builder's review. Staged source only, no ready, landing, runtime reload or live mutation.

## Result and exact scope

The inherited A2 reproduction now refuses stale memory through the unchanged atomic kernel. A valid equal-length replacement changes title One to Two and carries its matching state digest; no manual cache eviction occurs. Same-bytes rotation still recovers, and ordinary successful appends still serve their verified cached facts.

Only production change: `research/text-desk-lab/notation/store.py`. Added regression: `test_journal_cache.py` beside it. No atomic_world, carry, route, dispatcher or world-policy change. Coordinated on a7606/c13332 and a12833/c13334; their own A1/B findings and review gates remain independent.

Base commit: 8525c2c618909f716e560f408d116049d50a1c53.
Base store blob: a078b9110260c23cb54f1b855f8be2a2b188cdc0.
Current main checked read-only: 6fa8ecb12c5150331af5074ff3581c3ea3b4d4b6; store.py has no base-to-main diff at that check. This is source compatibility, not whole-main health or approval of another source union.

Frozen exact patch SHA256: bec49076d5395b22b1a35198de5bbaeb5d209a1be33c01d63fd2e2dc02037a80.
Candidate store.py SHA256: 2395bfef20fb4e6883b4f287e99f6cc022f39d98d4c6ecafb130e0c3357eb785.
Regression file SHA256: 68aa114ed6264a10372947771f3edb90dabb10f9b8d62096e444ee6385246cd7.

`inventory.json` includes base hash and exact file sizes. `candidate.patch` contains only the two source/test paths above. `freeze.py` writes these review artifacts using read-only Git queries, without index/object/ref writes. All files remain preserved uncommitted in this worktree for supported house checkpoint/transfer; no ad-hoc cross-worktree copy.

## What changed

- Cache entries retain the original size/sequence/digest/facts slots and add a file stamp: device, inode/file ID, birth time where available, size, nanosecond mtime and Unix ctime.
- `head()` reads the real complete tail record instead of trusting its own cache. It compares path/handle identity and before/after stamp, invalidates stale cache entries on stamp or sequence/digest changes, and refuses a witnessed read race.
- `flat()` reuses cached facts only after that validation. Otherwise it replays from byte zero into fresh facts, checks unchanged stamp/head and agreement between replay and head, then publishes its cache. A raced replay leaves no entry to reuse.
- Ordinary `begin()` benefits from `head()` invalidation before its existing weak world/path/size quick-path mark; it cannot reuse old cached facts on a replaced journal. Its outside-change recording policy is unchanged.
- Append retains its record encoding, sequence choice, torn-tail handling, write/flush/fsync, result and fact format. It stamps the actual written handle, then caches supplied facts only if the path still denotes that version. This changes cache publication, not commit acknowledgement policy.

Deliberate tradeoff: an unverified version change causes full replay, even if it might be an external append. Successful local appends supplying facts remain cached. There is no performance gain claim and no assumption that a larger file has an unchanged prefix.

Windows detail, measured on an owned seven-byte scratch file: Python path stat's legacy ctime was birth time, while fstat's ctime was change time. Comparing those falsely refused normal reads. The stamp uses explicit Windows birth time and mtime; it excludes that incomparable Windows ctime. Actual tail sequence/digest is always read, including a synthetic unchanged-stat-version test. Unix ctime remains a version check. This is ordinary filesystem identity/version checking, not protection against an adversary forging a journal digest or every filesystem timestamp.

## Executed evidence

All tests use synthetic state, owned test scratch and no supplied world, browser, server or model. The kernel fixture uses production Session locks with an in-memory loader.

- Baseline store, before production edit: 8 focused tests ran in 0.522s; 4 failures, including exact A2's missing UnknownCommit, replaced head, same-bytes rotation not replaying and same-file rewrite returning old facts.
- Final journal cache suite: **14 tests in 0.423s, OK**.
- Atomic kernel suite: **38 tests in 1.859s, OK**.
- Log-world suite: **42 tests in 8.972s, OK**.
- `test_store.py --quick`: **all passed**, 268 records (genesis1, command266, outside1); final replay/round-trip assertions pass.
- `git diff --check`: exit0.

The focused matrix includes actual equal-length replacement head and replay, same-bytes rotation/recovery, same-file rewriting, actual tail digest with a deliberately frozen stat version, tail sequence changes, growing replacement, truncation, disappearance, ordinary local cache reuse, an external append, ordinary begin's stale-cache exclusion, and replacement during replay with no cache publication. The A2 alternate journal is independently replayed under its own path before replacement, confirming title Two and matching digest.

Earlier development failures remain failures: the first stamp comparison produced 7/8 focused errors, 28/38 atomic errors and a store-quick exception because Windows ctime differed between path and handle. The stamp comparison was corrected and those production suites rerun. A later rotation fixture used a too-short operation ID and errored; correcting only that test ID and adding the begin regression produced the final 14-test pass. Those were implementation/fixture errors, not environmental waivers. Final exact stdout/stderr and exit codes are retained in this directory; no whole-health or production claim.

To rerun the complete isolated matrix:

```
C:/Projects/Agora4/.venv/Scripts/python.exe research/store-cache-review/run_checks.py
```

To regenerate the review-only diff/inventory without Git writes:

```
C:/Projects/Agora4/.venv/Scripts/python.exe research/store-cache-review/freeze.py
```

The runner supports one suite name for a focused rerun; results.json records each suite and production/test hashes. It propagates failed exits.

## Review gate and rollback

Please assign an uninvolved builder the two exact files plus patch, inventory, this note, runner and retained outputs through the supported house route. Review identity/version checks, head content validation, ordinary begin's cache path, replay-race refusal, Windows comparison and successful-append cache behavior. Re-run the tests independently; this author's passes do not certify review.

No cache repair approval clears a7606's separate no-event `_log_at` trust or post-recovery narrow-fence ordering blockers. Pike's route kernel union still needs its own tests. No source/runtime activation on this card before review and lead disposition. Rollback after any eventual landing is one revert of this narrow source increment; no world changes or data restoration are needed.
