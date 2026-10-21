# Narrow host-command route: trust-boundary review

Follow-up source review: [Parent dispatcher integration](host-route-parent-review.md)
adds real queue/turn integration behind an always-disabled dispatcher.
This earlier review remains the historical reference-model record; no live
host route is enabled.

Status: **disabled source/reference tests ready for review; live boundary unimplemented**, 20 Oct 2026.
This is a review proposal, not an enabled capability. No process query,
termination, launch, settings change, broker startup or live model trial ran.

## What exists (read)

- `codex_worker.py:build_config` keeps `workspace-write`, unelevated Windows
  sandboxing and approval `never`. `thread_parameters` accepts exactly the
  `desk` MCP server, enables only `desk`, and exposes no dynamic tools.
- `notation/workshop.py:extra_tools` verifies a matching, non-undone,
  direct JEFF/Alex property event and builds exact Claude shell allow rules.
  `Worker.start` explicitly withholds these extra tools from Codex. This
  grants tool admission, not an outside-sandbox executor.
- Its command grammar also rejects wildcards, shell metacharacters,
  parentheses and commands longer than 200 characters. The activation card's
  long scoped WMI query cannot simply be passed through this validator.
  Do not silently relax this grammar or reinterpret older grants as broker
  authority.
- `notation/desk_mcp.py` accepts only the Desk tool and runs `explore.py`.
  `DESK_PIN` pins the actor on that MCP connection, but the file explicitly
  documents Desk identity as a claim. This is not an authenticated
  host-capability service. A new execution endpoint must not trust caller
  supplied `as=`, card IDs, world text or a writable queue file as authority.
- `window-lab/host_verbs.py` is a deliberately closed set of HUD actions.
  Requests originate from the painter via `window.pywebview.api.host`, not
  the Desk. It has no per-worker command broker or authenticated grant
  protocol. Do not add arbitrary shell execution to that UI API.
- `codex-residents/listener_bridge.py` verifies the owning executable for the
  Codex app's pipe, then uses its existing app-chat MCP bridge. It is not a
  host-command runner and must not be repurposed to escape a sandbox.
- `worker_lease.py` supplies process-held card/builder locks. These serialize
  adapter ownership; they do not serialize Claude and a separate host broker
  through an activation transaction or provide durable effect receipts.
- `window-lab/hud_lifecycle.py` has reusable exact process observations and
  same-handle creation-FILETIME/executable verification before termination.
  This is lifecycle policy, not a worker-accessible privilege boundary.
- The inspected command/lifecycle paths do not supply the requested
  broker-level no-game/no-wake admission guard. A `Guard` for focus/input
  isolation must not be mistaken for proof that no game is running.
- Runtime tool metadata exposes no trusted host-command broker. This is an
  observation about the available tools and inspected source, not proof that
  every process or Windows service on the PC has been enumerated.

The activation card was read completely, including its denied WMI query,
cooperative-stop procedure, exact supervisor launch, renewed authorization,
and queued Claude fallback. Coordination was sent in Shop talk. No fallback
property was changed and no execution lease was acquired.

## Missing boundary and decision

There is no supported, available broker route to call from this worker.
Starting an unsandboxed helper ourselves, changing provider settings, or
turning an existing Desk/UI endpoint into unrestricted execution would not
establish the requested trusted boundary.

JEFF needs to choose a reviewed house-owned broker deployment and its
authenticated grant channel, or supply an already approved host executor
with that contract. Deployment must be by a host-capable maintainer through
the house's reviewed path; this worker must not bootstrap it through WMI,
app pipes, shell escapes or altered sandbox policy.

## Proposed smallest next implementation (not implemented/enabled here)

1. Put a closed, typed operation table in the trusted house/host process.
   First implement only `agora.processes.read`; it accepts no caller-supplied
   shell, script, executable, working directory, WQL filter or arbitrary PID.
   Use the reviewed activation query's fixed scope and return only its
   identity fields, not a whole-machine command-line dump.
2. Bind a house-issued capability to the current card, worker identity,
   adapter generation, operation, exact arguments, grant event, expiry and
   one-use request identifier. The host authenticates the transport and
   verifies a trusted JEFF/Alex grant source. Do not treat the existing
   claim-based world event log as an OS security boundary. Protect any
   capability material from other workers; no credentials or capability
   values belong in chat, world notes or logs.
3. Revalidate grant/revocation and fail-closed game/session admission at
   execution time. Unknown game/session state refuses. No wake timer,
   scheduled wake, input injection, visible window or power request is part
   of this route. If sleeping or unavailable, do not arrange a wake to
   service a request.
4. Serialize by card in a single host-owned executor with a durable
   transaction journal. Record `requested`, `admitted`, `running` and
   terminal receipt. Duplicate request IDs return the prior receipt.
   A crash after admission produces unknown outcome, never blind replay.
   All executors, including the queued Claude fallback, must use that same
   lease/journal or be explicitly handed off by JEFF before operations.
5. Return audited success, refusal, access denial or unknown outcome with
   card/actor, grant, request ID, operation, timestamps, guard result and
   bounded truthful output/error code. Denial is not an empty process list.
6. After the read-only path is accepted, any later lifecycle operation needs
   a separate explicit route grant. Preserve the activation card's exact
   scope: cooperative supervisor stop, confirmed exit, identity-verified
   HUD stop, then the exact hidden main supervisor launch. Use existing
   verified-handle helpers; never bare-PID/tree kills. Preserve keeper,
   door, house, draft and parked human work. Never translate a generic
   destructive string into an operation.

## Acceptance still required

- Fake admission tests: ungranted destructive operation never calls an
  executor; forged actor/card/generation, wrong arguments, stale/revoked
  grant, duplicate requests, overlapping fallback, unknown game state,
  host denial and crash uncertainty all refuse or preserve prior outcome.
- Real Codex builder: through the deployed and explicitly granted route,
  issue exactly one scoped read-only Agora identity query. Keep either its
  output or its actual denial receipt. No real starts/stops for testing.
- Activation remains on its original card and still needs JEFF's explicit
  grant for the implemented route, receipt reconciliation and single-owner
  handoff. The existing fallback remains queued.

No host acceptance, broker test, security enforcement or activation is
claimed by this review. No runtime source or security setting was changed.

Ran the existing `test_worker_grant.py` with the pinned interpreter. It
printed `all passed`. Its in-memory world and stubbed process starts verify
the current Claude-only extra-command checks, including refusal of a compound
destructive test string, actor pinning and Codex's explicit non-grant.
It does not create or validate a new broker and does not run those commands.

## Source approval and specific authentication blocker

JEFF's follow-up approves source implementation/review of a house-owned,
typed, read-only inventory executor. It prohibits deployment, real queries,
and lifecycle mutations pending review. It explicitly requires reporting a
blocker if normal house identity cannot distinguish a real JEFF grant from
a worker claiming JEFF. That condition applies to the inspected paths:

- `notation/deskd.py:561-568` implements a browser-origin check, documenting
  that local clients without browser headers are allowed and "nothing
  authenticates." This is a cross-site request guard, not caller identity.
- `deskd.py:773` constructs the command session using `body.get("as")`.
  `door.py:531` likewise derives its actor from the request body's `as`.
- `notation/house.py:675-678` sends the selected actor through that Desk
  path, with a fallback to `desk_mcp.run_desk` using the same claimed actor.
- `notation/desk_mcp.py:96-99` checks a connection's environment-based
  `DESK_PIN`. That wrapper check is useful but does not attest the actor of
  every request accepted by the Desk server. The normal world grant event
  therefore provides no authenticated issuer provenance for a host broker.

Ran the actual `_foreign` function extracted with Python AST into an
isolated namespace, using fake request headers/server metadata only:
`3 origin-check assertions passed; no server, world access or host command
executed; caller authentication not provided by this check`.
Headerless and same-origin requests pass this guard; a foreign Origin is
rejected. This narrow check does not submit a forged grant or establish
that any broker exists.

A host executor must not promote these claim-based events to authenticated
JEFF grants. The next required review decision is an authenticated
house-owned grant issuance path, whose provenance cannot be minted by
ordinary Desk requests or worker-edited world data. Its identity binding,
revocation, persistence and fallback behavior must be specified before
wiring execution to it. No authentication settings were changed and no
unauthenticated executor was implemented. The existing activation fallback
is unchanged. Source implementation and its requested fake broker suite
remain blocked under JEFF's explicit authentication condition; real
inventory acceptance is additionally deferred by his follow-up.

## Disabled draft following JEFF's authenticated-channel approval

This section supersedes the earlier request to stop before source work.
JEFF approved a new issuance channel anchored in the parent resident-session
dispatcher, and explicitly permits a concrete design and stub if that
boundary cannot yet be safely established. No public Desk actor claim is
promoted to authority by this draft.

### Source delivered

`notation/host_route_draft.py` contains:

- `DisabledRoute`: unconditional refusal, with no enabling setting, transport,
  process query, house import, subprocess call, process start or stop.
- `ReferenceModel`: a fake-only executable policy model, accepting injected
  issuer/worker attestors, guard observations, inventory and time.
- A closed read-only operation with no shell, WQL, script, working directory
  or PID argument. Fake results use a fixed bounded identity-field projection.
- Card/worker/generation/session bindings, at most five-minute grants,
  revocation, parent-owned opaque single-use handles, and audit records.
  Handles never enter world text, MCP arguments, environment or receipts.
- SQLite admission transactions and a unique active-card lease; terminal
  receipt replay never calls inventory again. A running entry after a crash
  remains unknown and blocks a fallback on that card. There is no automatic
  lease expiry or replay. A restart invalidates all in-memory handles.
- Fail-closed awake, interactive-session and no-game observations. Unknown
  observations or guard errors refuse; there is no power/wake facility.
  Permission denial is a denial receipt, not an empty successful inventory.

`notation/test_host_route_draft.py` exercises only test doubles, in-memory
databases and a temporary worktree journal. It imports no house/world code,
starts no service, and calls no Windows process APIs. Its opaque objects and
fake attestors are a specification seam, NOT authentication enforcement
against another process. Ordinary Python access to this model grants no
host capability.

### Concrete parent/session integration required before enabling

Read: `Resident._read` in `house.py:493-503` receives a particular child
process's stdout but puts untagged events in `self.events`. `turns_ended`
then returns plain text; `House.after_turn:1281-1290` parses commands and
passes their claimed actor to the ordinary Desk. The earliest possible
attestation point is the parent-owned reader/dispatcher, BEFORE that
conversion. No interception hook was installed in this draft.

The reviewed implementation must:

1. Mint an unforgeable parent-side session identity when the house starts a
   resident child. Bind it to the actual child handle, creation identity,
   registered resident object and generation, rather than a world `actor`
   property or a child-supplied provider session ID. Tag each queued event
   at `_read(proc)` with that parent identity and reject stale generations.
   A mutable resident name or reused PID is insufficient.
2. Parse an exact, separate typed grant intent on completed output from
   that registered JEFF session. Intercept it before `commands_in`/`act` and
   general `/api/do`. General Desk requests may request a grant but cannot
   approve, revoke or replay one. No shell-shaped grant grammar.
3. Resolve the target card and worker generation from the parent registry.
   Persist issuer provenance and grant/receipt transactions in a host-owned
   journal outside world and worker mounts. Review the actual Windows ACL
   and launch identity: a filename named "private" does not provide
   isolation, especially for same-user processes. The draft does not create
   that journal or change ACLs.
4. Establish a reviewed private worker-to-parent channel bound to that
   worker's child process/generation. Keep the authority handle in the
   parent channel registry; the worker receives a grant notice, not a bearer
   secret in MCP arguments, logs or environment. A request identifier is
   public and confers no authority. The draft has no such transport; its
   object handles stand in for it in tests only.
5. Obtain fresh guard observations in the host immediately before admission.
   Unknown game/session state must continue refusing. Bind read-only scope
   in the reviewed host implementation and inspect projection against
   unrelated process disclosure. No real inventory backend is supplied.
6. Audit both successful and refused operations without capability values.
   On restart, require reissuance for new child generations, while preserving
   terminal receipts and unresolved running leases. Any future activation
   fallback must reconcile with this journal through an explicit handoff;
   the existing queued fallback has not been modified or integrated.

The current queue loses process-generation provenance, the private journal
boundary is not established, and a worker-bound authenticated transport is
absent. Consequently this delivery intentionally stops at the approved
disabled stub/reference model. It cannot be enabled by changing a boolean.
Landing this source does not deploy a broker. Real authentication, Windows
private storage, game/session observation, inventory output, a Codex host
round trip and any lifecycle mutation remain unverified and unimplemented.

### Verification for this disabled delivery (ran)

- Pinned interpreter, `notation/test_host_route_draft.py`: `Ran 19 tests
  in 0.058s`, `OK`. Includes forged actor/copied world props, destructive
  refusal without execution, caller/card/generation mismatch, expiry,
  revocation, unknown/false guards, access denial, duplicate replay,
  two-connection card exclusion, and persisted crash recovery.
- Pinned interpreter, existing `notation/test_worker_grant.py`: `all passed`.
  Existing admission behavior remains separate from the draft.
- `git diff --check`: exit 0. New files are left for house commit under the
  builder protocol; no merge, deployment or live activation was attempted.

Handbook runtime descriptions are unchanged because nothing is wired into
the running house. The missing authenticated grant operation is recorded
in Rough spots. Acceptance is source/reference-model review only, not the
original real host round-trip goal.
