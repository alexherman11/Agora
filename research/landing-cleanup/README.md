# Visit fixtures and landing cleanup

Source prepared for commission a9652; not a live-process cleanup tool.

## Cause (read, then reproduced offline)

`test_visit.py` creates small independent Git repositories, not registered Git
worktrees. It used inherited TMP, which landing health points inside the landing
room, and `shutil.rmtree(ignore_errors=True)`. Git objects on Windows are
read-only: a real private repository reproduces the silent leftover with that
old cleanup. The test also forcibly terminated its door and slept 3.5 seconds
for orphan watchdogs instead of joining owned child processes. Visit cleanup
threads can outlive their removal from the door's version map.
JEFF's later third case (e23253) found the same ignored-removal pattern in
`test_preserved_work.py` (`bring-*`) and `test_landing_queue.py` (`lq-*`).

The reported historical errors fit two independently reproduced failure modes:
held files/directories refuse removal, and a concurrent remover makes paths
disappear during traversal. No historical holder PID or unique cause of either
old incident was established; neither incident was replayed on the live room.

## Repair

- Landing health supplies `AGORA_VISIT_TMP=<live house-state>/test-visits`,
  outside the landing room. This does not relax `agora_tmp`'s worktree boundary.
- Test visits create directories with inherited permissions. Only their own
  Git fixture files have the read-only file attribute cleared during cleanup;
  no security ACL is changed.
- The opt-in `door.py --lifetime-stdin` closes on parent pipe EOF. The test waits
  for that exact owned process, not a PID discovered later. Shutdown stops the
  watch, waits for an in-progress visit start and retired visit cleanup threads,
  and reaps owned backends. Spawned output handles close in the parent.
  A killed child is waited for before removal.
  Every door subprocess (Git and backends) gets `stdin=DEVNULL`: none uses
  stdin. On Windows, inheriting the pipe while the lifetime reader blocks can
  stall child startup until EOF. This caused the first rejected landing; the
  control regression reproduces it without a world or socket, then proves the
  actual Git/backend spawn paths work while the lifetime pipe remains open.
- Visit startup retains bounded door/backend diagnostics on failure, and
  registers ownership before readiness. Cleanup checks every started door,
  including one that failed to become ready, before removing its fixture.
- Cleanup retries sharing failures, accepts vanished paths, and reports retained
  paths instead of silently ignoring errors. It does not remove a fixture while
  its owned door is still running.
  Preserved-work tests now assert private Git fixture cleanup in `addCleanup`;
  landing-queue tests explicitly check it before choosing their exit code and
  report early-exception cleanup through `atexit`. Both clear only their own
  Git objects' read-only attribute and retry races, rather than ignore errors.
- Legacy `research/window-lab/.tmp-agora/` is removed best-effort and excluded
  by a rooted Git-clean exclusion. Unremovable scratch is named on stderr and
  in `house-state/landing-log.jsonl` as `cleanup-warning`. All non-scratch
  untracked files still go through Git clean; one retry handles a vanished path,
  and persistent failure refuses the landing.
  The exclusion covers the entire rooted scratch directory, including
  `test-visit-*`, `bring-*` and `lq-*`; it is not a name-specific workaround.

An OS kill of the whole test family can bypass all Python finalizers; external
scratch may remain. This patch never discovers or stops old foreign processes
or changes their files' attributes. It prevents that scratch from blocking room
cleanup; it does not claim a general crash garbage collector.

## Verification

Run from the worktree root with the pinned interpreter:

```
C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/test_fixture_cleanup.py
C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/test_preserved_work.py
C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/test_landing_queue.py
C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/health.py frontier-try --only test_fixture_cleanup --json
```

The focused suite includes a real nested Git repository and old-cleanup
reproduction, a real Windows no-sharing output handle, deterministic injection
of the two historical error shapes and vanished nested `.git` paths, actual Git
clean exclusion/source removal, non-scratch refusal, outside-room TMP routing,
and real child/pipe/output lifetime through the actual backend constructor
(fake service, no world/model). A Windows negative control proves the
inherited-stdin stall and its release at EOF.

The first implementation failed house judgment: door readiness timed out after
60 seconds. Earlier local runs also timed out at readiness or the first visit;
cleanup passed. These were real failures, not established sandbox limitations.
The Windows inherited-pipe regression above accounts for them. Disconnecting
only backend stdin fixed readiness but left Git stalled at entry; all five
subprocess paths now explicitly disconnect stdin.

**Ran after repair:** 14 focused tests pass. Partial health on frontier-try at
e23214 (23217 events) passes Python, scripts and test_fixture_cleanup in 4.3 s.
The revised preserved-work suite passes 19 tests in 35.108 s (one nonfatal
ResourceWarning printed); its per-test cleanup assertions pass. The revised
landing-queue suite prints `all passed`, including new check 21 that its private
repositories and lock scratch were removed.
The real `test_visit` now enters a9001 in 1.6 s and passes through isolation,
pinned commits, switching versions, joining and refusing a broken version.
It then stops at the existing crash fixture: `taskkill` of its own reported
version PID returns `ERROR: Access denied` inside this sandbox. The test now
checks that exit code and names the blocker; previously it ignored the failed
kill and produced 13 misleading downstream failures. Cleanup still passes.
Crash recovery and the subsequent real-door restart are **not verified here**.
No process-access bypass, model call or production test was used. The house
must run the complete integration suite and judge landing.

An interrupted diagnostic left its own roomworld-visit-41704-try fixture.
Runtime process enumeration was denied; no unverified process was stopped and
no broad leftover cleanup was attempted. Sessions are excluded from landing.

Handbook updates: **Commissions, workers and the keeper — Visit-test cleanup**;
**Processes and state — Test-owned door lifetime**. After source landing a
previously held commission uses ordinary `commission=ready`; do not manually
delete leftovers or repeat old process kills.
