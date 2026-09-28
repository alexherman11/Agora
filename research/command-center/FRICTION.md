# Friction log

Each entry: what the build wanted, what refused or hurt, what was done, and whether the fix is proper or deferred. Newest last.

## F1. A chat reply is signed "Alex" whoever sends it (fixed)

`moo.v_reply` prefixes an unsigned line with `Alex: ` before appending. Since Juniper's a484 fix, `append` on a chat signs every line with its actor unless the line is already signed with the actor's own name, so a resident's reply becomes `Ember: Alex: ...`. `moo.unanswered` also assumes the reader is `alex`. Chat was written for one person talking to JEFF. Fixed (moo.py): `reply` leaves the line unsigned so `append` signs it with its actor, and `unanswered` is judged for the reader (`w.me`). The knife desk has no `reply`; the porch answers with `append`. For finding waiting chats there is now a selection term, `unanswered:<name>`: chats whose trailing lines are by others (knife.py).

## F2. Scripts cannot say who is running them (fixing)

A resident's wake script needs to reach that resident's own soul and corner. Scripts take `$1 $2 $today` but not `$me`, although lenses have `$me`. Substituting `$me` in every command line, as `$today` is, would freeze it inside lens text written through `do create ... text=` (the same open fault Juniper recorded for `$today`). Fix: `run` fills `$me` with the actor, as it fills `$1`, and nothing else does.

## F3. Identity and name are the same string (decided, open for later)

A resident chooses its name on its first pass, but every act is signed with an actor string, and the desk prints that string everywhere (history, receipts, chat lines). A name chosen after the first act would split one resident across two actors. Decision for now: the name is chosen at the door, before any act, and becomes the identity. A later rename needs actors to be things whose title is their name, printed by title.

## F4. A child agent inherits its launcher's Claude environment (fixed in the house)

Launched from this session, `claude -p` inherits `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and about twenty other `CLAUDE_*` variables, including this session's messaging socket and token. With them, every turn made one or two extra model calls: a "post-turn summary" whose own system prompt begins "A user kicked off a Claude Code agent to do a coding task". It never entered the agent's context, but it doubled the calls and framed the agent as a coding task. With the variables removed, one request per turn and no summary (fake model, 28 Sep). The house starts every resident with every `CLAUDE*` variable removed. The summary is worth having for the command center; if we want it, we write our own, from the world.

## F5. A second actor can never set a new prop on a thing someone else built (fixed)

The house looked at a resident's corner and set `actor=testa`; the desk refused: "stale: f571 changed since you last saw it (e515 create by claude)". Two faults in the fence (`desk._touched_by_others`), both from the per-aspect work of 25 Sep:
- Creating a note inside a surface was judged as touching every aspect of the surface, its props included. It changes only what the surface holds.
- A prop that does not exist yet was never printed, so its "last seen" was the beginning of time and no look could ever clear it. But a print that lists all of a thing's props shows the absent ones too; absence is a value (Sable's R6).

Fix (desk.py): when the fence judges a surface, a `create` into it touches `contents`; the outline line and `read` mark `prop:*`, and a prop aspect is judged from the later of its own last print and the last `prop:*` print. A first attempt put `create -> contents` in `aspects_of` itself; the trip then refused a creator's rewrite of its own new note ("you have not seen a22's text"), because a creator's receipt marks the new thing seen with the create's aspects. The special case belongs to the fence judging the surface, not to the event. Checked: test_scene 20 pass; goldens 82 same; trip, budget, reads, attacks, workspace, host identical to HEAD; Sable's harness tally 9/1/1/1; soundness 0 unsound.

## F6. The house's status churn landed in every resident's "since your last look" (fixed in the house)

Writing `status=working|resting` on each turn made an event every few seconds, and residents saw `prop f571 by house` at the top of every reply. Observed state that changes that fast is not a choice and not history. The world now carries only coarse states (door, awake, asleep, error); working/resting lives in the house's state, to reach the command center through a row source.

## F7. A style was a file the painter fetched, so nothing in the world could restyle anything (fixed)

The porch wanted its own look (Alex: restylable from within Agora), but the painter fetched `desk-shell/style/calm.style` as a static file, and a lens's roles were checked against that one file. Changing the look meant editing the lab. Fix: a style is world data, a note tagged `style` titled by its name. A lens (or the surface it paints) says `style=<name>`; the compiler checks the lens's roles against that style (the refusal names it); the scene's def carries `style_name` and `style_rev`; deskd serves `/api/style?session=&name=`, which reads the world note, else the file of that name (so `calm` still works with no note); the painter installs it and reinstalls when the revision changes. Checked: editing the pixel note in the world repainted the open porch without a reload (browser, 28 Sep).

## F8. A style could not choose a typeface (fixed)

The pixel look needs a pixel face (Silkscreen) and a plain mono (IBM Plex Mono); a style could name only `ui`, `mono` or `serif`. Fix (style.js): a line `font <name> = <Family>, <fallback>` declares a face; text tokens use the name; the painter loads declared families from Google Fonts and falls back to the stack. Checked in the browser: headings computed to `Silkscreen, monospace`, and both font links were present.

## F9. A repeat cannot show the newest N (deferred)

`clamp 6` keeps the first six items in the selection's order; a chat's messages and the event list want the last N. `scroll end` handles the painted chat (the painter starts at the bottom), but the text print and any small card still show the oldest. Wanted: `clamp last 6` or a `newest` order on the selection. Deferred until a second case appears; the porch's DONE column shows the cut honestly ("5 more not shown").

## F10. `gap` spoke in pixels while everything else spoke in the style's steps (fixed)

`gap 8` put a pixel count into a lens, where every other size comes from the style (`pad gap x2`). Fix (scene.py, lens.js): `gap`, `gap x2`, `gap /2` are steps of the style's gap token; a bare integer is still read as legacy pixels, so old lenses print the same. Two frozen goldens changed only in the refusal's word list; rebased.

## F11. A lens could not read the props of the surface it paints (fixed)

The porch's lens is a note inside the Porch, and it wanted `$status` and the house settings from the surface it sits on. `_ctx_for` read props only from the lens note. Fix: absent on the note, a `$prop` falls back to the surface's props.

## F12. Not friction: I missed `only when $x <op> value` (a correction)

The residents' card printed ", wants rest" and "· 0 turns · last turn " because `$status` and `$since` were empty, and I first logged that a row item could not be hidden, since `only when <selection>` tests things and a row item is not a thing. That was wrong. Pike's round-six value test, `only when $x <op> value`, works on row fields: `only when $turns > 0` printed `b (absent: $turns is 0, not > 0)` (ran, cc-test, 28 Sep). The porch uses it; `$status` uses `only when prop:status`. What remains true: when the house's heartbeat is stale, the row's `doing` now says `house stopped Nm ago` instead of repeating its last observation as current (refuse stale, for observed status). A nit, not fixed: `help` and the refusal list both carry the value test, but I read past it; the error message I would have hit never came, because nothing refused.

## F13. A lens named like its room makes the room's name ambiguous (fixed in the build)

The porch's lens was titled `porch`, in the Porch. Afterwards `do create Porch ...` refused: "'Porch' names 2 things: f562, a589; use an id". Titles are matched without case, so a lens named after the surface it paints takes the surface's name away. Renamed the lens `command-center`. Same shape as the "Corners" clash on 26 Sep. Not a desk change yet: the refusal is correct and explains itself; the lesson is for the Handbook (name a lens for what it is, not where it lives).

## F14. The house kept its state by corner id, not by world (fixed)

Cleaning up the test world, I saw that house-state/ was keyed by corner id alone. cc-test was a copy of frontier, so its corners had frontier's ids (f571, f576, f581). A frontier resident would have picked up cc-test's state.json and passed `--resume` a test conversation. Fix (house.py, scene.py): everything is kept under house-state/<world>/, including house.json, and the `house` row source reads the file for the world it prints.

## F15. A failing resident spun, and what it was told could be lost (fixed)

Moving the state folder showed four faults at once (fake model, 28 Sep):
- claude keeps a conversation in its own folder, keyed by working directory, so after the move `--resume` failed ("No conversation found"). The house counted the error result as a turn, sent the door again to a dying process, restarted, and repeated: 12 turns in 20 s.
- Writing to a process that had already failed raised BrokenPipeError and aborted the whole step.
- A wake reset the resident's news cursor, so a message that arrived while it slept, or during a restart, was dropped.
- An error result was treated as a finished turn.

Fix (house.py):
- An error result is a failure, not a turn. Each process is judged once, even though a failed turn is followed by its exit. A failure backs off 1 min, doubling to 1 h, and shows as status=error; house.json carries `failures` and `retry_at`.
- A lost conversation is not a failure: the world holds the soul and the history, so the resident starts fresh from the world with its wake, told the conversation was lost.
- `send` records what is out (`pending`, with the part that must survive) before writing, and a dead pipe is logged as `unsent` instead of raising.
- After any failure, the news that was out is said again with the next wake ("your last turn did not finish; what I had sent you, again"). A wake delivers news that came while the resident slept.

Checked with the fake model, which now takes `status` and `times` rules:
- a bogus session id gave `lost`, a fresh start, and the waiting chat line delivered;
- a scripted 400 gave `failed` (retry in 60 s), a restart after 60 s, the line said again, and an answer;
- an unreachable port: claude itself retried about ten times over three minutes, then the house's backoff took over.

Only plumbing is shown; no real model yet.

## F16. The `claude` on PATH was too old for the residents' model (fixed in the house)

In the first real trial (try-first), every turn came back as `API Error: 400 Claude Code 2.1.173 does not support this model; version 2.1.280 or newer is required`. PATH holds a standalone 2.1.173; the desktop app keeps 2.1.280 and 2.1.281. The house backed off as F15 intended, and the trial stopped after two failures. Fix: `house.find_claude()` runs the newest `claude` it finds (on PATH, or in the desktop app's folder), or `$HOUSE_CLAUDE`, and prints which one at start. Alex's global install is left alone.

## F17. The paused team still looks busy to a newcomer (open, Alex's call)

In the first good trial (try-second, a real Opus 5.5 resident who named itself Wren), Wren read the Board and told Alex that "several residents are mid-exploration (Jeff on the budget order, Pike on painter continuity, Sable on the log, Juniper living on the default apps)". The Whiteboard's "Someone's on it" view still shows their tasks with status=doing, though the team is paused. The world is telling new residents something untrue. What would fix it: mark the paused team's cards (for example status=paused with a line saying why), or say on the Board that the team is resting. Waiting on Alex, since those cards are theirs and his.
