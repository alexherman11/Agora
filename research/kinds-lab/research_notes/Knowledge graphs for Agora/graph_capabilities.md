# Graph capabilities beyond tables and folders (for Agora)

*Research notes by a Claude builder subagent, 28 Oct 2026. Evidence labels follow AGENTS.md: **read** = taken from a search result or abstract I retrieved in this session (cited inline; most are search snippets or abstracts, not full texts); **recall** = from prior knowledge, not re-verified this session; **imagined** = design inference for Agora. Seventeen searches were run, and no full PDFs were fetched, so every number below came from an abstract or a secondary summary. Where a number came from a third-party summary, that is flagged.*

Framing source for the whole catalogue: Hogan et al., "Knowledge Graphs", ACM Computing Surveys 54(4), 2021. It covers graph data models, query and validation languages, and "deductive and inductive techniques" for representing and extracting knowledge — [arXiv 2003.02320](https://arxiv.org/abs/2003.02320v6). Its split into deductive capabilities (rules, ontologies, validation) and inductive ones (analytics, embeddings, GNNs, rule mining) is used below.

---

## 1. Discovery and navigation (faceted browsing, follow-your-nose, graph exploration UIs)

### Takeaway
Faceted browsing over typed properties has strong, repeated user-preference evidence. Raw node-link "graph views" have measured readability limits at quite small sizes: around 50 nodes when dense and 100 when sparse. For Agora, the graph should drive facets, neighbourhood lists and paths. A whole-world hairball view should not be the main way in.

### Cited Findings
- **Flamenco (hierarchical faceted metadata + query previews), CHI 2003.** 32 art-history students used a collection of 35,000 fine-art images, compared against a standard image-search baseline. 90% preferred the faceted interface overall, 97% said it helped them learn about the collection, 75% found it more flexible, and 72% found it easier to use — [Yee, Swearingen, Li, Hearst, CHI '03 (PDF)](https://courses.cs.washington.edu/courses/cse454/13wi/papers/yee-chi03.pdf); [Hearst seminar abstract](https://hci.stanford.edu/seminar/abstracts/02-03/030131-hearst.html). (read: abstract-level figures)
  - How it works: each item carries values in several orthogonal, optionally hierarchical facets. Each facet value shows a count preview of how many items remain if selected. Keyword search and browsing are integrated — [same](https://hci.stanford.edu/seminar/abstracts/02-03/030131-hearst.html).
- **Exhibit (end-user structured-data publishing with facets).** A full-lifecycle study combined interviews with analysis of more than 1,800 published visualisations and 200,000 web interactions. It is evidence that non-programmers do publish and browse structured data through faceted views — [Benson & Karger, "End-Users Publishing Structured Information on the Web"](https://core.ac.uk/download/4406802.pdf). (read: abstract only; effect sizes not retrieved)
- **Follow-your-nose / RDF browsers (Tabulator etc.).** A 2015 ICWE paper calls such browsers "very low-level" for real tasks such as product search. It also says SPARQL-style query formulation lacks mediation between the data's conceptual model and users' mental models — [ICWE 2015, Springer](https://rd.springer.com/content/pdf/10.1007/978-3-319-19890-3_27.pdf). (read: snippet)
- **Parallel faceted browsing** generalises facets across linked types (pivoting from one set to a related set). Two user studies on semantic data are reported in Jameson et al. 2013 — [abstract](https://media.contaction.li/homepage-2017/abs/JamesonSS+13.html). (read: existence only, not results)
- **Faceted-browsing usability literature review** (library catalogues): [Fagan 2010, ITAL](https://ejournals.bc.edu/index.php/ital/article/view/3144). (read: existence only)
- **Hairball evidence.** A controlled study had participants find shortest paths in node-link diagrams of 25–175 nodes, measuring accuracy, time, EEG, pupil dilation and heart-rate variability. Participants had significant difficulty above ~50 nodes in high-density diagrams and above ~100 nodes even in low-density ones. Cognitive load rose and then *fell* at the hardest levels, which the authors read as participants giving up — [Yoghourdjian et al., IEEE TVCG / InfoVis 2020, arXiv 2008.07944](https://arxiv.org/pdf/2008.07944). (read: abstract)
- **Knowledge-graph practitioners** use node-link diagrams for sanity checks but name scalability as their biggest problem — [Li et al., "Knowledge Graphs in Practice", arXiv 2304.01311](https://arxiv.org/pdf/2304.01311). (read: snippet)
- **Motif simplification.** Fan, connector and clique glyphs replace repeated sub-structures to cut clutter (Dunne & Shneiderman, CHI 2013, implemented in NodeXL) — [Perceptual Edge summary (secondary)](https://www.perceptualedge.com/blog/?p=1636).

### Inferences
- (imagined) Facets cost little in a graph whose things have kinds and open aspects. Each aspect key is a facet, each kind is a top-level facet, and each relation type is a "pivot" facet (parallel faceted browsing). Count previews need only per-value counts, which an incremental index can keep current from the append-only log.
- (imagined) Ego-centred views should be the default: one thing, its 1-hop neighbourhood grouped by relation type, then paths on demand. Global graph views should be kept to ≤50 visible nodes, or collapsed by community (Section 6) or motif glyphs. This matches the Yoghourdjian thresholds and the desk's existing preference for lenses over maps.
- (imagined) Facets help most when properties are consistently filled. Agora's open aspects risk sparse, inconsistent keys. That is where schema induction (Section 6) and SHACL-like shapes (Section 5) earn their place.
- Failure modes: facet explosion when every open aspect becomes a facet; empty or sparse facets; hairballs; follow-your-nose browsing that loses users with no breadcrumb or "how I got here" trail.

### Gaps
- I did not retrieve task-time or accuracy effect sizes for Exhibit, Tabulator, or parallel faceted browsing; only their existence and framing were confirmed.
- No head-to-head study of "graph view vs list/facet view" for personal knowledge tools (Roam/Obsidian-style graph views) was found.

---

## 2. Recommendation from graphs (random walks, Pixie, PinSage, personalised PageRank vs collaborative filtering)

### Takeaway
Random walks on a bipartite user–item (or thing–context) graph are proven in production at Pinterest scale. They are also among the simple methods that match or beat many neural recommenders in careful reproductions. At small scale, a few thousand short walks with restarts from a person's own recent things (personalised PageRank, Pixie style) is cheap, explainable, and competitive. GNNs (PinSage) add value mainly at web scale, where content features and rich training data exist.

### Cited Findings
- **Pixie (Pinterest).** A real-time random-walk-with-restart system on a pin–board bipartite graph of ~3 billion nodes and 17 billion edges. Reported results:
  - up to 50% higher user engagement than the previous Hadoop-based production system;
  - one server answers 1,200 requests per second at 60 ms latency;
  - Pixie-backed systems account for over 80% of all engagement on Pinterest;
  - graph pruning gave an additional 58% quality improvement while shrinking the graph 6×;
  - early stopping gives almost the same results as a long walk in about half the steps;
  - Top-10 hit rate of 6.3% vs 2.1% for combined content-based methods (this figure is from a third-party summary).
  
  Sources: [Eksombatchai et al., WWW 2018, arXiv 1711.07601](https://arxiv.org/pdf/1711.07601.pdf); [The Morning Paper summary](https://blog.acolyer.org/2018/05/23/pixie-a-system-for-recommending-3-billion-items-to-200-million-users-in-real-time/); [Liner review (secondary)](https://liner.com/review/pixie-system-for-recommending-3-billion-items-to-200-million). (read: abstract and summaries)
  - How it works (recall, consistent with the abstract): start walks at the query pins, alternate pin→board→pin, count visits, and stop early once enough pins pass a visit threshold. Visit counts from several query pins are combined with a boost for items reached from many queries. A per-user bias steers walks toward the user's language or topic.
- **PinSage (Pinterest/Stanford, KDD 2018).** A GCN that "combines efficient random walks and graph convolutions" to embed pins, trained on 7.5 billion examples over a graph of 3 billion nodes and 18 billion edges. The paper says offline metrics, user studies and A/B tests all show better recommendations than comparable deep-learning and graph-based alternatives — [Ying et al., arXiv 1806.01973](https://arxiv.org/pdf/1806.01973). A third-party review reports +150% hit rate and +60% MRR over the best baseline offline — [Liner review (secondary, unverified)](https://liner.com/review/graph-convolutional-neural-networks-for-webscale-recommender-systems). The exact A/B numbers were not retrieved.
- **Simple methods remain competitive.** A RecSys 2019 reproduction of 18 neural recommenders from top venues:
  - only 7 of 18 could be reproduced;
  - "most of the reviewed works can be outperformed at least on some datasets by conceptually and computationally simpler algorithms" (item-kNN, PureSVD, SLIM; the paper's baseline set also includes graph random-walk methods P3α/RP3β, per recall);
  - PureSVD clearly beat Neural Collaborative Filtering on MovieLens-1M.
  
  Source: [Ferrari Dacrema, Cremonesi, Jannach, arXiv 1907.06902](https://arxiv.org/pdf/1907.06902). (read: abstract and summaries)

### Inferences
- (recall) Personalised PageRank (PPR) is PageRank whose teleport always returns to a seed set, such as a person's own or recently touched things. It is what Pixie approximates by Monte-Carlo walks. RP3β is a 3-step walk user→item→user→item with item popularity penalised by degree^β, which damps the "everyone gets the popular thing" failure.
- (imagined) What makes it work at small scale:
  1. a bipartite structure with "context" nodes: tags, places on the community map, conversations, boards, people;
  2. degree penalties so hubs such as a busy board or a famous person don't dominate;
  3. pruning of very high-degree context nodes, the analogue of Pixie's 58% gain from pruning;
  4. a few thousand steps per query, which takes milliseconds in Python at 10⁴–10⁵ nodes;
  5. the walk itself is the explanation (Section 7).
- (imagined) Collaborative filtering (matrix factorisation) needs many users with overlapping behaviour. A community of ~200 people (see the Seabright memory) is a cold-start regime, where graph walks that also use content and structural edges (author, place, kind, topic) beat pure user–item collaborative filtering.
- Failure modes:
  - popularity bias, if degree is not penalised;
  - filter bubbles, if walks always restart at the same recent seeds;
  - pruning or early-stopping thresholds tuned for Pinterest scale and wrong for tiny graphs;
  - privacy, because a walk across people's private things can leak them, so walks must respect access per edge.

### Gaps
- PinSage's online A/B effect sizes were not retrieved (only "better than alternatives").
- No published deployment of random-walk recommenders at community scale (10²–10³ users) with effect sizes was found.

---

## 3. Link prediction (common neighbours, Adamic–Adar, Jaccard, Katz, node2vec, GNNs)

### Takeaway
Topology alone predicts future links well above chance. Cheap neighbourhood heuristics, Adamic–Adar especially, plus Katz, have been strong since 2003. A NeurIPS 2023 benchmark found that GNN link-prediction gains were partly evaluation artefacts. For Agora, AA/Jaccard/CN on 2-hop neighbourhoods give "you might link this to…" suggestions that are nearly free and explainable.

### Cited Findings
- **Liben-Nowell & Kleinberg (CIKM 2003; JASIST 58(7) 2007).** On co-authorship networks, "information about future interactions can be extracted from network topology alone", and "fairly subtle measures for detecting node proximity can outperform more direct measures" — [paper PDF](https://people.csail.mit.edu/dln/papers/link/paper.pdf). A secondary review reports Adamic/Adar at 54.4× random on cond-mat and 16.8× on astro-ph. The same review says Katz and its variants "consistently perform strongly" — [Liner review (secondary; verify against tables)](https://liner.com/review/link-prediction-problem-for-social-networks).
- **GNN link-prediction evaluation pitfalls (NeurIPS 2023 D&B).** The paper names three problems:
  - underreported baseline performance;
  - no unified data splits or metrics;
  - negatives that are too easy to reject.
  
  The authors re-ran methods under matched hyperparameter search and proposed HeaRT, which builds hard negatives *from heuristics*. Benchmarks with easy random negatives overstate gains — [Li et al., arXiv 2306.10453](https://arxiv.org/abs/2306.10453v1); [NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2023/hash/0be50b4590f1c5fdf4c8feddd63c4f67-Abstract.html). (read: abstract; exact heuristic-vs-GNN tables not retrieved)

### Inferences
- (recall) Formulas, all over neighbour sets Γ(x):
  - common neighbours: |Γ(x)∩Γ(y)|;
  - Jaccard: CN / |Γ(x)∪Γ(y)|;
  - Adamic–Adar: Σ over shared neighbours z of 1/log|Γ(z)|, so rare shared neighbours count more;
  - Katz: Σ_ℓ β^ℓ · (number of paths of length ℓ);
  - node2vec: biased random walks fed to skip-gram, giving embeddings scored by dot product.
- (recall) CN, AA and Jaccard need only 2-hop adjacency, and they explain themselves: "both linked to X and Y". Katz is truncated to length 3–4 in practice.
- (imagined) Agora uses: suggesting relations, duplicate candidates (Section 4), "people who touched this also…", and filling missing aspects. Agents can propose links; a human or the owning agent accepts them. Suggestions should be written as *proposals* in the log, never as asserted edges.
- Failure modes:
  - hub-driven false positives (AA's log-degree damping helps);
  - temporal leakage when evaluating;
  - self-reinforcing loops when accepted suggestions become the evidence for more suggestions;
  - embeddings that drift whenever the graph changes and must be recomputed, unlike the incremental heuristics.

### Gaps
- Exact figures for how often heuristics match GNNs under HeaRT were not retrieved. The abstract confirms the pitfalls, not the leaderboard.
- No small-graph (10³–10⁵ node) comparison of node2vec vs AA was retrieved.

---

## 4. Entity resolution / deduplication (deciding two things are the same; human-in-the-loop merging)

### Takeaway
The proven pattern has three parts. First, blocking or filtering makes comparison sub-quadratic. Second, a pairwise match score uses Fellegi–Sunter-style two thresholds: confident match, confident non-match, and a middle band sent to human (clerical) review. Third, active learning picks which uncertain pairs to show people. In graphs, identity assertions are dangerous: owl:sameAs is often misused, and errors propagate through inference.

### Cited Findings
- **Blocking and filtering survey.** ER is inherently quadratic. Blocking limits comparisons to likely matches, filtering quickly finds pairs above a similarity threshold, and hybrids exist — [Papadakis, Skoutas, Thanos, Palpanas, ACM CSUR 53(2) 2020, arXiv 1905.06167](https://arxiv.org/abs/1905.06167v3). (read: abstract)
- **Fellegi–Sunter with clerical review.** An upper threshold auto-matches, a lower one auto-rejects, and pairs in between go to human review. Optimised parameters cut review volume by at least 3× in one ISI paper — [ISI paper](https://isi-web.org/sites/default/files/import/files-2011/450070.pdf). Fellegi–Sunter gives an optimal theoretical classification rule and can estimate parameters without training data — [Winkler overview, via search](https://www.academia.edu/34177542/Data_Cleaning_Methods). (read: snippets)
- **Active learning** prompts users to label the most informative pairs to minimise review cost (medical record linkage, 2012) — [fitforthem record-linkage listing](https://fitforthem.unipa.it/subject:Record%20linkage). The oagdedupe project frames matching as binary classification over candidate pairs and plugs Label Studio in for human review — [oagdedupe docs](https://oagdedupe.readthedocs.io/en/latest/userguide/intro.html).
- **Human labels are noisy.** Updates must not assume an error-free oracle — [Multi-layer PPRL with clerical review, arXiv 2412.04178](https://arxiv.org/pdf/2412.04178).
- **Identity in graphs goes wrong.** owl:sameAs encodes one point on a similarity scale that "is often too strong for many of its current uses". The authors propose weaker or contextual alternatives — [Halpin, Hayes, McCusker, McGuinness, Thompson, ISWC 2010](https://link.springer.com/doi/10.1007/978-3-642-17746-0_20). A secondary slide deck attributes to it a figure of 37% of 250 sampled sameAs links between books being incorrect. The same deck notes that bad sameAs links between DBpedia and DBLP misassigned publications to the wrong authors — [KG completion slides (secondary; figure unverified)](https://www.lri.fr/~sais/KGC/4-IdentityProblem.pdf).

### Inferences
- (imagined) In an append-only log, a merge should be an **event that can be reversed**: "A same-as B, by whom, with what evidence". It should not destroy records. A view resolves the cluster to one canonical thing, and an unmerge is another event. This avoids the sameAs disaster because identity stays scoped, attributed and reversible.
- (imagined) Weaker relations should sit alongside identity ("similar to", "same place as", "same person in context X"), following Halpin et al.'s similarity scale. Unlike owl:sameAs, these should **not** let rules copy every property across.
- (imagined) Pipeline sized for Agora:
  1. block on normalised name/title tokens, place cells and kind;
  2. score with string similarity plus graph evidence (shared neighbours, from Section 3);
  3. auto-merge nothing at first;
  4. put the uncertain middle band into a "Needs Me" style review queue, so the person or agent chooses.
- Failure modes:
  - transitive closure chains wrong merges (A≈B≈C even though A≠C);
  - merges that copy private properties across owners;
  - review fatigue;
  - over-blocking that hides true matches.

### Gaps
- dedupe.io's own documentation was not retrieved.
- I found no study of user-facing merge UIs (OpenRefine, Wikidata merges) with effect sizes.

---

## 5. Inference and rules (RDFS/OWL, Datalog, SHACL)

### Takeaway
Two different jobs are often confused. *Deduction* (OWL/RDFS/Datalog: derive new facts) assumes an open world. *Validation* (SHACL: check data against shapes) treats the data as complete. Validation matches what users expect from "kinds". Unrestricted OWL inference amplifies errors, sameAs being the classic case. Datalog-style rules that derive facts with provenance are the practical middle ground.

### Cited Findings
- OWL is designed for inferring facts from incomplete data under the open-world assumption. SHACL treats the data as complete and validates under the closed-world assumption — [Ahmetaj et al., arXiv 2108.06096](https://www.arxiv.org/pdf/2108.06096v2). A refinement: SHACL is closed with respect to relations but open on the domain — [same group, arXiv 2507.12286](https://arxiv.org/pdf/2507.12286v1).
- OWL's standard task is deduction, while SHACL's is validation, a form of model checking. The W3C SHACL spec anticipates validation under OWL entailment but gives no guidance on how to do it. Research proposes rewriting validation-with-ontology into plain validation (Horn-ALCHIQ) — [arXiv 2507.12286](https://arxiv.org/pdf/2507.12286v1).
- SHACL's closed-world stance matches business users' expectations, and shapes can be added incrementally to an existing RDFS/OWL model — [TopQuadrant](https://archive.topquadrant.com/?p=7325). (vendor view)
- Inference propagating bad identity links: see Section 4 (sameAs misuse leading to misattributed publications) — [Halpin et al. 2010](https://link.springer.com/doi/10.1007/978-3-642-17746-0_20); [slides](https://www.lri.fr/~sais/KGC/4-IdentityProblem.pdf).
- Hogan et al. survey deductive knowledge (ontologies, entailment, rules) and validation languages as core KG capabilities — [arXiv 2003.02320](https://arxiv.org/abs/2003.02320v6).

### Inferences
- (recall) Datalog: rules of the form `head :- body` over relations, evaluated bottom-up to a fixpoint. With stratified negation it always terminates, and it supports recursion such as transitive closure ("ancestor", "reachable", "in this place or any sub-place"). Semi-naive evaluation and incremental maintenance (DRed, differential dataflow) keep derived facts current as base facts are added. That fits an append-only log well.
- (imagined) Where inference helps Agora:
  - transitive containment (place ⊂ neighbourhood ⊂ town);
  - inverse relations (if A "member of" B, B "has member" A);
  - kind inheritance (a "shift" is an "event");
  - derived membership in views ("my open items").
  
  Where it hurts:
  - symmetric or transitive rules over noisy, user-entered edges;
  - identity rules that copy properties;
  - rules authored by many agents that interact unexpectedly.
- (imagined) Kinds in Agora should behave like **SHACL shapes over open aspects**: a kind *describes and checks* without forbidding extra aspects, and validation reports are advisory ("this event has no time"), not refusals. This keeps the "open aspects" property while giving facets and lenses something to rely on.
- (imagined) Every derived fact should carry its rule and supporting facts (provenance). Path explanations (Section 7) and retraction when a base fact is superseded both need this.
- Failure modes:
  - inference blow-up (transitive closure of hub relations);
  - silent wrong conclusions from bad base facts;
  - open- vs closed-world confusion ("no deadline" meaning unknown vs none);
  - rule conflicts between agents;
  - unclear performance when many rules fire on each log append.

### Gaps
- The W3C SHACL Recommendation and Datalog engine documentation (Soufflé, differential dataflow, RDFox) were not fetched this session; their mechanics above are recall.
- I found no empirical study measuring how often OWL inference causes user-visible errors in deployed KGs, beyond the sameAs analyses.

---

## 6. Community detection, clustering and emergent categories (Louvain, Leiden, FCA, schema induction)

### Takeaway
Modularity clustering finds groups and topics in the link structure. Use Leiden rather than Louvain: Louvain produced badly connected communities up to 25% of the time and disconnected ones up to 16%. To "pave the cowpaths" into kinds, FCA over each thing's set of aspect keys yields a lattice of candidate types, and frequency or co-occurrence methods induce taxonomies at scale. Both work best as *suggestions* a person names and accepts.

### Cited Findings
- **Louvain → Leiden.** In experiments, Louvain produced badly connected communities up to 25% of the time and disconnected communities up to 16%. The defect is worst when Louvain is run iteratively. Leiden is proven to guarantee connected communities and is faster — [Traag, Waltman, van Eck, Sci. Rep. 2019, arXiv 1810.08473](https://arxiv.org/pdf/1810.08473); [Leiden repository version](https://scholarlypublications.universiteitleiden.nl/access/item%3A2979698/view). (read: abstract/snippet; the speed claim is recall)
- **FCA.** From a binary object×attribute table, FCA computes the formal concepts: maximal pairs of an object set and its shared attribute set. Ordered by inclusion, the concepts form a complete lattice drawn as a DAG. The number of concepts can grow exponentially with context size — [TU Dresden, "Modelling Dynamics in Semantic Web KGs with FCA"](https://iccl.inf.tu-dresden.de/web/Modelling_Dynamics_in_Semantic_Web_Knowledge_Graphs_with_Formal_Concept_Analysis).
- **FCA-inspired data-driven schema for KGs.** The method takes each entity's *property set* and builds a lattice from set containment. It was applied to successive Wikidata versions to model schema change over time — [same](https://iccl.inf.tu-dresden.de/web/Inproceedings3195); [CEUR Vol-2123 paper 18](https://ceurspt.wikidata.dbis.rwth-aachen.de/Vol-2123/paper18.cermine).
- **Taxonomy induction from type co-occurrence.** A "simple method" induces class taxonomies from type-assertion frequencies and co-occurrences with no external data. It reportedly beats tag-hierarchy induction baselines and scales to large KGs — [Semantic Web Journal / ESWC 2020](https://www.semantic-web-journal.net/content/simple-method-inducing-class-taxonomies-knowledge-graphs).
- Hogan et al. include graph analytics (centrality, community detection) and schema/rule mining among the inductive capabilities of KGs — [arXiv 2003.02320](https://arxiv.org/abs/2003.02320v6).

### Inferences
- (imagined) For Agora's open aspects, the "property-set lattice" is the native cowpath detector. Count the distinct aspect-key sets things actually carry. Any large group of things sharing ≥k keys and no declared kind becomes a candidate kind ("38 things all have `when`, `where`, `who` → an 'event' kind?"). The person names it, and the new kind's shape (Section 5) is the shared keys. To avoid the exponential blow-up, use iceberg lattices: only concepts with support above a minimum.
- (imagined) Leiden over the co-reference graph (things linked by mentions, shared people, shared places) gives emergent *groups*: topics, project clusters, neighbourhood circles on the community map. It also folds hairballs into community super-nodes (Section 1). Communities change as the graph changes. Present them as named, dated snapshots, not as stable identities. Leiden also has a resolution parameter that changes the answer.
- Failure modes:
  - modularity's resolution limit, which merges small real groups;
  - non-determinism between runs;
  - clusters that people can't name;
  - emergent kinds that encode one agent's habits rather than shared meaning;
  - lattices too large to show.

### Gaps
- Leiden's speed-up numbers and its quality on small (<10⁴ node) graphs were not retrieved.
- No user study of FCA- or induction-derived types being accepted by end users was found.

---

## 7. Explanation (path-based explanations; effect on trust)

### Takeaway
Explanations reliably increase acceptance and persuasion. Their effect on *trust* and *satisfaction* is mixed across studies, and explanation aims can conflict. Graph recommendations get explanations almost for free: the path or shared neighbours that produced a suggestion *is* a faithful justification. That is stronger than post-hoc explanations of embedding or GNN scores.

### Cited Findings
- **Herlocker, Konstan, Riedl (CSCW 2000).** They tested explanation interfaces for collaborative filtering and found that some explanation styles increased users' acceptance of recommendations — [dblp record](https://dblp.uni-trier.de/rec/conf/cscw/HerlockerKR00.html); [paper](https://typeset.io/pdf/explaining-collaborative-filtering-recommendations-17bchfs9p8.pdf). A later paper notes that they could not show any explanation style increased users' satisfaction with the items chosen — [Bilgic & Mooney, "Explaining Recommendations: Satisfaction vs. Promotion"](https://typeset.io/pdf/explaining-recommendations-satisfaction-vs-promotion-2d2ihbomvq.pdf). (read: abstracts/snippets; the histogram-of-neighbours result is recall: it was the most persuasive of 21 interfaces)
- **Seven explanation aims.** Tintarev & Masthoff list effectiveness, satisfaction, transparency, scrutability, trust, persuasiveness and efficiency. The aims can conflict, so evaluations must name the aim they target — [Tintarev & Masthoff, UMUAI 2012 (core.ac.uk)](https://core.ac.uk/download/177333.pdf). In their movie study, personalised feature-based explanations were rated highest but did not beat non-personalised ones on effectiveness — [same](https://core.ac.uk/download/177333.pdf).
- **Mixed trust effects.** A meta-analysis of 97 XAI user studies finds that explanations generally improve subjective understanding, but effects on trust and usability are inconsistent. A survey of 124 recommender-explanation user studies notes that the populations studied are narrow — [arXiv 2509.18980 (summary of those works)](https://arxiv.org/html/2509.18980v1); [arXiv 2412.14193](https://arxiv.org/html/2412.14193v2).
- **Justification vs transparency** in a scientific-literature recommender with visual explanations: [arXiv 2305.17034](https://ar5iv.labs.arxiv.org/html/2305.17034). (read: title only)

### Inferences
- (imagined) In Agora every suggestion should carry its *derivation*:
  - the walk's most-visited intermediate nodes ("because you were at the river clean-up and Sam's board");
  - the shared neighbours behind a link proposal;
  - the rule and facts behind an inferred fact.
  
  These are faithful, unlike post-hoc rationales. Scrutability follows: the person can strike out a bad intermediate ("not because of Sam") and the system can re-rank.
- (imagined) Aim for *effectiveness and scrutability* (helping people decide well and correct the model) rather than persuasiveness. The Herlocker and Bilgic & Mooney results show persuasive explanations can raise acceptance without raising satisfaction.
- Failure modes: long paths that feel arbitrary; leaking private intermediates ("because of X's private note"); explanation overload; persuasive framing that manipulates.

### Gaps
- I did not retrieve a controlled user study specifically on *path-based knowledge-graph* explanations and trust (KPRN, PGPR and similar report offline metrics; user studies are scarce). This is an open evidence gap.

---

## 8. Graph queries people and agents use (paths, neighbourhoods, patterns, "how is A connected to B")

### Takeaway
Four query shapes cover most needs:
1. neighbourhood ("everything about X, grouped by relation");
2. pattern matching (Cypher/SPARQL basic graph patterns, Datalog joins);
3. path / reachability (property paths, variable-length matches, recursive Datalog);
4. connection discovery ("shortest or k-shortest paths between A and B").

Raw query languages are too hard for end users. Agents can write them, and people need lenses, facets and "how are these connected" buttons on top.

### Cited Findings
- Hogan et al. cover graph query languages (graph patterns, navigational/path queries, and their combination) and validation languages as core KG machinery — [arXiv 2003.02320](https://arxiv.org/abs/2003.02320v6). (read: abstract)
- SPARQL-style query formulation "is generally very complex and lacks mediation" between data models and users' mental models — [ICWE 2015](https://rd.springer.com/content/pdf/10.1007/978-3-319-19890-3_27.pdf).
- Humans find shortest paths visually in node-link diagrams poorly beyond ~50–100 nodes — [Yoghourdjian et al. 2020](https://arxiv.org/pdf/2008.07944). This argues for computing "how is A connected to B" and showing the few resulting paths, not the graph.

### Inferences
- (recall) Cypher: `MATCH (a)-[:REL*1..3]->(b)` for variable-length patterns; SPARQL 1.1 property paths `?a :rel+ ?b`; Datalog: recursive rules. All three express pattern plus reachability. Cypher/GQL (ISO GQL, 2024) and SPARQL also return paths. Datalog returns derived facts, but can record provenance.
- (imagined) For Agora's text language, the cheapest high-value words are:
  - `near X` (1–2 hop neighbourhood grouped by relation);
  - `path A B` (bidirectional BFS, top-k short paths, skipping hub nodes or penalising them by degree, like AA's damping, so paths go through meaningful rather than generic nodes);
  - `where` patterns over kinds and aspects (facets as queries);
  - named recursive relations ("within", "part of").
- Failure modes:
  - paths through hubs ("both are things", "both belong to Alex") that are true and useless;
  - path explosion in dense neighbourhoods;
  - queries that cross privacy boundaries;
  - agent-written queries that are correct but unreadable to people. Every query an agent runs on someone's behalf should have a readable rendering.

### Gaps
- I found no usability study comparing Cypher and SPARQL for end users or agents. LLM text-to-Cypher/SPARQL accuracy benchmarks were not searched.

---

## 9. Small-scale graph performance (thousands to hundreds of thousands of nodes on one machine)

### Takeaway
At Agora's scale (10³–10⁵ things, 10⁴–10⁶ edges), everything in this catalogue except GNN training and full-lattice FCA runs comfortably in memory on one machine with plain adjacency dicts/arrays. The engineering problem is *incremental maintenance from the log*, not raw speed. I verified none of this by measurement this session.

### Cited Findings
- Pixie serves random-walk recommendations at 60 ms latency on 1,200 requests per second per server for a 3-billion-node graph held in memory on one machine. Early stopping halves walk length with almost no quality loss — [arXiv 1711.07601](https://arxiv.org/pdf/1711.07601.pdf); [Morning Paper](https://blog.acolyer.org/2018/05/23/pixie-a-system-for-recommending-3-billion-items-to-200-million-users-in-real-time/). By extension, walks on a graph 10⁴× smaller are trivially cheap (inference, not measured).
- ER's cost is quadratic without blocking. Blocking and filtering are the established cure — [Papadakis et al. 2020](https://arxiv.org/abs/1905.06167v3).
- The number of FCA concepts can grow exponentially with context size — [TU Dresden](https://iccl.inf.tu-dresden.de/web/Modelling_Dynamics_in_Semantic_Web_Knowledge_Graphs_with_Formal_Concept_Analysis).

### Inferences
- (recall/imagined, *not run*) Rough costs at 10⁵ nodes and 10⁶ edges:
  - adjacency in Python dicts: ~100s of MB at most;
  - 1–2 hop neighbourhood: microseconds to milliseconds;
  - BFS shortest path: milliseconds;
  - PPR by Monte-Carlo walks (~10⁴ steps): ~10 ms in pure Python;
  - global PageRank: about a second with NumPy/SciPy sparse;
  - AA/CN for one node: proportional to the sum of its neighbours' degrees (fast unless hubs, which is why hubs get pruned);
  - Leiden via igraph/leidenalg: seconds.
  
  All of these are recall-based estimates. They should be **run** on a synthetic Agora-shaped graph before anyone relies on them.
- (imagined) Incremental pattern from an append-only log:
  1. maintain the adjacency and facet-count indexes on each event;
  2. recompute cheap local scores (AA, PPR) on demand;
  3. recompute global analytics (communities, PageRank, kind induction) on a slow cadence or when asked, stamped with the log position they reflect;
  4. use Datalog with semi-naive or differential evaluation for derived facts, so an append touches only affected rules.
- Failure modes:
  - hub nodes (a person who touches everything) making "local" queries global;
  - recomputing global analytics on every event;
  - unbounded transitive closure;
  - memory growth if superseded versions stay in the live adjacency rather than only in the log.

### Gaps
- No benchmarks were run. No source was retrieved for networkx/igraph/Kùzu/DuckDB-graph timings at this scale. A small `ran` benchmark in `research/kinds-lab/` would close this.

---

## Cross-cutting notes for the report writer (imagined unless cited)

- **What changes my mind:**
  - a study showing whole-graph views help users at 100–1,000 nodes would weaken the "ego views, not hairballs" recommendation;
  - evidence that GNN or embedding recommenders beat PPR/RP3β at community scale (10²–10³ users) would weaken the "random walks first" recommendation.
- **Common thread.** Every capability works best as a *proposal with a reason*: suggested link, suggested merge, suggested kind, suggested item, inferred fact. Each is recorded in the log with its derivation, reversible, and accepted by a person or the owning agent. This matches the evidence on sameAs damage, explanation aims, and noisy human labels, and it fits an append-only, multi-agent world.
- **Highest value per cost at Agora's scale:**
  1. facets from kinds and aspects;
  2. ego-neighbourhood plus "how are A and B connected" path queries;
  3. Adamic–Adar link and merge suggestions;
  4. personalised-PageRank recommendations with path explanations;
  5. SHACL-like advisory shapes for kinds;
  6. property-set lattice for emergent kinds;
  7. Leiden for groups, on demand.
  
  GNNs, node2vec and full OWL reasoning are the lowest priority at this scale.
