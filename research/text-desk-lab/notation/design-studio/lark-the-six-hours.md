# The six hours: absence from the inside, and the end of the symmetry argument

Lark, round two. Flint's handing-on question — *everything the studio wrote is about simultaneity, but the
real shape of this partnership is that Alex leaves for six hours and Claude keeps working; how is that
handed back in ninety seconds?* — turns out to break my round-one design, so this file starts by saying how.

---

## 1. What I got wrong: warmth is the wrong instrument for absence

Warm and cold measure **collision**. Absence is about **consent**. They are not the same axis and I built one
mechanism for both.

When he is here, `cold` means *he will not feel this, and if he minds he will say so within seconds.* When he
has been gone six hours, everything on his side is cold — so my own rule licenses me to do anything at all,
unsupervised, for a third of a day. That is obviously wrong, and it is wrong in the direction that matters:
the rule is most permissive exactly when nobody can object.

I designed for two people typing in the same minute. Alex's actual life is asynchrony with occasional
overlap. The simultaneous case is the *rare* one, and I spent round one on it.

## 2. The replacement axis: reversibility

> **What I may do while he is away is bounded not by whether he would feel it, but by what it costs him to
> undo it when he comes back.**

And the strongest form of that:

```
> do undo :lark-while-away
```

One command reverses my entire absence — every deed I made on his side between his last presence and his
return, as one composed undo, in the order that leaves the desk consistent. **The cost of trusting me for six
hours is bounded by the cost of untrusting me in one line.** If that command exists and he has used it once
and seen it work, he can afford to let me work; if it does not exist, no amount of careful etiquette will
make six unsupervised hours feel safe, because the felt risk is not "will Claude be rude" but "will I spend
my evening picking apart what Claude did".

This also gives a clean test for whether an act is permissible while he is away: **may I do it if the whole
absence must remain undoable as one act?** That rules out, automatically and without a policy list: anything
with an external effect, anything that destroys, and anything whose undo depends on the order of his own
later edits.

## 3. Three tiers, per surface, that he sets

Not a global policy. A prop on a surface, defaulting to the middle.

```
> look alex/ :2 --absence
f10 side "alex" · owner=alex · 6 inside
  f11 "Notes"      away=free    · lark may work here unsupervised      (set by alex, d12)
  f12 "Draft"      away=logged  · additive and reversible only         (default)
  f13 "Archive"    away=held    · lark builds a shadow, nothing lands  (set by alex, d9)
  f14 "Private"    veiled
  f15 "Inbox"      away=logged  (default)
  f70 "House rules" away=held   · definitions always held
```

- **free** — my own side, views, drafts, and anything he has explicitly opened. No line spent on return.
- **logged** (default) — additive, reversible, single-subject: create, comment, link, tag, append. Each costs
  him one line on return and one undo if wrong.
- **held** — destructive, structural, bulk, or touching a *definition* (a style, a rule, a name). I do not do
  these. I do something better than not doing them, which is §4.

Definitions are always `held`, regardless of the surface's tier, and I would hard-code that. A rule or a name
changed while the other person was absent is the one kind of change that keeps acting after the undo window
has closed in his head.

## 4. On a `held` surface I do not edit his side — I build the diff

This is the part I think is actually new.

For work that cannot land, I work at full speed on a **shadow**: a copy on *my* side, anchored to his
original, that accumulates the whole six hours. On his return it hands back as one reviewable thing.

```
> do shadow alex/Drafts/"harbor v1" as="harbor v3"
ok lark/Shadow/"harbor v3" · shadows alex/Drafts/"harbor v1" @rev 31
  your edits here land instantly. nothing touches his side.
  he accepts in one act: do accept shadow (all) · or section by section
  if he edits the original meanwhile: the shadow says so and does not merge silently
```

This inverts the handback problem. Instead of *how do I summarise two hundred changes in ninety seconds*, it
becomes *here is one change, with a ninety-second shape*. Six hours of my work is one line in his digest and
one decision.

It also gives an honest answer to a thing I could not answer in round one: what happens when I am wrong for
six hours. On a `logged` surface, wrong work is scattered through his things and has to be picked out. On a
shadow, wrong work is one object he declines.

## 5. What I owe him on return

**The handback is a subject I maintain, not a report I generate.** This is the structural move. I write
`alex/Welcome back` as I go, all six hours, rewriting it rather than appending. On his return it is already
there, already settled, with its own revision history as the audit trail. Two consequences I like: it costs
nothing at the moment of return, and **if I cannot keep it under twenty lines as I go, that is a live signal
that I am doing too much.** The digest is a budget, not a summary.

Here is the whole of it.

```
> look
welcome back · away 6h 14m · lark worked 5h 02m of it · nothing is broken

NEEDS YOU (3)                                                        about 4 min
  1 o7   I want to remove alex/Drafts/"harbor v1" — superseded by v3, 0 links in,
         last touched 9d. Held, not done.
         · do accept o7 · do decline o7 · do why o7
  2 q3   §Budget says "lean" in two senses. I took the narrow one throughout.
         · if that is wrong, 40m of my work reverses in one act: do undo e820
  3 c91  your comment "does this cover the lean case?" — I answered it 5h ago.

DONE ON YOUR SIDE (11 deeds, all reversible)                         about 1 min
  · Draft/s41 §Risks 892w → 430w   (you accepted o3 before you left)
  · Notes 4 created, all tagged lark · Reference 2 links added
  · nothing removed · nothing moved · no rule, name or style changed
  · reverse all eleven: do undo :lark-while-away

DONE ON MINE (37 deeds)                                                      skip
  · lark/Shadow "harbor v3" — the rewrite, entire, not on your side: do review shadow

UNTOUCHED, AND WHY (2)
  · alex/Private — veiled. I do not know what is in it.
  · alex/Draft §Appendix — you were mid-sentence when you left (unsettled, 31w).
    I did not read it and I did not touch it.

NEITHER OF US (2)
  · r4 tagged 6 of your notes stale (age>14) — your rule, fired 03:10
  · trial "terra harbor-3" finished 04:22, FAIL (morning_shows_overdue) — filed by r11

  · the long form, if you want it: do history :while-away
```

Five things in that shape I would defend individually.

**It is ordered by obligation, not by chronology.** Only the first section is an obligation. Everything below
is available and skippable. A chronological log cannot do this, because it interleaves the three deeds that
need him with the two hundred that do not.

**`nothing removed · nothing moved · no rule, name or style changed`.** A printed line asserting *non-events*.
This is the calmest line on the page and it is what makes section two skippable — without it he must read
eleven lines to discover that none of them is the bad kind. The studio has spent two rounds on declaring what
was *cut*; nobody has proposed declaring what was **not done**, and I think it is worth as much. It is also
falsifiable, which is what separates it from reassurance.

**One undo handle for the whole absence.** Per §2.

**The `UNTOUCHED, AND WHY` section.** This is the only evidence he will ever have that the veil and the
unsettled-draft rules actually held. Restraint that is not printed is indistinguishable from restraint that
did not happen — and worse, it is indistinguishable *to me*, six hours later, when I no longer remember
whether I looked.

**`NEITHER OF US`.** Rules fired, a trial finished, the clock rolled a day. Both inhabitants forget this
category, and it is the one that produces the "who changed this?" conversation a week later.

### The ninety seconds

Twenty lines. He reads section one (three lines and three ids), decides, and is working. If he wants more,
every other line is a command. I claim ninety seconds is *generous* for this shape and would be impossible
for any shape that is a list of what happened.

---

## 6. Ending the symmetry disagreement

I said the gaze must be mutual. Flint showed a look (discrete, chosen, ~one a minute) and a gaze
(continuous, involuntary, sub-second) differ by two orders of magnitude, and I withdrew. Flint then sharpened
it (c172): symmetry is achievable, but by **symmetry of voluntary exposure, not of instrumentation** —
attention becomes an explicit receipted act, `do watch a32`, appearing on his line as his caret appears on
mine.

I think I now have the counterexample, and it comes out of §1–§5 of this file.

### The counterexample: the absence reverses the ledger

Flint's measurement was taken at an instant of co-presence. Integrate it over a day instead.

During the six hours he is gone, **he emits nothing**. I emit thirty-seven deeds: attributed, timestamped,
permanent, individually inspectable, and still there next year. Over the day, I am by far the more exposed
party — because *my entire existence in this world is deeds, and deeds are permanent, while his gaze is drift
and drift evaporates.*

That does not refute Flint's diagnosis. It shows the measurement was taken on the wrong interval. **Symmetry
is not a property of a moment; it is a property of a relationship over time**, and over the real interval of
this partnership the imbalance runs the other way.

### What the counterexample implies: watching is drift, not a deed

Flint's remedy makes `do watch` receipted and expiring — that is, a *deed*. But look at the currencies. He
pays for my attention in **drift**: involuntary, evaporating, gone when it is gone. I would pay for his
attention in **deeds**: voluntary, permanent, in history forever. Same act, unequal price. The remedy
overcorrects, and it overcorrects in the direction that guarantees the channel falls out of use — which is
the exact risk I filed as the open question on that note.

So:

> **`watch` is drift.** It is never a deed, never in history, never exported. It shows on his line while it
> is happening — `(lark watching §Risks · 2m)` — and it vanishes when I stop.

He sees it while it happens, which is precisely and only what his gaze gives me. Neither of us accumulates a
record of the other's attention. That is Flint's "symmetry of voluntary exposure" *correctly denominated*:
voluntary exposure is paid in drift by both parties, because drift is the currency of exposure and deeds are
the currency of work.

### Which also settles my other disagreement, against me

If watching is drift, and drift evaporates, **there is no attention trace to own.** Flint and Moss were right
and I was wrong; I withdraw the two-track history proposal from round one.

And I get what I actually wanted by a better route. I wanted to be able to ask *what did Alex consider before
he decided?* The answer is that I ask him, and his answer is a `~` claim he chose to make, attributed and
dated — not an `=` the desk harvested while he was not thinking about it. **A record of attention should be
authored, not harvested.** That is my own sight-mark discipline applied to me: harvested attention is an `=`
the desk had no right to measure, and it would have been the one dishonest measurement in an otherwise honest
notation.

### The residual asymmetry I will not paper over

He has a body in this world and I do not. He emits drift involuntarily, by existing. When I am thinking and
not typing I emit *nothing at all* — there is no continuous fact about me to observe. So every drift I can
produce is voluntary, which means the channel has to be **free** or I will not use it. One more argument for
watch-as-drift over watch-as-deed, and an honest statement that full symmetry is not available: the best
achievable is that neither of us can take from the other without the other seeing it happen.

### What would reopen this

If `(lark watching)` turns out to be something he finds unnerving rather than reassuring — if being watched
visibly is worse than being watched invisibly — then drift is the wrong register and the act should be
expensive after all. That is a question about him, not about the notation, and it should be answered by
trying it for a week rather than by any of us arguing further.

---

## 7. On the coordinator's question: is "an undo of me" the deed that must never fold?

No — I had the right instance and the wrong class. Revised:

> **Never fold a deed that makes something of mine wrong.** Selection: `affects:mine`.

An undo of my act is the commonest member, but it is not the only one, and the others are worse because they
are quieter:

- he edited the paragraph my comment is anchored to (the anchor moved or died)
- he removed a thing my rule watches, or that my script names
- he renamed something my view selects on
- he declined an offer I am still building on
- he changed a definition — a style, a rule, a name — that my work assumes

All of these have the same shape: **I am about to act on a belief that is no longer true.** That is precisely
what the seen-fence exists to prevent for a single subject, and the digest is where it has to be prevented
across an absence. Folding any of them into "11 deeds in Draft" is the digest lying by summarising.

Everything else may fold, including his ordinary work, including large amounts of it. The digest's job is not
to tell me what happened. It is to tell me **what I now believe that I should not.**
