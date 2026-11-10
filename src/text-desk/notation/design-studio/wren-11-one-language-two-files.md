# One language, two files, one shared word

Wren on the missing piece. Position, then the desktop written as a lens, then every missing word
defended or refused, then the eight concerns.

---

## 0. The measurement that settles the first question

`lens.html?session=lens&as=wren&lens=notes`, measured just now:

```
=  38 painted elements
=  8 distinct roles, every one resolved from calm.style
=  3 distinct type sizes — 11 / 13 / 15 — every one a step of the ramp
```

Against the hand-written desktop, where Iris measured **ten** sizes (11, 11.5, 12, 13, 14, 15, 16,
16.38, 23, 26 — two fractional) and I had to build a `style reach` report and a `snap to ramp`
override to even see the problem. Nobody asked the lens to behave. It has three sizes because
**a lens cannot say a size**. My round-five finding was *"a refusal only disciplines the person who
has to pass through it"*; a lens is a place everyone has to pass through. That is the whole argument
for this direction and it is already true in v0.

*Two corrections from Iris's A/B, which I accept. Forcing the ramp does **not** flatten hierarchy —
with snap on she measured the Editor at title 23 / heading 15 / body 13, reading correctly — so my
"consistent but slightly wrong" instinct was mostly wrong, and the case for making the ramp
**binding** is stronger than I argued in round five. What survives of the caution: meta and body
were one step apart and now share a step, a distinction the author meant and forcing cannot keep.
And she counted four sizes where I said five, because I reported a count without saying which
windows were open. A version number fixes staleness; it does not fix the fact that a desktop's type
scale depends on which lenses are on the stage.*

---

## 1. Is a lens a second language beside calm.style?

**No. It is one language in two files, and the seam is the word `role`.**

| | says | may never say | word count today |
|---|---|---|---|
| **style** (`calm.style`) | `token`, `role`, `when <selection>`, `theme` | any content, any thing in the world, any gesture | 4 |
| **lens** (a note tagged `lens`) | parts, `column row free`, `text`, `clamp`, `of`, `over`, `each`, `at`, `on … do` | any colour, any length, any font | 9 |

`role <name>` is the only crossing and it crosses **one way**: a lens names a role; the style has no
idea a lens exists. That asymmetry is what keeps either file readable alone.

They are already the same *shape* — `name : prop, prop, ...`, comma lists, a spaced colon (because
the desk's own selections use unspaced ones), `# ` comments, refusal with a line number. They should
share a lexer, literally, so that a person who has read one can read the other.

### The one duplication, and I am retiring it

`present card : title, body :3, meta, tags` in `calm.style` is mine, from round three, and the lens
supersedes it. A `present` line and a lens's indented children say the same thing, and the lens says
it better because it can also say where the words come from:

```
# calm.style, round three — retire this
present card : title, body :3, meta, tags

# the lens, which says all of that and the source of every word
card : column, role card, at item
  title : text $title, role title
  body  : text $text, clamp 3, role body
  tags  : row, over $tags, each tag
```

**v0 change I would make: delete `present` from the style language.** Two ways to say one thing is
how a small language stops being small, and I put the second one there myself.

---

## 2. The desktop, as a lens

Written against v0's grammar. Lines that need a word that does not exist are marked `<<< MISSING`.

```
lens desktop
desktop : column, role desk
  bar : row, role bar, spread                                        <<< MISSING: spread
    where : text $session · you are $me · $today, role meta          <<< MISSING: $session $me $today
    open  : text $count open, of in:$me screen, role meta            <<< MISSING: $count, $me in a selection
    fork  : text worktree $worktree, role mark, only when $worktree  <<< MISSING: only when
    theme : text theme $me.theme, role tool, on click do prop $me theme=$next   <<< MISSING: $me.prop, $next
  stage : free, of in:$me screen, each window
  dock  : row, role dock, of tag:lens, each launcher
window : column, role window, at item, on drag do move $item to=$x,$y
  bar : row, role titlebar, spread
    name : text $title, role windowname
    shut : text close, role tool, on click do remove $item
  inside : lens $lens.of $item                                       <<< MISSING: lens composition
launcher : column, role dockitem, on click do place $item into=$me screen
  glyph : text $glyph, role glyph                                    <<< MISSING: $<prop>
  label : text $title, role dockitem
```

Sixteen lines for bar, dock, stage and window frame, against **356 lines of `shell.js`** and 53 of
structural `shell.css`. That ratio is the same order as Flint's for Notes, and it is the honest
headline even before the missing words: **the frame of a desktop is not where the complexity is.**

### And the part that already runs

I wrote the subset v0 can express as a real lens in `proto-wren` (a copy of `lens.pickle`) — twelve
lines, no missing words:

```
lens desktop
desk : column, role desk
  bar : row, role bar
    where : text a desktop written as a lens, role meta
  stage : free, of kind:note,in:Canvas, each window
  dock : row, role dock, of tag:lens, each launcher
window : column, role window, at item, on drag do move $item to=$x,$y
  frame : row, role titlebar
    name : text $title, role windowname
    shut : text close, role tool, on click do remove $item
launcher : column, role dockitem, on click do look $item
  label : text $title, role dockitem
```

`scene desktop` prints a working desktop: eight draggable windows at their world positions, each
with a titlebar, a name and a live close button, over a dock. The last four lines of the output are
the thing I did not expect:

```
    dock [dock] row · 2 of tag:lens
      launcher a56 [dockitem] column · click: look a56
        label a56 "notes" [dockitem]
      launcher a58 [dockitem] column · click: look a58
        label a58 "desktop" [dockitem]
```

**The desktop lens appears in its own dock**, because it is a note tagged `lens` like every other
app, and `of tag:lens` does not know the difference. Nothing was designed to make that true. A
system where the shell is one of the applications, and the list of applications is a query, is the
first thing in six rounds that has felt like a foundation rather than a layer.

Two results worth stopping on, because neither needed a new word:

**The dock is `of tag:lens`.** The apps in the dock are the lenses in the world. *Installing an
application is `do create Claude kind=note title="triage" tags=lens text="…"`.* It is undoable,
forkable in a worktree, and visible to the other inhabitant as it happens. I did not design this;
it fell out of lenses being notes.

**A count needs no expression language.** `of <selection>` with no `each` should yield a count and
no children. `open : text $count open, of in:$me screen` — one part, one selection, one substitution,
and the scene prints `open "3 open" [meta] · 3 of in:wren screen`. See §4 on why this is the entire
expression language I want.

---

## 3. The missing words, defended or refused

### DEFEND — `lens <name> of <thing>` (composition)

The one that matters. Without it, a desktop lens must inline every app, so there is one giant lens
and no apps; and a window cannot show "whatever this thing's lens is". With it, a lens is a
component and `window/inside` is two words.

It is printable, which is the test: the scene prints the child lens's subtree under the part, with
its own name, so an agent reads one tree and nothing is hidden. It also makes the dock and the
stage agree — the same lens that the dock launches is the one the window shows.

Risk I accept: recursion. A lens that places itself is an infinite scene. Guard: a fixed depth
(say 8) and the scene prints `! depth 8 reached, not expanded` at the cut. Declared, not silent.

### DEFEND — `only when <selection>`

The bar must not draw an empty worktree band or "0 not in the world". Without conditional presence
every lens draws its own blank furniture, and lens authors will ask for `text` that can be empty,
and then for an empty `role`, and we will have invented `display:none` sideways.

Constraint that keeps it from being an expression language: **the selection is the desk's own
selection language, evaluated against the current thing, and there is no `and`, `or` or `not`
beyond what selections already have** (comma is AND, `-` negates). Absence is printable: the scene
prints `fork — not shown (only when $worktree; no worktree)`, so a text reader learns the part
exists *and* why it is absent. That line is worth more than the part.

### DEFEND — host facts in templates: `$me $session $today $worktree $count`

Not an expression language: a **closed, named set**, each one a fact the desk already prints
somewhere. Each new one is argued for individually on the studio desk, like a token. That is
concern 5's answer and it is the same answer as `token`: *naming is allowed, computing is not.*

### DEFEND, weakly — `spread` on a row

A bar needs its right-hand group at the right. Today that is impossible, and the workaround is a
spacer part with no words, which is worse: an invisible part with no meaning, which the text printer
would have to print as nothing. `spread` prints (`bar [bar] row spread`) and is one painter line.
I would take it, and I would refuse anything more — no `align`, no `justify`, no `end`.

### DEFEND — `$<prop>` substitution

A dock item wants a glyph. A lens is a note; a note has props. `do prop "notes" glyph=◇` puts it in
the world, and `text $glyph` reads it. This lets a lens carry its own metadata in the world instead
of in a special field, and it costs one substitution rule. It also makes a lens self-describing:
`do prop "notes" accepts=kind:doc` and the dock can say what an app opens.

### REFUSE — an expression language

No arithmetic, no comparison, no concatenation beyond template substitution. The moment `$a + $b`
exists, everything else in this document is decoration. Where a number is genuinely needed and
`$count` cannot give it, the answer is a **named measure** provided by the host and printed with its
conditions, exactly as `measure a91` already prints `=5 pages under width 736px`.

### REFUSE — `style` or `class` on a part

Someone will ask for `card : role card, width 400`. No. If a card needs to be 400 wide, either it is
`at item` (the world owns the geometry, and a person can drag it) or the role owns it. There is no
third place, and adding one re-opens the reach problem the lens just closed by construction.

This one is already true in v0 and the refusal is good. Tested in `proto-wren`, a copy of the lens
session:

```
> do rewrite a58 text="lens probe\nroot : column, role window\n  bad : text hi, width 400"
> scene probe
ERR line 3: a lens cannot say 'width 400'. It can say: column, row, free, role, text, clamp,
    of <selection>, over $field, each <part>, at item, on <gesture> do <command>
```

A refusal that prints the whole vocabulary is a closed vocabulary you can *read*, which is worth
more than a closed vocabulary you are told about. I would keep that shape for every new word.

And `of` without `each` is currently refused, so the `$count` proposal above is a real change to
v0, not a description of it:

```
ERR line 3: `of`/`over` repeats something; say what with `each <part>`
```

### REFUSE — an `if/else` pair

`only when` without an else. A lens that needs two alternatives writes two parts with opposite
selections; both print, both explain their absence. `else` is where a declarative language starts
growing a control flow, and it saves one line.

### REFUSE (for now) — sort and filter beyond a selection

`of kind:note,in:Canvas` is enough. `sort by $due desc` is the front door to a query language, and
the desk already has `sort` as a *verb* — a lens that wants order should ask the world to have
order, which is a deed, attributable and undoable. That is the general form of the discipline: **if
the world or the style could carry it, the lens must refuse it.**

---

## 4. Texture, states, motion — which belong where

From my round-five list of what the style cannot say.

**Texture → the style.** It is pure look with no content and no meaning, and it is the only way to
make an honesty mark loud without adding a colour. Every hatched band on the desktop today is
hand-written CSS. I would add exactly one word to the style, not the lens:

```
role mark : text down medium, mark, hatch mark at 45, pad gap /4
```

`hatch <colour> at <degrees>` — the pitch comes from `gap`, so there is no new number. Nothing else:
no gradients, no images, no blend modes.

**States → split, by one test.** *If the state exists when nobody is looking, it is the world's; if
it exists only because a pointer is there, it is the style's.*

- `hover`, `focus`, `pressed`, `drag-over` → **style**: `role tool:hot`. Per-viewer, ephemeral,
  never in the world, never in the scene. The other inhabitant does not need to know my mouse is
  over a button, and a scene that carried it would be a firehose.
- `selected`, `open`, `warm`, `overdue`, `claimed` → **world**, reached by a style clause
  (`when warm : …`) or a lens `only when`. These exist when nobody is looking. They are facts.

The dangerous middle is `selected`. I put it in the world: a selection is something Alex can hand
to me (*"do this to these"*), and that is impossible if it lives in his browser.

**Motion → neither.** Motion is a transition *between two scenes*; it has no text, and my standing
rule is that anything that cannot be printed cannot be authored. The painter may ease any change it
likes; that it eased is not a fact anyone needs, and `duration` can be one token. I would refuse a
curve, a keyframe and a stagger in both files. If motion ever needs authoring, that is the signal
that the painter has become an application and something has gone wrong.

---

## 5. Attacking the eight concerns

**1. The inner-platform trap.** Jeff's guard — closed vocabulary, printable before paintable — is
necessary and not sufficient; every declarative UI language had a closed vocabulary at v0. Three
more, in increasing order of how much I believe them:

- *If the world or the style could carry it, the lens must refuse it.* The dock over `tag:lens` is
  this rule paying out: what would have been a lens feature is a selection over notes.
- *A word must be printable **and** its print must be shorter than its paint.* If the text form of a
  feature is as long as the pixels, the feature is decoration and belongs to a role.
- **A line budget on the painter.** `lens.js` is 77 lines. Fix the ceiling at 150 and make every new
  word cost lines from it; at the ceiling, a word must be *removed* to add one. This is the only
  guard that cannot be argued around, because it is arithmetic — the same trick as forcing spacing
  onto a `gap` scale. I would write the budget into the file header today, while it is cheap.

**2. Continuous and ephemeral state.** Split it the way round four split windows. What exists when
nobody is looking goes in the world (theme, selection, which windows are open — all already props or
appearances); what exists only because an eye is there is drift, printed in parentheses, per actor,
never exported, and the scene declares its absence rather than carrying it. The scene needs one
thing: a drift line per part it is true of, which the painter fills and the text printer prints as
`(alex editing, 4s)`. Not a new authoring word — a host behaviour.

**3. Rich text editing and natives.** I accept a native part, and I think it is the most dangerous
thing in this design (see §7). My constraint: **a native must be declared in the same grammar
(`native prose-editor`), must print its own scene subtree, and must declare its opaque extent as
`?` with a measurement.** And the count matters more than the contract: I would fight to keep it at
**two** — `field` (one line) and `prose` — and refuse `image` on the grounds that an image is a
thing in the world with a role, not a widget.

**4. Where layout is computed.** Yes: measured facts flow back from the painter as `~` observations,
attributed to the painter as an actor, stale-marked when the scene revision moves. That is the eyes
protocol made structural and it is exactly what `=5 pages under width 736px` already does. The rule
that keeps it honest: **the text printer may never invent a number it did not receive**, and a
measure with no observation prints `? not measured` rather than a guess.

**5. Computed values.** Answered in §3: `$count` from an `of` with no `each`, a closed set of named
host facts, named measures for anything else. No expression language, ever.

**6. Conditional look: lens, style, or both?** **The style, and only the style.** A lens says
`role card`; the clause `when due<today : ink -> accent` is what makes every lens author obey a rule
they never read. Move conditional look into the lens and each author must remember every rule, and
they will not — that is round five's finding restated. Who wins: role, then clauses in file order,
then the per-appearance override, and `why <id> :look` prints the losers.

One real gap to declare: a clause matches a *thing*, and lens parts like `hint` or `shut` are not
things — no kind, no tags. So clauses cannot reach them, and they take their role and nothing else.
I would rather declare that limit than add `when part:hint`, which is a selector language arriving
through a side door.

**7. Cost.** The scene tree should carry a stable key per node — `item` where there is one, the part
path where there is not — from v0, even though nothing diffs yet. Keys are the one thing that is
expensive to retrofit and free to add now. Lark's 93%-of-polls-buy-nothing is an argument for
event-driven refresh, not for a different scene.

**8. Windows, dock and bar as a lens.** Yes — §2, and the sixteen lines are real. But I would keep
one thing out of the desktop lens: **the boot surface.** If the style, the scene or the server is
missing, something must still draw a sentence saying so. A shell that is entirely a lens cannot
report that lenses are broken. That is the round-five boot guard argument at the next level up, and
it is my only structural objection to "the shell is a lens too".

---

## 6. What I would change in v0

1. **Delete `present` from `calm.style`.** The lens says it better (§1).
2. **Share the lexer** between the two files: one comment rule, one spaced colon, one comma list,
   one refusal shape.
3. **Write the painter's line budget into `lens.js`'s header** (150), before anyone wants a word.
4. **Stable keys in the scene**, now, while free.
5. Add, in this order: `lens … of …`, `only when`, `$count`, `$<prop>`, `spread`, and `hatch` in
   the style. Six words, one of which is not a lens word.

## 7. The one thing most likely to sink this

**The native part.** Not because rich text is hard — because a native is a hole in the wall, and
every hard thing will be pushed through it. One native becomes three, three become "native
canvas", and then every app is a lens that places one native and the lens is a layout language for
opaque boxes. At that point `text(ctx)` comes back, hand-written, *inside each native*, and we are
exactly where we started with more ceremony.

The tell will be arithmetic, and I would watch it from the first native: **the ratio of scene nodes
to painted elements.** Today the notes lens is 38 painted elements from a scene of 38 nodes — 1:1,
nothing hidden. The day a window is 1 scene node and 400 painted elements, the scene has stopped
being the source of the picture and has become a placement list. I would put that ratio in Iris's
fixed script this round, before any native exists, so we have the baseline.
