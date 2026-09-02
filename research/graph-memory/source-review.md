# What the research supports

Primary-source review · Accessed 31 August 2026

**Conclusion:** connected representations are a credible tool for memory, especially when evidence is distributed across objects or changes over time. Published results do not establish that a graph is always better, that graph databases are necessary, or that any reviewed framework satisfies Agora's security and rollback requirements.

This is a targeted architectural review, not an exhaustive systematic survey. Full-text sections were inspected for Zep, HippoRAG 2, A-Mem, Mem0, Hindsight, SimpleMem, and LongMemEval. LeanMem, LoCoMo, and EverMemBench were screened through their primary abstracts. Official GraphRAG, Graphiti, SQLite, and provenance documentation supplied implementation context. No published result was independently reproduced; current upstream code was not audited.

## 1. Approaches worth borrowing from

| Work | Relevant mechanism | Proposed use in Agora | Limitation of the evidence |
| --- | --- | --- | --- |
| Zep / Graphiti | Episodes, resolved entities, qualified temporal facts, hybrid retrieval | Source-linked claims and time-aware retrieval | Conversation experiments do not establish rollback, authorization, or erasure correctness |
| Microsoft GraphRAG | Local entity retrieval and broader community-based synthesis | Separate object questions from project-wide questions | Broad synthesis can be expensive; not a reason to summarize the whole world continuously |
| HippoRAG 2 | Passage nodes and Personalized PageRank retrieval | Experimental associative retrieval over evidence and concepts | Passage-QA evaluations do not establish useful long-lived desktop behavior |
| A-Mem | Generated notes, candidate linking, evolving memory descriptions | Model-assisted links and selective consolidation | Generated organization can drift; revisions and correction remain necessary |
| Mem0 / graph variant | Compact memory extraction, with an added graph representation | Strong non-graph baseline and explicit graph ablation | The graph's benefit depends on task and comes with overhead |
| Hindsight | Separate facts, experiences, summaries, and beliefs | Distinguish evidence from JEFF's interpretation | Categorizing something as a fact does not independently verify it |
| SimpleMem | Structured compression, multi-view indexes, adaptive retrieval | Budget-conscious baseline and resumable briefings | Compression quality needs task-specific source checks |
| LeanMem | Different storage treatment for profiles, events, and records | Test selective maintenance by memory type | Recent preprint; abstract-level screening only in this pass |

The following notes are tied to the primary sources. The Agora applications and cautions are this researcher's design judgments.

### Zep, January 2025; Graphiti upstream checked August 2026

The paper distinguishes episodes, semantic entities/relations, and communities. It records valid time separately from ingestion time and describes cosine, BM25, and breadth-first retrieval. Its invalidation procedure favors new information; Agora should instead consider source authority, applicability, and unresolved conflict. Preserve episode references and temporal qualification, but add explicit branches and protected provenance. The paper evaluates a configured memory service, not a universally reproducible result for every Graphiti deployment. [Paper, §§2–4](https://arxiv.org/html/2501.13956v1).

Current Graphiti documentation distinguishes the open-source framework from managed Zep and lists pluggable graph backends. It marks Kuzu support deprecated. Treat Graphiti as an optional extraction/retrieval adapter whose outputs still pass Agora validation. The upstream documentation's own comparisons with competitors are not neutral evidence of superiority. [Official repository](https://github.com/getzep/graphiti).

### Microsoft GraphRAG, current query documentation

Local search combines graph information and source chunks. Global search synthesizes community reports; DRIFT adds community context to local exploration. Basic vector search is available for comparison. This supports multiple retrieval recipes rather than a single obligatory graph path. For Agora, test local provenance first and defer community synthesis until broad project questions justify it. [Official query overview](https://microsoft.github.io/graphrag/query/overview/).

### HippoRAG 2, February 2025

The framework adds passage nodes to a graph of extracted phrases and uses Personalized PageRank for retrieval. Its ablation reports average passage recall@5 of 87.1 with the complete system versus 81.0 without passage nodes across three multi-hop datasets. This suggests source-passage integration matters, not just abstract entity connectivity. For Agora, preserve evidence nodes/anchors when testing associative traversal. A high retrieval score is not a calibrated probability that a relation or answer is true. [Paper, §§3–4 and appendix](https://arxiv.org/html/2502.14802v1).

### A-Mem, February 2025

A-Mem generates structured notes, retrieves candidate neighbors, establishes links, and updates memory descriptions as new material arrives. This closely matches the desired role of JEFF as an organizer. Borrow candidate linking and evolution, but represent revisions as new attributable outputs; do not silently rewrite history or promote repeated interpretations to verified facts. Its organization and QA experiments do not test Agora's capability boundaries. [Paper, §§3–4](https://arxiv.org/html/2502.12110v1).

### Mem0, April 2025: a useful counterweight

The paper's Table 2 reports the following on LoCoMo:

| Configuration | Overall judge score | Total response p95 | Memory tokens |
| --- | ---: | ---: | ---: |
| Mem0 | 66.88% | 1.440 s | 1,764 |
| Mem0 with graph | 68.44% | 2.590 s | 3,616 |

That is **1.56 percentage points** of score improvement, with greater latency and context use. These are author-reported measurements under that experiment, not Agora projections. The paper also reports that the graph variant does not improve every question category, including its multi-hop comparison. Do not equate the graph label with automatic multi-hop improvement. [Paper, §§4.1–4.3, Table 2](https://arxiv.org/html/2504.19413v1).

### Hindsight, December 2025

Hindsight separates world facts, agent experiences, opinions, and synthesized observations, with retain, recall, and reflect operations. Recall combines semantic, lexical, graph, and temporal routes under a token budget. The separation of evidence and interpretation is especially relevant to Agora. Do not import opinion reinforcement as a trust mechanism: repeated correlated sources should not independently increase confidence. Reported benchmark gains combine architecture and model configuration, rather than isolating graph edges alone. [Paper, §§3–4](https://arxiv.org/html/2512.12818v1).

### SimpleMem, January 2026

SimpleMem combines structured extraction/compression, semantic/lexical/symbolic indexing, consolidation, and query-aware retrieval. It normalizes references and temporal expressions so compact memories remain interpretable. This is a useful comparator for testing whether careful memory units and retrieval budgeting deliver most of the benefit before graph traversal. The authors' phrase “semantic lossless compression” should not be treated as a general guarantee that an LLM summary preserves every detail Agora may later need. [Paper, §2](https://arxiv.org/html/2601.02553v1).

### LeanMem, August 2026

This recent preprint proposes separating profile, event, and source-grounded record memory according to temporal dynamics and fidelity needs, with selective updates and query-specific budgets. It reinforces a research direction: not every memory needs the same maintenance policy. This pass inspected the abstract only, so it does not recommend the implementation or endorse its comparative results. [Primary abstract](https://arxiv.org/abs/2608.03463).

## 2. Benchmarks to use, and their gaps

**LongMemEval** evaluates extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention. Use these categories and, later, a pinned public subset as a conversational regression suite. They are directly relevant to evolving memory but insufficient for project execution, scoped sharing, branch restore, and poisoned provenance. [Paper](https://arxiv.org/html/2410.10813v1).

**LoCoMo** evaluates very long conversational memory with temporal and multimodal aspects. It is useful for comparison with several memory papers above, but conversational recollection alone is not evidence that a worker will resume the correct version of a project or obey current grants. [Primary abstract](https://arxiv.org/abs/2402.17753).

**EverMemBench**, in the March 2026 revision titled *Evaluating Long-Horizon Memory for Multi-Party Collaborative Dialogues*, covers multiple participants and groups, evolving decisions, and role-sensitive understanding. Its setting is relevant to Agora rooms. Its published evaluation is not an access-control or privacy test, so separate adversarial sharing cases remain necessary. The revised title and scope matter when matching citations to earlier references. [Primary abstract, revised 11 March 2026](https://arxiv.org/abs/2602.01313).

Do not rank these systems by headline percentages across papers. Corpora, splits, readers, extraction models, prompts, available evidence, context budgets, judge rubrics, and latency boundaries differ. A retrieval recall score and an answer-quality score measure different things. Agora needs same-data, same-reader comparisons, plus independent checks of sources and behavior.

## 3. Foundations beyond agent-memory papers

W3C PROV offers a vocabulary for entities, activities, agents, and derivation. It is a useful conceptual cross-check for Agora's attribution and transformation records. Adopting that vocabulary does not require making the entire object system RDF or enforcing a universal ontology. [PROV overview](https://www.w3.org/TR/prov-overview/).

SQLite supports FTS5 and recursive common table expressions, sufficient mechanisms for an initial searchable adjacency representation. They do not establish a capacity or latency guarantee for Agora's workload. Benchmark before choosing a dedicated graph engine, and keep any engine behind portable object/event contracts. [FTS5 documentation](https://sqlite.org/fts5.html), [WITH/recursive-query documentation](https://sqlite.org/lang_with.html).

## 4. Conclusions to test rather than assume

1. Native object/action links will be more reliable and cheaper than reconstructing the same relations from prose.
2. Graph expansion will help decision tracing and prior-attempt discovery more than direct fact lookup.
3. Source-linked compact briefings will improve resumption even without advanced graph algorithms.
4. Branch-aware temporal retrieval will reduce repetition of rolled-back failures without contaminating current state.
5. A small number of explained, task-relevant associations will be more useful than unrestricted background linking.

These are Agora hypotheses. None is established by the surveyed papers alone. Their experimental treatment is specified in the [[evaluation|evaluation plan]].
