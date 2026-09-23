# Foundations R7: durable subjects, open facets, installed behavior

23 September 2026. Exploratory research only. This is neither a final object specification nor implementation evidence. Scope: long-lived extensibility and native applications, keeping the system/visual/object working contexts distinct from shell/application/object composition responsibilities. Running arbitrary scripts is not the organizing requirement.

## First-pass position

A durable subject with an open set of named components remains a better starting hypothesis than the shared-desk toy's fixed kind plus props. The important qualification is that a facet is not merely another unstructured property bucket. It is an independently identifiable aspect whose format, interpretation and supported operations can evolve without changing the subject's identity.

My current weak preference is durable open records plus explicitly installed behavior, rather than making the authoritative world an entire live programming-language heap. This is a new recommendation under Alex's narrower UI/application scope. The earlier research synthesis kept several foundations competing and did not select it. Historical examples support particular separations, not a claim that this architecture is novel or universally best.

## Reading coverage and current local boundary

Read the checkout AGENTS, Start Here, Constitution and Design Commitments; Objects and Facets sections 1-14 and its everyday appendix in several passes; relevant runtime discovery/schema/package sections; the implementation-status overview and Agora4 integration account. The initial large combined read was truncated, so key object-reference sections were subsequently read separately. The full Agora Spec was requested in the initial combined pass but was truncated; I do not claim a full new reading of it. No source execution, runtime inspection, browser interaction or live model trial was performed.

Objects and Facets is explicitly a candidate design ledger. Its valuable durable ideas include stable identity, identities for distinct occurrences, schema-version versus edit-revision separation, admitted unknown-data preservation, bounded generic inspection, and different lifetimes for subjects, installed tools and activities. Its complete merge taxonomy, overlay machinery, reconciler model and kind-free dispatch are explicitly revisable mechanisms.

Runtime Guide currently documents object-level revisions, register replacement, bounded application schemas, generic JSON projection and validation of existing instances when a schema changes. It separately identifies editable source revision, immutable build receipt and installation revision. Therefore the reference's immutable v1/v2 facet definitions must not be described as an already implemented general versioning protocol. Editing's independent source review found that direct schema.define can replace a global definition when extant bodies still validate; per-instance immutable definition references are absent in that path. This paragraph distinguishes my documentation verification from Editing's code verification.

The actual branch reported research/shared-visual-desk. I did not switch branches or change Git configuration. Only this authorized research note was written.

## Three historical comparisons

### Self: behavioral reuse and explicit reflection

Primary sources: [Language Reference](https://handbook.selflanguage.org/2024.1/langref.html), [Mirrors](https://handbook.selflanguage.org/2024.1/mirrors.html), [Programming Style](https://handbook.selflanguage.org/2024.1/progguid.html). Coverage: objects, slots, mutable parents and message lookup in the language chapter; complete short mirror section; complete programming-style chapter. These are the project's maintained handbook, not a claim to have newly read every original Self paper.

Self makes objects from slots and optional code, supports delegation through parent slots, and reports ambiguous message lookup rather than selecting arbitrarily. Mirrors expose structural inspection separately. Its style guide warns that clients inspecting representation become harder to reuse and evolve. The guide also describes a concrete failure: finding a printString method on a shared traits object does not mean the object has the instance state needed to execute it. An isComplete annotation is used by the printing facility.

**My inference for Agora:** an agent-friendly object protocol should combine reliable generic inspection with semantic domain verbs. Do not infer a usable operation from the mere presence of a named field or definition. Directly editable definitions are valuable; making ordinary clients depend on every implementation slot is a different and costly choice. A running component's identity is also not automatically the durable identity of the user's subject.

### Newton: open persistent records, with concrete lifecycle failures

Primary source: Mike Engber, Apple Computer PIE Technical Support, [Soup's On](https://web.mit.edu/unna/mirrors/staff.dstc.edu.au/david-arnold/newton/dev/Articles/SoupsOn.pdf), November 1993. Coverage: all seven PDF pages as extracted text, including examples. Figures were not separately inspected. The 942-page Newton Programmer's Guide was located/opened, but not substantively read and is not evidence for these conclusions.

Soup entries can have different slots; indexed fields still require agreed value types. RAM frames cache persistent entries, with explicit writes back. Adding entries deep-copies their data but omits prototype links. Entry IDs are soup-local, not union-soup-global. Extensions to another application's entries are advised to use one appSymbol-named slot. The article records missing change notifications in a built-in app and a cleanup ambiguity: RemoveScript handles both card removal and software removal, making data deletion there unsafe.

**My inference for Agora:** retain extensible records and namespaced contributions, but separate durable identity from storage locality and executable linkage. World updates should drive view invalidation through the accepted-write mechanism, not through voluntary application refresh conventions. Unavailable storage, inactive application, uninstalled application and disposed user data must remain distinct. This historical source exposes actual integration problems, not merely an elegant record format.

### BeOS: typed metadata, native bytes and a separate handler registry

Primary sources: Be, Inc., The Be Book for Release 5, [BNode](https://asleson.org/public/mirrors/www.be.com/documentation/be_book/The%20Storage%20Kit/Node.html) and [BMimeType](https://asleson.org/public/mirrors/www.be.com/documentation/be_book/The%20Storage%20Kit/MimeType.html), preserved mirror of vendor documentation. Coverage: BNode conceptual sections and attribute/identity/locking APIs; BMimeType conceptual sections, attribute descriptions, preferred/supporting apps, app hints, installation and monitoring. This was documentation reading, not execution on BeOS or verification of modern Haiku behavior.

BNode separates a node's bytes and arbitrary named attributes from its directory entry. Attribute type codes are stored, but reads do not enforce matching types. BMimeType separately describes typical attributes, identifies supporting applications and records preferred handlers. Its executable path is explicitly only a hint that may be stale or wrong.

**My inference for Agora:** one common object layer need not replace every native content format. Rich metadata and installed handlers can provide coherent discovery. But a typed-looking stored value or handler association does not prove compatibility, current availability or successful execution. The metadata/native-content option also owes an explicit account of which representation owns each writable fact.

## Distinctions worth keeping before choosing machinery

| Concern | Question | Candidate expression, not fixed syntax |
|---|---|---|
| Subject identity | Which enduring thing is this? | Stable ID and honest reference resolution |
| Facet identity | Which aspect/contract is being asserted? | Namespaced contract identity, possibly multiple keyed instances |
| Schema | How is this particular payload represented and bounded? | Retained immutable definition/version or equivalent exact format reference |
| Semantic interface | Which operations and postconditions are supported? | Versioned operation contracts with declared applicable formats |
| Storage | Where are bytes retained and who owns changes? | Inline record, blob, file or external resource with explicit availability |
| Behavior | Which implementation can perform the operation now? | Installed handler/build binding and current invocation admission |
| Profile | What familiar combination does this object satisfy? | Named facet combination and defaults; several profiles may apply |
| Activity | Which execution/view instance is presently working? | Separate session identity and lifecycle |

A JSON shape is not semantic type identity: {value:number} could denote time, distance or a progress fraction. Conversely, a semantic operation may survive a change of storage format through an explicitly supported adapter. A schema version, interface version and application release therefore need not advance together.

The kernel need not own a final list of meaningful object kinds. It does need a stable way to retain and resolve identities, delimit contributed data, identify the interpretation actually in use, admit conditional native changes and inspect unsupported material. Generic inspection should survive loss of an application. Specialized high-quality interfaces remain installed application work, not something automatically solved by schema forms.

## Competing object models worth retaining

1. **Durable open records with installed handlers.** Subjects retain facets; applications contribute schemas, semantic operations and views. Benefits: data can outlive applications, quiet inspection, independent contributions and explicit evolution. Costs: cross-facet invariants and migrations need ownership; nominal contracts can proliferate; generic CRUD is not sufficient for semantic edits. This is my current weak preference.
2. **Live prototype/delegation graph.** Objects include reusable behavior and editable parent relationships. Benefits: unusually direct exploration, reuse and interface authorship. Costs: changing shared parents can affect many subjects; persistent graphs need deliberate treatment of runtime handles and code generations; package replacement becomes graph evolution. This stays interesting if direct running-tool authorship proves substantially better, but scripts are not currently Alex's priority.
3. **Native formats plus a rich metadata and capability layer.** Objects identify files/resources while facets describe selected interoperable facts and available handlers. Benefits: mature application/storage formats remain usable and exports can be practical. Costs: metadata may become stale, cross-application edits may require adapters, and two writers can create competing truths. This is a serious alternative, not a temporary embarrassment to hide behind universal facets.

These are alternatives in what becomes authoritative and how behavior binds, not three sets of attractive vocabulary to union indiscriminately. A bounded mixture may be justified per domain; it should name the actual extra coordination cost.

## Long-lived extension pressure case

A note carries retained text, tags and an application-specific review facet. A second application adds a citation aspect. A saved view selects unresolved reviews automatically; two appearances show the same subject.

Now uninstall the review app, edit the text in the other app, install a newer review app, and later try its old release. Useful questions arise without demanding a universal solution now:

- Which review facts remain valid after the text edit, and which explicitly depend on the old revision?
- Can generic inspection explain the old review facet without running old code?
- Does the new release read v1 directly, project a translated view, or offer a recorded migration?
- Can the old release safely edit v2, only read it, or neither?
- Which views lose an available handler, and which simply continue through compatible installed behavior?

The point is to retain the same note while changing its capabilities and interpretations. Requiring the agent to rewrite each appearance after these ordinary content edits would contradict the stable reactive-adapter direction.

## Peer critique and open disagreements

Editing agrees that nominal contract identity cannot be replaced by structural shape. It is examining unknown-field preservation and interface evolution, and supplied the current schema.define distinction above. My challenge to Editing: unknown facets should not freeze every operation on an object. They should affect operations whose interpretation or invariants depend on them, with a discoverable owner for that dependency. How cheaply that can be made reliable is unresolved.

Media sharpened my initial retention minimum: payload plus schema descriptor is insufficient when meaning depends on assets, anchored content revisions or external resources. Preserve or disclose that dependency closure; opaque preservation cannot be advertised as successful rendering. Media also reports that current uninstall already retains subjects/schemas/view records while disabling installation and closing/revoking live leases. I have not independently rerun that source path. Its COM comparison usefully attaches a stable interface set to a runtime generation, not permanently to an evolving durable subject.

My remaining uncertainty is how much semantic contract belongs with a facet definition versus the installed operation package. Putting everything in schemas recreates an application language inside the validator. Putting everything in applications leaves generic inspection unable to explain dependencies or compatibility. A small retained descriptor plus explicit operation contracts is promising, but not yet a demonstrated sweet spot.

System/visual/object remain working contexts over the same subjects. Shell/application/object remain composition responsibilities. Facets should help carry identity and relationships across both axes; they should not force separate per-application studios or three storage authorities. Nothing in this research authorizes computer-control expansion.

No new model, runtime change, installation, live-world action or external post was made. This note records a coherent first pass and unresolved choices, not an adoption decision.

## Coordinator pressure: informal use, kind labels and converging vocabularies

The coordinator challenged two possible overcorrections. I agree that neither is desirable.

First, a universal ban on behavior depending on kind labels is too strong. A label can legitimately select defaults, a view or preferred application. The important boundary is that classification alone does not establish supported input semantics, satisfy invariants or grant authority. A package can choose useful defaults from a kind while its operation validates the actual contract it requires.

Second, not every informal observation needs a complete published schema. Allow lightweight namespaced metadata, tags and notes; promote recurring useful structure into a shared facet definition when interoperability warrants it. Such informal material needs honest interpretation, not a claim that every arbitrary key is a supported native capability. The reference's vernacular-facet section already preserves this nursery idea.

Three independent due-date facets expose a weakness in my nominal-contract proposal: namespacing avoids collisions but does not solve fragmented meaning or discovery. Keep these alternatives explicit:

- **Shared domain contract:** authors agree on one due-date vocabulary and retain private extensions. Integration cost is concentrated in governance and vocabulary evolution. A premature common type can erase meaningful distinctions.
- **Declared projections to a common working view:** each author explains how its dates appear in a common deadline query or inspector. This can reduce pairwise mappings from an N-squared family to roughly one mapping per source for that chosen task. It does not establish universal semantic equivalence, lossless round trips or safe generic writes. Several tasks may need several common views.
- **Task-specific correspondences:** preserve distinct vocabularies and relate only those required by a real combined operation. Less premature standardization; repeated integrations can become expensive and hard to discover.

A civil date, local deadline and absolute instant should not silently become one scalar. Time zones, precision, recurrence and unknown time can matter. A mapping should state its direction, supported operation and losses; writable mappings should be separately justified. I would not infer transitive equivalence or automatically compose write adapters merely because A maps to B and B maps to C.

My current inclination is shared small domain contracts where experience establishes them, plus declared read projections for broader discovery, while keeping lossy or uncertain results visible. This is a research hypothesis about manageable cost, not proof that translator proliferation has been solved. A useful next design exercise is three independently authored task/calendar/review facets and two combined questions: what is due today, and move this deadline one day. The read question and write operation may need different answers.
