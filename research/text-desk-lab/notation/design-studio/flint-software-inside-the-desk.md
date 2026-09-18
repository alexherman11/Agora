# Flint: software inside the desk

Alex asked how agents can work on software inside the desk, build more complex code through rules, and what
would unlock visual scripting. I answered it by building — a working issue tracker in a scratch session
(`python explore.py proto-flint`) using **only** what the desk has today: surfaces, views, props, scripts,
rules, the clock, handles. No proposed notation. Nothing from three rounds of my own design language.

Rendered: `http://localhost:8770/flint-desk-as-program/` — the board, the program, the cascade, the breakages.

The headline is not the one I expected to write.

---

## 1. The desk is already programmable, and I do not think anyone noticed

Three facts that are true today, in the shipped lab, with no additions:

**A tag is a button.**

```
rule on tag by=flint do run start $item
```

**A rule on a verb is an event handler.** `on <verb> by=<actor>` is a listener with an actor filter.

**Rules chain, and the chain prints itself.** One command, three rules deep:

```
> do tag a11 add=go
ok tag a11 add=go  [e18]
  tags now: design,go
~ r5 fired on a11: run start a11 → ok prop a11 state=doing  [e19]
~ r1 fired on a11: ok move a11 into=f03  [e21]
~ r4 fired on a11: ok tag a11 add=too-big  [e22]
```

A click ran a script, which set a property, which moved the card between columns, which tripped a size check.
Every step is a `~` line under the command that caused it, attributed, and the whole cascade undoes as **one
act**. `why a11` prints the causal chain with the rule that produced each step.

That is an event-driven application with provenance, written in six lines of desk text, and it was already
here. So **"what unlocks visual scripting" may be the wrong question.** The scripting is not missing. A visual
front end for this would be a *rendering* of rules, scripts and their fire counts — which is a presentation
problem, not a language problem, and every one of us spent two rounds on presentation.

What *is* missing is smaller and more specific than "scripting", and it is the subject of the rest of this file.

## 2. The thing I could not build: a WIP limit

The tracker works. States drive position, the clock tags overdue items, a size check fires. I could not write
the one rule that every kanban has:

```
> rule when in:Doing,count>3 do tag add=over-wip
ERR unknown selection term 'count>3'
```

There is no count. A view displays `3 matches`; nothing can act on the 3. Nor is there any comparison on a
property:

```
> find prop:size>3
ERR prop:k=v (prop:k alone selects things that have k)
```

Only `due<` and `age>` compare, because they are hard-coded. And a script cannot read a value at all:

```
script report = do comment $1 line="size is $1.size"
> run report a11
ok comment a11 line='size is a11.size'          <- the literal text, not the value
```

`$1.title` exists; nothing else does. **Scripts pass ids and literals, and compute nothing.**

So the ceiling is not power. It is **arithmetic**. The desk can route, filter, trigger, chain and attribute,
and it cannot count to three.

---

## 3. The breakage list, in priority order

Ordered by how much damage each does, not by effort. The first three are honesty failures, which in this
house outrank missing features.

### 1. `create` echoes arguments it discards — silently

```
> do create Inbox kind=task title="Silent argument test" wibble=7 due=2026-09-30 nonsense="hello"
ok create f02 kind=task title='Silent argument test' wibble=7 due=2026-09-30 nonsense=hello  [e15]
  a14 task "Silent argument test" · due 2026-09-30 · 0w
```

`wibble` and `nonsense` were accepted, repeated back inside the `ok`, and dropped. Only `due` did anything.
I found this because I had seeded three issues with `props=state:inbox,size:2,owner:flint` and later found a
table with an empty `size` column. `props` is not a create argument at all — it appears exactly once in
`explore.py`, inside a debug repr.

This is the worst bug I found, for a reason specific to this design. **The `ok` line repeats what was
*typed*; the `now:` line reports what was *done*; they sit in the same receipt and nothing distinguishes
them.** The desk's whole claim is that receipts state what changed. Here the receipt states what did not.

And it poisons everything downstream: my rules never fired for that issue, and a less suspicious reader would
have concluded that rules do not work.

> Fix: name what was ignored. `ok create … [e15] · ignored: wibble, nonsense (not arguments of create;
> use do prop to set properties)`. This is a receipt change, not a feature.

### 2. `$item` fires on the wrong object

```
> rule on tag by=flint do tag $item add=looped
> do tag a07 add=ping
~ r6 fired on a07: ok tag a14 add=looped  [e25]
```

The rule fired on `a07` and acted on `a14`. `help rules` says `$item` is "the thing it fired on";
`help handles` says `$item` is "the last thing" created in the session. Two meanings, one name, and the
handle wins inside a rule.

`why` records the contradiction in a single line and prints it without complaint:

```
> why a14
  e25 tag add=looped · flint by rule r6 (because of e24)      <- e24 happened to a07
```

A rule silently acting on the wrong object is the single most corrosive failure a rule engine can have,
because rules run unattended and the damage accumulates before anyone reads a receipt.

> Fix: give the rule-scoped binding its own name (`$fired`, or `$on`) so it cannot collide with a session
> handle, and refuse a rule whose action names a session handle at all — a standing rule must not close over
> a value that meant something at the moment it was typed.

### 3. The help and the parser disagree

```
> find prop:owner
ERR prop:k=v (prop:k alone selects things that have k)
```

The refusal states the rule it is refusing. `help selections` advertises the bare form; the parser rejects it,
and also rejects `-prop:owner`, so "things with no owner" cannot be selected. Small, but it undermines the
one thing an agent relies on in an unfamiliar system: that the help is true.

### 4. No count, therefore no limits, no rollups, no progress

WIP limits, "3 of 5 checks passed", "this surface is full", "nobody owns four of these". All unsayable.

### 5. No comparison on a property

`prop:size>3`, `prop:priority>=2`. `due<` and `age>` prove the shape is wanted; it is just not general.

### 6. A script cannot read a value

No `$1.prop.size`. So no script can pass one thing's value to another thing, which is most of what a small
automation does.

### 7. A rule cannot fire on talk

From round two, confirmed here: a comment is not a thing the selection language can name, so `rule when
comments:open,age>2 do …` can select the *host* but a rule can never fire on a *reply*. Half of what anyone
would want to automate in a shared desk is conversation, and it is unreachable.

### 8. There is no way to test a rule

You discover what a rule does by triggering it in the live desk. I wrote a self-triggering rule by accident
(#2 above) and found out by doing it. There is no dry run.

### 9. No form, no schema, no required fields

`create` accepts anything — which is the same defect as #1 seen from the other side. There is no declaration
of what a `task` is, so there is nothing for a receipt to check an argument against. A schema would have made
#1 impossible.

### 10. The tag-as-button overloads tags

The button works, but the trigger lives in the card's tag list forever, next to `bug` and `design`. Control
flow and data share one field. Anyone tidying tags changes behaviour.

---

## 4. The minimum additions that would have let me finish

Six, smallest first. Three are bug fixes, not features.

| | addition | risk |
|---|---|---|
| A | receipts name ignored arguments | none — this is a bug fix |
| B | `$fired` distinct from `$item`; refuse session handles inside standing rules | none — bug fix |
| C | `find prop:k` and `-prop:k` work as documented | none — bug fix |
| D | comparison on props: `prop:size>3` | low — same shape as `due<`, one parser change |
| E | `count>N` as a selection guard on a rule | **the dangerous one** |
| F | `test <rule>` — print what would fire, change nothing | low, and it pays for E |

A, B and C are not proposals; they are the desk failing its own standard and should be fixed regardless of
where this design goes.

## 5. Which of these are dangerous, and why

**E (count) is genuinely dangerous, and not for the reason you would guess.** It is not that counting is
complex. It is that a count is a fact about a *collection*, so a rule guarded by a count fires **because of
something that did not happen to the thing it acts on**. Today every rule action traces to one event on one
thing — `why` prints `by rule r1 (because of e19)` and that sentence is true. Add a count guard and the cause
becomes "Doing became four", which is not an event on any single thing, and the provenance line either lies or
goes vague.

> If `count` is added, the event model needs a way to name a **collective cause** first. Otherwise the desk
> buys WIP limits by spending the property that makes it trustworthy, which is a bad trade at any price.

**E (value substitution in scripts) is dangerous because it is the first inch of a language.** `$1.size` is
harmless. `$1.size + 1` is an expression language, and an expression language inside rules is one nobody can
audit and no refusal can bound — this is exactly how a small declarative system becomes a macro dialect with
no specification. My recommendation: **allow reading a value into an argument; forbid arithmetic on it.** If a
task genuinely needs arithmetic, that is the signal that the thing being built is a real program, and it
should be a foreign body with a declared interface and a stated opaque frontier — not a rule.

**Cascades are already dangerous and nothing bounds them.** My three-level cascade was a pleasure. I also
wrote a self-triggering rule, and the only thing that saved me was a *no-op detection* —
`~ r5 could not run a07: a07 already has state=doing; nothing to change`. That is luck, not a guarantee: a
rule pair that alternates two values would not no-op. Once conditions and counts make cascades common this
will bite.

> Needed before E: a cascade depth limit with a printed refusal naming the ring
> (`refused: r5 → r1 → r5, depth 8; do rules to see the ring`), and F, so a cascade can be tried before it is
> loosed.

**The tag-as-button should not be blessed.** It works by accident of overloading. If buttons are wanted, give
them a verb that leaves no residue — `do press <thing> <name>` — so tags stay data.

---

## 6. Real code as a holding — noted, not tested

I did not get to this, and I would rather say so than describe it. One observation from reading the source
(read only, never edited): the natural first use of the desk on real code is **not editing**. It is
diagnostics and discussion. The six bugs above are anchors on the line axis of one holding
(`explore.py`), the issue tracker I built is the rail, and nothing in the desk would have to change to hold
them except the ability to *have* a holding.

That is a one-evening experiment and it is the one I would do next, because it is the first case where the
desk would be doing work on something Alex already cares about rather than on itself.

---

## 7. What I would actually do next, in order

1. **Fix A, B and C.** They are honesty failures in a system whose only real asset is honesty. A day.
2. **Build F (`test <rule>`).** It costs little, and it is the prerequisite that makes everything after it
   safe to try.
3. **Render the program, not a new language.** Rules, scripts and fire counts drawn as a panel, with `why`
   as the click-through. The prototype linked above is a rough version. This is what "visual scripting" should
   mean here, and it needs no new semantics at all.
4. **Then, and only then, consider `count`** — after deciding what a collective cause looks like in `why`.
5. **`prop:k>n`** whenever convenient; it is cheap and it is not dangerous.

And the thing I would *not* do: add an expression language. Every reason to want one is a reason to find out
whether the thing being built should be a rule at all.

---

## Appendix: one more piece of evidence, from outside the desk

While writing this, my entry in `prototypes/index.html` was overwritten by a concurrent write from another
designer; Lark's entry was lost in the same collision, and neither of us was told. I restored both by hand.

Ten minutes earlier the desk had refused one of my commands with `stale: a09 changed since you last saw it`
and been right to. **The desk has a mechanism that prevents exactly this, and the moment four collaborators
stepped outside it onto a shared filesystem, the thing it prevents happened immediately.** That is the
strongest argument I have seen all week for putting real work inside the desk rather than beside it — and it
arrived as an accident, which is the only way I fully believe anything.
