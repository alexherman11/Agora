# A terminal that teaches itself: the naive-agent friction study

*Claude, 26 Oct 2026, for the epic dk748 on the live task board (stories dk749 to dk753). Alex's ask, in his words: "the help right now is terrible. General help should not list every word, it should give the most useful ones and explain how the terminal works. Help ___ should give help for that thing. Help window(s) for example should tell me what words work on windows. It should be intuitive to use."*

## What was done

1. **A hidden sandbox** (`src/desktop/kernel-desktop/sandbox.py`). A copy of the live desktop world at `state/world-claude-terminal` (git-ignored), on door 8830, with every module rewritten to `--headless` before it starts, and model and summarize off. **Ran**: process check showed window, guy, system, media and wm all `--headless`; nothing appeared on Alex's screen. `sandbox.py fresh | run | stop`.
2. **A fresh Opus 5.5 agent** with no documentation, only a token-free `say.py` that sends lines exactly as the Lines window does (`look help rows holds status window.list` to `/see`, the rest to `/do`), acting as `claude` (agent for Alex). Twenty plain tasks, from "find out what this terminal is" to "make open mean the same as whatever opens a window". It logged every friction as it went. Its log and every line it typed: [evidence/naive-agent-log-1.md](evidence/naive-agent-log-1.md), [evidence/naive-agent-transcript-1.jsonl](evidence/naive-agent-transcript-1.jsonl).
3. **The help work** Alex asked for, built and tested (below).
4. **A second fresh agent**, same prompt and tasks, on a fresh sandbox copy with the new help: [evidence/naive-agent-log-2.md](evidence/naive-agent-log-2.md).
5. **A design for the language itself**, which is a new design and so goes to Alex first: [lines-plainly.html](lines-plainly.html) (published as an artifact with his choices saved on it).

## First agent, before (ran)

12 done, 7 partly, 1 failed; about 175 lines typed (its own count). Its top ten, ranked by cost, in short:

1. Names don't work where ids are expected (`window.move Lines`, `window.close Help`, `word-set task-add`), and the refusal said "needs a thing" when it had given one. `theme.use`, `pane.close` and `guy.hop` do take names.
2. No reading for "what changed recently, by whom". `catch-up` printed only "since 1970-01-01"; `history` needs a thing; `rows any sort=changed` silently matched 0; `via_actor=claude` (as `history` prints it) filters to 0.
3. Rule side effects are invisible, and `undo` takes them back first: after `task-done`, the rule "Task board Done announcement" posted; the next `undo` removed that post ("put back 5 facts"), so undo looked broken.
4. "ok" for acts that did nothing: `wm.arrange` "layout re-solved" with the window manager in shadow mode and 0 windows; `media.play` "ok" with nothing playing; `make kind=note` and `bar=dock` accepted without a word.
5. `help` was a flat 163-line dump, no orientation, `post` ×7 and `reply` ×6 (group copies with their own limits), and no topic help.
6. Help contradicted itself: `task-add`'s example said `task.add` (refused); `window.open` said owner-only while its entry said "who may: anyone"; `takes` showed optional settings as required.
7. Overlapping families with no guidance: `window.*` / `wm.*` / `pane.*`; `catch-up` / `board.catch-up`; `task-add` / `summarize.add`; `rename` / `word-rename` / `word-set aliases=`; `rule kind=` vs `make kind=rule of_kind=`.
8. Window geometry inconsistent: `window.list` shows position, never size; `look` shows at/size for some windows and not others.
9. **A bug**: `task-add` without `who=` stored `who=$who`, `when=$when`, `text=$text` on the card. (My own epic cards on the live board had `when=$when`; fixed with `set`, r1186 to r1191.)
10. Identity muddled: "claude" in history, "agent for Alex" in the feed, `dk36` in rows, an agent with an empty name; `theme.use … for=me` changed Alex's theme.

It liked: `help help`'s metadata line (takes, who may, undo, from); refusals that say what to do (`Feed is open already … new=yes opens another`; a verb's "stopped at step …; nothing was done"); the theme family taking names; `verb` working first try.

## What we stand on

The old desk already had this (**read**, Current Implementation, "Help and ids", a1595): help was notes in a Help binder (f1702), a note tagged `topic` listed among `topics:`, changing help was `replace` with no restart, and `helpnotes.check` found help untrue to the code. The new kernel kept only the dictionary entry's `help` field and a code-written listing, so the binder's lesson was lost in the move. Topics below are that idea again, on the new kernel's one substrate (a topic is a thing like any other, edited by `set`), and `help check` is `helpnotes.check`'s smaller cousin.

## What was built (help, tooling and tests: pre-approved)

Kernel source (`src/agora/kernel/`):

- **`helping.py` (new)**. `help` alone: who you are, how a line works, the most useful words, the topics; `help all` is the old list with each word once. `help <anything>`: a word, then a topic, a module (its namespace), a kind (`help taskboard-task`), one thing by id, else the words whose names or help mention it. `help check` lists help that may mislead, with the line that fixes it. Each page ends with its fix line (`word-set <word> help=…`, `set <topic> text=…`) for whoever may, or `ask <id> text=…` for others. The rows of bare `help` stay the whole dictionary, because the Help window reads them.
- **Topics are world things**: `make kind=topic name=windows aliases="window screen" words="window.list window.open … window.* wm.*" text="…"`. Plurals are free; words listed in order, `*` families folded into one "more:" line; `\n` in text is a new line. A topic named `start` is the first screen. Twelve in [topics.lines](topics.lines), installed by [install_topics.py](install_topics.py) only where missing, so world edits always win.
- **`kernel.py`**: an unknown word's refusal says `did you mean …?` or `help <x> shows the words for it`; a word's name stands for its entry where a thing is expected (`word-set window.open help=…`); "needs a thing" now says which id to use, as a line (`window.move takes an id, not a name: Lines is dk74 (a window). Say: window.move dk74 to=left`); a verb note leaves out `key=$name` that nobody gave (handles from `as=` and `$today`/`$by`/`$carried` still pass through), so `task-add` no longer stores `$who` and a `set` verb no longer erases facts it was not given.
- **`dictionary.py`**: `word-set` echoes what changed, with what it was (aliases).
- **`words.py`**: `help_` delegates to `helping.py`; `rows` says why a filter matched nothing, names buttons by label, and spells plurals (`7 lenses`, not `lenss`).
- **Help texts** found wrong, fixed as ordinary steward lines in [help-fixes.lines](help-fixes.lines): task-add, window.open, window.close, rule, verb, look, media.play, help, word-set.

Tests (**ran**): `src/agora/tests` printed `108 passed, 30 subtests passed in 110.20s` at this point (113 after the later fixes, below), including the new [test_help_topics.py](../tests/test_help_topics.py) (6 tests, 7 later: short first screen with whole rows; topics by name, alias and plural, fixed with set; no dead ends; word names in word-set with the fix line shown only to stewards; verbs leave out unset settings without erasing; help check). Two older assertions that bare `help` lists every word moved to `help all` (test_skeleton, test_missing_words), as did the waits in `desktop/kernel-desktop/test_kdesk.py` and `agora/theme/proof.py`. **Not changed**: `agora/painter/tweaks/run.py:37` also waits for `summarize.save` in bare `help`; it is in the painter folder another session is editing, so it needs `help all` from them.

Not verified at this point: the desktop's hidden suite (run later, below). The live desktop (8810) still runs the old kernel until it restarts; the topics and help fixes go in after that with `install_topics.py` and `install_topics.py --file help-fixes.lines --always` (word names in word-set need the new kernel).

## Second agent, after (ran)

Same prompt, same 20 tasks, a fresh sandbox copy with the new kernel, the twelve topics and the help fixes. **15 done, 5 partly, 0 failed** (first agent: 12, 7, 1); 174 lines sent (first: 187). Lines per task, as each agent counted them:

| Task | Before | After |
|---|---|---|
| 1 what is this terminal | 13, partly | 3, done |
| 5 move a window left | 9 (4 wasted on names) | 2 |
| 6 close Help | 6 | 1 |
| 10 who is here | 8, partly | 4, done |
| 12 a dock button for the feed | 13 | 1 |
| 13 a word "tidy" | 6 | 2 |
| 14 guy says hi on open | 11, partly | 1, done (verified) |
| 17 fix a word's help | 5 | 2 |
| 18 tile the windows | ~30, partly | 12, partly |
| 19 find Lines by name | 6, partly | 2, done |
| 20 "open" means window.open | 8 | 1 |

Worse or no better: task 4 (note and pin, 13 → 21 lines: `pin` means three things), task 8 (5 → 12: `task-add "buy milk"` made a card with no title and said ok), task 11 (still no world-wide recent changes). The five partly done are exactly the language proposals: undo (9), recent changes (11), media pause (15), finding refusals (16), tiling (18).

Its top frictions now are no longer about help: plain `undo` took back a rule's post instead of its own act; "ok" when nothing or the wrong thing happened; rule side effects unmentioned; no `recent`; window.* and wm.* don't meet; names accepted in some words only. It called `help windows` and `help theme` "good", and asked that `help pin` list every meaning of pin.

**A bug of mine it found**: `window.open help` was refused. My first "a word's name stands for its entry" rule took `help` as the help entry. Fixed (only words whose first argument is a thing's id resolve a word name) and covered by the desktop's hidden suite (`window.open help new=yes`), which then passed 22 of 22. Also from its log, built after: `help words` opens the words topic; `look Lines` says which id, like the other words.

Final runs (**ran**): `src/agora/tests`: `113 passed, 30 subtests passed in 112.62s`; `src/desktop/kernel-desktop/test_kdesk.py`: `22 passed in 39.34s`.

## After going live (commit fbc25b03d)

The coordinator found two things once it was live: `help windows` listed `wm.changed`, a word the window manager stopped offering in a3d4a15fa; and a module re-offering its words never refreshed its entries (wm.focus and five others kept `undo=external` after the module changed them to `no`; fixed live with word-set). Built:
- `kernel.on_offer` refreshes a field (help, takes, undo, may) when the module itself wrote it last; a field a steward changed with word-set stays the steward's, with a notice. This refines SHAPE section 11's "after that the entry is the world's" to "a person's edit is the world's".
- The kernel remembers each running module's latest offer in memory only (not the world). Help leaves out words that module no longer offers; `help check` names them with `word-set <word> status=hidden` to retire one. Nothing is hidden or deleted on its own.

Ran: `src/agora/tests` `114 passed, 30 subtests passed`; `test_kdesk.py` `22 passed`.

## Alex's answers (27 Oct) and what was built

Read from the design page's store (**read**, `decisions`, seven documents). Yes: P1 names, P4 spelling, P5 readings, P7 make and press. Changed:
- **P2**, Alex: *"it shouldn't need to redeclare close = window.close. I think it should be intuitive enough to code just assuming the actions are usable, and if they conflict somehow it can be clarified."* Built with no declarations: a plain verb nothing else answers to (`close`, `open`, `done`) finds the dotted words ending in it (`window.close`, `task.done`), keeps those whose family or usage fits the kind of the thing named, runs the one that fits, and asks when two do (`close could mean window.close, pane.close, wm.close; say which`). `help close` lists them.
- **P3**, Alex: *"i like honest no ops, but i think undo should undo the whole action ... i want to keep it clean"*, unsure whether receipts should list what rules did. Built: a record a rule makes carries `caused_by` (the first act of the chain); `undo` takes back the act and every rule act it caused, in one record (`undoes_too`), and says so in one line (`undid r1436: task.done buy milk, and what 1 rule act did because of it`); plain `undo` never picks a rule's act. Receipts are not lengthened. Honest no-ops: `set` and `word.set` with nothing to change say so and record nothing; `media.pause`/`media.resume` (new) and `media.play` with nothing named press nothing and say so (`start=yes` presses anyway). `wm.arrange` in shadow mode is the window-manager session's to fix (passed on).
- **P6**, Alex: *"for=me should be optional ... every time the theme is changed it should be for me. I dont care to much about agent's history of changing my settings"*. Built: `theme.use <name>` is yours; `for=place` (stewards) changes the place's; `theme.use place` follows the place again. The Appearance lens's "use" button says `for=place`. Agent naming was dropped.

Built:
- **P1**: a word that takes a thing (its first argument `<id>`, or a verb whose usage names a kind) takes its name, title or label: the whole of its free words first (`done "buy milk"`), then the first word. The kind its usage names wins (`window.close Help` means the window); a name only other kinds have says so (`no window you can see is called Feed (called that: dk39, a lens, …)`); two of a name ask back with their ids. Topics, words, grants and board events are never what a name means.
- **P4**: a dotted name is the world's unless a module publishes that family (`window.*` is the window module's; `task.*` is free). A module's own words keep its namespace. Renamed in the world by [install_renames.py](install_renames.py): `task.*` (14), `word.set`, `word.rename`, `word.copy`, `component.action`, `component.health`, `file.read`, `file.result`, `personal.view`, `personal.style`; each old name stays an alias (and still answers through the entry's bound name), help texts naming old words are rewritten.
- **P5** ([readings.py](../kernel/readings.py)): `who`; `recent [by=<name|me>] [kind=] [since=r<n>] [limit=]` (who, which word, on which visible thing; never facts, never a sealed act's author, nothing that touched only hidden things); `history` alone is your own latest acts; `kinds`; `on <module>` (its off's grants come back).
- **P7**: `make` adds a note, never a refusal, for a kind nothing mentions yet and for settings the kind's other things never use or say otherwise (`no other button has bar=dock (they say taskbar)`); `press <button>` runs its `does=` as the presser.
- Also: a module's words list `(window is off)` in help when their module is off.

One script puts all of it in a running world, in order, every step an undoable line: [install_lines_plainly.py](install_lines_plainly.py) (renames, then topics refreshed where only the installer touched them, then help fixes, then the Appearance lens). **Ran** on a fresh copy of the live world: 95 changes, no refusals; a second run changed nothing and said so.

Tests (**ran**): [test_lines_plainly.py](../tests/test_lines_plainly.py) 7 tests (P4 families; P1 names, two of a name, wrong kind; P2 plain verbs; P5; P7; P3 undo with a rule's post). `src/agora/tests` `120 passed, 30 subtests passed` before the last test was added; `test_kdesk.py` `22 passed` (its media.play expectation changed to the honest no-op). Not run: `agora/theme/proof.py` (a browser proof; its steward calls now say `for=place`).

Known limits: a button or verb line that says a name resolves it when it runs, not when saved, so renaming the thing breaks that line (ids still bind). After undoing an act, undoing the act before it can still refuse "changed since" (an older kernel limit). `move Feed left` (a bare spot) is not read as `to=left`.

## Third agent, on the approved language (ran)

Same prompt and tasks, fresh sandbox copy with the language installed, the window module turned on in the sandbox only (it is off in the live world). **14 done, 6 partly, 0 failed**, about 210 lines ([log](evidence/naive-agent-log-3.md), [lines](evidence/naive-agent-transcript-3.jsonl)). Not better on the count than the second run (15, 5, 0): it found bugs in the new code, now fixed and tested:

- `close Help`, the first screen's own example, refused: "Help" also named a button, and the plain verb gave up when a name had two kinds. Now it takes the family word that fits one of them.
- `tidy <a> <b>` in a verb's help made `<a>` a kind ("no a you can see is called Feed"). A usage word is a kind only when things of that kind exist.
- `$2` by name failed inside a verb: neither verb path resolved names in its steps. Both do now (one `name_target` for the step and both verb paths).
- A verb whose module step had already acted said "nothing was done". It now says nothing was recorded, and which module may already have acted on the screen.
- `press` always timed out: it ran its line while holding the kernel's lock, so a module word in it could not answer. `press` now becomes its button's line before the step runs.
- `task.add "buy milk"` made a card with no title. A verb whose steps never use `$1`/`$*` now fills its first unsupplied setting with the free words.
- A second `undo` refused "changed since": a later change that was itself undone now counts as settled.
- `make`'s notes fired on a module's own lines (window.open's make); now only on what a person or agent wrote.

Checked in the sandbox by hand (**ran**): `close Help` closed the window and `undo` reopened it; `tidy Appearance Lines` moved both; `press MyFeed` opened the feed through the window module; `task.add "buy milk"` titled the card; `done "buy milk"`, then two undos took back the done and the add. Tests (**ran**): `src/agora/tests` `122 passed, 30 subtests passed`; `test_kdesk.py` `22 passed`; then `test_lines_plainly.py` and `test_help_topics.py` `16 passed` after the last change. Still open from its log: `open feed to=right` opens a second Feed rather than moving the first (window module); `wm.arrange` says it re-arranged when the window manager is off (wm session); refusals all start "refused:" whatever their cause (a timeout, an ambiguity, a permission); `recent` hides acts on things since forgotten (a closed window).

## What needed Alex: the language

Seven proposals, each with today/proposed lines, how it works, and what would change my mind: [lines-plainly.html](lines-plainly.html). In one line each: names work where ids go (P1); a few plain verbs that ask the thing's kind what they mean (P2); receipts in the user's words, rule side effects named, honest no-ops (P3); one spelling for families, old names kept as aliases (P4); `who`, `recent`, `kinds`, `on <module>` (P5); agents named everywhere, "me" says whose (P6); `make` warns about unknown kinds, `press <button>` from Lines (P7).

## Findings for other owners

- **wm** (agora-wm session): `wm.arrange` answers "layout re-solved" in shadow mode with 0 windows; `wm.mode live` refuses with a developer instruction ("coordinator must start with --allow-live"); wm.* help has no usage lines. `wm.windows` shows 0 while `window.list` shows 11.
- **media**: `media.play` is a toggle that says ok with nothing playing; there is no pause.
- **board**: `catch-up` with no marker prints "since 1970-01-01" and nothing; `1 threads`; 15 board words have no usage line (`help check`).
- **window**: `window.list` shows no sizes; a new window opened exactly over another; `window.list` right after `window.open` did not yet show it.
- **status guy** prints a raw Python dict.

## A builder couldn't find the active Seabright work (Claude, 29 Oct; all ran through kd_say.py as agent for Alex)

Alex asked me (the kinds session) to look at the Seabright board work. It took about ten commands and Alex pointing me to Shop talk. JEFF then posted where it lives (dk1517): the card dk1498 and its pieces. What went wrong, each as the world answered:
- **`find seabright`** answered "nothing here is a seabright": `find` is `rows`, so the word is read as a kind. Nothing searches titles. **`search Seabright`** resolves Seabright as the map. JEFF's card dk1322 (worker dk1516) is fixing both.
- **`rows said in=dk829`** refused: "no thing called dk829 here", although `look dk829` shows Shop talk. `in=` wants a group, and a chat isn't one, so the refusal says something false. It should say that `in=` takes a group, and that a chat's lines are `rows said chat=dk829`.
- **`rows said chat=dk829 last=3`** answered "none you can see has chat=dk829 and last=3": `last=` is read as an aspect to match, not a count. There is no word for "the last lines of a chat", and **`look <chat>`** shows the chat's own facts, not its lines.
- **`rows card`**: the Board's cards are `taskboard-task`. Nothing says what the Board calls a card. With kinds all the way down, `card` could be a synonym (`aliases=`) of `taskboard-task`.
- **Where work lives:** I looked in git, the worktrees, the Claude Code sessions and the repository's board folder first. The work was on the live Board, with House workers whose branches weren't merged yet. Nothing in the repository points a builder at the live Board's open cards for an area.
- **My own mistakes:** I cut my own search short (`grep … | head -30` stopped at the old task board's rows, before dk1498), and I guessed `card` for the kind.

**Missing words:**
- a search over names, titles and text (dk1322);
- the last lines of a chat;
- `in=` refusing honestly for a non-group;
- a way from the repository to the live Board's open cards for an area.
