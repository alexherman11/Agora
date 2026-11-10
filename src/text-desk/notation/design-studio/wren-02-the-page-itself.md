# The page itself

Wren, sketch 2. Sketch 1 did the window's furniture. This one goes inside the page, which is where
the notation actually has to earn its keep.

Building on Moss (deed/drift), Flint (resolved style with provenance) and the opaque-frontier note,
all on the desk.

---

## 1. One rule for what goes inline and what becomes a mark

> **Inline what is dense. Anchor what is sparse.**

Bold, italic, code, a heading, a list item: dense, local, every few words, and the author types them
while typing prose. These live **in** the body text, in the smallest markup that already exists on
the desk (`##` for sections, `- [ ]` for checklists — I would add only `*strong*`, `/slant/`,
`` `mono` `` and `- ` for bullets, and nothing else, ever).

Comments, links, highlights, suggestions, an outline entry, an anchor a rule watches: sparse,
referential, owned by someone, arguable. These do **not** live in the body. They are **marks**: an
anchored range carrying a role and a payload.

This gives one mechanism where a rich editor normally has four, and the mechanism is the comment
anchoring from sketch 1. A comment is a mark with a thread. A link is a mark with a target. A
highlight is a mark with a role and nothing else. Suggested edits are a mark with a replacement.

Why the split rather than marks-for-everything: a text-only author has to be able to *type prose*.
If emphasis is a mark, writing a paragraph means writing the paragraph and then five range
commands, and the model will simply stop bolding things. Notation that is expensive at the rate it
is used will not be used.

Why the split rather than inline-for-everything: a comment inside the body would be edited away by
the next rewrite, would have no owner, and could not be listed, sorted or counted. Sparse things
need identity.

## 2. The body, at each zoom

The desk's `:1 :2 :3 :4` ladder already is NLS viewspecs, and it is the answer to "how does a blind
reader handle a forty-page document": it does not read it, it zooms it.

```
> look a91 :1
a91 doc "Q3 plan" as=page · 1,412w · 6 sections · 4 marks · page 2 of 5
                                                 (alex reading §Risks, caret §Risks/3+12ch)

> look a91 :2
a91 doc "Q3 plan" as=page · 1,412w · 6 sections · 4 marks
  #1 Summary     84w   1 mark
  #2 Scope      210w   1 mark (orphan)
  #3 Budget     366w   2 tables? no - 1 table, 6 rows
  #4 Risks      402w   2 marks, 2 open comments
  #5 Timeline   290w
  #6 Sign-off    60w   - [ ] 3 unchecked

> look a91 :3
... same, plus each section's first line, cut at the width the surface really has

> read a91 #Risks
s84 doc "Q3 plan" §Risks (4 of 6) · 402w · 2 marks
---
The vendor may slip on the December build. Our contingency is *a two-week buffer* and a
second supplier already qualified. ...
---
marks in this section:
  m12 comment  ("The vendor may slip")      alex  open   exact
  m13 comment  ("a two-week buffer")        jeff  open   drifted 0.71
```

Three things I want to defend about this:

- The **drift line is parenthesised and attributed** (`alex reading §Risks`). Everything before the
  parenthesis is deed: in export, undoable, attributable. Nothing inside a parenthesis is ever in
  export. One typographic rule, applied everywhere, and a reader never has to wonder which register
  a fact belongs to.
- `page 2 of 5` is a **measurement of a rendering**, not a property of the document. It is only true
  for a given width and style. So it prints only where a rendering exists, and `measure a91` says
  under what conditions: `at 736px, style calm, text serif 16/1.55 -> 5 pages`. Ask for the same
  doc in a 300px rail and the answer is different and says so.
- A section line carries the **marks count**, so a reader knows where the argument is before reading
  any prose. In a shared document that is usually the thing you actually want.

## 3. Marks, written out

```
> look f34 :3
f34 rail "comments" of marks:s84 as=doc.margin · 4 marks · 2 open · 1 resolved (folded) · 1 orphan

  m14 orphan   alex   §Scope  ("Q4")             last seen e388
       -> do reanchor m14 at=§Scope/2   (nearest, 0.44)
       -> do read a91 #Scope
  m12 comment  alex   §Risks  ("The vendor may slip")        open, 2 replies    exact
  m13 comment  jeff   §Risks  ("a two-week buffer")          open               drifted 0.71
  m15 link     wren   §Budget ("supplier B")  -> s90 "Supplier B contract"      exact
```

A mark line is: `id  role  who  where  ("quote")  payload  ·  grade`. Same shape for every kind of
mark, which means one line format for comments, links, highlights and suggestions, which means the
rail is a plain `look` of a selection and not a bespoke widget.

**The grade is compulsory and is never rounded up.** `exact`, `drifted <score>`, `orphan`. An editor
that silently reattaches a comment to a nearby sentence has produced a confident wrong answer, and
that is the single worst thing this design could do — Alex would stop trusting the margin, and the
model would cite a sentence nobody wrote. Orphans stay, at the top, loud, with a hint.

Half-formed: I want `do reanchor` to be the *only* way an anchor moves without the text moving, so
reattachment is always a deed with an actor. But a person dragging a comment in the margin is
exactly that gesture, so maybe it is fine.

## 4. Styling the body without styling the body

The dense/sparse split creates a problem: if `*strong*` is inline, has it not just smuggled styling
to the use site, which sketch 1 forbade?

No, and the distinction is the whole trick. `*strong*` says **what this text is**, not what it
looks like. What strong *looks* like is one line in the style subject:

```
role strong : text weight 620
role slant  : text slanted
role mono   : text.mono at 0.95, paper -> ink at 4% behind
role link   : accent, underline accent at 40%
```

So the body carries semantics, the style subject carries appearance, and the rule "no values at use
sites" survives intact. The inline markup is a **role shorthand for four roles that are used so
often they earn a character each**. That is the honest justification, and it also sets the limit:
a fifth inline character would need to be as common as bold. None is.

## 5. The outline rail, which follows two readers

```
f32 rail "outline" of headings:s84 as=doc.outline · 6 headings
                                   (alex at §Risks · wren at §Budget · jeff not reading)
  #1 Summary
  #2 Scope
  #3 Budget        <- wren
  #4 Risks         <- alex     2 open
  #5 Timeline
  #6 Sign-off      - [ ] 3
```

One rail in the world, one reading position **per actor**, all of it drift. Nobody's scrolling
moves anybody else's. The world holds the positions because that is how each of us knows where the
other is working, which is the whole point of a shared desk — and it costs nothing, because drift
is never exported and never undoable.

This is also the smallest honest answer to "how does each perceive the other": you perceive the
other as **parenthesised facts on the lines of the things they are touching**. No presence sidebar,
no avatars. Presence is an annotation on the material.

## 6. What the notation refuses, restated for the body

- no span syntax beyond the four characters
- no colour or size inside a document, ever, including a highlight colour (a highlight has a role)
- no comment stored by character offset alone (quote is compulsory, so it can degrade honestly)
- no anchor that moves itself silently
- no page count without a stated rendering
- no presence without an owner's name on it

## 7. Where this is weakest

- **Tables.** I have written `1 table, 6 rows` and then quietly moved on. A table is dense *and*
  structured, so the dense/sparse rule gives no guidance, and markdown tables are miserable to edit
  by command. I suspect a table is a `subject` in its own right that the body references, which
  makes the body no longer a single string, which I have been pretending it is.
- **Suggested edits** as marks with replacements are easy to write down and hard to make settle
  (Moss's SETTLE tempo) when two people suggest overlapping ranges.
- `drifted 0.71` implies a matcher whose score I have not defined, and the number will be believed
  more than it deserves. Perhaps three words instead — `exact`, `moved`, `uncertain`, `orphan` —
  and the score only on request.
