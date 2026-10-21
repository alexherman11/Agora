# Browser harness diagnostics — staged handoff

21 October 2026, worker-a8333. Harness/receipt changes only. No engine launch,
public navigation, process termination, host restart or runtime activation here.

## What is known

**Read:** the retained `retained-failure.json` is the browser owner's report:
`initialization_failed`, COMException, HRESULT `-2147467260` (`0x80004004`,
E_ABORT). It has no timing, deadline, process-exit or child-readiness evidence.
The 15-second close timer is a possible contributor, **not an established cause**.
No new screen/process/account observation was used to infer a cause.

**Ran:** the offline recipe below prints `Ran 29 tests ... OK`, startup mock
checks including `unknown cleanup: receipt/state kept, no second launch: ok`,
and 10 scripted Guard cases ending `all passed`. Its final line is
`OFFLINE ONLY: receipt tests, startup fakes and 10 Guard cases passed; no probe invoked.`
These are fake handles/clocks/metadata/processes and local fixture files, not
browser, isolation or host-cleanup acceptance.

**Correction:** the initial legacy test runs still called diagnostic helpers
with fixture HWNDs (100/777/etc.) and attempted a loopback status request.
They were not fully offline. `test_sandbox_window.py` now stubs owner/exe;
`test_sandbox_start.py` stubs urlopen. The final recipe additionally refuses
unmocked subprocess, status-network, Windows-adapter, owner/exe and CreateProcess
paths. These test tripwires are not an OS security boundary. No browser was
launched or process stopped in either run.

## Source changes and consequences

- `sandbox_receipts.py`: atomic inherited-ACL receipt replacement, common
  launch/update/cleanup lease, durable intent before effect, retained prior
  cleanup/taskkill evidence, crash-unknown reconciliation, typed redacted
  exceptions and bounded monotonic diagnostic events.
- `sandbox_owned.py`: uses the existing `hud_lifecycle.Windows` handle adapter.
  Only the supplied recorded PID's parent/profile metadata is queried by a fixed
  read-only PowerShell command. No shell supplied by the caller, alternate query
  on denial, enumeration/adoption by title, desktop or profile, or tree kill.
  Admission compares exact creation FILETIME, executable, parent PID/FILETIME/
  executable and canonical absolute profile on the **same handle** subsequently
  terminated. PID reuse means the old identity is gone, not permission to kill
  the replacement. Access denial means unknown.
- `sandbox_window.py`: retains launch intent before CreateProcess and ownership
  captured on its original process handle; a shared exclusive file lease stops
  concurrent launch/update/cleanup. Failed writes stop effects or leave a pending
  intent. Cleanup retains manifests, profiles, error and old taskkill receipts;
  failure/unknown cannot be translated into “closed.” No process-tree kill or
  window-PID adoption. Unknown cleanup stops automatic Edge retry.
- Existing startup/Guard mock tests now isolate their remaining diagnostic calls.
  New receipt tests execute the real cleanup/launch wrapper through AST extraction
  with fake dependencies, plus the actual handle admission code with fake native
  calls. No native termination is exercised.

**Deliberate compatibility limit:** legacy PID-only manifests refuse cleanup.
An absent `--user-data-dir`/`--sandbox-profile` flag is recorded as an empty
profile argument, but cannot prove an in-process WebView2 profile, so termination
is refused. Empty desktop windows cannot prove headless children exited.
The harness therefore leaves `runtime_closure=unknown` and returns `ok=false`
even after recorded owners are confirmed gone. It does not delete the manifest,
erase a profile, retry a launch or claim complete runtime cleanup.
Missing historical taskkill output cannot be reconstructed; existing recorded
output is preserved without being republished into the world.

This is process-reuse protection, **not authentication or worker exclusion**.
Manifest files and the common lock are same-user files. No trusted service,
private principal, broker, provider privilege or OS policy was introduced.
A stale lease or unknown pending effect needs host-owner reconciliation, never
automatic lock deletion or blind replay.

**Lifecycle (read):** none of these filenames is in `workshop.HOUSE_FILES`.
No change to that set, provider, house, transport, engine or HUD. New harness
invocations import the landed code; existing processes keep imported code.
Landing needs no supervisor/HUD restart. A separately approved future harness
run changes cleanup behavior as described above; it does not authorize a run.

## Exact integration for the browser owner

`probe-diagnostics.patch` is the readable unified diff for the owner's two
**unlanded** files. `probe-diagnostics.json` carries the same exact OLD/NEW
passages and normalized UTF-8/LF base hashes. No files in the other worktree
were edited. `check_probe_patch.py` refuses changed bases or ambiguous passages,
then compiles the proposed Python text without importing/executing it.

The staged hunks add:

- initialization/import phases and elapsed milliseconds;
- durable deadline event **before** form close; original 15,000ms limit retained;
- redacted exception category, exception type and numeric HRESULT/WinError;
- `BrowserProcessExited` and `ProcessFailed` events after native core creation;
- explicit navigation identity/`IsSuccess`, not just NavigationCompleted;
- a fixed child fixture's source-checked postMessage readiness acknowledgment,
  correlated with this attempt, then native evaluation of top/child bridge
  absence and message/host-object settings;
- bounded asynchronous readiness polling inside the existing overall deadline;
- separate parent-timeout receipt (does not race-write the child receipt);
- failure exit when cleanup is unknown, even with no remaining windows.

**Instrumentation gap is explicit:** with the current implicit environment
creation, native core event hooks are unavailable before successful initialization.
`process_hooks_registered=false` records that gap. No event absence in an init
failure proves the browser process stayed alive. The owner must review native
SDK event wiring and Python/.NET callback lifetime/exception behavior on a future
authorized run. The correlation token is a freshness check for this fixed
fixture, not an authorization or general web isolation boundary.

## Reviewed offline recipe (available now)

From the owning worktree, with the pinned interpreter:

```powershell
C:/Projects/Agora4/.venv/Scripts/python.exe research/window-lab/browsing/diagnostics/run_offline_tests.py
```

The browser owner can check the exact staging against its preserved source:

```powershell
C:/Projects/Agora4/.venv/Scripts/python.exe research/window-lab/browsing/diagnostics/check_probe_patch.py --source C:/Projects/Agora4/.worktrees/a8247/research/window-lab/browsing
```

**Ran:** this second command checked both exact bases and compiled both staged
files without executing/importing either. Base → staged normalized-text hashes:

| File | Base SHA-256 | Staged SHA-256 |
|---|---|---|
| native_engine_probe.py | 182327deeb01e6788c02ddaa11146334dfd5009bb15a162e4dced0afa3a18ad6 | 3580f14d85598962a9d5581749c7f60b0f3fa344c5b5cd2555981ce7f73c9639 |
| probe_hidden.py | cfd5c66663c69d86d71a2207bc15c69467a8888fe74cd54c12f868c5233529d2 | e1694bcab78aab01581fa16228edd1c0282d96ebbe233afbeadb331158cc12bb |

No real-probe command is part of this recipe. Do not run `probe_hidden.py`,
`sandbox_window.py test`, Guard `--live`, or visible fallback on this card.

## Before the next real hidden run

JEFF/host owner must reconcile the prior runtime and retained manifests and
establish how **all** engine children, including headless children and delegated
hosts, acquire exact parent/executable/creation/profile ownership before any
cleanup admission. A normal browser exit signal alone is not a containment
boundary. Unknown metadata/access denial cannot become “safe to kill.”

The browser owner reviews and integrates the staged hooks with its engine work;
JEFF authorizes one bounded hidden-Guard run after that ownership boundary is
accepted. That run must inspect actual event wiring, child-ready results,
deadline order, cleanup receipts and Guard evidence. No visible fallback.
Root cause, browser rendering/input, actual isolation and complete process
cleanup remain **not run / not certified** here.

Reversal is source-only: owner declines/reverts the staged hunks; house reverts
this harness change through ordinary landing if required. Do not use reversal
as permission to run the old unverified PID/tree cleanup. Retained runtime files
are host-owner evidence and are not deleted by either direction.
