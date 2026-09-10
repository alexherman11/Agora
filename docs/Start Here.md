# Start Here

Agora is a computing environment that a person and JEFF can reshape through use.
It is meant to become a home for ordinary work, memory, invention and eventually
shared places—not merely an agent harness or an application-development demo.

This vault keeps three things together without confusing them:

1. the values and whole-system imagination that make Agora worth building;
2. detailed design reasoning, including alternatives and failure cases;
3. exact descriptions and evidence for the runtime that exists today.

A desire for architectural freedom is not a reason to erase design memory. When
a mechanism is too prescriptive, reclassify it as a hypothesis, explain the
property it was trying to protect, and leave room for a better solution.

## Document roles

| Role | Documents | How to read them |
|---|---|---|
| Moral direction | [[Constitution]] | An unratified statement of the project's human commitments. It is not a license, deployed guarantee or frozen technical architecture. |
| Durable design charter | [[Design Commitments]] | The smallest set of ends a substantially different implementation should preserve, plus the status vocabulary used across the vault. |
| Whole-system vision | [[Agora Spec]] | The complete experience and current architectural story. Detailed and revisable; it should remain generative rather than become an implementation checklist. |
| Current behavior | [[Runtime Guide]] | Exact implemented operations, package forms and commands. When code and this guide disagree, investigate and correct the current contract. |
| Evidence and limits | [[Implementation Status]] | What exists, what was tested, when, and what remains absent or experimental. |
| Design references | Reference/ | Deep reasoning, candidate contracts, worked schemas, alternatives and conformance questions. A reference governs current work only where it labels a chosen or current contract. |
| Vision essays | Essays/ | Ordinary situations and social possibilities. They are active sources of product meaning, not conformance requirements. |
| Transition record | [[Review Coverage]] | How the September 9 critique changed the status of former universal claims and what was deliberately retained. |
| Prototype lineage | [[Personal Lenses]], [[Executable Components]], [[Astra Harness]], [[Security Addendum]] | Important September 5 documents from the older `docs` branch, retained with explicit banners. They record implemented prototypes and decisions from that line, not Agora3 APIs. |

The person's direction and evidence from use guide development. A vision paragraph
does not authorize external action or establish an implemented guarantee. Conversely,
the absence of implementation does not make the product vision disposable.

## Reading order

1. [[Constitution]] — why power, privacy, loyalty, recovery and exit matter.
2. [[Design Commitments]] — what should survive and what remains free to change.
3. [[Agora Spec]] §1–§7 — the experience, world, object model, applications and JEFF.
   Continue through voice, attention, activity, authority, rooms and the feature
   horizon to understand the whole system.
4. [[Objects and Facets]] — identity, references, content, occurrences, overlays,
   capabilities, projection, storage and everyday worked examples.
5. [[Native Development]] — follow “make the notes draggable” through Linux,
   retained source, installed tools, candidates, shell replacement and evidence.
6. [[Presentation and Operators]] — the evidence-backed small presentation slice
   and the larger space of style, composition and interaction.
7. [[Personal Lenses]] and [[Executable Components]] — earlier implemented
   declarative and QuickJS approaches whose lessons inform the current package path.
8. [[Extensions]] and [[Reconcilers]] — growth, reuse, observation and maintained
   work, as design families rather than compulsory universal subsystems.
9. [[Security]] — present boundaries, the larger threat model and obligations that
   arise when integrations or multiple people are introduced.
10. [[The Web]] — pages, sources, browser behavior, adapters and publication.
11. The essays: [[Facets in Everyday Use]], [[Object Use Cases]], [[Rooms]],
    [[Democracy]] and [[Ownership]].
12. Before changing code: [[Implementation Status]], [[Runtime Guide]],
    [AGENTS.md](../AGENTS.md) and [DECISIONS.md](../DECISIONS.md).

## Reference map

| Note | Holds |
|---|---|
| [[Objects and Facets]] | Entities, identity, references, facet schemas, overlays, copy/transfer choices, actions, relationships, projection, storage and everyday examples |
| [[Native Development]] | Protected native state, Linux execution, source/build/install identities, persistent tools, candidates, shell/chat authorship and development evidence |
| [[Presentation and Operators]] | Retained visual intent, composition, layout, direct manipulation, preview, truthful rendering and the September 9 experiment |
| [[Personal Lenses]] | Older implemented declarative list/detail lens, revision-pinned activation, recovery and interaction evidence; prototype-lineage status |
| [[Executable Components]] | Older implemented QuickJS authored-component boundary, scoped effects, candidate worlds and action discovery; prototype-lineage status |
| [[Astra Harness]] | Earlier managed-account adapter design and runtime-inventory evidence, with current Agora3 differences routed to Runtime Guide |
| [[Security Addendum]] | Transition away from one fixed security spine toward broad standing delegation, protected crossings and open internal topology |
| [[Extensions]] | Package declarations, the search/draft/prove/adopt loop, compatibility, promotion, retrofit and reuse |
| [[Reconcilers]] | Desired and observed state, controller patterns, drift, blocked/conflict states, budgets, restore and alternative activity models |
| [[Security]] | Claims, grants, effects, current host/guest enforcement, threat cases, recovery and future sharing boundaries |
| [[The Web]] | Live and pinned sources, browser actions, adapters, object endpoints, publication and uncertain external outcomes |

## Essay map

| Note | Holds |
|---|---|
| [[Facets in Everyday Use]] | How identity, facets, views and actions should feel in ordinary life |
| [[Object Use Cases]] | Cross-domain pressure tests for documents, media, communication, calendars, files, devices, contacts and temporary data |
| [[Rooms]] | Shared places, parallel presence, accumulated craft, several JEFFs, consent and dissolution |
| [[Democracy]] | Civic attention, deliberation, human authority, governance tools and limits |
| [[Ownership]] | Inspectability, openness, capture resistance, stewardship and sustainable operation |

## Conventions

- **Status before syntax.** Check whether a passage is a constitutional value,
  chosen direction, current contract, hypothesis, example, evidence or open question.
  [[Design Commitments]] defines those terms.
- **Exact APIs.** The [[Runtime Guide]] owns current operation names and formats.
  Older schemas in references are worked designs unless explicitly marked current.
- **Evidence.** [[Implementation Status]] owns claims of working behavior. Static
  prose, a build receipt, a mock transport and live human interaction are different
  evidence levels.
- **Detailed reasoning.** Preserve examples, failed routes and counterarguments.
  Git history is a backup, not a substitute for an intelligible current design.
- **Changing commitments.** Relax an overbroad mechanism by naming the protected
  end and reopening the mechanism. Do not delete the surrounding product insight.
- **Open decisions.** Bracketed values and explicit open sections remain open.
  The feature horizon is not a build order.
- **Names.** “JEFF” is the first personal collaborator's name; “daemon” is the
  general role used in older passages. A package is an executable extension, not
  a second application ontology.
- **Links.** Wiki-link note names are unique. Keep this edition self-contained and
  correct contradictions rather than requiring readers to reconstruct the design
  from superseded commits.

[[Review Coverage]] records the mass-rewrite correction and the disposition of
the former universal claims. It is a map, not a replacement for the arguments
kept in the documents themselves.
