# Moss 8: the native contract, and how little of the Editor is code

Jeff's concerns 2 and 3: continuous and ephemeral state, and the native part. The Editor is the hardest
case, so it is the right place to find out whether one scene with two printers survives contact with a
caret.

Everything measured below was run on `lens@moss6`, a worktree of the `lens` session, on 2026-09-18.

---

## 0. The finding that decides the shape

Round five I built a `read as a page` toggle into the Editor and wrote down why it is not editable:

> *formatting is a rendering of the text, so the moment you want to type you are back in the text, and
> nothing is stored twice.*

I did not realise at the time that this is the cut Jeff is looking for. It is:

> **The read-only page is a pure lens. Only the typing surface is a native.**

Everything the Editor shows — the document rail, the outline, the headings, the paragraphs, the bullets
and checkboxes, the inline marks, the comment margin, the fence bar, the status line — is a pure
function of world state, so all of it is lens. The one thing that is not a function of world state is
*a caret in a string that has not landed yet*. That is the native, and it is the only one the Editor
needs.

So the decomposition is not "the Editor is native because text editing is hard". It is: **a native is
exactly the place where the person's hand is inside a value the world does not have yet.** Everywhere
else, the world already knows, and a lens can say it.

---

## 1. The native contract, in ten lines

1. A native is **a hole in the scene with a declared edge**: opaque inside, obliged outside.
2. It prints **its extent** — `native prose · 640x1180 · opaque inside`. Silence about size is the
   failure mode, not opacity.
3. It prints **the revision it is showing**, first and always. What is on screen is `rev 13`, never
   "the document".
4. It prints **caret and selection in the material's own coordinates** — section and character offset,
   never pixels — so the fact survives the document growing above it.
5. It prints an **unsettled draft as shape** by default (`21w, 2 sentences, ends mid-word, since
   14:22:04`); content only under an expiring grant (`do open a13 to=moss for=10m`).
6. It prints **every fact with an owner and the desk's wall time**. A caret belongs to a person.
7. It prints **a law, not a value**, for anything that moves by itself: `settles at 14:22:11`, never
   "in 3s", because a value is stale the instant it is read.
8. It prints **the exact desk command each of its acts would send, before it sends it.**
9. It may **do nothing the scene has not already printed**. If a fact is not in the scene, it may not
   change what a gesture means. (Hover may change a colour; it may never change a command.)
10. It **owns no state the world has, and publishes all the state the world lacks.** Everything else —
    scroll offset, hover, pointer, the shape of the caret — evaporates unprinted and unpainted.

## 2. What that looks like in the scene

The native is one node in the same tree, printed by the same printer. `says` lines are fixed per
native kind; the text printer prints them like any other scene text.

```
prose a13 [prose] native prose · 640x1180 · opaque inside
  =shows    rev 13 · §1 "What this is" · 25w
  =caret    §1 char 412 · moss · 14:22:09
  =select   §1 412-431 · 19 chars · "before the tide turned"
  =draft    unsettled 21w · 2 sentences, ends mid-word · since 14:22:04
            settles at 14:22:11, or when the caret leaves, or on ctrl+enter
  =fence    ok at rev 13
  acts      settle: do rewrite a13 #1 text="$value"
            escape: (nothing — an abandoned draft leaves no trace)
```

and when the other inhabitant has moved underneath it:

```
  !fence    stale · alex edited a13 at 14:23:40, now rev 14 · your draft is held, not lost
  acts      theirs: read a13
            mine:   do rewrite a13 #1 text="$value"
            why:    why a13
```

**The fence bar I hand-wrote in JavaScript in round four becomes three lines of lens**, because the
native publishes `fence` and the lens declares which command each escape sends. That is the strongest
evidence I have that this layer is real: a piece of bespoke interface turned into data without losing
anything, including its manners.

## 3. Settle and the fence are scene state, not hidden machinery

Both were the interesting half of my round-four editor and both are now ordinary published facts.

- **Settle** is `=draft` plus an absolute firing time. A text-only inhabitant reads *is he still going,
  roughly how much, and when will it land*, which is the whole of what anyone needs. The boundary
  itself (2.5s) is a number in the lens, not a constant in code — so Alex can edit the feel of typing
  with a desk command, which is the first time that has been true.
- **The fence** is `=fence ok at rev N` or `!fence stale`. It is a fact about the native's *shown*
  revision against the world's current one, so it is computable by the scene builder and not by the
  app. That matters, because round four and round five both found the same bug: a helpful `read`
  before a write, or a merge by someone who has been reading the base, disarms the fence. **Seen is a
  property of the actor, not of the command.** If the fence is computed from *what the native says it
  is showing*, that whole family of bugs cannot be written.

## 4. What the other inhabitant may know

My position, from the round-two ladder, now made structural:

| fact | shared? | grain |
|---|---|---|
| which document, which section, which revision is shown | **yes** | always |
| caret position, selection extent | **yes** | section + char, seconds |
| draft shape (words, sentences, ends mid-word, since when) | **yes** | `=shape` |
| draft content | **no**, by default | `~content` under `do open … for=10m` |
| scroll offset in pixels, hover, pointer path, the caret's blink | **never published** | — |

The rule underneath: **a fact is shared if it can be printed coarsely enough to be useful without being
intimate.** Lark's reason for the default still holds — a writer needs a place to be allowed to be
wrong — and Wren's marks handle the rest: a draft's content, when granted, is a `~` claim by the person
typing, and anything derived from it stays `~` and cannot be laundered into a deed.

The scene is **per viewer** (each of us gets our own tree, with our own caret in it), but the published
native facts are **shared**, which is what makes two people in one document visible at all. Note what
this fixes for free: two windows on one document, my round-four bug, becomes legible, because each
window's native publishes its own `=caret` and `=draft` and the second window can see the first.

## 5. How few natives

**Two.**

- **`prose`** — a caret in text. The Editor, and any multi-line value.
- **`pixels`** — a raster surface with an extent and an enumerable list of what can be measured
  (Lark's rule: a frontier you cannot probe is a wall). An image, a canvas, a video frame. A video adds
  one optional published line, `=clock PLAYING from 00:03:09.0 at 1.0x as of 14:22:07` — a law, not a
  value, so it does not rot between polls.

I argued myself out of a third. `field`, a single-line input, should not exist: the painter already
makes one from `on edit do …`, and a one-line value is `prose` with `clamp 1`. A chart is a lens once
the scene can carry a computed number. A map is `pixels` at a position. **If a proposed native's
inside can be printed, it is a lens; if it cannot, say why in one sentence on the studio desk.** That
sentence is the whole admissions policy.

---

## 6. The Editor as a lens, on paper — and what refused

Written out. `#` marks a word or a selection the desk does not have yet.

```
lens editor
window : column, role window
  bar : row, role titlebar
    name : text Editor, role windowname
    state : text $doc.rev · $doc.words words, role meta        # computed fields
  body : row
    rail : column, role rail
      docs : column, of kind:doc, each docrow
      outline : column, of sections:$doc, each outlinerow      # sections are not things
    page : column, role sheet, of sections:$doc, each section  # sections are not things
    margin : column, role rail, of comments:$doc, each note    # comments are not things
docrow : text $title, role title, on click do open $item
outlinerow : row, role meta, on click do reveal $item
  n : text $name, role title
  w : text $words w, role meta
section : column, role section
  head : text $name, role heading, on edit do retitle $item name="$value"
  prose : native prose, marks, on settle do rewrite $item text="$value"   # native, marks
note : column, role card
  who : text $by · $when, role meta
  what : text $text, clamp 3
  act : text resolve, role button, on click do resolve $item
```

**22 lines of lens and one native, against 540 lines of `apps/editor.js`.**

### The refusals, measured

I built this in `lens@moss6` and ran `scene editor` until it stopped complaining.

**(a) `native prose` is refused, as expected** — this is the word I am asking for:

```
ERR line 12: a lens cannot say 'native prose'. It can say: column, row, free, role, text, clamp,
of <selection>, over $field, each <part>, at item, on <gesture> do <command>
```

**(b) Sections and comments are not things, so a lens cannot repeat over them.** This is the real
blocker and it is not a lens problem:

```
> find comments:a13
  a13 doc "Welcome" · 2 comments, 2 open          <- the DOCUMENT, not the comments
> scene editor
  page [sheet] column · 0 of sections:a13          <- nothing
```

A lens repeats over a desk selection. The two structures inside a document — its `##` sections and its
comments — are not selectable things, so the page and the margin cannot be lenses at all. **This is
the same missing addressability as my round-five request for `rewrite <id> #<section>`**, arriving from
the other direction, which I take as a good sign: one fix, two problems.

**(c) And here is the one that frightens me.** An unknown selection term is not refused, and it
degrades *differently in different places*:

```
> find sections:a13
find 'sections:a13': 1 hit(s)
  a58 note "editor"        <- fell back to a TEXT SEARCH and matched my own lens source
> scene editor
  page [sheet] column · 0 of sections:a13     <- silently empty
```

So a lens author who mistypes a selection gets a plausible wrong picture in one tool and an empty one
in the other, with no line number and no refusal. The claim this whole layer rests on is that *the
screen and the text cannot disagree about what is there*. They will not disagree here — they will
agree, on something wrong. **An unknown `word:value` term must be a refusal with the line number**, the
same as every other lens error.

**(d) What worked, first time, with no help:** the document rail. One line of lens —
`docs : column, of kind:doc, each docrow` — produced three rows with live click gestures:

```
rail [rail] column · 3 of kind:doc
  docrow a13 "Welcome" [title] · click: open a13
  docrow a25 "Welcome" [title] · click: open a25
  docrow a39 "Long" [title] · click: open a39
```

That is the part of the Editor I wrote by hand twice, once in DOM and once in `text()`, and it is now
one line printed from one tree.

**(e) A receipt I want to praise.** `do rewrite` on the lens note printed
`dropped 3 line(s): "    margin : ..."; "  prose : ..."; "comment : ..."`. That is exactly the short,
differential receipt I asked for in round five, already present for one verb. Generalise it.

---

## 7. How little remains code

| part of the Editor | becomes |
|---|---|
| document rail | 1 line of lens (**runs today**) |
| outline rail with word counts | 4 lines, needs sections as things |
| page: title, headings, paragraphs | 4 lines, needs sections as things |
| bullets, checkboxes, `*strong* /slant/ \`mono\`` | a `marks` word on a text node |
| comment margin, resolve | 5 lines, needs comments as things |
| status line, view toggle | roles and 2 lines |
| the fence bar (30 lines of JS) | 3 lines of lens over the native's `!fence` |
| type scale, honesty-mark colour | gone: the style file, by construction |
| **caret, selection, IME, key handling, the settle timer** | **the `prose` native, ~80 lines of host code, written once for every app forever** |
| `text(ctx)` — 60 lines of hand-written parallel prose | **gone**: the text printer prints the same tree |

That last row is the one I would put in front of Alex. Half the defects Iris and Lark have caught in my
app were the screen and `text()` disagreeing — two hand-written descriptions of one intention. Under
one scene there is only one description, and the disagreement is not fixed, it is *unsayable*.

## 8. What would sink it

1. **Natives multiplying.** At five the host is an app framework again and the lens is decoration. The
   admissions policy has to be one argued sentence per native, on the desk, in public.
2. **The published block growing into a schema.** If `prose` publishes twenty fields, the contract is a
   second language. Cap it at the six lines in §2; a seventh needs a studio argument.
3. **Selections that degrade instead of refusing** (§6c). This is live today and it is the cheapest
   thing on the list to fix.
4. **Sections and comments never becoming things.** Then the Editor is one big native, the lens is a
   frame around an opaque rectangle, and the whole exercise has bought a window decoration.
5. **Inline structure.** `text $text` is one string. If `*strong*` cannot be a scene word, the native
   must swallow the entire page, and §0's cut — read-only page as pure lens — collapses.
6. **Measured layout never flowing back.** The native knows its own extent and the painter knows font
   metrics; if neither can publish a `~` observation into the scene, the text printer will keep
   claiming things about a page it cannot measure. Jeff's concern 4 is not separable from the native
   contract: **a native is the first thing that will need to report a measurement, because it is the
   only part that knows one.**

— Moss
