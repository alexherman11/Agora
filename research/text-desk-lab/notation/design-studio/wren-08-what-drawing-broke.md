# What drawing broke

Wren, round three. I built the renderer and the notation did not survive contact with it intact.
This file is the list of what broke, in the order it broke, because that order is itself the finding:
**everything that broke was invisible for two rounds of writing example text, and every one of them
broke within the first hour of having to paint pixels.**

The prototype: `design-studio/prototypes/wren-render/` → **http://localhost:8770/wren-render/**

- `desk.json` — a snapshot of the studio session (`python explore.py studio --dump`), 127 nodes.
- `calm.style` — the style, in my notation. Not translated by hand: **parsed at runtime.**
- `style.js` — the parser, token resolver, selection matcher, property→CSS resolver, refusals.
- `index.html` — the renderer, the inspector, the editable style, the honesty ledger.

The page's own CSS is structural only (flex, overflow, the side panel). Every colour, size, space,
border and radius on the desk comes from `calm.style` at runtime. If the parser cannot read a
property, the thing is drawn with browser defaults and marked with a dashed orange edge, and the
`honesty` tab counts it. That is the whole experiment: make the notation load-bearing, then see
what collapses.

---

## 1. The clause separator collides with the selection language

```
when kind:note : as=card
```

My round-one grammar was `when <selection> : <properties>`. The desk's selection language uses
colons — `kind:note`, `comments:open`, `tag:wren`, `in:f03`, `due<today`. A parser splitting on
"the colon" reads the selection as `kind` and the properties as `note : as=card`. Every clause in
my style file silently produced garbage, and the symptom was that *nothing had a role* — 114 cards
drawn with browser defaults.

Forced change: **the clause separator is a spaced colon, and you split on the last one.** An
unspaced colon always belongs to a selection.

```
when kind:note            : as=card        # separator is " : "
```

Round one also has `role anchor:hot : ...` for states, which has the same collision and which I
never noticed in two rounds of writing examples.

## 2. A bare colour is ambiguous, and I never saw it

My round-one showpiece line was:

```
role page : paper, text, pad gap x3, width 46em, edge line
```

Is `paper` the foreground or the background? I wrote that line four times across three files and it
reads perfectly until something has to paint it. Foreground and background are not a detail; they
are the two things a colour can be.

Forced change: **`on <colour>` is the background, a bare colour is the foreground.**

```
role card : on paper, ink, text, pad gap x1.5, edge faint, corner gap /2, space below gap
```

Every colour line in `wren-01`, `wren-04` and `wren-07` is wrong as written.

## 3. The notation said how things look and never what they are made of

This is the big one. I had `role card`. Nothing anywhere in two rounds said that a card consists of
a title, then a body, then a meta line, then tags — **in that order**. So for the first hour that
lived in JavaScript, which is precisely the "separately maintained shadow application" the research
notes warn about: change the style file all you like, the card still contains whatever my renderer
decided it contained.

The research notes' contract distinguishes **presentation** (which parts appear, with stable
meaningful parts) from style. I had collapsed the two and called the result a style language.

Forced addition:

```
present card   : title, body :3, meta, tags
present column : header, children
```

A part not listed is not drawn. `body :3` clamps to three lines and the clamp is declared in the
honesty ledger with the word count it hid. Delete `tags` from that line and the tags leave the desk;
reorder it and the card reorders. That is now text, and it was code an hour ago.

I think this is also the honest answer to Alex's "what is needed to unlock visual scripting from
within the desk": not a new scripting language. `present` is one line of text that decides what a
window contains, and it is the first thing I have written in three rounds that a person could edit
and immediately see change.

## 4. The notation cannot say arrangement at all

Still in JavaScript, still not text: that columns are 300px wide, that they sit in a row, that the
row scrolls sideways, that a column's children scroll while its header stays, that cards stack with
a gap. `role column` says padding, border and radius — and nothing about being a column.

I do not think the fix is to add flexbox to my notation; that road ends at CSS. The desk already
owns layout (`row`, `column`, `free` on every surface), so arrangement is arguably world material
rather than style. But then **width has two owners** — the world's geometry and the role's `width`
— and nothing in my notation says which wins. I hit that in the first ten minutes and resolved it
by ignoring the world's geometry entirely (see §6). Unresolved, and it is the largest hole left.

## 5. `as=` precedence was undefined

If an appearance carries `as=tag` and a clause says `when kind:note : as=card`, which wins? Two
rounds of writing and I had never asked. Every tag on the desk rendered as a card until I decided.

Decided while building: **the specific wins.** A clause may assign a role only where none is set,
because `as=` on an appearance is a deed about one thing and a clause is a rule about a kind of
thing. I believe it, but I want it on the record that the renderer forced the answer, not the
argument.

## 6. The stored geometry did not survive, and I said so on the page

The handoff asks: *which parts of the current geometry model survive contact with a real renderer?*
Answer, from having written one: **none of the absolute part.** Every node carries `x, y, w, h, z`
sized for a 1280×800 test screen; a real window is 1400 or 3400 or 760 wide, and columns need to
scroll. I ignored all of it and laid surfaces out as scrolling columns.

What survives is *containment and order* — `parent`, and the y-ordering within a parent. That is
the whole of the geometry model I actually used, and it is the part that was never controversial.

I did not hide this. The `honesty` tab says it in sight-marks, and every node's stored geometry is
printed in its `why :look` so the discrepancy between text and screen is one click away rather than
undiscoverable:

```
! the stored geometry (x, y, w, h, z on every node) is NOT used. the desk's
  1280x800 absolute model was built for testing; this render lays surfaces out as
  columns and lets them scroll. each node's stored geometry is printed in why :look.
```

## 7. Confirmed: `at N%` cannot make a palette

Round one named this as a suspected hole; it is real. `line`, `faint`, `quiet`, `hush` are four
percentages of one ink against one paper, and the result is a grey ramp with no tonal variation at
all. It is *calm*, which happens to suit this desk, but it is calm by inability. A second hue
requires a second ground colour, which requires a decision, which was the design — and I still
think that is right for chrome and hopeless for anything with data in it.

## 8. No states, and states are what a person sees that I never will

`role anchor:hot` implied hover and focus. There is no mechanism, and I did not add one, because I
realised while building that hover is the clearest case of something Alex perceives continuously
and I cannot perceive at all. It belongs in drift, not in the style file, and I do not know how to
say that yet.

---

## What held

- **The refusals are pleasant.** Typing `on #eeeeee` into a role in the page and getting
  *"colours are named here. `#eeeeee` may only appear on a token line → `token <name> = #eeeeee`"*
  feels like being helped, not blocked, and it took eleven lines of parser. Refusals 1, 2 and 6 of
  the catalogue run in the page; you can trigger them from the `style` tab.
- **`why :look` with the losers is the best thing I built.** Click anything and get the role, every
  applied layer with its file line, every resolved property with the clause that won it and, indented
  underneath, what it beat. Flint asked for the losers in round two; they cost four lines and they
  turn the cascade from a resolution into an argument you can read.
- **The token picker is real.** Tokens with swatches and usage counts, and the only route to a new
  colour is `token <name> = <value>`. You cannot pick a colour; you can pick a word.
- **A theme redefines tokens and is refused a role.** That rule survived being implemented, and the
  dark theme is three token lines.
- **Styling by the desk's own selections worked with no new matching machinery.** `kind:`, `tag:`,
  `in:`, `title:`, `comments:open`, negation, comma-AND — about forty lines, reusing the vocabulary
  that already exists. That was the bet of round one and it is the one part that cost nothing.

## The uncomfortable count

Eight things broke. Six of them (§1–§6) were invisible across two rounds, five files and perhaps
fifteen thousand words of example text that I believed was concrete. Writing example text is not
the same as writing text a machine must read, and I would now rather have one paragraph that parses
than five files that read well.
