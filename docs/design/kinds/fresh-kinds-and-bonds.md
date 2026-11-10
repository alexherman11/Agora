# Kinds and bonds: a fresh look

> Thinking by Claude (a fresh session), 27 Oct 2026, for Alex. Rounds 1 and 2 are thinking; Alex then said "build it", and round 3 (at the end) records what was built and what was measured (kernel source only; no live world was touched). For rounds 1 and 2, two probes ran read-only on a copy of the desktop world's log (1,669 records, 24 to 27 Oct). This sits beside the first take (README.md, NOTES.md) and questions it rather than extending it.

Labels: **ran** (executed here, number as printed), **read** (primary source), **recall** (memory, not checked), **imagined** (design).

## The question

How should Agora relate its things to each other, through kinds and through a graph, so the space stays explorable and holds together as it grows and many people and agents build in it?

## Five moves

### 1. Identity is the id, so kinds are free to be loose

In classical ontology a kind ("railing") also says what makes a thing the same thing over time. That is why kinds there are rigid and argued over. Agora doesn't need that: identity is the id, minted once, never reused, surviving renames, moves and forks (**read**: SHAPE section 2; Dynamic Desk, Objects). Replace the wooden railing with steel and it is the same thing because it has the same id, not because it is still a "railing".

So kinds carry no identity. A thing can have many, gain and lose them, and have different ones for different people, and nothing breaks. Most of the hard arguments in the first take (noun against adjective, essential against not) come from the classical job kinds no longer have here. (**imagined**, and the point I'd most like Alex to push on.)

### 2. A kind is what an interface needs

Alex's event reply is the centre: the Seabright calendar shows *events*, every event it can reach; the meeting group's event carries a meeting-notes facet the calendar doesn't draw; "some interfaces are more rich than others".

Read that as: **a kind is a requirement**. A calendar needs "has a time and a title". A word like `map.near` needs "has a place". Anything that meets the need fits; nobody signs up. A named kind ("event") is a requirement many interfaces share, given a name so people converge on it.

- **Nesting falls out for free.** "Meeting" needs everything "event" needs plus attendees, so every meeting is an event. That is Alex's own rule ("has the same but less of the aspects … sits inside") and it is width subtyping on records (**recall**: Cardelli; Go interfaces; TypeScript). No one maintains a tree.
- **It is how CSS already works**, which the desk uses daily. A selector is a requirement; many match one element; the most specific wins; some properties pass down. Kinds can work the same: many fit, the most specific one's word or default wins, and look and lifetime cascade (**imagined**).
- **The inverse is the useful direction.** "What kinds is this?" becomes "what can show it and what can act on it?": which lenses would draw it, which words reach it. Alex's "where it can be displayed" and "what can control it" are the kind question asked backwards.
- **Declaring is just another aspect.** Where shape can't tell (Rocket League is a program; only a person knows it's a game), a yes writes `is:game` on it, with author and date. Then "game" is "has `is:game`, or fits the game test". One mechanism, with history.

### 3. "Maybe not always" is a promise check, not a list

Reading through a wider kind is always safe. Writing through it is where things go wrong (square and rectangle; database view update; **recall**). Rather than having each kind list the words it withholds (the first take's approach), let a kind carry a **promise**: "a pamphlet has six panels", "a decision is edited only by leaders".

- A do word from a wider kind reaches the thing. The kernel works out the facts the act would write, then checks them against the promises of every kind the thing holds, before the record is written. If one breaks, it refuses and quotes the promise ("a pamphlet has six panels; make it a booklet to add pages").
- This sits beside the fence: the fence refuses an act on stale sight, the promise refuses an act by a word that never knew this kind (**read**: SHAPE section 9 computes facts before writing; **imagined**: the promise step).
- External words (WM moves, sending mail) can't be checked after the fact, so for them the kind must say yes up front, or the word must say what it will do. The first take had this right.
- Same word, different act (`close` on a window, a native window, a pane): the most specific fit wins, as in CSS.
- Classifying never adds power (the first take's rule, kept). Since kinds are shapes, anyone who can add an aspect could make a thing "fit"; grants must therefore name things and places, not shapes.

### 4. Bonds come from the log, not from people

Alex: "Things should be related because they were made together, they were both on the same task or mentioned the same person, they caused each other or they were both caused by the same thing."

**The log already is that graph.** Every record says who acted, for whom, through what (`via`), with which word, on which things, having seen what (`saw`), caused by which record (`caused_by`), what it undoes, and when (**ran**: on this log, `for` is on 765 records, `saw` on 336, `undoes` on 44, `rule` on 17, `caused_by` on 7). Each record ties all of those together at once. Every kind of bond Alex lists is a reading over it. Nobody types an edge.

Probe (**ran**, scratchpad only): 166 live content things (not words, components, grants, widgets and the like). Counting bonds from the log alone (same act, made by the same person within 3 minutes, saw while making, caused, explicit links, ids mentioned in text, sharing a maker, a `who` or a lane):
- 165 of 166 have at least one bond (the first take's count with links only: 81 isolated of 158).
- Pairs by number of independent bond types: 1,774 with one, 404 with two, 199 with three, 7 with four, 2 with five.
- The strongest pairs are exactly the meaningful ones: a reply and its parent post (five types); an uploaded file and the document read from it (five); each task and its event (three).
- The most common bond is also the weakest: "made by the same maker" is 1,222 of them, mostly one busy module. **A bond through something everyone shares says little; a bond through something two things share says a lot.** So strength = how many kinds of bond agree, each weighted by how rare it is (**recall**: this is how link prediction weights common neighbours, Adamic and Adar).

Two gaps the probe shows:
- **Cause is barely recorded.** `caused_by` is only on rule-triggered module answers. When JEFF makes a task because Alex said something in chat, nothing records that. The kernel could record cause automatically: the happening or message an act was answering. That is the one place the system should write more, and it costs nobody any typing (**imagined**).
- **Shared mentions need the mentioned thing to exist.** Alex's dock request ("i want rocket league to appear here") and the task nine minutes later ("I want rocket league to be able to open") have different makers, saw nothing, and share no link (**ran**). Their only bond is a name in their text, and Rocket League isn't a thing. Make it one (an adapter publishing installed programs) and both, plus the game gate's list and Steam, bond through it at once. People, places, programs and topics as things are the hubs that make "mentioned the same person" work.

Properties the bonds need as more people join (**imagined**):
- **Computed as the reader.** A bond whose evidence you can't see doesn't exist for you; otherwise bonds leak hidden things ("these two are related because of Maya's private note").
- **Explained.** Every bond says why ("made in the same act; it replies to it; you were looking at it when you wrote this"). That is what makes it trustworthy and correctable. "Not related" is one click and becomes a fact.
- **Some are personal.** What you looked at together belongs with your `seen/` marks, beside the world, not in it (Alex's 26 Oct rule on visual state).
- **A cache, never truth.** The bond index is derived and deletable, like snapshots (**read**: SHAPE section 1, `cache/`). Change how bonds are computed and you just rebuild. A group can add a bond type as a reading, without source.

### 5. Directions to walk

From any thing, a handful of directions, each a family of bonds:

| Direction | Bonds in it | From the log today? |
|---|---|---|
| **Alike** | same requirements fit; same named kinds; similar text (embeddings, later) | partly (kinds are strings) |
| **Origin** | made in the same act; caused by; copied from; who made it, for whom, through what | yes, cause thinly |
| **Consequence** | what it caused; what replies to or copies it; what undid it | yes, thinly |
| **Company** | same task, thread, place, person mentioned, moment | partly (needs entity things) |
| **Control** | words that reach it, modules and people who may use them on it | yes (dictionary, grants) |
| **Audience** | who can see it | yes (who-sees) |
| **Shows in** | lenses that would draw it; places it is in | yes (`in:`, lens selections) |
| **Then** | what else was happening around it | yes (`at`) |

The same walk works from a word, a kind, an aspect, a person or a lens, because they are all things. "The Agora space", not just its content.

## Meaning of aspects is the hard part

Shape-fitting only works if an aspect means one thing. The first take found it doesn't: `text` is prose, CSS and lens source; `about` is a link on some kinds and prose on a chat (**read**, its probe 1). I checked whether the words that write an aspect could tell its meanings apart (**ran**): mostly no, because generic `make` and `set` write almost everything; the *kind* of the thing does separate them (`where` on a grant is a scope; on an ask-request it's a place on screen). Which lenses *read* an aspect may be a better signal; I didn't measure that.

So some shared vocabulary is needed. The way the web got there is worth copying: microformats looked at how people already marked up events and named the common pattern ("pave the cowpaths"; **recall**). In Agora: notice two groups' aspects that are used alike, suggest `same as` with one click, and keep the answer. Per-group names, bridged; one calendar of all events.

## What this does as Agora grows

- **Tools interoperate without agreeing on code.** The calendar draws every event it can reach, whoever made it. Forks stay compatible because shapes outlive the programs that made them (Dynamic Desk leaning: "Data keeps its meaning after the program that made it is gone").
- **You know what a change will touch.** Change a kind, a lens or a word, walk outwards. That's Dynamic Desk's "Before making a change you know everything it will affect".
- **JEFF's memory has an index.** The vision says JEFF knows himself "through the accretion of artifacts". Bonds are how he finds the right ones for now: start at what Alex is looking at, walk origin and company.
- **Agents find each other.** Two builders touching things that bond strongly are working on the same thing; say so before they collide.
- **Clutter sheds itself.** Things nothing used can reach through strong bonds fade; things tied to living work stay (**recall**: tracing garbage collection). That ties back to C10's origin on the clutter page, and gives C2's lifetime a partner: a kind's lifetime is the default, bonds are the evidence.
- **Privacy is a walk too.** "Who can reach this, and through what" is one direction.

Risks:
- **The hairball.** With many bond types everything is near everything. Rarity weighting, explanation and directions are the answer; a flat "related" list isn't.
- **Gaming.** In a 200-person place someone can mass-mention to manufacture bonds. Weighting by whose acts made the bond (your own circle first) may be needed (**imagined**).
- **Vocabulary drift.** Without aspect meanings, shape-fitting gives false fits (the first take's lattice: 20 proposed nestings, about 6 sensible).

## Where I differ from the first take

- It split **nouns** (declared, nesting) from **adjectives** (computed). Here both are requirements, and a declaration is an aspect. The split guarded identity, which the id already guards.
- It had kinds **withhold** words by list. Here kinds state **promises** and the act is checked.
- It treated the graph as **roads, shelves and footpaths**, with kinds as the main structure. Here kinds are one bond family among eight, and the log's records are the main source.
- It leaned toward **per-group kinds**. Alex's event reply says otherwise and I agree: groups differ in names and in how rich their lenses are, not in separate kinds.
- Kept from it: classifying never adds power; external words need a yes; aspects need meanings; make the game gate's hidden kinds visible.

## What would change my mind

- If, once aspects have meanings, shape-fitting still gives many false fits, declared kinds have to come first and shape becomes a suggestion only.
- If real promises can't be written as checks (a pamphlet's panels, a decision's leaders), withhold lists are simpler.
- If Alex explores from five real things and the top five neighbours feel random, the strength weighting is wrong. That is the cheapest real test, in a hidden sandbox.
- If recorded causes are too coarse (everything in a long chat "caused by" its first message), cause needs finer grain or less weight.

## Not done

No live trial. Bond strength not ranked or shown to anyone. Lens reads of aspects not measured. The 3-minute window and the 40-thing cap on shared groups in the probe were my choices, not tested.

---

## Round 2 (27 Oct, after Alex's replies): three uses, and synonyms

Alex asked how "see what a change will touch", "JEFF finds what's relevant" and "agents notice each other" would actually work, and said he hopes aspects can have "things that are basically like synonyms".

### One reading under all three

All three are the same walk, `around <thing>`: bonds by direction, each with a strength and a reason, computed as the reader. They differ in which way they face:
- **impact** faces forward: from what I'm about to change, to what depends on it;
- **memory** faces back: from what's in front of us now, to what made it and what sits with it;
- **awareness** faces across: from my work in progress, to someone else's.

### Impact: what a change will touch

**What's already there (read).**
- Lenses name what they read. `work.lens` filters `of tag:taskboard-task, prop:lane=Now`.
- Stored lines bind word ids when saved (a1156: `do_bound`, `steps_bound`), so "what uses this word" is a reverse lookup.
- Rules say `of_kind=`, grants say `only=kind:…`, and hearers are known to the kernel.
- `caused_by` is already used by undo: undoing an act also undoes what rules did because of it (P3, Alex 27 Oct; `words.py`). That's impact after the fact.

**A real case (read facts; consequence imagined).** 12 live tasks say `lane=Now` as text, and the Work lens filters on `lane=Now`. Rename the Now lane (dk80) to "Doing" and the act writes one fact. But 12 tasks then name a lane that doesn't exist and drop out of Work's "moving" column. Nothing says so. That breaks Dynamic Desk's "Renaming, moving or reorganizing never silently breaks a link".

**How it's realized (imagined).** Before a do act commits, the kernel already has its facts. A preview walks backwards from each changed (thing, aspect):
1. **exact**: the facts themselves;
2. **readers**: lenses whose selections or parts read that aspect, then the windows and places showing those lenses, then the people who see them;
3. **hearers**: rules and modules that would wake, and what kind of thing they write (one step exact, beyond that estimated);
4. **bound lines**: stored lines bound to a changed word;
5. **membership**: for a change to a kind's requirement, the things that would enter or leave it ("5 events have no place; they'd leave the map").

Small changes show nothing. A change that reaches beyond its own thing gets one line ("this also changes what 12 tasks point at and what Work shows; fix both? · just this"). For shared things the preview names the audience: "used by 3 groups' lenses, about 40 people". That's what a group vote on a change would need to see.

### Memory: JEFF finds what's relevant now

**What's there (read).** The House wakes JEFF with the line, the chat's name and the record that woke him (`house.py` `wake`). His prompt carries the charter and his soul. Anything else he has to go and `look` for. Nothing tells him what is around the line.

**How it's realized (imagined).**
- **Focus**: the line, its chat, the things it names (by name match against things; this is why people, places and programs need to be things), and what Alex has open, read through Alex's own `seen/`. JEFF acts for Alex, so he reads as Alex.
- **Walk**: 1 to 2 steps from the focus, strongest first, with origin (why it exists), company (same task, thread or thing mentioned), consequence (what came after, including JEFF's own last tries) and then (what's happening now).
- **Hand over**: a few short lines with reasons, attached to the wake. JEFF can walk further with `around`.
- **Use strengthens it.** When JEFF looks at something while answering, the record's `saw` captures it, so that thing bonds to the line he was answering. What gets used together gets bonded more strongly; what nothing reaches fades. That's associative memory (recall: spreading activation, Collins and Loftus 1975; the Remembrance Agent, Rhodes 1996) built from the log, not a separate store.
- **Record cause for agents too.** The House knows which record woke JEFF. If his acts in that turn carried `caused_by` that record, then "undo what JEFF did because of my message" already works through P3. And "why does this exist?" gets an answer for everything JEFF makes. Today `caused_by` is set only for rules (`kernel.py` 1101).

**A test that needs no model and no live world (imagined, not run).** Replay past wakes from the log. For each, compute the neighbourhood from what was known then. Then check whether the things JEFF actually looked at or touched in that turn were in it. If the top ten rarely contain them, the bonds are wrong.

**Beside embeddings.** Bonds explain themselves, follow who-sees, and cost nothing to run. Embeddings would add likeness for things with no history yet. They complement each other; neither replaces the other.

### Awareness: agents notice they're on the same thing

**What's there (read).** Builders claim a card with a fence. Each works in its own worktree, two at once. `house.land` refuses if main moved or user edits overlap, and conflicts "remain for reconciliation" (BUILDERS.md). In the world, the per-aspect fence refuses stale writes. Both catch a collision at the end, and only an exact one.

**How it's realized (imagined).** Every piece of work in progress (a claimed card, an agent's turn, a person editing) has a working set: what it has looked at and touched recently, which the log already records (`saw`, facts, `by`, `for`). A standing hear on your working set's neighbourhood tells you when another working set comes near. By strength:
1. **same thing written by both**: a likely conflict, flagged before the fence refuses;
2. **one reads what the other writes**: "you're working from X; B is changing it";
3. **strongly bonded**: the same topic, e.g. one agent on the Rocket League task while another fixes the game gate. Not a conflict, a chance to coordinate;
4. **one changes what the other uses**: impact, aimed at a colleague.

Agents get it in Shop talk (AGENTS.md: agents coordinate there, not in Conversation). The board shows it on the card ("near: B, game gate"). For source work, a builder's result can list the files and words it changed as things, so source joins the same bonds.

People get the same thing: two Seabright groups planning a cleanup at the same park on the same Saturday bond strongly (same place, same time, same kind). That's an overlap of intentions, not of data.

### Synonyms for aspects

**Live cost of not having them (ran, copy of the log).**
- All 40 live tasks carry both `colour` and `note_colour`, always with the same value. Writers already duplicate to satisfy two readers.
- 43 things have both `name` and `title`.
- 40 things use `colour` and 12 use `color`; none use both.

**Precedent (read).** Words already have synonyms: `aliases` on a dictionary entry, editable with `word-set` and looked up nearest first (`dictionary.py`). Aspects can get the same thing.

**How it's realized (imagined).**
- **An aspect gets an entry** like a word: what it means, what it points at, and its aliases. `colour` with alias `color`; `start` with alias `when`.
- **Read time, never rewrite.** The log stays as written. When a lens or word asks for `start`, a thing that says `when` answers. Writes go to the spelling the thing already uses, so its own tools keep working; a thing with neither gets the asker's spelling.
- **Scoped like words.** Seabright can say "`when` is `start`" for itself. A bridge between two groups is a fact owned by whoever made it and never edits the other group's things. One calendar of all events, each group keeping its names.
- **Narrower, not just same.** `reply_to` is a narrower `about`: anything asking for `about` accepts `reply_to`, not the other way. That's the railing-and-wall nesting again, applied to aspects.
- **Homonyms are the reverse problem.** `text` is prose on a note and code on a lens. A synonym joins two names; a homonym needs one name split by kind ("`text` on a style means CSS"). Same entry, scoped.
- **Found, not typed.** Suggest a synonym when two aspects never appear together, hold the same shape of value (both dates), and sit on things that otherwise fit the same need. The best moment is when an interface misses things ("5 of the meeting group's things look like events but say `when`. Same as `start`? yes · no"). Also suggest at make time ("3 kinds already use `start`"), the cheapest place to stop drift. Agents need this most.
- **Explained and undoable.** Each synonym is a fact with an author. Anything shown because of one says so ("shown because Seabright says `when` is `start`, Maya, 3 Nov").
- **Where synonyms stop.** A pure rename is cheap. A difference in shape (one `start` against `date` plus `time`; a name against an id, as `who=Alex` against dk2; km against miles) needs a small two-way translation (get and put), which is real work per pair. Start with renames; add translations one at a time, when a real miss asks for one.

**What would change my mind.** If most real misses between groups turn out to be shape differences, not spellings, then synonyms alone won't carry it, and translations need designing first.

---

## Round 3 (27 Oct, evening): built

Alex: "this is a good plan, build it". The exact contracts are in [[SHAPE]] section 17, "Kinds, spellings, promises and bonds". In short:

- **Spellings**: `make kind=aspect name=colour aliases="color note_colour"` (place-wide or for a group's members); readers see one name, writes keep the thing's own spelling, `inside=` makes a narrower aspect read as a wider one.
- **Kinds as needs**: a kind declaration's `needs=`, `inside=` and `test=`; `rows <kind>` and a lens's `tag:<kind>` show what fits, each with why; `exact=yes` for the old list. `is <thing> <kind>` for what shape can't show. `kinds <thing>`.
- **Promises**: `promise=` and `promise_says=` on a kind; checked on every act before its record is written.
- **Words for wider kinds** reach what fits; outside-world words only where a kind was said.
- **Turns**: `turn <agent> r<n> work=<card>`; records then carry `because` and `work`. The House says it on wake and at the turn's end.
- **`around`, `nearby`, `preview`** readings; a rename's receipt names what still uses the old name.
- **JEFF's wake** carries up to four "around this" lines and three "nearby" lines.

Changed: `kernel/kernel.py`, `words.py`, `predicates.py`, `readings.py`, new `kinds.py` and `bonds.py`, `painter/arrangement.py` (one selection line), `modules/house/house.py` (wake context, turns). Nothing committed.

**Ran.**
- `tests/test_kinds_and_bonds.py`: 18 passed. Full kernel suite before this work: `128 passed, 30 subtests passed`; after: `146 passed, 30 subtests passed in 115.56s`, and again after the last fixes recorded below: `146 passed, 30 subtests passed in 116.84s`.
- `modules/house/proof_house.py` (hidden headless copy of the desktop, port 8830, scripted model): "all checks ok", 19 checks. In that copy the House has no grant for `turn`, `around` or `nearby`, so it ran without them, as designed; the proof shows nothing broke, not that the context helps.
- On a scratch copy of the desktop log (1,773 records, 660 live things), as Alex:
  - `around` on the Rocket League task: 53 ms. Its company now includes the dock request, "both mention rocket league". In round 1 those two had no bond at all.
  - `preview set dk80 name=Doing`: "14 taskboard-tasks say lane=Now; they would name something that is gone", plus the three lenses that filter by `=Now` (taskboard, Task board · Components, Work). Nothing written.

**Found on real data and fixed (ran, then changed).**
- One-word names matched ordinary words: "window" (the window module) and "open" (a widget). One-word names now count only for people, programs, places and the like.
- "The same aspects" fired on bookkeeping (`about, for, made_by`).
- A widget also called "Now" hid the 14 tasks from the rename check; only things of the renamed thing's kind count now.
- `within` was already make's visibility parent, so nesting is `inside` (Alex's "sits inside").
- The shell ate backslashes in one edit (AGENTS.md warns of this); nothing was written by it.

**Not done, or not verified.**
- Live: the desktop kernel runs the old code until it restarts, and the House needs grants (`turn`, `around`, `nearby`). Both are Alex's call; restarting kdesk drops the WM to shadow (memory).
- Builders: `builders.py` does not say `turn` yet. One agent session serves every builder, so two builders at once would share one turn; a turn per builder needs a session per builder.
- Claude Code and Codex sessions outside the House: no hook yet (Alex, 27 Oct: "No way we can reach inside existing applications I suppose?"). Seams named in chat: Claude Code hooks, a git adapter for commits, Codex's own end-of-turn notice (unverified).
- The JEFF memory replay test (does the neighbourhood contain what he went on to look at) is not run.
- Translations between differently shaped aspects (date + time against one start) are not built; only renames and narrower-than.
- `around` scans every thing on each call (fine at 660; not measured at 10,000).
- Bonds are not weighted by whose acts made them, so mass mentions could still inflate a bond.

**Source edits, as Rough spots** (the world-level words that were missing): an aspect entry with spellings; `needs`/`inside`/`test` and `promise` on a kind; `is`; `turn`; `around`; `nearby`; `preview`; `num`, `has` and comparisons in tests. Each now exists as a world-level word or field, so later kinds, spellings, promises and bond reading need no source.

---

## Round 4 (28 Oct): my own review of what I built

Alex asked me to walk through the changes and say where I disagree with myself.

**The serious one: declarations got power, and who may make them did not change (ran, scratch world).** Before this build a `kind=kind` thing constrained nothing, so letting any member `make` one was harmless. Now a declaration can refuse acts (promises), widen views (needs) and change what readers see (aspect spellings), and any member may still make one. On a scratch world:
- Bea, a plain member, made `kind=kind name=task promise="False"`. Alex, the steward, was then refused making any new task ("tasks are frozen"). An existing task stayed editable only because "already broken" lets it through.
- Bea made `kind=aspect name=lane aliases=who`. Alex's task with `who=Alex` then read `lane=Alex`, and `rows task lane=Alex` found it.
- At one level the last declaration of a name wins, so a member's later declaration also overrides the steward's.

This breaks the principle I proposed myself, "classifying never adds power". I guarded grants, but promises take power from others and spellings bend shared reading. The fix belongs in the kernel: a declaration counts for a scope only when a leader of that scope (a steward for the place) made it, or for its own maker. A member's declaration then applies to their own reading and their own things, and becomes shared when a leader takes it, the way a kit is taken.

**Hard-coded vocabularies (read: my own code).** `ENTITY`, `QUIET`, `NOT_FITTED`, `SKIP`, `WHO` and the phrase tables in `bonds.py` and `kinds.py` are kinds and aspect meanings kept in source, the same thing I criticised the game gate for. They are a bootstrap. Aspect entries already have `means=`, so `made_by means=who` and `kind=kind name=program named=yes` could replace them as world data.

**Untested weights (imagined).** 3.0 for a link, 2.5 for a cause, 1.5 for a mention: my guesses. The cheap check (Alex judges the top five neighbours of five real things) has not been run. The JEFF replay test would measure the same thing without him.

**Scope is the reader's membership, not the view's group.** Alex's example was the Seabright *calendar* showing events. I scoped spellings and declarations by the reader's groups, so two people looking at one lens can see different rows. That's defensible ("by who looks"), but it isn't what his example said. Promises are scoped by the thing's groups, which is right for protecting a thing but is a second rule to learn.

**P2 changed quietly.** Alex's P2 says "ask only when two fit". For one named thing with nested kinds, the nearest kind's word now wins instead of asking. I think that's right, but it's his rule and I changed it without asking.

**Preview reaches only the kernel's own words.** Most words people say are verb notes (`task.*`), and those are refused. Running a verb note's steps into one Tx without committing is the obvious next step.

**Turns never expire.** If the House stops mid-turn, the agent's later acts carry a stale `because` until its next wake. Add an expiry (30 minutes) or clear turns when the House goes off.

**Every call scans everything.** `around`, `nearby`, `names_left` and `Kinds._fresh` walk all things: 53 ms at 660 things (ran), unmeasured beyond. The derived index belongs in `cache/` before worlds grow large.

**What I'd keep (superseded by round 5 below).** Identity is the id, so kinds can be loose. A kind is what an interface needs. Spellings are applied at read time and the log is never rewritten. A promise is checked against the facts an act would leave. `because` is a bond, not an undo cascade. Every bond passes who-sees and comes with its reason.

---

## Round 5 (28 Oct): the proposal after three turns of thinking

> Draft by Claude for Alex's design gate, after his replies of 28 Oct and three independent reviews (one on the graph for every agent, one critic of the kinds design, one on privacy). **Nothing below is built yet**, except where it says the round 3 code already does it. His words that set the direction: kinds "have to be based on the properties of things"; promises "seems hella wishy washy … lets scrap it"; words reaching what fits "should be more central … a big part of my idea"; the graph should serve "all the agents, not just jeff".

### What changed my mind (all ran or read)
- **Declarations had power anyone could take** (ran): a plain member's promise blocked the steward's new tasks, and a member's alias changed what others read.
- **No true synonyms in the live world** (ran): `colour` is a swatch name on tasks; `note_colour` is the note excerpt's colour; `color` is CSS hex on styles and map layers; `name` is an identifier and `title` is a display name. My make-time hint would have suggested merging `colour` with `color`.
- **Agents' reads aren't remembered** (ran): 13 of 397 agent acts carry `saw`. "Use strengthens bonds" does not happen for agents.
- **The outside-world rule was dispatch only** (read): `wm.close <thing>` said in full runs with no kind check.
- **Five privacy leaks** (two ran, three read):
  - `nearby <person>` shows what that person read.
  - `around` matches hidden aspects, so it confirms private answers and phone numbers by guessing.
  - `audience` re-runs each person's private visibility tests.
  - `control` names hidden groups.
  - Strength numbers count hidden things.
- **The pattern in my own errors:** I treated "you may see this thing" as enough. Fields inside visible things leak, and so do patterns across many visible things.

### Kinds
1. **Properties only.** A kind is `needs=`: aspect names, and `aspect=value` for a marker (`make kind=kind name=game needs="run game=yes"`).
   - A mark is an ordinary fact, set with `set`'s rights, with its author and date in history.
   - `mark <thing> <kind>` sets it, or refuses naming what's missing ("a game needs run; this note has none").
   - A mark whose other needs lapse shows as stale, the way a broken link does.
2. **Nesting is computed** from needs, by Alex's rule: a kind needing more sits within one needing less. No `inside=`, whose picture was the opposite of his.
3. **Words say the kind they act on.**
   - Each entry has `on=<kind>`, defaulting to the kind its `takes` names when that kind is declared.
   - One check in `step`, for every word however it was said: the target must fit `on`, or the word refuses with what's missing.
   - Outside-world words (`undo=external`) need a kind whose needs include a mark someone set.
   - When two words share a name: nearest kind, then nearest group. This is Alex's call, and it also settles the P2 change.
4. **`words <thing>`**: every word whose kind the thing fits, most specific first. It feeds help, the right-click menu (the standing rule "right-click actions fit targets", made general), name matching and every agent's "what can I do with this?" Round 1's census found 85 of 198 words already naming a kind in their usage (ran).
5. **Governance.**
   - A kind declaration or aspect entry binds a scope only when that scope's leaders made it (a steward for the place).
   - A member's applies to their own reading and their own things until a leader takes it, as kits are taken.
6. **Kinds bound by id.** Lenses, grants and rules that name a kind store the declaration's id when saved, as stored lines bind words (a1156). Renaming a kind then breaks nothing silently. Today it would.
7. **Aspect entries keep `means=` and `points_at=`.** That's where the evidence is: pointer typing cut isolated things from 81 to 30 in the first take's probe, and homonyms are the live danger. `aliases` is parked until two groups really miss each other's things over a spelling.
8. **Scrapped:**
   - promises (keep the test language's `num`, `has` and comparisons, which `allows.` and `sees_when` can use);
   - `is:`;
   - `inside=`;
   - aliases, for now;
   - make's near-spelling hint.

### The graph
**Three layers.**
- *Evidence*: the log, plus bond providers (below).
- *Readings*: worked out for one reader, under one profile, never stored.
- *Uses*: what agents and people do with them.

**Rules.**
1. Every bond passes who-sees for each field, not just each thing. Its counts and weights use only what the reader can see.
2. Activity belongs to its person: what they read, their timing, who they work with, the names of an audience. Others get counts and acts, not patterns. `nearby` about someone else says only "is changing it too", on things the asker touched. A group may opt in to more.
3. Text from others enters an agent's context only fenced as data: quoted, with id and kind. The round 3 wake lines paste titles raw; that's a prompt-injection path.
4. An inbound bond counts by how many distinct makers made it, so one person's 30 notes can't flood it.
5. Weights and profiles (memory, review, impact, neighbour) are world things, not constants in `bonds.py`. So are the lists of named kinds, background kinds and "who" aspects.
6. Strength shows as words (strong, some), never numbers.

**New pieces.**
- **Read context.** A write carries what its actor read since its turn began, visible only to that actor's person and their agents. This is the memory signal agents lack today, and it's what the next two need.
- **Following a chain from outside.** Walk forward through `because` and `caused_by` from an outside arrival (a mail, a web page, a stranger's post) to everything it led agents to do. An outside-world act whose chain starts at an outside arrival nobody checked waits for its person's yes. This is Agora.md's "should not treat external information as rules", made checkable.
- **Leak check.** Before an agent posts to an audience, walk back through its read context. If it read something that audience can't see, it asks first.
- **Bond providers.** A module offers bonds from its own domain, worked out on request and never stored: git first (files changed together, commits naming cards), then the window host (kept personal, per Alex's 26 Oct rule) and mail. This is how builders and outside Claude Code or Codex sessions join the graph without the repo being poured into the world.
- **Queries:**
  - `between <a> <b>`: the explained paths between two things;
  - `around` a set of things;
  - `as of r<n>`: what could be seen then, which both replay tests and accountability need;
  - `alike` at make time, so a second beach cleanup offers to join the first.
- **Push** as a hear on an incremental index kept in `cache/`, derived and deletable.

**What it's for, across agents (imagined, each with a test).**
- **Continuity after a reset:** `around <card> toward=consequence`.
- **A builder's brief** written by the world from its card.
- **Review as a walk:** everything stamped `work=<card>`.
- **Duplicates caught at make time.**
- **Who to ask:** the people and agents bonded to a thing.
- **Agents proposing kinds** from clusters, leaders deciding.
- **Explaining an agent's act** to its person: what woke it and what it read.

### Build order (each step tested before the next)
1. **Fix the five leaks**, and fence the wake lines, with the privacy reviewer's three tests. Do this whatever else is decided.
2. **Rework kinds:** properties only, marks, `on=` checked in `step`, `words <thing>`, governance, kinds bound by id. Remove promises, `is:`, `inside=`, aliases and the near-spelling hint.
3. **Replay JEFF's wakes** on a log copy against a recency baseline (Alex's 10 most recent things), plus hidden-link recovery and weight sensitivity. **Gate:** if bonds don't beat recency, stop pushing context to agents and keep `around` as something people and agents ask for.
4. **Profiles as world data,** strength as words, the distinct-maker discount.
5. **Read context**, on Alex's yes.
6. **The git provider**, on Alex's yes.
7. **The outside-chain hold and the leak check**, on Alex's yes.
8. **The index in `cache/`**; `between` and `as of`.

### What would change my mind
- **If recency predicts what agents look at as well as bonds do,** the graph is for exploring and for safety, not for agent memory.
- **If leaders don't keep declarations current,** kinds stay plain words and fitting is rarely used. Measure it a month in.
- **If Seabright wants shared activity,** rule 2 relaxes, group by group.
- **If marks get set on things that can't meet the needs** (a game streamed in a browser tab), needs become suggestions and the mark carries more.

---

## Round 6 (28 Oct): built as shapes, replayed, and tried hard

> Claude, 28 Oct 2026. Round 5's kinds section was rebuilt as "words reach things that fit" on Alex's go-ahead; the design and what changed are in [[fresh-words-reach-kinds]], the contracts in `src/agora/SHAPE.md` section 17, and three large interoperability trials and their friction in `trials/FRICTION.md`.

**Replay against the committed kernel (ran).**
- **The method:** every word was said on every thing Alex can see in a copy of the desk log, and every plain word on every thing's name, each stopped before it committed. That's 130,101 lines, run against the committed kernel (`HEAD`) and the new one. The second run came after the trial fixes: who may answer a plain word, words scoped to their group, and `acts_on` met by a thing's own kind.
- **Identical:** 127,806 lines, including every plain-word pick.
- **Different:** 2,295 lines, all in five words, 459 each:
  - `is`, `around`, `nearby` and `preview` answered "unbound" in the committed kernel (their entries were in this copy from my 27 Oct load) and are now retired;
  - `turn` now runs.
- **No other word changed what it reached or refused.** Nothing changes until a world declares a shape.
