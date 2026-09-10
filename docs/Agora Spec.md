# Agora Spec

**Vision and present structure · September 9, 2026.**

## The experience we are trying to build

Agora is a general-purpose environment shared by a person and JEFF. It should
feel like a usable place to read, write, think, communicate and make things.
Ordinary work can reveal a missing capability, and developing that capability
should become part of the work rather than a trip into a separate development
project. The aim is fluid, increasingly reusable software developed through use.

Ask for a quieter reading area, a better document editor, a view of research
sources, a browser workspace or a more complete conversation interface. JEFF
should use what exists, invent what is missing and verify what the person can
actually do. A useful small application needs no special justification for
resembling an existing product. Reuse, wrappers and native replacements are
choices to compare through their usefulness and maintenance cost.

Documents, media, conversations, appointments, devices and services can have
stable identities across views and sessions. They need not all be executable,
native, fully imported or part of a project. Structured state can support rich
interfaces and semantic actions, while ordinary files, pixels and external
applications remain useful parts of the environment.

## Present structure

The current runtime is described precisely in [[Runtime Guide]]. It has:

- A protected Python service with an authenticated native gateway, SQLite event
  journal, rebuildable object state, package registry and recovery interface.
- Native objects with schema-admitted facets and object-level revisions.
- Versioned package source, retained build receipts and independently versioned
  installations. Installed actions and skills survive the closing of a view.
- An authored browser shell containing the desk and chat. Its parent retains
  credentials and recovery. The installed shell may differ from supplied source.
- A Linux VM with broad development authority, and a distinct resettable candidate
  VM without the live native connection.
- A host-side managed account/model adapter. JEFF discovers and invokes native
  operations; general code and shell execution happen in the guest.

This is a chosen implementation, not the permanent topology of Agora. Linux,
Python, a particular hypervisor, one service process and the present model adapter
can evolve. The protection and state boundaries are more important than those
deployment choices. [[Implementation Status]] distinguishes current code,
historical verification and experimental results.

## Objects, uses and meaning

Keep identity, content revision, source, representation, occurrence, location,
availability and activity understandable as different concepts. A reference can
mean a live subject, a retained revision or a particular use. Copy and Paste can
be ordinary human controls while their implementation distinguishes duplication,
reference, export and independent revision history.

Facets allow applications to add useful structured data. Advisory tags and
profiles can select views, styles and workflows; actual capabilities and caller
authority decide which actions are available. Generic inspection is a useful
starting point. Every new field need not arrive with a custom renderer, tokenizer,
serializer, merge type and perpetual controller.

The current store uses register replacement and object revisions. Finer conflict
scopes, richer anchors, separate appearances and replicated stores are options
to develop when concrete workflows need them. [[Objects and Facets]] explains
the distinction between present representation and longer-term identity goals.

## Presentation and direct interaction

Common visual changes should become small edits to retained intent: typography,
color, spacing, arrangements and application composition. Multiple contributors
can affect a result under explicit resolution—shared defaults, local exceptions,
container layouts and domain-specific solvers can coexist.

New forms remain programmable. No universal engine, acyclic-only computation
model, flat scene, integer coordinate system or closed operator vocabulary is
required. A diagram, document and desktop can use different layout machinery.
Geometry alone does not silently change semantic facts; an explicit drag/drop
interaction can legitimately change a task's stage or collection membership.

Actual rendering is evidence. Measurements, requested sizes and effective sizes
may differ. Preview, focus, selection, scrolling, undo and draft continuity matter
as much as accepting a parameter. [[Presentation and Operators]] records the
small slice and what its experiment taught us.

## Development through use

Use existing capability contracts for familiar work. Executable changes retain
source/build/install identities; ordinary data or presentation edits can be
cheaper. Tests for inventing a capability, reusing it and incrementally extending
it answer different questions. The system should reward reuse rather than make
every task rebuild its tools.

Measure correct completion, source traffic, time, correction effort and human
continuity. Ask JEFF what made work difficult, then test its suggestions against
an unchanged baseline. A green build is not proof of a usable interface, and a
fast incomplete result is not a winner. [[Native Development]] describes this
working approach and the current sources of friction.

## Activity, integrations and attention

Some actions are immediate, others observe changing resources or maintain an
intent over time. Applications can combine these with streams, transactions,
model calls and explicit workflows. Controllers are one useful pattern, not a
mandatory implementation of all behavior. [[Reconcilers]] describes the options.

Attention, memory, layout and retrieval may share useful signals, but a universal
heat field is a hypothesis, not infrastructure every feature must use. Prefer
understandable priorities, bounded interruptions and useful retrieval. Direct
reading, editing, inspection and recovery should remain useful without inference;
features that actually depend on a model should say so.

Browsers, provider adapters, files and native applications can cooperate. Live
links and pinned evidence have different uses. Publication may be a live view,
static release or provider-hosted artifact. External effects need truthful status
and retry behavior appropriate to the service. See [[The Web]] and [[Security]].

## Horizons that remain open

Shared rooms, offline collaboration, voice, devices, richer memory, background
agents and federation are directions to explore. They do not yet establish one
log-of-record topology, custody handshake, worker lifetime, model architecture,
publishing scheme or governance constitution. A new view may need new interaction
semantics while retaining the same subjects and intent.

The next useful proof is an increasingly capable application developed from
inside Agora. Let the difficulties of writing, revising, integrating and using
it determine which machinery deserves to become common infrastructure.
