# Requested house restart admission — a11546

Staged, not activated. Alex m11543 requested removal of the blanket
fullscreen veto. The only production change is `house_restart.game_seen`
and its module documentation. `guard_context.py`, `house.py`, keeper,
workshop, sessions, leases and native/browser admission are unchanged.
Module-builder owns the separate pending-transfer drain helper; coordination
sent in Shop talk m11553. This patch neither imports nor certifies that helper.

## Decision

Use a fresh, direct house observation at request admission and again just
before an owned requested restart exits. Never trust a caller's assertion
that the screen is clear.

- Refuse explicit game evidence (`game=True` or notification state 3),
  regardless of any non-game allowlist.
- Refuse failed/malformed/missing readings, no foreground, a changed/unknown
  foreground identity, a non-Default input desktop, inconsistent game data
  and notification states outside the existing observable normal/fullscreen
  cases 5 and 2. State 4 presentation and state 7 remain refused.
- Accept otherwise stable cases 2 and 5 without consulting `admitted`,
  fullscreen geometry or an app-name allowlist. OBS, Search, TextInputHost
  and any other readable basename receive the same rule; no global list
  has been expanded. State 2's `game=None` is expected observer output,
  not by itself evidence of a game.
- Native runs still require the unchanged stricter guard policy. A sample
  accepted for restart can still refuse native/browser admission.

## Ran

Pinned Python, offline fixtures only:

```
test_house_restart.py: 18 tests, OK (0.636 s)
test_guard_context.py: 20 tests, OK (1.249 s)
git diff --check: exit 0
```

The restart suite includes request authorization, keeper requirement,
cancellation, durable request state, no repeated restart, busy turns waiting
up to a simulated hour without a requested-restart timeout, and a real run
loop on an in-memory house. New cases cover fullscreen/nonfullscreen OBS,
Search, TextInputHost and an unlisted executable; game evidence; missing,
failed and unsafe metadata; stricter native refusal; and a game appearing
between admission and exit. Every observation/native call is mocked.
No live metadata probe, model turn, process termination or restart occurred.

## Read and remaining uncertainties

Read `house_restart.py`, `guard_context.py`, and `House.run`'s drain/exit
path. Game detection remains limited to what Windows reports; a windowed
game not reported as one is not independently detected here. Fullscreen
geometry and an unknown app name cannot solve that identification problem.
This change adds no game catalog, process enumeration or new surveillance.

Unchanged legacy behavior is explicit: landing-triggered drains can use
RESTART_GRACE, and a requested restart riding an already-owned landing
drain inherits that path. This patch does not make that path idle-only.
Use the requested restart route when no landing drain is in progress;
scope expansion to all landing restarts needs separate review. No session,
worktree or draft persistence code changes are made or newly certified.

## Supported integration, activation and reversal

Return these exact staged bytes to JEFF for scoped review first; no ready
or activation from this worker. After approval, use ordinary house
staging/judging, retaining module-builder's separate workshop edits.
Old processes keep the old imported predicate until an authorized lifecycle
reload. If the old predicate vetoes the current screen, do not edit a global
allowlist or settings as a workaround: the host owner must use the approved
idle-only lifecycle route when safe. This card does not authorize executing
that route.

After the approved source is loaded, JEFF/Alex can use the existing
`restart-house <reason>` verb with keeper present and no preexisting landing
drain. The request note reports waiting/in-flight, refusal or completed/new
house identity. No test request was created here.

Rollback is the inverse scoped change to `game_seen` and module description,
through ordinary reviewed source landing/lifecycle; preserve later peer work.
No world setting or native guard needs reversal.
