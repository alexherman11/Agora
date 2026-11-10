# Trial: "show it on the map": three calendars, three vocabularies

> Run 28 Oct 2026 by a trial agent for Claude, on a copy of the live desktop log; written here by Claude from its report (the agent could not write files).
> - Scripts and last output: `trial.py`, `data.py`, `freeze.py`, `explore.py`, `explore2.py`, `trial-output.txt` in this folder.
> - Scratch worlds: the session scratchpad (`trial-map/`).
> - The real `board.py` `call` and `map.py` functions ran in-process, with the network stubbed, so geocoding and the ground name search never ran.
> - Labels: **ran**, **read**, **imagined**.

## Set-up (ran)
On a copy of the live log:
- 50 spots;
- 300 board events;
- 300 iCal-style feed items (`summary`, `dtstart`, `dtend`, `location`, `uid`), made by Sable, a member;
- 100 of Alex's private meetings (`when`, `where`).

## Answers in brief
- **One calendar lens:** possible, but only the steward can make it, and only by working around two kernel rules. It shows no feed end times, doesn't sort in time order, and picks up real task cards.
- **The map:** mostly no.
- **RSVP / calendar export:** one `word-set` widens them, but it isn't safe.
- **Timings:** fine at this scale.

## Friction, highest severity first

### 1. The board's events are on no calendar or map today (ran)
- `event` is the board's own post-kind declaration (dk333), which has no `needs`, so it is closed. Board events are `kind=post`.
- `rows event` returns nothing, and the Events map layer shows 0.
- Opening dk333 with `set dk333 needs="title start"` is refused as "need more", because a lens names it. Opening a closed kind widens it, so this is misclassified (read: `kinds.py:360-386`).

### 2. A second declaration with the same name narrows a kind silently (ran)
- `make kind=kind name=event needs="title start seats"` was accepted and cut `rows event` from 732 to 182.
- The later declaration wins, and a new `make` skips the widen-only check (read: `kinds.py:112-125, 336-354`).
- It is also the only way the steward could open `event` at all.

### 3. The map can't place most events
- **What it reads:** `lat`/`lon`, `at`/`place` and `location` only, never `where` or `geo` (read: `map.py:208-256`).
- **Placed:** the Events layer placed 99 of 733 rows, all of them board events (ran).
- **Free text:** goes to Nominatim, at most 3 new names per call, cached in memory only (read: `map.py:52, 249-250`).
- **A `located` kind** (`needs="at|place|where"`) lifts it to 157 of 197 placed. But it also "places" 5 windows, whose `at=2301,582` is a screen position (ran).
- **A `lat|geo` spelling** fails 69 of 69: a spelling can't split `lat;lon`.
- **`map.show`** on one thing from each source was refused 6 of 6, while a spot works. The map's words go through `look`, which never fills spellings.

### 4. `look <post>` returns a summary, not the post
It drops title, start, place and seats, so the map can never place a board event (ran; read: `words.py:248-251, 275-276`).

### 5. Privacy
`map.show "Review lease with the landlord"`, a private meeting, sent that title to the stubbed Nominatim, and refused `map.show <id>` calls sent the id (ran; read: `map.py:279-286`).

### 6. Spellings reach module code in formats it can't read (ran)
`board.calendar` reads the filled `rows event`, so feed and meeting starts arrive in their own formats:
- An all-day feed date came out as `DTSTART:20261106` without `;VALUE=DATE`, which is invalid RFC 5545, silently.
- A floating time with a time zone, and Alex's `2026-11-23 15:00`, were refused.
- `tomorrow after lunch` produced a Python `Invalid isoformat` error.
- The kernel's shape check reads the raw thing while the module reads it filled, so the two disagree.
- dk333 already says `start` is a datetime (`field_types`), but nothing reads that.

### 7. Widening to all three vocabularies pulls in task cards (ran)
- It adds 32 real taskboard cards, whose `when` is a card timestamp.
- Keeping them out needs a marker, which `event` refused as narrowing, so it took a new kind name (`happening`).
- Only a steward can declare any of this; Sable was refused three ways.

### 8. Optional aspects can't have spellings (ran)
- `end|dtend` is refused, so 221 feed items have `dtend` and the lens shows 0 ends.
- `set … end=` was then accepted right beside an existing `dtend`, leaving two spellings that disagree.

### 9. Eight time formats in one column (ran)
- Sorting by start puts the 61 iCal all-day dates first (the painter sorts numbers before text), leaving 80 neighbouring pairs out of time order.
- Pages hold at most 100 rows.

### 10. `meeting extends=event` makes every event with a place a meeting (ran)
- `rows meeting` returned 733 things, including 300 board posts.
- A meeting with no `when` is listed as an event, yet a word that `acts_on=event` refuses it.

### 11. The same aspect name means different things across sources (ran)
- `status`: `CANCELLED` (feed) vs `cancelled` (meetings), so a filter finds 24 of 37 cancelled items.
- `when` becomes a calendar spelling, so `set <task> start=` is refused.
- `at` is both a screen position and a place.
- `set`'s suggested line leaves an ISO `dtstart` beside an iCal `dtend` on the same item.

### 12. RSVP (ran)
- In the copied world, `board.rsvp` has no shape until the board module re-offers its words.
- After widening, the board's own code RSVPs a cancelled feed item.
- It gives a feed item 1 seat because it has none, so the second person is told it's "taken".

### 13. Governance
A member's private lens freezes a steward's kind, and the refusal names a lens the steward can't see (ran: `freeze.py`; read: `kinds.py:388-401`).

### 14. Names don't pick among recurring things
- `done "Dentist"` matches 17 things, and `board.rsvp "Beach cleanup"` matches 8 (ran).
- Minor: `actions` prints "as what it hasn:" (`kinds.py:466-467`).
- `post` allows 5 a day per person, so the trial moved the kernel clock to load 300.

## Fixes
- **Need source:** findings 1, 2, 4, 5, 6, 8 and 10.
- **Work today with world data alone:**
  - a `located` kind as the map layer's reading;
  - `word-set` widening;
  - `word-set map.show acts_on=located`.

## What would change my mind
- **If importers normalize on the way in** (ISO `start`/`end`, plus `at`/`lat`/`lon`), findings 6, 8 and 9 shrink to "write a good importer".
- **If the map read things through `rows located`,** the map gap would mostly be world data plus geocoding.
- **Running the real ground search** would change the counts in finding 3, not its structure.

## Timings (ran; 1,945 things; medians)

| Reading | Time |
|---|---|
| `rows event` | 35.8 ms |
| `rows event exact=yes` | 1.6 ms |
| Lens compile, `of tag:event` | 36.0 ms |
| Lens compile, `of tag:happening limit 100` | 25.2 ms |
| `actions <thing>` | 8.8–9.9 ms |
| `kinds <thing>` | 1.6 ms |
| `done <id>` | 3.1 ms |
| `done "Dentist"` (by name) | 6.5 ms |
| `set` with spelling check | 1.8 ms |
| 10 × (`set` + `rows event`) | 375 ms |
| `map.py placed()`, 554 rows | 398 ms |
| Reopen the world (3,000 records) | 905 ms |
