# Adversarial kernel review of shape-reads.md draft 1, by a review agent for Claude, 28 Oct 2026.

> **What this is.** A review of [[shape-reads]] (`research/kinds-lab/shape-reads.md`), grounded in the kernel as it stands in the working tree today. No source file was edited and the live world was not touched.
> - **Read:** the draft; `trials/FRICTION.md` and the three `trials/*/FINDINGS.md`; `kernel/kinds.py` (all); `kernel/kernel.py` (guard, shown, named, resolve_name, plain_verb, may, fence, _commit, reaches, step, the module call sites, admit, _admit_lines, module_see); `kernel/words.py` (look, set_, claim, vote, rows, verb, RESERVED); `kernel/modules.py`; `kernel/painter.py` `saw_of`; `kernel/refusals.py` header; `kernel/kits.py`; `kernel/dictionary.py` `bind`; `kernel/world_words.py` `utc`; `painter/arrangement.py` 151–242; `modules/house/builders.py`; `modules/map/map.py` (position, point_of, w_show, WORDS); `community-app/board/board.py` (stamp, rsvp, calendar); `SHAPE.md` §17; `fresh-words-reach-kinds.md` §6 and its cost table.
> - **Ran:** two scratch scripts on fresh temporary worlds (`scratchpad/review-kernel/probe.py`, `probe2.py`), plus one venv check. Numbers are quoted as printed.
> - **Labels:** **read** (file:line), **ran** (as printed), **imagined** (design reasoning or a scenario not executed).

## Verdict in five lines
1. The goal is right, and two parts are sound: a closed, deterministic set of value readers, and the log never being rewritten by a reading.
2. Four parts are unsafe as written: the `thing` payload over-shares and skips module read grants; the cache key leaks between readers; "reach is reads" with today's ranking makes `done` and names pick **another** word or thing silently instead of refusing; unparseable stored needs already fail **open**, and the grammar change multiplies that.
3. Two parts are too clever for v1: `person` resolving names (it sits inside an authority check), and write-through with form-preserving writes.
4. The time type can't work on Alex's machine as specified (no tz database in the pinned venv), and the one line the draft proposes for zones is refused by `set`.
5. The cost is about 2× the estimate. A smaller first step fixes most of the trial failures (section "(a)" below).

---

## Critical (fix in the design before anything is built)

### C1. The call's `thing` hands modules reads their grants never allowed, and more than the shape (read; imagined consequence)
- **Today a module must hold a grant to read.** A module's `see` line runs as the caller narrowed to the module (`kernel.py:1677-1681`), and `may` for a module actor requires `_granted(actor.module, word)` as well as the caller's right (`kernel.py:795-799`). A module with no `look`/`rows` grant reads nothing.
- **The draft's `thing` is computed by the kernel and pushed**, so it arrives whether or not the module holds `look` (`shape-reads.md` §3.5). That is a new read path with no grant check.
- **And it carries everything,** "…the thing's other facts, untouched" (§3.1). For a post, `shown()` adds caller-specific derived facts (read: `kernel.py:460-478`):
  - `contacts` (other people's phone numbers, when the caller is a leader);
  - `your_vote` and `you_liked` (the caller's **sealed** choices);
  - `claimed_by` (names in claim order).
- **Why it matters:** FRICTION §7 already found `map.show` sending a private meeting's title to Nominatim. Pushing whole rows to every shaped word widens exactly that surface.
- **Change:** send `thing` only when the module holds a read grant that would have let it `look` the target; project it to the shape's names (needs plus `reads=`) and their provenance, nothing else. A module that wants more reads it, as today, under its grants.

### C2. The cache key `(thing, rev, shape)` has no reader in it, and a thing's `rev` doesn't cover what a reading depends on (read; imagined consequence)
A reading is a function of much more than the thing's facts:

| A reading depends on | Changes the thing's `rev`? | Where (read) |
|---|---|---|
| **who reads** (`sees`, `sees.<aspect>`, `sees_when`, `visibility_of` parents) | no | `kernel.py:426-442, 456-458` |
| group membership and leadership (the `leaders`/`group:` rules) | no (facts on the group) | `kernel.py:411-415` |
| the clock (`pin_until`; `made`/`changed` times) | no | `kernel.py:479-484` |
| the word's or kind's declaration (`word-set … needs=`, a kind widened) | no | `kinds.py:112-153` |
| a hopped place's point (`point` reading `at=<id>`) | no | draft §3.2 |
| who has a name (`person`), and renames | no | draft §3.2 |
| a group's `timezone=` | no | draft §3.2 |

- **As written, one reader's reading is served to another** (a per-field-hidden `lat` or a `sees=me` value crosses readers), and every non-rev dependency goes stale silently.
- **Change:** no cross-call cache in v1. The trials show no need: `rows` 27–122 ms, `actions` 9–27 ms (FRICTION, ran by the trial agents). If a cache is ever needed, key it the way `Kinds._fresh` already does, on the log length (`kinds.py:101-106`), **plus the reader**, and never cache `shown()` itself (it reads the clock).

### C3. "Reach is reads" plus today's ranking turns refusals into silent re-dispatch (ran the mechanism; imagined with types)
The draft promises that today's disagreement "becomes an honest refusal that names its reason" (§3.3). The ranking code does the opposite: a word that doesn't reach is dropped from the candidates, and something else answers.

- **Plain words (ran, `probe2.py`):** with `cal.done needs="title start"` and `task.done needs=title`:

  ```
  done <item with start>    -> ~ cal.done, one act [r6]
  done <item without start> -> ~ task.done, one act [r7]
  ```

  `plain_verb` ranks only the words whose shape reaches (`kernel.py:599-616`; `kinds.py:313-327`). Under the draft "reaches" becomes "reads", so an item whose `start` is *present but fuzzy* (still listed on the calendar, by the lenient rule) silently runs `task.done`. No refusal, no reason.
- **Names (ran, `probe.py` P3):** two things called "Beach cleanup", one with a `start`:

  ```
  cal 'Beach cleanup' -> ok set sh79 [r6] · exported=yes
  ```

  `resolve_name` keeps only the things the word reaches and, left with one, takes it without asking (`kernel.py:561-566`). Under the draft, a person who sees both in their calendar lens gets the *other* one's calendar file.
- **`actions <thing>`** also uses `reaches` (`kinds.py:525`), so the right-click list will omit words the lens's buttons still offer.
- **Change: dispatch and name resolution stay on "has" (exactly what lists and lenses use); only admission (`check_word` in `guard`) adds "reads" and refuses with the reason.** Then the lens, `actions`, plain words and names all agree on *which* word and thing, and the only new outcome is a refusal that names the unreadable value. This is the draft's stated intent; the code path it named doesn't give it.

### C4. A stored need the kernel can't parse already makes a word reach everything, and the grammar change multiplies that (ran)
- **Ran (`probe.py` P2):** a kit word carrying `needs="start:time"` was accepted by `take`, then acted on a thing with no start at all:

  ```
  take: ok take [r3] · 1 new definitions in Shapes
  ping on a thing with no start: ok set sh79 [r5] · pinged=yes
  same needs typed by verb: refused: start:time is not a need: …
  ```

- **Why (read):**
  - `word_shape` swallows a parse error and returns `needs=[]` (`kinds.py:265-268`), so `_lacks` finds nothing lacking.
  - `take` never validates `needs`/`acts_on`/`extends` (`kits.py:26-83, 145-191`); `verb` and `word-set` do (`words.py:930-933`, `dictionary.py:46-49`).
  - `shape()` also swallows (`kinds.py:146-149`). For a kind that fails closed by accident; for a word's own needs it fails open.
- **Why the draft makes it worse:** `start:time`, `lat+lon` and `reads=` are all unparseable by today's `NAME` (`kinds.py:25`). Any skew (a kit from a newer world, a rollback of the kernel, kdesk restarting an older working tree) turns every typed word into a word with no shape.
- **Change, before any grammar grows:** an unparseable stored shape refuses everything ("ping's shape can't be read by this kernel; nothing was done"); `take` validates shapes like `verb`; the grammar carries a version.

---

## High

### H1. Refusal text reaches the steward, including private titles today and private values under the draft (ran)
- **Ran (`probe.py` P1):** Bea's `sees=me` note "Therapy with Dr K" (Alex can't see it: `False`); a shaped verb refused it; Alex's `refusals all` then contained:

  ```
  → remind acts on things with start; Therapy with Dr K (sh79, a note) has no start
  ```

- **Read:** `check_word` names the target's title (`kinds.py:306, 310-311`); refusals are kept in `keep/refusals.jsonl`, and "a steward sees everyone's" (`refusals.py:15`). `forget` doesn't reach that file.
- **The draft adds values:** "Coffee (dk901) has start 'tomorrow after lunch'" (§3.3). "Names the value only if the caller can see it" protects the caller, not the log.
- **Change:** a refusal kept for others carries the word, the need and the thing's id only; the title and value go only in the reply to the caller. Fix the existing title leak at the same time.

### H2. The fence checks the shape's names, not the facts that changed (read; imagined consequence)
- **Painted gestures** report read aspects by desk name: `prop:start` becomes the kernel aspect `start` (`kernel/painter.py:92-112`). A row filled under `event` shows `start` though the fact is `starts`. The dict-`saw` fence then checks `last_seq(t, "start")`, which is 0 forever (`kernel.py:826-832`), so a change to `starts` after the paint is never stale. **This hole exists today** for `of tag:<kind>` lenses (`arrangement.py:231-233`); the draft makes every read go through it.
- **Module answers on a painted press** are fenced on `st.kv` keys before `set_` runs (`kernel.py:1668-1669`). With `set … end=… through=…` that fences `end` and `through`, not `dtend`, so two leaders pressing one painted button both write.
- **Change:** a reading's provenance (`read: {start: "starts"}`) is the translation table for the fence: `saw_of` and the press fence map shape names to real aspects. Translate a through-line once, before `may`, `guard`, `once`, the press fence, `reaches(fields=)`, `validate_write` and `fence`; not inside `set_`.

### H3. `person` reading a name sits inside an authority check (read; ran for cost; imagined for the sign-up scenario)
- **The House's owner check compares names,** not ids: `task.get('who') not in (caller.get('name'), 'JEFF')` (`builders.py:200-203`), with `task_owner`/`basis` stored from `who` and compared later (`builders.py:214, 248-249, 383, 451-453`). Handing the builder `who: "dk2"` breaks every comparison unless the builder is rewritten to ids. That's a change to authority code, not "a few dozen lines" of adoption.
- **Resolution is per reader and moves without the task changing:**
  - in Seabright (200 people, invite sign-up) anyone joining as "Alex" turns every `assignee: Alex` unread, so the builder refuses all of them, and `assert_owned` aborts running builds whose `basis.who` was `dk2`;
  - if dk2 is ever renamed, the remaining "Alex" inherits the ownership reading.
- **Agents:** `k.name(agent)` is "agent for Alex" (`kernel.py:300-303`), so it is unclear whether "JEFF" resolves at all. Today 'JEFF' is accepted literally.
- **Cost (ran, `probe.py` P5):** one `named()` over about 3,000 things took 1.4 ms, "x 2,174 rows = 3.1 s". A typed `rows task` would need a name index invalidated on renames, joins and visibility changes.
- **Change:** in v1, `person` reads ids only; a name is unread. The builder compares ids, and refuses (rather than skips the check) when the owner is a name. A name-to-person mapping, if wanted, is an explicit `set … who=<id>` someone makes once, not a reading redone at every read.

### H4. The time type, as specified, can't run here and isn't deterministic across machines (ran; read)
- **No tz database (ran):** in `C:/Projects/Agora4/.venv` (Python 3.12.10), `zoneinfo.ZoneInfo('America/Los_Angeles')` raised `ZoneInfoNotFoundError('No time zone found with key America/Los_Angeles')`, and `tzdata` is not installed. The floating-time rule needs a new dependency, and its answers then depend on the tzdata version. The Seabright box will have a different one, and future DST rule changes move readings of future events.
- **The proposed line is refused:** `set <place> timezone=…` hits `set_`'s refusal for reserved kinds, and `place` and `group` are reserved (`words.py:220, 699-700`). That needs a new word or a `group` field: an uncounted kernel change.
- **A group's zone re-dates every floating event retroactively**, with no record touching them, so no rev changes (see C2). It's also a lever: a group's leaders move every member's floating times by hours.
- **DST:** US DST ends **1 Nov 2026**, so `2026-11-01T01:30` floating is ambiguous. The trials' events are in early November.
- **Ambiguous digits:** `20261106` is both ISO basic and epoch seconds. `test_shapes.py` uses `start=1`, which epoch-reading makes "1970-01-01T00:00:01Z", readable. `fromisoformat` grew basic-format support in Python 3.11, and the kernel's own `utc()` uses it (`world_words.py:7-14`); a reader built on it varies with the interpreter.
- **Floating times are valid iCalendar** (`DTSTART:20261123T150000`). Converting them to an offset loses meaning; refusing them refuses Alex's own 100 meetings (`2026-11-23 15:00`).
- **Change:** a v1 `time` with no zones and no epoch. It reads ISO extended or basic date, datetime with `Z`/offset, and floating datetime; the canonical form keeps which of the three it is (`date`, `instant`, `floating`), and the module decides. A hand-written parser, not `fromisoformat`.

### H5. Write-through reopens what Alex already decided against, and its guarantees fail quietly (read; imagined)
- **History:** "Why no silent rewrite … A rewrite would also confirm an aspect the actor can't see, and two people can resolve it differently" (`fresh-words-reach-kinds.md:112`; `SHAPE.md:429`). The 27 Oct read-time fill and spelling-aware `set` were removed on 28 Oct (`SHAPE.md:438, 442`). `through=` makes the rewrite explicit, but the divergence remains:
  - **A hidden spelling:** `dtend` with `sees.dtend=person:<owner>`. A leader writing through the shape doesn't see it, so the write goes to `end`. The thing now has a visible `end` and a hidden `dtend`. `Need.met` takes the first name present (`kinds.py:48-56`), so **every** shape reader, the owner included, now reads the leader's `end`, while the owner's app reads raw `dtend`.
  - **Two spellings present and different:** the write goes to the first met, and the other stays stale. The draft doesn't say. It should refuse (or read as `unread: conflict`).
  - **Spelling chosen by presence, not vocabulary:** a feed item that lacks `dtend` gets `end`, though its app only ever reads `dtend`. The thing's own kind knows its vocabulary; the thing's present facts don't.
- **Form-preserving writes can't always preserve:**
  - a datetime can't be written into a basic-date `dtend` (all-day);
  - an all-day date can't go into epoch without becoming a UTC midnight, which is another day in Los Angeles;
  - RFC 5545 has no offset form in basic notation.
  
  "Canonical when unsure" then writes ISO into a field the owning adapter parses as basic.
- **Person write-back has no answer:** a name loses identity, and an id breaks the Tracker that shows names.
- **Two claims in §3.4 don't hold as written:**
  - **Grants:** `reaches(…, fields=st.kv)` is `set_`'s first line (`words.py:695`; `kernel.py:934-936`). Unless `through` is popped before it, a module with `fields:status` is refused for `through`. Unless the translation happens before it, `fields:` checks shape names.
  - **Hearing:** a happening's `text` is the line's words (`kernel.py:872-875`), so hearers see `status=… through=…`, not `state=…`.
- **Change:** no write-through in v1. A module writes the real aspect named in the reading's provenance (`thing.read.status == "state"`, so it says `set X state=paused`). That is plain `set`, with every existing check unchanged, and the module, which holds the raw value, chooses the form.

### H6. The kernel's own words read raw facts too, and the draft misattributes one trial failure (read)
- **"A feed item with no seats gets 1 seat" is the kernel's `claim`,** not `board.rsvp`: `seats = int(a.get("seats", 1)) … else 1` (`words.py:786`). The draft files it under "Module logic" (§4).
- **`claim` and `vote` disagree on `closes` today:**
  - `claim` compares strings, `now.strftime("%Y-%m-%dT%H:%MZ") >= str(closes)` (`words.py:789`);
  - `vote` parses with `utc()`, which **refuses** a date-only or floating `closes` (`words.py:816`, `world_words.py:10-11`).
  
  On a feed item with `closes=20261106T190000Z`, the string compare (`'-'` < `'1'`) means sign-up never closes (imagined from the code).
- **"Every check runs on the translated line"** covers line-level checks, not what kernel words read inside. `claim`, `vote`, `shown()`'s `seats_left` (`kernel.py:477-478`) and `pin_until` (`kernel.py:481-484`) all need the same `time`/`number` readers, or the kernel stays the least consistent reader in the world.

---

## Medium

### M1. "Fits means reads" contradicts the code's names, and the call sites don't share one scope (read)
- In the code, `kinds.fits()` **is** membership (`kinds.py:164-178`). §3 says "fits means reads"; §3.3 says membership is "has". Implementing both means splitting `Need.met` into has/reads, and every caller must pick correctly:

| Call site | Function today | Draft wants | Scope it resolves kinds in (read) |
|---|---|---|---|
| `guard` → `check_word` | `_lacks` → `fits`/`missing` | reads | the word's `lives` (`kinds.py:280`) |
| `plain_verb`, `resolve_name`, `actions` | `reaches` | reads (but see C3: should be has) | the word's `lives` |
| `rows <kind>` | `fits` + `filled` | has (+ typed values) | the line's `in=`/group (`words.py:854-866`) |
| painter `of tag:` | `fits` + `filled` | has | **the place only**, no group passed (`arrangement.py:231-233`) |
| `kinds <thing>`, `look`'s "also" | `kinds_of` | has | the thing's first group (`kinds.py:566`, `words.py:301`) |
| `mark` | `missing` | has | the thing's first group (`kinds.py:480`) |
| `set`'s spelling note | `spelled_otherwise` | has | the thing's first group (`words.py:712`) |
| `through=<kind>` | — | reads | **unspecified** |

- With group-scoped kinds (leaders may declare them), "the same thing read through `event`" differs by call site. `through=<kind>` resolved at the thing's group would let a group's leaders redirect a module's write-through in their group (`start` onto `closes`): a confused deputy (imagined).
- **Change:** one scope rule (the word's `lives`, or the place for a kind named in a line), written once in `kinds.py`, used by the painter too.

### M2. Typing a kind's need narrows reach, and the widen-only rule doesn't know (read; imagined)
- Adding `:time` to `event`'s `start` refuses fuzzy things for every word with `acts_on=event`. That is the narrowing the widen-only rule exists to stop (`kinds.py:395-400`), but `_narrower` compares names and values only (`:426-438`). `Need.__eq__`/`merged` dedupe by `(names, values)`, so a parent's `start` and a child's `start:time` both survive, and conflicting types (`start:time` vs `start:text`) have no rule.
- **Own-kind things skip needs entirely** (`kinds.py:169-172`). Either typed reach applies to them (a behaviour change for an app's own things) or it doesn't (the calendar crash survives for own-kind events with a hand-`set` fuzzy start). The draft must pick.

### M3. The reading overlays the fact namespace (read)
- `read`, `unread` and `through` sit beside the thing's facts (§3.1). Real facts use those names: `test_missing_words.py:240` sets `unread=`, and a mail adapter's natural field is `unread`.
- Canonical values **replace** raw ones under the shape's names (`start: "2026-11-06"` for a raw `20261106`), so module code can't tell raw from read. A module that then writes `set X start=<thing.start>` (without through) rewrites the form.
- **Change:** nest it: `thing = {id, kind, rev, shape: {values, read, unread}, …only the projected raw facts}`.

### M4. Several trial cases never get a `thing` (read)
- **`map.show` has no target in the kernel's sense:** its `takes` is `<thing|name|lat,lon>`, so `takes_id` is None (`kernel.py:732-738`) and `step` folds any id into words (`kernel.py:1142-1145`). The draft sends `thing` only "when … the line has a target".
- **Names aren't resolved for module words** (`name_target`'s `names_a_thing` is only for `<id>` or verbs: `kernel.py:681-682`). So `map.show "Beach cleanup"`, Alex's usual way, stays the module's own `look`.
- **The point hop loses its fence:** `map.py` today records the hopped place's rev in `saw` (`map.py:222-226`). A kernel-side hop inside `point` returns one `rev`, so a module's write is no longer fenced on the place moving.
- **Change:** define the target as `guard`'s `first` (`kernel.py:391`). Have readings carry their dependency set (see "(b)").

### M5. `through=` is an ordinary key today (ran)
- **Ran (`probe.py` P6):**

  ```
  rows event: 1 event | rows event through=cal: 0 events: none you can see has through=cal; …
  ok set sh81 [r7] · status=paused, through=house.build
  ```

  `rows` treats unknown keys as filters (`words.py:867`), and `set` writes `through` as a fact.
- A module updated before the kernel, or a kernel rolled back, silently stores `through` facts and filters lists to nothing. It must be reserved (`words.py:222-228`) in the same change, and `look`/`rows`/`set` must pop it.

### M6. Long-running readers see readings change with no fact changing (read; imagined)
- The builder re-reads for hours and aborts when `basis` (`title text acceptance who`) differs (`builders.py:390-394, 451-453`). Under the draft, a steward's `word-set house.build needs=…` (a new spelling ahead of `title`), a new person named like the assignee, or a place moving changes the reading. The run then aborts with "task instructions or owner changed", though the card is untouched and its `rev` is the same.
- The reading needs to say what it was read under (the word entry's rev, and the dependency revs), so a reader can tell "the card changed" from "the reading changed".

---

## Low
- **`number`** (imagined): say whether `1e3`, `NaN` and `inf` read (Python `float` takes all three; `map.num` rejects only NaN, `map.py:195-200`). `seats` is an integer everywhere it's used (`board.py:116`, `kernel.py:477`, `words.py:786`), so `3.5` reading as a number doesn't help those readers.
- **`yes` vs markers:** `game=true` reads as yes under the type but doesn't meet the marker `game=yes` (`kinds.py:54`). That gives two mechanisms for one idea.
- **`point`:** GeoJSON order (`lon,lat`) is indistinguishable in range. The draft is honest that `at=45,60` still passes.
- **`through=<word>` on a word or kind the reader can't see** must refuse as "no such", or the provenance reveals a hidden shape. `Kinds.decl` doesn't check visibility (`kinds.py:112-125`).
- **Dispatch and replay:** a replay of the log is unaffected, because records store the resolved entry and rewritten head (`kernel.py:1139-1141, 1175`), and rules and verbs bind heads to ids (`dictionary.py:118-128`). But a button's `does=` line is not bound (`kernel.py:1098`), so it re-dispatches. And the dispatch-equivalence replay that gated the shapes build (`SHAPE.md:419`, 130,101 lines) should be rerun with types declared and its differences listed. That is the honest test of C3.

---

## Cost (read; imagined estimate)
**Calibration:** the last design estimated `kinds.py` at about 220 lines (`fresh-words-reach-kinds.md:141`). It is 569, with 415 lines of `test_shapes.py` (ran: `wc -l`).

What §5 doesn't count:

| Missing from the draft's table | Why (read) |
|---|---|
| grammar: `NAME`, `Need` with type and joins, `__eq__`/`merged`, `_narrower`/`_dropped` with types | `kinds.py:25, 38-91, 426-443` |
| `reads=` in `verb`, `word-set`, module offers and refresh, `validate_decl`, kits **and kit validation that doesn't exist yet** | `words.py:930-933`, `dictionary.py:41-49`, `kernel.py:1749-1784`, `kits.py:11-17, 145-191` |
| fail-closed shape parsing (C4) | `kinds.py:146-149, 265-268` |
| reserving `through` in look/rows/set/make | `words.py:222-228, 867` |
| translation at one point, before `may`/`guard`/`once`/press fence/`reaches`/`validate_write`/`fence`, in all four paths (step, verb_note, `_verb_with_modules`, `_admit_lines`) | `kernel.py:1155-1163, 1343-1351, 1414-1416, 1659-1669`; `words.py:695-739` |
| fence translation for painted `saw` | `kernel/painter.py:92-112` |
| a time parser with three canonical forms, form-preserving writers per form, and tests; the zone path adds a dependency | ran: no tzdata |
| a writable `timezone` on place/group | `words.py:699-700` |
| a name index for `person`, or dropping it | ran: 3.1 s per 2,174 rows |
| `point` hop with a cycle guard and dependency revs | `map.py:208-240` does this today with depth < 2 |
| refusal redaction for the kept log | `refusals.py:15`, `kinds.py:306` |
| kernel words reading typed (`claim`, `vote`, `seats_left`) | `words.py:786-792, 816`; `kernel.py:477` |
| painter typed sort and one kind scope | `arrangement.py:231-242` |
| the builder's owner check moved from names to ids; the manager path | `builders.py:200-203, 214, 248-249, 383, 451-453` |
| rerunning three trials and the 130k-line dispatch replay | `SHAPE.md:419` |
| docs: Current Implementation, SHAPE §17 module table, `modules.py` header, help topics | — |

**My estimate (imagined):** 1,500–2,500 lines with tests for the whole draft, before module adoptions. The (a) version below is roughly 350–550.

---

## (a) The simplest version that still fixes most trial failures (imagined)
1. **`reads=`** (optional aspects with spellings), validated everywhere `needs=` is, **fail-closed** on parse.
2. **`look <id> through=<word|kind>` and `rows … through=`, read-only:** spellings plus one type, `time` (no zones, no epoch; three canonical forms). `through` is reserved, and the reading is nested (M3).
3. **The module call carries `thing`** only if the module holds a read grant, projected to the shape's names, with `read`/`unread` provenance and the revs it depended on. Target = `guard`'s `first`.
4. **Dispatch and names stay on "has"; `guard` adds "reads"** and refuses with the reason, kept redacted.
5. **No write-through, no `person`-by-name, no kernel-side `point` hop, no cache.** Modules write the real aspect named in provenance; the map keeps its own hop and `saw`.
6. **The painter's `by` sort uses the `time` reader** for a `tag:` kind's typed name.

Against the trials (imagined, each needs a rerun):

| Trial failure | Fixed by (a)? |
|---|---|
| House title on 1,058 issues | yes (`title\|name\|summary` read) |
| House text | yes (`reads=`) |
| owner check skipped for `assignee` | the builder sees `assignee` raw and must fail closed (module change) |
| `closed` vs held | no: values (friction 2), as in the draft |
| `map.show` 6 of 6 refused | yes, for ids; names stay the module's |
| calendar: eight formats, invalid iCal, crash, 0 of 221 end times, out-of-order sort | yes (floating is kept floating; iCal can say it) |
| RSVP seat | no (the kernel's `claim`); say so |
| `set end=` beside `dtend` | the module writes `dtend` from provenance |

## (b) A better mechanism, even if it overturns parts of the draft (imagined)
**1. Put the translation on the producer's kind, not on each consumer's word.**
- The draft makes every consuming word list every vocabulary: `where|at|place|geo|lat+lon:point`. That gives N consumers × M vocabularies, each consumer misreading windows' `at` (friction 6).
- Instead, the kind that *owns* a vocabulary says once how it spells the common names: `set <ical-item kind> spells="start=dtstart:time end=dtend:time title=summary where=location:text"`. Its declarer (steward or leader, the existing governance) makes it, and it's the 27 Oct aspect-entry idea scoped per source kind, so homonyms can't cross: a `window` never declares `at` as a point; a `spot` does.
- Consumers then need only canonical names, and their shapes stay short.
- Writes route by the own kind's declared spelling, not by what the caller happens to see, which removes H5's divergence and gives write-through a safe basis later.
- It is FRICTION's "translation in adapters", but as a reading: the log is never rewritten, and an importer that normalises simply declares nothing.

**2. A reading carries its basis.** Every reading returns `basis = {thing: rev, …}`: the target, the word entry or kind declaration (and its `spells=`), each hopped or resolved thing. That one value is:
- the module's `saw` (so the fence covers the hop and a shape change);
- the cache key if one is ever needed (with the reader);
- what a long-running reader compares, to tell "the card changed" from "the reading changed" (M6).

**3. Dispatch on has, admit on reads** (C3). This is the one-line rule that makes the asymmetry honest instead of silent.

## What would change my mind
- **On C3:** a run of the dispatch-equivalence replay with typed needs that shows no word and no name changing target for things the lenses list.
- **On H3:** if person names were unique and immutable by construction in every world (the entry service refusing duplicates), `person`-by-name would be a lookup, not a guess; it would still need an index.
- **On H5:** a write-through implementation where the spelling is chosen by the thing's own kind (b.1), the translation happens once before every check, and hidden spellings refuse rather than diverge. Then I'd accept it, in a second step.
- **On (b.1):** if the trial reruns showed most vocabularies arrive with no kind of their own (loose notes from many sources), consumer-side spellings would earn their place.

## Not verified
- The board, map and House modules running end to end with any of this; painted presses through the door.
- The Seabright box's Python and tzdata versions.
- Whether persons can be renamed or share names through the entry service (the sign-up scenario in H3 is imagined from "invite sign-up, 200 people").
- Whether any live module lacks a `look` grant today. C1 is about the mechanism, not a counted instance.
- The other reviewers' notes in this folder. I didn't read them, to stay independent.

---

## Round 2: draft 2 and the five fixes (28 Oct 2026, same reviewer)

> - **Read:** draft 2 of `shape-reads.md`; the working tree's `kinds.py` (`Unreadable`, `spellings_of`, `check_word`'s `kept`), `kernel.py` (`Refused`, `run`/`_run`, `fence`, `check_participants`, `admit`, `_module_saw`, `_admit_lines`, `_verb_with_modules`), `kits.py` `validate`/`take`, `words.py` `claim`, `house.py` and `manager.py` where they read `who`.
> - **Ran:** `probe.py` again, and new `probe3.py`, `probe4.py`, `probe5.py` (same scratchpad folder), on fresh temporary worlds.
> - No source edited, no live world.

### R0. The three reruns (ran, as printed)

| Probe | Round 1 | Now |
|---|---|---|
| **P1** refusal leak, by id | `in alex's refusals: True` | `in alex's refusals: False` |
| **P2** kit `needs="start:time"` | `take: ok take [r3]` … `ping on a thing with no start: ok set sh79 [r5] · pinged=yes` | `take: refused: a word in this kit has a shape this kernel can't read: start:time is not a need: …`; `ping on a thing with no start: refused: nothing answers to 'ping' here; did you mean pin?` |
| **P6** `through` as a key | `rows event through=cal: 0 events: none you can see has through=cal`; `ok set sh81 [r7] · status=paused, through=house.build` | unchanged, as expected (only the draft reserves it) |

P3, P4 and P5 printed the same as round 1, as expected: today's code is all "has" (P5 was `1.6 ms … 3.5 s`, timing noise).

### R1. The fixes: what still leaks, and what's new

**F1 (High, existing, ran): one member's `seats=²` breaks every lens and list that can see it.**
- **Ran (`probe3.py` R7, `probe4.py`):**

  ```
  alex rows note raised: ValueError invalid literal for int() with base 10: '²'
  alex look raised: ValueError invalid literal for int() with base 10: '²'
  after: Alex's lens raised ValueError invalid literal for int() with base 10: '²'
  ```

- **Why (read):** `shown()` does `str(a.get("seats")).isdigit()` then `int(...)` (`kernel.py:477-478`), and `'²'.isdigit()` is `True`. Every reader's `rows`, `look` and component lens (`compile_view` calls `shown` on every thing, `arrangement.py:154-157`) raises. `claim` has the same pair (`words.py:786`).
- Not caused by today's fixes, but it is the `count` reader draft 2 puts under `seats_left`, and it's a one-line fix (ASCII digits) worth landing with the five.

**F2 (High, ran): `take` checks that a shape parses, not who may declare it or on what.**
- **Ran (`probe3.py` R3):**

  ```
  make : refused: said is one of the kernel's own kinds; what it is can't be widened or extended
  take : ok take [r3] · 1 new definitions in Shapes
  rows said includes Bea's note: True
  ```

- **Read:** `kits.validate` now parses `needs` (`kits.py:73-83`), but `take` never calls `kinds.validate_decl` (`kits.py:156-204`). That skips the kernel-kinds guard, the leader check, cycles and unknown parents.
- Kits are the cross-world path, so a steward taking a stranger's kit puts a member's note into JEFF's `rows said`. That's the chats trial's finding 1, re-opened.
- **Change:** `take` runs `validate_decl` on every `kind` definition, and `check_acts_on` on words, exactly as `make`/`verb`/`word-set` do.

**F3 (High, ran): an unreadable shape fails closed for the word, but a plain word goes sideways.**
- **Ran (`probe3.py` R2):** `cal.done`'s stored needs set to `title start:time` (as a rolled-back kernel would see a newer world):

  ```
  before     : done -> ~ cal.done, one act [r6]
  unreadable : cal.done -> refused: cal.done's shape can't be read by this kernel (needs=title start:time); …
  unreadable : done -> ~ task.done, one act [r8]
  ```

- **Read:** `Unreadable` sits in `_lacks`, so `reaches` returns None (`kinds.py:362-370`), and `plain_verb` silently ranks the next word (`kernel.py` ranking, unchanged). The C4 fix makes the word honest and dispatch dishonest.
- Draft 2's `shape=2` versioning will produce exactly this on any older kernel.
- **Change:** a word with an unreadable shape stays a candidate in `plain_verb` (it might reach). If it would win or tie, refuse with its reason. Never fall through past it.

**F4 (Medium, ran): the H1 fix covers one message, not the log.**
- **Ran (`probe3.py` R1):**

  ```
  bea by id  : … | in alex's log: False
  bea by name: … | in alex's log: True
  bea mark   : refused: a event needs start; Therapy with Dr K has none, so it can't be marked one | in alex's log: True
  ```

- **Why (read):**
  - the log keeps the caller's whole **line** (`refusals.py:56, 77-78`), so a name typed for a private thing is kept;
  - `mark`'s refusals name the title with no `kept` (`kinds.py:539`);
  - `_verb_with_modules` re-wraps refusals as strings, `raise stop(x, str(exc))` (`kernel.py:1435, 1471, 1486`), which drops `kept`;
  - a pressed button's label and `does=` line go into `kept` (`kernel.py:1076-1077`).
- **Change:** decide what the steward's log may hold. The line can't be kept raw for a non-steward's refusal; keep the word, ids and the refusal's `kept`, and keep the raw line only for the caller's own view. Make `kept` survive re-wrapping (`stop(..., kept=)`).

**F5 (Medium, ran): `_module_saw` made `{rev}` a weaker fence than `rev`.**
- **Ran (`probe5.py`):** a card read at r2; someone sets `lane=Done`; the module writes `note`:

  ```
  {'sh77': 2} -> stale: sh77 changed since it was read (now at r3); nothing was done
  {'sh77': {'rev': 2}} -> admitted
  ```

- **Why (read):** a dict without `aspects` reaches `fence`'s per-aspect path, which then checks only the aspects written (`kernel.py:829-841`). `check_participants` treats missing aspects as `['*']` (`kernel.py:861`). A module author who writes the dict form, thinking it means the same as the bare rev, gets a silently weaker fence.
- **Change:** in `_module_saw`, missing `aspects` becomes `['*']`.

**F6 (Medium, ran/read): `spellings_of` is too wide in scope and too narrow in source.**
- **Too wide (ran, `probe3.py` R4):** a kind declared **in a group** joining `title|order` makes a place thing's title-only paint stale on an `order` change:

  ```
  fence on a title-only paint after an order change: stale: sh78 changed since it was painted (title, r5); …
  spellings_of('title') = ['order', 'title']
  ```

  It unions every declaration in every scope (`kinds.py:268-284`), so a group's leaders can make presses across the whole place refuse more often. It fails safe (stale, never admitted) but costs availability.
- **Too narrow (read):** it reads kind declarations only, not words' own `needs`. Draft 2 puts spellings on words (`needs="title|name|summary start|dtstart:time"`), and those won't widen the fence. It also `continue`s past a declaration it can't parse (`kinds.py:276-279`), so typed (v2) declarations would drop out of the fence on a v1 kernel: the C4 pattern, inside the fence.
- **Change:** this is an interim. The sound version is the reading's own basis (below), scoped to what was actually read through.

**F7 (Low, read): an unreadable kind can't be repaired once used.**
`_expand` still swallows a parse error into `[]` (`kinds.py:465-473`), so `_narrower(old, new)` sees "before" as empty, and any readable `needs=` the steward sets is "narrower" and refused while a word or lens names the kind (`kinds.py:475-487, 444-449`). The refusal on the word says "a steward can word-set … to fix it"; for a kind there is no such path. **Change:** an `Unreadable` "before" is never narrower than anything.

### R2. Draft 2, attacked

**Q1. Does "dispatch on has, admit on reads" remove the C3 swaps, names included?** Mostly yes, for typed values (imagined; read against `kernel.py` `plain_verb`, `resolve_name`). A present-but-fuzzy value still meets "has", so the same word and thing are chosen, and `guard` refuses with the reason. A name shared by two things that both have the aspect now asks rather than picking. Four ways a silent swap survives:
1. **Unreadable shapes** (F3, ran).
2. **Producer `spells=` changes "has"**, so a steward's declaration moves dispatch for every thing of that kind. That's intended, but it belongs in the 130k replay before and after.
3. **Unspecified rank inputs:** whether `reads=` and `?` needs count in `-len(needs)` ranking. If they do, a word gains rank by listing optional aspects. Say they don't.
4. **A silent downgrade, not a swap:** no `thing` when the module lacks a grant ("no thing and no error", §2). A module written for `thing` then silently reads raw again. Send `thing: null` with a reason, so the author's code can't confuse "not given" with "nothing to read".

**Q2. Is `basis` a sound `saw`? No, not with today's fence (ran; read).**
- **Ran (`probe3.py` R5):** with the declaration's rev in `saw` and the declaration changed since, `set <thing> note=ok` printed `ok set sh79 [r6] · note=ok`.
- **Why (read):**
  - `fence` is called per **written** thing (`words.py:739`), so `saw` entries for things the act doesn't write are ignored, unless marked `participant` (`kernel.py:856-861`).
  - `_module_saw` keeps only `rev` and `aspects`, so a module can't mark one (`kernel.py:1655`).
- **Not every word fences:** `claim` and `make` don't call `fence` at all (`words.py:779-800`, `584-662`). So `board.rsvp`'s `answer([claim, make], event)` saw is decorative today, and draft 2's "the fence covers both the card changed and the reading changed" holds only for `set`-like words.
- **A declaration's rev doesn't capture what the reading resolved:**
  - a nearer-scope declaration made later shadows it;
  - forgetting it falls back to the place's;
  - an `extends` parent changes.
  
  `decl()` resolves nearest-first (`kinds.py:138-151`), so the reading changes while dk333's rev doesn't. A word's shape also lives on its **dictionary entry** (`needs`, `reads`, `acts_on`) plus the kind chain, not on one declaration.
- **Found spellings only miss absences:** a reading of `start|dtstart` that found `dtstart` depends on `start` being absent.
- **Change:** the kernel keeps the basis it issued with `thing`, per call `use`, and `admit` checks **every** entry before admitting any line, whatever words the lines use.
  - Entries for shapes are a fingerprint of the resolved shape text and its scope, not a declaration's rev.
  - Entries for things carry every spelling of every name read, plus `sees.<aspect>` for each.
  - Modules may add to the basis, never subtract.
  - That makes "the reading changed" a kernel guarantee rather than an echo the module must get right.

**Q3. Holes in the `time` type as specified.**
- **Digits must be ASCII (ran):** Python's `\d` and `int()` accept other scripts:

  ```
  '٢٠٢٦١١٠٦' True True 20261106
  '２０２６１１０６' True True 20261106
  '²' False True int: ValueError
  1000 20 1000.0 nan        (int('1_000'), int(' 20 '), float('1e3'), float('nan'))
  ```

  A "hand parser" built on `\d`, `isdigit` or `int()` reads Arabic-Indic and full-width digits as dates, crashes on `²` (F1), and takes `1_000` and padded spaces as counts. Specify `[0-9]` and no `int()` on unchecked text.
- **Mixed forms can't be sorted or compared without a zone (imagined):**
  - §5 claims the 80 out-of-order pairs are fixed by sorting on "the typed instant/date". A floating `15:00` and an instant `19:00Z` have no order without a zone, so any order is a guess, and `guessed` is meant to be empty in v1.
  - The same holds for `claim`/`vote` comparing a date or floating `closes` with now. The board treats a date as UTC midnight (`board.py:16-17`); `vote` refuses it (`world_words.py:10-11`).
  - **Change:** say the rule (for example floating and dates as UTC, recorded in `guessed`), or sort by form groups and refuse comparisons.
- **The ISO subset is unstated:** week and ordinal dates, reduced precision (`T19`, `T1900`), `24:00`, leap second `:60`, comma fractions, `-00:00` (RFC 3339 "unknown offset"), lowercase `z`, `+05` and `+0530`, years `0000` and out of range. State an exact grammar. A hand parser that hasn't been fuzzed will crash some reader (F1 is the precedent).
- **Write-back needs the form, not just the offset:** `20261106T190000Z` and `2026-11-06T19:00:00+00:00` are both `{instant, offset:+00:00}`. Writing back "in the form it read" needs `reading.raw` (good, it's there) or a form tag; the iCal case needs basic notation and `Z`.
- **Conflicts must compare typed values:** `start=2026-11-06` and `dtstart=20261106` are the same date with different raw values. Comparing raw would refuse them as a conflict.

**Q4. Producer-side `spells=` (§6): what breaks, and the governance it needs (imagined; read where cited).**
- **Who may declare:**
  - Members can make closed kind declarations today; only shaped ones need a leader (`kinds.py:419`, the early return when not shaped).
  - So `spells=` must count as a shape for governance. Otherwise a member declares `kind=kind name=taskboard-task spells="start=when"`, and Alex's cards (whose `when` is a card timestamp) join every calendar.
  - With one declaration per name per scope, the member's declaration also squats the name.
- **Remaps aren't widenings:** changing `start=dtstart` to `start=created` changes meaning for every consumer, and the widen-only rule only knows wider/narrower. **Rule:** once relied on, a mapping only adds names, never re-points one.
- **"Own kind" isn't who owns a vocabulary:**
  - Any member can `make kind=ical-item`.
  - Two modules can both be granted `make only=kind:x`.
  - The board's events are `kind=post` with `post_kind=event`, so own-kind keying can't reach the board's vocabulary at all without special-casing `post_kind`.
  
  Say what "owns" means: a declaration made by the steward or leader, or the one module whose grant names the kind, unique.
- **Scope:** keyed on the thing's kind, the natural scope is the thing's group. Draft 2 §2 resolves kinds by "the line's `in=` or the place". Pick one; group leaders re-pointing spells in their group should be the deliberate answer, not an accident.
- **Precedence with consumer spellings:** producer spells must win and suppress consumer spellings for that kind. Otherwise both match, and the conflict rule refuses.
- **Everything downstream must learn it:** `filled` (rows and painter), `spellings_of` (fence), the basis, kits (`FIELDS["kind"]` plus validation), `kinds <thing>`/`actions` explanations, and the replay.

### R3. Other holes in draft 2
- **`who|assignee:id` breaks the House on day one (read).** `who=` holds a **name** by design: "a task card given to it (`who=` its name)" (`house.py:10`). The wake path matches `who` against agent names and parses `who=` in hearing text (`house.py:597-602`); `manager.py:64` and `builders.py:200-203` compare names. Under `:id`, every real card's `who=Alex` is unread, and `house.build` refuses Alex's own cards.
  - **Change:** the builder compares `who`/`assignee` to the caller's name **or** id itself (module logic, text type), and fails closed on anything else.
  - Moving cards to ids is a separate migration with the task board UI and wake path.
- **The conflict rule refuses non-synonyms.** Spellings like `title|name|summary` and `text|body|description` are often different fields in one vocabulary (a short name and a long title). "Unread on conflict" would refuse such cards outright.
  - **Change:** conflict only for typed needs. For `text`, use first-wins with `reading.from` naming the one used and `reading.also` the others present.
- **Typing `event` vs widen-only.** §4 says adding a type to a used kind is checked by widen-only, but §5's calendar sort relies on `through=event` being typed. Once any word acts on `event`, that is refused. Either put the type on the word (`through=board.calendar`), or decide that adding a type to a kind narrows admission only and is allowed.
- **Own-kind things and typed admission are still undecided** (round 1 M2). `fits` skips needs for a thing's own kind (`kinds.py:195-198`).
- **`claim` absent = unlimited** changes a documented default: "1 when it says none" (`words.py:780-781`), with help "a public-comment slot, a carpool seat". Any single-claim thing made without `seats` becomes open to all. Keep 1 as the default, and let the board's event word supply its own.
- **`through=` resolves words before kinds.** `verb` is `may=leaders` (ran: `refused: verb is for leaders of Shapes`), so a group's leader can make a bare verb `event` that shadows `through=event` for lines in that group. **Change:** `through=kind:event` / `through=word:x`, with no bare form.

### R4. What I'd change before stage 2 (short list)
1. **Land with the five fixes:**
   - ASCII digits in `shown`/`claim` (F1);
   - `take` runs `validate_decl` (F2);
   - unreadable shapes stay dispatch candidates (F3);
   - `_module_saw` defaults to `['*']` (F5);
   - an `Unreadable` "before" is never narrower (F7).
2. **Decide the refusals log's privacy model (F4)** rather than patching messages one by one.
3. **A kernel-held basis, checked in `admit` for every entry** (Q2). Shape fingerprints, not declaration revs.
4. **A written `time` grammar** (ASCII, exact ISO subset), a stated mixed-form order, and a fuzz test over the readers.
5. **No `:id` on the House's `who`.**
6. **Conflicts for typed needs only.**
7. **`through=kind:`/`word:` prefixes.**
8. **`spells=` counts as a shape** for governance, with add-only remaps and a defined owner.

**What would change my mind on Q2:** if every module write in practice were a `set` on the thing read (no `claim`, no `make`, no second thing), the echo-based `saw` would be nearly enough. `board.rsvp` is already a counterexample.

**Not verified (round 2):** the fixes' own new tests (I didn't run the suite); the House wake path running; any producer `spells=` (nothing is built).
