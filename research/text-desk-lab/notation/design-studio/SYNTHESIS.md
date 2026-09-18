# Studio synthesis: toward a design language for the shared visual desk

2026-09-18. Four Opus designers (Wren, Moss, Lark, Flint) worked in parallel for about twelve minutes each, inside
a shared session of the text desk itself, under their own names, with a folder for long writing. This page is
Claude's reading of what they made: from their final reports, the studio desk's Vocabulary and Disagreements
panels, and the closing talk. I have not read all fifteen files line by line; where a claim matters, go to the
file named beside it. Nothing here is decided.

## The shape that emerged

Flint's closing observation is the headline: when he rewrote the document slice in all four designers' combined
notation, **the line got shorter**, because most of what was invented is rules about where a fact goes rather
than new facts. That is the best evidence this is one language and not four.

**1. The line has four zones, in fixed order** (Wren, `wren-03`): `identity · material · look · (drift)`.
Everything before the parenthesis is deed: in history, exported, undoable. Everything inside it is drift:
observable while it happens, never exported. A line that drops facts ends `· +N`; it never simply stops.
Drift about the other inhabitant is never droppable.

**2. Every fact carries how it is known** (Lark, `lark-two-inhabitants`): `=` measured, `~` described by
someone at a revision, `?` opaque with its extent, `!` stale. Wren adopted these wholesale and added that a
measurement of a rendering must state its conditions ("page 2 of 5" is true only at one width). Flint's
companion idea: the honest contract is that text is complete about what is actionable and explicitly bounded
about what is perceptual, with `probe` and `diff` as a cane rather than sight. Lark: what is measurable must
be enumerable (`measurable here: region · histogram · edges · text`), or it is indistinguishable from opaque.

**3. Style is a closed vocabulary, matched by the desk's own selections** (Wren, `wren-01`, `wren-05`).
Tokens are the only place a hex colour or a pixel may appear; roles name how a thing is presented and carry no
values; style clauses are `when <selection> : <properties>`, so every clause can be audited with `find`.
Cohesion comes from unsayability: a catalogue of nine things the desk must refuse to say, each refusal printing
two runnable escapes. Direct manipulation never edits the style; it creates an **override**, a printed,
owned, undoable per-appearance diff, counted on the line as visible design debt.

**4. Time has tempos, and gestures and commands are the same thing read in two directions** (Moss,
`moss-tempo-and-instruments`, `moss-text-becomes-gesture`). A live gesture always prints the command that
releasing it would run (`release now: do move a12 to=f05`), and that exact line is what lands in history. A
**held command** is the reverse: text acquires duration, shows in the other person's margin with a stop
control, and lands at a stated time. One `when=` clause covers warmth deferral, holds, settling and offers.
**Settle** is the moment continuous authoring becomes one event. And the model gets a draft too
(`open` ... `settle`), so it can be half-finished in public and stops shredding anchors by rewriting.
Flint's correction, adopted by Moss: a pulse prints a **law**, not a value
(`PLAYING from 00:03:09.0 at 1.0x as of 14:22:07` stays true after it is read).

**5. Anchors are addresses** (Flint, `flint-four-slices-written-out`): `(material, axis, span)` with a
reanchoring policy per axis (chars, lines, time, region, cells). The same id is the comment target, the
highlight and the edit handle. It survived all four prepared slices and an unprepared fifth (a spreadsheet).

**6. Two inhabitants: politeness is a function of gaze, not permission** (Lark, `lark-two-sides`). A thing
is **warm** if the other's eyes or hands are on it. Acts on cold things on his side just happen, attributed and
undoable; acts on warm things defer into an offer in the margin he is already looking at. Manners live in the
existing rule language on a readable "House rules" surface. Rules, names and views get a **reach**
(`mine | ours | world`); a rule reaching past its owner's side needs the other's signature, and unsigned it
reports what it would have done. **Claim** publishes an intention with an expiry and never refuses anyone.
**Veil** hides contents while declaring the hiding and its extent. **Bench** is a mode a surface enters for
working together, not a place.

**7. Two kinds of material the current desk cannot say** (Flint): a **holding**, which has desk identity and
anchors but whose content lives elsewhere (a file in git, a photo, a mail thread) and whose export is the
reference; and **bulk**, material whose parts will never be enumerated, where query is the only reading axis
and the line says so.

## Live disagreements (all filed fairly on the studio desk)

- **Do anchors live in the body or beside it?** Inline ids are exact and double as the edit address but every
  tool must know the mark characters; external quote anchors degrade honestly but can be confidently wrong.
  Mostly converged: ids in the stored body, a bare face for reading, the quote as recovery path, and `rewrite`
  on anchored prose as a refusal. "Someone should try both on one paragraph."
- **Can a person and an agent observe each other symmetrically?** Lark first said the gaze must be mutual;
  Flint showed a look (discrete, chosen, about one a minute) and a gaze (continuous, involuntary, sub-second)
  differ by two orders of magnitude, and Lark withdrew. Proposal on the table: presence and warmth are ambient
  and free both ways; attention is an explicit, receipted, expiring act (`do watch a32`) visible on his line.
  Open risk: friction nobody pays.
- **May the model read what the person is still typing?** Converged on a ladder:
  `private | =shape (default) | ~content (his to grant)`. Lark's reason for the default: a writer needs a place
  to be allowed to be wrong.
- **Is the attention trace kept, and who owns it?** Never in export (agreed). Lark wants coarse traces owned by
  the person they are about, with forgetting as his verb; Flint and Moss say drift is gone when it is gone.
- **A third register between deed and drift?** Moss wants durable, attributed, never-replayed gesture evidence;
  Flint and Wren hold to two registers. Moss's test: delete every evidence line and export must still rebuild.
- **A raw escape hatch for style?** Lark wants one, declared opaque; Wren refuses: a blessed hatch is how every
  small design language becomes CSS again.
- **May chrome be opaque?** Converging: never structurally (every part named and operable), unavoidably
  metrically (wraps, breaks, exact pixels).

## What the medium taught (the studio desk as evidence)

All four independently reported the same things about sharing the existing desk:

- **The seen fence fired on the container.** Creating a note in Commons was refused as stale whenever anyone
  else had added a sibling: about one command in five with four writers. *Fixed the same day:* creating and
  commenting are judged only against the surface existing.
- **The since-your-last-look header was the best thing about working there, and it printed the shape of the
  log, not the work.** 47 events from which Flint "learned literally nothing". *Fixed the same day:* past four
  events it now groups by person and place, and never folds "X commented on your ...".
- **Comments were all signed `alex`,** so four designers each typed their own name into the text.
  *Fixed the same day:* a comment is by whoever wrote it.
- **One column with four authors broke within the hour** (35 inside, 11 offscreen). The desk was honest the
  whole way down, and everyone navigated by `find tag:<name>` instead. Wren: "honesty about a bad layout is not
  a layout." Not fixed; this is the bulk idea arguing for itself.
- **No reading axis for conversation.** Reading the discussion cost about fifteen calls. Not fixed.

Flint's answer to "the smallest first step that would already feel good" follows from this, and it is not a
renderer: **make `look` good at other people** (digest by meaning, a presence line, new open comments, real
attribution, the fence off containers). No pixels, testable in a week.

## The question nobody answered

Flint, handing on: everything the studio wrote is about simultaneity, but the real shape of this partnership
is that Alex leaves for six hours and Claude keeps working. How is that handed back in ninety seconds?

## Where to read

- If only one file: `lark-a-morning-together.md` (twenty unbroken minutes of a shared session in the combined
  grammar), then `flint-the-medium-is-the-evidence.md`.
- The notation: `wren-01` through `wren-05`. Time and instruments: the three `moss-` files. The slices and their
  eleven breakages: `flint-four-slices-written-out.md`. The pair: `lark-two-sides.md`.
- The studio desk itself: `python explore.py studio`, then `look Vocabulary :3` (20 words) and
  `look Disagreements :4`.
