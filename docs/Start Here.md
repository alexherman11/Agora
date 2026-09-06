# Start Here

The Agora OS design documents. This is an Obsidian-style vault: wiki-links resolve
by note name, and note names are unique across the current documentation.

## Authority

The structure separates commitments, the whole-system vision, precise contracts,
and the essays that explain why they matter.

| Tier | Where | Rule |
|---|---|---|
| Constitutional draft | [[Constitution]] | Rights, invariants, stewardship and the fork right govern the design. It remains unratified; bracketed values are open. |
| Master specification | [[Agora Spec]] | The whole-system vision, shape, reasons and roadmap. Governs where references are silent. |
| Reference | `Reference/` | Detailed contracts. Each reference owns its stated subject; it wins over the Spec on that detail, never over constitutional rights. |
| Essays | `Essays/` | Examples, pressure tests, social and civic vision. References govern mechanics; essays are not implementation evidence. |
| Implementation | [[Implementation Status]] | What actually exists and what has been checked. Proposed schemas and SDK calls do not imply a working runtime. |
| Working guidance | Repository root | `AGENTS.md` explains contribution practice; `DECISIONS.md` records choices and evidence. |

This is the complete current design set for Agora3. It does not depend on an
earlier edition or an absent addendum. When two current documents disagree,
correct the passages rather than leaving readers to assemble a chain of overrides.

“Authoritative” means the current design to work from, not an immutable build
order. Experiments and the person's intent can revise it; a mismatch with code
needs an explicit decision, not an implicit redefinition.

## Reading order

1. [[Constitution]] — what Agora may never become.
2. [[Agora Spec]] §1–§4 — the vision and object system in outline; continue through
   the full Spec for JEFF, voice, attention, recovery, rooms and the feature horizon.
3. [[Objects and Facets]] — the object contract, beginning with its ten-minute
   introduction. Appendix A carries documents, music, messages, appointments,
   devices and creation examples.
4. [[Native Development]] — follow “make the notes draggable” through Linux,
   native source, installed tools, candidate testing and a programmable shell.
5. [[Extensions]] — package declarations, search-before-mint, adoption, the widget
   example, and the longer path toward shared vocabulary.
6. [[Reconcilers]] — the thermostat model, spec/status schemas and failure cases.
7. [[Security]] — broad development authority, protected boundaries, the threat
   cases, and conflicts that remain to be resolved.
8. [[The Web]] — casts, browser actions, source adapters and publishing.
9. Essays as interest takes you: [[Facets in Everyday Use]], [[Object Use Cases]],
   [[Rooms]], [[Democracy]], [[Ownership]].
10. Before implementation: [[Implementation Status]], [[Agora Spec]] §22 and
    [[Native Development]] §9, then [AGENTS.md](../AGENTS.md).

## Reference

| Note | Holds |
|---|---|
| [[Objects and Facets]] | Entities, facet schemas, live/pinned references, overlays, copy verbs, residency, live collections, projection, storage; Appendix A: everyday subjects |
| [[Reconcilers]] | Managed controllers, spec/status, observation freshness, ownership, blocked/conflict, restore and conformance |
| [[Security]] | Claims/grants/effects, broad local development, the host/guest boundary, coverage map, sharing and recovery obligations |
| [[Extensions]] | Native source packages, handlers, lenses, skills, dependencies, conformance, adoption and common/core promotion |
| [[Native Development]] | VM and state placement, source/build/install identities, persistent tools, feedback loop, shell/chat editing, asynchronous workers and portability |
| [[The Web]] | Pages and casts, browser verbs, adapters, object endpoints, publishing and uncertain external outcomes |

## Essays

| Note | Holds |
|---|---|
| [[Facets in Everyday Use]] | What the object contracts should feel like in ordinary use |
| [[Object Use Cases]] | Cross-domain pressure tests and obligations before freezing the protocol |
| [[Rooms]] | Shared places, parallel presence, co-created work and several daemons |
| [[Democracy]] | Civic attention, deliberation, human franchise, governance and the fork |
| [[Ownership]] | Openness, license direction, stewardship, hosting and the founder transition |

## Conventions

- **Citing.** `Spec §N`, `Objects §N`, `Security §N`, `Constitution III.6`.
  Keep established section numbers stable where practical.
- **Examples.** Field tables, schemas, SDK sketches and worked sequences live
  alongside their contracts. Label illustrative syntax and hypothetical outcomes.
- **Status.** References state intended behavior. [[Implementation Status]] owns
  claims of working behavior and tested limits. A proposed security mechanism is
  an obligation to test, not evidence of enforcement.
- **Open decisions.** Bracketed values and explicit open-decision sections stay
  open until there is reason to choose. The feature horizon is not a build order.
- **Names.** “JEFF” is the first daemon's name; “daemon” is the role and the
  Constitution's term. A package is an executable form of the extension model,
  not a second application ontology.
- **History.** Historical drafts and review evidence remain in Git. They do not
  need to be read to understand this edition.
