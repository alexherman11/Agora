# Objects and facets

This note explains the object model's direction and present implementation.
[[Runtime Guide]] owns exact APIs; [[Implementation Status]] owns evidence.

## Identity and use

A subject has an identity; its current content, location, open view and activity
are different things. A paper may be a retained document, a reference to an
external source, several appearances on desks, and a citation inside a memo.
Those uses should remain distinguishable without inventing a universal identity
for every internal value. Ordinary imported or read-only things are first-class
uses of the environment.

References can follow current content or retain a particular revision. Anchors
can identify a span, page, item or domain-specific location. Live anchors may
track edits under a declared mapping; pinned citations retain their evidence.
Ambiguous or missing targets should remain understandable rather than silently
becoming a different subject. General cross-revision anchoring is not implemented.

## Current records and schemas

The native store contains objects identified by strings, with schema-admitted
facets, object-level revisions and recorded authorship. `world.transact` replaces
selected facet values atomically using expected revisions. A stale or invalid
change rejects the batch. `null` detaches a facet. This is not per-span provenance,
independent facet revisioning or a general CRDT system.

Applications can install schemas and use generic JSON inspection before building
specialized views. The current validator's accepted schema subset is documented
in [[Runtime Guide]]. Future compatibility should preserve inert unfamiliar data
where possible and make only relevant unsupported constraints block an action.
Unknown labels should not disable unrelated edits or confer authority.

Tags and profiles are useful for choosing presentation, templates and workflows.
They are advisory classifications. Action availability still depends on supported
contracts and current caller authority; satisfying a tag is not satisfying a
capability or receiving permission.

## Content and representations

The current shell stores `core.appearance` on note subjects. This is a bootstrap
representation, not proof that a subject can have several independent native
appearances. Separate appearance objects, scene records or adapters are possible
ways to add that capability. Preserve independent identity and lifecycle of uses
without requiring one storage encoding before an application can be useful.

Content can live in retained native records, files, blobs or external resources.
The important questions are which bytes are retained, what is authoritative, how
edits reconcile and what can be exported or recovered. A path or hash is not a
backup. Two editing interfaces can be writable if they participate in one defined
version/conflict protocol. Independent writers should not masquerade as one truth.

## Computed values and presentation

A value can come from a literal, a binding or several contributions under an
explicit resolver. Exclusive ownership is one possible policy; precedence,
pipelines, container layout and joint solvers are others. Security authority is
separate from presentation precedence.

A first dependency engine may accept only acyclic inputs. Bounded cyclic solvers,
feedback and simulations remain possible in authored extensions. Pure evaluation
excludes hidden I/O and model calls; authorized observations and model results can
arrive as explicit inputs. Lazy pure evaluation can run on demand under a budget,
returning pending, stale or unavailable where appropriate. A read should not hide
an external effect. The general binding/dependency engine remains unimplemented.

Maintain implementation identities and explicit update policies where results
depend on code. A standing policy can adopt compatible updates without repeated
human approval. Data and theme references can be live independently of code pins.
Derived geometry and committed placements are both useful; their resolution and
manual-edit semantics need to be visible. See [[Presentation and Operators]].

## Ordinary actions and reuse

People can Copy, Duplicate, Paste, move and export. The implementation determines
whether that means another reference, independent content, a retained revision
or a transfer. Closing a view is different from deleting its subject. Annotation
and reading-position export can be intentional while private overlays stay private
by default. Copying content does not copy executable authority or expand audiences.

Native domain actions share meaning between human controls and JEFF tools. This
does not require every gesture, frame or local UI button to become a public verb.
The installed action registry remains available when a view closes. Generic
inspection can precede polished visual or token projections.

## Queries, revisions and recovery

Current queries are bounded, paginated reads, not subscriptions. Small snapshots
are useful during prototyping. Scoped inputs, extensible bounded queries and
targeted writes can reduce broad scans and false conflicts as real use grows.
Custom analysis belongs on supplied inputs in an appropriate execution boundary,
not as arbitrary code or unbounded SQL inside the protected service.

An unresolved disagreement may deserve durable alternatives and authorship.
A stale preview or unsupported property can be a compact diagnostic. Every
technical conflict need not become another persistent object. Finer field/facet
guards and merge strategies should follow observed contention rather than an
universal merge taxonomy.

The current local journal is the accepted native history. Replay rebuilds state
without executing programs or repeating external effects. Restoring a view or
package is distinct from restoring data, VM files or external state. Current
authority remains outside replay. Distributed custody, offline merge, retention
and erasure need their own experiments; a local journal does not settle them.

## Useful pressure tests

Try two views of one document; a pinned quotation beside a live source; a native
and external editor touching the same content; a style edit during autosave; and
annotation export without private activity history. These are ways to evaluate
the model, not prerequisites for every new application.
