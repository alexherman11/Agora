# Slim dock — staged, not applied

Pins are ordinary notes in Alex's dock. `lens` + optional `shows` identify an
app panel; `opens` identifies a document/surface/view; `window` names an existing
Agora window definition. No HWND is saved, no external program is invented.
Panel pins copy `chrome`, `sizing`, `filled`, `pin`, icon and colour intent.
Every restore searches only the current home layout, including tab activation.
Malformed/unsupported trees leave panels/full state unchanged. No chat text or
explicit context is changed. Native Windows app identity/launch remains a
separate missing capability (JEFF c7264).

The compact dock renders pins only. The small dot/highlight means an unshelved
matching panel in this workspace, or the document currently in the viewer.
It does **not** claim that an external window is running. A window-only pin
says only Pinned and dispatches the existing closed `host window` capability.
Right-click removes softly; Undo, Restore removed pins, or dropping the same
thing again reverses it. Left/middle of a pin reorders before it; right edge
reorders after it. Dropping outside is not removal.

## Source integration

`CarryTargets` adds `on drop any`, cross-lens receiver discovery, pickup-time
receiver/action snapshots and both revision fences. Named targets beat `any`.
Guarded host clicks/menu entries preserve existing window definitions.
Command templates gain the identity fields already available to lens frames.
`tree-activate` changes typed tab references only, preserving literal JSON.
Computed values keep literal dollar signs (`$ref` must not become a template).

**Dependency:** a7045's partition adapter consumes whole-panel carries.
`partition_hook.py --diff <partition-ui.js>` prints its exact external-drop
handoff. It checks every old passage before producing anything. Integrate that
hook with a7045 source before accepting dock pinning in the new layout.
No other worktree was edited or copied into this branch.

## JEFF's scoped world application, after source lands

1. Read home-dock, home-style, home-viewer, home-thing. Save their current text
   and pin props in a plain **Restore: slim dock** note in your corner.
2. Check every `world_patch.passages()` old text exactly once. If moved, stop
   and reconcile just that passage; preserve new music and layout changes.
   `world_patch.py` prints commands, never applies them. It has no live route.
3. Create the four `.verb` notes on=f5189 from these files (do not duplicate an
   existing verb of the same name). Append the namespaced style after the
   appgrip anchor; add carry to the viewer title and home-thing result name.
   Replace home-dock only if its **entire saved old text** still matches.
4. Optional real seeds: pin the actual Waiting on you panel with `dock-pin
   a5668 f5565`; do not invent calendar or Seabright apps. Existing pins stay.
   Set existing pins' tint deliberately (JEFF purple, Board amber,
   Conversation blue, Writing green); record each old value for reversal.
5. Do not change home-tiling, music, workspace layouts or chat props here.
   Drag a document/surface/lens by its viewer title; drag a panel by its
   ordinary/app-owned grip. Editable document text remains selection/editing.

**Reverse:** `world_patch.py --reverse` prints exact reverse replacements,
including removal of only the appended style block. Restore changed pin props
from the saved note; undo any newly seeded pin event. New verbs may remain
dormant, or JEFF may untag only the four new definitions after confirming their
recorded identities. Existing/new user pin data is retained. Never reset a
workspace to an old whole snapshot.

## Guarded copy recipe and acceptance

Run from this worktree with the pinned interpreter:

```
python research/window-lab/slim-dock/review_copy.py --world frontier-try
python research/window-lab/slim-dock/review_copy.py --world frontier-try --small
```

This uses screen.py's disposable world, hidden desktop and guard; no live mode,
HUD process, real host actions or Conversation sends. The recipe stages exact
world passages in the copy, then requests facts and a screenshot. Check every
desk receipt: moved passages or duplicate verb refusal invalidate acceptance.
It measures the current-column layout. Repeat after a7045's own copy staging
with the external hook integrated for whole-panel acceptance.

Browser-capable reviewer must additionally drive these journeys on the same
guarded copy at 2560x1440 (Alex's 150% setup) and 1280x800:

- Inspect bar height, coloured icons, contrast, hover names, hit targets and
  dock bounds. No raw ids, visible labels, Dock this, widget/panel duplicates,
  gaps, clipping or decorative animation. Take normal and hover shots.
- Drag a normal panel and bare music appgrip to the dock; inspect pickup ghost,
  landing preview and release. Pin a document, surface/view and lens by their
  viewer title; pin a real window definition. No playback/heart/edit theft.
- Drop each twice: one pin. Open twice: one matching panel. Shelf then open:
  restored, correct tab active, intentional full exits. Music remains bare,
  content-sized intent and full-player lens preserved.
- Reorder both directions and to the last position. Remove only by menu;
  dropping outside changes nothing. Undo/remove/restore/re-pin preserve order.
- Switch workspaces and reopen: current matching panel or one new panel;
  never a panel appearance from the prior workspace. Repeat with tabs,
  natural sizing, pinned/shelved/full mode and title-divider interaction.
- Type an unsent chat draft with explicit context; perform dock operations;
  verify exact draft/context remain. **Do not send any Conversation test.**
- Inspect/refuse a stale pickup after a receiver/source changes; no duplicate
  act on retry. Check guard verdict and page errors; retain shots and facts.

## Evidence

Ran: in-memory `test_dock.py`, carry-target DOM stand-ins, source parser/filler
regressions (see card for final printed counts), and exact partition-hook diff
against a7045's preserved source. No live world/lens apply or host action.

Guarded copy attempted: Edge's DevTools connection closed in
`sandbox_window.open_edge`, WinError 10054 / ConnectionClosedError, before
page-ready and before staging/steps. No screenshot or interaction acceptance
was obtained; the guard did not return a completed run verdict. The copy
server cleanup returned. This is not evidence of visual success.
