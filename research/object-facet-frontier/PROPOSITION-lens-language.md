# The lens language: how we know it stays a lens, and how to build it out

A proposition for Alex from the object/facet frontier, round six. 24 September 2026.

Written by Jeff from the three round-six notes: Sable (`sable-6-right-side.md`, the properties as a formal statement and the behavior language), Pike (`pike-6-compiler-and-painter.md`, the compiler and painter, the case on `if` and nesting, the growth measures) and Juniper (`juniper-6-attacks-and-budget.md`, attacks on the properties, an audit of the prototype, the household budget). The brief was `HANDOFF-lens-language.md`, written by the session that taught POSITION v2 to Alex and recorded his reactions. Where the three disagreed, the disagreement is shown and named. Cross-challenges between the three ran by message and in the desk's Talk column (a136 to a144), and each amended their note where they changed position.

Labels, as in POSITION: **[ran]** was executed in the desk or over the source, and the number printed is quoted; **[source]** was read in `scene.py` (796 lines) or `lens.js` (123 lines); **[design]** is a proposal that has not been run.

This document teaches the concepts first, then gives the evidence, then the two-part proposition Alex asked for, then his decisions.

---

## 1. The question

Alex's directions, from the handoff:

- The compiler may grow. `scene.py` is a compiler for a new language, and real compilers are far longer than 796 lines. No cap. But it must not grow linearly per word.
- The painter may grow too, for more complex geometry. Same rule.
- The "fifth interpretation that is not about dates" tripwire was a bad proxy.
- He likes Pike's line in the sand but asks why we are so against `if`, which seems useful, and wants the case against nesting made properly.
- His question: are we heading for a worse JavaScript even without a scripting language? What in the design prevents it? What are the advantages of lenses?

He wants back two things: reasonable ways of knowing we are on the right side, each checkable and ideally runnable in the desk, with what would count as failing it; and ideas for building out the language and its structure.

**The short answer, before the long one.** A worse JavaScript is not a language with `if` in it. It is a language whose programs can only be understood by running them in your head, because their meaning is their implementation. JavaScript's defining freedoms are five: ambient reads, ambient writes, hidden state, silent failure and unbounded evaluation. The lens stays a lens by removing each of those five, as properties a test can check. Any feature that keeps the five properties is admissible, `if`, arithmetic and nesting included. The prototype today keeps some of them and breaks others, and the round found exactly where. The place it is most a worse JavaScript today is not the lens at all. It is scripts and rules, which live beside the lens, outside history, and act on things a click never named.

---

## 2. Concepts, in the order they build on each other

### 2.1 A lens is a definition, and its parts are anchors

A lens is a note whose text is a program. In the kernel's nouns from POSITION, the lens is a referent whose code aspect holds the text. Its parts (`cal : column, of tag:day, each card`) are anchors inside that text, the way a character id is an anchor inside prose. That is Sable's answer to Pike's round-four question of whether a part is an aspect or an anchor: an anchor. Two consequences follow. A part is addressed by its path, so a gesture and a fence can name it. And an override by another owner is not a write to the part; it is a separate definition that refers to the part, the same shape as an anchored comment. Claim is not grant. When upstream removes the part, the override prints `override orphaned`; when upstream revises it, the override is pinned or follows, by the overrider's choice.

### 2.2 Evaluation is a function

Sable writes the scene as S = E(L@rev, W, V): the lens at a revision, the world, and V, the viewer's declared facts (`$me`, `$today`, the painter's `~` observations, and, after this round, the viewer's own state). Two properties fall straight out of writing it that way.

- **Purity.** E appends no operation, and reads only through the accessor, the world and V. Check: the event count is unchanged across a `scene` command. **[ran]** Sable's probe 1 passed: two builds, history still ends at e67. **[source]** Juniper found a violation of the read half: the `worktrees` row source loads other sessions' pickle files from disk during compilation. Sable confirmed it as a purity violation and amended the property to say "reads only through the accessor".
- **Determinism.** The same (L@rev, W, V) gives the same S. No clock, random or iteration-order reads except through V. Check: two builds are byte-identical. **[ran]** Passed in probe 1. **[ran]** Juniper then broke it: a plain `look` by one viewer, which appends no event, changed another viewer's `of actors` scene at the same world revision. Per-actor read positions are an input the function does not declare. Sable's fix: they become world facts or printed per-viewer drift.

### 2.3 The read-set: what a scene read, and why it is the whole mechanism

Every node in the scene records which aspects it read, at which revision. The property is soundness: for any other world that agrees with this one on the recorded reads, the scene is the same. The test is perturbation: change an aspect outside the printed reads and nothing moves; change one inside and exactly the nodes that list it move.

**[ran]** Sable's probes 2 and 3 passed for props: changing the unread `color` moved only the header; changing the read `beds` moved the card that printed `read beds=5`. **[ran]** Juniper then broke it with a negative read: tagging a thing outside the printed reads moved the scene, because a repeat over `tag:day` had read "the set of things matching this selection" and printed nothing. Pike independently added the fix: the accessor must log membership reads as well as aspect reads.

The read-set is not only honesty. Sable's point, which Pike accepted, is that one read list does three jobs: it is what the text printer prints, it is what a gesture's fence carries, and it is what an incremental compiler uses to rebuild only the nodes whose inputs moved. That is the runtime half of "sublinear", beside the source-code half in section 4.

The handoff's "everything prints" and "no hidden state" both fold into this one property. Hidden state is exactly what makes the perturbation test fail. And Juniper showed "everything prints" is not a property at all: a lens can print fourteen lines of true-looking absence and no Mondays (her A5), and a derive can print its inputs perfectly and mean the wrong thing (her A2, `day-n $a.start $a.week`, week six treated as day six). The checkable form is: the printed reads equal the recorded read-set, and there is no silent value.

### 2.4 Names and scopes, written down

Every bug the handoff listed was a scope bug: the prop `n` that shadowed the repeat count and crashed the compiler, `$item` against `$it`, "that name is taken" without saying by what, `only when $wd=Mon` accepted though `$wd` named nothing. A language whose scope rules exist only in its implementation is a worse JavaScript in miniature. Pike wrote the rules down:

```
ref      := '$' name ( '.' field )?
lookup, innermost first:
  1. lets      names made by `derive` in this part or an ancestor
  2. frames    names made by `as`, and `it` for the nearest repeat without `as`
  3. thing     the current thing's fields: title text kind due tags id item, then its props
  4. host      me today session count
reserved   title text kind due tags id item it count me today session
```

- **N1.** A `derive` or `as` may not shadow a visible name. The refusal names the earlier binder and its line. **[ran]** Juniper's A1: today a user frame silently shadows another user frame (`as a` inside `as a`), and the scene prints "Alpha under Alpha" under both outer rows.
- **N2.** A prop whose name is reserved is read as `$props.<name>`. This was the crash that lost four accepted writes.
- **N3.** `$count` is the size of the nearest repeat, defined inside its instances too. `$n` is retired with an alias period. **[ran]** Juniper's A6: `$n` is empty inside an instance, so `"$n days here"` painted " days here" fifteen times while the header printed 15.
- **N4.** `as` names what its part binds: on one thing, the thing; on a repeat, each instance; on a part that binds nothing, refused.
- **N5.** `$item` is the occurrence, the appearance a gesture acts on. `$id` is the referent. `$it` is a frame, never a thing.
- **N6.** Every reference resolves at check time to a let, a frame, a thing field or a host fact. Prop reads resolve at evaluation and print `(no x)` when missing. Sable accepted this on one condition: a missing prop is a third state, not false. A test on a missing prop must print `(absent: no x)`, never a wrong reason like `(absent: not $wd=Mon)`.

Sable's property behind these is total name resolution: every name resolves at compile time to exactly one thing, unresolved and shadowed names are refused, and the refusal vocabulary is generated from the same table as the grammar. **[ran]** His probe 7: `if` is refused today with a list of eleven allowed words that omits seven the grammar has. A refusal text kept by hand is a second grammar, and it drifts. Juniper added that selection syntax needs the same stage: `prop:to>date` is accepted today and matches nothing.

### 2.5 The compiler as stages, so a word is a table entry

**[ran]** Pike measured the growth Alex diagnosed. From the first version on 18 September to now, seven words cost 605 lines, about 86 per word. The one `make()` function grew from 24 lines with 4 word branches to 175 lines with 12. Every word touches three places (parse, make, the text printer), and seven words also touch the painter. `make()` does five jobs at once: resolves names, evaluates, fences, keys occurrences and builds nodes, so every new word interleaves with every old one. The same repeat is written five times.

The proposed shape:

```
parse -> resolve -> check -> lower -> evaluate -> print (text) -> scene (painter)
 table    scopes    rules    to IR    6 kinds     by IR kind      by paint kind
```

The core intermediate representation has six kinds, and every current word lowers to them:

| Kind | Meaning | Words today |
|---|---|---|
| `bind one` / `bind many` | make a thing, or each of a sequence, the current frame | `the`, `of`, `over`, `each` |
| `let` | name a value computed from inputs by an operator or a definition | `derive`, `capture`, template reads, `spread`, `at item` |
| `guard` | build the part only if a test holds; otherwise print the absence and the test | `only when` |
| `emit` | a scene node with paint properties | `column row free`, `role`, `text`, `clamp` |
| `act` | a gesture bound to a command template, with its read set | `on click/edit/drag do` |
| `place` | put another definition here | `lens`, later `from` |

The printer walks the IR, not the surface words: `bind` prints its state (live, empty, ambiguous, unplaced, gone), `let` prints `name = op(inputs) = result`, `guard` prints its test, inputs and branch, `act` prints its filled line. So the printer never learns a new word. A new surface word is one row in the parse table plus a lowering of a few lines, and a library word costs the compiler nothing.

**Core versus library.** Core: the six kinds; the operator table (arithmetic, comparison, date arithmetic with units, `running`, and the allocation operator in 2.13); the selection language; and the row sources that expose kernel nouns only (things, the identified parts of an aspect such as text blocks, timeline segments and list elements, operations, observers). Library, written in lens in notes tagged `lib`: `define day-n(date, n) = date + days(n - 1)`, and likewise `days-from`, `week-of`, `spread`, later `every`, `pick`, and shapes. Pike withdrew "row sources are core" after Juniper's audit: `sections` hard-codes the document app's `##` convention and becomes a library grouping of text blocks; `comments:` becomes a typed relation term like `parts:`; the `worktrees` source moves into the world as operations and things. A row source can be written in lens exactly when it filters, groups or maps core rows. It cannot when it needs new world access, because that is a new kernel noun.

### 2.6 `if`

Why were we against it? Wren's growth rule, "no if, no arithmetic", was protecting three things, and each can be stated directly:

1. **Printed absence.** An `if` without an `else` makes a value that silently does not exist. So a value `if` must be total, and it prints its test, its inputs and the branch taken, with `(not taken: ...)`. A structural `if` is `only when`, which already prints absence; it gains value tests, so `only when $wd = Mon` becomes legal and meaningful instead of accepted and meaningless.
2. **One meaning per gesture.** A gesture's command line may not branch. What the painter sends must be what the scene printed. Two outcomes are two guarded parts with two lines, and the guard's inputs join the gesture's read-set.
3. **Declared inputs.** An `if` on `today` makes the view depend on the clock; `today` is a host fact, read, printed and refreshed, never hidden.

From the kernel's side, Sable adds what the fence must know. The sound read-set of `if T then A else B` is the inputs of T plus the inputs of the branch taken, recorded as it runs. Fencing both branches statically is sound but over-blocks, the same failure as Astra's whole-state fingerprint. Both branches must still be name-resolved at compile time, or an untaken branch is an unexercised program that fails on the first Monday.

So the kernel has no objection to `if`. The old rule was standing in for "no unprinted, unfenced branching", which read-set soundness and total name resolution now state directly. Juniper's budget shows the first `if` anyone needs: the housemates who stay have no leave date, so the day count needs a default, which is `if` or coalesce by another name.

### 2.7 Nesting: the case is about pointers, not taste

Alex asked for this argued, not asserted. Here it is.

An intermediate value inside `f(g(x), h(y))` can be named only by position: "argument one of the outer call". Position is the worst pointer. POSITION 2.1 showed why for lists: an insertion retargets it and it still looks right. Anything outside the expression that needs to name an intermediate needs a stable key: a capture, a comment ("why +2?"), a proposal row's provenance, a fence entry, a history query.

That is the whole cost. It is not readability, and it is not printing. **[ran]** Pike's `lower.py` takes the course due date Juniper had to store by hand as `off=45` because the lens could not compute it, and writes it as one nested derive:

```
derive dd = start + days(7 * (week - 1) + 2 + (7 if week >= breakweek else 0))
  dd.1 = week 6 - 1 = 5
  dd.2 = 7 x dd.1 = 35
  dd.3 = dd.2 + 2 = 37
  dd.4 = week 6 >= breakweek 4 = True
  dd.5 = if dd.4 -> then 7 = 7
  dd.6 = dd.3 + dd.5 = 44
  dd.7 = days(dd.6) = 44d
dd = start 2027-03-29 + dd.7 = 2027-05-12
```

That is the date Juniper computed by hand, and when the break moves it follows, and the print shows which branch the break took. Compilers have always lowered nested expressions to named steps; this is three-address code with the names printed.

The rule, in the wording Sable and Pike both signed: **nesting is allowed and the printer lowers it to steps. A step named with `let` has a stable key and can be captured, commented or queried. An unnamed step prints under a position label like `dd.3` for reading only, and any reference to it is refused with "name it first".** Pike's round-five rule, one operator per derive, is withdrawn as syntax and kept as printing: a derive that lowers to more than eight steps prints a notice that it would read better with named parts. Advice, not refusal.

### 2.8 Effects are proposals, and a proposal is the whole cascade

The lens cannot write. A gesture's `do` line is the only effect, and it goes through the desk's gateway, attributed, fenced on what the gesture read, undoable. The handoff had that as property two. Sable showed it is not enough. **[ran]** His probe 4: `do prop a122 beds=6; do prop a999 x=1` applied the first half and refused the second. **[ran]** I reproduced it in a scratch session: `beds=6` became event e2, then `no such id 'a999'`. A two-command gesture has exactly that shape. The missing word was *atomic*.

The proposed semantics are Astra's, from the Codex team's evaluator, with Sable's changes:

- A gesture or a rule action yields one proposal: operation rows that all read from one input state, applied whole or not at all, undone as one batch. Preview is free: the rows print as `(referent, aspect): before -> after` before anything applies.
- The guard is the read-set fence at (referent, aspect), not Astra's whole-state fingerprint, which her own spec admits over-blocks.
- Mints get placeholders (`$new.1`), so "create, then place it" is one proposal without a sequential read.
- Equal writes coalesce, unequal writes to one address refuse the whole proposal. That is exactly Sable's round-four merge rule, so gestures, rules and worktree merges share one conflict rule.
- **The proposal is the whole cascade.** This came from Juniper's A4 (section 2.9). A script expands in the preview; rules run to a fixpoint of at most three passes, and each pass prints; the gesture carries every pass's reads plus the revision of every definition that fired; at apply, the gateway recomputes and refuses if anything moved. A rule's write on a thing the gesture never named is fenced because the preview promised to write it. This depends on rules being world data, so they have revisions.
- **Viewer effects are admitted.** Juniper's F4: copy three amounts to the clipboard, open the landlord's portal. Sable admits them inside the same property as named viewer effects from a closed host list. They print their exact payload in the preview, have no undo, and are never replayed.

The cost is read-your-own-write inside one gesture. A gesture that must see a value it just wrote becomes a proposal plus a rule cascade, printed as two proposals. **[ran]** Juniper checked the household budget against this: no step needs it, given mint placeholders.

### 2.9 Definitions are world data, and today most are not

A lens is a note: versioned, forkable, undone with the same verbs. That is the handoff's property five and it holds. Sable generalised it: every definition that can change a scene or an effect must be a referent whose code changes only by operations. Then he tested it. **[ran]** His probe 9: `script sprobe = look f18` left history unchanged. **[ran]** I reproduced it. Rules, scripts, the clock and the style file are definitions outside history.

Juniper then showed why this is the finding of the round. **[ran]** Her A4: a script `tidy` that tags, retitles and sets a prop, a rule `on tag do prop Beta week=99`, and a gesture `on click do run tidy $item`. The scene printed only `click: run tidy a03`. Running it made four events. One was `prop a05 week=99 via rule r1`, on Beta, a thing the gesture never named, so the gesture's fence never covered it. The script and the rule made no events when defined. Every effect went through the gateway, attributed and undoable, and the scene still could not say what the click would do.

That is the worse-JavaScript route in the prototype today. The program has not gone into the lens. It has gone beside it, into global definitions the note cannot show. Juniper's recommendation, which I have taken into the build order: forbid gestures from calling scripts or rules now, until proposals preview their full effect including the cascade.

### 2.10 Bounded, and honest about it

Evaluation terminates: no recursion in `define`, no loops other than a repeat over a finite source, a node budget. Sable's addition: every cap prints as `n of N`. **[ran]** His probe 8: `of events` prints `20 of events` while the world holds 76; the cap is silent. **[ran]** Juniper's F3: a year view of 365 days by 5 parts was refused over the 1500-node budget, and the last-good fallback did not engage because the fallback build starts with the failed attempt's count. A bound should degrade, not refuse a lens that was working. Pike's split: the check stage refuses at write time only what the lens text alone makes wrong (unresolved names, a value test used as a selection, a branching gesture line, recursion). Bounds that depend on data degrade: the compiler clamps the repeat nearest the budget and prints `days (showing 1-292 of 365 · node budget 1500)`. Juniper's warning stands: a lens can pass check at write time and exceed the budget later as the world grows, so the clamp is not optional.

### 2.11 Per-viewer state

A tab, a sort order, a collapsed section. The handoff's "no hidden state" allowed only world data or printed per-viewer drift, and a lens can read neither kind of per-viewer state. **[ran]** Juniper's A3 built a tab switcher the only way possible today: props on the lens note. Ben's click switched everyone's tab and added a journal event that undo must step through.

Pike and Sable gave the same answer from two sides. Pike: a declared viewer variable, `view tab = bills`, read like a host fact, printed as `~ alex: tab=bills`, written by a gesture whose target is the viewer store rather than the gateway, so never journaled; the painter keeps these values and sends them with each scene request, about five lines. Sable: these are viewer-owned aspects in the viewer's own log, never merged, and four things stop them becoming hidden state: they are in the scene's reads and prints, only gestures write them, rules and other viewers cannot read them, and they can be listed and reset. Determinism and the read-set still hold because the viewer's values are an explicit, printed input. Juniper's test: two viewers, one lens; one changes a tab; fail if the other's scene changes or the journal gains an event.

### 2.12 Valid time: when a value is true, not when it was written

POSITION 2.8a named this as an open kernel item. **[ran]** Juniper's budget hit it at step five: the rent rose to 2550 from 1 November, the write overwrote the rent, and the captured October statement printed `Rent 2550` under `captured month=2026-10-01`. `capture` fixes the frame's month but not the bills' amount. The captured statement is silently wrong.

Sable's shape needs no new noun. An aspect may have a sequence representation; text is one, and a timeline is another: segments `{from, value}`, each an anchor with element identity. The one-sentence kernel change: an aspect's representation may be a sequence with element identity, and the fence may key on (referent, aspect, anchor). Two people editing different segments of `pace` do not conflict. `at <date>` is library: Pike lowers it to a `bind one` over the segments where the date falls, which gets the binding states for free, so a gap prints `(empty)` and an overlap prints `(ambiguous)`. A repeat over a timeline needs one general change to row sources that sections will need too once text has anchors: rows keyed by the segment's own id, a read-set entry per segment plus the segment list, and ordering by valid time. Valid time (`pace at 2026-11-03`, what applies on that date) and transaction time (`pace@e40`, what we had said by then) stay distinct, and together answer the bitemporal question.

**[ran]** Juniper checked the shape against the budget. It survives: Casey leaving becomes one write that closes her segment; the rent rise is one added segment; the October statement derives with `at` October dates and the captured-statement wrong disappears. Two things must be declared in the timeline's definition, because both changed her numbers: the end convention (an exclusive end makes Casey absent on the 15th, a one-day slip, and a missing end must mean open-ended or Ana and Ben vanish from every day), and the split policy (per-day among those present gives Casey 425.81; person-days gives 514.29).

### 2.13 Quantities need more than printed inputs

This is the concept the round added that nobody had before. **[ran]** Juniper's budget: with every input printed correctly, the three shares summed to 2640.01 against a total of 2640. A penny, silent, in arithmetic that printed perfectly. Printing inputs is what makes a date trustworthy. A derivation over a whole also needs a conservation check: that the parts sum to the whole, with the rounding rule and where the remainder went. Her proposed print:

```
share.Casey = 2640 x 15 / 77 = 514.2857 -> 514.29 (round half-up, cents)
check: 1062.86 + 1062.86 + 514.29 = 2640.01; remainder -0.01 to the largest share (Ana) by rule -> 1062.85
```

The one disagreement left in the round is where this lives. Pike makes it a core operator producing a `let` whose value is a list of rows, `derive shares = split $total by $days rounding cents remainder largest`, because the sum guarantee has to belong to the operator and not to each author. Sable makes it a `check` word that prints pass or fail, plus library allocation words that always print their check, a named remainder rule and a named split policy. My recommendation is Pike's for allocation, so that no author can split a whole without the check, with Sable's `check` word available for every other derivation over a whole.

### 2.14 The painter grows by primitives, never by shape or app

**[source]** Today the painter has one element kind, three layouts, a role class, an absolute box, clamped text and three gestures. It names no role, kind or lens, and paints exactly one element per scene node, which is Wren's ratio at 1.0. Pike proposes it grow by paint primitives, each printed: `frame` (layouts including grid, clip, scroll, transform), `text run` (later with anchored ranges), `path` (points in the frame's space, stroke and fill by role, printed as `path [series] 12 points, bbox ..., from let pts`), `image`. Shapes, charts, arrows and routes are library lenses that emit `path` from `let` values. Gestures are interaction primitives, not per app: press, edit, drag, carry and drop, each with a keyboard path. Continuity is generic and keyed by occurrence: the per-part definition hash on every gesture, a draft kept on refusal, the pending scene held while a draft is open. Estimate **[design]**: about 180 lines, growing by primitive only.

Pike's answer on the hidden last-good cache follows from this. It is removed in three parts: a lens edit that fails the check is refused at write time, so the current revision always compiles; if an inner lens or library definition breaks, the scene shows the latest revision of the whole closure that passes, which is derivable from history; and the draft needs no stored scene, because the only one is the frame the painter already holds, printed as a viewer observation with gestures off.

---

## 3. The evidence, executed

### 3.1 Sable's probes against the properties [ran]

| Probe | What printed | Property |
|---|---|---|
| `scene` twice, same world | byte-identical; history still ends at e67 | purity, determinism pass |
| change the unread prop `color` | lines identical, only the `world @N` header moved | read-set passes |
| change the read prop `beds` | `card a122 ... read beds=5` moved | read-set passes |
| `do prop a122 beds=6; do prop a999 x=1` | `ERR no such id`, but `e70 prop a122 beds=6` applied | atomic proposals **fails** |
| `only when $wd=Mon` | accepted; `(absent: not $wd=Mon)`; `$wd` is not a name | name resolution **fails** |
| prop `n=7`, `text "n is $n"` | `"n is 7"`, the repeat count silently shadowed, no `read n=7` | name resolution **fails** |
| `if $beds` | refused; the list of eleven allowed words omits seven in the grammar | name resolution **fails** |
| `of events` | `20 of events` with 76 in the world | bounded and honest **fails in part** |
| `script sprobe = look f18` | `scripts` lists it; history unchanged | definitions as world data **fails** |
| gesture with two commands | `click: do prop a122 beds=9; prop a122 color=red`; same non-atomic batch; `$title` read not printed | atomic proposals, read-set printing **fail** |

I reproduced probes 4 and 9 in a scratch session with the same result.

### 3.2 Pike's growth measurements [ran]

| Commit | Date | `scene.py` lines | parse branches | `make()` lines | `make()` branches |
|---|---|---|---|---|---|
| v0 | 18 Sep | 191 | 8 | 24 | 4 |
| binding words | 23 Sep | 788 | 15 | 169 | 12 |
| now | 23 Sep | 796 | 15 | 175 | 12 |

Seven words, 605 lines, about 86 per word. Checks that pass today: the compiler never writes the world; the painter names no application; one painted element per scene node; every visibly painted field is printed. Gaps: one hidden compiler state (the last-good lens cache); occurrence keys painted as `data-key` but never printed, so an agent cannot name "this card".

### 3.3 Juniper's attacks: lenses that keep all eight handoff properties and are still wrong [ran]

- **A1** a user frame silently shadowing another; both outer rows print "Alpha under Alpha".
- **A2** a derive with perfect provenance and the wrong meaning (`day-n $a.start $a.week`).
- **A3** a tab switcher built from props on the lens note: one click flips every viewer's tab and journals an event.
- **A4** a click that runs a script; a rule changes a thing the click never named; no events for either definition; preview says `run tidy a03`.
- **A5** `only when $wd=Mon` over fourteen days: fourteen true-looking absences, no Mondays.
- **A6** `$n` empty in instances: " days here" painted fifteen times.

What the properties wrongly refuse: per-viewer view state (F1); a 13-month lease, `days-from` refusing spans over a year (F2); a plain year view, refused over the node budget with the fallback dead (F3); effects that are not world writes, such as copying three amounts to the clipboard or opening the landlord's portal (F4).

Her audit of the prototype against the eight, by line: the `worktrees` row source calls `pickle.loads` on other sessions' files during compilation, which is a read outside the world and code execution; the painter posts observations straight into desk memory; painter behaviour the scene never states (an empty edit silently dropped, a drag clamped at zero, `$x` filled with `String.replace` so only the first occurrence is replaced); per-actor read positions feeding the `actors` rows; lenses bound by title, not referent; row sources and interpretations as host code per feature.

Past Sable's probes, three more breaks: a negative read (tagging outside the printed reads moved the scene); a `look` with no event changing another viewer's `of actors` scene; `prop:to>date` accepted and matching nothing.

### 3.4 The household budget, the fourth task [ran]

Bills of 2400, 180 and 60 split three ways; Casey leaves on 15 October; rent rises to 2550 from 1 November; a cleaning bill is added.

| Step | Writes | Repairs | Silent wrongs before repair |
|---|---|---|---|
| seed, people, bills | 13 | | |
| split | 7, six of them hand-computed copies | | 0 |
| Casey leaves | 2 | 4 | 6, plus the empty `$n`, plus one penny |
| November, rent 2550 | 3 | 3 | 4, including the captured October statement |
| add cleaning | 2 | 2 | 2 |
| **total** | **36** | **9** | **14** silent, 2 visible |

Proration is step four. A bounded `days-from` gives Casey's fifteen days, so a range is a `where` over days. But the members who stay have no leave date and need a default, which is an `if`; the count cannot be used as a number because `$n` is empty; and the share needs multiply, divide, a sum across the people repeat (77 person-days), rounding and a conservation check. None of that is a `where`.

Juniper's honest cost: a ten-line JavaScript app would have split October correctly, penny included. The lens needed six hand copies, nine repairs and fourteen silent wrongs. Without printed arithmetic, defaults and dated segments, the lens is worse than the small app at the one everyday thing everyone does with money.

---

## 4. Part one: ways of knowing we are on the right side

Three kinds of check, from three seats. None is a line cap.

### 4.1 Properties of the language (Sable), each a desk test

| | Property | Check, runnable in the desk | Fails when | Today |
|---|---|---|---|---|
| L1 | Purity: evaluation appends no operation and reads only through the accessor | event count unchanged across `scene`; no disk or session read outside the accessor | any event, any outside read | passes the write half; fails for `worktrees` |
| L2 | Determinism: same lens, world and viewer facts give the same scene | two builds byte-identical | any difference | passes for props; fails for `of actors` after a `look` |
| L3 | Read-set soundness: recorded reads (aspects and memberships) are sound and printed; no silent value | perturb outside the printed reads: nothing moves; inside: exactly the listed nodes move | anything else moves, a read is unprinted, or a value fills empty without a marked absence | passes for props; fails for tag membership, `$title`, `$n` |
| L4 | Effects are atomic proposals, cascade included, previewed | a batch whose second step refuses leaves no trace; a preview names every write the apply makes | any half-applied batch, any write the preview did not name | fails |
| L5 | Definitions are world data | defining anything appends an event; undo reverts it | a definition with no event | fails for scripts, rules, clock, style |
| L6 | Total name resolution, selection terms included | a corpus of undefined, shadowed and misspelled names and terms, each refused with the binder named | any rendered instead of refused | fails |
| L7 | Bounded and honest | a pathological lens is refused naming the budget; every cap prints `n of N`; data-dependent bounds clamp, never refuse a working lens | a silent cap, or a refusal of a lens that compiled | fails in part |
| L8 | The host is independent of applications | grep the painter and compiler for kinds and app names | one or more | passes for the painter; fails for row sources and interpretations |

What became of the handoff's eight: "pure" is L1 plus L2 (purity without determinism still allows a clock-dependent scene); "effects through the gateway" is L4, strengthened by the words atomic and previewed; "everything prints" and "no hidden state" are one property, L3, restated as "no silent value"; "a lens is world data" is L5, generalised; "customization without forking" is a goal, measured as an override copying zero upstream lines; "host does not grow per app" is L8; "bounded" is L7 plus the no-silent-cap clause. Added: L6, where the listed bugs live.

### 4.2 Measures of host growth (Pike), each with the value that stops the build

| | Measure | Today | Fails when |
|---|---|---|---|
| C1 | core lines per new word, from git history | about 86 | after staging, the median of the next five words exceeds 20 |
| C2 | word branches in the evaluator | 12 | more than the six IR kinds, or any increase from a new word |
| C3 | places a new word touches | parse, make, printer, and the painter for seven words | a new word needs a printer or painter edit |
| C4 | print covers paint | passes for fields; keys unprinted | any painted field or element with no text counterpart |
| C5 | hidden compiler state | 1 | any state that changes output and is not derivable from world plus printed viewer facts |
| C6 | painted elements per scene node | 1.0 | a part paints more than three without a printed summary |
| C7 | the painter knows no app | 0 | 1 or more |
| C8 | core words per new task | trip 7; three tasks 7 plus 4 | more than one in five new everyday tasks needs a core change rather than a library define |
| C9 | lens against the code it replaces | notes lens 11 lines against 523 of JavaScript | a lens longer than a fifth of what it replaces |
| C10 | evaluation terminates and is bounded | node budget 1500; no recursion | any lens that loops or recurses past the check |

C1 to C3 are the direct test of "not linearly". They are measured per commit by `experiments/growth/measure.py`, so the trend is visible, and they should flatten after staging.

### 4.3 Tests of use (Juniper), each executable

- **T1 The task suite is the test.** Trip, course, book club, garden and budget, each with its changes. Fail on any repair or silent wrong after a change. Today the budget fails with 9 and 14; the trip's H2 run passed with 0 and 0. Record host lines added per task made to pass; it is linear if each task needs its own host code.
- **T2 Lint, as the check stage.** Refuse shadowed frames, `$` names that fill empty without a marked absence, and value tests in `only when` until value guards exist. Warn on gestures that run scripts or rules, title bindings, and derives over eight steps. One checker from the grammar table, at write time and on a desk command `check <lens|all>`. Pike and Juniper agree it must be the check stage itself, not a second tool, or it becomes a second grammar.
- **T3 Gesture preview.** Dry-run each gesture's line in a scratch fork and print the events it would make. Fail if it touches anything the line does not name, or depends on a definition that is not an event.
- **T4 Retitle everything** in the suite and rerun. Fail if any scene changes.
- **T5 Two viewers, one lens.** One changes a tab or sort. Fail if the other's scene changes or the journal gains an event.
- **T6 Degrade, don't refuse.** A 13-month span and a year view clamp or page with a printed note, and the last good version still shows.
- **T7 Conservation.** Any derivation that divides a whole prints that its parts sum to it.

What no check catches: A2, a derive that is meaningful, printed and wrong for the domain. Only the task suite and a reader catch that. That is true of every language, and it should be said plainly.

---

## 5. Part two: how to build out the language

### 5.1 One expression language, two contexts

Sable and Pike converged from opposite ends. There is one expression language with one scope model and one printer. It is used in a pure context (lens parts, derives, `only when`, a rule's `when`), where it may only read, and in a proposing context (a gesture's `do`, a rule's action, a definition's named operations), where the desk verbs are its only way to write and each verb is a function from arguments and an input state to operation rows. A command line is then a proposal, the union of its rows.

Pike's line in the sand, revised: no evaluator separate from this IR, ever. The trigger to watch is no longer an `if` or five steps. It is a derivation that needs state carried between evaluations, an accumulator across time rather than across a list. That is where a view language ends and a behavior language begins, and if the budget ever needs it inside a view, the boundary is in the wrong place.

### 5.2 What is core and what is library

Core: six IR kinds; operators per value type (number, date with units, text, comparison), `running`, `split`; the selection language; row sources over kernel nouns only. Library, written in lens: domain words (`day-n`, `days-from`, `week-of`, `every`, `pick`, `spread`), `sections`, the timeline type with `at`, shapes and charts emitting `path`. The test of the cut is C8: once the library exists, fewer than one in five new everyday tasks should need a core change.

### 5.3 The build order, merged and amended

Pike and Sable each proposed an order, then merged them; Juniper amended two places and I have taken both. The gateway track runs in parallel.

1. **Freeze the present.** Golden prints of every lens in the lab sessions, including Sable's probe lenses, plus the L1 to L8 checks as a test suite. Everything after must reproduce the prints except for intended changes. **1b. Atomic batches now**, with mint placeholders: a `;` line applies whole or not at all. **1c. Gestures may not call scripts or rules** until proposals preview the full cascade (Juniper, from A4).
2. **The read-set accessor**, the evaluator's only way into the world, logging aspect reads and membership reads. This is the seam the staging is cut along, and it closes the `worktrees` purity hole.
3. **The resolve and check stages** with the table-driven parse: scope rules N1 to N6, selection terms included, the lint as the check stage, refusal text generated from the grammar, `$n` retired for `$count`.
4. **Lower and evaluate by the six kinds, with a printer by kind.** Re-run the measures: C2 should read 6, C3 "parse table only". Golden prints must match.
5. **Expressions inside `derive`**: operators with units, total `if` with a dynamic read-set, nesting lowered to printed steps, value tests in `only when`, and the `split` allocation operator with its conservation check. **5b. Timelines and `at`** as the first library entries, moved here from last (Juniper): the budget's fifth step cannot pass without them. The deciding test is the household budget, both halves.
6. **Full proposal semantics** on the gateway track: rows from one input state, coalesce or refuse, preview, the rule cascade to a printed fixpoint, named viewer effects. Must land before any new gesture; a drop is a proposal.
7. **The library and definitions as world data**: `define` in notes tagged `lib`; the domain words move out of core; `from <lens>` for reuse; rules, scripts, clock and style become world data; the last-good cache is removed; row sources split as in 2.5.
8. **The painter**: carry and drop and continuity first, because they protect people's work; the viewer store for per-viewer state; then `path`, `image` and `grid` with one chart lens as the test.
9. **Behavior definitions** on the same IR.

What would change the team's mind, stated by Pike and kept: if staging leaves C1 above 20 lines per word, the IR is the wrong cut; if the budget needs state carried between evaluations inside a view, the view/behavior boundary is wrong; if people routinely want to name intermediates from outside, the naming rule should become syntax again.

---

## 6. Alex's questions, answered

**Why were we against `if`?** Because the rule was protecting three properties without naming them: printed absence, one meaning per gesture, declared inputs. Named, they admit `if` and forbid only its silent forms. The "fifth non-date interpretation" tripwire was a proxy for linear growth, and the questionable decision sat one level up, in refusing arithmetic. The budget shows arithmetic and a default are the first things everyday quantities need.

**The case against nesting.** It is not readability, since the compiler prints every step. It is that unnamed intermediates can only be pointed at by position, and position is the pointer that fails silently. So nest freely, and name what you will talk about.

**Are we heading for a worse JavaScript?** We were, on two routes. The first was the language side: variables, loops, conditionals, calls and handlers, each specified only by a branch in `make()`, with scope bugs as the symptom. The written grammar, the resolve stage and the staged compiler close that route, and C1 to C3 measure whether it stays closed. The second route is open today and is the round's main finding: scripts and rules, outside history, reachable from a click, acting on things the click never named. Steps 1c, 6 and 7 close it, and T3 measures it.

**What prevents it** is not weakness. It is the five properties: no ambient reads (L1, L3), no ambient writes (L4), no hidden state (L3, L5, the viewer store), no silent failure (L6, L7, T7), no unbounded evaluation (L7). A feature that keeps them is admissible.

**What a lens gives that a small JavaScript app does not.** From the user's side, Juniper's four, each with the condition that makes it true: you can read what you are looking at and why (condition: no silent values); your stuff outlives the view, as the trip did when its calendar was removed (condition: no computing in data); the view is yours to change like a note, undone, forked, copied (condition: the program must not escape into scripts and rules the note cannot show); what a click will do is written next to it and refused if the world moved (condition: the full effect is previewed). From the compiler's side, Pike's four: every lens has a free text rendering to diff, so golden tests cost nothing; the compiler can refuse before running; the fence knows exactly what each gesture read; the agent edits a view with the same verbs it uses on a note.

And the honest cost today, which the proposition is built to remove: a ten-line JavaScript app splits the October bills correctly, and the lens does not.

---

## 7. Decisions that are Alex's

1. **Replace the growth rule with the properties.** Retire "no if, no arithmetic" and the painter's line budget. Adopt L1 to L8, C1 to C10 and T1 to T7 as the definition of the right side, with their failing values as the stop condition. Recommended.
2. **One expression language, two contexts**, with no separate evaluator. The alternative is Astra's evaluator as a second system beside the lens, which the team rejects as a second grammar to print, fence and teach. Recommended: one.
3. **Forbid gestures from calling scripts and rules now** (step 1c), before proposals exist. This removes a capability people have used. The team's view is that it is the worse-JavaScript route and should close first. Recommended.
4. **Viewer effects outside the world** (clipboard, opening a portal). Sable admits them as named, printed, non-replayed viewer effects from a closed host list. The alternative is to keep them outside the language altogether. Recommended: admit, with the closed list.
5. **Timeline conventions.** The end of a segment is exclusive and a missing end is open-ended; the split policy is named and printed. These are the two declarations that changed the budget's numbers. Recommended as stated.
6. **Where allocation lives.** Pike: a core `split` operator that always prints its check. Sable: library allocation words plus a `check` word. Recommended: Pike's operator, with Sable's `check` word for other derivations over a whole.
7. **The redact operation.** Sable flags that the Constitution's right to have one's history deleted conflicts with immutable operations, and proposes a redact that keeps the operation skeleton and removes the values. Kernel scope, not this round's; it needs a decision on whether to design it now.

---

## 8. Open after the round

- A2 has no check but the task suite. That is a limit of every language and should be said so.
- F2, the one-year span cap, becomes a library policy and is still unstated.
- The `actors` row source reads other viewers' positions; Sable says they must become world facts or printed per-viewer drift. Neither is designed yet.
- Read-your-own-write inside a gesture is given up. The budget did not need it. A task that does is the trigger to revisit.
