# Agora graph memory research

Reframed research dossier · 31 August 2026 · Proposals, not adopted specifications

**Start with [Memory for a whole operating system of objects](<C:/Projects/Agora/research/graph-memory/operating-system-memory.md>).** This is the revised conceptual direction after the first pass focused too narrowly on ideation and experimentation. It reasons from video editing, browsing, code, casual listening, interruption and live system resources. No further web research was used for the revision.

**Working conclusion:** Agora's graph should preserve continuity between objects, their meaningful parts, their representations, particular uses, and the situations in which they matter. Useful memory can locate a moment, restore a working context, align different views, explain a dependency, or prepare a precise operation. Decision history is one application of this broader model.

The key proposed additions are addressable parts, independent occurrences, correspondence maps across representations, contextual roles, overlapping situations, and purpose-dependent working sets. Native tools should preserve connections their operations already know; models can propose interpretations and associations where useful.

The revised first prototype should cross browsing, code and media, testing whether it can:

1. Follow a selected passage, code artifact or transcript span to the right material and representation.
2. Edit one use of an object without accidentally changing its other uses.
3. Preserve actual transformation dependencies while distinguishing looser reference relationships.
4. Restore a situation across interruption without confusing old observations with current state.
5. Retrieve material through an encounter cue even when no named project exists.

The [earlier architecture](<C:/Projects/Agora/research/graph-memory/architecture.md>) and [earlier evaluation plan](<C:/Projects/Agora/research/graph-memory/evaluation.md>) remain supporting work on evidence, temporal claims, rollback, security and project history. Their project-first framing and first-prototype recommendation are superseded by the broader design. The [source review](<C:/Projects/Agora/research/graph-memory/source-review.md>) records the initial literature pass; it is not the basis for claiming that the new conceptual design has been validated.

The initial pass reviewed Agora's object, core, facet, room, constitutional, and security documents, alongside primary memory-system papers and official documentation. The revision uses first-principles scenarios and local object/facet design work. The workspace has no production object or memory implementation. A separate object/facet research directory contains bounded toy counterexamples; its recorded results are not performance or security validation of this proposal. Existing core design documents were left unchanged.

[Source fingerprints](<C:/Projects/Agora/research/graph-memory/source-fingerprints.json>) record the local design files at completion of the initial pass, not this revision; they are not an archive of those files.

No memory benchmark, model extraction experiment, database performance trial, or security test was run for this dossier. Paper results remain author-reported results. The research is sufficient to specify a first experiment, not to declare an architecture proven or a large research program finished.

The central unresolved question is whether Agora can preserve the person's referent and intention across tools, representations, situations and time without constant annotation. Adapter fidelity, part identity across edits, correspondence quality, contextual meaning, selective retention and useful action scope should guide the next experiments.
