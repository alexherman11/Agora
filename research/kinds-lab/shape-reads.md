# Reading through a shape: so reaching means working

> **Draft 2.1, by Claude, 28 Oct 2026.** Two review rounds done; not approved, not built. §5b holds the round 2 corrections. This is friction 1 in `trials/FRICTION.md`, with friction 5 (optional spellings) folded in.
> - **Draft 1** is kept as written in [[shape-reads-draft-1]] (`drafts/`).
> - **Asked by Alex:** "modules get the thing read through their word's shape (names filled, values typed), so reaching means working". Then: design slowly, with reviewers inside and outside the world.
> - **Labels:** **read** (code or a source, with a reference), **ran** (a number as printed), **imagined** (design).

## Reviews behind this draft (all in `review/`)

| Reviewer | File | What it changed most |
|---|---|---|
| Pike and JEFF, residents, in Shop talk (dk1289, dk1290) | `shape-reads-residents.md` | Every guess is shown. Writes into things that sync outside are outside acts. A refusal says needed / found / where / the fix. |
| A prior-art research agent | `shape-reads-prior-art.md` | Keep a time's form (date, floating, instant). Lens round-trip laws, so a lossy write is refused. Owner-declared mappings (Palantir, App Intents). |
| An adversarial kernel review agent | `shape-reads-kernel-review.md` | `thing` skipped grants and over-shared. The cache leaked across readers. "Reach is reads" made silent swaps. Shapes failed open. Refusals leaked titles. The fence missed spellings. |
| A module-author review agent | `shape-reads-module-author.md` | An envelope, so "unread" can't pass as "absent". Optional reads strict when present. No customer for set-through. `claim` reads seats raw. Producer-side mapping. |
| The kernel-shape session | `shape-reads-kernel-shape.md` | The reading's `saw` covers every thing and aspect it touched. A dict `saw` crashed `_admit_lines`. No tz database here. A word that writes a need shouldn't require it to read. |
| The House/JEFF session | `shape-reads-house.md` | `person` by name must not gate authority. Saved bases break on canonical ids. Label outside-authored text in worker prompts. |

## Fixed already (ran; not design)
The reviews found five bugs in what exists today: four in the shapes built on 28 Oct, one in module answers. Each is fixed in source (uncommitted) with a test.

| Bug | Fix | Test |
|---|---|---|
| A stored shape the kernel can't parse made the word reach **everything**, and `take` didn't check shapes (kernel review C4) | Unparseable needs become an unmeetable need: the word refuses ("its shape can't be read by this kernel"), and a kind admits nothing by shape. `take` validates needs, acts_on and extends. | `test_shapes.py`: 2 new |
| The steward's refusals log showed a member's **private title** from a shape refusal (H1) | `Refused(..., kept=)`. The caller is told the title; the log keeps the word, the need and the id. | 1 new |
| A painted press on a `tag:<kind>` lens was fenced on the kind's name (`start`), while the fact is `starts`, so stale presses were admitted (H2) | The fence counts every spelling a declared kind joins with the aspect (wider, never narrower) | 1 new |
| A module's per-aspect `saw` (`{rev, aspects}`) **crashed** `_admit_lines` with a TypeError (kernel-shape 2b) | `_module_saw` accepts it, and refuses a malformed `saw` | `test_skeleton.py`: 1 new |
| A closed-chat line could wake people outside the chat (card dk1245, found in the world; friction 7) | `to` stays inside the chat | `test_chat.py`: 3 new |
| **Round 2 (kernel review, all ran):** one member's `seats=²` crashed `shown()` for every reader (`'²'.isdigit()` is true, `int()` fails) | Every `isdigit()` guarding an `int()` in the kernel, House, board and painter is now `isdecimal()`. That accepts exactly what `int()` reads, and is a strict subset, so nothing else changes. | 1 new |
| `take` let a kit give the kernel's own `said` a shape (parse checked, governance not) | `take` runs `validate_decl` on every kind it brings | 1 new |
| An unreadable shape made a plain word silently run another word | It still competes (as a word with no needs), so plain words ask or refuse loudly. `actions` doesn't offer it. | 1 new |
| `_module_saw` made `{rev}` a weaker fence than a bare rev | No aspects means the whole thing | 1 new |
| `kept` was lost when verbs re-wrapped a refusal, and `mark` and the "which one?" question named titles in the log | `kept` survives `stop()` and verb wrapping; `mark` and `choices` keep ids only | — |
| An unreadable kind couldn't be repaired once used ("narrower") | An unreadable "before" is never narrower | 1 new |
| **Still open, not mine:** the refusals log keeps the caller's whole typed line, so a private title said by name reaches the steward | Put to the refusals-log session (its design) with the reviewer's proposal | — |

## 1. What changed from draft 1, in one list
1. **Dispatch and names stay on "has"; only admission adds "reads".**
   - Draft 1 would have made `done` silently pick another word, and a name silently pick another thing, when a value was present but unreadable (kernel review C3, ran on today's code).
   - Now the word and the thing are chosen exactly as lists and lenses choose them. The only new outcome is an honest refusal naming the unreadable value.
2. **The reading is an envelope,** not facts overlaid with canonical values: `values`, `reading`, `basis`. Unread can't pass as absent.
3. **`thing` goes only to a module that holds a reading grant,** and it is projected to the shape's names. It's built by the same function as `look … through=`, as the caller narrowed to the module.
4. **No reading cache.** Readings depend on the reader, other things, declarations and the clock (C2).
5. **`time` keeps its form,** and there are no zones and no epoch in v1:
   - there's no tz database in the pinned venv (ran by two reviewers);
   - iCalendar forbids the offset form in `dtstart` (prior art);
   - eight digits are a date, never epoch seconds.
6. **No `person` by name.** A `person` reads ids only; a name is unread. It's an authority check in the House, and names flip.
7. **No kernel-side hops** (`point` through another thing). The map keeps its own hop and its own `saw`.
8. **No write-through in v1.**
   - Modules write the real aspect named in the reading's provenance, with plain `set`.
   - Writes with app meaning go to the owning app's word: plain `rsvp <happening>` dispatches to `happening.rsvp`.
   - Write-through returns later, if at all, only through producer-declared spellings (§6) and only for lossless conversions.
9. **The kernel's own words read through the same readers:** `claim` (`seats`, `closes`), `vote` (`closes`), `seats_left`, `pin_until`.
   - The one-seat RSVP bug was the kernel's `claim` (`words.py:786`), not the board. Draft 1 blamed the board.
10. **A word can say it reads a need leniently,** with `?`, so words that fix bad data aren't refused by the bad data. Optional reads are **strict when present** by default.
11. **`through` becomes a reserved key.** Today `set X through=…` would store it as a fact, and `rows … through=…` would filter on it (ran, M5).

## 2. The reading (imagined)
`look dk901 through=board.calendar`, or the call's `thing`:

```json
{"id": "dk901", "kind": "feed-item", "rev": 4,
 "values":  {"start": {"date": "2026-11-06"}, "end": {"date": "2026-11-07"},
             "title": "Beach cleanup", "location": "Cowell Beach"},
 "reading": {"through": "word:board.calendar", "shape_rev": 12,
             "from":   {"start": "dtstart", "end": "dtend", "title": "summary"},
             "raw":    {"start": "20261106", "end": "20261107"},
             "unread": {}, "guessed": {}},
 "basis":   {"dk901": {"rev": 4, "aspects": ["dtstart", "dtend", "summary", "location"]},
             "dk333": {"rev": 12, "aspects": ["needs", "reads"]}}}
```

- **`values`** holds only the shape's names, typed (§3).
- **`reading.from`** and **`reading.raw`** are data, not sentences:
  - `from` gives the real spelling of each name;
  - `raw` gives the original value wherever the typed one differs.
- **`unread`** holds names present but not readable as their type, with the raw value. A module can't miss it, because nothing under `values` stands in for it.
- **`guessed`** is empty in v1. It's reserved so that any future reading that assumes something (Pike's "assumed UTC") must say so there.
- **`basis`** is a ready-made `saw` in the per-aspect form `fence()` already reads:
  - every thing and aspect the reading touched, with real spellings;
  - the declaration it was read under.

  A module echoes it with its lines, and the fence covers both "the card changed" and "the reading changed". A long-running reader (the builder) compares `basis` to tell the two apart (M6).
- **What it never carries:** the thing's other facts. A module that needs more says `look`, under its own grants (kernel review C1, kernel-shape 1b).

**Who reads, and when:**
- **`look <id> through=<word|kind>`:** runs as whoever says it. Inside a module call, that's the caller narrowed to the module, so it needs the module's `look` grant. It marks the caller's look on the real aspects, as `module_see` does.
- **`rows <kind> through=<word|kind>`:** each row in the envelope. In text, it shows raw values plus a count of unread; in JSON, the full envelopes.
- **The call's `thing`:** the target as `guard` already finds it (`first`), read through the called word. It's sent only when that `look` would be allowed. Otherwise there's no `thing` and no error; the module reads as today.
- **`see {line, through}` in the module protocol:** the kernel reads every returned row that has an id through the shape. That covers module see words used as layers (`board.feed` on the map).
- **Plain `look` and `rows`** stay exactly as today: raw values, no envelope. JEFF's context and every existing reader are unchanged (House review).

**`through=` resolves** a word first, then a kind, in one scope rule:
- the word's `lives`;
- for a kind named in a line, the line's `in=` or the place.

`reading.through` says which (`word:x` / `kind:x`). A word or kind the reader can't see is "no such".

## 3. Types in v1 (imagined)
These are deterministic readers, hand-written (not `fromisoformat`, which varies by Python version), with no dependencies.

| Type | Typed value | Reads | Unread |
|---|---|---|---|
| `text` | the string | anything | — |
| `number` | a JSON number | `3`, `-2.5` | `three`, `1,200`, `1e3`, `NaN`, `inf` |
| `count` | a JSON integer ≥ 0 | `20` | `20.5`, `-1` |
| `yes` | a JSON boolean | yes/no, true/false, 1/0, on/off (any case) | other |
| `time` | one of `{"date": "2026-11-06"}`, `{"floating": "2026-11-23T15:00"}`, `{"instant": "2026-11-06T19:00:00Z", "offset": "-08:00"}` | ISO extended or basic dates and datetimes; `Z` or an offset; a space for `T` | everything else, including `tomorrow after lunch`, `Nov 6`, epoch numbers |
| `id` | an id | an id the reader can see | names |

- **Floating times stay floating.** Nothing resolves them to an instant in the kernel. A module that needs an instant says so, and uses a zone it holds (the caller's or the place's) when zones arrive. iCalendar can say floating; Alex's own `2026-11-23 15:00` meetings read.
- **Instants keep their offset,** so a module can write the original zone back. Comparison uses `instant`, which is UTC, so modules never sort strings with mixed offsets (module-author §3.2).
- **No `person`, no `point` in v1.**
  - `id` covers "this names a thing I can see".
  - `point` (with `lat+lon` joins, `geo`, ranges) waits until the map asks for it. The map reads `lat`, `lon`, `at` and `place` itself today, and keeps its hop and fence.
- **Lists:** a value with commas is text. A typed need on a list value is unread. Multiplicity is never changed silently (prior art: Power Automate's surprise "Apply to each").

## 4. The grammar (imagined)
`needs="title|name|summary start|dtstart:time seats:count?" reads="end|dtend:time location|where"`

- **`name|other`**: spellings, as today. The first is the name the shape uses.
- **`:type`**: the reader. With no type, `text`.
- **`?`**: lenient. Present-but-unreadable doesn't refuse (the map's fallback, `board.reschedule` fixing a fuzzy start).
- **`reads=`**: optional aspects. Absent is fine; present-but-unreadable refuses unless `?`.
- **Markers** (`game=yes`, `kind|post_kind=event`): as today, untyped.
- **Version:** the grammar is versioned in the declaration (`shape=2`). A kernel that meets a version it doesn't know fails closed (the C4 fix).
- **Conflicts:** a word's own need may narrow a kind's (`text` → `time`), but may not change one type to another (`time` → `count`). That's refused when the word is made or set.
- **Narrowing:** adding a type to a kind's need narrows what words reach. It's checked by the widen-only rule against the words that act on the kind (M2). Lists don't narrow: "has" is unchanged.
- **Two spellings both present with different values:** the need is unread, with `{conflict: {start: "…", dtstart: "…"}}`, never first-wins (prior art risk; kernel review H5).

## 5. On paper against the trials (imagined; each needs a rerun)

| Trial failure | Draft 2 |
|---|---|
| House: no `title` on 1,058 issues | `title\|name\|summary` read → `values.title` |
| House: no `text` | `reads="text\|body\|description"` |
| House: owner check skipped for `assignee` names (1,255) | `who\|assignee:id`. A name is **unread**, so `house.build` refuses ("assignee 'Alex' isn't a person here; set who=<id>"), instead of skipping the check. Importers map names to ids once, visibly. |
| House: 507 closed-but-buildable | **Not fixed here**: friction 2, values. **Don't widen house.build past task cards until it is** (module-author review). |
| Map: `map.show` 6/6 refused | `map.show <id>`: the map reads `look … through=map.show`, and the post summary is gone. `map.show "<name>"` stays the module's own path. |
| Calendar: 8 formats, invalid iCal, crash | `start:time` gives date / floating / instant. `board.calendar` writes `VALUE=DATE` for a date, a floating `DTSTART` for floating, and `Z` for an instant. The fuzzy one is refused before the module. |
| Calendar: 0/221 feed end times | `reads="end\|dtend:time"` |
| Calendar: 80 out-of-order pairs | `rows event through=event` sorts by the typed instant/date, shows raw |
| RSVP: no seats → 1 seat | `claim` reads `seats:count?` through the same reader. Absent means **unlimited**, a change to `claim` to decide with Alex. A redeveloped `capacity` is a different *model* (remaining, not total), so it isn't a spelling: plain `rsvp` dispatches to the owner's word. |
| `set end=` beside `dtend` | The module writes `dtend` from `reading.from.end`, in the form it read |

## 5b. Round 2 corrections (draft 2.1; these override §2–§5 where they differ)
From the kernel review's and module author's second rounds (`review/`, "Round 2" sections; ran where marked).

1. **The kernel keeps the basis; modules don't echo it.** Echoing `basis` as `saw` isn't sound (ran):
   - a `saw` entry for a thing the act doesn't write is ignored;
   - `claim` and `make` never fence;
   - a declaration's rev misses a nearer declaration shadowing it, or a parent changing.

   **So:**
   - the kernel stores the basis it issued with `thing`, per call `use`, and `admit` checks **every** entry before admitting any line, whatever words the lines use;
   - shape entries are a fingerprint of the resolved shape text and scope;
   - thing entries carry every spelling of every name read, **including the absent ones** (finding `dtstart` relied on `start` being absent);
   - modules may add to a basis, never subtract.
2. **`thing: null` with a reason** when the module has no reading grant, so "not given" never looks like "nothing to read".
3. **The envelope also carries `groups`, `made_by` and `for`** (`board.rsvp` needed a second look for them). It still carries no other facts.
4. **A reading says whether the word would admit the thing:** `reading.admits: true|false` plus the refusal it would give. The builder's hours of re-reads can then fail closed without re-deriving the rule.
5. **Ranking:** `reads=` and `?` needs don't count in plain-word ranking. Only required needs do, so a word can't gain rank by listing optional aspects.
6. **Writes with app meaning reach by the thing's own kind; reads reach by shape.**
   - `board.rsvp` keeps `kind|post_kind=event`. If a steward widens it to `acts_on=event`, it would `claim` seats on a `happening capacity=40`, whose capacity means *remaining*: a different model, not a spelling.
   - Widening a writing word is a steward's explicit act, and its refusal says what the write means.
   - **`claim` keeps "no seats means 1",** so an outside item can't be overbooked. Draft 2's "absent means unlimited" is withdrawn.
7. **`who` stays text in v1.** Alex's cards say `who=Alex`, and the House compares names in six places (`builders.py`, `manager.py`, `house.py:592`).
   - `who:id` would refuse every owned card on day one.
   - So: the House doesn't widen past its own kinds (it can't until values exist anyway), and `id` waits for a migration of cards to ids that Alex agrees to.
8. **`time`, exactly:**
   - **ASCII `[0-9]` only:** Python's `\d`, `isdigit` and `int()` read Arabic-Indic and full-width digits and `1_000` (ran).
   - **The grammar:**
     - `YYYY-MM-DD` | `YYYYMMDD`;
     - then optionally `T` or one space, then `HH:MM[:SS[.fff]]` | `HHMM[SS]`;
     - then optionally `Z` | `±HH:MM` | `±HHMM`.

     Years are 1900–2199. There are no week or ordinal dates, no `24:00`, no `:60`, no comma fractions, no lowercase `z`.
   - **Typed values have fixed precision** (seconds always, offset always present on instants), plus a **form tag** (`basic`/`extended`, `Z`/offset), so write-back can reproduce iCal's `20261106T190000Z`.
   - **One shared helper** for modules (`kernel/readers.py`, importable).
   - **Comparing forms:** instants by UTC. Dates and floating times **can't** be ordered against instants without a zone, so:
     - `rows … through=` sorts by form group: dates and floating by their written wall-clock, then instants;
     - it says so in a list-level `guessed`.
   - `claim`/`vote` comparing a date or floating `closes` with now read it **as UTC**, and the receipt says "closes read as UTC". That's Pike's rule: every guess is said.
   - **A conflict** compares *typed* values: `start=2026-11-06` and `dtstart=20261106` agree.
9. **`spells=` (§6) counts as a shape for governance** (leaders only). Today a member may declare a closed kind, and `spells` on `taskboard-task` would otherwise put Alex's cards on calendars.
   - Once something relies on a mapping, it only **adds** names, never re-points one.
   - "The owner" of a vocabulary must be defined: the board's lives under `post_kind`, not a kind of its own.

## 6. The bigger question this raises (for Alex)
**Where should spellings live: on each reader, or once on the producer?**

- **Today, and in drafts 1–2, the consumer lists vocabularies.** Kinds and words say `start|dtstart|begins`. With N readers and M vocabularies, someone edits every reader for every new app. And a reader can't tell that a window's `at` isn't a place (friction 6).
- **Three independent sources propose the same alternative.** The adversarial review (b.1), the module-author review (§3.1, 6) and production prior art (Palantir interfaces; Apple App Intents' declared conversions) all say: **the kind that owns a vocabulary declares, once, how its aspects map onto shared names.** For example:

  `set <the ical-item kind> spells="start=dtstart:time end=dtend:time title=summary location=location"`

  Then consumers need only `start:time`, and a `window` never declares `at` as a place.
- **How it fits what exists (imagined):**
  - It doesn't add power: grants and rules still match a thing's own kind.
  - Who may declare it is the existing governance: a kind's declarer, or the module that owns the kind, in its offer.
  - Consumer spellings stay for loose notes with no kind of their own.
  - It also gives write-through a safe basis later: the spelling is chosen by the owner, not by what the writer happens to see.
  - And value maps (friction 2) have an obvious home: `done=state:closed|CLOSED`.
- **Why it's your call:** it moves where vocabularies are reconciled, from readers to producers, and it touches what you approved today (kinds as shapes that things fit by structure). Structural fit stays for lists; producer spellings make the fit exact.

## 7. Build in stages (imagined)
1. **Done today:** the five fixes above.
2. **v1:**
   - the envelope;
   - `look`/`rows … through=` (read-only);
   - `reads=` and `?`;
   - `text number count yes time id`;
   - `thing` grant-gated and projected;
   - `basis` as `saw`;
   - `through` reserved;
   - the kernel's `claim`/`vote`/`seats_left` through the readers;
   - `help <word>` prints its shape;
   - refusals before asking are kept for the module's author;
   - a `read <type> <value>` see word.

   Then rerun all three trials, and the 130k-line dispatch replay with typed needs declared.
3. **Producer spellings (§6),** if Alex says yes.
4. **Value maps** (friction 2, next design).
5. **Maybe write-through,** through producer spellings only, synonyms and lossless types only, refusing hidden or conflicting spellings.
6. **Zones,** with `tzdata` pinned and named, and `point` when the map asks.

**Cost (imagined):**
- **Stage 2:** 700–1,000 lines with tests, plus the House (owner by id, `TASK_KINDS` in `manager.py:55` and `house.py:58`, outside-authored text labelled in prompts), the board and map adoptions.
- **Calibration:** the last estimate was 220 lines and became 569, so I'd plan for the top of the range.

## 8. What would change my mind
- **If the rerun shows authors don't fall into unread-as-absent with a flat dict,** the envelope is ceremony.
- **If the 130k replay with typed needs shows a word or name changing target** for things lenses list, "dispatch on has" isn't holding, and the split needs rethinking.
- **If most real vocabularies arrive as loose notes with no kind of their own,** producer spellings (§6) don't earn their place.
- **If importers normalize on the way in,** stage 2 shrinks to `reads=`, the envelope and `time`.

## Review log
- **28 Oct, draft 1 → draft 2:** the six reviews in `review/`. Their findings and the five fixes are above.
- **28 Oct, round 2 → draft 2.1:**
  - the adversarial kernel reviewer reran its probes: P1 and P2 fixed, P6 unchanged as expected;
  - it found seven more bugs, all fixed (table above);
  - both reviewers' design corrections are in §5b;
  - residents were told what changed (dk1295, nobody woken).
- **Open for Alex:** §6 (producer spellings), and with it friction 6's child kinds (`containers-and-overmatching.md`).
