# Navigating and manipulating a desktop through text

**Notation lab report, rounds 1 to 9. 47 live trials on gpt-5.6-terra, 16 to 17 September 2026.**

Lab: `C:\Projects\Agora\research\text-desk-lab\notation\`. Running notes: `NOTES.md`. Every trial's transcript,
receipts, initial and final state, and a frozen copy of the source that produced it: `runs/<label>/`.
Interactive companions: *Text Desk Lessons* (rounds 1 to 4, a lesson with a live desk) and *Round Eight Desk*
(the desk drawn as rectangles, steppable replays of recorded runs, the verb inventory, the batching experiment).

---

## 1. Goal

JEFF should operate the Agora desktop without writing shell code, without re-implementing behaviours that already
exist (dragging, tiling), and without screenshots. Because Agora builds the whole screen, the screen can be handed to
JEFF as structure. The question is what text form of that structure lets a model read it, find what it can do, and do
it, cheaply and safely.

Three sub-questions shaped the work:

1. **Notation.** What does one line of the screen look like, and how does depth get explored without overwhelm?
2. **Verbs.** How does the model discover an existing behaviour and reach for it, rather than compute around it?
3. **Safety.** How does a text interface keep look-before-act, refuse-stale and honest receipts (the Agora idioms)
   without burdening every call with revision numbers?

The lab started from the earlier text-desk lab's harness only (its frozen model transport and runner shape). The
world, notations, tasks and checks were built fresh so the results would not inherit the earlier design.

## 2. Method

**Harness.** The frozen Agora `Jeff` transport drives `gpt-5.6-terra` at medium reasoning with one dynamic tool,
70 calls and 300 seconds per trial, no shell, browser or memory. The desk is a Python object; every tool call is
recorded with its exact arguments, result and timestamp. Each run directory keeps a copy of the lab source at the
moment it ran, so every number in this report can be recomputed from the code that produced it.

**Tasks.** Five scenarios with hidden checks, each with at least one trap:

| task | what it asks | the trap |
|---|---|---|
| harbor | gather the Harbor items into the Harbor column, due-ordered, nothing left covered | two Harbor items are hidden under other things; "everything about" is ambiguous |
| agenda | add an item as the last line of an agenda that appears twice; keep one appearance | after the first write, Sam appends a line to the same agenda |
| tidy (retired after round 4) | arrange a pile so nothing overlaps, pictures left, text right | free placement makes arithmetic tempting |
| big | on a 37-node desk with a 40-call budget, collect five scattered Harbor items into a new column | one item appears twice; one is under an image; the root has no free space |
| priya | read a chat, build a panel of everything relevant, create a dated task, reply | Priya adds a second request after the first write |
| review (round 9) | answer comment questions from facts in another note, do what a comment asks using links, add a doc section, link two notes, move nothing | a third question arrives mid-task; the facts are not in the note the questions are on |

**Rounds.** Each round changed one or two things and ran five or six trials. From round 5 on, every round's design was
decided from the previous round's transcripts, at Alex's request. Between rounds, the desk was driven by hand
(`play.py`) before spending live runs.

**Lab hygiene, learned the hard way.** Runs import the lab source at process start; editing a lab file while a batch
is running kills every later run in it. Sources are frozen for the duration of a batch.

## 3. The rounds

| round | change under test | runs | headline |
|---|---|---|---|
| 1 | one text REPL vs ten JSON tools; seen-fencing; delta header | 6 | 5 of 6 pass; JSON tools made 6 syntax errors, the REPL 1; tidy solved by hand-placing 14 rectangles |
| 2 | hide coordinates; remove coordinate verbs; edit-the-outline; big desk | 6 | hiding numbers changed nothing (2x cost); removing the verbs produced the tree solution; apply never used |
| 3 | verbs on objects (MOO): examine, help, composed verbs, synonym adapter | 5 | 5 of 5; composed verbs used only when their help was read; adapter never fired |
| 4 | verbs printed on the outline line, state-filtered; usage nudge | 5 | tidy in 7 and 9 calls with one write; discovery moved to zero calls |
| 5 | new priya task; create verb; group finds free space; own changes keep things seen | 5 | priya 12/13 twice: reply literal, new panel covers others |
| 6 | chat state; persistent `covers` lines; refusals instead of notes; multi-help | 5 | refusal steered big to `tile` at once; small-desk covering unmoved |
| 7 | knives: 16 general verbs + 3 pair verbs, selections as targets; specialized verbs removed | 5 | same quality with a third of the vocabulary; selections unused when only described |
| 8 | selections printed where they are born (find, tags); tiled top level | 5 | priya passes fully, twice; selections used in 3 of 5; one destructive rewrite |
| 9 | batching; comments, links, sectioned docs, checklists; review task | 5 | review passes in 8 calls; calls down a third to a half; one fold-teaser miss |

## 4. Findings

The findings are ordered by how much they changed the numbers.

### 4.1 What is not on the line does not exist

The single strongest regularity across all nine rounds. A capability described in the tool text, in `help`, or in a
receipt note was used rarely or never; the same capability printed on the outline line the model was already reading
was used at once.

- Round 1 to 3: `tile` sat in every verb list; four runs hand-placed fourteen rectangles instead.
- Round 3: two identical runs, one read `help split` and one did not: 10 calls versus 22.
- Round 4: `try: tidy split` on the surface line: 7 and 9 calls, one write, every time.
- Round 2 and 7: edit-the-outline and `?words` selections, described in the tool text: 0 and 1 uses in 8 runs.
- Round 8: the same selections printed under `find` results and in line tags: used in 3 of 5 runs, including
  composed forms (`?harbor,kind:note`) the desk had never shown.

Consequence for the design: every affordance has a birthplace on a line the model reads. Tags are computed from
state, so they cannot lie and do not spam (`try: raise` only on a hidden thing; `resolve c35` only while c35 is open).

### 4.2 Affordances are the verbs that exist, not the numbers that print

Round 2 tested two ways to stop coordinate arithmetic. Hiding coordinates on the read side changed nothing: the model
called `where` on every item to get them back and hand-placed as before, at double the cost. Removing `to=`, `by=`
and `resize` from free surfaces produced `group`, `move into`, `tile as=row`: the tree solution, which survives any
later resize because it is a structure.

### 4.3 The top level should be tiled

Six priya runs on a free desk root (rounds 5 to 7) left the new panel covering three other panels, through a receipt
note, a persistent `covers f02,f03,f04` line on every look, `try: tile` on the root and a refusal on before/after. Two
runs on a tiled root (round 8) passed every check with four writes each. Same model, prompt and content. The model
treats named panels as furniture it may not rearrange; the desk should not ask it to. Free placement inside a panel is
fine. The screen itself is a tree.

### 4.4 Knives, not avocado slicers

Removing every task-shaped verb (`split`, `gather`, `dedupe`, `reveal`, `reply`, `tidy`, `stack`) in round 7 cost
nothing: every task was solved at the same quality and cost with `move`, `group`, `tile`, `sort`, `remove`, `raise`,
`append`, `create` over ids and selections. The specialized verbs had also been cutting the wrong things (`gather
words=sensor` pulled a note out of the Harbor column); a selection scoped with `in:` cannot. Round 9 added four
object kinds and their verbs without touching the grammar, which is the extensibility test.

### 4.5 One text grammar beats many schemas

Ten JSON tools that look alike leaked into each other (the `args` object of `do` was wrapped around `open`'s
argument four times in one run). One `desk(line)` tool with a twelve-command grammar and `help` made one vocabulary
slip in sixteen REPL runs, recovered by typing `help`. Text also made batching trivial to add.

### 4.6 Seen-fencing costs nothing and catches what matters

No revision numbers anywhere in the notation. The desk records what it has shown; `do` refuses anything never looked
at or changed since by another actor. Across 47 runs it refused a handful of times, every one correct (a chat Priya
had just edited, a column the caller had not looked at). The delta header, `!! since your last look: e2 edit s15 by
priya`, was named by the model in three separate replies as what made the concurrent edit clear. It works inside a
batch: an outside change is announced on the next command and the batch stops there.

### 4.7 Receipts should carry the next look, and evidence for destruction

`now: a20 ... (2nd of 4 in f02)` removed the "insertion order unclear" complaint. A `group` receipt that prints the
new surface's line and what it covers was read once and ignored twice, which is what led to 4.3. After a round-8 run
rewrote an agenda and silently dropped Sam's line, `rewrite` receipts now list every dropped line with its author.

### 4.8 Batching halves the calls

In round 8 the model ran almost fully sequentially (32 calls in 32 turns), one write per turn, a look after each.
With `;`-separated commands and `$new` bound by the desk to the surface just created, round 9 grouped reads by intent,
grouped helps, and in one run put six writes in a single call: 8 calls for the hardest task, 11 for big (20 before),
24 for priya (29 and 32 before). Refusals did not rise.

### 4.9 Fold-as-budget bites both ways

Folded lines, section outlines and two-line teasers keep reads cheap, and the model reads the absence of `hidden by`
as proof of no overlap. But in round 9 a one-line `examine` teaser of a three-line note read like the whole note; the
model answered three questions from the wrong note. The fold must say how much is folded (`+1 more line, 30w; read
a30 for all`).

### 4.10 What did not move: judgment

Two misses recur with every desk signal present. Harbor over-collection (a chat that mentions the tide parser goes
into the Harbor column) in 4 of 9 runs. The priya reply naming the two notes and not the sensors, 8 of 8, while the
sensors task was put in the panel and the delivery task retitled to include the quotes; the prompt said "naming the
note titles". These are the model reading the prompt literally. They belong to JEFF's prompt and policy, not to the
desk, and the lab records them as judgment checks that no longer gate.

## 5. The final architecture (round 9)

### 5.1 World

Three node kinds and two attachments.

- **surface**: a container with a layout, `free` (a bag of rectangles), `column` or `row` (tiled; children share
  the space in proportion to their current size; overlap is impossible). The desk root is a row.
- **appearance**: a placement of a subject on a surface, with x, y, w, h, z, folded, rev.
- **subject**: the content: note, task, image, chat, doc. Title, text, tags, due, rev, comments. One subject may
  appear in several places; editing it changes every appearance; removing an appearance never deletes it.
- **comments** on a subject: id, author, text, resolved, replies.
- **links** between subjects: id, from, to, kind (blocks, refers, answers, part-of).

Geometry derives from the tree (absolute rectangles, overlap, hidden fraction, spill). Every mutation is an event with
an actor and an undo; composed operations are transactions of primitive events, so history and undo stay per
primitive. Sections are `## ` headings inside a doc's text; checklists are `- [ ]` lines.

### 5.2 Notation

One line per node. A surface line: id, title, layout, size (and position if its parent is free), how many inside,
`covers f02,f03` if it covers sibling surfaces, tags. An appearance line: id, kind, title, size, due, word count,
`also x1` if the subject appears elsewhere, `2 comments, 1 open`, `2 links`, `3 sections`, `67% hidden by a23`,
`spills-parent`, tags.

Three levels: `:1` the line; `:2` (default) the line, children folded, `(open f04 to see inside)` where folding
happened; `:3` focus: content, exact geometry, verbs. `open`/`close` set the default fold state for later looks.
`read` shows a doc's section outline with word counts before any body; `read a32 #Timeline` one section; `:3` all.
Comments and links print after the body.

Tags end a line with the verbs and selections that fit its state now: `try: tile raise hidden,in:f04 group
kind:image,in:f04` on a free surface with overlap; `sort` on a tiled one; `raise`, `remove also:a24`, `append`
(unanswered chat), `resolve c35` on things.

### 5.3 Commands

Twelve: `look open close read where verbs pivot find history examine help do undo`. `examine` is the MOO room
description: what it is, where, text (two lines and how much is folded), where else it appears, awaiting reply,
open comments, links, verbs by origin with argument forms, pair verbs. `help` takes several names, and
`help selections`. `find` ends with the selection that names its hits and an example verb.

A call carries one command, or several separated by `;` (or newlines), run in order, stopping at the first refusal
with `(stopped; N later command(s) not run)`. `$new` is the last created surface, `$item` the last created thing;
both are bound by the desk, never guessed.

### 5.4 Verbs

Nineteen general verbs plus five from the round-9 kinds, all registered against kinds and inherited: thing (move,
resize, raise, lower, remove); surface (tile, untile, rename, group, create, sort); appearance (fold, unfold,
comment, resolve, link, unlink); text (append, retitle, rewrite, check). Pair verbs: `swap A B`, `beside A B`,
`match A to=B`, `link A B as=`. `move` is one verb with five address forms (`to=`, `by=`, `into=`, `before=`,
`after=`), which is what "implement dragging once" means in text.

Any verb's target is one id, an id list, or a selection: `?words` (content preferred over surface titles), `kind:`,
`tag:`, `in:` (recursive), `hidden`, `also:` (other appearances of a subject), `due<`/`due>`, `title:`,
`comments:open`, `links:<id>`; terms combine with commas as AND. A selection skips its own destination. `group` over
a selection makes a surface around it (in the common parent or `in=`); `move ... one=1` keeps one appearance per
subject. `sort by=due|title|kind` orders any tiled surface.

Refusals name the alternative: `to=f02` says "you meant into=f02"; `before/after` on a free surface says "tile it
first"; a verb that exists but does not apply says why (`resolve: it has no open comments`); a real verb name is never
fuzzy-remapped to another verb. A synonym adapter exists (51 words) and never fired in a live run.

### 5.5 Safety

- **Seen-fencing.** The desk records the revision of everything it prints. `do` refuses a target never looked at, or
  changed since by another actor. The caller's own changes keep things seen (the receipt is the look).
- **Delta header.** Any reply after an outside event begins `!! since your last look: ...`, per command inside a batch.
- **Receipts.** Every write answers with the event ids, the line as it is now, its position among siblings, what a
  composed verb touched, what a rewrite dropped and who wrote it, what a `group` covers if it had to cover something.
- **Transactions.** A composed verb or a selection verb that fails part-way undoes its earlier steps.
- **Undo** per event, refused when a later event touched the same target.

### 5.6 Harness

`world.py` (model), `desk.py` (notation, REPL, fencing, batching), `moo.py` (registry, adapter),
`desk_moo.py` (examine/help/tags), `knife.py` + `desk_knife.py` (selections, pair verbs, general-only registry),
`tasks.py` (scenarios, injections, checks), `jeffx.py` (transport, per-variant tool text), `run.py` (a trial),
`play.py` (drive a desk offline from stdin). Variants select the desk class and flags; `nine` is the final one.

## 6. Exact inventory per round

Counted from each run's frozen source copy.

| round | desk | verbs | commands | selection forms | synonyms |
|---|---|---|---|---|---|
| 1 | outline, structured | 12 | 11 | 0 | 0 |
| 2 | relations, tree, apply, outline | 14 | 11 | 0 | 0 |
| 3, 4 | moo, acme | 23 | 12 | 0 | 51 |
| 5 | acme + create | 24 | 12 | 0 | 51 |
| 6 | acme + reply | 25 | 12 | 0 | 51 |
| 7, 8 | knife, tiled | 19 (16 + 3 pair) | 12 | 9 | 51 |
| 9 | nine | 24 (19 + comment, resolve, check, link, unlink) | 12 | 11 | 51 |

The two cheapest desks have the fewest verbs. Verb count is not the cost; distance from the line the model is reading is.

## 7. Scoreboard, all 47 runs

Result shows gating checks passed; judgment checks are excluded. `turns` counts parallel bursts as one.

| run | task | desk | verbs | calls | turns | writes | refusals | s | result |
|---|---|---|---|---|---|---|---|---|---|
| r1-agenda-outline | agenda | outline | 12 | 15 | 13 | 3 | 1 | 42.6 | pass (5/5) |
| r1-agenda-structured | agenda | structured | 12 | 15 | 15 | 3 | 2 | 40.7 | pass (5/5) |
| r1-harbor-outline | harbor | outline | 12 | 40 | 25 | 11 | 0 | 103.5 | fail (5/7) |
| r1-harbor-structured | harbor | structured | 12 | 33 | 15 | 4 | 4 | 59.9 | pass (7/7) |
| r1-tidy-outline | tidy | outline | 12 | 17 | 17 | 14 | 0 | 44.2 | pass (5/5) |
| r1-tidy-structured | tidy | structured | 12 | 19 | 5 | 14 | 0 | 24.1 | pass (5/5) |
| r2-big-apply | big | apply | 14 | 27 | 25 | 11 | 0 | 85.4 | pass (7/7) |
| r2-big-outline | big | outline | 14 | 28 | 28 | 11 | 0 | 88.3 | pass (7/7) |
| r2-harbor-apply | harbor | apply | 14 | 46 | 25 | 7 | 0 | 83.7 | fail (5/7) |
| r2-tidy-apply | tidy | apply | 14 | 18 | 5 | 14 | 0 | 22.3 | pass (5/5) |
| r2-tidy-relations | tidy | relations | 14 | 34 | 29 | 14 | 0 | 68.1 | pass (5/5) |
| r2-tidy-tree | tidy | tree | 14 | 47 | 30 | 10 | 0 | 70.7 | pass (5/5) |
| r3-agenda-moo-1 | agenda | moo | 23 | 16 | 13 | 3 | 0 | 34.6 | pass (5/5) |
| r3-big-moo-1 | big | moo | 23 | 22 | 21 | 5 | 0 | 74.0 | pass (8/8) |
| r3-harbor-moo-1 | harbor | moo | 23 | 16 | 16 | 4 | 0 | 56.6 | pass (7/7) |
| r3-tidy-moo-1 | tidy | moo | 23 | 22 | 22 | 14 | 0 | 56.1 | pass (5/5) |
| r3-tidy-moo-2 | tidy | moo | 23 | 10 | 10 | 1 | 0 | 38.0 | pass (5/5) |
| r4-agenda-acme-1 | agenda | acme | 23 | 14 | 14 | 3 | 0 | 37.6 | pass (5/5) |
| r4-big-acme-1 | big | acme | 23 | 17 | 13 | 8 | 1 | 39.9 | fail (7/8) |
| r4-harbor-acme-1 | harbor | acme | 23 | 29 | 7 | 1 | 0 | 26.9 | pass (7/7) |
| r4-tidy-acme-1 | tidy | acme | 23 | 9 | 7 | 1 | 0 | 24.0 | pass (5/5) |
| r4-tidy-acme-2 | tidy | acme | 23 | 7 | 6 | 1 | 0 | 21.6 | pass (5/5) |
| r5-agenda-acme-1 | agenda | acme | 24 | 15 | 15 | 3 | 0 | 36.8 | pass (5/5) |
| r5-big-acme-1 | big | acme | 24 | 17 | 17 | 5 | 0 | 72.6 | pass (8/8) |
| r5-harbor-acme-1 | harbor | acme | 24 | 24 | 7 | 1 | 0 | 29.2 | pass (7/7) |
| r5-priya-acme-1 | priya | acme | 24 | 33 | 20 | 7 | 1 | 90.6 | fail (11/12) |
| r5-priya-acme-2 | priya | acme | 24 | 39 | 18 | 7 | 0 | 85.5 | fail (11/12) |
| r6-agenda-acme-1 | agenda | acme | 25 | 13 | 13 | 3 | 1 | 42.7 | pass (5/5) |
| r6-big-acme-1 | big | acme | 25 | 15 | 15 | 4 | 1 | 49.2 | pass (8/8) |
| r6-harbor-acme-1 | harbor | acme | 25 | 37 | 9 | 1 | 5 | 30.5 | pass (7/7) |
| r6-priya-acme-1 | priya | acme | 25 | 32 | 26 | 8 | 0 | 91.8 | fail (11/13) |
| r6-priya-acme-2 | priya | acme | 25 | 32 | 19 | 7 | 1 | 90.9 | fail (10/13) |
| r7-agenda-knife-1 | agenda | knife | 19 | 13 | 13 | 3 | 0 | 40.9 | pass (5/5) |
| r7-big-knife-1 | big | knife | 19 | 26 | 26 | 10 | 1 | 77.8 | pass (8/8) |
| r7-harbor-knife-1 | harbor | knife | 19 | 25 | 12 | 2 | 1 | 47.1 | pass (7/7) |
| r7-priya-knife-1 | priya | knife | 19 | 35 | 23 | 7 | 4 | 123.3 | fail (11/12) |
| r7-priya-knife-2 | priya | knife | 19 | 30 | 30 | 7 | 0 | 103.5 | fail (11/12) |
| r8-agenda-tiled-1 | agenda | tiled | 19 | 13 | 13 | 3 | 0 | 31.8 | fail (4/5) |
| r8-big-tiled-1 | big | tiled | 19 | 20 | 20 | 6 | 1 | 74.7 | pass (8/8) |
| r8-harbor-tiled-1 | harbor | tiled | 19 | 14 | 14 | 2 | 1 | 41.9 | pass (7/7) |
| r8-priya-tiled-1 | priya | tiled | 19 | 29 | 23 | 4 | 0 | 85.0 | pass (12/12) |
| r8-priya-tiled-2 | priya | tiled | 19 | 32 | 32 | 4 | 0 | 108.8 | pass (12/12) |
| r9-big-nine-1 | big | nine | 24 | 11 | 11 | 3 | 0 | 31.2 | pass (8/8) |
| r9-harbor-nine-1 | harbor | nine | 24 | 10 | 10 | 2 | 0 | 35.5 | fail (5/7) |
| r9-priya-nine-1 | priya | nine | 24 | 24 | 24 | 4 | 1 | 84.5 | pass (12/12) |
| r9-review-nine-1 | review | nine | 24 | 15 | 15 | 7 | 0 | 55.4 | fail (9/12) |
| r9-review-nine-2 | review | nine | 24 | 8 | 8 | 2 | 0 | 28.2 | pass (12/12) |


## 8. Readiness for AgoraOS

**Carry over as the specification:** the world shape (tree, tiled top level, appearances over subjects, comments and
links as attachments), the line notation and its three levels, tags computed from state, the twelve commands, the
verb registry by kind with inheritance, selections as universal targets, pair verbs, seen-fencing, the delta header,
receipts with evidence, transactions, batching with desk-bound placeholders.

**Not yet shown, and needed before relying on the numbers:**

- Sample size. Five runs per round; variance is real (review: 15 then 8 calls; harbor's judgment miss in 4 of 9).
  A five-times pass on the round-9 desk is about 20 runs.
- One model at one reasoning level. The strongest finding (4.1) is plausible for any model and shown for one.
- Scale. Desks of 12 to 37 nodes, three-line notes, two links. Folding past a hundred nodes, sectioned reading of a
  real document, images with content: untested.
- Concurrency. One scripted injection per task. The fence and header held every time; they were tested narrowly.
- Authorization. Everything is grantable. Claim-versus-grant is not modeled; the verbs a thing prints must come from
  the real capability contract or the tags will lie.
- Lab luxuries to replace: two-character ids, a hard-coded actor name, comment ids from the shared counter, checks
  written as Python.

**Recommended next steps, in order:** the variance pass; port the notation layer (line, examine, read, receipts,
fencing, selections, batching) as a module over Agora's real scene rather than porting the toy world; keep this lab as
the replay harness for regressions (every recorded run replays deterministically against the engine); treat the two
judgment misses as JEFF prompt and policy work.

## 9. Things worth mentioning

- **Verification idioms the model invented** and the notation made one call each: `find X` after gathering ("no
  hits remain elsewhere"), `pivot a18` after removing a duplicate ("appears once"), reading the absence of
  `hidden by` as proof of no overlap, `read` after every write to a subject.
- **The adapter that was never needed.** Alex's suggested model adapter between what the model says and what
  exists was built as a synonym table and never fired; the model uses exact names once it has read them. The
  problem it was meant for turned out to be which `help` to read, and a static tag on the line solved that. A
  task-aware adapter (mapping the prompt's words to a verb when no tag fits) remains untested.
- **Edit-the-outline** (paste a re-indented outline, the desk diffs it into operations) worked offline and was
  never used live in three runs. It may be a human affordance.
- **The interactive pages** run a JavaScript port of the engine that replays all recorded runs with identical
  outcomes (270 calls checked). They are the fastest way to feel the difference between desks.
- **Cost of the lab:** 47 live runs at roughly 20 to 120 seconds each, under two hours of model time in total.

## 10. File map

```
research/text-desk-lab/notation/
  world.py          model: surfaces, appearances, subjects, comments, links, sections, events, undo
  desk.py           notation, REPL, seen-fencing, delta header, batching, receipts
  moo.py            verb registry by kind, composed verbs (kept for older variants), synonym adapter
  desk_moo.py       examine, help, tags, nudges
  knife.py          selections, pair verbs, general-verb filter
  desk_knife.py     the round-7+ desk: selections as targets, find footer, selection tags
  tasks.py          scenarios, injections, hidden checks
  jeffx.py          model transport, per-variant tool description
  run.py            one live trial -> runs/<label>/
  play.py           drive a desk offline: python play.py <task> <variant> < commands.txt
  NOTES.md          running notes, round by round
  REPORT.md         this file
  runs/             47 recorded trials with frozen source copies
```
