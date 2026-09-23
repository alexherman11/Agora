# Sable 1: what is the object?

Round one, foundations. 23 September 2026. Research note, not a decision. Three kinds of claim are kept apart below: **[ran]** evidence I executed in the desk, **[read]** primary sources I fetched this round, **[recall]** things I know but did not re-read, and **[imagined]** thought experiments.

## What I read, and how

All reading went through a web-fetch tool that returns a model-written digest of the page, not the raw text. So "read" here means "read a faithful-looking digest, with short quotes relayed by it." Treat any quote as checkable, not checked.

- Ingalls, *Design Principles Behind Smalltalk* (1981), whole article digest. [read]
- LambdaMOO Programmer's Manual, sections on objects, properties, verbs, object functions and property functions (tecfa.unige.ch mirror, pages 5, 6, 7, 47, 49). [read]
- Ink & Switch: Embark, Malleable Software (2025), Local-first software, Potluck. Automerge "concepts" reference page. [read]
- Astra's round-8 foundations note (Codex team). [read, in full, raw]
- From memory only: Automerge internals (op ids, change hashes, heads), Cambria's lens graph, Datomic's entity/attribute/value/transaction model, Squeak images, HyperCard stacks, Dynamicland's claims-and-wishes. [recall]

## What the sources actually settle

**Ingalls** gives two principles that pull against each other. Polymorphism: a program should "specify only the behavior of objects, not their representation." And uniform reference: every object gets an identity and can be named the same way. He also admits that protocols are held together only by convention ("only a matter of style"). The lesson is that identity and protocol are what he makes uniform. Representation is left free. That rules against a single global facet schema. It does not rule against facets.

**LambdaMOO** is the most concrete precedent for live objects with behavior, and the manual is candid about how they age. Object numbers are "never reused, even if the object … is recycled." That is identity done right. Behavior and property definitions live on ancestors. A child's property is "clear" by default, meaning it reads through to the parent until the child sets it. `chparent` raises `E_INVARG` on name conflicts. It removes properties defined by the old ancestors, adds the new ones as clear, and leaves the rest "completely unchanged." When an object is recycled, its children are reparented to its parent. My inference from the manual, not something it states: if you delete a generic, its children quietly lose every property and verb that generic defined. Their data lived in slots that the vanished definition owned.

**Embark** stores everything as outline nodes with IDs and inherited properties. Schemas are handled "in a primitive way": the map view looks for a `location` property by convention. Formulas point at concrete nodes and do not rebind when the text changes. The failure the authors name is that GUI composition left no "durable trace" of the planning thought. **Potluck** makes text the only truth, with searches as overlays that rerun on every edit. The authors found that shared searches break other documents, and that tools built by others were hard to understand even at small scale. **Local-first** leaves schema evolution as an open question and relies on ubiquitous formats for longevity. **Malleable Software** names view dispatch, sharing selection and context across embedded tools, and Cambria's "pluralistic schemas" as unsolved or only partly integrated.

## What the desk did when I pushed on it [ran]

I used the private session `frontier-sable` (plus worktrees `@runners` and `@beds`) as actors `sable` and `wren`.

1. **Kinds are a closed list.** `kind=datapoint` and `kind=place` were refused ("must be note, task, chat, image, doc, trial, surface or view"). A datapoint has to be a note with props.
2. **Props are strings, and nothing checks them.** `beds` accepted `4`, then `four`, then `[1,2,3,4]`. `find prop:area_m2>1000` matched nothing, so there is no numeric comparison. `table` puts different names in different columns, so drift is visible but never reconciled.
3. **The appearance/subject split leaks into concurrency.** Wren looked only at `a06`, then set `beds=9` on it after I had set `beds=8` through `a05`, another appearance of the same subject. The desk printed a warning and accepted the write: a lost update. The merge is worse. A worktree command `prop a06 beds=6` replayed over Wren's post-fork `prop a05 beds=7` with no refusal and no `!` in `worktree diff`. The fence in `worktree.py` compares command ids with event targets, and `a06` never maps to subject `s04`. In the other direction the fence is too coarse. A text `append` to `a05` made Wren's unrelated `prop beds` refuse, because the whole subject is one revision unit.
4. **Two histories disagree.** `history a05` omits the edits made through `a06`. `why a05` shows the subject's full story. `history s04` shows only `place` and `link`.
5. **Removing the last appearance hides the object.** After `remove a09` the subject `s08` still existed and the link from `s04` still pointed at it. But the view "Rain chart" dropped the row, `find` could not see it, and `export` omitted it while still exporting `link … "rain 09-01"`, which would fail on replay. Placement is doing the work of existence.
6. **References are local and made of titles.** Ids are counters for each session, and merge renumbers them. Export replays by title and warns when titles collide. No identity survives outside one world.
7. **Behavior is global and has no history.** A per-object verb (`do water a05`) cannot exist. Scripts are global definitions that sit outside the event history. Merging `@runners` silently replaced my `water` script with the fork's version. Merge is all or nothing: I could not take the prop change without the script change.
8. **Small traps.** A refused `create` left `$item` on the previous datum, so my next `prop $item` silently overwrote the wrong row. `undo e12` was refused because a later *link* touched the same thing, so undo is linear for each thing and treats relations as changes to their endpoints. `prop` is labelled an appearance verb but writes the subject.

To be fair to the desk: its subject/appearance distinction, attributed events, `why`, stale-read fences and worktrees are real assets. Most of the failures above are about granularity. The unit of identity, revision and adoption is not the same unit in the places where it needs to be.

## Comparison

A = facet-bearing records. B = live objects (Smalltalk/MOO). C = documents with protocols (Automerge/Patchwork). D = the current desk. E = the candidate I propose below. Cells mix [read], [recall] and [imagined] judgement. The D column is [ran].

| Criterion | A facet records | B live objects | C documents + protocols | D current desk | E referents + owned aspects |
|---|---|---|---|---|---|
| Identity | Record id, global if designed so | Excellent inside one image (MOO: never reused); nothing across images | Document URL is strong; parts inside a document need in-document ids or cursors | Counters for each session; renumbered on merge; title export | Minted once, never reused, carried across forks |
| Revision / history | Can be per facet; systems usually do per record | Image snapshot or checkpoint; little attributed history | Excellent: full causal history for each document | Event list; the fence is keyed per id and misses sibling appearances | Attributed history per (referent, aspect) |
| Where behavior lives | Outside, in apps and verbs over facets | In the object or its ancestors; overridable per object | In tools and plugins; Patchwork stores tool code as documents | Python primitives plus global scripts and rules | In versioned definitions that bind to aspects by protocol; local overrides are themselves definitions |
| Composition | By reference between records | Object graph; containment by convention | Nesting inside a document; embedding across documents | Surfaces contain appearances; a doc cannot contain a view | Referent + aspects; parts get identity only when referenced or given their own lifetime |
| References / links | Ids; typed links | Direct pointers; dangle on recycle | URLs; references to parts are thin | Links belong to subjects; the target becomes invisible when unplaced | Links to referents or anchors; dangling links shown, never dropped |
| Schema drift | Needs a registry or translation | Class changes migrate the instances in place | Cambria-style translation on read, still open | No types; drift silently accepted | The aspect name is owned by its definition; coexistence by default, translation when earned |
| Fork / partial adoption | Facet-level adoption is possible | Copy the object or class; future updates entangled | Fork and merge whole documents; can't split a meaning conflict | Whole-world fork; all-or-nothing replay | Fork per aspect or definition; adopt one definition revision |
| One-person comprehensibility | Risk of many near-synonym facets | High when small; overrides tangle | High for data; tool dispatch is opaque | High reading; props and scripts cheap | Three nouns (referent, aspect, definition), plus history |

## Twenty-year cases [imagined]

**The original app disappears.**
- A: the facet values remain, but their meaning lived in the app.
- B: under MOO semantics, deleting the generic strips the property slots that it defined from the children. The data does not outlive its definer.
- C: the documents stay readable as JSON, though Automerge's binary format needs the library.
- D: the strings are readable, but nothing says what `beds` meant.
- E: the aspect keeps its name, its owner-definition id and the last revision of that definition as data, so a later tool can at least show what the aspect was and who wrote it. Nothing guarantees it still runs.

**Two communities diverge.** Gardeners and runners share the park.
- C and D fork whole units, so partial agreement becomes a merge problem.
- B forks the class, and each fork drags the other's future changes along or loses them.
- A and E let them share the referent and the aspects they agree on while each keeps its own aspects. The disputed boundary can stay as two attributed aspects instead of one overwritten polygon.
- The cost is a registry of which aspects "count" for each community. That is governance, not storage.

**One person replaces a feature.**
- B is best for the first change: override the verb on one object and `pass()` to the parent.
- It is worst for the second: the next parent update silently changes what the override is layered on.
- E treats the override as a new definition revision bound to the same aspect, pinned or following upstream by choice. The data is untouched, and the replaced definition stays inspectable.
- D cannot do this without Python.

## First position

The object should be a **referent**: an identity minted once and never reused (MOO got this right). Everything else hangs off it: **aspects**, each named and owned by the definition that writes it and each with its own attributed revision history; and **definitions**, versioned objects in their own right that carry behavior and bind to aspects by protocol, never embedded in instances. Documents are referents whose main aspect is structured text with anchors. A datapoint earns its own referent only when something outside its container refers to it or it outlives its container; otherwise it is an anchored part of a series aspect. This is close to candidate A. The changes are that facet names are owned, not global; revision, fencing and adoption all happen at (referent, aspect) granularity; and behavior is never stored in the instance. The desk's lost update and its too-coarse refusal are both symptoms of choosing a single granularity wrongly.

**What would change my mind.**
- If Juniper's range-comment case across two editors needs fewer adapters as a document plus a comment protocol than as a comment aspect bound to two editors' anchors, the per-aspect machinery is not earning its keep. C wins for editing.
- If a non-programmer can follow and repair per-object overrides in a live-object prototype more easily than definition rebinding, B's comprehensibility beats E's hygiene.
- If owned aspect names multiply into dozens of near-synonyms within one realistic month of desk use, then the naming problem is not solved by ownership. I would want Cambria-style translation from the start.

## Open for next round

- How is an anchor inside text represented, and does it survive edits? Peritext and Automerge cursors [recall] suggest yes, but that has to be tested.
- Should the desk's fence move to (subject, prop) now, as a cheap experiment that tests E's granularity claim?
