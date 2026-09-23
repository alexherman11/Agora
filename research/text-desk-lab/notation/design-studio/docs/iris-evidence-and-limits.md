# Evidence and limits

*Iris, 23 September 2026. Paths are relative to `research/text-desk-lab/notation/` unless noted. Every statement is
marked by how it is known: **run** (executed today), **live** (observed in a browser or session, with date),
**code** (read in source, not exercised). Nothing here was measured in a browser today; `deskd` was not running.*

## 1. Automated checks

| Check | How to run | Result today | What it proves | What it does not |
|---|---|---|---|---|
| `test_scene.py` | `python test_scene.py` | **run:** `4 passed` (0.1 s) | Lens admission: quoted text keeps `,` and `#`; `\n` in a lens is data; nine malformed lenses are refused for the right reason (recursion, duplicate parts, unknown role, undeclared gesture, unsupported property, unknown `$name`, repeat without `each`); command values escape `"` and `\`. | Anything about `world.py`, verbs, undo, persistence, `deskd` or painting. These are **the only automated tests of the notation desk.** |
| `../test_desk.py`, `../test_hard.py` | `python -m unittest test_desk test_hard` from the parent lab | **run:** `Ran 16 tests … OK` (0.05 s) | Atomic refusal, stale-edit refusal, undo conflict and ABA refusal, visibility classes, replay of recorded `after` states. | They import the **parent** lab's `desk.py` / `hard_desk.py` (an earlier JSON-verb desk), not `notation/world.py`. They are evidence for a predecessor, not for this code. |
| `harness.py`, `run.py`, `tasks.py` | Not run (they launch models) | — | `tasks.py` defines 11 tasks (`home`…`home5`, `harbor`, `agenda`, `tidy`, `priya`, `review`, `big`) with hidden `assess()` checks. `run.py` copies and SHA-256-hashes the source into `runs/<label>/` and writes report, events and transcript. `launch` (in `harness.py`) is a desk verb that spawns `run.py`. | Not reproducible from this checkout alone: `run.py` imports the transport from `C:/Projects/Agora/local/arrangement-current-20260916/native/src` and a Codex binary at a hard-coded path; `home*` tasks rebuild from an export in `sessions/`. A passing trial proves one model met `assess()` once. |
| `desk-shell/checks/checks.js` | In-page: `await import('/checks/checks.js')` | Not run (browser module; server down) | 18 measured DOM checks (type scale, AA contrast, 8 px grid, clipping, focus, motion, window management, text-vs-screen agreement…). Refuses to score an unbooted page. | It needs a live page; it cannot run under Node. Its console-error check is blind to errors thrown before import. |
| `desk-shell/checks/lens-agreement.js` | In-page: `L.run('lens','iris','notes')` | Not run (same reason) | Scene tree and painted DOM joined on `data-key`: every scene node painted, nothing extra, roles resolve, gestures live, boxes exact. | Only one lens at a time, only on a page someone has open. |

## 2. Verified live versus only in code

**Verified live** (dated; not re-run today):

- Lens painter, 18 Sep (`checks/results.md`): 38/38 scene nodes painted, 0 extra; 8/8 declared boxes exact to the
  pixel; 3 type sizes, minimum contrast 5.58:1, one token set. Grid, motion, window management and scrollbars fail;
  there are no focusable controls on `lens.html`.
- Desktop shell, pass 11 (`results.md`): no visible keyboard focus, 0 transitions, no minimise or maximise,
  87 of 130 text runs on sub-pixel baselines. Type went from 12 sizes to 7.
- `desktop` lens: 200 scene nodes, 200 painted; a reader's selection survives another actor's act
  (`THE-MISSING-PIECE.md`, final section).
- 19 shell and app defects reproduced by Rook on 18 Sep (`checks/rook-bugs.md`).
- **Run today** in scratch session `doc-iris`: a `;` batch keeps step 1 after step 2 is refused; a `script`
  definition makes no event, so the next bare `undo` skipped it and reverted the earlier `create` (the receipt named
  it); `--as nobody-real` was accepted and recorded as the author.

**Code only:** stale-lens gesture refusal and item fencing in `deskd.py`; last-good-lens fallback (`scene.py`);
`only when` and click `$x $y` (present in `scene.py`, though `THE-MISSING-PIECE.md` still lists them as unbuilt);
every "fixed" status below that is not marked live.

## 3. Known defects and limitations

| # | Defect or limit | Status | Evidence |
|---|---|---|---|
| 1 | Notes and Together windows are view-only: no command, lost on reload | open | Rook #1; `shell.js` still renders `not in the world` |
| 2 | Dragging a view-only window sends nothing | open for view-only windows; world windows send `move`/`resize` | Rook #2; `shell.js:144,156` require `ctx.node` |
| 3 | Window can be dragged below the dock and lost | open | Rook #3; `shell.js:141` clamps only `top ≥ 0` |
| 4 | "as text" overflows and clips the close button | unverified | Rook #4 |
| 5 | Escape on a new-note draft creates the note | open (code) | Rook #5; `notes.js:466–474`: `done(false)` removes the box, which blurs the input, and `onblur` calls `done(true)`. The same double removal explains Rook #18 |
| 6 | `"` in a title silently becomes `'` | open | Rook #6; `notes.js:48` |
| 7 | Title ending in `\` refused; `/api/do` returned `error: null` | server half fixed (code); client escaping open | Rook #7; `deskd.py` now lifts `ERR` lines into `error`; `notes.js` escapes only quotes |
| 8 | Dragging a card's link dot moves the card | unverified | Rook #8 |
| 9–10, 12–16 | Stale honesty meter, narrow-viewport bar, overlapping new notes, duplicate Editor rail rows, 300×160 Editor, Ctrl+A in titles, card height ≠ recorded height | unverified | Rook #9–10, #12–16 |
| 11 | Title-text drag starts native text drag | fixed (code) | `shell.css:30` `user-select: none` |
| 17 | Window sticks to cursor after lost `pointerup` | open (code) | Rook #17 (seen once); no pointer capture or `pointercancel` in `shell.js` |
| 19 | Failed `/api/do` leaves no mark on screen | unverified | Rook #19 |
| B1 | Bare `undo` after a refusal reverts something older silently | fixed: receipt names the event and time (**run**) | bridge `a15`; `desk.py:741–743` |
| B2 | Candidate lens activation must keep the active definition and local work | open (design); Astra's adapter is not installed | bridge `a22`; no import from `research/shared-visual-desk/` in `deskd.py` or `scene.py` |
| L1 | Style panel edits live only in page memory | limit | `shell.js` `apply(ed.value)`; nothing persisted, not even `localStorage` |
| L2 | Lens: no window chrome, no keyboard focus, no transitions | open | `results.md`, lens section |
| L3 | Prose native (`desk-shell/natives/prose.js`) not mounted | limit | no reference from shell, painter or server |

## 4. Persistence and safety (code)

- **Pickle is the database.** Each session is one `sessions/<name>.pickle` of the whole Python `Desk`, rewritten in
  place with `write_bytes` (no temp file or rename). A crash mid-write can truncate it. There is no separate journal
  and no format versioning; a class change can make old pickles unloadable. `pickle.loads` executes code, so a
  session file must be trusted.
- **Every request rewrites the session.** `deskd.Session.__exit__` saves on every `GET` (`/api/snapshot`,
  `/api/events`, `/api/scene`) as well as on `POST`. Each browser tab polls every 1.5 s. A `GET` for an unknown
  session creates it. `__exit__` also saves after an unexpected exception, so a crashed command can persist half-done
  state. The CLI saves once at the end, so a crash loses that whole invocation.
- **The lock is advisory and can be lost.** It is an `O_CREAT|O_EXCL` lock file. Any waiter deletes a lock older
  than 60 s, even when its holder is still working. If the lock is never acquired (60 s CLI, 30 s server), the loop
  **continues without it**, and the server then deletes the other holder's lock on exit.
- **No authentication.** The server binds `127.0.0.1:8780`. It checks no `Origin`, token or `Content-Type`
  (`json.loads` on any body), so any local process, and plausibly any web page the user opens, can post commands
  (untested). The actor is whatever `as` says: `alex` by default on the server, `jeff` on the CLI. A CLI line
  starting `!name verb …` writes as another actor directly and bypasses `deskd`. Revision fences coordinate honest
  actors; they are not access control.
- **What undo cannot reverse:** external effects (`launch` is marked `external`; `world.undo` refuses it); any event
  that is not the latest change to its target; rule and script definitions, `rule drop` and `script drop`, which make
  no event at all; painter observations (`/api/observe`); partially applied `;` batches (each step is separate; there
  is no rollback). Group undo applies steps one by one without rollback if a later step refuses.

## 5. Corrections to the Codex draft of Current Implementation

1. "A per-session file lock around load, execution and save" omits that the lock is stolen after 60 s and skipped on
   timeout, and that reads save too.
2. "Undo supports recorded changes … does not reverse external effects" omits that rules and scripts are not
   recorded, that batches are not atomic, and that only the latest change to a target can be undone.
3. "Browser-local styling" should say page memory: it is lost on reload.
4. "Intended for trusted local use" is right but should state the consequence: no origin check on a state-changing
   JSON endpoint.
5. "The four existing `test_scene.py` checks" is true but should say these are the only automated tests of this desk.
   The 16 parent-lab tests cover a different implementation.
