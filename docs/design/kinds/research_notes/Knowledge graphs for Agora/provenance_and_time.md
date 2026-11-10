# Provenance, Time and Information Flow: mechanisms for Agora's record log

*Research notes by a Claude builder, 28 Oct 2026. Every claim below is **read**: from the cited page as fetched today. Several pages were long and were read only in part (noted where it matters). Lines marked "Inference" are **imagined**: my reasoning about Agora, not something a source says.*

Agora's starting point, for reference: an append-only log of records, each holding who acted, for whom, which verb, which things, facts as `[thing, aspect, hash before, value]`, what the actor saw, and what caused it. That record already contains most of what the systems below had to add separately.

## 1. W3C PROV: entities, activities, agents and their relations

### Takeaway
PROV is a small, stable vocabulary of three node types and about seven core edges. Agora's records map onto it almost one to one. A record is an Activity, the things it changed become new Entity versions, and the actor and principal are Agents linked by `actedOnBehalfOf`. Its most useful extra ideas are *bundles* (provenance about provenance) and *qualified relations* (an edge that carries a role or plan).

### Cited Findings
- Core classes: an Entity is "a physical, digital, conceptual, or other kind of thing with some fixed aspects"; an Activity is "something that occurs over a period of time and acts upon or with entities"; an Agent is "something that bears some form of responsibility for an activity taking place." — [W3C PROV-O](https://www.w3.org/TR/prov-o/)
- Starting-point properties — [W3C PROV-O](https://www.w3.org/TR/prov-o/):
  - `wasGeneratedBy` (Entity→Activity) is when an activity finishes producing an entity.
  - `used` (Activity→Entity) is when an activity starts using an entity.
  - `wasDerivedFrom` (Entity→Entity) has the subproperties `wasRevisionOf`, `wasQuotedFrom` and `hadPrimarySource`.
  - `wasAttributedTo` (Entity→Agent) and `wasAssociatedWith` (Activity→Agent), which may name a plan.
  - `actedOnBehalfOf` (Agent→Agent) records "accountability of an agent towards another agent."
  - `wasInformedBy` (Activity→Activity) links two activities through an unnamed entity.
  - `startedAtTime` and `endedAtTime` bound an activity.
- PROV versions things rather than mutating them. Entities have "fixed aspects", and `generatedAtTime`/`invalidatedAtTime` bound an entity's existence. `specializationOf` links a specific entity to a general one, for example today's news page to "the news page". `alternateOf` links entities that present "aspects of the same thing". — [W3C PROV-O](https://www.w3.org/TR/prov-o/)
- Qualification pattern: a binary relation such as `wasAssociatedWith` can be restated as an intermediate node (`qualifiedAssociation` → `prov:Association`), which carries `hadPlan` (a `prov:Plan`) and `hadRole` (a `prov:Role`). Consumers should accept both forms, and the unqualified form is preferred when no extra detail is needed. — [W3C PROV-O](https://www.w3.org/TR/prov-o/)
- A `prov:Bundle` is "a named set of provenance descriptions, and is itself an Entity", so provenance can itself have provenance. PROV-O does not fix how bundles are serialized. — [W3C PROV-O](https://www.w3.org/TR/prov-o/)

### Inferences
- How an Agora record maps onto PROV (imagined):

  | Agora record | PROV |
  |---|---|
  | record | Activity |
  | who acted | `wasAssociatedWith` → Agent |
  | for whom | `actedOnBehalfOf` (actor → principal), or a qualified Association with `hadRole` |
  | verb | `hadPlan` / activity type |
  | "what the actor saw" | `used` edges |
  | each fact `[thing, aspect, hash before, value]` | a new Entity version that `wasGeneratedBy` the record and `wasRevisionOf` the version identified by "hash before" |
  | "what caused it" | `wasInformedBy` (record → record) |

  So a graph of PROV shape can be derived from the log without new data.
- The "thing" versus "thing-at-hash" distinction matters. PROV's `specializationOf` is exactly the edge from "note a123 as of hash H" to "note a123". Traversals for people want the general thing, and traversals for safety and audit want the specific version.
- Bundles suggest a way to let agents annotate the log ("I think record X was a mistake") without editing it. The annotations become records about records.
- **Cost (inference):** the qualified pattern multiplies nodes. Agora should keep the plain edge as the default and qualify only when a role or plan has to be carried.

### Gaps
- I did not read PROV-DM or PROV-CONSTRAINTS directly. Only PROV-O was fetched, and only its first 100k characters.
- I found no source in this session on PROV adoption in scientific workflows (e.g., ProvONE, workflow systems). That claim stays unverified here.

## 2. Immutable/accretive databases, bitemporality, event sourcing: what "as of" enables

### Takeaway
Datomic shows the cheapest useful design. Facts are 5-tuples (entity, attribute, value, transaction, added?), and transactions are themselves entities that can carry metadata. That metadata is where provenance lives. "As of" lets you replay what an actor saw when it acted. "Since" and "history" give change feeds and audit trails. Bitemporality (XTDB) separates "when it was true" from "when we learned it". Fowler warns that this is messy and should be used only when needed. Event sourcing's real costs are external side effects on replay, nondeterministic external inputs, and the occasional legal need to truly delete.

### Cited Findings
- Datomic `as-of` returns "a database 'as of' at a particular point in time", given a transaction id, a basis-t or a date. `since` returns "only datoms added by transactions after that point". `history` returns "the present and the unfiltered past, including retractions". — [Datomic filters](https://docs.datomic.com/reference/filters.html)
- Datoms have the columns e, a, v, tx and added (true for an assertion, false for a retraction). An update is a retraction plus an assertion in the same transaction. — [Datomic filters](https://docs.datomic.com/reference/filters.html)
- Transactions are entities with attributes such as `:db/txInstant`. The docs show a custom `:source/confidence` attribute on transactions, and a filter that excludes data from low-confidence transactions. — [Datomic filters](https://docs.datomic.com/reference/filters.html)
- Costs and caveats — [Datomic filters](https://docs.datomic.com/reference/filters.html):
  - "Filtering is not free."
  - The unfiltered current db pays no history penalty.
  - A lookup by identity can fail under `since`, so you resolve the entity with the current db.
  - `as-of` is not a branch.
  - A time-window question ("what happened 8:00–9:00") asked through as-of/since needs a full scan, so use the log instead.
- Datomic excision: it permanently removes matching datoms from the indexes and the log, for privacy or retention, and "is not a way to fix errors" (use retraction for that).
  - "Every excision creates a permanent record", and excision records cannot themselves be excised.
  - It is irreversible and causes heavy indexing load, so keep live excisions to a few thousand datoms.
  - Tracking is lossy: you can tell an entity *may* have been affected, but not which datom was removed.
  - Source: [Datomic excision](https://docs.datomic.com/operation/excision.html)
- XTDB has two time axes — [XTDB key concepts](https://docs.xtdb.com/concepts/key-concepts.html):
  - **System time** (`_system_from/_system_to`) is automatic and captures "the time that information entered the system", which makes it the audit axis.
  - **Valid time** (`_valid_from/_valid_to`) is set by the user, for when facts hold in the domain. It supports backfill, out-of-order updates and corrections.
  - Both are closed-open periods, and Allen interval operators (OVERLAPS, CONTAINS, PRECEDES) query across them.
  - Updates are non-destructive. The page I read did not cover erasure.
- Fowler on event sourcing — [Fowler, Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html):
  - **Complete rebuild:** state can be discarded and rebuilt by replay.
  - **Temporal query:** "determine the application state at any point in time", including branch-like parallel timelines.
  - **Retroactive fix:** reverse a wrong event and the later ones, then replay. Reversal is easiest when events store differences. Otherwise each event must store the prior value it overwrote.
  - **Snapshots:** they cache state, which "you can cache anywhere you like" because it is derived.
  - **External side effects:** wrap external systems in Gateways that suppress effects during replay.
  - **External queries:** record their responses, because replaying them later may return different data.
  - **Bitemporal handling:** it gets "very messy", so avoid it unless needed.
  - **Hard to retrofit:** "it's very hard to retrofit these patterns onto a system that wasn't built with Event Sourcing."
  - Fowler marks the article as an unfinished mid-2000s draft.

### Inferences
- Agora's fact `[thing, aspect, hash before, value]` is a Datomic datom with a stronger guard. "Hash before" makes every write a compare-and-set, so each fact carries its own `wasRevisionOf` edge. Datomic has no such per-fact edge, because it relies on transaction order.
- Agora already stores two things Fowler says event-sourced systems must add:
  - the prior value, which is reachable through the hash;
  - what the actor saw, which plays the role of recorded external-query responses.

  "What the actor saw" is the input to an AI decision. Recording it makes agent decisions reproducible and auditable in the way Fowler's recorded query responses make replay deterministic.
- What "as of" buys Agora in practice (imagined):
  1. "What did agent X see when it did Y?" means opening the world as of the record's predecessor, the frontier of its "saw" set.
  2. Undo as a new record that writes the old value forward, with no destructive rewind.
  3. Lenses that show a thing's history (`history` in Datomic terms).
  4. Change feeds: wake an agent with "since my last record", which is `since`.
  5. Differential review: compare as-of(before) with now for a story.
- Transaction metadata is the provenance hook, and Agora's record header (who, for whom, verb, caused-by) is that metadata. Datomic's confidence-filter example maps directly to a view that hides everything written by untrusted agents or derived from an adapter.
- Bitemporality: a world with adapters (mail, Twitch) will meet facts whose real-world time differs from ingestion time, for example a mail sent yesterday and pulled today. Fowler's warning and XTDB's design together suggest keeping system time (log order) as the only *kernel* axis, and treating valid time as an ordinary aspect where a kind needs it.
- Deletion: an append-only log conflicts with privacy and clutter (see Alex's clutter design). Datomic's answer is a separate, rare and loud excision operation that leaves a permanent tombstone and is never used for error correction. That is a model worth copying, because it keeps "retract" (normal) and "excise" (legal/privacy) apart.
- Snapshots are caches. The pickle beside the log already plays that role. Fowler's framing says it can be dropped and rebuilt, which is a useful invariant to test.

### Gaps
- I did not read the XTDB SQL syntax for as-of queries, or its erasure (`ERASE`) semantics.
- I found no measured cost numbers for as-of query overhead in Datomic. The docs say only "not free".

## 3. Data lineage tools: OpenLineage, Marquez, dbt, and impact analysis

### Takeaway
OpenLineage reduces lineage to Job, Run and Dataset plus extensible "facets", carried in run events. Impact analysis ("what breaks if I change this") is then a downstream traversal of that graph. It is most useful at column (field) granularity. This is the same pattern Agora would use for "which lenses, rules and agents depend on this aspect".

### Cited Findings
- OpenLineage core model — [OpenLineage object model](https://openlineage.io/docs/spec/object-model):
  - A Job is "a process that consumes or produces Datasets".
  - A Run is "an instance of a Job that represents one of its occurrences in time", with a client-made UUID (UUIDv7 recommended).
  - A Dataset is "an abstract representation of data", named uniquely within a namespace from its physical location (e.g., `db.host.database.schema.table`).
- Event types — [OpenLineage object model](https://openlineage.io/docs/spec/object-model):
  - A RunEvent is emitted at runtime, usually START then COMPLETE. Updates are additive, so inputs and outputs can arrive in either.
  - JobEvent and DatasetEvent carry design-time metadata (source code location, declared I/O, schema, ownership).
- Facets are the extension point — [OpenLineage object model](https://openlineage.io/docs/spec/object-model):
  - job facets: `sourceCodeLocation`, `sourceCode`;
  - run facets: `nominalTime`, `parent` (parent job and run), `errorMessage`, `sql`;
  - dataset facets: `schema`, `dataSource`, `lifecycleStateChange`, `version`;
  - input/output facets: data-quality metrics and assertions, output statistics.
- Marquez is described as the reference implementation that stores and visualizes OpenLineage events. These are secondary sources: [DEV Community comparison](https://dev.to/amoussa-eduhub/datalineage-vs-openlineage-marquez-datahub-which-data-lineage-tool-should-you-use-5f7m); [DEV Community, open standards](https://dev.to/gowthampotureddi/openlineage-openmetadata-open-standards-for-lineage-and-cataloging-133n).
- Column-level lineage is said to matter most for impact analysis, meaning which consumers a source-column change affects. Spark, dbt, Airflow and Flink emitters are reported to support a column-lineage facet. This is secondary/glossary-level: [Galaxy glossary](https://www.getgalaxy.io/learn/glossary/column-level-lineage-open-source-tools-explained).
- Practitioner pattern (a vendor case study): combine dbt manifest parsing, SQL parsing for column coverage and OpenLineage runtime events, then run impact analysis on every pull request — [Bacancy case study](https://www.bacancytechnology.com/insights/how-we-built-data-lineage-automation).

### Inferences
- OpenLineage separates **design-time** lineage (what a job declares it reads and writes) from **runtime** lineage (what a run actually did). Agora has both:
  - a lens, rule or verb *declares* which aspects it reads;
  - the log *records* what each act saw and wrote.

  Impact analysis can use the declared graph ("what might break") and check it against the observed graph ("what actually depended on this in the last N days"). A gap between the two is itself a finding: a declared dependency never exercised, or an undeclared one observed.
- The `parent` run facet is the same as Agora's "caused-by" and "for whom", so nesting agent runs under the story or commission that started them falls out of it.
- Facets are a good template for keeping the record schema small while allowing kinds to attach extra provenance (model id, prompt hash, cost) without kernel changes. This fits "general words, not bespoke".
- Granularity matters. Thing-level lineage over-approximates, the way table-level lineage does. Aspect-level lineage, the analogue of column-level, is what makes "what breaks if I rename this aspect" precise. Agora's facts are already aspect-level.

### Gaps
- I did not reach official Marquez docs on its lineage API or any downstream-impact endpoint. The Marquez claims above come from secondary sources.
- The OpenLineage page I read did not describe the column-lineage facet's schema or the FAIL/ABORT states. I recall they exist but did not verify them.
- I found no quantitative evidence (incident reduction etc.) for impact analysis in practice.

## 4. Provenance and information flow in security: system provenance IDS, taint, IFC/DIFC, and LLM-agent IFC

### Takeaway
There are two lineages:
1. **System provenance graphs** for intrusion detection. They record everything and suffer *dependency explosion*: coarse edges make everything look connected.
2. **Information-flow control**, from Denning's lattice through decentralised labels (Jif, HiStar) to 2025–26 LLM-agent work (CaMeL, FIDES, RTBAS, ARM).

The agent work converges on one mechanism:
- label every value with its source (integrity) and allowed readers (confidentiality);
- join labels as data mixes;
- keep untrusted content out of the planner's context, by reference rather than by value;
- check labels deterministically at consequential tool calls, with escalation to a human when a check fails.

The known costs are lost utility (about 7 points for CaMeL, up to 24.5% for FIDES), roughly 2.8× tokens for CaMeL, label creep, policy-authoring burden and side channels.

### Cited Findings
**System provenance / IDS**
- A 2020 survey of system-level provenance graphs makes three points — [Threat Detection and Investigation with System-level Provenance Graphs: A Survey (arXiv 2006.01722)](https://arxiv.org/pdf/2006.01722):
  - Dependency explosion comes from coarse-grained provenance and causality analysis, which adds false positives and overhead.
  - Fine-grained collection is the fundamental remedy, but it is too costly in deployment, and existing mitigations are only partial.
  - Most detectors are sequence-based rather than graph-based.
- Provenance graphs grow very large as capture gets finer, and detection needs analysis of dynamic, attributed, streaming graphs, which the literature has rarely studied. — [Han, Pasquier, Seltzer, TAPP 2018 (arXiv 1806.00934)](https://arxiv.org/pdf/1806.00934)
- Mimicry attacks are reported to evade provenance-graph host IDS, with 100% evasion success on public datasets. This comes from a search snippet of an NSF award listing, and I did not read the paper. — [NSF PAR listing](https://par.nsf.gov/search/award_ids:1750024)

**Classical IFC**
- Denning (CACM 19(5), 1976, pp. 236–243) models security classes as a lattice "justified by the semantics of information flow". The lattice supports automatic program certification of secure flow. — [CACM listing](https://cacmb4.acm.org/magazines/1976/5/11471-a-lattice-model-of-secure-information-flow); full text at [Duke reading copy](https://courses.cs.duke.edu/spring15/cps210/readings/ifc-denning76.pdf). I did not read the full text this session. That implicit (control-dependency) flows are central to it is my recall.
- Myers & Liskov's decentralized label model (SOSP 1997) — [Myers & Liskov, SOSP 97](https://www.cs.cornell.edu/andru/papers/iflow-sosp97); [Jif paper copy](https://cs.brown.edu/courses/csci2390/2023/readings/jif.pdf):
  - It supports mutually distrusting principals.
  - Each owner sets the policies on its own data and may declassify *its own* data without leaking others'.
  - It is statically checked in Jif, an extension of Java.
- HiStar enforces decentralized IFC in an OS, with OS objects as the labelled variables. It isolates a lot of untrusted code using a little trusted wrapper code that decides how to declassify results. — [CACM Technical Perspective](https://cacmb4.acm.org/magazines/2011/11/138222-technical-perspective-making-untrusted-code-useful). Sources disagree on HiStar's kernel size (search results gave both ~2,000 and ~20,000 lines), so I am not quoting a number.

**IFC for LLM agents**
- **CaMeL** ("Defeating Prompt Injections by Design", arXiv 2503.18813) — [arXiv HTML](https://arxiv.org/html/2503.18813); [abstract](https://arxiv.org/abs/2503.18813):
  - **Planner:** a Privileged LLM sees only the trusted user query and writes Python for the plan. It never sees tool output contents.
  - **Parser:** a Quarantined LLM has no tools and parses untrusted data into a schema.
  - **Interpreter:** a custom interpreter runs restricted Python and tracks each value's dependencies. In STRICT mode, branch and loop conditions become dependencies of everything assigned inside the block, which is the side-channel defence.
  - **Capabilities:** each value carries provenance (User, CaMeL, or a specific tool plus inner source such as an email sender) and allowed readers (Public, or a set of users).
  - **Policies:** Python functions checked before each tool call. For example, `send_money` requires recipient and amount to have no untrusted ancestor. A denial "will require user confirmation".
  - **Key insight:** protecting the *control flow* is not enough, because injected data can still change *arguments* (e.g., the recipient), as in SQL injection.
- CaMeL results and costs — same sources:
  - 77% of AgentDojo tasks solved with provable security, against 84% undefended.
  - 0 of 949 attacks succeeded with Claude 3.5 Sonnet.
  - 2.82× input and 2.73× output tokens at the median.
  - Limitations: the side channels above; failures where "data requires action"; user fatigue from maintaining policies and confirmations; text-to-text attacks out of scope; possible ROP-style chaining of allowed blocks. In the authors' words, "prompt injection attacks are not fully solved."
- **FIDES** (Microsoft, arXiv 2505.23643; code at github.com/microsoft/fides) — [arXiv HTML v2](https://arxiv.org/html/2505.23643v2); [MSR page](https://www.microsoft.com/en-us/research/publication/securing-ai-agents-with-information-flow-control/):
  - **Labels:** the product of an integrity lattice (Trusted/Untrusted) and a confidentiality readers lattice, joined as data combines.
  - **Planner context:** the planner tracks the join of its whole history, so once tainted it stays tainted ("label creep").
  - **Variables:** tool results that would raise the context label are stored as variables (e.g., `#read_emails_0`) and passed by reference.
  - **`inspect`** expands a variable into context and accepts the taint.
  - **`query_llm`** sends a variable to a tool-less LLM whose output is constrained to a type such as bool or enum. Low-capacity types carry little injected information.
  - **Policies:** P-T (consequential calls need trusted context and arguments) and P-F (egress only to authorized readers).
- FIDES results and costs — same source:
  - Without policies, the Basic planner suffered 156 successful injections and FIDES 23. With policies, every policy-violating attack was blocked.
  - Utility drops up to 40% for Basic (gpt-4o) and up to 24.5% for FIDES (o3/o4-mini). FIDES still beats Basic by up to 16.7%.
  - Limitations: text-only manipulation is not stopped; label propagation through LLM calls is conservative (over-tainting); trusted tool wrappers are needed to assign labels; one benchmark, one attack, five runs.
- **RTBAS** (arXiv 2502.08966) — [arXiv abstract](https://arxiv.org/abs/2502.08966):
  - Applies IFC to tool-based agents, with two dependency screeners (LM-as-judge and attention-based saliency) that decide which inputs a model output actually depended on. This counters over-tainting.
  - Asks the user only when integrity or confidentiality cannot be ensured.
  - Reported to prevent all targeted attacks on AgentDojo at about 2% utility loss under attack.
- **Causality Laundering / ARM** (Chinaei, arXiv 2604.04035, Apr 2026) — [arXiv abstract](https://arxiv.org/abs/2604.04035):
  - Attack: an attacker probes a protected action, learns from the *denial*, then leaks the inference through a later benign-looking call. Flat provenance misses this.
  - Defence: the Agentic Reference Monitor keeps a provenance graph of tool calls, returned data, field-level provenance *and denied actions*, with **counterfactual edges** from denied-action nodes.
  - Evaluated on three scenarios with sub-millisecond policy overhead. There are no larger-scale numbers.
- **NeuroTaint** (arXiv 2604.23374) is reported to argue that memory-style taint analysis fails for LLMs, and to propose provenance-based auditing of agent information flow. — [Emergent Mind listing](https://www.emergentmind.com/papers/2604.23374) (search snippet only, not read)
- **APPA** (arXiv 2607.24625, NeurIPS 2026 listing) is reported to target "monotone" taint that over-blocks or permanently strands execution once untrusted data is ingested, and to propose *recoverable* IFC. — [arXiv PDF](https://arxiv.org/pdf/2607.24625); [NeurIPS listing](https://neurips.cc/virtual/2026/168263) (search snippet only, not read)

### Inferences
- Agora's record already holds the inputs IFC needs:
  - "what the actor saw" is the `used` set;
  - "who acted / for whom" gives the principal for decentralized labels;
  - "what caused it" gives control dependence.

  A label for any fact can therefore be *computed* as the join of the labels of everything its record saw, rather than stored. That is FIDES's history-join, but per record instead of per conversation. Computing labels from the log means policy changes apply retroactively without rewriting data.
- Dependency explosion is the main risk for a traversable Agora graph. If "saw" means "had in context", one widely-read note (the charter, the board) becomes an ancestor of everything. That mirrors the IDS problem and FIDES label creep. Mitigations seen in the literature:
  1. Finer granularity: record *which aspects* were read, not whole things (column-level, as in lineage; field-level, as in ARM).
  2. By-reference handling: an agent passes a thing id without reading its contents (FIDES variables, CaMeL's P-LLM), so "saw" stays small.
  3. Low-capacity channels: an untrusted thing influences a decision only through a bool or enum (FIDES `query_llm`).
  4. Dependency screening: decide afterwards which seen inputs mattered (RTBAS). This is probabilistic, so it is weaker as a guarantee.
- Distinguish "saw" from "cited" (imagined). An agent's context is broad, but the inputs a record *claims as justification* can be narrow. Keep both: the broad set for security (conservative) and the narrow set for explanation (useful).
- Integrity is the more urgent axis for Agora. Residents read adapter content (mail, Twitch chat), and that content is the prompt-injection vector. A minimal policy in the style of FIDES P-T (imagined): consequential verbs (send, delete, change a standing rule, run code on the PC) need a record whose `saw` set carries no untrusted-integrity ancestor, or else escalate to Alex as a one-click confirmation. This fits Alex's rule of "make it one click", and CaMeL and RTBAS both default to confirmation on denial.
- Decentralized labels fit Agora's "things belong to people" (No rooms, 27 Oct). Each owner declassifies only their own things, as in Myers & Liskov. HiStar's "little trusted wrapper decides declassification" corresponds to adapters as the labelled boundary: an adapter stamps everything it ingests as untrusted-integrity with readers set by the owner.
- ARM's denied-action edges suggest that Agora should log refusals and denials as records too. A denial is information, and an agent that learned from it carries that influence.
- Costs to plan for:
  - Utility loss and confirmation fatigue (CaMeL, FIDES).
  - Token overhead whenever planning and parsing are split into two models (CaMeL about 2.8×).
  - Over-tainting, which pushes people to over-declassify and so defeats the system.
  - No IFC scheme here stops text-to-text persuasion. An injected mail can still mislead a summary Alex reads.

### Gaps
- I did not read the full texts of NeuroTaint and APPA. Their claims are from search snippets, and I could not verify APPA's arXiv id or date beyond the listing.
- I did not read the Flume paper. No search result covered it.
- I read no measured overhead for system-provenance capture (e.g., CamFlow/SPADE storage per day). Only qualitative "very large" claims.

## 5. Explanations and accountability: how provenance supports trust in automated decisions

### Takeaway
None of the sources I read is primarily about explanation, so this section is mostly inference from mechanisms that are cited. The common thread across PROV, Datomic, Fowler and CaMeL is that accountability needs three recorded things:
- **who was responsible, and for whom** (PROV `actedOnBehalfOf`);
- **what the decision-maker saw** (Fowler's recorded query responses; CaMeL and FIDES provenance on every value);
- **a deterministic, human-readable reason when an action is allowed or refused** (CaMeL policies return Allowed/Denied *with a reason*).

### Cited Findings
- PROV defines `actedOnBehalfOf` as "accountability of an agent towards another agent", and lets an Association carry the Plan the agent intended to follow. — [W3C PROV-O](https://www.w3.org/TR/prov-o/)
- Fowler lists audit and support diagnosis, plus debugging by replaying production events in a test environment, as reasons to use event sourcing. — [Fowler](https://martinfowler.com/eaaDev/EventSourcing.html)
- CaMeL's security policies return Allowed or Denied with a reason before a tool runs, and a denial goes to user confirmation. Errors whose message depends on untrusted data are redacted before the planner sees them. — [CaMeL arXiv HTML](https://arxiv.org/html/2503.18813)
- Datomic transaction metadata (e.g., a confidence attribute) can be used to filter which facts a reader trusts. — [Datomic filters](https://docs.datomic.com/reference/filters.html)

### Inferences
- An "explain" verb over Agora's graph (imagined). For any fact, walk:
  1. the record that wrote it (who, for whom, verb, when);
  2. what that record saw, opened as-of so you see exactly what the agent saw, not today's version;
  3. what caused it, up to a human request.

  That is a PROV traversal ending at Alex or a story. It answers "why is this here?" for both people and agents.
- Explanations should come from the log, not from the agent's after-the-fact narrative. An LLM's own account of why it acted is unreliable, while the record of what it saw and what triggered it is not. The narrative can be stored as an annotation that is itself attributed, like a PROV bundle about the record.
- The trust gradient follows provenance. A view can show each fact's integrity, for example by dimming facts whose ancestry includes adapters or untrusted agents. This is Datomic's confidence filter, rendered visually.
- **Failure mode:** an explanation graph that is too big to read (dependency explosion again). Explanations need a *narrow* "cited" set, with the full set behind a click.

### Gaps
- I found and read no primary source specifically on provenance for explainable AI or algorithmic accountability (e.g., the PROV in-use literature, or regulatory audit-trail requirements). This section's links between provenance and trust are design inferences, not findings.
- I have no evidence on whether people actually use provenance views when they are offered. User studies were not searched.
