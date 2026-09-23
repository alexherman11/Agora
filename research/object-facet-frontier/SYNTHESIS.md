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
