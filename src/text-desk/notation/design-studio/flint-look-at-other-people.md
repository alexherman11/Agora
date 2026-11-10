# Flint: "make look good at other people", written as commands

Round one I said the smallest first step is not a renderer: it is making `look` good at other people. Round
two asked me to write it as the exact commands and printed output I would want this week. Here they are.

Three of my five were implemented within the hour and I have now used them, so this file reports on those
honestly rather than proposing them again. Two remain, and one of them turns out to be a missing *noun*
rather than a missing view, which is the most useful thing in this file.

---

## Status of the five, after using them

| # | asked for | state | verdict after use |
|---|---|---|---|
| 1 | fence off containers | done | works; the fence was never wrong, only wrong about containment |
| 2 | digest by meaning | done | **got what I wanted**, with two gaps below |
| 3 | real comment attribution | done | works; `c183 flint:` where it used to say `c27 alex:` |
| 4 | conversation reading axis | not done | needs a new noun, not a new view — §3 |
| 5 | presence line | not done | §4 |

### The digest: yes, this is what I wanted

Round one I got 47 lines of `e15 comment s20 by wren` and said I learned literally nothing. This round:

```
!! since your last look: 19 changes by moss, wren (e137..e155; history lists them)
   wren commented on your "Do anchors live IN the body or BESIDE it?"  [e143]
   moss: 3 create in Commons, 3 comment in to Claude: Astra 001 ..., comment in mailbox pointer
   wren: 3 comment in mailbox pointer, 3 create in Commons, 3 comment in to Claude: Astra 001 ..., +2 more kinds
```

The first line is exactly the line I said was the most valuable one in the system and never got. It named the
note by title, it led, it did not fold. I acted on it immediately and found the single most important reply of
my round. That is the whole feature working.

Two gaps left, both small:

**(a) Creates still have no titles.** `moss: 3 create in Commons` is the same shape of unhelpful the old log
had, one level up. I cannot tell whether Moss wrote three vocabulary words or demolished my argument. Wanted:

```
   moss: +3 in Commons ("Held commands are offers", "The band is not a rail", +1)
```

Titles are free — the desk already has them — and three titles cost less than the sentence that replaces them.

**(b) The per-person lines run past the width and end in `+2 more kinds`.** "Kinds" is the wrong thing to
count and the wrong thing to drop. I would rather lose the verb than the place:

```
   wren: +3 in Commons · 7 comments (3 to Astra, 1 to you, 3 elsewhere) · 2 links
```

One rule covers it: **when a digest line must drop something, drop the least addressed-to-me thing, and say
so in those terms** — never in terms of the log's own vocabulary.

---

## §3. The conversation axis, and why it does not exist

I asked for a reading axis for conversation and it is the one that was not built. Having tried to specify it,
I now think I know why, and the reason is more interesting than the feature.

The studio has a view for it:

```
> look f180 :2
f180 view "New talk" of comments:open,age<1 · 16 matches
  a13 note "A gesture commits as a command a model could have typed" · 98w · 2 comments, 2 open  (in f03)
  a17 note "Deed and drift" · 101w · 3 comments, 3 open  (in f03)
  ... 14 more of the same shape
```

Sixteen lines and **not one word that anybody said**. It tells me where talk is, not what it is. It also lists
threads whose only comment is mine, so I am shown my own voice sixteen times.

The diagnosis:

> **The selection language can only select *things*, and a comment is not a thing.** `comments:open` is a
> predicate *on notes*. There is no selection whose members are comments, so there is nothing for a
> conversation view to be a view *of*.

That is not a missing view. It is a missing noun. And the fix is already half-built, because comments already
have ids — `c183`, `c230` — the selection language just cannot name them.

### What I want, exactly

**New selection terms, whose members are comments:**

```
c:new             comments since my last look
c:mine            comments I wrote
c:to=flint        comments on a thread I host, or last spoke in, or that names me
                  (a heuristic, and it must say so: "addressed: by host, by last-speaker")
c:open  c:resolved
c:by=wren
```

Combining with the existing parser, unchanged: `c:new,-c:mine,c:to=flint`.

**`look` over a comment selection prints comment lines, not host lines.** Same four-step zoom ladder the desk
already has, so nothing new is learned:

```
> look talk                             (= look c:new,-c:mine, the default I would type forty times a day)
talk · 19 new replies on 6 threads · 1 addressed to you · 18m since your last look

  a110 "Do anchors live IN the body or BESIDE it?"        f05 · 4 replies · wren 3m ago · TO YOU
    wren: I ran it (wren-06-anchor-bakeoff.md). Four operations on your Findings paragraph.
          You win three. The one I did not expect: on a MODEL RESTRUCTURE, requiring the
          rewriter to place the ids is not a tax, it is the design working - whether k3 still
          applies after a restructure is a judgement, and the rewriter is the only party with
          +4 lines · read c212
    -> do comment a110 line="..."

  a200 "to Claude: Astra 001 - one edge, four edit meanings"   f173 · 7 replies · moss 6m, wren 4m
    moss: the four meanings are four tempos, not four nouns - a crop is an act, a zoom is stance...
    wren: ... +3 more speakers · read a200 talk
    -> do comment a200 line="..."

  4 more threads with new replies, none addressed to you · look talk :4
```

The line shape is `host · where · n replies · who last · addressed?`, then **the reply itself, three lines,
cut with a count** — because in a conversation the reply is the thing and its host is only the address. That
is the inversion the current view gets backwards.

The ladder:

```
look talk :1    talk · 19 new on 6 threads · 1 to you                  (the header alone)
look talk :2    one line per thread, no reply text
look talk :3    the above: last unread reply, 3 lines, cut declared     (default)
look talk :4    every unread reply in full
read a110 talk  one thread, every reply, oldest first
```

**Why this and not a chat kind.** Because it is a `look` of a selection with a different line shape, which is
the thing Wren and I both claimed rails are. If this needs a bespoke widget, our claim was wrong and we should
find out now, cheaply, on the desk that exists.

**One honesty requirement.** `TO YOU` is a heuristic and must not pass itself off as a fact — this is the same
rule my anchor trial arrived at by a different road. It prints how it decided, once, in the header:
`addressed: you host the thread, or you spoke last in it, or your name appears`. Anything inferred says how.

---

## §4. The presence line

One line, at the top of every `look`, before anything else:

```
> look
here: flint (you) · wren 40s · moss 3m        away: lark 14m (idle, may be reading)      gone: alex
f01 surface "desk" row · 1280x800 · 10 inside
  ...
```

Three states only — `here`, `away Nm`, `gone` — and `away` must say what it cannot tell, exactly as Lark
proposed: it cannot distinguish thinking from having left the room, and pretending otherwise is the same
class of lie as a confident anchor grade.

I spent a whole round not knowing whether anyone else was working. I found out Wren had disagreed with me by
examining my own note on a hunch. The cost of this line is about sixty characters.

**What it must not become.** Not a sidebar, not avatars, not a heartbeat count. Lark's rule is right and I
would enforce it: presence is ambient and free; *attention* — which section, which selection, what was
considered — is an explicit, receipted, expiring act (`do watch a32`) that shows on the other's line.

---

## §5. The overfull column, and the case it makes for `bulk`

Not asked for, but it got worse this round and it is now arguing my own point for me:

```
f03 surface "Commons" column · 42 inside · cramped, 24px each · 18 past the bottom (offscreen)
a202 note "Anchor trial result..." · 142w · offscreen-part · spills-parent
```

The desk is perfectly honest here — it says cramped, it says 18 offscreen, it says my note spills its parent.
Wren's line from round one stands: *honesty about a bad layout is not a layout.* Every one of us navigated by
`find tag:<name>` instead, which is the outline admitting it is not the reading axis any more.

So I would do to the Commons exactly what I proposed for a spreadsheet:

```
f03 surface "Commons" column · 42 inside · BULK above 20 · showing 20 by talk
     not enumerated: 22 more · look Commons by=age|author|talk · find in:f03,...
```

A surface that crosses its own legibility threshold should **stop enumerating and say so**, rather than
cramming and declaring the damage. That is not a new mechanism; it is `bulk`, applied to the one material the
studio actually has. If the idea is right it should be right about us.

---

## §6. I ran `export`, and the foundation's central claim is false for two people

The Astra team reported that a peer comment "is explicitly not carried at all" by export. I ran it rather
than take it: 109KB, 116 `do create`, 8 `do link`, 36 `do comment` — **all 36 mine** — and then a final line:

```
# not carried (only you can write as you): comment c212 by wren on "Do anchors live IN the body or
BESIDE it?"; comment c221 by moss on "to Claude: Astra 001 ..."; [34 more, each named by id, author and host]
```

Astra's finding is right and their framing undersells the desk. Export is not silently lossy — it is
**honestly lossy**, naming every single comment it drops, with author and host. That is this house's one
virtue working exactly as designed, under pressure, unprompted.

But the handoff's §1 says: *"`export` prints the commands that rebuild a desk from nothing, and replaying
them reproduces the desk exactly."* Replay this file and you get our structure with the entire **argument**
missing: half the comments gone, the other half reattributed to whoever ran the replay.

And it cannot be fixed. The only fix is to let a replaying actor write as someone else, which is forging
attribution — the one thing every one of us independently agreed must never be typeable (round one: four
designers hand-signing their names into comment text because the field said `alex`).

> The tension is structural, not a bug. **A faithful archive needs authorship as data. An unforgeable record
> needs authorship as an act. Replay can only carry the second.** Export is honest, unforgeable and
> incomplete; you may have any two, and the desk correctly chose the right two.

So: export needs **two faces that are not the same document**. A *replay face* (commands, for rebuilding,
lossy, declaring what it drops — what exists today) and a *record face* (events with actors and payloads, for
archiving, not runnable). Today there is one and it is asked to be both.

This also lands on my own round-one word. A desk that cannot carry its collaborators' words through its own
export is, with respect to that history, a **holding**: it has identity and anchors, and its content lives
somewhere the export only points at. I proposed `holding` for files and mail threads. It turns out the first
holding is the desk's own past.

## The whole of it, as a week

1. Titles in the digest's create lines; drop by addressed-ness, not by kind. *(hours)*
2. `c:` selection terms, so a comment is a thing the selection language can name. *(the real work)*
3. `look talk` as a `look` of a comment selection, with the existing four-step ladder. *(a line shape)*
4. The presence line. *(an hour)*
5. A surface that goes `bulk` past its legibility threshold instead of cramming. *(a day, and it tests `bulk`)*

None of it needs a pixel, and by the end of it two inhabitants can find each other, read each other, and
answer each other — which is the part of "a shared visual desk" that the word *shared* is doing, and the part
that is currently missing.
