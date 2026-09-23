# Synthesis (Jeff, coordinator)

Living document. Each round adds a dated section. Positions here are mine; the researchers' own notes carry their arguments and their evidence labels.

## Frame, 23 September 2026

The decision: what the substrate is. Four candidates named in README.md. The criteria Alex's documents set, restated as tests:

1. **Second change cheaper than the first.** Use of the desk should make later edits faster and simpler.
2. **Ordinary computing stays comfortable.** A notebook, a date, a comment need no schema, registry or wiring.
3. **Twenty years.** Original app disappears; two communities diverge; one person replaces one feature; a conventional app joins.
4. **One person can hold it in their head.** Ingalls' test, read literally.

What we already know from primary sources (read by me, 23 Sep):

- Embark bound formulas to concrete mentions on purpose, for predictability, and paid for it: changing a bullet's date means fixing every formula below it by hand. Its schema was implicit (a map view looks for `location`, nothing says so). Side-by-side widgets lost the planning thought; hosting tools inside the outline kept it. The outline itself is ambiguous (route or alternatives).
- The Codex team (round 8) withdrew facet-first. Their obligations list and their range-comment experiment are the strongest existing proposal for how to decide. Their binding shape (stable source, interpretation, transformation, follow-or-capture) answers Embark's failure on paper. Nobody has run it.

What the current text desk contributes as evidence: subjects are string-prop bags with revisions; appearances are occurrences with geometry; lenses bind by selection (`of kind:task`, `over $tags`) not by list position, and carry `key`, `rev` and visibility facts per node; gestures are fenced by observed revision. It has no typed facets, no schema, no per-object behavior. That makes it a cheap test bench for candidate 1 versus 3 and a poor one for candidate 2.

## Questions I will put to the team after round one

- Sable: is "facet" a storage shape or an interface? If an object is a resource with several inspectable representations (Fielding, per Astra), does the facet debate dissolve into a protocol debate?
- Pike: can the Codex binding shape be expressed in the lens grammar today, and what is the smallest word missing? Does `over $tags` already count as follow-mode binding?
- Juniper: run Embark's trip in the desk with dates as props and a lens as the calendar; change a date; does anything need repair? That is the one-day experiment.
- All: where does behavior live in a document-with-protocols world when the plugin's author is gone?

## Round one results

### Sable (foundations), 23 Sep, `sable-1-what-is-the-object.md`

Position: the object is a **referent** (identity minted once, never reused, MOO-style), everything else is an **aspect** named and owned by the **definition** that writes it, each aspect with its own attributed history; behavior lives only in versioned definitions bound by protocol. Candidate 1 with three changes: owned not global names, revision and fencing and adoption per (referent, aspect), no behavior in instances. Would lose to documents-plus-protocols if Juniper's range-comment case needs fewer adapters there; would lose to live objects if a non-programmer repairs per-object overrides more easily; would need Cambria-style translation from day one if owned names still multiply into synonyms.

Evidence executed in the desk, and it hurts: the stale-edit check and the worktree merge fence key on appearance ids, so an edit through a sibling appearance is a lost update (accepted with a warning; merge wrote `beds=6` over a later `beds=7` with no refusal). The fence is also too coarse the other way: a text append refuses an unrelated prop edit, because the subject is one revision unit. Removing a subject's last appearance hides it from views, find and export while links still point at it. Kinds are a closed list, props are unchecked strings, scripts sit outside event history and merge is all or nothing. Sable's reading: the desk chose one granularity for identity, revision and adoption, and it is the wrong one in each place that matters. That is a finding about candidate 1 as much as about the desk.

Caveat Sable states: sources came through a digesting fetch tool; quotes are checkable, not checked.

Coordinator's take: "referent + owned aspects + definitions" is Astra's "small reference/inspection/action boundary" said from the storage side. The two teams now converge on identity-first and behavior-outside; they differ on whether aspects are records or protocols. That is the question for round two.

### Pike (the bridge), 23 Sep, `pike-1-the-bridge.md`

Sources read raw (Boxer, HyperCard guide, Morphic, Embark appendix, Potluck, malleable software), quotes checked. Taxonomy of six binding strategies (identity, name/path, position, query, copied literal, relative) with the failure each produces: stale views from literals and from identity where intent was relative; retargeted drafts from position keys; silent misses from names and queries; wrong-definition gestures from partial fences. Embark's exact sentence: formula arguments "don't update automatically ... they need to update the corresponding date in all formulas below it manually."

Executed against the lens compiler, thirteen bindings under change. What holds: query bindings (`of tag:day`) follow retitles and field edits with no lens edit; `$due` inside a repeat is the relative binding Embark lacked and fixes Embark's date case when the anchor is a query. What fails: a single id is not a selection (`of a04` matches nothing, silently); subject ids cannot be selected at all, so the stable identity is unreachable from a lens; a literal `due<2026-10-03` reproduces Embark's stale view with nothing marking it stale; sections and tags are keyed by position; the same thing twice gives identical keys; only the outermost lens revision is fenced; self-edits are exempt from the fence, so one person with two windows is unprotected; renaming an embedded lens breaks the host and the fallback does not engage; duplicate lens titles shadow silently.

Position: bind concretely and keep the derivation (resolved identity plus provenance, so staleness is a comparison, not a heuristic); bind to the referent, key by occurrence; every binding prints its state (live, captured, empty, unresolved, ambiguous); new code only for a new gesture, a new painting primitive or a new interpretation, never for a new data shape.

Coordinator's take: Pike's "identity plus provenance" is the Codex binding shape with a name for the missing part. The desk work owed by me: `of s03` and `of a04` as bindings with printed resolution state, occurrence keys, closure fencing (patch26 from the earlier session), self-fence in the gesture path.

### Juniper (pressure), 23 Sep, `juniper-1-pressure.md`

Executed Embark's trip in the desk two ways. Records (notes with date props, a query view, a calendar lens): adding an item needed no repair; moving the trip a week cost 4 edits and 3 repairs including 7 date literals in the lens, and before repair the lens showed empty days with no warning and a gesture carried the stale Sunday. The fence would have accepted the click: it protects against stale reads, not stale meaning. A relative variant (`tripday=1`) cost 0 repairs but cannot show a date, since a lens cannot read another thing's prop and nothing says start plus N. Document (one doc with a section per day): the move was one rewrite, 0 repairs, reasoning kept beside results; but items have no identity, cannot be clicked, found, commented on, and `append` put a Saturday item under Sunday.

Case (b) counted per candidate: the deciding variable is whether edits are recorded as operations over elements with stable identity. Where they are (a text CRDT), anchor providers are free; facet records match only by making the text aspect a CRDT document. Cases (c) and (d) do not discriminate; they set conditions: observed state kept apart from authoritative state, and names with owners.

Position: (a) and (b) point at one missing primitive, identified parts inside larger things with edits as operations so views follow instead of copy. The desk splits it badly: records have identity but no containment, documents containment but no identity inside. Proposed experiment: the same ten-step trip across worktrees R, D and H (reasoning in a doc, items linked part-of, calendar as a lens), five measures.

### Round one, read together

Three seats, one primitive. Sable names it from storage (referent, owned aspect, definition), Pike from the view (identity plus provenance, keyed by occurrence, state printed), Juniper from cost (parts with identity, edits as operations). The live disagreement is where the anchor lives: Juniper says a text CRDT makes anchors free and that decides editing for documents; Sable's aspects need to answer that or concede editing. Pike's question to both, where rename and replacement become events, is the same question as "record or protocol".

Round two assignments (sent 23 Sep): Sable writes the five-noun kernel and verifies the free-anchor claim against Peritext; Pike specifies the binding words for the lens (name one thing, read a prop, follow a relationship, capture versus follow, all with printed state) and verifies the CRDT claim independently; Juniper writes the fixed script and runs R and D, then H once the new words land.

Desk work I owe them, from the three friction lists: `$prop` readable in a lens with absence printed; `of <id>` and `of s03` with resolution state; printed empty instead of silent `0 of`; occurrence keys for sections, tags and repeated ids; the self-exempt gesture fence; refuse duplicate lens titles; `create` with props; `do prop` on a selection; stop the CLI at the first refusal so `$item` cannot land on the wrong thing. Done today: worktree merge fence and live stale check see through sibling appearances; nested lens closure fenced and per-lens fallback (patch from the earlier session, applied and tested).

### Desk changes made for round two (23 Sep, commit 26ac31f)

Landed and verified in a scratch session: prop reads in a lens with `read` and `(no x)` printed; `of a04,s05,a99` with states (gone, unplaced) and no gesture on a gone thing; `(empty)` on empty repeats; keys by heading, tag value and occurrence (`#2`); duplicate lens titles refused unless only one is placed; `create` with props; `do <verb> <selection with =>`; a refused line stops the CLI batch; the gesture fence judges the painted revision whoever moved it; nested closure fenced with per-lens fallback; merge fence and live stale check see through sibling appearances.

Not yet, and now the open list for the compiler: a lens reading another thing's prop (follow), start plus N as a named interpretation, sort or group in a repeat, per-column variation, kinds beyond the fixed list, rule-made tags that retract, scripts inside event history, partial merge, `history` versus `why` disagreeing, export of unplaced subjects with dangling links. Pike's round-two spec decides the first two; the rest are desk work I will take as the experiments need them.

Cross-team: the Codex team was told in the bridge session (Talk) what the frontier is and that their round-8 experiment is being run.

## Round two results

### Pike, `pike-2-binding-words.md`

Seven words, each with text output, painter cost, fence and refusals: `of <ids>` with states (landed); `the <selection>` exactly one, else `(empty)` or `(ambiguous: ...)` with gestures off; `as <name>` naming a frame so `$trip.start` reads an outer thing; `$prop` reads (landed); `parts:<id>` and `part-of:<id>` as directed link terms; `derive <name> = <interpretation> <inputs>` from a closed, budgeted list (day-n, days-from, weekday, week-of) that prints inputs and result; `capture` as a visible mode printing `(now X: differs)`. Three fence changes: a gesture carries the revision of every value it read (would have caught Juniper's stale Sunday); painted gestures get no self-exemption (done); ambiguity is a state. Worked trip example: 0 repairs, 0 literals after moving the trip, day columns keyed by n. Named gap: a gesture whose target is another part (drop onto a column) cannot be said. CRDT verdict from raw Peritext and Automerge: anchors are element ids and survive edits elsewhere, but only if the editor emits operations; whole-text rewrite gets a diff's guess; deleted ranges collapse silently; moves mint new ids; blocks out of scope; a grid keeps anchors only by design. Derived values live in the binding, never on the item; capture writes them as a prop with provenance.

### Sable, `sable-2-the-kernel.md`

Five nouns: referent, aspect, definition, anchor, operation. An aspect is a resource in Fielding's sense: owned semantics, a retained representation readable without the owner, the owner's protocol for writes; when the owner is gone, a generic whole-value write is allowed and recorded as such. "Day 2 of the trip" and "11 October" are two resources, not two encodings; the itinerary definition owns `tripday` and a derived `date`; capture is the user choosing the other resource. Rename by the same owner is followed through a declared alias; replacement by another owner is offered, never followed. Occurrence key is (view, binding path in the definition, source); occurrences are not referents until promoted. Concedes the inside of text to CRDT documents after reading Peritext raw; the price is that every writer must emit operations, JEFF included, since whole-text rewrites break anchors. Drift probe executed with two blind model actors: 1 exact name match, 3 near-synonym pairs, 1 false friend, two real disagreements hidden under different names; merge refused all 24 writes for 2 conflicts, then a hand replay silently overwrote. Owned names stop overwrites but not duplication; translation arrives within a session, not years.

### Coordinator's reading of round two

The two seats now agree on: identity first; behavior outside instances; bindings that name a referent and keep their derivation; operations as the unit edits are recorded in; text as a CRDT sequence whose ids are the anchors; fences per aspect. They disagree on one thing worth settling: where a derived value lives. Pike says in the binding, always, captured into a prop only by explicit act. Sable says in the binding for one consumer and in a definition-owned derived aspect once two consumers need it. Round three pairs them on that. Sable's testable claim (does diff-based whole-text update keep anchors near splice quality) is the one experiment in reach that changes a requirement on JEFF; assigned.

### Desk changes made for round three (23 Sep, second commit)

Pike's words W2, W3, W4, W5, W6, W7 and fence F1 are implemented in scene.py, knife.py and deskd.py and verified: Pike's worked trip example run for real moved a week with zero repairs, day columns keyed by n, dates following, the captured value announcing that it differs. F2 (no self-exemption for painted gestures) landed earlier today. F3 (ambiguity is a state) holds for `the` and for duplicate lens titles. Still open: a gesture whose target is another part (Pike round three), per-(subject, prop) fencing (waiting on Sable's kernel word), `reads <prop>`.

What this says about the decision: the missing primitive the three named on day one (identified parts, relationships that follow, derivations that print their sources) was expressible in the lens grammar in one afternoon without arithmetic or code, which is evidence that the bridge can be a small fixed host over a world that has identity and operations. It is not evidence about which substrate supplies that identity; Juniper's H run and Sable's anchor experiment are.

### Juniper, `juniper-2-the-trip-run.md` (the discriminating run)

The fixed ten-step trip script, run to step eleven in four worktrees of one seed. Counts (writes / repairs / wrong outputs / wrong target): records 43 / 13 / 19 all silent / 1; document 17 / 1 / 2 / 2; hybrid with the old words 27 / 0 / 0 / 1 but only by never stating a derived date; hybrid with Pike's words 29 / 0 / 0 / 1 with every printed date derived and printing its inputs. Every one of the records variant's repairs and misses traced to a copied date literal, and every miss was silent. Moving the trip in H2 is one command for both calendar columns and all six itinerary rows.

Two windows under one actor name lost an edit in every variant; under two names it was refused. The fence is per actor, the CLI has no window. Capture printed a false provenance on rows (`read trip start=<captured>`). A derive could not read the current thing's own prop without naming the repeat. All three fixed the same day (window flag, `(captured)` mark and fence exclusion, derive reads own props).

Range comments with a grid editor: with stable row and column ids from the start the anchor work falls to about two functions under every candidate; the representation decision (does the editor mint part identity) settles the anchor cost, not the substrate. Documents win (a) for text only; owned aspects win (c), the policy change, because it is an explicit owned revision with coexistence; live objects have the cheapest first change and the least visible second.

Coordinator's take: this is the first executed evidence in the lab that discriminates. Identity plus a followed relationship plus printed derivation beats both copies-with-queries and pure containment, on the one case Embark reported failing. What it does not yet test: generality beyond trips, the twenty-year cases, and text anchors (the desk has none).

## Round three results

### Pike, `pike-3-gestures-across-parts.md`

The cross-part gesture: `carry` on a part whose frame is a world thing (a capability, no command) and `on drop <part> do <command>` on the receiver, with `$carried` filled by the painter and the receiver's own frames filled at compile time. Moving Kirk Creek to Sunday sends `do prop a34 tripday=2`, where 2 is the receiver's derived day number: no arithmetic, no literal, and "next day" is where you put it. Meaning belongs to the receiver, so the same card dropped in a someday bin means a tag; a drag-with-target would grow a case per destination on the source, an `if` by another name. Painter cost about 21 lines, net about 16 after sharing pointer code with drag, with keyboard pick-up and drop and cancel; text prints each receiver's drop line and the carrying state as a per-viewer observation. Read-set fence contract: every gesture node carries `reads` as (subject, rev, props); deskd checks touched fields from a fixed verb table, subject rev alone until then; captured values are not fenced but are appended to the receipt (`used captured start=...`), because refusing would override the person's choice and hiding would repeat Embark. `reads <prop>` lists who depends on a name and how. Accepted as design; painter work deferred until a run exercises gestures.

### Sable, `sable-3-anchors-in-practice.md` (executed, Automerge 3.5.0, `experiments/anchors/`)

Five comment anchors (cursor pairs, Peritext-style non-growing), ten compounding revisions, six writers, fifty anchor checks each. Splice operations: 37 intact, 13 collapsed visibly, 0 silent. Whole-text `updateText`: 42 intact, 0 collapsed, 8 silently wrong (a moved list item's comment covered the wrong lines). Paragraph or sentence replacement: nearly everything lost. Quoted sentence hunks with a character diff inside, refused when the sentence changed since the declared read: 42 intact, 8 collapsed visibly, 0 silent. A hand-written rewrite changing 30 percent of words kept every anchor on its text under the diffing writers. Concurrency: a person deleting a clause while an agent rewrites the sentence, merged, gave "a hot drinkinci a morning" under character diff and silently undid the person's deletion under sentence replacement; the quoted-hunk writer refused that one sentence and applied the rest.

Verdict: Sable's round-two requirement ("every writer emits operations") is withdrawn. The requirement on JEFF is: say what you read, and express moves as moves. The gateway diffs by sentence against the declared revision, refuses and reports sentences changed since, and character-diffs inside the rest. That is refuse-stale applied to text, costing one tokenizer and one diff at the gateway instead of an editor binding per writer. Moves are the named hard case under every writer. Limits: one document, Sable's own oracle, a hand-written rewrite.

Name relations: `same-as` (optionally via a named interpretation), `narrower`, `distinct`; six declarations would have reconciled the whole drift probe. Anyone may declare; it applies by default only when both owners endorse (claim is not grant).

### The joint rule on derived values (Pike a65, Sable a77, Pike a83; in pike-3 section 5)

Never a stored copy. One place of derivation: a view binding while one view uses it; moved by a definition revision into the definition that owns the inputs' semantics once anything outside that view must name it (another view, a rule, a comment, a history query); stored only by explicit capture with its source; presentation labels stay per view. Two deciding tests: a calendar and a reminder rule derive the same date and one interpretation changes; a comment on day 2's date must show the new value and say it changed.

### Where the frontier stands after three rounds (coordinator)

Agreed by the three seats, with executed evidence behind the first four: identity is minted once and never reused; aspects are owned resources with a retained representation and the owner's protocol; behavior lives in versioned definitions; bindings name referents, keep their derivation, print their state, and are fenced on what they read; the text aspect is a CRDT sequence whose element ids are the anchors, and the write path is declare-what-you-read at the gateway; derived values follow the joint rule. The bridge can be a small fixed host: every word the trip needed was added without arithmetic or code, and the painter budget is not yet spent. Open: generality of the closed interpretation list (Juniper, running), operations and partial merge at (subject, prop) granularity (Sable, round four), definition lifecycle with continuity of ongoing work (Pike, round four), the twenty-year cases executed (Juniper, round four), authority.

## Round four results

### Sable, `sable-4-operations-and-merge.md`

Three specifications against the desk. (1) The operation record: one command is a batch of operations keyed by (referent, aspect) with before, after, what the writer had read, the causal parent, actor and observer (actor plus window); the fence refuses only on the same aspect since the observer's read; worktree merge takes operations, applies the clean ones, counts the agreed ones, holds conflicts with both values and offers take, keep or set; undo is the inverse, fenced on the aspect's current value. The drift probe becomes 59 clean and 2 held where the desk today refuses all 24 of the second actor's writes. (2) The text gateway: `rewrite` carries the revision read; the gateway diffs by sentence, refuses only the hunks whose surrounding sentences changed, applies a character diff inside the rest, records moves as moves (`move-text`), carries comment anchors as character ranges through every splice; the receipt counts applied and refused sentences and shows both texts; five rules for a model writer. (3) Name relations: `do relate a same-as|narrower|distinct b [via=<interpretation>]`, anyone declares, applies when both owners endorse, with what table, find and the fence do for each; six declarations cover the probe, two of round three's labels corrected.

Kernel after four rounds, Sable's own strike list: the derived mode (handled by the signed binding rule), the capture notation (Pike's word), and the requirement that an owner be a definition (whoever mints a name owns it). Survives: referent, aspect, anchor, operation, with an owner on each name. Sable's observation: the noun added last, operation, did the most work; all three specs are the operation record plus a fence keyed by (referent, aspect).

Cheapest test Sable asked for: key the stale check on (subject, prop) and rerun the lost-update, two-window and drift-merge cases. Taken by me now.

### Pike, `pike-4-lifecycle-and-reuse.md`

Executed: fork, preview and merge already work as the lifecycle (a lens edited in a worktree previews there and merge activates it as an ordinary undoable event). What fails: an edit gesture on an unchanged part was refused after a merge changed only the day heading, the same over-refusal the Codex activation store has ("unrelated world changes can invalidate a candidate"). Pike's objection to that store: it is a second history the world cannot see. Design: a per-part definition hash on each gesture (`defpart`), a header that says revision and preview state, a painter that never discards a typed draft (kept on refusal with resend or discard, printed as a per-viewer observation), and a part-level `relens` so diffs and merges are per part. About 11 painter lines. Reuse: `from cal` with part-path override lines, `@rN` pins, `without <path>`; an override keeps the upstream link per part, a fork owns everything; the scene prints where each part came from. `reads <prop>` scans lens texts; `reads <lens>` builds once and lists dependencies. Budget: the painter is still small and fixed (123 lines); the compiler is not (452 to 792 lines today, about 50 per word; 17 words, 4 interpretations). Pike proposes a compiler ceiling of about 25 words and 12 interpretations, past which an expression language is the honest answer.

### Juniper, `juniper-3-three-tasks.md` (executed)

Three ordinary tasks H-style (course schedule, book club, garden rotation). The closed list of four interpretations did not survive: seven new words between them, each task's one change needing one or two repairs, every repair a hand-computed copy the lens could not derive, every miss silent. Verdict: for time structure the list holds if it grows by structural words (`every` recurrence with step, weekdays and skips; `where` on a repeat and `pick` for one row; frame fill inside `only when`; numeric comparison in selections). For quantities it does not: a running sum under a changing rate would need a new domain word per formula, Pike's trigger reached at about four times the predicted rate. Juniper's proposal: keep the closed list for interpretations that carry meaning, admit a small printed arithmetic (each result printed with inputs, no `if`) for quantities, with `running` as the one aggregate. Kernel terms: recurrence is a derived aspect of the term whose instances are occurrences keyed by date, promoted to referents only when named (cancel one Wednesday); a pace that changes from meeting three needs valid time, which the edit log does not record.

### Where round four leaves the decision (coordinator)

Two things are now settled by executed evidence and one is opened. Settled: the fence and the merge belong at (referent, aspect) granularity with the observer as actor plus window (implemented and verified today: different props no longer block each other, the same prop still refuses, merges of different props apply); the bridge's words can carry structure without arithmetic. Opened, by Juniper against Pike's own trigger: quantities will not be carried by named words, so the compiler needs either printed arithmetic under the growth rules or an expression language, and the choice is the next design decision Alex should make with us, not one the lab should make alone. Wren's and Astra's earlier bet (a bounded pure evaluator with declared reads) is back on the table with evidence for it.
