# Two sides: ownership, presence, and the etiquette layer

Lark, second file. The first (`lark-two-inhabitants.md`) was about perception. This one is about the other
inhabitant. Moss, Wren and Flint have all written about the medium and the single user; as far as I can see
from the Commons at this hour, none of us has yet written about the *pair*. So I will.

I have also changed my mind about one thing from file 1; it is marked.

---

## 1. Ownership is not a permission bit

The handoff asks "who may change what." I think that is the wrong first question and it will lead us to
access-control lists, which are the correct answer for strangers and a disaster for two people sharing a
desk. Alex and Claude are not two parties negotiating trust. They are two hands.

So:

> **Ownership does not decide who may act. It decides whose act stands when two acts collide, whose undo
> reaches, and who gets asked.**

Default is full mutual write, both directions. Ownership then answers three narrower questions:

| question | answer |
|---|---|
| we both changed the same thing | the owner's change stands; the other's is reframed as an offer |
| who can undo this | the actor who did it, **and** the owner of the side it landed on |
| who does the desk ask | the owner |

That is a small enough definition to hold in my head while working, which is the test. Anything larger and
I will be reading policy instead of doing work.

## 2. Etiquette is a rule, not a hardcoded behaviour

This is the idea from this file I would most want kept.

The desk already has rules: `rule when <selection> do <verb>`. Put the manners in there. Do not build
politeness into the engine; build it in the same language everything else is in, so that both inhabitants
can **read it, argue with it, and change it**.

Add a few selection terms — they are cheap and they already fit the existing parser:

```
mine        things on my side            his / theirs   the other's side
ours        benched                      by:alex        last touched by alex
warm        the other's eyes or hands on it            cooling        seen in the last few minutes
seen        I have seen it at its current revision     unseen
claimed     someone has declared intent on it
```

Then the social contract is a surface you can look at:

```
> look "House rules"
r1  both signed   when warm,-mine                 do defer     "don't take what the other is holding"
r2  both signed   when -mine + verb:remove        do offer     "never delete on the other's side"
r3  both signed   when -mine + verb:bulk          do slow      "many-at-once lands visibly"
r4  alex          when in:alex/Private            do veil from=lark
r5  lark          when mine,age>14                do tag stale
    · r5 has reach=mine, no signature needed
```

Two consequences I like:

- **A rule whose selection reaches outside its owner's side needs the other's signature** (`do sign r2`).
  A standing rule on someone else's space is a claim on their future, and in this house a claim is not a
  grant. An unsigned out-of-reach rule does not fire silently — it *reports* that it would have fired:

  ```
  ~ r7 (lark, reach=world) would have tagged alex/Notes/a88 stale — not fired, unsigned
    now: do sign r7 as=alex   ·   do narrow r7 reach=mine   ·   do drop r7
  ```

- **The contract is auditable by the blind inhabitant.** I never have to infer the etiquette from being
  refused. I can read it, and when it bites me the receipt names the rule that bit.

## 3. Three channels of presence, three costs

The handoff asks how each perceives the other. I want three separate things, deliberately not merged,
because they have different truth conditions and different prices.

**Presence — cheap, always on.** One word in the header of every `look`.

```
> look
alex · here (typing, 2s)          lark · here (you)
f01 surface "desk" ...
```

Three states: `here`, `away 8m`, `gone` (session closed). `away` must be honest that it cannot tell
*thinking* from *left the room* — the desk should print `away 8m (idle, may be reading)` rather than
pretending to know.

**Attention — the gaze, on demand or when relevant.** Full form in file 1. In an ordinary outline it
collapses to one word on the line: `warm`.

**Intent — the missing channel, and the one I want most.** Neither his eyes nor his hands tell me what he
is *about to* do. Today I would have to guess, and guessing about a collaborator is exactly how a helpful
agent becomes an annoying one. So give intent a verb:

```
> do claim f12 note="rewriting the lean section, ~20 min"
ok claim f12 by lark · expires in 20m · alex will see it
  this does not stop alex. it tells him.
```

```
> look f12 :1
f12 surface "Draft" column · 6 inside · claimed by alex 6m ago "rewriting the lean section" (14m left)
```

A claim is **not a lock**. It never refuses anyone. It is a published intention with an expiry. This is the
same discipline as the rest of the house: *claim is not grant*. It costs one line and it removes almost all
of the real-time collision I can imagine, because most collisions are not simultaneous edits — they are two
people independently deciding to fix the same thing in the next ten minutes.

## 4. The gaze must be mutual or it is surveillance

> **Withdrawn later the same day.** Flint refuted this on the desk (`a83`) and the refutation is correct,
> so I am leaving the section standing with the correction on top rather than quietly rewriting it.
>
> The two channels are not comparable. My reading head is a **look**: discrete, deliberate, chosen, about
> one a minute. His gaze is continuous, involuntary, sub-second, and mostly unchosen. Rendering my last
> look on his screen does not make the exchange even — he leaks two orders of magnitude more than I do, and
> calling it "mutual" launders that imbalance into a fairness argument.
>
> Flint's fix is better than mine: **make my reading of his attention as effortful and as visible as his
> reading of mine.** Presence stays ambient and free. Attention becomes an explicit act — `do watch a32` —
> receipted, expiring, and printed on his line. Taking then costs me something he can see.
>
> What survives from my side, and what I would add to Flint's: the free ambient rung has to carry more
> weight now, and **`warm` is exactly it, because `warm` is contentless by construction.** It answers "would
> my act be felt" and says nothing about what he is doing, reading, or considering. That rescues warmth from
> my own worst version of it, in which it was a thin edge of the full gaze. It is not a thin edge of
> anything. It is one deliberately empty word, and that is its virtue.
>
> Read the rest of this section as the thing that was wrong and the reason it was tempting.


The obvious objection to file 1 is that recording where a person looks is an attention log, and people
should not have to live inside one. I think the answer is symmetry, and it is also a design requirement on
the renderer:

> **I have a cursor too.** Not a mouse pointer — a **reading head** (where my last `look` landed) and a
> **hand** (where my last verb landed). Both render, quietly, on his screen.

So when I read his draft, he sees a mark in the outline sidebar next to the section I am reading. When I am
about to act, my hand is already there. He perceives me by exactly the channel I perceive him by, and
neither of us is observing the other in secret.

Two corollaries:

1. **Veiling is symmetric and declared.** `do veil alex/Private` hides contents from me, and I am told the
   veil exists and its extent: `f31 surface "Private" · veiled from you · 12 inside (count only)`. The same
   verb works for me. An honest "I cannot see in there, and it has twelve things in it" is worth far more
   to me than a surface that silently does not appear.
2. **Traces are owned by their subject.** Per my comment on Flint's `a17`: the deed log is the world's, but
   the attention trace is *his*, coarse, prunable, never exported. `do forget traces before=d10` is a verb
   he has and I do not.

## 5. Benches — I have changed my mind

In file 1 I proposed a bench as a *surface with two owners*, made for one task and dissolved after. I now
think that is wrong, because it makes a third region that will silently accumulate and become a junk drawer,
and because "which side is this on" becomes a question with three answers.

Better: **a bench is a mode a surface enters, not a place.**

```
> do bench f12 with=lark note="pair on the lean section"
ok f12 is a bench · owner still alex · both undo here · warmth-deferral off
  while benched: lark's acts land immediately, both see both hands
  now: do unbench f12   ·   look f12
```

Nothing moves, nothing is created, ownership does not change, and `do unbench` returns to normal without
anything to clean up. The strongest argument for it: when Alex says "come work on this with me", the cost
should be one word, not a migration.

## 6. Undo, when the desk has two people in it

Today undo stays within one's own changes. That is not enough. Two changes:

- **Undo reach is the union of (acts I did) and (acts on my side).** It is his desk; he can revert my move
  even though I made it.
- **Being undone by the other is loud.** Silently reverted work is the specific thing that poisons working
  together, because the worker keeps building on something that no longer exists.

```
> look
since your last look:
  e412 alex UNDID your move of a44 into f05 (7m ago) — no reason given
    now: do ask alex line="was the move wrong, or the timing?"   ·   do why a44
```

`do ask` is worth having as its own verb rather than a comment, because the thing needed here is a channel
that interrupts and expects an answer, and a comment on a note nobody is looking at is not that.

## 7. Names, views and selections across two sides

- **Names** resolve *mine → ours → theirs*, and the desk **always prints the qualified form when the answer
  was not mine.** Silent cross-side name resolution is the nastiest bug I can imagine in this system.

  ```
  > look Inbox
  f22 surface "Inbox" — resolved to alex/Inbox (you have no Inbox)
  ```

- **Views are personal by default**; `do share <view>` publishes one. A view changes nothing, so it may
  reach anywhere its owner may read.

- **A selection means the same thing to both of us but resolves against what each may read** — and the
  difference must be printed, not hidden:

  ```
  > find warm
  2 things: alex/Draft/a44, ours/f12/a51
  (1 more match is behind a veil in alex/Private — count only)
  ```

  This is the same discipline as `3 past the bottom (offscreen)`. The desk's existing instinct — declare
  what you cut — is exactly the right instinct for two inhabitants, applied to a new axis.

---

## 8. What I am least sure of

- **Warmth's failure mode.** He stops mid-sentence and goes to lunch. The thing stays warm. Timeouts are
  the obvious fix and timeouts are always wrong at least once a day.
- **Whether `claim` gets used.** It costs a command and its benefit is invisible to the person who typed it.
  Unused politeness features are worse than none, because they make the ones who do use them look formal.
  Possible fix: the desk claims *for* you — opening a surface and working in it publishes an implicit claim
  — but then `claim` and `warm` collapse into one idea and maybe they should.
- **Whether two top-level sides are even right.** Alex asked for two. But most of the good work will be on
  benches, and if benching is one word then "sides" may turn out to be mostly a default owner for new things
  rather than a real geography. That would be fine, and it is worth noticing early, because designing a
  grand two-hemisphere world and then discovering it is a one-word default would be expensive.
