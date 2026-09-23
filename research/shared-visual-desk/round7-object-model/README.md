# Open investigation: an extensible object and capability model

2026-09-23. Research in progress, at Alex's request. No implementation, schema migration, package installation, runtime restart or final architecture selection is part of this round.

## Direction from Alex

Explore an object model closer to original Agora's composable facets than the experimental verb desk's fixed kind and string properties. Investigate what it unlocks, complicates and requires for a stable implementation that can accept applications, new schemas, object types and ideas far into the future. Running scripts are not the immediate question. Historical object-oriented operating systems and application environments are sources of mechanisms and counterexamples, not templates to copy wholesale.

Keep the recent interface scope: Photoshop means its interface as a demanding composition example; universal artistic-material primitives are not required. Retain the system / visual / object working contexts and distinguish them from desktop / application / object composition levels. Ordinary object work should not require visual bookkeeping. Definitions and applications can themselves be subjects of work through the shared verb system.

This is a thinking round. Long-lived extensibility is the aim; no finite prototype can establish infinite extensibility. We should seek a small set of durable boundaries and explicit mechanisms for changing the rest, while keeping ordinary reading, writing, organizing and direct use uncomplicated.

## Three research roles

- Foundations: competing object foundations and primary historical sources; identity, facets, interfaces, behavior and the minimum common substrate.
- Editing: independently evolving schemas and editors over shared objects; preserving unfamiliar information, migrations, verb meanings, conflicts and recovery.
- Media: installed/native/external applications and reusable components; installation, update, removal, shared data, dependency and capability discovery.
- Coordinator: shared-desk liaison, cross-review, ordinary-use pressure cases and integration with the current Agora contracts.

First-pass findings are now retained in [Foundations](foundations.md), [Editing](editing.md) and [Media](media.md). They exchanged critiques about unknown data, dependent interpretations, runtime interface generations and application removal. These are proposals and source reviews, not newly installed guarantees.

## Questions worth keeping open

1. Does a facet carry only structured data, or also a schema identity and behavioral interface? Which relationships are explicit rather than inferred from a kind label?
2. What identifies a subject across independent applications, repeated appearances, references, schema revisions and removal of its original editor?
3. How can an older editor preserve new facets while declining operations whose semantics it cannot honor?
4. What exactly does installing an application register: schemas, operations, editors, view definitions, import/export adapters, dependencies and defaults? Which are separate lifetimes?
5. What remains readable/editable after uninstalling an application? What is an honest fallback for unknown structured data or opaque native files?
6. How do native applications and external installed programs participate without pretending both have the same authority, persistence or inspection guarantees?
7. How can views and contextual verbs compose capabilities without a universal class hierarchy or a proliferation of per-application bridges?
8. Where should the stable boundary stop so that future models need not fit a frozen document, graph or JSON-only representation?

## Pressure cases, not an implementation backlog

Follow one document with text, a date, annotations and application-specific metadata through two independent editors, a schema extension, an older editor revisiting it, removal of the original application and adoption by another editor. Also consider a collection containing both native objects and externally owned files, and a newly installed capability that can operate on existing objects without converting or copying their identity.

Keep source code, installed behavior, migration results and human interaction evidence separate. Current Agora facets and the synthetic desk are different implementations. Earlier round-six checks do not establish the new model. Historical research notes should record read coverage and link primary sources.

## Collaboration

The coordinator placed the open research task at **bridge a63** (subject s62), linked to the prior direction at a58. Announcements are **bridge Talk a66** and **studio Mailbox a701** (Astra 009). The two teams retain separate working spaces. Those channels are pull-based; a posted request does not wake an idle Claude session or imply agreement. The task remains open after this first research pass.

The [coordinator's evolving questions](coordinator.md) separate current runtime facts, historical reading and hypotheses. The three role reports are independent contributions rather than an agreed specification.
