# Pike 6: a compiler and painter that grow sublinearly

Round six, 24 September 2026. This is a proposition for Alex, from the compiler and painter seat. Labels: **[ran]** means executed. **[source]** means read in `scene.py` (796 lines) and `lens.js` (123 lines) at `aceebc9`. **[imagined]** means design or estimate. I read HANDOFF-lens-language.md in full, plus wren-11 for the ratio and the decoration rule.

The measures below are produced by `experiments/growth/measure.py`, which reads git history and source without writing anything. The lowering examples are produced by `experiments/growth/lower.py`, a 90-line sketch that is not the lab compiler. Both scripts run with the lab's pinned interpreter.

## 1. What the growth is today [ran]

| Commit | Date | scene.py lines | Word branches in `parse()` | `make()` lines | Word branches in `make()` |
|---|---|---|---|---|---|
| b49be13 (v0) | 09-18 | 191 | 8 | 24 | 4 |
| c411e34 | 09-18 | 452 | 11 | 66 | 7 |
| fa8a2ed (my binding words) | 09-23 | 788 | 15 | 169 | 12 |
| aceebc9 (now) | 09-23 | 796 | 15 | 175 | 12 |

Alex's diagnosis is right, and it can be measured. From v0 to now, 7 words cost 605 lines, about 86 per word. `make()` alone grew about 22 lines per word. That growth is not the words being complicated. It is the shape of the code:

- **Every word touches three places.** `measure.py` M3 finds each word's fields in `parse`, in `make` and in the text printer. For `layout`, `role`, `text`, `clamp`, `at`, `only` and `on`, they are also in the painter. A word is a branch in each.
- **`make()` does five jobs in one function.** It resolves names (`the`, `of`, `_named`), evaluates (`derive`, template fill), fences (`reads`, `bind`, `rev`), keys occurrences, and builds nodes. So every new word interleaves with every old one.
- **There are three repeat paths plus two `over` paths:** row sources, ids one by one, selections, derived rows and plain lists. They are the same idea written five times.

Property checks that already pass:

- The compiler never writes the world: no event or apply call in `scene.py`.
- The painter names no role, kind or lens (0 matches).
- The painter makes exactly one element per scene node, which is Wren's ratio at 1.0.
- Every visibly painted field is printed.

Two gaps:

- **The compiler keeps one piece of hidden state,** `desk._lens_good`, the last text that compiled. It changes what a scene shows and is not a world fact.
- **Occurrence keys are painted as `data-key` but never printed,** so an agent cannot name "this card".

## 2. The compiler as stages, so a word is a table entry

The shape I propose:

```
parse ─► resolve ─► check ─► lower ─► evaluate ─► print (text)  ─► scene (painter)
 table    scopes     rules    to IR    6 kinds      by IR kind      by paint kind
```

The **core IR has six kinds**. Every current word lowers to them:

| IR kind | Meaning | Current words that lower to it |
|---|---|---|
| `bind one` / `bind many` | make a thing, or each of a sequence, the current frame | `the`; `of` (selections, ids, row sources); `over`; `each` |
| `let` | name a value computed from inputs by an operator or interpretation | `derive`; `capture` (a literal with a source); template reads; `spread`; `at item` (box = frame x,y,w,h) |
| `guard` | build the part only if a test holds; otherwise print the absence and the test | `only when` |
| `emit` | a scene node with paint properties | `column row free`, `role`, `text`, `clamp` |
| `act` | a gesture bound to a command template, with its read set | `on click/edit/drag do` |
| `place` | put another definition here | `lens`; later `from` |

What each stage owns:

- **Parse** becomes a table. Each surface word declares its argument shape (selection, template, name, number, call, command) and the lowering that produces IR. A new surface word is one row, plus a lowering rule of a few lines.
- **Resolve and check** own the names (section 3). They also own the static refusals: layout constraints, gestures the painter declares it supports, cycles, budgets. They run before anything is evaluated.
- **Evaluate** knows six kinds, not sixteen words. Operators and interpretations are **tables** of pure functions.
- **Print** walks the IR, not the surface. It prints:
  - `bind` as its state (live, empty, ambiguous, unplaced, gone);
  - `let` as `name = op(inputs) = result`;
  - `guard` as its test, inputs and branch;
  - `act` as its filled line.
  
  So the printer never learns a new word. That fixes the "three places per word" problem at its root.

**Core versus library.**

- **Core** is fixed: the six IR kinds; the operator table, which is per value type and not per domain (arithmetic, comparison, date arithmetic with units, `weekday`, `round`, and the aggregates `running` and `split`); the selection language (the desk's own); and the row sources that expose kernel nouns (section 10).
- **Library** is written in lens, in notes tagged `lib`: `define day-n(date, n) = date + days(n - 1)`. The same applies to `days-from`, `week-of`, `spread`, and later `every`, `pick`, and shapes such as bars and arrows.

When a library word is used, the scene prints `day-n(2026-10-10, 2) = 2026-10-11 · lib day-n r2`, with its steps when asked. Most future growth should land in the library, where it costs the compiler nothing.

**Estimate [imagined].** A staged core of roughly 650 to 750 lines, about the size of today's file. Its marginal cost per new surface word is a lowering of 3 to 10 lines, and 0 for a library word.

## 3. Scope and namespaces, written down

```
ref      := '$' name ( '.' field )?          name, field := [a-z][a-z0-9_-]*
lookup, innermost first:
  1. lets      names made by `derive` in this part or an ancestor (lexical)
  2. frames    names made by `as`, and `it` for the nearest `bind many` without `as`
  3. thing     the current thing's fields: title text kind due tags id item, then its props
  4. host      me today session count
reserved   title text kind due tags id item it count me today session
```

- **R1.** A `derive` or `as` may not shadow a visible name. The refusal names the earlier binder and its line. (Today we get "that name is taken" without saying by what.)
- **R2.** A prop whose name is reserved is read as `$props.<name>`. This was the Python keyword-argument crash on a prop named `n` that lost four writes; it becomes a rule instead of a crash.
- **R3.** `$count` is the size of the nearest enclosing `bind many`, including inside its own instances (Juniper's A6: `"$n days here"` painted " days here"), and `$x.count` is the size of a named one. **`$n` is retired**, because it collides with the prop `n` and with the row field `$it.n`. It gets one alias period that prints a note.
- **R4.** `as` names what its part binds: on `bind one`, the thing; on `bind many`, *each instance*; on a part that binds nothing, it is refused. [ran, round four] I wrote `over $days, as day` and the compiler named the *trip*, printing `(no day.date on s31)`. It was visible, but the meaning was not what anyone would guess.
- **R5.** `$item` is the occurrence handle, the appearance a gesture acts on. `$id` is the referent. `$it` is a frame, never a thing. (That was my `$item` against `$it` confusion in round two.)
- **R6.** Every reference resolves at check time to a let, a frame, a thing field or a host fact. The one exception is prop reads, which resolve at evaluation and print `(no x)` when missing.
- **Occurrence key** = `parent-key / part-name [ / source-key ] [ #k ]`. The source key is a referent id, or the key field a row source declares: `n` for days, the value for tags, the heading slug for sections until text has anchors, and the anchor id after. The text printer prints the key.

## 4. Nesting and `if`, argued

### Nesting

**I accept the handoff's lowering, with one refinement.** `lower.py` [ran] takes Juniper's course due date, which she had to store by hand as `off=45` [juniper-3] because the lens could not compute it, and writes it as one nested derive:

```
derive dd = start + days(7 * (week - 1) + 2 + (7 if week >= breakweek else 0))
  dd.1 = week 6 - 1 = 5
  dd.2 = 7 × dd.1 = 35
  dd.3 = dd.2 + 2 = 37
  dd.4 = week 6 >= breakweek 4 = True
  dd.5 = if dd.4 → then 7 = 7
  dd.6 = dd.3 + dd.5 = 44
  dd.7 = days(dd.6) = 44d
dd = start 2027-03-29 + dd.7 = 2027-05-12
```

That is the date Juniper computed by hand. The difference is that when the break moves, it follows, and the print shows which branch the break took. So nesting costs nothing in *printing*: the compiler names every intermediate by its place in the definition (`dd.3`) and prints it.

**The refinement.** Intermediates named by position are printable, but they are **not addressable**. `dd.3` changes meaning when someone edits the expression. It is a list-position key inside a definition, the same failure as round one's `secs/0`. That is harmless for reading, because definition edits are fenced (defpart, pike-4). It is fatal for anything that must name the value from outside: a capture, a comment ("why +2?"), a fence entry, a `reads` query.

So my round-five rule, one operator per derive, is withdrawn as a *syntax* rule and restated as a **naming rule**: *anything referred to from outside a derive must be a named derive.* Nest freely; name what you will talk about. A print budget replaces the step cap: if a derive lowers to more than 8 steps, the scene prints a notice that it would read better with named parts. That is advice, not a refusal.

### `if`

**`if` is admissible.** The old "no if" rule was protecting three properties, and `if` can keep all three:

1. **Printed absence.** An `if` without an `else` makes a value that silently does not exist. So a value `if` must be **total** (it must have an `else`). It prints its test, its inputs and the branch taken. From `lower.py`:

   ```
   status = if done False → else status.2 = late,  with  status.1 = due 2026-10-02 < today 2026-10-03 = True
   ```
   
   A structural `if` is `only when`, which already prints absence. It should accept value tests (`only when $wd = Mon`), which today are accepted and meaningless. Juniper found `(absent: not $wd=Mon)` on all 75 days.
2. **One meaning per gesture.** A gesture's command line **may not branch**. What the painter sends must be what the scene printed. Choose between two gestures with two guarded parts, each with its own line. The guard's inputs join the gesture's read set, so the fence sees them.
3. **Declared inputs.** An `if` on `today` makes the view depend on the clock. `today` is a host fact in the lookup (section 3): it is read, printed and refreshed, never hidden.

**What stays refused:**
- `if` with effects (a lens has none);
- recursion in `define` (evaluation must terminate; the check rejects cycles, as it does for `lens`);
- loops other than `bind many` over a finite source.

**My line in the sand, revised.** No *evaluator* separate from this IR, ever. Lenses and behavior definitions share one expression IR. What differs between them is the context: a lens is pure, and a behavior produces proposals, in Astra's semantics, for Sable to specify. The trigger I would watch is no longer "an `if` or five steps". It is **a derivation that needs state carried between evaluations** (an accumulator across time, not across a list). That is where a view language ends and a behavior language begins.

## 5. How we know we are on the right side (compiler and painter measures)

All are executable now unless marked. "Fails" is the value that should stop the build and bring the design back to Alex.

| # | Measure | How | Today | Fails when |
|---|---|---|---|---|
| C1 | Core lines per new word | `measure.py` history | about 86 per word (v0 to now) | after staging, the median of the next five words exceeds 20 core lines |
| C2 | Word branches in the evaluator | `measure.py` M2 | 12 in `make()` | more than the IR kinds (6), or any increase caused by a new word |
| C3 | Places a new word touches | M3 | parse + make + printer (+ painter for 7 words) | a new word needs a printer or painter edit |
| C4 | Print ≥ paint | M4, plus Iris's `lens-agreement.js` in a browser | pass for visible fields; keys unprinted | any painted field or element with no text counterpart |
| C5 | Hidden compiler state | M5 | 1 (`_lens_good`) | any state that changes output and is not derivable from the world plus printed viewer observations |
| C6 | Painted elements per scene node (Wren) | M6 static; browser count [not run] | 1.0 | a part paints more than 3 elements without a printed summary, or a native paints 1:N |
| C7 | The painter knows no app | grep `lens.js` for role, kind and lens names | 0 | 1 or more |
| C8 | Core words per new task | Juniper's runs | trip: 7 words; three tasks: 7 interpretations + 4 abilities | once the library exists, more than 1 in 5 new everyday tasks needs a *core* change (an IR kind or operator) rather than a library `define` |
| C9 | Lens against the code it replaces | line counts | notes lens 11 : 523 `notes.js`; Wren's desktop 16 : 356 | a lens longer than a fifth of the JS it replaces, or a word whose print is longer than its paint (Wren) |
| C10 | Evaluation terminates and is bounded | check stage | node budget 1500; no recursion | any lens that can loop or recurse past the check |

C1 to C3 are the direct test of Alex's "not linearly": they should flatten *after* staging, and they are measured per commit, so the trend is visible.

## 6. The painter: primitives, not shapes

**Today [source]:** one element kind (a `div`) with layout (`column`, `row`, `free`), a role class, an absolute box, text with clamp, and three gestures.

I propose the painter grow by **paint primitives**, each printed:

| Primitive | What it adds | How it prints |
|---|---|---|
| `frame` | layouts incl. a `grid`, clip, scroll, transform | as today |
| `text run` | text (later with anchored ranges for comments) | as today |
| `path` | points or segments in the frame's space, stroke and fill by role | `path [series] 12 points, bbox 0,12–330,40, from let pts` |
| `image` | a world image subject | by reference |

Shapes, charts, arrows and routes are **library lenses** that emit `path` from `let` values. They are never painter code. Estimate [imagined]: path about 15 lines (one SVG element per node, so the ratio stays 1.0), image about 5, grid, clip and transform about 8.

**Gestures are interaction primitives**, again not per app: press, edit, drag and carry/drop (pike-3). Each has a keyboard path and is written once. Continuity is generic and keyed by occurrence (pike-4):
- the per-part definition hash on every gesture;
- a draft kept on refusal;
- the pending scene held while a draft is open.

**Total estimate:** 123 + about 30 (primitives) + about 16 (carry/drop) + about 11 (continuity) = **about 180 lines**, and it grows by primitive, never by shape, role or app (C7).

## 7. "A worse JavaScript?" from this seat

A worse JavaScript is a language whose programs you can understand only by running them in your head, whose meaning is its implementation. The lens was drifting there. It had the skeleton of a language (variables, loops, conditionals, calls, handlers) with each feature specified only by a branch in `make()`, and its bugs were scope bugs.

What prevents that is not refusing arithmetic or `if`:

- **A written grammar with static name resolution** (section 3).
- **A small IR whose every evaluation step prints itself.** The scene explains its own computation in text, which JavaScript cannot do.
- **Effects only as fenced, printed desk commands.**
- **No hidden state** (C5).

What would make it a worse JavaScript anyway: a script or native escape that paints without printing (C6), per-word special cases (C1 to C3), and caches that change output (C5).

What lenses give that JavaScript does not:
- **Every lens has a free text rendering to diff.** Golden tests cost nothing.
- **The compiler can refuse before running.**
- **The fence knows exactly what each gesture read.**
- **The agent edits a view with the same verbs it uses on a note.**

## 8. Build order, reconciled with Sable's (sable-6 §5)

1. **Freeze the present.** Take golden prints of every lens in the lab sessions, including Sable's probe lenses in f120, as a test. Every later step must reproduce them except for intended changes. Sable's order has no such step, and a refactor without one is blind.
1b. **Atomic `;` now, beside the golden prints** (Sable R4 minimum, Juniper's failure atomicity). A batch applies whole or not at all, on the gateway, with placeholders for read-your-own-write. The full proposal semantics can follow on the parallel track.
2. **The read-set accessor (Sable R3).** The evaluator reaches the world only through it. This is the seam the staging is cut along.
3. **The resolve stage and a table-driven parse (R6, my section 3).** The refusal vocabulary is generated from the grammar table. `$n` is retired.
4. **Lower and evaluate by the six IR kinds, with a printer by IR kind.** Re-run `measure.py`: C2 should read 6, and C3 should read "parse table only".
5. **Expressions inside `derive`:** operators with units, total `if` with a dynamic read-set, nesting lowered to printed steps, and value tests in `only when`. The deciding test is Juniper's household budget.
6. **Proposals replacing `;` (Sable R4).** This is a gateway change on a parallel track. It does not block steps 2 to 5, but it must land before any new gesture: a drop is a proposal.
7. **The library and definitions as world data (R5):**
   - `define` in notes tagged `lib`;
   - `day-n`, `days-from`, `week-of` and `spread` move out of core;
   - `from <lens>`;
   - rules, scripts and style become world data;
   - `_lens_good` is removed:
     - a lens edit that fails check is refused at write time, so the current revision always compiles;
     - a lens broken by a *dependency* (an inner lens, a library `define`) shows the latest revision of its closure that checks, derivable from history;
     - the only "last good scene" is the frame the painter already holds, printed as a viewer observation with gestures off, which is where the never-discard-draft rule keeps the draft.
8. **The painter:**
   - carry/drop and continuity first;
   - then `path`, `image` and `grid`, with one chart lens as the test.
9. **Sable's timeline and `at` as library, then behavior definitions** on the same expression IR.

**Where the two orders differ:**
- I add golden prints first.
- Atomic `;` goes first (1b), since it is small and the current gesture path already has the half-applied batch. The full proposal semantics goes on a parallel track, and it must land before any new gesture.

## 9. Folding in Sable 6

- **R3, the read-set accessor.** Accepted. It is the evaluator's only way to the world, and its log feeds the printer, the gesture fence and incremental recompiling. That makes it the runtime half of "sublinear", beside my source-side C1 to C3. One addition: the accessor must log **membership reads** as well as `(r, a)@rev`. A `bind many` over `tag:day` has read "the set matching `tag:day` at world position N". Without that, a newly tagged thing would not invalidate the scene. My C5 (hidden state) is, as Sable says, a corollary of R3's perturbation test.
- **R6, total name resolution.** Accepted. My R1 to R6 in section 3 are its rules. Sable's probe 7 shows why the parse table must also generate the refusal text: the `if` refusal lists 11 words and omits 7. Probe 6 (a prop `n` silently shadowing `$n`) is fixed by my R2 and R3.
- **`if`.** Accepted. The read-set is the test's inputs plus the branch taken, recorded dynamically. Both branches are name-resolved at compile time, and the print shows `(not taken: …)`. In a gesture, the guard's inputs join the fence as before.
- **Nesting.** Accepted, in the same form. Steps are keyed `(definition, part path, let-name)`, so only named steps are addressable. A capture or comment on an unnamed step is refused with "name it first". My one-operator rule is now a printing rule.

**What would change my mind.**
- If staging leaves C1 above 20 lines per word, the IR is the wrong cut.
- If Juniper's household budget needs state carried between evaluations *inside a view*, the view/behavior boundary is in the wrong place.
- If people routinely want to name intermediates from outside, the naming rule should become syntax again.

**Addendum: timelines (Sable's valid time).** A timeline read lowers to the existing kinds. `at <date>` is a library `define`: a `bind one` over the aspect's segments, filtered on `start <= d < end`. It inherits `the`'s states for free: a gap prints `(empty)`, and an overlap prints `(ambiguous: seg3, seg7)`.

`bind many` over a timeline needs three things that today's row sources lack:
- rows keyed by the segment's element id, not by its dates, which change when edited;
- a read-set entry per segment, `(r, a, seg)@rev`, plus a membership read of the segment list;
- ordering by valid time.

Sections will need the same once text has anchors. So this is one general change to row sources, not a timeline special case.

## 10. Folding in Juniper 6

**Row sources.** I withdraw "the row sources are core". Core row sources are only those that expose **kernel nouns**:
- things (selections);
- the element-identified parts of an aspect: text blocks by anchor once text has anchors, timeline segments, list elements;
- operations (today's `events`, with an honest `n of N`, not a silent last 20);
- observers (today's `actors`).

The rest become library `define`s that transform core rows:
- `sections` groups text blocks under `##` headings. That is the document app's convention, not the host's.
- `comments:<id>` becomes a typed relation term, like `parts:`.

A row source *can* be written in lens exactly when it is a filter, group or map over core rows. It cannot when it needs a new kind of world access, because that is a new kernel noun.

`worktrees` currently loads other sessions' pickles during compilation. That breaks purity (R1) and the read set (R3). Instead, forks and merges become operations in the base world, and each worktree is a referent with aspects (name, by, journal size) kept by the worktree commands through the gateway. The compiler never opens another session.

**Bounds degrade, refusals are static.** The check stage **refuses** only what the definition alone makes wrong: an unresolved or shadowed name, a value test used as a selection, a branching gesture line, recursion. Those refusals happen at write time. Bounds that depend on **data** (node budget, span length, as in F2 and F3) **degrade**: the compiler clamps the repeat nearest the budget and prints `days (showing 1–292 of 365 · node budget 1500)`. The F3 fallback failure is a bug of shared state: each compile attempt needs its own count.

**The lint is the check stage.** Juniper's lint list maps onto the checker, not onto my C1–C10. My measures are about the host; hers are about lenses. Both are needed. One table-driven checker runs at write time, and on `check <lens|all>` in the desk, with two severities:

| Juniper's lint | Severity | Why |
|---|---|---|
| shadowed frames | refuse | R1 |
| value tests in `only when` | refuse until value guards exist, then legal | step 5 |
| `$` filling empty without a marked absence | refuse | R6 |
| gestures that run scripts or trigger rules | warn | effect not visible in the line (until R5 and proposals) |
| title bindings | warn | a name pointer (round one) |
| derives lowering past 8 steps | warn | mine |

A separate lint tool would be a second grammar, which is Sable's probe 7 again.

**Conservation.** This is a core operator producing a `let` whose value is rows, not a new IR kind: `derive shares = split $total by $days rounding cents remainder largest`. The operator itself prints the parts, the rounding rule, the sum check and where the remainder went. It is core rather than library because the sum guarantee has to be the operator's, not each author's.

**Per-viewer state (F1).** A declared viewer variable, `view tab = bills`. It is read through lookup level 4 (host and viewer facts), so it is an input V, printed as `~ alex: tab=bills`. It is written by an `act` whose target is the viewer store, not the gateway, so it is not journaled. The painter keeps the variables and sends them with each scene request (about 5 lines). R2 and R3 hold because V is an explicit, printed input. Juniper's check 5 (two viewers, one lens) is its test.
