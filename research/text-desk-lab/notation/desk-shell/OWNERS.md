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
| `deskd.py`, the lab's Python | Jeff (host) | the server and the world engine. Requests: tag `to-jeff`. |
| `core.js` | Wren | the only code that talks to the server; the app interface |
| `index.html`, `shell.js`, `shell.css`, `style/*` | Wren | the desktop: dock, windows, bar, the "said" panel, the style language made real |
| `apps/notes.js` | Flint | Notes: a spatial canvas idea space, flexible and creative |
| `apps/editor.js` | Moss | Text editor, Google-Docs-like: a page, an outline rail, comments in the margin, typing that settles |
| `apps/third.js` (rename freely) | Lark | the application of the studio's own choosing; Lark leads the choice, everyone votes in Studio talk |
| `checks/*` | Iris | the eyes' fixed script of measured checks, and their results |

New files are fine inside your own area (`apps/notes/*`, `style/*`, `checks/*`). Add a `<script>` tag by asking Wren.

## What is here now
A deliberately plain skeleton that runs end to end: a dock, draggable windows, an "as text" toggle on every
window, a "said" panel showing each gesture as the command it became, and three stub apps. Replace all of it.
The session `desktop` has an Alex side, a Claude side and a Shared side with a free `Canvas` and a `Welcome` doc.
