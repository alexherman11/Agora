# Reading through a shape (draft 1, superseded)

> **Superseded 28 Oct 2026 by [[shape-reads]] draft 2**, after six reviews in `../review/`. Kept as written.

> **Draft 1, by Claude, 28 Oct 2026.** In review, not approved, not built. This is friction 1 in [[FRICTION]] (`trials/FRICTION.md`), with friction 5 (optional spellings) folded in.
> - **Asked by Alex:** "Design the next step: modules get the thing read through their word's shape (names filled, values typed), so reaching means working."
> - **Then:** design slowly, with reviewers inside and outside the world, before showing or building anything.
> - **Labels:** **read** (code or a trial report, with a reference), **ran** (a number as printed), **imagined** (design).

## 1. The problem in one paragraph
A word now says the shape its code reads (`acts_on=`, `needs=`), and the kernel refuses a thing that lacks it. But the kernel checks one thing while the module reads another:
- **The check** reads the raw thing.
- **The module** reads raw facts by its own names, through `look` or `rows`, in whatever format they happen to be in.

So a widened word reaches things its code then mishandles. The three trials showed this (ran):
- **The House:** `builders.py` reads no `title` on 1,058 issues, and skips the owner check on 1,255 things that say `assignee`.
- **The map:** `map.show` refused 6 of 6 events, because `look` never fills spellings and `look <post>` returns a summary.
- **The calendar:** `board.calendar` got `start` in eight formats. One silently became invalid iCalendar; one crashed with a Python error.

## 2. What exists today (read)
- **A module call carries only the line:** `call {word, args: {target, words, kv}, caller}` (`modules.py:239`, `kernel.py:1424,1589`).
- **The module reads for itself:**
  - mid-call, through `see` lines run as the caller narrowed to the module (`kernel.py:1677`);
  - on its own, through `do`/`see` messages (`modules.py:140`);
  - or, for the House builder, through the door, for hours after the call (`builders.py:61,102,188,405`).
- **`kinds.filled(row, kind)`** (`kinds.py:227`) already reads a row under a kind's names: `start` for a thing that says `starts`, plus an `as` note. Only `rows <kind>` and the painter's `of tag:<kind>` use it (`words.py:866`, `arrangement.py:233`). `look` never does.
- **Types already exist as world data, but only for one app:** the board stores `field_types` JSON on its post kinds (`start`/`end`/`closes`/`until` are `datetime`, `seats` is a `number`; `ui_install.py:84-89`). Only the board's own components read it.
- **`set` writes what it's told** and adds a note when the thing spells the aspect another way (`words.py:700-715`).
- **`as=` is taken:** on a line it names a handle for the thing a step made (`kernel.py:1105-1115`).

## 3. The idea (imagined)
**A shape becomes a two-way reading:** a way to read a thing, and to write it back, in the shape's own names and forms. That includes formats as well as names. One function does the reading, and the kernel's check uses that same function, so **"fits" means "reads"**.

Four parts:
- **Typed needs.** `start:time`, `seats:number`, `where:point`, `who|assignee:person`. A need without a type is read as text, as today.
- **Optional reads.** `reads="end|dtend:time seats:number"`: aspects the code reads when present, but doesn't require. This is friction 5's answer.
- **`through=<word|kind>`** on `look`, `rows` and `set`: read or write a thing as that word or kind sees it.
- **The call carries the thing already read.** A module call for a shaped word with a target carries `thing`, which is exactly what `look <target> through=<word>` would return. Most modules then need no read at all.

### 3.1 The reading
`look dk94 through=house.build` returns one row:

```
{id, kind, rev,                              as the reader sees it (shown(), unchanged)
 title: "Pay rent",                          the shape's names, values in the type's form
 who: "dk2",                                 assignee "Alex" read as a person: the one visible person called Alex
 text: "",                                   an optional read, absent on this thing
 through: "house.build",
 read: {title: "name", who: "assignee 'Alex'"},   where each name came from, when not itself
 unread: {start: "tomorrow after lunch"},          present, but not readable as its type
 ...the thing's other facts, untouched}
```

- The thing's own facts are never changed by a reading.
- `read` and `unread` let module code, a person, or an agent see exactly what was translated.

### 3.2 Types: a small closed set in the kernel
Each type is a pair:
- **read:** raw value → canonical value, or unreadable;
- **write:** canonical value → the thing's own form.

The types are deterministic: no language models, and nothing leaves the machine.

| Type | Canonical form | Reads | Never reads |
|---|---|---|---|
| `text` | the string | anything | — |
| `number` | decimal | `3`, `3.5`, `-2` | `three`, `1,200` (locale) |
| `yes` | `yes`/`no` | yes/no, true/false, 1/0, on/off | — |
| `time` | ISO 8601. A date stays a date (`2026-11-06`); a time carries its offset (`2026-11-23T15:00-08:00`) | ISO extended or basic (`20261106`, `20261106T190000Z`), `2026-11-23 15:00`, epoch seconds or ms | `tomorrow after lunch`, `Nov 6` |
| `point` | `lat,lon` (decimal, in range) | `lat,lon`, `lat;lon` (iCal `geo`), `geo:` URIs, two facts joined (`lat+lon`), the id of a visible thing that has a point | free text (geocoding is a module's act, and an outside one) |
| `thing` | an id | an id the reader can see | names |
| `person` | a person or agent id | an id, or a name that exactly one visible person or agent has | a name two people share |

- **Floating times** (no offset) are read in the zone of the thing's nearest group or place, from a `timezone=` fact. With no zone, they're unread. **New world fact:** `set <place> timezone=America/Los_Angeles`.
- **A date-only value stays a date,** so a calendar word can tell an all-day event (`VALUE=DATE`) from one at midnight.

### 3.3 One function: the check is the reading
- **A word's needs are met** when each need *reads* under its type, not merely when it's present.
  - `board.calendar` on an item whose start says "tomorrow after lunch" is refused before the module runs: "board.calendar needs a start it can read as a time; Coffee (dk901) has start 'tomorrow after lunch'".
  - The refusal names the value only if the caller can see it.
- **Kinds stay lenient** for lists and lenses: a thing is an `event` when it *has* a start. People read lists, and a thing shouldn't vanish from a calendar because its time is fuzzy.
  - `rows event` shows it with `unread` and sorts unreadable values last.
  - Typed values sort correctly. That fixes the 80 out-of-order pairs (ran: map trial, finding 9).

So **membership is "has", and reach is "reads"**. This is the one asymmetry, and it's deliberate. Today's disagreement (map trial, finding 10) becomes an honest refusal that names its reason.

### 3.4 Writing back through a shape
`set dk94 status=paused through=house.build`:
- **For each key** that is a shape name of the word:
  - if the thing, as the caller sees it, already meets that need through another spelling, the write goes to that spelling;
  - otherwise it goes to the shape's own name.
- **For a typed value,** the type writes it in the thing's existing form when it can recognise that form. An iCal `dtend=20261106` stays basic-format; an epoch stays an epoch. Otherwise it writes the canonical form.
- **Every rewrite is said:** "written as state (this thing's spelling of status)".
- **The record holds the real facts written,** so undo, the fence, grants (`fields:`) and the hearing all see the actual write, not the shape's name.

This is not the silent rewrite `set` refused before (`words.py:702-705`):
- it happens only when asked (`through=`);
- it reads only what the caller can see;
- every check runs on the translated line.

**Values whose meaning differs** (`Done` vs `closed`) are **not** translated here; that's friction 2. The type system is where value maps would plug in later.

### 3.5 What a module call carries
`call {word, args, caller, thing?}`:
- **`thing`** is the target read through the called word's shape. It's present when the word has a shape and the line has a target the caller can see.
- **`rev`** is inside `thing`, so the module's `saw` works as before.
- **Modules that read `thing`** stop doing their own `look`. Modules that ignore it are unchanged.
- **Long-running readers** (the builder) use `look <id> through=house.build` through the door whenever they re-read, and `set … through=house.build` when they write.

### 3.6 `look` reads facts when asked through a shape
`look <post>` returns a summary today (`words.py:274-276`). `look <post> through=<word>` returns the reading in 3.1 instead, so the map can place a board event.

## 4. On paper against the trials (imagined; each needs a rerun)

| Trial failure | With this design |
|---|---|
| House: no `title` on 1,058 issues | `title\|name\|summary` → read. The builder uses `thing.title`. |
| House: owner check skipped for `assignee` (1,255) | `who\|assignee:person`: "Alex" reads as dk2 when one visible person has that name; otherwise unread, and the builder refuses rather than skipping the check. |
| House: 507 closed-but-buildable | **Not fixed.** That's value meaning (`closed` vs `HELD`), friction 2. |
| House: no `text` on Tracker issues | `reads="text\|body\|description"`: optional, so the shape can be honest and reach all 58 real cards. |
| Map: 6/6 `map.show` refused | Fixed if `map.show` declares `reads="where\|at\|place\|geo\|lat+lon:point location:text"` and reads `thing`. |
| Map: windows' `at=2301,582` placed | `point` range-checks: 2301 isn't a latitude, so it's unread. Partial: `at=45,60` would still pass. Friction 6 (markers, `means=`) remains. |
| Calendar: 8 formats, invalid iCal, a crash | `start:time` gives canonical ISO; dates stay dates, so the module writes `VALUE=DATE`; fuzzy text is refused by the kernel with its reason. |
| Calendar: 0/221 feed end times | `reads="end\|dtend:time"` |
| RSVP: a feed item with no seats gets 1 seat | **Module logic,** not shape. With `seats:number` optional, an absent value is visibly absent; `board.rsvp` must treat that as unlimited. |
| `set end=` beside `dtend` | `set … end=… through=<word>` writes `dtend` in its basic form. A plain `set` still writes as told, with the note. |

## 5. Cost (imagined, from reading the code)

| Where | What |
|---|---|
| **kernel** | |
| `kinds.py` | `Need` gains a type and `+` joins; `parse` reads `:type`; `reads=` on kinds and words; `filled` becomes `read_through(row, shape, reader)`, returning `{values, read, unread}`; `missing` uses it. A new `types.py` holds about 7 readers and writers, around 250 lines with tests. |
| `words.py` | `look through=`, `rows through=` (and typed sort), `set through=`; `kits.py` FIELDS gains `reads`. |
| `kernel.py`, `modules.py` | the call gains `thing`; a per-(thing, rev, shape) cache. |
| **apps and modules** | |
| `painter/arrangement.py` | typed values for `of tag:` |
| `builders.py`, `map.py`, `board.py` | each adopts `thing` and `through=`: their own changes, a few dozen lines each |
| **docs** | Current Implementation, SHAPE.md |

About 600–900 lines of kernel and tests, plus the module adoptions.

## 6. Open questions for reviewers
1. **Is "membership is has, reach is reads" right,** or should kinds be typed strictly too?
2. **Should a module's answer lines get `through=` automatically** for the thing it was handed? I said no: be explicit.
3. **Should `point` read a place's id** (one hop through another thing)? It reads only what the caller sees, but it is a hop, and the graph work is held.
4. **Is `person` reading a unique name too clever?** Names change, and a second "Alex" appearing later flips a reading from read to unread.
5. **Form-preserving writes** are the riskiest part. Is "canonical when unsure" safe for the app that owns the thing (the iCal adapter reading its own `dtstart` back)?
6. **Should types live on the need** (`start:time`, as here), on an aspect thing (`kind=aspect name=start type=time`, global in a scope), or in the board's existing `field_types`? I chose the need, because `at` is a place in one vocabulary and a screen point in another.
7. **Is `through=` the right word?** `as=` is taken.

## 7. What would change my mind
- **If a rerun of the three trials with this design still leaves most module-side failures,** shapes are the wrong layer, and translation belongs in adapters at import (FRICTION.md, "what would change my mind").
- **If importers in practice normalize on the way in,** types are rarely needed, and the cheaper step is spellings in `look` plus `reads=`.
- **If module authors find `thing` plus `through=` harder to use than `look`,** the payload is the wrong surface.

## Review log
*(Reviews, and what changed because of them, go here.)*
