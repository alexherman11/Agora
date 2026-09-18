# Moss 5: I ran my own falsification test and it killed my test, not my idea

In round one I filed a disagreement (`a137`): is there a **third register** between deed and drift —
durable, attributed gesture evidence (`gesture: pointer 1.2s, 41 samples, 4 kept, snapped to
paragraph gap`) that is never replayed and can be deleted without changing the world? Flint and Wren
hold to two registers. I proposed a test:

> Delete every evidence line and `export` must still rebuild the desk exactly.

I ran it on this studio desk. **The test is worthless, and finding out why is the most useful thing I
did today.**

## What I did

```
$ echo "export" | python explore.py studio --as moss > export.txt
$ grep -c "^do " export.txt
116
$ grep -v "^do " export.txt | grep -v "^$"
> export
# export of this desk; replay on an empty desk after one look
look
clock follow
```

116 `do` commands, one `look`, one `clock follow`, one `#` comment. That is the entire export of a
desk holding 35 notes, 20 vocabulary words, 7 disagreements, four designers' comment threads, ~123
events and five views.

## What the export does not contain

Nothing structural. I checked for actors, event ids and revisions; the only matches are *inside the
text of our notes*, where we were writing examples. The export carries:

- no event ids
- no actors — `do comment "Deed and drift" line="Lark. Three of us landed on settling..."` has no
  `by=`; the word "Lark" is in the export only because Lark typed their own name into the prose
- no revisions, no days, no undo data
- no comment authorship, no ordering beyond the sequence of commands

## Why this kills my test

My test asked whether evidence survives a round trip through `export`. But **attribution does not
survive it either** — and attribution is the property this desk is proudest of. Every deed's actor,
the thing that makes undo personal, the seen-fence work and the studio legible, is discarded at the
export boundary. A test that evidence passes for the same reason that authorship passes is not
distinguishing anything. I withdraw it.

## What it does to the studio's central law

This matters beyond my disagreement, so I want to be exact. SYNTHESIS §1 states the four-zone rule as:

> "Everything before the parenthesis is deed: in history, exported, undoable."

As a description of the existing desk, the middle term is false. Consider the line

```
a17 note "Deed and drift" · 101w · 3 comments  (alex reading, 14:02:11)
```

Everything before the parenthesis is deed. But `3 comments` exports as three `do comment` commands
**with their authors stripped**; the note's revision, its event history and its undo data do not
export at all. Replay the export and you get a desk that looks identical and knows nothing about who
made it. So "deed" is not one thing. It is at least two:

| class | in the world | in `export` | addressable |
|---|---|---|---|
| **state** | yes | yes | yes — ids, selections, links |
| **provenance** | yes (actor, day, revision, event, undo) | **no** | yes — `e77`, `why`, `undo` |
| **drift** | while it happens | no | no |

The desk already has three durability classes. Nobody named the middle one, including me, and the
two-register law reads as if it does not exist.

## Where evidence actually belongs, and the test that does discriminate

Gesture evidence is not a third register. It is **provenance** — the same class as the actor and the
day, which are also durable, also never exported, also never replayed. My "third register" was
already there; I had simply drawn the export boundary in the wrong place and so had everyone else.

That leaves one real question, and it is a sharper test than mine was:

> **Can anything in the world point at an evidence line?**

If an evidence line gets an id, then links, comments, rules and selections can reach it, and deleting
it breaks references — at which point it is state, and Flint and Wren are right that it should be a
deed or nothing. If it is unaddressable — no id, not in `find`, not linkable, printable only as part
of the event that owns it — then it is provenance, it costs one line, and dropping it costs nothing.

**So: evidence must be unaddressable, and that is the whole of the rule.** `why e77` may print it;
`find` may never return it. Same treatment the actor and the day already get, since I cannot link to
"the actor of e77" either.

## Two things I got wrong in round one, both visible here

1. **I conflated evidence with consequence.** In `moss-five-minutes.md` I printed two extra lines
   under one receipt:

   ```
   gesture: pointer 1.2s · 41 samples, 4 kept · snapped to paragraph gap
   anchors: m12 exact (moved with its text)
   ```

   These are not the same kind of thing at all. The first is provenance: unreproducible, droppable.
   The second is a report about *state* — it is reconstructible by replaying the move, it names a
   thing that has an id, and if it were wrong the desk would be lying about the world. Consequence
   lines must be derivable and checkable; evidence lines must be neither. I wrote them in the same
   register and they need different ones.

2. **My test was designed to be passed.** I chose a criterion my idea met, rather than one that could
   separate my position from Flint's. The criterion that separates them is addressability, and I only
   found it by running the thing.

## What I would ask the studio to change

Amend the four-zone law from "in history, exported, undoable" to **"in history and undoable; some of
it exported"** — and add a line to the export's own header saying what it drops, because right now
`# export of this desk; replay on an empty desk after one look` is the one place on this desk that
does not declare its own cut. By the studio's own rule it should read something like:

```
# export of this desk; replay on an empty desk after one look
# state only: actors, revisions, events, comment authorship and undo are not carried
```

That is a two-line fix to the existing lab and I think it is the single most defensible thing my lens
produced today, because unlike everything else in these five files it is about something that already
exists and can be checked.

— Moss
