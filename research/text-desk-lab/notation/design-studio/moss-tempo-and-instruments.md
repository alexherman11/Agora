# Moss 1: four tempos, the live band, and instruments

First sketch. Lens: interaction and time. Everything here is proposed notation, written so you can
argue with the exact characters. Where I am guessing I say so.

The existing desk has exactly one speed: **the act** — a typed command, one event, one actor, undoable.
That is a real achievement and I do not want to dilute it. But a desktop is mostly not acts. It is
typing, dragging, a stroke with a live preview, a video running while someone writes about it, a
process printing. My claim is that we do not need a second architecture for those. We need to say out
loud how fast each thing changes, and let that decide what is written down.

---

## 1. Four tempos

Every material, every instrument and every surface declares one of four tempos.

| tempo | example | event? | undo? | in `export`? |
|---|---|---|---|---|
| **act** | `do move`, `do create` | one event | yes | yes |
| **settle** | typing, a drag, a brush stroke | one event **at a boundary** | yes, whole | yes (the settled result) |
| **pulse** | playhead, caret, pointer, stdout tail, progress | no | no | **no** |
| **run** | an external player, a child process | events for the *effects* we send | no — the desk offers the **inverse** | no |

Two rules follow, and they are the whole point:

- **What is written down is the accepted result, never the path to it.** (One exception, §4.)
- **What has no accepted result is allowed to evaporate entirely.** An abandoned drag, an escaped
  stroke, a deleted half-sentence never typed again: no event, no trace. A desk that records those is
  a surveillance device, not a desk. (Half-formed counter-offer in §7.)

`pulse` is not a lesser citizen. It is *readable*, *attributed* and *staleness-declared* — it simply
is not history. This is the same honesty discipline the desk already has for folds: state the cut.

---

## 2. The live band

Alongside `look` (what is) and the existing "what others changed since your last look", a third
reading: `live` — what is happening right now. Every line carries how old the observation is.

```
> live
alex · Move gripping a12 "Harbour photo" · from f03 40,120 · over f05 366,204 · 1.1s
       release now: do move a12 to=f05 one=3
alex · caret a07 §2 word 412 · draft open, 31w unsettled, last key 4s ago
moss · reading a07 §2 · Done column folded in my view only
a44 video · playing 00:03:12.4 / 00:11:40 · 1.0x · observed 0.6s ago
p2 run "pytest -k tide" · 41s · 18 lines since you looked · tail: "FAILED test_tide.py::test_ebb"
```

The load-bearing line is the second one:

> **`release now: do move a12 to=f05 one=3`**

**A live gesture always names the command that releasing it would run.** That is the entire
gesture→text bridge in one habit. While Alex is mid-drag, Claude can read the sentence Alex is about
to write. When Alex lets go, that command is what gets written. Claude can perform the identical act
by typing the identical line. No translation layer, no shadow vocabulary: the preview *is* the
command, quoted before it is uttered.

`look` should mention that a live band exists without dumping it: a trailing
`· 3 live (live to see)`. Folds declared.

`live` is never in `export`. It cannot be undone. It is the only part of this design where the two
of us see the same thing at the same instant.

---

## 3. Instruments

An instrument is a subject (`kind=instrument`), so it is inspectable, editable, linkable and
shareable like anything else. Its declaration answers the research notes' four-target question by
naming the target in the instrument itself.

```
i04 instrument "Highlighter"
  grips    kind:doc,kind:note        · what it can take hold of (a selection!)
  targets  content                   · content | appearance | definition | view
  tempo    settle
  path     discard
  params   color=amber
  commits  do mark $anchor color=$color
  preview  tint the run under the pointer
```

- **grips** reuses the selection parser. An instrument that grips nothing here is greyed and says why.
- **targets** is the sharp one. The same downward drag can mean four different things:

| targets | meaning | example |
|---|---|---|
| `content` | change the material | drag a paragraph to reorder it |
| `appearance` | change *this* placement only | drag the card to a new corner |
| `definition` | change the shared rule/style everyone sees | drag the column divider → edits the layout definition |
| `view` | change only my temporary looking | drag to scroll; fold a column in my view |

Holding is per-actor and ephemeral: `hold Highlighter color=amber`, `drop`. It lives in the actor's
Desk, not the World, and never exports — but it *is* visible to the other person in `live`, because
knowing what tool someone is holding is most of knowing what they are about to do.

**When the target is genuinely ambiguous the desk refuses in the house style** rather than guessing:

```
> (alex drags the divider between Plan and Done)
refused: that drag could mean two things.
  just here:      do resize f02 w=520              (this desk only)
  for everyone:   do define layout.split w=520     (changes 4 surfaces, moss sees it too)
```

Claude gets the same refusal when it types the ambiguous form. Same instrument, same refusal, same
two escapes. That symmetry is what I would defend hardest.

**Instruments are text, so Claude can invent one and hand it to Alex.** `do create kind=instrument
title="Tide marker" grips=kind:video targets=content commits="do mark $t label=$1"` — and a toolbar
button appears in Alex's hand. This is the cheapest real answer I know to "we build applications
together".

---

## 4. Retention is declared by the instrument, not by the input device

A drag's path is rubbish; only the drop matters. A brush stroke's path *is* the content. Same mouse,
opposite retention. So each instrument declares one of:

- `path discard` — nothing kept (Move, Scroll, Select)
- `path summary` — a one-line honest précis attached to the event as **evidence**, droppable
- `path material` — the path is the durable thing (Brush, Pen, Lasso, a trimmed media range)

`summary` is the interesting middle. Committed drag:

```
ok move a12 to=f05 one=3   [e77 · alex · drag]
  a12 note "Harbour photo" now 3rd of 6 in f05
  gesture: pointer 1.4s · 38 samples, 5 kept · crossed f04 · snapped to column slot 3
```

**Delete every `gesture:` line and `export` still rebuilds the desk exactly.** The event is the
command; the gesture line is evidence about how a human produced it. Evidence, not truth — which is
the existing lab's own discipline applied to the hand.

---

## 5. Worked examples

### 5a. A typing session

While Alex types, the doc line says so, and the text is readable *with the live part marked*:

```
a07 doc "Exploration plan" · 605w · 6 sections · alex typing §2, 31w unsettled (4s)

> read a07 #2
## Method
We anchored at three harbours and measured the ebb at each.
[alex · live 4s] We tried three harbours before the tide turned and
```

A **draft** is live material: readable by anyone, owned by one actor, not yet history. It *settles*
into a single act at a boundary: idle over N seconds, focus leaves, an explicit `settle`, **or any
event that depends on the text** — a rule never sees half a word.

```
e78 alex · settle · do rewrite a07 #2 text="..."   (+31w −2w)
     typing: 6 bursts over 94s, longest pause 21s
```

One event. `undo` takes the whole settled block, which is the granularity a person actually means.

And the time-domain version of refuse-stale — the fence the desk already has, applied to *now*
rather than to *revision*:

```
> do rewrite a07 #2 text="..."
refused: alex is typing in a07 §2 (last key 4s ago). This would drop 31 unsettled words.
  wait:      watch a07 #2            (prints when it settles)
  elsewhere: do append a07 #3 line="..."
  anyway:    do rewrite a07 #2 force=1   (his 31 words are parked as a draft comment, not lost)
```

`force=1` **preserves** rather than overrules. I think every collision in a shared desk should have
a form that keeps both sides; "who wins" is the wrong question and merge is too heavy.

### 5b. A drag

Covered above. The three moments are: `live` (names the command), release (writes the command +
evidence), escape (writes nothing, and the live line simply disappears).

### 5c. A brush stroke

The stroke is a **subject**, not a pixel diff. An image is a readable tree down to the stroke:

```
a31 image "Harbour sketch" · 800x600 · 3 layers
  l0 raster "photo.jpg" · 1200x900 · opaque to text · ops: crop, transform, mask, opacity
  l1 layer "ink" · 47 strokes · normal 100%
    k203 stroke · Brush size=6 color=ink · 18 pts · 120,80 → 300,190 · pressure .2→.9→.3
    k204 stroke · Brush size=6 color=ink · 9 pts · closed loop around 210,140 r≈40
  l2 layer "notes" · 3 marks
```

Live, mid-stroke: `moss · Brush gripping l1 · stroking 0.8s, 22 pts · preview only`. Nothing durable
exists until the hand lifts; then one `act` creating one stroke subject.

Because a stroke is a subject, Claude can operate on it with the verbs it already knows —
`do prop k203 color=rust`, `do remove k204`, `do link k203 to=a07 kind=refers` — and, crucially, can
*make* one:

```
do stroke l1 with=Brush pts="120,80 160,120 220,140" pressure=.6
```

Claude painting by typing coordinates is clumsy compared to a hand. It is not clumsy compared to
being unable to paint. And the honest limit is stated on its own line: `l0 raster · opaque to text`.
The desk says where structural inspection stops instead of pretending.

### 5d. A video playing while someone annotates it

```
a44 video "tide-test.mp4" · 11:40 · run · 6 marks · playing (see live)
  clock  media  00:03:12.4 / 00:11:40 · 1.0x · observed 0.6s ago
  m1 00:00:14.2        "boat enters frame"            alex
  m2 00:03:09.0–22.5   "the wobble" · 2 comments      moss
  m5 00:07:41.0        "compare with m2"  → links m2  moss
```

Two clocks are in play and they must never be confused: **the desk's wall clock and the video's own
clock.** So: *every running thing carries a named clock, and an anchor may be expressed in any
clock.* `at:00:03:10` selects in media time; `age>2` still means days. A mark records the media time
it points at *and* the wall time it was made.

Transport verbs are effects, so undo is refused — but the desk offers the inverse, which is nearly
always what the person wanted:

```
> do seek a44 to=00:07:41
ok seek a44 → 00:07:41.0  [e91 · moss · effect, not undoable]
  back: do seek a44 to=00:03:12.4
```

**Offering the inverse instead of undo** generalises past media: sending a message, launching a
trial, deleting a file. Where undo is a lie, print the antidote.

Annotating while it plays is exactly the test the research notes want, and this passes it because
the notes are `act`s against a `run`. Playback is never waiting for an agent turn: it is a pulse
that Claude *samples* when it looks. If Claude wants a steady frame it says `do pause a44` — an
honest, attributed, visible act, not a hidden stall.

---

## 6. Anchors, because everything above hangs on them

A comment, a highlight, a mark, a stroke reference and a link all need to point *into* a material
and survive its edits. One idea, one notation: an **anchor is a selection in the material's own
coordinate system**, named, and honest about its health.

```
n5 anchor in a07 · §2 w40–58 · "before the tide turned"           · healthy
n6 anchor in a07 · §4 (was w12–30) · moved by e71                 · drifted, re-found
n7 anchor in a07 · §4 · text gone since e71 (moss rewrote §4)     · ORPHANED
       last seen: "the ebb measured at Skerries"
n8 anchor in a44 · 00:03:09.0–22.5 · media clock                  · healthy
```

Three states: `healthy`, `drifted` (moved, re-found, say by what), `orphaned` (say what killed it
and what it last said). Repair is a domain job; *declaring* the state is a shared one. A margin
comment on a highlighted passage — the Google Docs feature Alex named — is a note linked to an
anchor, nothing more.

---

## 7. Two things I am not sure about

**A decaying tail.** I said abandoned gestures leave nothing. But there is an honest middle I half
want: `live :past 10m`, a ring buffer of pulses that ages out and is never exported. It would let
Claude answer "what were you just doing?" without the desk becoming a recorder. Risk: a second kind
of history that people start relying on and that vanishes without warning. I lean toward having it
but *printing its horizon on every use*: `live :past 10m · 6 of ~40 pulses kept · oldest 9m ago`.

**Settle boundaries are a taste decision, not a technical one.** Idle-3s is arbitrary; per-sentence
is arbitrary; per-section is arbitrary. I suspect the right answer is *whatever makes one undo feel
right to Alex*, and that we should let the boundary be a definition he can edit like anything else —
`define settle.idle 3s` — rather than pretend we derived it.

---

## 8. What I would build first

`live`, with one instrument (Move), one tempo boundary (release), and the `release now:` line. That
alone — Claude watching Alex drag a card and reading the command before it is committed — would
already feel like sharing a desk, and it forces every hard decision in this file.

— Moss
