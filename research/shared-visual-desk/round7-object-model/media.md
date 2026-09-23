# Media: application lifetime, facets and installed capabilities

Exploratory first pass, 2026-09-23. Proposal and static inspection only. No implementation, tests, native writes, runtime installation, browser actions or Claude contact. The scope is an extensible object environment with system, visual and object contexts; visual work concerns interface composition rather than a universal artistic-content engine.

## Opinion

Prefer durable typed facets plus separately installed behavioral interfaces. A facet says what retained data means; a capability says which operation a particular installed implementation can perform on it. A visual lens composes the interface for that capability. These can be packaged together without becoming the same identity or lifetime.

This is stronger than both a fixed kind-plus-properties model and an object whose every meaning exists only as a method on its owning application. The former makes new domains depend on platform branches; the latter makes removal of code threaten intelligibility of data. Neither failure requires a universal object calculus to repair.

System context can inspect applications, installations, capability providers and adoption. Object context works on subjects and discovers applicable operations. Visual context inspects occurrences/views and follows their lenses when authoring is intended. These are working contexts over related objects, not three databases. An install does not implicitly open every possible view, and closing a view does not remove headless capabilities.

## What exists in inspected Agora4 source

- packages.py retains source, build receipt and installation separately. install checks package/build/source/base-installation consistency and commits schema additions with the installation. restore deliberately bypasses current-source matching, not installation revision checks.
- application_schema.py admits namespaced bounded JSON schemas. Application accepts/read/write declarations identify facet requirements. Existing schema descriptors must be byte-canonically equal during application install; differing definitions refuse with an explicit-migration diagnostic. This is conservative admission, not semantic compatibility analysis.
- applications.py open binds package/build/installation revision to a subject, records a separate application-view object, and captures a bounded facet/relation grant. It creates defaults only when no subject is supplied.
- refresh allows facet-grant subsets and unchanged declared relation rules, verifies accepted facets, and preserves the lease. It does not prove equivalent action meanings, compatible retained state or editor anchor semantics. Existing views retain their bound build until refreshed.
- uninstall disables the installation, closes its open views and changes their leases in one native commit. Subjects, schemas and stored view records/state survive. Export reads retained source even from a disabled installation. This is a valuable existing lifetime separation.
- application_data.py exposes filtered subject data, one-subject facet transactions and per-view retained state. The browser app cannot infer global management authority from its manifest.
- schemas.py refuses unknown facet writes until a schema is defined. It stores current schemas by facet type and validates replacement payloads; it does not supply the full candidate facet-instance/schema-version system described in the design references.
- check_source currently separates browser-1 applications from python-1 headless actions and explicitly refuses dependencies. There is no general nested-component loader or resolved application dependency closure here.

Runtime Guide was read in full. Its no-general-application-mounting statement is stale relative to applications.py and the newer integration evidence in Implementation Status. The status document also preserves older limits below newer sections; those must not be treated as one consistent current inventory. No installed runtime was inspected.

## The toy comparison

notation/world.py retains subject identity separately from appearances, which is useful. Subjects nevertheless have a fixed envelope: kind/title/text/tags/due/rev/comments/props. create enumerates allowed kinds; some content behavior checks kind directly. moo.py prop coerces values to strings. desk_knife.py offers generic property tables alongside kind-specific descriptions. These are effective experiment conveniences, but props alone provide neither typed extension contracts nor installed application lifecycle. Replacing kind branches with namespaced facets would make data more composable; replacing those branches also requires extensible operation discovery, not merely renaming props.

## Two primary-source lessons

Microsoft's [Rules for Implementing QueryInterface](https://learn.microsoft.com/en-us/windows/win32/com/rules-for-implementing-queryinterface) requires stable object identity, a static interface set for an instance, and navigation among supported interfaces. Its [lifetime explanation](https://learn.microsoft.com/en-us/windows/win32/learnwin32/managing-the-lifetime-of-an-object) describes QueryInterface/AddRef/Release. The useful Agora analogy is a pinned runtime component or interaction generation. It is not the durable subject: requiring that subject's available capabilities to remain fixed would forbid the desired installation and facet growth. Reference-counted process lifetime does not settle user-data retention.

Mike Engber's Apple technical-support article [Soup's On](https://web.mit.edu/unna/mirrors/staff.dstc.edu.au/david-arnold/newton/dev/Articles/SoupsOn.pdf), 1993, pp. 1-2 and 5-6, distinguishes persisted soup entries from cached frames. It describes shared soup notifications and namespacing additional application data. Crucially, RemoveScript ran for both application-card removal and software removal; the article warns against deleting data there and leaves cleanup unresolved. My inference: unavailable provider, uninstalled application and deliberately discarded user data deserve distinct states. Persistence and notification conventions alone do not solve compatibility between writers.

## Survival is more than keeping bytes

The minimum surviving object needs identity, retained payload or honest resource reference, schema identity/descriptor, provenance sufficient to interpret relevant claims, and the references needed to recover its content. A missing executable should leave generic inspection/export and an explicit missing-capability explanation. A preserved external URL is not preserved media bytes, and a saved component declaration is not a loaded implementation.

Editing supplied the discriminating case: Notes 1 rewrites text while an unknown Review 2 facet contains anchors and approval. Preserving that facet verbatim can still misrepresent current applicability. Preserve what was approved, including its content basis; distinguish historical validity from applicability to current text. An edit can invalidate or recompute a current interpretation without deleting the original claim. Unfamiliar metadata should not automatically veto unrelated title edits. Strong coupled invariants require an explicit adopted operation contract, not an arbitrary facet declaring itself indispensable.

## Native and external applications

Use one discoverable capability presentation, with truthful differences behind it. A native handler reads and changes admitted world material through native operations. An external application adapter can expose open/inspect/import/export or its actual provider operations; its status names observed process/provider incarnation and freshness. An opaque window remains a legitimate appearance even when its interior cannot be projected as native facets. Do not create a second purportedly authoritative document from accessibility text merely to make it resemble native data.

The default visual adapter can compose title bars, property panels, collections, controls and missing-provider views for both. The application or installed specialist component owns its internal editing semantics. Adding a reusable interface component can require executable work; ordinary app composition and object organization should reuse installed components through definitions.

## Stable host and open choices

Keep stable: native identity/reference interpretation, bounded inert schema admission, authenticated commit and revocation, retained install/build identity, discovery/invocation transport, resource observation boundaries and independent recovery. Put domain schemas, action implementations, visual definitions and specialist components in extensions. The exact executable ABI, schema evolution policy, dependency resolver and garbage collection rules remain open.

Two viable alternatives remain: direct typed-facet edits with explicit compatibility rules, or selected application-owned aggregate mutations for coupled structures. They can coexist, but a procedural interface must disclose what it reads/writes sufficiently for other editors to reason about compatibility. A raw JSON editor is not automatically safe for every valid schema.

A minimal later proof should install two applications over one document, add an annotation schema/action in the second, edit a title and then text in the first, uninstall the second, inspect/export the retained annotation and its old content basis, reinstall a compatible release, and reopen without silently treating old approval as approval of new text. Include an unavailable external provider only as an honest unavailable reference, not a new device subsystem. This round does not build that proof.

## Coverage

Read applicable Agora4 AGENTS, Start Here, Constitution, Design Commitments, Runtime Guide; targeted Agora Spec sections 3-6 and Objects and Facets introduction/reference/identity sections; Implementation Status integration/current-runtime/limits evidence. Inspected application_schema.py in full, applications.py lifecycle and dispatch, application_data.py in full, packages.py manifest/install/tools portions, schemas.py facet validation, and relevant notation world.py/moo.py/desk_knife.py construction/property/discovery portions. Read the COM pages and Engber article; a Newton Technology Journal programming introduction was also inspected but is not needed for these findings. Prior memory only oriented the distinction between operation compatibility and payload preservation; current-source statements above were checked directly. No executable or end-to-end claims follow.

## Additional external-file pressure case

"Native application" has two plausible meanings here. An OS-native application can be a conventional Windows/Linux/macOS program reached through its own APIs, accessibility or file formats. A world-native application consumes Agora objects and admitted operations. Supporting the former does not require rewriting it into the latter. A world-native package can provide an adapter to an OS-native program, while the program remains external to native replay.

For one document edited in an external program, keep logical subject identity distinct from the file locator, file/resource incarnation and observed content revision. A rename can preserve a subject; replacing bytes at the old pathname need not preserve it. File identity signals and explicit provider bindings can support continuity, but a path string alone cannot establish it. On refresh, an adapter records a new observation with origin/freshness and resolves the binding according to its contract. It must not call a stale cached facet the authoritative current external file. Importing a retained copy is a different explicit operation from observing the live file.

Uninstall can remove an adopted default handler/provider binding without discarding the subject. Native records survive under native retention; external files survive under their own custody and deletion rules. The object journal does not back up their bytes merely by recording a path. A retained export must say whether it includes actual content or only metadata and references. None of this requires volume or driver implementation in this round.
