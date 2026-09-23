# Juniper 2: the trip, run

Round two, pressure. 23 September 2026. **[ran]** means executed in the desk. **[recall]** means not re-read this round. **[imagined]** means a thought experiment. The procedure is in `juniper-trip-script.md`, written as run. Every count below comes from its measures: M1 writes, M2 repairs, M3 wrong outputs with visibility, M4 wrong-target, M5 stated-date agreement.

## What was run [ran]

**Sessions.** The seed session `frontier-trip` holds one doc, "Big Sur trip" (a03), with informal prose. Three worktrees were forked from it:

- `@R`: records. Items are notes tagged `trip`, carrying `day=` and `tripday=`. There is a table view, a literal calendar lens and a relative calendar lens.
- `@D`: document. `## day` sections with `- item` lines, and a lens over `sections:a03`.
- `@H`: hybrid. Items are notes with `tripday=`, linked `part-of` the trip. The trip carries `start=`. The calendar is bound to the trip by id (`of a03`) and reads `$start`; the itinerary view is `links:a03`.

All three were run to step 11. There was no deskd, so the CLI ran source from disk.

**The build moved during R.**

- Before R step 2, `scene.py` hashed f1dd4b17 and head was f717590. Jeff committed 26ac31f at 14:16.
- From R step 4 on, `scene.py` hashed 9408f314, and the scene began printing `(empty)` after a `0 of`.
- D and H ran entirely on 26ac31f, plus an uncommitted `knife.py`.
- No count changed because of the build. Only the marker text did.

## Results

| | R records | D document | H hybrid |
|---|---|---|---|
| M1 writes, steps 2–10 (plus the shared seed: 1) | 43 (+1 refused) | 17 | 27 |
| M2 repairs | **13** (steps 4 and 9: 6 and 7) | **1** (step 5) | **0** |
| M3 wrong outputs | **19**: 15 silent, 4 silent 0-of | 2: 1 silent, 1 visible | **0** |
| M4 wrong-target | 1 (step 11a) | 2 (step 5 append; step 11a) | 1 (step 11a) |
| M5 places stating the dates / disagreeing | 12 / 0 | 3 / 0 | 2 / 0 |
| n/e (not expressible) | alternatives; the relative lens cannot print a date | itinerary table; "what is open"; comment on an item; alternatives | alternatives; the day 2 date; dates in the itinerary |

**H carries steps 4, 7 and 9 with zero repairs:**

- Step 4: 2 target writes; every check was correct.
- Step 7: the comment sits on the hike itself.
- Step 9: 2 target writes; everything correct.

It does so partly by *not stating* derived dates. Only the day 1 heading prints a date: "Day 1, 2026-10-17 · read start=2026-10-17". Day 2 and the itinerary show day numbers. This is honest (nothing false is printed) but incomplete.

## Per-step transcript summary [ran]

**R, records.**

| Step | Writes | Repairs | Misses before repair (visibility) |
|---|---|---|---|
| 2 | 12, and `do due` refused on a doc | 0 | — |
| 3 | 3 | 0 | — |
| 4 | 2 + 6 | 5 item `day` edits and 1 literal-lens rewrite (4 literals) | Itinerary: 5 stale day cells (silent). Literal lens: 2 stale headings (silent). After the item repairs, before the lens repair: `0 of …prop:day=2026-10-10 (empty)` twice (silent 0-of). Relative lens: 0 |
| 5 | 2 | 0 | 0. The user had to know the current Saturday's date, itself a copy |
| 6 | 2 | 0 | 0. `only when prop:uncertain` appeared and retracted correctly in both lenses |
| 7 | 1 | 0 | 0 |
| 8 | 4 | 0 | 0; n/e: `examine` shows "refers from", not alternatives |
| 9 | 2 + 7 | 6 item edits and 1 lens rewrite | Itinerary: 6 silent. Literal lens: 2 silent heads, then 2 silent 0-of |
| 10 | 2 | 0 | 0. Reasoning intact, itinerary 6 rows |

**D, document.**

| Step | Writes | Repairs | Misses |
|---|---|---|---|
| 2 | 7 appends | 0 | — |
| 3 | 1 | 0 | The preamble became a calendar column headed "(before the first heading)" (visible) |
| 4 | 1 whole-doc rewrite | 0 | 0 |
| 5 | 1 + 1 | 1 rewrite | The append landed "Pfeiffer Beach" under Sunday: silent, and 1 M4 |
| 6 | 2 rewrites | 0 | 0; n/e: `find ?trail` returns the whole doc |
| 7 | 1 | 0 | n/e: the comment attaches to the doc. The lens shows no comments |
| 8 | 1 | 0 | n/e: the alternatives are prose sub-lines, drawn as Saturday lines |
| 9 | 1 | 0 | 0 |
| 10 | 1 | 0 | 0. Reasoning intact |

**H, hybrid.**

| Step | Writes | Repairs | Misses |
|---|---|---|---|
| 2 | 11 (1 trip prop; 5 × create-with-prop + link) | 0 | — |
| 3 | 2 | 0 | — |
| 4 | 2 | 0 | 0 |
| 5 | 2 | 0 | 0 |
| 6 | 2 | 0 | 0. The lens printed "open: trail status · read uncertain=trail status", then `(absent: not prop:uncertain)` |
| 7 | 1 | 0 | 0 |
| 8 | 4 | 0 | n/e: refers, not alternatives |
| 9 | 2 | 0 | 0 |
| 10 | 1 | 0 | 0. Reasoning intact; the itinerary still lists 6 |

## Pike's split: repairs and misses by binding, steps 4 + 9 [ran]

| Binding | Repairs | Misses | Visibility |
|---|---|---|---|
| Literal lens (dates in `of` and headings) | 2 rewrites (8 literals) | 4 stale headings + 4 empty days | silent, and silent 0-of `(empty)` |
| Query view over copied values (R itinerary) | 11 item edits | 11 stale cells | silent |
| Relative lens (`prop:tripday=N`) | 0 | 0 | — (prints no date) |
| Section lens (D, keyed by heading) | 0 | 0 | — |
| Identity binding (H, `of a03` + `links:$item` + `$start`) | 0 | 0 | — (the date is printed with `· read start=`) |

These counts support Pike's position against Embark's predictability claim. Every miss came from a copied literal, and every miss was silent. `(empty)` does not distinguish a stale literal from an honestly empty day.

## Step 11: one person, two windows [ran]

The same run in R, D and H, with identical outcomes:

- **(a) Two windows under one actor name.** A read, B rewrote, then A rewrote from its old read. The write was **accepted**, and B's edit was lost. The only trace is A's own receipt: "dropped 1 line(s): '4.5 mi loop; trail reopened…'". Visible after the fact, to the wrong window.
- **(b) Window B as `juniper-tab2`.** The write was **refused**: "stale: a09 changed since you last saw it (e48 edit by juniper-tab2)".

The fence is per actor name. The CLI has no notion of a window, so one person is not protected from themselves. D pays more for this [imagined]: its unit is the whole doc, so under (b) two windows editing *different* lines would also be refused, and under (a) one would silently overwrite the other.

## What H still needs: the lens lines I wanted [ran as refusal or absence; the output is proposed]

1. **Day 2's date.** I wanted `head : text "Day 2, $start+1d", role heading`. It should print `head a03 "Day 2, 2026-10-11" [heading] · read start=2026-10-10 · start+1d`. Today the only honest line is `text "Day 2"`. Pike's named transform (`day-after`) would do the same job if it prints what it computed.
2. **Group, instead of one part per day.** With one part per day, a third day means a lens edit. I wanted:

   ```
   cal : row, of a03, each trip
   trip : row, of links:$item, group tripday, each day
   day : column, role sheet
     head : text "Day $tripday, $trip.start+($tripday-1)d", role heading
     items : column, of links:$trip.item,prop:tripday=$tripday, each entry
   ```

   It should print one `day` per distinct `tripday`, keyed `day/1` and `day/2` by value, with `· read trip.start=2026-10-10`.

   That needs three missing words: `group`, an outer-context read (`$trip.start`, Embark's cascade), and a day offset. Grouping also hides empty days. A day with no items should still show, so eventually the trip needs a range (start to end), not a group.
3. **Dates in the itinerary.** An item should read its parent's prop through the link: `cols=tripday,title,part-of.start`. That is a cross-thing read, the same word as 2 at the table level.
4. **Scene text prints `of links:$item,…` unfilled.** It should print `of links:a03,prop:tripday=1`, so the agent can see what was queried. This is Pike's friction 6, still open.

With 1 to 3 in place, H's date statements would all be derived, M5a would fall to 1 (the `start` prop plus prose), and the n/e column would lose its date entries.

## Sable's question (a21), with a grid as E2 [imagined; the C column partly recall]

**Setup.**

- E1 edits prose.
- E2 edits a grid. A range is a cell rectangle. The edits are insert or delete row, insert or delete column, sort rows, and move row.
- The tool is range comments.
- **(a)** anchor adapter functions the editors author: selection to anchor, anchor to current range, and one mapping case per edit kind.
- **(b)** shared comment definition: record and verbs, panel, and decoration mount points.
- **(c)** user decisions when the policy changes from "comments follow the text" to "comments pinned to the revision they were made on".

| | (a) E1 prose | (a) E2 grid, index rows | (a) E2 grid, stable row/column ids from the start | (b) shared | (c) at the policy change |
|---|---|---|---|---|---|
| A facet records (owned aspects) | 2, plus 3 map cases, or 0 if the host records op-level text edits | 2 + 6 map cases; a whole-grid write needs a diff heuristic | 2 + 0 map cases + 1 decision (after sort, is a range a span or a set?) | 1 definition (3 verbs + panel) + 2 deco mounts, or 0 with a host slot | **1 explicit decision per workspace**. Old comments keep the old aspect revision and coexist |
| B live objects | 2 + 3 notify hooks | 2 + 6 notify hooks | 2 + 0 (anchors hold row objects directly) + 1 sort decision | 1 class + 2 overlays | **0 decisions, silently**. Instances follow the new class; each local override is a hidden decision the user does not know exists |
| C documents with protocols | **0**: CRDT cursors and marks [recall] | 2 + 6 unless rows are CRDT list elements | 2 + 0 + 1 sort decision. Risk: if sort is delete plus reinsert, cursors do not survive [recall, unverified] | 1 plugin + 2 deco | 1 decision per document (or fork), plus a schema translation Patchwork has not integrated [read in round 1 via Jeff] |
| D current desk | host only | n/a (no grid editor) | n/a | host changes: comment anchor, diff mapping in rewrite, a lens word for ranges | n/a |

**What changes when E2 rows have stable ids from the start.** The mapping column disappears for every candidate at once: 6 cases become 0 and one semantic decision about sort remains. On (a) the three substrates then tie at about 2 functions per editor.

So the representation decision (does the editor mint part identity?) matters more for (a) than the substrate decision. C wins (a) only for text, and only because the CRDT already mints character identity. A wins (c), because the policy change is an explicit, owned revision with coexistence. B has the cheapest first change and the least visible second one.

My answer to Sable's condition is therefore split:

- Documents plus protocol beat per-aspect on (a) for text only.
- Per-aspect beats documents on (c).
- The per-aspect position survives for editing if the text aspect records op-level edits, which means holding a CRDT inside the aspect.

That is the same convergence as round 1: A's text facet becomes C's document.

## What the run says about the substrate

1. **Copies are the cost.** R's 13 repairs and 19 wrong outputs all trace to the date being *copied* into items and lens literals. D and H state it once. Identity plus a relationship (H) beat both a pure query over copies (R) and pure containment (D).
2. **H is where records and documents meet.** The reasoning stays in a document, the parts have identity, membership is a link, and the view binds to the whole by id and reads through it. That is Sable's referent with aspects, and also Embark's outline node with mentions. What H lacks is not storage. It lacks three lens words: an outer-context read, group or range, and a named date transform.
3. **Silence is the bridge's worst defect, even after Jeff's fixes.** Every miss in this run was silent. The one visible thing, D's preamble column, was not a date.

**What would change my mind.**

- If H with the three missing words needs a repair when the trip gains a third day, then relationship-plus-read is not enough and the calendar needs a range generator.
- If Sable's drift probe shows `tripday` and `day` style synonyms multiplying across actors, H's zero-repair result depends on one careful author.

## Friction this round [ran]

- A fresh desk refuses `create` before `look`.
- `due` is refused on a doc.
- A refused line now stops the batch ("stopped: 10 later line(s) not run"). This is a real fix, and it prevented a repeat of round 1's wrong-target props.
- `(empty)` does not distinguish a stale literal from a true empty.
- The scene prints `links:$item` unfilled.
- Same-actor two-window edits are accepted and lose data.
- `append` cannot target a section, and a comment cannot name a line.
- Worktree forks taken after a refused create are empty. I deleted my two empty fork pickles and forked again.
