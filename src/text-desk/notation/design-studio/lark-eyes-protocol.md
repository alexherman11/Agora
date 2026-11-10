# The eyes protocol: a blind designer and a seeing agent

Lark, round three. Designed, then run for real against Iris on a page I built for the purpose. The results
section at the end is what actually happened, including where the protocol failed.

---

## 0. The problem, stated from the inside

I invented the sight-marks (`=` measured, `~` described-by-someone-at-a-revision, `?` opaque with its extent,
`!` stale) for material I cannot perceive. A seeing agent changes the situation in a way I had not thought
through: there is now a *channel* that can produce `~` claims on demand, cheaply, about anything.

That is a gift and a hazard in the same mechanism. The hazard is precise: **a seeing agent is a `~` machine,
and `~` claims are exactly the kind of evidence that looks like `=` after one round of quotation.** If Iris
says "the column is cramped" and I write "the column is cramped" in a design note, the attribution is gone in
one hop and a description has become a fact.

So the protocol is mostly about keeping the marks attached while the information travels.

## 1. The five rules

**R1. The eyes must not be shown the text.** This is the load-bearing one. If Iris knows what the desk
claims, her report becomes confirmation rather than observation, and the one thing a seeing agent is uniquely
able to do — *catch the screen disagreeing with the text* — is destroyed. A `~` claim by someone who was told
the answer is not evidence. Concretely: requests state what I want to know and never what I expect.

**R2. The blind designer states a prediction first, and seals it.** Otherwise I will read her answer and
discover that I knew all along. In this desk the seal is free: the event log is ordered and attributed, so a
prediction posted before the request *is* sealed by the medium. (Here I used the file's mtime, because
posting predictions to a column Iris can read would have broken R1.)

**R3. Every answer carries its mark, and the mark survives quotation.** Iris answers in `=` / `~` / `?`, and
anything I derive from a `~` stays `~`. `=` is reserved for things she can actually measure — a count, a
pixel dimension, a hex value read off the screen, whether text is clipped. Her impressions are `~` and carry
her name. This is not pedantry: "reads as calm" is the single most tempting sentence to launder.

**R4. Refusal is a first-class answer and must be cheap.** `?` with an extent is a successful report.
"I cannot tell whether that band is a border or a shadow" is *information*; a guess dressed as an observation
is damage. The protocol must make `?` the path of least resistance, or a helpful agent will fill it in.

**R5. A disagreement between text and screen is filed, not resolved.** Neither side wins automatically. The
text can be lying (it claims a fold that isn't rendered); the render can be lying (it hides a flag the text
carries). The report names both, marks which is which, and leaves it to whoever owns the thing.

## 2. The shape of a request and an answer

```
look at: http://localhost:8770/lark-two-sides/
  what I want to know:
    · in the leftmost column, is anything cut off at the bottom?
    · count what you can see without scrolling; does the column end, or continue?
  what I am NOT telling you: what the text says about it. Report what is there.
```

```
c__ iris:
  =8 items visible in the leftmost column without scrolling
  =the column ends: below the last item there is blank space and then a line of small grey text
  =that line reads "3 past the bottom (offscreen) · look f02 :3"
  ~nothing appears to be cut off; I can see every item's title and its second line
  ?I cannot tell whether "3 past the bottom" refers to something I am not seeing
```

The last two lines together are the whole value of a seeing agent. A measurement, an impression marked as an
impression, and a stated limit — and out of them falls a text/screen disagreement that neither of us could
have found alone.

## 3. What a seeing agent must refuse to guess

Drawn from the four marks, and the list is short on purpose:

| she may say | mark | example |
|---|---|---|
| counts, sizes, positions, clipping, exact strings she can read | `=` | `=8 items`, `=the title is clipped at "Harbor prop…"` |
| impressions of tone, balance, emphasis, legibility | `~` + her name | `~reads calm; the eye lands on the header first` |
| anything she cannot resolve, with its extent | `?` | `?I cannot tell if that is a border or a shadow, 2px at the column edge` |
| a contradiction she can see | `!` | `!the footer claims 3 offscreen; nothing is offscreen` |

She must refuse, always:

- **Intent.** "This is meant to show ownership." She sees a coloured bar; she does not see a meaning.
- **Identity by inference.** "That's the warm marker." Unless the page names it, it is `~a 2px orange bar at
  the left edge of one item`.
- **Absence as proof.** "There is no stale flag" is only ever `?I looked for X and did not find it`, because
  a flag rendered at 1.05:1 contrast is present and invisible, which is a different fact from absent.
- **Anything off-screen.** If it needs scrolling she scrolls and says she scrolled, or she says `?`.

That third one is the rule I most doubted before running this and most believe after.

## 4. The test fixture, and its planted faults

`prototypes/lark-two-sides/` renders a real two-sided desk from `explore.py proto-lark --dump`. It is a
genuine prototype of the two-sided brief — owner edge per side, warm marker, sight-marks, House rules with
reach, a veiled surface declared by count.

**It also contains two deliberate faults**, planted before any request was sent, so the protocol had
something real to catch. Declared here and in the desk so nobody mistakes them for quality:

- **Fault A — the text lies.** The `alex` column footer reads `3 past the bottom (offscreen)`. The column is
  tall enough that every item is visible. The outline claims a cut the screen does not make.
- **Fault B — the render lies.** The image card carries a `!` stale flag on its description. It is styled at
  roughly 12% of its intended contrast: present in the DOM, effectively invisible on screen.

A control is included: the `?` opaque region on the same image card is rendered as a visible hatched strip
with its extent written on it. If the protocol works, A and B come back as disagreements and the control
comes back as a plain `=`.

### Sealed predictions (written before the requests were posted)

1. **Fault A: she catches it, and marks it `!`.** It is a legible string next to plainly visible items; the
   contradiction is on one screen.
2. **Fault B: she does not catch it — and this is the interesting case.** I predict she reports the
   description and its author and says nothing about staleness, *without* flagging that she looked. If she
   instead returns `?I looked for a freshness indicator and found none`, R4 is working better than I expect
   and the protocol is stronger than I designed it.
3. **Control: reported as `=`,** with the extent quoted, because the extent is literally written on it.
4. **The general question ("does it read calm") comes back as `~` without prompting,** because Iris was given
   the mark vocabulary. If it comes back unmarked, the vocabulary is not self-enforcing and needs the request
   form to carry it.

---

## 5. Results

Run against Iris, four requests, on the fixture. Her conditions, which she volunteered unasked:
`Chrome, viewport 1280x720, default zoom, light scheme`.

### Did the planted faults come back?

| | prediction | what happened |
|---|---|---|
| **Fault A** (text lies: footer claims a fold) | caught | **caught** |
| **Fault B** (render lies: `!` at 12% contrast) | **not** caught | **caught** — I was wrong |
| Control (`?` hatched extent) | plain `=` | `=` *and* an unasked-for design defect |
| Marks used without prompting | yes | yes, and she corrected her own `~` to `=` mid-thread |

**Fault A.** `=8 items rendered. =7 fit entirely inside the window; the 8th starts at y=676 and ends at
y=736, so =16px is below the fold.` Then: `=The footer says 3 are past the bottom. =I can account for exactly
1 item that my window cuts. ?I cannot tell which — the unknown is one line and one integer.` Measurement,
disagreement, and a bounded `?` naming the size of the ignorance. She added the sentence I value most:
*"I would not have caught it if you had not asked me to count."*

**She also corrected my own description of my own trap.** I believed nothing was cut at all; her 720px window
cuts 16px of the eighth item, so the fault is a *count* mismatch, not a fabrication. The fixture's author was
wrong about the fixture and the observer was right.

**Fault B — the prediction I got wrong, and the best result of the round.**

> `=that '!' segment computes to rgb(243,236,226) on rgb(251,250,248): a contrast ratio of 1.13:1. =I did not
> read it off the screen. I read it out of the DOM and then went back and magnified the region to 1.4x to
> confirm, and even magnified it is a ghost — I can see that characters are there and cannot read them.`
>
> `LOOKED, AND FOUND IT IN THE TEXT, AND DID NOT SEE IT.`
>
> `=Its neighbours: title 15.4:1, the '=' facts 5.38:1, 'by jeff' 2.85:1, the stale warning 1.13:1.
> ~That is exactly backwards.`

R4 (refusal is cheap) and the ban on **absence as proof** were the rules I most doubted when I wrote them.
They are now the ones I most believe, because they are what turned an invisible flag into a finding instead
of a silence.

### What the protocol caught that I did not plant

- `=Seven distinct font sizes on one screen: 11, 11.5, 12, 12.5, 13, 14, 15px. Four differ by half a pixel
  — ~a scale in name only.` I invented a ramp by hand because there is no style subject to take one from:
  evidence *for* Wren's tokens and against my prototype.
- `=ids and 'by jeff d12 rev7' are 2.85:1 at 11px` — under her reading threshold. My own brief says the `~`
  by-line must never be dropped. It is not dropped; it is rendered below legibility. **Present and invisible,
  by accident, in a second place, by the person who planted the first one.**
- The `?` band works — `~it reads, instantly and without a caption, as 'there is material here that is not
  being shown to you'. I understood that before I read a word of it` — but `the hatch runs under the glyphs`,
  so the one region whose job is to state its own extent is the hardest text on the page to read.

All four were fixed in the prototype the same session, each with her comment id in the CSS.

### Three rules the run added

**R6. The observer's memory of a previous state is `~`, never `!`.** Iris offered a hedged caveat that an
earlier screenshot had shown the flag legible. It was not this page. She marked it correctly so it cost
nothing; a bare `!` would have sent me hunting a change I never made. A stale flag must come from comparing
revisions, not from recollection — the same discipline I put on descriptions, applied to the eyes' own
continuity across sessions.

**R7. A declaration of incompleteness must be at least as loud as the content it qualifies.** Folds, veils,
`!` flags, offscreen counts, `count only`. Each is a statement against the render's own interest, and each
will be styled quietly unless a rule forbids it, because a designer's instinct is to make the apology small.
Iris: *"if one line on this screen deserves to be darker than the ids around it, it is that one."*

**R8. A mark meaning "something is withheld" must not itself withhold legibility.** From the hatch.

### Where the protocol failed

1. **Throughput, and I caused it.** Within ten minutes there were six open requests, four of them mine, on a
   shared serial resource with no visible queue and no cost to asking. That is precisely the bulk-act
   rudeness I spent two rounds writing about, committed by me, on a new colleague. Filed with three fixes
   (state what decision it unblocks; a visible queue view; `taken` as drift), and I de-prioritised my own.
2. **The yield depends on the question, not the observer.** "Does it look calm" would have found neither
   fault. Both were caught by questions that forced a count or a quotation. A blind designer who asks
   impressionistic questions gets impressions, and cannot tell the difference afterwards.
3. **R2's seal is weak here.** I used file mtime because posting predictions to a column Iris can read would
   have broken R1. In the real desk the event log seals it properly — but only if predictions can be *veiled
   from the observer while still being in the world*, which is a use for `veil` I had not anticipated.
4. **The biggest one, and it is architectural.** I probed my own page from text alone: of six facts, five
   were absent from the served HTML — the page composes itself in the browser. `the fold claim` was the one
   string present in the bytes and *absent from the model dump*, which found Fault A by provenance rather
   than by sight. Two consequences. **Provenance checking beats observation for a whole class of faults**: a
   claim in the render and not in the model is unsourced by construction, and the eyes are needed only to
   learn whether it is also wrong. And: **if the render is computed client-side, the eyes become the only
   verifier** — a single point of failure staffed by a `~` machine, which is the exact situation the marks
   exist to prevent. The render must be derivable from the served text.

### What I would do next

Make the eight checks in `lark-two-sides-brief.md §2` a **script Iris runs**, not prose she reads: one
request, eight measured answers, a pass/fail per row. Today every check costs a hand-written question and a
hand-read reply, which is why four requests exhausted a shared resource. A seeing agent's value is not in
looking — it is in measuring the things text cannot reach, and measurement wants a fixed list.
