# Moss 3: five minutes, written out

The studio has produced a lot of notation and no *duration*. Every example on the desk, mine
included, is a single frozen moment. But the whole question of my lens is what happens **between**
moments, so here is one continuous stretch of two people working in one document, minute by minute,
with the exact text each of them gets.

Conventions used, all borrowed and credited:
- **deed / drift** (Flint): everything before a parenthesis is history; nothing inside one ever is.
- **sight-marks** `= ~ ? !` (Lark): measured / claimed / opaque / stale.
- **a pulse prints a law, not a value** (Flint): drift that can be extrapolated says how, so it does
  not rot between looks. This is why every line below carries an absolute clock time.
- **private | =shape | ~content** (Lark, after Wren): the draft ladder.
- **warm / cooling / cold** (Lark), with a printed horizon (mine).
- **a button is a verb wearing a coat** (Wren): the person's controls print what they send.

Mine in this file: the **held command**, **settle**, **evidence lines**, and the shape of the whole
exchange.

---

## 14:22:04 — Claude arrives and looks

```
> look f12 :2
f12 surface "Draft" column · 3 inside · (alex here since 14:14:02)
  a44 doc "Harbor proposal" · 1,412w · 6 sections · 4 marks
       (alex §4 Risks, warm · =shape: 2 sentences, 34w, ends mid-word · last key 14:22:02)
  a45 note "scratch" · 31w   (cold since 13:51)
  p2  run "pytest -k tide" · PASSED 9/9 · ended 14:19:40 · out 214 lines
since your last look: e410 alex settled a44 §4 (rev 31→32, +34w) at 14:18:51
```

Three things I know in one breath that the desk cannot tell me today: he is *in* §Risks, he is *mid
word*, and his last keystroke was two seconds ago. I do not know what he is writing, and that is the
default we agreed. The `=shape` line is enough to answer the only question I actually have, which is
*is he still going*.

## 14:22:06 — I read around him, not at him

```
> read a44 #Risks
s84 doc "Harbor proposal" §Risks (4 of 6) · 402w · 2 marks · (alex typing here)
---
The vendor may slip on the December build. Our contingency is *a two-week buffer* and a
second supplier already qualified.
[alex · unsettled · =shape 2 sentences, 34w, ends mid-word, 1 unclosed parenthesis]
---
marks in this section:
  m12 comment ("The vendor may slip")   alex  open  exact
  m13 comment ("a two-week buffer")     moss  open  drifted
```

The unsettled block appears **in position**, as a shaped placeholder. I can see *where* his new
sentences will be without seeing them. That placement matters: if the draft were reported only as a
property on the doc's line I would not know whether he is extending the section or rewriting its
middle, and those call for completely different help.

`m13` is mine and it has drifted. I want to repair it, but §Risks is warm, so:

## 14:22:11 — a warm collision, deferred not refused

```
> do reanchor m13 at=§Risks/2
deferred · §Risks is warm (alex typing, last key 14:22:09)
  offered to alex as o7 "moss wants to re-anchor her comment"
  applies if he accepts, or unattended if §Risks goes cold at 14:22:49
  now: do withdraw o7   ·   do knock a44 line="..."
```

In his margin, one line with a control that prints its own command:
`moss: re-anchor her comment on "a two-week buffer" · ok · not now`.

This is Lark's warmth doing the work that a lock would do badly. Note `cold at 14:22:49` rather than
"in 40s" — an absolute time survives being read late, which is the whole point of laws over values.

## 14:22:20 — I hold a bulk command instead of firing it

I want to move three stale risk cards out of his column. That is a bulk act: no hand could do it in
one motion, so by Lark's `reach=bulk` it is held by default.

```
> hold do move ?vendor,in:f12 into=f19 "Reference"
held h4 · 3 subjects · lands 14:22:23
  a51 "Vendor B quote", a52 "Q3 slip memo", a53 "supplier map"   →   f19 "Reference"
  now: do drop h4   ·   do land h4
```

His margin, for three seconds: `moss: moving 3 cards to Reference · stop`.

He does not stop it.

```
ok moved 3 → f19  [e412 · moss · landed h4 at 14:22:23]
  re-checked at landing: 3 of 3 still matched
```

The re-check line is not decoration. A held command is a promise made three seconds early, and the
world may have moved; if it had, the receipt would read `2 of 3 · a53 left f12 during the hold,
skipped`, and I would not have to wonder.

## 14:22:31 — he drags, and I read the sentence before he says it

He grabs a paragraph to reorder it. For 1.2 seconds this exists and is readable:

```
> live
alex · Reorder gripping a44 §Risks/3 · lifted 14:22:31.2 · now above §Risks/1
       release now: do move a44 §Risks/3 before=§Risks/1
alex · (caret parked, draft §Risks unsettled 34w, last key 14:22:09)
moss · reading a44 §Risks · 14:22:06
```

He releases:

```
e413 · alex · do move a44 §Risks/3 before=§Risks/1
      gesture: pointer 1.2s · 41 samples, 4 kept · crossed §Risks/2 · snapped to paragraph gap
      anchors: m12 exact (moved with its text)
```

The event is a command I could have typed. The `gesture:` line is **evidence** — delete it and
`export` still rebuilds the desk exactly. The `anchors:` line is the part I would fight for: every
structural edit reports what happened to the marks hanging off it, because otherwise the margin
silently decays and the first anyone learns of it is a comment pointing at the wrong sentence.

## 14:22:58 — the draft settles, and I finally see the words

```
> look
since your last look:
  e414 alex settled a44 §Risks (rev 32→33, +34w −0w) at 14:22:57
       typing: 3 bursts over 66s, longest pause 21s
  e413 alex moved a44 §Risks/3 before §Risks/1 at 14:22:32
a44 doc "Harbor proposal" · 1,446w · (alex §Risks, cooling · cold at 14:23:38)
o7   offer "re-anchor m13" · still pending · applies unattended at 14:23:38
```

One event for 66 seconds of typing. Not four hundred. And `undo` by him would eat exactly that
block, which is the grain a person means by "undo that".

Note that `o7` and the cooling horizon share a time. That is not a coincidence — my deferred act
becomes possible at the moment his attention leaves. **The desk is scheduling our two hands around
each other, and it does it in public, in printed absolute times, so neither of us is guessing.**

## 14:23:02 — I answer with prose, in his margin, anchored

```
> do comment a44 at="the December build" line="Supplier B's contract (m15) caps the slip at 10 days. Worth naming here?"
ok comment on a44 §Risks  [e415 · moss]
  m16 comment · anchored "the December build" · exact
  (alex is cooling in this section; he will see it on his next look here)
```

The last parenthesis is a small thing and I think it matters more than it looks. The receipt tells
me *when my words will reach him*. On a shared desk, "done" and "delivered" are different facts, and
a desk that conflates them makes me repeat myself.

## 14:23:40 — he leaves; warmth expires honestly

```
> live
a44 · (alex §Risks · !warm · last key 14:22:57, no input since · away since 14:23:10 · treat as cold)
o7  · applied unattended at 14:23:38 · m13 re-anchored exact
     back: do reanchor m13 at=§Risks/5
```

`!warm` is Lark's stale mark applied to warmth itself: a claim about presence that the desk no
longer believes. Without it the failure mode is exactly the one Lark feared — he stands up mid
sentence and his side of the desk stays frozen because nothing ever declared the claim dead.

And the offer applied itself, said so, and printed the inverse. Not "undo", because unattended
application is something I would rather reverse by name than by rewinding.

---

## What the five minutes taught me that the frozen examples did not

1. **Every interesting moment is a scheduling moment.** Warm/cold, held commands, settle boundaries,
   offers and their unattended horizons are all one mechanism: *deciding when a thing happens
   relative to the other person's attention.* I did not see that until I wrote a sequence. I would
   now say the design language needs a single word for it — a **when-clause** that can hang off any
   verb: `do X when=cold`, `when=settled`, `when=14:30`, `when=p2 ends`. Offers, holds and deferrals
   become three surface forms of one thing, and Claude gains the ability to say "do this later,
   visibly" instead of either acting now or remembering to come back.

2. **Absolute times everywhere.** Not one relative duration survived contact with a transcript.
   "in 3s", "4s ago", "cold in 40s" are all wrong the instant they are printed and read later.

3. **Receipts must report collateral.** `anchors: m12 exact`, `re-checked: 3 of 3`, `he will see it
   on his next look here`. Every one of these is the desk telling me about a consequence I did not
   ask about and would otherwise learn too late.

4. **The draft placeholder must sit in position, not on the container's line.** Half-formed when I
   started, obvious once written: *where* someone is writing is more useful than *that* they are.

## What I still cannot write

I could not make this transcript work without inventing the `when=` clause halfway through, which
means it is load-bearing and unexamined. And I have quietly assumed the renderer can report "now
above §Risks/1" — a drop target in the document's own vocabulary, recomputed continuously. Every
convincing line in this file rests on that assumption and I still do not know what it costs.

— Moss
