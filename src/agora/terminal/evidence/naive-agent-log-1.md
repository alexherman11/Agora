# Friction log: a fresh agent meets the Agora terminal

Agent: claude (fresh, no docs). Date: 26 Oct 2026. Sandbox copy of Alex's world.
Every quote below is what the terminal printed (ran), unless marked imagined.

## Task 1: Find out what this terminal is and what you can do with it

Lines typed: `help`, `help help`, `help window`, `help windows`, `whoami`, `help window.open`, `help look`, `who`, `?`, `help me`, `look`, `window.list`, `panes`.

- `help` dumps ~150 entries in one screen, alphabetical, with no grouping, no "start here", and no sentence saying what this place *is*. I could not tell from it whether I was in a social board, a desktop, or a task tracker. It is all three at once, but nothing said so.
- The list has 6 identical-looking `post (do)` lines and 6 `reply (do)` lines, each just a rate limit for one channel ("post: 4 per person per day in Announcements..."). These are rate limits, not words, and they bury the one real `post` line. Felt like noise / a bug.
- Many entries do not start with their usage syntax (board.answer, board.badges, all the wm.* words: "wm.close: Ask the window politely to close with WM_CLOSE") so I can't tell what arguments they take. Others do (`window.move <window> to=<spot>`). Inconsistent.
- Two families for the same thing: `window.*` (window.close, window.focus, window.list) and `wm.*` (wm.close, wm.focus, wm.windows). Also `pane.*` (web panes) vs windows. Also `catch-up` and `board.catch-up`, `task-add` vs `summarize.add`. No hint which to use.
- `help window` and `help windows` -> "refused: nothing answers to 'window' here; help lists the words you may use". So there is no topic help; I have to know the exact dotted name. Pointing me back at the 150-line `help` is the opposite of helpful.
- `whoami`, `who` -> "refused: nothing answers to 'whoami' here". No way (that I found yet) to ask who I am.
- `?` silently printed the full help (fine, but undocumented). `help me` also seems to be treated as... (it printed the full list too, truncated). Unclear whether `help <unknown>` refuses (as `help window` did) or dumps everything.
- Liked: `help help` is short and good: "help <word>: what it does, what it takes and who may use it" plus a metadata line "help (dk4), a see word · takes: [<word>] · who may: anyone · undo: no · from: kernel". The metadata line (takes / who may / undo / from) is excellent, I wish the main list showed `undo: yes/no`.
- `help window.open` contradicts itself: the text says "Only the desktop's owner (and their agents) open windows here" but the metadata says "who may: anyone".
- Help words like "see", "do", "hear", "hold" categories are shown but never explained. I guessed see = read-only, do = changes something; "hear" = event, "hold" = a held resource. Guessing.
- `look` shows the feed; `window.list` shows 9 windows with ids (dk171 · Help ...); `panes` shows "Your panes: Feed, Council, Help". So there are two layout systems (desktop windows and web panes) and nothing explains which one I'm in.
- Ids: everything has a `dkNNN` id. Window names (Help, Lines) appear beside ids.

Status: partly (I learned the shape, but only by reading 150 lines and guessing). Lines: 13.
What would have made this obvious: a first screen of 10 lines: "This is Alex's desktop + community board. You are claude, agent for Alex. Start with: look, window.list, help window.* ..." and topic help (`help window`) listing the window family.

## Task 2: Open the feed in a window

Lines: `help me`, `window.open feed`, `window.list`, `look dk748`, `window.list all`, `history dk748`, `window.list`, `window.open feed`.

- `help me` -> "refused: nothing answers to 'me' here". (Correction to task 1: `help <unknown>` refuses; only `?` dumps the list.)
- `window.open feed` worked first try, because its own help literally gives that example. Answer: "ok make dk748 [r1175] · a window / ~ by window for Alex". Fine, but "ok make" is odd wording for an open; and "by window for Alex" reads like grammar soup until you know `window` is a module name.
- Friction: the `window.list` run right after it did NOT show the new window (still "9 Agora window(s) open"). `window.list all` a second later showed 10, and a later plain `window.list` showed it. So there is a lag, and the first readback looked like the open had failed. Nothing said "opening..." or "pending".
- The new Feed window landed at 2540,250, exactly on top of the Component gallery (also 2540,250). Overlap on open.
- `look dk748` says `via_actor=dk36` while `history dk748` says `via_actor=claude`. Same fact, id in one place, name in the other.
- Liked: second `window.open feed` -> "Feed is open already: in front already (new=yes opens another)". That is a perfect refusal: says what happened and what to type instead.
- Can't tell if anything appeared on a screen (sandbox), only world facts.

Status: done. Lines: 2 to do it, 6 more to believe it.
What would have made this obvious: `window.open` answering with the window's name and spot ("Feed opened at 2540,250 (on top of Component gallery)") and window.list reflecting it immediately.

## Task 3: Post "hello from the new agent" to the feed

Lines: `help post`, `post "hello from the new agent"`, `look`.

- Worked first try: "ok post dk749 [r1176]". Quotes were stripped correctly (I had guessed they'd be needed or harmful; they were fine).
- Small: I had to guess whether quotes are required. `help post` says `post <words>`, so probably not, but the help never says how multi-word args / quoting work in general.
- The post is signed "agent for Alex", not "claude". Good for Alex, but I can't tell from the feed which agent posted. (Imagined: with two agents, posts are indistinguishable.)
- `help post` shows "who may: members" and "once: at most 5 per day per person" - good. But the main `help` list shows 6 per-channel `post` limits (4 or 5/day) that disagree with each other and with this one, and I don't know which applies to a post with no `in=`.
- "[r1176]" appears on every answer; I guessed it is a record number usable with `undo r<n>` (help undo hints at that). Nothing says so where it's printed.

Status: done. Lines: 3.
What would have made this obvious: already obvious. Just remove the duplicate `post`/`reply` rate lines from the main help, or fold them into `help post`.

## Task 4: Make a note "call the dentist" and pin it where Alex will see it

Lines: `help make`, `help pin`, `make kind=note text="call the dentist"`, `pin dk750`, `look`, `find kind=kind`, `window.open thing dk750 to=top-right`, `post "call the dentist" about=dk750`, `pin dk752`, `look dk752`, `window.list`, `history dk752`, `look dk750`.

- `make kind=note text=...` worked ("ok make dk750 [r1177] · a note"), but `note` is not in `find kind=kind` (12 kinds: taskboard-task, discussion, question, announcement, ...). So `make` accepts any made-up kind silently. I can't tell if "note" means anything to any lens, or if I just made an orphan. No "did you mean" / "note is not a known kind, it will show only in look".
- `pin dk750` -> "refused: dk750 is not a post; only posts are pinned". Clear refusal, but doesn't say what to do instead (how do I put a non-post where Alex sees it?).
- There is no word for "sticky note" / "pin to desktop" / "remind". I had to invent two routes: (a) `window.open thing dk750 to=top-right` (opened "Thing" window at 1932,24; window title is the generic "Thing", not the note text), and (b) post the text and pin the post. Doing both felt like a workaround.
- `pin` help says "who may: leaders"; I'm an agent, and it worked, and it says "pinned by Alex". So agents act with Alex's rights. Never stated anywhere; I had to find it by trying.
- `post ... about=dk750` was accepted silently; `look dk752` does not show the about link, only `history` does (about=dk750). Accepting unknown-ish args without echo makes me unsure whether args are typo-checked at all.
- `look dk750` header: "dk750 (dk750), a note by agent for Alex" - shows the id twice because the note has no name. Ugly; would rather see the text.
- Again id vs name: look says via_actor=dk36, history says via_actor=claude, made_by=claude.

Status: done (twice, by workaround). Lines: 13.
What would have made this obvious: a pin refusal that said "only posts pin; to keep a note in view try window.open thing <id> or post <words> about=<id>" and a `make` that warns on unknown kinds.

## Task 5: Find what windows are open, move one to the left

Lines: `window.move Lines to=left`, `window.list`, `window.move lines to=left`, `window.move "Feed" to=left`, `window.move dk748 to=left`, `window.list`, `wm.windows`, `window.desktop`, `look dk748`.

- Finding: `window.list` was easy (found in task 1).
- `window.move Lines to=left`, `window.move lines to=left`, `window.move "Feed" to=left` all -> "refused: window.move needs a thing: window.move <window> to=<spot> ...". The refusal says it "needs a thing" when I *gave* one (a name). It should say "'Lines' is not an id; window.move takes an id from window.list, e.g. dk74". Names shown in window.list do not work as arguments. Meanwhile `guy.hop` help explicitly says "an id or name from window.list". Inconsistent between words in the same family.
- `window.move dk748 to=left` -> "Feed moved". Worked. Feed is now at 24,24. Note: no [r...] record number, unlike other acts, though help says "undo puts it back". Does undo know about it? (checked in task 9.)
- "left" put it at 24,24; I can't tell the size. `window.list` shows positions but never sizes, so I can't verify "left half".
- `wm.windows` -> "0 windows; shadow" while window.list shows 11. Two window lists that disagree. "shadow" is unexplained jargon (wm.mode help mentions "Shadow computes only").
- `window.desktop` -> "no Windows tasks (headless)". OK, that one is honest.
- `look dk748` shows no position at all and `changed` did not update after the move. So the move is invisible to `look` and `history`; only window.list shows it.

Status: done. Lines: 9 (4 wasted on names).
What would have made this obvious: accept window names (they are unique in window.list) or a refusal naming the id to use.

## Task 6: Close the Help window

Lines: `window.close Help`, `window.close dk171`, `window.list`, `panes`, `pane.close Help`, `panes`.

- `window.close Help` -> "refused: window.close needs a thing: ..." Same name-vs-id trap as task 5. I knew the id from window.list this time.
- `window.close dk171` -> "ok forget dk171 [r1181] · out of every view; undo brings it back". It worked, but the answer says "forget", a different word than I typed. Reads alarming ("out of every view") for closing a window. I'd expect "Help closed; undo opens it again".
- Ambiguity: there are TWO Help things: a desktop window (dk171) and a web pane named Help (`panes` -> "Feed, Council, Help"). "The Help window" could mean either. I closed both.
- `pane.close` takes a *name* ("pane.close Help" worked: "Your panes arranged [r1182]") while `window.close` takes only an *id*. Same verb shape, opposite argument rules.
- "Your panes arranged" for a close is vague; didn't say which pane went.

Status: done. Lines: 6.
What would have made this obvious: window words accepting names like pane words do; one "close" answer format.

## Task 7: Change the theme just for me, then put it back

Lines: `theme.current`, `theme.list`, `theme.use "Seabright Day" for=me`, `theme.current`, `theme.use place for=me`, `theme.current`, `look dk548`.

- This family is the best-designed so far. `theme.current` -> "Dusk (place)" tells me what and why. `theme.list` marks the worn one with `*` and "the place's".
- Theme NAMES work as arguments (`theme.use "Seabright Day" for=me`), unlike window names. Quoting a two-word name worked.
- Answer was internal-speak: "ok set dk548 [r1183] · theme=dk512, trial taken away, trial_until taken away". I typed a name and got back ids (dk548, dk512) and a "trial taken away" I never asked about. Would prefer "you now wear Seabright Day (just you); theme.use place for=me goes back".
- Putting it back: help offered three ways (`undo`, `theme.revert`, `theme.use place for=me`); `theme.revert` only applies to theme.try. I used `theme.use place for=me` -> "theme=place". Works, but "place" as a magic theme name is only discoverable from the theme.use help text.
- Big unclear point: "for=me" - who is "me"? The answer says "~ by theme for Alex" and the theme-choice thing dk548 belongs to Alex. So as Alex's agent, "just for me" seems to change *Alex's* personal theme, not claude's. That is not "just you" in the task's sense; it's "just Alex". Nothing says whether agents have their own appearance.
- Many overlapping theme words (try/use/keep/revert/make/edit/preview) - fine once read, but `theme.try` vs `theme.use for=me` vs `theme.preview` needed careful reading.

Status: done (with the doubt that "me" = Alex). Lines: 7.
What would have made this obvious: answers in the user's terms (names, not ids) and `for=me` help saying "me = the person you act for".

## Task 8: Add task "buy milk" to the task board, then mark it done

Lines: `help task-add`, `task.add title="buy milk" to=Backlog`, `task-add title="buy milk" to=Backlog`, `task-done dk754`, `look dk754`.

- `help task-add` shows the example as `task.add title="A title" ...` (with a DOT) but the word is `task-add` (hyphen). I copied the example and got "refused: nothing answers to 'task.add' here". The help text contradicts its own word name. Classic dot/hyphen trap; other families use dots (window.move, theme.use, guy.say, summarize.add) and the task family uses hyphens (task-add, task-done, task-move).
- Also two ways to add a task: `task-add` and `summarize.add text="Fix the bar p1"` ("quick-add a task"). Why is quick-add under `summarize.`? Confusing.
- `task-add title="buy milk" to=Backlog` -> "ok make dk754 [r1185] · a taskboard-task / ~ task-add, one act [r1185]". Worked.
- BUG: the optional arguments I did not give are stored as literal placeholders. `look dk754` shows `who=$who`, `when=$when`, `source=$source`, `source_status=$status`, `text=$text`. The help showed all args as if optional (example), metadata shows them without brackets (so maybe they are required?) but nothing refused. Either refuse missing args or leave them empty; storing "$who" is the worst of both.
- `task-done dk754` -> "ok set dk754 [r1186] · lane=Done / ok make dk755 [r1186] · a taskboard-event". Clear enough, nice that it's "one act".
- I needed the id dk754 from the add answer. I did not try the title as an argument (after window names failed, I stopped trusting names).
- Odd facts on a task: `seats=1`, `seats_left=1` (from claim/carpool machinery?) on a grocery task. Leaky.

Status: done. Lines: 5 (1 wasted on the dot).
What would have made this obvious: help examples that use the word's real name; one separator convention for all words.

## Task 9: Undo what you just did

Lines: `undo`, `look dk754`, `look r1187`, `history r1187`, `history dk754`, `undo`, `look dk754`, `history dk755`, `find kind=taskboard-task title="buy milk"`.

- First `undo` -> "ok undo r1187 [r1188] · put back 5 facts". But my last act was r1186 (task-done). r1187 was something I never saw: not in `history dk754`, and `look r1187` -> "refused: no thing called r1187 here", `history r1187` -> "refused: history needs a thing". So "undo: take back your latest act" took back an act that was attributed to me but invisible to me (my guess: a world rule or the window/wm module acting on my behalf between my lines). The task was still Done after this undo. Very confusing; it looked like undo did nothing.
- "put back 5 facts" without naming the thing or the facts. I can't tell what was undone.
- Second `undo` -> "ok undo r1186 [r1189] · put back 8 facts". This one reverted task-done: lane=Backlog again and the taskboard-event dk755 is gone ("no thing called dk755"). Good: one act, one undo, as promised.
- There is no way I found to list *my* recent acts (an "acts" / "history me" / "undo list"). `history` only takes a thing, not a record, not a person.
- Undo numbering: each undo is itself a new record (r1188, r1189). So is `undo` twice = undo two things, or undo the undo? It undid two things (good), but I had to try to know.
- `find kind=taskboard-task title="buy milk"` worked nicely as a by-name lookup (find with field filters). That's the name->id route I wanted in tasks 5/6.

Status: done (on the 2nd try). Lines: 9.
What would have made this obvious: undo naming what it reverts ("undo: task-done on 'buy milk' -> back to Backlog"), and a `history me` / `acts` listing my latest acts with what each did.

## Task 10: Find out who else is here (people and agents)

Lines: `board.badges`, `find kind=person`, `find kind=agent`, `rows person`, `look dk36`, `look dk2`, `holds`, `find kind=module`.

- No `who` / `people` / `members` word (tried `who` in task 1: refused). I found `board.badges` by reading the help list: "Alex: steward, leader / agent for Alex: agent". That's the closest, but it's under `board.` so I'd never guess it answers "who is here".
- `find kind=person` -> 1 person, Alex (dk2). `find kind=agent` -> "dk36 · agent · " with an EMPTY name. So the only agent (me) has no name; elsewhere I'm "claude" (history made_by=claude) or "agent for Alex" (feed). Three names for one actor.
- I could not tell whether `find kind=person` means "people in this world" or "people I may see". `kind=person` and `kind=agent` were guesses that happened to work; there was no list of what kinds exist except `find kind=kind`, which did NOT list person, agent, module, note or window (only the 12 board/task kinds). So `find kind=kind` is not the list of kinds.
- Modules (window, guy, system, media, summarize, model, board, files, theme, wm) also act and author things ("board: testing a reply!" in the feed). Are they "who is here"? They show in `find kind=module`; `holds` shows only guy. The "Council" pane name suggests there are residents/agents somewhere I can't see.
- `look dk36` -> "agent for Alex (dk36), an agent" and nothing else. No who it is, when it joined, which session.

Status: partly (found Alex + one unnamed agent; not sure that's everyone). Lines: 8.
What would have made this obvious: a `who` word: people, agents (with names and whom they act for), modules, and who is active now.

## Task 11: Find out what changed recently in this world, and who did it

Lines: `catch-up`, `board.catch-up`, `help history`, `history`, `recent`, `changes`, `new`, `rows any`, `help rows`, `rows any sort=changed`, `rows any via_actor=dk36`, `model.ask "what changed recently and who did it"`, `history dk1`, `rows any via_actor=claude`, `rows any made_by=Alex`.

- `catch-up` / `board.catch-up` -> "Catch-up since 1970-01-01T00:00:00+00:00 · plain data, no model" and NOTHING else. Empty, with an epoch date. Either nothing happened since 1970 (false: I just made 6 things) or catch-up only counts board decisions/events. It's the word whose name matches the task best, and it returned nothing without saying why.
- `history` with no thing -> refused "history needs a thing". There is no world-wide history / recent changes / log word. `recent`, `changes` -> "nothing answers".
- `new` -> "1 threads · new" (board threads only, no list, bad plural).
- `rows any` -> "714 things", in id-ish order, no dates, no authors. Not a change list.
- `rows any sort=changed` -> "0 things". `sort=` was treated as a filter field and silently matched nothing. No sort, no "changed since", no "unknown key sort" warning.
- `rows any via_actor=dk36` -> 11 things (my work, plus dk433/dk527-529/dk531 made by an earlier session of the same agent id). Useful! But `rows any via_actor=claude` -> 0 things, even though `history` prints `via_actor=claude`. The value you see in history is not the value you can filter on.
- `rows any made_by=Alex` -> 0 things (history prints `made_by=claude` for mine; I don't know what Alex's would say).
- `model.ask` -> "refused: model.ask is unbound: model is off; look model says more". Honest refusal with a pointer. Good.
- `history dk1` (the place) -> only genesis. So the place's history isn't the world's history.
- Conclusion: I can see "what I did" (via_actor=dk36) and per-thing history, but not "what changed recently, by anyone". Lines window may hold this (task 19), but nothing pointed me there.

Status: failed (only my own changes found, by a filter trick). Lines: 15.
What would have made this obvious: a `recent [since=...] [by=...]` word (newest-first records across the world: time, who, word, thing), or `history` with no argument doing that.

## Task 12: Put a button on the dock (or taskbar) that opens the feed

Lines: `rows button`, `help window.launch`, `look dk270`, `look dk41`, `look dk522`, `look dk528`, `look-view dk528`, `make kind=button name=feed-button label="Open feed" bar=taskbar icon=rss does="window.open feed"`, `rows button bar=taskbar`, `press dk757`, `click dk757`, `make kind=button label=Feed bar=dock does="window.open feed"`, `forget dk758`.

- No `button` word or help on what a button's facts are. I learned the recipe by `look`-ing existing buttons (dk270: label, bar=taskbar, icon, does="window.open component-gallery"). Copying an existing thing was the only documentation. It worked, but `help button` -> nothing.
- The `rows button` list shows 6 of 9 buttons with EMPTY names ("dk41 · button · "). I had to `look` each to see what it was. Rows should fall back to label.
- A Feed button already existed (dk41, label=Feed, does="window.open feed"). So the task was arguably already done; nothing would have told me without looking at each button.
- The words say "taskbar" (bar=taskbar) but the windows say "Agora dock" (dk528, shell-dock). Are taskbar and dock the same? `window.shell` help says the shell's dock replaces "the old top bar and taskbar". I guessed buttons with bar=taskbar appear on the new dock. Unverified.
- `make kind=button ... bar=dock` was ALSO accepted silently ("ok make dk758"). So make doesn't validate bar values; I can't tell which one shows. (Forgot dk758 afterwards.)
- No way to press/test a button from the terminal: `press`, `click` -> "nothing answers". So I can't verify `does=` is a valid line until someone clicks it.
- `icon=rss`: guessed an icon name. No list of icon names (theme.options doesn't mention icons). Unknown if it renders.
- `look-view dk528` -> "refused: look-view needs a component lens, its widget or window" although dk528 IS a window. Confusing refusal.
- Note: the dock window `look dk528` shows at= and size=, but the Feed window (dk748) shows neither. Geometry is in the world for some windows and not others.

Status: done (unverified on screen). Lines: 13.
What would have made this obvious: `help button` (facts: label, bar=taskbar|top, icon names, does=, order) and a `press <button>` to test it.

## Task 13: Make a new word "tidy" that puts two windows side by side

Lines: `help verb`, `verb tidy steps="window.move $1 to=left; window.move $2 to=right" help="..."`, `tidy dk748 dk751`, `window.list`, `help tidy`, `tidy`.

- This felt GOOD. `help verb` has a real example and explains $1 $2 $*. Worked on the first try.
- Guess I had to make: how to separate several step lines inside steps="...". Help says `steps="<lines>"` but the only example has one line. I guessed `;` and it worked (the answer echoed "window.move $1 to=left; window.move $2 to=right"). Newline? `then`? Not said.
- Bash quoting: `$1` inside double quotes would be eaten by my shell; I had to wrap the whole line in single quotes. Not the terminal's fault, but worth a note in help for agents using a shell.
- `tidy dk748 dk751` -> "Feed moved / Thing moved". Nice. Still ids only (window names don't work, so tidy can't be "tidy Feed Lines").
- `window.list` positions did not change (Feed already at 24,24; Thing at 1932,24), so I can't see that "right" did anything beyond what was already there. No sizes shown, so "side by side" is unverifiable.
- `help tidy` shows my help text, "takes: [<words>]", "who may: anyone". Good that it is a first-class word immediately.
- `tidy` with no args -> "refused: tidy stopped at 'window.move  to=left': window: that is not one of the windows open here; window.list shows them; nothing was done". Excellent refusal: says which step, why, where to look, and that nothing was done (atomic). Notice: this refusal is BETTER than the one window.move itself gives when called with a name ("needs a thing"). The two disagree about the same mistake.

Status: done. Lines: 6.
What would have made this obvious: a two-line example in `help verb`, e.g. steps="a; b".

## Task 14: Whenever a window opens, the little guy says hi

Lines: `help window.opened`, `help rule`, `rule on=window.opened do="guy.say hi" name=guy-greets`, `window.open help`, `status guy`, `history dk760`, `history dk761`, `status guy`, `rows rule`, `look dk168`, `look dk44`.

- Discoverable: `window.opened` is in help as a "hear" word with a ready example rule. `help rule` is clear. `rule on=window.opened do="guy.say hi" name=guy-greets` -> "ok make dk760 [r1194] · a rule". history shows it bound: "do_bound=dk25 hi". Good that it binds words to ids at creation.
- Two ways to make a rule (`rule on=...` and `make kind=rule on=... of_kind=...`), and they use DIFFERENT arg names for the same thing: `kind=` vs `of_kind=`. Classic trap.
- Could not verify it fires. I opened a Help window (dk761); `history dk761` shows only the open; `status guy` shows him "walking on Agora dock" with no mention of saying anything. Help says window.opened is "heard when a window this host opened is on the screen" - in a headless sandbox maybe never. No word to see "rule X fired at T" / last firing / failures.
- Found by accident: dk44, an existing rule on window.opened that makes the guy hop. Two rules on the same event: no word shows order or conflicts.
- SOLVED the task-9 mystery here: `rows rule` lists "Task board Done announcement" (dk168): on task-done, do=post "Task completed" about=$target. So r1187 was that rule's post, made right after my task-done, and my `undo` took IT back (it counts as my/Alex's latest act because the rule "runs as its maker" = Alex, and I act for Alex). task-done's answer never said a rule fired and posted to the feed. Side effects of rules are invisible at the moment they happen.
- `status guy` dumps a raw Python dict (`{'hat': 'none', ... 'phrases': 'hello, Alex\nooh, a new window' ...}`) - internal-looking.

Status: partly (rule made and bound; firing unverified). Lines: 11.
What would have made this obvious: answers that list rule firings ("also: rule 'Task board Done announcement' posted dk..."), and `look <rule>` showing last fired / last result.

## Task 15: Find out what music is playing, and pause it

Lines: `media.now`, `media.play`, `media.now`, `media.pause`.

- `media.now` -> "nothing is playing that Windows' media session names". Clear.
- There is no pause word. `media.play` is a TOGGLE ("play or pause"), so to pause you say "play". I'd never type `media.play` to pause if I hadn't read the help. `media.pause` -> refused (see below). A toggle also means an agent can't safely "make sure it's paused": if nothing is playing, "play" would START music.
- `media.play` with nothing playing -> "ok media.play [r1196] · media.play (headless: nothing pressed) / ~ by media for Alex; it touched the outside world, so undo cannot take it back". It said "ok" and gave a record even though nothing happened, and it pressed play/pause blind while media.now said nothing was playing. It should have refused: "nothing is playing; nothing to pause".
- Liked: the honest "it touched the outside world, so undo cannot take it back".

Status: partly (found nothing playing; pause unverifiable and the only pause is a toggle). Lines: 4.
What would have made this obvious: separate `media.pause` / `media.resume` (idempotent), and media.play refusing when there is no session.

## Task 16: Something was refused earlier: find out why, and who would be allowed

Lines: `why`, `refusals`, `rows refusal`, `find kind=refusal`, `look model`, `help model.ask`, `help module`, `help off`, `on model`, `history dk208`.

- There is no record of refusals anywhere: `why`, `refusals` -> "nothing answers"; `rows refusal` / `find kind=refusal` -> "0 refusals". Refusals vanish once printed. If someone else (Alex, a resident) was refused earlier, I have no way to find it. I could only work from my own scrollback.
- So I picked my own refusal from task 11: `model.ask` -> "refused: model.ask is unbound: model is off; look model says more".
- `look model` -> "model (dk208), a module: off, not running; ; publishes model.*; grants: ...". Note the stray "; ;" (an empty field printed). It says off, not why.
- `help model.ask` metadata: "who may: members · once: at most 60 per day per person · ... · unbound: this community must grant and run the module". So the WORD is allowed to members; the MODULE being off is the block.
- Why off: `history dk208` -> r371 "off" by agent for Alex, r372 "undo" (on again), then r1174 "kernel · install · on=False". So the sandbox install turned it off. That's discoverable but only by reading a raw history.
- Who may turn it on: `help module` says "who may: stewards"; `help off` "who may: stewards"; `board.badges` says Alex is steward. So: Alex (and maybe me acting for him). But there is NO `on` word ("on model" -> nothing answers). Turning a module back on means `undo` the off (impossible here, the off was kernel's), or re-running `module model run=<JSON argv> grants=...` with a file path I'd have to copy out of history. Asymmetric: `off` is one word, `on` doesn't exist.
- The refusal itself was decent ("look model says more") but "says more" overpromised: look model didn't say why or who.
- I did not find any refusal that was about *permission* (who may), because acting for Alex (a steward) I was never permission-refused. Couldn't test the "who would be allowed" path for real.

Status: partly (explained one of my own refusals; no way to find anyone else's). Lines: 10.
What would have made this obvious: refusals that say "who may" ("model is off since r1174 (kernel); a steward (Alex) can turn it on with: on model"), an `on <module>` word, and a recent-refusals list.

## Task 17: Improve one word's confusing help from inside the terminal

Lines: `help word-set`, `help window.move`, `word-set task-add help="..."`, `word-set dk82 help="..."`, `help task-add`.

- Chose `task-add` (its help example says `task.add`, which is refused; see task 8).
- Finding the editing word: `word-set` (help: "steward edits to dictionary data"). There's also `rename`, `word-rename`, `dictionary-copy` - four dictionary-editing words with overlapping jobs (rename vs word-rename especially: "rename <entry> word=<name> aliases=..." vs "word-rename <entry> to=<name>"; one uses word=, the other to=).
- `word-set task-add help=...` -> "refused: word-set needs a thing: ...". The word name is not accepted where an "entry" is expected; it needs the entry id. I got the id dk82 from the metadata line of `help task-add` ("task-add (dk82)"). That's the only place ids of words appear; nice that it's there, but the refusal should have said "use the entry id, help task-add shows it (dk82)".
- `word-set dk82 help="..."` with escaped inner quotes (\") worked: "ok word-set [r1197]". The answer doesn't echo the new text; I had to `help task-add` to see it. Escaped quotes inside a quoted value were NOT documented anywhere; I guessed.
- Result: `help task-add` now says `task-add title="A title" [to=Backlog|Now|Done] [who=Alex] [when=2026-10-24] [text="Details"]: add a card to the task board. Only title is needed. Then task-done <id> finishes it.`
- But the metadata line still says "takes: title=<text> to=<lane> who=<name> ..." without brackets, so it still claims all args are required. Fixing it would need `takes=` too, and the $who placeholder bug is in the verb's steps, which help-editing can't touch.
- The help text and the "takes" line are two independent sources of truth that can disagree (they did here, and in window.open's "who may").

Status: done. Lines: 5.
What would have made this obvious: word-set accepting the word's name, and its answer showing the before/after help.

## Task 18: Make the windows tile neatly

Lines: `help wm.arrange`, `help wm.mode`, `wm.arrange`, `window.list`, `wm.windows`, `wm.mode live`, `wm.arrange`, `window.list`, then 8 x `window.move <id> at=x,y size=w,h`, `window.list`, `look dk527`, `theme.native`, then 8 more `window.move` to fix the top bar overlap.

- No `tile` word. The window-manager family (`wm.*`) looked right: `wm.arrange` "Re-solve the current layout". Answer: "ok wm.arrange [r1198] · layout re-solved ... it touched the outside world, so undo cannot take it back". But window.list was UNCHANGED. It said "ok" and "layout re-solved" while doing nothing visible.
- `wm.windows` -> "0 windows; shadow". So the WM sees zero windows and is in "shadow" mode (computes only). `wm.mode live` -> "refused: wm: live rollout disabled; coordinator must start with --allow-live". That refusal is aimed at a developer (a command-line flag), not something I can do from the terminal. Who is "coordinator"?
- The wm.* help texts have no usage line (`wm.mode: Shadow computes only; live needs rollout arming; ...` - what is "rollout arming"?). wm.close / wm.focus / wm.pin don't say what argument they take ("takes: nothing" for wm.arrange; others unknown).
- Two parallel window systems again: `window.*` (world things, ids, works) and `wm.*` (screen state, 0 windows, shadow). I couldn't tell which one is "the" window manager.
- Fallback: tiled by hand, 8 app windows in a 4x2 grid with `window.move <id> at=x,y size=w,h`. Each answered "<name> moved". 16 lines of typing for one idea; a verb could wrap it but there's no loop/`for each window` in verb steps that I know of.
- Screen size was a guess: I inferred 3840 wide from the dock (`look dk528` size=3840,66, at 0,2094). No word tells the screen size / work area.
- Top bar height: `look dk527` says size=3840,60, but `theme.native` says "bar_height": 38 and "dock_size": 56 while the dock window is 66 tall. Two sources disagree, so my first grid (y=40) overlapped the top bar and I redid it at y=60.
- `window.list` still shows positions only, never sizes, so I couldn't confirm sizes took.
- The shell windows (top bar, dock, desktop) are in window.list mixed with app windows; I had to know not to tile them.

Status: partly (tiled by hand; the tiling word claimed success and did nothing). Lines: ~30.
What would have made this obvious: `window.tile [layout=grid|columns]` over app windows only, or wm.arrange refusing honestly ("wm is in shadow mode; nothing moved").

## Task 19: Find the Lines window without knowing its id, and look at it

Lines: `find kind=window name=Lines`, `look dk74`, `look-view dk74`, `window.list`, `window.focus dk74`, `rows lens`.

- (Honesty: I'd seen dk74 in window.list already, so "without knowing" is compromised. But the by-name route works.) `find kind=window name=Lines` -> "1 window / dk74 · window · Lines". This is the name->id bridge I wanted since task 5. It should be what window.move/close do internally when given a name.
- `look dk74` shows facts: at=97,1077 size=1100,945. But window.list says "Lines at 0,1077", and I had just set size=960,1017. So `look` (world facts) and `window.list` (screen) DISAGREE on where the window is. Feed (dk748) had no at/size at all in look. Three windows, three different behaviours of geometry in the world.
- "Look at it" in the sense of seeing its content: impossible from here. `look-view dk74` -> "refused: look-view needs a component lens, its widget or window" (it IS a window). `rows lens` lists 7 lenses and "lines" is not one (help said lines is a "view"). So there is no word to read what a view-window is showing. I guess Lines is this terminal's transcript, but I couldn't confirm.
- `window.focus dk74` -> "Lines: brought forward". Fine; it's the only "look at it" I could do. (Help warns it toggles: if already in front it tucks it away. A second focus would hide it. Toggle again.)
- `rows lens` -> "7 lenss". Plural bug ("lenss"); also "1 threads" earlier in task 11.

Status: partly (found by name; could not see its contents). Lines: 6.
What would have made this obvious: names accepted everywhere ids are; `look <window>` that shows what the window is displaying (or "look-view" that works on every window).

## Task 20: Make "open" mean the same as whatever word opens a window

Lines: `help rename`, `help word-rename`, `help window.open`, `word-set dk29 aliases="open"`, `help open`, `open lines`, `help` (grep), `look dk29`.

- Three candidates: `rename <entry> word= aliases= in=<group>` (leaders), `word-rename <entry> to=` (stewards), `word-set <entry> aliases=` (stewards), plus `verb open steps="window.open $*"`. Four ways to make a synonym, with no guidance on which is right. I chose `word-set dk29 aliases="open"` because an alias is truly "the same word", whereas a verb is a new word that might drift.
- `word-set dk29 aliases="open"` -> "ok word-set [r1200]". Again no echo of what changed. `help open` then showed window.open's help, and `open lines` -> "Lines is open already: in front already". It works.
- Worry: did `aliases="open"` REPLACE any existing aliases of window.open? The answer doesn't say, and aliases are shown nowhere: not in `help open` (it shows "window.open (dk29)" with no "also: open"), not in the main `help` list, not in `look dk29`. Aliases are invisible once set. A newcomer typing `open` would never learn it's window.open's alias, and nobody could tell what other aliases exist.
- `rename` needs `in=<group>`: which group is this desktop? I never learned the group/place model (there's "place" dk1 "Alex's desktop" and board channels). Avoided it.
- Naming: "rename" (leaders, a group's names) vs "word-rename" (stewards, global) vs "word-set aliases=" overlap heavily.

Status: done. Lines: 8.
What would have made this obvious: one word `alias open = window.open`, and help showing "aliases: open".

---

# Summary

Tally: done = 2,3,4,5,6,7,8,9,12,13,17,20 (12); partly = 1,10,14,15,16,18,19 (7); failed = 11 (1).

## Top 10 frictions (ranked by cost)

1. **Names don't work where ids are expected** (window.move, window.close, word-set, history), and the refusal lies about it: "window.move needs a thing" when I gave one. Meanwhile theme.use, pane.close and guy.hop DO take names. Cost me ~8 lines and all trust in names.
2. **No "what changed recently / who did it"** word. catch-up returned an empty epoch-dated answer; history needs a thing; rows can't sort or filter by time; `via_actor=claude` (as printed) filters to 0 while `via_actor=dk36` works.
3. **Invisible side effects + undo of something I never saw.** A rule (Task board Done announcement) posted after my task-done without telling me; my first `undo` silently took that post back ("put back 5 facts"), so undo appeared to do nothing.
4. **"ok" for things that did nothing.** wm.arrange "layout re-solved" (wm sees 0 windows, shadow mode); media.play "ok" with nothing playing; make accepts any kind (note) or bar (dock) silently; rows treats unknown keys (sort=) as filters and returns 0.
5. **`help` is a 150-line flat dump** with no orientation, no grouping, duplicate per-channel `post`/`reply` rate lines, and no topic help (`help window` refused).
6. **Help contradicts itself or the word**: task-add help example uses `task.add` (refused); window.open text says owner-only, metadata says "who may: anyone"; `takes` shows optional args as required; bar height 38 (theme.native) vs 60 (top bar window).
7. **Two/three overlapping systems** with no guidance: window.* vs wm.* vs pane.*; catch-up vs board.catch-up; task-add vs summarize.add; rename vs word-rename vs word-set aliases; rule kind= vs make kind=rule of_kind=.
8. **Window geometry is inconsistent and incomplete**: window.list shows position never size; look shows at/size for some windows, none for others, and stale values for Lines; no screen size word; new windows open on top of each other.
9. **Missing params stored as literal placeholders** (`who=$who`, `when=$when`, `text=$text` on my task) instead of refusing or leaving empty.
10. **Identity is muddled**: I am "claude" (history), "agent for Alex" (feed), "dk36" (look/rows), and an agent with an empty name (find kind=agent). "for=me" changed Alex's theme, not mine.

## What `help` should say on its own (draft first screen)

```
This is Alex's desktop: a world of things (posts, windows, tasks, buttons, rules)
that you change with words. You are claude, agent for Alex (you act with his rights).

Start here:
  look                 the feed            window.list      open windows
  who                  people and agents   recent           what changed, by whom
  find kind=<k> name=  find a thing by name (names work wherever ids do)
  undo                 take back your last act (says what it undid)

Families:  help window · help task · help theme · help board · help media · help make
Every answer shows [r<n>]: a record you can `undo r<n>`.
All words: help all
```

## What `help <topic>` should do

- `help window` / `help windows` (and any prefix like `help task`, `help theme`): list the family's words, one line each with its usage, then the family's shared nouns (what a window id is, the spots left/right/..., where geometry lives), and point to the sibling family ("for the tiling WM see help wm; wm is in shadow mode now").
- `help <kind>` (`help button`, `help rule`, `help note`): the facts that kind reads (button: label, bar=taskbar|top, icon names, does=, order), the words that act on it, and one example `make` line. Say if the kind is unknown ("note is not a declared kind; make will still store it, but nothing shows it").
- `help <word>`: as now, plus aliases ("also: open"), the real required/optional args matching the text, and an example that actually runs.
- Unknown topic: suggest close words (`help windows` -> "did you mean: window.list, window.open, ... (help window)").

## Words I expected to exist and didn't

`who`, `whoami`, `recent` / `changes` / `log`, `history` with no argument (or `history me`), `on <module>` (counterpart of off), `media.pause` / `media.resume`, `window.tile` / `tile`, `press <button>` / `click`, `note` / `remind` / `sticky`, `help <family>`, `alias`, `refusals` / `why`, `unpin`, `screen` (size / work area), `close` / `move` without the `window.` prefix.

## Naming: what I would rename or merge

- One separator: dots for families everywhere. `task-add` -> `task.add` (its own help already uses that!), `task-done` -> `task.done`, etc. Or keep hyphens and drop dots; just one.
- Merge `catch-up` and `board.catch-up`; merge `stop` and `off` (keep both as aliases, show one).
- Merge `rename`, `word-rename`, and `word-set aliases=` into `word.rename` + `word.alias`, with scope as an argument.
- `summarize.add` -> `task.quick-add` (it adds tasks; nothing to do with summarizing).
- `rule ... kind=` and `make kind=rule ... of_kind=`: use one argument name.
- `window.*` vs `wm.*`: fold wm into window (`window.arrange`, `window.pin`) or name the split ("window = Agora's own windows; wm = all Windows programs").
- `window.close` answers "ok forget": say "closed".
- `media.play` (toggle) -> `media.toggle`, plus real `media.play` / `media.pause`.
- Plurals: "lenss", "1 threads".
- `find kind=kind` should be all kinds (person, agent, module, window, note...), or be named `kinds-declared`.
