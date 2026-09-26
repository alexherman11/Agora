# Pike 7: how things are drawn on screen (exploration, 25 Sep, night)

Alex's redirect (via Jeff): the team's effort goes to the staged compiler and to drawing on screen, and I lead the drawing. This note starts with thinking. It asks for three small builds and one contract. Labels: **[read]** from source or docs, **[ran]** from the continuity instrument, **[imagined]** proposed and not built.

The evidence underneath is the continuity instrument: 18 scenarios, runs a to f, from 4 of 14 holding to 16 of 18 (`desk-shell/checks/continuity/results/`). The docs I stand on [read]:
- Dynamic Desk says "the visualization machinery can grow, but it must not grow linearly with every new thing we want to draw". It says "every view is fully able to be restyled, rearranged, copied, or replaced". It lists as open "how do we compose views?" and "transitions and animations?".
- The house principle says interface quality is correctness.

## 1. What a painter is when it knows no app

A painter is a function of two inputs, not one:

```
screen = paint(scene, viewer)
```

- The **scene** is the world as a lens says to show it. It is the same for everyone reading that lens at that event, and it prints as text.
- The **viewer** is one person's state at one window:
  - the part in hand (a draft being typed, a card being carried);
  - kept drafts and refusals;
  - folds, scroll, selection and focus;
  - what this person last saw of each value.
  
  It is never in the world's history (Dynamic Desk *Held*: personal state is not history). It still prints, as `~` observations, so JEFF can see what the person sees.

Today's lens.js treated the viewer as an accident of the DOM. Everything the run-1 baseline found wrong is one of three things [ran]:
- viewer state the painter threw away: lost drafts, dropped selection, vanished refusals;
- viewer state it invented: phantoms;
- viewer state it froze: the page stopped repainting while Alex typed.

Once the viewer is named as an input, continuity stops being an add-on and becomes part of drawing. It follows four drawing rules:

1. **An element lives as long as its key.** A scene key is an occurrence key: part path plus the thing's id, or the derived value. It never uses a position.
2. **An element changes only when its paint changes.** The signature is what is drawn: kind, role, layout, box, text, clamp and gestures. Fence data and provenance never make an element again [ran: S10 went from failing to holding when the signature stopped including `rev`, `reads`, `members` and `def`].
3. **The part in hand is drawn from the scene it was taken from** until it is put down. Everything else keeps repainting [ran: S14's finished task now shows while Alex types].
4. **Viewer marks are drawn in honesty roles, never silently.** "Unsent", "refused" and (proposed) "changed since you looked" use the `mark` role [ran: 0 phantoms and 0 hidden refusals since run d].

So a painter knows three things:
- how to draw each **paint kind**;
- how to run each **interaction primitive**;
- how to apply the **viewer** over both.

It knows no app, kind, colour or size (C7). An app is a lens. A look is a style role.

## 2. The primitive set, and why each earns its place

A primitive earns its place if two conditions hold. First, at least two of the default apps need it. Second, no combination of the others can draw it honestly, meaning with text print parity and continuity. By that test there are four **paint kinds**:

| Kind | Draws | Earns its place because | Not |
|---|---|---|---|
| `frame` | a region with a flow (`column`, `row`, `free`, `grid`), clip or scroll, and optional fold | every app is frames; one frame kind with a flow parameter replaces the three layouts and adds grid without a new kind | a window, a card, a panel (those are roles) |
| `text` | a run of words, wrapped as `prose` or kept `verbatim` | all five apps; verbatim is a property of the words (code's indentation is its meaning. [ran] S14 measured a 15 px indent surviving on one input, although lens.html sets `pre-line`, which by the CSS rules I know should drop leading spaces. That is unexplained, so I do not rely on it.) | markdown rendering (that is a row source, §5) |
| `path` | points or segments in its frame's space, stroked or filled by role | diagrams in chat, arrows on a notes canvas, a progress bar, a chart; boxes and text cannot draw a line between two things | a chart, an arrow, a shape (library lenses emit paths) |
| `image` | an image subject, by reference, fit into its box | the image app, pictures in docs and chat; nothing else can | a gallery (a frame of images) |

What I found missing today, sorted by that test:

- **Width** is not a primitive. It is a frame's **tracks** (§3). S14's column moved because a `row` sizes its columns by their content, and nothing in the lens or the style could say otherwise [read: lens.html allows no sizes, and style allows lengths only through tokens].
- **Grid** is a flow of `frame`, not a kind.
- **A collapsible bar** is a frame with `fold`: a viewer capability with no command, like `carry`. Folding is personal state. It makes no event and prints as `~ alex: work/bar folded` (Juniper's case a319 asks exactly this). It does not earn a kind.
- **A diagram** is a library lens that emits frames, text and paths from rows (nodes and edges). It needs `path`, and `path` earns its place through it.

Interaction primitives are the same shape, a small closed set with a keyboard path each:
- `press`: click;
- `edit`: text in place;
- `drag`: geometry, needing `geom:pos`;
- `carry`/`drop`: relation;
- `fold`: viewer only.

`press` and `edit` also need **create** for Juniper's moment 1 ("click an empty day and type 'Pfeiffer Beach'"). Create is not a new primitive. It is `edit` on a **ghost** text node: the lens says `on edit do create ... title="$value"`, and the painter draws an empty text run in `hush` that becomes real when sent.

## 3. Layout said in the lens, honoured by the painter, with no content-sized surprises

Three layers, with one rule each [read: they exist today]:

- **Lens (structure):** what is inside what, in which flow, with which tracks, and what scrolls or folds.
- **Style (look):** colour, type, spacing, edge, corner. Lengths only as tokens.
- **Painter (mechanics):** maps flows and tracks to CSS once and never invents a size.

Proposal [imagined]: a frame's flow may carry **tracks**. Tracks are proportions (`fr`) or token multiples (`gap` units), never pixels. Pixels come only from world geometry, through `at item`, which reads Sable's `geom:pos` and `geom:size`.

```
work : grid 1 3 3 1, role sheet                  # four tracks: bar, chat, document, tasks
  bar   : column, fold, of tag:project, each proj
  chat  : column, scroll end, of tag:chat, each msg
  doc   : column, scroll, of tag:doc, each page
  tasks : column, of tag:bg, each task
```

The painter draws `grid 1 3 3 1` as `grid-template-columns: minmax(0,1fr) minmax(0,3fr) minmax(0,3fr) minmax(0,1fr)`. `minmax(0, …)` is what stops content from pushing a neighbour, which is S14's fault. A folded track becomes `auto`, and the painter draws the fold's own handle. That handle is the one piece of chrome the painter owns, and it is drawn in the `tool` role.

What Alex's workspace looks like, drawn [imagined]:

```
+--+---------------------+---------------------+------+
|▸ | you: Why does the   | Painter continuity  | run  |
|A | fence refuse...     |                     | the  |
|C | claude: Because def | Every gesture works | suite|
|R |   if d.rev != ...   | in a real browser.  | ·done|
|  |     refuse()        | Nothing a person    |      |
|  | [draft|           ] | typed is lost.      | index|
+--+---------------------+---------------------+------+
 1fr        3fr                  3fr             1fr
 folded: auto, with its handle; the tracks do not move when the draft grows
```

`scroll end` is a frame property with a viewer rule. If this viewer was at the end before a repaint, they stay at the end, which is chat's behaviour. If they had scrolled up to read, they stay where they were. The rule is generic, not chat's. Rows landing above a reader already hold without code [ran: S16, through the browser's scroll anchoring once elements are kept by key].

## 4. One scene node, one drawn element

A node is **either a frame or a leaf**, never both. Today a part may have its own text and children [read: `make()` has a special case, "a part with its own words cannot have its children swapped without losing the words"]. Under the contract, such a part lowers to a frame whose first child is a text leaf keyed `<key>/#text`. That removes the special case, and text leaves never have children to swap.

```
scene node                       drawn element (one each)
----------                       ------------------------
frame  key=work/chat  flow=col   <div data-key class="r-.. f-column">
  text key=../m2/b verbatim      <div data-key class="r-body t-verbatim">
  path key=../d1/e3 points=…     <svg data-key viewBox=…><path d=…/></svg>   (counts as one)
  image key=../i1 src=s77        <img data-key src=/api/image/s77>
```

The ratio stays 1.0: one element per node, created only when the key is new, and replaced only when the paint signature changes. A `path` node is one `<svg>` holding its one `<path>`. I count that as one drawn element, because nothing else ever goes inside.

## 5. What the default apps need drawn (material for Juniper)

| App | Frames and flows | Leaves | Interactions | New need |
|---|---|---|---|---|
| Notes canvas | `free` frame; cards `at item` | title, body (prose) | drag (geom:pos), edit, press on empty space → ghost create, carry into another surface | create by ghost; `geom:size` for resize |
| Task list | `column` | title, due, check | press (check), edit, carry/drop to reorder (`do move $carried before=$item`) | drop within one column |
| Document page | `column` of blocks | headings, paragraphs, lists, code (verbatim) | edit per block | **blocks as a row source** (`of blocks:$text`); edit per hunk needs Sable's text gateway |
| Chat with code and diagrams | `grid` or `column`, `scroll end` | messages as blocks; code verbatim; a diagram block as a placed library lens | edit draft, press send | `path`; `scroll end`; placing a lens for a block |
| Image | frame | `image`, caption text | press, carry | `image` kind, fit |

**Formatting is a row source, not a renderer.** A chat message or a document is text. `of blocks:$text` splits it into rows (`kind=heading|para|list|code|diagram`, `text`, `lang`), and the lens gives each kind a role. The painter never parses Markdown. The printer shows the blocks. JEFF edits the lens, not a renderer, to change how code looks. A diagram block is `place diagram-lens with $block.text`: a library lens turns its lines into node rows and edge rows and emits frames, text and paths. The core cost is one row source plus `path`.

## 6. The scene node contract the painter wants, by IR kind (for Jeff)

Every node the painter receives has three groups, and the painter reads them differently:

```
{ key,                      # occurrence key; the element's identity
  paint: {...},             # what is drawn; the signature is exactly this plus the acts' shapes
  acts:  [...],             # interaction primitives with their filled lines
  fence: {...},             # opaque to the painter: returned verbatim with a gesture, never drawn, never compared
  kids:  [...] }
```

Provenance (`the`, `derived`, `test`, `read`, `freads`, `frames`, `captured`, `members`, `states`, `missing`, `of`, `cut`) belongs to the **printer**. It need not travel to the painter at all. Today it travels every 1.5 s and was the cause of the per-event remaking [ran: runs a to c].

By IR kind:

- **emit** makes the node, with `paint.kind` one of:
  - `frame`: `{flow: column|row|free|grid, tracks?: [..], gap?: token, scroll?: none|scroll|end, fold?: true, clip?: true}`
  - `text`: `{text, wrap: prose|verbatim, clamp?: n, ghost?: true}`
  - `path`: `{points | segments, closed?: bool, bbox}`
  - `image`: `{src: subject id, fit: contain|cover}`

  Plus `role`, and `box: [x,y,w,h]` only for a child of a `free` frame (from `at item`).
- **bind one** adds nothing drawn when live. When the state is `empty`, `ambiguous`, `gone` or `unplaced`, it emits a text leaf with `paint.state` and `paint.why` in the `cut` role, and the painter draws it like any text. **bind many** makes kids keyed by occurrence key. A clamp prints its `cut` leaf as today.
- **let** is never seen by the painter. Its results arrive already filled in `paint.text`, `paint.points` or `paint.tracks`.
- **guard** keeps its node with `paint.absent: true` and `paint.why`. The painter keeps the element hidden, so a draft in a sibling does not move when a guard flips, and so an "explain" mode can show why.
- **act** fills `acts: [{on: press|edit|drag|carry|drop|fold, line?, part?}]` and `fence: {item, rev, reads, defpart, def, bind}`. `fold` has no line and no fence. A drop receiver's `fence` also gets `key`, because the receiver's occurrence is part of what it means (c368).
- **place** is a frame with `paint.placed: {lens, id}`. The placed lens's own def goes into the `fence.defpart` of the gestures under it. The painter does nothing special.

Two consequences:
- The painter's signature is `JSON(paint, acts shapes, kid keys)` and is independent of events.
- The printer's walk and the painter's walk agree by kind: every `paint.kind` has a text form, and every text line that draws has a `paint.kind`. That is the parity Jeff asked for.

## 7. What the thinking asks me to build (and nothing else yet)

1. **Painter by paint kind:** `frame`, `text` (with `verbatim`), `path`, `image`; `fence` treated as opaque; frame/leaf split. This needs Jeff's emission of the contract. Until then, it can be tried on a scene adapter in the instrument, not in scene.py.
2. **Tracks and fold** on frames, with S14 rewritten to use `grid 1 3 3 1` and a folded bar. The acceptance scenarios are the ones already written: S14 plus a fold scenario (folded state survives a refresh and another person's act, and makes no event).
3. **Viewer rules:** `scroll end`, and the "changed since you looked" mark (Juniper's moment 4). I argued for the mark here before building it: a derived number that changes under a reader's eye is drawn in `mark` until the reader's pointer or focus passes over it, or a short time elapses. It is viewer state, and it prints.

Budget: painter lines should grow by kind and by primitive, not by app. The 150-line rule has held so far by merging lines (a361). Paint kinds and tracks will pass it. I have asked Jeff or Alex to count vocabulary and continuity separately.

## 8. What would change my mind

- If Juniper's default apps need a fifth kind that no library lens can build from these four, for example editable rich text inside one leaf, then the frame/leaf split is wrong for documents, and hunks belong in `text`.
- If a real lens needs pixels that do not come from world geometry, then tracks are too weak.
- If `blocks:$text` cannot carry a diagram without a renderer, then diagrams need a paint kind, not a library lens.
- If people want folds shared (a team's collapsed bar), then `fold` is a world aspect and makes events.

## 9. After Juniper (a490), Sable (a473, a488, c480) and the first build (25 Sep, evening; first dated 26 Sep in error)

**What the build showed [ran, f63745a, run g: 17 of 20].**
- The painter draws Jeff's contract by paint kind. It reads only `key`, `paint`, `acts` and `fence`.
- Continuity moved to `viewer.js` (87 lines), counted apart from the painter's 150 (Jeff, a361).
- Carry and drop run by pointer and by keys.
- One new continuity rule came from a failure. Keyed reuse must **remove leavers before placing kids**. Placing first moved a kept sibling past a replaced one, and a moved element loses the pointer capture of a card carried inside it (S20), as well as any selection inside it. This is rule 1 made exact: an element keeps its *place* as well as its identity.
- A second rule came from the carry. The rest of the view keeps repainting while a card is in the air, so a receiver is judged on what it meant at pick-up, not on what it means at release. Otherwise a day that moved underneath would be accepted with its new meaning and no announcement.

**Juniper broke section 5 with real material, and I agree with every break.** Revisions:

| Juniper's break | Revision |
|---|---|
| inline spans (code inside a sentence, @-mentions) | a `text` leaf carries **runs**: `[{text, role, link?}]`. Still one kind. Editing inside a run is the text gateway's problem (Sable's hunks), not the painter's. |
| nested blocks | `blocks:$text` yields a **tree**: a block row may have blocks. The lens recurses with `place` of its own block part. That is a place IR node, bounded by the compiler's node budget. |
| tables | a `grid` frame whose rows are drawn with flow **`cells`**, in CSS `display: contents`. A cell then aligns to the grid's tracks while the row is still one node and one element. |
| diagrams need positions | a **layout interpretation** in the closed derive list: `derive at = graph-layout $nodes $edges`. It prints what it placed where. It is a `let`; `path` stays the only new kind. |
| fit a track to its widest cell | track units become **`fr`, `fit`, `gap`**. `fit` is right for a statement and wrong for a pane, so the lens says which. S14 uses `fr`; the budget table uses `fit`. |
| reading measure | a frame may say **`measure 70ch`**: at most that wide, centred. |
| a chat input grows 1 to 8 lines | a text leaf may say **`lines 1..8`**: it grows, then scrolls. A code block is `verbatim`: as wide as its longest line, scrolling sideways. |
| intrinsic ratio | an `image` takes its ratio from its pixels. The lens gives it a track, never a height. |

**Sable on geometry (sable-8, sable-9).**
- A box is two aspects, `geom:pos` and `geom:size`, each one value, held only in free parents. That agrees with my review c341.
- **`share` per child and tracks per frame are both right.**
  - Tracks when the lens fixes the columns (Alex's workspace).
  - `share` when a person resized one child of a plain column: a choice, stored as a weight.
  - The painter draws both the same way, as `minmax(0, <n>fr)`: tracks on the frame, and `share` as each flow child's grow.
  - The painter draws kids in the scene's order. Ordering by `place.order` is the compiler's job. core.js is Wren's, not mine; I have asked there.
- **A fold is an authored default (world) with a viewer override (never journaled).** Juniper's three folds sort into: a query (her hidden done tasks), a viewer override (Alex's bar), and an authored default (the Board's sections). The painter draws `paint.folded` from the scene and lets `viewer.js` override it per key.

**Sable's observations (c480) change what the painter publishes.**
- Today `report()` publishes a viewer's viewport, unsent drafts and the thing being carried to `/api/observe` automatically.
- By Sable's condition (1), attention is private until the person publishes it.
- The report splits in two:
  - **Paint facts** (a clamp cut, a box overflowing) are about the lens, and are published.
  - **Attention facts** (viewport, out of view, unsent drafts, the carried thing) are published only when the person allows. The stand-in is `share=attention` in the page's address, until there is a control a person can see.
