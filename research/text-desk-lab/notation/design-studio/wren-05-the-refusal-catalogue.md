# The refusal catalogue

Wren, sketch 5, short. My whole position in one page, after the studio has had a go at it.

The rest of the studio has been designing what the desk can *say*. My contribution is the list of
things it must refuse to say, because that list is what makes the result cohesive, and because a
refusal in this house is not a wall — it is a printed line with two runnable alternatives, which is
the most teachable object the system has.

Every entry below is: the refusal, and the two escapes. If an entry has no second escape it is a
wall and I would cut it.

---

## The nine

**1. A colour or a length outside the token block.**
```
refused: colours are named here. nearest existing token is "accent" (#3F5D73).
  -> do style a91 ink=accent
  -> do define calm token <name>=#3F5D73     (a new ground colour, for everyone)
```

**2. A length that is not on the scale.**
```
refused: 17px is not on the scale. nearest are gap x2 (16px) and gap x3 (24px).
  -> do style a91 pad="gap x2"
  -> do define calm token gap=<n>            (moves everything; 214 appearances)
```

**3. A rendering measurement without its conditions.**
```
refused: "page 2 of 5" is only true at width 736px in style calm.
  -> say "5 pages under width 736px, style calm"
  -> do measure a91                          (the conditions, printed)
```
This is the only one of the nine that protects the *person from the model* rather than the desk
from us, and it is the one I would ship first.

**4. A perceptual fact with no epistemic mark.**
A presentation that emits an unmarked perceptual fact is refused registration, not merely frowned
at. Marks are Lark's: `=` measured, `~` claimed and attributed, `?` opaque with its extent, `!`
stale. Unmarked means structural: counts, ids, kinds, section names. And the marks propagate — a
fact derived from a `~` is a `~`, which is how a model can read someone's unsettled draft without
being able to launder it into a deed.

**5. A truncation without a count.**
The desk already refuses this vertically (`3 past the bottom (offscreen)`). Horizontally too: a line
ends `· +6`, never simply stops. Flint's version is better than mine and I adopt it: a truncation
should state its *reason* where it has one — `SUPPRESSED 44 diagnostics downstream of this one`
beats `+44`.

**6. A theme that redefines a role.**
```
refused: a theme may redefine tokens, not roles. "page" is the world's.
  -> do define calm role page "…"            (change it for both of us)
  -> do style <this appearance> …            (change only this one, as an override)
```
Consequence: Alex's side and Claude's side may differ in shade and never in shape, and a thing
dragged across cannot change form. One style per world; `as=page` means one thing forever.

**7. `rewrite` on anchored prose.**
```
refused: 2 anchors in §Findings. rewrite would orphan them.
  -> do replace a32 span=k4 text="38ms"
  -> do splice a32 after=k3 text=" (but see the rerun)"
  -> do rewrite a32 #Findings text="…" anchors=orphan    (parks them, loudly)
```
Flint calls this a cultural mitigation belonging in help text. I want it as a refusal, because the
destructive path should be sayable only on purpose. This is the one place I am asking for more
viscosity than anyone else in the studio.

**8. Structural opacity in chrome.**
Flint corrected me here and the corrected rule is better than mine was. Three states, not two:

| | structure | metric |
|---|---|---|
| chrome | never opaque — every part named, listed, operable | opaque until asked; `measure` always answers, with conditions |
| content | may be opaque, with extent | `?` and terminal: no amount of asking produces the picture |

Only one of the three is a dead end, and it is the one that was always going to be.

**9. An anonymous claim, or drift outside its parentheses.**
Every `~` has a `by`. Everything before a parenthesis on a line is deed and exports; nothing inside
one ever does.

---

## Where I moved today

- **Anchors.** I argued for quote-outside-the-body; Flint argued for ids-in-the-body-as-edit-address.
  His is better wherever the edit goes *through* the anchor, because then there is nothing to match.
  I now want both: ids in the stored body, a bare face that `read` prints by default, the quote
  riding alongside purely as the recovery path, and my compulsory grade on the recovery.
- **Opacity in chrome.** Conceded, and sharpened (entry 8).
- **`page 2 of 5`.** Flint generalised my point past me — *every derived thing states what it is
  from, the revision, and whether that is current* covers pagination, diagnostics, outlines,
  composites, charts, word counts. Mine was a special case of his and I would drop my phrasing for
  his.

## Where I have not moved

- **No raw escape hatch for style.** Lark wants one, declared opaque. I still say no: a blessed
  hatch is how every small design language becomes CSS again, and the pressure to use it arrives
  exactly when someone is in a hurry, which is exactly when cohesion dies. If you need a pixel, the
  language is missing a word; coining a word costs one command and produces an argument, and the
  argument is the feature.
- **Friction belongs at the coining of words and nowhere else.** Writing prose, moving things,
  reading, commenting: all should be frictionless. Naming a new colour, a new role, a new spacing
  step: all should cost a sentence and a witness. Almost every ugly shared system I have seen got
  that ratio backwards.

## The hole I still have

Data-driven colour — ramps, heat maps, syntax palettes, nine chart series. `ramp` and `set` as new
*kinds* of token is my half-formed patch (wren-04 §5). It keeps colours in the token block and keeps
them named and enumerable, and I do not yet know whether it survives a real spectrogram.
