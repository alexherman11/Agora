# Sable 8: what the staged compiler means, and what geometry is (25 Sep, night)

Alex's redirect: the team's effort goes to the staged compiler and to drawing. Jeff asked me for two things:

- the semantics of Pike's IR as a formal statement to build against;
- the kernel side of drawing.

Labels: **[ran]** means a probe or an experiment produced the result. **[read]** means it comes from `scene.py` at bda4cfe..53736f4 or from pike-6/pike-7. **[imagined]** means it is a proposal. §5 lists the changes to the compiler's shape.

## 1. The statement

A lens `L` is a set of part definitions. A scene is

```
(scene, R) = eval(L, A_W, H)
```

- `A_W` is the **read accessor** over the world `W` at one read point (today, an event count; later, a journal seq).
- `H` is the host facts actually used: `me`, `today`, `session`.
- `R` is the **read set**: every access made through `A_W`.

Viewer state is not an input to `eval`. It is an input to painting, `paint(scene, viewer)` (pike-7 §1), and to printing, as `~` lines.

**Determinism (R2).** `eval` is a function. The same `L`, the same answers from `A_W` and the same `H` give the same scene, byte for byte in print and paint. Nothing else may reach it: no wall clock, no randomness, no container order, and no compiler memory.

**Read-set soundness (R3).** For every world `W'` whose accessor gives the same answers as `W` on every entry of `R`, and the same `H`:

```
eval(L, A_W', H) = eval(L, A_W, H)
```

`R` is a sufficient statistic of the world for this scene. Tightness, meaning that `R` is small, is measured and not required.

**Per-gesture soundness.** For each act `g`, `R_g ⊆ R`. If no entry of `R_g` changed, then `g`'s filled line and its guards are unchanged. This is what makes "the gesture means what was printed" checkable by the fence without re-running the lens.

**The accessor is the seam.** It is the only door from evaluation to the world. It answers six questions and records each in `R`:

| Call | Answers | Recorded as |
|---|---|---|
| `value(r, a)` | the value of aspect `a` of `r`, or ABSENT | `(r, a)` |
| `select(q)` | the referents matching selection `q`, in a **defined order** | `(q, [ids in order])`, a membership read |
| `occurs(r)` | `r`'s appearances, or unplaced, or gone | `(r, occurrences)` |
| `rows(src, r)` | rows derived from one aspect (`sections:<id>` from `(id, text)`) | the underlying `(r, a)` |
| `define(name)` | the definition a name resolves to (a lens, a library `define`): one, none or ambiguous | `(name → id, code at rev)` |
| `host(f)` | `me`, `today`, `session` | `(host, f)` |

- **ABSENT** is a third value, distinct from `""` and from false (R6). Every printer shows it as `(no x)`.
- **Order** is part of the contract. `select` orders by a stable key of the referent (its mint order), or by a declared `by`. Never by dict insertion order, which today differs after a merge or a rebuild.

**Stages and what each may touch:**

| Stage | Input → output | May read the world? |
|---|---|---|
| parse | text → AST (table of words) | no |
| resolve | AST → every `$name` bound to a let, frame, field, host fact or gesture slot; `lens`/`define` names looked up | only `define()` through the accessor (definitions are world data, R5) |
| check | resolved AST + the painter's declared capabilities → refusals (layout, cycles, budgets, gesture shapes, shadowing) | no |
| lower | → IR: a tree of the six kinds, with **dependency edges** from each act, guard and emit to the lets, frames and fields it uses | no |
| evaluate | IR × accessor × host → scene + R | only through the accessor |
| print, paint | scene (+ viewer) → text; → drawn elements | no (the painter gets viewer state; the printer gets viewer observations for `~`) |

## 2. The six kinds, one by one

Notation:
- `Γ` is the environment: frames, lets, the current thing `t`, the host facts, and `count`.
- `K` is the occurrence key of the node being built.

Evaluation is depth-first and in pre-order. Siblings go in declaration order and instances in source order. **Within one part** the order is fixed: bind, then lets (in declaration order), then guard, then emit, then acts, then the repeat's instances, then the placed lens, then the fixed children.

**bind one** (`the q [as f]`, or `of id,id` naming exactly one).
- Evaluates `S = select(fill(q, Γ))`, and for named ids `occurs(id)` each.
- The state is `live` if `|S| = 1`. Otherwise it is `empty`, `ambiguous(S)`, `gone` or `unplaced`. When live, `t := S[0]`, and `f := t` if `as` is given.
- When not live, the node is a text leaf carrying state and why. Nothing below it is evaluated, and it has no acts.
- **Reads:** the membership read `(q, S)`, the whole result and not just the chosen one. A new match anywhere turns live into ambiguous.

**bind many** (`of q | of src:r | over $let`, `each P`, `[as f]`, `[clamp k]`).
- The source is one of three:
  - `select(q)`: membership read `(q, ordered ids)`;
  - `rows(src, r)`: reads the source aspect;
  - a list let: reads nothing new, because its inputs were recorded at the let.
- For each element `e_i`, instance `i` evaluates `P` with `Γ_i = Γ + {t := e_i, f := e_i, count := n}` under key `K/okey(e_i)`. `okey` is the element's identity: a referent id, the row's key field, or the derived value. A repeat within one parent gets `#k`.
- **`count` is the true size `n`.** `clamp k` limits the instances built and prints how many are cut. It never changes `count`.
  - [ran] Today, `$count` under `clamp 1` printed "A of 1" while 4 existed, because `count = min(total, keep)` [read].

**let** (`derive name = expr`).
- A pure, total function of values in `Γ`. A missing input or a type error gives the value `uninterpretable(why)`, which prints and behaves as ABSENT downstream.
- Prop inputs are `value(t, prop:k)` reads. Nothing else is read.
- A nested expression lowers to a chain of positional intermediates (`dd.3`). They are printable and not addressable. Anything named from outside must be a named let (pike-6 §4).
- **Scope:** lexical. It is visible to its part and to the part's descendants. It may not shadow a visible name, and the refusal names the earlier binder.
- **Operators** come from a table, pure per value type. `today` enters only as `host(today)`.

**guard** (`only when q`, or `only when $x op v`).
- Judged **after the part's own bind and lets**, against the part's own frame. Three-valued:
  - **true**: build the part.
  - **false**: an absence node with why `$x is A, not = B`.
  - **absent**: an absence node with why `no x`.
- A selection guard with a current thing tests `t ∈ select(q)`. Only `t`'s aspects that `q`'s terms name are read (`tag:y` reads `(t, tag:y)`; `in:f04` reads `(t, place)` up the chain). A selection guard with no current thing is a membership read.
- The guard node stays in the scene with `absent` (pike-7 §6), so siblings do not move when it flips.
- Every input of every guard on an act's chain joins that act's `R_g`.
- **[ran] Today the two guard forms judge different things.**
  - In `p : the tag:x, only when tag:y`, the selection guard runs before the part's `the` and tests the parent. It printed `p a03 "sel guard: A"` for a note tagged only x.
  - In `q : the tag:x, only when $title = B`, the value test runs after, against A, and printed absent.
  - One rule is needed. I propose the one above: a guard judges the part's own frame. The golden prints will show which lenses change.

**emit** (layout, role, `text`, `clamp`; frame or leaf).
- The node is a frame or a leaf, never both (pike-7 §4).
- Text fills from `Γ` and `value(t, prop:k)`. A missing prop is ABSENT, printed `(no k)`, and drawn as nothing.
- `emit` reads only what its template's dependency edges name.
- A box exists only for a child of a `free` frame, and comes from `at item` (§3). Every other box is the painter's business.

**act** (`on press|edit|drag|carry|drop do line`).
- The line is a **template filled at evaluation** from `Γ`. It keeps holes that only the painter fills (`$x $y $value $carried`), and it does not branch.
- Its fence is `{defpart: hash of its binding chain, reads: R_g}`, where

  ```
  R_g = reads(deps(line)) ∪ reads(deps(guards on its chain)) ∪ {occurs(t)}
  ```

  and `deps` comes from the IR's dependency edges, not from whatever a tracker happened to see.

  **Amended [ran], the same night:** add the **binds on its chain**. That means the membership read `(q, S)` of every `bind one` above the act, and for every `bind many` above it, the instance's membership condition: `t`'s aspects that `q`'s terms name, or the membership read when `q` has no current thing. The corrected formula:

  ```
  R_g = reads(deps(line)) ∪ reads(deps(guards on its chain)) ∪ reads(binds on its chain) ∪ {occurs(t)}
  ```

  - **Evidence.** `experiments/soundness/soundness.py` builds worlds from the suite and from Juniper 7's two apps as they run today. It applies 900 single edits by another actor and watches every painted gesture. There were **21 unsound cases, all of these two kinds.** The line never changed; the gesture **disappeared** while its fence reads were untouched.
    - A task's `owner` changed, so it left `of kind:task,prop:owner=juniper,...`. Its retitle and check gestures were gone, but their reads were `[[s02, title]]` only.
    - A second note matching `title:Charter` made `the kind:note,title:Charter` ambiguous, and every gesture under it vanished.
  - **Harm.** deskd would accept such a gesture [read, deskd.py 178-230: it checks the item and the reads, never the chain's membership]. "Mark done" would land on a task that is no longer the person's.
  - **Tightness.** 36 of 62 touched trials left the gesture unchanged. Mostly these are reads with an empty aspect list, which the fence treats as "everything".
- An act's effect is a **proposal**. The gateway runs the line and its cascade and returns rows (jeff-1, sable-7). The compiler does not preview effects; it guarantees the line.
- An act may target only a **held** aspect (§3.3).

**place** (`lens name [with $a $b]`).
- `define(name)` is a definition read.
- The placed lens is evaluated inline under `K/lens:name` with a **fresh** `Γ`, containing only the values passed by `with`. Nothing lexical leaks in, which is hygiene.
- A literal name is checked for cycles statically. A templated name (`lens $x`, which today's grammar admits [read]) is resolved at evaluation with a runtime stack check.
- **Fallback.** "Show the last version that compiled" must be a **definition-version read**, `(lens, code at an earlier seq)`, not compiler memory. Today it is `desk._lens_good`, which is hidden state (C5). The frame's closure already prints `fallback, shown_rev`, so the version read is half there; the journal would make it exact.

**Termination and bounds (R7).** The IR is a finite tree. `bind many` ranges over finite sources, `place` is acyclic, and lets cannot recurse. The node budget refuses with the advice `clamp N`, and every cut prints its count.

## 3. Geometry at the kernel

### 3.1 What the world stores today [ran]

In sable-7's working-copy experiment:
- `move Groceries into=Later` wrote **23 rows**.
- `tidy f01` wrote 23 and `remove` 25.
- `resize Essay` wrote 21.

22 of the 23 rows of the move are the siblings' `x, y, w, h`, recomputed by the world's reflow of a tiled surface.

Order within a `column` is not stored at all. `children()` derives it by sorting on `(y, x)` [read, world.py:140]. So today the world **stores a layout engine's output as if it were a fact**, and encodes a chosen order in coordinates. The costs, all seen this week:
- Every reflow is a world write, signed by whoever caused it.
- Two people adding to different places in one column conflict on sibling geometry that neither chose.
- A fork's merge meets geometry conflicts nobody made.
- The journal would fill with layout churn.
- The world knows a screen, `SCREEN = 1280x800`.

### 3.2 The rule

**A world aspect is something a person or an agent chose, that must survive a reload and merge. Anything a layout computes from those choices is derived: a let or the painter's work, never stored.** Applied to appearances:

| Aspect | Held when | Value | Written by |
|---|---|---|---|
| `place` | always | `(parent, order)`. `order` is an anchor-based order key, as for text hunks: `after` fixed at insert, RGA. In a free parent the same key is the stacking order (raise and lower). | create, move, place, an arrangement act |
| `geom:pos` | parent is `free` | `(x, y)` as one value, in the **free frame's own units**, not screen pixels | a drag, `move to=` |
| `geom:size` | parent is `free` | `(w, h)` as one value, same units | a resize |
| `folded` | always, as an authored default | bool | `do fold` (a lens act or a command) |

- A child of a `column`, `row` or `grid` **has no geometry aspect**. Its box is the flow's output from the lens's tracks (pike-7 §3) and the painter's measurement of content.
- `sort` splits into two things:
  - **a view order**, `of q by due`: a lens word that writes nothing;
  - **an arrangement**, `do sort f02 by=due`: a chosen reorder that writes `order` for each child it moves.

  Both are legitimate, and they are different acts.
- `tidy` on a free surface is an arrangement. It writes `geom:pos` for what it moves, because someone chose it.
- Projected on the working-copy acts [imagined, not re-run]:
  - `move` goes from 23 rows to 1;
  - `resize` in a column from 21 to 0 (a resize is meaningless there and would be refused);
  - `remove` from 25 to 4.

**Units.** A free frame has its own coordinate space. The painter maps it to pixels with a zoom that is viewer state. Then the world does not know a screen, and one appearance drawn on a canvas and in a minimap reads the same held `geom:pos`.

### 3.3 What the painter may write back

**The painter writes nothing on its own.** It fills holes in acts the lens declared. The chrome it owns (scroll, selection, focus, the fold handle, zoom) writes only viewer state.

An act may name only a held aspect, which gives three cases:

1. **Identity.** The drawn box *is* the held value: `at item` in a free frame. `on drag do move $item to=$x,$y` writes `geom:pos`, and the drag reads `(item, geom:pos)`. It is not the subject, which is the fault Pike found in c341.
2. **Derived box.** `spread`, a flow child, or a let-computed position. There is no aspect to write. A drag here is refused at check time. This rule is already in `spread` [read], and generalizes to every derived box.
3. **Writing through a derivation.** Dragging a bar changes the amount it was drawn from. That is allowed only when the lens's line states the inverse, for example `on drag do prop $item amount=$y` with the frame's scale applied. It is printed like any line, so the effect is explicit and fenced, never inferred by the painter.

### 3.4 Pike's two questions

- **Is a free child's box one aspect or two, for a resize while it is dragged?** Two. `geom:pos` and `geom:size` are independent choices. Each is one value (a point or a size half-merged from two gestures is one nobody chose).
  - A bottom-right resize writes size.
  - A top-left resize writes both, in one batch with one undo.
  - Ann's drag and Ben's bottom-right resize both land: her position, his size. Each choice is kept, as with a title and a text.
  - Ann's drag against Ben's top-left resize meets on `pos`. The later one is refused or held, naming the other.
- **Is a fold ever a world fact?** Yes, as an **authored default** (the world aspect `folded`, above). It is joined by a **viewer override** that is never journaled.
  - The painter draws the override if there is one, otherwise the default.
  - The fold handle, which is chrome, writes the override.
  - `do fold` or a lens act `on press do fold $item` writes the default.
  - A team's shared collapsed bar is then a default. My collapsing it for myself is an override. Juniper's a319 case is the override.

### 3.5 What follows for the compiler and the scene

- `at item` reads `(item, geom:pos)` and `(item, geom:size)` through the accessor. In a flow it stays refused.
- Visibility facts (`offscreen-part`, `43% hidden by f52`, from `w.relations`) are derived from geometry.
  - Among free siblings, a lens may compute them. They are a let over the siblings' held geometry, and those reads are large, so honest.
  - For flow children, only the painter knows. They become observations (`~`), not world facts.
- **Transitions** (a Dynamic Desk open question) fall out. An element is keyed by occurrence, so when its derived box changes between two scenes, the painter may interpolate. No world data is involved, and nothing prints except the end state.

## 4. Today's evaluation against the seam [read]

These are the places where `scene.py` evaluation reaches the world outside an accessor. Each would become an accessor call or be removed:

- `desk._parse_selection`: selection, with the order being container order.
- `w.appearances_of`: occurrences.
- `w.relations`: visibility facts.
- `_rev_of`: revisions for fences, which become seqs.
- `desk._resolve`, inside `rows()`.
- `find_lens`: scans every subject. That is a definition read, and its membership is all lenses.
- `rows(actors)`: reads `desk._per`, **every person's read position**. That is viewer state entering the scene as if it were world data.
- `rows(worktrees)`: unpickles other sessions' files during evaluation.
- `desk._lens_good`: compiler memory.

## 5. What this changes in the compiler's shape (for Jeff, before the next stage)

1. **Evaluate takes `(IR, accessor, host)`, and nothing else is in scope.** The accessor records `R`, so a scene's `R` and each act's `R_g` stop being assembled by hand in `make()`.
2. **Lower emits dependency edges.** `R_g` is derived from the IR: deps of the line, plus deps of the guards on its chain, plus the occurrence. This is the static half of read-set soundness, and it can be tested without a browser.
3. **One order within a part:** bind, lets, guard, emit, acts, instances, placed lens, fixed kids. Guards judge the part's own frame. This changes lenses that use `the` together with `only when <selection>`, and the goldens will show which.
4. **ABSENT is a value.** Guards are three-valued, and `uninterpretable` behaves as ABSENT.
5. **`count` is the true size.** `clamp` prints the cut.
6. **`select` has a defined order.** It orders by mint order or a declared `by`, never container order.
7. **`place` is hygienic.** It gets a fresh `Γ` plus `with` arguments. Fallback is a definition-version read; until the journal exists it stays printed as it is, and C5 counts it.
8. **Row sources that read viewer state or other files leave evaluation.** `actors`' read positions become viewer observations. `worktrees` becomes a world row source once forks are journal data.
9. **Geometry.** The scene carries a box only from `at item` in a free frame. A drag's read is `(item, geom:pos)`. The world's stored reflow geometry is a kernel change for later, in `world.py`, which is mine. The compiler should assume flow boxes are not world data.

## 6. What would change my mind

- **A lens that needs to read viewer state to be correct.** Then viewer state enters `eval` as an input, printed per viewer, and the scene is no longer the same for everyone at one read point.
- **A real arrangement that people expect to follow content.** For example: "keep this column ordered by due, and let me drag exceptions." Then order is a derived view with held overrides, and `place.order` needs a mode.
- **Golden prints showing many lenses depend on today's guard-before-bind.** Then the order in §2 needs a word for "guard the parent", not a silent change.
- **Free-frame units that cannot be screen-independent for a real app.** For example, a pixel-exact image annotation. Then `geom` carries a unit.
