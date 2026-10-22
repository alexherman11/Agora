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
- Cleanup retries sharing failures, accepts vanished paths, and reports retained
  paths instead of silently ignoring errors. It does not remove a fixture while
  its owned door is still running.
- Legacy `research/window-lab/.tmp-agora/` is removed best-effort and excluded
  by a rooted Git-clean exclusion. Unremovable scratch is named on stderr and
  in `house-state/landing-log.jsonl` as `cleanup-warning`. All non-scratch
  untracked files still go through Git clean; one retry handles a vanished path,
  and persistent failure refuses the landing.

An OS kill of the whole test family can bypass all Python finalizers; external
scratch may remain. This patch never discovers or stops old foreign processes
or changes their files' attributes. It prevents that scratch from blocking room
cleanup; it does not claim a general crash garbage collector.

## Verification

Run from the worktree root with the pinned interpreter:

```
C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/test_fixture_cleanup.py
C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/test_landing_queue.py
C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/health.py frontier-try --only test_fixture_cleanup --json
```

The focused suite includes a real nested Git repository and old-cleanup
reproduction, a real Windows no-sharing output handle, deterministic injection
of the two historical error shapes and vanished nested `.git` paths, actual Git
clean exclusion/source removal, non-scratch refusal, outside-room TMP routing,
and real child/pipe/output lifetime with a fake backend (no world or socket).

The ordinary real `test_visit` attempt timed out at its first `visit a9001`
request (300-second urllib timeout). Its cleanup assertion passed and its
temporary directory/world were removed. A separate bounded diagnostic attempt
failed door readiness after 60 seconds; tracebacks captured the door blocked in
`socket.create_connection` during `Door.healthy`. Its cleanup assertion passed
too. No bypass or production test was used. These are failed integration runs,
not an all-pass visit claim. Full host visit/landing judgment remains the
house's responsibility.

Handbook updates: **Commissions, workers and the keeper — Visit-test cleanup**;
**Processes and state — Test-owned door lifetime**. After source landing a
previously held commission uses ordinary `commission=ready`; do not manually
delete leftovers or repeat old process kills.
