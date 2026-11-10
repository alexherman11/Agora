# Words reach things that fit: the implementation

> Plan by Claude, 28 Oct 2026, for Alex. He asked: "what i really care about is the interoperability of different kinds, and making it so that verbs reach through kinds. Can we start with that and hold the graph and trail work? How much code is that, and also how strong of a grasp do you have on it." Labels: **ran** (with the number as printed), **read** (code I opened today), **imagined**. Nothing here is built. It supersedes round 5's "Kinds" section in `fresh-kinds-and-bonds.md`.
>
> **Built 28 Oct 2026** on Alex's "i think it looks good to build", with every decision below taken as recommended, `extends` included. Contracts as built: `src/agora/SHAPE.md` section 17, "Words reach things that fit". Differences from this plan:
> - The check sits in `guard`, which every site already calls. That's four callers, not six call sites.
> - The reading is `actions <thing>`, because `words` is a help topic.
> - The kernel now retires its own words it no longer runs (`around`, `nearby`, `preview`, `is`).
> - The House and the board keep exactly today's reach: their old checks, written as `needs`.
>
> **Second draft.** The first draft put each word on a kind (`on=<kind>`). A critic read it against the code and found three blockers, all confirmed (read):
> - **Check sites missed.** Module answers run kernel words without going through `step` (`_admit_lines`), and so do visibility tests (`predicate` calls `verb_note` directly).
> - **The migration would have broken lines that work today.** The kernel's own `task.next`… say `<task>`, a kind no thing has; the House accepts `taskboard-task` or `task`.
> - **"Reaches" isn't "works".** RSVP needs an event *and* a seat to claim.
>
> The design below moves the shape onto the word.

## What is true today (ran on a copy of the desk log, 660 things)

- **198 words:** 98 from modules, 78 from the kernel, 22 verb notes. No word says what it acts on.
- **`step` never checks the kind of a thing given by its id** (read).
- **The kernel guesses a kind only when a *name* stands for a thing,** from the first `<…>` in the word's help, plus a suffix rule (`<task>` finds `taskboard-task`).
- **Kinds are named as plain strings in:**
  - grants (`only=kind:window`, 2 of 33);
  - rules (`of_kind=`, 2 of 4);
  - lenses (`of tag:`, 34 selectors).
- **17 kind declarations; none says what its things need.**
- **Apps hand-roll their shapes in module code, invisible to every other word (read):**
  - The board's RSVP accepts "a post whose `post_kind` is event, or a thing of kind event" (`community/board/board.py`, line 195), then claims a seat.
  - The House accepts "kind `taskboard-task` or `task`" (`modules/house/builders.py`, line 161).

**Interoperability today is zero.** A task from another app can't be `done`. And a meeting can't be RSVP'd.

## The precedent (read)

- **The Entity Component System pattern in games:** a system declares the components it needs, and runs on every entity that has them.
- **Palantir's interface rules:** actions that run on any object type with the interface's shape.
- **Windows' `AppliesTo`:** shell verbs declare conditions on properties.
- **Lexicons (AT Protocol):** many communities share names, change them only additively, and give a breaking change a new name.

## The design

### 1. A shape is a list of needs
One grammar, used by kinds and words alike:

| Need | Means |
|---|---|
| `start` | has a non-empty `start` |
| `game=yes` | a marker: `game` is `yes` (someone set it on purpose) |
| `start\|starts` | has one of these spellings; the first is the name this shape uses |
| `kind\|post_kind=event` | `kind` or `post_kind` is `event`. This is the board's hand-written check, as data |
| `kind=taskboard-task\|task` | one of these values. This is the House's hand-written check, as data |

A thing's own kind is just the marker `kind=…`. No special rule is needed.

### 2. A kind is a named shape
```
make kind=kind name=event needs="title start|starts"
make kind=kind name=game  needs="run game=yes"
```
- **Kinds are for people and lenses:** `rows event`, a lens's `of tag:event`, `kinds <thing>`, and the grouping in `actions <thing>`. Nesting is just order: a kind needing more is the more specific.
- **Kinds are referred to by name, as a lexicon is:**
  - a kind may only widen (more spellings, more values);
  - a change that would narrow it is refused, naming the words and lenses that use it;
  - a breaking change gets a new name.

  This keeps kits and other worlds working. Binding to declaration ids would have made kinds local to one world (read: kits copy by name; `take` makes a second `event`).
- **A declaration with needs is made by a leader:** a steward for the place, a group's leader for the group. A word or lens resolves a kind's name in its own scope, upward to the place.
  - **Why** (ran, round 4): a member's declaration could change what the steward's words reach.

### 3. A word declares the shape it needs
```
verb task.done acts_on=… needs="kind=taskboard-task|task" steps="…"
{"word": "board.rsvp", "acts_on": "event", "needs": "seats", …}
word.set <entry> needs="…"          (a steward, or the entry's group leader)
```
- **A word's shape** is its `acts_on` kind's needs plus its own `needs`. It is what the word's code actually reads, so "reaches" means "works". The name is `acts_on` because `on` already has three meanings in the kernel (read).
- **A word with no shape reaches anything, as every word does today.** So the change itself alters nothing: shapes are added app by app, each with that app's tests.
- **One check, in one helper, at every place a word meets its thing (read):**
  - `step` (typed lines, presses, rules, the door, the painter, readings);
  - the start of `verb_note`, which also covers visibility tests;
  - the kernel calls inside `verb_note` and `_verb_with_modules`;
  - `_admit_lines` (module answers).

  That's six direct calls in all, replaced by one `call_word`. If the thing doesn't fit, the word refuses with what's missing, read as the actor sees the thing: "board.rsvp acts on an event with seats; Paint fence has no start".
- **Not covered yet:** things passed as settings (`about=`, `within=`). A word could later declare shapes for those too.

### 4. Plain words find the right implementation
For `done <thing>`, `close <thing>`, `open <thing>`:
1. family words whose shape the thing fits come first, in this order:
   - those naming the thing's own kind;
   - then the most needs;
   - then the nearest group;
2. words with no shape come after;
3. a tie asks which.

When no candidate has a shape, today's logic runs unchanged. This settles round 4's P2 question; it's Alex's rule to confirm.

Values differ between apps (`lane=Done` vs `status=closed`), so each app brings its own `done`. The plain word picks the one for the thing.

### 5. `actions <thing>`: what can I do with this?
A reading:
- every word the reader may say that reaches the thing, grouped by kind, most specific first, with each word's usage;
- then the lenses it fits.

It's the one answer for help and for every agent's "what can I do here?". Later it's the right-click menu, which is a painter change.

### 6. Spellings: read through, never written silently
- **Fitting, `rows <kind>` and a lens's `of tag:<kind>`** read a thing's other spelling under the kind's name, marked `(as starts)`.
- **`set` writes what it's told.** If the thing already says another spelling of that aspect, in a kind it fits (as the actor sees it), `set` refuses with the line to say instead: "Beach cleanup says starts; set … starts=…".

  **Why no silent rewrite** (read): grant `fields:` limits are checked before any rewrite, and undo checks the recorded name. A rewrite would also confirm an aspect the actor can't see, and two people can resolve it differently.

### 7. Classifying never adds power
- **Grants (`only=kind:`) and rules (`of_kind=`) keep matching a thing's own kind.** A module granted tasks can't reach a note that has gained a lane.
- **`mark <thing> <kind>`** sets a kind's markers, or refuses naming what's missing. It is a `set`, with `set`'s rights and its history.
- **Correction to round 5:** no outside-world word takes a thing today.
  - `window.launch` takes a path; `wm.*` takes a screen key (read).
  - The real gate is `press` on a button with `does=`.

  So `game` is a kind for people and lenses for now, not a guard on launching.

## What leaves (round 3 code, never live)
- promises;
- `is` and `is:` facts;
- `inside=`;
- aspect-entry aliases and the read-time fill in `shown()`;
- make's near-spelling hint.

## The graph, held
- **Leave the dictionary until the graph work resumes:**
  - `around`, `nearby` and `preview`, which carry round 5's privacy leaks;
  - the House's wake context.
- **`bonds.py` stays in the tree.** Its tests are skipped, with the reason.
- **`turn` stays live,** so records keep `because` and `work` for the trails later.

## The code (read; sizes are estimates)

| Where | What | Lines |
|---|---|---|
| `kernel/kinds.py` | Rewrite: the shape grammar, fitting with what's missing, kinds as named shapes with leader governance and the widen-only rule, `mark`, `words` | ~220 (from 362) |
| `kernel/kernel.py` | `call_word` and the check at its six sites; `plain_verb` ordering; `named`/`resolve_name` using shapes; `acts_on`/`needs` in `on_offer` and `_refresh_offer`; remove the `shown()` fill and the promise call | ~+120 / −70 |
| `kernel/words.py` | `verb … acts_on= needs=`; kind validation; `rows` and lens fill under a kind; `set`'s spelling refusal; `look` and `_make_notes` cleanup; `mark` and `words` entries | ~+100 / −90 |
| `kernel/dictionary.py`, `kernel/kits.py` | `acts_on`/`needs` in `word.set`, `FIELDS`, kit validation | ~+20 |
| `painter/arrangement.py`, `kernel/helping.py` | `tag:` through the kind's shape; help says what a word acts on | ~+25 |
| House, board | Shapes on their words; remove their hand-written checks | ~+15 / −10 |
| taskboard, window, theme, map, model, summarize | Shapes on the words that take a thing, about 30 one-line edits, each app with its own test | ~30 |
| `bonds.py`, House context | Unregister the held words; skip their tests | ~−30 |
| tests | The kinds half of `test_kinds_and_bonds.py`; new scenario tests; fixes in test_kits, test_lines_plainly, test_help_topics, test_missing_words, test_skeleton | ~400 |

**In total:** about 500 to 600 kernel lines touched, with net growth near zero, since round 3's machinery goes. Then about 400 lines of tests and about 45 lines across seven modules.

**Three build sessions:**
1. The kernel, its check and the regression replay.
2. Shapes on each app, with its tests.
3. The painter, help and docs.

**Making it live** (kdesk restart and a check on the desktop) is Alex's call.

**Shared checkout (read, 11:18 today):** another session has uncommitted edits in `kernel.py` and `words.py` (refusal logging, `refusals.py`), beside my round 3 changes. Before building, those need to be committed, or the two builds agreed, so neither overwrites the other.

## How I'd know it works

**1. Replay on the desk copy (the gate, run before any shape exists).** For every word and every thing Alex can see:
- which entry a plain word picks;
- whether the word runs or refuses.

Every pair should match today exactly. This time that's achievable, because no shape means no change.

**2. Scenarios, one per app as its shapes go in (imagined until run).**
- **Calendar:** a Seabright board event (`kind=post post_kind=event start=…`) and Alex's own meeting both show in a lens `of tag:event`. A task's `when` (a due date) doesn't.
- **RSVP:**
  - `board.rsvp` reaches the meeting once the meeting has seats;
  - without seats it refuses, naming them;
  - the board's hand-written check is gone.
- **House:** `house.build` reaches `taskboard-task` and `task` cards and refuses a note, with the reason. The check in `builders.py` is gone.
- **Done across apps:** `done` on a taskboard card runs `task.done`; on a second app's todo it runs that app's word.
- **Spellings:** an event saying `starts` shows in the calendar. `set … start=` refuses with the right line.
- **Homonyms:** `colour` on tasks and `color` on styles stay apart.
- **Governance:** Bea can't declare a kind with needs in the place, and narrowing `event` is refused, naming its words.
- **Power:** the summarize grant (`only=kind:taskboard-task`) can't touch a note that fits task.
- **Privacy:** a need on an aspect the actor can't see doesn't fit, and the refusal doesn't name it.

## How strong my grasp is
- **Strong (read twice now, once by me and once by an independent critic, with file and line):**
  - every place a word meets its thing;
  - where kinds are named;
  - how modules publish and refresh words;
  - what a rewrite of `set` would break;
  - the code being removed (mine).
- **Medium:** `painter/arrangement.py`, kits, and the map, theme and model modules' word code. I'd read each before touching it.
- **Weak, where I could be wrong:**
  - **Whether apps share shapes in practice.** The evidence is two hand-written checks (board, House) and my fixtures. If shared shapes stay rare, the payoff is exact refusals and `actions <thing>`, not cross-app reach.
  - **Values across apps.** Per-app `done` answers it in principle; nobody has yet used two side by side.
  - **Cost.** Fitting on every name lookup is unmeasured beyond 17 declarations.
  - **The desktop shell's right-click menu.** I haven't read `shell.js`.

## Decisions that are Alex's
1. **The shape goes on the word** (`acts_on` + `needs`). Kinds are named shapes for people, lenses and shorthand.
2. **Authority goes by own kind;** reach and views go by fit.
3. **Spellings are read through but never written silently;** `set` refuses with the right line.
4. **The order when two words fit:** own kind, most needs, nearest group, then ask.
5. **Kinds change additively,** made by leaders, referred to by name.
6. **Hold `around`, `nearby`, `preview` and the House context** until the graph work resumes.
7. **`extends` on kinds** (Alex's suggestion, 28 Oct):
   - `make kind=kind name=meeting extends=event needs=place`;
   - a child inherits its parent's needs, and later widenings of the parent;
   - it may add needs, never remove them (Tana's supertag rule);
   - it may extend several kinds;
   - cycles are refused.

   Words keep `acts_on` + `needs`, which reads as "extends this kind, for this word only". About 30 lines in `kinds.py`.

## What would change my mind
- **If app authors find declaring a word's shape a chore they skip,** shapes need inferring from the word's steps (a verb note's `set $1 lane=` already says it needs `lane`). Only module words would need declaring.
- **If two apps sharing a kind still need a translation for every word,** shapes aren't enough. Kinds need Palantir-style mappings ("this kind implements event, with `begins` as `start`").
- **If a month in, leaders aren't keeping kinds current,** the payoff is checks and `actions <thing>`, and cross-app reach waits for the commons.
- **Later, not now:** check that a module's answer touches only the aspects its word declared. That would make a shape a contract the kernel verifies.
