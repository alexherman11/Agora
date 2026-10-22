# Effective host and enumeration checkpoint — design only

22 October 2026, worker-a9231 / codex-builder-1. Authority: Rowan c11088,
JEFF m11087. No production implementation, native query, retry, prepare or ready.
The previous eight edits/reports remain intact.

## Evidence and limits

Read the retained a10815 receipts, not running process metadata. Recomputed:

| File | SHA256 |
| --- | --- |
| launch.json | 8cd2578d73d09d820c2d16c141c0ebbe7b68c01f44ba6ff07d7586184fc92b46 |
| receipt.json | d4a25218d4ff7928693148193f7841eec2ce02632527724b6f97e5538af4cf14 |
| source.json | 8fbbcc2a92ed3631d777bf9450e519cea69f8ad2548a234a460e84a1b36ae4d8 |

The receipt is still `importing`, PID29228. Retained evidence records root96436,
descendant29228 and conhost85796 in the held Job, followed by verified empty
cleanup. No new process observation or cleanup occurred. Venv redirection is
still a hypothesis, not a proved identity rule.

## Smallest proposed binding

Keep launcher birth/root and effective fixture host as separate identities.
Do not change sandbox_birth's direct-child definition or substitute a reported
PID for it. Do not accept an arbitrary member simply because it is in the Job.

Before any future launch, the parent must possess an explicitly reviewed exact
allowed effective-interpreter image identity (canonical path plus content hash).
The launched executable may match directly, or an independently admitted
interpreter may be reached by a bounded measured ancestry chain. Do not derive
that allowlist from the child's receipt, executable basename or an assumed venv
relationship. No such extra admitted interpreter identity is established by
this checkpoint; that remains a review prerequisite.

Treat a fixture PID as a candidate only. Open and retain read-only process
handles; measure creation time and image from those handles; require live,
unchanged identities and membership in the same retained Job. Measure parent
links, reject loops/missing ancestors, require nondecreasing birth times back
to the exact retained root, and recheck each identity and Job membership after
the chain is collected. Parent PID alone cannot resolve recycled identities.
Bound depth; ambiguity, disappearance, denied access and missing provenance
refuse. Pin exactly one effective host for the run, never follow a replacement.
Retain the root checks and original Job cleanup path.

Bind ALL envelope consumers to the resulting parent-owned tuple:
request token, Job identity, launcher birth, effective-host birth/image, named
desktop and fresh profile identity. Specifically:

1. `receipt.json`: pending/importing and every later phase must match the same
   effective host; no child record alone supplies measured birth authority.
2. `engine-request.json`: same host, token and expected profile; engine PID
   independently measured/pinned in the Job, with measured provenance to the
   admitted family. The shared verifier's current all-member checks remain.
3. `engine_report()` callback: use the same pinned host/fence, not a second
   self-consistent JSON-only acceptance path. Read stable envelopes and recheck
   pinned handles around the read; changed/missing envelopes are unknown.
4. `engine-admission.json`: echo both host/root bindings and engine birth; the
   fixture checks its own PID, token, engine and profile before navigation.
   These file messages are run correlation, NOT an authenticated host service.
5. Final success requires unchanged bindings, the existing verifier verdict and
   actual empty-Job receipt; phase=`child_exit` cannot bypass admission.

Every additional engine process remains subject to shared measured family
checks; reported engine PIDs/kinds do not grant authority. This does not solve
brokered descendants or snapshot privacy limits, nor authorize public browsing.

## Enumeration diagnosis and proposal

Read `Native.processes()` and `Native.desktop_window_owners()`. Current
Process32Next completion leaves its last error unchecked; current window code
does not clear last error before enumeration. It raises on false+18 with no
windows, accepts false+18 with partial windows, and accepts false+0 as empty.
Offline fake API fixtures reproduce those three SOURCE paths. They do not show
which occurred inside Windows in the retained run.

Microsoft documents zero EnumDesktopWindows return as failed/unable to
enumerate, with GetLastError and callback failure reporting. It does not
document error18 as a modern empty-desktop certificate:
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumdesktopwindows
Process32Next documents ERROR_NO_MORE_FILES:
https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-process32next
Thus inherited Toolhelp last error is a possible explanation, not a measured
cause. Even proving a stale code would not make a false BOOL a successful scan.

Propose clearing last error immediately before enumeration; capture BOOL/error
immediately afterward, before cleanup. Track callback failures explicitly
(including GetWindowThreadProcessId returning zero); never let a ctypes callback
exception disappear into an apparently successful scan. Persist bounded API,
BOOL, error, visited count and callback-failure metadata, without titles/content.
Any false BOOL or callback failure stays unknown, including zero error or
partial results. Only true completion with no callback failure can report empty.
Process enumeration similarly distinguishes expected Toolhelp completion from
unexpected errors; a partial snapshot is not complete provenance.

## Bounded scope, owners and tests before implementation

| Proposed file/hunk | Scope and coordination |
| --- | --- |
| browsing/admission_job.py | Browser owner Rowan/a9231: one effective-host fence, run receipt validation, EngineFence and engine_report consistency |
| browsing/admission_probe.py | Same owner: echo/check run binding in all envelopes; no engine/navigation policy expansion |
| browsing/run_admission.py | Same owner: supply reviewed interpreter identity and use single fence-aware report callback; no guard-policy change |
| browsing/test_admission_job.py | Browser fixtures: direct and measured descendant success; wrong image/hash, recycled PID, unrelated member, missing/looped ancestry, changed host, wrong token/profile/Job, raced report, handle closure and unchanged cleanup |
| native_run_verify.py | Shared verifier a10179; coordinate Rowan browser and Mica AgoraMail BEFORE edit: Native process/window enumeration diagnostics and fail-closed completion only |
| shared verifier tests | Fake API BOOL/error/callback/partial/Toolhelp completion matrix; preserve existing verdict and must_prove semantics |

No sandbox_window/job/birth changes, house/provider edits, authority service,
world lens changes, new process launch or deployment effect is proposed.
Before implementation, Rowan must accept scope and the shared owners must
review enumeration compatibility. Full existing offline suites plus the new
negative matrix are required; none certify native behavior.

Reversal: this round adds only this design and a separately named offline
characterization test. Exclude those two files to reverse it; do not revert
prior preserved edits/reports or delete retained run evidence. Future production
hunks require their own exact base/output hashes and reviewed reversal.

## Ran this round

- Pinned Python unittest discovery, `test_enumeration_design.py`: Ran 6 tests
  in 0.001s; OK. Five invoke the actual shared enumeration method using only
  fake APIs; the sixth covers proposed callback-failure classification.
  The classifier is an unwired design fixture, not production certification.
- Pinned Python unittest discovery, `test_admission*.py`: Ran 48 tests in
  0.609s; OK. No native initialization or browser launch.
- Rehashed all nine runtime source files named by the retained `source.json`:
  Changed: []. Existing staged source is unchanged from that run.
- `git diff --check`: exit0. No full health, real API enumeration, effective-host
  binding implementation or native acceptance run was performed.
- Characterization test SHA256:
  4126f827881dc7e96a19885085f51e7c404a063a061b27759754878fa4e19de6.
