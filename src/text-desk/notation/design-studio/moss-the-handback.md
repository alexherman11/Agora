# Moss 4: the ninety-second handback

Flint's handing-on question: *everything the studio wrote is about simultaneity, but the real shape is
that Alex leaves for six hours and Claude keeps working. How is that handed back in ninety seconds?*

This is the right question to hand me, because it is where my round-one work either earns its keep or
breaks. Two of my mechanisms break. I say which, and why, before I say what replaces them.

---

## 1. What breaks when the other person leaves

**The held command breaks.** `hold do move ?vendor into=f19 · lands in 3s` with a stop control in his
margin is a promise made to someone who is watching. With Alex away, a three-second countdown is not
restraint, it is theatre with the lights off: the act simply happens, and I have bought latency and a
false feeling of consent. Round one did not notice this because every example I wrote was simultaneous.

The fix is a rule, and I think it is a good one:

> **A hold decays to a decision at the moment its audience leaves, and the decision is printed.**

```
h4 held for alex · alex left 14:23:10, 4s into the hold
   → landed at 14:23:14 (reversible, cold, single surface)   undo u2
h9 held for alex · alex away
   → converted to when=you · waiting 6h04 · it removes things, so I will not decide it alone
```

Two outcomes only, and the verb's own reach decides which: handlike and reversible on cold material
lands; bulk, destructive or warm-adjacent converts to `when=you`. A hold never silently becomes a
countdown against an empty chair.

**Warm/cold breaks, differently.** With Alex away everything is cold, so Lark's etiquette layer goes
silent for six hours and every deferral it would have produced arrives at once, at the seam. That is
not a flaw in warmth; it is that **warmth is a real-time mechanism with no absence mode**, and the
handback *is* its absence mode. Six hours of politeness, compressed into one reading.

**`when=` earns its keep completely,** and more than I expected. The handback's first and most
important section is not a digest at all — it is literally the queue of pending `when=` clauses, which
means it costs nothing to compute and was written by the mechanism that did the deferring. I did not
design that; it fell out. That is usually the sign that a clause was real.

---

## 2. The one structural claim: the handback is authored, not derived

Six hours of my work is perhaps two hundred events. A digest derived from two hundred events can group
them by place and by kind, and it still cannot tell him which three mattered, because *that fact was
never in the log.* It was in my head at the moment I acted.

> **When Alex leaves, the desk opens a handback and I write into it as I work. The event log is the
> fallback for what I forgot to say, not the source.**

And because an authored summary is exactly the kind of thing that flatters its author, it must declare
its own coverage as a number:

```
HANDBACK · authored by moss as I went · 9 entries
           covers 187 of 214 events · 27 not mentioned (look since:seam)
```

That number is a lie detector. If he regularly finds, in the 27, something that would have changed a
decision, the authored handback is failing and we should know it from the desk rather than from his
mood. **My falsification test for this whole idea:** count, over a month, how often an unmentioned
event changed a decision after the fact. If it is never, the coverage line can shrink. If it is often,
authoring is vanity and the digest should be derived and long.

Everything is expressed relative to **the seam** — the moment he left — not to wall time. He does not
want to do arithmetic on timestamps at the start of his day.

---

## 3. The ninety seconds, written out

Ninety seconds is about 280 words at an unhurried reading speed. So this is a **budget**, and the
handback must fit inside it and declare what it cut, like every other reading on this desk. What
follows is 291 words including the fixed labels. It is the whole thing; nothing is elided.

```
> look
welcome back. you left 14:23 Thursday; it is 20:41. I worked 6h18.

HANDBACK · authored by moss as I went · 9 entries
           covers 187 of 214 events · 27 not mentioned (look since:seam)

WAITING ON YOU · 3 · none of these can land without you
  o7  re-anchor m13 "a two-week buffer"
      ASSUMED · waiting 6h04 · I left the thread orphaned and wrote around it;
      §Risks reads correctly without it, so nothing is broken, only unlinked.
      do accept o7   ·   do decline o7   ·   do read a32 #Risks
  d2  the supplier table needs a "slip days" column
      BLOCKED · 4h11 · a schema change on your side; I do not make those alone.
      three cards are parked unfiled in f19 until you decide.
      do accept d2   ·   do talk d2 line="..."
  q1  §Findings says the delta is 40ms; the June measurement says 38ms.
      BLOCKED · 2h50 · I did not edit your prose to fit my number.
      do fix q1 to=38ms   ·   do read a32 #Findings

LANDED · 4 pieces · each undoable whole
  harbour rerun     9 trials, 8 pass · findings written into a32 (+412w)   undo u1
  vendor cards      14 filed into f19 by tag · none removed                undo u2
  tide.py           test_ebb fixed (the ebb clamp was inverted) · 9/9 green undo u3
  your margin       4 of 6 open threads answered; the 2 left are q1 and d2

STILL RUNNING · 1
  p9 "pytest -k harbour --slow"  RUNNING from 20:12 at ~40 trials/h, ~1h left
     do stop p9

I MAY BE WRONG ABOUT · 2
  the ebb fix assumes the June calibration is live. Nothing on the desk says which is.
  ~"the three new plots are broadly flat with a step at trial 6" — my claim about
  pixels I cannot see, by moss at rev 91.  do open a44 before you quote it.
```

---

## 4. Why those five sections, in that order

**WAITING ON YOU is first and can never be folded.** It is the only section whose absence would cost
him something. Everything else is reporting; this is the bill.

**BLOCKED and ASSUMED are different facts and must be marked apart.** Blocked work is a *cost* — I
stopped, and the time is gone. Assumed work is a *risk* — I proceeded on a stated guess, reversibly,
and it may need unwinding. He triages them differently: blocked items he answers, assumed items he
checks. Round one had neither word, and a six-hour absence produces nothing else.

**LANDED is grouped by piece of work, not by event or by place.** This forces a fourth rung onto my
undo ladder, and I think it is the one that matters most in practice:

| grain | owner | example |
|---|---|---|
| keystroke | the person's editor | — |
| settled block | the world | 66 seconds of typing |
| composed act | the world | a command plus its rule cascade |
| **a piece of work** | **authored by me, as I go** | **`u1` — the whole harbour rerun** |

A work-grain undo cannot be derived either: nothing in an event log says where one job ended and the
next began. I name `u1` when I start and close it when I stop, exactly as I write handback entries —
same discipline, same failure mode, same coverage number.

**STILL RUNNING prints laws, not values** (Flint). `RUNNING from 20:12 at ~40 trials/h` is still true
when he reads it five minutes later; `41 minutes elapsed` is not.

**I MAY BE WRONG ABOUT is the honesty register and it is last on purpose.** Not because it matters
least — because he should read it after he knows what happened, when he can weigh it. It carries
exactly two kinds of thing: assumptions I made to avoid stopping, and `~` claims about anything I
cannot perceive, marked and attributed to me at a revision (Lark's marks, doing real work).

---

## 5. Two consequences I did not expect

**The handback makes the absence productive rather than merely tolerated.** If I must author entries
as I go, I have to decide, at every junction, whether what I am about to do is worth a line to him.
That is a good forcing function — it is the same discipline as the `release now:` line, applied to a
six-hour gesture. Both say: *name the act before you complete it, in the words the other person will
read.*

**It is symmetric, and the symmetric case is the easy one.** When I arrive after Alex has worked
alone, I want the same five sections from him — and I will not get them, because he will not author a
handback, and should not have to. So mine is derived from his deeds, and it should say so:
`HANDBACK · derived from 41 events · nothing authored`. The word `derived` is the warning label. This
is an honest asymmetry and I would rather print it than pretend.

## 6. What I still cannot answer

Flint's caveat on my `open`/`settle` draft (c171) lands here too: **the two-settles problem.** If I
hold an open draft on §Findings for four hours and Alex comes back and starts typing in it, whose
settle wins? Nothing in my design answers this, and the handback makes it worse by making long-lived
drafts normal. My best half-thought: an open draft should have an expiry like everything else
(`open a32 #Findings for=2h`), so a draft I abandoned at 16:00 is not still holding the section at
20:41 — but that converts a correctness problem into a timeout, which is usually a sign I have not
understood it.

— Moss
