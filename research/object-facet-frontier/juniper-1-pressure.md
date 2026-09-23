# Juniper 1: pressure cases, counted

Round one, pressure. 23 September 2026. Research note, not a decision. Labels: **[ran]** means I executed it in the desk. **[source]** means I read it in the lab's code. **[read]** means a primary source I fetched this round. **[recall]** means I know it but did not re-read it. **[imagined]** means a thought experiment. Counts marked [imagined] are estimates made under the stated assumptions, not measurements.

## Sources read

- **[read]** The docs_2 drafts: Agora, Dynamic Desk and Current Implementation (the Constitution is empty). Astra's round-8 notes: coordinator, editing and media. Sable's round-1 note and Jeff's Sources notes in the desk.
- **[read]** Embark: the raw page, downloaded and reduced to text. Each claim below was checked against the page text, not a digest.
  - The authors say the formulas made by the repeat tool reference a specific date. Changing the date in a parent node therefore leaves the formula unchanged, "possibly causing unexpected staleness" (section on the repeat tool).
  - Their fix is deliberate: concrete arguments you can see, plus autosuggest and copy tools (Appendix I).
  - Views can reach any data in their node's subtree. Map, Calendar, Route and Weather were hardcoded.
  - Schemas were handled "in a primitive way": the map view looks for a `location` property, and nothing describes or enforces that (Limitations).
  - Early prototypes composed GUI widgets side by side. They left no durable trace of the planning, and the authors kept a notes app open beside them. Hosting tools inside the outline fixed this (Findings).
  - The outline is ambiguous: a list of places might be a route or a set of alternatives.
- **[source]** Lab code:
  - The docstring and parser of `scene.py`. `NAMES` (line 48) is the only list of values a lens may print.
  - `moo.py` `v_comment`, which takes `line=` only.
  - The header of `desk-shell/apps/editor.js`. It says rewrite is whole-document and "a comment cannot name the passage it is about".

## Case (a), executed [ran]

Private session `frontier-juniper`, events e1 to e61. I ran the trip two ways.

**Variant R: records.**

1. The trip began as one informal note (e1).
2. Enrichment went into props on that note: start, end, status and alt (e2).
3. The trip got its own column surface (e7, e8).
4. Five items were each made as a note plus props: day, place, when, uncertain.
5. An itinerary view gave a sorted table (e17): `kind=view query=prop:day cols=day,when,title,place,uncertain by=day`.
6. A calendar lens with one column per day used `of prop:day=2026-10-10` (e36 to e39).
7. A rule tagged uncertain items `open` (r1).

What carried it:

- Adding an item (e18, e53) needed no repair of the view. The view is a selection re-run at every look, and that is the desk's best property here.
- `find prop:uncertain` answered "what is still open?" with no setup.
- `table` made drift visible.
- Undo repaired my mistakes cleanly.

**The date change.** I moved the trip a week (e20), and nothing else followed. The repair cost:

- 1 edit to the trip's props.
- 2 bulk edits to the items. These needed explicit id lists, because `do prop prop:day=2026-10-10 ...` was refused with "do needs a target after the verb".
- 1 lens rewrite touching 7 date literals on 6 lines (e60): headings, `of` clauses, a catch-all bucket and a gesture.
- The prose ("Thinking Oct 10-12") and the `alt`/`status` props went stale. Nothing noticed.

Before the lens repair, the lens showed two empty days with no error. It did so only because I had written a "not on a shown day" bucket; without that bucket the items would simply have vanished.

Its "move to Sun" gesture still carried the old Sunday literal. The revision fence would have accepted a click, because neither the item nor the lens had changed. The fence protects against stale reads, not stale meaning.

This is Embark's staleness reproduced exactly, with the lens in the formula's place.

**Relative variant.** I gave the items `tripday=1|2` (e45 to e49), with a lens `of tag:bigsur,prop:tripday=1`. Now a date change was 1 edit and 0 repairs. The price is that no one can show the calendar date: there is no start+N anywhere, and a lens cannot read another thing's prop. The items now carried both `day` and `tripday`. This is Embark's Appendix I tension (concrete against abstract), and the desk offers only the two ends of it.

**Variant D: document.** The same plan went into one `doc` with `## Sat Oct 10` sections and `-` lines. A lens `of sections:a25` showed one column per section (e57, e58).

- The date change was one rewrite and 0 repairs (e59). The note explaining why the trip moved sat in the same text as the result, which is Embark's finding 2, reproduced.
- Items had no identity. They could not be clicked, found, tabled, commented on or flagged. "(? availability)" is prose.
- `append` put "Cambria dinner?", a Saturday item, under Sunday (e61), because it only appends to the end.
- The preamble became a calendar "day".
- Every scene node carried the same item id, `a25`.

**Where the desk stops for (a):**

- A lens cannot name props. `$place` was refused, since only title, text, kind, due and tags are allowed, plus row-source fields.
- A lens cannot sort a repeat or group by a value.
- A lens part cannot vary per column, so the "move to Sun" button also appears on Sunday items.
- `sort` accepts only due, title or kind.
- `link` has no alternative-to, so alternatives lived in a string, `place="Kirk Creek | Cambria"`.
- Rule-made tags never retract. Sam's item still said "open question" after its uncertainty was removed (e32). The derived `only when prop:uncertain` was correct.
- An event rule with a selection target was accepted, then failed when it fired.
- `prop kind=lodging` was silently accepted and is invisible to `kind:` and to `table`.
- Twice a refused line was followed by `$new`/`$item` resolving to the previous thing. My props landed on the trip note, then on a lens note, and that lens then showed up as an itinerary row. Sable hit the same trap.

**Cost of (a) in the desk, counted:**

| | Records | Relative records | Document |
|---|---|---|---|
| User commands to reach an itinerary and calendar | ~20 | ~22 | 2 |
| Date change: edits | 4 | 1 | 1 |
| Date change: repairs (edits to things whose meaning did not change) | 3, plus silent prose/prop staleness | 0 | 0 |
| Silently wrong output before repair | lens empty; gesture writes a stale date; tag says open | none | none |
| Add an item | 2 commands (create cannot take props) | 2 + a rule for the tag | whole rewrite; append goes to the wrong day |
| Per-item comment, query or flag | yes | yes | no |
| Who pays | user | user; the dates are no longer shown | user loses addressability |

Neither variant carries the case. The missing primitive is the same in both: **a part inside a larger thing that has a stable identity, plus a relationship that follows its source instead of copying it.**

## Case (b): range comments across two editors [imagined, grounded in source]

Setup:

- **E1** edits prose, a character sequence.
- **E2** is genuinely different: a grid, where a range is a cell rectangle and the edits are insert or delete row or column, and sort.
- **T1** is range comments. **T2** is a second range tool, "quote this range into a note", which needs an anchor plus a snapshot.

Counts follow Sable's split:

- **anc**: anchor providers that editors must author (selection to anchor, anchor to current range, mapping through edits).
- **shared**: shared tool definitions.
- **deco**: places where an editor must draw marks.
- **H**: host changes.
- **U**: user decisions at a later incompatible policy change, for example comments switching from "follow the text" to "pinned to the revision".

| | anc (T) | shared (T) | deco (T) | H | T2 marginal | U at policy change |
|---|---|---|---|---|---|---|
| A facet records | 2; E2 must first give rows and columns stable ids (a representation repair) | 1 comment record kind + verbs | 2, or 0 with a host slot for range decoration | 2–3: anchor facet admission, op-level edit events or a diff mapper, a decoration slot | 1 definition, 0 anc, 0–2 deco | 1 per workspace; old anchors coexist as the old facet |
| B live objects | 2, plus one notification per mutating method: ~3 in E1, ~6 in E2. The special cases grow with editor verbs | 1 class | 2 (easy to overlay in a Morphic-style system [recall]) | 0–1 | 1 class, 0 anc | hidden. Each local override layers on the new parent; the user may not know overrides exist |
| C documents with protocols | E1: 0, because CRDT cursors and marks map through edits for free [recall: Automerge cursors, Peritext]. E2: 1 small adapter if rows are list elements, 1 full adapter otherwise | 1 plugin; comments stored in-doc or in a sidecar doc | 2, or 0 if the host shell has an annotation slot | 0–1 (cross-document anchor references) | 1 plugin, 0 anc | per document fork: take the branch, all or nothing |
| D current desk [source] | impossible without Python: comments have no anchor, and rewrite is whole-document, so nothing can map | 1 | 2 (editor.js, notes.js); the lens cannot mark a text range | 3–4: anchor on comment, diff mapping in rewrite, a lens/painter word for text ranges, a new verb for T2 | a Python verb every time | n/a |

The deciding variable is not record against object against document. It is **whether edits are recorded as operations over elements with stable identity**:

- Where they are (C for text), anchor providers are free.
- Where they are not, every editor authors the mapping (A), or every mutating method does (B).
- Facet records can match C only by recording op-level edits, and at that point the text facet *is* a CRDT document.

That is where I expect Sable's per-aspect position to lose for editing and keep its value for everything around the text: who wrote the comment, its status, and which community sees it.

## Case (c): a conventional app joins [imagined]

The honest claims are the same under every candidate:

- identity of the installed resource;
- windows, with observed geometry and focus;
- process state as *observed at time t*;
- files handed to it, as identities with before and after hashes;
- clipboard exchange;
- OS verbs: launch, focus, tile, close.

Nothing can be claimed about interior selection, undo, anchors or replay.

Cost is 1 host integration with the window manager for all apps, 0 per app, and 1 per file-format converter if anyone wants the interior (the tool author pays). A pays the risk that observed facets look authoritative. B pays the risk that a proxy's methods pretend. C cannot express a non-document except as a blob plus a launcher, and it needs explicit "unsupported" answers for each protocol.

The desk already has the right precedent:

- **[ran]** `launch` exists only on trials and says "External effect: cannot be undone".
- **[ran]** `help prop` sets `status=queued` on a trial in its own example: external work is modelled as a thing with an observed-status prop.

This case does not discriminate among the candidates. It discriminates on **status discipline**: observed state stays distinct from authoritative state. The user cost is zero only if verb discovery is by applicability, which the desk's `verbs` already does.

## Case (d): two communities diverge [imagined, partly grounded in Sable's run]

Gardeners and runners share a park page. They disagree about what "closed" means: closed to events, or closed to the public.

- **A.** They share the referent and every facet they agree on. The disputed meaning becomes two owned facets. Cost: 1 facet definition (T), 1 default-display choice per community (U, which is governance), and a translation only if someone asks for one (T, 1 per direction).
- **B.** Data can be shared only if both forks' classes accept the same slots. Rehoming instances is N reparent operations. Sable read in the MOO manual that `chparent` drops slots owned by the old ancestors. Divergence therefore risks data loss unless state is separated from behavior, and at that point B has become A.
- **C.** They share the history up to the fork. Later sharing means merging whole documents. A meaning conflict is either last-writer-wins or a conflict with no owner. Cambria-style translation costs 1 lens per schema pair [recall].
- **D, the current desk [ran by Sable].** A whole-world worktree with all-or-nothing replay. Unowned string props collide silently.

What they still share is exactly the set of names whose owner both accept. Only A and Sable's E make that set explicit.

## Position

- **(a) and (b) point at the same missing primitive:** identified parts inside larger things, with edits recorded as operations, so that views and tools can *follow* instead of *copy*.
- **The desk splits the difference badly.** Its records have identity but no containment. Its documents have containment but no identity inside them. Its lens can neither read props nor follow a relationship.
- **(c) and (d) are constraints any winner must meet,** namely observed status and owned names. They are not discriminators among the candidates.

## Proposed experiment (one day, current desk, no source edits)

**Trip × three representations × one fixed script.** Use worktrees of one seed session, one per representation:

- **R**: records, as run above.
- **D**: a document with sections.
- **H**: hybrid. The reasoning lives in a doc; items are notes linked `part-of` to it; the calendar is a lens over items.

Script, identical for each:

1. Seed the informal note.
2. Add 5 items.
3. Build an itinerary and a calendar.
4. Move the trip a week.
5. Add a Saturday item.
6. Mark one item uncertain, then resolve it.
7. Comment on one item.
8. Record an alternative for lodging.
9. Move the trip back.
10. Remove the calendar and check that the reasoning survives.

**Measure:**

- user commands;
- repairs (edits to things whose meaning did not change);
- silently wrong outputs (a view printing something false without saying so);
- wrong-target incidents;
- prose contradicting props at the end.

**Predictions:**

- R: cheap on steps 6 and 7, expensive on steps 4 and 9.
- D: the reverse, and it fails step 7.
- H: pays both unless the lens can follow `part-of`.

If H pays both, the next move is a research branch that adds one word, a follow-by-reference binding, and reruns the same script. Optionally, a smaller model runs each script from a plain-language brief without source access, counting refusals.

Sable's drift probe (two actors, one month, near-synonym count) fits beside this as a second-day run.

## What would change my mind

- If H carries steps 4, 7 and 9 with zero repairs using existing words, the desk's records plus links are closer to sufficient than I claim.
- If an Automerge grid needs a full anchor adapter anyway, C's advantage for (b) is confined to text.
