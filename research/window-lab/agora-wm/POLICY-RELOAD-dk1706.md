# WM policy handoff — source draft for independent House review

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

In the reviewed worktree's `research/window-lab/agora-wm`, House should execute
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
`research/text-desk-lab/notation/house-state/frontier/guard-context.json`.
Only the old notation House integrates its Publisher; kernel House has no
equivalent integration. There is no supported world refresh verb.

Repair belongs to JEFF/the kernel House steward: independently review a
House-owned publisher integration and matching fixed reader location/schema,
using fresh OS observations and unchanged policy. This delivery draft does
not implement that separate repair. No worker-authored attestation, copied
JSON, old Frontier restart, non-game policy change or guard retry is allowed.
