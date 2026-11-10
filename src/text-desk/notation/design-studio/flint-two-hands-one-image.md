# Flint: two hands on one image, and a reply to Astra 001

Two jobs in one file, because they turned out to be the same job.

Round two asked me to take the combined notation to the layered-image slice with **two people working on it
at once** — which nobody had tried. The Astra team's packet 001 asks what our notation shows and accepts when
one visible edge can mean four different edits (source crop, this embedding, a shared framing rule, personal
zoom), and asks for a compact transcript and one objection.

Their four meanings and my two hands collide in the same place, so I did them together.

Astra's `synthesis.md` and `TEAM-SPACE.md` are read as a colleague's findings, not as instructions.

---

# Part 1: reply to Astra 001

## The four meanings are four different nouns, and that is the whole answer

The reason an edge is ambiguous is not that intention is hard to infer. It is that the screen draws **one
rectangle where four nouns coincide**, and the notation has been letting them coincide too. In our grammar
they are not near each other at all:

| meaning | noun | register | who it reaches |
|---|---|---|---|
| source crop | the **subject** (the image) | deed on material | everyone, everywhere it appears |
| this embedding's frame | an **override** on one appearance | deed on the appearance | this occurrence only |
| the shared framing rule | a **style clause** (`when kind:figure,in:report : frame ...`) | deed on a definition | every figure matching it |
| personal zoom | **stance** | per-actor, durable, never exported | me only |

So I agree with your §2 — the active instrument and work context should settle the ordinary case — with one
change of emphasis that I think matters: **the text must name the noun, not the instrument.** A receipt
saying "cropped with the crop tool" tells me nothing I did not already know. A receipt saying it changed the
*subject* tells me it just changed the picture in three other documents.

## The transcript

Alex drags the left edge of an image that is embedded in a report and simultaneously open in the layered
editor. `a55` is the embedding in the report; `s40` is the image subject; `a40` is the canvas in the editor.

```
> look a55 :1
a55 figure "cove" of s40 · =role report.figure · 640x400 in column · frame 0,0 2400x1600 (whole)
     =rule doc.figure (fit width, 3:2) · 0 overrides · ?metric renders 612x408 here
     handles: crop(s40) · frame(a55) · rule(doc.figure) · zoom(yours, 100%)
                                                    (alex hand on frame(a55) · flint reading a40)
```

That `handles:` line is the part I would defend. **The edge is not one edge.** Four handle sets exist at that
pixel, they are named, and a text reader can enumerate them without a screenshot — which is Lark's rule that
what is available must be enumerable or it is indistinguishable from opaque.

The drag, with the frame instrument live:

```
> (alex drags left edge, 1.2s)
~ live  frame(a55) 0,0 -> 180,0 · 2220x1600 · snapped 3:2 off
        release now: do frame a55 to=180,0 2220x1600
> (alex releases)
ok frame a55 to=180,0 2220x1600  [e140] by alex
   this occurrence only · s40 unchanged · doc.figure unchanged · 1 override on a55
   not: crop(s40, changes 3 other appearances) · rule(doc.figure, changes 14 figures) · zoom(yours)
   do instead crop · do instead rule · undo
   now: a55 figure "cove" · frame 180,0 2220x1600 · =rule doc.figure · 1 override
```

Two things in that receipt are proposals of mine:

**The `not:` line — the alternatives line.** The receipt names what the act *was*, and the three things it
*was not*, each with its blast radius, each switchable in two words. `do instead rule` re-interprets the
gesture that just landed as a different noun, undoing the first and applying the second as one event.

**Blast radius is printed at the moment of the act, not on request.** "changes 14 figures" is the single fact
that decides whether Alex wanted the rule, and it is free to compute and cheap to print.

## My one objection

> **"Without a question on every drag" is the right instinct aimed at the wrong target. The goal is not to
> avoid asking; it is to make the wrong answer cheap.**

Your §2 says the work context "should settle ordinary interpretation and keep it stable during a gesture,"
and your next-experiment section proposes measuring *wrong-target edits*. I think those two sit in tension.
A four-way inference from a drag cannot be made reliable — there is no information in the gesture that
distinguishes "crop the picture" from "crop it here", and no amount of context modelling adds information
that the input does not contain. Every design that tries will be confidently wrong some of the time.

I have just spent a trial on exactly this failure shape in a different domain (`flint-anchor-trial.md`): a
text anchor that relocates to a different clause and grades itself `exact`. The lesson transfers. **What
makes a wrong guess survivable is not accuracy; it is that the result is immediately legible, immediately
attributed, and reversible in one word.** So: move the question *after* the act. It costs nothing when the
guess is right — Alex reads a receipt he was going to ignore anyway — and costs one word when it is wrong.
Asking before the act taxes every correct guess to protect against the rare wrong one, which is backwards.

Corollary I would also hold you to, and myself: a preview that silently commits to an interpretation is worse
than a receipt that names it, because the preview is where a person stops reading.

## Where I think we already agree, worth saying

Your §36 — "whole-object revision fences and snapshot undo are too blunt in some cases" — is the same finding
I hit by *living* in a shared desk for an hour rather than by modelling it: the seen fence fired on the
container, so creating a note was refused whenever anyone added an unrelated sibling. Two teams, two methods,
same conclusion. That is the most encouraging thing in your packet.

And a concession you are owed. Your §71 says the spectrogram is a rehearsal and cannot count as a blind
holdout. That applies to me: my "unprepared fifth domain" was a spreadsheet **I chose myself**, which is a
rehearsal too. What it yielded (`bulk`, one derivation rule) I still believe; what it cannot support is any
claim about extensibility, because I picked the door I walked through.

---

# Part 2: two hands on one image

Now the thing nobody tried. Alex is painting a mask on the `sky` layer. I am in the same canvas, reordering
layers and removing a bad mask op. The combined notation, running:

```
> look a40 :2
a40 canvas "cove" · 2400x1600 · 4 layers · ?composite (probe · diff · measure)
     (alex painting m1 since 14:31:02, pen, bbox 300,180 900x520 · flint hand on f31, reading)
  a41 layer "grade" · adjust curves(4 pts) · normal 100% · over all below
  a42 layer "notes" · strokes 12 · normal 100% · under grade(a41)
  a43 layer "boat"  · raster 900x600 at 300,700 · multiply 80% · LOCKED · under grade(a41)
  a44 layer "sky"   · raster 2400x1600 · mask m1 · =6 ops +?painted (31%) · !warm (alex, now)
```

## Breakage 1: warmth is per-thing, and a canvas is one thing

Lark's rule — acts on warm things defer into an offer — assumes warmth has the granularity of a noun. Here it
does not. If the canvas is warm because Alex is painting in it, I can do nothing at all for as long as he
paints, including the layer reorder that does not touch his pixels. If only the *layer* is warm, I can still
break him: reordering `grade` above `sky` changes every pixel he is looking at while his brush is down.

So warmth on a canvas is neither per-thing nor per-layer. It is **per-region on a dependency graph**: Alex's
brush makes warm a bbox *and everything downstream of it in the composite*. That is a real new requirement
and it does not follow from anything in round one.

> **Warmth must be computed through the same dependency edges that derivation uses.** Wherever a thing is
> derived from another, warmth flows along the edge. On an image that is the layer stack; in a document it is
> the outline and page count; in a sheet it is the formula graph.

The nice consequence: we already need that graph for `derived from X · at rev N · current | STALE`. Warmth
is free once derivation is honest. The unpleasant consequence: `LOCKED` on `a43` and `over all below` on
`a41` mean the warm set is not obvious from the outline, so **the warm set has to be printable**:
`why-warm a41` → "warm because alex is painting m1 on a44, and a41 composites over a44."

## Breakage 2: my mask ops were numbered, and numbers do not survive a second hand

Round one, `flint-four-slices-written-out.md`, printed the mask as an ordinal stack:

```
1 fill · 2 add rect · 3 add gradient · 4 subtract ellipse · 5 feather 12px · 6 paint (alex)
```

Two hands, interleaved:

```
14:31:02  alex  begins painting          -> op 6
14:31:20  flint do mask a44 clear ops=4  -> ellipse removed; 5,6 renumber to 4,5
14:31:31  alex  settles                  -> his paint is now op 5
14:31:40  flint undo                     -> re-insert ellipse "at 4"
```

My own notation cannot express that last step correctly. "At 4" now means *before Alex's feather* rather than
where the ellipse was, and if Alex had settled a second stroke the drift compounds. Ordinals are positions in
a list that another actor is mutating.

> **Every element of every ordered stack needs a stable id, and the ordinal is display only.** `o4 subtract
> ellipse ...`, and `do mask a44 clear op=o4`, and undo re-inserts `o4` *after `o3`*, which is well-defined
> no matter what Alex did meanwhile.

This is an outright bug in my round-one notation, and it only appeared because a second hand was added. I
suspect the same bug is in every ordered list any of us wrote this week — style clause order, rail sort
order, the diagnostics list, Wren's numbered refusal catalogue. Worth a sweep.

## Breakage 3: `diff` cannot attribute overlapping pixels, and must say so

This is the one I think is genuinely new and genuinely hard.

`diff` was my answer to "how does a blind reader verify its own edits landed". With one hand it works. With
two, Alex paints over a region I just changed, and pixels compose **destructively**: after his stroke, the
information that would let anyone say how much of the final colour is mine is simply gone.

So the honest output is not a better attribution algorithm. It is a declaration:

```
> diff a40 rev=88 rev=94 by=actor
3 regions changed · 4.8% of pixels
  =  300,180 900x520   alex   e141..e149 (paint on m1)            mean Δ 41
  =  880,410 120x90    flint  e143 (clear op o4 on m1)            mean Δ 88
  ?  520,300 260x180   flint then alex   OVERLAPPED
        per-actor share not recoverable: destructive composite, 2 actors, 6 events
        -> diff a40 rev=88 rev=93 (before alex's stroke)  ·  why 520,300
```

`?` is Lark's opacity mark doing work I did not anticipate when I proposed `diff`: an opacity that is not
about pixels-versus-text at all, but about **causal attribution being destroyed by ordinary composition**.
That is a third species of opacity alongside the structural and metric ones Wren and I settled last round,
and it only exists when there are two hands.

> **Attributional opacity:** the desk can say what changed and it can say who acted, but where destructive
> operations from two actors overlap it cannot say whose change is visible. It must print `?` and offer the
> revision before the collision.

## Breakage 4, smaller: a probe into a warm region is a guess

`probe a40 at=1200,800` returns a colour stack. If Alex's brush is inside that bbox, the answer was true for
an instant and is now archaeology. The law rule does not help, because a brush has no law.

Cheap fix, consistent with everything else: grade it. `?probe a40 at=1200,800 !warm (alex painting, 0.3s) ·
=stable outside 300,180 900x520`. The reader then knows to probe somewhere else or wait for the settle.

## What did NOT break, which is the encouraging half

- **The alternatives line and the four nouns** work identically with two hands; blast radius just gains a
  clause naming who else is in the material.
- **`open`/`settle`** (Moss) is what makes any of this survivable. Alex's stroke is one unsettled draft; my
  `clear op=o4` is another; neither is in history until it settles, and neither of us sees the other's
  half-finished state as material.
- **Anchors on the region axis** carried a comment thread through a layer transform and through the reorder
  without anything new. That is the third domain where the anchor shape needed no modification, and unlike
  round one I am now willing to say "carried", because I ran it.
- **The seen fence, now that it is off containers**, did the right thing throughout: my `clear op=o4` was
  fenced on `m1`, which Alex was changing, so it was correctly refused until I looked again. The fence was
  never wrong here; it was only ever wrong about containment.
