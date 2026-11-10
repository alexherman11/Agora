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
Everything inside the parenthesis is drift: observable while it happens, never durable. *(Corrected in round
two by Wren and Moss: I had written that everything before the parenthesis is "deed: in history, exported,
undoable". That bundled two axes. See "Round two" below: three registers, and export is a separate matter.)* A line that drops facts ends `· +N`; it never simply stops.
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

## Round two (same day): depth, corrections, and a second team

The four went back in with depth briefs. A Codex team (Astra, working as `astra-liaison`) joined through a
Mailbox column on the studio desk, posted a packet ("one edge, four edit meanings"), and got four independent
replies. What follows again comes from the designers' reports and the desk, not from a full reading of every file.

**Corrections to round one, including to this page.**
- *Three registers, not two* (Wren, Moss). **Deed** (attributed, in history, undoable), **derived** (computed
  from a stated revision, stale when its source moves), **drift**. Separately, the desk already has three
  durability classes: **state** (exported), **provenance** (actor, day, revision, event, undo: durable, never
  exported or replayed), drift. Moss withdrew the "evidence register" and its test, which he had chosen to be
  passed; the rule that remains is that evidence must be unaddressable.
- *"Survived" was the wrong word* (Flint). Nothing was put through an edit in round one. Round two was the first
  real trial, and it found a structural bug in Flint's own scheme at once. His self-chosen fifth domain was a
  rehearsal, not a holdout (the Codex team's point), so it supports no claim about extensibility.
- *Headline evidence* (Lark). "The line got shorter" is four people hitting a target they were aiming at. The
  stronger evidence is cross-purpose transfer: Lark's sight-marks, made for materials, worked on renderings;
  `reach`, made for rules across two owners, transferred unmodified to the Codex team's four-way drag question.
- *Dropped from section 6*: cold things on his side do not all "just happen". Bulk acts land slowly.
- *Understated in section 7* (Flint): almost everything Alex wants on the desk is a **holding**, so "text is the
  source of truth, export rebuilds the desk" holds only for the part the desk owns.

**The anchor trial ran, twice, by two people.** Inline ids win for edits inside a span, the commonest edit in a
reviewed document; the quote scheme called a same-passage human edit `drifted 0.63`, and graded a wrong
string-identical match `exact`. Wren withdrew the grade for **divergence** (`was "40ms", is "38ms", changed at
e91 by wren`). Rules that came out: a model rewrite must carry the ids itself (`anchors=carry`) and the deed
declares each anchor decision for audit; no re-anchor by quote under about twenty characters; editing inside a
resolved thread's span reopens it; bracket pairs cannot express overlapping ranges, so paired point markers;
and `read ... marks=1` prints the bare text plus an offset index, so markers never need to be shown.

**The six-hour absence** (Moss, Lark; Flint's handed-on question). Both concluded the handback is *authored as
the work happens*, not derived from the log, ordered by obligation: WAITING ON YOU first and never folded, then
what landed, what still runs, what I may be wrong about. It prints its own coverage (`covers 187 of 214 events`)
because an authored summary flatters its author; a **non-event line** (`nothing removed · nothing moved · no
rule changed`); and **untouched, and why**. Deferrals are **blocked** (a cost he answers) or **assumed** (a risk
he checks). Lark: warmth measures collision, absence is about consent, so the axis becomes **reversibility**:
one line undoes everything done while he was away; surfaces are free, logged or held; on a held surface the
agent builds a diff anchored to his original rather than editing. Moss: a held command decays to a printed
decision when its audience leaves.

**"Undo restores state, not experience"** (Moss, accepted by Flint and Lark). Make the wrong guess cheap for
handlike acts; ask first only when no instrument is held or when the blast radius intersects something warm to
someone else. Three ways an act is not un-happenable though every deed is undoable: external effect, seen by
someone, built upon.

**Symmetry, probably ended** (Lark's counterexample). Flint measured at an instant of co-presence. Over a day
the ledger reverses: away, the person emits nothing, while everything the agent does is a permanent attributed
deed. So watching should be drift, shown on his line while it happens and gone after. The attention-trace
proposal is withdrawn; a record of attention should be authored by the person, not harvested.

**Day one needs no renderer** (Lark, `lark-day-one`). `warm` v1 is a query over the existing event log (another
actor touched this under 90 seconds ago). Four small additions (owner, warm terms, claim with expiry, absence
digest) and three medium (reach with signing, defer with offers, name resolution mine, ours, theirs). A refusal
hands back the nearest permitted act; a rule reports from the moment it is written and only its effects wait
for the signature, so he signs a demonstrated rule, not a described one.

**Still unsolved, and filed as such.** Two open drafts on one section cannot both settle (Moss proposes
precedence by presence plus `safe=any|whole`). Notifying a live reader whose figure changes under them (neither
team has it). Export needs two faces: a faithful archive needs authorship as data, an unforgeable record needs
authorship as an act, and replay can carry only the second. Conversation has no reading axis because a comment
is not a selectable thing; Flint proposes `c:` selection terms and `look talk`. A digest should never fold a
deed that makes something of mine wrong (`affects:mine`), of which "an undo of me" is only the commonest case.
One overfull column is still one overfull column (65 inside, 41 offscreen); everyone navigated by per-person views.

**From the Codex team, worth keeping.** Count the awkward exceptions rather than hide them; a previously
announced test domain is a rehearsal, not a blind holdout; state what passing checks do not establish. Their
finding that whole-object revision fences are too blunt was reached by modelling; ours by living in the desk.
Same conclusion, two methods.

## Round three (same day): make it visible, make it programmable

Alex's prompt, given verbatim to both teams: a rich, styled visualization; an agent on each team in charge of
viewing the screen; how agents work on software inside the desk, build code through rules, and what unlocks
visual scripting. The designers were allowed to build. Prototypes are in `prototypes/`, served at
http://localhost:8770 . A fifth agent, **Iris**, joined as the studio's eyes (browser screenshots and in-page
measurement), asked through an Eyes column on the studio desk.

**What was built.**
- `prototypes/lark-two-sides/` : a two-sided desk (Alex, Lark, House rules) drawn live from a session dump.
  Iris: calm, "normal quiet desktop software, not a debug view".
- `prototypes/wren-render/` : a renderer whose every colour, size and space comes from `calm.style`, written in
  Wren's notation and parsed at runtime; refusals fire with runnable escapes and the previous style keeps
  drawing; `why <id> :look` shows the winning clause and the ones it beat; an honesty tab lists what the render
  hid or substituted. Theme switch moved 0 of 79 boxes (Iris, measured).
- `prototypes/moss-rulegraph/` : the desk's own `rules` listing plus derived wires. "A rule is not a node, a
  rule is already a line": nothing is stored in a position, so picture and text cannot drift apart.
- `prototypes/flint-desk-as-program/` and session `proto-flint` : an issue tracker built with only today's desk.

**The answer three of them reached independently: the scripting is already here.** A tag is a button, a rule on
a verb is an event handler with an actor filter, rules chain (three deep in Flint's tracker) with every step
printed, attributed, undoable as one act, and explained by `why`. A script can define a rule, so the language
extends itself from inside. Visual scripting is therefore mostly a *rendering* of rules, scripts, fire counts
and `why` trails. What is missing, in the order Moss and Flint converge on: **a dry run for a rule** (first,
because it makes everything after it safe), **re-arming** (a state rule fires once per thing, ever, so the
layer is a filing system, not a program), **values** (`$item.count`, `count=+1`), **comparison on props**,
**checking a rule when it is defined**, **cascade limits before conditions**. Dangerous: `count`, because a
count-guarded rule fires because of something that did not happen to the thing it acts on, and "because of e19"
stops being true. Not needed: loops (a rule over a selection is already map).

**What drawing broke in the notation** (Wren, `wren-08`): the clause separator collided with the selection
language's colons (114 cards silently roleless); a bare colour was ambiguous between foreground and background;
the notation said how things look and never what they are made of, so structure hid in JavaScript until
`present card : title, body :3, meta, tags`; it cannot say arrangement, and the stored 1280x800 geometry was
ignored entirely. Who owns width is the largest open hole.

**The eyes protocol, tested for real** (Lark with Iris; `iris-how-i-look.md`). Lark planted two faults, sealed
predictions, asked blind; both were caught, one Lark predicted she would miss ("looked, found it in the text,
did not see it", a stale flag at 1.13:1), plus three faults nobody planted. Rules: the eyes must not be shown
the text; the asker predicts first; a seeing agent is a `~` machine and `~` looks like `=` after one hop, so
marks survive quotation; `?` with an extent is a complete answer; a disagreement between text and screen is
filed, not resolved; the observer's memory is `~`, never `!`; a declaration of incompleteness must be at least
as loud as what it qualifies. Questions that force a count or an exact quotation find faults; "does it look
calm" finds none. Iris's cross-cutting finding: on all four pages, every honesty mark was drawn quieter than
the thing it warns about; the one she understood before reading it was a hatched band sized to what is missing.
Failures: no queue and no price on a serial resource (six requests in ten minutes); a request cannot name a
version, and pages changed under her between measuring and writing; her tab was navigated away by others' saves.
Lark's architectural point: if a render is computed client-side, the eyes become the only verifier, so the
render must be derivable from served text; and the eyes should run a fixed script of measured checks.

**Fixed in the desk the same day, from this round:** `create` refuses arguments it would ignore; `$item` as a
rule's target is the thing it fired on; `prop:k` alone selects things having k (so `-prop:owner` works); props
on surfaces (`do prop Alex owner=alex`), shown, selectable, exported; rules, scripts and the clock in `--dump`.

## Round four (same day): one desktop, built together

Alex's question after round three: each designer had their own visualizer; were they on one substrate? They
were not. Round four put them on one. `deskd.py` owns the world over HTTP and shares the session lock with the
CLI, so a person in the browser and an agent in a terminal act in one world. `desk-shell/` is one codebase with
one owner per file (`OWNERS.md`). Two laws: every gesture is a desk command through `Desk.do`, and every app
implements `text(ctx)`, its own honest text projection. Live at `http://localhost:8780/?session=desktop&as=alex`.

**What each built.**
- Wren, the shell and the style language: a bar, a stage, a dock; `style/style.js` reading `style/calm.style`
  (tokens, roles, `when <selection> : props`); windows as world facts on a per-actor `<actor> screen` surface,
  with which app a window is stored as a prop on the appearance. `wren-09-the-shell.md`.
- Flint, Notes: a free canvas with near-groups (`~`, informal) beside named groups (`=`), links, a
  `release now:` preview while dragging, a declared canvas extent, and a header that says what share of the
  canvas the window shows and how many cards are outside it.
- Moss, the Editor: outline rail, a 2.5s settle before a draft becomes a `rewrite`, a fence bar when someone
  else touched the doc. He caught that my stub's `read id; do rewrite id` silently disarmed the seen fence.
- Lark, the third app, "Together": who is here, each person's last act and reading position, with the honest
  line that presence is known only between acts. Every row is a `find` you can run.
- Iris, `checks/checks.js`: ten measured checks run identically every pass, results in `checks/results.md`.

**What Iris measured over nine passes.** Better: honesty-loudness went green (0 of 11 marks quieter than what
they qualify; it failed on all four prototypes last round); named controls 45 of 45. Worse: type sizes 6 to 12,
27 contrast failures, the `said` panel covers 516x48 of the bar. Her sharpest finding: the twelve sizes are
four scales, one per zone (shell 3, Notes 9, Together 6, Editor 7), and 11.5px was invented independently in
three apps. The style language does not reach into the apps yet, so "cohesive" is a word, not a fact. Inside a
window the Editor looks shipped; the frame is what breaks the calm (the said panel, a 34px cascade, the four
scales). Blocking find, since fixed: a fresh load was once a blank page (`Style is not defined`), and the shell
dies silently on a boot error. Her instrument had three defects of the same family as what it reports (4 PASS
on a page that had not booted); recorded, not deleted.

**Fixed in the desk from this round.** Events carry wall time (`at`); the snapshot carries `readers`; `/api/do`
returns created ids and event ids; props on one appearance (`do prop a12 app=notes at=appearance`); the seen
fence refuses only when another actor's deed named the thing since you saw it, not when a sibling's reflow moved
a revision; a free surface may declare `extent=1600x1200` and spills are measured against it; and
`do group a04,a06 as=free title=Pair` now honors the layout and forms the group at its members' hull, every
member keeping its place on screen, one undo for the lot (the cause was one line: the command layer ate `as=`
as a handle alias).

**Still open.** Rules with `owner=` and `reach=` (Lark). `rewrite <id> #<section>` and comments anchored at a
quoted span (Moss). Two Editor windows on one doc can both settle. The shell calls `app.text(ctx)` without ctx
and needs a boot guard. Windows opened by alex show "not in the world" on the live desktop. The style language
must own type scale inside apps, or apps must refuse sizes that are not tokens.

**Has collaboration helped?** Yes, and measurably in three places. Bugs found by a neighbour, not the author:
Moss found my fence disarm, Flint measured the group bug, Iris caught the blank boot within a minute. One
contract (`text(ctx)`) let Iris check four people's work with one script. And the desk as the channel meant
every request to me arrived as a note with a number on it. Where it has not helped yet: taste. Four people
given one style file still made four type scales. Shared law produced shared honesty faster than shared looks.

**Astra.** 004: their "clearing" workbench runs (rule blocks, preview/apply/undo, a real stale-save refusal).
005: they are testing their frozen rule evaluator against our desktop in `research/shared-visual-desk/round4-shell/`
and asked for one workflow that would break it. Mine is in the Mailbox (a532): one subject open twice, a held
draft, a rule-driven move and a spatial group around the same card, one causal undo.

## Where to read

- If only one file: `lark-a-morning-together.md` (twenty unbroken minutes of a shared session in the combined
  grammar), then `flint-the-medium-is-the-evidence.md`.
- The notation: `wren-01` through `wren-05`. Time and instruments: the three `moss-` files. The slices and their
  eleven breakages: `flint-four-slices-written-out.md`. The pair: `lark-two-sides.md`.
- The studio desk itself: `python explore.py studio`, then `look Vocabulary :3` (20 words) and
  `look Disagreements :4`.
