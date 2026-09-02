# Whole-OS object revision

August 31, 2026. The user requested changes to the core documents and further reasoning about objects stable enough for a whole OS, without new web research.

## Current documents

*Since this revision the object contract was consolidated into [[Objects and Facets]] v0.3, which supersedes the revised [[Agora Objects (superseded)]] and incorporates [[Facets in Everyday Use]]; the design documents now live under `docs/` (see [[Start Here]]). Links below point at the archived copies where the current documents have moved on.*

- [[Agora Spec]]: general-purpose scope, ordinary-use coverage, and explicit OS responsibilities that object records do not implement.
- [[Agora Objects (superseded)|Agora Objects]]: subject and reference semantics, scoped facets, domain operations, independent state dimensions, compatibility, recovery, and bounded failure.
- [[Facets in Everyday Use|Facets]]: everyday explanation centered on photos, reading, media, communication, schedules, and devices.
- [[Object Use Cases]]: twelve everyday areas, cross-domain upgrade/outage cases, revised principles, and acceptance obligations.
- [[ASSESSMENT|Revised assessment]]: preserves earlier research and counterexamples while correcting the development-workflow emphasis and overly broad identity-splitting advice.
- [[example_world.json|Example world]]: fifteen fictional entities illustrating repeated memberships, private state, frozen submissions, recurring occurrences, disconnected resources, and uncertain effects.

## Important changes of position

1. An object need not acquire behavior or generate another object. Receiving, reading, listening, maintaining, and revisiting are complete uses.
2. Preserve the intended subject; distinguish content revision, location, representation, occurrence, activity, and role.
3. A difference in perspective or privacy can belong in scoped facets without duplicating the subject.
4. Maintained intent is one operation family. Sends, prints, device use, view state, and content edits require different contracts.
5. Unknown bytes surviving an edit do not imply preserved meaning. Enforce dependencies and compatibility at operation boundaries.
6. Restoring code, restoring data, and reconciling external outcomes are distinct. Basic controls must survive degraded semantic services.
7. An object subsystem does not account for most OS implementation work, even after broadening its demonstrations.

## Preservation and validation limits

The `before-revision` directory contains historical copies, not current design recommendations. `source-hashes-before.json` records the initial source hashes. The Constitution was left unchanged. This work did not edit `Security Model.md`; that document changed independently while the object revision was in progress.

Content QA checks Markdown fences and local links, JSON reference integrity, and internal invariants in the illustrative world. The world omits the full journal, older revisions, payloads, registry, and grants, and is not a runnable OS or a complete export bundle. The fourteen earlier counterexamples and their results remain separate bounded exercises; they do not validate the newly proposed OS behavior. Historical citations in the assessment are retained from the earlier research. No new web research was performed for this revision.
