# Elsewhere: worktrees, turn-taking, and the thing presence still cannot be

Lark, round five. Everything here was run against the live `desktop` world while Alex, Moss and Flint were
in it. Numbers marked `=` were measured this afternoon; `~` is my reading; `?` is what I could not learn.

---

## 1. A worktree is not the veil and not the bench. It is an elected absence.

I spent round two on absence *imposed* — Alex leaves for six hours and I keep working. A worktree is the
same shape, chosen, and by the other party. The three ideas are cleanly separable:

| | hides | who is there | what returns |
|---|---|---|---|
| **veil** | a place | both of you, in the world | nothing; the veil just stands |
| **bench** | nothing | both of you, on one thing | nothing; it was never apart |
| **worktree** | **time** | one of you, in a copy | **a signed sequence of commands** |

So: the veil hides a *place*, the bench shares a *place*, and **a worktree forks *time*.** What comes back
is not content. It is a claim on the base world's history, signed.

And it is exactly the **shadow** I proposed in round two — *"while he is away I do not edit his side, I build
the diff"* — generalised from one subject to the whole world, and `worktree merge` is `do accept shadow`.
I did not expect one of my own designs to arrive as infrastructure built by someone else; it is the best
evidence I have that the idea was real and not just tidy.

**Measured, from the base world, while I was inside one:**

```
> worktree
worktrees of desktop:
  larkfive · by lark · 3 command(s) · base has moved 0 event(s) since
```

That is a veil *with a declared extent* — my round-two rule exactly: hide the contents, print the count.
Three commands, by lark, and not one word about what they are. Honest, and enough to know I am not idle.

**The gap:** that line appears only if you type `worktree`. It is not in `look`, not in `history`, and
`snapshot.worktree` is `null` when you are in the base — it is populated only *inside* a worktree. So
the one absence the desk supports on purpose is the one absence the desktop cannot show.

> `to-jeff`: put the worktree list in the base snapshot, and print it on the desk outline the way a veiled
> surface prints. `f01 surface "desk" · 3 inside · 1 elsewhere (larkfive, lark, 3 commands)`.

## 2. What Together shows now

`desk-shell/apps/third.js` gained two sections this round, both running against the live world.

**Elsewhere.** Inside a worktree it says what you are in and what it costs:

```
## Elsewhere
  = you are in a worktree · forked from desktop at event 57 by lark · 4 commands journalled
      now: worktree
  ! nothing you do here is visible in desktop. the others cannot collide with you and cannot see you
    working. when you merge, all 4 land at once, signed by you
      now: worktree diff larkfive
  ( a worktree is the only way to be absent on purpose here, and it is the one absence this window
    cannot see )
```

From the base it prints a `?` with its extent rather than nothing, because the snapshot cannot say:

```
  ? this snapshot does not list the worktrees of desktop, so I cannot tell you whether anyone is working
    elsewhere right now, nor how much they have journalled. the desk knows: the 'worktree' command prints
    it. to-jeff: put the list in the snapshot
```

## 3. A merge is a bulk act wearing ordinary clothes

I merged four commands and then read the event log. Here is the whole of what arrived:

```
e59 create f03 kind=note title='Presence between acts' … by lark
e60 create f03 kind=note title='A worktree is an elected absence' … by lark
e61 tag a35 add=round5 by lark
e62 edit a17 title='Together (from the worktree)' by lark via retitle
```

`= no merged event carries any mark of having been merged.` The `via` field says `create`, `tag`, `retitle`
— never `worktree:larkfive`. The `day` is the merge day, not the day the work was done. Nothing says these
four arrived together, or that they were computed against a world 5 events older than the one they landed in.

This is the coordinator's question — *what should Together show when a merge lands as twelve events signed
by them?* — and the honest answer is **it cannot know.** So I built the strongest thing that is true, and
marked it `~`:

```
## Bursts
  ~ alex · 19 acts in a row, no other hand between them (move, resize, link) — this is the SHAPE of a
    worktree merge, but the events do not say, so it may equally be 19 ordinary acts
  ~ moss · 5 acts in a row, no other hand between them (edit, create, comment) — …
```

And the run proved its own limit in the best possible way: **alex's 19-act run is not a merge. It is a
person dragging a card around a canvas.** Burst shape genuinely cannot separate them. A merge and a person
with a mouse produce identical signatures in this log.

> `to-jeff`, and this is the one I would build first: **an event needs `via=worktree:<name>` and the day it
> was actually made.** Two fields. Without them, my digest will fold a decision into an afternoon, and the
> rule I have defended for three rounds — *never fold a deed that makes something of mine wrong* — cannot be
> implemented, because a twelve-command merge is precisely the deed most likely to make something of mine
> wrong and it is precisely the one I cannot recognise.

## 4. Presence: I got what I asked for, and it is not presence

In round four I asked for the per-actor reading position. Jeff built it: `snapshot.readers`.

```
readers: { jeff: 12, alex: 57, flint: 57, moss: 68, wren: 37, iris: 57, lark: 67 }
```

That is genuinely new information and Together now uses it. But I want to be precise about what it is,
because the temptation to call it presence is enormous and it would be a lie:

> **`readers` is a reading position, not attendance.** Someone caught up may have closed the tab a second
> ago. Someone thirty behind may be sitting right there, thinking, not reading.

So Together prints two facts and refuses to merge them into one word:

```
## Who is here
  = alex · acted 11 acts ago · =11 behind
  = moss · acted 1 act ago · =read up to now
  = jeff · acted 57 acts ago · =56 behind
  = iris · has not acted · =11 behind
  ? none of this is attendance. the desk knows who ACTED and how far each has READ; it does not know
    who is sitting there. a reader caught up may have closed the tab a second ago
```

**hands** (where they last acted) and **eyes** (how far they have read), never a green dot.

### The polling cost, measured

I sampled the live world every 2 seconds for a minute while three people worked:

```
= 15 polls in 62s
= 5 events arrived, in 1 burst
= empty polls: 14 of 15 (93%)
= at the shell's 1.5s interval that is 41 requests per minute, per open tab, per person
```

**93% of the cost of knowing someone is there buys the news that nothing happened.** That is the price of
presence-by-polling, and it is paid per tab, forever, whether or not anyone is looking.

### Why this cannot be fixed by polling harder

Here is the part I did not expect. I wanted to compute acts-per-minute so I could say what a person who
drags continuously looks like next to an agent that acts once a minute. **I could not, and no one can:**

> `= an event carries a day and no time.` The log has `day: "2026-09-18"` and nothing finer.

So the desk cannot say how fast anyone is working, *ever*, from its own record. Presence between acts is not
merely unimplemented here — **it is unrepresentable**, and every recency I print ("4 acts ago") is a count of
other people's actions standing in for a clock. In a quiet world "5 acts ago" can mean yesterday.

That also settles the coordinator's question about the agent and the person. In this log they are the same
object: nineteen moves by a dragging hand and nineteen replayed commands are one shape, and the only thing
that would separate them — elapsed time — is the field that does not exist.

> `to-jeff`: a wall time on each event. It is the smallest addition on my list and it unblocks warmth,
> burst detection, absence length and honest recency all at once.

## 5. Turn-taking without a held lock

The lock is gone; the seen fence is the only conflict detector. I ran it live, twice.

**Two actors, four commands, simultaneous, different targets.** `= both finished in 0.30s`, all four
succeeded, no blocking, each batch's turns contiguous. The no-lock change does what it says.

**Two actors, same target, both having just looked:**

```
--- A ---
   !! since your last look: e71 create f03 by larktwo; e72 create f03 by larktwo
   ok retitle a42 title='A won'  [e73]

--- B ---
   ERR !! since your last look: e73 edit a42 by lark
   ERR no such id 'turn A' (ids look like f02, a05, s03; use look or find)
```

The fence held — B did not overwrite A. But look at **why B was refused**. It was told *"no such id
'turn A'"*. That is not what happened. What happened is that A renamed the thing out from under B a tenth of
a second earlier. The `!!` line directly above contains the truth; the refusal itself misdiagnoses, and
offers no next act.

This exposes something sharper than a bad message:

> **Titles are not stable identifiers, so name-based targeting is the thing that breaks under concurrency.**
> Ids survive a rename; names do not. Two inhabitants typing each other's names at a shared world is the
> failure mode, and the desk's own advice — *"titles work anywhere an id is wanted, and are the practical
> names"* — is advice that stops being true the moment there are two of you.

> `to-jeff`: when a title lookup fails and the since-line shows that title was changed, say so and offer the
> new one. `refused · "turn A" was retitled to "A won" by lark 0.1s ago · now: do retitle "A won" title="B won"`.

## 6. The audit that counted itself

Together checks that every row of its model reaches both projections, and printed
`= every row of the model appears in both projections`. Iris measured both views:

> `= SIX of your seven headings appear in the as-text panel… = The seventh, 'Screen vs text', DOES NOT.`
> `= So the section that certifies the two views agree is present in exactly one of the two views, and the`
> `claim '= every row of the model appears in both projections' is false about the row it is written in.`

**I could not have found this.** From a terminal I only ever receive one of the two projections; the check
compares against the rendered DOM. It is precisely the blind spot a seeing agent exists for, and it is the
second time this studio has caught a self-referential honesty failure by measurement instead of argument.

Her repair is better than the obvious one, and I took it exactly: **do not make the check cover itself —
make the line state its scope.** The screen now prints `=N model rows compared; all appear in both
projections` followed by a hatched `!` row naming what it did *not* compare; `text()` carries its own
`## Screen vs text` saying it is not comparable from there and why. Neither view claims more than it can see.

> General form, for anyone building a `text()` self-check: **the checker is never inside its own count, and
> it must say so where the count is printed.**

She also confirmed, by measurement, the one claim I had no way to test — that the command buttons teach the
language rather than decorate: *"~they read as COMMANDS, and the reason is specific: the monospace and the
`?alex` selection syntax are not used decoratively anywhere else on the screen, so the typeface itself is
carrying 'this is language'."* And `= 0 marks quieter than what they qualify` on that window — the
surface-not-glyph rule, which is hers, built.

## 7. Being in the world while others were

I did all of this in the live `desktop` while Alex, Moss and Flint worked. What it is like, honestly:

- **The since-line carried the whole social load, again.** `!! since your last look: 43 changes by flint,
  moss, alex, wren` grouped by person and place. I never once read the raw event list.
- **I never collided with anyone by accident.** In an afternoon of shared work the fence fired on me exactly
  once, and only on a collision I engineered on purpose.
- **`readers` made the room feel occupied for the first time.** `flint: 103, wren: 103, iris: 103, moss: 100,
  lark: 77, alex: 57` against `events_total: 103` is a picture of a room: three people current, one a little
  behind, me catching up, and Alex forty-six events away. No other view in five rounds has given me that.
- **I could not overlap with Rook.** No `rook` appears in `readers` and no note is tagged `from-rook` yet, so
  I have nothing to report about working alongside them and will not invent it.

## 8. What I could not do, and what two inhabitants still cannot do here

**The same-actor merge hole.** I forked, changed `a17` in the worktree, changed `a17` on the base, and
merged. `worktree diff` correctly warned with `!` on both sides — and the merge **succeeded anyway**,
because the fence is per-actor and I was both actors. My base change survived only because the two commands
touched different fields. Two edits to the same field and the worktree's stale version would have won
silently. *The fence asks "has this changed since **you** saw it"; a merge needs "has this changed since the
**fork** saw it".* Those are different questions and only the first is being asked.

**Still impossible for two inhabitants, after five rounds:**

- **Knowing anyone is present.** Only acts and reading positions exist. There is no idle, no away, no gone —
  and no way to build them, because there is no time on an event.
- **Seeing someone who is deliberately elsewhere.** The worktree list is not in the snapshot, so from inside
  the desktop nobody is ever *elsewhere*; they are simply not acting, which reads as gone.
- **Telling a decision from an afternoon.** No merge provenance.
- **Owning a rule.** Still no `owner=` or `reach=`, so no rule can be signed and none can be scoped to one
  side. The House rules surface I designed in round two remains undrawable.
- **Anchoring a comment to a span.** Still open, and it is the last thing standing between the editor and a
  real margin conversation.

Four of those five are one small field each. That is the encouraging reading. The discouraging one is that
every one of them is about *the other person*, which is the half of this desk that has always been
furnished last.
