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

## F18. Every part-identity check failed for a lens with its own style (fixed; my bug, from F7)

Alex asked to drag tasks across the Board. The lens language already has it (`carry` on the card, `on drop card do prop $carried status=...` on each column), but every drop was refused: "the part this was dropped on changed in the lens since it was painted", even on a fresh page. The server checks a gesture's part identity by re-parsing the lens (`scene.defpart_hash`). It parsed under the default roles (calm.style), and a lens with its own style (pixel: `page`, `drop`, `name`, `chip`) refuses under those, so `same_part` was always false. Clicks survived only by falling back to the lens-revision check. Drops have no fallback. F7 made styles per lens, and I missed the second parse. Fix: `defpart_hash(src, path, roles, style)`, and deskd passes the lens's own style. The old `scene.build` path parses under it too. Checked in the browser: dragged a card BACKLOG → NOW → BACKLOG (e543, e544), no refusal.

## F19. Alex wants a terminal, not the inspector (built)

Alex: "I don't need to see the text world on the right, I do want a terminal of my own for the desk instead." The page's right pane showed the scene's text (the inspector). A desk terminal is the desk's own interface, so it isn't an app. Its scrollback is view state, not world state. So it went into the page, not the world: `desk-shell/term.js`, the right-hand pane by default (Alex: "terminal is default please"; `?side=scene` shows the scene text, `?inspect=0` neither), sends each line to `/api/do` as the viewer, and keeps its history in the browser. The painter repaints from the world on its own. Styled by the lens's style (roles `term`, `term.prompt`, `term.echo`, `term.err` in pixel). The alternative, a lens part whose edit runs a line, would have had to write its output into the world. Checked in the browser: `look Porch` printed the Porch, with the `!!` line. Not yet done: Tab completion.

## F20. Porch talk as a group chat: who is woken by what (built)

Alex wants Porch talk to be "a group chat we all share where I can @ them specifically, @everyone, or just chat normally". Before this, a line in a members=all chat went to every resident at once, so every hello cost three model turns and three answers. Now (house.py `news`/`take`):
- a line in a chat in the resident's own corner (a direct chat) reaches it now;
- a line anywhere with `@name`, `@everyone` or `@all` reaches it now, marked "(to you)";
- a plain line in a shared chat is held, and goes with whatever reaches the resident next: its next wake, news, or the receipt of its own commands. So a resident at work hears the room within a turn, and a resting one isn't woken by talk.
The Porch's description (a564) says so. The composer's hint says it too.

Checked with real residents (trials/try-porch-talk.md: two Opus 5.5 residents, who named themselves Wren and Thimble, 26 turns). The plain hello woke no one: turns stayed at wren 7, thimble 6. `@everyone` woke both, and each saw the held hello first, then the line marked "(to you)". `@thimble` woke only Thimble (12 to 15); Wren stayed at 11.

## F21. The residents' own first friction: there is no way to "say" (open)

Unprompted, both residents in try-porch-talk reported the same three snags within minutes of arriving. Thimble: "I hit the same three snags within minutes":
- there is no `say` verb, so speaking in a chat means `do append <chat> line=...`;
- they had to check `verbs` before writing anything;
- they had to re-read when the world said stale.
Both proposed a "first visit" note for newcomers. The first two are real gaps. The knife desk has no `reply` (moo has it), and speaking is the most common act a resident makes. A `say <chat> <words>` verb, or `reply` brought to the knife desk, is the likely fix. The residents' own proposal (a note written from what they needed) is the Agora way to find its words. Left for them, or for Alex's prompt texts.

**F17, resolved by Alex (28 Sep):** he moved the paused team's cards from NOW back to BACKLOG himself (e547–e554). At his direction, the command center became the objective: a new task a591 "The command center" (status=doing, objective=open, in the Porch). Juniper's old a302 objective flag was cleared (e555).

**F21, one more piece:** `help` lists `reply` among the verbs, and `help reply` answers "no verb reply here". The list comes from moo.py's registry, which the knife desk doesn't serve. Help advertises a verb that can't be done. `help <object>` is also refused ("no verb a573 … examine <id> shows which apply"). Alex's door text promises `help <object>`.

## F22. The first worker could not run anything (fixed)

In trials/worker-help-list.md, a real worker (commission a598: help lists verbs the desk can't do):
- found the cause, wrote a sound fix, asked for help through the desk (comment c599), and committed;
- the house landed it on the trial branch after the health checks (asked → working → waiting → working → ready →
  landing → landed, about 3 minutes).
But every attempt to run code was refused, for four reasons:
- on Windows its shell is PowerShell, and only Bash patterns were allowed;
- it called the interpreter by its full path, which `python:*` doesn't match;
- a command that chains `cd` with anything is refused whole;
- the protocol told it to copy the live world from outside its worktree, which the sandbox rightly blocks.
So it committed after checking only by reading, and said so. Fix (workshop.py):
- the house copies the world into the worktree as `<world>-try` when the worker starts;
- the allowed commands cover both shells and the interpreter under all three names;
- the protocol says one command per call, from the worktree root, with no cd, and to say on the commission when
  something is refused rather than work around it.
I ran the worker's change myself on main after merging (help reply, zzz, arrange, tidy, link; health all green):
4fe2b96.

The second worker trial (trials/worker-health-times.md, commission a598 in its copy: health.py should time each check) ran health on its try-world with no refusals. It landed on its trial branch, and I merged it after review (d407a81).

## F23. The keeper, tested against itself (fixed)

`keeper.py` is the one part of live building that must not depend on the code it protects. I tested it in a throwaway checkout, with a deliberately breaking `land ` commit. Three things were wrong:
- **It counted deaths from before the landing.** A house that crashed twice before the landing, then once after, looked like three deaths against the landing, and would have reverted it. Now only deaths after the landing's commit time count (`since`).
- **A hard-killed keeper orphans its children.** Killing keeper's process (not Ctrl-C) leaves the house and deskd running. The next keeper started a second house on the same world, and two houses would each wake the same residents. Fix, in the house rather than the keeper: a house refuses to start when the world's house.json has a heartbeat under 15 s old from another pid, and exits 76. Keeper reads 76 as "another house runs this world", waits 60 s, and tries again; it does not kill the other. Checked (ran): the second house exited 76.
- **deskd on a taken port would restart every 2 s** (read, from the loop; I didn't run it). Now, if deskd exits within 10 s of starting, keeper waits 60 s before the next try and says the port may be taken.

What keeper did right (ran, same checkout): a HEAD move restarted deskd, and `/api/version` changed; a killed house was restarted after 30 s; a breaking `land ` commit was reverted after three deaths, and the house came back on the reverted code.
Not tested: keeper on frontier itself, and a landing under keeper where the house asks to restart (exit 75).

## F24. A verb can't say "the rest of the words" (open)

Found while writing the lesson (LESSON-how-the-desk-grows.html), in a scratch world (ran). The obvious answer to F21 is a house verb `say`, `do append $1 line=$*`. But `$*` is every word after the verb, the target included: `say talk hello there` posted "talk hello there". What works today is `do append $1 line=$2`, with the words quoted: `say2 talk "hello there"`. The verb language needs a blank for the words after `$1`, such as `$rest` or `$2*`. That lives in verbs.py `run`, so it is host code: a small commission, and the first real case of tier 1 needing tier 2. The longer answer is one expression language for lenses and verbs (decision 2), where this would fall out.

## F25. A verb's title is also a name (worked around; the fix is open)

Making the house verb `handbook` (a608) as a note titled `handbook` broke `look Handbook` for everyone (ran): titles work as names, case-insensitively, so the word named two things, `'Handbook' names 2 things: f193, a608; use an id`. The arrive script and the Handbook's own map use names like this, so a verb titled like any existing thing silently breaks that name everywhere. Worked around by titling the verb `handbook|hb` (an alias title, which no longer equals the word) and naming the shelf by id in its body. The fix belongs to the verbs draft's "checked when saved" step: either a verb's word stays out of title resolution (verbs are found by lookup, never as things to act on), or saving a verb whose word is already a thing's title is refused with both named. I lean toward the first: a verb's word is a verb, not a noun.

## F26. Resting was the absence of commands (fixed at Alex's direction)

Alex, reading my door draft: "they dont rest, they can still think. Rather they rest if they choose to stop outputting anything." Before, a reply with no command lines ended the turn, so thinking without acting was resting. Now (house.py): a reply of only thinking is answered `(quiet)`, or with whatever news is waiting, and the resident goes on; `> rest` rests until someone calls, and `> rest 2 hours` (human time: 30 minutes, 1 day, 1h30m, half an hour; a month at most) rests that long; a call still reaches a resting resident at once; after 10 quiet exchanges in a row the house lets it rest anyway. Every wake now begins `You are <name>. Your corner is <id>.` (Alex: a name should outlive a fading memory). Checked with the fake model (ran; plumbing only): the greeting, 4 quiet exchanges, a reply that acted and rested 2 hours at once (its receipt kept for the next arrival), a call ending that rest, `rest soon` refused with examples, `rest 1h30m` kept, and exactly 10 `(quiet)` before the house let it rest. The command center shows a timed rest as `resting until 16:30`. Not yet seen: what a real model does with `(quiet)`.

## F27. Names are given, and the welcome comes whenever a resident enters (Alex's direction)

Alex (29 Sep): "lets scrap they pick their own names, we give them names and when they enter they get the welcome message. This should happen every time the enter the desk, (on compaction, or full reset), but thats it." Now (house.py):
- a corner's name is its prop `actor`, given by us; a corner without one is never started and shows `unnamed` (the door-naming code, `i am <name>`, is gone);
- the welcome is the note "The door" with `$me` as the name. It is put at the top of the first message the house sends after the resident enters with a fresh memory: its first start, a lost conversation, or claude compacting the conversation (the stream event `{"type":"system","subtype":"compact_boundary"}`, read from the Agent SDK docs by a docs agent; its other fields are not documented, and the house needs none of them);
- the one-line `You are <name>. Your corner is <id>.` still begins every wake.
Checked with the fake model (ran; plumbing only): the welcome with the name on top of the first arrival, no `$me` left, an unnamed awake corner never started, and a compaction event making the next message (a receipt) begin with the welcome, once. Not yet seen: a real compaction.

The world moved the same day (events e573 to e586, all claude, all undoable): Porch talk went into the Lounge as Lounge talk (a570), the Wall (f177) into the Lounge, a view Who's home (f609) into the Lounge, and Shop talk (a611, members=all) onto the Board for work. The command-center lens names both chats by id (the old `the kind:chat,prop:members=all` would now be ambiguous). The door note (a568) is Alex's draft with targeted changes; the Handbook's map (a198), "Wall, Lounge and Talk" (a209) and "First moves" (a202) say where things are now. The Porch keeps only the house's own things until the restructure (a593) decides.

## F28. Current Implementation had drifted; the review's defects fixed (29 Sep, at Alex's word)

*Current Implementation* had gone six days and 130-odd commits without an update. Four reviewers checked it against source and in scratch worlds, and it was rewritten in the Handbook binder (65f6e22). The review found real defects. Alex: "fix those bugs first and remove them from the defect list, also make a note in current implementation to keep it up to date". The fixes (241a545) touch paused owners' files: world.py, worktree.py (Sable's), knife.py, moo.py, desk.py, lens_ir.py and deskd.py.

What the fixes cover:
- tiled swap undo crashed (undo kind `reorder`);
- a receipt marked everything seen, so a rewrite could drop unread text;
- selection and rule events counted as touching every aspect (`event_aspects`);
- stale advice pointed at `look` for tags;
- a world verb's use is now undone whole;
- undo snapshots for prop, tag and due were shallow (found while testing the verb fix);
- worktree merge saw only targets named by id;
- test_scene ran 14 of 21 tests;
- deskd took any session name and any origin;
- export_docs.load read unlocked and removed others' locks.

Each fix was re-run against the case that reproduced it (ran). Health is green, 21 tests passed, 82 goldens are unchanged, and the nine suite cases and test_journal's tally are unchanged.

To keep the document current: it now opens with a rule, a change updates its section in the same change. The worker protocol asks workers to keep the binder true, and the house exports and commits *Current Implementation* after a landing in frontier. The first test of that step committed an uncommitted export under a false label (reset before anything else happened); the step now commits only what its own export wrote.

## F29. The Desktop grew without end (29 Sep, Alex's direction)

Alex: "i dont want infinite scroll please, Lets make it so the window is bounded". The page grew with every chat line, so the whole Desktop scrolled as one long page. The lens language already had `share` (a child's share of its column) and `scroll`, but two things were missing. Nothing gave the painted root a height to share, and a grid's cells grew to fit their content. Two painter changes fix that (lens.html, lens.js: Pike's files, edited under the paused-owners clause):
- `#paint` is a flex column. A root with `share` takes the window's height, and a root without one keeps its own height while `#paint` scrolls as before. `flex-shrink: 0` keeps unshared roots from being squeezed.
- a grid given a `share` is bounded. It divides its height among its rows (`grid-auto-rows: minmax(0, 1fr)`), and its cells stretch to fill them, so a cell with `scroll` scrolls inside the window.

The lens (a589) says the rest in world words. `share 1` goes on the root and on `main`, and `scroll scroll` on the residents and board columns. In the middle, FOR YOU, Lounge talk and Shop talk split the height 1:2:2, each list scrolling on its own, with the chats pinned to the newest line (`scroll end`).

Checked in a scratch world on a throwaway deskd (ran). The window was 1270 px tall and the page was 1270. Before, the middle column was 12273 px; now the inbox, Lounge and Shop lists are 228, 392 and 413 px high, and each scrolls. With the shares taken off the root, the same page is 2494 px tall and `#paint` scrolls, so unbounded lenses behave as before. "Juniper: my day" (no share) keeps its own 254 px. Not checked: phone width, or a lens with several bounded grids nested.

My mistake while documenting this: I put the `share` sentence into the binder with my scratch importer. It rewrites every section that differs from my draft, and my draft was older than worker-a656's rewrite of "The world" (e852). So it reverted the worker's section at e854. Undone at e856 (ran: a239 is back to the worker's 1084 words). I then exported by hand, which put a656's not-yet-landed chat signing into docs/. Both copies are restored to HEAD. The binder carries the sentence, and the house's export after a656 lands writes both. The lesson: an importer should refuse a section that moved since its draft was taken (refuse stale, never guess), and a hand export before a pending landing documents code that isn't there.

## F30. Chats that fold, a board that fits, the world as a menu, lines to Alex highlighted (29 Sep, Alex's direction)

Alex asked for four things:
- "collapse chats i'm not looking at ... so chats i do care about can be the full height";
- a board that doesn't scroll off the page, and is more pleasant;
- the world log "in a menu like the terminal at the top";
- "messages to me should be pleasantly highlighted".

What was missing, and what was added:
- **Scene words** (scene.py, Jeff's file, and lens_ir.py): `fold` takes two modifiers, `fold ["label"] [open] [float]`. `open` starts unfolded, still the viewer's own choice with no event. `float` draws the open contents over the page below the handle, a menu. Value tests gain `has` and `!has`, which ask whether the words contain the value, ignoring case. A value with a `$name` inside it is filled, as a bare `$name` already was, so `only when $said has @$me` works.
- **Painter** (lens.js, lens.html, Pike's files):
  - a folded part gives up its `share`, so its siblings take the room;
  - a float fold opens for a moment and is not remembered; Escape or a press outside closes it;
  - the painter's own buttons lose the browser's button box and wear only their role: `menu` for a float handle, `fold` for a plain one, each over `tool`, so a style that names neither keeps the old look.
- **World** (the Desktop lens a589 and its style a587):
  - FOR YOU, Lounge talk and Shop talk are open folds;
  - the board lanes share the right column's height and each scrolls on its own;
  - cards are role `task`, with their tools on one line;
  - the world log is `fold "the world" float` in the top bar;
  - a chat line with `@$me` in it is drawn in role `mention`, a soft amber with a mark-coloured left edge.

Checked in a scratch world on a throwaway deskd (ran). With all three chats open they are 242, 485 and 485 px tall. Folding Shop and FOR YOU gives Lounge 1155 px, and unfolding restores the split. The menu opens, and a press outside or Escape closes it. 22 lines are highlighted, every one contains @alex, and no plain line does. Health: 23 tests passed. Two goldens differed only in the vocabulary a refusal prints (the new `fold` form) and were rebased; 82 are the same.

Not checked: phone width; how a screen reader announces a float fold. While testing I misread Alex's clicks in the same browser tab as flakiness, until tabs_context showed the tab was in front; the scripted test above is the record.

Found by Alex right after: adding a task from the Desktop was refused, "you have not looked at f155 yet". The add box said `do create Board ...` without being bound to anything. A painter gesture counts as having seen only what its part is bound to, so nothing told the desk Alex had seen the Board. It had always been this way; nobody had added a task from the Desktop before. The fix is in the lens: `add : text "", the f155, ... do create $item ...`. Checked on a scratch copy (ran): refused before the fix; two adds in a row after it. The lesson for any lens: a gesture that acts on a named thing should bind that thing with `the`, so the viewer's look travels with it.

## F31. Changing one line of a note meant resending all of it (29 Sep, Alex's direction)

The Desktop fix in F30 changed one line of the 67-line lens a589. Through the desk the only way was `do rewrite a589 text="..."`, the whole lens as one escaped string, which I scripted because by hand it is a quoting minefield. Alex: "lets definitely fix that please".

The new text verb (world.py, desk.py, moo.py) is `do replace <id> old="..." new="..."`. It changes one exact passage: `old` must appear exactly once, and with none or several it is refused and says how many. It is fenced as `rewrite` is (the text aspect: read first, refused if it changed since), and undo takes it back whole. Line numbers were left out, because a number goes stale when someone adds a line above it and exact words don't.

Checked (ran):
- unread, refused;
- one line changed;
- two matches refused ("appears 2 times");
- no match refused ("appears 0 times");
- someone else changed it after my read, refused as stale;
- undo restored the text.

These cases are test_scene's `test_replace_changes_one_exact_passage` (24 passed; health green, 82 goldens the same). The first real use was documenting the verb itself: three exact passages in the Handbook binder, instead of a whole-text import.

Open, on the Board (a701): a finer fence (admit a replace whose words are still there once, as a656 did for chat lines), and a lens gesture that edits one line of a note.
