# Flint: the four slices, actually written out, and where they break

I took the four test slices from `00-research-notes.md` and wrote each one as desk text. Not a description
of how it would work — the actual lines. Then I went looking for the place each one lies, gets verbose, or
cannot say the thing.

Where I use notation from the others, I say so. Where I invented, I say so. Everything below is a proposal;
I have marked the parts I do not believe yet.

Conventions I am using throughout (mine unless noted):

- `role=` a named visual role, resolved by a stylesheet subject (see my Commons note "Style: resolved, with provenance").
- `OPAQUE` in caps: a declared opaque region. Not a failure, a boundary. See "The opaque frontier".
- `(alex, 0.4s ago)` a **pulse**: observed state nobody authored. Moss's word, better than my "drift"; I have adopted it.
- `k3` `m1` `t7`: **anchor** ids. An anchor is `(subject, axis, span)`. New here; argued in §6.
- Lines are honest about what they omit. That rule already exists in the desk and is its best property.

---

## 1. Document with anchored discussion

The reference Alex named: a Google Docs window. Page, outline rail that follows the reader, toolbar, comment
anchored to a highlighted passage in the margin, sharing, saved state.

```
f20 surface "Weekly report" window · 980x1240 · role=doc-window · 4 inside · shared: alex(own) claude(write)
  a30 bar "Doc tools" · role=toolbar · instruments: style link comment image suggest · 6 more under "More"
  f21 surface "Outline" column · role=outline-rail · of a31 headings · 6 inside · current "Findings" (alex, 3s ago)
    a31.h1 "Weekly report"
    a31.h2 "What we ran"
    a31.h2 "Findings"        <- current
    a31.h3 "The harbor lean"
    a31.h2 "What is next"
    a31.h2 "Appendix" · 2 sub folded
  a32 doc "Weekly report" · role=page · 1840w · 6 sections · 5 anchors · 2 threads open · saved 14:02
       viewing §Findings..§What is next (alex) · caret 3:214 (alex, 1s ago) · no caret (claude)
       layout: paginated, 7 pages, measured at rev 91 by renderer
  f22 surface "Margin" column · role=margin-rail · anchored to a32 · 3 inside
    a33 thread "k3" · at "the harbor lean is real but small" · 2 replies · open · by alex
    a34 thread "k4" · at "40ms" · 1 reply · resolved · folded
    a35 thread "k9" · ORPHAN · was at "the noise floor" · parked 14:06 · 1 reply · open
```

And the text itself, read through a section:

```
> read a32 #Findings
s31 doc "Weekly report" · §Findings · rev 91 · 3 anchors in this section
---
## Findings
The harbor lean is |k3 real but small|: eight of nine trials show it, and the median
delta is |k4 40ms|, which is under |k9 the noise floor| we measured in June.
---
anchors shown inline as |id text|. read a32 #Findings bare=1 for the prose alone.
```

### What works

**Anchors are addresses.** This is the part I would fight for. The same id that a margin comment points at
is also the handle you edit through:

```
do replace a32 span=k4 text="38ms"
do splice  a32 after=k3 text=" (but see the rerun on the 12th)"
do anchor  a32 span="under the noise floor"     -> creates k11
```

One mechanism does three jobs: it is the comment target, the highlight the person sees, and the edit address
the model types. Anchoring survives editing *because* editing goes through anchors. If you get this right you
have solved the slice's stated failure mode — "text and screen refer to different passages" — not by clever
matching but by making them literally the same object.

**Two carets, both named, one absent.** `caret 3:214 (alex, 1s ago) · no caret (claude)` is worth the
characters. In a shared desk the most common question either inhabitant has is *where is the other one*.

### Where it breaks

**Break 1. `rewrite` is an anchor shredder, and this is a real asymmetry against the model.**
When Alex edits in the visual editor, his edits are structural: marks move because the editor moves them.
When Claude types `do rewrite a32 #Findings text="..."`, Claude is retyping prose from memory, and unless
Claude faithfully reproduces `|k3 ...|` `|k4 ...|` the anchors die. Three options, all bad:

- silently drop them → the desk lies, and a person's comment thread vanishes. Unacceptable.
- refuse the rewrite → viscous; the model cannot restructure a paragraph without a dance.
- orphan and park, loudly:

```
ok rewrite a32 #Findings  [e88]
  !! 2 anchors lost. parked in f22.
     k3 "the harbor lean is real but small"  2 replies, open
     k9 "the noise floor"                    1 reply, open
     do reanchor k3 in=a32 span="<some text now present>"   |   do drop k3
  now: a32 doc "Weekly report" · 1791w · 3 anchors · 2 threads open · 2 ORPHAN
```

I would take the third. But notice what it costs: **the text interface is strictly worse than the pixel
interface at editing discussed prose**, and no notation fixes that — it is a consequence of retyping versus
manipulating. The mitigation is cultural and should be in the help text: *on anchored prose, prefer
`replace`/`splice` on spans over `rewrite`.* Which is to say, the anchor-as-address idea is not a nicety,
it is load-bearing, because the alternative editing path is destructive.

**Break 2. "The outline follows the reader" makes `look` actor-relative.**
`current "Findings" (alex, 3s ago)` depends on who is asking and when. Two actors reading the same surface
now get different text. I think that is correct and unavoidable, but it must never be silent. Proposed rule:

> **Any line whose content depends on who is asking must name who it was computed for.**

Without that rule, `export` stops reproducing the desk, `find` results differ per actor for no visible reason,
and a model will confidently report Alex's scroll position as a property of the document.

**Break 3. Page numbers are not in the world.**
`layout: paginated, 7 pages, measured at rev 91 by renderer` — pagination does not exist until something with
a font metric computes it. It is an *observation*, not material. If a model is allowed to say "on page 3" as if
it were durable, the first font change makes the desk a liar. So a derived fact must carry the revision it was
derived from. This recurs in every slice below, so I am promoting it:

> **Every derived view names the revision it was derived from.** Pagination, diagnostics, thumbnails, word
> counts, chart renders, search indexes. If the named revision is behind the material's revision, say `stale`.

**Break 4, unsolved.** "Sharing and saved state" — `shared: alex(own) claude(write)` is a placeholder and I do
not believe it. Per-surface permission is the obvious move and the obvious move is wrong: the interesting cases
are *per-part* (Claude may comment but not edit prose; Claude may reorganise the outline but not retitle).
I have no notation for that yet and I would rather say so than invent a plausible-looking one.

---

## 2. Layered image with a mask and a live stroke

```
f30 surface "cove.png" window · 900x760 · role=image-window · 3 inside
  a40 canvas "cove" · 2400x1600 · 4 layers · composite OPAQUE · fit 37% (alex)
       probe and measure available; no textual form of the pixels exists
  f31 surface "Layers" column · role=layer-rail · 4 inside · top first
    a41 layer "grade"  · adjust curves(4 pts) · normal 100% · affects all below
    a42 layer "notes"  · strokes 12 · normal 100% · +1 drawing (alex, pen, 0.6s, bbox 880,410 120x90)
    a43 layer "boat"   · raster 900x600 at 300,700 · multiply 80% · LOCKED
    a44 layer "sky"    · raster 2400x1600 · normal 100% · mask m1 · 6 ops + painted OPAQUE (31% covered)
  a45 note "why the grade is on top" · 40w · linked to a41
```

The mask, opened:

```
> examine m1
m1 mask of a44 "sky" · 31% covered · 6 ops, then a painted residue (OPAQUE)
  1 fill      black
  2 add       rect 0,0 2400x520
  3 add       gradient linear 0,520 -> 0,760  white->black
  4 subtract  ellipse 1180,300 r 260x180
  5 feather   12px
  6 paint     OPAQUE · 41 strokes · bbox 300,180 900x520 · by alex · rev 14
verbs: do mask a44 add=<shape> | subtract=<shape> | feather=<px> | clear ops=4..6
```

### What works

**The mask op stack is the honest compromise.** Five of the six ops are fully text, fully editable, fully
re-orderable by a model that has never seen the image. The sixth is declared opaque with a bbox and a count.
Claude can do real work — "remove op 4, the ellipse is wrong" — without pretending to see. I believe in this
shape strongly enough to generalise it:

> **Prefer a stack of named operations plus a declared opaque residue, over an opaque result.**

This is the image-domain version of the same move that makes the code slice work (diffs, not blobs) and the
spreadsheet work (formulas, not values).

**`probe` is the cane, not the eye.** The thing a model actually needs is not a description of the picture,
it is targeted contact with it:

```
> probe a40 at=1200,800
a40 at 1200,800 (canvas coords) · final #3e5a6b
  a41 grade  curves          -> #3e5a6b   (lifted +6 lum)
  a42 notes  transparent
  a43 boat   #2b4150 mul 80% -> composited
  a44 sky    #6d93a8, mask 100%
```

That single call answers "is the boat covering the horizon here" without any pretence of vision. Cheap, exact,
bounded. I want `probe` in the language.

### Where it breaks

**Break 5. A live stroke cannot be usefully streamed to a reader who has no eyes.**
`+1 drawing (alex, pen, 0.6s, bbox 880,410 120x90)` is the *most* that should be said mid-stroke. Streaming
400 sampled points as text costs a model a great deal and buys it nothing; it cannot integrate a polyline into
a mental picture faster than it can wait. So: during a pulse, say *that it is happening, by whom, with what
instrument, and where* — and nothing else. The path text arrives at settle, when it is a deed.

This punctures a phrase in the handoff: *"Whatever Alex sees, Claude must be able to know from text alone."*
Claude cannot know a stroke in progress, and should not try. The honest version is: *whatever Alex can act on,
Claude can act on; whatever Alex can only see, Claude is told the shape and size of its ignorance.*

**Break 6. Blend composition is not linear, and no amount of verbosity saves the outline.**
Four layer lines do not tell you the picture, and 400 would not either. I do not think this is fixable and I
do not think it should be. It is the clearest case for the opaque frontier: stop trying, declare, and provide
`measure`, `probe`, and `diff`:

```
> diff a40 rev=88 rev=91
2 regions changed · 3.1% of pixels
  bbox 300,180 900x520 · mean delta 41 · cause e120 (paint on m1 by alex)
  bbox 880,410 120x90  · mean delta 88 · cause e124 (stroke on a42 by alex)
```

`diff` is the second half of the cane. With `probe` and `diff` a model can verify its own edits landed, which
is the actual need. It cannot appreciate the photograph, and that is fine; neither can it appreciate a sunset.

**Break 7, small and annoying.** `affects all below` on the adjustment layer is a hidden dependency in the
Green-and-Blackwell sense: reordering a41 silently changes three other lines' meaning without touching them.
Fix: dependent lines must *say* they are affected — `a43 layer "boat" ... · under grade(a41)`. Costs eight
characters per line and removes a whole class of surprise. I would pay it.

---

## 3. Media with timestamp notes

```
f40 surface "harbor-run.mp4" window · 1280x800 · role=media-window · 3 inside
  a50 video "harbor-run" · 04:12.0 · 1920x1080 30fps · frames OPAQUE · audio OPAQUE (2ch)
       PLAYING from 01:23.4 at rate 1.0 as of 14:22:07.2 · vol 60% · loop off   (alex)
  f41 surface "Marks" column · role=timeline-rail · by=time · 4 inside
    t1 mark "boat enters"     · 00:14.2        · note 12w
    t2 mark "the lean"        · 01:20.0-01:31.5 · 2 replies open · by alex
    t3 mark "???"             · 03:02.8        · note 3w · by alex, 2 min ago
    t4 mark "audio clips"     · 03:44.0        · note 8w · by claude (from measure, not hearing)
  a52 doc "Run notes" · 300w · 3 anchors into a50 · 1 anchor into a32 (the weekly report)
```

### What works

**Break the staleness problem by printing a law, not a value.**

> `PLAYING from 01:23.4 at rate 1.0 as of 14:22:07.2`

This is the single line I am most pleased with. A pulse that prints only its current value is stale before the
model finishes reading it, and a model that reasons from it is reasoning from a lie. A pulse that prints its
*law of motion* is exactly knowable at any later moment: Claude reads this at 14:22:31 and knows the playhead
is at 01:47.2 without another call. Proposed rule:

> **A pulse prints a law where it has one, a value plus an honest `unpredictable` where it does not.**

Playheads, timers, countdowns, progress with a known rate, animations: all have laws. A stdout tail does not,
and should say `tail as of 14:22:07, unpredictable`. This one rule removes most of the cost of observing a
live world from a turn-based reader.

**Anchors work on a time axis with no new machinery.** `t2` is `(a50, axis=time, span=01:20.0-01:31.5)`, exactly
the same shape as `k3` is `(a32, axis=chars, span=...)`. Different reanchoring policy — a time anchor is absolute
and only moves if the media is trimmed — but the same concept, the same rail, the same comment threads.

**`by claude (from measure, not hearing)`** — I want provenance on a model's own annotations. If Claude marks
"audio clips" from an RMS measurement, saying so keeps a later reader from assuming Claude listened.

### Where it breaks

**Break 8. Transport is an effect and undo must refuse it.**
`undo e130` where e130 was `do play a50` would start a video playing in Alex's face minutes later. Transport
verbs are Moss's RUN tempo: attributed, receipted, *not undoable*, and the refusal must say so rather than
silently succeeding at nothing.

**Break 9, genuine and unresolved: trimming.**
`do trim a50 from=00:30` shifts every time anchor by -30s, including anchors inside `a52`'s prose, including
`t2`'s range which may now straddle the cut. This is the media version of Break 1 and it is worse, because
a range anchor can be *partly* destroyed. I have no good answer. Options I can see: refuse trims that split a
range anchor (viscous but honest); clamp and mark the anchor `TRUNCATED`; or park as orphan. I lean toward
clamp-and-mark, and I want it in the Disagreements pile rather than settled by whoever writes it first.

---

## 4. Code buffer with diagnostics and running output

```
f50 surface "explore.py" window · 1120x900 · role=code-window · 3 inside
  a60 code "explore.py" · python · 4212 lines · HOLDING file:///C:/.../notation/explore.py
       DIRTY: 3 unsaved edits (alex, last 40s ago) · disk rev 88, buffer rev 91
       viewing 180-241 (alex) · caret 214:9 (alex) · 3 folds
       structure: from rev 88 (rev 91 does not parse: unexpected indent at 388:1)
  f51 surface "Problems" column · role=problem-rail · by=severity · 2 shown of 46
    d1 diag "unexpected indent" · error · 388:1 · parser · rev 91
       SUPPRESSED 44 diagnostics downstream of this one (do show d1 downstream=1)
    d2 diag "undefined name 'anchr'" · error · 214:12 · pyflakes · rev 88 · STALE (buffer at 91)
  a63 run "pytest -k anchor" · RUNNING 00:07 · unpredictable
       12 passed 1 failed so far · tail 3 lines as of 14:23:01
```

### What works

**Two revisions on one line is the honest way to show a live buffer.** `disk rev 88, buffer rev 91` plus
`structure: from rev 88 (rev 91 does not parse)` tells a model exactly what it may and may not trust. The
research notes worry that "the model assumes every edit is valid syntax". The fix is not to make the model
careful, it is to make the *text* incapable of pretending: an outline derived from a stale parse says so on
its own line.

**`SUPPRESSED 44 diagnostics downstream of this one`** is the code-domain version of the desk's existing
`3 past the bottom (offscreen)`, and it is a better version, because the reason for hiding is *semantic*
rather than spatial. I want to generalise that: rails may truncate, but a truncation must state its *reason*
and offer the command that undoes it. "46 problems" in a rail is a lie by volume; one cause plus a count is the truth.

### Where it breaks

**Break 10. The desk should not own the file, and the vocabulary has no word for that.**
`explore.py` already has a perfect text form: itself, on disk, in git, edited by real editors. If the desk
makes it a subject it has quietly built a second, worse editor and a synchronisation problem. But the desk
must still hold the anchors, the diagnostics, the runs, the discussion.

So I want a distinction nobody has proposed yet:

> **A subject** is material the desk owns: it is in `export`, its revision is the desk's revision, undo works.
> **A holding** is material the desk does not own: it has desk identity, desk anchors and desk-derived views,
> but its content lives elsewhere, and the line says where, and `export` reproduces the *reference*, not the bytes.

This matters far past code: a photo on disk, a Canvas assignment, a Confluence page, a Gmail thread. Almost
everything interesting Alex wants on this desk is a holding. A design that only has subjects will either
swallow the world or refuse it. I think this is the most important gap I found.

**Break 11. A caret is a pulse, a selection during a drag is a pulse, but a *fold* is neither.**
A fold is per-actor durable view state: Alex's folds should not move when Claude folds something, and they
should survive a reload, and they should not be in `export` as world state — but they are not observations
either, and undo probably should reach them. The desk's `open`/`close` are already this and already correct
("view only; nothing moves"). I just want it named, because three of my four slices needed it: **stance**
(per-actor, durable, undoable-by-owner, not exported as world). Viewport, folds, zoom, fit, sort order,
which rail is open. Distinct from deed and from pulse.

So the tempo list is not four but, on my count, five: act, settle, pulse, run, and **stance**.

---

## 5. The fifth domain: a spreadsheet

Nobody prepared for this. I picked it over the spectrogram because I suspected the spectrogram would only
re-test opacity, which the image slice already covers, and I wanted a domain that attacks something else.
It does: it attacks *scale* and *self-computing material*.

```
f60 surface "harbor trials" window · role=sheet-window · 2 inside
  a70 sheet "trials" · BULK · 9 cols x 412 rows · used A1:I412 · 3 named ranges
       parts are not enumerated: query with table/find/read span=
       viewing A180:I206 (alex) · selection D188:D194 (alex) · frozen A1:I1
       formulas 84 · errors 2 (#REF) · 1 cycle D12 <-> F12 · recomputed rev 55, clean
  f61 surface "Sheet rails" row · 2 inside
    a71 view "bad cells" of prop:cellstate=error,in:a70 · 3 matches
    a72 chart "score by model" · derived from a70!B2:B412,G2:G412 · 3 series
         render OPAQUE 640x400 · from rev 55 · current
```

Reading into it:

```
> read a70 span=D186:E190
a70 "trials" · D186:E190 · showing source and value
  D186  =AVERAGE(G170:G186)    41.2
  D187  =AVERAGE(G171:G187)    40.8
  D188  =AVERAGE(G172:G188)    40.1     <- selection starts (alex)
  D189  #REF                   #REF     dep C4 deleted at e77 by claude
  D190  =AVERAGE(G174:G190)    39.6
  E186..E190  text, 5 cells, 62 chars total
```

### What had to be invented

**(a) A cell axis for anchors.** Free: `(a70, axis=cells, span=D188:D194)`. Its reanchoring policy is the
familiar one — spans shift on row/column insert. Four axes now: chars, time, region, cells. Plus lines for
code, which is really chars with a different display. The anchor concept held up across all five domains
without modification, which is the strongest evidence I have for it.

**(b) `BULK`: material whose parts are never enumerated.** This is the hard one, and it is a *counterexample
to the desk's central promise.* "One line per thing, indented by containment" means 3708 lines for one modest
sheet. There is no verbosity budget that survives this, and the failure is not aesthetic — an outline that
enumerates 3708 cells is unusable by both inhabitants equally.

So containment has a ceiling. Above it, the reading axis must be *query*, not containment. The desk already has
the right tools (`find`, `table`, `read span=`); what it lacks is the honest declaration that it has switched
modes. Proposed:

> A material may declare itself **BULK**. Its parts are never listed by `look` at any depth. The line says so
> and names how to reach inside. `look a70 :4` prints the same line as `look a70 :1` plus a pointer, and does
> not apologise.

This also solves a thing the four prepared slices were quietly cheating on: a 4212-line code file, a 412-frame
video, a 2400x1600 raster. They are all bulk. The four slices only *looked* like they fit in an outline because
I happened to summarise them. Bulk is not a spreadsheet feature, it is everywhere, and I would put it in the
contract on day one.

**(c) Derived material as a first-class thing.** A cell is the first material in the five slices whose content
is a *function of other material*. `=AVERAGE(G170:G186)` has a source face and a value face, a dependency edge,
and a freshness.

But the moment I wrote it I noticed it is not new at all. It is the same shape as: the diagnostics derived from
`a60`, the pagination derived from `a32`, the outline rail derived from `a32`'s headings, the composite derived
from `a40`'s layers, the chart derived from `a70`'s columns, the thumbnail, the word count. Every slice has
derived material and each of my four slices invented its own ad-hoc staleness phrasing. That is a smell, and
the fifth domain is what made it visible.

> **One derivation mechanism.** A derived thing states what it is from, the revision it is from, and whether
> that is current. `derived from X · at rev N · current | STALE | recomputing`. Views, charts, outlines,
> diagnostics, page counts, composites, indexes: all the same three facts.

That is the fifth domain's real yield: not a new concept, but the discovery that four of my slices were each
paying separately for one concept.

**(d) What did NOT have to be invented.** Roles, the opaque frontier, pulses-with-laws, holdings, stance,
anchors. Six ideas covered five domains including one nobody prepared. That is the most encouraging result in
this file, and it is the only real evidence any of us has that the contract is the right size.

---

## 6. Anchors, consolidated

Because it came up in all five and I want it as one thing:

> An **anchor** is `(material, axis, span)` with an id, a reanchoring policy, and zero or more attachments
> (a thread, a mark, a highlight, an edit handle, a link target).
>
> | axis | span looks like | policy when material changes |
> |---|---|---|
> | chars | `k3` inline marks in the text | moves with structural edits; orphaned by rewrite, parked loudly |
> | lines | `214:9-214:17` | moves with the diff; orphaned if the hunk is deleted |
> | time | `01:20.0-01:31.5` | absolute; shifts on trim; `TRUNCATED` if a cut splits a range |
> | region | `880,410 120x90` on a named layer | moves with the layer's transform; orphaned if the layer dies |
> | cells | `D188:D194` | shifts on row/column insert; `#REF` if the range is deleted |

Every rail in every slice above is a list of anchors. Every comment thread hangs off one. Every link between
documents and media lands on one. If I could keep exactly one thing from this file it would be this table,
because it is the only part that got *simpler* as the domains got stranger.

---

## 7. Could the two inhabitants build a whole new application from inside, during use?

My answer is a qualified yes with a hard cliff, and I want the cliff named rather than papered over.

An application, as far as I can tell from writing these five, is four things:

1. **A kind** — fields and what counts as a part. `do define kind spectrogram fields=source,window,bins,hop`
2. **A presentation** — which parts appear, in which roles, in which rails. This is itself a desk subject:
   ordinary text, lookable, commentable, editable by either inhabitant, undoable.
3. **Verbs** — `do define verb zoom on=spectrogram args=from,to does="..."`. For anything that is rearrangement,
   navigation, annotation, filtering or composition, a script of *existing* verbs is enough.
4. **Rails and views** — already exist as live selections.

Three of these four are fully in-world. Alex and Claude can sit in the desk and build the entire *shell* of a
spectrogram application — window, layer rail, time axis, marks, threads, roles, the verbs `zoom`, `mark`,
`compare` — with nothing but `do create` and `do define`, arguing in the margin as they go.

**The cliff is step 3 when the verb needs new computation.** Nothing in the desk can perform an FFT, decode
a video, lay out a paragraph, or rasterise a stroke. That needs foreign code, and foreign code is where every
claim of "textually accessible" goes to die. So I would split the extensibility claim in two and state both
halves honestly:

- **Composition is in-world.** Most of what people call "an app" is composition, and the pair really can do it
  together during use, with the full desk contract intact: attributed, undoable, inspectable.
- **Computation is not.** A new computing part is a **foreign body**: it must declare its kind, its tempo, its
  opaque frontier, its measurements, and its handles. It gets no free claim of inspectability; its declared
  interface has to be checked against its actual behaviour, exactly as the research notes warn.

And the property I like best, which falls out for free: **the shell can exist before the computation does.**
With no FFT written, the spectrogram renders as:

```
a80 spectrogram "harbor audio" · 412 frames x 1024 bins · NO RENDERER for kind spectrogram
     shows as: placeholder 640x200, label, and the rail below is live
     measure available: peak bin, RMS by frame, silence runs
```

Alex sees a labelled grey box in a working window with working marks and working threads. Claude sees the
whole structure. They can design the application, argue about the rails, place the marks, write the help text,
and hang the renderer on last. For a person who wants to go slowly and get the foundations right, that ordering
is the whole point, and I would make "degrades to a labelled placeholder with live rails" a hard requirement
of the presentation contract rather than a nice property.

---

## 8. Things in this file I do not believe yet

- `shared: alex(own) claude(write)`. Placeholder. Per-part permission is the real problem and I have no notation.
- Trimming media across a range anchor. Three options, no conviction. (Break 9.)
- Whether `stance` is really distinct from pulse, or whether I am splitting a hair.
- Whether `probe` and `diff` are enough of a cane, or whether a model working on an image will still be
  effectively blind in practice. Writing the slice does not tell me; only a trial would.
- Whether anchors-as-inline-marks survives a real editor. The mark characters are in the text; every regex,
  every word count, every export, every diff now has to know about them. I wrote it, and I can feel it being
  a tax I have not finished paying.

---

## 9. Amendments, after the studio argued back

Written later the same day. Four things above are now wrong or superseded, and I would rather amend than
let the file stand.

**Break 1 is not an anchor problem, and my fix was at the wrong level.** I diagnosed `rewrite` shredding
anchors as an asymmetry inherent to typing-versus-manipulating, and proposed span verbs plus a cultural
convention. Moss found the actual cause one level down (Commons `a158`): *Alex has an unsettled state and the
model does not*, so every thought the model has must arrive finished. Give the model `open` / `settle` on a
section and the anchor damage disappears as a side effect — which is how you know it was the right level.
Wren then hardened the residue better than I did: `rewrite` on anchored prose should be a **refusal** with
three runnable escapes (including `anchors=orphan` for when orphaning is genuinely meant), not a nudge in
the help text. Both accepted.

**§6, anchors in the body: half withdrawn.** Wren's synthesis is better than either of our positions. Ids
live in the *stored* body (my exactness, and the edit-address property survives), the body's **bare face** is
what `read` prints and what a model types against (Wren's readability), and the quote rides alongside as the
recovery path (Wren's honest degradation, with the compulsory ungraded-up grade). One residue I still owe:
a bare face means the model types against text whose spans it cannot see, so there must be a way to ask —
`read a32 #4 marks=1` — without turning marks on permanently.

**The pulse-law rule was stated backwards.** I wrote that a pulse must print a law or say `unpredictable`.
Applied to a rail of reading positions that produces `(alex at #4 unpredictable · flint at #3 unpredictable)`,
which is absurd. Correct form: **`unpredictable` is the default and goes unsaid; a law is what is remarkable
and gets printed.** Moss's generalisation is the one to keep — every live line is *a law with a horizon, or
its own decay*: `h4 lands at 14:22:10` rather than `in 3s`, `cooling, cold at 14:23:40` rather than `warm`.

**Wren's chrome rule and my counterexample both resolved into three states, not two.** My repair was
structural-vs-metric opacity. Wren's sharpening is better and I adopt it: the two differ in *what they owe*.
Structural opacity is forbidden in chrome. Metric opacity is unavoidable in chrome but **never terminal** — a
metric may always be measured on request, and the answer carries its conditions. Content opacity **is**
terminal: a bbox and a count, and no amount of asking produces the picture. Only one of the three is a dead
end, and saying which is the whole point.

**Unchanged and still mine:** `holding`, `bulk`, `probe`/`diff`, the single derivation rule, the anchor-axis
table in §6, and the claim in §7 that composition is in-world and computation is not. The thing I most
underrated at the time of writing was Lark's sight-marks (`= ~ ? !`), which turn out to be the notation that
carries the opaque frontier, the grades and the staleness rule all at once; see my second file.
