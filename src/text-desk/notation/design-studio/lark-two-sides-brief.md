# What the two-sided desk should look like: a brief for whoever builds the renderer

Lark, round three. Short, because the prototype is the argument:
**`http://localhost:8770/lark-two-sides/`**, rendered live from `explore.py proto-lark --dump`, nothing
hand-written. Read this next to it.

*(That page contains two deliberate faults, planted as a test fixture for the eyes protocol. They are named
in `lark-eyes-protocol.md`. Do not copy them.)*

---

## 1. The one claim I would defend hardest

> **The two sides are columns of one continuous surface, not two windows.**

Not two panes with their own toolbars, scrollbars, title bars and menus. One world, one header, one type
ramp, one scroll gesture, a hairline between. The reason is not aesthetics — it is that *duplicated chrome
is a lie about the world.* Two toolbars imply two applications; there is one desk with two owners. The
moment a side gets its own window furniture, every subsequent question ("which toolbar do I use for a thing
on the bench?") becomes unanswerable.

Corollary: **a bench is not a third column.** It is a mode a column enters — the edge changes, nothing moves.

## 2. What must be visible at a glance, and how

This table is the actual deliverable. The left column is what the text says; the middle is what the pixels do;
the right is **how Iris can catch the render lying**. A visual convention with no falsification test is
decoration, and decoration is where dishonesty hides.

| the text says | the render does | how to catch it lying |
|---|---|---|
| `owner=alex` | a 2px edge under the column name, one hue per owner; no badge, no border around the column | sample the hue; two columns with different owners must differ, same owner must match |
| `warm` | a 2px bar on the line's left edge, warm hue | count warm bars on screen = count of `warm` in the dump |
| `=` measured | plain text, no ornament | every `=` value in the dump appears as a literal string on screen |
| `~` described | italic, with `by <author> <day>` in a lighter grey — **the by-line is never dropped** | no italic description on screen without a visible author |
| `?` opaque | a hatched strip **with its extent written on it**, not a grey box | the extent string is legible at 100% zoom |
| `!` stale | an amber flag adjacent to the claim it marks | **contrast ratio ≥ 4.5:1** — see §4 |
| `N past the bottom` | a footer line in the column | the count on screen must equal the count actually clipped |
| `veiled · =12 inside` | the surface line renders, the contents do not, the count does | no child titles present in the DOM at all, not merely hidden |

Two rules about that table:

- **Every row is bidirectional.** A fact in the text must reach the screen, *and* a mark on the screen must
  trace back to a fact. A warm bar with no `warm` in the dump is as bad as the reverse.
- **The right-hand column is executable.** Every one of those checks is a thing a seeing agent can be asked
  to do in one request. That is the point: the render is not reviewed by taste, it is reviewed by test.

## 3. What must *not* be rendered

Easy to get wrong, because a renderer's instinct is to show everything it is given.

- **My reading head is drift, not a deed.** `(lark reading §Risks)` appears while it is true and vanishes.
  It never accumulates, never appears in a history panel, never gets a timestamp on screen.
- **Personal zoom, scroll and selection are the viewer's own.** They are never drawn on the other's screen
  and never leave the viewer's machine.
- **Veiled contents must be absent from the document, not hidden by CSS.** If the titles are in the DOM with
  `display:none`, the veil is a costume. This is the one row of the table where "how to catch it lying"
  requires reading source rather than looking.
- **Offers and deferrals belong in the margin of the thing they concern**, not in a global notification
  stack. A notification stack is how a shared desk turns into two people using an app.

## 4. The one hard number

`!` stale is the only mark whose *job* is to be noticed against the reader's wishes. Everything else can be
quiet. So it gets the only hard constraint in this brief: **contrast ratio ≥ 4.5:1 against its background,
and it may not be the only indicator** (an amber colour plus the literal character `!`).

I know this because I broke it on purpose in the prototype — rendered the flag at roughly 12% of intended
contrast — to find out whether a seeing reviewer would catch a flag that was *present and invisible*. That
failure mode is invisible to every text-level check ever written, because the DOM is correct. It is the exact
class of bug that only eyes can find, and it is the reason the studio needs eyes at all.

## 5. Where a renderer will hit the wall

Named honestly, from building the thing:

- **`prop` does not apply to surfaces in the current engine.** I could not set `owner=alex` on a side; I had
  to carry owner in the renderer's own config. That is item 1 of my day-one ledger and I had it marked
  "small". It is not free, and it is a prerequisite for everything in §2.
- **The geometry in the dump is the old fixed 1280×800 test geometry** (`x`, `y`, `w`, `h` per node). I
  ignored it entirely and laid out from the containment tree and `layout=column`. I think that is correct and
  I think the coordinates should eventually go, but a renderer that honours them will produce something
  nobody wants and be right to.
- **Tiled columns have no scroll.** The whole "cramped, 24px each, N past the bottom" pathology comes from
  this. The honest declaration is good; the layout is not. A column should scroll and the footer should say
  what is *actually* below the fold, which means the count has to come from the renderer, not the model.
- **There is no style subject yet.** My tokens live in the page's `:root`. Wren's roles-and-tokens design is
  where they belong; until it exists, every prototype re-invents a palette and the desk has no cohesion to
  be honest about.

## 6. The smallest next step

Not a framework. **Make one column honest**: surface owner as a real prop, scroll, and a fold count computed
from the layout rather than asserted by the model. Then point the eyes at it and ask for the eight checks in
§2. If all eight pass on one column, the brief is buildable; if any fails, we learn which row of the table
was wishful thinking before anyone writes a second column.
