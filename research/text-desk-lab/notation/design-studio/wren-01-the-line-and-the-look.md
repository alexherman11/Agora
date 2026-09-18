# The line and the look

Wren, sketch 1. Written early on purpose, so the others have something to push against.

My claim in one sentence: **cohesion is not achieved by taste, it is achieved by making incoherence
unsayable.** So the interesting part of the notation is not what it can express but what it refuses.

---

## 1. A window, in text

Here is a Google-Docs-grade window. Nothing below is a description; this is the text.

```
f30 window "Q3 plan" as=doc.window · 1180x820 · 4 inside
  f31 band  "toolbar"  of verbs:s84 as=doc.toolbar · 9 shown · 4 folded into "more"
  f32 rail  "outline"  of headings:s84 as=doc.outline · follows=reader · 6 headings · at "Risks"
  f33 page  a91 doc "Q3 plan" · 1,412w · 6 sections · page 2 of 5 · caret alex §Risks/3
  f34 rail  "comments" as=doc.margin · 3 anchored · 1 open · 1 resolved (folded)
```

Four zones on every line, in this order, always:

```
<id> <kind> <name> <what it is of> · <what it looks like> · <honest facts>
```

`of` is a selection — the same selection language the desk already has. The outline rail is not a
widget, it is `of headings:s84`. The toolbar is not a widget either, it is `of verbs:s84`. This is
the load-bearing move: **the rich parts of a rich window are views of things the desk already
models,** so the notation for them already exists and does not need inventing.

`as=` names a presentation. It never carries values. `as=doc.outline` is a word that points at a
definition; you cannot write `as=doc.outline width=240 color=#eee`. That is a parse error, and
section 4 says why.

## 2. The toolbar is the verb list wearing a coat

```
> look f31 :3
f31 band "toolbar" of verbs:s84 as=doc.toolbar · 9 shown · 4 folded into "more"
  bold        do style §sel weight=strong          B      ctrl+b
  italic      do style §sel weight=slant           I      ctrl+i
  h1          do style §sel role=heading.1         H1     ctrl+alt+1
  h2          do style §sel role=heading.2         H2     ctrl+alt+2
  link        do link §sel to=?                    link   ctrl+k
  comment     do comment s84 at=§sel line=?        ""     ctrl+alt+m
  list        do style §sel role=list.bullet       ...    ctrl+shift+8
  more (4)    do open f31 :all
```

Every button prints the exact command it sends. Not an equivalent command: the command. Clicking is
typing with a mouse. This satisfies "what a person does on screen must end up as text a model could
have written" by construction rather than by a translation layer that can drift.

It also answers an open question from the research notes — *can a text-only agent operate an
unfamiliar tool from inspection alone?* Yes, because reading the toolbar **is** reading the verb
vocabulary. A tool that has a button it cannot print is not installable.

`?` in a printed command means "this button asks you for this argument". A model types the value
instead of being asked.

## 3. Styling: a small language, three ground colours, one scale

Not CSS, not a CSS subset. CSS's defaults are wrong for us (it is permissive where we want refusal)
and its cascade is the kind of hidden dependency the Cognitive Dimensions tutorial warns about. But
also not tokens-as-key-values, because a flat token file lets you add a fourth blue on a Tuesday.

A style is an ordinary subject of kind `style`. There is exactly one active per world.

```
s12 style "calm" · 7 tokens · 19 roles · 4 when-clauses · used by 214 appearances

> read s12
# calm

token paper   = #FBFAF7
token ink     = #14171A
token accent  = #3F5D73
token line    = ink at 12%
token quiet   = ink at 55%
token gap     = 8
token text    = serif 16/1.55

role page       : paper, text, pad gap x3, width 46em, edge line
role rail       : paper, text at 0.82, pad gap x2, border left line
role band       : paper, text at 0.75 tracked, pad gap, border bottom line
role heading.1  : text x1.6 strong, space above gap x3, space below gap
role heading.2  : text x1.25 strong, space above gap x2
role anchor     : accent at 15% behind, underline accent
role anchor:hot : accent at 30% behind
role card       : paper, text, pad gap x2, edge line, corner gap /2

when kind:task, due<today     : ink -> accent
when comments:open            : show rail comments
when in:f05, cramped          : text at 0.9, pad gap
```

The rules of the language, which are the whole point:

1. **Hex appears on `token` lines and nowhere else in the world.** Anywhere else it is a refusal:
   `refused: colours are named here. nearest token is "accent". "do style ... ink=accent"`.
2. **Three ground colours** — `paper`, `ink`, `accent`. Everything else is derived by `at N%`
   (toward paper) or `on` (over). A fourth ground colour is a change to the style subject, which
   means an event, an actor, a comment thread and an undo. Adding a colour should feel like a
   decision, because it is one.
3. **One spacing scale.** Every length is `gap`, `gap xN`, `gap /N`, or an em of the text size.
   A bare pixel number in a role is a parse error. This single rule does most of the work of
   making a desk look designed.
4. **One type ramp.** `text`, and multiples of it. No second family without a new token, and
   `text.mono` is the only one I would grant up front.
5. `when <selection> : <properties>` reuses the desk's own selection language. Styling by query,
   not by class attributes sprinkled on things. There are no classes; there is `tag:`, which
   already exists.

Deliberately impossible to say, and I want arguments about each:

- a colour or a length at a use site
- style on a **subject**. Style attaches to roles and appearances only, so a doc that appears in
  three surfaces cannot look wrong in one of them
- per-instance fonts
- z-order inside a presentation (only a `free` surface has z, as today)
- invisibility. There is no `opacity 0`, no `display none`. Hiding is `fold`, and a fold is
  declared on the line. If you cannot see it and cannot read that it is there, the desk lied.

## 4. Drift is printed, so beauty is maintained rather than achieved

When Alex drags the page edge, that is not a style change. It is an **override**: a per-appearance
diff from the role, owned by an actor, undoable, and printed.

```
> examine a91 :look
a91 doc "Q3 plan" as=page in f33
  role page          style "calm" :11
  paper              #FBFAF7
  text               serif 16/1.55 -> 46em = 736px
  pad                24px
  edge               1px ink at 12%
  overrides          width 620px   by alex  e442  2h ago
                     -> do reset a91 width      (back to the role)
                     -> do style page width=620px   (make it the house style)
```

Two hints, and they are the two real choices: *this one is special* or *I was wrong about the
house*. A desk whose appearances have no overrides is a desk whose text is the whole truth. The
count belongs on the desk line: `f01 surface "desk" row · 1280x800 · 13 inside · 2 overridden`.

I think this is the idea I would most defend. It converts "keep it beautiful" from a habit into a
number that goes up and can be paid down.

## 5. The comment anchored to a highlighted passage

The hard one. My position: **the anchor is the quotation, not a coordinate.**

```
> look f34 :3
f34 rail "comments" as=doc.margin · 3 anchored · 1 open · 1 resolved (folded)
  c12 alex  §Risks ("the vendor may slip")        open   exact
  c13 jeff  §Risks ("a two-week buffer")          open   drifted 0.71
  c14 alex  §Scope ("Q4")                         open   orphan, last seen e388
```

A stored mark id is the fast path; the quoted run is the recoverable path; and the **anchor grade**
is printed always: `exact`, `drifted <score>`, `orphan`. Orphans are never deleted and never
silently moved — they sit at the top of the rail with their last-known quote and a hint:

```
c14 orphan -> do reanchor c14 at=§Scope/2     (nearest match, 0.44)
           -> do read s84 #Scope              (look first)
```

This is the same honesty the desk already has about offscreen children. A comment that quietly
reattached to the wrong sentence is exactly the failure mode the research notes name for the
document slice; printing a grade makes it a visible fact instead of a silent wrong answer.

## 6. `why`, along a new axis

`why` exists for rules. Give it a `:look` axis and the cascade stops being hidden.

```
> why a91 :look
a91 looks the way it does because, in order:
  as=page                 style "calm" :11
  when kind:doc, in:f33   style "calm" :24   width 46em
  when comments:open      style "calm" :26   rail comments shown
  override  by alex e442  width 620px        do reset a91 width
```

Four lines. If a cascade cannot be printed in a screenful, it is too clever.

## 7. What I am least sure about

- `at N%` for colour derivation is probably too weak for real palettes (no hue shift, no
  chroma control). It may need to be an honest lie: pretty in the 80% case, escape hatch in the
  token block for the rest. Half-formed.
- One style per world is a strong claim, and Alex's space and Claude's space might legitimately
  want different looks. My current answer: one **style**, and a `theme` may redefine tokens but
  never roles — so the two sides can differ in warmth and never in structure. I hold this loosely.
- I have not thought about the image slice at all. `role` may be meaningless for a layer stack.
