# Friction log — fresh agent "claude", Agora terminal, 26 Oct 2026

All quotes are what the terminal printed (ran). Line counts are lines I sent to the terminal.

## Task 1 — What is this terminal, what can I do

Lines: `help`, `help lines`, `help all` (3).

- Liked: `help` first screen is genuinely good. It tells me who I am ("You are agent for Alex, acting with Alex's rights"), the grammar (word, thing id, key=value), quoting, `;`, receipts and undo. That is most of what I need.
- Liked: `help all` says "all 153 words here, each once" — a full, honest list.
- Friction: `help all` is 153 lines, unsorted by area, mixes very different worlds: `board.*` (a community board?), `task-*` (hyphen), `theme.*` (dot), `window.*` vs `wm.*` vs `pane.*` (three window families), `summarize.*`, `model.*`. As a newcomer I can't tell which window family to use for "a window".
- Friction: naming style mixes dot and hyphen: `window.open`, `theme.use` vs `task-add`, `task-done`, `word-set`, `word-rename`, `look-view`, `personal-view`. Also `catch-up` vs `board.catch-up` both exist.
- Friction: many help lines are truncated with "…" in the list ("history its record trail, oldest first: record, at (UTC), by, word and…"). The truncated part is often the useful part.
- Friction: some help lines describe implementation, not use: "upload send bytes through POST /upload or agora.upload(file)", "summarize.save painter multiline save adapter", "window.native the shell's bars only (SHELL.md)" — SHELL.md is a file I'm not allowed to read; help pointing to a file is a dead end for a desk agent.
- Friction: `reply` help says "30 per person per day in Announcements" — that is a limit, not what the word does.
- Friction: three entries share the help "a copyable feed reading; make your own board-order thing or verb" (`happening-soon`, `needs-answers`, `new`, `top-this-week`) — you can't tell them apart from help.
- Odd: the "fix this page" footer names a different id each time: `help` said `set dk756 text=…`, `help lines` said `set dk757 …`. Is each help answer its own thing? Not explained.
- Unclear: "see words only read; do words change things" — but help never marks which words are see vs do in the listing.

Status: done. 3 lines. What would have made this obvious: it mostly was; grouping `help all` by area (windows, feed, tasks, theme, people, rules/words) and marking see/do would make it scannable.

## Task 2 — Open the feed in a window

Lines: `window.open feed`, `window.list`, `look dk768`, `window.list`, `help window.open` (5; it worked on line 1).

- Liked: the help example literally was `window.open feed to=left`, so my first guess worked.
- Friction: the receipt is cryptic: "ok make dk768 [r1216] · a window\n~ by window for Alex". It says "make", not "open". What does "~ by window for Alex" mean? (I think: the `window` module did it on Alex's behalf, but it reads like noise.) It doesn't say "Feed window opened at 2540,250".
- Friction (could not tell if it happened): `window.list` straight after showed 9 windows and NOT dk768. Only on the second `window.list` did "dk768 · Feed · feed at 2540,250" appear. So the open is asynchronous, and nothing tells you so. I briefly believed it had failed.
- Friction: the new window landed at 2540,250 — exactly on top of the Component gallery (dk549, also 2540,250). Default placement stacks windows.
- Friction: `window.list` help says "front first", but the list looks sorted by id (dk171 … dk74, dk768 last even though it is newest and should be in front). Note also dk74 sorts after dk549 — string sort, not number sort.
- Unclear: `look dk768` shows `via_actor=dk36` — an id with no name. Who is dk36? Rule says "show names, never ids".
- Good: `help window.open` is excellent — signature, spots, "Open already: brought forward; new=yes opens another", who may, undo: yes, and how to fix the help. This is the model every word's help should follow.

Status: done. 1 line to do it, 5 total. What would have made this obvious: a receipt that says "opened Feed (dk768) at 2540,250; may take a moment to appear" and window.list showing pending windows.

## Task 3 — Post "hello from the new agent"

Lines: `post "hello from the new agent"`, `help post`, `look dk769`, `rows post` (4; worked on line 1).

- Liked: worked first try; quoting rule from `help` was enough.
- Friction: receipt "ok post dk769 [r1217]" doesn't echo what was posted or where (which feed). I had to `look dk769` to confirm.
- Note: `look dk769` signs it "agent for Alex" — not "claude". So my own name isn't used; I am anonymous "agent for Alex". If there are several agents, posts are indistinguishable.
- Friction: `rows post` lists 5 posts with text truncated mid-word ("Your desktop now runs on the new kernel: these windows, the ") and no author column.
- Surprise: `help post` says "once: at most 5 per day per person" and "a slower lane" — useful, but a new agent testing would burn its quota fast; nothing tells me how many I have left.

Status: done. 1 line. What would have made this obvious: already obvious; receipt could echo "posted to the feed as agent for Alex: hello from the new agent".

## Task 4 — Note "call the dentist", pinned where Alex will see it

Lines: `help make`, `help pin`, `make kind=note text="call the dentist"`, `rows kind`, `help kinds`, `pin dk770`, `look dk770`, `window.open thing dk770 to=top-right`, `help wm.pin`, `window.list`, `window.list`, `wm.windows`, `wm.pin dk771`, `help pin windows`, `help buttons`, `make kind=pin bar=taskbar shows=dk770`, `rows pin`, `rows button bar=taskbar`, `set dk772 label="call the dentist"`, `look dk772`, `look dk46` (21).

- Guess: there is no `note` word. I guessed `make kind=note text=…` and it worked — but `rows kind` lists 12 kinds and **note is not one of them** (taskboard-task, discussion, question, announcement, event, poll, ask, offer, document, decision…). So `make` accepts any kind name silently, with no warning "note is a new kind". A typo like `kind=ntoe` would silently make an orphan.
- Friction: "pin" means three different things:
  1. `pin <post>` = keep a post at the top of the feed (leaders only; refused: "dk770 is not a post; only posts are pinned").
  2. `wm.pin <key>` = keep a window fixed in the window manager.
  3. `make kind=pin bar=taskbar shows=<id>` = a dock pin that opens a thing (only found inside `help buttons`!).
  `help pin` only knows meaning 1. `help pin windows` returned the same `pin` help — the extra word was ignored silently.
- Friction: the refusal for `pin dk770` was clear about why but not about what to do instead (it could have said "to keep a thing on the dock: make kind=pin bar=taskbar shows=dk770").
- Friction: `wm.pin` "takes: <key>" — what is a key? `wm.windows` answered "0 windows; shadow" (no explanation what shadow means here), and `wm.pin dk771` → "refused: wm: choose a current manageable window from wm.windows". So window.list ids (dk…) are not wm keys, and wm.windows is empty. Two window systems that don't share ids.
- Friction: `window.open thing dk770` worked, but the window is titled "Thing" in window.list (`dk771 · Thing · thing at 1932,24`), not "call the dentist". Again async: first window.list after open didn't show it.
- Friction: `make kind=pin` receipt doesn't say where it went; `rows pin` shows pins with **empty names** ("dk46 · pin · "). I added `label=` by guessing; help buttons only mentions `label=` for buttons. I cannot tell if a pin shows the label or the note's text on the dock (can't see the screen).
- Friction: `look dk772` header "dk772 (dk772)" repeats the id instead of a name.
- Did it end up somewhere Alex sees? I believe yes: a dock pin (dk772) plus a note window top-right (dk771). Unverified visually.

Status: done (unverified visually). 21 lines. What would have made this obvious: a `help pin` that lists all three meanings, or a `note` word ("note \"call the dentist\" pin=dock").

## Task 5 — List windows, move one left

Lines: `help window.move`, `window.move dk768 to=left`, `look dk768`, `window.list`, `window.move Appearance to=right`, `window.list` (6; worked on line 2).

- Liked: `window.list` is the obvious word and it worked; help gave `to=left`.
- Friction: answer was just "Feed moved" — **no receipt [r…]**, unlike every other do word. The first `help` page promised "every act prints a receipt"; so is this undoable? (help says "undo puts it back".) Inconsistent.
- Friction: `look dk768` after the move still shows `changed=…04:31:25Z` and no position at all; position is only in `window.list` ("feed at 24,24"). `look` on a window doesn't tell you where it is or its size.
- Friction: "to=left" landed at 24,24 — I can't tell size; did it become a left half? window.list shows only position, never size.
- Refusal I liked: `window.move Appearance to=right` → "refused: window.move takes an id, not a name: Appearance is dk546 (a window). Say: window.move dk546 to=right". It tells me exactly what to type. But: if it can resolve the name unambiguously, why refuse? (And Alex's rule says show names, not ids.)
- Unclear: window.list has window kinds like "Agora top bar", "Agora dock", "Agora desktop" mixed with real app windows. Moving dk529 (desktop) would be odd; nothing marks which are movable.

Status: done. 2 lines to do it. What would have made this obvious: already near obvious; accept unambiguous names, and show size in window.list.

## Task 6 — Close the Help window

Lines: `window.close dk171`, `window.list` (2).

- Liked: worked at once, and this time the list updated immediately.
- Friction: the receipt reads "ok forget dk171 [r1222] · out of every view; undo brings it back". Closing a window is reported as *forget … out of every view*, which sounds like I deleted the Help thing for everyone. The word is close; the receipt should say "closed Help (dk171)".
- Note: I had the id from the earlier window.list; `window.close Help` by name would probably be refused the same way as move.

Status: done. 1 line. What would have made this obvious: obvious; just fix the receipt wording.

## Task 7 — Theme just for me: try one, put it back

Lines: `help theme`, `theme.current`, `theme.list`, `theme.try "Seabright Day"`, `theme.current`, `theme.revert`, `theme.current`, `look dk548`, `theme.use "Night Metal" for=me`, `theme.current`, `theme.use place for=me`, `theme.current` (12).

- Liked: `help theme` is a good topic page: it names the "just for you" path explicitly and warns that `theme.use <name>` alone changes the place's theme. `theme.current` saying "Dusk (place)" / "(trial, 29 s left)" / "(me)" is lovely.
- Surprise: `theme.try` lasts only ~30 seconds ("trial, 29 s left"). help says "for a while". Nowhere says how long, or how to set the length (`for=5m`?).
- Friction: two ways to undo a theme: `theme.revert` (for a trial) vs `theme.use place for=me` (for a kept one) vs `undo`. Three words for "put it back".
- Friction: `theme.use place for=me` — "place" as a magic theme name is only discoverable from `help theme`.
- Real confusion: who is "me"? The receipt says "~ by theme for Alex" and the choice dk548 belongs to Alex's desktop. I am "agent for Alex", so "just for me" actually changed **Alex's** own look, not the agent's. There seems to be no separate per-agent theme (agents have no screen). The task's "not for everyone" was satisfied (place theme untouched), but help's "just for you" is ambiguous for an agent.
- Friction: receipts expose internals: "ok set dk548 [r1223] · trial=dk512, trial_until=2026-10-27T04:34:14.498309+00:00" — ids and microsecond timestamps, not "trying Seabright Day for 30 s".
- `look dk548` → "a theme-choice by theme", doesn't say whose choice.
- Odd: `theme.list` shows "Catppuccin Mocha · dark · Catppuccin Org" — "Catppuccin Org" looks like an author label; column meaning not stated.

Status: done. 4 lines for the core (try, revert, use for=me, use place for=me). What would have made this obvious: help theme was enough; say trial length, and make "for=me" explain whose "me" it is when an agent speaks.

## Task 8 — Add "buy milk" to the task board, mark it done

Lines: `help tasks`, `task-add "buy milk"`, `look dk773`, `task-done dk773`, `look dk773`, `rows taskboard-task`, `help task-add`, `task-remove dk773`, `task-add title="buy milk"`, `task-done dk776`, `look dk776`, `history r1229` (12).

- **Big friction (silent wrong result):** `task-add "buy milk"` answered "ok make dk773 [r1227] · a taskboard-task" — but the card has **no title**. The quoted text was silently dropped. `rows taskboard-task` showed it as "dk773 · taskboard-task · " (blank). `post "…"` takes positional text, so I expected `task-add "…"` to as well. `help task-add` says "Only title is needed" — yet it accepted a card without one. It should either take the free words as the title, or refuse: "task-add needs title=…; say task-add title=\"buy milk\"".
- Note: `help tasks` actually shows `task-add title="Buy milk"` — I skimmed it, because `post "hello"` taught me positional quoting. Two neighbouring words, two conventions.
- Friction: an untitled card shows `seats=1 seats_left=1` — sign-up-slot facts leaking onto a task (looks like tasks are built on `claim` slots). Meaningless to a task user.
- Liked: `task-done` receipt shows both effects (lane=Done, plus a taskboard-event) under one receipt and says "one act". `look dk776` header finally shows a name: "buy milk (dk776)". Names appear in the header only when there's a `title`.
- Friction: receipt numbers skipped (r1228 → r1230 for my next act). Something else acted in between (r1229) — I can't look a receipt up: `history r1229` → "refused: history needs a thing, by its id". There's no word to look up a receipt by its r-number, though receipts are what every answer hands you. (`look r1229` untried.)
- Friction: task-remove's receipt again says "forget … out of every view".
- `rows taskboard-task` list is 33 lines of Alex's real work; no filter by lane shown in help (does `rows taskboard-task lane=Done` work? help says "filtered by their aspects" — untried).

Status: done (after one silent failure). 12 lines; 2 for the right way. What would have made this obvious: task-add taking free words as the title, or refusing when title is missing.

## Task 9 — Undo what I just did

Lines: `undo`, `look dk776`, `history dk776`, `help undo`, `undo r1232`, `look dk776`, `history dk548`, `look r1233`, `undo r1234` (9).

- **Biggest friction so far (undo did the wrong thing, invisibly):** my last act was task-done [r1232]. `undo` answered "ok undo r1233 [r1234] · put back 5 facts". **r1233 was not mine** — I never saw it. `look dk776` showed the task still in lane=Done. So plain `undo` took back *someone/something else's* act (probably a module or another actor acting "for Alex", since I act with Alex's rights and "your latest act" seems to mean Alex's latest). The receipt didn't say which thing or which word it undid — only "5 facts".
- I could not find out what r1233 was: `look r1233` → "refused: no thing called r1233 here"; `history` needs a thing id. And I can't put it back: `undo r1234` → "refused: r1234 is itself an undo; there is no redo". So I silently reverted 5 unknown facts in Alex's world and can't repair it. (In the sandbox this is harmless; in the live world this is dangerous.)
- `undo r1232` then worked: "ok undo r1232 [r1235] · put back 8 facts", and the task left Done (no lane fact now — it isn't back in Backlog explicitly; it just has no lane).
- Friction: undo receipts should name the thing and word: "undid task-done on buy milk (dk776): lane Done → (none)".
- Friction: `history dk776` shows `made_by=claude; via_actor=claude` but `look` says "by agent for Alex". Two names for me.
- Friction: "put back 8 facts" for a one-lane move is surprising (task-done also made a taskboard-event dk777; presumably forgotten too — not shown).
- Seen in passing: `history dk548` shows earlier theme trials (03:44–03:49) by someone before me in this sandbox — so the sandbox is shared with prior runs/agents, which explains foreign records.

Status: partly (plain undo undid the wrong act; `undo r1232` did the right one). 9 lines. What would have made this obvious: `undo` should mean *my* (claude's) latest act, and its receipt should name the word and thing it reverted; and a `look r1233` / `receipt r1233` word should exist.

## Task 10 — Who else is here

Lines: `help people`, `role`, `rows person`, `rows agent`, `rows module`, `board.badges` (6).

- Liked: `help people` is exactly right: rows person, rows agent, rows module, board.badges. Answers: 1 person (Alex, dk2), 1 agent (claude, dk36), 10 modules (window, guy, system, media, summarize, model, board, files, theme, wm). Badges: "Alex: steward, leader / agent for Alex: agent".
- Solved a mystery: `via_actor=dk36` on everything I made is me, "claude". But `look` prints me as "agent for Alex", history prints `made_by=claude`, rows agent prints "claude". Three renderings of one actor; the `look` one hides my name.
- Friction: `role` alone (to see roles) → "refused: role needs a thing, by its id: role <person> leader|member|none in=<group>…" — help says role is "who leads a group and who belongs to it", which reads like a see word, but it's a do word that changes roles. Its one-line help is misleading.
- Friction: "who else is here" mixes presence and membership. Nothing says who is *active now* (online, awake).
- Modules are listed as actors ("which act too") — good to know, explains "~ by window for Alex".

Status: done. 4 useful lines. What would have made this obvious: a `who` word that prints people, agents and modules in one go, with names.

### Task 9 — correction, found during task 11 (ran)

I found what r1229 and r1233 were. `rows` (all) showed `dk775 · post · Task completed`; `history dk775` → "r1229 · … · Alex · post · kind=post; text=Task completed; made_by=Alex; about=a hidden thing". `look dk168` → a rule "Task board Done announcement", `on=task-done`, `do=post "Task completed" about=$target`, by Alex. So:
- Every `task-done` fires Alex's rule, which posts "Task completed" **as Alex**, as a separate act with its own receipt, *after* my receipt. My task-done receipt never mentioned it.
- r1233 was the rule's post for my second task-done. Plain `undo` took that back (Alex's latest act, and I act with Alex's rights), not my task-done. So undo is "the latest act by anyone I act for", and rule side-effects are separate acts — the help's "a do line that runs several steps is still one act, one undo" isn't true when a rule fires.
- Leftover: the first rule post dk775 "Task completed" still stands in the feed, `about=a hidden thing` (the untitled card I removed). My mistake left a public feed post as Alex, and nothing told me.
- Also my 5-a-day post limit: the rule posts as Alex, not me — so automation spends Alex's quota.

## Task 11 — What changed recently, and who

Lines: `history`, `catch-up`, `help history`, `rows record`, `history dk1`, `help changes`, `help recent`, `rows`, `help rows`, `board.catch-up`, `help find`, `history dk775`, `look dk168`, `history dk768`, `rows any via_actor=dk36`, `history dk2`, `history dk36` (17).

- **No world-wide "what changed" word.** `history` alone → "refused: history needs a thing, by its id". `history dk1` (the place) only shows genesis. `rows record` → "0 records" — records (r…) aren't things. `catch-up` → "Catch-up since 1970-01-01T00:00:00+00:00 · plain data, no model" and then **nothing** (empty, but with a since-1970 header that suggests it read everything). `board.catch-up` same.
- `help changes` and `help recent` both landed on the "Undo and history" topic (nice fuzzy matching), but it only offers per-thing `history <id>`.
- `rows` with no kind dumped **735 things** in one answer, ~370 of them blank `paint-report` rows. Wall of text; no paging, no sort by changed, no "most recent first". (Rule "Nothing scrolls" notwithstanding, this is the opposite of brief.)
- Workaround that partly worked: `rows any via_actor=dk36` → 30 things touched via me (claude). That shows *what I* made, not what changed or when. I could not filter by time (`changed>…` syntax unknown; not tried further). Filtering needed an id (dk36), not `claude`.
- Who did things: history rows name "Alex", "window for Alex", "theme for Alex", "agent for Alex", "kernel" — readable. But I found the sandbox has earlier acts (theme trials at 03:44–03:49, the help topics dk756–767 made via dk36 = an earlier "claude") — **"claude" is shared by every agent session**, so I can't tell my acts from a previous agent's.

Status: partly (per-thing histories yes; a recent-changes view across the world, no). 17 lines. What would have made this obvious: a `recent [n] [by=<name>]` word (or `history` with no id = the place's latest acts, newest first).

## Task 12 — A dock button that opens the feed

Lines: `look dk41`, `make kind=button bar=taskbar label="Open feed" does="window.open feed" order=2`, `rows button bar=taskbar`, `press dk779`, `help press` (5).

- Liked: `help buttons` (seen in task 4) gave the exact line, including "bar=taskbar is the dock". Worked first time: "ok make dk779 [r1236] · a button".
- Finding: a Feed button already exists (dk41, label Feed, does=window.open feed, order=1). Nothing warned me I was making a duplicate. (Memory note says the shell avoids duplicate launchers — the world doesn't.)
- Friction: the dock is called "taskbar" in `bar=taskbar` but "dock" in window.list ("Agora dock") and the help. Two names for one bar. Also the task said "dock (or taskbar)" — a newcomer has to learn they are the same.
- Friction: I can't test the button from the terminal: `press dk779` → "refused: nothing answers to 'press' here; did you mean panes?" — the "did you mean" suggestion is unrelated. No `press`/`click`/`run <button>` word, so I can't verify `does=` works without a screen.
- Friction: order=2 put mine second in `rows` (between Feed and Help), but Help had no visible order; unclear if order is per-bar and whether two buttons may share one.
- Friction: three bar items have machine-ish labels: "component-gallery-button", "seabright-board-button", "appearance-button" — these are names, not labels, shown to people.

Status: done (unverified on screen). 1 line. What would have made this obvious: it was; add `press <button>` to test it, and warn on duplicate does=.

## Task 13 — A new word "tidy" that puts two windows side by side

Lines: `help words`, `help verb`, `verb tidy steps="window.move $1 to=left; window.move $2 to=right" help="…"`, `tidy dk768 dk771`, `window.list`, `tidy Feed Thing`, `help tidy` (7).

- Liked a lot: `help verb` contains *this exact example* ("e.g. verb tidy steps=…"). `$1 $2 $* $target $name` explained in one line. Receipt "ok verb tidy (dk780) [r1237] · a new word in Alex's desktop: …" is the best receipt I've seen — names the word and echoes the steps. `help tidy` immediately shows my help text.
- Friction: `help words` is listed as a topic in the first help screen ("topics: … words …"), but it just printed the full 153-word list again, not the "Making your own words" topic (dk766 exists in `rows`, titled exactly that). So the `words` topic is shadowed by "all words".
- Friction: running `tidy dk768 dk771` answered "Feed moved / Thing moved" — no receipt, so I can't see that it's "one act, one undo" as help promises.
- Friction: "Thing" was already at 1932,24; after `to=right` window.list still says 1932,24. Did right do anything? No size shown, so I can't tell whether either window is now a half-screen.
- Inconsistent refusals: `tidy Feed Thing` → "refused: tidy stopped at 'window.move Feed to=left': window: that is not one of the windows open here; window.list shows them; nothing was done". Calling `window.move Appearance` directly (task 5) gave the much better "takes an id, not a name: Appearance is dk546 … Say: window.move dk546". Same word, different refusal depending on whether a verb called it. Liked: "nothing was done" — clear atomicity.
- Quoting: nested quotes worked as long as the whole line is in bash single quotes; `$1` survived. A shell user must know to single-quote or `$1` vanishes — not the terminal's fault but worth a line in help verb.
- `help tidy` says "takes: [<words>]" — auto-derived; it doesn't know it takes two window ids.

Status: done. 1 line to define, 1 to run. What would have made this obvious: already obvious; route `help words` to the "Making your own words" topic.

## Task 14 — Whenever a window opens, the little guy says hi

Lines: `help rule`, `help guy`, `help window.opened`, `rule on=window.opened do="guy.say hi" name="…"`, `window.open help`, `window.list`, `status guy`, `window.open tasks`, `window.list`, `status guy`, `history dk781`, `window.list`, `status guy`, `look dk782` (14).

- Liked: `help window.opened` gives a rule example on that very word. `help guy` lists guy.say. The rule line worked first try: "ok make dk781 [r1238] · a rule". `status guy` then showed `saying "hi"` — so I could verify it fired without a screen. 
- Friction: `rule` receipt says "make … a rule", doesn't echo "when window.opened → guy.say hi".
- **Bug-looking refusal:** `window.open help` → "refused: window: window.open needs a view: lines, thing, help, tasks". *help is in its own list of allowed views.* (Maybe because I closed the Help window earlier = "forget dk171"? Unknown.) The refusal contradicts itself.
- **Naming trap:** `window.open tasks` did not open the task board. It opened "Running windows" (dk782, shows=tasks) — i.e. Windows *task* buttons. Meanwhile the task board is `taskboard-components`. "tasks" means two different things.
- Timing: the hear word fires only when the window is actually on screen; first `window.list`/`status guy` after the open showed nothing, a few seconds later the guy was "saying hi". Async again, unannounced.
- Rule fires "as the rule's maker" — rules I make act as me (claude/agent for Alex); Alex's rule posts as Alex. Good to know; only `help rule` says it.
- `status guy` dumps a raw Python dict ("{'hat': 'none', 'hair': 'original', …}") and "look r0" — internals, and r0 looks like a receipt id but isn't.
- Guy's phrases already include "ooh, a new window" — there may already be built-in behaviour for new windows; my rule may double up. Not told.

Status: done (verified via status guy). 1 line for the rule. What would have made this obvious: it was; fix the `window.open help` refusal and rename the `tasks` view to `running` or similar.

## Task 15 — What music is playing; pause it

Lines: `media.now`, `help music`, `help media.play`, `media.pause`, `status media` (5).

- `media.now` → "nothing is playing that Windows' media session names". So nothing to pause.
- **Friction / hazard:** there is no pause word. `media.pause` → "refused: nothing answers to 'media.pause' here; did you mean media.prev or media.play or media.next?" (good suggestions). `media.play` is a *toggle* — "play or pause (one word, a toggle)". With nothing playing, sending it would likely *start* music on Alex's real PC (help says it "acts outside the world, so undo cannot take it back"). I deliberately did not send it. A safe `media.pause` (does nothing if already paused) is the word a user/agent needs; a toggle is unsafe for agents that can't hear the result.
- Unclear: is the sandbox's media module real (Alex's actual Windows session) or simulated? The terminal doesn't say which effects in this sandbox are real. `status media` → "media: running" only.
- Liked: `help music` topic is short and names undo: external up front.
- Naming: help topic is "music", words are "media.*".

Status: partly (found nothing playing; there was nothing to pause, and no safe pause word). 5 lines. What would have made this obvious: `media.pause` / `media.resume` as idempotent words, and `media.now` saying "paused: <song>" vs "nothing".

## Task 16 — Something was refused earlier: why, and who would be allowed

Lines: `help refused`, `help why`, `help test`, `refusals`, `help may`, `pin dk769`, `look dk7`, `role dk36`, `undo r1240`, `forgotten`, `help wm.mode`, `status wm`, `why pin dk770`, `test dk770 expr="field('kind') == 'post'"` (14).

- **No memory of refusals.** Refusals are not records: no receipt, not in any `history`. `refusals` → "refused: nothing answers to 'refusals' here"; `help refused` only found window.native (?!); `help why` found board.why-here/theme.current; `why pin dk770` → nothing answers to 'why'. So "find out why something was refused earlier" only works if you still have the text in your scrollback. In a shared world, I can't see refusals other people/agents/modules hit either.
- What I could reconstruct from my scrollback: my refusals were (a) `pin dk770` "dk770 is not a post; only posts are pinned"; (b) `wm.pin dk771` "wm: choose a current manageable window from wm.windows" (WM in "shadow", 0 windows); (c) `window.open help` "needs a view: lines, thing, help, tasks" (self-contradicting); (d) name-for-id refusals. None were about *rights* — all about wrong targets.
- Who would be allowed: only discoverable per word through `help <word>`'s "who may:" line (pin: "who may: leaders"; wm.mode: anyone; word-set: stewards). `board.badges` then says who is a leader (Alex: steward, leader). I *am* allowed to pin, because I act with Alex's rights: `pin dk769` → "ok pin dk769 [r1240] · it stays at the top of the feed" (then `undo r1240` → "put back 1 fact"). So "who may: leaders" quietly includes agents of leaders — help doesn't say so.
- `look dk7` (the pin word) shows only its help line, not its "who may".
- `wm.mode` help: "live needs rollout arming" — a refusal waiting to happen, with jargon ("rollout arming") and no way to see who/what arms it. I did not try `wm.mode live` (it would move real windows if it were armed).
- `role dk36` → "refused: dk36 is not a person" — I wanted my own role; agents have no role, they inherit their person's.
- `test` works (`… == 'post'` → "no") but its help is one dense paragraph of policy internals (sees_when, allows.<word>, digest, "fail closed") — the most intimidating help in the terminal.
- `forgotten` printed an empty answer (blank line) — empty results should say "nothing forgotten".

Status: partly (why: yes, from my own scrollback; who may: yes, per word; no way to find refusals I didn't witness). 14 lines. What would have made this obvious: refusals kept as a short per-actor trail (`refusals` / `history me`), each with "who may" and "say instead".

## Task 17 — Improve a confusing word's help, from inside the terminal

Lines: `help fixing`, `help role`, `word-set role help="…"`, `help role`, `help check`, `word-set task-add help="…"`, `help task-add` (7).

- Liked: this is very well supported. Every help answer ends "fix this help: word-set <word> help=\"…\"", `help fixing` explains steward vs `ask`, and `help check` is a great self-audit: "19 of 154 words have help that may mislead" plus "long first lines (over 220 characters), worth trimming". (Note 154 now — my `tidy` added one; `help all` had said 153.)
- Fixed `role` (its help "who leads a group and who belongs to it" reads like a see word but it changes roles): now "role <person> leader|member|none in=<group>: make a person a leader or member of a group, or take them out (it changes roles; to see who leads, say board.badges). Agents have no role of their own: they act with their person's." → "ok word-set role [r1242]".
- Fixed `task-add` to warn that bare quoted words are dropped (task 8's silent blank card). Escaped `\"` inside `help="…"` worked.
- Friction: the word-set receipt truncates the new help mid-word ("…or take them out (it changes r"). I had to `help role` to see it all.
- Friction: `help check` now flags my new `role` help as too long (>220 chars). The rule exists but word-set didn't warn me when I saved it.
- Friction: help check's "no usage line" complaints are all board.* and component-* — module words that don't follow the kernel's help convention.
- Unclear: I could word-set a kernel word because I act with Alex's rights (steward). Nothing warned "you are changing help for everyone, as Alex". For an agent fixing help, that's a big silent permission.

Status: done. 2 lines to fix. What would have made this obvious: it was; word-set could echo the full new help and warn if it fails `help check`.

## Task 18 — Make the windows tile neatly

Lines: `help tile`, `help wm`, `help windows`, `wm.arrange`, `help wm.arrange`, `theme.native`, `window.list`, `status wm`, `wm.windows`, `window.close dk782`, `window.move dk768 to=top-left; … dk771 to=top-right; … dk74 to=bottom-left; … dk268 to=bottom-right`, `window.list` (12).

- `help tile` → "no word called tile; these mention it: window.native the shell's bars only (SHELL.md)". The fuzzy search keeps landing on window.native for unrelated queries (refused, tile).
- `help windows` is good and says "wm.* is the window manager for every window on the PC" — so wm.arrange looked like the answer.
- **Silent no-op:** `wm.arrange` → "ok wm.arrange [r1244] · layout re-solved ~ by wm for Alex; it touched the outside world, so undo cannot take it back". But `status wm` = "shadow; 0 windows" and window.list positions were unchanged. So it said ok, claimed to touch the outside world, and did nothing visible. In shadow mode it should say "shadow: computed, nothing moved (wm.mode live to apply)".
- `wm.mode` "live needs rollout arming" — no word or help explains arming, so the WM is effectively unusable from here. And `window.*` and `wm.*` are two disjoint window systems: Agora windows (dk ids) don't appear in `wm.windows` at all.
- Workaround: four `window.move … to=<corner>` in one line with `;` worked → quadrants at 24,24 / 1932,24 / 24,1023 / 1932,1023. But only 9 spots exist; I had 7 app windows (+3 shell windows). The other three (Seabright board, Appearance, Component gallery) still overlap. There's no grid/columns spot, no `to=` for thirds, and no size printed.
- `theme.native` printed raw JSON (gap_inner 12, gap_outer 14…) — handy for understanding the 24px gutters, but JSON isn't a terminal answer.
- The `;` line answered with four "… moved" lines and no receipt, so I can't undo the batch as one act.

Status: partly (4 windows in quadrants by hand; no real tiling). 12 lines. What would have made this obvious: `window.tile` (or `wm.arrange` that works on Agora windows), and wm in shadow saying plainly that nothing moved.

## Task 19 — Find the Lines window without knowing its id, and look at it

Lines: `find kind=window name=Lines`, `rows window name=Lines`, `look Lines`, `look dk74`, `look-view dk74`, `window.focus dk74`, `window.list` (7).

- Liked: `find kind=window name=Lines` and `rows window name=Lines` both → "dk74 · window · Lines". Filtering by name= works. (window.list would also have shown it; that's the real first move.)
- Friction: `look Lines` → "refused: no thing called Lines here; look shows what there is". There *is* a thing whose name is Lines. Names don't work in `look`, and this refusal (unlike window.move's) doesn't say "Lines is dk74".
- **Contradiction:** `look dk74` says `at=97,1077 size=1100,945`, while `window.list` says "Lines at 24,1023" (after my task-18 move). `look` shows stale world geometry; window.list shows live screen state. Which is true? Neither answer says which source it is. (Also: look shows size for Lines but showed no at/size at all for the Feed window — inconsistent.)
- `look-view dk74` → "refused: look-view needs a component lens, its widget or window" — but dk74 *is* a window. Lines is apparently not a "component" window, so the refusal is misleading.
- `window.focus dk74` → "Lines: brought forward" (no receipt). Then `window.list` order did not change — confirms "front first" is not what the list does.
- Ambiguity in the task "look at it": `look` (facts) vs `window.focus` (bring to front). I did both.

Status: done. 1 line to find, 1 to look. What would have made this obvious: `look Lines` resolving a unique name; one source of truth for a window's position.

## Task 20 — Make "open" mean the same as window.open

Lines: `help alias`, `help word-rename`, `help open`, `word-set window.open aliases="open"`, `open feed`, `help open` (6).

- Liked: `help alias` landed on the "Making your own words" topic, which says exactly "word-set <word> aliases=\"open\" gives a word another name". Worked: "ok word-set window.open [r1246] · aliases now open". `open feed` → "Feed is open already: brought forward (new=yes opens another)". `help open` now shows window.open's help with "also said: open". 
- Friction: the alias recipe lives in the "words" topic, which `help words` does *not* reach (it prints all 153 words); `help alias` does. 
- Friction: `aliases="open"` — is it a replace or an add? "aliases now open" suggests replace; if window.open had other aliases I'd have wiped them silently. A plural setting set with `=` needs "add"/"remove" semantics or a warning.
- Alternative I considered: `verb open steps="window.open $*"` — would also work but would be a second word, not an alias. Help doesn't say when to prefer which.
- `word-rename` "Dotted names belong to the implementing module" — useful hint, but implies I shouldn't rename window.open; the alias is the right route. Nice.
- Again: as an agent with Alex's rights I changed the dictionary for the whole place without any "this changes it for everyone" note.

Status: done. 1 line. What would have made this obvious: `help words` → the words topic; an `alias` word (`alias open = window.open`).

---

# Summary

Tasks: done 15 (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 14, 17, 19, 20; of these 4, 12 and 14 were checked only through the terminal, never on screen), partly 5 (9, 11, 15, 16, 18), failed 0. About 190 lines sent in all.

## Top 10 frictions (ranked by cost)

1. **Plain `undo` undid an act that wasn't mine** (a rule's side-effect post, made as Alex), said only "put back 5 facts", and there's no redo and no way to look up r1233. Undo should mean *my* latest act and name what it reverted.
2. **Silent wrong results**: `task-add "buy milk"` made a blank card with an ok receipt; `wm.arrange` said "layout re-solved … touched the outside world" while moving nothing (shadow, 0 windows); `make kind=note` silently invented a kind. "ok" should mean it did what I asked.
3. **Rules fire invisible side effects**: task-done triggered Alex's rule to post "Task completed" as Alex, as a separate act, unmentioned in my receipt; it left a public post about a hidden thing.
4. **No world-wide recent changes**: `history` needs an id, `catch-up` is empty "since 1970", `rows` dumps 735 lines (370 blank paint-reports). No `recent`.
5. **Two window systems that don't meet**: `window.*` (dk ids) vs `wm.*` (keys, shadow, "rollout arming", 0 windows). wm.pin/wm.arrange useless for Agora windows; no real tiling.
6. **Names vs ids inconsistent**: window.move refuses a name but tells you the id; look refuses with no hint; inside a verb the refusal changes again; `find … name=` works. Just accept unambiguous names.
7. **Async with no notice**: window.open's window isn't in window.list until a moment later; window.opened rules fire later; nothing says "pending".
8. **One word, several meanings**: pin (feed post / wm window / dock pin), tasks (task board vs "Running windows" view), dock vs taskbar, music vs media, "just for me" (= Alex's own look, not the agent's).
9. **Receipts are uneven and internal**: window.move/focus/verb runs print no receipt; window.close says "forget … out of every view"; theme receipts show ids and microsecond timestamps; word-set truncates the echo mid-word.
10. **No refusal memory, no safe media pause**: refusals vanish (no `refusals`/`why`); media.play is a toggle, so an agent that can't hear can start music by mistake.

Also notable: `window.open help` refused with a list that contains "help"; `look` and `window.list` disagree on Lines' position; `window.list` is not "front first"; I am "claude", "agent for Alex" and dk36 depending on the answer.

## What `help` should say (draft first screen)

```
You are claude, an agent for Alex. You act with Alex's rights here, so what you change, Alex changes.
A line: word, then the thing (a name or id), then key=value.   window.move Feed to=left
Quote text with spaces: post "hello".  ; joins lines.
Every change prints a receipt [r812]. undo = your latest; undo r812 = that one; receipt r812 says what it was.
Find things: window.list · rows <kind> · find kind=<kind> name=<name> · recent
Ask about anything: help <topic>   windows · feed · tasks · theme · dock · rules · words · people · music · undo
Not sure? help check · something refused? refusals
```

## What `help <topic>` should do

- Match topics first, then words, then fuzzy mentions — and say which it matched. `help words` must reach the "Making your own words" topic, not the full list (that's `help all`).
- A topic page = 2–4 sentences of how-to with one runnable example per common task, then the 6–8 main words, then "more:" — exactly like the current `help windows` / `help theme`, which are good.
- `help window` and `help windows` should both show the Windows topic, and that page should say plainly when to use window.* vs wm.*, and that wm is in shadow (and what that means).
- `help pin` should list every meaning of pin (feed pin, dock pin, wm.pin). Generally: when a word name is a prefix or suffix of others (pin / wm.pin / kind=pin), `help <word>` should mention the siblings.
- `help <kind>` (e.g. `help note`, `help button`) should say what words make, change and list that kind.
- Extra words after a topic (`help pin windows`) shouldn't be silently ignored.

## Words I expected and didn't find

`note` (make a note), `recent` / `changes` (world-wide history), `who` (people+agents+modules in one), `press` / `click` (run a button's does=), `media.pause` / `media.resume` (idempotent), `refusals` / `why`, `receipt r<n>` (look up a receipt), `redo`, `alias`, `window.tile` / `tile`, `window.size`, `unpin` (for feed pins — undo is the only way), `me` / `whoami`.

## Naming: rename or merge

- Pick one separator: `task-add` vs `theme.use`. Suggest dots for every family: `task.add`, `task.done`, `word.set`, `word.rename`, `look.view`, `personal.view`.
- Merge `catch-up` and `board.catch-up` (or say how they differ); merge `stop` and `off` (help already says "the same as off").
- `window.*` and `wm.*`: one family for "a window", with wm as its engine; at least make wm accept window ids.
- Rename view `tasks` → `running` (it shows Windows' running task buttons), so `tasks` can mean the task board.
- `bar=taskbar` → `bar=dock` (or accept both); the UI calls it the dock.
- `pin` (feed) → `feed.pin`; dock pin kind → `kind=shortcut` or `kind=dock-pin`.
- `media.play` (toggle) → `media.toggle`, and add real `media.play` / `media.pause`.
- `role` → `role.set` (or split into a see word `roles` and the do word), since the bare word reads like a question.
- `happening-soon` / `needs-answers` / `new` / `top-this-week` — all share the same help; prefix them `feed.new`, `feed.top-this-week` and give each its own line.
- Show one name for me everywhere: "claude (agent for Alex)".
