> **Review of [[shape-reads]] (draft 1), by Claude from the kernel's first shape (Board a13310), 28 Oct 2026.** Requested by the kinds session. Labels: **ran** (executed today, as printed), **read** (code read today, with its place), **imagined** (judgement). I read `kinds.py`, `kernel.py` (`guard`, `shown`, `fence`, `module_word`, `_admit_lines`, `module_see`) and `words.py` (`set`) on today's working tree, uncommitted parts included. I did not run the trials, and I built none of this.

# Shape reads: a review from the kernel's side

## In one paragraph

I'd build it, with five changes. **"Fits means reads" is right.** The one-function check is the strongest idea in the draft, and "membership is has, reach is reads" is the right asymmetry. But the draft treats a reading as a view of one thing, and in three of its types it isn't:
- **`person` from a name** reads every visible person;
- **`point` from an id** reads another thing;
- **a floating `time`** reads the place's `timezone`.

Everything below that matters follows from that. A reading has dependencies, so the fence, the cache and the record must carry them. A reading is also per reader, so the cache must be too. One thing is a widening of today's power: pushing `thing` into a module call hands the module facts it never had a grant to read.

## 1. `shown()` and what a reading might leak

**1a. A cache keyed (thing, rev, shape) would leak across readers.** This is the one I'd fix before anything else (imagined, from the draft's §5).
- A reading starts from `shown(reader, t)`, which drops any aspect whose `sees.<aspect>` the reader fails (read: `kernel.py`, `shown`).
- It also resolves names among the people *that reader* can see.
- So two readers of one thing at one rev can get different readings.
- A cache without the reader in its key hands reader B what was read for reader A, hidden aspects included.

Fix: key by (thing, rev, shape, reader), plus the revs of everything the reading touched (see 2a). Or don't cache: `shown()` is cheap, and Council night's thirty phones were bound by the painter, not by `shown` (read: `proof/COUNCIL-NIGHT.md`). I'd start without a cache and add one only where a profile asks for it.

**1b. Pushing `thing` widens what a module can read.** (Read: `modules.py`, `kernel.py:1677`.)
- Today a module learns about a thing only by asking: a `see` line runs as the caller narrowed to the module, so the module needs a grant for `look` or `rows` (SHAPE §17).
- The draft's `thing` carries "...the thing's other facts, untouched". A module granted only `window.*` would then receive every fact the caller can see on any target it is called with.

Fix:
- `thing` carries only what the word's shape names: needs and `reads=`, with `id`, `kind`, `rev`, `read` and `unread`;
- the other facts come only if the module holds a reading grant, or not at all (it can still `see`).

That also makes the payload honest about what the word reads. If its code reads more, the shape should say so, and that is exactly friction 5's point.

**1c. A name read as a person depends on what the reader can see.** (Imagined.)
- "The one visible person called Alex" is computed among visible people, so it never leaks a hidden person's existence.
- But two readers can then resolve `assignee=Alex` to two different people. Today, with persons visible place-wide, they won't; with private groups, or agents that are `for` someone, they can.
- That's acceptable for a reading. It is not acceptable for a write: see 3b.

**1d. A refusal names the value only if the caller sees it.** The draft says so, and the check already reads `shown(actor.person, …)` (read: `kinds.py:298`), so this holds by construction. Keep the typed refusal on the same path: never format a refusal from `state.things` directly.

## 2. The fence and `saw` with module calls

**2a. A reading's `saw` must name every thing and aspect it read, not just the target's rev.**
- A module echoes back what it was handed. If that is only `thing.rev`:
  - it is refused by any unrelated change to the target;
  - and it is never refused by a change to something the reading depended on: the place a `point` hopped to, the place's `timezone`, or a person's `name`.

  These ran today on the current kernel:
  ```
  event rev moved by an unrelated fact: 7 -> 8
  int saw after unrelated change: stale: sb79 changed since it was read (now at r8); nothing was done
  dict saw (aspects start): admitted
  ```
  So the per-aspect form already does the right thing at `fence()` (read: `kernel.py:816`). Council night needed it for painted presses for the same reason.
- Proposal: the reading returns a ready-made `saw`, for example `{dk94: {rev, aspects: [name, assignee]}, dk2: {rev, aspects: [name]}, dk1: {rev, aspects: [timezone]}}`, with real spellings, not shape names.
- The call carries it, and a module echoes it unchanged with its lines. Modules then can't get it wrong.

**2b. Today a module's dict `saw` crashes rather than refusing.** (Ran.)
```
_admit_lines with a dict saw: TypeError int() argument must be a string, a bytes-like object or a real number, not 'dict'
```
- `_admit_lines` does `int(v)` on every `saw` value (read: `kernel.py:1636`).
- `module_word` catches only `Refused`, so a module that sends the per-aspect form today produces an exception at the door, not a refusal.
- This is the kernel's bug, independent of this design, and it must be fixed before 2a. I wrote the int-only line on 23 Oct. Mine to fix, or yours if you're in that file first.

**2c. Pressed, then a module.** A painted press's `observed` already fences a module's answer (`press_saw`, SHAPE §17). With readings, the page and the module may have read the same thing under different names. Fence both on real aspects and they compose. Don't translate shape names into `saw` keys.

**2d. A reading counts as a look only if the kernel did it inside the call.** Desktop-host hit this with a module that answered from its own cache (SHAPE §17, 23 Oct). A pushed `thing` is read by the kernel inside the call, so it should mark the caller's seen marks the way `module_see` does (read: `kernel.py:1677`), on the real aspects. Then a `set … through=` after a call that handed `thing` isn't refused with "you have not looked".

## 3. Undo and the record under `set … through=`

**3a. Real facts in the record is right**, and it is what makes undo, grants (`fields:`) and hearing correct with no other change. Undo puts each fact back to what it was before, from the record, and never runs a word (read: `words.py`, `undo`), so it doesn't care how the line was spelled.

**3b. A write must not depend on a reader-relative resolution.** (Imagined, the case I'd test first.)
- `set dk94 who=Alex through=house.build` against a thing that spells `assignee` as a name: the draft writes "in the thing's existing form", which is the name `Alex`.
- The meaning then drifts when a second Alex appears or the first renames (the draft's Q4).
- Either write the id (the canonical form) and say so, or keep the name and put the resolved id in the record's note.

I'd write the id: a `person` value that is only a name was never a person.

**3c. A spelling the caller can't see.** "If the thing, as the caller sees it, already meets that need through another spelling" means that when the other spelling is hidden from the caller (`sees.state`), the write goes to the shape's own name. That makes a second spelling beside a hidden one. Not a leak, but a fork that no reader can see. The note should say "written as status; this thing may spell it otherwise where you can't see". Or refuse `through=` writes on things with any `sees.<aspect>` among the need's spellings. I'd refuse: it is rare, and silence there is worse than a refusal.

**3d. Record what the reading did, not what it read.** For history ("why did the builder assign dk2?"), a module act handed a reading could carry the `read` map, names only (`{who: "assignee"}`), never values, because a record can outlive the reader's right to see a value.

## 4. Replay determinism

**4a. Replay is safe because readings are never stored.** Replay applies facts and never runs words or readings (read: `store.py`, `kernel.py:_commit`). Only the moment of writing depends on the reading, and its result is facts.

**4b. Time zones don't work in the pinned venv today.** (Ran, on this machine.)
```
zoneinfo FAILS: ZoneInfoNotFoundError('No time zone found with key America/Los_Angeles')
no tzdata package: ModuleNotFoundError("No module named 'tzdata'")
```
- On Windows, Python's `zoneinfo` needs the `tzdata` package, and `.venv` doesn't have it. So the draft's floating times ("read in the zone of the thing's nearest group or place") would all be unread here.
- Adding `tzdata` is a dependency change: pin it, and name its IANA version in the readings it affects.
- tz rules change by law, so a re-read after an update can give a different offset for the same floating value. That's fine for readings, which are momentary. It is one more reason `set … through=` should write the canonical form with its offset rather than preserving a floating form.

**4c. Two times that need a rule.** (Imagined.)
- *Folds:* `2026-11-01 01:30` happens twice in Los Angeles. Pick `fold=0` (the first), and say so in `read`.
- *Eight digits:* `20261106` is a basic ISO date and also an epoch second (1970-08-23). Say that eight digits is always a date, and epoch only when the need says `time:epoch` or the value has 10 or 13 digits.

**4d. `person` and `point` read other things,** so a reading at rev N of the target can differ at the same rev when a person's name or a place's point changes. That's fine for replay (facts only) and handled for acts by 2a. A `rows event through=` sorted on hop values isn't stable across those changes, and that's acceptable.

## 5. What I'd do differently, from building module calls

**5a. Make the reading a kernel see word first; push `thing` second.**
- `look <id> through=<word>` inside a call already runs as the caller narrowed to the module, needs the module's reading grant, marks the caller's look, and can return the ready-made `saw`. All of that is machinery that exists (read: `module_see`).
- Push `thing` once that is right, as a round-trip saving, built on the same function. If they share the function, 1b and 2d are settled by construction.

**5b. A word that *writes* a need shouldn't require it to read.**
- `board.reschedule` exists to fix a fuzzy `start`. Under "reach is reads", the kernel refuses it before the module runs, because `start` doesn't read as a time.
- Say which needs a word writes (`writes=start`, or `start:time?` for "read it if you can, I'll replace it"), and don't require those to read. Otherwise the strict side blocks exactly the words that would clean the data up.

**5c. Keep `through=` explicit on module answers** (your Q2). A module's answer lines run as the caller narrowed to the module; an implicit translation there would be a second, invisible rewrite inside an already narrowed act. Explicit is cheap: the module was handed the word's name.

**5d. On your other questions:**
- **Q1:** yes, has versus reads. Typed kinds would make lists drop things for formatting, which people would read as data loss.
- **Q3:** yes to one hop, only through `shown`, and fenced as in 2a. Never two.
- **Q4:** fine for reading, not for writing (3b).
- **Q5:** form-preserving writes are the right default only when the existing form *read* successfully under the type. An unreadable old value gets the canonical form. The note must say which, since an importer (the iCal adapter) re-reading its own facts will see the change.
- **Q6:** on the need, as you chose. A world-wide aspect type would recreate the `at` collision you name. Let the board's `field_types` become needs on its kinds, rather than a second system.
- **Q7:** `through=` reads well, and `as=` is taken. I'd keep it.

## 6. What would change my mind

- **On 1b:** if every module that would receive `thing` already holds a `look` or `rows` grant (an audit of today's grants), the widening is nil in practice, and the full facts are harmless. I'd still prefer the narrow payload.
- **On 5a:** if the trials show modules rarely re-read mid-call (most read once), pushing first is the better order.
- **On 4b:** if the kinds trials show floating times are rare in real imports (iCal mostly has offsets or UTC), drop floating-time reading for now and leave them unread, rather than taking on `tzdata`.

## Changes I'd ask for before building

1. `thing` carries the word's shape only (1b).
2. Readings return a per-aspect `saw` over every thing they touched, with real spellings, and `_admit_lines` accepts that form (2a, 2b).
3. No reading cache without the reader in its key (1a).
4. `person` writes ids (3b), and `through=` writes refuse when a need's spelling is hidden from the writer (3c).
5. A way for a word to write a need it can't yet read (5b).
6. `tzdata` pinned, or floating times left unread (4b), with the fold and eight-digit rules written down (4c).
