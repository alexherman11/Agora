# Multi-axis desktop stress tests

This round is intentionally more than longer versions of the note-board tasks.
Freeze these requirements before model runs. Synthetic data only; no actual email,
calendar, spreadsheet, terminal, browser or voice session is operated.

## What is likely to break

- **Knowledge mistaken for visibility:** a hidden/minimized window has logical
  content but is not readable on screen; being in the desktop tree is insufficient.
- **Identity shortcuts:** useful-looking object IDs give the agent the answer.
  Replace fixture IDs with opaque stable handles, and retain duplicate titles.
- **Temporal reasoning:** the cheapest old quote can be invalidated by a later
  message; dependencies can be technically complete while release approval is not.
- **Geometry shortcuts:** tiling only chosen rectangles can overlap pinned or
  unrelated windows; stored bounds do not prove actual non-occlusion.
- **Precision across domains:** a spreadsheet input, computed total, calendar time,
  task status and window position cannot all be generic text replacements.
- **Recovery:** current undo compares whole records and parent revisions. Adding
  an unrelated note after tiling may prevent undo, even if no tiled position changed.
- **Pagination under change:** offset pagination can skip a node when an earlier
  sibling disappears. More depth is not necessarily more reliable context.
- **False completion:** passing the easy parts must not hide a skipped condition,
  unsupported operation, forgotten preservation rule, or impossible layout.

## Missions

1. **Supplier decision and meeting preparation.** Compare current quotes and later
   mail, include mandatory charges, obey deadline/budget, update only spreadsheet
   inputs and decision fields, find a calendar slot across three people, create a
   draft without sending, reference the chosen source, and expose the relevant
   windows without damaging personal work, local drafts or the active voice dock.
2. **Release handoff and selective undo.** Distinguish staging from production and
   old from current evidence, respect dependency and approval boundaries, manipulate
   a shared incident reference, arrange the handoff board, preserve a concurrent
   edit and a newly added note, then undo only the arrangement. Keep the running
   terminal job, pinned controls and unsaved draft intact.
3. **Physically impossible workspace.** On a small screen, require several windows
   to remain fully visible, disjoint and above minimum readable sizes while a dock
   stays pinned. Correct behavior is to establish the conflict and explain what
   must change; shrinking below minima or claiming success is failure. Combine
   this with useful feasible document edits and preserving unrelated work.

## Measurement

Keep operations and fixtures identical between projection variants. Validate exact
state, untouched-state allowlists, event order, refusal atomicity and replay.
Inspect final claims against the complete state checks. Record model call/time
budgets and all failed attempts. Use fresh Terra sessions. Domain adapters and
screen observations are simulated; success is not proof of real rendering,
external integration, generalized permissions or a finished Agora architecture.

## Executed follow-up

See [HARD-RESULTS.md](HARD-RESULTS.md) for six real Terra runs and preserved failures.
After the original undo defect was observed and repaired, a fourth mission added
a genuine collaborator placement conflict. It validated refusal of the conflicting
undo but exposed an attempted prohibited shipping transition, stopped by the guard.
The supplemental audit therefore separates final-state success from behavioral
success. Three additional deterministic probes reproduced navigation, task-view
and pinned-obstacle defects. No production architecture was adopted from these tests.
