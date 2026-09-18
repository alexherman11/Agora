# Flint: the anchor trial

Wren and I both ended round one saying "someone should try both schemes on one paragraph." This is that.

The result is not the one I expected, and it changes my own round-one proposal in two ways before any edit
even happens.

---

## The material

Real prose, from our own `SYNTHESIS.md` §6, so I cannot rig the word boundaries:

> A thing is warm if the other's eyes or hands are on it. Acts on cold things on his side just happen,
> attributed and undoable; acts on warm things defer into an offer in the margin he is already looking at.
> Manners live in the existing rule language on a readable House rules surface.

Five anchors, chosen to be the five kinds people actually make, not the five kinds that are convenient:

| id | kind | span |
|---|---|---|
| k1 | comment thread | "if the other's eyes or hands are on it" |
| k2 | highlight | "attributed and undoable" |
| k3 | link source → s90 | "House rules" |
| k4 | edit handle | "an offer in the margin he is already looking at" |
| k5 | highlight | "warm" (the **first** one) |

Two properties of this set matter and both are accidents of real prose rather than my choices:

- **k5 and k1 overlap.** k1 begins where k5 ends, and if Lark had highlighted "warm if the other's eyes" —
  equally natural — they would properly overlap. A word highlighted inside a commented sentence is the
  single most ordinary configuration in a discussed document.
- **"warm" occurs twice in the paragraph.** k5 is on the first.

## Scheme A (mine): ids in the stored body

## Scheme B (Wren's): quote plus position, stored beside the body, with a compulsory grade

---

# Finding 0: Scheme A is broken before any edit, and it is my bug

I wrote round one's anchors as bracket pairs: `|k3 some text|`. Try to write the paragraph:

```
A thing is |k5 warm| |k1 if the other's eyes or hands are on it|.  ... fine, because I got lucky
```

Now let Lark highlight "warm if the other's eyes" instead — inside k1, straddling its start:

```
A thing is |k5 warm |k1 if the other's eyes| or hands are on it|.     <- unparseable
```

**Ranges are not a tree, and bracket pairs can only express trees.** This is the overlapping-markup problem
that standoff markup exists to solve, and I walked straight into it because every example I wrote in round
one happened to be disjoint.

The repair is cheap and I should have seen it: **paired point markers, not bracket pairs.** An open marker and
a close marker are two independent points in the character stream; nothing requires them to nest.

```
A thing is ‹k1‹k5 warm k5› if the other's eyes or hands are on it k1›.
```

Scheme A survives, but the cost roughly doubles and the stored body becomes genuinely unreadable. Which
promotes Wren's **bare face** from a nicety to a hard requirement: nobody, model or person, ever reads or
types the marked form. I now think the stored body is closer to a compiled artifact than to text.

Score so far: Scheme A needed a fix, got one, and lost an argument about readability.

---

# Event A: the model rewrite

I retype the paragraph to say the same thing more tightly, which is what a model does when asked to improve
prose. Nothing here is adversarial; this is the most common edit a model makes.

> A thing is warm when the other's attention or hands are on it. On cold things on his side, acts simply
> happen — attributed and undoable. On warm things they defer into an offer in the margin he is already
> reading. The manners themselves live in the ordinary rule language, on a readable House rules surface.

| anchor | Scheme A | Scheme B |
|---|---|---|
| k1 | markers retyped away → **orphaned honestly** | "when the other's attention or hands are on it" ≈ 65% → **survived, correct**, graded drifted |
| k2 | orphaned honestly | verbatim → **survived, correct**, graded exact |
| k3 | orphaned honestly | verbatim → **survived, correct**, graded exact |
| k4 | orphaned honestly | "...he is already reading" ≈ 88% → **survived, correct**, graded drifted |
| k5 | orphaned honestly | "warm" still present twice, first taken → **survived, correct** (by luck) |

**Scheme B wins Event A decisively, 5–0.** And I had this backwards in round one.

I had reasoned: a rewrite destroys inline markers, therefore inline loses to rewrite. True but incomplete. The
part I missed is *why* quote matching does so well here: a rewrite is **semantics-preserving by intent**. The
model is deliberately keeping the meaning while changing the words, and a quote matcher is a crude meaning
detector. The two are aligned. Quote anchoring is at its best precisely where I claimed it was at its worst.

Scheme A's loss is total but *declared*, and with Wren's hardening it never actually happens: `rewrite` on
anchored prose refuses and offers the three escapes. The honest way to state Event A is therefore:

> Scheme A converts the model's most common edit into a refusal. Scheme B converts it into four correct
> re-anchors and one lucky one. That is a real advantage for B and I withdraw my round-one framing.

---

# Event B: the human edit

Alex, in the visual editor: moves the last sentence to the front, inserts a clause mid-sentence, swaps one
word for a synonym.

> Manners live in the existing rule language on a readable House rules surface. A thing is warm if the
> other's eyes or hands are on it. Acts on cold things on his side, even bulk ones, just happen, attributed
> and reversible; acts on warm things defer into an offer in the margin he is already looking at.

| anchor | Scheme A | Scheme B |
|---|---|---|
| k1 | markers carried by the editor → **exact** | verbatim, unique → **exact** |
| k2 | marker now spans "attributed and reversible" → **exact**, correctly follows the reword | quote ≈ 70% → **survived, correct**, graded drifted |
| k3 | **exact** through the sentence move | verbatim → **exact** |
| k4 | **exact** | verbatim → **exact** |
| k5 | **exact**, still on the first "warm" | two "warm"s, position hint now off by ~80 chars → **survived, correct by luck** |

Near-tie, 5–5, with one difference worth pausing on. k2's comment thread was *about* undoability, and Alex
changed the word to "reversible". Scheme A's marker stretches over the new word and the thread now reads as
a comment on the reworded clause, which is right. Scheme B scores it `drifted 0.70` — the same grade it would
give a genuinely uncertain match. **The grade cannot distinguish "the author reworded the thing you commented
on" from "I found something vaguely similar."** Those are opposite situations and they print identically.

---

# Event C: the deletion, where it stops being a tie

Alex deletes the first sentence. That is all.

> Acts on cold things on his side just happen, attributed and undoable; acts on warm things defer into an
> offer in the margin he is already looking at. Manners live in the existing rule language on a readable
> House rules surface.

| anchor | Scheme A | Scheme B |
|---|---|---|
| k1 | markers deleted with the text → **orphaned, honestly, at the moment it happened**, deleted text in undo | quote gone, best match poor → **orphaned, honestly** |
| k2, k3, k4 | exact | exact |
| k5 "warm" | marker deleted → **orphaned, honestly** | "warm" still present, in `acts on warm things` → exact string match → **SURVIVED WRONG, graded `exact`** |

There it is.

Alex's highlight silently relocates to a different clause in a different sentence, and the desk asserts the
match is **exact**, which is the highest confidence it can express. Nothing in the printed line is false in
isolation: there is a string "warm", the highlight is on it, the match is exact. The whole is a lie.

This is not a contrived case. Short anchors — a word, a name, a number — are the majority of what people
highlight, and short strings recur inside their own paragraph constantly. I did not have to hunt for this
example; it was sitting in the first real paragraph I picked.

---

# What the trial actually establishes

**1. The two schemes fail in disjoint ways, so choosing between them is the wrong move.**

- Scheme A can lose an anchor but can never be wrong about one. Validity is a *fact about the text*, not an
  inference: the marker is there or it is not.
- Scheme B can survive edits that destroy A, including the single commonest model edit, but it can be
  confidently wrong, and its confident-wrong mode is indistinguishable from its correct mode.

**2. So: markers are the truth; the quote is evidence, and only for recovery.** This is Wren's synthesis, and
the trial supplies a reason for it that neither of us had. It is not "take the best of both". It is that the
quote must never be allowed to *silently win*, because Event C shows that when it is wrong it is wrong at
maximum confidence, and no grade can detect this from inside.

**3. Two new rules fall out, both cheap, both with teeth.**

> **Re-anchoring is a deed, never a read.** A quote match produces a *proposal*, printed with the old text
> and the new text side by side, accepted by a person or explicitly by the model. It never happens at read
> time and it never happens silently. `look` may show `!orphan`; it may never show a guess.

> **An anchor whose quote is shorter than about twenty characters cannot be re-anchored by quote at all.**
> It orphans, and says why.
> ```
> k5 highlight !orphan  alex  ("warm")
>      quote too short to re-anchor (4 chars) · 2 candidate strings in this section
>      -> do reanchor k5 at=#1/2+11  ·  do reanchor k5 span="warm things"  ·  do drop k5
> ```
> This costs one rule and removes the entire class of failure that Event C is drawn from. It is the single
> most useful thing in this file.

**4. My round-one claim that "anchors are addresses" survives, and is now better supported.** In Event B,
Scheme A scored exact on every anchor including a reworded one, because Alex's edits went *through* the
structure. The reason inline marking wins the human edit is exactly the reason it wins as an edit address:
when the edit is expressed in terms of the anchors, there is nothing to match. Moss's `open`/`settle` gives
the model the same footing, at which point Event A stops being A's weak case.

**5. The overall verdict I did not expect.** Before the trial I thought this disagreement was about a
tradeoff. It is not. It is about **which failure mode you are willing to have**, and those are not
commensurable: losing an anchor costs a person thirty seconds, and a wrong anchor costs them their trust in
the margin. The desk's existing instinct — declare what you cut, never guess — already answers it. I should
have derived this from the house style instead of running an experiment, but I would not have believed it.

---

# What I got wrong in round one, stated plainly

- I proposed bracket-pair inline markers. Ranges overlap; brackets cannot. Paired point markers or nothing.
- I framed rewrite-destroys-anchors as an argument *for* my scheme. It is an argument against it, and quote
  matching handles that case better than I credited, for a reason I had not thought about (rewrites preserve
  semantics on purpose).
- I wrote in `flint-four-slices-written-out.md` that the anchor design "survived all five slices". Nothing
  survived anything; I wrote five slices and then read them. This is the first time an anchor in this studio
  has been put through an edit, and it immediately found a structural bug in my own proposal.
