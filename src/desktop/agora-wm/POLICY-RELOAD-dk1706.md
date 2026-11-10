# Current resolution: no supported live policy replacement

**4 November 2026:** no supported hot replacement still holds. Use
[the joint dk1706/dk2125 handoff](SHARING-CLOSEOUT-dk1706-dk2125.md) for current
source, test and activation status. Test counts and draft details below are
historical; none verifies the latest sharing corrections.

This section supersedes the earlier design preserved below. House generic
review passed `7a7c49e22c0af99a8f8ffb57374bdd59d8a2fea7`; this worktree contains
uncommitted corrections to that commit. No source has been activated.

## Imported-code provenance

`policy_reload.py` now contains read-only `PolicyStatus`, not a loader.
At startup, before the intent thread can arm live, it snapshots actual
`__code__` objects of Manager/Native direct methods and local top-level functions
in manager/win32_host. Canonical structural hashes include bytecode, arguments,
constants (including nested code), names, flags, line/exception tables and
qualified names. Only checkout filenames are excluded. No source is read.

`wm.policy` returns `runtime_code_sha256`, the per-symbol `code_manifest`,
Python cache tag and optimization level. It does not return a disk-source
hash under a loaded-code label. `compiled_manifest` compiles House-supplied
reviewed bytes without execution, for an independent per-symbol comparison:

```python
from pathlib import Path
from policy_reload import compiled_manifest
expected = compiled_manifest({
    n: Path(n).read_bytes() for n in ('manager.py', 'win32_host.py')
})
# House compares expected exactly with wm.policy rows[0].code_manifest.
```

Use the same pinned Python build and optimization. This is explicitly a
startup snapshot of the declared function/method scope, not an attestation of
globals, defaults, imports, DLLs, other classes, or the entire running process.
It does not claim continued integrity after external monkeypatching.

## Watchdog stall finding

The existing three-second watchdog has no reservation/handoff protocol.
Heartbeat calls between operations cannot bound a blocked filesystem or OS
call. A helper keepalive would weaken the existing recovery rule by keeping a
stalled manager alive. Timeouts cannot cancel arbitrary Python/Win32 execution
safely. Neither approach is authorized here.

The correction removes source reads, compilation, native admission/enumeration,
lease calls, class swapping, rollback state and request scheduling from the
reload path. Both reload/rollback refuse immediately, including with a valid
reviewed hash. No policy request enters the owner-thread queue, waits on its
lock, or runs on tick. The ordinary controller tick/request/lifecycle logic
and watchdog retain their landed fullscreen behavior. The strict helper added
only for reload is removed from win32_host; native safety is otherwise unchanged.

This resolves the added stall hazard by removing the unsafe operation. It
does not claim to eliminate the pre-existing watchdog recovery behavior or
provide a replacement mechanism that preserves claims across process exit.

## Exact lifecycle exception needed, not granted or executed

There is no safe hot bootstrap in the old running WM and no supported
arrangement/claim-preserving restart. JEFF's prohibition on off/on and geometry
release remains in force. The minimal available lifecycle is **one WM-only
off/on**, requiring a separate explicit authorization that includes its effects:

> Authorize JEFF, as kernel-world steward, to perform one `off wm`, verify the
> old WM manager has exited and its existing watchdog has completed
> identity/cookie-checked lease release, then one `on wm` against independently
> reviewed source. Authorize WM process termination (including the existing
> host's two-second stop fallback), temporary WM grant revocation/restoration,
> release of saved geometry/styles/claim cookies and fresh live lease/claims.
> Accept that current window geometry may change. No app/window-host/kernel
> restart, app closure, draft reload, settings rewrite or retry is included.

The target is WM module `dk532`, desktop owner Alex `dk2`; JEFF `dk827` is the
steward/resolver. The existing world words are `off wm` and `on wm` (confirmed
by read-only help). `Host.reconcile` starts absent/dead modules only;
`ModuleProcess.stop` sends off then may kill the WM manager after two seconds.
WM's finally block calls `Manager.switch('off')`; watchdog release restores
saved placements/styles only where identity and cookie still match. Release
failure can leave entries/claims unresolved. A fresh manager reuses its existing
home/screen.json pins/adoption and standing world settings, but does not retain
the old in-memory layout, pending intent or lease. Normal live startup can
rearrange windows; exact preservation is not promised.

Before such an exception can be exercised, House must independently review
the new source, supply fresh unchanged-policy admission and complete guarded
hidden feature checks. House must also establish the actual `run` target is
the reviewed source; a branch commit or a changed path does not establish this.
After off, do not on until old-process exit and complete lease release are
independently confirmed. On timeout, denial, incomplete release or mismatch:
stop and report; no retry, manual claim clearing, recovery script or alternate
termination. If that geometry/claim exception is unacceptable, activation waits
for a separately permitted lifecycle opportunity. The worker executes neither.

## Current focused checks and remaining blockers

Ran pinned Python `-B -m unittest -v test_policy_reload`:
**Ran 8 tests in 0.024s, OK**. These use source/in-memory fixtures: imported objects
versus independent compilation (including actually imported Manager and native
code objects without native initialization), changed source/nested code, method replacement,
no source/native access, snapshot immutability, principal checks and immediate
reload/rollback refusal with no queue/lock/manager/lease work. No temp directories,
native initialization, guarded fixtures or denied-operation retries. An earlier
production fixture check failed because compiling extracted definitions changed
Python's import-aware optimization; the corrected fixture retains the whole
module compiler context. That was a fixture failure, not a denied operation.

For independent House execution from agora-wm:

```text
C:\Projects\Agora4\.venv\Scripts\python.exe -B -m unittest -v test_policy_reload test_fullscreen_delivery
```

Also execute existing `check_dock_delivery.mjs` using an approved installed Node
runtime. The existing focused fullscreen/controller and seven shipped dock
click cases remain supplied but unrun by this worker. No installation.

Still blocked: independently reviewed new source, kernel House-owned admission
repair (exact rejection in world note `dk1716`/`r3702` and historical section),
guarded hidden dock/native maximized/borderless and remembered-bounds proof,
explicit lifecycle exception or permitted opportunity, narrow shell activation
and owner outcome. Generic review of the earlier commit is not acceptance.
Exclusive fullscreen remains unsupported. No publication or activation is
recommended from these source-only checks.

---

# Superseded design: WM policy handoff draft

Everything below is retained as historical design/evidence. Its reload commands,
API, tests and claims describe the rejected earlier draft, not current source.

JEFF authorized this delivery repair on the existing task. Nothing here has
been activated. Do not off/on WM, release geometry, retry the guard, or restart
any live service. This does not add exclusive-fullscreen support.

## Reuse the existing owner and lease

**Read:** `Host.reconcile` has no cooperative reload command; changing `run`
does not reload a living module. `modproto.Module` already routes WM words to
the module, and `WMModule.tick` serializes native operations on one thread.
Its existing watchdog can remain alive, with its original owner PID, socket,
lease file and per-window claim cookies. No new process/supervisor is needed.

**Implemented, unrun:** `policy_reload.PolicyReload` stages compatible
definitions in isolated dictionaries, checks state again, then changes the
classes of the existing manager/native instances on the WM thread. It does
not reconstruct their state, replay layout, call constructors, reacquire or
release the lease, reoffer words, change grants or transfer process ownership.
Original `WindowRef`/`Rect` classes and imported module namespaces remain in
place. The native candidate uses the original reference class, avoiding
dataclass identity mismatches across a reload.

Permitted source changes are Manager policy methods/module functions,
`Native.windows`, and `covers_monitor`. AST comparisons freeze imports,
constants, constructors, Manager.switch, native check/mutation methods,
WindowRef and other native helpers. Byte comparisons additionally freeze
engine, feel, watchdog, controller, this receiver and modproto. This intentionally
cannot load arbitrary WM upgrades or migrate an incompatible state schema.
Candidate bytes need independent review; a hash is an identifier, not proof of
review or containment of hostile Python.

Each source read is limited to 256,000 bytes. Staging rejects class initialization,
decorators, annotations and executable default expressions; special Manager
methods remain frozen. This avoids executing initialization while defining
candidate methods. It is not a sandbox for unreviewed code.

`wm.policy` reads the loaded and rollback hashes. A desktop steward can request
`wm.reload sha256=<independently reviewed bundle digest>`; `wm.rollback
sha256=<retained previous digest>` restores only the previous code generation.
Neither word belongs in the shell grants. Existing WM caller/permission checks
still apply, and the new operations also require steward membership.

The bundle digest covers file names, lengths and bytes of both policy files
and all fixed files. House can compute it, without native imports, with the
pinned interpreter in the agora-wm directory:

```python
from pathlib import Path
from policy_reload import POLICY, FIXED, digest
print(digest({n: Path(n).read_bytes() for n in POLICY + FIXED}))
```

The exact hash must be computed again on the independently reviewed checkout;
do not substitute this worker's self-proof for House review.

## Refusal and rollback contract

Requests carry a two-second monotonic deadline inside the existing four-second
controller request timeout. The receiver binds to the first `tick` thread,
not the protocol reader's hello thread. It refuses wrong-thread execution,
expired requests, non-live/unarmed state, panic hold, shutdown, queued settings,
backlog, another queued action, drag/preview/share transactions, pending native
acknowledgements, initial boot or an already-gated controller.
Unread native hook events are retained in the controller backlog and refuse
the handoff. A thread-binding failure returns before settings or layout.

It uses uncached, original gaming gates without a share exemption. Strict
original `reload_context` also requires notification state 5, Default input
desktop and a known foreground process/window identity. Missing/unknown
inspection and busy/fullscreen notification states refuse. Context is sampled
around native enumeration. Window keys/identity records, rectangles, visibility
state, maximized state, normal/preferred bounds, ownership and work area must
match the controller observation and remain stable through staging and commit.
These are bounded observations, not a claim to prevent every concurrent OS
change between instructions.

Only heartbeat messages go to the same lease during staging and observation.
Candidate methods are not run on live state during staging: class-layout
compatibility is checked on disposable shallow copies. A changed source read,
hash mismatch, unsupported ABI or compilation failure leaves original code
active. Failure during commit restores the old classes and gate reference
before the next tick. Both success and refusal end that controller tick without
ingest/apply.

After successful handoff, one previous code generation remains in memory.
Explicit rollback requires the same safe/settled conditions and pinned previous
hash. It keeps **current** state, bounds and claims; it does not undo user actions
or restore old screen geometry. There is no automatic retry or oscillating
fallback loop. Once ordinary layout resumes, a later policy bug is not claimed
to be a reversible screen transaction.

### Unresolved activation review limits

The initial `loaded` digest describes files read at receiver initialization.
It does not independently attest that those bytes match every already imported
code object. House must establish a coherent, reviewed bootstrap snapshot;
`wm.policy` alone is not evidence of code provenance.

Source size and request deadlines bound data and admission, not wall-clock
latency of filesystem or OS calls. A stalled read/observation could exceed the
existing three-second watchdog deadline, whose recovery releases saved geometry.
The receiver does not disable that watchdog. Same-process handoff therefore
does not yet prove preservation under stalls. Independent review must resolve
this before activation; do not treat this draft as a safe bootstrap decision.

## Bootstrap is still blocked

The live WM predates both the fullscreen patch and this receiver. It cannot
receive these new words or execute newly written source. The receiver also
deliberately freezes controller/lease ABI, so it cannot retrofit itself through
an old generic action. No supported existing hot-load hook was found.

Consequently this draft solves compatible policy handoff **after a reviewed
receiver has been loaded during a permitted lifecycle opportunity**. It does
not satisfy immediate live delivery under the current no-restart/no-off-on
constraint. JEFF/House must retain that blocker and determine a separately
permitted bootstrap; no process injection, credentials/providers change,
new worker, debugger evaluation or reinterpretation of `wm.arrange` as code
execution is authorized. Do not partially update the dock against the old WM.

## Focused checks for independent House execution

No tests below were executed by this worker. The prior guard rejection was not
retried, and no denied directory was read again. Only source syntax compilation
is suitable for this worker's present source-only verification.

In the reviewed worktree's `src/desktop/agora-wm`, House should execute
with `C:\Projects\Agora4\.venv\Scripts\python.exe -B`:

```text
-m unittest -v test_policy_reload test_fullscreen_delivery
```

`test_policy_reload` checks same manager/native/lease/state/ref/container
identities, preserved normal/preferred bounds/pins/adoption, explicit rollback,
bad hash/syntax/ABI, queued intent, lost watchdog, expiration, gate/foreground/
identity/work-area change, failed commit and owner-thread/steward admission.
Oversized source and source changes after staging must retain the original
generation without lease release.
It checks unread native events and that policy requests and thread-binding
failures exit tick without ingest or switch.

`test_fullscreen_delivery` drives production `WMModule.call` through its actual
request queue/tick, production Manager and solver, with deterministic fake native
acknowledgements. It checks maximized/restored and screen-sized borderless cases,
normal and remembered dimensions, both visible/nonoverlapping/in-work-area,
settling, new-executable waiting, timeout, pinned/dialog refusal and exclusive/
inspection/gate changes. All windows/processes are fixture data.

House should also execute `check_dock_delivery.mjs` with an already installed,
approved Node runtime. It mounts the shipped dock-item component and executes
the shipped Data vocabulary against explicit DOM/transport stand-ins. Seven
cases check focus, restore, pinned focus, minimize, quoted executable launch
ordering, rejection preventing launch, and preserving Agora app launch.
No browser, input, network or native window is involved. Missing runtime is a
reported prerequisite; do not install one or replace this with a visible test.

The pinned focus case also fixes a landed regression: pinned windows must use
plain `wm.focus`, because `request_share` correctly refuses pinned targets.
The existing exact word-offer assertion is updated for the three new words.

**Required before activation, still unrun:** independent guarded hidden native
dock-click validation through the real widget principal, production dispatch and
fixture-owned HWNDs; maximized/borderless actual bounds/visibility, remembered
normal bounds, unchanged claim cookies, continuous guard evidence and no
unrelated app/window/draft disruption. The stand-in tests do not prove native
screen outcomes, bootstrap safety or user acceptance. Generic House suites do
not substitute for these focused or native checks.

## Guard admission repair

World note `dk1716` / receipt `r3702` records the exact previous rejection.
Issuer `house`, PID `11724`; `observed_at=1793129324.3414583`,
`uptime_ms=760705125`, schema `house-guard-context-v2`; old state 2,
claude.exe, full_screen true, game null, Default input desktop and admitted
false. Reader returned `house observation stale/unknown/unsafe`. These are
stale fields, not a current observation of Alex.

The fixed reader path is the main checkout's old
`src/text-desk/notation/house-state/frontier/guard-context.json`.
Only the old notation House integrates its Publisher; kernel House has no
equivalent integration. There is no supported world refresh verb.

Repair belongs to JEFF/the kernel House steward: independently review a
House-owned publisher integration and matching fixed reader location/schema,
using fresh OS observations and unchanged policy. This delivery draft does
not implement that separate repair. No worker-authored attestation, copied
JSON, old Frontier restart, non-game policy change or guard retry is allowed.
