# Proposed doc edits for kinds all the way down, 3 Nov 2026 (for Alex's yes)

> Draft by Claude. Each edit is small and targeted, and the surrounding text stays as it is. Say yes or no to each by number. Why these are needed (ran, live, 3 Nov): no kind has been declared since 29 Oct, and loose shared aspects rose from 54 to 68 while things grew from 308 to 504. Nothing a creator reads mentions the system.

## src/agora/guide/HOW-TO-BUILD-HERE.md (the builders' guide)

**1. After the `make` paragraph (line 23), add one paragraph:**
"Before making a new kind of thing, look for one that exists: `kinds`, `alike <kind>`, `aspects suggest`. Use its names for the same facts (`start`, not `starts`). If yours is new, declare it with its parts: `make kind=kind name=tool has="seats:number"`. A fact no kind names is loose, and `aspects` counts it."

**2. The lending-shelf example (line 29).**
- Old: "Make tools with `kind=tool`, a title and `seats=1`."
- New: "Declare the kind once (`make kind=kind name=tool has="seats:number"`), then make tools with `kind=tool`, a title and `seats=1`."

## src/agora/SHAPE.md (section 17, the contracts as built)

**3. After "Words reach things that fit: shapes", add one short subsection:**
"### Kinds all the way down (built 29 Oct 2026, Alex's approval of [[kinds-all-the-way-down]])
- A need may give its part a kind: `needs="title start:time"`. `has=` lists parts a thing may have, without requiring them: `has="priority:number when:time"`.
- Value kinds end in a value: the kernel's `text number time yes-no link person thing`, or a declared one (`make kind=kind name=upvote value=number`). `aliases=` gives a kind other names.
- A word whose `acts_on` is a value kind reaches anything with such a part. Guard sets `part=`: `$part` in a verb, `kv.part` for a module.
- `alike <kind>`, `aspects` and `aspects suggest` find the same kind and the loose aspects. Making a kind says which kind already has the same parts, and `set` says when a value isn't its part's kind."

## In the world (help is world data; listed here so you see it)

**4. `help kinds`:** add one sentence: "A kind says what its things are made of: needs= (must have), has= (may have), each part with its kind (start:time); see the topic Kinds and parts."

**5. A help topic, "Kinds and parts":** the same content as edit 3, written for someone typing lines rather than writing code.
