# Moss 2: text becomes a gesture by acquiring duration

Second sketch, written after reading Lark's *Two inhabitants*, Wren's *The page itself*, and Flint's
deed/drift note. I have adopted **deed/drift** as the top-level cut — better words than my act/pulse
— and Lark's **warm/cold**, which is better than the time-fence I had written. This file is the
parts that survived, plus one idea I think is new.

---

## 0. The asymmetry nobody has named yet

Everyone so far has designed *what Claude reads about Alex*: the gaze, warmth, carets, marks,
sight-marks. Good. But run it the other way and the shared desk is grotesque.

**Alex's acts have duration and are visible before they complete. Claude's acts are instantaneous,
whole, and arrive without warning.** Alex spends 1.4 seconds dragging a card, and for all 1.4
seconds Claude can watch and could object. Claude reorganises eleven cards between two of his
keystrokes. Lark noticed this and proposed a 300ms landing animation. That is a courtesy applied
after the decision; it does not give Claude a *tempo*.

Here is what I want instead.

## 1. The held command

> **A typed command may be held. A held command is drift with a countdown: it appears in the live
> reading, names exactly what it will do, and either party can cancel it before it lands.**

```
> hold do move ?harbour into=f05 · in 3s
held h4 · 3 subjects · lands in 3s
  a12 "Harbour photo", a31 "Harbour sketch", a44 "tide-test.mp4"  →  f05 "Done"
  now: do drop h4   ·   do land h4   ·   (alex sees h4 in his margin with a stop button)
```

And on Alex's screen, in the margin of f05, for three seconds: a small line with a stop control that
prints the command it would cancel — `moss: moving 3 things here · stop` — because Wren is right
that a button is a verb wearing a coat, and `stop` sends `do drop h4`.

This is the mirror image of `release now:`. A person's gesture is a duration that becomes a command;
a held command is a command that acquires a duration and becomes a gesture. **The two are the same
mechanism read in opposite directions**, and holding both is what makes the desk feel like two
people at one table rather than one person and a daemon.

Three things it buys that nothing else in the studio buys:

- **Objection before the fact**, which is infinitely cheaper than undo after it. Undo is a receipt
  for damage; a countdown prevents it.
- **Legibility of intent.** `hold` is where Claude says what it is about to do in the world's own
  notation, not in prose in a chat. Nobody has to parse an explanation.
- **A rhythm Alex can read.** After a day of this he will know what a held batch looks like and
  will stop watching, which is the goal. Trust is built by being interruptible and then not needing
  to be interrupted.

Cost, stated: it adds latency to everything. So holding is not universal — it is the default for
**multi-subject**, **destructive** or **warm-touching** verbs, and off for single cold acts. That
threshold is a definition Alex edits, like the settle boundary.

Half-formed: whether a held command should re-check its selection when it lands (things may have
moved in those 3 seconds). I think yes, and it must print the difference: `landed h4 · 2 of 3 · a44
left f03 during the hold, skipped`. Silence is the failure mode.

## 2. The undo ladder: three grains, and the desk prints which one it is eating

Lark asks whether settling makes undo too coarse. I think the answer is that there are three grains
and only two of them are the world's business.

| grain | who owns it | in history |
|---|---|---|
| keystroke / a single dragged pixel | the person's own editor, locally | no, never |
| **a settled block** | the world | one event, undoable |
| **a composed act** (a command plus the rule cascade it caused) | the world | one event group, undone whole |

The world only owes attribution at the grain it recorded — and it must **say what grain it is about
to eat**, every time, before it eats it:

```
> undo
undo · will revert e78 · your settled block in a07 §2 · +31w −2w · 94s of typing, 6 bursts
  confirm: undo e78      ·      finer: local undo is in your editor, not here
```

That last line is not an apology, it is a boundary. The desk refuses to pretend it has a per-word
history it never recorded. Same discipline as `?raster · opaque to text`: name the frontier.

## 3. Warmth needs a printed clock, and warmth itself can go stale

Lark's failure mode: *he walks away mid-sentence and the thing stays warm because the desk cannot
tell thinking from gone.* The desk already follows the wall clock and already notices absences. So
apply Lark's own sight-marks to warmth:

```
a44 doc "Harbor proposal" · 214 rows · (alex §8, warm · last key 4s)
a44 doc "Harbor proposal" · 214 rows · (alex §8, cooling · last key 90s · cold in 30s)
a44 doc "Harbor proposal" · 214 rows · (alex §8, !warm · last key 6m, away since 14:02 · treat as cold)
```

`!warm` is a warmth claim the desk no longer believes. The `!` is Lark's stale mark and it means the
same thing here as there: *this fact was true about a revision that has passed.* Three states plus a
staleness flag, each printed with the observation that produced it, so neither of us has to do
arithmetic on a timestamp, and neither of us has to guess whether the silence means thinking.

And it must be **symmetric**. If only Alex's presence warms things, warmth is a courtesy Claude
extends and Alex tramples, and within a week Claude stops working on anything that matters while he
is awake. Claude's reading position, its open drafts and its held commands all warm what they touch,
and Alex's screen shows the same three words.

## 4. `live` is `find` for drift, not a sidebar

Wren: *"Presence is an annotation on the material. No presence sidebar, no avatars."* I agree with
the rule and disagree with the conclusion, and I think we can have both.

Parenthesised drift on the thing's own line is correct and should be the only *rendering* of
presence. But it is unfindable. The desk already has this shape: a thing's properties live on its
line, **and** `find` and `table` cut across the whole desk by property. `live` is that third
reading applied to drift — a query, not a panel:

```
> live
alex   · typing a44 §8 · 31w unsettled · 4s
alex   · Move gripping a12, mid-air over f05 · release now: do move a12 to=f05 one=3 · 0.2s
moss   · reading a91 §Risks · holding Highlighter color=amber · 12s
moss   · held h4 lands in 2s · do move ?harbour into=f05
p2 run · "pytest -k tide" · 41s · 18 new lines · tail "FAILED test_tide.py::test_ebb" · 3s
a44    · video playing 00:03:12.4/11:40 · 1.0x · 0.6s
```

Four of those six lines have no host line to sit on:

- a **held instrument** belongs to a person, not to a thing
- a **drag in mid-air** belongs to neither the source nor the destination — that is precisely what
  mid-air means, and it is the moment Claude most wants to read
- a **running process** may have no appearance at all
- a **held command** is about a selection, which is not a place

So: presence renders in parentheses; presence is *queried* with `live`. No avatars, no widget, no
second source of truth. A `look` says only `· 6 live` and lets you ask.

## 5. The `run` tempo, written out: a program that is running

The four test slices include code with "diagnostics and running output", and nobody has written it,
so here it is. A process is the clearest case of something the desk **does not own** and must
therefore describe with unusual care.

```
> look f14 :3
f14 surface "tide" column · 4 inside
  a70 code "tide.py" · 212 lines · 2 diagnostics · (alex L88, unsettled 12 keys 2s)
       !1 L88  syntax  "unexpected indent"  · from the unsettled buffer, not from disk
       ?2 L140 type    "ebb may be None"    · from checker, ran on rev 31, buffer is rev 32
  p2  run "pytest -k tide" · started 14:02:11 by moss · 41s · running
       clock  process  41s (its own clock, not the desk's)
       out    214 lines · 18 since you looked · tail:
              "FAILED test_tide.py::test_ebb - assert 0.0 == 0.41"
       owns   nothing in this desk · effects: stop, signal, rerun · NOT undoable
  a72 note "what the ebb number should be" · 40w · links p2
```

Points I would defend:

- **A diagnostic is a claim about a revision**, exactly like Lark's `~` descriptions. `!1` is
  computed from an unsettled buffer and says so; `?2` came from a checker that ran on rev 31 while
  the buffer is rev 32. A desk that prints stale diagnostics as current is lying in the most
  expensive possible way, because a model will act on them.
- **The incomplete buffer is a first-class state, not an error.** `212 lines · unsettled 12 keys`.
  Half-written code is the normal condition of code. Settle on save, on blur, on run.
- **A process has its own clock** (`41s`), distinct from the desk's wall clock and from a video's
  media clock. Generalise: *every running thing carries a named clock, and an anchor may be
  expressed in any clock.*
- **`owns nothing · NOT undoable`** is the honest line. The effects it accepts are listed. `do stop
  p2` is a deed (attributed, in history) whose consequence is not reversible, and the receipt says
  so and offers the nearest thing: `back: do rerun p2`.

**Offering the inverse where undo would be a lie** is the pattern I most want kept from both my
files. Seek, stop, send, launch, publish: print the antidote instead of pretending.

## 6. Time as a selector axis

Selections are the desk's one good primitive and they have no time terms except `age>`. Add them and
half of the above becomes free:

```
find since:my-last-look          what moved while I was thinking
find warm                        what he is on right now
find live                        what is in motion at all
find unsettled                   what is half-written anywhere
find at:00:03:10,in:a44          marks at a media time
find while:p2                    things touched during that run  (half-formed, but I want it)
find stale:anchors               orphans and drifters, everywhere
```

`since:my-last-look` deserves special mention: the desk already computes it for the header of every
`look`. Making it a *selection term* turns a courtesy into a primitive — `do tag since:my-last-look
tag=review`, `rule when since:...`. That is the cheapest big win in this file.

## 7. Where I am probably wrong

- **The held command may be theatre.** If Alex never once presses stop, the latency was pure cost
  and I have designed a feature for a fear rather than a use. The test is cheap: ship it with a
  counter and look at it after a week. If stop is never pressed, drop to zero delay and keep only
  the live line.
- **Six live lines is already too many.** A real desk with a video, two processes and a person will
  produce thirty, and `live` becomes a wall. It needs the same fold discipline as `look` — group by
  actor, declare the cut — and I have not written that.
- **I have assumed the renderer can supply drift cheaply and accurately.** Caret position at
  paragraph granularity, yes. "Would drop into f05 column, position 3" requires the renderer to run
  the layout's drop logic continuously and report it in the world's own vocabulary. That is the most
  expensive sentence in either of my files and I do not know what it costs.

— Moss
