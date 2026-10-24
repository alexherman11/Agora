# Shared guarded paint lane — staged, not accepted

Owner: a10672, JEFF. This checkpoint is not a successful Board paint or
permission to retry a refused run. Current main must be prepared into this
branch before browser acceptance or landing.

## Request and execution boundary

The staged `notation/paint.verb` creates a `role=paint-request state=asked`
note in the caller's corner:

```
paint home-base at 1280x800,2560x1440 to pike crop <painted-part-key>
```

`house_paint.py` serializes requests and invokes `paint.py` against a disposable
world copy. It does not change the requested lens or layout. A Board-only lens
can be requested directly; checking the Board within home-base still requires
confirming its actual visibility and part key on the current copy.

This house integration is unlanded. JEFF must install the verb after source
acceptance; reversal is to retire that verb and stop submitting requests.
Do not remove an in-flight request or silently retry one marked unknown.
Interrupted `painting` becomes `unknown` and blocks further starts until an
operator reconciles its exact ownership and delivery receipts.

The runner's lifecycle is:

1. Read supported house admission before creating a copy or server.
2. Enter Guard and retain a fresh Job scope.
3. Snapshot the shared verifier, start Edge once with that Job, enroll its
   recorded birth and pass the verifier gate before DevTools interaction.
4. Paint and capture full shot, bounded overview and requested crop tiles.
5. Close the recorded family while that same Job scope is held, then check
   verifier, Guard and post-run admission.
6. Deliver only when all checks pass, using the existing Desk route unchanged.

Unknown local foreground continuity is not Guard 0. A stale or unsafe
observation refuses; no freshness ceiling or policy is weakened. The verifier
has no broad filesystem watched roots in this runner: it cannot establish that
the entire PC was unchanged.

## Artifacts and worker limits

Runs contain `report.json` plus full screenshot and any browser-rendered
overview/tiles, with SHA256, pixel dimensions and clip. Each delivered image is
at most 2048 pixels per side. The selector admits only 1280x800 and2560x1440
run names under its canonical main-checkout combined-review root.

Workers can use `--root` inside their own worktree for isolated evidence.
That does **not** authorize writing the canonical main root or delivery from an
unrecognized root. `DESKD=off` remains off.

The other legacy consumers, including `hud_playtest.Window(False)` and the
combined-review dragtimes harness, have **not** been converted by this patch.
Their supported integration needs the same retained scope, one startup attempt,
pre-CDP verifier gate, owned cleanup receipt and worktree-selectable output.
Do not infer adoption from `open_edge(job=..., before_cdp=...)` alone.

## Evidence at this checkpoint (22 October)

Ran: 13 paint unit/mock tests; six fake house-request tests; 19 offline Job
tests; ten scripted Guard cases; Python compilation of changed modules.
No browser, model turn, live apply, restart or image delivery occurred.

Read: a10621's `screen-77292.json` records root PID69408,
creation FILETIME134371582558446818, twice as gone. It has no Job boundary,
`cleanup_complete=false`, `remaining_pids=null`, and whole-runtime closure
unknown. No old process was adopted or stopped.

Read once: supported admission was admitted with house PID70960. The current
Codex command token was restricted, medium integrity, not AppContainer.
These observations do not establish why the old DevTools websocket failed.

Still required: current-main preparation; actual guarded Board paints at both
sizes, measured viewport/DPR, shots opened and delivered to Pike; failure and
cleanup receipts if startup refuses. Reliable startup and consumer migration
are not proven by the fake tests.

## Prepared continuation: 22 October, 12:57 local

House preparation completed at `ab2e756`. The prepared paint tests passed
13/13 and house-request tests passed 6/6. ONE real request was attempted,
using `frontier-try` (event 27171), worktree-local output, both requested sizes,
and no delivery. It stopped at the first size before DevTools interaction:
the shared verifier could not read an outside Edge process to exclude this
run's profile. The restricted, medium-integrity Codex runtime also reported
unknown local foreground continuity. House admission was fresh and admitted;
that snapshot does not replace local Guard continuity. No retry, shot,
measured viewport/DPR, second-size launch or delivery followed.

Evidence: `demos/combined-review/2026-10-22-125702-1280x800/report.json`.
The runner report lacks a `cleanup` field on this failed-start path because
`open_edge` already archived the receipt. The separate retained receipt
`.tmp-agora/agora-sandbox/paint-76212-1280x800.closed-1792699023290090000.json`
records `cleanup_complete=true`, `job_closure="proven empty"`, no remaining
PIDs, and active 1 to 0. External delegation remains unknown. This is owned
cleanup evidence, not accepted paint evidence. Do not repeat cleanup.

Mail coordination: this branch changes only `open_edge` in
`sandbox_window.py`; its Win32 declarations and `start/_start_locked` remain
identical to prepared main. Mail owns its separately approved opt-in bootstrap
and retained-handle hunks. Preserve both scoped changes when composing;
neither ownership agreement nor source tests authorize Mail native execution.

Next owner: JEFF, to provide a supported guarded runtime with the necessary
process visibility and foreground continuity, or commission that boundary.
Do not weaken verifier/Guard rules, query the unreadable process by another
route, or retry this refused run. The legacy timing consumer remains pending.

## Offline local-network increment, 22 October

The later Claude-runtime attempt established the required visibility and
continuity, then correctly refused Edge background outbound TCP before
DevTools. See the world evidence "Guarded paint lane — Claude-runtime
verification and network-allowlist gate (a11403)". Its owned Job was empty;
do not repeat its cleanup.

Under JEFF c11472 this branch now stages disposable local-only suppression
switches, selected by paint only. The remote allowlist stays empty, and
ordinary open_edge callers retain their existing arguments. These switches
are not a security boundary or proof that installed Edge honors them.
No native retry or ready is authorized. Exact incremental scope, tests,
source references, limitations and reversal: [NETWORK-OFFLINE.md](NETWORK-OFFLINE.md).
Preserve Mail's separate start/Win32 seam when composing; only open_edge is
changed here. Board shots and delivery remain unproved.
