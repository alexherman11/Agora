# Combined tiling + slim dock: guarded browser review (a7466, for a7366)

worker-a7466 (builder-1), 20 Oct 2026. Acceptance only: no source fix to the reviewed code, no live apply.

## Verdict

Not accepted yet: two defects for the source owner (a7045), both reproduced in the real hidden Edge. Everything else
I could drive passed at both sizes. Production apply stays gated.

1. **A panel carry selects page text, and that kills the next carry.** The partition carry (partition-ui.js `carry`)
   never turns off text selection; lens.js's older carry does (`document.body.style.userSelect = "none";
   getSelection().removeAllRanges()`, lens.js:1268). Mid-carry 804 characters were selected at 2560x1440, up to
   41,136 depending on the path. The next press that lands on that selection starts Chromium's own text drag. The page
   gets `pointerdown`, `mousedown`, then `pointercancel` straight away, and no carry starts: no ghost and no
   preview, so the panel does not move. The press clears the selection, so the carry after that works.
   Reproduce: drag any panel title to the desk's bottom edge and release, then drag the same title again.
   (syncdiag, ran: carried, then not carried with 804 characters left selected, then carried with the selection
   cleared first, twice.)
2. **Old dividers and Fit tools stay in place for about half a second after a drop.** `finish()` paints the
   planned layout with `tools=false`, so the 12 px invisible dividers and the Fit buttons keep the old geometry
   until the world's answer re-syncs. Measured from release until gone: 406–1,000 ms at 2560x1440 and
   422–922 ms at 1280x800 (24 carries each). A press in that window lands on an old divider. That is exactly why
   a7045's own `partition_navigation` step failed at both sizes ("a press at its centre lands on DIV").

Pre-existing, not from this change: at 1280x800 the chat composer can't be reached. The top widgets stack to about
326 CSS px, the panels get 383 px, and the composer sits below the chat panel's cut. The unstaged world behaves
the same (screen.py, ran: the composer's centre is covered).

## Setup (copy-only) and hashes

- Source: a7045's 57 uncommitted files on base c5c988c, composed over main c3ad04e (landed harness, tabs
  3cc2796) in this worktree's files only, by `overlay.py`. a7045's tree, git and the live world were not
  written. Result: 49 clean (new, theirs, merged or same as main) and 4 conflicts, all additive unions recorded in
  `resolved/`:
  - lens.html: both script lists
  - scene.py: PAINT_WORDS `remember` beside partition's words
  - lens_ir.py: `_static` words, the same union
  - FRICTION.md: main's version kept
- `manifest.json` lists every file with base, theirs, main and composed SHA-256. partition-ui.js is
  89769A67AFFAF5FA4783FB1F318E5BEA233AFFC6D10EC557174A7AFDC904E332, the same as c7426.
- World: hud_playtest's disposable copy of frontier-try (the copy was at e14709), staged by a7045's
  `review_copy.stage_copy`. That preflights both halves and then makes one write at a time; there were no
  refusals.
- Harness delta, my own a7413 area, committed: Edge now starts with
  `--disable-features=CalculateNativeWinOcclusion --disable-backgrounding-occluded-windows
  --disable-renderer-backgrounding`.
  - Why: with Alex's PC idle for 39 minutes (display probably asleep), the hidden page went
    `visibilityState: hidden`, drew blank and dropped carries.
  - With the flags (ran): visible and drawing. Isolation is unchanged.
  - The driver also marks any journey that saw a hidden page as invalid.
- Composed tree tests: test_review_copy 8 ok, test_dock_integration 2 ok, test_navigation 10 ok,
  test_scene 58 passed. The node DOM tests were not run (node needs approval here).

## Journeys (ran: journeys.py, hidden Edge, guard on)

Pages measured: **2560x1440 CSS at DPR 1.5** (fullscreen on its hidden desktop) and **1280x800 CSS at DPR 1.5**.
Both visible, no page overflow, page errors [] in both runs. Guard on every run: "alex: untouched by the sandbox".

The driver clears any text left selected before each press (defect 1) and reports each count. Without that, about
half the carries fail.

| journey | 2560x1440 | 1280x800 |
|---|---|---|
| facts: CSS size, DPR, no overlap/overflow/dock collision/stale chrome at rest | pass | pass |
| title click, 4 px move and text click on all four panels: no snap or resize | pass | pass |
| whole-panel ghost past 5 px, source dims to .35, preview, no animation, Escape cancels | **fail** (selection, defect 1); rest pass | **fail** (467 characters); rest pass |
| four desk edges × Board, Chat and bare Music (12): preview = result within 1 px, full span | 12 pass | 12 pass |
| four local edges + centre tabs on the Viewer; each tab selects its panel | 5 pass | 5 pass |
| Fit content / ↔ restore; bare app content-width handle kept over reload | pass | no change: both already fill their 300 px allocation, which the design says bounds them |
| every column divider, then with Chat across the bottom every divider: ±80 saved, both ends hold minima | pass | pass |
| double-click focus: pinned Chat beside, rail; focused divider kept over reload; double-click restores | pass | pass |
| pin the Board panel to the dock, shelve it from the header, open its pin twice: one panel, same place, open marker right | pass | pass |
| resize and blur events mid-carry cancel with nothing committed | pass (dispatched events) | pass |
| competing tree change while held: the stale drop is refused and the page repaints | pass | pass |
| unsent chat draft and caret through drop, divider and focus; words kept over reload | pass (caret at the end after reload) | blocked: composer cut off (pre-existing) |
| bare Spotify: compact, no generic header or Fit; appgrip carries the whole app | pass | pass |
| over the dock only the dock's box shows, back over the desk only the split's; two drops make one pin; tree untouched | pass | pass |
| reorder pins both ways and to the end; outside drop changes nothing; Remove pin; Restore removed pins | pass | pass |
| hover names readable (15 px, inside the page); open markers true | pass | pass |
| pins coloured apart | blocked: no pin has `tint=` (live dock checked too); JEFF sets tints at apply (handoff step 4) | blocked |
| changed layout identical after reload | pass | pass |
| a7045 recipe `partition_navigation` | fail (defect 2) | fail (defect 2) |

Reports and shots: `research/window-lab/demos/combined-review/2026-10-20-180513-2560x1440/` and
`2026-10-20-181014-1280x800/` (report.md, report.json, numbered PNGs) in the main checkout. Recipe runs:
`demos/hud-playtest/2026-10-20-173108` and `2026-10-20-181541`.

## Not covered

- Real `pointercancel` (touch).
- Workspace switch with dock reopen.
- Pinning a document, surface or lens by the viewer title, or a window definition.
- A receiver changing while a panel is held over the dock.
- Drops started from a tab or from focused mode.
- Music playback and heart controls: nothing is playing in the copy, and media/account operations are out of
  scope, so Connect Spotify was never pressed.
- Landed tabs (3cc2796) plus staged a7439/a7441: not composed here. That stays a separate acceptance, so no
  dependency drift is hidden.

## Withdrawn on the way

- "The carry after an Escape fails" was defect 1: the carry before the Escape had left text selected.
- Blank shots and dead carries around 17:40 were Edge's occlusion handling (see the harness delta), not the page.
