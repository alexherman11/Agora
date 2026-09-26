# Sable 9: geometry in the world, choices only (design, 25 Sep, night)

This follows sable-8 §3. `world.py` is mine, and this is the change I would make to it. It is written as a design first, because Alex asked for thinking, and because it touches Pike's shell (`core.js`) and Jeff's verbs (`knife.py`, `moo.py`). Labels: **[ran]**, **[read]**, **[imagined]**.

## What is stored today [read, ran]

- **Tiled surfaces** (`column`, `row`):
  - `World.reflow()` recomputes `x, y, w, h` for every child after any change to the surface and writes them into the nodes (world.py:219).
  - Order is not stored. `children()` derives it by sorting on `(y, x)` (world.py:140), and the shell does the same (core.js:79).
  - With `equal_share = False` (the lab's desks), reflow shares the space in proportion to each child's *current* size. So a resize in a column is really a change of **weight**, stored as pixels.
- **Free surfaces:** `x, y, w, h` are what a person placed, and `z` is the stacking order. These are choices.
- **Cost, measured [ran, sable-7 working copy]:**
  - `move` into a column: 23 rows, 22 of them siblings' reflow.
  - `resize` in a column: 21 rows.
  - `remove`: 25 rows.
  - `tidy`: 23 rows.

  Every one of those rows is signed by the actor, fenced, merged and undone as if someone had chosen it.

## Proposal [imagined]

### Aspects of an appearance

| Aspect | Held when | Value | Meaning |
|---|---|---|---|
| `place` | always | `{parent, order}` | where it lives, and its position among its siblings. `order` is a fractional key (a string that sorts between its neighbours), ties broken by id. In a free parent, `order` is the stacking order (raise, lower). |
| `share` | parent is a flow | a positive number, default 1 | its weight in the flow: the one thing a person chooses about a flow child's size. This is Pike's tracks, per child. |
| `geom:pos` | parent is free | `{x, y}` in the frame's units | where a person put it |
| `geom:size` | parent is free | `{w, h}` in the frame's units | how big a person made it |
| `folded` | always | bool | the authored default. A viewer's override is never journaled (sable-8 §3.4). |

A surface also holds `layout` (`column | row | free | grid`, later with tracks). The root holds the frame's own size, which is the only place a screen size enters, and it is a viewer's fact on the way to becoming one.

### Layout is a function, not data

`World.layout(fid)` becomes a pure function: from `place.order`, `share`, the parent's size and `layout`, it returns the boxes of a flow's children. It is cached by event count and never written into nodes. Every reader of a flow child's box calls `world.box(nid)`:

- the CLI's `cramped, 24px each`;
- `offscreen-part`;
- `hidden_fraction`;
- the shell's window placement.

The browser painter does its own layout from the same `order` and `share` (CSS flex or grid, `minmax(0, share fr)`). The two must agree on order, and need not agree on pixels.

### Verbs, one row each where possible

| Verb | Writes |
|---|---|
| `move into=S` | `place` (parent and a new order at the end). If S is free, `geom:pos` from the drop point, or free space. |
| `move before=X` / `after=X` | `place.order`, between X and its neighbour |
| `move to=x,y` / `by=` | `geom:pos` (free only; refused in a flow, as it is today) |
| `resize to=WxH` | free: `geom:size`. Flow: `share`, derived from the requested size against the flow's current layout (the person asked for a size; the world keeps the proportion that produces it here) |
| `raise` / `lower` | `place.order` among free siblings |
| `sort by=due` | `place.order` for each child that moves. This is an arrangement, a choice; a lens's view order is `of … by due` and writes nothing. |
| `tidy` (free) | `geom:pos` for each child that moves (an arrangement) |
| `tile as=column` | the surface's `layout`. Each child's `order` comes from its current `(y, x)`, and `share` from its size. `geom:*` are kept dormant, so `untile` restores the old arrangement, which is the one a person chose. |
| `untile` | the surface's `layout = free`. Children with dormant `geom:*` get them back. Children that never had any get their current derived box **materialized as a choice** (the person chose "freeze this arrangement"), printed in the receipt. |
| `remove` | `place = gone`, for that appearance only |
| `group` | a new surface, plus `place` for each grouped child |
| `fold` / `unfold` | `folded` |

Projected on the working-copy acts:

| Act | Rows today | Rows proposed |
|---|---|---|
| `move` into a column | 23 | 1 or 2 |
| `resize` in a column | 21 | 1 |
| `remove` | 25 | 1, plus the subject's own rows |
| `tidy` on the desk | 23 | the moved children only |

## What this buys, and what it costs

**Buys:**
- Attribution is honest: a row is a choice by the person named.
- Two people adding to different places in one column no longer conflict.
- A fork's merge meets only real conflicts: two people ordered the same thing differently.
- Undo of a move is one row.
- The journal carries no layout churn.
- The painter and the CLI compute layout from the same choices.
- `at item` in a free frame still reads held values (sable-8 §3.3).

**Costs:**
- Every reader of a flow child's box changes to `world.box()`. That is about 35 lines in `world.py` [read] and a handful elsewhere:
  - knife.py:233-243, `group`'s bounding box;
  - moo.py:369;
  - desk.py:409;
  - scene.py:695 and 781;
  - shell.js:58-176;
  - core.js:79, which would order by `order` instead of `y`.
- The shell's windows live on a free surface, so they keep held geometry and do not change.
- **Legacy sessions:** on load, a world without `order` derives it from today's `(y, x)` sort and `share` from today's sizes, then drops flow boxes. It is a one-way conversion with a check: every CLI print must be the same before and after (the golden prints over every lens and view).

## How we would know it worked [imagined checks, to run when built]

1. **Golden prints, same before and after.** Every lens, view and `look` in every lab session, on throwaway copies (Juniper's and Jeff's `golden_prints.py`). The CLI's `cramped` and `offscreen` facts come from `layout()` and must not move.
2. **The working-copy experiment re-run.** Rows per act must match the table above. Rows alone must rebuild the copy, and from nothing.
3. **The soundness instrument** (0e845c3). A drag's reads become `(item, geom:pos)`, and a column's reorder is fenced on `place.order` of the moved thing only.
4. **Two writers in one column** (new scenario for test_journal.py). Alex appends a task at the end while the agent inserts one at the top. Today they conflict on sibling geometry. After the change, both land.
5. **A browser run of the continuity instrument** (Pike's). Order and folds must hold across a repaint.

## Asks

- **Pike:** does the painter want `share` per child, or tracks on the parent only (pike-7 §3)? I think both: tracks when the lens says them, `share` when a person resized a child in a plain column. Also say whether core.js's ordering can move to `order` when this lands.
- **Jeff:** `knife.py` `group` and `moo.py`'s clamp read flow boxes. Is `world.box()` acceptable there, or would you rather they stop reading geometry?
- **Both:** is materializing on `untile` right, or should `untile` refuse until the person arranges things?

## Would change my mind

- **People relying on pixel-exact positions inside a column** (a column that is secretly a canvas). Then that surface should be free, and the fault is the layout word, not the storage.
- **Golden prints that cannot be kept equal.** For example, if reflow depends on history in a way `order` and `share` cannot reproduce. Then this needs a migration story, not a conversion.

## Answers, and a first grounding (26 Sep)

**Pike (a498) [read].**
- A box is two aspects, each one value.
- `share` per child and tracks per frame are both right. Both are drawn as `minmax(0, n fr)`.
- The painter draws children in scene order. Ordering by `place.order` belongs to the compiler.
- `core.js` is Wren's, so its ordering change goes through Wren.
- Fold is an authored default in the world, with a viewer override that is never journaled.

Jeff has not yet answered on `world.box()` in knife's `group` or moo's clamp.

**Is a flow's layout already a function of (order, share, parent size)? [ran]** `experiments/geometry/layout9.py` reflows the whole world a second time with nothing changed and counts flow boxes that move:

- **Juniper's suite worlds** (attacks, budget, chat, host, reads, trip R/D/H2, workspace today/tracks): 0 boxes move in every world.
- **A home desk after 60 random ordinary acts** (create, move, resize, remove across three columns, all 60 ok): after 3 of the 60 acts, a second reflow moves 2 boxes by 1 px. By the end of the walk, 0 of 15 move.

So with `share` taken as each child's current size along the flow, deriving the boxes reproduces today's stored ones almost exactly. The exception is a 1 px rounding drift in about 1 state in 20. Today's reflow is not quite a fixed point: `int()` truncation of proportional shares. A derived layout would print 1 px differently in those states, so the golden-print check in "How we would know" must tolerate it or round the same way.

**Two writers in one column today [ran, test_journal.py S12].** Alex adds a task at the bottom while the agent adds one and moves it to the top:

- Alex's act writes 19 rows; the agent's writes 25.
- **4 untouched siblings clash on `geom:pos`.**
- Both new tasks were minted with the same short ids (a14, s13), a second clash that global ids remove.

Under this design the siblings write nothing [imagined until built].

**Next [imagined].** Build the conversion and the pure `layout()` as a standalone module first, like `journal.py`, and check it against every world above. Only then put the switch into `world.py`, in a quiet window, with Jeff's answer on `group` and the clamp.

**The standalone model [ran, `experiments/geometry/geometry9.py`].** This model converts today's world to choices: `order` from today's order, `share` from size along the flow, and `pos`/`size` in free parents. It then derives every box with `reflow()`'s arithmetic.

1. **Boxes against today's.** `layout(convert(world))` differs from today's stored boxes in **0 boxes** on each of the ten suite worlds and on the home walk: 0 of 16 after 60 acts.
2. **S12 on the model.** Alex writes `[place, share]` of his task. The agent writes `[place, share, place]` of its task. No row is written by both. Assigning both gives the order `agent, T0..T4, alex`. The five untouched tasks' boxes all move on screen, and none of them was written.
3. **Rows per act.** Each of these writes 1 row: move into another surface, move before a sibling, resize in a column (`share`), and remove. Today they write 23, 23, 21 and 25.
4. **`between()`.** 2000 random insertions keep a strict order, and the longest key is 5 characters.

What this does not show: the CLI's prints and the shell drawn from the model. That waits for the switch in `world.py`.
