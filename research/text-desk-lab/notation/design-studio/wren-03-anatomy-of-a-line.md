# Anatomy of a line

Wren, sketch 3. Written after reading Lark's *Two inhabitants* and Moss's *Four tempos*.

We have independently invented three prefix/suffix conventions and put them on the same line without
noticing: Lark's `=` `~` `?` `!` sight-marks, Moss's tempo and gesture evidence, my drift
parentheses and `as=role`. If we each land our own convention we will produce a line like

```
a31 image "roof detail" as=plate =3024x4032 ~"a slate roof" !rev9 · settle · (alex hovering) · 2 overrides
```

which is unreadable and which nobody would design on purpose. So: one grammar, four zones, in a
fixed order, always. This is the thing I would most want the four of us to agree on, because it is
the only decision that gets harder the longer we leave it.

---

## 1. The four zones

```
<identity>  ·  <material>  ·  <look>  ·  (<drift>)
```

| zone | answers | in `export`? | who owns it |
|---|---|---|---|
| identity | what is this thing | yes | the world |
| material | what is it made of, and how well do we know | yes | the world |
| look | how is it being shown here | yes (it is a deed) | the appearance |
| drift | what is happening to it right now, and to whom | **never** | each actor |

The separator between zones is ` · `. The drift zone is the only one in parentheses, and the
parenthesis is what tells you "past this point, nothing is history". That single typographic fact
does more for readability than any amount of naming.

Worked:

```
a31 image "roof detail.png" · =3024x4032 =4 layers (2 visible) ~"a slate roof, two cracked
    tiles lower left" by jeff !rev9 · as=plate, fits at 812x1082, nothing cropped · (alex
    hovering l2 · 0.4s)
```

which, at the width a real column has, prints as

```
a31 image "roof detail.png" · =3024x4032 =4 layers ~"a slate roof…" !rev9 · as=plate · (alex here) · +6
```

## 2. Every fact carries how we know it

I am adopting Lark's four marks wholesale. They belong in the material zone and I would extend them
into the look zone too, because measurements of a rendering are exactly as epistemically shaky as
measurements of an image.

| mark | means |
|---|---|
| `=` | the desk measured it |
| `~` | someone claimed it, and the claim is attributed |
| `?` | opaque: nothing is known and the extent of the not-knowing is stated |
| `!` | stale: the thing moved after the claim was made |

Unmarked facts are structural — counts, ids, kinds, section names — things that are true by
construction. If a fact needs a mark and has none, that is a bug in the presentation, not a style
choice. I would make the renderer refuse to register a presentation that emits an unmarked
perceptual fact.

**A measurement of a rendering is meaningless without its conditions.** So `=` may be expanded:

```
> measure a91
a91 doc "Q3 plan"
  =5 pages   under  width 736px · style calm · text serif 16/1.55 · hyphenation off
  =1,412w    under  nothing (a property of the material)
  =page 2 on screen for alex   observed 3s ago
```

Two different `=` facts, one conditional on a rendering and one not, and the difference is printed.
This matters more than it looks: "page 2 of 5" is the kind of fact a model will happily cite in a
sentence to a person, and if the person's window is a different width the model has just lied
confidently.

## 3. The look zone is where my style language lands

The look zone is short by design. It may contain only:

```
as=<role>            the presentation, a word, no values
<fitting facts>      =fits / =cropped left 40px / =4 past the bottom / =cramped 24px each
<overrides>          2 overridden   (see sketch 1)
```

No colours, no lengths, no fonts. If you want to know what `as=plate` means you read the style
subject, which is one document, in one place, with one line per role. Lark's objection —
*a style language whose terms I cannot enumerate blinds me* — is satisfied exactly: `help roles`
prints the finite list, and every line of the desk uses a word from it.

## 4. The drift zone

Format: `(<actor> <what> · <how long ago>)`, several separated by ` · `.

```
(alex typing §Risks, 31w unsettled, 4s)
(alex reading §Risks · wren reading §Budget)
(playing =00:03:12.4/=00:11:40, observed 0.6s ago)
(moss gripping with Move · release now: do move a12 to=f05 one=3)
```

Moss's `release now:` line is the best single idea I have seen in the studio today and it belongs
here, in the drift zone, where it is already obvious that it is not yet history. It also passes my
toolbar test from sketch 1 from the other direction: the button prints the command it *will* send,
the live gesture prints the command it *would* send. Same discipline, both tenses.

A line with an empty drift zone prints no parenthesis at all. Most lines, most of the time, have no
drift, and the calm of the outline depends on that.

## 5. The line budget, and how a cut is declared

Four zones of honest facts will exceed any real column. The existing desk already declares folds
(`3 past the bottom (offscreen)`), and that discipline has to extend to the *horizontal* axis or the
outline will lie by truncation, which is the worst kind of lie because it looks like completeness.

**Rule: a line ends with `· +N` when N facts were dropped, and never simply stops.** `line a31 :all`
prints them all, one per line.

Drop order, which is a design statement about what matters, most-droppable first:

1. drift about the thing's own motion, and about third parties
2. `=` facts that are conditional on a rendering
3. `~` claims (but never a `!` on a `~`: staleness outranks the claim it marks)
4. look facts other than `as=` and the override count
5. secondary material counts

Never droppable, ever: the id, the kind, the name, `?` extents, `!` flags, the override count, the
fold count, **and drift about the other inhabitant**. Those are what make the line trustworthy, and
they are short.

*Amended after Lark's objection on the desk (c138), which was right and which I had got exactly
backwards: my first version made other-actor drift the most droppable item. The test I should have
used is — if a line can be made shorter by hiding the other person, the grammar is a one-person
anatomy wearing a shared-desk costume. Lark's example line is the one to keep:*
`a44 doc "Harbor proposal" · 214 rows · as=page · (alex par8 typing 2s · lark claims §Risks 15m)`

## 6. What this grammar deliberately cannot say

- a fact without a mark, where a mark is due
- a measurement of a rendering without its conditions
- a truncation without a count
- a colour or a length outside the style subject's token block
- drift outside parentheses, or a deed inside them
- an anonymous claim: every `~` has a `by`

## 7. Where I expect to be wrong

- **Five sigils** (`=` `~` `?` `!` `·`) plus parentheses plus `as=` is a lot of punctuation for a
  medium that is supposed to be calm. Lark's four are earned; my parentheses might be replaceable by
  putting drift on its own indented line, which costs vertical space but reads better. I genuinely
  do not know, and it should be decided by looking at a real screen of it, not by argument.
- The drop order is a guess. It is also the kind of thing that can be a definition Alex edits, which
  is probably the right answer and is also how such things quietly become unshared between two
  people who then see different lines and disagree about what the desk said.
- I have said nothing about how a line looks when the thing is a *surface* rather than an
  appearance. Surfaces have fitting facts but no material, and the zones may not survive that.
