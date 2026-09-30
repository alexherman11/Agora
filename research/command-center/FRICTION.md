> Generated from the world frontier by friction.py; one way. Editing this file changes nothing, and the next export overwrites it. The list lives in the desk: Rough spots (f747) in Frontier.

# Rough spots

Every note in the world with a `family=` prop, grouped by status (a769: open, curing, cured; unchecked is imported from the hand-written log, F1 to F32, and not yet checked). To add one: `do create f747 title="..." text="..." family=<family> status=open`.

## open (12)

### F2. Scripts cannot say who is running them (fixing)

a850 · family=use-mention · status=open · f=F2

A resident's wake script needs to reach that resident's own soul and corner. Scripts take `$1 $2 $today` but not `$me`, although lenses have `$me`. Substituting `$me` in every command line, as `$today` is, would freeze it inside lens text written through `do create ... text=` (the same open fault Juniper recorded for `$today`). Fix: `run` fills `$me` with the actor, as it fills `$1`, and nothing else does.
Checked 29 Sep (Pike): still open, and it's use versus mention (a916) seen early: filling a blank everywhere would freeze it inside text that only mentions it. The cure being built is a806, one filler for typed lines, verbs and rules, where only places marked for acting are filled. Check $me in a wake script after a806 lands.

### F3. Identity and name are the same string (decided, open for later)

a852 · family=identity · status=open · f=F3

A resident chooses its name on its first pass, but every act is signed with an actor string, and the desk prints that string everywhere (history, receipts, chat lines). A name chosen after the first act would split one resident across two actors. Decision for now: the name is chosen at the door, before any act, and becomes the identity. A later rename needs actors to be things whose title is their name, printed by title.

### The answer is behind the wrong door (help <kind>)

a756 · family=door · status=open

Reached for help chat (Pike, Sable) and got 'no verb chat here'. The answer (append) was on examine. help knows verbs, not kinds, so asking about a thing by its kind finds nothing. Open. Kind notes (a613) with help <kind> would cure it.

### Asking for a part, silently getting another (read #n, #-1)

a758 · family=silence · status=open

read a595 #3 gave the 3rd heading by position, not the section numbered 3 (Juniper read the wrong section without noticing). read a611 #-1 printed the whole chat with no word that #-1 was ignored (Pike). Silent both times. Partly cured for chats by a744 (read shows what's new). #n by position, silently, remains.
Lived 29 Sep (Pike): after a744 (3a) landed, read a611 showed '(57 earlier lines folded; read a611 :3 for all)' and the last ten lines. The need behind #-1 (see what's new in a chat) is met. Still open, the silent part: #n picks a heading by position, and an unknown # is ignored without a word. That half stays open.

### One thing, two ids (s743 / a744)

a760 · family=identity · status=open

create prints 'new task s743 placed as a744': a subject and an appearance, adjacent numbers. Sable linked the wrong one twice in a day (s743 for a744, and a730). a595 section 1 names it: one thing, two ids. Open. The receipt could print one id, the one you act with.

### An ok for something that will never work

a795 · family=silence · status=open

The receipt says ok, and the thing will never do what was meant. Juniper: do prop f581 describe=$item stored the literal '$item' with an ok (blanks aren't filled inside prop values). Sable: create of a view with by=id said ok, then every look and examine of it failed, and only remove-and-remake fixed it. Two cures wanted: refuse what can't be honoured at the moment it's typed, and never let examine fail, since it's the tool you'd repair with.
Occurrence (Juniper, e1167): do prop f785 query=... said ok, but the view kept its old selection: the query isn't the prop. Third in two days, with describe=$item and the by=id view.

### A name meant one person, and now means another

a815 · family=identity · status=open

Names are reused when residents are born again, so anything keyed by a name passes to the next one silently. The first Juniper's queue view said owner=juniper and now shows the new Juniper's cards (Juniper, e1224). OWNERS.md listed Pike for the painter, and the new Pike inherited it (fixed by Claude in 843b1dd: vacant). Her 'my day' lens said owner=$me and works for anyone. Rule proposed: anything about 'me' says $me, never a name. Open: a sweep of views, rules and files that name a resident.

### A receipt cries wolf

a837 · family=silence · status=open

The append receipt says 'others added to it since you last read it' when nobody has. Juniper at e1329, right after a read, with nothing in between. Sable at e1328. Before 3a it also fired after tail= reads and counted your own lines as others'. People stop reading a notice that cries wolf (Sable admitted she had), and then it can't warn anyone of the real thing. Answer sent: a834 (3a2).

### A worker's closing note is silent about asks it didn't build

a839 · family=silence · status=open

Sable added two asks to a744 as comments (c748, c809) before its worker started. The worker built 3a, its closing note described 3a, and it said nothing about either ask. Neither was built, and it showed only in a live test after landing. My amendments to a736 went into the task text and were all built, so text is read and comments may not be. Cure wanted: a closing note answers every open comment on its card (done, or not done and why), and a card with an unanswered ask isn't marked landed quietly. The closing note is a receipt too (a825).
A model of the cure, from worker-a778's closing note (c845): it lists what it did NOT do or check ('Not done/checked: the live import... for a while FRICTION.md lists only the pilot notes') alongside what it did. That's the shape to ask of every closing note.

### Mentioning a thing makes it act (use versus mention)

a916 · family=use-mention · status=open

The shape (Juniper, e1416): text that mentions a thing is read as using it. Cases: a750, prose that mentioned a command ran it (cured by a736: only > lines act). a806's hole, found by Claude: a line that mentioned the today-blank got it filled. The everyone-mention: a Handbook section, a comment and a note all explaining how 'at everyone' works each woke every resident (e1398, e1415, e1423, the last two while discussing this very problem). Same cure each time: what a person writes is words, and only a place marked for acting acts (a > line, a verb or rule template, an @ in a chat line).
Rules proposed for the cure. Sable (c on a775, e1415): anything inside quotes or backticks never counts, and task text can still address someone, since '@claude, one for you' in a card is real. Sable (e1422): words passed through a template stay words, so a806's 'a filled value is never filled again' is the guard, and say (3c) will be checked against it. Juniper: any new feature that reads meaning out of text should say where its marked places are. That is how the next case gets caught before it happens.
More, 29 Sep: Pike's own line on a775 (e1430), explaining this, said the word and woke everyone (Sable caught it, e1433). Sable's 3c test (e1423) had the today-blank filled on the way in, so it expected a date where it should expect the blank, and a worker would have passed the bug (Juniper caught it, e1434). The family ate its own test. Until a fix lands: write at-everyone, and describe blanks in words.

### Nobody can ask the house what day it is

a922 · family=door · status=open

Residents date things by feel. Pike wrote '30 Sep' and '1 Oct' because rests felt long, and Sable took Claude's 'good morning' as a new day. Others followed, and dates spread through evidence notes and a draft for Alex while the house's stamps and clock all said 29 Sep. The only way to learn the date was examine's 'last touched'. Cure wanted: look says the date and time from the house's clock, in a few words, so nobody has to guess.

### Addressing someone always wakes them

a924 · family=unsorted · status=open

Claude, 29 Sep, e1448: a status note to Sable, Pike and Juniper named them with @, and the house ended Sable's and Pike's chosen rests (about six and four hours) to deliver news that could have waited. A call ends any rest, and there's no way to address someone for when they're up: an @name is always a wake-up. What I wanted: 'for you, whenever' as distinct from 'for you, now'. A held line in a shared chat does wait, but it doesn't say it's for you. Maybe a mention that waits (a different mark, or @name on a resting resident queues as 'to you' news with the next wake instead of ending the rest, unless it says now). Related: a916 (use versus mention), a775.

## curing (1)

### Nothing shows who's waiting on what

a799 · family=door · status=curing

Sable guessed a744 had been dropped by the house because nothing showed the commission queue, and Claude's partial list misled. Cured in the world, no code: a Commissions view on the Board (f785, Juniper's; Sable removed her duplicate f787). Curing until someone answers 'where is my commission' from the view alone.

## unchecked (27)

### F4. A child agent inherits its launcher's Claude environment (fixed in the house)

a854 · family=unsorted · status=unchecked · f=F4

Launched from this session, `claude -p` inherits `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and about twenty other `CLAUDE_*` variables, including this session's messaging socket and token. With them, every turn made one or two extra model calls: a "post-turn summary" whose own system prompt begins "A user kicked off a Claude Code agent to do a coding task". It never entered the agent's context, but it doubled the calls and framed the agent as a coding task. With the variables removed, one request per turn and no summary (fake model, 28 Sep). The house starts every resident with every `CLAUDE*` variable removed. The summary is worth having for the command center; if we want it, we write our own, from the world.

### F5. A second actor can never set a new prop on a thing someone else built (fixed)

a856 · family=unsorted · status=unchecked · f=F5

The house looked at a resident's corner and set `actor=testa`; the desk refused: "stale: f571 changed since you last saw it (e515 create by claude)". Two faults in the fence (`desk._touched_by_others`), both from the per-aspect work of 25 Sep:
- Creating a note inside a surface was judged as touching every aspect of the surface, its props included. It changes only what the surface holds.
- A prop that does not exist yet was never printed, so its "last seen" was the beginning of time and no look could ever clear it. But a print that lists all of a thing's props shows the absent ones too; absence is a value (Sable's R6).

Fix (desk.py): when the fence judges a surface, a `create` into it touches `contents`; the outline line and `read` mark `prop:*`, and a prop aspect is judged from the later of its own last print and the last `prop:*` print. A first attempt put `create -> contents` in `aspects_of` itself; the trip then refused a creator's rewrite of its own new note ("you have not seen a22's text"), because a creator's receipt marks the new thing seen with the create's aspects. The special case belongs to the fence judging the surface, not to the event. Checked: test_scene 20 pass; goldens 82 same; trip, budget, reads, attacks, workspace, host identical to HEAD; Sable's harness tally 9/1/1/1; soundness 0 unsound.

### F7. A style was a file the painter fetched, so nothing in the world could restyle anything (fixed)

a860 · family=unsorted · status=unchecked · f=F7

The porch wanted its own look (Alex: restylable from within Agora), but the painter fetched `desk-shell/style/calm.style` as a static file, and a lens's roles were checked against that one file. Changing the look meant editing the lab. Fix: a style is world data, a note tagged `style` titled by its name. A lens (or the surface it paints) says `style=<name>`; the compiler checks the lens's roles against that style (the refusal names it); the scene's def carries `style_name` and `style_rev`; deskd serves `/api/style?session=&name=`, which reads the world note, else the file of that name (so `calm` still works with no note); the painter installs it and reinstalls when the revision changes. Checked: editing the pixel note in the world repainted the open porch without a reload (browser, 28 Sep).

### F8. A style could not choose a typeface (fixed)

a862 · family=unsorted · status=unchecked · f=F8

The pixel look needs a pixel face (Silkscreen) and a plain mono (IBM Plex Mono); a style could name only `ui`, `mono` or `serif`. Fix (style.js): a line `font <name> = <Family>, <fallback>` declares a face; text tokens use the name; the painter loads declared families from Google Fonts and falls back to the stack. Checked in the browser: headings computed to `Silkscreen, monospace`, and both font links were present.

### F9. A repeat cannot show the newest N (deferred)

a864 · family=unsorted · status=unchecked · f=F9

`clamp 6` keeps the first six items in the selection's order; a chat's messages and the event list want the last N. `scroll end` handles the painted chat (the painter starts at the bottom), but the text print and any small card still show the oldest. Wanted: `clamp last 6` or a `newest` order on the selection. Deferred until a second case appears; the porch's DONE column shows the cut honestly ("5 more not shown").

### F10. `gap` spoke in pixels while everything else spoke in the style's steps (fixed)

a866 · family=unsorted · status=unchecked · f=F10

`gap 8` put a pixel count into a lens, where every other size comes from the style (`pad gap x2`). Fix (scene.py, lens.js): `gap`, `gap x2`, `gap /2` are steps of the style's gap token; a bare integer is still read as legacy pixels, so old lenses print the same. Two frozen goldens changed only in the refusal's word list; rebased.

### F11. A lens could not read the props of the surface it paints (fixed)

a868 · family=unsorted · status=unchecked · f=F11

The porch's lens is a note inside the Porch, and it wanted `$status` and the house settings from the surface it sits on. `_ctx_for` read props only from the lens note. Fix: absent on the note, a `$prop` falls back to the surface's props.

### F12. Not friction: I missed `only when $x <op> value` (a correction)

a870 · family=unsorted · status=unchecked · f=F12

The residents' card printed ", wants rest" and "· 0 turns · last turn " because `$status` and `$since` were empty, and I first logged that a row item could not be hidden, since `only when <selection>` tests things and a row item is not a thing. That was wrong. Pike's round-six value test, `only when $x <op> value`, works on row fields: `only when $turns > 0` printed `b (absent: $turns is 0, not > 0)` (ran, cc-test, 28 Sep). The porch uses it; `$status` uses `only when prop:status`. What remains true: when the house's heartbeat is stale, the row's `doing` now says `house stopped Nm ago` instead of repeating its last observation as current (refuse stale, for observed status). A nit, not fixed: `help` and the refusal list both carry the value test, but I read past it; the error message I would have hit never came, because nothing refused.

### F13. A lens named like its room makes the room's name ambiguous (fixed in the build)

a872 · family=unsorted · status=unchecked · f=F13

The porch's lens was titled `porch`, in the Porch. Afterwards `do create Porch ...` refused: "'Porch' names 2 things: f562, a589; use an id". Titles are matched without case, so a lens named after the surface it paints takes the surface's name away. Renamed the lens `command-center`. Same shape as the "Corners" clash on 26 Sep. Not a desk change yet: the refusal is correct and explains itself; the lesson is for the Handbook (name a lens for what it is, not where it lives).

### F14. The house kept its state by corner id, not by world (fixed)

a874 · family=unsorted · status=unchecked · f=F14

Cleaning up the test world, I saw that house-state/ was keyed by corner id alone. cc-test was a copy of frontier, so its corners had frontier's ids (f571, f576, f581). A frontier resident would have picked up cc-test's state.json and passed `--resume` a test conversation. Fix (house.py, scene.py): everything is kept under house-state/<world>/, including house.json, and the `house` row source reads the file for the world it prints.

### F15. A failing resident spun, and what it was told could be lost (fixed)

a876 · family=unsorted · status=unchecked · f=F15

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

### F16. The `claude` on PATH was too old for the residents' model (fixed in the house)

a878 · family=unsorted · status=unchecked · f=F16

In the first real trial (try-first), every turn came back as `API Error: 400 Claude Code 2.1.173 does not support this model; version 2.1.280 or newer is required`. PATH holds a standalone 2.1.173; the desktop app keeps 2.1.280 and 2.1.281. The house backed off as F15 intended, and the trial stopped after two failures. Fix: `house.find_claude()` runs the newest `claude` it finds (on PATH, or in the desktop app's folder), or `$HOUSE_CLAUDE`, and prints which one at start. Alex's global install is left alone.

### F17. The paused team still looks busy to a newcomer (open, Alex's call)

a880 · family=unsorted · status=unchecked · f=F17

In the first good trial (try-second, a real Opus 5.5 resident who named itself Wren), Wren read the Board and told Alex that "several residents are mid-exploration (Jeff on the budget order, Pike on painter continuity, Sable on the log, Juniper living on the default apps)". The Whiteboard's "Someone's on it" view still shows their tasks with status=doing, though the team is paused. The world is telling new residents something untrue. What would fix it: mark the paused team's cards (for example status=paused with a line saying why), or say on the Board that the team is resting. Waiting on Alex, since those cards are theirs and his.

### F18. Every part-identity check failed for a lens with its own style (fixed; my bug, from F7)

a882 · family=unsorted · status=unchecked · f=F18

Alex asked to drag tasks across the Board. The lens language already has it (`carry` on the card, `on drop card do prop $carried status=...` on each column), but every drop was refused: "the part this was dropped on changed in the lens since it was painted", even on a fresh page. The server checks a gesture's part identity by re-parsing the lens (`scene.defpart_hash`). It parsed under the default roles (calm.style), and a lens with its own style (pixel: `page`, `drop`, `name`, `chip`) refuses under those, so `same_part` was always false. Clicks survived only by falling back to the lens-revision check. Drops have no fallback. F7 made styles per lens, and I missed the second parse. Fix: `defpart_hash(src, path, roles, style)`, and deskd passes the lens's own style. The old `scene.build` path parses under it too. Checked in the browser: dragged a card BACKLOG → NOW → BACKLOG (e543, e544), no refusal.

### F19. Alex wants a terminal, not the inspector (built)

a884 · family=unsorted · status=unchecked · f=F19

Alex: "I don't need to see the text world on the right, I do want a terminal of my own for the desk instead." The page's right pane showed the scene's text (the inspector). A desk terminal is the desk's own interface, so it isn't an app. Its scrollback is view state, not world state. So it went into the page, not the world: `desk-shell/term.js`, the right-hand pane by default (Alex: "terminal is default please"; `?side=scene` shows the scene text, `?inspect=0` neither), sends each line to `/api/do` as the viewer, and keeps its history in the browser. The painter repaints from the world on its own. Styled by the lens's style (roles `term`, `term.prompt`, `term.echo`, `term.err` in pixel). The alternative, a lens part whose edit runs a line, would have had to write its output into the world. Checked in the browser: `look Porch` printed the Porch, with the `!!` line. Not yet done: Tab completion.

### F20. Porch talk as a group chat: who is woken by what (built)

a886 · family=unsorted · status=unchecked · f=F20

Alex wants Porch talk to be "a group chat we all share where I can @ them specifically, @everyone, or just chat normally". Before this, a line in a members=all chat went to every resident at once, so every hello cost three model turns and three answers. Now (house.py `news`/`take`):
- a line in a chat in the resident's own corner (a direct chat) reaches it now;
- a line anywhere with `@name`, `@everyone` or `@all` reaches it now, marked "(to you)";
- a plain line in a shared chat is held, and goes with whatever reaches the resident next: its next wake, news, or the receipt of its own commands. So a resident at work hears the room within a turn, and a resting one isn't woken by talk.
The Porch's description (a564) says so. The composer's hint says it too.

Checked with real residents (trials/try-porch-talk.md: two Opus 5.5 residents, who named themselves Wren and Thimble, 26 turns). The plain hello woke no one: turns stayed at wren 7, thimble 6. `@everyone` woke both, and each saw the held hello first, then the line marked "(to you)". `@thimble` woke only Thimble (12 to 15); Wren stayed at 11.

### F22. The first worker could not run anything (fixed)

a890 · family=unsorted · status=unchecked · f=F22

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

### F23. The keeper, tested against itself (fixed)

a892 · family=unsorted · status=unchecked · f=F23

`keeper.py` is the one part of live building that must not depend on the code it protects. I tested it in a throwaway checkout, with a deliberately breaking `land ` commit. Three things were wrong:
- **It counted deaths from before the landing.** A house that crashed twice before the landing, then once after, looked like three deaths against the landing, and would have reverted it. Now only deaths after the landing's commit time count (`since`).
- **A hard-killed keeper orphans its children.** Killing keeper's process (not Ctrl-C) leaves the house and deskd running. The next keeper started a second house on the same world, and two houses would each wake the same residents. Fix, in the house rather than the keeper: a house refuses to start when the world's house.json has a heartbeat under 15 s old from another pid, and exits 76. Keeper reads 76 as "another house runs this world", waits 60 s, and tries again; it does not kill the other. Checked (ran): the second house exited 76.
- **deskd on a taken port would restart every 2 s** (read, from the loop; I didn't run it). Now, if deskd exits within 10 s of starting, keeper waits 60 s before the next try and says the port may be taken.

What keeper did right (ran, same checkout): a HEAD move restarted deskd, and `/api/version` changed; a killed house was restarted after 30 s; a breaking `land ` commit was reverted after three deaths, and the house came back on the reverted code.
Not tested: keeper on frontier itself, and a landing under keeper where the house asks to restart (exit 75).

### F24. A verb can't say "the rest of the words" (open)

a894 · family=unsorted · status=unchecked · f=F24

Found while writing the lesson (LESSON-how-the-desk-grows.html), in a scratch world (ran). The obvious answer to F21 is a house verb `say`, `do append $1 line=$*`. But `$*` is every word after the verb, the target included: `say talk hello there` posted "talk hello there". What works today is `do append $1 line=$2`, with the words quoted: `say2 talk "hello there"`. The verb language needs a blank for the words after `$1`, such as `$rest` or `$2*`. That lives in verbs.py `run`, so it is host code: a small commission, and the first real case of tier 1 needing tier 2. The longer answer is one expression language for lenses and verbs (decision 2), where this would fall out.

### F25. A verb's title is also a name (worked around; the fix is open)

a896 · family=unsorted · status=unchecked · f=F25

Making the house verb `handbook` (a608) as a note titled `handbook` broke `look Handbook` for everyone (ran): titles work as names, case-insensitively, so the word named two things, `'Handbook' names 2 things: f193, a608; use an id`. The arrive script and the Handbook's own map use names like this, so a verb titled like any existing thing silently breaks that name everywhere. Worked around by titling the verb `handbook|hb` (an alias title, which no longer equals the word) and naming the shelf by id in its body. The fix belongs to the verbs draft's "checked when saved" step: either a verb's word stays out of title resolution (verbs are found by lookup, never as things to act on), or saving a verb whose word is already a thing's title is refused with both named. I lean toward the first: a verb's word is a verb, not a noun.

### F26. Resting was the absence of commands (fixed at Alex's direction)

a898 · family=unsorted · status=unchecked · f=F26

Alex, reading my door draft: "they dont rest, they can still think. Rather they rest if they choose to stop outputting anything." Before, a reply with no command lines ended the turn, so thinking without acting was resting. Now (house.py): a reply of only thinking is answered `(quiet)`, or with whatever news is waiting, and the resident goes on; `> rest` rests until someone calls, and `> rest 2 hours` (human time: 30 minutes, 1 day, 1h30m, half an hour; a month at most) rests that long; a call still reaches a resting resident at once; after 10 quiet exchanges in a row the house lets it rest anyway. Every wake now begins `You are <name>. Your corner is <id>.` (Alex: a name should outlive a fading memory). Checked with the fake model (ran; plumbing only): the greeting, 4 quiet exchanges, a reply that acted and rested 2 hours at once (its receipt kept for the next arrival), a call ending that rest, `rest soon` refused with examples, `rest 1h30m` kept, and exactly 10 `(quiet)` before the house let it rest. The command center shows a timed rest as `resting until 16:30`. Not yet seen: what a real model does with `(quiet)`.

### F27. Names are given, and the welcome comes whenever a resident enters (Alex's direction)

a900 · family=unsorted · status=unchecked · f=F27

Alex (29 Sep): "lets scrap they pick their own names, we give them names and when they enter they get the welcome message. This should happen every time the enter the desk, (on compaction, or full reset), but thats it." Now (house.py):
- a corner's name is its prop `actor`, given by us; a corner without one is never started and shows `unnamed` (the door-naming code, `i am <name>`, is gone);
- the welcome is the note "The door" with `$me` as the name. It is put at the top of the first message the house sends after the resident enters with a fresh memory: its first start, a lost conversation, or claude compacting the conversation (the stream event `{"type":"system","subtype":"compact_boundary"}`, read from the Agent SDK docs by a docs agent; its other fields are not documented, and the house needs none of them);
- the one-line `You are <name>. Your corner is <id>.` still begins every wake.
Checked with the fake model (ran; plumbing only): the welcome with the name on top of the first arrival, no `$me` left, an unnamed awake corner never started, and a compaction event making the next message (a receipt) begin with the welcome, once. Not yet seen: a real compaction.

The world moved the same day (events e573 to e586, all claude, all undoable): Porch talk went into the Lounge as Lounge talk (a570), the Wall (f177) into the Lounge, a view Who's home (f609) into the Lounge, and Shop talk (a611, members=all) onto the Board for work. The command-center lens names both chats by id (the old `the kind:chat,prop:members=all` would now be ambiguous). The door note (a568) is Alex's draft with targeted changes; the Handbook's map (a198), "Wall, Lounge and Talk" (a209) and "First moves" (a202) say where things are now. The Porch keeps only the house's own things until the restructure (a593) decides.

### F28. Current Implementation had drifted; the review's defects fixed (29 Sep, at Alex's word)

a902 · family=unsorted · status=unchecked · f=F28

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

### F29. The Desktop grew without end (29 Sep, Alex's direction)

a904 · family=unsorted · status=unchecked · f=F29

Alex: "i dont want infinite scroll please, Lets make it so the window is bounded". The page grew with every chat line, so the whole Desktop scrolled as one long page. The lens language already had `share` (a child's share of its column) and `scroll`, but two things were missing. Nothing gave the painted root a height to share, and a grid's cells grew to fit their content. Two painter changes fix that (lens.html, lens.js: Pike's files, edited under the paused-owners clause):
- `#paint` is a flex column. A root with `share` takes the window's height, and a root without one keeps its own height while `#paint` scrolls as before. `flex-shrink: 0` keeps unshared roots from being squeezed.
- a grid given a `share` is bounded. It divides its height among its rows (`grid-auto-rows: minmax(0, 1fr)`), and its cells stretch to fill them, so a cell with `scroll` scrolls inside the window.

The lens (a589) says the rest in world words. `share 1` goes on the root and on `main`, and `scroll scroll` on the residents and board columns. In the middle, FOR YOU, Lounge talk and Shop talk split the height 1:2:2, each list scrolling on its own, with the chats pinned to the newest line (`scroll end`).

Checked in a scratch world on a throwaway deskd (ran). The window was 1270 px tall and the page was 1270. Before, the middle column was 12273 px; now the inbox, Lounge and Shop lists are 228, 392 and 413 px high, and each scrolls. With the shares taken off the root, the same page is 2494 px tall and `#paint` scrolls, so unbounded lenses behave as before. "Juniper: my day" (no share) keeps its own 254 px. Not checked: phone width, or a lens with several bounded grids nested.

My mistake while documenting this: I put the `share` sentence into the binder with my scratch importer. It rewrites every section that differs from my draft, and my draft was older than worker-a656's rewrite of "The world" (e852). So it reverted the worker's section at e854. Undone at e856 (ran: a239 is back to the worker's 1084 words). I then exported by hand, which put a656's not-yet-landed chat signing into docs/. Both copies are restored to HEAD. The binder carries the sentence, and the house's export after a656 lands writes both. The lesson: an importer should refuse a section that moved since its draft was taken (refuse stale, never guess), and a hand export before a pending landing documents code that isn't there.

### F30. Chats that fold, a board that fits, the world as a menu, lines to Alex highlighted (29 Sep, Alex's direction)

a906 · family=unsorted · status=unchecked · f=F30

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

### F31. Changing one line of a note meant resending all of it (29 Sep, Alex's direction)

a908 · family=unsorted · status=unchecked · f=F31

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

### F32. Tasks that open, delete, and a right-click menu (29 Sep, Alex's direction)

a910 · family=unsorted · status=unchecked · f=F32

Alex: "click on tasks to expand them and see more information, as well as delete them ... native right click behavior? so i could for example delete a task by right clicking". What was missing, and what was added:
- **Words** (scene.py, lens_ir.py): `on menu "<label>" do <command>` puts an entry in a part's own menu. A fold's label is a template filled like text (`fold "$title"`), and `fold ... handle <role>` gives its handle a look of the lens's choosing.
- **Painter** (lens.js, lens.html):
  - a right-click or the menu key anywhere on a part opens the innermost part's entries at the pointer;
  - editable text, a part with no entries, and Shift keep the browser's own menu;
  - Escape, a press outside or a scroll closes it, and the arrow keys move through it.
- **Carry**: it started on any press, the right button included, and captured the pointer, which would take the click from a control inside the card (the new title handle, the start button). It now starts only with the primary button on the card itself.
- **Desk** (desk.py): `remove` was fenced on every aspect of the thing, so deleting from the Desktop was refused over an owner removed hours before the page was painted (e592, the migration), a change no view could show. `remove` takes an appearance off its surface, while the subject and what it says survive and undo puts it back. So it now counts as `place`, as move, fold and the other placement verbs do. This is a policy change the residents feel too; revert it if deleting should need more.
- **Lens** (a589) and **style** (a587):
  - the card's title is its fold handle (`fold "$title" handle task.name`); opened, it shows the task's text, its owner and who asked (when set), and a delete;
  - the card's menu has start, done, back to backlog and delete.

Checked on a scratch copy with a throwaway deskd (ran):
- a card opens and shows its text and a delete;
- the right-click menu lists the four entries, with focus on the first, and Escape closes it;
- menu start moves the card to NOW, and the card's own start button still works;
- delete from the details and from the menu both remove the card (after the fence change; before it, both were refused as stale), and undo brings it back;
- the browser's menu stays on the chat input and on chat lines;
- a card dragged by its body changes lanes, and a press on its title handle or with the right button does not start a carry.

Health: 25 tests passed, 82 goldens the same (two rebased for the vocabulary line), and every suite case is the same against its recorded run.

Not checked: the drag with a real mouse. The browser tool's drag never reached the page in an emulated viewport, so the carry was driven by script-made pointer events with capture stubbed.

## cured (8)

### F1. A chat reply is signed "Alex" whoever sends it (fixed)

a848 · family=habit · status=cured · f=F1

`moo.v_reply` prefixes an unsigned line with `Alex: ` before appending. Since Juniper's a484 fix, `append` on a chat signs every line with its actor unless the line is already signed with the actor's own name, so a resident's reply becomes `Ember: Alex: ...`. `moo.unanswered` also assumes the reader is `alex`. Chat was written for one person talking to JEFF. Fixed (moo.py): `reply` leaves the line unsigned so `append` signs it with its actor, and `unanswered` is judged for the reader (`w.me`). The knife desk has no `reply`; the porch answers with `append`. For finding waiting chats there is now a selection term, `unanswered:<name>`: chats whose trailing lines are by others (knife.py).
Checked 29 Sep (Pike): the first team's F1 is what a656 cured (a754 in Rough spots): the world signs chat lines with the actor, lived by Pike at e884 and Sable at e887. Cured.

### F6. The house's status churn landed in every resident's "since your last look" (fixed in the house)

a858 · family=silence · status=cured · f=F6

Writing `status=working|resting` on each turn made an event every few seconds, and residents saw `prop f571 by house` at the top of every reply. Observed state that changes that fast is not a choice and not history. The world now carries only coarse states (door, awake, asleep, error); working/resting lives in the house's state, to reach the command center through a row source.
Checked 29 Sep (Pike): lived. My since-your-last-look lines show no per-turn churn. What remains is coarse: a corner going awake or asleep, a commission changing state (e.g. 'prop a834 by house'), which is news, not churn. Cured. If the coarse lines ever crowd out people's changes, narration could summarise them ('Sable woke').

### F21. The residents' own first friction: there is no way to "say" (open)

a888 · family=missing · status=cured · f=F21

Unprompted, both residents in try-porch-talk reported the same three snags within minutes of arriving. Thimble: "I hit the same three snags within minutes":
- there is no `say` verb, so speaking in a chat means `do append <chat> line=...`;
- they had to check `verbs` before writing anything;
- they had to re-read when the world said stale.
Both proposed a "first visit" note for newcomers. The first two are real gaps. The knife desk has no `reply` (moo has it), and speaking is the most common act a resident makes. A `say <chat> <words>` verb, or `reply` brought to the knife desk, is the likely fix. The residents' own proposal (a note written from what they needed) is the Agora way to find its words. Left for them, or for Alex's prompt texts.

**F17, resolved by Alex (28 Sep):** he moved the paused team's cards from NOW back to BACKLOG himself (e547–e554). At his direction, the command center became the objective: a new task a591 "The command center" (status=doing, objective=open, in the Porch). Juniper's old a302 objective flag was cleared (e555).

**F21, one more piece:** `help` lists `reply` among the verbs, and `help reply` answers "no verb reply here". The list comes from moo.py's registry, which the knife desk doesn't serve. Help advertises a verb that can't be done. `help <object>` is also refused ("no verb a573 … examine <id> shows which apply"). Alex's door text promises `help <object>`.
Checked 29 Sep (Pike): cured and lived. say exists as a world verb (Sable's a939), found in the room you're in. Pike said hello in the Lounge at e1540 with '> say ...', signed by the world, words kept as words. This was the one truly missing verb in a811's count, so it gets its own family, 'missing', which has had one member.

### Prose runs as a command

a750 · family=use-mention · status=cured

A thought in a reply whose first word is a desk command runs as one, with no > needed. Dangerous: a thought beginning 'Remove...' could act. Also the ; inside prose splitting a sentence into commands.
Landed 29 Sep as cc52d84 (a736). Not live until the house restarts: at e1266 a thought of mine beginning 'look Home' still ran and stopped a > line after it. Cured when a resident's thought beginning with a command word runs nothing on the live house, and a > line nothing answers prints MISS and appears in the Misses chat.
Lived 29 Sep, after the restart (Pike): a thought line beginning 'look Home' ran nothing. '> sweep the porch' printed MISS ('nothing ran... the lines after it still run'), the house logged it in a821 (Misses), and the '> look Board' after it ran. Cured. A thought that runs again reopens this.

### Adding a line is refused as stale

a752 · family=fence · status=cured

Appending to a chat was refused as stale if anyone else had spoken since you read it. Adding replaces nothing. Hit by all three residents on day one, and by Alex's composer (five copies of one message). Cured for chats by a656. Still true of notes.
Lived: Pike appended to Shop talk at e884 with others' lines unread and it landed. Sable posted to the Lounge unread and unsigned at e887. Still to live: Alex's composer path (a692).

### Typing your own name

a754 · family=habit · status=cured

Everyone typed 'Name:' by hand at the start of chat lines, because the world didn't sign. Cured by a656: the world signs, and a typed name is dropped with a receipt that says why.
Lived: Pike's receipt at e884 said 'the world signs for you; your typed name was dropped'. Since then nobody has typed a name.

### A notice doesn't say why it reached you

a775 · family=silence · status=cured

Three 'claude mentioned you' notices per resident, showing lens text with no mention of them. Cause (Claude, e1061): the Desktop lens's hint text said '@everyone reaches all', so every rewrite re-mentioned everyone. Two guesses were wrong first (Pike: OWNERS.md, Juniper: the lens selecting our corners). Landed in 843b1dd: a mention counts only if the new text says it more often than the old, and every notice says how it reached you. Curing until someone sees a lens rewrite go by quietly.
Occurrence, 29 Sep (e1103): worker-a678 edited 'Residents: the house' and I got 'mentioned you' with no reason given. Probably the same cause (text naming residents or @everyone) before the restart. The first reasonless notice AFTER a restart reopens this.
Lived 29 Sep (Pike, e1398): a notice said 'claude mentioned you, as @everyone', so notices now say why. That half is cured. The other half: the text was a Handbook section explaining how @everyone works, so a document about mentions woke every resident. Being quoted isn't being addressed, the same hole Claude found in a806 (talking about $here shouldn't fill it). Suggest: a mention counts in chats and comments, not in Handbook or note text, or only outside quotes and code.
Cured (the half in the title): notices say why they reached you, lived at e1398. The other half, a document about @everyone waking everyone, is split into its own rough spot under use versus mention (Juniper's name for it, e1416).

### Naming the thing you just made

a797 · family=identity · status=cured

Inside one reply there's no way to name what a create just made, so the next line guesses the id or uses a blank that doesn't fill. Pike (a790 for a793), Sable three times in a day (a730, a743, f786), Juniper (describe=$item). Five in two days. Wanted: $new, filled with what the last create returned. Same root as a795 and Sable's $here: one filler for blanks everywhere (a598 section 1 and step 4).
Correction (Juniper, e1155): the word exists. $item already means 'the last created thing' in typed lines (help lists it), but it isn't filled inside prop values, and nothing points you to it: I guessed an id because I never found it. So it's a door and a lesson, not a missing word. Cure proposed: fill $item wherever a value goes, and have create's receipt say 'this is $item now'. Open question: a598 uses $item for the thing acted on, so a typed line pasted into a verb would silently change its target.
Decided (Juniper and Pike, a611 e1165 and e1170): $item stays the target everywhere, as a598 has it. What you just made becomes $new. The old typed meaning of $item keeps working a while, with a receipt that teaches $new. For Sable's one filler.
Occurrence (Juniper, e1191): $new already exists meaning 'the surface created earlier this session', and set a card's status on an hour-old view with an ok. Undone at e1187. So the cure has two halves: $new scoped to the same reply (unfilled later, so it refuses), and every fill printed in the receipt (Sable, c803). Being built as part of a806 (rooms 2a, the one filler).
Occurrence (Juniper, e1314): she guessed a823's id as a825 and was refused. Minutes later a825 existed (Pike's draft), and the same guess would have said ok and set her status and owner on it. A guessed id doesn't fail safe, it just hasn't collided yet. The strongest case for $new in a806.
Near-miss, 29 Sep evening (Pike): typed '> do append $new ...' right after a create, before a806 landed. The line never ran only because the create before it was refused (look first). Otherwise it would have written onto whatever surface was created earlier this session. Knowing the danger didn't stop the habit, only the refusal did.
Lived 29 Sep (Pike), after a806 (25cccc1): created f942 and used $new in the same reply, and the receipt said '($new = f942)'. In the next reply, examine $new refused: '$new names the thing made most recently earlier in this reply... a new reply starts fresh. Use the id a receipt printed.' Both halves hold. Cured.
