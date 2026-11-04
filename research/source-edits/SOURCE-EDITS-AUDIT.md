# Why source keeps changing, and how to make it go down

*Claude, 4 Nov 2026, from Alex's ask: "do an in depth audit of the recent source changes, and do a long and hard think about
how some of them could have been avoided … I want to see a codebase where source changes are going down over time."
Research note, mine; the drafts at the end are for Alex to accept, change or refuse. Evidence by area:
[[SOURCE-AUDIT-KERNEL]], [[SOURCE-AUDIT-HOST]], [[SOURCE-AUDIT-HOUSE]], [[SOURCE-AUDIT-APPS]] (four read-only helpers read
every non-merge diff since 26 Oct; I spot-checked the headline claims).*

## 1. What the numbers say

**Ran** (git log, non-merge commits touching live-system source: the kernel, modules, painter, the desktop host, the WM, and
before 27 Oct the old desk):

| week from | source commits | all commits | share |
|---|---|---|---|
| 5 Oct | 30 | 42 | 71% |
| 12 Oct | 129 | 211 | 61% |
| 19 Oct | 124 | 271 | 46% |
| 26 Oct | 84 | 105 | 80% |
| 2 Nov (3 days) | 15 | 18 | 83% |

The raw count falls only because less work happened. The share of work that is a source edit has risen since the move to the
kernel.

**Ran** (kernel): 40 built-in words on 24 Oct → 75 now, none retired; about 19 of the 35 new ones serve one app (task.* ×6,
chat ×3, files ×4, painter ×4, paint-clear, turn). Kernel source 13 files / 3,756 lines → 25 files / 8,969 lines. The kernel
now contains the literal `"JEFF"` (card_signals.py:35, 52), document-library kinds, chat's `said`, the board's posts and likes,
and the task board's lanes.

**Read** (all four areas, the helpers' classification, my spot checks): roughly 150 commits. About a third were legitimate:
OS and outside-service seams, bug fixes inside general mechanisms, and general words. About half were avoidable in whole or
part. Only a minority named the missing world word, in at least 12 different places, and none of the named words has been
built since. The agent-invite word was named three times while three bespoke resident movers shipped.

**Read: some universal edits clearly paid off.**
- `visibility_of` / `within=` is reused by seven things.
- Word shapes moved board.py's checks into the world ("word-set board.rsvp needs=… without editing this file").
- The refusals log found four bugs on its first day.
- `lead` made card authority a world opt-in.
- Bars as components made the bars world lenses.
- `shell-settings` let the JEFF button move from the archived desk to `window.open jeff-chat` with one `set`.

The approach works when it is used. It mostly isn't.

## 2. Why: four layers

### Layer 1. The world lacks general words, so the code fills in
Ranked by how many edits each would have absorbed, across all four audits (counts overlap; imagined design, counted from read
diffs):

1. **Settings things read at each use.**
   - What is hard-coded today: models and reasoning, max turns, timeouts, caps, review checks, tool lists, the brief and every
     wake or notice text, the Twitch channel, game exe lists, dock apps, sizes, poll rates, default scopes.
   - The pattern is proven (shell-settings, wm-settings, `compact_at`, `charter=`). It only needs to be the rule.
   - Cheapest, and ~20+ edits.
2. **The world is master for app content, and installing is a world act.**
   - Today `painter/install.py upsert` overwrites any lens or component field that differs from the repo file.
   - Taskboard lens text is generated in Python, and `kdesk.py` seeds people, chats, pins and Twitch at every start.
   - So a one-line lens change is a source edit by construction, and residents, who don't code, can't change their own apps.
   - Largest: ~19 app commits, 11 host commits, 7 House onboarding commits.
3. **Kind policy as world data.**
   - Who may make or set which aspects, aspects nobody may change, kinds only one word or module may make, and the
     not-nameable / not-fitted flags.
   - Kinds v1 gave kinds a shape vocabulary but no policy vocabulary. Policy keeps arriving as `if kind == "post"` /
     `"said"` / `"chat"` / `"file-settings"` in `make`, `set_` and `shown`, the kernel's two hottest functions.
   - With relational `may`/`sees` (SHAPE §15): ~16.
4. **Rules over a set, and notices.**
   - `each <reading> do=…`, a dedupe key, `$row.<aspect>`, `notify to= about=`, and a module hearing changes it doesn't own.
   - The old desk had query rules (`when <query> do comment <selection>`). The new `rule on=<word>` fires on one target, so
     card rules became a kernel word that names JEFF.
   - Polling (theme hash, `who`, wm titles) is the same gap seen from the host.
   - ~18.
5. **Richer readings.**
   - Joins, related counts and names, computed fields, `-prop:`/OR, ids shown as names.
   - board.py's docstring says it exists for what "the thin composition language cannot yet express".
   - Work moved from a 62-line world lens into House Python.
   - ~12.
6. **Agents' and workers' runs as world things.**
   - The House keeps its state in state.json, activity.jsonl and live.json, outside the world. So every rule about workers
     (who may tell, who is woken, what shows) has to be Python.
   - ~10.
7. **Shared seams in the host.**
   - "Covers the monitor" exists 6 times, there are 14 DevTools clients in the repo, the steward poll exists twice, the dock
     app list lives 2–3 times, and the bars exist twice (hand-written and components).
   - Each builder writes their own because nothing says one exists.
   - ~15 duplicate edits.
8. **Old-desk machinery that wasn't ported.**
   - The adapter runner ("No adapter needs a source file of its own", the old adapters.py) and query rules.
   - Every "bring X from the old desk" card turned world content into source:
     - Music: 297 lines of lens became JS.
     - Writing: 665 lines of lens became 826 lines of JS.
     - Twitch: a 17-line adapter note became a 164-line module.
     - Card rules: 7 world rules became a kernel word.

### Layer 2. The way work is asked for produces edits even when a word exists
- **Asks arrive as outcomes with names in them:**
  - "JEFF can unstick anything"
  - "four Claude and four Codex"
  - "Twitch chat for my channel"
  - "the JEFF button opens his chat"

  The fastest way to the outcome is to write it in literally, and nothing in a card, a brief or a review makes "the next one
  needs no source" part of done.
- **Even an explicit brief didn't hold.** dk1813 said "add a kernel word only if a rule cannot say it". The worker found that
  a rule couldn't, and built `task.signal` with JEFF inside, instead of the missing rule step.
- **The House's review runs tests; nothing asks whether a diff belongs in source.** House-landed worker commits carry a cut-off
  title as their whole message, so the log can't be audited.
- **The loop is fast.** Things are built in an evening, live that night, and fixed live by the same session. Each live symptom
  becomes a patch where it bit: pywebview was patched 9 times at 9 different moments, and the WM's placement policy was
  rewritten 4 times in a week.

### Layer 3. No memory and no meter
- **The controls Alex set up for this were lost in the move.**
  - On 7 Oct: every source edit logged as friction, in the world (f747).
  - On 14 Oct, after 19 source commits for ~14 asks: general words, not bespoke ones, with guidance at the top of the old
    desk's `lens.js`.

  Both lived in the old desk, which was archived on 27 Oct. Nothing replaced them in the kernel.
- **No file in the kernel, host or modules says what may be added to it.** The `kdesk.py` header still says the kernel is
  "unchanged".
- **Rough spots are scattered and never counted.** They sit in SHELL.md, ROUGH-SPOTS-WM, BAR-FAILURES, BOARD-ROUGH-SPOTS,
  KERNEL-WORDS-HANDOFF, CONTINUITY and more. Naming a missing word queues nothing, and no number goes up or down.

### Layer 4. My own share
- **On 27 Oct, fixing the bars:** I made a four-file fix so that full-screen checks wouldn't mistake the wallpaper window for
  a game. In the same message Alex had asked whether the wallpaper window should exist at all. I removed it the same day, and
  the fix now matters only in a fallback mode.
- **The JEFF button bridge:** `window.open url=` was added to reach the archived desk, and nothing uses it now.
- **Yesterday's offer:** I offered to let Alex pick his own photo as wallpaper by adding a value to `theme.edit`. That is the
  same pattern: a feature in source where a general word would have done it.

## 3. Do we need wallpaper.py?

**We need about a quarter of it.** The behaviour was right: the old full-screen wallpaper window covered the desktop icons,
kept a browser renderer running, and needed four files fixed so that full-screen checks would not mistake it for a game. The
shape is wrong. Read, by line counts in the file:

- **About 87 lines are an OS seam and should stay.** They save Alex's wallpaper, set a picture, restore it, and deal with
  Spotlight. As a word, this is `system.wallpaper` (see / set), and undo restores what was there before.
- **About 127 lines are a private copy of a hidden browser renderer.** It is the 14th in the repo, and it lacks the
  kill-on-exit guard added after 42 browsers leaked. `house.snap` already takes hidden pictures. It should become one general
  `render <thing> size=` word whose picture is a file thing in the world.
- **About 64 lines are glue.** The window module can't hear theme changes, so it asks for the theme's hash every 5 seconds,
  and it uses a window thing that no longer opens a window as an on/off flag.

With the two words, that glue is **one rule in the world**: on a change to Alex's theme, render the desktop page at screen size,
then `system.wallpaper set` that picture. `window.shell off` forgets the rule. Then "my own photo as the wallpaper" is
`system.wallpaper set <photo>`, with no source edit. The same goes for a wallpaper per time of day, or one shared by a
theme someone sends.

**What would change my mind:** wanting an animated or live wallpaper. That needs a window behind the icons again, and the static
picture becomes moot.

**I'd make this the pilot** for the approach below. It is small, contained, and Alex can see the difference: delete three
quarters of a file, and the next three wallpaper asks need no code.

## 4. What should change

### 4.1 Make the second objective explicit
Every task carries two objectives: what was asked, and leaving the system so that the next task like it needs no source edit.
When they conflict, the second may change the first:
- build the missing word first and do the ask in the world with it;
- or put a card for the word on the Board, do the ask as a marked bridge, and name that card as the bridge's removal;
- or say plainly to whoever asked that doing it right takes longer.

A bridge is allowed. A silent special case is not. This is the AGENTS.md directive drafted in §5.

### 4.2 Three edits go straight to source
1. A seam to the OS or an outside service.
2. A bug inside a general mechanism.
3. A general word itself.

Everything else (a preference, a name, a list, a lens, a prompt, an app's behaviour) belongs in the world. If the world can't
hold it yet, that is case 3 first.

### 4.3 Headers that say what each tier may hold
Short, the same for every file in a tier, pointing to one canonical text (§5). Four tiers:
- **The kernel:** universal only, never names a tenant.
- **The desktop host:** seams only; no preferences, no content, no seeding.
- **Modules:** a seam to the outside; what the world does with it lives in rules, lenses and a settings thing.
- **The painter:** a general vocabulary; never one app's handle.

App lenses and components shipped in the repo get their header after the decision in §4.6, because today their installers
overwrite the world.

### 4.4 A meter, so "going down" can be seen
- **Commit trailers on every commit that touches source:** `Source: word|fix|seam|bridge` and `Missing-word: <word or
  none>`. Git becomes the one friction log, and a weekly count by class comes from `git log`. The House should require them
  on the commits it lands and stop truncating worker commit messages.
- **A ratchet test in the kernel's tests.** It counts tenant names in `kernel/` (JEFF, Alex, said, chat, post, taskboard,
  document-, house, theme, paint-report, …) against a recorded number that may only go down. A new `if kind == "post"` then
  fails the tests instead of passing review.
- **Missing words become Board cards**, one per word, with each citing commit linked. Naming a word then queues it, and the
  card with the most citations is the next thing to build.

### 4.5 Build the missing words in an order that pays back fastest
1. **Settings for every module** (mechanical; removes the P class): house-settings with brief and notice templates,
   twitch-settings, gate exe lists, dock and app list as world things.
2. **`system.wallpaper` + `render`**, as the pilot (§3).
3. **Rules over a set, and notices** (`each`, dedupe, `notify`), then card_signals goes, and JEFF leaves the kernel.
4. **Kind policy and relational may/sees**, then the `if kind ==` branches go from `make` / `set_` / `shown`.
5. **Richer readings**, then board.py, work_overview and parts of the house shrink.
6. **Worker runs as world things**, then the House's Python authority and views go.
7. **The adapter runner**, ported from the old desk (Twitch, then Gmail).
8. **Shared host seams**: one screen-facts module, one renderer, one window lifecycle, one bar implementation.

Each step is measured by what it deletes, not by what it adds.

### 4.6 A decision only Alex can make: who is master for app content?
Today the repo is master and the world is a deployment target. The alternative: the world is master for lenses, components,
settings and rules. The repo keeps a seed for new worlds and an export of the live world (as the old desk's docs_sync did).
Installers make what is missing and never overwrite. The House can land a world change as well as a commit.

This is the biggest single source of edits (~37 commits). It is also a real design change with costs: review of component code,
drift between worlds, and what a fresh world starts from. So it goes through Alex's gate, as its own explanation, not inside
this note.

**What would change my mind:** evidence that Alex and the residents already edit lenses live and only workers go through the
repo. The apps helper could not check the world's log for that.

## 5. Drafts for Alex (nothing applied yet)

### 5.1 AGENTS.md: one new paragraph and one changed sentence

**New paragraph**, in "How we work", after "Every card has a level …":

> **Source edits go down over time (Alex, 4 Nov 2026).** Every task carries a second objective: when you finish, the next
> task like it should need no source edit. This may change what you do. Before touching source, look for the world way (a
> setting, rule, verb, kind, lens or component) and use it, even when code would be quicker. If there is none, name the
> general word that is missing. If it is small, build the word first, then do the task in the world with it. If it is big,
> put a card for the word on the Board, tell whoever asked, and either wait for it or do the task as a marked bridge whose
> comment and commit name that card. Only three things go straight into source: a seam to the OS or an outside service, a
> bug inside a general mechanism, and a general word itself. Never write a preference into source (a name, id, list, size,
> model, prompt or wording); put it in a settings thing the code reads each time. When bringing something over from another
> world, bring the machinery it needs before the feature. Commissioning a worker is no exception: write the card as "make X
> possible from the world, then do X".

**Changed sentence**, in Practical rules, "Source and world". Old:

> Log each source edit as a Rough spots note naming the world-level word that was missing.

New:

> Every commit that touches source ends with two lines, `Source: word|fix|seam|bridge` and `Missing-word: <the word, or
> none>`, and a missing word gets its own Board card (or a link on the one that exists).

### 5.2 File headers (one block per tier, at the top of each file's docstring or comment)

**Kernel**: every file in `research/kernel-lab/kernel/`:

```
EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. tests/test_kernel_tenants.py counts the names still here; the count only goes down.
```

**Desktop host**: kdesk.py, kd_*.py, shell_native.py, gaming_gate.py, wallpaper.py and the agora-wm files:

```
EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, one hidden renderer) instead of adding a copy.
```

**Modules**: the main file of each module (house.py, builders.py, theme_module.py, board.py, documents.py, map.py,
kd_twitch.py, kd_media.py, …):

```
EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session) and turns it into
world facts and words. What the world does with them (who is told, when, in what words, how it looks) belongs in rules,
lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models, counts, timeouts and
message text found in this file are debt: move them to settings when you touch them, and never add more.
```

**Painter**: painter.js, arrangement.py, handles.py, catalogue.py:

```
EDITING THE PAINTER (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The painter's vocabulary (formats, handles, scopes, parts) is shared by every app. Add to it only something any lens could
use, documented where lens authors read; never a handle, format or branch for one app. If one app needs it, the general
form is the change.
```

### 5.3 What applying them involves
- **Headers:** comments only, no behaviour change, about 50 files, in one commit with no `Source:` line (it changes no behaviour).
- **The ratchet test:** a new test plus a recorded count. It changes nothing live.
- **The trailers:** start with the next commit. The House's landing step needs a small change to require them and to stop
  truncating worker messages, which is itself a `Source: fix`.
- **§4.5 and §4.6** are new design work and go through Alex one at a time.
