# Sable 3: anchors in practice

Round three, foundations. 23 September 2026. Research note, not a decision.

Labels:
- **[ran]**: executed. The script, the document, the oracle and the raw output are in `experiments/anchors/`.
- **[read-raw]**: read directly from source text.
- **[imagined]**: a thought experiment.

In round two I set a requirement on every writer, JEFF included: to keep comment anchors, a writer must emit fine-grained operations rather than hand back whole texts. This round tests that requirement in Automerge.

## 1. The experiment [ran]

**Setup.**
- `@automerge/automerge` 3.5.0, pinned exactly in `package.json` and `package-lock.json`. Node 25.6.1. Run with `node anchors.mjs`, which writes `results.md` and `results.json`.
- The seed is a 363-word planning note: a title, three prose sections, a five-item task list, and a closing section.
- **The five comments:**
  - c1: a word ("Saturday");
  - c2: a phrase ("the drip under the standpipe");
  - c3: a whole sentence;
  - c4: a list item;
  - c5: a range spanning a paragraph break.
- **How each comment is anchored.** A pair of Automerge cursors:
  - one before the first character, resolving forward if that character is deleted;
  - one on the last character, resolving backward;
  - resolved range = [start, last + 1). This is Peritext's non-growing comment.
- As a second representation, each comment is also an Automerge mark with `expand: "none"`. Marks gave the same result as cursors in every cell, so I report cursors only.

**The ten revisions, applied in sequence so that drift compounds:**
1. insert a sentence;
2. delete a clause inside c3;
3. move c4 to the top of the list (delete and insert);
4. retitle a heading;
5. rewrite the paragraph holding c2 and the start of c5, as five phrase edits;
6. replace the commented word itself ("Saturday 18" → "Sunday 19");
7. insert a new section;
8. edit c4 in place and add an item;
9. merge the two paragraphs c5 spans;
10. tidy: "volunteers" → "helpers" throughout, and shorten c3.

**The oracle.** For every anchor after every revision, `doc.mjs` records the text a careful reader would say the comment is still about. For example, after revision 6 that is "Sunday". The script checks that each oracle entry exists and is unique.

**The six writers.** Each receives the same revisions, and every writer's text is asserted identical after every revision:
- **op**: one splice per edit, covering only the changed words. This is what an operation-emitting editor sends.
- **ut**: `Automerge.updateText(newText)`. This is an agent handing back the whole text.
- **wd**: a word-token diff applied as splices.
- **pr**: paragraph replacement. Changed paragraphs are deleted and reinserted.
- **ss**: sentence replacement.
- **qc**: *quoted sentence hunks*. The writer's whole text is diffed by sentence against the revision the writer read. Each changed sentence is applied only if it is still present verbatim in the current text; otherwise it is refused and reported. Inside an accepted sentence, a character diff is applied.

**Classes.**
- **intact**: exactly the oracle span.
- **partial**: overlaps the oracle span with Jaccard ≥ 0.5.
- **drifted**: overlaps less.
- **collapsed**: an empty range while the intended text exists.

**Two further runs:**
- **(c)** an agent-style rewrite of the seed that changes 29.7% of the words and keeps the meaning. I wrote it by hand, not with a model.
- **(e)** concurrency. A person makes revisions 1 and 2 as operations while an agent, from the same seed, writes the rewrite. The two are then merged.

### Results, ten revisions (cursor anchors, 50 anchor-revisions per writer)

| writer | intact | collapsed (visible) | drifted (silent) | where it failed |
|---|---|---|---|---|
| op: splices | 37 | 13 | 0 | c4 collapsed from R3 on (move); c1 collapsed from R6 on (the commented word was retyped) |
| ut: updateText | **42** | 0 | **8** | c4 from R3 on covered " the gate⏎- Clear the drain beside the standpipe", the wrong lines |
| wd: word diff | 31 | 5 | 14 | c4 drift as ut; c2 drifted at R5 to "the drip at the " because word alignment matched the wrong "the"; c1 collapsed at R6 |
| pr: paragraph replace | 11 | 33 | 6 | everything in a touched paragraph |
| ss: sentence replace | 16 | 28 | 6 | everything in a touched sentence |
| **qc: quoted sentences, char diff inside** | **42** | 8 | **0** | only c4 from R3 on (the move), collapsed visibly |

Across op, ut and qc, c2, c3 and c5 stay intact at every revision, including the clause deletion inside c3, the paragraph rewrite through c2 and c5, and the paragraph merge inside c5. The three writers differ only on c4 from the move (R3) onward and on c1 from the retyped word (R6) onward. The full per-anchor, per-revision tables for all six writers are in `results.md`.

### Run (c): one rewrite changing 29.7% of the words

| writer | c1 | c2 | c3 | c4 | c5 |
|---|---|---|---|---|---|
| ut | intact | partial "ter, and the leaking standpipe" | partial "ring gloves, … cold morning." | partial "a new washer on the tap by the gate" | partial "he city, … bed three." |
| wd | intact | intact | partial | partial | partial |
| pr, ss | collapsed | collapsed | collapsed | collapsed | drifted "⏎⏎" |
| qc | same as ut | | | | |

Every anchor stayed on its text under the diffing writers. The ends are ragged: character diffs cut mid-word, and a new first word ("Please", "According") falls outside the range. The writers that replace whole units lose everything.

### Run (e): a person and an agent at the same time

The person deletes a clause from c3's sentence while the agent rewrites that same sentence. Then the two are merged.

- **ut then merge:** "Please bring gloves, a trowel and a hot drink**inci a morning.**"
- **wd then merge:** "…a hot drink**sinceita  morning.**"
- **ss then merge:** coherent text, but it contains the clause the person had just deleted. The person's edit is silently undone.
- **qc applied to the person's current text:** the rewrite of that one sentence is **refused and reported** as "quoted text changed". The person's version stands. All other sentences apply. No text is garbled, and every anchor resolves on its text.

## 2. The verdict on the requirement

**The requirement relaxes, and it moves.**

"Every writer must emit operations" is wrong as stated. On one writer's sequential revisions, Automerge's whole-text `updateText` kept more anchors exactly than editor-style splices did: 42 against 37. The character diff preserves boundary characters. Retyping "Saturday" as "Sunday" keeps the S and "day", so the comment survives, where a person's select-and-type collapses it. A rewrite changing 30% of the words kept every anchor on its text.

Two failures remain, and neither is fixed by operations alone.

1. **Moves.** Every writer loses a moved list item. Splices lose it *visibly* (the comment collapses). A diff loses it *silently*: the comment now covers the wrong lines. A silently wrong comment is worse than an orphaned one. Moves need a real move operation, or a move recorded at the gateway.

2. **Concurrency.** A whole text written from a stale base, then merged, corrupts prose ("drinkinci a morning"). This happens at *any* diff granularity finer than the unit of conflict. At a coarser granularity it instead silently undoes the other person's edit. This is the real cost of whole-text writes, and it is the same stale-read problem the desk's revision fence already solves for props.

**The middle path that passed (qc).** A writer may hand back whole text, provided it declares the revision it read. The gateway then does three things:
- diffs by sentence (or block) against that revision;
- applies each changed sentence only if that sentence is unchanged since then, and refuses and reports the others;
- applies a character diff inside the accepted sentences.

Result: 42/50 intact, 0 silent drifts, no garbling. The only failures are moves, which collapse visibly.

**So the requirement on JEFF becomes: say what you read, and express moves as moves.** It does not become "emit operations." That is refuse-stale applied to text, and it costs one tokenizer and one diff at the gateway, not an editor binding per writer.

**Limits:**
- one document and my own oracle;
- a rewrite written by me, not by a model;
- Automerge 3.5.0 only;
- a naive sentence tokenizer, which abbreviations would break;
- a repeated identical sentence makes a quote ambiguous (qc refuses; it does not guess);
- ragged mid-word boundaries under character diff, fixable by snapping to word boundaries when displaying.

**What would reverse this:** a model's real rewrites of longer documents producing many refused sentences. Refusals then become the new friction, and a finer fence unit (the clause) would be needed.

## 3. The joint rule with Pike on derived values

Pike proposed the text in Talk a65. I signed it with one amendment in a77, and Pike countersigned in a83 with one clarification, which I accept: a gesture's read-set fence entry does not by itself force the move, because the fence names the inputs, and those already have addresses.

> **Rule (Pike and Sable).** A derived value is never a stored copy. A derivation, meaning a named interpretation plus input paths, resolves when read and prints its inputs at their revisions. It is written in exactly one place. While one view uses it, that place is that view's binding. Once anything outside that view must *name* the meaning, the derivation moves, by a definition revision, into the definition that owns the inputs' semantics (for the trip, the itinerary). "Anything outside the view" means another view, a rule, an agent query, a comment on the value, or a history query. Consumers then read it by name (`date (derived by itinerary r4)`). A value becomes stored data only by an explicit capture with its source. Presentation derivations such as a weekday label stay per view.
>
> **Deciding tests:**
> - *Pike's:* a calendar and a reminder rule each derive the date. Change one interpretation. If they silently disagree, the move is required.
> - *Sable's:* comment on day 2's date, then change the interpretation. The comment must show the new value and say that it changed.

## 4. The smallest declared relation between two owners' names

The drift probe needed exactly three kinds of statement, and nothing smaller would do:
- **`same-as`**: interchangeable meaning, optionally `via` one of Pike's closed interpretations when only the format differs. Three pairs: hazard/hazards, steward/manager, and water/water_access only via an interpretation.
- **`narrower`**: every A-claim is also a B-claim, but not the reverse. Two pairs: winter_status against hours, size against capacity.
- **`distinct`**: looks alike, means something else. One pair: access against accessibility. It stops later suggestions from re-proposing the match.

Six such events would have reconciled the whole probe.

**Recording and authority [imagined].**
- Each declaration is an attributed event. It creates a small referent, the relation itself, owned by whoever declared it.
- *Anyone* may declare one, because it is a claim.
- It takes effect for a reader by default only when **both names' owners have endorsed it**. A one-sided or third-party declaration is offered to readers and printed, not applied. This is claim ≠ grant, the same rule as the cross-owner replacement in round two.
- Once in effect, `same-as` does two things:
  - tables and queries union the two names, showing the source of each value;
  - the concurrency fence treats a write to either name as touching both. That would have caught the drift probe's hidden disagreement: "ice around base in freeze" against "drips, shut off in frost" on the same tap.

## What moved since round two

- The operations requirement on writers is withdrawn. It is replaced by "declare what you read" plus a fence for each sentence or block at the gateway. Moves are now the named hard case.
- Fielding's resource reading of aspects is unchanged. What changed is that the text aspect's representation is a CRDT *and* the gateway owns the diffing.
- The derived-value rule is agreed with Pike and countersigned (a83).
