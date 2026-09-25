# desk-shell: one desktop, one world, one owner per file

Run: `python deskd.py 8780` (already running). Open http://localhost:8780/?session=desktop&as=alex .
The same world from a terminal: `python explore.py desktop --as <name>`.

## The law
1. The world lives in `deskd`. **Every change is a desk command line** sent through `Desk.do(line)`. An app may
   never change the world any other way, and keeps no state the world does not have except honest view state.
2. Every app implements `text(ctx)`: what a text-only inhabitant reads for this window right now. If the screen
   shows something `text()` cannot say, that is a defect in the app or a gap in the desk. File it.
3. One owner per file. **Never edit a file you do not own.** Two people writing one file already lost work once
   in this studio. To ask an owner for a change, post a note on the studio desk tagged `to-<owner>`
   (`do create Commons kind=note title="to wren: ..." tags=to-wren`); owners check `find tag:to-<self>` at each visit.
4. If the desk itself cannot say something you need (a verb, a field, a selection term), do not fake it in
   JavaScript. Post `to-jeff` with the smallest addition that would do, and build around it meanwhile.

## Owners
| file | owner | what it is |
|---|---|---|
| `deskd.py`, `desk.py`, `desk_moo.py`, `desk_knife.py`, `knife.py`, `scene.py`, `explore.py`, `test_scene.py` and the rest of the lab's Python not listed below | Jeff (host) | the server, the verb gateway, selections, the lens compiler. Requests: tag `to-jeff`. |
| `../world.py`, `../worktree.py` (notation/) | Sable (from 25 Sep) | the world's events, undo, persistence and forks; the pickle becomes a rebuildable cache behind a switch. Jeff asks for verb-side changes with `to-sable`. |
| `core.js` | Wren | the only code that talks to the server; the app interface |
| `index.html`, `shell.js`, `shell.css`, `style/*` | Wren | the desktop: dock, windows, bar, the "said" panel, the style language made real |
| `apps/notes.js` | Flint | Notes: a spatial canvas idea space, flexible and creative |
| `apps/editor.js` | Moss | Text editor, Google-Docs-like: a page, an outline rail, comments in the margin, typing that settles |
| `apps/third.js` (rename freely) | Lark | the application of the studio's own choosing; Lark leads the choice, everyone votes in Studio talk |
| `checks/*` | Pike (from 25 Sep; Iris's studio-era files stay as they are, new work under `checks/continuity/*`) | browser continuity checks driven with real input, reporting into the desk |
| `../journal.py`, `../test_journal.py` (notation/, new) | Sable (from 25 Sep) | the operation journal the world rebuilds from, and its replay, crash, identity and merge tests (charter: Sable's corner, a296). `world.py` and `worktree.py` handed over 25 Sep (row above). Requests: tag `to-sable` |
| `../suite/*` (notation/suite/: the everyday-task suite, its oracles and runner) | Juniper | every pressure-tested everyday task as an executable, self-judging script; counts writes, repairs, silent and visible wrongs per task per commit. Requests: tag `to-juniper` |

New files are fine inside your own area (`apps/notes/*`, `style/*`, `checks/*`). Add a `<script>` tag by asking Wren.

## What is here now
A deliberately plain skeleton that runs end to end: a dock, draggable windows, an "as text" toggle on every
window, a "said" panel showing each gesture as the command it became, and three stub apps. Replace all of it.
The session `desktop` has an Alex side, a Claude side and a Shared side with a free `Canvas` and a `Welcome` doc.

- **Pike** owns `lens.html`, `lens.js` from 25 Sep (the generic painter for `scene.py`; it knows no app and may never learn one, and grows only by primitives). **Jeff** owns `scene.py`, including the gesture node's `def` and `reads` fields the painter fences on. New scene words are asked for with `to-jeff` and must be printable as text before they may be painted. See `design-studio/THE-MISSING-PIECE.md`.
