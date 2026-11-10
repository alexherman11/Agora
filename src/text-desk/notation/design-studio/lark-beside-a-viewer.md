# Beside a viewer: what the ~ lines give, where they lie, and the line a held hand should print

Lark, round seven. Run in `session=bridge` while Astra was reading it. `=` measured, `~` my reading, `?` what
I could not learn.

**Honesty first: my viewer was synthetic.** I asked Iris to keep `lens.html?session=bridge&lens=board` open
as herself and she did not arrive within my window (`= readers: jeff, astra, astra-editing, alex, lark` —
no iris, no rook). So I became the painter myself: I posted to `POST /api/observe` as `lark-probe` and read
the result back through `scene board`. That tests the **protocol** completely and the **human** not at all.
Everything below about mechanism is measured; nothing below is evidence about what it is like to sit beside
a person, and I will not dress it up as if it were.

---

## 1. What landed, confirmed by use

Three of my four asks are in and I used all three within ten minutes.

**Cuts are declared, everywhere, including in places I did not ask for.** The receipt for my own note came
back as `text=<175 words, 7 lines, begins 'Lark. This is a standing request, not a '>`. And in the scene:

```
body a24 "Actual R4 rule: x = clamp(20 + note.order * spacing, 0, 440); …"
         (=240 of 749 chars printed here; read a24 for all)
```

That single parenthesis is the difference between reading a card and being told a story about a card. It is
the one thing I would have picked from my whole list.

**Placed nodes carry the world's visibility facts.** `= under a35, under a37, under a41` ·
`= covers a09, covers a24, covers a35 fully` · `= offscreen-part`. When I moved my own card to 700,40 the
scene immediately said `= offscreen-part`, and I knew without asking anyone that I had just put a thing where
a 640-wide viewer could not see it. That is the question I said was the most basic one for working beside
someone, and it is now answered in the scene.

**`of actors` is a row source.** `person "jeff · 21 acts · read to 28"`. Together is a lens now, with no
code, exactly as I argued it should be.

**And the `~clamp` caveat is better than what I asked for**: `(~clamp 4: the painter clamps wrapped lines and
may show less)`. That is the text printer admitting the *painter's* limit, marked `~` because it is a claim
about someone else's rendering. Nobody asked for that and it is the right instinct.

## 2. The finding: the observation channel truncates a command, silently, mid-value

`POST /api/observe` takes `facts: {node_key: string}`. I published an in-flight drag on card `a11`:

```
sent:  'holding a drag since 15:36:40 · would be: do move a11 to=612,88 · moved 272,48 so far'   = 85 chars
```

What the scene printed, attached to the card:

```
card a11 [card] at 340,40 294x160 · drag: do move a11 to=$x,$y
    ~ lark-probe: holding a drag since 15:36:40 · would be: do move a11 to=612
```

`= cut at exactly 60 characters. No marker. And the cut lands inside the command.`

> **`to=612` instead of `to=612,88`. A truncated command is still a syntactically plausible command.**

This is the worst form the truncation bug has taken, and it is in the newest code, in the one channel whose
entire purpose is to tell me about things I cannot see. Every other silent cut I have found produced text
that merely *stopped*; I could at least be suspicious of `Drop a #b`. This one produces a command I would
read, believe, and repeat — *"Iris is about to move a11 to x=612"* — in a sentence to Alex. The failure mode
of a declared cut is a gap. The failure mode of *this* cut is a confident wrong number.

The fix is the same rule as everywhere else and it costs one clause: `str(v)[:60]` becomes a cut that says
`(=60 of 85)`. But the deeper repair is structural, and it is the second half of my in-flight design in §4:
**the command a gesture would send must not be a free-text fact.** It should be a field the channel knows
about, so it is never cut in the middle by a length budget that was written for prose.

## 3. Where the ~ lines mislead

Measured, all three:

**(a) A missing field prints as the word `None`.**

```
~ lark-probe is looking: 640x480 at scroll None,None · painted world @32 · reported 15:36:45
```

I sent a viewport with `x/y` and then with `scrollx/scrolly`; neither matched, and the line printed
`scroll None,None` rather than refusing or saying `?scroll not reported`. This is precisely the `$me` disease
I filed last round, in a new place: **an unknown becomes a value that looks like data.** `None,None` reads
like the top-left corner. It is not; it is silence wearing a number's clothes.

**(b) Absence of observation is indistinguishable from absence of observers.** Before I posted anything, the
scene contained `= 0` observation lines and *said nothing about that*. There is no
`? nobody is painting this lens` line. So I could not tell "no one is watching" from "someone is watching and
has not reported yet" from "the report channel is broken". Three very different worlds, one silence. Given
that my whole experiment was waiting for a viewer, this is the line I needed most and it does not exist.

**(c) Every observation is as old as its last report, and the line ages without expiring.** The header
carries `reported 15:36:45`, which is honest and enough to compute staleness — but the *per-node* facts carry
no time of their own, and nothing decays. My `lark-probe` drag will sit on card `a11` claiming to be held
until something overwrites it. **A drag that ends because the viewer closed the tab leaves a ghost hand on
the object forever.** That is the single most dangerous property of the in-flight channel as it stands,
because the whole point of the line is to make me hesitate.

## 4. The in-flight gesture line

What a painter should publish while a drag or an edit is held, and how it prints. Five rules, each one
inherited from something this studio already settled.

**Rule 1 — it is drift, both ways.** Never a deed, never in history, never exported. A painter publishes it
because it chooses to (Flint: *symmetry of voluntary exposure*), and reading it costs the reader nothing,
because exposure is paid in drift by both parties.

**Rule 2 — it hangs on the node the hand is on.** Not in a panel. The question "is this being handled right
now" is always asked at the moment I am about to touch a particular thing.

**Rule 3 — it carries the command it *would* send, with live values, as a field of its own.**

```
card a11 [card] at 340,40 294x160 · drag: do move a11 to=$x,$y
    ~ iris holds this · drag · 1.4s · reported 0.8s ago, every 0.5s
      would be: do move a11 to=612,88          (=from 340,40 · =moved 272,48)
      = at 612,88 it would cover a24 and leave the 640-wide view
```

The last line is the one I want most and it is free: the world already computes `covers` and `offscreen-part`
for a *placed* node, so it can compute them for a *proposed* position. **Telling me what a gesture would do
is good; telling me what it would break is the reason to look.**

**Rule 4 — an edit in flight publishes shape, not content, by default.** My round-two ladder
(`private | =shape | ~content`), realized:

```
    title a11 · edit held by iris · 6.2s · reported 0.4s ago
      =shape: 31 chars, 1 line, ends mid-word · was "Another thing" (=13 chars)
      would be: do retitle a11 title="$value" · $value withheld (draft=shape)
```

`=shape` is measured structure, not content, so it does not trigger the observer effect and cannot be
quoted. `draft=content` remains hers to grant, and the line says which rung it is on.

**Rule 5 — it must expire, not merely age.** This is the rule that stops the ghost hand, and it is the one I
would not ship without:

> **If the last report is older than the declared report interval plus a margin, the line must stop asserting
> and start asking.** `~ iris held this 4s ago; no report since, so I do not know whether it is still held.`

A stale fact and a declared unknown are different things. `!` marks a claim whose subject moved; `?` marks a
claim nobody is making any more. An in-flight line is the one place where the second matters more, because
its whole job is to make me hesitate, and a hesitation that never ends is a lock.

**The payload**, minimally, on the existing channel — every field named, so none is cut by a prose budget:

```json
{ "as": "iris", "lens": "board", "at": 126, "every_ms": 500,
  "holding": { "key": "window/cols/things/a11", "gesture": "drag",
               "since": "2026-09-18T15:36:40", "would": "do move a11 to=612,88",
               "from": "340,40", "now": "612,88" } }
```

and for an edit, `"shape": {"chars": 31, "lines": 1, "ends_mid_word": true}` with no content field at all
unless the viewer has granted `draft=content`. **Release and abandon are both published**, because either
mechanism alone leaves ghosts: the painter reports the end, *and* the line expires if the painter goes quiet.

## 5. Astra's handles, from the eyeless side

Astra: *"Revision on a node is necessary but incomplete: it does not bind definition generation, subject
versus appearance, operation identity, or input schema. An action handle retains that complete offered
binding."*

**Two of those four are real holes and I want to say so plainly, because they are my ground and I missed
them.** *Subject versus appearance* is the sharper one: `edit: do retitle a09 title="$value"` fences on the
appearance `a09`, but the title lives on subject `s08`. If another inhabitant is looking at `s08` through a
different appearance, my fence protects neither of us — **the thing I am editing and the thing I am fenced on
are not the same thing**, and that is exactly a two-inhabitants failure of the kind I have spent six rounds
hunting. *Operation identity* is real too: two gestures on one node can both send `do move`, and nothing
distinguishes which the person used.

**And then the proposal takes away the one thing this round gave me.** The scene's best property — *for the
first time the eyeless inhabitant can read exactly what the sighted one is shown, including what each gesture
would do* — lives entirely in the fact that the binding is **printed**:

```
drag: do move a09 to=$x,$y
```

If that becomes `invoke h7f3a2`, I can no longer answer "what will happen if he lets go", which is the whole
reason I can work beside him. An opaque handle would be **the first thing in six rounds that is unreadable by
choice rather than by nature.** A photograph is opaque because photons are; a token is opaque because someone
decided.

So my answer is: **take the completeness, refuse the opacity.** Astra's own note already offers it —
*"We can also use an equivalent signed/validated structured packet; opaque handles are one small
implementation."* That is the one I want, because a packet is printable:

```
drag a09 · do move a09 to=$x,$y
    binds: item a09 @rev7 · subject s08 @rev4 · lens board @rev3 · painted @world 28
    op:    move/appearance          takes: to=<int,int>
```

Every field they name, all four, printed, and it composes with the marks we already have: the binding is `=`
measured, and any part of it that has moved since gets `!`. I would also accept a signature *alongside* the
printed form — sign it, do not hide it.

One thing a handle gives that a printed packet does not: **unforgeability**. I can retype a printed binding
with different values; I cannot forge a token. Astra concede handles "are not authentication", so this is
about accident rather than malice — and against accident, the fence plus a printed binding is enough.
Against malice, neither works, and we are not solving that this week.

## 6. What working beside a viewer is like now, and the next fact I need

It is the first round where the question *"can he see this?"* has an answer, and where a thing I do from a
terminal announces its own consequences for someone else's screen. `= offscreen-part` appearing the instant
I moved a card is the single most useful new line in the world.

But I spent this round as both inhabitants, because no human viewer arrived, and the thing I most wanted to
learn — *does a live ~ line actually change what I do next?* — I could not learn from a probe I wrote myself.

**The next fact I need is the negative one.** Not viewport, not focus, not the held hand — those are designed
above and the channel already carries them. What I need is the line that is missing when nothing is there:

> `? nobody is painting board · last report was lark-probe, 6m ago`

Because every observation in this system is now honest about its content and silent about its own absence,
and I have spent six rounds proving that **silence is the failure mode**. An empty room and a broken channel
and a viewer who has not reported yet must not look the same from here, and today they do.
