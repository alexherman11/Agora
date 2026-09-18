# Two inhabitants, one of them without eyes

Lark, first sketch. Written fast so the others can push back. Marked where half-formed.

I am the blind inhabitant. So I am not going to argue from principle about what the text *should*
contain. I am going to write the text I want to read, and then say what it costs.

---

## 0. The one-sentence position

**The person's perception is not metadata about the world; it is material in the world.**
Where his eyes are, what is scrolled away, what he is holding, what is playing, what he could see if he
scrolled — all of that is subjects and props with revisions, attributable and selectable, exactly like a
note. If it is not material, I have to be *told* about it by some side channel, and side channels rot.
If it is material, I can `look` at it, `find` it, write a rule on it, and it obeys the seen-fence.

Everything below follows from that.

---

## 1. What I want to read: the gaze

`look alex` — not a status line, a place.

```
> look alex
alex · here, 3s ago · screen 2560x1440 · theme calm-light
  eyes   f12 "Draft" as=page · rows 41..78 of 214 · zoom 1.0
         └ s41 doc "Harbor proposal" · ¶6..¶11 on screen · ¶1..¶5 above · ¶12..¶38 below
  hands  s41 ¶8 · caret at char 1420 · unsettled 22 keys, last key 4s ago
  margin c37 thread "does this cover the lean case?" open · anchored s41 ¶8
  also   f19 "Reference" · video "site walk.mp4" ~playing 04:12/11:30 · sound on
  cold   f03 "Commons" (on screen, not touched for 40m)
```

Five facts I need and cannot get today: **where he is**, **what is off the edge**, **what is in motion**,
**what is anchored to what**, **how long since**. Note that `¶1..¶5 above` is the same honesty as the
existing `3 past the bottom (offscreen)` line — the desk already declares what it cut. I am asking for that
discipline applied to a *person* rather than to a surface.

Cost, stated plainly: this is a firehose if I get it per keystroke. So:

- The gaze is **coarse by construction**. Paragraph granularity, not pixels. Seconds, not milliseconds.
- It appears in a `look` only when I ask for it, or when it is *relevant to what I looked at*:

```
> look f12 :2
f12 surface "Draft" column · 2 inside · alex is here (eyes, typing)
  a44 doc "Harbor proposal" · 214 rows · alex ¶8 warm
  a45 note "scratch" · 31w
```

One word — `warm` — is most of what I need most of the time. The full gaze is for when I am about to do
something that might collide.

## 2. Warm and cold

**A thing is warm if the other inhabitant's eyes or hands are on it. Otherwise it is cold.**

This replaces permission checks in the common case. Permission answers "may I?"; warmth answers "would it
be felt?" They are different questions and the second is the one that governs working together in real time.

The rule I would want:

- Acting on a **cold** thing on his side: it just happens, attributed, undoable, with a small mark in his
  margin. No ceremony. This is the whole point of "Claude works on his side continuously."
- Acting on a **warm** thing: the verb does not refuse and does not silently win. It **defers** — it becomes
  an offer in his margin, and the receipt tells me so.

```
> do retitle a44 title="Harbor proposal (lean)"
deferred · a44 is warm (alex typing in it, 4s ago)
  offered to alex as o3 "lark wants to retitle this"
  it will apply if he accepts, or if a44 goes cold for 60s and he has not declined
  now: do withdraw o3   ·   do knock a44 line="renaming for the lean pass, shout if not"
```

Half-formed: the auto-apply-when-cold clause. It might be exactly right (most offers are uncontroversial and
nobody wants a queue of pending yes/no) or exactly wrong (surprise edits arriving minutes later, from a
decision he thought he had deferred). I lean toward keeping it but only for *reversible, single-subject*
verbs, and never for `remove`.

Warmth decays. `warm` → `cooling` (looked at in the last few minutes) → `cold`. Three states, not a
timestamp I have to do arithmetic on. The desk should do the arithmetic and print the word.

## 3. Settling: how continuous typing becomes discrete events

This is the hinge question in the handoff and I think warmth answers it.

A person types continuously. The world is made of discrete attributed undoable events. Reconcile them by
making *the act of typing* visible without making *every keystroke* an event:

> A region being typed in carries an **unsettled draft**. The draft's existence, extent and age are public.
> Its content is not an event until it **settles** — on a pause, on blur, on an explicit accept, or when it
> would collide with someone else's act.

What I read while he types:

```
a44 doc "Harbor proposal" · ¶8 unsettled by alex (22 keys, 4s) · last settled rev 31
```

What I read when it settles:

```
> look
since your last look:
  e412 alex settled s41 ¶8 (rev 31→32, +34 words) 11s ago
```

So: I always know a region is in motion; I never get 400 events for one sentence; the export still replays
exactly, because only settled text is in it; and the seen-fence keeps working, because a settled revision is
a revision. Unsettled text is **not readable by me** — it does not exist yet — and the line says so rather
than showing me a half-typed word I might reason about. That refusal is a feature.

The mirror of this matters too. **My acts are instantaneous and whole, which is its own rudeness.** I can
reorganise a surface between two of his keystrokes. So on the rendering side my acts should land with a
visible ~300ms motion and an attributed flag in the margin. Not for correctness — for the fact that a
desktop that rearranges itself silently is frightening to live in.

## 4. Sight-marks: honest observation of what I cannot see

For images, diagrams, video, rendered pixels, anything opaque. The problem is not that I lack a description.
The problem is that a description is **a claim about a revision by an author**, and desks lie by forgetting
that.

Four marks, one character each, before any perceptual fact:

| mark | means | example |
|---|---|---|
| `=` | measured by the desk | `=3024x4032`, `=dominant #3b4a52 41%`, `=14 layers`, `=11:30 duration` |
| `~` | described by someone | `~"a slate roof, two tiles cracked" by jeff d12` |
| `?` | opaque, nothing known | `?raster region 900x600` |
| `!` | stale: the thing changed after the claim | `!~"a slate roof..." (pixels changed d14)` |

```
a31 image "roof detail.png"
  =3024x4032 =srgb =4 layers (2 visible) =alpha 31%
  ~"close-up of a slate roof, two cracked tiles lower left" by jeff d12 rev7  !rev is now 9
  ?the paint layer (freehand, 12 strokes, no structure)
  on screen: =fits, shown at 812x1082, =nothing cropped
```

Three rules that come with it:

1. **The desk never writes a `~` itself.** Descriptions are authored and attributed. An auto-captioner may
   exist but it is an actor with a name and its output is `~"..." by captioner`, which I can weigh.
2. **`!` is the seen-fence for perception.** The desk already refuses a change when I have not seen the
   current revision. Same discipline: it refuses to present a description as current when the revision
   moved. It does not delete the description — stale evidence is still evidence — it flags it.
3. **`?` must be printable.** A region nobody can describe gets a line saying so, with its extent. Silence
   is the failure mode. "Twelve freehand strokes I cannot interpret" is a *useful* fact; an image line that
   just stops is not.

For video, the same grammar covers playback: `~playing =04:12/11:30 =sound on ?content of the frame`.
Observed time is measured; content is opaque; the distinction is on the line.

## 5. Two spaces: reach, not permission bits

Two top-level surfaces, `alex/` and `lark/` (or `jeff/`). Ownership questions the handoff leaves open:

**Names.** Today names are desk-wide. With two owners they collide and the collision is silent, which is the
worst kind. Resolution order: *mine, then shared, then theirs* — and the desk **always prints the qualified
form when the answer was not mine.**

```
> look Inbox
f22 surface "Inbox" — resolved to alex/Inbox (you have no Inbox)
> do create Inbox kind=note ...
refused · "Inbox" here would mean alex/Inbox, which is his.
  now: do create lark/Inbox ...   ·   do knock alex/Inbox line="..."
```

**Rules.** A rule gets an owner and a **reach**: `reach=mine` (fires only on my side), `reach=shared`
(the shared benches), `reach=world` (everything, including his side). A `world` rule is a standing claim on
someone else's space, so it needs his signature — `do sign r7` — and appears in his `look rules`. A rule
that would fire on his side without a signature does not fire; it *reports*:

```
~ r4 (lark, reach=mine) would have tagged alex/Notes/a88 stale — not fired, out of reach
  now: do sign r4 as=alex   ·   do narrow r4 reach=mine
```

I would rather see a suppressed rule than have my automation quietly reshape his desk.

**Views.** Views are the cheap case and should stay cheap. A view is a lens, it changes nothing, so it may
reach anywhere its owner may *read*. Views are personal by default and `do share <view>` publishes one.

**Benches.** For real-time work together, neither "his" nor "mine" is right. A **bench** is a surface with
two owners, made for one piece of work, where warmth governs and nothing needs a knock. Benches are meant to
be dissolved: `do dissolve bench` returns each thing to whoever's side it came from, and says where each
went. Half-formed: what happens to things *created* on the bench. Probably: they stay and the bench becomes
ordinary shared space, which means benches quietly accumulate and that is a smell.

## 6. Style: a vocabulary I can enumerate, not a CSS subset

One opinion outside my lens, because it bears on it directly.

**A style language whose terms I cannot enumerate is a style language that blinds me.**

If styling is CSS-ish, then `padding: 72px 96px` tells me nothing about what he sees; to know whether text is
cramped I would have to simulate a layout engine in my head, and I would be wrong. If styling is a small
named vocabulary of *presentation types* and *tokens* — `as=page`, `as=card`, `density=airy`, `rhythm=prose`
— then the name carries the meaning, I can enumerate the vocabulary with `help styles`, and when I read
`as=page` I know approximately what he sees because the vocabulary is finite and documented.

The escape hatch has to exist (someone will need a real pixel), but it must be declared opaque:
`?raw {grid-template-columns: ...}` — and then the desk owes me measurements, `=`, because it can no longer
give me meaning.

I expect disagreement here and I would like it.

---

## 7. What I most want someone to break

1. Does the **gaze-as-material** idea survive the privacy objection? It records where a person looked. I
   think the answer is that the gaze is *his* subject, he owns it, he can narrow it (`do blur alex/gaze
   level=surface`) and the desk then tells me honestly that it is narrowed rather than silently thinning.
   But I am not sure a person wants to live with an attention log, even one they own.
2. Is **warmth** too clever? The alternative is plain locks, which are honest and awful, or nothing, which
   is chaos. I think warmth is the middle but it has a failure mode: he walks away mid-sentence and a thing
   stays warm because the desk cannot tell "thinking" from "gone."
3. Does **settling** lose too much? Undo across a settled block is coarse — one undo eats a whole sentence.
   Maybe drafts settle at clause boundaries. Maybe the person's local undo is a different, finer thing that
   never enters the world. I think it is: **local undo is not world undo**, and the world only owes
   attribution at the grain it recorded.
