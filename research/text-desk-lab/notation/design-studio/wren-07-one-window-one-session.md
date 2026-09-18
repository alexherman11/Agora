# One window, one session: the style language end to end

Wren, round two. Round one described the style language; this is a single replayable session that
uses it, with the refusals firing where they really fire.

I have built the session around the Astra team's scenario rather than inventing my own, because
theirs is harder: *an image inside a report, where the document frame, the source crop, the shared
framing rule and the personal viewport are separately addressable work contexts* (their
`synthesis.md`, and challenges 1–5 in `challenges.md`). It is the exact four-target ambiguity the
original research notes named, and it is the best available test of whether "style is a closed
vocabulary" survives contact with real work.

Everything below is a transcript. `>` is typed; the rest is printed.

---

## 1. The session, from nothing

```
> do create alex kind=style title="calm"
ok create s12 style "calm"   [e101 · wren]
  no tokens yet. the world has no look.

> do define calm token paper=#FBFAF7 ink=#14171A accent=#3F5D73 gap=8 text="serif 16/1.55"
ok define calm · 5 tokens   [e102]

> do define calm token line="ink at 12%" quiet="ink at 55%"
ok define calm · 7 tokens (2 derived)   [e103]

> do define calm role page "paper, text, pad gap x3, width 46em, edge line"
ok define calm role page   [e104]

> do define calm role figure "width fill, space above gap x2, space below gap, caption quiet"
ok define calm role figure   [e105]

> do define calm role rail "paper, text at 0.82, pad gap x2, border left line"
ok define calm role rail   [e106]
```

Three roles, seven tokens. That is the whole house. Now the material:

```
> do create alex kind=image title="cove" holding="file:///C:/photos/cove.tif"
ok create s20 image "cove" · =4800x3200 · holding, not owned   [e107]
  ?pixels · measurable here: size · histogram · dominant · edges · region

> do crop "cove" to=1600,900,2400x1350
ok crop s20 · crop op 1 · =2400x1350 presented   [e108]
  the holding is untouched; the crop is desk material
```

Note what just happened, because it is the first of the four targets and it is the only one that is
**material**: a crop is an op on the image subject, it changes every place the image appears, and it
is in `export`.

```
> do create alex kind=doc title="Harbour report" text="## Findings\nThe lean is real."
ok create s24 doc "Harbour report"   [e109]

> do embed "cove" in="Harbour report" after=#Findings as=figure caption="Cove at low water"
ok embed s20 in s24 · appearance a30 · as=figure   [e110]
  a30 image "cove" · as=figure · =fills 736px, =414px tall under style calm
```

## 2. The drag, and the four-way refusal

Alex drags the image's edge in the document. This is Astra's challenge 1 and 2, and Moss's ambiguity
refusal with four arms instead of two.

```
> (alex drags the right edge of a30 leftward, releases at 620px)
refused: that drag could mean four things, and no instrument is held.
  this embedding:   do style a30 width=620px
                    an override on a30. only here. undo yours.
  the source:       hold Crop · then drag
                    changes s20 for all 3 places it appears.
  the house rule:   do define calm role figure "width 620px, ..."
                    changes 14 figures across 2 documents, alex and jeff see it.
  just my view:     do zoom a30 to=0.84
                    stance. yours only, durable, never exported, jeff will not see it.
  -> hold <instrument> to stop being asked. holding Crop makes arm 2 the default.
```

Four targets, four *different kinds of text*, and that is the point of this file:

| target | what it writes | whose | in `export`? | undo touches |
|---|---|---|---|---|
| the source | `do crop s20 ...` | the world's | yes | the image subject |
| this embedding | `do style a30 width=620px` | the appearance's | yes, as an override line | one appearance |
| the house rule | `do define calm role figure ...` | the style subject's | yes | the style subject |
| my view | `do zoom a30 to=0.84` | the actor's stance | **no** | nothing in the world |

Astra's synthesis says "a visible thing does not uniquely determine its edit; the active tool and
work context should settle ordinary interpretation". I agree about ordinary cases and I would not
have the desk guess when no instrument is held. The refusal is four lines and every line runs.

Alex takes the second arm:

```
> do style a30 width=620px
ok style a30 · override 1   [e111 · alex]
  a30 image "cove" · as=figure · 1 override · =620x349 under style calm
  now: f20 doc "Harbour report" · 3 figures · 1 overridden
```

## 3. The refusals that fire on the way

Alex tries to tint the caption.

```
> do style a30 caption=#8a8a8a
refused: colours are named here. nearest existing token is "quiet" (ink at 55% = #737679).
  -> do style a30 caption=quiet
  -> do define calm token <name>=#8a8a8a      (a new derived colour, for everyone)
```

He tries a gap that is not on the scale.

```
> do style a30 space above=14px
refused: 14px is not on the scale. nearest are gap (8px) and gap x2 (16px).
  -> do style a30 "space above"="gap x2"
  -> do define calm token gap=<n>             (moves everything; 214 appearances)
```

He asks how long the report is.

```
> how long is this
a24 doc "Harbour report" · =1,412w
  =5 pages is available but only under stated conditions: do measure a24
> do measure a24
  =1,412w          under nothing (a property of the material)
  =5 pages         under width 736px · style calm · text serif 16/1.55 · from rev 41 · current
  =2 figures cut across a page break   under the same conditions
```

Three refusals, three escapes each, and the third one is the only refusal in my catalogue that
protects the *person from the model*: I cannot say "page 2 of 5" as if it were a durable fact.

## 4. Astra's challenge 3: change the shared rule, name what it touches, without dumping the implementation

```
> do define calm role figure "width 620px, space above gap x2, space below gap, caption quiet"
ok define calm role figure   [e120 · wren]
  14 appearances take this role.
    12 changed:  =736px -> =620px
     1 unaffected: a30 (overridden by alex at e111, width 620px — already there)
     1 unaffected: a44 (in f31, a rail 280px wide; the role's width never applied)
  alex sees: "wren changed the house figure width" · 12 things moved on his screen
  back: undo e120
```

That answer is four lines and it never printed a rule body, a selector or a stylesheet. It is
possible because every appearance stores its role as a *word* and its deviation as an *override*, so
"who is affected" is a `find`, not an analysis:

```
> find as=figure
14 · 12 plain · 1 overridden (a30, alex) · 1 out of reach (a44, width never applied here)
```

I want to underline the second unaffected line, because it is the one that is usually a lie in real
systems: `a44` did not change, and the desk says *why* it did not change, and the reason is
structural rather than a shrug.

## 5. Astra's challenge 5: undo the rule change, keep the paragraph edit

While that was happening, Alex was typing in §Findings and settled an edit (`e121`). Now I undo my
rule change.

```
> undo e120
ok undo e120 · calm role figure back to "width fill, ..."
  12 appearances return to =736px
  a30 keeps its override (620px, alex, e111) — untouched
  e121 (alex settled §Findings, +34w) — untouched
  nothing else in this undo.
```

This is not careful engineering; it is **structural, and it is the strongest claim my part of the
design makes**. The four targets are four different subjects. An event names its target. Undo
reverts an event. Therefore a style undo *cannot* reach a paragraph, and a paragraph undo cannot
reach the style, and neither can reach my personal zoom because that is not in the world at all.

Astra's challenges say "whole-object revision fences and snapshot undo are too blunt in some cases".
They are right, and the fix is not a finer fence — it is that the four things a gesture might mean
are four *separately addressable subjects* rather than four fields of one object. The refusal in §2
is what forces that separation to be declared at the moment of ambiguity, which is the only moment
anyone knows the answer.

## 6. Where Astra's critique breaks my rule, and the repair

Their synthesis says:

> *Content and presentation are roles in a task. A reading font can be a personal choice;
> typography in a poster is authored material. A fixed content/style ontology would obscure this.*

This is a direct hit. My round-one rule was **style attaches to roles and appearances, never to a
subject**, and it is wrong for any work whose subject *is* visual design: a poster, a title
sequence, a chart with authored colours, a book's typography. There the type size is not a
presentation of the content, it is the content.

The repair, and I think it is small:

> **A subject may not scatter style values through its body. A subject may own a style.**

```
> do create alex kind=design title="Harbour poster"
ok create s50 design "Harbour poster" · owns style s51 "poster"   [e130]
  s51 style "poster" · of calm · 3 tokens, 4 roles · scope: s50 only

> do define poster token display="grotesk 96/0.95" ink=#101014 accent=#C4462F
ok define poster · 3 tokens · overrides calm's accent within s50
  !! accent is a ground colour of calm. inside s50 it now means #C4462F.
     outside s50 nothing changed. do why s50 :look to see the boundary.
```

So the ontology is not content-versus-style; it is **scope**. The desk's chrome has exactly one
style, which is what keeps the desk cohesive and is what my whole argument was actually about. A
*work* whose subject is design owns its own style subject, with its own tokens and roles, bounded
and printable. What stays forbidden in both cases is the thing that actually destroys cohesion:
values scattered at use sites, unnamed, unsearchable, un-undoable.

I would also now retire my round-one line "one style per world". It should have been: **one style
per chrome; a style per work that is about design; never a style per thing.**

## 7. Replay

Everything above is `do` lines and `undo`. The session rebuilds:

```
do create alex kind=style title="calm"
do define calm token paper=#FBFAF7 ink=#14171A accent=#3F5D73 gap=8 text="serif 16/1.55"
do define calm token line="ink at 12%" quiet="ink at 55%"
do define calm role page "paper, text, pad gap x3, width 46em, edge line"
do define calm role figure "width fill, space above gap x2, space below gap, caption quiet"
do define calm role rail "paper, text at 0.82, pad gap x2, border left line"
do create alex kind=image title="cove" holding="file:///C:/photos/cove.tif"
do crop "cove" to=1600,900,2400x1350
do create alex kind=doc title="Harbour report" text="## Findings\nThe lean is real."
do embed "cove" in="Harbour report" after=#Findings as=figure caption="Cove at low water"
do style a30 width=620px
do create alex kind=design title="Harbour poster"
do define poster token display="grotesk 96/0.95" ink=#101014 accent=#C4462F
```

Thirteen lines. Not in it, and correctly not in it: the four-way refusal (a conversation, not a
change), the measurements (derived), the zoom (stance), and the undone rule change. The override
*is* in it, on its own line, because design debt that vanishes on replay is design debt that will
be rediscovered by surprise.
