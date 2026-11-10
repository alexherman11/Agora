# One window, end to end

Wren, sketch 4. The three earlier files argued. This one just writes the text out: a
Google-Docs-grade window, the style subject that produces it, what `look` prints, what the person's
gestures write, and — the test nobody has run yet — **what `export` emits**, since Alex's whole
foundation rests on "the commands that rebuild a desk from nothing".

Written in the four-zone grammar of sketch 3, with Lark's `=` `~` `?` `!` marks.

---

## 1. `export` of a rich window

This is the honest test. If a Google-Docs-grade window cannot be printed as commands that replay,
the design has failed Alex's constraint, and no amount of pretty `look` output saves it.

```
# style, first, because everything else names it
do create desk kind=style title="calm"
do define calm token paper=#FBFAF7 ink=#14171A accent=#3F5D73 gap=8 text="serif 16/1.55"
do define calm token line="ink at 12%" quiet="ink at 55%" mono="mono 15/1.5"
do define calm role page  "paper, text, pad gap x3, width 46em, edge line"
do define calm role rail  "paper, text at 0.82, pad gap x2, border left line"
do define calm role band  "paper, text at 0.75 tracked, pad gap, border bottom line"
do define calm role heading.1 "text x1.6 strong, space above gap x3, space below gap"
do define calm role strong "text weight 620"
do define calm role anchor "accent at 15% behind, underline accent"
do define calm when "kind:task,due<today" "ink -> accent"

# the material
do create alex kind=doc title="Q3 plan" text="## Summary\nWe ship in three phases. ..."
do mark "Q3 plan" kind=comment at="Risks" quote="The vendor may slip" by=alex line="is this the Dec build?"
do mark "Q3 plan" kind=link at="Budget" quote="supplier B" to="Supplier B contract"

# the window
do create alex kind=window title="Q3 plan" as=doc.window w=1180 h=820
do place "Q3 plan" in="Q3 plan" as=page
do add "Q3 plan" band  "toolbar"  of="verbs:Q3 plan"    as=doc.toolbar
do add "Q3 plan" rail  "outline"  of="headings:Q3 plan" as=doc.outline
do add "Q3 plan" rail  "comments" of="marks:Q3 plan"    as=doc.margin
do style a91 width=620px          # alex's one override, e442
```

Sixteen lines for a window a commercial product spends a hundred thousand lines on. That is the
whole argument for this design in one exhibit, and the reason it works is that three of the four
panes are **views of things the desk already models** — verbs, headings, marks — so they need no
definition of their own, only a role.

Two things the export makes visible that the prose arguments did not:

- **The override survives export, as an override.** It replays as `do style a91 width=620px`, a
  separate line at the bottom, attributed in history to alex. Design debt is not laundered into the
  design by round-tripping. I think this is the single strongest piece of evidence for the override
  idea from sketch 1.
- **`do define` is a verb like any other.** The style subject is edited by commands, not by opening
  a file. So a style change is an event, has an actor, can be undone, can be commented on, and
  appears in the other inhabitant's "since your last look". Alex sees `jeff changed the house
  spacing` in the same channel he sees everything else.

## 2. What `look` prints, at three depths

```
> look "Q3 plan"
f30 window "Q3 plan" · =1180x820 · as=doc.window · (alex here, typing §Risks 4s)
  f31 band  "toolbar"  of verbs:s84      · as=doc.toolbar · 9 shown, 4 folded
  f32 rail  "outline"  of headings:s84   · as=doc.outline · 6 headings · (alex at §Risks)
  f33 page  a91 doc "Q3 plan" · 1,412w · 6 sections · 4 marks · as=page, 1 override,
                                          =page 2 of 5 under 620px · (alex §Risks/3+12ch)
  f34 rail  "comments" of marks:s84      · as=doc.margin · 4 marks, 2 open, 1 orphan
```

```
> look f34 :3
f34 rail "comments" of marks:s84 · as=doc.margin · 4 · 2 open · 1 resolved (folded) · 1 orphan
  m14 orphan  alex  §Scope   ("Q4")                     last seen e388
       -> do reanchor m14 at=§Scope/2      (~0.44, uncertain)
  m12 comment alex  §Risks   ("The vendor may slip")    open, 2 replies      exact
  m13 comment jeff  §Risks   ("a two-week buffer")      open                 moved
  m15 link    wren  §Budget  ("supplier B") -> s90      exact
```

```
> why a91 :look
a91 looks the way it does because, in order:
  as=page                   calm :11
  when kind:doc,in:f33      calm :24    width 46em
  when comments:open        calm :26    rail comments shown
  override by alex e442     width 620px
    -> do reset a91 width          (back to the house)
    -> do define calm role page "…, width 620px"   (make it the house)
```

Four lines of cascade, each naming a source line, ending in the two real choices. If a cascade
cannot be printed in a screenful it is too clever; this one fits.

## 3. The colour picker is a token picker

This is where the notation reaches back and changes the visual product, and it is the part I would
show Alex first because it is the most immediately visible consequence.

A normal application gives you a colour wheel. Ours cannot, because the notation refuses to say a
colour anywhere but a `token` line. So the thing that opens when Alex reaches for colour is:

```
f40 window "Colour" · as=picker · of tokens:calm
  paper    #FBFAF7   ███  used by 214
  ink      #14171A   ███  used by 214
  accent   #3F5D73   ███  used by 31
  ---- derived ----
  line     ink at 12%     ███  used by 87
  quiet    ink at 55%     ███  used by 44
  ---- new ----
  do define calm token <name>=<value>      a new ground colour, named, for everyone
  do define calm token <name>="accent at N%"   a shade of one we have
```

You cannot pick a colour. You can pick a **word**, or coin one, and coining one asks for a name and
lands as an event everyone sees. That is friction, deliberately, at exactly the moment where
friction produces a coherent desk — and it costs nothing at the moment where friction would be
intolerable, which is writing prose.

The same shape works for spacing (`gap`, `gap x2`, `gap /2`, with counts) and type (`text`, and its
multiples). Three pickers, each a `look` at a selection of the style subject. No new machinery.

## 4. Two sides, one style

Lark's second file suspects that "sides" may be mostly a default owner for new things rather than a
real geography. If that is right — and I think it is — then my claim from sketch 1 gets easier and I
will restate it harder:

> **One style per world. A `theme` may redefine tokens; it may never define or redefine a role.**

So Alex's side can be warmer and Claude's cooler, or one dark and one light, and a thing dragged
from one side to the other **cannot change shape**, only shade. The structure of the desk is shared
even where the mood is not. This also makes the blind inhabitant's life sane: `as=page` means one
thing in the whole world, forever, and I never have to ask "whose page?".

```
do create alex kind=theme title="warm" of=calm
do define warm token paper=#FCF8F1 accent=#8A5A3B
do define warm role page "…"
refused: a theme may redefine tokens, not roles. "page" is the world's.
  -> do define calm role page "…"     (change it for both of us; jeff will see it)
  -> do style <this appearance> …     (change only this one, as an override)
```

## 5. The hole in my language, named

**Data-driven colour.** Three ground colours and `at N%` cannot express a spectrogram's ramp, a
heat map, a syntax-highlighting palette, or a chart with nine series. This is the research notes'
fifth-domain test and my style language fails it as written.

What I do not want is to cave and allow arbitrary colour, because the fifth domain would then reach
back and destroy the first four. What I think is right, half-formed:

```
token ramp.heat  = ramp from quiet through accent to #B4462F   # the one place a 4th value lands
token set.series = set of 9 from accent                        # generated, not authored
role  spectrogram : ramp.heat, mono, ?pixels
```

A `ramp` and a `set` are new **kinds of token**, not new places to write colours. They still live in
the token block, they are still named, `help tokens` still enumerates them, and a line that uses one
still says a word. The generated members are `=` measurable (`measure set.series -> 9 colours,
ΔE min 11.2`) so the blind reader can check they are distinguishable, which is a real question a
person cannot answer by eye either.

And the pixels of a spectrogram are `?`. They were always going to be.

## 6. The three refusals I would ship first

If only three parts of this notation survive, I want these, because each converts a habit into a
mechanism:

```
refused: colours are named here. nearest existing token is "accent".
  -> do style a91 ink=accent        -> do define calm token <name>=#3F5D73

refused: 17px is not on the scale. nearest are gap x2 (16px) and gap x3 (24px).
  -> do style a91 pad="gap x2"      -> do define calm token gap=<n>   (moves everything)

refused: a91 is showing "page 2 of 5", which is only true at 736px.
  say instead: "5 pages under width 736px, style calm"
```

The third is the one I would defend to the last, because it is the only one that protects the
*person* from the *model*. The first two just protect the desk from us.
