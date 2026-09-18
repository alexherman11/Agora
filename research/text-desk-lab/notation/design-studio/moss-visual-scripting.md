# Moss 6: visual scripting — what I built, what broke, what is missing

Round three. Alex: *"how can our agents work on software inside the desk? Or build more complex code
through rules? What is needed to unlock visual scripting from within the desk?"*

I did two things. I pushed the existing rule language in a scratch session (`proto-moss`) until it
broke, writing down the exact refusals; and I built a page that draws a real session's rules as a
graph, at `design-studio/prototypes/moss-rulegraph/` (live at `http://localhost:8770/moss-rulegraph/`).
Everything below is measured on the running lab, not imagined. Where I propose notation I say so.

---

## 1. The design question: what is a rule, visually?

My answer is not a node canvas, and I want to argue against one before I show mine.

A node-and-wire canvas (Max, Blueprint, Node-RED) puts the program in the *positions*. Positions are
not text. You can serialise them, but then the picture is the truth and the text is a dump of it,
which inverts this desk's whole premise. And a text-only reader gains nothing: reading a node canvas
as text is famously worse than reading code.

> **A rule is not a node. A rule is already a line. What is missing is not a picture of the line —
> it is the wires between lines, and those are exactly what the text cannot print.**

So the picture I built *is* the `rules` listing — same rows, same order, same words — with one thing
added: a wire drawn from rule A to rule B when A's action makes (or unmakes) something B waits for.
The rows are the text. The wires are the analysis. Nothing is stored in a position, so there is
nothing to keep in sync, and the export is unchanged.

```
r1  when kind:task,tag:urgent   do tag add=triaged      fired 1×
 ╭─────────────────────────────────────────────────────────╮
r2  when tag:triaged            do move into=Today      fired 1×
...
r4  when tag:ping               do tag add=pong         fired 1×   one-shot
 ╭╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╮
r5  when tag:pong               do tag remove=ping      fired 1×
```

Click a row and you get the command that made it (`rule when tag:ping do tag add=pong`), the command
that removes it (`rule drop r4`), the body of any script it runs, the sentence for each wire
(*"r1 makes tag:triaged, which r2 waits for"*), and its faults. **The picture and the text are the
same object because the picture is the text plus derived wires, and the derivation is printed as
prose next to every wire it drew.**

The page declares what it cannot see, in the studio's own marks: `?` it does not know what a person
will do, so *unreached* means "no rule feeds this", not "nothing feeds this"; `?` it understands six
verbs and is silent about the rest, so a missing wire is not proof of no wire; `!` it is a snapshot.

## 2. What the graph found in twelve real rules

These are not illustrations. The generator found them in `proto-moss`:

| grade | rule | what |
|---|---|---|
| `broken` | r6 | `do move into=Nowhere` — the surface does not exist. Accepted at definition, fails only when it fires, as a `~` line under someone else's command. |
| `frozen` | r8 | `when due<2026-09-18` — I wrote `due<$today`. |
| `unreached` | r6 r7 r11 r12 | never fired and no rule makes what they wait for. |
| `one-shot` | r5 | undoes what r4 waits for: looks like a cycle, is not one. |

The `frozen` one is the finding I would put in front of Alex first, because it is a **trap, not a
gap**:

```
> rule when due<$today do tag add=overdue
ok r8: when due<2026-09-18 do tag add=overdue      ← substituted at WRITING time, silently

> rule when due<today do tag add=overdue-live
ok r10: when due<today do tag add=overdue-live     ← stays live
```

Two spellings, one character apart, opposite behaviour, no warning. `$today` is substituted by the
command reader before `rule` ever sees it. Any scheduled program someone writes with `$today` is
frozen on the day it was written and will look correct in `rules` only if you know to notice the
literal date. **This should be a refusal**: `rule ... $today: did you mean today? $today freezes the
date now; today is evaluated when the rule fires.`

## 3. What broke, verb by verb (the probes)

**Rules cascade, and that is the good news.** One command produced two rule firings, in order, with a
readable causal trail:

```
> do create Inbox kind=task title="fix the ebb clamp" tags=urgent due=2026-09-19
~ r1 fired on a06: ok tag a06 add=triaged  [e5]
~ r2 fired on a06: ok move a06 into=f03    [e6]

> why "fix the ebb clamp"
  e4 create ... · moss via create
  e5 tag add=triaged · moss by rule r1 (because of e4)
  e6 move into=f03   · moss by rule r2 (because of e4)
```

`why` is already a real debugger: cause, actor, and the rule that did it. Chaining, sequencing
(`script outer = run inner $1; do tag $1 add=outer-was-here`, which prints numbered steps like a
stack trace), and even **metaprogramming** work today — a script can define a rule:

```
> script mkrule = rule when tag:$1 do tag add=seen
> run mkrule blue
run mkrule: rule when tag:blue do tag add=seen
ok r7: when tag:blue do tag add=seen
```

That is more than I expected. Rules can write rules; the language is extensible from inside it.

**Then it breaks, and it breaks in one place harder than all the others.**

### The central break: a `when` rule fires at most once per thing, ever

```
> do tag a06 remove=triaged      (a06 leaves r2's selection)
> do move a06 into=Inbox
> do tag a06 add=triaged         (a06 re-enters r2's selection)
> look Today :2
f03 surface "Today" column · empty      ← r2 did not fire again
```

Every rule keeps a `done` set of things it has acted on, forever. This is what makes the ping/pong
pair safe — r4 tags pong, r5 removes ping, and nothing spins — but it means **the loop guard and
recurrence are the same knob**. You cannot write "whenever this becomes overdue", "each time it comes
back to Inbox", "every time a trial fails". Those are most real programs. As it stands the rule layer
is a *filing system*, not a *program*: it can classify each thing once and cannot respond to anything
twice.

### No values, no arithmetic

```
> script bump = do prop $1 count=1
> rule on comment do run bump $item
> do comment a06 line="one"
~ r3 fired on a06: run bump a06 → ok prop a06 count=1  [e11]
> do comment a06 line="two"
~ r3 could not run a06: a06 already has count=1; nothing to change
```

A counter is impossible. There is no expression anywhere: no `count=$item.count+1`, no reading a
prop into an argument, no concatenation beyond `$item.title`. Props are the only state and they can
only be *set to literals*.

### No comparison on props

```
> find prop:count>3
ERR prop:k=v (prop:k alone selects things that have k)
```

`due<` and `age>` compare; `prop:` only tests equality. So even if a counter existed, no rule could
branch on it. Conditions today are exactly: kind, tag, containment, prop equality, due, age, and
negation (`-tag:urgent` is a usable `else`, which does work).

### No check at definition time

```
> rule when tag:ghost do move into=Nowhere
ok r6: when tag:ghost do move into=Nowhere        ← accepted
...
~ r6 could not move a12: no such id 'Nowhere'     ← discovered later, under someone else's command
```

Nothing validates the target, the verb's applicability, or the argument names when the rule is
written. The failure surfaces as a `~` line attached to an innocent command, possibly days later.

### No dry run

There is no way to ask what a rule *would* do. `find <selection>` tests the `when` half; the `do`
half has no preview at all. `now=1` is the opposite of a dry run: it applies to everything matching
immediately.

### The automation layer is invisible to any renderer

`python explore.py <session> --dump` returns `subjects`, `nodes`, `links` — and nothing else. **Rules
and scripts are not in the dump.** They live on the per-actor Desk, not in the World. So a visual
desk built from the dump would draw a world with no program in it, and the person could not see the
automation that is moving their things. My generator has to scrape the printed `rules` text instead.

---

## 4. Missing primitives, in priority order

Ordered by *how much program becomes possible per unit of new notation*, which is not the same as by
difficulty.

**1. Re-arming — a rule that can fire on the same thing again.** Everything else is decoration
without this. The `done` set should be per *entry*, not per thing: leaving the selection clears the
entry. Proposed, and the default should stay one-shot so nothing breaks:
`rule when tag:overdue do ... again=1`. The receipt must say which it is, because "fired 6×" on a
one-shot rule and on a re-arming rule mean different things. Loop safety then needs its own honest
guard rather than a side effect: a fire budget per command (`~ r4 stopped: 20 firings from one
command, budget spent; why a10 shows the chain`).

**2. Values: read a prop, compute, write it back.** The smallest useful form is not an expression
language — it is one substitution and one verb:
`$item.count` readable anywhere `$item.title` is, and `do prop $item count=+1`.
Counters, scores, retries and "third failure" all become expressible, and nothing else in the desk
changes.

**3. Comparison in selections.** `prop:count>3`, `prop:status!=done`. Selections already parse `<`
and `>` for due and age; extending them to props makes every accumulated value into a condition, and
rules-as-branches fall out for free. These first three together are the whole of "conditions and
state".

**4. Definition-time checking, with the refusal doing the teaching.** Validate the target exists, the
verb applies to the kind the selection can yield, and the argument names are real — at `rule` time,
in the house style: `refused: move into=Nowhere — no such surface. now: do create desk kind=surface
title=Nowhere · rule when tag:ghost do move into=Inbox`. Plus the `$today` refusal above. This is
cheap and it converts the worst failure mode (a silent `~` line under an unrelated command) into an
ordinary teachable refusal.

**5. Dry run.** `rule ... test=1` prints what it would do to what, now, and defines nothing:
`would fire on 3: a06 "fix the ebb clamp" → tag add=triaged; a18 ...`. Also `why a18 :next` for
"which rule acts on this next, and what will it do". A person watching an agent write automation on
their desk needs this more than the agent does.

**6. Rules and scripts in the dump.** One key each. Without it no renderer can draw the program, and
the visual desk will silently under-report the thing most likely to surprise its owner.

**7. Ordering and reach.** Rules fire in definition order, undeclared. With two people in one world
(the round-one/two problem) a rule also needs an owner and a reach; Lark's `reach=mine|ours|world`
with a signature for crossing sides is the version I would take. Priority is lower only because one
person can live without it; two cannot.

**8. Composition with a return value.** Scripts sequence but cannot answer. `run` produces receipts,
not values, so no script can decide anything. This is the top of the ladder and I would leave it last
deliberately: with 1–3 in place, most programs people actually want on a desk are expressible without
functions that return, and adding returns is where a small language turns into a large one.

**Deliberately not on the list: loops.** A rule over a selection is already `map`, and it is the right
shape for a desk. What is missing is not iteration but *fold* — a count, a total, a max — and fold is
primitive 2 plus primitive 3, not a new construct. I would refuse `for` in this language for as long
as possible.

---

## 5. What I would do next

Build **primitive 5 (dry run) first, even though it is fifth in value**, because it is the only one
that is pure addition: it changes no existing behaviour, it needs no new state, and it makes every
subsequent change safe to try on a real desk. Then 1, 2, 3 together as one release — they are one
idea (a rule that can fire again, on a value it computed, tested by a comparison) and shipping them
apart produces three half-languages.

And then re-run `make.py` against a desk with real automation on it and see what the graph says. The
honest test of the whole picture is whether the wires tell Alex something he did not know about his
own desk. On twelve rules I wrote myself, deliberately, it told me four things I had forgotten. That
is a weak test and I know it; the strong one is somebody else's rules.

— Moss
