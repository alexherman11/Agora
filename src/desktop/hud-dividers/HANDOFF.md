# Superseded initial handoff — retained as the earlier evidence record

Current implementation, staging and review gate: **NAVIGATION.md**. JEFF
directed continued source work on Codex (c7139); the cross-provider handoff did
not occur. The statements below about the expansion being unimplemented describe
the initial divider-only checkpoint, not the current source.

## Initial checkpoint — do not land this foundation alone

Read a7045, especially JEFF's c7080 and proposal c7092. Alex expanded the card
from dividers to coherent panel navigation during this turn. The divider
foundation is implemented and tested without a window. The expanded navigation
is **not implemented**. No live lens/style/layout was changed, no host was
restarted, and no real Conversation line was sent.

Handing to a Claude builder for the expanded navigation and guarded browser
acceptance: this Codex sandbox cannot start the test browser. Continue from
these preserved edits. The card is not ready for landing.

## Source foundation

- `scene.py`: `resize <prop> min <CSS pixels>` on a repeated shared frame.
- `lens_ir.py`: generates fenced ordinary `do prop` acts, including a missing
  property in the fence. Share expressions and resize properties now enter
  `_static`/fingerprints; previously real prop writes persisted but a kept
  repeat still showed old shares. This was reproduced by the persistence test.
- `desk-shell/dividers.js`: generic sibling boundaries, minimum outer sizes
  plus weighted surplus. Minima scale together when physically infeasible in
  a small viewport. Paired weights retain their sum; other siblings stay
  unchanged. Movement previews; release sends both ordinary desk acts in one
  request with both read fences. Matching definition paths/hashes/lenses are
  required. Escape, pointercancel, lost capture, focus loss and viewport resize
  cancel. Arrows adjust; Enter saves. Twelve-pixel transparent hit targets.
- `lens.js`/`lens.html`: install the helper, suspend repaint/reload while
  resizing/awaiting its answer, resize cursors and separator focus.
- Existing carry/title drag is unchanged by this foundation.

The minimum model adds minima before dividing weighted surplus, intentionally
different from plain `flex: weight 1 0`. There is no HUD-specific source logic.
Persistent layout truth stays in the declared world properties.

## Staged world foundation

`home-tiling.before` was read live during this turn, including JEFF's music
`filledbody`, scrolling boundaries and current controls. `stage.py` prints five
exact replacements, with no live connection. These are **only** the divider
foundation, not the proposed tree migration: column `span`, panel
`height_share`, full-mode `full_share`. No current layout/panel data or style
is replaced. Never activate this as the completed c7080 design.

Preserve latest home-style `tilefoot=4px`, music and scrolling; reread before
any world apply. Shop talk m7074/m7076 coordinates staged-only/no-restart work
with a7009 and a6443. Return additive staged changes to JEFF; no live lens or
style replacement by the builder.

## Proposed design and remaining implementation

Proposal c7092, not implemented:

1. World slicing tree: row/column split surfaces; child split surfaces/panel
   notes carry weights. Migrate existing columns to horizontal root/vertical
   child splits without resetting Alex's arrangement. Save reversible migration.
2. Global edge drop wraps the root: bottom spans the whole desk. Local edge
   drop splits the target leaf. Never fake global bottom as a column insertion.
3. One placement plan drives preview and drop, including gaps. Carry the whole
   panel after a movement threshold. A stationary title/control press never
   snaps/resizes. Entering a target shows the intended extent without animation.
4. Content sizing and tab groups coexist with stretch and intentional fill;
   retain pin/shelf/full and equal-footing chat. Exact tab/content policy still
   needs implementation.

Constraints read in source:

- Current column model cannot express arbitrary full-width bottom regions.
- `in:` selections are recursive. Tree rendering must restrict direct children,
  or descendants appear repeatedly.
- Placed lenses stand on their part's current thing. `lens_ir` refuses any
  repeated lens name in its stack; explicit tree descent needs identity
  progress, cycle/depth/budget checks. Do not simply remove the guard.
- `_static` also recurses over `each` definitions; allowing `each` cycles alone
  is unsafe.
- Carry ghost clones the grip; receiver lookup picks the first hit. Pane hits
  can hide outer desk-edge receivers. Both need deliberate changes.
- `landing()` halves a receiver without subtracting a new split's gap.
  Preview/drop agreement needs an explicit common geometric rule.

These are implementation constraints, not claims of an existing tree renderer.

## Ran

Pinned Python, from this worktree:

- `test_stage.py`: **5 tests OK**, fresh in-memory world. Admission, text/painter
  emission, missing-property fences, real prop writes/repaint, patch idempotence
  and concurrent unrelated edit preservation, music/scroll passage preservation.
- `node test_dividers.js`: **155 divider geometry checks passed**.
- `node test_pointer.js`: **12 divider pointer/keyboard/fence scenarios passed
  (DOM stand-in; no window)**.
- Five existing scene regressions passed: data-driven share/scroll, carry/drop,
  drop sides/double, painter emission, paint words.
- `node --check desk-shell/lens.js` and `git diff --check` passed.

Full `test_scene.py` printed 31 passing checks, then stopped in
`test_rooms_go_look_and_replay`: PermissionError writing
`%LOCALAPPDATA%/Temp/tmpbzug9cd9/base@walk.pickle`. A worktree-temp/runpy retry
did not reach tests because its import path was missing; do not count that run.

`health.py frontier-try` completed, **exit 1**, at world **e13783**
(13775 events), total **180.7s**. Python and scripts passed; **73 lenses
compile, 0 unexpected refusals, 1 expected (p-if)**. This is not a health pass:
temp-folder permissions blocked multiple suites, door did not answer within
60s, textedit lock was not acquired, paint/browser tests failed to start/respond,
and `test_reach` reported four failures (not baseline-checked here). One new
documentation failure is actionable: Help note a1853 does not yet name the new
`resize` word. Stage that Help/Handbook update for JEFF with the final capability;
do not describe the incomplete word as already live. Styles reported 14 read
and 13 properties with no painter drawing. Disposable roomworld sessions
belong to the harness; do not manually remove or commit them.

## Browser blocker and required acceptance

Ran browser availability check on the unchanged copied-world lens:

`screen.py frontier-try --as alex --lens home-base --size 2560x1440 --scale 1.5 facts stage 1 shot screen-dividers.png`

Reported `nothing answered at http://127.0.0.1:57953/json/version within 20s`.
No shot/geometry obtained. This was not divider visual acceptance. No fallback
to Alex's screen, inputs or host processes was attempted.

After the refinement, run guarded copy checks with this worktree's painter and
fresh world staging at 2560×1440 CSS/1.5 scale and 1280×800:

- Every shared axis both directions and to minima; no overflow, accidental
  wrapping, dock growth or unexplained foot gap.
- Stationary title/control clicks versus threshold whole-panel drag.
- Four global edges, four local edges, especially full-width screen bottom.
- Preview/final bounds agree including gaps; own-ancestor and last-panel moves.
- Tabs/content sizing, explicit fill, pinned companion, shelf/restore, empty
  branches, cancellation, resize during viewport shrink, concurrent world edit.
- Reload persistence for geometry and memberships.
- Compose/edit a draft without sending Conversation tests; resize/rearrange
  beside it and confirm words/caret survive.
- Existing title drag, music controls and scroll boundaries.
- Add one unique `playtest_steps/<name>.py`; no shared runner-list edit.

Notebook entry is added; Rough spots a7107 records the missing world word.
