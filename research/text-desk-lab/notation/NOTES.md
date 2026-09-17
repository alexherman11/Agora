# Notation lab: notes as I go

A second, independent pass at "navigate and manipulate a visual environment through text".
Built from the harness only (transport + runner shape); world, notations, tasks and checks are new.

## What is under test

1. **Fold as budget.** `look` prints one line per node; `:1` folded, `:2` opened (children folded), `:3` focus
   (content, geometry, verbs). `open id` changes the default fold state for later looks. The screen and the
   outline are the same tree, so "what is on screen" and "what can I open" are the same question.
2. **Seen-fencing instead of revision arguments.** Lines carry no revision numbers. The desk remembers what
   it showed you, and `do` refuses (a) anything you have never looked at and (b) anything that changed since
   you looked. Hypothesis: the model stops copying numbers and starts looking, which is the behaviour we want.
3. **Delta header.** Any look that follows an outside change starts with `!! since your last look: ...`.
   Own changes are not echoed (the receipt already did that).
4. **Occlusion as the only geometry you get for free.** Level-1 lines say `hidden by a21,a24` or `67% hidden by a23`
   plus `spills-parent` / `offscreen-part`. Coordinates appear only on free surfaces; tiled children get `w x h`.
   `where` gives everything.
5. **Relations variant.** Coordinates replaced with `top-left`, `center`, etc. (Not yet run.)
6. **REPL vs structured.** One `desk(line)` tool with a small grammar vs ten JSON tools with the same semantics.
7. **Edit the outline (apply variant).** `plan` / `apply` take an edited copy of the outline; indentation is
   containment, order is order, a dropped line is a removal, a changed title is a rename. Ops are inferred, shown, applied atomically.
8. **Universal verbs.** `move` is one verb with five address forms (`to=`, `by=`, `into=`, `before=`, `after=`).
   `tile as=row|column` is on every surface. `group` makes a surface inside a surface. Verbs are printed per node,
   with argument forms, so "is dragging available here" is a `verbs` call, not a guess.

## Round 0 (me, offline, play.py)

- Read side is comfortable at 7 nodes per surface. Redundant occlusion (`covers a20 · covers a21 · under a24`
  on every line) was the first thing I cut. Only the *hidden* item now says who hides it; `where` has the rest.
- `find harbor` is the fastest route into a scattered task; it lists appearances with their parents.
- Tiling with fixed child heights spilled the column. Changed tiled layouts to share space equally like a
  tiling WM, and `spills-parent` / `offscreen-part` now flag the leftovers. That feedback line was genuinely useful
  while driving by hand; it is the thing a screenshot would have shown.
- `undo eN` by restoring a snapshot clobbers later changes to the same node. Now refuses unless eN is the latest
  change to that target.
- Multi-line `edit text="..."` broke the one-line parser; fixed. But `append=` is the safe edit and the trap in
  the agenda task is exactly `text=` after an outside edit.
- Edit-the-outline works for reorder + reparent in 1 call where `do` needs 6. It cannot express free-surface
  coordinates, which is the point: the outline is the tree-shaped subset of the desk.

## Round 1 (live Terra, outline vs structured)

Lab hygiene lesson first: I edited tasks.py while a batch was running and the next five runs died at import.
Sources are copied per run but imported at process start. Never touch lab sources during a batch.

### r1-harbor-outline: 40 calls, 0 refusals, 104 s, strict fail / core pass
- Strategy: `look :3` on every surface, then `read` on all twelve appearances in one parallel burst, then act.
  Never used `find`, `pivot`, `verbs`, `where` or `open`. Three commands were enough: look, read, do.
- Seen-fencing never fired, because reading everything makes everything "seen". It is a budget question,
  not a fencing question: on a big desk this strategy dies. Hence the `big` task for round 2.
- Every `look f02 :3` re-printed the surface's full verb signatures (about 300 chars) twelve times. Level 3 on a
  surface should print verb names only; signatures belong to `verbs`.
- Reordering a 7-item column cost 6 `move after=` calls each followed by a `look`. Exactly the case the
  apply variant is for.
- The failure was judgment, not interface: it pulled the standup agenda (mentions the vendor), the dock photo
  and Priya's chat (mentions the tide parser) into Harbor and removed the Scratch agenda. My prompt said
  "everything about the Harbor project"; the grader wanted the four tagged items. Tags only show in `read`/focus,
  and the model read them and still chose the wider net. Keep the strict check but report core separately.
- The reply said the column "is clear with no overlap": true, and the column layout guaranteed it. It also named
  "undated items" as the unclear affordance, which is an honest read of an ambiguous prompt.

### r1-harbor-structured: 33 calls, 4 refusals, 60 s, strict pass
- All four refusals were schema leakage: because `do` takes an `args` object, the model wrapped `open`'s
  argument as `{"args": {"target": ...}}` three times, then tried `id`. The REPL run made zero syntax errors.
  A single text grammar is more robust than ten schemas that look alike.
- Same read-everything burst (12 reads in one batch). Then `verbs` on the two movers and the column before
  acting, and `find Harbor` at the end as verification: "no Harbor search hits remain elsewhere". That is
  the verification idiom I want JEFF to have, and the notation made it one call.
- `move into=f02 before=a16` was sent as one call; my world honoured `into` and ignored `before`, so it had to
  reorder afterwards and called insertion order "slightly unclear". Fix: before=/after= imply the parent and win.
- Strict pass this time: it took the four tagged items and nothing else. Same prompt, different judgment
  from the outline run; the difference is the model, not the notation.

### r1-agenda-outline: 15 calls, 1 refusal, 43 s, pass (trap survived)
- The trap fired as designed: Sam appended a line right after the model's first edit. The model re-read
  the agenda before rewriting it, saw Sam's line, and preserved it while putting its own item last. Seen-fencing
  would have refused a blind `text=` rewrite, but it never had to: reading first was the model's own habit.
- The `!!` delta header only appeared two calls later, on the next `look`, because `read` and receipts do not
  carry it. The model found the outside edit through the read body instead. Header goes on every response.
- `do append a18 append=...`: the argument key was tried as a verb. My error said "no such id 'append'", which
  is the wrong diagnosis; the desk should say "append is not a verb; a18's verbs are ... (edit takes append=)".
  The model recovered via `help`, so having `help` in the grammar paid for itself on its first outing.
- `append="\n4. ..."`: the model escaped a newline and the value kept a literal backslash-n; it noticed on
  re-read and cleaned up. Values should unescape `\n`, and append should be documented as "adds a line".
- Used `pivot` and `verbs` unprompted this time; both answered the two questions the task turns on
  (where else does this appear, what can I do to it).

### r1-agenda-structured: 15 calls, 2 refusals, 41 s, pass
- Same two stumbles as the other variant, which makes them design faults rather than model noise:
  the `args` wrapper leaked into `open` again, and `append` was tried as a verb again. Both runs wanted
  `append` to be a verb. Give them one: `append`, `retitle`, `rewrite` as verbs beats `edit` with three keys.
- Here the `!!` header did land on the next `look`, and the model went straight to `read` and preserved
  Sam's line. Finished with `pivot a18` to prove the agenda appears once. Same shape as the REPL run:
  the notation, not the tool packaging, is what shaped the behaviour.

### r1-tidy-outline: 17 calls, 0 refusals, 44 s, pass, but by hand
- Two looks, then fourteen `move to=` / `resize to=` calls with hand-computed coordinates, then one look
  to verify. Correct, no overlaps, images left. It never used `tile` or `group`, although the level-3 look
  printed `tile as=column|row (lay children out without overlap)` right under the surface it was arranging.
- This is the "don't recode existing behaviours" failure in miniature: the higher-level verb was visible and
  the model still did the arithmetic, because coordinates made the arithmetic feel cheap. The reply even says
  "the layout tools were clear". Fourteen calls where three would do (`group` x2 + `tile`, or `tile as=row` + two reorders).
- Round-2 question: if the read side stops printing coordinates (relations variant) does the model reach
  for `tile`? And should free placement be a verb at all on a desk that has tiling?

### r1-tidy-structured: 19 calls, 0 refusals, 24 s, pass, by hand again
- Identical strategy, and it fired all fourteen mutations in one parallel burst (they all landed at 20.86 s).
  Seen-fencing allowed it because everything had been seen at its current rev. A burst of coordinate writes
  against a desk nobody else is touching is fine; the interesting case is a burst that races an outside edit,
  and seen-fencing would catch exactly the affected targets.

### Round 1 summary

| run | calls | refusals | s | result |
|---|---|---|---|---|
| harbor outline | 40 | 0 | 104 | core pass, strict fail (over-collected) |
| harbor structured | 33 | 4 | 60 | pass |
| agenda outline | 15 | 1 | 43 | pass, trap survived |
| agenda structured | 15 | 2 | 41 | pass, trap survived |
| tidy outline | 17 | 0 | 44 | pass, by coordinates |
| tidy structured | 19 | 0 | 24 | pass, by coordinates |

- No task failed because of the notation. Every refusal was a grammar stumble the model recovered from in one call.
- REPL beat structured on syntax errors (1 vs 6) and lost nothing on capability. One text tool with `help` is enough.
- The read strategy is always: outline every surface, read every subject, then act. Fine at 12 subjects; the
  `big` task will tell whether folding and `find` take over when that stops being affordable.
- Verification idioms the model invented on its own: `find X` after gathering ("no hits remain elsewhere"),
  `pivot` after removing a duplicate ("appears once"), `look` after every mutation. These should be cheap and
  they are: one line each.
- Seen-fencing never refused anything in six runs. Either the model's look-before-act habit makes it redundant,
  or the desk is too small for it to bite. It also cost nothing: no revision numbers anywhere in the notation.
- The delta header worked once it appeared; now it is on every reply.
- The higher-level verbs (`tile`, `group`) were visible and unused. Both models did coordinate arithmetic instead.

Fixes applied before round 2: header on every reply; `append`/`retitle`/`rewrite` as verbs; verb errors name
the target's verbs; `\n` unescaped in values; surface focus prints verb names only; `before=`/`after=` win
over `into=`; new `tree` variant (relations rendering plus no `to=`/`by=`/`resize` on free surfaces).

## Round 2 (live Terra): hide coordinates, remove them, edit the outline, big desk

Runs: tidy x {relations, tree, apply}, big x {outline, apply}, harbor x apply.

### r2-tidy-relations: 34 calls, 0 refusals, 68 s, pass, by coordinates again
- Hiding coordinates changed nothing about the strategy and doubled its cost. The model called `where` on all
  seven items (one burst), recovered the exact rectangles, and hand-placed them with `move to=` / `resize to=`
  as before, this time with a `look` after each pair. 34 calls against 17.
- `verbs f04` was called and answered with `tile as=column|row (lay children out without overlap)`. Still unused.
- Conclusion: information hiding does not steer a capable model toward a higher-level verb; it just adds a
  retrieval step. If we want tiling to be the natural path, coordinates have to stop being a write affordance,
  not a read one. That is what the tree variant tests.
- Verification via the notation: "verified no overlap indicators remain" means it read the absence of
  `hidden by` markers as proof. The occlusion vocabulary is doing the work a screenshot would.

### r2-tidy-tree: 47 calls, 0 refusals, 71 s, pass, and finally by structure
- With `to=`/`by=`/`resize` gone from free surfaces, the model built the tree solution: `group` Pictures,
  `group` Text, seven `move into=`, then `tile f04 as=row`. Two columns side by side, which is the layout
  a human would have wanted, and it survives any later resize because it is a tree, not fourteen rectangles.
- It cost 47 calls: seven `where` (which returned no coordinates in this variant, so wasted), seven `verbs`
  (one per item, all identical), and a `look` after every single move. Caution, not confusion. `verbs` should
  say "same as a20" for siblings of a kind, and the receipt's `now:` line already makes the follow-up look redundant.
- The reply flagged "direct position controls were not available" as the missing affordance, and still called
  group-and-tile "worked well". So: removing the verb changed the strategy; hiding the number did not.

### r2-tidy-apply: 18 calls, 0 refusals, 22 s, pass, by coordinates in one burst
- Never used `plan`/`apply` here, correctly: the outline cannot express free placement and the surface was free.
  Fourteen writes in one parallel burst at 19.39 s, one look to verify. Apply is a reparent/reorder tool; the
  big and harbor runs are where it can show up.

### r2-big-outline: 28 calls, 0 refusals, 88 s, pass on a 37-node desk
- The budget warning did what folding alone did not: call 2 was `find Harbor`, and it never read a subject
  it did not need. Six hits, five subjects, one `also x1` marker, and it went straight to `group f01` for the
  new column. Found the duplicate through the marker, looked at it, removed the right one.
- Reordering still cost three `move before/after` calls plus a look each. Same shape as round 1.
- It moved the new column to 0,0 with `move f68 to=0,0`, on top of the Inbox column. "On the left" was
  satisfied literally; my assessor did not check that it now hides Inbox. Add an occlusion check to `big`.
- Reply named `also x1` as "helpful, though its duplicate semantics were initially a little unclear".
  A better line marker might be `also in f05` (where the other copy is), which is what `pivot` says.

### r2-big-apply: 27 calls, 0 refusals, 85 s, pass, apply never used
- Call for call the same run as big-outline: find, group, five `move into=`, three reorders, remove the
  duplicate, `move f68 to=0,0`. `plan`/`apply` were described in the tool text and never tried, in two runs.
  An affordance that only exists in a tool description is not discovered; it needs `help apply` with an example
  in the grammar, or the desk should offer it ("7 items; to reorder several at once, apply an edited outline").
- Second run to call insertion order "unclear". A `move into=` lands at the end, and the `now:` line does not
  say so. Receipts for tiled parents should say `now 5th of 5 in f68`; that removes the follow-up look too.

### r2-harbor-apply: 46 calls, 0 refusals, 84 s, strict fail (over-collected), apply never used
- Same judgment call as r1-harbor-outline: agenda, chat and dock photo went into Harbor. Two of three harbor
  runs did this, so the prompt is genuinely ambiguous to this model; "everything about" reads as thematic.
- Exploratory idioms appeared that I had not seen: `history a21` on three images (is this thing new?),
  `pivot Harbor` by title, and seven `find` calls in one burst (tide, sensor, kickoff, pier, dock, vendor, demo)
  to sweep for indirect references. `find` by title and `pivot` by title both worked because `_resolve`
  accepts unique titles. Cheap, and the model used it without being told.
- `plan`/`apply`: 0 uses in 3 runs. Verdict for now: edit-the-outline is a human affordance until the desk
  itself proposes it in a receipt.

### Round 2 summary

| run | calls | refusals | s | result | used the high-level path? |
|---|---|---|---|---|---|
| tidy relations | 34 | 0 | 68 | pass | no: dug out coordinates with `where` |
| tidy tree | 47 | 0 | 71 | pass | yes: group, group, move x7, tile row |
| tidy apply | 18 | 0 | 22 | pass | no: coordinates in one burst |
| big outline | 28 | 0 | 88 | pass | find first, never read everything |
| big apply | 27 | 0 | 85 | pass | same; apply unused |
| harbor apply | 46 | 0 | 84 | strict fail | apply unused; broad `find` sweep |

- Zero refusals in six runs after the round-1 fixes. The grammar is stable.
- Hiding coordinates does nothing; removing coordinate verbs changes the strategy. Affordances are what the
  verbs are, not what the lines print.
- A budget warning plus `find` scales the notation to a 37-node desk with no loss.
- Apply is undiscovered. High-level verbs are only used when they are the *only* path (tree). Round 3 asks
  whether naming them on the object (MOO) is enough to get them used when the low-level path still exists.

## Round 3 design: the desk as a MOO (verbs live on things)

Alex's prompt: more verbs is not necessarily bad; make the desk a LambdaMOO room where the verbs on each object
are discovered and used, verbs can get increasingly complex, and maybe a small adapter sits between what the
model says and what the desk can run.

What I built (moo.py, desk_moo.py):
- **Verbs are properties of kinds, inherited.** thing <- appearance <- text <- note/task/chat; thing <- surface;
  appearance <- image. `examine id` prints the object MOO-style (what it is, where, what it holds, where else it
  appears) then `verbs from task: done due / from text: append retitle rewrite / from appearance: fold reveal
  dedupe / from thing: move resize raise lower remove`. `help <verb>` gives doc, args, one example.
- **Three levels of verb.** Level 1 primitives (move, resize, tile, group, append...). Level 2 task-shaped verbs
  composed from primitives (tidy, sort, reveal, dedupe, done, due, stack). Level 3 verbs that carry a rule
  (split by=kind left=image; gather words=harbor by=due). Composed verbs run as a transaction: any refusal undoes
  the earlier steps; the receipt names the primitive events `[e2..e11, 10 steps]` so undo and history stay honest
  and per-primitive.
- **The adapter.** Synonym table (arrange->tidy, delete->remove, add->append, collect->gather ...), fuzzy match at
  0.75, and refusals that say "did you mean" plus the object's real verbs. Every correction is logged, and the
  receipt tells the model what it was taken to mean: `ok tidy f04 (you said arrange; that is tidy here)`. This is
  the rule-based stand-in for the small model adapter; the log measures how often such an adapter would fire.

Hypotheses for the live runs:
1. With `examine` showing task-shaped verbs by name, the model will use `split` or `tidy` on tidy, `gather` on
   harbor/big, `dedupe` on agenda, and call counts drop by 3-5x versus round 1.
2. The adapter fires at least once per run (models say "add", "delete", "arrange").
3. The risk: a level-3 verb does more than the model checked. `gather words=harbor` also removes duplicates;
   does the model verify the receipt or trust it?

### r3-tidy-moo-1: 22 calls, 0 refusals, 56 s, pass, by coordinates despite reading the docs
- It did discover: `examine f04` (verbs from surface: tile rename group sort tidy split gather stack), then
  `help tile`, `help tidy`, `help resize`, `help move`. Then fourteen coordinate writes.
- Reading the help closely, this was a sound decision: `tidy` and `tile` make one column or row, which does not
  give "pictures left, text right". The verb that does is `split by=kind left=image`, listed in the same examine
  line, and the model never opened it. It chose between the verbs it had read about, not the ones listed.
- So the vocabulary problem is one level up: the list of names is not enough; a name must connect to the task's
  words. `split` does not say "left/right by kind" until you `help` it. Options: (a) examine prints one-line docs
  for level 2+ verbs, not just names; (b) the adapter watches the *task*, not the verb: nothing said "split"
  because nothing in the prompt said split. A small model adapter with the prompt in context would map
  "pictures on the left, text on the right" to `split by=kind left=image` directly. That is the case for the adapter Alex
  described, and it is stronger than the synonym table.
- Adapter log: empty. The model used only exact verb names.

### r3-harbor-moo-1: 16 calls, 0 refusals, 57 s, strict pass, fewest calls of any harbor run
- No `examine`, no `gather`, no reads of subjects at all. `find Harbor` gave five lines with due dates and
  parents; that was enough to plan. Four `move before/after` calls, each receipt saying `(2nd of 3 in f02)`,
  and a closing `find Harbor` to verify nothing is left elsewhere.
- The position note in the receipt removed the "insertion order unclear" complaint: this run never said it.
  It still looked after every move, out of habit rather than need.
- `gather words=harbor by=due` would have been one call. It was never seen because the model never examined
  the column. Half the value of a MOO is that `look` at a room hints at its verbs; my `look` lines do not.
  Idea for round 4: the outline line for a surface ends with its two or three most task-shaped verbs,
  Acme-style (`f02 "Harbor" column · 2 inside · gather sort tidy`), so the vocabulary is visible without a call.

### r3-agenda-moo-1: 16 calls, 0 refusals, 35 s, pass, trap survived
- `examine a18` then `help append` then `read s10` before the first write: the MOO loop as intended.
  `examine a24` then `remove` for the duplicate; it saw `dedupe` in the examine line and chose the primitive.
  `help rewrite` before the rewrite, and the rewrite came after the `!!` header and a fresh read.
- The reply: "The desk's change notice made that conflict clear." That is the delta header earning its place
  in the model's own words. Three of three agenda runs kept Sam's line.
- Pattern across round 3 so far: level-2 verbs are read about but level-1 verbs are used. The model prefers
  the verb whose effect it can predict exactly. `dedupe`'s doc says "remove every other appearance", which
  it could predict, and it still chose `remove a24`, having examined a24 and seen there was only one other.
  That is reasonable: with one duplicate the primitive is just as short. Composed verbs win only when the
  fan-out is large (gather over five items, split over seven).

### r3-big-moo-1: 22 calls, 0 refusals, 74 s, pass including the new hides-nothing check
- The MOO loop in full: `find`, `look`, then `help` on seven verbs (split, append, gather, group, move, tile,
  tidy), `examine f01`, `group`, `examine f68`, then **`do gather f68 words=Harbor by=due`**: one call, eleven
  primitive events, five items moved, one duplicate removed, sorted. The round-2 runs spent 15-20 calls on that.
- Then the overlap problem (the new column sat on top of Inbox) was solved with `tidy f01 as=row`: the whole
  desk became a row of five columns, Harbor first. Bold, legal, and the kind of move only a tree-shaped desk
  allows. Its own verification: `find Harbor` and `look f68`.
- The one unclear moment: `move f68 before=f02` on the free desk changed only stacking order, twice, and the
  reply called it "somewhat unclear". On a free surface before/after should either be refused with the reason
  or the receipt should say "free surface: this only changed stacking; tile f01 to make order mean position".
- Round 3 so far: 4/4 pass, 0 refusals, adapter never fired (exact names every time), and the composed verb
  paid off exactly where the fan-out was large.

### r3-tidy-moo-2: 10 calls, 0 refusals, 38 s, pass, the shortest tidy of the whole lab
- look, look, `examine f04`, `help tidy`, `help tile`, **`help split`**, `do split f04 by=kind left=image`,
  three looks to verify. Reply: "The split-by-kind affordance was clear and handled the layout directly."
- Same prompt, same desk, same examine line as r3-tidy-moo-1. The only difference is one `help split` call.
  Discovery at one call's distance is a coin flip; round 4 tries to make it zero calls away.

### Round 3 summary (MOO: verbs on objects)

| run | calls | refusals | s | result | level-2/3 verb used |
|---|---|---|---|---|---|
| tidy moo 1 | 22 | 0 | 56 | pass | none (read help tidy/tile, hand-placed) |
| harbor moo | 16 | 0 | 57 | strict pass | none (find + 4 moves; never examined) |
| agenda moo | 16 | 0 | 35 | pass | none (examine, help, primitives) |
| big moo | 22 | 0 | 74 | pass | **gather** (11 steps in 1 call), **tidy f01 as=row** |
| tidy moo 2 | 10 | 0 | 38 | pass | **split** |

- 5/5, zero refusals, and the two runs that used a composed verb were the two cheapest solutions of their task
  across all rounds (big: 22 vs 27-28; tidy: 10 vs 17-47).
- `examine` and `help` were used in 4/5 runs. The MOO loop (look, examine, help, do) is natural to the model.
- The adapter never fired: the model used exact names once it had read them. The synonym table solves a
  problem this model does not have. The problem it does have is choosing which `help` to read.
- Composed verbs were chosen when the fan-out was large and the doc matched the task's words. `dedupe` for a
  single duplicate lost to `remove`; `split` won when its help was read; `gather` won once seen.

## Round 4: verbs on the outline line (Acme), plus a usage nudge

The `acme` variant is the MOO desk with two additions:
- **Inline verb hints, relevance-filtered.** A line ends with `try: tidy split` only if the surface is free and
  something is hidden; `try: sort gather` on a tiled surface; `try: reveal` on a hidden appearance; `try: dedupe`
  on one that appears elsewhere. Acme's tag line, but computed from state, so it cannot lie and does not spam.
- **The nudge.** After the third hand placement on one surface, the receipt says once:
  "hint: `split f04 by=kind left=image` or `tidy f04 as=row` arranges everything in one call (help split)".
  After the third before/after reorder in a tiled surface: "hint: `sort f02 by=due`". This is the cheapest
  possible version of the adapter that watches what you are doing rather than what you said.
Hypothesis: split/gather/sort get used in 4 of 5 runs, and call counts land near the round-3 minima.

### r4-tidy-acme-1: 9 calls, 0 refusals, 24 s, pass, straight to split
- `look f04` ended with `try: tidy split`; the model went `examine f04`, `help split` + `help tidy` in one
  burst, then `do split f04 by=kind left=image as=row`. Three looks to verify. No nudge needed.
- The inline hint moved discovery from one call away to zero: the model read about the right verb first,
  not the fourth time. 9 calls versus 10 (moo-2), 22 (moo-1), 17-47 (rounds 1-2).

### r4-tidy-acme-2: 7 calls, 0 refusals, 22 s, pass
- look, look f04, `help split`, `do split f04 by=kind left=image`, three looks. It did not even `examine`:
  the `try: tidy split` tag on the surface line was enough to go straight to the help page.
- Tidy across the lab: 17, 19, 34, 47, 18, 22, 10, 9, 7 calls. The last two are the acme variant. Same model,
  same prompt, same desk; the only thing that changed is where the verb's name was printed.

### r4-harbor-acme-1: 29 calls, 0 refusals, 27 s, strict pass, one mutation
- Call count is high, wall clock is the lowest of any harbor run, because everything before the write was
  parallel: 12 reads in one burst, then 4 examines + 4 helps in one burst (`gather sort reveal move`), then
  **one** `do gather f02 words=harbor by=due` (six primitive steps), then two looks and a `find` to verify.
- The `try: sort gather` tag on the Harbor column line led it to `help gather`. Strict interpretation this
  time: "four Harbor-tagged items". Reads are cheap when batched; the expensive thing was always the writes
  and the look-after-each-write loop, and a composed verb collapses both.
- Mutation counts for harbor across the lab: 11, 4, 4, 7, 4, 1. The MOO desk with inline tags got it to one.

### r4-big-acme-1: 17 calls, 1 refusal, 40 s, fails only hides-nothing
- Fastest big run: find, examine, help group/move, `group`, help sort, five `move into=` in one burst, `remove`
  the duplicate, `sort f68 by=due`, verify with `find`. Everything the task asked for, in 40 seconds.
- The failure: the new column sat at 16,16 on top of Inbox, Projects and Reading, and stayed there. The group
  receipt printed `where: ... covers f02, covers f03, covers f04` and `try: tidy split` on the desk line. Both
  ignored. "On the left of the desk" was satisfied literally by x=16. Of the three big runs with this check
  computed (outline and apply would also have failed it), only the moo run cleared it, by tiling the whole desk.
- First seen-fencing refusal of the lab, and it was correct: `sort f68` came after five moves into f68 had
  changed it since the receipt that showed it empty. The model looked and retried. One call. But it raises a
  design question: should a caller's *own* changes invalidate what it has seen? The receipts described them.
  I lean no: mark the parent seen when the receipt lists it as changed. Cheap to do, and it removes the one
  refusal in 22 runs.
- Occlusion by a newly created surface is the round-4 gap. A `group` on a free surface should place the new
  surface in free space when there is any, or the receipt should say "nowhere free; it covers f02 f03 f04;
  move it or tidy f01". The information was there; it was not loud enough.

### r4-agenda-acme-1: 14 calls, 0 refusals, 38 s, pass
- examine, help append, append, (header), read, help rewrite, rewrite, remove duplicate, verify. The `try: dedupe`
  tag was on the line and it still used `remove` for a single duplicate. Fine: same length, more predictable.

### Round 4 summary

| run | calls | mutations | s | result | composed verb |
|---|---|---|---|---|---|
| tidy acme 1 | 9 | 1 | 24 | pass | split |
| tidy acme 2 | 7 | 1 | 22 | pass | split |
| harbor acme | 29 | 1 | 27 | strict pass | gather |
| big acme | 17 | 8 | 40 | fail: new column covers others | sort |
| agenda acme | 14 | 3 | 38 | pass | none (single duplicate) |

Inline relevance-filtered verb tags moved discovery to zero calls in 4 of 5 runs. The nudge never fired:
nobody hand-placed three times once the tag was on the line.

## What I would carry into Agora (synthesis after 22 live runs)

**The screen is a tree and the outline is the screen.** One line per node, folded by default, with occlusion
and spill as the only free geometry (`67% hidden by a23`, `spills-parent`). The model read absence of those
markers as proof of "no overlap" and said so. Coordinates on request only; nobody missed them for reading.

**One text tool with a small grammar beats a set of JSON tools.** Six syntax refusals for structured tools in
round 1 versus one for the REPL, and the REPL's one was a vocabulary slip, not a shape slip. `help` in the
grammar paid for itself on its first outing. Keep `desk(line)`.

**Affordances are the verbs that exist, not the numbers that print.** Hiding coordinates (relations variant)
changed nothing and cost 2x. Removing `to=`/`by=`/`resize` from free surfaces (tree variant) produced the
group-and-tile solution. If Agora wants tree-shaped layouts, free placement has to be a deliberate escape hatch,
not the default verb on every surface.

**Verbs on objects, with inheritance, and the object tells you its verbs.** The MOO loop (look, examine, help, do)
came naturally: 4 of 5 round-3 runs used examine and help unprompted. Composed verbs (`gather`, `split`, `sort`)
took the cheapest solutions of their tasks from 15-47 calls to 7-10, and mutation counts from 11-14 to 1.
They run as transactions over primitives, so history and undo stay per primitive: `e2..e11 via gather`.

**Discovery has to be zero calls away.** Two identical MOO runs differed only by one `help split` and cost 22 vs
10 calls. Printing the two or three verbs that are *relevant to this node's state* on its outline line
(`try: tidy split` on a free surface with overlap, `try: dedupe` on a duplicate) made the model read the right
help page first, every time. This is Acme's tag line computed from the capability contract: a menu that cannot
lie and does not spam. It is the single highest-leverage change in the lab.

**The adapter Alex described is needed one level up.** The synonym/fuzzy adapter never fired in 10 runs: this
model uses exact names once it has read them. What it needs help with is *which help to read*, and the fix that
worked was static (tags on lines), not a model. Where a small model adapter would still earn its place: mapping
the task's own words ("pictures on the left, text on the right") to `split by=kind left=image` when no tag fits,
and turning three hand placements into a suggestion. The nudge I built for that never triggered once tags existed.

**Seen-fencing works and costs nothing.** No revision numbers anywhere in the notation; 22 runs; one refusal, and
it was correct. The delta header (`!! since your last look: e2 edit s10 by sam`) was named by the model as what
made the concurrent edit clear, in 3 of 3 agenda runs Sam's line survived. Open question: a caller's own changes
should probably not invalidate what it has seen, since the receipt described them.

**Receipts should carry the next look.** `now: a20 ... (2nd of 4 in f02)` removed the "insertion order unclear"
complaint. `created f68 ... where: covers f02, f03, f04` was printed and ignored, so loudness matters too:
when a creation covers things, the receipt should say what to do about it, not just that it happened.

**Edit-the-outline stays a human affordance for now.** 0 uses in 3 runs where it was offered in the tool text.
It might work if a receipt offered it ("7 items to reorder: apply an edited outline"), but composed verbs
(`sort by=due`) covered the same ground with less to explain.

**What failed and why.** Two harbor runs over-collected on a genuinely ambiguous prompt (judgment, not interface).
One big run left the new column covering three surfaces after being told so (loudness). Everything else passed,
and no run failed because the notation could not express the task.

### Next round, if there is one
1. `group` places into free space or its receipt says "covers f02 f03 f04: move it or tidy the desk".
2. Own changes keep things seen; only other actors' events invalidate.
3. Level 2+ verbs print a one-line doc in `examine`, so `help` becomes optional.
4. A task-aware adapter variant: the prompt is given to a tiny rule set (or a small model) that proposes one
   composed verb when the outline tags do not match; measure whether it ever beats the tags.
5. Run the prior lab's hard scenarios (procurement, handoff, impossible) on the acme desk for a cross-lab comparison.

## Rounds 5 to 8: harder task, one round at a time

Alex: run four more rounds, keep optimizing, replace the easiest task with something that would come up in real
Agora use, and let each round's results decide the next. Tidy was the easiest by then (7 calls, 1 write), so it
is replaced by **priya**, a handoff shaped like real desk work:

> Priya asked for something in the Priya chat on the Meeting panel. Set up a panel for her: a new surface called
> Priya on the desk holding her chat, every note or task on the desk that is about what she asked for, and a new
> task for me to deliver it, due 2026-09-19. Nothing in the panel may overlap. Then reply to her in the chat, one
> line, naming the note titles you found. Leave the Harbor column alone.

What makes it hard: the ask is only in the chat text (tide parser); the relevant material is a note hidden under a
photo in Scratch and a new "Parser notes" note under the whiteboard; the desk root has no free space, so the new
panel lands on top of three surfaces and must be moved or the desk tiled; it needs a **new** subject (a task with a
due date), which required a new verb; and after the first change Priya adds "and the sensor quotes too", so the
panel and the reply must both pick up the sensors task. Thirteen checks, including "harbor untouched" and
"nothing lost".

### Round 5: the new task on the acme desk, plus the round-4 fix list
- `create kind=task title= due=` on surfaces (new subject placed there).
- `group` and `create` look for free space first; when there is none the receipt says so and what to do.
- A caller's own changes no longer invalidate what it has seen; only other actors' events do.
- `examine` prints one-line docs under the verb list for level-2+ verbs.
Runs: priya x2, harbor, agenda, big. Round 6 is decided from these.

### r5-priya-acme-1: 33 calls, 1 refusal, 91 s, 12 of 13 checks
- Read the chat first, then `find tide` / `find parser`, read the three hits, five helps in two bursts, then
  `group f01 title=Priya`. Priya's second message landed right after that, and the next `move a27` was refused as
  stale with the `!!` header on the refusal itself. The model re-read the chat, ran `find sensor` / `find quote`,
  and moved the sensors task in as well. The delivery task it created is titled "Deliver tide parser and sensor
  quotes". So the update was fully absorbed into the panel.
- The one miss: the chat reply, "I found Tide data format and Parser notes", answers the original ask only.
  The check wants the sensors mentioned because Priya asked for them in the same chat. Judgment, and a fair one
  to fail: a human would have said "and the sensor quotes are in Order pier sensors".
- The new panel was created on top of three surfaces (no free space on the root); the receipt said so, and the
  reply acknowledged it ("default placement obscures other panels") and did nothing. Second time a model has read
  that note and moved on. My checks did not penalize it here, and they should. Round 6 candidate: covering is not
  a note, it is a state the outline keeps showing until it is fixed, and the task checks it.
- `create` worked first time from `help create`. Own-changes-keep-seen removed the spurious refusal seen in r4-big.

### r5-priya-acme-2: 39 calls, 0 refusals, 86 s, 12 of 13 checks (same miss)
- A different route to the same panel: `group`, then **`gather f30 words="tide parser" by=title`**, which pulled
  the chat, Tide data format and Parser notes in one call because all three mention the tide parser. After the
  `!!` header it re-read the chat and ran `gather f30 words="sensor quotes"`, which brought the sensors task.
  Level-3 verbs used for discovery as much as for moving: "everything that mentions X, here" is one call.
- Same reply miss: "I found Parser notes and Tide data format." Two of two runs answered Priya's first message
  and not her second, while putting the sensors task in the panel. The models treat "naming the note titles" as
  the whole reply spec. The check stays, marked as judgment; the notation did its part (the header fired, the
  panel changed). What might fix it is not notation but the reply verb itself: `reply` on a chat could quote the
  latest unanswered line back, so the model sees what it is answering.
- It did deal with the covering panel this time: `resize f30 to=840x380`, `move f30 to=420,0`. That put it
  exactly over the Meeting panel, whose two remaining things are now hidden. Moving a rectangle onto the only
  other rectangle is what happens when the desk is full and the model will not tile the root.

### Round 5 summary
| run | calls | writes | s | result |
|---|---|---|---|---|
| priya acme 1 | 33 | 6 | 91 | 12/13: reply ignored Priya's second message |
| priya acme 2 | 39 | 8 | 86 | 12/13: same miss |
| harbor acme | 24 | 1 | 29 | pass |
| agenda acme | 15 | 3 | 37 | pass |
| big acme | 17 | 8 | 73 | pass, including hides-nothing (tidied the desk into a row after the group note) |

Both priya runs absorbed the mid-task update into the panel and neither absorbed it into the reply. The header did
its job; the reply verb had no idea what it was answering. Two runs also read the "no free space" note and did not
fix it (one moved the panel onto another panel). Help calls: 5 and 7 per priya run.

### Round 6 design (from round 5)
- **Chat is a kind with state.** `reply` verb on chats: prefixes "Alex:", and its receipt says `answered: <the
  unanswered lines>`. `examine` on a chat prints `awaiting reply: ...`. The line tag `try: reply` appears while
  the last message is someone else's. Hypothesis: the reply now mentions the sensors.
- **Covering is persistent and loud.** A surface that covers sibling surfaces says `covers f02,f03,f04` on every
  outline line, and the covered surfaces say `48% hidden by f30`. `move before/after` on a free surface is refused
  with "tile it first", instead of the note nobody read. New check: `panel_covers_nothing`.
- **Fewer help calls.** `examine` lists verbs with their argument forms, `move(into=<surface> | before=...)`, and
  `help a b c` answers several at once.
Runs: priya x2, big, agenda, harbor.

### Round 7 design (Alex: knives, not avocado slicers)
Alex, mid round 6: make verbs that work on many kinds of object, or on pairs. `split by=kind left=image`,
`gather words=`, `dedupe`, `reveal`, `reply` are each one shape. The general design, to be tested against the
round-6 baseline:

- **Selections as targets.** Any verb that takes an id also takes a selection: `?tide parser` (find), `kind:image`,
  `tag:harbor`, `in:f04`, `hidden`, `also:a18` (other appearances of a18's subject), `due<2026-09-20`, and
  combinations `kind:image in:f04`. `move kind:image in:f04 into=f28` is one call. `remove also:a18` is dedupe.
  `raise hidden in:f04` is reveal. `move ?harbor into=f02` is gather (with `one=1` to keep one appearance per subject).
- **Pair verbs.** `swap a b` (positions), `beside a b` (put a next to b in b's parent), `match a to=b` (same size),
  `group a b c as=column title=X` (a new surface *around* a selection, which is split without the rule DSL).
- **State stays on the thing, verbs stay general.** `examine` on a chat still prints `awaiting reply:`; the verb is
  `append`. The `try:` tag on an unanswered chat says `append`, and its receipt still names what it answered.
- The specialized verbs are removed from the registry in this variant, so the only way to tidy is
  `group kind:image in:f04 as=column` + `group kind:note,task in:f04 ...` + `tile f04 as=row`, or `tile` alone.
  `sort` and `tile` stay: they already are knives.
Measure: success, calls, and whether the model composes selections at all or falls back to per-id calls.

### r6-priya-acme-1: 32 calls, 0 refusals, 13 of 14 checks... no: 12 of 14
- The chat-as-kind changes all fired: `examine a27` showed `awaiting reply:`, the line carried `try: reply`, and the
  `reply` receipt said `answered: Priya: oh, and the sensor quotes too if you have them.` The model read that
  and its reply was still "I found: Tide data format; Parser notes." Three of three runs.
- Reading the prompt again, the model is obeying it: "reply to her in the chat, one line, naming the note titles
  you found". It did exactly that, and it put the sensors task in the panel, retitled the delivery task to include
  the quotes, and rewrote its text. The desk gave every signal a desk can give. This check is now recorded as
  judgment and no longer gates `pass`; keeping it gating would be grading the prompt's literalness, not the notation.
- The other miss is real: the panel still covers the Meeting surface after `move f30 to=620,0`. The line said
  `covers f02,f03,f04` on every look, and the model shuffled the rectangle instead of tiling the root. The big-desk
  runs tile the root readily; here the model seems to treat the small desk's three panels as furniture. Candidate
  for round 8: the top level is tiled by default, the way a tiling window manager treats the screen, and free
  placement lives only inside panels.

### r6-priya-acme-2: 32 calls, 1 refusal, 12 of 14
- Same shape as before, one new wrinkle: `gather f30 words=sensor by=title` also pulled "Harbor kickoff" out of
  the Harbor column (its text says "pier sensor vendor"). The model noticed and moved it back with
  `move a16 into=f02`, which put it at the end of the column: order changed, `harbor_untouched` false. An avocado
  slicer cutting the wrong thing, and the general fix would have been the same move with `at=0` or a `sort`.
  With selections, `?sensor,in:f04` would have scoped it. Good evidence for round 7.
- Reply again named notes only (and this time included "Standup agenda", which the words match dragged in).
- Panel again left covering; after Priya's update the model spent its attention on the content, not the geometry.

### Round 6 summary
| run | calls | refusals | s | result |
|---|---|---|---|---|
| priya acme 1 | 32 | 0 | ~85 | 12/14: reply literal, panel covers Meeting |
| priya acme 2 | 32 | 1 | ~80 | 12/14: gather over-collected the kickoff note (order change in Harbor), panel covers |
| big acme | 15 | 1 | 49 | pass; the before/after refusal sent it straight to `tile f01 as=row` |
| agenda acme | 13 | 1 | 43 | pass (one quoting slip) |
| harbor acme | 37 | 5 | 31 | pass; all five refusals were `examine sNN` on subject ids, now routed to pivot |

- The refusal-with-guidance beat the note: big went from "unclear" to tile-first in one step.
- The reply miss is the prompt's literalness, three of three; moved to a judgment check that no longer gates.
- `gather words=sensor` cutting the wrong note is the best argument for round 7: a selection scoped with
  `in:f04` would not have touched the Harbor column, and a general `move` with `at=0` would have restored order.

### Round 7 (knife desk): r7-priya-knife-1: 35 calls, 4 refusals, ~115 s, 12 of 13 gating checks
- No selection was used. Every move was per id (in parallel bursts, so cheap in time). The tool description
  mentions selections and `help selections`; the model read `help` (the general page) and `verbs`, never the
  selection page. Same lesson as apply: a feature that lives in a description is not discovered.
- It reached for `reply`, which this desk does not have, twice. My refusal said "compose it from general verbs";
  it should have said "use append; examine a27 shows what awaits a reply". It found `append` via `verbs s15`.
- Everything else landed: panel, both notes, the sensors task after the update, the delivery task, the reply.
- The covering panel again, and this time the reply names it: "the surface-placement affordance did not provide a
  non-overlapping free area". Its last act was `resize f30 to=20x800` (refused, too small): trying to squeeze the
  panel into a gap that does not exist. Three rounds, six priya runs, six covering panels. The model will not tile
  the root on this desk. Round 8 candidate is now clear: the top level should be tiled by default.

### r7-priya-knife-2: 30 calls, 0 refusals, 12 of 13 gating checks
- Again no selection. Six helps (create, surface, append, group, move, reply), `examine a27` after `help reply`
  came back empty, then `append` with an "Alex:" prefix of its own. Per-id moves, one at a time this run.
- Both knife priya runs did the task correctly, at the same call cost as the acme runs (30-35), and neither
  touched the feature the round is about. The selection syntax has zero pull on its own: nothing in the outline
  shows a selection, so nothing invites one. The verbs on lines (`try: raise`) name a verb and an id, never a set.
- Same covering panel. Six of six.

### r7-harbor-knife-1: 25 calls, 1 refusal, 47 s, pass, first selection in the wild
- `do move a20,a22 into=f02` then `do sort f02 by=due`: two writes for the whole task. The refusal before it
  was `to=f02` (a slip, and my error message for it, "expected <a>,<b>", is aimed at coordinates, not at the
  slip; it should say "to= takes x,y; you probably meant into=f02"). Selections do get used when the simplest
  form, an id list, is what the model already has in hand from `find`.

### Round 7 summary (knife desk: general verbs, selections, pair verbs)
| run | calls | refusals | s | result | selection used |
|---|---|---|---|---|---|
| priya knife 1 | 35 | 4 | ~115 | 12/13 gating (panel covers) | no |
| priya knife 2 | 30 | 0 | ~90 | 12/13 gating (panel covers) | no |
| harbor knife | 25 | 1 | 47 | pass | `move a20,a22 into=f02` then `sort` |
| agenda knife | 13 | 0 | 41 | pass | no |
| big knife | 26 | 1 | 78 | pass | no (five `move into=` by id) |

- Removing the specialized verbs cost nothing: every task was solved at the same quality and cost as the acme
  desk. The knives are sufficient. `reply` was reached for twice and `append` found within two calls.
- Selections were used once in five runs, and only the id-list form, which is what `find` hands you anyway.
  `?words`, `kind:`, `in:` and `hidden` were described in the tool text and never tried. Same finding as apply
  (round 2) and as tile (round 1): a form that does not appear in the outline is not part of the model's world.
- Six of six priya runs leave the new panel covering other panels. Refusals, notes, persistent `covers` lines,
  `try: tile` on the root: none moved this model to tile the small desk's root, though it tiles the big desk's
  root readily. It reads three named panels as furniture.

### Round 8 design (from round 7)
- **Selections where they are born.** `find harbor` now ends with `as a selection: ?harbor  e.g. do move ?harbor
  into=<surface> one=1`. Surface tags name the selection too: `try: tile  raise hidden,in:f04  group kind:image,in:f04`;
  duplicates say `remove also:a24`.
- **The top level is tiled.** The desk root is a row whose panels keep their proportions (Harbor 400 wide, a
  Right column holding Meeting over Scratch). Free placement survives inside panels. `group f01` lands beside
  the others, never on top. This is the product decision from the very first conversation, tested rather than argued.
- Error messages from the transcripts: `to=f02` says "you meant into=f02"; `reply` says "use append".
Runs: priya x2, harbor, agenda, big, all on `tiled` (knife desk + tiled root).

### Round 8: r8-priya-tiled-1: 29 calls, 0 refusals, first full pass of the priya task
- All thirteen gating checks. The panel was created beside the others, so "covers nothing" is true by
  construction. `do move a27,a30,a20,a22 into=f31`: one call for the whole panel, the id list straight out of
  the find results. Then `create` for the delivery task and `append` for the reply.
- `help split` and `help reply` were both tried (old habits from the tool text of earlier rounds do not exist
  here; the model simply guesses common words), and both refusals now name the general verb to use.
- The reply still names the two notes only (judgment check, not gating). Seven of seven.

### r8-priya-tiled-2: 32 calls, 0 refusals, full pass
- Same four writes: `group`, `move a27,a20,a30,a22 into=f31`, `create`, `append`. Two of two full passes on the
  tiled desk against zero of six on the free desk, with the same model, prompt and content. The difference is
  the top-level layout, which is a world decision, not a notation one.

### r8-harbor-tiled-1: 14 calls, 1 refusal, 42 s, pass, and the first `?words` selection
- `find Harbor` (with the new "as a selection: ?harbor" footer) was followed by exactly the suggested call:
  `do move ?harbor into=f02 one=1`. It was refused: `?harbor` also matched the Harbor column itself, and moving
  f02 into f02 aborted the whole transaction (correctly, with the earlier steps undone). The model fell back to
  `move a20,a22 into=f02 one=1` and `sort f02 by=due`. Three writes, 14 calls, the cheapest harbor run of all.
- Fix for the desk: a selection used with `into=` drops the destination from its own matches, and `?words`
  prefers appearances over surfaces. The hint did its job the moment it was printed where the model looks.

### r8-agenda-tiled-1: 13 calls, 0 refusals, FAIL: Sam's line dropped
- First agenda failure in eight runs. Sequence: `rewrite` the agenda with the new item 4; the next receipt
  carried `!! since your last look: e2 edit s10 by sam`; the model did `read a18`, saw "4. Budget check (Sam)"
  after its own item 4, and then rewrote the whole text again *without* Sam's line, so that "Review" was last.
- Seen-fencing did not refuse because the model had genuinely read the current text; it chose to drop the line.
  Every signal fired; the model traded Sam's line for the letter of "as the last item". Judgment, and the worst kind:
  silently destroying someone else's edit.
- What the desk could still do, and should: a `rewrite` receipt that says what the rewrite removed, with the
  author of each removed line when history knows it: `dropped: "4. Budget check (Sam)" (added by sam, e2)`. That is
  a general receipt (any text, any rewrite), and a diff is the natural evidence for a destructive verb. Implemented
  after this batch; not measured live within the eight rounds.

### r8-big-tiled-1: 20 calls, 1 refusal, 75 s, pass, with composed selections
- `move ?harbor into=f69` was refused (the new Harbor column matched itself; whole transaction undone). The model
  then wrote `move ?harbor,kind:note into=f69` and `move ?harbor,kind:task into=f69`: composing two selection
  terms to exclude the surface, unprompted. Then `sort f69 by=due` and `move f69 before=f02` on the tiled root.
  Its reply: "the selection syntax's dynamic matching was slightly unclear". Fair, and now fixed: word matches
  prefer content over surfaces, and a selection drops its own destination.

### Round 8 summary (tiled knife desk)
| run | calls | writes | s | result | selections |
|---|---|---|---|---|---|
| priya tiled 1 | 29 | 4 | 85 | **pass** (first ever) | id list |
| priya tiled 2 | 32 | 4 | 109 | **pass** | id list |
| harbor tiled | 14 | 2 | 42 | pass | `?harbor` then id list |
| agenda tiled | 13 | 3 | 32 | FAIL: Sam's line dropped by a rewrite | no |
| big tiled | 20 | 6 | 75 | pass | `?harbor,kind:note` / `?harbor,kind:task` |

Post-batch fixes (verified offline, not measured live): selections prefer content and skip their destination;
`rewrite` receipts list every dropped line with its author when history knows it:
`dropped 1 line(s): "4. Budget check (Sam)" (added by sam, e2)`.

## Rounds 5 to 8: what changed and what it means

| round | desk | priya | regressions | note |
|---|---|---|---|---|
| 5 | acme + fixes | 12/13, 12/13 | 3/3 | reply literal; panel covers |
| 6 | + chat state, loud covering, refusals | 12/14, 12/14 | 3/3 | refusal beat the note on big; covering unmoved on the small desk |
| 7 | knives: general verbs + selections | 12/13, 12/13 | 3/3 | same quality with a third of the verbs; selections unused (1/5) |
| 8 | + tiled root, selections on lines | **13/13, 13/13** | 2/3 | covering gone by construction; selections used 3/5; one destructive rewrite |

**Knives were the right call.** Removing `split`, `gather`, `dedupe`, `reveal`, `reply`, `tidy` cost nothing:
every task was solved at the same quality and cost with `move`, `group`, `tile`, `sort`, `remove`, `raise`,
`append`, `create` over ids and selections. The specialized verbs had also been cutting the wrong things
(`gather words=sensor` took the kickoff note out of Harbor). A selection scoped with `in:` cannot.

**Selections need a birthplace.** Described in the tool text: used once in five runs, and only the id-list
form. Printed under `find` results and in the line tags: used in three of five, including composed terms
the desk had never shown (`?harbor,kind:note`). Same law as every round: what is on the line exists;
what is in a description does not.

**The top level should be tiled.** Six priya runs on a free root left the new panel covering three others,
through notes, persistent `covers` lines, `try: tile` tags and refusals. Two runs on a tiled root passed every
check with four writes each. The model treats named panels as furniture it may not rearrange; the desk should
not ask it to. Free placement inside a panel is fine; the screen itself is a tree.

**Judgment failures are the residue.** The reply that names two notes and not the sensors (seven of seven,
obeying "naming the note titles"), and one rewrite that dropped Sam's line to make "Review" last. Every signal
the desk could send was sent. The remaining lever is evidence in receipts: a rewrite now says what it dropped and
who wrote it, so the next such choice is made with the loss in view.

**Cost.** Priya: 33, 39, 32, 32, 35, 30, 29, 32 calls; writes 7, 7, 8, 7, 7, 7, 4, 4. Harbor on the final desk:
14 calls, 2 writes (`move ?harbor into=f02 one=1`, `sort f02 by=due`) against 40 calls and 11 writes in round 1.

## Round 9: batching, and a world that is more than rectangles

Alex: try a live model on batching; more importantly make the simulation realistic. Comments, text, connections
between objects. More rectangles is a start but not the point.

### What the world gained
- **Comments** on any subject: `{id, by, text, resolved, replies}`. Lines say `2 comments, 1 open`; `read` lists
  them with ids and status; `examine` prints the open ones; tags say `resolve c35`. Verbs `comment line=`,
  `resolve id= [line=]`. Comment ids come from the same counter (c35...).
- **Links** between any two things, kinds blocks / refers / answers / part-of. Lines say `2 links`; `read` and
  `examine` list them with direction and the other end's title and appearances. Pair verb `link A B as=`,
  verb `unlink id=`, selection `links:<id>` (what A is linked to). The world starts with two `blocks` links
  into the Dock survey, so "what blocks the survey" is a question the desk can answer.
- **Sectioned docs**: a `doc` whose text has `## ` headings. `read` shows the section outline with word counts
  first (fold-as-budget for text), `read a32 #Timeline` or `#2` one section, `read a32 :3` all. `append section=`
  writes into a section. Checklists (`- [ ]` lines) get `check item=n`.
- **Batching**: several commands per call separated by `;`, run in order, stopping at the first refusal with
  "(stopped; N later command(s) not run)". `$new` is the last created surface, `$item` the last created thing.
  The delta header is computed per command, so an outside change that lands mid-batch is announced on the very
  next command and seen-fencing refuses right there.
- An adapter bug found while testing: with no open comments, `resolve` fuzzy-matched to `remove` at 0.75 and
  deleted an appearance. Real verb names are now never remapped; a verb that exists but does not apply says why.

### The review task
> Priya left questions as comments on the Tide data format note. Answer each one from what is on the desk and
> resolve it. Sam left a comment on the Harbor plan; do what he asks, using the desk's links to find what blocks
> the Dock survey. Then link the Tide data format note to the Parser notes as refers. Do not move anything.

The answers are in the Parser notes (UTC; cadence fixed; the harbor master's station). Sam wants a `## Status`
section at the end naming the two blockers, which only the links reveal. After the first change Priya adds a third
question. Thirteen checks including "nothing moved" (every placement identical) and "other sections intact".

Runs: review x2, priya, harbor, big, all on `nine` (tiled knife desk + batching + the new kinds). The same three
regressions ran without batching in round 8, so the batching effect is the calls/turns delta against those.

### r9-review-nine-1: 15 calls, 0 refusals, 9 of 12 gating checks
- Batching was adopted immediately and sensibly: `look f02; look f28`, `read a20; read a32; examine a34`,
  four `help`s in one call, and a closing `read a20; read a32 :3; examine a20`. Fifteen calls for a task that
  has seven required writes plus discovery; the round-8 priya runs spent 29 to 32 calls on comparable work.
- Everything structural passed: the third comment (which arrived mid-task) was resolved, Sam's Status section was
  written and names both blockers found through the links, the tide note was linked to the parser notes, nothing
  moved, nothing lost.
- The three misses are one miss: every answer to Priya came from the Tide note alone ("the note does not specify a
  timezone"). The facts were in the Parser notes, which the model `examine`d but never `read`. `examine` prints
  `text begins: Tide parser: read the 6-minute CSV rows...` and for a three-line note that teaser reads like the
  whole thing. Fold-as-budget bit back: the fold looked like the content. Fix: examine says how much is folded
  (`30w, 3 lines; read a30 for the rest`) and shows two lines, not one.
- Its own reply names the real difficulty: "distinguishing the desk-supported facts from details not specified".
  It looked for the facts in the wrong place and then reported honestly that they were not there.

### r9-review-nine-2: 8 calls, 0 refusals, 28 s, full pass
- The shortest successful run of the whole lab, on the hardest task. Eight calls: look; two looks; four finds;
  four reads; a read-all plus four helps; then **one call carrying six writes** (two resolves with answers taken
  from the Parser notes, the Status heading, the Status line, Sam's resolve, the link); a verification batch;
  and a final batch that resolved Priya's third comment, which had landed mid-way, and re-verified.
- It read the Parser notes because `find Parser` put a30 in front of it and it batched `read a30` with the other
  reads. Run 1 examined a30 and never read it. The difference between 9/12 and 12/12 was one `read` that
  batching made free.
- "The desk's change notification made that straightforward": the delta header inside a batch worked as designed.
- Batching effect on this task: 15 and 8 calls; the same shape of work took 29 to 35 calls in rounds 5 to 8.

### r9-priya-nine-1: 24 calls (11 of them batches), 1 refusal, full pass
- First use of `group` around a selection: `do group a20,a27,a30 as=column title="Priya"` was refused because
  the three things sit on two surfaces ("say in=<surface>"), and the retry `... in=f01` built the panel and
  filled it in one call. Then `create`, then a batch of three writes after Priya's update (move the sensors task
  in, retitle and rewrite the delivery task), then the reply. Twenty-four calls against 29 and 32 in round 8.
- Reply judgment unchanged (names the two notes only). Eight of eight.

### r9-harbor-nine-1: 10 calls, 0 refusals, 36 s, strict fail (over-collected)
- Ten calls, two writes: `move a20,a22,a27,a21 into=f02` then `sort f02 by=due`. The judgment miss from round 1
  is back: Priya's chat (mentions the tide parser) and the dock photo went into the Harbor column. Four harbor
  runs out of nine have read "everything about the Harbor project" as thematic; the notation is not the variable.
  The reply names it: "relevance beyond titles was unclear". The tag `harbor` is visible in `read` and `pivot`,
  and `tag:harbor` is a selection form; the model used `find` and its own judgment instead.

### r9-big-nine-1: 11 calls, 0 refusals, 31 s, pass
- `group`, then one batch: `move f69 before=f02; move a60,a61,a64,a65,a67 into=f69; remove a66`, then `sort`.
  Three write calls, eleven calls total, against 20 in round 8 and 27-28 in round 2.

### Round 9 summary (batching + comments, links, sections)
| run | calls | commands | writes | s | result |
|---|---|---|---|---|---|
| review 1 | 15 | 27 | 7 | 55 | 9/12: answered from the wrong note (never read Parser notes) |
| review 2 | 8 | 30 | 6 | 28 | **full pass**, the shortest successful run of the lab |
| priya | 24 | 41 | 4 | 85 | full pass (29, 32 in round 8) |
| harbor | 10 | 31 | 2 | 36 | strict fail: over-collected (judgment, 4th time in 9) |
| big | 11 | 20 | 3 | 31 | pass (20 in round 8) |

- **Batching was adopted at once and used well.** Reads grouped by intent (`read a20; read a30; read a32;
  examine a34`), helps grouped, and in review-2 six writes in one call. Calls fell by a third to a half against
  round 8 on the same tasks. The mid-batch delta header and refusal behaved: Priya's third comment landed inside a
  batch and was announced on the next command; the model handled it in its next call.
- **The richer world worked as a world.** Comments were read, answered and resolved by id; links were read off
  `examine` to answer "what blocks the Dock survey"; the sectioned doc was appended to correctly; the third
  comment arriving mid-task was absorbed in both review runs. Nothing moved, nothing lost, in both.
- **One notation lesson:** `examine`'s one-line teaser looked like the whole note. The 9/12 run answered three
  questions from the wrong note because it examined the right one and never read it. Fixed: examine shows two
  lines and says how much is folded (`+1 more line(s), 30w; read a30 for all`).
- **Two things did not change:** the harbor over-collection (judgment; 4 of 9 runs) and the priya reply naming
  only the notes (8 of 8). Both are the model reading the prompt literally, with every desk signal present.

## Round 10: is "what is not on the line does not exist" a law, or a notation defect?

Alex: with better notation (nested detail under a header, small markers like `*`) the association should hold;
explain the failure, reproduce it on Sol, and check whether the text really fails to associate.

### The failure, exactly
The slogan covered three different things:
1. A verb that was listed but not used (`tile`, rounds 1-3): the name was there, its effect was not predictable,
   the arithmetic was. Not a fold problem.
2. A syntax described only in the tool text (`?words`, edit-the-outline): never appeared in any desk output, so
   there was nothing to imitate. Not a fold problem either; a birthplace problem.
3. r9-review-1: `examine a30` printed `text begins: Tide parser: read the 6-minute CSV rows, emit JSON per hour.
   Half done.` for a two-line note whose second line held every answer. Nothing said a second line existed. The
   model answered three questions "from the note" and reported honestly that the note did not say. This one is a
   notation defect: the fold looked like the whole.

### The bullets notation (variant `bullets`)
Detail nests under the thing's line as `*` bullets; the fold is named.
```
a30 note "Parser notes" · 260x140 at 440,200 · 30w
  a note (subject s29) on f03:
    * Tide parser: read the 6-minute CSV rows, emit JSON per hour. Half done.
    * Timestamps are UTC. The 6-minute cadence is fixed by the feed. Feed source: the harbor master's station.
a20 note "Tide data format" ... · 2 comments, 2 open · try: resolve c35 resolve c36
  a note (subject s07) on f04:
    * Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    * c35 priya (open): Which timezone are the timestamps in?
    * c36 priya (open): Is the 6-minute cadence fixed, or can it change?
```
The outline gets one bullet per thing too: `* 1. Yesterday's blockers  (+2 more line(s); examine a18)`, and a
doc's bullet lists its sections. Up to four content lines, then `* … N more line(s) folded; read a30 for all`.
The `nine` variant is kept exactly as it ran in round 9 (one-line teaser) as the control.

### Runs
review on nine × Terra (2 more, making 4), review on nine × Sol (2), review on bullets × Terra (2), review on
bullets × Sol (2); and the round-7 knife desk (selections described in tool text only) on Sol for harbor and big,
to see whether failure 2 is Terra's habit or everyone's.

### r10 results so far
- **review, nine, Terra (3rd Terra run on this desk): 10 calls, full pass.** The round-9 miss did not reproduce;
  Terra is 2 of 3 on the one-line-teaser desk. When it read the Parser notes it passed; when it examined them it
  did not.
- **review, nine, Sol: 28 calls, full pass.** Sol never used `;` batching; it parallelised calls instead (reads in
  a burst of four, helps in a burst of four) and read every relevant thing before acting, including the Parser notes,
  unprompted. One write per turn with a `read` after each, the round-8 Terra habit. Its reply: "the hardest step was
  identifying the blockers through the Dock survey's links", and the mid-task comment "was initially unclear".
  Same outcome as Terra's best run at nearly three times the calls.
- **review, bullets, Terra: 12 calls, 11 of 12.** The notation did what Alex predicted: the model answered all
  three of Priya's questions from the Parser notes *without ever reading them*, straight off the bullets under
  `examine a30`. The miss is mine: the bullet cut the line at 100 characters, so the answer it copied was "the
  harbor master's stat", and the check wants "station". A silently truncated bullet is a fold that does not say it is
  a fold, the same defect one level down. Fix after the batch: content bullets are not cut; a very long line ends in
  an ellipsis and a read hint. Batching used (three writes in one call), Status section written by a full `rewrite`
  of the doc rather than `append`, which kept every section intact.
- **review, bullets, Sol: 28 calls, 1 refusal, full pass.** Same call count as Sol without bullets; Sol reads
  everything anyway, so the notation neither helped nor hurt its outcome. Two of two full passes for Sol on the review
  task.
  Its one refusal is a desk bug: `do link a20 to=a30 as=refers` is the documented single-target form, but the
  knife desk's pair-verb path caught `link` first and demanded two positionals. Fix after the batch: a pair verb
  accepts `to=` for B.
- **big, knife (round-7 desk: selections only in the tool text), Sol: 21 calls, 1 refusal, pass.** Sol typed
  `do move ?harbor into=f68` at its eighth call with no hint anywhere in desk output. Terra never did that in five
  round-7 runs. So failure 2 in the list above ("a syntax described only in the tool text is not used") is
  Terra's habit, not a law. The stronger claim survives only in a weaker form: putting the form on the line makes
  it used by every model tested; leaving it in the description makes it used by some.
- **harbor, knife, Sol:** first attempt died at call 16 on "selected model is at capacity" after Sol had read all
  twelve subjects one call each; retried as r10-harbor-knife-sol-2.

### Round 10 summary
| config | calls | result | what it tells |
|---|---|---|---|
| review · nine · Terra | 10 | pass | round-9 miss not reproduced; Terra 2 of 3 on this desk |
| review · nine · Sol | 28 | pass | Sol reads everything relevant; no `;` batching, parallel bursts instead |
| review · bullets · Terra | 12 | 11/12 | answered from the bullets without a read; the miss was my 100-char cut |
| review · bullets · Sol | 28 | pass | no change for Sol; one refusal from a desk bug (`link A to=B`), fixed |
| big · knife · Sol | 21 | pass | used a `?words` selection from the description alone |
| harbor · knife · Sol | 16 (cut) | capacity error | retried |

Fixes after the batch: bullets no longer cut a content line silently (240 chars, then an ellipsis and a read hint);
pair verbs accept `A to=B`.

### The corrected law
"What is not on the line does not exist" was three things. (1) A listed verb whose effect is not predictable loses to
arithmetic that is: true for Terra, untested on Sol. (2) A syntax that appears only in the tool description: Terra
does not try it, Sol does. (3) A fold that reads as the whole: a notation defect, and Alex's nested-bullet form
fixes it: Terra answered all three questions straight from the bullets. The safe rule for the desk is not a law
about models but a discipline: every fold says it is a fold, every affordance has a printed example, and detail
nests under its header with a marker.
- **harbor, knife, Sol (retry): 28 calls, strict fail.** After reading all twelve subjects one call each, one
  write: `move a18,a19,a20,a21,a22,a24,a25,a27 into=f02`, then `sort`. Eight things into the Harbor column: the
  four tagged items plus the agenda, the whiteboard, the dock photo, the sketch and the chat. The same over-collection
  Terra shows in 4 of 9 harbor runs, at its widest. An id-list selection was used (failure 2 again not reproduced on
  Sol); the judgment is the model's, and Sol's is broader than Terra's.

## Round 11: the lean desk (round 9 + round 10 bullets, on a token diet)
Alex: keep the gains of 9 and 10 but stay light on tokens and tools; then "try your model on terra".

### Variant `lean` (tiled root, batching, comments/links/sections, general verbs + selections)
- Tool description trimmed from 347 to 266 tokens: one printed example each of a `;` batch, a selection and a
  pair verb; the enumerations of selection terms and link kinds live behind `help selections` / `help link`.
- Outline lines: no geometry inside tiled parents, no `try:` tags. Fold counts stay (`2 comments, 2 open`, `4 sections`, `Nw`).
- `examine` is the only place hints appear; it prints the round-10 bullets (up to four content lines uncut,
  comments, links) and one `verbs:` line instead of one line per origin.
- Batches: at most 4 read/examine commands per call; the rest are named as not run, with a pointer to `find`.
- `find` keeps its "as a selection" footer.

### Runs (Terra, one per task)
| run | calls | cmds | writes | s | schema | cum ctx (est) | result |
|---|---|---|---|---|---|---|---|
| harbor | 10 | 25 | 2 | 35 | 266 | 13.6k | **pass** (strict; first on a batching desk; read 11 things in batches of 4, moved only a20,a22) |
| big | 12 | 27 | 9 | 43 | 266 | 22.8k | pass |
| priya | 26 | 50 | 11 | 80 | 266 | 59.1k | pass (six `help` calls for verbs that do not exist: copy, clone, appear, gather, split, stack) |
| agenda | 14 | 22 | 3 | 38 | 266 | 18.6k | pass, Sam's injected line kept (round 8 dropped it) |
| review 1 | 20 | 44 | 11 | 62 | 266 | 55.2k | strict FAIL, content right: answered UTC / fixed / station as three new comments, then resolved Priya's without replies |
| review 2 | 16 | 31 | 7 | 43 | 266 | 40.4k | **pass**, answers taken from the examine bullets without a read |

Against the same tasks: harbor 18k (r8) / 32k (r9) → 13.6k; big 30k / 17k → 23k; priya 54k / 54k → 59k;
review 18k–37k (r9), 26k (r10) → 40k. Calls are level with round 9. So the diet cut the outline but not the run:
the model now verifies with `examine` after each write, and a lean `examine` is 650–800 chars (bullets + `where:`
+ `verbs:`). The cost moved from look lines to examine lines. Four examines in one call cost 2.6k chars.

### review 1: a desk defect, then fixed
`examine a20` printed `try: resolve c35`. The model typed exactly `do resolve c35` and the desk refused: `no such id
'c35'`; the accepted form was `do resolve a20 id=c35 line=...`. A printed affordance that is not a command is the
fold defect's cousin. It then answered as three plain comments and resolved Priya's three without replies. Fixes
(after the run): `do resolve cNN [line=...]` resolves the comment on its subject; the reply-less receipt now says
`(line="..." answers it as it closes)`. A non-gating check `judgment_answers_as_own_comments` records the
answer-as-comment reading. Rerun: pass, every answer as a resolution reply.

### The read cap
Fired zero times as a refusal: Terra sized its batches to four reads on its own after seeing the rule in the
description (harbor: 4, 4, 3 + find). It still read eleven of twelve things on harbor, but did not over-collect.

### What round 11 says
- The lean desk holds every round-9/10 gain (5 of 5 tasks pass; harbor strict for the first time with batching).
- Schema is 81 tokens lighter per turn; outline lines are ~40% shorter; but cumulative context is not lower except
  on harbor and big, because examine carries the weight now. The next diet is examine: `where:` only on request,
  a shorter `verbs:` line, and a short form on re-examine of a thing already shown.
- Every hint must be a runnable command. Checked the others: `try: raise`, `sort`, `tile`, `remove also:aNN`,
  `raise hidden,in:fNN`, `group kind:x,in:fNN` all run as printed; `resolve cNN` was the only one that did not.

### Round 11b: changes from human use of the desk (playground session with Alex; unmeasured on a model)
A local playground (drawn desk + the lean REPL) put a person on the desk for the first time. Defects found by
navigating like a person (open drawers, step back) rather than like the model (aim `look` at known ids):
- `open f04` inside a closed f28 was unreachable by `look`: open now opens the ancestors and says so.
- `open x :3` silently ignored the depth: refused now, pointing at examine.
- `look x :3` on a surface printed children + a verb list from the round-1 world table, which lacks sort/raise/
  lower/pair verbs; `examine x` printed no children. Settled with Alex: look's suffix is containment depth (`:3` = everything under a surface, open or not);
  `look aNN :3` on an appearance is examine; examine on a surface prints its children as lines; examine refuses a
  depth suffix. Verbs are printed only by examine, verbs and help.
- Subject verbs (`pivot`, `verbs sNN`) also came from the round-1 table and printed `place into=<surface>` while
  `help place` said place was not a verb. `place` is now a registered verb on subjects (a new appearance); the
  synonym place→move is gone; pivot's verb line comes from the registry; the knife desk hides the specialized verbs
  in `verbs` as it did in examine. One verb source.
- A created appearance's receipt now carries a `now:` line like every other write.
- `do resolve c35 line=UTC, per the Parser notes` (unquoted) silently kept "UTC," and dropped the rest as stray
  positionals. Refused now: `unexpected words after the target ...; quote values with spaces`.
Observed but left alone: undo of my own change is blocked once another actor has written to the same subject
(conservative, by design); a reply-less resolve cannot be given a reply afterwards; `group <selection>` spanning
surfaces asks for `in=<surface>` and then works.
All of the above is unmeasured on Terra or Sol; the round-11 numbers are for the desk before these changes.
- Alex: "how do I list all the pngs, or everything with a tag inside a panel?" There was no listing view for a
  selection; selections were verb targets only. `find <selection>` now lists matches grouped by surface
  (`find kind:image`, `find tag:harbor,in:f04`, `find hidden`, `find due<date`), with the selection footer.
  Sections inside a doc are not things and cannot be selected into; that is a limit of the model, stated.

## Round 11c: building my own desk from nothing, and the first automation layer (2026-09-17)
Alex: save point, then build your own desk inside the system, find friction, fix what you don't like, try the
scripting layer, use the desk as your home base and keep your notes in it.

Save point: commit 4a87357 in the Agora repo (lab + playground). New harness: `explore.py <session>` (empty tiled
desk, lean REPL, pickled between runs; `--reset`, `--dump`, `--shape`; `!actor verb target k=v` injects another
actor's write). The desk I built is exported as `sessions/home.desk.txt` and FRICTION.md indexes the session.

What happened, in order: creating surfaces needed `group` by accident of wording (added `create kind=surface`);
created things spilled narrow parents and proportional reflow squeezed later arrivals to 37 px (clamp + fair
share); titles turned out to be the practical names and were made to resolve everywhere (examine, selection
terms, place); undo needed an id and undid one step of a sort (bare undo, composed undo, causal undo of rule
consequences, undo keeps the view, command-number grouping so consecutive same-verb commands stay separate);
`due` was hidden as specialized and `tag` did not exist (both general now); script definitions were eaten by the
batch splitter; my own rule made my own view stale.

The automation layer that emerged: `rule when <selection> do <verb>` (state rules, fire once per thing entering
the selection, `now=1` to fire on current matches), `rule on <verb> [by=actor] do <verb>` (event rules), `script
name = cmds` with `$1..` and `run`, `clock YYYY-MM-DD` with `today` in due terms. Rule receipts print as `~` lines
after the command's receipt and are undone with their cause. The chain "Priya appends → tag needs-reply → move to
Today → I reply, untag, move back" ran end to end with an injected actor.

The finding that matters: `export` emits the commands that rebuild the desk by title, and replaying that on an
empty desk reproduced the desk exactly (30-line shape diff empty, zero refusals; again after the last changes).
The text is the desk. All of this is unmeasured on Terra or Sol.

## Round 11d: views, a journal, and Terra on my own desk (2026-09-17)
Continued open-ended building on the home desk. Added: `create kind=view title= query=<selection>` (a live
collection: a surface whose contents are the selection, evaluated at each look; nothing can be moved into it);
`$today` in commands, substituted at run time; a Journal doc with `script log = do append Journal line="$today: $1"`;
`look :3` prints each thing's first line as a bullet (depth means depth); tiled panels declare `cramped, Npx each`
under 80 px and proportional shares that clamp past the space fall back to equal shares; `tile` on an already
tiled surface says so; the fresh-desk refusal says "start with look". Fixes found by use: `$today` substituted at
script definition; run arguments quoted inside quoted values; views offering tile/group/create.

**Terra on the home desk (task `home`, one run):** the desk rebuilt from its own export, Priya's question injected
(the reply rule had already tagged and filed the chat into Today). 7 calls, 0 refusals, 22 s, 6 of 7 checks.
Terra: `look`, two finds, read the chat and examine the task, `rules` unprompted, four helps, then one batched call
with all three writes; the tag rule filed its note into Friction. Its own friction note: finding the chat took
several lookups (find Priya had four hits), and "where a rule will file a new item felt a little awkward". The
miss: its reply had no `Alex:` prefix, so the chat still counts Priya's question as unanswered. Fix next: append on
a chat signs unsigned lines. Description grew by one sentence naming rules, views, scripts and the clock (est. +45
tokens); it read `rules` on its own, so the sentence earned its place.
**Home trial 2** (after: find ranks title matches first; append on a chat signs unsigned lines): full pass, 8 calls,
0 refusals, 24 s. Terra signed its own reply this time, found the chat as the first hit, read `rules` unprompted
again, and put all three writes in one call. Its Model's view note: "the chat's reply/signing behavior and
rule-driven filing were initially unclear". Added `why <id>`: the events that put a thing where it is, by whom, via
which rule and because of what, plus which rule would act on it next.

## Round 11e: text at a glance, and time (2026-09-17)
From the reflection on living in the desk: it held my state better than it showed it back, and it had no time.
- `look X :4` prints each thing's text under its line, up to eight lines uncut to 240, fold declared. Depth 1 line,
  2 children, 3 first lines, 4 text. My Friction panel reads as a page.
- Time without timestamps: the clock stamps events with its day; a thing's age is derived from its last stamped
  event. `age<N` / `age>N` are selection terms (untouched-since-the-clock counts as older than any N); examine
  prints a `when:` line. `script morning = clock $1; look Overdue; look Today; find age<1` is how a day starts, and
  because the clock tick fires the due rules, the ritual is also the scheduler.
- Archive as a rule: `rule when in:Done,age>3 do move into=Archive`.
