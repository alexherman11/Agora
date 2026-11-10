# Guard diagnosis: stopped, no native retry

22 October, codex-builder-2 / worker-a9231. Scope: Rowan c10597,
JEFF e26527. Diagnose through the supported reader, preserve its reason, test
offline. A retry is conditional on an established benign/transient cause AND
fresh positive admission. Unknown/unsafe or ambiguous means stop.

## Preserved work

Ran status/log/diff before editing: receiver f337dfd, prior nine-file
checkpoint795151d. Four Python edits and two untracked reports were present.
They remain preserved; no reset, merge, restore or other-worktree edit.
Parent a8247 stays paused. Legacy runtime ownership remains UNKNOWN and
untouched under the revised independent-Job boundary.

## Source increment

`admission_job.guard_details` projects only the authoritative admitted boolean,
bounded reader reason, foreground image basename, boolean/unknown game state
and observation age. It never reimplements or relaxes policy. No title,
command line, arbitrary observation fields or private content is retained.
`require_guard` raises `GuardRefused` with that structure. Initial CLI refusal
happens before importing the launcher or allocating its state/profile/Job.
Later orchestration refusals retain the same details in `launch.json` before
returning, or through existing owned-family cleanup if already launched.

`run_admission.py --guard-status` reads the supported house snapshot once and
prints that bounded projection. It does not observe/publish new host state,
poll, instantiate a launcher, create a Job, or launch a browser. The shared
guard reader, policy and verifier were not changed.

## Ran

Pinned Python:

```
-m unittest discover -s src/desktop/browsing -p test_admission*.py
Ran 48 tests in 0.711s
OK
```

Four added diagnostic tests cover missing/stale/unknown/unsafe reason
retention, metadata bounds/privacy, read-once status without importing a
launcher, and initial structured refusal before launcher import. Existing
preflight/pre-birth/in-run tests also assert persisted refusal details.
These are fake/native-boundary tests, not native containment evidence.
Ruff E9/F passed; git diff --check passed.

Exactly one read-only diagnostic command:

```
C:/Projects/Agora4/.venv/Scripts/python.exe src/desktop/browsing/run_admission.py --guard-status
```

Exit0, printed:

```json
{"admitted": false, "foreground_exe": "pythonw.exe", "game": null, "observation_age_seconds": 7.544, "reason": "house observation stale/unknown/unsafe"}
```

Read `guard_context.py`: its age ceiling is 5 seconds, with both wall and boot
ages and policy checks required. This result is older than that ceiling; it
does NOT establish that staleness is the only failed check or a benign cause.
The reader's combined reason remains combined. `game=null` is unknown, and a
pythonw basename alone does not establish HUD identity or safety.

No second status read, native retry, public page, child, profile, Guard or Job
was created this round. No cleanup was needed or proven. No account action,
legacy process query/cleanup, live apply, host restart, settings or policy
change. Family/engine/profile/network/window/write containment, screen
continuity, screenshots and empty-Job closure remain NOT RUN. The two named
snapshot coverage limits (`family.brokered`, `writes.unscanned`) remain unknown,
never passes. No new model/runtime launched.

## Next owner and reversal

Rowan/JEFF must review the ambiguous refusal and arrange supported fresh
admission/explicit next scope. Do not republish an observation from a worker,
infer safety from an executable name, or poll until the guard permits.
No ready/landing/live-activation claim. Have the house checkpoint all seven
changed/new source/report files before replacing this worktree. Declining
this increment needs no runtime reversal; preserve its evidence and prior
checkpoint. The shared modules remain unchanged.

Raw SHA256:

| File | SHA256 |
| --- | --- |
| admission_job.py | 98821bd6aeaa442152a749553101a633f3bc2397b29678ba38f01e74204c7ff8 |
| admission_probe.py | 4159eaa0d26313d7b5448fd540c15bdb3562be1e9a3ba518022c3b4e209f7912 |
| run_admission.py | 81ea8a31f0221b504ba86828ac9a3eb9979a9daf41f674c33d23bad223ef06df |
| test_admission_job.py | 8484d8101b7b58aceac25f12e416a98bac9e2c6f06ac87ba05c74d25bb37fbf4 |
| ../native_run_verify.py (unchanged) | d51e118898dde4d952d88a3af904382e44e7f03800ce3b8f5015b1e7e96f8c7c |
