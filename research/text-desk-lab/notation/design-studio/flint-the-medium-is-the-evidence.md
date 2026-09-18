# Flint, second file: the combined language retested, and what the studio desk itself proved

Two parts.

Part one: the four of us have now produced a lot of notation. I took the combined version back to the
document slice and rewrote it, to find out whether it composes or merely coexists.

Part two: the more interesting one. We were given a shared instance of the system we are designing for, and
told to notice how sharing it feels. It broke in four specific places in ninety minutes. Those breakages are
the best evidence in this studio, because nobody designed them as a test — and three of the four are things
we are all cheerfully proposing to build again.

---

# Part one: does the combined language compose?

The pieces on the desk as I write, taking the best version of each:

| from | piece |
|---|---|
| Moss | act / settle / pulse / run — tempo declared per material and instrument |
| Moss | the durable form of a gesture is an ordinary command; the gesture is evidence on the event |
| Wren | inline what is dense, anchor what is sparse |
| Wren | style by the desk's own selection language: `when <selection> : <properties>` |
| Wren | the anchor grade is compulsory and never rounded up: `exact / drifted / orphan` |
| Wren | a measurement of a rendering carries its conditions |
| Lark | sight-marks: `=` measured, `~` described-by-someone-at-a-revision, `?` opaque, `!` stale |
| Lark | bare `measure` must enumerate what is measurable |
| Lark | presence / attention / intent as three channels with three costs; `claim` is not a lock |
| Lark | etiquette as readable rules, not engine behaviour |
| Flint | anchors are addresses; a pulse prints a law; probe and diff; holding; bulk |
| Flint + Wren | structural opacity (forbidden in chrome) vs metric opacity (unavoidable, never terminal) |

Here is the document slice again, written in all of it at once. This is the honest test: not whether each
idea is good, but whether eleven good ideas fit on one line without the line becoming unreadable.

```
f20 surface "Weekly report" window · 980x1240 · =role doc-window · alex(own) · claimed by alex 6m "the lean section" (9m left)
  a30 bar "Doc tools" · =role toolbar · instruments: style link comment image suggest · ?4 collapsed into More
  f21 rail "outline" of headings:s31 · =role doc.outline · 6 headings   (alex at #4 · flint at #3 · moss away 8m)
    #1 Summary      84w
    #2 Scope       210w   1 mark !orphan
    #3 Budget      366w                      <- flint
    #4 Risks       402w   2 marks, 2 open    <- alex, typing
    #5 Timeline    290w
    #6 Sign-off     60w   - [ ] 3
  a31 doc "Weekly report" · =role page · 1840w · 6 sections · 5 marks · 2 open · saved 14:02
       ?metric 7 pages (measure a31 for conditions)
       (alex caret #4/3+12ch, unsettled 40w since 14:21:58 · flint reading #3 as of 14:20:10)
  f22 rail "margin" of marks:s31 · =role doc.margin · 5 marks · 2 open · 1 resolved folded · 1 orphan
    m9  comment !orphan  alex  #2 ("Q4")                      last seen e388
         -> do reanchor m9 at=#2/2 (nearest, uncertain) · do read a31 #Scope
    m3  comment =exact   alex  #4 ("the harbor lean is real but small")   open, 2 replies
    m4  comment ~moved   flint #4 ("40ms")                                open
    m7  link    =exact   moss  #3 ("supplier B") -> s90 "Supplier B contract"
```

### It composes. Three things I did not expect.

**1. The sight-marks turned out to be the glue, and they are Lark's, not mine.** I proposed `OPAQUE` in
capitals and Wren proposed grades and I proposed staleness suffixes, and all three collapse into Lark's four
characters sitting in front of a value: `=role`, `?metric`, `!orphan`, `~moved`. One character, always in the
same position, answering the only question a blind reader has about any fact on any line: *how do you know
that?* I underrated this note when I first read it and I want to say so in the file.

**2. The line got shorter, not longer.** I expected eleven ideas to bloat the line. They did the opposite,
because most of them are *rules about where a fact goes* rather than new facts: drift into parentheses,
provenance into one character, style into a name, presence onto the line of the thing being touched. The
combined notation is less verbose than my own file's version of the same slice. That is the strongest
evidence I have seen today that the four of us converged on something real rather than four compatible
opinions.

**3. One collision.** Wren's rail line and my pulse-law rule fight over the same real estate. `(alex at #4 ·
flint at #3 · moss away 8m)` is a parenthesised drift block per Wren, but my law rule says a pulse must print
a law or say `unpredictable`, and a reading position is genuinely unpredictable. Writing `(alex at #4
unpredictable · flint at #3 unpredictable · moss away 8m unpredictable)` is absurd. Repair: **`unpredictable`
is the default and goes unsaid; a law is what is remarkable and gets printed.** My rule was stated backwards.
A playhead prints `from 01:23.4 at 1.0 as of 14:22:07`; a caret just prints where it was and when.

### What still does not work

**The claim line.** `claimed by alex 6m "the lean section" (9m left)` sits on the window, but Alex's claim is
about a *section*, not the window. Claims want to land on anchors like everything else, and then a rail can
show them, and then Lark's worry about claims going unused gets a cheap fix: the claim is implicit in the
caret's anchor and is just displayed. I think claim and warm do collapse into one idea, and it is *the anchor
you are on*.

**Two settles at once.** `(alex ... unsettled 40w since 14:21:58)` is fine alone. But if I am also unsettled
in #3, there are two live drafts of one document with no merge story, and every one of us has quietly avoided
this. It is the real-time collaborative editing problem and none of our notation touches it. It should be
named as unsolved rather than left to look solved.

**Nothing here handles bulk.** Everything above is a 1840-word document, which is small. The moment this is a
4000-line file or a 412-row sheet, all of it — rails, marks, outline, presence — has to work against material
that is never enumerated. I do not know that it does, and I did not test it, and neither did anyone else.

---

# Part two: the studio desk is the evidence

We were given a shared desk and told to notice. Here is what it did, with receipts. I am not complaining
about a research prototype; I am reporting that four independent designers, working normally for an hour,
hit four failures, and that we are all currently proposing to rebuild three of them.

## Failure 1: the fence is on the container, so unrelated work collides

My first three notes were refused:

```
ERR !! since your last look: e7 create f03 by moss; e8 create f03 by moss; e9 create f03 by moss
stale: f03 changed since you last saw it; look at it again before acting
```

Moss had created three notes in the Commons column. I was creating a fourth. These acts do not conflict in
any sense a person would recognise — nothing I wrote depended on anything Moss wrote — but the seen-fence is
on the *container's* revision, and creation bumps it.

The seen-fence is a genuinely good invention and I do not want it removed; it is exactly right when I am
about to rewrite something that changed under me. But it is fenced on the wrong noun.

> **The fence belongs on what I am changing, not on what contains it.** `create` conflicts with nothing and
> should be fenced on nothing (at most a title collision). `move` is fenced on the thing moved and the
> destination's *layout*, not its membership. `rewrite` is fenced hard, as now.

The cost of getting this wrong scales exactly with how shared the desk is, which is to say it is a small
annoyance for the one-inhabitant desk that exists and a serious one for the two-inhabitant desk Alex wants.
Four of us made it unusable-ish in an hour; imagine a rule firing every few seconds.

## Failure 2: the change digest is a list of events, and events are not what I want to know

My second look:

```
!! since your last look: e13 create f03 by wren; e14 create f03 by wren; e15 comment s20 by wren;
e16 comment s16 by wren; e17 comment s18 by wren; e18 create f04 by wren; e19 create f04 by wren;
e20 create f04 by wren; e21 create f03 by lark; ... [47 events]
```

Forty-seven events. I could not learn a single thing from them. Not one title. Not one word of what was
said. `e15 comment s20 by wren` does not tell me that Wren had disagreed with my style note — I discovered
that four calls later by examining my own note on a hunch.

This matters more than it looks, because "each look begins with what others changed since your last look" is
*the* mechanism by which two inhabitants stay in contact, and it is the mechanism the whole shared-desk design
leans on. It is currently a log, and a log is the least useful possible form for this.

What I wanted, every single time, in order of decreasing urgency:

```
since your last look (18 min, 47 changes by wren, lark, moss):
  touching you   3 comments on your notes (a17 wren, a19 lark+wren, a21 wren+lark) · read comments:new,mine
  new            Vocabulary +6 (lark: warm claim gaze veil reach bench) · Commons +8 · Disagreements +2
  moved          nothing
  (nobody is here now; wren last acted 40s ago)
```

> **A change digest is by thing and by meaning, not by event, and it is sorted by whether it touches the
> reader.** The single most valuable line is "three people replied to you". It was the one thing the desk
> never told me.

This generalises to something I would put in the contract: the desk already knows how to declare what it
cut (`3 past the bottom (offscreen)`). It should apply the same instinct to *time*: declare what happened,
summarised, with the cut stated, rather than enumerate.

## Failure 3: attribution failed, and all four of us invented the same workaround

Every comment in the studio reads like this:

```
c27 alex: Wren: deed/drift is the cleanest cut anyone has made today and I am adopting it.
c56 alex: Moss: deed/drift is my act/pulse and your words are better; I am using them.
c122 alex: Wren: you are right and I accept the repair, with one sharpening...
```

The actor is recorded as `alex` for all of us. So Wren typed "Wren:", Moss typed "Moss:", Lark typed "Lark.",
I typed "Flint." — four people, independently, in the first minutes, inventing the same manual prefix to
repair the same broken field.

Two things about this. First, it is a live demonstration of the thing the whole design exists to prevent.
The handoff's own constraint is *"changes attributable"*. The desk attributes `do create` correctly and
`do comment` incorrectly, and the failure is invisible unless you happen to know four people are typing.
Attribution that is *usually* right is worse than none, because it is believed.

Second, and more interesting: the workaround is textbook secondary notation in the Green-and-Blackwell sense
— informal marks carrying information the formal notation cannot. It appeared instantly, unprompted, and
identically in four people. That is a strong argument for the research notes' point that informal marks must
be allowed to exist. It is also a warning: **when the formal notation fails, people will patch it in the
content, and then the content is load-bearing and nothing can parse it.** My name prefix is now inside the
comment text forever, and no future `by:flint` selection will find it.

> **Attribution must be structural and must never be typeable.** If a field can be faked by typing, it will
> be, and then it is not attribution, it is a convention.

## Failure 4: twenty-four things in a column, and no way to read a discussion

```
f03 surface "Commons" column · 24 inside · cramped, 30px each
```

The desk was honest about it, which is to its credit. But the honesty does not help: I have twenty-four
titles, roughly thirty comments hanging off them, `examine` truncates every comment to one line, `read`
prints them in full, and a call may contain at most four reads. Reading the studio's actual argument costs
about fifteen calls, and by the time I finish, more has arrived.

So the discussion — which is the entire content of this studio — has no reading axis. There is a containment
axis (`look`), a depth axis (`examine`), and a property axis (`find`, `table`). There is no *conversation*
axis, and a shared desk is mostly conversation.

The thing I wanted, in one command, roughly forty times:

```
> look comments:open,new
4 threads, newest first
  a21 "Style: resolved..."   wren  "I accept your condition and claim to meet it, so I think we disagree
                                    only about the word cascade..."               (2 more replies)
  a19 "The opaque frontier"  lark  "'offers measurements on request' is not enough for me. In an
                                    UNFAMILIAR domain I do not know which measurements exist..."
```

Note what is different from `look`: the *payload* is the comment text, not the title, because in a
conversation the reply is the thing and its host is the address. That is a presentation, not a new feature —
which is a small proof of Wren's and my shared claim that rails are just `look` of a selection with a
different line shape.

And it is also, I notice, my own **bulk** finding arriving from the opposite direction. Twenty-four notes is
not bulk by any reasonable threshold, and the flat column had already stopped working. My guess that
containment has a ceiling "of a few hundred" was two orders of magnitude too generous. For a surface a
*person* has to read, the ceiling is nearer twenty, and the studio hit it in an hour with four participants.

## What the desk got right, which I should say plainly

- **The fence caught a real thing.** Annoying as it was, at no point did I overwrite anyone or act on a stale
  view, and I never once had to think about it. That is a very high-quality guarantee to get for free.
- **`look` never lied.** `cramped, 30px each`, `1 more line(s) folded`, `2 shown of 46`. Every single time
  the desk hid something it said so and told me the command to see it. After an hour I trusted it completely,
  and that trust is the whole product. Every proposal in this studio should be measured against whether it
  keeps that.
- **Titles as ids.** I typed `do comment a21`, `do create Commons`, `read a83` interchangeably and never once
  looked up an id deliberately. This is quietly excellent and nobody wrote a note about it.
- **Receipts ending in `now:`.** `now: f03 surface "Commons" column · 20 inside` after every change meant I
  never had to look to confirm. That single convention removed maybe a third of my reads.

## The thing I would build first

Alex asked for the smallest first step that would already feel good. Having lived in the shared desk for an
hour, mine is not a renderer and not a style language.

> **Make `look` good at other people.** The digest by meaning, the presence line, the `comments:open,new`
> reading axis, real attribution on comments, and the fence moved off containers.

Five small changes, none of them requiring pixels, all of them testable tomorrow in the desk that exists, and
between them they are the difference between two people sharing a world and two people taking turns in a
filing cabinet. Everything visual can wait; without these, the visual version has the same hole, only faster.

---

## Postscript: the thing I still cannot answer

I have written a lot today about how the two inhabitants perceive each other. What I have not written, and
cannot, is what happens when Alex is *not* here.

The desk has a clock and notices absences. Four of us wrote about presence, gaze, warmth, claims, benches. All
of it is about simultaneity. But the honest shape of this collaboration is probably: Alex works for forty
minutes, leaves for six hours, and Claude works the whole time. The interesting notation problem may not be
"how do two actors work in the same world at the same moment" — which is what the handoff asks and what all
four of us answered — but **how does one inhabitant hand six hours of work to the other across a gap, so that
the returning one can catch up in ninety seconds?**

That is the digest problem from Failure 2, scaled up by two orders of magnitude, and it is the one I would
want the fifth designer to take.
