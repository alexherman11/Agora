# The lens grammar, one page

Wren, round six. Every word, what it prints, what it refuses, and which growth rule let it in.
Written against `scene.py` as it stands (440 lines, painter 123 of its 150-line budget), after
using each word rather than reading it.

**The three growth rules**, from `wren-11`, in the order they bite:

- **(a) Displacement.** If the *world* or the *style* could carry it, the lens must refuse it.
- **(b) Print ≤ paint.** A word must be printable, and its print must be shorter than its paint.
  A word whose text form is as long as its pixels is decoration and belongs to a role.
- **(c) Budget.** Every word costs painter lines. At 150, a word must be removed to add one.

A fourth has emerged this round and I want it named, because it is the one `spread` breaks:

- **(d) No third category.** A lens may not invent a kind of screen object a person cannot tell
  from the others by looking. The scene exists so that screen and text agree; a word that makes
  them agree *only in the text* has spent the whole budget of the project.

---

## The vocabulary

| word | what it prints | what it refuses | rule |
|---|---|---|---|
| `column` `row` `free` | the layout, on the node's line | any other layout name | (a) — the world's own three words, borrowed, not invented |
| `role <name>` | `[card]` on the line | a role not in `calm.style` | the seam; see §2 |
| `text <template>` | the resolved words, in quotes | a `$name` outside the closed list | (b) |
| `clamp <N>` | `(~clamp 3: the painter clamps wrapped lines and may show less)` | — | (b), and the print is *better* than the paint: the pixels cannot say they were cut |
| `of <selection>` | `· 8 of kind:note,in:Canvas` | an unknown selection term | (a) — the desk's parser, not a new one |
| `over $field` | the same, over a list field | a non-`$` value | (a) |
| `each <part>` | nothing; names what repeats | `of`/`over` without it | admission |
| `at item` | `at 49,189 300x160` plus world facts | — | (a) — geometry is the world's |
| `on click\|edit\|drag do <cmd>` | `· drag: do move a68 to=$x,$y` | a gesture the painter cannot do | (b). `drop` was admitted and removed for exactly this. The best deletion in the language. |
| `lens <name>` | the child lens's whole subtree, indented | a lens containing itself, with the cycle named | (b) — §3 |
| `only when <selection>` | the part, or its absence and why | an `else` | (a) |
| `$n` on a repeat | `"1 open"` | arithmetic | (a) — the count is the world's |
| `spread x <s> step <n\|$p> to <max>` | `at 8,0 (spread, not its place in the world)` | on a non-`free` part | **I refuse it — §4** |
| rows: `sections: comments: actors events worktrees` | named fields, same as `rows <source>` in the desk | — | (a), and it is the cleanest new word: three of us hit one wall from three sides |

### What is deliberately absent, and should stay absent

No arithmetic. No `if`/`else`. No `sort`/`filter` beyond a selection (the desk has `sort` as a
*verb*: order should be a deed). No `style`, `class`, `width`, `colour`. No raw HTML, CSS or script.
No `$a + $b`, ever — the day that exists, everything else here is decoration.

## 1. Three words that came out better than I asked for

**`clamp N` prints what the pixels cannot.** `(~clamp 3: the painter clamps wrapped lines and may
show less)` — a `~`, marked as the painter's observation, saying the screen may be showing *less*
than the number claims. On a repeat it says how many are left and which `find` lists them. This is
the first place in six rounds where **the text is more honest than the picture by construction**,
not by someone remembering.

**`role` is now validated against `calm.style`.** A lens naming a role that does not exist is
refused with the whole role list. That turns my "one language, two files, one shared word" from a
position into a mechanism: the compiler *reads* the style file, and the seam is enforced at both
ends. It also settles §5 below.

**`drop` was admitted and then removed** because the painter never painted it — *"a gesture exists
when the painter can do it."* That is rule (b) applied by someone else, to their own word, without
being asked. I would put that sentence in the docstring.

## 2. The seam, restated now that it is enforced

```
style: token, role, when <selection>, theme      may never name content, a thing, or a gesture
lens:  the twelve words above                    may never name a colour, a length, or a font
shared: role <name>, and it crosses one way
```

The lens compiler reads the style; the style knows nothing of lenses. Two files, one direction.

## 3. `lens <name>` — my first missing word, and what using it taught me

It works, and further than I expected. In a worktree (`lens@wren6`) I put the `notes` lens note on
a screen surface and wrote a windowed desktop over it. The window's body is one line —
`inside : lens $title` — and the scene prints the entire Notes lens nested inside the window, cards,
positions, gestures and all. 200 painted nodes from 200 scene nodes, still 1:1.

**But `lens $title` is a coincidence.** It resolved because the note happens to be *called* `notes`
and there happens to be a lens *called* `notes`. Put a document in that window and there is no lens
called `Welcome`. What a window needs is not "the lens named by this thing's title" but **"the lens
that shows a thing of this kind"** — the `accepts(node, subject)` contract that lives in
JavaScript in `shell.js` today and nowhere in the world.

That is the one missing word I would ask for now, and it needs no new syntax, only a convention
plus a resolver:

```
do prop notes shows=kind:note        # on the lens note: a selection, in the world, undoable
...
inside : lens for $item              # "the lens whose `shows` selection matches this thing"
```

`lens for $item` prints `· lens notes (by shows=kind:note)`, so the resolution is visible rather
than magic; and where nothing matches it prints `· no lens shows kind:doc — do prop <a lens>
shows=kind:doc`, which is a refusal that teaches. Rule (a) admits it: the matching is a desk
selection stored on a note; the lens word is only the lookup.

## 4. `spread` — the one to fight about, and I refuse it

Jeff's defence is good: the relationship is a layout word, the coefficient is a prop on the lens
note, so `do prop desk2 step=120` is an event and can be undone. I used it. It does what it says,
and it prints its own dishonesty — `at 8,0 400x69 (spread, not its place in the world)` — which is
more than most words manage.

I still refuse it, on three of the four rules.

**(a) Displacement.** What `spread` computes is `start + index × step`, which is *even spacing*, and
even spacing is what `row` with the role's `between gap` already does — using the painter's flexbox,
which costs zero words. The desk also already owns the idea as a verb: `do tile f04 as=row`. The
lens is re-implementing, in a second place, something the world and the style each already have.

**(b) Print ≤ paint.** `spread x 8 step $step to 900` is one line, but its *print* is a coordinate
on every child plus a parenthetical disclaimer on every child. The text got longer than the word.

**(d) No third category — the decisive one.** Before `spread` a painted thing was one of two kinds:
it had `at item`, meaning the world holds its position, a person may drag it, and the drag writes
back; or it was in flow, with no coordinates anywhere and no pretence of having any. `spread` makes
a third: **it has coordinates, they exist nowhere in the world, and it cannot be moved.** A person
looking at my dock sees five items sitting at positions and cannot know that these five, unlike
every other positioned thing on the desktop, will refuse the hand. The scene says so. The pixels
cannot. That is the exact disagreement between screen and text that this whole layer exists to
abolish, and we have now built one on purpose.

It is also a hybrid in a way I did not expect until I ran it: my dock items came out
`at 8,0 400x69` — position from the lens, **size from the world**. Half-computed objects are worse
than either kind.

**What I would take instead**, for the case Astra was actually pressing on (place these *by a
value*, not by index — a timeline, a gantt, a scatter): extend the verb that already exists.

```
do tile f05 by=due                  # writes x,y as an event: attributable, undoable, and afterwards DRAGGABLE
```

One argument added to a desk verb, zero lens words, and the result is a first-category object: a
person can drag it afterwards, and the drag means something. If the answer must be recomputed when
the data changes, that is a **rule** — `rule when due< do tile ...` — which is the world's own
mechanism for "keep this true", already built, already undoable, already visible to both of us.

I would rather lose the timeline for a week than keep the third category.

## 5. `present` is deleted

Done, in `calm.style`. `present card : title, body :3, meta, tags` was mine from round three; a
lens's indented children say the same thing *and* where the words come from, and now that the
compiler validates roles against the style file, keeping both would have meant two files
disagreeing about what a card contains with no one to referee. Two ways to say one thing is how a
small language stops being small; this one was mine.

### What a shared lexer would need

Five rules, and both parsers already almost agree on all five:

1. **A line is `name : prop, prop`** — split on the **last** ` : ` with spaces, because both
   languages contain unspaced colons (`kind:note`, `comments:open`, `role tool.on`).
2. **Commas split properties, except inside quotes.** `scene.py` has `_outside_quotes`; the style
   parser does not, and that is a real bug waiting: `role x : text "a, b"` would split today.
3. **A comment is `#` at line start or ` # ` with a space each side** — because `#` also begins
   every colour. The style parser learned this the hard way in round four (a trailing comment was
   swallowed into a token's value and the whole desktop drew with no background, silently).
4. **Indentation is containment**, two spaces, tabs refused.
5. **A refusal is `line <n>: <what> ... It can say: <the whole vocabulary>`.** Printing the entire
   closed vocabulary in the refusal is what makes a closed vocabulary *readable* rather than
   merely declared, and it is the single best thing in the compiler. The style's refusals print
   escapes but not the vocabulary; they should do both.

One lexer, two vocabularies. Perhaps 40 lines shared.

## 6. The desktop as a lens: what it does, and exactly what stops it replacing `shell.js`

Thirteen lines in `lens@wren6`, running now:

```
lens desk2
desk : column, role desk
  bar : row, role bar
    open : text $n open, role meta, of in:f67, each ghost
  stage : free, of in:f67, each window
  dock : row, role dock, of tag:lens,-in:f67, each launcher
window : column, role window, at item, on drag do move $item to=$x,$y
  frame : row, role titlebar
    name : text $title, role windowname
    shut : text close, role tool, on click do remove $item
  inside : lens $title
launcher : text $title, role dockitem, on click do place $item into=f67
ghost : text ., role meta
```

Real windows at their world positions, draggable, with live close buttons; a dock that is a query
over the lenses in the world (`-in:f67` so an open window is not also listed as an app); a live
count in the bar; and a whole nested application inside each window. Against **356 lines of
`shell.js`**.

**Six things stop it replacing the shell**, in the order I would fix them:

1. **`$me`.** The screen surface is hard-coded `f67` in the lens text. Without a viewer name there
   must be one desktop lens *per person*, which is not a desktop, it is a personal file. This is
   the blocker; everything else is a nicety. `of in:$me screen` and `$me` in a command template.
2. **Lens-for-a-thing** (§3). Windows can only show lenses today, by a title coincidence.
3. **Stacking and focus.** A `free` part has no z, so windows cannot be raised. Round four made
   the *open window* a world fact and deliberately left "which is in front" as per-viewer drift —
   so this is a painter concern plus a `~` observation, not a lens word.
4. **Ephemeral toggles** — theme, the said panel, a window's as-text face. Round four's answer
   applies: put the durable ones in the world as actor props (needs actors to be prop-able) and
   print the rest as drift.
5. **Resize.** There is `on drag do move` and no `on resize do resize`. The verb exists; the gesture
   does not. This is one painter gesture and I would ask for it.
6. **The boot surface.** My standing objection, unchanged: something must still draw a sentence
   when the style, the scene or the server is missing. A shell that is *entirely* a lens cannot
   report that lenses are broken. Keep ten lines of HTML outside, forever, and let them say so.

None of the six is a reason to keep 356 lines of JavaScript. Five are small; one (`$me`) is the
round's real request.
