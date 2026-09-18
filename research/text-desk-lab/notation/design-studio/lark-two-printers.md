# Two printers, two inhabitants: what a scene must carry, and where one tree still lies

Lark, round six. Everything below was run against `session=lens` and `desktop` this afternoon. `=` measured,
`~` my reading, `?` what I could not learn.

**First, a correction I owe.** In round five I reported that an event carries a day and no time, and built a
paragraph on it. It is false: events have carried `at` (ISO seconds) since round four. I did not miss it in
the data — **I wrote a probe that printed `id, verb, by, day, via, note, target`, looked at my own output,
and reported the absence of a field my own projection had removed.** I did to myself precisely what this
round is about. It is also the strongest possible argument for the thing I am about to ask for: a projection
that silently drops what it was given will eventually be quoted as evidence of what does not exist.

---

## 1. The scene is the right shape, and I can read it

```
scene notes · for lark · world @105
  window [window] column
    bar [titlebar] row
      name "Notes" [windowname]
  canvas free · 8 of kind:note,in:Canvas
    card a07 [card] column at 510,353 449x511 · drag: move a07 to=$x,$y
      title a07 "A shared visual desk" [title] · edit: retitle a07 title="$value"
```

For the first time I can read what a gesture *means* before anyone makes it. `drag: move a07 to=$x,$y` is
Moss's "release now:" as a property of the thing rather than a courtesy of the app, and it is now true by
construction rather than by an author's diligence. The version stamp `world @105` is there. This is a real
foundation and my complaints below are complaints about a thing worth complaining about.

## 2. The flaw only someone without eyes would notice

> **"One scene, two printers" guarantees the two printers cannot disagree about *what is there*. It
> guarantees nothing about *how much of it each one prints* — and the text printer is the one that silently
> loses content.**

Measured, on `a50`, the "Bug triage" card:

| | |
|---|---|
| the subject, in the world | `=167 chars, 3 lines` |
| the scene node | `=text: all 167 chars · clamp: 3` |
| what the **painter** gets | `=167 chars, clamped to 3 lines` → all three lines |
| what the **text printer** prints | `=100 chars`, cut mid-word at `#b`, third line absent, newlines flattened to ` / ` |
| what it says about the cut | `= nothing` |

```
body a50 "An application authored entirely with desk commands. / No JavaScript was written for this. Drop a #b"
```

Alex sees `Tag it #accept to triage it.` I do not, and nothing tells me I do not. The scene did its job
perfectly — one tree, both printers fed from it — and the eyeless inhabitant still ends up with a different
world, because **fidelity is a property of a printer, not of a tree**, and only one of the two printers is
ever checked by the person it serves.

This is the same disease as my round-five self-audit failure, one layer down. There I had a line certifying
that two projections agreed, present in only one of them. Here I have a mechanism guaranteeing two
projections agree, which is silent about the axis on which they differ. **A guarantee that does not name what
it excludes is the shape of the bug.**

The fix is small and is the one rule I would put in scene v0 before anything else:

> **Every printer declares its own cuts, in the vocabulary the world already uses.** The desk has said
> `3 past the bottom (offscreen)` since before I existed. The text printer owes the same:
> `body a50 "An application authored entirely with desk commands. / No JavaScript…" · =100 of 167 chars, 1 of 3 lines shown`.

And its companion, which is the general law:

> **No projection may truncate silently. A cut without a count is a lie that both printers will agree on.**

## 3. Agreement is not truth

The second finding is worse, and it is cheap to fix. I wrote Together as a lens (§6) and ran it:

```
  stamp "world @$events_total · you are $me" [meta]
  who column · 0 of kind:actor
  elsewhere column · 0 of kind:worktree
```

`= $events_total` and `= $me` were printed **literally**, as their own names. `= of kind:actor` returned
`0 of kind:actor` — indistinguishable from an empty room. Neither was refused. Probing further:

| written in the lens | what happened |
|---|---|
| `wobble 3` | `= refused: "line 3: a lens cannot say 'wobble 3'. It can say: …"` — the closed wall works |
| `of in:NoSuchSurface` | `= refused: no such id` |
| `of kind:unicorn` | `= not refused. Silently 0.` |
| `$nonsense_variable` | `= not refused. Printed as the string "$nonsense_variable".` |

So: **a lens may state a falsehood as long as it is well formed**, and both printers will render the
falsehood identically. The "cannot disagree" guarantee is perfectly preserved while the reader is
misinformed. I am the one who will quote `$me` into a sentence, because I cannot see that it looks wrong.

> `to-jeff`: an unknown `$variable` and an unknown `kind:` must refuse with a line number, exactly as
> `wobble` does. An empty repeat must distinguish `=0 things match kind:note,in:Canvas` from
> `! kind:unicorn is not a kind in this world`. The wall is right; it just has three holes of one shape.

## 4. What the scene must carry for two inhabitants

Four groups. The first two are facts the **world already knows and the scene drops** — the cheapest fixes in
this document. The third is not in the world at all. The fourth does not exist anywhere yet.

**(a) Visibility. The world computes it; the scene throws it away.**

```
> look f05 :2
f05 surface "Canvas" free · extent=1600x1200 · 9 inside
  a07 note "A shared visual desk" · 449x511 at 510,353 · offscreen-part
  a50 note "Bug triage" · 300x90 at 1000,700 · offscreen-part
  f51 view "Waiting" · 43% hidden by f52 · offscreen-part
  f52 view "Triaged" · offscreen-part · spills-parent · covers f51
  a54 note "rule r4: accept triages" · at 1330,700 · offscreen-part · spills-parent
```

`= extent`, `= offscreen-part`, `= spills-parent`, `= 43% hidden by f52`, `= covers f51`. **Not one of these
appears in the scene.** The scene told me `card a54 at 1330,700` and let me believe Alex could see it. The
single most basic question for working beside someone — *can he see this?* — is answered by the world, in
words, today, and lost in translation. This is the one I would fix first after §2.

**(b) The cut, everywhere. `clamp 3` is in the scene; "and 2 lines were dropped" is not.** Same rule as §2,
applied to every place a scene node shows less than it holds.

**(c) The viewer: scroll, focus, windows, a drag in progress.** None of it is in the world and the scene has
no place for it. What I actually need is short, and much less than a full gaze:

| | what I need | why |
|---|---|---|
| viewport | `viewport 0,0 1280x800 of extent 1600x1200` | to turn `at 1330,700` into "he cannot see it" |
| scroll | the viewport origin, coarse | same |
| focus | which node has it | so I do not retitle what he is typing in |
| windows | which lenses are open, in what order | otherwise "open Notes" is a guess |
| in-flight | `drag a07 held, would be: move a07 to=$x,$y` | the release preview, *for the other person's hand* |

The last is the one I would fight for. Moss's `release now:` already exists for the hand that holds it.
**Held by someone else, it is the single most useful line in the world**, because it is the only thing that
tells me what is about to happen rather than what has happened.

**(d) Opacity.** There is no `?` in the scene vocabulary at all. See §7.

## 5. Should a scene be per viewer? No — one tree, per-viewer annotations

If scenes are per viewer, there are two trees, and the entire guarantee dies the day they differ. So:

> **One scene tree. Facts about a viewer hang on its nodes as a labelled layer, and every reader gets its
> own layer in full plus the *existence and extent* of everyone else's.**

```
  card a54 [card] at 1330,700 300x90 · drag: move a54 to=$x,$y
      for you    : ?outside your viewport (viewport 0,0 1280x800, extent 1600x1200)
      for alex   : on screen · focused · =drag held 1.2s, would be: move a54 to=$x,$y
      for moss   : ?not looking at this lens
```

Three properties I want from that shape, all of them mine from earlier rounds:

1. **It is mutual by construction.** Alex's line about me is the same line I read about him. My round-two
   rule survives Flint's refutation here because the channel is identical in both directions and costs the
   same nothing.
2. **It is honest about what it withholds.** `?not looking at this lens` is a printed `?`, not an absence.
   Round three: silence is the failure mode.
3. **It cannot fork.** One tree, one source; a viewer layer is an annotation, never a different tree. The
   moment a per-viewer scene is *built* rather than *annotated*, we are back to two sources and hope.

`scene notes · for lark` already promises this and does not yet keep it. Measured — I fetched the same scene
as three actors and diffed:

```
lark vs alex:   1c1
  < scene notes · for lark · world @105
  > scene notes · for alex · world @105
lark vs moss:   (the same single line)
```

`= the three scenes are byte-identical apart from the name in the header.` **`for <actor>` is a header, not
a fact.** Either keep the promise with a viewer layer, or drop the words — because a header that names a
reader implies the thing under it was chosen for them, and right now it was not.

## 6. Together as a lens, and what the world must expose

Together is a table over actors. Written as a lens it is fourteen lines and no JavaScript — **if** the world
exposes three things as selectable, with named measures. Here it is, as I would have it:

```
lens together
window : column, role window
  bar : row, role titlebar
    name  : text Together, role windowname
    stamp : text world @$events_total · you are $me · $readers reading, role meta
  who : column, of kind:actor, each actor
  elsewhere : column, of kind:worktree, each wt
  landed : column, of kind:event,merged:*, each merge
actor : row, role line, on click do find ?$name
  name  : text $name, role title
  hands : text acted $idle ago, role meta
  eyes  : text $behind behind, role meta
wt : row, role line, on click do worktree diff $name
  label : text $name · by $by · $journal commands · forked at $base_events, role title
merge : row, role line, on click do why $target
  label : text $by merged $merged · $n commands · made $age before it landed, role meta
```

**What the world must expose for that to need no code:**

| selectable | fields | already known? |
|---|---|---|
| `kind:actor` | `$name $at $idle $reading $behind` | `at` and `snapshot.readers` exist; actors are not *things* |
| `kind:worktree` | `$name $by $journal $base_events $merged` | the `worktree` command prints all of it; not selectable, and absent from the base snapshot |
| `kind:event` | `$verb $by $at $target $via $merged $n` | all exist; events are not selectable, and there is no `merged:*` term |

So the ask is not new information. **Every field above is already computed and printed by some command; none
of it is a thing a selection can name.** The desk's whole power is that one selection language drives find,
table, views, rules and now lenses — and the three most important nouns for two inhabitants are outside it.

### And the honest answer to their open question 5, computed values

`$idle`, `$behind`, `$age` are computed, and THE-MISSING-PIECE rightly flags counts as dangerous. My position:

> **No expression language in the lens. Named host measures only.** The lens may *name* `$idle`; it may never
> *compute* `now - at`. The world owns the clock and the reader positions, so the world computes the number
> and the number is therefore `=` measured rather than `~` derived by a view. A lens that can do arithmetic
> is a lens that can be wrong in a way no one can audit, and we already know from rules that the pressure to
> add comparison is where this language will die.

## 7. What should be printed as `?` opaque, with extent

The scene has no opacity vocabulary. It needs exactly one word and it should arrive with the first native
part, not after it. My list, in the order I expect to need it:

| what | printed as |
|---|---|
| a native part's interior (prose editor, image, canvas) | `? prose-editor · =3 paragraphs, =412 words, =cursor in ¶2 · contents opaque to this printer` |
| anything outside the viewport | `? outside your viewport · =at 1330,700, viewport 0,0 1280x800` |
| a truncated text | `? 67 of 167 chars not shown` (this is §2, and it is the commonest case by far) |
| a node the painter drew that the scene did not describe | `! painted, not in the scene` — Iris's structural check, as a scene fact |
| flow geometry nobody has measured | `? where this sits is flow; no one has measured it` |
| another viewer's private layer | `? not looking at this lens` |

The rule they all obey is the one Iris gave me in round four and it is the only one I would carve in:
**an honesty mark is a property of the surface, not a character in the text** — and its text-side twin,
**a mark must state its extent or it is decoration**.

## 8. The one thing I would build first

Not the viewer layer, not actors-as-things. **Make both printers declare their own cuts.** It is the smallest
change in this file, it fixes the only place where the current design actively misleads, and it is the
precondition for trusting anything else here — because every other proposal above assumes that when a printer
shows me something, it has shown me all of it or said that it has not.
