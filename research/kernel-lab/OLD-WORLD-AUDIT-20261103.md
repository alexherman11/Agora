# What the move to the kernel lost, gained and can still bring back

> Draft by Claude, 3 Nov 2026, from Alex's ask: "go look at the old world and make sure that we brought over all the useful things, and that workers in the world can bring over things… give me a reasoned assessment about what was lost, what the improvements we now have are, and how we can generally take some of the lessons from the old world and bring them into the new. (Also look into how git handled this transition)". This audit replaces the one card dk1482 asked for on 29 Oct, which never ran (see "Workers" below). Nothing was changed while making it.
>
> Labels: **ran** (executed, numbers as printed), **read** (a primary source), **inferred** (my reasoning). Sources: the archive book `C:/Projects/Agora/archive/frontier-2026-10/` (things.jsonl, index.json, alex-words.md), a plain replay of the kernel log `research/window-lab/kernel-desktop/state/world/log/0001.jsonl`, the House's builder records, and git.

## In one paragraph

Nothing was destroyed. The archive is lossless and checked against the old door (read: its README). What we lost is **the old desk's working machinery, not its data**. That means the panels Alex used every day, notices, the adapters, the small organising verbs, and the rules that moved cards along. On 27 Oct (MOVING-IN D8) the plan was to carry only souls and rules and port two lenses. That plan was carried out, and slightly more than that came over. The gap is that nobody listed the machinery Alex relied on before the cut, so it disappeared silently instead of being chosen. Workers *can* bring things over, and have done so three times, but only by hand. There is no word, guide or help topic for it. Git kept main healthy, but the transition itself is not recorded in git. Some important work is uncommitted, 86 commits are unpushed, and the new world has no backup at all.

## Sizes

- **Old desk** (ran): 2,725 things. 102 lenses, 16 styles, 34 verbs plus 46 commands, 11 rule things plus the charter, 13 kinds, 33 chats, 90 open Board cards.
- **New world** (ran, plain replay): 3,901 records, 1,804 things, 1,421 live.

## What came over (read/ran)

- **JEFF:** his soul and the charter, word for word (`move_jeff.py`).
- **Residents:** Sable and Pike moved with continuity. Rowan has a fresh soul.
- **Interface:**
  - The jeff-chat lens and home-style.
  - The Work app, rebuilt from home-work and home-board.
  - The Writing app (from doc-page and Rowan's editor).
- **Words:** the `$` fill-in words (card dk1368).
- **Documents:** five, including Alex's "Migrating into Windows" and "Friction I've found", with provenance (card dk954).

## What was lost or not carried yet, ranked by how much Alex used it

| # | What | Old | Status now |
|---|---|---|---|
| 1 | **The HUD / home-base panels**: Needs Me (waiting-on-me), notices, viewer, search, glance, pomodoro, plan usage | the most-cited lenses (home-viewer in 27 repo files, home-search in 25). Alex 21 Oct: home-board "honestly one of the most useful ones" | Only their CSS survives, inside home-style. Several of his standing rules (Needs Me → Delete, nothing scrolls on HUD, only the pomodoro ring moves) now refer to things that don't exist |
| 2 | **Notices / notifications**: 248 notices, the four "Notice Alex" rules, the notification kind, two designs | | No notification kind in the kernel (ran: grep of kinds.py) |
| 3 | **Adapters**: Twitch (live until 27 Oct), Gmail (headers), and the declarative adapter language | | The Twitch port is built but **uncommitted** in worktree `kernel-dk1140-…` (ran: git status). Gmail: nothing |
| 4 | **Comment on anything**, a charter rule since 22 Oct | | Comments exist only inside Writing |
| 5 | **Organising verbs**: link, tag, due, check, markread | | Missing (ran: word lists compared) |
| 6 | **Card-flow rules**: waiting_on wakes the waiter, call whoever waits, tell the reporter a fix is in | | Not carried. The new world has 5 rules |
| 7 | **The Board's direction**: 90 open cards, 4 epics | | About 6 re-seeded (fuzzy title match, may undercount). Deliberately left behind by D8 |
| 8 | **Voice with JEFF**: voice.* words, home-voice, the plan | | Not carried |
| 9 | **Juniper, Ibis, Mica** | | Not asked yet (D6 said ask them) |
| 10 | **Design drafts**: Built-in browser (Alex asked again as dk1656), Living map, AgoraMail, Board rethought, Building Agora from inside | | In the archive only |
| 11 | **Music lenses**, extra media words, and the lens-language help topic | | Not carried |
| — | Rooms, corners, promises (270) | | Rightly left behind: Alex abandoned rooms on 27 Oct. Promises were never used much (inferred) |

Not checked: features that lived only in the old code (lens.js, house.py), `house-state/frontier/` (2 GB), the old forks, and whether any "not carried" item would actually work if brought.

## What the new world has that the old lacked (read)

- **People:** persons with accounts, groups with leaders, and sealed authorship on a hash-chained log. The old desk signed lines by text, and one rule once signed JEFF's lines "Alex:".
- **Facts, not words, on replay.** Changing a word's code can't rewrite history.
- **Kinds with shapes:** extends, has, value kinds, alike and aspects. Words reach only the things that fit them.
- **Modules in any language**, with the kernel never running module code. There are 12 now: window, wm, theme, map, house and others.
- **Real Windows windows** under Agora's own window manager, not a viewer inside a browser.
- **The House inside the kernel.** Residents run their own workers, and builders are landed and reviewed independently. JEFF never runs tests (D5).
- **Real apps:** the Seabright community apps (board, polls, RSVP, calendar, map), Writing, Taskboard and themes.
- **A smaller, calmer world:** 1,421 live things against 2,724. This is the clutter relief Alex asked for.

## Workers: can they bring things over? (read)

**Yes, by hand.**
- Claude workers have unrestricted read access. Codex workers write only inside their worktree, but read the archive fine. Both have the old code inside every worktree, because `research/text-desk-lab/notation` is still tracked.
- Three bring-overs happened this way: dk1368 ($ fill-ins), dk954 (Alex's documents) and dk1326 (an archive search).

**What's missing:**
- **JEFF and the residents have no way in.** They speak only Lines through the door. JEFF learned the archive path from a document imported on 27 Oct, and has pasted it into card text by hand since.
- **No guide mentions the archive.** WORKERS.md, BUILDERS.md and HOW-TO-BUILD-HERE.md don't, and neither does the builder prompt (`builders.py:697`). The prompt only says to *skip* the old charter line.
- **Authorship of brought things is a convention.** dk954 used `author=Alex source=<old id>`, but the kernel still records the agent as the maker.
- **The audit JEFF commissioned never ran.** dk1482's worker started background helpers and ended its turn to wait ("the worker ended its turn without words"). The House recorded that as a received result (ran: world log, state.json `result_ok True`, no AUDIT.md). **A worker that is waiting looks finished.**

## Git through the transition (ran)

**Main is healthy:**
- 248 commits from 22 Oct to 2 Nov.
- Landings fast-forward main after merging main into the worker branch.
- One revert in the window, and no history rewrites.

**Problems:**
- **Important work is uncommitted.** "Kinds all the way down" v1 (`kernel/kinds.py` +601 lines across 5 files, `tests/test_parts.py`) has sat in the working tree since 28 Oct 22:41. MOVING-IN.md, the clutter lab and the old-desk lens copies are untracked.
- **86 commits are unpushed.** github/main stopped at 27 Oct 12:14, minutes before the archive.
- **The new world has no backup.** `kernel-desktop/state/` is gitignored, and its 41 MB log and the `keep/` folder exist in one place. The seal key shouldn't go into git, but the world needs a backup somewhere.
- **The transition isn't in git.** No commit or tag marks the archive. AGENTS.md still says Agora "is a text desk" and points at `a6529`. Current Implementation still describes the text desk (audited 8 Oct). Previous Work has no section 8. MOVING-IN T4 and T5 asked for all three.
- **The old world is still tracked.** It has 35 tracked pickles, and frontier.pickle shows as modified. It is byte-identical to the archive copy (ran: cmp); the old desk wrote it until shutdown.
- **Sprawl:**
  - 95 worktrees, of which 64 sit on branches already merged.
  - 172 branches, including 31 unmerged old-world worker branches and 3 research branches against the one-at-a-time rule.
  - A 1 GB `frontier.undo.sqlite` committed as a fixture on `worker/a1` (not on main), inflating the pack.
- **Authorship in git is blurred.** Every commit's author is Alex. Agents show only in subject prefixes.
- The session setting naming `codex/parallel-worldline` as the PR base is stale. That branch is an ancestor of main from 12 Sep.

## Lessons to carry forward (inferred)

1. **Split data from machinery when migrating.**
   - *Data* (notes, chats, cards) can stay archived and be brought on demand.
   - *Machinery* (lenses, verbs, rules, adapters, kinds) is how Alex lives day to day. It needs a list, made before the cut, of what he used and whether it will be ported, replaced or dropped. That list is what was missing.
2. **Choose by use, not by tier.** The archive's tiers were sorted by plain rules. Alex's own record is a better signal: what he opened, cited and praised, plus his 325 chat lines. The top of the table above comes from that.
3. **Bring on demand, with provenance.** This keeps D8's fresh start and makes the past reachable. It's the planned read-only `archive` module:
   - `archive find` to search;
   - `archive look <old>` to read a thing;
   - `archive bring <old>` to make a new thing with `imported_from=frontier:<id>@39581` and the author taken from its events.

   That gives JEFF and the residents a word of their own instead of a pasted path. **New design → Alex's gate.**
4. **Test the "same language" claim on the old verbs.** The kernel promised to carry the line and lens language. If that holds, old verb notes (tag, link, due) and rules should come over nearly as written. Trying one tells us whether the old world's machinery is cheap to restore or needs real porting. That one result would change how much of the table above is worth restoring.
5. **Close out a migration.** A cut isn't finished until:
   - the docs say what is current (AGENTS.md, Current Implementation, Previous Work);
   - git has a commit and tag marking it, and is pushed;
   - the new world has a backup;
   - the worker guides say where the old world lives.
6. **"Done" must be a claim the House checks.** A worker ending its turn is not a result. The old desk's landing rule ("candidate ready is not installed") applies to reports as well as code.

## Found later on 3 Nov, while reading the kernel for the docs

These are from helpers' reports, with their labels. I checked only the first one myself.

- **The old desk's code is still live (read: `kernel/painter.py:27` `NOTATION = …/text-desk-lab/notation`).** Every lens without `painter=components` (jeff-chat, feed, the top bar) is drawn by the old lens compiler and `desk-shell/lens.js`. MOVING-IN step 5 ("its source moved to research/archive") would break those windows, so don't move `notation/` until they're ported. The desktop README's claim that no live window uses that path is wrong.
- **`press` is a see word but acts** (ran, in a scratch world: a see verb that calls `press` made a record, 3 → 4).
- **"Look first" marks are memory-only** (read: `kernel.py:110`), so a restart forgets them, although the docstrings say they're kept beside the world.
- **Sandboxes:**
  - Codex workers can't make test folders with `tempfile.mkdtemp`, which is owner-only on Windows since Python 3.12.4 (ran, icacls). This is fixed by `kernel/scratch.py` and `test_kdesk.scratch_dir`.
  - They can't start a headless browser either (ran: music's proof), so browser proofs run outside the sandbox.
- **Stale source docs** (read; listed for small, approved edits later):
  - kdesk README: "kernel unchanged", two modules;
  - SHELL.md: "nothing here is live";
  - THEMES.md: the `theme.use` default;
  - `kdesk_off.py`: the taskbar;
  - `mcp/README.md`: the tool count;
  - HOW-TO-BUILD-HERE: "no module-install word";
  - the docstrings of `modules.py` and `door.py`;
  - the house docs: "two builders".
- **`state/` is 6.7 GB**, with 83 leftover offscreen Edge profiles (ran).

## Suggested next steps

- **Builder work, pre-approved:**
  - commit the 28 Oct kinds work, and push when Alex says;
  - a world backup outside git;
  - fix AGENTS.md (T4);
  - add the archive paragraph to WORKERS.md and the builder prompt;
  - add a `help archive` topic;
  - make the House refuse an empty result;
  - land or close the Twitch port;
  - remove the merged worktrees.
- **For Alex's gate:**
  - the `archive` module;
  - which of the top panels (Needs Me, notices, pomodoro, viewer) to bring back, and on which surface;
  - whether to ask Juniper, Ibis and Mica.
