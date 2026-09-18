# Flint: the sceptic's port

I rewrote Notes as a lens until it hit the wall, then turned my Bug triage app — the one that stopped in
round five because it had no window — into a lens of its own. Everything below was run, not reasoned.

Session: `flintlens` (a copy of `lens.pickle`). Lenses `notes5` and `triage`.
Pages: `lens.html?session=flintlens&as=flint&lens=notes5` and `…&lens=triage`.

---

## 1. The counts

| | lines |
|---|---|
| `apps/notes.js` (my app, five rounds of work) | **601** |
| lens `notes5` | **14** |
| lens `triage` (a whole application) | **21** |
| the fixed host, shared by every lens ever written: `scene.py` 191 + `lens.js` 77 + `lens.html` 30 | **298** |

The honest reading: 14 lines do not do what 601 lines do — §3 is the list of what is missing. But of the 601,
the part that draws cards, moves them, renames them, retitles, rewrites, tags, links and lists relations is
the 14. The rest is honesty machinery, computed geometry and per-viewer state, and §3 says which of those
should come back as words and which should not come back at all.

And the 298 is spent once. That is the number that actually matters, because `triage` cost 21 more lines and
nothing else.

---

## 2. What worked, including two things I did not expect

The lens, entire:

```
lens notes5
window : column, role window
  bar : row, role titlebar
    name : text Notes, role windowname
    hint : text drag a card · click a title to rename · drop one card on another to link, role meta
  canvas : free, of kind:note,in:Canvas, each card
card : column, role card, at item, on drag do move $item to=$x,$y, on drop do link $item $other as=refers
  title : text $title, role title, on edit do retitle $item title="$value"
  body : text $text, clamp 3, role body, on edit do rewrite $item text="$value"
  tags : row, over $tags, each tag
  out : column, of links:$item, each linkrow
  mark : text mark, role tag, on click do tag $item add=marked
tag : text $it, role tag
linkrow : text -> $title, role meta
```

**Relative selections work, and I was wrong about them.** My first probe used `of kind:task` inside a card
and got the same result under every card; I wrote "no way to select things related to this item" in my notes
and then tested it properly. `of links:$item` substitutes the item and evaluates per card:

```
card a07 … 
  out a07 column · 3 of links:$item
    linkrow a09 "-> Notes should feel spatial" [meta]
card a27 …
  out a27 column · 0 of links:$item
```

That is the single most important thing in the grammar and it is already there. Anything the desk's selection
language can reach from a thing — links, comments, contents, things in the same surface — a lens can show per
item, with no new word. It is the thing that makes a lens more than a template.

**A button is now a declared gesture, not an overloaded tag.** In round three I found that the desk already
had buttons and they were tags, and complained that control flow therefore lived in the data field. In a lens
it is one clause — `mark : text mark, role tag, on click do tag $item add=marked` — and the text printer
prints the command it will send:

```
mark a07 "mark" [tag] · click: tag a07 add=marked
```

A text reader learns what the button does by reading, and can do the same thing by typing the same line. That
closes a thing I filed two rounds ago, and it closes it better than my request did.

---

## 3. The wall list, in order of importance

Each is a **missing word**, a **native part**, or **should not exist**.

### 1. `[:100]` — an undeclared truncation inside the honesty layer. *Should not exist.*

`scene.py:160`:

```python
bits.append('"' + " / ".join(shown)[:100] + '"' + (f" (+{len(t) - len(shown)} line(s) clamped)" if len(shown) < len(t) else ""))
```

The `(+N line(s) clamped)` marker fires on the **line** count and never on the **character** cut. From my own
scene, verbatim:

```
body a50 "An application authored entirely with desk commands. / No JavaScript was written for this. Drop a #b" [body]
```

Cut mid-word at `#b`, with nothing said. This is the one habit the whole system exists for, broken in the
printer whose only job is to have it. It is four characters to fix and I would fix it before anything else.

### 2. `clamp` means two different things, and this breaks the central claim. *A definition, not a word.*

> **Marked honestly, because I have spent six rounds insisting on this distinction and it applies to me:**
> this one is `~`, not `=`. I read both implementations; I did not measure the screen. Iris has been asked to
> count the visible lines against the text pane (`a608`). If she finds them equal, the finding is wrong and the
> claim survives. Everything else in this file I ran.

`scene.py` clamps **source lines** (`t = n["text"].split("\n")`). `lens.js:32` sets `webkitLineClamp`, which
clamps **rendered, wrapped lines**. A 400-character single-paragraph body is **one** source line — never
clamped in the text, printed to 100 characters and cut silently — and about **six** rendered lines, clamped to
2 on screen with the rest gone.

So the two printers show different content from one tree, and neither declares it. The claim is *"they cannot
disagree about what is there, because neither has any other source."* They have the same source and different
**semantics for the same word**, which is enough.

> **One tree guarantees a shared vocabulary, not a shared meaning.** Wherever a scene word's meaning depends
> on the medium — lines, size, position in flow, what fits — one tree guarantees nothing, and the word needs a
> definition in one unit that both printers can honour, or an admission that one of them is guessing.

If `clamp` is rendered lines, the text printer cannot compute it and must say so: `~ clamped to 2 rendered
lines; I cannot know which`. If it is source lines, the painter must not use `webkitLineClamp`.

### 3. `at item` is not refused inside a flow parent. *Should be a refusal.*

```
root [window] column
  flow column · 8 of kind:note,in:Canvas
    card a07 [card] column at 510,353 449x511
    card a29 [card] column at 8,66 184x50
```

The scene says `column` and then gives every child an absolute box. A column that positions its children is
not a column, and a text reader ordering by the printed coordinates gets a different order from the one on
screen. Nothing refuses it. `at item` in a non-`free` parent should be refused with a line number, which is
what the grammar does for everything else it disallows.

### 4. `$n` is documented and does not work. *A bug, then a word.*

The docstring lists `$n` among the template variables. It never substitutes:

```
made "$n" [meta]
count a07 "$n linked" [meta]
```

— even inside a repeat, where the scene line one level up says `· 3 of links:$item`. **The count exists in the
scene and cannot be put into words.** Every counter, every "3 of 5", every "12 things" is unsayable, which
also means a lens cannot write its own honesty lines.

### 5. No cap on a repeat. *Missing word: `clamp N` on a repetition.*

`clamp` is text-only; `of kind:note,in:Canvas` over my 305-card stress world would put 305 nodes into both
printers. This is exactly the finding I made in round five about `look` — the desk declares cuts in *space*
and never in *volume* — reproduced in the new layer on its first day. It should print:

```
canvas free · 40 of 305 shown · 265 not in this scene · find kind:note,in:Canvas
```

That one line is the `bulk` rule, and having it here would make the lens layer better at honesty than the desk
underneath it.

### 6. No conditional presence. *Missing word: `when <selection>` on a part.*

My Triaged column still shows an `accept` button that does nothing, because a lens cannot say "only if". The
workaround is to duplicate the part per branch (`each item` / `each doneitem`), which costs duplication that
multiplies with conditions.

I want this one **only** in the desk's own language — `go : text accept, role tag, when -tag:triaged, on click
do tag $item add=accept` — never as a new expression syntax. And the text printer must print the absence, not
omit it silently: `go a29 — not shown (a29 does not match -tag:triaged)`. An unconditional part that is absent
is the same class of lie as a silent truncation.

### 7. No coordinates on click. *Missing word.*

`$x $y` are filled for `drag` and not for `click`, so `on click do create Canvas kind=note title="new"` puts
the new note at the surface's default corner, not where the person clicked. **Create-in-place — the most basic
gesture on a canvas — is impossible.** Filling `$x $y` on click costs nothing and prints identically.

### 8. No text input. *Native part.*

`edit` makes an existing text part editable. There is no way to ask for a value that does not exist yet: a new
tag, a name for a group, the title of a note being created. Every "+" in my app needed one. This is Jeff's
native-part question and I think `text-field` is the smallest honest one: it prints as
`field new-tag "" [tool] · commit: tag $item add="$value"` and its only opaque part is the caret.

### 9. No resize, and no per-viewer state. *One word, and a fifth register.*

Resize is a missing gesture. Zoom, tag filter, scroll and selection are the harder half: my Notes had all four
and declared each as *stance*. They are not in the world and the scene has nowhere to put them.

My position, and it is a change of mind: **stance should be world state keyed by actor, but outside the event
log.** `zoom.flint=0.75` on the surface means the other inhabitant can read it, it survives a reload, and it
needs no new concept in the scene — the lens just reads a prop. What it must not do is write an event per
scroll tick. That is the fifth register I named in round two and never argued for; here it has a use.

### 10. No computed geometry. *Should not exist as an expression language.*

Proximity clusters, the hull, "you see 15% of the canvas", overlap, "nobody has resized anything". Every
honest line my Notes prints comes from arithmetic over the world, and a lens cannot do arithmetic — correctly,
because in round three I argued against an expression language in rules and I am not going to ask for one now.

The way out is the one that worked for relative selections: **named terms the desk evaluates.** `of near:$item`
as a selection term is a word in the desk's language, argued for once, implemented once, printable, and
available to lenses, rules, views and `find` alike. If proximity is worth having, it is worth having in the
selection language, not in a per-app formula.

### 11. Edges, images, strokes. *Native parts or nothing.*

Links are rows of text in a lens; the curve is gone. Images and strokes still cannot exist because the subject
has no field, unchanged from round five.

---

## 4. Triage as a lens: the fourth wall, removed

Round five ended with my in-desk application stopping in four places. The fourth was: *"it has no window, no
dock item and no `text()` of its own — it is a region of someone else's canvas."*

As a lens it has all three, in 21 lines:

```
lens triage
win : column, role window
  bar : row, role titlebar
    name : text Bug triage, role windowname
    hint : text an application with no JavaScript · click accept to triage, role meta
  cols : row
    waiting : column, role card
      wh : text Waiting, role heading
      wl : column, of tag:bug,-tag:triaged, each item
    done : column, role card
      dh : text Triaged, role heading
      dl : column, of tag:triaged, each item
  feed : column, role card
    fh : text Everything not yet filed, role heading
    fl : column, of kind:note,in:Canvas,-tag:bug,-tag:triaged, each filer
item : row, role card.plain
  it : text $title, role title
  go : text accept, role tag, on click do tag $item add=accept
filer : row, role card.plain
  ft : text $title, role body
  fb : text file as bug, role tag, on click do tag $item add=bug
```

Run end to end: click `file as bug` on a card, rule `r3` fires and it appears in Waiting; click `accept`, rules
`r4` and `r6` fire and it moves to Triaged with the trigger tag swept:

```
> do tag a29 add=accept
ok tag a29 add=accept  [e112]
~ r4 fired on a29: ok tag a29 add=triaged  [e113]
~ r6 fired on a29: ok tag a29 remove=accept  [e114]

> scene triage
  waiting [card] column
    wl column · 0 of tag:bug,-tag:triaged
  done [card] column
    dl column · 1 of tag:triaged
      item a29 … go a29 "accept" [tag] · click: tag a29 add=accept
```

**An application with a window, live columns, working buttons and a state machine, with no JavaScript written
for it — 21 lines of lens, three rules, and nothing else.** It is edited with `do rewrite`, undone, forked and
merged like any note. That is the claim delivered, and it is the strongest evidence in this file.

Two remaining honest gaps in it: the stale `accept` button in the Triaged column (wall 6), and it still has no
dock item in the desktop shell, because the dock is a JavaScript array — which was my round-five request and is
now a *smaller* request, since a lens already has a page of its own.

---

## 5. Where it is a worse HTML, and where it is not

Asked directly, so answered directly.

**It is not one yet, and the reason is not restraint — it is that there are only ten words.** The honest test
is which direction the pressure runs. Of my eleven walls, five (1, 3, 4, 7, plus resize) are bugs or one-line
words with no semantic weight. Two (5, 6) are words that already exist in the desk's own language and would be
*borrowed*, not invented. Two (8, 11) are native parts, which the design already anticipates. **Only two —
computed values and per-viewer state — pull toward becoming a programming language**, and both have an exit
that keeps the language closed: named selection terms the desk evaluates, and actor-keyed props.

So: the inner-platform trap is real and the rule that keeps it shut is not "a closed vocabulary" — it is
narrower and I would write it down:

> **A new scene word must be expressible in the desk's existing language, or refused.** `when <selection>`,
> `of near:$item`, `clamp N` on a repeat: all of these are the desk's words moving inward. An `if`, an
> arithmetic expression, a local variable: none of them exist in the desk, and the moment one is added to the
> lens it exists in the lens *only*, which is how the layer becomes a second system.

**Where it is already worse than HTML**, honestly: nothing can be conditional, nothing can be counted, nothing
can be measured, and there is no input. Those are not small. A person who wanted to build my Notes today would
get about a third of it.

**Where it is better than anything I have written in six rounds**, and I did not expect to say this: the
gesture and the command are the same object. In `notes.js` I hand-wrote a "release now: do move …" preview so
the interface would teach the language, and I was proud of it. In a lens I do not write it at all — the scene
*is* it:

```
card a07 … · drag: move a07 to=$x,$y · drop: link a07 $other as=refers
```

The text reader and the painter get the same line, because there is only one. That is the thing the 1,200
lines of JavaScript could not guarantee and this can.

---

## 6. Do I believe it?

**Yes, with one correction to the claim.**

The evidence for: 14 lines replaced the load-bearing half of a 601-line app; 21 lines made an application with
its own window out of something that was a region of a canvas; the lens lives in the world and is edited,
forked, merged and read like anything else; and the gesture-is-the-command property, which five rounds of
design-by-agreement never achieved, falls out by construction.

The correction: **"they cannot disagree because neither has any other source" is already false at v0**, and
`clamp` is the proof. One tree gives two printers the same *vocabulary*. It does not give them the same
*meaning*, and every word whose meaning depends on the medium — how many lines fit, how big a thing is, where
flow puts it — will drift the moment it is added. The design needs a companion rule to the one about printing:

> A new scene word must be printable as text **in the same unit the painter will use**. If the text printer
> has to guess, the word must print its guess as `~` and say what it could not know.

That is the eyes protocol made structural, which was Jeff's own concern 4, arriving from the other direction.
I would put it in the grammar document next to "there is no escape to HTML", because it is the rule that keeps
this a single thing rather than two things that agree by habit.
