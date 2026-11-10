# Browser Job integration — offline checkpoint, not native acceptance

21 October 2026. Worker-a9231 / codex-builder-1. Rowan's c10145 is the
bounded implementation authorization. No native launch, host process query,
cleanup of an existing runtime, public page, activation or landing this round.

## Received base and scope

Base HEAD: `433a9b5a1ae9824e46a8392a4e493abf00df01bf`.
House transfer `f472345d1e4b92ac462aac0780fa0e4f18f1fb60d40301581b44bf0960132f89`,
source `daaf123c196fd5f80396a8ac31f69c6013b763cc`.
Ran raw SHA-256 comparisons: all six received files match that manifest.
The received shared modules have not been edited:

| Shared module | SHA-256 |
|---|---|
| guard_context.py | dd67351d71311cc254cdb1f82c256346eeb8e3600d926ca20b6197d98d5a7ba5 |
| sandbox_birth.py | 6857f08867e5ad36f029a5c97234ee6e806448237d675eb1c91c919aeff57690 |
| sandbox_job.py | c8e64ab3f68fc0d48dfb2826c2c79101ab493f73cdee45b9540eaccbda88fb72 |
| sandbox_owned.py | 0a94ce253cadf78420cdd91728b82e3b026cbcc83af94b40d1d6a85aa3e27182 |
| sandbox_receipts.py | 3216c1d5e2735bbf151bea47e229aec0fc608fcbf6f1d0878284ff872f3d0e83 |
| sandbox_window.py | 1f158a3a4987666e6eda14617953686e70414655714e9eb7c50ff98984f46770 |

Read shared start/close, Job Scope and cleanup, birth receipt validation,
Windows identity adapter, fixed-path guard consumer, takeover source and the
landed diagnostics handoff. The imported local dependencies are present.
Compiled the six received modules plus agora_tmp, hud_lifecycle, screen_tools,
and the five admission modules without importing/executing native code.
This establishes Python source coherence, not installed .NET API compatibility.

JEFF e24262 / Rowan c10121 supersedes the earlier all-legacy-reconciliation
precondition in ADMISSION-REVIEW-a9231.md. Legacy runs remain UNKNOWN and
untouched. They do not by themselves block a separately enrolled new family.
This does not authorize a launch. Parent a8247 stays paused.

## Source changes

- `run_admission.py` no longer uses the hardcoded game list or any WMI
  discovery/name match as runtime-closure evidence. Uses the current world-owned
  guard reader; retains the shared Job through shared close.
- `admission_job.py` exercises the shared suspended birth API and shared
  receipt writer. Validates the recorded root and Job, then opens and pins
  the engine handle. Requires matching request/root, fresh engine creation,
  msedgewebview2.exe image, live kernel Job membership and a complete active
  snapshot. Unknown identity, older/reused engine, missing membership or changed
  request refuses. No engine termination by PID, adoption, legacy query or
  retry. Cleanup calls only shared close while the same Job scope is live.
- Shared cleanup's archived receipt must match the Job and prove an empty
  PID list; only then is job_closure reported proven empty. Failed persistence,
  pending/unknown effects, missing receipts and exceptions stay unknown.
  KILL_ON_JOB_CLOSE is a backstop, never an empty-job observation.
- Parent deadline remains 40 seconds, child deadline remains 25 seconds.
  Explicit parent timeout is retained. Fresh guard is required before launch
  and throughout polling. Local Guard's separate verdict is retained.
- `admission_probe.py` installs offline refusal hooks before fixture content,
  checks the fresh InPrivate profile, and waits for parent engine admission.
  Rejects changed Core engine PID and closes on ProcessFailed. Keeps timers
  alive and disposes them. Existing positive/disabled native message controls
  are preserved.
- `admission_policy.py` disables host objects, devtools, autofill/password
  save, context menus, browser accelerators and script dialogs. Only the fixed
  positive control enables web messages. Denies non-fixture top/frame navigation,
  all resource sources, popups, permissions, downloads and external schemes.
  A missing required API aborts initialization, not policy installation.
- `admission_result.py` also rejects an explicit engine_refused event.

The per-run JSON request/response is trusted fixture coordination and freshness
checking, NOT an authenticated host channel, worker exclusion or a new service.
JSON grants no authority. The parent uses kernel handles to establish enrolled
membership; it cannot certify an arbitrary same-user writer's fixture report.
This harness must not be exposed as a public/worker host-command capability.
No host object, HUD bridge, public-page mode or private account path is added.

## Ran

Pinned Python:

```
C:/Projects/Agora4/.venv/Scripts/python.exe -m unittest discover -s src/desktop/browsing -p test_admission*.py -v
Ran 38 tests in 0.630s
OK
```

24 Job-orchestration tests use actual shared Scope, birth persistence and
cleanup logic with fake process/Job adapters; six event-policy tests invoke
the actual handlers with fake Core/event arguments; eight message-receipt
regressions remain passing. Subprocess and WinDLL tripwires supplement the
fakes; they are not a security boundary.

Coverage includes admission ordering, stale guard, unknown/out-of-job/old engine,
birth race, changed request, wrong image/child receipt, partial start,
explicit deadline, normal engine exit before the final child receipt flush,
cleanup/persistence failure, unknown-effect non-replay, retained-folder
non-overwrite, redirects/top/frame/external navigation refusal, resource
SourceKinds.All (including fake worker sources), permission/popup/download
refusal, missing policy API, settings and message-channel regressions.

`py_compile` and `git diff --check` returned exit 0. Full health and the older
native-importing diagnostic recipe were not run. No test imports sandbox_window
or instantiates the Windows adapter. Fake files live under this worktree's
inherited-ACL .tmp-agora; no old fixture or session was read or modified.

## Exact source hashes

All paths below are in src/desktop/browsing.

| File | SHA-256 |
|---|---|
| admission_job.py | 666ab9f966c1cda2409f37ec43215a78a2a3e624c9a44ba1ad394b4cb4bc2f38 |
| admission_policy.py | 27ceba5a8ecd04351e880720daf374c164ca7e021205e2e9b636ee13652a837a |
| admission_probe.py | a5f7b88c924f58b90246269e02d412857361017ac3bbfdf515adca7116b34f7b |
| admission_result.py | 8ac05356fd42038677c2126f52143c2df3ad217f31ce9561224ba4e65cb2f77a |
| run_admission.py | de2fdcd779a915631e0f5842b89bb59d4fd7492b85cc06c38be10d352bed1749 |
| test_admission_job.py | 49a12d539a6bd4260413925dd16df83adeb6bad80313e5da7f98973ec4546ffc |
| test_admission_policy.py | 01a239a4df6684288f98c81689d1a091ba018f11d6e225fcd16b165ac5fccf78 |
| test_admission_result.py | ea4405227078152a96a1329cced00fdfa354132b0e88930d9ecad1ac2f664735 |

## Remaining acceptance and reversal

STOP before native execution for Rowan's review, as c10145 requires.
Not proved: installed SDK event wiring, child/top/worker enforcement in an
actual engine, native host-object adversarial attempts, redirected/child
requests actually reaching refusal hooks, same-user report integrity, native
profile isolation, network/filesystem side effects, actual empty-job cleanup,
native Guard continuity or any public-page rendering/input. No screenshots.
The first guarded lane still needs independent containment acceptance and
fresh world guard admission. A public page and world navigation/control
integration remain separate later steps; no fake browser chrome is offered.

New lifecycle source: none. No HOUSE_FILES/provider/house/transport edits,
new port/service, security settings or runtime activation. These are harness
files only; do not ready/land as a substitute for review or run admission.

Source is preserved uncommitted in this card's worktree. Have the house preserve
this exact patch before replacing the worktree. Reversal is to decline these
eight source/test changes and this note relative to base 433a9b5, through the
normal house source path. Preserve existing handoff documents, native/legacy
receipts and profiles. No source reversal is permission to run the old launcher.
