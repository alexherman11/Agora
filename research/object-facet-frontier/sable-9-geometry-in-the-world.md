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
