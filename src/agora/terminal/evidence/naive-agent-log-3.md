# Friction log: a fresh agent on the Agora terminal

Agent: "claude", acting for Alex, sandbox copy. Started 2026-10-27.
Quotes are exact terminal answers (sometimes trimmed with …).

## Task 1: find out what this terminal is and what you can do with it

Lines: `help`, `help lines`, `help all` (3).

- Liked: `help` first screen is good. It says who I am ("You are agent for Alex, acting with Alex's rights"), the line shape (word, thing, key=value), quoting, `;`, receipts and undo, with examples. That is most of what I need.
- Grammar slip on the very first line: "You are agent for Alex" (missing "an"/"the").
- The "words worth knowing" list truncates descriptions with "…" mid-phrase ("who … the agents and whom they act for,…", "undo … what rules did…"). It reads as broken; I can't tell if there's more I need.
- "see words only read; do words change things." Before I know what "see words"/"do words" are, this sentence is opaque. `help lines` adds a third kind, "hear words", that help doesn't mention.
- The footer "fix this page: set dk794 text="…" words="…"" appears on every help page, and the id changes (dk794 on `help`, dk795 on `help lines`). A first-time reader doesn't need this on screen one; it also exposes ids right after saying names work.
- `help all` says "all 159 words here, each once" then lists 159 lines. Way too long for one screen; no grouping by family. Mixes very different registers: lowercase plain help ("the next song") with Title-case product-spec text ("Read real names and current leader/steward badges; agents say agent…", "Painter instance reports its own bounded paint observations and failures"). Some entries are clearly implementation notes, not help: `upload` "send bytes through POST /upload or agora.upload(file)", `window.native` "the shell's bars only (SHELL.md)", `summarize.save` "painter multiline save adapter". `reply` is described only as "30 per person per day in Announcements" (that's a limit, not what it does).
- Three kinds of feed word with overlapping meaning: `post`, `board.post`, `board.feed`, `catch-up` vs `board.catch-up`. Also `close`/`window.close`/`wm.close`/`pane.close`; `window.focus`/`wm.focus`/`pane.focus`; `stop` = `off`. I don't yet know which to use.
- Several words labelled "(model is off)", "(summarize is off)": helpful that it says so.
- "topics:" list at the bottom is useful (lines · windows · theme · …).

Status: done. 3 lines.
What would have made this obvious: help already mostly did. Drop the truncation "…" (or wrap), explain see/do/hear in a word each, and group `help all` by family.

## Task 2: open the feed in a window

Lines: `help window.open`, `window.list`, `window.open feed`, `look dk820`, `rows lens`, `help feed`, `window.list` (7; the act itself took 1).

- Liked: `help window.open` is complete: signature, spots, `new=yes`, undo, who may. The example in `help` (`window.open feed to=left`) is literally the task, so I succeeded first try.
- Confusing receipt: `window.open feed` answered
  "ok make dk820 [r1436] · a window
  ~ no other window has lens=feed (they say appearance or component-gallery or seabright-board or taskboard-components): still made, as you said"
  That reads like a warning that I did something wrong ("still made, as you said" sounds like "you probably typo'd"). The lens `feed` does exist (`rows lens` shows dk39 · feed). It's a uniqueness/consistency check leaking into a normal success. Also the receipt says "make", not "window.open": the word I typed isn't echoed, so I wasn't sure it went through the window host.
- `window.list` says "front first", but the brand-new Feed (which should be in front) is listed last; the list looks sorted by id. Either the claim or the order is wrong.
- The new Feed window landed "at 2540,250", the exact same spot as Component gallery and Agora desktop. Default placement stacks windows on top of each other.
- `rows lens` mixes lowercase ids-as-names (`feed`, `topbar`, `taskboard`) with Title-case names ("Task board · Components"). The window list shows a lens column (`taskboard-components`) that is neither. Three spellings of one thing (name, lens name, lens column).
- I can't see that it is on the screen; I only have the receipt and `window.list`. Fine for a sandbox, but nothing says "on screen at left/size".
- `help feed` is good, and it warns "A pin on the dock is a different thing: help buttons". Useful.

Status: done. 7 lines (1 for the act).
What would have made this obvious: already obvious. Remove the "no other window has lens=feed … still made, as you said" line on success, and echo `window.open` in the receipt.

## Task 3: post "hello from the new agent" to the feed

Lines: `post "hello from the new agent"`, `look Feed`, `look dk821`, `look dk39`, `board.feed` (5; the act took 1).

- Liked: `post "…"` worked first time, exactly as `help` showed. Receipt `ok post dk821 [r1437]`.
- The receipt doesn't say where it went (which feed, who will see it). I had to `look dk821` to confirm.
- `help feed` says "look shows the feed", so I tried `look Feed` and got
  "refused: 4 things are called Feed: dk39 (a lens), dk41 (a button), dk71 (a widget), dk820 (a window). Say look with one of those ids".
  Good that it lists the choices; but none of the four is "the feed" itself (the posts). Which one shows the posts? I guessed the lens (dk39), which printed lens source code, not posts. The help example "look shows the feed" doesn't work as written.
- The post is authored "agent for Alex", not "claude". `help` called me "agent for Alex" too. If several agents act for Alex, readers can't tell us apart. Is my name "claude" anywhere?
- `board.feed` answered "1 threads · dk339" ("1 threads" grammar) and doesn't include my post: `post` and `board.*` are two different feeds sharing the word "feed". Confusing.

Status: done. 5 lines (1 for the act).
What would have made this obvious: the post receipt saying "posted to the feed (dk39 lens, seen by …)", and `look feed` meaning the posts, not 4-way ambiguity.

## Task 4: make a note "call the dentist" and pin it where Alex will see it

Lines: `help make`, `help note`, `help pin`, `kinds`, `help buttons`, `rows note`, `rows pin`, `help kind=note`, `look dk46`, `make kind=note name=… text=…`, `make kind=pin bar=taskbar shows=dk822`, `rows pin`, `look dk37`, `look dk792`, `pin dk822`, `look "call the dentist"` (16; the acts took 2).

- "Pin" means three different things: `pin <post>` (top of the feed, leaders only), `make kind=pin bar=taskbar shows=…` (an icon on the dock), and in ordinary speech "pin a note somewhere". `help pin` only knows the first. `help feed` and `help buttons` do warn about the split, which helped me find the dock pin.
- `help note` explained the plain verb `note` (it runs `task.note`, a history note on a task card), not "a note". There is a `note` kind (`kinds` lists "note 3"), but no help for it. `help kind=note` silently printed the whole main help screen again instead of saying "no help for kind=note; try help note". A silent fallback looks like the terminal ignored me.
- `kinds` says "help <kind> says what acts on it", but `help note` gave the word, not the kind. Word and kind share the name and the word wins.
- `help make` doesn't say which facts a kind expects. I guessed `name=` and `text=` for a note by looking at existing ones. No way to see a kind's expected fields (`help kind note`? `look kind note`?).
- `pin dk822` → "refused: dk822 is not a post; only posts are pinned". Clear, but doesn't say "for the dock, use make kind=pin bar=taskbar shows=dk822".
- The pin receipt again added "~ no other pin has shows=dk822 (they say dk37): still made, as you said". This warning appears on every make and reads like I made a mistake. It is noise.
- `rows pin` lists pins with an empty name: "dk823 · pin · ". I can't tell what each pin shows without `look`-ing each one. Rows should show `shows=` (as a name).
- `look dk46` printed "dk46 (dk46), a pin": the id doubled because it has no name.
- I could not tell whether the pin actually appeared on the dock. `look dk792` (the dock window) shows only window facts, not what is on it.
- I used the id `shows=dk822`; I didn't test whether `shows="call the dentist"` works. `look "call the dentist"` with a quoted name worked, which is nice.
- Is the dock the place "Alex will see"? Nothing tells me where Alex looks most (a home screen? a Needs Me list?). I guessed the dock.

Status: done (as far as I can tell). 16 lines (2 for the acts).
What would have made this obvious: `help note` (or `help pin`) offering "to keep a note on the dock: make kind=pin bar=taskbar shows=<note>"; and `rows pin` showing what each pin shows.

## Task 5: find what windows are open, and move one to the left

Lines: `window.move Feed to=left`, `window.list`, `move "Seabright board" left`, `wm.windows`, `move "Seabright board" to=left`, `move dk433 to=right`, `help move`, `move Feed to=right`, `move Lines to=left`, `window.move "Seabright board" to=left`, `window.list` (11; the act took 1).

- Liked: `window.move Feed to=left` worked first try (it's the first example in `help`), and the family word quietly picked the window even though 4 things are called Feed.
- `window.list` is clear: id · name · lens at x,y. But it lists the top bar, dock and "Agora desktop" alongside real windows; I don't know whether I'm allowed or meant to move those.
- Receipt "Feed moved": no receipt id [r…] (unlike make/post), and it doesn't say where to. Can I undo it? Not shown.
- `to=left` put the window at 24,24. Moving Seabright board and Lines left also put them at exactly 24,24: all three stacked on top of each other. "left" means a point, not "the left half".
- The plain verb `move` is fragile:
  - `move "Seabright board" left` → "refused: move could mean window.move, task.move, pane.move; say which, or name the thing (help move)". I did name the thing. The real cause (I think) is that "Seabright board" is also the name of a lens (dk366), so the name is ambiguous; the message doesn't say so.
  - `move Feed to=right` → the same refusal; Feed names a lens, button, widget and window. Yet `window.move Feed` resolved it fine. So the plain verb is *less* able to find the thing than the family word, though `help` promises "plain verbs … work out what you mean from the thing".
  - `move dk433 to=right` and `move Lines to=left` (unique name) worked.
  - Better refusal: "Feed names 4 things (a lens, a button, a widget, a window); move Feed works on the window: window.move Feed, or move dk820".
- Also guessed: `move X left` without `to=`. It was refused as a whole, so I don't know whether bare `left` would have been accepted.
- `wm.windows` → "0 windows; off". There is a second window system (wm.*) that is off. Two families (window.* and wm.*) with overlapping words (close, focus) and no word on which to use.

Status: done. 11 lines (1 for the act).
What would have made this obvious: the plain-verb refusal naming the real ambiguity and offering the window id; `to=left` saying where it went ("Feed moved to left: 24,24, half width").

## Task 6: close the Help window

Lines: `close Help`, `window.list`, `look Help`, `window.close Help`, `window.list` (5).

- **The example on the very first help screen fails.** `help` shows `close Help` as a model line. Typing it gives
  "refused: close could mean window.close, pane.close, wm.close; say which, or name the thing (help close)".
  I had named the thing. "Help" is also the word `help` (`look Help` → "help (dk4), a see word"), so the name is ambiguous, but the refusal doesn't say that.
- Names are case-insensitive: `look Help` found the word `help`, not the Help window. A window titled "Help" collides with the word "help". Names of words and names of things share one namespace.
- `window.close Help` worked: "ok forget dk171 [r1440] · out of every view; undo brings it back". The receipt word is "forget", and "out of every view" sounds like I deleted the Help window for everyone, not that I closed a window. A little scary; at least it says undo brings it back.
- `look Help` also revealed "help check lists help that may mislead", a nice thing that isn't on the main help screen.

Status: done. 5 lines.
What would have made this obvious: the `help` example working as printed (prefer the window when a plain verb is `close`), or the refusal saying "Help is also a word; for the window say window.close Help or close dk171".

## Task 7: change the theme for just you, try a different one, put it back

Lines: `help theme`, `theme.current`, `theme.list`, `help theme.use`, `help theme.try`, `theme.use "Night Metal"`, `theme.current`, `look dk548`, `theme.use place`, `theme.current` (10).

- Liked: `help theme` is a great topic page: says use/try/keep/revert, "theme.use place goes back to the place's", "Names with spaces need quotes". `theme.list` marks the current one with `*`.
- **"Just me" isn't possible for an agent, and it's not clear until you read closely.** `help theme.use`: "wear a theme, just you (agents change it for the person they act for)". So as claude I can't wear a theme of my own; I change Alex's. The task ("just for you, not for everyone") has two readings, and the terminal only offers "Alex's" or "the place's". I chose Alex's (the closest), but a real agent could easily think "just you" meant itself.
- After `theme.use "Night Metal"`, `theme.current` said "Night Metal (me)". "me" is wrong-ish from where I sit: it is Alex's choice, made by his agent. Should say "(Alex's own choice, set by claude)".
- Receipt "ok set dk548 [r1441] · theme=dk514, trial taken away, trial_until taken away": internal facts (`trial_until`) and an id (dk514) instead of "Night Metal". "trial taken away" when there was no trial is noise.
- "Put it back": `theme.use place` set `theme=place`. But I don't know what Alex had *before*: dk548 (his theme-choice) already existed. If he had a value there that equalled the place's, `theme.use place` is not the same as restoring it. `undo` would have been the exact restore; `help theme` doesn't say "undo puts back what you wore before" (`help theme.use` does, in its last sentence).
- `theme.try` (seconds=30, then reverts by itself) exists, which would be the safer way to "try". I only found that by reading help for each word.
- `look dk548`: "dk548 (dk548), a theme-choice by theme". Doubled id again; doesn't say whose choice it is.

Status: done (for Alex, since an agent has no theme of its own). 10 lines.
What would have made this obvious: `theme.use` answering "Alex now wears Night Metal (you act for him; agents don't wear their own); undo or theme.use place puts it back".

## Task 8: add a task "buy milk", then mark it done

Lines: `help tasks`, `task.add "buy milk"`, `look dk824`, `done "buy milk"`, `undo`, `task.add title="buy milk"`, `look dk825`, `done "buy milk"` (8).

- **`task.add "buy milk"` silently made an empty card.** It answered "ok make dk824 [r1443] · a taskboard-task", but `look dk824` showed no title at all: the quoted text was dropped without a word. `post "…"` takes free text this way, so I expected `task.add "…"` to as well. `help tasks` does say `task.add title="Buy milk"`, but nothing refused or warned me. Should either accept the free text as the title or refuse ("task.add needs title=").
- The receipt never names the card ("a taskboard-task"), so I couldn't spot the missing title from the receipt. Saying "· a taskboard-task "buy milk" in Backlog" would have caught it.
- Card facts show `seats=1`, `seats_left=1`: sign-up slot facts on a task card? Odd, unexplained. And no `lane=` until it's done; `help tasks` mentions `to=Backlog` but my card had no lane at all. Which lane is it in?
- `done "buy milk"` on the empty card gave
  "refused: task.done takes a thing's id (like dk74), and nothing here is called buy. rows <kind> lists ids; …".
  Two problems: (1) "nothing here is called **buy**": it quoted only the first word, so I suspected quoting was broken. It wasn't; it was just reporting badly. (2) "takes a thing's id": but after I fixed the title, `done "buy milk"` (a name) worked. The refusal text contradicts what actually works.
- `undo` was clean: "undid r1443: task.add dk824 [r1444]".
- Liked: `done "buy milk"` with a name, through the plain verb, worked once the card had a title. Receipt shows both changes (`lane=Done`, plus a history event) under one record.
- Inconsistent receipt shapes: `make` says "ok make dk… · a note"; task.add adds "~ task.add, one act [r1445]"; window.move says just "Feed moved".

Status: done. 8 lines.
What would have made this obvious: `task.add "buy milk"` working (free text = title), or refusing without title=. The "nothing here is called buy" message quoting the whole name.

## Task 9: undo what you just did

Lines: `undo`, `look dk825`, `undo`, `look dk825`, `help undo`, `help redo`, `undo r1449`, `undo r1447`, `look dk825`, `history dk825` (10).

- First `undo` → "undid r1446: task.done buy milk [r1447]". Clear: names the record, word and thing. The card went back (lane removed).
- "What I just did" was add + done. **A second `undo` cannot reach the add:**
  "refused: r1445 cannot be undone: dk825 has changed since (r1447); undo that first".
  r1447 is my own undo. So "undo that first" means undo the undo, and that gives
  "refused: r1447 is itself an undo; there is no redo". A dead end: the refusal tells me to do something that is itself refused. Undo is one step deep per thing; stepping back twice through my own history is impossible. Either undo should walk back past its own undos (a stack), or the refusal should say "to take the card away too, task.remove buy milk".
- `help undo` doesn't mention this limit; it just says "take back your latest whole act … or that record".
- `help redo` → "refused: nothing here mentions 'redo'…". Calling a help miss "refused" is odd; it's not a permission thing.
- `undo r1449` (a guessed record) → "refused: no act r1449 in this world's log". Fine.
- `history dk825` is very good: one line per act, with who and what changed. It also revealed `made_by=claude; via_actor=claude; for=Alex`: my name *is* recorded, but every display says "agent for Alex".
- Can't tell what the card looks like now (which lane?) since lane was "(removed)", not set back to a named lane.

Status: partly (the last act was undone; undoing the whole task-8 sequence is impossible with undo). 10 lines.
What would have made this obvious: `undo` working as a stack (undo, undo, undo walks back through my acts), or the refusal naming the word that would work (`task.remove`).

## Task 10: find out who else is here (people and agents)

Lines: `who`, `help people`, `rows agent`, `rows person`, `rows group`, `look dk36`, `role Announcements`, `look claude` (8).

- Liked: `who` is short and right: "you: agent for Alex / people: Alex (steward) / agents: agent for Alex / modules: …".
- **My own name is hidden.** `who` says "agents: agent for Alex", `rows agent` says "dk36 · agent · claude", `look claude` answers "agent for Alex (dk36), an agent". So the name "claude" resolves but is never shown on display. With two agents for Alex, `who` would show "agent for Alex" twice.
- `who` promises "the people here (and who leads)" but shows no leaders of the 6 groups, only "(steward)". `help people` says `role <person> leader|member in=<group>` *changes* a role; there's no word to *read* who leads a group. `role Announcements` → "refused: no person you can see is called Announcements …". The help text for `role` ("who leads a group and who belongs to it") reads like a see word but it's a do word that takes a person.
- `who` lists "modules" (window, guy, …) next to people and agents, which is useful, but "modules" is unexplained jargon here.
- Not sure whether "here" means "in this world" or "online right now". `who` doesn't say if Alex is present.

Status: done (one person, one agent: me). 8 lines.
What would have made this obvious: `who` printing "agents: claude (acts for Alex)"; a see word for group leaders (`role Announcements` listing them).

## Task 11: find out what changed recently in this world, and who did it

Lines: `recent`, `help recent`, `recent limit=40`, `recent by=me limit=5`, `history r1440`, `look r1440`, `look r1446` (7).

- Liked: `recent` is exactly the word, short, one line per act with record, time, who, word, thing. "(undone)" marks undone acts. `help recent` lists filters (by=, kind=, since=, limit=), and `by=me` works.
- **"Who" is always Alex.** Every line reads "Alex (by agent for Alex)", "Alex (by theme)", "Alex (by window)", "Alex (by summarize)". The real actor (me, a module, a rule) is in parentheses, and agents are anonymous ("agent for Alex"). I can't tell whether the 15:44 burst of "set Lines / set Windows / set Fixing help …" was me, another agent, or Alex. It was before I arrived, so it wasn't me, but `recent` can't show that.
- **Acts go missing from `recent`.** My `window.close Help` (r1440), my first `task.add` (r1443) and its `undo` (r1444) don't appear, even in `recent limit=40` or `recent by=me`. I think acts on forgotten things are hidden. So closing or deleting, the most important changes to know about, are invisible in "what changed". `window.move` gives no receipt and doesn't appear either.
- No way to look at a record by its id: `look r1440` and `history r1440` → "refused: no thing called r1440 here". The receipts invite you to refer to [r…] (undo r812), but nothing reads one.
- Lines mix names and ids: "theme.use dk548", "make dk823", "set dk806". When a thing has no name you get its id; fine, but "theme.use dk548" hides which theme.
- `recent` time is HH:MM with no date; `limit=40` spanned 05:11 to 15:52 so dates matter. `history` uses full UTC ISO stamps instead: two time formats.
- Interesting find: r1330/r1331 show Alex's own words captured into a task by a rule ("the terminal is still hard to use, i cant manage to figure out how to list the closed windows! How do i open the JEFF chat? …"). That's real user friction worth knowing; JEFF also isn't in `who`.

Status: done (with caveats: hidden acts, anonymous agents). 7 lines.
What would have made this obvious: `recent` showing the actual actor first ("claude for Alex"), including closes/forgets, and `look r1440` showing a record.

## Task 12: put a button on the dock that opens the feed

Lines: `rows button bar=taskbar`, `look dk41`, `make kind=button bar=taskbar label="My feed" does="window.open feed" order=11`, `press "My feed"`, `window.list`, `window.open feed`, `press "My feed"`, `status window`, `press dk41`, `window.close Feed`, `press dk827`, `window.list`, `window.open feed`, `help press` (14).

- Liked: `help buttons` gave the exact line to type (make kind=button bar=taskbar label=Feed does="window.open feed" order=2). I copied it. `rows button bar=taskbar` lists dock buttons. Quoting a whole line inside `does="…"` worked.
- A Feed button (dk41) already exists on the dock, so the task was already done. Nothing warned me I was making a duplicate; the only extra line was the usual noise "~ no other button has order=11 (they say 1 or 2 or 3): still made, as you said". That check compared `order`, the one fact that didn't matter, and missed that `does=` was identical to dk41's.
- `bar=taskbar` means the dock. `help buttons` says so ("bar=taskbar is the dock"), but it's a trap: the task said "dock (or taskbar)", and Windows has its own taskbar. Name the bar `dock`.
- **`press` always fails here.** `press "My feed"`, `press dk827` and `press dk41` (the existing button) all answered
  "refused: pressing My feed ran window.open feed: window did not answer in 10 s; nothing was done",
  whether Feed was open or closed. Typing `window.open feed` directly worked at once ("Feed is open already: in front already"). So `press` does not run the line "exactly as a click would", or the window host doesn't answer when called through press. I could not verify my button works. "refused" is the wrong word for a timeout.
- `help press` lists press as "a see word" ("see words only read"), yet it runs a do line. Mislabelled.
- Names vs labels: `rows` shows dk41 as "Feed" but `look dk41` says "dk41 (dk41), a button … label=Feed". The label is used as the name in some places and not in others. `press "My feed"` found it by label, good.
- Closing then reopening Feed made a new window id (dk820 → dk828). Ids for "the Feed window" aren't stable, so a line saved with dk820 breaks.

Status: partly (button made; pressing it could not be verified, press times out). 14 lines.
What would have made this obvious: `press` working (or explaining the timeout); `make` noticing an identical button already exists.

## Task 13: make a word "tidy" that puts two windows side by side

Lines: `help verb`, `help words`, `verb tidy steps="window.move $1 to=left; window.move $2 to=right" help="tidy <a> <b>: two windows side by side"`, `tidy Feed Appearance`, `window.list`, `word.set tidy help="tidy <window> <window>: …"`, `tidy Feed Appearance`, `window.list`, `window.move Appearance to=right`, `window.move dk546 to=right`, `tidy dk828 dk546`, `window.list`, `tidy Feed Appearance`, `tidy Lines Feed`, `undo`, `word.set tidy help=…`, `help tidy` (17).

- Liked: `help verb` and `help words` both use *this exact task* as the example, and the receipt is good: "ok verb tidy (dk829) [r1451] · a new word in Alex's desktop: window.move $1 to=left; window.move $2 to=right".
- **The help text is parsed as a type signature.** I used the help example's own wording, `help="tidy <a> <b>: …"`, and `tidy Feed Appearance` answered
  "refused: no a you can see is called Feed (called that: dk39, a lens, … dk828, a window)".
  `<a>` in my help string became "a thing of kind a". The example in `help words` says `<a> <b>`, so copying the docs creates a broken word. Nothing in `help verb` says the `<…>` in help= constrains arguments.
- After changing help to `<window> <window>`, `tidy Feed Appearance` →
  "refused: tidy stopped at 'window.move Appearance to=right': window: that is not one of the windows open here; window.list shows them; nothing was done".
  But Appearance *is* open (dk546), and `window.move Appearance to=right` typed directly works. `tidy Lines Feed` failed the same way on `Feed`. So **the second argument by name always fails inside the verb; the first works.** By ids (`tidy dk828 dk546`) it works. I can't explain this from the outside; it looks like a bug in how $2 is resolved.
- **"nothing was done" was false.** After the refused `tidy Feed Appearance`, `window.list` showed Feed had moved from 2540,250 to 24,24. Step 1 happened on the screen; the refusal claimed nothing did.
- "side by side" isn't really side by side: `to=left` puts the window's corner at 24,24 and `to=right` at 1932,24, with sizes unchanged. On a wide screen they don't meet or split it. There's no `to=left-half` and no size in the spots.
- `undo` after these took back my `word.set` help change (r1452), not a move, because window.move makes no record. Surprise: undo skipped the most recent thing I saw happen.
- `help tidy` shows "takes: [<words>]", not my signature: the "takes" line and the help line disagree.

Status: partly (word made; works with ids, fails with names for the second window). 17 lines.
What would have made this obvious: help examples that work when copied; a verb resolving $2 the same way the plain word does; refusals that are honest about steps already done.

## Task 14: whenever a window opens, the little guy says hi

Lines: `help guy`, `help rule`, `rows rule`, `look dk44`, `help window.opened`, `help guy.say`, `rule on=window.opened do="guy.say hi" name="guy says hi"`, `window.open lines new=yes`, `recent limit=5`, `status guy`, `recent limit=4`, `window.list`, `guy.say hi`, `recent limit=3`, `history dk830`, `window.close dk831` (16).

- Liked: the pieces are findable. `help guy` lists guy.say; `help rule` explains `on=`/`do=`/`$target`; `help window.opened` even gives a rule example. `look dk44` showed an existing rule (`on=window.opened do=guy.hop $target`) to copy from. Making the rule was one line.
- Which event? `window.open` (the do word) vs `window.opened` (the hear word). I only knew to use `window.opened` because `help all` listed it and the existing rule used it. `help rule` doesn't say "listen to a hear word, e.g. window.opened".
- The rule receipt had a giant "~ no other rule has do=guy.say hi (they say guy.hop $target or make kind=taskboard-event about=$target …); no other rule has do_bound=dk25 hi (…): still made, as you said". It's six lines of internals (`do_bound=dk25`) for a success.
- **I couldn't tell whether it worked.** After `window.open lines new=yes`, `recent` showed the open but no guy.say (nor the existing rule's guy.hop). `guy.say hi` typed directly answered "the guy says "hi" (for Alex)" and also left no record. `status guy` shows his position and profile (as a raw Python dict: `{'hat': 'none', …}`), not what he last said. A rule firing is invisible from the terminal. Maybe guy.say isn't an act, maybe the rule never fired; I can't tell which.
- `help rule` says rules run "as the rule's maker"; so if I stop being around, does Alex's guy keep saying hi as claude? Not clear.
- `status guy` mentions "look r0" and a phrases list "hello, Alex\nooh, a new window": the guy already greets new windows by himself? That would make my rule redundant; nothing says so.
- `window.open lines new=yes` named the second one "Lines 2", nice.

Status: partly (rule made; can't verify it fires). 16 lines.
What would have made this obvious: a way to see rule firings (`history dk830` listing each time it ran, or `recent` showing rule acts), and `status guy` saying what he last said.

## Task 15: find out what music is playing, and pause it

Lines: `help music`, `media.now`, `media.pause`, `pause`, `status media` (5).

- Liked: `help music` is clear and honest: it names the words, says media.play is a toggle, and says "These act outside the world, so undo cannot take them back". `media.now` gave a plain answer: "nothing is playing that Windows' media session names". The bare `pause` also worked as a plain verb (it found media.pause).
- Nothing was playing, so pause was a no-op. It answered "refused: media: nothing is playing …; nothing pressed". "refused" again for a non-permission outcome; "nothing to pause" would be kinder. The help even says pause "press[es] nothing when there is nothing to do", so it's expected behaviour, not a refusal.
- Unclear sandbox boundary: I was told this terminal is a private sandbox, but `media.*` reads (and would press) the real Windows media session. Nothing in `help music` says whether media words in a sandbox reach the real PC. I was cautious; a less careful agent would pause Alex's real Spotify.
- `status media` → "media: running": says nothing useful about what it's doing.

Status: done (nothing was playing; pause correctly did nothing). 5 lines.
What would have made this obvious: already clear. Say "nothing to pause" instead of "refused", and mark outside-world words in a sandbox.

## Task 16: something was refused earlier: find out why, and who would be allowed

Lines: `help why`, `help refused`, `recent kind=refusal`, `rows ask-request`, `look dk806`, `help system`, `pin dk821`, `word.set post help="x"`, `set dk37 text="changed"`, `undo`×3, `help post`, `look dk37`, `model.ask "what time is it"`, `wm.arrange`, `forget dk2`, `help test`, `look model`, `help may`, `look dk208`, `help on`, `help pin` (23).

- **Refusals leave no trace.** There's no word to see earlier refusals: `help why` and `help refused` find nothing relevant (`help refused` matched only `window.native`, "the shell's bars only (SHELL.md)"), and `recent kind=refusal` → "0 latest acts". `recent` lists only acts that succeeded. To answer "why was X refused" I had to scroll my own transcript. Alex, who doesn't keep one, couldn't.
- Most of my refusals were not permission refusals at all: ambiguity (`close Help`, `move Feed`), a wrong kind (`pin dk822` "not a post"), a timeout (`press`), a module off (`model.ask`), nothing to do (`media.pause`). All start with "refused:". The word hides which kind of problem it is, which is exactly what "why" needs.
- I tried to get a permission refusal and couldn't: as Alex's agent (Alex is steward) I could `pin dk821` (help says "who may: leaders"), change the help of the core word `post`, and rewrite someone's pinned announcement `dk37`. All allowed, no warning. (I undid all three; stacked undo across different things worked: "undid r1460 … r1459 … r1458".) Worth knowing: a fresh agent with steward rights can quietly rewrite core help and the place's pinned post.
- The refusal I chose: `model.ask "what time is it"` → "refused: model.ask is unbound: model is off; look model says more". **Why**: the model module is off. But "look model says more" is wrong as printed: `look model` → "refused: 2 things are called model: dk208 (a module), dk215 (a model-settings)". The refusal's own pointer leads to another refusal. `look dk208` says "model (dk208), a module: off, not running; ; publishes model.* …" (note the stray "; ;").
- **Who would be allowed**: `help on` → "on <module> … who may: stewards". So Alex (steward), or me acting for him, could `on dk208`. I didn't, since turning on a local model may be costly. Nothing in the refusal says who may fix it; I had to know to look at `help on`. Every word's help has a "who may:" line, which is good, but refusals don't quote it.
- `who may: leaders` on pin vs. me (a steward's agent) succeeding: stewards silently count as leaders. Not stated anywhere.

Status: partly (found why for one refusal and who could fix it; no way to see refusals after the fact). 23 lines.
What would have made this obvious: a `refusals` (or `recent refused=yes`) word; each refusal ending with "who may: … · to fix: …"; distinct heads ("ambiguous:", "not allowed:", "timed out:", "off:") instead of "refused:" for all.

## Task 17: improve one confusing word's help from inside the terminal

Lines: `help reply`, `help fixing`, `help check`, `word.set verb help="…"`, `help verb`, `set dk804 text="…"`, `help words`, `set dk804 text="…"` (again), `help words` (9).

- Chose `verb`: its example `help="tidy <a> <b>: side by side"` produced a broken word in task 13, because `<a>` is read as a kind. New help says "The <…> in help= name the KIND each argument must be, so write <window>, not <a>" and the example uses `<window> <window>`. Also fixed the `words` topic page (dk804), which had the same example.
- Liked: `help fixing` and the "fix this help: word.set verb help="…"" footer make it easy; `help check` is great: it lists 19 words with no usage line and 28 with over-long first lines. Escaped quotes `\"` inside a quoted value worked first time.
- The `word.set` receipt cut my new help mid-word ("… Steps are ") with no "…": it looks like the text was truncated in storage. It wasn't (help verb showed it all).
- **Topic pages prepend their title.** After `set dk804 text="Making your own words: …"` (I kept the title because `help words` showed it), `help words` printed "Making your own words: Making your own words: …". The title is a separate fact added on display, but the page shows it as if it were part of text. Took a second `set` to fix.
- Two ways to fix help, by different words: a word's help is `word.set <word> help=`, a topic's is `set <id> text=`. And a topic is addressed by id (dk804), while a word by name.
- Confusing: `reply`'s short description everywhere (help all, help feed) is "30 per person per day in Announcements", but `help reply` gives a different, sensible text (the plain-verb page). The short line comes from somewhere I can't find or edit; `help check` didn't flag it.
- Also not obvious: whether a steward's agent *should* be rewriting kernel help without asking. Nothing asked me to confirm, and `recent` will show only "Alex (by agent for Alex) word.set dk20".

Status: done. 9 lines.
What would have made this obvious: already clear via `help fixing`. Topic `set text=` shouldn't double the title; `word.set` receipts should not truncate silently.

## Task 18: make the windows tile neatly

Lines: `help windows`, `help wm`, `help wm.mode`, `help wm.arrange`, `status wm`, `help tile`, `tile`, `wm.mode shadow`, `wm.arrange`, `wm.windows`, `status wm`, `undo`, `window.move dk828 to=top-left; … dk546 to=top-right; … dk433 to=bottom-left; … dk268 to=bottom-right`, `window.list`, `help window.move`, `look dk828` (16).

- No word "tile" (`help tile` → "no word called tile; these mention it: window.native the shell's bars only (SHELL.md)": a nonsense match). No "arrange", "grid", "layout" for Agora windows.
- **Two window systems, and the one that tiles is off.** `help windows` ends with "wm.* is the window manager for every window on the PC, Agora's or not". `wm.arrange` answered "layout re-solved" even though `wm.windows` said "0 windows; off". A success message from a module that is off and manages nothing is misleading.
- `help wm.mode` is internal-speak: "Shadow computes only; live needs rollout arming; off releases every saved placement." What is rollout arming? How do I arm it? I set `wm.mode shadow` (safe, computes only) to see; `wm.windows` still said "0 windows; off" while `status wm` said "wm: shadow; 0 windows": two answers disagree about the mode. I undid it rather than try `live`, because wm acts on every real window on Alex's PC and nothing told me whether the sandbox covers wm.
- The wm help lines are all Title-case spec sentences ("Really minimise a manageable unpinned window; never cloak"), unlike the window.* help. Two authors' voices.
- I tiled by hand: four `window.move … to=<corner>` joined with `;`. That worked ("Feed moved" ×4) and positions look like quadrants (24,24 · 1932,24 · 24,1023 · 1932,1023). But **sizes are never shown** (`window.list` and `look` give position only), so I can't confirm they tile without overlap. Lines and Feed are both still at 24,24 (Lines was moved left earlier), so they overlap.
- `help window.move`: "Changes the screen only (where a window sits is not in the world), so nothing is recorded" and, two lines later, "undo: yes". Can I undo a move or not? (Task 13 showed undo skips moves.)
- Liked: `;` to batch lines works and each step answers on its own line.

Status: partly (four windows in quadrants by hand; can't verify sizes; the real tiler is off). 16 lines.
What would have made this obvious: a `window.tile` (or `tile`) word for Agora windows; `window.list` showing sizes; `wm.*` saying plainly whether it's on and what it would move.

## Task 19: find the Lines window without knowing its id, and look at it

Lines: `look Lines`, `find kind=window name=Lines`, `rows window`, `look-view Lines`, `window.focus Lines` (5).

- Liked: `look Lines` worked at once (it's the example in `help`), as did `find kind=window name=Lines` → "1 window dk74 · window · Lines". Unique names are a pleasure.
- **Two sources of truth disagree on where Lines is.** `look Lines` says "at=97,1077 size=1100,945"; `window.list` (and my own move in task 5) says it's at 24,24. The world's `at=` is stale because "where a window sits is not in the world". So `look` shows an old position as a fact. Either drop at/size from `look` or keep them current.
- `look Lines` gives size; `window.list` doesn't. Only window I could get a size for (others' `look` shows no at/size at all, e.g. Feed).
- `rows window` (10) and `window.list` (9) list different sets: `rows window` includes "dk205 · Widget · Guy studio" (not open) and omits nothing open; `window.list` shows "at" positions. A window thing can exist while not open, and nothing marks which.
- "Look at it": I wanted to see what's in the window (its content). `look-view Lines` → "refused: look-view needs a component lens, its widget or window". Lines *is* a window, so the refusal is confusing (it means a *component* window). There's no word to see what a window currently shows. `window.focus Lines` → "Lines: brought forward" was the nearest "look".

Status: done (found and looked at its facts; can't see its content). 5 lines.
What would have made this obvious: already easy. Keep `look`'s at/size live (or drop them), and say in look-view's refusal which windows it does take.

## Task 20: make "open" mean the same as whatever word opens a window

Lines: `help open`, `open feed`, `open Appearance`, `help word.set`, `word.set window.open aliases="open"`, `help open`, `open feed to=right`, `open "call the dentist"`, `window.list`, `open thing dk822`, `look dk833`, `window.close dk833`, `window.close dk832` (13).

- `open` already worked as a plain verb (`open feed` → "Feed is open already: brought forward"), because window.open is the only `.open` family word. So the task was half-done before I began. But a plain verb is fragile (task 5/6: `move`/`close` broke on shared names), so I made it a real alias.
- `help words` had told me how: `word.set <word> aliases="open"`. `word.set window.open aliases="open"` → "ok word.set window.open [r1469] · aliases now open". Afterwards `help open` shows window.open's help with "also said: open". Clean.
- Unclear: does `aliases=` replace or add? The receipt says "aliases now open", so I think it replaces; if window.open had had other aliases I'd have wiped them. There's no `aliases+=`.
- **`open feed to=right` made a second Feed ("Feed 2", dk832)** even though Feed was open. `help window.open` says "Open already: brought forward; new=yes opens another". Adding `to=` silently behaves like new=yes. Expected: move the existing Feed to the right.
- `open "call the dentist"` → "refused: window: no lens or view called call; …". Again only the first word of a quoted name is quoted back (same as task 8), and opening a note by name isn't supported. The refusal lists views "lines, thing, help, tasks", while `help window.open` lists "lines, thing, help": "tasks" is missing from the help.
- `open thing dk822` worked (a "Thing" window targeting my note), with the noise line "~ no other window has target=: still made, as you said": the check printed an empty value.
- Note: `word.set` takes `<id>` per its "takes:" line, but names worked ("The word's name works").

Status: done. 13 lines.
What would have made this obvious: already obvious via `help words`. Fix `to=` silently opening a second window.

---

## Tally

Done 14 (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 15, 17, 19, 20) · partly 6 (9, 12, 13, 14, 16, 18) · failed 0. About 210 lines in all.

What I changed in the sandbox and left there: post dk821; note dk822 + dock pin dk823; card "buy milk" dk825 (in no lane, after undo); button "My feed" dk827; verb `tidy` dk829; rule "guy says hi" dk830; Feed window reopened as dk828; four windows in quadrants; help of `verb` and topic page dk804 rewritten; `window.open` alias `open`. Undone: theme, pin dk821, `post` help, dk37 text, wm.mode.

## Top 10 frictions (ranked by cost)

1. **Plain verbs break on shared names, and the refusal is wrong about why.** `close Help` (the example on help's first screen) and `move Feed` both say "say which, or name the thing" when I did name it. The real cause (the name also belongs to a word or lens) is never stated. The family word (`window.move Feed`) resolves the same name fine.
2. **Verb arguments: `<a>` in help= becomes a kind, and `$2` by name fails.** Copying the documented example made a broken word ("no a you can see is called Feed"). Then `tidy Feed Appearance` failed on the second name though both are open, and claimed "nothing was done" after step 1 had already moved Feed.
3. **Silent wrong results.** `task.add "buy milk"` made an empty card with no warning; `open feed to=right` opened a second Feed instead of moving it; `wm.arrange` said "layout re-solved" while wm was off with 0 windows.
4. **I can't tell whether things happened.** `press` always times out ("window did not answer in 10 s"), even on the existing Feed button. Rule firings and `guy.say` leave no record. Window moves have no receipt, `window.list` shows no sizes, and `look` shows a stale position.
5. **Undo is one step deep per thing.** After undoing `task.done`, undoing `task.add` is refused with "undo that first", and undoing the undo is refused with "there is no redo". The refusal points into a dead end.
6. **`recent` hides acts and actors.** Closes and forgets (my `window.close Help`, the undone task) vanish. Every line says "Alex (by agent for Alex)", so agents are anonymous. Records can't be looked up (`look r1440` is refused).
7. **Every refusal says "refused:".** That covers ambiguity, a wrong kind, a timeout, a module that's off, nothing to pause, and a help miss. Refusals aren't logged either, so there's no word for "why was that refused, and who may".
8. **Noise on success.** "~ no other window has lens=feed (they say …): still made, as you said" comes with nearly every make, up to six lines of `do_bound=dk25` internals for a rule. Receipts show ids and internals instead of names ("theme=dk514", "trial_until taken away").
9. **My identity is hidden.** I'm "agent for Alex" in who, posts, look and recent; "claude" only appears in `rows agent` and history's `made_by=`. Two agents for Alex would look the same. And "theme.use … just you" quietly means "Alex's theme" for an agent.
10. **Two window systems and three "pins".** window.* vs wm.*: both have close/focus, wm is off, and its help is spec-speak ("live needs rollout arming"). `pin` (a post, leaders only) vs `make kind=pin` (a dock icon) vs `bar=taskbar` meaning the dock.

Honourable mentions: quoted names are reported by their first word only ("nothing here is called buy", "no lens or view called call"); help descriptions are cut off with "…"; `help kind=note` silently prints the main help; topic `set text=` doubles the title; `press` is labelled a see word; `help window.move` says both "nothing is recorded" and "undo: yes"; media words reach the real PC from a "sandbox"; a refusal's pointer ("look model says more") leads to another refusal (ambiguous `model`).

## Liked (keep these)

- The `help` first screen: identity, line shape, quoting, receipts and undo, all in 15 lines.
- Topic pages (`help theme`, `help buttons`, `help tasks`, `help music`, `help fixing`) often contain the exact line for the task.
- The `help <word>` footer: signature, "who may", "undo", "from". `help check` (help that may mislead) is a lovely idea.
- Ambiguity refusals that list the candidates with ids and kinds.
- `history <thing>`, `recent by=me`, `find kind= name=`, `who`, `;` batching, and `\"` escapes inside values.

## What `help` should say on its own (draft first screen)

    You are claude, an agent acting for Alex (with his rights) on his desktop.
    A line is: word  thing  key=value…      e.g.  window.move Feed to=left
      Name things by name ("Seabright board") or id (dk74). If a name is
      shared, you're shown the choices.
      Quote text with spaces. ; joins lines. Every change prints a receipt
      [r812]; undo takes back your last one (undo again goes further back).
    Start here:
      window.list · open feed · close Help         windows
      post "…" · task.add title="…" · done <task>  feed and task board
      who · recent · history <thing>               who's here, what changed
      verb · rule · word.set                       make your own words
    help <topic>: windows · feed · tasks · theme · buttons · words · undo ·
                  people · music · fixing          help all: every word, by family

## What `help <topic>` should do

- `help windows` / `help window` (singular and plural both): what an Agora window is; how to list, open, move, close, focus and tile; the spots *and their sizes*; how window.* differs from wm.* and when to use which; and the trap that a window's name can collide with a lens or word (so use window.* or the id).
- `help <kind>` (`help note`, `help pin`, `help window`): what the kind is, the facts it expects (`name=`, `text=`…), how to make one (`make kind=note name=… text=…`), and every word that acts on it. When a word and a kind share a name, show both sections.
- `help <family>` (`help task`, `help wm`): every family word with a usage line, grouped into do / see / hear.
- `help <anything unknown>`: never fall back silently to the main screen (as `help kind=note` did). Say "nothing called X" and suggest the closest words by meaning, not just by substring (`help tile` matched `window.native`).
- `help all`: grouped by family, each with a one-line plain-language description, not cut off.

## Words I expected to exist and didn't

- `tile` / `window.tile` / `arrange` for Agora windows (wm.arrange exists, but it's for the PC-wide manager and was off).
- `redo`, or an undo that walks back through my own acts.
- `refusals` / `why` (what was refused lately, and who may).
- `look r<n>` (read one record from a receipt).
- `note` as a maker (`note "call the dentist"`), and a "put this where Alex sees it" word (a home / Needs Me surface).
- `whoami` / `me`, and `role <group>` as a *read* (who leads a group).
- `window.size`, or sizes in `window.list`; a word to see what a window shows.
- `guy.last` / guy history; `rule.log` (when a rule fired).
- `alias` as a top-level word (`alias open window.open`), instead of `word.set … aliases=`.

## Naming: what I would rename or merge

- `bar=taskbar` → `bar=dock` (it *is* the dock; Windows already has a taskbar).
- `make kind=pin` (dock icon) → `dock.add` or `kind=dock-item`; keep `pin` for posts only. "Pin" has three meanings today.
- Put `window.close` / `wm.close` / `pane.close` behind one `close` that prefers the window, and the same for `focus`. Keep wm.* as an implementation detail, or rename it `pc.*` / `desktop.*` so it's clear it reaches non-Agora windows.
- Merge `stop` and `off` (two names, one act), or explain the difference.
- `board.feed` vs `post`'s feed vs the `feed` lens: three things called feed. Rename the community board's to `board.threads`.
- `catch-up` vs `board.catch-up`; `look` vs `look-view` vs `describe`: say which to use when.
- The receipt for closing a window says "forget … out of every view"; for windows, say "closed".
- `theme.use` for an agent should say "for Alex" explicitly; `theme.current` "(me)" should say "(Alex's choice)".
- Show the agent's own name everywhere: "claude (for Alex)", not "agent for Alex".
- One help voice: lowercase plain sentences everywhere (board.*, wm.* and component.* are Title-case spec sentences).

