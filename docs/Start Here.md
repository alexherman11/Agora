# Start Here

The Agora OS design documents. This repository is an Obsidian vault: every wiki-link resolves by note name, and every note name is unique across `docs/` and `research/`, so links survive moves between folders.

## Authority

Documents are arranged by how much they win, not by topic. The authoritative map is the document map at the top of [[Agora Spec]].

| Tier | Where | Rule |
|---|---|---|
| Supreme | [[Constitution]] | Wins over every other document. |
| Master specification | [[Agora Spec]] | The whole-system shape, the reasons, the roadmap. Governs where the references are silent. |
| Reference | `Reference/` | The contracts. A reference wins over the Spec on detail. |
| Essays | `Essays/` | Explainers, pressure tests, and social/civic design. Superseded on mechanics by the references. |
| Research | `research/` | Review dossiers, toy models, and archived drafts. Historical record, not current design. |
| Build | repository root | `BUILD_PROMPT.md` (what milestone one is), `AGENTS.md` (how to work on the code), `DECISIONS.md` (settled questions and friction). Governed by the Spec; the code never outranks the documents. |

## Reading order

1. [[Constitution]] — what Agora may never become.
2. [[Agora Spec]] §1–§4 — the core idea and the object system in outline.
3. [[Objects and Facets]] — the object layer contract. Appendix A carries the everyday worked examples.
4. [[Reconcilers]] — how spec/status keeps the world's promises.
5. [[Security]], then [[Security Addendum]] — the addendum's two-sided model is the version to build.
6. [[Extensions]] and [[The Web]] — how vocabulary changes, and how the world meets the web.
7. Essays as interest takes you: [[Facets in Everyday Use]], [[Object Use Cases]], [[Rooms]], [[Democracy]], [[Ownership]].
8. Before writing code: [[Agora Spec]] §22 for the roadmap, then `BUILD_PROMPT.md` and `AGENTS.md` at the repository root.

## Reference

| Note | Holds |
|---|---|
| [[Objects and Facets]] | entities, facets, references, state dimensions, copy verbs, residency, projection, storage; Appendix A: everyday subjects |
| [[Reconcilers]] | the spec/status contract, observations, drift, blocked, conflict, the constitutional catalog |
| [[Security]] | claims, grants, effects; the coverage map; the first drill |
| [[Security Addendum]] | the two-sided model; supersedes Security §3, §4.6, and §6 |
| [[Extensions]] | the bundle, the loop, tiers, promotion, retrofit |
| [[The Web]] | pages as objects, the browser lens, adapters, the object endpoint, publishing |

## Essays

| Note | Holds |
|---|---|
| [[Facets in Everyday Use]] | what the object contracts should feel like in ordinary use |
| [[Object Use Cases]] | twelve everyday areas under pressure, and the obligations they impose before the base protocol freezes |
| [[Rooms]] | the multiplayer layer: shared world-lines, presence, two daemons in one room |
| [[Democracy]] | the civic layer: sortition, consensus-mapping, the human franchise, the fork |
| [[Ownership]] | license, trademark, entity structure, the founder sunset |

## Research

| Folder | Holds |
|---|---|
| `research/whole-os-object-review/` | [[REVISION]] notes; [[Agora Objects (superseded)]], the object design that [[Objects and Facets]] replaced; pre-revision copies of the Spec, Objects, and Facets |
| `research/object-facet-review/` | [[ASSESSMENT]], executable toy counterexamples, an illustrative example world |
| `research/graph-memory/` | memory for a world of objects; start at [[operating-system-memory]] |
| `research/security/` | [[scoped-collaboration]] and [[composed-export-model]], follow-ons to the security model |

## Conventions

- **Citing.** `Spec §N`, `Objects §N`, `Security §N`, `Constitution III.6`. Inside the references, cited titles are links: `[[Objects and Facets|Objects]] §5.4`.
- **Status lines.** Every reference opens with a version, a "companion to" line, and a status block. Every essay opens with a banner naming what supersedes it.
- **The documents are specification, not description.** They state intended behavior. What is actually built is whatever passes the tests under `tests/`; milestone one ([[Agora Spec]] §22) is the first code, and it lives in `kernel/`, `cli.py`, `shell/`, and `jeff/`. Bracketed values are open decisions; values committed for M1 are listed in `DECISIONS.md`.
- **The code never outranks the documents.** Where an implementation and a reference disagree, the reference is right and the code carries a `DECISIONS.md` line explaining the deviation, or the code changes.
- **Names.** "JEFF" is the first daemon's name; "daemon" is the role and the Constitution's term. The essays say JEFF; the references say daemon.
- **Not in the repository.** Sol's *Security model and attack analysis* draft 0.2, which [[Security]] builds on, is not currently here. If it turns up, it belongs under `research/security/`.
