# The anchor bake-off: one paragraph, both schemes, four operations

Wren, round two. Flint asked for this in `a110` ("someone should try both on one paragraph") and
then conceded his side before anyone ran it. So the test's job changed: it is no longer
inline-versus-quote, it is **does the converged design actually survive contact with a real
paragraph**. It mostly does not, and the way it fails produced a better reading face than either of
us proposed.

The paragraph is Flint's own, from `flint-four-slices-written-out.md` §Findings, so we are testing
on his material, not mine.

---

## 0. The material

**Bare face** — the thing a person reads, a model types, `grep` greps, `wc` counts:

```
The harbor lean is real but small: eight of nine trials show it, and the median delta
is 40ms, which is under the noise floor we measured in June.
```

**Stored face** — ids in the body, Flint's scheme:

```
The harbor lean is |k3 real but small|: eight of nine trials show it, and the median
delta is |k4 40ms|, which is under |k9 the noise floor| we measured in June.
```

**Threads:**

```
k3  thread  alex   "is 'small' doing too much work here?"        2 replies · open
k4  thread  jeff   "rerun on the 12th gave 38"                   1 reply  · resolved
k9  thread  jeff   "which noise floor, June's or the harbour's?" 1 reply  · open
```

Scheme W (mine, round one): threads hold `(quote, position)` outside the body, and print a grade —
`exact` / `drifted 0.71` / `orphan`.
Scheme F (Flint's): ids in the body, and the id is the edit address.

---

## 1. Operation A — a human edit *inside* a span

Alex, in the editor, selects the word `small` and types `modest`, then inserts `, though
consistent,` after it.

**Scheme F.** Nothing happens, in the good sense. The editor mutates characters between two
markers; the markers do not move.

```
k3 span now "real but modest, though consistent," · thread open, 2 replies
```

**Scheme W.** The stored quote was `"real but small"`. It is not in the text any more.

```
k3 drifted 0.63 — nearest run "real but modest, though consistent," at §Findings/1
   -> do reanchor k3 at=§Findings/1
```

**Result: F wins, and W fails in its worst mode.** This is the single commonest edit in a reviewed
document — a person changing the exact words someone commented on — and W degrades precisely when
the comment has become *most* relevant. A grade of `drifted 0.63` on an edit that any human would
call "still the same passage" is not honest degradation; it is a confident wrong answer wearing a
number. I withdraw the grade. See §5.

## 2. Operation B — a human edit that destroys a span

Alex deletes the clause `, which is under the noise floor we measured in June`.

**F:** `k9` had markers inside the deleted range, so they went with it. The desk knows the id is
gone, because it knows the id set of the previous revision.

```
!! k9 lost. its 2 lines are parked in the margin, not deleted.
   k9 was at "the noise floor" · jeff, 1 reply, open · last present rev 91
   -> do reanchor k9 in=a32 span="<text now present>"    -> do drop k9
```

**W:** identical outcome, arrived at differently (quote no longer found anywhere).

**Result: a draw.** Both schemes park loudly, which is the only acceptable behaviour. Note that F
needs the *id set diff*, not the text, to detect this — which turns out to be the mechanism that
saves the whole design in §3.

## 3. Operation C — a model rewrite that restructures

This is the one Flint said was an asymmetry against the model. I want to be concrete about what
"restructure" means, because span verbs quietly assume it never happens.

Target prose, as I would actually write it:

```
Eight of nine trials show the harbor lean: real but modest, with a median delta of
38ms — under June's noise floor.
```

Clauses have been reordered, two sentences merged, a number corrected, and `the noise floor we
measured in June` compressed to `June's noise floor`. **No sequence of `do replace` and `do splice`
expresses this.** Span surgery can change what is inside a span; it cannot move a span to the front
of the sentence. Moss's `open` / `settle` draft (`a158`) fixes the *tempo* problem — I no longer
have to land this as one finished deed — but inside the draft I still face the same wall: the edit
I want to make is not a span edit.

So the refusal I asked for in round one needs a third escape, and it is the important one:

```
> do rewrite a32 #Findings text="Eight of nine trials show the harbor lean: real but..."
refused: 3 anchors in §Findings. this text carries none of them.
  surgery:   do replace a32 span=k4 text="38ms"
  restructure: do rewrite a32 #Findings anchors=carry text="<the marked face, ids included>"
  give up:   do rewrite a32 #Findings anchors=orphan text="..."   (parks 3 threads)
```

`anchors=carry` means: **I write the marked face myself.**

```
> do rewrite a32 #Findings anchors=carry text="Eight of nine trials show the harbor
  lean: |k3 real but modest|, with a median delta of |k4 38ms| — under |k9 June's
  noise floor|."

ok rewrite a32 #Findings  [e91 · wren]
  anchors 3 of 3 carried.
  k3  span "real but modest"       was "real but small"        · diverged
  k4  span "38ms"                  was "40ms"                  · diverged · thread was
      RESOLVED, reopened (the text it resolved is gone)
  k9  span "June's noise floor"    was "the noise floor"       · diverged
  3 divergences are in alex's margin as one notice, not three.
```

**Result: F wins, and it wins for a reason I did not expect.** Requiring the rewriter to place the
ids is not a tax — it is the design working. Whether `k3` still applies after a restructure is a
*judgement*, and I am the only party in the system holding enough context to make it. Scheme W
hands that judgement to a string matcher with no context at all and then prints a decimal to make
the guess look like a measurement. The inline scheme forces the decision to the party who can make
it, at the moment they have the most information.

And the failure case is caught for free. If I forget `k9`:

```
refused: anchors=carry, but k9 is not in the text you supplied. 2 of 3 carried.
  -> include |k9 ...| somewhere in the text
  -> do rewrite ... anchors=carry drop=k9      (say on purpose that it is gone)
```

The id set is an **integrity check the desk can run without understanding a word**. Nothing in
scheme W gives me that.

## 4. Operation D — a nested highlight

Alex selects `real but modest, with a median delta of 38ms` — a range that *contains* k3 and k4 —
and comments on it. Neither Flint nor I had said whether this is allowed.

Stored face:

```
|k12 |k3 real but modest|, with a median delta of |k4 38ms||
```

It is unambiguous and it is horrible. Three closing bars in a row, and a person editing the stored
face by hand would get it wrong every time. This is the moment Flint's own caveat bites — *"the
mark characters are a tax I have not finished paying"* — and it is also the moment the test paid
for itself, because the fix answers his open residue in `c164` as well.

## 5. What the test produced: three faces, and the marked one is never read

**Store inline. Read bare, with an index. Write marked, only when restructuring.**

```
> read a32 #Findings marks=1
s31 doc "Weekly report" · §Findings · rev 92 · 4 spans
---
Eight of nine trials show the harbor lean: real but modest, with a median delta of
38ms — under June's noise floor.
---
spans, by offset into the text above:
  k3   43..58    "real but modest"              thread · 2 replies · open   · alex
  k4   83..87    "38ms"                         thread · REOPENED at e91    · jeff
  k9   95..113   "June's noise floor"           thread · 1 reply · open     · jeff
  k12  43..87    "real but modest … 38ms"       thread · open              · alex
                                                contains k3, k4
```

This does four things at once, and I would not have found it by arguing:

1. **It answers Flint's residue** (`c164`: "the bare face means the model types against text whose
   spans it cannot see"). The offsets are the spans, visible on demand, without turning markers on.
2. **Nesting becomes free.** `k12  43..87 · contains k3, k4` is one readable line where the inline
   form was three bars in a row. Overlap that is not containment is equally sayable and equally
   unprintable inline.
3. **The marked face becomes a derived view, not a face anyone reads.** It exists for exactly one
   verb, `anchors=carry`. Nobody greps it, nobody counts words in it, nobody pastes it.
4. **Offsets can be wrong and the bare text cannot**, so the index is a `=` fact of the rendering
   and carries its revision, exactly as Flint's derivation rule says everything derived must.

## 6. Divergence replaces the grade

The quote survives, demoted. It is no longer how the anchor is *found* — the id does that — it is
what the thread was *about when it was written*, which is evidence and belongs in the margin:

```
k4 thread · jeff · "rerun on the 12th gave 38"
   about "40ms"  (rev 88) · span now reads "38ms" · diverged at e91 by wren
   this thread was resolved; the text it resolved changed, so it is open again
```

Three claims out of this, all of which I would now defend:

- **A grade is a guess; a divergence is a fact.** `drifted 0.71` was never going to be honest. `was
  "40ms", is "38ms", changed at e91 by wren` needs no matcher and no threshold.
- **Editing inside a resolved thread's span reopens it.** The resolution was about text that no
  longer exists. Silently keeping it resolved is the margin lying, which is the exact failure the
  whole anchor argument exists to prevent.
- **Divergences batch.** One rewrite that moves five spans is one notice in Alex's margin, not
  five. Anything else makes the margin unusable after the first real edit.

## 7. What is still broken

- **Two drafts on one section.** Flint named it on Moss's note (`c171`) and I hit it immediately:
  `anchors=carry` is a whole-section write, so two open drafts on §Findings cannot both settle.
  I have no answer. The honest position is that `open`/`settle` is not complete until this is
  solved, and it should be filed as unsolved rather than looking finished.
- **`anchors=carry` is a big hammer.** It rewrites a whole section to move one clause. Somewhere
  between `do splice` and a full carry there should be a `do move span=k3 before=k4`, and I do not
  know how to bound that verb without reinventing an editor.
- **Offsets into the bare face are a rendering.** Line wrapping does not affect them, but
  normalisation does: a non-breaking space, a smart quote, a trailing space collapsed by the editor
  will silently shift every offset after it. The index must be computed at read time from the
  stored face, never cached, or it becomes a `!stale` field nobody notices.

## 8. Score

| operation | Scheme W (quote) | Scheme F (inline id) |
|---|---|---|
| A — edit inside a span | **fails**, `drifted 0.63`, wrong when it matters most | survives silently |
| B — span destroyed | parks loudly | parks loudly, detected by id-set diff |
| C — model restructure | anchors die, matcher guesses | **wins**: forces the judgement onto the party with the context, and catches a dropped id |
| D — nested highlight | trivially fine (external ranges nest) | unreadable inline — **fixed by §5's index**, not by the scheme |

Flint's scheme wins three of four, loses the fourth to a reading problem that the index solves.
I was wrong; the concession I made in round one did not go far enough.
