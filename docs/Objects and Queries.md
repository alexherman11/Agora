# Objects and Queries

Status: proposed contracts. Operation names and wire formats are not yet fixed.

## Identity and meaning

An entity identifies a subject independently of its name, location or rendering.
Facets provide typed facts about that subject. A note can appear in several views
without becoming several notes; an appearance owns its placement and view-specific
settings. A package, installation, conversation and development task can each be
entities without sharing the same lifecycle.

References distinguish a live identity from an exact revision. Editing normally
targets an identity with an expected revision. Execution and build inputs pin
revisions. A missing, deleted, inaccessible or unsupported target must remain
distinguishable from a successful read; never silently substitute a newer object.

The object model is a common vocabulary for meaningful state. It is not a demand
to translate every Linux byte into a facet. Files, processes and external resources
may be represented by references and observations, as described in
[Architecture](Architecture.md).

## Application-defined facets

JEFF must be able to introduce data shapes without editing the platform's source.
An application facet definition is a native object with:

- A namespaced type identity and immutable schema version.
- A bounded, supported JSON Schema vocabulary for validating values.
- A generic projection description: labels, useful fields and summary limits.
- A supported update/conflict policy.
- Optional migration declarations with explicit source and destination versions.

An attached facet names its exact definition version. The first schema vocabulary
should cover records, strings, numbers, booleans, enums, lists and references.
The gateway validates values, limits and references before recording mutations.
Unknown definitions remain inspectable as attributed data; they cannot acquire
executable or privileged meaning simply by naming a field.

Definitions are data, not a route to arbitrary host-side validators. Custom
application computation runs in the package runtime. Initially, generic field
projection is enough; it must expose the schema identity, provenance, relevant
uncertainty and omitted content. A custom renderer cannot hide facts from the
ordinary inspector.

## Updates and evolution

The starting policy for application records is conditional replacement: the writer
supplies the revision it read, and a conflicting edit receives the current revision
without changing state. Do not offer an arbitrary merge function as a shortcut.
Specialized merge behavior, such as collaborative text, needs an explicit supported
contract and tests before a definition can select it.

A schema revision does not reinterpret all existing values. Old facets retain
their definition and remain readable. An additive schema change is compatible only
when old values actually validate and retain their meaning. A package declares
which versions it reads and writes.

Migrations are deliberate, separately identified actions with preconditions,
progress and results. They record resulting native changes. Replay applies those
recorded changes without executing migration code. Installing old code does not
automatically reverse a migration.

Namespaced definitions avoid accidental collisions; they do not decide trust or
authority. Installing a type cannot grant access to more objects or redefine a
protected host capability.

## Collections describe membership

A notes lens should mean “notes appearing in this scene,” including future notes.
Its binding stores a query, not a list that JEFF must rewrite whenever a note is
created.

The initial query vocabulary should support a scene or explicit collection scope,
required facet types, a small set of typed field filters, ordering and a limit.
Use declarative predicates with predictable cost; do not execute package code or
accept raw SQL inside the protected read service.

A query result contains references, a snapshot revision, ordering and completeness
information. Pagination belongs to that snapshot. A subscription begins with a
snapshot and watermark, then delivers changes after it; reconnection must either
resume without gaps or return a fresh snapshot. Coalescing rendering updates is
fine. Silently losing a membership change is not.

Indexes are derived from native history. A live result is not a second authoritative
collection. Persist a result only when the person intentionally asks for a frozen
selection or another durable artifact.

Scene membership and entity identity are different: a scene may show one entity
more than once. Queries must specify whether results are distinct entities or
appearances. Ordering needs a stable tie-breaker so refreshes do not shuffle equal
values. A selection should report when its target leaves a result rather than
silently selecting a neighboring item.

## Access follows the query's scope

A query describes what to select; authority determines what can be returned.
The local development profile can cover all current and future objects in the
personal world. Narrower profiles must explicitly define their collection scope,
including whether membership added later is included.

Subscriptions recheck changes in effective authority. Unauthorized objects must
not leak through counts, cursors or change notifications. Permission to read a
query result is not permission to modify every result. Sharing a query or lens
does not itself share its data or confer the author's delegation.

These rules permit simple broad local access now while keeping live collections
usable under later sharing. Detailed distributed query and synchronization
protocols remain open.

## A worked application

JEFF creates a review board:

1. Define an application facet with a review state and optional due date.
2. Attach that facet to selected notes through the gateway.
3. Bind the board to notes in a scene, filtering by the supported review state.
4. Render cards from live query results; keep pointer motion local to the view.
5. Commit a state change or final placement with the revision the interaction read.

A newly created matching note appears automatically. A conflicting edit is surfaced.
Changing the board's layout does not change note identity. A CLI tool and JEFF can
inspect the same review facts without opening the board.

This exercise should determine the first schema and query vocabulary. Rich graph
queries, custom merge engines and arbitrary computed projections should wait until
use demonstrates a need.
