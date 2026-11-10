# Kinds all the way down

> **Approved by Alex, 29 Oct 2026** ("i think you've got it. No reviewers, start building it out"), after a talk-through in the session "Think fresh: kinds and a graph of the Agora space". Written by Claude. It builds on [[kinds-intelligence]] (draft 1), which it partly supersedes: no bridges, no machine-only "supports" stage.
> **Labels:** **read** (code), **ran** (numbers as printed), **imagined** (design).

## Alex's words, in order
- "kinds to be managed by the system they are on, things can bring in their kinds and words when they enter the system, and its the job of intelligent agents to manage how they interoperate"
- The rare question for desk agents: "is this thing coming in the same as something we already have". If so, they make it interoperate. They also see whether it extends something we have.
- "i dont want to say anything ever, it should be figured out by the agents and just work."
- No bridges: synonyms in the dictionary.
- Same vs extends: missing aspects don't make a new kind (a video without a location is still a video). Notably different aspects do.
- Words should name kinds by entry, not only by name, so homonyms (a game event, an analytics event) are told apart.
- GitHub issues aren't tasks. An issue may extend task for lists; acting stays with GitHub's own words, and a rule can link them.
- "a kind all the way until it reaches a value": an upvote is a kind, and its value is the count. Words that work on upvotes reach anything with one, and an upvote draws the same everywhere.
- The base set of kinds should be as large as possible and always growing.
- Loose aspects matter, but too many loose ones is a worry.
- "kind is what it's made of, state is the values of its parts." (Claude's sentence; Alex: "i like this".)

## The design (imagined)
1. **Value kinds are the bottom.** The kernel holds a few fixed ones: `text`, `number`, `time`, `yes-no`, `link`, `person`, `thing`. A declared kind may be one: `make kind=kind name=upvote value=number`. Its value is checked.
2. **Aspects have kinds.** A need may say its part's kind: `needs="title start:time likes:upvote"`. A typed need is met only when the value reads as that kind. A part whose kind is made of parts holds the id of its own thing (a comment thread), and is checked when a word reaches it.
3. **An aspect is a part of a kind when:**
   - a kind the thing is declares it (`likes:upvote`); or
   - its name is a kind's name or synonym (`upvote=12`, or `likes=12` when upvote's synonyms include likes), and the value reads as that kind.
   Otherwise it's **loose**.
4. **Words reach parts.** A word with `acts_on=upvote` reaches anything with an upvote part. The word is told which one: guard sets `part=` for the line, so a verb reads `$part` and a module gets `kv.part`. Two upvote parts on one thing: the caller says `part=`. Permission doesn't change: the thing's own kind and grants still decide who may act.
5. **Synonyms are dictionary names.** A kind takes `aliases=`, as a word does. One kind, other names: `rows todo` lists tasks, an aspect spelled `likes` is an upvote. That's the agents' "same" answer. "Extends" stays `extends=`.
6. **Telling apart and finding the same (deterministic, no model):**
   - `alike <kind>`: declared kinds made of the same parts, closest first, with what's shared and what differs.
   - Making a kind says, in its ok line, which existing kinds are made of the same parts, so the maker (person or agent) can extend or use one instead.
   - `aspects`: every aspect on things you can see, as a part of which kind or loose, with counts. Many things sharing one loose aspect is a kind we're missing.
7. **Agents do the saying.** JEFF and other stewards' agents use `alike`, `aspects`, `aliases=`, `value=`, typed needs and `extends=` themselves; Alex never declares anything.

## v1, built now
1, 2, 3, 4, 5, 6 above, in `kernel/kinds.py` with small hooks in `kernel.guard`, `words.rows`, `kits` and the dictionary of kernel words.

## What the Seabright board shows (read: src/community/MESSAGE-BOARD.md and board/board.py, 29 Oct)
1. **Kinds need optional parts.** A board post kind says `fields=` (what it may have) and `required=` (what it must), and board.py checks types itself (`stamp(start)`, seats a number from 1 to 10000). `required` is `needs`; `fields` is optional parts, which kinds don't have yet ("a video without a location is still a video"). Next: typed optional parts on a kind, so board.py's own checks move into the world. **Built later on 29 Oct as `has=`**, with `aspects suggest`; see "Clearing loose aspects" below.
2. **Some parts are computed.** The board's upvotes are the kernel's sealed `like`: a count over per-person facts, never a stored number. Parts in v1 are stored aspects (an imported video's `likes=12`). An upvote count the kernel computes needs a part that is a reading.
3. **Reading crosses apps; acting stays with each app's words.** `rows upvote` can order board posts and imported clips together ("Top this week"), but upvoting a board post is `like`, while an imported count is read-only. The same lesson as GitHub issues.
4. **board.py compares `post_kind` strings** (search, catch-up, feed filters), so synonyms and `extends` don't reach it. Read through the kernel (`rows <kind>`, `fits`) instead.
5. **Where it helps now:**
   - neighbours add post kinds in the world ("Lost pet", "Ride share"), and making one says which existing kind has the same parts;
   - `aspects loose` shows fields people put on posts that no kind names;
   - `alike` finds the desk's `taskboard-event` and the board's events, so an agent can name one the other's synonym;
   - `calendar` can say `needs="start:time"`, and the kernel refuses a start that isn't a time.

## On a copy of the live world (ran, 29 Oct, headless; scratchpad dryrun_parts.py)
- 3,115 records load in 1.08 s; the load adds one record (the kernel's new words: alike, aspects).
- `aspects loose`: **162 aspects on 304 things Alex can see; 160 are loose somewhere.** Top: `about` (115 things across taskboard-event, chat, post, ask-request), then the task board's `lane`, `priority`, `colour`, `seats`, `short`, `who`. That list is the agents' first naming job, and `about` is the trials' homonym again.
- `rows time` and `rows event`: nothing yet. No kind gives `start`, `due` or `when` a kind; one declaration (`event needs="title start:time"`) and every dated thing answers.
- `alike taskboard-event`: nothing; the board's events are posts with `post_kind=event`, not a declared kind.

## Clearing loose aspects (Alex: "Yes, go ahead", 29 Oct)
The order he approved:
1. **Count what matters.** Done: one-thing settings and computed fields are counted apart. On the live copy that's 89 shared aspects, not 160.
2. **Optional parts** (`has=`). Built.
3. **Board cards first:** `aspects suggest` writes the `has=` line for `taskboard-task`.
4. **Let the values speak:** the same, for every kind.
5. **Judgment calls go through JEFF:**
   - people written as names;
   - the progress words (`status`, `build`, `build_phase`, `source_status`, `plan`, `state`, `verdict`): one stage kind (values.md);
   - `colour` and `note_colour`;
   - homonyms (`where`, `shows`, `about`);
   - hashes;
   - lists.
6. **Keep it from coming back:** `set` says when a value isn't its part's kind; JEFF gets the top of `aspects suggest` as a gardening card.

**Done live, 29 Oct (ran):**
- **Kernel restarts:** twice, through the keeper. Nothing closed, House and the board workers kept running, and the kernel was back in 3.3 s and 3.4 s.
- **The naming pass,** as agent for Alex: 11 declarations. `taskboard-task` got 25 typed parts, plus `taskboard-event`, `document`, `soul`, `charter`, `house-agent`, `window`, `map-layer`, `taskboard-lane` and `board-channel`, and `chat` as a closed kind.
- **Held back for JEFF:**
  - `verified`, which mixes yes, no and prose;
  - `import_sha256`, a hash;
  - `about` on posts, a homonym.
- **Loose shared aspects: 87 → 54.** The 54 are judgment calls, on card dk1557 for JEFF, and he was told in Shop talk (dk1559).
- **One false match, fixed:** making `charter` said it had `soul`'s parts, because both only record where they came from, in prose. Kinds that share only text parts are no longer offered as the same. The suggester also checks for hashes before prose.
- **Found:** windows keep `at` and `size` (screen geometry) in the world, against Alex's "visual state stays local". It's on JEFF's card.

## Not in v1
- **Words bound to a kind's id** (`acts_on` by declaration id, so renames and homonyms across scopes are safe). Next; today names are one per scope.
- **A model behind the agents** (the librarian). It needs a live model trial, which waits for Alex.
- **Value synonyms** (`closed` = `done`): values.md.
- **Module-named kinds** (`game.event`, `analytics.event`).
- **Kinds travelling between worlds** and being matched by meaning on arrival.
- **Drawing per kind** (an upvote looks the same everywhere): the painter's component per kind.
