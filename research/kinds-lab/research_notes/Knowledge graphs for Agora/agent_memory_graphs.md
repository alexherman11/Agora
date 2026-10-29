# Knowledge graphs as memory, retrieval and reasoning substrates for LLM agents

*Research notes by a Claude builder subagent, 28 Oct 2026, for the kinds-lab "Knowledge graphs for Agora" report. Evidence labels follow AGENTS.md: everything below is **read** (web sources, mostly arXiv abstract or HTML pages fetched today) unless marked **recall** (my memory of a paper body that I did not re-open) or **imagined** (inference for Agora). Numbers are as published by the authors unless an independent source is named.*

## 1. Microsoft GraphRAG (Edge et al. 2024): how it works, results, cost, limits

### Takeaway
GraphRAG builds an LLM-extracted entity graph, clusters it into a hierarchy of communities, pre-summarises every community, and answers "global" corpus-wide questions by map-reducing over those summaries; on two ~1M-token corpora it beat vector RAG on comprehensiveness and diversity in LLM-judged head-to-heads. Indexing is very expensive, local/detail questions often go to plain RAG, and later independent work shows the LLM-judge win rates are inflated by position and length bias.

### Cited Findings
- Method: an LLM builds the index in two stages, first extracting an entity knowledge graph from source documents, then pre-generating summaries for groups of closely related entities (communities); at query time each community summary yields a partial answer and the partials are summarised into a final answer. Target is "global sensemaking" questions (e.g. main themes of a corpus) that vector RAG handles poorly because they are query-focused summarisation, not retrieval. — [Edge et al. 2024, arXiv 2404.16130](https://arxiv.org/abs/2404.16130)
- Datasets: podcast transcripts (~1M tokens, 1,669 chunks of 600 tokens) and news articles (~1.7M tokens, 3,197 chunks). Community levels C0 (root, fewest summaries) to C3 (lowest level); baselines TS (map-reduce over source text, no graph) and SS (vector RAG). — [Edge et al. HTML v2](https://arxiv.org/html/2404.16130v2)
- Win rates of GraphRAG global vs vector RAG: comprehensiveness 72–83% (podcast) and 72–80% (news), p<.001; diversity 75–82% (podcast) and 62–71% (news); empowerment mixed; vector RAG won **directness** in every comparison (used by the authors as a validity check). — [Edge et al. HTML v2](https://arxiv.org/html/2404.16130v2)
- Token economics at query time: root-level C0 summaries used >97% fewer tokens than TS (podcast ~26.7K vs ~1.01M; news ~39.8K vs ~1.71M) while keeping a 72% comprehensiveness and 62% diversity win rate vs vector RAG; C3 used 26–33% fewer tokens than TS. — [Edge et al. HTML v2](https://arxiv.org/html/2404.16130v2)
- Claim-based check: 47,075 unique claims extracted; average claims per answer C0 34.18 (news) / 32.21 (podcast) vs SS 25.23 / 26.50; LLM judgments agreed with claim-based labels 78% (comprehensiveness) and 69–70% (diversity) of non-tie cases. — [Edge et al. HTML v2](https://arxiv.org/html/2404.16130v2)
- Authors' own limits: only two ~1M-token corpora; fabrication rates not measured; empowerment mixed; claim results sensitive to the clustering threshold. — [Edge et al. HTML v2](https://arxiv.org/html/2404.16130v2)
- Community detection uses Leiden hierarchical clustering. — **recall** of the paper body; consistent with [Edge et al. HTML v2](https://arxiv.org/html/2404.16130v2) (not re-verified in today's fetch). Local search (entity-centred: start from entities matching the query, pull their relations, text units and community reports) vs global search (map-reduce over community reports) is the split in Microsoft's implementation — **recall** of the graphrag docs, not fetched.
- Cost: Microsoft's own LazyGraphRAG post says its indexing cost equals vector RAG and is **0.1% of full GraphRAG's**, because it skips up-front LLM summarisation; one LazyGraphRAG configuration matched GraphRAG global search quality at **>700× lower query cost**; a single "relevance test budget" parameter trades cost for quality. — [Microsoft Research blog, LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag/)
- Secondary dollar figures (unverified against Microsoft): one Medium post claims a single GraphRAG index cost $33,000 in early 2024 — [Medium, "The GraphRAG cost cliff"](https://medium.com/graph-praxis/the-graphrag-cost-cliff-how-33-000-became-33-in-eighteen-months-be1b0fbe37e4); a DEV post cites ~$1,544 vs ~$1.45 per million tokens (GraphRAG vs vector RAG) from the LazyGraphRAG benchmark — [DEV Community](https://dev.to/saurabh_naik_b213f3bbeafe/graphrag-vs-vector-rag-when-the-knowledge-graph-pays-for-itself-3386). Treat as indicative only.
- Independent comparison (Han et al.): RAG and GraphRAG are complementary, no consistent winner. RAG better on single-hop and detail-oriented questions (Natural Questions); GraphRAG better on multi-hop (HotPotQA, MultiHop-RAG). On MultiHop-RAG overall: plain RAG 67.02, HippoRAG2 70.27, community-GraphRAG (local) 69.01, triplets-only KG-GraphRAG 41.24; on temporal queries RAG 30.70 vs community-local 50.60. Community **global** search loses query-specific detail and "generally underperforms RAG" on their datasets; GraphRAG has higher construction cost and retrieval latency. — [Han et al. 2025, arXiv 2502.11371](https://arxiv.org/html/2502.11371v1)
- Evaluation critique: Zeng et al. show LLM-judge GraphRAG evaluations suffer position bias (a LightRAG answer judged against itself shifted >30% in win rate by order), length bias (a 25-token difference on ~200-token answers moved win rate by >50%) and trial-to-trial variance, plus "unrelated questions"; with graph-text-grounded questions and an unbiased judge, gains of three GraphRAG methods were "much more moderate than reported". — [Zeng et al. 2025, arXiv 2506.06331](https://arxiv.org/pdf/2506.06331)
- GraphRAG-Bench (ICLR 2026) starts from the observation that GraphRAG "frequently underperforms vanilla RAG on many real-world tasks" and builds a benchmark spanning fact retrieval, complex reasoning, contextual summarisation and creative generation to find when graphs help. — [Xiang et al., arXiv 2506.05690](https://arxiv.org/html/2506.05690v3); [ICLR 2026 poster](https://iclr.cc/virtual/2026/poster/10007992)

### Inferences
- **imagined:** GraphRAG's community summaries are a precomputed "what is this world about" layer. For Agora this maps to periodic digests over the log (per person, per project), not to per-turn retrieval; the evidence says such digests help corpus-wide sensemaking and hurt detail lookup, so they should sit beside, not replace, direct object lookup.
- **imagined:** The cost story favours lazy or incremental construction (LazyGraphRAG; Graphiti's incremental communities, §3) for an append-only log that changes constantly; batch re-indexing of the whole world is the wrong shape.
- Most GraphRAG wins were measured by LLM judges; given Zeng et al., any Agora trial should use grounded claims or human checks, and swap answer order.

### Gaps
- GraphRAG-Bench's actual "when to use graphs" guidelines were not retrieved (only the abstract).
- No independent replication of LazyGraphRAG's 0.1%/700× figures found.
- Exact current Microsoft documentation for local vs global search (and DRIFT search) not fetched.

## 2. HippoRAG (2024) and HippoRAG 2 (2025)

### Takeaway
HippoRAG treats an LLM-extracted open knowledge graph as a "hippocampal index" over passages and retrieves by running Personalized PageRank from query entities, giving single-step multi-hop retrieval that beat iterative retrieval at a fraction of the cost; HippoRAG 2 fixes the original's weakness on simple factual recall and is, in an independent comparison, the strongest graph method on MultiHop-RAG.

### Cited Findings
- HippoRAG (NeurIPS 2024) is inspired by hippocampal indexing theory: LLM (neocortex role) + knowledge graph + Personalized PageRank (hippocampus role). Up to **20%** better than state of the art on multi-hop QA; single-step HippoRAG matches or beats IRCoT (iterative retrieval) while **10–30× cheaper** and **6–13× faster**; adding HippoRAG inside IRCoT gives further gains. — [Gutiérrez et al., arXiv 2405.14831](https://arxiv.org/abs/2405.14831)
- Mechanism detail: offline, an LLM does open information extraction into noun-phrase nodes and relation edges, plus synonym edges from embedding similarity; online, named entities in the query are linked to KG nodes, which become the PPR reset distribution (with node-specificity weighting, an IDF-like down-weighting of common nodes); passages are ranked by the PPR mass on their nodes. — **recall** of the paper body; abstract at [arXiv 2405.14831](https://arxiv.org/abs/2405.14831) confirms only "LLM + KG + PPR".
- HippoRAG 2 ("From RAG to Memory: Non-Parametric Continual Learning for LLMs"): earlier structure-augmented RAG improves sense-making and associativity but does **worse than standard RAG on basic factual memory**; HippoRAG 2 adds deeper passage integration and more online LLM use on top of PPR, and claims to beat standard RAG on factual, sense-making and associative tasks, with a **7%** associative-memory gain over the leading embedding model. — [Gutiérrez et al., arXiv 2502.14802](https://arxiv.org/abs/2502.14802)
- Independent: on MultiHop-RAG, HippoRAG2 scored 70.27 overall vs plain RAG 67.02 and community-GraphRAG local 69.01 (Han et al.'s setup). — [Han et al. 2025](https://arxiv.org/html/2502.11371v1)
- Spreading-activation framing: SYNAPSE (Findings of ACL 2026) explicitly contrasts itself with HippoRAG's PPR and GraphRAG's community summaries. — [SYNAPSE, arXiv 2601.02744](https://arxiv.org/abs/2601.02744)

### Inferences
- **imagined:** PPR from "the things in front of me now" is a direct fit for Agora's "find what is relevant to the moment": seed the walk from the objects on screen / mentioned in the turn, run it over the world's existing reference edges (links, mentions, ownership, cards on a board), and rank. Agora already *has* typed edges authored by people and agents, so it can skip HippoRAG's most error-prone step (LLM triple extraction).
- **imagined:** HippoRAG 2's lesson — graph-only retrieval loses on plain fact recall — argues for a hybrid where passages/objects themselves are nodes alongside entities, and dense similarity is one input to the seed set.

### Gaps
- Per-dataset HippoRAG numbers (MuSiQue, 2Wiki, HotpotQA Recall@k) not re-fetched.
- No independent cost measurement of HippoRAG indexing at large scale found.

## 3. Zep / Graphiti temporal knowledge graphs

### Takeaway
Zep's Graphiti stores raw episodes, an entity/fact graph extracted from them, and a community layer, with **bitemporal** edges (when a fact was true vs when the system learned/retired it) and LLM-driven invalidation of contradicted facts; it reports small gains on DMR and 15–18.5% gains plus ~90% latency cuts on LongMemEval vs full-context, but loses on some question types, and its LoCoMo comparisons with Mem0 are disputed.

### Cited Findings
- Architecture: three subgraphs. **Episode** subgraph holds raw messages/text/JSON non-lossily, with episodic edges to referenced entities; **semantic entity** subgraph holds resolved entities and fact edges; **community** subgraph clusters strongly connected entities with summaries, found by **label propagation** (not Leiden) so new nodes can be assigned incrementally, with periodic full refreshes. — [Rasmussen et al. 2025, arXiv 2501.13956 HTML](https://arxiv.org/html/2501.13956v1)
- Bitemporal model: timeline T (event time) with `t_valid`/`t_invalid`; timeline T′ (transaction time) with `t′_created`/`t′_expired`. — [Zep HTML](https://arxiv.org/html/2501.13956v1)
- Invalidation: an LLM compares a new edge with semantically related existing edges; if they contradict and time ranges overlap, the old edge's `t_invalid` is set to the new edge's `t_valid` (old edge kept, not deleted); newer information wins on the transaction timeline. — [Zep HTML](https://arxiv.org/html/2501.13956v1)
- Entity resolution: 1024-d name embeddings + full-text search find candidates, an LLM judges duplicates and merges name/summary; extraction context is the current message plus the last 4; graph writes use **predefined Cypher**, not LLM-generated queries; fact dedup only between the same entity pair. — [Zep HTML](https://arxiv.org/html/2501.13956v1)
- Retrieval: cosine, BM25 (Lucene) and breadth-first search up to n hops over facts, entity names and community names; rerank with RRF, MMR, episode-mention frequency, node distance from a centroid node, or cross-encoder. Top-20 edges+entities for LongMemEval, top-10 for DMR. — [Zep HTML](https://arxiv.org/html/2501.13956v1)
- DMR (gpt-4-turbo): recursive summarisation 35.3%, conversation summaries 78.6%, MemGPT 93.4%, full conversation 94.4%, **Zep 94.8%**. With gpt-4o-mini: summaries 88.0%, full conversation 98.0%, Zep 98.2%. — [Zep HTML](https://arxiv.org/html/2501.13956v1)
- Zep's own critique of DMR: single-turn fact retrieval only, ambiguous questions, ~60 messages per conversation (fits in context), so high full-context scores show the benchmark is inadequate. — [Zep HTML](https://arxiv.org/html/2501.13956v1)
- LongMemEval_S: gpt-4o-mini full-context 55.4% (31.3 s, 115k tokens) vs Zep 63.8% (3.20 s, 1.6k tokens); gpt-4o full-context 60.2% (28.9 s) vs Zep 71.2% (2.58 s); i.e. +15.2% and +18.5%, ~90% latency reduction. MemGPT could not be compared (it failed to answer when history was loaded into archival memory). — [Zep HTML](https://arxiv.org/html/2501.13956v1)
- Where Zep lost to full-context: single-session-assistant (gpt-4o-mini 81.8→75.0; gpt-4o 94.6→80.4) and knowledge-update with gpt-4o-mini (76.9→74.4); authors suggest weaker models may struggle to use temporal data. — [Zep HTML](https://arxiv.org/html/2501.13956v1)
- LoCoMo dispute (secondary sources only): Mem0's paper reported Zep at 65.99%; Zep re-ran and reported 75.14% (10-run average) and argued Mem0 ran Zep search sequentially; Mem0 rebutted that Zep mis-scored the adversarial category (putting Zep at 58.44%). Accounts disagree on which side mis-handled category 5; Zep's paper itself has no LoCoMo numbers. — [personaldevblog Mem0 deep dive](https://personaldevblog.firebaseapp.com/en/blog/mem0-deep-dive-from-paper-to-production-en); [braindetox, "One product, 58 to 95 on LoCoMo"](https://braindetox.kr/en/posts/memory_benchmark_scores_reliability_2026.html); [Mem0 blog, Zep vs Mem0](https://mem0.ai/blog/zep-vs-mem0-which-ai-memory-layer-should-you-choose) (vendor).

### Inferences
- **imagined:** Graphiti is the closest published design to what Agora already is: an append-only episode log (Agora's event log) with a derived, revisable fact layer. Bitemporality maps directly: `t_valid` = when the world says it held, `t′` = the log position (e.g. event e35003). Agora gets T′ for free from the log; the open design question is whether "valid-time" belongs on edges.
- **imagined:** Invalidation-without-deletion matches Agora's "design content is never deleted: supersede it with a banner". The same rule at the fact level ("this preference was superseded by event N") is likely the main thing JEFF needs to continue correctly after a context reset — knowing what is *still* true.
- Zep's loss on single-session-assistant questions is a warning: extraction discards what the assistant itself said. For Agora, agents' own outputs need to be first-class episodes.

### Gaps
- No independent (non-vendor) replication of Zep's LongMemEval numbers found.
- Primary GitHub threads of the Zep/Mem0 LoCoMo dispute not read.
- Graphiti cost per ingested episode (LLM calls per message) not found.

## 4. A-MEM, MemGPT/Letta, Mem0 graph memory

### Takeaway
These systems differ mainly in *who* links memories: A-MEM lets an LLM write Zettelkasten-style notes and links and rewrite old notes; MemGPT/Letta lets the agent page its own memory between tiers with tool calls; Mem0 extracts and consolidates facts, with an optional graph (Mem0g) that adds only ~2% overall. Strong simple baselines (full context, a plain file) score close to or above them on current benchmarks, which are themselves weak.

### Cited Findings
- A-MEM: each new memory becomes a structured note (contextual description, keywords, tags); the system looks through history for related notes and links them "where meaningful similarities exist"; adding a memory can **update existing notes' descriptions and attributes** (memory evolution). Reports gains over SOTA baselines across six foundation models. — [Xu et al. 2025, arXiv 2502.12110](https://arxiv.org/abs/2502.12110)
- MemGPT: "virtual context management" modelled on OS virtual memory — tiers of memory with the LLM moving data between in-context and external stores, plus interrupts to manage control flow; evaluated on large-document analysis and multi-session chat. — [Packer et al. 2023, arXiv 2310.08560](https://arxiv.org/abs/2310.08560). MemGPT originated the DMR benchmark — [Zep paper](https://arxiv.org/abs/2501.13956).
- Letta (MemGPT's successor company), "Benchmarking AI Agent Memory: Is a Filesystem All You Need?" (Aug 2025): an agent that simply stores conversation history in files and searches them scores **74.0% on LoCoMo**, above specialised memory libraries. — [Letta research](https://letta-home-site.pages.dev/research/); repeated in a third-party table listing full-context 72.9%, Mem0 66.9% (gpt-4o-mini as answerer and judge) — [rovemark LoCoMo results (competitor-authored)](https://huggingface.co/datasets/rovemark/locomo-benchmark-results)
- Mem0: extract → consolidate → retrieve salient facts; Mem0g adds a graph of relations among conversation elements. On LoCoMo: 26% relative improvement over OpenAI's memory on LLM-as-judge; Mem0g ~2% higher overall than base Mem0; Mem0 has 91% lower p95 latency and >90% token savings vs full context. — [Chhikara et al. 2025, arXiv 2504.19413](https://arxiv.org/abs/2504.19413)
- LoCoMo reliability: an audit reports 6.4% of the answer key wrong and an LLM judge accepting up to 63% of deliberately wrong answers; scores vary with judge model and category slice; one product ranges 58 to 95 depending on setup. — [braindetox](https://braindetox.kr/en/posts/memory_benchmark_scores_reliability_2026.html); [lobu memory benchmarks guide](https://lobu-ai.pages.dev/guides/memory-benchmarks/) (secondary; audit primary not located). LoCoMo conversations average ~16–26k tokens, which fits in modern context windows — [braindetox](https://braindetox.kr/en/posts/memory_benchmark_scores_reliability_2026.html).
- LongMemEval (ICLR 2025): 500 questions over scalable chat histories testing five abilities — information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention; commercial assistants and long-context LLMs show a ~30% accuracy drop over sustained interactions. Design split into indexing, retrieval, reading; proposed fixes: session decomposition, **fact-augmented key expansion**, **time-aware query expansion** — all improve recall and QA. — [Wu et al., arXiv 2410.10813](https://arxiv.org/abs/2410.10813)

### Inferences
- **imagined:** For Agora, the striking result is that the *graph* in Mem0g buys ~2% and a filesystem agent matches specialised memory on LoCoMo. The graph's value is not on short chat recall; it is on temporal/knowledge-update and multi-hop questions (Zep's and Han et al.'s per-category results), which are exactly JEFF's "what changed since I last looked, and what is still true" questions.
- **imagined:** A-MEM's "evolution" (rewriting old notes when new ones arrive) conflicts with an append-only log unless rewrites are new events that supersede; that is a mechanism Agora already has.
- **imagined:** MemGPT/Letta's lesson is agency over memory — the agent decides what to page in. In Agora, lenses and verbs that let JEFF *walk* the world (Think-on-Graph style, §7) are the analogue, and are cheaper than an always-on extraction pipeline.

### Gaps
- A-MEM's specific LoCoMo numbers not retrieved (abstract has none); an often-quoted "doubles multi-hop" claim is unverified here.
- No head-to-head of these systems on a multi-agent or shared-world benchmark found.

## 5. Spreading activation and associative retrieval (Collins & Loftus 1975; ACT-R)

### Takeaway
Spreading activation — activation flowing from cue nodes along weighted links and decaying with distance and time — is the cognitive ancestor of PPR-style graph retrieval; recent LLM-memory work (SYNAPSE 2026; ACT-R-based decay) re-imports it explicitly, adding decay, inhibition and recency/frequency effects that plain vector stores cannot express. Benchmarked evidence specific to agents is thin.

### Cited Findings
- Collins & Loftus, "A spreading-activation theory of semantic processing", *Psychological Review* 82(6), 407–428 (1975): concepts as nodes in a semantic network; processing a concept spreads activation to linked concepts, attenuating with distance. — [doi:10.1037/0033-295X.82.6.407](https://doi.org/10.1037/0033-295X.82.6.407) (citation **recall**; DOI not opened today)
- ACT-R base-level activation as used in agent memory: B = ln Σ (t − t_k)^(−d), with d ≈ 0.5 (Anderson 2007), combining recency and frequency of past accesses; implementations pair it with cosine similarity (e.g. Honda et al., HAI '25: filter by activation, then rank by similarity). A vector store alone "has no notion of time or frequency" so it cannot show recency or spacing effects. The d=0.5 value comes from dense human data streams and may not fit sparse agent histories; one project measures t in interactions rather than seconds. — [pensyve-core activation.rs](https://docs.rs/crate/pensyve-core/1.2.0/source/src/activation.rs); [teaparty ACT-R memory notes](https://dlewissandy.github.io/teaparty/systems/human-proxy/act-r/memory/); [DEV: ACT-R decay policy for agent memory](https://dev.to/futhgar/eviction-without-deletion-running-an-act-r-decay-policy-for-agent-memory-36hi) (implementation notes, not peer-reviewed)
- SYNAPSE: memory as a dynamic graph of episodic nodes (raw interactions) linked to semantic concept nodes via temporal and causal edges; relevance "emerges from spreading activation rather than pre-computed links", with **lateral inhibition** and **temporal decay** to suppress distractors; "Triple Hybrid Retrieval" fuses embeddings with activation-based traversal; claims SOTA on LoCoMo temporal and multi-hop questions (abstract gives no numbers). — [Jiang et al., arXiv 2601.02744](https://arxiv.org/abs/2601.02744); [ACL Findings 2026 listing](https://preview.aclanthology.org/ingest-acl/2026.findings-acl.1108/)
- Generative Agents (Park et al. 2023): an LLM logs experiences in natural language, periodically synthesises them into higher-level reflections, and retrieves memories dynamically to plan; ablation shows observation, planning and reflection each matter for believability. — [arXiv 2304.03442](https://arxiv.org/abs/2304.03442). Its retrieval score is a weighted sum of recency (exponential decay), importance (LLM-rated) and relevance (embedding similarity) — **recall** of the paper body; not on the abstract page.

### Inferences
- **imagined:** PPR (HippoRAG), spreading activation (SYNAPSE) and ACT-R activation are the same family: a cue-seeded diffusion over links, modulated by recency/frequency. For Agora, a single "activation" reading over the world graph — seeded by what is on screen and who is speaking, decayed by log distance, boosted by access counts — would unify "what is relevant now" for every agent without per-agent pipelines.
- **imagined:** The ACT-R caveat (time measured in interactions, not seconds) matters for JEFF, who sleeps between calls: decay should run on event count or Alex's activity, not wall-clock.

### Gaps
- No benchmark directly comparing ACT-R decay, PPR and plain recency for LLM agents found.
- SYNAPSE's numbers and ablations not read (full text not fetched).

## 6. Multi-agent systems sharing a graph or blackboard

### Takeaway
Blackboard designs have been revived for LLM teams in 2025 and show measurable gains over controller-based multi-agent systems in two papers (competitive accuracy with fewer tokens; 13–57% relative end-to-end gains in data discovery); work on shared memory with access control exists, but evidence that a shared *structured* memory improves coordination in general is still narrow.

### Cited Findings
- Han & Zhang (Jul 2025): agents share a blackboard where all see each other's messages; a control unit selects agents to act based on the current board; the loop repeats to consensus. Competitive with SOTA static and dynamic multi-agent systems on commonsense, reasoning and math datasets while using fewer tokens. — [arXiv 2507.01701](https://arxiv.org/html/2507.01701v1)
- Salemi et al. (Google Cloud AI Research / UMass, 2025–26): a central agent posts requests to a blackboard; autonomous sub-agents (each covering part of a data lake, or web search) decide whether to respond, so the coordinator need not know each agent's expertise. On KramaBench and modified DSBench and DA-Code: **13–57% relative** gain in end-to-end success and up to **9% relative** gain in data-discovery F1 over the best baseline. — [arXiv 2510.01285](https://arxiv.org/abs/2510.01285v2)
- Collaborative Memory (Accenture, ICML 2025): multi-user, multi-agent memory with asymmetric, time-varying permissions encoded as bipartite graphs (users–agents–resources); private and shared tiers; each fragment carries **immutable provenance** (contributing agents, resources accessed, timestamps) so permissions can be checked retrospectively; per-agent filtered read views. A secondary summary reports up to 61% resource reduction in collaborative scenarios (unverified against the paper). — [arXiv 2505.18279](https://arxiv.org/html/2505.18279v1); [alphaXiv overview](https://alphaxiv.org/overview/2505.18279v1)

### Inferences
- **imagined:** Agora's world + Board already is a blackboard: agents post cards and notes, others respond by capability. Salemi et al.'s result supports keeping coordination *pull-based* (agents decide whether a posted request is theirs) rather than having JEFF know every worker's skills.
- **imagined:** Collaborative Memory's provenance-per-fragment and per-agent read views map onto Agora's community members' personal agents: the append-only log already gives immutable provenance; what is missing is a read-policy word that filters the graph per agent/person.

### Gaps
- I found no controlled study isolating "shared structured graph memory" vs "shared message log" for coordination quality; failure-taxonomy work on multi-agent LLM systems (e.g. MAST, Cemri et al. 2025) was not fetched.
- Classic blackboard literature (Hearsay-II, Nii 1986) not re-read.

## 7. Knowledge-graph tool use by LLMs (text-to-Cypher/SPARQL, Think-on-Graph)

### Takeaway
Letting the LLM *walk* a graph step by step (Think-on-Graph) works well without training; asking it to write full graph queries (text-to-Cypher) remains brittle on real schemas (~62% execution accuracy at best on CypherBench). Production systems like Graphiti keep writes on predefined queries.

### Cited Findings
- Think-on-Graph (ICLR 2024): the LLM acts as an agent doing iterative **beam search** over KG entities and relations, reasoning over retrieved paths; training-free, plug-and-play across LLMs and KGs; knowledge paths are traceable and correctable; small models with ToG sometimes beat GPT-4; SOTA on 6 of 9 datasets where prior leaders often needed training. — [Sun et al., arXiv 2307.07697](https://arxiv.org/abs/2307.07697)
- CypherBench (2025): text-to-Cypher over full-scale KGs; with RDF graphs transformed into domain-specific property-graph views, LLMs reach **up to 61.58% execution accuracy**. — [CypherBench via search result, arXiv 2412.12612](https://web3.arxiv.org/pdf/2412.12612)
- Neo4j's Text2Cypher dataset: 44,387 instances combined from public sets; fine-tuning improves Google-BLEU and exact match; Neo4j notes accuracy "can be lacking" due to schema-specific details. SynthCypher reports up to 40% gains for fine-tuned 7–8B models on synthetic data. — [Neo4j Text2Cypher, ACL GenAIK 2025](https://aclanthology.org/2025.genaik-1.11.pdf); [alphaXiv overview 2412.18702](https://alphaxiv.org/overview/2412.18702v2)
- Graphiti writes graph updates through predefined Cypher queries rather than LLM-generated ones. — [Zep HTML](https://arxiv.org/html/2501.13956v1)

### Inferences
- **imagined:** For Agora's small text language, the ToG pattern ("show me this thing's neighbours; pick; go") fits better than free-form query generation: each step is a small, checkable command in the desk language, and the path is a record the agent and Alex can read afterwards.
- **imagined:** If agents do write queries, a narrow, schema-aware vocabulary (Agora's kinds and bonds) is the analogue of CypherBench's "domain-specific property-graph views", which is what got accuracy to ~62%.

### Gaps
- Per-model text-to-Cypher accuracy for frontier 2026 models not found; ToG-2 results not fetched; SPARQL-specific benchmarks not covered.

## 8. Graph retrieval vs plain vector retrieval vs recency baselines

### Takeaway
Graphs help on multi-hop, temporal, knowledge-update and corpus-wide sensemaking questions; plain vector RAG wins or ties on single-hop and detail questions, at much lower cost; full-context and simple file/recency baselines are strong on today's conversational memory benchmarks, which are short enough to fit in context. Reported graph gains shrink under unbiased evaluation.

### Cited Findings
- RAG better on single-hop/detail (NQ); GraphRAG better on multi-hop (HotPotQA, MultiHop-RAG) and much better on temporal queries (30.70 vs 50.60); community-global search generally underperforms RAG on their datasets; triplets-only KG retrieval is poor (41.24). — [Han et al. 2025](https://arxiv.org/html/2502.11371v1)
- HippoRAG 2's authors state structure-augmented RAG did worse than standard RAG on basic factual memory before their fix. — [arXiv 2502.14802](https://arxiv.org/abs/2502.14802)
- Unbiased evaluation shrinks GraphRAG gains to "much more moderate". — [Zeng et al. 2025](https://arxiv.org/pdf/2506.06331)
- GraphRAG-Bench motivation: GraphRAG "frequently underperforms vanilla RAG on many real-world tasks". — [arXiv 2506.05690](https://arxiv.org/html/2506.05690v3)
- Full-context baselines: on DMR, full conversation 94.4% vs Zep 94.8% (gpt-4-turbo), 98.0% vs 98.2% (gpt-4o-mini). On LongMemEval_S (115k tokens), Zep beats full context by 8–11 points at ~1/70 the context and ~1/10 the latency, but loses on single-session-assistant. — [Zep HTML](https://arxiv.org/html/2501.13956v1)
- Filesystem baseline 74.0% on LoCoMo vs Mem0 66.9% and full-context 72.9% (competitor-compiled table). — [Letta research](https://letta-home-site.pages.dev/research/); [rovemark table](https://huggingface.co/datasets/rovemark/locomo-benchmark-results)
- Mem0g's graph adds ~2% over Mem0 overall. — [arXiv 2504.19413](https://arxiv.org/abs/2504.19413)
- LongMemEval's time-aware query expansion (a recency/time-scoping step) improves recall and QA. — [arXiv 2410.10813](https://arxiv.org/abs/2410.10813)

### Inferences
- **imagined:** The evidence favours a layered retriever for Agora: (1) exact object lookup and recency over the log first (cheap, strong); (2) dense similarity; (3) graph diffusion from current context for multi-hop/"what is connected"; (4) temporal validity filtering ("still true?"). A graph is worth it mainly for (3) and (4).
- **imagined:** Agora has an advantage none of these benchmarks test: its edges are *authored* (people and agents link things on purpose), not LLM-extracted. Most graph failures above trace to extraction noise and cost; an authored graph removes both, so Agora's results may differ from the literature in the graph's favour. What would change this view: if Agora's authored edges turn out too sparse to connect what matters, extraction is back on the table.
- **imagined:** None of these benchmarks test multi-agent, multi-writer worlds or recovery after context reset. Agora would need its own trial: e.g. reset JEFF mid-story and measure whether a graph-seeded briefing vs a recency briefing vs a full-log search gets him to the right next action.

### Gaps
- No benchmark found that evaluates memory for an agent acting in a shared, multi-writer object world; all major results are on chat histories or document QA.
- No head-to-head of graph retrieval vs a pure recency baseline (last-N events) found; recency is usually folded into scoring rather than tested alone.
